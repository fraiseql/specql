"""
Test SQLAlchemy pattern syntax validation.

Verifies that all generated SQLAlchemy code is syntactically correct Python.
"""

import ast
import pytest
from src.pattern_library.api import PatternLibrary
import sqlite3


@pytest.fixture
def library():
    """Create pattern library with SQLAlchemy patterns loaded"""
    # Connect to existing database without reinitializing schema
    lib = PatternLibrary.__new__(PatternLibrary)
    lib.db_path = "pattern_library.db"
    lib.db = sqlite3.connect("pattern_library.db")
    lib.db.row_factory = sqlite3.Row
    return lib


def test_sqlalchemy_code_syntax_validation(library):
    """Test that all generated SQLAlchemy code is syntactically valid Python"""

    # Test cases with realistic context data
    test_cases = [
        {
            "pattern": "declare",
            "context": {
                "variable_name": "total",
                "variable_type": "Decimal",
                "default_value": "Decimal('0')"
            }
        },
        {
            "pattern": "assign",
            "context": {
                "variable_name": "total",
                "expression": "Decimal('100.50')"
            }
        },
        {
            "pattern": "if",
            "context": {
                "condition": "total > 0",
                "then_steps": "    return True",
                "else_steps": "    return False"
            }
        },
        {
            "pattern": "foreach",
            "context": {
                "iterator_var": "item",
                "collection": "items",
                "loop_body": "    process_item(item)"
            }
        },
        {
            "pattern": "query",
            "context": {
                "model_name": "User",
                "result_var": "users",
                "filters": {"is_active": "True"},
                "order_by": ["-created_at"]
            }
        },
        {
            "pattern": "insert",
            "context": {
                "model_name": "User",
                "instance_var": "user",
                "field_values": {
                    "username": "'john_doe'",
                    "email": "'john@example.com'",
                    "is_active": "True"
                }
            }
        },
        {
            "pattern": "update",
            "context": {
                "model_name": "User",
                "instance_var": "user",
                "lookup_value": "user_id",
                "field_values": {
                    "email": "'new_email@example.com'",
                    "last_login": "datetime.now()"
                }
            }
        },
        {
            "pattern": "delete",
            "context": {
                "model_name": "User",
                "instance_var": "user",
                "lookup_value": "user_id"
            }
        },
        {
            "pattern": "aggregate",
            "context": {
                "model_name": "Order",
                "result_var": "stats",
                "filters": {"status": "'completed'"},
                "aggregations": {"total": "func.count(Order.id)"}
            }
        },
        {
            "pattern": "call_function",
            "context": {
                "result_variable": "result",
                "function_name": "calculate_total",
                "arguments": ["order.items", "tax_rate"]
            }
        },
        {
            "pattern": "return",
            "context": {
                "expression": "JsonResponse({'status': 'success'})"
            }
        },
        {
            "pattern": "validate",
            "context": {
                "model_name": "User",
                "instance_var": "user",
                "custom_validators": ["validate_email", "validate_age"]
            }
        },
        {
            "pattern": "duplicate_check",
            "context": {
                "model_name": "User",
                "check_fields": {"email": "email_value"},
                "exists_var": "email_exists",
                "exclude_pk": "current_user_id",
                "duplicate_body": "    raise ValueError('Duplicate email')"
            }
        },
        {
            "pattern": "exception_handling",
            "context": {
                "try_body": "    result = risky_operation()",
                "exception_handlers": [("ValueError", "    handle_value_error()")],
                "finally_body": "    cleanup()"
            }
        },
        {
            "pattern": "json_build",
            "context": {
                "json_structure": {"name": "user.name", "email": "user.email"},
                "result_var": "user_data",
                "serialize": True
            }
        }
    ]

    for test_case in test_cases:
        pattern_name = test_case["pattern"]
        context = test_case["context"]

        # Generate code
        result = library.compile_pattern(
            pattern_name=pattern_name,
            language_name="python_sqlalchemy",
            context=context
        )

        # Verify it's a string
        assert isinstance(result, str), f"Pattern {pattern_name} should return string"

        # Verify it's not empty
        assert len(result.strip()) > 0, f"Pattern {pattern_name} should not return empty string"

        # Verify it's syntactically valid Python
        try:
            ast.parse(result)
        except SyntaxError as e:
            pytest.fail(f"Pattern {pattern_name} generated invalid Python syntax: {e}\nGenerated code:\n{result}")


def test_sqlalchemy_patterns_exist(library):
    """Test that all expected SQLAlchemy patterns are implemented"""

    # Get all SQLAlchemy implementations
    cursor = library.db.execute("""
        SELECT p.pattern_name
        FROM patterns p
        JOIN pattern_implementations pi ON p.pattern_id = pi.pattern_id
        JOIN languages l ON pi.language_id = l.language_id
        WHERE l.language_name = 'python_sqlalchemy'
        ORDER BY p.pattern_name
    """)

    implemented_patterns = [row["pattern_name"] for row in cursor.fetchall()]

    expected_patterns = [
        "declare", "assign", "if", "foreach", "query", "insert", "update", "delete",
        "aggregate", "call_function", "return", "validate", "duplicate_check",
        "exception_handling", "json_build"
    ]

    for pattern in expected_patterns:
        assert pattern in implemented_patterns, f"Pattern {pattern} should be implemented for SQLAlchemy"

    assert len(implemented_patterns) >= len(expected_patterns), f"Expected at least {len(expected_patterns)} patterns, got {len(implemented_patterns)}"