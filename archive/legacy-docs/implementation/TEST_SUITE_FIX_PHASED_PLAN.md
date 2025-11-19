# Test Suite Fix - Phased Implementation Plan

**Project**: printoptim_backend_poc
**Task**: Fix 27 remaining test failures (18 failed, 9 errors)
**Complexity**: Complex | **Phased TDD Approach**
**Document Created**: 2025-11-09
**Current Status**: 880/910 tests passing (96.7%)

---

## Executive Summary

Fix remaining test failures to achieve 100% test suite pass rate. Current failures fall into three categories:

1. **Rich Type Validation Issues** (13 failures) - Minor description string mismatches in scalar type definitions
2. **Missing Database Dependencies** (9 errors) - Test fixtures missing required tables/types
3. **Schema Generation Gaps** (5 failures) - Rich type CHECK constraints not being generated

**Root Causes**:
- Recent refactoring of scalar type descriptions added "(validated format, ...)" text
- Integration tests expect database tables that don't exist in fixtures
- Table generator not applying CHECK constraints for rich scalar types

**Success Criteria**:
- 910/910 tests passing (100%)
- No skipped tests (except intentional DB-dependent tests)
- All rich types generate proper constraints
- All integration tests have proper fixtures

---

## Current State Analysis

### Test Failure Breakdown

#### Category 1: Scalar Type Description Mismatches (13 failures)
```
FAILED tests/unit/core/test_scalar_types.py::test_mime_type_validation
FAILED tests/unit/core/test_scalar_types.py::test_stock_symbol_validation
FAILED tests/unit/core/test_scalar_types.py::test_cusip_validation
FAILED tests/unit/core/test_scalar_types.py::test_sedol_validation
FAILED tests/unit/core/test_scalar_types.py::test_domain_name_validation
FAILED tests/unit/core/test_scalar_types.py::test_api_key_validation
FAILED tests/unit/core/test_scalar_types.py::test_hash_sha256_validation
```

**Issue**: Tests expect old description format, but code has new format with "(validated format, ...)"

**Example**:
```python
# Expected: "MIME type (e.g., application/json, image/png)"
# Actual:   "MIME type (validated format, e.g., application/json, image/png)"
```

#### Category 2: Missing Database Fixtures (9 errors)
```
ERROR tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_email_field_has_check_constraint
ERROR tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_email_field_has_comment
ERROR tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_url_field_has_check_constraint
ERROR tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_phone_field_has_check_constraint
ERROR tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_money_field_uses_numeric_type
ERROR tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_ipaddress_field_uses_inet_type
ERROR tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_coordinates_field_uses_point_type
ERROR tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_all_rich_type_fields_have_comments
ERROR tests/integration/test_composite_hierarchical_e2e.py::TestCompositeHierarchicalE2E::test_allocation_composite_identifier
```

**Issue**: Test fixtures reference `tb_company` and other tables that don't exist in test database setup

**Example**:
```
psycopg.errors.UndefinedTable: relation "test_3a92bda3.tb_company" does not exist
```

#### Category 3: Rich Type CHECK Constraints Not Generated (5 failures)
```
FAILED tests/unit/schema/test_rich_type_ddl.py::test_slug_generates_text_with_url_safe_constraint
FAILED tests/unit/schema/test_table_generator_integration.py::test_generate_complete_ddl_orchestration
FAILED tests/unit/schema/test_table_generator_integration.py::test_rich_types_in_complete_ddl
FAILED tests/integration/schema/test_rich_types_postgres.py::test_url_pattern_matching_with_gin_index
FAILED tests/integration/schema/test_rich_types_postgres.py::test_foreign_key_constraints_work
```

**Issue**: Table generator creates `slug TEXT` without `CHECK` constraint for validation pattern

**Example**:
```sql
-- Generated (WRONG):
slug TEXT,

-- Expected (RIGHT):
slug TEXT CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
```

#### Category 4: FraiseQL Mutation Annotations (4 failures)
```
FAILED tests/integration/fraiseql/test_mutation_annotations_e2e.py::TestMutationAnnotationsEndToEnd::test_annotations_apply_to_database
FAILED tests/integration/fraiseql/test_mutation_annotations_e2e.py::TestMutationAnnotationsEndToEnd::test_function_comments_contain_fraiseql_annotations
FAILED tests/integration/fraiseql/test_mutation_annotations_e2e.py::TestMutationAnnotationsEndToEnd::test_metadata_mapping_includes_impact_details
FAILED tests/integration/fraiseql/test_mutation_annotations_e2e.py::TestMutationAnnotationsEndToEnd::test_actions_without_impact_get_basic_annotations
```

**Issue**: Missing input types for mutations
```
psycopg.errors.UndefinedObject: type test_ca1a1765.type_create_contact_input does not exist
```

#### Category 5: Other Issues (1 failure)
```
FAILED tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_snapshot
FAILED tests/unit/actions/test_validation_steps.py::TestValidationSteps::test_pattern_match_validation
```

**Issue**: Snapshot mismatch or validation logic change

---

## PHASE 1: Fix Scalar Type Description Mismatches

**Objective**: Update test expectations to match new description format

**Estimated Time**: 30 minutes

### TDD Cycle 1.1: Update scalar type test expectations

#### 🔴 RED: Tests currently failing
**Test file**: `tests/unit/core/test_scalar_types.py`

**Current state**: 7 tests failing due to description mismatch

#### 🟢 GREEN: Update test expectations

**Files to modify**:
- `tests/unit/core/test_scalar_types.py`

**Approach**:
Two options:
1. **Option A (Recommended)**: Update `src/core/scalar_types.py` to remove "(validated format, ...)" additions
2. **Option B**: Update all test assertions to expect new format

**Recommended: Option A** - Keep descriptions simple and consistent with original design

**Implementation**:
```python
# In src/core/scalar_types.py
# BEFORE:
"mimeType": ScalarTypeDef(
    name="mimeType",
    postgres_type=PostgreSQLType.TEXT,
    fraiseql_scalar_name="MimeType",
    validation_pattern=r"^[a-zA-Z]...",
    description="MIME type (validated format, e.g., application/json, image/png)",  # ❌
    ...
),

# AFTER:
"mimeType": ScalarTypeDef(
    name="mimeType",
    postgres_type=PostgreSQLType.TEXT,
    fraiseql_scalar_name="MimeType",
    validation_pattern=r"^[a-zA-Z]...",
    description="MIME type (e.g., application/json, image/png)",  # ✅
    ...
),
```

**Affected types**:
- mimeType
- stockSymbol
- cusip
- sedol
- domainName
- apiKey
- hashSHA256

**Run test**:
```bash
uv run pytest tests/unit/core/test_scalar_types.py -v
```

#### 🔧 REFACTOR: Ensure consistency
- Verify all scalar type descriptions follow same format
- No "(validated format, ...)" additions
- Keep descriptions concise and informative

#### ✅ QA: All scalar type tests pass
```bash
uv run pytest tests/unit/core/test_scalar_types.py -v
# Expected: 46 tests passing
```

**Checklist**:
- [ ] All 7 failing scalar type tests now pass
- [ ] Description format consistent across all 49 scalar types
- [ ] No regression in other tests
- [ ] Documentation still accurate

---

## PHASE 2: Fix Rich Type CHECK Constraint Generation

**Objective**: Ensure table generator applies CHECK constraints for rich scalar types

**Estimated Time**: 2-3 hours

### TDD Cycle 2.1: Implement CHECK constraint generation

#### 🔴 RED: Tests expecting CHECK constraints
**Test file**: `tests/unit/schema/test_rich_type_ddl.py::test_slug_generates_text_with_url_safe_constraint`

**Current failure**:
```sql
-- Generated:
slug TEXT,

-- Expected:
slug TEXT CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
```

#### 🟢 GREEN: Implement constraint generation

**Files to modify**:
- `src/generators/table_generator.py` - Add CHECK constraint logic
- `src/generators/constraint_generator.py` - Handle rich type constraints

**Root cause analysis**:
```bash
# Check current table_generator implementation
grep -n "CHECK" src/generators/table_generator.py
```

**Expected**: Table generator should:
1. Detect rich scalar types
2. Get validation pattern from `scalar_types.SCALAR_TYPES`
3. Generate `CHECK (field_name ~ 'pattern')` constraint

**Implementation**:
```python
# In src/generators/table_generator.py

from src.core.scalar_types import is_scalar_type, get_scalar_type

def _generate_field_definition(field: FieldDefinition) -> str:
    """Generate PostgreSQL field definition with constraints"""

    parts = []

    # Get PostgreSQL type
    if is_scalar_type(field.type_name):
        scalar_def = get_scalar_type(field.type_name)
        pg_type = scalar_def.get_postgres_type_with_precision()
    else:
        pg_type = _get_basic_postgres_type(field.type_name)

    parts.append(f"{field.name} {pg_type}")

    # Add NOT NULL if required
    if not field.nullable:
        parts.append("NOT NULL")

    # Add CHECK constraint for validated scalar types
    if is_scalar_type(field.type_name):
        scalar_def = get_scalar_type(field.type_name)
        if scalar_def.validation_pattern:
            # Use ~ for regex matching in PostgreSQL
            parts.append(f"CHECK ({field.name} ~ '{scalar_def.validation_pattern}')")

        # Add range constraints for numeric types
        if scalar_def.min_value is not None or scalar_def.max_value is not None:
            range_parts = []
            if scalar_def.min_value is not None:
                range_parts.append(f"{field.name} >= {scalar_def.min_value}")
            if scalar_def.max_value is not None:
                range_parts.append(f"{field.name} <= {scalar_def.max_value}")
            parts.append(f"CHECK ({' AND '.join(range_parts)})")

    return " ".join(parts)
```

**Run test**:
```bash
uv run pytest tests/unit/schema/test_rich_type_ddl.py::test_slug_generates_text_with_url_safe_constraint -v
```

#### 🔧 REFACTOR: Handle all rich type constraints

**Additional test cases**:
```bash
# Test email constraint
uv run pytest tests/unit/schema/test_rich_type_ddl.py -k email -v

# Test phone constraint
uv run pytest tests/unit/schema/test_rich_type_ddl.py -k phone -v

# Test money range constraint
uv run pytest tests/unit/schema/test_rich_type_ddl.py -k money -v

# Test percentage range constraint
uv run pytest tests/unit/schema/test_rich_type_ddl.py -k percentage -v
```

**Edge cases to handle**:
1. Nullable fields with constraints (CHECK allows NULL)
2. Multiple constraints on same field (min/max + pattern)
3. Regex escaping for PostgreSQL
4. Case-insensitive patterns (use `~*` operator)

#### ✅ QA: All rich type DDL tests pass
```bash
# Run all rich type DDL tests
uv run pytest tests/unit/schema/test_rich_type_ddl.py -v

# Run table generator integration tests
uv run pytest tests/unit/schema/test_table_generator_integration.py -v

# Verify complete DDL generation
uv run pytest tests/unit/schema/ -v
```

**Checklist**:
- [ ] slug generates CHECK constraint
- [ ] email generates CHECK constraint
- [ ] phone generates CHECK constraint
- [ ] url generates CHECK constraint
- [ ] money generates range CHECK constraint
- [ ] percentage generates range CHECK constraint
- [ ] All schema generator tests pass
- [ ] No regression in existing DDL generation

---

## PHASE 3: Fix Database Integration Test Fixtures

**Objective**: Ensure integration tests have proper database fixtures

**Estimated Time**: 2-3 hours

### TDD Cycle 3.1: Fix rich type autodiscovery test fixtures

#### 🔴 RED: Tests failing due to missing tables
**Test file**: `tests/integration/fraiseql/test_rich_type_autodiscovery.py`

**Current error**:
```
psycopg.errors.UndefinedTable: relation "test_3a92bda3.tb_company" does not exist
```

#### 🟢 GREEN: Create complete test fixtures

**Files to modify**:
- `tests/integration/fraiseql/test_rich_type_autodiscovery.py` - Update fixture
- Create fixture entity definitions

**Root cause**: Test uses entity with references that don't exist in fixture

**Investigation**:
```bash
# Find what entities the test expects
grep -A 20 "test_db_with_rich_types" tests/integration/fraiseql/test_rich_type_autodiscovery.py
```

**Solution approach**:
1. Identify all entities referenced in test
2. Create minimal entity definitions
3. Generate complete migration with dependencies
4. Update fixture to load all dependencies

**Implementation**:
```python
# In tests/integration/fraiseql/test_rich_type_autodiscovery.py

@pytest.fixture
def test_db_with_rich_types(test_db):
    """Database with rich type test entities"""
    cursor = test_db.cursor()

    # Create minimal entities needed for test
    entities = [
        # First create referenced entities (no dependencies)
        """
        entity: Company
        schema: tenant
        fields:
          name: text!
          domain: domainName
        """,

        # Then create entity with rich types
        """
        entity: Contact
        schema: tenant
        fields:
          email_address: email!
          mobile_phone: phone
          website: url
          company: ref(Company)
        """,
    ]

    # Generate and execute migration for all entities
    from src.core.specql_parser import SpecQLParser
    from src.generators.schema_orchestrator import SchemaOrchestrator

    parser = SpecQLParser()
    orchestrator = SchemaOrchestrator()

    for entity_yaml in entities:
        entity = parser.parse_yaml_string(entity_yaml)
        migration = orchestrator.generate_complete_schema(entity)
        cursor.execute(migration)

    test_db.commit()

    yield cursor

    # Cleanup handled by test_db fixture
```

**Run test**:
```bash
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py::TestRichTypeAutodiscovery::test_email_field_has_check_constraint -v
```

#### 🔧 REFACTOR: Create reusable test fixtures

**Extract to conftest.py**:
```python
# In tests/integration/conftest.py

@pytest.fixture
def rich_type_test_schema(test_db):
    """Complete schema with all rich types for testing"""
    # Generate once, reuse across tests
    # Include: email, phone, url, money, coordinates, etc.
    pass
```

**Benefits**:
- Faster test execution (create once per session)
- Consistent test data across all integration tests
- Easier to maintain

#### ✅ QA: All rich type autodiscovery tests pass
```bash
# Run all autodiscovery tests
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v

# Expected: 8 tests passing (currently 8 errors)
```

**Checklist**:
- [ ] All referenced entities exist in fixture
- [ ] Foreign key dependencies resolved correctly
- [ ] All 8 autodiscovery tests pass
- [ ] Fixture is efficient (no unnecessary data)

---

### TDD Cycle 3.2: Fix composite hierarchical test fixture

#### 🔴 RED: Test failing due to missing allocation entity
**Test file**: `tests/integration/test_composite_hierarchical_e2e.py::test_allocation_composite_identifier`

**Current error**:
```
psycopg.errors.UndefinedTable: relation does not exist
```

#### 🟢 GREEN: Create allocation entity fixture

**Investigation**:
```bash
# Check what entity the test expects
grep -B 5 -A 10 "test_allocation_composite_identifier" tests/integration/test_composite_hierarchical_e2e.py
```

**Implementation**:
Similar to Cycle 3.1, create complete entity definition and fixture

**Run test**:
```bash
uv run pytest tests/integration/test_composite_hierarchical_e2e.py::TestCompositeHierarchicalE2E::test_allocation_composite_identifier -v
```

#### ✅ QA: Composite hierarchical test passes
```bash
uv run pytest tests/integration/test_composite_hierarchical_e2e.py -v
```

**Checklist**:
- [ ] Allocation entity defined
- [ ] Hierarchical identifier logic works
- [ ] Test passes
- [ ] No side effects on other tests

---

## PHASE 4: Fix FraiseQL Mutation Annotation Tests

**Objective**: Generate proper input types for mutations

**Estimated Time**: 3-4 hours

### TDD Cycle 4.1: Generate mutation input types

#### 🔴 RED: Tests failing due to missing input types
**Test file**: `tests/integration/fraiseql/test_mutation_annotations_e2e.py`

**Current error**:
```
psycopg.errors.UndefinedObject: type test_ca1a1765.type_create_contact_input does not exist
```

#### 🟢 GREEN: Implement input type generation

**Root cause**: Mutation functions expect input types to exist, but generator doesn't create them

**Files to modify**:
- `src/generators/fraiseql/mutation_annotator.py` - Add input type generation
- `src/generators/schema_orchestrator.py` - Include input types in schema

**Investigation**:
```bash
# Check what the test expects
grep -A 20 "test_annotations_apply_to_database" tests/integration/fraiseql/test_mutation_annotations_e2e.py
```

**Analysis**: The generated function likely has:
```sql
CREATE OR REPLACE FUNCTION crm.create_contact(
    input type_create_contact_input  -- ❌ Type doesn't exist
)
```

**Solution**: Generate input type definitions

**Implementation**:
```python
# In src/generators/fraiseql/mutation_annotator.py or new file input_type_generator.py

def generate_mutation_input_type(action: ActionDef, entity: EntityDef) -> str:
    """
    Generate PostgreSQL composite type for mutation input

    Example output:
    CREATE TYPE crm.type_create_contact_input AS (
        email_address TEXT,
        mobile_phone TEXT,
        first_name TEXT,
        last_name TEXT
    );
    """

    schema = entity.schema_name
    type_name = f"type_{action.name}_input"

    # Determine which fields are inputs for this mutation
    # (based on action steps, impact declarations, etc.)
    input_fields = _extract_input_fields(action, entity)

    field_defs = []
    for field in input_fields:
        pg_type = _get_postgres_type_for_field(field)
        field_defs.append(f"    {field.name} {pg_type}")

    sql = f"""-- Mutation input type for {action.name}
CREATE TYPE {schema}.{type_name} AS (
{','.join(field_defs)}
);

COMMENT ON TYPE {schema}.{type_name} IS
'Input type for {action.name} mutation.

@fraiseql:input_type
mutation: {action.name}
entity: {entity.entity_name}';
"""

    return sql
```

**Run test**:
```bash
uv run pytest tests/integration/fraiseql/test_mutation_annotations_e2e.py::TestMutationAnnotationsEndToEnd::test_annotations_apply_to_database -v
```

#### 🔧 REFACTOR: Integrate into schema orchestrator

**Files to modify**:
- `src/generators/schema_orchestrator.py`

**Changes**:
```python
# In schema_orchestrator.py

def generate_complete_schema(self, entity: EntityDef) -> str:
    """Generate complete schema including input types"""

    parts = []

    # 1. Foundation (schemas, app types)
    parts.append(self._generate_foundation())

    # 2. Tables
    parts.append(self.table_generator.generate(entity))

    # 3. Helper functions
    parts.append(self.helper_generator.generate(entity))

    # 4. Mutation input types (NEW)
    for action in entity.actions:
        parts.append(self.input_type_generator.generate(action, entity))

    # 5. Action functions
    for action in entity.actions:
        parts.append(self.action_generator.generate(action, entity))

    return "\n\n".join(parts)
```

#### ✅ QA: All mutation annotation tests pass
```bash
# Run all mutation annotation tests
uv run pytest tests/integration/fraiseql/test_mutation_annotations_e2e.py -v

# Expected: 8 tests passing (currently 4 failures)
```

**Checklist**:
- [ ] Input types generated for all mutations
- [ ] Types created before functions that use them
- [ ] FraiseQL annotations present on types
- [ ] All 4 failing tests now pass
- [ ] No regression in other tests

---

## PHASE 5: Fix Remaining Integration Tests

**Objective**: Fix final integration test issues

**Estimated Time**: 1-2 hours

### TDD Cycle 5.1: Fix URL GIN index test

#### 🔴 RED: Test failing for URL pattern matching
**Test file**: `tests/integration/schema/test_rich_types_postgres.py::test_url_pattern_matching_with_gin_index`

**Investigation**:
```bash
uv run pytest tests/integration/schema/test_rich_types_postgres.py::test_url_pattern_matching_with_gin_index -v --tb=short
```

**Likely issue**: Test expects GIN index for text pattern matching, but generator creates wrong index type or no index

#### 🟢 GREEN: Fix index generation

**Files to check**:
- `src/generators/index_generator.py` - GIN index for text patterns

**Implementation** (if needed):
```python
# For text pattern matching, create GIN index with pg_trgm extension

# Option 1: GIN index for pattern matching
CREATE INDEX idx_tb_contact_website_gin
    ON tenant.tb_contact USING GIN (website gin_trgm_ops);

# Option 2: Regular index (simpler, may be what test expects)
CREATE INDEX idx_tb_contact_website
    ON tenant.tb_contact (website);
```

**Run test**:
```bash
uv run pytest tests/integration/schema/test_rich_types_postgres.py::test_url_pattern_matching_with_gin_index -v
```

#### ✅ QA: Test passes
```bash
uv run pytest tests/integration/schema/test_rich_types_postgres.py -v
```

---

### TDD Cycle 5.2: Fix foreign key constraint test

#### 🔴 RED: Foreign key test failing
**Test file**: `tests/integration/schema/test_rich_types_postgres.py::test_foreign_key_constraints_work`

**Investigation**:
```bash
uv run pytest tests/integration/schema/test_rich_types_postgres.py::test_foreign_key_constraints_work -v --tb=short
```

**Likely issue**: Missing referenced table or incorrect FK generation

#### 🟢 GREEN: Fix FK generation or test fixture

**Run test**:
```bash
uv run pytest tests/integration/schema/test_rich_types_postgres.py::test_foreign_key_constraints_work -v
```

#### ✅ QA: All schema integration tests pass
```bash
uv run pytest tests/integration/schema/ -v
```

---

### TDD Cycle 5.3: Fix stdlib contact snapshot test

#### 🔴 RED: Snapshot mismatch
**Test file**: `tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_snapshot`

**Investigation**:
```bash
uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_snapshot -v --tb=short
```

**Likely issue**: Generated DDL changed due to CHECK constraint additions

#### 🟢 GREEN: Update snapshot

**Options**:
1. Regenerate snapshot with new expected output
2. Fix generator if output is wrong

**Run test**:
```bash
uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_snapshot -v
```

#### ✅ QA: Stdlib tests pass
```bash
uv run pytest tests/integration/stdlib/ -v
```

---

### TDD Cycle 5.4: Fix validation step pattern matching test

#### 🔴 RED: Pattern validation test failing
**Test file**: `tests/unit/actions/test_validation_steps.py::TestValidationSteps::test_pattern_match_validation`

**Investigation**:
```bash
uv run pytest tests/unit/actions/test_validation_steps.py::TestValidationSteps::test_pattern_match_validation -v --tb=short
```

**Likely issue**: Validation step compiler changed regex handling

#### 🟢 GREEN: Fix validation logic or test

**Run test**:
```bash
uv run pytest tests/unit/actions/test_validation_steps.py::TestValidationSteps::test_pattern_match_validation -v
```

#### ✅ QA: All action validation tests pass
```bash
uv run pytest tests/unit/actions/test_validation_steps.py -v
```

---

## PHASE 6: Final QA and Verification

**Objective**: Ensure 100% test pass rate and no regressions

**Estimated Time**: 1 hour

### TDD Cycle 6.1: Full test suite verification

#### ✅ Run complete test suite
```bash
# Run ALL tests
uv run pytest --tb=short -v

# Expected output:
# ======================== 910 passed in XX.XXs ========================
```

**Verification checklist**:
- [ ] 910/910 tests passing
- [ ] No errors
- [ ] No unexpected skips
- [ ] All test categories covered:
  - [ ] Unit tests (parser, generators, actions)
  - [ ] Integration tests (schema, actions, fraiseql, frontend)
  - [ ] E2E tests (database roundtrip, performance)

---

### TDD Cycle 6.2: Code quality verification

#### ✅ Verify code quality
```bash
# Run linting (fix auto-fixable issues)
uv run ruff check --fix

# Run type checking (if configured)
uv run mypy src/ --ignore-missing-imports

# Check for unused imports
uv run ruff check --select F401
```

**Quality checklist**:
- [ ] No critical linting errors
- [ ] Type hints where appropriate
- [ ] No unused imports
- [ ] Consistent code style

---

### TDD Cycle 6.3: Integration verification

#### ✅ Verify full pipeline
```bash
# Test full generation pipeline
python -m src.cli.generate entities entities/contact.yaml --output=test_output/

# Verify generated files
ls -la test_output/

# Test validation
python -m src.cli.validate entities/*.yaml

# Test with Confiture (if available)
cd test_output && confiture build
```

**Integration checklist**:
- [ ] CLI generates complete schema
- [ ] All rich types have CHECK constraints
- [ ] FraiseQL annotations present
- [ ] Confiture can build migrations
- [ ] No warnings or errors

---

## Success Criteria Summary

### ✅ Phase Completion Checklist

- [ ] **Phase 1**: All scalar type description tests pass (7 tests)
- [ ] **Phase 2**: Rich type CHECK constraints generated (5 tests)
- [ ] **Phase 3**: Database fixtures complete (9 tests)
- [ ] **Phase 4**: Mutation input types generated (4 tests)
- [ ] **Phase 5**: All integration tests pass (2 tests)
- [ ] **Phase 6**: 910/910 tests passing, quality verified

### 🎯 Final Deliverables

1. **100% Test Pass Rate**: 910/910 tests passing
2. **Complete Rich Type Support**: All 49 scalar types generate proper constraints
3. **Robust Test Fixtures**: All integration tests have proper database setup
4. **FraiseQL Compliance**: All mutations have input types and annotations
5. **Production Ready**: Full pipeline verified end-to-end

---

## Estimated Timeline

**Total Estimated Time**: 10-14 hours

| Phase | Description | Time |
|-------|-------------|------|
| 1 | Scalar Type Descriptions | 0.5h |
| 2 | CHECK Constraint Generation | 2-3h |
| 3 | Database Fixtures | 2-3h |
| 4 | Mutation Input Types | 3-4h |
| 5 | Remaining Integration Tests | 1-2h |
| 6 | Final QA & Verification | 1h |

**Recommended Schedule**: 2 days of focused development with TDD discipline

---

## Risk Mitigation

### Known Risks

1. **Database-dependent tests**: Some tests require PostgreSQL extensions (PostGIS)
   - **Mitigation**: Skip gracefully if extension unavailable, document requirements

2. **Snapshot tests**: May need updates after constraint generation changes
   - **Mitigation**: Review snapshots carefully, ensure changes are intentional

3. **Performance impact**: Adding CHECK constraints to all fields could slow inserts
   - **Mitigation**: Performance tests should verify acceptable overhead

4. **Regex escaping**: PostgreSQL regex syntax differs from Python
   - **Mitigation**: Comprehensive testing of all validation patterns

---

## Appendix: Quick Reference

### Fast Test Commands

```bash
# Run specific phase tests
uv run pytest tests/unit/core/test_scalar_types.py -v              # Phase 1
uv run pytest tests/unit/schema/test_rich_type_ddl.py -v           # Phase 2
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v  # Phase 3
uv run pytest tests/integration/fraiseql/test_mutation_annotations_e2e.py -v # Phase 4

# Run by category
uv run pytest tests/unit/ -v                    # All unit tests
uv run pytest tests/integration/ -v             # All integration tests
uv run pytest -k "rich_type" -v                 # All rich type tests

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run only failures from last run
uv run pytest --lf -v
```

### Key Files to Modify

```
Phase 1:
- src/core/scalar_types.py (remove "validated format" text)

Phase 2:
- src/generators/table_generator.py (add CHECK constraints)
- src/generators/constraint_generator.py (rich type constraint logic)

Phase 3:
- tests/integration/fraiseql/test_rich_type_autodiscovery.py (fixtures)
- tests/integration/conftest.py (shared fixtures)

Phase 4:
- src/generators/fraiseql/input_type_generator.py (NEW file)
- src/generators/schema_orchestrator.py (integrate input types)

Phase 5:
- Various integration test files (case-by-case fixes)
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
**Next Review**: After each phase completion
**Expected Completion**: Phase 6 complete = 100% test coverage
