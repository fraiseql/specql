# Explicit Path Recalculation Pattern

**Decision**: Explicit over Implicit - NO TRIGGERS!
**Status**: ✅ Approved
**Date**: 2025-11-09

---

## 📋 Overview

The framework uses **explicit path recalculation** instead of database triggers for hierarchical entity path updates.

### Key Principle

**Mutations call `core.recalculate_tree_path()` explicitly, not via hidden triggers.**

---

## 🎯 Why Explicit Over Implicit?

| Aspect | Triggers (Implicit) ❌ | Explicit Calls ✅ |
|--------|----------------------|------------------|
| **Visibility** | Hidden in database | Visible in generated code |
| **Debugging** | Hard to trace | Easy to trace |
| **Testing** | Fires implicitly | Full control in tests |
| **Performance** | Unpredictable cascades | Predictable, controllable |
| **Transaction Control** | Coupled | Decoupled |
| **Code Clarity** | "Magic happens" | "This recalculates N paths" |

---

## 🏗️ Architecture

### Team B Responsibility: Generic Function

**Generate ONE framework function** (not per-entity):

```sql
-- File: templates/sql/hierarchy/recalculate_tree_path.sql.jinja2

CREATE TYPE core.recalculation_context AS (
    pk UUID,           -- Entity id (subtree mode)
    pk_tenant UUID,    -- Tenant scope (tenant mode)
    updated_by UUID    -- Audit tracking
);

CREATE FUNCTION core.recalculate_tree_path(
    entity TEXT,
    ctx core.recalculation_context
) RETURNS INTEGER;
```

**Three modes**:
1. **Subtree**: `ctx.pk` set → Recalculate from node down
2. **Tenant**: `ctx.pk_tenant` set → Recalculate all tenant trees
3. **Global**: Both NULL → Recalculate entire entity

### Team C Responsibility: Explicit Calls

**Generate explicit recalculation in mutations**:

```sql
-- Generated move_location function
CREATE FUNCTION tenant.move_location(p_id UUID, p_new_parent_id UUID) ...
DECLARE
    v_location_pk INTEGER;  -- INTEGER pk (naming: v_{entity}_pk)
    v_new_parent_pk INTEGER;
    v_paths_updated INTEGER;
BEGIN
    -- Resolve UUIDs to INTEGER pks
    v_location_pk := tenant.location_pk(p_id);
    v_new_parent_pk := tenant.location_pk(p_new_parent_id);

    -- Update parent
    UPDATE tenant.tb_location
    SET fk_parent_location = v_new_parent_pk
    WHERE pk_location = v_location_pk;

    -- ✅ EXPLICIT recalculation (visible!)
    v_paths_updated := core.recalculate_tree_path(
        'location',
        ROW(v_location_pk, NULL, p_caller_id)::core.recalculation_context
    );

    -- Include in response
    v_result.extra_metadata := jsonb_build_object(
        'pathsUpdated', v_paths_updated
    );
END;
```

---

## 📝 SpecQL Syntax

### Method 1: Explicit Declaration (Recommended)

```yaml
entity: Location
hierarchical: true

actions:
  - name: move_location

    # Explicit hierarchy impact
    hierarchy_impact: recalculate_subtree

    steps:
      - validate: not_circular($new_parent_id)
      - update: Location SET fk_parent_location = $new_parent_id
      # Framework auto-injects recalculation call
```

### Method 2: Auto-Detection (Fallback)

```yaml
actions:
  - name: move_location
    steps:
      - update: Location SET fk_parent_location = $new_parent_id
      # Framework detects parent field change → auto-injects subtree recalc
```

### Hierarchy Impact Values

- `recalculate_subtree`: Recalculate from modified node down (default for parent changes)
- `recalculate_tenant`: Recalculate all trees in tenant
- `recalculate_global`: Recalculate entire entity globally

---

## 🔧 Implementation Details

### Generic Function (Team B)

**Based on printoptim_backend pattern**:

```sql
CREATE FUNCTION core.recalculate_tree_path(entity TEXT, ctx core.recalculation_context)
RETURNS INTEGER AS $$
DECLARE
    v_schema TEXT;
    v_table TEXT;
    v_pk_column TEXT;
    v_parent_column TEXT;
BEGIN
    -- Dynamic schema discovery
    v_table := format('tb_%s', entity);
    v_pk_column := format('pk_%s', entity);
    v_parent_column := format('fk_parent_%s', entity);

    SELECT table_schema INTO v_schema
    FROM information_schema.tables
    WHERE table_name = v_table;

    -- MODE 1: Subtree (ctx.pk set)
    IF ctx.pk IS NOT NULL THEN
        -- Recalculate from given node down using INTEGER pk paths
        WITH RECURSIVE hierarchy AS (
            SELECT t.pk_location AS pk, t.pk_location::TEXT AS path_str
            FROM tenant.tb_location t
            WHERE t.id = ctx.pk

            UNION ALL

            SELECT c.pk_location, CONCAT(h.path_str, '.', c.pk_location::TEXT)
            FROM tenant.tb_location c
            JOIN hierarchy h ON c.fk_parent_location = h.pk
        )
        UPDATE tenant.tb_location t
        SET
            path = h.path_str::ltree,
            path_updated_at = now(),
            path_updated_by = ctx.updated_by
        FROM hierarchy h
        WHERE t.pk_location = h.pk
          AND t.path IS DISTINCT FROM h.path_str::ltree;  -- Idempotent

    -- MODE 2: Tenant (ctx.pk_tenant set)
    ELSIF ctx.pk_tenant IS NOT NULL THEN
        -- Similar but starting from all tenant roots

    -- MODE 3: Global (both NULL)
    ELSE
        -- Recalculate all trees
    END IF;

    RETURN (number of updated rows);
END;
$$ LANGUAGE plpgsql;
```

**Key Features**:
- ✅ Dynamic schema discovery
- ✅ INTEGER pk-based paths (e.g., `1.5.23.47`)
- ✅ Idempotent (only updates if changed)
- ✅ Returns count for transparency
- ✅ Audit tracking built-in

### Mutation Compilation (Team C)

**File**: `src/generators/actions/step_compiler.py`

```python
def compile_action_with_path_recalc(action: ActionAST, entity: EntityAST) -> str:
    """Compile action with automatic path recalculation injection."""

    # Detect if recalculation needed
    recalc_scope = needs_path_recalculation(action, entity)

    # Generate function body
    function_body = []
    for step in action.steps:
        function_body.append(compile_step(step, entity))

    # Inject explicit recalculation call
    if recalc_scope and entity.hierarchical:
        recalc_call = generate_path_recalculation_call(
            entity,
            recalc_scope,
            entity_id_var='p_id',
            caller_id_var='p_caller_id'
        )
        function_body.append(recalc_call)

        # Add to response metadata
        function_body.append("""
    v_result.extra_metadata := jsonb_build_object(
        'pathsUpdated', v_paths_updated
    );
""")

    return '\n'.join(function_body)


def needs_path_recalculation(action: ActionAST, entity: EntityAST) -> Optional[str]:
    """Determine if action needs path recalculation."""

    # Method 1: Explicit declaration
    if hasattr(action, 'hierarchy_impact'):
        return map_hierarchy_impact(action.hierarchy_impact)

    # Method 2: Auto-detect parent field changes
    for step in action.steps:
        if isinstance(step, UpdateStep):
            parent_field = f'fk_parent_{entity.name.lower()}'
            if parent_field in step.fields:
                return 'subtree'  # Default

    return None
```

---

## 📊 Comparison: Before vs After

### Before (Triggers)

```sql
-- User doesn't see this
CREATE TRIGGER trg_update_location_path
    BEFORE UPDATE OF fk_parent_location
    ON tenant.tb_location
    FOR EACH ROW
    EXECUTE FUNCTION tenant.update_location_path();

-- Mutation hides the complexity
CREATE FUNCTION tenant.move_location(...)
    UPDATE tenant.tb_location SET fk_parent_location = v_new_parent_pk;
    -- Trigger fires invisibly
```

**Problems**:
- ❌ Hidden side effects
- ❌ Hard to debug
- ❌ Can't control transaction
- ❌ Difficult to test

### After (Explicit)

```sql
-- NO TRIGGERS!

-- Mutation shows exactly what happens
CREATE FUNCTION tenant.move_location(...)
    -- Update parent
    UPDATE tenant.tb_location SET fk_parent_location = v_new_parent_pk;

    -- ✅ EXPLICIT recalculation (visible!)
    v_paths_updated := core.recalculate_tree_path(
        'location',
        ROW(p_id, NULL, p_caller_id)::core.recalculation_context
    );

    -- ✅ Include in response for transparency
    v_result.extra_metadata := jsonb_build_object('pathsUpdated', v_paths_updated);
```

**Benefits**:
- ✅ Visible in generated code
- ✅ Easy to debug
- ✅ Full transaction control
- ✅ Testable in isolation

---

## 🧪 Testing Strategy

### Test Generic Function (Team B)

```python
def test_recalculate_tree_path_subtree(db):
    """Test subtree recalculation mode."""

    # Setup hierarchy: root -> child1 -> child2
    root_id = create_location(db, name="Root", parent=None)
    child1_id = create_location(db, name="Child1", parent=root_id)
    child2_id = create_location(db, name="Child2", parent=child1_id)

    # Move child1 to a different parent
    new_parent_id = create_location(db, name="NewParent", parent=None)

    # Call explicit recalculation
    updated_count = db.execute("""
        SELECT core.recalculate_tree_path(
            'location',
            ROW(%s, NULL, %s)::core.recalculation_context
        )
    """, [child1_id, admin_user_id])

    # Verify
    assert updated_count == 2  # child1 + child2

    # Verify paths updated
    paths = get_location_paths(db, [child1_id, child2_id])
    assert paths[child1_id].startswith(new_parent_pk)
    assert paths[child2_id].startswith(new_parent_pk)
```

### Test Mutation (Team C)

```python
def test_move_location_recalculates_paths(db):
    """Test move_location explicitly recalculates paths."""

    # Setup
    root_id = create_location(db, name="Root")
    child_id = create_location(db, name="Child", parent=root_id)
    new_parent_id = create_location(db, name="NewParent")

    # Call mutation
    result = db.call_function('tenant.move_location', {
        'p_id': child_id,
        'p_new_parent_id': new_parent_id,
        'p_caller_id': admin_user_id
    })

    # Verify explicit behavior
    assert result.status == 'success'
    assert result.extra_metadata['pathsUpdated'] == 1

    # Verify path changed
    child = get_location(db, child_id)
    assert child.path.startswith(get_location_pk(db, new_parent_id))
```

---

## 📚 Benefits Summary

### For Developers

1. **Visibility**: See exactly what happens in generated code
2. **Debugging**: Trace execution flow easily
3. **Testing**: Full control over recalculation in tests
4. **Performance**: Predictable, no cascading surprises

### For Framework

1. **Single Function**: 1 generic function vs. N triggers
2. **Code Reduction**: 80% less generated code
3. **Maintainability**: Update 1 function vs. N triggers
4. **Consistency**: Same pattern across all hierarchical entities

### For Users

1. **Transparency**: Mutation responses show `pathsUpdated` count
2. **Error Handling**: Recalculation errors are explicit, not hidden
3. **Performance**: Can optimize recalculation timing
4. **Trust**: No hidden database magic

---

## 🚀 Migration Path

### From Current Plan

**OLD** (Team B Phase 3):
- Generate 3 functions per entity (calculate, update trigger, recalculate descendants)
- Total: 3N functions for N entities

**NEW** (This Pattern):
- Generate 1 generic function (Team B)
- Compile explicit calls in mutations (Team C)
- Total: 1 + N mutations

**Savings**: 67% code reduction for 5 hierarchical entities

### Implementation Order

1. **Week 2 Day 3-4** (Team B): Generate `core.recalculate_tree_path()` + context type
2. **Week 3 Day 4** (Team C): Implement recalculation detection + injection
3. **Week 4** (Testing): Verify across multiple hierarchical entities

---

## 📖 Related Documentation

- See `docs/teams/TEAM_B_DATABASE_DECISIONS_PLAN.md` - Phase 3 (revised)
- See `docs/teams/TEAM_C_DATABASE_DECISIONS_PLAN.md` - Phase 4 (revised)
- See printoptim_backend: `db/0_schema/03_functions/030_common/0304_hierarchy/03041_recalculate_tree_path.sql`

---

**Decision**: ✅ Adopted explicit recalculation pattern
**Impact**: Major - affects all hierarchical entities
**Status**: Ready for implementation
