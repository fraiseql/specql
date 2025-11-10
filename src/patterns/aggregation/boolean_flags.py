"""Boolean flag aggregation pattern implementation."""

import os
from typing import Any

from jinja2 import Template

from .utils import build_entity_info, is_multi_tenant_entity, needs_join_for_flags


def generate_boolean_flags(config: dict[str, Any]) -> str:
    """Generate SQL for boolean flag aggregation pattern.

    Args:
        config: Pattern configuration containing:
            - name: View name
            - config: Pattern-specific config with:
                - source_entity: Entity to generate flags for
                - flags: List of flag definitions with name and condition
                - array_field: Optional JSONB array field name
                - array_fields: Optional fields to include in array
                - order_by: Optional ordering for array

    Returns:
        Generated SQL string
    """
    # Load template from stdlib
    template_path = os.path.join(
        os.path.dirname(__file__),
        "../../../stdlib/queries/aggregation/boolean_flags.sql.jinja2",
    )

    with open(template_path) as f:
        template_content = f.read()

    template = Template(template_content)

    # Build entity information
    source_entity = build_entity_info(config["config"]["source_entity"])
    source_entity["is_multi_tenant"] = is_multi_tenant_entity(config["config"]["source_entity"])

    # Check if we need allocation join
    needs_allocation_join = needs_join_for_flags(config["config"]["flags"], "allocation")

    # Prepare template variables
    template_vars = {
        "name": config["name"],
        "source_entity": source_entity,
        "flags": config["config"]["flags"],
        "needs_allocation_join": needs_allocation_join,
        "schema": config.get("schema", "tenant"),
    }

    return template.render(**template_vars)
