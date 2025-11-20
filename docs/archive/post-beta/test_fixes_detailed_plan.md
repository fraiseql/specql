# Detailed Plan: Fix Conftest, Errors, and Failing Tests

**Date**: 2025-11-18
**Status**: Ready for Implementation
**Estimated Time**: 6-10 hours
**Current Failures**: 21 failed + 13 errors = 34 issues

---

## 📊 Problem Summary

### Issue Categories

| Category | Count | Type | Root Cause |
|----------|-------|------|------------|
| **Seed Generator** | 8 | FAILED | Missing `faker` dependency |
| **Rich Types PostgreSQL** | 5 | FAILED | Duplicate index creation (DDL isolation) |
| **FraiseQL Autodiscovery** | 8 | ERROR | Duplicate index creation (DDL isolation) |
| **Confiture Integration** | 1 | FAILED | Confiture config parsing error |
| **Total** | **22** | - | - |

---

## 🎯 Phase 1: Dependency Issues (30 min)

### Priority: **CRITICAL** | Difficulty: **EASY** | Impact: **+8 tests**

### Issue 1.1: Missing Faker Dependency

**Problem**: All seed generator tests fail with:
```
ImportError: Test data generation requires faker.
Install with: pip install specql[testing]
```

**Failing Tests** (8):
- `test_generate_basic_entity`
- `test_generate_tenant_scoped_entity`
- `test_generate_with_fk_resolution`
- `test_generate_with_group_leader`
- `test_generate_with_overrides`
- `test_generate_batch`
- `test_generate_with_sequence_context`
- `test_skip_group_dependent_fields`

**Root Cause**: Optional dependency `faker` not installed in test environment

#### Solution: Add Faker to Test Dependencies

**File**: `pyproject.toml`

**Current** (line ~40):
```toml
[project.optional-dependencies]
testing = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
]
```

**Fix**: Add `faker` to testing dependencies
```toml
[project.optional-dependencies]
testing = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "faker>=20.0.0",  # NEW: Required for seed data generation
]
```

**Alternative**: Add to main dependencies if seed generation is core feature
```toml
dependencies = [
    # ... existing deps ...
    "faker>=20.0.0",  # Seed data generation
]
```

#### Implementation Steps

1. **Update pyproject.toml**
   ```bash
   # Add faker to [project.optional-dependencies.testing]
   ```

2. **Sync dependencies**
   ```bash
   uv sync --extra testing
   # OR
   uv pip install faker
   ```

3. **Verify installation**
   ```bash
   uv run python -c "from faker import Faker; print(f'✅ Faker {Faker().VERSION} installed')"
   ```

4. **Test**
   ```bash
   uv run pytest tests/unit/testing/test_seed_generator.py -v
   ```

**Expected Result**: All 8 seed generator tests should pass ✅

**Time**: 30 minutes

---

## 🎯 Phase 2: Database Isolation Issues (2-3 hours)

### Priority: **HIGH** | Difficulty: **MEDIUM** | Impact: **+13 tests**

### Issue 2.1: Duplicate Index Creation

**Problem**: Integration tests create duplicate indexes when run sequentially, causing:
```
psycopg.errors.DuplicateTable: relation "idx_tb_contact_email" already exists
psycopg.errors.DuplicateTable: relation "idx_tb_company_domain" already exists
```

**Failing Tests** (13):
- Rich types PostgreSQL: 5 tests
- FraiseQL autodiscovery: 8 tests

**Root Cause Analysis**:

1. **Schema Isolation Works**: Tests use `isolated_schema` fixture correctly
2. **Index Problem**: Indexes are created with **global names** across schemas
3. **PostgreSQL Behavior**: Index names must be unique **per schema**

**Example DDL Issue**:
```sql
-- Test 1 creates in schema test_abc123:
CREATE SCHEMA test_abc123;
CREATE TABLE test_abc123.tb_contact (...);
CREATE INDEX idx_tb_contact_email ON test_abc123.tb_contact (email);  -- ✅

-- Test 2 creates in schema test_def456:
CREATE SCHEMA test_def456;
CREATE TABLE test_def456.tb_contact (...);
CREATE INDEX idx_tb_contact_email ON test_def456.tb_contact (email);  -- ❌ ERROR: already exists!
```

**Why This Happens**: PostgreSQL index names are global within the database, NOT schema-scoped.

#### Solution 2.1.1: Schema-Qualified Index Names

**Approach**: Prefix index names with schema name OR use schema-qualified syntax

**Option A**: Modify index generation to include schema prefix

**File**: `src/generators/schema/table_generator.py`

**Current**:
```python
def _generate_index_name(self, table_name: str, field_name: str) -> str:
    """Generate index name following conventions"""
    return f"idx_{table_name}_{field_name}"
```

**Fix**:
```python
def _generate_index_name(self, schema_name: str, table_name: str, field_name: str) -> str:
    """Generate index name following conventions with schema prefix"""
    # For isolated test schemas, include schema in index name
    if schema_name and schema_name.startswith("test_"):
        return f"idx_{schema_name}_{table_name}_{field_name}"
    else:
        # Production: standard naming
        return f"idx_{table_name}_{field_name}"
```

**Option B**: Use `DROP INDEX IF EXISTS` before creation (safer for tests)

**File**: `src/generators/schema/table_generator.py`

Add cleanup method:
```python
def generate_index_with_cleanup(self, schema: str, table: str, field: str) -> str:
    """Generate index DDL with cleanup for test isolation"""
    index_name = self._generate_index_name(table, field)

    return f"""
-- Drop index if exists (for test isolation)
DROP INDEX IF EXISTS {schema}.{index_name};

-- Create index
CREATE INDEX {index_name} ON {schema}.{table} USING btree ({field});
"""
```

**Option C**: Enhanced fixture cleanup (RECOMMENDED)

**File**: `tests/conftest.py` (line 192+)

**Current**:
```python
@pytest.fixture
def isolated_schema(test_db_connection):
    """Create unique schema per test for DDL isolation"""
    schema_name = f"test_{uuid.uuid4().hex[:8]}"

    with test_db_connection.cursor() as cur:
        cur.execute(f"CREATE SCHEMA {schema_name}")
    test_db_connection.commit()

    yield schema_name

    # Cleanup: Drop schema and all its objects
    try:
        with test_db_connection.cursor() as cur:
            cur.execute(f"DROP SCHEMA {schema_name} CASCADE")
        test_db_connection.commit()
    except Exception:
        test_db_connection.rollback()
```

**Fix**: Add index cleanup before schema drop
```python
@pytest.fixture
def isolated_schema(test_db_connection):
    """Create unique schema per test for DDL isolation"""
    schema_name = f"test_{uuid.uuid4().hex[:8]}"

    # Create schema
    with test_db_connection.cursor() as cur:
        cur.execute(f"CREATE SCHEMA {schema_name}")
    test_db_connection.commit()

    yield schema_name

    # Cleanup: Drop all indexes in schema first, then drop schema
    try:
        with test_db_connection.cursor() as cur:
            # Find all indexes in this schema
            cur.execute(f"""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = %s
            """, (schema_name,))

            indexes = cur.fetchall()

            # Drop each index explicitly
            for (idx_name,) in indexes:
                try:
                    cur.execute(f"DROP INDEX IF EXISTS {schema_name}.{idx_name}")
                except Exception:
                    pass  # Ignore individual index drop failures

            # Drop schema and remaining objects
            cur.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")

        test_db_connection.commit()
    except Exception as e:
        test_db_connection.rollback()
        print(f"⚠️  Schema cleanup failed for {schema_name}: {e}")
```

#### Solution 2.1.2: Test-Specific Index Names (BEST SOLUTION)

**File**: `tests/integration/schema/test_rich_types_postgres.py`

**Current** (line 45):
```python
def test_email_constraint_validates_format(test_db, isolated_schema, table_generator):
    entity = create_contact_entity_with_email()
    ddl = table_generator.generate_complete_ddl(entity)

    # Replace schema references
    ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    ddl = ddl.replace("crm.", f"{isolated_schema}.")

    cursor = test_db.cursor()
    cursor.execute(ddl)  # ❌ Fails with duplicate index
```

**Fix**: Make index names schema-unique
```python
def test_email_constraint_validates_format(test_db, isolated_schema, table_generator):
    entity = create_contact_entity_with_email()
    ddl = table_generator.generate_complete_ddl(entity)

    # Replace schema references
    ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    ddl = ddl.replace("crm.", f"{isolated_schema}.")

    # Make index names unique by prefixing with schema (for test isolation)
    ddl = ddl.replace("CREATE INDEX idx_", f"CREATE INDEX {isolated_schema}_idx_")

    cursor = test_db.cursor()
    cursor.execute(ddl)  # ✅ Should succeed
    test_db.commit()
```

**Apply to All Integration Tests**:
- `tests/integration/schema/test_rich_types_postgres.py` (5 tests)
- `tests/integration/fraiseql/test_rich_type_autodiscovery.py` (8 tests via fixture)

#### Implementation Steps

**Step 1**: Update `isolated_schema` fixture cleanup (30 min)
```bash
# Edit tests/conftest.py
# Add index cleanup logic as shown above
```

**Step 2**: Add index name prefixing to integration tests (1 hour)
```bash
# Edit tests/integration/schema/test_rich_types_postgres.py
# Add: ddl = ddl.replace("CREATE INDEX idx_", f"CREATE INDEX {isolated_schema}_idx_")
# to all 5 tests

# Edit tests/integration/fraiseql/test_rich_type_autodiscovery.py
# Add to test_db_with_rich_types fixture (line ~40)
```

**Step 3**: Test rich types PostgreSQL (30 min)
```bash
uv run pytest tests/integration/schema/test_rich_types_postgres.py -v
```

**Step 4**: Test FraiseQL autodiscovery (30 min)
```bash
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v
```

**Expected Result**: All 13 integration tests should pass ✅

**Time**: 2-3 hours

---

## 🎯 Phase 3: Confiture Integration Error (2-3 hours)

### Priority: **MEDIUM** | Difficulty: **HARD** | Impact: **+1 test**

### Issue 3.1: Confiture Config Parsing Error

**Problem**: Confiture migration fails with:
```
❌ Error: 'str' object has no attribute 'get'
```

**Failing Test**: `test_confiture_migrate_up_and_down`

**Error Context**:
```bash
$ uv run confiture migrate up --config db/environments/test.yaml
❌ Error: 'str' object has no attribute 'get'
```

**Root Cause**: Confiture is receiving a string when it expects a dict/object

#### Investigation Steps

**Step 1**: Check Confiture config file
```bash
cat db/environments/test.yaml
```

**Step 2**: Check Confiture CLI parsing
```bash
# Look for config loading code in confiture package
uv run python -c "
import yaml
with open('db/environments/test.yaml') as f:
    config = yaml.safe_load(f)
    print(type(config))
    print(config)
"
```

**Step 3**: Trace the error
```bash
uv run confiture migrate up --config db/environments/test.yaml --verbose 2>&1
```

#### Possible Root Causes

**Cause A**: YAML file contains string instead of dict
```yaml
# BAD (string)
database: "postgresql://localhost/specql_test"

# GOOD (dict)
database:
  host: localhost
  port: 5432
  name: specql_test
```

**Cause B**: Confiture CLI not loading YAML correctly
```python
# BAD
config = open('config.yaml').read()  # Returns string

# GOOD
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)  # Returns dict
```

**Cause C**: Config schema mismatch
```python
# Confiture expects:
config['database']['host']  # But config['database'] is a string
```

#### Solution 3.1.1: Fix YAML Config Structure

**File**: `db/environments/test.yaml`

**Check current structure**:
```bash
cat db/environments/test.yaml
```

**Expected structure** (if using database dict):
```yaml
database:
  host: localhost
  port: 5432
  dbname: specql_test
  user: postgres
  password: ""

migrations_dir: db/migrations
schema_version_table: schema_migrations
```

**Fix**: Ensure config matches expected schema

#### Solution 3.1.2: Fix Confiture CLI Config Loading

**File**: Search for confiture config loading code

```bash
# Find confiture entry point
grep -r "def migrate" --include="*.py" | grep confiture

# Check config loading
grep -r "\.get\(" --include="*.py" | grep confiture
```

**Fix**: Update config loading to handle both string and dict

```python
# Before
db_config = config['database']  # Assumes dict
host = db_config.get('host')    # ❌ Fails if db_config is string

# After
db_config = config['database']
if isinstance(db_config, str):
    # Parse connection string
    import urllib.parse
    parsed = urllib.parse.urlparse(db_config)
    db_config = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'dbname': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password,
    }

host = db_config.get('host')  # ✅ Works
```

#### Solution 3.1.3: Update Test Config

**File**: `tests/integration/test_confiture_integration.py`

**Check test setup** (around line 292):
```python
result = subprocess.run(
    ["uv", "run", "confiture", "migrate", "up", "--config", "db/environments/test.yaml"],
    capture_output=True,
    text=True,
)
```

**Ensure** `db/environments/test.yaml` exists and is valid:

```bash
# Create if missing
mkdir -p db/environments
cat > db/environments/test.yaml << 'EOF'
database:
  host: localhost
  port: 5432
  dbname: specql_test
  user: ${USER}
  password: ""

migrations_dir: db/migrations
schema_version_table: schema_migrations
apply_order: [framework, domain, tenant]
EOF
```

#### Implementation Steps

**Step 1**: Verify config file exists and structure (15 min)
```bash
cat db/environments/test.yaml
# If missing or malformed, create proper structure
```

**Step 2**: Trace confiture error with verbose output (30 min)
```bash
# Add debugging to confiture or run with traceback
uv run python -c "
import sys
import traceback
try:
    from confiture.cli import migrate_command
    migrate_command(['up', '--config', 'db/environments/test.yaml'])
except Exception as e:
    traceback.print_exc()
"
```

**Step 3**: Fix identified issue (1 hour)
- If YAML structure: Fix config file
- If Confiture code: Update CLI parsing
- If test issue: Update test expectations

**Step 4**: Test migration (30 min)
```bash
# Test confiture directly
uv run confiture migrate up --config db/environments/test.yaml

# Test via pytest
uv run pytest tests/integration/test_confiture_integration.py::TestConfitureIntegration::test_confiture_migrate_up_and_down -v
```

**Expected Result**: Confiture integration test should pass ✅

**Time**: 2-3 hours

---

## 🎯 Phase 4: Verification & Documentation (1 hour)

### Priority: **LOW** | Difficulty: **EASY** | Impact: **Quality**

### Task 4.1: Full Test Suite Run

**Run all tests** to ensure fixes don't break anything:
```bash
# Full suite
uv run pytest -v

# Just the fixed tests
uv run pytest \
  tests/unit/testing/test_seed_generator.py \
  tests/integration/schema/test_rich_types_postgres.py \
  tests/integration/fraiseql/test_rich_type_autodiscovery.py \
  tests/integration/test_confiture_integration.py \
  -v
```

**Expected**:
- Seed generator: 8/8 passing ✅
- Rich types PostgreSQL: 5/5 passing ✅
- FraiseQL autodiscovery: 8/8 passing ✅
- Confiture integration: 1/1 passing ✅
- **Total**: +22 tests passing

### Task 4.2: Update Test Documentation

**File**: `tests/README.md` (create if missing)

```markdown
# SpecQL Test Suite

## Running Tests

### All Tests
uv run pytest

### Unit Tests Only
uv run pytest tests/unit/

### Integration Tests (Requires PostgreSQL)
uv run pytest tests/integration/ -m database

### Skip Database Tests
uv run pytest -m "not database"

## Test Dependencies

### Required
- pytest>=8.0.0
- pytest-cov>=4.1.0

### Optional (for seed generation)
- faker>=20.0.0

Install with:
uv sync --extra testing

## Database Setup

Integration tests require PostgreSQL:

1. Create database:
   createdb specql_test

2. Set environment variables (optional):
   export TEST_DB_HOST=localhost
   export TEST_DB_PORT=5432
   export TEST_DB_NAME=specql_test
   export TEST_DB_USER=$USER

3. Run tests:
   uv run pytest tests/integration/ -v

## Test Isolation

Integration tests use isolated schemas (test_<uuid>) to prevent conflicts.
Each test gets a unique schema that's dropped after the test.
```

### Task 4.3: Create Summary Document

**File**: `docs/post_beta_plan/test_fixes_summary.md`

```markdown
# Test Fixes Summary - 2025-11-18

## Issues Fixed

### 1. Seed Generator Tests (8 tests)
**Problem**: Missing faker dependency
**Solution**: Added faker>=20.0.0 to testing dependencies
**Result**: ✅ All 8 tests passing

### 2. Rich Types PostgreSQL (5 tests)
**Problem**: Duplicate index names across isolated schemas
**Solution**: Prefix index names with schema in tests
**Result**: ✅ All 5 tests passing

### 3. FraiseQL Autodiscovery (8 tests)
**Problem**: Duplicate index names in fixture setup
**Solution**: Schema-prefixed index names in test fixture
**Result**: ✅ All 8 tests passing

### 4. Confiture Integration (1 test)
**Problem**: Config parsing error ('str' has no attribute 'get')
**Solution**: Fixed YAML config structure / CLI parsing
**Result**: ✅ Test passing

## Total Impact
- **Before**: 1456 passing, 21 failed, 13 errors
- **After**: 1478 passing, 0 failed, 0 errors
- **Improvement**: +22 tests (100% success rate)

## Files Modified
- pyproject.toml (faker dependency)
- tests/conftest.py (improved cleanup)
- tests/integration/schema/test_rich_types_postgres.py (index prefixing)
- tests/integration/fraiseql/test_rich_type_autodiscovery.py (fixture fix)
- db/environments/test.yaml (config structure)
```

**Time**: 1 hour

---

## 📊 Timeline Summary

| Phase | Tasks | Time | Result |
|-------|-------|------|--------|
| **Phase 1** | Faker dependency | 30 min | +8 tests |
| **Phase 2** | Index isolation | 2-3 hours | +13 tests |
| **Phase 3** | Confiture config | 2-3 hours | +1 test |
| **Phase 4** | Verification | 1 hour | Quality |
| **Total** | **4 phases** | **6-8 hours** | **+22 tests** |

---

## ✅ Success Criteria

1. ✅ All seed generator tests pass (faker installed)
2. ✅ All rich types integration tests pass (no duplicate indexes)
3. ✅ All FraiseQL autodiscovery tests pass (proper isolation)
4. ✅ Confiture integration test passes (config valid)
5. ✅ No regressions in existing tests
6. ✅ Test suite at 100% pass rate (1478+ passing)

---

## 🎯 Execution Order

### Recommended: Sequential
1. **Start with Phase 1** (quick win, 30 min)
2. **Then Phase 2** (most complex, 2-3 hours)
3. **Then Phase 3** (needs investigation, 2-3 hours)
4. **Finish with Phase 4** (verification, 1 hour)

### Alternative: Parallel (with 2 devs)
- **Dev 1**: Phases 1 + 2 (dependencies + isolation)
- **Dev 2**: Phase 3 (confiture)
- **Together**: Phase 4 (verification)

---

## 🚨 Risk Mitigation

### Risk 1: Index naming changes affect production
**Mitigation**: Changes only apply when `schema.startswith("test_")`
**Verification**: Run production schema generation and verify no changes

### Risk 2: Faker adds unwanted dependency
**Mitigation**: Keep in `[optional-dependencies.testing]` not main deps
**Verification**: Install without extras, ensure core functionality works

### Risk 3: Confiture fix requires deep debugging
**Mitigation**: Allocate 3 hours; if blocked, create minimal test config
**Fallback**: Skip confiture test, document as known issue

---

## 📝 Notes

- **Database Required**: Phases 2-3 require running PostgreSQL
- **Clean State**: Run `DROP DATABASE specql_test; CREATE DATABASE specql_test;` before Phase 2
- **Parallel Safe**: Phase 1 can be done independently
- **Documentation**: Update as you go to capture learnings

---

**Generated**: 2025-11-18
**Author**: Claude Code
**Status**: Ready for Implementation
**Next Step**: Execute Phase 1 (faker dependency)
