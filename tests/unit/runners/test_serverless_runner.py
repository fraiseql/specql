"""Tests for ServerlessRunner."""

import pytest
from unittest.mock import patch

from src.runners.job_runner import JobRecord, ExecutionContext, JobResult


@pytest.mark.asyncio
async def test_serverless_runner_invokes_lambda():
    """ServerlessRunner invokes AWS Lambda functions"""
    from src.runners.serverless_runner import ServerlessRunner

    runner = ServerlessRunner()

    job = JobRecord(
        id="test-job-lambda-1",
        service_name="lambda_processor",
        operation="process",
        input_data={
            "function_name": "my-lambda-function",
            "payload": {"data": "test"},
            "provider": "aws",
        },
        timeout_seconds=300,
        attempts=0,
        max_attempts=3,
    )

    context = ExecutionContext(
        tenant_id="tenant-1", triggered_by="user-1", correlation_id="corr-1"
    )

    expected_result = JobResult(
        success=True,
        output_data={"payload": {"result": "success"}},
        resource_usage={"provider": "aws"},
    )

    with patch.object(
        runner, "_invoke_lambda", return_value=expected_result
    ) as mock_invoke:
        result = await runner.execute(job, context)

        assert result.success is True
        assert result.output_data["payload"]["result"] == "success"
        mock_invoke.assert_called_once_with(job, context, {})


@pytest.mark.asyncio
async def test_serverless_runner_invokes_gcp_function():
    """ServerlessRunner invokes Google Cloud Functions"""
    from src.runners.serverless_runner import ServerlessRunner

    runner = ServerlessRunner()

    job = JobRecord(
        id="test-job-gcp-1",
        service_name="gcp_processor",
        operation="process",
        input_data={
            "function_name": "my-gcp-function",
            "payload": {"data": "test"},
            "provider": "gcp",
        },
        timeout_seconds=300,
        attempts=0,
        max_attempts=3,
    )

    context = ExecutionContext(
        tenant_id="tenant-1", triggered_by="user-1", correlation_id="corr-1"
    )

    expected_result = JobResult(
        success=True,
        output_data={"result": {"result": "success"}},
        resource_usage={"provider": "gcp"},
    )

    with patch.object(
        runner, "_invoke_gcp_function", return_value=expected_result
    ) as mock_invoke:
        result = await runner.execute(job, context)

        assert result.success is True
        assert result.output_data["result"]["result"] == "success"
        mock_invoke.assert_called_once_with(job, context, {})


@pytest.mark.asyncio
async def test_serverless_runner_validates_config():
    """ServerlessRunner validates runner configuration"""
    from src.runners.serverless_runner import ServerlessRunner

    runner = ServerlessRunner()

    # Valid AWS config
    valid_aws_config = {
        "provider": "aws",
        "region": "us-east-1",
        "auth": {"type": "iam_role"},
    }

    assert await runner.validate_config(valid_aws_config) is True

    # Valid GCP config
    valid_gcp_config = {
        "provider": "gcp",
        "project": "my-project",
        "region": "us-central1",
        "auth": {"type": "service_account"},
    }

    assert await runner.validate_config(valid_gcp_config) is True

    # Invalid config - missing provider
    invalid_config = {"region": "us-east-1"}

    with pytest.raises(
        ValueError, match="Serverless runner requires 'provider' in config"
    ):
        await runner.validate_config(invalid_config)


@pytest.mark.asyncio
async def test_serverless_runner_handles_lambda_errors():
    """ServerlessRunner handles AWS Lambda invocation errors"""
    from src.runners.serverless_runner import ServerlessRunner

    runner = ServerlessRunner()

    job = JobRecord(
        id="test-job-error-1",
        service_name="lambda_processor",
        operation="process",
        input_data={
            "function_name": "nonexistent-function",
            "payload": {"data": "test"},
            "provider": "aws",
        },
        timeout_seconds=30,
        attempts=0,
        max_attempts=3,
    )

    context = ExecutionContext(
        tenant_id="tenant-1", triggered_by="user-1", correlation_id="corr-1"
    )

    error_result = JobResult(
        success=False,
        error_message="AWS Lambda invocation failed: ResourceNotFoundException",
    )

    with patch.object(
        runner, "_invoke_lambda", return_value=error_result
    ) as mock_invoke:
        result = await runner.execute(job, context)

        assert not result.success
        assert "ResourceNotFoundException" in result.error_message
        mock_invoke.assert_called_once_with(job, context, {})


@pytest.mark.asyncio
async def test_serverless_runner_async_invocation():
    """ServerlessRunner handles async invocation with result polling"""
    from src.runners.serverless_runner import ServerlessRunner

    runner = ServerlessRunner()

    job = JobRecord(
        id="test-job-async-1",
        service_name="lambda_processor",
        operation="process_async",
        input_data={
            "function_name": "my-async-function",
            "payload": {"data": "test"},
            "provider": "aws",
            "invocation_type": "Event",  # Async invocation
        },
        timeout_seconds=300,
        attempts=0,
        max_attempts=3,
    )

    context = ExecutionContext(
        tenant_id="tenant-1", triggered_by="user-1", correlation_id="corr-1"
    )

    async_result = JobResult(
        success=True,
        output_data={
            "payload": {},
            "status_code": 202,
            "executed_version": "$LATEST",
            "invocation_type": "Event",
        },
        resource_usage={"provider": "aws", "invocation_type": "Event"},
    )

    with patch.object(
        runner, "_invoke_lambda", return_value=async_result
    ) as mock_invoke:
        result = await runner.execute(job, context)

        assert result.success is True
        assert result.output_data["invocation_type"] == "Event"
        mock_invoke.assert_called_once_with(job, context, {})


@pytest.mark.asyncio
async def test_serverless_runner_cancel_not_supported():
    """ServerlessRunner cancel method returns False (not supported)"""
    from src.runners.serverless_runner import ServerlessRunner

    runner = ServerlessRunner()

    cancelled = await runner.cancel("job-123")

    assert not cancelled
