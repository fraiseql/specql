"""Hierarchical count aggregation pattern implementation."""

import os
from typing import Any

from jinja2 import Template

from .utils import build_entity_info, has_hierarchical_metrics, is_multi_tenant_entity


def generate_hierarchical_count(config: dict[str, Any]) -> str:
    """Generate SQL for hierarchical count aggregation pattern.

    Args:
        config: Pattern configuration containing:
            - name: View name
            - config: Pattern-specific config with:
                - counted_entity: Entity being counted
                - grouped_by_entity: Entity to group by (must be hierarchical)
                - path_field: Optional custom path field (default: 'path')
                - metrics: List of metrics with name, direct, and hierarchical flags

    Returns:
        Generated SQL string
    """
    # Load template from stdlib
    template_path = os.path.join(
        os.path.dirname(__file__),
        "../../../stdlib/queries/aggregation/hierarchical_count.sql.jinja2",
    )

    with open(template_path) as f:
        template_content = f.read()

    template = Template(template_content)

    # Build entity information
    counted_entity = build_entity_info(config["config"]["counted_entity"])
    grouped_entity = build_entity_info(config["config"]["grouped_by_entity"])
    grouped_entity["is_multi_tenant"] = is_multi_tenant_entity(
        config["config"]["grouped_by_entity"]
    )

    # Determine path field
    path_field = config["config"].get("path_field", "path")

    # Check if we have any hierarchical metrics
    has_hierarchical = has_hierarchical_metrics(config["config"]["metrics"])

    # Prepare template variables
    performance_config = config.get("performance", {})
    template_vars = {
        "name": config["name"],
        "counted_entity": counted_entity,
        "grouped_by_entity": grouped_entity,
        "path_field": path_field,
        "metrics": config["config"]["metrics"],
        "has_hierarchical": has_hierarchical,
        "schema": config.get("schema", "tenant"),
        "performance": {
            "materialized": performance_config.get("materialized", False),
            "indexes": performance_config.get("indexes", []),
            "refresh_strategy": performance_config.get("refresh_strategy", "manual"),
        },
    }

    return template.render(**template_vars)
