# Week 15: Universal CI/CD Expression Language - DETAILED IMPLEMENTATION PLAN

**Date**: 2025-11-14
**Duration**: 5 days (Week 15 of the 15-17 CI/CD trilogy)
**Status**: 🔴 Planning - Ready to Execute
**Objective**: Create universal expression language for CI/CD pipelines with reverse engineering and multi-platform generation
**Complexity**: COMPLEX - Phased TDD Approach Required

**Prerequisites**: Week 14 complete (100% Trinity Pattern with Rust)
**Output**: Universal pipeline schema, pattern library foundation, reverse engineering for 2 platforms, generators for 2 platforms

---

## 🎯 Executive Summary

Week 15 establishes the **foundational architecture** for universal CI/CD expression, following the same proven pattern used for database schema modeling:

1. **Universal Schema Definition** → Platform-agnostic CI/CD representation
2. **Reverse Engineering** → GitHub Actions/GitLab → Universal format
3. **Code Generation** → Universal → Multiple CI/CD platforms
4. **Pattern Library Foundation** → Reusable pipeline components

### Strategic Context

This work directly applies SpecQL's core philosophy to CI/CD:
- **20 lines of business intent** → **200+ lines per platform**
- Platform switching becomes trivial (GitHub → GitLab in seconds)
- Pattern reuse across projects and platforms
- Semantic search for CI/CD patterns (Week 16-17)

### Success Criteria

By end of Week 15:
- [ ] Universal CI/CD schema defined with comprehensive test coverage
- [ ] GitHub Actions reverse engineering (parser) working with 90%+ pattern coverage
- [ ] GitLab CI reverse engineering (parser) working with 90%+ pattern coverage
- [ ] Universal → GitHub Actions generator producing valid workflows
- [ ] Universal → GitLab CI generator producing valid pipelines
- [ ] 10+ foundational pipeline patterns documented
- [ ] CLI commands for reverse-cicd and generate-cicd operations
- [ ] Integration tests proving round-trip conversion (platform → universal → platform)
- [ ] Documentation for schema, parsers, and generators
- [ ] 95%+ test coverage for all CI/CD modules

---

## 📊 Development Phases Overview

### Phase Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Week 15: 5 Major Phases                                          │
│                                                                   │
│ Phase 1: Universal Schema Foundation (Day 1)                     │
│ Phase 2: GitHub Actions Reverse Engineering (Day 2)              │
│ Phase 3: GitHub Actions Code Generation (Day 3)                  │
│ Phase 4: GitLab CI Support (Day 4)                               │
│ Phase 5: Pattern Library & CLI Integration (Day 5)               │
└─────────────────────────────────────────────────────────────────┘
```

Each phase follows strict TDD discipline: RED → GREEN → REFACTOR → QA

---

## 🔴 PHASE 1: Universal Schema Foundation (Day 1)

**Objective**: Define universal CI/CD pipeline schema with comprehensive test coverage

**Estimated Duration**: 8 hours
**Files Created**: ~10 files, ~1,200 lines
**Test Coverage Target**: 95%+

---

### Phase 1.1: Research & Design (2 hours)

**Objective**: Analyze common patterns across major CI/CD platforms to inform schema design

#### TDD Cycle:

**🔴 RED: Document Expected Patterns (30 minutes)**

Create documentation that defines what patterns we expect to find:

**File**: `docs/cicd_research/EXPECTED_PATTERNS.md`

```markdown
# Expected Common CI/CD Patterns

## Research Questions

1. What are the universal trigger types across all platforms?
   - Push to branch
   - Pull/Merge requests
   - Scheduled (cron)
   - Manual dispatch
   - Tag creation
   - Webhook events

2. What are the common job lifecycle phases?
   - Setup (checkout, runtime setup)
   - Dependencies (install packages)
   - Testing (lint, unit tests, integration tests)
   - Build (compile, package, container build)
   - Deploy (staging, production)
   - Cleanup (artifacts, notifications)

3. What are the common service dependencies?
   - Databases (PostgreSQL, MySQL, MongoDB)
   - Caches (Redis, Memcached)
   - Message queues (RabbitMQ, Kafka)
   - Storage (MinIO, S3-compatible)

4. What are the common matrix strategies?
   - Multiple language versions (Python 3.10, 3.11, 3.12)
   - Multiple OS (Ubuntu, macOS, Windows)
   - Multiple architectures (amd64, arm64)

## Expected Abstraction Layers

### Layer 1: Trigger System
**Expected**: All platforms have some form of event-based triggering
**Variance**: Syntax differs significantly (on: vs only: vs filters:)

### Layer 2: Execution Environment
**Expected**: All platforms specify runtime environment
**Variance**: Some use containers (GitLab), others use runners (GitHub)

### Layer 3: Step Execution
**Expected**: All platforms have atomic step/command execution
**Variance**: Some use marketplace actions (GitHub), others use scripts

### Layer 4: Artifact Management
**Expected**: All platforms support passing files between jobs
**Variance**: Different APIs and storage mechanisms

### Layer 5: Caching
**Expected**: All platforms support dependency caching
**Variance**: Different key strategies and restoration logic
```

**File**: `docs/cicd_research/PLATFORM_COMPARISON.md`

```markdown
# Platform Feature Comparison Matrix

| Feature | GitHub Actions | GitLab CI | CircleCI | Jenkins | Azure DevOps |
|---------|---------------|-----------|----------|---------|--------------|
| **Triggers** |
| Push events | ✅ `on.push` | ✅ `only` | ✅ `filters` | ✅ `triggers` | ✅ `trigger` |
| PR events | ✅ `on.pull_request` | ✅ `only.merge_requests` | ✅ `filters` | ✅ Manual | ✅ `pr` |
| Schedules | ✅ `on.schedule` | ✅ `schedules` | ✅ `triggers.schedule` | ✅ `cron` | ✅ `schedules` |
| Manual | ✅ `workflow_dispatch` | ✅ `when: manual` | ✅ API | ✅ Manual | ✅ Manual |
| **Structure** |
| Explicit stages | ❌ (implicit) | ✅ `stages` | ✅ `workflows` | ✅ `stages` | ✅ `stages` |
| Job dependencies | ✅ `needs` | ✅ `needs` | ✅ `requires` | ✅ `dependencies` | ✅ `dependsOn` |
| Parallel execution | ✅ (default) | ✅ (same stage) | ✅ (same workflow) | ✅ `parallel` | ✅ (same stage) |
| **Environment** |
| Services | ✅ `services` | ✅ `services` | ✅ Docker | ✅ Docker | ✅ `services` |
| Matrix builds | ✅ `strategy.matrix` | ✅ `parallel` | ✅ `matrix` | ✅ `matrix` | ✅ `strategy.matrix` |
| Containers | ✅ `container` | ✅ `image` | ✅ Docker | ✅ Docker | ✅ `container` |
| **Caching** |
| Built-in cache | ✅ `actions/cache` | ✅ `cache` | ✅ `save_cache` | ❌ (plugins) | ✅ `CacheBeta` |
| Artifacts | ✅ `upload/download-artifact` | ✅ `artifacts` | ✅ `persist_to_workspace` | ✅ `archiveArtifacts` | ✅ `PublishBuildArtifacts` |
| **Security** |
| Secrets | ✅ `secrets` | ✅ `variables` | ✅ `context` | ✅ Credentials | ✅ `variables` |
| Environments | ✅ `environment` | ✅ `environment` | ✅ `context` | ❌ | ✅ `environment` |
| Approvals | ✅ (via environments) | ✅ `when: manual` | ✅ `hold` | ✅ `input` | ✅ Approvals |
```

**🟢 GREEN: Collect Real Examples (1 hour)**

Create a collection of real-world pipeline examples from major projects:

**File**: `docs/cicd_research/examples/github_actions_django.yml`
**File**: `docs/cicd_research/examples/github_actions_fastapi.yml`
**File**: `docs/cicd_research/examples/gitlab_ci_nodejs.yml`
**File**: `docs/cicd_research/examples/gitlab_ci_rust.yml`

(Collect 10-15 diverse examples covering different languages, frameworks, and deployment strategies)

**🔧 REFACTOR: Synthesize Common Patterns (30 minutes)**

**File**: `docs/cicd_research/UNIVERSAL_ABSTRACTIONS.md`

```markdown
# Universal CI/CD Abstractions

## Core Abstractions Identified

### 1. Pipeline
**Universal Concept**: Top-level container for all CI/CD configuration
**Properties**:
- Name/identifier
- Global configuration (env vars, defaults)
- Triggers (when to run)
- Stages or jobs (what to run)
- Pattern metadata (for library)

### 2. Trigger
**Universal Concept**: Event that initiates pipeline execution
**Types Identified**:
- `PUSH`: Code pushed to repository
- `PULL_REQUEST`: PR created/updated
- `SCHEDULE`: Time-based (cron)
- `MANUAL`: Manual/API trigger
- `TAG`: Tag created
- `WEBHOOK`: External webhook
**Properties**:
- Type
- Branch/tag filters
- Path filters (run only if certain files change)
- Schedule (cron expression for scheduled triggers)

### 3. Runtime
**Universal Concept**: Execution environment for jobs
**Properties**:
- Language (python, node, go, rust, java)
- Version (3.11, 18, 1.21)
- Package manager (pip, poetry, uv, npm, yarn, pnpm)

### 4. Service
**Universal Concept**: External dependency (database, cache, etc.)
**Properties**:
- Name (postgres, redis, mongodb)
- Version
- Environment variables
- Ports
- Health checks

### 5. Step
**Universal Concept**: Atomic action within a job
**Types Identified**:
- `CHECKOUT`: Clone repository
- `SETUP_RUNTIME`: Install language/tools
- `INSTALL_DEPS`: Install dependencies
- `LINT`: Run linters
- `RUN_TESTS`: Run test suite
- `BUILD`: Compile/build artifacts
- `DEPLOY`: Deploy to environment
- `RUN`: Generic shell command
- `CACHE_SAVE/RESTORE`: Cache management
- `UPLOAD/DOWNLOAD_ARTIFACT`: Artifact management
**Properties**:
- Name
- Type
- Command (for RUN type)
- Parameters (type-specific config)
- Environment variables
- Working directory
- Error handling (continue on error, timeout)

### 6. Job
**Universal Concept**: Collection of steps that run together
**Properties**:
- Name
- Steps (ordered list)
- Runtime configuration
- Services (dependencies)
- Environment variables
- Dependencies (needs/requires)
- Conditional execution (if)
- Timeout
- Matrix strategy (multi-variant builds)

### 7. Stage
**Universal Concept**: Logical grouping of jobs (not all platforms have explicit stages)
**Properties**:
- Name
- Jobs (can run in parallel)
- Approval requirements
- Environment (staging, production)

## Mapping Strategy

### GitHub Actions → Universal
```yaml
# GitHub Actions
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

# Universal
triggers:
  - type: PUSH
    branches: [main]
stages:
  - name: default
    jobs:
      - name: test
        steps:
          - type: CHECKOUT
```

### GitLab CI → Universal
```yaml
# GitLab CI
stages:
  - test
test:
  stage: test
  script:
    - pytest

# Universal
stages:
  - name: test
    jobs:
      - name: test
        steps:
          - type: RUN_TESTS
            command: pytest
```
```

✅ **QA Phase**:
- [ ] Research documentation complete
- [ ] At least 10 real examples collected
- [ ] Common patterns identified and documented
- [ ] Universal abstractions defined
- [ ] Team review of abstractions (if applicable)

---

### Phase 1.2: Universal Schema Implementation (6 hours)

**Objective**: Implement Python dataclasses for universal CI/CD schema with comprehensive tests

#### TDD Cycle 1: Trigger System (1 hour)

**🔴 RED: Trigger Tests (20 minutes)**

**File**: `tests/unit/cicd/schema/test_triggers.py`

```python
"""
Tests for Universal CI/CD Trigger System

These tests define the expected behavior of trigger abstractions.
"""

import pytest
from src.cicd.schema.triggers import Trigger, TriggerType


class TestTriggerType:
    """Test TriggerType enumeration"""

    def test_trigger_type_values(self):
        """Test all expected trigger types exist"""
        assert TriggerType.PUSH == "push"
        assert TriggerType.PULL_REQUEST == "pull_request"
        assert TriggerType.SCHEDULE == "schedule"
        assert TriggerType.MANUAL == "manual"
        assert TriggerType.TAG == "tag"
        assert TriggerType.WEBHOOK == "webhook"

    def test_trigger_type_from_string(self):
        """Test creating TriggerType from string"""
        assert TriggerType("push") == TriggerType.PUSH
        assert TriggerType("pull_request") == TriggerType.PULL_REQUEST


class TestTrigger:
    """Test Trigger dataclass"""

    def test_create_push_trigger(self):
        """Test creating push trigger"""
        trigger = Trigger(
            type=TriggerType.PUSH,
            branches=["main", "develop"]
        )

        assert trigger.type == TriggerType.PUSH
        assert trigger.branches == ["main", "develop"]
        assert trigger.tags is None
        assert trigger.paths is None
        assert trigger.schedule is None

    def test_create_pull_request_trigger(self):
        """Test creating PR trigger"""
        trigger = Trigger(
            type=TriggerType.PULL_REQUEST,
            branches=["main"]
        )

        assert trigger.type == TriggerType.PULL_REQUEST
        assert trigger.branches == ["main"]

    def test_create_schedule_trigger(self):
        """Test creating scheduled trigger"""
        trigger = Trigger(
            type=TriggerType.SCHEDULE,
            schedule="0 2 * * *"  # Daily at 2 AM
        )

        assert trigger.type == TriggerType.SCHEDULE
        assert trigger.schedule == "0 2 * * *"

    def test_trigger_with_path_filters(self):
        """Test trigger with path filters"""
        trigger = Trigger(
            type=TriggerType.PUSH,
            paths=["src/**", "tests/**"]
        )

        assert trigger.paths == ["src/**", "tests/**"]

    def test_trigger_with_tag_filter(self):
        """Test trigger with tag filter"""
        trigger = Trigger(
            type=TriggerType.TAG,
            tags=["v*", "release-*"]
        )

        assert trigger.type == TriggerType.TAG
        assert trigger.tags == ["v*", "release-*"]

    def test_trigger_serialization(self):
        """Test trigger can be serialized to dict"""
        trigger = Trigger(
            type=TriggerType.PUSH,
            branches=["main"]
        )

        data = {
            "type": trigger.type.value,
            "branches": trigger.branches,
            "tags": trigger.tags,
            "paths": trigger.paths,
            "schedule": trigger.schedule
        }

        assert data["type"] == "push"
        assert data["branches"] == ["main"]

    def test_trigger_equality(self):
        """Test trigger equality comparison"""
        t1 = Trigger(type=TriggerType.PUSH, branches=["main"])
        t2 = Trigger(type=TriggerType.PUSH, branches=["main"])
        t3 = Trigger(type=TriggerType.PULL_REQUEST, branches=["main"])

        assert t1 == t2
        assert t1 != t3
```

**Run Tests**:
```bash
uv run pytest tests/unit/cicd/schema/test_triggers.py -v
# Expected: ModuleNotFoundError (tests fail, RED phase)
```

**🟢 GREEN: Implement Trigger System (30 minutes)**

**File**: `src/cicd/schema/triggers.py`

```python
"""
Universal CI/CD Trigger System

Defines platform-agnostic trigger abstractions that can be mapped to any CI/CD platform.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class TriggerType(str, Enum):
    """
    Universal trigger types across all CI/CD platforms

    These represent the common events that can initiate a pipeline execution.
    Each platform has its own syntax, but these abstractions cover 95%+ of use cases.
    """
    PUSH = "push"                    # Code pushed to repository
    PULL_REQUEST = "pull_request"    # PR/MR created or updated
    SCHEDULE = "schedule"            # Time-based (cron)
    MANUAL = "manual"                # Manual/API triggered
    TAG = "tag"                      # Tag created
    WEBHOOK = "webhook"              # External webhook event


@dataclass
class Trigger:
    """
    Universal pipeline trigger configuration

    Represents when a pipeline should be executed. Supports:
    - Branch filtering
    - Tag filtering
    - Path filtering (run only if certain files change)
    - Schedule expressions (cron)

    Example:
        # Push trigger for main branch only
        Trigger(
            type=TriggerType.PUSH,
            branches=["main"]
        )

        # Scheduled trigger (nightly builds)
        Trigger(
            type=TriggerType.SCHEDULE,
            schedule="0 2 * * *"
        )

        # PR trigger that only runs if Python files change
        Trigger(
            type=TriggerType.PULL_REQUEST,
            paths=["src/**/*.py", "tests/**/*.py"]
        )
    """
    type: TriggerType
    branches: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    paths: Optional[List[str]] = None  # File path filters (glob patterns)
    schedule: Optional[str] = None     # Cron expression for scheduled triggers

    def __post_init__(self):
        """Validate trigger configuration"""
        if self.type == TriggerType.SCHEDULE and not self.schedule:
            raise ValueError("Schedule trigger requires schedule expression")

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "type": self.type.value,
            "branches": self.branches,
            "tags": self.tags,
            "paths": self.paths,
            "schedule": self.schedule
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Trigger':
        """Create trigger from dictionary"""
        return cls(
            type=TriggerType(data["type"]),
            branches=data.get("branches"),
            tags=data.get("tags"),
            paths=data.get("paths"),
            schedule=data.get("schedule")
        )
```

**Run Tests**:
```bash
uv run pytest tests/unit/cicd/schema/test_triggers.py -v
# Expected: All tests pass (GREEN phase)
```

**🔧 REFACTOR: Add Validation & Documentation (10 minutes)**

Add docstrings, type hints validation, and helper methods:

```python
# Add to Trigger class

def matches_branch(self, branch: str) -> bool:
    """Check if trigger matches given branch"""
    if not self.branches:
        return True  # No filter = match all
    return branch in self.branches

def matches_path(self, path: str) -> bool:
    """Check if trigger matches given file path"""
    if not self.paths:
        return True  # No filter = match all

    import fnmatch
    return any(fnmatch.fnmatch(path, pattern) for pattern in self.paths)

def is_valid_cron(self) -> bool:
    """Validate cron expression format"""
    if not self.schedule:
        return True

    # Basic cron validation (5 fields)
    parts = self.schedule.split()
    return len(parts) == 5
```

**Update tests**:
```python
# Add to test_triggers.py

def test_trigger_matches_branch(self):
    """Test branch matching logic"""
    trigger = Trigger(type=TriggerType.PUSH, branches=["main", "develop"])

    assert trigger.matches_branch("main") is True
    assert trigger.matches_branch("develop") is True
    assert trigger.matches_branch("feature/test") is False

def test_trigger_matches_path(self):
    """Test path matching logic"""
    trigger = Trigger(
        type=TriggerType.PUSH,
        paths=["src/**/*.py", "tests/**"]
    )

    assert trigger.matches_path("src/main.py") is True
    assert trigger.matches_path("tests/test_main.py") is True
    assert trigger.matches_path("README.md") is False

def test_cron_validation(self):
    """Test cron expression validation"""
    valid_trigger = Trigger(
        type=TriggerType.SCHEDULE,
        schedule="0 2 * * *"
    )
    assert valid_trigger.is_valid_cron() is True

    invalid_trigger = Trigger(
        type=TriggerType.SCHEDULE,
        schedule="invalid"
    )
    assert invalid_trigger.is_valid_cron() is False
```

**Run Tests**:
```bash
uv run pytest tests/unit/cicd/schema/test_triggers.py -v --cov=src/cicd/schema/triggers
# Expected: All tests pass, 95%+ coverage
```

✅ **QA Phase**:
- [ ] All trigger tests pass
- [ ] Test coverage ≥ 95%
- [ ] Type hints correct
- [ ] Documentation complete

**Commit**:
```bash
git add tests/unit/cicd/schema/test_triggers.py src/cicd/schema/triggers.py
git commit -m "feat(cicd): implement universal trigger system with comprehensive tests

- Define TriggerType enum for all common CI/CD triggers
- Implement Trigger dataclass with branch/path/schedule filtering
- Add validation and helper methods
- Achieve 95%+ test coverage

Part of Phase 1.2 (Universal Schema) - Week 15 Day 1
"
```

---

#### TDD Cycle 2: Runtime & Services (1 hour)

**🔴 RED: Runtime & Service Tests (20 minutes)**

**File**: `tests/unit/cicd/schema/test_runtime.py`

```python
"""Tests for Runtime and Service abstractions"""

import pytest
from src.cicd.schema.runtime import Runtime, Service


class TestRuntime:
    """Test Runtime configuration"""

    def test_create_python_runtime(self):
        """Test creating Python runtime"""
        runtime = Runtime(
            language="python",
            version="3.11",
            package_manager="uv"
        )

        assert runtime.language == "python"
        assert runtime.version == "3.11"
        assert runtime.package_manager == "uv"

    def test_create_nodejs_runtime(self):
        """Test creating Node.js runtime"""
        runtime = Runtime(
            language="node",
            version="18",
            package_manager="pnpm"
        )

        assert runtime.language == "node"
        assert runtime.version == "18"
        assert runtime.package_manager == "pnpm"

    def test_runtime_defaults(self):
        """Test runtime with defaults"""
        runtime = Runtime(language="go", version="1.21")

        assert runtime.language == "go"
        assert runtime.version == "1.21"
        assert runtime.package_manager is None

    def test_runtime_to_setup_action_python(self):
        """Test converting runtime to setup action (GitHub Actions)"""
        runtime = Runtime(language="python", version="3.11")
        action = runtime.to_github_actions_setup()

        assert "setup-python" in action
        assert "3.11" in action

    def test_runtime_to_setup_action_node(self):
        """Test converting runtime to setup action for Node"""
        runtime = Runtime(language="node", version="18")
        action = runtime.to_github_actions_setup()

        assert "setup-node" in action
        assert "18" in action

    def test_runtime_serialization(self):
        """Test runtime serialization"""
        runtime = Runtime(
            language="python",
            version="3.11",
            package_manager="uv"
        )

        data = runtime.to_dict()
        assert data["language"] == "python"
        assert data["version"] == "3.11"
        assert data["package_manager"] == "uv"

        restored = Runtime.from_dict(data)
        assert restored == runtime


class TestService:
    """Test Service configuration"""

    def test_create_postgres_service(self):
        """Test creating PostgreSQL service"""
        service = Service(
            name="postgres",
            version="15",
            environment={"POSTGRES_PASSWORD": "test"},
            ports=[5432]
        )

        assert service.name == "postgres"
        assert service.version == "15"
        assert service.environment["POSTGRES_PASSWORD"] == "test"
        assert service.ports == [5432]

    def test_create_redis_service(self):
        """Test creating Redis service"""
        service = Service(
            name="redis",
            version="7",
            ports=[6379]
        )

        assert service.name == "redis"
        assert service.version == "7"
        assert service.ports == [6379]

    def test_service_defaults(self):
        """Test service with defaults"""
        service = Service(name="mongodb", version="6")

        assert service.name == "mongodb"
        assert service.version == "6"
        assert service.environment == {}
        assert service.ports == []

    def test_service_to_github_actions_format(self):
        """Test converting service to GitHub Actions format"""
        service = Service(
            name="postgres",
            version="15",
            environment={"POSTGRES_PASSWORD": "test"},
            ports=[5432]
        )

        yaml_dict = service.to_github_actions_dict()

        assert yaml_dict["image"] == "postgres:15"
        assert yaml_dict["env"]["POSTGRES_PASSWORD"] == "test"
        assert 5432 in yaml_dict["ports"]

    def test_service_to_gitlab_ci_format(self):
        """Test converting service to GitLab CI format"""
        service = Service(name="postgres", version="15")

        gitlab_format = service.to_gitlab_ci_format()
        assert gitlab_format == "postgres:15"

    def test_service_serialization(self):
        """Test service serialization"""
        service = Service(
            name="postgres",
            version="15",
            environment={"POSTGRES_PASSWORD": "test"},
            ports=[5432]
        )

        data = service.to_dict()
        restored = Service.from_dict(data)
        assert restored == service
```

**Run Tests**:
```bash
uv run pytest tests/unit/cicd/schema/test_runtime.py -v
# Expected: FAIL (RED phase)
```

**🟢 GREEN: Implement Runtime & Services (30 minutes)**

**File**: `src/cicd/schema/runtime.py`

```python
"""
Universal Runtime and Service Abstractions

Defines execution environment and external dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Runtime:
    """
    Runtime environment configuration

    Specifies the language, version, and package manager for job execution.

    Example:
        Runtime(
            language="python",
            version="3.11",
            package_manager="uv"
        )
    """
    language: str              # python, node, go, rust, java, ruby
    version: str               # 3.11, 18, 1.21, 1.70, 11, 3.2
    package_manager: Optional[str] = None  # pip, poetry, uv, npm, yarn, pnpm

    def to_github_actions_setup(self) -> str:
        """
        Generate GitHub Actions setup step

        Returns:
            Action uses string (e.g., "actions/setup-python@v5")
        """
        setup_actions = {
            "python": "actions/setup-python@v5",
            "node": "actions/setup-node@v4",
            "go": "actions/setup-go@v5",
            "rust": "dtolnay/rust-toolchain@stable",
            "java": "actions/setup-java@v4",
            "ruby": "ruby/setup-ruby@v1"
        }

        action = setup_actions.get(self.language, "actions/setup-python@v5")
        return f"{action} with {self.language}-version {self.version}"

    def to_gitlab_ci_image(self) -> str:
        """
        Generate GitLab CI Docker image

        Returns:
            Docker image string (e.g., "python:3.11")
        """
        image_map = {
            "python": f"python:{self.version}",
            "node": f"node:{self.version}",
            "go": f"golang:{self.version}",
            "rust": f"rust:{self.version}",
        }

        return image_map.get(self.language, f"{self.language}:{self.version}")

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "language": self.language,
            "version": self.version,
            "package_manager": self.package_manager
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Runtime':
        """Deserialize from dictionary"""
        return cls(
            language=data["language"],
            version=data["version"],
            package_manager=data.get("package_manager")
        )


@dataclass
class Service:
    """
    External service dependency (database, cache, etc.)

    Represents a containerized service that runs alongside the main job.
    Common for integration testing with databases.

    Example:
        Service(
            name="postgres",
            version="15",
            environment={"POSTGRES_PASSWORD": "test"},
            ports=[5432]
        )
    """
    name: str                                      # postgres, redis, mongodb, mysql
    version: str                                   # Version tag
    environment: Dict[str, str] = field(default_factory=dict)  # Environment variables
    ports: List[int] = field(default_factory=list)            # Exposed ports

    def to_github_actions_dict(self) -> dict:
        """
        Convert to GitHub Actions service format

        Returns:
            Dictionary for GitHub Actions YAML services section
        """
        result = {
            "image": f"{self.name}:{self.version}"
        }

        if self.environment:
            result["env"] = self.environment

        if self.ports:
            result["ports"] = self.ports

        return result

    def to_gitlab_ci_format(self) -> str:
        """
        Convert to GitLab CI service format

        Returns:
            Service string (e.g., "postgres:15")
        """
        return f"{self.name}:{self.version}"

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "environment": self.environment,
            "ports": self.ports
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Service':
        """Deserialize from dictionary"""
        return cls(
            name=data["name"],
            version=data["version"],
            environment=data.get("environment", {}),
            ports=data.get("ports", [])
        )
```

**Run Tests**:
```bash
uv run pytest tests/unit/cicd/schema/test_runtime.py -v
# Expected: PASS (GREEN phase)
```

**🔧 REFACTOR & ✅ QA** (10 minutes): Similar to previous cycle

**Commit**:
```bash
git add tests/unit/cicd/schema/test_runtime.py src/cicd/schema/runtime.py
git commit -m "feat(cicd): implement Runtime and Service abstractions

- Define Runtime dataclass for language/version/package manager
- Define Service dataclass for external dependencies
- Add platform-specific conversion methods
- Achieve 95%+ test coverage

Part of Phase 1.2 (Universal Schema) - Week 15 Day 1
"
```

---

#### TDD Cycle 3: Steps & Jobs (2 hours)

[Continue with similar detailed TDD cycles for Steps, Jobs, Stages, and Pipeline]

Due to length constraints, I'll provide the high-level structure for remaining cycles:

**🔴 RED**: Write comprehensive tests for:
- `StepType` enum (15+ step types)
- `Step` dataclass (20+ test cases)
- `Job` dataclass (with matrix, services, needs)
- `Stage` dataclass (with approval, environment)

**🟢 GREEN**: Implement minimal working version

**🔧 REFACTOR**: Add validation, helper methods, platform conversions

**✅ QA**: Verify coverage, documentation, integration

Files created:
- `tests/unit/cicd/schema/test_steps.py` (~200 lines)
- `tests/unit/cicd/schema/test_jobs.py` (~250 lines)
- `tests/unit/cicd/schema/test_stages.py` (~150 lines)
- `tests/unit/cicd/schema/test_pipeline.py` (~300 lines)
- `src/cicd/schema/steps.py` (~300 lines)
- `src/cicd/schema/jobs.py` (~250 lines)
- `src/cicd/schema/stages.py` (~150 lines)
- `src/cicd/schema/pipeline.py` (~400 lines)

---

#### TDD Cycle 4: Pipeline Integration Tests (1 hour)

**🔴 RED**: Write integration tests that test the full schema together

**File**: `tests/integration/cicd/test_schema_integration.py`

```python
"""Integration tests for universal CI/CD schema"""

def test_create_complete_pipeline():
    """Test creating a complete pipeline with all components"""

def test_pipeline_serialization_deserialization():
    """Test round-trip serialization"""

def test_pipeline_with_matrix_builds():
    """Test complex matrix build configuration"""

def test_pipeline_with_services():
    """Test pipeline with multiple services"""
```

**🟢 GREEN**: Ensure all integration tests pass

**🔧 REFACTOR**: Add convenience constructors, builder patterns

**✅ QA**: Full schema validation

---

### Phase 1 Summary

**Achievements**:
- ✅ Universal schema defined with 7 core abstractions
- ✅ Comprehensive test coverage (95%+)
- ✅ Platform conversion methods
- ✅ Serialization/deserialization
- ✅ Integration tests

**Files Created**: ~10 files, ~1,200 lines
**Test Coverage**: 95%+
**Commit Count**: 4-5 focused commits

---

## 🔴 PHASE 2: GitHub Actions Reverse Engineering (Day 2)

**Objective**: Parse GitHub Actions YAML into universal format

**Estimated Duration**: 8 hours
**Files Created**: ~8 files, ~1,500 lines
**Test Coverage Target**: 90%+

[Continue with similarly detailed TDD cycles for parser implementation...]

---

## 🔴 PHASE 3: GitHub Actions Code Generation (Day 3)

**Objective**: Generate GitHub Actions YAML from universal format

[Detailed TDD cycles...]

---

## 🔴 PHASE 4: GitLab CI Support (Day 4)

**Objective**: Add GitLab CI parser and generator

[Detailed TDD cycles...]

---

## 🔴 PHASE 5: Pattern Library & CLI Integration (Day 5)

**Objective**: Create reusable patterns and CLI commands

[Detailed TDD cycles...]

---

## 📊 Week 15 Success Metrics

### Quantitative Metrics
- [ ] 1,200+ lines of schema code
- [ ] 1,500+ lines of parser code
- [ ] 1,500+ lines of generator code
- [ ] 2,000+ lines of test code
- [ ] 95%+ test coverage for schema
- [ ] 90%+ test coverage for parsers/generators
- [ ] 10+ pipeline patterns documented

### Qualitative Metrics
- [ ] Round-trip conversion preserves functionality
- [ ] Schema supports 90%+ of common CI/CD patterns
- [ ] Parsers handle complex real-world workflows
- [ ] Generators produce valid, idiomatic platform YAML
- [ ] CLI is intuitive and well-documented

### Integration Metrics
- [ ] All tests pass
- [ ] No regressions in existing SpecQL functionality
- [ ] Documentation complete
- [ ] Code reviewed and approved

---

## 🎯 Daily Discipline Checklist

Each day must follow this discipline:

### Start of Day
- [ ] Review previous day's work
- [ ] Read phase objectives
- [ ] Set up testing environment
- [ ] Plan TDD cycles

### During Development
- [ ] Write failing test first (RED)
- [ ] Implement minimal code (GREEN)
- [ ] Refactor with confidence (REFACTOR)
- [ ] Verify quality (QA)
- [ ] Commit after each cycle
- [ ] Take breaks between cycles

### End of Day
- [ ] Run full test suite
- [ ] Review coverage reports
- [ ] Update documentation
- [ ] Commit remaining work
- [ ] Plan next day

---

## 🚀 Getting Started

### Day 1 Morning (RIGHT NOW)

```bash
# Create directory structure
mkdir -p src/cicd/schema
mkdir -p tests/unit/cicd/schema
mkdir -p tests/integration/cicd
mkdir -p docs/cicd_research/examples

# Create __init__.py files
touch src/cicd/__init__.py
touch src/cicd/schema/__init__.py
touch tests/unit/cicd/__init__.py

# Start with Phase 1.1: Research
# Create EXPECTED_PATTERNS.md following the template above

# Then proceed to Phase 1.2: TDD Cycle 1 (Triggers)
```

### First Command

```bash
# Create the first test file
uv run pytest tests/unit/cicd/schema/test_triggers.py -v
# This will fail - that's expected and correct (RED phase)
```

---

**Status**: 🟢 Ready to Execute
**Next Action**: Create `docs/cicd_research/EXPECTED_PATTERNS.md`
**Estimated Completion**: End of Week 15 (5 days from now)
