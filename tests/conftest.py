"""
Pytest configuration and shared fixtures
"""

import logging
import uuid
from io import StringIO
from pathlib import Path
from typing import Any

import psycopg
import pytest

from core.dependencies import (
    FAKER,
    PGLAST,
    TREE_SITTER,
    TREE_SITTER_PRISMA,
    TREE_SITTER_RUST,
    TREE_SITTER_TYPESCRIPT,
)


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
                        {"validate": "email MATCHES email_pattern", "error": "invalid_email"},
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


@pytest.fixture
def isolated_logger():
    """Create logger that works with Click CliRunner."""
    logger = logging.getLogger("specql_test")
    logger.handlers.clear()

    # Use StringIO instead of stdout
    handler = logging.StreamHandler(StringIO())
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


@pytest.fixture
def contact_lightweight_yaml():
    """YAML content for lightweight contact entity used in integration tests."""
    return """
entity: Contact
schema: crm
description: Lightweight contact for testing
fields:
  email: email
  name: text
  company_id: uuid
actions:
  - name: create_contact
    steps:
      - validate: email IS NOT NULL
      - insert: Contact (email, name) VALUES ($email, $name)
"""


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
    from generators.schema.naming_conventions import NamingConventions

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
    from generators.schema.schema_registry import SchemaRegistry

    return SchemaRegistry(naming_conventions.registry)


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
    from generators.table_generator import TableGenerator

    return TableGenerator(schema_registry)


@pytest.fixture
def trinity_helper_generator(schema_registry):
    """
    Pre-configured TrinityHelperGenerator with SchemaRegistry
    """
    from generators.trinity_helper_generator import TrinityHelperGenerator

    return TrinityHelperGenerator(schema_registry)


@pytest.fixture
def core_logic_generator(schema_registry):
    """
    Pre-configured CoreLogicGenerator with SchemaRegistry
    """
    from generators.core_logic_generator import CoreLogicGenerator

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
    from generators.function_generator import FunctionGenerator

    return FunctionGenerator(schema_registry)


# Markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (slower)")
    config.addinivalue_line("markers", "benchmark: Performance benchmarks")
    config.addinivalue_line("markers", "requires_pglast: test requires pglast (SQL parsing)")
    config.addinivalue_line("markers", "requires_faker: test requires faker (test data)")
    config.addinivalue_line(
        "markers", "requires_tree_sitter: test requires tree-sitter (AST parsing)"
    )
    config.addinivalue_line(
        "markers", "requires_tree_sitter_rust: test requires tree-sitter-rust (Rust parsing)"
    )
    config.addinivalue_line(
        "markers",
        "requires_tree_sitter_typescript: test requires tree-sitter-typescript (TS parsing)",
    )
    config.addinivalue_line(
        "markers",
        "requires_tree_sitter_prisma: test requires tree-sitter-prisma (Prisma parsing)",
    )


# Skip hooks and auto-apply markers
def pytest_collection_modifyitems(config, items):
    """Skip tests that require unavailable dependencies and auto-apply markers."""

    skip_pglast = pytest.mark.skip(reason="pglast not installed (pip install specql[reverse])")
    skip_faker = pytest.mark.skip(reason="faker not installed (pip install specql[testing])")
    skip_tree_sitter = pytest.mark.skip(
        reason="tree-sitter not installed (pip install specql[reverse])"
    )
    skip_tree_sitter_rust = pytest.mark.skip(
        reason="tree-sitter-rust not installed (pip install specql[reverse])"
    )
    skip_tree_sitter_typescript = pytest.mark.skip(
        reason="tree-sitter-typescript not installed (pip install specql[reverse])"
    )
    skip_tree_sitter_prisma = pytest.mark.skip(
        reason="tree-sitter-prisma not installed (pip install specql[reverse])"
    )

    for item in items:
        test_path = str(item.fspath)

        # Auto-apply markers based on test location
        # Reverse engineering tests need pglast/tree-sitter
        if "reverse_engineering" in test_path:
            if "tree_sitter" in test_path or "parser" in test_path:
                item.add_marker(pytest.mark.requires_tree_sitter)
            if "sql" in test_path:
                item.add_marker(pytest.mark.requires_pglast)
            # Rust-specific tests (includes SeaORM/Diesel which are Rust ORMs)
            # Also mark tree_sitter_performance since it tests Rust parsing
            if (
                "rust" in test_path
                or "tree_sitter_rust" in test_path
                or "seaorm" in test_path
                or "diesel" in test_path
                or "tree_sitter_performance" in test_path
            ):
                item.add_marker(pytest.mark.requires_tree_sitter_rust)
            # TypeScript-specific tests
            if "typescript" in test_path or "tree_sitter_typescript" in test_path:
                item.add_marker(pytest.mark.requires_tree_sitter_typescript)
            # Prisma-specific tests
            if "prisma" in test_path or "tree_sitter_prisma" in test_path:
                item.add_marker(pytest.mark.requires_tree_sitter_prisma)

        # Testing module needs faker
        if "testing/seed" in test_path or "field_generator" in test_path:
            item.add_marker(pytest.mark.requires_faker)

        # Check markers and skip if dependency unavailable
        if "requires_pglast" in item.keywords and not PGLAST.available:
            item.add_marker(skip_pglast)

        if "requires_faker" in item.keywords and not FAKER.available:
            item.add_marker(skip_faker)

        if "requires_tree_sitter" in item.keywords and not TREE_SITTER.available:
            item.add_marker(skip_tree_sitter)

        if "requires_tree_sitter_rust" in item.keywords and not TREE_SITTER_RUST.available:
            item.add_marker(skip_tree_sitter_rust)

        if (
            "requires_tree_sitter_typescript" in item.keywords
            and not TREE_SITTER_TYPESCRIPT.available
        ):
            item.add_marker(skip_tree_sitter_typescript)

        if "requires_tree_sitter_prisma" in item.keywords and not TREE_SITTER_PRISMA.available:
            item.add_marker(skip_tree_sitter_prisma)
