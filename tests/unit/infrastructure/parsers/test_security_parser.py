"""
Test Security Pattern Parser

Tests for parsing user-friendly security YAML into universal schema:
- Tier-based firewall syntax
- Service name expansion (http → 80, postgresql → 5432)
- Compliance preset application
- WAF and VPN configuration
"""

import pytest

from src.infrastructure.parsers.security_parser import SecurityPatternParser
from src.infrastructure.universal_infra_schema import (
    CompliancePreset,
)


def test_parse_tier_based_firewall():
    """Should parse high-level tier syntax into firewall rules"""
    yaml_content = """
    security:
      firewall:
        web:
          - allow: http, https
            from: internet
        api:
          - allow: 8080
            from: web
    """
    parser = SecurityPatternParser()
    config = parser.parse(yaml_content)

    assert len(config.firewall_rules) == 2
    assert config.firewall_rules[0].ports == [80, 443]
    assert config.firewall_rules[1].source == "web"


def test_parse_service_name_expansion():
    """Should expand service names to port numbers"""
    yaml_content = """
    security:
      firewall:
        database:
          - allow: postgresql
            from: api
          - allow: mysql
            from: web
    """
    parser = SecurityPatternParser()
    config = parser.parse(yaml_content)

    assert len(config.firewall_rules) == 2
    assert config.firewall_rules[0].ports == [5432]  # postgresql
    assert config.firewall_rules[1].ports == [3306]  # mysql


def test_parse_compliance_preset():
    """Should apply compliance preset defaults"""
    yaml_content = """
    security:
      tier: pci-compliant
      firewall:
        web:
          - allow: https
            from: internet
    """
    parser = SecurityPatternParser()
    config = parser.parse(yaml_content)

    assert config.compliance_preset == CompliancePreset.PCI_DSS
    assert config.encryption_at_rest is True
    assert config.encryption_in_transit is True
    assert config.waf.enabled is True


def test_parse_waf_configuration():
    """Should parse WAF settings"""
    yaml_content = """
    security:
      waf: enabled
      firewall:
        web:
          - allow: https
            from: internet
    """
    parser = SecurityPatternParser()
    config = parser.parse(yaml_content)

    assert config.waf.enabled is True
    assert config.waf.mode == "prevention"
    assert "OWASP_TOP_10" in config.waf.rule_sets


def test_parse_vpn_configuration():
    """Should parse VPN settings"""
    yaml_content = """
    security:
      vpn: enabled
      firewall:
        admin:
          - allow: ssh
            from: office
    """
    parser = SecurityPatternParser()
    config = parser.parse(yaml_content)

    assert config.vpn.enabled is True
    assert config.vpn.type == "site-to-site"


def test_parse_network_tiers():
    """Should create NetworkTier objects from tier definitions"""
    yaml_content = """
    security:
      firewall:
        web:
          - allow: http, https
            from: internet
        api:
          - allow: 8080
            from: web
        database:
          - allow: postgresql
            from: api
    """
    parser = SecurityPatternParser()
    config = parser.parse(yaml_content)

    assert len(config.network_tiers) == 3

    web_tier = next(t for t in config.network_tiers if t.name == "web")
    api_tier = next(t for t in config.network_tiers if t.name == "api")
    db_tier = next(t for t in config.network_tiers if t.name == "database")

    assert len(web_tier.firewall_rules) == 1
    assert len(api_tier.firewall_rules) == 1
    assert len(db_tier.firewall_rules) == 1

    assert web_tier.firewall_rules[0].ports == [80, 443]
    assert api_tier.firewall_rules[0].ports == [8080]
    assert db_tier.firewall_rules[0].ports == [5432]


def test_parse_mixed_ports_and_ranges():
    """Should handle both individual ports and port ranges"""
    yaml_content = """
    security:
      firewall:
        app:
          - allow: 8080, 8443
            from: load-balancer
          - allow: 9000-9100
            from: monitoring
    """
    parser = SecurityPatternParser()
    config = parser.parse(yaml_content)

    assert len(config.firewall_rules) == 2

    # First rule: individual ports
    rule1 = config.firewall_rules[0]
    assert rule1.ports == [8080, 8443]
    assert rule1.port_ranges == []

    # Second rule: port range
    rule2 = config.firewall_rules[1]
    assert rule2.ports == []
    assert rule2.port_ranges == ["9000-9100"]


def test_parse_complex_security_config():
    """Should parse complete security configuration with all features"""
    yaml_content = """
    security:
      tier: hardened
      firewall:
        web:
          - allow: http, https
            from: internet
        api:
          - allow: 8080
            from: web
        database:
          - allow: postgresql
            from: api
      waf: enabled
      vpn: enabled
    """
    parser = SecurityPatternParser()
    config = parser.parse(yaml_content)

    # Compliance preset
    assert config.compliance_preset == CompliancePreset.HARDENED

    # Network tiers
    assert len(config.network_tiers) == 3

    # Firewall rules
    assert len(config.firewall_rules) == 3

    # WAF and VPN
    assert config.waf.enabled is True
    assert config.vpn.enabled is True


def test_parse_invalid_service_name():
    """Should raise error for unknown service names"""
    yaml_content = """
    security:
      firewall:
        web:
          - allow: unknown-service
            from: internet
    """
    parser = SecurityPatternParser()

    with pytest.raises(ValueError, match="Unknown service names: unknown-service"):
        parser.parse(yaml_content)


def test_parse_invalid_yaml():
    """Should raise error for invalid YAML"""
    yaml_content = """
    security:
      firewall:
        web:
          - allow: http
            from: internet
        invalid_yaml_structure: [
    """
    parser = SecurityPatternParser()

    with pytest.raises(ValueError, match="Invalid YAML format"):
        parser.parse(yaml_content)


def test_parse_missing_security_section():
    """Should raise error when security section is missing"""
    yaml_content = """
    some_other_section:
      key: value
    """
    parser = SecurityPatternParser()

    with pytest.raises(ValueError, match="YAML must contain a 'security' section"):
        parser.parse(yaml_content)
