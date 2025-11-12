# Database Architecture: Final Decisions

**Date**: 2025-11-08
**Status**: ✅ ALL DECISIONS MADE - Ready for Implementation

---

## ✅ **APPROVED DECISIONS**

### **Core Architecture**

| Decision | Approved Choice | Notes |
|----------|----------------|-------|
| **UUID Version** | v4 (gen_random_uuid) | Built-in, simple, secure |
| **LTREE Path Strategy** | INTEGER-based (`1.5.23.47`) | Uses pk_{entity}, pure digits |
| **Identifier Slugs** | ASCII with unaccent | safe_slug from printoptim_backend |
| **Max Hierarchy Depth** | 20 levels | Enabled by INTEGER paths |
| **Multi-Tenancy** | tenant_id UUID direct | No mapping table |
| **Trinity Naming** | pk_* INTEGER, id UUID | Frontend-first |

---

### **1. ✅ Deduplication: 3-Field Pattern**

**APPROVED**:
```sql
CREATE TABLE tb_location (
    identifier TEXT NOT NULL,              -- Base: "headquarters"
    sequence_number INTEGER DEFAULT 1,     -- Sequence: 1, 2, 3...
    display_identifier TEXT GENERATED ALWAYS AS (
        CASE WHEN sequence_number > 1
            THEN identifier || '#' || sequence_number
            ELSE identifier
        END
    ) STORED,                              -- Display: "headquarters#2"

    UNIQUE (identifier, sequence_number),
    UNIQUE (display_identifier)
);
```

**Details**:
- ✅ Use `#` as separator
- ✅ First instance has no suffix (sequence starts at 1)
- ✅ Generated column for display

---

### **2. ✅ slugify(): safe_slug Pattern**

**APPROVED**: Use `safe_slug` from printoptim_backend

**Generate ONLY ONE function**:
```sql
CREATE FUNCTION public.safe_slug(
    value TEXT,
    fallback TEXT DEFAULT 'unnamed'
) RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    IF value IS NULL OR trim(value) = '' THEN
        RETURN fallback;
    END IF;

    -- Unaccent + lowercase + replace non-alphanumeric
    result := trim(BOTH '-' FROM regexp_replace(
        lower(unaccent(value)),
        '[^a-z0-9]+', '-', 'gi'
    ));

    -- Handle edge cases
    IF result = '' THEN
        RETURN fallback;
    ELSIF result ~ '^[0-9]+$' THEN
        -- All digits: prefix with 'n-'
        RETURN 'n-' || result;
    ELSE
        RETURN result;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

**Edge Cases**:
- ✅ Empty strings → "unnamed"
- ✅ All digits → "n-123"
- ✅ All special chars → "unnamed"
- ✅ Unicode → Unaccented (ASCII)

**NO other slugify variants** (slugify_immutable, slugify) - Keep it simple!

---

### **3. ✅ Partial Indexes: WHERE deleted_at IS NULL**

**APPROVED**: Add to ALL non-PK indexes

```sql
CREATE INDEX idx_location_parent
    ON tb_location(fk_parent_location)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_location_path
    ON tb_location USING GIST (path)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_location_type
    ON tb_location(fk_location_type)
    WHERE deleted_at IS NULL;
```

**Benefits**: 10-50% smaller indexes, 10-20% faster queries

---

### **4. ✅ Safety Triggers: 3 of 4 Triggers**

**APPROVED TRIGGERS**:

#### A. ✅ Prevent Circular References
```sql
CREATE TRIGGER trg_prevent_{entity}_cycle
    BEFORE INSERT OR UPDATE OF fk_parent_{entity}
    ON tb_{entity}
    FOR EACH ROW
    EXECUTE FUNCTION prevent_{entity}_cycle();
```

#### B. ✅ Check Identifier Sequence Limit
```sql
CREATE TRIGGER trg_check_sequence_limit
    BEFORE INSERT OR UPDATE OF sequence_number
    ON tb_{entity}
    FOR EACH ROW
    EXECUTE FUNCTION check_identifier_sequence_limit();
```
**Limit**: 100 duplicates max

#### C. ❌ Validate Identifier Format - **REMOVED**
**Rationale**: `safe_slug()` already handles this (sanitizes input)

#### D. ✅ Check Hierarchy Depth Limit
```sql
CREATE TRIGGER trg_check_depth_limit
    BEFORE INSERT OR UPDATE OF path
    ON tb_{entity}
    FOR EACH ROW
    EXECUTE FUNCTION check_hierarchy_depth_limit();
```
**Limit**: 20 levels max

**Total**: 3 safety triggers per hierarchical entity

---

### **5. ✅ Separate Audit Fields for Recalculation**

**APPROVED**:
```sql
CREATE TABLE tb_location (
    -- Business data audit
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    -- Identifier recalculation audit (NEW)
    identifier_recalculated_at TIMESTAMPTZ,
    identifier_recalculated_by UUID,

    -- Path recalculation audit (NEW)
    path_updated_at TIMESTAMPTZ,
    path_updated_by UUID
);
```

**Rule**:
- Business data changes → Update `updated_at`
- Identifier recalculation → Update `identifier_recalculated_at` (NOT updated_at)
- Path recalculation → Update `path_updated_at` (NOT updated_at)

---

### **6. ✅ Index Strategy: 6 Mandatory + Tenant Indexes**

**APPROVED**: 6 core indexes + tenant-scoped indexes

#### Core Indexes (ALL entities):
```sql
1. PRIMARY KEY (pk_{entity})           -- INTEGER (automatic)
2. UNIQUE (id)                         -- UUID
3. UNIQUE (display_identifier)         -- TEXT
```

#### Hierarchical Indexes (if hierarchical: true):
```sql
4. GIST (path)                         -- LTREE hierarchy queries
   WHERE deleted_at IS NULL

5. INDEX (fk_parent_{entity})          -- Parent lookups
   WHERE deleted_at IS NULL
```

#### Split Indexes (if metadata_split: true):
```sql
6. INDEX (fk_{entity}_info)            -- Join optimization
```

#### **NEW: Tenant-Scoped Indexes** (if multi_tenant: true):
```sql
7. INDEX (tenant_id)                   -- Tenant isolation
   WHERE deleted_at IS NULL

8. INDEX (tenant_id, path)             -- Tenant + hierarchy queries
   WHERE deleted_at IS NULL

9. INDEX (tenant_id, fk_parent_{entity})  -- Tenant + parent queries
   WHERE deleted_at IS NULL
```

**Total**: Up to 9 indexes per entity (depending on type)

**Benefits**:
- ✅ Tenant queries 5-10x faster
- ✅ RLS policies use tenant_id index efficiently
- ✅ Composite indexes prevent full table scans

---

### **7. ✅ Reserved Field Names: Hard Block**

**APPROVED**: Error if user tries to define these

**Reserved Names**:
```python
RESERVED_FIELD_NAMES = {
    # Primary/Foreign Keys
    'id', 'pk_*', 'fk_*',

    # Deduplication
    'identifier', 'sequence_number', 'display_identifier',

    # Hierarchy
    'path', 'fk_parent_*',

    # Business Audit
    'created_at', 'created_by',
    'updated_at', 'updated_by',
    'deleted_at', 'deleted_by',

    # Recalculation Audit
    'identifier_recalculated_at', 'identifier_recalculated_by',
    'path_updated_at', 'path_updated_by',

    # Multi-Tenancy
    'tenant_id',
}
```

**Error Message**:
```
Error: Field name 'path' is reserved by the framework.
Reserved fields: id, pk_*, fk_*, identifier, path, created_at, updated_at, ...
Please choose a different field name.
```

---

### **8. ⏸️ Async Recalculation Queue: DEFERRED**

**DECISION**: Defer to Week 8+

**Rationale**: Most hierarchies < 1000 nodes, can add later as optimization

---

### **9. ✅ Helper Functions: Generate if Facilitates Function Generation**

**APPROVED**: Auto-generate these convenience functions

```sql
-- For each hierarchical entity, generate:

get_{entity}_ancestors(p_id UUID)      -- Get all ancestor nodes
get_{entity}_descendants(p_id UUID)    -- Get all descendant nodes
move_{entity}_subtree(p_id UUID, p_new_parent UUID)  -- Move subtree
get_{entity}_root(p_id UUID)           -- Find root node
get_{entity}_depth(p_id UUID)          -- Get depth in tree
```

**Rationale**:
- ✅ FraiseQL provides rich LTREE filters
- ✅ But these functions make it easier for Team C to generate business logic
- ✅ Pre-built, tested, reusable patterns

**When to Generate**: Automatically for ALL hierarchical entities

---

### **10. ✅ Node+Info Split: IMPLEMENT NOW**

**APPROVED**: Implement in Week 2-3 (not deferred!)

**YAML Syntax**:
```yaml
entity: Location
hierarchical: true
metadata_split: true  # ← User opts in

fields:
  name: text
  description: text
  # ... 10+ business fields
```

**Generated Schema**:
```sql
-- Structure table (hierarchy only)
CREATE TABLE tb_location_node (
    pk_location INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    tenant_id UUID,

    -- Hierarchy fields
    path ltree NOT NULL,
    fk_parent_location INTEGER REFERENCES tb_location_node(pk_location),

    -- Foreign key to info
    fk_location_info INTEGER NOT NULL,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ,

    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, path)
);

-- Attributes table (business data)
CREATE TABLE tb_location_info (
    pk_location_info INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    tenant_id UUID,

    -- Deduplication
    identifier TEXT NOT NULL,
    sequence_number INTEGER DEFAULT 1,
    display_identifier TEXT GENERATED ALWAYS AS (...) STORED,

    -- Business fields
    name TEXT,
    description TEXT,
    fk_location_type INTEGER,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID,

    UNIQUE (tenant_id, display_identifier)
);

-- Convenience view
CREATE VIEW v_location AS
SELECT
    n.pk_location,
    n.id,
    n.tenant_id,
    n.path,
    n.fk_parent_location,
    i.identifier,
    i.sequence_number,
    i.display_identifier,
    i.name,
    i.description,
    i.fk_location_type,
    n.created_at,
    i.updated_at,
    i.updated_by,
    n.deleted_at
FROM tb_location_node n
JOIN tb_location_info i ON i.pk_location_info = n.fk_location_info
WHERE n.deleted_at IS NULL;
```

**Benefits**:
- ✅ Cleaner separation (structure vs attributes)
- ✅ Easier versioning (info table can have multiple versions)
- ✅ Better schema evolution (alter info without touching structure)
- ✅ Reusable hierarchy patterns across entities

**When to Use**:
- Complex entities (10+ business fields)
- Frequent attribute updates
- Temporal/versioning requirements

**Default**: Single table (simpler), opt-in to split via `metadata_split: true`

---

## 📋 **IMPLEMENTATION SUMMARY**

### **Core Schema Pattern**:
```sql
CREATE TABLE tb_{entity} (
    -- Trinity Pattern
    pk_{entity} INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,

    -- Multi-Tenancy
    tenant_id UUID NOT NULL,

    -- Hierarchy (if hierarchical: true)
    path ltree NOT NULL,  -- INTEGER-based: '1.5.23.47'
    fk_parent_{entity} INTEGER REFERENCES tb_{entity}(pk_{entity}),

    -- Deduplication
    identifier TEXT NOT NULL,
    sequence_number INTEGER DEFAULT 1,
    display_identifier TEXT GENERATED ALWAYS AS (
        CASE WHEN sequence_number > 1
            THEN identifier || '#' || sequence_number
            ELSE identifier
        END
    ) STORED,

    -- Business fields
    name TEXT,
    -- ... user-defined fields

    -- Business Audit
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    -- Recalculation Audit
    identifier_recalculated_at TIMESTAMPTZ,
    identifier_recalculated_by UUID,
    path_updated_at TIMESTAMPTZ,
    path_updated_by UUID,

    -- Constraints
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, display_identifier),
    UNIQUE (tenant_id, path),
    UNIQUE (identifier, sequence_number)
);

-- Core Indexes
CREATE INDEX idx_{entity}_tenant ON tb_{entity}(tenant_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_{entity}_tenant_path ON tb_{entity}(tenant_id, path)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_{entity}_parent ON tb_{entity}(fk_parent_{entity})
    WHERE deleted_at IS NULL;
CREATE INDEX idx_{entity}_path ON tb_{entity} USING GIST (path)
    WHERE deleted_at IS NULL;

-- Utility Functions
CREATE FUNCTION public.safe_slug(value TEXT, fallback TEXT DEFAULT 'unnamed')
    RETURNS TEXT AS $$ ... $$ LANGUAGE plpgsql IMMUTABLE;

-- Path Calculation
CREATE FUNCTION calculate_{entity}_path(p_pk INTEGER)
    RETURNS ltree AS $$ ... $$ LANGUAGE plpgsql IMMUTABLE;

-- Safety Triggers (3)
CREATE TRIGGER trg_prevent_{entity}_cycle ...;
CREATE TRIGGER trg_check_sequence_limit ...;
CREATE TRIGGER trg_check_depth_limit ...;

-- Helper Functions (5)
CREATE FUNCTION get_{entity}_ancestors(p_id UUID) ...;
CREATE FUNCTION get_{entity}_descendants(p_id UUID) ...;
CREATE FUNCTION move_{entity}_subtree(p_id UUID, p_new_parent UUID) ...;
CREATE FUNCTION get_{entity}_root(p_id UUID) ...;
CREATE FUNCTION get_{entity}_depth(p_id UUID) ...;
```

---

## 🎯 **IMPLEMENTATION PRIORITY**

### **Week 1 (Team A)** ✅
- [x] Reserved field name validation
- [x] All architectural decisions made

### **Week 2 (Team B)** 🔴 NEXT
1. Generate `safe_slug()` utility function
2. Implement 3-field deduplication pattern
3. Generate INTEGER-based path calculation functions
4. Implement partial indexes (`WHERE deleted_at IS NULL`)
5. Add separate audit fields (identifier/path recalculation)
6. Generate tenant-scoped indexes
7. Implement 3 safety triggers
8. **NEW**: Implement node+info split pattern (opt-in)

### **Week 3-4 (Team C)**
- Use correct audit fields for recalculation
- Generate helper functions for hierarchical entities
- Idempotent recalculation logic

### **Week 8+ (Enhancements)**
- Async recalculation queue (deferred)

---

## ✅ **READY FOR IMPLEMENTATION**

All critical decisions are now **approved and documented**.

**Next Steps**:
1. Update `DATABASE_ASSESSMENT_GAPS.md` with these final decisions
2. Create implementation specs for Team B
3. Begin Week 2 implementation

---

**Last Updated**: 2025-11-08
**Status**: ✅ ALL DECISIONS FINAL - Ready for Team B
**Key Changes from Assessment**:
- ✅ INTEGER-based LTREE paths (major improvement)
- ✅ Single `safe_slug()` function (simpler)
- ✅ Tenant-scoped indexes (performance)
- ✅ Node+info split NOW (not deferred)
- ✅ 3 safety triggers (not 4)
