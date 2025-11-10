# Performance Commands - Benchmarking and Optimization

The `specql test run --type performance` command executes performance tests, benchmarks database operations, and analyzes system performance. This guide covers performance testing, profiling, and optimization.

## 🎯 What You'll Learn

- Performance test execution and configuration
- Benchmarking database operations
- Performance profiling and analysis
- Optimization recommendations
- Performance regression detection
- Load testing and scalability analysis

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Performance tests generated](../guides/cli/generate.md)
- PostgreSQL database with realistic data
- Understanding of performance concepts

## 💡 Performance Testing Overview

### What Gets Measured

**SpecQL performance tests measure:**
- ✅ **Query Execution Time** - How fast SQL queries run
- ✅ **Function Performance** - Business logic operation speed
- ✅ **Scalability** - Performance under load
- ✅ **Resource Usage** - CPU, memory, I/O consumption
- ✅ **Concurrent Access** - Multi-user performance
- ✅ **Bottleneck Detection** - Identify slow operations

### Performance Test Types

| Test Type | Purpose | Example |
|-----------|---------|---------|
| **Micro-benchmarks** | Individual operations | Single user activation |
| **Macro-benchmarks** | End-to-end workflows | Complete order process |
| **Load Tests** | Concurrent users | 100 simultaneous operations |
| **Stress Tests** | System limits | Maximum throughput |
| **Regression Tests** | Performance stability | Compare against baseline |

## 🚀 Running Performance Tests

### Basic Performance Testing

```bash
# Run performance tests for an entity
specql test run --type performance entities/user.yaml

# Run performance tests for multiple entities
specql test run --type performance entities/user.yaml entities/order.yaml

# Run all performance tests
specql test run --type performance entities/*.yaml
```

### Performance Test Options

```bash
# Custom iterations
specql test run --type performance entities/user.yaml --iterations 1000

# Custom concurrency
specql test run --type performance entities/user.yaml --concurrency 10

# Custom timeout
specql test run --type performance entities/user.yaml --timeout 600

# Specific test pattern
specql test run --type performance entities/user.yaml --filter "*state_machine*"

# Verbose output
specql test run --type performance entities/user.yaml --verbose
```

## 📊 Performance Results

### Understanding Output

```bash
# Example performance test output
Performance Test Results for user
===================================

Test: user_activate
Iterations: 100
Concurrency: 1
Mean: 0.0234s
Median: 0.0218s
Min: 0.0189s
Max: 0.0456s
StdDev: 0.0056s
P95: 0.0321s
P99: 0.0412s

Test: bulk_user_update
Iterations: 10
Concurrency: 5
Mean: 0.4567s
Median: 0.4321s
Min: 0.3987s
Max: 0.5234s
StdDev: 0.0345s
P95: 0.5234s

Performance Requirements:
✅ user_activate: 0.0234s < 0.0500s (target)
✅ bulk_user_update: 0.4567s < 1.0000s (target)

Test Summary:
✅ All performance targets met
⏱️  Total execution time: 4.87 seconds
📊 Average throughput: 217 operations/second
```

### Performance Metrics Explained

| Metric | Meaning | Use Case |
|--------|---------|----------|
| **Mean** | Average execution time | General performance indicator |
| **Median** | Middle value (resistant to outliers) | Typical performance |
| **Min/Max** | Best/worst case | Performance variability |
| **StdDev** | Standard deviation | Performance consistency |
| **P95/P99** | 95th/99th percentile | Worst-case performance |
| **Throughput** | Operations per second | System capacity |

## 🔧 Performance Profiling

### Profile Specific Operations

```bash
# Profile a specific function
specql test profile entities/user.yaml --operation user_activate

# Profile query performance
specql test profile entities/user.yaml --query "SELECT * FROM user WHERE status = 'active'"

# Profile with custom data size
specql test profile entities/user.yaml --operation user_activate --data-size 10000
```

### Profiling Output

```bash
# Example profiling output
Profiling: user_activate
=======================

Execution Plan:
Seq Scan on user  (cost=0.00..15.00 rows=500 width=32)
  Filter: (status = 'active'::text)

Actual Execution:
  Buffers: shared hit=5
  I/O Timings: read=0.000 write=0.000
  Planning Time: 0.050 ms
  Execution Time: 0.234 ms

Optimization Recommendations:
✅ Index exists: idx_user_status
✅ Query uses index
⚠️  Consider partial index for active users only

Performance Breakdown:
  • Planning: 0.050ms (18%)
  • Execution: 0.234ms (82%)
  • I/O: 0.000ms (0%)
```

### System Resource Profiling

```bash
# Profile system resources
specql test run --type performance entities/user.yaml --system-profile

# Example system profiling
System Resource Usage:
======================

CPU Usage:
  • User CPU: 45.2%
  • System CPU: 12.8%
  • Idle CPU: 42.0%

Memory Usage:
  • PostgreSQL: 256MB
  • Total System: 2.1GB
  • Available: 1.2GB

Disk I/O:
  • Read: 45MB/s
  • Write: 12MB/s
  • IOPS: 1250

Network:
  • Receive: 5MB/s
  • Transmit: 2MB/s
```

## 📈 Performance Analysis

### Compare Against Baselines

```bash
# Compare with baseline
specql test run --type performance entities/user.yaml --baseline baseline.json

# Example comparison output
Performance Comparison
======================

Test: user_activate
Baseline (v1.0): 0.0215s mean
Current: 0.0234s mean
Change: +8.8% (regression)
Status: ⚠️  Exceeds tolerance (5%)

Test: bulk_user_update
Baseline (v1.0): 0.4231s mean
Current: 0.4567s mean
Change: +8.0% (regression)
Status: ⚠️  Exceeds tolerance (5%)

Summary:
⚠️  2 performance regressions detected
🔴 Overall status: FAILED
```

### Trend Analysis

```bash
# Analyze performance trends
specql test trends entities/user.yaml --days 30

# Example trend output
Performance Trends (Last 30 Days)
=================================

user_activate:
  • Day 1: 0.0215s
  • Day 15: 0.0221s (+2.8%)
  • Day 30: 0.0234s (+8.8%)
  • Trend: 📈 Increasing (0.0006s/day)

bulk_user_update:
  • Day 1: 0.4231s
  • Day 15: 0.4456s (+5.3%)
  • Day 30: 0.4567s (+8.0%)
  • Trend: 📈 Increasing (0.0112s/day)

Recommendations:
⚠️  Monitor user_activate for continued degradation
🔴 Investigate bulk_user_update performance regression
```

### Performance Health Score

```bash
# Calculate performance health
specql test health entities/user.yaml

# Example health score
Performance Health Score: 7.2/10
==============================

Components:
  ✅ Speed: 8.5/10 (Good execution times)
  ⚠️  Stability: 6.8/10 (Some variance detected)
  ✅ Scalability: 8.2/10 (Good concurrent performance)
  🔴 Regression: 5.1/10 (Performance degradation detected)

Recommendations:
  • Investigate variance in test results
  • Address performance regression in bulk operations
  • Consider optimizing database configuration
```

## 🔧 Performance Optimization

### Database Optimization

```bash
# Analyze slow queries
specql test analyze entities/user.yaml --slow-queries

# Example analysis output
Slow Query Analysis
===================

Query: SELECT * FROM user WHERE status = 'active'
Executions: 1250
Total Time: 45.67s
Mean Time: 0.0365s
Slowest: 0.0892s

Optimization Recommendations:
1. ✅ Index exists: CREATE INDEX idx_user_status ON user(status)
2. ⚠️  Consider partial index: CREATE INDEX idx_user_active ON user(id) WHERE status = 'active'
3. 🔴 Add covering index: CREATE INDEX idx_user_status_covering ON user(status, id, email)

Potential Improvement: 65% faster execution
```

### Index Optimization

```bash
# Check index usage
specql test index-analysis entities/user.yaml

# Example index analysis
Index Usage Analysis
====================

Table: user
Indexes:
  • idx_user_email: 95% usage (excellent)
  • idx_user_status: 87% usage (good)
  • idx_user_created_at: 23% usage (low)

Recommendations:
  ✅ Keep idx_user_email (high usage)
  ✅ Keep idx_user_status (good usage)
  ⚠️  Consider dropping idx_user_created_at (low usage)
  🔴 Add idx_user_status_email (frequent combination)
```

### Configuration Tuning

```bash
# Database configuration recommendations
specql test config-recommendations entities/user.yaml

# Example recommendations
Database Configuration Recommendations
=====================================

Current Settings:
  shared_buffers: 128MB
  work_mem: 4MB
  maintenance_work_mem: 64MB

Recommended Settings:
  shared_buffers: 256MB (+100% - better caching)
  work_mem: 16MB (+300% - complex queries)
  maintenance_work_mem: 128MB (+100% - index creation)

Estimated Impact:
  • Query performance: +25% improvement
  • Index creation: +50% faster
  • Memory usage: +150MB additional
```

### Query Optimization

```bash
# Optimize generated queries
specql test query-optimization entities/user.yaml

# Example optimization
Query Optimization Results
==========================

Original Query:
SELECT * FROM user WHERE status = 'active' AND created_at > $1

Optimized Query:
SELECT id, email, status, created_at FROM user
WHERE status = 'active' AND created_at > $1
ORDER BY created_at DESC

Optimizations Applied:
  ✅ Column selection (avoid SELECT *)
  ✅ Index-friendly ordering
  ⚠️  Consider query result limits

Performance Impact:
  • Execution time: -40% (0.036s → 0.022s)
  • Data transfer: -60% (less columns)
  • Memory usage: -30% (smaller result set)
```

## 📊 Load Testing

### Concurrent User Testing

```bash
# Test with concurrent users
specql test run --type performance entities/user.yaml --concurrency 50

# Example concurrent test output
Concurrent Load Test Results
============================

Concurrency Level: 50
Total Requests: 1000
Total Time: 12.34s

Response Time Statistics:
  • Mean: 0.617s
  • Median: 0.589s
  • P95: 1.234s
  • P99: 2.456s

Requests per Second: 81.0
Transfer Rate: 45.6KB/s

Error Rate: 0.5%

Bottlenecks Identified:
  ⚠️  Connection pool exhausted at 30 concurrent users
  🔴 Lock contention on user table updates
```

### Scalability Testing

```bash
# Test scalability
specql test scalability entities/user.yaml --max-concurrency 100

# Example scalability output
Scalability Test Results
========================

Concurrency Scaling:
  • 1 user: 0.023s mean response time
  • 10 users: 0.056s mean response time (+143%)
  • 25 users: 0.145s mean response time (+530%)
  • 50 users: 0.423s mean response time (+1739%)
  • 100 users: 1.234s mean response time (+5252%)

Breaking Points:
  🔴 50+ users: Connection pool exhausted
  🔴 25+ users: Lock contention increases
  ⚠️  10+ users: Response time degradation

Recommendations:
  • Increase connection pool size to 100
  • Implement optimistic locking
  • Consider read replicas for queries
  • Add database indexes for contended columns
```

### Stress Testing

```bash
# Stress test system limits
specql test stress entities/user.yaml --duration 300 --max-concurrency 200

# Example stress test output
Stress Test Results (5 minutes)
==============================

Peak Concurrency: 150 users
Total Requests: 45,231
Successful Requests: 44,876 (99.2%)
Failed Requests: 355 (0.8%)

Response Time Degradation:
  • Start: 0.023s mean
  • Peak: 2.456s mean (+10,600%)
  • End: 1.234s mean (+5,252%)

System Resources:
  • CPU: 95% utilization
  • Memory: 1.8GB used
  • Disk I/O: 85% utilization
  • Network: 45MB/s throughput

Failure Analysis:
  • Timeout errors: 45%
  • Connection errors: 35%
  • Database locks: 20%

Recommendations:
  • System can handle ~100 concurrent users reliably
  • Implement circuit breaker for overload protection
  • Add auto-scaling based on response time
  • Optimize database connection pooling
```

## 🔧 Custom Performance Tests

### Performance Test Configuration

```yaml
# In entity YAML
name: user
# ... fields and patterns ...

test_config:
  performance:
    # Test settings
    enabled: true
    iterations: 1000
    concurrency: 10
    timeout: "5 minutes"

    # Custom test data
    fixtures:
      - name: performance_users
        count: 10000
        template:
          email: "perf_user_{index}@example.com"
          status: "active"

    # Performance requirements
    requirements:
      - operation: user_activate
        target_p95: 200ms
        target_mean: 100ms
        max_error_rate: 0.01

      - operation: user_bulk_update
        target_p95: 2000ms
        target_mean: 1000ms

    # Custom performance tests
    custom_tests:
      - name: complex_user_workflow
        description: "Test complete user lifecycle"
        sql: |
          SELECT complex_user_workflow_test($1, $2, $3)
        parameters: [100, "'new_status'", "'2024-01-01'"]

    # Monitoring
    metrics:
      - query_execution_time
      - memory_usage
      - lock_wait_time
      - connection_count
```

### Custom Performance Assertions

```sql
-- Custom performance test function
CREATE OR REPLACE FUNCTION complex_user_workflow_test(
  user_count INTEGER,
  new_status TEXT,
  date_filter DATE
)
RETURNS TABLE(
  test_name TEXT,
  execution_time INTERVAL,
  records_processed INTEGER,
  avg_response_time INTERVAL
) AS $$
DECLARE
  start_time TIMESTAMP;
  end_time TIMESTAMP;
  processed_count INTEGER := 0;
  total_response_time INTERVAL := '0 seconds';
BEGIN
  -- Setup test data
  INSERT INTO user (id, email, status, created_at)
  SELECT
    gen_random_uuid(),
    'test_' || i || '@example.com',
    'pending',
    NOW() - (random() * interval '365 days')
  FROM generate_series(1, user_count) i;

  -- Execute complex workflow
  start_time := clock_timestamp();

  -- Step 1: Filter users by date
  CREATE TEMP TABLE temp_users AS
  SELECT id FROM user
  WHERE created_at >= date_filter
  AND status = 'pending';

  -- Step 2: Bulk update status
  UPDATE user
  SET status = new_status,
      updated_at = NOW()
  WHERE id IN (SELECT id FROM temp_users);

  GET DIAGNOSTICS processed_count = ROW_COUNT;

  -- Step 3: Calculate response times
  SELECT SUM(NOW() - updated_at)
  INTO total_response_time
  FROM user
  WHERE id IN (SELECT id FROM temp_users);

  end_time := clock_timestamp();

  -- Return results
  test_name := 'complex_user_workflow';
  execution_time := end_time - start_time;
  avg_response_time := total_response_time / processed_count;

  RETURN NEXT;

  -- Cleanup
  DROP TABLE temp_users;
  DELETE FROM user WHERE email LIKE 'test_%@example.com';
END;
$$ LANGUAGE plpgsql;
```

## 🔄 CI/CD Performance Integration

### Performance Regression Pipeline

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  schedule:
    # Daily performance check
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  performance:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres

    steps:
      - uses: actions/checkout@v4

      - name: Setup database
        run: |
          specql generate schema entities/*.yaml
          # Load performance test data
          ./scripts/load_performance_data.sh

      - name: Run performance tests
        run: |
          specql test run --type performance entities/*.yaml \
            --report performance-report.html \
            --baseline .github/performance-baseline.json

      - name: Check regression
        run: |
          python scripts/check_performance_regression.py \
            --baseline .github/performance-baseline.json \
            --current performance-results.json \
            --max-degradation 0.1

      - name: Update baseline
        if: github.ref == 'refs/heads/main' && github.event_name == 'schedule'
        run: |
          cp performance-results.json .github/performance-baseline.json
          git add .github/performance-baseline.json
          git commit -m "Update performance baseline [automated]"
          git push

      - name: Alert on regression
        if: failure()
        run: |
          curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚨 Performance regression detected!"}' \
            ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Performance Dashboard

```bash
# Generate performance dashboard
specql test dashboard entities/*.yaml --output performance-dashboard.html

# Dashboard includes:
# - Performance trends over time
# - Regression alerts
# - Bottleneck analysis
# - Optimization recommendations
# - System resource usage
```

## 🎯 Best Practices

### Test Design
- **Use realistic data** - Test with production-scale data volumes
- **Set meaningful targets** - Base requirements on user expectations
- **Test complete workflows** - Not just individual operations
- **Include edge cases** - Test boundary conditions and error scenarios

### Execution
- **Run regularly** - Include in CI/CD pipelines
- **Monitor trends** - Track performance over time
- **Establish baselines** - Know your normal performance levels
- **Alert on regressions** - Catch performance issues early

### Analysis
- **Focus on percentiles** - P95/P99 for user experience
- **Consider variance** - Account for performance variability
- **Profile bottlenecks** - Identify root causes of slow performance
- **Compare environments** - Test in staging before production

### Optimization
- **Measure impact** - Quantify improvement from changes
- **Start with biggest wins** - Optimize most impactful operations first
- **Avoid premature optimization** - Focus on actual bottlenecks
- **Test after changes** - Verify optimizations work and don't break functionality

## 🆘 Troubleshooting

### "Performance tests are too slow"
```bash
# Reduce iterations
specql test run --type performance entities/user.yaml --iterations 100

# Use smaller data sets
specql generate tests --type performance entities/user.yaml --data-size 1000

# Run specific tests
specql test run --type performance entities/user.yaml --filter "*fast_test*"

# Increase timeout
specql test run --type performance entities/user.yaml --timeout 1800
```

### "Inconsistent results"
```bash
# Stabilize test environment
# - Use dedicated test database
# - Pre-warm database caches
# - Control system load
# - Use fixed test data sets

# Check system resources
top
iostat -x 1
free -h

# Profile database
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"
```

### "Performance regressions not detected"
```bash
# Check baseline accuracy
cat baseline-performance.json

# Verify test conditions match
# - Same data volumes
# - Same PostgreSQL version
# - Same system configuration

# Adjust sensitivity
specql test run --type performance entities/user.yaml --regression-threshold 0.05

# Use statistical analysis
specql test run --type performance entities/user.yaml --statistical-analysis
```

### "System becomes unresponsive"
```bash
# Reduce concurrency
specql test run --type performance entities/user.yaml --concurrency 5

# Add delays between tests
specql test run --type performance entities/user.yaml --delay 0.1

# Monitor resources
# - CPU usage
# - Memory usage
# - Disk I/O
# - Network I/O

# Check database configuration
psql $DATABASE_URL -c "SHOW max_connections;"
psql $DATABASE_URL -c "SHOW shared_buffers;"
```

## 📊 Performance Metrics

### Execution Metrics
- **Test completion time**: <10 minutes for typical suite
- **Result consistency**: <5% variance between runs
- **Resource usage**: <70% of system capacity
- **Error rate**: <1% under normal load

### Quality Metrics
- **Regression detection**: >95% accuracy
- **Bottleneck identification**: >90% of major issues found
- **Optimization impact**: >80% of recommendations implemented
- **Performance stability**: <10% degradation over time

### Business Impact
- **User experience**: P95 response times meet SLAs
- **System capacity**: Known limits and scaling points
- **Development velocity**: Performance issues caught early
- **Operational efficiency**: Data-driven optimization decisions

## 🎉 Summary

The performance testing commands provide:
- ✅ **Comprehensive benchmarking** - Query, function, and system performance
- ✅ **Regression detection** - Catch performance issues before production
- ✅ **Profiling and analysis** - Identify bottlenecks and optimization opportunities
- ✅ **Load and stress testing** - Understand system limits and scalability
- ✅ **CI/CD integration** - Automated performance monitoring
- ✅ **Optimization recommendations** - Data-driven improvement suggestions

## 🚀 What's Next?

- **[Generate Commands](generate.md)** - Schema and test generation
- **[Validate Commands](validate.md)** - YAML validation and checking
- **[Test Commands](test.md)** - Running and managing tests
- **[Workflows](workflows.md)** - Common development patterns

**Ready to optimize your application performance? Let's explore more commands! 🚀**