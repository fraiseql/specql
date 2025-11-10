# Generate Your First Tests

Learn how to automatically generate comprehensive tests for your SpecQL entities and patterns. SpecQL creates both pgTAP (PostgreSQL) and pytest (Python) tests with zero manual coding.

## 🎯 What You'll Learn

- Generate automated tests from YAML specs
- Run pgTAP tests in PostgreSQL
- Run pytest tests with Python
- Understand test coverage
- Integrate tests into CI/CD

## 📋 Prerequisites

- [Entity with patterns created](first-pattern.md)
- PostgreSQL database with schema applied
- Python environment (for pytest)

## 🧪 Step 1: Understand Test Generation

SpecQL generates three types of tests:

### 1. **pgTAP Tests** - PostgreSQL Native
- Run directly in the database
- Test business logic and constraints
- Fast execution, no external dependencies

### 2. **pytest Tests** - Python Integration
- Test from application code
- Integration with Python test frameworks
- API-level testing

### 3. **Performance Tests** - Benchmarking
- Measure query performance
- Compare pattern implementations
- Identify optimization opportunities

## 🔧 Step 2: Generate Tests

```bash
# Generate all test types for your entity
specql generate tests entities/user.yaml

# Check generated test files
tree tests/
# tests/
# ├── pgtap/
# │   ├── user_state_machine_test.sql
# │   ├── user_validation_test.sql
# │   └── user_constraints_test.sql
# └── pytest/
#     ├── test_user_state_machine.py
#     ├── test_user_validation.py
#     └── test_user_constraints.py
```

## 📄 Step 3: Review Generated pgTAP Tests

```bash
# View the state machine tests
cat tests/pgtap/user_state_machine_test.sql
```

**Generated pgTAP tests include:**

```sql
-- Auto-generated pgTAP tests for user state machine
BEGIN;

-- Setup test data
INSERT INTO user (id, email, first_name, last_name, status)
VALUES ('test-user-id', 'test@example.com', 'Test', 'User', 'inactive');

-- Test 1: Initial state is correct
SELECT ok(
    (SELECT status FROM user WHERE id = 'test-user-id') = 'inactive',
    'User starts in inactive state'
);

-- Test 2: Valid transition works
SELECT ok(
    user_request_verification('test-user-id') IS NOT NULL,
    'Can request verification from inactive state'
);

-- Test 3: State changed correctly
SELECT ok(
    (SELECT status FROM user WHERE id = 'test-user-id') = 'pending_verification',
    'State changed to pending_verification'
);

-- Test 4: Invalid transition fails
SELECT ok(
    user_verify_email('test-user-id', 'invalid-token') IS NULL,
    'Invalid verification token is rejected'
);

-- Test 5: Valid verification works
SELECT ok(
    user_verify_email('test-user-id', 'valid-token') IS NOT NULL,
    'Valid verification token works'
);

-- Test 6: Final state is active
SELECT ok(
    (SELECT status FROM user WHERE id = 'test-user-id') = 'active',
    'User ends in active state after verification'
);

-- Cleanup
DELETE FROM user WHERE id = 'test-user-id';

ROLLBACK;
```

## 🗄️ Step 4: Run pgTAP Tests

```bash
# Install pgTAP in PostgreSQL (one-time setup)
psql $DATABASE_URL -c "
CREATE EXTENSION IF NOT EXISTS pgtap;
"

# Run the generated tests
specql test run --type pgtap entities/user.yaml

# Or run directly with psql
psql $DATABASE_URL -f tests/pgtap/user_state_machine_test.sql
```

**Expected output:**
```
user_state_machine_test.sql
1..6
ok 1 - User starts in inactive state
ok 2 - Can request verification from inactive state
ok 3 - State changed to pending_verification
ok 4 - Invalid verification token is rejected
ok 5 - Valid verification token works
ok 6 - User ends in active state after verification
```

## 🐍 Step 5: Review Generated pytest Tests

```bash
# View the Python tests
cat tests/pytest/test_user_state_machine.py
```

**Generated pytest tests include:**

```python
# Auto-generated pytest tests for user state machine
import pytest
import psycopg2
from specql.testing.fixtures import database_connection

class TestUserStateMachine:
    @pytest.fixture
    def db_conn(self, database_connection):
        return database_connection

    @pytest.fixture
    def test_user(self, db_conn):
        """Create a test user and return its ID"""
        with db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user (email, first_name, last_name, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, ('test@example.com', 'Test', 'User', 'inactive'))
            user_id = cursor.fetchone()[0]
            db_conn.commit()
            yield user_id

            # Cleanup
            cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
            db_conn.commit()

    def test_initial_state_is_inactive(self, db_conn, test_user):
        """Test that user starts in inactive state"""
        with db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM user WHERE id = %s",
                (test_user,)
            )
            status = cursor.fetchone()[0]
            assert status == 'inactive'

    def test_request_verification_transition(self, db_conn, test_user):
        """Test requesting verification from inactive state"""
        with db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_request_verification(%s)",
                (test_user,)
            )
            result = cursor.fetchone()[0]
            assert result is not None

            # Check state changed
            cursor.execute(
                "SELECT status FROM user WHERE id = %s",
                (test_user,)
            )
            status = cursor.fetchone()[0]
            assert status == 'pending_verification'

    def test_invalid_verification_fails(self, db_conn, test_user):
        """Test that invalid verification token is rejected"""
        # First request verification
        with db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_request_verification(%s)",
                (test_user,)
            )

            # Try invalid verification
            cursor.execute(
                "SELECT user_verify_email(%s, %s)",
                (test_user, 'invalid-token')
            )
            result = cursor.fetchone()[0]
            assert result is None

    def test_complete_verification_workflow(self, db_conn, test_user):
        """Test complete verification workflow"""
        with db_conn.cursor() as cursor:
            # Start verification
            cursor.execute(
                "SELECT user_request_verification(%s)",
                (test_user,)
            )

            # Complete verification
            cursor.execute(
                "SELECT user_verify_email(%s, %s)",
                (test_user, 'valid-token')
            )
            result = cursor.fetchone()[0]
            assert result is not None

            # Check final state
            cursor.execute(
                "SELECT status FROM user WHERE id = %s",
                (test_user,)
            )
            status = cursor.fetchone()[0]
            assert status == 'active'
```

## 🧪 Step 6: Run pytest Tests

```bash
# Install test dependencies
pip install pytest psycopg2-binary

# Set database URL for tests
export DATABASE_URL="postgresql://user:pass@localhost:5432/test_db"

# Run the tests
specql test run --type pytest entities/user.yaml

# Or run directly with pytest
pytest tests/pytest/test_user_state_machine.py -v
```

**Expected output:**
```
tests/pytest/test_user_state_machine.py::TestUserStateMachine::test_initial_state_is_inactive
PASSED
tests/pytest/test_user_state_machine.py::TestUserStateMachine::test_request_verification_transition
PASSED
tests/pytest/test_user_state_machine.py::TestUserStateMachine::test_invalid_verification_fails
PASSED
tests/pytest/test_user_state_machine.py::TestUserStateMachine::test_complete_verification_workflow
PASSED
```

## 📊 Step 7: Check Test Coverage

```bash
# Generate coverage report
specql test coverage entities/user.yaml

# View detailed coverage
cat reports/coverage/user_coverage.html
```

**Coverage includes:**
- ✅ **State transitions** - All valid and invalid paths
- ✅ **Guard conditions** - Precondition validation
- ✅ **Actions** - Side effect execution
- ✅ **Events** - Notification emission
- ✅ **Constraints** - Data integrity rules
- ✅ **Edge cases** - Error conditions and boundaries

## 🔄 Step 8: Integrate with CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

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
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install SpecQL
        run: pip install specql

      - name: Install pgTAP
        run: |
          psql postgresql://postgres:postgres@localhost:5432/postgres -c "CREATE EXTENSION pgtap;"

      - name: Generate Schema
        run: specql generate schema entities/user.yaml

      - name: Apply Schema
        run: |
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/00_foundation/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/10_tables/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/40_functions/*.sql

      - name: Generate Tests
        run: specql generate tests entities/user.yaml

      - name: Run pgTAP Tests
        run: specql test run --type pgtap entities/user.yaml

      - name: Run pytest Tests
        run: specql test run --type pytest entities/user.yaml
```

### Local Development

```bash
# Quick test cycle
make test        # Run all tests
make test-pgtap  # Run only pgTAP tests
make test-pytest # Run only pytest tests

# Watch mode for development
specql test watch entities/user.yaml
```

## 🎯 Step 9: Customize Generated Tests

### Add Custom Test Cases

```yaml
# entities/user.yaml (add to patterns)
patterns:
  - name: state_machine
    # ... existing config ...
    custom_tests:
      - name: test_admin_can_force_activate
        description: "Administrators can force user activation"
        setup: |
          -- Create admin user
          INSERT INTO user (email, status) VALUES ('admin@test.com', 'active');
        test: |
          -- Test admin force activation
          SELECT ok(
            user_admin_activate('test-user-id', 'admin-id') IS NOT NULL,
            'Admin can force user activation'
          );
```

### Test Data Factories

```python
# tests/fixtures/user_factory.py
def create_test_user(db_conn, **overrides):
    """Factory for creating test users"""
    defaults = {
        'email': f'test-{uuid.uuid4()}@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'status': 'inactive'
    }
    data = {**defaults, **overrides}

    with db_conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO user (email, first_name, last_name, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (data['email'], data['first_name'], data['last_name'], data['status']))
        return cursor.fetchone()[0]
```

## 📈 Step 10: Performance Testing

```bash
# Generate performance tests
specql generate tests --type performance entities/user.yaml

# Run performance benchmarks
specql test run --type performance entities/user.yaml

# View performance report
cat reports/performance/user_performance.html
```

**Performance tests measure:**
- ⏱️ **Query execution time**
- 📊 **Memory usage**
- 🔄 **Concurrent user load**
- 📈 **Scalability metrics**

## 🎯 Best Practices

### Test Organization
- **Separate concerns**: pgTAP for database logic, pytest for integration
- **Use fixtures**: Reusable test data setup
- **Test edge cases**: Invalid inputs, boundary conditions
- **Clean up**: Always remove test data

### CI/CD Integration
- **Fast feedback**: Run tests on every commit
- **Parallel execution**: Split test suites
- **Coverage requirements**: Enforce minimum coverage
- **Performance gates**: Fail builds on performance regressions

### Test Maintenance
- **Regenerate regularly**: Keep tests in sync with schema changes
- **Review failures**: Understand why tests fail
- **Update expectations**: When business logic changes intentionally

## 🆘 Troubleshooting

### "pgTAP extension not found"
```bash
# Install pgTAP
sudo apt install postgresql-pgtap  # Ubuntu
brew install pgtap                 # macOS

# Or install manually
psql $DATABASE_URL -f /path/to/pgtap.sql
```

### "Test database not available"
```bash
# Create test database
createdb specql_test

# Set test-specific environment
export DATABASE_URL_TEST="postgresql://localhost/specql_test"
```

### "Tests pass locally but fail in CI"
```bash
# Check environment differences
# - PostgreSQL version
# - Extensions installed
# - Database permissions
# - Environment variables

# Use same versions in CI as local
```

### "Performance tests are slow"
```bash
# Reduce test data size
# Use faster hardware
# Optimize test queries
# Run performance tests separately
```

## 🎉 Congratulations!

You've successfully:
- ✅ Generated comprehensive automated tests
- ✅ Run pgTAP tests in PostgreSQL
- ✅ Run pytest tests with Python
- ✅ Integrated tests into CI/CD pipeline
- ✅ Measured test coverage and performance

## 🚀 What's Next?

- **[CLI Reference](../reference/cli-reference.md)** - All SpecQL commands
- **[Test Generation Guide](../guides/test-generation/)** - Advanced testing features
- **[CI/CD Integration](../guides/test-generation/ci-cd-integration.md)** - Production pipelines

## 📚 Related Topics

- **[pgTAP Guide](../guides/test-generation/pgtap-tests.md)** - PostgreSQL testing
- **[pytest Guide](../guides/test-generation/pytest-tests.md)** - Python integration testing
- **[Performance Testing](../guides/test-generation/performance-tests.md)** - Benchmarking

**Ready to explore more SpecQL features? Check out the guides! 🚀**