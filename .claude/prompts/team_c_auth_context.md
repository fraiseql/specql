# Team C: Action Compiler - Authentication Context Implementation

**Extracted from**: `auth_context_naming.md`
**Priority**: 🔴 HIGH
**Timeline**: Week 2, Days 3-4

---

## 🎯 Mission

Ensure compiled action functions use `auth_tenant_id` / `auth_user_id` for authentication context.

---

## 📋 Changes Required

### 1. Function Generation
**All compiled action functions must use:**
```sql
auth_tenant_id TEXT DEFAULT NULL
auth_user_id UUID DEFAULT NULL
```

### 2. Pass Through to Sub-Functions
**When calling other functions, pass auth context:**
```sql
-- Call helper function with auth context
PERFORM schema.helper_function(
    p_entity_id,
    auth_tenant_id,  -- Pass through
    auth_user_id     -- Pass through
);
```

### 3. Audit Step Handling
**UPDATE steps must set audit fields:**
```sql
UPDATE schema.tb_entity
SET column = value,
    updated_by = auth_user_id,  -- ✅ Use auth context
    updated_at = now()
WHERE ...
```

**INSERT steps must set created_by:**
```sql
INSERT INTO schema.tb_entity (
    column,
    created_by,   -- ✅ Use auth context
    created_at
) VALUES (
    value,
    auth_user_id,
    now()
);
```

---

## 📝 Example Transformation

### SpecQL Input
```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

### Generated Function (OLD - ❌)
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    input_tenant_id TEXT DEFAULT NULL,  -- ❌ OLD
    input_user_id UUID DEFAULT NULL     -- ❌ OLD
)
RETURNS jsonb AS $$
BEGIN
    -- Update
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_by = input_user_id,     -- ❌ OLD
        updated_at = now()
    WHERE pk_contact = v_pk;
END;
$$ LANGUAGE plpgsql;
```

### Generated Function (NEW - ✅)
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    auth_tenant_id TEXT DEFAULT NULL,  -- ✅ NEW
    auth_user_id UUID DEFAULT NULL     -- ✅ NEW
)
RETURNS jsonb AS $$
DECLARE
    v_pk INTEGER;
BEGIN
    -- Tenant check (if applicable)
    IF auth_tenant_id IS NOT NULL THEN
        PERFORM crm.check_tenant_access(p_contact_id, auth_tenant_id);
    END IF;

    -- Trinity resolution
    v_pk := crm.contact_pk(p_contact_id);

    -- Validation
    PERFORM crm.validate_lead_status(v_pk);

    -- Update
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_by = auth_user_id,  -- ✅ NEW
        updated_at = now()
    WHERE pk_contact = v_pk;

    -- Notification (pass auth context)
    PERFORM crm.notify_owner(
        p_contact_id,
        'Contact qualified',
        auth_user_id  -- ✅ Pass context
    );

    RETURN jsonb_build_object('success', true);
END;
$$ LANGUAGE plpgsql;
```

---

## 📁 Files to Modify

```
src/generators/actions/
├── action_compiler.py       # Update function templates
├── step_generators/
│   ├── update_step.py      # Use auth_user_id in UPDATE statements
│   ├── insert_step.py      # Use auth_user_id for created_by
│   └── call_step.py        # Pass auth context to called functions
```

---

## 🧪 Tests Required

```python
# tests/unit/actions/test_action_compiler.py

def test_compiled_action_uses_auth_context():
    """Compiled actions should use auth_* parameters"""
    action = Action(name='qualify_lead', steps=[...])
    sql = ActionCompiler().compile(action)

    assert 'auth_tenant_id TEXT' in sql
    assert 'auth_user_id UUID' in sql
    assert 'input_tenant_id' not in sql  # OLD naming
    assert 'input_user_id' not in sql    # OLD naming


def test_update_step_sets_auth_user():
    """UPDATE steps should set updated_by = auth_user_id"""
    step = UpdateStep(target='Contact', fields={'status': 'qualified'})
    sql = UpdateStepGenerator().generate(step)

    assert 'updated_by = auth_user_id' in sql
    assert 'updated_at = now()' in sql


def test_insert_step_sets_created_by():
    """INSERT steps should set created_by = auth_user_id"""
    step = InsertStep(
        target='Contact',
        fields={'email': 'test@example.com'}
    )
    sql = InsertStepGenerator().generate(step)

    assert 'created_by' in sql
    assert 'auth_user_id' in sql


def test_call_step_passes_auth_context():
    """Function calls should pass auth context through"""
    step = CallStep(function='notify_owner', args=[...])
    sql = CallStepGenerator().generate(step)

    # Should pass auth params to called function
    assert 'auth_tenant_id' in sql or 'auth_user_id' in sql
```

---

## ✅ Acceptance Criteria

- [ ] Compiled action functions use `auth_tenant_id` / `auth_user_id` parameters
- [ ] UPDATE steps set `updated_by = auth_user_id`
- [ ] INSERT steps set `created_by = auth_user_id`
- [ ] Function calls pass auth context to sub-functions
- [ ] All tests pass with new naming
- [ ] No references to old `input_*` naming

---

## 🔄 TDD Workflow

### RED Phase
```bash
# Write failing tests
vim tests/unit/actions/test_action_compiler.py
uv run pytest tests/unit/actions/test_action_compiler.py -v
# Expected: FAIL
```

### GREEN Phase
```bash
# Update action compiler
vim src/generators/actions/action_compiler.py
vim src/generators/actions/step_generators/update_step.py

uv run pytest tests/unit/actions/test_action_compiler.py -v
# Expected: PASS
```

### REFACTOR Phase
```bash
# Clean up step generators
# Ensure consistency across all step types

uv run pytest tests/unit/actions/ -v
# All tests pass
```

### QA Phase
```bash
# Full action compiler tests
make teamC-test

# Integration check
make test
```

---

## 🎯 Step-by-Step Implementation

### Step 1: Update Function Template
```python
# src/generators/actions/action_compiler.py

FUNCTION_TEMPLATE = """
CREATE OR REPLACE FUNCTION {schema}.{name}(
    {business_params},
    auth_tenant_id TEXT DEFAULT NULL,  -- ✅ NEW
    auth_user_id UUID DEFAULT NULL     -- ✅ NEW
)
RETURNS jsonb AS $$
{body}
$$ LANGUAGE plpgsql;
"""
```

### Step 2: Update UPDATE Step Generator
```python
# src/generators/actions/step_generators/update_step.py

def generate_update(step, entity):
    """Generate UPDATE statement with audit fields"""
    return f"""
    UPDATE {entity.schema}.tb_{entity.name.lower()}
    SET {', '.join(step.field_assignments)},
        updated_by = auth_user_id,  -- ✅ AUTO
        updated_at = now()          -- ✅ AUTO
    WHERE {step.condition};
    """
```

### Step 3: Update INSERT Step Generator
```python
# src/generators/actions/step_generators/insert_step.py

def generate_insert(step, entity):
    """Generate INSERT statement with audit fields"""
    fields = step.fields + ['created_by', 'created_at']
    values = step.values + ['auth_user_id', 'now()']

    return f"""
    INSERT INTO {entity.schema}.tb_{entity.name.lower()} (
        {', '.join(fields)}
    ) VALUES (
        {', '.join(values)}
    );
    """
```

---

## 🔗 Coordination with Team B

**Team B generates helper functions** → Team C calls them

**Ensure consistency**:
```sql
-- Team B generates:
CREATE FUNCTION schema.helper(p_id UUID, auth_tenant_id TEXT, auth_user_id UUID)

-- Team C calls with correct params:
PERFORM schema.helper(p_id, auth_tenant_id, auth_user_id);
```

**Meeting point**: Both teams use same parameter names and order.

---

## 🎯 Why This Change?

**Consistency**: Match Team B's schema generator naming
**Security**: Clear that these params come from authentication
**Future-proof**: Works with any auth method (JWT, API keys, OAuth, etc.)

---

**Timeline**: Implement by end of Week 2, Day 4
**Dependency**: Coordinate with Team B for consistency
**Next**: Team D will add FraiseQL metadata for these params
