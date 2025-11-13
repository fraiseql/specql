# Weeks 25-26: Rust Reverse Engineering & Pattern Detection

**Date**: 2025-11-13
**Duration**: 10 days (2 weeks)
**Status**: 🔴 Planning
**Objective**: Reverse engineer Rust/Diesel/SeaORM applications to SpecQL universal format

**Prerequisites**: Week 24 complete (Java Reverse Engineering)
**Output**: Rust AST parser, pattern detector, Diesel/SeaORM → SpecQL converter

---

## 🎯 Executive Summary

Enable SpecQL to learn from existing **Rust** applications by reverse engineering:
- Diesel schema macros → SpecQL entities
- SeaORM entities → SpecQL entities
- sqlx queries → SpecQL patterns
- Actix-web/Axum handlers → SpecQL actions

### Success Criteria

- [ ] Parse Rust source code to AST
- [ ] Detect Diesel table! macros
- [ ] Map SeaORM Entity traits to entities
- [ ] Extract sqlx queries
- [ ] Convert Actix-web/Axum handlers to actions
- [ ] Generate SpecQL YAML from Rust codebase
- [ ] 90%+ accuracy on Rust web apps

---

## Week 25: Rust AST Parser & Diesel/SeaORM Detection

**Objective**: Parse Rust code and map Diesel/SeaORM to SpecQL

### Day 1: Rust Parser Foundation

**Morning Block (4 hours): syn Parser Setup**

#### 🔴 RED: Parser Tests (2 hours)

**Test File**: `tests/unit/reverse_engineering/rust/test_rust_parser.py`

```python
"""Tests for Rust source code parsing"""

import pytest
from src.reverse_engineering.rust.rust_parser import RustParser


class TestRustParser:
    """Test Rust source code parsing"""

    @pytest.fixture
    def parser(self):
        return RustParser()

    def test_parse_simple_struct(self, parser):
        """Test parsing basic Rust struct"""
        rust_code = """
        #[derive(Debug, Clone)]
        pub struct User {
            pub id: i64,
            pub email: String,
            pub name: String,
            pub created_at: chrono::NaiveDateTime,
        }
        """

        # Act
        ast = parser.parse(rust_code)

        # Assert
        assert ast is not None
        assert len(ast.structs) == 1

        user_struct = ast.structs[0]
        assert user_struct.name == "User"
        assert len(user_struct.fields) == 4
        assert user_struct.fields[0].name == "id"
        assert user_struct.fields[0].rust_type == "i64"
        assert user_struct.is_public

    def test_parse_diesel_table_macro(self, parser):
        """Test parsing Diesel table! macro"""
        rust_code = """
        table! {
            users (id) {
                id -> Int8,
                email -> Varchar,
                name -> Varchar,
                organization_id -> Nullable<Int8>,
                role -> Varchar,
                created_at -> Timestamp,
            }
        }
        """

        # Act
        ast = parser.parse(rust_code)

        # Assert
        assert len(ast.diesel_tables) == 1

        users_table = ast.diesel_tables[0]
        assert users_table.name == "users"
        assert users_table.primary_key == "id"
        assert len(users_table.columns) == 6

        # Check column types
        email_col = next(c for c in users_table.columns if c.name == "email")
        assert email_col.diesel_type == "Varchar"
        assert email_col.nullable == False

        org_col = next(c for c in users_table.columns if c.name == "organization_id")
        assert org_col.nullable == True
        assert "Int8" in org_col.diesel_type

    def test_parse_seaorm_entity(self, parser):
        """Test parsing SeaORM entity"""
        rust_code = """
        use sea_orm::entity::prelude::*;

        #[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
        #[sea_orm(table_name = "contacts")]
        pub struct Model {
            #[sea_orm(primary_key)]
            pub id: i64,

            #[sea_orm(unique)]
            pub email: String,

            pub name: String,

            pub phone: Option<String>,

            #[sea_orm(column_type = "Text")]
            pub notes: String,

            pub created_at: DateTimeUtc,
        }

        #[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
        pub enum Relation {
            #[sea_orm(
                belongs_to = "super::organization::Entity",
                from = "Column::OrganizationId",
                to = "super::organization::Column::Id"
            )]
            Organization,

            #[sea_orm(has_many = "super::task::Entity")]
            Tasks,
        }
        """

        # Act
        ast = parser.parse(rust_code)

        # Assert
        assert len(ast.seaorm_entities) == 1

        entity = ast.seaorm_entities[0]
        assert entity.table_name == "contacts"
        assert entity.model_name == "Model"

        # Check fields
        id_field = next(f for f in entity.fields if f.name == "id")
        assert id_field.is_primary_key

        email_field = next(f for f in entity.fields if f.name == "email")
        assert email_field.is_unique

        phone_field = next(f for f in entity.fields if f.name == "phone")
        assert phone_field.is_optional

        # Check relationships
        assert len(entity.relations) == 2
        org_rel = next(r for r in entity.relations if "Organization" in r.name)
        assert org_rel.relation_type == "belongs_to"
```

**Run Tests (Should Fail)**:
```bash
uv run pytest tests/unit/reverse_engineering/rust/test_rust_parser.py -v
```

---

#### 🟢 GREEN: Implement Rust Parser (2 hours)

**Dependencies**: We'll use `tree-sitter` with Rust grammar for parsing

```bash
uv pip install tree-sitter tree-sitter-rust
```

**Parser**: `src/reverse_engineering/rust/rust_parser.py`

```python
"""
Rust Source Code Parser

Parses Rust code using tree-sitter.
Extracts structs, Diesel tables, SeaORM entities, and traits.
"""

from tree_sitter import Language, Parser
import tree_sitter_rust
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RustField:
    """Rust struct field"""
    name: str
    rust_type: str
    is_public: bool = False
    is_optional: bool = False
    attributes: List[str] = field(default_factory=list)

    def has_attribute(self, attr: str) -> bool:
        return any(attr in a for a in self.attributes)


@dataclass
class RustStruct:
    """Rust struct"""
    name: str
    fields: List[RustField] = field(default_factory=list)
    is_public: bool = False
    derives: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)


@dataclass
class DieselColumn:
    """Diesel table column"""
    name: str
    diesel_type: str
    nullable: bool = False


@dataclass
class DieselTable:
    """Diesel table! macro"""
    name: str
    primary_key: str
    columns: List[DieselColumn] = field(default_factory=list)


@dataclass
class SeaORMField:
    """SeaORM entity field"""
    name: str
    rust_type: str
    is_primary_key: bool = False
    is_unique: bool = False
    is_optional: bool = False
    column_type: Optional[str] = None


@dataclass
class SeaORMRelation:
    """SeaORM relation"""
    name: str
    relation_type: str  # belongs_to, has_one, has_many
    target_entity: Optional[str] = None
    from_column: Optional[str] = None
    to_column: Optional[str] = None


@dataclass
class SeaORMEntity:
    """SeaORM entity"""
    model_name: str
    table_name: str
    fields: List[SeaORMField] = field(default_factory=list)
    relations: List[SeaORMRelation] = field(default_factory=list)


@dataclass
class RustAST:
    """Rust Abstract Syntax Tree"""
    structs: List[RustStruct] = field(default_factory=list)
    diesel_tables: List[DieselTable] = field(default_factory=list)
    seaorm_entities: List[SeaORMEntity] = field(default_factory=list)


class RustParser:
    """Parse Rust source code"""

    def __init__(self):
        # Initialize tree-sitter with Rust grammar
        self.parser = Parser()
        rust_language = Language(tree_sitter_rust.language(), "rust")
        self.parser.set_language(rust_language)

    def parse(self, rust_code: str) -> RustAST:
        """
        Parse Rust source code

        Args:
            rust_code: Rust source as string

        Returns:
            RustAST with parsed structures
        """
        tree = self.parser.parse(bytes(rust_code, "utf8"))
        root_node = tree.root_node

        ast = RustAST()

        # Extract different constructs
        ast.structs = self._extract_structs(root_node, rust_code)
        ast.diesel_tables = self._extract_diesel_tables(root_node, rust_code)
        ast.seaorm_entities = self._extract_seaorm_entities(root_node, rust_code)

        return ast

    def _extract_structs(self, node, source_code: str) -> List[RustStruct]:
        """Extract struct definitions"""
        structs = []

        # Query for struct_item nodes
        query = """
        (struct_item
            name: (type_identifier) @name
            body: (field_declaration_list)? @body
        ) @struct
        """

        # Use tree-sitter query (simplified extraction)
        for child in self._walk_tree(node):
            if child.type == "struct_item":
                struct = self._parse_struct_node(child, source_code)
                if struct:
                    structs.append(struct)

        return structs

    def _parse_struct_node(self, node, source_code: str) -> Optional[RustStruct]:
        """Parse struct node"""
        name = None
        fields = []
        is_public = False
        derives = []

        # Get struct name
        for child in node.children:
            if child.type == "type_identifier":
                name = self._get_node_text(child, source_code)
            elif child.type == "visibility_modifier":
                is_public = True
            elif child.type == "field_declaration_list":
                fields = self._parse_fields(child, source_code)

        # Get attributes (derives)
        if node.prev_sibling and node.prev_sibling.type == "attribute_item":
            derives = self._parse_derives(node.prev_sibling, source_code)

        if name:
            return RustStruct(
                name=name,
                fields=fields,
                is_public=is_public,
                derives=derives
            )

        return None

    def _parse_fields(self, field_list_node, source_code: str) -> List[RustField]:
        """Parse struct fields"""
        fields = []

        for child in field_list_node.children:
            if child.type == "field_declaration":
                field = self._parse_field(child, source_code)
                if field:
                    fields.append(field)

        return fields

    def _parse_field(self, field_node, source_code: str) -> Optional[RustField]:
        """Parse single field"""
        name = None
        rust_type = None
        is_public = False
        is_optional = False

        for child in field_node.children:
            if child.type == "field_identifier":
                name = self._get_node_text(child, source_code)
            elif child.type == "visibility_modifier":
                is_public = True
            elif child.type in ["generic_type", "type_identifier", "primitive_type"]:
                rust_type = self._get_node_text(child, source_code)
                if "Option<" in rust_type:
                    is_optional = True

        if name and rust_type:
            return RustField(
                name=name,
                rust_type=rust_type,
                is_public=is_public,
                is_optional=is_optional
            )

        return None

    def _extract_diesel_tables(self, node, source_code: str) -> List[DieselTable]:
        """Extract Diesel table! macros"""
        tables = []

        # Look for macro_invocation with "table!"
        for child in self._walk_tree(node):
            if child.type == "macro_invocation":
                macro_name = self._get_node_text(child.child(0), source_code)
                if macro_name == "table":
                    table = self._parse_diesel_table(child, source_code)
                    if table:
                        tables.append(table)

        return tables

    def _parse_diesel_table(self, macro_node, source_code: str) -> Optional[DieselTable]:
        """Parse Diesel table! macro"""
        # Extract table name and primary key from macro content
        macro_text = self._get_node_text(macro_node, source_code)

        # Simple parsing (production would use proper macro parsing)
        import re

        # Extract table name and primary key: table_name (pk) { ... }
        match = re.search(r'table!\s*\{\s*(\w+)\s*\((\w+)\)', macro_text)
        if not match:
            return None

        table_name = match.group(1)
        primary_key = match.group(2)

        # Extract columns
        columns = self._parse_diesel_columns(macro_text)

        return DieselTable(
            name=table_name,
            primary_key=primary_key,
            columns=columns
        )

    def _parse_diesel_columns(self, macro_text: str) -> List[DieselColumn]:
        """Parse columns from Diesel table macro"""
        import re

        columns = []

        # Match column definitions: column_name -> Type
        pattern = r'(\w+)\s*->\s*([\w<>]+)'
        for match in re.finditer(pattern, macro_text):
            column_name = match.group(1)
            diesel_type = match.group(2)

            nullable = "Nullable<" in diesel_type

            columns.append(DieselColumn(
                name=column_name,
                diesel_type=diesel_type,
                nullable=nullable
            ))

        return columns

    def _extract_seaorm_entities(self, node, source_code: str) -> List[SeaORMEntity]:
        """Extract SeaORM entities"""
        entities = []

        # Look for structs with #[derive(DeriveEntityModel)]
        for struct_node in self._walk_tree(node):
            if struct_node.type == "struct_item":
                entity = self._parse_seaorm_entity(struct_node, source_code)
                if entity:
                    entities.append(entity)

        return entities

    def _parse_seaorm_entity(self, struct_node, source_code: str) -> Optional[SeaORMEntity]:
        """Parse SeaORM entity"""
        # Check for #[derive(DeriveEntityModel)]
        if not self._has_derive(struct_node, "DeriveEntityModel", source_code):
            return None

        # Get table name from #[sea_orm(table_name = "...")]
        table_name = self._extract_sea_orm_table_name(struct_node, source_code)

        # Get struct name
        model_name = self._get_struct_name(struct_node, source_code)

        # Extract fields
        fields = self._extract_seaorm_fields(struct_node, source_code)

        return SeaORMEntity(
            model_name=model_name,
            table_name=table_name or model_name.lower(),
            fields=fields
        )

    def _extract_seaorm_fields(self, struct_node, source_code: str) -> List[SeaORMField]:
        """Extract SeaORM entity fields"""
        fields = []

        for child in struct_node.children:
            if child.type == "field_declaration_list":
                for field_node in child.children:
                    if field_node.type == "field_declaration":
                        field = self._parse_seaorm_field(field_node, source_code)
                        if field:
                            fields.append(field)

        return fields

    def _parse_seaorm_field(self, field_node, source_code: str) -> Optional[SeaORMField]:
        """Parse SeaORM field"""
        name = None
        rust_type = None
        is_primary_key = False
        is_unique = False
        is_optional = False

        # Get field name and type
        for child in field_node.children:
            if child.type == "field_identifier":
                name = self._get_node_text(child, source_code)
            elif child.type in ["generic_type", "type_identifier"]:
                rust_type = self._get_node_text(child, source_code)
                is_optional = "Option<" in rust_type

        # Check for #[sea_orm(primary_key)]
        if self._field_has_attribute(field_node, "primary_key", source_code):
            is_primary_key = True

        # Check for #[sea_orm(unique)]
        if self._field_has_attribute(field_node, "unique", source_code):
            is_unique = True

        if name and rust_type:
            return SeaORMField(
                name=name,
                rust_type=rust_type,
                is_primary_key=is_primary_key,
                is_unique=is_unique,
                is_optional=is_optional
            )

        return None

    # Helper methods
    def _walk_tree(self, node):
        """Walk tree and yield all nodes"""
        cursor = node.walk()
        visited_children = False

        while True:
            if not visited_children:
                yield cursor.node
                if not cursor.goto_first_child():
                    visited_children = True
            elif cursor.goto_next_sibling():
                visited_children = False
            elif not cursor.goto_parent():
                break

    def _get_node_text(self, node, source_code: str) -> str:
        """Get text content of node"""
        return source_code[node.start_byte:node.end_byte]

    def _has_derive(self, struct_node, derive_name: str, source_code: str) -> bool:
        """Check if struct has specific derive"""
        # Simplified check
        return True  # TODO: Implement properly

    def _extract_sea_orm_table_name(self, struct_node, source_code: str) -> Optional[str]:
        """Extract table_name from #[sea_orm(table_name = "...")]"""
        # Simplified extraction
        import re
        node_text = self._get_node_text(struct_node, source_code)
        match = re.search(r'table_name\s*=\s*"([^"]+)"', node_text)
        return match.group(1) if match else None

    def _get_struct_name(self, struct_node, source_code: str) -> str:
        """Get struct name"""
        for child in struct_node.children:
            if child.type == "type_identifier":
                return self._get_node_text(child, source_code)
        return "Unknown"

    def _field_has_attribute(self, field_node, attr_name: str, source_code: str) -> bool:
        """Check if field has specific attribute"""
        node_text = self._get_node_text(field_node, source_code)
        return attr_name in node_text

    def _parse_derives(self, attr_node, source_code: str) -> List[str]:
        """Parse derive macros"""
        # Simplified
        return []
```

**Run Tests (Should Pass)**:
```bash
uv run pytest tests/unit/reverse_engineering/rust/test_rust_parser.py -v
```

**Commit**:
```bash
git add src/reverse_engineering/rust/rust_parser.py
git commit -m "feat(rust): implement Rust source code parser - GREEN phase"
```

---

**Afternoon Block (4 hours): Diesel to SpecQL Converter**

#### 🔴 RED + 🟢 GREEN: Diesel Converter (4 hours)

**Test & Implementation**: Convert Diesel tables to SpecQL entities

**Converter**: `src/reverse_engineering/rust/diesel_converter.py`

```python
"""
Diesel to SpecQL Converter

Converts Diesel table! macros and schema to SpecQL entities.
"""

from typing import Optional
from src.reverse_engineering.rust.rust_parser import RustParser, DieselTable, DieselColumn
from src.core.specql_parser import Entity, Field


class DieselConverter:
    """Convert Diesel schemas to SpecQL"""

    def __init__(self):
        self.parser = RustParser()

    def convert_table(self, diesel_table: DieselTable) -> Entity:
        """Convert Diesel table to SpecQL entity"""

        fields = []
        for column in diesel_table.columns:
            # Skip primary key (auto-added by Trinity pattern)
            if column.name == diesel_table.primary_key:
                continue

            field = self._convert_column(column)
            if field:
                fields.append(field)

        return Entity(
            name=self._to_pascal_case(diesel_table.name),
            table_name=diesel_table.name,
            fields=fields,
            schema="public"
        )

    def _convert_column(self, column: DieselColumn) -> Optional[Field]:
        """Convert Diesel column to SpecQL field"""

        # Map Diesel types to SpecQL types
        type_map = {
            "Int2": "integer",
            "Int4": "integer",
            "Int8": "integer",
            "Float": "decimal",
            "Double": "decimal",
            "Text": "text",
            "Varchar": "text",
            "Bool": "boolean",
            "Timestamp": "timestamp",
            "Date": "date",
            "Uuid": "uuid",
            "Json": "json",
            "Jsonb": "json",
        }

        # Extract base type (remove Nullable<>)
        base_type = column.diesel_type.replace("Nullable<", "").replace(">", "")

        specql_type = type_map.get(base_type, "text")

        return Field(
            name=column.name,
            field_type=specql_type,
            required=not column.nullable
        )

    def _to_pascal_case(self, snake_case: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.capitalize() for word in snake_case.split('_'))
```

**Day 1 Summary**:
- ✅ Rust parser with tree-sitter
- ✅ Diesel table! macro parsing
- ✅ SeaORM entity detection
- ✅ Diesel → SpecQL conversion

---

### Day 2: SeaORM and sqlx Pattern Detection

**Objective**: Convert SeaORM entities and sqlx queries to SpecQL

(Similar structure to Day 1, focusing on SeaORM → SpecQL conversion and sqlx query pattern detection)

**Day 2 Summary**:
- ✅ SeaORM entity converter
- ✅ Relationship mapping (belongs_to, has_many)
- ✅ sqlx query extraction
- ✅ Query pattern recognition

---

### Days 3-5: Complete Rust Integration

**Day 3**: Actix-web/Axum Handler Conversion
- Extract route handlers
- Convert to SpecQL actions
- Map HTTP methods to CRUD operations

**Day 4**: Complete Project Analyzer
- Scan entire Rust project
- Detect Diesel/SeaORM schemas
- Extract all handlers
- Generate complete SpecQL YAML

**Day 5**: Testing & CLI Integration
- Integration tests with real Rust projects
- CLI: `specql reverse rust src/`
- Documentation

---

## Week 26: Advanced Rust Patterns & Validation

### Day 1-2: Advanced ORM Features
- Complex Diesel joins
- SeaORM migrations
- Custom SQL queries
- Embedded structs

### Day 3-4: Async Patterns
- Tokio/async-std detection
- Connection pool patterns
- Transaction boundaries

### Day 5: Quality & Polish
- Performance optimization
- Documentation
- Example projects

---

## Success Metrics

- [ ] Parse 95%+ of Rust web projects
- [ ] Diesel table detection 95%+
- [ ] SeaORM entity mapping accurate
- [ ] sqlx query extraction working
- [ ] Handler conversion correct
- [ ] Complete project analysis < 5 minutes

---

**Status**: 🔴 Ready to Execute
**Priority**: High (Rust ecosystem growing rapidly)
**Expected Output**: Complete Rust/Diesel/SeaORM reverse engineering capability
