# Common Infrastructure Patterns Across Platforms

## Universal Concepts

### 1. Compute Resources

**Virtual Machines / Instances**:
- Size/Type (t3.medium, n1-standard-1)
- CPU, Memory, Disk
- Operating System
- Security Groups / Firewall Rules
- SSH Keys / Access

**Container Orchestration**:
- Kubernetes Deployments
- ECS/Fargate Tasks
- Google Cloud Run
- Azure Container Instances

**Serverless**:
- AWS Lambda
- Google Cloud Functions
- Azure Functions
- Function code, runtime, triggers

### 2. Storage

**Block Storage**:
- EBS volumes (AWS)
- Persistent Disks (GCP)
- Managed Disks (Azure)

**Object Storage**:
- S3 (AWS)
- Cloud Storage (GCP)
- Blob Storage (Azure)

**Database Storage**:
- RDS (AWS)
- Cloud SQL (GCP)
- Azure Database
- Self-managed on compute

### 3. Networking

**Load Balancers**:
- Application Load Balancer (AWS)
- Network Load Balancer
- Cloud Load Balancing (GCP)
- Azure Load Balancer

**Virtual Networks**:
- VPC (AWS)
- VPC (GCP)
- Virtual Network (Azure)
- Subnets, Route Tables, NAT Gateways

**DNS & Domains**:
- Route 53 (AWS)
- Cloud DNS (GCP)
- Azure DNS
- Domain registration, records

**CDN**:
- CloudFront (AWS)
- Cloud CDN (GCP)
- Azure CDN

### 4. Security

**Identity & Access**:
- IAM Roles/Policies (AWS)
- Service Accounts (GCP)
- Managed Identities (Azure)

**Secrets Management**:
- Secrets Manager (AWS)
- Secret Manager (GCP)
- Key Vault (Azure)
- HashiCorp Vault

**Certificates**:
- ACM (AWS)
- Certificate Manager (GCP)
- Key Vault Certificates (Azure)
- Let's Encrypt

### 5. Observability

**Logging**:
- CloudWatch Logs (AWS)
- Cloud Logging (GCP)
- Azure Monitor Logs

**Metrics**:
- CloudWatch Metrics (AWS)
- Cloud Monitoring (GCP)
- Azure Monitor Metrics
- Prometheus, Grafana

**Tracing**:
- X-Ray (AWS)
- Cloud Trace (GCP)
- Application Insights (Azure)
- Jaeger, Zipkin

**Alerting**:
- CloudWatch Alarms (AWS)
- Cloud Monitoring Alerts (GCP)
- Azure Alerts
- PagerDuty, Opsgenie

### 6. Application Patterns

**Web Application**:
- Load Balancer → Web Servers → Database
- Auto-scaling, Health Checks
- Static Assets on CDN

**Microservices**:
- API Gateway → Multiple Services
- Service Mesh (Istio, Linkerd)
- Service Discovery

**Data Pipeline**:
- Data Ingestion → Processing → Storage
- ETL/ELT workflows
- Streaming (Kafka, Kinesis)

**Machine Learning**:
- Training Infrastructure
- Model Serving
- Feature Store
- ML Pipelines

## Platform Comparison

| Resource | AWS | GCP | Azure | Kubernetes |
|----------|-----|-----|-------|------------|
| Compute | EC2 | Compute Engine | Virtual Machines | Deployment |
| Container | ECS/EKS | GKE | AKS | Native |
| Serverless | Lambda | Cloud Functions | Functions | Knative |
| Database | RDS | Cloud SQL | Azure Database | StatefulSet |
| Storage | S3 | Cloud Storage | Blob Storage | PV/PVC |
| Load Balancer | ALB/NLB | Load Balancing | Load Balancer | Ingress |
| Network | VPC | VPC | Virtual Network | NetworkPolicy |
