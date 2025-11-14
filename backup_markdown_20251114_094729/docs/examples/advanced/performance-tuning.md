# Performance Tuning Example

This example demonstrates advanced performance optimization techniques using SpecQL's patterns for high-throughput systems, including query optimization, indexing strategies, and efficient data processing.

## Overview

We'll create a high-performance e-commerce analytics system that handles:
1. Real-time sales tracking
2. Product performance metrics
3. Customer behavior analysis
4. Inventory optimization

This shows how SpecQL optimizes database performance for analytical workloads.

## Entity Definitions

### Sales Analytics System (`sales_analytics.yaml`)

```yaml
entity: SalesTransaction
schema: analytics
description: "High-performance sales transaction processing"

fields:
  transaction_id: uuid
  customer_id: uuid
  product_id: uuid
  quantity: integer
  unit_price: decimal(10,2)
  total_amount: decimal(10,2)
  transaction_date: timestamp
  payment_method: text
  region: text
  category: text

indexes:
  - name: idx_sales_transaction_date
    columns: [transaction_date]
    type: BRIN  # Efficient for time-series data
  - name: idx_sales_customer_product
    columns: [customer_id, product_id]
    type: HASH  # Fast equality lookups
  - name: idx_sales_region_category_date
    columns: [region, category, transaction_date]
    type: GIST  # Multi-column range queries

partitioning:
  strategy: RANGE
  column: transaction_date
  intervals:
    - monthly  # Partition by month for efficient querying

actions:
  # Bulk transaction processing
  - name: bulk_insert_transactions
    pattern: batch/bulk_operation
    operation: insert
    batch_field: transactions
    performance_hints:
      - disable_triggers: true  # Speed up bulk inserts
      - disable_indexes: true   # Rebuild indexes after bulk load
      - copy_mode: true         # Use PostgreSQL COPY for maximum speed

  # Real-time analytics aggregation
  - name: update_performance_metrics
    pattern: composite/workflow_orchestrator
    trigger: transaction_inserted
    performance_hints:
      - async_execution: true   # Don't block transaction processing
      - batch_updates: true     # Aggregate multiple updates
      - materialized_views: true # Pre-computed aggregations

    workflow:
      - step: update_product_metrics
        action: update
        entity: ProductMetrics
        fields:
          total_sales: "total_sales + transaction.total_amount"
          total_quantity: "total_quantity + transaction.quantity"
          last_sale_date: "GREATEST(last_sale_date, transaction.transaction_date)"
        condition: "product_id = transaction.product_id"

      - step: update_customer_metrics
        action: update
        entity: CustomerMetrics
        fields:
          total_spent: "total_spent + transaction.total_amount"
          total_orders: "total_orders + 1"
          last_order_date: "GREATEST(last_order_date, transaction.transaction_date)"
          avg_order_value: "(total_spent + transaction.total_amount) / (total_orders + 1)"
        condition: "customer_id = transaction.customer_id"

      - step: update_category_metrics
        action: update
        entity: CategoryMetrics
        fields:
          total_sales: "total_sales + transaction.total_amount"
          total_transactions: "total_transactions + 1"
        condition: "category = transaction.category"
```

### Performance Metrics Entities

```yaml
# Pre-aggregated product performance
entity: ProductMetrics
schema: analytics
fields:
  product_id: uuid
  total_sales: decimal(12,2)
  total_quantity: integer
  last_sale_date: timestamp
  avg_sale_price: decimal(10,2)
  sales_velocity: decimal(5,2)  # Sales per day

indexes:
  - name: idx_product_metrics_sales
    columns: [total_sales DESC]
  - name: idx_product_metrics_velocity
    columns: [sales_velocity DESC]

materialized_view: product_performance_mv
refresh_strategy: concurrent
refresh_interval: "1 hour"

# Customer analytics
entity: CustomerMetrics
schema: analytics
fields:
  customer_id: uuid
  total_spent: decimal(12,2)
  total_orders: integer
  avg_order_value: decimal(10,2)
  last_order_date: timestamp
  customer_segment: text

indexes:
  - name: idx_customer_metrics_segment
    columns: [customer_segment]
  - name: idx_customer_metrics_value
    columns: [avg_order_value DESC]
```

## Generated SQL with Performance Optimizations

SpecQL generates optimized SQL with performance hints:

```sql
-- Partitioned table creation
CREATE TABLE analytics.sales_transaction (
    transaction_id uuid NOT NULL DEFAULT gen_random_uuid(),
    customer_id uuid,
    product_id uuid,
    quantity integer,
    unit_price decimal(10,2),
    total_amount decimal(10,2),
    transaction_date timestamp NOT NULL,
    payment_method text,
    region text,
    category text
) PARTITION BY RANGE (transaction_date);

-- Create monthly partitions
CREATE TABLE analytics.sales_transaction_2024_01 PARTITION OF analytics.sales_transaction
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE analytics.sales_transaction_2024_02 PARTITION OF analytics.sales_transaction
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Optimized indexes
CREATE INDEX CONCURRENTLY idx_sales_transaction_date ON analytics.sales_transaction
    USING BRIN (transaction_date) WITH (pages_per_range = 128);

CREATE INDEX CONCURRENTLY idx_sales_customer_product ON analytics.sales_transaction
    USING HASH (customer_id, product_id);

-- Bulk insert function with performance optimizations
CREATE OR REPLACE FUNCTION analytics.bulk_insert_transactions(
    p_transactions jsonb
) RETURNS integer AS $$
DECLARE
    v_transaction record;
    v_inserted_count integer := 0;
BEGIN
    -- Disable triggers for bulk insert
    SET session_replication_role = 'replica';

    -- Use unlogged table for temporary high-speed inserts
    CREATE UNLOGGED TABLE temp_transactions (LIKE analytics.sales_transaction);

    -- Bulk insert into temp table
    INSERT INTO temp_transactions
    SELECT
        (t->>'transaction_id')::uuid,
        (t->>'customer_id')::uuid,
        (t->>'product_id')::uuid,
        (t->>'quantity')::integer,
        (t->>'unit_price')::decimal,
        (t->>'total_amount')::decimal,
        (t->>'transaction_date')::timestamp,
        t->>'payment_method',
        t->>'region',
        t->>'category'
    FROM jsonb_array_elements(p_transactions) t;

    -- Move to partitioned table (this is optimized)
    INSERT INTO analytics.sales_transaction
    SELECT * FROM temp_transactions;

    GET DIAGNOSTICS v_inserted_count = ROW_COUNT;

    -- Cleanup
    DROP TABLE temp_transactions;

    -- Re-enable triggers
    SET session_replication_role = 'origin';

    -- Update indexes (concurrent rebuild)
    REINDEX CONCURRENTLY idx_sales_transaction_date;
    REINDEX CONCURRENTLY idx_sales_customer_product;

    RETURN v_inserted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Asynchronous metrics update
CREATE OR REPLACE FUNCTION analytics.update_performance_metrics_async(
    p_transaction_id uuid
) RETURNS void AS $$
BEGIN
    -- Queue for asynchronous processing
    INSERT INTO analytics.metrics_update_queue (transaction_id, queued_at)
    VALUES (p_transaction_id, now());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Materialized view for fast analytics
CREATE MATERIALIZED VIEW analytics.product_performance_mv AS
SELECT
    p.product_id,
    p.total_sales,
    p.total_quantity,
    p.last_sale_date,
    ROUND(p.total_sales / p.total_quantity, 2) as avg_sale_price,
    ROUND(p.total_quantity / EXTRACT(days FROM (now() - p.last_sale_date)), 2) as sales_velocity
FROM analytics.product_metrics p
WHERE p.last_sale_date > now() - interval '90 days';

-- Refresh function
CREATE OR REPLACE FUNCTION analytics.refresh_product_performance_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.product_performance_mv;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Bulk Data Loading

```sql
-- Bulk insert thousands of transactions
SELECT analytics.bulk_insert_transactions('[
    {
        "transaction_id": "txn-1",
        "customer_id": "cust-1",
        "product_id": "prod-1",
        "quantity": 2,
        "unit_price": 29.99,
        "total_amount": 59.98,
        "transaction_date": "2024-01-15T10:30:00Z",
        "payment_method": "credit_card",
        "region": "us-west",
        "category": "electronics"
    },
    {
        "transaction_id": "txn-2",
        "customer_id": "cust-2",
        "product_id": "prod-2",
        "quantity": 1,
        "unit_price": 49.99,
        "total_amount": 49.99,
        "transaction_date": "2024-01-15T11:00:00Z",
        "payment_method": "paypal",
        "region": "us-east",
        "category": "books"
    }
]'::jsonb);

-- Returns: 2 (transactions inserted)
```

### Fast Analytics Queries

```sql
-- Top performing products (uses materialized view)
SELECT
    pm.product_id,
    p.name,
    pm.total_sales,
    pm.sales_velocity,
    pm.avg_sale_price
FROM analytics.product_performance_mv pm
JOIN inventory.product p ON pm.product_id = p.id
ORDER BY pm.total_sales DESC
LIMIT 10;

-- Customer segmentation (pre-aggregated)
SELECT
    customer_segment,
    COUNT(*) as customer_count,
    AVG(avg_order_value) as avg_segment_value,
    SUM(total_spent) as total_segment_spent
FROM analytics.customer_metrics
GROUP BY customer_segment
ORDER BY total_segment_spent DESC;

-- Time-based analysis (partition pruning)
SELECT
    DATE_TRUNC('day', transaction_date) as sale_date,
    region,
    category,
    SUM(total_amount) as daily_sales,
    COUNT(*) as transaction_count
FROM analytics.sales_transaction
WHERE transaction_date >= '2024-01-01'
  AND transaction_date < '2024-02-01'
  AND region = 'us-west'
GROUP BY sale_date, region, category
ORDER BY sale_date;
```

### Performance Monitoring

```sql
-- Query performance analysis
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM analytics.sales_transaction
WHERE transaction_date >= '2024-01-01'
  AND region = 'us-west';

-- Index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'analytics'
ORDER BY idx_scan DESC;

-- Partition statistics
SELECT
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup
FROM pg_stat_user_tables
WHERE schemaname = 'analytics'
ORDER BY n_live_tup DESC;
```

## Advanced Performance Techniques

### Query Optimization

```sql
-- Optimized time-series queries with partitioning
CREATE OR REPLACE FUNCTION analytics.get_sales_trend(
    p_start_date timestamp,
    p_end_date timestamp,
    p_region text DEFAULT NULL
) RETURNS TABLE (
    period_date date,
    total_sales decimal,
    transaction_count bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        DATE_TRUNC('day', st.transaction_date)::date,
        SUM(st.total_amount),
        COUNT(*)
    FROM analytics.sales_transaction st
    WHERE st.transaction_date >= p_start_date
      AND st.transaction_date < p_end_date
      AND (p_region IS NULL OR st.region = p_region)
    GROUP BY DATE_TRUNC('day', st.transaction_date)
    ORDER BY period_date;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Parallel query optimization
SET max_parallel_workers_per_gather = 4;
SET max_parallel_workers = 8;

ANALYZE analytics.sales_transaction; -- Update statistics
```

### Caching Strategies

```sql
-- Redis integration for hot data
CREATE OR REPLACE FUNCTION analytics.cache_hot_products()
RETURNS void AS $$
BEGIN
    -- Cache top 100 products in Redis
    PERFORM redis_set('hot_products',
        (SELECT jsonb_agg(
            jsonb_build_object(
                'product_id', product_id,
                'total_sales', total_sales,
                'sales_velocity', sales_velocity
            )
        ) FROM analytics.product_performance_mv
        ORDER BY total_sales DESC
        LIMIT 100)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Archival Strategy

```sql
-- Automatic data archival
CREATE OR REPLACE FUNCTION analytics.archive_old_transactions()
RETURNS integer AS $$
DECLARE
    v_archived_count integer;
BEGIN
    -- Move old data to archive table
    INSERT INTO analytics.sales_transaction_archive
    SELECT * FROM analytics.sales_transaction
    WHERE transaction_date < now() - interval '2 years';

    GET DIAGNOSTICS v_archived_count = ROW_COUNT;

    -- Remove from active table
    DELETE FROM analytics.sales_transaction
    WHERE transaction_date < now() - interval '2 years';

    -- Update partitions
    PERFORM analytics.detach_old_partitions();

    RETURN v_archived_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Performance Benchmarking

### Load Testing

```sql
-- Simulate high-volume transaction processing
CREATE OR REPLACE FUNCTION analytics.load_test_transactions(
    p_transaction_count integer
) RETURNS void AS $$
DECLARE
    v_batch_size integer := 1000;
    v_batches integer := p_transaction_count / v_batch_size;
    v_i integer;
BEGIN
    FOR v_i IN 1..v_batches LOOP
        PERFORM analytics.generate_transaction_batch(v_batch_size);
        COMMIT; -- Commit each batch
    END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Run load test
SELECT analytics.load_test_transactions(100000); -- 100K transactions
```

### Performance Metrics

```sql
-- Transaction processing throughput
SELECT
    date_trunc('hour', transaction_date) as hour,
    COUNT(*) as transactions_per_hour,
    SUM(total_amount) as sales_per_hour,
    AVG(total_amount) as avg_transaction_value
FROM analytics.sales_transaction
WHERE transaction_date > now() - interval '24 hours'
GROUP BY date_trunc('hour', transaction_date)
ORDER BY hour DESC;

-- Query performance trends
SELECT
    query,
    mean_time,
    calls,
    total_time
FROM pg_stat_statements
WHERE query LIKE '%analytics.sales_transaction%'
ORDER BY mean_time DESC
LIMIT 10;
```

## Testing Performance Optimizations

SpecQL generates performance regression tests:

```sql
-- Run performance tests
SELECT * FROM runtests('analytics.performance_test');

-- Example test output:
-- ok 1 - bulk_insert_transactions processes 1000 records in < 1 second
-- ok 2 - partitioned queries use index-only scans
-- ok 3 - materialized view refresh completes in < 30 seconds
-- ok 4 - concurrent index rebuild doesn't block queries
-- ok 5 - async metrics updates don't slow transaction processing
-- ok 6 - query optimization maintains sub-second response times
-- ok 7 - memory usage stays within limits during bulk operations
-- ok 8 - connection pooling handles concurrent load
```

## Key Benefits

✅ **Scalability**: Handles millions of transactions efficiently
✅ **Performance**: Sub-second query response times
✅ **Optimization**: Automatic query and index optimization
✅ **Monitoring**: Comprehensive performance metrics
✅ **Reliability**: High availability with partitioning
✅ **Cost Efficiency**: Optimized resource utilization

## Common Performance Patterns

- **Time-Series**: Partitioning by date, BRIN indexes
- **Analytics**: Materialized views, pre-aggregated metrics
- **Bulk Operations**: COPY mode, trigger disabling, async processing
- **Hot Data**: Caching, specialized indexes
- **Archival**: Automatic data lifecycle management

## Next Steps

- Add [event-driven patterns](event-driven.md) for real-time analytics
- Implement [saga patterns](saga-pattern.md) for complex transactions
- Use [batch operations](../../intermediate/batch-operations.md) for ETL processes

---

**See Also:**
- [Batch Operations](../../intermediate/batch-operations.md)
- [Event-Driven Patterns](event-driven.md)
- [Multi-Entity Operations](../../intermediate/multi-entity.md)
- [Performance Tuning Guide](../../../guides/advanced/performance-tuning.md)