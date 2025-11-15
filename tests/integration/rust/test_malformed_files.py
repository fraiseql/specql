"""
Test handling of malformed Rust files and edge cases.
"""

import tempfile
import os
from pathlib import Path
from src.reverse_engineering.rust_parser import RustReverseEngineeringService


class TestMalformedFiles:
    """Test handling of malformed files and error conditions."""

    def test_malformed_syntax_graceful_failure(self):
        """Test that malformed syntax doesn't crash the parser."""
        malformed_code = """
        pub struct Broken {
            pub id: i32,
            pub name: String
            // Missing closing brace
        """

        service = RustReverseEngineeringService()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(malformed_code)
            temp_path = f.name

        try:
            # Should not crash, should return empty or handle gracefully
            entities = service.reverse_engineer_file(Path(temp_path))
            # Should return empty list for malformed code
            assert entities == []
        finally:
            os.unlink(temp_path)

    def test_empty_file_handling(self):
        """Test handling of empty files."""
        service = RustReverseEngineeringService()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            entities = service.reverse_engineer_file(Path(temp_path))
            assert entities == []
        finally:
            os.unlink(temp_path)

    def test_non_rust_file_handling(self):
        """Test handling of files that aren't Rust code."""
        non_rust_content = """
        # This is a Python file
        def hello():
            print("Hello, World!")
        """

        service = RustReverseEngineeringService()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(non_rust_content)
            temp_path = f.name

        try:
            entities = service.reverse_engineer_file(Path(temp_path))
            assert entities == []
        finally:
            os.unlink(temp_path)

    def test_incomplete_diesel_derive(self):
        """Test handling of incomplete Diesel derive attributes."""
        incomplete_code = """
        #[derive(Queryable]
        pub struct User {
            pub id: i32,
            pub name: String,
        }
        """

        service = RustReverseEngineeringService()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(incomplete_code)
            temp_path = f.name

        try:
            entities = service.reverse_engineer_file(Path(temp_path))
            # Should handle gracefully, might return empty or partial
            assert isinstance(entities, list)
        finally:
            os.unlink(temp_path)

    def test_complex_nested_types(self):
        """Test parsing of complex nested types."""
        complex_code = """
        use diesel::prelude::*;
        use std::collections::HashMap;

        #[derive(Queryable)]
        #[table_name = "complex_entities"]
        pub struct ComplexEntity {
            pub id: i32,
            pub metadata: HashMap<String, serde_json::Value>,
            pub tags: Vec<String>,
            pub settings: Option<serde_json::Value>,
            pub nested: Option<Box<ComplexEntity>>,
        }
        """

        service = RustReverseEngineeringService()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(complex_code)
            temp_path = f.name

        try:
            entities = service.reverse_engineer_file(Path(temp_path))
            # Should parse successfully
            assert len(entities) == 1
            entity = entities[0]
            assert entity.name == "ComplexEntity"
            assert len(entity.fields) == 5
        finally:
            os.unlink(temp_path)

    def test_macro_usage_without_diesel(self):
        """Test files with macros that aren't Diesel-related."""
        macro_code = """
        use serde::{Deserialize, Serialize};

        #[derive(Debug, Clone, Serialize, Deserialize)]
        pub struct ApiResponse<T> {
            pub success: bool,
            pub data: Option<T>,
            pub error: Option<String>,
        }

        // Custom macro usage
        custom_macro!(something);

        pub struct RegularStruct {
            pub id: i32,
            pub name: String,
        }
        """

        service = RustReverseEngineeringService()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(macro_code)
            temp_path = f.name

        try:
            entities = service.reverse_engineer_file(Path(temp_path))
            # Non-Diesel structs should not be returned
            # Only Diesel-related structs (with Queryable, Insertable, etc.) are converted to entities
            assert len(entities) == 0
        finally:
            os.unlink(temp_path)

    def test_file_with_comments_and_whitespace(self):
        """Test parsing files with lots of comments and whitespace."""
        commented_code = """
// This is a comment
use diesel::prelude::*;

/* Multi-line
   comment */
#[derive(Queryable)]
#[table_name = "users"]
pub struct User {
    pub id: i32,  // Primary key
    pub name: String,  // User name
    /* Multi-line
       field comment */
    pub email: String,
}
"""

        service = RustReverseEngineeringService()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(commented_code)
            temp_path = f.name

        try:
            entities = service.reverse_engineer_file(Path(temp_path))
            assert len(entities) == 1
            assert entities[0].name == "User"
            assert len(entities[0].fields) == 3
        finally:
            os.unlink(temp_path)
