"""
Action Validator

Comprehensive validation for SpecQL actions before compilation.
Validates action structure, entity references, field access, and business rules.
"""

from typing import Any

from src.core.ast_models import ActionDefinition, ActionStep, EntityDefinition


class ValidationError(Exception):
    """Custom exception for action validation errors"""

    def __init__(self, message: str, step_index: int | None = None, field: str | None = None):
        self.message = message
        self.step_index = step_index
        self.field = field
        super().__init__(f"{message}" + (f" (step {step_index})" if step_index is not None else ""))


class ActionValidator:
    """Validates SpecQL actions for correctness before compilation"""

    def __init__(self):
        self.errors: list[ValidationError] = []
        self.warnings: list[str] = []

    def validate_action(
        self,
        action: ActionDefinition,
        primary_entity: EntityDefinition,
        related_entities: list[EntityDefinition],
    ) -> None:
        """
        Validate a complete action definition

        Args:
            action: Action to validate
            primary_entity: Primary entity for the action
            related_entities: Related entities that may be involved

        Raises:
            ValidationError: If action is invalid
        """
        self.errors = []
        self.warnings = []

        # Basic action structure validation
        self._validate_action_structure(action)

        # Entity and field reference validation
        all_entities = [primary_entity] + related_entities
        entity_map = {e.name: e for e in all_entities}

        # Validate each step
        for i, step in enumerate(action.steps):
            try:
                self._validate_step(step, i, entity_map, primary_entity)
            except ValidationError as e:
                if e.step_index is None:
                    e.step_index = i
                self.errors.append(e)

        # Cross-step validation
        self._validate_action_coherence(action, primary_entity)

        # Raise first error if any
        if self.errors:
            raise self.errors[0]

    def _validate_action_structure(self, action: ActionDefinition) -> None:
        """Validate basic action structure"""
        if not action.name:
            raise ValidationError("Action must have a name")

        if not action.name.replace("_", "").isalnum():
            raise ValidationError(f"Action name '{action.name}' contains invalid characters")

        if not action.steps:
            raise ValidationError("Action must have at least one step")

    def _validate_step(
        self,
        step: ActionStep,
        step_index: int,
        entity_map: dict[str, EntityDefinition],
        primary_entity: EntityDefinition,
    ) -> None:
        """Validate a single action step"""

        # Validate step type
        valid_step_types = {
            "validate",
            "if",
            "insert",
            "update",
            "delete",
            "call",
            "notify",
            "foreach",
        }

        if step.type not in valid_step_types:
            raise ValidationError(f"Unknown step type: {step.type}", step_index)

        # Type-specific validation
        if step.type == "validate":
            self._validate_validate_step(step, step_index)
        elif step.type == "if":
            self._validate_if_step(step, step_index, entity_map)
        elif step.type == "insert":
            self._validate_insert_step(step, step_index, entity_map)
        elif step.type == "update":
            self._validate_update_step(step, step_index, entity_map)
        elif step.type == "delete":
            self._validate_delete_step(step, step_index, entity_map)
        elif step.type == "call":
            self._validate_call_step(step, step_index)
        elif step.type == "notify":
            self._validate_notify_step(step, step_index)
        elif step.type == "foreach":
            self._validate_foreach_step(step, step_index, entity_map)

    def _validate_validate_step(self, step: ActionStep, step_index: int) -> None:
        """Validate validate step"""
        if not step.expression:
            raise ValidationError("Validate step must have an expression", step_index)

        if not step.error:
            self.warnings.append(f"Validate step at index {step_index} has no custom error message")

    def _validate_if_step(
        self, step: ActionStep, step_index: int, entity_map: dict[str, EntityDefinition]
    ) -> None:
        """Validate if step"""
        if not step.condition:
            raise ValidationError("If step must have a condition", step_index)

        if not step.then_steps:
            raise ValidationError("If step must have then_steps", step_index)

        # Recursively validate nested steps
        for i, nested_step in enumerate(step.then_steps):
            self._validate_step(nested_step, step_index, entity_map, None)  # type: ignore

        if step.else_steps:
            for i, nested_step in enumerate(step.else_steps):
                self._validate_step(nested_step, step_index, entity_map, None)  # type: ignore

    def _validate_insert_step(
        self, step: ActionStep, step_index: int, entity_map: dict[str, EntityDefinition]
    ) -> None:
        """Validate insert step"""
        if not step.entity:
            raise ValidationError("Insert step must specify target entity", step_index)

        if step.entity not in entity_map:
            raise ValidationError(
                f"Insert step references unknown entity: {step.entity}", step_index
            )

        entity = entity_map[step.entity]

        # Check if required fields are provided
        if step.fields:
            self._validate_field_references(list(step.fields.keys()), entity, step_index, "insert")

    def _validate_update_step(
        self, step: ActionStep, step_index: int, entity_map: dict[str, EntityDefinition]
    ) -> None:
        """Validate update step"""
        if step.entity and step.entity not in entity_map:
            raise ValidationError(
                f"Update step references unknown entity: {step.entity}", step_index
            )

        if step.fields:
            # If entity is specified, validate against that entity
            if step.entity:
                entity = entity_map[step.entity]
                self._validate_field_references(
                    list(step.fields.keys()), entity, step_index, "update"
                )
            else:
                # If no entity specified, assume primary entity context
                pass  # Would need primary entity passed in

    def _validate_delete_step(
        self, step: ActionStep, step_index: int, entity_map: dict[str, EntityDefinition]
    ) -> None:
        """Validate delete step"""
        if not step.entity:
            raise ValidationError("Delete step must specify target entity", step_index)

        if step.entity not in entity_map:
            raise ValidationError(
                f"Delete step references unknown entity: {step.entity}", step_index
            )

    def _validate_call_step(self, step: ActionStep, step_index: int) -> None:
        """Validate call step"""
        if not step.function_name:
            raise ValidationError("Call step must have a function_name", step_index)

        # Basic function name validation
        if not step.function_name.replace("_", "").replace(".", "").isalnum():
            raise ValidationError(f"Invalid function name: {step.function_name}", step_index)

    def _validate_notify_step(self, step: ActionStep, step_index: int) -> None:
        """Validate notify step"""
        if not step.recipient:
            raise ValidationError("Notify step must have a recipient", step_index)

        if not step.channel:
            raise ValidationError("Notify step must have a channel", step_index)

        valid_channels = {"email", "sms", "push", "webhook"}
        if step.channel not in valid_channels:
            raise ValidationError(
                f"Invalid notification channel: {step.channel}. Must be one of {valid_channels}",
                step_index,
            )

    def _validate_foreach_step(
        self, step: ActionStep, step_index: int, entity_map: dict[str, EntityDefinition]
    ) -> None:
        """Validate foreach step"""
        if not step.foreach_expr and not (step.iterator_var and step.collection):
            raise ValidationError(
                "Foreach step must have foreach_expr or iterator_var+collection", step_index
            )

        if not step.then_steps:
            raise ValidationError("Foreach step must have then_steps", step_index)

        # Recursively validate nested steps
        for i, nested_step in enumerate(step.then_steps):
            self._validate_step(nested_step, step_index, entity_map, None)  # type: ignore

    def _validate_field_references(
        self, field_names: list[str], entity: EntityDefinition, step_index: int, operation: str
    ) -> None:
        """Validate that referenced fields exist on the entity"""
        entity_fields = set(entity.fields.keys())

        for field_name in field_names:
            if field_name not in entity_fields:
                raise ValidationError(
                    f"{operation.capitalize()} step references unknown field '{field_name}' on entity '{entity.name}'",
                    step_index,
                )

    def _validate_action_coherence(
        self, action: ActionDefinition, primary_entity: EntityDefinition
    ) -> None:
        """Validate action coherence across all steps"""
        # Check for multiple primary entity inserts (should be rare)
        insert_steps = [
            step
            for step in action.steps
            if step.type == "insert" and step.entity == primary_entity.name
        ]
        if len(insert_steps) > 1:
            self.warnings.append(
                f"Action '{action.name}' has multiple inserts for primary entity '{primary_entity.name}'"
            )

        # Check for updates without prior validation
        update_steps = [i for i, step in enumerate(action.steps) if step.type == "update"]
        validate_steps = [i for i, step in enumerate(action.steps) if step.type == "validate"]

        for update_idx in update_steps:
            # Check if there's validation before this update
            prior_validations = [v_idx for v_idx in validate_steps if v_idx < update_idx]
            if not prior_validations:
                self.warnings.append(f"Update step at index {update_idx} has no prior validation")

    def get_validation_report(self) -> dict[str, Any]:
        """Get a complete validation report"""
        return {
            "valid": len(self.errors) == 0,
            "errors": [{"message": e.message, "step_index": e.step_index} for e in self.errors],
            "warnings": self.warnings,
        }
