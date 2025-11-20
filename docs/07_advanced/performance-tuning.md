# Performance Tuning Guide

> **Optimize SpecQL-generated code for production scale—milliseconds matter**

## Overview

SpecQL generates highly optimized PostgreSQL code by default, but you can tune performance further for specific workloads. This guide covers:

- ✅ Query optimization techniques
- ✅ Index strategies
- ✅ Trinity pattern performance
- ✅ Action compilation tuning
- ✅ Database configuration
- ✅ Profiling and monitoring

**Target**: Sub-10ms query latency, 1000+ TPS (transactions per second)

---

## Quick Wins

### 1. Use Trinity Pattern INTEGER Joins

**Problem**: UUID joins are 3x slower than INTEGER joins

**SpecQL Default**: Already uses INTEGER joins automatically
```sql
-- ✅ SpecQL auto-generates (fast)
SELECT c.*, co.name
FROM tb_contact c
INNER JOIN tb_company co ON c.fk_company = co.pk_company;  -- INTEGER join

-- ❌ Manual UUID join (slow)
SELECT c.*, co.name
FROM tb_contact c
INNER JOIN tb_company co ON c.company_id = co.id;  -- UUID join
```

**Performance**: 3x faster joins with Trinity pattern

---

### 2. Enable Auto-Indexing

**SpecQL Default**: Auto-creates indexes on:
- Foreign key columns (`fk_*`)
- Enum fields
- `tenant_id` (multi-tenant schemas)
- Unique constraints

**No configuration needed** - indexes generated automatically.

**Verify indexes**:
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'tb_contact';
```

---

### 3. Use EXPLAIN ANALYZE

**Profile slow queries**:
```sql
EXPLAIN ANALYZE
SELECT * FROM crm.tb_contact
WHERE fk_company = 123 AND status = 'lead';
```

**Look for**:
- ✅ "Index Scan" (good)
- ❌ "Seq Scan" (bad for large tables)
- Execution time < 10ms

---

## Index Optimization

### Composite Indexes

**When to use**: Queries filter on multiple columns

```yaml
entity: Order
schema: sales

fields:
  customer: ref(Customer)!
  status: enum(pending, shipped, delivered)!
  created_at: datetime!

indexes:
  # Composite index for common query pattern
  - columns: [customer, status]
    name: idx_order_customer_status

  # Time-series index
  - columns: [created_at]
    type: brin  # Block Range Index (efficient for time series)
```

**Generated SQL**:
```sql
-- Composite index for customer + status queries
CREATE INDEX idx_order_customer_status
    ON sales.tb_order (fk_customer, status);

-- BRIN index for time-series queries
CREATE INDEX idx_order_created_at
    ON sales.tb_order USING BRIN (created_at);
```

**Query benefits**:
```sql
-- Uses composite index
SELECT * FROM sales.tb_order
WHERE fk_customer = 123 AND status = 'pending';

-- Uses BRIN index
SELECT * FROM sales.tb_order
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

### Partial Indexes

**When to use**: Index only rows matching a condition

```yaml
entity: Order
schema: sales

fields:
  status: enum(pending, shipped, delivered, cancelled)!

indexes:
  # Index only active orders (pending/shipped)
  - columns: [status]
    where: "status IN ('pending', 'shipped')"
    name: idx_order_active_status
```

**Generated SQL**:
```sql
CREATE INDEX idx_order_active_status
    ON sales.tb_order (status)
    WHERE status IN ('pending', 'shipped');
```

**Benefits**:
- Smaller index size (excludes delivered/cancelled)
- Faster queries on active orders
- Lower maintenance overhead

---

### Covering Indexes

**When to use**: Avoid table lookups by including all needed columns in index

```yaml
entity: Contact
schema: crm

indexes:
  # Covering index: includes frequently accessed columns
  - columns: [status, email, first_name, last_name]
    name: idx_contact_status_covering
    include: [email, first_name, last_name]  # Extra columns
```

**Generated SQL**:
```sql
CREATE INDEX idx_contact_status_covering
    ON crm.tb_contact (status)
    INCLUDE (email, first_name, last_name);
```

**Query benefits**:
```sql
-- Index-only scan (no table access)
SELECT email, first_name, last_name
FROM crm.tb_contact
WHERE status = 'lead';
```

---

### Index Types

| Type | Use Case | Example |
|------|----------|---------|
| **B-tree** (default) | General purpose | `status`, `created_at` |
| **BRIN** | Time-series, append-only | `created_at`, `log_timestamp` |
| **GIN** | JSONB, arrays, full-text | `tags`, `metadata` |
| **GiST** | Geospatial, ranges | `coordinates`, `date_range` |
| **Hash** | Equality only (rare) | `exact_match_field` |

**Configuration**:
```yaml
indexes:
  - columns: [created_at]
    type: brin

  - columns: [metadata]
    type: gin

  - columns: [coordinates]
    type: gist
```

---

## Action Performance

### Minimize Database Round-Trips

**Bad**: Multiple queries
```yaml
actions:
  - name: get_order_details
    steps:
      - query: Order WHERE id = $order_id
        result: $order
      - query: Customer WHERE id = $order.customer
        result: $customer
      - query: OrderItem WHERE order = $order_id
        result: $items
      # 3 round-trips!
```

**Good**: Single JOIN query
```yaml
actions:
  - name: get_order_details
    steps:
      - query: |
          SELECT
            o.*,
            c.name as customer_name,
            c.email as customer_email,
            json_agg(oi.*) as items
          FROM Order o
          INNER JOIN Customer c ON o.customer = c.id
          LEFT JOIN OrderItem oi ON oi.order = o.id
          WHERE o.id = $order_id
          GROUP BY o.pk_order, c.pk_customer
        result: $order_details
      # 1 round-trip!
```

**Performance**: 3x faster (1 query vs 3)

---

### Batch Operations

**Bad**: Loop with individual updates
```yaml
actions:
  - name: update_prices
    params:
      product_ids: list(uuid)!
      new_price: money!
    steps:
      - foreach: $product_ids as $id
        do:
          - update: Product WHERE id = $id SET price = $new_price
      # N database calls
```

**Good**: Single batch update
```yaml
actions:
  - name: update_prices
    params:
      product_ids: list(uuid)!
      new_price: money!
    steps:
      - update: Product
        WHERE id = ANY($product_ids)
        SET price = $new_price
      # 1 database call
```

**Performance**: 10-100x faster for large batches

---

### Use CTEs for Complex Logic

**Common Table Expressions (CTEs)** organize complex queries:

```yaml
actions:
  - name: get_top_customers
    steps:
      - query: |
          WITH customer_stats AS (
            SELECT
              fk_customer,
              COUNT(*) as order_count,
              SUM(total_amount) as total_spent
            FROM sales.tb_order
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY fk_customer
          ),
          ranked_customers AS (
            SELECT
              c.*,
              cs.order_count,
              cs.total_spent,
              RANK() OVER (ORDER BY cs.total_spent DESC) as rank
            FROM crm.tb_customer c
            INNER JOIN customer_stats cs ON c.pk_customer = cs.fk_customer
          )
          SELECT * FROM ranked_customers
          WHERE rank <= 10
        result: $top_customers
```

---

## Query Optimization

### Avoid SELECT *

**Bad**:
```yaml
- query: SELECT * FROM Contact
  result: $contacts
```

**Good**:
```yaml
- query: SELECT id, email, first_name, last_name FROM Contact
  result: $contacts
```

**Benefits**:
- Less data transfer
- Better use of covering indexes
- Reduced memory usage

---

### Use LIMIT and OFFSET Wisely

**Bad**: Fetch all rows
```yaml
- query: SELECT * FROM Contact ORDER BY created_at DESC
  result: $contacts
```

**Good**: Paginate
```yaml
- query: |
    SELECT id, email, first_name, last_name
    FROM Contact
    ORDER BY created_at DESC
    LIMIT 50 OFFSET $page * 50
  result: $contacts
```

**Better**: Cursor-based pagination (for large datasets)
```yaml
- query: |
    SELECT id, email, first_name, last_name
    FROM Contact
    WHERE created_at < $last_created_at
    ORDER BY created_at DESC
    LIMIT 50
  result: $contacts
```

---

### Denormalization for Read-Heavy Workloads

**When to use**: Frequently joined data that rarely changes

```yaml
entity: Order
schema: sales

fields:
  customer: ref(Customer)!
  customer_name: text!  # Denormalized for performance
  customer_email: email!  # Denormalized for performance

actions:
  - name: create_order
    steps:
      - query: Customer WHERE id = $customer_id
        result: $customer

      - insert: Order VALUES (
          customer: $customer_id,
          customer_name: $customer.name,  # Store copy
          customer_email: $customer.email  # Store copy
        )
```

**Trade-off**: More storage, faster reads, potential staleness

---

## PostgreSQL Configuration

### Connection Pooling

**Use PgBouncer** for connection pooling:

```ini
# pgbouncer.ini
[databases]
myapp = host=localhost port=5432 dbname=myapp

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

**Benefits**:
- Reduce connection overhead
- Handle 1000+ concurrent connections
- Sub-millisecond connection acquisition

---

### Memory Configuration

**Tune PostgreSQL memory settings**:

```sql
-- postgresql.conf
shared_buffers = 4GB           -- 25% of RAM
effective_cache_size = 12GB    -- 75% of RAM
work_mem = 50MB                -- Per-operation memory
maintenance_work_mem = 1GB     -- For VACUUM, CREATE INDEX

-- Query planner settings
random_page_cost = 1.1         -- SSD-optimized
effective_io_concurrency = 200 -- SSD parallelism
```

---

### Autovacuum Tuning

**Aggressive autovacuum for high-write tables**:

```yaml
entity: Order
schema: sales

table_settings:
  autovacuum_vacuum_scale_factor: 0.05  # Vacuum at 5% change (default: 20%)
  autovacuum_analyze_scale_factor: 0.02 # Analyze at 2% change (default: 10%)
```

**Generated SQL**:
```sql
ALTER TABLE sales.tb_order SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);
```

---

## Profiling and Monitoring

### Enable Query Logging

**Log slow queries**:
```sql
-- postgresql.conf
log_min_duration_statement = 100  -- Log queries > 100ms
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_statement = 'all'  # Or 'ddl', 'mod', 'none'
```

---

### Use pg_stat_statements

**Install extension**:
```sql
CREATE EXTENSION pg_stat_statements;
```

**Find slow queries**:
```sql
SELECT
    query,
    calls,
    total_exec_time / 1000 as total_time_sec,
    mean_exec_time / 1000 as avg_time_ms,
    max_exec_time / 1000 as max_time_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

---

### Action Performance Metrics

**SpecQL auto-generates timing in actions**:

```sql
CREATE OR REPLACE FUNCTION app.qualify_lead(...)
RETURNS app.mutation_result AS $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
BEGIN
    v_start_time := clock_timestamp();

    -- Action logic here

    v_end_time := clock_timestamp();

    -- Log performance
    INSERT INTO core.action_metrics (
        action_name,
        duration_ms,
        executed_at
    ) VALUES (
        'qualify_lead',
        EXTRACT(MILLISECOND FROM v_end_time - v_start_time),
        NOW()
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

## Real-World Optimization Examples

### Example 1: E-commerce Order Query

**Before** (slow):
```yaml
actions:
  - name: get_orders
    steps:
      - query: |
          SELECT * FROM Order
          WHERE customer = $customer_id
        result: $orders

      - foreach: $orders as $order
        do:
          - query: OrderItem WHERE order = $order.id
            result: $order.items
          # N+1 queries!
```

**After** (fast):
```yaml
actions:
  - name: get_orders
    steps:
      - query: |
          SELECT
            o.*,
            json_agg(json_build_object(
              'id', oi.id,
              'product_name', p.name,
              'quantity', oi.quantity,
              'unit_price', oi.unit_price
            )) as items
          FROM Order o
          LEFT JOIN OrderItem oi ON oi.order = o.id
          LEFT JOIN Product p ON oi.product = p.id
          WHERE o.customer = $customer_id
          GROUP BY o.pk_order
        result: $orders
      # 1 query total
```

**Performance**: 50x faster (1 query vs 50+ for N=50 orders)

---

### Example 2: Dashboard Aggregation

**Before** (slow):
```yaml
actions:
  - name: get_dashboard_stats
    steps:
      - query: COUNT(*) FROM Order WHERE status = 'pending'
        result: $pending_count
      - query: COUNT(*) FROM Order WHERE status = 'shipped'
        result: $shipped_count
      - query: SUM(total_amount) FROM Order WHERE created_at > NOW() - INTERVAL '30 days'
        result: $monthly_revenue
      # 3 separate queries
```

**After** (fast):
```yaml
actions:
  - name: get_dashboard_stats
    steps:
      - query: |
          SELECT
            COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
            COUNT(*) FILTER (WHERE status = 'shipped') as shipped_count,
            SUM(total_amount) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as monthly_revenue
          FROM Order
        result: $stats
      # 1 query
```

**Performance**: 3x faster

---

### Example 3: Hierarchical Categories

**Before** (slow):
```yaml
actions:
  - name: get_category_tree
    steps:
      - query: Category WHERE parent IS NULL
        result: $root_categories

      - foreach: $root_categories as $cat
        do:
          - call: get_children_recursive, args: {parent_id: $cat.id}
          # Recursive calls
```

**After** (fast):
```yaml
actions:
  - name: get_category_tree
    steps:
      - query: |
          WITH RECURSIVE category_tree AS (
            -- Base case: root categories
            SELECT
              pk_category,
              id,
              name,
              fk_parent,
              1 as depth,
              ARRAY[pk_category] as path
            FROM catalog.tb_category
            WHERE fk_parent IS NULL

            UNION ALL

            -- Recursive case: children
            SELECT
              c.pk_category,
              c.id,
              c.name,
              c.fk_parent,
              ct.depth + 1,
              ct.path || c.pk_category
            FROM catalog.tb_category c
            INNER JOIN category_tree ct ON c.fk_parent = ct.pk_category
          )
          SELECT * FROM category_tree
          ORDER BY path
        result: $tree
      # 1 recursive CTE query
```

**Performance**: 10-100x faster depending on tree depth

---

## Caching Strategies

### Application-Level Caching

**Use Redis for frequently accessed data**:

```yaml
actions:
  - name: get_product
    params:
      product_id: uuid!
    steps:
      # Check cache first
      - call: redis_get, args: {key: "product:#{$product_id}"}
        result: $cached_product

      - if: $cached_product IS NULL
        then:
          # Cache miss: fetch from DB
          - query: Product WHERE id = $product_id
            result: $product

          # Store in cache (5 min TTL)
          - call: redis_set, args: {
              key: "product:#{$product_id}",
              value: $product,
              ttl: 300
            }

          - return: $product
        else:
          # Cache hit
          - return: $cached_product
```

---

### Materialized Views

**For expensive aggregations**:

```yaml
table_view: OrderSummary
schema: sales
refresh: hourly

query: |
  SELECT
    fk_customer,
    COUNT(*) as order_count,
    SUM(total_amount) as total_spent,
    AVG(total_amount) as avg_order_value,
    MAX(created_at) as last_order_at
  FROM sales.tb_order
  WHERE status != 'cancelled'
  GROUP BY fk_customer
```

**Generated SQL**:
```sql
CREATE MATERIALIZED VIEW sales.tv_order_summary AS
SELECT ...;

CREATE UNIQUE INDEX ON sales.tv_order_summary (fk_customer);

-- Refresh schedule (via cron or pg_cron)
REFRESH MATERIALIZED VIEW CONCURRENTLY sales.tv_order_summary;
```

---

## Best Practices Summary

### ✅ DO

1. **Use Trinity pattern INTEGER joins** (SpecQL default)
2. **Create composite indexes** for multi-column queries
3. **Use LIMIT/OFFSET** for pagination
4. **Batch operations** instead of loops
5. **Profile with EXPLAIN ANALYZE** before optimizing
6. **Monitor with pg_stat_statements**
7. **Use connection pooling** (PgBouncer)
8. **Denormalize selectively** for read-heavy workloads

---

### ❌ DON'T

1. **Don't use SELECT *** - specify columns
2. **Don't create N+1 queries** - use JOINs
3. **Don't over-index** - each index has maintenance cost
4. **Don't skip profiling** - measure before optimizing
5. **Don't ignore autovacuum** - keep tables healthy
6. **Don't use UUIDs for joins** - use Trinity pattern INTEGERs

---

## Next Steps

### Learn More

- **[Caching Guide](caching.md)** - Redis integration patterns
- **[Monitoring Guide](monitoring.md)** - Production observability
- **[Deployment Guide](deployment.md)** - Scale PostgreSQL

### Tools

- **pgAdmin** - Query profiling GUI
- **pg_stat_statements** - Query performance tracking
- **PgBouncer** - Connection pooling
- **pgBadger** - Log analysis

---

## Summary

You've learned:
- ✅ Index optimization strategies
- ✅ Query performance tuning
- ✅ Action compilation best practices
- ✅ PostgreSQL configuration
- ✅ Profiling and monitoring tools

**Key Takeaway**: SpecQL generates optimized code by default, but production scale requires tuning queries, indexes, and database configuration.

**Next**: Scale to production with [Deployment Guide](deployment.md) →

---

**Optimize for milliseconds—every query counts at scale.**
