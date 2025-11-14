# Getting Started with Test Generation

Learn how SpecQL automatically generates comprehensive tests from your YAML specifications. Get instant test coverage for business logic, data validation, and performance - without writing any test code.

## 🎯 What You'll Learn

- How automatic test generation works
- Generate and run your first tests
- Understand test coverage and results
- Integrate testing into your workflow
- Customize test generation

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Entity with patterns created](../getting-started/first-entity.md)
- PostgreSQL database running
- Basic understanding of testing concepts

## 💡 How Test Generation Works

### From YAML to Tests

**SpecQL analyzes your entity specifications and generates:**

```yaml
# entities/user.yaml
name: user
fields:
  id: uuid
  email: string
  status: string

patterns:
  - name: state_machine
    states: [inactive, active, suspended]
    transitions:
      - from: inactive
        to: active
        trigger: activate
```

**Generates:**
- **pgTAP tests** - Database-level validation
- **pytest tests** - Application-level testing
- **Performance tests** - Benchmarking and profiling

### Test Categories

| Test Type | Purpose | Example |
|-----------|---------|---------|
| **Business Logic** | Pattern behavior | State machine transitions |
| **Data Validation** | Constraints & rules | Email format, required fields |
| **Integration** | Cross-entity operations | Multi-table transactions |
| **Performance** | Speed & scalability | Query execution time |
| **Edge Cases** | Boundary conditions | Invalid inputs, error states |

## 🚀 Step 1: Generate Your First Tests

### Create a Test Entity

```bash
# Create entities directory
mkdir -p entities

# Create user entity with patterns
cat > entities/user.yaml << 'EOF'
name: user
description: "User account management"

fields:
  id: uuid
  email: string
  first_name: string
  last_name: string
  status: string
  created_at: timestamp

patterns:
  - name: state_machine
    description: "User account lifecycle"
    initial_state: inactive
    states: [inactive, active, suspended]
    transitions:
      - from: inactive
        to: active
        trigger: activate
      - from: active
        to: suspended
        trigger: suspend
      - from: suspended
        to: active
        trigger: reactivate

  - name: validation
    description: "User data validation"
    rules:
      - name: email_required
        field: email
        rule: "email IS NOT NULL"
        message: "Email is required"
      - name: email_format
        field: email
        rule: "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'"
        message: "Email must be in valid format"
EOF
```

### Generate Schema

```bash
# Generate database schema
specql generate schema entities/user.yaml

# Apply to database
psql $DATABASE_URL -f db/schema/10_tables/user.sql
psql $DATABASE_URL -f db/schema/20_constraints/user_constraints.sql
psql $DATABASE_URL -f db/schema/40_functions/user_state_machine.sql
```

### Generate Tests

```bash
# Generate all test types
specql generate tests entities/user.yaml

# Check generated files
tree tests/
# tests/
# ├── pgtap/
# │   ├── user_state_machine_test.sql
# │   └── user_validation_test.sql
# └── pytest/
#     ├── test_user_state_machine.py
#     └── test_user_validation.py
```

## 🧪 Step 2: Run pgTAP Tests

### Install pgTAP

```bash
# Install pgTAP extension (one-time setup)
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

# Verify installation
psql $DATABASE_URL -c "SELECT pgtap.version();"
```

### Run Tests

```bash
# Run pgTAP tests
specql test run --type pgtap entities/user.yaml

# Expected output:
# user_state_machine_test.sql
# 1..8
# ok 1 - User starts in inactive state
# ok 2 - Can transition from inactive to active
# ok 3 - State changes correctly after transition
# ok 4 - Cannot transition from invalid state
# ok 5 - Guard conditions are enforced
# ok 6 - Actions execute on transition
# ok 7 - Events are emitted
# ok 8 - Error handling works correctly
```

### Manual Test Execution

```bash
# Run tests directly with psql
psql $DATABASE_URL -f tests/pgtap/user_state_machine_test.sql

# Run specific test file
psql $DATABASE_URL -f tests/pgtap/user_validation_test.sql
```

## 🐍 Step 3: Run pytest Tests

### Install Dependencies

```bash
# Install Python testing dependencies
pip install pytest psycopg2-binary

# Optional: Install pytest plugins
pip install pytest-cov pytest-xdist pytest-html
```

### Run Tests

```bash
# Run pytest tests
specql test run --type pytest entities/user.yaml

# Expected output:
# tests/pytest/test_user_state_machine.py::TestUserStateMachine::test_initial_state_is_inactive
# PASSED
# tests/pytest/test_user_state_machine.py::test_successful_activation
# PASSED
# tests/pytest/test_user_state_machine.py::test_invalid_transition_fails
# PASSED
# tests/pytest/test_user_validation.py::test_email_validation
# PASSED
```

### Advanced pytest Options

```bash
# Run with coverage
specql test run --type pytest entities/user.yaml --cov --cov-report html

# Run in parallel
specql test run --type pytest entities/user.yaml --parallel 4

# Generate HTML report
specql test run --type pytest entities/user.yaml --html-report results.html

# Run specific test
specql test run --type pytest entities/user.yaml --filter "test_state_machine"
```

## 📊 Step 4: Check Test Coverage

### Generate Coverage Report

```bash
# Generate coverage report
specql test coverage entities/user.yaml

# Output formats
specql test coverage entities/user.yaml --format html --output coverage.html
specql test coverage entities/user.yaml --format json --output coverage.json
```

### Coverage Metrics

**What gets tested:**
- ✅ **Pattern Logic** - All state machine transitions and guards
- ✅ **Validation Rules** - All business rules and constraints
- ✅ **Data Integrity** - Foreign keys, uniqueness, types
- ✅ **Error Conditions** - Invalid inputs and edge cases
- ✅ **Performance** - Query execution time and scalability

**Coverage Goals:**
- **Line Coverage**: >95% of generated code
- **Branch Coverage**: >90% of conditional logic
- **Pattern Coverage**: 100% of declared patterns
- **Edge Case Coverage**: All boundary conditions

## 🔍 Step 5: Understand Test Results

### pgTAP Test Structure

```sql
-- Generated pgTAP test
BEGIN;

-- Setup test data
INSERT INTO user (id, email, status)
VALUES ('test-user-id', 'test@example.com', 'inactive');

-- Test 1: Initial state
SELECT ok(
    (SELECT status FROM user WHERE id = 'test-user-id') = 'inactive',
    'User starts in inactive state'
);

-- Test 2: Valid transition
SELECT ok(
    user_activate('test-user-id') IS NOT NULL,
    'Can activate user from inactive state'
);

-- Test 3: State change
SELECT ok(
    (SELECT status FROM user WHERE id = 'test-user-id') = 'active',
    'State changes to active after activation'
);

-- Cleanup
DELETE FROM user WHERE id = 'test-user-id';

ROLLBACK;
```

### pytest Test Structure

```python
# Generated pytest test
import pytest
import psycopg2
from specql.testing.fixtures import database_connection

class TestUserStateMachine:
    @pytest.fixture
    def db_conn(self, database_connection):
        return database_connection

    @pytest.fixture
    def test_user(self, db_conn):
        """Create test user and return ID"""
        with db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user (email, first_name, status)
                VALUES (%s, %s, %s)
                RETURNING id
            """, ('test@example.com', 'Test', 'inactive'))
            user_id = cursor.fetchone()[0]
            db_conn.commit()
            yield user_id

            # Cleanup
            cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
            db_conn.commit()

    def test_initial_state_is_inactive(self, db_conn, test_user):
        """Test user starts in inactive state"""
        with db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM user WHERE id = %s",
                (test_user,)
            )
            status = cursor.fetchone()[0]
            assert status == 'inactive'

    def test_successful_activation(self, db_conn, test_user):
        """Test successful user activation"""
        with db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_activate(%s)",
                (test_user,)
            )
            result = cursor.fetchone()[0]
            assert result is not None

            # Verify state change
            cursor.execute(
                "SELECT status FROM user WHERE id = %s",
                (test_user,)
            )
            status = cursor.fetchone()[0]
            assert status == 'active'
```

## ⚙️ Step 6: Customize Test Generation

### Test Configuration

```yaml
# Add to your entity YAML
name: user
# ... fields and patterns ...

test_config:
  # Enable/disable test generation
  enabled: true

  # Test types to generate
  types: [pgtap, pytest, performance]

  # Test data configuration
  fixtures:
    - name: basic_user
      email: "test@example.com"
      first_name: "Test"
      last_name: "User"
      status: "inactive"

    - name: edge_cases
      email: ""  # Invalid email
      first_name: ""  # Empty name
      status: "invalid_status"

  # Performance test settings
  performance:
    enabled: true
    iterations: 100
    concurrency: 5
    timeout: "30 seconds"

  # Coverage requirements
  coverage:
    minimum: 95
    exclude_patterns: ["debug_*", "temp_*"]
```

### Custom Test Data

```yaml
test_config:
  fixtures:
    # Realistic user data
    - name: premium_user
      email: "premium@example.com"
      first_name: "Premium"
      last_name: "User"
      status: "active"
      subscription_level: "premium"

    # Bulk test data
    - name: bulk_users
      count: 1000
      template:
        email: "user_{index}@example.com"
        first_name: "User"
        last_name: "{index}"
        status: "active"
```

## 🔄 Step 7: Integrate into Development Workflow

### Development Cycle

```bash
# 1. Edit entity specification
vim entities/user.yaml

# 2. Validate YAML
specql validate entities/user.yaml

# 3. Generate schema
specql generate schema entities/user.yaml

# 4. Apply schema changes
psql $DATABASE_URL -f db/schema/10_tables/user.sql

# 5. Generate tests
specql generate tests entities/user.yaml

# 6. Run tests
specql test run entities/user.yaml

# 7. Check coverage
specql test coverage entities/user.yaml
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Run tests before committing
specql validate entities/*.yaml
specql generate tests entities/*.yaml
specql test run entities/*.yaml

if [ $? -ne 0 ]; then
    echo "Tests failed! Fix issues before committing."
    exit 1
fi
```

### IDE Integration

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Generate Tests",
      "type": "shell",
      "command": "specql",
      "args": ["generate", "tests", "entities/*.yaml"],
      "group": "build"
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "specql",
      "args": ["test", "run", "entities/*.yaml"],
      "group": "test"
    }
  ]
}
```

## 🆘 Troubleshooting

### "Tests not generating"
```bash
# Check YAML syntax
specql validate entities/user.yaml

# Force regeneration
specql generate tests entities/user.yaml --force

# Check file permissions
ls -la tests/
```

### "pgTAP tests failing"
```bash
# Check pgTAP installation
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'pgtap';"

# Run tests manually for debugging
psql $DATABASE_URL -f tests/pgtap/user_test.sql -v

# Check database connection
psql $DATABASE_URL -c "SELECT 1;"
```

### "pytest tests failing"
```bash
# Check Python dependencies
pip list | grep pytest

# Run tests directly
pytest tests/pytest/ -v -s

# Check database connection in tests
python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"
```

### "Coverage report empty"
```bash
# Run tests first
specql test run entities/user.yaml

# Generate coverage with verbose output
specql test coverage entities/user.yaml --verbose

# Check coverage data exists
ls -la coverage/
```

### "Performance tests timeout"
```bash
# Reduce test data size
specql generate tests entities/user.yaml --performance-data-size 100

# Increase timeout
specql test run --type performance entities/user.yaml --timeout 300

# Run performance tests separately
specql test run --type performance entities/user.yaml --concurrency 1
```

## 🎯 Best Practices

### Test Generation
- **Generate tests immediately** after creating entities
- **Run tests frequently** during development
- **Check coverage regularly** to maintain quality
- **Use realistic test data** that matches production

### Test Maintenance
- **Regenerate tests** when specifications change
- **Review test failures** to understand root causes
- **Update test expectations** for intentional changes
- **Archive obsolete tests** to keep suites clean

### Performance Testing
- **Set realistic targets** based on production requirements
- **Monitor performance trends** over time
- **Profile bottlenecks** to optimize slow operations
- **Test at production scale** when possible

### CI/CD Integration
- **Run tests on every commit** for fast feedback
- **Use parallel execution** to speed up test suites
- **Block deployments** on test failures
- **Store test artifacts** for analysis and debugging

## 🎉 Congratulations!

You've successfully:
- ✅ **Generated comprehensive tests** from YAML specifications
- ✅ **Run pgTAP tests** in PostgreSQL
- ✅ **Run pytest tests** with Python
- ✅ **Checked test coverage** and quality metrics
- ✅ **Integrated testing** into your development workflow

## 🚀 What's Next?

- **[pgTAP Tests](pgtap-tests.md)** - Deep dive into PostgreSQL testing
- **[pytest Tests](pytest-tests.md)** - Python integration testing
- **[Performance Tests](performance-tests.md)** - Benchmarking and optimization
- **[CI/CD Integration](ci-cd-integration.md)** - Automated testing pipelines

**Ready to achieve 100% test coverage? Let's explore the test types! 🚀**