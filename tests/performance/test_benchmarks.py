"""
Performance benchmarks for all tracks
"""

import pytest
import time
from src.core.specql_parser import SpecQLParser
from src.pattern_library.api import PatternLibrary
from tests.integration.test_pattern_library_multilang import MultiLanguageGenerator


def generate_schema(yaml_content: str, target: str) -> str:
    """Generate schema from YAML content for given target"""
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    generator = MultiLanguageGenerator()

    if target == "postgresql":
        return generator.generate_postgresql(entity_def)
    elif target == "python_django":
        return generator.generate_django(entity_def)
    elif target == "python_sqlalchemy":
        return generator.generate_sqlalchemy(entity_def)
    else:
        raise ValueError(f"Unsupported target: {target}")


def test_benchmark_simple_entity_generation():
    """Benchmark: Generate simple entity (PostgreSQL)"""

    yaml_content = """
entity: Contact
fields:
  email: text
  name: text
"""

    start = time.time()
    generate_schema(yaml_content, target="postgresql")
    elapsed = time.time() - start

    print(f"Simple entity generation: {elapsed:.3f}s")

    # Should be fast (< 100ms)
    assert elapsed < 0.1


def test_benchmark_complex_entity_generation():
    """Benchmark: Generate entity with 3 domain patterns"""

    yaml_content = """
entity: Contact
patterns:
  - state_machine
  - audit_trail
  - soft_delete
fields:
  email: text
  name: text
"""

    start = time.time()
    generate_schema(yaml_content, target="postgresql")
    elapsed = time.time() - start

    print(f"Complex entity generation: {elapsed:.3f}s")

    # Should still be fast (< 500ms)
    assert elapsed < 0.5


def test_benchmark_reverse_engineering():
    """Benchmark: Reverse engineer SQL function"""

    sql = """
    CREATE OR REPLACE FUNCTION crm.calculate_total(p_order_id UUID)
    RETURNS NUMERIC AS $$
    DECLARE v_total NUMERIC := 0;
    BEGIN
        SELECT SUM(amount) INTO v_total FROM tb_order_line WHERE order_id = p_order_id;
        RETURN v_total;
    END;
    $$ LANGUAGE plpgsql;
    """

    # Import here to avoid import issues if not available
    try:
        from src.reverse_engineering.algorithmic_parser import AlgorithmicParser
    except ImportError:
        pytest.skip("AlgorithmicParser not available")

    parser = AlgorithmicParser()

    start = time.time()
    parser.parse(sql)
    elapsed = time.time() - start

    print(f"Reverse engineering (algorithmic): {elapsed:.3f}s")

    # Should be fast (< 1s)
    assert elapsed < 1.0


def test_benchmark_batch_generation():
    """Benchmark: Batch generate 100 entities"""

    entities = [
        f"""
        entity: Entity{i}
        fields:
          name: text
          value: integer
        """
        for i in range(100)
    ]

    start = time.time()
    for yaml in entities:
        generate_schema(yaml, target="postgresql")
    elapsed = time.time() - start

    print(f"Batch 100 entities: {elapsed:.3f}s")
    print(f"Average per entity: {elapsed/100:.3f}s")

    # Should be reasonable (< 10s total, < 100ms per entity)
    assert elapsed < 10.0


def test_benchmark_pattern_library_query():
    """Benchmark: Query pattern library"""

    library = PatternLibrary(":memory:")

    start = time.time()
    for _ in range(1000):
        library.get_pattern("state_machine")
    elapsed = time.time() - start

    print(f"1000 pattern queries: {elapsed:.3f}s")
    print(f"Average per query: {elapsed/1000*1000:.3f}ms")

    # Should be very fast (< 10ms per query)
    assert elapsed < 10.0


@pytest.mark.slow
def test_benchmark_full_pipeline():
    """Benchmark: Full pipeline (reverse → generate → multi-language)"""

    sql = """
    CREATE OR REPLACE FUNCTION crm.calculate_total(p_order_id UUID)
    RETURNS NUMERIC AS $$
    DECLARE v_total NUMERIC := 0;
    BEGIN
        SELECT SUM(amount) INTO v_total FROM tb_order_line WHERE order_id = p_order_id;
        RETURN v_total;
    END;
    $$ LANGUAGE plpgsql;
    """

    try:
        from src.reverse_engineering.algorithmic_parser import AlgorithmicParser
    except ImportError:
        pytest.skip("AlgorithmicParser not available")

    parser = AlgorithmicParser()

    start = time.time()

    # Reverse engineer
    parser.parse(sql)
    yaml = parser.parse_to_yaml(sql)

    # Generate PostgreSQL
    generate_schema(yaml, target="postgresql")

    # Generate Django
    generate_schema(yaml, target="python_django")

    # Generate SQLAlchemy
    generate_schema(yaml, target="python_sqlalchemy")

    elapsed = time.time() - start

    print(f"Full pipeline: {elapsed:.3f}s")

    # Should complete in reasonable time (< 5s)
    assert elapsed < 5.0