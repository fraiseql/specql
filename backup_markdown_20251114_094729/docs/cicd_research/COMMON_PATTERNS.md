# Common CI/CD Patterns Across Platforms

## Universal Concepts

### 1. Pipeline Structure
- **Triggers**: Events that start pipeline (push, PR, schedule)
- **Stages**: Logical grouping (test, build, deploy)
- **Jobs**: Individual units of work
- **Steps**: Atomic actions within jobs
- **Artifacts**: Files passed between jobs
- **Caching**: Speed up repeated builds

### 2. Language-Specific Patterns

**Python**:
- Setup Python version
- Install dependencies (pip, poetry, uv)
- Run linters (ruff, mypy, black)
- Run tests (pytest)
- Generate coverage reports
- Build distributions (wheel, sdist)

**Node.js**:
- Setup Node version
- Install dependencies (npm, yarn, pnpm)
- Run linters (eslint, prettier)
- Run tests (jest, vitest)
- Build production bundle

**Go**:
- Setup Go version
- Download modules
- Run vet/fmt
- Run tests with race detector
- Build binaries

### 3. Database Patterns

**PostgreSQL**:
- Start database service
- Run migrations
- Run integration tests
- Database seeding

**Docker**:
- Build images
- Tag with version
- Push to registry
- Multi-stage builds

### 4. Deployment Patterns

**Container Deployment**:
- Build Docker image
- Push to registry (Docker Hub, ECR, GCR)
- Deploy to platform (ECS, GKE, K8s)
- Health checks
- Rollback on failure

**Serverless**:
- Deploy to Lambda/Cloud Functions
- Update API Gateway
- Run smoke tests

### 5. Security Patterns

**Secrets Management**:
- Platform-specific secret stores
- Environment variables
- Credential rotation

**Security Scanning**:
- Dependency scanning
- SAST/DAST
- Container scanning
- License compliance

## Platform Comparison

| Concept | GitHub Actions | GitLab CI | CircleCI | Jenkins | Azure DevOps |
|---------|---------------|-----------|----------|---------|--------------|
| Trigger | `on:` | `only:` | `filters:` | `triggers` | `trigger:` |
| Stages | `jobs:` | `stages:` | `workflows:` | `stages` | `stages:` |
| Steps | `steps:` | `script:` | `steps:` | `steps` | `steps:` |
| Artifacts | `upload-artifact` | `artifacts:` | `persist_to_workspace` | `archiveArtifacts` | `PublishBuildArtifacts` |
| Caching | `actions/cache` | `cache:` | `save_cache` | `cache` | `CacheBeta` |
| Matrix | `strategy.matrix` | `parallel:` | `matrix:` | `matrix` | `strategy.matrix` |