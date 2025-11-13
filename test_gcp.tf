

# ============================================================================
# Provider Configuration
# ============================================================================
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = "us-east1"
}

# ============================================================================
# Compute Resources (Instance Group Manager)
# ============================================================================

# Instance Template
resource "google_compute_instance_template" "test-app" {
  name_prefix  = "test-app-"
  machine_type = "e2-micro"
  metadata_startup_script = <<-EOF
    #!/bin/bash
    # Install Docker
    apt-get update
    apt-get install -y docker.io

    # Run container
    docker run -d \
      -p 80:80 \
      -e ENV=production \
      nginx:latest
  EOF

  disk {
    source_image = "cos-cloud/cos-stable"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    network = google_compute_network.test-app.name
    subnetwork = google_compute_subnetwork.public.name
  }
  tags = ["test-app-backend"]

  labels = {
    name = "test-app"
  }
}

# Instance Group Manager
resource "google_compute_instance_group_manager" "test-app" {
  name = "test-app-igm"
  zone = "us-east1-a"

  version {
    instance_template = google_compute_instance_template.test-app.id
    name              = "primary"
  }

  base_instance_name = "test-app"
  target_size        = 2
  named_port {
    name = "http"
    port = 80
  }
}

# Auto Scaling
resource "google_compute_autoscaler" "test-app" {
  name   = "test-app-autoscaler"
  zone   = "us-east1-a"
  target = google_compute_instance_group_manager.test-app.id

  autoscaling_policy {
    max_replicas    = 5
    min_replicas    = 1
    cooldown_period = 60

    cpu_utilization {
      target = 0.7
    }
  }
}

# ============================================================================
# Database (Cloud SQL)
# ============================================================================

resource "google_sql_database_instance" "test-app" {
  name             = "test-app-db"
  database_version = "POSTGRES_15"
  region           = "us-east1"

  settings {
    tier = "db-f1-micro"

    disk_size = 50
    disk_type = "PD_SSD"

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    maintenance_window {
      day  = 7  # Sunday
      hour = 3
    }

    ip_configuration {
      ipv4_enabled = false
      authorized_networks {
        name  = "allow-app"
        value = "10.0.0.0/16"
      }
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "test-app" {
  name     = "test_app"
  instance = google_sql_database_instance.test-app.name
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "google_sql_user" "test-app" {
  name     = "admin"
  instance = google_sql_database_instance.test-app.name
  password = random_password.db_password.result
}

# Store password in Secret Manager
resource "google_secret_manager_secret" "test-app" {
  secret_id = "test-app-db-password"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "test-app" {
  secret = google_secret_manager_secret.test-app.id
  secret_data = random_password.db_password.result
}

# ============================================================================
# Load Balancer
# ============================================================================

resource "google_compute_global_address" "test-app" {
  name = "test-app-lb-ip"
}

resource "google_compute_backend_service" "test-app" {
  name        = "test-app-backend"
  protocol    = "HTTP"
  port_name   = "http"
  timeout_sec = 10

  backend {
    group = google_compute_instance_group_manager.test-app.instance_group
  }

  health_checks = [google_compute_http_health_check.test-app.id]
}

resource "google_compute_http_health_check" "test-app" {
  name               = "test-app-health-check"
  request_path       = "/health"
  check_interval_sec = 30
  timeout_sec        = 5
  healthy_threshold  = 2
  unhealthy_threshold = 3
}

resource "google_compute_url_map" "test-app" {
  name            = "test-app-url-map"
  default_service = google_compute_backend_service.test-app.id
}

resource "google_compute_target_http_proxy" "test-app" {
  name    = "test-app-http-proxy"
  url_map = google_compute_url_map.test-app.id
}

resource "google_compute_global_forwarding_rule" "test-app" {
  name       = "test-app-forwarding-rule"
  target     = google_compute_target_http_proxy.test-app.id
  port_range = "80"
  ip_address = google_compute_global_address.test-app.address
}

# ============================================================================
# Networking (VPC, Subnets, etc.)
# ============================================================================

resource "google_compute_network" "test-app" {
  name                    = "test-app-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "public" {
  name          = "test-app-public"
  ip_cidr_range = "10.0.1.0/24"
  region        = "us-east1"
  network       = google_compute_network.test-app.id
}

resource "google_compute_subnetwork" "private" {
  name          = "test-app-private"
  ip_cidr_range = "10.0.10.0/24"
  region        = "us-east1"
  network       = google_compute_network.test-app.id
}

resource "google_compute_router" "test-app" {
  name    = "test-app-router"
  region  = "us-east1"
  network = google_compute_network.test-app.id
}
resource "google_compute_router_nat" "test-app" {
  name                               = "test-app-nat"
  router                             = google_compute_router.test-app.name
  region                             = "us-east1"
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# Firewall Rules
resource "google_compute_firewall" "test-app-allow-http" {
  name    = "test-app-allow-http"
  network = google_compute_network.test-app.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["test-app-backend"]
}
resource "google_compute_firewall" "test-app-allow-db" {
  name    = "test-app-allow-db"
  network = google_compute_network.test-app.name

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }

  source_ranges = ["10.0.0.0/16"]
  target_tags   = ["test-app-db"]
}

# ============================================================================
# Variables
# ============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

# ============================================================================
# Outputs
# ============================================================================
output "load_balancer_ip" {
  value = google_compute_global_address.test-app.address
}
output "database_connection_name" {
  value = google_sql_database_instance.test-app.connection_name
}

output "database_password_secret" {
  value = google_secret_manager_secret.test-app.name
}

output "vpc_id" {
  value = google_compute_network.test-app.id
}