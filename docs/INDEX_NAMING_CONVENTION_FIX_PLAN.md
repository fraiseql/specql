# Index Naming Convention Fix Plan

## Executive Summary

**Problem**: Inconsistent index naming across codebase - some use `idx_{entity}_{field}` while convention should be `idx_tb_{entity}_{field}` to match table prefixes.

**Decision**: Include `tb_` prefix in ALL index names for consistency and clarity.

**Rationale**:
- Tables use `tb_` prefix (e.g., `tb_contact`, `tb_task`)
- Table views use `tv_` prefix (e.g., `tv_contact_active`)
- Indexes should mirror the object they index: `idx_tb_contact_email` clearly indicates it indexes `tb_contact.email`
- When we have both tables and views, this prevents ambiguity
- Future-proof: if we add indexes on table views, they'd be `idx_tv_{view}_{field}`

**Scope**: 26 failing tests due to partial implementation of this convention.

---

## Phase 1: Update Code Generators ✅ (COMPLETED)

### Files Modified:
1. ✅ `src/generators/table_generator.py` - Lines 199, 206, 212
   - Changed `idx_{entity}_id` → `idx_tb_{entity}_id`
   - Changed `idx_{entity}_{field}` → `idx_tb_{entity}_{field}` (FK indexes)
   - Changed `idx_{entity}_{field}` → `idx_tb_{entity}_{field}` (enum indexes)

2. ✅ `src/generators/index_generator.py` - Line 65
   - Changed `idx_{entity}_{field}` → `idx_tb_{entity}_{field}` (rich type indexes)

---

## Phase 2: Update Unit Tests (TODO)

### Test Files to Fix:

#### A. `tests/unit/schema/test_index_generation.py` (10 tests)
**Status**: Partially fixed (1/10 done)

Replace ALL occurrences of `idx_{entity}_` with `idx_tb_{entity}_`:

```bash
# Pattern to find and replace:
OLD: assert any("idx_{entity}_{field}" in idx for idx in indexes)
NEW: assert any("idx_tb_{entity}_{field}" in idx for idx in indexes)
```

**Specific fixes needed**:
- Line 22: ✅ `idx_contact_email` → `idx_tb_contact_email` (DONE)
- Line 35: `idx_page_url` → `idx_tb_page_url` (DONE)
- Line 50: `idx_location_coordinates` → `idx_tb_location_coordinates`
- Line 65: `idx_server_ip_address` → `idx_tb_server_ip_address`
- Line 80: `idx_device_mac` → `idx_tb_device_mac`
- Line 95: `idx_contact_phone` → `idx_tb_contact_phone`
- Line 110: `idx_article_slug` → `idx_tb_article_slug`
- Line 125: `idx_brand_color` → `idx_tb_brand_color`
- Line 140: `idx_product_price` → `idx_tb_product_price`

#### B. `tests/unit/generators/test_table_generator.py`
**Search for**: `idx_contact_`, `idx_task_`, etc.
**Replace with**: `idx_tb_contact_`, `idx_tb_task_`, etc.

**Expected assertions to update**:
```python
# Example pattern:
assert "CREATE INDEX idx_contact_id" in ddl
# Should become:
assert "CREATE INDEX idx_tb_contact_id" in ddl
```

#### C. `tests/unit/schema/test_table_generator_integration.py` (4 tests)
**Pattern**: Same as above - replace `idx_` with `idx_tb_`

**Specific tests**:
1. `test_generate_indexes_ddl_with_foreign_keys`
2. `test_generate_indexes_ddl_with_enum_fields`
3. `test_generate_complete_ddl_orchestration`
4. `test_rich_types_in_complete_ddl`

---

## Phase 3: Update Integration Tests (TODO)

### Test Files to Fix:

#### A. `tests/integration/schema/test_rich_types_postgres.py` (7 tests)
**Issue**: Database isolation + index naming

These tests fail with "DuplicateTable" errors AND will fail on index names once DB isolation is fixed.

**Tests affected**:
1. `test_email_constraint_validates_format`
2. `test_indexes_created_correctly` ← Primary index test
3. `test_comments_appear_in_postgresql`
4. `test_url_pattern_matching_with_gin_index`
5. `test_coordinates_gist_index_for_spatial_queries`
6. `test_enum_constraints_work`
7. `test_foreign_key_constraints_work`

**Action**:
1. Fix DB isolation first (see Phase 4)
2. Then update index assertions to use `idx_tb_` prefix

#### B. `tests/integration/fraiseql/test_mutation_annotations_e2e.py` (4 tests)
**Issue**: Similar DB isolation issues

**Tests affected**:
1. `test_annotations_apply_to_database`
2. `test_function_comments_contain_fraiseql_annotations`
3. `test_metadata_mapping_includes_impact_details`
4. `test_actions_without_impact_get_basic_annotations`

**Action**: Fix DB isolation (see Phase 4)

---

## Phase 4: Fix Database Isolation Issues (CRITICAL)

### Root Cause Analysis:

The integration tests are failing with:
```
psycopg.errors.DuplicateTable: relation "tb_contact" already exists
psycopg.errors.DuplicateObject: type "mutation_result" already exists
```

**Why this happens**:
- Tests execute DDL (CREATE TABLE, CREATE TYPE) directly
- The session-scoped `test_db_connection` fixture shares state
- The function-scoped `test_db` fixture does transaction rollback BUT:
  - DDL is NOT transactional in PostgreSQL (AUTO-COMMITS)
  - Rollback doesn't undo CREATE TABLE/TYPE statements

### Solution Options:

#### Option A: Use Temporary Schemas (RECOMMENDED)
```python
@pytest.fixture
def isolated_schema(test_db):
    """Create unique schema per test"""
    schema_name = f"test_{uuid.uuid4().hex[:8]}"
    with test_db.cursor() as cur:
        cur.execute(f"CREATE SCHEMA {schema_name}")
    test_db.commit()

    yield schema_name

    # Cleanup
    with test_db.cursor() as cur:
        cur.execute(f"DROP SCHEMA {schema_name} CASCADE")
    test_db.commit()
```

**Usage**:
```python
def test_something(test_db, isolated_schema):
    # Replace schema in DDL
    ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    cursor.execute(ddl)
```

#### Option B: Drop Objects After Test
```python
@pytest.fixture
def test_db_with_cleanup(test_db):
    """Clean up DDL objects after test"""
    objects_created = []

    yield test_db, objects_created

    # Drop all created objects
    with test_db.cursor() as cur:
        for obj_type, obj_name in reversed(objects_created):
            cur.execute(f"DROP {obj_type} IF EXISTS {obj_name} CASCADE")
    test_db.commit()
```

#### Option C: Use Test Database Per Session (SLOWEST)
- Create/drop entire test database per test
- Very slow, not recommended

### Recommended Approach: Option A + Smart Parsing

1. Create `isolated_schema` fixture in `tests/conftest.py`
2. Update integration tests to:
   - Use isolated schema
   - Parse DDL to replace schema names
   - Execute DDL in isolated schema
3. Schema is automatically dropped after test

**Files to update**:
- `tests/conftest.py` - Add `isolated_schema` fixture
- `tests/integration/schema/test_rich_types_postgres.py` - Use fixture
- `tests/integration/fraiseql/test_mutation_annotations_e2e.py` - Use fixture
- `tests/integration/fraiseql/test_rich_type_autodiscovery.py` - Use fixture

---

## Phase 5: Update Action Orchestrator Test (TODO)

### File: `tests/unit/actions/test_action_orchestrator.py`

**Test**: `test_compile_multi_entity_action_basic_structure`

**Issue**: Unknown - need to investigate

**Action**:
1. Run test in isolation: `uv run pytest tests/unit/actions/test_action_orchestrator.py::TestActionOrchestrator::test_compile_multi_entity_action_basic_structure -xvs`
2. Read error message
3. Determine if it's index naming or something else
4. Fix accordingly

---

## Phase 6: Verification & Cleanup (TODO)

### A. Run Full Test Suite
```bash
uv run pytest --tb=short -v
```

**Expected result**:
```
============= 874 passed, 3 skipped in ~20s =============
```

### B. Update Documentation

**Files to update**:
1. `.claude/CLAUDE.md` - Document index naming convention
2. `docs/archive/architecture/NAMING_CONVENTIONS.md` - Add index naming rules
3. `GETTING_STARTED.md` - Add example with indexes

**Convention to document**:
```markdown
## Index Naming Convention

**Format**: `idx_{table_prefix}_{entity}_{field}`

**Examples**:
- Tables: `idx_tb_contact_email`, `idx_tb_task_status`
- Table Views: `idx_tv_contact_active_email` (future)

**Rationale**: Mirrors table naming to prevent ambiguity when indexing both tables and views.
```

### C. Regenerate Schema Files

If any committed schema files exist in `db/schema/`, regenerate them:

```bash
# Regenerate all schema files
specql generate entities/*.yaml --output db/schema/
```

---

## Test Execution Strategy

### Run tests in phases to verify progress:

```bash
# Phase 2: Unit tests
uv run pytest tests/unit/schema/test_index_generation.py -v
uv run pytest tests/unit/generators/test_table_generator.py -v
uv run pytest tests/unit/schema/test_table_generator_integration.py -v

# Phase 3 + 4: Integration tests (after DB isolation fix)
uv run pytest tests/integration/schema/test_rich_types_postgres.py -v
uv run pytest tests/integration/fraiseql/ -v

# Phase 5: Action orchestrator
uv run pytest tests/unit/actions/test_action_orchestrator.py -v

# Phase 6: Full suite
uv run pytest --tb=short
```

---

## Success Criteria

✅ **All tests passing**: 874+ passed, 3 skipped, 0 failed, 0 errors
✅ **Consistent naming**: All indexes use `idx_tb_` or `idx_tv_` prefix
✅ **DB isolation**: Integration tests don't interfere with each other
✅ **Documentation**: Convention clearly documented
✅ **Schema files**: Regenerated with correct naming

---

## Estimated Effort

- **Phase 2**: 30 minutes (systematic find/replace in tests)
- **Phase 3**: 15 minutes (update assertions)
- **Phase 4**: 45 minutes (implement isolated_schema fixture)
- **Phase 5**: 15 minutes (investigate + fix)
- **Phase 6**: 30 minutes (verification + docs)

**Total**: ~2.5 hours

---

## Current Status

- ✅ Phase 1: COMPLETED (code generators fixed)
- 🔄 Phase 2: IN PROGRESS (2/10 tests in test_index_generation.py fixed)
- ⏳ Phase 3: PENDING
- ⏳ Phase 4: PENDING (CRITICAL PATH)
- ⏳ Phase 5: PENDING
- ⏳ Phase 6: PENDING

**Next Action**: Complete Phase 2 OR prioritize Phase 4 (DB isolation) first since it blocks Phase 3.

---

## Notes for Agent

1. **Convention is FINAL**: Always use `idx_tb_` prefix for table indexes
2. **DB isolation is critical**: Without it, integration tests will always fail
3. **Test in phases**: Don't try to fix everything at once
4. **Verify incrementally**: Run relevant tests after each phase
5. **Document changes**: Update CLAUDE.md when done

**Quick Command Reference**:
```bash
# Run specific test file
uv run pytest tests/unit/schema/test_index_generation.py -v

# Run all unit tests
uv run pytest tests/unit/ -v

# Run all tests
uv run pytest --tb=short

# Check test count
uv run pytest --collect-only -q | tail -3
```
