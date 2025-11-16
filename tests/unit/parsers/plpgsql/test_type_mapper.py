"""Unit tests for TypeMapper"""

import pytest
from src.parsers.plpgsql.type_mapper import TypeMapper
from src.core.universal_ast import FieldType


class TestTypeMapper:
    """Test TypeMapper"""

    @pytest.fixture
    def mapper(self):
        return TypeMapper()

    def test_map_integer_types(self, mapper):
        """Test mapping integer types"""
        assert mapper.map_postgres_type("INTEGER") == FieldType.INTEGER
        assert mapper.map_postgres_type("INT") == FieldType.INTEGER
        assert mapper.map_postgres_type("BIGINT") == FieldType.INTEGER
        assert mapper.map_postgres_type("SMALLINT") == FieldType.INTEGER

    def test_map_text_types(self, mapper):
        """Test mapping text types"""
        assert mapper.map_postgres_type("TEXT") == FieldType.TEXT
        assert mapper.map_postgres_type("VARCHAR") == FieldType.TEXT
        assert mapper.map_postgres_type("VARCHAR(255)") == FieldType.TEXT
        assert mapper.map_postgres_type("CHAR(10)") == FieldType.TEXT

    def test_map_boolean_type(self, mapper):
        """Test mapping boolean"""
        assert mapper.map_postgres_type("BOOLEAN") == FieldType.BOOLEAN
        assert mapper.map_postgres_type("BOOL") == FieldType.BOOLEAN

    def test_map_decimal_types(self, mapper):
        """Test mapping decimal types"""
        assert mapper.map_postgres_type("NUMERIC") == FieldType.TEXT
        assert mapper.map_postgres_type("DECIMAL") == FieldType.TEXT
        assert mapper.map_postgres_type("NUMERIC(10,2)") == FieldType.TEXT

    def test_map_datetime_types(self, mapper):
        """Test mapping date/time types"""
        assert mapper.map_postgres_type("TIMESTAMP") == FieldType.DATETIME
        assert mapper.map_postgres_type("TIMESTAMPTZ") == FieldType.DATETIME
        assert mapper.map_postgres_type("DATE") == FieldType.TEXT
        assert mapper.map_postgres_type("TIME") == FieldType.TEXT

    def test_map_uuid_type(self, mapper):
        """Test mapping UUID"""
        assert mapper.map_postgres_type("UUID") == FieldType.TEXT

    def test_map_json_types(self, mapper):
        """Test mapping JSON types"""
        assert mapper.map_postgres_type("JSON") == FieldType.TEXT
        assert mapper.map_postgres_type("JSONB") == FieldType.TEXT

    def test_detect_foreign_key(self, mapper):
        """Test detecting foreign key columns"""
        assert mapper._is_foreign_key("fk_company") is True
        assert mapper._is_foreign_key("company_id") is True
        assert not mapper._is_foreign_key("id")
        assert not mapper._is_foreign_key("email")

    def test_extract_reference_target(self, mapper):
        """Test extracting reference target entity"""
        assert mapper.extract_reference_target("fk_company") == "Company"
        assert mapper.extract_reference_target("company_id") == "Company"
        assert mapper.extract_reference_target("fk_order_item") == "OrderItem"
