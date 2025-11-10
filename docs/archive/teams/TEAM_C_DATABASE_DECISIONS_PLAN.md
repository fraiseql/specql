# Team C: Database Decisions Implementation Plan

**Team**: Action Compiler (Business Logic → PL/pgSQL)
**Impact**: MEDIUM (audit field usage, path recalculation logic)
**Timeline**: Week 3-4 (3-4 days)
**Status**: 🟡 MEDIUM PRIORITY - Depends on Team B

---

## 📋 Overview

Team C must update action compilation to:

1. ✅ Use correct audit fields (identifier_recalculated_at, NOT updated_at)
2. ✅ Idempotent recalculation (only update if changed)
3. ✅ Path recalculation only on parent change
4. ✅ Generate helper function usage in business logic

**Total Effort**: 3-4 days

---

## 🎯 Phase 1: Correct Audit Field Usage (Day 1)

### **Objective**: Update audit field logic in generated functions

### **1.1: Business Data Updates → updated_at**

**When**: User-initiated business data changes

**File**: `templates/actions/update_entity.sql.jinja2`

```sql
-- Business data update (user changes name, description, etc.)
CREATE OR REPLACE FUNCTION {{ schema }}.update_{{ entity_lower }}(
    p_id UUID,
    p_updates JSONB,
    p_caller_id UUID DEFAULT NULL
) RETURNS mutation_result AS $$
DECLARE
    v_pk_{{ entity_lower }} INTEGER;
    v_result mutation_result;
BEGIN
    -- Resolve UUID → INTEGER
    v_pk_{{ entity_lower }} := {{ schema }}.{{ entity_lower }}_pk(p_id);

    -- Update business fields
    UPDATE {{ schema }}.tb_{{ entity_lower }}
    SET
        name = COALESCE((p_updates->>'name')::TEXT, name),
        description = COALESCE((p_updates->>'description')::TEXT, description),
        -- ... other business fields

        -- ✅ CORRECT: Update updated_at for business changes
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_{{ entity_lower }} = v_pk_{{ entity_lower }};

    -- Build response
    v_result.status := 'success';
    v_result.message := '{{ entity }} updated successfully';
    v_result.updated_fields := array_agg(key)
        FROM jsonb_each(p_updates);

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

### **1.2: Identifier Recalculation → identifier_recalculated_at**

**When**: System recalculates identifier (due to parent change, type change, etc.)

**File**: `templates/actions/recalculate_identifier.sql.jinja2`

```sql
-- Identifier recalculation (system-initiated)
CREATE OR REPLACE FUNCTION {{ schema }}.recalculate_{{ entity_lower }}_identifier(
    p_pk_{{ entity_lower }} INTEGER,
    p_caller_id UUID DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    v_new_identifier TEXT;
    v_old_identifier TEXT;
BEGIN
    -- Get current identifier
    SELECT identifier INTO v_old_identifier
    FROM {{ schema }}.tb_{{ entity_lower }}
    WHERE pk_{{ entity_lower }} = p_pk_{{ entity_lower }};

    -- Calculate new identifier (business logic)
    v_new_identifier := {{ schema }}.calculate_{{ entity_lower }}_identifier(p_pk_{{ entity_lower }});

    -- Only update if changed (idempotent)
    IF v_new_identifier IS DISTINCT FROM v_old_identifier THEN
        UPDATE {{ schema }}.tb_{{ entity_lower }}
        SET
            identifier = v_new_identifier,

            -- ✅ CORRECT: Update identifier_recalculated_at (NOT updated_at)
            identifier_recalculated_at = now(),
            identifier_recalculated_by = COALESCE(p_caller_id, '00000000-0000-0000-0000-000000000000'::UUID)
            -- Note: NOT updating updated_at (no business data changed)
        WHERE pk_{{ entity_lower }} = p_pk_{{ entity_lower }};
    END IF;

    RETURN v_new_identifier;
END;
$$ LANGUAGE plpgsql;
```

---

### **1.3: Path Recalculation → path_updated_at (EXPLICIT!)**

**When**: Parent changes (mutation EXPLICITLY recalculates paths)

**File**: `templates/actions/move_entity.sql.jinja2`

```sql
-- Move entity to new parent (EXPLICIT path recalculation - NO TRIGGER!)
CREATE OR REPLACE FUNCTION {{ schema }}.move_{{ entity_lower }}(
    p_id UUID,
    p_new_parent_id UUID,
    p_caller_id UUID DEFAULT NULL
) RETURNS mutation_result AS $$
DECLARE
    v_{{ entity_lower }}_pk INTEGER;
    v_new_parent_pk INTEGER;
    v_paths_updated INTEGER;
    v_result mutation_result;
BEGIN
    -- Resolve UUIDs to INTEGER pks
    v_{{ entity_lower }}_pk := {{ schema }}.{{ entity_lower }}_pk(p_id);
    v_new_parent_pk := {{ schema }}.{{ entity_lower }}_pk(p_new_parent_id);

    -- Validation: Prevent circular reference
    IF EXISTS (
        SELECT 1
        FROM {{ schema }}.get_{{ entity_lower }}_descendants(p_id)
        WHERE pk_{{ entity_lower }} = v_new_parent_pk
    ) THEN
        v_result.status := 'error';
        v_result.message := 'Cannot move {{ entity_lower }} under its own descendant';
        RETURN v_result;
    END IF;

    -- Update parent
    UPDATE {{ schema }}.tb_{{ entity_lower }}
    SET
        fk_parent_{{ entity_lower }} = v_new_parent_pk,
        updated_at = now(),        -- Business change
        updated_by = p_caller_id
    WHERE pk_{{ entity_lower }} = v_{{ entity_lower }}_pk;

    -- ✅ EXPLICIT path recalculation (NO TRIGGER!)
    -- Recalculate paths for this subtree
    v_paths_updated := core.recalculate_tree_path(
        '{{ entity_lower }}',
        ROW(
            v_{{ entity_lower }}_pk,  -- INTEGER pk (NOT UUID id!)
            NULL,                     -- No tenant scope
            p_caller_id               -- Audit who triggered it
        )::core.recalculation_context
    );

    -- Success response
    v_result.status := 'success';
    v_result.message := FORMAT('{{ entity }} moved successfully (%s paths updated)', v_paths_updated);
    v_result.extra_metadata := jsonb_build_object(
        'pathsUpdated', v_paths_updated
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

**Key Points**:
- ✅ **Explicit call** to `core.recalculate_tree_path()` - NO hidden triggers!
- ✅ Returns number of paths updated for transparency
- ✅ Both `updated_at` AND `path_updated_at` are updated (business + structural change)
- ✅ Validation prevents circular references BEFORE update

---

## 🎯 Phase 2: Idempotent Recalculation (Day 2)

### **Objective**: Only update database if values actually changed

### **2.1: Idempotent Identifier Recalculation**

```sql
CREATE OR REPLACE FUNCTION {{ schema }}.recalculate_{{ entity_lower }}_identifiers_bulk(
    p_tenant_id UUID DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER := 0;
BEGIN
    WITH calculated AS (
        SELECT
            pk_{{ entity_lower }},
            {{ schema }}.calculate_{{ entity_lower }}_identifier(pk_{{ entity_lower }}) AS new_identifier,
            identifier AS old_identifier
        FROM {{ schema }}.tb_{{ entity_lower }}
        WHERE (p_tenant_id IS NULL OR tenant_id = p_tenant_id)
          AND deleted_at IS NULL
    ),
    updated_rows AS (
        UPDATE {{ schema }}.tb_{{ entity_lower }} l
        SET
            identifier = c.new_identifier,
            identifier_recalculated_at = now(),
            identifier_recalculated_by = '00000000-0000-0000-0000-000000000000'::UUID
        FROM calculated c
        WHERE l.pk_{{ entity_lower }} = c.pk_{{ entity_lower }}
          -- ✅ IDEMPOTENT: Only update if changed
          AND l.identifier IS DISTINCT FROM c.new_identifier
        RETURNING l.pk_{{ entity_lower }}
    )
    SELECT COUNT(*) INTO v_updated_count FROM updated_rows;

    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;
```

**Benefits**:
- ✅ No unnecessary database writes
- ✅ Doesn't trigger downstream updates if nothing changed
- ✅ Faster bulk operations
- ✅ Cleaner audit logs

---

### **2.2: Idempotent Path Recalculation**

Already implemented in Team B's `recalculate_descendant_paths`:

```sql
UPDATE {{ schema }}.tb_{{ entity_lower }} l
SET
    path = s.new_path,
    path_updated_at = now()
FROM subtree s
WHERE l.pk_{{ entity_lower }} = s.pk_{{ entity_lower }}
  AND l.path IS DISTINCT FROM s.new_path  -- ✅ IDEMPOTENT
RETURNING l.pk_{{ entity_lower }}
```

---

## 🎯 Phase 3: Helper Function Integration (Day 3)

### **Objective**: Use generated helper functions in business logic

### **3.1: get_ancestors() in Business Logic**

**Use Case**: Check permissions on parent entities

```sql
-- Example: Check if user has access to any ancestor
CREATE OR REPLACE FUNCTION {{ schema }}.user_can_access_{{ entity_lower }}(
    p_user_id UUID,
    p_{{ entity_lower }}_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_has_access BOOLEAN := FALSE;
BEGIN
    -- Check if user has access to this location or any ancestor
    SELECT EXISTS (
        SELECT 1
        FROM {{ schema }}.get_{{ entity_lower }}_ancestors(p_{{ entity_lower }}_id) a
        INNER JOIN {{ schema }}.user_{{ entity_lower }}_permissions p
            ON p.fk_{{ entity_lower }} = a.pk_{{ entity_lower }}
        WHERE p.fk_user = {{ schema }}.user_pk(p_user_id)
          AND p.permission_type IN ('owner', 'admin', 'edit')
    ) INTO v_has_access;

    RETURN v_has_access;
END;
$$ LANGUAGE plpgsql;
```

---

### **3.2: get_descendants() in Business Logic**

**Use Case**: Cascade operations to children

```sql
-- Example: Archive location and all descendants
CREATE OR REPLACE FUNCTION {{ schema }}.archive_{{ entity_lower }}_tree(
    p_id UUID,
    p_caller_id UUID
) RETURNS mutation_result AS $$
DECLARE
    v_pk_{{ entity_lower }} INTEGER;
    v_archived_count INTEGER;
    v_result mutation_result;
BEGIN
    v_pk_{{ entity_lower }} := {{ schema }}.{{ entity_lower }}_pk(p_id);

    -- Soft-delete this location and all descendants
    WITH archived AS (
        UPDATE {{ schema }}.tb_{{ entity_lower }} l
        SET
            deleted_at = now(),
            deleted_by = p_caller_id
        FROM {{ schema }}.get_{{ entity_lower }}_descendants(p_id) d
        WHERE l.pk_{{ entity_lower }} = d.pk_{{ entity_lower }}
          AND l.deleted_at IS NULL  -- Idempotent
        RETURNING l.pk_{{ entity_lower }}
    )
    SELECT COUNT(*) INTO v_archived_count FROM archived;

    v_result.status := 'success';
    v_result.message := FORMAT('%s {{ entity_lower }}(s) archived', v_archived_count);
    v_result.extra_metadata := jsonb_build_object(
        'archivedCount', v_archived_count
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

### **3.3: move_subtree() in Business Logic**

**Use Case**: Move location and all descendants to new parent

```sql
-- Example: Move subtree (uses helper function for safety)
CREATE OR REPLACE FUNCTION {{ schema }}.move_{{ entity_lower }}_subtree(
    p_id UUID,
    p_new_parent_id UUID,
    p_caller_id UUID
) RETURNS mutation_result AS $$
DECLARE
    v_pk INTEGER;
    v_new_parent_pk INTEGER;
    v_descendant_count INTEGER;
    v_result mutation_result;
BEGIN
    v_pk := {{ schema }}.{{ entity_lower }}_pk(p_id);
    v_new_parent_pk := {{ schema }}.{{ entity_lower }}_pk(p_new_parent_id);

    -- Count descendants (for user feedback)
    SELECT COUNT(*) INTO v_descendant_count
    FROM {{ schema }}.get_{{ entity_lower }}_descendants(p_id);

    -- Move (parent change triggers path recalculation for entire subtree)
    UPDATE {{ schema }}.tb_{{ entity_lower }}
    SET
        fk_parent_{{ entity_lower }} = v_new_parent_pk,
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_{{ entity_lower }} = v_pk;

    -- Trigger automatically recalculates paths for all descendants

    v_result.status := 'success';
    v_result.message := FORMAT(
        '{{ entity }} moved (affected: %s {{ entity_lower }}s)',
        v_descendant_count + 1
    );
    v_result.extra_metadata := jsonb_build_object(
        'affectedCount', v_descendant_count + 1
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

## 🎯 Phase 4: Explicit Path Recalculation Compilation (Day 4)

### **Objective**: Generate explicit path recalculation calls in mutations (NO TRIGGERS!)

### **4.1: Hierarchy Impact Detection**

**File**: `src/generators/actions/step_compiler.py`

```python
from typing import Optional
from ..ast_models import ActionAST, UpdateStep, EntityAST

def needs_path_recalculation(action: ActionAST, entity: EntityAST) -> Optional[str]:
    """Determine if action needs path recalculation and the scope.

    Returns:
        - 'subtree': Recalculate from modified node down
        - 'tenant': Recalculate all tenant trees
        - 'global': Recalculate entire entity
        - None: No recalculation needed
    """

    # Method 1: Explicit hierarchy_impact declaration
    if hasattr(action, 'hierarchy_impact'):
        impact = action.hierarchy_impact
        if impact == 'recalculate_subtree':
            return 'subtree'
        elif impact == 'recalculate_tenant':
            return 'tenant'
        elif impact == 'recalculate_global':
            return 'global'

    # Method 2: Auto-detect from steps
    for step in action.steps:
        if isinstance(step, UpdateStep):
            # Check if parent field is being updated
            parent_field = f'fk_parent_{entity.name.lower()}'
            if parent_field in step.fields:
                return 'subtree'  # Default to subtree for parent changes

    return None


def generate_path_recalculation_call(
    entity: EntityAST,
    scope: str,
    entity_pk_var: str = None,  # Will default to v_{entity}_pk
    tenant_id_var: str = 'p_tenant_id',
    caller_id_var: str = 'p_caller_id'
) -> str:
    """Generate explicit call to core.recalculate_tree_path().

    Args:
        entity: Entity AST
        scope: 'subtree', 'tenant', or 'global'
        entity_pk_var: Variable name containing entity INTEGER pk (e.g., 'v_location_pk')
        tenant_id_var: Variable name containing tenant UUID
        caller_id_var: Variable name containing caller UUID

    Returns:
        SQL code for explicit recalculation
    """

    entity_name = entity.name.lower()

    # Default naming convention: v_{entity}_pk
    if entity_pk_var is None:
        entity_pk_var = f'v_{entity_name}_pk'

    if scope == 'subtree':
        return f"""
    -- EXPLICIT path recalculation (subtree mode)
    v_paths_updated := core.recalculate_tree_path(
        '{entity_name}',
        ROW(
            {entity_pk_var},        -- INTEGER pk (e.g., v_location_pk)
            NULL,                   -- No tenant scope
            {caller_id_var}         -- Audit tracking
        )::core.recalculation_context
    );
"""
    elif scope == 'tenant':
        return f"""
    -- EXPLICIT path recalculation (tenant mode)
    v_paths_updated := core.recalculate_tree_path(
        '{entity_name}',
        ROW(
            NULL,                   -- No specific node
            {tenant_id_var},        -- Tenant scope
            {caller_id_var}         -- Audit tracking
        )::core.recalculation_context
    );
"""
    elif scope == 'global':
        return f"""
    -- EXPLICIT path recalculation (global mode)
    v_paths_updated := core.recalculate_tree_path(
        '{entity_name}',
        ROW(NULL, NULL, {caller_id_var})::core.recalculation_context
    );
"""
    else:
        raise ValueError(f"Invalid scope: {scope}")


def compile_action_with_path_recalc(action: ActionAST, entity: EntityAST) -> str:
    """Compile action with automatic path recalculation injection."""

    recalc_scope = needs_path_recalculation(action, entity)

    # Generate function body
    function_body = []

    # ... compile steps ...
    for step in action.steps:
        function_body.append(compile_step(step, entity))

    # Inject path recalculation if needed
    if recalc_scope and entity.hierarchical:
        entity_name = entity.name.lower()
        recalc_call = generate_path_recalculation_call(
            entity,
            recalc_scope,
            entity_pk_var=f'v_{entity_name}_pk',  # Naming convention: v_{entity}_pk
            caller_id_var='p_caller_id'
        )
        function_body.append(recalc_call)

        # Add to response metadata
        function_body.append("""
    -- Include path update info in response
    v_result.extra_metadata := jsonb_build_object(
        'pathsUpdated', v_paths_updated
    );
""")

    return '\n'.join(function_body)
```

---

### **4.2: SpecQL Syntax for Hierarchy Impact**

**Explicit Declaration** (Recommended):

```yaml
# entities/location.yaml
entity: Location
hierarchical: true

actions:
  - name: move_location

    # Explicit hierarchy impact declaration
    hierarchy_impact: recalculate_subtree

    steps:
      - validate: not_circular($new_parent_id)
      - update: Location SET fk_parent_location = $new_parent_id
      # Framework auto-injects recalculation call!
```

**Auto-Detection** (Fallback):

```yaml
# If hierarchy_impact not declared, framework detects parent field changes
actions:
  - name: move_location
    steps:
      - update: Location SET fk_parent_location = $new_parent_id
      # Framework detects parent change → auto-injects subtree recalculation
```

---

### **4.3: Mutation Responsibility Matrix**

**NO TRIGGERS! All recalculation is explicit in mutations**:

| Change Type | Where It Happens | Audit Fields Updated |
|-------------|-----------------|---------------------|
| **Business data** (name, description) | Mutation UPDATE | `updated_at`, `updated_by` |
| **Parent change** | Mutation UPDATE + explicit recalc call | `updated_at`, `updated_by`, `path_updated_at` |
| **Identifier calc** | Mutation calculation function | `identifier_recalculated_at`, `identifier_recalculated_by` |
| **Bulk recalc** | Admin function | `path_updated_at` (NOT `updated_at`) |

**Key Difference from Triggers**:
- ✅ Path recalculation is **visible** in generated function code
- ✅ Can be **tested** independently
- ✅ **Transaction control** is explicit
- ✅ **Performance** is predictable (no cascading triggers)

---

## 📊 Summary: Team C Deliverables

### **Files to Modify**

| File | Purpose | Changes |
|------|---------|---------|
| `templates/actions/update_entity.sql.jinja2` | Correct audit fields | Update audit logic |
| `templates/actions/recalculate_identifier.sql.jinja2` | Idempotent recalc | Add `IS DISTINCT FROM` |
| `templates/actions/move_entity.sql.jinja2` | Helper function usage | Use `move_subtree()` |
| `src/generators/actions/step_compiler.py` | Detect parent changes | Parent change detection |

### **New Templates**

| Template | Purpose | Lines |
|----------|---------|-------|
| `templates/actions/archive_tree.sql.jinja2` | Cascade operations | 50 |
| `templates/actions/user_permissions.sql.jinja2` | Ancestor checks | 40 |

### **Timeline**

- **Day 1**: Correct audit field usage
- **Day 2**: Idempotent recalculation
- **Day 3**: Helper function integration
- **Day 4**: Path recalculation logic

**Total**: 4 days

---

## ✅ Acceptance Criteria

- [ ] Business updates use `updated_at`
- [ ] Identifier recalculation uses `identifier_recalculated_at` (NOT `updated_at`)
- [ ] Path updates use `path_updated_at` (set by trigger)
- [ ] Recalculation is idempotent (only updates if changed)
- [ ] Helper functions used in business logic
- [ ] Parent changes trigger path recalculation for descendants
- [ ] All tests pass

---

## 🔗 Dependencies

**Depends On**:
- Team B Phase 5 (audit fields schema)
- Team B Phase 3 (path calculation functions)
- Team B Phase 9 (helper functions)

**Blocks**:
- None (Team D/E can work in parallel)

---

**Status**: 🟡 WAITING ON TEAM B
**Priority**: MEDIUM
**Effort**: 4 days
**Start**: After Team B completes Phases 3, 5, 9
