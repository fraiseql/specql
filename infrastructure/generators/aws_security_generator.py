"""
AWS Security Generator

Generates AWS security resources (Security Groups, WAF, VPN) from universal security schema.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    UniversalInfrastructure,
)


class AWSSecurityGenerator:
    """Generate AWS security resources from universal schema"""

    def __init__(self, template_dir: Path | None = None):
        if template_dir is None:
            template_dir = (
                Path(__file__).parent.parent.parent / "templates" / "infrastructure"
            )

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Add custom filters
        self.env.filters["map_protocol"] = self._map_protocol
        self.env.filters["format_ports"] = self._format_ports
        self.env.filters["get_security_group_refs"] = self._get_security_group_refs

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate AWS security resources as Terraform"""
        # Always use tiered security if we have network tiers or security features enabled
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
        template = self.env.get_template("aws_security_tiered.tf.j2")

        # Apply compliance preset effects
        waf_enabled = infrastructure.security.waf.enabled
        vpn_enabled = infrastructure.security.vpn.enabled

        if infrastructure.security.compliance_preset:
            waf_enabled = waf_enabled or self._should_enable_waf_for_preset(
                infrastructure.security.compliance_preset
            )
            vpn_enabled = vpn_enabled or self._should_enable_vpn_for_preset(
                infrastructure.security.compliance_preset
            )

        # Prepare context for template
        context = {
            "infrastructure": infrastructure,
            "security_groups": self._build_security_groups(infrastructure),
            "waf_enabled": waf_enabled,
            "vpn_enabled": vpn_enabled,
        }

        return template.render(**context)

    def _should_enable_waf_for_preset(self, preset: CompliancePreset) -> bool:
        """Check if WAF should be enabled for compliance preset"""
        return preset in [CompliancePreset.PCI_DSS, CompliancePreset.HIPAA]

    def _should_enable_vpn_for_preset(self, preset: CompliancePreset) -> bool:
        """Check if VPN should be enabled for compliance preset"""
        return preset in [CompliancePreset.HIPAA, CompliancePreset.SOC2]

    def _build_security_groups(self, infrastructure: UniversalInfrastructure) -> dict[str, dict]:
        """Build security group configurations from network tiers"""
        security_groups = {}

        for tier in infrastructure.security.network_tiers:
            sg_config = self._create_security_group_config(infrastructure, tier)
            security_groups[tier.name] = sg_config

        return security_groups

    def _create_security_group_config(
        self, infrastructure: UniversalInfrastructure, tier: NetworkTier
    ) -> dict:
        """Create a security group configuration for a network tier"""
        sg_config = {
            "name": f"{infrastructure.name}-{tier.name}",
            "vpc_id": f"aws_vpc.{infrastructure.name}.id",
            "ingress_rules": [],
            "egress_rules": [],
            "tags": self._create_security_group_tags(infrastructure, tier),
        }

        # Convert firewall rules to ingress rules
        for rule in tier.firewall_rules:
            if rule.action == "allow":
                ingress_rules = self._convert_firewall_rule_to_ingress_rules(rule, infrastructure)
                sg_config["ingress_rules"].extend(ingress_rules)

        # Add default egress rule
        sg_config["egress_rules"].append(self._create_default_egress_rule())

        return sg_config

    def _create_security_group_tags(
        self, infrastructure: UniversalInfrastructure, tier: NetworkTier
    ) -> dict[str, str]:
        """Create tags for a security group"""
        return {
            "Name": f"{infrastructure.name}-{tier.name}-sg",
            "Tier": tier.name,
            "Environment": infrastructure.environment,
            "ManagedBy": "SpecQL",
        }

    def _create_default_egress_rule(self) -> dict:
        """Create the default egress rule for security groups"""
        return {
            "from_port": 0,
            "to_port": 0,
            "protocol": "-1",
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow all outbound traffic",
        }

    def _convert_firewall_rule_to_ingress_rules(
        self, rule: FirewallRule, infrastructure: UniversalInfrastructure
    ) -> list[dict]:
        """Convert FirewallRule to AWS ingress rule(s) format"""
        base_ingress = {
            "protocol": self._map_protocol(rule.protocol),
            "description": rule.description or f"Allow {rule.name}",
        }

        # Handle source
        if rule.source == "0.0.0.0/0" or rule.source == "internet":
            base_ingress["cidr_blocks"] = ["0.0.0.0/0"]
        elif rule.source in [tier.name for tier in infrastructure.security.network_tiers]:
            # Cross-tier reference
            base_ingress["security_groups"] = [f"aws_security_group.{rule.source}.id"]
        else:
            # Assume it's a CIDR block
            base_ingress["cidr_blocks"] = [rule.source]

        ingress_rules = []

        # Handle ports - create one rule per port
        if rule.ports:
            for port in rule.ports:
                ingress = base_ingress.copy()
                ingress["from_port"] = str(port)
                ingress["to_port"] = str(port)
                ingress_rules.append(ingress)
        elif rule.port_ranges:
            # Handle port ranges
            for port_range in rule.port_ranges:
                start_port, end_port = self._parse_port_range(port_range)
                ingress = base_ingress.copy()
                ingress["from_port"] = str(start_port)
                ingress["to_port"] = str(end_port)
                ingress_rules.append(ingress)
        else:
            # Default for protocols without ports
            ingress = base_ingress.copy()
            ingress["from_port"] = "0"
            ingress["to_port"] = "0"
            ingress_rules.append(ingress)

        return ingress_rules

    def _map_protocol(self, protocol: str) -> str:
        """Map universal protocol to AWS protocol"""
        protocol_map = {"tcp": "tcp", "udp": "udp", "icmp": "icmp", "all": "-1"}
        return protocol_map.get(protocol, protocol)

    def _parse_port_range(self, port_range: str) -> tuple[int, int]:
        """Parse a port range string like '8000-9000'"""
        try:
            start_port, end_port = map(int, port_range.split("-"))
            if start_port > end_port:
                raise ValueError(f"Invalid port range: {port_range}")
            return start_port, end_port
        except ValueError as e:
            raise ValueError(f"Invalid port range format '{port_range}': {e}")

    def _format_ports(self, ports: list[int]) -> str:
        """Format port list for template"""
        if not ports:
            return "0"
        return str(ports[0])  # Simplified for now

    def _get_security_group_refs(
        self, source_tier: str, infrastructure: UniversalInfrastructure
    ) -> list[str]:
        """Get security group references for cross-tier rules"""
        refs = []
        for tier in infrastructure.security.network_tiers:
            if source_tier == tier.name:
                refs.append(f"aws_security_group.{tier.name}.id")
        return refs
