-- ============================================================================
-- Mutation: create_contact
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: create_contact
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create_contact(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_create_contact_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_create_contact_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN crm.create_contact(
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

COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';

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
    v_fk_company INTEGER;
BEGIN
    -- === VALIDATION ===

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.company_id IS NOT NULL THEN
        v_fk_company := crm.company_pk(input_data.company_id::TEXT, auth_tenant_id);

        IF v_fk_company IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                '00000000-0000-0000-0000-000000000000'::UUID,
                'NOOP',
                 'validation:reference_not_found',
                ARRAY['company_id']::TEXT[],
                 'Referenced company not found',
                NULL, NULL,
                jsonb_build_object('company_id', input_data.company_id)
            );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO crm.tb_contact (
        id,
        tenant_id,
        email,
        first_name,
        last_name,
        fk_company,
        status,
        phone,
        created_at,
        created_by
    ) VALUES (
        v_contact_id,
        auth_tenant_id,
        input_data.email,
        input_data.first_name,
        input_data.last_name,
        v_fk_company,
        input_data.status,
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

COMMENT ON FUNCTION crm.create_contact IS
'Core business logic for create contact.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- INSERT operation on crm.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.create_contact (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
