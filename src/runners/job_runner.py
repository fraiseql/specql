"""Abstract job runner interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ResourceRequirements:
    """Resource requirements for job execution."""

    cpu_cores: float = 1.0  # CPU cores (fractional allowed)
    memory_mb: int = 512  # Memory in MB
    disk_mb: int = 1024  # Disk space in MB
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
