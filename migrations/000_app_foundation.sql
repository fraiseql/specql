-- Create app schema
CREATE SCHEMA IF NOT EXISTS app;

-- ============================================================================
-- MUTATION RESULT TYPE
-- Standard output type for all mutations
-- ============================================================================
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB
);

COMMENT ON TYPE app.mutation_result IS
  '@fraiseql:type name=MutationResult';

COMMENT ON COLUMN app.mutation_result.id IS
  '@fraiseql:field name=id,type=UUID,description=Entity identifier';

COMMENT ON COLUMN app.mutation_result.updated_fields IS
  '@fraiseql:field name=updatedFields,type=[String],description=Fields that were modified in this mutation';

COMMENT ON COLUMN app.mutation_result.status IS
  'Status: success, failed:*, warning:*';

COMMENT ON COLUMN app.mutation_result.message IS
  '@fraiseql:field name=message,type=String,description=Human-readable success or error message';

COMMENT ON COLUMN app.mutation_result.object_data IS
  '@fraiseql:field name=object,type=JSON,description=Complete entity data after mutation';

COMMENT ON COLUMN app.mutation_result.extra_metadata IS
  '@fraiseql:field name=extra,type=JSON,description=Additional metadata including side effects and impact information';

-- ============================================================================
-- AUDIT LOG TABLE
-- Comprehensive audit trail for all mutations
-- ============================================================================
CREATE TABLE app.tb_mutation_audit_log (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    operation TEXT NOT NULL,        -- INSERT, UPDATE, DELETE, NOOP
    status TEXT NOT NULL,            -- success, failed:*
    updated_fields TEXT[],
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB,
    error_context JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_tenant ON app.tb_mutation_audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_entity ON app.tb_mutation_audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_user ON app.tb_mutation_audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_status ON app.tb_mutation_audit_log(status, created_at DESC);
CREATE INDEX idx_audit_operation ON app.tb_mutation_audit_log(operation, created_at DESC);

COMMENT ON TABLE app.tb_mutation_audit_log IS
  'Comprehensive audit trail for all data mutations across all entities';

-- ============================================================================
-- SHARED UTILITY: app.log_and_return_mutation
-- Used by ALL business schemas for standardized mutation responses with audit logging
-- ============================================================================
CREATE OR REPLACE FUNCTION app.log_and_return_mutation(
    p_tenant_id UUID,
    p_user_id UUID,
    p_entity TEXT,
    p_entity_id UUID,
    p_operation TEXT,          -- 'INSERT', 'UPDATE', 'DELETE', 'NOOP'
    p_status TEXT,             -- 'success', 'failed:*'
    p_updated_fields TEXT[],
    p_message TEXT,
    p_object_data JSONB,
    p_extra_metadata JSONB DEFAULT NULL,
    p_error_context JSONB DEFAULT NULL
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_audit_id UUID := gen_random_uuid();
BEGIN
    -- Insert audit log record
    INSERT INTO app.tb_mutation_audit_log (
        id,
        tenant_id,
        user_id,
        entity_type,
        entity_id,
        operation,
        status,
        updated_fields,
        message,
        object_data,
        extra_metadata,
        error_context,
        created_at
    ) VALUES (
        v_audit_id,
        p_tenant_id,
        p_user_id,
        p_entity,
        p_entity_id,
        p_operation,
        p_status,
        p_updated_fields,
        p_message,
        p_object_data,
        p_extra_metadata,
        p_error_context,
        now()
    );

    -- Return standardized mutation result
    RETURN ROW(
        p_entity_id,
        p_updated_fields,
        p_status,
        p_message,
        p_object_data,
        p_extra_metadata
    )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.log_and_return_mutation IS
  'Audit logger and standardized mutation result builder for all app/core functions';