# Team D: FraiseQL Metadata - Authentication Context Implementation

**Extracted from**: `auth_context_naming.md`
**Priority**: 🔴 HIGH
**Timeline**: Week 2, Day 5

---

## 🎯 Mission

Generate FraiseQL metadata that marks `auth_tenant_id` / `auth_user_id` as context parameters, ensuring they're excluded from GraphQL input schemas.

---

## 📋 The Problem

Without proper metadata, FraiseQL might expose auth params in GraphQL:

```graphql
# ❌ BAD - Security issue!
input QualifyLeadInput {
  contactId: UUID!
  authTenantId: String!  # ❌ Client can fake tenant!
  authUserId: UUID!      # ❌ Client can impersonate users!
}
```

We need to mark these as **context parameters** so FraiseQL excludes them.

---

## 📋 The Solution: `context_params` Metadata

### New Metadata Format

```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead,
   input=QualifyLeadInput,
   output=Contact,
   context_params=["auth_tenant_id", "auth_user_id"]';
```

**Effect**: FraiseQL will:
1. ✅ Exclude `auth_tenant_id` / `auth_user_id` from GraphQL input schema
2. ✅ Inject these from GraphQL resolver context (JWT claims)
3. ✅ Pass to PostgreSQL function automatically

---

## 📝 Implementation

### Auto-Detection Logic

```python
# src/generators/fraiseql/annotator.py

def generate_function_metadata(function_def):
    """Generate FraiseQL metadata for a function."""

    # Auto-detect context parameters
    context_params = []
    for param in function_def.parameters:
        if param.name in ['auth_tenant_id', 'auth_user_id']:
            context_params.append(param.name)

    # Build metadata parts
    metadata_parts = [
        f'name={to_camel_case(function_def.name)}',
        f'input={function_def.input_type}',
        f'output={function_def.output_type}',
    ]

    # Add context_params if any
    if context_params:
        params_json = json.dumps(context_params)
        metadata_parts.append(f'context_params={params_json}')

    # Combine into metadata comment
    metadata = '@fraiseql:mutation ' + ','.join(metadata_parts)
    return f"COMMENT ON FUNCTION {function_def.signature} IS '{metadata}';"
```

---

## 📝 Examples

### Example 1: Function with Both Auth Params

**PostgreSQL Function**:
```sql
CREATE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    auth_tenant_id TEXT,
    auth_user_id UUID
)
RETURNS jsonb AS $$...$$;
```

**Generated Metadata**:
```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead,
   input=QualifyLeadInput,
   output=Contact,
   context_params=["auth_tenant_id", "auth_user_id"]';
```

**Expected GraphQL** (by FraiseQL):
```graphql
input QualifyLeadInput {
  contactId: UUID!
  # NO auth params here
}
```

---

### Example 2: Function with Only User ID

**PostgreSQL Function**:
```sql
CREATE FUNCTION crm.create_contact(
    p_email TEXT,
    p_company_id UUID,
    auth_user_id UUID
)
RETURNS jsonb AS $$...$$;
```

**Generated Metadata**:
```sql
COMMENT ON FUNCTION crm.create_contact IS
  '@fraiseql:mutation
   name=createContact,
   input=CreateContactInput,
   output=Contact,
   context_params=["auth_user_id"]';
```

**Expected GraphQL** (by FraiseQL):
```graphql
input CreateContactInput {
  email: String!
  companyId: UUID!
  # auth_user_id excluded
}
```

---

### Example 3: Function Without Auth Context

**PostgreSQL Function**:
```sql
CREATE FUNCTION public.get_status()
RETURNS jsonb AS $$...$$;
```

**Generated Metadata**:
```sql
COMMENT ON FUNCTION public.get_status IS
  '@fraiseql:query name=status,output=Status';
-- No context_params (no auth params in function)
```

---

## 📁 Files to Modify

```
src/generators/fraiseql/
├── annotator.py          # Main: Add context_params detection
└── metadata_builder.py   # Helper: Build metadata with context_params
```

---

## 🧪 Tests Required

```python
# tests/unit/fraiseql/test_metadata_generation.py

def test_auth_params_listed_as_context_params():
    """Auth parameters should be listed in context_params metadata"""
    function_def = FunctionDef(
        name='qualify_lead',
        parameters=[
            Param('p_contact_id', 'UUID'),
            Param('auth_tenant_id', 'TEXT'),
            Param('auth_user_id', 'UUID'),
        ]
    )
    metadata = FraiseQLAnnotator().generate_function_metadata(function_def)

    # Should include context_params array
    assert 'context_params' in metadata
    assert 'auth_tenant_id' in metadata
    assert 'auth_user_id' in metadata
    # JSON array format
    assert '["auth_tenant_id","auth_user_id"]' in metadata or \
           '["auth_tenant_id", "auth_user_id"]' in metadata


def test_only_auth_params_in_context_params():
    """Business parameters should NOT be in context_params"""
    function_def = FunctionDef(
        name='create_contact',
        parameters=[
            Param('p_email', 'TEXT'),
            Param('p_company_id', 'UUID'),
            Param('auth_user_id', 'UUID'),
        ]
    )
    metadata = FraiseQLAnnotator().generate_function_metadata(function_def)

    # Only auth_user_id in context_params
    assert 'context_params=["auth_user_id"]' in metadata

    # Verify p_email and p_company_id NOT in context_params
    # (they might appear elsewhere in metadata, just not in context_params array)
    import re
    context_params_match = re.search(r'context_params=(\[.*?\])', metadata)
    if context_params_match:
        context_params_str = context_params_match.group(1)
        assert 'p_email' not in context_params_str
        assert 'p_company_id' not in context_params_str


def test_function_without_auth_has_no_context_params():
    """Functions without auth context should have no context_params"""
    function_def = FunctionDef(
        name='get_contact',
        parameters=[
            Param('p_contact_id', 'UUID'),
        ]
    )
    metadata = FraiseQLAnnotator().generate_function_metadata(function_def)

    # Should NOT have context_params
    assert 'context_params' not in metadata


def test_metadata_json_format_valid():
    """context_params should be valid JSON array"""
    function_def = FunctionDef(
        name='test_func',
        parameters=[
            Param('auth_tenant_id', 'TEXT'),
        ]
    )
    metadata = FraiseQLAnnotator().generate_function_metadata(function_def)

    # Extract context_params value
    import re
    match = re.search(r'context_params=(\[.*?\])', metadata)
    assert match, "context_params should be present"

    # Should be valid JSON
    import json
    params = json.loads(match.group(1))
    assert params == ['auth_tenant_id']
```

---

## ✅ Acceptance Criteria

- [ ] Metadata includes `context_params` for functions with auth context
- [ ] Only `auth_tenant_id` / `auth_user_id` are listed in `context_params`
- [ ] Business parameters are NOT in `context_params`
- [ ] Functions without auth context have no `context_params`
- [ ] `context_params` value is valid JSON array
- [ ] All tests pass

---

## 🔄 TDD Workflow

### RED Phase
```bash
# Write failing tests
vim tests/unit/fraiseql/test_metadata_generation.py
uv run pytest tests/unit/fraiseql/test_metadata_generation.py -v
# Expected: FAIL (context_params not yet generated)
```

### GREEN Phase
```bash
# Implement context_params detection
vim src/generators/fraiseql/annotator.py

uv run pytest tests/unit/fraiseql/test_metadata_generation.py -v
# Expected: PASS
```

### REFACTOR Phase
```bash
# Clean up metadata builder
# Ensure proper JSON formatting
# Handle edge cases (no params, mixed params, etc.)

uv run pytest tests/unit/fraiseql/ -v
# All tests pass
```

### QA Phase
```bash
# Full Team D tests
make teamD-test

# Integration check
make test
```

---

## 🔗 Integration with FraiseQL

### What You Generate
```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation context_params=["auth_tenant_id","auth_user_id"]';
```

### What FraiseQL Should Do
1. Parse `context_params` from metadata
2. Exclude those params from GraphQL input schema
3. Inject from GraphQL resolver context
4. Pass to PostgreSQL function

**See**: `/tmp/fraiseql_auth_context_prompt.md` for FraiseQL team coordination

---

## 🎯 Parameter Detection Rules

```python
# Context parameter detection
AUTH_CONTEXT_PARAMS = ['auth_tenant_id', 'auth_user_id']

def is_context_param(param_name: str) -> bool:
    """Check if parameter is an auth context parameter"""
    return param_name in AUTH_CONTEXT_PARAMS
```

**Future extensibility**: If we add more context params (e.g., `auth_session_id`), just add to this list.

---

## 🔒 Security Impact

**Critical**: This metadata prevents security vulnerabilities!

**Without `context_params`**:
- ❌ Client can set `auth_tenant_id` → tenant isolation bypass
- ❌ Client can set `auth_user_id` → audit trail poisoning

**With `context_params`**:
- ✅ FraiseQL excludes from GraphQL input
- ✅ FraiseQL injects from JWT (trusted source)
- ✅ Client cannot override auth context

---

## 📊 Metadata Format Reference

### Full Metadata Example
```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead,
   input=QualifyLeadInput,
   output=Contact,
   context_params=["auth_tenant_id", "auth_user_id"]';
```

### Breakdown
- `@fraiseql:mutation` - FraiseQL directive type
- `name=qualifyLead` - GraphQL mutation name (camelCase)
- `input=QualifyLeadInput` - GraphQL input type name
- `output=Contact` - GraphQL output type name
- `context_params=[...]` - **NEW**: Auth context parameters

---

**Timeline**: Implement by end of Week 2, Day 5
**Dependency**: Requires Teams B & C to generate functions with `auth_*` params
**Next**: Coordinate with FraiseQL team (see `/tmp/fraiseql_auth_context_prompt.md`)
