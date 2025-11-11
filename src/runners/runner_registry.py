"""Runner registry for execution type management."""

from src.runners.execution_types import ExecutionType
from src.runners.job_runner import JobRunner


class RunnerRegistry:
    """
    Registry for job execution runners.

    Maps execution types to their corresponding runner implementations.
    Uses singleton pattern for global access.
    """

    _instance = None

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._runners: dict[ExecutionType, type[JobRunner]] = {}

    @classmethod
    def get_instance(cls) -> "RunnerRegistry":
        """Get singleton instance of runner registry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, execution_type: ExecutionType, runner_class: type[JobRunner]) -> None:
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

    def get_runner(self, execution_type: ExecutionType) -> type[JobRunner]:
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
