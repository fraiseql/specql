# Performance Best Practices

Optimization techniques for high-performance SpecQL applications, covering database tuning, query optimization, caching strategies, and scalability patterns.

## Overview

SpecQL generates efficient SQL by default, but understanding performance characteristics and applying optimization techniques is crucial for high-performance applications. This guide covers performance optimization strategies.

## Database Performance Fundamentals

### Connection Pooling

**Configure connection pooling for high throughput:**
```python
# pgBouncer configuration
[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
reserve_pool_size = 5
```

**Application connection configuration:**
```python
# SQLAlchemy engine configuration
engine = create_engine(
    "postgresql://user:pass@host:6432/db",  # Connect to pgBouncer
    pool_size=10,          # Connection pool size
    max_overflow=20,       # Max additional connections
    pool_timeout=30,       # Connection timeout
    pool_recycle=3600,     # Recycle connections hourly
    pool_pre_ping=True     # Test connections before use
)
```

### PostgreSQL Tuning

**Essential PostgreSQL settings for SpecQL:**
```sql
-- Memory settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Checkpoint settings
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';

-- Query planning
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET random_page_cost = 1.1;

-- Connection settings
ALTER SYSTEM SET max_connections = 200;
```

## Query Optimization

### Index Strategy

**Index for query patterns, not just fields:**
```yaml
# Good: Index supports actual queries
indexes:
  - name: idx_orders_customer_status_date
    columns: [customer_id, status, created_at DESC]
    type: btree

  - name: idx_products_category_price
    columns: [category, price]
    type: btree

  - name: idx_users_email_active
    columns: [email]
    condition: "status = 'active'"  # Partial index

# Bad: Index not used by queries
indexes:
  - name: idx_users_first_name
    columns: [first_name]  # Rarely queried alone
```

### Query Pattern Optimization

**Optimize common query patterns:**
```sql
-- Use covering indexes for frequent queries
CREATE INDEX CONCURRENTLY idx_orders_covering
ON orders (customer_id, status, created_at DESC)
INCLUDE (total_amount, shipping_address);

-- Use generated columns for computed values
ALTER TABLE products
ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (
    setweight(to_tsvector('english', name), 'A') ||
    setweight(to_tsvector('english', description), 'B')
) STORED;

CREATE INDEX idx_products_search ON products USING gin(search_vector);
```

### Partitioning Strategy

**Partition large tables for better performance:**
```yaml
# Time-based partitioning for orders
partitioning:
  strategy: RANGE
  column: created_at
  intervals: monthly
  retention: "2 years"

# List partitioning for multi-tenant data
partitioning:
  strategy: LIST
  column: tenant_id
  intervals: [tenant_1, tenant_2, tenant_3]
```

**Partition maintenance:**
```sql
-- Create new partition
CREATE TABLE orders_2024_02 PARTITION OF orders
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Detach old partitions
ALTER TABLE orders DETACH PARTITION orders_2022_01;

-- Create indexes on new partitions
CREATE INDEX idx_orders_2024_02_customer ON orders_2024_02 (customer_id);
```

## SpecQL-Specific Optimizations

### Pattern Performance Characteristics

| Pattern | Performance | Best Use Case | Optimization Tips |
|---------|-------------|----------------|-------------------|
| `crud/create` | Excellent | All creates | Use duplicate_check wisely |
| `crud/update` | Excellent | Single updates | Enable partial_updates |
| `crud/delete` | Excellent | Single deletes | Use soft deletes for relations |
| `state_machine/transition` | Good | Simple workflows | Pre-validate common transitions |
| `state_machine/guarded_transition` | Fair | Complex rules | Cache expensive guard conditions |
| `validation/validation_chain` | Excellent | Input validation | Use database constraints |
| `batch/bulk_operation` | Variable | Bulk processing | Tune batch_size |
| `multi_entity/coordinated_update` | Good | Related updates | Keep transactions short |
| `multi_entity/saga_orchestrator` | Fair | Distributed tx | Use async compensations |

### Action Optimization

**Optimize action performance:**
```yaml
actions:
  # Fast path for common case
  - name: quick_approve
    pattern: state_machine/transition
    config:
      from_states: [pending]
      to_state: approved
      validation_checks:
        - condition: "amount <= 1000"  # Fast check
      side_effects:
        - entity: AuditLog
          insert:
            action: quick_approved
            timestamp: now()

  # Full approval for complex cases
  - name: full_approve
    pattern: state_machine/guarded_transition
    config:
      from_states: [pending]
      to_state: approved
      guards:
        - condition: "complex_business_rule(amount, department_id)"
        # Expensive check, separate action
```

### Projection Optimization

**Optimize materialized projections:**
```yaml
projections:
  - name: user_stats
    includes:
      - User: [id, status, created_at]
      - Order: [COUNT(*) as order_count, SUM(total) as total_spent]
    filters:
      - condition: "created_at > now() - interval '90 days'"
    refresh:
      materialized: true
      on: [create, update]  # Not on every order change
      concurrently: true    # Non-blocking refresh
```

## Caching Strategies

### Application-Level Caching

**Cache frequently accessed data:**
```python
from cachetools import TTLCache

# Cache user permissions (5 minute TTL)
user_permissions_cache = TTLCache(maxsize=10000, ttl=300)

def get_user_permissions(user_id):
    if user_id in user_permissions_cache:
        return user_permissions_cache[user_id]

    permissions = db.query_user_permissions(user_id)
    user_permissions_cache[user_id] = permissions
    return permissions
```

### Database-Level Caching

**Use PostgreSQL caching features:**
```sql
-- Cache prepared statements
PREPARE user_lookup (uuid) AS
SELECT id, name, email, status FROM users WHERE id = $1;

-- Cache query results with memoization
CREATE OR REPLACE FUNCTION get_product_price(product_id uuid)
RETURNS decimal AS $$
BEGIN
    -- Check cache first
    RETURN COALESCE(
        (SELECT price FROM product_price_cache
         WHERE id = product_id
           AND cached_at > now() - interval '1 hour'),
        -- Fallback to live data
        (SELECT price FROM products WHERE id = product_id)
    );
END;
$$ LANGUAGE plpgsql STABLE;
```

### Redis Integration

**Cache complex computed data:**
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def cache_user_dashboard(user_id):
    """Cache expensive dashboard calculations"""
    cache_key = f"user_dashboard:{user_id}"

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Compute dashboard data
    dashboard = compute_expensive_dashboard(user_id)

    # Cache for 10 minutes
    redis_client.setex(cache_key, 600, json.dumps(dashboard))

    return dashboard
```

## Bulk Operation Optimization

### Batch Size Tuning

**Find optimal batch size:**
```python
def find_optimal_batch_size():
    """Test different batch sizes to find optimum"""
    batch_sizes = [10, 50, 100, 500, 1000]

    for size in batch_sizes:
        start_time = time.time()

        # Process batch
        process_batch(size)

        end_time = time.time()
        throughput = size / (end_time - start_time)

        print(f"Batch size {size}: {throughput} items/second")

    # Optimal is usually 100-500 items
```

### Parallel Processing

**Process batches in parallel:**
```python
from concurrent.futures import ThreadPoolExecutor

def bulk_process_parallel(items, batch_size=100, max_workers=4):
    """Process items in parallel batches"""
    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]

        results = []
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())

    return results
```

### Transaction Optimization

**Optimize transaction boundaries:**
```python
# Good: Small, focused transactions
def process_orders_efficiently(orders):
    for order in orders:
        with db.transaction():
            validate_order(order)
            update_inventory(order)
            create_shipment(order)
            # Commit happens here

# Bad: Large transaction
def process_orders_inefficiently(orders):
    with db.transaction():
        for order in orders:  # Locks held for entire loop
            validate_order(order)
            update_inventory(order)
            create_shipment(order)
        # Commit happens here
```

## Monitoring and Profiling

### Query Performance Monitoring

**Monitor slow queries:**
```sql
-- Create view for slow query analysis
CREATE VIEW slow_queries AS
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    temp_blks_written,
    blk_read_time,
    blk_write_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- Queries slower than 1 second
ORDER BY mean_time DESC;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

### Application Performance Monitoring

**Monitor application metrics:**
```python
from prometheus_client import Histogram, Counter

# Request duration histogram
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status']
)

# Database operation counter
db_operations = Counter(
    'db_operations_total',
    'Total database operations',
    ['operation', 'table']
)

@app.route('/api/users')
@request_duration.time()  # Measure request time
def get_users():
    db_operations.labels(operation='select', table='users').inc()
    # ... endpoint logic
```

### Database Performance Dashboard

**Create performance monitoring views:**
```sql
-- Connection usage
CREATE VIEW connection_usage AS
SELECT
    datname,
    usename,
    count(*) as connections,
    count(*) FILTER (WHERE state = 'active') as active_connections,
    count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity
GROUP BY datname, usename;

-- Table bloat analysis
CREATE VIEW table_bloat AS
SELECT
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    ROUND(n_dead_tup::numeric / (n_live_tup + n_dead_tup) * 100, 2) as bloat_ratio
FROM pg_stat_user_tables
WHERE n_live_tup + n_dead_tup > 0
ORDER BY bloat_ratio DESC;

-- Index usage
CREATE VIEW index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Scalability Patterns

### Read/Write Splitting

**Separate read and write workloads:**
```python
# Write connection (master)
write_engine = create_engine("postgresql://user:pass@master/db")

# Read connection (replica)
read_engine = create_engine("postgresql://user:pass@replica/db")

def get_user(user_id):
    """Read from replica"""
    with read_engine.connect() as conn:
        return conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()

def update_user(user_id, data):
    """Write to master"""
    with write_engine.connect() as conn:
        conn.execute("UPDATE users SET ... WHERE id = %s", (user_id, *data))
        conn.commit()
```

### Database Sharding

**Shard large tables:**
```python
def get_shard(user_id):
    """Determine shard based on user_id"""
    shard_count = 4
    shard = hash(user_id) % shard_count
    return f"shard_{shard}"

def get_user_connection(user_id):
    """Get connection for user's shard"""
    shard = get_shard(user_id)
    return shard_connections[shard]
```

### CQRS Pattern

**Separate read and write models:**
```python
# Write model (normalized)
class OrderWriteModel:
    def create_order(self, order_data):
        # Complex business logic
        # Multiple table updates
        pass

# Read model (denormalized)
class OrderReadModel:
    def get_order_summary(self, order_id):
        # Fast query from denormalized table
        return db.query("""
            SELECT * FROM order_summaries
            WHERE id = %s
        """, (order_id,)).fetchone()
```

## Performance Testing

### Load Testing Framework

**Create realistic load tests:**
```python
import locust

class SpecQLUser(HttpUser):
    @task
    def create_order(self):
        """Simulate order creation"""
        order_data = {
            "customer_id": str(uuid.uuid4()),
            "items": [
                {"product_id": str(uuid.uuid4()), "quantity": random.randint(1, 5)}
                for _ in range(random.randint(1, 10))
            ]
        }

        self.client.post("/api/orders", json=order_data)

    @task(3)  # 3x more frequent
    def get_user_orders(self):
        """Simulate order history viewing"""
        user_id = str(uuid.uuid4())
        self.client.get(f"/api/users/{user_id}/orders")

# Run with: locust -f load_test.py --host=http://localhost:8000
```

### Performance Benchmarks

**Establish performance baselines:**
```python
PERFORMANCE_THRESHOLDS = {
    "create_user": 0.01,        # 10ms
    "get_user_profile": 0.05,   # 50ms
    "search_products": 0.1,     # 100ms
    "bulk_import_1000": 2.0,    # 2 seconds
}

def benchmark_operation(operation_name, operation_func, *args):
    """Benchmark operation against threshold"""
    start_time = time.perf_counter()
    result = operation_func(*args)
    end_time = time.perf_counter()

    duration = end_time - start_time
    threshold = PERFORMANCE_THRESHOLDS[operation_name]

    if duration > threshold:
        print(f"⚠️  {operation_name} exceeded threshold: {duration:.3f}s > {threshold}s")
    else:
        print(f"✅ {operation_name} within threshold: {duration:.3f}s")

    return result
```

## Maintenance and Optimization

### Regular Maintenance Tasks

**Automate database maintenance:**
```bash
# Vacuum and analyze daily
0 2 * * * psql -c "VACUUM ANALYZE;"

# Reindex weekly
0 3 * * 0 psql -c "REINDEX DATABASE specql;"

# Update statistics
0 4 * * * psql -c "ANALYZE;"
```

### Performance Monitoring

**Set up alerts for performance degradation:**
```yaml
# Prometheus alerting rules
groups:
  - name: database_performance
    rules:
      - alert: SlowQueries
        expr: rate(pg_stat_statements_mean_time[5m]) > 5000
        for: 10m
        labels:
          severity: warning

      - alert: HighConnectionCount
        expr: pg_stat_activity_count{state="active"} > 50
        for: 5m
        labels:
          severity: warning

      - alert: TableBloat
        expr: pg_stat_user_tables_n_dead_tup > 100000
        for: 15m
        labels:
          severity: info
```

### Capacity Planning

**Monitor growth and plan scaling:**
```sql
-- Database growth tracking
CREATE VIEW database_growth AS
SELECT
    schemaname,
    tablename,
    pg_total_relation_size(schemaname||'.'||tablename) as total_size,
    pg_relation_size(schemaname||'.'||tablename) as table_size,
    pg_total_relation_size(schemaname||'.'||tablename) -
    pg_relation_size(schemaname||'.'||tablename) as index_size,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables
ORDER BY total_size DESC;

-- Query for capacity planning
SELECT
    date_trunc('month', created_at) as month,
    COUNT(*) as records_created,
    pg_size_pretty(sum(pg_column_size(t))) as estimated_size
FROM large_table t
WHERE created_at > now() - interval '6 months'
GROUP BY date_trunc('month', created_at)
ORDER BY month;
```

## Troubleshooting Performance Issues

### Common Performance Problems

**Slow queries:**
```sql
-- Find slow queries
SELECT
    query,
    mean_time,
    calls,
    total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Explain slow query
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM large_table WHERE date_column > '2024-01-01';
```

**Lock contention:**
```sql
-- Check for locks
SELECT
    locktype,
    relation::regclass,
    mode,
    granted,
    pid,
    usename
FROM pg_locks
WHERE NOT granted;

-- Find blocking queries
SELECT
    blocked.pid as blocked_pid,
    blocked.query as blocked_query,
    blocking.pid as blocking_pid,
    blocking.query as blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));
```

**Memory issues:**
```sql
-- Check memory usage
SELECT
    name,
    setting,
    unit
FROM pg_settings
WHERE name LIKE '%mem%' OR name LIKE '%buffer%';

-- Monitor work_mem usage
SHOW work_mem;
```

### Performance Tuning Checklist

- [ ] Indexes support query patterns
- [ ] Tables are properly partitioned
- [ ] Connection pooling is configured
- [ ] Query plans are optimal
- [ ] Caching is implemented where appropriate
- [ ] Batch operations use optimal batch sizes
- [ ] Transactions are kept short
- [ ] Monitoring and alerting are in place

---

**See Also:**
- [Pattern Selection Best Practices](pattern-selection.md)
- [Entity Design Best Practices](entity-design.md)
- [Testing Strategy](testing-strategy.md)
- [Security Best Practices](security.md)