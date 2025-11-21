# Team A: CQRS Table Views Implementation Plan

**Team**: Parser & AST
**Impact**: MEDIUM (new table_views configuration parsing)
**Timeline**: Week 2-3 (3-4 days)
**Status**: 🟡 MEDIUM PRIORITY - Extends Team A base work

---

## 📋 Overview

Team A must extend the SpecQL parser to support **table_views configuration** for CQRS read-side optimization.

**New Capabilities**:
1. ✅ Parse `table_views` configuration block
2. ✅ Parse `include_relations` (explicit field selection)
3. ✅ Parse `extra_filter_columns` (performance optimization)
4. ✅ Parse `mode: auto/force/disable`
5. ✅ Add TableViewConfig to Entity AST

**Total Effort**: 3-4 days

---

## 🎯 Phase 1: AST Models for Table Views (Day 1)

### **Objective**: Define AST classes for table_views configuration

### **1.1: TableViewConfig Model**

**File**: `src/core/ast_models.py`

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

class TableViewMode(Enum):
    """Mode for table view generation."""
    AUTO = "auto"      # Generate if has foreign keys
    FORCE = "force"    # Always generate
    DISABLE = "disable"  # Never generate

@dataclass
class IncludeRelation:
    """Specification for including a related entity in table view."""
    entity_name: str
    fields: List[str]  # Which fields to include from related entity
    include_relations: List['IncludeRelation'] = field(default_factory=list)  # Nested

    def __post_init__(self):
        """Validate field list."""
        if not self.fields:
            raise ValueError(f"include_relations.{self.entity_name} must specify fields")

        # Special case: '*' means all fields
        if self.fields == ['*']:
            pass  # All fields, resolved during generation
        elif not all(isinstance(f, str) for f in self.fields):
            raise ValueError(f"Fields must be strings in {self.entity_name}")

@dataclass
class ExtraFilterColumn:
    """Extra filter column specification."""
    name: str
    source: Optional[str] = None  # e.g., "author.name" for nested extraction
    type: Optional[str] = None    # Explicit type override
    index_type: str = "btree"     # btree | gin | gin_trgm | gist

    @classmethod
    def from_string(cls, name: str) -> 'ExtraFilterColumn':
        """Create from simple string (e.g., 'rating')."""
        return cls(name=name)

    @classmethod
    def from_dict(cls, name: str, config: dict) -> 'ExtraFilterColumn':
        """Create from dict config (e.g., {source: 'author.name', type: 'text'})."""
        return cls(
            name=name,
            source=config.get('source'),
            type=config.get('type'),
            index_type=config.get('index', 'btree')
        )

@dataclass
class TableViewConfig:
    """Configuration for table view (tv_) generation."""

    # Generation mode
    mode: TableViewMode = TableViewMode.AUTO

    # Explicit relation inclusion
    include_relations: List[IncludeRelation] = field(default_factory=list)

    # Performance-optimized filter columns
    extra_filter_columns: List[ExtraFilterColumn] = field(default_factory=list)

    # Refresh strategy (always explicit for now)
    refresh: str = "explicit"

    @property
    def should_generate(self) -> bool:
        """Check if table view should be generated (resolved during generation)."""
        # This will be resolved by Team B based on mode and entity characteristics
        return self.mode != TableViewMode.DISABLE

    @property
    def has_explicit_relations(self) -> bool:
        """Check if explicit relations are specified."""
        return len(self.include_relations) > 0

# Extend EntityAST
@dataclass
class EntityAST:
    """Entity AST with table_views support."""
    name: str
    schema: str
    fields: List[FieldDefinition]
    actions: List[ActionDefinition]
    hierarchical: bool = False
    metadata_split: bool = False

    # NEW: Table views configuration
    table_views: Optional[TableViewConfig] = None

    @property
    def has_foreign_keys(self) -> bool:
        """Check if entity has any foreign key fields."""
        return any(
            field.field_type.startswith('ref(')
            for field in self.fields
        )

    @property
    def should_generate_table_view(self) -> bool:
        """Determine if table view should be generated."""
        if self.table_views is None:
            # Default: auto mode
            return self.has_foreign_keys

        if self.table_views.mode == TableViewMode.DISABLE:
            return False
        elif self.table_views.mode == TableViewMode.FORCE:
            return True
        else:  # AUTO
            return self.has_foreign_keys
```

---

### **1.2: Test AST Models**

**File**: `tests/unit/core/test_table_view_ast.py`

```python
import pytest
from src.core.ast_models import (
    TableViewMode, TableViewConfig, IncludeRelation,
    ExtraFilterColumn, EntityAST, FieldDefinition
)

class TestTableViewConfig:
    """Test TableViewConfig model."""

    def test_default_mode_is_auto(self):
        """Test default mode is AUTO."""
        config = TableViewConfig()
        assert config.mode == TableViewMode.AUTO
        assert config.refresh == "explicit"

    def test_include_relation_requires_fields(self):
        """Test IncludeRelation requires fields."""
        with pytest.raises(ValueError):
            IncludeRelation(entity_name="User", fields=[])

    def test_include_relation_with_wildcard(self):
        """Test wildcard '*' for all fields."""
        rel = IncludeRelation(entity_name="User", fields=['*'])
        assert rel.fields == ['*']

    def test_nested_include_relations(self):
        """Test nested include_relations."""
        rel = IncludeRelation(
            entity_name="Book",
            fields=["title", "isbn"],
            include_relations=[
                IncludeRelation(
                    entity_name="Publisher",
                    fields=["name", "country"]
                )
            ]
        )
        assert len(rel.include_relations) == 1
        assert rel.include_relations[0].entity_name == "Publisher"

    def test_extra_filter_column_from_string(self):
        """Test creating filter column from string."""
        col = ExtraFilterColumn.from_string("rating")
        assert col.name == "rating"
        assert col.source is None
        assert col.index_type == "btree"

    def test_extra_filter_column_from_dict(self):
        """Test creating filter column from dict."""
        col = ExtraFilterColumn.from_dict(
            "author_name",
            {"source": "author.name", "type": "text", "index": "gin_trgm"}
        )
        assert col.name == "author_name"
        assert col.source == "author.name"
        assert col.type == "text"
        assert col.index_type == "gin_trgm"

class TestEntityASTWithTableViews:
    """Test EntityAST with table_views."""

    def test_entity_without_table_views_config(self):
        """Test entity with no table_views (defaults to auto)."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[
                FieldDefinition(name="author", field_type="ref(User)")
            ],
            actions=[],
            table_views=None  # No config
        )

        assert entity.has_foreign_keys is True
        assert entity.should_generate_table_view is True  # Auto mode

    def test_entity_with_force_mode(self):
        """Test entity with force mode (no foreign keys)."""
        entity = EntityAST(
            name="AuditLog",
            schema="core",
            fields=[
                FieldDefinition(name="message", field_type="text")
            ],
            actions=[],
            table_views=TableViewConfig(mode=TableViewMode.FORCE)
        )

        assert entity.has_foreign_keys is False
        assert entity.should_generate_table_view is True  # Forced

    def test_entity_with_disable_mode(self):
        """Test entity with disable mode (has foreign keys but disabled)."""
        entity = EntityAST(
            name="SessionToken",
            schema="auth",
            fields=[
                FieldDefinition(name="user", field_type="ref(User)")
            ],
            actions=[],
            table_views=TableViewConfig(mode=TableViewMode.DISABLE)
        )

        assert entity.has_foreign_keys is True
        assert entity.should_generate_table_view is False  # Disabled
```

---

## 🎯 Phase 2: Parser Implementation (Day 2-3)

### **Objective**: Parse table_views configuration from YAML

### **2.1: Parse table_views Block**

**File**: `src/core/specql_parser.py`

```python
from .ast_models import (
    EntityAST, TableViewConfig, TableViewMode,
    IncludeRelation, ExtraFilterColumn
)

class SpecQLParser:
    def parse_entity(self, yaml_content: dict) -> EntityAST:
        """Parse entity with table_views support."""

        # ... existing parsing (name, schema, fields, actions)

        # NEW: Parse table_views
        table_views_config = None
        if 'table_views' in yaml_content:
            table_views_config = self._parse_table_views(
                yaml_content['table_views'],
                entity_name
            )

        return EntityAST(
            name=entity_name,
            schema=schema,
            fields=fields,
            actions=actions,
            hierarchical=hierarchical,
            table_views=table_views_config
        )

    def _parse_table_views(
        self,
        config: dict,
        entity_name: str
    ) -> TableViewConfig:
        """Parse table_views configuration block."""

        # Parse mode
        mode_str = config.get('mode', 'auto')
        try:
            mode = TableViewMode(mode_str)
        except ValueError:
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"Invalid table_views.mode: '{mode_str}'. "
                        f"Must be: auto, force, or disable"
            )

        # Parse include_relations
        include_relations = []
        if 'include_relations' in config:
            for rel_config in config['include_relations']:
                rel = self._parse_include_relation(rel_config, entity_name)
                include_relations.append(rel)

        # Parse extra_filter_columns
        extra_filter_columns = []
        if 'extra_filter_columns' in config:
            for col_config in config['extra_filter_columns']:
                col = self._parse_extra_filter_column(col_config, entity_name)
                extra_filter_columns.append(col)

        # Parse refresh (always explicit for now)
        refresh = config.get('refresh', 'explicit')
        if refresh != 'explicit':
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"Only 'explicit' refresh strategy is supported (got '{refresh}')"
            )

        return TableViewConfig(
            mode=mode,
            include_relations=include_relations,
            extra_filter_columns=extra_filter_columns,
            refresh=refresh
        )

    def _parse_include_relation(
        self,
        config: dict,
        entity_name: str
    ) -> IncludeRelation:
        """Parse include_relations entry."""

        # Format: - entity_name: { fields: [...], include_relations: [...] }
        if not isinstance(config, dict) or len(config) != 1:
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"Invalid include_relations format. Expected single-key dict."
            )

        relation_entity = list(config.keys())[0]
        relation_config = config[relation_entity]

        # Parse fields (required)
        if 'fields' not in relation_config:
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"include_relations.{relation_entity} must specify 'fields'"
            )

        fields = relation_config['fields']
        if not isinstance(fields, list):
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"include_relations.{relation_entity}.fields must be a list"
            )

        # Parse nested include_relations (recursive)
        nested_relations = []
        if 'include_relations' in relation_config:
            for nested_config in relation_config['include_relations']:
                nested = self._parse_include_relation(nested_config, entity_name)
                nested_relations.append(nested)

        return IncludeRelation(
            entity_name=relation_entity,
            fields=fields,
            include_relations=nested_relations
        )

    def _parse_extra_filter_column(
        self,
        config,
        entity_name: str
    ) -> ExtraFilterColumn:
        """Parse extra_filter_columns entry."""

        # Simple string format
        if isinstance(config, str):
            return ExtraFilterColumn.from_string(config)

        # Dict format with options
        elif isinstance(config, dict):
            if len(config) != 1:
                raise SpecQLValidationError(
                    entity=entity_name,
                    message=f"Invalid extra_filter_columns format"
                )

            col_name = list(config.keys())[0]
            col_config = config[col_name]

            return ExtraFilterColumn.from_dict(col_name, col_config)

        else:
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"extra_filter_columns must be string or dict"
            )
```

---

### **2.2: Test Parser**

**File**: `tests/unit/core/test_table_views_parsing.py`

```python
import pytest
from src.core.specql_parser import SpecQLParser
from src.core.exceptions import SpecQLValidationError
from src.core.ast_models import TableViewMode

class TestTableViewsParsing:
    """Test parsing table_views configuration."""

    def setup_method(self):
        self.parser = SpecQLParser()

    def test_parse_minimal_table_views(self):
        """Test parsing minimal table_views config."""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          rating: integer
          author: ref(User)

        table_views:
          mode: auto
        """

        entity = self.parser.parse_yaml(yaml_content)
        assert entity.table_views is not None
        assert entity.table_views.mode == TableViewMode.AUTO

    def test_parse_include_relations(self):
        """Test parsing include_relations."""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)
          book: ref(Book)

        table_views:
          include_relations:
            - author:
                fields: [name, email]
            - book:
                fields: [title, isbn]
        """

        entity = self.parser.parse_yaml(yaml_content)
        assert len(entity.table_views.include_relations) == 2

        author_rel = entity.table_views.include_relations[0]
        assert author_rel.entity_name == "author"
        assert author_rel.fields == ["name", "email"]

        book_rel = entity.table_views.include_relations[1]
        assert book_rel.entity_name == "book"
        assert book_rel.fields == ["title", "isbn"]

    def test_parse_nested_include_relations(self):
        """Test parsing nested include_relations."""
        yaml_content = """
        entity: Review
        fields:
          book: ref(Book)

        table_views:
          include_relations:
            - book:
                fields: [title, isbn]
                include_relations:
                  - publisher:
                      fields: [name, country]
        """

        entity = self.parser.parse_yaml(yaml_content)
        book_rel = entity.table_views.include_relations[0]
        assert len(book_rel.include_relations) == 1

        publisher_rel = book_rel.include_relations[0]
        assert publisher_rel.entity_name == "publisher"
        assert publisher_rel.fields == ["name", "country"]

    def test_parse_extra_filter_columns_simple(self):
        """Test parsing simple extra_filter_columns."""
        yaml_content = """
        entity: Review
        fields:
          rating: integer
          created_at: timestamp

        table_views:
          extra_filter_columns:
            - rating
            - created_at
        """

        entity = self.parser.parse_yaml(yaml_content)
        assert len(entity.table_views.extra_filter_columns) == 2
        assert entity.table_views.extra_filter_columns[0].name == "rating"
        assert entity.table_views.extra_filter_columns[1].name == "created_at"

    def test_parse_extra_filter_columns_advanced(self):
        """Test parsing advanced extra_filter_columns."""
        yaml_content = """
        entity: Review
        fields:
          author: ref(User)

        table_views:
          extra_filter_columns:
            - rating
            - author_name:
                source: author.name
                type: text
                index: gin_trgm
        """

        entity = self.parser.parse_yaml(yaml_content)
        assert len(entity.table_views.extra_filter_columns) == 2

        # Simple column
        assert entity.table_views.extra_filter_columns[0].name == "rating"

        # Advanced column
        col = entity.table_views.extra_filter_columns[1]
        assert col.name == "author_name"
        assert col.source == "author.name"
        assert col.type == "text"
        assert col.index_type == "gin_trgm"

    def test_parse_force_mode(self):
        """Test parsing force mode."""
        yaml_content = """
        entity: AuditLog
        fields:
          message: text

        table_views:
          mode: force
        """

        entity = self.parser.parse_yaml(yaml_content)
        assert entity.table_views.mode == TableViewMode.FORCE
        assert entity.should_generate_table_view is True

    def test_parse_disable_mode(self):
        """Test parsing disable mode."""
        yaml_content = """
        entity: SessionToken
        fields:
          user: ref(User)

        table_views:
          mode: disable
        """

        entity = self.parser.parse_yaml(yaml_content)
        assert entity.table_views.mode == TableViewMode.DISABLE
        assert entity.should_generate_table_view is False

    def test_invalid_mode(self):
        """Test invalid mode raises error."""
        yaml_content = """
        entity: Review
        table_views:
          mode: invalid_mode
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse_yaml(yaml_content)

        assert "Invalid table_views.mode" in str(exc_info.value)

    def test_include_relations_requires_fields(self):
        """Test include_relations requires fields."""
        yaml_content = """
        entity: Review
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - author: {}  # Missing fields!
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse_yaml(yaml_content)

        assert "must specify 'fields'" in str(exc_info.value)

    def test_entity_without_table_views_block(self):
        """Test entity without table_views block (defaults)."""
        yaml_content = """
        entity: Review
        fields:
          author: ref(User)
        """

        entity = self.parser.parse_yaml(yaml_content)
        assert entity.table_views is None
        assert entity.should_generate_table_view is True  # Auto mode default
```

---

## 🎯 Phase 3: Integration & Documentation (Day 4)

### **Objective**: Integrate with existing parser and document usage

### **3.1: Integration Tests**

**File**: `tests/integration/test_table_views_end_to_end.py`

```python
import pytest
from src.core.specql_parser import SpecQLParser

class TestTableViewsEndToEnd:
    """End-to-end tests for table_views."""

    def test_complete_review_example(self):
        """Test complete Review entity with table_views."""
        yaml_content = """
        entity: Review
        schema: library

        fields:
          rating: integer
          comment: text
          author: ref(User)
          book: ref(Book)
          created_at: timestamp

        table_views:
          include_relations:
            - author:
                fields: [name, email, avatarUrl]

            - book:
                fields: [title, isbn, publishedYear]
                include_relations:
                  - publisher:
                      fields: [name, country]

          extra_filter_columns:
            - rating
            - created_at
        """

        parser = SpecQLParser()
        entity = parser.parse_yaml(yaml_content)

        # Verify entity structure
        assert entity.name == "Review"
        assert entity.schema == "library"
        assert entity.should_generate_table_view is True

        # Verify table_views config
        tv = entity.table_views
        assert tv.mode == TableViewMode.AUTO
        assert len(tv.include_relations) == 2
        assert len(tv.extra_filter_columns) == 2

        # Verify author relation
        author = tv.include_relations[0]
        assert author.entity_name == "author"
        assert set(author.fields) == {"name", "email", "avatarUrl"}

        # Verify book relation (with nested publisher)
        book = tv.include_relations[1]
        assert book.entity_name == "book"
        assert set(book.fields) == {"title", "isbn", "publishedYear"}
        assert len(book.include_relations) == 1

        publisher = book.include_relations[0]
        assert publisher.entity_name == "publisher"
        assert set(publisher.fields) == {"name", "country"}

        # Verify filter columns
        assert tv.extra_filter_columns[0].name == "rating"
        assert tv.extra_filter_columns[1].name == "created_at"
```

---

### **3.2: Documentation**

**File**: `docs/guides/TABLE_VIEWS_CONFIGURATION.md`

```markdown
# Table Views Configuration Guide

## Overview

Table views (`tv_` tables) provide read-optimized denormalized data for FraiseQL.

## Basic Usage

### Auto Mode (Default)

No configuration needed - generates tv_ if entity has foreign keys:

\`\`\`yaml
entity: Review
fields:
  author: ref(User)
  book: ref(Book)

# Automatically generates tv_review
\`\`\`

### Explicit Field Selection

Control which fields to include from related entities:

\`\`\`yaml
entity: Review
fields:
  author: ref(User)
  book: ref(Book)

table_views:
  include_relations:
    - author:
        fields: [name, email]  # Only these fields

    - book:
        fields: [title, isbn]
\`\`\`

### Performance Optimization

Add extra filter columns for high-volume queries:

\`\`\`yaml
table_views:
  extra_filter_columns:
    - rating       # Frequently filtered
    - created_at   # Date range queries
\`\`\`

### Force Generation

Generate tv_ even without foreign keys:

\`\`\`yaml
entity: AuditLog
fields:
  message: text

table_views:
  mode: force  # Generate tv_auditlog
\`\`\`

### Disable Generation

Prevent tv_ generation for write-heavy tables:

\`\`\`yaml
entity: SessionToken
fields:
  user: ref(User)

table_views:
  mode: disable  # No tv_sessiontoken
\`\`\`

## Advanced Features

### Nested Relations

\`\`\`yaml
table_views:
  include_relations:
    - book:
        fields: [title, isbn]
        include_relations:
          - publisher:
              fields: [name, country]
\`\`\`

### Nested Field Extraction

\`\`\`yaml
table_views:
  extra_filter_columns:
    - author_name:
        source: author.name
        type: text
        index: gin_trgm  # For ILIKE queries
\`\`\`
```

---

## 📊 Summary: Team A Deliverables

### **Files to Create**

| File | Purpose | Lines |
|------|---------|-------|
| `src/core/ast_models.py` | TableViewConfig, IncludeRelation models | +150 |
| `src/core/specql_parser.py` | Parse table_views block | +200 |
| `tests/unit/core/test_table_view_ast.py` | AST model tests | 150 |
| `tests/unit/core/test_table_views_parsing.py` | Parser tests | 300 |
| `tests/integration/test_table_views_end_to_end.py` | Integration tests | 100 |
| `docs/guides/TABLE_VIEWS_CONFIGURATION.md` | User documentation | 200 |

**Total**: ~1,100 lines of code + documentation

---

### **Timeline**

- **Day 1**: AST models + model tests
- **Day 2**: Parser implementation (parse_table_views)
- **Day 3**: Parser tests + edge cases
- **Day 4**: Integration tests + documentation

**Total**: 4 days

---

## ✅ Acceptance Criteria

- [ ] TableViewConfig AST model created
- [ ] IncludeRelation AST model created (supports nesting)
- [ ] ExtraFilterColumn AST model created (simple + advanced)
- [ ] Parser handles table_views.mode (auto/force/disable)
- [ ] Parser handles include_relations (with nesting)
- [ ] Parser handles extra_filter_columns (simple + dict format)
- [ ] Parser validates required fields
- [ ] Parser provides helpful error messages
- [ ] All unit tests pass (100% coverage)
- [ ] Integration tests pass
- [ ] Documentation complete

---

## 🔗 Dependencies

**Depends On**:
- Phase 1 (Reserved field validation) - Must complete first

**Blocks**:
- Team B Phase 9 (tv_ generation) - Needs TableViewConfig AST
- Team C (tv_ refresh in mutations) - Needs AST structure
- Team D (tv_ annotations) - Needs AST structure

---

**Status**: 🟡 READY TO START (after Phase 1)
**Priority**: MEDIUM (enables CQRS)
**Effort**: 4 days
**Start**: Week 2-3
