"""
Security Pattern Library

Pre-built security patterns for common infrastructure scenarios.
Provides composable security configurations for web apps, APIs, databases, etc.
"""

from dataclasses import dataclass, field
from typing import Any

from infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    SecurityConfig,
    UniversalInfrastructure,
    VPNConfig,
    WAFConfig,
)


@dataclass
class SecurityPattern:
    """A pre-built security pattern for common infrastructure scenarios"""

    name: str
    description: str
    network_tiers: list[NetworkTier] = field(default_factory=list)
    waf_config: WAFConfig | None = None
    vpn_config: VPNConfig | None = None
    compliance_preset: CompliancePreset | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_security_config(self) -> SecurityConfig:
        """Convert this pattern to a SecurityConfig"""
        config = SecurityConfig(
            network_tiers=self.network_tiers.copy(),
            compliance_preset=self.compliance_preset,
        )

        if self.waf_config:
            config.waf = self.waf_config
        if self.vpn_config:
            config.vpn = self.vpn_config

        return config


class SecurityPatternLibrary:
    """Library of pre-built security patterns for common scenarios"""

    def __init__(self):
        self._patterns: dict[str, SecurityPattern] = {}
        self._load_builtin_patterns()

    def _load_builtin_patterns(self):
        """Load built-in security patterns"""
        self._patterns.update(
            {
                "web-app-basic": self._create_web_app_basic_pattern(),
                "web-app-secure": self._create_web_app_secure_pattern(),
                "api-gateway": self._create_api_gateway_pattern(),
                "database-cluster": self._create_database_cluster_pattern(),
                "microservices": self._create_microservices_pattern(),
                "three-tier-app": self._create_three_tier_app_pattern(),
                "pci-compliant-web": self._create_pci_compliant_web_pattern(),
                "hipaa-compliant-api": self._create_hipaa_compliant_api_pattern(),
            }
        )

    def get_pattern(self, name: str) -> SecurityPattern | None:
        """Get a security pattern by name"""
        return self._patterns.get(name)

    def list_patterns(self, tags: list[str] | None = None) -> list[SecurityPattern]:
        """List all available patterns, optionally filtered by tags"""
        patterns = list(self._patterns.values())

        if tags:
            patterns = [p for p in patterns if any(tag in p.tags for tag in tags)]

        return patterns

    def compose_patterns(self, pattern_names: list[str]) -> SecurityConfig:
        """Compose multiple patterns into a single security configuration"""
        if not pattern_names:
            return SecurityConfig()

        # Start with the first pattern
        base_pattern = self.get_pattern(pattern_names[0])
        if not base_pattern:
            raise ValueError(f"Pattern '{pattern_names[0]}' not found")

        result_config = base_pattern.to_security_config()

        # Merge additional patterns
        for pattern_name in pattern_names[1:]:
            pattern = self.get_pattern(pattern_name)
            if not pattern:
                raise ValueError(f"Pattern '{pattern_name}' not found")

            result_config = self._merge_security_configs(
                result_config, pattern.to_security_config()
            )

        return result_config

    def apply_pattern_to_infrastructure(
        self, infrastructure: UniversalInfrastructure, pattern_name: str
    ) -> UniversalInfrastructure:
        """Apply a security pattern to an existing infrastructure"""
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            raise ValueError(f"Pattern '{pattern_name}' not found")

        # Create a copy of the infrastructure
        new_infra = UniversalInfrastructure(
            name=infrastructure.name,
            region=infrastructure.region,
            security=pattern.to_security_config(),
            compute=infrastructure.compute,
            database=infrastructure.database,
            load_balancer=infrastructure.load_balancer,
            volumes=infrastructure.volumes.copy() if infrastructure.volumes else [],
            object_storage=infrastructure.object_storage,
            observability=infrastructure.observability,
            tags=infrastructure.tags.copy(),
        )

        return new_infra

    def validate_pattern_compatibility(self, pattern_names: list[str]) -> list[str]:
        """Validate that a set of patterns are compatible with each other"""
        warnings = []

        patterns = []
        for name in pattern_names:
            pattern = self.get_pattern(name)
            if not pattern:
                warnings.append(f"Pattern '{name}' not found")
                continue
            patterns.append(pattern)

        # Check for conflicting compliance presets
        compliance_presets = {p.compliance_preset for p in patterns if p.compliance_preset}
        if len(compliance_presets) > 1:
            warnings.append(f"Multiple compliance presets detected: {compliance_presets}")

        # Check for duplicate network tiers
        all_tier_names = []
        for pattern in patterns:
            for tier in pattern.network_tiers:
                if tier.name in all_tier_names:
                    warnings.append(
                        f"Duplicate network tier '{tier.name}' found in multiple patterns"
                    )
                all_tier_names.append(tier.name)

        return warnings

    def _merge_security_configs(
        self, base: SecurityConfig, overlay: SecurityConfig
    ) -> SecurityConfig:
        """Merge two security configurations"""
        # Merge network tiers (overlay takes precedence for duplicates)
        tier_dict = {tier.name: tier for tier in base.network_tiers}

        for tier in overlay.network_tiers:
            tier_dict[tier.name] = tier

        merged_tiers = list(tier_dict.values())

        # Merge WAF configs (overlay takes precedence)
        merged_waf = overlay.waf if overlay.waf else base.waf

        # Merge VPN configs (overlay takes precedence)
        merged_vpn = overlay.vpn if overlay.vpn else base.vpn

        # Merge compliance preset (overlay takes precedence)
        merged_compliance = (
            overlay.compliance_preset if overlay.compliance_preset else base.compliance_preset
        )

        return SecurityConfig(
            network_tiers=merged_tiers,
            waf=merged_waf,
            vpn=merged_vpn,
            compliance_preset=merged_compliance,
        )

    def _create_web_app_basic_pattern(self) -> SecurityPattern:
        """Create a basic web application security pattern"""
        return SecurityPattern(
            name="web-app-basic",
            description="Basic web application with internet access",
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-http-https",
                            protocol="tcp",
                            ports=[80, 443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                )
            ],
            tags=["web", "basic", "internet-facing"],
        )

    def _create_web_app_secure_pattern(self) -> SecurityPattern:
        """Create a secure web application pattern with WAF"""
        return SecurityPattern(
            name="web-app-secure",
            description="Secure web application with WAF protection",
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-http-https",
                            protocol="tcp",
                            ports=[80, 443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                )
            ],
            waf_config=WAFConfig(enabled=True, mode="prevention"),
            tags=["web", "secure", "waf", "internet-facing"],
        )

    def _create_api_gateway_pattern(self) -> SecurityPattern:
        """Create an API gateway security pattern"""
        return SecurityPattern(
            name="api-gateway",
            description="API gateway with authentication and rate limiting",
            network_tiers=[
                NetworkTier(
                    name="gateway",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-api-traffic",
                            protocol="tcp",
                            ports=[80, 443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                ),
                NetworkTier(
                    name="api",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-from-gateway",
                            protocol="tcp",
                            ports=[8080, 8443],
                            source="gateway",
                            action="allow",
                        )
                    ],
                ),
            ],
            waf_config=WAFConfig(enabled=True, mode="prevention"),
            tags=["api", "gateway", "microservices", "secure"],
        )

    def _create_database_cluster_pattern(self) -> SecurityPattern:
        """Create a database cluster security pattern"""
        return SecurityPattern(
            name="database-cluster",
            description="Secure database cluster with restricted access",
            network_tiers=[
                NetworkTier(
                    name="database",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-postgresql",
                            protocol="tcp",
                            ports=[5432],
                            source="api",
                            action="allow",
                        ),
                        FirewallRule(
                            name="allow-mysql",
                            protocol="tcp",
                            ports=[3306],
                            source="api",
                            action="allow",
                        ),
                        FirewallRule(
                            name="allow-redis",
                            protocol="tcp",
                            ports=[6379],
                            source="api",
                            action="allow",
                        ),
                    ],
                )
            ],
            tags=["database", "cluster", "restricted"],
        )

    def _create_microservices_pattern(self) -> SecurityPattern:
        """Create a microservices security pattern"""
        return SecurityPattern(
            name="microservices",
            description="Microservices architecture with service mesh security",
            network_tiers=[
                NetworkTier(
                    name="ingress",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-external",
                            protocol="tcp",
                            ports=[80, 443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                ),
                NetworkTier(
                    name="services",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-from-ingress",
                            protocol="tcp",
                            ports=[8080, 8443],
                            source="ingress",
                            action="allow",
                        ),
                        FirewallRule(
                            name="allow-service-mesh",
                            protocol="tcp",
                            ports=[15001, 15006],  # Istio ports
                            source="services",
                            action="allow",
                        ),
                    ],
                ),
            ],
            tags=["microservices", "service-mesh", "kubernetes"],
        )

    def _create_three_tier_app_pattern(self) -> SecurityPattern:
        """Create a three-tier application security pattern"""
        return SecurityPattern(
            name="three-tier-app",
            description="Classic three-tier application (web, app, database)",
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-internet",
                            protocol="tcp",
                            ports=[80, 443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                ),
                NetworkTier(
                    name="app",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-from-web",
                            protocol="tcp",
                            ports=[8080],
                            source="web",
                            action="allow",
                        )
                    ],
                ),
                NetworkTier(
                    name="database",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-from-app",
                            protocol="tcp",
                            ports=[5432],
                            source="app",
                            action="allow",
                        )
                    ],
                ),
            ],
            tags=["three-tier", "web-app", "database"],
        )

    def _create_pci_compliant_web_pattern(self) -> SecurityPattern:
        """Create a PCI DSS compliant web application pattern"""
        return SecurityPattern(
            name="pci-compliant-web",
            description="PCI DSS compliant web application",
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-https-only",
                            protocol="tcp",
                            ports=[443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                ),
                NetworkTier(
                    name="app",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-from-web",
                            protocol="tcp",
                            ports=[8443],
                            source="web",
                            action="allow",
                        )
                    ],
                ),
                NetworkTier(
                    name="database",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-from-app",
                            protocol="tcp",
                            ports=[5432],
                            source="app",
                            action="allow",
                        )
                    ],
                ),
            ],
            waf_config=WAFConfig(enabled=True, mode="prevention"),
            compliance_preset=CompliancePreset.PCI_DSS,
            tags=["pci-dss", "compliance", "web-app", "secure"],
        )

    def _create_hipaa_compliant_api_pattern(self) -> SecurityPattern:
        """Create a HIPAA compliant API pattern"""
        return SecurityPattern(
            name="hipaa-compliant-api",
            description="HIPAA compliant API with encryption and access controls",
            network_tiers=[
                NetworkTier(
                    name="api",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-https-only",
                            protocol="tcp",
                            ports=[443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                ),
                NetworkTier(
                    name="database",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-from-api",
                            protocol="tcp",
                            ports=[5432],
                            source="api",
                            action="allow",
                        )
                    ],
                ),
            ],
            waf_config=WAFConfig(enabled=True, mode="prevention"),
            vpn_config=VPNConfig(enabled=True, type="site-to-site"),
            compliance_preset=CompliancePreset.HIPAA,
            tags=["hipaa", "compliance", "api", "healthcare", "encrypted"],
        )
