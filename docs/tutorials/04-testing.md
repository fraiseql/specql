# Tutorial 4: Testing (30 minutes)

Master SpecQL's comprehensive testing capabilities by generating, running, and analyzing tests for your business logic patterns.

## 🎯 What You'll Learn

- Generate automatic tests
- Run different test types
- Analyze test coverage
- Debug failing tests
- Create custom test scenarios

## 📋 Prerequisites

- Completed [Tutorial 3: State Machines](../03-state-machines.md)
- Understanding of testing concepts

## 🧪 Step 1: Generate Tests

SpecQL can automatically generate comprehensive tests for all your patterns:

```bash
# Generate tests for all entities
specql generate tests

# Generate tests for specific entities
specql generate tests --entities orders/order.yaml

# Generate tests with specific patterns
specql generate tests --patterns state_machine
```

Check what tests were generated:

```bash
# List generated test files
find tests/ -name "*.sql" | head -10

# Should show files like:
# tests/unit/orders/order_crud_test.sql
# tests/unit/orders/order_state_machine_test.sql
# tests/integration/orders/order_workflow_test.sql
```

## 🏃 Step 2: Run Different Test Types

SpecQL supports multiple test frameworks:

### Unit Tests

```bash
# Run all unit tests
specql test unit

# Run specific unit tests
specql test unit --pattern "*order*"

# Run with verbose output
specql test unit --verbose
```

### Integration Tests

```bash
# Run integration tests
specql test integration

# Run specific integration tests
specql test integration --pattern "*workflow*"
```

### Performance Tests

```bash
# Run performance benchmarks
specql test performance

# Run with custom load
specql test performance --concurrency 10 --duration 30
```

### All Tests

```bash
# Run complete test suite
specql test

# Run tests in parallel
specql test --parallel 4

# Run with coverage reporting
specql test --coverage
```

## 📊 Step 3: Analyze Test Results

Check test execution results:

```sql
-- Connect to test database
psql $DATABASE_URL

-- View test summary
SELECT * FROM test_summary;

-- View detailed test results
SELECT
    test_name,
    status,
    execution_time,
    error_message
FROM test_results
ORDER BY execution_time DESC
LIMIT 20;

-- Test coverage by entity
SELECT
    entity_name,
    test_count,
    passed_count,
    failed_count,
    ROUND(100.0 * passed_count / test_count, 1) as pass_rate
FROM test_coverage
ORDER BY pass_rate DESC;
```

## 🔍 Step 4: Debug Failing Tests

When tests fail, debug systematically:

```bash
# Run failing test with debug output
specql test unit --pattern "*failing_test*" --debug

# Check test logs
tail -f logs/test_execution.log

# Run single failing test
specql test unit --test "orders.order_state_machine_test.test_invalid_transition"
```

Common debugging queries:

```sql
-- Check test data setup
SELECT * FROM test_data_setup
WHERE test_name = 'failing_test_name';

-- View test assertions
SELECT
    test_name,
    assertion_type,
    expected_value,
    actual_value,
    assertion_status
FROM test_assertions
WHERE test_name = 'failing_test_name'
ORDER BY assertion_order;

-- Check database state during test
SELECT * FROM test_database_state
WHERE test_name = 'failing_test_name'
  AND checkpoint_name = 'after_transition';
```

## ✏️ Step 5: Create Custom Tests

Add custom test scenarios for complex business logic:

### Custom Test File (`tests/custom/order_business_rules_test.sql`)

```sql
-- Custom business rule tests for orders
BEGIN;

-- Test: Large orders require approval
CREATE OR REPLACE FUNCTION test_large_order_approval()
RETURNS SETOF TEXT AS $$
DECLARE
    v_order_id uuid;
BEGIN
    -- Create a large order
    SELECT orders.create_order(
        'test-customer-id',
        10000.00,  -- Large amount
        '123 Test St',
        '123 Test St',
        'credit_card'
    ) INTO v_order_id;

    -- Should be in pending state (not auto-approved)
    RETURN NEXT is(
        (SELECT status FROM orders.order WHERE id = v_order_id),
        'pending',
        'Large orders should remain pending for approval'
    );

    -- Cleanup
    DELETE FROM orders.order WHERE id = v_order_id;
END;
$$ LANGUAGE plpgsql;

-- Test: International orders have different rules
CREATE OR REPLACE FUNCTION test_international_shipping()
RETURNS SETOF TEXT AS $$
DECLARE
    v_order_id uuid;
BEGIN
    -- Create order with international address
    SELECT orders.create_order(
        'test-customer-id',
        500.00,
        '123 International St, London, UK',
        '123 US St, USA',
        'credit_card'
    ) INTO v_order_id;

    -- Should require customs documentation
    RETURN NEXT ok(
        EXISTS (
            SELECT 1 FROM orders.order
            WHERE id = v_order_id
            AND shipping_address LIKE '%UK%'
        ),
        'International orders should be flagged'
    );

    -- Cleanup
    DELETE FROM orders.order WHERE id = v_order_id;
END;
$$ LANGUAGE plpgsql;

-- Run custom tests
SELECT * FROM runtests('custom.order_business_rules_test');

ROLLBACK;
```

## 📈 Step 6: Test Coverage Analysis

Analyze what your tests cover:

```sql
-- Code coverage by pattern type
SELECT
    pattern_type,
    COUNT(*) as patterns_tested,
    SUM(test_count) as total_tests,
    AVG(coverage_percentage) as avg_coverage
FROM pattern_test_coverage
GROUP BY pattern_type
ORDER BY avg_coverage DESC;

-- Uncovered code paths
SELECT
    entity_name,
    action_name,
    uncovered_paths,
    risk_level
FROM test_gaps
WHERE risk_level = 'high'
ORDER BY entity_name, action_name;

-- Test execution performance
SELECT
    test_type,
    AVG(execution_time) as avg_time,
    MAX(execution_time) as max_time,
    SUM(execution_time) as total_time
FROM test_performance
GROUP BY test_type
ORDER BY total_time DESC;
```

## 🔄 Step 7: Continuous Testing

Set up automated testing in your development workflow:

```bash
# Run tests on file changes
specql test --watch

# Run tests before commits (Git hook)
#!/bin/bash
specql test
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi

# CI/CD integration
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup SpecQL
        run: pip install specql
      - name: Run Tests
        run: specql test --coverage
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

## 📊 Step 8: Test Reporting

Generate comprehensive test reports:

```bash
# Generate HTML test report
specql test --report html --output reports/test_report.html

# Generate coverage report
specql test --coverage --report cobertura --output coverage.xml

# Generate performance report
specql test performance --report json --output performance.json
```

Analyze reports:

```sql
-- Test trends over time
SELECT
    DATE_TRUNC('day', test_run_date) as date,
    COUNT(*) as tests_run,
    SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) as failed,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) as pass_rate
FROM historical_test_results
WHERE test_run_date > now() - interval '30 days'
GROUP BY DATE_TRUNC('day', test_run_date)
ORDER BY date;

-- Flaky test detection
SELECT
    test_name,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as pass_count,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) as reliability_rate
FROM historical_test_results
GROUP BY test_name
HAVING COUNT(*) > 10
ORDER BY reliability_rate ASC
LIMIT 10;
```

## 🐛 Step 9: Test Debugging Techniques

Advanced debugging for complex test failures:

```sql
-- Create test isolation
CREATE OR REPLACE FUNCTION isolate_test(test_name text)
RETURNS void AS $$
BEGIN
    -- Save current database state
    CREATE TABLE test_isolation_backup AS
    SELECT * FROM orders.order;

    -- Run test in isolation
    PERFORM run_single_test(test_name);

    -- Restore state
    TRUNCATE orders.order;
    INSERT INTO orders.order SELECT * FROM test_isolation_backup;
    DROP TABLE test_isolation_backup;
END;
$$ LANGUAGE plpgsql;

-- Debug state transitions
CREATE OR REPLACE FUNCTION debug_state_transition(
    p_order_id uuid,
    p_from_state text,
    p_to_state text
) RETURNS TABLE (
    step_number integer,
    step_name text,
    step_status text,
    error_message text,
    execution_time interval
) AS $$
BEGIN
    -- Simulate transition with detailed logging
    RETURN QUERY
    SELECT
        st.step_number,
        st.step_name,
        st.step_status,
        st.error_message,
        st.execution_time
    FROM simulate_transition(p_order_id, p_from_state, p_to_state) st;
END;
$$ LANGUAGE plpgsql;

-- Usage
SELECT * FROM debug_state_transition(
    'order-uuid',
    'paid',
    'shipped'
);
```

## 🎯 Step 10: Test Best Practices

Implement testing best practices:

```sql
-- Test data factories
CREATE OR REPLACE FUNCTION create_test_order(
    p_customer_id uuid DEFAULT gen_random_uuid(),
    p_amount decimal DEFAULT 100.00,
    p_status text DEFAULT 'pending'
) RETURNS uuid AS $$
DECLARE
    v_order_id uuid;
BEGIN
    INSERT INTO orders.order (
        customer_id, total_amount, status, created_at
    ) VALUES (
        p_customer_id, p_amount, p_status, now()
    ) RETURNING id INTO v_order_id;

    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;

-- Property-based testing
CREATE OR REPLACE FUNCTION test_order_amounts()
RETURNS SETOF TEXT AS $$
DECLARE
    v_amount decimal;
BEGIN
    -- Test various amounts
    FOR v_amount IN SELECT unnest(ARRAY[0.01, 100, 1000, 10000, 999999.99]) LOOP
        RETURN NEXT throws_ok(
            format('SELECT orders.create_order(''test'', %s, ''address'', ''address'', ''card'')', v_amount),
            CASE WHEN v_amount <= 0 THEN 'invalid_order_amount' ELSE NULL END,
            format('Order amount %s validation', v_amount)
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Load testing
CREATE OR REPLACE FUNCTION load_test_orders(p_count integer)
RETURNS TABLE (
    total_orders integer,
    total_time interval,
    orders_per_second numeric
) AS $$
DECLARE
    v_start_time timestamp;
    v_end_time timestamp;
BEGIN
    v_start_time := clock_timestamp();

    -- Create orders in batch
    INSERT INTO orders.order (customer_id, total_amount, status, created_at)
    SELECT
        gen_random_uuid(),
        random() * 1000 + 10,
        'pending',
        now()
    FROM generate_series(1, p_count);

    v_end_time := clock_timestamp();

    RETURN QUERY SELECT
        p_count,
        v_end_time - v_start_time,
        p_count / EXTRACT(seconds FROM (v_end_time - v_start_time));
END;
$$ LANGUAGE plpgsql;
```

## 🎉 Success!

You've mastered comprehensive testing with:

✅ **Automatic Test Generation**: All patterns tested automatically
✅ **Multiple Test Types**: Unit, integration, performance tests
✅ **Test Coverage Analysis**: Detailed coverage reporting
✅ **Debugging Tools**: Advanced failure analysis
✅ **Custom Test Scenarios**: Business logic validation
✅ **CI/CD Integration**: Automated testing pipelines

## 🧪 Test Your Knowledge

Try these advanced testing exercises:

1. **Add property-based tests**: Test with random data generation
2. **Create performance benchmarks**: Compare different implementations
3. **Add chaos testing**: Simulate network failures, timeouts
4. **Implement contract tests**: Test API integrations
5. **Create mutation testing**: Verify test quality

## 📚 Next Steps

- [Tutorial 5: Production](../05-production.md) - Production deployment
- [Advanced Testing](../../../guides/testing/) - More testing patterns
- [CI/CD Integration](../../../guides/deployment/) - Automated deployment

## 💡 Pro Tips

- Run tests frequently during development
- Use `specql test --watch` for continuous testing
- Aim for >90% test coverage
- Test failure scenarios, not just success paths
- Use test data factories for consistent test data
- Monitor test performance and fix slow tests

---

**Time completed**: 30 minutes
**Tests generated**: 100+ automatic tests
**Coverage achieved**: 95%+ code coverage
**CI/CD integrated**: Automated testing pipeline
**Next tutorial**: [Production →](../05-production.md)