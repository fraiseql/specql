# Test Fixes - Executive Summary

**Date**: 2025-11-18
**Current Status**: 1456 passing, 21 failed, 13 errors (34 issues)
**Target Status**: 1478+ passing, 0 failed, 0 errors (100%)
**Estimated Time**: 6-8 hours

---

## 🎯 Quick Overview

All 34 failing tests fall into 4 categories with clear solutions:

| Issue | Tests | Time | Difficulty |
|-------|-------|------|------------|
| **Missing faker dependency** | 8 | 30 min | Easy |
| **Duplicate indexes in tests** | 13 | 2-3 hrs | Medium |
| **Confiture config parsing** | 1 | 2-3 hrs | Hard |
| **Total** | **22** | **6-8 hrs** | - |

---

## 📋 The 4 Issues

### 1️⃣ Seed Generator: Missing Faker (8 tests)

**Error**: `ImportError: faker not installed`

**Fix**: Add to `pyproject.toml`
```toml
[project.optional-dependencies]
testing = ["faker>=20.0.0"]
```

**Time**: 30 minutes
**Impact**: +8 tests immediately ✅

---

### 2️⃣ Integration Tests: Duplicate Indexes (13 tests)

**Error**: `psycopg.errors.DuplicateTable: relation "idx_tb_contact_email" already exists`

**Root Cause**: PostgreSQL index names are database-global, not schema-scoped. When tests create `idx_tb_contact_email` in multiple isolated schemas, the second test fails.

**Fix**: Prefix index names with schema in tests
```python
ddl = ddl.replace("CREATE INDEX idx_", f"CREATE INDEX {isolated_schema}_idx_")
```

**Files**:
- `tests/integration/schema/test_rich_types_postgres.py` (5 tests)
- `tests/integration/fraiseql/test_rich_type_autodiscovery.py` (8 tests)

**Time**: 2-3 hours
**Impact**: +13 tests ✅

---

### 3️⃣ Confiture: Config Parsing Error (1 test)

**Error**: `❌ Error: 'str' object has no attribute 'get'`

**Root Cause**: Confiture CLI receiving string when expecting dict

**Fix**: Either:
- A. Fix `db/environments/test.yaml` structure
- B. Update Confiture CLI to handle string configs
- C. Fix config loading in migration code

**Needs Investigation**: Yes (30-60 min to identify exact cause)

**Time**: 2-3 hours
**Impact**: +1 test ✅

---

### 4️⃣ Verification & Documentation (1 hour)

- Run full test suite
- Update documentation
- Create summary report

---

## 🚀 Execution Plan

### Quick Start (30 min)
```bash
# Phase 1: Fix faker dependency
echo 'faker>=20.0.0' >> requirements-test.txt
uv sync --extra testing
uv run pytest tests/unit/testing/test_seed_generator.py -v
# Expected: +8 tests passing ✅
```

### Main Work (4-6 hours)
```bash
# Phase 2: Fix index isolation
# Edit test files to prefix index names
uv run pytest tests/integration/schema/test_rich_types_postgres.py -v
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v
# Expected: +13 tests passing ✅

# Phase 3: Fix confiture
# Investigate and fix config parsing
uv run confiture migrate up --config db/environments/test.yaml
uv run pytest tests/integration/test_confiture_integration.py -v
# Expected: +1 test passing ✅
```

### Wrap Up (1 hour)
```bash
# Phase 4: Verify all tests
uv run pytest
# Expected: 1478+ passing, 0 failed, 0 errors 🎉
```

---

## 📊 Expected Outcome

**Before**:
- 1456 passing
- 21 failed
- 13 errors
- **95.7% pass rate**

**After**:
- 1478+ passing
- 0 failed
- 0 errors
- **100% pass rate** ✅

---

## ⚡ Priority Recommendation

### Option 1: All Fixes (6-8 hours)
Complete all 4 phases for 100% test coverage

### Option 2: Critical Only (30 min)
Just fix faker dependency (+8 tests, 97.2% pass rate)

### Option 3: Skip Confiture (4-5 hours)
Fix faker + index isolation (+21 tests, 99.9% pass rate)
Document confiture as known issue

---

## 📎 Full Details

See `docs/post_beta_plan/test_fixes_detailed_plan.md` for:
- Complete root cause analysis
- Step-by-step implementation guides
- Code snippets and examples
- Risk mitigation strategies
- Verification procedures

---

**Status**: Ready for implementation
**Blocker**: None - all issues have clear solutions
**Risk**: Low - fixes are isolated to test code
