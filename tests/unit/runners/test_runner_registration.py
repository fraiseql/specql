"""Tests for runner registration and registry functionality."""

import pytest
from src.runners.execution_types import ExecutionType
from src.runners.runner_registry import RunnerRegistry
from src.runners.job_runner import JobRunner


def test_runner_registry_singleton_pattern():
    """Runner registry uses singleton pattern"""
    registry1 = RunnerRegistry.get_instance()
    registry2 = RunnerRegistry.get_instance()

    assert registry1 is registry2
    assert isinstance(registry1, RunnerRegistry)


def test_runner_registry_initially_empty():
    """Runner registry starts empty (before auto-registration)"""
    # Create a fresh instance to test initial state
    registry = RunnerRegistry()  # Not using singleton

    assert len(registry._runners) == 0
    for exec_type in ExecutionType:
        assert not registry.has_runner(exec_type)


def test_runner_registry_register_and_retrieve():
    """Runner registry can register and retrieve runners"""
    registry = RunnerRegistry()  # Fresh instance

    # Mock runner class
    class MockRunner(JobRunner):
        async def validate_config(self, config):
            return True

        async def execute(self, job, context):
            return None

        async def cancel(self, job_id):
            return True

        def get_resource_requirements(self, config):
            return None

    # Register runner
    registry.register(ExecutionType.HTTP, MockRunner)

    # Verify registration
    assert registry.has_runner(ExecutionType.HTTP)
    assert registry.get_runner(ExecutionType.HTTP) == MockRunner

    # Other types should not be registered
    assert not registry.has_runner(ExecutionType.SHELL)


def test_runner_registry_get_unregistered_runner_raises_error():
    """Registry raises error for unregistered execution type"""
    registry = RunnerRegistry()  # Fresh instance

    with pytest.raises(ValueError, match="No runner registered for execution type"):
        registry.get_runner(ExecutionType.DOCKER)


def test_runner_registry_error_message_includes_display_name():
    """Error message includes execution type display name"""
    registry = RunnerRegistry()  # Fresh instance

    with pytest.raises(ValueError) as exc_info:
        registry.get_runner(ExecutionType.SERVERLESS)

    error_msg = str(exc_info.value)
    assert "Serverless Function" in error_msg


def test_runner_registry_overwrite_registration():
    """Registry allows overwriting existing registrations"""
    registry = RunnerRegistry()  # Fresh instance

    class MockRunner1(JobRunner):
        async def validate_config(self, config):
            return True

        async def execute(self, job, context):
            return None

        async def cancel(self, job_id):
            return True

        def get_resource_requirements(self, config):
            return None

    class MockRunner2(JobRunner):
        async def validate_config(self, config):
            return True

        async def execute(self, job, context):
            return None

        async def cancel(self, job_id):
            return True

        def get_resource_requirements(self, config):
            return None

    # Register first runner
    registry.register(ExecutionType.HTTP, MockRunner1)
    assert registry.get_runner(ExecutionType.HTTP) == MockRunner1

    # Overwrite with second runner
    registry.register(ExecutionType.HTTP, MockRunner2)
    assert registry.get_runner(ExecutionType.HTTP) == MockRunner2


def test_runner_registry_multiple_registrations():
    """Registry can handle multiple different registrations"""
    registry = RunnerRegistry()  # Fresh instance

    class HTTPRunner(JobRunner):
        async def validate_config(self, config):
            return True

        async def execute(self, job, context):
            return None

        async def cancel(self, job_id):
            return True

        def get_resource_requirements(self, config):
            return None

    class ShellRunner(JobRunner):
        async def validate_config(self, config):
            return True

        async def execute(self, job, context):
            return None

        async def cancel(self, job_id):
            return True

        def get_resource_requirements(self, config):
            return None

    # Register multiple runners
    registry.register(ExecutionType.HTTP, HTTPRunner)
    registry.register(ExecutionType.SHELL, ShellRunner)

    # Verify both are registered
    assert registry.has_runner(ExecutionType.HTTP)
    assert registry.has_runner(ExecutionType.SHELL)
    assert registry.get_runner(ExecutionType.HTTP) == HTTPRunner
    assert registry.get_runner(ExecutionType.SHELL) == ShellRunner

    # Others still not registered
    assert not registry.has_runner(ExecutionType.DOCKER)
    assert not registry.has_runner(ExecutionType.SERVERLESS)


def test_runner_registry_auto_registered_runners():
    """Auto-registered runners are available via singleton"""
    registry = RunnerRegistry.get_instance()  # Uses singleton with auto-registration

    # Currently registered execution types (from __init__.py)
    registered_types = [
        ExecutionType.HTTP,
        ExecutionType.DOCKER,
        ExecutionType.SERVERLESS,
    ]

    for exec_type in registered_types:
        assert registry.has_runner(exec_type), f"No runner for {exec_type.display_name}"

        runner_class = registry.get_runner(exec_type)
        assert runner_class is not None
        assert issubclass(runner_class, JobRunner)


def test_runner_registry_registered_runners_are_concrete_classes():
    """Registered runners are concrete classes (not abstract)"""
    registry = RunnerRegistry.get_instance()

    # Only check registered types
    registered_types = [
        ExecutionType.HTTP,
        ExecutionType.DOCKER,
        ExecutionType.SERVERLESS,
    ]

    for exec_type in registered_types:
        runner_class = registry.get_runner(exec_type)

        # Should be concrete classes (not abstract)
        assert runner_class != JobRunner
        assert issubclass(runner_class, JobRunner)


def test_runner_registry_has_runner_for_registered_types():
    """Registry has runners for currently registered execution types"""
    registry = RunnerRegistry.get_instance()

    # Currently registered types
    registered_types = [
        ExecutionType.HTTP,
        ExecutionType.DOCKER,
        ExecutionType.SERVERLESS,
    ]

    for exec_type in registered_types:
        assert registry.has_runner(exec_type)

    # SHELL is not currently registered
    assert not registry.has_runner(ExecutionType.SHELL)


def test_runner_registry_thread_safety():
    """Runner registry singleton is thread-safe"""
    import threading
    import time

    results = []

    def get_instance_worker():
        # Small delay to increase chance of race condition
        time.sleep(0.001)
        instance = RunnerRegistry.get_instance()
        results.append(instance)

    # Start multiple threads
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=get_instance_worker)
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # All should be the same instance
    first_instance = results[0]
    for instance in results[1:]:
        assert instance is first_instance


def test_runner_registry_string_representation():
    """Runner registry has reasonable string representation"""
    registry = RunnerRegistry()
    str_repr = str(registry)

    assert "RunnerRegistry" in str_repr

    # Should show object info
    assert "object at" in str_repr
