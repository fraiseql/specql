"""
SeaORM Parser - Extract entities and queries from SeaORM code

Supports:
- Entity model detection (DeriveEntityModel)
- Field attributes (primary_key, unique, nullable, etc.)
- Relations (has_one, has_many, belongs_to)
- CRUD operations (find, insert, update, delete)
"""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class SeaORMField:
    """Represents a SeaORM model field"""

    name: str
    type_name: str
    is_primary_key: bool = False
    is_unique: bool = False
    is_indexed: bool = False
    is_nullable: bool = False
    auto_increment: bool = False
    default_value: Optional[str] = None
    column_type: Optional[str] = None


@dataclass
class SeaORMRelation:
    """Represents a SeaORM relation"""

    name: str
    relation_type: str  # has_one, has_many, belongs_to
    target_entity: str


@dataclass
class SeaORMEntity:
    """Represents a SeaORM entity model"""

    name: str
    table_name: str
    fields: List[SeaORMField]
    primary_key: Optional[str]
    relations: List[SeaORMRelation]

    @property
    def has_relations(self) -> bool:
        return len(self.relations) > 0


@dataclass
class SeaORMQuery:
    """Represents a SeaORM query"""

    operation: str  # find, find_by_id, insert, update, delete
    entity: str
    has_filter: bool = False
    has_order: bool = False
    is_async: bool = True


class SeaORMParser:
    """Parser for SeaORM entities and queries"""

    def extract_entities(self, code: str) -> List[SeaORMEntity]:
        """Extract SeaORM entity models from code"""
        entities = []

        # Find DeriveEntityModel structs
        entity_pattern = r'#\[derive\([^]]*DeriveEntityModel[^]]*\)\]\s*#\[sea_orm\(table_name\s*=\s*"([^"]+)"\)\]\s*pub struct Model\s*\{([^}]+)\}'

        for match in re.finditer(entity_pattern, code, re.DOTALL):
            table_name = match.group(1)
            fields_text = match.group(2)

            # Infer entity name from table name (contacts -> Contact)
            entity_name = self._table_to_entity_name(table_name)

            # Extract fields
            fields = self._extract_fields(fields_text)

            # Find primary key
            primary_key = next((f.name for f in fields if f.is_primary_key), None)

            # Extract relations
            relations = self._extract_relations(code)

            entities.append(
                SeaORMEntity(
                    name=entity_name,
                    table_name=table_name,
                    fields=fields,
                    primary_key=primary_key,
                    relations=relations,
                )
            )

        return entities

    def _extract_fields(self, fields_text: str) -> List[SeaORMField]:
        """Extract fields with their attributes"""
        fields = []

        # Pattern: field with optional attributes
        field_pattern = r"(?:#\[sea_orm\(([^]]+)\)\])?\s*pub\s+(\w+):\s*([^,\n]+)"

        for match in re.finditer(field_pattern, fields_text):
            attributes_str = match.group(1) or ""
            field_name = match.group(2)
            field_type = match.group(3).strip().rstrip(",")

            # Parse attributes
            attributes = self._parse_field_attributes(attributes_str)

            # Check if nullable (Option<T>)
            is_nullable = "Option<" in field_type

            fields.append(
                SeaORMField(
                    name=field_name,
                    type_name=field_type,
                    is_primary_key=attributes.get("primary_key", False),
                    is_unique=attributes.get("unique", False),
                    is_indexed=attributes.get("indexed", False),
                    is_nullable=is_nullable,
                    auto_increment=attributes.get("auto_increment", False),
                    default_value=attributes.get("default_value"),
                    column_type=attributes.get("column_type"),
                )
            )

        return fields

    def _parse_field_attributes(self, attr_str: str) -> dict:
        """Parse SeaORM field attributes"""
        attributes = {}

        if not attr_str:
            return attributes

        # Boolean attributes
        if "primary_key" in attr_str:
            attributes["primary_key"] = True
        if "unique" in attr_str:
            attributes["unique"] = True
        if "indexed" in attr_str:
            attributes["indexed"] = True
        if "auto_increment" in attr_str:
            attributes["auto_increment"] = True

        # Value attributes
        if "default_value" in attr_str:
            default_match = re.search(r'default_value\s*=\s*"([^"]+)"', attr_str)
            if default_match:
                attributes["default_value"] = default_match.group(1)

        if "column_type" in attr_str:
            type_match = re.search(r'column_type\s*=\s*"([^"]+)"', attr_str)
            if type_match:
                attributes["column_type"] = type_match.group(1)

        return attributes

    def _extract_relations(self, code: str) -> List[SeaORMRelation]:
        """Extract relations from DeriveRelation enum"""
        relations = []

        # Pattern: #[sea_orm(has_many = "super::companies::Entity")]
        relation_pattern = r'#\[sea_orm\((has_many|has_one|belongs_to)\s*=\s*"([^"]+)"\)\]\s*(\w+)'

        for match in re.finditer(relation_pattern, code):
            relation_type = match.group(1)
            target_path = match.group(2)
            relation_name = match.group(3)

            # Extract entity name from path (super::companies::Entity -> Company)
            target_entity = self._extract_entity_from_path(target_path)

            relations.append(
                SeaORMRelation(
                    name=relation_name, relation_type=relation_type, target_entity=target_entity
                )
            )

        return relations

    def _table_to_entity_name(self, table_name: str) -> str:
        """Convert table name to entity name (contacts -> Contact)"""
        # Remove plural 's'
        singular = table_name.rstrip("s")
        # Capitalize
        return singular.capitalize()

    def _extract_entity_from_path(self, path: str) -> str:
        """Extract entity name from path (super::companies::Entity -> Company)"""
        parts = path.split("::")
        if len(parts) >= 2:
            # companies -> Company
            return parts[-2].rstrip("s").capitalize()
        return path

    def extract_queries(self, code: str) -> List[SeaORMQuery]:
        """Extract SeaORM queries from code"""
        queries = []

        # Find operations
        find_patterns = [
            (r"(\w+)::find_by_id\(", "find_by_id"),
            (r"(\w+)::find\(\)", "find"),
        ]

        for pattern, operation in find_patterns:
            for match in re.finditer(pattern, code):
                entity = match.group(1)
                has_filter = ".filter(" in code[match.end() : match.end() + 200]
                has_order = ".order_by" in code[match.end() : match.end() + 200]

                queries.append(
                    SeaORMQuery(
                        operation=operation,
                        entity=entity,
                        has_filter=has_filter,
                        has_order=has_order,
                    )
                )

        # Insert operations
        insert_pattern = r"(\w+)::insert\("
        for match in re.finditer(insert_pattern, code):
            entity = match.group(1)
            queries.append(SeaORMQuery(operation="insert", entity=entity))

        # Update operations
        update_patterns = [
            r"(\w+)::update_many\(",
            r"\.update\(db\)",
        ]

        for pattern in update_patterns:
            for match in re.finditer(pattern, code):
                if pattern.startswith("(\\w+)"):
                    entity = match.group(1)
                else:
                    # Infer from context
                    entity = self._infer_entity_from_context(code, match.start())

                queries.append(SeaORMQuery(operation="update", entity=entity or "Unknown"))

        # Delete operations
        delete_patterns = [
            (r"(\w+)::delete_by_id\(", "delete_by_id"),
            (r"(\w+)::delete_many\(", "delete_many"),
        ]

        for pattern, operation in delete_patterns:
            for match in re.finditer(pattern, code):
                entity = match.group(1)
                queries.append(SeaORMQuery(operation=operation, entity=entity))

        return queries

    def _infer_entity_from_context(self, code: str, position: int) -> Optional[str]:
        """Infer entity name from surrounding code"""
        # Look backwards for entity reference
        context = code[max(0, position - 200) : position]
        entity_match = re.search(r"(\w+)::find", context)
        if entity_match:
            return entity_match.group(1)
        return None
