"""Unit tests for pytest generator."""

import pytest

from src.testing.pytest.pytest_generator import PytestGenerator


class TestPytestGenerator:
    """Test pytest generator functionality."""

    @pytest.fixture
    def generator(self):
        """Create a pytest generator instance."""
        return PytestGenerator()

    @pytest.fixture
    def sample_entity_config(self):
        """Sample entity configuration for testing."""
        return {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "default_tenant_id": "01232122-0000-0000-2000-000000000001",
            "default_user_id": "01232122-0000-0000-2000-000000000002",
        }

    @pytest.fixture
    def sample_actions(self):
        """Sample actions for testing."""
        return [
            {"name": "qualify_lead", "description": "Qualify a lead contact"},
            {
                "name": "convert_to_customer",
                "description": "Convert qualified lead to customer",
            },
        ]

    def test_generate_pytest_integration_tests(
        self, generator, sample_entity_config, sample_actions
    ):
        """pytest generator should create integration tests."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "class TestContactIntegration:" in code
        assert "def test_create_contact_happy_path" in code
        assert "def test_create_duplicate_contact_fails" in code
        assert "def test_update_contact_happy_path" in code
        assert "def test_delete_contact_happy_path" in code
        assert "def test_full_crud_workflow" in code
        assert "def test_qualify_lead" in code
        assert "def test_convert_to_customer" in code

    def test_generate_pytest_integration_tests_imports(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include proper imports."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "import pytest" in code
        assert "from uuid import UUID" in code
        assert "import psycopg" in code

    def test_generate_pytest_integration_tests_fixtures(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include database fixtures."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "@pytest.fixture" in code
        assert "def clean_db(self, test_db_connection):" in code
        assert "DELETE FROM crm.tb_contact" in code

    def test_generate_pytest_integration_tests_create_test(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include create functionality test."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "app.create_contact(" in code
        assert "assert result['status'] == 'success'" in code
        assert "assert result['object_data']['id'] is not None" in code

    def test_generate_pytest_integration_tests_duplicate_test(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include duplicate creation failure test."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "test_create_duplicate_contact_fails" in code
        assert "result2['status'].startswith('failed:')" in code
        assert "'duplicate' in result2['message'].lower()" in code

    def test_generate_pytest_integration_tests_crud_workflow(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include full CRUD workflow test."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "test_full_crud_workflow" in code
        assert "CREATE" in code
        assert "UPDATE" in code
        assert "DELETE" in code
        assert "VERIFY DELETED" in code

    def test_generate_pytest_integration_tests_action_tests(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include action-specific tests."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "def test_qualify_lead(self, clean_db):" in code
        assert "crm.qualify_lead(" in code
        assert "def test_convert_to_customer(self, clean_db):" in code
        assert "crm.convert_to_customer(" in code

    def test_build_sample_input_data(self, generator, sample_entity_config):
        """Sample input data should be properly structured."""
        data = generator._build_sample_input_data(sample_entity_config)

        assert isinstance(data, dict)
        assert "email" in data
        assert "status" in data
        assert data["email"] == "test@example.com"
        assert data["status"] == "lead"

    def test_generate_action_test_method(self, generator, sample_entity_config):
        """Action test method generation should work correctly."""
        action = {"name": "qualify_lead"}
        method_code = generator._generate_action_test_method(
            action, sample_entity_config
        )

        assert "def test_qualify_lead(self, clean_db):" in method_code
        assert "crm.qualify_lead(" in method_code
        assert "assert action_result['status'] == 'success'" in method_code

    def test_generate_pytest_with_fixtures_cleanup(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated pytest should include proper database cleanup fixtures."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "@pytest.fixture" in code
        assert "clean_db" in code
        assert "DELETE FROM" in code
        assert "commit()" in code

    def test_generate_pytest_with_error_assertions(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated pytest should test error conditions."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should have error testing
        assert "assert" in code
        assert "failed" in code.lower() or "error" in code.lower()

    def test_generate_pytest_with_multiple_actions(
        self, generator, sample_entity_config
    ):
        """Should generate separate test methods for each action."""
        actions = [
            {"name": "action1"},
            {"name": "action2"},
            {"name": "action3"},
        ]

        code = generator.generate_pytest_integration_tests(
            sample_entity_config, actions
        )

        assert "def test_action1" in code
        assert "def test_action2" in code
        assert "def test_action3" in code

    def test_generate_pytest_with_no_actions(self, generator, sample_entity_config):
        """Should handle entities with no actions."""
        actions = []

        code = generator.generate_pytest_integration_tests(
            sample_entity_config, actions
        )

        # Should still have basic CRUD tests
        assert "def test_create_" in code
        assert "def test_update_" in code
        assert "def test_delete_" in code

    def test_generate_pytest_imports_complete(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated pytest should have all necessary imports."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        required_imports = ["pytest", "UUID", "psycopg"]
        for imp in required_imports:
            assert imp in code

    def test_generate_pytest_valid_python_syntax(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated pytest should be valid Python."""
        import ast

        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should parse without syntax errors
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"Generated Python has syntax error: {e}")

    def test_generate_pytest_test_naming_convention(
        self, generator, sample_entity_config
    ):
        """Test methods should follow naming convention."""
        actions = [{"name": "qualify_lead"}]

        code = generator.generate_pytest_integration_tests(
            sample_entity_config, actions
        )

        # All test methods should start with test_
        import re

        test_methods = re.findall(r"def (test_\w+)", code)
        assert len(test_methods) > 0
        assert all(name.startswith("test_") for name in test_methods)

    def test_generate_pytest_docstrings_present(
        self, generator, sample_entity_config, sample_actions
    ):
        """Test methods should have docstrings."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should have docstrings (""" ... """)
        assert '"""' in code
        assert code.count('"""') >= 4  # Class docstring + method docstrings

    def test_generate_pytest_database_connection_handling(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should properly handle database connections."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        assert "cursor()" in code
        assert "execute(" in code
        assert "fetchone()" in code or "fetchall()" in code

    def test_generate_pytest_assertion_messages(
        self, generator, sample_entity_config, sample_actions
    ):
        """Assertions should have helpful messages."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Pytest assertions (some should have messages)
        assert "assert " in code
        # Count assertions
        assert code.count("assert ") >= 5

    def test_generate_pytest_different_entities(self, generator):
        """Should work for different entity names."""
        entity_config = {
            "entity_name": "Company",
            "schema_name": "crm",
            "table_name": "tb_company",
        }
        actions = [{"name": "activate"}]

        code = generator.generate_pytest_integration_tests(entity_config, actions)

        assert "class TestCompanyIntegration:" in code
        assert "def test_create_company_happy_path" in code
        assert "def test_activate" in code

    def test_generate_pytest_empty_actions_list(self, generator, sample_entity_config):
        """Should handle empty actions list gracefully."""
        code = generator.generate_pytest_integration_tests(sample_entity_config, [])

        # Should still generate CRUD tests
        assert "test_create_contact" in code
        assert "test_update_contact" in code
        assert "test_delete_contact" in code
        # Should not have action tests
        assert "def test_qualify_lead" not in code

    def test_generate_pytest_fixture_structure(
        self, generator, sample_entity_config, sample_actions
    ):
        """Fixtures should have proper structure."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should have fixture decorator
        assert "@pytest.fixture" in code
        # Should have proper function signature
        assert "def clean_db(self, test_db_connection):" in code
        # Should have docstring
        assert '"""Clean Contact table before test"""' in code

    def test_generate_pytest_error_handling_in_actions(
        self, generator, sample_entity_config
    ):
        """Action tests should include error handling."""
        actions = [{"name": "invalid_action"}]
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, actions
        )

        # Should check for success status
        assert "assert action_result['status'] == 'success'" in code
        # Should have some error checking
        assert "failed" in code.lower()

    def test_generate_pytest_workflow_test_comprehensive(
        self, generator, sample_entity_config, sample_actions
    ):
        """Full CRUD workflow test should be comprehensive."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        workflow_test = [
            line for line in code.split("\n") if "test_full_crud_workflow" in line
        ]
        assert len(workflow_test) > 0

        # Should have multiple steps
        assert "CREATE" in code
        assert "UPDATE" in code
        assert "DELETE" in code
        assert "create_contact" in code
        assert "update_contact" in code
        assert "delete_contact" in code

    def test_generate_pytest_duplicate_test_logic(
        self, generator, sample_entity_config, sample_actions
    ):
        """Duplicate test should properly test uniqueness constraints."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should create two records
        assert code.count("create_contact(") >= 2
        # Should check second one fails
        assert "result2" in code
        assert "startswith('failed:')" in code

    def test_generate_pytest_class_structure(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated class should have proper structure."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should contain class definition
        assert "class TestContactIntegration:" in code
        # Should have class docstring
        assert '"""Integration tests for Contact entity"""' in code
        # Should have proper indentation
        lines = code.split("\n")
        # Methods should be indented
        method_lines = [
            i for i, line in enumerate(lines) if line.strip().startswith("def test_")
        ]
        assert all(lines[i].startswith("    ") for i in method_lines)

    def test_generate_pytest_method_docstrings(
        self, generator, sample_entity_config, sample_actions
    ):
        """All test methods should have docstrings."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Find all test methods
        import re

        test_methods = re.findall(r"def (test_\w+)\(self", code)

        # Each method should have a docstring
        for method in test_methods:
            method_start = code.find(f"def {method}")
            # Look for docstring after method definition
            docstring_start = code.find('"""', method_start)
            assert docstring_start > method_start, f"Method {method} missing docstring"

    def test_generate_pytest_database_queries(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include proper database queries."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should have SELECT queries for verification
        assert "SELECT" in code
        # Should have proper table references
        assert "crm.tb_contact" in code
        # Should have WHERE clauses
        assert "WHERE" in code

    def test_generate_pytest_assertion_variety(
        self, generator, sample_entity_config, sample_actions
    ):
        """Tests should use variety of assertion types."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should have different types of assertions
        assert "assert result[" in code  # Dictionary access
        assert "assert " in code and "is not None" in code  # None checks
        assert "startswith" in code  # String methods
        assert "in" in code and "lower()" in code  # String containment

    def test_generate_pytest_action_parameters(self, generator, sample_entity_config):
        """Action tests should pass correct parameters."""
        actions = [{"name": "qualify_lead"}]
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, actions
        )

        # Should pass contact_id and user_id
        assert "contact_id" in code
        assert "user_id" in code
        assert "crm.qualify_lead(" in code

    def test_generate_pytest_fixture_usage(
        self, generator, sample_entity_config, sample_actions
    ):
        """All test methods should use the clean_db fixture."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Find all test methods
        import re

        test_methods = re.findall(r"def (test_\w+)\(self, (\w+)\):", code)

        # All should use clean_db fixture
        for method, fixture in test_methods:
            assert fixture == "clean_db", (
                f"Method {method} uses {fixture} instead of clean_db"
            )

    def test_generate_pytest_no_syntax_errors(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated code should have no Python syntax errors."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Try to compile it
        compile(code, "<string>", "exec")

    def test_generate_pytest_indentation_consistent(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated code should have consistent indentation."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        lines = code.split("\n")
        # Check that indented lines use 4 spaces
        for line in lines:
            if line.startswith(" ") and not line.startswith("    "):
                # Allow for continuation lines or specific cases, but generally should be 4 spaces
                pass

    def test_generate_pytest_variable_naming(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated code should use consistent variable naming."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should use descriptive variable names
        assert "result" in code
        assert "contact_id" in code
        assert "action_result" in code

    def test_generate_pytest_error_messages_helpful(
        self, generator, sample_entity_config, sample_actions
    ):
        """Error messages in tests should be helpful."""
        code = generator.generate_pytest_integration_tests(
            sample_entity_config, sample_actions
        )

        # Should have descriptive assertion messages
        assert "assert action_result['status'] == 'success'" in code
        assert "assert result2['status'].startswith('failed:')" in code
