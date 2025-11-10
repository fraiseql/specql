"""Utilities for hierarchical patterns."""

from typing import Any


def detect_hierarchical_fields(entity_config: dict[str, Any]) -> dict[str, str]:
    """
    Auto-detect hierarchical fields from entity definition.

    Returns dict mapping field types to field names.
    """
    fields = {}

    if "fields" in entity_config:
        for field_name, field_config in entity_config["fields"].items():
            field_type = field_config.get("type", "").lower()

            # Check for ltree path fields
            if field_type == "ltree" or "path" in field_name.lower():
                fields["path"] = field_name

            # Check for parent references
            if "parent" in field_name.lower() or field_type.endswith("_id"):
                fields["parent_id"] = field_name

            # Check for name/label fields
            if field_type in ["text", "varchar"] and any(
                name in field_name.lower() for name in ["name", "title", "label"]
            ):
                fields["name"] = field_name

    return fields


def calculate_tree_depth(path_field: str, table_alias: str = "entity") -> str:
    """Generate SQL to calculate tree depth from path field."""
    return f"nlevel({table_alias}.{path_field})"


def build_parent_lookup_join(
    child_table: str, parent_table: str, child_fk_field: str, parent_pk_field: str
) -> str:
    """Build JOIN clause for parent lookup."""
    return f"LEFT JOIN {parent_table} parent ON child.{child_fk_field} = parent.{parent_pk_field}"


def validate_flattener_config(config: dict[str, Any]) -> list[str]:
    """Validate flattener configuration and return list of issues."""
    issues = []

    if "source_table" not in config:
        issues.append("source_table is required")

    if "extracted_fields" not in config:
        issues.append("extracted_fields is required")
    elif not isinstance(config["extracted_fields"], list):
        issues.append("extracted_fields must be a list")
    else:
        for i, field in enumerate(config["extracted_fields"]):
            if not isinstance(field, dict):
                issues.append(f"extracted_fields[{i}] must be a dict")
            elif "name" not in field or "expression" not in field:
                issues.append(f"extracted_fields[{i}] must have 'name' and 'expression' keys")

    frontend_format = config.get("frontend_format", "generic")
    valid_formats = ["rust_tree", "react_tree", "generic"]
    if frontend_format not in valid_formats:
        issues.append(f"frontend_format must be one of: {valid_formats}")

    return issues


def build_tree_indexes(view_name: str, config: dict[str, Any]) -> list[str]:
    """Build index creation statements for tree views."""
    indexes = []

    # Parent lookup index
    indexes.append(f"CREATE INDEX IF NOT EXISTS idx_{view_name}_parent")
    indexes.append(f"    ON tenant.{view_name}(parent_id)")
    indexes.append("    WHERE parent_id IS NOT NULL;")

    # Ltree index if path field exists
    if config.get("path_field"):
        indexes.append("")
        indexes.append(f"CREATE INDEX IF NOT EXISTS idx_{view_name}_ltree")
        indexes.append(f"    ON tenant.{view_name} USING GIST (ltree_id);")

    return indexes


def format_extracted_fields(fields: list[dict[str, str]]) -> str:
    """Format extracted fields for SELECT clause."""
    sql_parts = []
    for field in fields:
        name = field["name"]
        expression = field["expression"]
        sql_parts.append(f"    {expression} AS {name}")
    return ",\n".join(sql_parts)


def get_default_label_field(config: dict[str, Any]) -> str:
    """Get default label field name."""
    return str(config.get("label_field", "name"))


def get_default_value_field(config: dict[str, Any]) -> str:
    """Get default value field name."""
    return str(config.get("value_field", "id"))


def build_path_expansion_cte(source_entity: str, path_field: str, pk_field: str) -> str:
    """Build the expanded CTE for path expansion."""
    # Convert PascalCase to snake_case for table name
    import re

    snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", source_entity).lower()
    table_name = f"tb_{snake_case}"
    return f"""WITH expanded AS (
  SELECT
    {pk_field},
    {path_field},
    unnest(string_to_array({path_field}::text, '.'))::integer AS ancestor_id
  FROM tenant.{table_name}
  WHERE deleted_at IS NULL
)"""


def build_enriched_cte(
    expanded_fields: list[str],
    source_entity: str,
    path_field: str,
    pk_field: str,
    max_depth: int | None = None,
) -> str:
    """Build the enriched CTE with ancestor data."""
    # Convert PascalCase to snake_case for table name
    import re

    snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", source_entity).lower()
    table_name = f"tb_{snake_case}"

    # Map expanded fields to actual field names
    field_mappings = {
        "ancestor_ids": f"array_agg(a.{pk_field} ORDER BY nlevel(a.{path_field})) AS ancestor_ids",
        "ancestor_names": f"array_agg(a.name ORDER BY nlevel(a.{path_field})) AS ancestor_names",
        "breadcrumb_labels": f"array_agg(a.display_name ORDER BY nlevel(a.{path_field})) AS breadcrumb_labels",
    }

    # Build expanded fields SQL with proper comma separation
    expanded_sql = []
    for i, field in enumerate(expanded_fields):
        comma = "," if i < len(expanded_fields) - 1 else ""
        expanded_sql.append(f"    {field_mappings[field]}{comma}")

    # Add depth limiting if specified
    depth_filter = ""
    if max_depth:
        depth_filter = f" AND nlevel(a.{path_field}) <= {max_depth}"

    return f""",enriched AS (
  SELECT
    e.{pk_field},
{chr(10).join(expanded_sql)}
  FROM expanded e
  JOIN tenant.{table_name} a ON a.{pk_field} = e.ancestor_id{depth_filter}
  GROUP BY e.{pk_field}
)"""


def detect_node_type(path_field: str, table_alias: str = "entity") -> str:
    """Generate SQL to detect if a node is a leaf or internal node."""
    return f"""
CASE
  WHEN EXISTS (
    SELECT 1 FROM {table_alias} child
    WHERE child.{path_field} <@ {table_alias}.{path_field}
    AND child.{path_field} != {table_alias}.{path_field}
  ) THEN 'internal'
  ELSE 'leaf'
END AS node_type"""


def build_sibling_enumeration(source_entity: str, path_field: str, pk_field: str) -> str:
    """Build sibling enumeration for hierarchical queries."""
    table_name = f"tb_{source_entity.lower()}"
    return f"""
SELECT
  parent.{pk_field},
  array_agg(
    jsonb_build_object(
      'id', sibling.{pk_field},
      'name', sibling.name,
      'level', nlevel(sibling.{path_field})
    ) ORDER BY sibling.name
  ) AS siblings
FROM tenant.{table_name} parent
JOIN tenant.{table_name} sibling
  ON sibling.{path_field} <@ parent.{path_field}
  AND nlevel(sibling.{path_field}) = nlevel(parent.{path_field}) + 1
WHERE parent.deleted_at IS NULL
  AND sibling.deleted_at IS NULL
GROUP BY parent.{pk_field}"""


def validate_expander_config(config: dict[str, Any]) -> list[str]:
    """Validate path expander configuration."""
    issues = []

    if "source_entity" not in config:
        issues.append("source_entity is required")

    if "path_field" not in config:
        issues.append("path_field is required")

    if "expanded_fields" not in config:
        issues.append("expanded_fields is required")
    elif not isinstance(config["expanded_fields"], list):
        issues.append("expanded_fields must be a list")
    elif not config["expanded_fields"]:
        issues.append("expanded_fields cannot be empty")
    else:
        valid_fields = ["ancestor_ids", "ancestor_names", "breadcrumb_labels"]
        for field in config["expanded_fields"]:
            if field not in valid_fields:
                issues.append(f"Invalid expanded field '{field}'. Must be one of: {valid_fields}")

    return issues
