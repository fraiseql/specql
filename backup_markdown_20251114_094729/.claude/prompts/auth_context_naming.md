# Team Prompt: Standardize Authentication Context Parameter Naming

**Issue**: Current `input_tenant_id` / `input_user_id` naming is ambiguous and not future-proof for multiple authentication methods.

**Decision**: Adopt `auth_tenant_id` / `auth_user_id` convention across all generated code.

---

## 🎯 Objective

Standardize authentication context parameter naming to:
1. ✅ Be authentication-method agnostic (JWT, API keys, OAuth, sessions, etc.)
2. ✅ Clearly signal these are trusted, authenticated values
3. ✅ Maintain consistency across all generated artifacts
4. ✅ Support future authentication methods without renaming

---

## 📋 Naming Convention

### **ADOPT** (New Standard)
```sql
auth_tenant_id TEXT    -- Authenticated tenant context
auth_user_id UUID      -- Authenticated user context
```

### **REPLACE** (Old Convention)
```sql
input_tenant_id TEXT   -- Too generic, ambiguous source
input_user_id UUID
```

### **Rationale**
- `auth_` prefix signals "from authentication system" (not user input)
- Works with any auth method: JWT, API keys, OAuth, mTLS, sessions
- Industry-standard naming pattern
- Clear security boundary

---

## 👥 Team Responsibilities

### 🟢 **Team B: Schema Generator** (PRIMARY)

**Scope**: Generate PostgreSQL functions with correct parameter names

#### Changes Required

1. **Function Signature Generation**
   - When generating PL/pgSQL functions, use `auth_tenant_id` / `auth_user_id`
   - Apply to ALL generated functions (actions, helpers, etc.)

2. **Audit Field Updates**
   - Use `auth_user_id` when setting `created_by` / `updated_by`
   - Use `auth_tenant_id` for tenant isolation logic

#### Example Transformation

**Before** (OLD):
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    input_tenant_id TEXT DEFAULT NULL,
    input_user_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
BEGIN
    -- Tenant isolation
    IF input_tenant_id IS NOT NULL THEN
        -- Check tenant access
    END IF;

    -- Audit trail
    UPDATE crm.tb_contact
    SET updated_by = input_user_id,
        updated_at = now()
    WHERE pk_contact = v_pk;
END;
$$ LANGUAGE plpgsql;
```

**After** (NEW):
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    auth_tenant_id TEXT DEFAULT NULL,
    auth_user_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
BEGIN
    -- Tenant isolation
    IF auth_tenant_id IS NOT NULL THEN
        -- Check tenant access
    END IF;

    -- Audit trail
    UPDATE crm.tb_contact
    SET updated_by = auth_user_id,
        updated_at = now()
    WHERE pk_contact = v_pk;
END;
$$ LANGUAGE plpgsql;
```

#### Files to Modify

```
src/generators/schema/
├── schema_generator.py     # Update function signature templates
├── audit_fields.py         # Use auth_user_id for created_by/updated_by
└── tenant_isolation.py     # Use auth_tenant_id for RLS/filtering
```

#### Test Updates

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
```

---

### 🟠 **Team C: Action Compiler** (SECONDARY)

**Scope**: Compile SpecQL action steps to PL/pgSQL, ensuring auth context is used correctly

#### Changes Required

1. **Function Generation**
   - All compiled action functions use `auth_tenant_id` / `auth_user_id` parameters
   - Pass these through to any called sub-functions

2. **Audit Step Handling**
   - When action includes audit steps, use `auth_user_id` for tracking

#### Example

**SpecQL Input**:
```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

**Generated Function** (ensure uses `auth_*`):
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    auth_tenant_id TEXT DEFAULT NULL,  -- ✅ Correct naming
    auth_user_id UUID DEFAULT NULL     -- ✅ Correct naming
)
RETURNS jsonb AS $$
DECLARE
    v_pk INTEGER;
BEGIN
    -- Tenant check
    IF auth_tenant_id IS NOT NULL THEN
        PERFORM crm.check_tenant_access(p_contact_id, auth_tenant_id);
    END IF;

    -- Action logic...
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_by = auth_user_id,  -- ✅ Use auth_user_id
        updated_at = now()
    WHERE pk_contact = v_pk;

    RETURN jsonb_build_object('success', true);
END;
$$ LANGUAGE plpgsql;
```

#### Files to Modify

```
src/generators/actions/
├── action_compiler.py       # Update function templates
├── step_generators/
│   ├── update_step.py      # Use auth_user_id in UPDATE statements
│   └── insert_step.py      # Use auth_user_id for created_by
```

#### Test Updates

```python
# tests/unit/actions/test_action_compiler.py

def test_compiled_action_uses_auth_context():
    """Compiled actions should use auth_* parameters"""
    action = Action(name='qualify_lead', steps=[...])
    sql = ActionCompiler().compile(action)

    assert 'auth_tenant_id TEXT' in sql
    assert 'auth_user_id UUID' in sql
    assert 'input_' not in sql  # No old naming

def test_update_step_sets_auth_user():
    """UPDATE steps should set updated_by = auth_user_id"""
    step = UpdateStep(target='Contact', fields={'status': 'qualified'})
    sql = StepGenerator().generate(step)

    assert 'updated_by = auth_user_id' in sql
```

---

### 🟣 **Team D: FraiseQL Metadata Generator** (TERTIARY)

**Scope**: Ensure GraphQL metadata correctly documents authentication parameters

#### Changes Required

1. **Function Metadata Comments**
   - Document `auth_tenant_id` / `auth_user_id` in `@fraiseql:mutation` comments
   - Explicitly list these as `context_params` so FraiseQL excludes them from GraphQL input schema
   - Map to GraphQL context (not input arguments)

2. **Metadata Format**
   - Use `context_params` array to specify which parameters come from authentication context
   - These params should NEVER appear in GraphQL mutation input types

#### Example

```sql
-- Function with auth context
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    auth_tenant_id TEXT DEFAULT NULL,
    auth_user_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
-- ...
$$ LANGUAGE plpgsql;

-- Metadata annotation (NEW FORMAT)
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead,
   input=QualifyLeadInput,
   output=Contact,
   context_params=["auth_tenant_id", "auth_user_id"]';
```

**Why `context_params`**:
- Explicit contract with FraiseQL: "These params come from resolver context"
- Security: Prevents client from setting auth context
- Future-proof: Works with any auth method (JWT, API keys, OAuth, etc.)

#### Auto-Detection Logic

When generating metadata, automatically detect auth params:

```python
# src/generators/fraiseql/annotator.py

def generate_function_metadata(function_def):
    """Generate FraiseQL metadata for a function."""

    # Auto-detect context parameters
    context_params = []
    for param in function_def.parameters:
        if param.name in ['auth_tenant_id', 'auth_user_id']:
            context_params.append(param.name)

    # Build metadata
    metadata_parts = [
        f'name={to_camel_case(function_def.name)}',
        f'input={function_def.input_type}',
        f'output={function_def.output_type}',
    ]

    if context_params:
        # Add context_params to metadata
        metadata_parts.append(f'context_params={json.dumps(context_params)}')

    metadata = '@fraiseql:mutation ' + ','.join(metadata_parts)
    return f"COMMENT ON FUNCTION {function_def.signature} IS '{metadata}';"
```

#### FraiseQL Mapping

When FraiseQL introspects the function:
- `p_contact_id` → GraphQL input argument `contactId`
- `auth_tenant_id` → **Excluded** from GraphQL input (comes from context)
- `auth_user_id` → **Excluded** from GraphQL input (comes from context)

**GraphQL Mutation** (Generated by FraiseQL):
```graphql
# Input type (NO auth params - they're in context_params)
input QualifyLeadInput {
  contactId: UUID!
  # auth_tenant_id NOT here - injected from context
  # auth_user_id NOT here - injected from context
}

# Mutation
mutation {
  qualifyLead(
    contactId: "uuid-here"
    # auth context populated by FraiseQL resolver from JWT
  ) {
    success
    contact { id, status }
  }
}
```

**FraiseQL Resolver** (What FraiseQL does):
```javascript
// FraiseQL auto-generated resolver
async function qualifyLead(parent, args, context, info) {
  // Extract auth from context (JWT claims)
  const { tenantId, userId } = context.auth;

  // Call PostgreSQL function with context params
  return db.query(
    'SELECT crm.qualify_lead($1, $2, $3)',
    [
      args.contactId,        // From GraphQL input
      tenantId,              // From JWT context
      userId                 // From JWT context
    ]
  );
}
```

#### Files to Modify

```
src/generators/fraiseql/
├── annotator.py          # Add context_params detection
└── metadata_builder.py   # Build metadata with context_params array
```

#### Test Updates

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
    assert 'context_params=["auth_tenant_id","auth_user_id"]' in metadata
    # Or with spaces (JSON format)
    assert 'context_params' in metadata
    assert 'auth_tenant_id' in metadata
    assert 'auth_user_id' in metadata


def test_non_auth_params_not_in_context_params():
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
    # p_email and p_company_id should NOT be in context_params
    assert 'p_email' not in metadata.split('context_params')[1] if 'context_params' in metadata else True


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
```

#### Integration with FraiseQL

**Contract**: This project generates metadata, FraiseQL consumes it.

**What Team D provides** (in PostgreSQL):
```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation context_params=["auth_tenant_id","auth_user_id"]';
```

**What FraiseQL should do** (external tool):
1. Parse `context_params` from metadata
2. Exclude those params from GraphQL input schema
3. Inject values from GraphQL resolver context (JWT claims)
4. Pass to PostgreSQL function

**See**: `/tmp/fraiseql_auth_context_prompt.md` for FraiseQL team coordination

---

### 🔴 **Team E: CLI & Orchestration** (DOCUMENTATION)

**Scope**: Update documentation and examples

#### Changes Required

1. **Example Entities**
   - Update all example YAML → SQL outputs to show `auth_*` naming
   - Update CLI help text / error messages

2. **User Documentation**
   - Document that generated functions receive `auth_tenant_id` / `auth_user_id` automatically
   - Explain these come from authentication context (JWT claims, etc.)

#### Example Documentation

**File**: `docs/guides/authentication.md`

```markdown
# Authentication Context

All generated PostgreSQL functions automatically receive authentication context:

## Standard Parameters

```sql
CREATE FUNCTION schema.action_name(
    -- Business parameters (from GraphQL input)
    p_entity_id UUID,

    -- Authentication context (auto-injected)
    auth_tenant_id TEXT DEFAULT NULL,
    auth_user_id UUID DEFAULT NULL
)
```

## How It Works

1. **Client Request**: GraphQL mutation with business parameters only
2. **FraiseQL Resolver**: Extracts JWT claims (`tenant_id`, `user_id`)
3. **Function Call**: Passes JWT claims as `auth_tenant_id` / `auth_user_id`
4. **Database Function**: Uses auth context for:
   - Tenant isolation (`auth_tenant_id`)
   - Audit trails (`auth_user_id` → `created_by` / `updated_by`)
   - Authorization checks

## Authentication Methods Supported

The `auth_*` naming is method-agnostic and works with:
- ✅ JWT tokens (most common)
- ✅ API keys
- ✅ OAuth tokens
- ✅ Session-based auth
- ✅ mTLS client certificates

The resolver is responsible for extracting tenant/user IDs from the authentication method and passing to database functions.
```

#### Files to Modify

```
docs/guides/
├── authentication.md        # NEW: Document auth context
└── function_reference.md    # Update function signature examples

entities/examples/
├── contact.yaml            # Update comments showing generated SQL
└── machine_item.yaml       # Update expected output

src/cli/
└── generate.py             # Update help text / output messages
```

---

## ✅ Acceptance Criteria

### For Team B
- [ ] All generated functions use `auth_tenant_id` / `auth_user_id`
- [ ] Audit fields (`created_by`, `updated_by`) reference `auth_user_id`
- [ ] Tenant isolation logic uses `auth_tenant_id`
- [ ] Tests verify correct parameter naming
- [ ] No references to old `input_tenant_id` / `input_user_id`

### For Team C
- [ ] Compiled action functions use `auth_*` parameters
- [ ] UPDATE/INSERT steps set audit fields with `auth_user_id`
- [ ] Tests verify compiled SQL uses correct naming

### For Team D
- [ ] FraiseQL metadata marks auth params as context
- [ ] GraphQL schema excludes auth params from mutation inputs
- [ ] Tests verify auth params don't appear in GraphQL input types

### For Team E
- [ ] Documentation updated with `auth_*` examples
- [ ] Example YAML → SQL outputs show correct naming
- [ ] Help text references authentication context correctly

---

## 🧪 Testing Strategy

### Unit Tests (Each Team)
```bash
make teamB-test  # Schema generator tests
make teamC-test  # Action compiler tests
make teamD-test  # FraiseQL metadata tests
```

### Integration Test (Cross-Team)
```bash
# tests/integration/test_auth_context_flow.py

def test_end_to_end_auth_context():
    """SpecQL → SQL → FraiseQL should use auth_* throughout"""

    # Parse SpecQL
    entity = SpecQLParser().parse('entities/examples/contact.yaml')

    # Generate schema (Team B)
    schema_sql = SchemaGenerator().generate(entity)
    assert 'auth_tenant_id TEXT' in schema_sql
    assert 'auth_user_id UUID' in schema_sql

    # Compile actions (Team C)
    action_sql = ActionCompiler().compile(entity.actions)
    assert 'auth_tenant_id' in action_sql
    assert 'updated_by = auth_user_id' in action_sql

    # Generate FraiseQL metadata (Team D)
    metadata_sql = FraiseQLAnnotator().annotate(entity)
    assert 'auth_context=true' in metadata_sql

    # Full migration should have NO old naming
    migration = combine(schema_sql, action_sql, metadata_sql)
    assert 'input_tenant_id' not in migration
    assert 'input_user_id' not in migration
```

---

## 📅 Implementation Timeline

### Week 2 (Parallel Development)
- **Day 1-2**: Team B implements in schema generator
- **Day 3-4**: Team C implements in action compiler
- **Day 5**: Team D implements metadata generation

### Week 3 (Integration)
- **Day 1-2**: Integration testing across teams
- **Day 3**: Team E updates documentation
- **Day 4-5**: End-to-end validation

---

## 🔍 Migration Notes

**Current Status**: POC/Development (no production deployments)

**Breaking Change**: Yes, changes function signatures

**Migration Path**:
- ✅ Safe to implement now (Week 1-2)
- ⚠️ If any functions already generated, regenerate with new naming
- 📝 Update any hand-written SQL to use `auth_*` convention

---

## 📞 Questions?

**Naming Clarification**:
- `auth_tenant_id` - Authenticated tenant context (from JWT/API key/etc.)
- `auth_user_id` - Authenticated user context (from JWT/API key/etc.)
- These are ALWAYS from trusted authentication sources, never direct user input

**When to Use**:
- ✅ All generated functions (actions, helpers)
- ✅ Audit trail updates (`created_by`, `updated_by`)
- ✅ Tenant isolation logic
- ✅ Authorization checks

**When NOT to Use**:
- ❌ Business entity IDs (use `p_entity_id` for parameters)
- ❌ User-provided input (use descriptive names like `p_email`, `p_status`)

---

**Priority**: 🔴 HIGH (affects all generated SQL)
**Complexity**: 🟢 LOW (simple renaming, clear pattern)
**Impact**: All Teams (B, C, D, E)
**Timeline**: Week 2-3

---

## 🎯 Summary

**Old**: `input_tenant_id` / `input_user_id` (ambiguous, not future-proof)
**New**: `auth_tenant_id` / `auth_user_id` (clear, authentication-method agnostic)

**Why**: Support JWT, API keys, OAuth, and future auth methods without renaming.

**Teams Affected**: B (primary), C (secondary), D (tertiary), E (docs)

**Action Required**: Update function generation templates to use `auth_*` naming consistently.
