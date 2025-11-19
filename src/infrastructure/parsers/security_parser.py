"""
Security Pattern Parser

Parses user-friendly security YAML into universal security schema.
Supports tier-based firewall syntax, service name expansion, and compliance presets.
"""

from typing import Any

import yaml

from src.infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    SecurityConfig,
    VPNConfig,
    WAFConfig,
)


class SecurityPatternParser:
    """Parse user-friendly security YAML into universal schema"""

    # Standard service port mappings
    SERVICE_PORTS = {
        # Web services
        "http": 80,
        "https": 443,
        # Remote access
        "ssh": 22,
        # Databases
        "postgresql": 5432,
        "postgres": 5432,
        "mysql": 3306,
        "redis": 6379,
        "mongodb": 27017,
        "mongo": 27017,
        # File transfer
        "ftp": 21,
        "ftps": 990,
        # Email
        "smtp": 25,
        "smtps": 465,
        "imap": 143,
        "imaps": 993,
        "pop3": 110,
        "pop3s": 995,
        # Infrastructure
        "dns": 53,
        "dhcp": 67,
        "ntp": 123,
    }

    COMPLIANCE_PRESETS = {
        "standard": CompliancePreset.STANDARD,
        "hardened": CompliancePreset.HARDENED,
        "pci-compliant": CompliancePreset.PCI_DSS,
        "pci-dss": CompliancePreset.PCI_DSS,
        "hipaa": CompliancePreset.HIPAA,
        "soc2": CompliancePreset.SOC2,
        "iso27001": CompliancePreset.ISO27001,
    }

    def parse(self, yaml_content: str) -> SecurityConfig:
        """Parse security configuration from YAML"""
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")

        if not data:
            return SecurityConfig()

        if "security" not in data:
            raise ValueError("YAML must contain a 'security' section")

        security_data = data["security"]
        if not isinstance(security_data, dict):
            raise ValueError("'security' section must be a dictionary")

        # Parse compliance preset
        compliance_preset = self._parse_compliance_preset(security_data)

        # Parse firewall rules
        network_tiers, firewall_rules = self._parse_firewall_rules(security_data)

        # Parse WAF configuration
        waf_config = self._parse_waf_config(security_data)

        # Parse VPN configuration
        vpn_config = self._parse_vpn_config(security_data)

        # Apply compliance preset defaults
        if compliance_preset:
            waf_config, vpn_config = self._apply_compliance_defaults(
                compliance_preset, waf_config, vpn_config
            )

        return SecurityConfig(
            network_tiers=network_tiers,
            firewall_rules=firewall_rules,
            compliance_preset=compliance_preset,
            waf=waf_config,
            vpn=vpn_config,
        )

    def _parse_compliance_preset(self, security_data: dict[str, Any]) -> CompliancePreset | None:
        """Parse compliance preset from tier or compliance_preset field"""
        # Check compliance_preset field first (preferred)
        preset = security_data.get("compliance_preset")
        if preset and preset in self.COMPLIANCE_PRESETS:
            return self.COMPLIANCE_PRESETS[preset]

        # Fallback to tier field for backward compatibility
        tier = security_data.get("tier")
        if tier and tier in self.COMPLIANCE_PRESETS:
            return self.COMPLIANCE_PRESETS[tier]
        return None

    def _parse_firewall_rules(
        self, security_data: dict[str, Any]
    ) -> tuple[list[NetworkTier], list[FirewallRule]]:
        """Parse firewall rules from tier-based syntax"""
        network_tiers = []
        firewall_rules = []

        # Check for network_tiers format (preferred)
        network_tiers_data = security_data.get("network_tiers", [])
        if network_tiers_data:
            if not isinstance(network_tiers_data, list):
                raise ValueError("'network_tiers' section must be a list")

            for tier_data in network_tiers_data:
                if not isinstance(tier_data, dict):
                    continue  # Skip invalid entries

                tier_name = tier_data.get("name")
                if not tier_name:
                    continue  # Skip tiers without names

                tier_rules = []
                firewall_rules_data = tier_data.get("firewall_rules", [])
                if isinstance(firewall_rules_data, list):
                    for rule_data in firewall_rules_data:
                        if isinstance(rule_data, dict):
                            rule = self._parse_single_rule(rule_data, tier_name)
                            if rule:
                                tier_rules.append(rule)
                                firewall_rules.append(rule)

                network_tiers.append(NetworkTier(name=tier_name, firewall_rules=tier_rules))
        else:
            # Fallback to old firewall format for backward compatibility
            firewall_data = security_data.get("firewall", {})

            if not isinstance(firewall_data, dict):
                raise ValueError("'firewall' section must be a dictionary")

            for tier_name, rules in firewall_data.items():
                if not isinstance(rules, list):
                    raise ValueError(f"Firewall rules for tier '{tier_name}' must be a list")

                tier_rules = []
                for rule_data in rules:
                    if not isinstance(rule_data, dict):
                        raise ValueError("Each firewall rule must be a dictionary")

                    rule = self._parse_single_rule(rule_data, tier_name)
                    if rule:
                        tier_rules.append(rule)
                        firewall_rules.append(rule)

                network_tiers.append(NetworkTier(name=tier_name, firewall_rules=tier_rules))

        return network_tiers, firewall_rules

    def _parse_single_rule(
        self, rule_data: dict[str, Any], destination_tier: str
    ) -> FirewallRule | None:
        """Parse a single firewall rule"""
        if "allow" not in rule_data:
            return None

        allow_value = rule_data["allow"]
        # Convert to string if it's an integer
        if isinstance(allow_value, int):
            allow_value = str(allow_value)
        elif not isinstance(allow_value, str):
            return None

        source = rule_data.get("from", "0.0.0.0/0")

        # Handle service names and port lists
        ports, port_ranges = self._parse_ports_and_ranges(allow_value)

        return FirewallRule(
            name=f"{destination_tier}-rule",
            protocol="tcp",  # Default to TCP for now
            ports=ports,
            port_ranges=port_ranges,
            source=source,
            destination=destination_tier,
            action="allow",
        )

    def _parse_ports_and_ranges(self, allow_value: str) -> tuple[list[int], list[str]]:
        """Parse ports and port ranges from allow value"""
        ports = []
        port_ranges = []
        unknown_services = []

        # Split by comma and strip whitespace
        items = [item.strip() for item in allow_value.split(",")]

        for item in items:
            if item.isdigit():
                # Single port number
                port_num = int(item)
                if not (1 <= port_num <= 65535):
                    raise ValueError(f"Port number must be between 1-65535: {port_num}")
                ports.append(port_num)
            elif "-" in item and self._is_valid_port_range(item):
                # Valid port range
                port_ranges.append(item)
            elif item in self.SERVICE_PORTS:
                # Known service name
                ports.append(self.SERVICE_PORTS[item])
            else:
                # Unknown service or invalid format
                unknown_services.append(item)

        if unknown_services:
            raise ValueError(
                f"Unknown service names: {', '.join(unknown_services)}. "
                f"Supported services: {', '.join(sorted(self.SERVICE_PORTS.keys()))}"
            )

        return ports, port_ranges

    def _is_valid_port_range(self, port_range: str) -> bool:
        """Validate port range format (e.g., '8000-9000')"""
        try:
            start, end = port_range.split("-")
            start_port = int(start.strip())
            end_port = int(end.strip())
            return 1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port < end_port
        except ValueError:
            return False

    def _parse_waf_config(self, security_data: dict[str, Any]) -> WAFConfig:
        """Parse WAF configuration"""
        waf_enabled = security_data.get("waf") == "enabled"
        return WAFConfig(enabled=waf_enabled)

    def _parse_vpn_config(self, security_data: dict[str, Any]) -> VPNConfig:
        """Parse VPN configuration"""
        vpn_enabled = security_data.get("vpn") == "enabled"
        return VPNConfig(enabled=vpn_enabled)

    def _apply_compliance_defaults(
        self, preset: CompliancePreset, waf_config: WAFConfig, vpn_config: VPNConfig
    ) -> tuple[WAFConfig, VPNConfig]:
        """Apply compliance preset defaults to config objects"""
        if preset == CompliancePreset.PCI_DSS:
            # PCI-DSS requires WAF
            waf_config.enabled = True
        elif preset == CompliancePreset.HIPAA:
            # HIPAA has specific requirements
            pass
        # Add other preset defaults as needed

        return waf_config, vpn_config
