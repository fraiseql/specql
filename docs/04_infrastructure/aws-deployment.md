# AWS Deployment Guide

> **Deploy SpecQL backends to AWS with auto-generated Terraform and CloudFormation**

## Overview

SpecQL generates production-ready AWS infrastructure using Terraform or CloudFormation. Define your requirements in YAML, get battle-tested AWS resources with security, scalability, and cost optimization built-in.

**Think of it as**: AWS Well-Architected Framework, but declarative and automatic.

---

## Quick Start

### 1. Define Deployment

```yaml
# deployment.yaml
deployment:
  name: crm-backend
  cloud: aws
  region: us-east-1
  environment: production

compute:
  instances: 2
  instance_type: t3.medium  # 2 vCPU, 4GB RAM
  auto_scale:
    enabled: true
    min: 2
    max: 10
    cpu_target: 70

database:
  type: postgresql
  version: "15"
  instance_class: db.t3.medium
  storage: 100GB
  multi_az: true
  backups:
    retention_days: 7
    window: "03:00-04:00"

network:
  vpc_cidr: 10.0.0.0/16
  availability_zones: 3
  load_balancer:
    type: application
    https: true
    certificate_arn: ${ACM_CERT_ARN}

monitoring:
  cloudwatch:
    enabled: true
    retention_days: 7
  alarms:
    - cpu_high: "> 80% for 5 minutes"
    - memory_high: "> 80% for 5 minutes"
    - error_rate: "> 1% for 2 minutes"
```

### 2. Generate Terraform

```bash
# Generate Terraform configuration
specql deploy deployment.yaml --format terraform --output terraform/aws/

# Output structure
terraform/aws/
├── main.tf                 # Main configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── vpc.tf                  # VPC networking
├── compute.tf              # EC2 Auto Scaling
├── database.tf             # RDS PostgreSQL
├── load_balancer.tf        # ALB configuration
├── security_groups.tf      # Security rules
├── iam.tf                  # IAM roles and policies
├── cloudwatch.tf           # Monitoring and logs
└── backend.tf              # Terraform state backend
```

### 3. Deploy to AWS

```bash
cd terraform/aws/

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply

# Get outputs (database endpoint, load balancer DNS, etc.)
terraform output
```

---

## Deployment Patterns

### Pattern 1: Standard Web Application

**Best for**: Most web applications, REST APIs, SaaS platforms

```yaml
import:
  - patterns/infrastructure/aws_web_app_standard.yaml

deployment:
  name: web-app
  region: us-east-1

# Override defaults
compute:
  instance_type: t3.large  # Upgrade from default t3.medium
database:
  storage: 200GB           # Increase from default 100GB
```

**Generated Resources**:

**Compute**:
- EC2 Launch Template with latest Amazon Linux 2
- Auto Scaling Group (2-10 instances)
- Target Tracking Scaling Policy (CPU-based)

**Database**:
- RDS PostgreSQL 15 Multi-AZ
- Automated backups (7-day retention)
- Parameter group optimized for production
- Security group (PostgreSQL port 5432)

**Networking**:
- VPC with public/private subnets in 3 AZs
- Internet Gateway
- NAT Gateways (one per AZ)
- Route tables
- Application Load Balancer
- ACM certificate (HTTPS)

**Security**:
- Security groups with least privilege
- IAM roles for EC2 (SSM access, CloudWatch)
- Secrets Manager for database credentials
- KMS encryption for RDS

**Monitoring**:
- CloudWatch log groups
- CloudWatch metrics (CPU, memory, disk, network)
- CloudWatch alarms (CPU, memory, error rate)
- SNS topic for alerts

**Estimated Monthly Cost**: $500-600

| Resource | Monthly Cost |
|----------|--------------|
| EC2 (2x t3.medium) | $120 |
| Auto-scaling (avg 4 instances) | $240 |
| RDS Multi-AZ (db.t3.medium, 100GB) | $90 |
| Application Load Balancer | $25 |
| NAT Gateways (3x) | $100 |
| Data transfer | $20 |
| CloudWatch | $5 |
| **Total** | **~$600/month** |

**Generated Terraform (excerpt)**:

```hcl
# Auto Scaling Group
resource "aws_autoscaling_group" "app" {
  name                = "crm-backend-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = 2
  max_size         = 10
  desired_capacity = 2

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "crm-backend-instance"
    propagate_at_launch = true
  }
}

# Target Tracking Scaling Policy
resource "aws_autoscaling_policy" "cpu_target" {
  name                   = "cpu-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# RDS PostgreSQL Multi-AZ
resource "aws_db_instance" "postgresql" {
  identifier     = "crm-backend-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.rds.arn

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true

  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "crm-backend-db-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
}
```

---

### Pattern 2: Serverless API

**Best for**: Variable traffic, event-driven systems, cost optimization

```yaml
import:
  - patterns/infrastructure/aws_serverless_api.yaml

deployment:
  name: serverless-api
  region: us-west-2

compute:
  runtime: nodejs20.x
  memory: 1024MB
  timeout: 30
  reserved_concurrency: 100

database:
  type: aurora_serverless
  version: "15.4"
  min_capacity: 0.5  # ACU
  max_capacity: 4    # ACU
  auto_pause: true
  auto_pause_delay: 300  # seconds
```

**Generated Resources**:

**Compute**:
- Lambda functions (API handlers)
- Lambda layers (shared dependencies)
- API Gateway REST API
- API Gateway custom domain
- CloudFront distribution (edge caching)

**Database**:
- Aurora Serverless v2 PostgreSQL
- Auto-scaling (0.5-4 ACU)
- Auto-pause after 5 minutes idle
- Secrets Manager for credentials

**Authentication**:
- Cognito User Pool
- Cognito Identity Pool
- JWT authorizer for API Gateway

**Storage**:
- S3 bucket for file uploads
- S3 lifecycle policies
- CloudFront for CDN

**Monitoring**:
- Lambda CloudWatch Logs
- X-Ray tracing
- API Gateway access logs
- Custom CloudWatch metrics

**Estimated Monthly Cost**: $50-200 (pay per use)

| Resource | Monthly Cost (low traffic) | Monthly Cost (high traffic) |
|----------|----------------------------|----------------------------|
| Lambda (1M requests) | $0.20 | $20 |
| API Gateway | $3.50 | $35 |
| Aurora Serverless (avg 1 ACU) | $30 | $120 |
| CloudFront | $5 | $20 |
| Cognito | $0 (first 50k MAU free) | $5 |
| **Total** | **~$40/month** | **~$200/month** |

**Cost Advantage**: Scales to zero during idle periods!

---

### Pattern 3: High-Performance Multi-Region

**Best for**: Global applications, low-latency requirements, high availability

```yaml
import:
  - patterns/infrastructure/aws_multi_region.yaml

deployment:
  name: global-api
  regions:
    primary: us-east-1
    secondary:
      - eu-west-1
      - ap-southeast-1

compute:
  instance_type: c6g.large  # ARM Graviton2 (better price/performance)
  instances: 3
  auto_scale:
    max: 20

database:
  type: aurora_global
  engine: postgresql
  version: "15.4"
  instance_class: db.r6g.large
  replicas_per_region: 2

cache:
  type: elasticache_redis
  node_type: cache.t4g.micro
  cluster_mode: enabled
  replicas: 2

cdn:
  cloudfront:
    enabled: true
    geo_restrictions: none
    price_class: PriceClass_All
```

**Generated Resources (per region)**:

**Compute**:
- EC2 Auto Scaling with ARM Graviton2 instances
- Application Load Balancer
- Cross-region VPC peering

**Database**:
- Aurora Global Database (writer in us-east-1)
- Aurora read replicas in each region
- 1-second cross-region replication

**Cache**:
- ElastiCache Redis cluster mode
- Automatic failover
- Multi-AZ replication

**Networking**:
- Route53 latency-based routing
- CloudFront edge locations worldwide
- AWS Global Accelerator (optional)

**Estimated Monthly Cost**: $1,500-2,500/region

---

### Pattern 4: Cost-Optimized Staging

**Best for**: Development, staging, testing environments

```yaml
import:
  - patterns/infrastructure/aws_staging.yaml

deployment:
  name: staging-env
  region: us-east-1
  environment: staging

compute:
  instance_type: t3.micro  # Smallest instance
  instances: 1             # No auto-scaling
  spot_instances: true     # 70% cost savings

database:
  instance_class: db.t3.micro
  storage: 20GB
  multi_az: false          # Single AZ
  backups:
    retention_days: 1      # Minimal retention

network:
  load_balancer:
    type: application
    https: false           # HTTP only (save $)
```

**Cost Savings**:
- Spot instances: 70% off on-demand
- No Multi-AZ: 50% database cost reduction
- Smaller instances: 80% cost reduction
- Minimal backups: 90% backup storage savings

**Estimated Monthly Cost**: $50-80 (vs $500 for production)

---

## AWS Services Deep Dive

### EC2 Auto Scaling

**Instance Types** (recommended):

| Type | vCPU | RAM | Use Case | Monthly Cost |
|------|------|-----|----------|--------------|
| t3.micro | 2 | 1GB | Staging/dev | $7 |
| t3.small | 2 | 2GB | Light workloads | $15 |
| t3.medium | 2 | 4GB | **Standard** | $30 |
| t3.large | 2 | 8GB | Medium workloads | $60 |
| c6g.large | 2 | 4GB | CPU-intensive (ARM) | $50 |
| r6g.large | 2 | 16GB | Memory-intensive (ARM) | $85 |

**Scaling Policies**:

```hcl
# CPU-based scaling
resource "aws_autoscaling_policy" "cpu" {
  name                   = "cpu-target-70"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Request count scaling
resource "aws_autoscaling_policy" "request_count" {
  name                   = "request-count-target-1000"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.app.arn_suffix}/${aws_lb_target_group.app.arn_suffix}"
    }
    target_value = 1000.0
  }
}
```

---

### RDS PostgreSQL

**Instance Classes** (recommended):

| Class | vCPU | RAM | Storage IOPS | Use Case | Monthly Cost (Multi-AZ) |
|-------|------|-----|--------------|----------|-------------------------|
| db.t3.micro | 2 | 1GB | Baseline | Dev/test | $30 |
| db.t3.small | 2 | 2GB | Baseline | Staging | $55 |
| db.t3.medium | 2 | 4GB | Baseline | **Standard** | $90 |
| db.t3.large | 2 | 8GB | Baseline | Production | $180 |
| db.m6g.large | 2 | 8GB | 12,000 | High-performance | $230 |
| db.r6g.large | 2 | 16GB | 12,000 | Memory-intensive | $290 |

**High Availability Configuration**:

```hcl
resource "aws_db_instance" "postgresql" {
  # Multi-AZ for automatic failover
  multi_az = true

  # Automated backups
  backup_retention_period = 7
  backup_window          = "03:00-04:00"  # Low-traffic window

  # Read replicas (optional)
  replicate_source_db = null  # Set to primary DB ARN for replica

  # Performance Insights
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  # Enhanced Monitoring
  monitoring_interval = 60  # seconds
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  # Encryption
  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds.arn

  # Network isolation
  publicly_accessible = false
  db_subnet_group_name = aws_db_subnet_group.private.name
}
```

**Aurora Serverless v2** (for variable workloads):

```hcl
resource "aws_rds_cluster" "aurora_serverless" {
  engine         = "aurora-postgresql"
  engine_mode    = "provisioned"  # v2 uses provisioned mode
  engine_version = "15.4"

  database_name   = "appdb"
  master_username = "dbadmin"
  master_password = random_password.db.result

  # Serverless v2 scaling
  serverlessv2_scaling_configuration {
    min_capacity = 0.5  # ACU
    max_capacity = 4    # ACU
  }

  # Auto-pause (save costs during idle)
  # Note: Auto-pause not available in v2, use min_capacity = 0.5

  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"

  db_subnet_group_name   = aws_db_subnet_group.private.name
  vpc_security_group_ids = [aws_security_group.database.id]
}

resource "aws_rds_cluster_instance" "aurora_serverless" {
  cluster_identifier = aws_rds_cluster.aurora_serverless.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.aurora_serverless.engine
  engine_version     = aws_rds_cluster.aurora_serverless.engine_version
}
```

**Cost**: $0.12/hour per ACU (~$87/month for 1 ACU continuously) + storage

---

### Application Load Balancer

**Features**:
- HTTPS termination with ACM certificates
- Path-based routing
- Host-based routing
- WebSocket support
- HTTP/2 support
- Sticky sessions

**Configuration**:

```hcl
resource "aws_lb" "app" {
  name               = "crm-backend-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    enabled = true
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# Redirect HTTP to HTTPS
resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.app.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
```

**Cost**: $23/month base + $0.008/LCU-hour (LCU = Load Balancer Capacity Unit)

---

### VPC Networking

**Network Architecture**:

```
┌─────────────────────────────────────────────────────────┐
│ VPC (10.0.0.0/16)                                       │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ AZ us-east-1a│  │ AZ us-east-1b│  │ AZ us-east-1c│  │
│  │              │  │              │  │              │  │
│  │ Public       │  │ Public       │  │ Public       │  │
│  │ 10.0.1.0/24  │  │ 10.0.2.0/24  │  │ 10.0.3.0/24  │  │
│  │ - ALB        │  │ - ALB        │  │ - ALB        │  │
│  │ - NAT GW     │  │ - NAT GW     │  │ - NAT GW     │  │
│  │              │  │              │  │              │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  │
│  │              │  │              │  │              │  │
│  │ Private App  │  │ Private App  │  │ Private App  │  │
│  │ 10.0.11.0/24 │  │ 10.0.12.0/24 │  │ 10.0.13.0/24 │  │
│  │ - EC2        │  │ - EC2        │  │ - EC2        │  │
│  │              │  │              │  │              │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  │
│  │              │  │              │  │              │  │
│  │ Private DB   │  │ Private DB   │  │ Private DB   │  │
│  │ 10.0.21.0/24 │  │ 10.0.22.0/24 │  │ 10.0.23.0/24 │  │
│  │ - RDS        │  │ - RDS        │  │ - RDS        │  │
│  │              │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  Internet Gateway         ↔  Public Subnets            │
│  NAT Gateways (3x)        ↔  Private Subnets           │
│  VPC Peering/Transit GW   ↔  Other VPCs                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Security Groups**:

```hcl
# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "crm-backend-alb-sg"
  vpc_id      = aws_vpc.main.id

  # Allow HTTPS from internet
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTP (for redirect)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance Security Group
resource "aws_security_group" "app" {
  name        = "crm-backend-app-sg"
  vpc_id      = aws_vpc.main.id

  # Allow traffic from ALB
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS Security Group
resource "aws_security_group" "database" {
  name        = "crm-backend-db-sg"
  vpc_id      = aws_vpc.main.id

  # Allow PostgreSQL from app instances
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  # No outbound rules needed for RDS
}
```

---

## Monitoring and Observability

### CloudWatch Dashboards

Auto-generated dashboard with key metrics:

```hcl
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "crm-backend-overview"

  dashboard_body = jsonencode({
    widgets = [
      # EC2 CPU Utilization
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", { stat = "Average" }]
          ]
          period = 300
          region = var.region
          title  = "EC2 CPU Utilization"
        }
      },
      # RDS CPU Utilization
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { stat = "Average" }]
          ]
          period = 300
          region = var.region
          title  = "RDS CPU Utilization"
        }
      },
      # ALB Request Count
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", { stat = "Sum" }]
          ]
          period = 300
          region = var.region
          title  = "ALB Request Count"
        }
      },
      # ALB Target Response Time
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average" }]
          ]
          period = 300
          region = var.region
          title  = "Response Time"
        }
      }
    ]
  })
}
```

### CloudWatch Alarms

```hcl
# CPU High Alarm
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "crm-backend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "EC2 CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app.name
  }
}

# Database Connections High
resource "aws_cloudwatch_metric_alarm" "db_connections_high" {
  alarm_name          = "crm-backend-db-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "RDS connection count is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgresql.id
  }
}

# ALB Error Rate High
resource "aws_cloudwatch_metric_alarm" "alb_errors_high" {
  alarm_name          = "crm-backend-alb-errors-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "ALB 5xx error rate is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.app.arn_suffix
  }
}
```

---

## Cost Optimization

### Reserved Instances

**Savings**: 30-60% vs on-demand

```bash
# Calculate RI savings
specql deploy deployment.yaml --analyze-ri-savings --output ri-analysis.md
```

**Sample Analysis**:
```markdown
## Reserved Instance Recommendations

### EC2 Instances
- Current: 4x t3.medium on-demand ($120/month)
- RI (1-year, all upfront): $75/month
- **Savings**: $45/month (38%)

### RDS Instances
- Current: db.t3.medium Multi-AZ on-demand ($90/month)
- RI (1-year, partial upfront): $60/month
- **Savings**: $30/month (33%)

### Total Potential Savings: $75/month (31%)
```

### Spot Instances

**Savings**: 50-90% vs on-demand (for fault-tolerant workloads)

```hcl
resource "aws_autoscaling_group" "spot" {
  name = "crm-backend-spot-asg"

  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 1   # Always 1 on-demand
      on_demand_percentage_above_base_capacity = 0   # Rest are spot
      spot_allocation_strategy                 = "capacity-optimized"
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.app.id
        version            = "$Latest"
      }

      override {
        instance_type = "t3.medium"
      }
      override {
        instance_type = "t3a.medium"  # AMD alternative
      }
    }
  }

  min_size = 2
  max_size = 10
}
```

### S3 Lifecycle Policies

**Savings**: 50-90% on storage costs

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # 50% cheaper
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"   # 70% cheaper
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE" # 95% cheaper
    }

    expiration {
      days = 2555  # 7 years (compliance)
    }
  }
}
```

---

## Security Best Practices

### Encryption at Rest

**RDS**:
```hcl
resource "aws_db_instance" "postgresql" {
  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds.arn
}
```

**EBS Volumes**:
```hcl
resource "aws_ebs_encryption_by_default" "enabled" {
  enabled = true
}
```

**S3**:
```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}
```

### Secrets Management

```hcl
# Store database password in Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name = "crm-backend-db-password"

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db.result
}

# IAM policy to access secret
resource "aws_iam_role_policy" "secrets_access" {
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.db_password.arn
      }
    ]
  })
}
```

### Network Isolation

```hcl
# No public access to RDS
resource "aws_db_instance" "postgresql" {
  publicly_accessible = false
  db_subnet_group_name = aws_db_subnet_group.private.name
}

# Bastion host for SSH access (optional)
resource "aws_instance" "bastion" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t3.nano"
  subnet_id     = aws_subnet.public[0].id

  vpc_security_group_ids = [aws_security_group.bastion.id]

  # Only allow SSH from specific IP
  # Set via variable for security
}

resource "aws_security_group" "bastion" {
  name   = "bastion-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_ip]  # Your IP only
  }
}
```

---

## Deployment Workflow

### CI/CD with GitHub Actions

```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS

on:
  push:
    branches: [main]
    paths:
      - 'deployment.yaml'
      - 'entities/**'

env:
  AWS_REGION: us-east-1

jobs:
  deploy:
    runs-on: ubuntu-latest

    permissions:
      id-token: write  # OIDC authentication
      contents: read

    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Install SpecQL
        run: pip install specql

      - name: Generate Infrastructure
        run: |
          specql deploy deployment.yaml \
            --cloud aws \
            --format terraform \
            --output terraform/

      - name: Terraform Init
        working-directory: terraform
        run: terraform init

      - name: Terraform Plan
        working-directory: terraform
        run: terraform plan -out=tfplan

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        working-directory: terraform
        run: terraform apply -auto-approve tfplan

      - name: Get Outputs
        working-directory: terraform
        run: terraform output -json > outputs.json

      - name: Upload Outputs
        uses: actions/upload-artifact@v3
        with:
          name: terraform-outputs
          path: terraform/outputs.json
```

---

## Troubleshooting

### Common Issues

**Issue**: `Error creating DB Instance: DBSubnetGroupDoesNotCoverEnoughAZs`

**Solution**: Ensure DB subnet group covers at least 2 AZs:
```hcl
resource "aws_db_subnet_group" "main" {
  name       = "crm-backend-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id  # Must span 2+ AZs

  tags = {
    Name = "CRM Backend DB subnet group"
  }
}
```

**Issue**: `503 Service Unavailable` from ALB

**Solution**: Check target health:
```bash
aws elbv2 describe-target-health \
  --target-group-arn <TARGET_GROUP_ARN>

# If unhealthy, check:
# 1. Security group allows traffic from ALB
# 2. Application is listening on correct port
# 3. Health check endpoint is responding
```

**Issue**: RDS connection timeout

**Solution**: Verify security group and network ACLs:
```bash
# Check security group rules
aws ec2 describe-security-groups \
  --group-ids <DATABASE_SG_ID>

# Test connectivity from EC2
psql -h <RDS_ENDPOINT> -U dbadmin -d appdb
```

---

## Next Steps

- [GCP Deployment](gcp-deployment.md) - Deploy to Google Cloud
- [Azure Deployment](azure-deployment.md) - Deploy to Microsoft Azure
- [Kubernetes Guide](kubernetes-deployment.md) - Container orchestration
- [Cost Optimization](cost-optimization.md) - Reduce cloud costs

---

**AWS deployment with SpecQL means battle-tested infrastructure in minutes, not weeks. From YAML to production-ready AWS resources with security, scalability, and cost optimization built-in.**

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Coverage**: Complete AWS deployment guide (Terraform, patterns, services, cost optimization)
