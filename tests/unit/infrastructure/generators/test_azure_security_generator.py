"""
Test Azure Security Generator

Tests for generating Azure security resources (NSGs, Application Gateway WAF, VPN Gateway) from universal schema:
- NSG security rule generation for network tiers
- Application Gateway WAF security policy generation
- VPN Gateway generation
- Cross-tier NSG references
"""

import pytest
from src.infrastructure.generators.azure_security_generator import AzureSecurityGenerator
from src.infrastructure.universal_infra_schema import (
    UniversalInfrastructure,
    SecurityConfig,
    NetworkTier,
    FirewallRule,
    WAFConfig,
    VPNConfig,
    CompliancePreset,
)


def test_generate_azure_nsg_rules():
    """Should generate Azure NSG security rules from universal schema"""
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

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "azurerm_network_security_group" "test-app_web_nsg"' in terraform
    assert 'resource "azurerm_application_security_group" "web_asg"' in terraform
    assert 'protocol                                   = "Tcp"' in terraform
    assert 'destination_port_ranges                     = ["80", "443"]' in terraform
    assert 'source_address_prefix                       = "*"' in terraform


def test_generate_azure_nsg_with_multiple_rules():
    """Should generate NSG rules for multiple tiers"""
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

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "azurerm_network_security_group" "test-app_web_nsg"' in terraform
    assert 'resource "azurerm_network_security_group" "test-app_api_nsg"' in terraform
    assert (
        'source_application_security_group_ids       = ["azurerm_application_security_group.web_asg.id"]'
        in terraform
    )


def test_generate_application_gateway_waf():
    """Should generate Application Gateway with WAF when WAF is enabled"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            waf=WAFConfig(enabled=True, mode="prevention", rule_sets=["OWASP_TOP_10"])
        ),
    )

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "azurerm_application_gateway" "test-app_app_gateway"' in terraform
    assert 'firewall_mode    = "Prevention"' in terraform
    assert 'rule_set_type    = "OWASP"' in terraform
    assert 'rule_set_version = "3.2"' in terraform


def test_generate_vpn_gateway():
    """Should generate VPN Gateway when VPN is enabled"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            vpn=VPNConfig(enabled=True, type="site-to-site", remote_cidr="192.168.0.0/16")
        ),
    )

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'resource "azurerm_virtual_network_gateway" "test-app_vpn_gateway"' in terraform
    assert 'resource "azurerm_local_network_gateway" "test-app_local_gw"' in terraform
    assert (
        'resource "azurerm_virtual_network_gateway_connection" "test-app_vpn_connection"'
        in terraform
    )
    assert "192.168.0.0/16" in terraform


def test_generate_cross_tier_nsg_references():
    """Should generate NSG rules with ASG references for cross-tier access"""
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

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # Web tier allows from internet
    assert 'resource "azurerm_network_security_group" "test-app_web_nsg"' in terraform
    assert 'source_address_prefix                       = "*"' in terraform

    # API tier allows from web ASG
    assert 'resource "azurerm_network_security_group" "test-app_api_nsg"' in terraform
    assert (
        'source_application_security_group_ids       = ["azurerm_application_security_group.web_asg.id"]'
        in terraform
    )

    # Database tier allows from api ASG
    assert 'resource "azurerm_network_security_group" "test-app_database_nsg"' in terraform
    assert (
        'source_application_security_group_ids       = ["azurerm_application_security_group.api_asg.id"]'
        in terraform
    )


def test_generate_port_ranges():
    """Should generate NSG rules with port ranges"""
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

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'destination_port_ranges                     = ["8000-9000"]' in terraform


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

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # PCI-DSS should enable Application Gateway WAF
    assert 'resource "azurerm_application_gateway"' in terraform


def test_generate_udp_and_icmp_rules():
    """Should generate NSG rules for UDP and ICMP protocols"""
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

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    assert 'protocol                                   = "Udp"' in terraform
    assert 'destination_port_ranges                     = ["123"]' in terraform
    assert 'protocol                                   = "Icmp"' in terraform


def test_generate_multiple_ports():
    """Should generate NSG rules with multiple ports"""
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

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # Azure NSG rules support multiple ports in destination_port_ranges
    assert 'destination_port_ranges                     = ["80", "443", "8080"]' in terraform


def test_rule_priority_calculation():
    """Should calculate proper rule priorities based on tier and rule order"""
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
                            ports=[80],
                            source="0.0.0.0/0",
                            action="allow",
                        ),
                        FirewallRule(
                            name="allow-https",
                            protocol="tcp",
                            ports=[443],
                            source="0.0.0.0/0",
                            action="allow",
                        ),
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

    generator = AzureSecurityGenerator()
    terraform = generator.generate(infrastructure)

    # Web tier rules should have priority 100, 110
    assert "priority                                   = 100" in terraform
    assert "priority                                   = 110" in terraform
    # API tier rules should have priority 200
    assert "priority                                   = 200" in terraform
