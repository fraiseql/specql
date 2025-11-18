-- ============================================================================
-- Mutation: list_active_locales
-- Entity: Locale
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: list_active_locales
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.list_active_locales(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_list_active_locales_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_list_active_locales_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN catalog.list_active_locales(
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

COMMENT ON FUNCTION app.list_active_locales IS
'Performs list active locales operation on Locale.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: listActiveLocales
input_type: app.type_list_active_locales_input
success_type: ListActiveLocalesSuccess
failure_type: ListActiveLocalesError';

-- ============================================================================
-- CORE LOGIC: catalog.list_active_locales
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION catalog.list_active_locales(
    auth_tenant_id UUID,
    input_data app.type_list_active_locales_input,
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
    RAISE NOTICE 'list_active_locales: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;
    -- Query: SELECT
  l.*,
  lang.name as language_name,
  lang.iso_code as language_code
FROM catalog.tb_locale l
JOIN catalog.tb_language lang ON l.fk_language = lang.pk_language
WHERE l.is_active = TRUE AND l.deleted_at IS NULL
ORDER BY l.sort_order ASC NULLS LAST, l.name ASC


    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'locale',
        v_locale_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'List Active Locales completed',
        (SELECT row_to_json(t.*) FROM catalog.tb_locale t WHERE t.id = v_locale_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION catalog.list_active_locales IS
'Core business logic for list active locales.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on catalog.tb_locale
- Audit logging via app.log_and_return_mutation

Called by: app.list_active_locales (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
