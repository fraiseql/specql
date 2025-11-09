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
'Standard mutation result for all operations.
Returns entity data, status, and optional metadata.

@fraiseql:composite
name: MutationResult
tier: 1
storage: composite';

COMMENT ON COLUMN app.mutation_result.id IS
'Unique identifier of the affected entity.

@fraiseql:field
name: id
type: UUID!
required: true';

COMMENT ON COLUMN app.mutation_result.updated_fields IS
'Fields that were modified in this mutation.

@fraiseql:field
name: updatedFields
type: [String]
required: false';

COMMENT ON COLUMN app.mutation_result.status IS
'Operation status indicator.
Values: success, failed:error_code

@fraiseql:field
name: status
type: String!
required: true';

COMMENT ON COLUMN app.mutation_result.message IS
'Human-readable success or error message.

@fraiseql:field
name: message
type: String
required: false';

COMMENT ON COLUMN app.mutation_result.object_data IS
'Complete entity data after mutation.

@fraiseql:field
name: object
type: JSON
required: false';

COMMENT ON COLUMN app.mutation_result.extra_metadata IS
'Additional metadata including side effects and impact information.

@fraiseql:field
name: extra
type: JSON
required: false';

-- ============================================================================
-- AUDIT LOG TABLE: app.tb_mutation_audit_log
-- Comprehensive audit trail for all mutations across the application
-- ============================================================================
CREATE TABLE app.tb_mutation_audit_log (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    tenant_id UUID NOT NULL,

    -- User context
    user_id UUID,

    -- Entity context
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,

    -- Operation details
    operation TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE', 'NOOP'
    status TEXT NOT NULL,     -- 'success', 'failed:*'

    -- Data changes
    updated_fields TEXT[],
    message TEXT,
    object_data JSONB,

    -- Additional context
    extra_metadata JSONB,
    error_context JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_mutation_audit_tenant ON app.tb_mutation_audit_log(tenant_id);
CREATE INDEX idx_mutation_audit_entity ON app.tb_mutation_audit_log(entity_type, entity_id);
CREATE INDEX idx_mutation_audit_created ON app.tb_mutation_audit_log(created_at);

-- Comments
COMMENT ON TABLE app.tb_mutation_audit_log IS 'Comprehensive audit trail for all mutations across the application';
COMMENT ON COLUMN app.tb_mutation_audit_log.id IS 'Unique identifier for this audit log entry';
COMMENT ON COLUMN app.tb_mutation_audit_log.tenant_id IS 'Tenant that performed the operation';
COMMENT ON COLUMN app.tb_mutation_audit_log.user_id IS 'User who performed the operation';
COMMENT ON COLUMN app.tb_mutation_audit_log.entity_type IS 'Type of entity being mutated (e.g., contact, company)';
COMMENT ON COLUMN app.tb_mutation_audit_log.entity_id IS 'ID of the entity being mutated';
COMMENT ON COLUMN app.tb_mutation_audit_log.operation IS 'Type of operation: INSERT, UPDATE, DELETE, NOOP';
COMMENT ON COLUMN app.tb_mutation_audit_log.status IS 'Operation status: success or failed:*';
COMMENT ON COLUMN app.tb_mutation_audit_log.updated_fields IS 'Array of field names that were modified';
COMMENT ON COLUMN app.tb_mutation_audit_log.message IS 'Human-readable success or error message';
COMMENT ON COLUMN app.tb_mutation_audit_log.object_data IS 'Complete entity data after the mutation';
COMMENT ON COLUMN app.tb_mutation_audit_log.extra_metadata IS 'Additional metadata including side effects';
COMMENT ON COLUMN app.tb_mutation_audit_log.error_context IS 'Error context information for debugging';
COMMENT ON COLUMN app.tb_mutation_audit_log.created_at IS 'Timestamp when the audit log entry was created';

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