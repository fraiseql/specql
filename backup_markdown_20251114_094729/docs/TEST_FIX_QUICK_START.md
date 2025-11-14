# Test Suite Fix - Quick Start Guide

**For the implementing agent: Start here, then read the full implementation plan**

---

## TL;DR

- **38 failing tests + 7 errors** out of 846 total tests
- **Most failures are test maintenance**, not bugs
- **1 critical bug**: Trinity Helper FK resolution not generated
- **Estimated time**: 6-10 hours total
- **Execution order**: Phase 1 → Phase 2 → Phase 3 → (optional) Phase 4-6

---

## Quick Status Check

```bash
# Current test status
cd /home/lionel/code/printoptim_backend_poc
uv run pytest --tb=no -q | tail -5

# Expected output:
# ===== 38 failed, 765 passed, 36 skipped, 7 errors in ~30s =====
```

---

## Phase Summary (In Order)

### 🔴 Phase 1: CRITICAL BUG (2-3 hours)

**What**: Trinity Helper FK resolution not being generated in core functions
**Where**: `src/generators/core_logic_generator.py:175` (condition check)
**Test**: `tests/unit/generators/test_core_logic_generator.py::test_core_function_uses_trinity_helpers`

**Quick Check**:
```bash
uv run pytest tests/unit/generators/test_core_logic_generator.py::test_core_function_uses_trinity_helpers -xvs
```

**Expected Failure**: SQL should have `crm.company_pk(...)` but doesn't

**Fix**: Add FK resolution logic to INSERT step compiler

---

### 🟡 Phase 2: ARCHITECTURE DECISION (2-3 hours)

**What**: 25 tests expect old FraiseQL annotation behavior
**Where**: `tests/unit/fraiseql/test_mutation_annotator.py`
**Decision**: Keep new architecture (Core layer = no annotations, App layer = with annotations)

**Quick Check**:
```bash
uv run pytest tests/unit/fraiseql/test_mutation_annotator.py::TestMutationAnnotation::test_generates_mutation_annotation -xvs
```

**Expected Failure**: Test expects `@fraiseql:mutation` in core layer function

**Fix**: Split tests into `TestCoreMutationAnnotation` and `TestAppMutationAnnotation`

---

### 🟢 Phase 3: CLI TEST UPDATES (1.5-2 hours)

**What**: CLI interface changed, tests outdated
**Where**: `tests/unit/cli/test_generate.py`

**Quick Check**:
```bash
uv run pytest tests/unit/cli/test_generate.py::TestGenerateCLI::test_entities_foundation_only -xvs
```

**Expected Failure**: Exit code or output format mismatch

**Fix**: Update test assertions to match new CLI output

---

### 🔵 Phase 4: FRONTEND TESTS (30 mins)

**What**: Overly strict string matching
**Where**: `tests/integration/frontend/test_frontend_generators_e2e.py`

**Quick Check**:
```bash
uv run pytest tests/integration/frontend/test_frontend_generators_e2e.py::TestFrontendGeneratorsE2E::test_typescript_types_generator -xvs
```

**Expected Failure**: `MutationResult<T = any>` doesn't match `MutationResult<T>`

**Fix**: Make string assertions more flexible

---

### 🟣 Phase 5: MINOR FIXES (45 mins)

**What**: Annotation format mismatches
**Where**: `tests/unit/generators/test_composite_type_generator.py` and 2 others

**Fix**: Update annotations to match YAML format instead of inline format

---

### ⚪ Phase 6: DATABASE TESTS (SKIP)

**What**: Missing PostgreSQL fixtures
**Status**: OPTIONAL - skip for now, these are for CI/CD

---

## Verification Commands

### After Each Phase

```bash
# Phase 1
uv run pytest tests/unit/generators/test_core_logic_generator.py -v

# Phase 2
uv run pytest tests/unit/fraiseql/ tests/integration/fraiseql/ -v

# Phase 3
uv run pytest tests/unit/cli/ -v

# Phase 4
uv run pytest tests/integration/frontend/ -v

# Phase 5
uv run pytest tests/unit/generators/test_composite_type_generator.py tests/unit/schema/test_comment_generation.py tests/unit/schema/test_node_info_split.py -v
```

### Full Test Suite

```bash
# Run all tests
uv run pytest --tb=short

# Target: ~838 passed, 36 skipped (excludes 7 database tests)
```

---

## Critical Files Map

### Phase 1 Files

**Code to Fix**:
- `src/generators/core_logic_generator.py:175` - Change condition from tier check to type_name check

**Test to Pass**:
- `tests/unit/generators/test_core_logic_generator.py:77-95`

### Phase 2 Files

**Tests to Update**:
- `tests/unit/fraiseql/test_mutation_annotator.py` - Split into core + app tests
- `tests/integration/fraiseql/test_mutation_annotations_e2e.py` - Update to check both layers
- `tests/integration/test_confiture_integration.py:80-95` - Update annotation checks

**Reference Code** (DO NOT MODIFY):
- `src/generators/fraiseql/mutation_annotator.py` - Current implementation is CORRECT
- `src/generators/app_wrapper_generator.py` - Uses `generate_app_mutation_annotation()`

### Phase 3 Files

**Tests to Update**:
- `tests/unit/cli/test_generate.py` - 9 tests
- `tests/unit/cli/test_orchestrator.py` - 1 test
- `tests/unit/cli/test_validate.py` - 3 tests

**Reference Code** (DO NOT MODIFY):
- `src/cli/generate.py` - Current CLI implementation
- `src/cli/validate.py` - Current validation implementation

---

## Common Pitfalls

### ❌ DON'T

1. **Don't revert the FraiseQL architecture change** - the new architecture is better
2. **Don't modify working code** - fix the tests, not the implementation (except Phase 1)
3. **Don't skip verification** - run tests after each phase
4. **Don't batch all changes** - commit after each phase

### ✅ DO

1. **Read the full implementation plan** before starting
2. **Execute phases in order** (1 → 2 → 3 → 4 → 5)
3. **Verify no regressions** after each phase
4. **Document any deviations** from the plan

---

## Success Criteria

### Minimum (Production Ready)

- ✅ Phase 1 complete (Trinity helpers working)
- ✅ Phase 2 complete (FraiseQL tests updated)
- ✅ 800+ tests passing

### Full Success

- ✅ Phases 1-5 complete
- ✅ 838+ tests passing (99%+)
- ✅ Only database tests skipped

---

## Emergency Commands

### If Tests Get Worse

```bash
# See what changed
git status
git diff

# Revert to before changes
git stash

# Re-run tests
uv run pytest -v

# Compare before/after
diff <(git stash show) <(git diff)
```

### If Stuck

1. Read the detailed plan: `docs/TEST_SUITE_FIX_IMPLEMENTATION_PLAN.md`
2. Check the specific test failure output
3. Review the referenced code files
4. Compare expected vs actual test assertions

---

## Time Budget

- **Phase 1**: 2-3 hours (CRITICAL - actual bug fix)
- **Phase 2**: 2-3 hours (HIGH - 25 tests)
- **Phase 3**: 1.5-2 hours (MEDIUM - 12 tests)
- **Phase 4**: 30 mins (LOW - 3 tests)
- **Phase 5**: 45 mins (LOW - 3 tests)

**Total**: 7-10 hours for 100% test pass rate

---

## Next Steps

1. ✅ Read this quick start guide (you're here!)
2. 📖 Read the full implementation plan: `docs/TEST_SUITE_FIX_IMPLEMENTATION_PLAN.md`
3. 🔴 Start with Phase 1 (Trinity Helper FK resolution)
4. ✅ Verify Phase 1 tests pass
5. 🟡 Continue to Phase 2 (FraiseQL tests)
6. ✅ Verify Phase 2 tests pass
7. 🟢 Continue to Phase 3 (CLI tests)
8. ✅ Run full test suite
9. 🎉 Report completion

---

**Good luck! Most of this is straightforward test maintenance. The only real bug is in Phase 1.**
