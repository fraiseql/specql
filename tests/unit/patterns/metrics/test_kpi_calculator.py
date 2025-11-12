"""Test KPI Calculator Pattern"""

from src.patterns.pattern_registry import PatternRegistry


class TestKPICalculator:
    """Test KPI calculator pattern generation"""

    def test_kpi_calculator_pattern_generation(self):
        """Test: Generate KPI calculator view with utilization metrics"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/kpi_calculator")

        # This should fail initially - pattern doesn't exist yet
        assert pattern is not None

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

        # Validate SQL structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "v_machine_utilization_metrics" in sql
        assert "utilization_rate" in sql
        assert "downtime_hours" in sql
        assert "utilization_rate_pct" in sql
        assert "utilization_rate_status" in sql
        assert "downtime_hours_status" in sql
        assert "calculated_at" in sql
        assert "'30 days'" in sql

        # Validate threshold logic
        assert "CRITICAL" in sql
        assert "WARNING" in sql
        assert "OK" in sql

        # Validate formatting
        assert "ROUND((cm.utilization_rate * 100)::numeric, 2)" in sql

    def test_kpi_calculator_with_materialized_view(self):
        """Test: Generate materialized KPI calculator view"""
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

        # Validate materialized view
        assert "CREATE MATERIALIZED VIEW" in sql
        assert "refresh_v_machine_metrics_materialized" in sql
        assert "REFRESH MATERIALIZED VIEW CONCURRENTLY" in sql

    def test_kpi_calculator_complex_formulas(self):
        """Test: KPI calculator with complex multi-table formulas"""
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

        # Validate complex formula handling
        assert "efficiency_score" in sql
        assert "cost_per_unit" in sql
        assert "total_output - total_waste" in sql
        assert "NULLIF(total_output, 0)" in sql
