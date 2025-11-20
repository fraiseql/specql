# Explicit Validation Pattern - Replace Triggers with Function Calls

**Status**: 🎯 Architectural Proposal
**Impact**: Phase 7 of Team B Implementation
**Related**: `EXPLICIT_PATH_RECALCULATION.md`, Team B Plan Phase 7

---

## 🎯 Problem: Triggers are Implicit and Hidden

**Current Phase 7 Design** uses 3 triggers per hierarchical entity:
1. `prevent_cycle()` - Prevent circular references
2. `check_sequence_limit()` - Limit identifier duplicates (max 100)
3. `check_depth_limit()` - Limit hierarchy depth (max 20)

**Issues with Triggers**:
- ❌ Hidden behavior (not visible in mutation code)
- ❌ Hard to test in isolation
- ❌ Poor transaction control
- ❌ Difficult to debug (no explicit call site)
- ❌ Can't skip validation when appropriate (migrations, admin operations)
- ❌ Inconsistent with explicit pattern we established for path recalculation

---

## ✅ Solution: Explicit Validation Functions

**Same pattern as `recalculate_tree_path()`**: Mutations call validation explicitly.

### Core Principle
```python
# ❌ BAD: Hidden trigger validates automatically
UPDATE tb_location SET fk_parent = 5 WHERE pk_location = 10;
-- Trigger fires invisibly, might fail with cryptic error

# ✅ GOOD: Explicit validation before mutation
SELECT core.validate_hierarchy_change('location', 10, 5);  -- Returns error or NULL
UPDATE tb_location SET fk_parent = 5 WHERE pk_location = 10;
-- Clear validation step, visible in code, easy to debug
```

---

## 🏗️ Proposed Architecture

### 1. Generic Validation Function

**File**: `templates/sql/hierarchy/validate_hierarchy_change.sql.jinja2`

**ONE-TIME FRAMEWORK FUNCTION** (not per-entity, like `recalculate_tree_path`)

```sql
-- Validate hierarchy changes BEFORE they happen
-- Returns NULL if valid, raises EXCEPTION if invalid
-- Called explicitly from mutation functions (Team C)

CREATE TYPE core.hierarchy_validation_error AS (
    error_code TEXT,
    error_message TEXT,
    hint TEXT,
    detail JSONB
);

CREATE OR REPLACE FUNCTION core.validate_hierarchy_change(
    entity TEXT,
    node_pk INTEGER,                    -- Node being modified
    new_parent_pk INTEGER DEFAULT NULL, -- New parent (NULL for root)
    max_depth INTEGER DEFAULT 20,       -- Framework config
    check_cycle BOOLEAN DEFAULT TRUE,   -- Skip for performance if known safe
    check_depth BOOLEAN DEFAULT TRUE    -- Skip for performance if known safe
) RETURNS core.hierarchy_validation_error AS $$
DECLARE
    v_schema TEXT;
    v_table TEXT;
    v_pk_column TEXT;
    v_parent_column TEXT;
    v_node_path ltree;
    v_parent_path ltree;
    v_new_depth INTEGER;
    v_error core.hierarchy_validation_error;
    dyn_sql TEXT;
BEGIN
    IF entity IS NULL THEN
        RAISE EXCEPTION 'Parameter "entity" must not be NULL';
    END IF;

    -- Construct dynamic identifiers
    v_table := format('tb_%s', entity);
    v_pk_column := format('pk_%s', entity);
    v_parent_column := format('fk_parent_%s', entity);

    -- Find schema dynamically
    SELECT table_schema INTO v_schema
    FROM information_schema.tables
    WHERE table_name = v_table
      AND table_schema IN ('core', 'management', 'catalog', 'tenant')
    LIMIT 1;

    IF v_schema IS NULL THEN
        RAISE EXCEPTION 'Table "tb_%" not found in any expected schema', entity;
    END IF;

    -- Get current node's path
    dyn_sql := format($q$
        SELECT path FROM %I.%I WHERE %I = $1;
    $q$, v_schema, v_table, v_pk_column);
    EXECUTE dyn_sql INTO v_node_path USING node_pk;

    IF v_node_path IS NULL THEN
        v_error.error_code := 'node_not_found';
        v_error.error_message := format('%s with pk=%s not found', entity, node_pk);
        v_error.hint := 'Verify the node exists and is not deleted';
        RETURN v_error;
    END IF;

    -- If no parent change, no validation needed
    IF new_parent_pk IS NULL THEN
        RETURN NULL;  -- Valid (root node)
    END IF;

    -- Get new parent's path
    dyn_sql := format($q$
        SELECT path FROM %I.%I WHERE %I = $1;
    $q$, v_schema, v_table, v_pk_column);
    EXECUTE dyn_sql INTO v_parent_path USING new_parent_pk;

    IF v_parent_path IS NULL THEN
        v_error.error_code := 'parent_not_found';
        v_error.error_message := format('Parent %s with pk=%s not found', entity, new_parent_pk);
        v_error.hint := 'Verify the parent exists and is not deleted';
        RETURN v_error;
    END IF;

    -- VALIDATION 1: Check for circular reference (parent is descendant of node)
    IF check_cycle THEN
        IF v_parent_path <@ v_node_path THEN
            v_error.error_code := 'circular_reference';
            v_error.error_message := format(
                'Circular reference: %s (pk=%s) cannot be moved under its own descendant (pk=%s)',
                entity, node_pk, new_parent_pk
            );
            v_error.hint := 'Choose a parent that is not a descendant of this node';
            v_error.detail := jsonb_build_object(
                'node_path', v_node_path::text,
                'parent_path', v_parent_path::text,
                'node_pk', node_pk,
                'parent_pk', new_parent_pk
            );
            RETURN v_error;
        END IF;
    END IF;

    -- VALIDATION 2: Check depth limit (new parent path + 1 level)
    IF check_depth THEN
        v_new_depth := nlevel(v_parent_path) + 1;

        IF v_new_depth > max_depth THEN
            v_error.error_code := 'depth_limit_exceeded';
            v_error.error_message := format(
                'Depth limit exceeded: moving %s (pk=%s) would create depth %s (max: %s)',
                entity, node_pk, v_new_depth, max_depth
            );
            v_error.hint := 'Flatten the hierarchy or increase max_depth in framework config';
            v_error.detail := jsonb_build_object(
                'current_depth', nlevel(v_node_path),
                'new_depth', v_new_depth,
                'max_depth', max_depth,
                'parent_path', v_parent_path::text
            );
            RETURN v_error;
        ELSIF v_new_depth > (max_depth * 0.75) THEN
            -- Soft warning at 75% threshold
            RAISE WARNING 'Approaching depth limit: % of % levels (path: %)',
                v_new_depth, max_depth, v_parent_path || node_pk::text;
        END IF;
    END IF;

    -- All validations passed
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION core.validate_hierarchy_change IS
'Validate hierarchy parent changes BEFORE they happen.

Explicit over Implicit: NO TRIGGERS! Mutations call this explicitly.

Returns NULL if valid, returns error object if invalid.

Validations:
1. Circular reference check (parent is not descendant of node)
2. Depth limit check (new depth would not exceed max)

Example usage in mutations:
  DECLARE
    v_validation_error core.hierarchy_validation_error;
  BEGIN
    -- Validate before UPDATE
    v_validation_error := core.validate_hierarchy_change(
        ''location'',
        v_location_pk,
        v_new_parent_pk,
        max_depth => 20,
        check_cycle => true,
        check_depth => true
    );

    IF v_validation_error IS NOT NULL THEN
        -- Return error response
        RETURN jsonb_build_object(
            ''status'', ''error'',
            ''code'', v_validation_error.error_code,
            ''message'', v_validation_error.error_message,
            ''hint'', v_validation_error.hint,
            ''detail'', v_validation_error.detail
        );
    END IF;

    -- Safe to proceed with UPDATE
    UPDATE tenant.tb_location
    SET fk_parent_location = v_new_parent_pk
    WHERE pk_location = v_location_pk;
  END;

Based on explicit pattern from recalculate_tree_path().';
```

---

### 2. Identifier Sequence Validation

**File**: `templates/sql/hierarchy/validate_identifier_sequence.sql.jinja2`

```sql
-- Validate identifier sequence BEFORE insert/update
-- Returns NULL if valid, raises WARNING/EXCEPTION if invalid

CREATE OR REPLACE FUNCTION core.validate_identifier_sequence(
    entity TEXT,
    identifier TEXT,
    sequence_number INTEGER,
    tenant_id UUID DEFAULT NULL,  -- For tenant-scoped entities
    max_duplicates INTEGER DEFAULT 100  -- Framework config
) RETURNS core.hierarchy_validation_error AS $$
DECLARE
    v_schema TEXT;
    v_table TEXT;
    v_current_count INTEGER;
    v_error core.hierarchy_validation_error;
    dyn_sql TEXT;
BEGIN
    IF entity IS NULL THEN
        RAISE EXCEPTION 'Parameter "entity" must not be NULL';
    END IF;

    -- Construct dynamic identifiers
    v_table := format('tb_%s', entity);

    -- Find schema dynamically
    SELECT table_schema INTO v_schema
    FROM information_schema.tables
    WHERE table_name = v_table
      AND table_schema IN ('core', 'management', 'catalog', 'tenant')
    LIMIT 1;

    IF v_schema IS NULL THEN
        RAISE EXCEPTION 'Table "tb_%" not found in any expected schema', entity;
    END IF;

    -- Count existing sequences for this identifier
    IF tenant_id IS NOT NULL THEN
        -- Tenant-scoped count
        dyn_sql := format($q$
            SELECT COUNT(*)
            FROM %I.%I
            WHERE tenant_id = $1
              AND identifier = $2;
        $q$, v_schema, v_table);
        EXECUTE dyn_sql INTO v_current_count USING tenant_id, identifier;
    ELSE
        -- Global count
        dyn_sql := format($q$
            SELECT COUNT(*)
            FROM %I.%I
            WHERE identifier = $1;
        $q$, v_schema, v_table);
        EXECUTE dyn_sql INTO v_current_count USING identifier;
    END IF;

    -- Check hard limit
    IF sequence_number > max_duplicates THEN
        v_error.error_code := 'sequence_limit_exceeded';
        v_error.error_message := format(
            'Identifier sequence limit exceeded: "%s" has %s variants (max: %s)',
            identifier, sequence_number, max_duplicates
        );
        v_error.hint := format(
            'Current variant: %s#%s. Use more descriptive naming to reduce collisions.',
            identifier, sequence_number
        );
        v_error.detail := jsonb_build_object(
            'identifier', identifier,
            'sequence_number', sequence_number,
            'current_count', v_current_count,
            'max_duplicates', max_duplicates
        );
        RETURN v_error;
    END IF;

    -- Soft warning at 50% threshold
    IF sequence_number > (max_duplicates * 0.5) THEN
        RAISE WARNING 'High identifier duplication: "%" has % variants (limit: %)',
            identifier, sequence_number, max_duplicates;
    END IF;

    -- Valid
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION core.validate_identifier_sequence IS
'Validate identifier sequence numbers BEFORE insert/update.

Explicit over Implicit: NO TRIGGERS! Mutations call this explicitly.

Returns NULL if valid, returns error object if limit exceeded.

Example usage:
  v_validation_error := core.validate_identifier_sequence(
      ''location'',
      ''warehouse-a'',
      42,
      tenant_id => v_tenant_id,
      max_duplicates => 100
  );

  IF v_validation_error IS NOT NULL THEN
      RETURN error response;
  END IF;';
```

---

## 🎯 Team C Integration Pattern

### Mutation Function Template (Team C generates this)

```sql
-- Example: Move location in hierarchy
CREATE OR REPLACE FUNCTION tenant.move_location(
    p_location_id UUID,
    p_new_parent_id UUID,
    p_caller_id UUID DEFAULT NULL
) RETURNS mutation_result AS $$
DECLARE
    v_location_pk INTEGER;
    v_new_parent_pk INTEGER;
    v_validation_error core.hierarchy_validation_error;
    v_result mutation_result;
BEGIN
    -- Resolve UUIDs to INTEGER pks
    v_location_pk := tenant.location_pk(p_location_id);
    v_new_parent_pk := tenant.location_pk(p_new_parent_id);

    -- EXPLICIT VALIDATION (Team C generates this call)
    v_validation_error := core.validate_hierarchy_change(
        'location',
        v_location_pk,
        v_new_parent_pk,
        max_depth => 20,  -- From framework config
        check_cycle => true,
        check_depth => true
    );

    -- Handle validation error
    IF v_validation_error IS NOT NULL THEN
        v_result.status := 'error';
        v_result.message := v_validation_error.error_message;
        v_result.object_data := jsonb_build_object(
            '__typename', 'MoveLocationError',
            'code', v_validation_error.error_code,
            'message', v_validation_error.error_message,
            'hint', v_validation_error.hint,
            'detail', v_validation_error.detail
        );
        RETURN v_result;
    END IF;

    -- Validation passed - safe to update
    UPDATE tenant.tb_location
    SET
        fk_parent_location = v_new_parent_pk,
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_location = v_location_pk;

    -- EXPLICIT PATH RECALCULATION (existing pattern)
    PERFORM core.recalculate_tree_path(
        'location',
        ROW(p_location_id, NULL, p_caller_id)::core.recalculation_context
    );

    -- Success response
    v_result.status := 'success';
    v_result.message := 'Location moved successfully';
    v_result.object_data := (
        SELECT jsonb_build_object(
            '__typename', 'Location',
            'id', l.id,
            'path', l.path::text,
            -- ... other fields
        )
        FROM tenant.tb_location l
        WHERE l.pk_location = v_location_pk
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

## 📊 Comparison: Triggers vs Explicit

### Triggers (Current Phase 7 Design)
```sql
-- ❌ IMPLICIT: Validation happens invisibly

UPDATE tenant.tb_location
SET fk_parent_location = 5
WHERE pk_location = 10;
-- Hidden trigger fires, might throw cryptic error:
-- ERROR: Circular reference detected: Location (...) cannot be its own ancestor
-- WHERE did this come from? Hard to debug!
```

### Explicit Validation (Proposed)
```sql
-- ✅ EXPLICIT: Validation visible in mutation code

DECLARE
    v_error core.hierarchy_validation_error;
BEGIN
    -- Step 1: EXPLICIT validation
    v_error := core.validate_hierarchy_change('location', 10, 5);

    -- Step 2: Handle error (visible in code)
    IF v_error IS NOT NULL THEN
        RETURN error_response(v_error);
    END IF;

    -- Step 3: Safe to update
    UPDATE tenant.tb_location
    SET fk_parent_location = 5
    WHERE pk_location = 10;

    -- Step 4: EXPLICIT recalculation
    PERFORM core.recalculate_tree_path('location', ...);
END;
```

**Benefits**:
- ✅ Clear flow: validate → update → recalculate
- ✅ Easy to debug (see exact call site)
- ✅ Can skip validation when safe (migrations, admin ops)
- ✅ Consistent with `recalculate_tree_path()` pattern
- ✅ Testable in isolation

---

## 🔄 Migration from Triggers

### Phase 7 Refactored Deliverables

| Old Trigger Approach | New Explicit Approach |
|---------------------|----------------------|
| `prevent_cycle.sql.jinja2` (trigger) | `validate_hierarchy_change()` (function) |
| `check_sequence_limit.sql.jinja2` (trigger) | `validate_identifier_sequence()` (function) |
| `check_depth_limit.sql.jinja2` (trigger) | `validate_hierarchy_change()` (function) |

**Reduction**: 3 trigger templates → 2 validation functions

### New Team B Phase 7 Tasks

**Day 7: Validation Functions** (instead of triggers)

1. Generate `templates/sql/hierarchy/validate_hierarchy_change.sql.jinja2`
   - Circular reference check
   - Depth limit check
   - Returns error object or NULL

2. Generate `templates/sql/hierarchy/validate_identifier_sequence.sql.jinja2`
   - Sequence limit check
   - Returns error object or NULL

3. Update Team C templates to call validations explicitly

**No triggers generated!**

---

## ✅ Acceptance Criteria

- [ ] `validate_hierarchy_change()` function works for any hierarchical entity
- [ ] `validate_identifier_sequence()` function works for any entity
- [ ] Both return `hierarchy_validation_error` type or NULL
- [ ] Team C mutations call validations explicitly (visible in code)
- [ ] No triggers generated for validation logic
- [ ] Tests cover all validation scenarios
- [ ] Migration guide for existing trigger-based code

---

## 🎯 Decision: Explicit Pattern Everywhere

**Principle**: Mutations should be **explicit and predictable**.

### What Should Be Explicit (Called from Mutations)
✅ Path recalculation: `recalculate_tree_path()`
✅ Hierarchy validation: `validate_hierarchy_change()`
✅ Sequence validation: `validate_identifier_sequence()`
✅ Identifier recalculation: `recalculate_identifier()` (future)

### What Can Stay as Triggers
❌ Nothing for core business logic!
✅ ONLY infrastructure concerns:
   - `updated_at` timestamp updates
   - Event logging (after the fact)
   - Soft delete cascades (if needed)

---

## 📝 Updated Team B Timeline

**Phase 7: Validation Functions (Day 7)** - NOT triggers!

- Generate `validate_hierarchy_change.sql.jinja2`
- Generate `validate_identifier_sequence.sql.jinja2`
- Update Team C templates to call explicitly
- Write comprehensive tests

**No change to overall timeline** (still Day 7), just better architecture!

---

**Status**: 🎯 Ready for Approval
**Impact**: Refactors Phase 7 from trigger-based to explicit validation
**Consistency**: Matches `recalculate_tree_path()` explicit pattern
**Benefits**: Clearer code, easier debugging, better testing

---

## 🤔 Open Question

**Should we also make identifier recalculation explicit?**

Currently identifier is auto-calculated on INSERT (in table definition).
Should we have `recalculate_identifier()` similar to `recalculate_tree_path()`?

**Proposal**: Yes, for consistency!

```sql
-- Example: Explicit identifier calculation
PERFORM core.recalculate_identifier(
    'location',
    ROW(p_location_id, v_tenant_id, p_caller_id)::core.recalculation_context
);
```

This would complete the pattern:
- ✅ Explicit validation
- ✅ Explicit path recalculation
- ✅ Explicit identifier recalculation

All framework operations visible and testable!
