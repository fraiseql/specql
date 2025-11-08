# Team B: Schema Generator - Authentication Context Implementation

**Extracted from**: `auth_context_naming.md`
**Priority**: 🔴 HIGH
**Timeline**: Week 2, Days 1-2

---

## 🎯 Mission

Update PostgreSQL function generation to use `auth_tenant_id` / `auth_user_id` instead of `input_tenant_id` / `input_user_id`.

---

## 📋 Changes Required

### 1. Function Signature Generation
**When generating PL/pgSQL functions, use:**
```sql
auth_tenant_id TEXT DEFAULT NULL
auth_user_id UUID DEFAULT NULL
```

**NOT:**
```sql
input_tenant_id TEXT DEFAULT NULL  -- ❌ OLD
input_user_id UUID DEFAULT NULL    -- ❌ OLD
```

### 2. Audit Field Updates
**Use `auth_user_id` when setting audit fields:**
```sql
UPDATE schema.tb_entity
SET created_by = auth_user_id,    -- ✅ NEW
    updated_by = auth_user_id,    -- ✅ NEW
    updated_at = now()
WHERE ...
```

### 3. Tenant Isolation Logic
**Use `auth_tenant_id` for tenant checks:**
```sql
IF auth_tenant_id IS NOT NULL THEN
    PERFORM schema.check_tenant_access(p_entity_id, auth_tenant_id);
END IF;
```

---

## 📝 Example Transformation

### Before (OLD)
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    input_tenant_id TEXT DEFAULT NULL,
    input_user_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
BEGIN
    IF input_tenant_id IS NOT NULL THEN
        -- Check tenant access
    END IF;

    UPDATE crm.tb_contact
    SET updated_by = input_user_id,
        updated_at = now()
    WHERE pk_contact = v_pk;
END;
$$ LANGUAGE plpgsql;
```

### After (NEW)
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    auth_tenant_id TEXT DEFAULT NULL,
    auth_user_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
BEGIN
    IF auth_tenant_id IS NOT NULL THEN
        -- Check tenant access
    END IF;

    UPDATE crm.tb_contact
    SET updated_by = auth_user_id,
        updated_at = now()
    WHERE pk_contact = v_pk;
END;
$$ LANGUAGE plpgsql;
```

---

## 📁 Files to Modify

```
src/generators/schema/
├── schema_generator.py     # Update function signature templates
├── audit_fields.py         # Use auth_user_id for created_by/updated_by
└── tenant_isolation.py     # Use auth_tenant_id for RLS/filtering
```

---

## 🧪 Tests Required

```python
# tests/unit/schema/test_function_generation.py

def test_function_signature_uses_auth_context():
    """Function signatures should use auth_tenant_id and auth_user_id"""
    entity = Entity(name='Contact', ...)
    sql = SchemaGenerator().generate_action_function(entity)

    assert 'auth_tenant_id TEXT' in sql
    assert 'auth_user_id UUID' in sql
    assert 'input_tenant_id' not in sql  # OLD naming
    assert 'input_user_id' not in sql    # OLD naming


def test_audit_fields_use_auth_user_id():
    """Audit trail should reference auth_user_id"""
    entity = Entity(name='Contact', ...)
    sql = SchemaGenerator().generate_action_function(entity)

    assert 'updated_by = auth_user_id' in sql
    assert 'created_by = auth_user_id' in sql


def test_tenant_isolation_uses_auth_tenant_id():
    """Tenant checks should reference auth_tenant_id"""
    entity = Entity(name='Contact', ...)
    sql = SchemaGenerator().generate_action_function(entity)

    assert 'auth_tenant_id IS NOT NULL' in sql
    # Should NOT reference old naming
    assert 'input_tenant_id' not in sql
```

---

## ✅ Acceptance Criteria

- [ ] All generated functions use `auth_tenant_id` / `auth_user_id`
- [ ] Audit fields (`created_by`, `updated_by`) reference `auth_user_id`
- [ ] Tenant isolation logic uses `auth_tenant_id`
- [ ] All tests pass with new naming
- [ ] No references to old `input_tenant_id` / `input_user_id` in generated SQL

---

## 🔄 TDD Workflow

### RED Phase
```bash
# Write failing tests first
vim tests/unit/schema/test_function_generation.py
uv run pytest tests/unit/schema/test_function_generation.py -v
# Expected: FAIL (tests check for auth_* but code generates input_*)
```

### GREEN Phase
```bash
# Update schema generator
vim src/generators/schema/schema_generator.py
# Change input_tenant_id → auth_tenant_id
# Change input_user_id → auth_user_id

uv run pytest tests/unit/schema/test_function_generation.py -v
# Expected: PASS
```

### REFACTOR Phase
```bash
# Clean up any code duplication
# Ensure consistency across all function types

uv run pytest tests/unit/schema/ -v
# All tests still pass
```

### QA Phase
```bash
# Full test suite
make teamB-test

# Integration check
make test
```

---

## 🎯 Why This Change?

**Old naming** (`input_*`):
- ❌ Ambiguous source (could be from anywhere)
- ❌ Not future-proof for multiple auth methods
- ❌ Doesn't signal security boundary

**New naming** (`auth_*`):
- ✅ Clear: "from authentication system"
- ✅ Future-proof: Works with JWT, API keys, OAuth, sessions
- ✅ Security: Signals these are trusted values

---

**Timeline**: Implement by end of Week 2, Day 2
**Next**: Coordinate with Team C (action compiler) for consistency
