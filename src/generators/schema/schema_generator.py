"""
Schema Generator

Generates complete PostgreSQL DDL from Team A's AST:
- Trinity Pattern fields
- Business fields (scalars, composites, references)
- Audit fields
- Indexes
- Constraints
"""

from typing import List
from src.core.ast_models import EntityDefinition, FieldDefinition, FieldTier
from src.generators.schema.composite_type_mapper import CompositeTypeMapper
from src.generators.schema.foreign_key_generator import ForeignKeyGenerator


class SchemaGenerator:
    """Generates PostgreSQL schema DDL from EntityDefinition AST"""

    def __init__(self):
        self.composite_mapper = CompositeTypeMapper()
        self.fk_generator = ForeignKeyGenerator()

    def generate_table(self, entity: EntityDefinition) -> str:
        """
        Generate complete CREATE TABLE statement

        Args:
            entity: EntityDefinition from Team A

        Returns:
            Complete DDL including table, indexes, comments, and helper functions
        """
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

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

        # Business fields
        ddl_parts.append("    -- Business fields")
        for field_name, field_def in entity.fields.items():
            field_ddl = self._generate_field_ddl(field_def)
            ddl_parts.append(f"    {field_ddl},")
        ddl_parts.append("")

        # Remove last comma
        ddl_parts[-1] = ddl_parts[-1].rstrip(",")

        ddl_parts.append(");")
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

        # Indexes for composites and foreign keys
        indexes = self._generate_indexes(entity)
        if indexes:
            ddl_parts.append("-- Indexes")
            ddl_parts.extend(indexes)
            ddl_parts.append("")

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

    def _generate_validation_functions(self, entity: EntityDefinition) -> List[str]:
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

    def _generate_indexes(self, entity: EntityDefinition) -> List[str]:
        """Generate indexes for composite and reference fields"""
        indexes = []

        for field_name, field_def in entity.fields.items():
            if field_def.is_composite():
                # GIN indexes for JSONB fields
                composite_ddl = self.composite_mapper.map_field(field_def)
                index_sql = self.composite_mapper.generate_gin_index(
                    entity.schema, f"tb_{entity.name.lower()}", composite_ddl
                )
                indexes.append(index_sql)

            elif field_def.is_reference():
                # B-tree indexes for foreign key fields
                fk_ddl = self.fk_generator.map_field(field_def)
                index_sql = self.fk_generator.generate_index(
                    entity.schema, f"tb_{entity.name.lower()}", fk_ddl
                )
                indexes.append(index_sql)

        return indexes

    def _generate_trinity_helper_functions(self, entity: EntityDefinition) -> List[str]:
        """Generate Trinity Pattern helper functions for the entity"""
        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"

        functions = []

        # Helper function: UUID -> INTEGER (pk) with tenant scoping
        functions.append(f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{entity_lower}_pk(p_id UUID, p_tenant_id UUID DEFAULT NULL)
RETURNS INTEGER AS $$
    SELECT pk_{entity_lower}
    FROM {table_name}
    WHERE id = p_id
    AND (p_tenant_id IS NULL OR tenant_id = p_tenant_id);
$$ LANGUAGE SQL STABLE;""")

        # Helper function: INTEGER (pk) -> UUID (id)
        functions.append(f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{entity_lower}_id(p_pk INTEGER)
RETURNS UUID AS $$
    SELECT id
    FROM {table_name}
    WHERE pk_{entity_lower} = p_pk;
$$ LANGUAGE SQL STABLE;""")

        # Helper function: INTEGER (pk) -> TEXT (identifier)
        # All Trinity Pattern entities have an identifier field
        functions.append(f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{entity_lower}_identifier(p_pk INTEGER)
RETURNS TEXT AS $$
    SELECT identifier
    FROM {table_name}
    WHERE pk_{entity_lower} = p_pk;
$$ LANGUAGE SQL STABLE;""")

        return functions

    def _generate_trinity_fields(self, entity: EntityDefinition) -> List[str]:
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

    def _generate_trinity_indexes(self, entity: EntityDefinition) -> List[str]:
        """Generate Trinity Pattern indexes for the entity"""
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        entity_lower = entity.name.lower()

        indexes = []

        # Composite index on (id, tenant_id) for efficient tenant-scoped lookups
        indexes.append(f"CREATE INDEX idx_{entity_lower}_id_tenant ON {table_name}(id, tenant_id);")

        # Index on tenant_id for tenant filtering
        indexes.append(f"CREATE INDEX idx_{entity_lower}_tenant ON {table_name}(tenant_id);")

        return indexes
