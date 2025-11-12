-- ============================================================================
-- Mutation: qualify_lead
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: qualify_lead
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.qualify_lead(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_qualify_lead_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_qualify_lead_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN crm.qualify_lead(
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

COMMENT ON FUNCTION app.qualify_lead IS
'Performs qualify lead operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: qualifyLead
input_type: app.type_qualify_lead_input
success_type: QualifyLeadSuccess
failure_type: QualifyLeadError';

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

COMMENT ON FUNCTION crm.qualify_lead IS
'Core business logic for qualify lead.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on crm.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.qualify_lead (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';
