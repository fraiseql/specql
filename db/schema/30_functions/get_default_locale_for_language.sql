-- ============================================================================
-- Mutation: get_default_locale_for_language
-- Entity: Locale
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: get_default_locale_for_language
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.get_default_locale_for_language(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_get_default_locale_for_language_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_get_default_locale_for_language_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN catalog.get_default_locale_for_language(
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

COMMENT ON FUNCTION app.get_default_locale_for_language IS
'Performs get default locale for language operation on Locale.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: getDefaultLocaleForLanguage
input_type: app.type_get_default_locale_for_language_input
success_type: GetDefaultLocaleForLanguageSuccess
failure_type: GetDefaultLocaleForLanguageError';

-- ============================================================================
-- CORE LOGIC: catalog.get_default_locale_for_language
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION catalog.get_default_locale_for_language(
    auth_tenant_id UUID,
    input_data app.type_get_default_locale_for_language_input,
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
    RAISE NOTICE 'get_default_locale_for_language: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;
    -- Query: Locale WHERE
  language = :language_id AND
  is_default = TRUE AND
  deleted_at IS NULL
LIMIT 1


    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'locale',
        v_locale_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Get Default Locale For Language completed',
        (SELECT row_to_json(t.*) FROM catalog.tb_locale t WHERE t.id = v_locale_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION catalog.get_default_locale_for_language IS
'Core business logic for get default locale for language.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on catalog.tb_locale
- Audit logging via app.log_and_return_mutation

Called by: app.get_default_locale_for_language (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
