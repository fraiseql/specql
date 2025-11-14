# Test Commands - Running and Managing Tests

The `specql test` commands execute generated tests, generate coverage reports, and manage test execution. This guide covers all test-related CLI commands and options.

## 🎯 What You'll Learn

- Running pgTAP, pytest, and performance tests
- Test execution options and filtering
- Coverage report generation
- Parallel test execution
- Test result analysis
- CI/CD test integration

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Tests generated](../guides/cli/generate.md)
- PostgreSQL database with schema applied
- Test environment configured

## 💡 Test Command Overview

### Test Types

| Command | Purpose | Speed | Coverage |
|---------|---------|-------|----------|
| `specql test run --type pgtap` | Database-level tests | ⚡ Fast | Business logic |
| `specql test run --type pytest` | Application-level tests | 🐌 Slower | API integration |
| `specql test run --type performance` | Benchmarking tests | 🐌 Slowest | Performance |

### Test Execution Pipeline

```mermaid
graph LR
    A[Test Command] --> B[Setup Environment]
    B --> C[Load Test Data]
    C --> D[Execute Tests]
    D --> E[Collect Results]
    E --> F[Generate Reports]
    F --> G[Cleanup]
```

## 🚀 Running Tests

### Basic Test Execution

```bash
# Run all test types for an entity
specql test run entities/user.yaml

# Run specific test type
specql test run --type pgtap entities/user.yaml
specql test run --type pytest entities/user.yaml
specql test run --type performance entities/user.yaml

# Run tests for multiple entities
specql test run entities/user.yaml entities/company.yaml

# Run all tests in directory
specql test run entities/*.yaml
```

### Test Execution Options

```bash
# Verbose output
specql test run entities/user.yaml --verbose

# Run specific test pattern
specql test run entities/user.yaml --filter "*state_machine*"

# Run with timeout
specql test run entities/user.yaml --timeout 300

# Parallel execution
specql test run entities/*.yaml --parallel

# Continue on failure
specql test run entities/*.yaml --continue-on-error
```

## 📊 Test Results and Output

### pgTAP Test Output

```bash
# Run pgTAP tests
specql test run --type pgtap entities/user.yaml

# Example output:
# user_state_machine_test.sql
# 1..5
# ok 1 - User starts in inactive state
# ok 2 - Can transition from inactive to active
# ok 3 - State changes correctly after transition
# ok 4 - Cannot transition from invalid state
# ok 5 - Guard conditions are enforced
#
# Test Summary:
# ✅ Passed: 5/5 tests
# ⏱️  Execution time: 0.23 seconds
```

### pytest Test Output

```bash
# Run pytest tests
specql test run --type pytest entities/user.yaml

# Example output:
# tests/pytest/test_user_state_machine.py::TestUserStateMachine::test_initial_state_is_inactive
# PASSED
# tests/pytest/test_user_state_machine.py::test_successful_activation
# PASSED
# tests/pytest/test_user_state_machine.py::test_invalid_transition_fails
# PASSED
#
# Test Summary:
# ✅ Passed: 3/3 tests
# ⏱️  Execution time: 1.45 seconds
# 📊 Coverage: 95.2%
```

### Performance Test Output

```bash
# Run performance tests
specql test run --type performance entities/user.yaml

# Example output:
# Performance Test Results for user
# ===================================
#
# Test: user_activate
# Iterations: 100
# Mean: 0.0234s
# Median: 0.0218s
# Min: 0.0189s
# Max: 0.0456s
# StdDev: 0.0056s
# P95: 0.0321s
#
# Performance Requirements:
# ✅ user_activate: 0.0234s < 0.0500s (target)
#
# Test Summary:
# ✅ All performance targets met
# ⏱️  Total execution time: 2.34 seconds
```

## 📈 Coverage Reports

### Generate Coverage Reports

```bash
# Generate coverage report
specql test coverage entities/user.yaml

# Different output formats
specql test coverage entities/user.yaml --format html --output coverage.html
specql test coverage entities/user.yaml --format json --output coverage.json
specql test coverage entities/user.yaml --format xml --output coverage.xml

# Coverage for multiple entities
specql test coverage entities/*.yaml --format html --output full-coverage.html
```

### Coverage Report Contents

**Text Format:**
```
Coverage Report for user
========================

Test Coverage Summary:
✅ Line Coverage: 95.2%
✅ Branch Coverage: 89.7%
✅ Function Coverage: 100.0%

Pattern Coverage:
✅ state_machine: 100% (5/5 transitions tested)
✅ validation: 95% (19/20 rules tested)

Missing Coverage:
❌ user.validate_email_format - Not tested
❌ user.suspend_inactive_user - Edge case not covered
```

**HTML Format:**
- Interactive coverage visualization
- File-by-file breakdown
- Test case mapping
- Trend analysis

## 🔧 Advanced Test Options

### Test Filtering

```bash
# Run specific test file
specql test run entities/user.yaml --filter "test_user_state_machine.py"

# Run tests matching pattern
specql test run entities/user.yaml --filter "*validation*"

# Run specific test method
specql test run --type pytest entities/user.yaml --filter "test_successful_activation"

# Exclude tests
specql test run entities/user.yaml --exclude "*performance*"
```

### Test Configuration

```bash
# Custom test data size
specql test run entities/user.yaml --test-data-size large

# Custom iterations for performance tests
specql test run --type performance entities/user.yaml --iterations 1000

# Custom concurrency
specql test run --type performance entities/user.yaml --concurrency 10

# Custom timeout
specql test run entities/user.yaml --timeout 600
```

### Environment Configuration

```bash
# Use specific environment
specql test run entities/user.yaml --env staging

# Custom database URL
specql test run entities/user.yaml --database-url "postgresql://test:test@localhost/testdb"

# Custom test directory
specql test run entities/user.yaml --test-dir custom/tests
```

## 🔄 Parallel and Distributed Testing

### Parallel Execution

```bash
# Run tests in parallel
specql test run entities/*.yaml --parallel

# Specify parallelism level
specql test run entities/*.yaml --parallel 4

# Parallel by entity
specql test run entities/user.yaml entities/company.yaml --parallel
```

### CI/CD Parallel Testing

```yaml
# .github/workflows/parallel-tests.yml
name: Parallel Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-group: [1, 2, 3, 4]

    steps:
      - uses: actions/checkout@v4

      - name: Setup test environment
        run: |
          # Setup database and schema...

      - name: Run parallel tests
        run: |
          # Split entities into groups
          entities=$(ls entities/*.yaml | sed -n "${{ matrix.test-group }}~4p")
          specql test run $entities --parallel
```

### Distributed Testing

```bash
# Run on multiple database instances
specql test run entities/user.yaml --database-url "postgresql://db1,testdb"
specql test run entities/company.yaml --database-url "postgresql://db2,testdb"

# Load balancing
specql test run entities/*.yaml --load-balance --workers 3
```

## 📊 Test Result Analysis

### Test Result Formats

```bash
# JUnit XML for CI/CD
specql test run entities/user.yaml --junit-xml results.xml

# TAP output
specql test run --type pgtap entities/user.yaml --tap-output results.tap

# JSON results
specql test run entities/user.yaml --json-output results.json

# CSV export
specql test run entities/user.yaml --csv-output results.csv
```

### Result Analysis

```bash
# Show test summary
specql test results entities/user.yaml

# Compare with previous run
specql test compare entities/user.yaml --baseline previous-results.json

# Show failed tests
specql test results entities/user.yaml --failed-only

# Show slow tests
specql test results entities/user.yaml --slow-tests
```

### Performance Analysis

```bash
# Performance regression detection
specql test run --type performance entities/user.yaml --baseline baseline.json

# Performance profiling
specql test profile entities/user.yaml --operation user_activate

# Memory usage analysis
specql test run entities/user.yaml --memory-profile
```

## 🐛 Debugging Test Failures

### Debugging Workflow

```bash
# 1. Run tests with verbose output
specql test run entities/user.yaml --verbose

# 2. Run specific failing test
specql test run entities/user.yaml --filter "*failing_test*"

# 3. Check test data setup
psql $DATABASE_URL -c "SELECT * FROM user LIMIT 5;"

# 4. Run test manually
psql $DATABASE_URL -f tests/pgtap/user_test.sql

# 5. Check database logs
tail -f /var/log/postgresql/postgresql.log
```

### Common Failure Patterns

**pgTAP Test Failures:**
```sql
-- Check test isolation
SELECT * FROM user WHERE id LIKE 'test-%';

-- Debug assertion
SELECT user_activate('test-user-id');
SELECT * FROM user WHERE id = 'test-user-id';
```

**pytest Test Failures:**
```python
# Add debug prints
def test_user_activation(db_cursor, test_user):
    print(f"Test user ID: {test_user}")

    result = user_activate(test_user)
    print(f"Activation result: {result}")

    # Check database state
    db_cursor.execute("SELECT status FROM user WHERE id = %s", (test_user,))
    status = db_cursor.fetchone()[0]
    print(f"User status: {status}")

    assert status == 'active'
```

**Performance Test Failures:**
```bash
# Check system resources
top -p $(pgrep postgres)

# Profile query
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM user WHERE status = 'active';"

# Check database configuration
psql $DATABASE_URL -c "SHOW shared_buffers;"
psql $DATABASE_URL -c "SHOW work_mem;"
```

## 🔧 Test Management

### Test Lifecycle

```bash
# Generate tests
specql generate tests entities/user.yaml

# Run tests
specql test run entities/user.yaml

# Check coverage
specql test coverage entities/user.yaml

# Clean test data
specql test clean entities/user.yaml

# Archive test results
specql test archive entities/user.yaml --output test-results-$(date +%Y%m%d).tar.gz
```

### Test Data Management

```bash
# Setup test data
specql test setup entities/user.yaml

# Reset test database
specql test reset entities/user.yaml

# Backup test data
specql test backup entities/user.yaml --output test-data.sql

# Restore test data
specql test restore entities/user.yaml --input test-data.sql
```

### Test Configuration

```yaml
# In entity YAML
name: user
# ... fields and patterns ...

test_config:
  # Test execution
  timeout: 300
  parallel: true
  continue_on_error: false

  # Test data
  fixtures:
    - name: test_user
      count: 100
      template:
        email: "user_{index}@example.com"
        status: "active"

  # Performance requirements
  performance:
    targets:
      user_activate: { p95: 200ms, mean: 100ms }
      user_query: { p95: 100ms, mean: 50ms }

  # Coverage requirements
  coverage:
    minimum: 95
    exclude_patterns: ["debug_*", "temp_*"]
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
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

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install specql pytest psycopg2-binary

      - name: Setup database
        run: |
          specql generate schema entities/*.yaml
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/**/*.sql

      - name: Generate tests
        run: specql generate tests entities/*.yaml

      - name: Run pgTAP tests
        run: specql test run --type pgtap entities/*.yaml

      - name: Run pytest tests
        run: |
          specql test run --type pytest entities/*.yaml --cov --cov-report xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Test Result Storage

```yaml
# Store test results as artifacts
- name: Upload test results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: |
      test-results/
      coverage.html
      performance-results.json

# Store test results in database
- name: Store test metrics
  run: |
    specql test results entities/*.yaml --json | \
    curl -X POST -H "Content-Type: application/json" \
         -d @- ${{ secrets.TEST_METRICS_API }}
```

## 🎯 Best Practices

### Test Execution
- **Run tests frequently** - After every change
- **Use appropriate test types** - pgTAP for logic, pytest for integration
- **Parallel execution** - Speed up test suites
- **Isolate test data** - Clean database state between tests

### Result Management
- **Store results** - Keep historical test data
- **Monitor trends** - Track performance and coverage over time
- **Set baselines** - Know your normal performance levels
- **Alert on failures** - Get notified of test failures

### Debugging
- **Verbose output** - Use --verbose for detailed information
- **Isolate failures** - Run individual failing tests
- **Check environment** - Verify database and system state
- **Use logging** - Enable debug logging when needed

### Performance
- **Set realistic targets** - Base requirements on user expectations
- **Monitor regressions** - Catch performance issues early
- **Profile bottlenecks** - Identify and optimize slow operations
- **Scale appropriately** - Use larger test data sets for production-like testing

## 🆘 Troubleshooting

### "Tests not running"
```bash
# Check test files exist
ls -la tests/

# Regenerate tests
specql generate tests entities/user.yaml --force

# Check database connection
psql $DATABASE_URL -c "SELECT 1;"

# Run with verbose output
specql test run entities/user.yaml --verbose
```

### "pgTAP tests failing"
```bash
# Check pgTAP installation
psql $DATABASE_URL -c "SELECT pgtap.version();"

# Run test manually
psql $DATABASE_URL -f tests/pgtap/user_test.sql

# Check test data
psql $DATABASE_URL -c "SELECT * FROM user LIMIT 5;"

# Enable query logging
psql $DATABASE_URL -c "SET log_statement = 'all';"
```

### "pytest tests failing"
```bash
# Check Python dependencies
pip list | grep pytest

# Run pytest directly
pytest tests/pytest/ -v

# Check database connection in tests
python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"

# Run with debug output
specql test run --type pytest entities/user.yaml --verbose
```

### "Performance tests slow"
```bash
# Reduce test iterations
specql test run --type performance entities/user.yaml --iterations 50

# Check system resources
top
free -h

# Profile database
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"

# Optimize queries
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM user WHERE status = 'active';"
```

### "Coverage reports empty"
```bash
# Run tests first
specql test run entities/user.yaml

# Check coverage data exists
ls -la .coverage*

# Generate coverage manually
coverage run -m pytest tests/pytest/
coverage html

# Check coverage configuration
coverage --rcfile=.coveragerc report
```

## 📊 Test Metrics

### Execution Metrics
- **Test execution time**: <5 minutes for full suite
- **Test success rate**: >99% in main branch
- **Parallel efficiency**: >80% CPU utilization
- **Resource usage**: <500MB memory per test run

### Quality Metrics
- **Code coverage**: >95% of generated code
- **Test count**: 10-20 tests per entity
- **Performance stability**: <5% variance between runs
- **Failure investigation time**: <10 minutes average

### Performance Metrics
- **pgTAP execution**: <1 minute for typical suite
- **pytest execution**: <3 minutes for typical suite
- **Performance tests**: <5 minutes for benchmarking
- **Coverage generation**: <30 seconds

## 🎉 Summary

The `specql test` commands provide:
- ✅ **Comprehensive testing** - pgTAP, pytest, and performance tests
- ✅ **Flexible execution** - Parallel, filtered, and configured runs
- ✅ **Rich reporting** - Coverage, results, and performance analysis
- ✅ **CI/CD integration** - Automated testing pipelines
- ✅ **Debugging support** - Verbose output and failure analysis
- ✅ **Performance monitoring** - Regression detection and profiling

## 🚀 What's Next?

- **[Generate Commands](generate.md)** - Schema and test generation
- **[Validate Commands](validate.md)** - YAML validation and checking
- **[Performance Commands](performance.md)** - Advanced benchmarking
- **[Workflows](workflows.md)** - Common development patterns

**Ready to run comprehensive tests? Let's explore more commands! 🚀**