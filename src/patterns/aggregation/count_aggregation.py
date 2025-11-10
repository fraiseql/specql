"""Count aggregation pattern implementation."""

import os
from typing import Any

from jinja2 import Template

from .utils import build_default_join_condition, build_entity_info, is_multi_tenant_entity


def generate_count_aggregation(config: dict[str, Any]) -> str:
    """Generate SQL for count aggregation pattern.

    Args:
        config: Pattern configuration containing:
            - name: View name
            - config: Pattern-specific config with:
                - counted_entity: Entity being counted
                - grouped_by_entity: Entity to group by
                - join_condition: Optional JOIN condition
                - metrics: List of metrics with name and condition

    Returns:
        Generated SQL string
    """
    # Load template from stdlib
    template_path = os.path.join(
        os.path.dirname(__file__),
        "../../../stdlib/queries/aggregation/count_aggregation.sql.jinja2",
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

    # Determine join condition
    join_condition = config["config"].get("join_condition")
    if not join_condition:
        join_condition = build_default_join_condition(counted_entity, grouped_entity)

    # Prepare template variables
    performance_config = config.get("performance", {})
    template_vars = {
        "name": config["name"],
        "counted_entity": counted_entity,
        "grouped_by_entity": grouped_entity,
        "join_condition": join_condition,
        "metrics": config["config"]["metrics"],
        "schema": config.get("schema", "tenant"),
        "performance": {
            "materialized": performance_config.get("materialized", False),
            "indexes": performance_config.get("indexes", []),
            "refresh_strategy": performance_config.get("refresh_strategy", "manual"),
        },
    }

    return template.render(**template_vars)
