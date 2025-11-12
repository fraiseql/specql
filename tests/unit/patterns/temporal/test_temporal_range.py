"""Unit tests for temporal range pattern."""

from src.patterns.pattern_registry import PatternRegistry


class TestTemporalRangePattern:
    """Test temporal range pattern generation."""

    def test_temporal_range_current_mode(self):
        """Test: Generate view for currently valid records"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/temporal_range")

        assert pattern is not None

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

        # Validate SQL structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "daterange" in sql
        assert "validity_range" in sql
        assert "is_currently_valid" in sql
        assert "is_future" in sql
        assert "is_historical" in sql

        # Should filter for current records
        assert "effective_date <= CURRENT_DATE" in sql
        assert "expiration_date >= CURRENT_DATE" in sql

        # Validate indexes
        assert "CREATE INDEX" in sql
        assert "USING GIST" in sql

    def test_temporal_range_future_mode(self):
        """Test: Generate view for future records"""
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

        # Should filter for future records
        assert "effective_date > CURRENT_DATE" in sql
        # Should not have end_date conditions since not specified
        assert "expiration_date" not in sql

    def test_temporal_range_historical_mode(self):
        """Test: Generate view for historical records"""
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

        # Should filter for historical records
        assert "expiration_date IS NOT NULL" in sql
        assert "expiration_date < CURRENT_DATE" in sql

    def test_temporal_range_custom_mode(self):
        """Test: Generate view with custom date range"""
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

        # Should use custom range filter
        assert "daterange(effective_date, expiration_date, '[)') &&" in sql
        assert "daterange('2024-01-01'::date, '2024-04-01'::date, '[)')" in sql

    def test_temporal_range_no_end_date(self):
        """Test: Generate view with infinite validity (no end date)"""
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
        # Should not check end date since it's NULL
