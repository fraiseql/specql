"""Materialized view refresh orchestration for wrapper patterns."""

from typing import Any


def validate_refresh_config(config: dict[str, Any]) -> None:
    """Validate refresh configuration."""
    required_fields = ["mv_name", "schema"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Required field '{field}' missing from refresh config")

    if not isinstance(config.get("concurrent", True), bool):
        raise ValueError("concurrent must be a boolean")


def generate_refresh_function(config: dict[str, Any]) -> str:
    """Generate SQL for materialized view refresh function.

    Creates a PostgreSQL function that refreshes a materialized view
    with optional logging and concurrency control.
    """
    validate_refresh_config(config)

    mv_name = config["mv_name"]
    schema = config["schema"]
    concurrent = config.get("concurrent", True)
    log_table = config.get("log_table")

    function_name = f"{schema}.refresh_{mv_name}"

    sql_parts = [
        f"-- Auto-generated refresh function for {mv_name}",
        f"CREATE OR REPLACE FUNCTION {function_name}()",
        "RETURNS void AS $$",
        "BEGIN",
    ]

    # Refresh statement
    refresh_sql = "REFRESH MATERIALIZED VIEW"
    if concurrent:
        refresh_sql += " CONCURRENTLY"
    refresh_sql += f" {schema}.{mv_name};"

    sql_parts.append(f"  {refresh_sql}")

    # Optional logging
    if log_table:
        sql_parts.extend(
            [
                "",
                "  -- Log the refresh",
                f"  INSERT INTO {log_table} (mv_name, refreshed_at, duration_ms)",
                f"  VALUES ('{mv_name}', NOW(), EXTRACT(epoch FROM NOW() - clock_timestamp()) * 1000);",
            ]
        )

    sql_parts.extend(["", "END;", "$$ LANGUAGE plpgsql;"])

    return "\n".join(sql_parts)


def validate_trigger_config(config: dict[str, Any]) -> None:
    """Validate trigger configuration."""
    required_fields = ["mv_name", "schema", "base_table"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Required field '{field}' missing from trigger config")


def generate_refresh_trigger(config: dict[str, Any]) -> str:
    """Generate SQL for materialized view refresh trigger.

    Creates a trigger that invalidates MV cache when base tables change.
    Note: This assumes an invalidate_mv_cache function exists.
    """
    validate_trigger_config(config)

    mv_name = config["mv_name"]
    schema = config["schema"]
    base_table = config["base_table"]
    base_schema = config.get("base_schema", schema)
    trigger_name = config.get("trigger_name", f"trg_refresh_{mv_name}")

    sql_parts = [
        f"-- Auto-generated refresh trigger for {mv_name}",
        f"CREATE TRIGGER {trigger_name}",
        "AFTER INSERT OR UPDATE OR DELETE",
        f"ON {base_schema}.{base_table}",
        "FOR EACH STATEMENT",
        f"EXECUTE FUNCTION {schema}.invalidate_mv_cache('{mv_name}');",
    ]

    return "\n".join(sql_parts)


def generate_refresh_orchestration(config: dict[str, Any]) -> str:
    """Generate complete refresh orchestration (function + trigger)."""
    # Validate both function and trigger configs
    validate_refresh_config(config)
    validate_trigger_config(config)

    function_sql = generate_refresh_function(config)
    trigger_sql = generate_refresh_trigger(config)

    return f"{function_sql}\n\n{trigger_sql}"
