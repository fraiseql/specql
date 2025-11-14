"""Performance benchmarking for Java parsing and generation"""

import pytest
import time
import tempfile
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser
from src.generators.java.java_generator_orchestrator import JavaGeneratorOrchestrator
from src.core.yaml_serializer import YAMLSerializer
from src.core.specql_parser import SpecQLParser


class TestPerformance:
    """Performance benchmarks"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Spring Boot project"""
        return Path(__file__).parent / "sample_project" / "src" / "main" / "java"

    def test_parse_sample_entities_under_1_second(self, sample_project_dir):
        """Benchmark: Parse sample entities in < 1 second"""
        parser = SpringBootParser()

        start_time = time.time()
        entities = parser.parse_project(
            str(sample_project_dir / "com" / "example" / "ecommerce")
        )
        end_time = time.time()

        elapsed = end_time - start_time

        assert len(entities) >= 5, "Test requires at least 5 entities"
        assert elapsed < 1.0, f"Parsing took {elapsed:.2f}s, expected < 1s"

        print(f"✅ Parsed {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(entities):.4f}s per entity")

    def test_generate_sample_entities_under_5_seconds(self, sample_project_dir):
        """Benchmark: Generate sample entities in < 5 seconds"""
        parser = SpringBootParser()
        entities = parser.parse_project(
            str(sample_project_dir / "com" / "example" / "ecommerce")
        )

        temp_dir = tempfile.mkdtemp()
        orchestrator = JavaGeneratorOrchestrator(temp_dir)

        start_time = time.time()
        for entity in entities:
            files = orchestrator.generate_all(entity)
            orchestrator.write_files(files)
        end_time = time.time()

        elapsed = end_time - start_time

        assert len(entities) >= 5
        assert elapsed < 5.0, f"Generation took {elapsed:.2f}s, expected < 5s"

        print(f"✅ Generated {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(entities):.4f}s per entity")

    def test_round_trip_sample_entities_under_10_seconds(self, sample_project_dir):
        """Benchmark: Full round-trip for sample entities in < 10 seconds"""
        parser = SpringBootParser()
        entities = parser.parse_project(
            str(sample_project_dir / "com" / "example" / "ecommerce")
        )

        start_time = time.time()

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

        assert len(entities) >= 5
        assert elapsed < 10.0, f"Round-trip took {elapsed:.2f}s, expected < 10s"

        print(f"✅ Round-trip for {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(entities):.4f}s per entity")

    # Memory test removed - requires psutil dependency
