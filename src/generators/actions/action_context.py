"""
Action Context for compilation

Provides compilation context from SpecQL AST to guide PL/pgSQL generation.
"""

from dataclasses import dataclass
from typing import Any

from src.core.ast_models import ActionDefinition, ActionStep


@dataclass
class ActionContext:
    """Compilation context for action generation"""

    function_name: str
    entity_schema: str
    entity_name: str
    entity: Any  # Full entity definition for table view checks
    steps: list[ActionStep]
    impact: dict[str, Any] | None  # Impact metadata dict
    has_impact_metadata: bool

    @classmethod
    def from_ast(cls, action_ast: ActionDefinition, entity_ast: Any) -> "ActionContext":
        """Create compilation context from action and entity AST"""
        # Validate inputs
        if not action_ast.name:
            raise ValueError("Action name cannot be empty")
        if not entity_ast.schema:
            raise ValueError("Entity schema cannot be empty")
        if not entity_ast.name:
            raise ValueError("Entity name cannot be empty")

        return cls(
            function_name=f"{entity_ast.schema}.{action_ast.name}",
            entity_schema=entity_ast.schema,
            entity_name=entity_ast.name,
            entity=entity_ast,
            steps=action_ast.steps,
            impact=action_ast.impact,
            has_impact_metadata=action_ast.impact is not None,
        )

    def get_step_types(self) -> list[str]:
        """Get list of step types for this action"""
        return [step.type for step in self.steps]

    def has_step_type(self, step_type: str) -> bool:
        """Check if action contains a specific step type"""
        return any(step.type == step_type for step in self.steps)

    def requires_entity_id(self) -> bool:
        """Check if action operates on existing entity (needs ID parameter)"""
        return any(step.type in ("update", "delete", "validate") for step in self.steps)

    def get_primary_entity_impact(self) -> dict[str, Any] | None:
        """Get primary entity impact from impact metadata"""
        if not self.impact:
            return None
        return self.impact.get("primary")

    def get_side_effects(self) -> list[dict[str, Any]]:
        """Get side effects from impact metadata"""
        if not self.impact:
            return []
        return self.impact.get("side_effects", [])
