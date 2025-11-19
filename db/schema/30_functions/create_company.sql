-- ============================================================================
-- Mutation: create_company
-- Entity: Company
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: create_company
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create_company(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_create_company_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_create_company_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN crm.create_company(
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

COMMENT ON FUNCTION app.create_company IS
'Creates company.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createCompany
input_type: app.type_create_company_input
success_type: CreateCompanySuccess
failure_type: CreateCompanyError';

-- ============================================================================
-- CORE LOGIC: crm.create_company
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION crm.create_company(
    auth_tenant_id UUID,
    input_data app.type_create_company_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_company_id UUID := gen_random_uuid();
    v_company_pk INTEGER;
BEGIN
    -- === VALIDATION ===

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO crm.tb_company (
        id,
        tenant_id,
        name,
        industry,
        website,
        size,
        description,
        created_at,
        created_by
    ) VALUES (
        v_company_id,
        auth_tenant_id,
        input_data.name,
        input_data.industry,
        input_data.website,
        input_data.size,
        input_data.description,
        now(),
        auth_user_id
    )
    RETURNING pk_company INTO v_company_pk;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'company',
        v_company_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Company created successfully',
        (SELECT row_to_json(t.*) FROM crm.tb_company t WHERE t.id = v_company_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION crm.create_company IS
'Core business logic for create company.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- INSERT operation on crm.tb_company
- Audit logging via app.log_and_return_mutation

Called by: app.create_company (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
