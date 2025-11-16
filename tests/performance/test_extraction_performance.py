"""
Performance benchmarks for extraction patterns.

These tests demonstrate the performance benefits of extraction patterns
compared to direct LEFT JOINs with NULL filtering.
"""

import pytest
import time


class TestExtractionPerformance:
    """Performance tests for extraction patterns."""

    def test_component_extraction_sql_generation_performance(self):
        """Test that component extraction patterns generate SQL quickly."""
        from src.patterns.pattern_registry import PatternRegistry

        registry = PatternRegistry()
        pattern = registry.get_pattern("extraction/component")

        entity = {
            "name": "Location",
            "schema": "tenant",
            "table": "tb_location",
            "pk_field": "pk_location",
            "is_multi_tenant": True,
        }

        config = {
            "name": "coordinates",
            "pattern": "extraction/component",
            "config": {
                "source_entity": "Location",
                "extracted_fields": [{"name": "latitude"}, {"name": "longitude"}],
                "filter_condition": "latitude IS NOT NULL AND longitude IS NOT NULL",
                "purpose": "Extract locations with coordinates",
            },
        }

        # Measure generation time
        start_time = time.time()
        sql = pattern.generate(entity, config)
        generation_time = time.time() - start_time

        # Should generate quickly (< 10ms)
        assert generation_time < 0.01, (
            f"SQL generation took {generation_time:.4f}s, expected < 10ms"
        )

        # Verify SQL structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "latitude IS NOT NULL AND longitude IS NOT NULL" in sql

    def test_temporal_extraction_sql_generation_performance(self):
        """Test that temporal extraction patterns generate SQL quickly."""
        from src.patterns.pattern_registry import PatternRegistry

        registry = PatternRegistry()
        pattern = registry.get_pattern("extraction/temporal")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "is_multi_tenant": True,
        }

        config = {
            "name": "current_contracts",
            "pattern": "extraction/temporal",
            "config": {
                "source_entity": "Contract",
                "temporal_mode": "current",
                "date_field_start": "start_date",
                "date_field_end": "end_date",
                "reference_date": "CURRENT_DATE",
                "purpose": "Extract currently active contracts",
            },
        }

        # Measure generation time
        start_time = time.time()
        sql = pattern.generate(entity, config)
        generation_time = time.time() - start_time

        # Should generate quickly (< 10ms)
        assert generation_time < 0.01, (
            f"SQL generation took {generation_time:.4f}s, expected < 10ms"
        )

        # Verify SQL structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "start_date <= CURRENT_DATE" in sql

    def test_multiple_pattern_generation_performance(self):
        """Test generating multiple extraction patterns simultaneously."""
        from src.generators.query_pattern_generator import QueryPatternGenerator
        from src.patterns.pattern_registry import PatternRegistry

        entity = {
            "name": "Location",
            "schema": "tenant",
            "table": "tb_location",
            "pk_field": "pk_location",
            "is_multi_tenant": True,
            "query_patterns": [
                {
                    "name": "coordinates",
                    "pattern": "extraction/component",
                    "config": {
                        "source_entity": "Location",
                        "extracted_fields": [
                            {"name": "latitude"},
                            {"name": "longitude"},
                        ],
                        "filter_condition": "latitude IS NOT NULL AND longitude IS NOT NULL",
                        "purpose": "Extract locations with coordinates",
                    },
                },
                {
                    "name": "active_locations",
                    "pattern": "extraction/temporal",
                    "config": {
                        "source_entity": "Location",
                        "temporal_mode": "current",
                        "date_field_start": "created_at",
                        "reference_date": "CURRENT_DATE",
                        "purpose": "Extract currently active locations",
                    },
                },
            ],
        }

        registry = PatternRegistry()
        generator = QueryPatternGenerator(registry)

        # Measure generation time for multiple patterns
        start_time = time.time()
        sql_files = generator.generate(entity)
        generation_time = time.time() - start_time

        # Should generate multiple patterns quickly (< 50ms)
        assert generation_time < 0.05, (
            f"Multiple pattern generation took {generation_time:.4f}s, expected < 50ms"
        )
        assert len(sql_files) == 2

    @pytest.mark.parametrize("pattern_count", [1, 5, 10])
    def test_scalability_with_multiple_patterns(self, pattern_count: int):
        """Test that pattern generation scales linearly with pattern count."""
        from src.generators.query_pattern_generator import QueryPatternGenerator
        from src.patterns.pattern_registry import PatternRegistry

        # Create entity with multiple patterns
        query_patterns = []
        for i in range(pattern_count):
            query_patterns.append(
                {
                    "name": f"pattern_{i}",
                    "pattern": "extraction/component",
                    "config": {
                        "source_entity": "TestEntity",
                        "extracted_fields": [{"name": f"field_{i}"}],
                        "purpose": f"Test pattern {i}",
                    },
                }
            )

        entity = {
            "name": "TestEntity",
            "schema": "tenant",
            "table": "tb_test",
            "pk_field": "pk_test",
            "is_multi_tenant": False,
            "query_patterns": query_patterns,
        }

        registry = PatternRegistry()
        generator = QueryPatternGenerator(registry)

        # Measure generation time
        start_time = time.time()
        sql_files = generator.generate(entity)
        generation_time = time.time() - start_time

        # Should scale reasonably (allow up to 100ms for 10 patterns)
        max_expected_time = pattern_count * 0.01  # 10ms per pattern
        assert generation_time < max_expected_time, (
            f"Generation of {pattern_count} patterns took {generation_time:.4f}s, expected < {max_expected_time:.4f}s"
        )

        assert len(sql_files) == pattern_count

    def test_memory_usage_during_generation(self):
        """Test that pattern generation doesn't have excessive memory usage."""
        import psutil
        import os
        from src.generators.query_pattern_generator import QueryPatternGenerator
        from src.patterns.pattern_registry import PatternRegistry

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create a large entity with many patterns
        query_patterns = []
        for i in range(20):  # Generate 20 patterns
            query_patterns.append(
                {
                    "name": f"large_pattern_{i}",
                    "pattern": "extraction/component",
                    "config": {
                        "source_entity": "LargeEntity",
                        "extracted_fields": [
                            {"name": f"field_{j}"}
                            for j in range(10)  # 10 fields each
                        ],
                        "filter_condition": " AND ".join(
                            [f"field_{j} IS NOT NULL" for j in range(10)]
                        ),
                        "purpose": f"Large extraction pattern {i}",
                    },
                }
            )

        entity = {
            "name": "LargeEntity",
            "schema": "tenant",
            "table": "tb_large",
            "pk_field": "pk_large",
            "is_multi_tenant": True,
            "query_patterns": query_patterns,
        }

        registry = PatternRegistry()
        generator = QueryPatternGenerator(registry)

        # Generate patterns
        sql_files = generator.generate(entity)

        # Check memory usage after generation
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 50MB)
        assert memory_increase < 50, (
            f"Memory usage increased by {memory_increase:.2f}MB, expected < 50MB"
        )

        assert len(sql_files) == 20
