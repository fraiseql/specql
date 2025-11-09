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
            {"name": "convert_to_customer", "description": "Convert qualified lead to customer"},
        ]

    def test_generate_pytest_integration_tests(
        self, generator, sample_entity_config, sample_actions
    ):
        """pytest generator should create integration tests."""
        code = generator.generate_pytest_integration_tests(sample_entity_config, sample_actions)

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
        code = generator.generate_pytest_integration_tests(sample_entity_config, sample_actions)

        assert "import pytest" in code
        assert "from uuid import UUID" in code
        assert "import psycopg" in code

    def test_generate_pytest_integration_tests_fixtures(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include database fixtures."""
        code = generator.generate_pytest_integration_tests(sample_entity_config, sample_actions)

        assert "@pytest.fixture" in code
        assert "def clean_db(self, test_db_connection):" in code
        assert "DELETE FROM crm.tb_contact" in code

    def test_generate_pytest_integration_tests_create_test(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include create functionality test."""
        code = generator.generate_pytest_integration_tests(sample_entity_config, sample_actions)

        assert "app.create_contact(" in code
        assert "assert result['status'] == 'success'" in code
        assert "assert result['object_data']['id'] is not None" in code

    def test_generate_pytest_integration_tests_duplicate_test(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include duplicate creation failure test."""
        code = generator.generate_pytest_integration_tests(sample_entity_config, sample_actions)

        assert "test_create_duplicate_contact_fails" in code
        assert "result2['status'].startswith('failed:')" in code
        assert "'duplicate' in result2['message'].lower()" in code

    def test_generate_pytest_integration_tests_crud_workflow(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include full CRUD workflow test."""
        code = generator.generate_pytest_integration_tests(sample_entity_config, sample_actions)

        assert "test_full_crud_workflow" in code
        assert "CREATE" in code
        assert "UPDATE" in code
        assert "DELETE" in code
        assert "VERIFY DELETED" in code

    def test_generate_pytest_integration_tests_action_tests(
        self, generator, sample_entity_config, sample_actions
    ):
        """Generated tests should include action-specific tests."""
        code = generator.generate_pytest_integration_tests(sample_entity_config, sample_actions)

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
        method_code = generator._generate_action_test_method(action, sample_entity_config)

        assert "def test_qualify_lead(self, clean_db):" in method_code
        assert "crm.qualify_lead(" in method_code
        assert "assert action_result['status'] == 'success'" in method_code
