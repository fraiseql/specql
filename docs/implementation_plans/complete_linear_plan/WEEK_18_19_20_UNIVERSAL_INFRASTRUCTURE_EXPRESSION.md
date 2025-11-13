# Weeks 18-20: Universal Infrastructure Expression Language

**Date**: 2025-11-13
**Duration**: 15 days (3 weeks)
**Status**: 🔴 Planning
**Objective**: Create universal expression language for infrastructure with reverse engineering and multi-platform generation

**Prerequisites**: Weeks 15-17 complete (Universal CI/CD Expression)
**Output**: Universal infrastructure YAML, pattern library, reverse engineering, converters for 6+ platforms

---

## 🎯 Executive Summary

Extend SpecQL's architecture to infrastructure definition using the **same pattern** as database schemas and CI/CD pipelines:

1. **Universal Expression** → Business intent for infrastructure
2. **Pattern Library** → Reusable infrastructure patterns with semantic search
3. **Reverse Engineering** → Terraform/K8s → Universal
4. **Converters** → Universal → All major platforms

### Core Philosophy

```yaml
# Users write BUSINESS INTENT (30 lines)
service: backend_api
type: web_application

compute:
  instances: 3
  memory: 2GB
  cpu: 1
  auto_scale:
    min: 2
    max: 10
    cpu_target: 70%

database:
  type: postgresql
  version: 15
  storage: 50GB
  backups: daily

networking:
  load_balancer: true
  https: true
  domain: api.example.com

observability:
  logs: cloudwatch
  metrics: prometheus
  tracing: jaeger

# SpecQL generates TECHNICAL IMPLEMENTATION (2000+ lines)
# - Terraform (AWS/GCP/Azure)
# - Kubernetes manifests
# - Docker Compose
# - CloudFormation
# - Pulumi
# - Helm charts
```

### Success Criteria

- [ ] Universal infrastructure language defined
- [ ] Pattern library with 50+ infrastructure patterns
- [ ] Reverse engineering from Terraform, Kubernetes, Docker Compose
- [ ] Converters for 6+ major platforms
- [ ] Semantic search across infrastructure patterns
- [ ] LLM enhancement for recommendations
- [ ] Cost estimation integration

---

## Week 18: Universal Infrastructure Language & Pattern Library

**Objective**: Define universal expression language for infrastructure and build pattern library

### Day 1: Universal Infrastructure Language Design

**Morning Block (4 hours): Language Specification**

#### 1. Analyze Infrastructure Patterns (2 hours)

**Research Common Infrastructure**:

`docs/infrastructure_research/COMMON_PATTERNS.md`:
```markdown
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
```

#### 2. Define Universal Schema (2 hours)

**Universal Infrastructure Schema**: `src/infrastructure/universal_infra_schema.py`

```python
"""
Universal Infrastructure Schema

Platform-agnostic expression of infrastructure that can be converted to:
- Terraform (AWS, GCP, Azure)
- Kubernetes manifests
- Docker Compose
- CloudFormation
- Pulumi
- Helm charts
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Literal
from enum import Enum


# ============================================================================
# Cloud Providers
# ============================================================================

class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"


# ============================================================================
# Compute Resources
# ============================================================================

@dataclass
class ComputeConfig:
    """Compute resource configuration"""
    instances: int = 1
    cpu: float = 1.0  # CPU cores
    memory: str = "2GB"  # Memory (e.g., "2GB", "4GB")
    disk: str = "20GB"  # Disk size

    # Auto-scaling
    auto_scale: bool = False
    min_instances: int = 1
    max_instances: int = 10
    cpu_target: int = 70  # Target CPU percentage
    memory_target: int = 80  # Target memory percentage

    # Advanced
    instance_type: Optional[str] = None  # Cloud-specific (t3.medium, n1-standard-1)
    spot_instances: bool = False  # Use spot/preemptible instances
    availability_zones: List[str] = field(default_factory=list)


@dataclass
class ContainerConfig:
    """Container configuration"""
    image: str
    tag: str = "latest"
    port: int = 8000
    environment: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)

    # Resource limits
    cpu_limit: Optional[float] = None
    memory_limit: Optional[str] = None
    cpu_request: Optional[float] = None
    memory_request: Optional[str] = None

    # Health checks
    health_check_path: str = "/health"
    health_check_interval: int = 30  # seconds
    readiness_check_path: str = "/ready"

    # Volumes
    volumes: List['Volume'] = field(default_factory=list)


# ============================================================================
# Database Resources
# ============================================================================

class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: DatabaseType
    version: str  # e.g., "15", "8.0", "7.0"

    # Size
    storage: str = "50GB"
    instance_class: Optional[str] = None  # db.t3.medium

    # High Availability
    multi_az: bool = False
    replicas: int = 0

    # Backups
    backup_enabled: bool = True
    backup_retention_days: int = 7
    backup_window: str = "03:00-04:00"

    # Maintenance
    maintenance_window: str = "sun:04:00-sun:05:00"

    # Security
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    publicly_accessible: bool = False

    # Performance
    iops: Optional[int] = None
    storage_type: str = "gp3"  # gp2, gp3, io1


# ============================================================================
# Networking
# ============================================================================

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    enabled: bool = True
    type: Literal["application", "network"] = "application"

    # SSL/TLS
    https: bool = True
    certificate_domain: Optional[str] = None
    ssl_policy: str = "recommended"

    # Routing
    health_check_path: str = "/health"
    health_check_interval: int = 30
    healthy_threshold: int = 2
    unhealthy_threshold: int = 3

    # Advanced
    sticky_sessions: bool = False
    cross_zone: bool = True
    idle_timeout: int = 60


@dataclass
class NetworkConfig:
    """Network configuration"""
    # VPC/Virtual Network
    vpc_cidr: str = "10.0.0.0/16"
    public_subnets: List[str] = field(default_factory=lambda: ["10.0.1.0/24", "10.0.2.0/24"])
    private_subnets: List[str] = field(default_factory=lambda: ["10.0.10.0/24", "10.0.20.0/24"])

    # Internet access
    enable_nat_gateway: bool = True
    enable_vpn_gateway: bool = False

    # DNS
    custom_domain: Optional[str] = None
    subdomain: Optional[str] = None


@dataclass
class CDNConfig:
    """CDN configuration"""
    enabled: bool = False
    origin_domain: str
    price_class: str = "PriceClass_100"  # Geographic distribution
    cache_ttl: int = 86400  # 24 hours
    compress: bool = True


# ============================================================================
# Storage
# ============================================================================

@dataclass
class Volume:
    """Persistent volume"""
    name: str
    size: str  # e.g., "10GB"
    mount_path: str
    storage_class: str = "standard"  # standard, ssd, premium


@dataclass
class ObjectStorageConfig:
    """Object storage (S3, GCS, Azure Blob)"""
    buckets: List['Bucket'] = field(default_factory=list)


@dataclass
class Bucket:
    """Storage bucket configuration"""
    name: str
    versioning: bool = False
    lifecycle_rules: List[Dict[str, Any]] = field(default_factory=list)
    public_access: bool = False
    encryption: bool = True


# ============================================================================
# Observability
# ============================================================================

@dataclass
class ObservabilityConfig:
    """Monitoring, logging, tracing configuration"""

    # Logging
    logging_enabled: bool = True
    log_retention_days: int = 30
    log_level: str = "INFO"

    # Metrics
    metrics_enabled: bool = True
    metrics_provider: Literal["cloudwatch", "prometheus", "datadog"] = "prometheus"

    # Tracing
    tracing_enabled: bool = False
    tracing_provider: Literal["jaeger", "zipkin", "xray"] = "jaeger"
    tracing_sample_rate: float = 0.1

    # Alerting
    alerts: List['Alert'] = field(default_factory=list)


@dataclass
class Alert:
    """Alert configuration"""
    name: str
    condition: str  # e.g., "cpu > 80%", "error_rate > 1%"
    duration: int = 300  # seconds
    notification_channels: List[str] = field(default_factory=list)


# ============================================================================
# Security
# ============================================================================

@dataclass
class SecurityConfig:
    """Security configuration"""

    # Secrets
    secrets_provider: Literal["aws_secrets", "gcp_secrets", "azure_keyvault", "vault"] = "aws_secrets"
    secrets: Dict[str, str] = field(default_factory=dict)

    # IAM/RBAC
    service_account: Optional[str] = None
    iam_roles: List[str] = field(default_factory=list)

    # Network Security
    allowed_ip_ranges: List[str] = field(default_factory=lambda: ["0.0.0.0/0"])
    enable_waf: bool = False

    # Compliance
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    audit_logging: bool = True


# ============================================================================
# Complete Service Definition
# ============================================================================

@dataclass
class UniversalInfrastructure:
    """
    Universal Infrastructure Definition

    Platform-agnostic representation that can be converted to:
    - Terraform (AWS, GCP, Azure)
    - Kubernetes
    - Docker Compose
    - CloudFormation
    - Pulumi
    """

    # Service metadata
    name: str
    description: str = ""
    service_type: Literal["web_app", "api", "worker", "data_pipeline", "ml_service"] = "api"

    # Target platform
    provider: CloudProvider = CloudProvider.AWS
    region: str = "us-east-1"
    environment: Literal["development", "staging", "production"] = "production"

    # Resources
    compute: Optional[ComputeConfig] = None
    container: Optional[ContainerConfig] = None
    database: Optional[DatabaseConfig] = None

    # Networking
    network: NetworkConfig = field(default_factory=NetworkConfig)
    load_balancer: Optional[LoadBalancerConfig] = None
    cdn: Optional[CDNConfig] = None

    # Storage
    volumes: List[Volume] = field(default_factory=list)
    object_storage: Optional[ObjectStorageConfig] = None

    # Observability
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)

    # Security
    security: SecurityConfig = field(default_factory=SecurityConfig)

    # Tags/Labels
    tags: Dict[str, str] = field(default_factory=dict)

    # Pattern metadata
    pattern_id: Optional[str] = None
    category: Optional[str] = None
    embedding: Optional[List[float]] = None

    # Cost estimation
    estimated_monthly_cost: Optional[float] = None

    def to_terraform_aws(self) -> str:
        """Convert to Terraform for AWS"""
        pass

    def to_terraform_gcp(self) -> str:
        """Convert to Terraform for GCP"""
        pass

    def to_kubernetes(self) -> str:
        """Convert to Kubernetes manifests"""
        pass

    def to_docker_compose(self) -> str:
        """Convert to Docker Compose"""
        pass

    @classmethod
    def from_terraform(cls, tf_content: str) -> 'UniversalInfrastructure':
        """Reverse engineer from Terraform"""
        pass

    @classmethod
    def from_kubernetes(cls, k8s_manifests: str) -> 'UniversalInfrastructure':
        """Reverse engineer from Kubernetes"""
        pass
```

**Universal Infrastructure YAML Format**: `docs/infrastructure_research/UNIVERSAL_INFRA_SPEC.md`

```yaml
# Universal Infrastructure YAML Specification

service: backend_api
description: "FastAPI backend with PostgreSQL and Redis"
service_type: api
provider: aws
region: us-east-1
environment: production

# ============================================================================
# Compute Configuration
# ============================================================================
compute:
  instances: 3
  cpu: 2
  memory: 4GB
  disk: 50GB

  auto_scale:
    enabled: true
    min_instances: 2
    max_instances: 10
    cpu_target: 70
    memory_target: 80

  spot_instances: false
  availability_zones:
    - us-east-1a
    - us-east-1b
    - us-east-1c

# ============================================================================
# Container Configuration
# ============================================================================
container:
  image: mycompany/backend-api
  tag: v1.2.3
  port: 8000

  environment:
    ENV: production
    LOG_LEVEL: INFO

  secrets:
    DATABASE_URL: ${secrets.database_url}
    API_KEY: ${secrets.api_key}

  resources:
    cpu_limit: 2
    memory_limit: 4GB
    cpu_request: 1
    memory_request: 2GB

  health_check:
    path: /health
    interval: 30

  readiness_check:
    path: /ready
    interval: 10

# ============================================================================
# Database Configuration
# ============================================================================
database:
  type: postgresql
  version: "15"
  storage: 100GB
  instance_class: db.t3.large

  high_availability:
    multi_az: true
    replicas: 2

  backups:
    enabled: true
    retention_days: 30
    window: "03:00-04:00"

  security:
    encryption_at_rest: true
    encryption_in_transit: true
    publicly_accessible: false

  performance:
    iops: 3000
    storage_type: gp3

# Additional databases (Redis for caching)
additional_databases:
  - type: redis
    version: "7.0"
    instance_class: cache.t3.medium
    replicas: 1

# ============================================================================
# Networking
# ============================================================================
network:
  vpc_cidr: 10.0.0.0/16
  public_subnets:
    - 10.0.1.0/24
    - 10.0.2.0/24
  private_subnets:
    - 10.0.10.0/24
    - 10.0.20.0/24

  nat_gateway: true
  custom_domain: api.example.com

# Load Balancer
load_balancer:
  enabled: true
  type: application
  https: true
  certificate_domain: api.example.com

  health_check:
    path: /health
    interval: 30
    healthy_threshold: 2
    unhealthy_threshold: 3

  sticky_sessions: false
  cross_zone: true

# CDN
cdn:
  enabled: true
  origin_domain: api.example.com
  price_class: PriceClass_100
  cache_ttl: 3600
  compress: true

# ============================================================================
# Storage
# ============================================================================
volumes:
  - name: app-storage
    size: 50GB
    mount_path: /data
    storage_class: ssd

object_storage:
  buckets:
    - name: user-uploads
      versioning: true
      public_access: false
      encryption: true
      lifecycle_rules:
        - transition_to_glacier_after_days: 90
        - expire_after_days: 365

# ============================================================================
# Observability
# ============================================================================
observability:
  logging:
    enabled: true
    retention_days: 30
    level: INFO

  metrics:
    enabled: true
    provider: prometheus

  tracing:
    enabled: true
    provider: jaeger
    sample_rate: 0.1

  alerts:
    - name: high_cpu
      condition: "cpu > 80%"
      duration: 300
      channels: [pagerduty, slack]

    - name: high_error_rate
      condition: "error_rate > 1%"
      duration: 60
      channels: [pagerduty]

    - name: database_connections_high
      condition: "db_connections > 90%"
      duration: 300
      channels: [slack]

# ============================================================================
# Security
# ============================================================================
security:
  secrets_provider: aws_secrets
  secrets:
    database_url: /prod/backend-api/database_url
    api_key: /prod/backend-api/api_key

  service_account: backend-api-sa
  iam_roles:
    - s3-read-write
    - secrets-manager-read

  allowed_ip_ranges:
    - 0.0.0.0/0  # For production, restrict to known IPs

  waf: true
  encryption_at_rest: true
  encryption_in_transit: true
  audit_logging: true

# ============================================================================
# Tags
# ============================================================================
tags:
  Project: backend-api
  Team: platform
  Environment: production
  CostCenter: engineering

# ============================================================================
# Pattern Metadata
# ============================================================================
pattern:
  category: web_application
  tags: [fastapi, postgresql, redis, aws, production]
  estimated_monthly_cost: 1500  # USD
  best_practices:
    - "Multi-AZ deployment for high availability"
    - "Auto-scaling based on CPU and memory"
    - "Automated backups with 30-day retention"
    - "Encryption at rest and in transit"
    - "Comprehensive monitoring and alerting"
```

---

**Afternoon Block (4 hours): Pattern Library**

#### 1. Design Infrastructure Pattern Library (2 hours)

**Pattern Repository**: `src/infrastructure/pattern_repository.py`

```python
"""
Infrastructure Pattern Repository

Stores reusable infrastructure patterns with semantic search.
"""

from dataclasses import dataclass
from typing import List, Optional, Protocol
from src.infrastructure.universal_infra_schema import UniversalInfrastructure


@dataclass
class InfrastructurePattern:
    """Reusable infrastructure pattern"""
    pattern_id: str
    name: str
    description: str
    category: str  # web_app, microservices, data_pipeline, ml_infrastructure

    # Pattern definition
    infrastructure: UniversalInfrastructure

    # Metadata
    tags: List[str]
    cloud_provider: str  # aws, gcp, azure, multi-cloud

    # Cost
    estimated_monthly_cost: float
    cost_optimization_tips: List[str]

    # Usage
    usage_count: int = 0
    reliability_score: float = 1.0

    # Semantic search
    embedding: Optional[List[float]] = None


class InfrastructurePatternRepository(Protocol):
    """Protocol for infrastructure pattern storage"""

    def store_pattern(self, pattern: InfrastructurePattern) -> None:
        """Store infrastructure pattern"""
        ...

    def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[InfrastructurePattern]:
        """Semantic search for similar patterns"""
        ...

    def search_by_cost(
        self,
        max_monthly_cost: float
    ) -> List[InfrastructurePattern]:
        """Find patterns within budget"""
        ...
```

#### 2. Create Initial Infrastructure Patterns (2 hours)

**Pattern Library**: `patterns/infrastructure/`

```yaml
# patterns/infrastructure/web_app_aws_standard.yaml

pattern_id: "web_app_aws_standard_v1"
name: "Standard Web Application (AWS)"
description: "Production-ready web app with load balancer, auto-scaling, RDS"
category: web_application
cloud_provider: aws
estimated_monthly_cost: 500

service: web_application
provider: aws
region: us-east-1
environment: production

compute:
  instances: 2
  cpu: 1
  memory: 2GB
  auto_scale:
    enabled: true
    min_instances: 2
    max_instances: 10
    cpu_target: 70

database:
  type: postgresql
  version: "15"
  storage: 50GB
  multi_az: true
  backups:
    enabled: true
    retention_days: 7

load_balancer:
  enabled: true
  type: application
  https: true

observability:
  logging: true
  metrics: true
  alerts:
    - {name: high_cpu, condition: "cpu > 80%"}

best_practices:
  - "Multi-AZ for high availability"
  - "Auto-scaling for cost optimization"
  - "Automated backups"
  - "HTTPS with managed certificates"

cost_optimization:
  - "Use Reserved Instances for predictable workloads"
  - "Consider Spot Instances for dev/staging"
  - "Right-size instances based on actual usage"
```

**More Patterns**:

```bash
patterns/infrastructure/
├── web_app_aws_standard.yaml
├── web_app_gcp_standard.yaml
├── web_app_azure_standard.yaml
├── kubernetes_microservices.yaml
├── serverless_api_aws.yaml
├── data_pipeline_airflow.yaml
├── ml_training_gpu.yaml
├── ml_inference_serverless.yaml
└── multi_region_ha.yaml
```

---

**Day 1 Summary**:
- ✅ Universal infrastructure schema defined
- ✅ Common patterns analyzed across AWS/GCP/Azure
- ✅ Pattern library structure created
- ✅ 10+ initial infrastructure patterns

---

### Day 2: Reverse Engineering - Terraform Parser

**Objective**: Parse Terraform files to universal format

**Morning Block (4 hours): Terraform Parser**

#### 🔴 RED: Parser Tests (2 hours)

**Test File**: `tests/unit/infrastructure/parsers/test_terraform_parser.py`

```python
"""Tests for Terraform → Universal Infrastructure parser"""

import pytest
from src.infrastructure.parsers.terraform_parser import TerraformParser
from src.infrastructure.universal_infra_schema import *


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
        assert infra.database.multi_az == True
```

---

#### 🟢 GREEN: Implement Terraform Parser (2 hours)

**Parser**: `src/infrastructure/parsers/terraform_parser.py`

```python
"""
Terraform Parser

Reverse engineers Terraform configurations to universal infrastructure format.
Uses HCL parser (python-hcl2) to parse Terraform syntax.
"""

import hcl2
from typing import Dict, Any
from src.infrastructure.universal_infra_schema import *


class TerraformParser:
    """Parse Terraform HCL to universal format"""

    def parse(self, tf_content: str) -> UniversalInfrastructure:
        """
        Parse Terraform configuration to UniversalInfrastructure

        Args:
            tf_content: Terraform HCL content

        Returns:
            UniversalInfrastructure object
        """
        # Parse HCL
        tf_dict = hcl2.loads(tf_content)

        # Extract resources
        resources = tf_dict.get("resource", [])

        # Parse different resource types
        compute = self._parse_compute(resources)
        database = self._parse_database(resources)
        network = self._parse_network(resources)
        load_balancer = self._parse_load_balancer(resources)

        # Detect provider and region
        provider_config = tf_dict.get("provider", {})
        provider, region = self._detect_provider(provider_config, resources)

        return UniversalInfrastructure(
            name=self._extract_name(resources),
            provider=provider,
            region=region,
            compute=compute,
            database=database,
            network=network,
            load_balancer=load_balancer
        )

    def _parse_compute(self, resources: List[Dict]) -> Optional[ComputeConfig]:
        """Parse compute resources (EC2, Compute Engine, etc.)"""
        for resource_type, resource_configs in resources.items():
            if "aws_instance" in resource_type:
                for name, config in resource_configs.items():
                    return ComputeConfig(
                        instances=1,
                        instance_type=config.get("instance_type"),
                        # Parse CPU/memory from instance_type
                    )
            elif "google_compute_instance" in resource_type:
                # Parse GCP instances
                pass

        return None

    def _parse_database(self, resources: List[Dict]) -> Optional[DatabaseConfig]:
        """Parse database resources (RDS, Cloud SQL, etc.)"""
        for resource_type, resource_configs in resources.items():
            if "aws_db_instance" in resource_type:
                for name, config in resource_configs.items():
                    engine = config.get("engine", "")
                    db_type = self._map_engine_to_type(engine)

                    return DatabaseConfig(
                        type=db_type,
                        version=str(config.get("engine_version", "")),
                        storage=f"{config.get('allocated_storage', 0)}GB",
                        instance_class=config.get("instance_class"),
                        multi_az=config.get("multi_az", False),
                        backup_retention_days=config.get("backup_retention_period", 0)
                    )

        return None

    def _map_engine_to_type(self, engine: str) -> DatabaseType:
        """Map Terraform engine to universal DatabaseType"""
        engine_map = {
            "postgres": DatabaseType.POSTGRESQL,
            "mysql": DatabaseType.MYSQL,
            "redis": DatabaseType.REDIS,
        }
        return engine_map.get(engine, DatabaseType.POSTGRESQL)

    def _detect_provider(
        self,
        provider_config: Dict,
        resources: List[Dict]
    ) -> tuple[CloudProvider, str]:
        """Detect cloud provider and region"""
        # Check provider block
        if "aws" in provider_config:
            return CloudProvider.AWS, provider_config["aws"].get("region", "us-east-1")
        elif "google" in provider_config:
            return CloudProvider.GCP, provider_config["google"].get("region", "us-central1")

        # Infer from resource types
        for resource_type in resources.keys():
            if "aws_" in resource_type:
                return CloudProvider.AWS, "us-east-1"
            elif "google_" in resource_type:
                return CloudProvider.GCP, "us-central1"

        return CloudProvider.AWS, "us-east-1"
```

---

**Afternoon Block (4 hours): Kubernetes Parser**

Similar structure, parsing Kubernetes YAML manifests (Deployment, Service, Ingress, etc.) to universal format.

**Day 2 Summary**:
- ✅ Terraform parser complete (AWS resources)
- ✅ Kubernetes parser complete
- ✅ Docker Compose parser implemented
- ✅ Can reverse engineer 3 major platforms

---

### Day 3: Converters - Terraform Generator

**Objective**: Generate Terraform from universal format

**Morning Block (4 hours): Terraform AWS Generator**

#### 🔴 RED: Generator Tests (1.5 hours)

**Test File**: `tests/unit/infrastructure/generators/test_terraform_aws_generator.py`

```python
"""Tests for Universal → Terraform AWS generator"""

import pytest
from src.infrastructure.generators.terraform_aws_generator import TerraformAWSGenerator
from src.infrastructure.universal_infra_schema import *


class TestTerraformAWSGenerator:
    """Test generating Terraform for AWS"""

    @pytest.fixture
    def generator(self):
        return TerraformAWSGenerator()

    def test_generate_compute(self, generator):
        """Test generating EC2 instances"""
        infra = UniversalInfrastructure(
            name="web-server",
            provider=CloudProvider.AWS,
            compute=ComputeConfig(
                instances=3,
                cpu=2,
                memory="4GB",
                auto_scale=True,
                min_instances=2,
                max_instances=10
            )
        )

        # Act
        tf_output = generator.generate(infra)

        # Assert
        assert "resource \"aws_launch_template\"" in tf_output
        assert "resource \"aws_autoscaling_group\"" in tf_output
        assert "min_size = 2" in tf_output
        assert "max_size = 10" in tf_output

    def test_generate_database(self, generator):
        """Test generating RDS database"""
        infra = UniversalInfrastructure(
            name="backend-db",
            provider=CloudProvider.AWS,
            database=DatabaseConfig(
                type=DatabaseType.POSTGRESQL,
                version="15",
                storage="100GB",
                multi_az=True,
                backup_retention_days=7
            )
        )

        # Act
        tf_output = generator.generate(infra)

        # Assert
        assert "resource \"aws_db_instance\"" in tf_output
        assert "engine = \"postgres\"" in tf_output
        assert "engine_version = \"15\"" in tf_output
        assert "multi_az = true" in tf_output
        assert "backup_retention_period = 7" in tf_output
```

---

#### 🟢 GREEN: Implement Terraform Generator (2.5 hours)

**Template**: `templates/infrastructure/terraform_aws.tf.j2`

```hcl
{# Terraform AWS Template #}

# ============================================================================
# Provider Configuration
# ============================================================================
provider "aws" {
  region = "{{ infrastructure.region }}"
}

{%- if infrastructure.compute %}

# ============================================================================
# Compute Resources (Auto Scaling Group)
# ============================================================================

# Launch Template
resource "aws_launch_template" "{{ infrastructure.name }}" {
  name_prefix   = "{{ infrastructure.name }}-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "{{ _map_instance_type(infrastructure.compute) }}"

  {%- if infrastructure.container %}
  user_data = base64encode(<<-EOF
    #!/bin/bash
    # Install Docker
    apt-get update
    apt-get install -y docker.io

    # Run container
    docker run -d \
      -p {{ infrastructure.container.port }}:{{ infrastructure.container.port }} \
      {%- for key, value in infrastructure.container.environment.items() %}
      -e {{ key }}={{ value }} \
      {%- endfor %}
      {{ infrastructure.container.image }}:{{ infrastructure.container.tag }}
  EOF
  )
  {%- endif %}

  tags = {
    Name = "{{ infrastructure.name }}"
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "{{ infrastructure.name }}" {
  name                = "{{ infrastructure.name }}-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  min_size            = {{ infrastructure.compute.min_instances }}
  max_size            = {{ infrastructure.compute.max_instances }}
  desired_capacity    = {{ infrastructure.compute.instances }}

  launch_template {
    id      = aws_launch_template.{{ infrastructure.name }}.id
    version = "$Latest"
  }

  {%- if infrastructure.load_balancer %}
  target_group_arns = [aws_lb_target_group.{{ infrastructure.name }}.arn]
  {%- endif %}

  health_check_type         = "ELB"
  health_check_grace_period = 300

  tag {
    key                 = "Name"
    value               = "{{ infrastructure.name }}"
    propagate_at_launch = true
  }
}

# Auto Scaling Policies
resource "aws_autoscaling_policy" "cpu" {
  name                   = "{{ infrastructure.name }}-cpu-policy"
  autoscaling_group_name = aws_autoscaling_group.{{ infrastructure.name }}.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = {{ infrastructure.compute.cpu_target }}
  }
}
{%- endif %}

{%- if infrastructure.database %}

# ============================================================================
# Database (RDS)
# ============================================================================

resource "aws_db_instance" "{{ infrastructure.name }}" {
  identifier     = "{{ infrastructure.name }}-db"
  engine         = "{{ _map_database_engine(infrastructure.database.type) }}"
  engine_version = "{{ infrastructure.database.version }}"
  instance_class = "{{ infrastructure.database.instance_class or 'db.t3.medium' }}"

  allocated_storage     = {{ infrastructure.database.storage|replace('GB', '') }}
  storage_type          = "{{ infrastructure.database.storage_type }}"
  {%- if infrastructure.database.iops %}
  iops                  = {{ infrastructure.database.iops }}
  {%- endif %}

  db_name  = "{{ infrastructure.name|replace('-', '_') }}"
  username = "admin"
  password = random_password.db_password.result

  # High Availability
  multi_az               = {{ infrastructure.database.multi_az|lower }}
  {%- if infrastructure.database.replicas > 0 %}
  # Note: Read replicas created separately
  {%- endif %}

  # Backups
  backup_retention_period = {{ infrastructure.database.backup_retention_days }}
  backup_window          = "{{ infrastructure.database.backup_window }}"
  maintenance_window     = "{{ infrastructure.database.maintenance_window }}"

  # Security
  storage_encrypted = {{ infrastructure.security.encryption_at_rest|lower }}
  publicly_accessible = {{ infrastructure.database.publicly_accessible|lower }}

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.{{ infrastructure.name }}.name

  # Deletion protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "{{ infrastructure.name }}-final-snapshot"

  tags = {
    Name = "{{ infrastructure.name }}-database"
  }
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store password in Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name = "/{{ infrastructure.environment }}/{{ infrastructure.name }}/database-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}
{%- endif %}

{%- if infrastructure.load_balancer %}

# ============================================================================
# Load Balancer
# ============================================================================

resource "aws_lb" "{{ infrastructure.name }}" {
  name               = "{{ infrastructure.name }}-lb"
  internal           = false
  load_balancer_type = "{{ infrastructure.load_balancer.type }}"
  security_groups    = [aws_security_group.lb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
  enable_cross_zone_load_balancing = {{ infrastructure.load_balancer.cross_zone|lower }}

  tags = {
    Name = "{{ infrastructure.name }}-lb"
  }
}

# Target Group
resource "aws_lb_target_group" "{{ infrastructure.name }}" {
  name     = "{{ infrastructure.name }}-tg"
  port     = {{ infrastructure.container.port if infrastructure.container else 80 }}
  protocol = "HTTP"
  vpc_id   = aws_vpc.{{ infrastructure.name }}.id

  health_check {
    enabled             = true
    healthy_threshold   = {{ infrastructure.load_balancer.healthy_threshold }}
    unhealthy_threshold = {{ infrastructure.load_balancer.unhealthy_threshold }}
    timeout             = 5
    interval            = {{ infrastructure.load_balancer.health_check_interval }}
    path                = "{{ infrastructure.load_balancer.health_check_path }}"
  }
}

# HTTPS Listener
{%- if infrastructure.load_balancer.https %}
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.{{ infrastructure.name }}.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.{{ infrastructure.name }}.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.{{ infrastructure.name }}.arn
  }
}

# HTTP Listener (redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.{{ infrastructure.name }}.arn
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
{%- endif %}
{%- endif %}

# ============================================================================
# Networking (VPC, Subnets, etc.)
# ============================================================================

{# VPC configuration... #}

# ============================================================================
# Outputs
# ============================================================================

output "load_balancer_dns" {
  value = aws_lb.{{ infrastructure.name }}.dns_name
}

{%- if infrastructure.database %}
output "database_endpoint" {
  value = aws_db_instance.{{ infrastructure.name }}.endpoint
}
{%- endif %}
```

**Generator**: `src/infrastructure/generators/terraform_aws_generator.py`

```python
"""Terraform AWS Generator"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.infrastructure.universal_infra_schema import UniversalInfrastructure, DatabaseType


class TerraformAWSGenerator:
    """Generate Terraform for AWS from universal format"""

    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("terraform_aws.tf.j2")

        # Add custom filters
        self.env.filters["map_instance_type"] = self._map_instance_type
        self.env.filters["map_database_engine"] = self._map_database_engine

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Terraform configuration for AWS"""
        return self.template.render(
            infrastructure=infrastructure,
            _map_instance_type=self._map_instance_type,
            _map_database_engine=self._map_database_engine
        )

    def _map_instance_type(self, compute_config) -> str:
        """Map universal compute config to AWS instance type"""
        # Simple mapping based on CPU/memory
        if compute_config.instance_type:
            return compute_config.instance_type

        cpu = compute_config.cpu
        memory_gb = int(compute_config.memory.replace("GB", ""))

        if cpu <= 1 and memory_gb <= 2:
            return "t3.small"
        elif cpu <= 2 and memory_gb <= 4:
            return "t3.medium"
        elif cpu <= 4 and memory_gb <= 8:
            return "t3.large"
        else:
            return "t3.xlarge"

    def _map_database_engine(self, db_type: DatabaseType) -> str:
        """Map universal database type to AWS RDS engine"""
        engine_map = {
            DatabaseType.POSTGRESQL: "postgres",
            DatabaseType.MYSQL: "mysql",
            DatabaseType.REDIS: "redis",
        }
        return engine_map.get(db_type, "postgres")
```

**Run Tests (Should Pass)**:
```bash
uv run pytest tests/unit/infrastructure/generators/test_terraform_aws_generator.py -v
```

---

**Afternoon Block (4 hours): Kubernetes Generator**

Similar implementation for generating Kubernetes manifests (Deployment, Service, Ingress, HPA, etc.).

**Day 3 Summary**:
- ✅ Terraform AWS generator complete
- ✅ Kubernetes generator complete
- ✅ Docker Compose generator implemented
- ✅ Can convert universal → 3+ platforms

---

### Days 4-5: Additional Platforms & CLI Integration

**Day 4**:
- GCP Terraform generator
- Azure Terraform generator
- CloudFormation generator
- Pulumi generator

**Day 5**:
- CLI integration (`specql reverse-infra`, `specql generate-infra`)
- Cost estimation integration
- Documentation

---

### Day 6: Managed Bare Metal Support

**Objective**: Extend universal infrastructure to support managed bare metal providers (OVHcloud, Hetzner, Equinix Metal)

**Why Bare Metal Matters**:
- **Cost**: 50-70% cheaper than cloud for consistent workloads
- **Performance**: Dedicated hardware, no noisy neighbors
- **Use cases**: High-performance databases, Kubernetes nodes, CI/CD, data processing

**Morning Block (4 hours): Bare Metal Schema & Parsers**

#### 1. Extend Universal Schema for Bare Metal (1.5 hours)

**Update Schema**: `src/infrastructure/universal_infra_schema.py`

Add to existing file:

```python
# Add to CloudProvider enum
class CloudProvider(str, Enum):
    """Supported cloud and bare metal providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"

    # Managed Bare Metal
    OVH_BARE_METAL = "ovh_bare_metal"
    HETZNER_BARE_METAL = "hetzner_bare_metal"
    EQUINIX_METAL = "equinix_metal"
    VULTR_BARE_METAL = "vultr_bare_metal"


@dataclass
class PhysicalDrive:
    """Physical drive specification"""
    type: Literal["nvme", "ssd", "hdd"]
    size_gb: int
    quantity: int = 1


@dataclass
class RAIDConfig:
    """RAID configuration"""
    level: Literal["raid0", "raid1", "raid5", "raid10"]
    drives: List[int]  # Drive indices


@dataclass
class BareMetalConfig:
    """Bare metal specific configuration"""
    # Hardware specifications (actual physical specs)
    server_model: str  # e.g., "RISE-1", "AX41-NVMe", "c3.small.x86"
    cpu_model: str  # e.g., "Intel Xeon E-2288G", "AMD Ryzen 9 3900"
    cpu_cores: int  # Physical cores
    cpu_threads: int  # With hyperthreading
    ram_gb: int  # Actual RAM in GB

    # Storage configuration
    drives: List[PhysicalDrive]
    raid_config: Optional[RAIDConfig] = None

    # Networking
    network_interfaces: int = 1
    bandwidth_gbps: int = 1  # Network bandwidth
    public_ips: int = 1
    private_networking: bool = True

    # Provisioning
    os_template: str = "ubuntu_22.04"
    ssh_keys: List[str] = field(default_factory=list)
    provisioning_time_minutes: int = 10  # Typical provisioning time

    # Billing
    billing_cycle: Literal["hourly", "monthly", "annual"] = "monthly"
    monthly_cost: float = 0.0


# Update UniversalInfrastructure dataclass
@dataclass
class UniversalInfrastructure:
    # ... existing fields ...

    # Add bare metal configuration
    bare_metal: Optional[BareMetalConfig] = None

    # Flag to distinguish deployment types
    deployment_type: Literal["cloud_vm", "bare_metal", "container"] = "cloud_vm"
```

**Documentation**: `docs/infrastructure_research/BARE_METAL_COMPARISON.md`

```markdown
# Managed Bare Metal vs Cloud VMs

## Supported Providers

| Provider | Provisioning | Min Cost/Month | Best For |
|----------|--------------|----------------|----------|
| OVHcloud | 5-10 min | €40 | EU customers, price-sensitive |
| Hetzner | 5-15 min | €39 | EU customers, simple setup |
| Equinix Metal | 5-10 min | $150 | Global, hybrid cloud |
| Vultr | 10-15 min | $120 | Global presence |

## Key Differences

| Feature | Cloud VMs | Managed Bare Metal |
|---------|-----------|-------------------|
| Hardware | Virtualized | Dedicated physical |
| Provisioning | Seconds | 5-15 minutes |
| Specs | Abstract (t3.medium) | Specific (Xeon E-2388G) |
| Cost (DB workload) | $350/mo | $96/mo (73% savings) |
| Auto-scaling | Native | Manual/orchestration |
| Billing | Hourly | Monthly (usually) |

## Cost Example: PostgreSQL Database

**AWS RDS (db.r5.2xlarge)**:
- 8 vCPUs, 64GB RAM
- 500GB storage
- Multi-AZ
- Cost: ~$650/month

**OVHcloud RISE-1**:
- 8 cores, 128GB RAM
- 2x 960GB NVMe (RAID1)
- Self-managed PostgreSQL
- Cost: €95/month (~$102)
- **Savings: 84%**

## Best Use Cases for Bare Metal

1. **Databases**: High I/O, predictable workload
2. **Kubernetes nodes**: Control plane, worker nodes
3. **CI/CD**: Build servers, test runners
4. **Data processing**: ETL, analytics
5. **Game servers**: Low latency, dedicated resources
```

---

#### 🔴 RED: Bare Metal Parser Tests (1 hour)

**Test File**: `tests/unit/infrastructure/parsers/test_ovh_parser.py`

```python
"""Tests for OVHcloud bare metal parser"""

import pytest
from src.infrastructure.parsers.ovh_parser import OVHBareMetalParser
from src.infrastructure.universal_infra_schema import *


class TestOVHBareMetalParser:
    """Test parsing OVHcloud API responses to universal format"""

    @pytest.fixture
    def parser(self):
        return OVHBareMetalParser()

    def test_parse_rise_server(self, parser):
        """Test parsing OVH RISE-1 server specification"""
        ovh_config = {
            "name": "ns123456.ip-1-2-3.eu",
            "datacenter": "gra3",
            "commercialRange": "rise",
            "os": "ubuntu22_04",
            "specs": {
                "cpu": "Intel Xeon E-2388G",
                "cores": 8,
                "threads": 16,
                "ram": {"size": 128000},
                "disks": [
                    {"type": "NVME", "capacity": 960000},
                    {"type": "NVME", "capacity": 960000}
                ]
            }
        }

        # Act
        infra = parser.parse(ovh_config)

        # Assert
        assert infra.provider == CloudProvider.OVH_BARE_METAL
        assert infra.deployment_type == "bare_metal"
        assert infra.region == "gra3"

        # Bare metal config
        assert infra.bare_metal is not None
        assert infra.bare_metal.cpu_cores == 8
        assert infra.bare_metal.cpu_threads == 16
        assert infra.bare_metal.ram_gb == 128
        assert len(infra.bare_metal.drives) == 2
        assert infra.bare_metal.drives[0].type == "nvme"
        assert infra.bare_metal.drives[0].size_gb == 960

    def test_parse_with_raid(self, parser):
        """Test parsing server with RAID configuration"""
        ovh_config = {
            "name": "db-server",
            "commercialRange": "rise",
            "specs": {
                "cpu": "Intel Xeon E-2388G",
                "cores": 8,
                "threads": 16,
                "ram": {"size": 128000},
                "disks": [
                    {"type": "NVME", "capacity": 960000},
                    {"type": "NVME", "capacity": 960000}
                ]
            },
            "raid": {
                "level": "raid1",
                "drives": [0, 1]
            }
        }

        # Act
        infra = parser.parse(ovh_config)

        # Assert
        assert infra.bare_metal.raid_config is not None
        assert infra.bare_metal.raid_config.level == "raid1"
        assert infra.bare_metal.raid_config.drives == [0, 1]
```

**Test should FAIL** (parser not implemented yet)

```bash
uv run pytest tests/unit/infrastructure/parsers/test_ovh_parser.py -v
# Expected: ImportError or test failures
```

---

#### 🟢 GREEN: Implement OVH Parser (1.5 hours)

**Parser**: `src/infrastructure/parsers/ovh_parser.py`

```python
"""
OVHcloud Bare Metal Parser

Reverse engineers OVHcloud API responses to universal infrastructure format.
"""

from typing import Dict, Any, List
from src.infrastructure.universal_infra_schema import *


class OVHBareMetalParser:
    """Parse OVHcloud bare metal server specs to universal format"""

    def parse(self, ovh_config: Dict[str, Any]) -> UniversalInfrastructure:
        """
        Parse OVHcloud API response to universal format

        Args:
            ovh_config: OVHcloud API response with server specs

        Returns:
            UniversalInfrastructure object
        """
        specs = ovh_config.get("specs", {})

        # Parse drives
        drives = self._parse_drives(specs.get("disks", []))

        # Parse RAID if present
        raid_config = None
        if "raid" in ovh_config:
            raid_config = RAIDConfig(
                level=ovh_config["raid"]["level"],
                drives=ovh_config["raid"]["drives"]
            )

        # Build bare metal configuration
        bare_metal = BareMetalConfig(
            server_model=ovh_config.get("commercialRange", "").upper(),
            cpu_model=specs.get("cpu", ""),
            cpu_cores=specs.get("cores", 0),
            cpu_threads=specs.get("threads", 0),
            ram_gb=specs.get("ram", {}).get("size", 0) // 1000,
            drives=drives,
            raid_config=raid_config,
            os_template=ovh_config.get("os", "ubuntu_22.04"),
            billing_cycle="monthly"
        )

        return UniversalInfrastructure(
            name=ovh_config.get("name", ""),
            provider=CloudProvider.OVH_BARE_METAL,
            region=ovh_config.get("datacenter", "gra"),
            deployment_type="bare_metal",
            bare_metal=bare_metal
        )

    def _parse_drives(self, disks: List[Dict[str, Any]]) -> List[PhysicalDrive]:
        """Parse disk specifications"""
        drives = []
        for disk in disks:
            drives.append(PhysicalDrive(
                type=disk["type"].lower(),
                size_gb=disk["capacity"] // 1000,
                quantity=1
            ))
        return drives
```

**Run Tests (Should Pass)**:

```bash
uv run pytest tests/unit/infrastructure/parsers/test_ovh_parser.py -v
# Expected: All tests pass
```

---

**Afternoon Block (4 hours): Bare Metal Generators**

#### 🔴 RED: Terraform Generator Tests (1 hour)

**Test File**: `tests/unit/infrastructure/generators/test_terraform_ovh_generator.py`

```python
"""Tests for Universal → Terraform OVH generator"""

import pytest
from src.infrastructure.generators.terraform_ovh_generator import TerraformOVHGenerator
from src.infrastructure.universal_infra_schema import *


class TestTerraformOVHGenerator:
    """Test generating Terraform for OVHcloud bare metal"""

    @pytest.fixture
    def generator(self):
        return TerraformOVHGenerator()

    def test_generate_bare_metal_server(self, generator):
        """Test generating OVH bare metal server"""
        infra = UniversalInfrastructure(
            name="db-server",
            provider=CloudProvider.OVH_BARE_METAL,
            region="gra",
            deployment_type="bare_metal",
            bare_metal=BareMetalConfig(
                server_model="RISE-1",
                cpu_model="Intel Xeon E-2388G",
                cpu_cores=8,
                cpu_threads=16,
                ram_gb=128,
                drives=[
                    PhysicalDrive(type="nvme", size_gb=960, quantity=1),
                    PhysicalDrive(type="nvme", size_gb=960, quantity=1)
                ],
                raid_config=RAIDConfig(level="raid1", drives=[0, 1]),
                os_template="ubuntu_22.04",
                ssh_keys=["ssh-rsa AAAAB3..."]
            )
        )

        # Act
        tf_output = generator.generate(infra)

        # Assert
        assert 'resource "ovh_dedicated_server"' in tf_output
        assert "datacenter = \"gra\"" in tf_output
        assert "template_name = \"ubuntu_22.04\"" in tf_output
        assert "raid1" in tf_output

    def test_generate_with_database(self, generator):
        """Test generating bare metal with self-hosted database"""
        infra = UniversalInfrastructure(
            name="postgres-server",
            provider=CloudProvider.OVH_BARE_METAL,
            deployment_type="bare_metal",
            bare_metal=BareMetalConfig(
                server_model="RISE-1",
                cpu_model="Intel Xeon E-2388G",
                cpu_cores=8,
                cpu_threads=16,
                ram_gb=128,
                drives=[
                    PhysicalDrive(type="nvme", size_gb=960, quantity=2)
                ],
                os_template="ubuntu_22.04"
            ),
            database=DatabaseConfig(
                type=DatabaseType.POSTGRESQL,
                version="15",
                storage="1800GB"
            )
        )

        # Act
        tf_output = generator.generate(infra)

        # Assert - should include provisioner for PostgreSQL installation
        assert "postgresql" in tf_output.lower()
        assert "provisioner" in tf_output
```

**Run Tests (Should Fail)**:

```bash
uv run pytest tests/unit/infrastructure/generators/test_terraform_ovh_generator.py -v
```

---

#### 🟢 GREEN: Implement Terraform OVH Generator (2 hours)

**Template**: `templates/infrastructure/terraform_ovh.tf.j2`

```hcl
# Terraform for OVHcloud Bare Metal

terraform {
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "~> 0.35"
    }
  }
}

provider "ovh" {
  endpoint = "ovh-eu"
}

{%- if infrastructure.bare_metal %}

# ============================================================================
# Bare Metal Server
# ============================================================================

resource "ovh_dedicated_server" "{{ infrastructure.name }}" {
  service_name = "{{ infrastructure.name }}"

  # Server specifications
  plan_code = "{{ _map_to_ovh_plan_code(infrastructure.bare_metal) }}"
  datacenter = "{{ infrastructure.region }}"

  # Operating System
  template_name = "{{ infrastructure.bare_metal.os_template }}"

  {%- if infrastructure.bare_metal.ssh_keys %}
  # SSH Keys
  {%- for ssh_key in infrastructure.bare_metal.ssh_keys %}
  ssh_key_name = "key-{{ loop.index }}"
  {%- endfor %}
  {%- endif %}

  {%- if infrastructure.bare_metal.raid_config %}
  # RAID Configuration
  disk_group {
    disk_type = "{{ infrastructure.bare_metal.drives[0].type }}"
    raid_level = "{{ infrastructure.bare_metal.raid_config.level }}"
    disk_count = {{ infrastructure.bare_metal.raid_config.drives|length }}
  }
  {%- endif %}

  lifecycle {
    ignore_changes = [
      # Ignore changes to installed software
      template_name,
    ]
  }
}

# Additional IP addresses
{%- if infrastructure.bare_metal.public_ips > 1 %}
resource "ovh_ip_service" "additional_ips" {
  count = {{ infrastructure.bare_metal.public_ips - 1 }}
  ovh_subsidiary = "EU"
  description = "{{ infrastructure.name }}-ip-${count.index + 2}"
}
{%- endif %}

# Private network (vRack)
{%- if infrastructure.bare_metal.private_networking %}
resource "ovh_vrack" "{{ infrastructure.name }}" {
  name        = "{{ infrastructure.name }}-vrack"
  description = "Private network for {{ infrastructure.name }}"
}

resource "ovh_vrack_dedicated_server" "{{ infrastructure.name }}" {
  service_name     = ovh_vrack.{{ infrastructure.name }}.id
  dedicated_server = ovh_dedicated_server.{{ infrastructure.name }}.service_name
}
{%- endif %}

{%- if infrastructure.database %}
# ============================================================================
# Database Installation (Self-Hosted)
# ============================================================================

# Install and configure database via provisioner
resource "null_resource" "install_database" {
  depends_on = [ovh_dedicated_server.{{ infrastructure.name }}]

  connection {
    type = "ssh"
    host = ovh_dedicated_server.{{ infrastructure.name }}.ip
    user = "root"
    {%- if infrastructure.bare_metal.ssh_keys %}
    private_key = file("~/.ssh/id_rsa")
    {%- endif %}
  }

  # Install PostgreSQL
  provisioner "remote-exec" {
    inline = [
      "apt-get update",
      "apt-get install -y postgresql-{{ infrastructure.database.version }}",

      # Configure PostgreSQL
      "systemctl enable postgresql",
      "systemctl start postgresql",

      # Basic optimization for dedicated hardware
      "echo 'shared_buffers = 32GB' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",
      "echo 'effective_cache_size = 96GB' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",
      "echo 'maintenance_work_mem = 2GB' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",
      "echo 'checkpoint_completion_target = 0.9' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",
      "echo 'wal_buffers = 16MB' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",
      "echo 'default_statistics_target = 100' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",
      "echo 'random_page_cost = 1.1' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",
      "echo 'effective_io_concurrency = 200' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",
      "echo 'work_mem = 20MB' >> /etc/postgresql/{{ infrastructure.database.version }}/main/postgresql.conf",

      # Restart to apply configuration
      "systemctl restart postgresql"
    ]
  }
}
{%- endif %}

{%- if infrastructure.observability.metrics_enabled %}
# ============================================================================
# Monitoring Setup
# ============================================================================

resource "null_resource" "install_monitoring" {
  depends_on = [ovh_dedicated_server.{{ infrastructure.name }}]

  connection {
    type = "ssh"
    host = ovh_dedicated_server.{{ infrastructure.name }}.ip
    user = "root"
  }

  # Install Prometheus node exporter
  provisioner "remote-exec" {
    inline = [
      "wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz",
      "tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz",
      "cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/",

      # Create systemd service
      "cat > /etc/systemd/system/node_exporter.service <<EOF",
      "[Unit]",
      "Description=Node Exporter",
      "[Service]",
      "ExecStart=/usr/local/bin/node_exporter",
      "[Install]",
      "WantedBy=multi-user.target",
      "EOF",

      "systemctl daemon-reload",
      "systemctl enable node_exporter",
      "systemctl start node_exporter"
    ]
  }
}
{%- endif %}

{%- endif %}

# ============================================================================
# Outputs
# ============================================================================

output "server_ip" {
  value       = ovh_dedicated_server.{{ infrastructure.name }}.ip
  description = "Public IP address of the bare metal server"
}

output "server_name" {
  value       = ovh_dedicated_server.{{ infrastructure.name }}.service_name
  description = "OVH service name"
}

{%- if infrastructure.database %}
output "database_endpoint" {
  value       = "${ovh_dedicated_server.{{ infrastructure.name }}.ip}:5432"
  description = "Database connection endpoint"
}
{%- endif %}

output "monthly_cost" {
  value       = "€{{ infrastructure.bare_metal.monthly_cost }}"
  description = "Estimated monthly cost"
}
```

**Generator**: `src/infrastructure/generators/terraform_ovh_generator.py`

```python
"""Terraform OVHcloud Bare Metal Generator"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.infrastructure.universal_infra_schema import UniversalInfrastructure


class TerraformOVHGenerator:
    """Generate Terraform for OVHcloud bare metal from universal format"""

    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("terraform_ovh.tf.j2")

        # Add custom filters
        self.env.filters["map_to_ovh_plan_code"] = self._map_to_ovh_plan_code

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Terraform configuration for OVHcloud"""
        return self.template.render(
            infrastructure=infrastructure,
            _map_to_ovh_plan_code=self._map_to_ovh_plan_code
        )

    def _map_to_ovh_plan_code(self, bare_metal_config) -> str:
        """Map bare metal config to OVH plan code"""
        # Map server models to OVH plan codes
        model_map = {
            "RISE-1": "24ska01",  # OVH RISE-1 plan code
            "RISE-2": "24ska02",
            "ADVANCE-1": "24sk30",
            "ADVANCE-2": "24sk40",
        }

        model = bare_metal_config.server_model.upper()
        return model_map.get(model, "24ska01")  # Default to RISE-1
```

**Run Tests (Should Pass)**:

```bash
uv run pytest tests/unit/infrastructure/generators/test_terraform_ovh_generator.py -v
```

---

#### 🔧 REFACTOR: Add Cost Comparison Utility (1 hour)

**Utility**: `src/infrastructure/cost_comparison.py`

```python
"""
Cost Comparison Tool

Compare costs between cloud providers and bare metal.
"""

from dataclasses import dataclass
from typing import Dict
from src.infrastructure.universal_infra_schema import UniversalInfrastructure, CloudProvider


@dataclass
class CostBreakdown:
    """Cost breakdown for a deployment"""
    compute_cost: float
    storage_cost: float
    network_cost: float
    total_monthly: float
    provider: str


class CostComparator:
    """Compare infrastructure costs across providers"""

    def compare_database_hosting(
        self,
        cpu_cores: int,
        ram_gb: int,
        storage_gb: int
    ) -> Dict[str, CostBreakdown]:
        """
        Compare database hosting costs across providers

        Args:
            cpu_cores: Number of CPU cores needed
            ram_gb: RAM in GB
            storage_gb: Storage in GB

        Returns:
            Cost breakdown for each provider
        """
        costs = {}

        # AWS RDS
        costs["aws_rds"] = self._estimate_aws_rds(cpu_cores, ram_gb, storage_gb)

        # GCP Cloud SQL
        costs["gcp_cloud_sql"] = self._estimate_gcp_cloudsql(cpu_cores, ram_gb, storage_gb)

        # OVH Bare Metal
        costs["ovh_bare_metal"] = self._estimate_ovh_bare_metal(cpu_cores, ram_gb, storage_gb)

        # Hetzner Bare Metal
        costs["hetzner_bare_metal"] = self._estimate_hetzner_bare_metal(cpu_cores, ram_gb, storage_gb)

        return costs

    def _estimate_aws_rds(self, cpu_cores: int, ram_gb: int, storage_gb: int) -> CostBreakdown:
        """Estimate AWS RDS costs"""
        # db.r5.2xlarge: 8 vCPU, 64GB RAM = $0.504/hour = $367/month
        # db.r5.4xlarge: 16 vCPU, 128GB RAM = $1.008/hour = $734/month

        # Simple linear estimation
        base_cost_per_gb_ram = 734 / 128  # ~$5.73/GB RAM/month
        compute_cost = ram_gb * base_cost_per_gb_ram

        # Storage: gp3 = $0.115/GB/month
        storage_cost = storage_gb * 0.115

        # Multi-AZ doubles cost
        compute_cost *= 2

        return CostBreakdown(
            compute_cost=compute_cost,
            storage_cost=storage_cost,
            network_cost=20,  # Estimate
            total_monthly=compute_cost + storage_cost + 20,
            provider="AWS RDS"
        )

    def _estimate_gcp_cloudsql(self, cpu_cores: int, ram_gb: int, storage_gb: int) -> CostBreakdown:
        """Estimate GCP Cloud SQL costs"""
        # Similar to AWS, slightly cheaper
        base_cost_per_gb_ram = 5.5
        compute_cost = ram_gb * base_cost_per_gb_ram
        storage_cost = storage_gb * 0.17  # SSD storage

        # HA configuration
        compute_cost *= 2

        return CostBreakdown(
            compute_cost=compute_cost,
            storage_cost=storage_cost,
            network_cost=15,
            total_monthly=compute_cost + storage_cost + 15,
            provider="GCP Cloud SQL"
        )

    def _estimate_ovh_bare_metal(self, cpu_cores: int, ram_gb: int, storage_gb: int) -> CostBreakdown:
        """Estimate OVH bare metal costs"""
        # RISE-1: 8 cores, 128GB RAM, 2x960GB NVMe = €95/month
        # Fixed monthly cost
        if ram_gb <= 128:
            monthly_cost = 95.99
        else:
            monthly_cost = 149.99  # RISE-2 for higher specs

        return CostBreakdown(
            compute_cost=monthly_cost,
            storage_cost=0,  # Included
            network_cost=0,  # Included (1Gbps)
            total_monthly=monthly_cost,
            provider="OVHcloud Bare Metal"
        )

    def _estimate_hetzner_bare_metal(self, cpu_cores: int, ram_gb: int, storage_gb: int) -> CostBreakdown:
        """Estimate Hetzner bare metal costs"""
        # AX41-NVMe: 8 cores, 64GB RAM, 2x512GB NVMe = €43/month
        # AX101: 16 cores, 128GB RAM, 2x1.92TB NVMe = €99/month

        if ram_gb <= 64:
            monthly_cost = 43
        elif ram_gb <= 128:
            monthly_cost = 99
        else:
            monthly_cost = 169  # AX102

        return CostBreakdown(
            compute_cost=monthly_cost,
            storage_cost=0,
            network_cost=0,  # Included (1Gbps)
            total_monthly=monthly_cost,
            provider="Hetzner Bare Metal"
        )

    def print_comparison(self, costs: Dict[str, CostBreakdown]):
        """Print cost comparison table"""
        print("\n=== Infrastructure Cost Comparison ===\n")
        print(f"{'Provider':<25} {'Compute':<12} {'Storage':<12} {'Network':<12} {'Total/Month':<15}")
        print("-" * 80)

        for provider, cost in sorted(costs.items(), key=lambda x: x[1].total_monthly):
            print(f"{cost.provider:<25} ${cost.compute_cost:<11.2f} ${cost.storage_cost:<11.2f} "
                  f"${cost.network_cost:<11.2f} ${cost.total_monthly:<14.2f}")

        # Calculate savings
        most_expensive = max(costs.values(), key=lambda x: x.total_monthly)
        cheapest = min(costs.values(), key=lambda x: x.total_monthly)
        savings_percent = ((most_expensive.total_monthly - cheapest.total_monthly)
                          / most_expensive.total_monthly * 100)

        print(f"\n💰 Potential savings: ${most_expensive.total_monthly - cheapest.total_monthly:.2f}/month "
              f"({savings_percent:.1f}%) by choosing {cheapest.provider} over {most_expensive.provider}")
```

**CLI Integration**: Add to `src/cli/compare.py`

```python
"""CLI command for cost comparison"""

import click
from src.infrastructure.cost_comparison import CostComparator


@click.command()
@click.option('--cpu-cores', type=int, required=True, help='Number of CPU cores')
@click.option('--ram-gb', type=int, required=True, help='RAM in GB')
@click.option('--storage-gb', type=int, required=True, help='Storage in GB')
def compare_costs(cpu_cores: int, ram_gb: int, storage_gb: int):
    """Compare infrastructure costs across providers"""
    comparator = CostComparator()
    costs = comparator.compare_database_hosting(cpu_cores, ram_gb, storage_gb)
    comparator.print_comparison(costs)


if __name__ == '__main__':
    compare_costs()
```

**Usage**:
```bash
# Compare cost for database server
specql compare-costs --cpu-cores 8 --ram-gb 128 --storage-gb 500

# Output:
# === Infrastructure Cost Comparison ===
#
# Provider                  Compute      Storage      Network      Total/Month
# --------------------------------------------------------------------------------
# Hetzner Bare Metal        $99.00       $0.00        $0.00        $99.00
# OVHcloud Bare Metal       $95.99       $0.00        $0.00        $95.99
# GCP Cloud SQL             $1,410.00    $85.00       $15.00       $1,510.00
# AWS RDS                   $1,467.52    $57.50       $20.00       $1,545.02
#
# 💰 Potential savings: $1,449.03/month (93.8%) by choosing OVHcloud Bare Metal over AWS RDS
```

---

**Day 6 Summary**:
- ✅ Bare metal schema defined (`BareMetalConfig`, `PhysicalDrive`, `RAIDConfig`)
- ✅ OVH parser implemented (reverse engineering OVH API → universal format)
- ✅ OVH Terraform generator implemented (universal → OVH Terraform)
- ✅ Cost comparison tool (compare cloud vs bare metal costs)
- ✅ CLI integration for cost comparison
- ✅ Documentation on bare metal vs cloud trade-offs

**Additional Providers** (future work):
- Hetzner parser & generator
- Equinix Metal parser & generator
- Vultr parser & generator

**Lines of Code Added**:
- Schema extensions: ~200 lines
- OVH parser: ~150 lines
- OVH generator: ~300 lines (template + code)
- Cost comparison: ~250 lines
- Tests: ~200 lines
- Documentation: ~300 lines
- **Total: ~1,400 lines**

---

## Week 18 Summary (Updated)

**Achievements**:
- ✅ Universal infrastructure language defined (cloud + bare metal)
- ✅ Pattern library with 20+ infrastructure patterns
- ✅ Reverse engineering from Terraform, Kubernetes, Docker Compose, OVHcloud
- ✅ Generators for 6+ major platforms (AWS, GCP, Azure, K8s, Docker, OVH Bare Metal)
- ✅ CLI commands for infrastructure operations
- ✅ Cost comparison tool (cloud vs bare metal)
- ✅ Managed bare metal support (OVHcloud, extensible to Hetzner, Equinix Metal)

**Lines of Code**:
- Schema: ~1,400 lines (+200 for bare metal)
- Parsers: ~2,150 lines (+150 for OVH)
- Generators: ~3,300 lines (+300 for OVH)
- Patterns: ~3,000 lines (YAML)
- Cost comparison: ~250 lines
- Tests: +200 lines
- **Total: ~10,600 lines**

**Deployment Models Supported**:
- ☁️ Cloud VMs (AWS EC2, GCP Compute, Azure VMs)
- 🐳 Container orchestration (Kubernetes, Docker Compose)
- 🔩 Managed bare metal (OVHcloud, Hetzner, Equinix Metal)
- 📊 Cost optimization across all models

---

## Weeks 19-20: Advanced Features & Integration

### Week 19: Cost Estimation & Optimization
- Integrate cloud pricing APIs
- Automatic cost estimation
- Cost optimization recommendations
- Budget alerts

### Week 20: Multi-Cloud & Semantic Search
- Multi-cloud deployment patterns
- Semantic search across infrastructure patterns
- LLM-powered recommendations
- Complete documentation

---

## Success Metrics

- [ ] Universal language supports 90% of infrastructure patterns (cloud + bare metal)
- [ ] Pattern library with 50+ patterns
- [ ] Reverse engineering from 7+ platforms (AWS, GCP, Azure, K8s, Docker, Terraform, OVH)
- [ ] Generation to 7+ platforms (AWS, GCP, Azure, K8s, Docker, CloudFormation, OVH)
- [ ] Bare metal support for 3+ providers (OVHcloud, Hetzner, Equinix Metal)
- [ ] Cost estimation accurate within 10%
- [ ] Cost comparison tool for cloud vs bare metal
- [ ] Semantic search finds relevant patterns with 80%+ accuracy
- [ ] CLI integrated and documented

---

**Status**: 🔴 Ready to Execute
**Priority**: High (completes universal expressivity vision)
**Expected Output**: Universal infrastructure language with multi-platform support (cloud VMs, containers, and managed bare metal)
