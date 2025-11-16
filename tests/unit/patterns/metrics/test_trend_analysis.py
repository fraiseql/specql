"""Test Trend Analysis Pattern"""

from src.patterns.pattern_registry import PatternRegistry


class TestTrendAnalysis:
    """Test trend analysis pattern generation"""

    def test_trend_analysis_pattern_generation(self):
        """Test: Generate trend analysis view with moving averages"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/trend_analysis")

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
            "name": "v_machine_trends",
            "pattern": "metrics/trend_analysis",
            "config": {
                "base_metric_view": "v_machine_utilization_metrics",
                "trend_metrics": [
                    {
                        "metric": "utilization_rate",
                        "periods": [7, 30, 90],
                        "smoothing": "simple",
                    },
                    {
                        "metric": "downtime_hours",
                        "periods": [7, 30],
                        "smoothing": "simple",
                    },
                ],
                "trend_detection": {"enabled": True, "sensitivity": "medium"},
            },
        }

        sql = pattern.generate(entity, config)

        # Validate SQL structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "v_machine_trends" in sql
        assert "WITH historical_data AS" in sql
        assert "moving_averages AS" in sql
        assert "utilization_rate_ma7" in sql
        assert "utilization_rate_ma30" in sql
        assert "utilization_rate_ma90" in sql
        assert "downtime_hours_ma7" in sql
        assert "downtime_hours_ma30" in sql
        assert "utilization_rate_trend" in sql
        assert "downtime_hours_trend" in sql
        assert "INCREASING" in sql
        assert "DECREASING" in sql
        assert "STABLE" in sql

    def test_trend_analysis_without_detection(self):
        """Test: Generate trend analysis without trend detection"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/trend_analysis")

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "is_multi_tenant": True,
        }

        config = {
            "name": "v_machine_moving_averages",
            "pattern": "metrics/trend_analysis",
            "config": {
                "base_metric_view": "v_machine_metrics",
                "trend_metrics": [
                    {
                        "metric": "maintenance_cost",
                        "periods": [30, 90],
                        "smoothing": "simple",
                    }
                ],
                "trend_detection": {"enabled": False},
            },
        }

        sql = pattern.generate(entity, config)

        # Validate no trend detection
        assert "CREATE OR REPLACE VIEW" in sql
        assert "maintenance_cost_ma30" in sql
        assert "maintenance_cost_ma90" in sql
        assert "maintenance_cost_trend" not in sql
        assert "INCREASING" not in sql
