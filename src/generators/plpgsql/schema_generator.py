"""
PL/pgSQL Schema Generator

Generates PostgreSQL DDL from UniversalEntity objects.
Used for round-trip testing to validate parser accuracy.
"""

from typing import List
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class SchemaGenerator:
    """Generates PostgreSQL DDL from UniversalEntity objects"""

    def generate_schema(self, entities: List[UniversalEntity]) -> str:
        """
        Generate complete DDL for all entities

        Args:
            entities: List of UniversalEntity objects

        Returns:
            Complete DDL string
        """
        ddl_parts = []

        # Group entities by schema
        schemas = {}
        for entity in entities:
            if entity.schema not in schemas:
                schemas[entity.schema] = []
            schemas[entity.schema].append(entity)

        # Generate DDL for each schema
        for schema_name, schema_entities in schemas.items():
            if schema_name != "public":
                ddl_parts.append(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")

            # Sort entities by dependency (tables without FKs first)
            sorted_entities = self._sort_entities_by_dependency(schema_entities)

            for entity in sorted_entities:
                ddl_parts.append(self.generate_table(entity))

        return "\n\n".join(ddl_parts)

    def generate_table(self, entity: UniversalEntity) -> str:
        """
        Generate CREATE TABLE DDL for a single entity

        Args:
            entity: UniversalEntity to generate DDL for

        Returns:
            CREATE TABLE DDL
        """
        table_name = self._get_table_name(entity)
        full_table_name = (
            f"{entity.schema}.{table_name}" if entity.schema != "public" else table_name
        )

        # Start CREATE TABLE
        ddl = f"CREATE TABLE {full_table_name} ("

        # Collect all DDL parts
        ddl_parts = []

        # Add all fields
        for field in entity.fields:
            ddl_parts.append(self._generate_column_ddl(field))

        # Add primary key constraint
        pk_field = next((f for f in entity.fields if f.name.startswith("pk_")), None)
        if pk_field:
            ddl_parts.append(f"    PRIMARY KEY ({pk_field.name})")

        # Add unique constraints
        unique_fields = [
            f for f in entity.fields if f.unique and not f.name.startswith("pk_")
        ]
        if unique_fields:
            for field in unique_fields:
                ddl_parts.append(f"    UNIQUE ({field.name})")

        # Add foreign key constraints
        fk_fields = [f for f in entity.fields if f.references]
        for field in fk_fields:
            if field.references:
                referenced_table = self._get_table_name_from_reference(field.references)
                ddl_parts.append(
                    f"    FOREIGN KEY ({field.name}) REFERENCES {referenced_table}(pk_{referenced_table.replace('tb_', '')})"
                )

        # Join all parts
        ddl += "\n" + ",\n".join(ddl_parts) + "\n);"

        return ddl

    def _generate_column_ddl(self, field: UniversalField) -> str:
        """
        Generate column DDL

        Args:
            field: UniversalField to generate DDL for

        Returns:
            Column DDL string
        """
        # Use original PostgreSQL type if available (for round-trip testing)
        if field.postgres_type:
            type_str = field.postgres_type
            # Add length for character varying
            if type_str == "character varying" and field.character_maximum_length:
                type_str = f"character varying({field.character_maximum_length})"
        else:
            type_str = self._field_type_to_sql(field.type)

        # Detect SERIAL pattern: INTEGER with nextval default
        if (
            field.type == FieldType.INTEGER
            and field.default
            and "nextval(" in field.default
            and "_seq" in field.default
        ):
            type_str = "SERIAL"

        nullable = " NOT NULL" if field.required else ""
        default = (
            f" DEFAULT {field.default}"
            if field.default and type_str != "SERIAL"
            else ""
        )

        return f"    {field.name} {type_str}{nullable}{default}"

    def _field_type_to_sql(self, field_type: FieldType) -> str:
        """
        Convert FieldType to PostgreSQL type

        Args:
            field_type: SpecQL FieldType

        Returns:
            PostgreSQL type string
        """
        type_map = {
            FieldType.TEXT: "TEXT",
            FieldType.INTEGER: "INTEGER",
            FieldType.BOOLEAN: "BOOLEAN",
            FieldType.DATETIME: "TIMESTAMP WITH TIME ZONE",
            FieldType.LIST: "TEXT[]",  # Simplified
            FieldType.REFERENCE: "INTEGER",  # Simplified
            FieldType.ENUM: "TEXT",  # Simplified
            FieldType.RICH: "TEXT",  # Simplified
        }

        return type_map.get(field_type, "TEXT")

    def _get_table_name(self, entity: UniversalEntity) -> str:
        """
        Get table name for entity

        Args:
            entity: UniversalEntity

        Returns:
            Table name (with tb_ prefix)
        """
        # Convert PascalCase to snake_case
        import re

        snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", entity.name).lower()
        return f"tb_{snake_case}"

    def _get_table_name_from_reference(self, reference: str) -> str:
        """
        Get table name from reference string

        Args:
            reference: Reference string (e.g., "User", "tb_user")

        Returns:
            Table name with tb_ prefix
        """
        # If already has tb_ prefix, return as-is
        if reference.startswith("tb_"):
            return reference

        # Otherwise add tb_ prefix
        return f"tb_{reference.lower()}"

    def _sort_entities_by_dependency(
        self, entities: List[UniversalEntity]
    ) -> List[UniversalEntity]:
        """
        Sort entities so tables without foreign key dependencies are created first.

        This is a simple topological sort that handles most cases.
        """
        # Build dependency graph
        entity_map = {entity.name: entity for entity in entities}
        dependencies = {}

        for entity in entities:
            deps = set()
            for field in entity.fields:
                if field.references:
                    # Convert reference back to table name for dependency
                    ref_table = self._get_table_name_from_reference(field.references)
                    ref_entity_name = ref_table.replace("tb_", "").capitalize()
                    if ref_entity_name in entity_map:
                        deps.add(ref_entity_name)
            dependencies[entity.name] = deps

        # Simple topological sort (handles acyclic graphs)
        sorted_entities = []
        visited = set()
        visiting = set()

        def visit(entity_name):
            if entity_name in visiting:
                # Circular dependency - just add it anyway
                return
            if entity_name in visited:
                return

            visiting.add(entity_name)

            # Visit dependencies first
            for dep in dependencies[entity_name]:
                visit(dep)

            visiting.remove(entity_name)
            visited.add(entity_name)
            sorted_entities.append(entity_map[entity_name])

        # Visit all entities
        for entity_name in entity_map:
            if entity_name not in visited:
                visit(entity_name)

        return sorted_entities
