# Week 2: Comprehensive Documentation

**Duration**: 12-15 hours
**Goal**: Complete user-facing documentation for test features
**Status**: Planning

---

## Overview

Create comprehensive, user-friendly documentation that enables users to:
1. Understand what test generation is and why it's valuable
2. Generate tests for their entities
3. Reverse engineer existing tests
4. Integrate tests into CI/CD pipelines
5. Customize and extend generated tests

By end of week, documentation should be production-ready for v0.5.0-beta release.

---

## Phase 2.1: Test Generation Guide

**Time Estimate**: 5-6 hours
**Priority**: CRITICAL

### Objective

Create comprehensive guide at `docs/02_guides/TEST_GENERATION.md` (2000+ words) that serves as the definitive resource for test generation.

### Content Structure

#### Section 1: Overview (30 min)

```markdown
# Test Generation Guide

**Last Updated**: 2025-11-20
**Version**: v0.5.0-beta

## What is Automatic Test Generation?

SpecQL automatically generates comprehensive test suites from your entity definitions. Instead of manually writing hundreds of test cases, you define your entity once and get:

- **pgTAP tests**: PostgreSQL unit tests for schema, CRUD, constraints, and business logic
- **pytest tests**: Python integration tests for end-to-end workflows

### Why Generate Tests?

**Problem**: Writing comprehensive tests is time-consuming and repetitive
- Manual test writing: 10-15 hours per entity
- Easy to forget edge cases
- Tests become outdated as schema changes
- Inconsistent coverage across entities

**Solution**: Automated test generation
- Generate 70+ tests in seconds
- Consistent coverage for all entities
- Tests stay synchronized with entity definitions
- Focus on business logic, not boilerplate

### What You'll Learn

This guide covers:
1. Quick start - Generate your first tests in 5 minutes
2. Understanding generated tests - What gets tested and why
3. Test types - pgTAP vs pytest
4. Customization - Adapting tests to your needs
5. CI/CD integration - Running tests automatically
6. Advanced usage - Options, filters, and optimization
7. Troubleshooting - Common issues and solutions

**Prerequisites**:
- SpecQL installed (`pip install specql-generator`)
- PostgreSQL database (for pgTAP tests)
- Basic understanding of SpecQL entity definitions
```

#### Section 2: Quick Start (45 min)

```markdown
## Quick Start

### Step 1: Define Your Entity

Create `entities/contact.yaml`:

\`\`\`yaml
entity: Contact
schema: crm

fields:
  email: email
  first_name: text
  last_name: text
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
\`\`\`

### Step 2: Generate Tests

\`\`\`bash
# Generate both pgTAP and pytest tests
specql generate-tests entities/contact.yaml

# Output shows:
# ✅ Generated 4 test file(s)
#    - tests/test_contact_structure.sql
#    - tests/test_contact_crud.sql
#    - tests/test_contact_actions.sql
#    - tests/test_contact_integration.py
\`\`\`

### Step 3: Review Generated Tests

\`\`\`bash
ls -la tests/
# test_contact_structure.sql     (50 lines, 10 tests)
# test_contact_crud.sql          (100 lines, 15 tests)
# test_contact_actions.sql       (80 lines, 12 tests)
# test_contact_integration.py    (150 lines, 18 tests)
# Total: 55 tests across 380 lines
\`\`\`

### Step 4: Run the Tests

**pgTAP tests**:
\`\`\`bash
# Install pgTAP extension (once)
psql -d your_db -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

# Run tests
pg_prove -d your_db tests/test_contact_*.sql

# Output:
# tests/test_contact_structure.sql .. ok
# tests/test_contact_crud.sql ........ ok
# tests/test_contact_actions.sql ..... ok
# All tests successful.
\`\`\`

**pytest tests**:
\`\`\`bash
# Install dependencies
pip install pytest psycopg[binary]

# Run tests
pytest tests/test_contact_integration.py -v

# Output:
# test_contact_integration.py::TestContactIntegration::test_create_contact_happy_path PASSED
# test_contact_integration.py::TestContactIntegration::test_create_duplicate_fails PASSED
# ... 16 more passed
# ==================== 18 passed in 2.31s ====================
\`\`\`

🎉 **Success!** You've generated and run 55 tests in under 5 minutes.
```

#### Section 3: Understanding Generated Tests (1 hour)

```markdown
## Understanding Generated Tests

### Test Categories

SpecQL generates four types of test files:

#### 1. Structure Tests (`test_{entity}_structure.sql`)

**Purpose**: Validate database schema matches entity definition

**Tests Generated**:
- Table existence
- Column existence and types
- Primary key constraints
- Foreign key relationships
- Unique constraints
- Check constraints
- Index existence
- Default values
- Audit column presence (created_at, updated_at, deleted_at)

**Example**:
\`\`\`sql
-- Test: Contact table should exist
SELECT has_table(
    'crm'::name,
    'tb_contact'::name,
    'Contact table should exist'
);

-- Test: Email column exists with correct type
SELECT has_column('crm', 'tb_contact', 'email');
SELECT col_type_is('crm', 'tb_contact', 'email', 'text');

-- Test: Primary key constraint
SELECT col_is_pk('crm', 'tb_contact', 'pk_contact');
\`\`\`

**Why it matters**: Catches schema drift, migration errors, and ensures database matches code expectations.

#### 2. CRUD Tests (`test_{entity}_crud.sql`)

**Purpose**: Validate create, read, update, delete operations

**Tests Generated**:
- Create entity (happy path)
- Create with duplicate identifier (error case)
- Create with invalid data (validation)
- Read/lookup entity by various keys
- Update entity fields
- Update with concurrency check
- Delete entity (soft delete)
- Verify record persistence

**Example**:
\`\`\`sql
-- Test: Create contact successfully
SELECT lives_ok(
    \$\$SELECT app.create_contact(
        '01232122-0000-0000-2000-000000000001'::UUID,
        '01232122-0000-0000-2000-000000000002'::UUID,
        '{"email": "test@example.com", "first_name": "Test"}'::JSONB
    )\$\$,
    'Create contact should succeed'
);

-- Test: Duplicate email should fail
SELECT throws_ok(
    \$\$SELECT app.create_contact(...same email...)\$\$,
    'Duplicate email should be rejected'
);
\`\`\`

**Why it matters**: Ensures basic CRUD operations work correctly and handle errors appropriately.

#### 3. Action Tests (`test_{entity}_actions.sql`)

**Purpose**: Validate business logic and state transitions

**Tests Generated** (per action):
- Action execution (happy path)
- Action with invalid preconditions (error case)
- State transitions
- Permission checks
- Side effects (notifications, cascades)

**Example**:
\`\`\`sql
-- Test: Qualify lead action succeeds
SELECT ok(
    (SELECT app.qualify_lead(contact_id)).status = 'success',
    'Qualify lead should succeed for lead status'
);

-- Test: Qualify lead fails for non-lead
SELECT ok(
    (SELECT app.qualify_lead(customer_id)).status LIKE 'failed:%',
    'Qualify lead should fail for customer status'
);
\`\`\`

**Why it matters**: Validates business rules, state machines, and ensures actions behave correctly.

#### 4. Integration Tests (`test_{entity}_integration.py`)

**Purpose**: End-to-end workflow testing in Python

**Tests Generated**:
- Full CRUD workflow
- Create → Read → Update → Delete sequence
- Duplicate detection
- Action execution
- Error handling
- Database cleanup (fixtures)

**Example**:
\`\`\`python
def test_create_contact_happy_path(self, clean_db):
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
\`\`\`

**Why it matters**: Validates real-world usage patterns and integration with application code.

### Test Coverage Matrix

For a typical entity with 5 fields and 2 actions, you get:

| Category | pgTAP Tests | pytest Tests | Total |
|----------|-------------|--------------|-------|
| Structure | 10-15 tests | - | 10-15 |
| CRUD | 12-18 tests | 8-12 tests | 20-30 |
| Actions | 8-12 tests | 4-6 tests | 12-18 |
| Edge Cases | 5-8 tests | 3-5 tests | 8-13 |
| **Total** | **35-53** | **15-23** | **50-76** |

**Coverage**: Structure (100%), CRUD (95%), Actions (90%), Edge Cases (80%)
```

#### Section 4: CLI Options & Examples (1 hour)

```markdown
## CLI Options

### Basic Usage

\`\`\`bash
specql generate-tests ENTITY_FILES [OPTIONS]
\`\`\`

### Options

#### `--type` - Select Test Framework

Generate specific test types:

\`\`\`bash
# All tests (default)
specql generate-tests entities/contact.yaml --type all

# Only pgTAP tests
specql generate-tests entities/contact.yaml --type pgtap

# Only pytest tests
specql generate-tests entities/contact.yaml --type pytest
\`\`\`

**When to use**:
- `--type pgtap`: PostgreSQL-only projects, database-centric testing
- `--type pytest`: Python applications, integration testing focus
- `--type all`: Full coverage (recommended for production)

#### `--output-dir, -o` - Output Directory

Specify where to write test files:

\`\`\`bash
# Default: tests/
specql generate-tests entities/contact.yaml

# Custom directory
specql generate-tests entities/contact.yaml --output-dir tests/generated/

# Separate directories by type
specql generate-tests entities/*.yaml --type pgtap --output-dir tests/pgtap/
specql generate-tests entities/*.yaml --type pytest --output-dir tests/integration/
\`\`\`

#### `--preview` - Preview Mode

See what would be generated without writing files:

\`\`\`bash
specql generate-tests entities/contact.yaml --preview

# Output shows:
# 📋 Would generate 4 test file(s):
#    • tests/test_contact_structure.sql
#    • tests/test_contact_crud.sql
#    • tests/test_contact_actions.sql
#    • tests/test_contact_integration.py
\`\`\`

**Use cases**:
- Verify output before generation
- Check what tests would be created
- CI/CD dry runs

#### `--verbose, -v` - Detailed Output

Show detailed generation progress:

\`\`\`bash
specql generate-tests entities/*.yaml --verbose

# Output shows:
# 📄 Processing contact.yaml...
#    Entity: Contact
#    Schema: crm
#      ✓ test_contact_structure.sql
#      ✓ test_contact_crud.sql
#      ✓ test_contact_actions.sql
#      ✓ test_contact_integration.py
#    ✅ Generated 4 test file(s)
\`\`\`

#### `--overwrite` - Overwrite Existing Files

Force overwrite of existing test files:

\`\`\`bash
# Default: Skip existing files
specql generate-tests entities/contact.yaml

# Overwrite existing
specql generate-tests entities/contact.yaml --overwrite
\`\`\`

**⚠️ Warning**: This will replace any manual modifications. Use with caution.

### Common Workflows

#### Generate Tests for All Entities

\`\`\`bash
# All YAML files in directory
specql generate-tests entities/*.yaml -v

# Recursive (if using globstar)
specql generate-tests entities/**/*.yaml
\`\`\`

#### Separate pgTAP and pytest Directories

\`\`\`bash
# Create organized structure
specql generate-tests entities/*.yaml --type pgtap --output-dir tests/db/
specql generate-tests entities/*.yaml --type pytest --output-dir tests/integration/

# Result:
# tests/
# ├── db/                    (pgTAP tests)
# │   ├── test_contact_structure.sql
# │   ├── test_contact_crud.sql
# │   └── test_contact_actions.sql
# └── integration/           (pytest tests)
#     └── test_contact_integration.py
\`\`\`

#### CI/CD Pipeline Integration

\`\`\`bash
#!/bin/bash
# scripts/generate_tests.sh

set -e

echo "Generating tests for all entities..."

# Generate pgTAP tests
specql generate-tests entities/*.yaml \
    --type pgtap \
    --output-dir tests/db/ \
    --overwrite \
    --verbose

# Generate pytest tests
specql generate-tests entities/*.yaml \
    --type pytest \
    --output-dir tests/integration/ \
    --overwrite \
    --verbose

echo "✅ Test generation complete"
echo "Run tests with: make test"
\`\`\`

#### Preview Before Generation

\`\`\`bash
# Check what would be generated
specql generate-tests entities/new_entity.yaml --preview

# If looks good, generate
specql generate-tests entities/new_entity.yaml
\`\`\`
```

#### Section 5: Customization (1 hour)

```markdown
## Customizing Generated Tests

Generated tests are designed to be:
1. **Complete** - Cover all standard cases
2. **Extensible** - Easy to add custom tests
3. **Maintainable** - Clear structure and comments

### Approach 1: Extend Generated Tests

**Best Practice**: Don't modify generated files directly. Instead, extend them.

\`\`\`bash
# Generate base tests
specql generate-tests entities/contact.yaml

# Create custom test file
touch tests/test_contact_custom.sql
\`\`\`

**In `tests/test_contact_custom.sql`**:

\`\`\`sql
-- Custom Contact Tests
-- Add entity-specific business logic tests here

BEGIN;
SELECT plan(5);

-- Test: Custom business rule - VIP contacts get special treatment
SELECT ok(
    (SELECT app.create_contact(..., '{"is_vip": true}'::JSONB)).data->>'special_flag' = 'true',
    'VIP contacts should have special flag set'
);

-- Test: Custom validation - Email domain whitelist
SELECT throws_ok(
    \$\$SELECT app.create_contact(..., '{"email": "test@blocked.com"}'::JSONB)\$\$,
    'Email domain should be validated against whitelist'
);

-- Add more custom tests...

SELECT * FROM finish();
ROLLBACK;
\`\`\`

**Run all tests**:
\`\`\`bash
pg_prove tests/test_contact_*.sql
# Runs both generated and custom tests
\`\`\`

### Approach 2: Use as Templates

Copy generated tests as starting point for similar entities:

\`\`\`bash
# Generate tests for Contact
specql generate-tests entities/contact.yaml

# Copy as template for Lead (similar entity)
cp tests/test_contact_crud.sql tests/test_lead_crud.sql

# Edit test_lead_crud.sql:
# - Replace "Contact" with "Lead"
# - Replace "tb_contact" with "tb_lead"
# - Add Lead-specific tests
\`\`\`

### Approach 3: Regenerate After Entity Changes

When entity definition changes, regenerate tests:

\`\`\`bash
# Update entity definition
vim entities/contact.yaml
# Added new field: phone_number: phone

# Regenerate tests (overwrite)
specql generate-tests entities/contact.yaml --overwrite

# Review changes
git diff tests/test_contact_*.sql

# Merge with custom tests if needed
\`\`\`

### Customization Points

#### 1. Test Data

Modify sample data in generated tests:

\`\`\`sql
-- Generated (generic):
'{"email": "test@example.com"}'::JSONB

-- Customized (realistic):
'{"email": "john.doe@acmecorp.com", "first_name": "John", "last_name": "Doe"}'::JSONB
\`\`\`

#### 2. Additional Assertions

Add more specific assertions:

\`\`\`sql
-- Generated:
SELECT ok(result->>'status' = 'success', 'Should succeed');

-- Enhanced:
SELECT ok(result->>'status' = 'success', 'Should succeed');
SELECT ok(result->'data'->>'email' LIKE '%@%', 'Email should be valid');
SELECT ok(result->'data'->>'status' = 'lead', 'New contacts should be leads');
\`\`\`

#### 3. Custom Scenarios

Add business-specific test scenarios:

\`\`\`python
# In test_contact_integration.py, add:

def test_bulk_contact_import(self, clean_db):
    """Test importing multiple contacts from CSV"""
    # Your custom test logic
    pass

def test_contact_deduplication(self, clean_db):
    """Test duplicate contact detection and merging"""
    # Your custom test logic
    pass
\`\`\`

### Regeneration Strategy

**Recommended workflow**:

1. **Generated files**: Keep pristine, regenerate as needed
2. **Custom files**: `test_{entity}_custom.sql`, `test_{entity}_custom.py`
3. **Version control**: Commit generated files to track changes

\`\`\`gitignore
# .gitignore
# Option 1: Track generated tests (recommended)
# tests/test_*_structure.sql
# tests/test_*_crud.sql
# tests/test_*_actions.sql
# tests/test_*_integration.py

# Option 2: Ignore generated, regenerate in CI
# tests/test_*.sql
# tests/test_*.py
# !tests/test_*_custom.*
\`\`\`
```

#### Section 6: CI/CD Integration (1 hour)

Include examples for:
- GitHub Actions workflow
- GitLab CI configuration
- Make targets
- Docker integration
- Test reporting

#### Section 7: Troubleshooting (30 min)

Common issues and solutions:
- Generated tests fail
- Wrong schema/table names
- Missing pgTAP extension
- Database connection issues
- Python import errors

### Success Criteria

- [ ] Complete guide with all 9 sections
- [ ] 2000+ words
- [ ] All code examples tested and working
- [ ] Clear structure with table of contents
- [ ] Links to related documentation
- [ ] No typos or formatting errors

### Deliverables

1. `docs/02_guides/TEST_GENERATION.md` (~2500 words)
2. All code examples validated
3. Screenshots/diagrams if applicable

---

## Phase 2.2: Test Reverse Engineering Guide

**Time Estimate**: 3-4 hours
**Priority**: HIGH

### Objective

Create guide at `docs/02_guides/TEST_REVERSE_ENGINEERING.md` (1500+ words) explaining how to reverse engineer existing tests.

### Content Outline

```markdown
# Test Reverse Engineering Guide

## Overview
- What is test reverse engineering?
- Use cases: Coverage analysis, framework migration, documentation

## Quick Start
- Parse pgTAP test file
- Parse pytest test file
- Output formats (YAML, JSON)

## Supported Test Frameworks
- pgTAP (PostgreSQL unit tests)
- pytest (Python tests)
- Future: Jest, JUnit, RSpec

## TestSpec Format
- Universal test specification
- Why language-agnostic format matters
- TestSpec YAML structure

## Coverage Analysis
- Analyzing what's tested
- Finding gaps in test coverage
- Suggesting missing test scenarios

## Use Cases

### 1. Coverage Analysis
\`\`\`bash
specql reverse-tests tests/*.sql --analyze-coverage --preview
\`\`\`

### 2. Framework Migration
Convert pgTAP → pytest or vice versa (future feature)

### 3. Test Documentation
Generate test documentation from code

### 4. Gap Detection
Find untested business logic

## Examples
- Real-world pgTAP file
- Real-world pytest file
- Coverage analysis output

## Advanced Usage
- Multiple test files
- Custom entity mapping
- Batch processing

## Troubleshooting
- Parser errors
- Unsupported test patterns
- Entity detection issues
```

### Deliverables

1. `docs/02_guides/TEST_REVERSE_ENGINEERING.md` (~1500 words)

---

## Phase 2.3: Working Examples

**Time Estimate**: 3-4 hours
**Priority**: HIGH

### Objective

Create real, working examples that users can copy and run.

### Task 2.3.1: Generate Example Tests (1 hour)

```bash
# Generate tests for Contact entity
cd docs/06_examples/simple_contact/

# Create generated_tests directory
mkdir -p generated_tests

# Generate all tests
uv run specql generate-tests contact.yaml --output-dir generated_tests/ -v

# Verify outputs
ls -la generated_tests/
```

### Task 2.3.2: Create Example README (1 hour)

Create `docs/06_examples/simple_contact/generated_tests/README.md`:

```markdown
# Generated Test Examples

This directory contains real, working tests generated from [contact.yaml](../contact.yaml).

## Files

- `test_contact_structure.sql` - pgTAP structure tests (50 lines, 10 tests)
- `test_contact_crud.sql` - pgTAP CRUD tests (100 lines, 15 tests)
- `test_contact_actions.sql` - pgTAP action tests (80 lines, 12 tests)
- `test_contact_integration.py` - pytest integration tests (150 lines, 18 tests)

**Total**: 55 tests across 380 lines of code

## Running These Tests

[Include specific instructions]

## What Gets Tested

[Detailed breakdown of each test file]
```

### Task 2.3.3: Create TestSpec Example (1 hour)

Create example TestSpec YAML showing reverse engineering output:

`docs/06_examples/simple_contact/test_spec_example.yaml`:

```yaml
entity_name: Contact
test_framework: pgtap
source_language: pgtap

scenarios:
  - name: table_exists
    category: structure
    description: Verify Contact table exists in database
    assertions:
      - type: has_table
        target: crm.tb_contact
        expected: true
        message: Contact table should exist

  - name: create_contact_success
    category: crud_create
    description: Successfully create a new contact
    setup:
      - Insert test tenant and user
    steps:
      - Execute app.create_contact function
    assertions:
      - type: equals
        target: result.status
        expected: success
        message: Contact creation should return success
      - type: is_not_null
        target: result.object_data.id
        message: Created contact should have UUID

# ... more scenarios
```

### Task 2.3.4: Add Coverage Analysis Example (30 min)

Show example output of coverage analysis:

`docs/06_examples/simple_contact/coverage_analysis_example.md`:

```markdown
# Coverage Analysis Example

## Command

\`\`\`bash
specql reverse-tests generated_tests/test_contact_*.sql --analyze-coverage --preview
\`\`\`

## Output

\`\`\`
📊 Coverage Analysis for Contact Entity

✅ Well Covered:
  • Table structure (100%)
  • Basic CRUD operations (95%)
  • Primary key constraints (100%)
  • qualify_lead action happy path (100%)

⚠️ Partially Covered:
  • Error handling (60%)
    - Missing: Invalid email format test
    - Missing: Null email test
  • State transitions (70%)
    - Missing: Reverse transition tests

❌ Not Covered:
  • Concurrent updates
  • Bulk operations
  • Permission edge cases

📝 Suggested Tests:
  1. test_create_contact_invalid_email
  2. test_create_contact_null_email
  3. test_qualify_already_qualified_contact
  4. test_concurrent_contact_updates
  5. test_bulk_contact_creation

Coverage Score: 78% (43/55 potential scenarios)
\`\`\`
```

### Deliverables

1. Generated test files in `docs/06_examples/simple_contact/generated_tests/`
2. README explaining examples
3. TestSpec YAML example
4. Coverage analysis example

---

## Phase 2.4: Demo Creation & Polish

**Time Estimate**: 2-3 hours
**Priority**: MEDIUM

### Task 2.4.1: Record Demo Videos/GIFs (1.5 hours)

Record demonstrations:

1. **Basic Test Generation** (30 sec)
   - Show entity YAML
   - Run generate-tests command
   - Show generated files

2. **Test Execution** (45 sec)
   - Run pgTAP tests with pg_prove
   - Run pytest tests
   - Show all passing

3. **Coverage Analysis** (30 sec)
   - Run reverse-tests with --analyze-coverage
   - Show coverage report
   - Highlight gaps

```bash
# Record with asciinema
asciinema rec docs/demos/test_generation_demo.cast -c "bash docs/demos/test_generation_script.sh"
asciinema rec docs/demos/test_execution_demo.cast -c "bash docs/demos/test_execution_script.sh"
asciinema rec docs/demos/coverage_analysis_demo.cast -c "bash docs/demos/coverage_script.sh"

# Convert to GIFs
for cast in docs/demos/*.cast; do
    asciicast2gif -s 2 "$cast" "${cast%.cast}.gif"
done
```

### Task 2.4.2: Update Documentation Index (30 min)

Update `docs/README.md` to include new guides:

```markdown
## Guides

### Testing
- [Test Generation Guide](02_guides/TEST_GENERATION.md) - Generate comprehensive test suites
- [Test Reverse Engineering](02_guides/TEST_REVERSE_ENGINEERING.md) - Analyze existing tests
- [CI/CD Integration](02_guides/CI_CD_INTEGRATION.md) - Automate testing in pipelines

### Core Features
- [Entity Definition](02_guides/ENTITY_DEFINITION.md)
- ...
```

### Task 2.4.3: Create Quick Reference Card (30 min)

Create `docs/quick_reference/TEST_GENERATION.md`:

```markdown
# Test Generation - Quick Reference

## Generate Tests

\`\`\`bash
# All tests
specql generate-tests entities/contact.yaml

# pgTAP only
specql generate-tests entities/*.yaml --type pgtap -o tests/db/

# pytest only
specql generate-tests entities/*.yaml --type pytest -o tests/integration/

# Preview
specql generate-tests entities/contact.yaml --preview
\`\`\`

## Reverse Engineer Tests

\`\`\`bash
# Parse pgTAP
specql reverse-tests tests/test_contact.sql --preview

# Coverage analysis
specql reverse-tests tests/*.sql --analyze-coverage

# Convert to YAML
specql reverse-tests tests/*.py --entity=Contact --output-dir=specs/ --format=yaml
\`\`\`

## Run Tests

\`\`\`bash
# pgTAP
pg_prove -d dbname tests/test_*.sql

# pytest
pytest tests/test_*_integration.py -v
\`\`\`

## What Gets Generated

| Entity Elements | pgTAP Tests | pytest Tests | Total |
|----------------|-------------|--------------|-------|
| 5 fields | 10-15 | - | 10-15 |
| Basic CRUD | 12-18 | 8-12 | 20-30 |
| 2 actions | 8-12 | 4-6 | 12-18 |
| Edge cases | 5-8 | 3-5 | 8-13 |
| **Total** | **35-53** | **15-23** | **50-76** |

## Common Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--type` | Test framework | `--type pgtap` |
| `--output-dir` | Output location | `-o tests/` |
| `--preview` | Dry run | `--preview` |
| `--verbose` | Detailed output | `-v` |
| `--overwrite` | Replace existing | `--overwrite` |

## Links

- [Full Guide](../02_guides/TEST_GENERATION.md)
- [Examples](../06_examples/simple_contact/generated_tests/)
- [Troubleshooting](../02_guides/TEST_GENERATION.md#troubleshooting)
```

### Deliverables

1. Demo GIFs in `docs/demos/`
2. Updated documentation index
3. Quick reference card

---

## Week 2 Completion Checklist

### Documentation
- [ ] TEST_GENERATION.md complete (2000+ words)
- [ ] TEST_REVERSE_ENGINEERING.md complete (1500+ words)
- [ ] All code examples tested and working
- [ ] Examples in docs/06_examples/ created
- [ ] TestSpec YAML examples created
- [ ] Coverage analysis examples created
- [ ] Documentation index updated
- [ ] Quick reference created

### Demos
- [ ] Test generation demo GIF created
- [ ] Test execution demo GIF created
- [ ] Coverage analysis demo GIF created
- [ ] Demos embedded in documentation

### Quality
- [ ] All links work
- [ ] No typos or formatting errors
- [ ] Code examples are copy-paste ready
- [ ] Screenshots/diagrams are clear
- [ ] TOC and navigation work

### Git
- [ ] All documentation committed
- [ ] Commit message follows template
- [ ] No uncommitted changes

---

## Week 2 Git Commit

```bash
git add -A
git commit -m "docs: comprehensive test generation documentation

Week 2 Complete: User-facing documentation and examples

Phase 2.1: Test Generation Guide
- Complete guide: docs/02_guides/TEST_GENERATION.md (2500 words)
- Sections: Overview, Quick Start, Understanding Tests, CLI Options,
  Customization, CI/CD Integration, Troubleshooting
- All code examples tested and validated
- Screenshots and diagrams included

Phase 2.2: Test Reverse Engineering Guide
- Complete guide: docs/02_guides/TEST_REVERSE_ENGINEERING.md (1500 words)
- Coverage analysis explanation
- TestSpec format documentation
- Use cases and examples

Phase 2.3: Working Examples
- Generated tests: docs/06_examples/simple_contact/generated_tests/
- 4 test files (380 lines, 55 tests)
- Example README with usage instructions
- TestSpec YAML example
- Coverage analysis example output

Phase 2.4: Demos & Polish
- Test generation demo GIF
- Test execution demo GIF
- Coverage analysis demo GIF
- Updated documentation index
- Quick reference card created

Documentation Statistics:
- New guides: 4000+ words
- Examples: 380+ lines of generated tests
- Demo GIFs: 3
- Quick reference: 1 page
- Total pages: 8

Users can now:
- Understand test generation completely
- Generate tests confidently
- Customize generated tests
- Integrate with CI/CD
- Analyze test coverage
- Find answers quickly

Related: docs/implementation_plans/v0.5.0_beta/WEEK_02_DOCUMENTATION.md
Next: Week 3 - Testing & Marketing
"
```

---

## Next Steps

After completing Week 2:

1. **Review documentation** with users/team
2. **Test examples** in real projects
3. **Move to Week 3**: [WEEK_03_TESTING_MARKETING.md](WEEK_03_TESTING_MARKETING.md)
   - Expand test coverage
   - Create marketing content
   - Prepare release

**Week 2 Goal Achieved**: ✅ Comprehensive documentation enables users to master test generation!
