-- ============================================================================
-- Mutation: delete_contact
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: delete_contact
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.delete_contact(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
    -- No composite type needed for delete actions
    -- Delegate to core business logic
    RETURN tenant.delete_contact(
        auth_tenant_id,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.delete_contact IS
'Deletes an existing Contact record.
Validates permissions and delegates to core business logic.

@fraiseql:mutation
name: deleteContact
input_type: app.type_delete_contact_input
success_type: DeleteContactSuccess
failure_type: DeleteContactError';

-- ============================================================================
-- CORE LOGIC: tenant.delete_contact
-- Soft Delete with Audit Trail
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.delete_contact(
    auth_tenant_id UUID,
    input_entity_id UUID,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID;
    v_contact_pk INTEGER;
BEGIN
    -- === VALIDATION ===
    -- Check if entity exists and belongs to tenant
    SELECT id, pk_contact
    INTO v_contact_id, v_contact_pk
    FROM tenant.tb_contact
    WHERE id = input_entity_id
      AND tenant_id = auth_tenant_id
      AND deleted_at IS NULL;  -- Not already soft deleted

    IF v_contact_id IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_entity_id,
            'NOOP',
             'validation:reference_not_found',
            ARRAY['entity_id']::TEXT[],
             'Referenced contact not found',
            NULL, NULL,
            jsonb_build_object('entity_id', input_entity_id)
        );
    END IF;

    -- === BUSINESS LOGIC: SOFT DELETE ===
    UPDATE tenant.tb_contact
    SET
        deleted_at = now(),
        deleted_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'DELETE',
        'success',
        ARRAY['entity_id']::TEXT[],
        'Contact deleted successfully',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION tenant.delete_contact IS
'Core business logic for delete contact.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- DELETE operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.delete_contact (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
