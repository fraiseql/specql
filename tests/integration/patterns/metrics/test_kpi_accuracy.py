"""Integration tests for KPI calculator pattern accuracy"""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestKPICalculatorAccuracy:
    """Test KPI calculator pattern with real SQL generation and validation"""

    def test_kpi_calculator_generates_valid_sql(self):
        """Test that KPI calculator generates syntactically valid SQL"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/kpi_calculator")

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_machine_utilization_metrics",
            "pattern": "metrics/kpi_calculator",
            "config": {
                "base_entity": "Machine",
                "time_window": "30 days",
                "metrics": [
                    {
                        "name": "utilization_rate",
                        "formula": "COUNT(DISTINCT a.allocation_date) FILTER (WHERE a.status = 'active') / 30.0",
                        "format": "percentage",
                        "thresholds": {"warning": 0.5, "critical": 0.3},
                    },
                    {
                        "name": "downtime_hours",
                        "formula": "COALESCE(SUM(EXTRACT(EPOCH FROM (m.downtime_end - m.downtime_start)) / 3600), 0)",
                        "format": "decimal",
                        "thresholds": {"warning": 24, "critical": 48},
                    },
                ],
                "refresh_strategy": "real_time",
            },
        }

        sql = pattern.generate(entity, config)

        # Basic SQL structure validation
        assert sql.startswith("-- @fraiseql:view")
        assert "CREATE OR REPLACE VIEW tenant.v_machine_utilization_metrics AS" in sql
        assert "WITH base_data AS" in sql
        assert "calculated_metrics AS" in sql
        assert "SELECT" in sql
        assert "FROM calculated_metrics cm" in sql

        # KPI-specific validations
        assert "utilization_rate" in sql
        assert "downtime_hours" in sql
        assert "utilization_rate_pct" in sql
        assert "utilization_rate_status" in sql
        assert "downtime_hours_status" in sql
        assert "calculated_at" in sql
        assert "'30 days'" in sql

        # Join validation
        assert "LEFT JOIN tenant.tb_allocation a" in sql
        assert "a.fk_machine = m.pk_machine" in sql

        # Threshold validation
        assert "CRITICAL" in sql
        assert "WARNING" in sql
        assert "OK" in sql

        # Formatting validation
        assert "ROUND((cm.utilization_rate * 100)::numeric, 2)" in sql

    def test_kpi_calculator_materialized_view(self):
        """Test materialized view generation"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/kpi_calculator")

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_machine_metrics_materialized",
            "pattern": "metrics/kpi_calculator",
            "config": {
                "base_entity": "Machine",
                "time_window": "7 days",
                "metrics": [
                    {
                        "name": "maintenance_cost",
                        "formula": "COALESCE(SUM(mc.cost), 0)",
                        "format": "currency",
                    }
                ],
                "refresh_strategy": "materialized",
            },
        }

        sql = pattern.generate(entity, config)

        # Materialized view validation
        assert "CREATE MATERIALIZED VIEW tenant.v_machine_metrics_materialized AS" in sql
        assert "CREATE OR REPLACE FUNCTION tenant.refresh_v_machine_metrics_materialized()" in sql
        assert "REFRESH MATERIALIZED VIEW CONCURRENTLY" in sql

    def test_kpi_calculator_complex_formulas(self):
        """Test complex multi-table KPI formulas"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/kpi_calculator")

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_machine_comprehensive_metrics",
            "pattern": "metrics/kpi_calculator",
            "config": {
                "base_entity": "Machine",
                "time_window": "90 days",
                "metrics": [
                    {
                        "name": "efficiency_score",
                        "formula": """
                        CASE
                            WHEN total_output > 0
                            THEN (total_output - total_waste) / total_output::decimal
                            ELSE 0
                        END
                        """,
                        "format": "percentage",
                        "thresholds": {"warning": 0.8, "critical": 0.6},
                    },
                    {
                        "name": "cost_per_unit",
                        "formula": "total_cost / NULLIF(total_output, 0)",
                        "format": "currency",
                    },
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Complex formula validation
        assert "efficiency_score" in sql
        assert "cost_per_unit" in sql
        assert "total_output - total_waste" in sql
        assert "NULLIF(total_output, 0)" in sql
        assert "TO_CHAR(cm.cost_per_unit, 'FM$999,999,999.00')" in sql

    def test_kpi_calculator_index_creation(self):
        """Test that appropriate indexes are created"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/kpi_calculator")

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_machine_metrics",
            "pattern": "metrics/kpi_calculator",
            "config": {
                "base_entity": "Machine",
                "metrics": [
                    {
                        "name": "utilization_rate",
                        "formula": "COUNT(DISTINCT a.allocation_date) / 30.0",
                        "format": "percentage",
                    }
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Index validation
        assert "CREATE INDEX IF NOT EXISTS idx_v_machine_metrics_entity" in sql
        assert "ON tenant.v_machine_metrics(pk_machine)" in sql

    def test_kpi_calculator_comment_generation(self):
        """Test that appropriate comments are generated"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/kpi_calculator")

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_machine_metrics",
            "pattern": "metrics/kpi_calculator",
            "config": {
                "base_entity": "Machine",
                "time_window": "30 days",
                "metrics": [
                    {
                        "name": "utilization_rate",
                        "formula": "COUNT(DISTINCT a.allocation_date) / 30.0",
                        "format": "percentage",
                    }
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Comment validation
        assert "COMMENT ON VIEW tenant.v_machine_metrics IS" in sql
        assert "KPI metrics for Machine over 30 days window." in sql
