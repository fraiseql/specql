# CQRS Table Views Implementation - Complete Architecture

**Status**: 🔴 APPROVED - Ready for Implementation
**Date**: 2025-11-09
**Impact**: HIGH - New read-optimized layer for FraiseQL integration

---

## 📋 Executive Summary

SpecQL implements a **three-layer CQRS architecture**:

1. **tb_ tables** (Write Side) - Normalized storage for transactional integrity
2. **tv_ tables** (Read Side) - Denormalized JSONB for FraiseQL exposure
3. **FraiseQL** (Query Layer) - Auto-generates GraphQL from tv_ structure

**Key Innovation**: `tv_` tables compose JSONB data from related `tv_` tables (not `tb_` tables), creating a cascading denormalization strategy.

---

## 🎯 Three-Layer Architecture

### **Layer 1: tb_ Tables (Write Side - Normalized)**

**Purpose**: Transactional integrity, normalized storage, write operations

**Example**:
```sql
CREATE TABLE library.tb_review (
    -- Trinity pattern
    pk_review INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    tenant_id UUID NOT NULL,
    identifier TEXT UNIQUE,

    -- Business fields
    rating INTEGER NOT NULL,
    comment TEXT,

    -- Foreign keys (normalized)
    fk_author INTEGER NOT NULL REFERENCES crm.tb_user(pk_user),
    fk_book INTEGER NOT NULL REFERENCES library.tb_book(pk_book),

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    deleted_by UUID
);
```

**Characteristics**:
- ✅ Normalized (3NF)
- ✅ Foreign key constraints
- ✅ Audit trail
- ✅ Soft delete support
- ✅ Trinity pattern (pk_*, id, identifier)

---

### **Layer 2: tv_ Tables (Read Side - Denormalized)**

**Purpose**: Expose denormalized data to FraiseQL in optimized JSONB format

**Example**:
```sql
CREATE TABLE library.tv_review (
    -- Primary identification
    pk_review INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,

    -- Foreign keys (INTEGER) for JOINs during refresh
    fk_author INTEGER NOT NULL,
    fk_book INTEGER NOT NULL,

    -- UUID foreign keys for external filtering
    author_id UUID NOT NULL,
    book_id UUID NOT NULL,

    -- Performance-optimized filter columns
    rating INTEGER,              -- Promoted for high-volume queries
    created_at TIMESTAMPTZ,      -- Promoted for date range queries

    -- Denormalized JSONB payload (FraiseQL reads this!)
    data JSONB NOT NULL,

    -- Metadata
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

-- Performance indexes
CREATE INDEX idx_tv_review_tenant ON library.tv_review(tenant_id);
CREATE INDEX idx_tv_review_author_id ON library.tv_review(author_id);
CREATE INDEX idx_tv_review_book_id ON library.tv_review(book_id);
CREATE INDEX idx_tv_review_rating ON library.tv_review(rating);  -- Hot path
CREATE INDEX idx_tv_review_created ON library.tv_review(created_at);  -- Hot path
CREATE INDEX idx_tv_review_data ON library.tv_review USING GIN(data);  -- JSONB queries
```

**tv_review.data structure**:
```jsonb
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "rating": 5,
  "comment": "Excellent book on PostgreSQL!",
  "createdAt": "2024-01-15T10:00:00Z",

  "author": {
    "id": "author-uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "avatarUrl": "https://example.com/avatar.jpg"
  },

  "book": {
    "id": "book-uuid",
    "title": "PostgreSQL Deep Dive",
    "isbn": "978-1234567890",
    "publishedYear": 2024,

    "publisher": {
      "id": "publisher-uuid",
      "name": "Tech Books Inc",
      "country": "USA"
    }
  }
}
```

**Characteristics**:
- ✅ Denormalized (flattened relationships)
- ✅ JSONB for flexible querying
- ✅ Promoted columns for high-performance filtering
- ✅ Composed from related tv_ tables
- ✅ No foreign key constraints (read-only)

---

### **Layer 3: FraiseQL (Auto-Generated GraphQL)**

**Purpose**: Auto-discover tv_ structure and generate GraphQL API

**FraiseQL Introspection**:
```sql
-- FraiseQL reads tv_review table
-- Discovers data JSONB structure
-- Auto-generates GraphQL types
```

**Auto-Generated GraphQL**:
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
  avatarUrl: String
}

type ReviewBook {
  id: UUID!
  title: String!
  isbn: String!
  publishedYear: Int!
  publisher: ReviewPublisher!
}

type ReviewPublisher {
  id: UUID!
  name: String!
  country: String!
}

type Query {
  # Uses tv_review directly (no JOINs!)
  review(id: UUID!): Review

  # Uses author_id index
  reviewsByAuthor(authorId: UUID!): [Review!]!

  # Uses book_id index
  reviewsByBook(bookId: UUID!): [Review!]!

  # Uses rating column (fast B-tree)
  reviewsWithRating(minRating: Int!): [Review!]!

  # Uses JSONB GIN index (slower but works)
  reviewsWithComment(search: String!): [Review!]!
}
```

**Characteristics**:
- ✅ Auto-generated from tv_ structure
- ✅ No manual schema definition
- ✅ Reads directly from tv_ (no JOINs)
- ✅ Can filter on any JSONB field
- ✅ Optimized queries on promoted columns

---

## 🔄 JSONB Composition Strategy

### **Key Innovation: Compose from tv_, not tb_**

**OLD Approach** (❌ Don't do this):
```sql
-- Refresh tv_review by JOINing tb_ tables
INSERT INTO library.tv_review (data)
SELECT
    jsonb_build_object(
        'author', jsonb_build_object(
            'name', u.name,      -- From tb_user
            'email', u.email     -- From tb_user
        ),
        'book', jsonb_build_object(
            'title', b.title     -- From tb_book
        )
    )
FROM library.tb_review r
INNER JOIN crm.tb_user u ON u.pk_user = r.fk_author
INNER JOIN library.tb_book b ON b.pk_book = r.fk_book;
```

**Problem**: Duplicates data, inconsistent with tv_user and tv_book

---

**NEW Approach** (✅ Composition):
```sql
-- Refresh tv_review by composing from tv_ tables
CREATE OR REPLACE FUNCTION library.refresh_tv_review(
    p_pk_review INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    DELETE FROM library.tv_review
    WHERE p_pk_review IS NULL OR pk_review = p_pk_review;

    INSERT INTO library.tv_review (
        pk_review, id, tenant_id,
        fk_author, fk_book,
        author_id, book_id,
        rating, created_at,  -- Promoted filter columns
        data
    )
    SELECT
        r.pk_review,
        r.id,
        r.tenant_id,
        r.fk_author,
        r.fk_book,
        tv_u.id AS author_id,  -- From tv_user
        tv_b.id AS book_id,    -- From tv_book
        r.rating,
        r.created_at,

        -- Compose JSONB from tv_ tables ✅
        jsonb_build_object(
            'id', r.id,
            'rating', r.rating,
            'comment', r.comment,
            'createdAt', r.created_at,

            -- Extract selected fields from tv_user.data
            'author', jsonb_build_object(
                'id', tv_u.data->>'id',
                'name', tv_u.data->>'name',
                'email', tv_u.data->>'email',
                'avatarUrl', tv_u.data->>'avatarUrl'
            ),

            -- Extract selected fields from tv_book.data
            'book', jsonb_build_object(
                'id', tv_b.data->>'id',
                'title', tv_b.data->>'title',
                'isbn', tv_b.data->>'isbn',
                'publishedYear', (tv_b.data->>'publishedYear')::integer,

                -- Nested: publisher already composed in tv_book.data
                'publisher', tv_b.data->'publisher'  -- ✅ Reuse nested composition
            )
        ) AS data

    FROM library.tb_review r
    INNER JOIN crm.tv_user tv_u ON tv_u.pk_user = r.fk_author
    INNER JOIN library.tv_book tv_b ON tv_b.pk_book = r.fk_book
    WHERE r.deleted_at IS NULL
      AND (p_pk_review IS NULL OR r.pk_review = p_pk_review);
END;
$$ LANGUAGE plpgsql;
```

**Benefits**:
1. ✅ **Consistency**: Author data in tv_review matches tv_user exactly
2. ✅ **Reuse**: Nested publisher already composed in tv_book
3. ✅ **Cascading Updates**: When tv_user refreshes, tv_review can pick up changes
4. ✅ **Single Source**: tv_user.data is the source of truth for User data

---

### **Dependency Graph**

```
tv_publisher (depth 0)
    ↓
tv_book (depth 1, composes publisher from tv_publisher.data)
    ↓
tv_review (depth 2, composes book from tv_book.data)

tv_user (depth 0)
    ↓
tv_review (depth 1, composes author from tv_user.data)
```

**Refresh Order**:
1. Refresh leaf entities first (tv_publisher, tv_user)
2. Refresh intermediate entities (tv_book)
3. Refresh root entities (tv_review)

**Cascading Updates**:
```sql
-- User's email changes
UPDATE crm.tb_user SET email = 'newemail@example.com' WHERE pk_user = 123;

-- Mutation refreshes tv_user
PERFORM crm.refresh_tv_user(123);
-- Now tv_user.data has new email

-- Also refresh dependent entities
PERFORM library.refresh_tv_review_by_author(123);
-- Now all reviews by this author have updated email in data.author.email
```

---

## 📊 Performance Optimization Strategy

### **Two-Tier Filtering**

FraiseQL can filter on **any** JSONB field, but direct columns are 100-500x faster.

#### **Tier 1: Direct Columns (Fast - B-tree indexes)**

```sql
-- Queries: 1000/day
SELECT * FROM library.tv_review WHERE rating >= 4;
-- Uses: idx_tv_review_rating (B-tree)
-- Performance: ~0.1ms

-- Queries: 500/day
SELECT * FROM library.tv_review
WHERE created_at > '2024-01-01';
-- Uses: idx_tv_review_created (B-tree)
-- Performance: ~0.1ms
```

---

#### **Tier 2: JSONB Columns (Slower - GIN indexes)**

```sql
-- Queries: 10/day
SELECT * FROM library.tv_review
WHERE data->>'comment' ILIKE '%excellent%';
-- Uses: idx_tv_review_data (GIN)
-- Performance: ~50ms

-- Queries: 1/week
SELECT * FROM library.tv_review
WHERE data->'book'->>'title' = 'PostgreSQL Deep Dive';
-- Uses: idx_tv_review_data (GIN) or sequential scan
-- Performance: ~100ms
```

---

### **Auto-Inferred Filter Columns**

SpecQL **automatically** promotes these to direct columns:

```yaml
entity: Review
fields:
  author: ref(User)
  book: ref(Book)
```

**Auto-generates**:
```sql
CREATE TABLE library.tv_review (
    -- Auto-inferred (always high-value)
    tenant_id UUID NOT NULL,   -- Multi-tenant filtering
    author_id UUID NOT NULL,   -- Foreign key filtering
    book_id UUID NOT NULL,     -- Foreign key filtering

    -- User's business fields still in JSONB
    data JSONB
);

-- Auto-indexed
CREATE INDEX idx_tv_review_tenant ON library.tv_review(tenant_id);
CREATE INDEX idx_tv_review_author_id ON library.tv_review(author_id);
CREATE INDEX idx_tv_review_book_id ON library.tv_review(book_id);
```

**Rationale**: Foreign key filtering is **always** a hot path in queries.

---

### **Explicit Filter Columns**

User specifies additional hot paths:

```yaml
entity: Review
fields:
  rating: integer
  comment: text
  author: ref(User)
  book: ref(Book)
  created_at: timestamp

table_views:
  # Based on query analytics
  extra_filter_columns:
    - rating       # 1000 queries/day
    - created_at   # 500 queries/day
    # NOT comment (only 10 queries/day, JSONB GIN is fine)
```

**Generates**:
```sql
CREATE TABLE library.tv_review (
    -- Auto-inferred
    tenant_id UUID,
    author_id UUID,
    book_id UUID,

    -- Explicit (user-optimized)
    rating INTEGER,
    created_at TIMESTAMPTZ,

    -- Everything still in JSONB
    data JSONB  -- { rating: 5, comment: "...", createdAt: "..." }
);

-- Performance indexes
CREATE INDEX idx_tv_review_rating ON library.tv_review(rating);
CREATE INDEX idx_tv_review_created ON library.tv_review(created_at);
```

**Trade-off**:
- ✅ Fast queries on rating, created_at (B-tree)
- ✅ Acceptable performance on comment (GIN)
- ❌ Slight storage overhead (data duplicated in column + JSONB)

---

### **Advanced: Nested Field Extraction**

```yaml
table_views:
  extra_filter_columns:
    - author_name:
        source: author.name  # Extract from nested JSONB
        type: text
        index: gin_trgm      # Trigram for partial matching
```

**Generates**:
```sql
CREATE TABLE library.tv_review (
    ...
    author_name TEXT,  -- Extracted from data->'author'->>'name'
    data JSONB
);

-- Trigram index for ILIKE queries
CREATE INDEX idx_tv_review_author_name
ON library.tv_review
USING GIN(author_name gin_trgm_ops);
```

**Refresh function**:
```sql
INSERT INTO library.tv_review (
    ...,
    author_name,  -- Extract during refresh
    data
)
SELECT
    ...,
    tv_u.data->>'name' AS author_name,  -- From tv_user.data
    jsonb_build_object(
        'author', tv_u.data,  -- Full author still in JSONB
        ...
    )
FROM ...;
```

---

## 🎯 SpecQL Configuration

### **Global Config** (`specql.config.yaml`)

```yaml
version: 1.0

defaults:
  # Table Views (tv_ tables)
  table_views:
    mode: auto              # auto | force | disable
    auto_generate: true     # Generate tv_ when has foreign keys
    auto_filter_columns: true  # Auto-infer tenant_id, {entity}_id
    refresh: explicit       # No triggers, explicit calls only

  # Calculated fields
  calculated_fields:
    enabled: true
    max_depth: 3            # Max tables a calculation can span
    cache_by_default: true

  # Extensions
  extensions:
    jsonb_updater: postgresql  # postgresql | rust_extension (future)
```

---

### **Entity-Level Configuration**

#### **Example 1: Auto (Default)**

```yaml
entity: Review
schema: library

fields:
  rating: integer
  comment: text
  author: ref(User)
  book: ref(Book)

# NO table_views block needed
# ✅ Auto-generates tv_review (has foreign keys)
# ✅ Includes ALL fields from author and book
# ✅ Auto-infers: tenant_id, author_id, book_id
```

---

#### **Example 2: Explicit Field Selection**

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
  # Explicit: which fields to include from related entities
  include_relations:
    - author:
        fields: [name, email, avatarUrl]  # Only these from User

    - book:
        fields: [title, isbn, publishedYear]
        include_relations:
          - publisher:
              fields: [name, country]  # Only these from Publisher

  # Performance optimization
  extra_filter_columns:
    - rating       # High-volume queries
    - created_at   # Date range queries
```

**Generated tv_review.data**:
```jsonb
{
  "id": "...",
  "rating": 5,
  "comment": "...",
  "createdAt": "...",

  "author": {
    "id": "...",
    "name": "...",        // ✅ Included
    "email": "...",       // ✅ Included
    "avatarUrl": "..."    // ✅ Included
    // ❌ NO bio, phoneNumber (not in fields list)
  },

  "book": {
    "id": "...",
    "title": "...",       // ✅ Included
    "isbn": "...",        // ✅ Included
    "publishedYear": ..., // ✅ Included

    "publisher": {
      "id": "...",
      "name": "...",      // ✅ Included
      "country": "..."    // ✅ Included
      // ❌ NO website, foundedYear
    }
    // ❌ NO pageCount, description
  }
}
```

---

#### **Example 3: Force tv_ Without Foreign Keys**

```yaml
entity: AuditLog
schema: core

fields:
  message: text
  metadata: jsonb
  created_at: timestamp

table_views:
  mode: force  # Generate tv_ even without foreign keys

  extra_filter_columns:
    - created_at  # Time-based queries

# ✅ Generates tv_auditlog for fast JSONB + time filtering
```

---

#### **Example 4: Disable tv_ Despite Foreign Keys**

```yaml
entity: SessionToken
schema: auth

fields:
  user: ref(User)
  token: text
  expires_at: timestamp

table_views:
  mode: disable  # Don't generate tv_ (write-heavy table)

# ✅ Only generates v_sessiontoken (regular view)
# ❌ No tv_sessiontoken
```

---

#### **Example 5: Hierarchical Entity**

```yaml
entity: Location
schema: management
hierarchical: true

fields:
  name: text
  parent: ref(Location)  # Self-reference
  location_type: ref(LocationType)

table_views:
  # Auto-infers: path column (LTREE)
  include_relations:
    - parent:
        fields: [name]  # Parent location name only

    - location_type:
        fields: [name, color]

  extra_filter_columns:
    - name  # For name searches
```

**Generated tv_location**:
```sql
CREATE TABLE management.tv_location (
    pk_location INTEGER PRIMARY KEY,
    id UUID,
    tenant_id UUID,

    -- Foreign keys
    fk_parent_location INTEGER,
    fk_location_type INTEGER,

    -- UUID filters (auto-inferred)
    parent_id UUID,
    location_type_id UUID,

    -- Hierarchy (auto-inferred because hierarchical: true)
    path LTREE NOT NULL,

    -- Explicit filter column
    name TEXT,

    -- Denormalized data
    data JSONB
);

-- Indexes
CREATE INDEX idx_tv_location_path ON management.tv_location USING GIST(path);
CREATE INDEX idx_tv_location_name ON management.tv_location(name);
```

---

## 🔄 Mutation Integration (Team C)

### **Write Operation Flow**

```
User GraphQL Mutation
    ↓
PL/pgSQL Function (Team C)
    ↓
1. Write to tb_review (normalized)
    ↓
2. Explicit refresh_tv_review() call
    ↓
3. FraiseQL serves updated data
```

---

### **Mutation Example**

```yaml
entity: Review

actions:
  - name: update_rating
    steps:
      - validate: rating >= 1 AND rating <= 5
      - update: Review SET rating = $new_rating

      # Explicit tv_ refresh (Team C generates this)
      - refresh_table_view:
          scope: self              # Only this review
          propagate: [author]      # Also refresh author's avg rating
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
    v_author_pk INTEGER;
    v_result mutation_result;
BEGIN
    v_pk := library.review_pk(p_review_id);

    -- Get author PK for propagation
    SELECT fk_author INTO v_author_pk
    FROM library.tb_review
    WHERE pk_review = v_pk;

    -- Write to tb_review (normalized)
    UPDATE library.tb_review
    SET rating = p_new_rating,
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_review = v_pk;

    -- Refresh tv_review (self scope) ✅
    PERFORM library.refresh_tv_review(v_pk);

    -- Propagate to author (recalculate average_rating) ✅
    PERFORM crm.refresh_tv_user(v_author_pk);

    -- Build result from tv_review.data
    v_result.status := 'success';
    v_result.message := 'Review rating updated';
    v_result.object_data := (
        SELECT data  -- Return denormalized data from tv_
        FROM library.tv_review
        WHERE pk_review = v_pk
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

### **Refresh Scopes**

#### **Scope: self** (Default)
```yaml
- refresh_table_view:
    scope: self
```
Only refresh this entity's tv_ row.

---

#### **Scope: related**
```yaml
- refresh_table_view:
    scope: related
```
Refresh this entity + all entities that reference it.

---

#### **Scope: propagate** (Explicit)
```yaml
- refresh_table_view:
    scope: self
    propagate: [author, book]  # Only refresh these
```
Refresh this entity + specified related entities.

---

#### **Scope: batch** (Bulk operations)
```yaml
- refresh_table_view:
    scope: batch
    strategy: deferred  # Collect PKs, refresh at end
```
For bulk imports, collect all affected PKs and refresh once.

---

## 📊 FraiseQL Integration (Team D)

### **Annotations on tv_ Tables**

```sql
-- Table annotation
COMMENT ON TABLE library.tv_review IS
  '@fraiseql:table source=materialized,refresh=explicit,primary=true';

-- UUID filters (for GraphQL WHERE clauses)
COMMENT ON COLUMN library.tv_review.author_id IS
  '@fraiseql:filter type=UUID,relation=author,index=btree';

COMMENT ON COLUMN library.tv_review.book_id IS
  '@fraiseql:filter type=UUID,relation=book,index=btree';

-- Promoted filter columns
COMMENT ON COLUMN library.tv_review.rating IS
  '@fraiseql:filter type=Int,index=btree,performance=optimized';

COMMENT ON COLUMN library.tv_review.created_at IS
  '@fraiseql:filter type=DateTime,index=btree,performance=optimized';

-- JSONB data column (FraiseQL extracts GraphQL types from this)
COMMENT ON COLUMN library.tv_review.data IS
  '@fraiseql:jsonb expand=true,description=Denormalized review with author and book data';
```

---

### **FraiseQL Auto-Discovery**

FraiseQL reads these annotations:
1. Finds `library.tv_review` table
2. Sees `@fraiseql:jsonb expand=true` on data column
3. Introspects JSONB structure from sample rows
4. Auto-generates GraphQL types

**Example Auto-Discovery**:
```sql
-- FraiseQL samples data column
SELECT data FROM library.tv_review LIMIT 100;

-- Discovers structure:
-- {
--   "id": UUID,
--   "rating": Int,
--   "author": { "id": UUID, "name": String, "email": String },
--   "book": { "id": UUID, "title": String, "isbn": String, "publisher": {...} }
-- }

-- Auto-generates GraphQL:
type Review {
  id: UUID!
  rating: Int!
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
  publisher: ReviewPublisher!
}
```

---

## 📋 Implementation Roadmap

### **Phase 1: Team A - Parser Extensions** (Week 2-3, 3-4 days)

**Add to SpecQL Parser**:
1. Parse `table_views` configuration block
2. Parse `include_relations` (nested field selection)
3. Parse `extra_filter_columns`
4. Parse `mode: auto/force/disable`
5. Add to Entity AST

**Deliverables**:
- `src/core/ast_models.py` - TableViewConfig, IncludeRelation classes
- `src/core/specql_parser.py` - Parse table_views block
- Tests in `tests/unit/core/test_table_views_parsing.py`

---

### **Phase 2: Team B - tv_ Generation** (Week 3-5, 7-8 days)

**New Phase 9: Table View Generation**

**Generates**:
1. `tv_{entity}` table schema
2. Auto-infer filter columns (tenant_id, {entity}_id, path)
3. Explicit filter columns (from extra_filter_columns)
4. GIN index on data column
5. B-tree indexes on filter columns
6. `refresh_tv_{entity}()` function with JSONB composition

**Templates**:
- `templates/schema/table_view.sql.jinja2`
- `templates/schema/refresh_table_view.sql.jinja2`

**Key Innovation**: Compose from tv_ tables, not tb_ tables

---

### **Phase 3: Team C - Mutation Integration** (Week 5-6, 3-4 days)

**Update Action Compiler**:
1. Detect `refresh_table_view` action step
2. Generate `PERFORM refresh_tv_{entity}()` calls
3. Handle scopes (self, related, propagate, batch)
4. Return data from tv_ in mutation result

**Templates**:
- `templates/actions/refresh_table_view.sql.jinja2`

---

### **Phase 4: Team D - FraiseQL Annotations** (Week 6-7, 2-3 days)

**Generate Annotations**:
1. `@fraiseql:table` on tv_ tables
2. `@fraiseql:filter` on filter columns
3. `@fraiseql:jsonb expand=true` on data column

**Templates**:
- `templates/fraiseql/table_view_annotations.sql.jinja2`

---

### **Phase 5: Integration Testing** (Week 7, 2-3 days)

**End-to-End Tests**:
1. SpecQL → tb_ + tv_ generation
2. Mutation → tb_ write + tv_ refresh
3. FraiseQL → GraphQL query from tv_
4. Performance validation (B-tree vs GIN)

---

## ✅ Acceptance Criteria

### **Team A (Parser)**
- [ ] Parse `table_views.mode: auto/force/disable`
- [ ] Parse `table_views.include_relations` (nested)
- [ ] Parse `table_views.extra_filter_columns`
- [ ] Add TableViewConfig to Entity AST
- [ ] All parsing tests pass

---

### **Team B (Schema Generator)**
- [ ] Generate tv_ tables with correct schema
- [ ] Auto-infer filter columns (tenant_id, {entity}_id, path)
- [ ] Generate explicit filter columns
- [ ] Generate refresh functions that compose from tv_ tables
- [ ] Generate correct indexes (B-tree on filters, GIN on data)
- [ ] Handle hierarchical entities (auto-add path column)
- [ ] All schema generation tests pass

---

### **Team C (Action Compiler)**
- [ ] Compile `refresh_table_view` action step
- [ ] Handle scope: self, related, propagate, batch
- [ ] Generate correct PERFORM calls in mutations
- [ ] Return tv_.data in mutation results
- [ ] All action compilation tests pass

---

### **Team D (FraiseQL Annotations)**
- [ ] Generate @fraiseql:table annotations
- [ ] Generate @fraiseql:filter annotations
- [ ] Generate @fraiseql:jsonb annotations
- [ ] All annotation tests pass

---

### **Integration**
- [ ] End-to-end: SpecQL → SQL → Database → FraiseQL
- [ ] Performance: B-tree filters 100x faster than GIN
- [ ] JSONB composition: tv_review.data.author matches tv_user.data
- [ ] Cascading refresh: user update propagates to reviews
- [ ] FraiseQL auto-generates correct GraphQL types

---

## 🎯 Summary

**Three-Layer Architecture**:
1. **tb_** - Normalized storage (write side)
2. **tv_** - Denormalized JSONB (read side, exposes to FraiseQL)
3. **FraiseQL** - Auto-generated GraphQL (query layer)

**Key Innovations**:
1. ✅ JSONB composition from tv_ tables (not tb_)
2. ✅ Two-tier filtering (B-tree for hot paths, GIN for everything else)
3. ✅ Auto-inference + explicit optimization
4. ✅ Explicit field selection (no depth parameter)
5. ✅ Storage/query separation (tv_ stores, FraiseQL exposes)

**Total Timeline**: 4-5 weeks (parallel with other Team B work)

**Status**: 🔴 APPROVED - Ready for Implementation

---

**Last Updated**: 2025-11-09
**Document Version**: 1.0
