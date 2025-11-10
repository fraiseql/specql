"""Utilities for wrapper patterns."""

from typing import Any


def parse_table_reference(table_ref: str, default_schema: str) -> tuple[str, str]:
    """Parse a table reference that may include schema prefix.

    Args:
        table_ref: Table name, optionally with schema prefix (e.g., "schema.table" or "table")
        default_schema: Default schema to use if not specified

    Returns:
        Tuple of (schema, table_name)
    """
    if "." in table_ref:
        schema, table_name = table_ref.split(".", 1)
        return schema, table_name
    else:
        return default_schema, table_ref


def build_default_values_clause(default_values: dict[str, Any]) -> str:
    """Build the default values clause for SQL SELECT.

    Args:
        default_values: Dictionary mapping field names to default values

    Returns:
        SQL fragment for default value columns
    """
    if not default_values:
        return ""

    clauses = []
    for field, default in default_values.items():
        clauses.append(f"    {default} AS {field}")

    return ",\n".join(clauses)


def validate_wrapper_config(config: dict[str, Any]) -> None:
    """Validate wrapper pattern configuration.

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    required_fields = ["name", "schema", "materialized_view", "base_table", "key_field"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Required field '{field}' missing from wrapper config")

    if not isinstance(config.get("default_values", {}), dict):
        raise ValueError("default_values must be a dictionary")

    if not isinstance(config.get("ensure_zero_count_entities", True), bool):
        raise ValueError("ensure_zero_count_entities must be a boolean")
