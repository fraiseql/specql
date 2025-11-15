"""Tests for Terraform → Universal Infrastructure parser"""

import pytest
from src.infrastructure.parsers.terraform_parser import TerraformParser
from src.infrastructure.universal_infra_schema import CloudProvider, DatabaseType


class TestTerraformParser:
    """Test parsing Terraform to universal format"""

    @pytest.fixture
    def parser(self):
        return TerraformParser()

    def test_parse_simple_infrastructure(self, parser):
        """Test parsing basic Terraform configuration"""
        tf_content = """
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"

  tags = {
    Name = "web-server"
  }
}

resource "aws_db_instance" "postgres" {
  engine         = "postgres"
  engine_version = "15"
  instance_class = "db.t3.large"
  allocated_storage = 100

  backup_retention_period = 7
  multi_az = true
}
"""

        # Act
        infra = parser.parse(tf_content)

        # Assert
        assert infra.name == "web-server"
        assert infra.provider == CloudProvider.AWS

        # Compute
        assert infra.compute is not None
        assert infra.compute.instance_type == "t3.medium"

        # Database
        assert infra.database is not None
        assert infra.database.type == DatabaseType.POSTGRESQL
        assert infra.database.version == "15"
        assert infra.database.storage == "100GB"
        assert infra.database.multi_az is True

    def test_parse_with_load_balancer(self, parser):
        """Test parsing infrastructure with load balancer"""
        tf_content = """
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  count         = 3

  tags = {
    Name = "web-server-${count.index}"
  }
}

resource "aws_lb" "web_lb" {
  name               = "web-lb"
  internal           = false
  load_balancer_type = "application"

  enable_deletion_protection = true
}

resource "aws_lb_target_group" "web_tg" {
  name     = "web-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
}

resource "aws_autoscaling_group" "web_asg" {
  name                = "web-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  min_size            = 2
  max_size            = 10
  desired_capacity    = 3

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.web_tg.arn]
}
"""

        # Act
        infra = parser.parse(tf_content)

        # Assert
        assert infra.provider == CloudProvider.AWS
        assert infra.compute is not None
        assert infra.compute.instances == 3
        assert infra.compute.auto_scale is True
        assert infra.compute.min_instances == 2
        assert infra.compute.max_instances == 10

        assert infra.load_balancer is not None
        assert infra.load_balancer.enabled is True
        assert infra.load_balancer.type == "application"

    def test_parse_gcp_resources(self, parser):
        """Test parsing Google Cloud Platform resources"""
        tf_content = """
resource "google_compute_instance" "web" {
  name         = "web-server"
  machine_type = "n1-standard-1"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
  }

  tags = ["web"]
}

resource "google_sql_database_instance" "postgres" {
  name             = "postgres-instance"
  database_version = "POSTGRES_15"
  region           = "us-central1"

  settings {
    tier = "db-f1-micro"
    disk_size = 10
  }
}
"""

        # Act
        infra = parser.parse(tf_content)

        # Assert
        assert infra.provider == CloudProvider.GCP
        assert infra.region == "us-central1"

        # Compute
        assert infra.compute is not None
        assert infra.compute.instance_type == "n1-standard-1"

        # Database
        assert infra.database is not None
        assert infra.database.type == DatabaseType.POSTGRESQL
        assert infra.database.version == "15"

    def test_parse_kubernetes_manifests(self, parser):
        """Test parsing Kubernetes manifests (different from Terraform but testing parser flexibility)"""
        # Note: This would typically be handled by a separate KubernetesParser
        # but testing the main parser's ability to detect different formats
        k8s_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
"""

        # Act & Assert - should handle gracefully or delegate
        # This test ensures the parser doesn't crash on non-Terraform input
        with pytest.raises(ValueError, match="Not a valid Terraform configuration"):
            parser.parse(k8s_content)
