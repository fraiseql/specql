"""
Azure Security Generator

Generates Azure security resources (NSGs, Application Gateway WAF, VPN Gateway) from universal security schema.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    UniversalInfrastructure,
)


class AzureSecurityGenerator:
    """Generate Azure security resources from universal schema"""

    def __init__(self, template_dir: Path | None = None):
        if template_dir is None:
            template_dir = (
                Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"
            )

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Add custom filters
        self.env.filters["map_protocol"] = self._map_protocol
        self.env.filters["format_ports"] = self._format_ports
        self.env.filters["get_nsg_refs"] = self._get_nsg_refs

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Azure security resources as Terraform"""
        # Always use tiered security if we have security features enabled
        has_security_features = (
            infrastructure.security.network_tiers
            or infrastructure.security.waf.enabled
            or infrastructure.security.vpn.enabled
            or infrastructure.security.firewall_rules
        )

        if has_security_features:
            return self._generate_tiered_security(infrastructure)
        else:
            return self._generate_basic_security(infrastructure)

    def _generate_basic_security(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate basic security resources for backward compatibility"""
        # For now, return empty string - basic security is handled by main terraform generator
        return ""

    def _generate_tiered_security(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate tiered security resources from universal schema"""
        template = self.env.get_template("azure_security_tiered.tf.j2")

        # Apply compliance preset effects
        waf_enabled = infrastructure.security.waf.enabled
        vpn_enabled = infrastructure.security.vpn.enabled

        if infrastructure.security.compliance_preset:
            waf_enabled = waf_enabled or self._should_enable_app_gateway_waf_for_preset(
                infrastructure.security.compliance_preset
            )
            vpn_enabled = vpn_enabled or self._should_enable_vpn_gateway_for_preset(
                infrastructure.security.compliance_preset
            )

        # Prepare context for template
        context = {
            "infrastructure": infrastructure,
            "nsg_rules": self._build_nsg_rules(infrastructure),
            "waf_enabled": waf_enabled,
            "vpn_enabled": vpn_enabled,
        }

        return template.render(**context)

    def _should_enable_app_gateway_waf_for_preset(self, preset: CompliancePreset) -> bool:
        """Check if Application Gateway WAF should be enabled for compliance preset"""
        return preset in [CompliancePreset.PCI_DSS, CompliancePreset.HIPAA]

    def _should_enable_vpn_gateway_for_preset(self, preset: CompliancePreset) -> bool:
        """Check if VPN Gateway should be enabled for compliance preset"""
        return preset in [CompliancePreset.HIPAA, CompliancePreset.SOC2]

    def _build_nsg_rules(self, infrastructure: UniversalInfrastructure) -> list[dict]:
        """Build NSG security rule configurations from network tiers"""
        nsg_rules = []

        for tier in infrastructure.security.network_tiers:
            for rule in tier.firewall_rules:
                if rule.action == "allow":
                    azure_rule = self._convert_firewall_rule_to_azure(rule, tier, infrastructure)
                    if azure_rule:
                        nsg_rules.append(azure_rule)

        return nsg_rules

    def _convert_firewall_rule_to_azure(
        self, rule: FirewallRule, tier: NetworkTier, infrastructure: UniversalInfrastructure
    ) -> dict | None:
        """Convert FirewallRule to Azure NSG security rule format"""
        azure_rule = {
            "name": f"{tier.name}_{rule.name.lower().replace(' ', '_').replace('-', '_')}",
            "priority": self._calculate_rule_priority(tier, rule),
            "direction": "Inbound",
            "access": "Allow",
            "protocol": self._map_protocol(rule.protocol),
            "nsg_name": f"{infrastructure.name}_{tier.name}_nsg",
        }

        # Handle source
        if rule.source == "0.0.0.0/0" or rule.source == "internet":
            azure_rule["source_address_prefix"] = "*"
        elif rule.source in [t.name for t in infrastructure.security.network_tiers]:
            # Cross-tier reference using NSG name
            azure_rule["source_address_prefix"] = "*"
            azure_rule["source_application_security_group_ids"] = [
                f"azurerm_application_security_group.{rule.source}_asg.id"
            ]
        else:
            # Assume it's a CIDR block
            azure_rule["source_address_prefix"] = rule.source

        # Handle destination
        azure_rule["destination_address_prefix"] = "*"
        azure_rule["destination_application_security_group_ids"] = [
            f"azurerm_application_security_group.{tier.name}_asg.id"
        ]

        # Handle ports and protocol
        if rule.ports:
            azure_rule["destination_port_ranges"] = [str(port) for port in rule.ports]
        elif rule.port_ranges:
            # Azure supports port ranges in the same format
            azure_rule["destination_port_ranges"] = rule.port_ranges
        else:
            # All ports
            azure_rule["destination_port_range"] = "*"

        return azure_rule

    def _calculate_rule_priority(self, tier: NetworkTier, rule: FirewallRule) -> int:
        """Calculate rule priority based on tier and rule"""
        # Base priority by tier (web=100, api=200, db=300, etc.)
        tier_base = {"web": 100, "api": 200, "database": 300, "cache": 400}.get(tier.name, 500)

        # Add rule index within tier
        rule_index = 0
        for r in tier.firewall_rules:
            if r == rule:
                break
            rule_index += 1

        return tier_base + rule_index * 10

    def _map_protocol(self, protocol: str) -> str:
        """Map universal protocol to Azure protocol"""
        protocol_map = {"tcp": "Tcp", "udp": "Udp", "icmp": "Icmp", "all": "*"}
        return protocol_map.get(protocol, protocol)

    def _format_ports(self, ports: list[int]) -> str:
        """Format port list for template"""
        if not ports:
            return "*"
        return str(ports[0])  # Simplified for now

    def _get_nsg_refs(self, tier_name: str, infrastructure: UniversalInfrastructure) -> list[str]:
        """Get NSG references for a tier"""
        return [f"{infrastructure.name}_{tier_name}_nsg"]
