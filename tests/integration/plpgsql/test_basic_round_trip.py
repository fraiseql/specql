"""
Basic round-trip tests for PL/pgSQL.

Tests simple tables, data types, and basic constraints.
"""

import pytest
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser
from src.generators.plpgsql.schema_generator import SchemaGenerator
from tests.utils.schema_comparison import SchemaComparator
from tests.utils.test_db_utils import (
    create_test_database,
    drop_test_database,
    execute_sql,
    get_test_connection,
)


class TestBasicRoundTrip:
    """Test basic round-trip functionality"""

    @pytest.fixture
    def round_trip_setup(self):
        """Setup and teardown for round-trip tests"""
        parser = PLpgSQLParser(confidence_threshold=0.70)
        generator = SchemaGenerator()
        original_db = create_test_database(prefix="original_")
        generated_db = create_test_database(prefix="generated_")

        yield parser, generator, original_db, generated_db

        # Cleanup
        drop_test_database(original_db)
        drop_test_database(generated_db)

    def run_round_trip_test(self, original_ddl, expected_tables, round_trip_setup):
        """Helper method to run round-trip test"""
        parser, generator, original_db, generated_db = round_trip_setup

        # Step 1: Apply original DDL to original database
        with get_test_connection(original_db) as conn:
            execute_sql(conn, original_ddl)
            conn.commit()

        # Step 2: Parse original database to SpecQL entities
        entities = parser.parse_database(
            connection_string=f"postgresql://lionel@localhost:5432/{original_db}",
            schemas=["public"],
        )

        # Validate expected number of entities
        entity_names = {e.name for e in entities}
        expected_set = set(expected_tables)
        assert entity_names == expected_set, (
            f"Expected tables {expected_set}, got {entity_names}"
        )

        # Step 3: Generate DDL from SpecQL entities
        generated_ddl = generator.generate_schema(entities)

        # Step 4: Apply generated DDL to generated database
        with get_test_connection(generated_db) as conn:
            execute_sql(conn, generated_ddl)
            conn.commit()

        # Step 5: Compare schemas for equivalence
        with get_test_connection(original_db) as orig_conn:
            with get_test_connection(generated_db) as gen_conn:
                for entity in entities:
                    table_name = generator._get_table_name(entity)

                    # Compare each table individually using separate connections
                    orig_comparator = SchemaComparator(orig_conn)
                    gen_comparator = SchemaComparator(gen_conn)

                    orig_schema = orig_comparator.extract_table_schema(
                        "public", table_name
                    )
                    gen_schema = gen_comparator.extract_table_schema(
                        "public", table_name
                    )

                    is_equivalent, differences = orig_comparator.compare_tables(
                        orig_schema, gen_schema
                    )
                    assert is_equivalent, (
                        f"Table {table_name} not equivalent: {differences}"
                    )

    def test_simple_table_with_trinity_fields(self, round_trip_setup):
        """Test round-trip for simple table with Trinity pattern"""
        original_ddl = """
        CREATE TABLE tb_user (
            pk_user SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        self.run_round_trip_test(
            original_ddl=original_ddl,
            expected_tables=["User"],
            round_trip_setup=round_trip_setup,
        )

    def test_table_with_various_data_types(self, round_trip_setup):
        """Test round-trip for table with various PostgreSQL data types"""
        original_ddl = """
        CREATE TABLE tb_product (
            pk_product SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL,
            name TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            in_stock BOOLEAN DEFAULT TRUE,
            weight_kg DECIMAL(5,2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        self.run_round_trip_test(
            original_ddl=original_ddl,
            expected_tables=["Product"],
            round_trip_setup=round_trip_setup,
        )

    def test_table_with_foreign_key(self, round_trip_setup):
        """Test round-trip for table with foreign key relationship"""
        original_ddl = """
        CREATE TABLE tb_category (
            pk_category SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE TABLE tb_product (
            pk_product SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL,
            name TEXT NOT NULL,
            category_id INTEGER REFERENCES tb_category(pk_category),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        self.run_round_trip_test(
            original_ddl=original_ddl,
            expected_tables=["Category", "Product"],
            round_trip_setup=round_trip_setup,
        )

    def test_table_with_unique_constraints(self, round_trip_setup):
        """Test round-trip for table with unique constraints"""
        original_ddl = """
        CREATE TABLE tb_user (
            pk_user SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL UNIQUE,
            email TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        self.run_round_trip_test(
            original_ddl=original_ddl,
            expected_tables=["User"],
            round_trip_setup=round_trip_setup,
        )

    def test_multiple_tables_complex_schema(self, round_trip_setup):
        """Test round-trip for complex schema with multiple related tables"""
        original_ddl = """
        CREATE TABLE tb_user (
            pk_user SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE TABLE tb_category (
            pk_category SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL,
            name TEXT NOT NULL,
            parent_id INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE TABLE tb_product (
            pk_product SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL,
            name TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            category_id INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE TABLE tb_order (
            pk_order SERIAL PRIMARY KEY,
            id VARCHAR(50) NOT NULL,
            identifier VARCHAR(100) NOT NULL,
            user_id INTEGER,
            total DECIMAL(10,2) NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        self.run_round_trip_test(
            original_ddl=original_ddl,
            expected_tables=["User", "Category", "Product", "Order"],
            round_trip_setup=round_trip_setup,
        )
