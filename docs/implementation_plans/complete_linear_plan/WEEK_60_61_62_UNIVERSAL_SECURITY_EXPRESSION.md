# Weeks 60-62: Universal Security Expression Language

**Date**: 2025-11-13
**Duration**: 15 days (3 weeks)
**Status**: 🔴 Planning
**Objective**: Create universal expression language for security with tool integrations, reverse engineering, and multi-platform generation

**Prerequisites**: Weeks 18-20 complete (Universal Infrastructure Expression)
**Output**: Universal security YAML, extensible pattern library, tool integrations (CrowdSec, Fail2Ban, WAF), converters for 8+ platforms

---

## 🎯 Executive Summary

Extend SpecQL's architecture to security definition using the **same pattern** as database schemas, CI/CD pipelines, and infrastructure:

1. **Universal Expression** → Business intent for security policies
2. **Pattern Library** → Reusable security patterns with compliance mapping
3. **Reverse Engineering** → Import from AWS IAM, K8s RBAC, firewall configs
4. **Converters** → Universal → All major platforms + security tools
5. **Tool Integration** → CrowdSec, Fail2Ban, WAF, SIEM, vulnerability scanners

### Core Philosophy

```yaml
# Users write SECURITY INTENT (40 lines)
security_policy: backend_api_security
description: "Zero-trust security for production API"
compliance: [SOC2, GDPR]

# Identity & Access
iam:
  roles:
    - name: backend_developer
      permissions:
        - resource: database.prod
          actions: [read, write]
        - resource: api.deploy
          actions: [execute]

    - name: read_only_analyst
      permissions:
        - resource: database.analytics
          actions: [read]

# Network Security
network:
  firewall_rules:
    - name: allow_https
      source: internet
      destination: load_balancer
      ports: [443]
      protocol: tcp

    - name: database_internal_only
      source: application_tier
      destination: database_tier
      ports: [5432]
      deny_all_others: true

# Intrusion Detection (CrowdSec)
intrusion_detection:
  provider: crowdsec
  scenarios:
    - http_bruteforce
    - ssh_bruteforce
    - port_scan
  auto_ban: true
  ban_duration: 4h

# Web Application Firewall
waf:
  provider: modsecurity
  rulesets:
    - owasp_core_rules
    - custom_api_rules
  block_mode: true

# Secrets Management
secrets:
  provider: vault
  rotation: 30d
  encryption: aes_256
  access_control:
    - secret: db_password
      principals: [backend_service]
    - secret: api_keys
      principals: [frontend_service, mobile_app]

# Compliance
compliance:
  frameworks: [SOC2, GDPR]
  policies:
    - encryption_at_rest: required
    - encryption_in_transit: required
    - mfa: required_for_production
    - audit_logging: all_access
    - data_retention: 7y

# SpecQL generates TECHNICAL IMPLEMENTATION (3000+ lines):
# - AWS IAM policies, security groups, WAF rules
# - GCP IAM bindings, firewall rules, Armor policies
# - Azure RBAC, NSGs, Application Gateway WAF
# - Kubernetes RBAC, Network Policies, PSP
# - CrowdSec configuration files
# - ModSecurity WAF rules
# - HashiCorp Vault policies
# - Compliance audit reports
```

### Success Criteria

- [ ] Universal security language defined
- [ ] Pattern library with 50+ security patterns
- [ ] Reverse engineering from AWS IAM, K8s RBAC, iptables, CrowdSec
- [ ] Converters for 8+ platforms/tools
- [ ] CrowdSec, Fail2Ban, ModSecurity integrations
- [ ] Compliance framework mappings (SOC2, HIPAA, GDPR, PCI-DSS)
- [ ] Security posture assessment tool
- [ ] Vulnerability scanning integration
- [ ] Cost comparison for security services

---

## Week 60: Universal Security Language & IAM/RBAC

**Objective**: Define universal expression language for security and implement IAM/RBAC

### Day 1: Universal Security Language Design

**Morning Block (4 hours): Language Specification**

#### 1. Analyze Security Patterns Across Platforms (2 hours)

**Research Document**: `docs/security_research/UNIVERSAL_SECURITY_PATTERNS.md`

```markdown
# Universal Security Patterns

## IAM/RBAC Patterns

### Platform Comparison

| Concept | AWS | GCP | Azure | Kubernetes | PostgreSQL |
|---------|-----|-----|-------|------------|------------|
| Principal | User/Role | User/Service Account | User/Service Principal | User/ServiceAccount | Role/User |
| Permission | Action + Resource | Role + Binding | Role Assignment | Role/ClusterRole | GRANT |
| Policy | IAM Policy | IAM Policy | Policy Definition | RBAC Policy | pg_hba.conf |
| Group | IAM Group | Google Group | Azure AD Group | Group | GROUP |

### Universal Concepts

1. **Principals** (Who)
   - Users
   - Services
   - Applications
   - Machine identities

2. **Resources** (What)
   - Databases
   - APIs
   - Storage
   - Compute
   - Networks

3. **Permissions** (Actions)
   - read
   - write
   - execute
   - delete
   - admin

4. **Conditions** (When/Where)
   - Time-based
   - IP-based
   - MFA-required
   - Environment-specific

## Network Security Patterns

### Firewall Rules (Universal)

```
Source → Destination
  ↓
Protocol + Port
  ↓
Allow / Deny
```

**Platform Implementations**:
- AWS: Security Groups + NACLs
- GCP: VPC Firewall Rules
- Azure: NSGs
- Kubernetes: Network Policies
- Bare Metal: iptables, nftables

### Defense Layers

1. **Perimeter**: WAF, DDoS protection
2. **Network**: Firewall rules, segmentation
3. **Host**: Host-based firewalls, IDS/IPS
4. **Application**: Input validation, authentication
5. **Data**: Encryption, access control

## Intrusion Detection/Prevention

### Tools Comparison

| Tool | Type | Scope | Use Case |
|------|------|-------|----------|
| CrowdSec | IDS/IPS | Host + Network | Modern, collaborative threat intel |
| Fail2Ban | IPS | Host | Log-based brute force prevention |
| Snort | IDS/IPS | Network | Deep packet inspection |
| Suricata | IDS/IPS | Network | High-performance threat detection |
| OSSEC | HIDS | Host | File integrity, log analysis |

### CrowdSec Integration Pattern

```yaml
# CrowdSec is modern, community-driven IDS/IPS
intrusion_detection:
  provider: crowdsec

  # Scenarios (attack patterns)
  scenarios:
    - http_bruteforce       # Detect HTTP brute force
    - ssh_bruteforce        # Detect SSH brute force
    - port_scan             # Detect port scanning
    - http_crawl_bot        # Detect aggressive crawlers
    - http_path_traversal   # Detect path traversal attacks

  # Bouncers (enforcement)
  bouncers:
    - type: firewall        # iptables/nftables integration
      auto_ban: true
      duration: 4h

    - type: cloudflare      # Cloudflare WAF integration
      auto_ban: true
      duration: 24h

  # Community intelligence
  cti:
    enabled: true           # Share attack data with community
    api_key: ${CROWDSEC_API_KEY}
```

## Secrets Management

### Platform Comparison

| Platform | Service | Features |
|----------|---------|----------|
| AWS | Secrets Manager | Rotation, versioning, encryption |
| GCP | Secret Manager | Versioning, IAM integration |
| Azure | Key Vault | Keys, secrets, certificates |
| HashiCorp | Vault | Dynamic secrets, encryption-as-a-service |
| Kubernetes | Secrets | Base64 encoded (use with External Secrets) |

### Universal Pattern

```yaml
secrets:
  - name: database_password
    type: password
    rotation: 30d
    encryption: aes_256_gcm
    access_control:
      - principal: backend_service
        permissions: [read]

  - name: api_signing_key
    type: key_pair
    rotation: 90d
    algorithm: rsa_4096
```

## Compliance Frameworks

### SOC2 Type II Requirements

1. **Access Control**: Role-based, least privilege
2. **Encryption**: At-rest, in-transit
3. **Audit Logging**: All access, immutable logs
4. **Incident Response**: Detection, alerting, remediation
5. **Change Management**: Version control, approval workflows

### GDPR Requirements

1. **Data Minimization**: Collect only necessary data
2. **Right to Erasure**: Delete user data on request
3. **Data Portability**: Export user data
4. **Breach Notification**: Alert within 72 hours
5. **Privacy by Design**: Security built-in

### HIPAA Requirements

1. **Access Control**: Unique user IDs, emergency access
2. **Audit Controls**: Log all PHI access
3. **Integrity**: Data not improperly altered
4. **Transmission Security**: Encryption in-transit
5. **Person Authentication**: Strong authentication mechanisms
```

---

#### 2. Define Universal Security Schema (2 hours)

**Schema**: `src/security/universal_security_schema.py`

```python
"""
Universal Security Schema

Platform-agnostic expression of security that can be converted to:
- AWS IAM, Security Groups, WAF
- GCP IAM, Firewall Rules, Cloud Armor
- Azure RBAC, NSGs, Application Gateway
- Kubernetes RBAC, Network Policies
- CrowdSec, Fail2Ban, ModSecurity
- HashiCorp Vault, PostgreSQL grants
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Literal
from enum import Enum


# ============================================================================
# IAM / RBAC
# ============================================================================

class PrincipalType(str, Enum):
    """Types of security principals"""
    USER = "user"
    SERVICE = "service"
    APPLICATION = "application"
    GROUP = "group"


@dataclass
class Principal:
    """Security principal (user, service, etc.)"""
    name: str
    type: PrincipalType
    email: Optional[str] = None
    groups: List[str] = field(default_factory=list)

    # Authentication
    mfa_required: bool = False
    allowed_ip_ranges: List[str] = field(default_factory=list)


@dataclass
class Permission:
    """Permission to perform actions on resources"""
    resource: str  # Resource pattern (e.g., "database.*", "api.users.read")
    actions: List[str]  # Actions allowed (read, write, execute, delete, admin)

    # Conditions
    conditions: Dict[str, Any] = field(default_factory=dict)
    # Examples:
    # - {"time": {"between": ["09:00", "17:00"]}}
    # - {"ip_address": {"in": ["10.0.0.0/8"]}}
    # - {"mfa": {"required": true}}


@dataclass
class Role:
    """Role with set of permissions"""
    name: str
    description: str
    permissions: List[Permission]

    # Inheritance
    inherits_from: List[str] = field(default_factory=list)

    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class IAMPolicy:
    """Complete IAM/RBAC policy"""
    principals: List[Principal]
    roles: List[Role]
    role_assignments: Dict[str, List[str]]  # principal_name -> role_names

    # Least privilege analysis
    least_privilege_mode: bool = True
    unused_permission_alert: bool = True


# ============================================================================
# Network Security
# ============================================================================

class TrafficDirection(str, Enum):
    """Network traffic direction"""
    INGRESS = "ingress"
    EGRESS = "egress"
    BIDIRECTIONAL = "bidirectional"


class FirewallAction(str, Enum):
    """Firewall rule action"""
    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"


@dataclass
class FirewallRule:
    """Network firewall rule"""
    name: str
    direction: TrafficDirection
    action: FirewallAction

    # Source/Destination
    source: str  # IP range, security group, or tier name
    destination: str

    # Protocol/Port
    protocol: Literal["tcp", "udp", "icmp", "all"]
    ports: List[int] = field(default_factory=list)

    # Priority
    priority: int = 1000

    # Logging
    log_enabled: bool = True


@dataclass
class NetworkSegment:
    """Network segment/tier"""
    name: str
    cidr: str

    # Security zone
    zone: Literal["public", "private", "dmz", "management"]

    # Default policy
    default_ingress: FirewallAction = FirewallAction.DENY
    default_egress: FirewallAction = FirewallAction.ALLOW


@dataclass
class NetworkSecurity:
    """Network security configuration"""
    segments: List[NetworkSegment]
    firewall_rules: List[FirewallRule]

    # Network segmentation
    enable_micro_segmentation: bool = False

    # DDoS protection
    ddos_protection: bool = False


# ============================================================================
# Intrusion Detection/Prevention
# ============================================================================

class IDSProvider(str, Enum):
    """IDS/IPS provider"""
    CROWDSEC = "crowdsec"
    FAIL2BAN = "fail2ban"
    SNORT = "snort"
    SURICATA = "suricata"
    OSSEC = "ossec"


@dataclass
class IntrusionDetection:
    """Intrusion detection/prevention configuration"""
    provider: IDSProvider
    enabled: bool = True

    # CrowdSec specific
    scenarios: List[str] = field(default_factory=list)
    # Examples: http_bruteforce, ssh_bruteforce, port_scan

    # Actions
    auto_ban: bool = True
    ban_duration_hours: int = 4

    # Bouncers (enforcement mechanisms)
    bouncers: List[Dict[str, Any]] = field(default_factory=list)
    # Examples:
    # - {"type": "firewall", "auto_ban": true}
    # - {"type": "cloudflare", "auto_ban": true}
    # - {"type": "nginx", "auto_ban": true}

    # Community Threat Intelligence
    cti_enabled: bool = True
    cti_api_key: Optional[str] = None

    # Alerting
    alert_channels: List[str] = field(default_factory=list)
    # Examples: slack, email, pagerduty


# ============================================================================
# Web Application Firewall (WAF)
# ============================================================================

class WAFProvider(str, Enum):
    """WAF provider"""
    MODSECURITY = "modsecurity"
    AWS_WAF = "aws_waf"
    CLOUDFLARE_WAF = "cloudflare_waf"
    AZURE_WAF = "azure_waf"
    GCP_ARMOR = "gcp_armor"


@dataclass
class WAFConfig:
    """Web Application Firewall configuration"""
    provider: WAFProvider
    enabled: bool = True

    # Rule sets
    rulesets: List[str] = field(default_factory=list)
    # Examples: owasp_core_rules, custom_api_rules

    # Mode
    block_mode: bool = True  # False = detect only

    # Rate limiting
    rate_limiting: Optional[Dict[str, Any]] = None
    # Example: {"requests_per_minute": 100, "burst": 200}

    # Custom rules
    custom_rules: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================================
# Secrets Management
# ============================================================================

class SecretType(str, Enum):
    """Type of secret"""
    PASSWORD = "password"
    API_KEY = "api_key"
    KEY_PAIR = "key_pair"
    CERTIFICATE = "certificate"
    CONNECTION_STRING = "connection_string"


class SecretsProvider(str, Enum):
    """Secrets management provider"""
    VAULT = "vault"  # HashiCorp Vault
    AWS_SECRETS = "aws_secrets"
    GCP_SECRETS = "gcp_secrets"
    AZURE_KEYVAULT = "azure_keyvault"
    KUBERNETES_SECRETS = "kubernetes_secrets"


@dataclass
class Secret:
    """Secret definition"""
    name: str
    type: SecretType

    # Rotation
    rotation_days: int = 90
    auto_rotate: bool = False

    # Encryption
    encryption_algorithm: str = "aes_256_gcm"

    # Access control
    access_control: List[Dict[str, Any]] = field(default_factory=list)
    # Example: [{"principal": "backend_service", "permissions": ["read"]}]

    # Audit
    audit_access: bool = True


@dataclass
class SecretsManagement:
    """Secrets management configuration"""
    provider: SecretsProvider
    secrets: List[Secret]

    # Global settings
    encryption_at_rest: bool = True
    audit_all_access: bool = True

    # Dynamic secrets (Vault)
    dynamic_secrets_enabled: bool = False


# ============================================================================
# Compliance
# ============================================================================

class ComplianceFramework(str, Enum):
    """Compliance frameworks"""
    SOC2 = "soc2"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    NIST = "nist"


@dataclass
class CompliancePolicy:
    """Compliance policy"""
    name: str
    description: str
    enforced: bool = True

    # Controls
    controls: Dict[str, Any] = field(default_factory=dict)
    # Examples:
    # - {"encryption_at_rest": "required"}
    # - {"mfa": "required_for_production"}
    # - {"audit_logging": "all_access"}


@dataclass
class ComplianceConfiguration:
    """Compliance configuration"""
    frameworks: List[ComplianceFramework]
    policies: List[CompliancePolicy]

    # Audit
    audit_logging: bool = True
    log_retention_days: int = 2555  # 7 years for compliance

    # Reports
    generate_reports: bool = True
    report_frequency: str = "monthly"


# ============================================================================
# Vulnerability Scanning
# ============================================================================

@dataclass
class VulnerabilityScanning:
    """Vulnerability scanning configuration"""
    enabled: bool = True

    # Scanners
    image_scanning: bool = True  # Container images
    dependency_scanning: bool = True  # Package dependencies
    sast: bool = True  # Static analysis
    dast: bool = True  # Dynamic analysis

    # Thresholds
    block_on_critical: bool = True
    block_on_high: bool = False

    # Schedule
    schedule: str = "daily"


# ============================================================================
# Complete Security Policy
# ============================================================================

@dataclass
class UniversalSecurity:
    """
    Universal Security Policy

    Platform-agnostic representation that can be converted to:
    - AWS IAM, Security Groups, WAF, Secrets Manager
    - GCP IAM, Firewall, Cloud Armor, Secret Manager
    - Azure RBAC, NSGs, Application Gateway, Key Vault
    - Kubernetes RBAC, Network Policies, Secrets
    - CrowdSec, Fail2Ban, ModSecurity
    - HashiCorp Vault
    """

    # Policy metadata
    name: str
    description: str = ""
    version: str = "1.0"

    # Target environment
    environment: Literal["development", "staging", "production"] = "production"

    # Security domains
    iam: Optional[IAMPolicy] = None
    network: Optional[NetworkSecurity] = None
    intrusion_detection: Optional[IntrusionDetection] = None
    waf: Optional[WAFConfig] = None
    secrets: Optional[SecretsManagement] = None
    compliance: Optional[ComplianceConfiguration] = None
    vulnerability_scanning: Optional[VulnerabilityScanning] = None

    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    pattern_id: Optional[str] = None

    # Analysis
    security_score: Optional[float] = None
    risk_level: Optional[Literal["low", "medium", "high", "critical"]] = None

    def to_aws_iam(self) -> str:
        """Convert to AWS IAM policies"""
        pass

    def to_kubernetes_rbac(self) -> str:
        """Convert to Kubernetes RBAC"""
        pass

    def to_crowdsec_config(self) -> str:
        """Convert to CrowdSec configuration"""
        pass

    def to_modsecurity_rules(self) -> str:
        """Convert to ModSecurity WAF rules"""
        pass

    @classmethod
    def from_aws_iam(cls, iam_policies: str) -> 'UniversalSecurity':
        """Reverse engineer from AWS IAM"""
        pass

    @classmethod
    def from_kubernetes_rbac(cls, rbac_yaml: str) -> 'UniversalSecurity':
        """Reverse engineer from Kubernetes RBAC"""
        pass

    def assess_security_posture(self) -> Dict[str, Any]:
        """Assess security posture and provide recommendations"""
        pass
```

---

**Afternoon Block (4 hours): Pattern Library Foundation**

#### 1. Design Security Pattern Repository (2 hours)

**Repository**: `src/security/pattern_repository.py`

```python
"""
Security Pattern Repository

Stores reusable security patterns with compliance mappings.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from src.security.universal_security_schema import UniversalSecurity, ComplianceFramework


@dataclass
class SecurityPattern:
    """Reusable security pattern"""
    pattern_id: str
    name: str
    description: str
    category: str  # iam, network, zero_trust, compliance, devsecops

    # Pattern definition
    security: UniversalSecurity

    # Compliance
    compliance_frameworks: List[ComplianceFramework]
    compliance_coverage: float  # 0.0 to 1.0

    # Metadata
    tags: List[str]
    use_cases: List[str]

    # Risk profile
    risk_level: str  # low, medium, high
    attack_surface_score: float  # 0.0 (minimal) to 10.0 (extensive)

    # Best practices
    best_practices: List[str]
    anti_patterns: List[str]

    # Semantic search
    embedding: Optional[List[float]] = None

    # Validation
    validation_rules: List[str] = None


@dataclass
class SecurityRecommendation:
    """Security recommendation"""
    title: str
    description: str
    severity: str  # low, medium, high, critical
    category: str
    remediation: str
    references: List[str]
```

---

#### 2. Create Initial Security Patterns (2 hours)

**Pattern Library**: `patterns/security/`

```yaml
# patterns/security/zero_trust_web_app.yaml

pattern_id: "zero_trust_web_app_v1"
name: "Zero Trust Web Application"
description: "Complete zero-trust security for production web application"
category: zero_trust
compliance_frameworks: [SOC2, GDPR]
compliance_coverage: 0.95

# IAM - Least Privilege
iam:
  roles:
    - name: frontend_service
      description: "Frontend service with minimal permissions"
      permissions:
        - resource: api.read
          actions: [GET]
        - resource: cdn.assets
          actions: [read]

    - name: backend_service
      description: "Backend service with database access"
      permissions:
        - resource: database.read_write
          actions: [read, write]
        - resource: secrets.api_keys
          actions: [read]
          conditions:
            mfa: {required: true}

    - name: admin
      description: "Administrator with full access"
      permissions:
        - resource: "*"
          actions: [admin]
          conditions:
            mfa: {required: true}
            ip_address: {in: ["10.0.0.0/8"]}
            time: {between: ["09:00", "17:00"]}

  principals:
    - name: frontend_app
      type: service
      groups: [applications]
      mfa_required: false

    - name: backend_app
      type: service
      groups: [applications]
      mfa_required: true

    - name: admin_user
      type: user
      email: admin@company.com
      groups: [admins]
      mfa_required: true
      allowed_ip_ranges: ["10.0.0.0/8"]

  role_assignments:
    frontend_app: [frontend_service]
    backend_app: [backend_service]
    admin_user: [admin]

# Network Security - Micro-segmentation
network:
  segments:
    - name: public_tier
      cidr: 10.0.1.0/24
      zone: public
      default_ingress: deny
      default_egress: allow

    - name: application_tier
      cidr: 10.0.10.0/24
      zone: private
      default_ingress: deny
      default_egress: deny

    - name: database_tier
      cidr: 10.0.20.0/24
      zone: private
      default_ingress: deny
      default_egress: deny

  firewall_rules:
    # Public → Frontend
    - name: allow_https_public
      direction: ingress
      action: allow
      source: internet
      destination: public_tier
      protocol: tcp
      ports: [443]
      priority: 100

    # Frontend → Backend (internal only)
    - name: allow_frontend_to_backend
      direction: ingress
      action: allow
      source: public_tier
      destination: application_tier
      protocol: tcp
      ports: [8080]
      priority: 200

    # Backend → Database (encrypted)
    - name: allow_backend_to_database
      direction: ingress
      action: allow
      source: application_tier
      destination: database_tier
      protocol: tcp
      ports: [5432]
      priority: 300

    # Deny all other traffic
    - name: deny_all
      direction: bidirectional
      action: deny
      source: "*"
      destination: "*"
      protocol: all
      priority: 10000

  enable_micro_segmentation: true
  ddos_protection: true

# Intrusion Detection - CrowdSec
intrusion_detection:
  provider: crowdsec
  enabled: true

  scenarios:
    - http_bruteforce
    - ssh_bruteforce
    - port_scan
    - http_crawl_bot
    - http_path_traversal
    - http_sqli
    - http_xss

  auto_ban: true
  ban_duration_hours: 4

  bouncers:
    - type: firewall
      auto_ban: true
    - type: cloudflare
      auto_ban: true
      duration: 24h

  cti_enabled: true

  alert_channels:
    - slack
    - pagerduty

# Web Application Firewall
waf:
  provider: modsecurity
  enabled: true

  rulesets:
    - owasp_core_rules
    - owasp_crs_v3.3
    - custom_api_rules

  block_mode: true

  rate_limiting:
    requests_per_minute: 100
    burst: 200
    per_ip: true

  custom_rules:
    - name: block_sql_injection
      pattern: "(?i)(union|select|insert|update|delete|drop).*from"
      action: block

    - name: block_xss
      pattern: "(?i)<script|javascript:|onerror="
      action: block

# Secrets Management - Vault
secrets:
  provider: vault

  secrets:
    - name: database_password
      type: password
      rotation_days: 30
      auto_rotate: true
      encryption_algorithm: aes_256_gcm
      access_control:
        - principal: backend_service
          permissions: [read]
      audit_access: true

    - name: api_signing_key
      type: key_pair
      rotation_days: 90
      auto_rotate: true
      encryption_algorithm: rsa_4096
      access_control:
        - principal: backend_service
          permissions: [read]
        - principal: frontend_service
          permissions: [read]

    - name: tls_certificates
      type: certificate
      rotation_days: 365
      auto_rotate: true
      access_control:
        - principal: load_balancer
          permissions: [read]

  encryption_at_rest: true
  audit_all_access: true
  dynamic_secrets_enabled: true

# Compliance
compliance:
  frameworks: [SOC2, GDPR]

  policies:
    - name: encryption_at_rest
      description: "All data must be encrypted at rest"
      enforced: true
      controls:
        storage_encryption: required
        database_encryption: required

    - name: encryption_in_transit
      description: "All data must be encrypted in transit"
      enforced: true
      controls:
        tls_version: "1.3"
        certificate_validation: required

    - name: mfa_production
      description: "MFA required for all production access"
      enforced: true
      controls:
        mfa_for_admin: required
        mfa_for_sensitive_data: required

    - name: audit_logging
      description: "All access must be logged"
      enforced: true
      controls:
        log_all_access: required
        log_retention_days: 2555  # 7 years

    - name: data_retention
      description: "Data retention policy"
      enforced: true
      controls:
        retention_days: 2555
        secure_deletion: required

  audit_logging: true
  log_retention_days: 2555
  generate_reports: true
  report_frequency: monthly

# Vulnerability Scanning
vulnerability_scanning:
  enabled: true
  image_scanning: true
  dependency_scanning: true
  sast: true
  dast: true
  block_on_critical: true
  block_on_high: false
  schedule: daily

# Best Practices
best_practices:
  - "Least privilege access - users only have minimum required permissions"
  - "Zero trust network - all traffic authenticated and encrypted"
  - "Defense in depth - multiple security layers (WAF, IDS, firewall)"
  - "Secrets rotation - automatic rotation every 30-90 days"
  - "MFA enforcement - required for all production access"
  - "Audit logging - all access logged and retained for 7 years"
  - "Network segmentation - services isolated in separate tiers"
  - "Intrusion detection - CrowdSec monitors and blocks attacks"
  - "Vulnerability scanning - daily scans with critical blocking"
  - "Compliance automation - SOC2 and GDPR requirements enforced"

anti_patterns:
  - "Wildcard permissions (resource: '*', actions: '*')"
  - "Shared credentials across environments"
  - "No MFA for production access"
  - "Firewall rules allowing all traffic (0.0.0.0/0 → 0.0.0.0/0)"
  - "Secrets in source code or config files"
  - "No audit logging"
  - "Flat network (no segmentation)"
  - "Disabled intrusion detection"
  - "No vulnerability scanning"

tags: [zero_trust, web_application, soc2, gdpr, production]
use_cases:
  - "SaaS web applications"
  - "Customer-facing APIs"
  - "E-commerce platforms"
  - "Healthcare applications (HIPAA)"
  - "Financial services (PCI-DSS)"

risk_level: low
attack_surface_score: 2.5  # Out of 10.0 (lower is better)
```

---

**More Patterns**:

```bash
patterns/security/
├── zero_trust_web_app.yaml
├── least_privilege_database.yaml
├── soc2_compliant_saas.yaml
├── hipaa_healthcare_system.yaml
├── pci_dss_payment_processing.yaml
├── kubernetes_security_hardening.yaml
├── devsecops_pipeline.yaml
├── multi_cloud_security.yaml
└── bare_metal_server_hardening.yaml
```

---

**Day 1 Summary**:
- ✅ Universal security schema defined
- ✅ Common patterns analyzed across platforms
- ✅ Pattern library structure created
- ✅ 10+ initial security patterns drafted
- ✅ CrowdSec, WAF, Vault integration designed

---

### Day 2: Reverse Engineering - AWS IAM Parser

**Objective**: Parse AWS IAM policies to universal format

**Morning Block (4 hours): AWS IAM Parser**

#### 🔴 RED: Parser Tests (2 hours)

**Test File**: `tests/unit/security/parsers/test_aws_iam_parser.py`

```python
"""Tests for AWS IAM → Universal Security parser"""

import pytest
from src.security.parsers.aws_iam_parser import AWSIAMParser
from src.security.universal_security_schema import *


class TestAWSIAMParser:
    """Test parsing AWS IAM to universal format"""

    @pytest.fixture
    def parser(self):
        return AWSIAMParser()

    def test_parse_simple_iam_policy(self, parser):
        """Test parsing basic AWS IAM policy"""
        iam_policy = """
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
"""

        # Act
        security = parser.parse_policy(iam_policy)

        # Assert
        assert security.iam is not None
        assert len(security.iam.roles) > 0

        role = security.iam.roles[0]
        assert len(role.permissions) > 0
        assert "s3" in role.permissions[0].resource.lower()

    def test_parse_role_with_trust_policy(self, parser):
        """Test parsing IAM role with trust relationship"""
        role_json = """
{
  "RoleName": "BackendService",
  "AssumeRolePolicyDocument": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
}
"""

        # Act
        security = parser.parse_role(role_json)

        # Assert
        assert security.iam.principals[0].name == "BackendService"
        assert security.iam.principals[0].type == PrincipalType.SERVICE
```

---

#### 🟢 GREEN: Implement AWS IAM Parser (2 hours)

**Parser**: `src/security/parsers/aws_iam_parser.py`

```python
"""
AWS IAM Parser

Reverse engineers AWS IAM policies to universal security format.
"""

import json
from typing import Dict, Any, List
from src.security.universal_security_schema import *


class AWSIAMParser:
    """Parse AWS IAM policies to universal format"""

    def parse_policy(self, iam_policy_json: str) -> UniversalSecurity:
        """
        Parse AWS IAM policy to UniversalSecurity

        Args:
            iam_policy_json: AWS IAM policy JSON

        Returns:
            UniversalSecurity object
        """
        policy = json.loads(iam_policy_json)

        # Parse statements
        statements = policy.get("Statement", [])
        permissions = self._parse_statements(statements)

        # Create role
        role = Role(
            name="imported_role",
            description="Imported from AWS IAM",
            permissions=permissions
        )

        iam_policy = IAMPolicy(
            principals=[],
            roles=[role],
            role_assignments={}
        )

        return UniversalSecurity(
            name="aws_iam_import",
            description="Imported from AWS IAM policy",
            iam=iam_policy
        )

    def _parse_statements(self, statements: List[Dict]) -> List[Permission]:
        """Parse IAM statements to permissions"""
        permissions = []

        for statement in statements:
            if statement.get("Effect") != "Allow":
                continue

            # Extract actions and resources
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            resources = statement.get("Resource", [])
            if isinstance(resources, str):
                resources = [resources]

            for resource in resources:
                # Map AWS actions to universal actions
                universal_actions = self._map_aws_actions(actions)

                permissions.append(Permission(
                    resource=self._simplify_resource(resource),
                    actions=universal_actions
                ))

        return permissions

    def _map_aws_actions(self, aws_actions: List[str]) -> List[str]:
        """Map AWS actions to universal actions"""
        action_map = {
            "Get": "read",
            "List": "read",
            "Describe": "read",
            "Put": "write",
            "Create": "write",
            "Update": "write",
            "Delete": "delete",
            "*": "admin"
        }

        universal_actions = set()
        for action in aws_actions:
            if ":" in action:
                _, action_name = action.split(":", 1)
            else:
                action_name = action

            # Check each mapping
            for aws_prefix, universal_action in action_map.items():
                if action_name.startswith(aws_prefix) or action_name == "*":
                    universal_actions.add(universal_action)

        return list(universal_actions)

    def _simplify_resource(self, arn: str) -> str:
        """Simplify AWS ARN to universal resource pattern"""
        # arn:aws:s3:::my-bucket/* → s3.my-bucket.*
        if arn == "*":
            return "*"

        parts = arn.split(":")
        if len(parts) >= 6:
            service = parts[2]
            resource = parts[5] if len(parts) > 5 else "*"
            return f"{service}.{resource}"

        return arn
```

---

**Afternoon Block (4 hours): Kubernetes RBAC Parser**

Similar structure for parsing Kubernetes RBAC to universal format.

**Day 2 Summary**:
- ✅ AWS IAM parser complete
- ✅ Kubernetes RBAC parser complete
- ✅ Can reverse engineer 2 major IAM platforms
- ✅ Foundation for additional parsers

---

### Days 3-5: Generators, Tool Integrations & CLI

**Day 3**:
- AWS IAM generator
- GCP IAM generator
- Azure RBAC generator

**Day 4**:
- Kubernetes RBAC generator
- **CrowdSec configuration generator**
- **ModSecurity WAF rules generator**
- **HashiCorp Vault policies generator**

**Day 5**:
- CLI integration (`specql security generate`, `specql security assess`)
- Security posture assessment tool
- Compliance validation
- Documentation

---

## Week 60 Summary

**Achievements**:
- ✅ Universal security language defined
- ✅ IAM/RBAC schema complete
- ✅ Pattern library with 10+ security patterns
- ✅ Reverse engineering from AWS IAM, K8s RBAC
- ✅ Generators for 4+ IAM platforms
- ✅ CrowdSec, ModSecurity, Vault integration designed
- ✅ Compliance framework mappings

**Lines of Code**:
- Schema: ~1,500 lines
- Parsers: ~1,000 lines
- Generators: ~1,500 lines
- Patterns: ~2,000 lines (YAML)
- **Total: ~6,000 lines**

---

## Week 61: Network Security & Tool Integrations

### Focus Areas:

1. **Network Security Generation**
   - AWS Security Groups
   - GCP Firewall Rules
   - Azure NSGs
   - Kubernetes Network Policies
   - iptables/nftables (bare metal)

2. **CrowdSec Integration**
   - Configuration file generation
   - Scenario deployment
   - Bouncer setup (firewall, Cloudflare, nginx)
   - Community Threat Intelligence (CTI) integration
   - Alert integration (Slack, PagerDuty)

3. **WAF Integration**
   - ModSecurity rules generation
   - AWS WAF rules
   - Cloudflare WAF
   - GCP Cloud Armor
   - OWASP Core Rule Set integration

4. **Fail2Ban Integration**
   - jail.conf generation
   - Filter patterns
   - Action scripts
   - Integration with CrowdSec

---

## Week 62: Compliance, Scanning & Advanced Features

### Focus Areas:

1. **Compliance Automation**
   - SOC2 compliance validation
   - HIPAA compliance validation
   - GDPR compliance validation
   - PCI-DSS compliance validation
   - Automated compliance reports

2. **Vulnerability Scanning Integration**
   - Trivy (container scanning)
   - Snyk (dependency scanning)
   - OWASP Dependency-Check
   - Bandit (Python SAST)
   - SonarQube integration

3. **Security Posture Assessment**
   - Automated security scoring
   - Risk level calculation
   - Attack surface analysis
   - Security recommendations
   - Remediation guidance

4. **LLM-Powered Security**
   - Semantic search for security patterns
   - LLM-powered threat modeling
   - Security policy recommendations
   - Vulnerability impact analysis

---

## Success Metrics

- [ ] Universal security language supports 90% of security patterns
- [ ] Pattern library with 50+ security patterns
- [ ] Reverse engineering from 5+ platforms (AWS, GCP, Azure, K8s, iptables)
- [ ] Generation to 8+ platforms/tools
- [ ] CrowdSec full integration (config, scenarios, bouncers, CTI)
- [ ] Fail2Ban integration
- [ ] ModSecurity WAF rules generation
- [ ] HashiCorp Vault policies generation
- [ ] 4+ compliance frameworks supported (SOC2, HIPAA, GDPR, PCI-DSS)
- [ ] Security posture assessment with scoring
- [ ] Vulnerability scanning integration (3+ tools)
- [ ] LLM-powered security recommendations
- [ ] CLI integrated and documented

---

## Tool Integration Examples

### CrowdSec Configuration Generation

```yaml
# Universal security → CrowdSec config
intrusion_detection:
  provider: crowdsec
  scenarios:
    - http_bruteforce
    - ssh_bruteforce

# SpecQL generates: /etc/crowdsec/config.yaml
```

```yaml
# Generated CrowdSec config
api:
  server:
    listen_uri: 0.0.0.0:8080

common:
  daemonize: false
  log_media: stdout
  log_level: info

crowdsec_service:
  acquisition_path: /etc/crowdsec/acquis.yaml
  parser_routines: 1

db_config:
  type: sqlite
  db_path: /var/lib/crowdsec/data/crowdsec.db

cscli:
  output: human

# Scenarios
scenarios:
  - crowdsecurity/http-bruteforce
  - crowdsecurity/ssh-bruteforce
  - crowdsecurity/http-crawl-non-statics
  - crowdsecurity/http-path-traversal-probing

# Bouncers
bouncers:
  firewall:
    api_url: http://localhost:8080
    api_key: ${CROWDSEC_BOUNCER_KEY}
```

### ModSecurity WAF Rules

```yaml
# Universal security → ModSecurity rules
waf:
  provider: modsecurity
  rulesets:
    - owasp_core_rules

# SpecQL generates: /etc/modsec/rules.conf
```

```apache
# Generated ModSecurity rules
SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess Off

# OWASP Core Rule Set
Include /usr/share/modsecurity-crs/crs-setup.conf
Include /usr/share/modsecurity-crs/rules/*.conf

# Custom rules
SecRule REQUEST_URI "@rx (?i)(union|select|insert)" \
    "id:1001,\
    phase:2,\
    deny,\
    status:403,\
    msg:'SQL Injection Detected'"
```

---

**Status**: 🔴 Ready to Execute
**Priority**: High (completes security automation vision)
**Expected Output**: Universal security language with compliance automation and tool integrations
