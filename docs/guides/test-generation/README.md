# Test Generation

SpecQL automatically generates comprehensive tests for your entities and patterns. Get instant test coverage for business logic, data validation, state machines, and performance - without writing a single test manually.

## 🎯 What Is Automatic Test Generation?

**SpecQL generates three types of tests from your YAML specifications:**

### 1. **pgTAP Tests** - Database-Level Testing
- ✅ **Native PostgreSQL** - Run directly in the database
- ✅ **Business Logic** - Test patterns, constraints, functions
- ✅ **Fast Execution** - No external dependencies
- ✅ **Comprehensive Coverage** - All edge cases and error conditions

### 2. **pytest Tests** - Application-Level Testing
- ✅ **Python Integration** - Test from your application code
- ✅ **API Testing** - Validate generated functions
- ✅ **Data Consistency** - Cross-table relationship testing
- ✅ **CI/CD Ready** - Standard Python test framework

### 3. **Performance Tests** - Benchmarking & Optimization
- ✅ **Query Performance** - Measure SQL execution time
- ✅ **Scalability Testing** - Load testing with multiple users
- ✅ **Pattern Efficiency** - Compare different implementations
- ✅ **Bottleneck Detection** - Identify slow operations

## 💡 Why Automatic Testing?

| Traditional Testing | SpecQL Test Generation |
|---------------------|------------------------|
| **Manual coding** - Write every test | **Zero coding** - Tests from YAML |
| **Incomplete coverage** - Miss edge cases | **100% coverage** - All scenarios |
| **Maintenance burden** - Update when code changes | **Auto-sync** - Tests update with specs |
| **Slow feedback** - Hours to write tests | **Instant coverage** - Tests in seconds |
| **Error-prone** - Human mistakes | **Consistent** - Generated reliably |

## 🚀 Quick Start

### Generate Tests in 3 Steps

```bash
# 1. Create your entity with patterns
# (entities/user.yaml with state_machine pattern)

# 2. Generate all test types
specql generate tests entities/user.yaml

# 3. Run tests
specql test run entities/user.yaml
```

**That's it!** You now have comprehensive test coverage.

## 📊 Generated Test Coverage

### State Machine Tests
```sql
-- pgTAP test example
SELECT ok(
    user_request_verification('test-user-id') IS NOT NULL,
    'Can request verification from inactive state'
);

SELECT ok(
    (SELECT status FROM user WHERE id = 'test-user-id') = 'pending_verification',
    'State changed correctly'
);
```

### Validation Tests
```python
# pytest test example
def test_email_validation():
    # Test valid email
    result = validate_user_email("user@example.com")
    assert result.is_valid == True

    # Test invalid email
    result = validate_user_email("invalid-email")
    assert result.is_valid == False
    assert "Invalid email format" in result.errors
```

### Performance Tests
```python
# Performance benchmark
def test_state_machine_performance(benchmark):
    users = create_test_users(1000)

    # Benchmark bulk state transitions
    result = benchmark(
        lambda: bulk_update_user_status(users, 'active')
    )

    assert result.execution_time < 5.0  # seconds
```

## 📖 Test Generation Guides

### Getting Started
- **[Getting Started](getting-started.md)** - Test generation basics and workflow
- **[pgTAP Tests](pgtap-tests.md)** - PostgreSQL native testing
- **[pytest Tests](pytest-tests.md)** - Python integration testing

### Advanced Testing
- **[Performance Tests](performance-tests.md)** - Benchmarking and optimization
- **[CI/CD Integration](ci-cd-integration.md)** - Automated testing pipelines

## 🎯 Test Categories

### Business Logic Tests
- **Pattern Validation** - State machines, validation rules, multi-entity operations
- **Function Testing** - Generated database functions
- **Constraint Testing** - Data integrity rules
- **Trigger Testing** - Automatic actions and validations

### Data Integrity Tests
- **Relationship Testing** - Foreign key constraints
- **Uniqueness Testing** - Unique constraints and indexes
- **Type Validation** - Data type constraints
- **Range Testing** - Numeric and date range validations

### Integration Tests
- **Cross-Entity Testing** - Multi-table operations
- **API Testing** - Generated function interfaces
- **Workflow Testing** - End-to-end business processes
- **Error Handling** - Exception and rollback scenarios

### Performance Tests
- **Query Optimization** - SQL execution time
- **Scalability Testing** - Concurrent user load
- **Memory Usage** - Resource consumption
- **Bottleneck Analysis** - Performance profiling

## 🔧 Test Configuration

### Basic Configuration

```yaml
# In your entity YAML
name: user
fields:
  id: uuid
  email: string
  status: string

patterns:
  - name: state_machine
    # ... pattern config

# Test configuration (optional)
test_config:
  enabled: true
  types: [pgtap, pytest, performance]
  data_sets:
    - name: basic_user
      email: "test@example.com"
      status: "active"
    - name: edge_cases
      email: ""  # Empty email
      status: "invalid_status"
```

### Advanced Test Settings

```yaml
test_config:
  # Test types to generate
  types: [pgtap, pytest]

  # Test data generation
  fixtures:
    - name: test_users
      count: 100
      template:
        email: "user_{index}@example.com"
        status: "active"

  # Performance test settings
  performance:
    enabled: true
    iterations: 1000
    concurrency: 10
    timeout: "30 seconds"

  # Coverage requirements
  coverage:
    minimum: 95
    exclude_patterns: ["debug_*", "temp_*"]
```

## 📈 Test Metrics & Reporting

### Coverage Reports

```bash
# Generate coverage report
specql test coverage entities/user.yaml

# Output formats
specql test coverage entities/user.yaml --format html --output coverage.html
specql test coverage entities/user.yaml --format json --output coverage.json
```

### Performance Reports

```bash
# Run performance tests
specql test run --type performance entities/user.yaml

# Generate performance report
specql test performance-report entities/user.yaml --output performance.html
```

### Test Results

```bash
# Detailed test output
specql test run entities/user.yaml --verbose

# JUnit XML for CI/CD
specql test run entities/user.yaml --junit-xml results.xml

# Summary report
specql test run entities/user.yaml --summary
```

## 🚀 Common Workflows

### Development Workflow

```bash
# 1. Write YAML specification
vim entities/user.yaml

# 2. Generate schema
specql generate schema entities/user.yaml

# 3. Generate tests
specql generate tests entities/user.yaml

# 4. Run tests
specql test run entities/user.yaml

# 5. Check coverage
specql test coverage entities/user.yaml
```

### CI/CD Pipeline

```yaml
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

      - name: Generate Tests
        run: specql generate tests entities/*.yaml

      - name: Run pgTAP Tests
        run: specql test run --type pgtap entities/*.yaml

      - name: Run pytest Tests
        run: specql test run --type pytest entities/*.yaml

      - name: Performance Tests
        run: specql test run --type performance entities/*.yaml

      - name: Coverage Report
        run: specql test coverage entities/*.yaml --format html
```

### Debugging Failed Tests

```bash
# Run with verbose output
specql test run entities/user.yaml --verbose

# Run specific test
specql test run entities/user.yaml --filter "test_state_machine"

# Debug database state
psql $DATABASE_URL -c "SELECT * FROM user LIMIT 5;"

# Check test logs
cat logs/test_execution.log
```

## 🎯 Best Practices

### Test Design
- **Test early, test often** - Generate tests immediately after creating entities
- **Use realistic data** - Test with production-like data sets
- **Cover edge cases** - Include boundary conditions and error scenarios
- **Maintain test data** - Keep test fixtures up to date

### Performance Testing
- **Set realistic targets** - Define acceptable performance thresholds
- **Test at scale** - Use data volumes similar to production
- **Monitor trends** - Track performance over time
- **Profile bottlenecks** - Identify and optimize slow operations

### CI/CD Integration
- **Fast feedback** - Run critical tests on every commit
- **Parallel execution** - Split test suites across multiple runners
- **Quality gates** - Block deployments on test failures
- **Artifact storage** - Save test reports and coverage data

### Maintenance
- **Regenerate regularly** - Keep tests in sync with schema changes
- **Review failures** - Understand why tests fail and fix root causes
- **Update expectations** - Modify tests when business logic changes intentionally
- **Archive old tests** - Clean up obsolete test cases

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
# Install pgTAP extension
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

# Check database connection
psql $DATABASE_URL -c "SELECT 1;"

# Run tests manually
psql $DATABASE_URL -f tests/pgtap/user_test.sql
```

### "pytest tests failing"
```bash
# Install dependencies
pip install pytest psycopg2-binary

# Check Python path
python -c "import specql"

# Run tests directly
pytest tests/pytest/ -v
```

### "Performance tests slow"
```bash
# Reduce test data size
specql generate tests entities/user.yaml --performance-data-size 100

# Increase timeouts
specql test run --type performance entities/user.yaml --timeout 300

# Profile specific operations
specql test profile entities/user.yaml --operation state_machine
```

## 📊 Success Metrics

### Coverage Goals
- **Line Coverage**: >95% of generated code
- **Branch Coverage**: >90% of conditional logic
- **Pattern Coverage**: 100% of declared patterns
- **Edge Case Coverage**: All boundary conditions

### Performance Targets
- **Test Execution**: <5 minutes for full suite
- **pgTAP Tests**: <1 minute execution time
- **pytest Tests**: <2 minutes execution time
- **Performance Tests**: <10 minutes benchmarking

### Quality Gates
- **Zero failing tests** in main branch
- **No performance regressions** >10%
- **All patterns tested** before deployment
- **Test coverage maintained** across releases

## 🎉 Summary

SpecQL's automatic test generation provides:
- ✅ **Zero-effort testing** - Tests from YAML specifications
- ✅ **Comprehensive coverage** - All business logic and edge cases
- ✅ **Multiple test types** - pgTAP, pytest, and performance tests
- ✅ **CI/CD integration** - Automated testing pipelines
- ✅ **Performance monitoring** - Benchmarking and optimization

## 🚀 What's Next?

- **[Getting Started](getting-started.md)** - Learn test generation basics
- **[pgTAP Tests](pgtap-tests.md)** - PostgreSQL native testing
- **[pytest Tests](pytest-tests.md)** - Python integration testing
- **[CI/CD Integration](ci-cd-integration.md)** - Production pipelines

**Ready to achieve 100% test coverage instantly? Let's dive in! 🚀**