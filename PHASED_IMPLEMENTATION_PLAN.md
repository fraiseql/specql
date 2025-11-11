# Phased Implementation Plan: Multi-Execution-Type Call Service Extension

**Project**: SpecQL Call Service Framework Extension
**Status**: Planning Phase
**Complexity**: COMPLEX - Requires Phased TDD Approach
**Timeline**: 20 weeks (5 months)

---

## 🎯 Executive Summary

Extend SpecQL's `call_service` framework to support multiple execution types beyond HTTP APIs, including shell scripts, Docker containers, and serverless functions. This will transform the job queue system from a simple HTTP job dispatcher into a universal execution engine while maintaining backward compatibility and following SpecQL's convention-over-configuration philosophy.

**Current State**:
- HTTP-only job queue system (`jobs.tb_job_run`)
- Service registry with HTTP-centric configuration
- Basic retry and timeout handling
- Observability views for job monitoring

**Target State**:
- Multi-execution-type job runner (HTTP, Shell, Docker, Serverless)
- Extensible runner architecture with plugin support
- Enhanced security controls (command allowlists, resource limits)
- Execution-type-aware monitoring and observability
- Zero breaking changes to existing HTTP-based services

---

## 📊 Current Architecture Analysis

### Existing Components

#### 1. Job Queue System (`src/generators/schema/jobs_schema_generator.py`)
**Current Schema**: `jobs.tb_job_run`
```sql
- id UUID PRIMARY KEY
- identifier TEXT NOT NULL UNIQUE
- idempotency_key TEXT
- service_name TEXT NOT NULL
- operation TEXT NOT NULL
- input_data JSONB
- output_data JSONB
- error_message TEXT
- status TEXT (pending, running, completed, failed, cancelled)
- attempts INTEGER
- max_attempts INTEGER
- timeout_seconds INTEGER
- tenant_id UUID
- triggered_by UUID
- correlation_id TEXT
- entity_type TEXT
- entity_pk TEXT
- timestamps (created_at, started_at, completed_at, updated_at)
```

**Key Features**:
- Idempotency via `identifier` and `idempotency_key`
- Retry logic with `attempts` and `max_attempts`
- Correlation tracking for traceability
- Comprehensive observability views

**Extension Points**:
- Add `execution_type TEXT` to differentiate HTTP/Shell/Docker/Serverless
- Add `runner_config JSONB` for execution-type-specific configuration
- Add `resource_usage JSONB` for tracking CPU/memory/duration metrics
- Add `security_context JSONB` for audit trail

#### 2. CallServiceStepCompiler (`src/generators/actions/step_compilers/call_service_step_compiler.py`)
**Current Behavior**:
- Compiles SpecQL `call_service` steps → PL/pgSQL INSERT statements
- Generates idempotent identifiers
- Compiles input data to JSONB
- Handles variable references (`$entity.field`)
- Configures retry and timeout parameters

**Extension Points**:
- Add execution type detection from service registry
- Generate runner-specific configuration
- Validate execution-type-specific constraints
- Compile security policies into `security_context`

#### 3. Service Registry (`src/registry/service_registry.py`)
**Current Schema** (`registry/service_registry.yaml`):
```yaml
services:
  - name: stripe
    type: payment
    category: financial
    operations:
      - name: create_charge
        input_schema: {...}
        output_schema: {...}
        timeout: 30
        max_retries: 3
```

**Extension Points**:
- Add `execution_type` field (http | shell | docker | serverless)
- Add `runner_config` for execution-specific settings
- Add `security_policy` for command/image allowlists
- Maintain backward compatibility (default to `http`)

#### 4. AST Models (`src/core/ast_models.py`)
**Current Model**: `CallServiceStep`
```python
@dataclass
class CallServiceStep:
    service: str
    operation: str
    input: dict[str, Any]
    async_mode: bool = True
    timeout: int | None = None
    max_retries: int | None = None
    on_success: list["ActionStep"] = field(default_factory=list)
    on_failure: list["ActionStep"] = field(default_factory=list)
    correlation_field: str | None = None
```

**Extension Points**:
- No changes needed - execution type determined by service registry lookup
- Keep AST focused on business logic, not technical execution details

---

## 🔧 Requirements Specification

### Functional Requirements

#### FR1: Multi-Execution-Type Support
- **FR1.1**: HTTP API execution (existing, enhanced)
- **FR1.2**: Shell script execution (local processes)
- **FR1.3**: Docker container execution
- **FR1.4**: Serverless function invocation (AWS Lambda, Google Cloud Functions)
- **FR1.5**: Plugin architecture for custom execution types

#### FR2: Configuration Management
- **FR2.1**: Backward-compatible service registry format
- **FR2.2**: Execution-type-specific runner configuration
- **FR2.3**: Security policies (allowlists, resource limits)
- **FR2.4**: Environment-specific configurations (dev/staging/prod)

#### FR3: Job Processing
- **FR3.1**: Asynchronous job execution with result polling
- **FR3.2**: Resource management (CPU, memory, disk quotas)
- **FR3.3**: Timeout and cancellation handling per execution type
- **FR3.4**: Graceful failure handling and error propagation

#### FR4: Monitoring & Observability
- **FR4.1**: Execution-type-specific metrics (duration, resource usage)
- **FR4.2**: Performance dashboards (`v_execution_performance_by_type`)
- **FR4.3**: Failure pattern analysis (`v_runner_failure_patterns`)
- **FR4.4**: Resource usage tracking (`v_resource_usage_by_runner`)

### Non-Functional Requirements

#### NFR1: Security
- **NFR1.1**: Command injection prevention (input sanitization, allowlists)
- **NFR1.2**: Resource usage limits (CPU, memory, disk, network)
- **NFR1.3**: Network isolation (container sandboxing)
- **NFR1.4**: Comprehensive audit logging (execution traces)

#### NFR2: Reliability
- **NFR2.1**: Graceful degradation (fallback to HTTP on runner failure)
- **NFR2.2**: Resource cleanup (process termination, container removal)
- **NFR2.3**: Dead letter queue for unrecoverable failures
- **NFR2.4**: Circuit breaker patterns for failing runners

#### NFR3: Performance
- **NFR3.1**: Concurrent job execution (1000+ jobs/minute)
- **NFR3.2**: Runner overhead < 100ms per job
- **NFR3.3**: Resource pooling (container reuse, connection pooling)
- **NFR3.4**: Horizontal scalability (multi-worker support)

#### NFR4: Maintainability
- **NFR4.1**: Clean separation of concerns (runner abstraction)
- **NFR4.2**: Comprehensive logging and debugging tools
- **NFR4.3**: Configuration validation with helpful error messages
- **NFR4.4**: Extensive documentation and examples

---

## 🏗️ PHASED IMPLEMENTATION PLAN

---

## **PHASE 1: Architecture Foundation & Design**
**Objective**: Design the extensible execution framework with clear interfaces and abstractions.
**Duration**: 2 weeks
**Status**: Planning

### Phase Overview
Establish the architectural foundation for multi-execution-type support. This phase focuses on designing interfaces, abstractions, and integration points WITHOUT implementing concrete runners. All work is in Python (no PL/pgSQL changes yet).

### TDD Cycle 1.1: Execution Type Enum and Base Abstractions

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/runners/test_execution_types.py`

```python
def test_execution_type_enum_has_all_types():
    """Execution type enum defines all supported types"""
    from src.runners.execution_types import ExecutionType

    assert ExecutionType.HTTP in ExecutionType
    assert ExecutionType.SHELL in ExecutionType
    assert ExecutionType.DOCKER in ExecutionType
    assert ExecutionType.SERVERLESS in ExecutionType

def test_execution_type_has_metadata():
    """Each execution type has descriptive metadata"""
    from src.runners.execution_types import ExecutionType

    http_type = ExecutionType.HTTP
    assert http_type.display_name == "HTTP API"
    assert http_type.requires_network == True
    assert http_type.supports_streaming == False
```

**Expected Failure**: `ModuleNotFoundError: No module named 'src.runners'`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/runners/__init__.py`
```python
"""Job execution runner framework for SpecQL."""
```

**File**: `src/runners/execution_types.py`
```python
"""Execution type definitions and metadata."""

from enum import Enum
from dataclasses import dataclass


@dataclass
class ExecutionMetadata:
    """Metadata about an execution type."""
    display_name: str
    requires_network: bool
    supports_streaming: bool
    default_timeout: int  # seconds


class ExecutionType(Enum):
    """Supported execution types for job runners."""

    HTTP = ExecutionMetadata(
        display_name="HTTP API",
        requires_network=True,
        supports_streaming=False,
        default_timeout=300
    )

    SHELL = ExecutionMetadata(
        display_name="Shell Script",
        requires_network=False,
        supports_streaming=True,
        default_timeout=600
    )

    DOCKER = ExecutionMetadata(
        display_name="Docker Container",
        requires_network=False,
        supports_streaming=True,
        default_timeout=1800
    )

    SERVERLESS = ExecutionMetadata(
        display_name="Serverless Function",
        requires_network=True,
        supports_streaming=False,
        default_timeout=900
    )

    @property
    def display_name(self) -> str:
        return self.value.display_name

    @property
    def requires_network(self) -> bool:
        return self.value.requires_network

    @property
    def supports_streaming(self) -> bool:
        return self.value.supports_streaming

    @property
    def default_timeout(self) -> int:
        return self.value.default_timeout
```

**Run Test**: `uv run pytest tests/unit/runners/test_execution_types.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Add docstrings to all classes and methods
- Verify naming conventions match SpecQL patterns
- Run full test suite: `uv run pytest`

#### ✅ QA: Verify Quality
```bash
uv run pytest --tb=short
uv run ruff check src/runners/
uv run mypy src/runners/
```

---

### TDD Cycle 1.2: Job Runner Interface

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/runners/test_job_runner.py`

```python
def test_job_runner_interface_is_abstract():
    """JobRunner is an abstract base class"""
    from src.runners.job_runner import JobRunner

    # Cannot instantiate directly
    with pytest.raises(TypeError):
        JobRunner()

def test_job_runner_requires_abstract_methods():
    """Concrete runners must implement all abstract methods"""
    from src.runners.job_runner import JobRunner

    class IncompleteRunner(JobRunner):
        pass

    # Missing abstract methods
    with pytest.raises(TypeError):
        IncompleteRunner()

def test_job_runner_has_required_methods():
    """JobRunner interface defines required methods"""
    from src.runners.job_runner import JobRunner

    # Check method signatures exist
    assert hasattr(JobRunner, 'validate_config')
    assert hasattr(JobRunner, 'execute')
    assert hasattr(JobRunner, 'cancel')
    assert hasattr(JobRunner, 'get_resource_requirements')
```

**Expected Failure**: `ModuleNotFoundError: No module named 'src.runners.job_runner'`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/runners/job_runner.py`
```python
"""Abstract job runner interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ResourceRequirements:
    """Resource requirements for job execution."""
    cpu_cores: float = 1.0  # CPU cores (fractional allowed)
    memory_mb: int = 512    # Memory in MB
    disk_mb: int = 1024     # Disk space in MB
    timeout_seconds: int = 300  # Execution timeout


@dataclass
class JobRecord:
    """Job record from jobs.tb_job_run table."""
    id: str
    service_name: str
    operation: str
    input_data: dict[str, Any]
    timeout_seconds: int
    attempts: int
    max_attempts: int


@dataclass
class JobResult:
    """Result of job execution."""
    success: bool
    output_data: dict[str, Any] | None = None
    error_message: str | None = None
    duration_seconds: float | None = None
    resource_usage: dict[str, Any] | None = None


@dataclass
class ExecutionContext:
    """Runtime context for job execution."""
    tenant_id: str | None
    triggered_by: str | None
    correlation_id: str | None
    security_context: dict[str, Any] | None = None


class JobRunner(ABC):
    """
    Abstract interface for job execution runners.

    Each execution type (HTTP, Shell, Docker, Serverless) implements
    this interface to provide consistent job processing.
    """

    @abstractmethod
    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate runner-specific configuration.

        Args:
            config: Runner configuration from service registry

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult:
        """
        Execute the job.

        Args:
            job: Job record from database
            context: Execution context (tenant, user, etc.)

        Returns:
            JobResult with success/failure and output data
        """
        pass

    @abstractmethod
    async def cancel(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if job was successfully cancelled
        """
        pass

    @abstractmethod
    def get_resource_requirements(self, config: dict[str, Any]) -> ResourceRequirements:
        """
        Get resource requirements for this runner.

        Args:
            config: Runner configuration

        Returns:
            ResourceRequirements specifying CPU, memory, disk needs
        """
        pass
```

**Run Test**: `uv run pytest tests/unit/runners/test_job_runner.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Add comprehensive docstrings
- Ensure type hints are complete
- Add examples to docstrings

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/runners/ -v
uv run ruff check src/runners/
uv run mypy src/runners/
```

---

### TDD Cycle 1.3: Runner Registry

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/runners/test_runner_registry.py`

```python
def test_runner_registry_registers_runner():
    """Runner registry can register execution runners"""
    from src.runners.runner_registry import RunnerRegistry
    from src.runners.execution_types import ExecutionType

    registry = RunnerRegistry()

    # Mock runner
    class MockRunner:
        pass

    registry.register(ExecutionType.HTTP, MockRunner)

    assert registry.has_runner(ExecutionType.HTTP)
    assert registry.get_runner(ExecutionType.HTTP) == MockRunner

def test_runner_registry_raises_on_missing_runner():
    """Registry raises error for unregistered execution type"""
    from src.runners.runner_registry import RunnerRegistry
    from src.runners.execution_types import ExecutionType

    registry = RunnerRegistry()

    with pytest.raises(ValueError, match="No runner registered"):
        registry.get_runner(ExecutionType.DOCKER)

def test_runner_registry_singleton_pattern():
    """Runner registry uses singleton pattern"""
    from src.runners.runner_registry import RunnerRegistry

    registry1 = RunnerRegistry.get_instance()
    registry2 = RunnerRegistry.get_instance()

    assert registry1 is registry2
```

**Expected Failure**: `ModuleNotFoundError: No module named 'src.runners.runner_registry'`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/runners/runner_registry.py`
```python
"""Runner registry for execution type management."""

from typing import Type
from src.runners.execution_types import ExecutionType
from src.runners.job_runner import JobRunner


class RunnerRegistry:
    """
    Registry for job execution runners.

    Maps execution types to their corresponding runner implementations.
    Uses singleton pattern for global access.
    """

    _instance = None

    def __init__(self):
        """Initialize empty registry."""
        self._runners: dict[ExecutionType, Type[JobRunner]] = {}

    @classmethod
    def get_instance(cls) -> "RunnerRegistry":
        """Get singleton instance of runner registry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, execution_type: ExecutionType, runner_class: Type[JobRunner]) -> None:
        """
        Register a runner for an execution type.

        Args:
            execution_type: The execution type
            runner_class: The runner class to handle this type
        """
        self._runners[execution_type] = runner_class

    def has_runner(self, execution_type: ExecutionType) -> bool:
        """Check if runner is registered for execution type."""
        return execution_type in self._runners

    def get_runner(self, execution_type: ExecutionType) -> Type[JobRunner]:
        """
        Get runner class for execution type.

        Args:
            execution_type: The execution type

        Returns:
            Runner class for this execution type

        Raises:
            ValueError: If no runner registered for this type
        """
        if not self.has_runner(execution_type):
            raise ValueError(
                f"No runner registered for execution type: {execution_type.display_name}"
            )
        return self._runners[execution_type]
```

**Run Test**: `uv run pytest tests/unit/runners/test_runner_registry.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Add error messages with helpful suggestions
- Add method to list all registered runners
- Add validation for duplicate registrations

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/runners/ -v
uv run ruff check src/runners/
uv run mypy src/runners/
make test
```

---

### TDD Cycle 1.4: Service Registry Extension

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/registry/test_service_registry_execution_types.py`

```python
def test_service_registry_parses_execution_type():
    """Service registry parses execution_type from YAML"""
    yaml_content = """
    services:
      - name: test_shell
        type: script
        category: automation
        execution_type: shell
        operations:
          - name: run
            input_schema: {}
            output_schema: {}
    """

    registry = ServiceRegistry.from_yaml_string(yaml_content)
    service = registry.get_service("test_shell")

    assert service.execution_type == ExecutionType.SHELL

def test_service_registry_defaults_to_http():
    """Service registry defaults execution_type to HTTP for backward compatibility"""
    yaml_content = """
    services:
      - name: legacy_http
        type: api
        category: integration
        operations:
          - name: call
            input_schema: {}
            output_schema: {}
    """

    registry = ServiceRegistry.from_yaml_string(yaml_content)
    service = registry.get_service("legacy_http")

    # Should default to HTTP if not specified
    assert service.execution_type == ExecutionType.HTTP

def test_service_registry_parses_runner_config():
    """Service registry parses runner-specific configuration"""
    yaml_content = """
    services:
      - name: docker_service
        type: container
        category: compute
        execution_type: docker
        runner_config:
          image: "python:3.11"
          command: ["python", "script.py"]
          volumes:
            - "/data:/data"
        operations:
          - name: process
            input_schema: {}
            output_schema: {}
    """

    registry = ServiceRegistry.from_yaml_string(yaml_content)
    service = registry.get_service("docker_service")

    assert service.runner_config["image"] == "python:3.11"
    assert service.runner_config["command"] == ["python", "script.py"]
```

**Expected Failure**: `AttributeError: 'Service' object has no attribute 'execution_type'`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/registry/service_registry.py` (EDIT - extend existing Service class)

```python
# Add import
from src.runners.execution_types import ExecutionType

@dataclass
class Service:
    name: str
    type: str
    category: str
    operations: List[ServiceOperation]
    execution_type: ExecutionType = ExecutionType.HTTP  # NEW: Default to HTTP
    runner_config: Dict[str, Any] = field(default_factory=dict)  # NEW
    security_policy: Dict[str, Any] = field(default_factory=dict)  # NEW

    # ... existing methods ...
```

**File**: `src/registry/service_registry.py` (EDIT - extend from_yaml classmethod)

```python
@classmethod
def from_yaml(cls, path: str) -> "ServiceRegistry":
    """Load service registry from YAML file"""
    # ... existing file loading code ...

    for service_data in data.get("services", []):
        # ... existing validation ...

        # Parse execution type (NEW)
        execution_type_str = service_data.get("execution_type", "http").upper()
        try:
            execution_type = ExecutionType[execution_type_str]
        except KeyError:
            raise ValueError(
                f"Invalid execution_type '{execution_type_str}' for service {service_data['name']}. "
                f"Valid types: {[e.name.lower() for e in ExecutionType]}"
            )

        service = Service(
            name=service_data["name"],
            type=service_data["type"],
            category=service_data["category"],
            operations=operations,
            execution_type=execution_type,  # NEW
            runner_config=service_data.get("runner_config", {}),  # NEW
            security_policy=service_data.get("security_policy", {}),  # NEW
        )

        # ... rest of existing code ...

# Add helper method for testing
@classmethod
def from_yaml_string(cls, yaml_content: str) -> "ServiceRegistry":
    """Load service registry from YAML string (for testing)"""
    data = yaml.safe_load(yaml_content)
    # ... same parsing logic as from_yaml ...
```

**Run Test**: `uv run pytest tests/unit/registry/test_service_registry_execution_types.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Ensure backward compatibility with existing service definitions
- Add validation for runner_config based on execution type
- Update existing tests to handle new fields

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/registry/ -v
uv run pytest  # Ensure no regressions
uv run ruff check src/registry/
uv run mypy src/registry/
```

---

### Phase 1 Deliverables

- [ ] Execution type enum with metadata (`ExecutionType`)
- [ ] Abstract job runner interface (`JobRunner`)
- [ ] Runner registry with singleton pattern (`RunnerRegistry`)
- [ ] Extended service registry with execution types
- [ ] Extended AST models for runner configuration
- [ ] Comprehensive unit tests (100% coverage)
- [ ] Updated documentation

### Phase 1 Success Criteria

- [ ] All tests pass (`make test`)
- [ ] Type checking passes (`mypy`)
- [ ] Linting passes (`ruff`)
- [ ] No breaking changes to existing code
- [ ] Architecture allows for easy runner addition

---

## **PHASE 2: Database Schema Extension**
**Objective**: Extend PostgreSQL schema to support multi-execution types.
**Duration**: 1 week
**Status**: Planning

### Phase Overview
Extend the `jobs.tb_job_run` table and related database objects to track execution-type-specific information. This phase involves SQL schema changes and migrations.

### TDD Cycle 2.1: Extend Job Run Table Schema

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/schema/test_jobs_schema_execution_types.py`

```python
def test_jobs_schema_includes_execution_type():
    """Job run table includes execution_type column"""
    from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

    generator = JobsSchemaGenerator()
    sql = generator.generate()

    # Should include execution_type column
    assert "execution_type TEXT" in sql
    assert "DEFAULT 'http'" in sql  # Backward compatibility

def test_jobs_schema_includes_runner_config():
    """Job run table includes runner_config JSONB column"""
    from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

    generator = JobsSchemaGenerator()
    sql = generator.generate()

    # Should include runner_config for execution-specific settings
    assert "runner_config JSONB" in sql

def test_jobs_schema_includes_resource_usage():
    """Job run table includes resource_usage JSONB column"""
    from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

    generator = JobsSchemaGenerator()
    sql = generator.generate()

    # Should include resource_usage for tracking CPU/memory/duration
    assert "resource_usage JSONB" in sql

def test_jobs_schema_includes_security_context():
    """Job run table includes security_context JSONB column"""
    from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

    generator = JobsSchemaGenerator()
    sql = generator.generate()

    # Should include security_context for audit trail
    assert "security_context JSONB" in sql
```

**Expected Failure**: `AssertionError: execution_type TEXT not in sql`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/generators/schema/jobs_schema_generator.py` (EDIT)

```python
def _generate_job_run_table(self) -> str:
    """Generate tb_job_run table with all required columns"""
    columns = [
        "id UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        "identifier TEXT NOT NULL UNIQUE",
        "idempotency_key TEXT",
        "service_name TEXT NOT NULL",
        "operation TEXT NOT NULL",

        # Execution type support (NEW)
        "execution_type TEXT NOT NULL DEFAULT 'http' CHECK (execution_type IN ('http', 'shell', 'docker', 'serverless'))",
        "runner_config JSONB",
        "resource_usage JSONB",
        "security_context JSONB",

        # Input/output/error (existing)
        "input_data JSONB",
        "output_data JSONB",
        "error_message TEXT",

        # Status and retry (existing)
        "status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))",
        "attempts INTEGER DEFAULT 0",
        "max_attempts INTEGER DEFAULT 3",
        "timeout_seconds INTEGER",

        # Context (existing)
        "tenant_id UUID",
        "triggered_by UUID",
        "correlation_id TEXT",
        "entity_type TEXT",
        "entity_pk TEXT",

        # Timestamps (existing)
        "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        "started_at TIMESTAMP WITH TIME ZONE",
        "completed_at TIMESTAMP WITH TIME ZONE",
        "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
    ]

    return f"""
CREATE TABLE jobs.tb_job_run (
    {self._format_columns(columns)}
);
"""
```

**Run Test**: `uv run pytest tests/unit/schema/test_jobs_schema_execution_types.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Add comments explaining new columns
- Ensure consistent formatting
- Update existing tests

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/schema/ -v
uv run pytest  # Full suite
```

---

### TDD Cycle 2.2: Add Execution-Type-Aware Indexes

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/schema/test_jobs_schema_indexes.py`

```python
def test_jobs_schema_indexes_execution_type():
    """Job schema includes index on execution_type for filtering"""
    from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

    generator = JobsSchemaGenerator()
    sql = generator.generate()

    # Index for filtering by execution type
    assert "CREATE INDEX idx_tb_job_run_execution_type" in sql
    assert "ON jobs.tb_job_run (execution_type, status)" in sql

def test_jobs_schema_indexes_resource_usage():
    """Job schema includes GIN index on resource_usage JSONB"""
    from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

    generator = JobsSchemaGenerator()
    sql = generator.generate()

    # GIN index for JSONB queries
    assert "CREATE INDEX idx_tb_job_run_resource_usage" in sql
    assert "USING gin (resource_usage)" in sql
```

**Expected Failure**: `AssertionError`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/generators/schema/jobs_schema_generator.py` (EDIT)

```python
def _generate_indexes(self) -> str:
    """Generate indexes for efficient job polling and querying"""
    indexes = [
        # Existing indexes...
        self._create_index(
            "idx_tb_job_run_pending",
            "jobs.tb_job_run (status, created_at)",
            "WHERE status = 'pending'",
        ),
        # ... other existing indexes ...

        # NEW: Execution type index
        self._create_index(
            "idx_tb_job_run_execution_type",
            "jobs.tb_job_run (execution_type, status, created_at)",
        ),

        # NEW: Resource usage JSONB index
        "CREATE INDEX idx_tb_job_run_resource_usage ON jobs.tb_job_run USING gin (resource_usage);",
    ]

    return "\n\n".join(indexes)
```

**Run Test**: `uv run pytest tests/unit/schema/test_jobs_schema_indexes.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Ensure index naming is consistent
- Add comments explaining index purpose

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/schema/ -v
make test
```

---

### TDD Cycle 2.3: Extend Observability Views

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/schema/test_jobs_observability_views.py`

```python
def test_observability_view_execution_performance():
    """Observability includes v_execution_performance_by_type view"""
    from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

    generator = JobsSchemaGenerator()
    sql = generator.generate()

    # View for execution performance by type
    assert "CREATE VIEW jobs.v_execution_performance_by_type" in sql
    assert "execution_type" in sql
    assert "avg_duration_sec" in sql

def test_observability_view_resource_usage():
    """Observability includes v_resource_usage_by_runner view"""
    from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

    generator = JobsSchemaGenerator()
    sql = generator.generate()

    # View for resource usage tracking
    assert "CREATE VIEW jobs.v_resource_usage_by_runner" in sql
    assert "resource_usage" in sql
```

**Expected Failure**: `AssertionError`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/generators/schema/jobs_schema_generator.py` (EDIT)

```python
def _generate_observability_views(self) -> str:
    """Generate observability views for monitoring job execution"""
    views = [
        # ... existing views ...

        # NEW: Execution performance by type
        self._create_view(
            "v_execution_performance_by_type",
            """
SELECT
    execution_type,
    service_name,
    operation,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_jobs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))::numeric(10,2) as avg_duration_sec,
    PERCENTILE_CONT(0.95) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))
    )::numeric(10,2) as p95_duration_sec,
    PERCENTILE_CONT(0.99) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))
    )::numeric(10,2) as p99_duration_sec
FROM jobs.tb_job_run
WHERE started_at IS NOT NULL
    AND created_at > now() - interval '7 days'
GROUP BY execution_type, service_name, operation
ORDER BY total_jobs DESC;
""",
        ),

        # NEW: Resource usage by runner
        self._create_view(
            "v_resource_usage_by_runner",
            """
SELECT
    execution_type,
    service_name,
    operation,
    COUNT(*) as total_jobs,
    AVG((resource_usage->>'cpu_usage_percent')::numeric)::numeric(10,2) as avg_cpu_percent,
    AVG((resource_usage->>'memory_mb')::numeric)::numeric(10,2) as avg_memory_mb,
    AVG((resource_usage->>'duration_seconds')::numeric)::numeric(10,2) as avg_duration_sec,
    MAX((resource_usage->>'peak_memory_mb')::numeric)::numeric(10,2) as max_memory_mb
FROM jobs.tb_job_run
WHERE resource_usage IS NOT NULL
    AND created_at > now() - interval '24 hours'
GROUP BY execution_type, service_name, operation
ORDER BY avg_memory_mb DESC;
""",
        ),

        # NEW: Runner failure patterns
        self._create_view(
            "v_runner_failure_patterns",
            """
SELECT
    execution_type,
    service_name,
    operation,
    COUNT(*) as failure_count,
    ARRAY_AGG(DISTINCT error_message) as error_types,
    AVG(attempts)::numeric(10,2) as avg_attempts_before_failure,
    MAX(updated_at) as last_failure
FROM jobs.tb_job_run
WHERE status = 'failed'
    AND attempts >= max_attempts
    AND created_at > now() - interval '24 hours'
GROUP BY execution_type, service_name, operation
ORDER BY failure_count DESC;
""",
        ),
    ]

    return "\n\n".join(views)
```

**Run Test**: `uv run pytest tests/unit/schema/test_jobs_observability_views.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Ensure view names follow conventions
- Add helpful comments
- Optimize query performance

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/schema/ -v
make test
```

---

### Phase 2 Deliverables

- [ ] Extended `jobs.tb_job_run` table schema
- [ ] New indexes for execution type filtering
- [ ] GIN indexes for JSONB columns
- [ ] Execution-type-aware observability views
- [ ] Migration scripts (if needed)
- [ ] Updated schema documentation

### Phase 2 Success Criteria

- [ ] All schema tests pass
- [ ] Backward compatibility maintained (existing HTTP jobs work)
- [ ] Observability views provide actionable insights
- [ ] Indexes improve query performance

---

## **PHASE 3: Compiler Integration**
**Objective**: Extend CallServiceStepCompiler to support multiple execution types.
**Duration**: 2 weeks
**Status**: Planning

### Phase Overview
Modify the `CallServiceStepCompiler` to detect execution type from the service registry and generate appropriate PL/pgSQL code with runner-specific configuration.

### TDD Cycle 3.1: Execution Type Detection

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/actions/step_compilers/test_call_service_execution_types.py`

```python
def test_call_service_compiler_detects_http_type():
    """Compiler detects HTTP execution type from service registry"""
    from src.generators.actions.step_compilers.call_service_step_compiler import CallServiceStepCompiler
    from src.generators.actions.action_context import ActionContext
    from src.core.ast_models import ActionStep

    # Mock service registry with HTTP service
    step = ActionStep(
        type="call_service",
        service="stripe",
        operation="create_charge",
        input={"amount": "$order.total"}
    )

    context = ActionContext(entity_name="Order", schema_name="orders")
    compiler = CallServiceStepCompiler(step, context)

    execution_type = compiler.get_execution_type()

    assert execution_type == ExecutionType.HTTP

def test_call_service_compiler_detects_shell_type():
    """Compiler detects Shell execution type from service registry"""
    step = ActionStep(
        type="call_service",
        service="data_processor",
        operation="run_etl",
        input={"file": "$batch.input_file"}
    )

    context = ActionContext(entity_name="Batch", schema_name="jobs")
    compiler = CallServiceStepCompiler(step, context)

    execution_type = compiler.get_execution_type()

    assert execution_type == ExecutionType.SHELL
```

**Expected Failure**: `AttributeError: 'CallServiceStepCompiler' object has no attribute 'get_execution_type'`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/generators/actions/step_compilers/call_service_step_compiler.py` (EDIT)

```python
# Add imports
from src.registry.service_registry import ServiceRegistry
from src.runners.execution_types import ExecutionType

class CallServiceStepCompiler:
    """Compiles call_service steps to PL/pgSQL job queueing"""

    def __init__(self, step: ActionStep, context: ActionContext, registry_path: str = "registry/service_registry.yaml"):
        self.step = step
        self.context = context
        self.registry = ServiceRegistry.from_yaml(registry_path)  # NEW

    def get_execution_type(self) -> ExecutionType:
        """
        Determine execution type from service registry.

        Returns:
            ExecutionType for this service
        """
        service = self.registry.get_service(self.step.service)
        return service.execution_type

    # ... rest of existing code ...
```

**Run Test**: `uv run pytest tests/unit/actions/step_compilers/test_call_service_execution_types.py::test_call_service_compiler_detects_http_type -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Cache service registry to avoid repeated file reads
- Add error handling for missing services
- Update existing tests to provide registry path

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/actions/step_compilers/ -v
make test
```

---

### TDD Cycle 3.2: Generate Execution Type in SQL

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/actions/step_compilers/test_call_service_sql_generation.py`

```python
def test_compiled_sql_includes_execution_type():
    """Compiled SQL includes execution_type column"""
    step = ActionStep(
        type="call_service",
        service="stripe",
        operation="create_charge",
        input={"amount": 1000}
    )

    context = ActionContext(entity_name="Order", schema_name="orders")
    compiler = CallServiceStepCompiler(step, context)

    sql = compiler.compile()

    # Should include execution_type in INSERT
    assert "execution_type" in sql
    assert "'http'" in sql.lower()

def test_compiled_sql_includes_runner_config():
    """Compiled SQL includes runner_config JSONB"""
    step = ActionStep(
        type="call_service",
        service="docker_processor",
        operation="process",
        input={"data": "$batch.data"}
    )

    context = ActionContext(entity_name="Batch", schema_name="jobs")
    compiler = CallServiceStepCompiler(step, context)

    sql = compiler.compile()

    # Should include runner_config from service registry
    assert "runner_config" in sql
    assert "jsonb_build_object" in sql or "'image'" in sql
```

**Expected Failure**: `AssertionError: execution_type not in sql`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/generators/actions/step_compilers/call_service_step_compiler.py` (EDIT)

```python
def compile(self) -> str:
    """Compile call_service step to INSERT INTO jobs.tb_job_run"""
    self._validate_step()

    execution_type = self.get_execution_type()

    return f"""
    -- Queue job for {self.step.service}.{self.step.operation} ({execution_type.display_name})
    INSERT INTO jobs.tb_job_run (
        identifier,
        idempotency_key,
        service_name,
        operation,
        execution_type,  -- NEW
        runner_config,   -- NEW
        input_data,
        tenant_id,
        triggered_by,
        correlation_id,
        entity_type,
        entity_pk,
        max_attempts,
        timeout_seconds
    ) VALUES (
        {self._generate_identifier()},
        {self._generate_idempotency_key()},
        '{self.step.service}',
        '{self.step.operation}',
        '{execution_type.name.lower()}',  -- NEW
        {self._compile_runner_config()},  -- NEW
        {self._compile_input_data()},
        _tenant_id,
        _user_id,
        {self._compile_correlation()},
        '{self.context.entity_name}',
        {self._compile_entity_pk()},
        {self._compile_max_attempts()},
        {self._compile_timeout()}
    ) RETURNING id INTO _job_id_{self._job_var_suffix()};
    """

def _compile_runner_config(self) -> str:
    """
    Compile runner-specific configuration to JSONB.

    Returns:
        PL/pgSQL expression for runner_config JSONB
    """
    service = self.registry.get_service(self.step.service)

    if not service.runner_config:
        return "NULL"

    # Convert runner_config dict to JSONB literal
    import json
    return f"'{json.dumps(service.runner_config)}'::jsonb"
```

**Run Test**: `uv run pytest tests/unit/actions/step_compilers/test_call_service_sql_generation.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Use proper JSONB construction instead of string interpolation
- Add validation for runner_config format
- Update integration tests

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/actions/step_compilers/ -v
uv run pytest tests/integration/actions/ -v
make test
```

---

### TDD Cycle 3.3: Security Context Compilation

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/actions/step_compilers/test_call_service_security.py`

```python
def test_compiled_sql_includes_security_context():
    """Compiled SQL includes security_context JSONB"""
    step = ActionStep(
        type="call_service",
        service="shell_script",
        operation="run",
        input={"command": "process_data"}
    )

    context = ActionContext(entity_name="Job", schema_name="jobs")
    compiler = CallServiceStepCompiler(step, context)

    sql = compiler.compile()

    # Should include security_context with allowed commands
    assert "security_context" in sql
    assert "allowed_commands" in sql or "security_policy" in sql

def test_security_context_includes_tenant_isolation():
    """Security context includes tenant_id for isolation"""
    step = ActionStep(
        type="call_service",
        service="docker_job",
        operation="process",
        input={}
    )

    context = ActionContext(entity_name="Task", schema_name="jobs")
    compiler = CallServiceStepCompiler(step, context)

    sql = compiler.compile()

    # Security context should reference tenant_id
    assert "_tenant_id" in sql
```

**Expected Failure**: `AssertionError: security_context not in sql`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/generators/actions/step_compilers/call_service_step_compiler.py` (EDIT)

```python
def compile(self) -> str:
    """Compile call_service step to INSERT INTO jobs.tb_job_run"""
    self._validate_step()

    execution_type = self.get_execution_type()

    return f"""
    -- Queue job for {self.step.service}.{self.step.operation} ({execution_type.display_name})
    INSERT INTO jobs.tb_job_run (
        identifier,
        idempotency_key,
        service_name,
        operation,
        execution_type,
        runner_config,
        security_context,  -- NEW
        input_data,
        tenant_id,
        triggered_by,
        correlation_id,
        entity_type,
        entity_pk,
        max_attempts,
        timeout_seconds
    ) VALUES (
        {self._generate_identifier()},
        {self._generate_idempotency_key()},
        '{self.step.service}',
        '{self.step.operation}',
        '{execution_type.name.lower()}',
        {self._compile_runner_config()},
        {self._compile_security_context()},  -- NEW
        {self._compile_input_data()},
        _tenant_id,
        _user_id,
        {self._compile_correlation()},
        '{self.context.entity_name}',
        {self._compile_entity_pk()},
        {self._compile_max_attempts()},
        {self._compile_timeout()}
    ) RETURNING id INTO _job_id_{self._job_var_suffix()};
    """

def _compile_security_context(self) -> str:
    """
    Compile security context for job execution.

    Returns:
        PL/pgSQL expression for security_context JSONB
    """
    service = self.registry.get_service(self.step.service)

    # Build security context from service policy
    security_context = {
        "tenant_id_ref": "_tenant_id",  # Will be resolved at runtime
        "triggered_by_ref": "_user_id",
        "policy": service.security_policy,
    }

    import json
    return f"'{json.dumps(security_context)}'::jsonb"
```

**Run Test**: `uv run pytest tests/unit/actions/step_compilers/test_call_service_security.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Improve security context structure
- Add validation for security policies
- Document security context format

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/actions/step_compilers/ -v
make test
```

---

### Phase 3 Deliverables

- [ ] Extended CallServiceStepCompiler with execution type detection
- [ ] SQL generation includes execution_type, runner_config, security_context
- [ ] Service registry integration for configuration lookup
- [ ] Security context compilation
- [ ] Updated integration tests

### Phase 3 Success Criteria

- [ ] All compiler tests pass
- [ ] Generated SQL includes all new columns
- [ ] Backward compatibility with HTTP-only services
- [ ] Integration tests demonstrate end-to-end flow

---

## **PHASE 4: HTTP Runner Implementation**
**Objective**: Extract existing HTTP logic into HTTPRunner class.
**Duration**: 1 week
**Status**: Planning

### Phase Overview
Refactor existing HTTP job execution logic into a concrete `HTTPRunner` implementation. This establishes the pattern for future runners and ensures backward compatibility.

### TDD Cycle 4.1: HTTPRunner Implementation

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/runners/test_http_runner.py`

```python
@pytest.mark.asyncio
async def test_http_runner_executes_get_request():
    """HTTPRunner executes HTTP GET requests"""
    from src.runners.http_runner import HTTPRunner
    from src.runners.job_runner import JobRecord, ExecutionContext

    runner = HTTPRunner()

    job = JobRecord(
        id="test-job-1",
        service_name="test_api",
        operation="get_data",
        input_data={"endpoint": "https://api.example.com/data"},
        timeout_seconds=30,
        attempts=0,
        max_attempts=3
    )

    context = ExecutionContext(
        tenant_id="tenant-1",
        triggered_by="user-1",
        correlation_id="corr-1"
    )

    result = await runner.execute(job, context)

    assert result.success == True
    assert result.output_data is not None

@pytest.mark.asyncio
async def test_http_runner_validates_config():
    """HTTPRunner validates runner configuration"""
    from src.runners.http_runner import HTTPRunner

    runner = HTTPRunner()

    # Valid config
    valid_config = {
        "base_url": "https://api.example.com",
        "auth_type": "bearer",
        "timeout": 30
    }

    assert await runner.validate_config(valid_config) == True

    # Invalid config
    invalid_config = {
        "base_url": "not-a-url",
    }

    with pytest.raises(ValueError, match="Invalid base_url"):
        await runner.validate_config(invalid_config)
```

**Expected Failure**: `ModuleNotFoundError: No module named 'src.runners.http_runner'`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/runners/http_runner.py`

```python
"""HTTP API execution runner."""

import httpx
from typing import Any
from src.runners.job_runner import JobRunner, JobRecord, JobResult, ExecutionContext, ResourceRequirements
from src.runners.execution_types import ExecutionType


class HTTPRunner(JobRunner):
    """
    HTTP API execution runner.

    Executes jobs by making HTTP requests to external APIs.
    Supports GET, POST, PUT, DELETE methods with authentication.
    """

    def __init__(self):
        """Initialize HTTP runner with httpx client."""
        self.client = httpx.AsyncClient()

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate HTTP runner configuration.

        Required fields:
        - base_url: Base URL for API

        Optional fields:
        - auth_type: Authentication type (bearer, basic, api_key)
        - headers: Default headers
        - timeout: Request timeout
        """
        if "base_url" not in config:
            raise ValueError("HTTP runner requires 'base_url' in config")

        base_url = config["base_url"]
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            raise ValueError(f"Invalid base_url: {base_url}")

        return True

    async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult:
        """
        Execute HTTP API call.

        Args:
            job: Job record with input_data containing request details
            context: Execution context

        Returns:
            JobResult with API response
        """
        try:
            # Extract request details from input_data
            endpoint = job.input_data.get("endpoint", "")
            method = job.input_data.get("method", "GET").upper()
            payload = job.input_data.get("payload")
            headers = job.input_data.get("headers", {})

            # Make HTTP request
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=payload if method in ["POST", "PUT", "PATCH"] else None,
                headers=headers,
                timeout=job.timeout_seconds
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            output_data = response.json() if response.content else {}

            return JobResult(
                success=True,
                output_data=output_data,
                duration_seconds=response.elapsed.total_seconds(),
                resource_usage={
                    "status_code": response.status_code,
                    "response_size_bytes": len(response.content),
                }
            )

        except httpx.HTTPStatusError as e:
            return JobResult(
                success=False,
                error_message=f"HTTP {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            return JobResult(
                success=False,
                error_message=f"HTTP request failed: {str(e)}",
            )

    async def cancel(self, job_id: str) -> bool:
        """
        Cancel HTTP request.

        Note: HTTP requests are typically short-lived and cannot be cancelled
        once started. This is a no-op.
        """
        return False

    def get_resource_requirements(self, config: dict[str, Any]) -> ResourceRequirements:
        """Get resource requirements for HTTP runner."""
        return ResourceRequirements(
            cpu_cores=0.1,  # Minimal CPU
            memory_mb=128,  # Small memory footprint
            disk_mb=0,      # No disk usage
            timeout_seconds=config.get("timeout", 300)
        )
```

**Run Test**: `uv run pytest tests/unit/runners/test_http_runner.py -v`
**Expected**: ✅ PASSED (with mocked HTTP responses)

#### 🔧 REFACTOR: Clean Up
- Add authentication support (Bearer, API key)
- Add retry logic with exponential backoff
- Improve error handling and logging

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/runners/test_http_runner.py -v
make test
```

---

### TDD Cycle 4.2: Register HTTP Runner

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/runners/test_runner_registration.py`

```python
def test_http_runner_is_registered():
    """HTTP runner is registered in runner registry"""
    from src.runners.runner_registry import RunnerRegistry
    from src.runners.execution_types import ExecutionType

    registry = RunnerRegistry.get_instance()

    # HTTP runner should be auto-registered
    assert registry.has_runner(ExecutionType.HTTP)

    runner_class = registry.get_runner(ExecutionType.HTTP)
    assert runner_class.__name__ == "HTTPRunner"
```

**Expected Failure**: `AssertionError: HTTP runner not registered`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/runners/__init__.py` (EDIT)

```python
"""Job execution runner framework for SpecQL."""

# Auto-register runners on module import
from src.runners.runner_registry import RunnerRegistry
from src.runners.execution_types import ExecutionType
from src.runners.http_runner import HTTPRunner

# Register HTTP runner
_registry = RunnerRegistry.get_instance()
_registry.register(ExecutionType.HTTP, HTTPRunner)

__all__ = ["RunnerRegistry", "ExecutionType", "HTTPRunner"]
```

**Run Test**: `uv run pytest tests/unit/runners/test_runner_registration.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Add module docstrings
- Document registration pattern

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/runners/ -v
make test
```

---

### Phase 4 Deliverables

- [ ] HTTPRunner implementation with full HTTP support
- [ ] HTTP authentication (Bearer, API Key, Basic)
- [ ] Retry logic with exponential backoff
- [ ] Auto-registration in RunnerRegistry
- [ ] Comprehensive unit tests
- [ ] Integration tests with real API calls (mocked)

### Phase 4 Success Criteria

- [ ] All HTTP runner tests pass
- [ ] Backward compatibility with existing HTTP services
- [ ] Error handling covers all HTTP failure modes
- [ ] Resource usage tracking works

---

## **PHASE 5: Shell Script Runner**
**Objective**: Implement shell script execution with security controls.
**Duration**: 2 weeks
**Status**: Planning

### Phase Overview
Implement `ShellScriptRunner` to execute local shell commands with comprehensive security controls (command allowlists, resource limits, sandboxing).

### TDD Cycle 5.1: Shell Script Runner Core

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/runners/test_shell_runner.py`

```python
@pytest.mark.asyncio
async def test_shell_runner_executes_command():
    """ShellScriptRunner executes shell commands"""
    from src.runners.shell_runner import ShellScriptRunner
    from src.runners.job_runner import JobRecord, ExecutionContext

    runner = ShellScriptRunner()

    job = JobRecord(
        id="test-job-shell-1",
        service_name="data_processor",
        operation="run",
        input_data={
            "command": "echo",
            "args": ["Hello", "World"]
        },
        timeout_seconds=30,
        attempts=0,
        max_attempts=3
    )

    context = ExecutionContext(
        tenant_id="tenant-1",
        triggered_by="user-1",
        correlation_id="corr-1",
        security_context={
            "allowed_commands": ["/usr/bin/echo"]
        }
    )

    result = await runner.execute(job, context)

    assert result.success == True
    assert "Hello World" in result.output_data["stdout"]

@pytest.mark.asyncio
async def test_shell_runner_blocks_disallowed_commands():
    """ShellScriptRunner blocks commands not in allowlist"""
    from src.runners.shell_runner import ShellScriptRunner

    runner = ShellScriptRunner()

    job = JobRecord(
        id="test-job-shell-2",
        service_name="malicious",
        operation="run",
        input_data={
            "command": "rm",
            "args": ["-rf", "/"]
        },
        timeout_seconds=30,
        attempts=0,
        max_attempts=3
    )

    context = ExecutionContext(
        tenant_id="tenant-1",
        triggered_by="user-1",
        correlation_id="corr-1",
        security_context={
            "allowed_commands": ["/usr/bin/echo"]  # rm not allowed
        }
    )

    result = await runner.execute(job, context)

    assert result.success == False
    assert "not allowed" in result.error_message.lower()
```

**Expected Failure**: `ModuleNotFoundError: No module named 'src.runners.shell_runner'`

#### 🟢 GREEN: Minimal Implementation
**File**: `src/runners/shell_runner.py`

```python
"""Shell script execution runner with security controls."""

import asyncio
import shlex
from pathlib import Path
from typing import Any

from src.runners.job_runner import (
    JobRunner,
    JobRecord,
    JobResult,
    ExecutionContext,
    ResourceRequirements,
)


class ShellScriptRunner(JobRunner):
    """
    Shell script execution runner.

    Executes shell commands with comprehensive security controls:
    - Command allowlisting
    - Resource limits (CPU, memory, timeout)
    - Working directory restrictions
    - Environment variable control
    """

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate shell runner configuration.

        Required fields:
        - allowed_commands: List of allowed command paths

        Optional fields:
        - working_directory: Working directory for execution
        - environment: Environment variables
        - resource_limits: CPU/memory limits
        """
        if "allowed_commands" not in config:
            raise ValueError("Shell runner requires 'allowed_commands' in config")

        allowed = config["allowed_commands"]
        if not isinstance(allowed, list) or len(allowed) == 0:
            raise ValueError("'allowed_commands' must be a non-empty list")

        # Validate all commands are absolute paths
        for cmd in allowed:
            if not Path(cmd).is_absolute():
                raise ValueError(f"Commands must be absolute paths: {cmd}")

        return True

    async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult:
        """
        Execute shell command with security checks.

        Args:
            job: Job record with command and args in input_data
            context: Execution context with security policy

        Returns:
            JobResult with stdout/stderr and exit code
        """
        try:
            # Extract command details
            command = job.input_data.get("command")
            args = job.input_data.get("args", [])
            env_vars = job.input_data.get("env_vars", {})

            if not command:
                return JobResult(
                    success=False,
                    error_message="No command specified in input_data"
                )

            # Security check: Validate command is allowed
            security_context = context.security_context or {}
            allowed_commands = security_context.get("allowed_commands", [])

            # Resolve command to absolute path
            command_path = self._resolve_command_path(command)

            if command_path not in allowed_commands:
                return JobResult(
                    success=False,
                    error_message=f"Command '{command}' is not allowed. Allowed commands: {allowed_commands}"
                )

            # Build command with args
            cmd_list = [command_path] + args

            # Execute command with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd_list,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env_vars if env_vars else None
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=job.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return JobResult(
                    success=False,
                    error_message=f"Command timed out after {job.timeout_seconds} seconds"
                )

            # Check exit code
            exit_code = process.returncode
            success = exit_code == 0

            output_data = {
                "exit_code": exit_code,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
            }

            if success:
                return JobResult(
                    success=True,
                    output_data=output_data,
                )
            else:
                return JobResult(
                    success=False,
                    error_message=f"Command exited with code {exit_code}",
                    output_data=output_data,
                )

        except Exception as e:
            return JobResult(
                success=False,
                error_message=f"Shell execution failed: {str(e)}"
            )

    def _resolve_command_path(self, command: str) -> str:
        """
        Resolve command to absolute path.

        Args:
            command: Command name or path

        Returns:
            Absolute path to command
        """
        if Path(command).is_absolute():
            return command

        # Search in common paths
        common_paths = [
            "/usr/bin",
            "/usr/local/bin",
            "/bin",
        ]

        for path_dir in common_paths:
            full_path = Path(path_dir) / command
            if full_path.exists():
                return str(full_path)

        # Return as-is if not found (will fail allowlist check)
        return command

    async def cancel(self, job_id: str) -> bool:
        """
        Cancel running shell command.

        TODO: Implement process tracking and cancellation
        """
        return False

    def get_resource_requirements(self, config: dict[str, Any]) -> ResourceRequirements:
        """Get resource requirements for shell runner."""
        limits = config.get("resource_limits", {})

        return ResourceRequirements(
            cpu_cores=limits.get("cpu", 1.0),
            memory_mb=limits.get("memory_mb", 512),
            disk_mb=limits.get("disk_mb", 1024),
            timeout_seconds=limits.get("timeout", 600)
        )
```

**Run Test**: `uv run pytest tests/unit/runners/test_shell_runner.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Add process tracking for cancellation
- Add resource limit enforcement (cgroups on Linux)
- Improve error messages
- Add comprehensive logging

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/runners/test_shell_runner.py -v
make test
```

---

### TDD Cycle 5.2: Resource Limit Enforcement

#### 🔴 RED: Write Failing Test
**Test File**: `tests/unit/runners/test_shell_runner_limits.py`

```python
@pytest.mark.asyncio
async def test_shell_runner_enforces_memory_limit():
    """ShellScriptRunner enforces memory limits"""
    from src.runners.shell_runner import ShellScriptRunner

    runner = ShellScriptRunner()

    # Job that tries to allocate too much memory
    job = JobRecord(
        id="test-job-memory",
        service_name="memory_hog",
        operation="allocate",
        input_data={
            "command": "python",
            "args": ["-c", "x = ' ' * (1024 * 1024 * 1024)"]  # 1GB
        },
        timeout_seconds=30,
        attempts=0,
        max_attempts=3
    )

    context = ExecutionContext(
        tenant_id="tenant-1",
        triggered_by="user-1",
        correlation_id="corr-1",
        security_context={
            "allowed_commands": ["/usr/bin/python"],
            "resource_limits": {
                "memory_mb": 128  # Only 128MB allowed
            }
        }
    )

    result = await runner.execute(job, context)

    # Should fail due to memory limit
    assert result.success == False
    assert "memory" in result.error_message.lower()
```

**Expected Failure**: Test runs but doesn't enforce memory limits

#### 🟢 GREEN: Minimal Implementation
**File**: `src/runners/shell_runner.py` (EDIT - add resource limit enforcement)

```python
# Add import
import resource  # For setrlimit

async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult:
    """Execute shell command with resource limits."""
    try:
        # ... existing security checks ...

        # Extract resource limits
        security_context = context.security_context or {}
        resource_limits = security_context.get("resource_limits", {})

        # Prepare preexec_fn for resource limits
        def set_limits():
            """Set resource limits before executing command."""
            # Memory limit
            if "memory_mb" in resource_limits:
                memory_bytes = resource_limits["memory_mb"] * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

            # CPU time limit
            if "cpu_seconds" in resource_limits:
                cpu_seconds = resource_limits["cpu_seconds"]
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))

        # Execute with limits
        process = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env_vars if env_vars else None,
            preexec_fn=set_limits  # Apply limits
        )

        # ... rest of existing code ...
```

**Run Test**: `uv run pytest tests/unit/runners/test_shell_runner_limits.py -v`
**Expected**: ✅ PASSED

#### 🔧 REFACTOR: Clean Up
- Add cross-platform support (resource limits Linux-specific)
- Add disk usage limits
- Improve error messages for limit violations

#### ✅ QA: Verify Quality
```bash
uv run pytest tests/unit/runners/test_shell_runner_limits.py -v
make test
```

---

### Phase 5 Deliverables

- [ ] ShellScriptRunner with command execution
- [ ] Command allowlisting (security)
- [ ] Resource limit enforcement (CPU, memory, timeout)
- [ ] Working directory restrictions
- [ ] Process tracking and cancellation
- [ ] Comprehensive security tests

### Phase 5 Success Criteria

- [ ] All shell runner tests pass
- [ ] Security controls prevent unauthorized command execution
- [ ] Resource limits are enforced
- [ ] Error handling covers all failure modes

---

## **PHASE 6: Docker Runner**
**Objective**: Implement Docker container execution.
**Duration**: 2 weeks
**Status**: Planning

### Phase Overview
Implement `DockerRunner` to execute jobs in Docker containers with image allowlisting, volume mounting, and resource controls.

### Implementation Pattern
Similar to Phase 5, implement:
- DockerRunner with Docker SDK
- Image allowlisting and validation
- Volume mounting (with security checks)
- Container resource limits (CPU, memory)
- Container lifecycle management (start, monitor, cleanup)
- Network isolation

**Key Tests**:
- Container execution
- Image allowlisting
- Resource limits
- Volume mounting
- Container cleanup

---

## **PHASE 7: Serverless Runner**
**Objective**: Implement serverless function invocation.
**Duration**: 2 weeks
**Status**: Planning

### Phase Overview
Implement `ServerlessRunner` to invoke cloud functions (AWS Lambda, Google Cloud Functions) with authentication and async result handling.

### Implementation Pattern
Similar to Phase 4 (HTTP), implement:
- ServerlessRunner with cloud SDK integration
- Authentication with cloud providers
- Async invocation with result polling
- Cost tracking
- Error handling and retries

**Key Tests**:
- Lambda invocation
- Authentication
- Async result handling
- Cost tracking
- Timeout handling

---

## **PHASE 8: Frontend Integration**
**Objective**: Generate TypeScript types and Apollo hooks for job monitoring.
**Duration**: 1 week
**Status**: Planning

### Phase Overview
Extend frontend code generation to include:
- TypeScript types for new job fields (execution_type, runner_config)
- Apollo hooks for job monitoring queries
- Execution-type-specific UI components

### Deliverables
- Extended TypeScript type generation
- Job monitoring hooks (useJobStatus, useJobsByExecutionType)
- Documentation for frontend integration

---

## **PHASE 9: Documentation & Examples**
**Objective**: Complete documentation and usage examples.
**Duration**: 1 week
**Status**: Planning

### Deliverables
- Architecture overview document
- Configuration reference for each execution type
- Security guidelines and best practices
- Troubleshooting guide
- Migration guide for existing HTTP services
- Example SpecQL files for each execution type

---

## **PHASE 10: Testing & QA**
**Objective**: Comprehensive testing across all execution types.
**Duration**: 2 weeks
**Status**: Planning

### Testing Strategy

#### Unit Tests
- [ ] 100% coverage for runner implementations
- [ ] Configuration validation tests
- [ ] Error handling tests
- [ ] Resource management tests

#### Integration Tests
- [ ] End-to-end job execution workflows
- [ ] Multi-execution-type scenarios
- [ ] Retry and timeout behavior
- [ ] Observability view queries

#### Security Tests
- [ ] Command injection prevention
- [ ] Resource exhaustion attacks
- [ ] Configuration tampering
- [ ] Network isolation verification

#### Performance Tests
- [ ] Concurrent job execution (1000+ jobs/minute)
- [ ] Runner overhead measurement
- [ ] Memory profiling
- [ ] Scalability testing

---

## 📈 Success Metrics

### Functional Completeness
- [ ] All 4 execution types implemented (HTTP, Shell, Docker, Serverless)
- [ ] 100% backward compatibility with existing HTTP services
- [ ] Configuration validation prevents invalid setups
- [ ] Error handling covers 95%+ failure scenarios

### Performance Targets
- [ ] Job execution overhead < 100ms
- [ ] Throughput > 1000 jobs/minute
- [ ] Memory usage < 256MB per runner instance
- [ ] Resource utilization < 10% baseline increase

### Security Compliance
- [ ] Zero command injection vulnerabilities
- [ ] Resource limits enforced 100% of the time
- [ ] Audit logging captures all execution attempts
- [ ] Security tests pass with 100% coverage

### Reliability Goals
- [ ] Job success rate > 99.9%
- [ ] Mean time to recovery < 30 seconds
- [ ] Error handling coverage > 95%
- [ ] Monitoring alert accuracy > 99%

---

## 🎯 Risk Assessment & Mitigation

### High Risk: Security Vulnerabilities
**Risk**: Command injection, resource exhaustion, container escapes
**Impact**: Critical - System compromise
**Mitigation**:
- Defense-in-depth approach (allowlists, sandboxing, limits)
- Comprehensive security testing
- External security audit before production
- Monitoring and alerting for suspicious activity

### Medium Risk: Performance Degradation
**Risk**: Runner overhead slows down job processing
**Impact**: Medium - User experience degradation
**Mitigation**:
- Performance profiling during development
- Benchmarking against current HTTP implementation
- Optimization focus in refactor phases
- Caching and connection pooling

### Medium Risk: Docker/Cloud Dependencies
**Risk**: Docker daemon failures, cloud provider outages
**Impact**: Medium - Service disruption
**Mitigation**:
- Graceful fallback to simpler execution types
- Circuit breaker patterns
- Comprehensive health checks
- Multi-region cloud deployments

### Low Risk: Configuration Complexity
**Risk**: Users struggle to configure multiple execution types
**Impact**: Low - Adoption friction
**Mitigation**:
- Extensive documentation and examples
- Configuration validation with helpful errors
- Migration guides for common patterns
- Default configurations for typical use cases

---

## 📅 Timeline Summary

| Phase | Duration | Focus | Dependencies |
|-------|----------|-------|--------------|
| 1. Architecture | 2 weeks | Interfaces & abstractions | None |
| 2. Database | 1 week | Schema extensions | Phase 1 |
| 3. Compiler | 2 weeks | SQL generation | Phase 1, 2 |
| 4. HTTP Runner | 1 week | Reference implementation | Phase 1 |
| 5. Shell Runner | 2 weeks | Shell + security | Phase 1, 4 |
| 6. Docker Runner | 2 weeks | Container execution | Phase 1, 4 |
| 7. Serverless | 2 weeks | Cloud functions | Phase 1, 4 |
| 8. Frontend | 1 week | TS types & hooks | Phase 2, 3 |
| 9. Documentation | 1 week | Guides & examples | All phases |
| 10. Testing & QA | 2 weeks | Comprehensive testing | All phases |

**Total**: 20 weeks (5 months)

---

## 🚀 Rollout Strategy

### Week 20-21: Internal Testing
- Deploy to development environment
- Internal team testing and feedback
- Performance benchmarking
- Security validation

### Week 22-23: Beta Release
- Deploy to staging environment
- Selected customer beta testing (HTTP + Shell only)
- Monitoring and alerting setup
- Support team training

### Week 24-26: Gradual Production Rollout
- Phase 1: HTTP runner (backward compatibility test)
- Phase 2: Shell runner (limited customer set)
- Phase 3: Docker runner (containerized workloads)
- Phase 4: Serverless runner (cloud integrations)

### Week 27+: Post-Launch
- Production monitoring and optimization
- Customer feedback collection
- Documentation refinements
- Roadmap planning for Phase 2 features

---

## 📋 Deliverables Checklist

### Code & Implementation
- [ ] Extended job queue schema (jobs.tb_job_run)
- [ ] 4 execution runner implementations (HTTP, Shell, Docker, Serverless)
- [ ] Runner registry and plugin system
- [ ] Extended CallServiceStepCompiler
- [ ] Security controls (allowlists, resource limits)
- [ ] Observability views (performance, resource usage, failures)
- [ ] Frontend TypeScript types and hooks

### Testing
- [ ] Comprehensive unit test suite (100% coverage)
- [ ] Integration test suite (end-to-end workflows)
- [ ] Security test suite (penetration testing)
- [ ] Performance test suite (load testing, benchmarking)
- [ ] Chaos engineering scenarios (failure injection)

### Documentation
- [ ] Architecture overview document
- [ ] Configuration reference guide (all execution types)
- [ ] Security guidelines and best practices
- [ ] API documentation for custom runner development
- [ ] Troubleshooting and debugging guide
- [ ] Performance tuning guide
- [ ] Migration guide for existing HTTP services

### Examples & Tutorials
- [ ] Shell script execution examples
- [ ] Docker container integration examples
- [ ] Serverless function examples
- [ ] Multi-step processing pipelines
- [ ] Error handling and recovery patterns
- [ ] Performance optimization examples

---

## 🔍 Quality Assurance

### Code Quality Gates
- [ ] 100% unit test coverage for new code
- [ ] Static analysis passing (mypy, ruff)
- [ ] Code review by senior engineers
- [ ] Security audit by security team
- [ ] Performance benchmarks meet targets

### Integration Quality
- [ ] Backward compatibility maintained (all existing tests pass)
- [ ] No performance regressions
- [ ] Load testing completed (1000+ jobs/minute)
- [ ] Observability dashboards functional

### Documentation Quality
- [ ] All public APIs documented
- [ ] Configuration options explained with examples
- [ ] Examples tested and working
- [ ] Troubleshooting guides comprehensive
- [ ] Migration guides clear and complete

---

## 📝 Implementation Notes for Engineer

### Key Design Principles

1. **Security First**: Every runner must implement defense-in-depth:
   - Input validation and sanitization
   - Allowlists for commands/images/functions
   - Resource limits (CPU, memory, disk, network)
   - Audit logging for all execution attempts

2. **Convention Over Configuration**: Follow SpecQL philosophy:
   - Sensible defaults (execution_type defaults to 'http')
   - Minimal user configuration required
   - Framework handles technical complexity

3. **Observability Everywhere**: Every execution must be:
   - Logged with structured metadata
   - Tracked in observability views
   - Monitored for performance and failures
   - Alerted on anomalies

4. **Backward Compatibility**: Zero breaking changes:
   - Existing HTTP services work without modification
   - New columns have defaults
   - Execution type inference for legacy services

5. **Extensibility**: Plugin architecture for future runners:
   - Clean `JobRunner` interface
   - Registry pattern for runner discovery
   - Configuration validation hooks
   - Resource requirement declarations

### Implementation Priorities

1. **Security** (Critical): Never compromise on security
   - Implement defense in depth
   - Test security controls exhaustively
   - Document security implications
   - Get external security audit

2. **Reliability** (High): Jobs must complete successfully or fail cleanly
   - Graceful error handling
   - Resource cleanup (processes, containers)
   - Retry logic with exponential backoff
   - Dead letter queue for unrecoverable failures

3. **Performance** (Medium): Minimize overhead while maintaining functionality
   - Profile and benchmark each runner
   - Optimize hot paths
   - Use connection pooling and caching
   - Horizontal scalability

4. **Maintainability** (Medium): Code should be easy to understand and extend
   - Clear abstractions and interfaces
   - Comprehensive tests
   - Extensive documentation
   - Examples for common patterns

### Development Workflow

1. **Follow TDD Cycle Rigorously**: RED → GREEN → REFACTOR → QA
   - Write failing test first
   - Implement minimal code to pass
   - Refactor for quality
   - Verify with full test suite

2. **Small, Focused Commits**: Each TDD cycle = 1 commit
   - Easier to review
   - Easier to revert
   - Clear progress tracking

3. **Continuous Integration**: Run tests on every commit
   - Unit tests
   - Integration tests
   - Linting and type checking
   - Security scans

4. **Documentation As You Go**: Don't defer documentation
   - Docstrings for all public APIs
   - Architecture decisions recorded
   - Examples created during development

---

## ✅ Final Success Criteria

### Must Have
- [ ] All 4 execution types implemented and tested
- [ ] 100% backward compatibility with existing HTTP services
- [ ] Security controls prevent unauthorized execution
- [ ] Performance meets targets (<100ms overhead, >1000 jobs/min)
- [ ] Comprehensive documentation and examples

### Should Have
- [ ] Execution-type-aware monitoring dashboards
- [ ] Frontend TypeScript types and Apollo hooks
- [ ] Migration guide for existing services
- [ ] Performance optimization guide

### Nice to Have
- [ ] Custom runner plugin examples
- [ ] Multi-region deployment guide
- [ ] Advanced security patterns (sandboxing, network policies)
- [ ] Cost optimization recommendations

---

**End of Phased Implementation Plan**

This plan provides a comprehensive roadmap for extending SpecQL's call_service framework to support multiple execution types. Each phase follows disciplined TDD methodology with clear deliverables, success criteria, and quality gates.

The phased approach ensures:
- ✅ Incremental progress with frequent validation
- ✅ Backward compatibility throughout
- ✅ Security and reliability from day one
- ✅ Clear milestones for stakeholder communication
- ✅ Flexibility to adjust based on learnings

**Next Steps**: Review this plan with the team, adjust timeline based on capacity, and begin Phase 1 implementation.
