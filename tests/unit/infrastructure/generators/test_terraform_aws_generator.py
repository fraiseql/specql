"""Tests for Universal → Terraform AWS generator"""

import pytest
from src.infrastructure.generators.terraform_aws_generator import TerraformAWSGenerator
from src.infrastructure.universal_infra_schema import (
    CloudProvider,
    DatabaseType,
    UniversalInfrastructure,
    ComputeConfig,
    DatabaseConfig,
    ContainerConfig,
    LoadBalancerConfig,
    NetworkConfig,
)


class TestTerraformAWSGenerator:
    """Test generating Terraform for AWS"""

    @pytest.fixture
    def generator(self):
        return TerraformAWSGenerator()

    def test_generate_compute_only(self, generator):
        """Test generating compute resources only"""
        infra = UniversalInfrastructure(
            name="web-server",
            provider=CloudProvider.AWS,
            region="us-east-1",
            compute=ComputeConfig(
                instances=3,
                cpu=2,
                memory="4GB",
                auto_scale=True,
                min_instances=2,
                max_instances=10,
                cpu_target=70,
            ),
        )

        # Act
        tf_output = generator.generate(infra)

        # Assert
        assert 'resource "aws_launch_template" "web-server"' in tf_output
        assert 'resource "aws_autoscaling_group" "web-server"' in tf_output
        assert "min_size            = 2" in tf_output
        assert "max_size            = 10" in tf_output
        assert (
            "target_value = 70" in tf_output
        )  # cpu_target becomes target_value in policy

        # Should also generate basic networking
        assert 'resource "aws_vpc" "web-server"' in tf_output
        assert 'resource "aws_subnet" "public"' in tf_output
        assert 'resource "aws_security_group" "app"' in tf_output

    def test_generate_database_only(self, generator):
        """Test generating database resources only"""
        infra = UniversalInfrastructure(
            name="backend-db",
            provider=CloudProvider.AWS,
            region="us-east-1",
            database=DatabaseConfig(
                type=DatabaseType.POSTGRESQL,
                version="15",
                storage="100GB",
                multi_az=True,
                backup_retention_days=7,
            ),
        )

        # Act
        tf_output = generator.generate(infra)

        # Assert
        assert 'resource "aws_db_instance" "backend-db"' in tf_output
        assert 'engine         = "postgres"' in tf_output
        assert 'engine_version = "15"' in tf_output
        assert "allocated_storage     = 100" in tf_output
        assert "multi_az               = true" in tf_output
        assert "backup_retention_period = 7" in tf_output

    def test_generate_full_stack(self, generator):
        """Test generating complete infrastructure stack"""
        infra = UniversalInfrastructure(
            name="web-app",
            provider=CloudProvider.AWS,
            region="us-east-1",
            environment="production",
            compute=ComputeConfig(
                instances=2,
                cpu=1,
                memory="2GB",
                auto_scale=True,
                min_instances=2,
                max_instances=10,
            ),
            container=ContainerConfig(
                image="nginx:1.21", port=80, environment={"ENV": "production"}
            ),
            database=DatabaseConfig(
                type=DatabaseType.POSTGRESQL,
                version="15",
                storage="50GB",
                multi_az=True,
            ),
            load_balancer=LoadBalancerConfig(
                enabled=True, type="application", https=True
            ),
            network=NetworkConfig(
                vpc_cidr="10.0.0.0/16",
                public_subnets=["10.0.1.0/24", "10.0.2.0/24"],
                private_subnets=["10.0.10.0/24", "10.0.20.0/24"],
            ),
        )

        # Act
        tf_output = generator.generate(infra)

        # Assert basic structure
        assert "terraform {" in tf_output
        assert 'provider "aws"' in tf_output
        assert 'region = "us-east-1"' in tf_output

        # Compute resources
        assert "aws_launch_template" in tf_output
        assert "aws_autoscaling_group" in tf_output

        # Database
        assert "aws_db_instance" in tf_output
        assert 'engine         = "postgres"' in tf_output

        # Load balancer
        assert "aws_lb" in tf_output
        assert "aws_lb_target_group" in tf_output
        assert "aws_lb_listener" in tf_output

        # Networking
        assert "aws_vpc" in tf_output
        assert "aws_subnet" in tf_output
        assert "aws_security_group" in tf_output

        # Outputs
        assert 'output "load_balancer_dns"' in tf_output
        assert 'output "database_endpoint"' in tf_output

    def test_generate_with_container(self, generator):
        """Test generating with container configuration"""
        infra = UniversalInfrastructure(
            name="api-server",
            provider=CloudProvider.AWS,
            compute=ComputeConfig(instances=1),
            container=ContainerConfig(
                image="myapi:v1.0",
                tag="v1.0",
                port=8000,
                environment={"DEBUG": "false"},
                secrets={"DB_PASSWORD": "${secrets.db_password}"},
                cpu_limit=2.0,
                memory_limit="4GB",
            ),
        )

        # Act
        tf_output = generator.generate(infra)

        # Assert
        assert "docker run -d" in tf_output
        assert "-p 8000:8000" in tf_output
        assert "-e DEBUG=false" in tf_output
        assert "-e DB_PASSWORD=${secrets.db_password}" in tf_output
        assert "myapi:v1.0" in tf_output
