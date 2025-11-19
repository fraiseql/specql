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
    volumes: List["Volume"] = field(default_factory=list)

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

    buckets: List["Bucket"] = field(default_factory=list)


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
    alerts: List["Alert"] = field(default_factory=list)


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

"""
Tier-Based Security Model:

The security system follows a tier-based architecture where network segments
(web, api, database, admin) communicate through controlled firewall rules.
This enables defense-in-depth security across multi-tier applications.

Key Concepts:
- NetworkTier: Logical grouping of resources with shared security policies
- FirewallRule: Cloud-agnostic firewall rules that translate to provider-specific rules
- CompliancePreset: Pre-configured security standards (PCI-DSS, HIPAA, etc.)
- WAFConfig: Web Application Firewall settings for HTTP/HTTPS protection
- VPNConfig: Private connectivity configuration

Example Usage:
    security:
      network_tiers:
        - name: web
          firewall_rules:
            - name: allow-http
              protocol: tcp
              ports: [80, 443]
              source: internet
              action: allow
        - name: api
          firewall_rules:
            - name: allow-from-web
              protocol: tcp
              ports: [8080]
              source: web  # References tier name
              action: allow
"""


@dataclass
class FirewallRule:
    """Universal firewall rule (cloud-agnostic)"""

    name: str
    protocol: Literal["tcp", "udp", "icmp", "all"]
    ports: List[int] = field(default_factory=list)
    port_ranges: List[str] = field(default_factory=list)  # e.g., "8000-9000"
    source: str = "0.0.0.0/0"  # CIDR or tier name
    destination: str = "self"  # CIDR or tier name
    action: Literal["allow", "deny"] = "allow"
    priority: int = 1000
    description: str = ""

    def __post_init__(self):
        """Validate firewall rule after initialization"""
        if self.protocol not in ["tcp", "udp", "icmp", "all"]:
            raise ValueError(f"Invalid protocol: {self.protocol}")
        if self.action not in ["allow", "deny"]:
            raise ValueError(f"Invalid action: {self.action}")
        if self.ports and self.port_ranges:
            raise ValueError("Cannot specify both ports and port_ranges")

    @property
    def all_ports(self) -> List[int]:
        """Get all ports covered by this rule"""
        ports = self.ports.copy()
        for port_range in self.port_ranges:
            if "-" in port_range:
                start, end = map(int, port_range.split("-"))
                ports.extend(range(start, end + 1))
        return sorted(list(set(ports)))


@dataclass
class NetworkTier:
    """Network tier for multi-tier architectures"""

    name: str  # web, api, database, admin
    cidr_blocks: List[str] = field(default_factory=list)
    firewall_rules: List[FirewallRule] = field(default_factory=list)

    def __post_init__(self):
        """Validate network tier after initialization"""
        if not self.name:
            raise ValueError("Network tier name cannot be empty")
        # Basic CIDR validation
        for cidr in self.cidr_blocks:
            if not self._is_valid_cidr(cidr):
                raise ValueError(f"Invalid CIDR block: {cidr}")

    @staticmethod
    def _is_valid_cidr(cidr: str) -> bool:
        """Basic CIDR validation"""
        import ipaddress

        try:
            ipaddress.ip_network(cidr, strict=False)
            return True
        except ValueError:
            return False

    def get_inbound_rules(self) -> List[FirewallRule]:
        """Get all inbound firewall rules for this tier"""
        return [
            rule
            for rule in self.firewall_rules
            if rule.destination == self.name or rule.destination == "self"
        ]

    def get_outbound_rules(self) -> List[FirewallRule]:
        """Get all outbound firewall rules for this tier"""
        return [
            rule
            for rule in self.firewall_rules
            if rule.source == self.name or rule.source == "self"
        ]


class CompliancePreset(str, Enum):
    """Security compliance presets"""

    STANDARD = "standard"
    HARDENED = "hardened"
    PCI_DSS = "pci-compliant"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


@dataclass
class WAFConfig:
    """Web Application Firewall configuration"""

    enabled: bool = False
    mode: Literal["detection", "prevention"] = "prevention"
    rule_sets: List[str] = field(default_factory=lambda: ["OWASP_TOP_10"])
    rate_limiting: bool = True
    geo_blocking: List[str] = field(default_factory=list)  # ISO country codes
    ip_blacklist: List[str] = field(default_factory=list)
    ip_whitelist: List[str] = field(default_factory=list)


@dataclass
class VPNConfig:
    """VPN/Private connectivity configuration"""

    enabled: bool = False
    type: Literal["site-to-site", "client-vpn", "private-link"] = "site-to-site"
    remote_cidr: str = "192.168.0.0/16"
    bgp_asn: Optional[int] = None


@dataclass
class SecurityConfig:
    """Security configuration"""

    # Secrets
    secrets_provider: Literal["aws_secrets", "gcp_secrets", "azure_keyvault", "vault"] = (
        "aws_secrets"
    )
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

    # Enhanced security primitives
    network_tiers: List[NetworkTier] = field(default_factory=list)
    firewall_rules: List[FirewallRule] = field(default_factory=list)
    compliance_preset: Optional[CompliancePreset] = None
    waf: WAFConfig = field(default_factory=WAFConfig)
    vpn: VPNConfig = field(default_factory=VPNConfig)


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
        return ""

    def to_terraform_gcp(self) -> str:
        """Convert to Terraform for GCP"""
        return ""

    def to_kubernetes(self) -> str:
        """Convert to Kubernetes manifests"""
        return ""

    def to_docker_compose(self) -> str:
        """Convert to Docker Compose"""
        return ""

    @classmethod
    def from_terraform(cls, tf_content: str) -> "UniversalInfrastructure":
        """Reverse engineer from Terraform"""
        # Placeholder implementation
        return cls(name="placeholder")

    @classmethod
    def from_kubernetes(cls, k8s_manifests: str) -> "UniversalInfrastructure":
        """Reverse engineer from Kubernetes"""
        # Placeholder implementation
        return cls(name="placeholder")
