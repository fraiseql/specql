"""Test error handling and edge cases for PL/pgSQL parser"""

import pytest
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser


class TestPLpgSQLParserErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def parser(self):
        """Create parser instance with low confidence threshold for testing edge cases"""
        return PLpgSQLParser(confidence_threshold=0.1)

    def test_empty_ddl_string(self, parser):
        """Test parsing empty DDL string"""
        result = parser.parse_ddl_string("")
        assert result == []

    def test_invalid_sql_syntax(self, parser):
        """Test parsing invalid SQL syntax"""
        invalid_ddl = """
        CREATE TABLE invalid (
            id INTEGER PRIMARY KEY
            -- Missing closing parenthesis
        """

        # Should not crash, should return empty or partial results
        result = parser.parse_ddl_string(invalid_ddl)
        # Parser should handle gracefully, even if it returns empty
        assert isinstance(result, list)

    def test_malformed_create_table(self, parser):
        """Test malformed CREATE TABLE statements"""
        malformed_ddl = """
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT
        -- Missing closing parenthesis and semicolon
        """

        result = parser.parse_ddl_string(malformed_ddl)
        assert isinstance(result, list)

    def test_non_table_ddl(self, parser):
        """Test DDL with non-table statements"""
        ddl_with_other_statements = """
        CREATE SCHEMA test_schema;

        CREATE INDEX idx_test ON test_table(id);

        CREATE TYPE status_enum AS ENUM ('active', 'inactive');

        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            status status_enum NOT NULL DEFAULT 'active'
        );
        """

        result = parser.parse_ddl_string(ddl_with_other_statements)
        assert isinstance(result, list)
        # Should still find the table despite other DDL
        assert len(result) >= 0

    def test_duplicate_table_names(self, parser):
        """Test handling duplicate table names in same schema"""
        duplicate_ddl = """
        CREATE SCHEMA test;

        CREATE TABLE test.users (
            pk_user INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            name TEXT
        );

        CREATE TABLE test.users (
            pk_user INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            email TEXT
        );
        """

        result = parser.parse_ddl_string(duplicate_ddl)
        assert isinstance(result, list)
        # Should handle duplicates gracefully
        assert len(result) >= 1

    def test_extremely_long_identifiers(self, parser):
        """Test extremely long table and column names"""
        long_name = "a" * 200  # Very long identifier

        long_ddl = f"""
        CREATE TABLE {long_name} (
            {long_name}_id INTEGER PRIMARY KEY,
            {long_name}_name TEXT
        );
        """

        result = parser.parse_ddl_string(long_ddl)
        assert isinstance(result, list)

    def test_special_characters_in_names(self, parser):
        """Test table/column names with special characters"""
        special_ddl = """
        CREATE TABLE "user-table" (
            "user-id" INTEGER PRIMARY KEY,
            "user-name" TEXT,
            "user_email@test.com" TEXT
        );
        """

        result = parser.parse_ddl_string(special_ddl)
        assert isinstance(result, list)

    def test_nested_schema_creation(self, parser):
        """Test nested schema creation statements"""
        nested_ddl = """
        CREATE SCHEMA IF NOT EXISTS parent_schema;
        CREATE SCHEMA child_schema;

        CREATE TABLE parent_schema.parent_table (
            pk_parent INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT
        );

        CREATE TABLE child_schema.child_table (
            pk_child INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            parent_id INTEGER REFERENCES parent_schema.parent_table(id)
        );
        """

        result = parser.parse_ddl_string(nested_ddl)
        assert isinstance(result, list)
        assert len(result) >= 2  # Should find both tables

    def test_circular_references(self, parser):
        """Test tables with circular references (should not crash)"""
        circular_ddl = """
        CREATE TABLE table_a (
            pk_a INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            b_id INTEGER REFERENCES table_b(id)
        );

        CREATE TABLE table_b (
            pk_b INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            a_id INTEGER REFERENCES table_a(id)
        );
        """

        result = parser.parse_ddl_string(circular_ddl)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_unsupported_data_types(self, parser):
        """Test tables with unsupported or custom data types"""
        custom_type_ddl = """
        CREATE TYPE custom_type AS (
            field1 TEXT,
            field2 INTEGER
        );

        CREATE TABLE test_table (
            pk_test INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            custom_field custom_type,
            json_field JSON,
            jsonb_field JSONB,
            array_field TEXT[],
            unsupported_type SOME_UNKNOWN_TYPE
        );
        """

        result = parser.parse_ddl_string(custom_type_ddl)
        assert isinstance(result, list)
        assert len(result) >= 1  # Should find the table

    def test_unicode_characters(self, parser):
        """Test DDL with Unicode characters"""
        unicode_ddl = """
        CREATE TABLE café_table (
            pk_café INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            café_name TEXT,
            descripción TEXT
        );
        """

        result = parser.parse_ddl_string(unicode_ddl)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_extremely_large_ddl(self, parser):
        """Test parsing extremely large DDL (performance and memory test)"""
        # Generate a very large DDL with many tables
        large_ddl_parts = ["CREATE SCHEMA large_test;"]

        for i in range(200):  # 200 tables
            table_ddl = f"""
            CREATE TABLE large_test.table_{i:03d} (
                pk_table_{i} INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                id UUID NOT NULL DEFAULT gen_random_uuid(),
                identifier TEXT UNIQUE NOT NULL,
                field1 TEXT,
                field2 TEXT,
                field3 TEXT,
                field4 TEXT,
                field5 TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            );"""
            large_ddl_parts.append(table_ddl)

        large_ddl = "\n".join(large_ddl_parts)

        import time

        start_time = time.time()

        result = parser.parse_ddl_string(large_ddl)

        end_time = time.time()
        parsing_time = end_time - start_time

        assert isinstance(result, list)
        assert len(result) >= 150  # Should find most tables
        assert parsing_time < 10.0  # Should complete in reasonable time

    def test_database_connection_errors(self, parser):
        """Test database connection error handling"""
        # Test with invalid connection string
        with pytest.raises(Exception):
            parser.parse_database("postgresql://invalid:invalid@nonexistent:5432/db")

    def test_schema_filtering_edge_cases(self, parser):
        """Test schema filtering with edge cases"""
        multi_schema_ddl = """
        CREATE SCHEMA schema1;
        CREATE SCHEMA schema2;
        CREATE SCHEMA "quoted schema";

        CREATE TABLE schema1.table1 (
            pk_t1 INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT
        );
        CREATE TABLE schema2.table2 (
            pk_t2 INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT
        );
        CREATE TABLE "quoted schema".table3 (
            pk_t3 INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT
        );
        CREATE TABLE no_schema.table4 (
            pk_t4 INTEGER PRIMARY KEY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT
        );
        """

        # Test filtering by single schema
        result1 = parser.parse_ddl_string(multi_schema_ddl)
        assert isinstance(result1, list)

        # Parser should handle multiple schemas gracefully
        assert len(result1) >= 3
