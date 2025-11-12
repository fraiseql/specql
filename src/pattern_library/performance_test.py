"""
Performance comparison between hard-coded compilers and pattern library.
"""

import time
import sqlite3
from jinja2 import Template


def benchmark_pattern_compilation(iterations=1000):
    """Benchmark pattern-based compilation performance"""

    # Connect to existing database
    conn = sqlite3.connect("pattern_library.db")
    conn.row_factory = sqlite3.Row

    # Get template
    impl = conn.execute("""
        SELECT pi.implementation_template
        FROM pattern_implementations pi
        JOIN patterns p ON pi.pattern_id = p.pattern_id
        WHERE p.pattern_name = 'declare'
    """).fetchone()

    template = Template(impl["implementation_template"])

    # Test data
    context = {
        "variable_name": "total",
        "variable_type": "NUMERIC",
        "default_value": "0"
    }

    # Benchmark pattern compilation
    start_time = time.time()
    for _ in range(iterations):
        result = template.render(**context)
    pattern_time = time.time() - start_time

    conn.close()

    print(f"Pattern Library: {iterations} compilations in {pattern_time:.4f}s")
    print(".2f")
    print(f"Result: {result}")

    return pattern_time


def benchmark_hardcoded_compilation(iterations=1000):
    """Benchmark what hard-coded compilation would look like"""

    # Simulate hard-coded template rendering (simplified)
    template_str = "{{ variable_name }} {{ variable_type }}{% if default_value %} := {{ default_value }}{% endif %};"
    template = Template(template_str)

    context = {
        "variable_name": "total",
        "variable_type": "NUMERIC",
        "default_value": "0"
    }

    # Benchmark direct template rendering
    start_time = time.time()
    for _ in range(iterations):
        result = template.render(**context)
    hardcoded_time = time.time() - start_time

    print(f"Hard-coded: {iterations} compilations in {hardcoded_time:.4f}s")
    print(".2f")
    print(f"Result: {result}")

    return hardcoded_time


def main():
    """Run performance comparison"""
    print("🔬 Performance Comparison: Pattern Library vs Hard-coded")
    print("=" * 60)

    iterations = 10000

    # Run benchmarks
    pattern_time = benchmark_pattern_compilation(iterations)
    print()
    hardcoded_time = benchmark_hardcoded_compilation(iterations)
    print()

    # Calculate overhead
    if hardcoded_time > 0:
        overhead = ((pattern_time - hardcoded_time) / hardcoded_time) * 100
        print(".1f")

        if abs(overhead) < 10:
            print("✅ Performance acceptable (<10% overhead)")
        else:
            print("⚠️  Performance overhead significant")
    else:
        print("❌ Unable to calculate overhead")


if __name__ == "__main__":
    main()