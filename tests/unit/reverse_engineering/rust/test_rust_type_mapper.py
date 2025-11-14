"""
Unit tests for Rust type mapping functionality.
"""

import pytest
from src.reverse_engineering.rust_parser import RustTypeMapper


class TestRustTypeMapper:
    """Test Rust type to SQL type mapping."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = RustTypeMapper()

    def test_basic_integer_types(self):
        """Test mapping of basic integer types."""
        assert self.mapper.map_type("i32") == "integer"
        assert self.mapper.map_type("i64") == "bigint"
        assert self.mapper.map_type("u32") == "integer"
        assert self.mapper.map_type("u64") == "bigint"
        assert self.mapper.map_type("i16") == "smallint"
        assert self.mapper.map_type("u16") == "smallint"

    def test_floating_point_types(self):
        """Test mapping of floating point types."""
        assert self.mapper.map_type("f32") == "real"
        assert self.mapper.map_type("f64") == "double_precision"

    def test_boolean_type(self):
        """Test mapping of boolean type."""
        assert self.mapper.map_type("bool") == "boolean"

    def test_string_types(self):
        """Test mapping of string types."""
        assert self.mapper.map_type("String") == "text"
        assert self.mapper.map_type("str") == "text"
        assert self.mapper.map_type("&str") == "text"

    def test_time_types(self):
        """Test mapping of time-related types."""
        assert self.mapper.map_type("NaiveDateTime") == "timestamp"
        assert self.mapper.map_type("DateTime") == "timestamp with time zone"
        assert self.mapper.map_type("NaiveDate") == "date"
        assert self.mapper.map_type("NaiveTime") == "time"

    def test_uuid_type(self):
        """Test mapping of UUID type."""
        assert self.mapper.map_type("Uuid") == "uuid"

    def test_collection_types(self):
        """Test mapping of collection types."""
        assert self.mapper.map_type("Vec<String>") == "jsonb"
        assert self.mapper.map_type("HashMap<String, String>") == "jsonb"
        assert self.mapper.map_type("BTreeMap<String, i32>") == "jsonb"

    def test_option_types(self):
        """Test mapping of Option<T> types."""
        assert self.mapper.map_type("Option<String>") == "text"
        assert self.mapper.map_type("Option<i32>") == "integer"
        assert self.mapper.map_type("Option<Vec<String>>") == "jsonb"

    def test_array_types(self):
        """Test mapping of array types."""
        assert self.mapper.map_type("[String; 10]") == "jsonb"
        assert self.mapper.map_type("[i32]") == "jsonb"

    def test_unknown_types(self):
        """Test mapping of unknown types defaults to text."""
        assert self.mapper.map_type("CustomType") == "text"
        assert self.mapper.map_type("MyStruct") == "text"

    def test_diesel_type_mapping(self):
        """Test Diesel-specific type mapping."""
        assert self.mapper.map_diesel_type("Integer") == "integer"
        assert self.mapper.map_diesel_type("BigInt") == "bigint"
        assert self.mapper.map_diesel_type("Text") == "text"
        assert self.mapper.map_diesel_type("Bool") == "boolean"
        assert self.mapper.map_diesel_type("Timestamp") == "timestamp"
        assert self.mapper.map_diesel_type("Nullable<Text>") == "text"
        assert self.mapper.map_diesel_type("Nullable<Integer>") == "integer"

    def test_empty_generic_handling(self):
        """Test handling of malformed generics."""
        # These should not crash and should return text
        assert self.mapper.map_type("Vec<>") == "text"
        assert self.mapper.map_type("Option<") == "text"
        assert self.mapper.map_type("HashMap<") == "text"
