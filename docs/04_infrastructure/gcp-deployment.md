# GCP Deployment Guide

> **Deploy SpecQL backends to Google Cloud Platform with auto-generated Terraform**

## Overview

SpecQL generates production-ready GCP infrastructure using Terraform. Define your requirements in YAML, get Google Cloud resources with cost-efficiency, global scale, and managed services built-in.

**Think of it as**: Google's best practices, but declarative and automatic.

---

## Quick Start

### 1. Define Deployment

```yaml
# deployment.yaml
deployment:
  name: crm-backend
  cloud: gcp
  project: my-project-id
  region: us-central1
  environment: production

compute:
  instances: 2
  machine_type: e2-medium  # 2 vCPU, 4GB RAM
  auto_scale:
    enabled: true
    min: 2
    max: 10
    cpu_target: 0.7

database:
  type: postgresql
  version: "POSTGRES_15"
  tier: db-custom-2-8192  # 2 vCPU, 8GB RAM
  storage: 100GB
  high_availability: true
  backups:
    enabled: true
    retention_days: 7

network:
  vpc_name: crm-vpc
  load_balancer:
    type: https
    ssl_certificate: managed

monitoring:
  cloud_monitoring: true
  cloud_logging: true
  alerts:
    - cpu_high: "> 80% for 5 minutes"
    - memory_high: "> 80% for 5 minutes"
    - error_rate: "> 1% for 2 minutes"
```

### 2. Generate Terraform

```bash
# Generate Terraform configuration
specql deploy deployment.yaml --cloud gcp --format terraform --output terraform/gcp/

# Output structure
terraform/gcp/
├── main.tf                 # Main configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── vpc.tf                  # VPC networking
├── compute.tf              # Compute Engine instances
├── database.tf             # Cloud SQL PostgreSQL
├── load_balancer.tf        # HTTPS Load Balancer
├── iam.tf                  # IAM service accounts
├── monitoring.tf           # Cloud Monitoring
└── backend.tf              # Terraform state (GCS)
```

### 3. Deploy to GCP

```bash
cd terraform/gcp/

# Authenticate with GCP
gcloud auth application-default login

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply

# Get outputs
terraform output
```

---

## Deployment Patterns

### Pattern 1: Standard Web Application

**Best for**: Most web applications, REST APIs, SaaS platforms

```yaml
import:
  - patterns/infrastructure/gcp_web_app_standard.yaml

deployment:
  name: web-app
  project: my-project
  region: us-central1

# Override defaults
compute:
  machine_type: e2-standard-2  # 2 vCPU, 8GB RAM
database:
  tier: db-custom-4-16384      # 4 vCPU, 16GB RAM
```

**Generated Resources**:

**Compute**:
- Managed Instance Group (MIG) with autoscaling
- Instance Template with Container-Optimized OS
- Health checks (HTTP/HTTPS)
- Auto-healing policies

**Database**:
- Cloud SQL PostgreSQL 15 with high availability
- Automated backups (7-day retention)
- Private IP (VPC peering)
- Read replicas (optional)

**Networking**:
- Custom VPC with subnets
- Cloud NAT for egress traffic
- HTTPS Load Balancer with Google-managed SSL
- Cloud Armor (DDoS protection)

**Security**:
- Service accounts with least privilege
- Secret Manager for credentials
- VPC Service Controls (optional)
- Cloud KMS encryption

**Monitoring**:
- Cloud Monitoring dashboards
- Cloud Logging (application + system logs)
- Uptime checks
- Alerting policies

**Estimated Monthly Cost**: $400-500

| Resource | Monthly Cost |
|----------|--------------|
| Compute Engine (2x e2-medium) | $100 |
| Auto-scaling (avg 4 instances) | $200 |
| Cloud SQL HA (db-custom-2-8192, 100GB) | $170 |
| HTTPS Load Balancer | $18 |
| Cloud NAT | $45 |
| Egress traffic (1TB) | $12 |
| Cloud Monitoring/Logging | $5 |
| **Total** | **~$550/month** |

**Generated Terraform (excerpt)**:

```hcl
# Managed Instance Group with Autoscaling
resource "google_compute_instance_template" "app" {
  name_prefix  = "crm-backend-"
  machine_type = "e2-medium"

  disk {
    source_image = "cos-cloud/cos-stable"
    auto_delete  = true
    boot         = true
    disk_size_gb = 20
  }

  network_interface {
    network    = google_compute_network.vpc.id
    subnetwork = google_compute_subnetwork.app.id
  }

  metadata = {
    google-logging-enabled = "true"
    google-monitoring-enabled = "true"
  }

  service_account {
    email  = google_service_account.app.email
    scopes = ["cloud-platform"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_instance_group_manager" "app" {
  name               = "crm-backend-igm"
  base_instance_name = "crm-backend"
  zone               = "us-central1-a"

  version {
    instance_template = google_compute_instance_template.app.id
  }

  target_size = 2

  named_port {
    name = "http"
    port = 8080
  }

  auto_healing_policies {
    health_check      = google_compute_health_check.app.id
    initial_delay_sec = 300
  }
}

# Autoscaler
resource "google_compute_autoscaler" "app" {
  name   = "crm-backend-autoscaler"
  zone   = "us-central1-a"
  target = google_compute_instance_group_manager.app.id

  autoscaling_policy {
    min_replicas    = 2
    max_replicas    = 10
    cooldown_period = 60

    cpu_utilization {
      target = 0.7
    }
  }
}

# Cloud SQL PostgreSQL with HA
resource "google_sql_database_instance" "postgresql" {
  name             = "crm-backend-db"
  database_version = "POSTGRES_15"
  region           = "us-central1"

  settings {
    tier              = "db-custom-2-8192"
    availability_type = "REGIONAL"  # High availability
    disk_size         = 100
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
      transaction_log_retention_days = 7
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
    }
  }

  deletion_protection = true
}
```

---

### Pattern 2: Serverless with Cloud Run

**Best for**: Variable traffic, microservices, rapid scaling

```yaml
import:
  - patterns/infrastructure/gcp_serverless_cloudrun.yaml

deployment:
  name: serverless-api
  project: my-project
  region: us-central1

compute:
  type: cloud_run
  cpu: 2
  memory: 4Gi
  max_instances: 100
  min_instances: 0  # Scale to zero
  concurrency: 80

database:
  type: cloud_sql_serverless
  version: "POSTGRES_15"
  tier: db-f1-micro  # Smallest tier
  connections: 100
```

**Generated Resources**:

**Compute**:
- Cloud Run service (fully managed)
- Cloud Run Connector (VPC access)
- Container Registry/Artifact Registry

**Database**:
- Cloud SQL PostgreSQL with Cloud SQL Proxy
- Connection pooling (PgBouncer)
- Automatic pausing during idle

**Networking**:
- Global HTTPS Load Balancer
- Cloud CDN (optional)
- Google-managed SSL certificate

**Authentication**:
- Identity Platform (Firebase Auth)
- IAM service account authentication

**Estimated Monthly Cost**: $30-150 (pay per use)

| Resource | Monthly Cost (low) | Monthly Cost (high) |
|----------|-------------------|---------------------|
| Cloud Run (1M requests, 2s avg) | $12 | $60 |
| Cloud SQL (db-f1-micro, 10GB) | $15 | $15 |
| Load Balancer | $18 | $18 |
| Cloud CDN | $5 | $30 |
| Egress traffic | $5 | $20 |
| **Total** | **~$55/month** | **~$143/month** |

**Generated Terraform (excerpt)**:

```hcl
# Cloud Run Service
resource "google_cloud_run_service" "api" {
  name     = "crm-backend-api"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/crm-backend:latest"

        resources {
          limits = {
            cpu    = "2000m"
            memory = "4Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_url.secret_id
              key  = "latest"
            }
          }
        }
      }

      container_concurrency = 80
      timeout_seconds      = 300

      service_account_name = google_service_account.cloudrun.email
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"  # Scale to zero
        "autoscaling.knative.dev/maxScale" = "100"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.postgresql.connection_name
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.connector.id
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# Cloud SQL Connection
resource "google_vpc_access_connector" "connector" {
  name          = "cloudrun-connector"
  region        = "us-central1"
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.id
}
```

**Advantages**:
- ✅ **Scale to zero**: No cost during idle periods
- ✅ **Fast scaling**: 0 to 1000 instances in seconds
- ✅ **No infrastructure management**: Fully managed
- ✅ **Pay per use**: Only charged for actual usage

---

### Pattern 3: GKE Microservices

**Best for**: Kubernetes workloads, microservices, container orchestration

```yaml
import:
  - patterns/infrastructure/gcp_gke_microservices.yaml

deployment:
  name: microservices-platform
  project: my-project
  region: us-central1

compute:
  cluster_type: gke_standard  # or gke_autopilot
  node_pools:
    - name: app-pool
      machine_type: e2-standard-4
      node_count: 3
      auto_scale:
        min: 3
        max: 10
    - name: spot-pool
      machine_type: e2-standard-4
      node_count: 0
      auto_scale:
        min: 0
        max: 20
      spot: true  # Preemptible VMs (70% cheaper)

database:
  type: cloud_sql
  tier: db-custom-4-16384
  replicas: 2

service_mesh:
  istio: true
  monitoring: true
```

**Generated Resources**:

**Compute**:
- GKE cluster (Standard or Autopilot)
- Node pools with autoscaling
- Cluster autoscaler
- Workload Identity

**Database**:
- Cloud SQL PostgreSQL StatefulSet
- Cloud SQL Proxy sidecar
- Persistent volumes (SSD)

**Service Mesh**:
- Istio service mesh (optional)
- Envoy proxies
- Traffic management
- mTLS between services

**Networking**:
- VPC-native cluster
- Private GKE cluster (no public IPs)
- Ingress with Google-managed SSL
- Network policies

**Monitoring**:
- GKE monitoring (Prometheus-based)
- Cloud Trace (distributed tracing)
- Cloud Profiler

**Estimated Monthly Cost**: $300-600

| Resource | Monthly Cost |
|----------|--------------|
| GKE cluster (management) | $75 |
| Node pool (3x e2-standard-4) | $240 |
| Cloud SQL (db-custom-4-16384) | $350 |
| Persistent disks (300GB SSD) | $60 |
| Load Balancer | $18 |
| **Total** | **~$743/month** |

**GKE Autopilot** (simpler, more cost-effective):
```yaml
compute:
  cluster_type: gke_autopilot  # Fully managed nodes

# No node pools to manage!
# GKE automatically provisions nodes based on workload
```

**Autopilot Cost**: Pay only for pods (not nodes) = ~30% cheaper

---

### Pattern 4: Multi-Region with Cloud Spanner

**Best for**: Global applications, multi-region data, 99.999% SLA

```yaml
import:
  - patterns/infrastructure/gcp_multi_region.yaml

deployment:
  name: global-platform
  project: my-project
  regions:
    - us-central1
    - europe-west1
    - asia-southeast1

compute:
  type: cloud_run  # Serverless in all regions
  regions: all
  cpu: 2
  memory: 4Gi

database:
  type: cloud_spanner
  instance_config: nam-eur-asia1  # Multi-region
  processing_units: 1000  # 100 PU minimum
  replicas: 3

cdn:
  cloud_cdn: true
  cache_mode: CACHE_ALL_STATIC
```

**Generated Resources**:

**Compute** (per region):
- Cloud Run services with global load balancing
- Automatic traffic distribution
- Low-latency routing

**Database**:
- Cloud Spanner multi-region instance
- 99.999% availability SLA
- Automatic replication across regions
- Strong consistency globally

**Networking**:
- Global HTTPS Load Balancer
- Cloud CDN at edge locations
- Cloud Armor (DDoS protection)

**Estimated Monthly Cost**: $2,000-3,000

| Resource | Monthly Cost |
|----------|--------------|
| Cloud Run (3 regions) | $180 |
| Cloud Spanner (1000 PU) | $2,100 |
| Global Load Balancer | $18 |
| Cloud CDN | $50 |
| Egress traffic (10TB) | $120 |
| **Total** | **~$2,468/month** |

**Note**: Cloud Spanner is expensive but provides unmatched global consistency.

**Alternative** (cheaper multi-region):
```yaml
database:
  type: cloud_sql
  replication: cross_region
  primary_region: us-central1
  read_replicas:
    - europe-west1
    - asia-southeast1
```

**Cost**: ~$600/month (vs $2,100 for Spanner)

---

## GCP Services Deep Dive

### Compute Engine

**Machine Types** (E2 series - cost-optimized):

| Type | vCPU | RAM | Use Case | Monthly Cost |
|------|------|-----|----------|--------------|
| e2-micro | 2 shared | 1GB | Dev/test | $6 |
| e2-small | 2 shared | 2GB | Staging | $12 |
| e2-medium | 2 | 4GB | **Standard** | $24 |
| e2-standard-2 | 2 | 8GB | Production | $49 |
| e2-standard-4 | 4 | 16GB | High-performance | $97 |

**N2 series** (performance-optimized):
| Type | vCPU | RAM | Monthly Cost |
|------|------|-----|--------------|
| n2-standard-2 | 2 | 8GB | $70 |
| n2-standard-4 | 4 | 16GB | $140 |

**Preemptible VMs** (70-80% discount):
```hcl
resource "google_compute_instance_template" "preemptible" {
  scheduling {
    preemptible       = true
    automatic_restart = false
  }
}
```

---

### Cloud SQL PostgreSQL

**Tiers** (custom configurations):

| Tier | vCPU | RAM | Use Case | Monthly Cost (HA) |
|------|------|-----|----------|-------------------|
| db-f1-micro | 1 shared | 0.6GB | Dev/test | $15 |
| db-g1-small | 1 shared | 1.7GB | Staging | $40 |
| db-custom-2-8192 | 2 | 8GB | **Standard** | $170 |
| db-custom-4-16384 | 4 | 16GB | Production | $340 |
| db-custom-8-32768 | 8 | 32GB | High-performance | $680 |

**High Availability**:
```hcl
resource "google_sql_database_instance" "postgresql" {
  settings {
    availability_type = "REGIONAL"  # Automatic failover

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true  # Transaction log backups
      transaction_log_retention_days = 7
    }
  }
}
```

**Read Replicas** (for read scaling):
```hcl
resource "google_sql_database_instance" "read_replica" {
  name                 = "crm-backend-db-replica"
  master_instance_name = google_sql_database_instance.postgresql.name
  region               = "us-west1"  # Different region

  replica_configuration {
    failover_target = true  # Promote to master if primary fails
  }

  settings {
    tier = "db-custom-2-8192"
  }
}
```

---

### HTTPS Load Balancer

**Features**:
- Global anycast IP (single IP, worldwide)
- Automatic SSL certificate management
- Cloud CDN integration
- Cloud Armor (WAF/DDoS)
- URL maps for path-based routing

**Configuration**:

```hcl
# Global HTTPS Load Balancer
resource "google_compute_global_forwarding_rule" "https" {
  name       = "crm-backend-https-lb"
  target     = google_compute_target_https_proxy.default.id
  port_range = "443"
  ip_address = google_compute_global_address.default.address
}

resource "google_compute_target_https_proxy" "default" {
  name             = "crm-backend-https-proxy"
  url_map          = google_compute_url_map.default.id
  ssl_certificates = [google_compute_managed_ssl_certificate.default.id]
}

# Google-managed SSL certificate
resource "google_compute_managed_ssl_certificate" "default" {
  name = "crm-backend-cert"

  managed {
    domains = ["api.example.com"]
  }
}

# URL Map (routing)
resource "google_compute_url_map" "default" {
  name            = "crm-backend-url-map"
  default_service = google_compute_backend_service.app.id

  host_rule {
    hosts        = ["api.example.com"]
    path_matcher = "allpaths"
  }

  path_matcher {
    name            = "allpaths"
    default_service = google_compute_backend_service.app.id

    path_rule {
      paths   = ["/api/v2/*"]
      service = google_compute_backend_service.api_v2.id
    }
  }
}

# Backend Service
resource "google_compute_backend_service" "app" {
  name                  = "crm-backend-service"
  protocol              = "HTTP"
  port_name             = "http"
  timeout_sec           = 30
  enable_cdn            = true
  health_checks         = [google_compute_health_check.app.id]
  load_balancing_scheme = "EXTERNAL"

  backend {
    group           = google_compute_instance_group_manager.app.instance_group
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }

  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    default_ttl       = 3600
    client_ttl        = 3600
    max_ttl           = 86400
    negative_caching  = true
    serve_while_stale = 86400
  }
}
```

**Cost**: $18/month + $0.008-0.010/GB egress

---

### Cloud Monitoring & Logging

**Dashboards**:

```hcl
resource "google_monitoring_dashboard" "main" {
  dashboard_json = jsonencode({
    displayName = "CRM Backend Overview"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "CPU Utilization"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"gce_instance\" metric.type=\"compute.googleapis.com/instance/cpu/utilization\""
                  }
                }
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "Database Connections"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloudsql_database\" metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\""
                  }
                }
              }]
            }
          }
        }
      ]
    }
  })
}
```

**Alerts**:

```hcl
resource "google_monitoring_alert_policy" "cpu_high" {
  display_name = "High CPU Utilization"
  combiner     = "OR"

  conditions {
    display_name = "CPU > 80%"
    condition_threshold {
      filter          = "resource.type=\"gce_instance\" metric.type=\"compute.googleapis.com/instance/cpu/utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}
```

---

## Cost Optimization

### Committed Use Discounts (CUD)

**Savings**: 25-57% vs on-demand

```bash
# 1-year commitment
gcloud compute commitments create crm-backend-commitment \
  --region=us-central1 \
  --resources=vcpu=16,memory=64 \
  --plan=12-month

# Automatic application to matching VMs
```

**Example**:
- On-demand: $0.033/hour (e2-standard-4) = $24/month
- 1-year CUD: $0.017/hour = $12/month (50% savings)
- 3-year CUD: $0.014/hour = $10/month (58% savings)

### Sustained Use Discounts

**Automatic**: 20-30% discount for running VMs > 25% of month

### Preemptible VMs

**Savings**: 70-80% vs on-demand

```hcl
resource "google_compute_instance_template" "spot" {
  scheduling {
    preemptible       = true
    automatic_restart = false
    on_host_maintenance = "TERMINATE"
  }
}
```

**Use for**: Batch processing, CI/CD, dev/test environments

### Cloud SQL Cost Optimization

```hcl
# Auto-scale storage
resource "google_sql_database_instance" "postgresql" {
  settings {
    disk_autoresize       = true
    disk_autoresize_limit = 500  # GB max
  }
}

# Deletion protection
resource "google_sql_database_instance" "postgresql" {
  deletion_protection = true  # Prevent accidental deletion
}
```

---

## Security Best Practices

### VPC Service Controls

```hcl
resource "google_access_context_manager_service_perimeter" "secure" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/crm_backend"
  title  = "CRM Backend Perimeter"

  status {
    restricted_services = [
      "storage.googleapis.com",
      "sqladmin.googleapis.com"
    ]

    vpc_accessible_services {
      enable_restriction = true
      allowed_services = [
        "storage.googleapis.com"
      ]
    }
  }
}
```

### Secret Manager

```hcl
resource "google_secret_manager_secret" "db_password" {
  secret_id = "crm-backend-db-password"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db.result
}

# Grant access to service account
resource "google_secret_manager_secret_iam_member" "app_access" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}
```

### Workload Identity (GKE)

```hcl
resource "google_service_account" "gke_workload" {
  account_id   = "crm-backend-gke"
  display_name = "CRM Backend GKE Service Account"
}

resource "google_service_account_iam_binding" "workload_identity" {
  service_account_id = google_service_account.gke_workload.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[default/crm-backend]"
  ]
}
```

---

## Deployment Workflow

### CI/CD with Cloud Build

```yaml
# cloudbuild.yaml
steps:
  # Build container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/crm-backend:$COMMIT_SHA', '.']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/crm-backend:$COMMIT_SHA']

  # Generate Terraform
  - name: 'hashicorp/terraform:latest'
    entrypoint: 'sh'
    args:
      - '-c'
      - |
        pip install specql
        specql deploy deployment.yaml --cloud gcp --output terraform/

  # Deploy infrastructure
  - name: 'hashicorp/terraform:latest'
    dir: 'terraform'
    args: ['apply', '-auto-approve']

images:
  - 'gcr.io/$PROJECT_ID/crm-backend:$COMMIT_SHA'
```

---

## Next Steps

- [AWS Deployment](aws-deployment.md) - Deploy to Amazon Web Services
- [Azure Deployment](azure-deployment.md) - Deploy to Microsoft Azure
- [Kubernetes Guide](kubernetes-deployment.md) - Container orchestration
- [Cost Optimization](cost-optimization.md) - Multi-cloud cost comparison

---

**GCP deployment with SpecQL means leveraging Google's infrastructure at scale. From YAML to production-ready GCP resources with cost-efficiency and managed services built-in.**

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Coverage**: Complete GCP deployment guide (Terraform, Cloud Run, GKE, Cloud SQL, cost optimization)
