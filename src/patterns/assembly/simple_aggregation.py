"""Simple aggregation pattern for basic parent-child relationships."""

import re
from typing import Any

from jinja2 import Template


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    # Insert underscore between lowercase and uppercase letters
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore between letters and digits, and between letters and uppercase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def generate_simple_aggregation(config: dict[str, Any]) -> str:
    """Generate simple subquery aggregation SQL for parent-child relationships.

    This pattern creates views that aggregate child entities into JSONB arrays
    using correlated subqueries. It's simpler than the tree_builder pattern
    and suitable for 1-level nesting.

    Args:
        config: Pattern configuration with parent/child entity definitions

    Returns:
        Generated SQL string with CREATE OR REPLACE VIEW statement

    Raises:
        ValueError: If configuration is invalid

    Example:
        >>> config = {
        ...     "name": "v_contract_with_items",
        ...     "config": {
        ...         "parent_entity": "Contract",
        ...         "child_entity": "ContractItem",
        ...         "child_array_field": "items",
        ...         "child_fields": [...]
        ...     }
        ... }
        >>> sql = generate_simple_aggregation(config)
        >>> assert "CREATE OR REPLACE VIEW" in sql
    """
    _validate_config(config)

    # Preprocess config with defaults
    processed_config = _preprocess_config(config)

    template = _get_template()
    return template.render(**processed_config)


def _preprocess_config(config: dict[str, Any]) -> dict[str, Any]:
    """Preprocess configuration with computed defaults."""
    pattern_config = config["config"].copy()

    # Set default table names
    if "parent_entity_table" not in pattern_config:
        pattern_config["parent_entity_table"] = (
            f"tb_{_camel_to_snake(pattern_config['parent_entity'])}"
        )

    if "child_entity_table" not in pattern_config:
        pattern_config["child_entity_table"] = (
            f"tb_{_camel_to_snake(pattern_config['child_entity'])}"
        )

    # Set default key names
    if "parent_pk" not in pattern_config:
        pattern_config["parent_pk"] = f"pk_{pattern_config['parent_entity'].lower()}"

    if "parent_fk" not in pattern_config:
        pattern_config["parent_fk"] = f"pk_{pattern_config['parent_entity'].lower()}"

    return {**config, "config": pattern_config}


def _validate_config(config: dict[str, Any]) -> None:
    """Validate simple aggregation configuration.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if "config" not in config:
        raise ValueError("Missing 'config' section in simple aggregation pattern")

    pattern_config = config["config"]

    required_fields = ["parent_entity", "child_entity", "child_array_field", "child_fields"]
    for field in required_fields:
        if field not in pattern_config:
            raise ValueError(f"{field} is required for simple aggregation pattern")

    if not isinstance(pattern_config["child_fields"], list):
        raise ValueError("child_fields must be a list")

    if len(pattern_config["child_fields"]) == 0:
        raise ValueError("child_fields cannot be empty")

    # Validate child_fields structure
    for field in pattern_config["child_fields"]:
        if not isinstance(field, dict) or "name" not in field or "expression" not in field:
            raise ValueError("Each child field must have 'name' and 'expression' keys")


def _get_template() -> Template:
    """Get the Jinja2 template for simple aggregation SQL generation."""
    template_str = """
-- @fraiseql:view
-- @fraiseql:description Simple aggregation of {{ config.child_entity }} into {{ config.parent_entity }}
CREATE OR REPLACE VIEW {{ config.schema | default('tenant') }}.{{ name }} AS
SELECT
  parent.*,
  (
    SELECT jsonb_agg(jsonb_build_object(
{%- for field in config.child_fields %}
      '{{ field.name }}', {{ field.expression }}{% if not loop.last %},{% endif %}
{%- endfor %}
    ))
    FROM {{ config.child_entity_table }} child
    WHERE child.{{ config.parent_fk }} = parent.{{ config.parent_pk }}
      AND child.deleted_at IS NULL
{%- if config.order_by %}
    ORDER BY {{ config.order_by }}
{%- endif %}
  ) AS {{ config.child_array_field }}
FROM {{ config.parent_entity_table }} parent
WHERE parent.deleted_at IS NULL;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_{{ name }}_{{ config.child_array_field }}
    ON {{ config.schema | default('tenant') }}.{{ name }} USING GIN ({{ config.child_array_field }})
    WHERE {{ config.child_array_field }} IS NOT NULL;
"""
    return Template(template_str)
