"""Performance tests with actual 100-entity dataset"""

import pytest
import time
import tempfile
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser
from src.generators.java.java_generator_orchestrator import JavaGeneratorOrchestrator
from src.core.yaml_serializer import YAMLSerializer
from src.core.specql_parser import SpecQLParser


class TestPerformance100Entities:
    """Performance benchmarks with 100 entities"""

    @pytest.fixture
    def benchmark_dataset_dir(self):
        """Path to 100-entity benchmark dataset"""
        return (
            Path(__file__).parent
            / "benchmark_dataset"
            / "src"
            / "main"
            / "java"
            / "com"
            / "example"
            / "benchmark"
        )

    def test_parse_100_entities_under_10_seconds(self, benchmark_dataset_dir):
        """Benchmark: Parse 100 entities in < 10 seconds"""
        parser = SpringBootParser()

        start_time = time.time()
        entities = parser.parse_project(str(benchmark_dataset_dir))
        end_time = time.time()

        elapsed = end_time - start_time

        assert len(entities) == 100, f"Expected 100 entities, got {len(entities)}"
        assert elapsed < 10.0, f"Parsing took {elapsed:.2f}s, expected < 10s"

        print(f"\n✅ Parsed {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(entities):.4f}s per entity")
        print(f"   Rate: {len(entities) / elapsed:.1f} entities/second")

    def test_generate_100_entities_under_30_seconds(self, benchmark_dataset_dir):
        """Benchmark: Generate 100 entities in < 30 seconds"""
        parser = SpringBootParser()
        entities = parser.parse_project(str(benchmark_dataset_dir))

        temp_dir = tempfile.mkdtemp()
        orchestrator = JavaGeneratorOrchestrator(temp_dir)

        start_time = time.time()
        for entity in entities:
            files = orchestrator.generate_all(entity)
            orchestrator.write_files(files)
        end_time = time.time()

        elapsed = end_time - start_time

        assert len(entities) == 100
        assert elapsed < 30.0, f"Generation took {elapsed:.2f}s, expected < 30s"

        print(f"\n✅ Generated {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(entities):.4f}s per entity")
        print(f"   Rate: {len(entities) / elapsed:.1f} entities/second")

    def test_round_trip_100_entities_under_60_seconds(self, benchmark_dataset_dir):
        """Benchmark: Full round-trip for 100 entities in < 60 seconds"""
        parser = SpringBootParser()

        start_time = time.time()

        # Parse all entities
        entities = parser.parse_project(str(benchmark_dataset_dir))

        # Round-trip each entity
        for entity in entities:
            # Serialize to YAML
            serializer = YAMLSerializer()
            yaml_content = serializer.serialize(entity)

            # Parse back from YAML
            specql_parser = SpecQLParser()
            intermediate_entity = specql_parser.parse_universal(yaml_content)

            # Generate Java code
            temp_dir = tempfile.mkdtemp()
            orchestrator = JavaGeneratorOrchestrator(temp_dir)
            files = orchestrator.generate_all(intermediate_entity)
            orchestrator.write_files(files)

        end_time = time.time()
        elapsed = end_time - start_time

        assert len(entities) == 100
        assert elapsed < 60.0, f"Round-trip took {elapsed:.2f}s, expected < 60s"

        print(f"\n✅ Round-trip for {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(entities):.4f}s per entity")
        print(f"   Rate: {len(entities) / elapsed:.1f} entities/second")

    def test_memory_usage_100_entities_under_1gb(self, benchmark_dataset_dir):
        """Benchmark: Memory usage stays under 1GB"""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Parse 100 entities
            parser = SpringBootParser()
            entities = parser.parse_project(str(benchmark_dataset_dir))

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            assert len(entities) == 100
            assert memory_increase < 1024, (
                f"Memory increase: {memory_increase:.0f}MB, expected < 1024MB"
            )

            print(f"\n✅ Memory usage for {len(entities)} entities:")
            print(f"   Initial: {initial_memory:.1f} MB")
            print(f"   Final: {final_memory:.1f} MB")
            print(f"   Increase: {memory_increase:.1f} MB")
            print(f"   Per entity: {memory_increase / len(entities):.2f} MB")

        except ImportError:
            pytest.skip("psutil not installed")
