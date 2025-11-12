# Team F Phase 4: Observability Stack Implementation Plan

**Created**: 2025-11-12
**Phase**: 4 of 5
**Status**: Planning
**Complexity**: Medium - Monitoring and logging infrastructure
**Priority**: HIGH - Critical for production operations
**Prerequisites**: Phase 1 (Docker), Phase 2 (OpenTofu) complete

---

## Executive Summary

Implement comprehensive observability stack generation (Prometheus, Grafana, Loki) for monitoring, metrics, and logging. Generate production-ready dashboards, alerts, and log aggregation for FraiseQL applications.

**Goal**: From `deployment.yaml` (10 lines) → Generate observability stack (1000+ lines)

**Key Deliverables**:
1. Prometheus metrics collection setup
2. Grafana dashboards (FraiseQL-specific + infrastructure)
3. Loki log aggregation
4. Alert rules and notification channels
5. OpenTelemetry instrumentation (optional)
6. Cost-saving observability architecture

**Impact**:
- Production-ready monitoring out of the box
- FraiseQL-specific metrics (JSONB performance, GraphQL queries)
- Zero-configuration log aggregation
- Automatic alerting on critical issues
- Cost savings vs commercial APM (save $5-48K/year per FraiseQL README)

---

## 🎯 Phase 4 Objectives

### Core Goals
1. **Prometheus Setup**: Metrics collection and storage
2. **Grafana Dashboards**: Pre-built dashboards for FraiseQL + AWS
3. **Loki Integration**: Log aggregation and querying
4. **Alert Manager**: Critical alerts with multiple channels
5. **Framework-Specific Metrics**: FraiseQL Rust performance, GraphQL queries

### Success Criteria
- ✅ Generate complete observability stack configuration
- ✅ FraiseQL-specific Grafana dashboards included
- ✅ Prometheus scrapes all application metrics
- ✅ Loki aggregates all logs (JSON structured logging)
- ✅ Alerts fire correctly for critical conditions
- ✅ Cost < $50/month (vs $200-500 for commercial APM)

---

## 📋 Technical Design

### Architecture

```
src/generators/deployment/observability/
├── __init__.py
├── observability_orchestrator.py  # Main observability generation orchestrator
├── prometheus/
│   ├── __init__.py
│   ├── prometheus_generator.py    # Prometheus configuration
│   └── scrape_configs.py          # Scrape target definitions
├── grafana/
│   ├── __init__.py
│   ├── grafana_generator.py       # Grafana provisioning
│   ├── dashboards/
│   │   ├── fraiseql_dashboard.py  # FraiseQL-specific dashboard
│   │   ├── postgres_dashboard.py  # PostgreSQL dashboard
│   │   └── aws_dashboard.py       # AWS infrastructure dashboard
│   └── datasources.py             # Datasource configurations
├── loki/
│   ├── __init__.py
│   └── loki_generator.py          # Loki configuration
├── alertmanager/
│   ├── __init__.py
│   ├── alerts_generator.py        # Alert rule generation
│   └── notification_channels.py   # Slack, email, PagerDuty configs
└── templates/
    ├── prometheus/
    │   ├── prometheus.yml.j2
    │   └── alerts.yml.j2
    ├── grafana/
    │   ├── datasources.yml.j2
    │   └── dashboards/
    │       ├── fraiseql.json.j2
    │       ├── postgres.json.j2
    │       └── aws.json.j2
    └── loki/
        └── loki-config.yml.j2
```

### Deployment YAML Extension

```yaml
# deployment.yaml (EXTENDED for Phase 4)
deployment:
  name: my-app
  framework: fraiseql
  pattern: small-saas

# Monitoring configuration
monitoring:
  level: standard  # basic | standard | enterprise
  metrics:
    prometheus: true
    retention: 30d  # Prometheus retention
  logs:
    loki: true
    retention: 30d
  dashboards:
    - fraiseql  # Framework-specific dashboard
    - postgres  # Database dashboard
    - aws       # Infrastructure dashboard
  alerts:
    channels:
      - type: email
        to: ops@example.com
      - type: slack
        webhook_url: https://hooks.slack.com/...
    rules:
      - name: high_cpu
        condition: cpu > 80%
        duration: 5m
        severity: warning
      - name: database_connections
        condition: connections > 80%
        duration: 2m
        severity: critical
      - name: graphql_errors
        condition: error_rate > 5%
        duration: 1m
        severity: critical
```

---

## 🏗️ Implementation Details

### 1. Observability Orchestrator

```python
# src/generators/deployment/observability/observability_orchestrator.py
from pathlib import Path
from typing import Dict, Any

from .prometheus.prometheus_generator import PrometheusGenerator
from .grafana.grafana_generator import GrafanaGenerator
from .loki.loki_generator import LokiGenerator
from .alertmanager.alerts_generator import AlertsGenerator

class ObservabilityOrchestrator:
    """
    Orchestrates observability stack generation.
    Generates Prometheus, Grafana, Loki, and AlertManager configs.
    """

    def __init__(
        self,
        deployment_config: Dict[str, Any],
        framework: str,
        output_dir: Path
    ):
        self.config = deployment_config
        self.framework = framework
        self.output_dir = Path(output_dir) / 'observability'

        # Initialize generators
        self.prometheus_gen = PrometheusGenerator(self.config, framework)
        self.grafana_gen = GrafanaGenerator(self.config, framework)
        self.loki_gen = LokiGenerator(self.config)
        self.alerts_gen = AlertsGenerator(self.config, framework)

    def generate(self) -> Dict[str, Path]:
        """Generate all observability configurations"""
        generated_files = {}

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate Prometheus configuration
        prometheus_dir = self.output_dir / 'prometheus'
        prometheus_dir.mkdir(exist_ok=True)
        generated_files['prometheus'] = self.prometheus_gen.generate(prometheus_dir)

        # Generate Grafana configuration
        grafana_dir = self.output_dir / 'grafana'
        grafana_dir.mkdir(exist_ok=True)
        generated_files['grafana'] = self.grafana_gen.generate(grafana_dir)

        # Generate Loki configuration
        loki_dir = self.output_dir / 'loki'
        loki_dir.mkdir(exist_ok=True)
        generated_files['loki'] = self.loki_gen.generate(loki_dir)

        # Generate Alert Manager configuration
        alerts_dir = self.output_dir / 'alertmanager'
        alerts_dir.mkdir(exist_ok=True)
        generated_files['alerts'] = self.alerts_gen.generate(alerts_dir)

        # Generate docker-compose for observability stack
        generated_files['compose'] = self._generate_observability_compose()

        # Generate README
        generated_files['readme'] = self._generate_readme()

        return generated_files

    def _generate_observability_compose(self) -> Path:
        """Generate docker-compose.yml for observability stack"""
        app_name = self.config['deployment']['name']

        compose = f"""# ============================================
# AUTO-GENERATED BY SPECQL TEAM F
# Observability Stack
# ============================================

version: '3.9'

services:
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${{GRAFANA_ADMIN_PASSWORD}}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
      - loki
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/loki-config.yml
    volumes:
      - ./loki/loki-config.yml:/etc/loki/loki-config.yml:ro
      - loki_data:/loki
    restart: unless-stopped

  promtail:
    image: grafana/promtail:latest
    command: -config.file=/etc/promtail/promtail-config.yml
    volumes:
      - ./loki/promtail-config.yml:/etc/promtail/promtail-config.yml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    depends_on:
      - loki
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
"""

        compose_path = self.output_dir / 'docker-compose.yml'
        compose_path.write_text(compose)
        return compose_path

    def _generate_readme(self) -> Path:
        """Generate observability README"""
        readme = f"""# Observability Stack: {self.config['deployment']['name']}

**Framework**: {self.framework}
**Generated by**: SpecQL Team F

---

## Quick Start

### 1. Start Observability Stack
```bash
cd observability/
docker compose up -d
```

### 2. Access Dashboards

**Grafana**: http://localhost:3000
- Username: `admin`
- Password: (set in `.env` as `GRAFANA_ADMIN_PASSWORD`)

**Prometheus**: http://localhost:9090

**Loki**: http://localhost:3100

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Grafana Dashboards                      │
│  - FraiseQL Performance                  │
│  - PostgreSQL Metrics                    │
│  - AWS Infrastructure                    │
└──────────┬──────────────────────────────┘
           │
           ↓
┌──────────────────────┬──────────────────┐
│  Prometheus          │  Loki            │
│  (Metrics)           │  (Logs)          │
└──────────┬───────────┴──────────┬───────┘
           │                      │
           ↓                      ↓
┌──────────────────────────────────────────┐
│  Application                              │
│  - Prometheus metrics endpoint (/metrics) │
│  - Structured JSON logging                │
└──────────────────────────────────────────┘
```

---

## Cost Savings

**Commercial APM Tools**:
- Datadog: $200-500/month
- New Relic: $150-400/month
- Sentry: $100-300/month

**This Stack**: ~$20/month (AWS hosting)
**Annual Savings**: $5,000-48,000

---

## FraiseQL-Specific Metrics

The FraiseQL dashboard includes:

### Performance Metrics
- **Rust JSONB Processing Time**: How fast Rust transforms JSONB → HTTP
- **Python Overhead**: Time spent in Python vs Rust
- **Query Performance**: P50, P95, P99 latencies
- **Connection Pool**: Active connections, pool exhaustion

### GraphQL Metrics
- **Query Rate**: Queries per second
- **Mutation Rate**: Mutations per second
- **Error Rate**: Failed queries/mutations
- **Query Depth**: Average query depth (security metric)
- **Field Resolution Time**: Slowest resolvers

### Database Metrics
- **JSONB Query Performance**: View query times
- **Connection Pool Stats**: Active, idle, waiting connections
- **Cache Hit Rate**: PostgreSQL buffer cache effectiveness

---

## Alerts

Configured alerts:

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| High CPU | > 80% for 5min | Warning | Email + Slack |
| Database Connections | > 80% for 2min | Critical | Email + Slack |
| GraphQL Errors | > 5% error rate | Critical | Email + Slack + PagerDuty |
| Disk Space | < 10% free | Warning | Email |
| Memory Usage | > 85% for 5min | Warning | Email + Slack |

---

## Log Queries (Loki)

### View Recent Errors
```logql
{{app="{self.config['deployment']['name']}"}} |= "ERROR"
```

### View GraphQL Queries
```logql
{{app="{self.config['deployment']['name']}"}} | json | query != ""
```

### View Slow Queries (> 1s)
```logql
{{app="{self.config['deployment']['name']}"}} | json | duration > 1000
```

---

## Prometheus Queries

### Request Rate
```promql
rate(http_requests_total{{job="fraiseql"}}[5m])
```

### P95 Latency
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Error Rate
```promql
rate(http_requests_total{{job="fraiseql",status=~"5.."}}[5m]) / rate(http_requests_total{{job="fraiseql"}}[5m])
```

---

## Troubleshooting

### No Metrics Showing
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check application metrics endpoint
curl http://localhost:8000/metrics
```

### No Logs in Grafana
```bash
# Check Loki health
curl http://localhost:3100/ready

# Check Promtail
docker compose logs promtail
```

---

## Next Steps

1. Configure alert notification channels
2. Set up retention policies
3. Add custom dashboards for business metrics
4. Configure Grafana auth (LDAP/OAuth)
5. Set up backups for Grafana dashboards

For more information, see: https://github.com/fraiseql/specql
"""

        readme_path = self.output_dir / 'README.md'
        readme_path.write_text(readme)
        return readme_path
```

### 2. FraiseQL Dashboard Generator

```python
# src/generators/deployment/observability/grafana/dashboards/fraiseql_dashboard.py
import json
from typing import Dict, Any

class FraiseQLDashboard:
    """Generate FraiseQL-specific Grafana dashboard"""

    def __init__(self, app_name: str):
        self.app_name = app_name

    def generate(self) -> Dict[str, Any]:
        """Generate FraiseQL dashboard JSON"""
        return {
            "dashboard": {
                "title": f"{self.app_name} - FraiseQL Performance",
                "tags": ["fraiseql", "graphql", "performance"],
                "timezone": "browser",
                "panels": [
                    self._rust_performance_panel(),
                    self._graphql_queries_panel(),
                    self._error_rate_panel(),
                    self._database_connections_panel(),
                    self._jsonb_processing_panel(),
                    self._query_depth_panel(),
                ],
                "templating": {
                    "list": [
                        {
                            "name": "job",
                            "type": "constant",
                            "current": {"value": self.app_name}
                        }
                    ]
                },
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "30s"
            }
        }

    def _rust_performance_panel(self) -> Dict[str, Any]:
        """Panel showing Rust JSONB processing performance"""
        return {
            "title": "Rust JSONB Processing Time",
            "type": "graph",
            "targets": [
                {
                    "expr": 'histogram_quantile(0.95, rate(fraiseql_rust_jsonb_duration_seconds_bucket{job="$job"}[5m]))',
                    "legendFormat": "P95 Rust Processing"
                },
                {
                    "expr": 'histogram_quantile(0.50, rate(fraiseql_rust_jsonb_duration_seconds_bucket{job="$job"}[5m]))',
                    "legendFormat": "P50 Rust Processing"
                }
            ],
            "yaxes": [
                {"format": "s", "label": "Duration"},
                {"format": "short"}
            ],
            "description": "Time spent in Rust processing JSONB → HTTP (should be 7-10x faster than Python)"
        }

    def _graphql_queries_panel(self) -> Dict[str, Any]:
        """Panel showing GraphQL query metrics"""
        return {
            "title": "GraphQL Queries/sec",
            "type": "graph",
            "targets": [
                {
                    "expr": 'rate(graphql_queries_total{job="$job"}[5m])',
                    "legendFormat": "Queries/sec"
                },
                {
                    "expr": 'rate(graphql_mutations_total{job="$job"}[5m])',
                    "legendFormat": "Mutations/sec"
                }
            ],
            "yaxes": [
                {"format": "ops", "label": "Operations"},
                {"format": "short"}
            ]
        }

    def _error_rate_panel(self) -> Dict[str, Any]:
        """Panel showing GraphQL error rates"""
        return {
            "title": "GraphQL Error Rate",
            "type": "graph",
            "targets": [
                {
                    "expr": 'rate(graphql_errors_total{job="$job"}[5m]) / rate(graphql_queries_total{job="$job"}[5m])',
                    "legendFormat": "Error Rate"
                }
            ],
            "yaxes": [
                {"format": "percentunit", "label": "Error Rate"},
                {"format": "short"}
            ],
            "alert": {
                "conditions": [
                    {
                        "evaluator": {"params": [0.05], "type": "gt"},
                        "query": {"params": ["A", "5m", "now"]}
                    }
                ],
                "name": "High GraphQL Error Rate"
            }
        }

    def _database_connections_panel(self) -> Dict[str, Any]:
        """Panel showing database connection pool stats"""
        return {
            "title": "Database Connection Pool",
            "type": "graph",
            "targets": [
                {
                    "expr": 'fraiseql_db_pool_active_connections{job="$job"}',
                    "legendFormat": "Active Connections"
                },
                {
                    "expr": 'fraiseql_db_pool_idle_connections{job="$job"}',
                    "legendFormat": "Idle Connections"
                },
                {
                    "expr": 'fraiseql_db_pool_max_connections{job="$job"}',
                    "legendFormat": "Max Connections"
                }
            ]
        }

    def _jsonb_processing_panel(self) -> Dict[str, Any]:
        """Panel showing JSONB query performance"""
        return {
            "title": "JSONB Query Performance",
            "type": "graph",
            "targets": [
                {
                    "expr": 'histogram_quantile(0.95, rate(fraiseql_db_query_duration_seconds_bucket{job="$job",query_type="jsonb"}[5m]))',
                    "legendFormat": "P95 JSONB Query"
                }
            ],
            "description": "Performance of PostgreSQL JSONB view queries"
        }

    def _query_depth_panel(self) -> Dict[str, Any]:
        """Panel showing GraphQL query depth (security metric)"""
        return {
            "title": "GraphQL Query Depth",
            "type": "graph",
            "targets": [
                {
                    "expr": 'fraiseql_graphql_query_depth{job="$job"}',
                    "legendFormat": "Query Depth"
                }
            ],
            "description": "Average query depth - high values may indicate malicious queries",
            "alert": {
                "conditions": [
                    {
                        "evaluator": {"params": [15], "type": "gt"},
                        "query": {"params": ["A", "5m", "now"]}
                    }
                ],
                "name": "Deep GraphQL Query Detected"
            }
        }
```

---

## 📊 Testing Strategy

### Unit Tests

```python
# tests/unit/generators/deployment/observability/test_observability_orchestrator.py
import pytest
from pathlib import Path
from src.generators.deployment.observability.observability_orchestrator import ObservabilityOrchestrator

def test_generates_all_configs(tmp_path):
    """Test that all observability configs are generated"""
    config = {
        'deployment': {'name': 'test-app', 'framework': 'fraiseql'},
        'monitoring': {'level': 'standard'}
    }

    orchestrator = ObservabilityOrchestrator(config, 'fraiseql', tmp_path)
    generated = orchestrator.generate()

    assert 'prometheus' in generated
    assert 'grafana' in generated
    assert 'loki' in generated
    assert 'alerts' in generated
    assert 'compose' in generated

def test_fraiseql_dashboard_includes_rust_metrics():
    """FraiseQL dashboard should include Rust performance metrics"""
    from src.generators.deployment.observability.grafana.dashboards.fraiseql_dashboard import FraiseQLDashboard

    dashboard = FraiseQLDashboard('test-app')
    dashboard_json = dashboard.generate()

    # Check for Rust-specific panels
    panels = dashboard_json['dashboard']['panels']
    panel_titles = [p['title'] for p in panels]

    assert 'Rust JSONB Processing Time' in panel_titles
    assert 'JSONB Query Performance' in panel_titles
```

---

## 📝 Deliverables

### Code Files
1. ✅ `src/generators/deployment/observability/observability_orchestrator.py`
2. ✅ `src/generators/deployment/observability/prometheus/prometheus_generator.py`
3. ✅ `src/generators/deployment/observability/grafana/grafana_generator.py`
4. ✅ `src/generators/deployment/observability/grafana/dashboards/fraiseql_dashboard.py`
5. ✅ `src/generators/deployment/observability/loki/loki_generator.py`
6. ✅ `src/generators/deployment/observability/alertmanager/alerts_generator.py`

### Templates
7. ✅ Prometheus configuration templates
8. ✅ Grafana dashboard JSON templates (FraiseQL, PostgreSQL, AWS)
9. ✅ Loki configuration templates
10. ✅ AlertManager rule templates

### Tests
11. ✅ Unit tests for all generators
12. ✅ Integration tests for observability stack

### Documentation
13. ✅ `docs/guides/DEPLOYMENT_OBSERVABILITY.md`
14. ✅ Auto-generated observability README

---

## 🚀 Implementation Phases

### Week 1: Prometheus + Grafana (Days 1-3)
**TDD Cycles for metrics collection**

### Week 2: Loki + Dashboards (Days 4-6)
**TDD Cycles for log aggregation + FraiseQL dashboard**

### Week 3: Alerts + Integration (Days 7-9)
**TDD Cycles for alerting + E2E tests**

---

## ✅ Success Metrics

### Quantitative
- ✅ Generate complete observability stack from 10-line YAML
- ✅ FraiseQL dashboard shows Rust performance metrics
- ✅ Prometheus scrapes metrics successfully
- ✅ Loki aggregates logs successfully
- ✅ Alerts fire within 1 minute of condition
- ✅ Monthly cost < $50

### Qualitative
- ✅ Production-ready monitoring out of the box
- ✅ Framework-specific insights (Rust performance)
- ✅ Clear visibility into application health
- ✅ Cost savings vs commercial APM

---

**Status**: Ready for Implementation (After Phase 1-2)
**Priority**: HIGH - Critical for production operations
**Estimated Effort**: 3 weeks (phased TDD approach)
**Risk Level**: Medium - Observability complexity
