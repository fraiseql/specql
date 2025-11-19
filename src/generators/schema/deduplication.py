"""Generate 3-field deduplication pattern."""

from src.core.ast_models import EntityDefinition


def generate_deduplication_fields(entity: EntityDefinition) -> str:
    """Generate identifier, sequence_number, display_identifier fields."""

    entity.name.lower()

    return """
    -- Deduplication Fields (3-field pattern)
    identifier TEXT NOT NULL,
    sequence_number INTEGER NOT NULL DEFAULT 1,
    display_identifier TEXT GENERATED ALWAYS AS (
        CASE
            WHEN sequence_number > 1
            THEN identifier || '#' || sequence_number
            ELSE identifier
        END
    ) STORED
""".strip()


def generate_deduplication_indexes(entity: EntityDefinition, schema: str) -> str:
    """Generate tenant-scoped indexes and constraints for deduplication fields."""

    entity_name = entity.name.lower()
    table_name = f"{schema}.tb_{entity_name}"

    # Tenant-scoped unique constraints (all tables have tenant_id per Trinity pattern)
    return f"""
-- Tenant-scoped deduplication constraints
ALTER TABLE {table_name}
    DROP CONSTRAINT IF EXISTS tb_{entity_name}_display_identifier_key;

ALTER TABLE {table_name}
    ADD CONSTRAINT unique_tenant_display_identifier
    UNIQUE (tenant_id, display_identifier);

ALTER TABLE {table_name}
    ADD CONSTRAINT unique_tenant_identifier_sequence
    UNIQUE (tenant_id, identifier, sequence_number);

-- Tenant-scoped deduplication indexes
CREATE INDEX idx_{entity_name}_tenant_identifier
    ON {table_name}(tenant_id, identifier);
"""
