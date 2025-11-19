"""Safety constraint triggers for hierarchical entities."""

from jinja2 import Template

from src.core.ast_models import EntityDefinition


def generate_safety_constraints(entity: EntityDefinition, schema: str) -> list[str]:
    """Generate safety constraint triggers for hierarchical entities.

    Generates 3 safety triggers for entities with hierarchical relationships:
    1. Prevent circular references
    2. Check identifier sequence limits
    3. Check hierarchy depth limits

    Args:
        entity: Entity definition from AST
        schema: Schema name (tenant, catalog, etc.)

    Returns:
        List of SQL statements for safety triggers (empty list for non-hierarchical entities)
    """
    # Only generate constraints for hierarchical entities
    if not _is_entity_hierarchical(entity):
        return []

    entity_lower = entity.name.lower()
    constraints = []

    # Template variables
    template_vars = {"schema": schema, "entity": entity.name, "entity_lower": entity_lower}

    # 1. Prevent circular references
    with open("templates/sql/constraints/prevent_cycle.sql.jinja2") as f:
        cycle_template = Template(f.read())
    constraints.append(cycle_template.render(**template_vars))

    # 2. Check identifier sequence limits
    with open("templates/sql/constraints/check_sequence_limit.sql.jinja2") as f:
        sequence_template = Template(f.read())
    constraints.append(sequence_template.render(**template_vars))

    # 3. Check hierarchy depth limits
    with open("templates/sql/constraints/check_depth_limit.sql.jinja2") as f:
        depth_template = Template(f.read())
    constraints.append(depth_template.render(**template_vars))

    return constraints


def _is_entity_hierarchical(entity: EntityDefinition) -> bool:
    """Determine if an entity is hierarchical by checking for self-referencing parent fields."""
    for field_name, field_def in entity.fields.items():
        if field_def.is_reference():
            # Check if this field references the same entity (parent relationship)
            if field_def.reference_entity == entity.name:
                return True
    return False


def generate_circular_reference_check(entity: EntityDefinition, schema: str) -> str:
    """Generate just the circular reference prevention trigger."""
    if not _is_entity_hierarchical(entity):
        return ""

    entity_lower = entity.name.lower()
    template_vars = {"schema": schema, "entity": entity.name, "entity_lower": entity_lower}

    with open("templates/sql/constraints/prevent_cycle.sql.jinja2") as f:
        template = Template(f.read())
    return template.render(**template_vars)


def generate_sequence_limit_check(entity: EntityDefinition, schema: str) -> str:
    """Generate just the identifier sequence limit check trigger."""
    entity_lower = entity.name.lower()
    template_vars = {"schema": schema, "entity": entity.name, "entity_lower": entity_lower}

    with open("templates/sql/constraints/check_sequence_limit.sql.jinja2") as f:
        template = Template(f.read())
    return template.render(**template_vars)


def generate_depth_limit_check(entity: EntityDefinition, schema: str) -> str:
    """Generate just the hierarchy depth limit check trigger."""
    if not _is_entity_hierarchical(entity):
        return ""

    entity_lower = entity.name.lower()
    template_vars = {"schema": schema, "entity": entity.name, "entity_lower": entity_lower}

    with open("templates/sql/constraints/check_depth_limit.sql.jinja2") as f:
        template = Template(f.read())
    return template.render(**template_vars)
