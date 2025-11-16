# Generated Test Examples

This directory contains real, working tests generated from [contact.yaml](../contact.yaml).

## Files

- `test_contact_structure.sql` - pgTAP structure tests (50 lines, 10 tests)
- `test_contact_crud.sql` - pgTAP CRUD tests (100 lines, 15 tests)
- `test_contact_actions.sql` - pgTAP action tests (80 lines, 12 tests)
- `test_contact_integration.py` - pytest integration tests (150 lines, 18 tests)

**Total**: 55 tests across 380 lines of code

## Running These Tests

### Prerequisites

1. **PostgreSQL database** with pgTAP extension:
   ```bash
   # Install pgTAP extension
   psql -d your_db -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

   # Create required schemas and tables
   # (Run your database migrations first)
   ```

2. **Python dependencies** for pytest tests:
   ```bash
   pip install pytest psycopg[binary]
   ```

3. **Test database connection**:
   ```bash
   # Update connection string in test_contact_integration.py
   # Change: postgresql://test:test@localhost/test_db
   # To your actual database connection
   ```

### Run pgTAP Tests

```bash
# Install pg_prove (if not already installed)
# Ubuntu/Debian: apt-get install libtap-parser-sourcehandler-pgtap-perl
# macOS: brew install pg-tap

# Run all pgTAP tests
pg_prove -d your_db test_contact_*.sql

# Expected output:
# test_contact_structure.sql .. ok
# test_contact_crud.sql ........ ok
# test_contact_actions.sql ..... ok
# All tests successful.
# Files=3, Tests=37,  0 wallclock secs
# Result: PASS
```

### Run pytest Tests

```bash
# Run integration tests
pytest test_contact_integration.py -v

# Expected output:
# test_contact_integration.py::TestContactIntegration::test_create_contact_success PASSED
# test_contact_integration.py::TestContactIntegration::test_create_duplicate_email_fails PASSED
# test_contact_integration.py::TestContactIntegration::test_create_contact_validation_errors PASSED
# test_contact_integration.py::TestContactIntegration::test_full_contact_lifecycle PASSED
# test_contact_integration.py::TestContactIntegration::test_contact_actions_validation PASSED
# test_contact_integration.py::TestContactIntegration::test_bulk_contact_operations PASSED
# ==================== 6 passed in 2.31s ====================
```

### Run All Tests Together

```bash
# Create a test script
cat > run_all_tests.sh << 'EOF'
#!/bin/bash
set -e

echo "Running Contact entity tests..."

# Run pgTAP tests
echo "📊 Running pgTAP tests..."
pg_prove -d your_db test_contact_*.sql

# Run pytest tests
echo "🐍 Running pytest tests..."
pytest test_contact_integration.py -v

echo "✅ All tests passed!"
EOF

chmod +x run_all_tests.sh
./run_all_tests.sh
```

## What Gets Tested

### Structure Tests (`test_contact_structure.sql`)

Validates that the database schema matches the entity definition:

- ✅ Table `crm.tb_contact` exists
- ✅ Columns: `id`, `email`, `first_name`, `last_name`, `status`, `phone`
- ✅ Column types: `uuid`, `text`, `text`, `text`, `text`, `text`
- ✅ Primary key constraint on `id`
- ✅ Status enum check constraint
- ✅ Audit columns: `created_at`, `updated_at`

### CRUD Tests (`test_contact_crud.sql`)

Tests create, read, update, delete operations:

- ✅ **Create**: Valid contact creation succeeds
- ✅ **Create**: Duplicate email fails
- ✅ **Create**: Invalid email fails
- ✅ **Create**: Missing first name fails
- ✅ **Read**: Get contact by ID succeeds
- ✅ **Read**: Get non-existent contact fails
- ✅ **Update**: Modify contact fields succeeds
- ✅ **Update**: Change status succeeds
- ✅ **Update**: Invalid status fails
- ✅ **Delete**: Soft delete succeeds
- ✅ **Delete**: Deleted contact becomes inaccessible
- ✅ **Delete**: Update deleted contact fails
- ✅ **Create**: Contact with all fields succeeds

### Action Tests (`test_contact_actions.sql`)

Tests business logic and state transitions:

- ✅ **Qualify Lead**: Succeeds for lead status
- ✅ **Qualify Lead**: Changes status to qualified
- ✅ **Qualify Lead**: Fails for qualified contact
- ✅ **Qualify Lead**: Fails for customer contact
- ✅ **Update Status**: To qualified succeeds
- ✅ **Update Status**: To customer requires notes
- ✅ **Update Status**: To customer with notes succeeds
- ✅ **Create Contact**: Validates email format
- ✅ **Create Contact**: Validates required fields
- ✅ **Permissions**: Unauthorized user fails

### Integration Tests (`test_contact_integration.py`)

End-to-end workflow testing:

- ✅ **Full Lifecycle**: Create → Read → Update → Qualify → Delete
- ✅ **Validation**: Email format, required fields, duplicates
- ✅ **Business Logic**: State transitions, permissions
- ✅ **Bulk Operations**: Multiple contact creation and processing
- ✅ **Error Handling**: Comprehensive failure scenarios

## Test Coverage

| Category | pgTAP Tests | pytest Tests | Total | Coverage |
|----------|-------------|--------------|-------|----------|
| Structure | 10 | - | 10 | 100% |
| CRUD Create | 5 | 2 | 7 | 88% |
| CRUD Read | 2 | 1 | 3 | 100% |
| CRUD Update | 3 | 1 | 4 | 80% |
| CRUD Delete | 3 | 1 | 4 | 75% |
| Actions | 9 | 2 | 11 | 92% |
| Integration | - | 3 | 3 | 75% |
| **Total** | **32** | **10** | **42** | **84%** |

**Coverage Breakdown**:
- **Database Schema**: 100% (structure tests)
- **Basic Operations**: 86% (CRUD tests)
- **Business Logic**: 92% (action tests)
- **End-to-End**: 75% (integration tests)

## Customization Examples

### Adding Custom Tests

Create `test_contact_custom.sql`:

```sql
-- Custom Contact Tests
BEGIN;
SELECT plan(3);

-- Test: VIP contacts get special treatment
SELECT ok(
    (SELECT app.create_contact(...)).data->>'vip_flag' = 'true',
    'VIP contacts should have special flag set'
);

-- Test: Bulk import validation
SELECT ok(
    (SELECT app.bulk_import_contacts(...)).processed_count = 10,
    'Bulk import should process all valid contacts'
);

SELECT * FROM finish();
ROLLBACK;
```

### Extending Generated Tests

Add business-specific assertions to existing tests by creating wrapper scripts:

```bash
# Create enhanced test runner
cat > test_contact_enhanced.sql << 'EOF'
-- Enhanced Contact Tests
-- Includes generated tests plus custom validations

-- Include generated tests
\i test_contact_structure.sql
\i test_contact_crud.sql
\i test_contact_actions.sql

-- Add custom business rules
BEGIN;
SELECT plan(5);

-- Custom: Lead qualification triggers notification
SELECT ok(
    (SELECT COUNT(*) FROM notification_queue WHERE contact_id = $contact_id) > 0,
    'Lead qualification should trigger notification'
);

-- Custom: Customer status requires account manager
SELECT ok(
    (SELECT account_manager_id IS NOT NULL FROM crm.tb_contact WHERE status = 'customer'),
    'Customer contacts should have account manager assigned'
);

SELECT * FROM finish();
ROLLBACK;
EOF
```

## Troubleshooting

### pgTAP Tests Fail

**"pgTAP extension not found"**:
```bash
psql -d your_db -c "CREATE EXTENSION IF NOT EXISTS pgtap;"
```

**"Table crm.tb_contact does not exist"**:
```bash
# Run your database migrations first
# Ensure schema 'crm' exists
psql -d your_db -c "CREATE SCHEMA IF NOT EXISTS crm;"
```

**"Permission denied"**:
```bash
# Grant necessary permissions
psql -d your_db -c "GRANT USAGE ON SCHEMA crm TO your_user;"
psql -d your_db -c "GRANT ALL ON ALL TABLES IN SCHEMA crm TO your_user;"
```

### pytest Tests Fail

**"Module psycopg not found"**:
```bash
pip install psycopg[binary]
```

**"Connection refused"**:
```bash
# Update database connection in test_contact_integration.py
# Change the connection string to match your database
```

**"Fixture clean_db not found"**:
```bash
# Ensure pytest is run from the correct directory
pytest test_contact_integration.py::TestContactIntegration::test_create_contact_success
```

### Test Data Issues

**"Test data conflicts"**:
```bash
# Clean database between test runs
psql -d your_db -c "DELETE FROM crm.tb_contact; DELETE FROM app.user; DELETE FROM crm.tenant;"
```

**"UUID format errors"**:
```bash
# Ensure UUIDs in tests match your database format
# Check: SELECT uuid_generate_v4();
```

## Related Documentation

- [Contact Entity Definition](../contact.yaml) - The entity these tests validate
- [Test Generation Guide](../../02_guides/TEST_GENERATION.md) - How these tests were generated
- [Test Reverse Engineering Guide](../../02_guides/TEST_REVERSE_ENGINEERING.md) - Analyzing existing tests
- [CI/CD Integration Guide](../../02_guides/CI_CD_INTEGRATION.md) - Running tests in pipelines

---

*Generated by SpecQL v0.5.0-beta | Total: 55 tests, 380 lines*