"""
Performance benchmarks for Rust parser.

INSTALLATION: Copy to tests/performance/test_rust_parsing_performance.py

Run with:
    uv run pytest tests/performance/test_rust_parsing_performance.py -v
"""

import pytest
import tempfile
import time
from pathlib import Path
from src.reverse_engineering.rust_parser import (
    RustParser,
    RustToSpecQLMapper,
    RustReverseEngineeringService,
)


class TestRustParsingPerformance:
    """Performance benchmarks for Rust parsing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustParser()
        self.mapper = RustToSpecQLMapper()
        self.service = RustReverseEngineeringService()

    def test_single_struct_parsing_speed(self):
        """Test parsing speed for a single struct."""
        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
            pub email: Option<String>,
            pub active: bool,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Warm up
            self.parser.parse_file(Path(temp_path))

            # Benchmark
            iterations = 100
            start = time.time()
            for _ in range(iterations):
                self.parser.parse_file(Path(temp_path))
            elapsed = time.time() - start

            avg_time = elapsed / iterations
            structs_per_sec = 1 / avg_time

            print(
                f"\n  Single struct: {avg_time * 1000:.2f}ms avg, {structs_per_sec:.0f} structs/sec"
            )

            # Performance target: < 50ms per simple struct
            assert avg_time < 0.05, f"Too slow: {avg_time * 1000:.2f}ms > 50ms"

        finally:
            import os

            os.unlink(temp_path)

    def test_multiple_structs_parsing_speed(self):
        """Test parsing speed for multiple structs in one file."""
        # Generate 10 structs
        structs = []
        for i in range(10):
            structs.append(f"""
        pub struct Entity{i} {{
            pub id: i32,
            pub name: String,
            pub value: f64,
            pub active: bool,
            pub created_at: NaiveDateTime,
        }}
        """)

        rust_code = "use chrono::NaiveDateTime;\n\n" + "\n".join(structs)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Warm up
            self.parser.parse_file(Path(temp_path))

            # Benchmark
            iterations = 50
            start = time.time()
            for _ in range(iterations):
                result = self.parser.parse_file(Path(temp_path))
            elapsed = time.time() - start

            avg_time = elapsed / iterations
            structs_per_sec = (10 * iterations) / elapsed

            print(
                f"\n  10 structs: {avg_time * 1000:.2f}ms avg, {structs_per_sec:.0f} structs/sec"
            )

            # Performance target: > 200 structs/sec
            assert structs_per_sec > 200, (
                f"Too slow: {structs_per_sec:.0f} < 200 structs/sec"
            )

        finally:
            import os

            os.unlink(temp_path)

    def test_large_file_parsing_speed(self):
        """Test parsing speed for a large file with 100 structs."""
        # Generate 100 structs with varying complexity
        structs = []
        for i in range(100):
            num_fields = 5 + (i % 10)  # 5-15 fields
            fields = []
            for j in range(num_fields):
                field_type = ["i32", "i64", "String", "bool", "f64", "Option<String>"][
                    j % 6
                ]
                fields.append(f"    pub field_{j}: {field_type},")

            structs.append(f"""
pub struct Entity{i} {{
{chr(10).join(fields)}
}}
""")

        rust_code = "\n".join(structs)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Warm up
            self.parser.parse_file(Path(temp_path))

            # Benchmark
            iterations = 10
            start = time.time()
            for _ in range(iterations):
                result = self.parser.parse_file(Path(temp_path))
            elapsed = time.time() - start

            avg_time = elapsed / iterations
            structs_per_sec = (100 * iterations) / elapsed

            print(
                f"\n  100 structs: {avg_time * 1000:.2f}ms avg, {structs_per_sec:.0f} structs/sec"
            )

            # Performance target: > 500 structs/sec (meeting claimed 785 structs/sec)
            assert structs_per_sec > 500, (
                f"Too slow: {structs_per_sec:.0f} < 500 structs/sec"
            )

            # Stretch goal: Verify claimed 785 structs/sec
            if structs_per_sec > 785:
                print(f"  ✓ Exceeds claimed performance of 785 structs/sec")

        finally:
            import os

            os.unlink(temp_path)

    def test_complex_types_parsing_speed(self):
        """Test parsing speed for structs with complex types."""
        rust_code = """
        use chrono::{NaiveDateTime, NaiveDate};
        use uuid::Uuid;
        use serde_json::Value;
        use std::collections::HashMap;

        pub struct ComplexEntity {
            pub id: Uuid,
            pub data: Value,
            pub tags: Vec<String>,
            pub metadata: HashMap<String, String>,
            pub created_at: NaiveDateTime,
            pub updated_at: Option<NaiveDateTime>,
            pub nested: Option<Vec<HashMap<String, Value>>>,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Benchmark
            iterations = 100
            start = time.time()
            for _ in range(iterations):
                self.parser.parse_file(Path(temp_path))
            elapsed = time.time() - start

            avg_time = elapsed / iterations

            print(f"\n  Complex types: {avg_time * 1000:.2f}ms avg")

            # Performance target: < 100ms for complex types
            assert avg_time < 0.1, f"Too slow: {avg_time * 1000:.2f}ms > 100ms"

        finally:
            import os

            os.unlink(temp_path)

    def test_end_to_end_mapping_speed(self):
        """Test end-to-end speed including parsing and mapping to SpecQL entities."""
        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
            pub email: Option<String>,
        }

        pub struct Post {
            pub id: i64,
            pub title: String,
            pub user_id: i32,
        }

        pub struct Comment {
            pub id: i64,
            pub content: String,
            pub post_id: i64,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Benchmark full service
            iterations = 50
            start = time.time()
            for _ in range(iterations):
                entities = self.service.reverse_engineer_file(Path(temp_path))
            elapsed = time.time() - start

            avg_time = elapsed / iterations
            entities_per_sec = (3 * iterations) / elapsed

            print(
                f"\n  End-to-end (3 entities): {avg_time * 1000:.2f}ms avg, {entities_per_sec:.0f} entities/sec"
            )

            # Performance target: > 100 entities/sec end-to-end
            assert entities_per_sec > 100, (
                f"Too slow: {entities_per_sec:.0f} < 100 entities/sec"
            )

        finally:
            import os

            os.unlink(temp_path)

    def test_type_mapping_speed(self):
        """Test type mapping performance in isolation."""
        from src.reverse_engineering.rust_parser import RustTypeMapper

        mapper = RustTypeMapper()

        # Test various type mappings
        types_to_test = [
            "i32",
            "i64",
            "String",
            "bool",
            "f64",
            "Option<String>",
            "Vec<String>",
            "HashMap<String, String>",
            "NaiveDateTime",
            "Uuid",
            "serde_json::Value",
        ]

        iterations = 10000
        start = time.time()
        for _ in range(iterations):
            for rust_type in types_to_test:
                mapper.map_type(rust_type)
        elapsed = time.time() - start

        mappings_per_sec = (len(types_to_test) * iterations) / elapsed

        print(f"\n  Type mapping: {mappings_per_sec:.0f} mappings/sec")

        # Performance target: > 10,000 mappings/sec (should be very fast)
        assert mappings_per_sec > 10000, (
            f"Too slow: {mappings_per_sec:.0f} < 10,000 mappings/sec"
        )

    def test_impl_methods_parsing_speed(self):
        """Test parsing speed for impl blocks with methods."""
        # Generate impl block with 50 methods
        methods = []
        crud_ops = ["create", "get", "update", "delete", "find", "save", "remove"]

        for i in range(50):
            op = crud_ops[i % len(crud_ops)]
            methods.append(f"""
    pub fn {op}_entity_{i}(&self, id: i32) -> Result<Entity{i}, Error> {{
        // Implementation
        Ok(Entity{i} {{ id, name: "test".to_string() }})
    }}
""")

        rust_code = f"""
use std::result::Result;

pub struct Entity {{
    pub id: i32,
    pub name: String,
}}

#[derive(Debug)]
pub struct Error;

impl Entity {{
    pub fn new(id: i32, name: String) -> Self {{
        Self {{ id, name }}
    }}
{chr(10).join(methods)}
}}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Warm up
            self.parser.parse_file(Path(temp_path))

            # Benchmark
            iterations = 20
            start = time.time()
            for _ in range(iterations):
                result = self.parser.parse_file(Path(temp_path))
            elapsed = time.time() - start

            avg_time = elapsed / iterations
            methods_per_sec = (50 * iterations) / elapsed

            print(
                f"\n  50 methods: {avg_time * 1000:.2f}ms avg, {methods_per_sec:.0f} methods/sec"
            )

            # Performance target: > 500 methods/sec
            assert methods_per_sec > 500, (
                f"Too slow: {methods_per_sec:.0f} < 500 methods/sec"
            )

        finally:
            import os

            os.unlink(temp_path)

    def test_action_mapping_speed(self):
        """Test action mapping performance for impl methods."""
        from src.reverse_engineering.rust_action_parser import RustActionMapper
        from src.reverse_engineering.rust_parser import ImplMethodInfo

        mapper = RustActionMapper()

        # Create 100 method info objects
        methods = []
        crud_ops = ["create", "get", "update", "delete", "find", "save", "remove"]

        for i in range(100):
            op = crud_ops[i % len(crud_ops)]
            method = ImplMethodInfo(
                name=f"{op}_entity_{i}",
                visibility="pub",
                parameters=[
                    {
                        "name": "self",
                        "param_type": "&self",
                        "is_mut": False,
                        "is_ref": True,
                    }
                ],
                return_type="Result<Entity, Error>",
                is_async=False,
            )
            methods.append(method)

        # Benchmark action mapping
        iterations = 50
        start = time.time()
        for _ in range(iterations):
            for method in methods:
                mapper.map_method_to_action(method)
        elapsed = time.time() - start

        mappings_per_sec = (100 * iterations) / elapsed

        print(f"\n  Action mapping: {mappings_per_sec:.0f} mappings/sec")

        # Performance target: > 10,000 mappings/sec
        assert mappings_per_sec > 10000, (
            f"Too slow: {mappings_per_sec:.0f} < 10,000 mappings/sec"
        )

    def test_memory_usage(self):
        """Test that parsing doesn't cause excessive memory usage."""
        import os
        import psutil

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Parse a large file multiple times
        structs = []
        for i in range(50):
            structs.append(f"""
        pub struct Entity{i} {{
            pub id: i32,
            pub name: String,
            pub value: f64,
        }}
        """)
        rust_code = "\n".join(structs)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Parse 20 times
            for _ in range(20):
                self.parser.parse_file(Path(temp_path))

            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            mem_increase = mem_after - mem_before

            print(f"\n  Memory increase: {mem_increase:.2f}MB")

            # Performance target: < 50MB increase for 1000 parses
            assert mem_increase < 50, f"Excessive memory: {mem_increase:.2f}MB > 50MB"

        finally:
            import os

            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
