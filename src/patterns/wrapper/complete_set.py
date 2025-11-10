"""Complete set wrapper pattern for materialized views."""

from typing import Any

from .utils import build_default_values_clause, parse_table_reference, validate_wrapper_config


def generate_complete_set_wrapper(config: dict[str, Any]) -> str:
    """Generate SQL for complete set wrapper pattern.

    Wraps a materialized view to ensure complete result sets by including
    entities with zero counts that aren't present in the MV.
    """
    # Validate configuration
    validate_wrapper_config(config)

    name = config["name"]
    schema = config["schema"]
    key_field = config["key_field"]
    default_values = config.get("default_values", {})
    ensure_zero_count_entities = config.get("ensure_zero_count_entities", True)
    is_multi_tenant = config.get("is_multi_tenant", False)
    tenant_filter = config.get("tenant_filter", "CURRENT_SETTING('app.current_tenant_id')::uuid")

    # Parse table references
    mv_schema, mv_name = parse_table_reference(config["materialized_view"], schema)
    base_schema, base_name = parse_table_reference(config["base_table"], schema)

    sql_parts = [
        "-- @fraiseql:view",
        f"-- @fraiseql:description Complete result set wrapper for {config['materialized_view']}",
        f"CREATE OR REPLACE VIEW {schema}.{name} AS",
        "-- Include all results from materialized view",
        f"SELECT * FROM {mv_schema}.{mv_name}",
    ]

    if ensure_zero_count_entities:
        sql_parts.extend(
            [
                "",
                "UNION ALL",
                "",
                "-- Include missing entities with default values",
                "SELECT",
                f"    base.{key_field}{',' if default_values else ''}",
            ]
        )

        # Add default value columns using utility
        if default_values:
            default_clause = build_default_values_clause(default_values)
            sql_parts.append(default_clause)

        sql_parts.extend(
            [
                f"FROM {base_schema}.{base_name} base",
                "WHERE NOT EXISTS (",
                "    SELECT 1",
                f"    FROM {mv_schema}.{mv_name} mv",
                f"    WHERE mv.{key_field} = base.{key_field}",
                ")",
                "AND base.deleted_at IS NULL",
            ]
        )

        if is_multi_tenant:
            sql_parts.append(f"  AND base.tenant_id = {tenant_filter};")
        else:
            sql_parts.append(";")

    sql_parts.extend(
        [
            "",
            f"COMMENT ON VIEW {schema}.{name} IS",
            f"    'Wraps {config['materialized_view']} to include all {config['base_table']} entities, even those with zero counts';",
        ]
    )

    return "\n".join(sql_parts)
