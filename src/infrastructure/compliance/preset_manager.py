"""Compliance preset manager for automatic security control application"""

from dataclasses import replace
from typing import Dict, Any, List
from src.infrastructure.universal_infra_schema import (
    CompliancePreset,
    SecurityConfig,
    UniversalInfrastructure,
    WAFConfig,
    NetworkTier,
    FirewallRule,
)


class CompliancePresetManager:
    """Apply compliance framework requirements automatically"""

    def apply_preset(self, infrastructure: UniversalInfrastructure) -> UniversalInfrastructure:
        """Apply compliance preset to infrastructure"""
        if not infrastructure.security.compliance_preset:
            return infrastructure

        preset = infrastructure.security.compliance_preset

        # Apply preset-specific configurations
        if preset == CompliancePreset.PCI_DSS:
            return self._apply_pci_dss(infrastructure)
        elif preset == CompliancePreset.HIPAA:
            return self._apply_hipaa(infrastructure)
        elif preset == CompliancePreset.SOC2:
            return self._apply_soc2(infrastructure)
        elif preset == CompliancePreset.ISO27001:
            return self._apply_iso27001(infrastructure)
        else:
            return infrastructure

    def _apply_pci_dss(self, infrastructure: UniversalInfrastructure) -> UniversalInfrastructure:
        """Apply PCI-DSS requirements"""
        # PCI-DSS Requirements:
        # - Encryption at rest and in transit
        # - WAF enabled
        # - Network segmentation (3-tier minimum)
        # - Audit logging

        security = infrastructure.security

        # Enable encryption
        security.encryption_at_rest = True
        security.encryption_in_transit = True

        # Enable WAF with strict rules
        if not security.waf.enabled:
            security.waf = WAFConfig(
                enabled=True,
                mode="prevention",
                rule_sets=["OWASP_TOP_10", "SQL_INJECTION", "XSS"],
                rate_limiting=True,
            )

        # Enable audit logging
        security.audit_logging = True

        # Ensure network segmentation
        if len(security.network_tiers) < 3:
            # Add default 3-tier architecture if not present
            security.network_tiers = self._create_default_three_tier()

        return replace(infrastructure, security=security)

    def _apply_hipaa(self, infrastructure: UniversalInfrastructure) -> UniversalInfrastructure:
        """Apply HIPAA requirements"""
        # HIPAA Requirements:
        # - Encryption mandatory
        # - Access controls
        # - Audit trails
        # - PHI data isolation
        # - Backup retention (7 years)

        security = infrastructure.security

        security.encryption_at_rest = True
        security.encryption_in_transit = True
        security.audit_logging = True

        # HIPAA requires longer backup retention (7 years = 2555 days)
        if infrastructure.database:
            infrastructure.database.backup_retention_days = 2555

        return replace(infrastructure, security=security)

    def _apply_soc2(self, infrastructure: UniversalInfrastructure) -> UniversalInfrastructure:
        """Apply SOC2 requirements"""
        security = infrastructure.security

        security.encryption_at_rest = True
        security.encryption_in_transit = True
        security.audit_logging = True

        return replace(infrastructure, security=security)

    def _apply_iso27001(self, infrastructure: UniversalInfrastructure) -> UniversalInfrastructure:
        """Apply ISO27001 requirements"""
        security = infrastructure.security

        security.encryption_at_rest = True
        security.encryption_in_transit = True
        security.audit_logging = True

        return replace(infrastructure, security=security)

    def _create_default_three_tier(self) -> list[NetworkTier]:
        """Create default 3-tier network architecture"""
        return [
            NetworkTier(
                name="web",
                firewall_rules=[
                    FirewallRule(
                        name="allow_http_https",
                        protocol="tcp",
                        ports=[80, 443],
                        source="internet",
                        destination="web",
                    )
                ],
            ),
            NetworkTier(
                name="api",
                firewall_rules=[
                    FirewallRule(
                        name="allow_from_web",
                        protocol="tcp",
                        ports=[8080],
                        source="web",
                        destination="api",
                    )
                ],
            ),
            NetworkTier(
                name="database",
                firewall_rules=[
                    FirewallRule(
                        name="allow_from_api",
                        protocol="tcp",
                        ports=[5432],
                        source="api",
                        destination="database",
                    )
                ],
            ),
        ]

    def validate_compliance(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Validate infrastructure against compliance requirements"""
        if not infrastructure.security.compliance_preset:
            return {"compliant": True, "gaps": []}

        preset = infrastructure.security.compliance_preset
        gaps = []

        if preset == CompliancePreset.PCI_DSS:
            gaps = self._validate_pci_dss(infrastructure)
        elif preset == CompliancePreset.HIPAA:
            gaps = self._validate_hipaa(infrastructure)
        elif preset == CompliancePreset.SOC2:
            gaps = self._validate_soc2(infrastructure)
        elif preset == CompliancePreset.ISO27001:
            gaps = self._validate_iso27001(infrastructure)

        return {
            "compliant": len(gaps) == 0,
            "preset": preset.value,
            "gaps": gaps,
        }

    def _validate_pci_dss(self, infrastructure: UniversalInfrastructure) -> list[str]:
        """Check for PCI-DSS compliance gaps"""
        gaps = []
        security = infrastructure.security

        if not security.encryption_at_rest:
            gaps.append("PCI-DSS requires encryption at rest")

        if not security.encryption_in_transit:
            gaps.append("PCI-DSS requires encryption in transit")

        if not security.waf.enabled:
            gaps.append("PCI-DSS requires Web Application Firewall")

        if not security.audit_logging:
            gaps.append("PCI-DSS requires audit logging")

        if len(security.network_tiers) < 3:
            gaps.append("PCI-DSS requires network segmentation (3-tier minimum)")

        return gaps

    def _validate_hipaa(self, infrastructure: UniversalInfrastructure) -> list[str]:
        """Check for HIPAA compliance gaps"""
        gaps = []
        security = infrastructure.security

        if not security.encryption_at_rest:
            gaps.append("HIPAA requires encryption at rest")

        if not security.encryption_in_transit:
            gaps.append("HIPAA requires encryption in transit")

        if not security.audit_logging:
            gaps.append("HIPAA requires audit logging")

        return gaps

    def _validate_soc2(self, infrastructure: UniversalInfrastructure) -> list[str]:
        """Check for SOC2 compliance gaps"""
        gaps = []
        security = infrastructure.security

        if not security.encryption_at_rest:
            gaps.append("SOC2 requires encryption at rest")

        if not security.encryption_in_transit:
            gaps.append("SOC2 requires encryption in transit")

        if not security.audit_logging:
            gaps.append("SOC2 requires audit logging")

        return gaps

    def _validate_iso27001(self, infrastructure: UniversalInfrastructure) -> list[str]:
        """Check for ISO27001 compliance gaps"""
        gaps = []
        security = infrastructure.security

        if not security.encryption_at_rest:
            gaps.append("ISO27001 requires encryption at rest")

        if not security.encryption_in_transit:
            gaps.append("ISO27001 requires encryption in transit")

        if not security.audit_logging:
            gaps.append("ISO27001 requires audit logging")

        return gaps

    def combine_presets(
        self, infrastructure: UniversalInfrastructure, presets: List[CompliancePreset]
    ) -> UniversalInfrastructure:
        """Apply multiple compliance presets (most restrictive wins)"""
        if not presets:
            return infrastructure

        # Apply each preset in order, with later presets overriding earlier ones
        result = infrastructure
        for preset in presets:
            # Temporarily set the preset on security config
            temp_security = replace(result.security, compliance_preset=preset)
            temp_infra = replace(result, security=temp_security)

            # Apply the preset
            result = replace(
                temp_infra,
                security=replace(self.apply_preset(temp_infra).security, compliance_preset=None),
            )

        return result

    def get_preset_requirements(self, preset: CompliancePreset) -> Dict[str, Any]:
        """Get detailed requirements for a compliance preset"""
        requirements = {
            CompliancePreset.PCI_DSS: {
                "name": "PCI-DSS",
                "version": "4.0",
                "description": "Payment Card Industry Data Security Standard",
                "requirements": [
                    "Encryption at rest and in transit",
                    "Web Application Firewall (WAF) enabled",
                    "Audit logging enabled",
                    "Network segmentation (3-tier minimum)",
                    "Regular security scans",
                    "Strong access controls",
                ],
                "industry": "Financial Services",
                "mandatory_for": ["Payment processing", "Card data handling"],
            },
            CompliancePreset.HIPAA: {
                "name": "HIPAA",
                "version": "Security Rule",
                "description": "Health Insurance Portability and Accountability Act",
                "requirements": [
                    "Encryption at rest and in transit",
                    "Audit logging and access controls",
                    "PHI data isolation",
                    "7-year backup retention",
                    "Access logging",
                    "Breach notification procedures",
                ],
                "industry": "Healthcare",
                "mandatory_for": ["Protected Health Information (PHI) handling"],
            },
            CompliancePreset.SOC2: {
                "name": "SOC 2",
                "version": "Type II",
                "description": "System and Organization Controls 2",
                "requirements": [
                    "Security controls",
                    "Availability assurance",
                    "Processing integrity",
                    "Confidentiality protection",
                    "Privacy protection",
                    "Audit logging",
                ],
                "industry": "Technology Services",
                "mandatory_for": ["SaaS providers", "Cloud services"],
            },
            CompliancePreset.ISO27001: {
                "name": "ISO 27001",
                "version": "2022",
                "description": "Information Security Management Systems",
                "requirements": [
                    "Information security policy",
                    "Risk assessment and treatment",
                    "Access controls",
                    "Cryptography",
                    "Physical security",
                    "Operations security",
                    "Communications security",
                ],
                "industry": "All industries",
                "mandatory_for": ["Enterprise organizations", "Government contractors"],
            },
        }

        return requirements.get(preset, {})

    def generate_preset_documentation(self, preset: CompliancePreset) -> str:
        """Generate detailed documentation for a compliance preset"""
        reqs = self.get_preset_requirements(preset)
        if not reqs:
            return f"No documentation available for preset: {preset.value}"

        doc = f"""# {reqs["name"]} Compliance Requirements

**Version**: {reqs["version"]}
**Description**: {reqs["description"]}
**Industry**: {reqs["industry"]}
**Mandatory For**: {", ".join(reqs["mandatory_for"])}

## Security Controls Applied

When you specify `compliance_preset: {preset.value}` in your infrastructure YAML,
SpecQL automatically applies the following security controls:

"""

        for i, req in enumerate(reqs["requirements"], 1):
            doc += f"{i}. {req}\n"

        doc += """

## Example Usage

```yaml
security:
  compliance_preset: {preset.value}

  # Additional custom security settings
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
```

## Validation

SpecQL validates your infrastructure against these requirements and reports any gaps
that need to be addressed for full compliance.

"""
        return doc
