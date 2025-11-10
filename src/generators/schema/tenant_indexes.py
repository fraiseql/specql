"""Tenant-scoped composite index generation for multi-tenant performance."""

from src.core.ast_models import EntityDefinition


def generate_tenant_indexes(entity: EntityDefinition, schema: str) -> list[str]:
    """Generate tenant-scoped composite indexes for optimal multi-tenant performance.

    Args:
        entity: Entity definition from AST
        schema: Schema name (tenant, catalog, etc.)

    Returns:
        List of SQL CREATE INDEX statements

    Generated indexes:
    1. Tenant isolation: (tenant_id) WHERE deleted_at IS NULL
    2. Tenant + ID lookup: UNIQUE (tenant_id, id)
    3. For hierarchical: Tenant + Path: (tenant_id, path) WHERE deleted_at IS NULL
    4. For hierarchical: Tenant + Parent: (tenant_id, fk_parent_*) WHERE deleted_at IS NULL
    """
    entity_name = entity.name.lower()
    table_name = f"{schema}.tb_{entity_name}"
    indexes = []

    # 1. Tenant isolation index (most important for RLS and tenant queries)
    indexes.append(
        f"""CREATE INDEX idx_{entity_name}_tenant
    ON {table_name}(tenant_id)
    WHERE deleted_at IS NULL;"""
    )

    # 2. Tenant + ID (for efficient lookups by tenant + UUID)
    indexes.append(
        f"""CREATE UNIQUE INDEX idx_{entity_name}_tenant_id
    ON {table_name}(tenant_id, id);"""
    )

    # 3. For hierarchical entities: Tenant + Path
    if _is_entity_hierarchical(entity):
        indexes.append(
            f"""CREATE INDEX idx_{entity_name}_tenant_path
    ON {table_name}(tenant_id, path)
    WHERE deleted_at IS NULL;"""
        )

        # 4. For hierarchical entities: Tenant + Parent
        indexes.append(
            f"""CREATE INDEX idx_{entity_name}_tenant_parent
    ON {table_name}(tenant_id, fk_parent_{entity_name})
    WHERE deleted_at IS NULL;"""
        )

    return indexes


def _is_entity_hierarchical(entity: EntityDefinition) -> bool:
    """Determine if an entity is hierarchical by checking for self-referencing parent fields."""
    for field_name, field_def in entity.fields.items():
        if field_def.is_reference():
            # Check if this field references the same entity (parent relationship)
            if field_def.reference_entity == entity.name:
                return True
    return False


def generate_tenant_isolation_index(entity: EntityDefinition, schema: str) -> str:
    """Generate just the tenant isolation index (most critical for performance)."""
    entity_name = entity.name.lower()
    table_name = f"{schema}.tb_{entity_name}"

    return f"""CREATE INDEX idx_{entity_name}_tenant
    ON {table_name}(tenant_id)
    WHERE deleted_at IS NULL;"""


def generate_tenant_id_lookup_index(entity: EntityDefinition, schema: str) -> str:
    """Generate tenant + ID lookup index."""
    entity_name = entity.name.lower()
    table_name = f"{schema}.tb_{entity_name}"

    return f"""CREATE UNIQUE INDEX idx_{entity_name}_tenant_id
    ON {table_name}(tenant_id, id);"""
