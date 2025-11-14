# Tutorial 5: Production Deployment (60 minutes)

Deploy your SpecQL application to production with proper configuration, monitoring, security, and scalability considerations.

## 🎯 What You'll Learn

- Production database setup
- Security configuration
- Monitoring and alerting
- Backup and recovery
- Performance optimization
- CI/CD deployment

## 📋 Prerequisites

- Completed [Tutorial 4: Testing](../04-testing.md)
- Access to production infrastructure
- Understanding of production operations

## 🏗️ Step 1: Production Database Setup

Set up a production-ready PostgreSQL database:

### Database Configuration

```bash
# Create production database
createdb specql_prod

# Set production environment variables
export DATABASE_URL="postgresql://app_user:secure_password@localhost:5432/specql_prod"
export SPECQL_ENV=production

# Initialize SpecQL for production
specql init --env production
```

### Database Security

```sql
-- Connect as superuser
psql postgres

-- Create application user with limited privileges
CREATE USER specql_app WITH PASSWORD 'secure_password_here';
GRANT CONNECT ON DATABASE specql_prod TO specql_app;

-- Create schema and grant permissions
\c specql_prod
CREATE SCHEMA app;
CREATE SCHEMA orders;
CREATE SCHEMA crm;

GRANT USAGE ON SCHEMA app, orders, crm TO specql_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app, orders, crm TO specql_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA app, orders, crm TO specql_app;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO specql_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT USAGE ON SEQUENCES TO specql_app;
```

### Connection Pooling

```sql
-- Install pgBouncer for connection pooling
sudo apt-get install pgbouncer

-- Configure pgBouncer (/etc/pgbouncer/pgbouncer.ini)
[databases]
specql_prod = host=localhost port=5432 dbname=specql_prod

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
reserve_pool_size = 5
```

## 🚀 Step 2: Deploy Application Schema

Deploy your schema to production:

```bash
# Generate production schema
specql generate schema --env production

# Validate schema before deployment
specql validate

# Create deployment script
cat > deploy_schema.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting production deployment..."

# Run pre-deployment checks
echo "📋 Running pre-deployment checks..."
specql validate
specql test unit  # Run fast unit tests

# Backup current database
echo "💾 Creating database backup..."
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Deploy schema changes
echo "🏗️ Deploying schema changes..."
specql db migrate

# Run integration tests
echo "🧪 Running integration tests..."
specql test integration

# Run performance tests
echo "⚡ Running performance tests..."
specql test performance --duration 60

echo "✅ Deployment completed successfully!"
EOF

chmod +x deploy_schema.sh
```

## 🔒 Step 3: Security Configuration

Implement production security measures:

### Row Level Security (RLS)

```sql
-- Enable RLS on tables
ALTER TABLE orders.order ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm.contact ENABLE ROW LEVEL SECURITY;

-- Create security policies
CREATE POLICY order_isolation ON orders.order
    FOR ALL USING (customer_id = current_user_id());

CREATE POLICY contact_access ON crm.contact
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM user_permissions
            WHERE user_id = current_user_id()
        )
    );
```

### Audit Logging

```sql
-- Create audit table
CREATE TABLE audit_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name text NOT NULL,
    operation text NOT NULL,
    old_values jsonb,
    new_values jsonb,
    user_id uuid,
    timestamp timestamp DEFAULT now()
);

-- Create audit function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS trigger AS $$
BEGIN
    INSERT INTO audit_log (table_name, operation, old_values, new_values, user_id)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        CASE WHEN TG_OP != 'INSERT' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW) ELSE NULL END,
        current_user_id()
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add audit triggers
CREATE TRIGGER audit_orders_trigger
    AFTER INSERT OR UPDATE OR DELETE ON orders.order
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

### API Security

```yaml
# specql.yaml - Production configuration
environment: production
security:
  enable_rls: true
  enable_audit: true
  rate_limiting:
    enabled: true
    requests_per_minute: 100
  authentication:
    required: true
    jwt_secret: "${JWT_SECRET}"
    token_expiry: "24h"

database:
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600
```

## 📊 Step 4: Monitoring Setup

Implement comprehensive monitoring:

### Database Monitoring

```sql
-- Create monitoring views
CREATE VIEW system_health AS
SELECT
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables;

-- Query performance monitoring
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

-- Connection monitoring
CREATE VIEW connection_stats AS
SELECT
    datname,
    usename,
    client_addr,
    state,
    state_change,
    EXTRACT(epoch FROM (now() - state_change)) as state_duration
FROM pg_stat_activity
WHERE datname = current_database();
```

### Application Metrics

```bash
# Install monitoring tools
pip install prometheus_client psycopg2-binary

# Create metrics collection
cat > monitoring.py << 'EOF'
from prometheus_client import Counter, Histogram, Gauge
import psycopg2
import time

# Business metrics
orders_created = Counter('orders_created_total', 'Total orders created')
orders_completed = Counter('orders_completed_total', 'Total orders completed')
order_value = Histogram('order_value', 'Order value distribution',
                       buckets=[10, 50, 100, 500, 1000, 5000])

# System metrics
db_connections = Gauge('db_connections_active', 'Active database connections')
response_time = Histogram('http_request_duration_seconds', 'Request duration',
                         ['method', 'endpoint'])

def collect_metrics():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # Collect business metrics
    cur.execute("SELECT COUNT(*) FROM orders.order WHERE created_at > now() - interval '1 hour'")
    orders_created.inc(cur.fetchone()[0])

    # Collect system metrics
    cur.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE datname = %s", [os.environ['PGDATABASE']])
    db_connections.set(cur.fetchone()[0])

    cur.close()
    conn.close()

if __name__ == '__main__':
    collect_metrics()
EOF
```

### Alerting

```yaml
# alerting_rules.yml
groups:
  - name: specql_production
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status="500"}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: SlowQueries
        expr: pg_stat_statements_mean_time > 5000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"

      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
```

## 💾 Step 5: Backup and Recovery

Implement robust backup strategy:

### Automated Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/specql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump --no-owner --no-privileges --clean --if-exists $DATABASE_URL > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Upload to cloud storage (optional)
# aws s3 cp $BACKUP_FILE.gz s3://specql-backups/

echo "Backup completed: $BACKUP_FILE.gz"
EOF

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Point-in-Time Recovery

```sql
-- Enable WAL archiving
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/archive/%f';

-- Create recovery configuration
cat > recovery.conf << EOF
restore_command = 'cp /var/lib/postgresql/archive/%f %p'
recovery_target_time = '2024-01-15 14:30:00'
EOF
```

### Disaster Recovery Testing

```bash
# Test backup restoration
cat > test_recovery.sh << 'EOF'
#!/bin/bash

TEST_DB="specql_recovery_test"
BACKUP_FILE="/var/backups/specql/backup_$(date +%Y%m%d)_*.sql.gz"

# Create test database
createdb $TEST_DB

# Restore from backup
gunzip -c $BACKUP_FILE | psql $TEST_DB

# Run validation tests
export DATABASE_URL="postgresql://localhost/$TEST_DB"
specql test integration

# Cleanup
dropdb $TEST_DB

echo "Recovery test completed successfully"
EOF
```

## ⚡ Step 6: Performance Optimization

Optimize for production workloads:

### Database Tuning

```sql
-- Production PostgreSQL configuration
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- SpecQL specific optimizations
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET effective_io_concurrency = 200;
```

### Query Optimization

```sql
-- Create optimized indexes for production queries
CREATE INDEX CONCURRENTLY idx_orders_status_created ON orders.order (status, created_at DESC);
CREATE INDEX CONCURRENTLY idx_orders_customer_recent ON orders.order (customer_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_contacts_company_lead_score ON crm.contact (company_id, lead_score DESC);

-- Analyze tables for query planning
ANALYZE orders.order;
ANALYZE crm.contact;
ANALYZE crm.deal;
```

### Caching Strategy

```sql
-- Create materialized views for expensive queries
CREATE MATERIALIZED VIEW mv_order_summary AS
SELECT
    DATE_TRUNC('day', created_at) as order_date,
    COUNT(*) as orders_count,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value
FROM orders.order
WHERE created_at > now() - interval '90 days'
GROUP BY DATE_TRUNC('day', created_at);

-- Refresh materialized view
CREATE OR REPLACE FUNCTION refresh_order_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_order_summary;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh
SELECT cron.schedule('refresh-order-summary', '0 */4 * * *', 'SELECT refresh_order_summary()');
```

## 🚀 Step 7: CI/CD Deployment

Set up automated deployment pipeline:

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup SpecQL
        run: pip install specql
      - name: Run Tests
        run: specql test
      - name: Validate Schema
        run: specql validate

  deploy:
    needs: test
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to Production
        run: |
          # Update application
          aws ecs update-service --cluster specql-prod --service specql-app --force-new-deployment

          # Run database migrations
          aws ecs run-task --cluster specql-prod --task-definition specql-migration --overrides '{
            "containerOverrides": [{
              "name": "migration",
              "environment": [
                {"name": "DATABASE_URL", "value": "${{ secrets.DATABASE_URL }}"}
              ]
            }]
          }'

      - name: Health Check
        run: |
          # Wait for deployment
          aws ecs wait services-stable --cluster specql-prod --services specql-app

          # Run smoke tests
          curl -f https://api.specql.com/health || exit 1
```

### Blue-Green Deployment

```bash
# Blue-green deployment script
cat > blue_green_deploy.sh << 'EOF'
#!/bin/bash

ENVIRONMENT=$1
CURRENT_COLOR=$(get_current_color $ENVIRONMENT)
NEW_COLOR=$(if [ "$CURRENT_COLOR" = "blue" ]; then echo "green"; else echo "blue"; fi)

echo "🚀 Starting blue-green deployment to $NEW_COLOR environment..."

# Deploy to new environment
deploy_to_environment $NEW_COLOR

# Run tests against new environment
run_smoke_tests $NEW_COLOR

# Switch traffic
switch_traffic $NEW_COLOR

# Monitor for 5 minutes
monitor_health $NEW_COLOR 300

# If successful, decommission old environment
if [ $? -eq 0 ]; then
    decommission_environment $CURRENT_COLOR
    echo "✅ Deployment successful!"
else
    # Rollback
    switch_traffic $CURRENT_COLOR
    echo "❌ Deployment failed, rolled back to $CURRENT_COLOR"
    exit 1
fi
EOF
```

## 📈 Step 8: Production Monitoring

Set up comprehensive production monitoring:

### Application Performance Monitoring

```bash
# Install APM tools
pip install datadog py-spy

# Configure APM
cat > apm_config.py << 'EOF'
import datadog
from ddtrace import tracer

# Configure DataDog
datadog.initialize(
    api_key=os.environ['DD_API_KEY'],
    app_key=os.environ['DD_APP_KEY']
)

# Instrument database calls
tracer.configure(hostname=os.environ['DD_AGENT_HOST'])

# Custom metrics
@tracer.wrap()
def process_order(order_data):
    # Business logic here
    pass
EOF
```

### Log Aggregation

```bash
# Configure structured logging
cat > logging_config.py << 'EOF'
import logging
import json
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Structured logging helper
def log_business_event(event_type, **kwargs):
    logger.info('Business event', extra={
        'event_type': event_type,
        'event_data': kwargs
    })
EOF
```

### Dashboard Creation

```sql
-- Create monitoring dashboard data
CREATE VIEW production_dashboard AS
SELECT
    'orders_today' as metric,
    COUNT(*) as value
FROM orders.order
WHERE created_at >= CURRENT_DATE
UNION ALL
SELECT
    'revenue_today',
    COALESCE(SUM(total_amount), 0)
FROM orders.order
WHERE created_at >= CURRENT_DATE
UNION ALL
SELECT
    'active_users',
    COUNT(DISTINCT customer_id)
FROM orders.order
WHERE created_at >= now() - interval '24 hours'
UNION ALL
SELECT
    'avg_response_time',
    AVG(response_time_ms)
FROM api_request_logs
WHERE created_at >= now() - interval '1 hour';
```

## 🎉 Success!

You've successfully deployed to production with:

✅ **Production Database**: Properly configured PostgreSQL
✅ **Security**: RLS, audit logging, authentication
✅ **Monitoring**: Comprehensive metrics and alerting
✅ **Backup & Recovery**: Automated backups and testing
✅ **Performance**: Optimized queries and caching
✅ **CI/CD**: Automated deployment pipeline
✅ **Observability**: APM, logging, dashboards

## 🧪 Test Your Knowledge

Try these production exercises:

1. **Implement canary deployments**: Roll out changes to 5% of users first
2. **Add feature flags**: Control feature rollout without redeployment
3. **Set up multi-region deployment**: Deploy across multiple AWS regions
4. **Implement circuit breakers**: Handle downstream service failures
5. **Create runbooks**: Document incident response procedures

## 📚 Next Steps

- [Advanced Deployment](../../../guides/deployment/) - More deployment patterns
- [Security Guide](../../../guides/security/) - Advanced security topics
- [Performance Tuning](../../../guides/performance/) - Production optimization

## 💡 Pro Tips

- Always test deployments in staging first
- Use infrastructure as code (Terraform, CloudFormation)
- Implement proper secrets management (AWS Secrets Manager, Vault)
- Set up automated rollback procedures
- Monitor costs and optimize resource usage
- Document all production procedures

---

**Time completed**: 60 minutes
**Production ready**: Database, security, monitoring, backups
**CI/CD pipeline**: Automated testing and deployment
**Monitoring**: APM, alerting, dashboards configured
**Documentation**: Runbooks and procedures created