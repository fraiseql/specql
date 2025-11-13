# Weeks 15-17: Universal CI/CD Expression Language

**Date**: 2025-11-13
**Duration**: 15 days (3 weeks)
**Status**: ✅ Completed
**Objective**: Create universal expression language for CI/CD pipelines with reverse engineering and multi-platform generation

**Prerequisites**: Week 14 complete (100% Trinity Pattern)
**Output**: Universal pipeline YAML, pattern library, reverse engineering, converters for 5+ platforms

---

## 🎯 Executive Summary

Extend SpecQL's architecture to CI/CD pipelines using the **same pattern**:

1. **Universal Expression** → Business intent for pipelines
2. **Pattern Library** → Reusable CI/CD patterns with semantic search
3. **Reverse Engineering** → GitHub Actions/GitLab → Universal
4. **Converters** → Universal → All major platforms

### Core Philosophy

```yaml
# Users write BUSINESS INTENT (20 lines)
pipeline: backend_api
language: python
framework: fastapi
database: postgresql

stages:
  test:
    - lint
    - unit_tests
    - integration_tests

  deploy:
    environment: production
    approval_required: true
    health_check: /api/health

# SpecQL generates TECHNICAL IMPLEMENTATION (200+ lines per platform)
# - GitHub Actions
# - GitLab CI
# - CircleCI
# - Jenkins
# - Azure DevOps
```

### Success Criteria

- [ ] Universal pipeline language defined
- [ ] Pattern library with 50+ CI/CD patterns
- [ ] Reverse engineering from 3+ platforms
- [ ] Converters for 5+ major platforms
- [ ] Semantic search across pipeline patterns
- [ ] LLM enhancement for recommendations
- [ ] Integration with existing SpecQL projects

---

## Week 15: Universal Pipeline Language & Pattern Library

**Objective**: Define universal expression language for CI/CD and build pattern library

### Day 1: Universal Pipeline Language Design

**Morning Block (4 hours): Language Specification**

#### 1. Analyze Common CI/CD Patterns (2 hours)

**Analyze Multiple Platforms**:

```bash
# Collect examples from major platforms
mkdir -p docs/cicd_research/platforms/

# GitHub Actions
curl https://api.github.com/repos/django/django/.github/workflows/*.yml

# GitLab CI
# (collect examples)

# CircleCI, Jenkins, Azure DevOps
# (collect examples)
```

**Identify Common Abstractions**:

`docs/cicd_research/COMMON_PATTERNS.md`:
```markdown
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
```

#### 2. Define Universal Schema (2 hours)

**Universal Pipeline Schema**: `src/cicd/universal_pipeline_schema.py`

```python
"""
Universal CI/CD Pipeline Schema

Domain-agnostic expression of CI/CD pipelines that can be converted to any platform.
Follows the same pattern as SpecQL for database schemas.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Literal
from enum import Enum


# ============================================================================
# Triggers: When pipelines run
# ============================================================================

class TriggerType(str, Enum):
    """Universal trigger types"""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    TAG = "tag"
    WEBHOOK = "webhook"


@dataclass
class Trigger:
    """Pipeline trigger configuration"""
    type: TriggerType
    branches: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    paths: Optional[List[str]] = None  # File path filters
    schedule: Optional[str] = None  # Cron expression

    def matches_github_actions(self) -> bool:
        """Check if GitHub Actions supports this trigger"""
        return True

    def matches_gitlab_ci(self) -> bool:
        """Check if GitLab CI supports this trigger"""
        return True


# ============================================================================
# Environment & Runtime
# ============================================================================

@dataclass
class Runtime:
    """Runtime environment configuration"""
    language: str  # python, node, go, rust, java
    version: str  # 3.11, 18, 1.21
    package_manager: Optional[str] = None  # pip, poetry, uv, npm, yarn

    def to_setup_action(self, platform: str) -> str:
        """Convert to platform-specific setup"""
        pass


@dataclass
class Service:
    """External service (database, cache, etc.)"""
    name: str  # postgres, redis, mongodb
    version: str
    environment: Dict[str, str] = field(default_factory=dict)
    ports: List[int] = field(default_factory=list)


# ============================================================================
# Steps: Atomic actions
# ============================================================================

class StepType(str, Enum):
    """Universal step types"""
    RUN = "run"  # Run shell command
    CHECKOUT = "checkout"  # Clone repository
    SETUP_RUNTIME = "setup_runtime"  # Setup language runtime
    INSTALL_DEPS = "install_dependencies"
    RUN_TESTS = "run_tests"
    LINT = "lint"
    BUILD = "build"
    DEPLOY = "deploy"
    UPLOAD_ARTIFACT = "upload_artifact"
    DOWNLOAD_ARTIFACT = "download_artifact"
    CACHE_SAVE = "cache_save"
    CACHE_RESTORE = "cache_restore"


@dataclass
class Step:
    """Pipeline step (atomic action)"""
    name: str
    type: StepType
    command: Optional[str] = None
    with_params: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    working_directory: Optional[str] = None
    continue_on_error: bool = False
    timeout_minutes: Optional[int] = None


# ============================================================================
# Jobs: Collection of steps
# ============================================================================

@dataclass
class Job:
    """Pipeline job (collection of steps)"""
    name: str
    steps: List[Step]
    runtime: Optional[Runtime] = None
    services: List[Service] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    needs: List[str] = field(default_factory=list)  # Job dependencies
    if_condition: Optional[str] = None
    timeout_minutes: int = 60

    # Matrix builds
    matrix: Optional[Dict[str, List[str]]] = None  # {"python": ["3.10", "3.11"], "os": ["ubuntu", "macos"]}


# ============================================================================
# Stages: Logical grouping
# ============================================================================

@dataclass
class Stage:
    """Pipeline stage (logical grouping of jobs)"""
    name: str
    jobs: List[Job]
    approval_required: bool = False
    environment: Optional[str] = None  # production, staging, development


# ============================================================================
# Pipeline: Complete definition
# ============================================================================

@dataclass
class UniversalPipeline:
    """
    Universal CI/CD Pipeline Definition

    Platform-agnostic representation that can be converted to:
    - GitHub Actions
    - GitLab CI
    - CircleCI
    - Jenkins
    - Azure DevOps
    """
    name: str
    description: str = ""

    # Project metadata
    language: str = "python"
    framework: Optional[str] = None  # fastapi, django, express, react

    # Pipeline configuration
    triggers: List[Trigger] = field(default_factory=list)
    stages: List[Stage] = field(default_factory=list)

    # Global configuration
    global_environment: Dict[str, str] = field(default_factory=dict)
    cache_paths: List[str] = field(default_factory=list)

    # Pattern metadata (for pattern library)
    pattern_id: Optional[str] = None
    category: Optional[str] = None  # backend, frontend, fullstack, data
    tags: List[str] = field(default_factory=list)

    # Embedding for semantic search
    embedding: Optional[List[float]] = None

    def to_github_actions(self) -> str:
        """Convert to GitHub Actions YAML"""
        pass

    def to_gitlab_ci(self) -> str:
        """Convert to GitLab CI YAML"""
        pass

    def to_circleci(self) -> str:
        """Convert to CircleCI YAML"""
        pass

    @classmethod
    def from_github_actions(cls, yaml_content: str) -> 'UniversalPipeline':
        """Reverse engineer from GitHub Actions"""
        pass

    @classmethod
    def from_gitlab_ci(cls, yaml_content: str) -> 'UniversalPipeline':
        """Reverse engineer from GitLab CI"""
        pass
```

**Universal Pipeline YAML Format**: `docs/cicd_research/UNIVERSAL_PIPELINE_SPEC.md`

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
```

---

**Afternoon Block (4 hours): Pattern Library Structure**

#### 1. Design Pattern Library Schema (2 hours)

**Pattern Repository**: `src/cicd/pattern_repository.py`

```python
"""
CI/CD Pattern Repository

Stores reusable pipeline patterns with semantic search capabilities.
Same architecture as domain pattern library.
"""

from dataclasses import dataclass
from typing import List, Optional, Protocol
from src.cicd.universal_pipeline_schema import UniversalPipeline


@dataclass
class PipelinePattern:
    """Reusable CI/CD pipeline pattern"""
    pattern_id: str
    name: str
    description: str
    category: str  # backend, frontend, fullstack, data, mobile

    # Pattern definition
    pipeline: UniversalPipeline

    # Metadata
    tags: List[str]
    language: str
    framework: Optional[str] = None

    # Usage statistics
    usage_count: int = 0
    success_rate: float = 1.0

    # Semantic search
    embedding: Optional[List[float]] = None

    # Quality metrics
    avg_duration_minutes: Optional[int] = None
    reliability_score: float = 1.0


class PipelinePatternRepository(Protocol):
    """Protocol for pattern storage"""

    def store_pattern(self, pattern: PipelinePattern) -> None:
        """Store pipeline pattern"""
        ...

    def find_by_id(self, pattern_id: str) -> Optional[PipelinePattern]:
        """Find pattern by ID"""
        ...

    def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[PipelinePattern]:
        """Semantic search for similar patterns"""
        ...

    def search_by_tags(self, tags: List[str]) -> List[PipelinePattern]:
        """Find patterns by tags"""
        ...

    def search_by_category(self, category: str) -> List[PipelinePattern]:
        """Find patterns by category"""
        ...
```

#### 2. Create Initial Pattern Library (2 hours)

**Pattern Library**: `patterns/cicd/`

```yaml
# patterns/cicd/python_fastapi_backend.yaml

pattern_id: "python_fastapi_backend_v1"
name: "FastAPI Backend with PostgreSQL"
description: "Production-ready CI/CD for FastAPI applications"
category: backend_api
language: python
framework: fastapi
tags: [python, fastapi, postgresql, docker, pytest]

pipeline:
  name: fastapi_backend
  language: python
  framework: fastapi

  triggers:
    - type: push
      branches: [main, develop]
    - type: pull_request

  stages:
    - name: test
      jobs:
        - name: lint
          runtime:
            language: python
            version: "3.11"
            package_manager: uv
          steps:
            - {type: checkout}
            - {type: setup_runtime}
            - {type: install_dependencies, command: "uv pip install -e .[dev]"}
            - {type: lint, command: "uv run ruff check ."}
            - {type: run, name: "mypy", command: "uv run mypy src/"}

        - name: test
          services:
            - {name: postgres, version: "15"}
          steps:
            - {type: checkout}
            - {type: setup_runtime}
            - {type: install_dependencies}
            - {type: run_tests, command: "uv run pytest --cov"}

    - name: deploy
      environment: production
      approval_required: true
      jobs:
        - name: deploy
          steps:
            - {type: deploy, command: "deploy-to-production"}

best_practices:
  - "Use uv for fast dependency management"
  - "Run mypy for type safety"
  - "Require approval for production deploys"
  - "Use PostgreSQL service for integration tests"
```

**More Patterns**:

```bash
patterns/cicd/
├── python_fastapi_backend.yaml
├── python_django_fullstack.yaml
├── nodejs_express_api.yaml
├── nodejs_nextjs_frontend.yaml
├── go_microservice.yaml
├── rust_api.yaml
├── python_data_pipeline.yaml
├── python_ml_training.yaml
├── docker_multi_stage.yaml
└── kubernetes_deployment.yaml
```

**Create 10+ Base Patterns**:

Each pattern includes:
- Universal pipeline definition
- Best practices
- Common pitfalls
- Platform-specific optimizations
- Example repositories

---

**Day 1 Summary**:
- ✅ Universal pipeline schema defined
- ✅ Common patterns analyzed
- ✅ Pattern library structure created
- ✅ 10+ initial patterns created

---

### Day 2: Reverse Engineering - Parser Foundation

**Objective**: Build parsers to convert platform-specific YAML to universal format

**Morning Block (4 hours): GitHub Actions Parser**

#### 🔴 RED: Parser Tests (2 hours)

**Test File**: `tests/unit/cicd/parsers/test_github_actions_parser.py`

```python
"""Tests for GitHub Actions → Universal Pipeline parser"""

import pytest
from src.cicd.parsers.github_actions_parser import GitHubActionsParser
from src.cicd.universal_pipeline_schema import UniversalPipeline, TriggerType, StepType


class TestGitHubActionsParser:
    """Test parsing GitHub Actions YAML to universal format"""

    @pytest.fixture
    def parser(self):
        return GitHubActionsParser()

    def test_parse_simple_workflow(self, parser):
        """Test parsing basic GitHub Actions workflow"""
        yaml_content = """
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Run tests
        run: pytest
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        assert pipeline.name == "CI"
        assert len(pipeline.triggers) == 2
        assert pipeline.triggers[0].type == TriggerType.PUSH
        assert pipeline.triggers[0].branches == ["main"]
        assert pipeline.triggers[1].type == TriggerType.PULL_REQUEST

        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].name == "test"

        job = pipeline.stages[0].jobs[0]
        assert job.name == "test"
        assert len(job.steps) == 4

        # Check steps
        assert job.steps[0].type == StepType.CHECKOUT
        assert job.steps[1].type == StepType.SETUP_RUNTIME
        assert job.steps[2].type == StepType.INSTALL_DEPS
        assert job.steps[3].type == StepType.RUN_TESTS

    def test_parse_with_services(self, parser):
        """Test parsing workflow with services"""
        yaml_content = """
name: Integration Tests

jobs:
  test:
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - run: pytest tests/integration
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        job = pipeline.stages[0].jobs[0]
        assert len(job.services) == 1
        assert job.services[0].name == "postgres"
        assert job.services[0].version == "15"
        assert job.services[0].environment["POSTGRES_PASSWORD"] == "test"

    def test_parse_with_matrix(self, parser):
        """Test parsing matrix builds"""
        yaml_content = """
name: Matrix Build

jobs:
  test:
    strategy:
      matrix:
        python: ['3.10', '3.11', '3.12']
        os: [ubuntu-latest, macos-latest]
    steps:
      - run: pytest
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        job = pipeline.stages[0].jobs[0]
        assert job.matrix is not None
        assert job.matrix["python"] == ["3.10", "3.11", "3.12"]
        assert job.matrix["os"] == ["ubuntu-latest", "macos-latest"]
```

**Run Tests (Should Fail)**:
```bash
uv run pytest tests/unit/cicd/parsers/test_github_actions_parser.py -v

# Expected: ModuleNotFoundError
```

**Commit**:
```bash
git add tests/unit/cicd/parsers/
git commit -m "test(cicd): add failing tests for GitHub Actions parser - RED phase"
```

---

#### 🟢 GREEN: Implement Parser (2 hours)

**Parser**: `src/cicd/parsers/github_actions_parser.py`

```python
"""
GitHub Actions Parser

Reverse engineers GitHub Actions YAML to universal pipeline format.
"""

import yaml
from typing import Dict, Any, List
from src.cicd.universal_pipeline_schema import (
    UniversalPipeline,
    Trigger, TriggerType,
    Stage, Job, Step, StepType,
    Runtime, Service
)


class GitHubActionsParser:
    """Parse GitHub Actions workflows to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """
        Parse GitHub Actions YAML to UniversalPipeline

        Args:
            yaml_content: GitHub Actions workflow YAML

        Returns:
            UniversalPipeline object
        """
        data = yaml.safe_load(yaml_content)

        return UniversalPipeline(
            name=data.get("name", "Unnamed Pipeline"),
            triggers=self._parse_triggers(data.get("on", {})),
            stages=self._parse_jobs(data.get("jobs", {})),
            global_environment=data.get("env", {})
        )

    def _parse_triggers(self, on_config: Any) -> List[Trigger]:
        """Parse 'on:' section to universal triggers"""
        triggers = []

        if isinstance(on_config, str):
            # Simple case: on: push
            triggers.append(Trigger(type=TriggerType(on_config)))

        elif isinstance(on_config, list):
            # List case: on: [push, pull_request]
            for trigger_type in on_config:
                triggers.append(Trigger(type=TriggerType(trigger_type)))

        elif isinstance(on_config, dict):
            # Complex case with branches/paths
            for trigger_type, config in on_config.items():
                if isinstance(config, dict):
                    triggers.append(Trigger(
                        type=TriggerType(trigger_type),
                        branches=config.get("branches"),
                        tags=config.get("tags"),
                        paths=config.get("paths")
                    ))
                else:
                    triggers.append(Trigger(type=TriggerType(trigger_type)))

        return triggers

    def _parse_jobs(self, jobs_config: Dict[str, Any]) -> List[Stage]:
        """Parse jobs to universal stages"""
        # GitHub Actions doesn't have explicit stages
        # We create a single stage with all jobs

        jobs = []
        for job_id, job_config in jobs_config.items():
            jobs.append(self._parse_job(job_id, job_config))

        return [Stage(name="default", jobs=jobs)]

    def _parse_job(self, job_id: str, job_config: Dict[str, Any]) -> Job:
        """Parse single job"""
        return Job(
            name=job_config.get("name", job_id),
            steps=self._parse_steps(job_config.get("steps", [])),
            runtime=self._detect_runtime(job_config),
            services=self._parse_services(job_config.get("services", {})),
            needs=job_config.get("needs", []) if isinstance(job_config.get("needs"), list) else [job_config.get("needs")] if job_config.get("needs") else [],
            if_condition=job_config.get("if"),
            matrix=self._parse_matrix(job_config.get("strategy", {}).get("matrix")),
            environment=job_config.get("env", {})
        )

    def _parse_steps(self, steps_config: List[Dict[str, Any]]) -> List[Step]:
        """Parse steps to universal format"""
        steps = []

        for step_config in steps_config:
            step_type = self._detect_step_type(step_config)

            steps.append(Step(
                name=step_config.get("name", "Unnamed step"),
                type=step_type,
                command=step_config.get("run"),
                with_params=step_config.get("with", {}),
                environment=step_config.get("env", {}),
                continue_on_error=step_config.get("continue-on-error", False),
                timeout_minutes=step_config.get("timeout-minutes")
            ))

        return steps

    def _detect_step_type(self, step_config: Dict[str, Any]) -> StepType:
        """Detect step type from configuration"""

        # Check 'uses' field for actions
        uses = step_config.get("uses", "")

        if "checkout" in uses:
            return StepType.CHECKOUT
        elif "setup-python" in uses or "setup-node" in uses or "setup-go" in uses:
            return StepType.SETUP_RUNTIME
        elif "cache" in uses:
            return StepType.CACHE_RESTORE
        elif "upload-artifact" in uses:
            return StepType.UPLOAD_ARTIFACT
        elif "download-artifact" in uses:
            return StepType.DOWNLOAD_ARTIFACT

        # Check 'run' field for commands
        run = step_config.get("run", "")

        if "pip install" in run or "npm install" in run or "go mod download" in run:
            return StepType.INSTALL_DEPS
        elif "pytest" in run or "npm test" in run or "go test" in run:
            return StepType.RUN_TESTS
        elif "ruff" in run or "eslint" in run or "go vet" in run:
            return StepType.LINT
        elif "docker build" in run or "npm run build" in run:
            return StepType.BUILD
        elif "kubectl" in run or "deploy" in run:
            return StepType.DEPLOY

        return StepType.RUN

    def _parse_services(self, services_config: Dict[str, Any]) -> List[Service]:
        """Parse services (databases, caches, etc.)"""
        services = []

        for service_name, service_config in services_config.items():
            image = service_config.get("image", "")
            name, _, version = image.partition(":")

            services.append(Service(
                name=name or service_name,
                version=version or "latest",
                environment=service_config.get("env", {}),
                ports=[int(p.split(":")[0]) for p in service_config.get("ports", [])]
            ))

        return services

    def _detect_runtime(self, job_config: Dict[str, Any]) -> Runtime:
        """Detect runtime from steps"""
        steps = job_config.get("steps", [])

        for step in steps:
            uses = step.get("uses", "")

            if "setup-python" in uses:
                version = step.get("with", {}).get("python-version", "3.11")
                return Runtime(language="python", version=str(version))
            elif "setup-node" in uses:
                version = step.get("with", {}).get("node-version", "18")
                return Runtime(language="node", version=str(version))
            elif "setup-go" in uses:
                version = step.get("with", {}).get("go-version", "1.21")
                return Runtime(language="go", version=str(version))

        return None

    def _parse_matrix(self, matrix_config: Any) -> Dict[str, List[str]]:
        """Parse matrix strategy"""
        if not matrix_config:
            return None

        result = {}
        for key, values in matrix_config.items():
            if isinstance(values, list):
                result[key] = [str(v) for v in values]

        return result if result else None
```

**Run Tests (Should Pass)**:
```bash
uv run pytest tests/unit/cicd/parsers/test_github_actions_parser.py -v
```

**Commit**:
```bash
git add src/cicd/parsers/github_actions_parser.py
git commit -m "feat(cicd): implement GitHub Actions parser - GREEN phase"
```

---

**Afternoon Block (4 hours): GitLab CI Parser**

#### 🔴 RED + 🟢 GREEN: GitLab Parser (3 hours)

**Test + Implementation**: `tests/unit/cicd/parsers/test_gitlab_ci_parser.py`
**Parser**: `src/cicd/parsers/gitlab_ci_parser.py`

Similar structure to GitHub Actions parser, handling GitLab CI specific syntax:
- `stages:` → Explicit stages
- `script:` → Steps
- `services:` → Services
- `rules:` → Triggers
- `needs:` → Dependencies

#### 🔧 REFACTOR: Parser Factory (1 hour)

**Factory**: `src/cicd/parsers/parser_factory.py`

```python
"""Parser factory for detecting and using correct parser"""

from pathlib import Path
from typing import Union
from src.cicd.parsers.github_actions_parser import GitHubActionsParser
from src.cicd.parsers.gitlab_ci_parser import GitLabCIParser
from src.cicd.universal_pipeline_schema import UniversalPipeline


class ParserFactory:
    """Factory for auto-detecting platform and parsing"""

    @staticmethod
    def parse_file(file_path: Path) -> UniversalPipeline:
        """
        Auto-detect platform and parse file

        Args:
            file_path: Path to CI/CD config file

        Returns:
            UniversalPipeline
        """
        content = file_path.read_text()

        # Detect platform from file path
        if ".github/workflows" in str(file_path):
            parser = GitHubActionsParser()
        elif ".gitlab-ci.yml" in file_path.name:
            parser = GitLabCIParser()
        else:
            # Detect from content
            parser = ParserFactory._detect_from_content(content)

        return parser.parse(content)

    @staticmethod
    def _detect_from_content(content: str) -> Union[GitHubActionsParser, GitLabCIParser]:
        """Detect platform from YAML content"""
        if "jobs:" in content and "runs-on:" in content:
            return GitHubActionsParser()
        elif "stages:" in content and "script:" in content:
            return GitLabCIParser()
        else:
            # Default to GitHub Actions
            return GitHubActionsParser()
```

**Day 2 Summary**:
- ✅ GitHub Actions parser complete
- ✅ GitLab CI parser complete
- ✅ Parser factory for auto-detection
- ✅ Can reverse engineer 2 major platforms

---

### Day 3: Converters - GitHub Actions Generator

**Objective**: Generate GitHub Actions YAML from universal format

**Morning Block (4 hours): GitHub Actions Generator**

#### 🔴 RED: Generator Tests (1.5 hours)

**Test File**: `tests/unit/cicd/generators/test_github_actions_generator.py`

```python
"""Tests for Universal → GitHub Actions generator"""

import pytest
from src.cicd.generators.github_actions_generator import GitHubActionsGenerator
from src.cicd.universal_pipeline_schema import *


class TestGitHubActionsGenerator:
    """Test generating GitHub Actions YAML from universal format"""

    @pytest.fixture
    def generator(self):
        return GitHubActionsGenerator()

    def test_generate_simple_workflow(self, generator):
        """Test generating basic workflow"""
        pipeline = UniversalPipeline(
            name="CI",
            triggers=[
                Trigger(type=TriggerType.PUSH, branches=["main"]),
                Trigger(type=TriggerType.PULL_REQUEST)
            ],
            stages=[
                Stage(
                    name="test",
                    jobs=[
                        Job(
                            name="test",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Checkout", type=StepType.CHECKOUT),
                                Step(name="Setup", type=StepType.SETUP_RUNTIME),
                                Step(name="Test", type=StepType.RUN_TESTS, command="pytest")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "name: CI" in yaml_output
        assert "on:" in yaml_output
        assert "push:" in yaml_output
        assert "branches: [main]" in yaml_output
        assert "pull_request:" in yaml_output
        assert "jobs:" in yaml_output
        assert "runs-on: ubuntu-latest" in yaml_output
        assert "uses: actions/checkout@v4" in yaml_output
        assert "uses: actions/setup-python@v5" in yaml_output
        assert "run: pytest" in yaml_output
```

---

#### 🟢 GREEN: Implement Generator (2.5 hours)

**Template**: `templates/cicd/github_actions.yml.j2`

```yaml
{# GitHub Actions Workflow Template #}
name: {{ pipeline.name }}

on:
{%- if pipeline.triggers %}
{%- for trigger in pipeline.triggers %}
  {{ trigger.type }}:
  {%- if trigger.branches %}
    branches: [{{ trigger.branches|join(', ') }}]
  {%- endif %}
  {%- if trigger.paths %}
    paths:
    {%- for path in trigger.paths %}
      - {{ path }}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
{%- else %}
  push:
{%- endif %}

{%- if pipeline.global_environment %}

env:
{%- for key, value in pipeline.global_environment.items() %}
  {{ key }}: {{ value }}
{%- endfor %}
{%- endif %}

jobs:
{%- for stage in pipeline.stages %}
{%- for job in stage.jobs %}
  {{ job.name }}:
    runs-on: ubuntu-latest

    {%- if job.needs %}
    needs: [{{ job.needs|join(', ') }}]
    {%- endif %}

    {%- if job.if_condition %}
    if: {{ job.if_condition }}
    {%- endif %}

    {%- if job.matrix %}
    strategy:
      matrix:
      {%- for key, values in job.matrix.items() %}
        {{ key }}: [{{ values|join(', ') }}]
      {%- endfor %}
    {%- endif %}

    {%- if job.services %}
    services:
    {%- for service in job.services %}
      {{ service.name }}:
        image: {{ service.name }}:{{ service.version }}
        {%- if service.environment %}
        env:
        {%- for key, value in service.environment.items() %}
          {{ key }}: {{ value }}
        {%- endfor %}
        {%- endif %}
        {%- if service.ports %}
        ports:
        {%- for port in service.ports %}
          - {{ port }}:{{ port }}
        {%- endfor %}
        {%- endif %}
    {%- endfor %}
    {%- endif %}

    steps:
    {%- for step in job.steps %}
      - name: {{ step.name }}
        {{ _render_step(step) }}
    {%- endfor %}
{%- endfor %}
{%- endfor %}
```

**Generator**: `src/cicd/generators/github_actions_generator.py`

```python
"""
GitHub Actions Generator

Converts universal pipeline format to GitHub Actions YAML.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.cicd.universal_pipeline_schema import UniversalPipeline, Step, StepType


class GitHubActionsGenerator:
    """Generate GitHub Actions workflows from universal format"""

    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "cicd"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("github_actions.yml.j2")

        # Add custom filter for step rendering
        self.env.filters["render_step"] = self._render_step

    def generate(self, pipeline: UniversalPipeline) -> str:
        """
        Generate GitHub Actions YAML from universal pipeline

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            GitHub Actions YAML content
        """
        return self.template.render(
            pipeline=pipeline,
            _render_step=self._render_step
        )

    def _render_step(self, step: Step) -> str:
        """Convert universal step to GitHub Actions step"""

        # Map step types to GitHub Actions syntax
        step_map = {
            StepType.CHECKOUT: "uses: actions/checkout@v4",
            StepType.SETUP_RUNTIME: self._render_setup_runtime(step),
            StepType.CACHE_RESTORE: "uses: actions/cache@v4",
            StepType.UPLOAD_ARTIFACT: "uses: actions/upload-artifact@v4",
            StepType.DOWNLOAD_ARTIFACT: "uses: actions/download-artifact@v4",
        }

        if step.type in step_map:
            action = step_map[step.type]
            if step.with_params:
                params = "\n".join(f"        {k}: {v}" for k, v in step.with_params.items())
                return f"{action}\n      with:\n{params}"
            return action

        # Default: run command
        return f"run: {step.command}"

    def _render_setup_runtime(self, step: Step) -> str:
        """Render setup-* action based on language"""
        language = step.with_params.get("language", "python")

        runtime_actions = {
            "python": "actions/setup-python@v5",
            "node": "actions/setup-node@v4",
            "go": "actions/setup-go@v5",
            "rust": "dtolnay/rust-toolchain@stable",
        }

        return f"uses: {runtime_actions.get(language, 'actions/setup-python@v5')}"
```

**Run Tests (Should Pass)**:
```bash
uv run pytest tests/unit/cicd/generators/test_github_actions_generator.py -v
```

**Commit**:
```bash
git add src/cicd/generators/github_actions_generator.py templates/cicd/
git commit -m "feat(cicd): implement GitHub Actions generator - GREEN phase"
```

---

**Afternoon Block (4 hours): Multi-Platform Conversion**

Implement generators for:
- GitLab CI
- CircleCI
- Jenkins (Jenkinsfile)
- Azure DevOps

**Day 3 Summary**:
- ✅ GitHub Actions generator complete
- ✅ GitLab CI generator complete
- ✅ CircleCI generator implemented
- ✅ Can convert universal → 3+ platforms

---

### Day 4: CLI Integration

**Objective**: Add CI/CD commands to SpecQL CLI

**Commands to Implement**:

```bash
# Reverse engineer existing pipelines
specql reverse-cicd .github/workflows/ci.yml
specql reverse-cicd .gitlab-ci.yml

# Generate from universal YAML
specql generate-cicd pipeline.yaml --platform github-actions
specql generate-cicd pipeline.yaml --platform gitlab
specql generate-cicd pipeline.yaml --platform all

# Generate from SpecQL entities (auto-create pipeline)
specql generate-cicd entities/*.yaml --auto --platform github-actions
```

**Implementation** similar to existing `specql generate` command.

---

### Day 5: Semantic Search Integration

**Objective**: Enable semantic search across CI/CD patterns

**Features**:

```bash
# Search for similar pipelines
specql search-pipeline "fastapi backend with postgres"

# Get recommendations
specql recommend-pipeline entities/contact.yaml

# Compare pipelines
specql compare-pipeline .github/workflows/ci.yml .gitlab-ci.yml
```

**Implementation**:
- Use same embedding service as domain patterns
- Store pipeline embeddings in pattern library
- Enable similarity search

---

## Week 15 Summary

**Achievements**:
- ✅ Universal CI/CD expression language defined
- ✅ Pattern library with 20+ reusable pipelines
- ✅ Reverse engineering from GitHub Actions + GitLab CI
- ✅ Generators for 4+ major platforms
- ✅ CLI commands for CI/CD operations

**Lines of Code**:
- Schema: ~800 lines
- Parsers: ~1,200 lines
- Generators: ~1,500 lines
- Patterns: ~2,000 lines (YAML)
- **Total: ~5,500 lines**

---

## Weeks 16-17: Advanced Features

### Week 16: Additional Platforms
- CircleCI, Jenkins, Azure DevOps
- Platform-specific optimizations
- Migration guides

### Week 17: LLM Enhancement & Optimization
- LLM-powered pattern recommendations
- Automatic optimization suggestions
- Performance benchmarking
- Documentation

---

## Success Metrics

- [ ] Universal language supports 90% of CI/CD patterns
- [ ] Pattern library with 50+ patterns
- [ ] Reverse engineering from 5+ platforms
- [ ] Generation to 5+ platforms
- [ ] Round-trip conversion (GitHub → Universal → GitLab) preserves functionality
- [ ] Semantic search finds relevant patterns with 80%+ accuracy
- [ ] CLI integrated and documented

---

**Status**: 🔴 Ready to Execute
**Priority**: High (enables universal expressivity for CI/CD)
**Expected Output**: Universal CI/CD language with multi-platform support
