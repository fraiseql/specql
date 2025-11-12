"""Tests for DockerRunner."""

import pytest
from unittest.mock import MagicMock, patch

from src.runners.docker_runner import DockerRunner
from src.runners.job_runner import JobRecord, ExecutionContext


@pytest.mark.asyncio
async def test_docker_runner_executes_container():
    """DockerRunner executes Docker containers"""
    # Mock Docker client before creating runner
    with patch("docker.from_env") as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Mock container
        mock_container = MagicMock()
        mock_container.logs.return_value = b"Hello World\n"
        mock_container.wait.return_value = {"StatusCode": 0}

        mock_client.containers.run.return_value = mock_container

        runner = DockerRunner()

        job = JobRecord(
            id="test-job-docker-1",
            service_name="docker_processor",
            operation="run",
            input_data={
                "image": "python:3.11",
                "command": ["python", "-c", "print('Hello World')"],
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        context = ExecutionContext(
            tenant_id="tenant-1",
            triggered_by="user-1",
            correlation_id="corr-1",
            security_context={"allowed_images": ["python:3.11"]},
        )

        result = await runner.execute(job, context)

        assert result.success == True
        assert "Hello World" in result.output_data["stdout"]
        assert result.output_data["exit_code"] == 0


@pytest.mark.asyncio
async def test_docker_runner_blocks_disallowed_images():
    """DockerRunner blocks images not in allowlist"""
    runner = DockerRunner()

    job = JobRecord(
        id="test-job-docker-2",
        service_name="malicious",
        operation="run",
        input_data={"image": "malicious:latest", "command": ["echo", "hacked"]},
        timeout_seconds=30,
        attempts=0,
        max_attempts=3,
    )

    context = ExecutionContext(
        tenant_id="tenant-1",
        triggered_by="user-1",
        correlation_id="corr-1",
        security_context={
            "allowed_images": ["python:3.11"]  # malicious not allowed
        },
    )

    result = await runner.execute(job, context)

    assert result.success == False
    assert "not allowed" in result.error_message.lower()


@pytest.mark.asyncio
async def test_docker_runner_validates_config():
    """DockerRunner validates runner configuration"""
    runner = DockerRunner()

    # Valid config
    valid_config = {"allowed_images": ["python:3.11", "ubuntu:20.04"], "default_timeout": 300}

    assert await runner.validate_config(valid_config) == True

    # Invalid config
    invalid_config = {"default_timeout": 300}

    with pytest.raises(ValueError, match="allowed_images"):
        await runner.validate_config(invalid_config)


@pytest.mark.asyncio
async def test_docker_runner_secure_volume_mounting():
    """DockerRunner securely mounts volumes with path validation"""
    with patch("docker.from_env") as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_container.logs.return_value = b"processed\n"
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_client.containers.run.return_value = mock_container

        runner = DockerRunner()

        job = JobRecord(
            id="test-job-volumes",
            service_name="volume_processor",
            operation="process",
            input_data={
                "image": "ubuntu:20.04",
                "command": ["cat", "/data/input.txt"],
                "volumes": {"/tmp/safe_input.txt": {"bind": "/data/input.txt", "mode": "ro"}},
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        context = ExecutionContext(
            tenant_id="tenant-1",
            triggered_by="user-1",
            correlation_id="corr-1",
            security_context={"allowed_images": ["ubuntu:20.04"], "allowed_mounts": ["/tmp"]},
        )

        result = await runner.execute(job, context)

        assert result.success == True
        # Verify that containers.run was called with volumes
        mock_client.containers.run.assert_called_once()
        call_args = mock_client.containers.run.call_args
        assert "volumes" in call_args.kwargs
        assert call_args.kwargs["volumes"] == {
            "/tmp/safe_input.txt": {"bind": "/data/input.txt", "mode": "ro"}
        }


@pytest.mark.asyncio
async def test_docker_runner_blocks_unsafe_volume_mounts():
    """DockerRunner blocks volume mounts to disallowed paths"""
    runner = DockerRunner()

    job = JobRecord(
        id="test-job-unsafe",
        service_name="unsafe_processor",
        operation="hack",
        input_data={
            "image": "ubuntu:20.04",
            "command": ["rm", "-rf", "/"],
            "volumes": {
                "/etc/passwd": {"bind": "/data/passwd", "mode": "rw"}  # Dangerous!
            },
        },
        timeout_seconds=30,
        attempts=0,
        max_attempts=3,
    )

    context = ExecutionContext(
        tenant_id="tenant-1",
        triggered_by="user-1",
        correlation_id="corr-1",
        security_context={
            "allowed_images": ["ubuntu:20.04"],
            "allowed_mounts": ["/tmp", "/data"],  # /etc not allowed
        },
    )

    result = await runner.execute(job, context)

    assert result.success == False
    assert "not allowed" in result.error_message.lower()


@pytest.mark.asyncio
async def test_docker_runner_enforces_resource_limits():
    """DockerRunner enforces CPU and memory limits"""
    with patch("docker.from_env") as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_container.logs.return_value = b"completed\n"
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_client.containers.run.return_value = mock_container

        runner = DockerRunner()

        job = JobRecord(
            id="test-job-limits",
            service_name="resource_limited",
            operation="process",
            input_data={"image": "python:3.11", "command": ["python", "-c", "print('done')"]},
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        context = ExecutionContext(
            tenant_id="tenant-1",
            triggered_by="user-1",
            correlation_id="corr-1",
            security_context={
                "allowed_images": ["python:3.11"],
                "resource_limits": {
                    "cpu_quota": 50000,  # 50% of CPU
                    "cpu_period": 100000,
                    "memory": "128m",  # 128MB
                    "disk_quota": "1G",  # 1GB disk
                },
            },
        )

        result = await runner.execute(job, context)

        assert result.success == True
        # Verify resource limits were applied
        mock_client.containers.run.assert_called_once()
        call_args = mock_client.containers.run.call_args
        assert "cpu_quota" in call_args.kwargs
        assert call_args.kwargs["cpu_quota"] == 50000
        assert call_args.kwargs["mem_limit"] == "128m"


@pytest.mark.asyncio
async def test_docker_runner_container_cleanup_on_failure():
    """DockerRunner cleans up containers even when execution fails"""
    with patch("docker.from_env") as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_container.logs.return_value = b"error occurred\n"
        mock_container.wait.return_value = {"StatusCode": 1}  # Non-zero exit code
        mock_client.containers.run.return_value = mock_container

        runner = DockerRunner()

        job = JobRecord(
            id="test-job-fail",
            service_name="failing_service",
            operation="fail",
            input_data={"image": "ubuntu:20.04", "command": ["sh", "-c", "exit 1"]},
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        context = ExecutionContext(
            tenant_id="tenant-1",
            triggered_by="user-1",
            correlation_id="corr-1",
            security_context={"allowed_images": ["ubuntu:20.04"]},
        )

        result = await runner.execute(job, context)

        assert result.success == False
        assert result.output_data["exit_code"] == 1
        # Container should still be cleaned up (remove=True)
        call_args = mock_client.containers.run.call_args
        assert call_args.kwargs["remove"] == True


@pytest.mark.asyncio
async def test_docker_runner_cancel_stops_container():
    """DockerRunner cancel method stops running containers"""
    with patch("docker.from_env") as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        runner = DockerRunner()

        # Test cancel
        result = await runner.cancel("container-123")

        assert result == True
        mock_client.containers.get.assert_called_with("container-123")
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()


@pytest.mark.asyncio
async def test_docker_runner_network_isolation():
    """DockerRunner supports network isolation modes"""
    with patch("docker.from_env") as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_container.logs.return_value = b"isolated task\n"
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_client.containers.run.return_value = mock_container

        runner = DockerRunner()

        job = JobRecord(
            id="test-job-isolated",
            service_name="isolated_service",
            operation="run",
            input_data={
                "image": "alpine:latest",
                "command": ["echo", "isolated task"],
                "network_mode": "none",  # No network access
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        context = ExecutionContext(
            tenant_id="tenant-1",
            triggered_by="user-1",
            correlation_id="corr-1",
            security_context={
                "allowed_images": ["alpine:latest"],
                "network_mode": "none",  # Enforce no network
            },
        )

        result = await runner.execute(job, context)

        assert result.success == True
        # Verify network isolation was applied
        call_args = mock_client.containers.run.call_args
        assert call_args.kwargs["network_mode"] == "none"


def test_docker_runner_is_registered():
    """DockerRunner is registered in the runner registry"""
    from src.runners.runner_registry import RunnerRegistry
    from src.runners.execution_types import ExecutionType

    registry = RunnerRegistry.get_instance()

    # Docker runner should be registered
    assert registry.has_runner(ExecutionType.DOCKER)

    runner_class = registry.get_runner(ExecutionType.DOCKER)
    assert runner_class.__name__ == "DockerRunner"
