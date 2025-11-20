"""
Prisma Schema Parser - Parse Prisma schema files to SpecQL entities

Supports:
- Model definitions
- Field types and attributes
- Relations (one-to-one, one-to-many, many-to-many)
- Enums
- Indexes and constraints

Uses tree-sitter for robust AST-based parsing.
"""

import re
from dataclasses import dataclass

# Import tree-sitter parser with dependency check
from core.dependencies import TREE_SITTER

if TREE_SITTER.available:
    try:
        from .tree_sitter_prisma_parser import (
            PrismaField as TSPrismaField,
        )
        from .tree_sitter_prisma_parser import (
            PrismaModel as TSPrismaModel,
        )
        from .tree_sitter_prisma_parser import (
            TreeSitterPrismaParser,
        )
    except ImportError:
        # For testing without package structure
        from tree_sitter_prisma_parser import (
            PrismaField as TSPrismaField,
        )
        from tree_sitter_prisma_parser import (
            PrismaModel as TSPrismaModel,
        )
        from tree_sitter_prisma_parser import (
            TreeSitterPrismaParser,
        )


@dataclass
class PrismaField:
    """Represents a Prisma model field"""

    name: str
    type: str
    is_optional: bool = False
    is_list: bool = False
    is_relation: bool = False
    related_entity: str | None = None
    unique: bool = False
    indexed: bool = False
    default_value: str | None = None
    column_name: str | None = None
    enum_values: list[str] | None = None


@dataclass
class PrismaEntity:
    """Represents a Prisma model"""

    name: str
    table_name: str
    fields: list[PrismaField]
    indexes: list[list[str]]
    unique_constraints: list[list[str]]


class PrismaSchemaParser:
    """Parser for Prisma schema files using tree-sitter"""

    def __init__(self):
        self.ts_parser = TreeSitterPrismaParser()
        self.enums = {}  # Store enum definitions for compatibility

    def parse_schema(self, schema: str) -> list[PrismaEntity]:
        """
        Parse Prisma schema to entities using tree-sitter AST parsing.

        This replaces the previous regex-based parsing with grammar-validated
        AST traversal for robust handling of all Prisma syntax.
        """
        entities = []

        # Parse with tree-sitter
        ast = self.ts_parser.parse(schema)

        # Extract enums first (for compatibility with existing field mapping)
        enums = self.ts_parser.extract_enums(ast)
        self.enums = {enum.name: enum.values for enum in enums}

        # Extract models
        models = self.ts_parser.extract_models(ast)

        for model in models:
            entity = self._convert_model_to_entity(model)
            entities.append(entity)

        return entities

    def _convert_model_to_entity(self, model: TSPrismaModel) -> PrismaEntity:
        """Convert tree-sitter PrismaModel to legacy PrismaEntity format."""
        # Convert fields
        fields = [self._convert_field_to_legacy(field) for field in model.fields]

        # Convert indexes and unique constraints
        indexes = [idx["fields"] for idx in model.indexes]
        unique_constraints = [uc["fields"] for uc in model.unique_constraints]

        # Extract table name (look for @@map in the future, for now use default)
        table_name = self._extract_table_name_from_model(model)

        return PrismaEntity(
            name=model.name,
            table_name=table_name,
            fields=fields,
            indexes=indexes,
            unique_constraints=unique_constraints,
        )

    def _convert_field_to_legacy(self, field: TSPrismaField) -> PrismaField:
        """Convert tree-sitter PrismaField to legacy PrismaField format."""
        # Map type
        specql_type = self._map_prisma_type(field.type)

        # Determine if relation
        is_relation = field.type[0].isupper() and field.type not in [
            "String",
            "Int",
            "BigInt",
            "Float",
            "Boolean",
            "DateTime",
            "Json",
            "Bytes",
        ]

        # Get enum values if this is an enum type
        enum_values = None
        if field.type in self.enums:
            enum_values = self.enums[field.type]
            specql_type = "enum"

        # Extract column name from @map attribute
        column_name = None
        for attr in field.attributes:
            if "@map(" in attr:
                import re

                match = re.search(r'@map\(["\']([^"\']+)["\']', attr)
                if match:
                    column_name = match.group(1)

        return PrismaField(
            name=field.name,
            type=specql_type,
            is_optional=not field.is_required,
            is_list=field.is_list,
            is_relation=is_relation,
            related_entity=field.type if is_relation else None,
            unique=field.is_unique,
            indexed=field.is_id or field.is_unique or field.has_default,  # Approximation
            default_value=field.default_value,
            column_name=column_name,
            enum_values=enum_values,
        )

    def _extract_table_name_from_model(self, model: TSPrismaModel) -> str:
        """Extract table name from model (@@map) or use default."""
        if model.table_name:
            return model.table_name

        # Default: Convert PascalCase to snake_case and pluralize
        name = model.name
        snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return snake_case + "s"

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
