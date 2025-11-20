"""
Test AWS Security Generator

Tests for generating AWS security resources (Security Groups, WAF, VPN) from universal schema:
- Security group generation for network tiers
- Firewall rule conversion to ingress/egress rules
- WAF resource generation
- VPN Gateway generation
- Cross-tier security group references
"""

from infrastructure.generators.aws_security_generator import AWSSecurityGenerator
from infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    SecurityConfig,
    UniversalInfrastructure,
    VPNConfig,
    WAFConfig,
)


def test_generate_tiered_security_groups():
    """Should generate AWS security groups for each tier"""
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

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "aws_security_group" "web"' in terraform
    assert 'resource "aws_security_group" "api"' in terraform
    assert "from_port   = 80" in terraform
    assert "to_port     = 443" in terraform
    assert "from_port   = 8080" in terraform


def test_generate_security_group_with_multiple_rules():
    """Should generate security group with multiple ingress rules"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            network_tiers=[
                NetworkTier(
                    name="database",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-postgres",
                            protocol="tcp",
                            ports=[5432],
                            source="api",
                            action="allow",
                        ),
                        FirewallRule(
                            name="allow-ssh",
                            protocol="tcp",
                            ports=[22],
                            source="admin",
                            action="allow",
                        ),
                    ],
                )
            ]
        ),
    )

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "aws_security_group" "database"' in terraform
    assert terraform.count("from_port   = 5432") == 1
    assert terraform.count("from_port   = 22") == 1


def test_generate_waf_resources():
    """Should generate AWS WAF resources when WAF is enabled"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            waf=WAFConfig(enabled=True, mode="prevention", rule_sets=["OWASP_TOP_10"])
        ),
    )

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "aws_wafv2_web_acl" "test-app_waf"' in terraform
    assert '"AWSManagedRulesCommonRuleSet"' in terraform


def test_generate_vpn_gateway():
    """Should generate AWS VPN Gateway when VPN is enabled"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            vpn=VPNConfig(enabled=True, type="site-to-site", remote_cidr="192.168.0.0/16")
        ),
    )

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "aws_vpn_gateway" "test-app_vpn"' in terraform
    assert 'resource "aws_customer_gateway"' in terraform
    assert 'resource "aws_vpn_connection"' in terraform
    assert "192.168.0.0/16" in terraform


def test_generate_cross_tier_references():
    """Should generate security group references for cross-tier rules"""
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
                            source="web",  # Cross-tier reference
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
                            source="api",  # Cross-tier reference
                            action="allow",
                        )
                    ],
                ),
            ]
        ),
    )

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # Should have security group references for cross-tier rules
    # web is referenced by api, api is referenced by database
    assert "aws_security_group.web.id" in terraform  # referenced by api
    assert "aws_security_group.api.id" in terraform  # referenced by database


def test_generate_port_ranges():
    """Should generate port ranges for firewall rules with ranges"""
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

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert "from_port   = 8000" in terraform
    assert "to_port     = 9000" in terraform


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

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # PCI-DSS should enable WAF
    assert 'resource "aws_wafv2_web_acl"' in terraform


def test_generate_udp_and_icmp_rules():
    """Should generate rules for UDP and ICMP protocols"""
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

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'protocol    = "udp"' in terraform
    assert "from_port   = 123" in terraform
    assert 'protocol    = "icmp"' in terraform
    assert "from_port   = -1" in terraform


def test_generate_multiple_ports():
    """Should generate multiple ingress rules for multiple ports"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            network_tiers=[
                NetworkTier(
                    name="web",
                    firewall_rules=[
                        FirewallRule(
                            name="allow-web",
                            protocol="tcp",
                            ports=[80, 443, 8080],
                            source="0.0.0.0/0",
                            action="allow",
                        )
                    ],
                )
            ],
        ),
    )

    generator = AWSSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # Should have three ingress rules (one per port)
    assert terraform.count("ingress {") == 3
    assert "from_port   = 80" in terraform
    assert "from_port   = 443" in terraform
    assert "from_port   = 8080" in terraform
