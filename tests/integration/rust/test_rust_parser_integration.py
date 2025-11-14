"""
Integration tests for Rust parser end-to-end functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.reverse_engineering.rust_parser import (
    RustParser,
    RustToSpecQLMapper,
    RustReverseEngineeringService,
)


class TestRustParserIntegration:
    """Test end-to-end Rust parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustParser()
        self.mapper = RustToSpecQLMapper()
        self.service = RustReverseEngineeringService()

    def test_parse_simple_struct(self):
        """Test parsing a simple Rust struct."""
        rust_code = """
        #[derive(Debug, Clone)]
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
            structs = self.parser.parse_file(Path(temp_path))
            assert len(structs) == 1

            user_struct = structs[0]
            assert user_struct.name == "User"
            assert len(user_struct.fields) == 4

            # Check fields
            field_names = [f.name for f in user_struct.fields]
            assert "id" in field_names
            assert "name" in field_names
            assert "email" in field_names
            assert "active" in field_names

            # Check types
            id_field = next(f for f in user_struct.fields if f.name == "id")
            assert id_field.field_type == "i32"
            assert not id_field.is_optional

            email_field = next(f for f in user_struct.fields if f.name == "email")
            assert email_field.field_type == "String"
            assert email_field.is_optional

        finally:
            os.unlink(temp_path)

    def test_parse_multiple_structs(self):
        """Test parsing multiple structs in one file."""
        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
        }

        pub struct Post {
            pub id: i64,
            pub title: String,
            pub user_id: i32,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            structs = self.parser.parse_file(Path(temp_path))
            assert len(structs) == 2

            struct_names = [s.name for s in structs]
            assert "User" in struct_names
            assert "Post" in struct_names

        finally:
            os.unlink(temp_path)

    def test_struct_to_entity_mapping(self):
        """Test converting parsed structs to SpecQL entities."""
        rust_code = """
        pub struct Product {
            pub id: i32,
            pub name: String,
            pub price: f64,
            pub in_stock: bool,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            structs = self.parser.parse_file(Path(temp_path))
            assert len(structs) == 1

            entity = self.mapper.map_struct_to_entity(structs[0])

            assert entity.name == "Product"
            assert entity.table == "product"
            assert len(entity.fields) == 4

            # Check field mappings
            assert "id" in entity.fields
            assert "name" in entity.fields
            assert "price" in entity.fields
            assert "in_stock" in entity.fields

            id_field = entity.fields["id"]
            assert id_field.type_name == "integer"
            assert not id_field.nullable

            name_field = entity.fields["name"]
            assert name_field.type_name == "text"
            assert not name_field.nullable

            price_field = entity.fields["price"]
            assert price_field.type_name == "double_precision"
            assert not price_field.nullable

            stock_field = entity.fields["in_stock"]
            assert stock_field.type_name == "boolean"
            assert not stock_field.nullable

        finally:
            os.unlink(temp_path)

    def test_complex_types_mapping(self):
        """Test mapping of complex Rust types."""
        rust_code = """
        use chrono::{NaiveDateTime, NaiveDate};
        use uuid::Uuid;
        use serde_json::Value;

        pub struct ComplexEntity {
            pub id: Uuid,
            pub data: Value,
            pub tags: Vec<String>,
            pub metadata: HashMap<String, String>,
            pub created_at: NaiveDateTime,
            pub updated_at: Option<NaiveDateTime>,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            structs = self.parser.parse_file(Path(temp_path))
            assert len(structs) == 1

            entity = self.mapper.map_struct_to_entity(structs[0])

            assert entity.name == "ComplexEntity"
            assert len(entity.fields) == 6

            # Check complex type mappings
            id_field = entity.fields["id"]
            assert id_field.type_name == "uuid"

            data_field = entity.fields["data"]
            assert data_field.type_name == "jsonb"

            tags_field = entity.fields["tags"]
            assert tags_field.type_name == "jsonb"

            metadata_field = entity.fields["metadata"]
            assert metadata_field.type_name == "jsonb"

            created_field = entity.fields["created_at"]
            assert created_field.type_name == "timestamp"
            assert not created_field.nullable

            updated_field = entity.fields["updated_at"]
            assert updated_field.type_name == "timestamp"
            assert updated_field.nullable

        finally:
            os.unlink(temp_path)

    def test_service_integration(self):
        """Test the full service integration."""
        rust_code = """
        pub struct Category {
            pub id: i32,
            pub name: String,
        }

        pub struct Item {
            pub id: i32,
            pub name: String,
            pub category_id: i32,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))
            assert len(entities) == 2

            entity_names = [e.name for e in entities]
            assert "Category" in entity_names
            assert "Item" in entity_names

            # Verify all entities have proper structure
            for entity in entities:
                assert entity.table is not None
                assert isinstance(entity.fields, dict)
                assert len(entity.fields) > 0

        finally:
            os.unlink(temp_path)

    def test_empty_file_handling(self):
        """Test handling of empty or invalid files."""
        # Test empty file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            structs = self.parser.parse_file(Path(temp_path))
            assert len(structs) == 0
        finally:
            os.unlink(temp_path)

    def test_file_with_no_structs(self):
        """Test file with functions but no structs."""
        rust_code = """
        fn main() {
            println!("Hello, world!");
        }

        fn helper() -> i32 {
            42
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            structs = self.parser.parse_file(Path(temp_path))
            assert len(structs) == 0
        finally:
            os.unlink(temp_path)
