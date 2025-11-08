"""
Tests for Function Generator
"""

import pytest
from src.core.ast_models import Entity, FieldDefinition, Action
from src.generators.function_generator import FunctionGenerator
from tests.fixtures.mock_entities import mock_contact_entity, mock_simple_entity


class TestFunctionGenerator:
    """Test function generation"""

    @pytest.fixture
    def generator(self):
        """Create function generator instance"""
        return FunctionGenerator()

    def test_generate_crud_functions_simple_entity(self, generator):
        """Test CRUD function generation for simple entity"""
        entity = mock_simple_entity()

        # Enable all operations
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(create=True, update=True, delete="soft")

        sql = generator.generate_crud_functions(entity)

        # Check that all CRUD functions are generated
        assert "CREATE OR REPLACE FUNCTION inventory.fn_create_product" in sql
        assert "CREATE OR REPLACE FUNCTION inventory.fn_update_product" in sql
        assert "CREATE OR REPLACE FUNCTION inventory.fn_delete_product" in sql

        # Check function signatures
        assert "p_input JSONB" in sql
        assert "RETURNS JSONB" in sql
        assert "LANGUAGE plpgsql" in sql

    def test_generate_create_function(self, generator):
        """Test individual create function generation"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(create=True)

        sql = generator._generate_create_function(entity)

        # Check basic structure
        assert "CREATE OR REPLACE FUNCTION inventory.fn_create_product" in sql
        assert "p_input JSONB" in sql
        assert "RETURNS JSONB" in sql
        assert "LANGUAGE plpgsql" in sql

        # Check INSERT logic
        assert "INSERT INTO inventory.tb_product" in sql
        assert "name, price" in sql
        assert "v_data.name, v_data.price" in sql
        assert "RETURNING pk_product, id INTO v_pk, v_uuid" in sql

    def test_generate_update_function(self, generator):
        """Test individual update function generation"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(update=True)

        sql = generator._generate_update_function(entity)

        # Check basic structure
        assert "CREATE OR REPLACE FUNCTION inventory.fn_update_product" in sql
        assert "p_id TEXT" in sql
        assert "p_input JSONB" in sql

        # Check UPDATE logic
        assert "UPDATE inventory.tb_product" in sql
        assert "WHERE pk_product = v_pk" in sql

    def test_generate_delete_function(self, generator):
        """Test individual delete function generation"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(delete="soft")

        sql = generator._generate_delete_function(entity)

        # Check soft delete logic
        assert "UPDATE inventory.tb_product" in sql
        assert "deleted_at = now()" in sql
        assert "WHERE pk_product = v_pk" in sql
        assert "AND deleted_at IS NULL" in sql

    def test_generate_action_functions(self, generator):
        """Test action function generation"""
        entity = mock_contact_entity()

        sql = generator.generate_action_functions(entity)

        # Should generate function for qualify_lead action
        assert "CREATE OR REPLACE FUNCTION crm.fn_qualify_lead" in sql
        assert "LANGUAGE plpgsql" in sql

    def test_convert_action_steps_to_plpgsql(self, generator):
        """Test conversion of action steps to PL/pgSQL"""
        entity = mock_contact_entity()

        # Get the qualify_lead action
        action = entity.actions[0]  # qualify_lead
        plpgsql = generator._convert_action_steps_to_plpgsql(entity, action.steps)

        # Check that validation step is converted
        assert "-- Validate:" in plpgsql
        assert "IF NOT" in plpgsql
        assert "END IF;" in plpgsql

        # Check that update step is converted
        assert "-- Update Contact" in plpgsql

        # Check that notify step is converted
        assert "-- Notify" in plpgsql

    def test_convert_expression_to_sql(self, generator):
        """Test expression conversion"""
        # Simple expression
        sql = generator._convert_expression_to_sql("status = 'lead'")
        assert sql == "status = 'lead'"

        # Empty expression
        sql = generator._convert_expression_to_sql("")
        assert sql == "true"

        # None expression
        sql = generator._convert_expression_to_sql(None)
        assert sql == "true"

    def test_function_generator_produces_app_core_layers(self, generator):
        """Function generator produces both app and core layers"""
        # Create entity with create action
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type="text", nullable=False),
                "company": FieldDefinition(
                    name="company", type="ref", target_entity="Company", nullable=True
                ),
                "status": FieldDefinition(
                    name="status", type="enum", values=["lead", "qualified"], nullable=False
                ),
            },
            actions=[Action(name="create_contact")],
        )

        # When: Generate functions
        sql = generator.generate_action_functions(entity)

        # Then: Contains app wrapper
        assert "CREATE OR REPLACE FUNCTION app.create_contact(" in sql
        # Then: Contains core logic
        assert "CREATE OR REPLACE FUNCTION crm.create_contact(" in sql

        # Then: App wrapper has correct signature
        assert "auth_tenant_id UUID" in sql
        assert "auth_user_id UUID" in sql
        assert "input_payload JSONB" in sql
        assert "RETURNS app.mutation_result" in sql

        # Then: Core function has correct signature
        assert "auth_tenant_id UUID" in sql
        assert "input_data app.type_create_contact_input" in sql
        assert "input_payload JSONB" in sql
        assert "auth_user_id UUID" in sql
        assert "RETURNS app.mutation_result" in sql

    # ===== AUTH CONTEXT FIXES FOR LEGACY GENERATOR =====

    def test_legacy_create_function_has_auth_params(self, generator):
        """Legacy create function should have auth_tenant_id and auth_user_id"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(create=True)

        sql = generator._generate_create_function(entity)

        assert "auth_tenant_id TEXT DEFAULT NULL" in sql
        assert "auth_user_id UUID DEFAULT NULL" in sql
        assert "created_by" in sql
        assert "auth_user_id" in sql.split("VALUES")[1]  # In INSERT values

    def test_legacy_create_uses_auth_user_for_created_by(self, generator):
        """Legacy create should set created_by = auth_user_id"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(create=True)

        sql = generator._generate_create_function(entity)

        # Should NOT have null for created_by
        assert "created_by = null" not in sql.lower()
        # Should have auth_user_id in VALUES
        values_section = sql.split("VALUES")[1]
        assert "auth_user_id" in values_section

    def test_legacy_update_function_has_auth_params(self, generator):
        """Legacy update function should have auth_tenant_id and auth_user_id"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(update=True)

        sql = generator._generate_update_function(entity)

        assert "auth_tenant_id TEXT DEFAULT NULL" in sql
        assert "auth_user_id UUID DEFAULT NULL" in sql
        assert "updated_by = auth_user_id" in sql

    def test_legacy_update_no_null_audit_fields(self, generator):
        """Legacy update should NOT have null for audit fields"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(update=True)

        sql = generator._generate_update_function(entity)

        # Should NOT have TODO or null for updated_by
        assert "TODO: Add user context" not in sql
        assert "updated_by = null" not in sql.lower()

    def test_legacy_delete_function_has_auth_params(self, generator):
        """Legacy delete function should have auth_tenant_id and auth_user_id"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(delete="soft")

        sql = generator._generate_delete_function(entity)

        assert "auth_tenant_id TEXT DEFAULT NULL" in sql
        assert "auth_user_id UUID DEFAULT NULL" in sql
        assert "deleted_by = auth_user_id" in sql
        assert "updated_by = auth_user_id" in sql

    def test_legacy_delete_no_null_audit_fields(self, generator):
        """Legacy delete should NOT have null for audit fields"""
        entity = mock_simple_entity()
        from src.core.ast_models import OperationConfig

        entity.operations = OperationConfig(delete="soft")

        sql = generator._generate_delete_function(entity)

        # Should NOT have null for deleted_by or updated_by
        assert "deleted_by = null" not in sql.lower()
        assert "updated_by = null" not in sql.lower()
        assert "TODO" not in sql

    def test_legacy_action_function_has_auth_params(self, generator):
        """Legacy action function should have auth_tenant_id and auth_user_id"""
        entity = mock_contact_entity()
        action = entity.actions[0]  # qualify_lead

        sql = generator._generate_action_function(entity, action)

        assert "auth_tenant_id TEXT DEFAULT NULL" in sql
        assert "auth_user_id UUID DEFAULT NULL" in sql
