# Team B Phase 9: Table Views (tv_) Generation

**Phase**: 9 of 9 (NEW - CQRS Read Side)
**Timeline**: Week 5-6 (7-8 days)
**Priority**: 🔴 CRITICAL - Enables FraiseQL Integration
**Status**: 🔴 NEW PHASE - CQRS Implementation

---

## 📋 Overview

Generate **tv_ (table view) tables** for read-optimized CQRS pattern. These denormalized tables expose data to FraiseQL for auto-GraphQL generation.

**Key Innovation**: JSONB composition from related `tv_` tables (not `tb_` tables)

---

## 🎯 Objectives

1. ✅ Generate `tv_{entity}` table schema with JSONB data column
2. ✅ Auto-infer filter columns (tenant_id, {entity}_id, path)
3. ✅ Generate explicit filter columns (from extra_filter_columns)
4. ✅ Generate `refresh_tv_{entity}()` function with JSONB composition
5. ✅ Generate performance-optimized indexes (B-tree + GIN)
6. ✅ Handle dependency ordering for cascading composition

---

## 🏗️ tv_ Table Schema Pattern

### **Standard Structure**

```sql
CREATE TABLE {schema}.tv_{entity} (
    -- Primary identification (Trinity pattern)
    pk_{entity} INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,

    -- Foreign keys (INTEGER) for JOINs during refresh
    {for each ref field}
    fk_{referenced_entity} INTEGER [NOT NULL],

    -- UUID foreign keys for external filtering (auto-inferred)
    {for each ref field}
    {referenced_entity}_id UUID [NOT NULL],

    -- Hierarchy path (if hierarchical)
    path LTREE,  -- Auto-added for hierarchical entities

    -- Explicit filter columns (from extra_filter_columns)
    {for each extra_filter_column}
    {column_name} {column_type},

    -- Denormalized JSONB payload (FraiseQL reads this!)
    data JSONB NOT NULL,

    -- Metadata
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_tv_{entity}_tenant ON {schema}.tv_{entity}(tenant_id);

{for each UUID foreign key}
CREATE INDEX idx_tv_{entity}_{ref_entity}_id ON {schema}.tv_{entity}({ref_entity}_id);

{for each extra_filter_column}
CREATE INDEX idx_tv_{entity}_{column_name} ON {schema}.tv_{entity}({column_name});

{if hierarchical}
CREATE INDEX idx_tv_{entity}_path ON {schema}.tv_{entity} USING GIST(path);

-- GIN index for JSONB queries
CREATE INDEX idx_tv_{entity}_data ON {schema}.tv_{entity} USING GIN(data);
```

---

## 📊 Implementation by Day

### **Day 1-2: Schema Generation Logic**

#### **File**: `src/generators/schema/table_view_generator.py` (NEW)

```python
from typing import List, Optional
from src.core.ast_models import EntityAST, TableViewConfig, IncludeRelation

class TableViewGenerator:
    """Generate tv_ table schema and refresh functions."""

    def __init__(self, entity: EntityAST, all_entities: dict):
        self.entity = entity
        self.all_entities = all_entities  # For resolving references

    def should_generate(self) -> bool:
        """Determine if tv_ should be generated."""
        return self.entity.should_generate_table_view

    def generate_schema(self) -> str:
        """Generate complete tv_ table DDL."""
        if not self.should_generate():
            return ""

        parts = []

        # Table creation
        parts.append(self._generate_table_ddl())

        # Indexes
        parts.append(self._generate_indexes())

        # Refresh function
        parts.append(self._generate_refresh_function())

        return "\n\n".join(parts)

    def _generate_table_ddl(self) -> str:
        """Generate CREATE TABLE statement for tv_."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        columns = []

        # Trinity pattern
        columns.append(f"pk_{entity_lower} INTEGER PRIMARY KEY")
        columns.append(f"id UUID NOT NULL UNIQUE")
        columns.append(f"tenant_id UUID NOT NULL")

        # Foreign keys (INTEGER + UUID)
        for field in self.entity.fields:
            if field.field_type.startswith('ref('):
                ref_entity = self._extract_ref_entity(field.field_type)
                ref_lower = ref_entity.lower()

                # INTEGER FK for JOINs
                columns.append(f"fk_{ref_lower} INTEGER")

                # UUID FK for filtering
                columns.append(f"{ref_lower}_id UUID")

        # Hierarchy path (if hierarchical)
        if self.entity.hierarchical:
            columns.append(f"path LTREE NOT NULL")

        # Extra filter columns
        if self.entity.table_views:
            for col in self.entity.table_views.extra_filter_columns:
                col_type = self._infer_column_type(col)
                columns.append(f"{col.name} {col_type}")

        # JSONB data column
        columns.append(f"data JSONB NOT NULL")

        # Metadata
        columns.append(f"refreshed_at TIMESTAMPTZ DEFAULT now()")

        return f"""
-- Table view for {self.entity.name} (read-optimized, denormalized)
CREATE TABLE {schema}.tv_{entity_lower} (
    {',\n    '.join(columns)}
);
""".strip()

    def _generate_indexes(self) -> str:
        """Generate indexes for tv_ table."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema
        indexes = []

        # Tenant index (always)
        indexes.append(
            f"CREATE INDEX idx_tv_{entity_lower}_tenant "
            f"ON {schema}.tv_{entity_lower}(tenant_id);"
        )

        # UUID foreign key indexes (auto-inferred)
        for field in self.entity.fields:
            if field.field_type.startswith('ref('):
                ref_entity = self._extract_ref_entity(field.field_type)
                ref_lower = ref_entity.lower()

                indexes.append(
                    f"CREATE INDEX idx_tv_{entity_lower}_{ref_lower}_id "
                    f"ON {schema}.tv_{entity_lower}({ref_lower}_id);"
                )

        # Path index (if hierarchical)
        if self.entity.hierarchical:
            indexes.append(
                f"CREATE INDEX idx_tv_{entity_lower}_path "
                f"ON {schema}.tv_{entity_lower} USING GIST(path);"
            )

        # Extra filter column indexes
        if self.entity.table_views:
            for col in self.entity.table_views.extra_filter_columns:
                index_type = col.index_type.upper()

                if index_type == "GIN_TRGM":
                    # Trigram index for partial text matching
                    indexes.append(
                        f"CREATE INDEX idx_tv_{entity_lower}_{col.name} "
                        f"ON {schema}.tv_{entity_lower} "
                        f"USING GIN({col.name} gin_trgm_ops);"
                    )
                elif index_type == "GIN":
                    indexes.append(
                        f"CREATE INDEX idx_tv_{entity_lower}_{col.name} "
                        f"ON {schema}.tv_{entity_lower} "
                        f"USING GIN({col.name});"
                    )
                elif index_type == "GIST":
                    indexes.append(
                        f"CREATE INDEX idx_tv_{entity_lower}_{col.name} "
                        f"ON {schema}.tv_{entity_lower} "
                        f"USING GIST({col.name});"
                    )
                else:  # BTREE (default)
                    indexes.append(
                        f"CREATE INDEX idx_tv_{entity_lower}_{col.name} "
                        f"ON {schema}.tv_{entity_lower}({col.name});"
                    )

        # GIN index for JSONB queries (always)
        indexes.append(
            f"CREATE INDEX idx_tv_{entity_lower}_data "
            f"ON {schema}.tv_{entity_lower} USING GIN(data);"
        )

        return "\n".join(indexes)

    def _infer_column_type(self, col) -> str:
        """Infer SQL type for extra filter column."""
        if col.type:
            # Explicit type provided
            return col.type.upper()

        # Infer from source field if available
        if col.source:
            # Source like "author.name" - need to resolve type
            # For now, default to TEXT
            return "TEXT"

        # Try to find field in entity
        for field in self.entity.fields:
            if field.name == col.name:
                return self._map_specql_type_to_sql(field.field_type)

        # Default
        return "TEXT"

    def _map_specql_type_to_sql(self, specql_type: str) -> str:
        """Map SpecQL type to SQL type."""
        mapping = {
            'text': 'TEXT',
            'integer': 'INTEGER',
            'decimal': 'DECIMAL',
            'boolean': 'BOOLEAN',
            'timestamp': 'TIMESTAMPTZ',
            'date': 'DATE',
            'jsonb': 'JSONB',
        }
        return mapping.get(specql_type.lower(), 'TEXT')

    def _extract_ref_entity(self, field_type: str) -> str:
        """Extract entity name from ref(Entity) type."""
        # ref(User) -> User
        return field_type[4:-1]
```

---

### **Day 3-5: JSONB Composition Logic**

#### **File**: `src/generators/schema/table_view_generator.py` (continued)

```python
    def _generate_refresh_function(self) -> str:
        """Generate refresh_tv_{entity}() function with JSONB composition."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        # Build SELECT columns
        select_columns = self._build_select_columns()

        # Build FROM clause with JOINs to tv_ tables
        from_clause = self._build_from_clause_with_tv_joins()

        # Build JSONB data construction
        jsonb_construction = self._build_jsonb_data()

        return f"""
-- Refresh function for tv_{entity_lower}
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION {schema}.refresh_tv_{entity_lower}(
    p_pk_{entity_lower} INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM {schema}.tv_{entity_lower}
    WHERE p_pk_{entity_lower} IS NULL OR pk_{entity_lower} = p_pk_{entity_lower};

    -- Insert refreshed data
    INSERT INTO {schema}.tv_{entity_lower} (
        {', '.join(select_columns)}
    )
    SELECT
        {self._build_select_values()}
    {from_clause}
    WHERE base.deleted_at IS NULL
      AND (p_pk_{entity_lower} IS NULL OR base.pk_{entity_lower} = p_pk_{entity_lower});
END;
$$ LANGUAGE plpgsql;
""".strip()

    def _build_select_columns(self) -> List[str]:
        """Build list of columns for INSERT."""
        entity_lower = self.entity.name.lower()
        columns = [
            f"pk_{entity_lower}",
            "id",
            "tenant_id"
        ]

        # FK columns (INTEGER + UUID)
        for field in self.entity.fields:
            if field.field_type.startswith('ref('):
                ref_entity = self._extract_ref_entity(field.field_type)
                ref_lower = ref_entity.lower()
                columns.append(f"fk_{ref_lower}")
                columns.append(f"{ref_lower}_id")

        # Path (if hierarchical)
        if self.entity.hierarchical:
            columns.append("path")

        # Extra filter columns
        if self.entity.table_views:
            for col in self.entity.table_views.extra_filter_columns:
                columns.append(col.name)

        # Data column
        columns.append("data")

        return columns

    def _build_from_clause_with_tv_joins(self) -> str:
        """Build FROM clause with JOINs to tv_ tables (composition!)."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        lines = [f"FROM {schema}.tb_{entity_lower} base"]

        # Join to tv_ tables (not tb_ tables!)
        for field in self.entity.fields:
            if field.field_type.startswith('ref('):
                ref_entity = self._extract_ref_entity(field.field_type)
                ref_lower = ref_entity.lower()

                # Get referenced entity schema
                ref_schema = self._get_entity_schema(ref_entity)

                # Join to tv_ table (composition!)
                join_type = "INNER" if field.required else "LEFT"
                lines.append(
                    f"{join_type} JOIN {ref_schema}.tv_{ref_lower} tv_{ref_lower} "
                    f"ON tv_{ref_lower}.pk_{ref_lower} = base.fk_{ref_lower}"
                )

        return "\n    ".join(lines)

    def _build_jsonb_data(self) -> str:
        """Build JSONB data construction."""
        parts = []

        # Add entity's own fields
        for field in self.entity.fields:
            if not field.field_type.startswith('ref('):
                # Scalar field
                parts.append(f"'{field.name}', base.{field.name}")

        # Add related entities (compose from tv_.data)
        config = self.entity.table_views
        if config and config.include_relations:
            for rel in config.include_relations:
                parts.append(self._build_relation_jsonb(rel))
        else:
            # No explicit config - include all ref fields with all data
            for field in self.entity.fields:
                if field.field_type.startswith('ref('):
                    ref_entity = self._extract_ref_entity(field.field_type)
                    ref_lower = ref_entity.lower()

                    # Include full tv_.data
                    parts.append(f"'{field.name}', tv_{ref_lower}.data")

        return f"jsonb_build_object(\n            {',\n            '.join(parts)}\n        )"

    def _build_relation_jsonb(self, rel: IncludeRelation) -> str:
        """Build JSONB for a single relation (explicit field selection)."""
        rel_lower = rel.entity_name.lower()

        if rel.fields == ['*']:
            # Include all fields from tv_.data
            return f"'{rel.entity_name}', tv_{rel_lower}.data"
        else:
            # Extract specific fields from tv_.data
            field_extractions = []
            for field in rel.fields:
                field_extractions.append(
                    f"'{field}', tv_{rel_lower}.data->'{field}'"
                )

            # Handle nested relations
            if rel.include_relations:
                for nested in rel.include_relations:
                    # Nested relations are already composed in parent tv_.data
                    nested_lower = nested.entity_name.lower()
                    field_extractions.append(
                        f"'{nested.entity_name}', tv_{rel_lower}.data->'{nested.entity_name}'"
                    )

            return f"""'{rel.entity_name}', jsonb_build_object(
                {',\n                '.join(field_extractions)}
            )"""

    def _build_select_values(self) -> str:
        """Build SELECT values for INSERT."""
        entity_lower = self.entity.name.lower()
        values = [
            f"base.pk_{entity_lower}",
            "base.id",
            "base.tenant_id"
        ]

        # FK values
        for field in self.entity.fields:
            if field.field_type.startswith('ref('):
                ref_entity = self._extract_ref_entity(field.field_type)
                ref_lower = ref_entity.lower()

                # INTEGER FK
                values.append(f"base.fk_{ref_lower}")

                # UUID FK (from tv_ table)
                values.append(f"tv_{ref_lower}.id AS {ref_lower}_id")

        # Path (if hierarchical)
        if self.entity.hierarchical:
            values.append("base.path")

        # Extra filter columns
        if self.entity.table_views:
            for col in self.entity.table_views.extra_filter_columns:
                if col.source:
                    # Nested extraction (e.g., author.name)
                    parts = col.source.split('.')
                    if len(parts) == 2:
                        entity_name, field_name = parts
                        values.append(f"tv_{entity_name.lower()}.data->>'{field_name}' AS {col.name}")
                    else:
                        values.append(f"base.{col.name}")
                else:
                    # Direct field from base table
                    values.append(f"base.{col.name}")

        # JSONB data
        values.append(f"{self._build_jsonb_data()} AS data")

        return ",\n        ".join(values)

    def _get_entity_schema(self, entity_name: str) -> str:
        """Get schema for referenced entity."""
        if entity_name in self.all_entities:
            return self.all_entities[entity_name].schema
        # Default to same schema
        return self.entity.schema
```

---

### **Day 6: Dependency Ordering**

#### **File**: `src/generators/schema/table_view_dependency.py` (NEW)

```python
from typing import List, Dict, Set
from src.core.ast_models import EntityAST

class TableViewDependencyResolver:
    """Resolve dependency order for tv_ generation and refresh."""

    def __init__(self, entities: List[EntityAST]):
        self.entities = {e.name: e for e in entities}
        self.dependency_graph = self._build_dependency_graph()

    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph (entity -> depends on entities)."""
        graph = {}

        for entity in self.entities.values():
            deps = set()

            # Find ref() fields
            for field in entity.fields:
                if field.field_type.startswith('ref('):
                    ref_entity = field.field_type[4:-1]
                    if ref_entity != entity.name:  # Not self-reference
                        deps.add(ref_entity)

            graph[entity.name] = deps

        return graph

    def get_generation_order(self) -> List[str]:
        """Get entity names in dependency order (topological sort)."""
        # Kahn's algorithm for topological sort
        in_degree = {name: 0 for name in self.entities.keys()}

        # Calculate in-degrees
        for deps in self.dependency_graph.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Queue entities with no incoming edges
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Process entity with no dependencies
            entity_name = queue.pop(0)
            result.append(entity_name)

            # Reduce in-degree for dependent entities
            for dep_entity, deps in self.dependency_graph.items():
                if entity_name in deps:
                    in_degree[dep_entity] -= 1
                    if in_degree[dep_entity] == 0:
                        queue.append(dep_entity)

        if len(result) != len(self.entities):
            # Cycle detected
            raise ValueError("Circular dependency detected in entity references")

        return result

    def get_refresh_order_for_entity(self, entity_name: str) -> List[str]:
        """Get entities that must be refreshed when given entity changes."""
        # Find all entities that depend on this one
        dependents = []

        for name, deps in self.dependency_graph.items():
            if entity_name in deps:
                dependents.append(name)

        return dependents
```

---

### **Day 7-8: Integration & Testing**

#### **Test File**: `tests/unit/schema/test_table_view_generation.py`

```python
import pytest
from src.core.ast_models import (
    EntityAST, FieldDefinition, TableViewConfig,
    TableViewMode, IncludeRelation, ExtraFilterColumn
)
from src.generators.schema.table_view_generator import TableViewGenerator

class TestTableViewGeneration:
    """Test tv_ table generation."""

    def test_basic_tv_generation(self):
        """Test basic tv_ table DDL generation."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[
                FieldDefinition(name="rating", field_type="integer"),
                FieldDefinition(name="author", field_type="ref(User)")
            ],
            actions=[]
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "CREATE TABLE library.tv_review" in sql
        assert "pk_review INTEGER PRIMARY KEY" in sql
        assert "id UUID" in sql
        assert "tenant_id UUID" in sql
        assert "fk_author INTEGER" in sql
        assert "author_id UUID" in sql
        assert "data JSONB NOT NULL" in sql

    def test_indexes_generated(self):
        """Test indexes are generated correctly."""
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

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "idx_tv_review_tenant" in sql
        assert "idx_tv_review_author_id" in sql
        assert "idx_tv_review_rating" in sql
        assert "idx_tv_review_data" in sql
        assert "USING GIN(data)" in sql

    def test_hierarchical_entity(self):
        """Test hierarchical entity gets path column."""
        entity = EntityAST(
            name="Location",
            schema="management",
            fields=[],
            actions=[],
            hierarchical=True
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "path LTREE NOT NULL" in sql
        assert "idx_tv_location_path" in sql
        assert "USING GIST(path)" in sql

    def test_refresh_function_composition(self):
        """Test refresh function composes from tv_ tables."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[
                FieldDefinition(name="author", field_type="ref(User)")
            ],
            actions=[]
        )

        generator = TableViewGenerator(entity, {"User": EntityAST(...)})
        sql = generator.generate_schema()

        # Should JOIN to tv_user, not tb_user!
        assert "JOIN crm.tv_user tv_user" in sql
        assert "tv_user.data" in sql
        assert "tb_user" not in sql  # Should NOT join to tb_!

    def test_explicit_field_selection(self):
        """Test explicit field selection from relations."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[
                FieldDefinition(name="author", field_type="ref(User)")
            ],
            actions=[],
            table_views=TableViewConfig(
                include_relations=[
                    IncludeRelation(
                        entity_name="author",
                        fields=["name", "email"]
                    )
                ]
            )
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        # Should extract only specified fields
        assert "tv_author.data->'name'" in sql or "tv_author.data->>'name'" in sql
        assert "tv_author.data->'email'" in sql or "tv_author.data->>'email'" in sql

    def test_extra_filter_column_with_source(self):
        """Test nested field extraction for filter column."""
        entity = EntityAST(
            name="Review",
            schema="library",
            fields=[
                FieldDefinition(name="author", field_type="ref(User)")
            ],
            actions=[],
            table_views=TableViewConfig(
                extra_filter_columns=[
                    ExtraFilterColumn(
                        name="author_name",
                        source="author.name",
                        type="text"
                    )
                ]
            )
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "author_name TEXT" in sql
        assert "tv_author.data->>'name' AS author_name" in sql
```

---

## 📋 Template Files

### **File**: `templates/schema/table_view.sql.jinja2`

```jinja2
{# Template for tv_ table generation #}

-- Table view for {{ entity.name }} (read-optimized, denormalized)
CREATE TABLE {{ entity.schema }}.tv_{{ entity.name|lower }} (
    -- Primary identification
    pk_{{ entity.name|lower }} INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,

    {% for field in entity.fields if field.field_type.startswith('ref(') %}
    -- Foreign key: {{ field.name }}
    fk_{{ field.name|lower }} INTEGER{% if field.required %} NOT NULL{% endif %},
    {{ field.name|lower }}_id UUID{% if field.required %} NOT NULL{% endif %},

    {% endfor %}

    {% if entity.hierarchical %}
    -- Hierarchy path
    path LTREE NOT NULL,

    {% endif %}

    {% if entity.table_views and entity.table_views.extra_filter_columns %}
    -- Performance-optimized filter columns
    {% for col in entity.table_views.extra_filter_columns %}
    {{ col.name }} {{ col.type|default('TEXT') }},
    {% endfor %}

    {% endif %}

    -- Denormalized JSONB payload
    data JSONB NOT NULL,

    -- Metadata
    refreshed_at TIMESTAMPTZ DEFAULT now()
);
```

---

## ✅ Acceptance Criteria

- [ ] tv_ table DDL generated with correct columns
- [ ] Auto-inferred filter columns (tenant_id, {entity}_id, path)
- [ ] Explicit filter columns (from extra_filter_columns)
- [ ] Refresh function JOINs to tv_ tables (not tb_!)
- [ ] JSONB composition extracts from tv_.data
- [ ] Explicit field selection works (include_relations)
- [ ] Nested extraction works (source: "author.name")
- [ ] Correct indexes generated (B-tree, GIN, GIST)
- [ ] Dependency ordering works (topological sort)
- [ ] Hierarchical entities get path column
- [ ] All tests pass

---

## 📊 Summary

**Files Created**:
- `src/generators/schema/table_view_generator.py` (~800 lines)
- `src/generators/schema/table_view_dependency.py` (~100 lines)
- `templates/schema/table_view.sql.jinja2` (~50 lines)
- `templates/schema/refresh_table_view.sql.jinja2` (~100 lines)
- `tests/unit/schema/test_table_view_generation.py` (~400 lines)

**Total**: ~1,450 lines

**Timeline**: 7-8 days

---

## 🔗 Dependencies

**Depends On**:
- Team A Phase 2 (table_views parsing)
- Team B Phases 1-8 (schema generation foundation)

**Blocks**:
- Team C (tv_ refresh in mutations)
- Team D (tv_ annotations)
- FraiseQL integration

---

**Status**: 🔴 READY TO START (after Team A Phase 2)
**Priority**: CRITICAL (enables CQRS + FraiseQL)
**Effort**: 7-8 days
**Start**: Week 5-6
