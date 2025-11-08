# Troubleshooting Actions

This guide helps you diagnose and fix common issues with actions in the PrintOptim backend.

## Common Issues

### 1. Action Not Found

**Error**: `function app.create_contact(uuid, jsonb, uuid) does not exist`

**Cause**: Action not generated or migration not applied.

**Solution**:
```bash
# Regenerate schema
uv run python generate_sql.py entities/examples/contact.yaml

# Apply migration
psql -d your_database -f generated/contact.sql
```

### 2. Validation Errors

**Error**: `status: "failed:validation"`

**Cause**: Input data doesn't meet requirements.

**Check**:
- Required fields provided
- Data types correct
- Enum values valid
- References exist and accessible

**Debug**:
```sql
-- Check what validation failed
SELECT * FROM app.tb_mutation_audit_log
WHERE status LIKE 'failed:%'
ORDER BY created_at DESC LIMIT 5;
```

### 3. Foreign Key Errors

**Error**: `status: "failed:reference_not_found"`

**Cause**: Referenced entity doesn't exist or wrong tenant.

**Check**:
```sql
-- Verify reference exists in your tenant
SELECT id FROM crm.tb_company
WHERE id = 'company-uuid'
  AND tenant_id = 'your-tenant-id';
```

### 4. Permission Errors

**Error**: `status: "failed:security:tenant_isolation"`

**Cause**: Attempting to access data from another tenant.

**Check**:
- JWT contains correct `tenant_id`
- User belongs to the tenant
- References point to same tenant

### 5. SQL Execution Errors

**Error**: `status: "failed:constraint:unique_violation"`

**Cause**: Duplicate data violates unique constraints.

**Check**:
```sql
-- Find conflicting records
SELECT * FROM crm.tb_contact
WHERE email = 'duplicate@example.com'
  AND tenant_id = 'your-tenant-id';
```

## Debugging Techniques

### 1. Check Generated SQL

```bash
# View generated migration
cat generated/contact.sql

# Check function signatures
psql -d your_db -c "\df crm.*"
```

### 2. Audit Log Analysis

```sql
-- Recent mutations for entity
SELECT created_at, operation, status, message, extra_metadata
FROM app.tb_mutation_audit_log
WHERE entity_type = 'contact'
  AND tenant_id = 'your-tenant-id'
ORDER BY created_at DESC LIMIT 10;
```

### 3. Function Call Tracing

```sql
-- Enable logging (temporary)
SET log_statement = 'all';
SET log_min_duration_statement = 0;

-- Call your function
SELECT * FROM app.create_contact(
    'tenant-uuid', 'user-uuid',
    '{"email": "test@example.com"}'::jsonb
);

-- Check logs
tail -f /var/log/postgresql/postgresql.log
```

### 4. Test Individual Components

```sql
-- Test Trinity helpers
SELECT crm.contact_pk('contact-uuid', 'tenant-uuid');

-- Test composite type
SELECT '{"email": "test@example.com"}'::app.type_create_contact_input;

-- Test core function directly
SELECT * FROM crm.create_contact(
    'tenant-uuid',
    ('test@example.com', 'lead', null)::app.type_create_contact_input,
    '{"email": "test@example.com"}'::jsonb,
    'user-uuid'
);
```

## Performance Issues

### Slow Queries

**Symptoms**: Actions take >1 second

**Check**:
```sql
-- Query execution plan
EXPLAIN ANALYZE
SELECT * FROM crm.tb_contact
WHERE tenant_id = 'tenant-uuid'
  AND email = 'test@example.com';

-- Check indexes
SELECT * FROM pg_indexes
WHERE tablename = 'tb_contact';
```

**Solutions**:
- Ensure Trinity indexes exist
- Check FK resolution performance
- Consider additional indexes

### High Memory Usage

**Symptoms**: Out of memory errors

**Check**:
- Result set sizes
- JSONB processing
- Large text fields

**Solutions**:
- Add pagination
- Limit result sizes
- Optimize JSONB operations

## Schema Issues

### Migration Conflicts

**Error**: `relation already exists`

**Cause**: Migration applied multiple times or conflicts.

**Solution**:
```sql
-- Check existing objects
\dt crm.*
\df crm.*

-- Clean up if needed (CAUTION: DATA LOSS)
DROP SCHEMA crm CASCADE;
```

### Type Mismatches

**Error**: `cannot cast type text to app.type_create_contact_input`

**Cause**: Composite type definition changed.

**Solution**:
```sql
-- Recreate types
DROP TYPE IF EXISTS app.type_create_contact_input CASCADE;
-- Re-run migration
```

## Network Issues

### Connection Timeouts

**Symptoms**: `connection timeout`

**Check**:
- Database reachable
- Connection pool exhausted
- Network latency

**Solutions**:
- Check database status
- Monitor connection counts
- Implement retry logic

### SSL Issues

**Symptoms**: `SSL connection failed`

**Check**:
- SSL certificates valid
- Client configuration correct
- Server SSL settings

## Development Tips

### Local Testing

```bash
# Start test database
docker-compose up -d postgres-test

# Run tests
uv run pytest tests/integration/actions/ -v

# Check test database
psql -h localhost -p 5433 -U postgres -d test_specql
```

### Logging Configuration

```sql
-- Enable detailed logging
ALTER DATABASE your_db SET log_statement = 'all';
ALTER DATABASE your_db SET log_min_duration_statement = 100; -- ms

-- Check logs
tail -f /var/log/postgresql/postgresql-*.log
```

### Debugging Custom Actions

```yaml
# Add debug logging to actions
actions:
  - name: debug_action
    steps:
      - call: RAISE NOTICE 'Input: %', input_data
      - validate: condition, error: debug_error
      - call: RAISE NOTICE 'Validation passed'
```

## Getting Help

### Information to Provide

When reporting issues, include:

1. **Full error message**
2. **Action YAML definition**
3. **Input data used**
4. **Expected vs actual behavior**
5. **Database logs** (if available)
6. **Generated SQL** (if relevant)

### Support Channels

- **Slack**: #backend-support
- **GitHub Issues**: For bugs
- **Documentation**: Check this guide first
- **Team Leads**: For architectural issues

## Prevention

### Best Practices

1. **Test thoroughly**: Use integration tests
2. **Validate inputs**: Don't trust client data
3. **Monitor performance**: Set up alerts
4. **Keep schemas updated**: Apply migrations promptly
5. **Use audit logs**: Track all changes

### Monitoring

```sql
-- Failed mutations per hour
SELECT
    date_trunc('hour', created_at) as hour,
    status,
    count(*) as count
FROM app.tb_mutation_audit_log
WHERE created_at > now() - interval '24 hours'
GROUP BY hour, status
ORDER BY hour DESC;
```

### Health Checks

```sql
-- Basic connectivity
SELECT 1;

-- Schema health
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname IN ('crm', 'app')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```