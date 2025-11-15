"""
Prisma schema parser for SpecQL reverse engineering.

Parses schema.prisma files to extract models, fields, and relationships.
"""

import re
import logging
from pathlib import Path
from typing import List, Optional

from src.core.universal_ast import UniversalEntity, UniversalField, FieldType

logger = logging.getLogger(__name__)


class PrismaParser:
    """Parser for Prisma schema files."""

    def __init__(self):
        self.type_mapping = {
            "String": FieldType.TEXT,
            "Int": FieldType.INTEGER,
            "BigInt": FieldType.INTEGER,
            "Float": FieldType.RICH,  # Use RICH for decimal types
            "Decimal": FieldType.RICH,
            "Boolean": FieldType.BOOLEAN,
            "DateTime": FieldType.DATETIME,
            "Json": FieldType.RICH,  # JSON as rich type
            "Bytes": FieldType.RICH,  # Binary as rich type
        }

        # Pre-compile regex patterns for better performance
        self.model_pattern = re.compile(r"model\s+(\w+)\s*\{([^}]+)\}", re.DOTALL)

    def parse_schema_file(self, schema_path: str) -> List[UniversalEntity]:
        """
        Parse a Prisma schema.prisma file.

        Args:
            schema_path: Path to the schema.prisma file

        Returns:
            List of UniversalEntity objects
        """
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        content = schema_file.read_text()
        return self.parse_schema_content(content)

    def parse_schema_content(self, content: str) -> List[UniversalEntity]:
        """
        Parse Prisma schema content.

        Args:
            content: The schema.prisma file content

        Returns:
            List of UniversalEntity objects
        """
        entities = []

        # Split content into model blocks
        matches = self.model_pattern.findall(content)

        for model_name, model_content in matches:
            try:
                entity = self._parse_model(model_name, model_content)
                if entity:
                    entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to parse model {model_name}: {e}")
                continue

        return entities

    def _parse_model(
        self, model_name: str, model_content: str
    ) -> Optional[UniversalEntity]:
        """Parse a single Prisma model."""
        fields = []

        # Split into lines and parse each field
        lines = [line.strip() for line in model_content.split("\n") if line.strip()]

        for line in lines:
            if line.startswith("//") or line.startswith("@@"):
                continue  # Skip comments and model-level attributes

            field = self._parse_field_line(line)
            if field:
                fields.append(field)

        if not fields:
            return None

        # Create UniversalEntity
        entity = UniversalEntity(
            name=model_name,
            schema="public",
            fields=fields,
            actions=[],  # No actions from Prisma schema
            description=f"Prisma model {model_name}",
        )

        return entity

    def _parse_field_line(self, line: str) -> Optional[UniversalField]:
        """Parse a single field line from a Prisma model."""
        # Remove trailing comma and split
        line = line.rstrip(",")
        parts = line.split()

        if len(parts) < 2:
            return None

        field_name = parts[0]
        field_type = parts[1]

        # Handle relation fields (they have @relation)
        # These are like: author User @relation(...)
        is_relation_field = "@relation" in line

        # Check for optional field
        is_optional = field_type.endswith("?")
        if is_optional:
            field_type = field_type[:-1]

        # Check for array type (String[] syntax)
        is_array = field_type.endswith("[]")
        if is_array:
            field_type = field_type[:-2]  # Remove []

        # Determine field type
        if is_relation_field:
            # Relation navigation fields
            specql_type = FieldType.REFERENCE
        elif field_name.endswith("Id") and field_type in ["Int", "String"]:
            # Foreign key fields
            specql_type = FieldType.REFERENCE
        else:
            # Regular fields
            specql_type = self._map_prisma_type(field_type, is_array)

        # Check for @unique
        is_unique = "@unique" in line

        field = UniversalField(
            name=field_name,
            type=specql_type,
            required=not is_optional,
            unique=is_unique,
        )

        # Set references for relation fields
        if is_relation_field:
            # For relation fields like "author User @relation(...)", the type is the referenced model
            field.references = field_type
        elif field_name.endswith("Id") and field_type in ["Int", "String"]:
            # For foreign key fields, infer the model name
            potential_model = field_name[:-2]
            if potential_model:
                field.references = potential_model

        return field

    def _map_prisma_type(self, prisma_type: str, is_array: bool) -> FieldType:
        """Map Prisma type to SpecQL FieldType."""
        base_type = self.type_mapping.get(prisma_type, FieldType.TEXT)

        if is_array:
            return FieldType.LIST

        return base_type

    def parse_project(self, schema_path: str) -> List[UniversalEntity]:
        """
        Parse a complete Prisma project.

        Args:
            schema_path: Path to the schema.prisma file

        Returns:
            List of UniversalEntity objects
        """
        return self.parse_schema_file(schema_path)
