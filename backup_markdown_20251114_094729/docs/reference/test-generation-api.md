# Test Generation API Reference

Complete reference for SpecQL's automatic test generation capabilities, including pgTAP and pytest test generation, configuration options, and generated test structures.

## Overview

SpecQL provides comprehensive automatic test generation for all entity patterns and actions. Tests are generated in two formats:

- **pgTAP**: PostgreSQL-native tests that run inside the database
- **pytest**: Python integration tests that test database functions from outside

## Test Generation Commands

### Generate Tests for All Entities

```bash
# Generate both pgTAP and pytest tests for all entities
specql generate tests

# Generate only pgTAP tests
specql generate tests --type pgtap

# Generate only pytest tests
specql generate tests --type pytest

# Generate tests for specific entities
specql generate tests --entities user.yaml contract.yaml

# Generate tests for specific patterns
specql generate tests --patterns crud state_machine

# Custom output directory
specql generate tests --output-dir custom/tests
```

### Test Execution Commands

```bash
# Run all tests
specql test

# Run specific test types
specql test unit        # pgTAP unit tests
specql test integration # pytest integration tests
specql test performance # Performance benchmarks

# Run tests with options
specql test --verbose              # Detailed output
specql test --parallel 4           # Parallel execution
specql test --coverage             # Coverage reporting
specql test --pattern "*crud*"     # Pattern matching
```

## pgTAP Test Generation

pgTAP tests run directly in PostgreSQL and validate database structure, constraints, and function behavior.

### Generated Test Structure

```
tests/
├── unit/
│   └── pgtap/
│       ├── entity_name_test.sql
│       └── entity_name_actions_test.sql
└── integration/
    └── pgtap/
        └── entity_name_workflow_test.sql
```

### Test Categories

#### Structure Tests (`entity_name_test.sql`)

Validate database schema and constraints.

**Generated Tests:**
- Table existence
- Column existence and types
- Primary key constraints
- Foreign key constraints
- Unique constraints
- Check constraints
- Index existence
- Trigger existence

**Example Generated Code:**
```sql
-- Structure Tests for User
-- Auto-generated: 2024-01-15T10:30:00
BEGIN;

SELECT plan(15);

-- Table exists
SELECT has_table('app'::name, 'tb_user'::name, 'User table should exist');

-- Required columns
SELECT has_column('app', 'tb_user', 'id', 'Has id column');
SELECT has_column('app', 'tb_user', 'email', 'Has email column');
SELECT has_column('app', 'tb_user', 'created_at', 'Has created_at column');

-- Column types
SELECT col_type_is('app', 'tb_user', 'id', 'uuid', 'id is uuid');
SELECT col_type_is('app', 'tb_user', 'email', 'text', 'email is text');

-- Constraints
SELECT col_is_pk('app', 'tb_user', 'id', 'id is primary key');
SELECT col_is_unique('app', 'tb_user', 'email', 'email is unique');

-- Indexes
SELECT has_index('app', 'tb_user', 'idx_user_email', 'Has email index');

ROLLBACK;
```

#### CRUD Tests (`entity_name_actions_test.sql`)

Test basic CRUD operations and data integrity.

**Generated Tests:**
- Create operations with valid data
- Create operations with invalid data
- Read operations return correct data
- Update operations modify data correctly
- Update operations with invalid data
- Delete operations remove data
- Delete operations with dependencies
- Data type validation
- Required field validation
- Foreign key validation

**Example Generated Code:**
```sql
-- CRUD Tests for User
-- Auto-generated: 2024-01-15T10:30:00
BEGIN;

SELECT plan(25);

-- Setup test data
INSERT INTO app.tb_user (id, email, first_name, created_at)
VALUES ('test-user-id'::uuid, 'test@example.com', 'Test', now());

-- Create tests
SELECT lives_ok(
    $$SELECT app.create_user('user-uuid'::uuid, '{"email": "new@example.com", "first_name": "New"}'::jsonb)$$,
    'create_user with valid data should succeed'
);

SELECT throws_ok(
    $$SELECT app.create_user('user-uuid'::uuid, '{"email": null}'::jsonb)$$,
    '23502', -- not_null_violation
    'create_user with null email should fail'
);

-- Read tests
SELECT results_eq(
    $$SELECT email FROM app.tb_user WHERE id = 'test-user-id'::uuid$$,
    $$VALUES ('test@example.com'::text)$$,
    'User read returns correct email'
);

-- Update tests
SELECT lives_ok(
    $$SELECT app.update_user('test-user-id'::uuid, 'user-uuid'::uuid, '{"first_name": "Updated"}'::jsonb)$$,
    'update_user with valid data should succeed'
);

SELECT results_eq(
    $$SELECT first_name FROM app.tb_user WHERE id = 'test-user-id'::uuid$$,
    $$VALUES ('Updated'::text)$$,
    'User update modifies first_name correctly'
);

ROLLBACK;
```

#### Action Tests (`entity_name_actions_test.sql`)

Test custom entity actions and business logic.

**Generated Tests:**
- Action execution with valid inputs
- Action execution with invalid inputs
- State transitions (for state machines)
- Validation rule enforcement
- Side effect verification
- Error condition handling
- Permission checking

**Example Generated Code:**
```sql
-- Action Tests for Contract
-- Auto-generated: 2024-01-15T10:30:00
BEGIN;

SELECT plan(20);

-- Setup test data
INSERT INTO contract.tb_contract (id, customer_org, status, total_value, created_at)
VALUES ('test-contract-id'::uuid, 'customer-uuid'::uuid, 'draft', 1000.00, now());

-- State machine tests
SELECT lives_ok(
    $$SELECT contract.submit_for_review('test-contract-id'::uuid, 'user-uuid'::uuid, '{}'::jsonb)$$,
    'submit_for_review from draft should succeed'
);

SELECT results_eq(
    $$SELECT status FROM contract.tb_contract WHERE id = 'test-contract-id'::uuid$$,
    $$VALUES ('submitted'::text)$$,
    'Contract status changes to submitted'
);

SELECT throws_ok(
    $$SELECT contract.submit_for_review('test-contract-id'::uuid, 'user-uuid'::uuid, '{}'::jsonb)$$,
    'invalid_state_transition',
    'submit_for_review from submitted should fail'
);

-- Validation tests
SELECT throws_ok(
    $$SELECT contract.create_contract('user-uuid'::uuid, '{"total_value": -100}'::jsonb)$$,
    'validation_failed',
    'create_contract with negative value should fail'
);

ROLLBACK;
```

#### Workflow Tests (`entity_name_workflow_test.sql`)

Test complex multi-step business processes.

**Generated Tests:**
- Complete workflow execution
- Partial workflow execution
- Workflow failure recovery
- State consistency validation
- Side effect verification
- Error handling validation

**Example Generated Code:**
```sql
-- Workflow Tests for Order
-- Auto-generated: 2024-01-15T10:30:00
BEGIN;

SELECT plan(15);

-- Complete order fulfillment workflow
SELECT lives_ok(
    $$SELECT order.start_order_fulfillment('order-uuid'::uuid, 'user-uuid'::uuid, order_data::jsonb)$$,
    'Complete order fulfillment should succeed'
);

-- Verify final state
SELECT results_eq(
    $$SELECT status FROM order.tb_order WHERE id = 'order-uuid'::uuid$$,
    $$VALUES ('delivered'::text)$$,
    'Order reaches delivered state'
);

-- Verify side effects
SELECT ok(
    EXISTS(SELECT 1 FROM shipping.tb_shipment WHERE order_id = 'order-uuid'::uuid),
    'Shipment record created'
);

SELECT ok(
    EXISTS(SELECT 1 FROM payment.tb_transaction WHERE order_id = 'order-uuid'::uuid),
    'Payment transaction recorded'
);

-- Partial workflow test
SELECT lives_ok(
    $$SELECT order.request_payment('order-uuid-2'::uuid, 'user-uuid'::uuid, '{}'::jsonb)$$,
    'Payment request should succeed'
);

SELECT results_eq(
    $$SELECT status FROM order.tb_order WHERE id = 'order-uuid-2'::uuid$$,
    $$VALUES ('payment_pending'::text)$$,
    'Order status is payment_pending'
);

ROLLBACK;
```

## pytest Test Generation

pytest tests validate database functions from Python, testing the complete application stack.

### Generated Test Structure

```
tests/
├── integration/
│   └── pytest/
│       └── test_entity_name.py
└── performance/
    └── pytest/
        └── test_entity_name_performance.py
```

### Integration Tests (`test_entity_name.py`)

Test entity operations from the application layer.

**Generated Tests:**
- CRUD operation integration
- Action execution integration
- Data serialization/deserialization
- Error handling integration
- Transaction boundary testing
- Connection pooling validation

**Example Generated Code:**
```python
"""Integration tests for User entity"""

import pytest
from uuid import UUID
import psycopg


class TestUserIntegration:
    """Integration tests for User CRUD and actions"""

    @pytest.fixture
    def clean_db(self, test_db_connection):
        """Clean User table before test"""
        with test_db_connection.cursor() as cur:
            cur.execute("DELETE FROM app.tb_user WHERE email LIKE 'test%'")
        test_db_connection.commit()

    def test_create_user_success(self, test_db_connection, clean_db):
        """Test successful user creation"""
        with test_db_connection.cursor() as cur:
            # Execute create function
            cur.execute("""
                SELECT app.create_user(
                    'test-user-id'::uuid,
                    '{"email": "test@example.com", "first_name": "Test", "last_name": "User"}'::jsonb
                )
            """)

            result = cur.fetchone()[0]

            # Verify result structure
            assert 'success' in result['status']
            assert result['entity_name'] == 'user'
            assert UUID(result['entity_id'])  # Valid UUID

            # Verify database state
            cur.execute("""
                SELECT email, first_name, last_name FROM app.tb_user
                WHERE id = %s
            """, (result['entity_id'],))

            user = cur.fetchone()
            assert user[0] == 'test@example.com'
            assert user[1] == 'Test'
            assert user[2] == 'User'

    def test_create_user_validation_error(self, test_db_connection, clean_db):
        """Test user creation with validation error"""
        with test_db_connection.cursor() as cur:
            # Try to create user with invalid data
            cur.execute("""
                SELECT app.create_user(
                    'test-user-id'::uuid,
                    '{"email": null, "first_name": "Test"}'::jsonb
                )
            """)

            result = cur.fetchone()[0]

            # Verify error response
            assert result['status'] == 'validation:failed'
            assert 'email' in str(result.get('errors', []))

    def test_update_user_partial(self, test_db_connection, clean_db):
        """Test partial user update"""
        with test_db_connection.cursor() as cur:
            # Create user first
            cur.execute("""
                SELECT app.create_user(
                    'test-user-id'::uuid,
                    '{"email": "test@example.com", "first_name": "Test"}'::jsonb
                )
            """)
            create_result = cur.fetchone()[0]
            user_id = create_result['entity_id']

            # Update only first_name
            cur.execute("""
                SELECT app.update_user(
                    %s::uuid,
                    'test-user-id'::uuid,
                    '{"first_name": "Updated"}'::jsonb
                )
            """, (user_id,))

            update_result = cur.fetchone()[0]

            # Verify update
            assert update_result['status'] == 'success'
            assert 'first_name' in update_result['updated_fields']

            # Verify database
            cur.execute("""
                SELECT first_name, last_name FROM app.tb_user WHERE id = %s
            """, (user_id,))

            user = cur.fetchone()
            assert user[0] == 'Updated'
            assert user[1] == 'Test'  # Unchanged

    def test_user_actions_state_machine(self, test_db_connection, clean_db):
        """Test user state machine transitions"""
        with test_db_connection.cursor() as cur:
            # Create user
            cur.execute("""
                SELECT app.create_user(
                    'test-user-id'::uuid,
                    '{"email": "test@example.com", "first_name": "Test", "status": "pending"}'::jsonb
                )
            """)
            create_result = cur.fetchone()[0]
            user_id = create_result['entity_id']

            # Test state transition
            cur.execute("""
                SELECT app.activate_user(%s::uuid, 'test-user-id'::uuid, '{}'::jsonb)
            """, (user_id,))

            transition_result = cur.fetchone()[0]

            # Verify transition
            assert transition_result['status'] == 'success'

            # Verify final state
            cur.execute("""
                SELECT status FROM app.tb_user WHERE id = %s
            """, (user_id,))

            final_status = cur.fetchone()[0]
            assert final_status == 'active'
```

### Performance Tests (`test_entity_name_performance.py`)

Benchmark entity operations under load.

**Generated Tests:**
- CRUD operation performance
- Bulk operation performance
- Concurrent access performance
- Memory usage monitoring
- Query optimization validation

**Example Generated Code:**
```python
"""Performance tests for User entity"""

import pytest
import time
import psycopg
from concurrent.futures import ThreadPoolExecutor


class TestUserPerformance:
    """Performance benchmarks for User operations"""

    def test_create_user_performance(self, test_db_connection, benchmark):
        """Benchmark user creation performance"""
        def create_user_batch():
            with test_db_connection.cursor() as cur:
                for i in range(100):
                    cur.execute("""
                        SELECT app.create_user(
                            'bench-user-id'::uuid,
                            '{"email": "bench%d@example.com", "first_name": "Bench", "last_name": "User"}'::jsonb
                        )
                    """, (i,))
                test_db_connection.commit()

        # Run benchmark
        result = benchmark(create_user_batch)

        # Assert performance requirements
        assert result.stats.mean < 1.0  # Less than 1 second per batch

    def test_bulk_create_performance(self, test_db_connection, benchmark):
        """Benchmark bulk user creation"""
        def bulk_create():
            users_data = [
                {"email": f"bulk{i}@example.com", "first_name": f"User{i}"}
                for i in range(1000)
            ]

            with test_db_connection.cursor() as cur:
                cur.execute("""
                    SELECT app.bulk_create_users(
                        'bench-user-id'::uuid,
                        %s::jsonb
                    )
                """, (users_data,))

        result = benchmark(bulk_create)

        # Bulk operations should be fast
        assert result.stats.mean < 5.0  # Less than 5 seconds for 1000 users

    def test_concurrent_access(self, test_db_connection):
        """Test concurrent user operations"""
        def worker(worker_id):
            with psycopg.connect(test_db_connection.info.dsn) as conn:
                with conn.cursor() as cur:
                    for i in range(50):
                        cur.execute("""
                            SELECT app.create_user(
                                'worker-user-id'::uuid,
                                '{"email": "worker%d_%d@example.com", "first_name": "Worker"}'::jsonb
                            )
                        """, (worker_id, i))
                    conn.commit()

        # Run 10 concurrent workers
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(worker, i) for i in range(10)]
            for future in futures:
                future.result()
            end_time = time.time()

        total_time = end_time - start_time

        # Should complete within reasonable time
        assert total_time < 30.0  # Less than 30 seconds for 500 operations

    def test_query_performance(self, test_db_connection):
        """Test query performance with indexes"""
        # Setup test data
        with test_db_connection.cursor() as cur:
            for i in range(10000):
                cur.execute("""
                    INSERT INTO app.tb_user (id, email, first_name, created_at)
                    VALUES (gen_random_uuid(), %s, %s, now())
                """, (f"user{i}@example.com", f"User{i}"))
            test_db_connection.commit()

        # Test indexed query performance
        with test_db_connection.cursor() as cur:
            start_time = time.time()
            cur.execute("""
                SELECT COUNT(*) FROM app.tb_user
                WHERE email LIKE 'user5%'
            """)
            count = cur.fetchone()[0]
            end_time = time.time()

        query_time = end_time - start_time

        # Should be fast with index
        assert query_time < 0.1  # Less than 100ms
        assert count > 0
```

## Test Configuration

### Test Database Setup

```yaml
# specql.yaml - Test configuration
test:
  database:
    host: localhost
    port: 5432
    name: specql_test
    user: test_user
    password: test_password

  fixtures:
    load_before: all  # Load fixtures before all tests
    load_after: none  # Don't reload between tests

  parallel:
    enabled: true
    workers: 4
    isolation: database  # Separate database per worker

  coverage:
    enabled: true
    report_types: [html, xml, term]
    minimum_coverage: 90
```

### Test Fixtures

SpecQL generates test data fixtures automatically:

```sql
-- Generated test fixtures
INSERT INTO app.tb_user (id, email, first_name, last_name, created_at)
VALUES
  ('fixture-user-1'::uuid, 'fixture1@example.com', 'Fixture', 'User1', now()),
  ('fixture-user-2'::uuid, 'fixture2@example.com', 'Fixture', 'User2', now());

INSERT INTO contract.tb_contract (id, customer_org, total_value, status, created_at)
VALUES
  ('fixture-contract-1'::uuid, 'fixture-user-1'::uuid, 5000.00, 'draft', now()),
  ('fixture-contract-2'::uuid, 'fixture-user-2'::uuid, 10000.00, 'approved', now());
```

## Test Execution Options

### Filtering Tests

```bash
# Run tests for specific entities
specql test --entities user contract

# Run tests matching pattern
specql test --pattern "*crud*"
specql test --pattern "*state_machine*"

# Run tests by category
specql test unit --category structure
specql test unit --category crud
specql test integration --category workflow
```

### Test Output Options

```bash
# Verbose output
specql test --verbose

# JSON output for CI/CD
specql test --format json --output results.json

# JUnit XML for CI systems
specql test --format junit --output junit.xml

# HTML report
specql test --report html --output reports/test_report.html
```

### Performance Testing

```bash
# Performance test with custom parameters
specql test performance --duration 60 --concurrency 10

# Load testing
specql test performance --load-test --users 1000 --ramp-up 30

# Memory profiling
specql test performance --memory-profile
```

## Test Result Analysis

### Understanding Test Results

```sql
-- Query test execution results
SELECT
    test_name,
    test_type,
    status,
    execution_time,
    error_message
FROM test_results
ORDER BY execution_time DESC
LIMIT 10;

-- Test coverage analysis
SELECT
    entity_name,
    test_count,
    passed_count,
    failed_count,
    ROUND(100.0 * passed_count / test_count, 1) as pass_rate,
    coverage_percentage
FROM test_coverage
ORDER BY coverage_percentage DESC;

-- Performance metrics
SELECT
    test_name,
    avg_execution_time,
    min_execution_time,
    max_execution_time,
    p95_execution_time
FROM test_performance_metrics
WHERE test_type = 'integration';
```

### Debugging Failed Tests

```bash
# Run single failing test with debug output
specql test --test "user_crud_test.test_create_user_validation" --debug

# Check test logs
tail -f logs/test_execution.log

# Inspect test database state
specql test --inspect-db --test "failing_test_name"

# Generate test data dump
specql test --dump-data --test "failing_test_name" --output debug_data.sql
```

## Best Practices

### Test Organization
- Keep unit tests focused on individual functions
- Use integration tests for cross-function workflows
- Separate performance tests from functional tests
- Use fixtures for consistent test data

### Test Data Management
- Use generated fixtures for deterministic tests
- Clean up test data between test runs
- Avoid dependencies between tests
- Use realistic data volumes for performance tests

### CI/CD Integration
- Run fast unit tests on every commit
- Run integration tests before merge
- Run performance tests nightly
- Set up test result notifications

### Performance Benchmarking
- Establish baseline performance metrics
- Monitor performance regressions
- Test with realistic data volumes
- Profile slow tests and optimize

## Troubleshooting

### Common Test Issues

**Tests failing due to database state:**
```bash
# Reset test database
specql test --reset-db

# Run tests with clean state
specql test --clean-state
```

**Performance tests timing out:**
```bash
# Increase test timeout
specql test performance --timeout 300

# Run performance tests separately
specql test performance --exclude-slow
```

**Test data conflicts:**
```bash
# Use isolated test databases
specql test --isolate-databases

# Generate unique test data
specql generate tests --unique-fixtures
```

---

**See Also:**
- [Pattern Library API](pattern-library-api.md)
- [YAML Schema Reference](yaml-schema.md)
- [Best Practices: Testing Strategy](../best-practices/testing-strategy.md)
- [CLI Reference](../reference/cli-reference.md)