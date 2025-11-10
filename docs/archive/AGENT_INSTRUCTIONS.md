# 🤖 AGENT: Schema Registry Test Fixes - Your Mission

**Status**: 🔴 CRITICAL - 47 Tests Failing
**Your Task**: Fix all failing tests after SchemaRegistry implementation
**Time Estimate**: 2-3 hours
**Difficulty**: ⭐⭐ (Medium - repetitive pattern)

---

## 📋 Quick Summary

**What Happened**: The SchemaRegistry implementation is excellent, but it introduced a breaking API change. Generators now require a `schema_registry` parameter, but tests weren't updated.

**Your Mission**: Update all failing tests to use the new API.

**Detailed Plan**: See `docs/implementation-plans/SCHEMA_REGISTRY_TEST_FIX_PLAN.md`

---

## 🎯 The Fix Pattern (Very Simple!)

**Old Code** (failing):
```python
def test_something():
    generator = TableGenerator()  # ❌ Missing required parameter
    result = generator.generate(entity)
```

**New Code** (passing):
```python
def test_something(table_generator):  # ✅ Use fixture
    result = table_generator.generate(entity)
```

**That's it!** You need to apply this pattern to 47 tests across 5 files.

---

## 📝 Your Step-by-Step Checklist

### ✅ Phase 1: Create Shared Fixtures (15 min)
- [ ] Update `tests/conftest.py` with new fixtures
- [ ] Add: `schema_registry`, `table_generator`, `trinity_helper_generator`, `core_logic_generator`
- [ ] **See plan**: Section "Phase 1: Create Shared Fixtures"

### ✅ Phase 2: Fix TableGenerator Tests (90 min)
- [ ] Fix `tests/unit/generators/test_comment_generation.py` (13 tests)
- [ ] Fix `tests/unit/generators/test_constraint_generation.py` (9 tests)
- [ ] Fix `tests/unit/generators/test_index_generation.py` (6 tests)
- [ ] Fix `tests/unit/generators/test_rich_type_ddl.py` (12 tests)
- [ ] Fix `tests/integration/test_table_generator_integration.py` (10 tests)
- [ ] **Pattern**: Replace `TableGenerator()` with `table_generator` fixture
- [ ] **See plan**: Section "Phase 2: Fix TableGenerator Tests"

### ✅ Phase 3: Fix FK Resolver Tests (30 min)
- [ ] Update `tests/unit/actions/test_fk_resolver.py`
- [ ] Add `naming_conventions` fixture parameter
- [ ] Pass to `ForeignKeyResolver(naming_conventions)`
- [ ] Change assertions: `product` → `catalog` (bug fix!)
- [ ] **See plan**: Section "Phase 3: Fix FK Resolver Tests"

### ✅ Phase 4: Add Integration Tests (30 min)
- [ ] Create `tests/integration/test_schema_registry_integration.py`
- [ ] Test multi-tenant behavior (crm has tenant_id, catalog doesn't)
- [ ] Test alias resolution (management → crm)
- [ ] Test FK resolver uses registry
- [ ] **See plan**: Section "Phase 4: Add End-to-End Integration Test"

### ✅ Phase 5: Validation (15 min)
- [ ] Run full test suite: `uv run pytest --tb=short`
- [ ] Verify: 0 failures, 100+ passing
- [ ] Check coverage: `uv run pytest --cov=src`
- [ ] **See plan**: Section "Phase 5: Validation & Verification"

### ✅ Phase 6: Documentation (15 min)
- [ ] Create `docs/guides/SCHEMA_REGISTRY_MIGRATION.md`
- [ ] Update `src/generators/README.md` with usage examples
- [ ] **See plan**: Section "Phase 6: Documentation & Cleanup"

### ✅ Phase 7: Final Report (10 min)
- [ ] Run clean test suite
- [ ] Create completion report
- [ ] Verify git status
- [ ] **See plan**: Section "Phase 7: Final Verification"

---

## 🚀 Quick Start

**Step 1**: Read the detailed plan
```bash
cat docs/implementation-plans/SCHEMA_REGISTRY_TEST_FIX_PLAN.md
```

**Step 2**: Start with Phase 1 (fixtures)
```bash
# Open conftest.py and add the fixtures from the plan
vim tests/conftest.py
```

**Step 3**: Fix tests one file at a time
```bash
# Example: Fix first test file
vim tests/unit/generators/test_comment_generation.py

# Pattern: Replace TableGenerator() with table_generator fixture
# Run tests to verify
uv run pytest tests/unit/generators/test_comment_generation.py -v
```

**Step 4**: Repeat for all 5 test files

**Step 5**: Complete remaining phases

---

## 🎓 Key Concepts

### Why This Change Happened

**Before** (hardcoded):
```python
# Generators had hardcoded list
TENANT_SCHEMAS = ["tenant", "crm", "management", "operations"]
```

**After** (registry-driven):
```yaml
# Domain registry has metadata
"2":
  name: crm
  multi_tenant: true  # ← Determines tenant_id behavior
```

**Benefits**:
- ✅ Single source of truth
- ✅ Supports aliases (management → crm)
- ✅ Easy to add new domains
- ✅ Fixed bug: Manufacturer now maps to `catalog` (not `product`)

### The Fixture Pattern

```python
# In conftest.py (you create this):
@pytest.fixture
def table_generator(schema_registry):
    return TableGenerator(schema_registry)

# In test files (you use this):
def test_something(table_generator):  # ← Pytest auto-injects
    result = table_generator.generate(entity)
    assert "expected" in result
```

**Why**: Eliminates code duplication, ensures consistent setup.

---

## 💡 Pro Tips

1. **Work Phase by Phase** - Don't skip ahead
2. **Test Frequently** - Run tests after each file
3. **Copy the Pattern** - Once you fix one test file, others are identical
4. **Use Search/Replace** - `TableGenerator()` → `table_generator` (fixture param)
5. **Commit Often** - Git commit after each phase
6. **Ask If Stuck** - If blocked > 15 min, document and ask for help

---

## 📊 Progress Tracking

Create a checklist as you work:

```markdown
## My Progress

- [x] Read detailed plan
- [x] Phase 1: Fixtures created
- [ ] Phase 2.1: test_comment_generation.py (13 tests)
- [ ] Phase 2.2: test_constraint_generation.py (9 tests)
- [ ] Phase 2.3: test_index_generation.py (6 tests)
- [ ] Phase 2.4: test_rich_type_ddl.py (12 tests)
- [ ] Phase 2.5: test_table_generator_integration.py (10 tests)
- [ ] Phase 3: FK resolver tests
- [ ] Phase 4: Integration tests
- [ ] Phase 5: Validation
- [ ] Phase 6: Documentation
- [ ] Phase 7: Final report

**Current Status**: Working on Phase X
**Tests Fixed**: X/47
**Estimated Completion**: X hours remaining
```

---

## 🆘 If You Get Stuck

### Common Issues

**Issue 1**: Import errors
```python
# Make sure imports are correct
from src.generators.table_generator import TableGenerator
from src.generators.schema.schema_registry import SchemaRegistry
```

**Issue 2**: Fixture not found
```python
# Did you add the fixture to conftest.py?
# Check: grep "def table_generator" tests/conftest.py
```

**Issue 3**: Tests still failing after update
```python
# Run with verbose output to see error
uv run pytest tests/path/to/test.py::test_name -vv

# Check you removed the old TableGenerator() line
# Check you added the fixture parameter
```

### Get Help Template

If stuck > 15 minutes, document:

```markdown
## 🆘 STUCK - Need Help

**Phase**: X
**Task**: Y
**File**: tests/path/to/test.py

**Error**:
```
[paste error message]
```

**What I tried**:
1. [attempt 1]
2. [attempt 2]

**Current code**:
```python
[paste relevant test code]
```
```

---

## ✅ Success Criteria

You're done when:

1. ✅ All 47 tests are passing
2. ✅ Integration tests created and passing
3. ✅ Full test suite runs clean: `uv run pytest`
4. ✅ Coverage > 85%
5. ✅ Documentation created
6. ✅ Completion report written

---

## 📚 Resources

- **Detailed Plan**: `docs/implementation-plans/SCHEMA_REGISTRY_TEST_FIX_PLAN.md` ← START HERE
- **QA Report**: `docs/architecture/SCHEMA_REFACTORING_IMPACT.md`
- **Strategy Doc**: `docs/architecture/SCHEMA_ORGANIZATION_STRATEGY.md`

---

**You've got this!** 🚀

The implementation is excellent - you're just updating tests to use the new API. The pattern is simple and repetitive, so it will go quickly once you get into the rhythm.

**Estimated time**: 2-3 hours for all phases.

Start with Phase 1 in the detailed plan!
