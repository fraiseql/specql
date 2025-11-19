# Multi-Cloud Cost Optimization Guide

> **Reduce infrastructure costs by 30-90% across AWS, GCP, Azure, and Kubernetes**

## Overview

SpecQL provides **automatic cost optimization recommendations** across cloud providers. This guide shows you how to minimize infrastructure costs while maintaining performance, reliability, and security.

**Key Insight**: The cheapest cloud for one workload might be the most expensive for another. SpecQL helps you find the optimal deployment for your specific needs.

---

## Cost Comparison Tool

### Generate Cross-Cloud Cost Analysis

```bash
# Compare costs across all clouds
specql deploy deployment.yaml --compare-clouds --output cost-analysis.md

# Example output
```

**Sample Cost Analysis**:

```markdown
## Cost Comparison: CRM Backend (Production)

### Configuration
- Compute: 2-10 instances, 2 vCPU, 8GB RAM each
- Database: PostgreSQL 15, 2 vCPU, 8GB RAM, 100GB storage, HA
- Load Balancer: HTTPS with SSL
- Monitoring: Standard observability stack

### Monthly Costs by Provider

| Provider | Compute | Database | Networking | Monitoring | **Total** | vs Cheapest |
|----------|---------|----------|------------|------------|-----------|-------------|
| **Hetzner** | $90 | $60 | $10 | $5 | **$165** | **baseline** |
| **GCP** | $200 | $170 | $50 | $10 | **$430** | +161% |
| **AWS** | $240 | $180 | $165 | $10 | **$595** | +261% |
| **Azure** | $280 | $180 | $95 | $20 | **$575** | +248% |

### Recommendation
✅ **Deploy to Hetzner** for 72% cost savings ($430/month saved vs GCP)

### Trade-offs
- ⚠️ Hetzner: European data centers only (no US East/West)
- ⚠️ Hetzner: Smaller ecosystem vs big 3 clouds
- ✅ Hetzner: Excellent price/performance ratio
- ✅ Hetzner: 99.9% SLA (same as AWS/GCP/Azure standard tier)
```

---

## Cost Optimization Strategies

### 1. Reserved Instances / Committed Use Discounts

**Savings**: 30-72% for predictable workloads

#### AWS Reserved Instances

```bash
# 1-year standard RI (t3.medium)
# On-demand: $30/month → RI: $21/month (30% savings)

# 3-year convertible RI
# On-demand: $30/month → RI: $15/month (50% savings)

# Calculate your savings
specql deploy deployment.yaml --cloud aws --optimize-ri --output ri-analysis.md
```

**Example Savings**:
| Instance | On-Demand | 1-Year RI | 3-Year RI | Savings (3Y) |
|----------|-----------|-----------|-----------|--------------|
| t3.medium (2 vCPU, 4GB) | $30/month | $21/month | $15/month | **50%** |
| m5.large (2 vCPU, 8GB) | $70/month | $49/month | $37/month | **47%** |
| c5.xlarge (4 vCPU, 8GB) | $140/month | $98/month | $74/month | **47%** |

#### GCP Committed Use Discounts

```bash
# 1-year commitment (e2-medium)
# On-demand: $24/month → CUD: $17/month (29% savings)

# 3-year commitment
# On-demand: $24/month → CUD: $12/month (50% savings)
```

#### Azure Reserved Instances

```bash
# 1-year reservation (D2s_v3)
# Pay-as-you-go: $70/month → RI: $49/month (30% savings)

# 3-year reservation
# Pay-as-you-go: $70/month → RI: $37/month (47% savings)
```

**Best Practices**:
- ✅ Use RIs for baseline capacity (always-on workloads)
- ✅ Start with 1-year to test demand patterns
- ✅ Reserve 60-80% of steady-state capacity
- ✅ Use on-demand/spot for burst capacity

---

### 2. Spot/Preemptible Instances

**Savings**: 60-90% for fault-tolerant workloads

#### When to Use Spot Instances

**✅ Good for**:
- Batch processing
- Data analytics
- CI/CD build agents
- Dev/test environments
- Stateless web servers (with auto-healing)

**❌ Avoid for**:
- Databases
- Long-running transactions
- Single-instance applications
- Applications without checkpointing

#### AWS Spot Instances

```yaml
# deployment.yaml
compute:
  spot_instances: true
  spot_max_price: -1  # Up to on-demand price
  on_demand_base: 2   # Always have 2 on-demand
  spot_percentage: 70  # 70% of additional capacity is spot
```

**Generated Terraform**:
```hcl
resource "aws_autoscaling_group" "app" {
  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 2
      on_demand_percentage_above_base_capacity = 30
      spot_allocation_strategy                 = "capacity-optimized"
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.app.id
      }

      # Multiple instance types for better availability
      override { instance_type = "t3.medium" }
      override { instance_type = "t3a.medium" }
      override { instance_type = "t2.medium" }
    }
  }
}
```

**Savings Example**:
- On-demand: 4x t3.medium = $120/month
- Spot: 2 on-demand + 2 spot = $60 + $12 = $72/month
- **Savings**: $48/month (40%)

#### GCP Preemptible VMs

```yaml
compute:
  preemptible: true
  preemptible_percentage: 80
```

**Savings**: 70-80% off on-demand price

**Limitations**:
- Max 24-hour runtime
- Can be terminated with 30-second warning

#### Azure Spot VMs

```yaml
compute:
  spot_instances: true
  eviction_policy: Deallocate  # or Delete
  max_bid_price: -1
```

---

### 3. Auto-Scaling & Right-Sizing

**Savings**: 20-50% by matching resources to actual demand

#### Horizontal Auto-Scaling

**Scale out during high traffic, scale in during low traffic**:

```yaml
compute:
  auto_scale:
    enabled: true
    min: 2          # Baseline
    max: 20         # Peak capacity
    cpu_target: 70  # Scale at 70% CPU
    scale_in_cooldown: 300   # Wait 5 min before scale-in
    scale_out_cooldown: 60   # Wait 1 min before scale-out
```

**Cost Impact**:
- Without auto-scaling: 20 instances 24/7 = $14,400/month
- With auto-scaling: Avg 5 instances = $3,600/month
- **Savings**: $10,800/month (75%)

#### Vertical Auto-Scaling (Kubernetes VPA)

**Right-size pod resources automatically**:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-service-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  updatePolicy:
    updateMode: "Auto"
```

**Before VPA**:
```yaml
resources:
  requests:
    cpu: 2        # Over-provisioned
    memory: 4Gi
```

**After VPA** (based on actual usage):
```yaml
resources:
  requests:
    cpu: 500m     # Right-sized
    memory: 1Gi
```

**Savings**: 75% reduction in resource allocation = 75% cost savings

#### Database Auto-Scaling

**AWS Aurora Serverless v2**:
```yaml
database:
  type: aurora_serverless_v2
  min_capacity: 0.5  # ACU
  max_capacity: 4    # ACU
  auto_pause: true   # Stop when idle
```

**Cost**:
- Always-on RDS (db.t3.medium): $90/month
- Aurora Serverless (avg 1 ACU): $87/month
- Aurora Serverless (with auto-pause, 50% idle): $44/month
- **Savings**: $46/month (51%)

**GCP Cloud SQL Serverless** (coming soon):
```yaml
database:
  type: cloud_sql_serverless
  min_cpu: 0.5
  max_cpu: 4
```

---

### 4. Storage Optimization

**Savings**: 50-95% on storage costs

#### S3 Lifecycle Policies (AWS)

```yaml
storage:
  lifecycle_rules:
    - name: transition-old-data
      enabled: true
      transitions:
        - days: 30
          storage_class: STANDARD_IA  # 50% cheaper
        - days: 90
          storage_class: GLACIER_IR   # 70% cheaper
        - days: 365
          storage_class: DEEP_ARCHIVE # 95% cheaper
      expiration:
        days: 2555  # Delete after 7 years
```

**Cost Comparison** (per GB/month):
| Storage Class | Cost | Use Case |
|---------------|------|----------|
| S3 Standard | $0.023 | Frequent access |
| S3 Standard-IA | $0.0125 | Infrequent access (30+ days) |
| S3 Glacier Instant | $0.004 | Archives (90+ days) |
| S3 Glacier Deep Archive | $0.00099 | Long-term archives (365+ days) |

**Example**:
- 1TB stored for 1 year in Standard: $276
- 1TB with lifecycle (30d Standard, 60d IA, 275d Glacier): $83
- **Savings**: $193/year (70%)

#### GCS Autoclass (Google Cloud Storage)

```yaml
storage:
  autoclass: true  # Automatically move to cheaper tiers
```

**Automatic transitions**:
- Frequent access → Standard
- <30 days access → Nearline
- <90 days access → Coldline
- <365 days access → Archive

#### Azure Blob Storage Tiers

```yaml
storage:
  access_tier: Hot  # or Cool, Archive
  lifecycle_management:
    - transition_to_cool: 30 days
    - transition_to_archive: 90 days
    - delete: 365 days
```

---

### 5. Network Transfer Optimization

**Savings**: 50-90% on egress costs

#### CDN / Edge Caching

**Problem**: Egress traffic is expensive ($0.09/GB on AWS)

**Solution**: Use CDN to cache at edge locations

```yaml
cdn:
  enabled: true
  provider: cloudflare  # or cloudfront, cloud_cdn, azure_cdn
  cache_everything: true
  cache_ttl: 3600  # 1 hour
```

**Cost Impact**:
- Without CDN: 10TB egress from origin = $900/month
- With CDN (95% cache hit): 0.5TB origin egress + $50 CDN = $95/month
- **Savings**: $805/month (89%)

#### VPC Peering (Same-Region)

**Problem**: Cross-region data transfer is expensive

**Solution**: Keep services in same region, use VPC peering

```yaml
network:
  region: us-east-1  # Keep everything in one region
  vpc_peering:
    enabled: true
    peer_vpcs:
      - analytics-vpc
      - data-vpc
```

**Cost**:
- Cross-region transfer: $0.02/GB
- Same-region VPC peering: Free (AWS/GCP) or $0.01/GB (Azure)
- **Savings**: Up to 100%

#### Private Endpoints

**Avoid internet egress charges**:

```yaml
database:
  private_endpoint: true  # No public IP
  vpc_id: ${VPC_ID}
```

**Cost**:
- Public internet egress: $0.09/GB
- Private VPC traffic: Free
- **Savings**: 100% on database traffic

---

### 6. Serverless Optimization

**Savings**: Pay only for what you use (0-90% vs always-on)

#### AWS Lambda vs EC2

**Scenario**: API with variable traffic (1M requests/month, 200ms avg duration)

**EC2 (t3.small, always-on)**:
- Instance: $15/month
- **Total**: $15/month (minimum, regardless of traffic)

**Lambda**:
- Compute: 1M requests × 200ms × 128MB = $0.20
- Requests: 1M requests = $0.20
- **Total**: $0.40/month
- **Savings**: $14.60/month (97%)

**When Lambda wins**:
- ✅ Low/variable traffic
- ✅ Event-driven workloads
- ✅ Short-lived functions (<15 min)

**When EC2 wins**:
- ✅ Consistent high traffic (>10M requests/month)
- ✅ Long-running processes
- ✅ Need for custom runtime/libraries

#### GCP Cloud Run vs GKE

**Scenario**: Microservice with variable traffic

**GKE (always-on nodes)**:
- 3 nodes × e2-medium: $72/month
- **Total**: $72/month

**Cloud Run (scale to zero)**:
- CPU allocation: 0.5 vCPU × $0.000024/vCPU-second
- Memory: 1GB × $0.0000025/GB-second
- Requests: 500K/month
- Average usage: 30% of month (scales to zero 70% of time)
- **Total**: ~$22/month
- **Savings**: $50/month (69%)

#### Azure Functions vs App Service

**Scenario**: Background job processing

**App Service (Basic B1)**:
- Instance: $55/month
- **Total**: $55/month

**Azure Functions (Consumption Plan)**:
- Executions: 100K/month × $0.20/million = $0.02
- GB-seconds: 50K × $0.000016 = $0.80
- **Total**: $0.82/month
- **Savings**: $54.18/month (98%)

---

## Budget-Friendly Cloud Providers

### Hetzner Cloud

**Best for**: European startups, side projects, cost-sensitive workloads

**Pricing** (vs AWS/GCP/Azure):

| Resource | Hetzner | AWS | GCP | Azure | Savings |
|----------|---------|-----|-----|-------|---------|
| 2 vCPU, 4GB RAM | $5/month | $30 | $24 | $70 | **83-93%** |
| 4 vCPU, 8GB RAM | $11/month | $60 | $49 | $140 | **82-92%** |
| 100GB SSD storage | $5/month | $10 | $17 | $15 | **50-70%** |
| Load Balancer | $5/month | $18 | $18 | $125 | **72-96%** |

**Example: Full Stack**:
```yaml
# Hetzner deployment
deployment:
  cloud: hetzner
  location: fsn1  # Falkenstein, Germany

compute:
  server_type: cpx31  # 4 vCPU, 8GB RAM
  instances: 2

database:
  type: managed_postgresql
  plan: db-mg-4  # 2 vCPU, 4GB RAM

load_balancer:
  type: lb11

# Total: ~$50/month vs $600 on AWS
```

**Trade-offs**:
- ✅ 92% cost savings
- ✅ Excellent performance (NVMe SSDs, 10 Gbps network)
- ⚠️ EU-only data centers (Falkenstein, Helsinki, Nuremberg)
- ⚠️ Smaller ecosystem than big 3 clouds
- ✅ 99.9% SLA

### DigitalOcean

**Best for**: Startups, dev/test, simple deployments

**Pricing**:
| Droplet | vCPU | RAM | Monthly | AWS Equiv | Savings |
|---------|------|-----|---------|-----------|---------|
| Basic | 1 | 1GB | $6 | $8 | 25% |
| Basic | 2 | 2GB | $12 | $15 | 20% |
| Basic | 2 | 4GB | $24 | $30 | 20% |
| General Purpose | 4 | 8GB | $72 | $140 | 49% |

**Managed Databases**:
- PostgreSQL (2 vCPU, 4GB): $60/month (vs $180 on AWS)
- **Savings**: 67%

### OVHcloud

**Best for**: European companies, compliance (GDPR)

**Pricing** (vs big 3):
- Similar to Hetzner (50-80% cheaper)
- More regions (EU, US, Asia)
- Good for large storage needs (object storage $0.01/GB vs $0.023 AWS)

---

## Cost Monitoring & Alerts

### Set Up Budget Alerts

#### AWS Budget Alerts

```bash
# Create $500/month budget
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

#### GCP Budget Alerts

```bash
gcloud billing budgets create \
  --billing-account=ABC123-DEF456-GHI789 \
  --display-name="Monthly Budget" \
  --budget-amount=500 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

#### Azure Cost Alerts

```bash
az consumption budget create \
  --resource-group crm-backend-rg \
  --budget-name monthly-budget \
  --amount 500 \
  --time-grain Monthly \
  --threshold 80
```

### Cost Analysis Tools

```bash
# SpecQL cost analysis
specql analyze-costs deployment.yaml --output cost-report.md

# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost

# GCP Cost Table
gcloud billing accounts get-billing-info

# Azure Cost Management
az costmanagement query
```

---

## Cost Optimization Checklist

### Immediate Wins (0-1 day)

- [ ] Enable auto-scaling (save 30-50%)
- [ ] Delete unused resources (snapshots, volumes, IPs)
- [ ] Enable S3/GCS lifecycle policies (save 50-90% on storage)
- [ ] Use smaller instance types for dev/staging (save 60-80%)
- [ ] Enable CDN for static assets (save 50-90% on egress)

### Short-Term (1 week)

- [ ] Implement spot/preemptible instances (save 60-90%)
- [ ] Purchase reserved instances for baseline (save 30-50%)
- [ ] Right-size instances with monitoring data (save 20-40%)
- [ ] Consolidate low-traffic apps to serverless (save 70-95%)
- [ ] Move archives to cold storage (save 90-95%)

### Long-Term (1 month)

- [ ] Evaluate budget clouds (Hetzner, DigitalOcean) (save 70-90%)
- [ ] Implement multi-cloud strategy (deploy to cheapest)
- [ ] Optimize database queries (reduce DB size/tier)
- [ ] Implement caching (reduce compute/database load)
- [ ] Review and cancel unused licenses/subscriptions

---

## Real-World Cost Optimization Examples

### Example 1: SaaS Startup

**Before**:
- AWS deployment
- Always-on EC2 instances (t3.medium × 10)
- RDS Multi-AZ (db.m5.large)
- **Cost**: $1,200/month

**After** (optimizations):
- Spot instances for 70% of fleet → Save $250/month
- Right-size RDS to db.t3.large → Save $150/month
- Aurora Serverless for dev/staging → Save $200/month
- S3 lifecycle policies → Save $50/month
- **New Cost**: $550/month
- **Savings**: $650/month (54%)

### Example 2: E-Commerce Platform

**Before**:
- GCP deployment (us-central1)
- Compute Engine (n1-standard-4 × 5)
- Cloud SQL (db-n1-standard-4)
- **Cost**: $800/month

**After** (multi-cloud):
- Move to Hetzner (same EU region for customers)
- CPX41 instances × 2
- Managed PostgreSQL
- **New Cost**: $120/month
- **Savings**: $680/month (85%)

### Example 3: Mobile App Backend

**Before**:
- Azure App Service (P2v2 × 3)
- Azure Database for PostgreSQL (GP_Gen5_4)
- **Cost**: $900/month

**After** (serverless):
- Azure Functions (Consumption)
- Cosmos DB (serverless, 1000 RU/s)
- **New Cost**: $150/month
- **Savings**: $750/month (83%)

---

## Next Steps

- [AWS Deployment](aws-deployment.md) - AWS-specific optimizations
- [GCP Deployment](gcp-deployment.md) - GCP-specific optimizations
- [Azure Deployment](azure-deployment.md) - Azure-specific optimizations
- [Kubernetes Guide](kubernetes-deployment.md) - K8s cost optimization

---

**Cost optimization with SpecQL means data-driven decisions across clouds. From automatic cost analysis to deployment recommendations, minimize spend while maximizing performance.**

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Coverage**: Complete multi-cloud cost optimization guide (strategies, comparisons, real-world examples)
