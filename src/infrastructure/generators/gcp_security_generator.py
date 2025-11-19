"""
GCP Security Generator

Generates GCP security resources (Firewall Rules, Cloud Armor, Cloud VPN) from universal security schema.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    UniversalInfrastructure,
)


class GCPSecurityGenerator:
    """Generate GCP security resources from universal schema"""

    def __init__(self, template_dir: Path | None = None):
        if template_dir is None:
            template_dir = (
                Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"
            )

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Add custom filters
        self.env.filters["map_protocol"] = self._map_protocol
        self.env.filters["format_ports"] = self._format_ports
        self.env.filters["get_target_tags"] = self._get_target_tags
        self.env.filters["get_source_tags"] = self._get_source_tags

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate GCP security resources as Terraform"""
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
        template = self.env.get_template("gcp_security_tiered.tf.j2")

        # Apply compliance preset effects
        waf_enabled = infrastructure.security.waf.enabled
        vpn_enabled = infrastructure.security.vpn.enabled

        if infrastructure.security.compliance_preset:
            waf_enabled = waf_enabled or self._should_enable_cloud_armor_for_preset(
                infrastructure.security.compliance_preset
            )
            vpn_enabled = vpn_enabled or self._should_enable_cloud_vpn_for_preset(
                infrastructure.security.compliance_preset
            )

        # Prepare context for template
        context = {
            "infrastructure": infrastructure,
            "firewall_rules": self._build_firewall_rules(infrastructure),
            "waf_enabled": waf_enabled,
            "vpn_enabled": vpn_enabled,
        }

        return template.render(**context)

    def _should_enable_cloud_armor_for_preset(self, preset: CompliancePreset) -> bool:
        """Check if Cloud Armor should be enabled for compliance preset"""
        return preset in [CompliancePreset.PCI_DSS, CompliancePreset.HIPAA]

    def _should_enable_cloud_vpn_for_preset(self, preset: CompliancePreset) -> bool:
        """Check if Cloud VPN should be enabled for compliance preset"""
        return preset in [CompliancePreset.HIPAA, CompliancePreset.SOC2]

    def _build_firewall_rules(self, infrastructure: UniversalInfrastructure) -> list[dict]:
        """Build firewall rule configurations from network tiers"""
        firewall_rules = []

        for tier in infrastructure.security.network_tiers:
            for rule in tier.firewall_rules:
                if rule.action == "allow":
                    gcp_rule = self._convert_firewall_rule_to_gcp(rule, tier, infrastructure)
                    if gcp_rule:
                        firewall_rules.append(gcp_rule)

        return firewall_rules

    def _convert_firewall_rule_to_gcp(
        self, rule: FirewallRule, tier: NetworkTier, infrastructure: UniversalInfrastructure
    ) -> dict | None:
        """Convert FirewallRule to GCP firewall rule format"""
        gcp_rule = {
            "name": f"{tier.name}_{rule.name.lower().replace(' ', '_').replace('-', '_')}",
            "network": f"google_compute_network.{infrastructure.name}.name",
            "allow": [],
            "target_tags": [tier.name],
        }

        # Handle source
        if rule.source == "0.0.0.0/0" or rule.source == "internet":
            gcp_rule["source_ranges"] = ["0.0.0.0/0"]
        elif rule.source in [t.name for t in infrastructure.security.network_tiers]:
            # Cross-tier reference using network tags
            gcp_rule["source_tags"] = [rule.source]
        else:
            # Assume it's a CIDR block
            gcp_rule["source_ranges"] = [rule.source]

        # Handle ports and protocol
        allow_block = {
            "protocol": self._map_protocol(rule.protocol),
        }

        # Handle ports
        if rule.ports:
            allow_block["ports"] = [str(port) for port in rule.ports]
        elif rule.port_ranges:
            # GCP supports port ranges in the same format
            allow_block["ports"] = rule.port_ranges

        gcp_rule["allow"].append(allow_block)

        return gcp_rule

    def _map_protocol(self, protocol: str) -> str:
        """Map universal protocol to GCP protocol"""
        protocol_map = {"tcp": "tcp", "udp": "udp", "icmp": "icmp", "all": "all"}
        return protocol_map.get(protocol, protocol)

    def _format_ports(self, ports: list[int]) -> str:
        """Format port list for template"""
        if not ports:
            return "all"
        return str(ports[0])  # Simplified for now

    def _get_target_tags(
        self, tier_name: str, infrastructure: UniversalInfrastructure
    ) -> list[str]:
        """Get target tags for a tier"""
        return [tier_name]

    def _get_source_tags(
        self, source_tier: str, infrastructure: UniversalInfrastructure
    ) -> list[str]:
        """Get source tags for cross-tier rules"""
        if source_tier in [tier.name for tier in infrastructure.security.network_tiers]:
            return [source_tier]
        return []
