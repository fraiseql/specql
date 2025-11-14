"""
Prisma schema parser for SpecQL reverse engineering.

Parses schema.prisma files to extract models, fields, and relationships.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.core.universal_ast import UniversalEntity, UniversalField, FieldType

logger = logging.getLogger(__name__)


class PrismaParser:
    """Parser for Prisma schema files."""

    def __init__(self):
        self.type_mapping = {
            'String': FieldType.TEXT,
            'Int': FieldType.INTEGER,
            'BigInt': FieldType.INTEGER,
            'Float': FieldType.RICH,  # Use RICH for decimal types
            'Decimal': FieldType.RICH,
            'Boolean': FieldType.BOOLEAN,
            'DateTime': FieldType.DATETIME,
            'Json': FieldType.RICH,  # JSON as rich type
            'Bytes': FieldType.RICH,  # Binary as rich type
        }

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
        model_pattern = r'model\s+(\w+)\s*\{([^}]+)\}'
        matches = re.findall(model_pattern, content, re.DOTALL)

        for model_name, model_content in matches:
            try:
                entity = self._parse_model(model_name, model_content)
                if entity:
                    entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to parse model {model_name}: {e}")
                continue

        return entities

    def _parse_model(self, model_name: str, model_content: str) -> Optional[UniversalEntity]:
        """Parse a single Prisma model."""
        fields = []

        # Split into lines and parse each field
        lines = [line.strip() for line in model_content.split('\n') if line.strip()]

        for line in lines:
            if line.startswith('//') or line.startswith('@@'):
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
            description=f"Prisma model {model_name}"
        )

        return entity

    def _parse_field_line(self, line: str) -> Optional[UniversalField]:
        """Parse a single field line from a Prisma model."""
        # Remove trailing comma and split
        line = line.rstrip(',')
        parts = line.split()

        if len(parts) < 2:
            return None

        field_name = parts[0]
        field_type = parts[1]

        # Check for optional field
        is_optional = field_type.endswith('?')
        if is_optional:
            field_type = field_type[:-1]

        # Check for array type
        is_array = field_type.startswith('[') and field_type.endswith(']')
        if is_array:
            field_type = field_type[1:-1]

        # Check for relationship (references another model)
        if '@relation' in line:
            # This is a foreign key field
            specql_type = FieldType.REFERENCE
        else:
            # Map Prisma type to SpecQL FieldType
            specql_type = self._map_prisma_type(field_type, is_array)

        # Check for @unique
        is_unique = '@unique' in line

        field = UniversalField(
            name=field_name,
            type=specql_type,
            required=not is_optional,
            unique=is_unique
        )

        # Set reference target for foreign keys
        if '@relation' in line and 'references:' in line:
            ref_match = re.search(r'references:\s*\[([^\]]+)\]', line)
            if ref_match:
                referenced_fields = [f.strip() for f in ref_match.group(1).split(',')]
                if referenced_fields:
                    # For now, assume the field references the same model name
                    # In a full implementation, we'd need to parse the relation args more carefully
                    field.references = field_type

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
        return self.parse_schema_file(schema_path)</content>
