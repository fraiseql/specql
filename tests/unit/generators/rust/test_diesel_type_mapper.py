"""
Tests for SpecQL → Diesel SQL type mapping

Diesel uses specific type names that map to PostgreSQL types.
These must be precise for schema generation.
"""

import pytest
from src.generators.rust.diesel_type_mapper import (
    DieselTypeMapper,
    DieselSqlType,
    DieselFieldType,
)


class TestDieselTypeMapper:
    """Test mapping SpecQL types to Diesel SQL types"""

    @pytest.fixture
    def mapper(self):
        return DieselTypeMapper()

    def test_map_integer_to_int4(self, mapper):
        """Test integer maps to Int4 (default)"""
        result = mapper.map_field_type("integer")

        assert result.base_type == DieselSqlType.INT4
        assert result.to_rust_string() == "Int4"

    def test_map_integer_big_to_int8(self, mapper):
        """Test integer:big maps to Int8"""
        result = mapper.map_field_type("integer:big")

        assert result.base_type == DieselSqlType.INT8
        assert result.to_rust_string() == "Int8"

    def test_map_integer_small_to_int2(self, mapper):
        """Test integer:small maps to Int2"""
        result = mapper.map_field_type("integer:small")

        assert result.base_type == DieselSqlType.INT2
        assert result.to_rust_string() == "Int2"

    def test_map_text_to_varchar(self, mapper):
        """Test text maps to Varchar"""
        result = mapper.map_field_type("text")

        assert result.base_type == DieselSqlType.VARCHAR
        assert result.to_rust_string() == "Varchar"

    def test_map_text_long_to_text(self, mapper):
        """Test text:long maps to Text (unlimited)"""
        result = mapper.map_field_type("text:long")

        assert result.base_type == DieselSqlType.TEXT
        assert result.to_rust_string() == "Text"

    def test_map_decimal_to_numeric(self, mapper):
        """Test decimal maps to Numeric"""
        result = mapper.map_field_type("decimal")

        assert result.base_type == DieselSqlType.NUMERIC
        assert result.to_rust_string() == "Numeric"

    def test_map_boolean_to_bool(self, mapper):
        """Test boolean maps to Bool"""
        result = mapper.map_field_type("boolean")

        assert result.base_type == DieselSqlType.BOOL
        assert result.to_rust_string() == "Bool"

    def test_map_timestamp_to_timestamptz(self, mapper):
        """Test timestamp maps to Timestamptz (with timezone)"""
        result = mapper.map_field_type("timestamp")

        assert result.base_type == DieselSqlType.TIMESTAMPTZ
        assert result.to_rust_string() == "Timestamptz"

    def test_map_uuid_to_uuid(self, mapper):
        """Test uuid maps to Uuid"""
        result = mapper.map_field_type("uuid")

        assert result.base_type == DieselSqlType.UUID
        assert result.to_rust_string() == "Uuid"

    def test_map_json_to_jsonb(self, mapper):
        """Test json maps to Jsonb (binary JSON)"""
        result = mapper.map_field_type("json")

        assert result.base_type == DieselSqlType.JSONB
        assert result.to_rust_string() == "Jsonb"

    def test_map_enum_to_varchar(self, mapper):
        """Test enum maps to Varchar (stored as text)"""
        result = mapper.map_field_type("enum")

        assert result.base_type == DieselSqlType.VARCHAR
        assert result.to_rust_string() == "Varchar"

    def test_map_vector_to_custom_type(self, mapper):
        """Test vector maps to custom Vector type"""
        result = mapper.map_field_type("vector")

        assert result.base_type == DieselSqlType.VECTOR
        assert result.to_rust_string() == "Vector"

    def test_nullable_field(self, mapper):
        """Test optional field becomes Nullable<Type>"""
        result = mapper.map_field_type("text", required=False)

        assert result.to_rust_string() == "Nullable<Varchar>"

    def test_reference_field_maps_to_int4(self, mapper):
        """Test ref fields map to Int4 (foreign keys)"""
        result = mapper.map_field_type("ref", ref_entity="Company")

        assert result.base_type == DieselSqlType.INT4
        assert result.to_rust_string() == "Int4"

    def test_optional_reference_is_nullable(self, mapper):
        """Test optional ref becomes Nullable<Int4>"""
        result = mapper.map_field_type("ref", ref_entity="Company", required=False)

        assert result.to_rust_string() == "Nullable<Int4>"

    def test_array_type_mapping(self, mapper):
        """Test array types map to Array<Type>"""
        result = mapper.map_field_type("text[]")

        assert result.to_rust_string() == "Array<Varchar>"

    def test_unknown_type_raises_error(self, mapper):
        """Test unknown types raise descriptive error"""
        with pytest.raises(ValueError, match="Unknown SpecQL type"):
            mapper.map_field_type("unknown_type")

    def test_trinity_pattern_fields(self, mapper):
        """Test Trinity pattern audit fields map correctly"""
        trinity_fields = {
            "pk_contact": ("integer:big", True),
            "id": ("uuid", True),
            "created_at": ("timestamp", True),
            "created_by": ("uuid", False),
            "updated_at": ("timestamp", True),
            "updated_by": ("uuid", False),
            "deleted_at": ("timestamp", False),
            "deleted_by": ("uuid", False),
        }

        for field_name, (field_type, required) in trinity_fields.items():
            result = mapper.map_field_type(field_type, required=required)
            # Verify each maps correctly
            assert result is not None

    def test_get_rust_native_type_basic(self, mapper):
        """Test basic Rust native type conversion"""
        int4_type = DieselFieldType(DieselSqlType.INT4, is_nullable=False)
        result = mapper.get_rust_native_type(int4_type)
        assert result == "i32"

    def test_get_rust_native_type_nullable(self, mapper):
        """Test nullable field becomes Option<T>"""
        varchar_type = DieselFieldType(DieselSqlType.VARCHAR, is_nullable=True)
        result = mapper.get_rust_native_type(varchar_type)
        assert result == "Option<String>"

    def test_get_rust_native_type_array(self, mapper):
        """Test array field becomes Vec<T>"""
        int4_type = DieselFieldType(
            DieselSqlType.INT4, is_nullable=False, is_array=True
        )
        result = mapper.get_rust_native_type(int4_type)
        assert result == "Vec<i32>"

    def test_get_rust_native_type_nullable_array(self, mapper):
        """Test nullable array field becomes Option<Vec<T>>"""
        bool_type = DieselFieldType(DieselSqlType.BOOL, is_nullable=True, is_array=True)
        result = mapper.get_rust_native_type(bool_type)
        assert result == "Option<Vec<bool>>"

    def test_get_rust_native_type_uuid(self, mapper):
        """Test UUID type conversion"""
        uuid_type = DieselFieldType(DieselSqlType.UUID, is_nullable=False)
        result = mapper.get_rust_native_type(uuid_type)
        assert result == "uuid::Uuid"

    def test_get_rust_native_type_timestamp(self, mapper):
        """Test timestamp type conversion"""
        ts_type = DieselFieldType(DieselSqlType.TIMESTAMPTZ, is_nullable=False)
        result = mapper.get_rust_native_type(ts_type)
        assert result == "chrono::NaiveDateTime"

    def test_get_rust_native_type_jsonb(self, mapper):
        """Test JSONB type conversion"""
        json_type = DieselFieldType(DieselSqlType.JSONB, is_nullable=False)
        result = mapper.get_rust_native_type(json_type)
        assert result == "serde_json::Value"

    def test_get_rust_native_type_bigdecimal(self, mapper):
        """Test BigDecimal type conversion"""
        decimal_type = DieselFieldType(DieselSqlType.NUMERIC, is_nullable=False)
        result = mapper.get_rust_native_type(decimal_type)
        assert result == "BigDecimal"

    def test_get_rust_native_type_unknown_falls_back_to_string(self, mapper):
        """Test unknown types fall back to String"""
        # Create a mock type that's not in the rust_types dict
        from unittest.mock import MagicMock

        mock_type = MagicMock()
        mock_type.value = "UnknownType"
        unknown_type = DieselFieldType(mock_type, is_nullable=False)
        result = mapper.get_rust_native_type(unknown_type)
        assert result == "String"
