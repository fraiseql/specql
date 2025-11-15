"""
Generation performance tests for PL/pgSQL schema generator.

Tests SpecQL entity → DDL generation performance.
"""

import pytest
import time
from typing import List, Tuple

from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.generators.plpgsql.schema_generator import SchemaGenerator


class GenerationPerformanceTest:
    """Generation performance test infrastructure"""

    def __init__(self):
        self.generator = SchemaGenerator()
        self.results: List[
            Tuple[int, float, str]
        ] = []  # (num_entities, time, ddl_sample)

    def generate_entities_and_measure(
        self, num_entities: int
    ) -> Tuple[float, int, str]:
        """Generate entities and measure DDL generation time."""
        entities = self._generate_test_entities(num_entities)

        start_time = time.perf_counter()
        ddl = self.generator.generate_schema(entities)
        generation_time = time.perf_counter() - start_time

        return (
            generation_time,
            len(entities),
            ddl[:200] + "..." if len(ddl) > 200 else ddl,
        )

    def _generate_test_entities(self, num_entities: int) -> List[UniversalEntity]:
        """Generate test entities for performance testing"""
        entities = []
        for i in range(num_entities):
            entity = UniversalEntity(
                name=f"entity_{i:03d}",
                schema="benchmark",
                fields=[
                    UniversalField(name=f"pk_entity_{i:03d}", type=FieldType.INTEGER),
                    UniversalField(name="id", type=FieldType.TEXT),
                    UniversalField(name="identifier", type=FieldType.TEXT),
                    UniversalField(name="field_00", type=FieldType.TEXT),
                    UniversalField(name="field_01", type=FieldType.INTEGER),
                    UniversalField(name="created_at", type=FieldType.DATETIME),
                    UniversalField(name="updated_at", type=FieldType.DATETIME),
                ],
                actions=[],
            )
            entities.append(entity)
        return entities

    def run_benchmark(self, num_entities: int, label: str) -> dict:
        """Run single benchmark and return results"""
        print(f"\n🏗️ Running generation benchmark: {label}")
        print(f"   Entities: {num_entities}")

        generation_time, entities_count, ddl_sample = (
            self.generate_entities_and_measure(num_entities)
        )

        result = {
            "label": label,
            "entities_count": entities_count,
            "generation_time": generation_time,
            "generation_rate": entities_count / generation_time
            if generation_time > 0
            else 0,
            "ddl_sample": ddl_sample,
        }

        self.results.append((entities_count, generation_time, ddl_sample))

        print(
            f"   ✅ Generated DDL for {entities_count} entities in {generation_time:.2f}s"
        )
        print(f"   📈 Rate: {result['generation_rate']:.1f} entities/sec")

        return result


@pytest.fixture
def gen_perf_tester():
    """Fixture for generation performance testing"""
    return GenerationPerformanceTest()


@pytest.mark.performance
def test_generate_10_entities(gen_perf_tester):
    """Baseline: Generate DDL for 10 entities"""
    result = gen_perf_tester.run_benchmark(num_entities=10, label="10 entities")
    assert result["entities_count"] == 10
    assert result["generation_time"] < 0.1


@pytest.mark.performance
def test_generate_50_entities(gen_perf_tester):
    """Generate DDL for 50 entities"""
    result = gen_perf_tester.run_benchmark(num_entities=50, label="50 entities")
    assert result["entities_count"] == 50
    assert result["generation_time"] < 0.5


@pytest.mark.performance
def test_generate_100_entities_target(gen_perf_tester):
    """Primary target: Generate DDL for 100 entities in < 1 second"""
    result = gen_perf_tester.run_benchmark(
        num_entities=100, label="100 entities (PRIMARY TARGET)"
    )
    assert result["entities_count"] == 100
    assert result["generation_time"] < 1.0, (
        f"Generation time {result['generation_time']:.2f}s exceeds 1s target"
    )

    if result["generation_time"] < 0.5:
        print("   🎉 STRETCH GOAL ACHIEVED: < 0.5s")


@pytest.mark.performance
def test_generate_500_entities_stress(gen_perf_tester):
    """Stress test: Generate DDL for 500 entities"""
    result = gen_perf_tester.run_benchmark(
        num_entities=500, label="500 entities (stress test)"
    )
    assert result["entities_count"] == 500
    assert result["generation_time"] < 5.0


@pytest.mark.performance
@pytest.mark.extreme
def test_generate_1000_entities_extreme(gen_perf_tester):
    """Extreme stress test: Generate DDL for 1000 entities"""
    result = gen_perf_tester.run_benchmark(
        num_entities=1000, label="1000 entities (EXTREME)"
    )
    assert result["entities_count"] == 1000
    assert result["generation_time"] < 10.0


def test_generation_performance_report(gen_perf_tester):
    """Generate comprehensive generation performance report"""
    benchmarks = [
        (10, "10 entities"),
        (50, "50 entities"),
        (100, "100 entities"),
        (500, "500 entities"),
    ]
    results = [
        gen_perf_tester.run_benchmark(num_entities, label)
        for num_entities, label in benchmarks
    ]

    report = ["", "=" * 80, "GENERATION PERFORMANCE REPORT", "=" * 80, ""]
    report.append(
        f"{'Entities':<12} {'Time (s)':<12} {'Rate (ent/s)':<15} {'Target':<12} {'Status':<10}"
    )
    report.append("-" * 80)

    targets = {10: 0.1, 50: 0.5, 100: 1.0, 500: 5.0}

    for result in results:
        entities = result["entities_count"]
        gen_time = result["generation_time"]
        rate = result["generation_rate"]
        target = targets.get(entities, "N/A")

        if isinstance(target, float):
            status = "✅ PASS" if gen_time < target else "❌ FAIL"
            target_str = f"< {target:.1f}s"
        else:
            status = "N/A"
            target_str = "N/A"

        report.append(
            f"{entities:<12} {gen_time:<12.2f} {rate:<15.1f} {target_str:<12} {status:<10}"
        )

    report.extend(["-" * 80, "", ""])
    print("\n".join(report))
