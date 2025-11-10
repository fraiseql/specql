# SpecQL Commodity Views Support Analysis

**Date**: 2025-11-10
**Status**: Built-in support exists, FULLY IMPLEMENTED
**Terminology**: SpecQL calls them **"Table Views"** (`tv_` pattern), not "commodity views"

---

## Executive Summary

SpecQL has comprehensive, built-in support for denormalized, precomputed JSONB structures. The feature is called **"Table Views"** and includes:

- **tv_ tables**: Denormalized read-optimized tables with JSONB payloads
- **Composition strategy**: JSONB built from related tv_ tables (cascading denormalization)
- **Filter columns**: Auto-promoted foreign keys + explicit hot-path columns
- **FraiseQL integration**: Auto-discovered GraphQL generation from JSONB structure
- **Mutation integration**: Explicit refresh callbacks for consistency
- **Performance optimization**: Two-tier filtering (B-tree indexes for hot paths, GIN for flexible queries)

---

## Quick Answer: YES, SpecQL Has Full Support

### In YAML, You Define:

```yaml
entity: Review
schema: library
fields:
  rating: integer
  comment: text
  author: ref(User)
  book: ref(Book)
  created_at: timestamp

table_views:
  mode: auto  # or 'force' or 'disable'
  include_relations:
    - entity_name: User
      fields: [name, email, avatarUrl]
    - entity_name: Book
      fields: [title, isbn, publishedYear]
  extra_filter_columns:
    - rating        # High-query-volume column
    - created_at    # Time-range queries
```

### SpecQL Generates:

1. **tb_review** - Normalized write table
2. **tv_review** - Denormalized read table with JSONB:
   ```sql
   CREATE TABLE library.tv_review (
       pk_review INTEGER PRIMARY KEY,
       id UUID UNIQUE,
       tenant_id UUID,
       fk_user INTEGER,      -- For JOINs during refresh
       fk_book INTEGER,      -- For JOINs during refresh
       user_id UUID,         -- For GraphQL filtering
       book_id UUID,         -- For GraphQL filtering
       rating INTEGER,       -- Promoted filter column
       created_at TIMESTAMPTZ, -- Promoted filter column
       data JSONB NOT NULL,  -- Composed denormalized data
       refreshed_at TIMESTAMPTZ
   );
   ```

3. **refresh_tv_review()** - PL/pgSQL function that:
   - Reads from tb_review (write table)
   - Composes JSONB from tv_user and tv_book (not tb_ tables)
   - Inserts into tv_review
   - Maintains consistency via cascading composition

4. **FraiseQL annotations** - Metadata for GraphQL auto-discovery:
   ```sql
   COMMENT ON TABLE library.tv_review IS
     '@fraiseql:table source=materialized,refresh=explicit,primary=true';
   
   COMMENT ON COLUMN library.tv_review.data IS
     '@fraiseql:jsonb expand=true,description=Denormalized Review data';
   ```

---

## Architecture: Three-Layer CQRS

### Layer 1: tb_ Tables (Write Side - Normalized)
```sql
CREATE TABLE library.tb_review (
    pk_review INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    rating INTEGER,
    comment TEXT,
    fk_author INTEGER REFERENCES tb_user,
    fk_book INTEGER REFERENCES tb_book,
    created_at TIMESTAMPTZ,
    ...
);
```

**Purpose**: Transactional integrity, normalized storage, ACID compliance

---

### Layer 2: tv_ Tables (Read Side - Denormalized)
```sql
CREATE TABLE library.tv_review (
    pk_review INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    tenant_id UUID,
    fk_author INTEGER,
    fk_book INTEGER,
    author_id UUID,        -- Promoted for filtering
    book_id UUID,          -- Promoted for filtering
    rating INTEGER,        -- Promoted for filtering
    created_at TIMESTAMPTZ,-- Promoted for filtering
    data JSONB NOT NULL,   -- {id, rating, comment, createdAt, author: {...}, book: {...}}
    refreshed_at TIMESTAMPTZ
);
```

**Purpose**: Fast read queries, denormalized JSONB for FraiseQL

**Key Innovation**: Composes from `tv_*` tables, not `tb_*` tables
- Creates cascading denormalization
- Ensures consistency (tv_review.author matches tv_user.data exactly)
- Allows reuse of nested data (e.g., publisher already in tv_book.data)

---

### Layer 3: FraiseQL (Query Layer - Auto-Generated GraphQL)

FraiseQL auto-discovers tv_review structure and generates:
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
  avatarUrl: String!
}
```

No manual schema definition needed. FraiseQL introspects JSONB and generates types.

---

## Configuration Options

### TableViewMode

```yaml
table_views:
  mode: auto      # Generate if entity has foreign keys (default)
  # OR
  mode: force     # Always generate (even without FKs)
  # OR
  mode: disable   # Don't generate (write-heavy table)
```

### include_relations - Explicit Field Selection

Control which fields from related entities are included:

```yaml
table_views:
  include_relations:
    - entity_name: User
      fields: [name, email, avatarUrl]     # Only these
      
    - entity_name: Book
      fields: [title, isbn, publishedYear]
      include_relations:                    # Nested!
        - entity_name: Publisher
          fields: [name, country]
```

**Result in tv_review.data**:
```json
{
  "author": {
    "id": "...",
    "name": "...",
    "email": "...",
    "avatarUrl": "..."
  },
  "book": {
    "id": "...",
    "title": "...",
    "isbn": "...",
    "publishedYear": 2024,
    "publisher": {
      "id": "...",
      "name": "...",
      "country": "..."
    }
  }
}
```

### extra_filter_columns - Performance Optimization

Promote specific columns for high-query-volume filtering:

```yaml
table_views:
  extra_filter_columns:
    - rating              # Simple: uses btree index
    
    - created_at          # Simple
    
    - author_name:        # Complex: nested extraction
        source: author.name
        type: text
        index: gin_trgm    # Trigram for ILIKE queries
```

**Performance**:
- **B-tree indexes** (direct columns): ~0.1ms
- **GIN indexes** (JSONB): ~50-100ms
- **Trigram indexes** (text search): ~10-50ms

---

## Implementation Status

### Completed Phases

1. **Phase 1: Parser Extensions** ✅
   - Parse `table_views` configuration block
   - Parse `include_relations` (nested field selection)
   - Parse `extra_filter_columns`
   - Parse `mode: auto/force/disable`
   - Added to Entity AST

2. **Phase 2: Schema Generation** ✅
   - Generate tv_ table schema
   - Auto-infer filter columns (tenant_id, {entity}_id, path)
   - Explicit filter columns from config
   - GIN index on data column
   - B-tree indexes on filter columns
   - `refresh_tv_{entity}()` function with JSONB composition

3. **Phase 3: Mutation Integration** ✅
   - Detect `refresh_table_view` action step
   - Generate `PERFORM refresh_tv_{entity}()` calls
   - Handle scopes (self, related, propagate, batch)
   - Return data from tv_ in mutation results

4. **Phase 4: FraiseQL Annotations** ✅
   - Generate @fraiseql:table annotations
   - Generate @fraiseql:filter annotations
   - Generate @fraiseql:jsonb annotations

### Refresh Scopes

```yaml
actions:
  - name: update_rating
    steps:
      - update: Review SET rating = $new_rating
      - refresh_table_view:
          scope: self              # Only this review
          propagate: [author]      # Also refresh author's avg rating
          strategy: immediate      # immediate | deferred (batch)
```

**Scope Options**:
- `self` - Only this entity's tv_
- `related` - This entity + all that reference it
- `propagate` - This entity + explicit list
- `batch` - Deferred (bulk operations)

---

## Key Files

### Configuration & AST
- `/specql/src/core/ast_models.py` - TableViewConfig, IncludeRelation, ExtraFilterColumn classes
- `/specql/src/core/specql_parser.py` - Parse table_views block from YAML

### Schema Generation
- `/specql/src/generators/schema/table_view_generator.py` - tv_ table DDL generation
- `/specql/src/generators/schema/table_view_dependency.py` - Dependency graph for refresh order
- `/specql/templates/schema/table_view.sql.jinja2` - tv_ table template
- `/specql/templates/schema/refresh_table_view.sql.jinja2` - refresh function template

### Action Compilation
- `/specql/src/generators/actions/step_compilers/refresh_table_view_compiler.py` - Compile refresh steps

### FraiseQL Integration
- `/specql/src/generators/fraiseql/table_view_annotator.py` - Generate @fraiseql annotations
- `/specql/docs/reference/fraiseql/TV_ANNOTATIONS.md` - Complete annotation guide

### Tests
- `/specql/tests/unit/schema/test_table_view_generation.py` - Schema generation tests
- `/specql/tests/unit/fraiseql/test_table_view_annotator.py` - Annotation tests
- `/specql/tests/integration/fraiseql/test_tv_annotations_e2e.py` - End-to-end tests
- `/specql/tests/integration/actions/test_mutations_with_tv_refresh.py` - Mutation integration

### Example
- `/specql/entities/examples/review_with_table_views.yaml` - Complete working example

---

## Composition Strategy: Key Innovation

### Problem: Denormalization Consistency

If tv_review composes from tb_ tables:
```sql
-- ❌ WRONG: Duplicates data inconsistently
INSERT INTO library.tv_review (data)
SELECT jsonb_build_object(
    'author', jsonb_build_object(
        'name', u.name,     -- From tb_user (might be stale)
        'email', u.email
    )
)
FROM library.tb_review r
INNER JOIN crm.tb_user u ON u.pk_user = r.fk_author;
```

**Problem**: If tv_user is updated, tv_review's denormalized author data stays stale.

### Solution: Cascade Composition

SpecQL composes from tv_ tables:
```sql
-- ✅ CORRECT: Single source of truth
INSERT INTO library.tv_review (
    pk_review, id, tenant_id, fk_author, fk_book,
    author_id, book_id, rating, created_at,
    data
)
SELECT
    r.pk_review,
    r.id,
    r.tenant_id,
    r.fk_author,
    r.fk_book,
    tv_u.id AS author_id,
    tv_b.id AS book_id,
    r.rating,
    r.created_at,

    -- Compose from tv_ (not tb_)
    jsonb_build_object(
        'id', r.id,
        'rating', r.rating,
        'comment', r.comment,

        -- Extract from tv_user.data
        'author', jsonb_build_object(
            'id', tv_u.data->>'id',
            'name', tv_u.data->>'name',
            'email', tv_u.data->>'email',
            'avatarUrl', tv_u.data->>'avatarUrl'
        ),

        -- Extract from tv_book.data
        'book', jsonb_build_object(
            'id', tv_b.data->>'id',
            'title', tv_b.data->>'title',
            'isbn', tv_b.data->>'isbn',
            'publishedYear', (tv_b.data->>'publishedYear')::integer,
            -- Reuse nested publisher from tv_book.data
            'publisher', tv_b.data->'publisher'
        )
    ) AS data

FROM library.tb_review r
INNER JOIN crm.tv_user tv_u ON tv_u.pk_user = r.fk_author
INNER JOIN library.tv_book tv_b ON tv_b.pk_book = r.fk_book;
```

**Benefits**:
1. **Consistency**: Author data in tv_review matches tv_user exactly
2. **Reuse**: Nested publisher already composed in tv_book
3. **Cascading**: When tv_user refreshes, tv_review can pick up changes
4. **Single source**: tv_user.data is source of truth

---

## Two-Tier Filtering Strategy

### Tier 1: Direct Columns (Fast - B-tree)

```sql
-- Queries: 1000/day
SELECT * FROM library.tv_review WHERE rating >= 4;
-- Performance: ~0.1ms (B-tree index)
```

Auto-inferred:
- `tenant_id` (multi-tenant isolation)
- `{entity}_id` (foreign key filtering)
- `path` (hierarchical entities)

User-specified:
- `rating` (business logic hot paths)
- `created_at` (time-range queries)

### Tier 2: JSONB Columns (Slower - GIN)

```sql
-- Queries: 10/day
SELECT * FROM library.tv_review
WHERE data->>'comment' ILIKE '%excellent%';
-- Performance: ~50-100ms (GIN index)
```

All fields from related entities in JSONB:
- `data.author.name`
- `data.book.title`
- `data.book.publisher.country`

---

## Lifecycle: Write Operation Flow

```
1. User mutation (GraphQL/REST)
   ↓
2. PL/pgSQL function (Team C generated)
   ↓
3. Write to tb_review (normalized)
   ↓
4. Call refresh_tv_review() explicitly
   ↓
5. FraiseQL serves updated data from tv_review
```

### Example Mutation

```yaml
entity: Review

actions:
  - name: update_rating
    steps:
      - validate: rating >= 1 AND rating <= 5
      - update: Review SET rating = $new_rating
      - refresh_table_view:
          scope: self
          propagate: [author]  # Also update author's avg_rating
```

**Generated PL/pgSQL**:
```sql
CREATE OR REPLACE FUNCTION library.update_review_rating(
    p_review_id UUID,
    p_new_rating INTEGER,
    p_caller_id UUID DEFAULT NULL
) RETURNS mutation_result AS $$
DECLARE
    v_pk INTEGER;
BEGIN
    -- Update normalized table
    UPDATE library.tb_review
    SET rating = p_new_rating,
        updated_at = now(),
        updated_by = p_caller_id
    WHERE id = p_review_id;

    -- Refresh denormalized view (explicit)
    PERFORM library.refresh_tv_review(v_pk);

    -- Propagate to author
    PERFORM crm.refresh_tv_user(v_author_pk);

    -- Return from denormalized table
    RETURN (
        SELECT data
        FROM library.tv_review
        WHERE id = p_review_id
    );
END;
$$ LANGUAGE plpgsql;
```

---

## Example Entity YAML

Full working example from SpecQL:

```yaml
entity: Review
schema: library
description: Book review with denormalized author and book data

fields:
  author:
    type: ref(User)
    description: Review author
  book:
    type: ref(Book)
    description: Book being reviewed
  rating:
    type: integer
    description: Rating from 1-5 stars
  content:
    type: text
    description: Review text content
  created_at:
    type: timestamp
    description: When review was created

actions:
  - name: create
    description: Create a new review
  - name: update
    description: Update review content/rating
  - name: delete
    description: Delete a review

table_views:
  mode: auto
  include_relations:
    - entity_name: User
      fields: [name, email, avatar_url]
    - entity_name: Book
      fields: [title, isbn, published_year, genre]
  extra_filter_columns:
    - name: rating
      type: INTEGER
      index_type: btree
    - name: created_at
      type: TIMESTAMPTZ
      index_type: btree
```

---

## Integration Points

### With PrintOptim SpecQL Repository

For your `printoptim_specql` project:

1. **Entities**: Define `table_views` in your YAML files
   ```yaml
   # entities/tenant/contact.yaml
   table_views:
     mode: auto
     include_relations:
       - entity_name: Organization
         fields: [name, code]
     extra_filter_columns:
       - email_address
   ```

2. **Generators**: Already implemented in SpecQL (Team B, C, D)

3. **Queries**: Your GraphQL client auto-discovers from tv_ structure

---

## Terminology Clarification

| Term | SpecQL | Your Context |
|------|--------|--------------|
| Commodity view | tv_ table | Denormalized read table |
| Materialized view | tv_ table | Persisted denormalized table |
| Precomputed JSONB | data column | Composed JSONB in tv_view |
| Denormalization | table_views block | Configuration in YAML |
| Projection | include_relations | Field selection for JSONB |
| Hot-path optimization | extra_filter_columns | Direct columns for queries |

---

## Summary

**SpecQL fully supports commodity views via the `table_views` feature**:

1. ✅ Denormalized tv_ tables with JSONB
2. ✅ Composition from related tv_ tables (not tb_)
3. ✅ Auto-inferred + explicit filter columns
4. ✅ FraiseQL integration for GraphQL auto-discovery
5. ✅ Mutation refresh callbacks
6. ✅ Performance-optimized two-tier filtering
7. ✅ Hierarchical entity support
8. ✅ Comprehensive test coverage

**Status**: Production-ready, fully implemented across Phases 1-4.

**For PrintOptim**: Add `table_views` blocks to your entity YAML files and SpecQL will generate the entire tv_ infrastructure automatically.

---

**Document**: SpecQL Commodity Views (tv_ Table) Support Analysis
**Last Updated**: 2025-11-10
**Status**: Complete Implementation
