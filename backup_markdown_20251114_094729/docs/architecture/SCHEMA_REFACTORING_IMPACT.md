# Schema Refactoring Impact Analysis

**Date**: 2025-11-09
**Context**: Complete list of files affected by schema organization refactoring

---

## Summary

This refactoring moves from **hardcoded schema lists** to **registry-driven schema classification**.

**Key Changes**:
1. Add `multi_tenant` flag to domain registry
2. Create central `SchemaRegistry` class
3. Replace 3+ hardcoded `TENANT_SCHEMAS` lists
4. Fix FK resolver bug (Manufacturer → catalog)
5. Update documentation

---

## Files Requiring Changes

### 🔴 CRITICAL: Core Implementation Files

#### 1. `registry/domain_registry.yaml`
**Change**: Add `multi_tenant` flag to all domains

**Current**:
```yaml
"2":
  name: crm
  aliases: [management]
  description: "CRM"
```

**New**:
```yaml
"2":
  name: crm
  aliases: [management]
  description: "CRM"
  multi_tenant: true  # ← NEW FIELD
```

**Lines to Update**: All domain entries (domains 1-6)

**Effort**: 5 minutes (add one field per domain)

---

#### 2. `src/generators/schema/schema_registry.py` (NEW FILE)
**Change**: Create central schema registry

**Lines**: ~150 lines (new file)

**Effort**: 30 minutes

**Contents**:
- `is_multi_tenant()` - Replace hardcoded lists
- `get_canonical_schema_name()` - Resolve aliases
- `is_framework_schema()` - Check if common/app/core
- `is_shared_reference_schema()` - Check if shared data

---

#### 3. `src/generators/table_generator.py`
**Change**: Replace hardcoded list with registry lookup

**Current** (line 140-148):
```python
def _is_tenant_specific_schema(self, schema: str) -> bool:
    """
    Determine if schema is tenant-specific (needs tenant_id) or common (shared)

    Tenant-specific schemas: tenant, crm, management, operations
    Common schemas: common, catalog, public
    """
    tenant_schemas = ["tenant", "crm", "management", "operations"]
    return schema in tenant_schemas
```

**New**:
```python
def _is_tenant_specific_schema(self, schema: str) -> bool:
    """
    Determine if schema is tenant-specific (needs tenant_id) or common (shared)

    Uses domain registry to check multi_tenant flag
    """
    return self.schema_registry.is_multi_tenant(schema)
```

**Also Add** (in `__init__`):
```python
from src.generators.schema.schema_registry import SchemaRegistry

def __init__(self):
    # ... existing init ...
    self.schema_registry = SchemaRegistry(self.naming_conventions.registry)
```

**Lines to Change**: 2 (replace hardcoded list, add registry init)

**Effort**: 10 minutes

---

#### 4. `src/generators/trinity_helper_generator.py`
**Change**: Replace hardcoded `TENANT_SCHEMAS` constant

**Current** (line 64):
```python
TENANT_SCHEMAS = ["tenant", "crm", "management", "operations"]
```

**Search for Usage**:
```bash
# Find all references to TENANT_SCHEMAS in this file
grep -n "TENANT_SCHEMAS" src/generators/trinity_helper_generator.py
```

**Replacement Pattern**:
```python
# BEFORE
if entity.schema in TENANT_SCHEMAS:
    # Add tenant_id parameter

# AFTER
if self.schema_registry.is_multi_tenant(entity.schema):
    # Add tenant_id parameter
```

**Lines to Change**: ~5-10 (everywhere TENANT_SCHEMAS is used)

**Effort**: 15 minutes

---

#### 5. `src/generators/core_logic_generator.py`
**Change**: Replace hardcoded `TENANT_SCHEMAS` constant

**Current** (line 201):
```python
TENANT_SCHEMAS = ["tenant", "crm", "management", "operations"]
```

**Same replacement pattern as trinity_helper_generator.py**

**Lines to Change**: ~5-10

**Effort**: 15 minutes

---

#### 6. `src/generators/actions/step_compilers/fk_resolver.py`
**Change**: Replace hardcoded schema map with registry lookup

**Current** (line 127):
```python
schema_map = {
    "Contact": "crm",
    "Task": "crm",
    "Manufacturer": "product",  # ← BUG! Should be "catalog"
    "Product": "product",
}
```

**New**:
```python
def _resolve_entity_schema(self, entity_name: str) -> str:
    """
    Resolve entity name to schema name using registry

    Checks:
    1. Domain registry for registered entities
    2. Inference heuristics if not registered

    Returns canonical schema name (resolves aliases)
    """
    # Check if entity is registered
    entry = self.naming_conventions.registry.get_entity(entity_name)
    if entry:
        # Get domain from registry entry
        domain_code = entry.domain_code
        domain = self.naming_conventions.registry.get_domain(domain_code)
        return domain.name  # Use canonical domain name (not alias)

    # Fallback to inference (for backward compatibility)
    return self._infer_schema_from_entity_name(entity_name)

def _infer_schema_from_entity_name(self, entity_name: str) -> str:
    """
    Infer schema from entity name using common patterns

    This is a fallback for entities not yet registered
    """
    name_lower = entity_name.lower()

    # CRM/Management entities
    if any(x in name_lower for x in ["contact", "company", "account", "customer"]):
        return "crm"

    # Catalog entities
    if any(x in name_lower for x in ["manufacturer", "product", "brand", "model"]):
        return "catalog"

    # Project entities
    if any(x in name_lower for x in ["project", "task", "milestone"]):
        return "projects"

    # Default to entity's own schema (will be validated elsewhere)
    return name_lower
```

**Lines to Change**: Replace entire schema_map dict (~10 lines) with new logic (~40 lines)

**Effort**: 20 minutes

**🐛 BUG FIX**: This also fixes the Manufacturer → "product" bug!

---

### 🟡 MODERATE: Documentation Files

#### 7. `.claude/CLAUDE.md`
**Changes**:
1. Remove "catalog" from universal schema examples
2. Add Tier 1/2/3 explanation
3. Update Team B section with schema registry
4. Add examples for different app types

**Sections to Update**:
- "TEAM STRUCTURE" → Team B description (add schema_registry mention)
- Add new section: "Schema Organization (3 Tiers)"
- Update examples to show catalog as PrintOptim-specific

**Lines to Change**: ~50 lines (mostly additions)

**Effort**: 20 minutes

---

#### 8. `docs/architecture/SCHEMA_STRATEGY.md`
**Changes**:
1. Add "Schema Tiers" section
2. Explain `multi_tenant` flag
3. Update multi-tenancy table
4. Add schema registry pattern

**Current** (line 83-91):
```markdown
| Schema | Type | tenant_id | RLS | Purpose |
|--------|------|-----------|-----|---------|
| `crm` | Tenant-Specific | ✅ REQUIRED | ✅ YES | Customer data |
| `management` | Tenant-Specific | ✅ REQUIRED | ✅ YES | Organization structure |
| `operations` | Tenant-Specific | ✅ REQUIRED | ✅ YES | Operational data |
| `common` | Shared | ❌ NONE | ❌ NO | Reference data (countries, currencies) |
| `catalog` | Shared | ❌ NONE | ❌ NO | Product catalogs |
```

**New**:
```markdown
| Schema | Type | tenant_id | RLS | Purpose | Tier |
|--------|------|-----------|-----|---------|------|
| `common` | Framework | ❌ NONE | ❌ NO | Reference data | **Tier 1** |
| `app` | Framework | ❌ NONE | ❌ NO | API types | **Tier 1** |
| `core` | Framework | Mixed | Mixed | Business functions | **Tier 1** |
| `crm` | Multi-Tenant | ✅ REQUIRED | ✅ YES | Customer data | **Tier 2** |
| `projects` | Multi-Tenant | ✅ REQUIRED | ✅ YES | Projects/tasks | **Tier 2** |
| `catalog` | Shared (App-Specific) | ❌ NONE | ❌ NO | Product catalog (PrintOptim) | **Tier 3** |
```

**Lines to Change**: ~100 lines (add sections, update table)

**Effort**: 30 minutes

---

#### 9. `docs/guides/ADDING_CUSTOM_DOMAINS.md` (NEW FILE)
**Change**: Create user guide for adding custom schemas

**Lines**: ~200 lines (new file)

**Effort**: 45 minutes

**Contents**:
- How to add multi-tenant domain
- How to add shared domain
- Examples (sales, hr, legal, healthcare)
- Common pitfalls

---

### 🟢 LOW PRIORITY: Test Files

#### 10. Test Files Using Hardcoded Schemas

**Files**:
- `tests/unit/numbering/test_numbering_parser.py`
- `tests/integration/test_team_b_integration.py`
- `tests/unit/registry/test_naming_conventions.py`
- `tests/unit/generators/test_composite_type_generator.py`
- `tests/unit/schema/test_foreign_key_generator.py`

**Change**: Update assertions to use schema_registry

**Example**:
```python
# BEFORE
assert entity.schema == "catalog"

# AFTER
assert schema_registry.get_canonical_schema_name(entity.schema) == "catalog"
```

**Lines to Change**: ~20 lines across all test files

**Effort**: 30 minutes

---

#### 11. New Test File: `tests/unit/schema/test_schema_registry.py`
**Change**: Create comprehensive tests for SchemaRegistry

**Lines**: ~150 lines (new file)

**Effort**: 45 minutes

**Test Cases**:
- Multi-tenant flag respected
- Alias resolution
- Framework schemas unchanged
- FK resolver uses registry
- Canonical name resolution

---

### 🔵 CLEANUP: Deprecated Code

#### 12. Remove Hardcoded Lists (Post-Migration)

**Files**:
- `src/generators/table_generator.py` - Remove `tenant_schemas` list
- `src/generators/trinity_helper_generator.py` - Remove `TENANT_SCHEMAS` constant
- `src/generators/core_logic_generator.py` - Remove `TENANT_SCHEMAS` constant

**Effort**: 5 minutes (delete lines)

---

## Implementation Order

### Phase 1: Foundation (1 hour)
1. ✅ Add `multi_tenant` flag to `domain_registry.yaml` (5 min)
2. ✅ Create `SchemaRegistry` class (30 min)
3. ✅ Write tests for `SchemaRegistry` (45 min)

### Phase 2: Generator Updates (1 hour)
4. ✅ Update `table_generator.py` (10 min)
5. ✅ Update `trinity_helper_generator.py` (15 min)
6. ✅ Update `core_logic_generator.py` (15 min)
7. ✅ Update `fk_resolver.py` (20 min)

### Phase 3: Testing (30 minutes)
8. ✅ Update existing test files (30 min)
9. ✅ Run full test suite (validate no regressions)

### Phase 4: Documentation (1.5 hours)
10. ✅ Update `.claude/CLAUDE.md` (20 min)
11. ✅ Update `SCHEMA_STRATEGY.md` (30 min)
12. ✅ Create `ADDING_CUSTOM_DOMAINS.md` (45 min)

### Phase 5: Cleanup (15 minutes)
13. ✅ Remove deprecated hardcoded lists (5 min)
14. ✅ Final validation (10 min)

**Total Effort**: ~4 hours

---

## Risk Assessment

### 🔴 HIGH RISK: Breaking Changes

**Risk**: Existing code relies on hardcoded schema names

**Mitigation**:
- ✅ Keep backward compatibility (fallback to inference)
- ✅ Comprehensive test suite before deployment
- ✅ Phase implementation (feature flag if needed)

### 🟡 MEDIUM RISK: Migration Complexity

**Risk**: Users with custom schemas may need to update registry

**Mitigation**:
- ✅ Migration script to auto-add `multi_tenant` flag
- ✅ Clear documentation for users
- ✅ Validation to catch missing flags

### 🟢 LOW RISK: Performance Impact

**Risk**: Registry lookups add overhead

**Mitigation**:
- ✅ Registry lookups are fast (dict lookups)
- ✅ Only called during generation (not runtime)
- ✅ Can cache if needed

---

## Success Criteria

### Functional
- [ ] All generators use `SchemaRegistry` (no hardcoded lists)
- [ ] Alias resolution works ("management" → "crm")
- [ ] Multi-tenant flag controls tenant_id behavior
- [ ] FK resolver bug fixed (Manufacturer → catalog)

### Quality
- [ ] All existing tests pass
- [ ] New tests for `SchemaRegistry` (90%+ coverage)
- [ ] No regressions in integration tests

### Documentation
- [ ] `.claude/CLAUDE.md` updated with schema tiers
- [ ] `SCHEMA_STRATEGY.md` reflects new model
- [ ] User guide for custom domains complete

### Cleanup
- [ ] All hardcoded `TENANT_SCHEMAS` lists removed
- [ ] No references to old schema map in FK resolver
- [ ] Validation rules enforce `multi_tenant` flag

---

## Rollback Plan

**If issues arise**:

1. **Keep old code commented** (don't delete immediately)
2. **Feature flag**: `USE_SCHEMA_REGISTRY = True/False`
3. **Fallback**: Registry lookups fall back to hardcoded lists
4. **Validation**: Warn but don't error on missing `multi_tenant` flag

**Rollback Steps**:
```python
# In generators:
if USE_SCHEMA_REGISTRY:
    is_tenant = self.schema_registry.is_multi_tenant(schema)
else:
    is_tenant = schema in TENANT_SCHEMAS  # Old hardcoded list
```

---

## Post-Migration Benefits

### For Framework Developers
- ✅ One place to update schema logic (`SchemaRegistry`)
- ✅ No scattered hardcoded lists
- ✅ Easier to add new domains

### For Users
- ✅ Can define custom multi-tenant schemas
- ✅ Can use schema aliases ("crm" or "management")
- ✅ Clear documentation for adding domains

### For Code Quality
- ✅ Single source of truth (domain registry)
- ✅ Type-safe schema classification
- ✅ Better test coverage

---

## Next Actions

1. **Review** this impact analysis
2. **Create subtasks** in task tracker
3. **Assign priority** (High - affects Week 2 Team B work)
4. **Schedule implementation** (Before Team B starts)
5. **Set up feature branch** (`feature/schema-registry`)

---

**Status**: 📋 READY FOR IMPLEMENTATION
**Effort**: ~4 hours
**Priority**: High (blocks Team B improvements)
**Risk**: Medium (breaking changes, but mitigated)

**Last Updated**: 2025-11-09
