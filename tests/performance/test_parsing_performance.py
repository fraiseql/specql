"""
Parsing performance tests for PL/pgSQL parser.

Tests DDL → SpecQL entity parsing performance.
"""

import pytest
import time
import psycopg2
from pathlib import Path
from typing import List, Tuple

from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser
from tests.utils.test_db_utils import (
    create_test_database,
    drop_test_database,
    execute_sql,
)


class ParsingPerformanceTest:
    """Parsing performance test infrastructure"""

    def __init__(self):
        self.parser = PLpgSQLParser(
            confidence_threshold=0.30
        )  # Lower threshold for performance testing
        self.results: List[
            Tuple[int, float, int, dict]
        ] = []  # (num_entities, time, entities_parsed, stats)

    def load_and_parse_dataset(
        self, dataset_path: Path, expected_entities: int
    ) -> Tuple[float, int, dict]:
        """
        Load dataset into database and parse.

        Returns:
            (parse_time, entities_parsed, stats)
        """
        # Create test database
        db_name = create_test_database(prefix="perf_parse_")

        try:
            # Load DDL
            ddl = dataset_path.read_text()

            # Apply DDL to database
            with psycopg2.connect(f"postgresql://localhost/{db_name}") as conn:
                execute_sql(conn, ddl)
                conn.commit()

            # Time parsing
            start_time = time.perf_counter()

            entities = self.parser.parse_database(
                connection_string=f"postgresql://localhost/{db_name}",
                schemas=["benchmark"],
            )

            parse_time = time.perf_counter() - start_time

            # Collect statistics
            stats = {
                "entities_parsed": len(entities),
                "total_fields": sum(len(e.fields) for e in entities),
                "total_actions": sum(len(e.actions) for e in entities),
                "trinity_detected": 0,  # TODO: Implement pattern detection stats
                "audit_fields_detected": 0,  # TODO: Implement pattern detection stats
            }

            return parse_time, len(entities), stats

        finally:
            # Cleanup
            drop_test_database(db_name)

    def run_benchmark(
        self, dataset_path: Path, expected_entities: int, label: str
    ) -> dict:
        """Run single benchmark and return results"""
        print(f"\n📊 Running parsing benchmark: {label}")
        print(f"   Dataset: {dataset_path.name}")
        print(f"   Expected entities: {expected_entities}")

        parse_time, entities_parsed, stats = self.load_and_parse_dataset(
            dataset_path, expected_entities
        )

        result = {
            "label": label,
            "dataset": dataset_path.name,
            "expected_entities": expected_entities,
            "entities_parsed": entities_parsed,
            "parse_time": parse_time,
            "parse_rate": entities_parsed / parse_time if parse_time > 0 else 0,
            "stats": stats,
        }

        self.results.append((expected_entities, parse_time, entities_parsed, stats))

        print(f"   ✅ Parsed {entities_parsed} entities in {parse_time:.2f}s")
        print(f"   📈 Rate: {result['parse_rate']:.1f} entities/sec")

        return result


@pytest.fixture
def perf_tester():
    """Fixture for performance testing"""
    return ParsingPerformanceTest()


@pytest.mark.slow
@pytest.mark.performance
def test_parse_10_entities(perf_tester):
    """Baseline: Parse 10 entities"""
    dataset = Path("tests/performance/datasets/benchmark_010.sql")
    result = perf_tester.run_benchmark(
        dataset, expected_entities=10, label="10 entities"
    )

    assert (
        result["entities_parsed"] >= 8
    )  # Allow some entities to be filtered by confidence threshold
    assert result["parse_time"] < 2.0  # Should be very fast


@pytest.mark.slow
@pytest.mark.performance
def test_parse_50_entities(perf_tester):
    """Parse 50 entities"""
    dataset = Path("tests/performance/datasets/benchmark_050.sql")
    result = perf_tester.run_benchmark(
        dataset, expected_entities=50, label="50 entities"
    )

    assert result["entities_parsed"] >= 30  # Allow filtering by confidence threshold
    assert result["parse_time"] < 5.0


@pytest.mark.slow
@pytest.mark.performance
def test_parse_100_entities_target(perf_tester):
    """Primary target: Parse 100 entities in < 10 seconds"""
    dataset = Path("tests/performance/datasets/benchmark_100.sql")
    result = perf_tester.run_benchmark(
        dataset, expected_entities=100, label="100 entities (PRIMARY TARGET)"
    )

    assert result["entities_parsed"] >= 80  # Allow some filtering by confidence
    assert result["parse_time"] < 10.0, (
        f"Parse time {result['parse_time']:.2f}s exceeds 10s target"
    )

    # Stretch goal
    if result["parse_time"] < 5.0:
        print("   🎉 STRETCH GOAL ACHIEVED: < 5s")


@pytest.mark.slow
@pytest.mark.performance
def test_parse_500_entities_stress(perf_tester):
    """Stress test: Parse 500 entities"""
    dataset = Path("tests/performance/datasets/benchmark_500.sql")
    result = perf_tester.run_benchmark(
        dataset, expected_entities=500, label="500 entities (stress test)"
    )

    assert result["entities_parsed"] >= 400  # Allow some filtering by confidence
    # Linear scaling from 100 entities: 500 should be ~50s
    assert result["parse_time"] < 60.0


@pytest.mark.skip(
    reason="PostgreSQL memory limits prevent 1000 entity test - requires max_locks_per_transaction increase"
)
@pytest.mark.slow
@pytest.mark.performance
@pytest.mark.extreme
def test_parse_1000_entities_extreme(perf_tester):
    """Extreme stress test: Parse 1000 entities"""
    dataset = Path("tests/performance/datasets/benchmark_1000.sql")
    result = perf_tester.run_benchmark(
        dataset, expected_entities=1000, label="1000 entities (EXTREME)"
    )

    assert result["entities_parsed"] >= 800  # Allow some filtering by confidence
    # Linear scaling: 1000 should be ~100s
    assert result["parse_time"] < 120.0


def test_parsing_performance_report(perf_tester):
    """Generate comprehensive parsing performance report"""

    # Run all benchmarks
    datasets = [
        (Path("tests/performance/datasets/benchmark_010.sql"), 10),
        (Path("tests/performance/datasets/benchmark_050.sql"), 50),
        (Path("tests/performance/datasets/benchmark_100.sql"), 100),
        (Path("tests/performance/datasets/benchmark_500.sql"), 500),
    ]

    results = []
    for dataset_path, expected in datasets:
        result = perf_tester.run_benchmark(
            dataset_path, expected, f"{expected} entities"
        )
        results.append(result)

    # Generate report
    report = ["", "=" * 80, "PARSING PERFORMANCE REPORT", "=" * 80, ""]

    report.append(
        f"{'Entities':<12} {'Time (s)':<12} {'Rate (ent/s)':<15} {'Target':<12} {'Status':<10}"
    )
    report.append("-" * 80)

    targets = {
        10: 2.0,
        50: 5.0,
        100: 10.0,
        500: 60.0,
    }

    for result in results:
        entities = result["entities_parsed"]
        parse_time = result["parse_time"]
        rate = result["parse_rate"]
        target = targets.get(entities, "N/A")

        if isinstance(target, float):
            status = "✅ PASS" if parse_time < target else "❌ FAIL"
            target_str = f"< {target:.1f}s"
        else:
            status = "N/A"
            target_str = "N/A"

        report.append(
            f"{entities:<12} {parse_time:<12.2f} {rate:<15.1f} {target_str:<12} {status:<10}"
        )

    report.append("-" * 80)
    report.append("")

    print("\n".join(report))
