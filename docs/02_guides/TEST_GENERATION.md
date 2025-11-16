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

## Quick Start

### Step 1: Define Your Entity

Create `entities/contact.yaml`:

```yaml
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
```

### Step 2: Generate Tests

```bash
# Generate both pgTAP and pytest tests
specql generate-tests entities/contact.yaml

# Output shows:
# ✅ Generated 4 test file(s)
#    - tests/test_contact_structure.sql
#    - tests/test_contact_crud.sql
#    - tests/test_contact_actions.sql
#    - tests/test_contact_integration.py
```

### Step 3: Review Generated Tests

```bash
ls -la tests/
# test_contact_structure.sql     (50 lines, 10 tests)
# test_contact_crud.sql          (100 lines, 15 tests)
# test_contact_actions.sql       (80 lines, 12 tests)
# test_contact_integration.py    (150 lines, 18 tests)
# Total: 55 tests across 380 lines
```

### Step 4: Run the Tests

**pgTAP tests**:
```bash
# Install pgTAP extension (once)
psql -d your_db -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

# Run tests
pg_prove -d your_db tests/test_contact_*.sql

# Output:
# tests/test_contact_structure.sql .. ok
# tests/test_contact_crud.sql ........ ok
# tests/test_contact_actions.sql ..... ok
# All tests successful.
```

**pytest tests**:
```bash
# Install dependencies
pip install pytest psycopg[binary]

# Run tests
pytest tests/test_contact_integration.py -v

# Output:
# test_contact_integration.py::TestContactIntegration::test_create_contact_happy_path PASSED
# test_contact_integration.py::TestContactIntegration::test_create_duplicate_fails PASSED
# ... 16 more passed
# ==================== 18 passed in 2.31s ====================
```

🎉 **Success!** You've generated and run 55 tests in under 5 minutes.

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
```sql
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
```

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
```sql
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
    $$SELECT app.create_contact(...same email...)$$,
    'Duplicate email should be rejected'
);
```

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
```sql
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
```

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
```python
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
```

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

## CLI Options

### Basic Usage

```bash
specql generate-tests ENTITY_FILES [OPTIONS]
```

### Options

#### `--type` - Select Test Framework

Generate specific test types:

```bash
# All tests (default)
specql generate-tests entities/contact.yaml --type all

# Only pgTAP tests
specql generate-tests entities/contact.yaml --type pgtap

# Only pytest tests
specql generate-tests entities/contact.yaml --type pytest
```

**When to use**:
- `--type pgtap`: PostgreSQL-only projects, database-centric testing
- `--type pytest`: Python applications, integration testing focus
- `--type all`: Full coverage (recommended for production)

#### `--output-dir, -o` - Output Directory

Specify where to write test files:

```bash
# Default: tests/
specql generate-tests entities/contact.yaml

# Custom directory
specql generate-tests entities/contact.yaml --output-dir tests/generated/

# Separate directories by type
specql generate-tests entities/*.yaml --type pgtap --output-dir tests/db/
specql generate-tests entities/*.yaml --type pytest --output-dir tests/integration/
```

#### `--preview` - Preview Mode

See what would be generated without writing files:

```bash
specql generate-tests entities/contact.yaml --preview

# Output shows:
# 📋 Would generate 4 test file(s):
#    • tests/test_contact_structure.sql
#    • tests/test_contact_crud.sql
#    • tests/test_contact_actions.sql
#    • tests/test_contact_integration.py
```

**Use cases**:
- Verify output before generation
- Check what tests would be created
- CI/CD dry runs

#### `--verbose, -v` - Detailed Output

Show detailed generation progress:

```bash
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
```

#### `--overwrite` - Overwrite Existing Files

Force overwrite of existing test files:

```bash
# Default: Skip existing files
specql generate-tests entities/contact.yaml

# Overwrite existing
specql generate-tests entities/contact.yaml --overwrite
```

**⚠️ Warning**: This will replace any manual modifications. Use with caution.

### Common Workflows

#### Generate Tests for All Entities

```bash
# All YAML files in directory
specql generate-tests entities/*.yaml -v

# Recursive (if using globstar)
specql generate-tests entities/**/*.yaml
```

#### Separate pgTAP and pytest Directories

```bash
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
```

#### CI/CD Pipeline Integration

```bash
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
```

#### Preview Before Generation

```bash
# Check what would be generated
specql generate-tests entities/new_entity.yaml --preview

# If looks good, generate
specql generate-tests entities/new_entity.yaml
```

## Customizing Generated Tests

Generated tests are designed to be:
1. **Complete** - Cover all standard cases
2. **Extensible** - Easy to add custom tests
3. **Maintainable** - Clear structure and comments

### Approach 1: Extend Generated Tests

**Best Practice**: Don't modify generated files directly. Instead, extend them.

```bash
# Generate base tests
specql generate-tests entities/contact.yaml

# Create custom test file
touch tests/test_contact_custom.sql
```

**In `tests/test_contact_custom.sql`**:

```sql
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
    $$SELECT app.create_contact(..., '{"email": "test@blocked.com"}'::JSONB)$$,
    'Email domain should be validated against whitelist'
);

-- Add more custom tests...

SELECT * FROM finish();
ROLLBACK;
```

**Run all tests**:
```bash
pg_prove tests/test_contact_*.sql
# Runs both generated and custom tests
```

### Approach 2: Use as Templates

Copy generated tests as starting point for similar entities:

```bash
# Generate tests for Contact
specql generate-tests entities/contact.yaml

# Copy as template for Lead (similar entity)
cp tests/test_contact_crud.sql tests/test_lead_crud.sql

# Edit test_lead_crud.sql:
# - Replace "Contact" with "Lead"
# - Replace "tb_contact" with "tb_lead"
# - Add Lead-specific tests
```

### Approach 3: Regenerate After Entity Changes

When entity definition changes, regenerate tests:

```bash
# Update entity definition
vim entities/contact.yaml
# Added new field: phone_number: phone

# Regenerate tests (overwrite)
specql generate-tests entities/contact.yaml --overwrite

# Review changes
git diff tests/test_contact_*.sql

# Merge with custom tests if needed
```

### Customization Points

#### 1. Test Data

Modify sample data in generated tests:

```sql
-- Generated (generic):
'{"email": "test@example.com"}'::JSONB

-- Customized (realistic):
'{"email": "john.doe@acmecorp.com", "first_name": "John", "last_name": "Doe"}'::JSONB
```

#### 2. Additional Assertions

Add more specific assertions:

```sql
-- Generated:
SELECT ok(result->>'status' = 'success', 'Should succeed');

-- Enhanced:
SELECT ok(result->>'status' = 'success', 'Should succeed');
SELECT ok(result->'data'->>'email' LIKE '%@%', 'Email should be valid');
SELECT ok(result->'data'->>'status' = 'lead', 'New contacts should be leads');
```

#### 3. Custom Scenarios

Add business-specific test scenarios:

```python
# In test_contact_integration.py, add:

def test_bulk_contact_import(self, clean_db):
    """Test importing multiple contacts from CSV"""
    # Your custom test logic
    pass

def test_contact_deduplication(self, clean_db):
    """Test duplicate contact detection and merging"""
    # Your custom test logic
    pass
```

### Regeneration Strategy

**Recommended workflow**:

1. **Generated files**: Keep pristine, regenerate as needed
2. **Custom files**: `test_{entity}_custom.sql`, `test_{entity}_custom.py`
3. **Version control**: Commit generated files to track changes

```gitignore
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
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install specql-generator pytest psycopg[binary]

    - name: Generate tests
      run: |
        specql generate-tests entities/*.yaml --overwrite --verbose

    - name: Install pgTAP
      run: |
        psql -h localhost -U postgres -d postgres -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

    - name: Run pgTAP tests
      run: |
        pg_prove -h localhost -U postgres -d postgres tests/test_*_structure.sql tests/test_*_crud.sql tests/test_*_actions.sql

    - name: Run pytest tests
      run: |
        pytest tests/test_*_integration.py -v
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test

test:
  stage: test
  image: python:3.11

  services:
    - postgres:15

  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres

  before_script:
    - pip install specql-generator pytest psycopg[binary]
    - psql -h postgres -U postgres -d test_db -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

  script:
    - specql generate-tests entities/*.yaml --overwrite --verbose
    - pg_prove -h postgres -U postgres -d test_db tests/test_*.sql
    - pytest tests/test_*_integration.py -v
```

### Make Targets

Add to `Makefile`:

```makefile
.PHONY: test test-generate test-run test-clean

# Generate all tests
test-generate:
	specql generate-tests entities/*.yaml --overwrite --verbose

# Run all tests
test-run:
	pg_prove -d $(DATABASE_URL) tests/test_*.sql
	pytest tests/test_*_integration.py -v

# Generate and run tests
test: test-generate test-run

# Clean generated tests
test-clean:
	rm -f tests/test_*.sql tests/test_*_integration.py
```

### Docker Integration

Create `Dockerfile.test`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source
COPY . /app
WORKDIR /app

# Generate tests
RUN specql generate-tests entities/*.yaml --overwrite

# Default command: run tests
CMD ["make", "test-run"]
```

## Troubleshooting

### Generated tests fail

**Problem**: Tests fail immediately after generation

**Solutions**:
1. **Check database connection**: Ensure PostgreSQL is running and accessible
2. **Verify pgTAP extension**: `psql -d your_db -c "SELECT * FROM pg_extension WHERE extname = 'pgtap';"`
3. **Check entity definition**: Validate YAML syntax with `specql validate entities/contact.yaml`
4. **Review schema**: Ensure database schema matches entity definition

**Debug command**:
```bash
# Test database connectivity
psql -d your_db -c "SELECT version();"

# Test pgTAP installation
psql -d your_db -c "SELECT has_table('public', 'pgtap', 'pgTAP should be installed');"
```

### Wrong schema/table names

**Problem**: Tests reference incorrect table names

**Common causes**:
- Entity schema doesn't match database schema
- Table naming convention mismatch
- Migration not applied

**Solutions**:
```bash
# Check entity schema
grep "schema:" entities/contact.yaml

# Check actual database schema
psql -d your_db -c "\dt crm.*"

# Regenerate with correct schema
specql generate-tests entities/contact.yaml --overwrite
```

### Missing pgTAP extension

**Problem**: `pgTAP extension not found` error

**Solution**:
```bash
# Install pgTAP extension
psql -d your_db -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

# Verify installation
psql -d your_db -c "SELECT pgtap_version();"
```

### Database connection issues

**Problem**: `connection refused` or authentication errors

**Solutions**:
```bash
# Test connection
psql -h localhost -p 5432 -U your_user -d your_db -c "SELECT 1;"

# Check environment variables
echo $DATABASE_URL

# Use explicit connection parameters
pg_prove -h localhost -p 5432 -U your_user -d your_db tests/test_*.sql
```

### Python import errors

**Problem**: pytest fails with import errors

**Common causes**:
- Missing dependencies
- Incorrect Python path
- Database connection issues in fixtures

**Solutions**:
```bash
# Install all dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Test database connection in Python
python -c "import psycopg; conn = psycopg.connect('postgresql://user:pass@localhost/db'); print('Connected')"
```

### Tests are too slow

**Problem**: Test suite takes too long to run

**Solutions**:
1. **Use in-memory database** for development
2. **Parallel execution**: `pytest -n auto tests/`
3. **Selective testing**: Run only specific test files
4. **Database optimization**: Add indexes, use SSD storage

**Performance tips**:
```bash
# Run only structure tests (fastest)
pg_prove tests/test_*_structure.sql

# Run CRUD tests only
pg_prove tests/test_*_crud.sql

# Skip integration tests for quick feedback
pg_prove tests/test_*_structure.sql tests/test_*_crud.sql tests/test_*_actions.sql
```

### Entity changes not reflected

**Problem**: Modified entity definition doesn't update tests

**Solution**:
```bash
# Force regeneration
specql generate-tests entities/contact.yaml --overwrite --verbose

# Check what changed
git diff tests/test_contact_*.sql
```

### Custom tests overwritten

**Problem**: Custom modifications lost during regeneration

**Solutions**:
1. **Use custom files**: `test_contact_custom.sql`
2. **Don't overwrite**: Remove `--overwrite` flag
3. **Version control**: Commit custom changes separately
4. **Backup first**: `cp tests/test_contact_custom.sql tests/test_contact_custom.sql.backup`

### Large entities generate too many tests

**Problem**: Entity with many fields/actions generates overwhelming test files

**Solutions**:
1. **Split generation**: Generate by type
   ```bash
   specql generate-tests entities/large_entity.yaml --type pgtap
   specql generate-tests entities/large_entity.yaml --type pytest
   ```
2. **Separate directories**: Keep tests organized
3. **Selective regeneration**: Regenerate only when needed
4. **Custom filtering**: Focus on critical paths first

---

## Related Documentation

- [Entity Definition Guide](ENTITY_DEFINITION.md) - How to define entities
- [CLI Commands](CLI_COMMANDS.md) - Complete command reference
- [CI/CD Integration](CI_CD_INTEGRATION.md) - Advanced pipeline setup
- [Test Reverse Engineering](TEST_REVERSE_ENGINEERING.md) - Analyze existing tests

## Examples

See `docs/06_examples/simple_contact/` for complete working examples including:
- Entity definition
- Generated test files
- Test execution scripts
- Coverage analysis examples

---

*Last updated: 2025-11-20 | Version: v0.5.0-beta*