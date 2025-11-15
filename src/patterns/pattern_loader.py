"""
Pattern loader for SpecQL action patterns.

This module provides functionality to load action patterns from the stdlib,
validate configurations, and expand patterns into action steps using Jinja2 templates.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader

from .pattern_models import PatternDefinition, ExpandedPattern


class PatternLoader:
    """Loads and expands action patterns from the library."""

    def __init__(self, stdlib_path: Optional[Path] = None):
        """Initialize the pattern loader.

        Args:
            stdlib_path: Path to the stdlib/actions directory. Defaults to stdlib/actions.
        """
        if stdlib_path is None:
            stdlib_path = Path(__file__).parent.parent.parent / "stdlib" / "actions"

        self.stdlib_path = stdlib_path
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(stdlib_path)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )

        # Add custom filters
        self.jinja_env.filters["schema_for"] = self._schema_for_entity
        self.jinja_env.filters["type_for"] = self._type_for_field
        self.jinja_env.filters["format_where"] = self._format_where_clause
        self.jinja_env.filters["format_where_with_item"] = self._format_where_with_item
        self.jinja_env.filters["trim_prefix"] = self._trim_prefix

        # Cache for loaded patterns
        self._pattern_cache: Dict[str, PatternDefinition] = {}

    def load_pattern(self, pattern_name: str) -> PatternDefinition:
        """Load a pattern definition from the library.

        Args:
            pattern_name: Name of the pattern (e.g., 'state_machine/transition')

        Returns:
            PatternDefinition instance

        Raises:
            FileNotFoundError: If pattern file doesn't exist
            ValueError: If pattern YAML is invalid
        """
        if pattern_name in self._pattern_cache:
            return self._pattern_cache[pattern_name]

        pattern_path = self.stdlib_path / f"{pattern_name}.yaml"

        if not pattern_path.exists():
            raise FileNotFoundError(
                f"Pattern '{pattern_name}' not found at {pattern_path}"
            )

        try:
            with open(pattern_path, "r") as f:
                data = yaml.safe_load(f)

            pattern = PatternDefinition.from_yaml(data)
            self._pattern_cache[pattern_name] = pattern
            return pattern

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in pattern '{pattern_name}': {e}")

    def validate_config(
        self, pattern: PatternDefinition, config: Dict[str, Any]
    ) -> List[str]:
        """Validate a configuration against a pattern.

        Args:
            pattern: The pattern definition
            config: Configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required parameters
        for param in pattern.parameters:
            if param.required and param.name not in config:
                errors.append(
                    f"Missing required parameter '{param.name}' for pattern '{pattern.name}'"
                )

        # Validate parameter types and values
        for param in pattern.parameters:
            if param.name in config:
                value = config[param.name]
                if not param.validate_value(value):
                    errors.append(
                        f"Parameter '{param.name}' has invalid value. "
                        f"Expected {param.type}, got {type(value).__name__}: {value}"
                    )

        return errors

    def expand_pattern(
        self,
        pattern_name: str,
        entity: Any,  # EntityDefinition - avoiding circular import
        config: Dict[str, Any],
    ) -> ExpandedPattern:
        """Expand a pattern template with configuration.

        Args:
            pattern: The pattern definition
            entity: The entity this pattern is being applied to
            config: Configuration values

        Returns:
            ExpandedPattern with the rendered action steps

        Raises:
            ValueError: If configuration is invalid
        """
        pattern = self._pattern_cache.get(pattern_name)
        if not pattern:
            pattern = self.load_pattern(pattern_name)
        if not pattern:
            raise ValueError(f"Pattern '{pattern_name}' not found")

        # Validate configuration
        errors = self.validate_config(pattern, config)
        if errors:
            raise ValueError(f"Invalid pattern configuration: {'; '.join(errors)}")

        # Prepare template context
        context = {
            "entity": entity,
            "config": config,
            **config,  # Make config values directly available
        }

        # Render template
        try:
            template = self.jinja_env.from_string(pattern.template)
            rendered = template.render(**context)

            # Parse rendered YAML back to steps
            steps_data = yaml.safe_load(rendered)
            steps = steps_data.get("steps", [])

            return ExpandedPattern(
                pattern_name=pattern.name, config=config, expanded_steps=steps
            )

        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse expanded pattern template: {e}")
        except Exception as e:
            raise ValueError(f"Failed to expand pattern template: {e}")

    def list_available_patterns(self) -> List[str]:
        """List all available patterns in the library.

        Returns:
            List of pattern names (e.g., ['state_machine/transition', ...])
        """
        patterns = []
        if self.stdlib_path.exists():
            for yaml_file in self.stdlib_path.rglob("*.yaml"):
                if yaml_file.is_file():
                    relative_path = yaml_file.relative_to(self.stdlib_path)
                    pattern_name = (
                        str(relative_path).replace(".yaml", "").replace("\\", "/")
                    )
                    patterns.append(pattern_name)
        return sorted(patterns)

    # Jinja2 custom filters

    def _schema_for_entity(self, entity_name: str) -> str:
        """Get schema name for an entity (placeholder - would need entity registry)."""
        # This is a simplified version - in practice you'd look up the entity
        # For now, assume tenant schema for most entities
        return "tenant"

    def _type_for_field(self, field_name: str) -> str:
        """Get PostgreSQL type for a field (placeholder)."""
        # This is a simplified version - in practice you'd look up field types
        type_map = {
            "id": "UUID",
            "name": "TEXT",
            "status": "TEXT",
            "created_at": "TIMESTAMPTZ",
            "updated_at": "TIMESTAMPTZ",
        }
        return type_map.get(field_name, "TEXT")

    def _format_where_clause(self, where_dict: Dict[str, Any]) -> str:
        """Format a where clause dictionary into SQL."""
        conditions = []
        for field, value in where_dict.items():
            if isinstance(value, str) and value.startswith("$"):
                # Template variable
                conditions.append(f"{field} = {value[1:]}")
            else:
                # Literal value
                conditions.append(f"{field} = {repr(value)}")
        return " AND ".join(conditions)

    def _format_where_with_item(self, where_dict: Dict[str, Any]) -> str:
        """Format a where clause that references v_item for batch operations."""
        conditions = []
        for field, value in where_dict.items():
            if isinstance(value, str) and value.startswith("$item."):
                # Reference to batch item
                item_field = value[6:]  # Remove '$item.'
                conditions.append(f"{field} = (v_item->>'{item_field}')")
            elif isinstance(value, str) and value.startswith("$"):
                # Other template variable
                conditions.append(f"{field} = {value[1:]}")
            else:
                # Literal value
                conditions.append(f"{field} = {repr(value)}")
        return " AND ".join(conditions)

    def _trim_prefix(self, value: str, prefix: str) -> str:
        """Remove a prefix from a string if it exists."""
        if value.startswith(prefix):
            return value[len(prefix) :]
        return value
