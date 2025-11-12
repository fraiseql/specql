# Test Failures Fix Plan - Phased Approach

**Created**: 2025-11-11
**Status**: Planning
**Total Tests**: 1,419 (excluding archived)
**Estimated Failures**: ~31 tests

---

## Executive Summary

After the CDCConfig fix, we have approximately 31 failing tests across 5 main categories:
1. **Documentation Coverage** (3 tests) - Missing pattern docs
2. **Field Naming** (1 test) - Changed from `fk_user` to `fk_author`
3. **Impact Metadata Type Safety** (1 test) - dict vs ActionImpact object
4. **Job Execution Integration** (13 tests) - Needs investigation
5. **CLI Integration** (7 tests) - Parameter passing issues
6. **Performance/Integration** (6 tests) - Various integration issues

**Priority**: Start with quick wins (Phase 1-2) to get test suite mostly green, then tackle complex issues.

---

## Phase 1: Type Safety Fix - Impact Metadata 🔴 HIGH PRIORITY

**Estimated Time**: 1-2 hours
**Complexity**: Medium
**Impact**: Fixes 1 failing test, prevents future type errors

### Problem

`ImpactMetadataCompiler.build_primary_impact()` expects `ActionImpact` object but receives `dict`.

**Error**:
```python
AttributeError: 'dict' object has no attribute 'primary'
# impact is dict: {'primary': {'fields': ['rating']}}
# Expected: ActionImpact(primary=EntityImpact(...))
```

**Failing Tests**:
- `tests/unit/generators/actions/test_success_response_generator.py::test_generate_success_response_complete`

### Root Cause

Recent changes to `ImpactMetadataCompiler` assume type-safe `ActionImpact` objects, but some test contexts still pass raw dicts.

### Solution

#### Option A: Convert dict to ActionImpact in compiler (RECOMMENDED)
```python
# src/generators/actions/impact_metadata_compiler.py

def build_primary_impact(self, impact: ActionImpact | dict) -> str:
    """Build primary entity impact (type-safe)"""
    # Handle legacy dict format
    if isinstance(impact, dict):
        from src.core.ast_models import ActionImpact, EntityImpact
        primary_data = impact.get('primary', {})
        impact = ActionImpact(
            primary=EntityImpact(**primary_data) if primary_data else None,
            side_effects=[],
            cache_invalidations=[]
        )

    return f"""
    -- Build primary entity impact (type-safe)
    v_meta.primary_entity := {CompositeTypeBuilder.build_entity_impact(impact.primary)};
    """
```

#### Option B: Fix test to use proper ActionImpact objects
Update test fixtures to create proper `ActionImpact` instances.

### TDD Cycle

1. **RED**: Run failing test to confirm error
   ```bash
   uv run pytest tests/unit/generators/actions/test_success_response_generator.py::test_generate_success_response_complete -xvs
   ```

2. **GREEN**: Implement Option A (backwards compatible)
   - Add type check in `build_primary_impact()`
   - Add type check in `build_side_effects()`
   - Add type check in `build_cache_invalidations()`

3. **REFACTOR**: Clean up and optimize
   - Extract dict-to-ActionImpact conversion to helper method
   - Add type hints
   - Add docstring examples

4. **QA**: Verify
   ```bash
   uv run pytest tests/unit/generators/actions/test_success_response_generator.py -v
   uv run pytest tests/unit/actions/test_impact_metadata.py -v
   ```

### Success Criteria
- [ ] Test passes with dict input
- [ ] Test passes with ActionImpact input
- [ ] No regression in impact metadata tests
- [ ] Type hints are correct

---

## Phase 2: Field Naming Update - Table Views 🟡 MEDIUM PRIORITY

**Estimated Time**: 30 minutes
**Complexity**: Low
**Impact**: Fixes 1 failing test

### Problem

Test expects `fk_user` but code generates `fk_author` (field was renamed from `user` to `author`).

**Error**:
```python
assert 'fk_user INTEGER' in sql
# Actual: fk_author INTEGER, author_id UUID
```

**Failing Tests**:
- `tests/integration/fraiseql/test_tv_annotations_e2e.py::test_complete_tv_table_with_annotations`

### Root Cause

Test fixture still uses old field name `user: ref(User)` instead of `author: ref(User)`.

### Solution

Update test fixture to use current field name:

```python
# tests/integration/fraiseql/test_tv_annotations_e2e.py

entity_yaml = """
entity: Review
schema: library
fields:
  author: ref(User)  # Changed from 'user'
  book: ref(Book)
  rating: integer
"""

# Update assertions
assert "fk_author INTEGER" in sql  # Changed from fk_user
assert "author_id UUID" in sql      # Changed from user_id
```

### TDD Cycle

1. **RED**: Confirm failure
   ```bash
   uv run pytest tests/integration/fraiseql/test_tv_annotations_e2e.py::test_complete_tv_table_with_annotations -xvs
   ```

2. **GREEN**: Update fixture and assertions

3. **REFACTOR**: Check for other tests with same issue
   ```bash
   grep -r "fk_user" tests/
   grep -r "user: ref(User)" tests/integration/fraiseql/
   ```

4. **QA**: Verify all FraiseQL tests pass
   ```bash
   uv run pytest tests/integration/fraiseql/ -v
   ```

### Success Criteria
- [ ] Test passes with updated field name
- [ ] All FraiseQL integration tests pass
- [ ] No other tests broken by field rename

---

## Phase 3: Documentation Coverage 🟢 LOW PRIORITY

**Estimated Time**: 2-3 hours
**Complexity**: Low
**Impact**: Fixes 3 failing tests, improves documentation

### Problem

Missing index.md files for pattern documentation directories.

**Error**:
```python
AssertionError: Missing documentation (development in progress):
  ['docs/patterns/security/index.md',
   'docs/patterns/metrics/index.md',
   'docs/patterns/temporal/index.md',
   'docs/patterns/localization/index.md']
```

**Failing Tests**:
- `tests/docs/test_documentation_coverage.py::test_all_patterns_have_reference_docs`
- `tests/docs/test_documentation_coverage.py::test_pattern_docs_have_required_sections`
- `tests/docs/test_documentation_coverage.py::test_examples_reference_real_patterns`

### Root Cause

Pattern implementations exist but documentation index files are missing.

### Solution

Create minimal index.md files for each pattern category:

```markdown
# Security Patterns

## Overview
Security patterns provide data masking, permission filtering, and access control.

## Available Patterns
- **Data Masking**: Automatic PII/sensitive data masking
- **Permission Filter**: Row-level security based on user permissions

## Usage
See individual pattern documentation for detailed examples.

## Related Patterns
- Temporal Patterns (for audit trails)
- Junction Patterns (for role-based access)
```

### TDD Cycle

1. **RED**: Confirm missing docs
   ```bash
   uv run pytest tests/docs/test_documentation_coverage.py -xvs
   ```

2. **GREEN**: Create index.md files
   - `docs/patterns/security/index.md`
   - `docs/patterns/metrics/index.md`
   - `docs/patterns/temporal/index.md`
   - `docs/patterns/localization/index.md`

3. **REFACTOR**: Ensure required sections exist
   - Overview
   - Available Patterns
   - Usage
   - Related Patterns

4. **QA**: Verify docs tests pass
   ```bash
   uv run pytest tests/docs/ -v
   ```

### Success Criteria
- [ ] All 4 index.md files created
- [ ] All doc tests pass
- [ ] Docs follow consistent structure
- [ ] Links to actual pattern implementations

---

## Phase 4: CLI Integration Fixes 🔴 HIGH PRIORITY

**Estimated Time**: 3-4 hours
**Complexity**: Medium-High
**Impact**: Fixes 8 failing tests

### Problem

CLI tests failing due to parameter changes in orchestrator/generators.

**Failing Tests**:
- `tests/unit/cli/test_audit_cascade_cli.py::test_generate_with_audit_cascade_flag`
- `tests/unit/cli/test_generate.py::test_entities_foundation_only` (6 tests)

### Root Cause Investigation Needed

Need to check:
1. CLI parameter passing to orchestrator
2. Orchestrator signature changes
3. SchemaOrchestrator initialization
4. Missing CDC-related parameters

### Solution (TBD after investigation)

Likely issues:
- `SchemaOrchestrator` constructor changed
- Missing `audit_config` parameter
- Missing `cdc_config` parameter
- Changed return types

### TDD Cycle

1. **RED**: Run one CLI test to see exact error
   ```bash
   uv run pytest tests/unit/cli/test_generate.py::test_entities_foundation_only -xvs
   ```

2. **GREEN**: Fix parameter passing based on error

3. **REFACTOR**: Update all CLI tests with new pattern

4. **QA**: Run all CLI tests
   ```bash
   uv run pytest tests/unit/cli/ -v
   ```

### Investigation Tasks
- [ ] Check `SchemaOrchestrator.__init__()` signature
- [ ] Check `generate` command parameter mapping
- [ ] Check if audit/CDC flags are properly passed
- [ ] Update test fixtures with new parameters

---

## Phase 5: Job Execution Integration 🟡 MEDIUM PRIORITY

**Estimated Time**: 4-6 hours
**Complexity**: High
**Impact**: Fixes 13 failing tests

### Problem

Job execution E2E tests all failing. Likely related to recent runner framework changes.

**Failing Tests** (13 total):
- HTTP job execution (3 tests)
- Docker job execution (2 tests)
- Serverless job execution (2 tests)
- Error handling (2 tests)
- Resource management (2 tests)
- Security (1 test)
- Multi-runner workflow (1 test)

### Root Cause Investigation Needed

Need to check:
1. Runner initialization changes
2. Job schema changes
3. Execution type framework integration
4. Resource tracking changes

### Solution Strategy

1. **Investigate**: Run one test to see actual error
   ```bash
   uv run pytest tests/integration/runners/test_job_execution_e2e.py::test_http_job_execution_success -xvs
   ```

2. **Categorize**: Group errors by root cause
   - Schema changes
   - API changes
   - Configuration changes

3. **Fix**: Address each category systematically

### TDD Cycle

1. **RED**: Identify failure pattern
2. **GREEN**: Fix one test
3. **REFACTOR**: Apply fix to similar tests
4. **QA**: Verify all runner tests

### Investigation Tasks
- [ ] Check job schema changes in `app_schema_generator.py`
- [ ] Check runner initialization in test fixtures
- [ ] Check execution type enum changes
- [ ] Verify resource tracking still works

---

## Phase 6: Performance & Stdlib Integration 🟢 LOW PRIORITY

**Estimated Time**: 2-3 hours
**Complexity**: Medium
**Impact**: Fixes 6 failing tests

### Problem

Various integration and performance tests failing.

**Failing Tests**:
- `tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_snapshot`
- `tests/performance/test_extraction_performance.py::test_memory_usage_during_generation`
- `tests/pytest/test_contact_integration.py` (3 tests)

### Root Cause

Likely similar to other integration tests - parameter passing or schema changes.

### Solution

Investigate each test individually:

1. **Stdlib test**: Check Contact entity generation
2. **Performance test**: May need to adjust thresholds
3. **Contact integration**: Check database setup

### TDD Cycle

1. **RED**: Run each test individually
2. **GREEN**: Fix specific issue
3. **REFACTOR**: Extract common patterns
4. **QA**: Verify related tests

---

## Overall Strategy

### Recommended Order

1. **Phase 1** (Impact Metadata) - Fixes type safety issue, critical for code quality
2. **Phase 2** (Field Naming) - Quick win, 5 minutes
3. **Phase 4** (CLI Integration) - High impact, unlocks 8 tests
4. **Phase 3** (Documentation) - Low risk, can be done in parallel
5. **Phase 5** (Job Execution) - Complex but well-isolated
6. **Phase 6** (Performance) - Lowest priority

### Parallel Execution

Can be done simultaneously by different developers:
- **Developer 1**: Phase 1 + 2 (type safety + field naming)
- **Developer 2**: Phase 3 (documentation)
- **Developer 3**: Phase 4 + 5 (CLI + jobs investigation)

### Quick Wins First

After Phase 1 + 2:
- **Before**: ~31 failing tests
- **After**: ~29 failing tests
- **Time**: ~2 hours

After Phase 1 + 2 + 4:
- **Before**: ~31 failing tests
- **After**: ~21 failing tests
- **Time**: ~5 hours

### Success Metrics

- **Target**: < 5 failing tests
- **Stretch Goal**: 0 failing tests
- **Must Have**: All CDC/cascade/audit tests passing (✅ DONE)

---

## Investigation Checklist

Before starting each phase, run this investigation:

```bash
# 1. Identify exact error
uv run pytest <test_path> -xvs 2>&1 | tee error.log

# 2. Check recent changes to related files
git log --oneline -10 -- src/generators/actions/

# 3. Check for API signature changes
git diff HEAD~10 -- src/generators/schema_orchestrator.py

# 4. Run related tests to find patterns
uv run pytest tests/unit/generators/ -k "impact" -v
```

---

## Risk Assessment

### Low Risk (Green Light)
- ✅ Phase 2 (field naming) - Just test fixture update
- ✅ Phase 3 (documentation) - No code changes

### Medium Risk (Yellow Light)
- ⚠️ Phase 1 (type safety) - Affects core metadata compilation
- ⚠️ Phase 4 (CLI) - May have ripple effects
- ⚠️ Phase 6 (performance) - May need threshold adjustments

### High Risk (Red Light)
- 🔴 Phase 5 (job execution) - Large complex subsystem

### Mitigation

- Run full test suite after each phase
- Use git branches for each phase
- Review changes before merging
- Keep CDC tests passing at all times

---

## Notes

- **CDC/Audit/Cascade tests**: ✅ All 25 tests passing (PROTECTED)
- **Total test count**: 1,419 tests (excluding archived)
- **Estimated total fix time**: 12-18 hours
- **Recommended**: 2-3 focused sessions

---

**Last Updated**: 2025-11-11
**Next Review**: After Phase 1 completion
