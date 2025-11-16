"""Tests for HTTPRunner."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.runners.http_runner import HTTPRunner
from src.runners.job_runner import (
    JobRecord,
    ExecutionContext,
    ResourceRequirements,
)


@pytest.fixture
def http_runner():
    """Create HTTPRunner instance for testing."""
    return HTTPRunner()


@pytest.fixture
def sample_job():
    """Create a sample job record for testing."""
    return JobRecord(
        id="test-job-1",
        service_name="test-api",
        operation="get_data",
        input_data={"endpoint": "https://api.example.com/data", "method": "GET"},
        timeout_seconds=30,
        attempts=0,
        max_attempts=3,
    )


@pytest.fixture
def sample_context():
    """Create a sample execution context for testing."""
    return ExecutionContext(
        tenant_id="tenant-1", triggered_by="user-1", correlation_id="corr-1"
    )


class TestHTTPRunnerConfigValidation:
    """Test HTTP runner configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_config_valid_minimal(self, http_runner):
        """Validate minimal valid configuration."""
        config = {"base_url": "https://api.example.com"}

        result = await http_runner.validate_config(config)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_valid_https(self, http_runner):
        """Validate HTTPS base URL."""
        config = {"base_url": "https://secure-api.example.com"}

        result = await http_runner.validate_config(config)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_valid_http(self, http_runner):
        """Validate HTTP base URL."""
        config = {"base_url": "http://dev-api.example.com"}

        result = await http_runner.validate_config(config)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_missing_base_url(self, http_runner):
        """Reject configuration without base_url."""
        config = {"timeout": 30}

        with pytest.raises(ValueError, match="HTTP runner requires 'base_url'"):
            await http_runner.validate_config(config)

    @pytest.mark.asyncio
    async def test_validate_config_invalid_base_url_no_protocol(self, http_runner):
        """Reject base URL without http/https protocol."""
        config = {"base_url": "api.example.com"}

        with pytest.raises(ValueError, match="Invalid base_url"):
            await http_runner.validate_config(config)

    @pytest.mark.asyncio
    async def test_validate_config_invalid_base_url_ftp(self, http_runner):
        """Reject non-HTTP protocols."""
        config = {"base_url": "ftp://files.example.com"}

        with pytest.raises(ValueError, match="Invalid base_url"):
            await http_runner.validate_config(config)

    @pytest.mark.asyncio
    async def test_validate_config_empty_base_url(self, http_runner):
        """Reject empty base URL."""
        config = {"base_url": ""}

        with pytest.raises(ValueError, match="Invalid base_url"):
            await http_runner.validate_config(config)


class TestHTTPRunnerExecution:
    """Test HTTP runner job execution."""

    @pytest.mark.asyncio
    async def test_execute_get_request_success(
        self, http_runner, sample_job, sample_context
    ):
        """Execute successful GET request."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"data": "success"}'
        mock_response.json.return_value = {"data": "success"}
        mock_response.elapsed.total_seconds.return_value = 1.5
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(sample_job, sample_context)

            assert result.success is True
            assert result.output_data == {"data": "success"}
            assert result.duration_seconds == 1.5
            assert result.resource_usage == {
                "status_code": 200,
                "response_size_bytes": 19,  # len(b'{"data": "success"}')
            }
            assert result.error_message is None

            # Verify request was made correctly
            mock_request.assert_called_once_with(
                method="GET",
                url="https://api.example.com/data",
                json=None,
                headers={},
                timeout=30,
            )

    @pytest.mark.asyncio
    async def test_execute_post_request_with_payload(self, http_runner, sample_context):
        """Execute POST request with JSON payload."""
        job = JobRecord(
            id="post-job",
            service_name="api",
            operation="create",
            input_data={
                "endpoint": "https://api.example.com/items",
                "method": "POST",
                "payload": {"name": "test item", "value": 42},
            },
            timeout_seconds=60,
            attempts=0,
            max_attempts=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = b'{"id": 123, "name": "test item"}'
        mock_response.json.return_value = {"id": 123, "name": "test item"}
        mock_response.elapsed.total_seconds.return_value = 2.0
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_context)

            assert result.success is True
            assert result.output_data == {"id": 123, "name": "test item"}

            # Verify JSON payload was sent
            mock_request.assert_called_once_with(
                method="POST",
                url="https://api.example.com/items",
                json={"name": "test item", "value": 42},
                headers={},
                timeout=60,
            )

    @pytest.mark.asyncio
    async def test_execute_put_request(self, http_runner, sample_context):
        """Execute PUT request."""
        job = JobRecord(
            id="put-job",
            service_name="api",
            operation="update",
            input_data={
                "endpoint": "https://api.example.com/items/123",
                "method": "PUT",
                "payload": {"name": "updated item"},
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"id": 123, "name": "updated item"}'
        mock_response.json.return_value = {"id": 123, "name": "updated item"}
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_context)

            assert result.success is True
            mock_request.assert_called_once_with(
                method="PUT",
                url="https://api.example.com/items/123",
                json={"name": "updated item"},
                headers={},
                timeout=30,
            )

    @pytest.mark.asyncio
    async def test_execute_delete_request(self, http_runner, sample_context):
        """Execute DELETE request."""
        job = JobRecord(
            id="delete-job",
            service_name="api",
            operation="delete",
            input_data={
                "endpoint": "https://api.example.com/items/123",
                "method": "DELETE",
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_response.json.return_value = {}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_context)

            assert result.success is True
            assert result.output_data == {}
            mock_request.assert_called_once_with(
                method="DELETE",
                url="https://api.example.com/items/123",
                json=None,
                headers={},
                timeout=30,
            )

    @pytest.mark.asyncio
    async def test_execute_with_custom_headers(self, http_runner, sample_context):
        """Execute request with custom headers."""
        job = JobRecord(
            id="headers-job",
            service_name="api",
            operation="get",
            input_data={
                "endpoint": "https://api.example.com/data",
                "method": "GET",
                "headers": {"Authorization": "Bearer token123", "X-Custom": "value"},
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"data": "ok"}'
        mock_response.json.return_value = {"data": "ok"}
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_context)

            assert result.success is True
            mock_request.assert_called_once_with(
                method="GET",
                url="https://api.example.com/data",
                json=None,
                headers={"Authorization": "Bearer token123", "X-Custom": "value"},
                timeout=30,
            )

    @pytest.mark.asyncio
    async def test_execute_method_case_insensitive(self, http_runner, sample_context):
        """Execute handles method case insensitivity."""
        job = JobRecord(
            id="case-job",
            service_name="api",
            operation="get",
            input_data={
                "endpoint": "https://api.example.com/data",
                "method": "get",  # lowercase
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"data": "ok"}'
        mock_response.json.return_value = {"data": "ok"}
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_context)

            assert result.success is True
            mock_request.assert_called_once_with(
                method="GET",  # Should be uppercased
                url="https://api.example.com/data",
                json=None,
                headers={},
                timeout=30,
            )


class TestHTTPRunnerErrorHandling:
    """Test HTTP runner error handling."""

    @pytest.mark.asyncio
    async def test_execute_http_error_404(
        self, http_runner, sample_job, sample_context
    ):
        """Handle HTTP 404 error."""
        from httpx import HTTPStatusError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        http_error = HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )

        with patch.object(http_runner.client, "request", side_effect=http_error):
            result = await http_runner.execute(sample_job, sample_context)

            assert not result.success
            assert result.error_message == "HTTP 404: Not Found"
            assert result.output_data is None

    @pytest.mark.asyncio
    async def test_execute_http_error_500(
        self, http_runner, sample_job, sample_context
    ):
        """Handle HTTP 500 error."""
        from httpx import HTTPStatusError

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        http_error = HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch.object(http_runner.client, "request", side_effect=http_error):
            result = await http_runner.execute(sample_job, sample_context)

            assert not result.success
            assert result.error_message == "HTTP 500: Internal Server Error"

    @pytest.mark.asyncio
    async def test_execute_network_error(self, http_runner, sample_job, sample_context):
        """Handle network connection errors."""
        from httpx import ConnectError

        connect_error = ConnectError("Connection refused")

        with patch.object(http_runner.client, "request", side_effect=connect_error):
            result = await http_runner.execute(sample_job, sample_context)

            assert not result.success
            assert result.error_message == "HTTP request failed: Connection refused"

    @pytest.mark.asyncio
    async def test_execute_timeout_error(self, http_runner, sample_job, sample_context):
        """Handle request timeout errors."""
        from httpx import TimeoutException

        timeout_error = TimeoutException("Request timeout")

        with patch.object(http_runner.client, "request", side_effect=timeout_error):
            result = await http_runner.execute(sample_job, sample_context)

            assert not result.success
            assert "HTTP request failed: Request timeout" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_json_parse_error(self, http_runner, sample_context):
        """Handle JSON parsing errors in response."""
        job = JobRecord(
            id="json-job",
            service_name="api",
            operation="get",
            input_data={"endpoint": "https://api.example.com/data", "method": "GET"},
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"invalid json {{{"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_context)

            # Should succeed but with empty dict as fallback for invalid JSON
            assert result.success is True
            assert result.output_data == {}

    @pytest.mark.asyncio
    async def test_execute_empty_response(self, http_runner, sample_context):
        """Handle empty response body."""
        job = JobRecord(
            id="empty-job",
            service_name="api",
            operation="delete",
            input_data={
                "endpoint": "https://api.example.com/item/123",
                "method": "DELETE",
            },
            timeout_seconds=30,
            attempts=0,
            max_attempts=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""  # Empty content
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.raise_for_status.return_value = None

        with patch.object(
            http_runner.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await http_runner.execute(job, sample_context)

            assert result.success is True
            assert result.output_data == {}  # Empty dict for empty response


class TestHTTPRunnerCancel:
    """Test HTTP runner cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_always_returns_false(self, http_runner):
        """Cancel always returns False for HTTP runner."""
        result = await http_runner.cancel("job-123")
        assert not result

        result = await http_runner.cancel("any-job-id")
        assert not result


class TestHTTPRunnerResourceRequirements:
    """Test HTTP runner resource requirements."""

    def test_get_resource_requirements_default(self, http_runner):
        """Get default resource requirements."""
        config = {}

        reqs = http_runner.get_resource_requirements(config)

        assert isinstance(reqs, ResourceRequirements)
        assert reqs.cpu_cores == 0.1
        assert reqs.memory_mb == 128
        assert reqs.disk_mb == 0
        assert reqs.timeout_seconds == 300  # Default timeout

    def test_get_resource_requirements_custom_timeout(self, http_runner):
        """Get resource requirements with custom timeout."""
        config = {"timeout": 60}

        reqs = http_runner.get_resource_requirements(config)

        assert reqs.cpu_cores == 0.1
        assert reqs.memory_mb == 128
        assert reqs.disk_mb == 0
        assert reqs.timeout_seconds == 60

    def test_get_resource_requirements_zero_timeout(self, http_runner):
        """Handle zero timeout in config."""
        config = {"timeout": 0}

        reqs = http_runner.get_resource_requirements(config)

        assert reqs.timeout_seconds == 0


class TestHTTPRunnerInitialization:
    """Test HTTP runner initialization."""

    def test_init_creates_httpx_client(self):
        """Initialization creates httpx AsyncClient."""
        runner = HTTPRunner()

        assert hasattr(runner, "client")
        assert runner.client is not None
        # Note: We can't easily test the exact type due to mocking in tests
