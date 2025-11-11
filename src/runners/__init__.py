"""Job execution runner framework for SpecQL."""

# Auto-register runners on module import
from src.runners.docker_runner import DockerRunner
from src.runners.execution_types import ExecutionType
from src.runners.http_runner import HTTPRunner
from src.runners.runner_registry import RunnerRegistry
from src.runners.serverless_runner import ServerlessRunner

# Register runners
_registry = RunnerRegistry.get_instance()
_registry.register(ExecutionType.HTTP, HTTPRunner)
_registry.register(ExecutionType.DOCKER, DockerRunner)
_registry.register(ExecutionType.SERVERLESS, ServerlessRunner)

__all__ = ["RunnerRegistry", "ExecutionType", "HTTPRunner", "DockerRunner", "ServerlessRunner"]
