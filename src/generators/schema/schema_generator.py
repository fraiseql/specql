"""
Schema Generator

Generates complete PostgreSQL DDL from Team A's AST:
- Trinity Pattern fields
- Business fields (scalars, composites, references)
- Audit fields
- Indexes
- Constraints
- Table code integration with NamingConventions registry
"""

from src.core.ast_models import EntityDefinition, FieldDefinition
from src.generators.schema.audit_fields import generate_audit_fields
from src.generators.schema.composite_type_mapper import CompositeTypeMapper
from src.generators.schema.deduplication import (
    generate_deduplication_fields,
    generate_deduplication_indexes,
)
from src.generators.schema.foreign_key_generator import ForeignKeyGenerator
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.node_info_split import (
    generate_node_info_split_ddl,
    should_split_entity,
)
from src.generators.schema.tenant_indexes import generate_tenant_indexes
from src.utils.safe_slug import safe_table_name


class SchemaGenerator:
    """Generates PostgreSQL schema DDL from EntityDefinition AST"""

    def __init__(self, registry_path: str = "registry/domain_registry.yaml"):
        self.composite_mapper = CompositeTypeMapper()
        self.fk_generator = ForeignKeyGenerator()
        self.naming = NamingConventions(registry_path)

    def generate_table(self, entity: EntityDefinition) -> str:
        """
        Generate complete CREATE TABLE statement or node+info split DDL

        Args:
            entity: EntityDefinition from Team A

        Returns:
            Complete DDL including table, indexes, comments, and helper functions
        """
        # Check if entity should use node+info split pattern
        if should_split_entity(entity):
            ddl_statements = generate_node_info_split_ddl(entity, entity.schema)
            return "\n\n".join(ddl_statements)

        # Standard single table generation
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"

        ddl_parts = []

        # CREATE TABLE
        ddl_parts.append(f"-- Table: {entity.name}")
        if entity.description:
            ddl_parts.append(f"-- {entity.description}")
        ddl_parts.append(f"CREATE TABLE {table_name} (")

        # Trinity Pattern fields
        trinity_fields = self._generate_trinity_fields(entity)
        ddl_parts.append("    -- Trinity Pattern")
        for field in trinity_fields:
            ddl_parts.append(f"    {field},")
        ddl_parts.append("")

        # Deduplication fields (3-field pattern)
        dedup_fields = generate_deduplication_fields(entity)
        ddl_parts.append("    -- Deduplication Fields")
        ddl_parts.append(f"    {dedup_fields},")
        ddl_parts.append("")

        # Business fields
        ddl_parts.append("    -- Business fields")
        for field_name, field_def in entity.fields.items():
            field_ddl = self._generate_field_ddl(field_def)
            ddl_parts.append(f"    {field_ddl},")
        ddl_parts.append("")

        # Audit fields (separate recalculation tracking)
        is_hierarchical = self._is_entity_hierarchical(entity)
        audit_fields = generate_audit_fields(is_hierarchical=is_hierarchical)
        ddl_parts.append("    -- Audit Fields")
        ddl_parts.append(audit_fields)

        # Remove last comma from audit fields
        ddl_parts[-1] = ddl_parts[-1].rstrip(",")

        ddl_parts.append(");")
        ddl_parts.append("")

        # Add explicit validation pattern comment for hierarchical entities
        if self._is_entity_hierarchical(entity):
            ddl_parts.append(self._generate_explicit_validation_comment(entity))
            ddl_parts.append("")

        # Validation functions for composites
        validation_functions = self._generate_validation_functions(entity)
        if validation_functions:
            ddl_parts.append("-- Validation functions")
            ddl_parts.extend(validation_functions)
            ddl_parts.append("")

        # Trinity helper functions
        trinity_helpers = self._generate_trinity_helper_functions(entity)
        if trinity_helpers:
            ddl_parts.append("-- Trinity Helper Functions")
            ddl_parts.extend(trinity_helpers)
            ddl_parts.append("")

        # Trinity indexes
        trinity_indexes = self._generate_trinity_indexes(entity)
        if trinity_indexes:
            ddl_parts.append("-- Trinity Indexes")
            ddl_parts.extend(trinity_indexes)
            ddl_parts.append("")

        # Deduplication indexes and constraints
        dedup_indexes = generate_deduplication_indexes(entity, entity.schema)
        if dedup_indexes:
            ddl_parts.append("-- Deduplication Indexes & Constraints")
            ddl_parts.append(dedup_indexes)
            ddl_parts.append("")

        # Indexes for composites and foreign keys
        indexes = self._generate_indexes(entity)
        if indexes:
            ddl_parts.append("-- Indexes")
            ddl_parts.extend(indexes)
            ddl_parts.append("")

        # Tenant-scoped composite indexes
        tenant_indexes = generate_tenant_indexes(entity, entity.schema)
        if tenant_indexes:
            ddl_parts.append("-- Tenant Indexes")
            ddl_parts.extend(tenant_indexes)
            ddl_parts.append("")

        # NOTE: Explicit validation pattern replaces safety constraint triggers
        # Validation is now handled explicitly in mutation functions, not via triggers

        return "\n".join(ddl_parts)

    def _generate_field_ddl(self, field: FieldDefinition) -> str:
        """Generate DDL for a single field based on tier"""

        if field.is_composite():
            # Tier 2: Composite type
            composite_ddl = self.composite_mapper.map_field(field)
            return self.composite_mapper.generate_field_ddl(composite_ddl)

        elif field.is_reference():
            # Tier 3: Reference type
            fk_ddl = self.fk_generator.map_field(field)
            return self.fk_generator.generate_field_ddl(fk_ddl)

        else:
            # Basic type or other tiers (placeholder for now)
            null_constraint = "" if field.nullable else " NOT NULL"
            return f"{field.name} {field.postgres_type or 'TEXT'}{null_constraint}"

    def _generate_validation_functions(self, entity: EntityDefinition) -> list[str]:
        """Generate validation functions for composite fields"""
        functions = []

        for field_name, field_def in entity.fields.items():
            if field_def.is_composite():
                composite_def = field_def.composite_def
                if composite_def is None:
                    from src.core.scalar_types import get_composite_type

                    composite_def = get_composite_type(field_def.type_name)

                if composite_def:
                    functions.append(
                        self.composite_mapper.generate_validation_function(composite_def)
                    )

        return functions

    def _is_entity_hierarchical(self, entity: EntityDefinition) -> bool:
        """Determine if an entity is hierarchical by checking for self-referencing parent fields."""
        for field_name, field_def in entity.fields.items():
            if field_def.is_reference():
                # Check if this field references the same entity (parent relationship)
                if field_def.reference_entity == entity.name:
                    return True
        return False

    def _generate_explicit_validation_comment(self, entity: EntityDefinition) -> str:
        """Generate comment explaining explicit validation pattern."""
        entity_lower = entity.name.lower()
        schema = entity.schema

        return f"""-- ════════════════════════════════════════════════════════════════
-- VALIDATION PATTERN: Explicit over Implicit (NO TRIGGERS!)
-- ════════════════════════════════════════════════════════════════
--
-- This entity uses EXPLICIT validation instead of database triggers.
-- Mutations call validation functions directly (visible in code).
--
-- Available validation functions:
--   • core.validate_hierarchy_change('{entity_lower}', node_pk, new_parent_pk)
--   • core.validate_identifier_sequence('{entity_lower}', identifier, seq_num)
--
-- Available recalculation functions:
--   • core.recalculate_tree_path('{entity_lower}', context)
--   • core.recalculate_identifier('{entity_lower}', context)
--
-- Example mutation usage:
--   v_error := core.validate_hierarchy_change('{entity_lower}', ...);
--   IF v_error IS NOT NULL THEN RETURN error_response(v_error); END IF;
--
--   UPDATE {schema}.tb_{entity_lower} SET fk_parent_{entity_lower} = ...;
--
--   PERFORM core.recalculate_tree_path('{entity_lower}', ...);
--   PERFORM core.recalculate_identifier('{entity_lower}', ...);
--
-- Benefits: Visible, debuggable, testable, controllable
-- ════════════════════════════════════════════════════════════════""".strip()

    def _generate_indexes(self, entity: EntityDefinition) -> list[str]:
        """Generate indexes for composite and reference fields"""
        indexes = []

        for field_name, field_def in entity.fields.items():
            if field_def.is_composite():
                # GIN indexes for JSONB fields
                composite_ddl = self.composite_mapper.map_field(field_def)
                index_sql = self.composite_mapper.generate_gin_index(
                    entity.schema, safe_table_name(entity.name), composite_ddl
                )
                indexes.append(index_sql)

            elif field_def.is_reference():
                # B-tree indexes for foreign key fields
                fk_ddl = self.fk_generator.map_field(field_def)
                index_sql = self.fk_generator.generate_index(
                    entity.schema, safe_table_name(entity.name), fk_ddl
                )
                indexes.append(index_sql)

        return indexes

    def _generate_trinity_helper_functions(self, entity: EntityDefinition) -> list[str]:
        """Generate Trinity Pattern helper functions for the entity"""
        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"

        functions = []

        # Helper function: UUID -> INTEGER (pk) with tenant scoping
        functions.append(
            f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{entity_lower}_pk(p_id UUID, p_tenant_id UUID DEFAULT NULL)
RETURNS INTEGER AS $$
    SELECT pk_{entity_lower}
    FROM {table_name}
    WHERE id = p_id
    AND (p_tenant_id IS NULL OR tenant_id = p_tenant_id);
$$ LANGUAGE SQL STABLE;"""
        )

        # Helper function: INTEGER (pk) -> UUID (id)
        functions.append(
            f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{entity_lower}_id(p_pk INTEGER)
RETURNS UUID AS $$
    SELECT id
    FROM {table_name}
    WHERE pk_{entity_lower} = p_pk;
$$ LANGUAGE SQL STABLE;"""
        )

        # Helper function: INTEGER (pk) -> TEXT (identifier)
        # All Trinity Pattern entities have an identifier field
        functions.append(
            f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{entity_lower}_identifier(p_pk INTEGER)
RETURNS TEXT AS $$
    SELECT identifier
    FROM {table_name}
    WHERE pk_{entity_lower} = p_pk;
$$ LANGUAGE SQL STABLE;"""
        )

        return functions

    def _generate_trinity_fields(self, entity: EntityDefinition) -> list[str]:
        """Generate Trinity Pattern fields for the entity"""
        entity_lower = entity.name.lower()

        fields = []

        # Primary key
        fields.append(f"pk_{entity_lower} INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY")

        # Public ID (UUID)
        fields.append("id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE")

        # Tenant ID (UUID) - every table has this per Trinity pattern
        fields.append("tenant_id UUID NOT NULL")

        # Human-readable identifier
        fields.append("identifier TEXT UNIQUE")

        return fields

    def _generate_trinity_indexes(self, entity: EntityDefinition) -> list[str]:
        """Generate Trinity Pattern indexes for the entity"""
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
        entity_lower = entity.name.lower()

        indexes = []

        # Composite index on (id, tenant_id) for efficient tenant-scoped lookups
        indexes.append(f"CREATE INDEX idx_{entity_lower}_id_tenant ON {table_name}(id, tenant_id);")

        # Index on tenant_id for tenant filtering
        indexes.append(f"CREATE INDEX idx_{entity_lower}_tenant ON {table_name}(tenant_id);")

        return indexes
