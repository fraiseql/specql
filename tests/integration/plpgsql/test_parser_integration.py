"""Integration tests for PLpgSQLParser"""

import pytest
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser
from src.core.universal_ast import FieldType


class TestPLpgSQLParserIntegration:
    """Test complete parser integration"""

    @pytest.fixture
    def parser(self):
        return PLpgSQLParser(confidence_threshold=0.70)

    def test_parse_simple_table_ddl(self, parser):
        """Test parsing simple CREATE TABLE"""
        ddl = """
        CREATE TABLE crm.tb_contact (
            pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            email TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        );
        """

        entities = parser.parse_ddl_string(ddl)

        assert len(entities) == 1
        entity = entities[0]

        assert entity.name == "Contact"
        assert entity.schema == "crm"

        # Should have business fields only
        field_names = [f.name for f in entity.fields]
        assert "email" in field_names
        assert "first_name" in field_names
        assert "last_name" in field_names

        # Trinity and audit fields should be excluded
        assert "pk_contact" not in field_names
        assert "id" not in field_names
        assert "created_at" not in field_names

    def test_parse_table_with_foreign_keys(self, parser):
        """Test parsing table with foreign key relationships"""
        ddl = """
        CREATE TABLE crm.tb_contact (
            pk_contact INTEGER PRIMARY KEY,
            id UUID NOT NULL,
            identifier TEXT,
            email TEXT NOT NULL,
            fk_company INTEGER REFERENCES crm.tb_company(pk_company),
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        """

        entities = parser.parse_ddl_string(ddl)
        entity = entities[0]

        # Find company field
        company_field = next(f for f in entity.fields if f.name == "fk_company")
        assert company_field.type == FieldType.REFERENCE
        # TODO: Add reference target parsing

    def test_parse_multiple_tables(self, parser):
        """Test parsing multiple tables"""
        ddl = """
        CREATE TABLE crm.tb_company (
            pk_company INTEGER PRIMARY KEY,
            id UUID NOT NULL,
            identifier TEXT,
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );

        CREATE TABLE crm.tb_contact (
            pk_contact INTEGER PRIMARY KEY,
            id UUID NOT NULL,
            identifier TEXT,
            email TEXT NOT NULL,
            fk_company INTEGER,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        """

        entities = parser.parse_ddl_string(ddl)

        assert len(entities) == 2
        entity_names = [e.name for e in entities]
        assert "Company" in entity_names
        assert "Contact" in entity_names

    def test_parse_ddl_file(self, parser, tmp_path):
        """Test parsing DDL from file"""
        ddl_file = tmp_path / "schema.sql"
        ddl_file.write_text("""
        CREATE TABLE test.tb_product (
            pk_product INTEGER PRIMARY KEY,
            id UUID NOT NULL,
            identifier TEXT,
            name TEXT NOT NULL,
            price NUMERIC(10,2),
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        """)

        entities = parser.parse_ddl_file(str(ddl_file))

        assert len(entities) == 1
        assert entities[0].name == "Product"

    def test_confidence_threshold_filtering(self, parser):
        """Test that low-confidence entities are filtered"""
        # Table without Trinity or audit fields
        ddl = """
        CREATE TABLE test.simple_table (
            id INTEGER,
            value TEXT
        );
        """

        entities = parser.parse_ddl_string(ddl)

        # Should be filtered out (confidence < 0.70)
        assert len(entities) == 0
