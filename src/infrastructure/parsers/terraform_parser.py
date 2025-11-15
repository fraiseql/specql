"""
Terraform Parser

Reverse engineers Terraform configurations to universal infrastructure format.
Uses HCL parser (python-hcl2) to parse Terraform syntax.
"""

import hcl2
from typing import Dict, Any, Optional
from src.infrastructure.universal_infra_schema import (
    UniversalInfrastructure,
    ComputeConfig,
    DatabaseConfig,
    NetworkConfig,
    LoadBalancerConfig,
    ContainerConfig,
    ObservabilityConfig,
    SecurityConfig,
    ObjectStorageConfig,
    Bucket,
    DatabaseType,
    CloudProvider,
)


class TerraformParser:
    """Parse Terraform HCL to universal format"""

    def parse(self, tf_content: str) -> UniversalInfrastructure:
        """
        Parse Terraform configuration to UniversalInfrastructure

        Args:
            tf_content: Terraform HCL content

        Returns:
            UniversalInfrastructure object
        """
        try:
            # Parse HCL
            tf_dict = hcl2.loads(tf_content)
        except Exception as e:
            raise ValueError(f"Not a valid Terraform configuration: {e}")

        # Extract resources - hcl2 returns a list of resource blocks
        resource_blocks = tf_dict.get("resource", [])
        if isinstance(resource_blocks, dict):
            # Sometimes it's returned as a dict
            resources = resource_blocks
        else:
            # Flatten list of resource blocks into a single dict
            resources = {}
            for block in resource_blocks:
                resources.update(block)

        # Parse different resource types
        compute = self._parse_compute(resources)
        database = self._parse_database(resources)
        network = self._parse_network(resources)
        load_balancer = self._parse_load_balancer(resources)
        container = self._parse_container(resources)
        observability = self._parse_observability(resources)
        security = self._parse_security(resources)
        object_storage = self._parse_object_storage(resources)

        # Detect provider and region
        provider_config = tf_dict.get("provider", {})
        provider, region = self._detect_provider(provider_config, resources)

        return UniversalInfrastructure(
            name=self._extract_name(resources),
            provider=provider,
            region=region,
            compute=compute,
            container=container,
            database=database,
            network=network,
            load_balancer=load_balancer,
            observability=observability,
            security=security,
            object_storage=object_storage,
        )

    def _parse_compute(self, resources: Dict[str, Any]) -> Optional[ComputeConfig]:
        """Parse compute resources (EC2, Compute Engine, etc.)"""
        # First pass: look for autoscaling groups (highest priority)
        for resource_type, resource_configs in resources.items():
            if "aws_autoscaling_group" in resource_type:
                for name, config in resource_configs.items():
                    return ComputeConfig(
                        instances=config.get("desired_capacity", 1),
                        cpu=2,  # Default assumption - would need launch template parsing for accuracy
                        memory="4GB",  # Default assumption
                        auto_scale=True,
                        min_instances=config.get("min_size", 1),
                        max_instances=config.get("max_size", 10),
                        cpu_target=70,  # Default target
                    )

        # Second pass: look for individual instances
        for resource_type, resource_configs in resources.items():
            if "aws_instance" in resource_type:
                for name, config in resource_configs.items():
                    count = config.get("count", 1)
                    return ComputeConfig(
                        instances=count,
                        cpu=self._map_instance_type_to_cpu(
                            config.get("instance_type", "t3.medium")
                        ),
                        memory=self._map_instance_type_to_memory(
                            config.get("instance_type", "t3.medium")
                        ),
                        instance_type=config.get("instance_type"),
                        availability_zones=config.get("availability_zone", []),
                    )
            elif "google_compute_instance" in resource_type:
                for name, config in resource_configs.items():
                    return ComputeConfig(
                        instances=1,
                        instance_type=config.get("machine_type"),
                        cpu=self._map_gcp_machine_type_to_cpu(
                            config.get("machine_type", "n1-standard-1")
                        ),
                        memory=self._map_gcp_machine_type_to_memory(
                            config.get("machine_type", "n1-standard-1")
                        ),
                    )

        return None

    def _parse_database(self, resources: Dict[str, Any]) -> Optional[DatabaseConfig]:
        """Parse database resources (RDS, Cloud SQL, etc.)"""
        for resource_type, resource_configs in resources.items():
            if "aws_db_instance" in resource_type:
                for name, config in resource_configs.items():
                    engine = config.get("engine", "")
                    db_type = self._map_engine_to_type(engine)

                    return DatabaseConfig(
                        type=db_type,
                        version=str(config.get("engine_version", "")),
                        storage=f"{config.get('allocated_storage', 0)}GB",
                        instance_class=config.get("instance_class"),
                        multi_az=config.get("multi_az", False),
                        backup_retention_days=config.get("backup_retention_period", 0),
                        backup_window=config.get("backup_window", "03:00-04:00"),
                        maintenance_window=config.get(
                            "maintenance_window", "sun:04:00-sun:05:00"
                        ),
                        encryption_at_rest=config.get("storage_encrypted", True),
                        publicly_accessible=config.get("publicly_accessible", False),
                    )
            elif "google_sql_database_instance" in resource_type:
                for name, config in resource_configs.items():
                    settings_list = config.get("settings", [])
                    settings = (
                        settings_list[0]
                        if isinstance(settings_list, list) and settings_list
                        else {}
                    )
                    db_version = config.get("database_version", "")

                    return DatabaseConfig(
                        type=self._map_gcp_db_version_to_type(db_version),
                        version=self._extract_gcp_db_version(db_version),
                        storage=f"{settings.get('disk_size', 10)}GB",
                        instance_class=settings.get("tier"),
                        backup_retention_days=7,  # GCP default
                        encryption_at_rest=True,
                    )

        return None

    def _parse_network(self, resources: Dict[str, Any]) -> NetworkConfig:
        """Parse network resources (VPC, subnets, etc.)"""
        vpc_cidr = "10.0.0.0/16"  # Default
        public_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
        private_subnets = ["10.0.10.0/24", "10.0.20.0/24"]

        for resource_type, resource_configs in resources.items():
            if "aws_vpc" in resource_type:
                for name, config in resource_configs.items():
                    vpc_cidr = config.get("cidr_block", vpc_cidr)
            elif "aws_subnet" in resource_type:
                for name, config in resource_configs.items():
                    cidr = config.get("cidr_block", "")
                    if config.get("map_public_ip_on_launch", False):
                        if cidr not in public_subnets:
                            public_subnets.append(cidr)
                    else:
                        if cidr not in private_subnets:
                            private_subnets.append(cidr)

        return NetworkConfig(
            vpc_cidr=vpc_cidr,
            public_subnets=public_subnets,
            private_subnets=private_subnets,
        )

    def _parse_load_balancer(
        self, resources: Dict[str, Any]
    ) -> Optional[LoadBalancerConfig]:
        """Parse load balancer resources"""
        for resource_type, resource_configs in resources.items():
            if "aws_lb" in resource_type:
                for name, config in resource_configs.items():
                    return LoadBalancerConfig(
                        enabled=True,
                        type=config.get("load_balancer_type", "application"),
                        https=config.get(
                            "enable_deletion_protection", True
                        ),  # Rough approximation
                        cross_zone=config.get("enable_cross_zone_load_balancing", True),
                    )
            elif "aws_alb" in resource_type:  # Legacy ALB
                for name, config in resource_configs.items():
                    return LoadBalancerConfig(
                        enabled=True, type="application", https=True
                    )

        return None

    def _parse_container(self, resources: Dict[str, Any]) -> Optional[ContainerConfig]:
        """Parse container resources (ECS, EKS, etc.)"""
        # This is a simplified implementation
        # In practice, containers might be defined in ECS task definitions,
        # Kubernetes manifests, or Docker Compose files
        for resource_type, resource_configs in resources.items():
            if "aws_ecs_task_definition" in resource_type:
                for name, config in resource_configs.items():
                    container_definitions = config.get("container_definitions", [])
                    if container_definitions:
                        # Parse first container definition
                        container_def = (
                            container_definitions[0]
                            if isinstance(container_definitions, list)
                            else container_definitions
                        )
                        if isinstance(container_def, str):
                            # JSON string - would need to parse
                            continue

                        return ContainerConfig(
                            image=container_def.get("image", ""),
                            port=container_def.get("portMappings", [{}])[0].get(
                                "containerPort", 8000
                            ),
                            environment={
                                k: v for k, v in container_def.get("environment", [])
                            },
                            cpu_limit=container_def.get("cpu", 256)
                            / 1024,  # Convert from ECS units
                            memory_limit=f"{container_def.get('memory', 512)}MB",
                        )

        return None

    def _parse_observability(self, resources: Dict[str, Any]) -> ObservabilityConfig:
        """Parse observability resources (CloudWatch, etc.)"""
        logging_enabled = False
        metrics_enabled = False
        tracing_enabled = False

        for resource_type, resource_configs in resources.items():
            if "aws_cloudwatch_log_group" in resource_type:
                logging_enabled = True
            elif "aws_cloudwatch_metric_alarm" in resource_type:
                metrics_enabled = True
            elif "aws_xray_sampling_rule" in resource_type:
                tracing_enabled = True

        return ObservabilityConfig(
            logging_enabled=logging_enabled,
            metrics_enabled=metrics_enabled,
            tracing_enabled=tracing_enabled,
        )

    def _parse_security(self, resources: Dict[str, Any]) -> SecurityConfig:
        """Parse security resources (IAM, security groups, etc.)"""
        secrets_provider = "aws_secrets"
        iam_roles = []

        for resource_type, resource_configs in resources.items():
            if "aws_iam_role" in resource_type:
                for name, config in resource_configs.items():
                    iam_roles.append(name)
            elif "aws_secretsmanager_secret" in resource_type:
                secrets_provider = "aws_secrets"

        return SecurityConfig(secrets_provider=secrets_provider, iam_roles=iam_roles)

    def _parse_object_storage(
        self, resources: Dict[str, Any]
    ) -> Optional[ObjectStorageConfig]:
        """Parse object storage resources (S3, GCS, etc.)"""
        buckets = []

        for resource_type, resource_configs in resources.items():
            if "aws_s3_bucket" in resource_type:
                for name, config in resource_configs.items():
                    buckets.append(
                        Bucket(
                            name=config.get("bucket", name),
                            versioning=config.get("versioning", {}).get(
                                "enabled", False
                            ),
                            public_access=not config.get("block_public_acls", True),
                            encryption=config.get(
                                "server_side_encryption_configuration", {}
                            )
                            .get("rule", {})
                            .get("apply_server_side_encryption_by_default", {})
                            .get("sse_algorithm")
                            is not None,
                        )
                    )

        if buckets:
            return ObjectStorageConfig(buckets=buckets)
        return None

    def _map_engine_to_type(self, engine: str) -> DatabaseType:
        """Map Terraform engine to universal DatabaseType"""
        engine_map = {
            "postgres": DatabaseType.POSTGRESQL,
            "mysql": DatabaseType.MYSQL,
            "aurora-postgresql": DatabaseType.POSTGRESQL,
            "aurora-mysql": DatabaseType.MYSQL,
            "redis": DatabaseType.REDIS,
            "elasticsearch": DatabaseType.ELASTICSEARCH,
        }
        return engine_map.get(engine.lower(), DatabaseType.POSTGRESQL)

    def _map_gcp_db_version_to_type(self, db_version: str) -> DatabaseType:
        """Map GCP database version to universal DatabaseType"""
        if "POSTGRES" in db_version:
            return DatabaseType.POSTGRESQL
        elif "MYSQL" in db_version:
            return DatabaseType.MYSQL
        return DatabaseType.POSTGRESQL

    def _extract_gcp_db_version(self, db_version: str) -> str:
        """Extract version number from GCP database version string"""
        if "POSTGRES_" in db_version:
            return db_version.split("_")[1]
        elif "MYSQL_" in db_version:
            return db_version.split("_")[1]
        return "15"  # Default

    def _map_instance_type_to_cpu(self, instance_type: str) -> float:
        """Map AWS instance type to CPU cores"""
        # Simplified mapping - in practice would need comprehensive mapping
        cpu_map = {
            "t3.micro": 1,
            "t3.small": 1,
            "t3.medium": 2,
            "t3.large": 2,
            "t3.xlarge": 4,
            "m5.large": 2,
            "m5.xlarge": 4,
            "c5.large": 2,
            "c5.xlarge": 4,
        }
        return cpu_map.get(instance_type, 2)

    def _map_instance_type_to_memory(self, instance_type: str) -> str:
        """Map AWS instance type to memory"""
        # Simplified mapping
        memory_map = {
            "t3.micro": "1GB",
            "t3.small": "2GB",
            "t3.medium": "4GB",
            "t3.large": "8GB",
            "t3.xlarge": "16GB",
            "m5.large": "8GB",
            "m5.xlarge": "16GB",
            "c5.large": "4GB",
            "c5.xlarge": "8GB",
        }
        return memory_map.get(instance_type, "4GB")

    def _map_gcp_machine_type_to_cpu(self, machine_type: str) -> float:
        """Map GCP machine type to CPU cores"""
        # Simplified mapping
        if "n1-standard-1" in machine_type:
            return 1
        elif "n1-standard-2" in machine_type:
            return 2
        elif "n1-standard-4" in machine_type:
            return 4
        elif "n1-standard-8" in machine_type:
            return 8
        return 2  # Default

    def _map_gcp_machine_type_to_memory(self, machine_type: str) -> str:
        """Map GCP machine type to memory"""
        # Simplified mapping
        memory_map = {
            "n1-standard-1": "3.75GB",
            "n1-standard-2": "7.5GB",
            "n1-standard-4": "15GB",
            "n1-standard-8": "30GB",
        }
        return memory_map.get(machine_type, "7.5GB")

    def _detect_provider(
        self, provider_config: Dict[str, Any], resources: Dict[str, Any]
    ) -> tuple[CloudProvider, str]:
        """Detect cloud provider and region"""
        # Check provider block
        if "aws" in provider_config:
            return CloudProvider.AWS, provider_config["aws"].get("region", "us-east-1")
        elif "google" in provider_config:
            return CloudProvider.GCP, provider_config["google"].get(
                "region", "us-central1"
            )
        elif "azurerm" in provider_config:
            return CloudProvider.AZURE, provider_config["azurerm"].get(
                "location", "East US"
            )

        # Infer from resource types
        for resource_type in resources.keys():
            if "aws_" in resource_type:
                return CloudProvider.AWS, "us-east-1"
            elif "google_" in resource_type:
                return CloudProvider.GCP, "us-central1"
            elif "azurerm_" in resource_type:
                return CloudProvider.AZURE, "East US"

        return CloudProvider.AWS, "us-east-1"

    def _extract_name(self, resources: Dict[str, Any]) -> str:
        """Extract a reasonable name from resources"""
        # Try to find a main resource and extract name from tags
        for resource_type in [
            "aws_instance",
            "aws_db_instance",
            "google_compute_instance",
            "aws_ecs_service",
        ]:
            if resource_type in resources:
                resource_configs = resources[resource_type]
                if resource_configs:
                    # Get first resource
                    first_resource_name = list(resource_configs.keys())[0]
                    first_resource_config = resource_configs[first_resource_name]

                    # Try to extract name from tags
                    if "tags" in first_resource_config:
                        tags = first_resource_config["tags"]
                        if isinstance(tags, dict) and "Name" in tags:
                            return tags["Name"]
                        elif isinstance(tags, list) and len(tags) > 0:
                            # GCP style tags
                            return tags[0]

                    # Fallback to resource name
                    return first_resource_name

        return "infrastructure"  # Fallback
