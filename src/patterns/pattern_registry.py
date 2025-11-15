"""
Pattern Registry for Query Patterns.

This module provides a registry for discovering and managing query patterns
from the stdlib/queries directory.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml
from jinja2 import Template


@dataclass
class Pattern:
    """A query pattern definition."""

    name: str
    description: str
    parameters: dict[str, Any]
    template: Template
    custom_generate: Callable[[dict[str, Any]], str] | None = None

    def generate(self, entity: dict[str, Any], config: dict[str, Any]) -> str:
        """Generate SQL for this pattern."""
        # If there's a custom generate function, use it
        if self.custom_generate:
            # Prepare context for custom generate functions
            context = self._prepare_context(entity, config)
            config_with_context = dict(config)
            config_with_context["config"] = dict(config.get("config", config))
            config_with_context["config"]["is_multi_tenant"] = context["is_multi_tenant"]
            config_with_context["config"]["tenant_filter"] = context["tenant_filter"]
            return self.custom_generate(config_with_context)

        # Prepare context for template rendering
        context = self._prepare_context(entity, config)

        # Render template with context
        return self.template.render(**context)

    def _prepare_context(self, entity: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Prepare template context from entity and config."""
        # Handle nested config structure for query patterns
        pattern_config = config.get("config", config)

        context = dict(pattern_config)  # Start with pattern config
        context.update(entity)  # Add entity data

        # Add view name
        context["view_name"] = f"v_{config['name']}"
        context["name"] = config["name"]  # Override with the actual view name

        # Add multi-tenant detection and filtering
        context["is_multi_tenant"] = self._is_entity_multi_tenant(entity)
        context["tenant_filter"] = self._build_tenant_filter()

        # Add performance configuration
        performance_config = config.get("performance", {})
        context["performance"] = {
            "materialized": performance_config.get("materialized", False),
            "indexes": performance_config.get("indexes", []),
            "refresh_strategy": performance_config.get("refresh_strategy", "manual"),
        }

        # Add helper functions
        context["get_previous_alias"] = self._get_previous_alias
        context["get_previous_pk"] = self._get_previous_pk
        context["get_last_junction_alias"] = self._get_last_junction_alias
        context["get_last_junction_right_key"] = self._get_last_junction_right_key

        return context

    def _get_previous_alias(self, index: int) -> str:
        """Get alias for the table at the given index in the join chain."""
        if index == 0:
            return "src"  # Source entity alias
        else:
            return f"j{index}"  # Junction table alias

    def _get_previous_pk(self, index: int) -> str:
        """Get primary key field for the table at the given index."""
        # This is a simplified implementation - in practice this would
        # need to be more sophisticated based on the actual entity/junction config
        if index == 0:
            return "pk_source"  # Would be entity.pk_field
        else:
            return f"pk_j{index}"  # Would be junction.left_key or similar

    def _get_last_junction_alias(self) -> str:
        """Get alias for the last junction table."""
        # Simplified - would need actual junction table count
        return "j1"

    def _get_last_junction_right_key(self) -> str:
        """Get right key for the last junction table."""
        # Simplified - would need actual junction config
        return "right_key"

    def _is_entity_multi_tenant(self, entity: dict[str, Any]) -> bool:
        """Check if entity is multi-tenant."""
        # Check entity-level flag first (support both multi_tenant and is_multi_tenant keys)
        if "is_multi_tenant" in entity:
            return entity["is_multi_tenant"]
        if "multi_tenant" in entity:
            return entity["multi_tenant"]

        # Check schema-level multi-tenancy only if no explicit flag
        schema = entity.get("schema", "")
        # Common multi-tenant schemas in SpecQL
        multi_tenant_schemas = {"crm", "management"}  # Removed "tenant" to avoid false positives
        return schema in multi_tenant_schemas

    def _build_tenant_filter(self) -> str:
        """Build tenant filter clause for WHERE conditions."""
        return "CURRENT_SETTING('app.current_tenant_id')::uuid"


class PatternRegistry:
    """
    Registry for query patterns.

    Discovers patterns from stdlib/queries/ and provides access by name.
    """

    def __init__(self) -> None:
        self.patterns: dict[str, Pattern] = {}
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load patterns from stdlib/queries/ directory."""
        queries_dir = Path(__file__).parent.parent.parent / "stdlib" / "queries"

        if not queries_dir.exists():
            # Fallback to mock patterns if stdlib/queries doesn't exist
            self._load_mock_patterns()
            return

        # Discover all pattern directories
        for pattern_dir in queries_dir.rglob("*"):
            if pattern_dir.is_dir():
                self._load_pattern_from_dir(pattern_dir)

    def _load_pattern_from_dir(self, pattern_dir: Path) -> None:
        """Load all patterns from a pattern directory."""
        # Look for all YAML files in the directory
        for yaml_file in pattern_dir.glob("*.yaml"):
            pattern_name = yaml_file.stem  # filename without extension
            template_file = yaml_file.with_suffix(".sql.jinja2")
            yaml_file.with_suffix(".py")

            if not template_file.exists():
                continue

            # Load YAML config
            with open(yaml_file) as f:
                config = yaml.safe_load(f)

            # Load Jinja2 template
            with open(template_file) as f:
                template_content = f.read()
                template = Template(template_content)

            # Create pattern
            full_pattern_name = f"{pattern_dir.name}/{pattern_name}"

            # Check for custom generate function in src/patterns/
            custom_generate = None
            src_python_file = Path(__file__).parent / pattern_dir.name / f"{pattern_name}.py"
            if src_python_file.exists():
                # Import the module and get the generate function
                module_name = f"src.patterns.{pattern_dir.name}.{pattern_name}"
                try:
                    import importlib

                    module = importlib.import_module(module_name)
                    custom_generate = getattr(module, f"generate_{pattern_name}", None)
                except ImportError:
                    pass  # No custom generate function
            pattern = Pattern(
                name=full_pattern_name,
                description=config.get("description", ""),
                parameters=config.get("parameters", {}),
                template=template,
                custom_generate=custom_generate,
            )

            self.patterns[full_pattern_name] = pattern

    def _load_mock_patterns(self) -> None:
        """Load mock patterns for development."""
        # Keep existing mock pattern
        self.patterns["aggregation/hierarchical_count"] = Pattern(
            name="aggregation/hierarchical_count",
            description="Count entities in hierarchical relationships",
            parameters={
                "counted_entity": {"type": "entity_reference", "required": True},
                "grouped_by_entity": {"type": "entity_reference", "required": True},
                "metrics": {"type": "array", "required": True},
            },
            template=Template(
                "CREATE OR REPLACE VIEW tenant.{{ name }} AS SELECT 1 as dummy_column;"
            ),
        )

    def get_pattern(self, pattern_name: str) -> Pattern:
        """Get a pattern by name."""
        if pattern_name not in self.patterns:
            raise ValueError(f"Pattern '{pattern_name}' not found")
        return self.patterns[pattern_name]

    def discover_patterns(self, base_path: Path) -> dict[str, Pattern]:
        """Discover all patterns in the given base path."""
        # Mock implementation
        return self.patterns
