"""Unit tests for pgTAP generator."""

import pytest

from src.testing.pgtap.pgtap_generator import PgTAPGenerator


class TestPgTAPGenerator:
    """Test pgTAP generator functionality."""

    @pytest.fixture
    def generator(self):
        """Create a pgTAP generator instance."""
        return PgTAPGenerator()

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
    def sample_field_mappings(self):
        """Sample field mappings for testing."""
        return [
            {"field_name": "email", "field_type": "email", "generator_type": "random"},
            {
                "field_name": "status",
                "field_type": "enum(lead,qualified,customer)",
                "generator_type": "fixed",
            },
            {"field_name": "first_name", "field_type": "text", "generator_type": "random"},
        ]

    def test_generate_structure_tests(self, generator, sample_entity_config):
        """pgTAP generator should create structure tests."""
        sql = generator.generate_structure_tests(sample_entity_config)

        assert "has_table" in sql
        assert "has_column" in sql
        assert "col_is_pk" in sql
        assert "col_is_unique" in sql
        assert "crm" in sql
        assert "tb_contact" in sql
        assert "Contact" in sql
        assert "SELECT plan(10)" in sql
        assert "SELECT * FROM finish()" in sql

    def test_generate_structure_tests_table_exists(self, generator, sample_entity_config):
        """Structure tests should check table exists."""
        sql = generator.generate_structure_tests(sample_entity_config)

        assert "has_table(" in sql
        assert "'crm'::name" in sql
        assert "'tb_contact'::name" in sql
        assert "Contact table should exist" in sql

    def test_generate_structure_tests_columns(self, generator, sample_entity_config):
        """Structure tests should check required columns."""
        sql = generator.generate_structure_tests(sample_entity_config)

        assert "has_column('crm', 'tb_contact', 'pk_contact', 'Has INTEGER PK')" in sql
        assert "has_column('crm', 'tb_contact', 'id', 'Has UUID id')" in sql
        assert "has_column('crm', 'tb_contact', 'identifier', 'Has TEXT identifier')" in sql
        assert "has_column('crm', 'tb_contact', 'created_at', 'Has created_at')" in sql
        assert "has_column('crm', 'tb_contact', 'updated_at', 'Has updated_at')" in sql
        assert (
            "has_column('crm', 'tb_contact', 'deleted_at', 'Has deleted_at for soft delete')" in sql
        )

    def test_generate_structure_tests_constraints(self, generator, sample_entity_config):
        """Structure tests should check constraints."""
        sql = generator.generate_structure_tests(sample_entity_config)

        assert "col_is_pk('crm', 'tb_contact', 'pk_contact', 'pk_contact is primary key')" in sql
        assert "col_is_unique('crm', 'tb_contact', 'id', 'id is unique')" in sql

    def test_generate_crud_tests(self, generator, sample_entity_config, sample_field_mappings):
        """pgTAP generator should create CRUD tests."""
        sql = generator.generate_crud_tests(sample_entity_config, sample_field_mappings)

        assert "app.create_contact" in sql
        assert "lives_ok" in sql
        assert "SELECT plan(15)" in sql
        assert "SELECT * FROM finish()" in sql

    def test_generate_crud_tests_input_json(
        self, generator, sample_entity_config, sample_field_mappings
    ):
        """CRUD tests should build correct input JSON."""
        sql = generator.generate_crud_tests(sample_entity_config, sample_field_mappings)

        # Should contain JSON with test data
        assert '"email": "test@example.com"' in sql
        assert '"status": "lead"' in sql
        assert '"first_name": "test_first_name"' in sql

    def test_generate_crud_tests_create_succeeds(
        self, generator, sample_entity_config, sample_field_mappings
    ):
        """CRUD tests should verify CREATE succeeds."""
        sql = generator.generate_crud_tests(sample_entity_config, sample_field_mappings)

        assert "CREATE should return success status" in sql
        assert "CREATE should return object_data" in sql
        assert "object_data should contain id" in sql

    def test_generate_crud_tests_record_exists(
        self, generator, sample_entity_config, sample_field_mappings
    ):
        """CRUD tests should verify record exists in database."""
        sql = generator.generate_crud_tests(sample_entity_config, sample_field_mappings)

        assert "Record should exist in table" in sql
        assert "crm.tb_contact" in sql

    def test_generate_constraint_tests(self, generator, sample_entity_config):
        """pgTAP generator should create constraint tests."""
        scenarios = [
            {
                "scenario_type": "constraint_violation",
                "scenario_name": "duplicate_email",
                "input_overrides": {"email": "duplicate@example.com"},
                "expected_error_code": "duplicate",
            }
        ]

        sql = generator.generate_constraint_tests(sample_entity_config, scenarios)

        assert "Constraint Test: duplicate_email" in sql
        assert "First insert should succeed" in sql
        assert "should fail with error" in sql
        assert "Error message should mention constraint violation" in sql

    def test_generate_action_tests(self, generator, sample_entity_config):
        """pgTAP generator should create action tests."""
        actions = [{"name": "qualify_lead"}]

        scenarios = [
            {
                "target_action": "qualify_lead",
                "scenario_name": "valid_lead_qualification",
                "expected_result": "success",
                "setup_sql": "-- Setup: Create lead contact",
            }
        ]

        sql = generator.generate_action_tests(sample_entity_config, actions, scenarios)

        assert "Action Test: qualify_lead - valid_lead_qualification" in sql
        assert "crm.qualify_lead" in sql
        assert "SELECT plan(5)" in sql
        assert "updated_fields should not be empty" in sql
        assert "object_data should contain result" in sql

    def test_generate_action_tests_setup_sql(self, generator, sample_entity_config):
        """Action tests should include setup SQL."""
        actions = [{"name": "qualify_lead"}]
        scenarios = [
            {
                "target_action": "qualify_lead",
                "scenario_name": "test",
                "expected_result": "success",
                "setup_sql": "-- Custom setup SQL",
            }
        ]

        sql = generator.generate_action_tests(sample_entity_config, actions, scenarios)

        assert "-- Custom setup SQL" in sql
