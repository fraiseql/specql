"""
Prisma Schema Parser - Parse Prisma schema files to SpecQL entities

Supports:
- Model definitions
- Field types and attributes
- Relations (one-to-one, one-to-many, many-to-many)
- Enums
- Indexes and constraints
"""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class PrismaField:
    """Represents a Prisma model field"""

    name: str
    type: str
    is_optional: bool = False
    is_list: bool = False
    is_relation: bool = False
    related_entity: Optional[str] = None
    unique: bool = False
    indexed: bool = False
    default_value: Optional[str] = None
    column_name: Optional[str] = None
    enum_values: Optional[List[str]] = None


@dataclass
class PrismaEntity:
    """Represents a Prisma model"""

    name: str
    table_name: str
    fields: List[PrismaField]
    indexes: List[List[str]]
    unique_constraints: List[List[str]]


class PrismaSchemaParser:
    """Parser for Prisma schema files"""

    def __init__(self):
        self.enums = {}  # Store enum definitions

    def parse_schema(self, schema: str) -> List[PrismaEntity]:
        """Parse Prisma schema to entities"""
        entities = []

        # First, extract enums
        self._extract_enums(schema)

        # Extract models
        model_pattern = r"model\s+(\w+)\s*\{([^}]+)\}"

        for match in re.finditer(model_pattern, schema, re.DOTALL):
            model_name = match.group(1)
            model_body = match.group(2)

            # Extract fields
            fields = self._extract_fields(model_body)

            # Extract table name from @@map
            table_name = self._extract_table_name(model_body, model_name)

            # Extract indexes
            indexes = self._extract_indexes(model_body)
            unique_constraints = self._extract_unique_constraints(model_body)

            entities.append(
                PrismaEntity(
                    name=model_name,
                    table_name=table_name,
                    fields=fields,
                    indexes=indexes,
                    unique_constraints=unique_constraints,
                )
            )

        return entities

    def _extract_enums(self, schema: str):
        """Extract enum definitions"""
        enum_pattern = r"enum\s+(\w+)\s*\{([^}]+)\}"

        for match in re.finditer(enum_pattern, schema, re.DOTALL):
            enum_name = match.group(1)
            enum_body = match.group(2)

            # Extract enum values
            values = [
                line.strip()
                for line in enum_body.split("\n")
                if line.strip() and not line.strip().startswith("//")
            ]

            self.enums[enum_name] = values

    def _extract_fields(self, model_body: str) -> List[PrismaField]:
        """Extract fields from model body"""
        fields = []

        # Pattern: fieldName Type @attributes
        field_pattern = r"(\w+)\s+([\w\[\]?]+)\s*(@[^\n]*)?"

        for line in model_body.split("\n"):
            line = line.strip()

            # Skip block-level attributes (@@) and comments
            if line.startswith("@@") or line.startswith("//") or not line:
                continue

            match = re.match(field_pattern, line)
            if not match:
                continue

            field_name = match.group(1)
            field_type_raw = match.group(2)
            attributes_str = match.group(3) or ""

            # Parse type
            is_optional = field_type_raw.endswith("?")
            is_list = field_type_raw.endswith("[]")
            base_type = field_type_raw.rstrip("?[]")

            # Check if relation
            is_relation = base_type[0].isupper() and base_type not in [
                "String",
                "Int",
                "DateTime",
                "Boolean",
            ]

            # Map Prisma type to SpecQL type
            specql_type = self._map_prisma_type(base_type)

            # Parse attributes
            unique = "@unique" in attributes_str
            indexed = "@index" in attributes_str or "@unique" in attributes_str

            # Extract default value
            default_value = None
            default_match = re.search(r"@default\(([^)]+)\)", attributes_str)
            if default_match:
                default_value = default_match.group(1).strip('"')

            # Extract column name from @map
            column_name = None
            map_match = re.search(r'@map\("([^"]+)"\)', attributes_str)
            if map_match:
                column_name = map_match.group(1)

            # Check if enum
            enum_values = None
            if base_type in self.enums:
                enum_values = self.enums[base_type]
                specql_type = "enum"

            fields.append(
                PrismaField(
                    name=field_name,
                    type=specql_type,
                    is_optional=is_optional,
                    is_list=is_list,
                    is_relation=is_relation,
                    related_entity=base_type if is_relation else None,
                    unique=unique,
                    indexed=indexed,
                    default_value=default_value,
                    column_name=column_name,
                    enum_values=enum_values,
                )
            )

        return fields

    def _map_prisma_type(self, prisma_type: str) -> str:
        """Map Prisma types to SpecQL types"""
        type_map = {
            "String": "text",
            "Int": "integer",
            "BigInt": "bigint",
            "Float": "decimal",
            "Boolean": "boolean",
            "DateTime": "timestamp",
            "Json": "jsonb",
            "Bytes": "bytea",
        }
        return type_map.get(prisma_type, "text")

    def _extract_table_name(self, model_body: str, default_name: str) -> str:
        """Extract table name from @@map or use default"""
        map_match = re.search(r'@@map\("([^"]+)"\)', model_body)
        if map_match:
            return map_match.group(1)

        # Convert PascalCase to snake_case and pluralize
        snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", default_name).lower()
        return snake_case + "s"

    def _extract_indexes(self, model_body: str) -> List[List[str]]:
        """Extract @@index declarations"""
        indexes = []
        index_pattern = r"@@index\(\[([^\]]+)\]\)"

        for match in re.finditer(index_pattern, model_body):
            fields = [f.strip() for f in match.group(1).split(",")]
            indexes.append(fields)

        return indexes

    def _extract_unique_constraints(self, model_body: str) -> List[List[str]]:
        """Extract @@unique declarations"""
        constraints = []
        unique_pattern = r"@@unique\(\[([^\]]+)\]\)"

        for match in re.finditer(unique_pattern, model_body):
            fields = [f.strip() for f in match.group(1).split(",")]
            constraints.append(fields)

        return constraints
