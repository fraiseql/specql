# Monitoring Guide

> **Production observability for SpecQL applications—know before your users do**

## Overview

Comprehensive monitoring requires tracking:
- ✅ **Application Metrics** - Response times, error rates
- ✅ **Database Metrics** - Query performance, connection pool
- ✅ **GraphQL Metrics** - Query complexity, resolver performance
- ✅ **Business Metrics** - User actions, conversion rates
- ✅ **Infrastructure Metrics** - CPU, memory, disk

**Goal**: <1 minute MTTD (Mean Time To Detect), <5 minute MTTR (Mean Time To Resolve)

---

## Quick Start

### Prometheus + Grafana Stack

```yaml
# docker-compose.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    environment:
      DATA_SOURCE_NAME: "postgresql://user:password@postgres:5432/myapp?sslmode=disable"
    ports:
      - "9187:9187"

volumes:
  prometheus-data:
  grafana-data:
```

```bash
docker-compose up -d
```

**Access**:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

---

## Application Metrics

### Install prom-client

```bash
npm install prom-client
```

### Basic Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

// Create registry
const register = new Registry();

// HTTP request counter
const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status'],
  registers: [register],
});

// HTTP request duration
const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'route', 'status'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
  registers: [register],
});

// Active connections
const activeConnections = new Gauge({
  name: 'http_connections_active',
  help: 'Number of active HTTP connections',
  registers: [register],
});

// Middleware to track metrics
app.use((req, res, next) => {
  const start = Date.now();

  // Increment active connections
  activeConnections.inc();

  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;

    // Record metrics
    httpRequestsTotal.inc({
      method: req.method,
      route: req.route?.path || req.path,
      status: res.statusCode,
    });

    httpRequestDuration.observe(
      {
        method: req.method,
        route: req.route?.path || req.path,
        status: res.statusCode,
      },
      duration
    );

    // Decrement active connections
    activeConnections.dec();
  });

  next();
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

---

### GraphQL-Specific Metrics

```typescript
import { ApolloServerPlugin } from 'apollo-server-plugin-base';
import { Counter, Histogram } from 'prom-client';

const graphqlQueries = new Counter({
  name: 'graphql_queries_total',
  help: 'Total GraphQL queries',
  labelNames: ['operation', 'status'],
});

const graphqlDuration = new Histogram({
  name: 'graphql_query_duration_seconds',
  help: 'GraphQL query duration',
  labelNames: ['operation'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
});

const graphqlErrors = new Counter({
  name: 'graphql_errors_total',
  help: 'Total GraphQL errors',
  labelNames: ['operation', 'error_code'],
});

const metricsPlugin: ApolloServerPlugin = {
  async requestDidStart(requestContext) {
    const start = Date.now();

    return {
      async didEncounterErrors(context) {
        context.errors?.forEach(error => {
          graphqlErrors.inc({
            operation: context.operationName || 'unknown',
            error_code: error.extensions?.code || 'UNKNOWN',
          });
        });
      },

      async willSendResponse(context) {
        const duration = (Date.now() - start) / 1000;

        graphqlQueries.inc({
          operation: context.operationName || 'unknown',
          status: context.errors ? 'error' : 'success',
        });

        graphqlDuration.observe(
          { operation: context.operationName || 'unknown' },
          duration
        );
      },
    };
  },
};

const server = new ApolloServer({
  schema,
  plugins: [metricsPlugin],
});
```

---

## Database Monitoring

### PostgreSQL Metrics

**Key metrics to track**:

```sql
-- Active connections
SELECT count(*) AS active_connections
FROM pg_stat_activity
WHERE state = 'active';

-- Long-running queries (> 5 seconds)
SELECT
  pid,
  now() - query_start AS duration,
  state,
  query
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;

-- Table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;

-- Cache hit ratio
SELECT
  'index hit rate' AS name,
  (sum(idx_blks_hit)) / nullif(sum(idx_blks_hit + idx_blks_read), 0) * 100 AS ratio
FROM pg_stat_user_indexes
UNION ALL
SELECT
  'table hit rate' AS name,
  sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 AS ratio
FROM pg_stat_user_tables;

-- Slow queries (from pg_stat_statements)
SELECT
  query,
  calls,
  total_exec_time / 1000 AS total_time_sec,
  mean_exec_time / 1000 AS avg_time_ms,
  max_exec_time / 1000 AS max_time_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

---

### Custom Database Metrics

**Track action performance**:

```sql
CREATE TABLE IF NOT EXISTS core.action_metrics (
    metric_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    action_name TEXT NOT NULL,
    duration_ms NUMERIC NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'error')),
    error_code TEXT,
    executed_at TIMESTAMP DEFAULT NOW(),
    executed_by UUID,
    tenant_id UUID
);

CREATE INDEX idx_action_metrics_action ON core.action_metrics(action_name);
CREATE INDEX idx_action_metrics_executed_at ON core.action_metrics(executed_at);
CREATE INDEX idx_action_metrics_status ON core.action_metrics(status);
```

**Auto-track in actions**:

```sql
CREATE OR REPLACE FUNCTION app.qualify_lead(p_contact_id UUID)
RETURNS app.mutation_result AS $$
DECLARE
    v_start_time TIMESTAMP;
    v_duration_ms NUMERIC;
    v_result app.mutation_result;
BEGIN
    v_start_time := clock_timestamp();

    -- Action logic
    BEGIN
        -- ... action steps ...

        v_result.status := 'success';
        v_result.code := 'lead_qualified';

    EXCEPTION WHEN OTHERS THEN
        v_result.status := 'error';
        v_result.code := SQLSTATE;
        v_result.message := SQLERRM;
    END;

    v_duration_ms := EXTRACT(MILLISECOND FROM clock_timestamp() - v_start_time);

    -- Record metrics
    INSERT INTO core.action_metrics (
        action_name,
        duration_ms,
        status,
        error_code,
        executed_by,
        tenant_id
    ) VALUES (
        'qualify_lead',
        v_duration_ms,
        v_result.status,
        CASE WHEN v_result.status = 'error' THEN v_result.code ELSE NULL END,
        current_setting('app.current_user_id', true)::UUID,
        current_setting('app.current_tenant_id', true)::UUID
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

## Log Aggregation

### Structured Logging

```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'specql-app' },
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

// Log with context
logger.info('Lead qualified', {
  action: 'qualify_lead',
  contact_id: '550e8400-...',
  duration_ms: 42,
  user_id: 'user-123',
  tenant_id: 'tenant-456',
});

// Log errors with stack traces
logger.error('Action failed', {
  action: 'qualify_lead',
  error: error.message,
  stack: error.stack,
  contact_id: '550e8400-...',
});
```

---

### Centralized Logging (ELK Stack)

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
```

**Logstash config**:
```conf
# logstash.conf
input {
  file {
    path => "/var/log/app/combined.log"
    codec => json
  }
}

filter {
  # Parse timestamp
  date {
    match => [ "timestamp", "ISO8601" ]
  }

  # Extract duration into numeric field
  mutate {
    convert => { "duration_ms" => "integer" }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "specql-logs-%{+YYYY.MM.dd}"
  }
}
```

---

## Alerting

### Prometheus Alerts

**prometheus-alerts.yml**:
```yaml
groups:
  - name: specql_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(graphql_errors_total[5m]))
            /
            sum(rate(graphql_queries_total[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High GraphQL error rate ({{ $value }})"
          description: "Error rate is {{ $value }}% (threshold: 5%)"

      # Slow queries
      - alert: SlowQueries
        expr: |
          histogram_quantile(0.95,
            rate(graphql_query_duration_seconds_bucket[5m])
          ) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile query time > 1s"
          description: "P95 query time: {{ $value }}s"

      # Database connections
      - alert: HighDatabaseConnections
        expr: pg_stat_activity_count{state="active"} > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of active DB connections"
          description: "{{ $value }} active connections"

      # Low cache hit ratio
      - alert: LowCacheHitRatio
        expr: |
          (
            redis_keyspace_hits_total
            /
            (redis_keyspace_hits_total + redis_keyspace_misses_total)
          ) < 0.90
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Redis cache hit ratio < 90%"
          description: "Hit ratio: {{ $value }}%"
```

---

### Alertmanager Configuration

**alertmanager.yml**:
```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h

  routes:
    - match:
        severity: critical
      receiver: pagerduty
      continue: true

    - match:
        severity: warning
      receiver: slack

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops@company.com'
        from: 'alerts@company.com'
        smarthost: smtp.gmail.com:587
        auth_username: 'alerts@company.com'
        auth_password: 'password'

  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'
```

---

## Dashboards

### Grafana Dashboard (JSON)

**SpecQL Overview Dashboard**:

```json
{
  "dashboard": {
    "title": "SpecQL Application Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(graphql_errors_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "P95 Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(graphql_query_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "pg_stat_activity_count{state='active'}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Cache Hit Ratio",
        "targets": [
          {
            "expr": "redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

---

## Health Checks

### Endpoint Implementation

```typescript
app.get('/health', async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    checks: {},
  };

  try {
    // Check database
    await db.query('SELECT 1');
    health.checks.database = { status: 'up' };
  } catch (error) {
    health.status = 'unhealthy';
    health.checks.database = { status: 'down', error: error.message };
  }

  try {
    // Check Redis
    await redis.ping();
    health.checks.redis = { status: 'up' };
  } catch (error) {
    health.status = 'degraded';
    health.checks.redis = { status: 'down', error: error.message };
  }

  // Return appropriate status code
  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
});

// Readiness check (for Kubernetes)
app.get('/ready', async (req, res) => {
  try {
    // Check if app is ready to accept traffic
    await db.query('SELECT 1');
    res.status(200).send('Ready');
  } catch (error) {
    res.status(503).send('Not ready');
  }
});

// Liveness check (for Kubernetes)
app.get('/live', (req, res) => {
  // Simple check that process is alive
  res.status(200).send('Alive');
});
```

---

## Distributed Tracing

### OpenTelemetry Integration

```bash
npm install @opentelemetry/api @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node
```

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';

const sdk = new NodeSDK({
  traceExporter: new JaegerExporter({
    endpoint: 'http://localhost:14268/api/traces',
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-pg': {},
      '@opentelemetry/instrumentation-http': {},
      '@opentelemetry/instrumentation-graphql': {},
    }),
  ],
});

sdk.start();
```

**Trace example**:
```
HTTP Request → GraphQL Query → Resolver → Database Query
  100ms         50ms            30ms        15ms
```

---

## Best Practices

### ✅ DO

1. **Monitor the 4 golden signals**: Latency, Traffic, Errors, Saturation
2. **Set up alerts** for critical metrics (error rate, response time)
3. **Use structured logging** (JSON format)
4. **Track business metrics** (not just technical)
5. **Implement health checks** for orchestrators (Kubernetes, etc.)
6. **Monitor database** performance (slow queries, connections)
7. **Set SLOs** (Service Level Objectives) and measure against them
8. **Create runbooks** for common alerts

---

### ❌ DON'T

1. **Don't alert on everything** (alert fatigue)
2. **Don't ignore patterns** (investigate recurring issues)
3. **Don't skip dashboards** (visualize trends)
4. **Don't store logs forever** (set retention policies)
5. **Don't monitor in silos** (correlate metrics, logs, traces)

---

## Monitoring Checklist

### Essential

- [ ] Application metrics (requests, errors, latency)
- [ ] Database metrics (connections, slow queries)
- [ ] Health check endpoints (/health, /ready, /live)
- [ ] Error tracking (Sentry, Rollbar)
- [ ] Alerting configured (critical alerts only)

### Recommended

- [ ] Distributed tracing (OpenTelemetry/Jaeger)
- [ ] Log aggregation (ELK/Loki)
- [ ] Custom dashboards (Grafana)
- [ ] Business metrics tracking
- [ ] Performance budgets set
- [ ] Runbooks documented

---

## Next Steps

### Learn More

- **[Performance Tuning](performance-tuning.md)** - Optimize based on metrics
- **[Deployment Guide](deployment.md)** - Production deployment
- **[Security Hardening](security-hardening.md)** - Security monitoring

### Tools

- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **Jaeger** - Distributed tracing
- **ELK Stack** - Log aggregation
- **Sentry** - Error tracking

---

## Summary

You've learned:
- ✅ Application and database metrics
- ✅ Log aggregation with ELK
- ✅ Alerting with Prometheus
- ✅ Dashboards with Grafana
- ✅ Health checks for orchestrators
- ✅ Distributed tracing

**Key Takeaway**: Observability is about metrics, logs, and traces working together—monitor proactively, not reactively.

**Next**: Deploy to production with [Deployment Guide](deployment.md) →

---

**Monitor everything—you can't fix what you can't see.**
