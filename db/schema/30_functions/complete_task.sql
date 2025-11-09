-- ============================================================================
-- Mutation: complete_task
-- Entity: Task
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: complete_task
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.complete_task(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_complete_task_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_complete_task_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN projects.complete_task(
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

COMMENT ON FUNCTION app.complete_task IS
'Performs complete task operation on Task.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: completeTask
input_type: app.type_complete_task_input
success_type: CompleteTaskSuccess
failure_type: CompleteTaskError';

-- ============================================================================
-- CORE LOGIC: projects.complete_task
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION projects.complete_task(
    auth_tenant_id UUID,
    input_data app.type_complete_task_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_task_id UUID := input_data.id;
    v_task_pk INTEGER;
    v_current_status TEXT;
    v_fk_assignee INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'complete_task: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;
    -- Fetch current values for validation: status = 'in_progress'
    RAISE NOTICE 'Before SELECT: v_task_id=%, auth_tenant_id=%', v_task_id, auth_tenant_id;
    SELECT status INTO v_current_status
    FROM projects.tb_task WHERE id = v_task_id AND tenant_id = auth_tenant_id;
    RAISE NOTICE 'After SELECT: v_current_status=%', v_current_status;
    -- Validate: status = 'in_progress'
    RAISE NOTICE 'Before validation: v_current_status=%', v_current_status;
    IF NOT (v_current_status = 'in_progress') THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id, 'task', v_task_id,
            'CUSTOM', 'failed:validation_error',
            ARRAY[]::TEXT[], 'task_not_in_progress', NULL, NULL
        );
    END IF;
    -- Update Task
    UPDATE projects.tb_task SET status = 'done', updated_at = now(), updated_by = auth_user_id
    WHERE id = v_task_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'task',
        v_task_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Complete Task completed',
        (SELECT row_to_json(t.*) FROM projects.tb_task t WHERE t.id = v_task_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION projects.complete_task IS
'Core business logic for complete task.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on projects.tb_task
- Audit logging via app.log_and_return_mutation

Called by: app.complete_task (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
