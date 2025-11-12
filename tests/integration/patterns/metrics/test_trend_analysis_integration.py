"""Integration tests for trend analysis pattern"""

from src.patterns.pattern_registry import PatternRegistry


class TestTrendAnalysisIntegration:
    """Test trend analysis pattern with real SQL generation"""

    def test_trend_analysis_generates_valid_sql(self):
        """Test that trend analysis generates syntactically valid SQL"""
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
            "name": "v_machine_trends",
            "pattern": "metrics/trend_analysis",
            "config": {
                "base_metric_view": "v_machine_utilization_metrics",
                "trend_metrics": [
                    {"metric": "utilization_rate", "periods": [7, 30, 90], "smoothing": "simple"},
                    {"metric": "downtime_hours", "periods": [7, 30], "smoothing": "simple"},
                ],
                "trend_detection": {"enabled": True, "sensitivity": "medium"},
            },
        }

        sql = pattern.generate(entity, config)

        # Basic SQL structure validation
        assert sql.startswith("-- @fraiseql:view")
        assert "CREATE OR REPLACE VIEW tenant.v_machine_trends AS" in sql
        assert "WITH historical_data AS" in sql
        assert "moving_averages AS" in sql
        assert "SELECT" in sql
        assert "FROM moving_averages" in sql
        assert "ORDER BY metric_date DESC" in sql

        # Trend-specific validations
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
        assert "1.1" in sql  # medium sensitivity threshold
        assert "0.9" in sql

    def test_trend_analysis_without_detection(self):
        """Test trend analysis without trend detection"""
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
                    {"metric": "maintenance_cost", "periods": [30, 90], "smoothing": "simple"}
                ],
                "trend_detection": {"enabled": False},
            },
        }

        sql = pattern.generate(entity, config)

        # Validate moving averages without trend detection
        assert "CREATE OR REPLACE VIEW tenant.v_machine_moving_averages AS" in sql
        assert "maintenance_cost_ma30" in sql
        assert "maintenance_cost_ma90" in sql
        assert "maintenance_cost_trend" not in sql
        assert "INCREASING" not in sql
        assert "ROWS BETWEEN 29 PRECEDING" in sql  # 30-day window
        assert "ROWS BETWEEN 89 PRECEDING" in sql  # 90-day window

    def test_trend_analysis_different_sensitivities(self):
        """Test trend analysis with different sensitivity levels"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("metrics/trend_analysis")

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "is_multi_tenant": True,
        }

        # Test high sensitivity
        config_high = {
            "name": "v_machine_trends_high",
            "pattern": "metrics/trend_analysis",
            "config": {
                "base_metric_view": "v_machine_metrics",
                "trend_metrics": [
                    {"metric": "utilization_rate", "periods": [7, 30], "smoothing": "simple"}
                ],
                "trend_detection": {"enabled": True, "sensitivity": "high"},
            },
        }

        sql_high = pattern.generate(entity, config_high)
        assert "1.2" in sql_high  # high sensitivity threshold
        assert "0.8" in sql_high

        # Test low sensitivity
        config_low = {
            "name": "v_machine_trends_low",
            "pattern": "metrics/trend_analysis",
            "config": {
                "base_metric_view": "v_machine_metrics",
                "trend_metrics": [
                    {"metric": "utilization_rate", "periods": [7, 30], "smoothing": "simple"}
                ],
                "trend_detection": {"enabled": True, "sensitivity": "low"},
            },
        }

        sql_low = pattern.generate(entity, config_low)
        assert "1.05" in sql_low  # low sensitivity threshold
        assert "0.95" in sql_low

    def test_trend_analysis_index_creation(self):
        """Test that appropriate indexes are created"""
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
            "name": "v_machine_trends",
            "pattern": "metrics/trend_analysis",
            "config": {
                "base_metric_view": "v_machine_metrics",
                "trend_metrics": [
                    {"metric": "utilization_rate", "periods": [7, 30], "smoothing": "simple"}
                ],
                "trend_detection": {"enabled": True, "sensitivity": "medium"},
            },
        }

        sql = pattern.generate(entity, config)

        # Index validation
        assert "CREATE INDEX IF NOT EXISTS idx_v_machine_trends_date" in sql
        assert "ON tenant.v_machine_trends(metric_date DESC)" in sql

    def test_trend_analysis_comment_generation(self):
        """Test that appropriate comments are generated"""
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
            "name": "v_machine_trends",
            "pattern": "metrics/trend_analysis",
            "config": {
                "base_metric_view": "v_machine_utilization_metrics",
                "trend_metrics": [
                    {"metric": "utilization_rate", "periods": [7, 30], "smoothing": "simple"}
                ],
                "trend_detection": {"enabled": True, "sensitivity": "medium"},
            },
        }

        sql = pattern.generate(entity, config)

        # Comment validation
        assert "COMMENT ON VIEW tenant.v_machine_trends IS" in sql
        assert "Trend analysis with moving averages for v_machine_utilization_metrics" in sql
        assert "Trend detection sensitivity: medium" in sql
