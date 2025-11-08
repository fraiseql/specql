# Team B: Fix Legacy Function Generator - Authentication Context

**Priority**: 🔴 HIGH
**Status**: ⚠️ INCOMPLETE (60% done)
**File**: `src/generators/function_generator.py`

---

## 🎯 Problem Summary

The **legacy function generator** (`function_generator.py`) is still using outdated patterns:
- ❌ Missing `auth_tenant_id` / `auth_user_id` parameters
- ❌ Hardcoded `null` for audit fields (`created_by`, `updated_by`, `deleted_by`)
- ❌ No tenant context for multi-tenancy

**Good news**: The new **App/Core pattern** generators are already correct! This only affects the legacy generator.

---

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Core Logic Generator** | ✅ 100% | Perfect - uses `auth_*` throughout |
| **App Wrapper Template** | ✅ 95% | Correct (metadata is Team D's job) |
| **Core CRUD Templates** | ✅ 100% | All correct |
| **Legacy CRUD Functions** | ❌ 0% | **NEEDS FIX** - Missing `auth_*` params |
| **Legacy Action Functions** | ❌ 0% | **NEEDS FIX** - Missing `auth_*` params |

**Overall Team B Progress**: 60% complete

---

## 🔍 Issues Found

### Issue 1: Missing `auth_*` Parameters in Function Signatures

**Location**: Lines 98, 167, 246, 298

**Current (WRONG)**:
```python
# Line 98 - Create function
params = ["p_input JSONB"]

# Line 167 - Update function
params = ["p_id TEXT", "p_input JSONB"]

# Line 246 - Delete function
params = ["p_id TEXT"]

# Line 298 - Action function
params = ["p_input JSONB DEFAULT NULL"]
```

**Should be (CORRECT)**:
```python
# All functions need auth context
params = [
    "p_input JSONB",  # or p_id for update/delete
    "auth_tenant_id TEXT DEFAULT NULL",
    "auth_user_id UUID DEFAULT NULL"
]
```

---

### Issue 2: Hardcoded `null` for Audit Fields

**Location**: Lines 221, 257, 259

**Current (WRONG)**:
```python
# Line 221 - Update function
updated_by = null  # TODO: Add user context

# Line 257 - Delete function
deleted_by = null,  # TODO: Add user context

# Line 259 - Delete function
updated_by = null
```

**Should be (CORRECT)**:
```python
updated_by = auth_user_id
deleted_by = auth_user_id
```

---

### Issue 3: Missing `created_by` in Create Function

**Location**: Lines 123-131

**Current (WRONG)**:
```python
INSERT INTO {schema}.{table_name} (
    {field_list},
    created_at,
    updated_at
)
VALUES (
    {value_list},
    now(),
    now()
)
```

**Should be (CORRECT)**:
```python
INSERT INTO {schema}.{table_name} (
    {field_list},
    created_at,
    created_by,    -- ADD THIS
    updated_at
)
VALUES (
    {value_list},
    now(),
    auth_user_id,  -- ADD THIS
    now()
)
```

---

## 🛠️ Required Fixes

### Fix 1: Update `_generate_create_function()` (Lines 90-158)

**Changes**:
1. Add `auth_*` params to signature
2. Add `created_by` to INSERT

**Implementation**:
```python
def _generate_create_function(self, entity: Entity) -> str:
    """Generate INSERT function for entity"""
    schema = entity.schema
    table_name = f"tb_{entity.name.lower()}"
    function_name = f"fn_create_{entity.name.lower()}"

    # Build parameter list
    params = [
        "p_input JSONB",
        "auth_tenant_id TEXT DEFAULT NULL",  # ✅ ADD
        "auth_user_id UUID DEFAULT NULL"     # ✅ ADD
    ]

    # Build parameter assignments (existing logic)
    # ...

    # Build INSERT SQL
    field_list = ", ".join(business_fields)
    value_list = ", ".join([f"v_data.{field}" for field in business_fields])

    insert_sql = f"""
    -- Create record
    INSERT INTO {schema}.{table_name} (
        {field_list},
        created_at,
        created_by,    -- ✅ ADD
        updated_at
    )
    VALUES (
        {value_list},
        now(),
        auth_user_id,  -- ✅ ADD
        now()
    )
    RETURNING pk_{entity.name.lower()}, id INTO v_pk, v_uuid;"""

    # Rest of function body...
```

---

### Fix 2: Update `_generate_update_function()` (Lines 160-237)

**Changes**:
1. Add `auth_*` params to signature
2. Replace `updated_by = null` with `auth_user_id`

**Implementation**:
```python
def _generate_update_function(self, entity: Entity) -> str:
    """Generate UPDATE function for entity"""
    schema = entity.schema
    table_name = f"tb_{entity.name.lower()}"
    function_name = f"fn_update_{entity.name.lower()}"

    # Build parameter list
    params = [
        "p_id TEXT",
        "p_input JSONB",
        "auth_tenant_id TEXT DEFAULT NULL",  # ✅ ADD
        "auth_user_id UUID DEFAULT NULL"     # ✅ ADD
    ]

    # ... existing FK lookup logic ...

    # Build function body
    function_body = f"""
    -- Resolve primary key
    v_pk := core.{entity.name.lower()}_pk(p_id);

    -- ... existing logic ...

    -- Update record
    UPDATE {schema}.{table_name}
    SET
{chr(10).join(update_assignments)},
        updated_at = now(),
        updated_by = auth_user_id  -- ✅ CHANGE FROM null
    WHERE pk_{entity.name.lower()} = v_pk;

    -- Return updated record
    RETURN jsonb_build_object(
        'success', true,
        'result', jsonb_build_object(
            'id', v_current.id,
            'pk', v_pk
        ),
        'error', null
    );
"""
    # ...
```

---

### Fix 3: Update `_generate_delete_function()` (Lines 239-281)

**Changes**:
1. Add `auth_*` params to signature
2. Replace `deleted_by = null` with `auth_user_id`
3. Replace `updated_by = null` with `auth_user_id`

**Implementation**:
```python
def _generate_delete_function(self, entity: Entity) -> str:
    """Generate soft DELETE function for entity"""
    schema = entity.schema
    table_name = f"tb_{entity.name.lower()}"
    function_name = f"fn_delete_{entity.name.lower()}"

    # Build parameter list
    params = [
        "p_id TEXT",
        "auth_tenant_id TEXT DEFAULT NULL",  # ✅ ADD
        "auth_user_id UUID DEFAULT NULL"     # ✅ ADD
    ]

    # Build function body
    function_body = f"""
    -- Resolve primary key
    v_pk := core.{entity.name.lower()}_pk(p_id);

    -- Soft delete
    UPDATE {schema}.{table_name}
    SET
        deleted_at = now(),
        deleted_by = auth_user_id,  -- ✅ CHANGE FROM null
        updated_at = now(),
        updated_by = auth_user_id   -- ✅ CHANGE FROM null
    WHERE pk_{entity.name.lower()} = v_pk
      AND deleted_at IS NULL;

    -- Check if record was found and updated
    IF FOUND THEN
        RETURN jsonb_build_object(
            'success', true,
            'result', jsonb_build_object('deleted', true),
            'error', null
        );
    ELSE
        RETURN jsonb_build_object(
            'success', false,
            'result', null,
            'error', 'Record not found or already deleted'
        );
    END IF;
"""
    # ...
```

---

### Fix 4: Update `_generate_action_function()` (Lines 283-318)

**Changes**:
1. Add `auth_*` params to signature
2. Pass auth context to action step converters

**Implementation**:
```python
def _generate_action_function(self, entity: Entity, action: Action) -> str:
    """
    Generate function for SpecQL action

    Args:
        entity: Entity containing the action
        action: Action to generate function for

    Returns:
        SQL function definition
    """
    schema = entity.schema
    function_name = f"fn_{action.name}"

    # Build parameter list
    params = [
        "p_input JSONB DEFAULT NULL",
        "auth_tenant_id TEXT DEFAULT NULL",  # ✅ ADD
        "auth_user_id UUID DEFAULT NULL"     # ✅ ADD
    ]

    # Convert action steps to PL/pgSQL
    # NOTE: Need to pass auth context to step converters
    plpgsql_body = self._convert_action_steps_to_plpgsql(
        entity,
        action.steps,
        auth_tenant_id='auth_tenant_id',  # ✅ ADD
        auth_user_id='auth_user_id'       # ✅ ADD
    )

    # Build function body
    function_body = f"""
    -- {action.name} action implementation
{plpgsql_body}

    -- Return success
    RETURN jsonb_build_object(
        'success', true,
        'result', jsonb_build_object('action', '{action.name}'),
        'error', null
    );
"""

    return self.sql_utils.format_create_function(
        schema, function_name, params, "JSONB", function_body.strip(), "plpgsql"
    )
```

---

### Fix 5: Update `_convert_action_steps_to_plpgsql()` (Lines 320-388)

**Changes**:
1. Accept `auth_tenant_id` and `auth_user_id` parameters
2. Use them in UPDATE/INSERT steps

**Implementation**:
```python
def _convert_action_steps_to_plpgsql(
    self,
    entity: Entity,
    steps: List[ActionStep],
    auth_tenant_id: str = 'auth_tenant_id',  # ✅ ADD
    auth_user_id: str = 'auth_user_id'       # ✅ ADD
) -> str:
    """
    Convert SpecQL action steps to PL/pgSQL code

    Args:
        entity: Entity context
        steps: List of action steps
        auth_tenant_id: Variable name for tenant ID
        auth_user_id: Variable name for user ID

    Returns:
        PL/pgSQL code block
    """
    plpgsql_lines = []

    for step in steps:
        if step.type == "validate" and step.expression:
            # ... existing validation logic ...

        elif step.type == "insert":
            # Generate INSERT logic with audit fields
            plpgsql_lines.append(f"        -- Insert into {step.entity}")
            plpgsql_lines.append(f"        -- TODO: Add created_by = {auth_user_id}")

        elif step.type == "update":
            # Generate UPDATE logic with audit fields
            plpgsql_lines.append(f"        -- Update {step.entity}")
            plpgsql_lines.append(f"        -- TODO: Add updated_by = {auth_user_id}")

        # ... rest of step handling ...

    return "\n".join(plpgsql_lines)
```

---

## 🧪 Testing Requirements

### Test 1: Create Function Has Auth Params
```python
def test_legacy_create_function_has_auth_params():
    """Legacy create function should have auth_tenant_id and auth_user_id"""
    entity = Entity(name='Contact', schema='crm', fields={...})
    gen = FunctionGenerator()
    sql = gen._generate_create_function(entity)

    assert 'auth_tenant_id TEXT' in sql
    assert 'auth_user_id UUID' in sql
    assert 'created_by' in sql
    assert 'auth_user_id' in sql.split('VALUES')[1]  # In INSERT values


def test_legacy_create_uses_auth_user_for_created_by():
    """Legacy create should set created_by = auth_user_id"""
    entity = Entity(name='Contact', schema='crm', fields={...})
    gen = FunctionGenerator()
    sql = gen._generate_create_function(entity)

    # Should NOT have null for created_by
    assert 'created_by = null' not in sql.lower()
    # Should have auth_user_id in VALUES
    values_section = sql.split('VALUES')[1]
    assert 'auth_user_id' in values_section
```

### Test 2: Update Function Has Auth Params
```python
def test_legacy_update_function_has_auth_params():
    """Legacy update function should have auth_tenant_id and auth_user_id"""
    entity = Entity(name='Contact', schema='crm', fields={...})
    gen = FunctionGenerator()
    sql = gen._generate_update_function(entity)

    assert 'auth_tenant_id TEXT' in sql
    assert 'auth_user_id UUID' in sql
    assert 'updated_by = auth_user_id' in sql


def test_legacy_update_no_null_audit_fields():
    """Legacy update should NOT have null for audit fields"""
    entity = Entity(name='Contact', schema='crm', fields={...})
    gen = FunctionGenerator()
    sql = gen._generate_update_function(entity)

    # Should NOT have TODO or null for updated_by
    assert 'TODO: Add user context' not in sql
    assert 'updated_by = null' not in sql.lower()
```

### Test 3: Delete Function Has Auth Params
```python
def test_legacy_delete_function_has_auth_params():
    """Legacy delete function should have auth_tenant_id and auth_user_id"""
    entity = Entity(name='Contact', schema='crm', fields={...})
    gen = FunctionGenerator()
    sql = gen._generate_delete_function(entity)

    assert 'auth_tenant_id TEXT' in sql
    assert 'auth_user_id UUID' in sql
    assert 'deleted_by = auth_user_id' in sql
    assert 'updated_by = auth_user_id' in sql


def test_legacy_delete_no_null_audit_fields():
    """Legacy delete should NOT have null for audit fields"""
    entity = Entity(name='Contact', schema='crm', fields={...})
    gen = FunctionGenerator()
    sql = gen._generate_delete_function(entity)

    # Should NOT have null for deleted_by or updated_by
    assert 'deleted_by = null' not in sql.lower()
    assert 'updated_by = null' not in sql.lower()
    assert 'TODO' not in sql
```

### Test 4: Action Function Has Auth Params
```python
def test_legacy_action_function_has_auth_params():
    """Legacy action function should have auth_tenant_id and auth_user_id"""
    entity = Entity(name='Contact', schema='crm', fields={...})
    action = Action(name='qualify_lead', steps=[...])
    gen = FunctionGenerator()
    sql = gen._generate_action_function(entity, action)

    assert 'auth_tenant_id TEXT' in sql
    assert 'auth_user_id UUID' in sql
```

---

## 🔄 TDD Workflow

### RED Phase
```bash
# Write failing tests
vim tests/unit/generators/test_function_generator.py
# Add the tests above

uv run pytest tests/unit/generators/test_function_generator.py::test_legacy_create_function_has_auth_params -v
# Expected: FAIL
```

### GREEN Phase
```bash
# Fix the function generator
vim src/generators/function_generator.py
# Apply fixes 1-5 above

uv run pytest tests/unit/generators/test_function_generator.py -v
# Expected: PASS
```

### REFACTOR Phase
```bash
# Clean up duplicated code
# Consider extracting common patterns

uv run pytest tests/unit/generators/test_function_generator.py -v
# Still PASS
```

### QA Phase
```bash
# Full generator tests
make teamB-test

# Integration check
make test
```

---

## ✅ Acceptance Criteria

- [ ] `_generate_create_function()` has `auth_*` params and uses `auth_user_id` for `created_by`
- [ ] `_generate_update_function()` has `auth_*` params and uses `auth_user_id` for `updated_by`
- [ ] `_generate_delete_function()` has `auth_*` params and uses `auth_user_id` for `deleted_by` and `updated_by`
- [ ] `_generate_action_function()` has `auth_*` params
- [ ] `_convert_action_steps_to_plpgsql()` accepts and uses auth context
- [ ] All tests pass
- [ ] No `TODO: Add user context` comments remain
- [ ] No `= null` for audit fields (`created_by`, `updated_by`, `deleted_by`)

---

## 📊 Priority & Timeline

**Priority**: 🔴 HIGH
**Reason**: Legacy generator is still used when `entity.operations` is defined (not SpecQL actions)

**Timeline**: Week 2, Days 1-2 (same as original Team B timeline)

**Coordination**:
- After fixing, ensure consistency with Core Logic Generator patterns
- Team D will then add FraiseQL metadata for these functions too

---

## 🎯 Why This Matters

### Current Usage Pattern

The legacy generator is invoked from `generate_crud_functions()` (lines 29-53):

```python
def generate_crud_functions(self, entity: Entity) -> str:
    functions = []

    # Create function
    if entity.operations and entity.operations.create:
        functions.append(self._generate_create_function(entity))  # ❌ USES LEGACY

    # Update function
    if entity.operations and entity.operations.update:
        functions.append(self._generate_update_function(entity))  # ❌ USES LEGACY

    # Delete function
    if entity.operations and entity.operations.delete:
        functions.append(self._generate_delete_function(entity))  # ❌ USES LEGACY

    return "\n\n".join(functions)
```

**This means**: If entities use `operations:` in YAML (not `actions:`), they get legacy functions with broken auth context!

### Security Impact

**Without auth context**:
- ❌ Audit trail is incomplete (`created_by`/`updated_by` are null)
- ❌ Cannot track who created/modified/deleted records
- ❌ Multi-tenancy broken (no tenant_id filtering)
- ❌ Compliance issues (no accountability)

**With auth context**:
- ✅ Full audit trail
- ✅ Tenant isolation works
- ✅ Compliance-ready
- ✅ Security best practices

---

## 📞 Questions?

**Q: Should we deprecate the legacy generator instead of fixing it?**
A: Possibly! If you're only using the App/Core pattern going forward, you could:
1. Mark legacy generator as deprecated
2. Remove it in a future version
3. Focus only on App/Core pattern

**Q: What's the difference between legacy and App/Core?**
A:
- **Legacy**: Single-layer functions, generated in `function_generator.py`
- **App/Core**: Two-layer pattern (app wrapper + core logic), better separation of concerns

**Q: Do I need to fix the legacy generator if we're not using it?**
A: Check your entity YAML files:
- If they use `operations:` → Legacy generator is used → **Must fix**
- If they use `actions:` → App/Core pattern is used → **Already correct**

---

## 🎯 Summary

**Current Status**: Team B is 60% complete
- ✅ App/Core pattern generators: Perfect
- ❌ Legacy function generator: Needs auth context

**What to Fix**:
1. Add `auth_tenant_id` / `auth_user_id` to all legacy function signatures
2. Replace `null` with `auth_user_id` for audit fields
3. Add `created_by` to INSERT statements

**Timeline**: Week 2, Days 1-2
**Priority**: HIGH (security and audit trail)

---

**File**: `src/generators/function_generator.py`
**Lines to Fix**: 98, 123-131, 167, 221, 246, 257, 259, 298, 320-388
**Tests**: `tests/unit/generators/test_function_generator.py`
