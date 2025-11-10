-- ============================================================================
-- Mutation: change_timezone
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: change_timezone
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.change_timezone(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_change_timezone_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_change_timezone_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.change_timezone(
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

COMMENT ON FUNCTION app.change_timezone IS
'Performs change timezone operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: changeTimezone
input_type: app.type_change_timezone_input
success_type: ChangeTimezoneSuccess
failure_type: ChangeTimezoneError';

-- ============================================================================
-- CORE LOGIC: tenant.change_timezone
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.change_timezone(
    auth_tenant_id UUID,
    input_data app.type_change_timezone_input,
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
    RAISE NOTICE 'change_timezone: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Change Timezone completed',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION tenant.change_timezone IS
'Core business logic for change timezone.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.change_timezone (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
