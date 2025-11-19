# Team D: FraiseQL tv_ Annotations

**Team**: FraiseQL Metadata Generator
**Impact**: LOW (metadata annotations only)
**Timeline**: Week 7 (2-3 days)
**Status**: 🟢 LOW PRIORITY - Metadata layer for CQRS

---

## 📋 Overview

Team D must generate **FraiseQL metadata annotations** for `tv_` tables to enable auto-GraphQL discovery.

**Purpose**: Tell FraiseQL how to introspect tv_ tables and auto-generate GraphQL types from JSONB structure.

---

## 🎯 Objectives

1. ✅ Annotate tv_ tables with `@fraiseql:table`
2. ✅ Annotate filter columns with `@fraiseql:filter`
3. ✅ Annotate data column with `@fraiseql:jsonb expand=true`
4. ✅ Mark internal columns as `internal=true`

---

## 📊 FraiseQL Annotation Patterns

### **Pattern 1: Table Annotation**

```sql
-- Tell FraiseQL this is a table to introspect
COMMENT ON TABLE library.tv_review IS
  '@fraiseql:table source=materialized,refresh=explicit,primary=true,description=Read-optimized review with denormalized author and book data';
```

**Attributes**:
- `source=materialized` - This is a materialized table view
- `refresh=explicit` - Refreshed explicitly in mutations (not automatic)
- `primary=true` - This is the primary table for GraphQL (not tb_review)

---

### **Pattern 2: Filter Column Annotations**

```sql
-- UUID foreign key filters
COMMENT ON COLUMN library.tv_review.author_id IS
  '@fraiseql:filter type=UUID,relation=author,index=btree,performance=optimized,description=Filter by author';

COMMENT ON COLUMN library.tv_review.book_id IS
  '@fraiseql:filter type=UUID,relation=book,index=btree,performance=optimized,description=Filter by book';

-- Promoted scalar filters
COMMENT ON COLUMN library.tv_review.rating IS
  '@fraiseql:filter type=Int,index=btree,performance=optimized,description=Filter by rating (1-5)';

COMMENT ON COLUMN library.tv_review.created_at IS
  '@fraiseql:filter type=DateTime,index=btree,performance=optimized,description=Filter by creation date';
```

**Attributes**:
- `type` - GraphQL type (UUID, Int, String, DateTime, etc.)
- `relation` - Related entity name (for foreign keys)
- `index` - Index type (btree = fast, gin = slower)
- `performance=optimized` - This column is optimized for filtering
- `description` - Help text for GraphQL schema

---

### **Pattern 3: JSONB Data Column**

```sql
-- Main data column (FraiseQL extracts GraphQL types from this)
COMMENT ON COLUMN library.tv_review.data IS
  '@fraiseql:jsonb expand=true,description=Denormalized review data with nested author and book';
```

**Attributes**:
- `expand=true` - FraiseQL should introspect JSONB structure and generate GraphQL types
- FraiseQL will sample rows and discover nested structure:
  ```jsonb
  {
    "id": UUID,
    "rating": Int,
    "comment": String,
    "author": { "id": UUID, "name": String, "email": String },
    "book": { "id": UUID, "title": String, "isbn": String, "publisher": {...} }
  }
  ```

---

### **Pattern 4: Internal Columns**

```sql
-- Internal columns (not exposed in GraphQL)
COMMENT ON COLUMN library.tv_review.pk_review IS
  '@fraiseql:field internal=true,description=Internal primary key';

COMMENT ON COLUMN library.tv_review.fk_author IS
  '@fraiseql:field internal=true,description=Internal foreign key for JOINs';

COMMENT ON COLUMN library.tv_review.fk_book IS
  '@fraiseql:field internal=true,description=Internal foreign key for JOINs';

COMMENT ON COLUMN library.tv_review.refreshed_at IS
  '@fraiseql:field internal=true,description=Last refresh timestamp';
```

**Result**: These columns are NOT exposed in GraphQL (internal use only)

---

## 🎯 Implementation by Day

### **Day 1: Annotation Generator**

#### **File**: `src/generators/fraiseql/table_view_annotator.py` (NEW)

```python
from src.core.ast_models import EntityAST, ExtraFilterColumn

class TableViewAnnotator:
    """Generate FraiseQL annotations for tv_ tables."""

    def __init__(self, entity: EntityAST):
        self.entity = entity

    def generate_annotations(self) -> str:
        """Generate all FraiseQL annotations for tv_ table."""

        if not self.entity.should_generate_table_view:
            return ""

        parts = []

        # Table annotation
        parts.append(self._annotate_table())

        # Column annotations
        parts.append(self._annotate_primary_keys())
        parts.append(self._annotate_filter_columns())
        parts.append(self._annotate_data_column())

        return "\n\n".join(filter(None, parts))

    def _annotate_table(self) -> str:
        """Annotate tv_ table."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        return f"""
-- FraiseQL table annotation
COMMENT ON TABLE {schema}.tv_{entity_lower} IS
  '@fraiseql:table source=materialized,refresh=explicit,primary=true,description=Read-optimized {self.entity.name} with denormalized relations';
""".strip()

    def _annotate_primary_keys(self) -> str:
        """Annotate internal primary keys."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        lines = [
            "-- Internal columns (not exposed in GraphQL)",
            f"COMMENT ON COLUMN {schema}.tv_{entity_lower}.pk_{entity_lower} IS",
            "  '@fraiseql:field internal=true,description=Internal primary key';",
            "",
            f"COMMENT ON COLUMN {schema}.tv_{entity_lower}.refreshed_at IS",
            "  '@fraiseql:field internal=true,description=Last refresh timestamp';"
        ]

        # FK columns (INTEGER) are internal
        for field in self.entity.fields:
            if field.field_type.startswith('ref('):
                ref_entity = self._extract_ref_entity(field.field_type)
                ref_lower = ref_entity.lower()

                lines.append("")
                lines.append(f"COMMENT ON COLUMN {schema}.tv_{entity_lower}.fk_{ref_lower} IS")
                lines.append(f"  '@fraiseql:field internal=true,description=Internal FK for {ref_entity}';")

        return "\n".join(lines)

    def _annotate_filter_columns(self) -> str:
        """Annotate filter columns."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema
        lines = ["-- Filter columns (for efficient WHERE clauses)"]

        # Tenant ID (always)
        lines.append(f"COMMENT ON COLUMN {schema}.tv_{entity_lower}.tenant_id IS")
        lines.append("  '@fraiseql:filter type=UUID,index=btree,performance=optimized,description=Multi-tenant filter';")

        # UUID foreign keys
        for field in self.entity.fields:
            if field.field_type.startswith('ref('):
                ref_entity = self._extract_ref_entity(field.field_type)
                ref_lower = ref_entity.lower()

                lines.append("")
                lines.append(f"COMMENT ON COLUMN {schema}.tv_{entity_lower}.{ref_lower}_id IS")
                lines.append(
                    f"  '@fraiseql:filter type=UUID,relation={ref_entity},index=btree,"
                    f"performance=optimized,description=Filter by {ref_entity}';"
                )

        # Path (if hierarchical)
        if self.entity.hierarchical:
            lines.append("")
            lines.append(f"COMMENT ON COLUMN {schema}.tv_{entity_lower}.path IS")
            lines.append(
                "  '@fraiseql:filter type=String,index=gist,format=ltree_integer,"
                "performance=optimized,description=Hierarchical path (INTEGER-based)';"
            )

        # Extra filter columns
        if self.entity.table_views and self.entity.table_views.extra_filter_columns:
            for col in self.entity.table_views.extra_filter_columns:
                graphql_type = self._map_sql_type_to_graphql(col.type or 'TEXT')
                index_type = col.index_type

                performance = "optimized" if index_type == "btree" else "acceptable"

                lines.append("")
                lines.append(f"COMMENT ON COLUMN {schema}.tv_{entity_lower}.{col.name} IS")
                lines.append(
                    f"  '@fraiseql:filter type={graphql_type},index={index_type},"
                    f"performance={performance},description=Filter by {col.name}';"
                )

        return "\n".join(lines)

    def _annotate_data_column(self) -> str:
        """Annotate JSONB data column."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        return f"""
-- JSONB data column (FraiseQL extracts GraphQL types from structure)
COMMENT ON COLUMN {schema}.tv_{entity_lower}.data IS
  '@fraiseql:jsonb expand=true,description=Denormalized {self.entity.name} data with nested relations';
""".strip()

    def _extract_ref_entity(self, field_type: str) -> str:
        """Extract entity name from ref(Entity)."""
        return field_type[4:-1]

    def _map_sql_type_to_graphql(self, sql_type: str) -> str:
        """Map SQL type to GraphQL type."""
        mapping = {
            'TEXT': 'String',
            'INTEGER': 'Int',
            'DECIMAL': 'Float',
            'BOOLEAN': 'Boolean',
            'TIMESTAMPTZ': 'DateTime',
            'DATE': 'Date',
            'UUID': 'UUID',
            'JSONB': 'JSON'
        }
        return mapping.get(sql_type.upper(), 'String')
```

---

### **Day 2: Template Integration**

#### **File**: `templates/fraiseql/table_view_annotations.sql.jinja2`

```jinja2
{# FraiseQL annotations for tv_ tables #}

-- FraiseQL table annotation
COMMENT ON TABLE {{ entity.schema }}.tv_{{ entity.name|lower }} IS
  '@fraiseql:table source=materialized,refresh=explicit,primary=true,description=Read-optimized {{ entity.name }} with denormalized relations';

-- Internal columns (not exposed in GraphQL)
COMMENT ON COLUMN {{ entity.schema }}.tv_{{ entity.name|lower }}.pk_{{ entity.name|lower }} IS
  '@fraiseql:field internal=true,description=Internal primary key';

COMMENT ON COLUMN {{ entity.schema }}.tv_{{ entity.name|lower }}.refreshed_at IS
  '@fraiseql:field internal=true,description=Last refresh timestamp';

{% for field in entity.fields if field.field_type.startswith('ref(') %}
{%- set ref_entity = field.field_type[4:-1] -%}
{%- set ref_lower = ref_entity|lower -%}

COMMENT ON COLUMN {{ entity.schema }}.tv_{{ entity.name|lower }}.fk_{{ ref_lower }} IS
  '@fraiseql:field internal=true,description=Internal FK for {{ ref_entity }}';
{% endfor %}

-- Filter columns (for efficient WHERE clauses)
COMMENT ON COLUMN {{ entity.schema }}.tv_{{ entity.name|lower }}.tenant_id IS
  '@fraiseql:filter type=UUID,index=btree,performance=optimized,description=Multi-tenant filter';

{% for field in entity.fields if field.field_type.startswith('ref(') %}
{%- set ref_entity = field.field_type[4:-1] -%}
{%- set ref_lower = ref_entity|lower -%}

COMMENT ON COLUMN {{ entity.schema }}.tv_{{ entity.name|lower }}.{{ ref_lower }}_id IS
  '@fraiseql:filter type=UUID,relation={{ ref_entity }},index=btree,performance=optimized,description=Filter by {{ ref_entity }}';
{% endfor %}

{% if entity.hierarchical %}

COMMENT ON COLUMN {{ entity.schema }}.tv_{{ entity.name|lower }}.path IS
  '@fraiseql:filter type=String,index=gist,format=ltree_integer,performance=optimized,description=Hierarchical path (INTEGER-based)';
{% endif %}

{% if entity.table_views and entity.table_views.extra_filter_columns %}
{% for col in entity.table_views.extra_filter_columns %}
{%- set graphql_type = map_type(col.type or 'TEXT') -%}
{%- set performance = 'optimized' if col.index_type == 'btree' else 'acceptable' -%}

COMMENT ON COLUMN {{ entity.schema }}.tv_{{ entity.name|lower }}.{{ col.name }} IS
  '@fraiseql:filter type={{ graphql_type }},index={{ col.index_type }},performance={{ performance }},description=Filter by {{ col.name }}';
{% endfor %}
{% endif %}

-- JSONB data column (FraiseQL extracts GraphQL types from structure)
COMMENT ON COLUMN {{ entity.schema }}.tv_{{ entity.name|lower }}.data IS
  '@fraiseql:jsonb expand=true,description=Denormalized {{ entity.name }} data with nested relations';
```

---

### **Day 3: Testing & Documentation**

#### **Test File**: `tests/unit/fraiseql/test_table_view_annotations.py`

```python
import pytest
from src.core.ast_models import (
    EntityAST, FieldDefinition, TableViewConfig, ExtraFilterColumn
)
from src.generators.fraiseql.table_view_annotator import TableViewAnnotator

class TestTableViewAnnotations:
    """Test FraiseQL annotations for tv_ tables."""

    def test_table_annotation(self):
        """Test table-level annotation."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[],
            actions=[]
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "COMMENT ON TABLE library.tv_review" in sql
        assert "@fraiseql:table" in sql
        assert "source=materialized" in sql
        assert "refresh=explicit" in sql

    def test_filter_column_annotations(self):
        """Test filter column annotations."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[
                FieldDefinition(name="author", field_type="ref(User)")
            ],
            actions=[],
            table_views=TableViewConfig(
                extra_filter_columns=[
                    ExtraFilterColumn.from_string("rating")
                ]
            )
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        # UUID FK filter
        assert "COMMENT ON COLUMN library.tv_review.author_id" in sql
        assert "@fraiseql:filter type=UUID" in sql
        assert "relation=User" in sql

        # Extra filter column
        assert "COMMENT ON COLUMN library.tv_review.rating" in sql
        assert "@fraiseql:filter" in sql

    def test_data_column_annotation(self):
        """Test JSONB data column annotation."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[],
            actions=[]
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "COMMENT ON COLUMN library.tv_review.data" in sql
        assert "@fraiseql:jsonb expand=true" in sql

    def test_internal_columns(self):
        """Test internal column annotations."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[
                FieldDefinition(name="author", field_type="ref(User)")
            ],
            actions=[]
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        # Primary key internal
        assert "COMMENT ON COLUMN library.tv_review.pk_review" in sql
        assert "internal=true" in sql

        # FK internal
        assert "COMMENT ON COLUMN library.tv_review.fk_author" in sql
        assert "internal=true" in sql

    def test_hierarchical_path_annotation(self):
        """Test path column annotation for hierarchical entities."""
        entity = EntityAST(
            name="Location",
            schema="management",
            fields=[],
            actions=[],
            hierarchical=True
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "COMMENT ON COLUMN management.tv_location.path" in sql
        assert "format=ltree_integer" in sql
        assert "index=gist" in sql
```

---

## 📋 Complete Example

### **Entity**: Review

**SpecQL**:
```yaml
entity: Review
schema: library

fields:
  rating: integer
  comment: text
  author: ref(User)
  book: ref(Book)

table_views:
  include_relations:
    - author:
        fields: [name, email]
    - book:
        fields: [title, isbn]

  extra_filter_columns:
    - rating
    - created_at
```

**Generated Annotations**:
```sql
-- FraiseQL table annotation
COMMENT ON TABLE library.tv_review IS
  '@fraiseql:table source=materialized,refresh=explicit,primary=true,description=Read-optimized Review with denormalized relations';

-- Internal columns (not exposed in GraphQL)
COMMENT ON COLUMN library.tv_review.pk_review IS
  '@fraiseql:field internal=true,description=Internal primary key';

COMMENT ON COLUMN library.tv_review.fk_author IS
  '@fraiseql:field internal=true,description=Internal FK for User';

COMMENT ON COLUMN library.tv_review.fk_book IS
  '@fraiseql:field internal=true,description=Internal FK for Book';

COMMENT ON COLUMN library.tv_review.refreshed_at IS
  '@fraiseql:field internal=true,description=Last refresh timestamp';

-- Filter columns (for efficient WHERE clauses)
COMMENT ON COLUMN library.tv_review.tenant_id IS
  '@fraiseql:filter type=UUID,index=btree,performance=optimized,description=Multi-tenant filter';

COMMENT ON COLUMN library.tv_review.author_id IS
  '@fraiseql:filter type=UUID,relation=User,index=btree,performance=optimized,description=Filter by User';

COMMENT ON COLUMN library.tv_review.book_id IS
  '@fraiseql:filter type=UUID,relation=Book,index=btree,performance=optimized,description=Filter by Book';

COMMENT ON COLUMN library.tv_review.rating IS
  '@fraiseql:filter type=Int,index=btree,performance=optimized,description=Filter by rating';

COMMENT ON COLUMN library.tv_review.created_at IS
  '@fraiseql:filter type=DateTime,index=btree,performance=optimized,description=Filter by created_at';

-- JSONB data column (FraiseQL extracts GraphQL types from structure)
COMMENT ON COLUMN library.tv_review.data IS
  '@fraiseql:jsonb expand=true,description=Denormalized Review data with nested relations';
```

**FraiseQL Auto-Generates**:
```graphql
type Review {
  id: UUID!
  rating: Int!
  comment: String
  createdAt: DateTime!
  author: ReviewAuthor!
  book: ReviewBook!
}

type ReviewAuthor {
  id: UUID!
  name: String!
  email: String!
}

type ReviewBook {
  id: UUID!
  title: String!
  isbn: String!
}

type Query {
  review(id: UUID!): Review
  reviews(
    where: ReviewFilter
    limit: Int
    offset: Int
  ): [Review!]!
}

input ReviewFilter {
  # Auto-generated from filter column annotations
  authorId: UUIDFilter
  bookId: UUIDFilter
  rating: IntFilter
  createdAt: DateTimeFilter
}
```

---

## ✅ Acceptance Criteria

- [ ] Table annotations generated with @fraiseql:table
- [ ] Internal columns marked with internal=true
- [ ] Filter columns annotated with type, index, performance
- [ ] Data column annotated with expand=true
- [ ] Hierarchical entities get path annotation
- [ ] All annotations valid (no syntax errors)
- [ ] FraiseQL can introspect and generate GraphQL

---

## 📊 Summary

**Files Created**:
- `src/generators/fraiseql/table_view_annotator.py` (~300 lines)
- `templates/fraiseql/table_view_annotations.sql.jinja2` (~100 lines)
- `tests/unit/fraiseql/test_table_view_annotations.py` (~200 lines)

**Total**: ~600 lines

**Timeline**: 2-3 days

---

## 🔗 Dependencies

**Depends On**:
- Team B Phase 9 (tv_ tables must exist)

**Blocks**:
- FraiseQL integration (final step)

---

**Status**: 🟢 READY TO START (after Team B Phase 9)
**Priority**: LOW (metadata layer only)
**Effort**: 2-3 days
**Start**: Week 7
