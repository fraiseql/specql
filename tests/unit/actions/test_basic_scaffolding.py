"""
Tests for Basic Action Compiler Scaffolding
Phase 1: Function Scaffolding & Basic Returns
"""

import pytest

from src.core.ast_models import Action, ActionStep, Entity, FieldDefinition
from src.generators.actions.action_compiler import ActionCompiler


class TestBasicScaffolding:
    """Test basic PL/pgSQL function generation"""

    @pytest.fixture
    def compiler(self):
        """Create action compiler instance"""
        return ActionCompiler()

    @pytest.fixture
    def contact_entity(self):
        """Create test Contact entity"""
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text"),
                "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company"),
            },
        )

    def test_generate_basic_function_signature(self, compiler, contact_entity):
        """Test: Generate function with correct signature"""
        action = Action(name="create_contact", steps=[ActionStep(type="insert", entity="Contact")])

        sql = compiler.compile_action(action, contact_entity)

        # Expected: function exists with proper signature
        assert "CREATE OR REPLACE FUNCTION crm.create_contact(" in sql
        assert "RETURNS mutation_result AS $$" in sql
        assert "LANGUAGE plpgsql" in sql

    def test_generate_function_parameters(self, compiler, contact_entity):
        """Test: Generate parameters from field inputs"""
        action = Action(name="create_contact", steps=[])
        entity = Entity(
            name="Contact",
            fields={
                "email": FieldDefinition(name="email", type_name="text"),
                "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company"),
            },
        )

        sql = compiler.compile_action(action, entity)

        # Expected: UUID parameters for ref fields, native types for others
        assert "p_email TEXT" in sql
        assert "p_company_id UUID" in sql
        assert "p_caller_id UUID DEFAULT NULL" in sql  # Auto-added caller context

    def test_basic_success_response(self, compiler, contact_entity):
        """Test: Generate basic success response structure"""
        action = Action(name="create_contact", steps=[ActionStep(type="insert", entity="Contact")])

        sql = compiler.compile_action(action, contact_entity)

        # Expected: mutation_result structure
        assert "v_result mutation_result;" in sql
        assert "v_result.status := 'success';" in sql
        assert "v_result.message :=" in sql
        assert "v_result.object_data :=" in sql
        assert "RETURN v_result;" in sql

    def test_trinity_resolution_for_update_action(self, compiler, contact_entity):
        """Test: Auto-generate Trinity resolution for actions needing pk"""
        action = Action(name="update_contact", steps=[ActionStep(type="update", entity="Contact")])

        sql = compiler.compile_action(action, contact_entity)

        # Expected: Trinity helper call
        assert "v_pk INTEGER;" in sql
        assert "v_pk := crm.contact_pk(p_contact_id);" in sql
