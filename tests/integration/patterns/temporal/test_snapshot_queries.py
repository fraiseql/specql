"""Integration tests for temporal snapshot pattern queries."""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestSnapshotPatternIntegration:
    """Test temporal snapshot pattern with real SQL generation"""

    def test_snapshot_pattern_generates_valid_sql(self):
        """Test that snapshot pattern generates syntactically valid SQL"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/snapshot")

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

        # Basic SQL structure validation
        assert sql.startswith("# @fraiseql:view")
        assert "CREATE OR REPLACE VIEW tenant.v_contract_snapshot AS" in sql
        assert "SELECT" in sql
        assert "FROM tenant.tb_contract t" in sql
        assert "WHERE t.deleted_at IS NULL" in sql
        assert "ORDER BY pk_contract, effective_date DESC" in sql

        # Temporal-specific validations
        assert "tsrange(" in sql
        assert "LEAD(effective_date)" in sql
        assert "valid_period" in sql
        assert "is_current" in sql
        assert "version_effective_date" in sql
        assert "version_superseded_date" in sql

        # Index validations
        assert "CREATE INDEX IF NOT EXISTS idx_v_contract_snapshot_temporal" in sql
        assert "USING GIST (pk_contract, valid_period)" in sql
        assert "CREATE INDEX IF NOT EXISTS idx_v_contract_snapshot_current" in sql
        assert "WHERE is_current = true" in sql

    def test_snapshot_pattern_current_only_mode(self):
        """Test snapshot pattern with current_only mode"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/snapshot")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_current",
            "pattern": "temporal/snapshot",
            "config": {
                "effective_date_field": "effective_date",
                "end_date_field": "superseded_date",
                "snapshot_mode": "current_only",
                "include_validity_range": False,
            },
        }

        sql = pattern.generate(entity, config)

        # Should include current_only filter
        assert "AND superseded_date IS NULL" in sql
        # Should not include validity range
        assert "tsrange(" not in sql
        # Note: valid_period still appears in comment and index, but not in SELECT

    def test_snapshot_pattern_without_end_date(self):
        """Test snapshot pattern when end_date_field is not specified"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/snapshot")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_snapshot",
            "pattern": "temporal/snapshot",
            "config": {
                "effective_date_field": "effective_date",
                # No end_date_field specified
                "snapshot_mode": "point_in_time",
                "include_validity_range": True,
            },
        }

        sql = pattern.generate(entity, config)

        # Should handle NULL end dates gracefully
        assert "true AS is_current" in sql  # When no end_date_field, all records are current
        # The tsrange should still work with LEAD function for computed end dates

    def test_snapshot_pattern_performance_considerations(self):
        """Test that snapshot pattern includes appropriate performance optimizations"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/snapshot")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
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

        # Should include GIST index for temporal queries
        assert "USING GIST" in sql
        assert "valid_period" in sql

        # Should include partial index for current records
        assert "WHERE is_current = true" in sql

        # Should include ordering for efficient pagination
        assert "ORDER BY pk_contract, effective_date DESC" in sql
