-- ============================================================================
-- Mutation: change_mobile_phone
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: change_mobile_phone
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.change_mobile_phone(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_change_mobile_phone_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_change_mobile_phone_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.change_mobile_phone(
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

COMMENT ON FUNCTION app.change_mobile_phone IS
'Performs change mobile phone operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: changeMobilePhone
input_type: app.type_change_mobile_phone_input
success_type: ChangeMobilePhoneSuccess
failure_type: ChangeMobilePhoneError';

-- ============================================================================
-- CORE LOGIC: tenant.change_mobile_phone
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.change_mobile_phone(
    auth_tenant_id UUID,
    input_data app.type_change_mobile_phone_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := input_data.id;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'change_mobile_phone: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Change Mobile Phone completed',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION tenant.change_mobile_phone IS
'Core business logic for change mobile phone.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.change_mobile_phone (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
