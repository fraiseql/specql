# Weeks 71-72: Platform-Agnostic Infrastructure & European Cloud Sovereignty

**Date**: 2025-11-13
**Duration**: 10 days (2 weeks)
**Status**: 🔴 Planning
**Objective**: True infrastructure freedom - Scaleway, OVH, Hetzner compete equally with AWS/GCP/Azure, plus self-hosted

**Prerequisites**: Week 69-70 complete (European-first architecture)
**Output**: Universal infrastructure DSL generating code for any platform, European providers as first-class citizens

---

## 🎯 Executive Summary

**Problem**: Current "European-first" still uses AWS (US company). True sovereignty requires **European cloud providers** as equals, not afterthoughts.

### Infrastructure Democracy

```
Traditional Approach:                SpecQL Approach:
    ↓                                       ↓
AWS is default                       NO DEFAULT
Other clouds = "alternatives"        ALL PLATFORMS EQUAL
European clouds = second-class       European clouds = first-class
Self-hosting = unsupported          Self-hosting = supported
Vendor lock-in encouraged           Vendor independence guaranteed
```

### Supported Platforms (Equal Priority)

**European Providers**:
1. 🇫🇷 **Scaleway** - French cloud, GDPR-native, competitive pricing
2. 🇫🇷 **OVH Cloud** - Managed cloud (not just bare metal), multi-region
3. 🇩🇪 **Hetzner Cloud** - German, best price/performance, Nuremberg/Helsinki
4. 🇫🇮 **UpCloud** - Finnish, high-performance, GDPR-compliant

**US Hyperscalers** (Equal, not preferred):
5. 🇺🇸 **AWS** - If user explicitly chooses
6. 🇺🇸 **Google Cloud** - If user explicitly chooses
7. 🇺🇸 **Microsoft Azure** - If user explicitly chooses

**Self-Hosted**:
8. 🏠 **Coolify** - Self-hosted PaaS, full control
9. 🏠 **Bare Metal** - Direct server management

### The Use Case Matcher

SpecQL analyzes requirements and recommends optimal platform:

```yaml
use_case: startup_mvp
requirements:
  - budget: low
  - compliance: GDPR
  - scale: <10k users
  - region: Europe

# SpecQL recommends:
recommended_platform: hetzner
reasoning: |
  Hetzner offers best price/performance for European startups.
  €40/month for production-grade setup vs €500/month AWS equivalent.
  GDPR-compliant, German data centers, excellent network.

alternatives:
  - platform: scaleway
    reason: More managed services, easier scaling
    cost: +30%
  - platform: ovh
    reason: More locations (32 regions), enterprise support
    cost: +50%
```

```yaml
use_case: enterprise_saas
requirements:
  - budget: high
  - compliance: GDPR + SOC2 + ISO27001
  - scale: 1M+ users
  - region: Global
  - need: Multi-region HA

# SpecQL recommends:
recommended_platform: ovh_cloud
reasoning: |
  OVH provides enterprise-grade infrastructure with European sovereignty.
  32 data centers globally, SOC2 Type II certified, 99.99% SLA.
  Cost: 40% less than AWS, better support for European customers.

alternatives:
  - platform: aws
    reason: More managed services (RDS, Lambda, etc.)
    cost: +40%
  - platform: azure
    reason: Better Windows support, Microsoft integrations
    cost: +35%
```

```yaml
use_case: privacy_first_app
requirements:
  - budget: medium
  - compliance: GDPR + zero US jurisdiction
  - scale: 100k users
  - region: EU-only
  - need: Maximum data sovereignty

# SpecQL recommends:
recommended_platform: scaleway
reasoning: |
  Scaleway: 100% French company, EU jurisdiction only.
  No CLOUD Act exposure, no US government access.
  Paris + Amsterdam data centers, full GDPR compliance.
  Cost competitive with Hetzner, more managed services.

alternatives:
  - platform: hetzner
    reason: Lower cost, but limited managed services
    cost: -25%
  - platform: coolify_selfhosted
    reason: Maximum control, zero vendor dependency
    cost: Variable (infrastructure + ops time)
```

---

## 🏗️ Universal Infrastructure DSL

### Abstraction Layers

```
User YAML (Universal)
        ↓
  Platform-Agnostic AST
        ↓
    ┌───┴───┬───────┬────────┬─────────┬────────┐
    ↓       ↓       ↓        ↓         ↓        ↓
Scaleway  OVH   Hetzner  AWS/GCP  Azure  Coolify
  IaC     IaC     IaC      IaC     IaC    Docker
```

### Universal Infrastructure Specification

```yaml
# infrastructure.specql.yaml
# Platform-agnostic infrastructure definition

infrastructure:
  name: "Production SpecQL"

  # Let SpecQL choose, or specify explicitly
  platform: auto  # or: scaleway, ovh, hetzner, aws, gcp, azure, coolify

  # Requirements (SpecQL uses these to recommend platform)
  requirements:
    legislation: EU
    data_residency: EU_ONLY
    budget: medium
    scale: high
    compliance:
      - GDPR
      - NIS2
      - ISO27001

  # Universal resource definitions
  resources:
    # Database (translates to managed DB on any platform)
    - type: postgresql
      name: specql-production
      version: "16"
      size: medium  # Universal size: small/medium/large/xlarge

      storage: 500GB
      backups:
        retention: 30_days
        frequency: daily

      high_availability: true
      encryption: required

      # Auto-translated to platform-specific:
      # Scaleway: Database for PostgreSQL
      # OVH: Public Cloud Databases
      # Hetzner: Managed PostgreSQL (via partner)
      # AWS: RDS PostgreSQL
      # Coolify: PostgreSQL container + backup script

    # Object storage (translates to S3-compatible on any platform)
    - type: object_storage
      name: specql-data
      size: 1TB

      versioning: true
      encryption: required
      public_access: blocked

      lifecycle:
        - after: 90_days
          action: move_to_cold_storage
        - after: 365_days
          action: delete

      # Auto-translated to:
      # Scaleway: Object Storage
      # OVH: Object Storage
      # Hetzner: S3-compatible storage
      # AWS: S3
      # Coolify: MinIO

    # Compute (translates to VMs/containers on any platform)
    - type: compute
      name: api-servers
      count: 3

      size: medium  # Universal: 4 vCPU, 8GB RAM
      os: ubuntu_22_04

      auto_scaling:
        min: 3
        max: 10
        metric: cpu
        threshold: 70

      # Auto-translated to:
      # Scaleway: Instances
      # OVH: Public Cloud Instances
      # Hetzner: Cloud Servers
      # AWS: EC2
      # Coolify: Docker containers

    # Load balancer
    - type: load_balancer
      name: api-lb
      type: application  # L7

      ssl: automatic
      health_check:
        path: /health
        interval: 30s

      # Auto-translated to platform-specific LB

    # CDN
    - type: cdn
      name: static-assets
      origin: object_storage.specql-data

      cache_ttl: 1_hour
      geo_restriction: none

      # Auto-translated to:
      # Scaleway: N/A (recommend Cloudflare)
      # OVH: CDN
      # Hetzner: N/A (recommend Cloudflare)
      # AWS: CloudFront
      # Coolify: N/A (recommend Cloudflare)

  # Network configuration
  network:
    vpc:
      cidr: 10.0.0.0/16
      subnets:
        - name: public
          cidr: 10.0.1.0/24
          availability_zones: 3
        - name: private
          cidr: 10.0.10.0/24
          availability_zones: 3
        - name: database
          cidr: 10.0.20.0/24
          availability_zones: 3

    firewall:
      - name: allow_https
        port: 443
        protocol: tcp
        source: 0.0.0.0/0
      - name: allow_http
        port: 80
        protocol: tcp
        source: 0.0.0.0/0
      - name: allow_postgres
        port: 5432
        protocol: tcp
        source: private_subnet_only

  # Regions (platform-agnostic)
  regions:
    primary: fr_paris  # Universal region code
    replicas:
      - nl_amsterdam
      - de_frankfurt

  # Cost optimization
  cost:
    budget_monthly: 500_eur
    alerts:
      - threshold: 400_eur
        action: email
      - threshold: 480_eur
        action: email_and_slack

    savings:
      - reserved_instances: true  # Where applicable
      - spot_instances: false
      - auto_shutdown_dev: true
```

---

## Week 71: Platform Abstraction Layer

**Objective**: Build universal infrastructure AST and platform adapters

### Day 1: Universal Infrastructure AST

**Morning Block (4 hours): Core Abstraction**

#### 🔴 RED: Platform Abstraction Tests (1 hour)

**Test File**: `tests/unit/infrastructure/test_platform_abstraction.py`

```python
"""Tests for platform-agnostic infrastructure abstraction"""

import pytest
from src.infrastructure.universal import (
    UniversalInfrastructure,
    Resource,
    ResourceType,
    UniversalSize,
    Platform,
)
from src.infrastructure.adapters import (
    ScalewayAdapter,
    OVHAdapter,
    HetznerAdapter,
    AWSAdapter,
    CoolifyAdapter,
)


class TestUniversalInfrastructure:
    """Test universal infrastructure abstraction"""

    @pytest.fixture
    def universal_spec(self):
        return UniversalInfrastructure(
            name="test-infrastructure",
            platform=Platform.AUTO,
            requirements={
                "legislation": "EU",
                "data_residency": "EU_ONLY",
                "budget": "medium",
                "scale": "high",
            },
            resources=[
                Resource(
                    type=ResourceType.POSTGRESQL,
                    name="main-db",
                    version="16",
                    size=UniversalSize.MEDIUM,
                    storage="500GB",
                    high_availability=True,
                ),
                Resource(
                    type=ResourceType.OBJECT_STORAGE,
                    name="data-bucket",
                    size="1TB",
                    versioning=True,
                    encryption=True,
                ),
            ],
        )

    def test_recommend_platform_for_eu_startup(self):
        """Test platform recommendation for EU startup"""
        # Arrange
        requirements = {
            "legislation": "EU",
            "budget": "low",
            "scale": "small",
            "region": "Europe",
        }

        # Act
        from src.infrastructure.recommender import PlatformRecommender
        recommender = PlatformRecommender()
        recommendation = recommender.recommend(requirements)

        # Assert
        assert recommendation.platform == Platform.HETZNER
        assert "price/performance" in recommendation.reasoning.lower()
        assert recommendation.monthly_cost_eur < 100

    def test_recommend_platform_for_enterprise(self):
        """Test platform recommendation for enterprise"""
        # Arrange
        requirements = {
            "legislation": "EU",
            "budget": "high",
            "scale": "large",
            "compliance": ["GDPR", "SOC2", "ISO27001"],
            "need": "multi_region_ha",
        }

        # Act
        from src.infrastructure.recommender import PlatformRecommender
        recommender = PlatformRecommender()
        recommendation = recommender.recommend(requirements)

        # Assert
        assert recommendation.platform in [Platform.OVH, Platform.SCALEWAY]
        assert "enterprise" in recommendation.reasoning.lower()

    def test_recommend_platform_for_privacy_first(self):
        """Test platform recommendation for maximum privacy"""
        # Arrange
        requirements = {
            "legislation": "EU",
            "data_residency": "EU_ONLY",
            "zero_us_jurisdiction": True,
            "budget": "medium",
        }

        # Act
        from src.infrastructure.recommender import PlatformRecommender
        recommender = PlatformRecommender()
        recommendation = recommender.recommend(requirements)

        # Assert
        assert recommendation.platform in [Platform.SCALEWAY, Platform.OVH]
        assert "sovereignty" in recommendation.reasoning.lower()

    def test_scaleway_adapter_postgresql(self, universal_spec):
        """Test Scaleway adapter generates correct PostgreSQL config"""
        # Arrange
        adapter = ScalewayAdapter()

        # Act
        output = adapter.generate(universal_spec)

        # Assert
        assert "scaleway_rdb_instance" in output.terraform
        assert "node_type = \"DB-DEV-M\"" in output.terraform  # Medium size
        assert "engine = \"PostgreSQL-16\"" in output.terraform
        assert "is_ha_cluster = true" in output.terraform

    def test_hetzner_adapter_compute(self, universal_spec):
        """Test Hetzner adapter generates correct compute config"""
        # Arrange
        spec = UniversalInfrastructure(
            name="test",
            platform=Platform.HETZNER,
            resources=[
                Resource(
                    type=ResourceType.COMPUTE,
                    name="api-server",
                    size=UniversalSize.MEDIUM,
                    count=3,
                )
            ],
        )
        adapter = HetznerAdapter()

        # Act
        output = adapter.generate(spec)

        # Assert
        assert "hcloud_server" in output.terraform
        assert "server_type = \"cpx31\"" in output.terraform  # 4 vCPU, 8GB
        assert "count = 3" in output.terraform

    def test_ovh_adapter_object_storage(self, universal_spec):
        """Test OVH adapter generates correct object storage config"""
        # Arrange
        adapter = OVHAdapter()

        # Act
        output = adapter.generate(universal_spec)

        # Assert
        assert "openstack_objectstorage_container_v1" in output.terraform
        assert "versioning = true" in output.terraform

    def test_aws_adapter_compatibility(self, universal_spec):
        """Test AWS adapter still works for users who choose it"""
        # Arrange
        spec = universal_spec
        spec.platform = Platform.AWS
        adapter = AWSAdapter()

        # Act
        output = adapter.generate(spec)

        # Assert
        assert "aws_db_instance" in output.terraform
        assert "instance_class = \"db.r6g.large\"" in output.terraform  # Medium

    def test_coolify_adapter_docker_compose(self, universal_spec):
        """Test Coolify adapter generates docker-compose.yml"""
        # Arrange
        spec = universal_spec
        spec.platform = Platform.COOLIFY
        adapter = CoolifyAdapter()

        # Act
        output = adapter.generate(spec)

        # Assert
        assert "version:" in output.docker_compose
        assert "postgres:16" in output.docker_compose
        assert "minio" in output.docker_compose  # For object storage
        assert output.coolify_config is not None

    def test_universal_size_translation(self):
        """Test universal sizes translate correctly per platform"""
        # Arrange
        size = UniversalSize.MEDIUM

        # Act & Assert
        assert ScalewayAdapter.translate_size(size, ResourceType.POSTGRESQL) == "DB-DEV-M"
        assert HetznerAdapter.translate_size(size, ResourceType.COMPUTE) == "cpx31"
        assert AWSAdapter.translate_size(size, ResourceType.POSTGRESQL) == "db.r6g.large"
        assert OVHAdapter.translate_size(size, ResourceType.COMPUTE) == "d2-8"

    def test_cost_estimation_all_platforms(self, universal_spec):
        """Test cost estimation for all platforms"""
        # Arrange
        from src.infrastructure.cost_estimator import CostEstimator
        estimator = CostEstimator()

        # Act
        costs = {
            Platform.SCALEWAY: estimator.estimate(universal_spec, Platform.SCALEWAY),
            Platform.OVH: estimator.estimate(universal_spec, Platform.OVH),
            Platform.HETZNER: estimator.estimate(universal_spec, Platform.HETZNER),
            Platform.AWS: estimator.estimate(universal_spec, Platform.AWS),
        }

        # Assert
        # Hetzner should be cheapest
        assert costs[Platform.HETZNER].monthly_eur < costs[Platform.AWS].monthly_eur
        # Scaleway competitive with OVH
        assert abs(costs[Platform.SCALEWAY].monthly_eur - costs[Platform.OVH].monthly_eur) < 100
        # AWS most expensive
        assert costs[Platform.AWS].monthly_eur > costs[Platform.HETZNER].monthly_eur * 1.5

    def test_region_translation(self):
        """Test universal region codes translate to platform-specific"""
        # Arrange
        universal_region = "fr_paris"

        # Act & Assert
        assert ScalewayAdapter.translate_region(universal_region) == "fr-par"
        assert HetznerAdapter.translate_region(universal_region) == "nbg1"  # Closest: Nuremberg
        assert AWSAdapter.translate_region(universal_region) == "eu-west-3"
        assert OVHAdapter.translate_region(universal_region) == "GRA"  # Gravelines (Paris region)

    def test_platform_feature_matrix(self):
        """Test platform feature support matrix"""
        # Arrange
        from src.infrastructure.platform_features import PlatformFeatures

        # Act
        features = PlatformFeatures()

        # Assert - European providers have managed databases
        assert features.supports(Platform.SCALEWAY, "managed_postgresql")
        assert features.supports(Platform.OVH, "managed_postgresql")
        assert features.supports(Platform.HETZNER, "managed_postgresql") is False  # Uses partner

        # Assert - All platforms support object storage
        assert features.supports(Platform.SCALEWAY, "object_storage")
        assert features.supports(Platform.OVH, "object_storage")
        assert features.supports(Platform.HETZNER, "object_storage")

        # Assert - CDN availability varies
        assert features.supports(Platform.OVH, "cdn")
        assert features.supports(Platform.SCALEWAY, "cdn") is False
        assert features.supports(Platform.HETZNER, "cdn") is False
```

---

#### 🟢 GREEN: Universal Infrastructure Core (3 hours)

**Core Module**: `src/infrastructure/universal.py`

```python
"""
Universal Infrastructure Abstraction

Platform-agnostic infrastructure definitions that translate to any provider.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class Platform(str, Enum):
    """Supported infrastructure platforms"""
    AUTO = "auto"  # Let SpecQL choose

    # European providers (first-class)
    SCALEWAY = "scaleway"
    OVH = "ovh"
    HETZNER = "hetzner"
    UPCLOUD = "upcloud"

    # US hyperscalers (equal, not preferred)
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"

    # Self-hosted
    COOLIFY = "coolify"
    BARE_METAL = "bare_metal"


class ResourceType(str, Enum):
    """Universal resource types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    REDIS = "redis"
    OBJECT_STORAGE = "object_storage"
    COMPUTE = "compute"
    LOAD_BALANCER = "load_balancer"
    CDN = "cdn"
    VPC = "vpc"
    FIREWALL = "firewall"
    DNS = "dns"


class UniversalSize(str, Enum):
    """Universal resource sizing (translates to platform-specific)"""
    SMALL = "small"      # 2 vCPU, 4GB RAM, 100GB storage
    MEDIUM = "medium"    # 4 vCPU, 8GB RAM, 250GB storage
    LARGE = "large"      # 8 vCPU, 16GB RAM, 500GB storage
    XLARGE = "xlarge"    # 16 vCPU, 32GB RAM, 1TB storage
    XXLARGE = "xxlarge"  # 32 vCPU, 64GB RAM, 2TB storage


@dataclass
class Resource:
    """Universal resource definition"""
    type: ResourceType
    name: str

    # Common attributes
    size: Optional[UniversalSize] = None
    version: Optional[str] = None
    count: int = 1

    # Database-specific
    storage: Optional[str] = None  # "500GB", "1TB"
    high_availability: bool = False
    backups: Optional[Dict[str, Any]] = None

    # Object storage-specific
    versioning: bool = False
    encryption: bool = True
    public_access: str = "blocked"  # "blocked", "read_only", "read_write"
    lifecycle: List[Dict[str, Any]] = field(default_factory=list)

    # Compute-specific
    os: Optional[str] = None
    auto_scaling: Optional[Dict[str, Any]] = None

    # Load balancer-specific
    lb_type: Optional[str] = None  # "application", "network"
    ssl: Optional[str] = None  # "automatic", "manual", "none"
    health_check: Optional[Dict[str, Any]] = None

    # Additional config
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkConfig:
    """Universal network configuration"""
    vpc_cidr: str = "10.0.0.0/16"
    subnets: List[Dict[str, Any]] = field(default_factory=list)
    firewall_rules: List[Dict[str, Any]] = field(default_factory=list)
    nat_gateway: bool = True
    vpn: bool = False


@dataclass
class CostConfig:
    """Cost optimization configuration"""
    budget_monthly_eur: float
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    savings: Dict[str, bool] = field(default_factory=dict)


@dataclass
class UniversalInfrastructure:
    """
    Universal infrastructure specification

    Platform-agnostic definition that can be translated to any provider.
    """
    name: str
    platform: Platform = Platform.AUTO

    # Requirements for platform recommendation
    requirements: Dict[str, Any] = field(default_factory=dict)

    # Resources
    resources: List[Resource] = field(default_factory=list)

    # Network
    network: Optional[NetworkConfig] = None

    # Regions
    regions: Dict[str, Any] = field(default_factory=dict)

    # Cost
    cost: Optional[CostConfig] = None

    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InfrastructureOutput:
    """Generated infrastructure code"""
    platform: Platform
    terraform: Optional[str] = None
    docker_compose: Optional[str] = None
    coolify_config: Optional[Dict[str, Any]] = None
    ansible: Optional[str] = None
    cost_estimate: Optional[Dict[str, Any]] = None
    documentation: Optional[str] = None
```

**Platform Recommender**: `src/infrastructure/recommender.py`

```python
"""
Platform Recommender

Analyzes requirements and recommends optimal infrastructure platform.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from .universal import Platform


@dataclass
class PlatformRecommendation:
    """Platform recommendation with reasoning"""
    platform: Platform
    reasoning: str
    monthly_cost_eur: float
    pros: List[str]
    cons: List[str]
    alternatives: List['PlatformRecommendation']


class PlatformRecommender:
    """Recommend optimal platform based on requirements"""

    # Platform scoring matrix
    PLATFORM_SCORES = {
        # European providers
        Platform.SCALEWAY: {
            "cost": 7,  # Good value
            "performance": 8,  # Excellent
            "managed_services": 9,  # Very good
            "eu_sovereignty": 10,  # 100% French
            "enterprise_support": 8,
            "multi_region": 7,
            "ecosystem": 7,
        },
        Platform.OVH: {
            "cost": 8,  # Very competitive
            "performance": 8,
            "managed_services": 8,
            "eu_sovereignty": 10,  # 100% French
            "enterprise_support": 9,  # Excellent
            "multi_region": 9,  # 32 data centers
            "ecosystem": 7,
        },
        Platform.HETZNER: {
            "cost": 10,  # Best value
            "performance": 9,  # Excellent
            "managed_services": 6,  # Limited
            "eu_sovereignty": 10,  # 100% German
            "enterprise_support": 6,  # Good but not enterprise
            "multi_region": 5,  # 3 locations
            "ecosystem": 6,
        },
        Platform.UPCLOUD: {
            "cost": 7,
            "performance": 9,  # Very fast
            "managed_services": 7,
            "eu_sovereignty": 10,  # 100% Finnish
            "enterprise_support": 7,
            "multi_region": 7,
            "ecosystem": 6,
        },

        # US hyperscalers
        Platform.AWS: {
            "cost": 4,  # Expensive
            "performance": 9,
            "managed_services": 10,  # Most complete
            "eu_sovereignty": 3,  # US company, CLOUD Act
            "enterprise_support": 10,
            "multi_region": 10,  # Global
            "ecosystem": 10,  # Largest
        },
        Platform.GCP: {
            "cost": 5,
            "performance": 9,
            "managed_services": 9,
            "eu_sovereignty": 3,
            "enterprise_support": 9,
            "multi_region": 9,
            "ecosystem": 9,
        },
        Platform.AZURE: {
            "cost": 5,
            "performance": 8,
            "managed_services": 9,
            "eu_sovereignty": 3,
            "enterprise_support": 9,
            "multi_region": 9,
            "ecosystem": 9,
        },

        # Self-hosted
        Platform.COOLIFY: {
            "cost": 10,  # Infrastructure cost only
            "performance": 8,  # Depends on hardware
            "managed_services": 3,  # DIY
            "eu_sovereignty": 10,  # Full control
            "enterprise_support": 2,  # Community
            "multi_region": 5,  # Manual setup
            "ecosystem": 5,
        },
    }

    def recommend(self, requirements: Dict[str, Any]) -> PlatformRecommendation:
        """
        Recommend optimal platform based on requirements

        Args:
            requirements: Dictionary of requirements
                - legislation: "EU", "US", etc.
                - budget: "low", "medium", "high"
                - scale: "small", "medium", "large"
                - compliance: List of frameworks
                - zero_us_jurisdiction: bool
                - need: Special needs (multi_region_ha, etc.)

        Returns:
            PlatformRecommendation with reasoning
        """
        scores = {}

        for platform, platform_scores in self.PLATFORM_SCORES.items():
            score = self._calculate_score(platform, platform_scores, requirements)
            scores[platform] = score

        # Get top recommendation
        top_platform = max(scores, key=scores.get)
        top_score = scores[top_platform]

        # Get alternatives (within 10% of top score)
        alternatives = [
            p for p, s in scores.items()
            if p != top_platform and s >= top_score * 0.9
        ]

        # Generate reasoning
        reasoning = self._generate_reasoning(top_platform, requirements)
        cost = self._estimate_monthly_cost(top_platform, requirements)
        pros, cons = self._get_pros_cons(top_platform, requirements)

        # Generate alternative recommendations
        alt_recommendations = [
            self._generate_alternative(alt, requirements, scores[alt])
            for alt in alternatives[:2]  # Top 2 alternatives
        ]

        return PlatformRecommendation(
            platform=top_platform,
            reasoning=reasoning,
            monthly_cost_eur=cost,
            pros=pros,
            cons=cons,
            alternatives=alt_recommendations,
        )

    def _calculate_score(
        self,
        platform: Platform,
        platform_scores: Dict[str, int],
        requirements: Dict[str, Any]
    ) -> float:
        """Calculate weighted score for platform"""
        # Weight factors based on requirements
        weights = {
            "cost": 1.0,
            "performance": 1.0,
            "managed_services": 1.0,
            "eu_sovereignty": 1.0,
            "enterprise_support": 1.0,
            "multi_region": 1.0,
            "ecosystem": 1.0,
        }

        # Adjust weights based on requirements

        # Budget sensitivity
        budget = requirements.get("budget", "medium")
        if budget == "low":
            weights["cost"] = 3.0  # Cost is critical
        elif budget == "high":
            weights["cost"] = 0.5  # Cost less important
            weights["enterprise_support"] = 2.0

        # EU sovereignty requirement
        if requirements.get("zero_us_jurisdiction"):
            weights["eu_sovereignty"] = 5.0  # Critical
        elif requirements.get("legislation") == "EU":
            weights["eu_sovereignty"] = 2.0  # Important

        # Scale sensitivity
        scale = requirements.get("scale", "medium")
        if scale == "large":
            weights["multi_region"] = 2.0
            weights["enterprise_support"] = 2.0

        # Compliance sensitivity
        compliance = requirements.get("compliance", [])
        if "SOC2" in compliance or "ISO27001" in compliance:
            weights["enterprise_support"] = 2.0

        # Calculate weighted score
        total_score = sum(
            platform_scores[factor] * weight
            for factor, weight in weights.items()
        )

        total_weight = sum(weights.values())

        return total_score / total_weight

    def _generate_reasoning(self, platform: Platform, requirements: Dict[str, Any]) -> str:
        """Generate human-readable reasoning"""
        budget = requirements.get("budget", "medium")
        scale = requirements.get("scale", "medium")
        legislation = requirements.get("legislation", "GLOBAL")

        reasonings = {
            Platform.HETZNER: f"""
Hetzner offers the best price/performance for European {scale}-scale deployments.
At ~€40/month for production setup vs €500+ AWS equivalent, you get:
- German data centers (Nuremberg, Helsinki, Falkenstein)
- Full GDPR compliance without US jurisdiction
- Excellent network performance (10 Gbps connectivity)
- Simple, predictable pricing with no hidden costs

Perfect for: Startups, SMBs, cost-conscious European companies.
""".strip(),

            Platform.SCALEWAY: f"""
Scaleway provides enterprise-grade infrastructure with 100% European sovereignty.
As a French company, zero CLOUD Act exposure. Excellent managed services:
- Paris + Amsterdam + Warsaw data centers
- Managed PostgreSQL, Redis, Kubernetes
- Competitive pricing (30% less than AWS)
- Strong privacy focus (GDPR-native)

Perfect for: Privacy-first applications, French market, EU-only deployments.
""".strip(),

            Platform.OVH: f"""
OVH delivers enterprise infrastructure at scale with European values.
32 data centers globally, SOC2 Type II certified, 99.99% SLA:
- Largest European cloud provider
- Excellent enterprise support
- 40% cost savings vs AWS
- Strong in European markets

Perfect for: Enterprise SaaS, multi-region HA, global scale with EU headquarters.
""".strip(),

            Platform.AWS: f"""
AWS provides the most comprehensive managed services ecosystem.
Choose AWS when you need:
- Maximum service variety (200+ services)
- Global reach (33 regions)
- Best-in-class enterprise support
- Large ecosystem and talent pool

Note: US company subject to CLOUD Act. Consider European alternatives for {legislation} data sovereignty.
""".strip(),

            Platform.COOLIFY: f"""
Self-hosted with Coolify gives maximum control and cost efficiency.
Perfect for teams who want:
- Zero vendor lock-in
- Complete data sovereignty
- Infrastructure costs only (~€100/month)
- Full customization

Requires: DevOps expertise, time for maintenance.
""".strip(),
        }

        return reasonings.get(platform, f"Recommended based on your {scale}-scale {legislation} requirements.")

    def _estimate_monthly_cost(self, platform: Platform, requirements: Dict[str, Any]) -> float:
        """Estimate monthly cost in EUR"""
        scale = requirements.get("scale", "medium")

        # Base costs for production setup (DB + compute + storage + network)
        base_costs = {
            Platform.HETZNER: {"small": 40, "medium": 150, "large": 500},
            Platform.SCALEWAY: {"small": 60, "medium": 200, "large": 700},
            Platform.OVH: {"small": 70, "medium": 250, "large": 800},
            Platform.UPCLOUD: {"small": 65, "medium": 220, "large": 750},
            Platform.AWS: {"small": 200, "medium": 600, "large": 2000},
            Platform.GCP: {"small": 180, "medium": 550, "large": 1800},
            Platform.AZURE: {"small": 190, "medium": 580, "large": 1900},
            Platform.COOLIFY: {"small": 50, "medium": 150, "large": 500},  # Infra only
        }

        return base_costs.get(platform, {}).get(scale, 200)

    def _get_pros_cons(self, platform: Platform, requirements: Dict[str, Any]) -> tuple:
        """Get pros and cons for platform"""
        pros_cons = {
            Platform.HETZNER: (
                ["Best price/performance", "German quality", "Simple pricing", "Fast deployment"],
                ["Limited managed services", "Smaller ecosystem", "Basic enterprise features"],
            ),
            Platform.SCALEWAY: (
                ["100% French sovereignty", "Great managed services", "Privacy-focused", "Competitive pricing"],
                ["Smaller ecosystem than hyperscalers", "Fewer regions than OVH"],
            ),
            Platform.OVH: (
                ["32 global data centers", "Enterprise support", "SOC2 certified", "40% cheaper than AWS"],
                ["Learning curve", "Ecosystem smaller than AWS"],
            ),
            Platform.AWS: (
                ["Most services", "Largest ecosystem", "Best documentation", "Global reach"],
                ["Expensive", "US jurisdiction (CLOUD Act)", "Complex pricing", "Vendor lock-in"],
            ),
            Platform.COOLIFY: (
                ["Maximum control", "Zero lock-in", "Infrastructure cost only", "Full customization"],
                ["Requires DevOps expertise", "Manual scaling", "No managed services", "Ops overhead"],
            ),
        }

        return pros_cons.get(platform, ([], []))

    def _generate_alternative(
        self,
        platform: Platform,
        requirements: Dict[str, Any],
        score: float
    ) -> PlatformRecommendation:
        """Generate alternative recommendation"""
        reasoning = self._generate_reasoning(platform, requirements)
        cost = self._estimate_monthly_cost(platform, requirements)
        pros, cons = self._get_pros_cons(platform, requirements)

        return PlatformRecommendation(
            platform=platform,
            reasoning=reasoning,
            monthly_cost_eur=cost,
            pros=pros,
            cons=cons,
            alternatives=[],  # No nested alternatives
        )
```

---

### Days 2-3: Platform Adapters (European Providers)

**Scaleway Adapter**: `src/infrastructure/adapters/scaleway_adapter.py`

```python
"""
Scaleway Infrastructure Adapter

Translates universal infrastructure to Scaleway Terraform/API.
"""

from typing import Dict, Any
from ..universal import (
    UniversalInfrastructure,
    Resource,
    ResourceType,
    UniversalSize,
    InfrastructureOutput,
    Platform,
)


class ScalewayAdapter:
    """Generate Scaleway infrastructure from universal spec"""

    # Size mappings
    SIZE_MAPPINGS = {
        ResourceType.POSTGRESQL: {
            UniversalSize.SMALL: "DB-DEV-S",    # 2 vCPU, 2GB RAM
            UniversalSize.MEDIUM: "DB-DEV-M",   # 4 vCPU, 4GB RAM
            UniversalSize.LARGE: "DB-DEV-L",    # 8 vCPU, 8GB RAM
            UniversalSize.XLARGE: "DB-DEV-XL",  # 12 vCPU, 16GB RAM
        },
        ResourceType.COMPUTE: {
            UniversalSize.SMALL: "DEV1-S",      # 2 vCPU, 2GB RAM
            UniversalSize.MEDIUM: "DEV1-M",     # 3 vCPU, 4GB RAM
            UniversalSize.LARGE: "DEV1-L",      # 4 vCPU, 8GB RAM
            UniversalSize.XLARGE: "DEV1-XL",    # 4 vCPU, 12GB RAM
        },
    }

    # Region mappings
    REGION_MAPPINGS = {
        "fr_paris": "fr-par",
        "nl_amsterdam": "nl-ams",
        "pl_warsaw": "pl-waw",
    }

    def generate(self, spec: UniversalInfrastructure) -> InfrastructureOutput:
        """
        Generate Scaleway infrastructure code

        Args:
            spec: Universal infrastructure specification

        Returns:
            InfrastructureOutput with Terraform code
        """
        terraform = self._generate_terraform_header()

        for resource in spec.resources:
            if resource.type == ResourceType.POSTGRESQL:
                terraform += self._generate_postgresql(resource, spec)
            elif resource.type == ResourceType.OBJECT_STORAGE:
                terraform += self._generate_object_storage(resource, spec)
            elif resource.type == ResourceType.COMPUTE:
                terraform += self._generate_compute(resource, spec)
            elif resource.type == ResourceType.LOAD_BALANCER:
                terraform += self._generate_load_balancer(resource, spec)

        # Add networking
        if spec.network:
            terraform += self._generate_network(spec.network, spec)

        return InfrastructureOutput(
            platform=Platform.SCALEWAY,
            terraform=terraform,
            cost_estimate=self._estimate_cost(spec),
            documentation=self._generate_documentation(spec),
        )

    def _generate_terraform_header(self) -> str:
        """Generate Terraform header for Scaleway"""
        return '''
terraform {
  required_version = ">= 1.0"

  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.0"
    }
  }
}

provider "scaleway" {
  zone   = "fr-par-1"
  region = "fr-par"
}

'''

    def _generate_postgresql(self, resource: Resource, spec: UniversalInfrastructure) -> str:
        """Generate Scaleway Managed PostgreSQL"""
        size = self.SIZE_MAPPINGS[ResourceType.POSTGRESQL].get(
            resource.size, "DB-DEV-M"
        )

        region = self.REGION_MAPPINGS.get(
            spec.regions.get("primary", "fr_paris"),
            "fr-par"
        )

        return f'''
# Scaleway Managed Database for PostgreSQL
resource "scaleway_rdb_instance" "{resource.name}" {{
  name           = "{resource.name}"
  node_type      = "{size}"
  engine         = "PostgreSQL-{resource.version or '16'}"
  is_ha_cluster  = {str(resource.high_availability).lower()}

  # Disable public endpoint (security)
  disable_backup = false
  backup_schedule_frequency = 24  # Daily backups
  backup_schedule_retention = {resource.backups.get("retention_days", 30) if resource.backups else 30}

  # Encryption at rest (automatic)

  # GDPR compliance tags
  tags = [
    "gdpr-compliant",
    "data-residency-eu",
    "environment-production"
  ]

  region = "{region}"
}}

# Database credentials (store in secrets)
resource "scaleway_rdb_user" "{resource.name}_admin" {{
  instance_id = scaleway_rdb_instance.{resource.name}.id
  name        = "admin"
  password    = var.db_admin_password
  is_admin    = true
}}

output "{resource.name}_endpoint" {{
  value     = scaleway_rdb_instance.{resource.name}.endpoint_ip
  sensitive = true
}}

output "{resource.name}_port" {{
  value = scaleway_rdb_instance.{resource.name}.endpoint_port
}}
'''

    def _generate_object_storage(self, resource: Resource, spec: UniversalInfrastructure) -> str:
        """Generate Scaleway Object Storage"""
        region = self.REGION_MAPPINGS.get(
            spec.regions.get("primary", "fr_paris"),
            "fr-par"
        )

        return f'''
# Scaleway Object Storage (S3-compatible)
resource "scaleway_object_bucket" "{resource.name}" {{
  name   = "{resource.name}"
  region = "{region}"

  # ACL settings
  acl = "private"  # Block public access by default

  # GDPR compliance tags
  tags = {{
    "gdpr-compliant" = "true"
    "data-residency" = "EU"
  }}
}}

# Enable versioning (GDPR Article 32 - integrity)
resource "scaleway_object_bucket_versioning" "{resource.name}" {{
  bucket = scaleway_object_bucket.{resource.name}.name
  region = "{region}"

  versioning_configuration {{
    status = "{("enabled" if resource.versioning else "disabled")}"
  }}
}}

# Lifecycle policy (GDPR data minimization)
resource "scaleway_object_bucket_lifecycle_configuration" "{resource.name}" {{
  bucket = scaleway_object_bucket.{resource.name}.name
  region = "{region}"

  rule {{
    id     = "archive-old-data"
    status = "Enabled"

    transition {{
      days          = 90
      storage_class = "GLACIER"
    }}

    expiration {{
      days = 365  # Delete after 1 year
    }}
  }}
}}

output "{resource.name}_endpoint" {{
  value = "s3.{region}.scw.cloud"
}}

output "{resource.name}_bucket" {{
  value = scaleway_object_bucket.{resource.name}.name
}}
'''

    def _generate_compute(self, resource: Resource, spec: UniversalInfrastructure) -> str:
        """Generate Scaleway Instances"""
        size = self.SIZE_MAPPINGS[ResourceType.COMPUTE].get(
            resource.size, "DEV1-M"
        )

        return f'''
# Scaleway Compute Instances
resource "scaleway_instance_server" "{resource.name}" {{
  count = {resource.count}

  name  = "{resource.name}-${{count.index + 1}}"
  type  = "{size}"
  image = "ubuntu_jammy"  # Ubuntu 22.04 LTS

  # Security: Private network only
  enable_dynamic_ip = false
  enable_ipv6       = true

  tags = [
    "gdpr-compliant",
    "role-{resource.name}"
  ]
}}

output "{resource.name}_ips" {{
  value = scaleway_instance_server.{resource.name}[*].private_ip
}}
'''

    def _generate_load_balancer(self, resource: Resource, spec: UniversalInfrastructure) -> str:
        """Generate Scaleway Load Balancer"""
        return f'''
# Scaleway Load Balancer
resource "scaleway_lb_ip" "{resource.name}" {{
}}

resource "scaleway_lb" "{resource.name}" {{
  ip_id = scaleway_lb_ip.{resource.name}.id
  name  = "{resource.name}"
  type  = "LB-S"  # Small load balancer

  tags = ["production", "gdpr-compliant"]
}}

# Frontend (HTTPS)
resource "scaleway_lb_frontend" "{resource.name}_https" {{
  lb_id        = scaleway_lb.{resource.name}.id
  backend_id   = scaleway_lb_backend.{resource.name}.id
  name         = "https-frontend"
  inbound_port = 443

  # Automatic Let's Encrypt SSL
  certificate_ids = [scaleway_lb_certificate.{resource.name}.id]
}}

# Backend
resource "scaleway_lb_backend" "{resource.name}" {{
  lb_id            = scaleway_lb.{resource.name}.id
  name             = "backend"
  forward_protocol = "http"
  forward_port     = 80

  health_check_tcp {{}}
}}

# SSL Certificate (Let's Encrypt)
resource "scaleway_lb_certificate" "{resource.name}" {{
  lb_id = scaleway_lb.{resource.name}.id
  name  = "ssl-cert"

  letsencrypt {{
    common_name = var.domain_name
  }}
}}

output "{resource.name}_ip" {{
  value = scaleway_lb_ip.{resource.name}.ip_address
}}
'''

    def _generate_network(self, network: Any, spec: UniversalInfrastructure) -> str:
        """Generate Scaleway Private Network"""
        return f'''
# Scaleway Private Network (VPC equivalent)
resource "scaleway_vpc_private_network" "main" {{
  name = "{spec.name}-vpc"
  tags = ["gdpr-compliant", "private"]
}}
'''

    def _estimate_cost(self, spec: UniversalInfrastructure) -> Dict[str, Any]:
        """Estimate monthly cost for Scaleway"""
        total_eur = 0.0
        breakdown = {}

        for resource in spec.resources:
            if resource.type == ResourceType.POSTGRESQL:
                # Scaleway DB pricing (approximate)
                cost = {"SMALL": 20, "MEDIUM": 40, "LARGE": 80, "XLARGE": 160}.get(
                    resource.size.value.upper(), 40
                )
                if resource.high_availability:
                    cost *= 2
                breakdown[resource.name] = cost
                total_eur += cost

            elif resource.type == ResourceType.COMPUTE:
                # Instance pricing
                cost_per_instance = {"SMALL": 7, "MEDIUM": 15, "LARGE": 30, "XLARGE": 60}.get(
                    resource.size.value.upper(), 15
                )
                cost = cost_per_instance * resource.count
                breakdown[resource.name] = cost
                total_eur += cost

            elif resource.type == ResourceType.OBJECT_STORAGE:
                # Storage: ~€0.01/GB/month
                storage_gb = int(resource.size.replace("TB", "000").replace("GB", ""))
                cost = storage_gb * 0.01
                breakdown[resource.name] = cost
                total_eur += cost

        return {
            "monthly_eur": round(total_eur, 2),
            "breakdown": breakdown,
            "currency": "EUR",
            "platform": "Scaleway",
        }

    def _generate_documentation(self, spec: UniversalInfrastructure) -> str:
        """Generate deployment documentation"""
        return f'''
# Scaleway Infrastructure Deployment

## Overview
This infrastructure is deployed on Scaleway (French cloud provider).
- **Data residency**: France (Paris region)
- **Compliance**: GDPR, NIS2, ISO27001
- **No US jurisdiction**: 100% European sovereignty

## Deployment

### Prerequisites
```bash
# Install Scaleway CLI
brew install scaleway

# Login
scw init
```

### Deploy
```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

## Cost Estimate
- **Monthly**: €{self._estimate_cost(spec)["monthly_eur"]}
- **Annual**: €{self._estimate_cost(spec)["monthly_eur"] * 12}

## Support
- Scaleway Console: https://console.scaleway.com
- Support: https://console.scaleway.com/support
- Documentation: https://www.scaleway.com/en/docs/

## GDPR Compliance
✅ Data stays in EU (France)
✅ No cross-border transfers
✅ Encryption at rest and in transit
✅ Automatic backups with 30-day retention
✅ Right to erasure supported
'''

    @staticmethod
    def translate_size(size: UniversalSize, resource_type: ResourceType) -> str:
        """Translate universal size to Scaleway size"""
        return ScalewayAdapter.SIZE_MAPPINGS.get(resource_type, {}).get(
            size, "DEV1-M"
        )

    @staticmethod
    def translate_region(universal_region: str) -> str:
        """Translate universal region to Scaleway region"""
        return ScalewayAdapter.REGION_MAPPINGS.get(universal_region, "fr-par")
```

---

## Week 71 Summary

**Achievements**:
- ✅ Universal infrastructure DSL
- ✅ Platform-agnostic AST
- ✅ Intelligent platform recommender
- ✅ Scaleway adapter (complete)
- ✅ Cost estimation across all platforms
- ✅ European providers as first-class citizens

---

## Week 72: Complete Platform Ecosystem

**Days 1-2**: OVH + Hetzner adapters
**Days 3-4**: Coolify self-hosted adapter
**Day 5**: CLI integration + documentation

---

## Success Metrics

**Week 71**:
- [ ] Universal infrastructure parser working
- [ ] Platform recommender suggests best fit
- [ ] Scaleway adapter generates valid Terraform
- [ ] Cost estimation accurate (±10%)
- [ ] Tests passing for all European providers

**Week 72**:
- [ ] All 8 platforms supported (Scaleway, OVH, Hetzner, UpCloud, AWS, GCP, Azure, Coolify)
- [ ] Cost comparison shows 40-60% savings (European vs US)
- [ ] Self-hosted Coolify option working
- [ ] Documentation for each platform
- [ ] CLI command: `specql infra generate --platform auto`

---

## Strategic Impact

### 1. True Infrastructure Freedom

**No vendor lock-in**: Switch providers by changing one line:
```yaml
platform: scaleway  # or ovh, hetzner, aws, coolify
```

### 2. European Cloud Empowerment

**Market impact**: Puts Scaleway/OVH/Hetzner on equal footing with AWS/GCP/Azure.

**Cost advantage**: 40-60% savings for European SMBs.

### 3. Data Sovereignty by Default

**100% European options**: No US jurisdiction, no CLOUD Act exposure.

### 4. Developer Choice

**Best tool for the job**: Platform recommendations based on actual requirements, not vendor preference.

---

**Status**: 🔴 Ready to Execute
**Priority**: Strategic (Market differentiation)
**Expected Output**: Platform democracy, European cloud empowerment, true infrastructure freedom
