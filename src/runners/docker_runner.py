"""Docker container execution runner."""

from typing import Any

import docker

from src.runners.job_runner import (
    ExecutionContext,
    JobRecord,
    JobResult,
    JobRunner,
    ResourceRequirements,
)


class DockerRunner(JobRunner):
    """
    Docker container execution runner.

    Executes jobs in Docker containers with comprehensive security controls:
    - Image allowlisting
    - Volume mounting with path validation
    - Resource limits (CPU, memory, disk)
    - Network isolation
    - Container lifecycle management
    """

    def __init__(self) -> None:
        """Initialize Docker runner with Docker client."""
        self.client = docker.from_env()

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate Docker runner configuration.

        Required fields:
        - allowed_images: List of allowed Docker images

        Optional fields:
        - default_timeout: Default execution timeout
        - network_mode: Network isolation mode
        - resource_limits: Default resource limits
        """
        if "allowed_images" not in config:
            raise ValueError("Docker runner requires 'allowed_images' in config")

        allowed_images = config["allowed_images"]
        if not isinstance(allowed_images, list) or len(allowed_images) == 0:
            raise ValueError("'allowed_images' must be a non-empty list")

        return True

    async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult:
        """
        Execute job in Docker container.

        Args:
            job: Job record with container configuration in input_data
            context: Execution context with security policy

        Returns:
            JobResult with container execution results
        """
        try:
            # Extract container configuration
            image = job.input_data.get("image")
            command = job.input_data.get("command", [])
            env_vars = job.input_data.get("env_vars", {})
            volumes = job.input_data.get("volumes", {})
            network_mode = job.input_data.get("network_mode")

            if not image:
                return JobResult(success=False, error_message="No image specified in input_data")

            # Security check: Validate image is allowed
            security_context = context.security_context or {}
            allowed_images = security_context.get("allowed_images", [])

            if image not in allowed_images:
                return JobResult(
                    success=False,
                    error_message=f"Image '{image}' is not allowed. Allowed images: {allowed_images}",
                )

            # Security check: Validate volume mounts
            if volumes:
                allowed_mounts = security_context.get("allowed_mounts", [])
                if not self._validate_volume_mounts(volumes, allowed_mounts):
                    return JobResult(
                        success=False, error_message="One or more volume mounts are not allowed"
                    )

            # Apply resource limits
            resource_limits = security_context.get("resource_limits", {})
            container_config = {
                "image": image,
                "command": command,
                "environment": env_vars,
                "volumes": volumes,
                "detach": False,  # Run synchronously
                "remove": True,  # Auto-remove container after execution
            }

            # Apply network isolation
            if network_mode:
                container_config["network_mode"] = network_mode
            elif "network_mode" in security_context:
                container_config["network_mode"] = security_context["network_mode"]

            # Apply CPU limits
            if "cpu_quota" in resource_limits:
                container_config["cpu_quota"] = resource_limits["cpu_quota"]
            if "cpu_period" in resource_limits:
                container_config["cpu_period"] = resource_limits["cpu_period"]

            # Apply memory limits
            if "memory" in resource_limits:
                container_config["mem_limit"] = resource_limits["memory"]

            # Apply disk limits (storage-opt for overlay driver)
            if "disk_quota" in resource_limits:
                container_config["storage_opt"] = {"size": resource_limits["disk_quota"]}

            # Execute container
            container = self.client.containers.run(**container_config)

            # Get logs and exit code
            logs = container.logs(stdout=True, stderr=True)
            exit_code = container.wait()["StatusCode"]

            # Parse output
            output_data = {
                "exit_code": exit_code,
                "stdout": logs.decode("utf-8") if logs else "",
            }

            if exit_code == 0:
                return JobResult(
                    success=True,
                    output_data=output_data,
                )
            else:
                return JobResult(
                    success=False,
                    error_message=f"Container exited with code {exit_code}",
                    output_data=output_data,
                )

        except Exception as e:
            return JobResult(success=False, error_message=f"Docker execution failed: {str(e)}")

    def _validate_volume_mounts(self, volumes: dict[str, Any], allowed_mounts: list[str]) -> bool:
        """
        Validate volume mounts against allowed paths.

        Args:
            volumes: Volume mapping dict
            allowed_mounts: List of allowed host path prefixes

        Returns:
            True if all mounts are allowed
        """
        for host_path in volumes.keys():
            # Check if host path starts with any allowed mount path
            allowed = any(host_path.startswith(allowed_path) for allowed_path in allowed_mounts)
            if not allowed:
                return False
        return True

    async def cancel(self, job_id: str) -> bool:
        """
        Cancel running container.

        Args:
            job_id: Container ID to cancel

        Returns:
            True if container was successfully cancelled
        """
        try:
            # Get the container
            container = self.client.containers.get(job_id)

            # Stop the container
            container.stop(timeout=10)  # Give 10 seconds to stop gracefully

            # Remove the container
            container.remove()

            return True

        except Exception:
            # Container might already be stopped/removed
            return False

    def get_resource_requirements(self, config: dict[str, Any]) -> ResourceRequirements:
        """Get resource requirements for Docker runner."""
        limits = config.get("resource_limits", {})

        return ResourceRequirements(
            cpu_cores=limits.get("cpu", 1.0),
            memory_mb=limits.get("memory_mb", 512),
            disk_mb=limits.get("disk_mb", 1024),
            timeout_seconds=config.get("default_timeout", 1800),
        )
