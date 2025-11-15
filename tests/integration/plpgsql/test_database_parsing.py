"""Database integration tests for PLpgSQLParser"""

import pytest
import psycopg
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser


@pytest.fixture
def test_schema_setup(test_db, isolated_schema):
    """Create test schema with sample tables"""
    schema_name = isolated_schema

    with test_db.cursor() as cur:
        # Create test tables in isolated schema
        cur.execute(f"""
        CREATE TABLE {schema_name}.tb_contact (
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
        );

        CREATE TABLE {schema_name}.tb_company (
            pk_company INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        );

        -- Insert test data
        INSERT INTO {schema_name}.tb_company (name) VALUES ('Acme Corp'), ('TechStart Inc');
        INSERT INTO {schema_name}.tb_contact (email, first_name, last_name, fk_company)
        VALUES ('john@acme.com', 'John', 'Doe', 1), ('jane@techstart.com', 'Jane', 'Smith', 2);
        """)
        test_db.commit()

    return schema_name


class TestDatabaseParsing:
    """Test parsing live database"""

    def test_parse_database(self, db_config, test_schema_setup):
        """Test parsing entire database"""
        parser = PLpgSQLParser()

        # Build connection string from db_config
        connection_string = f"postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"

        entities = parser.parse_database(connection_string, schemas=[test_schema_setup])

        assert len(entities) == 2
        entity_names = [e.name for e in entities]
        assert "Contact" in entity_names
        assert "Company" in entity_names

    def test_parse_specific_schemas(self, db_config, test_schema_setup):
        """Test parsing only specific schemas"""
        parser = PLpgSQLParser()

        connection_string = f"postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"

        entities = parser.parse_database(
            connection_string,
            schemas=[test_schema_setup],  # Only test schema
        )

        # All entities should be from test schema
        assert all(e.schema == test_schema_setup for e in entities)

    def test_parse_database_with_functions(self, test_db, db_config, test_schema_setup):
        """Test parsing database with PL/pgSQL functions"""
        schema_name = test_schema_setup

        # First create a test function
        with test_db.cursor() as cur:
            # Set search path to the test schema
            cur.execute(f"SET LOCAL search_path TO {schema_name}")
            cur.execute(f"""
            CREATE OR REPLACE FUNCTION create_contact(
                p_email TEXT,
                p_first_name TEXT,
                p_last_name TEXT
            ) RETURNS INTEGER AS $$
            BEGIN
                INSERT INTO tb_contact (email, first_name, last_name, created_at, updated_at)
                VALUES (p_email, p_first_name, p_last_name, NOW(), NOW())
                RETURNING pk_contact;
            END;
            $$ LANGUAGE plpgsql;
            """)
            test_db.commit()

        parser = PLpgSQLParser()
        connection_string = f"postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"

        entities = parser.parse_database(
            connection_string, schemas=[schema_name], include_functions=True
        )

        # Should have Contact entity with actions
        contact_entity = next(e for e in entities if e.name == "Contact")
        assert len(contact_entity.actions) > 0

    def test_parse_database_confidence_filtering(
        self, test_db, db_config, test_schema_setup
    ):
        """Test that confidence filtering works with database parsing"""
        schema_name = test_schema_setup

        # Add a table without SpecQL patterns
        with test_db.cursor() as cur:
            cur.execute(f"""
            CREATE TABLE {schema_name}.simple_table (
                id INTEGER,
                value TEXT
            );
            """)
            test_db.commit()

        # Parse with default confidence threshold (0.7)
        parser = PLpgSQLParser()
        connection_string = f"postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"

        entities = parser.parse_database(connection_string, schemas=[schema_name])

        # Should only include entities with high confidence (Contact, Company)
        # simple_table should be filtered out
        entity_names = [e.name for e in entities]
        assert "Contact" in entity_names
        assert "Company" in entity_names
        assert "SimpleTable" not in entity_names
