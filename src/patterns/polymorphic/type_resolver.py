"""Polymorphic type resolver pattern implementation."""

import os
from typing import Any

from jinja2 import Template


def generate_type_resolver(config: dict[str, Any]) -> str:
    """Generate SQL for polymorphic type resolver pattern.

    Args:
        config: Pattern configuration containing:
            - name: View name
            - config: Pattern-specific config with:
                - discriminator_field: Field that discriminates between types
                - variants: List of entity variants
                - output_key: Unified field name for primary key
                - schema: Schema name (default: tenant)
                - materialized: Whether to create materialized view (default: True)

    Returns:
        Generated SQL string

    Raises:
        ValueError: If configuration is invalid
    """
    # Extract configuration
    pattern_config = config.get("config", config)

    # Validate required fields
    if "discriminator_field" not in pattern_config:
        raise ValueError("discriminator_field is required for polymorphic type resolver")

    if "variants" not in pattern_config:
        raise ValueError("variants is required for polymorphic type resolver")

    if not isinstance(pattern_config["variants"], list) or len(pattern_config["variants"]) == 0:
        raise ValueError("variants must be a non-empty list")

    # Validate each variant
    for i, variant in enumerate(pattern_config["variants"]):
        if "entity" not in variant:
            raise ValueError(f"variant {i}: entity is required")
        if "key_field" not in variant:
            raise ValueError(f"variant {i}: key_field is required")
        if "class_value" not in variant:
            raise ValueError(f"variant {i}: class_value is required")

    # Load template from stdlib
    template_path = os.path.join(
        os.path.dirname(__file__),
        "../../../stdlib/queries/polymorphic/type_resolver.sql.jinja2",
    )

    with open(template_path) as f:
        template_content = f.read()

    template = Template(template_content)

    # Prepare template variables
    template_vars = {
        "name": config["name"],
        "view_name": f"v_{config['name']}",
        "discriminator_field": pattern_config["discriminator_field"],
        "variants": pattern_config["variants"],
        "output_key": pattern_config.get("output_key", "pk_value"),
        "schema": pattern_config.get("schema", "tenant"),
        "materialized": pattern_config.get("materialized", False),
        "is_multi_tenant": pattern_config.get("is_multi_tenant", False),
        "tenant_filter": pattern_config.get(
            "tenant_filter", "CURRENT_SETTING('app.current_tenant_id')::uuid"
        ),
    }

    return template.render(**template_vars)
