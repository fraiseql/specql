# SpecQL Table Views Documentation Index

**Date**: 2025-11-10
**Topic**: Commodity Views (tv_ Tables) Support in SpecQL
**Status**: Complete Implementation - Production Ready

---

## Quick Links

### For Quick Understanding
- **[SPECQL_TABLE_VIEWS_QUICK_REFERENCE.md](./SPECQL_TABLE_VIEWS_QUICK_REFERENCE.md)** - 5-10 minute read covering essentials
- **[SpecQL Review Example](./specql/entities/examples/review_with_table_views.yaml)** - Working YAML example you can study

### For Deep Dive
- **[SPECQL_TABLE_VIEWS_ANALYSIS.md](./SPECQL_TABLE_VIEWS_ANALYSIS.md)** - 30+ page comprehensive analysis
- **[CQRS Architecture](./specql/docs/architecture/CQRS_TABLE_VIEWS_IMPLEMENTATION.md)** - Official SpecQL architecture doc
- **[FraiseQL Annotations](./specql/docs/reference/fraiseql/TV_ANNOTATIONS.md)** - GraphQL integration details

### Implementation Details
- **[AST Models](./specql/src/core/ast_models.py)** - TableViewConfig, IncludeRelation classes (lines 36-132)
- **[Schema Generator](./specql/src/generators/schema/table_view_generator.py)** - tv_ table DDL generation
- **[FraiseQL Annotator](./specql/src/generators/fraiseql/table_view_annotator.py)** - GraphQL metadata generation

### Tests
- **[Unit Tests](./specql/tests/unit/schema/test_table_view_generation.py)** - Schema generation tests
- **[Integration Tests](./specql/tests/integration/fraiseql/test_tv_annotations_e2e.py)** - End-to-end tests

---

## One-Minute Summary

**Question**: Does SpecQL support commodity views (denormalized tables with precomputed JSONB)?

**Answer**: YES - fully implemented as "Table Views" (tv_ pattern)

**In YAML**:
```yaml
table_views:
  mode: auto
  include_relations:
    - entity_name: RelatedEntity
      fields: [field1, field2]
  extra_filter_columns:
    - hot_path_column
```

**What Gets Generated**:
1. `tb_*` - Normalized write table
2. `tv_*` - Denormalized read table with JSONB
3. `refresh_tv_*()` - Function to keep tv_ in sync
4. FraiseQL annotations for GraphQL auto-discovery

---

## Document Organization

### 1. Quick Reference (9 KB)
**File**: `SPECQL_TABLE_VIEWS_QUICK_REFERENCE.md`

**Contents**:
- What are table views
- Configuration options (mode, include_relations, extra_filter_columns)
- Two-tier filtering strategy (B-tree vs GIN)
- Common patterns
- Troubleshooting

**Best for**: Getting up to speed quickly, copy-paste examples

---

### 2. Detailed Analysis (16 KB)
**File**: `SPECQL_TABLE_VIEWS_ANALYSIS.md`

**Contents**:
- Executive summary
- Architecture: three-layer CQRS
- Configuration options (all details)
- Composition strategy (key innovation)
- Implementation status (Phases 1-4)
- Lifecycle: write operation flow
- Complete example YAML
- Integration with PrintOptim

**Best for**: Understanding the full picture, making design decisions

---

### 3. Official SpecQL Docs

**CQRS Implementation** (`specql/docs/architecture/CQRS_TABLE_VIEWS_IMPLEMENTATION.md`)
- 1000+ lines of detailed architecture
- Includes all configuration examples
- Performance optimization strategies
- Implementation roadmap

**FraiseQL Annotations** (`specql/docs/reference/fraiseql/TV_ANNOTATIONS.md`)
- How FraiseQL discovers tv_ tables
- Annotation format and meaning
- Generated GraphQL types
- Integration with auto-discovery

**TV Annotations E2E Test** (`specql/tests/integration/fraiseql/test_tv_annotations_e2e.py`)
- Complete working example in test format
- Shows all phases in action
- Validates all features

---

### 4. Source Code

**AST Models** (`specql/src/core/ast_models.py`, lines 36-132)
```python
class TableViewMode(Enum):
    AUTO = "auto"        # Generate if has FKs
    FORCE = "force"      # Always generate
    DISABLE = "disable"  # Never generate

class IncludeRelation:
    entity_name: str
    fields: list[str]           # Which fields to include
    include_relations: list[...] # Nested

class ExtraFilterColumn:
    name: str
    source: str | None  # For nested extraction
    type: str | None
    index_type: str     # btree|gin|gin_trgm|gist

class TableViewConfig:
    mode: TableViewMode
    include_relations: list[IncludeRelation]
    extra_filter_columns: list[ExtraFilterColumn]
```

**Schema Generator** (`specql/src/generators/schema/table_view_generator.py`)
- `should_generate()` - Determine if tv_ needed
- `generate_schema()` - Create DDL
- `_generate_table_ddl()` - Table creation
- `_generate_indexes()` - Index creation
- `_generate_refresh_function()` - Refresh function

**FraiseQL Annotator** (`specql/src/generators/fraiseql/table_view_annotator.py`)
- `annotate_table()` - Table-level metadata
- `annotate_columns()` - Column-level metadata
- `annotate_jsonb_data()` - JSONB introspection hints

---

## Common Questions Answered

### Q: What's the difference between tv_ and tb_?

| Aspect | tb_ (Write Side) | tv_ (Read Side) |
|--------|------------------|-----------------|
| Normalization | Normalized (3NF) | Denormalized |
| Purpose | Transactional integrity | Fast queries |
| Foreign keys | Yes, with constraints | Yes, no constraints |
| JSONB | No | Yes (data column) |
| Indexes | All fields | Selective (hot paths) |
| Updates | Direct writes | Via refresh function |

### Q: When should I use table_views?

**Use** (mode: auto/force):
- Entity has multiple foreign keys
- Queries frequently filter by FK
- GraphQL needs nested entity data
- Read queries much more common than writes

**Don't use** (mode: disable):
- Write-heavy tables
- No foreign keys and no hot-path filtering
- Large JSONB would bloat storage

### Q: How does consistency work?

SpecQL composes JSONB from `tv_` tables, not `tb_` tables:
```sql
-- When tv_contact refreshes:
jsonb_build_object(
    'organization', tv_organization.data  -- From tv_, not tb_!
)
```

This ensures: When tv_organization updates, tv_contact picks up changes automatically.

### Q: What about performance?

**Two-tier filtering**:
- Direct columns (B-tree): ~0.1ms
- JSONB fields (GIN): ~50-100ms

Specify hot-path columns in `extra_filter_columns` to use B-tree instead of GIN.

### Q: How does GraphQL integration work?

FraiseQL introspects tv_ structure via annotations:
```sql
COMMENT ON COLUMN schema.tv_entity.data IS
  '@fraiseql:jsonb expand=true,...'
```

FraiseQL auto-generates GraphQL types from JSONB structure - zero configuration.

### Q: Can I use tv_ for hierarchical entities?

Yes - SpecQL auto-generates `path LTREE` column for hierarchical entities.

---

## Implementation Phases (All Complete)

| Phase | What | Status | Key Files |
|-------|------|--------|-----------|
| 1 | Parser extensions | ✅ | `ast_models.py`, `specql_parser.py` |
| 2 | Schema generation (tv_ DDL) | ✅ | `table_view_generator.py` |
| 3 | Mutation integration | ✅ | `refresh_table_view_compiler.py` |
| 4 | FraiseQL annotations | ✅ | `table_view_annotator.py` |

**All phases implemented and tested**

---

## Key Innovations

### 1. Cascading Composition
Composes JSONB from tv_ tables, creating automatic consistency when related entities update.

### 2. Two-Tier Filtering
Auto-inferred hot paths (B-tree) + explicit optimization + GIN fallback.

### 3. Nested Include Relations
Can specify fields from entities within entities (e.g., Book.Publisher fields in Review).

### 4. Explicit Refresh Scopes
Control exactly which tv_ tables refresh after a mutation (self, related, propagate, batch).

---

## File Structure in This Repository

```
printoptim_specql/
├── SPECQL_TABLE_VIEWS_INDEX.md          (THIS FILE)
├── SPECQL_TABLE_VIEWS_QUICK_REFERENCE.md
├── SPECQL_TABLE_VIEWS_ANALYSIS.md
├── specql/
│   ├── src/
│   │   ├── core/
│   │   │   ├── ast_models.py            (TableViewConfig, IncludeRelation)
│   │   │   └── specql_parser.py         (parse table_views block)
│   │   └── generators/
│   │       ├── schema/
│   │       │   ├── table_view_generator.py
│   │       │   └── table_view_dependency.py
│   │       ├── fraiseql/
│   │       │   └── table_view_annotator.py
│   │       └── actions/
│   │           └── step_compilers/
│   │               └── refresh_table_view_compiler.py
│   ├── tests/
│   │   ├── unit/
│   │   │   └── schema/
│   │   │       └── test_table_view_generation.py
│   │   └── integration/
│   │       └── fraiseql/
│   │           └── test_tv_annotations_e2e.py
│   ├── entities/examples/
│   │   └── review_with_table_views.yaml
│   ├── docs/
│   │   ├── reference/fraiseql/
│   │   │   └── TV_ANNOTATIONS.md
│   │   └── architecture/
│   │       └── CQRS_TABLE_VIEWS_IMPLEMENTATION.md
│   └── templates/
│       ├── schema/
│       │   ├── table_view.sql.jinja2
│       │   └── refresh_table_view.sql.jinja2
│       └── actions/
│           └── refresh_table_view.sql.jinja2
└── entities/
    ├── tenant/
    ├── common/
    ├── catalog/
    └── management/
```

---

## Next Steps for PrintOptim

### 1. Review
- Read `SPECQL_TABLE_VIEWS_QUICK_REFERENCE.md` (10 min)
- Look at `specql/entities/examples/review_with_table_views.yaml` (5 min)

### 2. Design
- Identify which entities need denormalized views
- Plan which fields to include in each tv_
- Identify hot-path columns for performance

### 3. Implement
- Add `table_views` block to entity YAML files
- Run SpecQL generators
- Test mutations and queries

### 4. Optimize
- Monitor query performance
- Add columns to `extra_filter_columns` as needed
- Adjust `include_relations` based on usage patterns

---

## Learning Path

### Beginner (15 minutes)
1. Read: SPECQL_TABLE_VIEWS_QUICK_REFERENCE.md
2. View: specql/entities/examples/review_with_table_views.yaml
3. Try: Add simple `table_views` block to one entity

### Intermediate (45 minutes)
1. Read: SPECQL_TABLE_VIEWS_ANALYSIS.md (sections 1-4)
2. Study: specql/docs/architecture/CQRS_TABLE_VIEWS_IMPLEMENTATION.md
3. Review: AST models and schema generator code

### Advanced (2 hours)
1. Read: Full SPECQL_TABLE_VIEWS_ANALYSIS.md
2. Study: All source files (ast_models, generators, templates)
3. Review: All tests (unit + integration)
4. Understand: FraiseQL integration and annotations

---

## Reference

### Configuration Examples

**Minimal (auto-generate)**:
```yaml
table_views:
  mode: auto
```

**With field selection**:
```yaml
table_views:
  mode: auto
  include_relations:
    - entity_name: Organization
      fields: [name, code]
```

**With performance tuning**:
```yaml
table_views:
  mode: auto
  include_relations:
    - entity_name: Organization
      fields: [name, code]
  extra_filter_columns:
    - email
    - created_at
```

**Nested relations**:
```yaml
table_views:
  mode: auto
  include_relations:
    - entity_name: Book
      fields: [title, isbn]
      include_relations:
        - entity_name: Publisher
          fields: [name, country]
```

**Force generation (no FKs)**:
```yaml
table_views:
  mode: force
  extra_filter_columns:
    - created_at
```

**Disable generation (write-heavy)**:
```yaml
table_views:
  mode: disable
```

---

## Support & Questions

For questions about:
- **YAML syntax**: See SPECQL_TABLE_VIEWS_QUICK_REFERENCE.md
- **Architecture**: See SPECQL_TABLE_VIEWS_ANALYSIS.md
- **Performance**: See "Two-Tier Filtering Strategy" section
- **GraphQL**: See specql/docs/reference/fraiseql/TV_ANNOTATIONS.md
- **Implementation**: See specql/src source code

---

**Document Created**: 2025-11-10
**Last Updated**: 2025-11-10
**Status**: Complete and Production-Ready
