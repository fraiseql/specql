"""Integration tests for SCD Type 2 pattern."""

from src.patterns.pattern_registry import PatternRegistry


class TestSCDType2PatternIntegration:
    """Test SCD Type 2 pattern with real SQL generation"""

    def test_scd_type2_pattern_generates_valid_sql(self):
        """Test that SCD Type 2 pattern generates syntactically valid SQL"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/scd_type2")

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

        # Basic SQL structure validation
        assert "# @fraiseql:view" in sql
        assert "CREATE OR REPLACE VIEW tenant.v_customer_scd AS" in sql
        assert "SELECT" in sql
        assert "FROM tenant.tb_customer t" in sql
        assert "WHERE t.deleted_at IS NULL" in sql

        # SCD Type 2 specific validations
        assert "surrogate_key" in sql
        assert "natural_key" in sql
        assert "ROW_NUMBER() OVER" in sql
        assert "tsrange(" in sql
        assert "valid_period" in sql
        assert "is_current" in sql
        assert "version_number" in sql

        # Index validations
        assert "CREATE UNIQUE INDEX" in sql
        assert "WHERE is_current = true" in sql
        assert "CREATE INDEX" in sql
        assert "USING GIST" in sql

    def test_scd_type2_with_surrogate_key_field(self):
        """Test SCD Type 2 with custom surrogate key field"""
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

        # Should use custom surrogate key
        assert "sk_product_version" in sql
        assert "ROW_NUMBER() OVER (ORDER BY" not in sql  # Should not auto-generate

        # Should use custom field names
        assert "effective_from" in sql
        assert "effective_to" in sql
        assert "current_flag" in sql
        assert "version_num" in sql

        # Indexes should use custom field names
        assert "WHERE current_flag = true" in sql

    def test_scd_type2_defaults(self):
        """Test SCD Type 2 with default field names"""
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
            "config": {
                "effective_date_field": "effective_date",
                "end_date_field": "end_date",
                "is_current_field": "is_current",
                "version_number_field": "version_number",
            },  # Explicit defaults
        }

        sql = pattern.generate(entity, config)

        # Should use default field names
        assert "effective_date" in sql
        assert "end_date" in sql
        assert "is_current" in sql
        assert "version_number" in sql

        # Should auto-generate surrogate key
        assert "ROW_NUMBER() OVER (ORDER BY pk_employee, effective_date)" in sql

    def test_scd_type2_index_creation(self):
        """Test that SCD Type 2 creates appropriate indexes"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/scd_type2")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
        }

        config = {
            "name": "v_contract_scd",
            "pattern": "temporal/scd_type2",
            "config": {
                "effective_date_field": "effective_date",
                "end_date_field": "end_date",
                "is_current_field": "is_current",
            },
        }

        sql = pattern.generate(entity, config)

        # Unique index on current versions
        assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_v_contract_scd_current_unique" in sql
        assert "ON tenant.v_contract_scd(pk_contract)" in sql
        assert "WHERE is_current = true" in sql

        # Temporal range index
        assert "CREATE INDEX IF NOT EXISTS idx_v_contract_scd_temporal_lookup" in sql
        assert "ON tenant.v_contract_scd USING GIST (pk_contract, valid_period)" in sql

    def test_scd_type2_comment_generation(self):
        """Test that SCD Type 2 generates appropriate comments"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("temporal/scd_type2")

        entity = {
            "name": "Customer",
            "schema": "tenant",
            "table": "tb_customer",
            "pk_field": "pk_customer",
        }

        config = {
            "name": "v_customer_scd",
            "pattern": "temporal/scd_type2",
            "config": {},
        }

        sql = pattern.generate(entity, config)

        # Comment should be present
        assert "COMMENT ON VIEW tenant.v_customer_scd IS" in sql
        assert "SCD Type 2 view" in sql
        assert "full version history" in sql
        assert "WHERE is_current = true" in sql
