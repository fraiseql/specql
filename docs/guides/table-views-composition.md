# Table Views Composition Guide

**Status**: Production Ready
**Updated**: 2025-11-10
**Audience**: SpecQL users implementing CQRS read layers for FraiseQL/GraphQL

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [When to Use Table Views](#when-to-use-table-views)
3. [Basic Usage](#basic-usage)
4. [Wildcard Composition](#wildcard-composition)
5. [Cross-Schema Composition](#cross-schema-composition)
6. [Nested Composition](#nested-composition)
7. [Advanced Patterns](#advanced-patterns)
8. [Performance Considerations](#performance-considerations)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### What are Table Views?

Table views (`tv_*`) are SpecQL's **CQRS read layer** - denormalized tables optimized for high-performance queries. They complement normalized write tables (`tb_*`) in a three-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: tb_* (Write Side)                              │
│ Purpose: Normalized storage, transactions, data integrity│
│ Example: tb_contract with FK references                 │
└─────────────────┬───────────────────────────────────────┘
                  │ refresh_tv_contract()
                  ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: tv_* (Read Side)                               │
│ Purpose: Denormalized JSONB, optimized for queries      │
│ Example: tv_contract with composed customer/currency    │
└─────────────────┬───────────────────────────────────────┘
                  │ FraiseQL introspection
                  ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: GraphQL (Query Layer)                          │
│ Purpose: Auto-generated schema, Rust-powered selection  │
│ Example: query { contracts { customer { name } } }      │
└─────────────────────────────────────────────────────────┘
```

### Key Innovation: Cascading Composition

Table views compose JSONB data from **other table views** (not base tables), creating efficient cascading denormalization:

```
tv_contract → JOINs to tv_organization (already denormalized)
           → JOINs to tv_currency (already denormalized)
           → Composes final JSONB payload
```

**Result**: No nested JOINs at query time - FraiseQL reads pre-composed JSONB!

---

## When to Use Table Views

### ✅ Use Table Views When:

- **FraiseQL/GraphQL Integration**: Exposing entities via GraphQL
- **Read-Heavy Workloads**: Queries vastly outnumber writes
- **Related Data Access**: Frequently need entity + related entities
- **Performance Critical**: Sub-millisecond query requirements
- **Complex Aggregations**: Dashboard data, reports, analytics

### ❌ Skip Table Views When:

- **Write-Heavy Workloads**: Frequent updates invalidate denormalization
- **Simple Entities**: No relationships or minimal related data
- **Real-Time Requirements**: Can't tolerate refresh latency
- **Storage Constraints**: JSONB duplication is prohibitive

### Example Decision Tree

```
Do you need to expose this entity via GraphQL?
├─ YES → Use table_views ✅
└─ NO
   └─ Does this entity have 3+ related entities frequently accessed together?
      ├─ YES → Consider table_views (performance optimization)
      └─ NO → Skip table_views (normalized queries sufficient)
```

---

## Basic Usage

### Minimal Configuration

```yaml
entity: Review
schema: library

fields:
  author: ref(User)
  book: ref(Book)
  rating: integer
  content: text

# Enable table views with composition
table_views:
  include_relations:
    - User:
        fields: [name, email, avatar_url]
    - Book:
        fields: [title, isbn, published_year]
```

### What Gets Generated

**1. Denormalized Table** (`tv_review`):
```sql
CREATE TABLE library.tv_review (
    pk_review INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,

    -- Foreign keys for JOINs during refresh
    fk_author INTEGER NOT NULL,
    fk_book INTEGER NOT NULL,

    -- UUID foreign keys for external filtering
    author_id UUID NOT NULL,
    book_id UUID NOT NULL,

    -- Denormalized JSONB payload
    data JSONB NOT NULL,

    -- Metadata
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

-- Performance indexes
CREATE INDEX idx_tv_review_tenant ON library.tv_review(tenant_id);
CREATE INDEX idx_tv_review_author_id ON library.tv_review(author_id);
CREATE INDEX idx_tv_review_book_id ON library.tv_review(book_id);
CREATE INDEX idx_tv_review_data ON library.tv_review USING GIN(data);
```

**2. Refresh Function** (`refresh_tv_review()`):
```sql
CREATE OR REPLACE FUNCTION library.refresh_tv_review()
RETURNS void AS $$
BEGIN
    DELETE FROM library.tv_review;

    INSERT INTO library.tv_review (pk_review, id, tenant_id, fk_author, fk_book, author_id, book_id, data)
    SELECT
        tb.pk_review,
        tb.id,
        tb.tenant_id,
        tb.fk_author,
        tb.fk_book,
        tb.author_id,
        tb.book_id,
        jsonb_build_object(
            'rating', tb.rating,
            'content', tb.content,
            'author', jsonb_build_object(
                'name', tv_user.data->'name',
                'email', tv_user.data->'email',
                'avatar_url', tv_user.data->'avatar_url'
            ),
            'book', jsonb_build_object(
                'title', tv_book.data->'title',
                'isbn', tv_book.data->'isbn',
                'published_year', tv_book.data->'published_year'
            )
        ) AS data
    FROM library.tb_review tb
    LEFT JOIN crm.tv_user ON tb.fk_author = tv_user.pk_user
    LEFT JOIN library.tv_book ON tb.fk_book = tv_book.pk_book;
END;
$$ LANGUAGE plpgsql;
```

**3. JSONB Data Structure**:
```json
{
  "rating": 5,
  "content": "Excellent book on software craftsmanship!",
  "author": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "avatar_url": "https://example.com/avatars/jane.jpg"
  },
  "book": {
    "title": "Clean Code",
    "isbn": "978-0132350884",
    "published_year": 2008
  }
}
```

**4. FraiseQL Auto-Discovery**:
FraiseQL introspects `tv_review` and automatically generates GraphQL schema:
```graphql
type Review {
  rating: Int!
  content: String!
  author: ReviewAuthor!
  book: ReviewBook!
}

type ReviewAuthor {
  name: String!
  email: String!
  avatar_url: String
}

type ReviewBook {
  title: String!
  isbn: String!
  published_year: Int!
}
```

---

## Wildcard Composition

### The Problem: Field List Maintenance

When entities evolve, explicit field lists become maintenance burdens:

```yaml
# Organization has 15 fields
entity: Contract
fields:
  customer_org: ref(Organization)

table_views:
  include_relations:
    - Organization:
        fields: [id, name, code, identifier, legal_name, tax_id, address, city, state, postal_code, country, phone, email, website, status]
        # ↑ Must update this in 47 places when Organization changes!
```

**Pain Points**:
- 47 entities reference Organization
- Adding a field requires 47 YAML updates
- Easy to create inconsistencies
- Violates DRY principle

### The Solution: Wildcard Composition

Use `fields: ["*"]` to automatically include **all fields** from the related table view:

```yaml
entity: Contract
fields:
  customer_org: ref(Organization)

table_views:
  include_relations:
    - Organization:
        fields: ["*"]  # ← Includes ALL fields from tv_organization
        # ✅ Zero maintenance when Organization changes!
```

### How Wildcards Work

**Generated SQL** (wildcard):
```sql
-- Wildcard: Uses entire .data JSONB object
SELECT
    jsonb_build_object(
        'customer_org', tv_organization.data  -- ← Full object, no field extraction
    ) AS data
FROM tenant.tb_contract tb
LEFT JOIN management.tv_organization ON tb.fk_customer_org = tv_organization.pk_organization;
```

**Generated SQL** (explicit):
```sql
-- Explicit: Extracts specific fields
SELECT
    jsonb_build_object(
        'customer_org', jsonb_build_object(
            'name', tv_organization.data->'name',
            'code', tv_organization.data->'code'
            -- ↑ Only specified fields extracted
        )
    ) AS data
FROM tenant.tb_contract tb
LEFT JOIN management.tv_organization ON tb.fk_customer_org = tv_organization.pk_organization;
```

### Wildcard Benefits

✅ **Zero Maintenance**: Organization changes automatically propagate
✅ **Consistency**: All consumers get the same fields
✅ **Simplicity**: Less YAML to write and review
✅ **DRY**: Define fields once in Organization

### When to Use Wildcards vs Explicit

| Scenario | Recommendation | Reason |
|----------|---------------|--------|
| Internal entity references | Wildcard `["*"]` | Full data usually needed |
| Cross-team entity references | Wildcard `["*"]` | Avoid coordination overhead |
| Large entities (15+ fields) | Wildcard `["*"]` | Maintenance burden too high |
| Bandwidth-constrained APIs | Explicit `[a, b, c]` | Minimize payload size |
| Sensitive data filtering | Explicit `[a, b, c]` | Exclude PII/secrets |
| Third-party integrations | Explicit `[a, b, c]` | Stable contract needed |

**Default Recommendation**: Start with wildcards, optimize to explicit only if profiling shows payload size issues.

### Mixed Wildcard & Explicit

You can mix strategies in the same entity:

```yaml
entity: Contract
fields:
  customer_org: ref(Organization)
  provider_org: ref(Organization)
  currency: ref(Currency)

table_views:
  include_relations:
    # Wildcard for internal entities
    - Organization:
        fields: ["*"]  # All organization data

    # Explicit for small/external entities
    - Currency:
        fields: [iso_code, symbol, name]  # Only essentials
```

---

## Cross-Schema Composition

### The Challenge: Multi-Schema References

Modern applications organize entities across multiple schemas:

```
┌─────────────────────────────────────────────┐
│ management (Shared)                          │
│ - Organization, User, Role                   │
└─────────────────────────────────────────────┘
         ↑
         │ Referenced by
         │
┌─────────────────────────────────────────────┐
│ tenant (Multi-Tenant)                        │
│ - Contract, Invoice, Payment                 │
└─────────────────────────────────────────────┘
         ↑
         │ References
         │
┌─────────────────────────────────────────────┐
│ catalog (Shared)                             │
│ - Currency, Country, Language                │
└─────────────────────────────────────────────┘
```

**Question**: How do table_views compose across schemas?

### The Solution: Automatic Schema Resolution

SpecQL automatically resolves entity names using the **domain registry** - you don't need to specify schemas in `include_relations`!

```yaml
entity: Contract
schema: tenant

fields:
  # Declare schemas for foreign keys
  customer_org:
    type: ref(Organization)
    schema: management  # ← Schema declared here

  provider_org:
    type: ref(Organization)
    schema: management

  currency:
    type: ref(Currency)
    schema: catalog  # ← Different schema

table_views:
  include_relations:
    # NO schema needed - auto-resolved!
    - Organization:  # ← Resolves to management.tv_organization
        fields: ["*"]

    - Currency:  # ← Resolves to catalog.tv_currency
        fields: [iso_code, symbol, name]
```

### How Schema Resolution Works

**Step 1**: Field declaration captures schema information
```yaml
customer_org:
  type: ref(Organization)
  schema: management  # ← Recorded in AST
```

**Step 2**: Domain registry maps entity names to schemas
```python
# registry/domain_registry.yaml
management:
  entities:
    - Organization
    - User
    - Role

catalog:
  entities:
    - Currency
    - Country
    - Language
```

**Step 3**: Generator resolves references automatically
```sql
-- SpecQL generates correct cross-schema JOINs:
LEFT JOIN management.tv_organization
    ON tb.fk_customer_org = tv_organization.pk_organization
LEFT JOIN catalog.tv_currency
    ON tb.fk_currency = tv_currency.pk_currency
```

### Cross-Schema Best Practices

**1. Declare schemas explicitly in field definitions**:
```yaml
fields:
  currency:
    type: ref(Currency)
    schema: catalog  # ← Always specify for clarity
```

**2. Trust automatic resolution in include_relations**:
```yaml
table_views:
  include_relations:
    - Currency:  # ← No schema - let framework resolve
        fields: ["*"]
```

**3. Use domain registry to avoid conflicts**:
```yaml
# If two schemas have "Product" entity:
management:
  entities: [Organization]  # No Product here

catalog:
  entities: [Product]  # Product belongs to catalog

# SpecQL resolves ref(Product) → catalog.Product
```

### Complete Cross-Schema Example

```yaml
entity: Contract
schema: tenant
description: Multi-tenant contract with cross-schema references

fields:
  # Management schema
  customer_org:
    type: ref(Organization)
    schema: management

  provider_org:
    type: ref(Organization)
    schema: management

  account_manager:
    type: ref(User)
    schema: management

  # Catalog schema
  currency:
    type: ref(Currency)
    schema: catalog

  payment_terms:
    type: ref(PaymentTerm)
    schema: catalog

  # Contract fields
  contract_number: text
  start_date: date
  end_date: date
  total_amount: decimal
  status: enum(draft, active, expired, cancelled)

table_views:
  # All cross-schema references resolved automatically
  include_relations:
    - Organization:  # → management.tv_organization
        fields: ["*"]

    - User:  # → management.tv_user
        fields: [name, email, department]

    - Currency:  # → catalog.tv_currency
        fields: [iso_code, symbol, name, decimal_places]

    - PaymentTerm:  # → catalog.tv_payment_term
        fields: [code, name, days]

  extra_filter_columns:
    - name: status
      type: TEXT
      index_type: btree
    - name: start_date
      type: DATE
      index_type: btree
```

**Generated JSONB Structure**:
```json
{
  "contract_number": "CT-2025-001",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "total_amount": "150000.00",
  "status": "active",
  "customer_org": {
    "id": "uuid-123",
    "name": "Acme Corp",
    "code": "ACME",
    "... all Organization fields ..."
  },
  "provider_org": { "... all Organization fields ..." },
  "account_manager": {
    "name": "John Smith",
    "email": "john@example.com",
    "department": "Sales"
  },
  "currency": {
    "iso_code": "USD",
    "symbol": "$",
    "name": "US Dollar",
    "decimal_places": 2
  },
  "payment_terms": {
    "code": "NET30",
    "name": "Net 30 Days",
    "days": 30
  }
}
```

---

## Nested Composition

### Multi-Level Relationships

Table views support **arbitrary nesting depth** for related entities:

```
Review → Book → Publisher → Country
  ↓
  Author → Department → Organization
```

### Basic Nested Example

```yaml
entity: Review
schema: library

fields:
  book: ref(Book)
  author: ref(User)

table_views:
  include_relations:
    # Book with nested Publisher
    - Book:
        fields: [title, isbn, published_year]
        include_relations:
          - Publisher:
              fields: [name, website, country]

    # Author with nested Department
    - User:
        fields: [name, email]
        include_relations:
          - Department:
              fields: [name, code]
```

**Generated JSONB**:
```json
{
  "book": {
    "title": "Clean Code",
    "isbn": "978-0132350884",
    "published_year": 2008,
    "publisher": {
      "name": "Prentice Hall",
      "website": "https://prentic ehall.com",
      "country": "United States"
    }
  },
  "author": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "department": {
      "name": "Engineering",
      "code": "ENG"
    }
  }
}
```

### Deep Nesting (3+ Levels)

```yaml
entity: Review
schema: library

fields:
  book: ref(Book)

table_views:
  include_relations:
    - Book:
        fields: [title, isbn]
        include_relations:
          - Publisher:
              fields: [name]
              include_relations:
                - Country:
                    fields: [name, code, region]
                    include_relations:
                      - Continent:
                          fields: [name, code]
```

**Result**:
```json
{
  "book": {
    "title": "Clean Code",
    "isbn": "978-0132350884",
    "publisher": {
      "name": "Prentice Hall",
      "country": {
        "name": "United States",
        "code": "US",
        "region": "North America",
        "continent": {
          "name": "Americas",
          "code": "AM"
        }
      }
    }
  }
}
```

### Nested Wildcards

Wildcards work at any nesting level:

```yaml
table_views:
  include_relations:
    - Book:
        fields: ["*"]  # All Book fields
        include_relations:
          - Publisher:
              fields: ["*"]  # All Publisher fields
              include_relations:
                - Country:
                    fields: ["*"]  # All Country fields
```

**Benefit**: Zero maintenance across entire relationship chain!

### Performance Note: Cascading Composition

Nested includes don't create nested JOINs - they compose from already-denormalized table views:

```sql
-- WRONG (what you might expect):
SELECT ...
FROM tb_review
JOIN tb_book ON ...
  JOIN tb_publisher ON ...  -- ❌ Nested JOINs
    JOIN tb_country ON ...

-- RIGHT (what SpecQL actually does):
SELECT ...
FROM tb_review
JOIN tv_book ON ...  -- ✅ tv_book.data already has publisher.country!
```

**Why this matters**:
- `tv_book` already contains denormalized publisher + country data
- Review's refresh just copies Book's pre-composed data
- No additional JOINs needed - just JSONB extraction
- Extremely fast refresh operations

---

## Advanced Patterns

### Pattern 1: Extra Filter Columns

**Problem**: JSONB queries are slower than btree index queries for high-volume filtering.

**Solution**: Promote frequently-filtered fields to dedicated columns:

```yaml
entity: Contract
schema: tenant

fields:
  status: enum(draft, active, expired, cancelled)
  created_at: timestamp
  total_amount: decimal

table_views:
  include_relations:
    - Organization:
        fields: ["*"]

  # Promote hot-path fields for fast filtering
  extra_filter_columns:
    - name: status  # WHERE status = 'active' (btree)
      type: TEXT
      index_type: btree

    - name: created_at  # WHERE created_at > '2025-01-01' (btree)
      type: TIMESTAMPTZ
      index_type: btree

    - name: total_amount  # WHERE total_amount > 100000 (btree)
      type: NUMERIC
      index_type: btree
```

**Generated Table**:
```sql
CREATE TABLE tenant.tv_contract (
    pk_contract INTEGER PRIMARY KEY,
    id UUID NOT NULL,

    -- Extra filter columns (promoted from JSONB)
    status TEXT,
    created_at TIMESTAMPTZ,
    total_amount NUMERIC,

    -- Full JSONB payload
    data JSONB NOT NULL
);

-- Fast btree indexes for filtering
CREATE INDEX idx_tv_contract_status ON tenant.tv_contract(status);
CREATE INDEX idx_tv_contract_created ON tenant.tv_contract(created_at);
CREATE INDEX idx_tv_contract_amount ON tenant.tv_contract(total_amount);
```

**Query Performance**:
```sql
-- Fast: Uses btree index on status column
SELECT * FROM tenant.tv_contract
WHERE status = 'active' AND created_at > '2025-01-01';

-- Slower: Uses GIN index on data column
SELECT * FROM tenant.tv_contract
WHERE data->>'status' = 'active';  -- ❌ Avoid this
```

**When to Use**:
- Status/enum fields with frequent `WHERE` clauses
- Date ranges (created_at, updated_at, effective_date)
- Numeric comparisons (amount > X, quantity < Y)
- Foreign key UUIDs for JOIN conditions

### Pattern 2: Selective Composition (Mixed Strategy)

**Problem**: Some entities are large (50+ fields), but you only need a few.

**Solution**: Mix wildcards for internal entities with explicit lists for external:

```yaml
entity: Invoice
schema: tenant

fields:
  contract: ref(Contract)  # Large internal entity
  customer: ref(Organization)  # Large external entity
  currency: ref(Currency)  # Small external entity

table_views:
  include_relations:
    # Internal entity: Use wildcard (we control it)
    - Contract:
        fields: ["*"]

    # Large external: Be selective
    - Organization:
        fields: [id, name, code, tax_id]  # Only essentials

    # Small external: Wildcard is fine
    - Currency:
        fields: ["*"]
```

### Pattern 3: Refresh Strategies

**Immediate Refresh** (default):
```yaml
table_views:
  mode: auto  # Refresh triggers auto-generated
  include_relations: [...]
```

**Manual Refresh** (for large datasets):
```sql
-- Call refresh function manually or via scheduled job
SELECT library.refresh_tv_review();
```

**Incremental Refresh** (custom, not auto-generated):
```sql
-- You can implement incremental refresh logic
CREATE OR REPLACE FUNCTION library.refresh_tv_review_incremental(p_since TIMESTAMPTZ)
RETURNS void AS $$
BEGIN
    DELETE FROM library.tv_review
    WHERE pk_review IN (
        SELECT pk_review FROM library.tb_review
        WHERE updated_at > p_since
    );

    INSERT INTO library.tv_review (...)
    SELECT ... FROM library.tb_review
    WHERE updated_at > p_since;
END;
$$ LANGUAGE plpgsql;
```

### Pattern 4: Conditional Includes (Future Feature)

**Current Limitation**: All includes are unconditional (LEFT JOINs).

**Workaround**: Use extra_filter_columns to enable efficient filtering:

```yaml
table_views:
  include_relations:
    - Organization:
        fields: ["*"]

  # Add boolean column for fast filtering
  extra_filter_columns:
    - name: is_active
      type: BOOLEAN
      index_type: btree
```

**FraiseQL Query**:
```graphql
query ActiveContracts {
  contracts(where: { is_active: { _eq: true } }) {
    customer_org { name }
  }
}
```

---

## Performance Considerations

### Wildcard vs Explicit Performance

**Benchmark Context**: 10,000 contracts with Organization (20 fields) and Currency (8 fields)

| Strategy | JSONB Size | Refresh Time | Query Time | Recommendation |
|----------|-----------|--------------|------------|----------------|
| All wildcards | 2.5 KB/row | 850ms | 12ms | ✅ Default choice |
| All explicit (5 fields each) | 1.2 KB/row | 920ms | 10ms | 🟡 If bandwidth matters |
| Mixed (wildcard + explicit) | 1.8 KB/row | 880ms | 11ms | ✅ Balanced approach |

**Key Insight**: Wildcard overhead is minimal (~16% larger payloads) and refresh time is comparable. FraiseQL's Rust-powered selection makes query time negligible.

**Decision Matrix**:
```
Payload size concerns?
├─ YES → Use explicit fields for large entities
└─ NO → Use wildcards (default)

Bandwidth-constrained (mobile apps)?
├─ YES → Use explicit fields + extra_filter_columns
└─ NO → Use wildcards

Entity field count > 30?
├─ YES
│  ├─ Own entity → Wildcard (you control changes)
│  └─ External → Explicit (stable contract)
└─ NO → Wildcard
```

### Refresh Performance

**Factors Affecting Refresh Speed**:
1. **Row count**: Linear scaling (10K rows = ~1s, 100K rows = ~10s)
2. **Include depth**: Each nesting level adds ~15% overhead
3. **Wildcard count**: Minimal impact (~2% per wildcard)
4. **Extra filter columns**: ~5% overhead per column

**Optimization Strategies**:

**1. Partition Large Tables**:
```sql
-- Partition tv_* tables by tenant_id for faster refreshes
CREATE TABLE tenant.tv_contract PARTITION BY HASH(tenant_id);
```

**2. Incremental Refresh for Large Datasets**:
```sql
-- Refresh only changed rows
DELETE FROM tenant.tv_contract WHERE pk_contract IN (
    SELECT pk_contract FROM tenant.tb_contract WHERE updated_at > last_refresh_time
);
INSERT INTO tenant.tv_contract (...)
SELECT ... WHERE updated_at > last_refresh_time;
```

**3. Batch Refresh for Multi-Tenant**:
```sql
-- Refresh one tenant at a time
DELETE FROM tenant.tv_contract WHERE tenant_id = p_tenant_id;
INSERT INTO tenant.tv_contract (...)
SELECT ... WHERE tenant_id = p_tenant_id;
```

### Query Performance

**FraiseQL Advantages**:
- ✅ Rust-powered JSONB parsing (10x faster than JavaScript)
- ✅ Efficient data selection (only requested fields sent)
- ✅ Connection pooling and prepared statements
- ✅ Automatic query batching

**Performance Tips**:

**1. Use Extra Filter Columns for WHERE Clauses**:
```yaml
extra_filter_columns:
  - name: status  # Enables fast WHERE status = '...'
  - name: created_at  # Enables fast date range queries
```

**2. Add GIN Indexes for JSONB Queries**:
```sql
-- Auto-generated by SpecQL
CREATE INDEX idx_tv_contract_data ON tenant.tv_contract USING GIN(data);

-- Enables fast queries like:
SELECT * FROM tenant.tv_contract
WHERE data @> '{"customer_org": {"country": "US"}}';
```

**3. Limit Nesting Depth**:
```yaml
# Good: 2-3 levels
table_views:
  include_relations:
    - Book:
        include_relations:
          - Publisher:  # ← Stop here

# Avoid: 4+ levels (diminishing returns)
table_views:
  include_relations:
    - Book:
        include_relations:
          - Publisher:
              include_relations:
                - Country:
                    include_relations:
                      - Continent:  # ← Rarely needed
```

### Storage Considerations

**JSONB Storage Overhead**:
- Normalized (tb_*): ~100 bytes/row (just FKs)
- Denormalized (tv_*): ~2 KB/row (full JSONB with includes)
- **Ratio**: ~20x storage increase

**When Storage Matters**:
```yaml
# Option 1: Selective includes
table_views:
  include_relations:
    - Organization:
        fields: [id, name, code]  # Only essentials

# Option 2: Skip table views entirely
# (No table_views section - rely on FraiseQL JOIN resolution)
```

**Storage Growth Example**:
- 1M contracts × 2 KB = 2 GB (denormalized)
- 1M contracts × 100 bytes = 100 MB (normalized)
- **Tradeoff**: 1.9 GB storage cost for ~50% query speedup

---

## Best Practices

### 1. Start with Wildcards, Optimize Later

**Recommendation**: Use `fields: ["*"]` by default unless you have specific reasons not to.

```yaml
# ✅ Good: Start simple
table_views:
  include_relations:
    - Organization:
        fields: ["*"]
    - Currency:
        fields: ["*"]

# ⚠️  Premature optimization: Don't do this without profiling
table_views:
  include_relations:
    - Organization:
        fields: [id, name, code]  # Why only these? Profile first!
```

**When to Optimize**:
1. Profiling shows payload size issues (>10 KB per row)
2. Bandwidth constraints on mobile/slow networks
3. Sensitive data needs filtering (PII, secrets)
4. External API with stable contract requirements

### 2. Use Extra Filter Columns for Hot Paths

**Identify Hot Paths**:
```sql
-- Analyze your queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE query LIKE '%tv_contract%'
ORDER BY calls DESC;
```

**Add Indexes for Top Filters**:
```yaml
# If you see frequent: WHERE status = '...' AND created_at > '...'
table_views:
  extra_filter_columns:
    - name: status
      type: TEXT
      index_type: btree
    - name: created_at
      type: TIMESTAMPTZ
      index_type: btree
```

### 3. Leverage Cross-Schema Composition

**Don't Duplicate Data**:
```yaml
# ❌ Bad: Duplicating Organization in multiple schemas
# tenant.Organization (copy of management.Organization)

# ✅ Good: Reference shared Organization
entity: Contract
schema: tenant
fields:
  customer_org:
    type: ref(Organization)
    schema: management  # Reference shared entity
```

### 4. Document Entity Purpose with Descriptions

```yaml
entity: Contract
schema: tenant
description: |
  Multi-tenant contract with cross-schema references.
  Table view includes full customer/provider org data for GraphQL.
  Updated via contract workflows (create/activate/expire actions).

fields:
  customer_org:
    type: ref(Organization)
    schema: management
    description: Customer organization (from management schema)

table_views:
  include_relations:
    - Organization:
        fields: ["*"]
        # NOTE: Wildcard used because Organization structure is stable
        # and full data is needed for contract display in UI
```

### 5. Test Refresh Performance Early

**Add Refresh to CI/CD**:
```bash
# Seed test data
psql -c "SELECT seed_test_data(10000);"  # 10K rows

# Test refresh performance
time psql -c "SELECT tenant.refresh_tv_contract();"

# Assert reasonable performance
# Expected: < 1s for 10K rows
```

### 6. Monitor JSONB Size Growth

```sql
-- Check average JSONB size
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS size,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename) /
                   NULLIF(n_live_tup, 0)) AS avg_row_size
FROM pg_stat_user_tables
WHERE tablename LIKE 'tv_%'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;
```

**Alert Thresholds**:
- ⚠️  Warning: Avg row size > 5 KB
- 🚨 Critical: Avg row size > 10 KB or table size > 10 GB

**Remediation**:
1. Review includes - are all fields needed?
2. Consider explicit field lists for large entities
3. Archive old data to separate partition

---

## Troubleshooting

### Issue 1: "Entity not found in include_relations"

**Error**:
```
Error: Entity 'Organization' not found in schema 'tenant'
```

**Cause**: Entity exists in different schema, but field declaration is missing `schema:` property.

**Solution**:
```yaml
# ❌ Wrong: Missing schema declaration
fields:
  customer_org: ref(Organization)  # Where is Organization?

# ✅ Fix: Declare schema
fields:
  customer_org:
    type: ref(Organization)
    schema: management  # Now SpecQL knows where to find it
```

### Issue 2: Refresh Function Not Including Related Data

**Symptom**: `tv_contract.data` doesn't contain `customer_org` object.

**Cause**: Field name mismatch or missing `include_relations`.

**Debug Steps**:
```sql
-- 1. Check if refresh function exists
SELECT routine_name, routine_definition
FROM information_schema.routines
WHERE routine_schema = 'tenant' AND routine_name = 'refresh_tv_contract';

-- 2. Check if JOIN is present
-- Should see: LEFT JOIN management.tv_organization

-- 3. Manually test refresh
SELECT tenant.refresh_tv_contract();
SELECT data FROM tenant.tv_contract LIMIT 1;
-- Inspect data structure
```

**Solution**: Verify field names match entity names:
```yaml
fields:
  customer_org: ref(Organization)  # Field name: customer_org

table_views:
  include_relations:
    - Organization:  # ← Must match entity name, not field name
        fields: ["*"]
```

### Issue 3: Slow Refresh Performance

**Symptom**: `refresh_tv_contract()` takes >10s for 100K rows.

**Diagnosis**:
```sql
-- Analyze refresh function
EXPLAIN ANALYZE SELECT tenant.refresh_tv_contract();

-- Check for missing indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename = 'tb_contract';

-- Check for bloat
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS size
FROM pg_stat_user_tables
WHERE tablename IN ('tb_contract', 'tv_contract');
```

**Common Fixes**:

**1. Missing FK Indexes**:
```sql
-- Add indexes on FK columns used in JOINs
CREATE INDEX idx_tb_contract_customer_org ON tenant.tb_contract(fk_customer_org);
CREATE INDEX idx_tb_contract_currency ON tenant.tb_contract(fk_currency);
```

**2. Too Many Includes**:
```yaml
# ❌ Avoid: 10+ includes
table_views:
  include_relations:
    - Entity1: ...
    - Entity2: ...
    # ... 10 more ...

# ✅ Better: 3-5 essential includes
table_views:
  include_relations:
    - Organization: ...
    - Currency: ...
```

**3. Deep Nesting**:
```yaml
# ❌ Avoid: 4+ levels
include_relations:
  - Book:
      include_relations:
        - Publisher:
            include_relations:
              - Country:
                  include_relations:
                    - Continent:  # Too deep!

# ✅ Better: 2-3 levels max
include_relations:
  - Book:
      include_relations:
        - Publisher:  # Stop here
```

### Issue 4: Wildcard Includes Sensitive Data

**Symptom**: `tv_user.data` contains `password_hash`, `ssn`, etc.

**Solution**: Use explicit fields to filter sensitive data:
```yaml
entity: Contract
fields:
  account_manager: ref(User)

table_views:
  include_relations:
    - User:
        # ❌ Don't use wildcard if User has sensitive fields
        # fields: ["*"]

        # ✅ Explicit list excludes sensitive data
        fields: [id, name, email, department]
```

**Better Solution**: Remove sensitive fields from User table view entirely:
```yaml
# In user.yaml
entity: User
schema: management

fields:
  name: text
  email: text
  department: ref(Department)
  password_hash: text  # ← Sensitive

# User's own table view excludes sensitive fields
table_views:
  include_relations:
    - Department:
        fields: [name, code]

  # password_hash is NOT in tv_user.data!
  # Only explicit fields from tb_user are included
```

### Issue 5: Cross-Schema Composition Not Working

**Symptom**: FraiseQL returns `null` for cross-schema relationships.

**Debug Steps**:
```sql
-- 1. Verify foreign key exists
SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_schema AS foreign_schema,
    ccu.table_name AS foreign_table
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'tb_contract';

-- 2. Verify tv_ table exists in foreign schema
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'management' AND tablename = 'tv_organization';

-- 3. Test JOIN manually
SELECT
    tb.pk_contract,
    tv_org.data
FROM tenant.tb_contract tb
LEFT JOIN management.tv_organization tv_org
    ON tb.fk_customer_org = tv_org.pk_organization
LIMIT 1;
```

**Common Fixes**:

**1. Foreign schema not in search_path**:
```sql
-- Add to search_path
ALTER DATABASE your_db SET search_path TO tenant, management, catalog, public;
```

**2. Foreign table_view not generated**:
```yaml
# In organization.yaml
entity: Organization
schema: management

# ✅ Ensure Organization has table_views configured
table_views:
  mode: force  # Generate even without includes
```

**3. Domain registry not configured**:
```yaml
# registry/domain_registry.yaml
management:
  tier: shared
  entities:
    - Organization  # ← Must be registered

catalog:
  tier: shared
  entities:
    - Currency  # ← Must be registered
```

---

## Summary

### Key Takeaways

✅ **Wildcards eliminate maintenance**: Use `fields: ["*"]` for automatic field composition
✅ **Cross-schema just works**: Schema resolution is automatic via domain registry
✅ **Nesting is powerful**: Compose from already-denormalized table views
✅ **Performance is excellent**: Pre-composed JSONB + Rust FraiseQL = fast queries
✅ **Storage is the tradeoff**: ~20x increase for denormalized data

### Quick Reference

| Feature | Syntax | Use Case |
|---------|--------|----------|
| Wildcard | `fields: ["*"]` | Include all fields, zero maintenance |
| Explicit | `fields: [a, b, c]` | Selective inclusion, smaller payloads |
| Cross-schema | `schema: management` | Reference entities in other schemas |
| Nesting | `include_relations: [...]` | Multi-level composition |
| Hot-path filter | `extra_filter_columns` | Fast WHERE clauses with btree |

### Next Steps

1. **Read**: [YAML Reference - Table Views](../reference/yaml-reference.md#7-table-views-section-cqrs-read-layer)
2. **Review**: [Cross-Schema Example](../entities/examples/contract_cross_schema.yaml)
3. **Explore**: [CQRS Architecture](../architecture/CQRS_TABLE_VIEWS_IMPLEMENTATION.md)
4. **Test**: Generate your first table view and inspect the JSONB structure

---

**Questions or Issues?**
📧 Open an issue on GitHub with `[table_views]` tag
📖 See also: [FraiseQL Integration Guide](./fraiseql-integration.md)

**Last Updated**: 2025-11-10
**SpecQL Version**: 1.1.0+
