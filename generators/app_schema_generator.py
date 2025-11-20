"""
App Schema Foundation Generator (Team B)
Generates the app.* schema foundation including shared utility functions
"""

from jinja2 import Environment, FileSystemLoader


class AppSchemaGenerator:
    """Generates app.* schema foundation with shared utilities"""

    def __init__(self, templates_dir: str = "templates/sql"):
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self._generated = False  # Ensure foundation is generated only once

    def generate_app_foundation(self) -> str:
        """
        Generate the complete app.* schema foundation

        Returns:
            SQL for app schema creation and shared utilities
        """
        if self._generated:
            return ""  # Already generated

        self._generated = True

        parts = []

        # Create app schema
        parts.append("-- Create app schema")
        parts.append("CREATE SCHEMA IF NOT EXISTS app;")
        parts.append("")

        # Generate mutation_result type
        mutation_result_type = self._generate_mutation_result_type()
        parts.append(mutation_result_type)
        parts.append("")

        # Generate audit log table
        audit_table = self._generate_audit_log_table()
        parts.append(audit_table)
        parts.append("")

        # Generate shared utility functions
        utility_functions = self._generate_shared_utilities()
        parts.append(utility_functions)

        return "\n".join(parts)

    def _generate_mutation_result_type(self) -> str:
        """Generate the standard mutation_result composite type"""
        template = self.env.get_template("mutation_result_type.sql.j2")
        return template.render()

    def _generate_audit_log_table(self) -> str:
        """Generate the mutation audit log table"""
        return """-- ============================================================================
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
COMMENT ON COLUMN app.tb_mutation_audit_log.created_at IS 'Timestamp when the audit log entry was created';"""

    def _generate_shared_utilities(self) -> str:
        """Generate shared utility functions used across all schemas"""
        functions = []

        # Log and return mutation utility
        functions.append(self._generate_log_and_return_mutation())

        # Future: Add other shared utilities like build_error_response, emit_event, etc.

        return "\n\n".join(functions)

    def _generate_log_and_return_mutation(self) -> str:
        """Generate the shared log_and_return_mutation utility function with audit logging"""
        return """-- ============================================================================
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
  'Audit logger and standardized mutation result builder for all app/core functions';"""
