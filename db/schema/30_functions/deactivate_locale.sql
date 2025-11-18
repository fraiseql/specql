-- ============================================================================
-- Mutation: deactivate_locale
-- Entity: Locale
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: deactivate_locale
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.deactivate_locale(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_deactivate_locale_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_deactivate_locale_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN catalog.deactivate_locale(
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

COMMENT ON FUNCTION app.deactivate_locale IS
'Performs deactivate locale operation on Locale.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: deactivateLocale
input_type: app.type_deactivate_locale_input
success_type: DeactivateLocaleSuccess
failure_type: DeactivateLocaleError';

-- ============================================================================
-- CORE LOGIC: catalog.deactivate_locale
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION catalog.deactivate_locale(
    auth_tenant_id UUID,
    input_data app.type_deactivate_locale_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_locale_id UUID := input_data.id;
    v_locale_pk INTEGER;
    v_fk_language INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'deactivate_locale: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;
    -- Update Locale
    UPDATE catalog.tb_locale SET is_active = FALSE, updated_at = now(), updated_by = auth_user_id
    WHERE id = v_locale_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'locale',
        v_locale_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Deactivate Locale completed',
        (SELECT row_to_json(t.*) FROM catalog.tb_locale t WHERE t.id = v_locale_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION catalog.deactivate_locale IS
'Core business logic for deactivate locale.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on catalog.tb_locale
- Audit logging via app.log_and_return_mutation

Called by: app.deactivate_locale (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
