"""
Prisma schema generator for TypeScript/Prisma projects.

Generates schema.prisma files from UniversalEntity objects.
"""

from typing import List
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class PrismaSchemaGenerator:
    """Generates Prisma schema.prisma content from UniversalEntity."""

    def __init__(self):
        self.type_mapping = {
            FieldType.TEXT: "String",
            FieldType.INTEGER: "Int",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "DateTime",
            FieldType.RICH: "Json",  # Use Json for rich/complex types
        }

    def generate(self, entities: List[UniversalEntity]) -> str:
        """
        Generate complete Prisma schema from list of entities.

        Args:
            entities: List of UniversalEntity objects

        Returns:
            Complete schema.prisma file content
        """
        parts = []

        # Add schema header
        parts.append(self._generate_header())
        parts.append("")

        # Generate enums first
        for entity in entities:
            enum_definitions = self._generate_enums(entity)
            if enum_definitions:
                parts.extend(enum_definitions)
                parts.append("")

        # Generate models
        for entity in entities:
            model_definition = self._generate_model(entity)
            parts.append(model_definition)
            parts.append("")

        return "\n".join(parts)

    def _generate_header(self) -> str:
        """Generate Prisma schema header with datasource and generator."""
        return """generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}"""

    def _generate_enums(self, entity: UniversalEntity) -> List[str]:
        """Generate enum declarations for entity."""
        enums = []

        for field in entity.fields:
            if field.type == FieldType.ENUM and field.enum_values:
                enum_name = f"{field.name.capitalize()}Status"
                enum_def = f"enum {enum_name} {{"
                enum_def += "\n  " + "\n  ".join(field.enum_values)
                enum_def += "\n}"
                enums.append(enum_def)

        return enums

    def _generate_model(self, entity: UniversalEntity) -> str:
        """Generate a single Prisma model."""
        lines = [f"model {entity.name} {{"]

        # Add fields
        for field in entity.fields:
            field_line = self._generate_field(field, entity)
            if field_line:
                lines.append(f"  {field_line}")

        lines.append("}")

        return "\n".join(lines)

    def _generate_field(self, field: UniversalField, entity: UniversalEntity) -> str:
        """Generate a single Prisma field declaration."""
        # Skip relation navigation fields for now (they're auto-generated)
        if field.type == FieldType.REFERENCE:
            # Generate foreign key field
            fk_field_name = f"{field.name}Id"
            fk_type = "Int"
            optional = "" if field.required else "?"

            # Add foreign key field
            fk_line = f"{fk_field_name:<15} {fk_type}{optional}"

            # Add relation field
            ref_type = field.references or field.name.capitalize()
            relation_line = f"{field.name:<15} {ref_type}{optional}  @relation(fields: [{fk_field_name}], references: [id])"

            return f"{fk_line}\n  {relation_line}"

        # Regular field
        field_name = field.name

        # Map field type
        if field.type == FieldType.ENUM:
            field_type = f"{field.name.capitalize()}Status"
        elif field.type == FieldType.LIST:
            # Array type
            base_type = self.type_mapping.get(FieldType.TEXT, "String")
            field_type = f"{base_type}[]"
        else:
            field_type = self.type_mapping.get(field.type, "String")

        # Optional marker
        optional = "" if field.required else "?"

        # Attributes
        attributes = []

        # ID field
        if field_name == "id":
            attributes.append("@id @default(autoincrement())")

        # Unique constraint
        if field.unique:
            attributes.append("@unique")

        # Default values
        if field.default is not None:
            if isinstance(field.default, bool):
                attributes.append(f"@default({str(field.default).lower()})")
            elif isinstance(field.default, str):
                attributes.append(f'@default("{field.default}")')

        # Special handling for timestamp fields
        if field_name == "createdAt" and field.type == FieldType.DATETIME:
            attributes.append("@default(now())")
        elif field_name == "updatedAt" and field.type == FieldType.DATETIME:
            attributes.append("@updatedAt")

        # Soft delete field
        if field_name == "deletedAt":
            optional = "?"

        # Build field line
        field_line = f"{field_name:<15} {field_type}{optional}"

        if attributes:
            field_line += "  " + " ".join(attributes)

        return field_line

    def write_schema(self, entities: List[UniversalEntity], output_path: str):
        """
        Generate and write Prisma schema to file.

        Args:
            entities: List of UniversalEntity objects
            output_path: Path to output schema.prisma file
        """
        from pathlib import Path

        schema_content = self.generate(entities)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(schema_content)
