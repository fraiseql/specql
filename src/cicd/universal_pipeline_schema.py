"""
Universal CI/CD Pipeline Schema

Domain-agnostic expression of CI/CD pipelines that can be converted to any platform.
Follows the same pattern as SpecQL for database schemas.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
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
        # TODO: Implement platform-specific setup actions
        return ""


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
        # TODO: Implement GitHub Actions conversion
        return ""

    def to_gitlab_ci(self) -> str:
        """Convert to GitLab CI YAML"""
        # TODO: Implement GitLab CI conversion
        return ""

    def to_circleci(self) -> str:
        """Convert to CircleCI YAML"""
        # TODO: Implement CircleCI conversion
        return ""

    @classmethod
    def from_github_actions(cls, yaml_content: str) -> 'UniversalPipeline':
        """Reverse engineer from GitHub Actions"""
        # TODO: Implement GitHub Actions parsing
        raise NotImplementedError("GitHub Actions parsing not yet implemented")

    @classmethod
    def from_gitlab_ci(cls, yaml_content: str) -> 'UniversalPipeline':
        """Reverse engineer from GitLab CI"""
        # TODO: Implement GitLab CI parsing
        raise NotImplementedError("GitLab CI parsing not yet implemented")