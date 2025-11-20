# Week 4: Schema Generation Polish
**Duration**: 5 days | **Tests**: 19 | **Priority**: 🟡 MEDIUM

## 🎯 What You'll Build

By the end of this week, you'll have:
- ✅ Table generator integration tests passing (10 tests)
- ✅ Table generator assertion formats fixed (6 tests)
- ✅ Stdlib contact snapshot tests passing (3 tests)
- ✅ DDL format standardized and consistent
- ✅ All schema generation edge cases handled

**Why this matters**: These tests ensure our DDL generation is consistent, follows conventions, and produces valid SQL that matches expectations exactly.

---

## 📋 Tests to Unskip

### File 1: `tests/unit/schema/test_table_generator_integration.py` (10 tests)

These tests verify complete DDL orchestration:

1. `test_complete_ddl_with_foreign_keys` - FK generation in full DDL
2. `test_complete_ddl_with_enum_constraints` - ENUM constraints properly generated
3. `test_generate_indexes_ddl_with_foreign_keys` - Index DDL includes FK indexes
4. `test_generate_indexes_ddl_with_enum_fields` - Index DDL for enum fields
5. `test_generate_complete_ddl_orchestration` - Full DDL order correct
6. `test_common_schema_skips_multi_tenant_fields` - Common schema has no tenant_id
7. `test_rich_types_in_complete_ddl` - Rich types fully integrated
8. `test_no_duplicate_comments_in_complete_ddl` - No duplicate COMMENT statements
9. `test_audit_fields_always_present` - Audit fields in every table
10. `test_index_method_specification_explicit` - Indexes specify USING btree/gin/gist

### File 2: `tests/unit/generators/test_table_generator.py` (6 tests)

These tests check DDL format details:

1. `test_generate_simple_table` - Basic CREATE TABLE format
2. `test_generate_contact_table` - Contact entity DDL format
3. `test_table_comments_with_fraiseql_yaml_format` - Comment format matches spec
4. `test_generate_foreign_keys_ddl` - FK DDL format correct
5. `test_generate_indexes_ddl` - Index DDL format correct
6. `test_trinity_pattern_always_applied` - Trinity fields always present

### File 3: `tests/integration/stdlib/test_stdlib_contact_generation.py` (3 tests)

These tests verify stdlib Contact entity:

1. `test_generate_contact_entity_snapshot` - Generated DDL matches snapshot
2. `test_generate_contact_entity_production_readiness` - Production-ready validation
3. `test_generate_contact_entity_full_ddl` - Complete DDL with all features

---

## 🧠 Understanding Schema Polish

### What Is "Polish"?

Polish means making the generated SQL:
- **Consistent**: Same format everywhere
- **Correct**: Follows PostgreSQL standards
- **Complete**: No missing pieces
- **Clean**: No duplicates or artifacts

### Why These Tests Were Skipped

These tests were marked "deferred to post-beta" because they check:
- Minor formatting differences (spaces, line breaks)
- Assertion expectations that need updating
- Snapshot comparisons that changed during development

**They're not bugs** - just format mismatches between expected and actual output.

### Common Issues

1. **Index method not explicit**: `CREATE INDEX` vs `CREATE INDEX USING btree`
2. **DDL ordering**: Comments before indexes vs indexes before comments
3. **Whitespace differences**: Tabs vs spaces, extra line breaks
4. **Duplicate statements**: Same comment or index generated twice
5. **Missing conventions**: Trinity pattern not applied consistently

---

## 📅 Day-by-Day Plan

### Day 1: Analyze Test Failures 🔍

**Goal**: Understand what's failing and why

#### Step 1: Review Test Files

Read the three test files to understand what they're checking:

```bash
# Table generator integration
cat tests/unit/schema/test_table_generator_integration.py | less

# Table generator format
cat tests/unit/generators/test_table_generator.py | less

# Stdlib contact
cat tests/integration/stdlib/test_stdlib_contact_generation.py | less
```

**Look for**:
- What assertions are made
- What DDL format is expected
- What conventions must be followed

#### Step 2: Temporarily Unskip and Run Tests

Comment out skip markers to see actual failures:

```bash
# Edit test files and comment out:
# pytestmark = pytest.mark.skip(reason="...")

# Run to see failures
uv run pytest tests/unit/schema/test_table_generator_integration.py -v --tb=short

uv run pytest tests/unit/generators/test_table_generator.py -v --tb=short

uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py -v --tb=short
```

**Expected**: Tests will fail - that's good! We need to see the failures.

#### Step 3: Document Failures

Create `docs/post_beta_plan/week4_failure_analysis.md`:

```markdown
# Week 4 Failure Analysis

## Test Failures Summary

### test_table_generator_integration.py

#### test_index_method_specification_explicit
**Status**: FAILED
**Expected**: `CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);`
**Actual**: `CREATE INDEX idx_tb_contact_email ON crm.tb_contact (email);`
**Fix**: Add explicit `USING btree` to B-tree indexes

#### test_complete_ddl_orchestration
**Status**: FAILED
**Expected order**:
1. CREATE SCHEMA
2. CREATE TYPE
3. CREATE TABLE
4. CREATE INDEX
5. COMMENT ON COLUMN
6. CREATE FUNCTION (Trinity)
7. CREATE FUNCTION (Actions)

**Actual order**:
1. CREATE SCHEMA
2. CREATE TYPE
3. CREATE TABLE
4. COMMENT ON COLUMN
5. CREATE INDEX  ← Wrong order
6. CREATE FUNCTION (Trinity)
7. CREATE FUNCTION (Actions)

**Fix**: Move indexes before comments in orchestrator

[... document all failures ...]
```

#### Step 4: Categorize Failures

Group failures by type:

**Category A: Index Method Specification** (2 tests)
- `test_index_method_specification_explicit`
- `test_generate_indexes_ddl`

**Fix**: Ensure all indexes explicitly state `USING btree/gin/gist`

**Category B: DDL Ordering** (3 tests)
- `test_complete_ddl_orchestration`
- `test_generate_complete_ddl_orchestration`
- `test_generate_contact_entity_full_ddl`

**Fix**: Correct DDL generation order in `SchemaOrchestrator`

**Category C: Duplicate Prevention** (2 tests)
- `test_no_duplicate_comments_in_complete_ddl`
- `test_no_duplicate_indexes_in_complete_ddl`

**Fix**: Deduplicate comments and indexes

**Category D: Format Consistency** (8 tests)
- Various format and whitespace issues

**Fix**: Standardize DDL formatting

**Category E: Snapshot Mismatches** (3 tests)
- Stdlib contact tests

**Fix**: Update snapshots or fix generation

#### Step 5: Create Fix Plan

For each category, plan the fix:

```markdown
## Fix Plan

### Priority 1: Index Method Specification (Easy)
**Files to modify**:
- `src/generators/schema/rich_type_index_generator.py`
- Ensure all index types explicitly state USING clause

**Tests affected**: 2
**Estimated time**: 30 minutes

### Priority 2: DDL Ordering (Medium)
**Files to modify**:
- `src/generators/schema_orchestrator.py`
- Reorder DDL components: indexes before comments

**Tests affected**: 3
**Estimated time**: 1 hour

### Priority 3: Duplicate Prevention (Medium)
**Files to modify**:
- `src/generators/table_generator.py`
- Add deduplication logic

**Tests affected**: 2
**Estimated time**: 1 hour

[... continue for all categories ...]
```

#### ✅ Day 1 Success Criteria

- [ ] All 19 tests run (with failures documented)
- [ ] Failures analyzed and categorized
- [ ] Fix plan created
- [ ] Priority order determined
- [ ] Ready to start fixing

**Deliverable**: Comprehensive failure analysis document ✅

---

### Day 2: Fix Index Method Specification & DDL Ordering 🔧

**Goal**: Fix the highest priority issues (5 tests)

#### Step 1: Fix Index Method Specification

**Problem**: Some indexes don't explicitly state `USING btree`

Edit `src/generators/schema/rich_type_index_generator.py`:

```python
def _generate_btree_index(self, entity: Entity, field: FieldDefinition) -> str:
    """
    Generate B-tree index for exact lookups and ranges

    IMPORTANT: Always explicitly specify USING btree
    Even though B-tree is the default, tests expect it to be explicit
    """
    table_name = f"tb_{entity.name.lower()}"
    index_name = f"idx_{table_name}_{field.name}"
    full_table = f"{entity.schema}.{table_name}"

    # MUST include "USING btree" explicitly
    return f"CREATE INDEX {index_name} ON {full_table} USING btree ({field.name});"
```

**Also check foreign key indexes**:

Edit `src/generators/table_generator.py`:

```python
def _generate_fk_indexes(self, entity: Entity) -> List[str]:
    """Generate indexes for foreign key columns"""
    indexes = []

    for field_name, field in entity.fields.items():
        if field.type_name == 'ref':
            table_name = f"tb_{entity.name.lower()}"
            fk_col = f"fk_{field.ref_entity.lower()}"
            index_name = f"idx_{table_name}_{fk_col}"
            full_table = f"{entity.schema}.{table_name}"

            # Explicitly specify USING btree
            index_sql = f"CREATE INDEX {index_name} ON {full_table} USING btree ({fk_col});"
            indexes.append(index_sql)

    return indexes
```

**Test the fix**:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py::test_index_method_specification_explicit -v
```

**Expected**: Test passes! ✅

#### Step 2: Fix DDL Ordering

**Problem**: Comments come before indexes (should be after)

**Correct order**:
1. CREATE SCHEMA
2. CREATE TYPE (composite types)
3. CREATE TABLE
4. CREATE INDEX (all indexes together)
5. COMMENT ON COLUMN (comments after tables and indexes)
6. CREATE FUNCTION (Trinity helpers)
7. CREATE FUNCTION (Actions)

Edit `src/generators/schema_orchestrator.py`:

```python
def generate_complete_schema(self, entity: Entity) -> str:
    """
    Generate complete schema in correct order

    Order matters for DDL:
    1. Schemas must exist before objects
    2. Types must exist before tables use them
    3. Tables must exist before indexes reference them
    4. Indexes should come before comments (convention)
    5. Functions come last (may reference tables)
    """
    parts = []

    # 1. CREATE SCHEMA (if needed)
    if entity.schema not in ['common', 'app', 'core']:
        parts.append(f"CREATE SCHEMA IF NOT EXISTS {entity.schema};")

    # 2. CREATE TYPE (composite types)
    type_generator = CompositeTypeGenerator(self.schema_registry)
    composite_types = type_generator.generate_types(entity)
    if composite_types:
        parts.append(composite_types)

    # 3. CREATE TABLE
    table_generator = TableGenerator(self.schema_registry)
    table_ddl = table_generator.generate(entity)
    parts.append(table_ddl)

    # 4. CREATE INDEX (FK + rich types + enum indexes)
    index_ddl = table_generator.generate_indexes(entity)
    if index_ddl:
        parts.append(index_ddl)

    # 5. COMMENT ON COLUMN (after tables and indexes)
    comments = table_generator.generate_field_comments(entity)
    if comments:
        parts.extend(comments)

    # 6. CREATE FUNCTION (Trinity helpers)
    trinity_generator = TrinityHelperGenerator(self.schema_registry)
    trinity_ddl = trinity_generator.generate(entity)
    parts.append(trinity_ddl)

    # 7. CREATE FUNCTION (Actions)
    action_generator = ActionOrchestrator(self.schema_registry)
    for action in entity.actions:
        action_ddl = action_generator.generate_action(entity, action)
        parts.append(action_ddl)

    return "\n\n".join(parts)
```

**Key change**: Indexes (step 4) now come BEFORE comments (step 5).

**Test the fix**:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py::test_complete_ddl_orchestration -v

uv run pytest tests/unit/schema/test_table_generator_integration.py::test_generate_complete_ddl_orchestration -v
```

**Expected**: Tests pass! ✅

#### Step 3: Verify Index Tests Pass

Run all index-related tests:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py -v -k "index"
```

**Expected**: All index tests passing ✅

#### Step 4: Verify Ordering Tests Pass

Run all ordering-related tests:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py -v -k "orchestration"
```

**Expected**: Ordering tests passing ✅

#### ✅ Day 2 Success Criteria

- [ ] Index method specification fixed
- [ ] DDL ordering corrected
- [ ] 5 tests now passing
- [ ] No regressions in previous tests

**Deliverable**: 5 tests passing (index specification + ordering) ✅

---

### Day 3: Fix Duplicates & Common Schema 🧹

**Goal**: Prevent duplicate statements and handle schema types correctly (4 tests)

#### Step 1: Understand Duplicate Issue

**Problem**: Comments or indexes generated multiple times

**Example**:
```sql
-- Generated twice!
COMMENT ON COLUMN crm.tb_contact.email IS 'Email address...';
COMMENT ON COLUMN crm.tb_contact.email IS 'Email address...';
```

**Why this happens**:
- Comment generator called multiple times
- Index generator called from different places
- No deduplication logic

#### Step 2: Add Deduplication Helper

Create `src/generators/schema/ddl_deduplicator.py`:

```python
"""
DDL deduplication utilities

Prevents duplicate CREATE INDEX and COMMENT statements
"""

from typing import List


class DDLDeduplicator:
    """Remove duplicate DDL statements"""

    @staticmethod
    def deduplicate_indexes(indexes: List[str]) -> List[str]:
        """
        Remove duplicate index statements

        Args:
            indexes: List of CREATE INDEX statements

        Returns:
            Deduplicated list (preserves order of first occurrence)
        """
        seen = set()
        result = []

        for idx in indexes:
            # Normalize whitespace for comparison
            normalized = " ".join(idx.split())

            if normalized not in seen:
                seen.add(normalized)
                result.append(idx)

        return result

    @staticmethod
    def deduplicate_comments(comments: List[str]) -> List[str]:
        """
        Remove duplicate comment statements

        Args:
            comments: List of COMMENT ON COLUMN statements

        Returns:
            Deduplicated list (preserves order of first occurrence)
        """
        seen = set()
        result = []

        for comment in comments:
            # Normalize whitespace for comparison
            normalized = " ".join(comment.split())

            if normalized not in seen:
                seen.add(normalized)
                result.append(comment)

        return result

    @staticmethod
    def deduplicate_ddl(ddl_statements: List[str]) -> List[str]:
        """
        Remove duplicate DDL statements of any type

        Args:
            ddl_statements: List of SQL DDL statements

        Returns:
            Deduplicated list
        """
        seen = set()
        result = []

        for stmt in ddl_statements:
            # Normalize whitespace
            normalized = " ".join(stmt.split())

            if normalized not in seen:
                seen.add(normalized)
                result.append(stmt)

        return result
```

#### Step 3: Apply Deduplication

Edit `src/generators/table_generator.py`:

```python
from src.generators.schema.ddl_deduplicator import DDLDeduplicator

class TableGenerator:
    def generate_indexes(self, entity: Entity) -> str:
        """
        Generate all indexes (foreign keys + rich types + enums)

        Returns deduplicated index DDL
        """
        indexes = []

        # Generate FK indexes
        fk_indexes = self._generate_fk_indexes(entity)
        indexes.extend(fk_indexes)

        # Generate rich type indexes
        rich_type_indexes = self.index_generator.generate_all_indexes(entity)
        indexes.extend(rich_type_indexes)

        # Generate enum indexes (if needed)
        enum_indexes = self._generate_enum_indexes(entity)
        indexes.extend(enum_indexes)

        # Deduplicate
        indexes = DDLDeduplicator.deduplicate_indexes(indexes)

        return "\n".join(indexes) if indexes else ""

    def generate_field_comments(self, entity: Entity) -> List[str]:
        """
        Generate comments for entity fields

        Returns deduplicated comments
        """
        comments = self.comment_generator.generate_all_comments(entity)

        # Deduplicate
        comments = DDLDeduplicator.deduplicate_comments(comments)

        return comments
```

**Test the fix**:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py::test_no_duplicate_comments_in_complete_ddl -v

uv run pytest tests/unit/schema/test_table_generator_integration.py::test_no_duplicate_indexes_in_complete_ddl -v
```

**Expected**: Duplicate tests pass! ✅

#### Step 4: Fix Common Schema (No tenant_id)

**Problem**: Common schema tables shouldn't have `tenant_id` field

**Rule**:
- Multi-tenant schemas (crm, projects, etc.) → Add `tenant_id`
- Common schema (common) → No `tenant_id`
- Shared schemas (catalog, analytics) → No `tenant_id` (configurable)

Edit `src/generators/table_generator.py`:

```python
def _should_add_tenant_field(self, entity: Entity) -> bool:
    """
    Determine if entity should have tenant_id field

    Rules:
    - Common schema: NO tenant_id
    - Framework schemas (app, core): NO tenant_id
    - Multi-tenant schemas: YES tenant_id
    - Shared schemas: Depends on registry configuration
    """
    # Framework schemas never have tenant_id
    if entity.schema in ['common', 'app', 'core']:
        return False

    # Check schema registry for multi-tenant configuration
    schema_config = self.schema_registry.get_schema_config(entity.schema)

    if schema_config:
        return schema_config.is_multi_tenant

    # Default: assume multi-tenant if not in registry
    return True

def _generate_fields(self, entity: Entity) -> List[str]:
    """Generate field definitions for CREATE TABLE"""
    fields = []

    # Trinity pattern (always first)
    fields.append(f"pk_{entity.name.lower()} INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY")
    fields.append(f"id UUID DEFAULT gen_random_uuid()")
    fields.append(f"identifier TEXT")

    # Multi-tenant field (if applicable)
    if self._should_add_tenant_field(entity):
        fields.append("tenant_id UUID NOT NULL")

    # User-defined fields
    for field_name, field in entity.fields.items():
        field_ddl = self._generate_field_ddl(field)
        fields.append(field_ddl)

    # Audit fields (always last)
    fields.append("created_at TIMESTAMP DEFAULT NOW()")
    fields.append("created_by UUID")
    fields.append("updated_at TIMESTAMP DEFAULT NOW()")
    fields.append("updated_by UUID")
    fields.append("deleted_at TIMESTAMP")

    return fields
```

**Test the fix**:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py::test_common_schema_skips_multi_tenant_fields -v
```

**Expected**: Common schema test passes! ✅

#### Step 5: Verify All Integration Tests

Run all table generator integration tests:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py -v
```

**Expected**: More tests passing now ✅

#### ✅ Day 3 Success Criteria

- [ ] Deduplication helper created
- [ ] Duplicates prevented in indexes and comments
- [ ] Common schema handling fixed (no tenant_id)
- [ ] 4 more tests passing (9 total)

**Deliverable**: Duplicate prevention + schema handling ✅

---

### Day 4: Fix Format & Convention Tests 🎨

**Goal**: Fix format assertions and ensure conventions (7 tests)

#### Step 1: Fix Simple Table Format

Run simple table test to see format issues:

```bash
uv run pytest tests/unit/generators/test_table_generator.py::test_generate_simple_table -vv
```

**Common format issues**:

1. **Whitespace**: Extra spaces or line breaks
2. **Field order**: Fields in unexpected order
3. **Constraint format**: CHECK constraints formatted differently

**Fix**: Create DDL formatter

Create `src/generators/schema/ddl_formatter.py`:

```python
"""
DDL formatting utilities

Ensures consistent SQL formatting across all generators
"""

import re
from typing import List


class DDLFormatter:
    """Format DDL statements consistently"""

    @staticmethod
    def format_create_table(ddl: str) -> str:
        """
        Format CREATE TABLE statement consistently

        Rules:
        - Each field on its own line
        - Proper indentation (4 spaces)
        - Constraints after fields
        - Closing parenthesis on its own line
        """
        # Remove extra whitespace
        ddl = re.sub(r'\s+', ' ', ddl)

        # Split at commas
        parts = ddl.split(',')

        # Format each part
        formatted_parts = []
        for part in parts:
            part = part.strip()
            if part:
                formatted_parts.append(f"    {part}")

        # Reconstruct
        result = parts[0].split('(')[0] + '(\n'
        result += ',\n'.join(formatted_parts)
        result += '\n);'

        return result

    @staticmethod
    def normalize_whitespace(sql: str) -> str:
        """Normalize whitespace in SQL"""
        # Replace multiple spaces with single space
        sql = re.sub(r'\s+', ' ', sql)
        # Remove leading/trailing whitespace
        sql = sql.strip()
        return sql

    @staticmethod
    def format_index(index_sql: str) -> str:
        """Format CREATE INDEX statement"""
        return DDLFormatter.normalize_whitespace(index_sql)

    @staticmethod
    def format_comment(comment_sql: str) -> str:
        """Format COMMENT ON COLUMN statement"""
        return DDLFormatter.normalize_whitespace(comment_sql)
```

#### Step 2: Apply Formatting

Use formatter in generators:

```python
from src.generators.schema.ddl_formatter import DDLFormatter

class TableGenerator:
    def generate(self, entity: Entity) -> str:
        """Generate CREATE TABLE statement"""
        # ... generate DDL ...
        ddl = self._generate_create_table(entity)

        # Format consistently
        ddl = DDLFormatter.format_create_table(ddl)

        return ddl
```

#### Step 3: Fix Trinity Pattern Assertion

Ensure Trinity pattern is always present:

```bash
uv run pytest tests/unit/generators/test_table_generator.py::test_trinity_pattern_always_applied -v
```

Test expects:
- `pk_{entity}` - INTEGER PRIMARY KEY
- `id` - UUID
- `identifier` - TEXT

**Our implementation already does this**, but verify the assertion:

```python
def test_trinity_pattern_always_applied(table_generator):
    """Test that Trinity pattern is always present"""
    entity = Entity(
        name="TestEntity",
        schema="test",
        fields={}  # Empty fields - should still have Trinity
    )

    ddl = table_generator.generate(entity)

    # Must have all three Trinity fields
    assert "pk_testentity" in ddl.lower()
    assert "id UUID" in ddl
    assert "identifier TEXT" in ddl
```

Should pass! ✅

#### Step 4: Fix Audit Fields Assertion

Ensure audit fields always present:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py::test_audit_fields_always_present -v
```

Test expects:
- `created_at TIMESTAMP`
- `created_by UUID`
- `updated_at TIMESTAMP`
- `updated_by UUID`
- `deleted_at TIMESTAMP`

**Our implementation already includes these**, verify assertion matches format.

#### Step 5: Fix Rich Types in Complete DDL

Test that rich types are fully integrated:

```bash
uv run pytest tests/unit/schema/test_table_generator_integration.py::test_rich_types_in_complete_ddl -v
```

Test expects:
- Rich type fields in table
- Indexes for rich types
- Comments for rich types

Should already work with our implementations! ✅

#### Step 6: Run All Table Generator Tests

```bash
# Run all table generator tests
uv run pytest tests/unit/generators/test_table_generator.py -v

# Run all integration tests
uv run pytest tests/unit/schema/test_table_generator_integration.py -v
```

**Expected**: Most tests passing now ✅

#### ✅ Day 4 Success Criteria

- [ ] DDL formatter created
- [ ] Format consistency applied
- [ ] Trinity pattern verified
- [ ] Audit fields verified
- [ ] Rich types integration verified
- [ ] 16 tests passing (table gen + integration)

**Deliverable**: Format and conventions standardized ✅

---

### Day 5: Fix Stdlib Snapshots & Final QA ✨

**Goal**: Fix remaining 3 tests and verify everything works

#### Step 1: Understand Snapshot Tests

Snapshot tests compare generated DDL with saved snapshots:

```python
def test_generate_contact_entity_snapshot(orchestrator, snapshot):
    """Test that Contact entity matches saved snapshot"""
    # Parse Contact entity
    contact = parse_contact_yaml()

    # Generate DDL
    ddl = orchestrator.generate_complete_schema(contact)

    # Compare with snapshot
    assert ddl == snapshot
```

**Two options to fix**:
1. **Update snapshot** (if current DDL is correct)
2. **Fix generator** (if current DDL is wrong)

#### Step 2: Generate Current Contact DDL

Generate fresh DDL for Contact entity:

```bash
uv run python -c "
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator

# Parse stdlib contact
yaml_content = Path('stdlib/crm/contact.yaml').read_text()
parser = SpecQLParser()
entity_def = parser.parse(yaml_content)

# Generate complete DDL
orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity_def.to_entity())

# Save to file
Path('/tmp/contact_current.sql').write_text(ddl)
print('Generated DDL saved to /tmp/contact_current.sql')
"
```

#### Step 3: Compare with Snapshot

Compare generated DDL with expected snapshot:

```bash
# Find snapshot file
find tests/fixtures/snapshots -name "*contact*"

# Compare
diff tests/fixtures/snapshots/contact_expected.sql /tmp/contact_current.sql
```

**Analysis**:
- If differences are minor (whitespace, order) → Update snapshot
- If differences are major (missing features) → Fix generator

#### Step 4: Update Snapshots (if needed)

If current DDL is correct, update snapshots:

```bash
# Copy current DDL to snapshot
cp /tmp/contact_current.sql tests/fixtures/snapshots/contact_expected.sql

# Or use pytest --snapshot-update (if using pytest-snapshot plugin)
uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py --snapshot-update
```

#### Step 5: Test Contact Generation

Run all contact tests:

```bash
uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py -v
```

**Tests**:

1. **test_generate_contact_entity_snapshot**
   - Verifies DDL matches snapshot
   - Should pass after snapshot update ✅

2. **test_generate_contact_entity_production_readiness**
   - Verifies production requirements:
     - Trinity pattern ✅
     - Audit fields ✅
     - Foreign keys ✅
     - Indexes ✅
     - Comments ✅
   - Should pass! ✅

3. **test_generate_contact_entity_full_ddl**
   - Verifies complete DDL includes:
     - Schema creation ✅
     - Table creation ✅
     - Indexes ✅
     - Comments ✅
     - Trinity helpers ✅
     - Action functions ✅
   - Should pass! ✅

#### Step 6: Remove All Skip Markers

Edit all three test files and remove skip markers:

```bash
# Edit test files
vim tests/unit/schema/test_table_generator_integration.py
vim tests/unit/generators/test_table_generator.py
vim tests/integration/stdlib/test_stdlib_contact_generation.py

# Comment out or remove:
# pytestmark = pytest.mark.skip(reason="...")
```

#### Step 7: Run All 19 Tests

```bash
# Run all Week 4 tests
uv run pytest \
    tests/unit/schema/test_table_generator_integration.py \
    tests/unit/generators/test_table_generator.py \
    tests/integration/stdlib/test_stdlib_contact_generation.py \
    -v
```

**Expected output**:
```
tests/unit/schema/test_table_generator_integration.py::test_complete_ddl_with_foreign_keys PASSED
tests/unit/schema/test_table_generator_integration.py::test_complete_ddl_with_enum_constraints PASSED
tests/unit/schema/test_table_generator_integration.py::test_generate_indexes_ddl_with_foreign_keys PASSED
tests/unit/schema/test_table_generator_integration.py::test_generate_indexes_ddl_with_enum_fields PASSED
tests/unit/schema/test_table_generator_integration.py::test_generate_complete_ddl_orchestration PASSED
tests/unit/schema/test_table_generator_integration.py::test_common_schema_skips_multi_tenant_fields PASSED
tests/unit/schema/test_table_generator_integration.py::test_rich_types_in_complete_ddl PASSED
tests/unit/schema/test_table_generator_integration.py::test_no_duplicate_comments_in_complete_ddl PASSED
tests/unit/schema/test_table_generator_integration.py::test_audit_fields_always_present PASSED
tests/unit/schema/test_table_generator_integration.py::test_index_method_specification_explicit PASSED

tests/unit/generators/test_table_generator.py::test_generate_simple_table PASSED
tests/unit/generators/test_table_generator.py::test_generate_contact_table PASSED
tests/unit/generators/test_table_generator.py::test_table_comments_with_fraiseql_yaml_format PASSED
tests/unit/generators/test_table_generator.py::test_generate_foreign_keys_ddl PASSED
tests/unit/generators/test_table_generator.py::test_generate_indexes_ddl PASSED
tests/unit/generators/test_table_generator.py::test_trinity_pattern_always_applied PASSED

tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_snapshot PASSED
tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_production_readiness PASSED
tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_full_ddl PASSED

========================= 19 passed in 2.87s =========================
```

🎉 **All 19 tests passing!**

#### Step 8: Run Full Test Suite

Verify no regressions:

```bash
# Run all tests
uv run pytest --tb=no -q
```

**Expected**:
```
1453 passed, 52 skipped, 3 xfailed in 58.4s
```

(1434 + 19 new = 1453 passed)

#### Step 9: Document Changes

Create `docs/post_beta_plan/week4_changes.md`:

```markdown
# Week 4 Changes Summary

## Files Created

1. `src/generators/schema/ddl_deduplicator.py`
   - Deduplication utilities for indexes and comments
   - Prevents duplicate DDL statements

2. `src/generators/schema/ddl_formatter.py`
   - DDL formatting utilities
   - Ensures consistent SQL format

3. `docs/post_beta_plan/week4_failure_analysis.md`
   - Analysis of test failures
   - Categorization and fix plan

4. `docs/post_beta_plan/week4_changes.md`
   - This file

## Files Modified

1. `src/generators/schema_orchestrator.py`
   - Fixed DDL generation order (indexes before comments)
   - Consistent ordering across all entities

2. `src/generators/schema/rich_type_index_generator.py`
   - Added explicit USING clause for all index types
   - Ensures consistent index format

3. `src/generators/table_generator.py`
   - Added deduplication for indexes and comments
   - Fixed common schema handling (no tenant_id)
   - Added multi-tenant field logic
   - Applied consistent formatting

4. `tests/fixtures/snapshots/contact_expected.sql`
   - Updated snapshot to match current DDL format

5. Test files (removed skip markers):
   - `tests/unit/schema/test_table_generator_integration.py`
   - `tests/unit/generators/test_table_generator.py`
   - `tests/integration/stdlib/test_stdlib_contact_generation.py`

## Key Improvements

### 1. DDL Order Standardization
**Before**:
```
CREATE TABLE
COMMENT ON COLUMN
CREATE INDEX
```

**After**:
```
CREATE TABLE
CREATE INDEX
COMMENT ON COLUMN
```

### 2. Index Method Explicit
**Before**:
```sql
CREATE INDEX idx_tb_contact_email ON crm.tb_contact (email);
```

**After**:
```sql
CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);
```

### 3. Duplicate Prevention
**Before**: Could generate same index/comment multiple times

**After**: Deduplication ensures each statement appears once

### 4. Common Schema Handling
**Before**: Common schema tables had tenant_id (incorrect)

**After**: Common schema tables have no tenant_id (correct)

## Tests Fixed

### Table Generator Integration (10 tests)
- DDL ordering
- Index method specification
- Duplicate prevention
- Schema type handling
- Rich types integration

### Table Generator Format (6 tests)
- CREATE TABLE format
- Foreign key DDL format
- Index DDL format
- Trinity pattern
- Audit fields

### Stdlib Contact (3 tests)
- Snapshot matching
- Production readiness
- Complete DDL

## Total: 19 tests now passing ✅
```

#### ✅ Day 5 Success Criteria

- [ ] Snapshots updated
- [ ] All contact tests passing
- [ ] All 19 tests passing
- [ ] No regressions in test suite
- [ ] Changes documented
- [ ] Ready for Week 5

**Deliverable**: All schema polish tests passing ✅

---

## 🎉 Week 4 Complete!

### What You Accomplished

✅ **19 schema polish tests passing**
- 10 table generator integration tests
- 6 table generator format tests
- 3 stdlib contact generation tests

✅ **Code quality improvements**
- DDL deduplication (no duplicate statements)
- DDL formatting (consistent SQL format)
- DDL ordering (correct sequence)
- Index method explicit (USING clause always present)
- Common schema handling (proper multi-tenant logic)

✅ **New utilities**
- `DDLDeduplicator` class
- `DDLFormatter` class
- Snapshot management

### Progress Tracking

```bash
# Before Week 4: 1434 passed, 71 skipped (Weeks 1-3 complete)
# After Week 4:  1453 passed, 52 skipped
# Progress:      +19 tests (18.3% of remaining tests complete)
```

### Files Created/Modified

**Created**:
- `src/generators/schema/ddl_deduplicator.py` - Deduplication utilities
- `src/generators/schema/ddl_formatter.py` - Formatting utilities
- `docs/post_beta_plan/week4_failure_analysis.md` - Failure analysis
- `docs/post_beta_plan/week4_changes.md` - Changes summary

**Modified**:
- `src/generators/schema_orchestrator.py` - Fixed DDL order
- `src/generators/schema/rich_type_index_generator.py` - Explicit USING clause
- `src/generators/table_generator.py` - Deduplication, common schema, formatting
- `tests/fixtures/snapshots/contact_expected.sql` - Updated snapshot
- All 3 test files - Removed skip markers

### What's Next

**👉 [Week 5: FraiseQL GraphQL Polish](./week5_fraiseql_graphql.md)** (7 tests)

Week 5 focuses on completing FraiseQL GraphQL integration:
- Rich type scalar mappings
- GraphQL schema generation
- FraiseQL autodiscovery metadata
- Validation pattern descriptions

---

## 💡 What You Learned

### Test-Driven Debugging

**Process**:
1. Run tests to see failures
2. Analyze failure patterns
3. Categorize by root cause
4. Fix in priority order
5. Verify no regressions

This is how professionals debug complex systems!

### DDL Ordering Matters

PostgreSQL DDL has dependencies:
1. Schemas must exist before objects
2. Types must exist before tables use them
3. Tables must exist before indexes reference them
4. Conventions: indexes before comments

**Wrong order = SQL errors**

### Deduplication Prevents Bugs

Duplicate statements can cause:
- Performance issues (duplicate indexes slow down writes)
- Maintenance confusion (which one is real?)
- Test failures (assertions expect exact output)

**Deduplication = clean code**

### Snapshot Testing

Snapshot tests are useful for:
- Verifying complex output
- Catching unexpected changes
- Documenting expected format

**But**: Snapshots need maintenance when format evolves

---

## 🐛 Troubleshooting

### Test Fails: "Index method not specified"

```sql
-- Wrong
CREATE INDEX idx ON table (col);

-- Right
CREATE INDEX idx ON table USING btree (col);
```

Even though B-tree is default, tests expect it explicit.

### Test Fails: "DDL in wrong order"

Check `schema_orchestrator.py` order:
1. Schema
2. Types
3. Table
4. Indexes ← Before comments!
5. Comments
6. Functions

### Test Fails: "Duplicate statement"

Add deduplication:
```python
from src.generators.schema.ddl_deduplicator import DDLDeduplicator

indexes = DDLDeduplicator.deduplicate_indexes(indexes)
```

### Test Fails: "Common schema has tenant_id"

Check `_should_add_tenant_field()` logic:
```python
if entity.schema == 'common':
    return False  # No tenant_id for common schema
```

---

**Excellent work completing Week 4! 🎨 Schema generation is now polished and consistent!**
