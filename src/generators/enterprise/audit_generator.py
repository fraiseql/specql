"""
Enterprise audit and compliance features for SpecQL

Generates audit trails, compliance reports, and monitoring capabilities
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json


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
        trigger_name = f"audit_trigger_{entity_name.lower()}"

        sql_parts = []

        # Create audit table
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_entity_id ON app.{audit_table_name}(entity_id);
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_tenant_id ON app.{audit_table_name}(tenant_id);
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_changed_at ON app.{audit_table_name}(changed_at);
""")

        # Create audit trigger function
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
        change_reason
    ) VALUES (
        COALESCE(NEW.id, OLD.id),
        COALESCE(NEW.tenant_id, OLD.tenant_id),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN OLD.updated_by ELSE NEW.updated_by END,
        CASE WHEN TG_OP != 'INSERT' THEN row_to_json(OLD)::JSONB ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW)::JSONB ELSE NULL END,
        CASE WHEN TG_OP = 'DELETE' THEN 'Entity deleted' ELSE 'Entity modified' END
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

        # Create trigger
        sql_parts.append(f"""
-- Create audit trigger
DROP TRIGGER IF EXISTS {trigger_name} ON {{ entity.schema }}.tb_{entity_name.lower()};
CREATE TRIGGER {trigger_name}
    AFTER INSERT OR UPDATE OR DELETE ON {{ entity.schema }}.tb_{entity_name.lower()}
    FOR EACH ROW EXECUTE FUNCTION app.{trigger_name}();
""")

        # Create audit query functions
        sql_parts.append(f"""
-- Audit query functions
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

        return "\n".join(sql_parts)

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
