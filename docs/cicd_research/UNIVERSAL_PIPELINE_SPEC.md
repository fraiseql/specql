# Universal Pipeline YAML Specification

## Universal CI/CD Pipeline YAML Format

Users write BUSINESS INTENT (20 lines) and SpecQL generates TECHNICAL IMPLEMENTATION (200+ lines per platform).

```yaml
# Universal Pipeline YAML Specification

pipeline: backend_api
description: "FastAPI backend with PostgreSQL"
language: python
framework: fastapi

# ============================================================================
# Triggers: When to run
# ============================================================================
triggers:
  - type: push
    branches: [main, develop]

  - type: pull_request
    branches: [main]

  - type: schedule
    schedule: "0 2 * * *"  # Daily at 2 AM

# ============================================================================
# Global Configuration
# ============================================================================
environment:
  DATABASE_URL: "postgresql://localhost/test"
  PYTHON_VERSION: "3.11"

cache_paths:
  - ~/.cache/pip
  - .venv

# ============================================================================
# Stages & Jobs
# ============================================================================
stages:
  # ------------------------------------------------------------------------
  # Stage 1: Test
  # ------------------------------------------------------------------------
  - name: test
    jobs:
      - name: lint
        runtime:
          language: python
          version: "3.11"
          package_manager: uv

        steps:
          - type: checkout

          - type: setup_runtime
            with:
              python-version: "3.11"

          - type: cache_restore
            with:
              key: pip-${{ hashFiles('pyproject.toml') }}

          - type: install_dependencies
            command: "uv pip install -e .[dev]"

          - type: lint
            command: "uv run ruff check src/"

          - type: run
            name: "Type checking"
            command: "uv run mypy src/"

      - name: unit_tests
        runtime:
          language: python
          version: "3.11"

        services:
          - name: postgres
            version: "15"
            environment:
              POSTGRES_PASSWORD: "test"
            ports: [5432]

        steps:
          - type: checkout
          - type: setup_runtime
          - type: install_dependencies

          - type: run_tests
            command: "uv run pytest tests/unit/ --cov=src"

          - type: upload_artifact
            with:
              name: coverage-report
              path: htmlcov/

      - name: integration_tests
        needs: [unit_tests]
        services:
          - name: postgres
            version: "15"

        steps:
          - type: checkout
          - type: setup_runtime
          - type: install_dependencies

          - type: run
            name: "Run migrations"
            command: "uv run specql migrate --apply"

          - type: run_tests
            command: "uv run pytest tests/integration/"

  # ------------------------------------------------------------------------
  # Stage 2: Build
  # ------------------------------------------------------------------------
  - name: build
    jobs:
      - name: docker_build
        needs: [lint, unit_tests, integration_tests]

        steps:
          - type: checkout

          - type: build
            name: "Build Docker image"
            command: "docker build -t myapp:${{ git.sha }} ."

          - type: run
            name: "Push to registry"
            command: "docker push myapp:${{ git.sha }}"

  # ------------------------------------------------------------------------
  # Stage 3: Deploy
  # ------------------------------------------------------------------------
  - name: deploy
    environment: production
    approval_required: true

    jobs:
      - name: deploy_production
        needs: [docker_build]
        if: github.ref == 'refs/heads/main'

        steps:
          - type: checkout

          - type: deploy
            command: "kubectl set image deployment/api api=myapp:${{ git.sha }}"

          - type: run
            name: "Health check"
            command: "curl -f https://api.example.com/health || exit 1"
            timeout_minutes: 5

# ============================================================================
# Pattern Metadata (for pattern library)
# ============================================================================
pattern:
  category: backend_api
  tags: [python, fastapi, postgresql, docker, kubernetes]
  best_practices:
    - "Run linting before tests"
    - "Use matrix builds for multiple Python versions"
    - "Health check after deployment"
    - "Require approval for production"
    - "Use PostgreSQL service for integration tests"
```

## Schema Reference

### Pipeline Level
- `pipeline`: Pipeline name (required)
- `description`: Human-readable description
- `language`: Programming language (python, node, go, rust, java)
- `framework`: Framework name (fastapi, django, express, react)

### Triggers
Array of trigger objects:
- `type`: push, pull_request, schedule, manual, tag, webhook
- `branches`: Array of branch names
- `tags`: Array of tag patterns
- `paths`: Array of file path patterns
- `schedule`: Cron expression

### Environment
Key-value pairs for global environment variables.

### Cache Paths
Array of paths to cache between runs.

### Stages
Array of stage objects:
- `name`: Stage name (required)
- `jobs`: Array of job objects (required)
- `approval_required`: Boolean, requires manual approval
- `environment`: Environment name (production, staging, development)

### Jobs
- `name`: Job name (required)
- `steps`: Array of step objects (required)
- `runtime`: Runtime configuration object
- `services`: Array of service objects
- `environment`: Job-specific environment variables
- `needs`: Array of job names this job depends on
- `if`: Conditional expression
- `timeout_minutes`: Job timeout
- `matrix`: Matrix build configuration

### Steps
- `name`: Step name (required)
- `type`: Step type (required)
- `command`: Shell command to run
- `with_params`: Platform-specific parameters
- `environment`: Step-specific environment variables
- `working_directory`: Working directory for step
- `continue_on_error`: Continue pipeline on step failure
- `timeout_minutes`: Step timeout

### Runtime
- `language`: Programming language
- `version`: Language version
- `package_manager`: Package manager (pip, poetry, uv, npm, yarn)

### Services
- `name`: Service name (postgres, redis, mongodb)
- `version`: Service version
- `environment`: Service environment variables
- `ports`: Array of port numbers

### Pattern Metadata
- `category`: Pattern category
- `tags`: Array of tags for search
- `best_practices`: Array of best practice descriptions