# Universal Infrastructure YAML Specification

## Overview

The Universal Infrastructure YAML format provides a platform-agnostic way to define infrastructure that can be converted to multiple cloud platforms and deployment targets.

## Basic Structure

```yaml
service: backend_api
description: "FastAPI backend with PostgreSQL and Redis"
service_type: api
provider: aws
region: us-east-1
environment: production

# ============================================================================
# Compute Configuration
# ============================================================================
compute:
  instances: 3
  cpu: 2
  memory: 4GB
  disk: 50GB

  auto_scale:
    enabled: true
    min_instances: 2
    max_instances: 10
    cpu_target: 70
    memory_target: 80

  spot_instances: false
  availability_zones:
    - us-east-1a
    - us-east-1b
    - us-east-1c

# ============================================================================
# Container Configuration
# ============================================================================
container:
  image: mycompany/backend-api
  tag: v1.2.3
  port: 8000

  environment:
    ENV: production
    LOG_LEVEL: INFO

  secrets:
    DATABASE_URL: ${secrets.database_url}
    API_KEY: ${secrets.api_key}

  resources:
    cpu_limit: 2
    memory_limit: 4GB
    cpu_request: 1
    memory_request: 2GB

  health_check:
    path: /health
    interval: 30

  readiness_check:
    path: /ready
    interval: 10

# ============================================================================
# Database Configuration
# ============================================================================
database:
  type: postgresql
  version: "15"
  storage: 100GB
  instance_class: db.t3.large

  high_availability:
    multi_az: true
    replicas: 2

  backups:
    enabled: true
    retention_days: 30
    window: "03:00-04:00"

  security:
    encryption_at_rest: true
    encryption_in_transit: true
    publicly_accessible: false

  performance:
    iops: 3000
    storage_type: gp3

# Additional databases (Redis for caching)
additional_databases:
  - type: redis
    version: "7.0"
    instance_class: cache.t3.medium
    replicas: 1

# ============================================================================
# Networking
# ============================================================================
network:
  vpc_cidr: 10.0.0.0/16
  public_subnets:
    - 10.0.1.0/24
    - 10.0.2.0/24
  private_subnets:
    - 10.0.10.0/24
    - 10.0.20.0/24

  nat_gateway: true
  custom_domain: api.example.com

# Load Balancer
load_balancer:
  enabled: true
  type: application
  https: true
  certificate_domain: api.example.com

  health_check:
    path: /health
    interval: 30
    healthy_threshold: 2
    unhealthy_threshold: 3

  sticky_sessions: false
  cross_zone: true

# CDN
cdn:
  enabled: true
  origin_domain: api.example.com
  price_class: PriceClass_100
  cache_ttl: 3600
  compress: true

# ============================================================================
# Storage
# ============================================================================
volumes:
  - name: app-storage
    size: 50GB
    mount_path: /data
    storage_class: ssd

object_storage:
  buckets:
    - name: user-uploads
      versioning: true
      public_access: false
      encryption: true
      lifecycle_rules:
        - transition_to_glacier_after_days: 90
        - expire_after_days: 365

# ============================================================================
# Observability
# ============================================================================
observability:
  logging:
    enabled: true
    retention_days: 30
    level: INFO

  metrics:
    enabled: true
    provider: prometheus

  tracing:
    enabled: true
    provider: jaeger
    sample_rate: 0.1

  alerts:
    - name: high_cpu
      condition: "cpu > 80%"
      duration: 300
      channels: [pagerduty, slack]

    - name: high_error_rate
      condition: "error_rate > 1%"
      duration: 60
      channels: [pagerduty]

    - name: database_connections_high
      condition: "db_connections > 90%"
      duration: 300
      channels: [slack]

# ============================================================================
# Security
# ============================================================================
security:
  secrets_provider: aws_secrets
  secrets:
    database_url: /prod/backend-api/database_url
    api_key: /prod/backend-api/api_key

  service_account: backend-api-sa
  iam_roles:
    - s3-read-write
    - secrets-manager-read

  allowed_ip_ranges:
    - 0.0.0.0/0  # For production, restrict to known IPs

  waf: true
  encryption_at_rest: true
  encryption_in_transit: true
  audit_logging: true

# ============================================================================
# Tags
# ============================================================================
tags:
  Project: backend-api
  Team: platform
  Environment: production
  CostCenter: engineering

# ============================================================================
# Pattern Metadata
# ============================================================================
pattern:
  category: web_application
  tags: [fastapi, postgresql, redis, aws, production]
  estimated_monthly_cost: 1500  # USD
  best_practices:
    - "Multi-AZ deployment for high availability"
    - "Auto-scaling based on CPU and memory"
    - "Automated backups with 30-day retention"
    - "Encryption at rest and in transit"
    - "Comprehensive monitoring and alerting"
```

## Field Reference

### Service Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service` | string | Yes | Service name |
| `description` | string | No | Service description |
| `service_type` | enum | No | `web_app`, `api`, `worker`, `data_pipeline`, `ml_service` |
| `provider` | enum | No | `aws`, `gcp`, `azure`, `kubernetes`, `docker` |
| `region` | string | No | Cloud region (e.g., `us-east-1`) |
| `environment` | enum | No | `development`, `staging`, `production` |

### Compute Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instances` | integer | No | Number of instances (default: 1) |
| `cpu` | number | No | CPU cores (default: 1.0) |
| `memory` | string | No | Memory size (e.g., "2GB", "4GB") |
| `disk` | string | No | Disk size (e.g., "20GB", "50GB") |
| `auto_scale.enabled` | boolean | No | Enable auto-scaling |
| `auto_scale.min_instances` | integer | No | Minimum instances |
| `auto_scale.max_instances` | integer | No | Maximum instances |
| `auto_scale.cpu_target` | integer | No | CPU target percentage |
| `auto_scale.memory_target` | integer | No | Memory target percentage |
| `spot_instances` | boolean | No | Use spot/preemptible instances |
| `availability_zones` | array | No | List of availability zones |

### Container Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | string | Yes | Container image |
| `tag` | string | No | Image tag (default: "latest") |
| `port` | integer | No | Container port (default: 8000) |
| `environment` | object | No | Environment variables |
| `secrets` | object | No | Secret references |
| `volumes` | array | No | Volume mounts |
| `cpu_limit` | number | No | CPU limit |
| `memory_limit` | string | No | Memory limit |
| `cpu_request` | number | No | CPU request |
| `memory_request` | string | No | Memory request |
| `health_check_path` | string | No | Health check endpoint |
| `readiness_check_path` | string | No | Readiness check endpoint |

### Database Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | enum | Yes | `postgresql`, `mysql`, `mongodb`, `redis`, `elasticsearch` |
| `version` | string | Yes | Database version |
| `storage` | string | No | Storage size (default: "50GB") |
| `instance_class` | string | No | Cloud-specific instance type |
| `multi_az` | boolean | No | Multi-AZ deployment |
| `replicas` | integer | No | Number of replicas |
| `backup_enabled` | boolean | No | Enable backups (default: true) |
| `backup_retention_days` | integer | No | Backup retention (default: 7) |
| `encryption_at_rest` | boolean | No | Encrypt data at rest (default: true) |
| `publicly_accessible` | boolean | No | Public access (default: false) |

### Networking Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vpc_cidr` | string | No | VPC CIDR block |
| `public_subnets` | array | No | Public subnet CIDR blocks |
| `private_subnets` | array | No | Private subnet CIDR blocks |
| `enable_nat_gateway` | boolean | No | Enable NAT gateway |
| `custom_domain` | string | No | Custom domain name |

### Load Balancer Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | No | Enable load balancer (default: true) |
| `type` | enum | No | `application`, `network` |
| `https` | boolean | No | Enable HTTPS (default: true) |
| `certificate_domain` | string | No | SSL certificate domain |
| `health_check_path` | string | No | Health check path |
| `sticky_sessions` | boolean | No | Enable sticky sessions |
| `cross_zone` | boolean | No | Enable cross-zone load balancing |

### Observability Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `logging.enabled` | boolean | No | Enable logging (default: true) |
| `logging.retention_days` | integer | No | Log retention (default: 30) |
| `metrics.enabled` | boolean | No | Enable metrics (default: true) |
| `metrics.provider` | enum | No | Metrics provider |
| `tracing.enabled` | boolean | No | Enable tracing |
| `tracing.provider` | enum | No | Tracing provider |
| `alerts` | array | No | Alert configurations |

### Security Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `secrets_provider` | enum | No | Secrets provider |
| `secrets` | object | No | Secret references |
| `service_account` | string | No | Service account name |
| `iam_roles` | array | No | IAM roles |
| `allowed_ip_ranges` | array | No | Allowed IP ranges |
| `enable_waf` | boolean | No | Enable WAF |
| `encryption_at_rest` | boolean | No | Encrypt at rest (default: true) |
| `audit_logging` | boolean | No | Enable audit logging (default: true) |

## Examples

### Simple Web Application

```yaml
service: my-web-app
provider: aws
region: us-east-1

compute:
  instances: 2
  cpu: 1
  memory: 2GB

database:
  type: postgresql
  version: "15"
  storage: 50GB

load_balancer:
  enabled: true
  https: true
```

### Microservices with Kubernetes

```yaml
service: user-service
provider: kubernetes
service_type: api

container:
  image: mycompany/user-service
  port: 8080

database:
  type: postgresql
  version: "15"

observability:
  metrics:
    enabled: true
    provider: prometheus
  tracing:
    enabled: true
    provider: jaeger
```

### Data Pipeline

```yaml
service: data-pipeline
provider: aws
service_type: data_pipeline

compute:
  instances: 1
  cpu: 4
  memory: 16GB
  disk: 200GB

database:
  type: postgresql
  version: "15"
  storage: 500GB

object_storage:
  buckets:
    - name: data-lake
      versioning: true
      encryption: true
```