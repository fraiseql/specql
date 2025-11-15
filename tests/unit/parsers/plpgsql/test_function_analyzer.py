"""Unit tests for FunctionAnalyzer"""

import pytest
from src.parsers.plpgsql.function_analyzer import FunctionAnalyzer
from src.core.universal_ast import StepType


class TestFunctionAnalyzer:
    """Test PL/pgSQL function parsing"""

    @pytest.fixture
    def analyzer(self):
        """Create FunctionAnalyzer instance"""
        return FunctionAnalyzer()

    def test_parse_function_with_insert(self, analyzer):
        """Test parsing function with INSERT statement"""
        function = {
            "routine_name": "create_contact",
            "routine_definition": """
            BEGIN
                INSERT INTO contact (email, name) VALUES (p_email, p_name);
            END;
            """,
            "external_language": "PLPGSQL",
        }

        action = analyzer.parse_function(function)

        assert action is not None
        assert action.name == "create_contact"
        assert action.entity == "Contact"
        assert len(action.steps) == 1
        assert action.steps[0].type == StepType.INSERT
        assert action.steps[0].entity == "Contact"

    def test_parse_function_with_schema_qualified_table(self, analyzer):
        """Test parsing function with schema.table reference"""
        function = {
            "routine_name": "create_contact",
            "routine_definition": """
            BEGIN
                INSERT INTO crm.contact (email, name) VALUES (p_email, p_name);
            END;
            """,
            "external_language": "PLPGSQL",
        }

        action = analyzer.parse_function(function)

        assert action is not None
        assert action.steps[0].entity == "Contact"

    def test_parse_function_non_plpgsql(self, analyzer):
        """Test that non-PL/pgSQL functions are ignored"""
        function = {
            "routine_name": "create_contact",
            "routine_definition": "SELECT 1;",
            "external_language": "SQL",
        }

        action = analyzer.parse_function(function)

        assert action is None

    def test_parse_function_no_statements(self, analyzer):
        """Test function with no parseable statements"""
        function = {
            "routine_name": "empty_function",
            "routine_definition": """
            BEGIN
                -- Just a comment
                NULL;
            END;
            """,
            "external_language": "PLPGSQL",
        }

        action = analyzer.parse_function(function)

        assert action is None

    def test_extract_entity_from_function_name(self, analyzer):
        """Test entity name extraction from function names"""
        test_cases = [
            ("create_contact", "Contact"),
            ("update_order", "Order"),
            ("delete_user", "User"),
            ("app_create_lead", "Lead"),
            ("core_update_status", "Status"),
            ("unknown_function", "Unknown"),
        ]

        for func_name, expected_entity in test_cases:
            assert (
                analyzer._extract_entity_from_function_name(func_name)
                == expected_entity
            )

    def test_parse_if_statement(self, analyzer):
        """Test parsing IF validation statements"""
        stmt = "IF status != 'pending' THEN RAISE EXCEPTION 'not_pending'; END IF;"

        step = analyzer._parse_if_statement(stmt)

        assert step is not None
        assert step.type == StepType.VALIDATE
        assert "status = 'pending'" in step.expression

    def test_parse_update_statement(self, analyzer):
        """Test parsing UPDATE statements"""
        stmt = "UPDATE contact SET status = 'active' WHERE pk_contact = v_id;"

        step = analyzer._parse_update_statement(stmt)

        assert step is not None
        assert step.type == StepType.UPDATE
        assert step.entity == "Contact"
        assert step.fields["status"] == "'active'"

    def test_parse_delete_statement(self, analyzer):
        """Test parsing DELETE statements"""
        stmt = "DELETE FROM contact WHERE pk_contact = v_id;"

        step = analyzer._parse_delete_statement(stmt)

        assert step is not None
        assert step.type == StepType.DELETE
        assert step.entity == "Contact"

    def test_parse_raise_exception(self, analyzer):
        """Test parsing RAISE EXCEPTION statements"""
        stmt = "RAISE EXCEPTION 'validation_error';"

        step = analyzer._parse_raise_exception(stmt)

        assert step is not None
        assert step.type == StepType.VALIDATE
        assert "error_code = 'validation_error'" in step.expression

    def test_table_to_entity_name(self, analyzer):
        """Test table name to entity name conversion"""
        test_cases = [
            ("tb_contact", "Contact"),
            ("contact", "Contact"),
            ("user_profile", "UserProfile"),
            ("order_items", "OrderItems"),
        ]

        for table_name, expected_entity in test_cases:
            assert analyzer._table_to_entity_name(table_name) == expected_entity
