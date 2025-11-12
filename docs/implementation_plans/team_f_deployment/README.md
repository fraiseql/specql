# Team F: Deployment Generator - Implementation Plans

**Created**: 2025-11-12
**Team**: Team F (Deployment Generation)
**Status**: Planning Complete
**Total Phases**: 5

---

## 🎯 Vision

Extend SpecQL to auto-generate **complete deployment infrastructure** from minimal YAML, following the same philosophy as database generation:

**15 lines of YAML → 5000+ lines of production infrastructure**

Just like SpecQL generates database schema, Team F generates:
- Docker containers
- Cloud infrastructure (OpenTofu/AWS)
- CI/CD pipelines
- Observability stack
- Advanced deployment patterns

---

## 📚 Implementation Phases

### ✅ [Phase 1: Docker & Local Dev](./phase_1_docker_local_dev.md)
**Priority**: HIGH | **Status**: Ready for Implementation
**Estimated Effort**: 3-4 weeks

**Deliverables**:
- Framework-aware Dockerfile generation (FraiseQL, Django, Rails)
- docker-compose.yml for local dev + production
- Multi-stage Docker builds with best practices
- Caddy reverse proxy configuration
- Environment management

**Impact**: Users can deploy locally with one command

---

### ✅ [Phase 2: OpenTofu Modules](./phase_2_opentofu_modules.md)
**Priority**: HIGH | **Status**: Ready for Implementation (after Phase 1)
**Estimated Effort**: 4 weeks

**Deliverables**:
- AWS infrastructure modules (VPC, RDS, ECS, ALB, CloudWatch)
- Pattern-based configurations (small-saas, production-saas)
- Secure-by-default configurations
- Cost-optimized resource sizing
- Infrastructure documentation

**Impact**: Production AWS deployment without DevOps expertise

**Why OpenTofu?**
- Open-source (MPL license) - no vendor lock-in
- Drop-in Terraform replacement
- Community-driven, truly FOSS

---

### ✅ [Phase 3: CI/CD Pipelines](./phase_3_cicd_pipelines.md)
**Priority**: MEDIUM | **Status**: Ready for Implementation (after Phase 1-2)
**Estimated Effort**: 3 weeks

**Deliverables**:
- GitHub Actions workflow generation
- Multi-stage pipelines (lint → test → build → deploy)
- Database migration automation
- Rollback procedures
- Environment promotion (staging → production)

**Impact**: Fully automated deployment pipeline, zero-touch deployments

---

### ✅ [Phase 4: Observability Stack](./phase_4_observability_stack.md)
**Priority**: HIGH | **Status**: Ready for Implementation (after Phase 1-2)
**Estimated Effort**: 3 weeks

**Deliverables**:
- Prometheus metrics collection
- Grafana dashboards (FraiseQL-specific + infrastructure)
- Loki log aggregation
- Alert rules and notification channels
- Framework-specific metrics (FraiseQL Rust performance)

**Impact**: Production-ready monitoring out of the box

**Cost Savings**: ~$5-48K/year vs commercial APM (Datadog, New Relic, Sentry)

---

### ✅ [Phase 5: Advanced Patterns](./phase_5_advanced_patterns.md)
**Priority**: LOW-MEDIUM | **Status**: Future (after Phases 1-4)
**Estimated Effort**: 6 weeks

**Deliverables**:
- Kubernetes Helm chart generation
- Multi-region deployments (disaster recovery)
- Blue-green deployment strategies
- Django framework support
- Rails framework support (optional)

**Impact**: Enterprise-grade deployment patterns, multi-framework support

---

## 🏗️ Architecture Overview

```
SpecQL YAML (Entities + Actions)
    ↓
[Teams A-E: Database Generation]
    ↓
PostgreSQL Schema + PL/pgSQL Functions
    ↓
[Team F: Deployment Generation] ← THIS
    ↓
┌────────────┬────────────┬────────────┬────────────┐
│   Phase 1  │  Phase 2   │  Phase 3   │  Phase 4   │
│   Docker   │  OpenTofu  │   CI/CD    │Observability│
│  + Compose │    AWS     │  Pipelines │  Prometheus│
└────────────┴────────────┴────────────┴────────────┘
    ↓
Complete Production Infrastructure
```

---

## 🎨 Framework-Aware Generation

Team F respects framework differences (building on Issue #9's framework system):

### FraiseQL (Python 3.13 + Rust)
- Multi-stage Docker build (Rust compilation via maturin)
- Rust-optimized JSONB metrics in Grafana
- GraphQL-specific monitoring (query depth, resolver timing)
- FastAPI + Uvicorn stack

### Django (Python 3.12)
- Python-only Docker build
- Gunicorn + Celery + Redis stack
- Django-specific monitoring
- ORM-aware database queries

### Rails (Ruby 3.2) - Future
- Ruby Docker build
- Puma + Sidekiq + Redis stack
- Rails-specific monitoring

**Framework defaults in `src/cli/framework_defaults.py`**:
```python
FRAMEWORK_DEFAULTS = {
    "fraiseql": {
        "deployment": {
            "runtime": "python",
            "version": "3.13",
            "requires": ["postgresql", "rust"],
            "docker_base": "python:3.13-slim",
            "framework_package": "fraiseql[all]",
            "build_system": "maturin",
        }
    },
    # ... Django, Rails
}
```

---

## 📋 Deployment Patterns

### Pattern: hobby-project
**Use Case**: Solo dev, low cost
**Stack**: Docker Compose, Caddy, single server
**Cost**: ~$10-20/month

### Pattern: small-saas
**Use Case**: Startup MVP, <1000 users
**Stack**: AWS (RDS db.t4g.micro, ECS Fargate 2 tasks)
**Cost**: ~$50-100/month

### Pattern: production-saas
**Use Case**: Production app, >10k users
**Stack**: AWS (Multi-AZ RDS, ECS autoscaling 5-50 tasks)
**Cost**: ~$300-500/month

### Pattern: kubernetes
**Use Case**: Complex apps, microservices
**Stack**: Helm charts, CloudNativePG operator, Istio/Linkerd
**Cost**: Variable (cluster + resources)

---

## 📁 Team F File Structure

```
src/generators/deployment/
├── __init__.py
├── deployment_orchestrator.py     # Main orchestrator
├── docker/                         # Phase 1
│   ├── dockerfile_generator.py
│   ├── compose_generator.py
│   └── caddy_generator.py
├── opentofu/                       # Phase 2
│   ├── opentofu_orchestrator.py
│   └── modules/
│       ├── networking/
│       ├── database/
│       ├── compute/
│       └── monitoring/
├── cicd/                           # Phase 3
│   ├── github/
│   │   └── actions_generator.py
│   └── gitlab/
│       └── gitlab_ci_generator.py
├── observability/                  # Phase 4
│   ├── prometheus/
│   ├── grafana/
│   ├── loki/
│   └── alertmanager/
└── advanced/                       # Phase 5
    ├── kubernetes/
    ├── multiregion/
    └── bluegreen/
```

---

## 🚀 Usage Examples

### Generate Docker Stack
```bash
specql deploy generate deployment.yaml --framework fraiseql
# → Generates Dockerfile, docker-compose.yml, Caddyfile, .env.example
```

### Generate Full AWS Infrastructure
```bash
specql deploy generate deployment.yaml --framework fraiseql --platform aws --pattern small-saas
# → Generates OpenTofu modules for VPC, RDS, ECS, ALB, CloudWatch
```

### Generate CI/CD Pipeline
```bash
specql deploy generate deployment.yaml --framework fraiseql --cicd github-actions
# → Generates .github/workflows/*.yml
```

### Generate Observability Stack
```bash
specql deploy generate deployment.yaml --framework fraiseql --monitoring standard
# → Generates Prometheus, Grafana, Loki configs with FraiseQL dashboards
```

### Generate Kubernetes Helm Chart
```bash
specql deploy generate deployment.yaml --framework fraiseql --pattern kubernetes
# → Generates Helm chart with CloudNativePG, Ingress, autoscaling
```

---

## 🎯 Success Metrics

### Quantitative Goals
- ✅ Generate 5000+ lines from 15-line YAML (300x leverage)
- ✅ Docker builds successfully in < 5 minutes
- ✅ OpenTofu validates with zero errors
- ✅ CI/CD pipeline deploys in < 10 minutes
- ✅ Observability costs < $50/month
- ✅ 100% test coverage for all generators

### Qualitative Goals
- ✅ Users deploy to production without DevOps expertise
- ✅ Generated configs pass security best practices
- ✅ Framework-specific optimizations applied automatically
- ✅ Cost-optimized by default
- ✅ Self-documenting (auto-generated READMEs)

---

## 🧪 Testing Philosophy

**TDD Cycle** (per Phase 1 methodology):
1. **RED**: Write failing test for specific behavior
2. **GREEN**: Implement minimal code to pass
3. **REFACTOR**: Clean up and optimize
4. **QA**: Verify phase completion

**Test Categories**:
- **Unit Tests**: Generator logic, template rendering
- **Integration Tests**: End-to-end generation, actual builds
- **Validation Tests**: `docker build`, `tofu validate`, `helm lint`

---

## 🔗 Dependencies

### External Tools
- **Docker** - Containerization
- **OpenTofu** - Infrastructure as code (open-source Terraform alternative)
- **Ansible** - Configuration management (optional)
- **Prometheus/Grafana** - Observability
- **Helm** - Kubernetes package manager

### Internal Dependencies
- **Phase 1** (Docker) - Foundation for all other phases
- **Phase 2** (OpenTofu) - Required for cloud deployments
- **Phases 3-5** - Build on top of Phases 1-2

### Python Dependencies
```toml
# Add to pyproject.toml
dependencies = [
    "jinja2>=3.1.0",  # Template engine
    "pyyaml>=6.0.0",  # YAML parsing
]

[project.optional-dependencies]
deployment = [
    "docker>=7.0.0",  # Docker API (for build testing)
]
```

---

## 📚 Documentation

### Guides (to be created)
- `docs/guides/DEPLOYMENT_DOCKER.md` - Docker deployment guide
- `docs/guides/DEPLOYMENT_AWS.md` - AWS deployment guide
- `docs/guides/DEPLOYMENT_CICD.md` - CI/CD guide
- `docs/guides/DEPLOYMENT_OBSERVABILITY.md` - Observability guide
- `docs/guides/DEPLOYMENT_KUBERNETES.md` - Kubernetes guide

### Reference
- `docs/reference/TEAM_F_OVERVIEW.md` - Team F architecture overview

### Auto-Generated (per project)
- `generated/deployment/DEPLOYMENT_README.md` - Deployment instructions
- `generated/infrastructure/opentofu/README.md` - Infrastructure guide
- `generated/observability/README.md` - Observability guide

---

## 🛠️ Implementation Roadmap

### Q1 2026: Foundation
- ✅ Team F structure
- ✅ Phase 1: Docker generation
- ✅ Local development workflows

### Q2 2026: Cloud Infrastructure
- ✅ Phase 2: OpenTofu module generation
- ✅ AWS deployment (small-saas pattern)
- ✅ Production deployment tested

### Q3 2026: Automation & Observability
- ✅ Phase 3: CI/CD pipelines
- ✅ Phase 4: Observability stack
- ✅ Full automation achieved

### Q4 2026: Advanced Patterns
- ✅ Phase 5: Kubernetes, multi-region, blue-green
- ✅ Django framework support
- ✅ Enterprise features complete

---

## 🔒 Security Considerations

All generated configurations follow security best practices:
- ✅ Non-root Docker users
- ✅ Multi-stage builds (minimal attack surface)
- ✅ Private subnets for databases
- ✅ Security groups with least privilege
- ✅ Encryption at rest and in transit
- ✅ Secrets management (AWS Secrets Manager / Vault)
- ✅ No hardcoded credentials

---

## 💰 Cost Optimization

Generated infrastructure is cost-optimized by default:
- ✅ Right-sized instances for each pattern
- ✅ Spot instances where appropriate
- ✅ Auto-scaling to match demand
- ✅ Backup retention policies
- ✅ Log retention policies
- ✅ Cost estimates provided per pattern

**Example Costs** (small-saas pattern):
- Infrastructure: ~$50-100/month (AWS)
- Observability: ~$20/month (self-hosted)
- **Total**: ~$70-120/month
- **vs Commercial Solutions**: $500-1000/month (saves $430-880/month)

---

## 🤝 Integration with Existing Teams

Team F builds on the foundation of Teams A-E:

### Team A (Parser)
- Uses entity definitions for deployment naming
- Respects schema registry for multi-tenant vs shared

### Team B (Schema Generator)
- Database migrations automatically included in Docker/K8s
- RDS configurations match generated schema requirements

### Team C (Action Compiler)
- PL/pgSQL functions deployed via migrations
- Function naming conventions respected in deployment

### Team D (FraiseQL)
- FraiseQL framework detection triggers framework-specific configs
- GraphQL metrics auto-configured in observability

### Team E (CLI)
- New `specql deploy` command group
- Consistent CLI patterns and help text
- Framework flag reused from Issue #9

---

## 📞 Questions / Feedback

For questions about Team F implementation:
- **GitHub Issues**: https://github.com/fraiseql/specql/issues
- **Documentation**: https://github.com/fraiseql/specql/docs

---

**Last Updated**: 2025-11-12
**Status**: Planning Complete - Ready for Implementation
**Next Step**: Begin Phase 1 implementation
