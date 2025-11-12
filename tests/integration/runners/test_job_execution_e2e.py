"""End-to-end integration tests for job execution across all runners."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.runners.execution_types import ExecutionType
from src.runners.runner_registry import RunnerRegistry
from src.runners.job_runner import JobRecord, ExecutionContext, JobResult
from src.registry.service_registry import ServiceRegistry, Service, ServiceOperation


@pytest.fixture
def mock_service_registry():
    """Create a mock service registry with all execution types."""
    services = [
        Service(
            name="http_api",
            type="api",
            category="integration",
            operations=[
                ServiceOperation(name="call", input_schema={}, output_schema={})
            ],
            execution_type=ExecutionType.HTTP,
            runner_config={"base_url": "https://api.example.com"},
            security_policy={},
        ),
        Service(
            name="docker_task",
            type="container",
            category="compute",
            operations=[
                ServiceOperation(name="run", input_schema={}, output_schema={})
            ],
            execution_type=ExecutionType.DOCKER,
            runner_config={"allowed_images": ["ubuntu:20.04"]},
            security_policy={"allowed_images": ["ubuntu:20.04"]},
        ),
        Service(
            name="lambda_func",
            type="serverless",
            category="compute",
            operations=[
                ServiceOperation(name="invoke", input_schema={}, output_schema={})
            ],
            execution_type=ExecutionType.SERVERLESS,
            runner_config={"provider": "aws", "region": "us-east-1"},
            security_policy={},
        ),
    ]
    return ServiceRegistry(services=services)


@pytest.fixture
def sample_execution_context():
    """Sample execution context for testing."""
    return ExecutionContext(
        tenant_id="test-tenant-123",
        triggered_by="test-user-456",
        correlation_id="test-corr-789",
        security_context={
            "allowed_images": ["ubuntu:20.04"],
            "allowed_commands": ["/usr/bin/echo"],
        },
    )


class TestHTTPJobExecutionE2E:
    """End-to-end HTTP job execution tests."""

    @pytest.mark.asyncio
    async def test_http_job_timeout_error(
        self, mock_service_registry, sample_execution_context
    ):
        """HTTP job execution handles timeout errors."""
        from src.runners.http_runner import HTTPRunner

        http_runner = HTTPRunner()  # Directly instantiate HTTP runner

        job = JobRecord(
            id="timeout-job",
            service_name="http_api",
            operation="call",
            input_data={
                "endpoint": "https://slow-api.example.com/data",
                "method": "GET",
            },
            timeout_seconds=5,  # Short timeout
            attempts=0,
            max_attempts=3,
        )

        from httpx import TimeoutException

        timeout_error = TimeoutException("Request timeout")

        with patch.object(http_runner.client, "request", side_effect=timeout_error):
            result = await http_runner.execute(job, sample_execution_context)

            assert result.success == False
            assert "HTTP request failed: Request timeout" in result.error_message

    @pytest.mark.asyncio
    async def test_docker_job_container_failure(
        self, mock_service_registry, sample_execution_context
    ):
        """Docker job execution handles container failures."""
        from src.runners.docker_runner import DockerRunner

        # Mock the Docker client before instantiating runner
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            docker_runner = DockerRunner()  # Instantiate with mocked client

            job = JobRecord(
                id="failing-docker-job",
                service_name="docker_task",
                operation="run",
                input_data={
                    "image": "ubuntu:20.04",
                    "command": ["sh", "-c", "exit 1"],  # Command that fails
                },
                timeout_seconds=300,
                attempts=0,
                max_attempts=3,
            )

            mock_container = MagicMock()
            mock_container.logs.return_value = b"Error: something went wrong\n"
            mock_container.wait.return_value = {"StatusCode": 1}  # Non-zero exit code
            mock_client.containers.run.return_value = mock_container

            result = await docker_runner.execute(job, sample_execution_context)

            assert result.success == False
            assert result.output_data["exit_code"] == 1
            assert "Error: something went wrong" in result.output_data["stdout"]


class TestJobExecutionResourceManagementE2E:
    """End-to-end resource management tests."""

    @pytest.mark.asyncio
    async def test_http_job_resource_tracking(
        self, mock_service_registry, sample_execution_context
    ):
        """HTTP jobs track resource usage correctly."""
        from src.runners.http_runner import HTTPRunner

        http_runner = HTTPRunner()  # Directly instantiate HTTP runner

        job = JobRecord(
            id="resource-job",
            service_name="http_api",
            operation="call",
            input_data={
                "endpoint": "https://api.example.com/large-response",
                "method": "GET",
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        # Large response to test size tracking
        large_content = b'{"data": "' + b"x" * 10000 + b'"}'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = large_content
        mock_response.json.return_value = {"data": "x" * 10000}
        mock_response.elapsed.total_seconds.return_value = 2.5
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_execution_context)

            assert result.success == True
            assert result.duration_seconds == 2.5
            assert result.resource_usage["status_code"] == 200
            assert result.resource_usage["response_size_bytes"] == len(large_content)

    @pytest.mark.asyncio
    async def test_runner_resource_requirements_calculation(
        self, mock_service_registry
    ):
        """All runners calculate resource requirements correctly."""
        from src.runners.http_runner import HTTPRunner
        from src.runners.docker_runner import DockerRunner
        from src.runners.serverless_runner import ServerlessRunner

        # Test HTTP runner resource requirements
        http_runner = HTTPRunner()
        http_reqs = http_runner.get_resource_requirements({"timeout": 120})
        assert http_reqs.cpu_cores == 0.1
        assert http_reqs.memory_mb == 128
        assert http_reqs.disk_mb == 0
        assert http_reqs.timeout_seconds == 120

        # Test Docker runner resource requirements
        docker_runner = DockerRunner()
        docker_reqs = docker_runner.get_resource_requirements(
            {"resource_limits": {"memory_mb": 512}}
        )
        assert docker_reqs.memory_mb == 512  # Should use configured limit

        # Test Serverless runner resource requirements
        serverless_runner = ServerlessRunner()
        serverless_reqs = serverless_runner.get_resource_requirements({})
        assert serverless_reqs.cpu_cores == 0.1  # Minimal CPU
        assert serverless_reqs.memory_mb == 64  # Minimal memory


class TestJobExecutionSecurityE2E:
    """End-to-end security validation tests."""

    @pytest.mark.asyncio
    async def test_docker_job_image_allowlist_enforcement(
        self, sample_execution_context
    ):
        """Docker jobs enforce image allowlists."""
        from src.runners.docker_runner import DockerRunner

        runner = DockerRunner()

        job = JobRecord(
            id="blocked-image-job",
            service_name="docker_task",
            operation="run",
            input_data={
                "image": "malicious:latest",  # Not in allowlist
                "command": ["echo", "hacked"],
            },
            timeout_seconds=300,
            attempts=0,
            max_attempts=3,
        )

        context = ExecutionContext(
            tenant_id="tenant-1",
            triggered_by="user-1",
            correlation_id="corr-1",
            security_context={
                "allowed_images": [
                    "ubuntu:20.04",
                    "python:3.11",
                ]  # malicious not allowed
            },
        )

        result = await runner.execute(job, context)

        assert result.success == False
        assert "not allowed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_http_job_config_validation(self, sample_execution_context):
        """HTTP jobs validate configuration."""
        from src.runners.http_runner import HTTPRunner

        runner = HTTPRunner()

        # Test missing base_url
        try:
            await runner.validate_config({})
            assert False, "Should have raised ValueError for missing base_url"
        except ValueError as e:
            assert "base_url" in str(e)

        # Test invalid base_url
        try:
            await runner.validate_config({"base_url": "ftp://invalid"})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid base_url" in str(e)

        # Test valid config
        result = await runner.validate_config({"base_url": "https://api.example.com"})
        assert result == True


class TestMultiRunnerWorkflowE2E:
    """Multi-runner workflow integration tests."""

    @pytest.mark.asyncio
    async def test_multiple_runners_in_sequence(
        self, mock_service_registry, sample_execution_context
    ):
        """Execute jobs with different runners in sequence."""
        registry = RunnerRegistry.get_instance()

        # HTTP job
        http_job = JobRecord(
            id="http-seq-1",
            service_name="http_api",
            operation="call",
            input_data={
                "endpoint": "https://api.example.com/init",
                "method": "POST",
                "payload": {"action": "init"},
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        # Docker job that depends on HTTP result
        docker_job = JobRecord(
            id="docker-seq-2",
            service_name="docker_task",
            operation="run",
            input_data={
                "image": "ubuntu:20.04",
                "command": ["echo", "Processing initialized data"],
            },
            timeout_seconds=300,
            attempts=0,
            max_attempts=3,
        )

        # Execute HTTP job
        from src.runners.http_runner import HTTPRunner
        http_runner = HTTPRunner()  # Directly instantiate HTTP runner
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.content = b'{"status": "initialized"}'
        mock_http_response.json.return_value = {"status": "initialized"}
        mock_http_response.elapsed.total_seconds.return_value = 1.0
        mock_http_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_http_response
            http_result = await http_runner.execute(http_job, sample_execution_context)
            assert http_result.success == True

        # Execute Docker job
        from src.runners.docker_runner import DockerRunner

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            docker_runner = DockerRunner()  # Instantiate with mocked client

            mock_container = MagicMock()
            mock_container.logs.return_value = b"Processing initialized data\n"
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_client.containers.run.return_value = mock_container

            docker_result = await docker_runner.execute(
                docker_job, sample_execution_context
            )
            assert docker_result.success == True

        # Both jobs succeeded
        assert http_result.success and docker_result.success
