# CQRS Table Views - Implementation Summary

**Date**: 2025-11-09
**Status**: 🔴 APPROVED - Ready for Implementation
**Total Timeline**: 4-5 weeks (parallel with existing Team B work)

---

## 🎯 Executive Summary

SpecQL now implements a **three-layer CQRS architecture** for optimal read performance and FraiseQL integration:

1. **tb_ tables** (Write Side) - Normalized storage
2. **tv_ tables** (Read Side) - Denormalized JSONB
3. **FraiseQL** (Query Layer) - Auto-generated GraphQL

**Key Innovation**: `tv_` tables compose JSONB from related `tv_` tables (not `tb_`), creating cascading denormalization.

---

## 📚 Documentation Created

### **Core Architecture**
- **`CQRS_TABLE_VIEWS_IMPLEMENTATION.md`** - Complete architecture specification (1,100+ lines)
  - Three-layer architecture explained
  - JSONB composition strategy
  - Performance optimization (B-tree vs GIN)
  - SpecQL configuration reference
  - Complete examples

---

### **Team Implementation Plans**

| Team | Document | Timeline | Lines of Code | Status |
|------|----------|----------|---------------|--------|
| **Team A** | `TEAM_A_CQRS_TABLE_VIEWS_PLAN.md` | 3-4 days | ~1,100 | 🟡 Ready |
| **Team B** | `TEAM_B_PHASE_9_TABLE_VIEWS.md` | 7-8 days | ~1,450 | 🔴 Critical |
| **Team C** | `TEAM_C_CQRS_TV_REFRESH.md` | 3-4 days | ~800 | 🟡 Ready |
| **Team D** | `TEAM_D_CQRS_TV_ANNOTATIONS.md` | 2-3 days | ~600 | 🟢 Low Priority |

**Total New Code**: ~3,950 lines across 4 teams

---

## 🏗️ Architecture at a Glance

### **Data Flow**

```
┌─────────────────────────────────────────────────────────┐
│  User GraphQL Mutation                                   │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  PL/pgSQL Function (Team C)                             │
│  1. Write to tb_review (normalized)                     │
│  2. PERFORM refresh_tv_review(pk)                       │
│  3. Return tv_review.data (denormalized JSONB)          │
└──────────────┬──────────────────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
┌─────────────┐ ┌─────────────────────────────────────────┐
│  tb_review  │ │  tv_review (Team B)                     │
│  (Write)    │ │  - pk, id, tenant_id                    │
│  Normalized │ │  - fk_author, author_id (UUID)          │
│             │ │  - fk_book, book_id (UUID)              │
│             │ │  - rating, created_at (filter columns)  │
│             │ │  - data JSONB (composed from tv_user    │
│             │ │    + tv_book)                            │
└─────────────┘ └──────────────┬──────────────────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │  FraiseQL (External)          │
               │  1. Introspects tv_review     │
               │  2. Reads data JSONB structure│
               │  3. Auto-generates GraphQL    │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │  GraphQL API                  │
               │  type Review {                │
               │    author: ReviewAuthor!      │
               │    book: ReviewBook!          │
               │  }                            │
               └───────────────────────────────┘
```

---

## 🎯 Key Decisions Implemented

### **1. Configuration Naming**

✅ **APPROVED**: `table_views` (matches `tv_` prefix)
- Global config: `defaults.table_views`
- Entity config: `table_views` block
- Modes: `auto` | `force` | `disable`

---

### **2. JSONB Composition Strategy**

✅ **APPROVED**: Compose from `tv_` tables, not `tb_` tables

**Example**:
```sql
-- Refresh tv_review by composing from tv_ tables
SELECT
    jsonb_build_object(
        'author', tv_user.data,  -- From tv_user (not tb_user!)
        'book', tv_book.data     -- From tv_book (not tb_book!)
    ) AS data
FROM tb_review r
INNER JOIN tv_user ON tv_user.pk_user = r.fk_author
INNER JOIN tv_book ON tv_book.pk_book = r.fk_book;
```

**Benefits**:
- ✅ Consistency (author data identical in tv_user and tv_review)
- ✅ Reuse (nested publisher already composed in tv_book)
- ✅ Cascading updates (changes propagate through tv_ layers)

---

### **3. Performance Optimization**

✅ **APPROVED**: Two-tier filtering system

**Tier 1: Direct Columns** (100-500x faster)
- Auto-inferred: `tenant_id`, `{entity}_id`, `path`
- Explicit: `extra_filter_columns`
- Index: B-tree

**Tier 2: JSONB Queries** (slower but flexible)
- All fields in JSONB
- Index: GIN
- Works for any field

**Example**:
```yaml
table_views:
  extra_filter_columns:
    - rating       # Promoted (1000 queries/day)
    - created_at   # Promoted (500 queries/day)
    # comment NOT promoted (10 queries/day, GIN is fine)
```

---

### **4. Refresh Strategy**

✅ **APPROVED**: Explicit refresh (no triggers)

```yaml
actions:
  - name: update_rating
    steps:
      - update: Review SET rating = $new_rating
      - refresh_table_view:
          scope: self
          propagate: [author]  # Recalculate author stats
```

**Generated**:
```sql
UPDATE tb_review SET rating = $new_rating WHERE pk_review = $pk;
PERFORM refresh_tv_review($pk);         -- Self
PERFORM refresh_tv_user($fk_author);    -- Propagate
```

---

### **5. Field Selection**

✅ **APPROVED**: Explicit field selection (no depth parameter)

```yaml
table_views:
  include_relations:
    - author:
        fields: [name, email]  # Only these
    - book:
        fields: [title, isbn]
        include_relations:
          - publisher:
              fields: [name]  # Explicit nesting
```

---

## 📊 Implementation Roadmap

### **Timeline Overview**

```
Week 1: Existing Team A work (reserved fields)
  ↓
Week 2-3: Team A - Parse table_views (3-4 days)
  ↓
Week 3-6: Team B - Generate tv_ tables (7-8 days, Phase 9)
  ↓
Week 6-7: Team C - tv_ refresh in mutations (3-4 days)
  ↓
Week 7: Team D - FraiseQL annotations (2-3 days)
  ↓
Week 7-8: Integration testing & FraiseQL validation
```

**Total**: 4-5 weeks (some parallelization possible)

---

### **Dependency Graph**

```
Team A (Reserved Fields)
    ↓
Team A (table_views parsing)
    ↓
Team B (Phases 1-8) ─┐
                     ├─→ Team B (Phase 9: tv_ generation)
Team A (table_views) ─┘        ↓
                               ├─→ Team C (tv_ refresh)
                               └─→ Team D (annotations)
                                        ↓
                                  Integration Testing
```

---

## ✅ Acceptance Criteria (Global)

### **Team A**
- [ ] Parse `table_views` configuration block
- [ ] Parse `include_relations` (nested)
- [ ] Parse `extra_filter_columns`
- [ ] Add TableViewConfig to Entity AST

---

### **Team B**
- [ ] Generate tv_ table DDL with correct schema
- [ ] Auto-infer filter columns (tenant_id, {entity}_id, path)
- [ ] Generate explicit filter columns
- [ ] Generate refresh functions that compose from tv_ tables
- [ ] Generate correct indexes (B-tree + GIN)
- [ ] Dependency ordering (topological sort)

---

### **Team C**
- [ ] Compile `refresh_table_view` action step
- [ ] Generate PERFORM calls in mutations
- [ ] Handle scopes (self, related, propagate, batch)
- [ ] Return tv_.data in mutation results
- [ ] Cascading refresh for calculated fields

---

### **Team D**
- [ ] Generate @fraiseql:table annotations
- [ ] Generate @fraiseql:filter annotations
- [ ] Generate @fraiseql:jsonb annotations
- [ ] Mark internal columns correctly

---

### **Integration**
- [ ] End-to-end: SpecQL → SQL → Database → FraiseQL
- [ ] Performance validation (B-tree 100x faster than GIN)
- [ ] JSONB composition works (tv_ composes from tv_)
- [ ] Cascading refresh works
- [ ] FraiseQL auto-generates correct GraphQL types

---

## 📋 Configuration Examples

### **Minimal (Auto Mode)**

```yaml
entity: Review
fields:
  author: ref(User)
  book: ref(Book)

# NO table_views block needed!
# Auto-generates tv_review with all fields
```

---

### **Explicit Field Selection**

```yaml
entity: Review
fields:
  rating: integer
  author: ref(User)
  book: ref(Book)

table_views:
  include_relations:
    - author:
        fields: [name, email]  # Only these
    - book:
        fields: [title, isbn]
        include_relations:
          - publisher:
              fields: [name, country]

  extra_filter_columns:
    - rating       # High-volume queries
    - created_at   # Date ranges
```

---

### **Force tv_ Without Foreign Keys**

```yaml
entity: AuditLog
fields:
  message: text

table_views:
  mode: force  # Generate tv_ even without refs
```

---

### **Disable tv_ for Write-Heavy Table**

```yaml
entity: SessionToken
fields:
  user: ref(User)

table_views:
  mode: disable  # No tv_ generation
```

---

## 🎯 Success Metrics

### **Performance**

- ✅ Filter queries on promoted columns: **< 1ms** (B-tree)
- ✅ Filter queries on JSONB fields: **< 100ms** (GIN)
- ✅ Refresh operations: **Single-pass JOINs** (no N+1)

---

### **Code Leverage**

- ✅ User writes: **10-20 lines** of SpecQL
- ✅ Generated: **2000+ lines** of SQL (100x leverage)
- ✅ FraiseQL generates: **Complete GraphQL API** (automatic)

---

### **Developer Experience**

- ✅ **Zero manual GraphQL** schema definition
- ✅ **Zero manual resolver** implementation
- ✅ **Automatic query optimization** via filter columns
- ✅ **Type-safe** JSONB composition

---

## 🚀 Next Steps

1. **Review & Approve** - Confirm all design decisions
2. **Team A** - Start table_views parsing (Week 2-3)
3. **Team B** - Continue existing phases, add Phase 9 (Week 3-6)
4. **Team C** - Implement tv_ refresh integration (Week 6-7)
5. **Team D** - Generate FraiseQL annotations (Week 7)
6. **Integration Testing** - End-to-end validation (Week 7-8)

---

## 📚 Related Documentation

- `DATABASE_DECISIONS_FINAL.md` - Database architecture decisions
- `DATABASE_ASSESSMENT_GAPS.md` - Assessment analysis
- Team A/B/C/D original plans - Base implementation
- FraiseQL documentation (external)

---

**Status**: 🔴 APPROVED FOR IMPLEMENTATION
**Owner**: All Teams (A, B, C, D)
**Start Date**: Week 2 (Team A)
**Estimated Completion**: Week 8

---

**Last Updated**: 2025-11-09
**Document Version**: 1.0
