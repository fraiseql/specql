"""
Performance benchmarks for Rust parsing functionality.
"""

import time
import tempfile
import os
from pathlib import Path
from src.reverse_engineering.rust_parser import (
    RustParser,
    RustToSpecQLMapper,
    RustReverseEngineeringService,
)


def generate_test_rust_file(num_structs: int, fields_per_struct: int = 5) -> str:
    """Generate a test Rust file with the specified number of structs."""
    lines = []

    for i in range(num_structs):
        lines.append(f"#[derive(Debug, Clone)]")
        lines.append(f"pub struct TestStruct{i} {{")

        for j in range(fields_per_struct):
            field_type = get_field_type(j)
            lines.append(f"    pub field_{j}: {field_type},")

        lines.append("}")
        lines.append("")

    return "\n".join(lines)


def get_field_type(index: int) -> str:
    """Get a field type based on index for variety."""
    types = [
        "i32",
        "String",
        "bool",
        "f64",
        "Option<String>",
        "Vec<String>",
        "HashMap<String, String>",
        "Uuid",
        "NaiveDateTime",
        "Value",
    ]
    return types[index % len(types)]


def benchmark_parsing(num_structs: int, fields_per_struct: int = 5) -> dict:
    """Benchmark parsing performance for given parameters."""
    # Generate test data
    rust_code = generate_test_rust_file(num_structs, fields_per_struct)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        parser = RustParser()
        mapper = RustToSpecQLMapper()
        service = RustReverseEngineeringService()

        # Benchmark parsing
        start_time = time.time()
        structs = parser.parse_file(Path(temp_path))
        parse_time = time.time() - start_time

        # Benchmark mapping
        start_time = time.time()
        entities = [mapper.map_struct_to_entity(s) for s in structs]
        mapping_time = time.time() - start_time

        # Benchmark full service
        start_time = time.time()
        service_entities = service.reverse_engineer_file(Path(temp_path))
        service_time = time.time() - start_time

        return {
            "num_structs": num_structs,
            "fields_per_struct": fields_per_struct,
            "total_fields": num_structs * fields_per_struct,
            "parse_time": parse_time,
            "mapping_time": mapping_time,
            "service_time": service_time,
            "structs_per_second": num_structs / parse_time,
            "fields_per_second": (num_structs * fields_per_struct) / parse_time,
        }

    finally:
        os.unlink(temp_path)


def run_performance_tests():
    """Run performance tests with different sizes."""
    print("Rust Parser Performance Benchmarks")
    print("=" * 50)

    test_cases = [
        (1, 5),  # Small: 1 struct, 5 fields
        (5, 5),  # Medium: 5 structs, 5 fields each
        (10, 5),  # Larger: 10 structs, 5 fields each
        (20, 5),  # Even larger: 20 structs, 5 fields each
        (5, 10),  # More fields: 5 structs, 10 fields each
    ]

    results = []
    for num_structs, fields_per_struct in test_cases:
        print(
            f"\nTesting {num_structs} structs with {fields_per_struct} fields each..."
        )
        result = benchmark_parsing(num_structs, fields_per_struct)
        results.append(result)

        print(f"  Parse time: {result['parse_time']:.3f}s")
        print(f"  Mapping time: {result['mapping_time']:.3f}s")
        print(f"  Structs/sec: {result['structs_per_second']:.1f}")
        print(f"  Fields/sec: {result['fields_per_second']:.1f}")

    print("\n" + "=" * 50)
    print("Summary:")
    if results:
        avg_parse_time = sum(r["parse_time"] for r in results) / len(results)
        avg_structs_per_sec = sum(r["structs_per_second"] for r in results) / len(
            results
        )
        print(f"  Average parse time: {avg_parse_time:.3f}s")
        print(f"  Average structs/sec: {avg_structs_per_sec:.1f}")

        # Check performance targets
        print("\nPerformance Targets:")
        print(f"  Target parse time: < 0.1s (actual: {avg_parse_time:.3f}s)")
        print(
            f"  Target throughput: > 50 structs/sec (actual: {avg_structs_per_sec:.1f})"
        )
        if avg_parse_time < 0.1:
            print("  ✅ Parse time target met")
        else:
            print("  ❌ Parse time target not met")

        if avg_structs_per_sec > 50:
            print("  ✅ Throughput target met")
        else:
            print("  ❌ Throughput target not met")


if __name__ == "__main__":
    run_performance_tests()
