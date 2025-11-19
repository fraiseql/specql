"""
Tests for Kubernetes Generator
"""

from src.infrastructure.generators.kubernetes_generator import KubernetesGenerator
from src.infrastructure.universal_infra_schema import (
    CloudProvider,
    ComputeConfig,
    ContainerConfig,
    DatabaseConfig,
    DatabaseType,
    LoadBalancerConfig,
    UniversalInfrastructure,
    Volume,
)


class TestKubernetesGenerator:
    """Test Kubernetes manifest generation"""

    def test_generate_simple_container(self):
        """Test generating manifests for a simple container"""
        infra = UniversalInfrastructure(
            name="test-app",
            provider=CloudProvider.KUBERNETES,
            container=ContainerConfig(
                image="nginx",
                tag="latest",
                port=80,
                environment={"ENV": "production"}
            ),
            compute=ComputeConfig(instances=2)
        )

        generator = KubernetesGenerator()
        result = generator.generate(infra)

        assert "apiVersion: apps/v1" in result
        assert "kind: Deployment" in result
        assert "name: test-app" in result
        assert "replicas: 2" in result
        assert "image: nginx:latest" in result
        assert "containerPort: 80" in result
        assert "name: ENV" in result
        assert 'value: "production"' in result

    def test_generate_with_database(self):
        """Test generating manifests with database"""
        infra = UniversalInfrastructure(
            name="api-server",
            provider=CloudProvider.KUBERNETES,
            container=ContainerConfig(
                image="python:3.9",
                port=8000,
                environment={"DATABASE_URL": "postgres://db:5432"}
            ),
            database=DatabaseConfig(
                type=DatabaseType.POSTGRESQL,
                version="15",
                storage="50GB"
            )
        )

        generator = KubernetesGenerator()
        result = generator.generate(infra)

        assert "apiVersion: apps/v1" in result
        assert "kind: StatefulSet" in result
        assert "name: api-server-db" in result
        assert "image: postgres:15" in result
        assert "containerPort: 5432" in result
        assert "name: api-server" in result  # Check for the main app deployment

    def test_generate_with_load_balancer(self):
        """Test generating manifests with load balancer"""
        infra = UniversalInfrastructure(
            name="web-app",
            provider=CloudProvider.KUBERNETES,
            container=ContainerConfig(
                image="nginx",
                port=80
            ),
            load_balancer=LoadBalancerConfig(
                enabled=True,
                https=True,
                certificate_domain="example.com"
            )
        )

        generator = KubernetesGenerator()
        result = generator.generate(infra)

        assert "apiVersion: networking.k8s.io/v1" in result
        assert "kind: Ingress" in result
        assert "host: example.com" in result
        assert "pathType: Prefix" in result
        assert "cert-manager.io/cluster-issuer" in result

    def test_generate_with_volumes(self):
        """Test generating manifests with persistent volumes"""
        infra = UniversalInfrastructure(
            name="data-app",
            provider=CloudProvider.KUBERNETES,
            container=ContainerConfig(
                image="busybox",
                port=8080,
                volumes=[
                    Volume(name="data", size="10GB", mount_path="/data")
                ]
            ),
            volumes=[
                Volume(name="data", size="10GB", mount_path="/data")
            ]
        )

        generator = KubernetesGenerator()
        result = generator.generate(infra)

        assert "apiVersion: v1" in result
        assert "kind: PersistentVolumeClaim" in result
        assert "name: data-pvc" in result
        assert "storage: 10GB" in result
        assert "mountPath: /data" in result
        assert "name: data" in result  # Check volume name
