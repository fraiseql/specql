# Implementation Plan: Explicit Validation & Recalculation Pattern

**Status**: 🎯 Detailed Phased Plan
**Timeline**: 7 days (Team B Week 2 - Days 7-13)
**Dependencies**: Phases 1-6 of Team B completed
**Related Docs**:
- `EXPLICIT_VALIDATION_PATTERN.md`
- `EXPLICIT_PATH_RECALCULATION.md`
- `TEAM_B_DATABASE_DECISIONS_PLAN.md`

---

## 📋 Overview

This plan refactors **Phase 7** of Team B from trigger-based to explicit validation, and adds explicit identifier recalculation to complete the pattern.

### What We're Replacing

**OLD (Trigger-Based)**:
- ❌ `prevent_cycle` trigger (hidden validation)
- ❌ `check_sequence_limit` trigger (hidden validation)
- ❌ `check_depth_limit` trigger (hidden validation)
- ❌ Auto-calculated identifiers (no explicit recalculation)

**NEW (Explicit Pattern)**:
- ✅ `validate_hierarchy_change()` - Called explicitly
- ✅ `validate_identifier_sequence()` - Called explicitly
- ✅ `recalculate_identifier()` - Called explicitly (like `recalculate_tree_path()`)
- ✅ All validations and recalculations visible in mutation code

---

## 🎯 Success Criteria

- [ ] Zero triggers for business logic validation
- [ ] All validations called explicitly from mutations
- [ ] Identifier recalculation works like path recalculation
- [ ] Validation functions return structured errors (not exceptions)
- [ ] Team C templates auto-generate explicit calls
- [ ] 90%+ test coverage on all validation logic
- [ ] Performance equivalent or better than triggers
- [ ] Clear migration path from trigger-based code

---

## 📅 Phased Implementation

### **Phase 1: Core Types & Validation Functions** (Days 7-8)

**Objective**: Create foundation types and validation functions

**TDD Cycle 1.1: Validation Error Type**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/schema/test_validation_types.py` (NEW)

```python
"""Test validation error types."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestValidationErrorType:
    """Test core.hierarchy_validation_error composite type."""

    def test_create_validation_error(self, db):
        """Should create validation error with all fields."""
        result = execute_query(db, """
            SELECT ROW(
                'circular_reference',
                'Circular reference detected',
                'Choose a different parent',
                '{"node_pk": 5, "parent_pk": 10}'::jsonb
            )::core.hierarchy_validation_error AS error;
        """)

        assert result['error']['error_code'] == 'circular_reference'
        assert result['error']['error_message'] == 'Circular reference detected'
        assert result['error']['hint'] == 'Choose a different parent'
        assert result['error']['detail']['node_pk'] == 5

    def test_null_validation_error_means_valid(self, db):
        """NULL error should indicate validation passed."""
        result = execute_query(db, """
            SELECT NULL::core.hierarchy_validation_error AS error;
        """)

        assert result['error'] is None
```

**Expected**: ❌ FAIL - Type does not exist

#### 🟢 GREEN: Minimal Implementation

**File**: `templates/sql/000_types.sql.jinja2` (UPDATE)

Add to existing file:

```sql
-- Validation error type for explicit validation functions
CREATE TYPE core.hierarchy_validation_error AS (
    error_code TEXT,
    error_message TEXT,
    hint TEXT,
    detail JSONB
);

COMMENT ON TYPE core.hierarchy_validation_error IS
'Return type for validation functions. NULL indicates validation passed.

Fields:
- error_code: Machine-readable error code (e.g., ''circular_reference'')
- error_message: Human-readable error message
- hint: Suggestion for fixing the error
- detail: Additional context as JSONB

Used by:
- core.validate_hierarchy_change()
- core.validate_identifier_sequence()

Example usage:
  v_error := core.validate_hierarchy_change(...);
  IF v_error IS NOT NULL THEN
    -- Handle error
    RETURN error_response(v_error);
  END IF;';
```

**Expected**: ✅ PASS

#### 🔧 REFACTOR: Add Type Helper Function

```sql
-- Helper to convert validation error to JSONB
CREATE OR REPLACE FUNCTION core.validation_error_to_jsonb(
    error core.hierarchy_validation_error
) RETURNS JSONB AS $$
BEGIN
    IF error IS NULL THEN
        RETURN NULL;
    END IF;

    RETURN jsonb_build_object(
        'code', error.error_code,
        'message', error.error_message,
        'hint', error.hint,
        'detail', error.detail
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

#### ✅ QA: Run Full Test Suite

```bash
uv run pytest tests/unit/schema/test_validation_types.py -v
uv run pytest --tb=short  # Ensure no regressions
```

---

**TDD Cycle 1.2: Hierarchy Validation Function**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/schema/test_validate_hierarchy.py` (NEW)

```python
"""Test core.validate_hierarchy_change() function."""

import pytest
from tests.utils.db_test import execute_sql, execute_query, setup_hierarchy


class TestValidateHierarchyChange:
    """Test hierarchy validation function."""

    @pytest.fixture
    def sample_hierarchy(self, db):
        """Create sample hierarchy for testing.

        Structure:
            1 (root)
            ├── 2
            │   └── 3
            └── 4
        """
        execute_sql(db, """
            CREATE SCHEMA IF NOT EXISTS test_schema;

            CREATE TABLE test_schema.tb_location (
                pk_location INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                path ltree NOT NULL,
                fk_parent_location INTEGER REFERENCES test_schema.tb_location(pk_location)
            );

            INSERT INTO test_schema.tb_location (pk_location, path, fk_parent_location) VALUES
                (1, '1', NULL),
                (2, '1.2', 1),
                (3, '1.2.3', 2),
                (4, '1.4', 1);
        """)
        yield
        execute_sql(db, "DROP SCHEMA test_schema CASCADE;")

    def test_valid_parent_change(self, db, sample_hierarchy):
        """Should return NULL for valid parent change."""
        # Move node 3 from under 2 to under 4 (valid)
        result = execute_query(db, """
            SELECT core.validate_hierarchy_change(
                'location',
                3,      -- node_pk
                4,      -- new_parent_pk
                20,     -- max_depth
                true,   -- check_cycle
                true    -- check_depth
            ) AS error;
        """)

        assert result['error'] is None

    def test_circular_reference_detected(self, db, sample_hierarchy):
        """Should detect circular reference (parent is descendant)."""
        # Try to move node 2 under its child node 3 (circular!)
        result = execute_query(db, """
            SELECT core.validate_hierarchy_change(
                'location',
                2,      -- node_pk (parent of 3)
                3,      -- new_parent_pk (child of 2) - CIRCULAR!
                20,
                true,
                true
            ) AS error;
        """)

        error = result['error']
        assert error is not None
        assert error['error_code'] == 'circular_reference'
        assert 'descendant' in error['error_message'].lower()
        assert error['detail']['node_pk'] == 2
        assert error['detail']['parent_pk'] == 3

    def test_depth_limit_exceeded(self, db, sample_hierarchy):
        """Should detect depth limit violation."""
        # Create deep hierarchy (19 levels)
        execute_sql(db, """
            INSERT INTO test_schema.tb_location (pk_location, path, fk_parent_location)
            SELECT
                i,
                ('1.' || array_to_string(array_agg(j ORDER BY j), '.'))::ltree,
                i - 1
            FROM generate_series(5, 19) i
            CROSS JOIN LATERAL generate_series(2, i) j
            GROUP BY i;
        """)

        # Try to add one more level (would be 21, exceeds max 20)
        result = execute_query(db, """
            SELECT core.validate_hierarchy_change(
                'location',
                99,     -- new node
                19,     -- parent at depth 19
                20,     -- max_depth
                false,  -- skip cycle check
                true    -- check depth
            ) AS error;
        """)

        error = result['error']
        assert error is not None
        assert error['error_code'] == 'depth_limit_exceeded'
        assert error['detail']['new_depth'] == 20
        assert error['detail']['max_depth'] == 20

    def test_node_not_found(self, db, sample_hierarchy):
        """Should return error if node doesn't exist."""
        result = execute_query(db, """
            SELECT core.validate_hierarchy_change(
                'location',
                999,    -- non-existent node
                1,
                20,
                true,
                true
            ) AS error;
        """)

        error = result['error']
        assert error is not None
        assert error['error_code'] == 'node_not_found'
        assert '999' in error['error_message']

    def test_skip_cycle_check_for_performance(self, db, sample_hierarchy):
        """Should skip cycle check if check_cycle=false."""
        # This would be circular, but we skip the check
        result = execute_query(db, """
            SELECT core.validate_hierarchy_change(
                'location',
                2,
                3,
                20,
                false,  -- SKIP cycle check
                false   -- SKIP depth check
            ) AS error;
        """)

        # Should pass because checks are skipped
        assert result['error'] is None
```

**Expected**: ❌ FAIL - Function does not exist

#### 🟢 GREEN: Minimal Implementation

**File**: `templates/sql/hierarchy/validate_hierarchy_change.sql.jinja2` (NEW)

```sql
-- Validate hierarchy changes BEFORE they happen
-- Returns NULL if valid, error object if invalid
-- NO TRIGGERS - Called explicitly from mutations!

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

    -- Find schema dynamically (search expected schemas)
    SELECT table_schema INTO v_schema
    FROM information_schema.tables
    WHERE table_name = v_table
      AND table_schema IN ('core', 'management', 'catalog', 'tenant', 'test_schema')
    LIMIT 1;

    IF v_schema IS NULL THEN
        v_error.error_code := 'table_not_found';
        v_error.error_message := format('Table "tb_%s" not found in any expected schema', entity);
        v_error.hint := 'Verify entity name is correct';
        RETURN v_error;
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
        v_error.detail := jsonb_build_object('node_pk', node_pk);
        RETURN v_error;
    END IF;

    -- If making root node, no further validation needed
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
        v_error.detail := jsonb_build_object('parent_pk', new_parent_pk);
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
        RETURN error_response(v_validation_error);
    END IF;

    -- Safe to proceed with UPDATE
  END;

Based on explicit pattern from recalculate_tree_path().';
```

**Expected**: ✅ PASS

#### 🔧 REFACTOR: Add Performance Optimization

```sql
-- Add index hint comments for query planner
-- (Already covered by existing indexes on path column)

-- Consider adding cached depth column if depth checks become bottleneck
-- (Future optimization if needed)
```

#### ✅ QA: Run Full Test Suite

```bash
uv run pytest tests/unit/schema/test_validate_hierarchy.py -v
uv run pytest tests/unit/schema/ -v
uv run pytest --tb=short
```

---

**TDD Cycle 1.3: Identifier Sequence Validation**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/schema/test_validate_identifier_sequence.py` (NEW)

```python
"""Test core.validate_identifier_sequence() function."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestValidateIdentifierSequence:
    """Test identifier sequence validation function."""

    @pytest.fixture
    def sample_table(self, db):
        """Create sample table with identifiers."""
        execute_sql(db, """
            CREATE SCHEMA IF NOT EXISTS test_schema;

            CREATE TABLE test_schema.tb_product (
                pk_product INTEGER PRIMARY KEY,
                tenant_id UUID,
                identifier TEXT NOT NULL,
                sequence_number INTEGER NOT NULL DEFAULT 1,
                UNIQUE (tenant_id, identifier, sequence_number)
            );

            -- Create 50 variants of 'widget'
            INSERT INTO test_schema.tb_product (pk_product, tenant_id, identifier, sequence_number)
            SELECT
                i,
                'tenant-123'::uuid,
                'widget',
                i
            FROM generate_series(1, 50) i;
        """)
        yield
        execute_sql(db, "DROP SCHEMA test_schema CASCADE;")

    def test_valid_sequence_number(self, db, sample_table):
        """Should return NULL for valid sequence number."""
        result = execute_query(db, """
            SELECT core.validate_identifier_sequence(
                'product',
                'widget',
                51,
                'tenant-123'::uuid,
                100  -- max_duplicates
            ) AS error;
        """)

        assert result['error'] is None

    def test_sequence_limit_exceeded(self, db, sample_table):
        """Should return error when sequence exceeds limit."""
        result = execute_query(db, """
            SELECT core.validate_identifier_sequence(
                'product',
                'widget',
                101,     -- exceeds max 100
                'tenant-123'::uuid,
                100
            ) AS error;
        """)

        error = result['error']
        assert error is not None
        assert error['error_code'] == 'sequence_limit_exceeded'
        assert 'widget' in error['error_message']
        assert error['detail']['sequence_number'] == 101
        assert error['detail']['max_duplicates'] == 100

    def test_warning_at_50_percent(self, db, sample_table, caplog):
        """Should raise warning at 50% of limit."""
        # 51 is > 50% of 100
        result = execute_query(db, """
            SELECT core.validate_identifier_sequence(
                'product',
                'widget',
                51,
                'tenant-123'::uuid,
                100
            ) AS error;
        """)

        # Should still be valid
        assert result['error'] is None

        # But should have raised warning
        # (Check PostgreSQL logs or use pg_stat_statements)

    def test_global_scope_no_tenant(self, db, sample_table):
        """Should work without tenant_id for global entities."""
        execute_sql(db, """
            CREATE TABLE test_schema.tb_global (
                pk_global INTEGER PRIMARY KEY,
                identifier TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                UNIQUE (identifier, sequence_number)
            );

            INSERT INTO test_schema.tb_global (pk_global, identifier, sequence_number)
            SELECT i, 'item', i FROM generate_series(1, 60) i;
        """)

        result = execute_query(db, """
            SELECT core.validate_identifier_sequence(
                'global',
                'item',
                61,
                NULL,  -- No tenant
                100
            ) AS error;
        """)

        assert result['error'] is None
```

**Expected**: ❌ FAIL - Function does not exist

#### 🟢 GREEN: Minimal Implementation

**File**: `templates/sql/hierarchy/validate_identifier_sequence.sql.jinja2` (NEW)

```sql
-- Validate identifier sequence BEFORE insert/update
-- Returns NULL if valid, error object if limit exceeded

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
      AND table_schema IN ('core', 'management', 'catalog', 'tenant', 'test_schema')
    LIMIT 1;

    IF v_schema IS NULL THEN
        v_error.error_code := 'table_not_found';
        v_error.error_message := format('Table "tb_%s" not found', entity);
        RETURN v_error;
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

**Expected**: ✅ PASS

#### ✅ QA: Phase 1 Complete

```bash
uv run pytest tests/unit/schema/test_validate*.py -v
uv run pytest tests/unit/schema/ -v
uv run pytest --tb=short
make lint && make typecheck
```

**Deliverables**:
- ✅ `core.hierarchy_validation_error` type
- ✅ `core.validate_hierarchy_change()` function
- ✅ `core.validate_identifier_sequence()` function
- ✅ Comprehensive test coverage

---

### **Phase 2: Identifier Recalculation Function** (Days 9-10)

**Objective**: Implement explicit identifier recalculation (like `recalculate_tree_path`)

**TDD Cycle 2.1: Recalculation Context Extension**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/schema/test_recalculate_identifier.py` (NEW)

```python
"""Test core.recalculate_identifier() function."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestRecalculateIdentifier:
    """Test identifier recalculation function."""

    @pytest.fixture
    def sample_hierarchy(self, db):
        """Create hierarchy with identifiers needing recalculation."""
        execute_sql(db, """
            CREATE SCHEMA IF NOT EXISTS test_schema;

            CREATE TABLE test_schema.tb_location (
                pk_location INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                path ltree NOT NULL,
                fk_parent_location INTEGER REFERENCES test_schema.tb_location(pk_location),
                name TEXT NOT NULL,
                identifier TEXT NOT NULL,
                sequence_number INTEGER NOT NULL DEFAULT 1,
                display_identifier TEXT,
                identifier_recalculated_at TIMESTAMPTZ,
                identifier_recalculated_by UUID
            );

            -- Initial hierarchy (identifiers need recalculation)
            INSERT INTO test_schema.tb_location
                (pk_location, id, tenant_id, path, fk_parent_location, name, identifier, sequence_number)
            VALUES
                (1, gen_random_uuid(), 'tenant-1'::uuid, '1', NULL, 'Building A', 'old-id-1', 1),
                (2, gen_random_uuid(), 'tenant-1'::uuid, '1.2', 1, 'Floor 1', 'old-id-2', 1),
                (3, gen_random_uuid(), 'tenant-1'::uuid, '1.2.3', 2, 'Room 101', 'old-id-3', 1),
                (4, gen_random_uuid(), 'tenant-1'::uuid, '1.4', 1, 'Floor 2', 'old-id-4', 1);
        """)
        yield
        execute_sql(db, "DROP SCHEMA test_schema CASCADE;")

    def test_recalculate_single_node(self, db, sample_hierarchy):
        """Should recalculate identifier for single node."""
        # Get node id
        node_id = execute_query(db, "SELECT id FROM test_schema.tb_location WHERE pk_location = 2")['id']
        caller_id = 'user-123'

        # Recalculate
        result = execute_query(db, """
            SELECT core.recalculate_identifier(
                'location',
                ROW($1, NULL, $2)::core.recalculation_context
            ) AS updated_count;
        """, node_id, caller_id)

        assert result['updated_count'] == 1

        # Check identifier was updated
        updated = execute_query(db, """
            SELECT
                identifier,
                display_identifier,
                identifier_recalculated_by
            FROM test_schema.tb_location
            WHERE pk_location = 2;
        """)

        assert updated['identifier'] == 'building-a_floor-1'  # parent_name
        assert updated['display_identifier'] == 'building-a_floor-1'
        assert updated['identifier_recalculated_by'] == caller_id

    def test_recalculate_subtree(self, db, sample_hierarchy):
        """Should recalculate identifiers for entire subtree."""
        node_id = execute_query(db, "SELECT id FROM test_schema.tb_location WHERE pk_location = 1")['id']
        caller_id = 'user-123'

        # Recalculate from root
        result = execute_query(db, """
            SELECT core.recalculate_identifier(
                'location',
                ROW($1, NULL, $2)::core.recalculation_context
            ) AS updated_count;
        """, node_id, caller_id)

        # Should update all 4 nodes
        assert result['updated_count'] == 4

        # Verify hierarchy of identifiers
        identifiers = execute_query(db, """
            SELECT pk_location, identifier
            FROM test_schema.tb_location
            ORDER BY pk_location;
        """, fetch_all=True)

        assert identifiers[0]['identifier'] == 'building-a'  # Root
        assert identifiers[1]['identifier'] == 'building-a_floor-1'
        assert identifiers[2]['identifier'] == 'building-a_floor-1_room-101'
        assert identifiers[3]['identifier'] == 'building-a_floor-2'

    def test_recalculate_tenant_scope(self, db, sample_hierarchy):
        """Should recalculate all identifiers in tenant."""
        # Add second tenant
        execute_sql(db, """
            INSERT INTO test_schema.tb_location
                (pk_location, id, tenant_id, path, fk_parent_location, name, identifier, sequence_number)
            VALUES
                (5, gen_random_uuid(), 'tenant-2'::uuid, '5', NULL, 'Warehouse', 'old-id-5', 1);
        """)

        tenant_id = 'tenant-1'
        caller_id = 'user-123'

        # Recalculate tenant scope
        result = execute_query(db, """
            SELECT core.recalculate_identifier(
                'location',
                ROW(NULL, $1, $2)::core.recalculation_context
            ) AS updated_count;
        """, tenant_id, caller_id)

        # Should update only tenant-1 nodes (4 nodes)
        assert result['updated_count'] == 4

        # Verify tenant-2 unchanged
        tenant2 = execute_query(db, """
            SELECT identifier
            FROM test_schema.tb_location
            WHERE tenant_id = 'tenant-2'::uuid;
        """)
        assert tenant2['identifier'] == 'old-id-5'  # Unchanged

    def test_idempotent_recalculation(self, db, sample_hierarchy):
        """Recalculating again should be idempotent (no changes)."""
        node_id = execute_query(db, "SELECT id FROM test_schema.tb_location WHERE pk_location = 1")['id']
        caller_id = 'user-123'

        # First recalculation
        result1 = execute_query(db, """
            SELECT core.recalculate_identifier('location', ROW($1, NULL, $2)::core.recalculation_context);
        """, node_id, caller_id)

        # Second recalculation (identifiers already correct)
        result2 = execute_query(db, """
            SELECT core.recalculate_identifier('location', ROW($1, NULL, $2)::core.recalculation_context);
        """, node_id, caller_id)

        # Should update 0 rows (idempotent)
        assert result2 == 0
```

**Expected**: ❌ FAIL - Function does not exist

#### 🟢 GREEN: Minimal Implementation

**File**: `templates/sql/hierarchy/recalculate_identifier.sql.jinja2` (NEW)

```sql
-- Generic identifier recalculation for ANY entity
-- Pattern: Concatenate parent identifier + safe_slug(name)
-- NO TRIGGERS - Called explicitly from mutations!

CREATE OR REPLACE FUNCTION core.recalculate_identifier(
    entity TEXT,
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
) RETURNS INTEGER AS $$
DECLARE
    v_schema TEXT;
    v_table TEXT;
    v_pk_column TEXT;
    v_parent_column TEXT;
    v_updated_count INTEGER := 0;
    v_root_pk INTEGER;
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
      AND table_schema IN ('core', 'management', 'catalog', 'tenant', 'test_schema')
    LIMIT 1;

    IF v_schema IS NULL THEN
        RAISE EXCEPTION 'Table "tb_%" not found in any expected schema', entity;
    END IF;

    -- MODE 1: Subtree recalculation (ctx.pk set)
    IF ctx.pk IS NOT NULL THEN
        -- Find root of subtree
        dyn_sql := format($q$
            WITH RECURSIVE t_chain AS (
                SELECT %1$I AS pk, %2$I AS parent
                FROM %3$I.%4$I
                WHERE id = $1

                UNION ALL

                SELECT t.%1$I, t.%2$I
                FROM %3$I.%4$I t
                JOIN t_chain ON t.%1$I = t_chain.parent
            )
            SELECT pk FROM t_chain WHERE parent IS NULL LIMIT 1;
        $q$, v_pk_column, v_parent_column, v_schema, v_table);

        EXECUTE dyn_sql INTO v_root_pk USING ctx.pk;

        IF v_root_pk IS NULL THEN
            -- Given node IS the root
            dyn_sql := format($q$
                SELECT %1$I FROM %2$I.%3$I WHERE id = $1;
            $q$, v_pk_column, v_schema, v_table);
            EXECUTE dyn_sql INTO v_root_pk USING ctx.pk;
        END IF;

        -- Recalculate subtree identifiers
        dyn_sql := format($q$
            WITH RECURSIVE hierarchy AS (
                -- Root: identifier = safe_slug(name)
                SELECT
                    t.%1$I AS pk,
                    public.safe_slug(t.name) AS new_identifier
                FROM %2$I.%3$I t
                WHERE t.%1$I = $1

                UNION ALL

                -- Children: parent_identifier + '_' + safe_slug(name)
                SELECT
                    c.%1$I,
                    h.new_identifier || '_' || public.safe_slug(c.name)
                FROM %2$I.%3$I c
                JOIN hierarchy h ON c.%4$I = h.pk
            ),
            updated AS (
                UPDATE %2$I.%3$I t
                SET
                    identifier = h.new_identifier,
                    display_identifier = h.new_identifier,  -- Assuming sequence_number = 1
                    identifier_recalculated_at = now(),
                    identifier_recalculated_by = $2
                FROM hierarchy h
                WHERE t.%1$I = h.pk
                  AND t.identifier IS DISTINCT FROM h.new_identifier  -- Idempotent
                RETURNING t.%1$I
            )
            SELECT COUNT(*) FROM updated;
        $q$, v_pk_column, v_schema, v_table, v_parent_column);

        EXECUTE dyn_sql INTO v_updated_count USING v_root_pk, ctx.updated_by;

    -- MODE 2: Tenant-scoped recalculation
    ELSIF ctx.pk_tenant IS NOT NULL THEN
        dyn_sql := format($q$
            WITH RECURSIVE hierarchy AS (
                -- Roots in tenant
                SELECT
                    t.%1$I AS pk,
                    public.safe_slug(t.name) AS new_identifier
                FROM %2$I.%3$I t
                WHERE t.tenant_id = $1 AND t.%4$I IS NULL

                UNION ALL

                -- Children
                SELECT
                    c.%1$I,
                    h.new_identifier || '_' || public.safe_slug(c.name)
                FROM %2$I.%3$I c
                JOIN hierarchy h ON c.%4$I = h.pk
            ),
            updated AS (
                UPDATE %2$I.%3$I t
                SET
                    identifier = h.new_identifier,
                    display_identifier = h.new_identifier,
                    identifier_recalculated_at = now(),
                    identifier_recalculated_by = $2
                FROM hierarchy h
                WHERE t.%1$I = h.pk
                  AND t.identifier IS DISTINCT FROM h.new_identifier
                RETURNING t.%1$I
            )
            SELECT COUNT(*) FROM updated;
        $q$, v_pk_column, v_schema, v_table, v_parent_column);

        EXECUTE dyn_sql INTO v_updated_count USING ctx.pk_tenant, ctx.updated_by;

    -- MODE 3: Global recalculation
    ELSE
        dyn_sql := format($q$
            WITH RECURSIVE hierarchy AS (
                -- All roots
                SELECT
                    t.%1$I AS pk,
                    public.safe_slug(t.name) AS new_identifier
                FROM %2$I.%3$I t
                WHERE t.%4$I IS NULL

                UNION ALL

                -- All children
                SELECT
                    c.%1$I,
                    h.new_identifier || '_' || public.safe_slug(c.name)
                FROM %2$I.%3$I c
                JOIN hierarchy h ON c.%4$I = h.pk
            ),
            updated AS (
                UPDATE %2$I.%3$I t
                SET
                    identifier = h.new_identifier,
                    display_identifier = h.new_identifier,
                    identifier_recalculated_at = now(),
                    identifier_recalculated_by = $1
                FROM hierarchy h
                WHERE t.%1$I = h.pk
                  AND t.identifier IS DISTINCT FROM h.new_identifier
                RETURNING t.%1$I
            )
            SELECT COUNT(*) FROM updated;
        $q$, v_pk_column, v_schema, v_table, v_parent_column);

        EXECUTE dyn_sql INTO v_updated_count USING ctx.updated_by;
    END IF;

    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION core.recalculate_identifier IS
'Generic identifier recalculation for any entity using hierarchical naming.

Explicit over Implicit: NO TRIGGERS! Mutations call this explicitly.

Pattern: parent_identifier + ''_'' + safe_slug(name)
Example: ''building-a_floor-1_room-101''

Three modes:
1. Subtree (ctx.pk set): Recalculate from given node down
2. Tenant (ctx.pk_tenant set, ctx.pk NULL): Recalculate all trees in tenant
3. Global (both NULL): Recalculate entire entity

Returns: Number of rows updated

Example usage in mutations:
  v_count := core.recalculate_identifier(
      ''location'',
      ROW(v_location_id, NULL, p_caller_id)::core.recalculation_context
  );

Based on explicit pattern from recalculate_tree_path().';
```

**Expected**: ✅ PASS

#### 🔧 REFACTOR: Handle Deduplication (sequence_number)

Update function to handle sequence numbers:

```sql
-- Enhanced version that respects sequence_number
-- Update display_identifier calculation:
display_identifier = CASE
    WHEN t.sequence_number > 1
    THEN h.new_identifier || '#' || t.sequence_number
    ELSE h.new_identifier
END
```

#### ✅ QA: Phase 2 Complete

```bash
uv run pytest tests/unit/schema/test_recalculate_identifier.py -v
uv run pytest tests/unit/schema/ -v
uv run pytest --tb=short
```

**Deliverables**:
- ✅ `core.recalculate_identifier()` function
- ✅ Works with existing `recalculation_context` type
- ✅ Supports subtree/tenant/global modes
- ✅ Idempotent (no changes if already correct)

---

### **Phase 3: Team B Template Integration** (Day 11)

**Objective**: Update Team B generators to use explicit pattern

**TDD Cycle 3.1: Schema Generator Integration**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/schema/test_schema_generator_explicit_pattern.py` (NEW)

```python
"""Test SchemaGenerator produces explicit validation pattern."""

import pytest
from src.core.ast_models import EntityAST, FieldDefinition
from src.generators.schema.schema_generator import SchemaGenerator


class TestSchemaGeneratorExplicitPattern:
    """Test schema generator uses explicit pattern (no triggers)."""

    def test_no_validation_triggers_generated(self):
        """Should NOT generate validation triggers."""
        entity = EntityAST(
            name='Location',
            schema='tenant',
            hierarchical=True,
            fields=[
                FieldDefinition(name='name', type='text', required=True)
            ]
        )

        generator = SchemaGenerator()
        sql = generator.generate(entity)

        # Should NOT contain trigger definitions
        assert 'CREATE TRIGGER' not in sql
        assert 'prevent_cycle' not in sql
        assert 'check_sequence_limit' not in sql
        assert 'check_depth_limit' not in sql

    def test_includes_validation_function_references(self):
        """Should reference core validation functions in comments."""
        entity = EntityAST(
            name='Location',
            schema='tenant',
            hierarchical=True,
            fields=[
                FieldDefinition(name='name', type='text', required=True)
            ]
        )

        generator = SchemaGenerator()
        sql = generator.generate(entity)

        # Should mention validation functions in comments
        assert 'validate_hierarchy_change' in sql
        assert 'recalculate_tree_path' in sql
        assert 'recalculate_identifier' in sql

    def test_generates_audit_fields(self):
        """Should generate audit fields for recalculation tracking."""
        entity = EntityAST(
            name='Location',
            schema='tenant',
            hierarchical=True,
            fields=[]
        )

        generator = SchemaGenerator()
        sql = generator.generate(entity)

        # Should include recalculation audit fields
        assert 'path_updated_at' in sql
        assert 'path_updated_by' in sql
        assert 'identifier_recalculated_at' in sql
        assert 'identifier_recalculated_by' in sql
```

**Expected**: ❌ FAIL - Generator still produces triggers

#### 🟢 GREEN: Update SchemaGenerator

**File**: `src/generators/schema/schema_generator.py` (UPDATE)

```python
class SchemaGenerator:
    def generate(self, entity: EntityAST) -> str:
        """Generate schema DDL with explicit validation pattern."""

        parts = []

        # Generate table
        parts.append(self._generate_table(entity))

        # Generate indexes
        parts.append(self._generate_indexes(entity))

        # Generate helper functions (pk/id/identifier lookup)
        parts.append(self._generate_helper_functions(entity))

        # ❌ REMOVED: Don't generate validation triggers
        # parts.append(self._generate_validation_triggers(entity))

        # ✅ NEW: Add comment about explicit validation
        if entity.hierarchical:
            parts.append(self._generate_validation_comment(entity))

        return '\n\n'.join(parts)

    def _generate_validation_comment(self, entity: EntityAST) -> str:
        """Generate comment explaining explicit validation pattern."""
        entity_lower = entity.name.lower()
        schema = entity.schema

        return f"""
-- ════════════════════════════════════════════════════════════════
-- VALIDATION PATTERN: Explicit over Implicit (NO TRIGGERS!)
-- ════════════════════════════════════════════════════════════════
--
-- This entity uses EXPLICIT validation instead of database triggers.
-- Mutations call validation functions directly (visible in code).
--
-- Available validation functions:
--   • core.validate_hierarchy_change('{entity_lower}', node_pk, new_parent_pk)
--   • core.validate_identifier_sequence('{entity_lower}', identifier, seq_num)
--
-- Available recalculation functions:
--   • core.recalculate_tree_path('{entity_lower}', context)
--   • core.recalculate_identifier('{entity_lower}', context)
--
-- Example mutation usage:
--   v_error := core.validate_hierarchy_change('{entity_lower}', ...);
--   IF v_error IS NOT NULL THEN RETURN error_response(v_error); END IF;
--
--   UPDATE {schema}.tb_{entity_lower} SET fk_parent_{entity_lower} = ...;
--
--   PERFORM core.recalculate_tree_path('{entity_lower}', ...);
--   PERFORM core.recalculate_identifier('{entity_lower}', ...);
--
-- Benefits: Visible, debuggable, testable, controllable
-- ════════════════════════════════════════════════════════════════
""".strip()
```

**Expected**: ✅ PASS

#### ✅ QA: Phase 3 Complete

```bash
uv run pytest tests/unit/schema/test_schema_generator*.py -v
make teamB-test
```

**Deliverables**:
- ✅ No triggers generated
- ✅ Clear comments about explicit pattern
- ✅ All Team B tests pass

---

### **Phase 4: Team C Mutation Templates** (Days 12-13)

**Objective**: Update mutation templates to call validations explicitly

**TDD Cycle 4.1: Mutation Template with Validation**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/actions/test_action_compiler_explicit_validation.py` (NEW)

```python
"""Test ActionCompiler generates explicit validation calls."""

import pytest
from src.core.ast_models import EntityAST, ActionDefinition, ActionStep
from src.generators.actions.action_compiler import ActionCompiler


class TestActionCompilerExplicitValidation:
    """Test action compiler generates explicit validation calls."""

    def test_generates_hierarchy_validation_for_parent_change(self):
        """Should generate validate_hierarchy_change() call."""
        entity = EntityAST(
            name='Location',
            schema='tenant',
            hierarchical=True,
            fields=[]
        )

        action = ActionDefinition(
            name='move_location',
            parameters=['new_parent_id'],
            steps=[
                ActionStep(
                    type='update',
                    target='Location',
                    set_clause='fk_parent_location = $new_parent_id'
                )
            ]
        )

        compiler = ActionCompiler()
        sql = compiler.compile(action, entity)

        # Should include validation call
        assert 'core.validate_hierarchy_change' in sql
        assert 'v_validation_error' in sql
        assert 'IF v_validation_error IS NOT NULL THEN' in sql

        # Should return error response on validation failure
        assert 'RETURN' in sql
        assert 'error_response' in sql or 'error' in sql.lower()

    def test_generates_path_recalculation_call(self):
        """Should generate recalculate_tree_path() call after parent change."""
        entity = EntityAST(
            name='Location',
            schema='tenant',
            hierarchical=True,
            fields=[]
        )

        action = ActionDefinition(
            name='move_location',
            parameters=['new_parent_id'],
            steps=[
                ActionStep(
                    type='update',
                    target='Location',
                    set_clause='fk_parent_location = $new_parent_id'
                )
            ]
        )

        compiler = ActionCompiler()
        sql = compiler.compile(action, entity)

        # Should include path recalculation
        assert 'core.recalculate_tree_path' in sql
        assert 'location' in sql  # entity name parameter
        assert 'recalculation_context' in sql

    def test_generates_identifier_recalculation_on_rename(self):
        """Should generate recalculate_identifier() on name change."""
        entity = EntityAST(
            name='Location',
            schema='tenant',
            hierarchical=True,
            fields=[]
        )

        action = ActionDefinition(
            name='rename_location',
            parameters=['new_name'],
            steps=[
                ActionStep(
                    type='update',
                    target='Location',
                    set_clause='name = $new_name'
                )
            ]
        )

        compiler = ActionCompiler()
        sql = compiler.compile(action, entity)

        # Should include identifier recalculation
        assert 'core.recalculate_identifier' in sql

    def test_validation_order_correct(self):
        """Validation should happen BEFORE update."""
        entity = EntityAST(
            name='Location',
            schema='tenant',
            hierarchical=True,
            fields=[]
        )

        action = ActionDefinition(
            name='move_location',
            parameters=['new_parent_id'],
            steps=[
                ActionStep(
                    type='update',
                    target='Location',
                    set_clause='fk_parent_location = $new_parent_id'
                )
            ]
        )

        compiler = ActionCompiler()
        sql = compiler.compile(action, entity)

        # Validation should come before UPDATE
        validation_pos = sql.find('validate_hierarchy_change')
        update_pos = sql.find('UPDATE')

        assert validation_pos > 0
        assert update_pos > 0
        assert validation_pos < update_pos  # Validation first!
```

**Expected**: ❌ FAIL - Compiler doesn't generate validation calls

#### 🟢 GREEN: Update ActionCompiler

**File**: `src/generators/actions/action_compiler.py` (UPDATE)

```python
class ActionCompiler:
    def _compile_update_step(
        self,
        step: ActionStep,
        entity: EntityAST,
        context: CompilerContext
    ) -> str:
        """Compile UPDATE step with explicit validation."""

        parts = []

        # Detect if this is a parent field change (hierarchical)
        if entity.hierarchical and self._is_parent_change(step):
            parts.append(self._generate_hierarchy_validation(entity, step))

        # Detect if this is a name change (affects identifier)
        if self._is_name_change(step):
            # Identifier validation happens in recalculation
            pass

        # Generate the actual UPDATE
        parts.append(self._generate_update_sql(step, entity, context))

        # Post-update recalculations
        if entity.hierarchical and self._is_parent_change(step):
            parts.append(self._generate_path_recalculation(entity, context))

        if self._is_name_change(step):
            parts.append(self._generate_identifier_recalculation(entity, context))

        return '\n\n'.join(parts)

    def _generate_hierarchy_validation(
        self,
        entity: EntityAST,
        step: ActionStep
    ) -> str:
        """Generate validation call for hierarchy changes."""
        entity_lower = entity.name.lower()

        return f"""
    -- Validate hierarchy change (explicit!)
    v_validation_error := core.validate_hierarchy_change(
        '{entity_lower}',
        v_{entity_lower}_pk,
        v_new_parent_pk,
        max_depth => 20,  -- Framework config
        check_cycle => true,
        check_depth => true
    );

    IF v_validation_error IS NOT NULL THEN
        -- Return structured error
        v_result.status := 'error';
        v_result.message := v_validation_error.error_message;
        v_result.object_data := core.validation_error_to_jsonb(v_validation_error);
        RETURN v_result;
    END IF;
""".strip()

    def _generate_path_recalculation(
        self,
        entity: EntityAST,
        context: CompilerContext
    ) -> str:
        """Generate path recalculation call."""
        entity_lower = entity.name.lower()

        return f"""
    -- Recalculate paths (explicit!)
    v_paths_updated := core.recalculate_tree_path(
        '{entity_lower}',
        ROW(p_{entity_lower}_id, NULL, p_caller_id)::core.recalculation_context
    );

    -- Track in response metadata
    v_result.extra_metadata := jsonb_build_object(
        'pathsUpdated', v_paths_updated
    );
""".strip()

    def _generate_identifier_recalculation(
        self,
        entity: EntityAST,
        context: CompilerContext
    ) -> str:
        """Generate identifier recalculation call."""
        entity_lower = entity.name.lower()

        return f"""
    -- Recalculate identifiers (explicit!)
    v_identifiers_updated := core.recalculate_identifier(
        '{entity_lower}',
        ROW(p_{entity_lower}_id, NULL, p_caller_id)::core.recalculation_context
    );

    -- Add to response metadata
    v_result.extra_metadata := jsonb_set(
        COALESCE(v_result.extra_metadata, '{{}}'::jsonb),
        '{{identifiersUpdated}}',
        to_jsonb(v_identifiers_updated)
    );
""".strip()

    def _is_parent_change(self, step: ActionStep) -> bool:
        """Check if step modifies parent field."""
        return 'fk_parent' in step.set_clause.lower()

    def _is_name_change(self, step: ActionStep) -> bool:
        """Check if step modifies name field."""
        return step.set_clause.lower().strip().startswith('name =')
```

**Expected**: ✅ PASS

#### ✅ QA: Phase 4 Complete

```bash
uv run pytest tests/unit/actions/test_action_compiler*.py -v
make teamC-test
```

**Deliverables**:
- ✅ Mutations call validations explicitly
- ✅ Validations happen BEFORE updates
- ✅ Recalculations happen AFTER updates
- ✅ Structured error responses

---

### **Phase 5: Integration Testing** (Day 14)

**Objective**: End-to-end testing of explicit pattern

**TDD Cycle 5.1: Integration Test**

#### 🔴 RED: Write Failing Integration Test

**File**: `tests/integration/test_explicit_validation_e2e.py` (NEW)

```python
"""End-to-end test of explicit validation pattern."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestExplicitValidationE2E:
    """Test complete flow: SpecQL → SQL → Validation → Recalculation."""

    @pytest.fixture
    def generated_location_schema(self, db):
        """Generate Location entity using Team B + C."""
        from src.core.specql_parser import SpecQLParser
        from src.generators.schema.schema_generator import SchemaGenerator
        from src.generators.actions.action_compiler import ActionCompiler

        # Parse SpecQL
        yaml_content = """
entity: Location
schema: tenant
hierarchical: true

fields:
  name: text

actions:
  - name: move_location
    parameters:
      - new_parent_id: uuid
    steps:
      - update: Location SET fk_parent_location = $new_parent_id
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        # Generate schema (Team B)
        schema_gen = SchemaGenerator()
        schema_sql = schema_gen.generate(entity)

        # Generate actions (Team C)
        action_compiler = ActionCompiler()
        action_sql = action_compiler.compile(entity.actions[0], entity)

        # Execute generated SQL
        execute_sql(db, schema_sql)
        execute_sql(db, action_sql)

        yield

        execute_sql(db, "DROP SCHEMA tenant CASCADE;")

    def test_move_location_validates_and_recalculates(self, db, generated_location_schema):
        """Full flow: move location with validation and recalculation."""
        # Create hierarchy
        root_id = execute_query(db, """
            INSERT INTO tenant.tb_location (path, fk_parent_location, name, identifier)
            VALUES ('1', NULL, 'Building A', 'building-a')
            RETURNING id;
        """)['id']

        child_id = execute_query(db, """
            INSERT INTO tenant.tb_location (path, fk_parent_location, name, identifier)
            VALUES ('1.2', (SELECT pk_location FROM tenant.tb_location WHERE id = $1), 'Floor 1', 'building-a_floor-1')
            RETURNING id;
        """, root_id)['id']

        # Try to create circular reference (should fail validation)
        result = execute_query(db, """
            SELECT tenant.move_location($1, $2);
        """, root_id, child_id)

        # Should return error
        assert result['status'] == 'error'
        assert 'circular' in result['message'].lower()

        # Valid move should succeed
        result = execute_query(db, """
            SELECT tenant.move_location($1, NULL);  -- Make root
        """, child_id)

        assert result['status'] == 'success'
        assert result['extra_metadata']['pathsUpdated'] > 0
```

**Expected**: ❌ FAIL initially, then ✅ PASS

#### ✅ QA: Phase 5 Complete

```bash
uv run pytest tests/integration/test_explicit*.py -v
make integration
```

---

### **Phase 6: Documentation & Migration** (Day 15)

**Objective**: Document pattern and provide migration guide

**Deliverables**:

1. **User Documentation** (`docs/guides/EXPLICIT_VALIDATION_GUIDE.md`)
2. **Migration Guide** (`docs/migration/TRIGGER_TO_EXPLICIT_MIGRATION.md`)
3. **API Reference** (Update function comments)

---

## 📊 Summary

### Timeline

| Phase | Days | Focus | Deliverables |
|-------|------|-------|-------------|
| **Phase 1** | 7-8 | Core types & validation functions | Types, validate functions, tests |
| **Phase 2** | 9-10 | Identifier recalculation | recalculate_identifier(), tests |
| **Phase 3** | 11 | Team B integration | Schema generator updates |
| **Phase 4** | 12-13 | Team C integration | Mutation compiler updates |
| **Phase 5** | 14 | Integration testing | End-to-end tests |
| **Phase 6** | 15 | Documentation | Guides, migration docs |

**Total**: 7 days (1.5 weeks)

### Files Created/Modified

**New SQL Templates** (6 files):
- `templates/sql/hierarchy/validate_hierarchy_change.sql.jinja2`
- `templates/sql/hierarchy/validate_identifier_sequence.sql.jinja2`
- `templates/sql/hierarchy/recalculate_identifier.sql.jinja2`

**Updated SQL Templates** (1 file):
- `templates/sql/000_types.sql.jinja2` (add validation error type)

**Updated Python Generators** (2 files):
- `src/generators/schema/schema_generator.py`
- `src/generators/actions/action_compiler.py`

**New Tests** (6 files):
- `tests/unit/schema/test_validation_types.py`
- `tests/unit/schema/test_validate_hierarchy.py`
- `tests/unit/schema/test_validate_identifier_sequence.py`
- `tests/unit/schema/test_recalculate_identifier.py`
- `tests/unit/schema/test_schema_generator_explicit_pattern.py`
- `tests/unit/actions/test_action_compiler_explicit_validation.py`
- `tests/integration/test_explicit_validation_e2e.py`

**Documentation** (3 files):
- `docs/guides/EXPLICIT_VALIDATION_GUIDE.md`
- `docs/migration/TRIGGER_TO_EXPLICIT_MIGRATION.md`
- Update existing team docs

**Total Effort**: ~1200 lines SQL + 800 lines Python + 1500 lines tests = 3500 lines

---

## ✅ Final Acceptance Criteria

- [ ] Zero triggers for validation logic
- [ ] All validations return structured errors (not exceptions)
- [ ] Mutations call validations explicitly (visible in code)
- [ ] Path recalculation explicit (existing ✅)
- [ ] Identifier recalculation explicit (NEW ✅)
- [ ] Team B generates no triggers
- [ ] Team C generates explicit calls
- [ ] 90%+ test coverage
- [ ] Integration tests pass
- [ ] Documentation complete
- [ ] Migration guide written

---

## 🎯 Benefits Achieved

✅ **Visibility**: All operations visible in generated code
✅ **Debuggability**: Clear call sites, easy to trace
✅ **Testability**: Functions testable in isolation
✅ **Control**: Can skip validations when safe
✅ **Consistency**: Same pattern for all framework operations
✅ **Performance**: No hidden trigger cascades
✅ **Maintainability**: Easier to understand and modify

---

**Status**: 🎯 Ready for Implementation
**Priority**: CRITICAL (refactors Phase 7 of Team B)
**Timeline**: Days 7-15 of Team B (Week 2)
**Dependencies**: Phases 1-6 of Team B complete
