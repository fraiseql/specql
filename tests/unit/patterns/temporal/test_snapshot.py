"""Unit tests for temporal snapshot pattern."""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestSnapshotPattern:
    """Test temporal snapshot pattern generation."""

    def test_contract_snapshot_at_date(self):
        """Test: Retrieve contract state as of specific date"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/snapshot")

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
            "name": "v_contract_snapshot",
            "pattern": "temporal/snapshot",
            "config": {
                "effective_date_field": "effective_date",
                "end_date_field": "superseded_date",
                "snapshot_mode": "point_in_time",
                "include_validity_range": True,
            },
        }

        sql = pattern.generate(entity, config)

        # Validate SQL structure
        assert "tsrange" in sql or "BETWEEN" in sql
        assert "effective_date" in sql
        assert "LEAD(" in sql or "LAG(" in sql  # Window functions
        assert "valid_period" in sql
