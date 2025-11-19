"""
Test Universal Security Schema

Tests for the enhanced security primitives in UniversalInfrastructure:
- FirewallRule dataclass
- NetworkTier dataclass
- CompliancePreset enum
- WAFConfig dataclass
- VPNConfig dataclass
"""

from src.infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    SecurityConfig,
    VPNConfig,
    WAFConfig,
)


def test_firewall_rule_parsing():
    """Universal firewall rule should parse tier-based security"""
    rule = FirewallRule(
        name="web-tier",
        protocol="tcp",
        ports=[80, 443],
        source="0.0.0.0/0",
        destination="web-tier",
        action="allow",
    )
    assert rule.protocol == "tcp"
    assert 443 in rule.ports


def test_network_tier_creation():
    """Network tier should contain firewall rules and CIDR blocks"""
    tier = NetworkTier(
        name="web",
        cidr_blocks=["10.0.1.0/24", "10.0.2.0/24"],
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
    assert tier.name == "web"
    assert len(tier.firewall_rules) == 1
    assert tier.firewall_rules[0].ports == [80, 443]


def test_compliance_preset_enum():
    """Compliance presets should be defined as enum values"""
    assert CompliancePreset.STANDARD == "standard"
    assert CompliancePreset.HARDENED == "hardened"
    assert CompliancePreset.PCI_DSS == "pci-compliant"
    assert CompliancePreset.HIPAA == "hipaa"


def test_waf_config_creation():
    """WAF configuration should support detection and prevention modes"""
    waf = WAFConfig(
        enabled=True,
        mode="prevention",
        rule_sets=["OWASP_TOP_10"],
        rate_limiting=True,
        geo_blocking=["CN", "RU"],
        ip_blacklist=["192.168.1.1"],
    )
    assert waf.enabled is True
    assert waf.mode == "prevention"
    assert "OWASP_TOP_10" in waf.rule_sets
    assert waf.rate_limiting is True
    assert "CN" in waf.geo_blocking


def test_vpn_config_creation():
    """VPN configuration should support different VPN types"""
    vpn = VPNConfig(enabled=True, type="site-to-site", remote_cidr="192.168.0.0/16", bgp_asn=65000)
    assert vpn.enabled is True
    assert vpn.type == "site-to-site"
    assert vpn.remote_cidr == "192.168.0.0/16"
    assert vpn.bgp_asn == 65000


def test_security_config_with_firewall_rules():
    """SecurityConfig should support firewall rules and network tiers"""
    config = SecurityConfig(
        network_tiers=[
            NetworkTier(
                name="web",
                firewall_rules=[
                    FirewallRule(
                        name="allow-web",
                        protocol="tcp",
                        ports=[80, 443],
                        source="internet",
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
        ],
        waf=WAFConfig(enabled=True),
        vpn=VPNConfig(enabled=False),
    )

    assert len(config.network_tiers) == 2
    assert config.network_tiers[0].name == "web"
    assert config.network_tiers[1].name == "api"
    assert config.waf.enabled is True
    assert config.vpn.enabled is False
