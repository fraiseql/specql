"""
Unit tests for performance monitoring

Following TDD: RED phase - these tests should FAIL initially
"""

import json
import time
from pathlib import Path

import pytest

from src.utils.performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    get_performance_monitor,
)


class TestPerformanceMonitor:
    """Test performance monitoring context manager"""

    def test_monitor_tracks_elapsed_time(self):
        """RED: Monitor should track elapsed time for operations"""
        monitor = PerformanceMonitor()

        with monitor.track("test_operation"):
            time.sleep(0.01)  # Sleep for 10ms

        metrics = monitor.get_metrics()
        assert "test_operation" in metrics.timings
        assert metrics.timings["test_operation"] >= 0.01
        assert metrics.timings["test_operation"] < 0.02  # Should be < 20ms

    def test_monitor_tracks_nested_operations(self):
        """RED: Monitor should track nested operations"""
        monitor = PerformanceMonitor()

        with monitor.track("outer"):
            time.sleep(0.01)
            with monitor.track("inner1"):
                time.sleep(0.01)
            with monitor.track("inner2"):
                time.sleep(0.01)

        metrics = monitor.get_metrics()
        assert "outer" in metrics.timings
        assert "inner1" in metrics.timings
        assert "inner2" in metrics.timings

        # Outer should be >= sum of inner operations
        outer_time = metrics.timings["outer"]
        inner_sum = metrics.timings["inner1"] + metrics.timings["inner2"]
        assert outer_time >= inner_sum

    def test_monitor_tracks_multiple_operations_same_name(self):
        """RED: Monitor should aggregate multiple operations with same name"""
        monitor = PerformanceMonitor()

        for i in range(3):
            with monitor.track("repeated_op"):
                time.sleep(0.01)

        metrics = monitor.get_metrics()
        # Should have count and total time
        assert metrics.operation_counts["repeated_op"] == 3
        assert metrics.timings["repeated_op"] >= 0.03

    def test_metrics_to_dict(self):
        """RED: Metrics should convert to structured dict"""
        monitor = PerformanceMonitor()

        with monitor.track("operation1"):
            time.sleep(0.01)

        metrics = monitor.get_metrics()
        data = metrics.to_dict()

        assert isinstance(data, dict)
        assert "total_time" in data
        assert "timings" in data
        assert "operation1" in data["timings"]

    def test_metrics_to_json(self):
        """RED: Metrics should serialize to valid JSON"""
        monitor = PerformanceMonitor()

        with monitor.track("operation1"):
            time.sleep(0.01)

        metrics = monitor.get_metrics()
        json_str = metrics.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert "total_time" in data
        assert "timings" in data

    def test_metrics_to_json_pretty(self):
        """RED: Metrics should support pretty-printed JSON"""
        monitor = PerformanceMonitor()

        with monitor.track("operation1"):
            time.sleep(0.01)

        metrics = monitor.get_metrics()
        json_str = metrics.to_json(indent=2)

        # Should contain newlines (pretty printed)
        assert "\n" in json_str
        data = json.loads(json_str)
        assert "timings" in data

    def test_global_performance_monitor(self):
        """RED: Should provide global performance monitor instance"""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)

        # Should be singleton
        monitor2 = get_performance_monitor()
        assert monitor is monitor2

    def test_monitor_reset(self):
        """RED: Monitor should support resetting metrics"""
        monitor = PerformanceMonitor()

        with monitor.track("operation1"):
            time.sleep(0.01)

        monitor.reset()
        metrics = monitor.get_metrics()

        assert len(metrics.timings) == 0
        assert metrics.total_time == 0.0

    def test_monitor_with_categories(self):
        """RED: Monitor should support categorizing operations"""
        monitor = PerformanceMonitor()

        with monitor.track("parse", category="parsing"):
            time.sleep(0.01)

        with monitor.track("generate", category="generation"):
            time.sleep(0.01)

        metrics = monitor.get_metrics()
        data = metrics.to_dict()

        assert "categories" in data
        assert "parsing" in data["categories"]
        assert "generation" in data["categories"]
        assert data["categories"]["parsing"]["parse"] >= 0.01

    def test_monitor_error_handling(self):
        """RED: Monitor should handle errors gracefully"""
        monitor = PerformanceMonitor()

        with pytest.raises(ValueError):
            with monitor.track("failing_operation"):
                raise ValueError("Test error")

        # Should still have recorded the operation
        metrics = monitor.get_metrics()
        assert "failing_operation" in metrics.timings

    def test_performance_metrics_summary(self):
        """RED: Metrics should provide summary statistics"""
        monitor = PerformanceMonitor()

        with monitor.track("parse"):
            time.sleep(0.01)
        with monitor.track("generate"):
            time.sleep(0.02)

        metrics = monitor.get_metrics()
        summary = metrics.get_summary()

        assert "total_operations" in summary
        assert summary["total_operations"] == 2
        assert "total_time" in summary
        assert summary["total_time"] >= 0.03


class TestPerformanceMetrics:
    """Test PerformanceMetrics data structure"""

    def test_metrics_initialization(self):
        """RED: PerformanceMetrics should initialize with default values"""
        metrics = PerformanceMetrics()

        assert metrics.total_time == 0.0
        assert isinstance(metrics.timings, dict)
        assert isinstance(metrics.operation_counts, dict)
        assert isinstance(metrics.categories, dict)

    def test_metrics_add_timing(self):
        """RED: PerformanceMetrics should track individual timings"""
        metrics = PerformanceMetrics()

        metrics.add_timing("operation1", 0.123)
        metrics.add_timing("operation2", 0.456)

        assert metrics.timings["operation1"] == 0.123
        assert metrics.timings["operation2"] == 0.456

    def test_metrics_add_timing_aggregates(self):
        """RED: Adding same operation multiple times should aggregate"""
        metrics = PerformanceMetrics()

        metrics.add_timing("operation1", 0.1)
        metrics.add_timing("operation1", 0.2)
        metrics.add_timing("operation1", 0.3)

        assert abs(metrics.timings["operation1"] - 0.6) < 0.0001
        assert metrics.operation_counts["operation1"] == 3

    def test_metrics_add_categorized_timing(self):
        """RED: Metrics should support categorized timings"""
        metrics = PerformanceMetrics()

        metrics.add_timing("parse", 0.1, category="parsing")
        metrics.add_timing("generate", 0.2, category="generation")

        assert "parsing" in metrics.categories
        assert metrics.categories["parsing"]["parse"] == 0.1
        assert metrics.categories["generation"]["generate"] == 0.2

    def test_metrics_calculate_total_time(self):
        """RED: Metrics should calculate total time correctly"""
        metrics = PerformanceMetrics()

        metrics.add_timing("op1", 0.1)
        metrics.add_timing("op2", 0.2)
        metrics.add_timing("op3", 0.3)

        # Total time should be automatically updated
        assert abs(metrics.total_time - 0.6) < 0.0001


class TestPerformanceInstrumentation:
    """Test instrumentation integration points"""

    def test_instrumentation_decorator(self):
        """RED: Should provide decorator for instrumenting functions"""
        from src.utils.performance_monitor import instrument

        monitor = PerformanceMonitor()

        @instrument("test_function", monitor=monitor)
        def test_function():
            time.sleep(0.01)
            return "result"

        result = test_function()
        assert result == "result"

        metrics = monitor.get_metrics()
        assert "test_function" in metrics.timings
        assert metrics.timings["test_function"] >= 0.01

    def test_instrumentation_with_category(self):
        """RED: Decorator should support categories"""
        from src.utils.performance_monitor import instrument

        monitor = PerformanceMonitor()

        @instrument("test_function", category="testing", monitor=monitor)
        def test_function():
            time.sleep(0.01)
            return "result"

        test_function()

        metrics = monitor.get_metrics()
        data = metrics.to_dict()
        assert "testing" in data["categories"]


class TestMetricsOutput:
    """Test metrics output formats"""

    def test_metrics_output_to_file(self, tmp_path):
        """RED: Metrics should support writing to file"""
        monitor = PerformanceMonitor()

        with monitor.track("operation1"):
            time.sleep(0.01)

        metrics = monitor.get_metrics()
        output_file = tmp_path / "metrics.json"

        metrics.write_to_file(output_file)

        assert output_file.exists()

        # Should be valid JSON
        data = json.loads(output_file.read_text())
        assert "timings" in data
        assert "operation1" in data["timings"]

    def test_metrics_output_structured_format(self):
        """RED: Metrics should output in structured format for pipeline"""
        monitor = PerformanceMonitor()

        # Simulate pipeline operations
        with monitor.track("total_pipeline"):
            with monitor.track("parse_yaml", category="parsing"):
                time.sleep(0.01)

            with monitor.track("generate_schema", category="generation"):
                time.sleep(0.01)
                with monitor.track("table_ddl", category="template_rendering"):
                    time.sleep(0.005)
                with monitor.track("helpers", category="template_rendering"):
                    time.sleep(0.005)

            with monitor.track("generate_frontend", category="generation"):
                time.sleep(0.01)

        metrics = monitor.get_metrics()
        data = metrics.to_dict()

        # Should have structured output
        assert "categories" in data
        assert "parsing" in data["categories"]
        assert "generation" in data["categories"]
        assert "template_rendering" in data["categories"]

        # Should have timing breakdown
        parsing_time = data["categories"]["parsing"]["parse_yaml"]
        generation_time = sum(data["categories"]["generation"].values())
        template_time = sum(data["categories"]["template_rendering"].values())

        assert parsing_time >= 0.01
        assert generation_time >= 0.02
        assert template_time >= 0.01
