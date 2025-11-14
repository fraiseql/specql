# pgTAP Tests - PostgreSQL Native Testing

pgTAP is SpecQL's PostgreSQL-native testing framework. Run comprehensive tests directly in the database without external dependencies. Test business logic, constraints, functions, and data integrity with native SQL performance.

## 🎯 What You'll Learn

- pgTAP testing fundamentals
- Generate and run database-level tests
- Test patterns, constraints, and functions
- Debug test failures
- Performance and best practices

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Entity with patterns created](../getting-started/first-entity.md)
- PostgreSQL with pgTAP extension
- Basic SQL knowledge

## 💡 pgTAP Fundamentals

### What is pgTAP?

**pgTAP** is a unit testing framework for PostgreSQL that allows you to:
- ✅ **Write tests in SQL** - No external languages required
- ✅ **Test database objects** - Functions, constraints, triggers
- ✅ **Run tests in-database** - Direct PostgreSQL execution
- ✅ **Get TAP output** - Standard test protocol
- ✅ **Integrate with CI/CD** - Works with any test runner

### Why pgTAP for SpecQL?

| Feature | pgTAP | pytest | Traditional SQL Tests |
|---------|-------|--------|----------------------|
| **Performance** | ⚡ Fastest | 🐌 Slower | ⚡ Fast |
| **Setup** | ✅ None | 🛠️ Python deps | ✅ None |
| **Coverage** | ✅ Database logic | ✅ App logic | ⚠️ Limited |
| **Maintenance** | ✅ Auto-generated | ✅ Auto-generated | 🛠️ Manual |
| **CI/CD** | ✅ Native | ✅ Python | 🛠️ Custom |

## 🚀 Step 1: Install pgTAP

### Install Extension

```bash
# Install pgTAP extension
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

# Verify installation
psql $DATABASE_URL -c "SELECT pgtap.version();"
```

### Alternative Installation Methods

#### Using pgxn
```bash
# Install via pgxn client
pgxn install pgtap
pgxn load pgtap -d mydatabase
```

#### Manual Installation
```bash
# Download and install manually
wget https://github.com/theory/pgtap/archive/master.zip
unzip master.zip
cd pgtap-master
make
make install
make installcheck
```

#### Docker Installation
```bash
# Use PostgreSQL with pgTAP pre-installed
docker run --name postgres-pgtap \
  -e POSTGRES_DB=mydb \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypass \
  -p 5432:5432 \
  -d theory/pgtap:latest
```

## 🧪 Step 2: Generate pgTAP Tests

### Create Test Entity

```yaml
# entities/order.yaml
name: order
fields:
  id: uuid
  customer_id: uuid
  status: string
  total_amount: decimal
  created_at: timestamp

patterns:
  - name: state_machine
    description: "Order processing workflow"
    initial_state: pending
    states: [pending, confirmed, shipped, delivered]
    transitions:
      - from: pending
        to: confirmed
        trigger: confirm
        guard: "total_amount > 0"
      - from: confirmed
        to: shipped
        trigger: ship
      - from: shipped
        to: delivered
        trigger: deliver

  - name: validation
    description: "Order validation rules"
    rules:
      - name: positive_total
        field: total_amount
        rule: "total_amount > 0"
        message: "Order total must be positive"
```

### Generate Tests

```bash
# Generate pgTAP tests
specql generate tests --type pgtap entities/order.yaml

# Check generated files
ls -la tests/pgtap/
# order_state_machine_test.sql
# order_validation_test.sql
```

### Generated Test Structure

```sql
-- tests/pgtap/order_state_machine_test.sql
BEGIN;

-- Setup test data
INSERT INTO order (id, customer_id, status, total_amount)
VALUES ('test-order-id', 'test-customer-id', 'pending', 100.00);

-- Test 1: Initial state verification
SELECT ok(
    (SELECT status FROM order WHERE id = 'test-order-id') = 'pending',
    'Order starts in pending state'
);

-- Test 2: Valid transition
SELECT ok(
    order_confirm('test-order-id') IS NOT NULL,
    'Can confirm order from pending state'
);

-- Test 3: State change verification
SELECT ok(
    (SELECT status FROM order WHERE id = 'test-order-id') = 'confirmed',
    'Order status changes to confirmed after confirmation'
);

-- Test 4: Invalid transition prevention
SELECT ok(
    order_ship('test-order-id') IS NULL,
    'Cannot ship unconfirmed order'
);

-- Test 5: Guard condition enforcement
UPDATE order SET total_amount = 0 WHERE id = 'test-order-id';
SELECT ok(
    order_confirm('test-order-id') IS NULL,
    'Cannot confirm order with zero total'
);

-- Cleanup
DELETE FROM order WHERE id = 'test-order-id';

ROLLBACK;
```

## 🏃 Step 3: Run pgTAP Tests

### Basic Test Execution

```bash
# Run all pgTAP tests for entity
specql test run --type pgtap entities/order.yaml

# Expected output:
# order_state_machine_test.sql
# 1..5
# ok 1 - Order starts in pending state
# ok 2 - Can confirm order from pending state
# ok 3 - Order status changes to confirmed after confirmation
# ok 4 - Cannot ship unconfirmed order
# ok 5 - Cannot confirm order with zero total
```

### Manual Test Execution

```bash
# Run tests directly with psql
psql $DATABASE_URL -f tests/pgtap/order_state_machine_test.sql

# Run multiple test files
psql $DATABASE_URL -f tests/pgtap/order_state_machine_test.sql \
                   -f tests/pgtap/order_validation_test.sql
```

### Advanced Execution Options

```bash
# Run with verbose output
specql test run --type pgtap entities/order.yaml --verbose

# Run specific test file
specql test run --type pgtap entities/order.yaml --filter "*state_machine*"

# Generate TAP output for CI/CD
specql test run --type pgtap entities/order.yaml --tap-output results.tap

# Run tests in parallel (if multiple entities)
specql test run --type pgtap entities/*.yaml --parallel
```

## 📊 Step 4: Understand pgTAP Assertions

### Core Assertions

| Assertion | Purpose | Example |
|-----------|---------|---------|
| `ok(boolean, description)` | Test passes if true | `ok(1=1, 'Math works')` |
| `is(actual, expected, desc)` | Exact equality | `is(status, 'active')` |
| `isnt(actual, unexpected, desc)` | Inequality | `isnt(status, 'deleted')` |
| `cmp_ok(left, op, right, desc)` | Comparison | `cmp_ok(total, '>', 0)` |

### Database-Specific Assertions

```sql
-- Table and column assertions
SELECT has_table('order');
SELECT has_column('order', 'status');
SELECT col_is_pk('order', 'id');
SELECT col_is_fk('order', 'customer_id');

-- Constraint assertions
SELECT has_check('order', 'positive_total');
SELECT check_is('order', 'positive_total', 'total_amount > 0');

-- Function assertions
SELECT has_function('order_confirm');
SELECT function_returns('order_confirm', 'uuid', 'order_result');

-- Index assertions
SELECT has_index('order', 'idx_order_status');
SELECT index_is_unique('order', 'idx_order_customer_status');
```

### Business Logic Assertions

```sql
-- State machine testing
SELECT ok(
    order_can_transition('order-id', 'confirm'),
    'Order can transition to confirmed'
);

SELECT ok(
    NOT order_can_transition('order-id', 'ship'),
    'Order cannot transition to shipped from current state'
);

-- Validation testing
SELECT ok(
    validate_order_data('order-id'),
    'Order data passes validation'
);

-- Performance assertions
SELECT cmp_ok(
    (SELECT count(*) FROM order WHERE status = 'pending'), '<', 1000,
    'Pending orders count is reasonable'
);
```

## 🔍 Step 5: Debug Test Failures

### Common Failure Patterns

#### Test Setup Issues
```sql
-- Check test data exists
SELECT * FROM order WHERE id = 'test-order-id';

-- Verify test isolation
SELECT count(*) FROM order;  -- Should be 1 in test
```

#### Assertion Failures
```sql
-- Debug state machine issues
SELECT status FROM order WHERE id = 'test-order-id';
SELECT * FROM order_get_available_transitions('test-order-id');

-- Check guard conditions
SELECT total_amount > 0 FROM order WHERE id = 'test-order-id';
```

#### Constraint Violations
```sql
-- Check for constraint conflicts
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'order'::regclass;

-- Test constraint manually
INSERT INTO order (id, status, total_amount)
VALUES ('debug-id', 'pending', -100);
-- Should fail with constraint violation
```

### Debugging Workflow

```bash
# 1. Run test with verbose output
specql test run --type pgtap entities/order.yaml --verbose

# 2. Check test data setup
psql $DATABASE_URL -c "
BEGIN;
INSERT INTO order (id, customer_id, status, total_amount)
VALUES ('debug-order', 'debug-customer', 'pending', 100.00);
SELECT * FROM order WHERE id = 'debug-order';
ROLLBACK;
"

# 3. Test individual assertions
psql $DATABASE_URL -c "
BEGIN;
INSERT INTO order (id, customer_id, status, total_amount)
VALUES ('debug-order', 'debug-customer', 'pending', 100.00);

-- Test each assertion manually
SELECT (SELECT status FROM order WHERE id = 'debug-order') = 'pending';
SELECT order_confirm('debug-order') IS NOT NULL;
SELECT (SELECT status FROM order WHERE id = 'debug-order') = 'confirmed';

ROLLBACK;
"

# 4. Check generated functions
psql $DATABASE_URL -c "\df order_confirm"
psql $DATABASE_URL -c "SELECT pg_get_functiondef('order_confirm'::regproc);"
```

## 📈 Step 6: Performance Testing with pgTAP

### Performance Assertions

```sql
-- Query performance tests
SELECT cmp_ok(
    (SELECT extract(epoch from now() - query_start) FROM (
        SELECT now() as query_start,
               (SELECT count(*) FROM order WHERE status = 'pending') as result
    ) q), '<', 0.1,
    'Order count query executes in under 100ms'
);

-- Function performance tests
SELECT ok(
    (SELECT extract(epoch from (
        SELECT now() - clock_timestamp() +
               order_confirm('test-order-id')::interval
    )) < 0.5),
    'Order confirmation completes in under 500ms'
);
```

### Load Testing

```sql
-- Bulk operation performance
SELECT cmp_ok(
    (SELECT extract(epoch from (
        SELECT now() - clock_timestamp() FROM (
            SELECT count(order_bulk_update_status(order_ids, 'confirmed'))
            FROM (SELECT array_agg(id) as order_ids FROM order LIMIT 1000) q
        ) timing
    ))), '<', 5.0,
    'Bulk update of 1000 orders completes in under 5 seconds'
);
```

### Index Performance Tests

```sql
-- Index usage verification
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_stat_user_indexes
        WHERE relname = 'order' AND indexrelname = 'idx_order_status'
        AND idx_scan > 0
    ),
    'Status index is being used'
);

-- Query plan analysis
SELECT ok(
    NOT EXISTS (
        SELECT 1 FROM pg_stat_statements
        WHERE query LIKE '%SELECT * FROM order WHERE status =%'
        AND mean_time > 1000000  -- Over 1 second
    ),
    'Order status queries are fast'
);
```

## 🔧 Step 7: Customize pgTAP Tests

### Test Configuration

```yaml
# In your entity YAML
name: order
# ... fields and patterns ...

test_config:
  pgtap:
    # Test isolation
    schema: test_schema  # Run tests in separate schema

    # Data setup
    fixtures:
      - name: test_customer
        table: customer
        data:
          id: test-customer-id
          name: Test Customer

      - name: test_order
        table: order
        data:
          id: test-order-id
          customer_id: test-customer-id
          status: pending
          total_amount: 100.00

    # Test categories
    categories:
      - unit: Test individual functions
      - integration: Test function interactions
      - performance: Test execution speed

    # Custom assertions
    custom_assertions:
      - name: order_is_valid
        sql: "SELECT order_meets_business_rules(id) FROM order WHERE id = $1"
```

### Custom Test Templates

```sql
-- Custom test template for complex scenarios
CREATE OR REPLACE FUNCTION test_order_workflow()
RETURNS SETOF TEXT AS $$
DECLARE
    order_id UUID := gen_random_uuid();
    customer_id UUID := gen_random_uuid();
BEGIN
    -- Setup
    INSERT INTO customer (id, name) VALUES (customer_id, 'Test Customer');
    INSERT INTO order (id, customer_id, status, total_amount)
    VALUES (order_id, customer_id, 'pending', 150.00);

    -- Test complete workflow
    RETURN NEXT ok(order_confirm(order_id) IS NOT NULL, 'Can confirm order');
    RETURN NEXT is((SELECT status FROM order WHERE id = order_id), 'confirmed', 'Status updated');

    RETURN NEXT ok(order_ship(order_id) IS NOT NULL, 'Can ship confirmed order');
    RETURN NEXT is((SELECT status FROM order WHERE id = order_id), 'shipped', 'Order shipped');

    RETURN NEXT ok(order_deliver(order_id) IS NOT NULL, 'Can deliver shipped order');
    RETURN NEXT is((SELECT status FROM order WHERE id = order_id), 'delivered', 'Order delivered');

    -- Cleanup
    DELETE FROM order WHERE id = order_id;
    DELETE FROM customer WHERE id = customer_id;
END;
$$ LANGUAGE plpgsql;
```

## 🔄 Step 8: CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/pgtap-tests.yml
name: pgTAP Tests

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

      - name: Install SpecQL
        run: pip install specql

      - name: Setup pgTAP
        run: |
          psql postgresql://postgres:postgres@localhost:5432/postgres -c "CREATE EXTENSION pgtap;"

      - name: Generate Schema
        run: specql generate schema entities/*.yaml

      - name: Apply Schema
        run: |
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/00_foundation/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/10_tables/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/40_functions/*.sql

      - name: Generate pgTAP Tests
        run: specql generate tests --type pgtap entities/*.yaml

      - name: Run pgTAP Tests
        run: specql test run --type pgtap entities/*.yaml

      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: pgtap-results
          path: test-results/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Setup Database') {
            steps {
                sh '''
                    docker run -d --name postgres-test \
                        -e POSTGRES_PASSWORD=test \
                        -p 5432:5432 postgres:15

                    sleep 10

                    psql postgresql://postgres:test@localhost:5432/postgres \
                        -c "CREATE EXTENSION pgtap;"
                '''
            }
        }

        stage('Generate Tests') {
            steps {
                sh 'specql generate tests --type pgtap entities/*.yaml'
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    specql test run --type pgtap entities/*.yaml \
                        --junit-xml results.xml
                '''
            }
            post {
                always {
                    junit 'results.xml'
                }
            }
        }
    }
}
```

## 🎯 Best Practices

### Test Design
- **Test one thing per assertion** - Keep tests focused
- **Use descriptive test names** - Explain what each test validates
- **Test edge cases** - Include boundary conditions
- **Isolate tests** - Each test should be independent

### Performance
- **Keep tests fast** - pgTAP tests should run in seconds
- **Use appropriate data sizes** - Test with realistic data volumes
- **Index test data** - Ensure queries perform well
- **Profile slow tests** - Optimize bottlenecks

### Maintenance
- **Regenerate tests regularly** - Keep in sync with schema changes
- **Review test failures** - Understand root causes
- **Update test expectations** - When business logic changes
- **Document complex tests** - Explain non-obvious test logic

### Database Considerations
- **Use transactions** - Isolate test data with BEGIN/ROLLBACK
- **Clean up test data** - Don't leave test artifacts
- **Test constraints** - Verify database integrity rules
- **Check permissions** - Ensure test user has required access

## 🆘 Troubleshooting

### "pgTAP extension not found"
```bash
# Check PostgreSQL version compatibility
psql $DATABASE_URL -c "SELECT version();"

# Install correct pgTAP version
# For PostgreSQL 15, use pgTAP 1.2.0+
```

### "Tests pass locally but fail in CI"
```bash
# Check environment differences
# - PostgreSQL version
# - pgTAP version
# - Database collation
# - Timezone settings

# Use same versions in CI as local
# Test with CI database version locally
```

### "Test data conflicts"
```sql
-- Use unique identifiers
INSERT INTO order (id, customer_id, status)
VALUES (gen_random_uuid(), gen_random_uuid(), 'pending');

-- Or use test-specific schemas
CREATE SCHEMA test_schema;
SET search_path TO test_schema;
```

### "Performance tests are slow"
```sql
-- Reduce test data size
SELECT cmp_ok(
    (SELECT count(*) FROM order LIMIT 100), '<', 100,
    'Sample query is fast'
);

-- Use EXPLAIN to optimize queries
EXPLAIN ANALYZE SELECT * FROM order WHERE status = 'pending';
```

### "Function not found errors"
```bash
# Check function exists
psql $DATABASE_URL -c "\df order_confirm"

# Regenerate functions
specql generate schema entities/order.yaml --force

# Apply functions to database
psql $DATABASE_URL -f db/schema/40_functions/order_state_machine.sql
```

## 📊 Success Metrics

### Test Quality Metrics
- **Test execution time**: <30 seconds for full suite
- **Test coverage**: >95% of database functions
- **Assertion count**: 10-20 assertions per pattern
- **Failure rate**: <1% in stable branches

### Performance Benchmarks
- **Simple queries**: <10ms average
- **Complex functions**: <100ms average
- **Bulk operations**: <5 seconds for 1000 records
- **Index usage**: >90% of queries use appropriate indexes

### Reliability Goals
- **Zero false positives** - Tests only fail on real issues
- **Consistent results** - Same tests pass/fail across runs
- **Fast feedback** - Results available within 5 minutes
- **CI stability** - <5% flaky tests

## 🎉 Summary

pgTAP testing provides:
- ✅ **Native PostgreSQL testing** - No external dependencies
- ✅ **Comprehensive database coverage** - Functions, constraints, triggers
- ✅ **Fast execution** - Direct database performance
- ✅ **CI/CD integration** - Standard TAP output
- ✅ **Auto-generated tests** - Zero manual test writing

## 🚀 What's Next?

- **[pytest Tests](pytest-tests.md)** - Python integration testing
- **[Performance Tests](performance-tests.md)** - Benchmarking and optimization
- **[CI/CD Integration](ci-cd-integration.md)** - Automated testing pipelines
- **[Custom Test Patterns](../best-practices/testing.md)** - Advanced testing techniques

**Ready to achieve comprehensive database test coverage? Let's continue! 🚀**