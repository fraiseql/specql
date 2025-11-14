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
            structs, diesel_tables, diesel_derives, impl_blocks = (
                self.parser.parse_file(Path(temp_path))
            )
            assert len(structs) == 1
            assert len(diesel_tables) == 0  # No diesel tables in this test

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

    def test_diesel_table_macro_parsing(self):
        """Test parsing Diesel table! macros."""
        rust_code = """
        table! {
            users (id) {
                id -> Integer,
                username -> Text,
                email -> Nullable<Text>,
                created_at -> Timestamp,
            }
        }

        table! {
            posts (id) {
                id -> BigInt,
                title -> Text,
                user_id -> Integer,
                published -> Bool,
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            structs, diesel_tables, diesel_derives, impl_blocks = (
                self.parser.parse_file(Path(temp_path))
            )

            # Should have no structs but 2 diesel tables
            assert len(structs) == 0
            assert len(diesel_tables) == 2

            # Check users table
            users_table = next(t for t in diesel_tables if t.name == "users")
            assert users_table.name == "users"
            assert users_table.primary_key == ["id"]
            assert len(users_table.columns) == 4

            # Check column details
            id_col = next(c for c in users_table.columns if c.name == "id")
            assert id_col.sql_type == "Integer"
            assert not id_col.is_nullable

            email_col = next(c for c in users_table.columns if c.name == "email")
            assert email_col.sql_type == "Text"
            assert email_col.is_nullable

        finally:
            import os

            os.unlink(temp_path)

    def test_diesel_table_to_entity_mapping(self):
        """Test converting Diesel tables to SpecQL entities."""
        rust_code = """
        table! {
            products (id) {
                id -> Integer,
                name -> Text,
                price -> Double,
                in_stock -> Bool,
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(
                Path(temp_path), include_diesel_tables=True
            )

            # Should have 1 entity from diesel table
            assert len(entities) == 1

            entity = entities[0]
            assert entity.name == "Products"  # PascalCase
            assert entity.table == "products"  # original name
            assert len(entity.fields) == 4

            # Check field mappings
            assert "id" in entity.fields
            assert entity.fields["id"].type_name == "integer"
            assert not entity.fields["id"].nullable

            assert "name" in entity.fields
            assert entity.fields["name"].type_name == "text"

            assert "price" in entity.fields
            assert entity.fields["price"].type_name == "double_precision"

        finally:
            import os

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
            structs, diesel_tables, diesel_derives, impl_blocks = (
                self.parser.parse_file(Path(temp_path))
            )
            assert len(structs) == 1
            assert len(diesel_tables) == 0

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
            structs, diesel_tables, diesel_derives, impl_blocks = (
                self.parser.parse_file(Path(temp_path))
            )
            assert len(structs) == 1
            assert len(diesel_tables) == 0

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
            structs, diesel_tables, diesel_derives, impl_blocks = (
                self.parser.parse_file(Path(temp_path))
            )
            assert len(structs) == 0
            assert len(diesel_tables) == 0
        finally:
            os.unlink(temp_path)

    def test_impl_block_parsing_and_action_extraction(self):
        """Test parsing impl blocks and extracting actions."""
        from src.reverse_engineering.rust_action_parser import RustActionParser

        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
            pub email: String,
        }

        impl User {
            pub fn new(id: i32, name: String, email: String) -> Self {
                Self { id, name, email }
            }

            pub fn create_user(&self, name: String, email: String) -> Result<User, Error> {
                // Create user logic
                Ok(User { id: 1, name, email })
            }

            pub fn get_user(&self, id: i32) -> Result<User, Error> {
                // Get user logic
                Ok(User { id, name: "test".to_string(), email: "test@test.com".to_string() })
            }

            pub fn update_user(&self, id: i32, name: String) -> Result<(), Error> {
                // Update logic
                Ok(())
            }

            pub fn delete_user(&self, id: i32) -> Result<(), Error> {
                // Delete logic
                Ok(())
            }

            pub fn validate_email(&self, email: &str) -> bool {
                // Custom validation logic
                email.contains("@")
            }

            fn private_method(&self) {
                // Private method should not be extracted
            }
        }

        pub struct Error;
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            action_parser = RustActionParser()
            actions = action_parser.extract_actions(Path(temp_path))

            # Should extract 6 public actions (new, create_user, get_user, update_user, delete_user, validate_email)
            # Private method should be ignored
            assert len(actions) == 6

            # Check action types
            action_types = [a["type"] for a in actions]
            assert action_types.count("create") == 2  # new and create_user
            assert "read" in action_types
            assert "update" in action_types
            assert "delete" in action_types
            assert "custom" in action_types

            # Check specific actions
            new_action = next(a for a in actions if a["name"] == "new")
            assert new_action["type"] == "create"
            assert new_action["return_type"] == "Self"
            assert len(new_action["parameters"]) == 3  # id, name, email

            create_action = next(a for a in actions if a["name"] == "create_user")
            assert create_action["type"] == "create"
            assert create_action["return_type"] == "Result"
            assert len(create_action["parameters"]) == 2  # name, email

            read_action = next(a for a in actions if a["name"] == "get_user")
            assert read_action["type"] == "read"
            assert len(read_action["parameters"]) == 1  # id

            update_action = next(a for a in actions if a["name"] == "update_user")
            assert update_action["type"] == "update"

            delete_action = next(a for a in actions if a["name"] == "delete_user")
            assert delete_action["type"] == "delete"

            custom_action = next(a for a in actions if a["name"] == "validate_email")
            assert custom_action["type"] == "custom"
            assert custom_action["return_type"] == "bool"

            # Check that private method is not included
            action_names = [a["name"] for a in actions]
            assert "private_method" not in action_names

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
            structs, diesel_tables, diesel_derives, impl_blocks = (
                self.parser.parse_file(Path(temp_path))
            )
            assert len(structs) == 0
            assert len(diesel_tables) == 0
        finally:
            os.unlink(temp_path)
