-- Core Logic Functions
-- ============================================================================
-- CORE LOGIC: crm.qualify_lead
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    auth_tenant_id UUID,
    input_data app.type_qualify_lead_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := input_data.id;
    v_contact_pk INTEGER;
    v_current_status TEXT;
    v_fk_company INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'qualify_lead: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;
    -- Fetch current values for validation: status = 'lead'
    RAISE NOTICE 'Before SELECT: v_contact_id=%, auth_tenant_id=%', v_contact_id, auth_tenant_id;
    SELECT status INTO v_current_status
    FROM crm.tb_contact WHERE id = v_contact_id AND tenant_id = auth_tenant_id;
    RAISE NOTICE 'After SELECT: v_current_status=%', v_current_status;
    -- Validate: status = 'lead'
    RAISE NOTICE 'Before validation: v_current_status=%', v_current_status;
    IF NOT (v_current_status = 'lead') THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id, 'contact', v_contact_id,
            'CUSTOM', 'failed:validation_error',
            ARRAY[]::TEXT[], 'not_a_lead', NULL, NULL
        );
    END IF;
    -- Update Contact
    UPDATE crm.tb_contact SET status = 'qualified', updated_at = now(), updated_by = auth_user_id
    WHERE id = v_contact_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Qualify Lead completed',
        (SELECT row_to_json(t.*) FROM crm.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

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

-- Trinity Helper Functions



-- ============================================================================
-- Trinity Helper: crm.contact_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION crm.contact_pk(p_identifier TEXT, p_tenant_id UUID)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_contact
    FROM crm.tb_contact
    WHERE (id::TEXT = p_identifier
        OR pk_contact::TEXT = p_identifier)
      AND tenant_id = p_tenant_id
    LIMIT 1;
$$;

COMMENT ON FUNCTION crm.contact_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_contact.';




-- ============================================================================
-- Trinity Helper: crm.contact_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION crm.contact_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM crm.tb_contact
    WHERE pk_contact = p_pk;
$$;

COMMENT ON FUNCTION crm.contact_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';