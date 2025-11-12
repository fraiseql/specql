"""Integration tests for temporal audit trail pattern queries."""

from src.patterns.pattern_registry import PatternRegistry


class TestAuditTrailPatternIntegration:
    """Test temporal audit trail pattern with real SQL generation"""

    def test_audit_trail_pattern_generates_valid_sql(self):
        """Test that audit trail pattern generates syntactically valid SQL"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/audit_trail")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_contract_audit_trail",
            "pattern": "temporal/audit_trail",
            "config": {
                "audit_table": "tb_contract_audit",
                "change_columns": ["status", "value", "effective_date"],
                "include_user_info": True,
                "include_diff": True,
                "retention_period": "7 years",
            },
        }

        sql = pattern.generate(entity, config)

        # Basic SQL structure validation
        assert sql.startswith("# @fraiseql:view")
        assert "CREATE OR REPLACE VIEW tenant.v_contract_audit_trail AS" in sql
        assert "WITH audit_with_changes AS" in sql
        assert "tb_contract_audit" in sql
        assert "operation" in sql  # INSERT, UPDATE, DELETE
        assert "changed_at" in sql
        assert "old_values" in sql
        assert "new_values" in sql
        assert "changes" in sql  # Computed diff
        assert "time_since_last_change" in sql
        assert "change_sequence" in sql

        # User info validation
        assert "changed_by_email" in sql
        assert "changed_by_name" in sql

        # Index validation
        assert "CREATE INDEX IF NOT EXISTS idx_v_contract_audit_trail_entity" in sql
        assert "CREATE INDEX IF NOT EXISTS idx_v_contract_audit_trail_user" in sql
        assert "CREATE INDEX IF NOT EXISTS idx_v_contract_audit_trail_time" in sql

    def test_audit_trail_pattern_without_user_info(self):
        """Test audit trail pattern without user information"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/audit_trail")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_audit_simple",
            "pattern": "temporal/audit_trail",
            "config": {
                "audit_table": "tb_contract_audit",
                "include_user_info": False,
                "include_diff": False,
                "retention_period": "1 year",
            },
        }

        sql = pattern.generate(entity, config)

        # Should not include user joins
        assert "LEFT JOIN app.tb_user" not in sql
        assert "changed_by_email" not in sql
        assert "changed_by_name" not in sql

        # Should not include diff computation (check for CASE statement)
        assert "CASE" not in sql

        # Should use correct retention period
        assert "INTERVAL '1 year'" in sql
