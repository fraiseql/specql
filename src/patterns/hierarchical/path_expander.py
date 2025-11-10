"""Hierarchical path expander pattern for SpecQL."""

from typing import Any

from .utils import build_enriched_cte, build_path_expansion_cte, validate_expander_config


def generate_path_expander(config: dict[str, Any]) -> str:
    """
    Generate SQL for hierarchical path expander pattern.

    Expands ltree paths to arrays of ancestor data for efficient
    breadcrumb navigation and hierarchical queries.
    """
    pattern_config = config.get("config", {})

    # Validate configuration
    issues = validate_expander_config(pattern_config)
    if issues:
        raise ValueError(f"Invalid expander configuration: {', '.join(issues)}")

    name = config["name"]
    source_entity = pattern_config["source_entity"]
    path_field = pattern_config["path_field"]
    expanded_fields = pattern_config["expanded_fields"]
    max_depth = pattern_config.get("max_depth")

    # Build table and field names
    # Convert PascalCase to snake_case for table/field names
    import re

    snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", source_entity).lower()
    pk_field = f"pk_{snake_case}"

    # Build SQL
    sql_parts = []

    # View comment
    sql_parts.append("-- @fraiseql:view")
    sql_parts.append(f"-- @fraiseql:description Expanded {path_field} paths for {source_entity}")
    sql_parts.append(f"CREATE OR REPLACE VIEW tenant.{name} AS")

    # Add CTEs using utilities
    sql_parts.append(build_path_expansion_cte(source_entity, path_field, pk_field))
    sql_parts.append(
        build_enriched_cte(expanded_fields, source_entity, path_field, pk_field, max_depth)
    )

    # Final SELECT
    sql_parts.append("SELECT * FROM enriched;")

    return "\n".join(sql_parts)
