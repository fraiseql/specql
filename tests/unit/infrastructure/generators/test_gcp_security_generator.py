"""
Test GCP Security Generator

Tests for generating GCP security resources (Firewall Rules, Cloud Armor, Cloud VPN) from universal schema:
- Firewall rule generation for network tiers
- Cloud Armor security policy generation
- Cloud VPN generation
- Cross-tier firewall references
"""

from infrastructure.generators.gcp_security_generator import GCPSecurityGenerator
from infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    SecurityConfig,
    UniversalInfrastructure,
    VPNConfig,
    WAFConfig,
)


def test_generate_gcp_firewall_rules():
    """Should generate GCP firewall rules from universal schema"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-http",
                            protocol="tcp",
                            ports=[80, 443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                )
            ]
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "google_compute_firewall" "web_allow_http"' in terraform
    assert 'protocol = "tcp"' in terraform
    assert 'ports    = ["80", "443"]' in terraform
    assert 'source_ranges = ["0.0.0.0/0"]' in terraform


def test_generate_gcp_firewall_with_multiple_rules():
    """Should generate firewall rules for multiple tiers"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-http",
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
                            name="allow-from-web",
                            protocol="tcp",
                            ports=[8080],
                            source="web",
                            action="allow",
                        )
                    ],
                ),
            ]
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "google_compute_firewall" "web_allow_http"' in terraform
    assert 'resource "google_compute_firewall" "api_allow_from_web"' in terraform
    assert 'target_tags = ["web"]' in terraform
    assert 'source_tags = ["web"]' in terraform


def test_generate_cloud_armor():
    """Should generate Cloud Armor security policy when WAF is enabled"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            waf=WAFConfig(enabled=True, mode="prevention", rule_sets=["OWASP_TOP_10"])
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "google_compute_security_policy" "test-app_cloud_armor"' in terraform
    assert "rule {" in terraform
    assert 'action   = "deny(403)"' in terraform
    assert 'priority = "1000"' in terraform


def test_generate_cloud_vpn():
    """Should generate Cloud VPN when VPN is enabled"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            vpn=VPNConfig(enabled=True, type="site-to-site", remote_cidr="192.168.0.0/16")
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "google_compute_vpn_gateway" "test-app_vpn"' in terraform
    assert 'resource "google_compute_vpn_tunnel"' in terraform
    assert 'resource "google_compute_router"' in terraform
    assert "192.168.0.0/16" in terraform


def test_generate_cross_tier_firewall_references():
    """Should generate firewall rules with target and source tags for cross-tier access"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
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
                    name="api",
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
                            name="allow-from-api",
                            protocol="tcp",
                            ports=[5432],
                            source="api",
                            action="allow",
                        )
                    ],
                ),
            ]
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # Web tier allows from internet
    assert 'resource "google_compute_firewall" "web_allow_internet"' in terraform
    assert 'target_tags = ["web"]' in terraform
    assert 'source_ranges = ["0.0.0.0/0"]' in terraform

    # API tier allows from web
    assert 'resource "google_compute_firewall" "api_allow_from_web"' in terraform
    assert 'target_tags = ["api"]' in terraform
    assert 'source_tags = ["web"]' in terraform

    # Database tier allows from api
    assert 'resource "google_compute_firewall" "database_allow_from_api"' in terraform
    assert 'target_tags = ["database"]' in terraform
    assert 'source_tags = ["api"]' in terraform


def test_generate_port_ranges():
    """Should generate firewall rules with port ranges"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            network_tiers=[
                NetworkTier(
                    name="app",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-dynamic-ports",
                            protocol="tcp",
                            ports=[],
                            port_ranges=["8000-9000"],
                            source="load-balancer",
                            action="allow",
                        )
                    ],
                )
            ]
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'ports    = ["8000-9000"]' in terraform


def test_generate_with_compliance_preset():
    """Should apply compliance preset configurations"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            compliance_preset=CompliancePreset.PCI_DSS,
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-https",
                            protocol="tcp",
                            ports=[443],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                )
            ],
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # PCI-DSS should enable Cloud Armor
    assert 'resource "google_compute_security_policy"' in terraform


def test_generate_udp_and_icmp_rules():
    """Should generate firewall rules for UDP and ICMP protocols"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            network_tiers=[
                NetworkTier(
                    name="monitoring",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-ntp",
                            protocol="udp",
                            ports=[123],
                            source="0.0.0.0/0",
                            action="allow",
                        ),
                        FirewallRule(
                            name="allow-ping",
                            protocol="icmp",
                            ports=[-1],  # ICMP type/code
                            source="admin",
                            action="allow",
                        ),
                    ],
                )
            ]
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'protocol = "udp"' in terraform
    assert 'ports    = ["123"]' in terraform
    assert 'protocol = "icmp"' in terraform


def test_generate_multiple_ports():
    """Should generate firewall rules with multiple ports"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-web-services",
                            protocol="tcp",
                            ports=[80, 443, 8080],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                )
            ]
        ),
    )

    generator = GCPSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # GCP firewall rules can have multiple ports in one rule
    assert 'ports    = ["80", "443", "8080"]' in terraform
