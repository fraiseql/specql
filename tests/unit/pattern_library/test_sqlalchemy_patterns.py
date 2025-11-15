"""
Tests for SQLAlchemy pattern implementations in the pattern library.

Tests the core 15 most-used primitives for SQLAlchemy ORM generation.
GREEN PHASE: All tests should PASS - implementations are working.
"""

import pytest
from pathlib import Path
from src.pattern_library.api import PatternLibrary


class TestSQLAlchemyPatterns:
    """Test SQLAlchemy pattern implementations"""

    @pytest.fixture
    def library(self):
        """Create pattern library with SQLAlchemy patterns loaded"""
        # Connect to existing database without reinitializing schema
        import sqlite3

        db_path = Path("pattern_library.db")
        if not db_path.exists():
            raise FileNotFoundError("pattern_library.db not found. Run seed_data.py first")

        # Create library instance without calling __init__
        lib = PatternLibrary.__new__(PatternLibrary)
        lib.db_path = str(db_path)
        lib.db = sqlite3.connect(str(db_path))
        lib.db.row_factory = sqlite3.Row

        return lib

    def test_declare_pattern(self, library):
        """Test declare pattern compilation"""
        result = library.compile_pattern(
            pattern_name="declare",
            language_name="python_sqlalchemy",
            context={
                "variable_name": "total",
                "variable_type": "Decimal",
                "default_value": "Decimal('0')"
            }
        )

        assert result == "total: Decimal = Decimal('0')"

    def test_assign_pattern(self, library):
        """Test assign pattern compilation"""
        result = library.compile_pattern(
            pattern_name="assign",
            language_name="python_sqlalchemy",
            context={
                "variable_name": "total",
                "expression": "Decimal('100.50')"
            }
        )

        assert result == "total = Decimal('100.50')"

    def test_if_pattern(self, library):
        """Test if pattern compilation"""
        result = library.compile_pattern(
            pattern_name="if",
            language_name="python_sqlalchemy",
            context={
                "condition": "total > 0",
                "then_steps": "    return True",
                "else_steps": "    return False"
            }
        )

        expected = """if total > 0:
        return True
else:
        return False"""

        assert result == expected

    def test_foreach_pattern(self, library):
        """Test foreach pattern compilation"""
        result = library.compile_pattern(
            pattern_name="foreach",
            language_name="python_sqlalchemy",
            context={
                "iterator_var": "item",
                "collection": "items",
                "loop_body": "    print(item.name)"
            }
        )

        expected = """for item in items:
        print(item.name)"""

        assert result == expected

    def test_query_pattern(self, library):
        """Test query pattern compilation"""
        result = library.compile_pattern(
            pattern_name="query",
            language_name="python_sqlalchemy",
            context={
                "model_name": "User",
                "result_var": "users",
                "filters": {
                    "is_active": "True"
                }
            }
        )

        # Should contain basic query structure
        assert "# Query User" in result
        assert "users = session.query(User)" in result
        assert "User.is_active  is True" in result

    def test_insert_pattern(self, library):
        """Test insert pattern compilation"""
        result = library.compile_pattern(
            pattern_name="insert",
            language_name="python_sqlalchemy",
            context={
                "model_name": "User",
                "instance_var": "user",
                "field_values": {
                    "username": "'john_doe'",
                    "email": "'john@example.com'"
                }
            }
        )

        # Should contain insert structure
        assert "# Insert new User" in result
        assert "user = User(" in result
        assert "username='john_doe'" in result
        assert "session.add(user)" in result
        assert "session.commit()" in result

    def test_update_pattern(self, library):
        """Test update pattern compilation"""
        result = library.compile_pattern(
            pattern_name="update",
            language_name="python_sqlalchemy",
            context={
                "model_name": "User",
                "instance_var": "user",
                "lookup_value": "user_id",
                "field_values": {
                    "email": "'new_email@example.com'"
                }
            }
        )

        # Should contain update structure
        assert "# Update User" in result
        assert "user = session.query(User).get(user_id)" in result
        assert "user.email = 'new_email@example.com'" in result
        assert "session.commit()" in result

    def test_delete_pattern(self, library):
        """Test delete pattern compilation"""
        result = library.compile_pattern(
            pattern_name="delete",
            language_name="python_sqlalchemy",
            context={
                "model_name": "User",
                "instance_var": "user",
                "lookup_value": "user_id"
            }
        )

        # Should contain delete structure
        assert "# Delete User" in result
        assert "user = session.query(User).get(user_id)" in result
        assert "session.delete(user)" in result
        assert "session.commit()" in result

    def test_aggregate_pattern(self, library):
        """Test aggregate pattern compilation"""
        result = library.compile_pattern(
            pattern_name="aggregate",
            language_name="python_sqlalchemy",
            context={
                "model_name": "Order",
                "result_var": "stats",
                "aggregations": {
                    "total": "func.count(Order.id)"
                }
            }
        )

        # Should contain aggregate structure
        assert "# Aggregate Order" in result
        assert "stats = session.query(" in result
        assert "func.count(Order.id)" in result

    def test_call_function_pattern(self, library):
        """Test call_function pattern compilation"""
        result = library.compile_pattern(
            pattern_name="call_function",
            language_name="python_sqlalchemy",
            context={
                "result_variable": "result",
                "function_name": "calculate_total",
                "arguments": ["order.items", "tax_rate"]
            }
        )

        assert result == "result = calculate_total(order.items, tax_rate)"

    def test_return_pattern(self, library):
        """Test return pattern compilation"""
        result = library.compile_pattern(
            pattern_name="return",
            language_name="python_sqlalchemy",
            context={
                "expression": "JsonResponse({'status': 'success'})"
            }
        )

        assert result == "return JsonResponse({'status': 'success'})"

    def test_validate_pattern(self, library):
        """Test validate pattern compilation"""
        result = library.compile_pattern(
            pattern_name="validate",
            language_name="python_sqlalchemy",
            context={
                "model_name": "User",
                "instance_var": "user",
                "custom_validators": ["validate_email", "validate_age"]
            }
        )

        # Should contain validation structure
        assert "# Validate User" in result
        assert "validate_email(user)" in result
        assert "validate_age(user)" in result

    def test_duplicate_check_pattern(self, library):
        """Test duplicate_check pattern compilation"""
        result = library.compile_pattern(
            pattern_name="duplicate_check",
            language_name="python_sqlalchemy",
            context={
                "model_name": "User",
                "check_fields": {"email": "email_value"},
                "exists_var": "email_exists",
                "exclude_pk": "current_user_id"
            }
        )

        # Should contain duplicate check structure
        assert "# Check for duplicates" in result
        assert "email_exists = session.query(User).filter(" in result
        assert "User.email == email_value" in result

    def test_exception_handling_pattern(self, library):
        """Test exception_handling pattern compilation"""
        result = library.compile_pattern(
            pattern_name="exception_handling",
            language_name="python_sqlalchemy",
            context={
                "try_body": "    result = risky_operation()",
                "exception_handlers": [("ValueError", "    handle_value_error()")],
                "finally_body": "    cleanup()"
            }
        )

        # Should contain try-except structure
        assert "try:" in result
        assert "result = risky_operation()" in result
        assert "except ValueError:" in result
        assert "finally:" in result

    def test_json_build_pattern(self, library):
        """Test json_build pattern compilation"""
        result = library.compile_pattern(
            pattern_name="json_build",
            language_name="python_sqlalchemy",
            context={
                "json_structure": {"name": "user.name", "email": "user.email"},
                "result_var": "user_data",
                "serialize": True
            }
        )

        # Should contain JSON build structure
        assert "# Build JSON structure" in result
        assert "user_data = {" in result
        assert '"name": user.name' in result
        assert '"email": user.email' in result
        assert "json.dumps(user_data)" in result