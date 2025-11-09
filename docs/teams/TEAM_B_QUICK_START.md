# Team B: Quick Start Guide - Phase 9 Table Views

**Date**: 2025-11-09
**Status**: 🟢 READY TO START - Team A has unblocked you!

---

## 🎯 Your Mission

Generate `tv_{entity}` tables and `refresh_tv_{entity}()` functions from the parsed `table_views` configuration that Team A just delivered.

---

## 📦 What Team A Delivered

### **1. Parsed AST Available**

You now have access to `entity.table_views` with this structure:

```python
from src.core.specql_parser import SpecQLParser

parser = SpecQLParser()
entity = parser.parse(yaml_content)

# Check if tv_ should be generated
if entity.should_generate_table_view:
    tv_config = entity.table_views  # Can be None (auto mode)

    # Check mode
    if tv_config:
        mode = tv_config.mode  # TableViewMode.AUTO | FORCE | DISABLE

    # Get explicit relations
    if tv_config and tv_config.has_explicit_relations:
        for rel in tv_config.include_relations:
            print(f"Relation: {rel.entity_name}")
            print(f"Fields: {rel.fields}")
            print(f"Nested: {rel.include_relations}")

    # Get filter columns
    if tv_config:
        for col in tv_config.extra_filter_columns:
            print(f"Filter column: {col.name}")
            print(f"  Source: {col.source}")  # e.g., "author.name"
            print(f"  Type: {col.type}")
            print(f"  Index: {col.index_type}")  # btree | gin | gin_trgm
```

### **2. Test Coverage**

Team A created 11 tests covering all edge cases. You can use these as examples:

**Location**: `tests/unit/core/test_table_views_parsing.py`

**Key Examples**:
- `test_parse_minimal_table_views` - Simplest case (just mode)
- `test_parse_include_relations` - Flat field selection
- `test_parse_nested_include_relations` - Multi-level nesting
- `test_parse_extra_filter_columns_advanced` - Performance optimization
- `test_complete_table_views_example` - Full integration

---

## 🏗️ What You Need to Generate

### **1. tv_ Table DDL**

For an entity with `table_views` config, generate:

```sql
CREATE TABLE library.tv_review (
    -- Primary key (same as tb_review)
    pk_review INTEGER PRIMARY KEY,

    -- Identifiers (for filtering)
    id UUID NOT NULL,
    review_id TEXT NOT NULL,
    tenant_id TEXT,
    path TEXT,  -- If hierarchical

    -- Foreign keys (for JOINs during refresh)
    fk_author INTEGER REFERENCES core.tb_user(pk_user),
    fk_book INTEGER REFERENCES library.tb_book(pk_book),
    author_id UUID,  -- For GraphQL filtering
    book_id UUID,    -- For GraphQL filtering

    -- Auto-inferred filter columns (high-volume queries)
    -- These come from tb_review directly

    -- Explicit filter columns (from extra_filter_columns)
    rating INTEGER,           -- From: extra_filter_columns: [rating]
    review_date TIMESTAMPTZ,  -- From: extra_filter_columns: [review_date]

    -- Denormalized JSONB data
    data JSONB NOT NULL,

    -- Metadata
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

-- B-tree indexes (exact match, range queries - 100-500x faster)
CREATE INDEX idx_tv_review_tenant ON library.tv_review(tenant_id);
CREATE INDEX idx_tv_review_author_id ON library.tv_review(author_id);
CREATE INDEX idx_tv_review_rating ON library.tv_review(rating);
CREATE INDEX idx_tv_review_review_date ON library.tv_review(review_date);

-- GIN index (JSONB queries - slower but flexible)
CREATE INDEX idx_tv_review_data ON library.tv_review USING GIN(data);
```

### **2. refresh_tv_review() Function**

Generate a function that composes JSONB from `tv_` tables (NOT `tb_` tables!):

```sql
CREATE OR REPLACE FUNCTION library.refresh_tv_review(p_pk INTEGER)
RETURNS void AS $$
BEGIN
    INSERT INTO library.tv_review (
        pk_review, id, review_id, tenant_id,
        fk_author, fk_book, author_id, book_id,
        rating, review_date,  -- Filter columns
        data
    )
    SELECT
        r.pk_review,
        r.id,
        r.identifier AS review_id,
        r.tenant_id,
        r.fk_author,
        r.fk_book,
        u.id AS author_id,
        b.id AS book_id,

        -- Filter columns
        r.rating,
        r.review_date,

        -- Compose JSONB from tv_ tables (cascading denormalization!)
        jsonb_build_object(
            '__typename', 'Review',
            'id', r.id,
            'rating', r.rating,
            'comment', r.comment,
            'reviewDate', r.review_date,

            -- From tv_user (NOT tb_user!)
            'author', jsonb_build_object(
                '__typename', 'User',
                'id', tv_user.data->>'id',
                'name', tv_user.data->>'name',
                'email', tv_user.data->>'email'
            ),

            -- From tv_book (which already has publisher nested!)
            'book', jsonb_build_object(
                '__typename', 'Book',
                'id', tv_book.data->>'id',
                'title', tv_book.data->>'title',
                'isbn', tv_book.data->>'isbn',
                'publisher', tv_book.data->'publisher'  -- Already composed in tv_book!
            )
        ) AS data
    FROM library.tb_review r
    INNER JOIN core.tv_user ON tv_user.pk_user = r.fk_author
    INNER JOIN library.tv_book ON tv_book.pk_book = r.fk_book
    WHERE r.pk_review = p_pk
    ON CONFLICT (pk_review) DO UPDATE SET
        data = EXCLUDED.data,
        rating = EXCLUDED.rating,
        review_date = EXCLUDED.review_date,
        refreshed_at = now();
END;
$$ LANGUAGE plpgsql;
```

**Key Points**:
- ✅ Compose from `tv_user` and `tv_book` (NOT `tb_user`/`tb_book`)
- ✅ This creates cascading denormalization (publisher is already in `tv_book.data`)
- ✅ Include only fields specified in `include_relations.fields`
- ✅ Use `ON CONFLICT ... DO UPDATE` for upsert behavior

---

## 🎯 Implementation Steps

### **Phase 9.1: Basic tv_ Table Generation** (Day 1-2)

1. Create `src/generators/schema/table_view_generator.py`
2. Implement `generate_tv_table()`:
   - Auto-infer filter columns (tenant_id, {entity}_id, path)
   - Add explicit filter columns from `extra_filter_columns`
   - Generate B-tree indexes for filter columns
   - Generate GIN index for `data` JSONB

**Test**: Generate `tv_review` table DDL and verify schema

### **Phase 9.2: Refresh Function Generation** (Day 3-5)

1. Implement `generate_refresh_function()`:
   - Build `jsonb_build_object()` from `include_relations`
   - Compose from `tv_` tables (cascading)
   - Handle nested relations recursively
   - Use `ON CONFLICT` for upsert

**Test**: Generate `refresh_tv_review()` and verify JSONB structure

### **Phase 9.3: Dependency Ordering** (Day 6-7)

1. Topological sort of entities by FK dependencies
2. Generate tv_ tables in correct order
3. Ensure `tv_user` and `tv_book` exist before `tv_review`

**Test**: Generate multiple related entities and verify order

### **Phase 9.4: Integration Testing** (Day 8)

1. End-to-end: SpecQL → tv_ table + refresh function
2. Execute in test database
3. Verify JSONB composition works
4. Performance validation (B-tree vs GIN)

---

## 📚 Key References

### **Documentation**
- `docs/architecture/CQRS_TABLE_VIEWS_IMPLEMENTATION.md` - Complete architecture
- `docs/teams/TEAM_B_PHASE_9_TABLE_VIEWS.md` - Your detailed implementation plan
- `docs/teams/TEAM_A_COMPLETION_STATUS.md` - What Team A delivered

### **Code Examples**
- `tests/unit/core/test_table_views_parsing.py` - See how table_views is parsed
- `src/core/ast_models.py` lines 36-115 - AST model definitions

### **Test Command**
```bash
# Run your Team B tests
make teamB-test

# Run all tests (including Team A)
make test
```

---

## 🚨 Critical Decisions

### **1. Compose from tv_ tables, NOT tb_ tables**

❌ **WRONG**:
```sql
-- Don't do this!
SELECT jsonb_build_object('author', jsonb_build_object('name', tb_user.name))
FROM tb_review r
INNER JOIN tb_user ON tb_user.pk_user = r.fk_author
```

✅ **CORRECT**:
```sql
-- Do this instead!
SELECT jsonb_build_object('author', tv_user.data)
FROM tb_review r
INNER JOIN tv_user ON tv_user.pk_user = r.fk_author
```

**Why**: Cascading denormalization. If `tv_user` has nested company data, it's already composed in `tv_user.data`. Reusing it ensures consistency.

### **2. Filter Columns = B-tree, JSONB = GIN**

- **B-tree**: For exact match and range queries (100-500x faster)
  - Auto: tenant_id, {entity}_id, path
  - Explicit: extra_filter_columns
- **GIN**: For JSONB queries (slower but flexible)
  - Always on `data` column

### **3. Field Selection**

If `include_relations` specifies `fields: [name, email]`:
```sql
-- Only include specified fields
jsonb_build_object(
    'name', tv_user.data->>'name',
    'email', tv_user.data->>'email'
    -- NOT all fields from tv_user.data!
)
```

---

## ✅ Acceptance Criteria

- [ ] Generate tv_ table DDL with correct schema
- [ ] Auto-infer filter columns (tenant_id, {entity}_id, path)
- [ ] Generate explicit filter columns from `extra_filter_columns`
- [ ] Generate refresh functions that compose from tv_ tables
- [ ] Generate correct indexes (B-tree + GIN)
- [ ] Handle dependency ordering (topological sort)
- [ ] All tests pass (no regressions)
- [ ] Performance validation (B-tree 100x faster than GIN)

---

## 🚀 You're Ready!

Team A has delivered a clean, tested AST. You have:

- ✅ Access to `entity.table_views` configuration
- ✅ Properties: `should_generate_table_view`, `has_foreign_keys`
- ✅ 11 test examples to learn from
- ✅ Complete architecture documentation

**Next Command**:
```bash
# Start with Day 1 work
mkdir -p src/generators/schema
touch src/generators/schema/table_view_generator.py
make teamB-test  # Create your first test!
```

**Remember**: Follow TDD (RED → GREEN → REFACTOR → QA)

Good luck! 🎉

---

**Status**: 🟢 READY FOR TEAM B
**Unblocked By**: Team A (2025-11-09)
**Estimated Duration**: 7-8 days (per original plan)
