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
            {
                "field_name": "first_name",
                "field_type": "text",
                "generator_type": "random",
            },
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

    def test_generate_structure_tests_table_exists(
        self, generator, sample_entity_config
    ):
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
        assert (
            "has_column('crm', 'tb_contact', 'identifier', 'Has TEXT identifier')"
            in sql
        )
        assert "has_column('crm', 'tb_contact', 'created_at', 'Has created_at')" in sql
        assert "has_column('crm', 'tb_contact', 'updated_at', 'Has updated_at')" in sql
        assert (
            "has_column('crm', 'tb_contact', 'deleted_at', 'Has deleted_at for soft delete')"
            in sql
        )

    def test_generate_structure_tests_constraints(
        self, generator, sample_entity_config
    ):
        """Structure tests should check constraints."""
        sql = generator.generate_structure_tests(sample_entity_config)

        assert (
            "col_is_pk('crm', 'tb_contact', 'pk_contact', 'pk_contact is primary key')"
            in sql
        )
        assert "col_is_unique('crm', 'tb_contact', 'id', 'id is unique')" in sql

    def test_generate_crud_tests(
        self, generator, sample_entity_config, sample_field_mappings
    ):
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

    def test_generate_structure_tests_different_entities(self, generator):
        """Structure tests should work for different entity names."""
        entity_config = {
            "entity_name": "Company",
            "schema_name": "crm",
            "table_name": "tb_company",
        }

        sql = generator.generate_structure_tests(entity_config)

        assert "Company" in sql
        assert "tb_company" in sql
        assert "pk_company" in sql
        assert "SELECT plan(10)" in sql

    def test_generate_crud_tests_different_field_types(self, generator):
        """CRUD tests should handle various field types."""
        entity_config = {
            "entity_name": "Product",
            "schema_name": "inventory",
            "table_name": "tb_product",
        }

        field_mappings = [
            {"field_name": "name", "field_type": "text", "generator_type": "random"},
            {"field_name": "price", "field_type": "numeric", "generator_type": "fixed"},
            {
                "field_name": "in_stock",
                "field_type": "boolean",
                "generator_type": "fixed",
            },
            {
                "field_name": "category_id",
                "field_type": "uuid",
                "generator_type": "random",
            },
        ]

        sql = generator.generate_crud_tests(entity_config, field_mappings)

        assert "inventory" in sql
        assert "tb_product" in sql
        assert "app.create_product" in sql
        assert '"name": "test_name"' in sql
        assert '"price": "test_price"' in sql
        assert '"in_stock": true' in sql
        assert '"category_id": "01232122-0000-0000-2000-000000000001"' in sql

    def test_generate_crud_tests_empty_fields(self, generator):
        """CRUD tests should handle entities with no fields."""
        entity_config = {
            "entity_name": "EmptyEntity",
            "schema_name": "test",
            "table_name": "tb_empty",
        }

        field_mappings = []

        sql = generator.generate_crud_tests(entity_config, field_mappings)

        assert "app.create_emptyentity" in sql
        assert "'{}'::JSONB" in sql  # Empty JSON object

    def test_generate_constraint_tests_multiple_scenarios(
        self, generator, sample_entity_config
    ):
        """Constraint tests should handle multiple scenarios."""
        scenarios = [
            {
                "scenario_type": "constraint_violation",
                "scenario_name": "duplicate_scenario_1",
                "input_overrides": {"email": "dup1@example.com"},
                "expected_error_code": "duplicate",
            },
            {
                "scenario_type": "constraint_violation",
                "scenario_name": "duplicate_scenario_2",
                "input_overrides": {"email": "dup2@example.com"},
                "expected_error_code": "unique_violation",
            },
        ]

        sql = generator.generate_constraint_tests(sample_entity_config, scenarios)

        assert "duplicate_scenario_1" in sql
        assert "duplicate_scenario_2" in sql
        assert sql.count("DO $$") == 2

    def test_generate_constraint_tests_empty_scenarios(
        self, generator, sample_entity_config
    ):
        """Constraint tests should handle empty scenarios."""
        scenarios = []

        sql = generator.generate_constraint_tests(sample_entity_config, scenarios)

        assert sql == ""

    def test_generate_action_tests_different_actions(
        self, generator, sample_entity_config
    ):
        """Action tests should work for different actions."""
        actions = [{"name": "activate"}, {"name": "deactivate"}]
        scenarios = [
            {
                "target_action": "activate",
                "scenario_name": "activate_success",
                "expected_result": "success",
                "setup_sql": "-- Setup for activate",
            },
            {
                "target_action": "deactivate",
                "scenario_name": "deactivate_success",
                "expected_result": "success",
                "setup_sql": "-- Setup for deactivate",
            },
        ]

        sql = generator.generate_action_tests(sample_entity_config, actions, scenarios)

        assert "activate_success" in sql
        assert "deactivate_success" in sql
        assert "crm.activate" in sql
        assert "crm.deactivate" in sql

    def test_generate_action_tests_empty_scenarios(
        self, generator, sample_entity_config
    ):
        """Action tests should handle actions with no scenarios."""
        actions = [{"name": "some_action"}]
        scenarios = []

        sql = generator.generate_action_tests(sample_entity_config, actions, scenarios)

        assert sql == ""

    def test_generate_action_tests_failure_scenarios(
        self, generator, sample_entity_config
    ):
        """Action tests should handle failure scenarios."""
        actions = [{"name": "qualify_lead"}]
        scenarios = [
            {
                "target_action": "qualify_lead",
                "scenario_name": "should_fail",
                "expected_result": "failed:invalid_state",
                "setup_sql": "-- Setup invalid state",
            }
        ]

        sql = generator.generate_action_tests(sample_entity_config, actions, scenarios)

        assert "should_fail" in sql
        assert "isnt" in sql  # Should use isnt for failure
        assert "should fail" in sql

    def test_generate_structure_tests_sql_structure(
        self, generator, sample_entity_config
    ):
        """Structure tests should have proper SQL structure."""
        sql = generator.generate_structure_tests(sample_entity_config)

        # Should start with comment
        assert sql.startswith("-- Structure Tests")

        # Should have BEGIN and ROLLBACK
        assert "BEGIN;" in sql
        assert "ROLLBACK;" in sql

        # Should have SELECT plan
        assert "SELECT plan(10)" in sql

        # Should end with finish
        assert "SELECT * FROM finish();" in sql

    def test_generate_crud_tests_sql_structure(
        self, generator, sample_entity_config, sample_field_mappings
    ):
        """CRUD tests should have proper SQL structure."""
        sql = generator.generate_crud_tests(sample_entity_config, sample_field_mappings)

        # Should start with comment
        assert sql.startswith("-- CRUD Tests")

        # Should have BEGIN and ROLLBACK
        assert "BEGIN;" in sql
        assert "ROLLBACK;" in sql

        # Should have SELECT plan
        assert "SELECT plan(15)" in sql

        # Should have PREPARE statement
        assert "PREPARE create_test" in sql

        # Should have DO blocks
        assert "DO $$" in sql

        # Should end with finish
        assert "SELECT * FROM finish();" in sql

    def test_generate_action_tests_sql_structure(self, generator, sample_entity_config):
        """Action tests should have proper SQL structure."""
        actions = [{"name": "test_action"}]
        scenarios = [
            {
                "target_action": "test_action",
                "scenario_name": "test_scenario",
                "expected_result": "success",
                "setup_sql": "",
            }
        ]

        sql = generator.generate_action_tests(sample_entity_config, actions, scenarios)

        # Should start with comment
        assert sql.startswith("-- Action Test")

        # Should have BEGIN and ROLLBACK
        assert "BEGIN;" in sql
        assert "ROLLBACK;" in sql

        # Should have SELECT plan
        assert "SELECT plan(5)" in sql

        # Should have DO block
        assert "DO $$" in sql

        # Should end with finish
        assert "SELECT * FROM finish();" in sql
