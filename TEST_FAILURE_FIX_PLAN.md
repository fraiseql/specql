# Test Failure Fix Plan - SpecQL v0.5.0b1

**Date**: 2025-11-17
**Current Status**: 5 failed, 1122 passed, 18 skipped, 3 xfailed
**Success Rate**: 99.6%
**Target**: 100% passing tests for stable v0.5.0 release

---

## Executive Summary

The v0.5.0b1 beta release has an excellent test pass rate of 99.6% (1122/1127 passing tests). However, to achieve production readiness for a stable v0.5.0 release, we need to fix the remaining **5 critical test failures** across 2 categories:

1. **Database Integration Tests** (3 failures) - Missing PostgreSQL functions
2. **Frontend Generation Tests** (2 failures) - `Path` variable scoping bug

All failures are **straightforward to fix** and represent regression bugs introduced during recent refactoring, not fundamental architectural issues.

---

## Current Test Landscape

### ✅ Passing Test Coverage (99.6%)

- **1122 tests passing** across all major subsystems
- **18 tests skipped** (database-dependent, optional features)
- **3 tests xfailed** (expected failures, experimental features)

### ❌ Critical Failures (5 tests, 0.4%)

#### Category 1: Database Integration (3 tests)
- `tests/pytest/test_contact_integration.py::test_create_contact_happy_path`
- `tests/pytest/test_contact_integration.py::test_create_duplicate_contact_fails`
- `tests/pytest/test_contact_integration.py::test_convert_to_customer`

**Root Cause**: PostgreSQL function `app.create_contact()` not deployed to test database

#### Category 2: Frontend Generation (2 tests)
- `tests/unit/cli/test_generate.py::test_entities_with_frontend_generation`
- `tests/unit/cli/test_generate.py::test_entities_with_frontend_and_impacts`

**Root Cause**: `UnboundLocalError: cannot access local variable 'Path'` in `src/cli/generate.py:162`

---

## Phased Fix Implementation Plan

### Phase 1: Quick Wins - Frontend Generation Bug (Priority: HIGH)

**Complexity**: Simple
**Impact**: 2 test failures
**Estimated Time**: 15 minutes
**Dependencies**: None

#### Objective
Fix the `Path` variable scoping bug in frontend generation that causes `UnboundLocalError`.

#### Problem Analysis
```python
# Current buggy code in src/cli/generate.py:162
frontend_dir = Path(output_frontend)  # Path is not in scope here
```

The `Path` class from `pathlib` is either:
1. Not imported at all
2. Imported conditionally and not available in this scope
3. Shadowed by a local variable

#### TDD Cycle

**RED Phase**: Write failing test
```bash
# Verify tests are currently failing
uv run pytest tests/unit/cli/test_generate.py::TestGenerateCLI::test_entities_with_frontend_generation -v
uv run pytest tests/unit/cli/test_generate.py::TestGenerateCLI::test_entities_with_frontend_and_impacts -v
```

**Expected Failure**: `UnboundLocalError: cannot access local variable 'Path'`

**GREEN Phase**: Implement minimal fix
1. **Inspect the code**:
   ```bash
   # Check imports in src/cli/generate.py
   grep -n "^import\|^from.*import" src/cli/generate.py | grep -i path
   ```

2. **Identify the issue**:
   - If `Path` is not imported: Add `from pathlib import Path`
   - If conditionally imported: Move import to top level
   - If shadowed: Rename conflicting variable

3. **Apply fix**:
   ```python
   # Option 1: Ensure Path is imported at module level
   from pathlib import Path

   # Option 2: If Path is shadowed, use pathlib.Path explicitly
   import pathlib
   frontend_dir = pathlib.Path(output_frontend)
   ```

4. **Run tests**:
   ```bash
   uv run pytest tests/unit/cli/test_generate.py::TestGenerateCLI::test_entities_with_frontend_generation -v
   uv run pytest tests/unit/cli/test_generate.py::TestGenerateCLI::test_entities_with_frontend_and_impacts -v
   ```

**Expected Result**: Both tests pass

**REFACTOR Phase**: Clean up and verify
1. **Check for similar issues**:
   ```bash
   # Search for other instances of Path usage
   grep -n "Path(" src/cli/generate.py
   ```

2. **Verify no other UnboundLocalError patterns**:
   ```bash
   # Run all CLI tests
   uv run pytest tests/unit/cli/ -v
   ```

3. **Code quality check**:
   ```bash
   uv run ruff check src/cli/generate.py
   uv run mypy src/cli/generate.py
   ```

**QA Phase**: Full validation
1. **Run full CLI test suite**:
   ```bash
   uv run pytest tests/unit/cli/ -v
   ```

2. **Run integration tests**:
   ```bash
   uv run pytest tests/integration/ -v
   ```

3. **Manual smoke test**:
   ```bash
   # Test actual frontend generation
   specql generate entities/examples/contact.yaml --output-frontend=/tmp/test-frontend
   ls -la /tmp/test-frontend
   ```

**Success Criteria**:
- ✅ Both frontend generation tests pass
- ✅ No new test failures introduced
- ✅ Ruff and mypy checks pass
- ✅ Manual frontend generation works

---

### Phase 2: Database Integration Tests (Priority: MEDIUM)

**Complexity**: Medium
**Impact**: 3 test failures
**Estimated Time**: 45 minutes
**Dependencies**: None (can run in parallel with Phase 1)

#### Objective
Ensure PostgreSQL test database has all required functions deployed before running integration tests.

#### Problem Analysis
```
psycopg.errors.UndefinedFunction: function app.create_contact(uuid, uuid, jsonb) does not exist
HINT: No function matches the given name and argument types.
```

The test assumes `app.create_contact()` exists in the PostgreSQL database, but:
1. The function hasn't been generated/deployed
2. The test database setup doesn't run migrations
3. The function signature has changed

#### TDD Cycle

**RED Phase**: Confirm test failures
```bash
# Run failing tests
uv run pytest tests/pytest/test_contact_integration.py::TestContactIntegration -v

# Check database state
psql -h localhost -U postgres -d specql_test -c "\df app.create_contact"
```

**Expected Result**: Tests fail, function doesn't exist

**GREEN Phase**: Minimal implementation

1. **Option A: Generate and deploy SQL migrations**
   ```bash
   # Generate SQL from Contact entity
   specql generate entities/examples/contact.yaml --output=db/migrations

   # Apply migrations to test database
   psql -h localhost -U postgres -d specql_test -f db/migrations/30_functions/create_contact.sql
   ```

2. **Option B: Fix test database setup (preferred)**

   Create a test fixture that ensures migrations are applied:

   ```python
   # In tests/pytest/conftest.py or test_contact_integration.py

   @pytest.fixture(scope="module")
   def setup_contact_schema(db_connection):
       """Deploy Contact entity SQL before running integration tests."""
       # Generate SQL
       result = subprocess.run([
           "specql", "generate",
           "entities/examples/contact.yaml",
           "--output", "/tmp/contact_test_migrations"
       ])

       # Apply to test database
       with db_connection.cursor() as cur:
           # Read and execute migration files
           sql_files = sorted(Path("/tmp/contact_test_migrations").glob("**/*.sql"))
           for sql_file in sql_files:
               cur.execute(sql_file.read_text())

       db_connection.commit()
       yield

       # Cleanup: drop schema
       with db_connection.cursor() as cur:
           cur.execute("DROP SCHEMA IF EXISTS app CASCADE")
       db_connection.commit()


   class TestContactIntegration:
       @pytest.fixture(autouse=True)
       def setup(self, setup_contact_schema):
           """Ensure schema is deployed before each test."""
           pass
   ```

3. **Option C: Use pytest markers for database-dependent tests**

   ```python
   # Mark tests that require database
   @pytest.mark.database
   @pytest.mark.requires_migrations
   class TestContactIntegration:
       ...
   ```

   ```bash
   # Skip database tests in CI if no DB available
   pytest -m "not database"
   ```

**Recommended Approach**: Option B (automated fixture)

**REFACTOR Phase**: Improve test infrastructure

1. **Create reusable database fixture**:
   ```python
   # tests/conftest.py

   @pytest.fixture(scope="session")
   def test_database():
       """Create and configure test database."""
       # Setup: create database
       # Apply base schema
       yield connection
       # Teardown: drop database


   @pytest.fixture
   def deploy_entity_sql(test_database):
       """Factory fixture to deploy entity migrations."""
       def _deploy(entity_file: str):
           # Generate SQL
           # Apply to test_database
           # Return cleanup function
           pass
       return _deploy
   ```

2. **Update integration tests**:
   ```python
   class TestContactIntegration:
       @pytest.fixture(autouse=True)
       def setup_schema(self, deploy_entity_sql):
           cleanup = deploy_entity_sql("entities/examples/contact.yaml")
           yield
           cleanup()
   ```

3. **Document database test requirements**:
   ```markdown
   # tests/pytest/README.md

   ## Database Integration Tests

   Tests in this directory require a PostgreSQL database.

   ### Setup
   ```bash
   # Create test database
   createdb specql_test

   # Set environment variables
   export DATABASE_URL=postgresql://localhost/specql_test
   ```

**QA Phase**: Comprehensive validation

1. **Run all database integration tests**:
   ```bash
   uv run pytest tests/pytest/ -v
   ```

2. **Run with fresh database**:
   ```bash
   dropdb specql_test && createdb specql_test
   uv run pytest tests/pytest/ -v
   ```

3. **Verify no side effects**:
   ```bash
   # Check database state after tests
   psql specql_test -c "\dn"  # List schemas
   psql specql_test -c "\dt app.*"  # List tables
   psql specql_test -c "\df app.*"  # List functions
   ```

4. **Run full test suite**:
   ```bash
   uv run pytest --tb=short
   ```

**Success Criteria**:
- ✅ All 3 Contact integration tests pass
- ✅ Tests can run in isolation (clean database)
- ✅ Tests can run repeatedly (proper cleanup)
- ✅ No database state leaks between tests
- ✅ Clear documentation for database setup

---

### Phase 3: Full Test Suite Validation (Priority: CRITICAL)

**Complexity**: Simple
**Impact**: Release readiness
**Estimated Time**: 30 minutes
**Dependencies**: Phases 1 and 2 complete

#### Objective
Verify all tests pass and maintain stability across multiple runs.

#### TDD Cycle

**RED Phase**: Establish baseline
```bash
# Run full test suite with verbose output
uv run pytest --tb=short -v > test_baseline.txt 2>&1

# Count failures
grep "FAILED" test_baseline.txt | wc -l

# Expected: 5 failures (before fixes)
```

**GREEN Phase**: Apply all fixes
```bash
# After Phase 1 and Phase 2 fixes are applied
uv run pytest --tb=short -v > test_after_fixes.txt 2>&1

# Count failures
grep "FAILED" test_after_fixes.txt | wc -l

# Expected: 0 failures
```

**REFACTOR Phase**: Optimize test performance

1. **Identify slow tests**:
   ```bash
   uv run pytest --durations=20
   ```

2. **Optimize database fixtures** (if needed):
   - Use session-scoped fixtures for schema setup
   - Implement transactional rollback instead of full cleanup
   - Consider using pytest-xdist for parallel execution

3. **Add test categories**:
   ```python
   # pytest.ini or pyproject.toml
   [tool.pytest.ini_options]
   markers = [
       "unit: Unit tests (fast, no external dependencies)",
       "integration: Integration tests (database, file system)",
       "slow: Slow-running tests (> 1 second)",
       "database: Requires PostgreSQL database",
   ]
   ```

**QA Phase**: Release readiness check

1. **Run full test suite multiple times**:
   ```bash
   for i in {1..3}; do
     echo "=== Test Run $i ==="
     uv run pytest --tb=short -v
   done
   ```

2. **Run in parallel** (if pytest-xdist installed):
   ```bash
   uv run pytest -n auto --tb=short
   ```

3. **Run with coverage**:
   ```bash
   uv run pytest --cov=src --cov-report=html --cov-report=term
   ```

4. **Run CI workflow locally**:
   ```bash
   # Simulate CI environment
   uv run ruff check
   uv run mypy src/
   uv run pytest --tb=short
   ```

**Success Criteria**:
- ✅ 100% test pass rate (0 failures)
- ✅ Tests pass consistently (3 consecutive runs)
- ✅ Test coverage maintained or improved (>96%)
- ✅ All code quality checks pass (ruff, mypy)
- ✅ CI pipeline green
- ✅ Ready for v0.5.0 stable release

---

## Post-Fix Validation Checklist

### Code Quality
- [ ] All tests passing (`uv run pytest --tb=short`)
- [ ] Linting clean (`uv run ruff check`)
- [ ] Type checking clean (`uv run mypy src/`)
- [ ] Security scan clean (`uv run bandit -r src/`)
- [ ] No new warnings introduced

### Test Infrastructure
- [ ] Database fixtures properly implemented
- [ ] Test isolation verified (can run in any order)
- [ ] Cleanup logic working (no test pollution)
- [ ] Test documentation updated

### Documentation
- [ ] Fix details added to CHANGELOG.md
- [ ] Test setup instructions in tests/README.md
- [ ] Database requirements documented
- [ ] Known limitations documented (if any)

### Release Readiness
- [ ] All fixes merged to main branch
- [ ] CI/CD pipeline passing
- [ ] Version bumped to v0.5.0rc1 or v0.5.0
- [ ] Release notes prepared
- [ ] GitHub release created

---

## Implementation Timeline

### Sprint 1: Critical Fixes (Day 1)
- **Hour 1**: Phase 1 - Frontend generation bug fix
  - Investigate Path import issue
  - Implement fix
  - Run tests

- **Hour 2-3**: Phase 2 - Database integration setup
  - Create database fixtures
  - Deploy test schema
  - Verify integration tests

- **Hour 4**: Phase 3 - Validation
  - Full test suite run
  - Code quality checks
  - Documentation updates

### Sprint 2: Optimization & Documentation (Day 2)
- **Morning**: Test infrastructure improvements
  - Refactor database fixtures
  - Add test markers
  - Optimize slow tests

- **Afternoon**: Documentation
  - Update test documentation
  - Write contribution guide for testing
  - Create troubleshooting guide

---

## Risk Assessment

### Low Risk Fixes
✅ **Frontend Path bug** - Simple import issue, isolated change
✅ **Database fixture setup** - Standard pytest pattern, well-understood

### Potential Challenges
⚠️ **Database state management** - Ensure proper isolation between tests
⚠️ **Test data dependencies** - Contact entity might have complex relationships

### Mitigation Strategies
1. **Incremental testing**: Fix one test at a time, verify before moving on
2. **Rollback plan**: Keep git history clean, easy to revert
3. **Parallel development**: Frontend fixes independent of database fixes
4. **Continuous validation**: Run full suite after each fix

---

## Success Metrics

### Immediate Goals (v0.5.0b2)
- **Target**: 100% test pass rate (0 failures)
- **Current**: 99.6% (5 failures)
- **Gap**: 5 tests to fix

### Quality Gates
- ✅ **Unit Tests**: 100% passing
- ✅ **Integration Tests**: 100% passing (with database available)
- ✅ **Code Coverage**: Maintain >96%
- ✅ **Type Safety**: 100% mypy compliance
- ✅ **Code Quality**: 0 ruff violations

### Long-term Goals (v0.5.0 stable)
- **Performance**: Test suite completes in <30 seconds
- **Reliability**: 0 flaky tests (100% deterministic)
- **Maintainability**: Clear test organization and documentation
- **CI/CD**: All checks passing consistently

---

## Appendix A: Detailed Error Analysis

### Error 1-3: Database Integration Failures

**Error Message**:
```
psycopg.errors.UndefinedFunction: function app.create_contact(uuid, uuid, jsonb) does not exist
LINE 2: SELECT app.create_contact(
               ^
HINT: No function matches the given name and argument types.
```

**Location**: `tests/pytest/test_contact_integration.py`

**Affected Tests**:
1. `TestContactIntegration::test_create_contact_happy_path`
2. `TestContactIntegration::test_create_duplicate_contact_fails`
3. `TestContactIntegration::test_convert_to_customer`

**Root Cause Analysis**:
- Tests expect PostgreSQL function `app.create_contact(uuid, uuid, jsonb)`
- Function is generated by SpecQL from Contact entity YAML
- Test database doesn't have migrations applied
- No fixture to ensure schema deployment before tests run

**Impact**: High - Blocks integration testing of core CRUD functionality

**Complexity**: Medium - Requires database fixture infrastructure

**Priority**: P1 - Critical for release

---

### Error 4-5: Frontend Generation Failures

**Error Message**:
```
UnboundLocalError: cannot access local variable 'Path' where it is not associated with a value
Traceback:
  File "src/cli/generate.py", line 162, in entities
    frontend_dir = Path(output_frontend)
                   ^^^^
```

**Location**: `src/cli/generate.py:162`

**Affected Tests**:
1. `test_entities_with_frontend_generation`
2. `test_entities_with_frontend_and_impacts`

**Root Cause Analysis**:
- `Path` class not available in scope at line 162
- Likely causes:
  1. Missing `from pathlib import Path` import
  2. Conditional import that doesn't execute in test scenario
  3. Variable shadowing (local `Path` variable somewhere)

**Impact**: High - Breaks frontend code generation feature

**Complexity**: Low - Simple import/scoping fix

**Priority**: P0 - Trivial fix, should be done first

---

## Appendix B: Test Infrastructure Recommendations

### Current State
- 1122 passing tests (excellent coverage)
- Basic pytest setup
- Some database-dependent tests
- Limited fixture sharing

### Recommended Improvements

#### 1. Test Organization
```
tests/
├── unit/                    # Fast, no external dependencies
│   ├── parsers/
│   ├── generators/
│   └── utils/
├── integration/             # Requires external systems
│   ├── database/           # PostgreSQL required
│   ├── filesystem/         # File I/O
│   └── subprocess/         # CLI commands
├── e2e/                     # End-to-end workflows
└── conftest.py             # Shared fixtures
```

#### 2. Fixture Hierarchy
```python
# conftest.py (root level)

@pytest.fixture(scope="session")
def test_database():
    """Session-level database (created once)."""
    pass

@pytest.fixture(scope="function")
def clean_database(test_database):
    """Function-level transaction rollback."""
    pass

@pytest.fixture
def sample_entity():
    """Reusable entity YAML for tests."""
    return """
    entity: Contact
    schema: crm
    fields: [...]
    """
```

#### 3. Test Markers
```python
# Mark slow tests
@pytest.mark.slow
def test_large_dataset_processing():
    pass

# Mark database tests
@pytest.mark.database
def test_create_contact_integration():
    pass

# Mark external dependencies
@pytest.mark.requires_postgresql
@pytest.mark.requires_docker
def test_full_deployment():
    pass
```

#### 4. Configuration
```toml
# pyproject.toml

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

markers = [
    "unit: Fast unit tests with no external dependencies",
    "integration: Integration tests requiring external systems",
    "database: Tests requiring PostgreSQL",
    "slow: Slow-running tests (>1 second)",
    "skip_ci: Skip in CI environment",
]

# Run only fast tests by default
addopts = "-m 'not slow'"
```

---

## Appendix C: Command Reference

### Quick Fix Commands
```bash
# Fix Phase 1: Frontend generation
uv run pytest tests/unit/cli/test_generate.py -k frontend -v

# Fix Phase 2: Database integration
uv run pytest tests/pytest/test_contact_integration.py -v

# Fix Phase 3: Full validation
uv run pytest --tb=short

# Run specific categories
uv run pytest -m unit          # Fast unit tests only
uv run pytest -m integration   # Integration tests only
uv run pytest -m "not database" # Skip database tests
```

### Debugging Commands
```bash
# Run with full tracebacks
uv run pytest --tb=long

# Run with pdb on failure
uv run pytest --pdb

# Run specific test with verbose output
uv run pytest tests/pytest/test_contact_integration.py::TestContactIntegration::test_create_contact_happy_path -vvs

# Show test durations
uv run pytest --durations=10

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
```

### Database Debugging
```bash
# Check if test database exists
psql -l | grep specql_test

# Create test database
createdb specql_test

# Inspect test database state
psql specql_test -c "\dn"      # Schemas
psql specql_test -c "\dt app.*" # Tables
psql specql_test -c "\df app.*" # Functions

# Reset test database
dropdb specql_test && createdb specql_test
```

### Code Quality Commands
```bash
# Full quality check (same as CI)
uv run ruff check
uv run mypy src/
uv run bandit -r src/
uv run pytest --tb=short

# Auto-fix linting issues
uv run ruff check --fix

# Format code
uv run ruff format
```

---

## Conclusion

The SpecQL v0.5.0b1 release has achieved an excellent **99.6% test pass rate** with only 5 straightforward failures remaining. Both failure categories are:

1. **Well-understood**: Clear root causes identified
2. **Low-risk**: Standard bug fixes, no architectural changes needed
3. **Quick to fix**: Estimated 2-4 hours total implementation time

Following this phased TDD approach will ensure:
- ✅ Systematic, confidence-building fixes
- ✅ No regression introduction
- ✅ Improved test infrastructure
- ✅ Clear path to v0.5.0 stable release

**Recommended Action**: Execute Phase 1 (Frontend bug) immediately as it's a 15-minute fix, then proceed with Phase 2 (Database fixtures) and Phase 3 (Validation) to achieve 100% test pass rate.
