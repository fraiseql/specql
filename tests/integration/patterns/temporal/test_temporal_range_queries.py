"""Integration tests for temporal range pattern."""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestTemporalRangePatternIntegration:
    """Test temporal range pattern with real SQL generation"""

    def test_temporal_range_current_mode(self):
        """Test temporal range pattern with current filter mode"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/temporal_range")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_contract_current",
            "pattern": "temporal/temporal_range",
            "config": {
                "start_date_field": "effective_date",
                "end_date_field": "expiration_date",
                "filter_mode": "current",
            },
        }

        sql = pattern.generate(entity, config)

        # Basic SQL structure validation
        assert "# @fraiseql:view" in sql
        assert "CREATE OR REPLACE VIEW tenant.v_contract_current AS" in sql
        assert "SELECT" in sql
        assert "FROM tenant.tb_contract t" in sql
        assert "WHERE t.deleted_at IS NULL" in sql

        # Temporal range specific validations
        assert "daterange(" in sql
        assert "validity_range" in sql
        assert "is_currently_valid" in sql
        assert "is_future" in sql
        assert "is_historical" in sql

        # Current mode filter
        assert "effective_date <= CURRENT_DATE" in sql
        assert "expiration_date >= CURRENT_DATE" in sql

        # Index validation
        assert "CREATE INDEX" in sql
        assert "USING GIST (validity_range)" in sql

    def test_temporal_range_future_mode(self):
        """Test temporal range pattern with future filter mode"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/temporal_range")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_future",
            "pattern": "temporal/temporal_range",
            "config": {
                "start_date_field": "effective_date",
                "filter_mode": "future",
            },
        }

        sql = pattern.generate(entity, config)

        # Future mode filter
        assert "effective_date > CURRENT_DATE" in sql
        # Should not check end date since not specified
        assert "expiration_date" not in sql

    def test_temporal_range_historical_mode(self):
        """Test temporal range pattern with historical filter mode"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/temporal_range")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_historical",
            "pattern": "temporal/temporal_range",
            "config": {
                "start_date_field": "effective_date",
                "end_date_field": "expiration_date",
                "filter_mode": "historical",
            },
        }

        sql = pattern.generate(entity, config)

        # Historical mode filter
        assert "expiration_date IS NOT NULL" in sql
        assert "expiration_date < CURRENT_DATE" in sql

    def test_temporal_range_custom_mode(self):
        """Test temporal range pattern with custom date range"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/temporal_range")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_q1_2024",
            "pattern": "temporal/temporal_range",
            "config": {
                "start_date_field": "effective_date",
                "end_date_field": "expiration_date",
                "filter_mode": "custom_range",
                "custom_date_range": {
                    "start": "2024-01-01",
                    "end": "2024-04-01",
                },
            },
        }

        sql = pattern.generate(entity, config)

        # Custom range filter
        assert "daterange(effective_date, expiration_date, '[)') &&" in sql
        assert "daterange('2024-01-01'::date, '2024-04-01'::date, '[)')" in sql

    def test_temporal_range_no_end_date(self):
        """Test temporal range pattern with infinite validity (no end date)"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/temporal_range")

        entity = {
            "name": "License",
            "schema": "tenant",
            "table": "tb_license",
            "pk_field": "pk_license",
        }

        config = {
            "name": "v_license_current",
            "pattern": "temporal/temporal_range",
            "config": {
                "start_date_field": "issued_date",
                # No end_date_field specified
                "filter_mode": "current",
            },
        }

        sql = pattern.generate(entity, config)

        # Should handle NULL end dates
        assert "daterange(issued_date, NULL, '[)')" in sql
        assert "issued_date <= CURRENT_DATE" in sql
        # Should not check end date conditions

    def test_temporal_range_index_creation(self):
        """Test that temporal range creates appropriate indexes"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/temporal_range")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_range",
            "pattern": "temporal/temporal_range",
            "config": {
                "start_date_field": "effective_date",
                "end_date_field": "expiration_date",
                "filter_mode": "current",
            },
        }

        sql = pattern.generate(entity, config)

        # GiST index for range operations
        assert "CREATE INDEX IF NOT EXISTS idx_v_contract_range_validity_range" in sql
        assert "ON tenant.v_contract_range USING GIST (validity_range)" in sql

    def test_temporal_range_comment_generation(self):
        """Test that temporal range generates appropriate comments"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/temporal_range")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_current",
            "pattern": "temporal/temporal_range",
            "config": {
                "start_date_field": "effective_date",
                "end_date_field": "expiration_date",
                "filter_mode": "current",
            },
        }

        sql = pattern.generate(entity, config)

        # Comment should be present
        assert "COMMENT ON VIEW tenant.v_contract_current IS" in sql
        assert "Temporal range filtered" in sql
        assert "current" in sql
        assert "WHERE validity_range && daterange" in sql
