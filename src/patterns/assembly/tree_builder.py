"""Assembly pattern for building deeply nested hierarchies with multi-CTE composition."""

from typing import Any

from jinja2 import Template


def build_cte_hierarchy(config: dict[str, Any]) -> str:
    """Build the CTE hierarchy section of the SQL.

    Args:
        config: Pattern configuration

    Returns:
        SQL string for CTE definitions
    """
    ctes = []

    # Root level CTEs
    for level in config["hierarchy"]:
        cte = _build_level_cte(level)
        ctes.append(cte)

    # Aggregation CTEs for child levels
    for level in config["hierarchy"][0]["child_levels"]:
        cte = _build_aggregation_cte(level, config)
        ctes.append(cte)

    return ",\n".join(ctes)


def _build_level_cte(level: dict[str, Any]) -> str:
    """Build a basic level CTE."""
    fields_sql = []
    for field in level.get("fields", []):
        fields_sql.append(f"      {field['expression']} AS {field['name']}")

    fields_str = ",\n".join(fields_sql) if fields_sql else "      1"  # Dummy if no fields

    return f"""  -- CTE: {level["level"]}
  {level["level"]} AS (
    SELECT
{fields_str}
    FROM {level["source"]}
  )"""


def _build_aggregation_cte(level: dict[str, Any], config: dict[str, Any]) -> str:
    """Build an aggregation CTE with nested child levels."""
    # Build nested CTEs first
    nested_ctes = []
    for child_level in level.get("child_levels", []):
        nested_cte = _build_nested_aggregation_cte(child_level)
        nested_ctes.append(nested_cte)

    # Build main aggregation
    group_by = ", ".join(level["group_by"])
    fields_json = _build_json_fields(level["fields"])

    # Add nested child aggregations to JSON
    for child_level in level.get("child_levels", []):
        child_agg = f",\n        '{child_level['array_field']}', COALESCE({child_level['level']}_aggregated.{child_level['array_field']}, '[]'::jsonb)"
        fields_json += child_agg

    joins = []
    for child_level in level.get("child_levels", []):
        join_condition = f"{child_level['level']}_aggregated.{child_level['group_by'][0]} = {level['level']}.{level['group_by'][0]}"
        joins.append(f"    LEFT JOIN {child_level['level']}_aggregated\n      ON {join_condition}")

    joins_str = "\n".join(joins)

    cte = f"""  -- CTE for {level["level"]} aggregation
  {level["level"]}_aggregated AS (
    SELECT
      {group_by},
      jsonb_agg(DISTINCT jsonb_build_object(
{fields_json}
      )) AS {level["array_field"]}
    FROM {level["level"]}
{joins_str}
    GROUP BY {group_by}
  )"""

    # Add nested CTEs
    if nested_ctes:
        cte = ",\n".join(nested_ctes) + ",\n" + cte

    return cte


def _build_nested_aggregation_cte(level: dict[str, Any]) -> str:
    """Build a nested aggregation CTE."""
    group_by = ", ".join(level["group_by"])
    fields_json = _build_json_fields(level["fields"])

    return f"""  -- CTE for {level["level"]} aggregation (nested)
  {level["level"]}_aggregated AS (
    SELECT
      {group_by},
      jsonb_agg(DISTINCT jsonb_build_object(
{fields_json}
      )) AS {level["array_field"]}
    FROM {level["level"]}
    GROUP BY {group_by}
  )"""


def _build_json_fields(fields: list[dict[str, Any]]) -> str:
    """Build JSON field definitions for jsonb_build_object."""
    field_parts = []
    for field in fields:
        field_parts.append(f"        '{field['name']}', {field['name']}")

    return ",\n".join(field_parts)


def generate_tree_builder(config: dict[str, Any]) -> str:
    """Generate complex tree assembly SQL with multiple CTEs for deeply nested hierarchies.

    This pattern creates views that aggregate related data into nested JSONB structures
    using multiple Common Table Expressions (CTEs) to handle complex parent-child
    relationships efficiently.

    Args:
        config: Pattern configuration with hierarchy definition
            - root_entity: The root entity name
            - hierarchy: List of hierarchy levels with child relationships
            - max_depth: Maximum nesting depth (default: 4)
            - schema: Target schema (default: 'tenant')

    Returns:
        Generated SQL string with CREATE OR REPLACE VIEW statement

    Raises:
        ValueError: If configuration is invalid

    Example:
        >>> config = {
        ...     "name": "v_contract_price_tree",
        ...     "config": {
        ...         "root_entity": "Contract",
        ...         "hierarchy": [{
        ...             "level": "contract_base",
        ...             "source": "tb_contract",
        ...             "group_by": ["pk_contract"],
        ...             "child_levels": [...]
        ...         }]
        ...     }
        ... }
        >>> sql = generate_tree_builder(config)
        >>> assert "CREATE OR REPLACE VIEW" in sql
    """
    _validate_config(config)

    template = _get_template()
    return template.render(**config)


def _validate_config(config: dict[str, Any]) -> None:
    """Validate tree builder configuration."""
    if "config" not in config:
        raise ValueError("Missing 'config' section in tree builder pattern")

    pattern_config = config["config"]

    if "root_entity" not in pattern_config:
        raise ValueError("root_entity is required for tree builder pattern")

    if "hierarchy" not in pattern_config:
        raise ValueError("hierarchy is required for tree builder pattern")

    if not isinstance(pattern_config["hierarchy"], list):
        raise ValueError("hierarchy must be a list")

    if len(pattern_config["hierarchy"]) == 0:
        raise ValueError("hierarchy cannot be empty")

    # Validate hierarchy structure
    for level in pattern_config["hierarchy"]:
        if "level" not in level:
            raise ValueError("Each hierarchy level must have a 'level' name")
        if "source" not in level:
            raise ValueError("Each hierarchy level must have a 'source' table/view")
        if "group_by" not in level:
            raise ValueError("Each hierarchy level must have 'group_by' keys")


def _get_template() -> Template:
    """Get the Jinja2 template for tree builder SQL generation."""
    template_str = """
-- @fraiseql:view
-- @fraiseql:description Complex tree assembly for {{ config.root_entity }}
CREATE OR REPLACE VIEW {{ config.schema | default('tenant') }}.{{ name }} AS
WITH
{%- for level in config.hierarchy %}
  -- CTE {{ loop.index }}: {{ level.level }}
  {{ level.level }} AS (
    SELECT
    {%- for field in level.fields %}
      {{ field.expression }} AS {{ field.name }}{% if not loop.last %},{% endif %}
    {%- endfor %}
    FROM {{ level.source }}
    {% if level.where %}
    WHERE {{ level.where }}
    {% endif %}
  ){% if not loop.last %},{% endif %}

{%- endfor %}

{%- for level in config.hierarchy[0].child_levels %}
  -- CTE for {{ level.level }} aggregation
  {{ level.level }}_aggregated AS (
    SELECT
      {{ level.group_by|join(', ') }},
      jsonb_agg(DISTINCT jsonb_build_object(
        {%- for field in level.fields %}
        '{{ field.name }}', {{ field.name }}{% if not loop.last %},{% endif %}
        {%- endfor %}
        {%- if level.child_levels %}
        {%- for child_level in level.child_levels %}
        , '{{ child_level.array_field }}', COALESCE({{ child_level.level }}_aggregated.{{ child_level.array_field }}, '[]'::jsonb)
        {%- endfor %}
        {%- endif %}
      )) AS {{ level.array_field }}
    FROM {{ level.level }}
    {%- for child_level in level.child_levels %}
    LEFT JOIN {{ child_level.level }}_aggregated
      ON {{ child_level.level }}_aggregated.{{ child_level.group_by[0] }} = {{ level.level }}.{{ level.group_by[0] }}
    {%- endfor %}
    GROUP BY {{ level.group_by|join(', ') }}
  ),

{%- for child_level in level.child_levels %}
  -- CTE for {{ child_level.level }} aggregation (nested)
  {{ child_level.level }}_aggregated AS (
    SELECT
      {{ child_level.group_by|join(', ') }},
      jsonb_agg(DISTINCT jsonb_build_object(
        {%- for field in child_level.fields %}
        '{{ field.name }}', {{ field.name }}{% if not loop.last %},{% endif %}
        {%- endfor %}
      )) AS {{ child_level.array_field }}
    FROM {{ child_level.level }}
    GROUP BY {{ child_level.group_by|join(', ') }}
  ){% if not loop.last %},{% endif %}

{%- endfor %}
{%- endfor %}

-- Final assembly
SELECT
  root.{{ config.hierarchy[0].group_by[0] }},
  jsonb_build_object(
{%- for level in config.hierarchy[0].child_levels %}
    '{{ level.array_field }}', COALESCE({{ level.level }}_aggregated.{{ level.array_field }}, '[]'::jsonb){% if not loop.last %},{% endif %}
{%- endfor %}
  ) AS data
FROM {{ config.hierarchy[0].level }} root
{%- for level in config.hierarchy[0].child_levels %}
LEFT JOIN {{ level.level }}_aggregated
  ON {{ level.level }}_aggregated.{{ level.group_by[0] }} = root.{{ config.hierarchy[0].group_by[0] }}
{%- endfor %};

-- Performance indexes
{%- for level in config.hierarchy[0].child_levels %}
CREATE INDEX IF NOT EXISTS idx_{{ name }}_{{ level.level }}
    ON {{ config.schema | default('tenant') }}.{{ name }} USING GIN ((data->'{{ level.array_field }}'));
{%- endfor %}
"""
    return Template(template_str)


def _render_join_condition(level: dict[str, Any], root_level: dict[str, Any]) -> str:
    """Render JOIN condition for child level to root level."""
    # Default join condition based on group_by keys
    root_key = root_level["group_by"][0]
    child_key = level["group_by"][0]

    # Assume foreign key relationship
    return f"{{ level.level }}.{child_key} = root.{root_key}"
