"""
Unit tests for ActionOrchestrator
"""

import pytest
from src.generators.actions.action_orchestrator import ActionOrchestrator
from src.core.ast_models import ActionDefinition, EntityDefinition, ActionStep, FieldDefinition


class TestActionOrchestrator:
    """Test ActionOrchestrator functionality"""

    def setup_method(self):
        """Set up test fixtures"""

        # Mock step compiler registry
        class MockStepCompiler:
            def compile(self, step, entity, context):
                return f"-- Mock compiled: {step.type}"

        self.mock_registry = {
            "validate": MockStepCompiler(),
            "update": MockStepCompiler(),
            "foreach": MockStepCompiler(),
            "call": MockStepCompiler(),
            "notify": MockStepCompiler(),
        }

        self.orchestrator = ActionOrchestrator(step_compiler_registry=self.mock_registry)

        # Mock entities
        self.primary_entity = EntityDefinition(
            name="Reservation",
            schema="bookings",
            fields={
                "title": FieldDefinition(name="title", type_name="text"),
                "start_date": FieldDefinition(name="start_date", type_name="date"),
            },
        )

        self.related_entities = [
            EntityDefinition(
                name="Allocation",
                schema="bookings",
                fields={
                    "resource_id": FieldDefinition(name="resource_id", type_name="uuid"),
                    "quantity": FieldDefinition(name="quantity", type_name="integer"),
                },
            ),
            EntityDefinition(
                name="MachineItem",
                schema="inventory",
                fields={
                    "name": FieldDefinition(name="name", type_name="text"),
                    "status": FieldDefinition(name="status", type_name="text"),
                },
            ),
        ]

    def test_compile_multi_entity_action_basic_structure(self):
        """Test that multi-entity action compilation produces correct structure"""
        action = ActionDefinition(
            name="create_reservation",
            steps=[
                ActionStep(type="insert", entity="Reservation"),
                ActionStep(type="insert", entity="Allocation"),
                ActionStep(type="update", entity="MachineItem"),
            ],
        )

        result = self.orchestrator.compile_multi_entity_action(
            action, self.primary_entity, self.related_entities
        )

        # Should contain function definition
        assert "CREATE OR REPLACE FUNCTION bookings.create_reservation" in result
        assert "RETURNS app.mutation_result" in result
        assert "LANGUAGE plpgsql" in result

        # Should contain transaction management
        assert "BEGIN;" in result
        assert "COMMIT;" in result
        assert "EXCEPTION" in result
        assert "ROLLBACK;" in result

    def test_compile_multi_entity_action_with_steps(self):
        """Test compilation of various step types"""
        action = ActionDefinition(
            name="complex_reservation",
            steps=[
                ActionStep(type="validate", expression="start_date > now()"),
                ActionStep(type="insert", entity="Reservation"),
                ActionStep(
                    type="foreach",
                    foreach_expr="item in related_items",
                    then_steps=[ActionStep(type="update", entity="MachineItem")],
                ),
                ActionStep(type="call", function_name="send_notification"),
                ActionStep(type="notify", recipient="user", channel="email"),
            ],
        )

        result = self.orchestrator.compile_multi_entity_action(
            action, self.primary_entity, self.related_entities
        )

        # Should contain compiled steps
        assert "-- Mock compiled: validate" in result
        assert "-- Primary insert: Reservation" in result
        assert "-- Mock compiled: foreach" in result
        assert "-- Call: send_notification" in result
        assert "-- Notify: user via email" in result

    def test_find_entity_by_name(self):
        """Test entity lookup by name"""
        found = self.orchestrator._find_entity_by_name("Allocation", self.related_entities)
        assert found is not None
        assert found.name == "Allocation"

        not_found = self.orchestrator._find_entity_by_name("NonExistent", self.related_entities)
        assert not_found is None

    def test_build_function_parameters(self):
        """Test parameter building"""
        action = ActionDefinition(name="test_action", steps=[])
        params = self.orchestrator._build_function_parameters(action, self.primary_entity)

        expected = "auth_tenant_id UUID, input_data app.type_create_reservation_input, input_payload JSONB, auth_user_id UUID"
        assert params == expected

    def test_error_handling_in_compilation(self):
        """Test that compilation handles errors gracefully"""
        action = ActionDefinition(
            name="error_action",
            steps=[
                ActionStep(type="unknown_step_type")  # This should raise an error
            ],
        )

        with pytest.raises(ValueError, match="No compiler for step type"):
            self.orchestrator.compile_multi_entity_action(
                action, self.primary_entity, self.related_entities
            )
