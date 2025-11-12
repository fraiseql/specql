# SpecQL Deployment Patterns Proposal

## 🎯 Vision

**User writes 15 lines of deployment intent → Framework generates production-ready infrastructure**

```yaml
# deployment.yaml (USER WRITES THIS)
deployment:
  pattern: small-saas
  platform: aws
  database:
    size: small
    backup: daily
  application:
    instances: 2
  monitoring: standard
```

**Framework auto-generates:**
- 🐳 Multi-stage Dockerfile (Node.js + PostgreSQL clients)
- 📦 docker-compose.yaml (local dev + production-like)
- 🏗️ OpenTofu modules (AWS RDS, ECS, ALB, VPC)
- 🔧 Ansible playbooks (server hardening, monitoring)
- 🚀 GitHub Actions workflows (CI/CD)
- 📊 Observability stack (Prometheus, Grafana, Loki)
- 🔒 Secrets management (AWS Secrets Manager / Vault)
- 📝 Environment configs (.env templates)

---

## 🏗️ Architecture: Team F - Deployment Generator

```
SpecQL YAML → Teams A-E → Database + GraphQL
                ↓
         deployment.yaml
                ↓
      Team F: Deployment Generator
                ↓
   ┌────────────┼────────────┐
   ↓            ↓            ↓
Docker      OpenTofu      CI/CD
Config      Modules       Pipelines
   └────────────┼────────────┘
                ↓
    Production Infrastructure
```

---

## 📋 Deployment Patterns (Pre-Configured)

### Pattern 1: `hobby-project`
**Use Case**: Solo dev, low cost, simple setup

**Framework-Specific Stacks:**

**FraiseQL** (Python GraphQL Framework):
- Docker Compose (Python 3.13 + PostgreSQL + FraiseQL)
- Caddy (auto-SSL reverse proxy)
- FraiseQL server (FastAPI + Rust-optimized JSONB)
- GraphQL Playground built-in
- Basic monitoring (Prometheus + Uptime Kuma)

**Django** (future):
- Docker Compose (Python + PostgreSQL + Gunicorn)
- Caddy (auto-SSL)
- Django Admin
- Basic monitoring

**Example:**
```yaml
deployment:
  framework: fraiseql  # Auto-selects appropriate stack
  pattern: hobby-project
  domain: myapp.com
  # Framework handles: SSL, backups, basic monitoring
```

**Generated (FraiseQL):**
```bash
docker-compose.yml
├── fraiseql-server (Node.js + Apollo)
├── postgres (PostgreSQL 16)
└── caddy (reverse proxy + SSL)
```

### Pattern 2: `small-saas`
**Use Case**: Startup MVP, <1000 users, cost-effective

**Generated Stack:**
- AWS: RDS (db.t4g.micro), ECS Fargate (2 instances), ALB
- OpenTofu modules for AWS resources
- Ansible for bastion host setup
- GitHub Actions (test → build → deploy)
- CloudWatch + Grafana Cloud

**Example:**
```yaml
deployment:
  pattern: small-saas
  platform: aws
  region: us-east-1
  database:
    size: small  # maps to db.t4g.micro
    backup: daily
  application:
    instances: 2
    memory: 512Mi
  monitoring: standard  # CloudWatch + basic Grafana
```

### Pattern 3: `production-saas`
**Use Case**: Production app, >10k users, HA required

**Generated Stack:**
- AWS: Multi-AZ RDS, ECS with autoscaling, CloudFront CDN
- Redis cluster (session/cache)
- S3 for file storage
- Comprehensive observability (Prometheus, Grafana, Loki, Tempo)
- Advanced CI/CD (blue-green deployments)
- WAF + Shield

**Example:**
```yaml
deployment:
  pattern: production-saas
  platform: aws
  regions:
    - us-east-1  # primary
    - eu-west-1  # DR
  database:
    size: large
    replicas: 2
    backup: continuous
  application:
    instances: 5
    autoscale:
      min: 5
      max: 50
      target_cpu: 70
  cache: redis-cluster
  storage: s3
  monitoring: enterprise
  security:
    waf: enabled
    ddos_protection: enabled
```

### Pattern 4: `kubernetes`
**Use Case**: Complex apps, microservices, K8s infrastructure

**Generated Stack:**
- Helm charts for app deployment
- PostgreSQL operator (CrunchyData or CloudNativePG)
- Ingress controller (Nginx or Traefik)
- Cert-manager (Let's Encrypt)
- Prometheus + Grafana + Loki (Kube-Prometheus-Stack)
- ArgoCD (GitOps)

**Example:**
```yaml
deployment:
  pattern: kubernetes
  cluster: existing  # or 'create' to gen Terraform for EKS/GKE
  namespace: myapp-prod
  database:
    operator: cloudnative-pg
    size: medium
  application:
    replicas: 3
    hpa: enabled
  ingress:
    class: nginx
    ssl: cert-manager
  monitoring: kube-prometheus-stack
```

---

## 🔗 Framework-Specific Deployment Details

### FraiseQL Framework

**What is FraiseQL:**
FraiseQL is a **production-ready Python GraphQL framework** built on FastAPI with Rust-optimized JSONB processing. It's a complete runtime GraphQL server.

**Tech Stack:**
- **Runtime**: Python 3.13+ with Rust extensions (via maturin)
- **Web Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **GraphQL**: graphql-core with custom Rust-optimized JSONB resolver
- **Database**: PostgreSQL 16+ with psycopg3 (connection pooling)
- **Performance**: Rust pipeline for JSONB → HTTP (zero Python serialization overhead)
- **Database Migrations**: SQL files (direct execution via SpecQL)
- **Frontend**: Auto-generated TypeScript + Apollo hooks
- **Monitoring**: Built-in Prometheus metrics, structured logging (structlog)

**Why Rust?**
- PostgreSQL returns JSONB from views
- Rust transforms JSONB → HTTP response (7-10x faster than Python JSON)
- No ORM overhead, no Python object serialization
- Security: Explicit field contracts in PostgreSQL JSONB views

**Key Features:**
- ⚡ **Rust-optimized pipeline** - Direct JSONB → HTTP (no Python overhead)
- 🔒 **Secure by design** - PostgreSQL views define explicit field contracts
- 🤖 **AI-native** - Simple decorators (`@type`, `@query`, `@mutation`)
- 🔍 **Advanced filtering** - Full-text search, JSONB queries, array ops, regex
- 📊 **Built-in observability** - Prometheus, structured logs, cryptographic audit chains

**Generated Docker Stack:**
```yaml
# docker-compose.yml (FraiseQL)
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  fraiseql-server:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      PORT: 8000
      PYTHON_ENV: development
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app  # For development hot reload
    command: fraiseql run --host 0.0.0.0 --port 8000 --reload

  caddy:
    image: caddy:2-alpine
    depends_on:
      - fraiseql-server
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    environment:
      DOMAIN: ${DOMAIN:-localhost}

volumes:
  postgres_data:
  caddy_data:
```

**Generated Dockerfile (FraiseQL):**
```dockerfile
# Multi-stage build for FraiseQL (Python + Rust extensions)
FROM python:3.13-slim AS builder

# Install build dependencies for Rust + PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . "$HOME/.cargo/env" \
    && rm -rf /var/lib/apt/lists/*

# Add Rust to PATH
ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /app

# Install uv for faster Python dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY Cargo.toml Cargo.lock ./

# Install Python dependencies (including fraiseql with Rust extensions)
RUN uv pip install --system --no-cache-dir -e .

# Production stage
FROM python:3.13-slim AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 fraiseql && \
    mkdir /app && \
    chown -R fraiseql:fraiseql /app

WORKDIR /app

# Copy built packages from builder (includes Rust .so files)
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=fraiseql:fraiseql ./app ./app
COPY --chown=fraiseql:fraiseql ./migrations ./migrations

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHON_ENV=production

# Switch to non-root user
USER fraiseql

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# FraiseQL server (FastAPI + Rust-optimized JSONB processing)
EXPOSE 8000
CMD ["fraiseql", "run", "--host", "0.0.0.0", "--port", "8000"]
```

**Generated Caddyfile (auto-SSL):**
```caddyfile
{$DOMAIN} {
    # Reverse proxy to FraiseQL FastAPI server
    reverse_proxy fraiseql-server:8000

    # Enable compression
    encode gzip

    # Headers for GraphQL
    header {
        # Security headers
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"

        # CORS for GraphQL (adjust for production)
        Access-Control-Allow-Origin "*"
        Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Access-Control-Allow-Headers "Content-Type, Authorization"
    }

    # Health check endpoint
    handle /health {
        reverse_proxy fraiseql-server:8000
    }

    # GraphQL endpoint
    handle /graphql {
        reverse_proxy fraiseql-server:8000
    }

    # GraphQL playground (disable in production)
    handle /playground {
        reverse_proxy fraiseql-server:8000
    }
}
```

**Monitoring Stack (FraiseQL):**
- **Prometheus** built-in metrics exporter (FastAPI middleware)
  - GraphQL query performance
  - Resolver timings (Rust-optimized JSONB processing)
  - Database connection pool stats (psycopg3)
  - HTTP request metrics (Uvicorn/Starlette)
  - Custom business metrics
- **Grafana** dashboards with FraiseQL-specific panels:
  - JSONB processing performance (Rust vs Python comparison)
  - PostgreSQL view query patterns
  - Cache hit rates
  - Security events (failed auth, invalid queries)
- **Structured logging** (structlog)
  - JSON formatted logs
  - Correlation IDs for request tracing
  - Cryptographic audit chains (SHA-256 + HMAC)
- Optional: **OpenTelemetry** for distributed tracing
- Optional: **Sentry** for error tracking

---

### Django Framework (Future)

**Tech Stack:**
- **Runtime**: Python 3.12+
- **WSGI Server**: Gunicorn
- **Task Queue**: Celery + Redis
- **Database Client**: psycopg3
- **Database Migrations**: Django migrations
- **Admin**: Django Admin
- **Monitoring**: Prometheus + Django metrics

**Generated Docker Stack:**
```yaml
# docker-compose.yml (Django)
services:
  postgres:
    image: postgres:16-alpine

  redis:
    image: redis:7-alpine

  django-web:
    build: .
    command: gunicorn myapp.wsgi:application
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"

  celery-worker:
    build: .
    command: celery -A myapp worker
    depends_on:
      - redis
```

---

### Rails Framework (Future)

**Tech Stack:**
- **Runtime**: Ruby 3.2+
- **App Server**: Puma
- **Background Jobs**: Sidekiq + Redis
- **Database Client**: pg gem
- **Database Migrations**: Rails migrations
- **Monitoring**: Prometheus + Rails metrics

---

## 🛠️ Tool Selection (Opinionated)

### Docker & Orchestration
- **Docker**: Standard containerization
- **docker-compose**: Local dev + simple production
- **Kubernetes/Helm**: Complex production

### Infrastructure as Code
- **OpenTofu** (NOT Terraform): Open-source, FOSS guarantee
  - Why: Post-HashiCorp license change, OpenTofu is the community choice
  - AWS/GCP/Azure providers fully supported
  - Modules for: VPC, RDS, ECS, ALB, CloudFront, etc.

### Configuration Management
- **Ansible**: Server provisioning, OS hardening
  - Pre-built playbooks for:
    - PostgreSQL tuning
    - Security hardening (UFW, fail2ban, SSH)
    - Monitoring agent setup

### CI/CD
- **GitHub Actions**: Primary (most users)
- **GitLab CI**: Alternative (if requested)
- Pre-configured workflows:
  - Lint → Test → Build → Deploy
  - Database migrations
  - Rollback procedures

### Observability
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards
- **Loki**: Log aggregation
- **Tempo**: Distributed tracing (optional)
- **OpenTelemetry**: Instrumentation

### Reverse Proxy / Load Balancer
- **Caddy**: Simple setups (auto-SSL, minimal config)
- **Nginx**: Production (more control)
- **Traefik**: Kubernetes
- **AWS ALB**: Cloud-native

---

## 📁 Generated File Structure

```
generated/
├── docker/
│   ├── Dockerfile                    # Multi-stage build
│   ├── docker-compose.dev.yaml       # Local development
│   ├── docker-compose.prod.yaml      # Production-like local
│   └── .dockerignore
├── infrastructure/
│   ├── opentofu/
│   │   ├── main.tf                   # Root module
│   │   ├── modules/
│   │   │   ├── networking/           # VPC, subnets, security groups
│   │   │   ├── database/             # RDS with best practices
│   │   │   ├── application/          # ECS/EKS cluster
│   │   │   ├── monitoring/           # CloudWatch, Grafana
│   │   │   └── cdn/                  # CloudFront distribution
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.example
│   ├── ansible/
│   │   ├── playbooks/
│   │   │   ├── setup-bastion.yml
│   │   │   ├── harden-server.yml
│   │   │   └── install-monitoring.yml
│   │   └── inventory/
│   └── kubernetes/
│       ├── helm/
│       │   ├── Chart.yaml
│       │   ├── values.yaml
│       │   └── templates/
│       └── manifests/
├── ci-cd/
│   ├── github-actions/
│   │   ├── test.yml
│   │   ├── build-deploy.yml
│   │   └── rollback.yml
│   └── gitlab-ci/
│       └── .gitlab-ci.yml
├── observability/
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── application.json
│   │   │   └── database.json
│   │   └── datasources.yml
│   └── loki/
│       └── loki-config.yml
├── config/
│   ├── .env.example
│   ├── .env.production.example
│   └── secrets/
│       └── secrets.yaml.example
└── docs/
    ├── DEPLOYMENT.md
    ├── RUNBOOK.md
    └── ROLLBACK.md
```

---

## 🎯 Integration with SpecQL Framework System

### Framework-Aware Deployment Defaults

**Building on Issue #9's framework system**, deployment patterns are **framework-aware**:

```python
# src/cli/framework_defaults.py (EXTENDED)
FRAMEWORK_DEFAULTS = {
    "fraiseql": {
        # Database generation (existing)
        "include_tv": True,  # FraiseQL uses JSONB views for GraphQL
        "trinity_pattern": True,
        # Deployment defaults (NEW)
        "deployment": {
            "runtime": "python",
            "version": "3.13",
            "requires": ["postgresql", "rust"],  # Rust for maturin build
            "docker_base": "python:3.13-slim",
            "services": ["postgres", "fraiseql-server", "caddy"],
            "framework_package": "fraiseql[all]",  # Includes FastAPI, Rust extensions
            "asgi_server": "uvicorn",
            "monitoring": "prometheus+structlog",
            "build_system": "maturin",  # Rust extension builder
        }
    },
    "django": {
        "include_tv": False,
        "trinity_pattern": False,
        # Deployment defaults
        "deployment": {
            "runtime": "python",
            "version": "3.12",
            "requires": ["postgresql", "redis"],
            "docker_base": "python:3.12-slim",
            "services": ["postgres", "redis", "gunicorn", "celery"],
            "framework_package": "django>=5.0",
            "wsgi_server": "gunicorn",
            "monitoring": "prometheus+django",
        }
    },
}
```

### CLI Integration

```bash
# Deployment generation uses same --framework flag
specql deploy generate --framework fraiseql
# → Generates Node.js + PostgreSQL + FraiseQL stack

specql deploy generate --framework django
# → Generates Python + PostgreSQL + Django stack

# Override framework defaults
specql deploy generate --framework fraiseql --platform aws --pattern production-saas
```

---

## 🎯 SpecQL DSL Extension

### Deployment Manifest (`deployment.yaml`)

```yaml
# Meta
deployment:
  name: my-saas-app
  framework: fraiseql  # Inherits from --framework flag or explicit here
  pattern: small-saas  # hobby-project | small-saas | production-saas | kubernetes
  version: "1.0.0"

# Platform
platform:
  provider: aws  # aws | gcp | azure | digitalocean | bare-metal
  region: us-east-1
  availability_zones: 2

# Database Configuration
database:
  engine: postgresql
  version: "16"
  size: small  # small | medium | large | xlarge
  storage: 100  # GB
  backup:
    frequency: daily  # hourly | daily | weekly
    retention: 30  # days
  replicas: 1  # read replicas
  multi_az: false

# Application Configuration
application:
  runtime: nodejs  # nodejs | python | go
  version: "20"
  instances: 2
  memory: 512Mi
  cpu: 0.5
  autoscale:
    enabled: true
    min: 2
    max: 10
    target_cpu: 70
    target_memory: 80
  health_check:
    path: /health
    interval: 30
    timeout: 5

# Networking
networking:
  vpc_cidr: "10.0.0.0/16"
  public_subnets: 2
  private_subnets: 2
  nat_gateway: true
  load_balancer:
    type: application  # application | network
    ssl: true
    certificate: letsencrypt  # or arn:aws:acm:...

# Storage (Optional)
storage:
  type: s3  # s3 | gcs | azure-blob | local
  buckets:
    - name: user-uploads
      public: false
      versioning: true
    - name: backups
      lifecycle: 90  # days

# Cache (Optional)
cache:
  enabled: true
  type: redis  # redis | memcached
  size: small
  replicas: 1

# Monitoring
monitoring:
  level: standard  # basic | standard | enterprise
  metrics:
    prometheus: true
    cloudwatch: true
  logs:
    aggregator: loki  # loki | cloudwatch | elasticsearch
    retention: 30  # days
  dashboards:
    grafana: true
  alerts:
    - name: high_cpu
      condition: cpu > 80
      duration: 5m
      channel: email
    - name: database_connections
      condition: connections > 80%
      channel: slack

# Security
security:
  ssl: true
  certificate_provider: letsencrypt  # letsencrypt | aws-acm
  waf: false
  ddos_protection: false
  secrets_manager: aws-secrets  # aws-secrets | vault | env-file
  encryption_at_rest: true

# CI/CD
cicd:
  provider: github-actions  # github-actions | gitlab-ci | circleci
  triggers:
    - push:
        branch: main
        action: deploy
    - pull_request:
        action: test
  environments:
    - name: staging
      auto_deploy: true
    - name: production
      auto_deploy: false
      approval_required: true
  migrations:
    auto_run: false  # require manual approval
    rollback_on_failure: true

# Environments
environments:
  - name: development
    variables:
      NODE_ENV: development
      LOG_LEVEL: debug
  - name: staging
    variables:
      NODE_ENV: staging
      LOG_LEVEL: info
  - name: production
    variables:
      NODE_ENV: production
      LOG_LEVEL: warn
    secrets:
      - DATABASE_URL
      - JWT_SECRET
      - STRIPE_API_KEY
```

---

## 🚀 Usage Flow

### 1. Define Deployment Intent
```bash
# User creates minimal deployment.yaml
cat > deployment.yaml <<EOF
deployment:
  pattern: small-saas
  platform: aws
  database:
    size: small
  application:
    instances: 2
EOF
```

### 2. Generate Infrastructure
```bash
# Generate all infrastructure code
specql deploy generate deployment.yaml

# Output:
# ✅ Generated Docker files
# ✅ Generated OpenTofu modules (AWS)
# ✅ Generated GitHub Actions workflows
# ✅ Generated monitoring configs
# ✅ Generated deployment docs
```

### 3. Review & Customize (Optional)
```bash
# Review generated infrastructure
ls generated/infrastructure/opentofu/

# Make custom adjustments if needed
vim generated/infrastructure/opentofu/modules/database/main.tf
```

### 4. Deploy
```bash
# Initialize infrastructure
cd generated/infrastructure/opentofu
tofu init
tofu plan
tofu apply

# Deploy application
cd ../../
docker compose -f docker/docker-compose.prod.yaml up -d
```

### 5. Monitor
```bash
# Access Grafana dashboard
open http://monitoring.myapp.com

# View logs
docker compose logs -f app
```

---

## 🏗️ Implementation Plan (Team F)

### Phase 1: Docker & Local Dev ✨
**Goal**: Generate production-ready Docker setup

**Generates:**
- Multi-stage Dockerfile (Node.js + PostgreSQL)
- docker-compose.dev.yaml (local dev with hot reload)
- docker-compose.prod.yaml (production-like)
- Health check endpoints
- Environment config templates

**Pattern Library:**
- `nodejs-graphql-postgresql`
- `python-fastapi-postgresql`
- `go-gqlgen-postgresql`

### Phase 2: OpenTofu Modules 🏗️
**Goal**: Generate cloud infrastructure (AWS first)

**Generates:**
- VPC + networking (subnets, security groups, NAT)
- RDS (PostgreSQL with best practices)
- ECS Fargate (or EC2 instances)
- Application Load Balancer
- CloudWatch monitoring
- S3 buckets (backups, uploads)
- IAM roles & policies

**Pattern Library:**
- `aws-ecs-rds` (small-saas)
- `aws-eks-rds` (kubernetes)
- `aws-multi-region` (production-saas)

### Phase 3: CI/CD Pipelines 🚀
**Goal**: Automated deployments

**Generates:**
- GitHub Actions workflows
  - PR: lint → test
  - Main: build → deploy → smoke test
  - Rollback workflow
- Database migration steps
- Environment promotion (staging → prod)

### Phase 4: Observability Stack 📊
**Goal**: Production monitoring & debugging

**Generates:**
- Prometheus config (metrics collection)
- Grafana dashboards (app + DB performance)
- Loki config (log aggregation)
- Alert rules (CPU, memory, DB connections, errors)
- OpenTelemetry instrumentation

### Phase 5: Advanced Patterns 🎯
**Goal**: Enterprise features

**Generates:**
- Kubernetes Helm charts
- Multi-region deployments
- Blue-green deployment scripts
- Disaster recovery procedures
- Auto-scaling policies

---

## 🎨 Generated Docker Example

### Multi-Stage Dockerfile (Auto-Generated)

```dockerfile
# ============================================
# AUTO-GENERATED BY SPECQL - DO NOT EDIT
# Pattern: small-saas
# Generated: 2025-11-12
# ============================================

# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install dependencies
RUN npm install -g pnpm && \
    pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build application
RUN pnpm build

# Stage 2: Production
FROM node:20-alpine AS production

# Install PostgreSQL client (for migrations)
RUN apk add --no-cache postgresql-client

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Copy built assets from builder
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

# Copy database migrations
COPY --chown=nodejs:nodejs db/migrations ./db/migrations

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:4000/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1); })"

# Switch to non-root user
USER nodejs

# Expose application port
EXPOSE 4000

# Start application
CMD ["node", "dist/index.js"]
```

---

## 🌐 Generated OpenTofu Example

### RDS Module (Auto-Generated)

```hcl
# ============================================
# AUTO-GENERATED BY SPECQL - DO NOT EDIT
# Pattern: small-saas
# Module: RDS PostgreSQL
# Generated: 2025-11-12
# ============================================

resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.app_name}-db-subnet"
    ManagedBy   = "SpecQL"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.app_name}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from application"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.app_name}-rds-sg"
    ManagedBy   = "SpecQL"
    Environment = var.environment
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.app_name}-postgres"

  # Engine
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = var.instance_size  # db.t4g.micro for "small"
  allocated_storage    = var.storage_size   # 100 GB
  storage_type         = "gp3"
  storage_encrypted    = true

  # Database
  db_name  = replace(var.app_name, "-", "_")
  username = var.db_username
  password = var.db_password  # From AWS Secrets Manager

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = var.multi_az  # false for small-saas

  # Backups
  backup_retention_period = var.backup_retention  # 30 days
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.app_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  # Best Practices
  auto_minor_version_upgrade = true
  deletion_protection       = var.environment == "production" ? true : false
  copy_tags_to_snapshot     = true

  # Parameters
  parameter_group_name = aws_db_parameter_group.main.name

  tags = {
    Name        = "${var.app_name}-postgres"
    ManagedBy   = "SpecQL"
    Environment = var.environment
  }
}

# Optimized parameters for FraiseQL/SpecQL workloads
resource "aws_db_parameter_group" "main" {
  name   = "${var.app_name}-postgres16"
  family = "postgres16"

  # Connection pooling optimizations
  parameter {
    name  = "max_connections"
    value = "200"
  }

  # Memory optimizations
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/4096}"  # 25% of RAM
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/2048}"  # 50% of RAM
  }

  # Query performance
  parameter {
    name  = "random_page_cost"
    value = "1.1"  # SSD optimization
  }

  # Logging (for FraiseQL debugging)
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries > 1s
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  tags = {
    Name        = "${var.app_name}-postgres16"
    ManagedBy   = "SpecQL"
    Environment = var.environment
  }
}

# Outputs
output "endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}
```

---

## 🚀 Generated GitHub Actions Example

```yaml
# ============================================
# AUTO-GENERATED BY SPECQL - DO NOT EDIT
# Pattern: small-saas
# Workflow: Build & Deploy
# Generated: 2025-11-12
# ============================================

name: Build & Deploy

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: my-saas-app
  ECS_SERVICE: my-saas-app-service
  ECS_CLUSTER: my-saas-app-cluster
  ECS_TASK_DEFINITION: .aws/task-definition.json

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Run database migrations
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
        run: pnpm run migrate

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
        run: pnpm test

      - name: Run linter
        run: pnpm lint

  build-and-deploy:
    name: Build & Deploy to AWS
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image to Amazon ECR
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

      - name: Run database migrations
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          docker run --rm \
            -e DATABASE_URL=$DATABASE_URL \
            ${{ steps.build-image.outputs.image }} \
            npm run migrate

      - name: Fill in the new image ID in the Amazon ECS task definition
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: ${{ env.ECS_TASK_DEFINITION }}
          container-name: app
          image: ${{ steps.build-image.outputs.image }}

      - name: Deploy Amazon ECS task definition
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true

      - name: Smoke test
        run: |
          ENDPOINT=$(aws elbv2 describe-load-balancers \
            --names my-saas-app-alb \
            --query 'LoadBalancers[0].DNSName' \
            --output text)
          curl -f https://$ENDPOINT/health || exit 1

      - name: Notify deployment
        if: success()
        run: echo "Deployment successful!"
```

---

## 🎯 Key Benefits

### For Users:
1. **15 lines YAML → Production infrastructure** (100x leverage, like SpecQL)
2. **No DevOps expertise required** (best practices encoded)
3. **Consistent deployments** (same pattern everywhere)
4. **Fast iteration** (regenerate anytime)

### For SpecQL Ecosystem:
1. **Complete solution** (database → API → infrastructure)
2. **Opinionated stack** (curated tools, proven patterns)
3. **Open-source first** (OpenTofu, Ansible, FOSS tools)
4. **Extensible patterns** (add new patterns easily)

---

## 🛠️ Tool Justification

### Why OpenTofu over Terraform?
- ✅ Truly open-source (MPL license)
- ✅ No vendor lock-in risk
- ✅ Community-driven
- ✅ Drop-in Terraform replacement
- ✅ All AWS/GCP/Azure providers work

### Why Ansible over Chef/Puppet?
- ✅ Agentless (no client installation)
- ✅ YAML syntax (consistent with SpecQL)
- ✅ Huge module library
- ✅ Simpler learning curve

### Why Caddy over Nginx (for simple setups)?
- ✅ Auto-SSL (zero config Let's Encrypt)
- ✅ Modern defaults (HTTP/2, TLS 1.3)
- ✅ Simpler config
- ✅ Built-in health checks

### Why Prometheus/Grafana?
- ✅ Industry standard
- ✅ Open-source
- ✅ Huge ecosystem
- ✅ Works everywhere (cloud, on-prem, K8s)

---

## 🚧 Implementation Roadmap

### Q1 2026: Foundation
- [ ] Team F structure (`src/generators/deployment/`)
- [ ] Pattern system (`patterns/deployment/*.yaml`)
- [ ] Docker generator (Dockerfile, compose)
- [ ] Local dev environment generation

### Q2 2026: Cloud Infrastructure
- [ ] OpenTofu module generator (AWS first)
- [ ] Pattern: `small-saas`
- [ ] Pattern: `production-saas`
- [ ] Environment management

### Q3 2026: CI/CD & Observability
- [ ] GitHub Actions workflows
- [ ] Prometheus/Grafana configs
- [ ] Alert rules
- [ ] Runbook generation

### Q4 2026: Advanced Patterns
- [ ] Kubernetes Helm charts
- [ ] Multi-region support
- [ ] Blue-green deployments
- [ ] GCP/Azure support

---

## 📚 References

- **OpenTofu**: https://opentofu.org/
- **Ansible**: https://www.ansible.com/
- **Caddy**: https://caddyserver.com/
- **Prometheus**: https://prometheus.io/
- **Grafana**: https://grafana.com/
- **FraiseQL**: ../fraiseql (AutoFraiseQL integration)

---

**Status**: Proposal
**Next Steps**: Review, refine, implement Phase 1 (Docker)
**Discussion**: GitHub Issue #10
