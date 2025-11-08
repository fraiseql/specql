# Team C Naming Correction - Quick Fix Summary

**Issue**: Team C is using `input_pk_organization` instead of Trinity pattern naming
**Impact**: Breaks consistency, unclear variable semantics, non-standard JWT mapping
**Priority**: 🚨 FIX BEFORE TEAM C STARTS IMPLEMENTATION

---

## 🎯 The Fix (Simple Search & Replace)

### **1. Auth Parameters**
```diff
# In ALL templates and generators:
- input_pk_organization UUID
+ auth_tenant_id UUID

- input_created_by UUID
+ auth_user_id UUID
```

### **2. Variable Names**
```diff
# For entity-specific variables:
- v_id UUID := gen_random_uuid()
+ v_{entity}_id UUID := gen_random_uuid()
  Example: v_contact_id

- v_pk_{entity} INTEGER
+ v_{entity}_pk INTEGER
  Example: v_contact_pk
```

### **3. Usage in Code**
```diff
# When calling functions or inserting data:
- input_pk_organization
+ auth_tenant_id

- input_created_by
+ auth_user_id

- v_id
+ v_{entity}_id
```

---

## 📝 Files to Update

### **Templates** (4 files)
```bash
templates/sql/app_wrapper.sql.j2
templates/sql/core_create_function.sql.j2
templates/sql/core_update_function.sql.j2
templates/sql/core_delete_function.sql.j2
```

**Search for**: `input_pk_organization`, `input_created_by`, `v_id UUID :=`
**Replace with**: Trinity pattern names

### **Generators** (2 files)
```bash
src/generators/app_wrapper_generator.py
src/generators/core_logic_generator.py
```

**Update**: Template context to use correct parameter names

### **Tests** (2 files)
```bash
tests/unit/generators/test_app_wrapper_generator.py
tests/unit/generators/test_core_logic_generator.py
```

**Update**: Test assertions to expect new naming

### **Documentation** (3 files)
```bash
docs/implementation-plans/TEAM_C_APP_CORE_FUNCTIONS_PLAN.md
docs/teams/TEAM_C_DETAILED_PLAN.md
docs/architecture/APP_CORE_FUNCTION_PATTERN.md
```

**Update**: Examples to show correct Trinity pattern

---

## ✅ Quick Validation

After making changes, run:

```bash
# Should return NO results:
git grep -n "input_pk_organization"
git grep -n "input_created_by" | grep -v "created_by UUID" | grep "input_"
git grep -n "v_id UUID :="

# Tests should pass:
uv run pytest tests/unit/generators/ -v
```

---

## 📖 Why This Matters

### **Trinity Pattern Naming Principles**

| Old (Wrong) | New (Correct) | Reason |
|------------|--------------|---------|
| `input_pk_organization` | `auth_tenant_id` | Clearer that it's JWT auth context, not input data |
| `input_created_by` | `auth_user_id` | Consistent with `auth_tenant_id`, shows it's auth context |
| `v_id` | `v_contact_id` | Entity-specific, avoids ambiguity in multi-entity functions |
| `v_pk_contact` | `v_contact_pk` | Consistent ordering: `v_{entity}_pk` pattern |

### **Benefits**

1. **Clarity**: `auth_` prefix immediately identifies JWT context
2. **Consistency**: All auth params follow same pattern
3. **Type Safety**: `v_contact_id` (UUID) vs `v_contact_pk` (INTEGER) is unambiguous
4. **Greppability**: Easy to search for entity-specific operations
5. **Standards**: Matches PostgreSQL RLS and JWT claim conventions

---

## 🚀 Implementation Steps

1. **Read**: `/home/lionel/code/printoptim_backend_poc/docs/teams/TEAM_C_TRINITY_PATTERN_CORRECTION.md`
2. **Update Templates**: Search & replace in 4 SQL template files
3. **Update Generators**: Fix context in 2 Python files
4. **Update Tests**: Fix assertions in 2 test files
5. **Update Docs**: Fix examples in 3 documentation files
6. **Verify**: Run grep commands to ensure no old naming remains
7. **Test**: Run `uv run pytest tests/unit/generators/ -v`
8. **Commit**: "fix(Team C): Correct naming to follow Trinity pattern"

---

## 📋 Detailed Correction Document

For complete details, examples, and rationale, see:

**👉 `/docs/teams/TEAM_C_TRINITY_PATTERN_CORRECTION.md`**

This document contains:
- ✅ Complete before/after examples
- ✅ Full template diffs
- ✅ Python generator updates
- ✅ Test updates
- ✅ Reference implementation
- ✅ Verification checklist

---

**Status**: Ready for immediate implementation
**Time Required**: ~30 minutes
**Priority**: Must fix before Team C starts coding
