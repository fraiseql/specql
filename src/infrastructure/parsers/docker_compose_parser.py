"""
Docker Compose Parser

Reverse engineers Docker Compose YAML files to universal infrastructure format.
"""

import yaml
from typing import Dict, Any, List, Optional
from src.infrastructure.universal_infra_schema import (
    UniversalInfrastructure,
    ContainerConfig,
    NetworkConfig,
    Volume,
    DatabaseConfig,
    DatabaseType,
    CloudProvider,
)


class DockerComposeParser:
    """Parse Docker Compose YAML to universal format"""

    def parse(self, compose_content: str) -> UniversalInfrastructure:
        """
        Parse Docker Compose configuration to UniversalInfrastructure

        Args:
            compose_content: Docker Compose YAML content

        Returns:
            UniversalInfrastructure object
        """
        try:
            compose_dict = yaml.safe_load(compose_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Not a valid Docker Compose file: {e}")

        if not compose_dict:
            raise ValueError("Empty Docker Compose file")

        # Extract services
        services = compose_dict.get("services", {})

        # Detect main service (usually the first web/API service)
        main_service_name = self._detect_main_service(services)
        main_service_config = services.get(main_service_name, {})

        # Parse secrets section
        secrets_config = compose_dict.get("secrets", {})

        # Parse different components
        container = self._parse_container(main_service_config, secrets_config)
        database = self._parse_database(services)
        network = self._parse_network(compose_dict)
        volumes = self._parse_volumes(compose_dict)

        # Extract environment and other metadata
        compose_dict.get("version", "3.8")

        return UniversalInfrastructure(
            name=main_service_name,
            provider=CloudProvider.DOCKER,
            region="docker-compose",  # Generic for docker
            container=container,
            database=database,
            network=network,
            volumes=volumes,
        )

    def _detect_main_service(self, services: Dict[str, Any]) -> str:
        """Detect the main service in the compose file"""
        # Priority: web, frontend, api, app, backend, then first service
        priority_patterns = ["web", "frontend", "api", "app", "backend"]

        for pattern in priority_patterns:
            for service_name in services.keys():
                if pattern in service_name.lower():
                    return service_name

        # Fallback to first service
        return list(services.keys())[0] if services else "docker-service"

    def _parse_container(
        self,
        service_config: Dict[str, Any],
        secrets_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[ContainerConfig]:
        """Parse container configuration"""
        if not service_config:
            return None

        # Basic container info
        image = service_config.get("image", "")
        if ":" not in image:
            image = f"{image}:latest"

        # Ports
        ports = service_config.get("ports", [])
        port = 80  # Default
        if ports:
            # Extract first port mapping
            first_port = ports[0]
            if isinstance(first_port, str):
                # Format: "8080:80"
                if ":" in first_port:
                    port = int(first_port.split(":")[-1])
                else:
                    port = int(first_port)
            elif isinstance(first_port, int):
                port = first_port

        # Environment variables
        environment = service_config.get("environment", {})
        if isinstance(environment, list):
            # Convert list format ["KEY=value", "KEY2=value2"] to dict
            env_dict = {}
            for env_item in environment:
                if isinstance(env_item, str) and "=" in env_item:
                    key, value = env_item.split("=", 1)
                    env_dict[key] = value
            environment = env_dict
        elif not isinstance(environment, dict):
            environment = {}

        # Secrets (environment variables that reference secrets)
        secrets = {}

        # Check for secrets referenced in environment variables
        for key, value in environment.items():
            if (
                isinstance(value, str)
                and value.startswith("${")
                and "secrets" in value.lower()
            ):
                secrets[key] = f"${{secrets.{key.lower()}}}"

        # Check for secrets defined in service secrets section
        service_secrets = service_config.get("secrets", [])
        if service_secrets and secrets_config:
            for secret_ref in service_secrets:
                if isinstance(secret_ref, str) and secret_ref in secrets_config:
                    # Map secret name to the expected format
                    secret_key = secret_ref.upper()
                    secrets[secret_key] = f"${{secrets.{secret_ref}}}"

        # Remove secrets from regular environment
        for key in secrets.keys():
            if key in environment:
                del environment[key]

        # Resources
        deploy = service_config.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})
        reservations = resources.get("reservations", {})

        cpu_limit = limits.get("cpus")
        if cpu_limit:
            cpu_limit = float(cpu_limit)

        memory_limit = limits.get("memory")
        if memory_limit:
            memory_limit = self._parse_memory(memory_limit)

        cpu_request = reservations.get("cpus")
        if cpu_request:
            cpu_request = float(cpu_request)

        memory_request = reservations.get("memory")
        if memory_request:
            memory_request = self._parse_memory(memory_request)

        # Health check
        healthcheck = service_config.get("healthcheck", {})
        health_check_path = "/health"  # Default
        if healthcheck:
            test = healthcheck.get("test", [])
            if isinstance(test, list) and len(test) > 1:
                # Look for curl command with path
                test_cmd = " ".join(test[1:])
                if "curl" in test_cmd and "-f" in test_cmd:
                    # Extract URL path from curl command
                    parts = test_cmd.split()
                    for i, part in enumerate(parts):
                        if part.startswith("http"):
                            from urllib.parse import urlparse

                            parsed = urlparse(part)
                            if parsed.path:
                                health_check_path = parsed.path
                            break

        return ContainerConfig(
            image=image,
            port=port,
            environment=environment,
            secrets=secrets,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            cpu_request=cpu_request,
            memory_request=memory_request,
            health_check_path=health_check_path,
        )

    def _parse_database(self, services: Dict[str, Any]) -> Optional[DatabaseConfig]:
        """Parse database services"""
        # Priority order: db/database first, then specific types, cache last
        priority_patterns = [
            ["db", "database"],  # Primary databases
            ["postgres", "mysql", "mongodb"],  # Specific database types
            ["redis"],  # Cache services
        ]

        for pattern_group in priority_patterns:
            for service_name, service_config in services.items():
                if any(pattern in service_name.lower() for pattern in pattern_group):
                    image = service_config.get("image", "").lower()

                    # Detect database type from image
                    db_type = DatabaseType.POSTGRESQL  # Default
                    version = "15"  # Default

                    if "postgres" in image:
                        db_type = DatabaseType.POSTGRESQL
                        version = self._extract_version_from_image(image, "postgres")
                    elif "mysql" in image:
                        db_type = DatabaseType.MYSQL
                        version = self._extract_version_from_image(image, "mysql")
                    elif "redis" in image:
                        db_type = DatabaseType.REDIS
                        version = self._extract_version_from_image(image, "redis")
                    elif "mongo" in image:
                        db_type = DatabaseType.MONGODB
                        version = self._extract_version_from_image(image, "mongo")

                    # Environment variables for database config
                    environment = service_config.get("environment", {})

                    if isinstance(environment, list):
                        env_dict = {
                            k: v
                            for item in environment
                            for k, v in [item.split("=", 1)]
                            if "=" in item
                        }
                        environment = env_dict

                    # Extract storage from volumes if present
                    storage = "50GB"  # Default
                    volumes = service_config.get("volumes", [])
                    for volume in volumes:
                        if isinstance(volume, str) and "postgres" in volume.lower():
                            # Parse volume mapping like "./postgres-data:/var/lib/postgresql/data"
                            if ":" in volume:
                                volume.split(":")[0]
                                # Could parse size from host directory, but for now use default

                    return DatabaseConfig(
                        type=db_type, version=version, storage=storage
                    )

        return None

    def _parse_network(self, compose_dict: Dict[str, Any]) -> NetworkConfig:
        """Parse network configuration"""
        # Docker Compose networks are usually simple
        networks = compose_dict.get("networks", {})
        if networks:
            # Use first network configuration
            first_network = list(networks.values())[0]
            if isinstance(first_network, dict):
                first_network.get("driver", "bridge")
                # Could map driver to network config, but keep simple for now

        return NetworkConfig()

    def _parse_volumes(self, compose_dict: Dict[str, Any]) -> List[Volume]:
        """Parse named volumes"""
        volumes = []
        named_volumes = compose_dict.get("volumes", {})

        for volume_name, volume_config in named_volumes.items():
            if isinstance(volume_config, dict):
                volume_config.get("driver", "local")
                # For now, create basic volume config
                # In practice, would need to map to actual storage requirements
                volumes.append(
                    Volume(
                        name=volume_name,
                        size="10GB",  # Default size
                        mount_path=f"/data/{volume_name}",
                        storage_class="standard",
                    )
                )
            else:
                # Volume defined without config (just the name)
                volumes.append(
                    Volume(
                        name=volume_name,
                        size="10GB",  # Default size
                        mount_path=f"/data/{volume_name}",
                        storage_class="standard",
                    )
                )

        return volumes

    def _parse_memory(self, memory_str: str) -> str:
        """Parse Docker Compose memory format to universal format"""
        if not memory_str:
            return "512MB"

        memory_str = memory_str.lower()

        # Convert to MB or GB
        if memory_str.endswith("gb") or memory_str.endswith("g"):
            value = float(memory_str.rstrip("gb").rstrip("g"))
            return f"{int(value)}GB" if value.is_integer() else f"{value}GB"
        elif memory_str.endswith("mb") or memory_str.endswith("m"):
            value = float(memory_str.rstrip("mb").rstrip("m"))
            return f"{int(value)}MB" if value.is_integer() else f"{value}MB"
        else:
            # Assume MB if no unit
            try:
                value = float(memory_str)
                return f"{int(value)}MB" if value.is_integer() else f"{value}MB"
            except ValueError:
                return "512MB"

    def _extract_version_from_image(self, image: str, db_type: str) -> str:
        """Extract version from container image"""
        if ":" in image:
            version_part = image.split(":")[-1]
            # Remove any suffixes like -alpine
            version = version_part.split("-")[0]
            return version

        # Defaults
        defaults = {"postgres": "15", "mysql": "8.0", "redis": "7.0", "mongo": "7.0"}
        return defaults.get(db_type, "latest")
