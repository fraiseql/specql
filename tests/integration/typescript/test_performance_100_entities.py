"""Performance tests with 100-entity Prisma schema."""

import pytest
import time
from pathlib import Path
from src.parsers.typescript.prisma_parser import PrismaParser
from src.generators.typescript.prisma_schema_generator import PrismaSchemaGenerator


class TestPerformance100Entities:
    """Performance benchmarks with 100 entities."""

    @pytest.fixture
    def benchmark_schema_path(self):
        """Path to 100-entity benchmark schema."""
        return Path(__file__).parent / "benchmark_dataset" / "schema.prisma"

    def test_parse_100_entities_under_5_seconds(self, benchmark_schema_path):
        """Benchmark: Parse 100 entities in < 5 seconds."""
        parser = PrismaParser()

        start = time.time()
        entities = parser.parse_schema_file(str(benchmark_schema_path))
        elapsed = time.time() - start

        assert len(entities) == 100
        assert elapsed < 5.0, f"Parsing took {elapsed:.2f}s, expected < 5s"

        print(f"\n✅ Parsed {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Rate: {len(entities) / elapsed:.1f} entities/second")

    def test_generate_100_entities_under_10_seconds(self, benchmark_schema_path):
        """Benchmark: Generate 100 entities in < 10 seconds."""
        parser = PrismaParser()
        entities = parser.parse_schema_file(str(benchmark_schema_path))

        generator = PrismaSchemaGenerator()

        start = time.time()
        schema = generator.generate(entities)
        elapsed = time.time() - start

        assert len(entities) == 100
        assert elapsed < 10.0, f"Generation took {elapsed:.2f}s, expected < 10s"

        print(f"\n✅ Generated {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Rate: {len(entities) / elapsed:.1f} entities/second")

    def test_round_trip_100_entities_under_30_seconds(self, benchmark_schema_path):
        """Benchmark: Round-trip 100 entities in < 30 seconds."""
        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        start = time.time()

        # Parse
        entities = parser.parse_schema_file(str(benchmark_schema_path))

        # Generate
        schema = generator.generate(entities)

        # Parse again
        regenerated = parser.parse_schema_content(schema)

        elapsed = time.time() - start

        assert len(entities) == 100
        assert len(regenerated) == 100
        assert elapsed < 30.0, f"Round-trip took {elapsed:.2f}s, expected < 30s"

        print(f"\n✅ Round-trip {len(entities)} entities in {elapsed:.2f}s")
