"""HTTP API execution runner."""

from typing import Any

import httpx

from src.runners.job_runner import (
    ExecutionContext,
    JobRecord,
    JobResult,
    JobRunner,
    ResourceRequirements,
)


class HTTPRunner(JobRunner):
    """
    HTTP API execution runner.

    Executes jobs by making HTTP requests to external APIs.
    Supports GET, POST, PUT, DELETE methods with authentication.
    """

    def __init__(self) -> None:
        """Initialize HTTP runner with httpx client."""
        self.client = httpx.AsyncClient()

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate HTTP runner configuration.

        Required fields:
        - base_url: Base URL for API

        Optional fields:
        - auth_type: Authentication type (bearer, basic, api_key)
        - headers: Default headers
        - timeout: Request timeout
        """
        if "base_url" not in config:
            raise ValueError("HTTP runner requires 'base_url' in config")

        base_url = config["base_url"]
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            raise ValueError(f"Invalid base_url: {base_url}")

        return True

    async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult:
        """
        Execute HTTP API call.

        Args:
            job: Job record with input_data containing request details
            context: Execution context

        Returns:
            JobResult with API response
        """
        try:
            # Extract request details from input_data
            endpoint = job.input_data.get("endpoint", "")
            method = job.input_data.get("method", "GET").upper()
            payload = job.input_data.get("payload")
            headers = job.input_data.get("headers", {})

            # Make HTTP request
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=payload if method in ["POST", "PUT", "PATCH"] else None,
                headers=headers,
                timeout=job.timeout_seconds,
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            try:
                output_data = response.json() if response.content else {}
            except ValueError:
                # If JSON parsing fails, return empty dict
                output_data = {}

            return JobResult(
                success=True,
                output_data=output_data,
                duration_seconds=response.elapsed.total_seconds(),
                resource_usage={
                    "status_code": response.status_code,
                    "response_size_bytes": len(response.content),
                },
            )

        except httpx.HTTPStatusError as e:
            return JobResult(
                success=False,
                error_message=f"HTTP {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            return JobResult(
                success=False, error_message=f"HTTP request failed: {str(e)}"
            )

    async def cancel(self, job_id: str) -> bool:
        """
        Cancel HTTP request.

        Note: HTTP requests are typically short-lived and cannot be cancelled
        once started. This is a no-op.
        """
        return False

    def get_resource_requirements(self, config: dict[str, Any]) -> ResourceRequirements:
        """Get resource requirements for HTTP runner."""
        return ResourceRequirements(
            cpu_cores=0.1,  # Minimal CPU
            memory_mb=128,  # Small memory footprint
            disk_mb=0,  # No disk usage
            timeout_seconds=config.get("timeout", 300),
        )
