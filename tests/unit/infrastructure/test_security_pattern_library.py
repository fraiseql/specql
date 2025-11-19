"""
Test Security Pattern Library

Tests for the security pattern library functionality:
- Pattern retrieval and listing
- Pattern composition and merging
- Pattern validation
- Pattern application to infrastructure
"""

import pytest
from src.infrastructure.security_pattern_library import SecurityPatternLibrary, SecurityPattern
from src.infrastructure.universal_infra_schema import (
    UniversalInfrastructure,
    SecurityConfig,
    NetworkTier,
    FirewallRule,
    WAFConfig,
    VPNConfig,
    CompliancePreset,
)


def test_get_pattern():
    """Should retrieve a pattern by name"""
    library = SecurityPatternLibrary()

    pattern = library.get_pattern("web-app-basic")
    assert pattern is not None
    assert pattern.name == "web-app-basic"
    assert "web" in pattern.tags
    assert "basic" in pattern.tags


def test_get_nonexistent_pattern():
    """Should return None for nonexistent patterns"""
    library = SecurityPatternLibrary()

    pattern = library.get_pattern("nonexistent-pattern")
    assert pattern is None


def test_list_patterns():
    """Should list all available patterns"""
    library = SecurityPatternLibrary()

    patterns = library.list_patterns()
    assert len(patterns) > 0
    assert any(p.name == "web-app-basic" for p in patterns)
    assert any(p.name == "three-tier-app" for p in patterns)


def test_list_patterns_with_tags():
    """Should filter patterns by tags"""
    library = SecurityPatternLibrary()

    web_patterns = library.list_patterns(tags=["web"])
    assert len(web_patterns) > 0
    assert all("web" in p.tags for p in web_patterns)

    secure_patterns = library.list_patterns(tags=["secure"])
    assert len(secure_patterns) > 0
    assert all("secure" in p.tags for p in secure_patterns)


def test_compose_patterns():
    """Should compose multiple patterns into one security config"""
    library = SecurityPatternLibrary()

    # Compose web app with database cluster
    composed_config = library.compose_patterns(["web-app-basic", "database-cluster"])

    assert len(composed_config.network_tiers) == 2
    tier_names = [tier.name for tier in composed_config.network_tiers]
    assert "web" in tier_names
    assert "database" in tier_names


def test_compose_patterns_with_conflicts():
    """Should merge patterns with conflicting configurations"""
    library = SecurityPatternLibrary()

    # Compose patterns with different compliance presets
    composed_config = library.compose_patterns(["web-app-secure", "pci-compliant-web"])

    # Should use the last pattern's compliance preset
    assert composed_config.compliance_preset == CompliancePreset.PCI_DSS
    assert composed_config.waf.enabled == True


def test_compose_nonexistent_pattern():
    """Should raise error for nonexistent patterns"""
    library = SecurityPatternLibrary()

    with pytest.raises(ValueError, match="Pattern 'nonexistent' not found"):
        library.compose_patterns(["web-app-basic", "nonexistent"])


def test_validate_pattern_compatibility():
    """Should validate pattern compatibility"""
    library = SecurityPatternLibrary()

    # Compatible patterns
    warnings = library.validate_pattern_compatibility(["web-app-basic", "database-cluster"])
    assert len(warnings) == 0

    # Patterns with conflicting compliance and duplicate tiers
    warnings = library.validate_pattern_compatibility(["web-app-secure", "pci-compliant-web"])
    assert len(warnings) >= 1
    assert any(
        "compliance presets" in warning or "duplicate" in warning.lower() for warning in warnings
    )


def test_apply_pattern_to_infrastructure():
    """Should apply a pattern to existing infrastructure"""
    library = SecurityPatternLibrary()

    # Create basic infrastructure
    infra = UniversalInfrastructure(
        name="test-app",
        region="us-east-1",
    )

    # Apply secure web app pattern
    new_infra = library.apply_pattern_to_infrastructure(infra, "web-app-secure")

    assert new_infra.name == "test-app"
    assert new_infra.region == "us-east-1"
    assert len(new_infra.security.network_tiers) == 1
    assert new_infra.security.network_tiers[0].name == "web"
    assert new_infra.security.waf.enabled == True


def test_pattern_to_security_config():
    """Should convert pattern to security config"""
    pattern = SecurityPattern(
        name="test-pattern",
        description="Test pattern",
        network_tiers=[
            NetworkTier(
                name="test-tier",
                firewall_rules=[
                    FirewallRule(
                        name="test-rule",
                        protocol="tcp",
                        ports=[80],
                        source="0.0.0.0/0",
                        action="allow",
                    )
                ],
            )
        ],
        waf_config=WAFConfig(enabled=True),
        compliance_preset=CompliancePreset.PCI_DSS,
    )

    config = pattern.to_security_config()

    assert len(config.network_tiers) == 1
    assert config.network_tiers[0].name == "test-tier"
    assert config.waf.enabled == True
    assert config.compliance_preset == CompliancePreset.PCI_DSS


def test_builtin_patterns_exist():
    """Should have all expected built-in patterns"""
    library = SecurityPatternLibrary()

    expected_patterns = [
        "web-app-basic",
        "web-app-secure",
        "api-gateway",
        "database-cluster",
        "microservices",
        "three-tier-app",
        "pci-compliant-web",
        "hipaa-compliant-api",
    ]

    for pattern_name in expected_patterns:
        pattern = library.get_pattern(pattern_name)
        assert pattern is not None, f"Pattern {pattern_name} should exist"
        assert pattern.name == pattern_name


def test_web_app_basic_pattern():
    """Should have correct configuration for web-app-basic pattern"""
    library = SecurityPatternLibrary()
    pattern = library.get_pattern("web-app-basic")

    assert pattern is not None
    assert len(pattern.network_tiers) == 1
    assert pattern.network_tiers[0].name == "web"
    assert len(pattern.network_tiers[0].firewall_rules) == 1
    assert pattern.network_tiers[0].firewall_rules[0].ports == [80, 443]
    assert pattern.waf_config is None
    assert "web" in pattern.tags
    assert "basic" in pattern.tags


def test_three_tier_app_pattern():
    """Should have correct three-tier configuration"""
    library = SecurityPatternLibrary()
    pattern = library.get_pattern("three-tier-app")

    assert pattern is not None
    assert len(pattern.network_tiers) == 3

    tier_names = [tier.name for tier in pattern.network_tiers]
    assert "web" in tier_names
    assert "app" in tier_names
    assert "database" in tier_names

    # Check cross-tier references
    app_tier = next(tier for tier in pattern.network_tiers if tier.name == "app")
    db_tier = next(tier for tier in pattern.network_tiers if tier.name == "database")

    assert len(app_tier.firewall_rules) == 1
    assert app_tier.firewall_rules[0].source == "web"

    assert len(db_tier.firewall_rules) == 1
    assert db_tier.firewall_rules[0].source == "app"


def test_compliance_patterns():
    """Should have correct compliance configurations"""
    library = SecurityPatternLibrary()

    pci_pattern = library.get_pattern("pci-compliant-web")
    hipaa_pattern = library.get_pattern("hipaa-compliant-api")

    assert pci_pattern is not None
    assert pci_pattern.compliance_preset == CompliancePreset.PCI_DSS
    assert pci_pattern.waf_config is not None
    assert pci_pattern.waf_config.enabled == True

    assert hipaa_pattern is not None
    assert hipaa_pattern.compliance_preset == CompliancePreset.HIPAA
    assert hipaa_pattern.waf_config is not None
    assert hipaa_pattern.waf_config.enabled == True
    assert hipaa_pattern.vpn_config is not None
    assert hipaa_pattern.vpn_config.enabled == True


def test_pattern_metadata():
    """Should have proper metadata for patterns"""
    library = SecurityPatternLibrary()

    for pattern in library.list_patterns():
        assert pattern.name
        assert pattern.description
        assert isinstance(pattern.tags, list)
        assert isinstance(pattern.metadata, dict)
