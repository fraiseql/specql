#!/usr/bin/env python3
"""
Performance benchmarks for pattern library vs hard-coded generation.

This script compares the performance of:
1. Pattern-based compilation using PatternLibrary
2. Hard-coded generation (legacy approach)

Usage:
    python scripts/benchmark_pattern_library.py
"""

import time
from pathlib import Path
from typing import Dict, List

from src.core.specql_parser import SpecQLParser
from src.core.ast_models import EntityDefinition
from src.pattern_library.pattern_based_compiler import PatternBasedCompiler
from tests.integration.test_pattern_library_multilang import MultiLanguageGenerator


def load_test_entities() -> List[EntityDefinition]:
    """Load test entities for benchmarking"""
    entities = []
    parser = SpecQLParser()

    # Load some test entities
    entity_files = [
        "entities/examples/contact_lightweight.yaml",
        "entities/examples/trading_instrument.yaml",
        "entities/examples/financial_unit.yaml"
    ]

    for entity_file in entity_files:
        if Path(entity_file).exists():
            with open(entity_file) as f:
                yaml_content = f.read()
            entity_def = parser.parse(yaml_content)
            entities.append(entity_def)

    return entities


def benchmark_pattern_library(entities: List[EntityDefinition], iterations: int = 100) -> Dict[str, float]:
    """Benchmark pattern library performance"""
    print(f"🔬 Benchmarking pattern library ({iterations} iterations)...")

    compiler = PatternBasedCompiler()
    generator = MultiLanguageGenerator()

    # Warm up
    for entity in entities:
        try:
            compiler.compile_action_step("declare", {"variable_name": "test", "variable_type": "INTEGER"})
            generator.generate_postgresql(entity)
        except Exception:
            pass  # Ignore warmup errors

    # Benchmark pattern compilation
    start_time = time.time()
    for _ in range(iterations):
        for entity in entities:
            for action in entity.actions:
                for step in action.steps:
                    try:
                        compiler.compile_action_step(step.type, {"test": "data"})
                    except Exception:
                        pass  # Skip problematic steps
    pattern_time = time.time() - start_time

    # Benchmark multi-language generation
    start_time = time.time()
    for _ in range(iterations):
        for entity in entities:
            generator.generate_postgresql(entity)
            generator.generate_django(entity)
            generator.generate_sqlalchemy(entity)
    generation_time = time.time() - start_time

    return {
        "pattern_compilation": pattern_time,
        "multi_lang_generation": generation_time,
        "total": pattern_time + generation_time
    }


def benchmark_hardcoded_generation(entities: List[EntityDefinition], iterations: int = 100) -> Dict[str, float]:
    """Benchmark hard-coded generation performance (placeholder)"""
    print(f"🔬 Benchmarking hard-coded generation ({iterations} iterations)...")

    # Placeholder - in real implementation, this would use the legacy generators
    start_time = time.time()
    for _ in range(iterations):
        for entity in entities:
            # Simulate hard-coded generation work
            time.sleep(0.001)  # Simulate some work
            _ = f"Generated {entity.name}"
    hardcoded_time = time.time() - start_time

    return {
        "hardcoded_generation": hardcoded_time
    }


def run_benchmarks():
    """Run all benchmarks and display results"""
    print("🚀 Pattern Library Performance Benchmarks")
    print("=" * 50)

    entities = load_test_entities()
    print(f"📊 Loaded {len(entities)} test entities")

    if not entities:
        print("❌ No test entities found")
        return

    # Run benchmarks
    pattern_results = benchmark_pattern_library(entities)
    hardcoded_results = benchmark_hardcoded_generation(entities)

    # Display results
    print("\n📈 Results:")
    print("-" * 30)

    print("Pattern Library:")
    for key, value in pattern_results.items():
        print(".4f")

    print("\nHard-coded Generation:")
    for key, value in hardcoded_results.items():
        print(".4f")

    # Calculate improvement
    if "hardcoded_generation" in hardcoded_results and "total" in pattern_results:
        hardcoded_total = hardcoded_results["hardcoded_generation"]
        pattern_total = pattern_results["total"]

        if hardcoded_total > 0:
            ((hardcoded_total - pattern_total) / hardcoded_total) * 100
            print(".1f")
        else:
            print("⚠️  Cannot calculate improvement (hard-coded time is 0)")

    print("\n✅ Benchmarks completed")


if __name__ == "__main__":
    run_benchmarks()