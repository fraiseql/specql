# Performance Tests - Benchmarking & Optimization

SpecQL generates performance tests to benchmark your database operations, measure query execution times, and ensure your application meets performance requirements. Identify bottlenecks, optimize slow queries, and maintain performance standards.

## 🎯 What You'll Learn

- Performance testing fundamentals
- Generate and run performance benchmarks
- Analyze performance results
- Optimize slow operations
- Set performance standards

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Entity with patterns created](../getting-started/first-entity.md)
- PostgreSQL database with data
- Understanding of performance concepts

## 💡 Performance Testing Concepts

### What Are Performance Tests?

**Performance tests** measure how fast your SpecQL-generated code executes:

```yaml
# Performance test configuration
performance:
  enabled: true
  iterations: 1000
  concurrency: 10
  timeout: "30 seconds"
  metrics:
    - query_execution_time
    - memory_usage
    - connection_pool_utilization
```

**Key Metrics:**
- ✅ **Query Execution Time** - How fast SQL queries run
- ✅ **Throughput** - Operations per second
- ✅ **Latency** - Response time distribution
- ✅ **Resource Usage** - CPU, memory, I/O
- ✅ **Scalability** - Performance under load

### Why Performance Testing?

| Benefit | Description | Example |
|---------|-------------|---------|
| **Early Detection** | Catch performance issues before production | Query taking 5 seconds instead of 50ms |
| **Capacity Planning** | Understand system limits | Support 1000 concurrent users |
| **Optimization** | Identify bottlenecks | Missing index causing slow queries |
| **Regression Prevention** | Ensure changes don't break performance | New feature doesn't slow down existing operations |
| **SLA Compliance** | Meet performance requirements | API responses under 200ms |

## 🚀 Step 1: Generate Performance Tests

### Create Test Entity with Data

```yaml
# entities/order.yaml
name: order
fields:
  id: uuid
  customer_id: uuid
  status: string
  total_amount: decimal
  created_at: timestamp
  updated_at: timestamp

patterns:
  - name: state_machine
    description: "Order processing workflow"
    initial_state: pending
    states: [pending, confirmed, shipped, delivered]
    transitions:
      - from: pending
        to: confirmed
        trigger: confirm
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
```

### Generate Performance Tests

```bash
# Generate performance tests
specql generate tests --type performance entities/order.yaml

# Check generated files
ls -la tests/performance/
# order_state_machine_performance.sql
# order_validation_performance.sql
# order_benchmark.py
```

### Generated Performance Tests

```sql
-- tests/performance/order_state_machine_performance.sql
-- Performance tests for order state machine

-- Setup test data (1000 orders)
INSERT INTO order (id, customer_id, status, total_amount, created_at)
SELECT
    gen_random_uuid(),
    (SELECT id FROM customer ORDER BY random() LIMIT 1),
    'pending',
    (random() * 1000 + 10)::decimal(10,2),
    NOW() - (random() * interval '365 days')
FROM generate_series(1, 1000);

-- Benchmark 1: Single order confirmation
SELECT * FROM benchmark(
    'single_order_confirm',
    $$
    SELECT order_confirm(order_id) FROM (
        SELECT id as order_id FROM order WHERE status = 'pending' LIMIT 1
    ) q
    $$,
    100  -- iterations
);

-- Benchmark 2: Bulk order confirmation
SELECT * FROM benchmark(
    'bulk_order_confirm',
    $$
    SELECT count(*) FROM (
        SELECT order_confirm(id)
        FROM order
        WHERE status = 'pending'
        LIMIT 100
    ) confirmed
    $$,
    10  -- iterations
);

-- Benchmark 3: Order status query performance
SELECT * FROM benchmark(
    'order_status_query',
    $$
    SELECT count(*) FROM order WHERE status = 'pending'
    $$,
    1000  -- iterations
);

-- Benchmark 4: Complex order search
SELECT * FROM benchmark(
    'complex_order_search',
    $$
    SELECT count(*) FROM order
    WHERE status = 'confirmed'
      AND total_amount > 100
      AND created_at > NOW() - interval '30 days'
    $$,
    500  -- iterations
);

-- Cleanup
DELETE FROM order WHERE created_at > NOW() - interval '1 hour';
```

```python
# tests/performance/order_benchmark.py
import time
import psycopg2
import statistics
from concurrent.futures import ThreadPoolExecutor

def benchmark_operation(name, operation_func, iterations=100):
    """Generic benchmarking function"""
    times = []

    for i in range(iterations):
        start_time = time.perf_counter()
        operation_func()
        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return {
        'name': name,
        'iterations': iterations,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0
    }

def test_order_state_machine_performance():
    """Performance test for order state machine"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()

    # Setup test data
    cursor.execute("""
        INSERT INTO order (id, customer_id, status, total_amount)
        SELECT
            gen_random_uuid(),
            'test-customer-id',
            'pending',
            100.00
        FROM generate_series(1, 100)
    """)
    conn.commit()

    # Benchmark single confirmations
    def single_confirmation():
        cursor.execute("""
            SELECT order_confirm(id) FROM order
            WHERE status = 'pending' LIMIT 1
        """)
        conn.commit()

    result = benchmark_operation(
        'single_order_confirmation',
        single_confirmation,
        iterations=100
    )

    print(f"Single confirmation: {result['mean']:.4f}s average")

    # Benchmark bulk operations
    def bulk_confirmation():
        cursor.execute("""
            SELECT count(*) FROM (
                SELECT order_confirm(id)
                FROM order
                WHERE status = 'pending'
                LIMIT 10
            ) q
        """)
        conn.commit()

    result = benchmark_operation(
        'bulk_order_confirmation',
        bulk_confirmation,
        iterations=50
    )

    print(f"Bulk confirmation (10): {result['mean']:.4f}s average")

    # Cleanup
    cursor.execute("DELETE FROM order WHERE customer_id = 'test-customer-id'")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    test_order_state_machine_performance()
```

## 🏃 Step 2: Run Performance Tests

### Basic Performance Testing

```bash
# Run performance tests
specql test run --type performance entities/order.yaml

# Expected output:
# Performance Test Results for order
# ===================================
#
# Test: single_order_confirm
# Iterations: 100
# Mean: 0.0234s
# Median: 0.0218s
# Min: 0.0189s
# Max: 0.0456s
# StdDev: 0.0056s
#
# Test: bulk_order_confirm
# Iterations: 10
# Mean: 0.4567s
# Median: 0.4321s
# Min: 0.3987s
# Max: 0.5234s
# StdDev: 0.0345s
#
# Performance Requirements:
# ✅ single_order_confirm: 0.0234s < 0.0500s (target)
# ✅ bulk_order_confirm: 0.4567s < 1.0000s (target)
```

### Advanced Performance Options

```bash
# Run with custom iterations
specql test run --type performance entities/order.yaml --iterations 500

# Run with concurrency
specql test run --type performance entities/order.yaml --concurrency 5

# Run specific performance test
specql test run --type performance entities/order.yaml --filter "*state_machine*"

# Generate detailed report
specql test run --type performance entities/order.yaml --report detailed.html

# Compare against baseline
specql test run --type performance entities/order.yaml --baseline baseline.json
```

### Manual Performance Testing

```bash
# Run Python performance tests
python tests/performance/order_benchmark.py

# Run SQL performance tests
psql $DATABASE_URL -f tests/performance/order_state_machine_performance.sql

# Profile specific queries
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM order WHERE status = 'pending' LIMIT 100;"
```

## 📊 Step 3: Analyze Performance Results

### Understanding Metrics

```json
{
  "test_name": "single_order_confirm",
  "iterations": 100,
  "metrics": {
    "mean": 0.0234,
    "median": 0.0218,
    "min": 0.0189,
    "max": 0.0456,
    "stdev": 0.0056,
    "p95": 0.0321,
    "p99": 0.0412
  },
  "requirements": {
    "target_mean": 0.0500,
    "max_p95": 0.1000,
    "status": "PASS"
  }
}
```

### Performance Analysis

```python
# Analyze performance distribution
def analyze_performance_results(results):
    """Analyze performance test results"""

    # Check for performance regressions
    if results['mean'] > results['requirements']['target_mean']:
        print(f"⚠️  Performance regression: {results['mean']:.4f}s > {results['requirements']['target_mean']:.4f}s")

    # Check for outliers
    if results['max'] > results['p95'] * 2:
        print(f"⚠️  Performance outliers detected: max {results['max']:.4f}s vs p95 {results['p95']:.4f}s")

    # Check stability
    if results['stdev'] / results['mean'] > 0.5:
        print(f"⚠️  Unstable performance: coefficient of variation {results['stdev']/results['mean']:.2f}")

    # Performance health score
    health_score = calculate_performance_health(results)
    if health_score < 0.8:
        print(f"🔴 Poor performance health: {health_score:.2f}")
    elif health_score < 0.9:
        print(f"🟡 Acceptable performance health: {health_score:.2f}")
    else:
        print(f"🟢 Good performance health: {health_score:.2f}")

def calculate_performance_health(results):
    """Calculate performance health score (0-1)"""
    score = 1.0

    # Penalize for exceeding targets
    if results['mean'] > results['requirements']['target_mean']:
        excess = results['mean'] / results['requirements']['target_mean'] - 1
        score -= min(excess, 0.5)  # Max penalty 0.5

    # Penalize for high variability
    cv = results['stdev'] / results['mean']
    if cv > 0.3:
        score -= min(cv - 0.3, 0.2)  # Max penalty 0.2

    # Penalize for outliers
    outlier_ratio = results['max'] / results['p95']
    if outlier_ratio > 1.5:
        score -= min(outlier_ratio - 1.5, 0.3)  # Max penalty 0.3

    return max(0, score)
```

### Performance Baselines

```json
// performance-baseline.json
{
  "version": "1.0",
  "timestamp": "2024-01-15T10:00:00Z",
  "environment": "production-like",
  "baselines": {
    "single_order_confirm": {
      "mean": 0.0234,
      "p95": 0.0321,
      "tolerance": 0.1  // 10% tolerance for changes
    },
    "bulk_order_confirm": {
      "mean": 0.4567,
      "p95": 0.5234,
      "tolerance": 0.15
    }
  }
}
```

## 🔧 Step 4: Optimize Performance Issues

### Query Optimization

```sql
-- Before: Slow query
SELECT * FROM order
WHERE status = 'pending'
  AND created_at > NOW() - interval '30 days'
ORDER BY created_at DESC;

-- After: Optimized query
SELECT o.id, o.customer_id, o.total_amount, o.created_at
FROM order o
WHERE o.status = 'pending'
  AND o.created_at > NOW() - interval '30 days'
ORDER BY o.created_at DESC;

-- Add composite index
CREATE INDEX idx_order_status_created ON order(status, created_at DESC)
WHERE status IN ('pending', 'confirmed');
```

### Index Optimization

```sql
-- Analyze slow queries
EXPLAIN ANALYZE
SELECT * FROM order
WHERE customer_id = 'customer-123'
  AND status = 'confirmed';

-- Add missing indexes
CREATE INDEX idx_order_customer_status ON order(customer_id, status);
CREATE INDEX idx_order_total_amount ON order(total_amount) WHERE total_amount > 100;

-- Check index usage
SELECT
    schemaname, tablename, indexname,
    idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'order'
ORDER BY idx_scan DESC;
```

### Connection Pooling

```python
# Use connection pooling for better performance
from psycopg2.pool import ThreadedConnectionPool

# Create connection pool
pool = ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    host="localhost",
    database="specql_db",
    user="specql_user",
    password="password"
)

def get_connection():
    return pool.getconn()

def release_connection(conn):
    pool.putconn(conn)
```

### Query Result Caching

```python
# Cache expensive queries
from functools import lru_cache
import time

@lru_cache(maxsize=1000)
def get_customer_order_count(customer_id: str, status: str = None) -> int:
    """Cached function for customer order counts"""
    cache_key = f"{customer_id}:{status}:{int(time.time() // 300)}"  # 5-minute cache

    # Check Redis cache first
    cached_result = redis.get(cache_key)
    if cached_result:
        return int(cached_result)

    # Query database
    with get_connection() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("""
                SELECT count(*) FROM order
                WHERE customer_id = %s AND status = %s
            """, (customer_id, status))
        else:
            cursor.execute("""
                SELECT count(*) FROM order
                WHERE customer_id = %s
            """, (customer_id,))

        result = cursor.fetchone()[0]

        # Cache result for 5 minutes
        redis.setex(cache_key, 300, result)

        return result
```

### Database Configuration Tuning

```sql
-- Optimize PostgreSQL settings for performance
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Create optimized table structure
CREATE TABLE order (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    status TEXT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create partitions for better performance
CREATE TABLE order_2024_01 PARTITION OF order
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE order_2024_02 PARTITION OF order
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

## 📈 Step 5: Set Performance Standards

### Performance Requirements

```yaml
# performance-requirements.yaml
version: "1.0"
requirements:
  # API Response Times
  api:
    order_create: { p95: 200ms, mean: 100ms }
    order_update: { p95: 150ms, mean: 75ms }
    order_query: { p95: 100ms, mean: 50ms }

  # Database Query Times
  database:
    simple_select: { p95: 50ms, mean: 25ms }
    complex_join: { p95: 200ms, mean: 100ms }
    bulk_update: { p95: 1000ms, mean: 500ms }

  # State Machine Transitions
  state_machine:
    single_transition: { p95: 100ms, mean: 50ms }
    bulk_transition: { p95: 500ms, mean: 250ms }

  # Concurrent Load
  load:
    concurrent_users: 1000
    requests_per_second: 500
    error_rate: 0.01  # 1%

  # Resource Usage
  resources:
    memory_per_request: 10MB
    cpu_per_request: 5ms
    connections: 100
```

### Performance SLAs

```yaml
# performance-slas.yaml
service_level_agreements:
  # Critical Operations (99.9% uptime)
  critical:
    - operation: order_create
      availability: 0.999
      response_time_p95: 200ms
      error_budget: 0.1  # 0.1% errors allowed

  # Important Operations (99.5% uptime)
  important:
    - operation: order_update
      availability: 0.995
      response_time_p95: 500ms
      error_budget: 0.5

  # Standard Operations (99% uptime)
  standard:
    - operation: order_query
      availability: 0.99
      response_time_p95: 1000ms
      error_budget: 2.0
```

### Performance Monitoring

```python
# Continuous performance monitoring
def monitor_performance():
    """Monitor performance metrics continuously"""
    while True:
        # Run performance tests
        results = run_performance_tests()

        # Check against SLAs
        violations = check_sla_violations(results)

        if violations:
            # Alert on violations
            send_performance_alert(violations)

        # Store metrics for trending
        store_performance_metrics(results)

        # Wait before next check
        time.sleep(300)  # 5 minutes

def check_sla_violations(results):
    """Check if performance violates SLAs"""
    violations = []

    for test_name, metrics in results.items():
        sla = get_sla_for_operation(test_name)

        if metrics['p95'] > sla['response_time_p95']:
            violations.append({
                'operation': test_name,
                'violation': 'p95_response_time',
                'actual': metrics['p95'],
                'limit': sla['response_time_p95']
            })

        if metrics['error_rate'] > sla['error_budget']:
            violations.append({
                'operation': test_name,
                'violation': 'error_rate',
                'actual': metrics['error_rate'],
                'limit': sla['error_budget']
            })

    return violations
```

## 🔧 Step 6: Customize Performance Tests

### Test Configuration

```yaml
# In your entity YAML
name: order
# ... fields and patterns ...

test_config:
  performance:
    # Test settings
    enabled: true
    iterations: 1000
    concurrency: 10
    timeout: "5 minutes"

    # Test data
    data_sets:
      - name: small_dataset
        orders: 100
        customers: 10

      - name: large_dataset
        orders: 10000
        customers: 1000

    # Performance requirements
    requirements:
      - operation: order_confirm
        target_p95: 200ms
        target_mean: 100ms
        max_error_rate: 0.01

      - operation: bulk_order_update
        target_p95: 2000ms
        target_mean: 1000ms

    # Monitoring
    metrics:
      - query_execution_time
      - memory_usage
      - lock_wait_time
      - connection_count

    # Reporting
    reports:
      - format: html
        include_charts: true
        include_trends: true
      - format: json
        include_raw_data: true
```

### Custom Performance Tests

```sql
-- Custom performance test for complex business logic
CREATE OR REPLACE FUNCTION test_complex_order_processing_performance()
RETURNS TABLE(test_name text, execution_time interval, records_processed integer) AS $$
DECLARE
    start_time timestamp;
    end_time timestamp;
    processed_count integer := 0;
BEGIN
    -- Setup complex test data
    INSERT INTO order (id, customer_id, status, total_amount, created_at)
    SELECT
        gen_random_uuid(),
        'perf-test-customer',
        'pending',
        (random() * 1000 + 10)::decimal,
        NOW() - (random() * interval '90 days')
    FROM generate_series(1, 1000);

    -- Test complex order processing workflow
    start_time := clock_timestamp();

    -- Process orders with complex business logic
    UPDATE order
    SET status = CASE
            WHEN total_amount > 500 THEN 'requires_approval'
            WHEN total_amount > 100 THEN 'confirmed'
            ELSE 'cancelled'
        END,
        updated_at = NOW()
    WHERE customer_id = 'perf-test-customer'
      AND status = 'pending'
      AND created_at > NOW() - interval '30 days';

    GET DIAGNOSTICS processed_count = ROW_COUNT;

    end_time := clock_timestamp();

    -- Return results
    test_name := 'complex_order_processing';
    execution_time := end_time - start_time;
    records_processed := processed_count;

    RETURN NEXT;

    -- Cleanup
    DELETE FROM order WHERE customer_id = 'perf-test-customer';
END;
$$ LANGUAGE plpgsql;
```

## 🔄 Step 7: CI/CD Integration

### GitHub Actions Performance Testing

```yaml
# .github/workflows/performance-tests.yml
name: Performance Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    # Run daily performance tests
    - cron: '0 2 * * *'

jobs:
  performance:
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

      - name: Setup SpecQL
        run: pip install specql

      - name: Generate Schema
        run: specql generate schema entities/*.yaml

      - name: Setup Test Data
        run: |
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/00_foundation/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/10_tables/*.sql
          # Load performance test data
          ./scripts/load_performance_data.sh

      - name: Run Performance Tests
        run: specql test run --type performance entities/*.yaml --report performance-report.html

      - name: Check Performance Regression
        run: |
          # Compare against baseline
          python scripts/check_performance_regression.py \
            --baseline baseline-performance.json \
            --current performance-results.json \
            --max-degradation 0.1

      - name: Upload Performance Report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: performance-report.html

      - name: Alert on Performance Issues
        if: failure()
        run: |
          # Send alert to Slack/Teams
          curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"Performance regression detected!"}' \
            $SLACK_WEBHOOK_URL
```

### Performance Regression Detection

```python
# scripts/check_performance_regression.py
import json
import sys
import argparse

def check_performance_regression(baseline_file, current_file, max_degradation):
    """Check for performance regressions"""

    with open(baseline_file) as f:
        baseline = json.load(f)

    with open(current_file) as f:
        current = json.load(f)

    regressions = []

    for test_name in baseline['results']:
        if test_name in current['results']:
            baseline_mean = baseline['results'][test_name]['mean']
            current_mean = current['results'][test_name]['mean']

            degradation = (current_mean - baseline_mean) / baseline_mean

            if degradation > max_degradation:
                regressions.append({
                    'test': test_name,
                    'baseline': baseline_mean,
                    'current': current_mean,
                    'degradation': degradation
                })

    if regressions:
        print(f"🚨 Performance regressions detected:")
        for regression in regressions:
            print(f"  {regression['test']}: {regression['degradation']:.1%} degradation")
        sys.exit(1)
    else:
        print("✅ No performance regressions detected")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--current', required=True)
    parser.add_argument('--max-degradation', type=float, default=0.1)

    args = parser.parse_args()
    check_performance_regression(args.baseline, args.current, args.max_degradation)
```

## 🎯 Best Practices

### Test Design
- **Use realistic data volumes** - Test with production-scale data
- **Test under load** - Include concurrent user scenarios
- **Measure percentiles** - Focus on p95/p99, not just averages
- **Set meaningful targets** - Base requirements on user expectations

### Optimization
- **Profile before optimizing** - Measure before making changes
- **Index strategically** - Add indexes for performance-critical queries
- **Cache effectively** - Use caching for expensive operations
- **Monitor continuously** - Track performance over time

### Monitoring
- **Establish baselines** - Know your normal performance levels
- **Alert on regressions** - Catch performance issues early
- **Trend analysis** - Monitor performance changes over time
- **Capacity planning** - Plan for future growth

### Maintenance
- **Update baselines** - Adjust expectations as application evolves
- **Review performance tests** - Ensure they remain relevant
- **Document optimizations** - Explain why changes were made
- **Share knowledge** - Document performance lessons learned

## 🆘 Troubleshooting

### "Performance tests are too slow"
```bash
# Reduce test iterations
specql test run --type performance entities/order.yaml --iterations 100

# Use smaller data sets
specql generate tests --type performance entities/order.yaml --data-size 1000

# Run tests in parallel
specql test run --type performance entities/order.yaml --concurrency 4
```

### "Inconsistent performance results"
```bash
# Stabilize test environment
# - Use dedicated test database
# - Disable autovacuum during tests
# - Pre-warm database caches

# Add result stabilization
# - Run multiple iterations and average
# - Discard outlier results
# - Use statistical analysis
```

### "Performance regressions not detected"
```bash
# Check baseline accuracy
cat baseline-performance.json

# Verify test conditions match
# - Same data volumes
# - Same PostgreSQL configuration
# - Same hardware specifications

# Adjust sensitivity
specql test run --type performance entities/order.yaml --regression-threshold 0.05
```

### "Database becomes unresponsive under load"
```bash
# Check PostgreSQL configuration
psql $DATABASE_URL -c "SHOW shared_buffers;"
psql $DATABASE_URL -c "SHOW work_mem;"

# Monitor system resources
# - CPU usage
# - Memory usage
# - Disk I/O
# - Network I/O

# Optimize connection pooling
# Use PgBouncer or similar
```

## 📊 Success Metrics

### Performance Targets
- **API Response Time**: p95 < 200ms for critical operations
- **Database Query Time**: p95 < 50ms for simple queries
- **Concurrent Users**: Support 1000+ simultaneous users
- **Error Rate**: < 1% under normal load

### Reliability Goals
- **Performance Stability**: < 10% variance between test runs
- **Regression Detection**: Catch > 5% performance changes
- **Test Coverage**: Performance tests for all critical paths
- **Monitoring Coverage**: 100% of production operations monitored

### Business Impact
- **User Satisfaction**: Fast, responsive application
- **Operational Efficiency**: Reduced infrastructure costs
- **Development Velocity**: Quick feedback on performance impact
- **Risk Reduction**: Prevent performance issues in production

## 🎉 Summary

Performance testing provides:
- ✅ **Benchmarking** - Measure execution times and resource usage
- ✅ **Optimization** - Identify and fix performance bottlenecks
- ✅ **Regression prevention** - Catch performance issues before production
- ✅ **Capacity planning** - Understand system limits and scaling needs
- ✅ **Quality assurance** - Ensure consistent performance standards

## 🚀 What's Next?

- **[CI/CD Integration](ci-cd-integration.md)** - Automated performance testing
- **[Database Optimization](../best-practices/database-tuning.md)** - Advanced PostgreSQL tuning
- **[Monitoring](../best-practices/monitoring.md)** - Production performance monitoring
- **[Load Testing](../best-practices/load-testing.md)** - Advanced load testing techniques

**Ready to ensure your application performs at production levels? Let's continue! 🚀**