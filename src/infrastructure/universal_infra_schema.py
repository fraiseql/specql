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


# Forward declarations for cost estimation
@dataclass
class CostBreakdown:
    """Detailed cost breakdown by resource type"""
    compute_cost: float = 0.0
    database_cost: float = 0.0
    storage_cost: float = 0.0
    network_cost: float = 0.0
    load_balancer_cost: float = 0.0
    monitoring_cost: float = 0.0
    total_monthly_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compute_cost": round(self.compute_cost, 2),
            "database_cost": round(self.database_cost, 2),
            "storage_cost": round(self.storage_cost, 2),
            "network_cost": round(self.network_cost, 2),
            "load_balancer_cost": round(self.load_balancer_cost, 2),
            "monitoring_cost": round(self.monitoring_cost, 2),
            "total_monthly_cost": round(self.total_monthly_cost, 2)
        }


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
    OVHCLOUD = "ovhcloud"
    HETZNER = "hetzner"


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
    volumes: List['Volume'] = field(default_factory=list)

    # Resource limits
    cpu_limit: Optional[float] = None
    memory_limit: Optional[str] = None
    cpu_request: Optional[float] = None
    memory_request: Optional[str] = None

    # Health checks
    health_check_path: str = "/health"
    health_check_interval: int = 30  # seconds
    readiness_check_path: str = "/ready"


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
    origin_domain: str
    enabled: bool = False
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
# Bare Metal Support
# ============================================================================

@dataclass
class BareMetalConfig:
    """Bare metal server configuration"""

    # Server specifications
    server_model: str  # e.g., "AX41", "CPX11", "KS-1"
    cpu_cores: int
    ram_gb: int
    storage_type: Literal["hdd", "ssd", "nvme"] = "ssd"
    storage_gb: int = 0  # 0 means use default for model

    # OS installation
    os: str = "ubuntu2204"  # OS template identifier
    ssh_keys: List[str] = field(default_factory=list)  # SSH key fingerprints

    # Network configuration
    private_network: bool = False
    ipv6: bool = False

    # Additional services
    backup_service: bool = False
    monitoring: bool = False

    # Provider-specific options
    datacenter: Optional[str] = None  # Specific datacenter location
    bandwidth: Optional[str] = None  # Bandwidth allocation


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
    bare_metal: Optional[BareMetalConfig] = None

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
        try:
            from .generators.terraform_aws_generator import TerraformAWSGenerator
            generator = TerraformAWSGenerator()
            return generator.generate(self)
        except ImportError:
            return ""

    def to_terraform_gcp(self) -> str:
        """Convert to Terraform for GCP"""
        try:
            from .generators.terraform_gcp_generator import TerraformGCPGenerator
            generator = TerraformGCPGenerator()
            return generator.generate(self)
        except ImportError:
            return ""

    def to_terraform_azure(self) -> str:
        """Convert to Terraform for Azure"""
        try:
            from .generators.terraform_azure_generator import TerraformAzureGenerator
            generator = TerraformAzureGenerator()
            return generator.generate(self)
        except ImportError:
            return ""

    def to_cloudformation(self) -> str:
        """Convert to AWS CloudFormation"""
        try:
            from .generators.cloudformation_generator import CloudFormationGenerator
            generator = CloudFormationGenerator()
            return generator.generate(self)
        except ImportError:
            return ""

    def to_pulumi(self) -> str:
        """Convert to Pulumi Python"""
        try:
            from .generators.pulumi_generator import PulumiGenerator
            generator = PulumiGenerator()
            return generator.generate(self)
        except ImportError:
            return ""

    def to_kubernetes(self) -> str:
        """Convert to Kubernetes manifests"""
        try:
            from .generators.kubernetes_generator import KubernetesGenerator
            generator = KubernetesGenerator()
            return generator.generate(self)
        except ImportError:
            return ""

    def to_ovhcloud(self) -> str:
        """Convert to OVHcloud provisioning script"""
        try:
            from .generators.ovhcloud_generator import OVHcloudGenerator
            generator = OVHcloudGenerator()
            return generator.generate(self)
        except ImportError:
            return ""

    def to_hetzner(self) -> str:
        """Convert to Hetzner provisioning script"""
        try:
            from .generators.hetzner_generator import HetznerGenerator
            generator = HetznerGenerator()
            return generator.generate(self)
        except ImportError:
            return ""

    def to_docker_compose(self) -> str:
        """Convert to Docker Compose"""
        return ""

    def estimate_cost(self) -> 'CostBreakdown':
        """Estimate monthly cost for this infrastructure"""
        from .services.cost_estimation_service import CostEstimationService
        service = CostEstimationService()
        return service.estimate_cost(self)

    def get_cost_comparison(self) -> Dict[str, 'CostBreakdown']:
        """Get cost estimates across all supported providers"""
        from .services.cost_estimation_service import CostEstimationService
        service = CostEstimationService()
        return service.get_cost_comparison(self)

    @classmethod
    def from_terraform(cls, tf_content: str) -> 'UniversalInfrastructure':
        """Reverse engineer from Terraform"""
        # Placeholder implementation
        return cls(name="placeholder")

    @classmethod
    def from_kubernetes(cls, k8s_manifests: str) -> 'UniversalInfrastructure':
        """Reverse engineer from Kubernetes"""
        # Placeholder implementation
        return cls(name="placeholder")