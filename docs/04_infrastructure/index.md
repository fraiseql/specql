# Infrastructure Deployment: From Code to Cloud

> **SpecQL doesn't just generate code—it generates complete infrastructure deployments**

## Overview

SpecQL's infrastructure capabilities transform your business logic into **production-ready deployments** across multiple cloud providers. Define your requirements once in YAML, generate infrastructure as code (IaC) for any platform.

**This is SpecQL's secret weapon**: Most tools stop at code generation. SpecQL goes all the way to deployed infrastructure.

## Supported Platforms

### Cloud Providers
- ☁️ **AWS**: Terraform, CloudFormation
- ☁️ **GCP**: Terraform, Deployment Manager
- ☁️ **Azure**: Terraform, ARM templates
- ☁️ **Hetzner**: Budget-friendly European hosting
- ☁️ **OVHcloud**: European cloud alternative

### Container Platforms
- 🐳 **Kubernetes**: Manifests, Helm charts
- 🐳 **Docker Compose**: Local development
- 🐳 **AWS ECS**: Container orchestration
- 🐳 **Google Cloud Run**: Serverless containers

### Infrastructure as Code
- 🛠️ **Terraform**: Multi-cloud standard
- 🛠️ **Pulumi**: TypeScript/Python IaC
- 🛠️ **CloudFormation**: AWS native
- 🛠️ **Bicep**: Azure native

## Quick Start

### Define Deployment Requirements

```yaml
# deployment.yaml
deployment:
  name: crm-backend
  environment: production

compute:
  instances: 2
  cpu: 2
  memory: 4GB
  auto_scale:
    enabled: true
    min: 2
    max: 10
    cpu_target: 70%

database:
  type: postgresql
  version: "15"
  storage: 100GB
  multi_az: true
  backups:
    enabled: true
    retention_days: 7

network:
  load_balancer: true
  https: true
  domain: api.example.com

monitoring:
  enabled: true
  metrics: cloudwatch
  alerts:
    - cpu_high
    - memory_high
    - error_rate_high
```

### Generate Infrastructure

```bash
# Generate for AWS
specql deploy deployment.yaml --cloud aws --format terraform --output terraform/aws/

# Generate for GCP
specql deploy deployment.yaml --cloud gcp --format terraform --output terraform/gcp/

# Generate for Kubernetes
specql deploy deployment.yaml --cloud kubernetes --format yaml --output k8s/
```

### Deploy

```bash
# AWS with Terraform
cd terraform/aws/
terraform init
terraform plan
terraform apply

# Kubernetes
kubectl apply -f k8s/
```

## Deployment Patterns

SpecQL includes **pre-configured deployment patterns** for common use cases:

### 1. Standard Web Application

**Best for**: Most web applications, APIs, SaaS products

```yaml
import:
  - patterns/infrastructure/web_app_standard.yaml

deployment:
  cloud: aws
  region: us-east-1

# Automatically get:
# - Load balancer with HTTPS
# - Auto-scaling (2-10 instances)
# - Multi-AZ PostgreSQL
# - CloudWatch monitoring
# - Automated backups
# - Security groups
# - VPC networking
```

**Estimated Cost**: $400-600/month

**Generated Resources**:
- Application Load Balancer
- EC2 Auto Scaling Group (2-10 t3.medium)
- RDS PostgreSQL Multi-AZ (db.t3.medium)
- CloudWatch logs and metrics
- S3 for backups
- Route53 DNS

### 2. Serverless API

**Best for**: Variable traffic, event-driven systems

```yaml
import:
  - patterns/infrastructure/serverless_api.yaml

deployment:
  cloud: aws
  region: us-west-2

# Automatically get:
# - Lambda functions
# - API Gateway
# - Aurora Serverless PostgreSQL
# - DynamoDB for caching
# - CloudFront CDN
# - Cognito authentication
```

**Estimated Cost**: $50-200/month (pay per use)

**Generated Resources**:
- Lambda functions (Node.js runtime)
- API Gateway with custom domain
- Aurora Serverless v2
- DynamoDB tables
- CloudFront distribution
- Cognito User Pool

### 3. Kubernetes Microservices

**Best for**: Complex systems, microservices architecture

```yaml
import:
  - patterns/infrastructure/kubernetes_microservices.yaml

deployment:
  cloud: gcp
  cluster: gke

# Automatically get:
# - GKE cluster
# - Service mesh (Istio)
# - PostgreSQL StatefulSet
# - Redis cache
# - Prometheus monitoring
# - Grafana dashboards
```

**Estimated Cost**: $300-500/month

**Generated Resources**:
- GKE cluster (3 nodes, n1-standard-2)
- Istio service mesh
- PostgreSQL StatefulSet with persistent volumes
- Redis deployment
- Prometheus + Grafana
- Ingress with TLS

### 4. Budget Hosting (Hetzner)

**Best for**: Startups, side projects, cost-conscious teams

```yaml
import:
  - patterns/infrastructure/hetzner_budget.yaml

deployment:
  cloud: hetzner
  region: eu-central

# Automatically get:
# - Hetzner Cloud Server
# - Managed PostgreSQL
# - Load balancer
# - Automated backups
# - Monitoring
```

**Estimated Cost**: $50-100/month

**Generated Resources**:
- Hetzner CX31 server (2 vCPU, 8GB RAM)
- Managed PostgreSQL (2GB)
- Hetzner Load Balancer
- Automated snapshots
- Built-in monitoring

## Multi-Cloud Strategy

Same SpecQL definition works across clouds:

```yaml
# deployment.yaml - Cloud-agnostic specification
deployment:
  name: my-backend
  compute:
    instances: 2
    memory: 4GB
  database:
    type: postgresql
    storage: 100GB
```

**Generate for each cloud**:

```bash
# AWS
specql deploy deployment.yaml --cloud aws --output terraform/aws/

# GCP
specql deploy deployment.yaml --cloud gcp --output terraform/gcp/

# Azure
specql deploy deployment.yaml --cloud azure --output terraform/azure/

# Compare costs
specql deploy deployment.yaml --compare-clouds --show-costs
```

**Output**:
```
Cloud Cost Comparison (monthly):

AWS:      $485/month
  - EC2: $240
  - RDS: $180
  - Load Balancer: $45
  - Networking: $20

GCP:      $420/month  ← Cheapest
  - Compute Engine: $210
  - Cloud SQL: $170
  - Load Balancer: $25
  - Networking: $15

Azure:    $510/month
  - VMs: $250
  - Azure Database: $200
  - Load Balancer: $40
  - Networking: $20

Hetzner:  $85/month  ← Budget option
  - Server: $45
  - Managed DB: $30
  - Load Balancer: $10
```

## Infrastructure Features

### Auto-Scaling

```yaml
compute:
  auto_scale:
    enabled: true
    min: 2
    max: 20
    cpu_target: 70%
    memory_target: 80%
    scale_in_cooldown: 300
    scale_out_cooldown: 60
```

**Generated (Terraform/AWS)**:
```hcl
resource "aws_autoscaling_policy" "cpu_target" {
  name                   = "cpu-target-tracking"
  policy_type           = "TargetTrackingScaling"
  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

### High Availability

```yaml
database:
  multi_az: true
  read_replicas: 2
  failover: automatic

compute:
  availability_zones: 3
  health_checks:
    enabled: true
    interval: 30
    timeout: 5
```

### Security

```yaml
security:
  encryption:
    at_rest: true
    in_transit: true

  network:
    private_subnets: true
    bastion_host: true
    vpn_access: false

  iam:
    least_privilege: true
    mfa_required: true
```

### Monitoring & Alerts

```yaml
monitoring:
  metrics:
    - cpu_utilization
    - memory_utilization
    - disk_usage
    - database_connections
    - api_response_time
    - error_rate

  alerts:
    - type: cpu_high
      threshold: 80%
      duration: 5m
      action: scale_out

    - type: error_rate_high
      threshold: 5%
      duration: 2m
      action: notify_oncall

  dashboards:
    - system_health
    - application_metrics
    - business_kpis
```

## Cost Optimization

SpecQL provides **automatic cost optimization recommendations**:

### Development Environment

```yaml
environment: development

# SpecQL automatically:
# - Uses smaller instance types
# - Disables Multi-AZ
# - Reduces backup retention
# - Uses spot instances where possible
# - Minimal monitoring
```

**Cost Savings**: 60-80% vs production

### Production Environment

```yaml
environment: production

# SpecQL automatically:
# - Recommends reserved instances
# - Enables all security features
# - Full monitoring and alerts
# - Multi-AZ and backups
# - Auto-scaling
```

### Cost Analysis Command

```bash
# Analyze and optimize costs
specql deploy deployment.yaml --optimize-cost --report cost-analysis.md

# Suggest cheaper alternatives
specql deploy deployment.yaml --suggest-alternatives
```

**Sample Output**:
```markdown
## Cost Optimization Opportunities

1. **Switch to Reserved Instances**: Save $145/month (30%)
2. **Use Aurora Serverless for DB**: Save $80/month (44% on database)
3. **Enable S3 lifecycle policies**: Save $25/month
4. **Use CloudFront caching**: Save $30/month on bandwidth

Total Potential Savings: $280/month (45% reduction)
```

## Deployment Workflows

### Local Development

```yaml
environment: local

# Generate Docker Compose
specql deploy deployment.yaml --cloud local --format docker-compose
```

```bash
# Start services
docker-compose up

# Access at http://localhost:3000
```

### Staging Deployment

```yaml
environment: staging

# Cost-optimized version of production
# - Smaller instances
# - Single AZ
# - Shorter backup retention
```

```bash
# Deploy to staging
specql deploy deployment.yaml --environment staging --cloud aws
terraform apply -var-file=staging.tfvars
```

### Production Deployment

```yaml
environment: production

# Full production setup
# - High availability
# - Auto-scaling
# - Comprehensive monitoring
# - Automated backups
# - Security hardening
```

```bash
# Deploy to production
specql deploy deployment.yaml --environment production --cloud aws
terraform apply -var-file=production.tfvars
```

## Integration with CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Infrastructure

on:
  push:
    branches: [main]
    paths:
      - 'deployment.yaml'
      - 'entities/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install SpecQL
        run: pip install specql

      - name: Generate Infrastructure
        run: specql deploy deployment.yaml --cloud aws --output terraform/

      - name: Terraform Plan
        run: |
          cd terraform
          terraform init
          terraform plan

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: |
          cd terraform
          terraform apply -auto-approve
```

## Real-World Examples

### Startup MVP (Budget: $50/month)

```yaml
import:
  - patterns/infrastructure/hetzner_budget.yaml

deployment:
  name: startup-mvp
  cloud: hetzner
  region: eu-central

compute:
  instances: 1
  memory: 4GB

database:
  storage: 20GB
```

### Growing SaaS ($500/month)

```yaml
import:
  - patterns/infrastructure/web_app_standard.yaml

deployment:
  name: saas-platform
  cloud: aws
  region: us-east-1

compute:
  instances: 3
  auto_scale:
    max: 10

database:
  storage: 100GB
  multi_az: true
  read_replicas: 1
```

### Enterprise System ($2000+/month)

```yaml
import:
  - patterns/infrastructure/kubernetes_microservices.yaml

deployment:
  name: enterprise-platform
  cloud: gcp

compute:
  cluster_size: 6
  node_type: n2-standard-4

database:
  storage: 500GB
  multi_region: true
  replicas: 3
```

## Next Steps

- [Deployment Patterns](patterns/index.md) - Pre-built deployment patterns
- [Cost Optimization](cost-optimization.md) - Reduce infrastructure costs
- [Security Hardening](security.md) - Production security best practices

---

**SpecQL's infrastructure capabilities mean you're never just generating code—you're deploying production systems. From code to cloud in minutes, not weeks.**
