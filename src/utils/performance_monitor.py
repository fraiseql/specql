"""
Performance monitoring utilities for tracking code generation pipeline timing

Provides instrumentation for:
- Parse time (YAML → AST)
- Generation time (AST → SQL)
- Template rendering time (individual generators)
- Total pipeline time

Output format: Structured JSON for easy analysis
"""

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""

    timings: Dict[str, float] = field(default_factory=dict)
    operation_counts: Dict[str, int] = field(default_factory=dict)
    categories: Dict[str, Dict[str, float]] = field(default_factory=dict)
    total_time: float = 0.0

    def add_timing(self, operation: str, elapsed: float, category: Optional[str] = None) -> None:
        """
        Add timing for an operation

        Args:
            operation: Name of the operation
            elapsed: Elapsed time in seconds
            category: Optional category for grouping operations
        """
        # Update total timing (aggregate if operation exists)
        if operation in self.timings:
            self.timings[operation] += elapsed
            self.operation_counts[operation] += 1
        else:
            self.timings[operation] = elapsed
            self.operation_counts[operation] = 1

        # Update category if provided
        if category:
            if category not in self.categories:
                self.categories[category] = {}
            if operation in self.categories[category]:
                self.categories[category][operation] += elapsed
            else:
                self.categories[category][operation] = elapsed

        # Update total time
        self.total_time = sum(self.timings.values())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary

        Returns:
            Dictionary representation of metrics
        """
        return {
            "total_time": round(self.total_time, 6),
            "timings": {k: round(v, 6) for k, v in self.timings.items()},
            "operation_counts": self.operation_counts,
            "categories": {
                cat: {op: round(time, 6) for op, time in ops.items()}
                for cat, ops in self.categories.items()
            },
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Convert metrics to JSON string

        Args:
            indent: Optional indentation for pretty printing

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)

    def write_to_file(self, file_path: Path) -> None:
        """
        Write metrics to JSON file

        Args:
            file_path: Path to output file
        """
        file_path.write_text(self.to_json(indent=2))

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics

        Returns:
            Summary statistics including total operations and time
        """
        return {
            "total_operations": sum(self.operation_counts.values()),
            "total_time": round(self.total_time, 6),
            "unique_operations": len(self.timings),
            "categories": list(self.categories.keys()),
        }


class PerformanceMonitor:
    """
    Performance monitoring context manager

    Usage:
        monitor = PerformanceMonitor()

        with monitor.track("parse_yaml"):
            # ... parsing code ...

        metrics = monitor.get_metrics()
        print(metrics.to_json())
    """

    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = PerformanceMetrics()
        self._start_times: Dict[str, float] = {}

    @contextmanager
    def track(self, operation: str, category: Optional[str] = None):
        """
        Track timing for an operation

        Args:
            operation: Name of the operation
            category: Optional category for grouping

        Yields:
            None

        Example:
            with monitor.track("parse_yaml", category="parsing"):
                entity_def = parser.parse(yaml_content)
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            self.metrics.add_timing(operation, elapsed, category)

    def get_metrics(self) -> PerformanceMetrics:
        """
        Get current metrics

        Returns:
            PerformanceMetrics instance
        """
        return self.metrics

    def reset(self) -> None:
        """Reset all metrics"""
        self.metrics = PerformanceMetrics()
        self._start_times.clear()


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get global performance monitor instance (singleton)

    Returns:
        Global PerformanceMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def instrument(operation: str, category: Optional[str] = None, monitor: Optional[PerformanceMonitor] = None):
    """
    Decorator for instrumenting functions with performance tracking

    Args:
        operation: Name of the operation
        category: Optional category for grouping
        monitor: Optional monitor instance (uses global if not provided)

    Returns:
        Decorated function

    Example:
        @instrument("parse_yaml", category="parsing")
        def parse(yaml_content: str) -> EntityDefinition:
            # ... parsing logic ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            perf_monitor = monitor or get_performance_monitor()
            with perf_monitor.track(operation, category):
                return func(*args, **kwargs)
        return wrapper
    return decorator
