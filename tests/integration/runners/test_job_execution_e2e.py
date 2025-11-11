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
    async def test_http_job_execution_success(
        self, mock_service_registry, sample_execution_context
    ):
        """Execute HTTP job end-to-end with successful response."""
        registry = RunnerRegistry.get_instance()
        http_runner = registry.get_runner(ExecutionType.HTTP)

        job = JobRecord(
            id="http-job-1",
            service_name="http_api",
            operation="call",
            input_data={"endpoint": "https://api.example.com/data", "method": "GET"},
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success", "data": [1, 2, 3]}'
        mock_response.json.return_value = {"result": "success", "data": [1, 2, 3]}
        mock_response.elapsed.total_seconds.return_value = 1.2
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request = AsyncMock(return_value=mock_response)

            # Create a fresh runner instance to use the mocked client
            from src.runners.http_runner import HTTPRunner

            runner = HTTPRunner()
            result = await runner.execute(job, sample_execution_context)

            assert result.success == True
            assert result.output_data == {"result": "success", "data": [1, 2, 3]}
            assert result.duration_seconds == 1.2
            assert result.resource_usage["status_code"] == 200
            assert result.resource_usage["response_size_bytes"] == 44  # len of content

    @pytest.mark.asyncio
    async def test_http_job_execution_with_post_payload(
        self, mock_service_registry, sample_execution_context
    ):
        """Execute HTTP job with POST payload."""
        registry = RunnerRegistry.get_instance()
        http_runner = registry.get_runner(ExecutionType.HTTP)

        job = JobRecord(
            id="http-post-job",
            service_name="http_api",
            operation="call",
            input_data={
                "endpoint": "https://api.example.com/webhook",
                "method": "POST",
                "payload": {"event": "order_created", "order_id": "12345"},
                "headers": {"Content-Type": "application/json"},
            },
            timeout_seconds=60,
            attempts=0,
            max_attempts=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = b'{"webhook_id": "wh_123", "status": "received"}'
        mock_response.json.return_value = {"webhook_id": "wh_123", "status": "received"}
        mock_response.elapsed.total_seconds.return_value = 0.8
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_execution_context)

            assert result.success == True
            assert result.output_data["webhook_id"] == "wh_123"

            # Verify POST request was made with payload
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.kwargs["method"] == "POST"
            assert call_args.kwargs["json"] == {
                "event": "order_created",
                "order_id": "12345",
            }
            assert call_args.kwargs["headers"] == {"Content-Type": "application/json"}

    @pytest.mark.asyncio
    async def test_http_job_execution_failure_404(
        self, mock_service_registry, sample_execution_context
    ):
        """Execute HTTP job that fails with 404."""
        registry = RunnerRegistry.get_instance()
        http_runner = registry.get_runner(ExecutionType.HTTP)

        job = JobRecord(
            id="http-404-job",
            service_name="http_api",
            operation="call",
            input_data={"endpoint": "https://api.example.com/missing", "method": "GET"},
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        from httpx import HTTPStatusError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        http_error = HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )

        with patch.object(http_runner.client, "request", side_effect=http_error):
            result = await http_runner.execute(job, sample_execution_context)

            assert result.success == False
            assert "HTTP 404: Not Found" in result.error_message


class TestDockerJobExecutionE2E:
    """End-to-end Docker job execution tests."""

    @pytest.mark.asyncio
    async def test_docker_job_execution_success(
        self, mock_service_registry, sample_execution_context
    ):
        """Execute Docker job end-to-end with successful container run."""
        registry = RunnerRegistry.get_instance()
        docker_runner = registry.get_runner(ExecutionType.DOCKER)

        job = JobRecord(
            id="docker-job-1",
            service_name="docker_task",
            operation="run",
            input_data={
                "image": "ubuntu:20.04",
                "command": ["echo", "Hello", "World"],
            },
            timeout_seconds=300,
            attempts=0,
            max_attempts=3,
        )

        # Mock Docker container execution
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            mock_container = MagicMock()
            mock_container.logs.return_value = b"Hello World\n"
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_client.containers.run.return_value = mock_container

            result = await docker_runner.execute(job, sample_execution_context)

            assert result.success == True
            assert result.output_data["stdout"] == "Hello World\n"
            assert result.output_data["exit_code"] == 0

            # Verify container was run with correct parameters
            mock_client.containers.run.assert_called_once()
            call_args = mock_client.containers.run.call_args
            assert call_args.kwargs["image"] == "ubuntu:20.04"
            assert call_args.kwargs["command"] == ["echo", "Hello", "World"]
            assert call_args.kwargs["remove"] == True  # Cleanup

    @pytest.mark.asyncio
    async def test_docker_job_execution_with_volume_mounts(
        self, mock_service_registry, sample_execution_context
    ):
        """Execute Docker job with volume mounts."""
        registry = RunnerRegistry.get_instance()
        docker_runner = registry.get_runner(ExecutionType.DOCKER)

        job = JobRecord(
            id="docker-volume-job",
            service_name="docker_task",
            operation="run",
            input_data={
                "image": "ubuntu:20.04",
                "command": ["cat", "/data/input.txt"],
                "volumes": {
                    "/tmp/input.txt": {"bind": "/data/input.txt", "mode": "ro"}
                },
            },
            timeout_seconds=300,
            attempts=0,
            max_attempts=3,
        )

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            mock_container = MagicMock()
            mock_container.logs.return_value = b"file contents\n"
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_client.containers.run.return_value = mock_container

            result = await docker_runner.execute(job, sample_execution_context)

            assert result.success == True
            assert result.output_data["stdout"] == "file contents\n"

            # Verify volumes were mounted
            call_args = mock_client.containers.run.call_args
            assert call_args.kwargs["volumes"] == {
                "/tmp/input.txt": {"bind": "/data/input.txt", "mode": "ro"}
            }


class TestServerlessJobExecutionE2E:
    """End-to-end serverless job execution tests."""

    @pytest.mark.asyncio
    async def test_serverless_job_execution_aws_lambda(
        self, mock_service_registry, sample_execution_context
    ):
        """Execute AWS Lambda job end-to-end."""
        registry = RunnerRegistry.get_instance()
        serverless_runner = registry.get_runner(ExecutionType.SERVERLESS)

        job = JobRecord(
            id="lambda-job-1",
            service_name="lambda_func",
            operation="invoke",
            input_data={
                "function_name": "my-lambda-function",
                "payload": {"action": "process", "data": "test"},
                "provider": "aws",
            },
            timeout_seconds=900,
            attempts=0,
            max_attempts=3,
        )

        expected_result = JobResult(
            success=True,
            output_data={"payload": {"result": "processed", "status": "success"}},
            resource_usage={"provider": "aws"},
        )

        with patch.object(
            serverless_runner, "_invoke_lambda", return_value=expected_result
        ) as mock_invoke:
            result = await serverless_runner.execute(job, sample_execution_context)

            assert result.success == True
            assert result.output_data["payload"]["result"] == "processed"
            mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_serverless_job_execution_gcp_function(
        self, mock_service_registry, sample_execution_context
    ):
        """Execute Google Cloud Function job end-to-end."""
        registry = RunnerRegistry.get_instance()
        serverless_runner = registry.get_runner(ExecutionType.SERVERLESS)

        job = JobRecord(
            id="gcp-job-1",
            service_name="lambda_func",  # Same service, different provider
            operation="invoke",
            input_data={
                "function_name": "my-gcp-function",
                "payload": {"action": "transform", "input": "data"},
                "provider": "gcp",
            },
            timeout_seconds=900,
            attempts=0,
            max_attempts=3,
        )

        expected_result = JobResult(
            success=True,
            output_data={"result": {"output": "transformed", "success": True}},
            resource_usage={"provider": "gcp"},
        )

        with patch.object(
            serverless_runner, "_invoke_gcp_function", return_value=expected_result
        ) as mock_invoke:
            result = await serverless_runner.execute(job, sample_execution_context)

            assert result.success == True
            assert result.output_data["result"]["output"] == "transformed"
            mock_invoke.assert_called_once()


class TestJobExecutionErrorHandlingE2E:
    """End-to-end error handling across all runners."""

    @pytest.mark.asyncio
    async def test_http_job_timeout_error(
        self, mock_service_registry, sample_execution_context
    ):
        """HTTP job execution handles timeout errors."""
        registry = RunnerRegistry.get_instance()
        http_runner = registry.get_runner(ExecutionType.HTTP)

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
        registry = RunnerRegistry.get_instance()
        docker_runner = registry.get_runner(ExecutionType.DOCKER)

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

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

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
        registry = RunnerRegistry.get_instance()
        http_runner = registry.get_runner(ExecutionType.HTTP)

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
        registry = RunnerRegistry.get_instance()

        # Test HTTP runner resource requirements
        http_runner = registry.get_runner(ExecutionType.HTTP)
        http_reqs = http_runner.get_resource_requirements({"timeout": 120})
        assert http_reqs.cpu_cores == 0.1
        assert http_reqs.memory_mb == 128
        assert http_reqs.disk_mb == 0
        assert http_reqs.timeout_seconds == 120

        # Test Docker runner resource requirements
        docker_runner = registry.get_runner(ExecutionType.DOCKER)
        docker_reqs = docker_runner.get_resource_requirements(
            {"resource_limits": {"memory_mb": 512}}
        )
        assert docker_reqs.memory_mb == 512  # Should use configured limit

        # Test Serverless runner resource requirements
        serverless_runner = registry.get_runner(ExecutionType.SERVERLESS)
        serverless_reqs = serverless_runner.get_resource_requirements({})
        assert serverless_reqs.cpu_cores == 0.1  # Minimal CPU
        assert serverless_reqs.memory_mb == 128  # Minimal memory


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
        result = await runner.validate_config({})
        assert result == False  # Should raise ValueError, but we catch it

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
        http_runner = registry.get_runner(ExecutionType.HTTP)
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
        docker_runner = registry.get_runner(ExecutionType.DOCKER)
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

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
