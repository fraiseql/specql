"""Hierarchical flattener pattern for SpecQL."""

from typing import Any

from .utils import (
    build_tree_indexes,
    format_extracted_fields,
    get_default_label_field,
    get_default_value_field,
    validate_flattener_config,
)


def generate_hierarchical_flattener(config: dict[str, Any]) -> str:
    """
    Generate SQL for hierarchical flattener pattern.

    Flattens tree structures for frontend tree components by extracting
    fields from JSONB data and adding required tree navigation fields.
    """
    pattern_config = config.get("config", {})

    # Validate configuration
    issues = validate_flattener_config(pattern_config)
    if issues:
        raise ValueError(f"Invalid flattener configuration: {', '.join(issues)}")

    name = config["name"]
    source_table = pattern_config["source_table"]
    extracted_fields = pattern_config["extracted_fields"]
    frontend_format = pattern_config.get("frontend_format", "generic")
    label_field = get_default_label_field(pattern_config)
    value_field = get_default_value_field(pattern_config)
    path_field = pattern_config.get("path_field")

    # Build SQL
    sql_parts = []

    # View comment
    sql_parts.append("-- @fraiseql:view")
    sql_parts.append(
        f"-- @fraiseql:description Flattened {source_table} for {frontend_format} component"
    )
    sql_parts.append(f"CREATE OR REPLACE VIEW tenant.{name} AS")

    # SELECT clause
    select_parts = []

    # Add extracted fields
    select_parts.append(format_extracted_fields(extracted_fields))

    # Add required tree fields
    select_parts.append("    (data->>'id')::uuid AS id")
    select_parts.append("    NULLIF(data->'parent'->>'id', '')::uuid AS parent_id")
    select_parts.append(f"    data->>'{label_field}' AS label")
    select_parts.append(f"    data->>'{value_field}' AS value")

    # Add ltree field if path_field is specified
    if path_field:
        select_parts.append(f"    REPLACE(data->>'{path_field}', '.', '_')::text AS ltree_id")

    # Add full data column
    select_parts.append("    data  -- Include full data for reference")

    sql_parts.append("SELECT")
    sql_parts.append(",\n".join(select_parts))

    # FROM clause
    sql_parts.append(f"FROM tenant.{source_table}")

    # WHERE clause
    where_parts = ["WHERE deleted_at IS NULL"]
    if pattern_config.get("is_multi_tenant", False):
        tenant_filter = pattern_config.get(
            "tenant_filter", "CURRENT_SETTING('app.current_tenant_id')::uuid"
        )
        where_parts.append(f"  AND tenant_id = {tenant_filter}")
    sql_parts.append("\n".join(where_parts) + ";")

    # Indexes
    indexes = build_tree_indexes(name, pattern_config)
    if indexes:
        sql_parts.append("")
        sql_parts.extend(indexes)

    return "\n".join(sql_parts)
