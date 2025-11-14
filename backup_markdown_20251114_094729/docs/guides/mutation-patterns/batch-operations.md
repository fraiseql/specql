# Batch Operations Pattern

The **batch operations** pattern handles bulk data processing efficiently. It's designed for mass updates, imports, exports, and any operation that needs to process multiple records while maintaining performance and data consistency.

## 🎯 What You'll Learn

- Batch operation concepts and benefits
- Configuring bulk data processing
- Performance optimization techniques
- Error handling in batch operations
- Monitoring and reporting

## 📋 Prerequisites

- [Pattern basics](getting-started.md)
- Understanding of bulk data operations
- Knowledge of performance considerations

## 💡 Batch Operations Concepts

### What Are Batch Operations?

**Batch operations** process multiple records efficiently:

```yaml
patterns:
  - name: batch_operations
    description: "Bulk user status updates"
    operation: bulk_update_user_status
    batch_size: 100
    parallel: true
    error_handling: continue_on_error
```

**Benefits:**
- **Performance** - Process thousands of records efficiently
- **Consistency** - All-or-nothing or partial success options
- **Monitoring** - Progress tracking and error reporting
- **Resource management** - Controlled memory and CPU usage

### When to Use Batch Operations

| Use Case | Example | Why Batch |
|----------|---------|-----------|
| **Data Migration** | Import 100k users | Efficient bulk loading |
| **Status Updates** | Activate pending accounts | Mass state changes |
| **Data Cleanup** | Remove old logs | Bulk deletion |
| **Report Generation** | Process monthly invoices | Aggregate operations |
| **Cache Updates** | Refresh product prices | Bulk cache invalidation |

## 🏗️ Basic Batch Operation

### Bulk Status Update

```yaml
# entities/user.yaml
name: user
fields:
  id: uuid
  email: string
  status: string
  updated_at: timestamp

patterns:
  - name: batch_operations
    description: "Bulk update user statuses"
    operation: bulk_update_user_status
    target_entity: user

    # Processing configuration
    batch_size: 100
    parallel: false
    timeout: "30 minutes"

    # Operation definition
    operation_type: update
    update_data:
      status: :new_status
      updated_at: "NOW()"
    where_condition: "id = ANY(:user_ids)"

    # Error handling
    error_handling: continue_on_error
    max_errors: 10

    # Progress tracking
    progress_tracking: true
    notify_on_completion: true
```

### Generated Function

```sql
-- Generated batch operation function
CREATE FUNCTION bulk_update_user_status(
  user_ids UUID[],
  new_status TEXT
) RETURNS batch_operation_result AS $$
DECLARE
  result batch_operation_result;
  batch_start_time TIMESTAMP;
  processed_count INTEGER := 0;
  error_count INTEGER := 0;
BEGIN
  result.operation_id := gen_random_uuid();
  result.started_at := NOW();
  result.total_records := array_length(user_ids, 1);

  -- Process in batches
  FOR i IN 0..(array_length(user_ids, 1) / 100) LOOP
    batch_start_time := NOW();

    BEGIN
      -- Update batch
      UPDATE user
      SET status = new_status,
          updated_at = NOW()
      WHERE id = ANY(user_ids[i*100+1:(i+1)*100]);

      processed_count := processed_count + 100;

      -- Log progress
      INSERT INTO batch_operation_log (
        operation_id, batch_number, records_processed,
        started_at, completed_at
      ) VALUES (
        result.operation_id, i, 100,
        batch_start_time, NOW()
      );

    EXCEPTION WHEN OTHERS THEN
      error_count := error_count + 1;

      -- Log error
      INSERT INTO batch_operation_errors (
        operation_id, batch_number, error_message,
        failed_records
      ) VALUES (
        result.operation_id, i, SQLERRM,
        user_ids[i*100+1:(i+1)*100]
      );

      -- Continue or stop based on error handling
      IF error_handling = 'stop_on_error' THEN
        EXIT;
      END IF;
    END LOOP;

  -- Complete operation
  result.completed_at := NOW();
  result.processed_records := processed_count;
  result.error_count := error_count;
  result.status := CASE WHEN error_count = 0 THEN 'completed' ELSE 'completed_with_errors' END;

  RETURN result;
END;
$$ LANGUAGE plpgsql;
```

## ⚙️ Advanced Configuration

### Parallel Processing

```yaml
patterns:
  - name: batch_operations
    description: "Parallel data import"
    operation: import_products
    target_entity: product

    # Parallel processing
    parallel: true
    max_workers: 4
    worker_batch_size: 250

    # Data processing
    operation_type: insert
    insert_data:
      name: :product.name
      price: :product.price
      category_id: :product.category_id
      created_at: "NOW()"

    # Source data
    data_source: :products_array

    # Error handling
    error_handling: collect_errors
    max_errors_per_worker: 5

    # Monitoring
    progress_tracking: true
    heartbeat_interval: "10 seconds"
```

### Complex Operations

```yaml
patterns:
  - name: batch_operations
    description: "Complex user migration"
    operation: migrate_user_data
    target_entity: user

    # Multi-step batch operation
    steps:
      - name: validate_data
        operation_type: select
        select_fields: [id, email, legacy_id]
        where_condition: "legacy_id IS NOT NULL"
        batch_size: 500

      - name: update_profiles
        operation_type: update
        update_data:
          migrated_at: "NOW()"
          migration_version: "2.0"
        where_condition: "id IN (:validated_user_ids)"
        depends_on: validate_data

      - name: cleanup_legacy
        operation_type: delete
        where_condition: "migrated_at < NOW() - INTERVAL '30 days'"
        depends_on: update_profiles
        batch_size: 1000

    # Overall configuration
    batch_size: 100
    parallel: true
    error_handling: stop_on_error
```

### Conditional Batch Operations

```yaml
patterns:
  - name: batch_operations
    description: "Conditional bulk approval"
    operation: bulk_approve_orders
    target_entity: order

    # Conditions
    preconditions:
      - "COUNT(*) FILTER (WHERE status = 'pending') > 0"
      - "CURRENT_USER_HAS_PERMISSION('approve_orders')"

    # Operation
    operation_type: update
    update_data:
      status: approved
      approved_at: "NOW()"
      approved_by: "CURRENT_USER_ID()"
    where_condition: "status = 'pending' AND total_amount <= :max_amount"

    # Limits and controls
    max_records: 1000
    timeout: "15 minutes"
    requires_confirmation: true
```

## 📊 Progress Tracking and Monitoring

### Built-in Monitoring

```yaml
patterns:
  - name: batch_operations
    operation: large_data_import

    # Progress tracking
    progress_tracking: true
    progress_notification_interval: 1000  # Notify every 1000 records

    # Detailed logging
    logging_level: detailed
    log_table: batch_operation_logs

    # Performance metrics
    collect_metrics: true
    metrics_table: batch_performance_metrics

    # Completion notification
    notify_on_completion: true
    notification_channels: [email, webhook]
```

### Monitoring Tables

```sql
-- Progress tracking
CREATE TABLE batch_operation_logs (
  operation_id UUID,
  batch_number INTEGER,
  records_processed INTEGER,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status TEXT
);

-- Error tracking
CREATE TABLE batch_operation_errors (
  operation_id UUID,
  batch_number INTEGER,
  error_message TEXT,
  failed_records JSONB,
  occurred_at TIMESTAMP
);

-- Performance metrics
CREATE TABLE batch_performance_metrics (
  operation_id UUID,
  metric_name TEXT,
  metric_value NUMERIC,
  recorded_at TIMESTAMP
);
```

## 🧪 Testing Batch Operations

### Generated Tests

```bash
# Generate comprehensive tests
specql generate tests entities/user.yaml

# Run tests
specql test run entities/user.yaml
```

**Test Coverage:**
- ✅ **Batch processing** - Correct batch sizes and ordering
- ✅ **Error handling** - Various failure scenarios
- ✅ **Progress tracking** - Monitoring and reporting
- ✅ **Parallel execution** - Worker coordination
- ✅ **Data consistency** - All-or-nothing guarantees
- ✅ **Performance** - Timeout and resource limits

### Manual Testing

```sql
-- Test successful batch operation
SELECT bulk_update_user_status(
  ARRAY[
    'user-1-uuid'::UUID,
    'user-2-uuid'::UUID,
    'user-3-uuid'::UUID
  ]::UUID[],
  'active'
);

-- Check results
SELECT id, status, updated_at FROM user
WHERE id IN ('user-1-uuid', 'user-2-uuid', 'user-3-uuid');

-- Test error handling
SELECT bulk_update_user_status(
  ARRAY['invalid-uuid'::UUID]::UUID[],
  'active'
);

-- Check error logs
SELECT * FROM batch_operation_errors
ORDER BY occurred_at DESC LIMIT 5;
```

## 🚀 Common Use Cases

### Data Import/Export

```yaml
patterns:
  - name: batch_operations
    description: "Import products from CSV"
    operation: import_products_csv
    target_entity: product

    # CSV processing
    data_source: csv_file
    csv_delimiter: ','
    csv_has_header: true

    # Data mapping
    field_mapping:
      name: csv_column_1
      price: csv_column_2
      category: csv_column_3

    # Validation
    validation_rules:
      - "price > 0"
      - "name IS NOT NULL"

    # Processing options
    batch_size: 500
    parallel: true
    skip_invalid_rows: true
    max_errors: 100
```

### User Management

```yaml
patterns:
  - name: batch_operations
    description: "Bulk user deactivation"
    operation: deactivate_inactive_users
    target_entity: user

    # Target selection
    where_condition: |
      last_login_at < NOW() - INTERVAL '1 year'
      AND status = 'active'
      AND is_admin = false

    # Operation
    operation_type: update
    update_data:
      status: inactive
      deactivated_at: "NOW()"
      deactivation_reason: 'automated_inactive_cleanup'

    # Safety limits
    max_records: 10000
    batch_size: 200
    requires_confirmation: true

    # Notification
    notify_on_completion: true
    notification_message: "Deactivated {processed_records} inactive users"
```

### Cache Management

```yaml
patterns:
  - name: batch_operations
    description: "Refresh product cache"
    operation: refresh_product_cache
    target_entity: product_cache

    # Complex refresh logic
    steps:
      - name: identify_stale
        operation_type: select
        select_fields: [product_id]
        where_condition: "last_updated < NOW() - INTERVAL '1 hour'"

      - name: fetch_fresh_data
        operation_type: custom_function
        function: fetch_product_data_from_api
        input: :stale_product_ids

      - name: update_cache
        operation_type: upsert
        upsert_data:
          product_id: :fresh_data.product_id
          name: :fresh_data.name
          price: :fresh_data.price
          last_updated: "NOW()"
        conflict_target: product_id

    # Performance settings
    parallel: true
    batch_size: 50
    timeout: "10 minutes"
```

### Report Generation

```yaml
patterns:
  - name: batch_operations
    description: "Generate monthly invoices"
    operation: generate_monthly_invoices
    target_entity: invoice

    # Complex multi-step process
    steps:
      - name: calculate_usage
        operation_type: custom_function
        function: calculate_customer_usage
        input: {month: :target_month}

      - name: create_invoices
        operation_type: insert
        insert_data:
          customer_id: :usage.customer_id
          month: :target_month
          amount: :usage.total_amount
          status: pending

      - name: generate_pdf
        operation_type: custom_function
        function: generate_invoice_pdf
        input: :created_invoice_ids

      - name: send_notifications
        operation_type: custom_function
        function: send_invoice_notifications
        input: :created_invoice_ids

    # Monitoring
    progress_tracking: true
    collect_metrics: true
    notify_on_completion: true
```

## 🎯 Best Practices

### Performance Optimization
- **Right batch size** - Balance memory vs overhead (100-1000 records)
- **Parallel processing** - Use multiple workers for CPU-bound tasks
- **Index optimization** - Ensure WHERE conditions are indexed
- **Resource limits** - Set timeouts and memory limits

### Error Handling
- **Graceful degradation** - Continue processing on individual failures
- **Detailed logging** - Track exactly what failed and why
- **Retry logic** - Handle transient failures automatically
- **Circuit breakers** - Stop processing on systemic failures

### Monitoring and Alerting
- **Progress tracking** - Know how long operations take
- **Error thresholds** - Alert when error rates are high
- **Performance metrics** - Monitor throughput and latency
- **Completion notifications** - Inform stakeholders of results

### Data Consistency
- **Transaction boundaries** - Decide what should be atomic
- **Idempotency** - Ensure operations can be safely retried
- **Rollback plans** - Know how to undo failed operations
- **Validation** - Check data before processing

## 🆘 Troubleshooting

### "Batch operation timeout"
```yaml
# Increase timeout
patterns:
  - name: batch_operations
    timeout: "2 hours"  # Extend timeout

# Or reduce batch size
patterns:
  - name: batch_operations
    batch_size: 50  # Smaller batches
```

### "Out of memory"
```yaml
# Reduce batch size
patterns:
  - name: batch_operations
    batch_size: 25

# Process sequentially
patterns:
  - name: batch_operations
    parallel: false
```

### "Deadlock detected"
```bash
# Analyze deadlock
psql $DATABASE_URL -c "
SELECT
  blocked_locks.pid AS blocked_pid,
  blocking_locks.pid AS blocking_pid,
  blocked_activity.usename AS blocked_user,
  blocking_activity.usename AS blocking_user,
  blocked_activity.query AS blocked_statement,
  blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;"
```

### "High error rate"
```yaml
# Add more validation
patterns:
  - name: batch_operations
    preconditions:
      - "validate_batch_data(:input_data)"

# Or change error handling
patterns:
  - name: batch_operations
    error_handling: stop_on_error  # Stop immediately
```

## 🎉 Summary

Batch operations provide:
- ✅ **Efficient processing** - Handle large datasets quickly
- ✅ **Resource management** - Controlled CPU and memory usage
- ✅ **Error resilience** - Continue processing despite failures
- ✅ **Progress monitoring** - Track operation status and performance
- ✅ **Flexible configuration** - Adapt to different use cases

## 🚀 What's Next?

- **[Validation](validation.md)** - Data integrity patterns
- **[Composing Patterns](composing-patterns.md)** - Combining multiple patterns
- **[State Machines](state-machines.md)** - Entity lifecycle management
- **[Examples](../../examples/)** - Real-world batch operations

**Ready to process large datasets efficiently? Let's continue! 🚀**