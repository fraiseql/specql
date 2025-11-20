"""
Unit tests for ActionValidator
"""

import pytest

from core.ast_models import ActionDefinition, ActionStep, EntityDefinition, FieldDefinition
from generators.actions.action_validator import ActionValidator, ValidationError


class TestActionValidator:
    """Test ActionValidator functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = ActionValidator()

        # Mock entities
        self.contact_entity = EntityDefinition(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text"),
                "first_name": FieldDefinition(name="first_name", type_name="text"),
                "status": FieldDefinition(name="status", type_name="text"),
            },
        )

        self.task_entity = EntityDefinition(
            name="Task",
            schema="projects",
            fields={
                "title": FieldDefinition(name="title", type_name="text"),
                "assignee_id": FieldDefinition(name="assignee_id", type_name="uuid"),
            },
        )

    def test_validate_valid_action(self):
        """Test validation of a valid action"""
        action = ActionDefinition(
            name="create_contact",
            steps=[
                ActionStep(type="validate", expression="email IS NOT NULL", error="email_required"),
                ActionStep(type="insert", entity="Contact", fields={"email": "input.email"}),
            ],
        )

        # Should not raise any exceptions
        self.validator.validate_action(action, self.contact_entity, [])

        report = self.validator.get_validation_report()
        assert report["valid"] is True
        assert len(report["errors"]) == 0

    def test_validate_invalid_action_name(self):
        """Test validation of action with invalid name"""
        action = ActionDefinition(
            name="invalid-name!", steps=[ActionStep(type="validate", expression="true")]
        )

        with pytest.raises(ValidationError, match="contains invalid characters"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_validate_empty_action(self):
        """Test validation of action with no steps"""
        action = ActionDefinition(name="empty_action", steps=[])

        with pytest.raises(ValidationError, match="must have at least one step"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_validate_unknown_step_type(self):
        """Test validation of unknown step type"""
        action = ActionDefinition(name="test_action", steps=[ActionStep(type="unknown_step")])

        with pytest.raises(ValidationError, match="Unknown step type"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_validate_invalid_entity_reference(self):
        """Test validation of step referencing unknown entity"""
        action = ActionDefinition(
            name="test_action", steps=[ActionStep(type="insert", entity="UnknownEntity")]
        )

        with pytest.raises(ValidationError, match="unknown entity: UnknownEntity"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_validate_invalid_field_reference(self):
        """Test validation of step referencing unknown field"""
        action = ActionDefinition(
            name="test_action",
            steps=[ActionStep(type="insert", entity="Contact", fields={"unknown_field": "value"})],
        )

        with pytest.raises(ValidationError, match="unknown field 'unknown_field'"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_validate_missing_validation_error(self):
        """Test warning for validate step without custom error"""
        action = ActionDefinition(
            name="test_action", steps=[ActionStep(type="validate", expression="email IS NOT NULL")]
        )

        self.validator.validate_action(action, self.contact_entity, [])

        report = self.validator.get_validation_report()
        assert len(report["warnings"]) == 1
        assert "custom error message" in report["warnings"][0]

    def test_validate_if_step_requirements(self):
        """Test validation of if step requirements"""
        # Test missing condition
        action = ActionDefinition(
            name="test_action",
            steps=[
                ActionStep(type="if", then_steps=[ActionStep(type="validate", expression="true")])
            ],
        )

        with pytest.raises(ValidationError, match="must have a condition"):
            self.validator.validate_action(action, self.contact_entity, [])

        # Test missing then_steps
        action = ActionDefinition(
            name="test_action", steps=[ActionStep(type="if", condition="true")]
        )

        with pytest.raises(ValidationError, match="must have then_steps"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_validate_call_step_requirements(self):
        """Test validation of call step requirements"""
        action = ActionDefinition(
            name="test_action",
            steps=[ActionStep(type="call")],  # Missing function_name
        )

        with pytest.raises(ValidationError, match="must have a function_name"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_validate_notify_step_requirements(self):
        """Test validation of notify step requirements"""
        # Test missing recipient
        action = ActionDefinition(
            name="test_action", steps=[ActionStep(type="notify", channel="email")]
        )

        with pytest.raises(ValidationError, match="must have a recipient"):
            self.validator.validate_action(action, self.contact_entity, [])

        # Test missing channel
        action = ActionDefinition(
            name="test_action", steps=[ActionStep(type="notify", recipient="user@example.com")]
        )

        with pytest.raises(ValidationError, match="must have a channel"):
            self.validator.validate_action(action, self.contact_entity, [])

        # Test invalid channel
        action = ActionDefinition(
            name="test_action",
            steps=[ActionStep(type="notify", recipient="user@example.com", channel="invalid")],
        )

        with pytest.raises(ValidationError, match="Invalid notification channel"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_validate_foreach_step_requirements(self):
        """Test validation of foreach step requirements"""
        # Test missing foreach expression
        action = ActionDefinition(
            name="test_action",
            steps=[
                ActionStep(
                    type="foreach", then_steps=[ActionStep(type="validate", expression="true")]
                )
            ],
        )

        with pytest.raises(ValidationError, match="must have foreach_expr or iterator_var"):
            self.validator.validate_action(action, self.contact_entity, [])

        # Test missing then_steps
        action = ActionDefinition(
            name="test_action",
            steps=[ActionStep(type="foreach", foreach_expr="item in collection")],
        )

        with pytest.raises(ValidationError, match="must have then_steps"):
            self.validator.validate_action(action, self.contact_entity, [])

    def test_action_coherence_warnings(self):
        """Test warnings for action coherence issues"""
        action = ActionDefinition(
            name="test_action",
            steps=[
                ActionStep(type="update", entity="Contact", fields={"status": "updated"}),
                ActionStep(type="update", entity="Contact", fields={"email": "updated"}),
            ],
        )

        self.validator.validate_action(action, self.contact_entity, [])

        report = self.validator.get_validation_report()
        assert len(report["warnings"]) == 2
        assert "no prior validation" in report["warnings"][0]
        assert "no prior validation" in report["warnings"][1]
