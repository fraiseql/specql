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

    def test_function_generator_produces_app_core_layers(self, generator):
        """Function generator produces both app and core layers"""
        # Create entity with create action
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False),
                "company": FieldDefinition(name="company", type_name="ref", nullable=True),
                "status": FieldDefinition(name="status", type_name="enum", nullable=False),
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
