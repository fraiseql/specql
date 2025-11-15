"""Serverless function execution runner."""

import json
from typing import Any

from src.runners.job_runner import (
    JobRunner,
    JobRecord,
    JobResult,
    ExecutionContext,
    ResourceRequirements,
)


class ServerlessRunner(JobRunner):
    """
    Serverless function execution runner.

    Invokes cloud functions (AWS Lambda, Google Cloud Functions) with
    authentication, async invocation, and cost tracking.
    """

    def __init__(self):
        """Initialize serverless runner."""
        pass

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate serverless runner configuration.

        Required fields:
        - provider: "aws" or "gcp"
        - region/project: Cloud provider region/project
        - auth: Authentication configuration

        Optional fields:
        - timeout: Function timeout (seconds)
        - memory_size: Memory allocation (MB)
        - cost_tracking: Enable cost tracking
        - retry_policy: Retry configuration
        """
        if "provider" not in config:
            raise ValueError("Serverless runner requires 'provider' in config")

        provider = config["provider"].lower()
        if provider not in ["aws", "gcp"]:
            raise ValueError(f"Unsupported provider '{provider}'. Must be 'aws' or 'gcp'")

        if provider == "aws":
            if "region" not in config:
                raise ValueError("AWS provider requires 'region' in config")
            # Validate AWS auth types
            auth = config.get("auth", {})
            if auth.get("type") not in ["iam_role", "access_key", "profile"]:
                raise ValueError("AWS auth type must be 'iam_role', 'access_key', or 'profile'")
        elif provider == "gcp":
            if "project" not in config:
                raise ValueError("GCP provider requires 'project' in config")
            # Validate GCP auth types
            auth = config.get("auth", {})
            if auth.get("type") not in ["service_account", "default_credentials"]:
                raise ValueError("GCP auth type must be 'service_account' or 'default_credentials'")

        if "auth" not in config:
            raise ValueError("Serverless runner requires 'auth' configuration")

        # Validate timeout if specified
        timeout = config.get("timeout")
        if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
            raise ValueError("timeout must be a positive integer")

        # Validate memory_size if specified
        memory = config.get("memory_size")
        if memory is not None and (not isinstance(memory, int) or memory <= 0):
            raise ValueError("memory_size must be a positive integer")

        return True

    async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult:
        """
        Execute serverless function invocation.

        Args:
            job: Job record with function details in input_data
            context: Execution context

        Returns:
            JobResult with function response
        """
        try:
            # Extract function details
            provider = job.input_data.get("provider", "").lower()
            function_name = job.input_data.get("function_name")
            job.input_data.get("payload", {})
            job.input_data.get("invocation_type", "RequestResponse")

            # Get runner config (would come from service registry in production)
            config = {}  # Placeholder

            if not function_name:
                return JobResult(
                    success=False, error_message="function_name is required in input_data"
                )

            if provider == "aws":
                return await self._invoke_lambda(job, context, config)
            elif provider == "gcp":
                return await self._invoke_gcp_function(job, context, config)
            else:
                return JobResult(success=False, error_message=f"Unsupported provider: {provider}")

        except Exception as e:
            return JobResult(success=False, error_message=f"Serverless execution failed: {str(e)}")

    async def _invoke_lambda(
        self, job: JobRecord, context: ExecutionContext, config: dict[str, Any]
    ) -> JobResult:
        """Invoke AWS Lambda function."""
        try:
            # Extract Lambda details
            function_name = job.input_data["function_name"]
            payload = job.input_data.get("payload", {})
            invocation_type = job.input_data.get("invocation_type", "RequestResponse")

            # Import boto3 (may not be available)
            try:
                import boto3
                from botocore.exceptions import ClientError
            except ImportError:
                return JobResult(
                    success=False,
                    error_message="AWS boto3 library not installed. Install with: pip install boto3",
                )

            # Create Lambda client (would use proper auth in production)
            lambda_client = boto3.client("lambda", region_name="us-east-1")

            # Invoke function
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload),
            )

            # Parse response
            if "Payload" in response:
                payload_data = json.loads(
                    response["Payload"].read()
                    if hasattr(response["Payload"], "read")
                    else response["Payload"]
                )
            else:
                payload_data = {}

            return JobResult(
                success=True,
                output_data={
                    "payload": payload_data,
                    "status_code": response.get("StatusCode"),
                    "executed_version": response.get("ExecutedVersion"),
                    "invocation_type": invocation_type,
                },
                resource_usage={
                    "provider": "aws",
                    "function_name": function_name,
                    "invocation_type": invocation_type,
                    "estimated_cost_usd": self._calculate_aws_lambda_cost(
                        memory_mb=config.get("memory_size", 128),
                        duration_ms=1000,  # Placeholder
                        request_count=1,
                    ),
                },
            )

        except Exception as e:
            # Handle both ClientError and general exceptions
            error_msg = str(e)
            if hasattr(e, "response") and "Error" in e.response:
                error_msg = e.response["Error"]["Message"]
            return JobResult(
                success=False, error_message=f"AWS Lambda invocation failed: {error_msg}"
            )

            # Parse response
            if "Payload" in response:
                payload_data = json.loads(
                    response["Payload"].read()
                    if hasattr(response["Payload"], "read")
                    else response["Payload"]
                )
            else:
                payload_data = {}

            return JobResult(
                success=True,
                output_data={
                    "payload": payload_data,
                    "status_code": response.get("StatusCode"),
                    "executed_version": response.get("ExecutedVersion"),
                    "invocation_type": invocation_type,
                },
                resource_usage={
                    "provider": "aws",
                    "function_name": function_name,
                    "invocation_type": invocation_type,
                },
            )

        except ClientError as e:
            return JobResult(
                success=False, error_message=f"AWS Lambda error: {e.response['Error']['Message']}"
            )
        except Exception as e:
            return JobResult(success=False, error_message=f"Lambda invocation failed: {str(e)}")

    async def _invoke_gcp_function(
        self, job: JobRecord, context: ExecutionContext, config: dict[str, Any]
    ) -> JobResult:
        """Invoke Google Cloud Function."""
        try:
            # Extract GCP function details
            function_name = job.input_data["function_name"]
            payload = job.input_data.get("payload", {})

            # Import GCP libraries (may not be available)
            try:
                from google.cloud import functions_v1
                from google.api_core.exceptions import GoogleAPIError
            except ImportError:
                return JobResult(
                    success=False,
                    error_message="Google Cloud libraries not installed. Install with: pip install google-cloud-functions",
                )

            # Create client (would use proper auth in production)
            client = functions_v1.CloudFunctionsServiceAsyncClient()

            # Call function
            request = functions_v1.CallFunctionRequest(
                name=function_name, data=json.dumps(payload).encode("utf-8")
            )

            response = await client.call_function(request)

            # Parse response
            result_data = json.loads(response.result) if response.result else {}

            return JobResult(
                success=True,
                output_data={
                    "result": result_data,
                    "execution_id": response.execution_id,
                    "status": "success",
                },
                resource_usage={"provider": "gcp", "function_name": function_name},
            )

        except Exception as e:
            # Handle both GoogleAPIError and general exceptions
            error_msg = str(e)
            return JobResult(
                success=False, error_message=f"GCP function invocation failed: {error_msg}"
            )

            response = await client.call_function(request)

            # Parse response
            result_data = json.loads(response.result) if response.result else {}

            return JobResult(
                success=True,
                output_data={
                    "result": result_data,
                    "execution_id": response.execution_id,
                    "status": "success",
                },
                resource_usage={"provider": "gcp", "function_name": function_name},
            )

        except GoogleAPIError as e:
            return JobResult(success=False, error_message=f"GCP function error: {str(e)}")
        except Exception as e:
            return JobResult(
                success=False, error_message=f"GCP function invocation failed: {str(e)}"
            )

    async def cancel(self, job_id: str) -> bool:
        """
        Cancel serverless function execution.

        Note: Serverless functions typically cannot be cancelled once invoked.
        This is a no-op for most serverless platforms.
        """
        return False

    def get_resource_requirements(self, config: dict[str, Any]) -> ResourceRequirements:
        """Get resource requirements for serverless runner."""
        return ResourceRequirements(
            cpu_cores=0.1,  # Minimal CPU for invocation
            memory_mb=64,  # Small memory footprint
            disk_mb=0,  # No disk usage
            timeout_seconds=config.get("timeout", 900),  # 15 minutes default
        )

    def _calculate_aws_lambda_cost(
        self, memory_mb: int, duration_ms: int, request_count: int
    ) -> float:
        """
        Calculate estimated AWS Lambda cost.

        Based on current pricing (as of 2024):
        - $0.0000166667 per GB-second
        - $0.20 per 1M requests

        This is a rough estimate for cost tracking purposes.
        """
        # Convert to GB-seconds
        gb_seconds = (memory_mb / 1024) * (duration_ms / 1000)

        # Cost per GB-second
        compute_cost = gb_seconds * 0.0000166667

        # Request cost ($0.20 per million requests)
        request_cost = request_count * (0.20 / 1_000_000)

        return round(compute_cost + request_cost, 8)

    def _calculate_gcp_function_cost(
        self, memory_mb: int, duration_ms: int, request_count: int
    ) -> float:
        """
        Calculate estimated Google Cloud Functions cost.

        Based on current pricing (as of 2024):
        - $0.0000025 per GB-second (first 2M invocations/month)
        - $0.0000015 per GB-second (additional)
        - $0.40 per million invocations

        This is a simplified estimate.
        """
        # Convert to GB-seconds
        gb_seconds = (memory_mb / 1024) * (duration_ms / 1000)

        # Cost per GB-second (using first tier pricing)
        compute_cost = gb_seconds * 0.0000025

        # Request cost ($0.40 per million requests)
        request_cost = request_count * (0.40 / 1_000_000)

        return round(compute_cost + request_cost, 8)
