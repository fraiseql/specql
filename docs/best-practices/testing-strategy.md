# Testing Strategy Best Practices

Comprehensive testing approach for SpecQL applications, covering unit tests, integration tests, performance tests, and CI/CD integration.

## Overview

SpecQL generates extensive tests automatically, but effective testing requires understanding test types, coverage goals, and testing best practices. This guide covers testing strategies for SpecQL applications.

## Test Pyramid for SpecQL

```
🐵 End-to-End Tests (Manual, ~10%)
├── API Integration Tests (~20%)
├── Component Tests (~30%)
├── Unit Tests (Generated, ~40%)
└── Static Analysis (Generated, ~10%)
```

### Unit Tests (40%)

**Generated automatically by SpecQL:**
- Schema validation tests
- CRUD operation tests
- State machine transition tests
- Validation rule tests
- Constraint tests

**Characteristics:**
- Fast execution (< 1 second)
- Isolated from external dependencies
- Generated from entity definitions
- High coverage of business logic

### Integration Tests (30%)

**Test component interactions:**
- Database operations with real PostgreSQL
- External service integrations
- Multi-entity transactions
- API endpoint testing

**Characteristics:**
- Medium execution time (seconds)
- Test real dependencies
- Validate data consistency
- Catch integration issues

### API Tests (20%)

**Test complete user workflows:**
- End-to-end business processes
- Authentication and authorization
- Error handling and edge cases
- Performance under load

**Characteristics:**
- Slower execution (minutes)
- Test complete user journeys
- Validate system behavior
- Catch workflow issues

### End-to-End Tests (10%)

**Manual testing of critical paths:**
- User interface workflows
- Critical business processes
- Cross-system integrations
- Performance validation

## Generated Test Coverage

### Automatic Test Generation

SpecQL generates tests for all patterns:

```bash
# Generate all tests
specql generate tests

# Generate specific test types
specql generate tests --type pgtap    # PostgreSQL tests
specql generate tests --type pytest   # Python integration tests

# Generate for specific entities
specql generate tests --entities user order

# Generate for specific patterns
specql generate tests --patterns crud state_machine
```

### Test File Structure

```
tests/
├── unit/
│   └── pgtap/
│       ├── entity_name_test.sql          # Schema tests
│       ├── entity_name_actions_test.sql  # CRUD tests
│       └── entity_name_workflow_test.sql # State machine tests
├── integration/
│   └── pytest/
│       └── test_entity_name.py           # Integration tests
└── performance/
    └── pytest/
        └── test_entity_name_performance.py  # Performance tests
```

## Unit Testing Strategy

### Schema Tests

**Validate database structure:**
```sql
-- Generated schema tests
SELECT plan(15);

-- Table exists
SELECT has_table('app', 'tb_user', 'User table exists');

-- Columns exist with correct types
SELECT has_column('app', 'tb_user', 'id');
SELECT col_type_is('app', 'tb_user', 'id', 'uuid');
SELECT col_is_pk('app', 'tb_user', 'id');

-- Constraints
SELECT col_is_unique('app', 'tb_user', 'email');
SELECT has_index('app', 'tb_user', 'idx_user_email');

-- Enums
SELECT enum_has_labels('user_status', ARRAY['active', 'inactive']);
```

### CRUD Tests

**Test basic operations:**
```sql
-- Generated CRUD tests
SELECT lives_ok(
    $$SELECT app.create_user('test-user'::uuid, '{"email": "test@example.com"}'::jsonb)$$,
    'create_user succeeds with valid data'
);

SELECT throws_ok(
    $$SELECT app.create_user('test-user'::uuid, '{"email": null}'::jsonb)$$,
    '23502',  -- not_null_violation
    'create_user fails with null email'
);

SELECT results_eq(
    $$SELECT email FROM app.tb_user WHERE id = 'test-user'::uuid$$,
    $$VALUES ('test@example.com'::text)$$,
    'User created with correct email'
);
```

### State Machine Tests

**Test workflow transitions:**
```sql
-- Generated state machine tests
-- Setup: Create order in pending state
SELECT app.create_order('test-user'::uuid, '{"status": "pending"}'::jsonb);

-- Test valid transition
SELECT lives_ok(
    $$SELECT app.confirm_order('test-order'::uuid, 'test-user'::uuid, '{}'::jsonb)$$,
    'confirm_order succeeds from pending'
);

SELECT results_eq(
    $$SELECT status FROM app.tb_order WHERE id = 'test-order'::uuid$$,
    $$VALUES ('confirmed'::text)$$,
    'Order status changed to confirmed'
);

-- Test invalid transition
SELECT throws_ok(
    $$SELECT app.confirm_order('test-order'::uuid, 'test-user'::uuid, '{}'::jsonb)$$,
    'invalid_state_transition',
    'confirm_order fails from confirmed'
);
```

### Validation Tests

**Test business rules:**
```sql
-- Generated validation tests
SELECT throws_ok(
    $$SELECT app.create_contract('test-user'::uuid, '{"total_value": -100}'::jsonb)$$,
    'validation_failed',
    'Contract creation fails with negative value'
);

SELECT lives_ok(
    $$SELECT app.validate_contract('test-user'::uuid, '{"total_value": 1000}'::jsonb)$$,
    'Contract validation passes with positive value'
);
```

## Integration Testing Strategy

### Database Integration Tests

**Test with real PostgreSQL:**
```python
class TestUserIntegration:
    def test_create_user_integration(self, db_connection):
        """Test user creation with database integration"""
        with db_connection.cursor() as cur:
            # Create user
            cur.execute("""
                SELECT app.create_user(
                    'test-user-id'::uuid,
                    '{"email": "integration@example.com", "name": "Integration Test"}'::jsonb
                )
            """)

            result = cur.fetchone()[0]

            # Verify success
            assert result['status'] == 'success'
            assert result['entity_name'] == 'user'

            # Verify database state
            cur.execute("""
                SELECT email, name FROM app.tb_user
                WHERE id = %s
            """, (result['entity_id'],))

            user = cur.fetchone()
            assert user[0] == 'integration@example.com'
            assert user[1] == 'Integration Test'
```

### Multi-Entity Tests

**Test complex transactions:**
```python
def test_create_order_with_items(db_connection):
    """Test order creation with items (multi-entity)"""
    with db_connection.cursor() as cur:
        # Create order with items in one transaction
        cur.execute("""
            SELECT sales.create_order_with_items(
                'customer-id'::uuid,
                '[{"product_id": "prod-1", "quantity": 2}, {"product_id": "prod-2", "quantity": 1}]'::jsonb
            )
        """)

        result = cur.fetchone()[0]

        # Verify order created
        assert result['status'] == 'success'

        # Verify order items created
        cur.execute("""
            SELECT COUNT(*) FROM sales.tb_order_item
            WHERE order_id = %s
        """, (result['entity_id'],))

        item_count = cur.fetchone()[0]
        assert item_count == 2

        # Verify inventory updated
        cur.execute("""
            SELECT stock_quantity FROM inventory.tb_product
            WHERE id = 'prod-1'
        """)

        stock = cur.fetchone()[0]
        assert stock == 8  # Assuming started with 10, ordered 2
```

### External Service Tests

**Test integrations with mocking:**
```python
def test_payment_processing_integration(mock_payment_service):
    """Test payment processing with mocked external service"""
    # Mock payment service response
    mock_payment_service.charge.return_value = {
        'success': True,
        'transaction_id': 'txn-123'
    }

    with db_connection.cursor() as cur:
        # Process payment
        cur.execute("""
            SELECT sales.process_payment(
                'order-id'::uuid,
                '{"amount": 100.00, "card_token": "tok_123"}'::jsonb
            )
        """)

        result = cur.fetchone()[0]

        # Verify payment service called
        mock_payment_service.charge.assert_called_once_with(
            amount=100.00,
            card_token='tok_123'
        )

        # Verify order updated
        assert result['status'] == 'success'
```

## Performance Testing Strategy

### Load Testing

**Test under realistic load:**
```python
def test_bulk_user_creation_performance(benchmark):
    """Benchmark bulk user creation performance"""
    def create_users_batch():
        users = [
            {"email": f"user{i}@example.com", "name": f"User {i}"}
            for i in range(1000)
        ]

        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT app.bulk_create_users(
                    'system-user'::uuid,
                    %s::jsonb
                )
            """, (users,))
            db_connection.commit()

    # Benchmark execution time
    result = benchmark(create_users_batch)

    # Assert performance requirements
    assert result.stats.mean < 5.0  # Less than 5 seconds for 1000 users
```

### Concurrent Access Tests

**Test multi-user scenarios:**
```python
def test_concurrent_order_creation(db_connection_pool):
    """Test concurrent order creation"""
    def create_order(worker_id):
        conn = db_connection_pool.getconn()
        try:
            with conn.cursor() as cur:
                for i in range(10):
                    cur.execute("""
                        SELECT sales.create_order(
                            'customer-id'::uuid,
                            '{"total": 100.00}'::jsonb
                        )
                    """)
                conn.commit()
        finally:
            db_connection_pool.putconn(conn)

    # Run 5 concurrent workers
    with ThreadPoolExecutor(max_workers=5) as executor:
        start_time = time.time()
        futures = [executor.submit(create_order, i) for i in range(5)]
        for future in futures:
            future.result()
        end_time = time.time()

    total_time = end_time - start_time

    # Should complete within reasonable time
    assert total_time < 30.0  # 50 orders in under 30 seconds
```

### Memory and Resource Tests

**Monitor resource usage:**
```python
def test_memory_usage_during_bulk_operation():
    """Test memory usage during large bulk operations"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Perform large bulk operation
    with db_connection.cursor() as cur:
        cur.execute("""
            SELECT app.bulk_import_users(%s::jsonb)
        """, (large_user_dataset,))

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    # Assert reasonable memory usage
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
```

## Test Data Management

### Test Fixtures

**Use consistent test data:**
```python
@pytest.fixture
def test_user(db_connection):
    """Create a test user fixture"""
    with db_connection.cursor() as cur:
        cur.execute("""
            SELECT app.create_user(
                'fixture-user-id'::uuid,
                '{"email": "fixture@example.com", "name": "Test User"}'::jsonb
            )
        """)
        result = cur.fetchone()[0]
        user_id = result['entity_id']

        yield user_id

        # Cleanup
        cur.execute("""
            DELETE FROM app.tb_user WHERE id = %s
        """, (user_id,))
        db_connection.commit()
```

### Factory Pattern

**Generate test data programmatically:**
```python
class TestDataFactory:
    @staticmethod
    def create_user(overrides=None):
        """Create a test user with defaults"""
        defaults = {
            "email": f"user-{uuid.uuid4()}@example.com",
            "name": "Test User",
            "status": "active"
        }
        if overrides:
            defaults.update(overrides)
        return defaults

    @staticmethod
    def create_order(customer_id, overrides=None):
        """Create a test order"""
        defaults = {
            "customer_id": str(customer_id),
            "total_amount": 100.00,
            "status": "pending"
        }
        if overrides:
            defaults.update(overrides)
        return defaults
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test
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
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install specql pytest psycopg2-binary

      - name: Generate test database
        run: |
          specql init --env test
          specql generate schema
          specql db migrate
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/specql_test

      - name: Generate tests
        run: specql generate tests

      - name: Run unit tests
        run: specql test unit
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/specql_test

      - name: Run integration tests
        run: specql test integration
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/specql_test

      - name: Run performance tests
        run: specql test performance
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/specql_test
```

### Test Reporting

**Generate comprehensive reports:**
```bash
# Generate coverage report
specql test --coverage --format cobertura --output coverage.xml

# Generate HTML test report
specql test --format html --output test_report.html

# Upload to external services
# Codecov, SonarQube, etc.
```

## Test Organization Best Practices

### Test Naming Conventions

```python
class TestUserCRUD:
    """Test CRUD operations for User entity"""

    def test_create_user_success(self):
        """Test successful user creation"""

    def test_create_user_validation_error(self):
        """Test user creation with validation error"""

    def test_update_user_partial(self):
        """Test partial user update"""

class TestUserStateMachine:
    """Test state machine transitions for User entity"""

    def test_activate_user_from_pending(self):
        """Test user activation from pending state"""

    def test_activate_user_invalid_transition(self):
        """Test invalid activation transition"""
```

### Test Isolation

**Ensure tests don't interfere:**
```python
@pytest.fixture(autouse=True)
def clean_database(db_connection):
    """Clean database before each test"""
    with db_connection.cursor() as cur:
        # Clean all test data
        cur.execute("DELETE FROM app.tb_user WHERE email LIKE 'test%'")
        cur.execute("DELETE FROM sales.tb_order WHERE created_at > now() - interval '1 hour'")
    db_connection.commit()
```

### Test Categories

**Organize tests by purpose:**
- **unit/**: Generated tests, fast feedback
- **integration/**: Component integration tests
- **e2e/**: End-to-end workflow tests
- **performance/**: Load and performance tests
- **contract/**: API contract tests

## Debugging Test Failures

### Common Issues

**Database state issues:**
```bash
# Check test database state
specql test --inspect-db --test failing_test_name

# Reset test database
specql test --reset-db
```

**Race conditions:**
```python
# Add delays for timing-dependent tests
import time
time.sleep(0.1)  # Small delay to avoid race conditions
```

**Resource leaks:**
```python
# Ensure proper cleanup
@pytest.fixture(autouse=True)
def cleanup_resources():
    yield
    # Cleanup code here
```

### Test Debugging Tools

**Verbose test output:**
```bash
specql test --verbose --debug failing_test
```

**Database query logging:**
```python
# Enable query logging in tests
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**Interactive debugging:**
```python
# Add breakpoint in test
import pdb; pdb.set_trace()

def test_debug_example():
    # Test code
    result = some_function()
    pdb.set_trace()  # Debug here
    assert result == expected
```

## Performance Testing Guidelines

### Realistic Load Patterns

**Test with production-like data:**
```python
def create_realistic_user_load():
    """Create test data resembling production"""
    # Mix of user types
    user_types = [
        ("regular", 70),    # 70% regular users
        ("premium", 20),    # 20% premium users
        ("admin", 5),       # 5% admin users
        ("inactive", 5),    # 5% inactive users
    ]

    users = []
    for user_type, percentage in user_types:
        count = int(1000 * percentage / 100)
        for i in range(count):
            users.append({
                "email": f"{user_type}{i}@example.com",
                "type": user_type,
                "status": "active" if user_type != "inactive" else "inactive"
            })

    return users
```

### Performance Baselines

**Establish and monitor baselines:**
```python
PERFORMANCE_BASELINES = {
    "create_user": 0.01,      # 10ms max
    "bulk_create_100": 0.5,   # 500ms max
    "query_active_users": 0.1, # 100ms max
}

def test_performance_baseline(operation_name):
    """Test that operations meet performance baselines"""
    with timer() as t:
        # Execute operation
        result = perform_operation(operation_name)

    baseline = PERFORMANCE_BASELINES[operation_name]
    assert t.elapsed < baseline, f"Operation {operation_name} exceeded baseline: {t.elapsed} > {baseline}"
```

## Test Coverage Goals

### Coverage Metrics

**Aim for high coverage:**
- **Unit Tests**: 90%+ line coverage
- **Integration Tests**: 80%+ API coverage
- **End-to-End Tests**: 100% critical paths

### Coverage Analysis

```bash
# Generate coverage report
specql test --coverage

# Check coverage by entity
SELECT
    entity_name,
    unit_test_coverage,
    integration_test_coverage,
    overall_coverage
FROM test_coverage_report
ORDER BY overall_coverage ASC;

# Identify untested code
SELECT
    entity_name,
    action_name,
    untested_lines,
    risk_assessment
FROM code_coverage_gaps
WHERE risk_assessment = 'high';
```

## Continuous Testing

### Pre-commit Hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run fast unit tests
specql test unit --quick

if [ $? -ne 0 ]; then
    echo "Unit tests failed. Commit aborted."
    exit 1
fi

# Run schema validation
specql validate

if [ $? -ne 0 ]; then
    echo "Schema validation failed. Commit aborted."
    exit 1
fi
```

### Automated Test Runs

**Scheduled testing:**
```bash
# Nightly full test suite
0 2 * * * cd /path/to/project && specql test

# Performance regression testing
0 3 * * * cd /path/to/project && specql test performance --baseline-check
```

---

**See Also:**
- [Pattern Selection Best Practices](pattern-selection.md)
- [Entity Design Best Practices](entity-design.md)
- [Performance Best Practices](performance.md)
- [Test Generation API](../reference/test-generation-api.md)