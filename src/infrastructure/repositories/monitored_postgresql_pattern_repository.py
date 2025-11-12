"""
Monitored PostgreSQL Pattern Repository

Adds performance monitoring to PostgreSQL pattern repository operations
for Phase 5 pattern library integration.
"""

import time
import logging
from typing import List
from src.infrastructure.repositories.postgresql_pattern_repository import PostgreSQLPatternRepository

logger = logging.getLogger(__name__)


class MonitoredPostgreSQLPatternRepository(PostgreSQLPatternRepository):
    """
    PostgreSQL pattern repository with performance monitoring.

    Tracks query performance during pattern library integration.
    """

    def __init__(self, db_url: str):
        super().__init__(db_url)
        self.performance_stats = {
            'queries_executed': 0,
            'total_query_time': 0.0,
            'slow_queries': [],  # Queries taking > 100ms
            'failed_queries': 0
        }

    def get(self, pattern_name: str):
        """Get pattern with performance monitoring"""
        start_time = time.time()
        try:
            result = super().get(pattern_name)
            self._record_query_time('get', time.time() - start_time)
            return result
        except Exception as e:
            self._record_query_failure('get', str(e))
            raise

    def find_by_category(self, category: str) -> List:
        """Find patterns by category with performance monitoring"""
        start_time = time.time()
        try:
            result = super().find_by_category(category)
            self._record_query_time('find_by_category', time.time() - start_time)
            return result
        except Exception as e:
            self._record_query_failure('find_by_category', str(e))
            raise

    def save(self, pattern):
        """Save pattern with performance monitoring"""
        start_time = time.time()
        try:
            result = super().save(pattern)
            self._record_query_time('save', time.time() - start_time)
            return result
        except Exception as e:
            self._record_query_failure('save', str(e))
            raise

    def list_all(self) -> List:
        """List all patterns with performance monitoring"""
        start_time = time.time()
        try:
            result = super().list_all()
            self._record_query_time('list_all', time.time() - start_time)
            return result
        except Exception as e:
            self._record_query_failure('list_all', str(e))
            raise

    def _record_query_time(self, operation: str, duration: float):
        """Record query performance metrics"""
        self.performance_stats['queries_executed'] += 1
        self.performance_stats['total_query_time'] += duration

        # Track slow queries (> 100ms)
        if duration > 0.1:
            self.performance_stats['slow_queries'].append({
                'operation': operation,
                'duration': duration,
                'timestamp': time.time()
            })

            logger.warning(f"Slow pattern query detected - {operation}: {duration:.3f}s")

    def _record_query_failure(self, operation: str, error: str):
        """Record query failure"""
        self.performance_stats['failed_queries'] += 1
        logger.error(f"Pattern query failed - {operation}: {error}")

    def get_performance_report(self) -> dict:
        """Get performance statistics report"""
        stats = self.performance_stats.copy()

        if stats['queries_executed'] > 0:
            stats['average_query_time'] = stats['total_query_time'] / stats['queries_executed']
        else:
            stats['average_query_time'] = 0.0

        stats['slow_query_count'] = len(stats['slow_queries'])
        stats['success_rate'] = ((stats['queries_executed'] - stats['failed_queries']) /
                                max(stats['queries_executed'], 1)) * 100

        return stats

    def reset_performance_stats(self):
        """Reset performance statistics"""
        self.performance_stats = {
            'queries_executed': 0,
            'total_query_time': 0.0,
            'slow_queries': [],
            'failed_queries': 0
        }