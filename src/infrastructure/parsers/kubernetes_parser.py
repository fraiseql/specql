"""
Kubernetes Parser

Reverse engineers Kubernetes manifests to universal infrastructure format.
Parses YAML manifests (Deployment, Service, Ingress, ConfigMap, Secret, etc.)
"""

import yaml
from typing import Dict, Any, List, Optional
from src.infrastructure.universal_infra_schema import (
    UniversalInfrastructure,
    ComputeConfig,
    ContainerConfig,
    DatabaseConfig,
    LoadBalancerConfig,
    NetworkConfig,
    ObservabilityConfig,
    SecurityConfig,
    Volume,
    CloudProvider,
    DatabaseType,
)


class KubernetesParser:
    """Parse Kubernetes YAML manifests to universal format"""

    def parse(self, k8s_content: str) -> UniversalInfrastructure:
        """
        Parse Kubernetes manifests to UniversalInfrastructure

        Args:
            k8s_content: Kubernetes YAML content (can contain multiple documents separated by ---)

        Returns:
            UniversalInfrastructure object
        """
        try:
            # Parse YAML documents
            documents = yaml.safe_load_all(k8s_content)
            manifests = [doc for doc in documents if doc is not None]
        except yaml.YAMLError as e:
            raise ValueError(f"Not a valid Kubernetes manifest: {e}")

        # Group manifests by kind
        grouped_manifests = self._group_manifests_by_kind(manifests)

        # Extract main service name
        name = self._extract_service_name(grouped_manifests)

        # Parse different resource types
        compute = self._parse_compute(grouped_manifests)
        container = self._parse_container(grouped_manifests)
        database = self._parse_database(grouped_manifests)
        network = self._parse_network(grouped_manifests)
        load_balancer = self._parse_load_balancer(grouped_manifests)
        observability = self._parse_observability(grouped_manifests)
        security = self._parse_security(grouped_manifests)
        volumes = self._parse_volumes(grouped_manifests)

        return UniversalInfrastructure(
            name=name,
            provider=CloudProvider.KUBERNETES,
            region="kubernetes-cluster",  # Generic for k8s
            compute=compute,
            container=container,
            database=database,
            network=network,
            load_balancer=load_balancer,
            observability=observability,
            security=security,
            volumes=volumes,
        )

    def _group_manifests_by_kind(
        self, manifests: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group manifests by their kind"""
        grouped = {}
        for manifest in manifests:
            kind = manifest.get("kind", "Unknown")
            if kind not in grouped:
                grouped[kind] = []
            grouped[kind].append(manifest)
        return grouped

    def _extract_service_name(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Extract the main service name from manifests"""
        # Priority: Ingress > Deployment > StatefulSet > Service
        for kind in ["Ingress", "Deployment", "StatefulSet", "Service"]:
            if kind in grouped_manifests:
                manifest = grouped_manifests[kind][0]
                return manifest.get("metadata", {}).get("name", "kubernetes-service")

        return "kubernetes-service"

    def _parse_compute(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> Optional[ComputeConfig]:
        """Parse compute resources from Deployments and StatefulSets"""
        for kind in ["Deployment", "StatefulSet"]:
            if kind in grouped_manifests:
                manifest = grouped_manifests[kind][0]
                spec = manifest.get("spec", {})

                replicas = spec.get("replicas", 1)

                # Try to extract resource requests from containers
                containers = self._get_containers_from_manifest(manifest)
                if containers:
                    container = containers[0]
                    resources = container.get("resources", {})

                    cpu_request = self._parse_cpu_resource(
                        resources.get("requests", {}).get("cpu", "100m")
                    )
                    memory_request = resources.get("requests", {}).get(
                        "memory", "128Mi"
                    )

                    return ComputeConfig(
                        instances=replicas, cpu=cpu_request, memory=memory_request
                    )

                # Fallback
                return ComputeConfig(instances=replicas)

        return None

    def _parse_container(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> Optional[ContainerConfig]:
        """Parse container configuration"""
        for kind in ["Deployment", "StatefulSet"]:
            if kind in grouped_manifests:
                manifest = grouped_manifests[kind][0]
                containers = self._get_containers_from_manifest(manifest)

                if containers:
                    container = containers[0]  # Primary container

                    # Basic container info
                    image = container.get("image", "")
                    ports = container.get("ports", [])
                    port = ports[0].get("containerPort", 80) if ports else 80

                    # Environment variables
                    env_vars = {}
                    secrets = {}

                    # Environment variables from ConfigMaps and Secrets (envFrom)
                    env_from_list = container.get("envFrom", [])
                    for env_from in env_from_list:
                        if isinstance(env_from, dict):
                            if "configMapRef" in env_from:
                                config_map_name = env_from["configMapRef"].get("name")
                                # Parse ConfigMap data
                                config_map_data = self._get_config_map_data(
                                    grouped_manifests, config_map_name
                                )
                                env_vars.update(config_map_data)
                            elif "secretRef" in env_from:
                                secret_name = env_from["secretRef"].get("name")
                                # Parse Secret data
                                secret_data = self._get_secret_data(
                                    grouped_manifests, secret_name
                                )
                                for key in secret_data.keys():
                                    secrets[key] = f"${{secrets.{key}}}"

                    # Direct environment variables
                    env_list = container.get("env", [])
                    for env in env_list:
                        if isinstance(env, dict) and "name" in env and "value" in env:
                            env_vars[env["name"]] = env["value"]

                    # Secrets (from env with secretKeyRef)
                    for env in env_list:
                        if isinstance(env, dict) and "name" in env:
                            env_name = env["name"]
                            if (
                                "valueFrom" in env
                                and "secretKeyRef" in env["valueFrom"]
                            ):
                                secrets[env_name] = f"${{secrets.{env_name}}}"

                    # Resources
                    resources = container.get("resources", {})
                    cpu_request = self._parse_cpu_resource(
                        resources.get("requests", {}).get("cpu", "100m")
                    )
                    memory_request = resources.get("requests", {}).get(
                        "memory", "128Mi"
                    )
                    cpu_limit = self._parse_cpu_resource(
                        resources.get("limits", {}).get("cpu", "200m")
                    )
                    memory_limit = resources.get("limits", {}).get("memory", "256Mi")

                    # Health checks
                    health_check_path = "/health"
                    liveness_probe = container.get("livenessProbe", {})
                    if "httpGet" in liveness_probe:
                        health_check_path = liveness_probe["httpGet"].get(
                            "path", "/health"
                        )

                    return ContainerConfig(
                        image=image,
                        port=port,
                        environment=env_vars,
                        secrets=secrets,
                        cpu_request=cpu_request,
                        memory_request=memory_request,
                        cpu_limit=cpu_limit,
                        memory_limit=memory_limit,
                        health_check_path=health_check_path,
                    )

        return None

    def _parse_database(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> Optional[DatabaseConfig]:
        """Parse database configuration from StatefulSets"""
        if "StatefulSet" in grouped_manifests:
            manifest = grouped_manifests["StatefulSet"][0]
            containers = self._get_containers_from_manifest(manifest)

            if containers:
                container = containers[0]
                image = container.get("image", "")

                # Detect database type from image
                db_type = DatabaseType.POSTGRESQL  # Default
                version = "15"  # Default

                if "postgres" in image.lower():
                    db_type = DatabaseType.POSTGRESQL
                    version = self._extract_version_from_image(image, "postgres")
                elif "mysql" in image.lower():
                    db_type = DatabaseType.MYSQL
                    version = self._extract_version_from_image(image, "mysql")
                elif "redis" in image.lower():
                    db_type = DatabaseType.REDIS
                    version = self._extract_version_from_image(image, "redis")

                return DatabaseConfig(type=db_type, version=version)

        return None

    def _parse_load_balancer(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> Optional[LoadBalancerConfig]:
        """Parse load balancer from Services and Ingress"""
        # Check for LoadBalancer type Service
        if "Service" in grouped_manifests:
            for service in grouped_manifests["Service"]:
                spec = service.get("spec", {})
                service_type = spec.get("type", "")

                if service_type == "LoadBalancer":
                    return LoadBalancerConfig(
                        enabled=True,
                        type="network",  # LoadBalancer service maps to network LB
                    )

        # Check for Ingress
        if "Ingress" in grouped_manifests:
            ingress = grouped_manifests["Ingress"][0]
            spec = ingress.get("spec", {})

            https = "tls" in spec
            certificate_domain = None
            if https and spec["tls"]:
                tls = spec["tls"][0]
                hosts = tls.get("hosts", [])
                if hosts:
                    certificate_domain = hosts[0]

            return LoadBalancerConfig(
                enabled=True,
                type="application",  # Ingress maps to application LB
                https=https,
                certificate_domain=certificate_domain,
            )

        return None

    def _parse_network(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> NetworkConfig:
        """Parse network configuration"""
        # Kubernetes networking is mostly handled by the cluster
        # We can extract some info from Services
        return NetworkConfig()

    def _parse_observability(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> ObservabilityConfig:
        """Parse observability configuration"""
        # Basic observability detection
        return ObservabilityConfig()

    def _parse_security(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> SecurityConfig:
        """Parse security configuration from Secrets"""
        secrets = {}

        if "Secret" in grouped_manifests:
            for secret in grouped_manifests["Secret"]:
                metadata = secret.get("metadata", {})
                metadata.get("name", "")
                data = secret.get("data", {})

                # Map secret keys
                for key in data.keys():
                    secrets[key] = f"${{secrets.{key}}}"

        return SecurityConfig(secrets=secrets)

    def _parse_volumes(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]]
    ) -> List[Volume]:
        """Parse persistent volumes"""
        volumes = []

        # Check StatefulSet volumeClaimTemplates
        if "StatefulSet" in grouped_manifests:
            manifest = grouped_manifests["StatefulSet"][0]
            spec = manifest.get("spec", {})
            volume_claim_templates = spec.get("volumeClaimTemplates", [])

            for vct in volume_claim_templates:
                metadata = vct.get("metadata") or {}
                name = metadata.get("name", "data")

                spec_claim = vct.get("spec", {})
                resources = spec_claim.get("resources", {})
                requests = resources.get("requests", {})
                storage = requests.get("storage", "10Gi")

                volumes.append(
                    Volume(
                        name=name,
                        size=storage,  # Keep original format (e.g., "50Gi")
                        mount_path="/var/lib/postgresql/data",  # More specific for databases
                    )
                )

        return volumes

    def _get_config_map_data(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]], config_map_name: str
    ) -> Dict[str, str]:
        """Get data from a ConfigMap"""
        if "ConfigMap" not in grouped_manifests:
            return {}

        for config_map in grouped_manifests["ConfigMap"]:
            metadata = config_map.get("metadata", {})
            name = metadata.get("name", "")
            if name == config_map_name:
                return config_map.get("data", {})

        return {}

    def _get_secret_data(
        self, grouped_manifests: Dict[str, List[Dict[str, Any]]], secret_name: str
    ) -> Dict[str, str]:
        """Get data from a Secret"""
        if "Secret" not in grouped_manifests:
            return {}

        for secret in grouped_manifests["Secret"]:
            metadata = secret.get("metadata", {})
            name = metadata.get("name", "")
            if name == secret_name:
                return secret.get("data", {})

        return {}

    def _get_containers_from_manifest(
        self, manifest: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract containers from a Deployment/StatefulSet manifest"""
        spec = manifest.get("spec", {})
        template = spec.get("template", {})
        pod_spec = template.get("spec", {})
        return pod_spec.get("containers", [])

    def _parse_cpu_resource(self, cpu_str: str) -> float:
        """Parse Kubernetes CPU resource string to float cores"""
        if not cpu_str:
            return 0.1

        cpu_str = cpu_str.lower()
        if cpu_str.endswith("m"):
            # Millicores
            return float(cpu_str[:-1]) / 1000
        else:
            # Cores
            return float(cpu_str)

    def _parse_storage_size(self, storage_str: str) -> int:
        """Parse Kubernetes storage size to GB"""
        if not storage_str:
            return 10

        storage_str = storage_str.lower()
        if storage_str.endswith("gi"):
            return int(storage_str[:-2])
        elif storage_str.endswith("g"):
            return int(storage_str[:-1])
        elif storage_str.endswith("mi"):
            return int(storage_str[:-2]) // 1024
        else:
            return 10  # Default

    def _extract_version_from_image(self, image: str, db_type: str) -> str:
        """Extract version from container image"""
        # Simple extraction - look for version after colon
        if ":" in image:
            version_part = image.split(":")[-1]
            # Remove any suffixes like -alpine
            version = version_part.split("-")[0]
            return version

        # Defaults
        if db_type == "postgres":
            return "15"
        elif db_type == "mysql":
            return "8.0"
        elif db_type == "redis":
            return "7.0"

        return "latest"
