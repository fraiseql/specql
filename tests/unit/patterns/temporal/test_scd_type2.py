"""Unit tests for SCD Type 2 pattern."""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestSCDType2Pattern:
    """Test SCD Type 2 pattern generation."""

    def test_scd_type2_pattern_generation(self):
        """Test: Generate SCD Type 2 view for customer history"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/scd_type2")

        assert pattern is not None

        entity = {
            "name": "Customer",
            "schema": "tenant",
            "table": "tb_customer",
            "pk_field": "pk_customer",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_customer_scd",
            "pattern": "temporal/scd_type2",
            "config": {
                "effective_date_field": "effective_date",
                "end_date_field": "end_date",
                "is_current_field": "is_current",
                "version_number_field": "version_number",
            },
        }

        sql = pattern.generate(entity, config)

        # Validate SQL structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "surrogate_key" in sql
        assert "natural_key" in sql
        assert "ROW_NUMBER() OVER" in sql
        assert "tsrange" in sql
        assert "valid_period" in sql
        assert "is_current" in sql
        assert "version_number" in sql

        # Validate indexes
        assert "CREATE UNIQUE INDEX" in sql
        assert "WHERE is_current = true" in sql
        assert "USING GIST" in sql

    def test_scd_type2_with_surrogate_key(self):
        """Test: SCD Type 2 with custom surrogate key field"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/scd_type2")

        entity = {
            "name": "Product",
            "schema": "tenant",
            "table": "tb_product",
            "pk_field": "pk_product",
        }

        config = {
            "name": "v_product_scd",
            "pattern": "temporal/scd_type2",
            "config": {
                "surrogate_key_field": "sk_product_version",
                "effective_date_field": "effective_from",
                "end_date_field": "effective_to",
                "is_current_field": "current_flag",
                "version_number_field": "version_num",
            },
        }

        sql = pattern.generate(entity, config)

        # Should use custom surrogate key field
        assert "sk_product_version" in sql
        assert "ROW_NUMBER() OVER (ORDER BY" not in sql  # Should not auto-generate
        assert "effective_from" in sql
        assert "effective_to" in sql
        assert "current_flag" in sql
        assert "version_num" in sql

    def test_scd_type2_defaults(self):
        """Test: SCD Type 2 with default field names"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/scd_type2")

        entity = {
            "name": "Employee",
            "schema": "tenant",
            "table": "tb_employee",
            "pk_field": "pk_employee",
        }

        config = {
            "name": "v_employee_scd",
            "pattern": "temporal/scd_type2",
            "config": {},  # Use all defaults
        }

        sql = pattern.generate(entity, config)

        # Should use default field names
        assert "effective_date" in sql
        assert "end_date" in sql
        assert "is_current" in sql
        assert "version_number" in sql
