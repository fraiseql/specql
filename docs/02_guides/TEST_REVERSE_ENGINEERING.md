# Test Reverse Engineering Guide

**Last Updated**: 2025-11-20
**Version**: v0.5.0-beta

## Overview

### What is Test Reverse Engineering?

Test reverse engineering analyzes existing test files to understand what they test, extract test logic, and convert tests into a universal, language-agnostic format. Instead of manually reading through test code, you get structured insights about test coverage, scenarios, and gaps.

**Why it matters**:
- **Coverage analysis**: Know exactly what's tested (and what's missing)
- **Framework migration**: Convert tests between frameworks (pgTAP ↔ pytest)
- **Documentation**: Generate test documentation automatically
- **Quality assurance**: Identify weak test coverage areas
- **Maintenance**: Understand legacy test suites quickly

### Use Cases

#### Coverage Analysis
Understand what your existing tests actually cover:
```bash
specql reverse-tests tests/*.sql --analyze-coverage
# Output: Detailed coverage report with gaps and suggestions
```

#### Framework Migration
Convert between test frameworks:
```bash
# Convert pgTAP tests to pytest
specql reverse-tests tests/*.sql --format pytest --output-dir tests/converted/

# Convert pytest tests to pgTAP
specql reverse-tests tests/*.py --format pgtap --output-dir tests/converted/
```

#### Test Documentation
Generate documentation from test code:
```bash
specql reverse-tests tests/ --format markdown --output-dir docs/tests/
# Creates comprehensive test documentation
```

#### Gap Detection
Find untested business logic:
```bash
specql reverse-tests tests/ --analyze-gaps --entity=Contact
# Identifies missing test scenarios
```

## Quick Start

### Step 1: Parse a pgTAP Test File

Create a simple pgTAP test file:

```sql
-- tests/test_contact_crud.sql
BEGIN;
SELECT plan(3);

-- Test: Create contact successfully
SELECT lives_ok(
    $$SELECT app.create_contact(
        '01232122-0000-0000-2000-000000000001'::UUID,
        '01232122-0000-0000-2000-000000000002'::UUID,
        '{"email": "test@example.com", "first_name": "Test"}'::JSONB
    )$$,
    'Create contact should succeed'
);

-- Test: Duplicate email should fail
SELECT throws_ok(
    $$SELECT app.create_contact(
        '01232122-0000-0000-2000-000000000001'::UUID,
        '01232122-0000-0000-2000-000000000002'::UUID,
        '{"email": "test@example.com"}'::JSONB
    )$$,
    'Duplicate email should be rejected'
);

-- Test: Read contact by ID
SELECT ok(
    (SELECT app.get_contact('01232122-0000-0000-2000-000000000001'::UUID)).status = 'success',
    'Get contact should succeed'
);

SELECT * FROM finish();
ROLLBACK;
```

Parse it with SpecQL:

```bash
specql reverse-tests tests/test_contact_crud.sql --preview

# Output:
# 📄 Parsed test_contact_crud.sql
# Entity: Contact (detected)
# Framework: pgtap
# Scenarios: 3
#
# 📊 Test Scenarios:
#   1. create_contact_success
#      Category: crud_create
#      Description: Create contact should succeed
#      Assertions: 1 (lives_ok)
#
#   2. create_contact_duplicate_fail
#      Category: crud_create
#      Description: Duplicate email should be rejected
#      Assertions: 1 (throws_ok)
#
#   3. get_contact_success
#      Category: crud_read
#      Description: Get contact should succeed
#      Assertions: 1 (ok)
#
# ✅ Parsing complete
```

### Step 2: Parse a pytest Test File

Create a pytest integration test:

```python
# tests/test_contact_integration.py
import pytest
from uuid import UUID

class TestContactIntegration:
    def test_create_contact_success(self, clean_db):
        """Test creating Contact via app.create function"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        with clean_db.cursor() as cur:
            cur.execute(
                "SELECT app.create_contact(%s::UUID, %s::UUID, %s::JSONB)",
                (tenant_id, user_id, {"email": "test@example.com"})
            )
            result = cur.fetchone()[0]

        assert result['status'] == 'success'
        assert result['object_data']['id'] is not None

    def test_create_duplicate_email_fails(self, clean_db):
        """Test that duplicate emails are rejected"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        # First contact
        with clean_db.cursor() as cur:
            cur.execute("SELECT app.create_contact(%s::UUID, %s::UUID, %s::JSONB)",
                       (tenant_id, user_id, {"email": "test@example.com"}))
            result1 = cur.fetchone()[0]
            assert result1['status'] == 'success'

        # Duplicate should fail
        with clean_db.cursor() as cur:
            cur.execute("SELECT app.create_contact(%s::UUID, %s::UUID, %s::JSONB)",
                       (tenant_id, user_id, {"email": "test@example.com"}))
            result2 = cur.fetchone()[0]
            assert result2['status'] == 'failed'
```

Parse it:

```bash
specql reverse-tests tests/test_contact_integration.py --preview

# Output:
# 📄 Parsed test_contact_integration.py
# Entity: Contact (detected)
# Framework: pytest
# Scenarios: 2
#
# 📊 Test Scenarios:
#   1. test_create_contact_success
#      Category: crud_create
#      Description: Test creating Contact via app.create function
#      Setup: clean_db fixture
#      Assertions: 2 (status, id check)
#
#   2. test_create_duplicate_email_fails
#      Category: crud_create
#      Description: Test that duplicate emails are rejected
#      Setup: clean_db fixture, create first contact
#      Assertions: 2 (first success, second failed)
#
# ✅ Parsing complete
```

### Step 3: Export to TestSpec Format

Convert to universal YAML format:

```bash
# Export as YAML
specql reverse-tests tests/test_contact_*.sql tests/test_contact_*.py \
    --format yaml \
    --output-dir specs/

# Output:
# 📄 Generated specs/test_contact_spec.yaml
# 📄 Generated specs/test_contact_integration_spec.yaml
```

**Result**: `specs/test_contact_spec.yaml`

```yaml
entity_name: Contact
test_framework: pgtap
source_language: pgtap

scenarios:
  - name: create_contact_success
    category: crud_create
    description: Create contact should succeed
    assertions:
      - type: lives_ok
        target: app.create_contact function call
        expected: true
        message: Create contact should succeed

  - name: create_contact_duplicate_fail
    category: crud_create
    description: Duplicate email should be rejected
    assertions:
      - type: throws_ok
        target: app.create_contact with duplicate email
        expected: exception
        message: Duplicate email should be rejected

  - name: get_contact_success
    category: crud_read
    description: Get contact should succeed
    assertions:
      - type: ok
        target: app.get_contact result status
        expected: success
        message: Get contact should succeed
```

## Supported Test Frameworks

### pgTAP (PostgreSQL Unit Tests)

**Best for**: Database-centric testing, schema validation, stored procedure testing

**Supported assertions**:
- `has_table`, `has_column`, `has_index` - Schema validation
- `lives_ok`, `throws_ok` - Function execution testing
- `ok`, `is`, `isnt` - Value comparison
- `bag_eq`, `set_eq` - Set comparison
- Custom pgTAP assertions

**Example parsing**:
```bash
specql reverse-tests tests/test_*_structure.sql --framework pgtap
```

### pytest (Python Integration Tests)

**Best for**: End-to-end testing, API testing, complex workflows

**Supported patterns**:
- `assert` statements (direct and via pytest helpers)
- `pytest.raises` context managers
- Database fixtures and setup
- Class-based test organization
- Parameterized tests

**Example parsing**:
```bash
specql reverse-tests tests/test_*_integration.py --framework pytest
```

### Future Support

**Planned frameworks**:
- **Jest**: JavaScript/React testing
- **JUnit**: Java unit testing
- **RSpec**: Ruby testing
- **xUnit**: .NET testing

**Migration paths**:
```bash
# Future: Convert between frameworks
specql reverse-tests tests/jest/ --format junit --output-dir tests/converted/
```

## TestSpec Format

### Universal Test Specification

TestSpec is SpecQL's language-agnostic test format that captures the essence of what tests do, regardless of the framework they use.

**Why language-agnostic?**
- **Framework independence**: Tests can be converted between frameworks
- **Documentation**: Clear, readable test specifications
- **Analysis**: Easy to analyze coverage and gaps
- **Generation**: Source for generating new tests

### TestSpec YAML Structure

```yaml
# Top-level metadata
entity_name: Contact                    # Entity being tested
test_framework: pgtap                  # Original framework
source_language: pgtap                 # Source language
source_file: tests/test_contact.sql    # Original file path
parsed_at: 2025-11-20T10:30:00Z       # When parsed

# Test scenarios
scenarios:
  - name: create_contact_success        # Unique scenario identifier
    category: crud_create              # Test category
    description: Create contact should succeed  # Human-readable description

    # Setup (optional)
    setup:
      - type: insert_fixture           # Setup action type
        table: tenant                  # Target table
        data:                          # Data to insert
          id: "01232122-0000-0000-2000-000000000001"
          name: "Test Tenant"

    # Test steps
    steps:
      - action: call_function          # Action to perform
        function: app.create_contact   # Function name
        parameters:                    # Parameters
          - type: uuid
            value: "01232122-0000-0000-2000-000000000001"
          - type: uuid
            value: "01232122-0000-0000-2000-000000000002"
          - type: jsonb
            value: {"email": "test@example.com"}

    # Assertions
    assertions:
      - type: equals                    # Assertion type
        target: result.status          # What to check
        expected: success              # Expected value
        message: Create should succeed # Assertion message

      - type: is_not_null
        target: result.object_data.id
        message: Created contact should have ID

    # Cleanup (optional)
    cleanup:
      - type: delete_records
        table: contact
        condition: "email = 'test@example.com'"
```

### Assertion Types

| Type | Description | Example |
|------|-------------|---------|
| `equals` | Value equality | `result.status == 'success'` |
| `not_equals` | Value inequality | `result.status != 'failed'` |
| `is_null` | Null check | `result.data IS NULL` |
| `is_not_null` | Not null check | `contact.id IS NOT NULL` |
| `contains` | String/array contains | `error_msg CONTAINS 'duplicate'` |
| `matches_regex` | Regex match | `email ~ '@.*\\.com$'` |
| `greater_than` | Numeric comparison | `count > 0` |
| `less_than` | Numeric comparison | `age < 150` |
| `throws_exception` | Exception expected | `function should throw` |
| `lives_ok` | No exception expected | `function should succeed` |

### Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `structure` | Schema validation | Table exists, columns, constraints |
| `crud_create` | Create operations | Insert, validation, duplicates |
| `crud_read` | Read operations | Select by ID, filters, pagination |
| `crud_update` | Update operations | Modify fields, concurrency |
| `crud_delete` | Delete operations | Soft delete, cascade |
| `actions` | Business logic | State transitions, workflows |
| `edge_cases` | Error conditions | Invalid data, permissions |
| `integration` | End-to-end | Multi-step workflows |

## Coverage Analysis

### Analyzing What's Tested

Coverage analysis tells you exactly what your tests cover and what they miss.

```bash
specql reverse-tests tests/ --analyze-coverage --entity=Contact

# Output:
# 📊 Coverage Analysis for Contact Entity
#
# ✅ Well Covered (90-100%):
#   • Table structure (100%) - 5/5 scenarios
#   • Basic CRUD operations (95%) - 18/19 scenarios
#   • Primary key constraints (100%) - 3/3 scenarios
#   • qualify_lead action (100%) - 4/4 scenarios
#
# ⚠️ Partially Covered (50-89%):
#   • Error handling (70%) - 7/10 scenarios
#     Missing: Invalid email format, null values, oversized fields
#   • State transitions (60%) - 3/5 scenarios
#     Missing: Reverse transitions, invalid state changes
#   • Permission checks (50%) - 2/4 scenarios
#     Missing: Cross-tenant access, role-based restrictions
#
# ❌ Not Covered (0-49%):
#   • Concurrent updates - 0/5 scenarios
#   • Bulk operations - 0/3 scenarios
#   • Audit logging - 0/4 scenarios
#   • Performance under load - 0/2 scenarios
#
# 📈 Overall Coverage: 78%
# 🎯 Recommended: Add 15 more test scenarios
```

### Finding Gaps in Test Coverage

Gap analysis identifies missing test scenarios:

```bash
specql reverse-tests tests/ --analyze-gaps --entity=Contact --format markdown

# Output: docs/coverage_gaps.md
```

**Generated report**:

```markdown
# Test Coverage Gaps - Contact Entity

## Critical Gaps (High Priority)

### 1. Error Handling - Invalid Email Format
**Impact**: High - Data integrity
**Current**: 0 tests
**Recommended**: 3 tests
- `test_create_contact_invalid_email`
- `test_create_contact_malformed_email`
- `test_update_contact_email_validation`

**Example test**:
```sql
SELECT throws_ok(
    $$SELECT app.create_contact(
        '01232122-0000-0000-2000-000000000001'::UUID,
        '01232122-0000-0000-2000-000000000002'::UUID,
        '{"email": "not-an-email"}'::JSONB
    )$$,
    'Invalid email should be rejected'
);
```

### 2. Concurrent Update Handling
**Impact**: High - Data consistency
**Current**: 0 tests
**Recommended**: 2 tests
- `test_concurrent_contact_updates`
- `test_optimistic_locking`

### 3. Permission Validation
**Impact**: Medium - Security
**Current**: 1/4 tests
**Recommended**: 3 tests
- `test_cross_tenant_access_denied`
- `test_insufficient_permissions`
- `test_admin_override`

## Medium Priority Gaps

### 4. Bulk Operations
**Impact**: Medium - Performance
**Current**: 0 tests
**Recommended**: 2 tests
- `test_bulk_contact_import`
- `test_bulk_contact_update`

### 5. Edge Cases
**Impact**: Low - Robustness
**Current**: 2/8 tests
**Recommended**: 6 tests
- `test_contact_with_minimum_data`
- `test_contact_with_all_fields`
- `test_unicode_characters`
- `test_special_characters`
- `test_max_length_fields`
- `test_timezone_handling`
```

### Suggesting Missing Test Scenarios

The analyzer suggests specific test scenarios to add:

```bash
specql reverse-tests tests/ --suggest-tests --entity=Contact

# Output:
# 🤖 Suggested Test Scenarios for Contact
#
# 1. test_create_contact_invalid_email_format
#    Category: crud_create
#    Priority: high
#    Description: Test rejection of malformed email addresses
#    Template: Use throws_ok with invalid email patterns
#
# 2. test_concurrent_contact_updates
#    Category: crud_update
#    Priority: high
#    Description: Test optimistic locking for concurrent updates
#    Template: Use two connections updating same record
#
# 3. test_cross_tenant_access_denied
#    Category: security
#    Priority: medium
#    Description: Ensure contacts are properly isolated by tenant
#    Template: Try accessing contact from different tenant
#
# [... more suggestions ...]
```

## Use Cases

### 1. Coverage Analysis

**Scenario**: You have a large test suite and want to understand coverage

```bash
# Analyze all tests for Contact entity
specql reverse-tests tests/ --analyze-coverage --entity=Contact --output-dir reports/

# Result: reports/contact_coverage.html (interactive report)
```

**Benefits**:
- Visual coverage heatmap
- Drill-down by category
- Historical trends
- Gap prioritization

### 2. Framework Migration

**Scenario**: Migrating from pgTAP to pytest or vice versa

```bash
# Step 1: Parse existing tests
specql reverse-tests tests/pgtap/ --format testspec --output-dir specs/

# Step 2: Generate new framework tests
specql generate-tests entities/contact.yaml --from-spec specs/contact_spec.yaml --framework pytest

# Step 3: Validate migration
specql reverse-tests tests/pytest/ --compare specs/contact_spec.yaml
```

### 3. Test Documentation

**Scenario**: Generate documentation from test code

```bash
# Generate markdown documentation
specql reverse-tests tests/ --format markdown --output-dir docs/tests/

# Result: docs/tests/Contact.md
```

**Generated documentation**:

```markdown
# Contact Entity Tests

## Overview
- **Entity**: Contact
- **Test Files**: 4
- **Total Scenarios**: 55
- **Coverage**: 78%

## Test Categories

### CRUD Operations (18 scenarios)
- Create contact (success/failure cases)
- Read contact (by ID, filters)
- Update contact (fields, validation)
- Delete contact (soft delete)

### Business Actions (12 scenarios)
- Qualify lead action
- State transitions
- Permission checks

### Edge Cases (8 scenarios)
- Invalid data handling
- Error conditions
- Boundary testing

## Detailed Scenario List

### create_contact_success
**Category**: crud_create
**Framework**: pgTAP
**File**: test_contact_crud.sql:15

Test creating a contact with valid data.

**Assertions**:
- Function executes without error
- Returns success status
- Creates contact with valid ID

**Code**:
```sql
SELECT lives_ok(
    $$SELECT app.create_contact(...)::JSONB$$,
    'Create contact should succeed'
);
```

[... continues for all scenarios ...]
```

### 4. Gap Detection

**Scenario**: Find untested business logic in your application

```bash
# Step 1: Parse all tests
specql reverse-tests tests/ --format testspec --output-dir specs/

# Step 2: Analyze against entity definition
specql analyze-gaps entities/contact.yaml --specs specs/ --output-dir reports/

# Step 3: Generate missing tests
specql generate-tests entities/contact.yaml --fill-gaps reports/contact_gaps.yaml
```

## Examples

### Real-world pgTAP File

```sql
-- test_contact_actions.sql
BEGIN;
SELECT plan(8);

-- Setup test data
INSERT INTO crm.tenant (id, name) VALUES
    ('01232122-0000-0000-2000-000000000001'::UUID, 'Test Tenant');

INSERT INTO app.user (id, tenant_id, email) VALUES
    ('01232122-0000-0000-2000-000000000002'::UUID,
     '01232122-0000-0000-2000-000000000001'::UUID, 'test@example.com');

-- Test: Qualify lead succeeds
SELECT lives_ok(
    $$SELECT app.qualify_lead(
        '01232122-0000-0000-2000-000000000001'::UUID,
        '01232122-0000-0000-2000-000000000002'::UUID,
        '{"contact_id": "01232122-0000-0000-2000-000000000003"}'::UUID
    )$$,
    'Qualify lead should succeed for lead status'
);

-- Test: Qualify lead fails for non-lead
SELECT throws_ok(
    $$SELECT app.qualify_lead(
        '01232122-0000-0000-2000-000000000001'::UUID,
        '01232122-0000-0000-2000-000000000002'::UUID,
        '{"contact_id": "01232122-0000-0000-2000-000000000004"}'::UUID
    )$$,
    'not_a_lead',
    'Qualify lead should fail for customer status'
);

SELECT * FROM finish();
ROLLBACK;
```

**Parsed TestSpec**:

```yaml
entity_name: Contact
test_framework: pgtap
source_file: test_contact_actions.sql

scenarios:
  - name: qualify_lead_success
    category: actions
    description: Qualify lead should succeed for lead status
    setup:
      - type: insert
        table: tenant
        data: {id: "...", name: "Test Tenant"}
      - type: insert
        table: user
        data: {id: "...", tenant_id: "...", email: "test@example.com"}
    steps:
      - action: call_function
        function: app.qualify_lead
        parameters:
          - type: uuid
            value: "..."
    assertions:
      - type: lives_ok
        message: Qualify lead should succeed for lead status

  - name: qualify_lead_fails_non_lead
    category: actions
    description: Qualify lead should fail for customer status
    assertions:
      - type: throws_ok
        expected_error: not_a_lead
        message: Qualify lead should fail for customer status
```

### Real-world pytest File

```python
# test_contact_integration.py
import pytest
from uuid import UUID
import psycopg

class TestContactIntegration:
    @pytest.fixture
    def clean_db(self):
        """Clean database for each test"""
        conn = psycopg.connect("postgresql://test:test@localhost/test_db")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM crm.contact")
            cur.execute("DELETE FROM app.user")
            cur.execute("DELETE FROM crm.tenant")
        conn.commit()
        yield conn
        conn.close()

    def test_full_contact_workflow(self, clean_db):
        """Test complete contact lifecycle"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        # Create tenant and user
        with clean_db.cursor() as cur:
            cur.execute("""
                INSERT INTO crm.tenant (id, name) VALUES (%s, %s)
            """, (tenant_id, "Test Tenant"))

            cur.execute("""
                INSERT INTO app.user (id, tenant_id, email) VALUES (%s, %s, %s)
            """, (user_id, tenant_id, "test@example.com"))

        # Create contact
        with clean_db.cursor() as cur:
            cur.execute(
                "SELECT app.create_contact(%s::UUID, %s::UUID, %s::JSONB)",
                (tenant_id, user_id, {
                    "email": "contact@example.com",
                    "first_name": "John",
                    "last_name": "Doe"
                })
            )
            result = cur.fetchone()[0]
            contact_id = result['object_data']['id']

        assert result['status'] == 'success'
        assert contact_id is not None

        # Update contact
        with clean_db.cursor() as cur:
            cur.execute(
                "SELECT app.update_contact(%s::UUID, %s::UUID, %s::UUID, %s::JSONB)",
                (tenant_id, user_id, contact_id, {"first_name": "Jane"})
            )
            update_result = cur.fetchone()[0]

        assert update_result['status'] == 'success'

        # Qualify lead
        with clean_db.cursor() as cur:
            cur.execute(
                "SELECT app.qualify_lead(%s::UUID, %s::UUID, %s::UUID)",
                (tenant_id, user_id, contact_id)
            )
            action_result = cur.fetchone()[0]

        assert action_result['status'] == 'success'

        # Verify final state
        with clean_db.cursor() as cur:
            cur.execute("SELECT status FROM crm.contact WHERE id = %s", (contact_id,))
            final_status = cur.fetchone()[0]

        assert final_status == 'qualified'
```

### Coverage Analysis Output

```bash
specql reverse-tests tests/ --analyze-coverage --entity=Contact --verbose

# Output:
# 🔍 Analyzing Contact entity test coverage...
#
# 📊 Coverage Matrix:
# ┌─────────────────────┬─────────┬─────────┬─────────┬─────────┐
# │ Category           │ pgTAP   │ pytest  │ Total   │ %       │
# ├─────────────────────┼─────────┼─────────┼─────────┼─────────┤
# │ Structure          │ 5/5     │ 0/5     │ 5/5     │ 100%    │
# │ CRUD Create        │ 4/6     │ 3/6     │ 5/6     │ 83%     │
# │ CRUD Read          │ 3/4     │ 2/4     │ 4/4     │ 100%    │
# │ CRUD Update        │ 2/5     │ 1/5     │ 2/5     │ 40%     │
# │ CRUD Delete        │ 1/3     │ 0/3     │ 1/3     │ 33%     │
# │ Actions            │ 4/4     │ 2/4     │ 4/4     │ 100%    │
# │ Edge Cases         │ 2/8     │ 1/8     │ 2/8     │ 25%     │
# │ Integration        │ 0/5     │ 3/5     │ 3/5     │ 60%     │
# └─────────────────────┴─────────┴─────────┴─────────┴─────────┘
#
# 📈 Overall Coverage: 72% (30/42 scenarios)
#
# 🎯 Top Missing Scenarios:
# 1. test_update_contact_concurrent (CRUD Update) - Priority: High
# 2. test_delete_contact_cascade (CRUD Delete) - Priority: High
# 3. test_create_contact_invalid_data (Edge Cases) - Priority: Medium
# 4. test_bulk_contact_operations (Integration) - Priority: Medium
# 5. test_contact_permission_checks (Security) - Priority: High
#
# 💡 Recommendations:
# • Add 3 high-priority tests for data integrity
# • Add 4 medium-priority tests for edge cases
# • Consider adding performance tests for bulk operations
# • Review security testing coverage
#
# 📄 Detailed report saved to: reports/contact_coverage_20251120.html
```

## Advanced Usage

### Multiple Test Files

Process entire test directories:

```bash
# Process all test files
specql reverse-tests tests/ --recursive --verbose

# Process specific patterns
specql reverse-tests tests/test_contact*.sql tests/test_contact*.py

# Process with glob patterns
specql reverse-tests "tests/**/*.sql" "tests/**/*integration*.py"
```

### Custom Entity Mapping

When entity detection fails:

```bash
# Explicitly specify entity
specql reverse-tests tests/custom_tests.sql --entity=Contact --entity-schema=crm

# Map multiple entities
specql reverse-tests tests/ \
    --entity-mapping "test_user.sql:User" \
    --entity-mapping "test_order.sql:Order"
```

### Batch Processing

Process large test suites efficiently:

```bash
# Parallel processing (if supported)
specql reverse-tests tests/ --parallel 4

# Batch output
specql reverse-tests tests/ --batch-size 50 --output-dir specs/

# Incremental processing
specql reverse-tests tests/ --since "2025-11-15" --output-dir specs/
```

### Custom Output Formats

Generate different output formats:

```bash
# JSON format
specql reverse-tests tests/ --format json --output-dir specs/

# XML format (for CI tools)
specql reverse-tests tests/ --format xml --output-dir specs/

# CSV format (for spreadsheets)
specql reverse-tests tests/ --format csv --output-dir specs/
```

## Troubleshooting

### Parser Errors

**Problem**: "Failed to parse test file" error

**Common causes**:
- Unsupported test framework version
- Syntax errors in test file
- Complex test patterns not recognized

**Solutions**:
```bash
# Check file syntax
specql validate-tests tests/test_contact.sql

# Use verbose mode for details
specql reverse-tests tests/test_contact.sql --verbose --debug

# Try alternative parsing
specql reverse-tests tests/test_contact.sql --parser fallback
```

### Unsupported Test Patterns

**Problem**: "Unsupported assertion pattern" warning

**Common patterns**:
- Custom assertion functions
- Complex SQL expressions
- Non-standard test structures

**Solutions**:
```bash
# Skip unsupported tests
specql reverse-tests tests/ --skip-unsupported

# Manual annotation
# Add comments to help parser:
-- @specql:category crud_create
-- @specql:description Test custom validation
SELECT custom_assertion(...);
```

### Entity Detection Issues

**Problem**: "Could not detect entity" error

**Common causes**:
- Non-standard naming conventions
- Multiple entities in one file
- Indirect entity references

**Solutions**:
```bash
# Explicit entity specification
specql reverse-tests tests/test_custom.sql --entity=Contact

# Entity hints in test comments
-- @specql:entity Contact
-- @specql:schema crm
SELECT test_function(...);

# Multiple entities
specql reverse-tests tests/test_multi.sql \
    --entity-mapping "test_multi.sql:Contact,User,Order"
```

### Performance Issues

**Problem**: Parsing takes too long for large test suites

**Solutions**:
```bash
# Process in batches
specql reverse-tests tests/ --batch-size 20

# Parallel processing
specql reverse-tests tests/ --parallel $(nproc)

# Incremental updates
specql reverse-tests tests/ --since "2025-11-15"
```

### Inconsistent Results

**Problem**: Different results on repeated runs

**Common causes**:
- Non-deterministic test ordering
- Time-dependent tests
- External dependencies

**Solutions**:
```bash
# Use deterministic mode
specql reverse-tests tests/ --deterministic

# Exclude problematic files
specql reverse-tests tests/ --exclude "test_*_flaky.sql"

# Check for external dependencies
specql analyze-dependencies tests/ --output-dir reports/
```

### Missing TestSpec Fields

**Problem**: Incomplete TestSpec output

**Solutions**:
```bash
# Add manual annotations
-- @specql:description Test contact creation with validation
-- @specql:category crud_create
-- @specql:priority high

# Use enhanced parsing
specql reverse-tests tests/ --enhanced-parsing

# Post-process TestSpec
specql enhance-spec specs/contact_spec.yaml --add-descriptions
```

---

## Related Documentation

- [Test Generation Guide](TEST_GENERATION.md) - Generate tests from entity definitions
- [Entity Definition Guide](ENTITY_DEFINITION.md) - Define entities for testing
- [CLI Commands](CLI_COMMANDS.md) - Complete command reference

## Examples

See `docs/06_examples/test_reverse_engineering/` for complete working examples including:
- Sample test files for parsing
- TestSpec YAML outputs
- Coverage analysis reports
- Gap analysis examples

---

*Last updated: 2025-11-20 | Version: v0.5.0-beta*