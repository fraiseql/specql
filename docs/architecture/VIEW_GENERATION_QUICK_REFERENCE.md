# SpecQL View Generation - Quick Reference

## Files to Know

| File | Purpose | Key Methods |
|------|---------|-------------|
| `src/generators/schema/table_view_generator.py` | Generate DDL, indexes, refresh functions | `generate_schema()` |
| `src/generators/schema/table_view_dependency.py` | Topological sort for generation order | `get_generation_order()` |
| `src/generators/fraiseql/table_view_annotator.py` | FraiseQL COMMENT statements | `generate_annotations()` |
| `src/generators/schema_orchestrator.py` | Orchestrate all TV_ generation | `generate_table_views()` |
| `src/cli/orchestrator.py` | CLI orchestrator | `generate_from_files()` (lines 424-437) |
| `src/cli/generate.py` | CLI command | `entities()` (lines 74-291) |
| `src/core/ast_models.py` | AST models | `TableViewConfig`, `IncludeRelation`, `ExtraFilterColumn` |

## Current File Output

```
├─ db/schema/00_foundation/000_app_foundation.sql
├─ db/schema/10_tables/{entity}.sql
├─ db/schema/20_helpers/{entity}_helpers.sql
├─ db/schema/30_functions/{action_name}.sql
└─ 200_table_views.sql                          ← ALL TV_ IN ONE FILE
```

## Key Entry Points for Changes

### To Split TV_ by Entity:

1. **Modify `TableViewGenerator`** (line 13-40)
   - Split `generate_schema()` into separate methods
   - Return DDL, indexes, refresh function separately

2. **Modify `SchemaOrchestrator.generate_table_views()`** (lines 219-258)
   - Return list of structured outputs instead of single string
   - One output per entity: DDL + indexes + refresh + metadata

3. **Modify `CLIOrchestrator.generate_from_files()`** (lines 424-437)
   - Write multiple files instead of one
   - Follow hierarchy: `db/schema/15_table_views/{entity}_tv.sql`

### CLI Flags to Support View Generation

```bash
specql generate entities/*.yaml --include-tv
# Generates with default (monolithic) file structure

specql generate entities/*.yaml --include-tv --table-views-format=hierarchical
# Would generate per-entity files (future)
```

## YAML Configuration

### Entity with Table Views

```yaml
entity: Post
schema: blog

fields:
  title: text
  author: ref(User)
  category: ref(Category)

table_views:
  mode: auto                    # auto | force | disable
  include_relations:
    - entity_name: author
      fields: [name, email]     # Select specific fields
  extra_filter_columns:
    - name: category_name
      source: category.name     # Extract from relation
      type: TEXT
      index_type: btree

actions:
  - name: create_post
    steps:
      - insert: Post
      - refresh_table_view: Post
```

## How Views Are Generated

### Generation Order (Topological Sort)

```
User → Post → Comment
  ↓      ↓       ↓
tv_user tv_post tv_comment

Dependencies respected: parent entities created before child entities
```

### What Each TV_ Contains

```sql
CREATE TABLE blog.tv_post (
    pk_post INTEGER PRIMARY KEY,         -- Trinity pattern
    id UUID NOT NULL UNIQUE,             -- Entity UUID
    tenant_id UUID NOT NULL,             -- Multi-tenant
    fk_author INTEGER,                   -- FK for JOIN
    author_id UUID,                      -- UUID for filter
    fk_category INTEGER,                 -- Another FK
    category_id UUID,                    -- Another UUID FK
    path LTREE,                          -- If hierarchical
    category_name TEXT,                  -- Extra filter column (indexed)
    data JSONB NOT NULL,                 -- All entity + relation data
    refreshed_at TIMESTAMPTZ DEFAULT now()
);
```

### Refresh Function

```sql
CREATE OR REPLACE FUNCTION blog.refresh_tv_post(
    p_pk_post INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    DELETE FROM blog.tv_post
    WHERE p_pk_post IS NULL OR pk_post = p_pk_post;
    
    INSERT INTO blog.tv_post (...)
    SELECT
        base.pk_post,
        base.id,
        base.tenant_id,
        base.fk_author,
        tv_user.id AS author_id,         -- From tv_ table (not tb_!)
        base.fk_category,
        tv_category.id AS category_id,
        base.category_name,
        jsonb_build_object(               -- Compose JSONB
            'title', base.title,
            'author', tv_user.data,       -- Include related entity
            'category', tv_category.data,
        ) AS data,
        now()
    FROM blog.tb_post base
    LEFT JOIN blog.tv_user tv_user ON tv_user.pk_user = base.fk_author
    LEFT JOIN blog.tv_category tv_category ON tv_category.pk_category = base.fk_category
    WHERE base.deleted_at IS NULL
      AND (p_pk_post IS NULL OR base.pk_post = p_pk_post);
END;
$$ LANGUAGE plpgsql;
```

## FraiseQL Annotations

Each TV_ table gets COMMENT annotations:

```sql
COMMENT ON TABLE blog.tv_post IS
  '@fraiseql:table source=materialized,refresh=explicit,primary=true';

COMMENT ON COLUMN blog.tv_post.pk_post IS
  '@fraiseql:field internal=true';

COMMENT ON COLUMN blog.tv_post.author_id IS
  '@fraiseql:filter type=UUID,relation=User,index=btree';

COMMENT ON COLUMN blog.tv_post.data IS
  '@fraiseql:jsonb expand=true';
```

This tells FraiseQL how to introspect and generate GraphQL schema.

## Framework Defaults

| Framework | include_tv | Reason |
|-----------|-----------|--------|
| fraiseql | TRUE | GraphQL queries need optimized views |
| django | FALSE | ORM doesn't use TV_ |
| rails | FALSE | ActiveRecord doesn't use TV_ |
| prisma | FALSE | Prisma doesn't use TV_ |

## Testing

### Run TV_ Tests

```bash
# Unit tests for DDL, indexes, refresh functions
pytest tests/unit/schema/test_table_view_generation.py -v

# Unit tests for FraiseQL annotations
pytest tests/unit/fraiseql/test_table_view_annotator.py -v

# E2E annotation tests
pytest tests/integration/fraiseql/test_tv_annotations_e2e.py -v

# All view-related tests
pytest -k "table_view" -v
```

## Design Principles

1. **CQRS Pattern**: Write to `tb_*`, read from `tv_*`
2. **Denormalization**: TV_ contains entity + all relations as JSONB
3. **TV_ Joins TV_**: Refresh functions JOIN to tv_ tables, not tb_
4. **Dependency Order**: Generated in topological order (dependencies first)
5. **GraphQL Ready**: FraiseQL annotations enable auto-schema discovery
6. **Flexible Control**: auto | force | disable modes for fine-grained control

## Common Tasks

### Add Extra Filter Column

```yaml
table_views:
  extra_filter_columns:
    - name: status_text
      source: status           # From entity field
      type: TEXT
      index_type: btree        # For performance
```

### Include Only Specific Fields from Relation

```yaml
table_views:
  include_relations:
    - entity_name: author      # Must match field name
      fields: [name, email]    # Only these fields
```

### Force Generation Even Without FK

```yaml
table_views:
  mode: force                  # Generate even if no refs
```

### Skip TV_ Generation

```yaml
table_views:
  mode: disable                # Don't generate tv_
```

---

**Reference**: See `/home/lionel/code/specql/docs/architecture/VIEW_GENERATION_ARCHITECTURE.md` for comprehensive details.
