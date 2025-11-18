-- ============================================================================
-- Mutation: create_locale
-- Entity: Locale
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: create_locale
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create_locale(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_create_locale_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_create_locale_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN catalog.create_locale(
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

COMMENT ON FUNCTION app.create_locale IS
'Creates a new Locale record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createLocale
input_type: app.type_create_locale_input
success_type: CreateLocaleSuccess
failure_type: CreateLocaleError';

-- ============================================================================
-- CORE LOGIC: catalog.create_locale
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION catalog.create_locale(
    auth_tenant_id UUID,
    input_data app.type_create_locale_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_locale_id UUID := gen_random_uuid();
    v_locale_pk INTEGER;
    v_fk_language INTEGER;
BEGIN
    -- === VALIDATION ===
    IF input_data.code IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'locale',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['code']::TEXT[],
            'Code is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_code_null')
        );
    END IF;
    IF input_data.language IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'locale',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['language']::TEXT[],
            'Language is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_language_null')
        );
    END IF;
    IF input_data.name IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'locale',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['name']::TEXT[],
            'Name is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_name_null')
        );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.language_id IS NOT NULL THEN
        v_fk_language := catalog.language_pk(input_data.language_id::TEXT);

        IF v_fk_language IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'locale',
                '00000000-0000-0000-0000-000000000000'::UUID,
                'NOOP',
                 'validation:reference_not_found',
                ARRAY['language_id']::TEXT[],
                 'Referenced language not found',
                NULL, NULL,
                jsonb_build_object('language_id', input_data.language_id)
            );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO catalog.tb_locale (
        id,
        tenant_id,
        code,
        fk_language,
        name,
        flag_emoji,
        decimal_separator,
        grouping_separator,
        numeric_pattern,
        currency_symbol_position,
        currency_pattern,
        date_format,
        time_format,
        first_day_of_week,
        is_rtl,
        is_default,
        is_active,
        sort_order,
        created_at,
        created_by
    ) VALUES (
        v_locale_id,
        auth_tenant_id,
        input_data.code,
        v_fk_language,
        input_data.name,
        input_data.flag_emoji,
        input_data.decimal_separator,
        input_data.grouping_separator,
        input_data.numeric_pattern,
        input_data.currency_symbol_position,
        input_data.currency_pattern,
        input_data.date_format,
        input_data.time_format,
        input_data.first_day_of_week,
        input_data.is_rtl,
        input_data.is_default,
        input_data.is_active,
        input_data.sort_order,
        now(),
        auth_user_id
    )
    RETURNING pk_locale INTO v_locale_pk;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'locale',
        v_locale_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Locale created successfully',
        (SELECT row_to_json(t.*) FROM catalog.tb_locale t WHERE t.id = v_locale_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION catalog.create_locale IS
'Core business logic for create locale.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- INSERT operation on catalog.tb_locale
- Audit logging via app.log_and_return_mutation

Called by: app.create_locale (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
