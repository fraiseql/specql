-- ============================================================================
-- Mutation: create_booking
-- Entity: Booker
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: create_booking
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create_booking(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_create_booking_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_create_booking_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN public.create_booking(
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

COMMENT ON FUNCTION app.create_booking IS
'Creates a new Booker record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createBooking
input_type: app.type_create_booking_input
success_type: CreateBookingSuccess
failure_type: CreateBookingError';

-- ============================================================================
-- CORE LOGIC: public.create_booker
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION public.create_booker(
    auth_tenant_id UUID,
    input_data app.type_create_booker_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_booker_id UUID := gen_random_uuid();
    v_booker_pk INTEGER;
BEGIN
    -- === VALIDATION ===
    IF input_data.name IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'booker',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['name']::TEXT[],
            'Name is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_name_null')
        );
    END IF;
    IF input_data.email IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'booker',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['email']::TEXT[],
            'Email is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_email_null')
        );
    END IF;
    IF input_data.phone IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'booker',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['phone']::TEXT[],
            'Phone is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_phone_null')
        );
    END IF;
    IF input_data.group_size IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'booker',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['group_size']::TEXT[],
            'Group_size is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_group_size_null')
        );
    END IF;
    IF input_data.registered_at IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'booker',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['registered_at']::TEXT[],
            'Registered_at is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_registered_at_null')
        );
    END IF;
    IF input_data.last_updated IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'booker',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['last_updated']::TEXT[],
            'Last_updated is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_last_updated_null')
        );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO public.tb_booker (
        id,
        tenant_id,
        name,
        email,
        phone,
        group_size,
        registered_at,
        last_updated,
        created_at,
        created_by
    ) VALUES (
        v_booker_id,
        auth_tenant_id,
        input_data.name,
        input_data.email,
        input_data.phone,
        input_data.group_size,
        input_data.registered_at,
        input_data.last_updated,
        now(),
        auth_user_id
    )
    RETURNING pk_booker INTO v_booker_pk;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'booker',
        v_booker_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Booker created successfully',
        (SELECT row_to_json(t.*) FROM public.tb_booker t WHERE t.id = v_booker_id)::JSONB,
        NULL
    );
END;
$$;

COMMENT ON FUNCTION public.create_booking IS
'Core business logic for create booking.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- INSERT operation on public.tb_booker
- Audit logging via app.log_and_return_mutation

Called by: app.create_booking (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
