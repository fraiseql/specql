# Team Prompts: Authentication Context Naming Standardization

**Issue**: Rename `input_tenant_id` / `input_user_id` → `auth_tenant_id` / `auth_user_id`

**Reason**: Future-proof naming that works with JWT, API keys, OAuth, sessions, and other auth methods

---

## 📋 Quick Reference

| Prompt File | Team | Priority | Timeline | Status |
|-------------|------|----------|----------|--------|
| [`team_b_auth_context.md`](./team_b_auth_context.md) | Team B: Schema Generator | 🔴 HIGH | Week 2, Days 1-2 | ⏳ Pending |
| [`team_c_auth_context.md`](./team_c_auth_context.md) | Team C: Action Compiler | 🔴 HIGH | Week 2, Days 3-4 | ⏳ Pending |
| [`team_d_auth_context.md`](./team_d_auth_context.md) | Team D: FraiseQL Metadata | 🔴 HIGH | Week 2, Day 5 | ⏳ Pending |
| [`team_e_auth_context.md`](./team_e_auth_context.md) | Team E: Documentation | 🟡 MEDIUM | Week 3, Day 3 | ⏳ Pending |
| [`auth_context_naming.md`](./auth_context_naming.md) | All Teams (Master) | 🔴 HIGH | Week 2-3 | ⏳ Pending |

**External**: [`/tmp/fraiseql_auth_context_prompt.md`](/tmp/fraiseql_auth_context_prompt.md) - For FraiseQL team coordination

---

## 🎯 The Change

### Before (OLD) ❌
```sql
CREATE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    input_tenant_id TEXT,  -- Ambiguous
    input_user_id UUID     -- Not future-proof
)
```

### After (NEW) ✅
```sql
CREATE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    auth_tenant_id TEXT,   -- Clear: from authentication
    auth_user_id UUID      -- Works with any auth method
)
```

---

## 👥 Team Responsibilities

### 🟢 Team B: Schema Generator (PRIMARY)
**What**: Update function signature templates to use `auth_*`

**Files**:
- `src/generators/schema/schema_generator.py`
- `src/generators/schema/audit_fields.py`

**Key Changes**:
- Function signatures: `auth_tenant_id TEXT`, `auth_user_id UUID`
- Audit fields: `updated_by = auth_user_id`
- Tenant checks: `auth_tenant_id IS NOT NULL`

**Read**: [`team_b_auth_context.md`](./team_b_auth_context.md)

---

### 🟠 Team C: Action Compiler (SECONDARY)
**What**: Ensure compiled actions use `auth_*` params

**Files**:
- `src/generators/actions/action_compiler.py`
- `src/generators/actions/step_generators/update_step.py`
- `src/generators/actions/step_generators/insert_step.py`

**Key Changes**:
- Function templates: `auth_tenant_id`, `auth_user_id`
- UPDATE steps: `SET updated_by = auth_user_id`
- INSERT steps: `created_by = auth_user_id`

**Read**: [`team_c_auth_context.md`](./team_c_auth_context.md)

---

### 🟣 Team D: FraiseQL Metadata (TERTIARY)
**What**: Mark auth params as context parameters in metadata

**Files**:
- `src/generators/fraiseql/annotator.py`
- `src/generators/fraiseql/metadata_builder.py`

**Key Changes**:
- Auto-detect `auth_tenant_id` / `auth_user_id`
- Add `context_params=["auth_tenant_id", "auth_user_id"]` to metadata
- Ensure FraiseQL excludes these from GraphQL input

**Read**: [`team_d_auth_context.md`](./team_d_auth_context.md)

---

### 🔴 Team E: Documentation (FINAL)
**What**: Update docs and examples

**Files**:
- `docs/guides/authentication.md` (NEW)
- `docs/guides/function_reference.md` (UPDATE)
- `entities/examples/*.yaml` (UPDATE comments)

**Key Changes**:
- Comprehensive auth context guide
- Security explanation (why not in GraphQL input)
- Updated examples showing `auth_*` usage

**Read**: [`team_e_auth_context.md`](./team_e_auth_context.md)

---

## 🔗 External Coordination

### FraiseQL Team
**Issue**: FraiseQL needs to support `context_params` metadata

**What They Need to Do**:
1. Parse `context_params` from function metadata
2. Exclude those params from GraphQL input schema
3. Inject from GraphQL resolver context (JWT claims)

**Prompt for Them**: `/tmp/fraiseql_auth_context_prompt.md`

**Our Integration Point**: Team D generates the metadata they'll consume

---

## 📅 Implementation Timeline

### Week 2 (Parallel Development)
| Day | Team | Milestone |
|-----|------|-----------|
| 1-2 | Team B | Schema generator uses `auth_*` |
| 3-4 | Team C | Action compiler uses `auth_*` |
| 5 | Team D | Metadata includes `context_params` |

### Week 3 (Integration & Docs)
| Day | Team | Milestone |
|-----|------|-----------|
| 1-2 | All | Integration testing |
| 3 | Team E | Documentation complete |
| 4-5 | All | End-to-end validation |

### Week 5-6 (External)
| Week | Team | Milestone |
|------|------|-----------|
| 5 | FraiseQL | Implement `context_params` support |
| 6 | All | Joint integration testing |

---

## ✅ Overall Acceptance Criteria

- [ ] **Team B**: All generated functions use `auth_*` parameters
- [ ] **Team C**: Compiled actions use `auth_*` parameters
- [ ] **Team D**: Metadata includes `context_params` for auth params
- [ ] **Team E**: Documentation updated, examples corrected
- [ ] **Integration**: End-to-end test passes (SpecQL → SQL → metadata)
- [ ] **External**: FraiseQL integration tested (requires their implementation)
- [ ] **Security**: No references to old `input_*` naming anywhere

---

## 🧪 Integration Test

```python
# tests/integration/test_auth_context_flow.py

def test_end_to_end_auth_context():
    """SpecQL → SQL → Metadata should use auth_* throughout"""

    # Parse SpecQL
    entity = SpecQLParser().parse('entities/examples/contact.yaml')

    # Team B: Generate schema
    schema_sql = SchemaGenerator().generate(entity)
    assert 'auth_tenant_id TEXT' in schema_sql
    assert 'auth_user_id UUID' in schema_sql
    assert 'input_tenant_id' not in schema_sql  # OLD

    # Team C: Compile actions
    action_sql = ActionCompiler().compile(entity.actions)
    assert 'auth_tenant_id' in action_sql
    assert 'updated_by = auth_user_id' in action_sql
    assert 'input_user_id' not in action_sql  # OLD

    # Team D: Generate metadata
    metadata_sql = FraiseQLAnnotator().annotate(entity)
    assert 'context_params' in metadata_sql
    assert 'auth_tenant_id' in metadata_sql

    # Full migration should be clean
    migration = combine(schema_sql, action_sql, metadata_sql)
    assert 'input_tenant_id' not in migration
    assert 'input_user_id' not in migration
```

---

## 📚 Why This Change?

### Problem with `input_*`
- ❌ Ambiguous: "input" could mean many things
- ❌ Not future-proof: What if auth method changes?
- ❌ Security unclear: Doesn't signal trusted source

### Solution with `auth_*`
- ✅ Clear: "from authentication system"
- ✅ Future-proof: Works with JWT, API keys, OAuth, sessions, mTLS
- ✅ Security: Signals server-controlled, trusted values
- ✅ Industry standard: Common naming pattern

### Security Impact
**Critical**: These parameters must NEVER be client-controlled!

```graphql
# ❌ SECURITY VULNERABILITY if exposed
input QualifyLeadInput {
  authTenantId: String  # Client can fake tenant!
  authUserId: UUID      # Client can impersonate users!
}
```

**Solution**: Mark as `context_params` so FraiseQL excludes from input schema and injects from server context.

---

## 🎯 Quick Start for Each Team

### If you're working on Team B
```bash
cd /home/lionel/code/printoptim_backend_poc
cat .claude/prompts/team_b_auth_context.md
# Follow TDD workflow: RED → GREEN → REFACTOR → QA
```

### If you're working on Team C
```bash
cat .claude/prompts/team_c_auth_context.md
# Coordinate with Team B for consistency
```

### If you're working on Team D
```bash
cat .claude/prompts/team_d_auth_context.md
# Read /tmp/fraiseql_auth_context_prompt.md for integration requirements
```

### If you're working on Team E
```bash
cat .claude/prompts/team_e_auth_context.md
# Wait for Teams B, C, D to complete implementation first
```

---

## 📞 Questions?

**Naming**: Why `auth_*` instead of `jwt_*` or `caller_*`?
- See decision rationale in [`auth_context_naming.md`](./auth_context_naming.md)

**Security**: Why can't clients set these?
- See Team E's documentation guide for explanation

**FraiseQL**: What if they don't support `context_params`?
- See `/tmp/fraiseql_auth_context_prompt.md` for coordination plan

**Testing**: How do we validate this works?
- See integration test in master prompt

---

**Created**: 2025-11-08
**Status**: Ready for implementation
**Impact**: All teams (B, C, D, E) + external (FraiseQL)
