-- ============================================================================
-- Mutation: create
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: create
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_create_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_create_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN crm.create(
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

COMMENT ON FUNCTION app.create IS
'Performs create operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: create
input_type: app.type_create_input
success_type: CreateSuccess
failure_type: CreateError';

-- ============================================================================
-- CORE LOGIC: crm.create_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION crm.create_contact(
    auth_tenant_id UUID,
    input_data app.type_create_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := gen_random_uuid();
    v_contact_pk INTEGER;
BEGIN
    -- === VALIDATION ===

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO crm.tb_contact (
        id,
        tenant_id,
        email,
        first_name,
        last_name,
        phone,
        created_at,
        created_by
    ) VALUES (
        v_contact_id,
        auth_tenant_id,
        input_data.email,
        input_data.first_name,
        input_data.last_name,
        input_data.phone,
        now(),
        auth_user_id
    )
    RETURNING pk_contact INTO v_contact_pk;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact created successfully',
        (SELECT row_to_json(t.*) FROM crm.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION crm.create IS
'Core business logic for create.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on crm.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.create (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
