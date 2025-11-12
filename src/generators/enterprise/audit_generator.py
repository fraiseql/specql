"""
Enterprise audit and compliance features for SpecQL

Generates audit trails, compliance reports, and monitoring capabilities
"""

from typing import Dict, List, Any


class AuditGenerator:
    """Generates audit and compliance features"""

    def __init__(self):
        self.audit_tables = {}
        self.compliance_rules = {}

    def generate_audit_trail(
        self, entity_name: str, fields: List[str], audit_config: Dict[str, Any]
    ) -> str:
        """Generate audit trail functionality for an entity"""
        audit_table_name = f"audit_{entity_name.lower()}"

        # Check if cascade integration is enabled
        include_cascade = audit_config.get("include_cascade", False)

        sql_parts = []

        # Create audit table (EXISTING + NEW cascade columns)
        cascade_columns = ""
        if include_cascade:
            cascade_columns = """,
    -- GraphQL Cascade Integration
    cascade_data JSONB,
    cascade_entities TEXT[]  -- ['Post', 'User', etc.]"""

        sql_parts.append(f"""
-- Audit table for {entity_name}
CREATE TABLE IF NOT EXISTS app.{audit_table_name} (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(){cascade_columns}
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_entity_id ON app.{audit_table_name}(entity_id);
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_tenant_id ON app.{audit_table_name}(tenant_id);
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_changed_at ON app.{audit_table_name}(changed_at);
""")

        if include_cascade:
            sql_parts.append(f"""
-- Cascade-specific indexes
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_cascade_entities
    ON app.{audit_table_name} USING GIN (cascade_entities);
""")

        # Create audit trigger function
        trigger_sql = self.generate_audit_trigger({"name": entity_name, "schema": "{{ entity.schema }}"}, audit_config)
        sql_parts.append(trigger_sql)

        # Create audit query functions
        query_functions_sql = self.generate_audit_query_functions(entity_name, audit_config)
        sql_parts.append(query_functions_sql)

        # Add cascade audit views if cascade is enabled
        if include_cascade:
            views_sql = self.generate_cascade_audit_views(entity_name)
            sql_parts.append(views_sql)

        return "\n".join(sql_parts)

    def generate_audit_trigger(self, entity: dict, audit_config: dict) -> str:
        """Generate audit trigger function with optional cascade capture"""
        entity_name = entity.get("name", "Entity")
        schema_name = entity.get("schema", "{{ entity.schema }}")
        audit_table_name = f"audit_{entity_name.lower()}"
        trigger_name = f"audit_trigger_{entity_name.lower()}"
        include_cascade = audit_config.get("include_cascade", False)

        # Build cascade capture logic
        cascade_columns = ""
        cascade_values = ""
        if include_cascade:
            cascade_columns = ", cascade_data, cascade_entities, cascade_timestamp, cascade_source"
            cascade_values = """,
        NULLIF(current_setting('app.cascade_data', true), '')::jsonb,
        string_to_array(NULLIF(current_setting('app.cascade_entities', true), ''), ','),
        now(),
        NULLIF(current_setting('app.cascade_source', true), '')"""

        sql_parts = []

        sql_parts.append(f"""
-- Audit trigger function for {entity_name}
CREATE OR REPLACE FUNCTION app.{trigger_name}()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert audit record
    INSERT INTO app.{audit_table_name} (
        entity_id,
        tenant_id,
        operation_type,
        changed_by,
        old_values,
        new_values,
        change_reason,
        transaction_id,
        application_name{cascade_columns}
    ) VALUES (
        COALESCE(NEW.id, OLD.id),
        COALESCE(NEW.tenant_id, OLD.tenant_id),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN OLD.updated_by ELSE NEW.updated_by END,
        CASE WHEN TG_OP != 'INSERT' THEN row_to_json(OLD)::JSONB ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW)::JSONB ELSE NULL END,
        CASE WHEN TG_OP = 'DELETE' THEN 'Entity deleted' ELSE 'Entity modified' END,
        txid_current(),
        current_setting('application_name', true){cascade_values}
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger
DROP TRIGGER IF EXISTS {trigger_name} ON {schema_name}.tb_{entity_name.lower()};
CREATE TRIGGER {trigger_name}
    AFTER INSERT OR UPDATE OR DELETE ON {schema_name}.tb_{entity_name.lower()}
    FOR EACH ROW EXECUTE FUNCTION app.{trigger_name}();
""")

        return "\n".join(sql_parts)

    def generate_audit_query_functions(self, entity_name: str, audit_config: dict) -> str:
        """Generate audit query functions with optional cascade support"""
        audit_table_name = f"audit_{entity_name.lower()}"
        include_cascade = audit_config.get("include_cascade", False)

        sql_parts = []

        # Standard audit history query (EXISTING)
        sql_parts.append(f"""
-- Standard audit query (backward compatible)
CREATE OR REPLACE FUNCTION app.get_{entity_name.lower()}_audit_history(
    p_entity_id UUID,
    p_tenant_id UUID,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    audit_id UUID,
    operation_type TEXT,
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE,
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.audit_id,
        a.operation_type,
        a.changed_by,
        a.changed_at,
        a.old_values,
        a.new_values,
        a.change_reason
    FROM app.{audit_table_name} a
    WHERE a.entity_id = p_entity_id
      AND a.tenant_id = p_tenant_id
    ORDER BY a.changed_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

        # NEW: Cascade-aware audit query
        if include_cascade:
            sql_parts.append(f"""
-- Cascade-aware audit query
CREATE OR REPLACE FUNCTION app.get_{entity_name.lower()}_audit_history_with_cascade(
    p_entity_id UUID,
    p_tenant_id UUID,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0,
    p_affected_entity TEXT DEFAULT NULL  -- Filter by entity type in cascade
)
RETURNS TABLE (
    audit_id UUID,
    operation_type TEXT,
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE,
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT,
    cascade_data JSONB,
    cascade_entities TEXT[],
    cascade_source TEXT,
    affected_entity_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.audit_id,
        a.operation_type,
        a.changed_by,
        a.changed_at,
        a.old_values,
        a.new_values,
        a.change_reason,
        a.cascade_data,
        a.cascade_entities,
        a.cascade_source,
        COALESCE(array_length(a.cascade_entities, 1), 0) as affected_entity_count
    FROM app.{audit_table_name} a
    WHERE a.entity_id = p_entity_id
      AND a.tenant_id = p_tenant_id
      AND (
          p_affected_entity IS NULL
          OR p_affected_entity = ANY(a.cascade_entities)
      )
    ORDER BY a.changed_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

            # NEW: Query mutations by affected entity
            sql_parts.append(f"""
-- Find mutations that affected a specific entity type
CREATE OR REPLACE FUNCTION app.get_mutations_affecting_entity(
    p_entity_type TEXT,
    p_tenant_id UUID,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    audit_id UUID,
    primary_entity_id UUID,
    mutation_name TEXT,
    changed_at TIMESTAMP WITH TIME ZONE,
    cascade_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.audit_id,
        a.entity_id as primary_entity_id,
        a.cascade_source as mutation_name,
        a.changed_at,
        a.cascade_data
    FROM app.{audit_table_name} a
    WHERE a.tenant_id = p_tenant_id
      AND p_entity_type = ANY(a.cascade_entities)
    ORDER BY a.changed_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

        return "\n\n".join(sql_parts)

    def generate_cascade_audit_views(self, entity_name: str) -> str:
        """Generate convenient views for cascade audit queries"""
        audit_table_name = f"audit_{entity_name.lower()}"

        return f"""
-- Cascade audit summary view
CREATE OR REPLACE VIEW app.v_{entity_name.lower()}_cascade_audit AS
SELECT
    a.audit_id,
    a.entity_id,
    a.operation_type,
    a.changed_at,
    a.cascade_source as mutation_name,
    a.cascade_entities as affected_entities,
    jsonb_array_length(a.cascade_data->'updated') as entities_updated,
    jsonb_array_length(a.cascade_data->'deleted') as entities_deleted,
    (a.cascade_data->'metadata'->>'affectedCount')::integer as total_affected
FROM app.{audit_table_name} a
WHERE a.cascade_data IS NOT NULL
ORDER BY a.changed_at DESC;

-- Recent cascade mutations view
CREATE OR REPLACE VIEW app.v_{entity_name.lower()}_recent_cascade_mutations AS
SELECT
    a.audit_id,
    a.entity_id,
    a.cascade_source as mutation_name,
    a.changed_at,
    a.cascade_entities,
    a.cascade_data
FROM app.{audit_table_name} a
WHERE a.cascade_data IS NOT NULL
  AND a.changed_at > now() - interval '7 days'
ORDER BY a.changed_at DESC;
"""

    def generate_compliance_monitoring(
        self, entity_name: str, compliance_config: Dict[str, Any]
    ) -> str:
        """Generate compliance monitoring and alerting"""
        monitoring_table = f"compliance_monitoring_{entity_name.lower()}"

        sql_parts = []

        # Compliance monitoring table
        sql_parts.append(f"""
-- Compliance monitoring for {entity_name}
CREATE TABLE IF NOT EXISTS app.{monitoring_table} (
    monitoring_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    check_type TEXT NOT NULL,
    check_result TEXT NOT NULL CHECK (check_result IN ('pass', 'fail', 'warning')),
    check_details JSONB,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monitoring indexes
CREATE INDEX IF NOT EXISTS idx_{monitoring_table}_tenant ON app.{monitoring_table}(tenant_id);
CREATE INDEX IF NOT EXISTS idx_{monitoring_table}_type ON app.{monitoring_table}(check_type);
""")

        # Basic compliance check function
        sql_parts.append(f"""
-- Basic compliance check for {entity_name}
CREATE OR REPLACE FUNCTION app.check_{entity_name.lower()}_basic_compliance(p_tenant_id UUID)
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    details JSONB
) AS $$
DECLARE
    v_total_records BIGINT;
BEGIN
    -- Get basic record count
    SELECT COUNT(*) INTO v_total_records
    FROM {{ entity.schema }}.tb_{entity_name.lower()}
    WHERE tenant_id = p_tenant_id;

    -- Return basic compliance check
    RETURN QUERY SELECT
        'record_count'::TEXT,
        'pass'::TEXT,
        jsonb_build_object('total_records', v_total_records);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

        return "\n".join(sql_parts)

    def generate_enterprise_features(self, entity_name: str, config: Dict[str, Any]) -> str:
        """Generate complete enterprise feature set"""
        sql_parts = []

        # Audit trail
        if config.get("audit", {}).get("enabled", False):
            sql_parts.append(
                self.generate_audit_trail(entity_name, config.get("fields", []), config["audit"])
            )

        # Compliance monitoring
        if config.get("compliance", {}).get("enabled", False):
            sql_parts.append(self.generate_compliance_monitoring(entity_name, config["compliance"]))

        return "\n\n".join(sql_parts)
