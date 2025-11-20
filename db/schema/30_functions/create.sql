-- ============================================================================
-- Mutation: create
-- Entity: Task
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
'Performs create operation on Task.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: create
input_type: app.type_create_input
success_type: CreateSuccess
failure_type: CreateError';

-- ============================================================================
-- CORE LOGIC: crm.create_task
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION crm.create_task(
    auth_tenant_id UUID,
    input_data app.type_create_task_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_task_id UUID := gen_random_uuid();
    v_task_pk INTEGER;
BEGIN
    -- === VALIDATION ===

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO crm.tb_task (
        id,
        tenant_id,
        title,
        description,
        priority,
        created_at,
        created_by
    ) VALUES (
        v_task_id,
        auth_tenant_id,
        input_data.title,
        input_data.description,
        input_data.priority,
        now(),
        auth_user_id
    )
    RETURNING pk_task INTO v_task_pk;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'task',
        v_task_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Task created successfully',
        (SELECT row_to_json(t.*) FROM crm.tb_task t WHERE t.id = v_task_id)::JSONB,
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
- OPERATION operation on crm.tb_task
- Audit logging via app.log_and_return_mutation

Called by: app.create (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
