"""Unit tests for temporal audit trail pattern."""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestAuditTrailPattern:
    """Test temporal audit trail pattern generation."""

    def test_contract_audit_trail_generation(self):
        """Test: Generate audit trail for contract changes"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/audit_trail")

        # This should fail initially - pattern doesn't exist yet
        assert pattern is not None

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

        # Validate SQL structure contains audit trail components
        assert "CREATE OR REPLACE VIEW tenant.v_contract_audit_trail AS" in sql
        assert "tb_contract_audit" in sql
        assert "operation" in sql  # INSERT, UPDATE, DELETE
        assert "changed_at" in sql
        assert "old_values" in sql
        assert "new_values" in sql
        assert "changes" in sql  # Computed diff
        assert "time_since_last_change" in sql
        assert "change_sequence" in sql
