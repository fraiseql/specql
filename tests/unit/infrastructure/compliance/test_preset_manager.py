"""Tests for CompliancePresetManager"""

from src.infrastructure.universal_infra_schema import (
    CompliancePreset,
    DatabaseConfig,
    DatabaseType,
    SecurityConfig,
    UniversalInfrastructure,
    WAFConfig,
)


class TestCompliancePresetManager:
    """Test compliance preset application and validation"""

    def test_apply_pci_compliance_preset(self):
        """Should auto-configure PCI-DSS requirements"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="payment-app", security=SecurityConfig(compliance_preset=CompliancePreset.PCI_DSS)
        )

        preset_manager = CompliancePresetManager()
        enhanced = preset_manager.apply_preset(infrastructure)

        # PCI-DSS requires encryption
        assert enhanced.security.encryption_at_rest is True
        assert enhanced.security.encryption_in_transit is True

        # PCI-DSS requires WAF
        assert enhanced.security.waf.enabled is True

        # PCI-DSS requires audit logging
        assert enhanced.security.audit_logging is True

        # PCI-DSS requires network segmentation
        assert len(enhanced.security.network_tiers) >= 3  # web, app, db minimum

    def test_apply_hipaa_preset(self):
        """Should auto-configure HIPAA requirements"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="healthcare-app",
            security=SecurityConfig(compliance_preset=CompliancePreset.HIPAA),
            database=DatabaseConfig(type=DatabaseType.POSTGRESQL, version="15"),
        )

        preset_manager = CompliancePresetManager()
        enhanced = preset_manager.apply_preset(infrastructure)

        # HIPAA requires encryption
        assert enhanced.security.encryption_at_rest is True
        assert enhanced.security.encryption_in_transit is True

        # HIPAA requires audit logging
        assert enhanced.security.audit_logging is True

        # HIPAA requires 7-year backup retention
        assert enhanced.database.backup_retention_days == 2555  # 7 years

    def test_no_preset_returns_unchanged(self):
        """Should return infrastructure unchanged when no preset specified"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(name="app", security=SecurityConfig())

        preset_manager = CompliancePresetManager()
        result = preset_manager.apply_preset(infrastructure)

        assert result == infrastructure

    def test_validate_pci_compliance_gaps(self):
        """Should identify PCI-DSS compliance gaps"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        # Infrastructure missing required controls
        infrastructure = UniversalInfrastructure(
            name="incomplete-app",
            security=SecurityConfig(
                compliance_preset=CompliancePreset.PCI_DSS,
                encryption_at_rest=False,
                encryption_in_transit=False,
                waf=WAFConfig(enabled=False),
                audit_logging=False,
                network_tiers=[],  # No segmentation
            ),
        )

        preset_manager = CompliancePresetManager()
        result = preset_manager.validate_compliance(infrastructure)

        assert result["compliant"] is False
        assert "PCI-DSS requires encryption at rest" in result["gaps"]
        assert "PCI-DSS requires encryption in transit" in result["gaps"]
        assert "PCI-DSS requires Web Application Firewall" in result["gaps"]
        assert "PCI-DSS requires audit logging" in result["gaps"]
        assert "PCI-DSS requires network segmentation (3-tier minimum)" in result["gaps"]

    def test_validate_compliant_pci_infrastructure(self):
        """Should validate compliant PCI-DSS infrastructure"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        # Properly configured infrastructure
        infrastructure = UniversalInfrastructure(
            name="compliant-app",
            security=SecurityConfig(
                compliance_preset=CompliancePreset.PCI_DSS,
                encryption_at_rest=True,
                encryption_in_transit=True,
                waf=WAFConfig(enabled=True),
                audit_logging=True,
                network_tiers=[
                    {"name": "web"},  # At least 3 tiers
                    {"name": "app"},
                    {"name": "db"},
                ],
            ),
        )

        preset_manager = CompliancePresetManager()
        result = preset_manager.validate_compliance(infrastructure)

        assert result["compliant"] is True
        assert len(result["gaps"]) == 0

    def test_validate_no_preset(self):
        """Should return compliant when no preset specified"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(name="app", security=SecurityConfig())

        preset_manager = CompliancePresetManager()
        result = preset_manager.validate_compliance(infrastructure)

        assert result["compliant"] is True
        assert len(result["gaps"]) == 0

    def test_apply_soc2_preset(self):
        """Should auto-configure SOC2 requirements"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="saas-app", security=SecurityConfig(compliance_preset=CompliancePreset.SOC2)
        )

        preset_manager = CompliancePresetManager()
        enhanced = preset_manager.apply_preset(infrastructure)

        # SOC2 requires encryption
        assert enhanced.security.encryption_at_rest is True
        assert enhanced.security.encryption_in_transit is True

        # SOC2 requires audit logging
        assert enhanced.security.audit_logging is True

    def test_apply_iso27001_preset(self):
        """Should auto-configure ISO27001 requirements"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="enterprise-app",
            security=SecurityConfig(compliance_preset=CompliancePreset.ISO27001),
        )

        preset_manager = CompliancePresetManager()
        enhanced = preset_manager.apply_preset(infrastructure)

        # ISO27001 requires encryption
        assert enhanced.security.encryption_at_rest is True
        assert enhanced.security.encryption_in_transit is True

        # ISO27001 requires audit logging
        assert enhanced.security.audit_logging is True

    def test_validate_hipaa_compliance_gaps(self):
        """Should identify HIPAA compliance gaps"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="healthcare-app",
            security=SecurityConfig(
                compliance_preset=CompliancePreset.HIPAA,
                encryption_at_rest=False,
                encryption_in_transit=False,
                audit_logging=False,
            ),
        )

        preset_manager = CompliancePresetManager()
        result = preset_manager.validate_compliance(infrastructure)

        assert result["compliant"] is False
        assert "HIPAA requires encryption at rest" in result["gaps"]
        assert "HIPAA requires encryption in transit" in result["gaps"]
        assert "HIPAA requires audit logging" in result["gaps"]

    def test_validate_soc2_compliance_gaps(self):
        """Should identify SOC2 compliance gaps"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="saas-app",
            security=SecurityConfig(
                compliance_preset=CompliancePreset.SOC2,
                encryption_at_rest=False,
                audit_logging=False,
            ),
        )

        preset_manager = CompliancePresetManager()
        result = preset_manager.validate_compliance(infrastructure)

        assert result["compliant"] is False
        assert "SOC2 requires encryption at rest" in result["gaps"]
        assert "SOC2 requires audit logging" in result["gaps"]

    def test_validate_iso27001_compliance_gaps(self):
        """Should identify ISO27001 compliance gaps"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="enterprise-app",
            security=SecurityConfig(
                compliance_preset=CompliancePreset.ISO27001,
                encryption_in_transit=False,
                audit_logging=False,
            ),
        )

        preset_manager = CompliancePresetManager()
        result = preset_manager.validate_compliance(infrastructure)

        assert result["compliant"] is False
        assert "ISO27001 requires encryption in transit" in result["gaps"]
        assert "ISO27001 requires audit logging" in result["gaps"]

    def test_preset_combination_not_supported(self):
        """Should handle unsupported preset combinations gracefully"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="app",
            security=SecurityConfig(
                compliance_preset=CompliancePreset.STANDARD  # Not implemented
            ),
        )

        preset_manager = CompliancePresetManager()
        result = preset_manager.apply_preset(infrastructure)

        # Should return unchanged for unsupported presets
        assert result == infrastructure

    def test_network_tier_creation_for_pci(self):
        """Should create default 3-tier network when applying PCI-DSS to infrastructure without tiers"""
        from src.infrastructure.compliance.preset_manager import CompliancePresetManager

        infrastructure = UniversalInfrastructure(
            name="web-app",
            security=SecurityConfig(
                compliance_preset=CompliancePreset.PCI_DSS,
                network_tiers=[],  # No existing tiers
            ),
        )

        preset_manager = CompliancePresetManager()
        enhanced = preset_manager.apply_preset(infrastructure)

        # Should have created 3 tiers
        assert len(enhanced.security.network_tiers) == 3
        tier_names = [tier.name for tier in enhanced.security.network_tiers]
        assert "web" in tier_names
        assert "api" in tier_names
        assert "database" in tier_names
