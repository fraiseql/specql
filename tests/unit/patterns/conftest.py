"""
Shared fixtures for pattern tests
"""

import pytest
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry


@pytest.fixture
def naming_conventions():
    """
    Shared NamingConventions instance with domain registry

    Use this when tests need access to the naming conventions or domain registry
    """
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
