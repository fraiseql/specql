"""
Pattern library models for SpecQL action patterns.

This module defines the data structures used to represent action patterns,
their parameters, and configuration.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PatternParameter:
    """Represents a parameter in a pattern definition."""

    name: str
    type: str
    required: bool = False
    default: Any = None
    description: str = ""

    def validate_value(self, value: Any) -> bool:
        """Validate that a value matches this parameter's type."""
        if value is None:
            return not self.required

        # Basic type checking
        type_map = {
            "string": str,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected_type = type_map.get(self.type)
        if expected_type:
            return isinstance(value, expected_type)

        # Handle array<type> syntax
        if self.type.startswith("array<") and self.type.endswith(">"):
            if not isinstance(value, list):
                return False
            element_type = self.type[6:-1]  # Extract inner type
            return all(isinstance(item, type_map.get(element_type, object)) for item in value)

        # Handle enum syntax
        if self.type.startswith("enum[") and self.type.endswith("]"):
            allowed_values = self.type[5:-1].split(",")
            return value in [v.strip() for v in allowed_values]

        return True


@dataclass
class PatternDefinition:
    """Represents a complete action pattern definition."""

    name: str
    version: str
    description: str
    author: str
    parameters: List[PatternParameter]
    template: str
    examples: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> "PatternDefinition":
        """Create a PatternDefinition from YAML data."""
        parameters = []
        for param_data in data.get("parameters", []):
            parameters.append(
                PatternParameter(
                    name=param_data["name"],
                    type=param_data["type"],
                    required=param_data.get("required", False),
                    default=param_data.get("default"),
                    description=param_data.get("description", ""),
                )
            )

        return cls(
            name=data["pattern"],
            version=data["version"],
            description=data["description"],
            author=data.get("author", "SpecQL Team"),
            parameters=parameters,
            template=data["template"],
            examples=data.get("examples", []),
        )


@dataclass
class PatternConfig:
    """Configuration for a pattern instantiation."""

    pattern_name: str
    config: Dict[str, Any]

    def validate(self, pattern: PatternDefinition) -> List[str]:
        """Validate this config against a pattern definition."""
        errors = []

        # Check required parameters
        for param in pattern.parameters:
            if param.required and param.name not in self.config:
                errors.append(f"Missing required parameter '{param.name}'")

        # Validate parameter types
        for param in pattern.parameters:
            if param.name in self.config:
                value = self.config[param.name]
                if not param.validate_value(value):
                    errors.append(
                        f"Parameter '{param.name}' has invalid type. "
                        f"Expected {param.type}, got {type(value)}"
                    )

        return errors


@dataclass
class ExpandedPattern:
    """Result of expanding a pattern with configuration."""

    pattern_name: str
    config: Dict[str, Any]
    expanded_steps: List[Dict[str, Any]]

    def to_action_steps(self) -> List[Dict[str, Any]]:
        """Convert expanded steps to action step format."""
        return self.expanded_steps
