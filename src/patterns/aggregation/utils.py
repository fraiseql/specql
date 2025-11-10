"""Utilities for aggregation patterns."""

from typing import Any


def build_entity_info(entity_name: str) -> dict[str, Any]:
    """Build entity information dict for templates."""
    return {
        "name": entity_name,
        "table": f"tb_{entity_name.lower()}",
        "alias": entity_name.lower(),
        "pk_field": f"pk_{entity_name.lower()}",
    }


def build_default_join_condition(counted_entity: dict, grouped_entity: dict) -> str:
    """Build default JOIN condition between counted and grouped entities."""
    fk_field = f"{grouped_entity['name'].lower()}_id"
    return f"{counted_entity['alias']}.{fk_field} = {grouped_entity['alias']}.{grouped_entity['pk_field']}"


def format_metrics_sql(metrics: list[dict[str, str]]) -> str:
    """Format metrics list into SQL COUNT statements."""
    sql_parts = []
    for metric in metrics:
        sql_parts.append(f"COUNT(CASE WHEN {metric['condition']} THEN 1 END) AS {metric['name']}")
    return ",\n".join(sql_parts)


def is_multi_tenant_entity(entity_name: str) -> bool:
    """Check if entity is multi-tenant."""
    # This could be expanded with a registry lookup
    return entity_name in ["Location", "NetworkConfiguration", "Contract", "Organization"]


def build_tenant_filter(alias: str) -> str:
    """Build tenant filter clause."""
    return f"{alias}.tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid"


def build_ltree_containment(parent_path_field: str, child_path_field: str) -> str:
    """Build ltree containment check for hierarchical queries."""
    return f"parent.{parent_path_field} @> child.{child_path_field}"


def build_direct_child_check(parent_pk_field: str, child_fk_field: str) -> str:
    """Build direct child relationship check."""
    return f"child.{child_fk_field} = parent.{parent_pk_field}"


def has_hierarchical_metrics(metrics: list[dict[str, Any]]) -> bool:
    """Check if any metrics require hierarchical aggregation."""
    return any(metric.get("hierarchical", False) for metric in metrics)


def needs_join_for_flags(flags: list[dict[str, Any]], join_entity: str) -> bool:
    """Check if flags require a JOIN to a specific entity."""
    return any(join_entity in flag["condition"] for flag in flags)


def validate_flag_conditions(flags: list[dict[str, Any]]) -> list[str]:
    """Validate flag conditions and return any issues."""
    issues = []
    for flag in flags:
        condition = flag["condition"]
        if not condition.strip():
            issues.append(f"Flag '{flag['name']}' has empty condition")
        # Could add more validation here
    return issues
