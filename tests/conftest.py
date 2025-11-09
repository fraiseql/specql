"""
Pytest configuration and shared fixtures
"""

from pathlib import Path
from typing import Any, Dict

import pytest
import psycopg


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
def mock_entity_dict() -> Dict[str, Any]:
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
def db():
    """PostgreSQL test database connection"""
    try:
        import psycopg

        conn = psycopg.connect(
            host="localhost", dbname="test_specql", user="postgres", password="postgres"
        )
        # Enable required extensions
        conn.cursor().execute("CREATE EXTENSION IF NOT EXISTS ltree;")
        conn.commit()
        yield conn
        conn.close()
    except Exception:
        pytest.skip("PostgreSQL not available for integration tests")


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
