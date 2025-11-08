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

        # Generate shared utility functions
        utility_functions = self._generate_shared_utilities()
        parts.append(utility_functions)

        return "\n".join(parts)

    def _generate_mutation_result_type(self) -> str:
        """Generate the standard mutation_result composite type"""
        return """-- ============================================================================
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
  '@fraiseql:field name=extra,type=JSON,description=Additional metadata including side effects and impact information';"""

    def _generate_shared_utilities(self) -> str:
        """Generate shared utility functions used across all schemas"""
        functions = []

        # Log and return mutation utility
        functions.append(self._generate_log_and_return_mutation())

        # Future: Add other shared utilities like build_error_response, emit_event, etc.

        return "\n\n".join(functions)

    def _generate_log_and_return_mutation(self) -> str:
        """Generate the shared log_and_return_mutation utility function"""
        return """-- ============================================================================
-- SHARED UTILITY: app.log_and_return_mutation
-- Used by ALL business schemas for standardized mutation responses
-- ============================================================================
CREATE OR REPLACE FUNCTION app.log_and_return_mutation(
    p_tenant_id UUID,
    p_user_id UUID,
    p_entity TEXT,
    p_entity_id UUID,
    p_operation TEXT,
    p_status TEXT,
    p_updated_fields TEXT[],
    p_message TEXT,
    p_object_data JSONB,
    p_extra_metadata JSONB DEFAULT NULL
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_result app.mutation_result;
BEGIN
    -- TODO: Insert into audit log table (future Phase)
    -- INSERT INTO app.tb_mutation_log (...)

    -- Build standardized result
    v_result.id := p_entity_id;
    v_result.updated_fields := p_updated_fields;
    v_result.status := p_status;
    v_result.message := p_message;
    v_result.object_data := p_object_data;
    v_result.extra_metadata := COALESCE(p_extra_metadata, '{}'::jsonb);

    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION app.log_and_return_mutation IS
  '@fraiseql:utility Used by mutations to build standardized responses';"""
