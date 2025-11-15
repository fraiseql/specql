"""Unit tests for SchemaAnalyzer"""

import pytest
from src.parsers.plpgsql.schema_analyzer import SchemaAnalyzer


class TestSchemaAnalyzer:
    """Test SchemaAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        return SchemaAnalyzer()

    def test_extract_table_name_with_schema(self, analyzer):
        """Test extracting schema and table name"""
        ddl = "CREATE TABLE crm.tb_contact (id INTEGER)"
        schema, table = analyzer._extract_table_name(ddl)

        assert schema == "crm"
        assert table == "tb_contact"

    def test_extract_table_name_without_schema(self, analyzer):
        """Test extracting table name without schema"""
        ddl = "CREATE TABLE contact (id INTEGER)"
        schema, table = analyzer._extract_table_name(ddl)

        assert schema == "public"
        assert table == "contact"

    def test_table_to_entity_name(self, analyzer):
        """Test converting table names to entity names"""
        assert analyzer._table_to_entity_name("tb_contact") == "Contact"
        assert analyzer._table_to_entity_name("contact") == "Contact"
        assert analyzer._table_to_entity_name("tb_order_item") == "OrderItem"
        assert analyzer._table_to_entity_name("order_item") == "OrderItem"

    def test_extract_columns(self, analyzer):
        """Test extracting column definitions"""
        ddl = """
        CREATE TABLE contact (
            pk_contact INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            first_name TEXT
        )
        """

        columns = analyzer._extract_columns(ddl)

        assert len(columns) == 3
        assert columns[0]["name"] == "pk_contact"
        assert columns[1]["name"] == "email"
        assert columns[2]["name"] == "first_name"

    def test_parse_column_definition(self, analyzer):
        """Test parsing individual column"""
        col_def = "email TEXT NOT NULL DEFAULT 'test@example.com'"

        column = analyzer._parse_column_definition(col_def)

        assert column["name"] == "email"
        assert column["data_type"] == "TEXT"
        assert column["nullable"] == "NO"
        assert column["default"] == "'test@example.com'"

    def test_parse_complete_table(self, analyzer):
        """Test parsing complete CREATE TABLE"""
        ddl = """
        CREATE TABLE crm.tb_contact (
            pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            email TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            fk_company INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
        """

        entity = analyzer.parse_create_table(ddl)

        assert entity.name == "Contact"
        assert entity.schema == "crm"

        # Should have business fields only (Trinity and audit fields excluded)
        field_names = [f.name for f in entity.fields]
        assert "email" in field_names
        assert "first_name" in field_names
        assert "last_name" in field_names

        # Trinity and audit fields should be excluded
        assert "pk_contact" not in field_names
        assert "id" not in field_names
        assert "created_at" not in field_names
