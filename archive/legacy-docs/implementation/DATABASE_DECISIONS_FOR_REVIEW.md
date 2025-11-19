# Database Assessment: Items Requiring Your Review/Decision

**Date**: 2025-11-08
**Purpose**: Extract critical implementation decisions that need explicit approval before Team B starts
**Status**: Awaiting review

---

## ✅ **Already Decided (No Further Review Needed)**

| Item | Your Decision | Status |
|------|---------------|--------|
| LTREE Path Strategy | INTEGER-based (`1.5.23.47`) | ✅ APPROVED |
| Identifier Slugs | ASCII with unaccent | ✅ APPROVED |
| Max Hierarchy Depth | 20 levels | ✅ APPROVED |
| Multi-Tenancy | `tenant_id UUID` direct | ✅ APPROVED |
| Trinity Naming | `pk_* INTEGER`, `id UUID` | ✅ APPROVED |
| UUID Version | **v4 (NOT v7)** | ✅ APPROVED |

---

## 🔴 **CRITICAL ITEMS - Need Your Explicit Approval**

### 1. 🔴 **Deduplication Schema: 3-Field Pattern**

**What**: Handle duplicate identifiers with separate `sequence_number` column

**Schema**:
```sql
CREATE TABLE tb_location (
    identifier TEXT NOT NULL,              -- Base: "headquarters"
    sequence_number INTEGER DEFAULT 1,     -- Sequence: 1, 2, 3...
    display_identifier TEXT GENERATED ALWAYS AS (
        CASE WHEN sequence_number > 1
            THEN identifier || '#' || sequence_number
            ELSE identifier
        END
    ) STORED,                              -- Display: "headquarters", "headquarters#2"

    UNIQUE (identifier, sequence_number),
    UNIQUE (display_identifier)
);
```

**Example Data**:
```
pk | identifier   | sequence_number | display_identifier
---|--------------|-----------------|-------------------
23 | headquarters | 1               | headquarters
45 | headquarters | 2               | headquarters#2
67 | headquarters | 3               | headquarters#3
```

**Benefits**:
- ✅ Clean queries: `WHERE identifier = 'headquarters'` returns all variants
- ✅ Concurrency-safe: Atomic sequence increment
- ✅ Migration-friendly: Sequence persists if identifier format changes

**Your Decision Needed**:
- ⚠️ **Approve this 3-field pattern?** (identifier + sequence_number + display_identifier)
- ⚠️ **Approve `#` as separator?** (Could be `-` or `_` instead)
- ⚠️ **Approve sequence starting at 1?** (First instance has no suffix)

**Recommendation**: ✅ APPROVE - This is industry best practice

---

### 2. 🔴 **slugify() Edge Case Handling**

**What**: How to handle edge cases when generating slugs

**Edge Cases**:

| Input | Current Behavior | Your Approval? |
|-------|------------------|----------------|
| `""` (empty) | → `"unnamed"` | ⚠️ Approve fallback? |
| `"123"` (all digits) | → `"n-123"` | ⚠️ Approve `n-` prefix? |
| `"---"` (all special) | → `"unnamed"` | ⚠️ Approve fallback? |
| `"Café"` | → `"cafe"` (unaccented) | ✅ Already approved (ASCII) |

**Functions Generated**:
```sql
-- Three functions (assessment recommendation):
slugify_immutable(value)      -- For generated columns (strict, IMMUTABLE)
slugify(value)                -- For triggers (runtime detection, STABLE)
slugify_safe(value, fallback) -- With edge case handling
```

**Your Decision Needed**:
- ⚠️ **Approve "unnamed" as default fallback** for empty/invalid inputs?
- ⚠️ **Approve "n-" prefix** for all-digit slugs (e.g., "123" → "n-123")?
- ⚠️ **Approve generating all 3 functions**, or just `slugify_safe`?

**Alternative**: Generate only `slugify_safe()` and use it everywhere (simpler)

**Recommendation**:
- ✅ APPROVE "unnamed" fallback
- ✅ APPROVE "n-" prefix for digits
- ⚠️ **Your choice**: All 3 functions OR just `slugify_safe()`?

---

### 3. 🔴 **Partial Indexes: `WHERE deleted_at IS NULL`**

**What**: Add `WHERE deleted_at IS NULL` to ALL non-PK indexes

**Current**:
```sql
CREATE INDEX idx_location_parent ON tb_location(fk_parent_location);
CREATE INDEX idx_location_path ON tb_location USING GIST (path);
```

**Proposed**:
```sql
CREATE INDEX idx_location_parent
    ON tb_location(fk_parent_location)
    WHERE deleted_at IS NULL;  -- ← NEW

CREATE INDEX idx_location_path
    ON tb_location USING GIST (path)
    WHERE deleted_at IS NULL;  -- ← NEW
```

**Benefits**:
- ✅ 10-50% smaller indexes (excludes soft-deleted rows)
- ✅ 10-20% faster queries (90%+ of queries ignore deleted rows)
- ✅ Better VACUUM performance

**Trade-off**:
- ❌ Queries that INCLUDE deleted rows won't use these indexes
  ```sql
  -- This query WON'T use partial index:
  SELECT * FROM tb_location WHERE deleted_at IS NOT NULL;

  -- But this is rare (admin/audit queries only)
  ```

**Your Decision Needed**:
- ⚠️ **Approve partial indexes on ALL non-PK indexes?**
- ⚠️ **Exception**: Keep full indexes on audit fields (created_at, updated_at)?

**Recommendation**: ✅ APPROVE - Standard best practice for soft-delete patterns

---

### 4. 🔴 **Safety Constraint Triggers: 4 Critical Checks**

**What**: Generate triggers to prevent data corruption

#### A. Prevent Circular References
```sql
-- Prevents: Location A → B → C → A (infinite loop)
CREATE TRIGGER trg_prevent_location_cycle
    BEFORE INSERT OR UPDATE OF fk_parent_location
    ON tb_location
    FOR EACH ROW
    EXECUTE FUNCTION prevent_location_cycle();
```

**Your Decision**: ⚠️ **Approve auto-generating this trigger?**

---

#### B. Check Identifier Sequence Limit
```sql
-- Prevents: More than 100 variants of same identifier
-- Example: headquarters, headquarters#2, ... headquarters#101 ❌

CREATE TRIGGER trg_check_sequence_limit
    BEFORE INSERT OR UPDATE OF sequence_number
    ON tb_location
    FOR EACH ROW
    EXECUTE FUNCTION check_identifier_sequence_limit();
```

**Your Decision**:
- ⚠️ **Approve limit of 100 duplicates?**
- ⚠️ **Or different limit** (50? 200? No limit?)

**Recommendation**: 100 is reasonable (prevents runaway duplicates)

---

#### C. Validate Identifier Format
```sql
-- Prevents: Invalid characters in identifiers
-- Disallowed: < > " ' \ / : * ? |

CREATE TRIGGER trg_validate_identifier
    BEFORE INSERT OR UPDATE OF identifier
    ON tb_location
    FOR EACH ROW
    EXECUTE FUNCTION validate_location_identifier();
```

**Your Decision**:
- ⚠️ **Approve these disallowed characters?**
- ⚠️ **Or different set?** (e.g., allow `/` for paths?)

**Recommendation**: ✅ APPROVE - These break most systems (Windows filenames, URLs, etc.)

---

#### D. Check Hierarchy Depth Limit
```sql
-- Prevents: More than 20 levels deep
-- Already decided: 20 levels max

CREATE TRIGGER trg_check_depth_limit
    BEFORE INSERT OR UPDATE OF path
    ON tb_location
    FOR EACH ROW
    EXECUTE FUNCTION check_hierarchy_depth_limit();
```

**Your Decision**: ✅ **Already approved** (20 levels)

---

**Summary Decision for Safety Triggers**:
- ⚠️ **Approve ALL 4 safety triggers?**
- ⚠️ **Or make them optional** (configurable per project)?

**Recommendation**: ✅ APPROVE ALL - Essential for data integrity

---

### 5. 🔴 **Separate Audit Fields for Identifier Recalculation**

**What**: Don't update `updated_at` when identifier recalculates

**Current** (problematic):
```sql
-- User renames location:
UPDATE tb_location
SET name = 'New HQ', updated_at = now()  -- ✅ Correct
WHERE pk_location = 23;

-- System recalculates identifier (due to parent change):
UPDATE tb_location
SET identifier = 'new-identifier', updated_at = now()  -- ❌ Wrong! No business data changed
WHERE pk_location = 47;
```

**Proposed**:
```sql
CREATE TABLE tb_location (
    -- Business data audit
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),  -- Only for business changes

    -- Identifier audit (NEW)
    identifier_recalculated_at TIMESTAMPTZ,  -- When identifier changed
    identifier_recalculated_by UUID,

    -- Path audit (NEW)
    path_updated_at TIMESTAMPTZ,  -- When path changed (parent move)
    path_updated_by UUID
);
```

**Benefits**:
- ✅ Frontend knows when **actual** business data changed
- ✅ Audit trail distinguishes business edits from system recalculations
- ✅ Webhooks/triggers don't fire on system maintenance

**Your Decision Needed**:
- ⚠️ **Approve separate audit fields?**
- ⚠️ **Or keep simple** (always update `updated_at`)?

**Recommendation**: ✅ APPROVE - Critical for correct frontend behavior

---

### 6. 🔴 **Index Strategy: 6 Mandatory Indexes**

**What**: Always generate these 6 indexes for every entity

#### Mandatory for ALL Entities:
```sql
1. PRIMARY KEY (pk_location)           -- INTEGER (automatic)
2. UNIQUE (id)                         -- UUID
3. UNIQUE (display_identifier)         -- TEXT (with #n suffix)
```

#### Conditional (based on entity type):
```sql
4. GIST (path)                         -- If hierarchical: true
   WHERE deleted_at IS NULL

5. INDEX (fk_parent_location)          -- If hierarchical: true
   WHERE deleted_at IS NULL

6. INDEX (fk_location_info)            -- If metadata_split: true
```

**Your Decision Needed**:
- ⚠️ **Approve these as MANDATORY** (not configurable)?
- ⚠️ **Or allow users to opt-out** of specific indexes?

**Recommendation**: ✅ APPROVE as mandatory - Essential for performance

---

### 7. 🔴 **Reserved Field Names: Block These**

**What**: Error if user tries to define these field names

**Reserved Names**:
```yaml
# User tries to define:
entity: Location
fields:
  id: text              # ❌ ERROR: "id" is reserved
  path: text            # ❌ ERROR: "path" is reserved
  created_at: integer   # ❌ ERROR: "created_at" is reserved
```

**Full Reserved List**:
- `id`, `pk_*`, `fk_*` (primary/foreign keys)
- `identifier`, `sequence_number`, `display_identifier` (deduplication)
- `path`, `fk_parent_*` (hierarchy)
- `created_at`, `updated_at`, `deleted_at`, `created_by`, `updated_by`, `deleted_by` (audit)
- `identifier_recalculated_at`, `identifier_recalculated_by`, `path_updated_at`, `path_updated_by` (recalc audit)
- `tenant_id` (multi-tenancy)

**Your Decision Needed**:
- ⚠️ **Approve blocking ALL these names?**
- ⚠️ **Or allow some** (e.g., user can define `id` but framework warns)?

**Recommendation**: ✅ APPROVE hard block - Prevents conflicts

---

## 🟡 **NICE-TO-HAVE ITEMS - Lower Priority**

### 8. 🟡 **Async Recalculation Queue (Week 8+)**

**What**: Queue large recalculations (> 1000 nodes) for background processing

**Thresholds** (from assessment benchmarks):
- 1-100 nodes: Immediate (< 300ms) ✅
- 100-1,000 nodes: Immediate with warning (300ms-2s) ⚠️
- 1,000+ nodes: **Queue for async** (2s-30s) ❌

**Your Decision**:
- ⚠️ **Implement in MVP (Week 2-4)?**
- ⚠️ **Or defer to Week 8+?**

**Recommendation**: Defer to Week 8+ (most hierarchies < 1000 nodes)

---

### 9. 🟡 **Helper Functions for Hierarchies (Week 3-4)**

**What**: Auto-generate convenience functions

```sql
get_location_ancestors(id UUID)
get_location_descendants(id UUID)
move_location_subtree(id UUID, new_parent UUID)
get_location_root(id UUID)
get_location_depth(id UUID)
```

**Your Decision**:
- ⚠️ **Generate these automatically?**
- ⚠️ **Or on-demand** (user opts in)?

**Recommendation**: Auto-generate (good DX, minimal cost)

---

### 10. 🟡 **Node+Info Split: Opt-In Syntax (Week 8+)**

**What**: Allow users to split complex entities

```yaml
entity: Location
metadata_split: true  # ← User opts in

# Generates:
# - tb_location_node (structure: path, parent)
# - tb_location_info (attributes: name, type, etc.)
# - v_location (view combining both)
```

**Your Decision**:
- ⚠️ **Support this in MVP?**
- ⚠️ **Or defer?**

**Recommendation**: Defer to Week 8+ (single table works fine initially)

---

## 📋 **DECISION SUMMARY CHECKLIST**

Please review and approve/modify:

### 🔴 **CRITICAL (Need Before Week 2)**

- [ ] **Deduplication**: 3-field pattern (identifier, sequence_number, display_identifier)
- [ ] **Deduplication**: Use `#` as separator
- [ ] **Deduplication**: First instance has no suffix (starts at 1)
- [ ] **slugify()**: "unnamed" fallback for empty/invalid inputs
- [ ] **slugify()**: "n-" prefix for all-digit slugs
- [ ] **slugify()**: Generate all 3 functions OR just slugify_safe()?
- [ ] **Partial Indexes**: Add `WHERE deleted_at IS NULL` to all non-PK indexes
- [ ] **Safety Triggers**: Generate all 4 constraint triggers
- [ ] **Safety Triggers**: 100 duplicate limit (or different?)
- [ ] **Safety Triggers**: Disallow characters: `< > " ' \ / : * ? |`
- [ ] **Audit Fields**: Add separate identifier/path recalculation tracking
- [ ] **Index Strategy**: 6 mandatory indexes (not configurable)
- [ ] **Reserved Names**: Block all reserved field names (hard error)

### 🟡 **NICE-TO-HAVE (Can Defer)**

- [ ] **Async Queue**: Implement now OR defer to Week 8+?
- [ ] **Helper Functions**: Auto-generate OR on-demand?
- [ ] **Node+Info Split**: Support now OR defer?

---

## 🎯 **Next Steps**

1. **Review this document** and mark your decisions above
2. **Let me know your decisions** on critical items
3. **I'll update DATABASE_ASSESSMENT_GAPS.md** with your final approvals
4. **Team B can start implementation** once all critical items approved

---

**Your Current Decisions**:
- ✅ UUID v4 (NOT v7)
- ✅ INTEGER-based LTREE paths
- ✅ ASCII slugification
- ✅ 20-level max depth
- ✅ tenant_id UUID direct

**Pending Decisions**: 13 critical items above ⬆️
