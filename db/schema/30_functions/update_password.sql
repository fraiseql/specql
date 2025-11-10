-- ============================================================================
-- Mutation: update_password
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: update_password
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.update_password(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_update_password_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_update_password_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.update_password(
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

COMMENT ON FUNCTION app.update_password IS
'Updates an existing Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: updatePassword
input_type: app.type_update_password_input
success_type: UpdatePasswordSuccess
failure_type: UpdatePasswordError';

-- ============================================================================
-- CORE LOGIC: tenant.update_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.update_contact(
    auth_tenant_id UUID,
    input_data app.type_update_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- === VALIDATION ===
    -- Check if entity exists and belongs to tenant
    SELECT id, pk_contact
    INTO v_contact_id, v_contact_pk
    FROM tenant.tb_contact
    WHERE id = input_data.id::UUID
      AND tenant_id = auth_tenant_id;

    IF v_contact_id IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_data.id::UUID,
            'NOOP',
             'validation:reference_not_found',
            ARRAY['id']::TEXT[],
             'Referenced contact not found',
            NULL, NULL,
            jsonb_build_object('entity_id', input_data.id)
        );
    END IF;
    IF input_data.email_address IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                v_contact_id,
                'NOOP',
                'validation:required_field',
                ARRAY['email_address']::TEXT[],
                'Email_address is required',
                NULL, NULL,
                jsonb_build_object('reason', 'validation_email_address_null')
            );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.customer_org_id IS NOT NULL THEN
        v_fk_customer_org := tenant.organization_pk(input_data.customer_org_id::TEXT, auth_tenant_id);

        IF v_fk_customer_org IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['customer_org_id']::TEXT[],
                     'Referenced organization not found',
                    NULL, NULL,
                    jsonb_build_object('customer_org_id', input_data.customer_org_id)
                );
        END IF;
    END IF;
    IF input_data.genre_id IS NOT NULL THEN
        v_fk_genre := tenant.genre_pk(input_data.genre_id::TEXT, auth_tenant_id);

        IF v_fk_genre IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['genre_id']::TEXT[],
                     'Referenced genre not found',
                    NULL, NULL,
                    jsonb_build_object('genre_id', input_data.genre_id)
                );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: UPDATE ===
    UPDATE tenant.tb_contact
    SET
        first_name = input_data.first_name,
        last_name = input_data.last_name,
        email_address = input_data.email_address,
        office_phone = input_data.office_phone,
        mobile_phone = input_data.mobile_phone,
        job_title = input_data.job_title,
        position = input_data.position,
        lang = input_data.lang,
        locale = input_data.locale,
        timezone = input_data.timezone,
        handles = input_data.handles,
        password_hash = input_data.password_hash,
        fk_customer_org = v_fk_customer_org,
        fk_genre = v_fk_genre,
        updated_at = now(),
        updated_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'UPDATE',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact updated successfully',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION tenant.update_password IS
'Core business logic for update password.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- UPDATE operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.update_password (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
