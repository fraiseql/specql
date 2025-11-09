-- ============================================================================
-- Mutation: update
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: update
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.update(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_update_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_update_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN crm.update(
        auth_tenant_id,
        input_data,
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

COMMENT ON FUNCTION app.update IS
'Performs update operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: update
input_type: app.type_update_input
success_type: UpdateSuccess
failure_type: UpdateError';

-- ============================================================================
-- CORE LOGIC: crm.update_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION crm.update_contact(
    auth_tenant_id UUID,
    input_data app.type_update_contact_input,
    input_payload JSONB,
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
    FROM crm.tb_contact
    WHERE id = input_data.id::UUID
      AND tenant_id = auth_tenant_id;

    IF v_contact_id IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_data.id::UUID,
            'NOOP',
             'validation:reference_not_found',
            ARRAY['id']::TEXT[],
             'Referenced contact not found',
            NULL, NULL,
            jsonb_build_object('entity_id', input_data.id)
        );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===

    -- === BUSINESS LOGIC: UPDATE ===
    UPDATE crm.tb_contact
    SET
        email = input_data.email,
        first_name = input_data.first_name,
        last_name = input_data.last_name,
        phone = input_data.phone,
        updated_at = now(),
        updated_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'UPDATE',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact updated successfully',
        (SELECT row_to_json(t.*) FROM crm.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION crm.update IS
'Core business logic for update.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on crm.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.update (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
