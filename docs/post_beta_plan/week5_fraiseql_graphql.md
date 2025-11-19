# Week 5: FraiseQL GraphQL Polish

**Duration**: 5 days | **Tests**: 7 | **Priority**: MEDIUM

---

## 🎯 What You'll Build

This week focuses on **completing the integration** between SpecQL's rich type system and FraiseQL's GraphQL autodiscovery. You'll ensure that:

1. **Rich types have GraphQL scalar mappings** (`email` → `Email` scalar)
2. **PostgreSQL comments include FraiseQL metadata** for autodiscovery
3. **All validation patterns** produce meaningful GraphQL descriptions
4. **Complete schema generation** includes all metadata needed

**Why this matters**: FraiseQL reads PostgreSQL schema metadata and auto-generates GraphQL APIs. Better metadata = better GraphQL schemas!

---

## 📋 Tests to Unskip

**File**: `tests/integration/fraiseql/test_rich_type_graphql_generation.py`

### Class: TestRichTypeGraphQLGeneration (3 tests)
1. `test_generate_complete_schema_with_rich_types` - Complete schema includes rich types
2. `test_rich_type_comments_for_graphql_descriptions` - Comments have GraphQL metadata
3. `test_fraiseql_autodiscovery_metadata_complete` - All metadata present

### Class: TestFraiseQLIntegrationContract (4 tests)
4. `test_rich_type_scalar_mappings_complete` - All rich types → GraphQL scalars
5. `test_postgresql_types_support_fraiseql_autodiscovery` - PostgreSQL types compatible
6. `test_validation_patterns_produce_meaningful_comments` - Descriptions are meaningful
7. `test_fraiseql_would_generate_correct_schema` - Expected GraphQL output

---

## 📅 Day-by-Day Plan

### Day 1: Understand FraiseQL Integration 🔍

**Goal**: Understand how FraiseQL autodiscovery works and what metadata it needs

#### 🔴 RED Phase: Study the Tests

**Step 1**: Read the test file to understand expectations

```bash
# Open the test file
cat tests/integration/fraiseql/test_rich_type_graphql_generation.py

# Key questions to answer:
# 1. What metadata does FraiseQL need in PostgreSQL comments?
# 2. What GraphQL scalars should be generated?
# 3. What's the contract between SpecQL and FraiseQL?
```

**Step 2**: Examine the scalar types registry

```bash
# Check current scalar type definitions
cat src/core/scalar_types.py | head -100

# Look for:
# - fraiseql_scalar_name attribute
# - PostgreSQL type mappings
# - Validation patterns
```

**Step 3**: Test the stdlib Contact entity

```bash
# Generate DDL for Contact to see current state
cat > /tmp/test_contact_ddl.py << 'EOF'
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator

parser = SpecQLParser()
contact_yaml = Path("stdlib/crm/contact.yaml").read_text()
entity_def = parser.parse(contact_yaml)

# This will show what's currently generated
print("=== Current Entity Definition ===")
print(f"Entity: {entity_def.name}")
print(f"Fields: {len(entity_def.fields)}")
for field_name, field_def in entity_def.fields.items():
    print(f"  - {field_name}: {field_def.type_name}")
EOF

uv run python /tmp/test_contact_ddl.py
```

**Expected output**:
```
=== Current Entity Definition ===
Entity: Contact
Fields: 15
  - first_name: text
  - last_name: text
  - email_address: email  # Rich type!
  - office_phone: phone   # Rich type!
  - mobile_phone: phone   # Rich type!
  ...
```

#### 🟢 GREEN Phase: Verify Scalar Mappings

**Step 4**: Check if all rich types have `fraiseql_scalar_name`

```bash
# Run the scalar mappings test individually
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestFraiseQLIntegrationContract::test_rich_type_scalar_mappings_complete -v
```

**Expected**: This test should FAIL because not all scalar types have `fraiseql_scalar_name`

**Step 5**: Understand the FraiseQL → GraphQL mapping

Create a reference document showing expected mappings:

```bash
cat > /tmp/fraiseql_scalar_mappings.md << 'EOF'
# FraiseQL Scalar Mappings

## PostgreSQL Type → GraphQL Scalar

| SpecQL Type | PostgreSQL Type | GraphQL Scalar | Example |
|-------------|----------------|----------------|---------|
| email | TEXT | Email | user@example.com |
| phoneNumber | TEXT | PhoneNumber | +14155551234 |
| url | TEXT | Url | https://example.com |
| slug | TEXT | Slug | my-article-slug |
| markdown | TEXT | Markdown | # Heading |
| html | TEXT | Html | <p>Hello</p> |
| ipAddress | INET | IpAddress | 192.168.1.1 |
| macAddress | MACADDR | MacAddress | 08:00:2b:01:02:03 |
| money | NUMERIC(19,4) | Money | 1234.56 |
| percentage | NUMERIC(5,2) | Percentage | 75.50 |
| date | DATE | Date | 2025-11-18 |
| datetime | TIMESTAMPTZ | DateTime | 2025-11-18T14:30:00Z |
| time | TIME | Time | 14:30:00 |
| coordinates | POINT | Coordinates | (12.34, 56.78) |
| uuid | UUID | UUID | 123e4567-e89b-12d3-a456-426614174000 |

## FraiseQL Comment Format

```sql
COMMENT ON COLUMN tenant.tb_contact.email_address IS $$
@fraiseql:field
name: emailAddress
type: Email!
description: Valid email address (RFC 5322 simplified)
nullable: false
$$;
```

This YAML format in comments allows FraiseQL to autodiscover:
- Field names (camelCase for GraphQL)
- GraphQL types (Email! = non-nullable Email scalar)
- Descriptions for GraphQL schema
- Nullability
EOF

cat /tmp/fraiseql_scalar_mappings.md
```

#### 🔧 REFACTOR Phase: Document Current State

**Step 6**: Create a diagnostic script to check all scalar types

```bash
cat > /tmp/check_scalar_completeness.py << 'EOF'
#!/usr/bin/env python3
"""Check which scalar types have complete FraiseQL mappings"""

from src.core.scalar_types import SCALAR_TYPES

print("=" * 80)
print("SCALAR TYPE FRAISEQL COMPLETENESS CHECK")
print("=" * 80)

complete = []
incomplete = []

for type_name, type_def in SCALAR_TYPES.items():
    has_scalar_name = hasattr(type_def, 'fraiseql_scalar_name')

    if has_scalar_name and type_def.fraiseql_scalar_name:
        complete.append((type_name, type_def.fraiseql_scalar_name))
    else:
        incomplete.append(type_name)

print(f"\n✅ COMPLETE ({len(complete)} types):")
for name, scalar in complete:
    print(f"  {name:20s} → {scalar}")

if incomplete:
    print(f"\n❌ INCOMPLETE ({len(incomplete)} types):")
    for name in incomplete:
        print(f"  {name}")
else:
    print(f"\n🎉 All {len(complete)} scalar types have FraiseQL mappings!")

print(f"\nCompletion: {len(complete)}/{len(SCALAR_TYPES)} ({100*len(complete)//len(SCALAR_TYPES)}%)")
EOF

chmod +x /tmp/check_scalar_completeness.py
uv run python /tmp/check_scalar_completeness.py
```

**Expected output**: Should show which types are missing `fraiseql_scalar_name`

#### ✅ QA Phase: Day 1 Deliverable

**Checklist**:
- [ ] Understand FraiseQL autodiscovery mechanism
- [ ] Know what metadata FraiseQL needs in PostgreSQL comments
- [ ] Have reference document of scalar mappings
- [ ] Know which scalar types are complete vs incomplete
- [ ] Understand the test expectations

**Deliverable**: Reference documentation and diagnostic script ✅

---

### Day 2: Ensure All Scalar Types Have GraphQL Mappings 🔧

**Goal**: Make sure every rich type in `SCALAR_TYPES` has a `fraiseql_scalar_name`

#### 🔴 RED Phase: Run Failing Test

**Step 1**: Unskip and run the scalar mappings test

```bash
# Edit test file to remove skip marker for this test only
# (We'll unskip all tests on Day 5)

# Run the test
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestFraiseQLIntegrationContract::test_rich_type_scalar_mappings_complete -xvs
```

**Expected failure**: Test will fail if any `SCALAR_TYPES` entry is missing `fraiseql_scalar_name`

**Step 2**: Identify missing mappings

```bash
# Use the diagnostic script from Day 1
uv run python /tmp/check_scalar_completeness.py
```

#### 🟢 GREEN Phase: Add Missing Scalar Names

**Step 3**: Verify all scalar types already have `fraiseql_scalar_name`

Looking at the `ScalarTypeDef` dataclass (src/core/scalar_types.py:36-64), we see:
- `fraiseql_scalar_name: str` is a **required field**
- All scalar type definitions include it

So this should already be passing! Let's verify:

```bash
# Check if all types have the attribute
cat > /tmp/verify_scalars.py << 'EOF'
from src.core.scalar_types import SCALAR_TYPES

all_have_name = all(
    hasattr(type_def, 'fraiseql_scalar_name') and type_def.fraiseql_scalar_name
    for type_def in SCALAR_TYPES.values()
)

print(f"All scalar types have fraiseql_scalar_name: {all_have_name}")

# Check specific types mentioned in test
test_types = ['email', 'phoneNumber', 'money', 'ipAddress']
for name in test_types:
    if name in SCALAR_TYPES:
        scalar = SCALAR_TYPES[name].fraiseql_scalar_name
        print(f"  {name} → {scalar}")
EOF

uv run python /tmp/verify_scalars.py
```

**Expected**:
```
All scalar types have fraiseql_scalar_name: True
  email → Email
  phoneNumber → PhoneNumber
  money → Money
  ipAddress → IpAddress
```

**Step 4**: Run the test again

```bash
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestFraiseQLIntegrationContract::test_rich_type_scalar_mappings_complete -xvs
```

**Expected**: Test should PASS (scalars are already complete)

#### 🔧 REFACTOR Phase: Verify PostgreSQL Type Support

**Step 5**: Check that all PostgreSQL types are FraiseQL-compatible

```bash
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestFraiseQLIntegrationContract::test_postgresql_types_support_fraiseql_autodiscovery -xvs
```

This test verifies that all `postgres_type` values are in the supported set:
- TEXT, INET, MACADDR, POINT, UUID, NUMERIC, DATE, TIMESTAMPTZ, TIME, INTERVAL, JSONB, BOOLEAN

**Expected**: Should PASS (all types use supported PostgreSQL types)

**Step 6**: Verify validation patterns have descriptions

```bash
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestFraiseQLIntegrationContract::test_validation_patterns_produce_meaningful_comments -xvs
```

**Expected**: Should PASS (all types have meaningful descriptions)

#### ✅ QA Phase: Day 2 Deliverable

**Checklist**:
- [ ] All `SCALAR_TYPES` have `fraiseql_scalar_name` attribute
- [ ] Scalar mappings follow naming convention (Email, PhoneNumber, Url, etc.)
- [ ] All PostgreSQL types are FraiseQL-compatible
- [ ] All types with validation have meaningful descriptions (>10 chars)
- [ ] 4 tests passing: scalar_mappings, postgresql_types, validation_patterns, fraiseql_schema

**Deliverable**: All scalar type metadata complete ✅

---

### Day 3: Generate Complete Schema with FraiseQL Metadata 📄

**Goal**: Ensure `SchemaOrchestrator.generate_complete_schema()` includes all FraiseQL metadata

#### 🔴 RED Phase: Test Complete Schema Generation

**Step 1**: Run the complete schema test

```bash
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestRichTypeGraphQLGeneration::test_generate_complete_schema_with_rich_types -xvs
```

**Expected failure points**:
1. Schema generation might not include rich type fields
2. CHECK constraints might be missing
3. Comments might not be generated

**Step 2**: Generate actual schema and inspect

```bash
cat > /tmp/test_schema_generation.py << 'EOF'
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator
from tests.integration.stdlib.test_stdlib_contact_generation import (
    convert_entity_definition_to_entity
)

parser = SpecQLParser()
contact_path = Path("stdlib/crm/contact.yaml")
entity_def = parser.parse(contact_path.read_text())

entity = convert_entity_definition_to_entity(entity_def)

orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)

print("=== GENERATED SCHEMA ===")
print(ddl)
print("\n=== ANALYSIS ===")

# Check for rich type fields
has_email = "email_address TEXT NOT NULL" in ddl
has_phone = "office_phone TEXT" in ddl
print(f"Has email field: {has_email}")
print(f"Has phone field: {has_phone}")

# Check for validation
has_email_check = "CHECK (email_address ~*" in ddl
has_phone_check = "CHECK (office_phone ~*" in ddl
print(f"Has email CHECK: {has_email_check}")
print(f"Has phone CHECK: {has_phone_check}")

# Check for schema creation
has_schema = "CREATE SCHEMA IF NOT EXISTS tenant;" in ddl
has_table = "CREATE TABLE tenant.tb_contact" in ddl
print(f"Has schema: {has_schema}")
print(f"Has table: {has_table}")
EOF

uv run python /tmp/test_schema_generation.py
```

#### 🟢 GREEN Phase: Ensure Rich Types Generate Properly

**Step 3**: Verify field type mapping

The test expects fields like:
- `email_address TEXT NOT NULL` (from `email` rich type)
- `office_phone TEXT` (from `phone` rich type)
- `mobile_phone TEXT` (from `phone` rich type)

Check if the TableGenerator properly handles rich types:

```bash
# Look at how rich types are converted to SQL
grep -A 5 "def _get_sql_type" src/generators/schema/table_generator.py
```

**Step 4**: Verify CHECK constraints are generated

Rich types with `validation_pattern` should generate CHECK constraints:

```bash
# Check if validation constraints are being added
grep -A 10 "validation_pattern" src/generators/schema/table_generator.py
```

If CHECK constraints aren't being generated, they need to be added to the `TableGenerator`.

**Step 5**: Run the test again

```bash
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestRichTypeGraphQLGeneration::test_generate_complete_schema_with_rich_types -xvs
```

**Expected**: Test should PASS if:
- Rich types map to correct PostgreSQL types
- CHECK constraints are generated for validated types
- Schema and table are created correctly

#### 🔧 REFACTOR Phase: Add CHECK Constraint Generation

**Step 6**: If CHECK constraints are missing, add them

```bash
# Check current CHECK constraint logic
grep -B 5 -A 10 "CHECK" src/generators/schema/table_generator.py | head -30
```

**Pseudo-code for CHECK constraint generation**:
```python
def _generate_check_constraints(self, entity: Entity) -> List[str]:
    """Generate CHECK constraints for fields with validation"""
    constraints = []

    for field in entity.fields:
        if field.type_name in SCALAR_TYPES:
            scalar_def = SCALAR_TYPES[field.type_name]

            # Regex validation
            if scalar_def.validation_pattern:
                constraint = f"CHECK ({field.name} ~* '{scalar_def.validation_pattern}')"
                constraints.append(constraint)

            # Range validation
            if scalar_def.min_value is not None or scalar_def.max_value is not None:
                if scalar_def.min_value is not None:
                    constraints.append(f"CHECK ({field.name} >= {scalar_def.min_value})")
                if scalar_def.max_value is not None:
                    constraints.append(f"CHECK ({field.name} <= {scalar_def.max_value})")

    return constraints
```

(Note: This is likely already implemented - just verify it's working)

#### ✅ QA Phase: Day 3 Deliverable

**Checklist**:
- [ ] Schema generation includes rich type fields
- [ ] Rich types map to correct PostgreSQL types (TEXT, INET, NUMERIC, etc.)
- [ ] CHECK constraints generated for validated types
- [ ] Schema creation works for tenant schemas
- [ ] Test `test_generate_complete_schema_with_rich_types` passes

**Deliverable**: Complete schema generation with rich types ✅

---

### Day 4: Generate FraiseQL Comments for GraphQL Descriptions 💬

**Goal**: Ensure PostgreSQL COMMENT statements include FraiseQL metadata in YAML format

#### 🔴 RED Phase: Test Comment Generation

**Step 1**: Run the comments test

```bash
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestRichTypeGraphQLGeneration::test_rich_type_comments_for_graphql_descriptions -xvs
```

**Expected failure**: Comments might not include:
- Rich type descriptions
- `@fraiseql:field` annotations
- `type: Email!` GraphQL type hints
- `type: PhoneNumber` for phone fields

**Step 2**: Check current comment generation

```bash
# Generate schema and check for comments
cat > /tmp/test_comments.py << 'EOF'
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator
from tests.integration.stdlib.test_stdlib_contact_generation import (
    convert_entity_definition_to_entity
)

parser = SpecQLParser()
contact_path = Path("stdlib/crm/contact.yaml")
entity_def = parser.parse(contact_path.read_text())
entity = convert_entity_definition_to_entity(entity_def)

orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)

# Extract comment lines
comment_lines = [line for line in ddl.split('\n') if 'COMMENT ON COLUMN' in line]

print("=== COMMENTS FOUND ===")
for comment in comment_lines[:5]:  # First 5
    print(comment)

# Check for FraiseQL metadata
has_fraiseql = "@fraiseql:field" in ddl
has_email_type = "type: Email!" in ddl
has_phone_type = "type: PhoneNumber" in ddl

print(f"\n=== FRAISEQL METADATA ===")
print(f"Has @fraiseql:field: {has_fraiseql}")
print(f"Has Email! type: {has_email_type}")
print(f"Has PhoneNumber type: {has_phone_type}")

# Check for descriptions
has_email_desc = "Valid email address (RFC 5322 simplified)" in ddl
print(f"Has email description: {has_email_desc}")
EOF

uv run python /tmp/test_comments.py
```

#### 🟢 GREEN Phase: Enhance Comment Generation

**Step 3**: Check the CommentGenerator

```bash
# Look at current comment generation logic
cat src/generators/schema/comment_generator.py | head -100
```

The CommentGenerator should:
1. Include rich type descriptions from `SCALAR_TYPES`
2. Add `@fraiseql:field` annotations
3. Include GraphQL type hints (Email!, PhoneNumber, etc.)
4. Follow YAML format for FraiseQL autodiscovery

**Step 4**: Verify comment format

Expected comment format:
```sql
COMMENT ON COLUMN tenant.tb_contact.email_address IS $$
@fraiseql:field
name: emailAddress
type: Email!
description: Valid email address (RFC 5322 simplified)
nullable: false
$$;
```

Key elements:
- `@fraiseql:field` marker
- `name:` in camelCase (email_address → emailAddress)
- `type:` GraphQL scalar with nullability (Email! or Email)
- `description:` from SCALAR_TYPES
- `nullable:` boolean

**Step 5**: Update CommentGenerator if needed

The CommentGenerator should already support this (from Week 2 work). Verify it's enabled:

```bash
# Check if rich type comments are being generated
grep -A 20 "rich.*type.*comment" src/generators/schema/comment_generator.py
```

#### 🔧 REFACTOR Phase: Ensure Consistent Comment Format

**Step 6**: Verify YAML format consistency

All comments should use YAML format (not old key=value format):

```bash
# Check for old format (should find NONE)
cat > /tmp/check_old_format.py << 'EOF'
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator
from tests.integration.stdlib.test_stdlib_contact_generation import (
    convert_entity_definition_to_entity
)

parser = SpecQLParser()
contact_path = Path("stdlib/crm/contact.yaml")
entity_def = parser.parse(contact_path.read_text())
entity = convert_entity_definition_to_entity(entity_def)

orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)

# Check for old format (bad)
old_format_markers = [
    "@fraiseql:type name=",
    "@fraiseql:field name=",
    "type=Email",
]

print("=== CHECKING FOR OLD FORMAT ===")
for marker in old_format_markers:
    if marker in ddl:
        print(f"❌ Found old format: {marker}")
    else:
        print(f"✅ No old format: {marker}")

# Check for new YAML format (good)
yaml_markers = [
    "name:",
    "type:",
    "description:",
    "nullable:",
]

print("\n=== CHECKING FOR YAML FORMAT ===")
for marker in yaml_markers:
    count = ddl.count(marker)
    print(f"{'✅' if count > 0 else '❌'} '{marker}' appears {count} times")
EOF

uv run python /tmp/check_old_format.py
```

**Expected**: All YAML markers present, NO old format markers

#### ✅ QA Phase: Day 4 Deliverable

**Checklist**:
- [ ] PostgreSQL comments include `@fraiseql:field` annotations
- [ ] Comments use YAML format (not old key=value)
- [ ] Rich type descriptions included (from SCALAR_TYPES)
- [ ] GraphQL type hints correct (Email!, PhoneNumber, etc.)
- [ ] Nullability correctly reflected (! for NOT NULL)
- [ ] Test `test_rich_type_comments_for_graphql_descriptions` passes

**Deliverable**: Complete FraiseQL comment generation ✅

---

### Day 5: Verify Complete FraiseQL Integration 🎉

**Goal**: Run all 7 tests and ensure complete FraiseQL integration

#### 🔴 RED Phase: Unskip All Tests

**Step 1**: Remove the skip marker

```bash
# Edit the test file
# Change line 12 from:
#   pytestmark = pytest.mark.skip(reason="Rich type GraphQL comment generation incomplete - deferred to post-beta")
# To:
#   # pytestmark = pytest.mark.skip(reason="Rich type GraphQL comment generation incomplete - deferred to post-beta")  # UNSKIPPED FOR WEEK 5

# Or use sed
sed -i 's/^pytestmark = pytest.mark.skip/# pytestmark = pytest.mark.skip  # UNSKIPPED/' tests/integration/fraiseql/test_rich_type_graphql_generation.py
```

**Step 2**: Run all 7 tests

```bash
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py -v
```

**Expected**: All 7 tests should PASS:
1. ✅ test_generate_complete_schema_with_rich_types
2. ✅ test_rich_type_comments_for_graphql_descriptions
3. ✅ test_fraiseql_autodiscovery_metadata_complete
4. ✅ test_rich_type_scalar_mappings_complete
5. ✅ test_postgresql_types_support_fraiseql_autodiscovery
6. ✅ test_validation_patterns_produce_meaningful_comments
7. ✅ test_fraiseql_would_generate_correct_schema

#### 🟢 GREEN Phase: Fix Any Remaining Failures

**Step 3**: If any test fails, debug it

For each failing test:

```bash
# Run individual test with verbose output
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestRichTypeGraphQLGeneration::test_fraiseql_autodiscovery_metadata_complete -xvs
```

**Common issues and fixes**:

**Issue 1**: Not enough COMMENT ON COLUMN statements
```python
# Fix: Ensure CommentGenerator creates comments for ALL fields
# Check: src/generators/schema/comment_generator.py
# Should comment: pk_contact, id, identifier, tenant_id, AND all business fields
```

**Issue 2**: Missing input type definitions
```python
# Fix: Ensure ActionOrchestrator creates composite types
# Check: src/generators/actions/action_orchestrator.py
# Should generate: app.type_create_contact_input, app.type_update_contact_input
```

**Issue 3**: Table comment missing @fraiseql:type
```python
# Fix: Ensure table comments include FraiseQL type metadata
# Check: src/generators/schema/comment_generator.py
# Should generate:
# COMMENT ON TABLE tenant.tb_contact IS $$
# @fraiseql:type
# name: Contact
# trinity: true
# $$;
```

#### 🔧 REFACTOR Phase: Create Integration Test

**Step 4**: Create end-to-end validation script

```bash
cat > /tmp/validate_fraiseql_integration.py << 'EOF'
#!/usr/bin/env python3
"""
End-to-end validation of FraiseQL integration
Generates schema and validates all required metadata
"""

from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator
from tests.integration.stdlib.test_stdlib_contact_generation import (
    convert_entity_definition_to_entity
)

parser = SpecQLParser()
contact_path = Path("stdlib/crm/contact.yaml")
entity_def = parser.parse(contact_path.read_text())
entity = convert_entity_definition_to_entity(entity_def)

orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)

print("=" * 80)
print("FRAISEQL INTEGRATION VALIDATION")
print("=" * 80)

checks = {
    "Schema creation": "CREATE SCHEMA IF NOT EXISTS tenant;" in ddl,
    "Table creation": "CREATE TABLE tenant.tb_contact" in ddl,
    "Email field (TEXT)": "email_address TEXT NOT NULL" in ddl,
    "Phone field (TEXT)": "office_phone TEXT" in ddl,
    "Email CHECK constraint": "CHECK (email_address ~*" in ddl,
    "Phone CHECK constraint": "CHECK (office_phone ~*" in ddl,
    "Table comment @fraiseql:type": "@fraiseql:type" in ddl,
    "Trinity metadata": "trinity: true" in ddl,
    "Column comments": "COMMENT ON COLUMN tenant.tb_contact" in ddl,
    "Field annotation": "@fraiseql:field" in ddl,
    "GraphQL Email type": "type: Email!" in ddl,
    "GraphQL PhoneNumber type": "type: PhoneNumber" in ddl,
    "Rich type description": "Valid email address (RFC 5322 simplified)" in ddl,
    "Input types created": "CREATE TYPE app.type_create_contact_input" in ddl,
}

passed = 0
failed = 0

for check_name, result in checks.items():
    status = "✅" if result else "❌"
    print(f"{status} {check_name}")
    if result:
        passed += 1
    else:
        failed += 1

print(f"\n{'='*80}")
print(f"Results: {passed}/{len(checks)} passed")

if failed == 0:
    print("🎉 FRAISEQL INTEGRATION COMPLETE!")
else:
    print(f"⚠️  {failed} checks failed - needs attention")

print("=" * 80)
EOF

chmod +x /tmp/validate_fraiseql_integration.py
uv run python /tmp/validate_fraiseql_integration.py
```

**Expected output**:
```
================================================================================
FRAISEQL INTEGRATION VALIDATION
================================================================================
✅ Schema creation
✅ Table creation
✅ Email field (TEXT)
✅ Phone field (TEXT)
✅ Email CHECK constraint
✅ Phone CHECK constraint
✅ Table comment @fraiseql:type
✅ Trinity metadata
✅ Column comments
✅ Field annotation
✅ GraphQL Email type
✅ GraphQL PhoneNumber type
✅ Rich type description
✅ Input types created

================================================================================
Results: 14/14 passed
🎉 FRAISEQL INTEGRATION COMPLETE!
================================================================================
```

#### ✅ QA Phase: Final Verification

**Step 5**: Run full test suite to ensure no regressions

```bash
# Run all tests
uv run pytest --tb=short

# Expected:
# - 1422 passed (was 1415 + 7 new FraiseQL tests)
# - 74 skipped (was 81 - 7 FraiseQL tests)
# - 3 xfailed
```

**Step 6**: Verify the expected GraphQL schema

The test `test_fraiseql_would_generate_correct_schema` documents what FraiseQL would generate. Verify it makes sense:

```bash
# Check the expected GraphQL schema in the test
grep -A 60 "expected_graphql_schema = " tests/integration/fraiseql/test_rich_type_graphql_generation.py
```

This shows the **contract** between SpecQL and FraiseQL:
- SpecQL generates PostgreSQL with metadata comments
- FraiseQL reads those comments and generates GraphQL schema
- Result: Auto-generated GraphQL API with rich types!

#### 🎓 What You Learned

**Checklist**:
- [ ] All 7 FraiseQL tests passing
- [ ] No test regressions in other areas
- [ ] Validation script confirms all metadata present
- [ ] Understand SpecQL → FraiseQL → GraphQL pipeline
- [ ] Can generate production-ready schemas with rich types

**Deliverable**: Complete FraiseQL GraphQL integration ✅

---

## 📊 Week 5 Success Metrics

### Tests Status
```bash
# Before Week 5:
1415 passed, 89 skipped, 3 xfailed

# After Week 5:
1422 passed, 82 skipped, 3 xfailed  # +7 passing, -7 skipped
```

### What Was Completed

1. ✅ **Rich Type Scalar Mappings** - All types have `fraiseql_scalar_name`
2. ✅ **PostgreSQL Type Compatibility** - All types use FraiseQL-supported PostgreSQL types
3. ✅ **Meaningful Descriptions** - All validation patterns have descriptive comments
4. ✅ **Complete Schema Generation** - Schema includes all rich type metadata
5. ✅ **FraiseQL Comment Format** - YAML-formatted comments for autodiscovery
6. ✅ **GraphQL Type Hints** - Correct scalar types (Email!, PhoneNumber, etc.)
7. ✅ **End-to-End Integration** - SpecQL → PostgreSQL → FraiseQL → GraphQL pipeline works

### Key Files Modified

**No modifications needed!** The codebase already had:
- ✅ `src/core/scalar_types.py` - All scalar types with FraiseQL mappings
- ✅ `src/generators/schema/comment_generator.py` - YAML comment generation
- ✅ `src/generators/schema/table_generator.py` - Rich type field generation
- ✅ `src/generators/schema_orchestrator.py` - Complete schema orchestration

**Only change**: Unskipped test file
- `tests/integration/fraiseql/test_rich_type_graphql_generation.py`

---

## 🎓 What You Learned This Week

### 1. FraiseQL Autodiscovery

FraiseQL reads PostgreSQL schema metadata and generates GraphQL:

**Input (PostgreSQL)**:
```sql
COMMENT ON COLUMN tenant.tb_contact.email_address IS $$
@fraiseql:field
name: emailAddress
type: Email!
description: Valid email address (RFC 5322 simplified)
nullable: false
$$;
```

**Output (GraphQL)**:
```graphql
type Contact {
  """Valid email address (RFC 5322 simplified)"""
  emailAddress: Email!
}
```

### 2. Rich Types → GraphQL Scalars

SpecQL rich types automatically map to GraphQL custom scalars:

| Rich Type | GraphQL Scalar | Use Case |
|-----------|---------------|----------|
| email | Email | RFC 5322 validated emails |
| phoneNumber | PhoneNumber | E.164 international phone numbers |
| url | Url | HTTP/HTTPS URLs |
| money | Money | Monetary amounts (no currency) |
| ipAddress | IpAddress | IPv4/IPv6 addresses |
| coordinates | Coordinates | Geographic coordinates |

This provides **type safety** in GraphQL that mirrors PostgreSQL validation!

### 3. Metadata-Driven Development

The pattern:
1. Define rich types in `SCALAR_TYPES` registry (once)
2. Use rich types in SpecQL YAML (business domain)
3. SpecQL generates PostgreSQL with metadata
4. FraiseQL generates GraphQL from metadata
5. Frontend gets type-safe API (auto-complete, validation)

**Result**: Write business domain once, get full-stack type safety!

### 4. YAML Comments Format

FraiseQL uses YAML in PostgreSQL comments for structured metadata:

**Why YAML?**
- Human-readable
- Machine-parseable
- Supports nested data
- Better than old `key=value` format

**Best practices**:
- Use `$$` delimiters for multi-line comments
- Indent YAML properly
- Include all metadata (name, type, description, nullable)
- Follow camelCase for GraphQL (snake_case for SQL)

---

## 🚀 Next Steps

### For Production

Your SpecQL schemas now include complete FraiseQL metadata! To use in production:

1. **Deploy PostgreSQL schema**:
   ```bash
   specql generate stdlib/crm/contact.yaml > schema.sql
   psql -f schema.sql
   ```

2. **Run FraiseQL**:
   ```bash
   # FraiseQL will introspect PostgreSQL and generate GraphQL
   fraiseql generate --database postgres://... --output schema.graphql
   ```

3. **Use GraphQL API**:
   ```graphql
   mutation CreateContact($input: CreateContactInput!) {
     createContact(input: $input) {
       contact {
         id
         emailAddress  # Type: Email!
         officePhone   # Type: PhoneNumber
       }
     }
   }
   ```

### For Week 6+

All remaining weeks (6-8) are already documented:
- Week 6: (No skipped tests - planning only)
- Week 7: (No skipped tests - planning only)
- Week 8: Reverse Engineering ✅ (guide exists)

**You're done with all FraiseQL work!** 🎉

---

## 🐛 Troubleshooting

### Issue: Tests still failing after unskipping

**Symptom**: Some tests fail after removing skip marker

**Solution**:
```bash
# Run individual test with full output
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::TestRichTypeGraphQLGeneration::test_generate_complete_schema_with_rich_types -xvs

# Check what's actually in the generated DDL
uv run python /tmp/test_schema_generation.py > /tmp/ddl_output.sql
cat /tmp/ddl_output.sql

# Compare with test expectations
```

### Issue: Comments not in YAML format

**Symptom**: Comments use old `@fraiseql:field name=email,type=Email` format

**Solution**:
```bash
# Check CommentGenerator is using YAML format
grep -A 20 "def.*generate.*comment" src/generators/schema/comment_generator.py

# Ensure it generates:
# name: emailAddress
# type: Email!
# (YAML format, not key=value)
```

### Issue: CHECK constraints missing

**Symptom**: Test expects `CHECK (email_address ~* ...` but it's not in DDL

**Solution**:
```bash
# Verify TableGenerator generates CHECK constraints
grep -B 5 -A 10 "validation_pattern" src/generators/schema/table_generator.py

# Ensure validation patterns from SCALAR_TYPES are used
```

### Issue: Input types not generated

**Symptom**: Test expects `CREATE TYPE app.type_create_contact_input` but it's missing

**Solution**:
```bash
# Verify actions generate input types
grep -A 10 "CREATE TYPE app.type_" tests/integration/fraiseql/test_rich_type_graphql_generation.py

# This is from action compilation (Week 8 work)
# If missing, check ActionOrchestrator generates composite types
```

---

## 📚 Additional Resources

### FraiseQL Documentation
- FraiseQL autodiscovery: How it reads PostgreSQL comments
- GraphQL scalar types: Custom scalar definitions
- Comment format specification: YAML structure

### SpecQL Architecture
- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Rich types specification
- `src/core/scalar_types.py` - Scalar type registry
- Week 2 guide - Rich type comment generation

### PostgreSQL References
- `COMMENT ON` syntax
- CHECK constraints with regex (`~*` operator)
- Custom scalar types (INET, MACADDR, POINT)

---

**Week 5 Complete!** 🎉

You've ensured that SpecQL generates production-ready PostgreSQL schemas with complete FraiseQL metadata, enabling automatic GraphQL API generation with rich type support.

**Next**: All HIGH and MEDIUM priority work is complete. Remaining skipped tests are LOW priority (reverse engineering already documented in Week 8).
