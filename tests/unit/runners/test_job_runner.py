"""Tests for job runner interface and data classes."""

import pytest
from src.runners.job_runner import (
    JobRunner,
    ResourceRequirements,
    JobRecord,
    JobResult,
    ExecutionContext,
)


def test_resource_requirements_dataclass():
    """ResourceRequirements dataclass works correctly"""
    reqs = ResourceRequirements(
        cpu_cores=2.5, memory_mb=1024, disk_mb=2048, timeout_seconds=600
    )

    assert reqs.cpu_cores == 2.5
    assert reqs.memory_mb == 1024
    assert reqs.disk_mb == 2048
    assert reqs.timeout_seconds == 600


def test_resource_requirements_defaults():
    """ResourceRequirements has sensible defaults"""
    reqs = ResourceRequirements()

    assert reqs.cpu_cores == 1.0
    assert reqs.memory_mb == 512
    assert reqs.disk_mb == 1024
    assert reqs.timeout_seconds == 300


def test_job_record_dataclass():
    """JobRecord dataclass works correctly"""
    job = JobRecord(
        id="job-123",
        service_name="test-service",
        operation="test-op",
        input_data={"key": "value"},
        timeout_seconds=30,
        attempts=1,
        max_attempts=3,
    )

    assert job.id == "job-123"
    assert job.service_name == "test-service"
    assert job.operation == "test-op"
    assert job.input_data == {"key": "value"}
    assert job.timeout_seconds == 30
    assert job.attempts == 1
    assert job.max_attempts == 3


def test_job_result_success():
    """JobResult for successful execution"""
    result = JobResult(
        success=True,
        output_data={"result": "success"},
        duration_seconds=1.5,
        resource_usage={"cpu": 0.1, "memory": 50},
    )

    assert result.success  is True
    assert result.output_data == {"result": "success"}
    assert result.error_message is None
    assert result.duration_seconds == 1.5
    assert result.resource_usage == {"cpu": 0.1, "memory": 50}


def test_job_result_failure():
    """JobResult for failed execution"""
    result = JobResult(
        success=False,
        error_message="Command failed",
        duration_seconds=2.0,
        resource_usage={"cpu": 0.2, "memory": 75},
    )

    assert not result.success
    assert result.output_data is None
    assert result.error_message == "Command failed"
    assert result.duration_seconds == 2.0
    assert result.resource_usage == {"cpu": 0.2, "memory": 75}


def test_job_result_minimal():
    """JobResult with minimal fields"""
    result = JobResult(success=True)

    assert result.success  is True
    assert result.output_data is None
    assert result.error_message is None
    assert result.duration_seconds is None
    assert result.resource_usage is None


def test_execution_context_dataclass():
    """ExecutionContext dataclass works correctly"""
    context = ExecutionContext(
        tenant_id="tenant-123",
        triggered_by="user-456",
        correlation_id="corr-789",
        security_context={"allowed_commands": ["/bin/ls"]},
    )

    assert context.tenant_id == "tenant-123"
    assert context.triggered_by == "user-456"
    assert context.correlation_id == "corr-789"
    assert context.security_context == {"allowed_commands": ["/bin/ls"]}


def test_execution_context_minimal():
    """ExecutionContext with minimal fields"""
    context = ExecutionContext(tenant_id=None, triggered_by=None, correlation_id=None)

    assert context.tenant_id is None
    assert context.triggered_by is None
    assert context.correlation_id is None
    assert context.security_context is None


def test_job_runner_is_abstract():
    """JobRunner is an abstract base class"""
    # Cannot instantiate directly
    with pytest.raises(TypeError):
        JobRunner()


def test_job_runner_requires_abstract_methods():
    """Concrete runners must implement all abstract methods"""

    class IncompleteRunner(JobRunner):
        pass

    # Missing abstract methods
    with pytest.raises(TypeError):
        IncompleteRunner()


def test_job_runner_has_required_methods():
    """JobRunner interface defines required methods"""
    # Check method signatures exist
    assert hasattr(JobRunner, "validate_config")
    assert hasattr(JobRunner, "execute")
    assert hasattr(JobRunner, "cancel")
    assert hasattr(JobRunner, "get_resource_requirements")

    # Check they are callable
    assert callable(JobRunner.validate_config)
    assert callable(JobRunner.execute)
    assert callable(JobRunner.cancel)
    assert callable(JobRunner.get_resource_requirements)


def test_job_runner_abstract_method_signatures():
    """Abstract methods have correct signatures"""
    import inspect

    # validate_config
    sig = inspect.signature(JobRunner.validate_config)
    assert len(sig.parameters) == 2  # self, config
    assert "config" in sig.parameters

    # execute
    sig = inspect.signature(JobRunner.execute)
    assert len(sig.parameters) == 3  # self, job, context
    assert "job" in sig.parameters
    assert "context" in sig.parameters

    # cancel
    sig = inspect.signature(JobRunner.cancel)
    assert len(sig.parameters) == 2  # self, job_id
    assert "job_id" in sig.parameters

    # get_resource_requirements
    sig = inspect.signature(JobRunner.get_resource_requirements)
    assert len(sig.parameters) == 2  # self, config
    assert "config" in sig.parameters


def test_dataclasses_are_mutable():
    """Data classes are currently mutable (not frozen)"""
    # Test ResourceRequirements
    reqs = ResourceRequirements()
    reqs.cpu_cores = 2.0  # Should work
    assert reqs.cpu_cores == 2.0

    # Test JobRecord
    job = JobRecord(
        id="test",
        service_name="test",
        operation="test",
        input_data={},
        timeout_seconds=30,
        attempts=0,
        max_attempts=1,
    )
    job.id = "modified"  # Should work
    assert job.id == "modified"

    # Test JobResult
    result = JobResult(success=True)
    result.success = False  # Should work
    assert not result.success

    # Test ExecutionContext
    context = ExecutionContext(tenant_id=None, triggered_by=None, correlation_id=None)
    context.tenant_id = "modified"  # Should work
    assert context.tenant_id == "modified"


def test_dataclass_string_representations():
    """Data classes have reasonable string representations"""
    reqs = ResourceRequirements(cpu_cores=1.5, memory_mb=256)
    str_repr = str(reqs)
    assert "ResourceRequirements" in str_repr
    assert "cpu_cores=1.5" in str_repr
    assert "memory_mb=256" in str_repr

    job = JobRecord(
        id="job-1",
        service_name="svc",
        operation="op",
        input_data={"k": "v"},
        timeout_seconds=60,
        attempts=1,
        max_attempts=3,
    )
    str_repr = str(job)
    assert "JobRecord" in str_repr
    assert "job-1" in str_repr
    assert "svc" in str_repr


def test_dataclass_equality():
    """Data classes support equality comparison"""
    reqs1 = ResourceRequirements(cpu_cores=1.0, memory_mb=512)
    reqs2 = ResourceRequirements(cpu_cores=1.0, memory_mb=512)
    reqs3 = ResourceRequirements(cpu_cores=2.0, memory_mb=512)

    assert reqs1 == reqs2
    assert reqs1 != reqs3

    job1 = JobRecord(
        id="j1",
        service_name="s",
        operation="o",
        input_data={"a": 1},
        timeout_seconds=30,
        attempts=0,
        max_attempts=1,
    )
    job2 = JobRecord(
        id="j1",
        service_name="s",
        operation="o",
        input_data={"a": 1},
        timeout_seconds=30,
        attempts=0,
        max_attempts=1,
    )
    job3 = JobRecord(
        id="j2",
        service_name="s",
        operation="o",
        input_data={"a": 1},
        timeout_seconds=30,
        attempts=0,
        max_attempts=1,
    )

    assert job1 == job2
    assert job1 != job3


def test_dataclass_hashability():
    """Data classes are not hashable (since they're not frozen)"""
    reqs = ResourceRequirements()
    job = JobRecord(
        id="test",
        service_name="test",
        operation="test",
        input_data={},
        timeout_seconds=30,
        attempts=0,
        max_attempts=1,
    )
    result = JobResult(success=True)
    context = ExecutionContext(tenant_id=None, triggered_by=None, correlation_id=None)

    # Should not be hashable
    with pytest.raises(TypeError):
        hash(reqs)

    with pytest.raises(TypeError):
        hash(job)

    with pytest.raises(TypeError):
        hash(result)

    with pytest.raises(TypeError):
        hash(context)


def test_job_result_different_constructors():
    """JobResult can be constructed in different ways"""
    # Success with data
    success_result = JobResult(
        success=True, output_data={"result": "ok"}, duration_seconds=1.0
    )
    assert success_result.success  is True
    assert success_result.output_data == {"result": "ok"}
    assert success_result.error_message is None

    # Failure with error
    failure_result = JobResult(
        success=False, error_message="Failed", duration_seconds=2.0
    )
    assert not failure_result.success
    assert failure_result.output_data is None
    assert failure_result.error_message == "Failed"

    # Partial result
    partial_result = JobResult(success=True, resource_usage={"cpu": 0.5})
    assert partial_result.success  is True
    assert partial_result.output_data is None
    assert partial_result.error_message is None
    assert partial_result.resource_usage == {"cpu": 0.5}
