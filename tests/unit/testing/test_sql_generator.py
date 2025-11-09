"""Tests for SQL File Generator component"""

import pytest
from datetime import datetime
from src.testing.seed.sql_generator import SeedSQLGenerator
from src.testing.seed.uuid_generator import SpecQLUUID


class TestSeedSQLGenerator:
    """Test SQL file generation functionality"""

    def test_generate_insert_basic(self):
        """Test generating basic INSERT statement"""
        entity_config = {"entity_name": "Contact", "schema_name": "crm", "table_name": "tb_contact"}

        generator = SeedSQLGenerator(entity_config)

        entity_data = {
            "id": SpecQLUUID("01232121-0000-0000-0001-000000000001"),
            "tenant_id": "22222222-2222-2222-2222-222222222222",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
        }

        result = generator.generate_insert(entity_data)

        expected = (
            "INSERT INTO crm.tb_contact "
            "(id, tenant_id, email, first_name, last_name) "
            "VALUES "
            "('01232121-0000-0000-0001-000000000001', "
            "'22222222-2222-2222-2222-222222222222', "
            "'john@example.com', "
            "'John', "
            "'Doe');"
        )

        assert result == expected

    def test_generate_insert_with_null_values(self):
        """Test generating INSERT with NULL values"""
        entity_config = {"entity_name": "Contact", "schema_name": "crm", "table_name": "tb_contact"}

        generator = SeedSQLGenerator(entity_config)

        entity_data = {
            "id": SpecQLUUID("01232121-0000-0000-0001-000000000001"),
            "email": "john@example.com",
            "phone": None,
            "notes": None,
        }

        result = generator.generate_insert(entity_data)

        expected = (
            "INSERT INTO crm.tb_contact "
            "(id, email, phone, notes) "
            "VALUES "
            "('01232121-0000-0000-0001-000000000001', "
            "'john@example.com', "
            "NULL, "
            "NULL);"
        )

        assert result == expected

    def test_generate_insert_with_special_characters(self):
        """Test generating INSERT with special characters in strings"""
        entity_config = {"entity_name": "Contact", "schema_name": "crm", "table_name": "tb_contact"}

        generator = SeedSQLGenerator(entity_config)

        entity_data = {
            "id": SpecQLUUID("01232121-0000-0000-0001-000000000001"),
            "name": "O'Connor",
            "description": "Contains \"quotes\" and 'apostrophes'",
        }

        result = generator.generate_insert(entity_data)

        expected = (
            "INSERT INTO crm.tb_contact "
            "(id, name, description) "
            "VALUES "
            "('01232121-0000-0000-0001-000000000001', "
            "'O''Connor', "
            "'Contains \"quotes\" and ''apostrophes''');"
        )

        assert result == expected

    def test_generate_insert_with_numeric_types(self):
        """Test generating INSERT with various numeric types"""
        entity_config = {
            "entity_name": "Product",
            "schema_name": "sales",
            "table_name": "tb_product",
        }

        generator = SeedSQLGenerator(entity_config)

        entity_data = {
            "id": SpecQLUUID("01232121-0000-0000-0001-000000000001"),
            "price": 99.99,
            "quantity": 42,
            "is_active": True,
            "is_featured": False,
        }

        result = generator.generate_insert(entity_data)

        expected = (
            "INSERT INTO sales.tb_product "
            "(id, price, quantity, is_active, is_featured) "
            "VALUES "
            "('01232121-0000-0000-0001-000000000001', "
            "99.99, "
            "42, "
            "TRUE, "
            "FALSE);"
        )

        assert result == expected

    def test_generate_insert_with_datetime(self):
        """Test generating INSERT with datetime values"""
        entity_config = {"entity_name": "Contact", "schema_name": "crm", "table_name": "tb_contact"}

        generator = SeedSQLGenerator(entity_config)

        test_datetime = datetime(2025, 11, 8, 14, 30, 0)
        entity_data = {
            "id": SpecQLUUID("01232121-0000-0000-0001-000000000001"),
            "created_at": test_datetime,
            "updated_at": test_datetime,
        }

        result = generator.generate_insert(entity_data)

        expected = (
            "INSERT INTO crm.tb_contact "
            "(id, created_at, updated_at) "
            "VALUES "
            "('01232121-0000-0000-0001-000000000001', "
            "'2025-11-08T14:30:00', "
            "'2025-11-08T14:30:00');"
        )

        assert result == expected

    def test_generate_file_basic(self):
        """Test generating complete SQL file"""
        entity_config = {"entity_name": "Contact", "schema_name": "crm", "table_name": "tb_contact"}

        generator = SeedSQLGenerator(entity_config)

        entities = [
            {
                "id": SpecQLUUID("01232121-0000-0000-0001-000000000001"),
                "email": "john@example.com",
                "first_name": "John",
            },
            {
                "id": SpecQLUUID("01232121-0000-0000-0002-000000000002"),
                "email": "jane@example.com",
                "first_name": "Jane",
            },
        ]

        result = generator.generate_file(entities, scenario=0, description="default seed data")

        lines = result.strip().split("\n")

        # Check header comments
        assert lines[0] == "-- Seed data for Contact"
        assert lines[1] == "-- Schema: crm"
        assert lines[2] == "-- Scenario: 0 (default seed data)"
        assert lines[3].startswith("-- Generated: ")
        assert lines[4] == "-- Record count: 2"
        assert lines[5] == ""

        # Check INSERT statements
        assert "INSERT INTO crm.tb_contact" in lines[6]
        assert "john@example.com" in lines[6]
        assert "INSERT INTO crm.tb_contact" in lines[7]
        assert "jane@example.com" in lines[7]

    def test_generate_file_empty_list(self):
        """Test generating SQL file with no records"""
        entity_config = {"entity_name": "Contact", "schema_name": "crm", "table_name": "tb_contact"}

        generator = SeedSQLGenerator(entity_config)

        result = generator.generate_file([], scenario=1000, description="empty test")

        lines = result.splitlines()

        # Check header comments
        assert lines[0] == "-- Seed data for Contact"
        assert lines[1] == "-- Schema: crm"
        assert lines[2] == "-- Scenario: 1000 (empty test)"
        assert lines[3].startswith("-- Generated: ")
        assert lines[4] == "-- Record count: 0"
        assert lines[5] == ""  # Trailing empty line

    def test_format_value_uuid(self):
        """Test formatting UUID values"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        uuid = SpecQLUUID("01232121-0000-0000-0001-000000000001")
        result = generator._format_value(uuid)
        assert result == "'01232121-0000-0000-0001-000000000001'"

    def test_format_value_string(self):
        """Test formatting string values"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        result = generator._format_value("hello world")
        assert result == "'hello world'"

    def test_format_value_string_with_quotes(self):
        """Test formatting string values with quotes"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        result = generator._format_value("It's a 'test' string")
        assert result == "'It''s a ''test'' string'"

    def test_format_value_integer(self):
        """Test formatting integer values"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        result = generator._format_value(42)
        assert result == "42"

    def test_format_value_float(self):
        """Test formatting float values"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        result = generator._format_value(99.99)
        assert result == "99.99"

    def test_format_value_boolean(self):
        """Test formatting boolean values"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        assert generator._format_value(True) == "TRUE"
        assert generator._format_value(False) == "FALSE"

    def test_format_value_none(self):
        """Test formatting NULL values"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        result = generator._format_value(None)
        assert result == "NULL"

    def test_format_value_datetime(self):
        """Test formatting datetime values"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        dt = datetime(2025, 11, 8, 14, 30, 0)
        result = generator._format_value(dt)
        assert result == "'2025-11-08T14:30:00'"

    def test_format_value_unknown_type(self):
        """Test formatting unknown types (fallback)"""
        entity_config = {"entity_name": "Test", "schema_name": "test", "table_name": "tb_test"}
        generator = SeedSQLGenerator(entity_config)

        result = generator._format_value([1, 2, 3])  # List as unknown type
        assert result == "'[1, 2, 3]'"
