"""
Pytest configuration and shared fixtures
"""

import uuid
from pathlib import Path
from typing import Any

import psycopg
import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def entity_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return path to entity YAML fixtures"""
    return fixtures_dir / "entities"


@pytest.fixture
def simple_contact_yaml(entity_fixtures_dir: Path) -> str:
    """Return simple contact entity YAML"""
    return """
entity: Contact
  schema: crm
  description: "Simple CRM contact"

  fields:
    first_name: text
    last_name: text
    email: text
    status: enum(lead, qualified, customer)

  actions:
    - name: create_contact
      steps:
        - validate: email MATCHES email_pattern
          error: "invalid_email"
        - insert: Contact
"""


@pytest.fixture
def mock_entity_dict() -> dict[str, Any]:
    """Return mock entity dictionary for testing"""
    return {
        "entity": {
            "name": "Contact",
            "schema": "crm",
            "description": "Mock contact entity",
            "fields": {
                "email": {"type": "text", "nullable": False},
                "status": {"type": "enum", "values": ["lead", "qualified"]},
            },
            "actions": [
                {
                    "name": "create_contact",
                    "steps": [
                        {
                            "validate": "email MATCHES email_pattern",
                            "error": "invalid_email",
                        },
                        {"insert": "Contact"},
                    ],
                }
            ],
        }
    }


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create temporary output directory for generated files"""
    output_dir = tmp_path / "generated"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def get_db_config():
    """Get database configuration from environment or defaults"""
    import os

    return {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "port": int(os.getenv("TEST_DB_PORT", "5432")),
        "dbname": os.getenv("TEST_DB_NAME", "specql_test"),
        "user": os.getenv("TEST_DB_USER", os.getenv("USER")),
        "password": os.getenv("TEST_DB_PASSWORD", ""),
    }


@pytest.fixture(scope="session")
def db_config():
    """Database configuration"""
    return get_db_config()


@pytest.fixture(scope="session")
def test_db_connection(db_config):
    """
    Session-scoped PostgreSQL connection for integration tests

    Environment variables (optional):
    - TEST_DB_HOST: Database host (default: localhost)
    - TEST_DB_PORT: Database port (default: 5432)
    - TEST_DB_NAME: Database name (default: specql_test)
    - TEST_DB_USER: Database user (default: current user)
    - TEST_DB_PASSWORD: Database password (default: empty)

    To skip database tests:
        pytest -m "not database"
    """
    try:
        # Build connection string
        conn_parts = [
            f"host={db_config['host']}",
            f"port={db_config['port']}",
            f"dbname={db_config['dbname']}",
            f"user={db_config['user']}",
        ]

        if db_config["password"]:
            conn_parts.append(f"password={db_config['password']}")

        conn_string = " ".join(conn_parts)

        # Connect with autocommit=False for transaction control
        conn = psycopg.connect(conn_string, autocommit=False)

        # Verify connection
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            result = cur.fetchone()
            if result:
                version = result[0]
                print(f"\n✅ Database connected: {version[:70]}...")
            else:
                print("\n✅ Database connected (version unknown)")

        # Install extensions if needed
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            conn.commit()
            print("✅ PostgreSQL extensions installed (pg_trgm, postgis)")
        except Exception as e:
            conn.rollback()
            print(f"⚠️  Could not install extensions: {e}")
            print("   (Some tests may be skipped)")

        yield conn

        # Cleanup
        conn.close()

    except psycopg.OperationalError as e:
        pytest.skip(
            f"PostgreSQL database not available: {e}\n\n"
            f"To run database tests:\n"
            f"  1. Create database: createdb {db_config['dbname']}\n"
            f"  2. Load schema: psql {db_config['dbname']} < tests/schema/setup.sql\n"
            f"  3. Or set ENABLE_DB_TESTS=0 to skip\n\n"
            f"Connection attempted:\n"
            f"  Host: {db_config['host']}\n"
            f"  Database: {db_config['dbname']}\n"
            f"  User: {db_config['user']}\n"
        )


@pytest.fixture
def test_db(test_db_connection):
    """
    Function-scoped database fixture with transaction rollback

    Each test gets a fresh transaction that's rolled back after the test.
    This ensures test isolation without needing to delete data.
    """
    # Start a transaction
    test_db_connection.rollback()  # Ensure clean state

    yield test_db_connection

    # Rollback transaction to clean up
    test_db_connection.rollback()


@pytest.fixture
def isolated_schema(test_db_connection):
    """
    Create unique schema per test for DDL isolation

    DDL operations (CREATE TABLE, CREATE TYPE) auto-commit in PostgreSQL
    and cannot be rolled back. This fixture creates a unique schema for each
    test to prevent object name conflicts between tests.

    Usage:
        def test_something(test_db, isolated_schema):
            ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
            cursor = test_db.cursor()
            cursor.execute(ddl)
            test_db.commit()
            # ... test logic
    """
    # Generate unique schema name
    schema_name = f"test_{uuid.uuid4().hex[:8]}"

    # Create schema
    with test_db_connection.cursor() as cur:
        cur.execute(f"CREATE SCHEMA {schema_name}")
    test_db_connection.commit()

    yield schema_name

    # Cleanup: Drop schema and all its objects
    try:
        with test_db_connection.cursor() as cur:
            cur.execute(f"DROP SCHEMA {schema_name} CASCADE")
        test_db_connection.commit()
    except Exception:
        # Ignore cleanup errors (schema might already be gone)
        test_db_connection.rollback()


def execute_sql(db, query, *args):
    """Execute SQL query and return all results"""
    cursor = db.cursor()
    cursor.execute(query, args)
    return cursor.fetchall()


def execute_query(db, query, *args):
    """Execute SQL query and return single result as dict"""
    cursor = db.cursor()
    cursor.execute(query, args)
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    result = cursor.fetchone()
    if result:
        return dict(zip(columns, result))
    return None


# ============================================================================
# Schema Registry Fixtures (for tests using new API)
# ============================================================================


@pytest.fixture
def naming_conventions():
    """
    Shared NamingConventions instance with domain registry

    Use this when tests need access to the naming conventions or domain registry
    """
    from src.generators.schema.naming_conventions import NamingConventions

    return NamingConventions()


@pytest.fixture
def schema_registry(naming_conventions):
    """
    Shared SchemaRegistry instance

    Use this fixture in any test that needs to create generators:

    Example:
        def test_something(schema_registry):
            generator = TableGenerator(schema_registry)
            # ... rest of test
    """
    from src.generators.schema.schema_registry import SchemaRegistry

    return SchemaRegistry()


@pytest.fixture
def table_generator(schema_registry):
    """
    Pre-configured TableGenerator with SchemaRegistry

    Use this when you just need a TableGenerator instance:

    Example:
        def test_table_ddl(table_generator):
            result = table_generator.generate(entity)
            assert "CREATE TABLE" in result
    """
    from src.generators.table_generator import TableGenerator

    return TableGenerator(schema_registry)


@pytest.fixture
def trinity_helper_generator(schema_registry):
    """
    Pre-configured TrinityHelperGenerator with SchemaRegistry
    """
    from src.generators.trinity_helper_generator import TrinityHelperGenerator

    return TrinityHelperGenerator(schema_registry)


@pytest.fixture
def core_logic_generator(schema_registry):
    """
    Pre-configured CoreLogicGenerator with SchemaRegistry
    """
    from src.generators.core_logic_generator import CoreLogicGenerator

    return CoreLogicGenerator(schema_registry)


@pytest.fixture
def function_generator(schema_registry):
    """
    Pre-configured FunctionGenerator with SchemaRegistry

    Use this when you need a FunctionGenerator instance:

    Example:
        def test_generate_functions(function_generator):
            result = function_generator.generate_action_functions(entity)
            assert "CREATE FUNCTION" in result
    """
    from src.generators.function_generator import FunctionGenerator

    return FunctionGenerator(schema_registry)


# Markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (slower)")
    config.addinivalue_line("markers", "benchmark: Performance benchmarks")
