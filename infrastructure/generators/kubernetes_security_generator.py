"""
Kubernetes Security Generator

Generates Kubernetes security resources (NetworkPolicies, RBAC, Pod Security Standards) from universal security schema.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    UniversalInfrastructure,
)


class KubernetesSecurityGenerator:
    """Generate Kubernetes security resources from universal schema"""

    def __init__(self, template_dir: Path | None = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Add custom filters
        self.env.filters["map_protocol"] = self._map_protocol
        self.env.filters["format_ports"] = self._format_ports
        self.env.filters["get_namespace_labels"] = self._get_namespace_labels

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Kubernetes security resources as YAML"""
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
        # For now, return empty string - basic security is handled by main kubernetes generator
        return ""

    def _generate_tiered_security(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate tiered security resources from universal schema"""
        template = self.env.get_template("kubernetes_security.yaml.j2")

        # Apply compliance preset effects
        rbac_enabled = infrastructure.security.waf.enabled or self._should_enable_rbac_for_preset(
            infrastructure.security.compliance_preset
        )
        network_policies_enabled = True  # Always enable network policies for tiered security
        pod_security_enabled = self._should_enable_pod_security_for_preset(
            infrastructure.security.compliance_preset
        )

        # Prepare context for template
        context = {
            "infrastructure": infrastructure,
            "network_policies": self._build_network_policies(infrastructure),
            "rbac_enabled": rbac_enabled,
            "network_policies_enabled": network_policies_enabled,
            "pod_security_enabled": pod_security_enabled,
            "service_accounts": self._build_service_accounts(infrastructure),
            "roles": self._build_roles(infrastructure),
            "role_bindings": self._build_role_bindings(infrastructure),
        }

        return template.render(**context)

    def _should_enable_rbac_for_preset(self, preset: CompliancePreset | None) -> bool:
        """Check if RBAC should be enabled for compliance preset"""
        if preset is None:
            return False
        return preset in [CompliancePreset.PCI_DSS, CompliancePreset.HIPAA, CompliancePreset.SOC2]

    def _should_enable_pod_security_for_preset(self, preset: CompliancePreset | None) -> bool:
        """Check if Pod Security Standards should be enabled for compliance preset"""
        if preset is None:
            return False
        return preset in [CompliancePreset.HIPAA, CompliancePreset.SOC2]

    def _build_network_policies(self, infrastructure: UniversalInfrastructure) -> list[dict]:
        """Build NetworkPolicy configurations from network tiers"""
        network_policies = []

        for tier in infrastructure.security.network_tiers:
            policy = self._convert_firewall_rules_to_network_policy(tier, infrastructure)
            if policy:
                network_policies.append(policy)

        return network_policies

    def _convert_firewall_rules_to_network_policy(
        self, tier: NetworkTier, infrastructure: UniversalInfrastructure
    ) -> dict | None:
        """Convert FirewallRule to Kubernetes NetworkPolicy format"""
        allow_rules = [rule for rule in tier.firewall_rules if rule.action == "allow"]

        if not allow_rules:
            return None

        network_policy = {
            "name": f"{tier.name}-network-policy",
            "namespace": infrastructure.name,
            "tier_labels": {"app.kubernetes.io/tier": tier.name},
            "ingress_rules": [],
        }

        for rule in allow_rules:
            ingress_rule = self._convert_rule_to_ingress_rule(rule, tier, infrastructure)
            if ingress_rule:
                network_policy["ingress_rules"].append(ingress_rule)

        return network_policy

    def _convert_rule_to_ingress_rule(
        self, rule: FirewallRule, tier: NetworkTier, infrastructure: UniversalInfrastructure
    ) -> dict | None:
        """Convert a single firewall rule to NetworkPolicy ingress rule"""
        ingress_rule = {
            "from": [],
            "ports": [],
        }

        # Handle source
        if rule.source == "0.0.0.0/0" or rule.source == "internet":
            # Allow from anywhere
            ingress_rule["from"].append({"ipBlock": {"cidr": "0.0.0.0/0"}})
        elif rule.source in [t.name for t in infrastructure.security.network_tiers]:
            # Cross-tier reference using pod selector labels
            ingress_rule["from"].append(
                {"podSelector": {"matchLabels": {"app.kubernetes.io/tier": rule.source}}}
            )
        else:
            # Assume it's a CIDR block
            ingress_rule["from"].append({"ipBlock": {"cidr": rule.source}})

        # Handle ports and protocol
        port_spec = {"protocol": self._map_protocol(rule.protocol)}

        if rule.ports:
            # For single ports, use port field
            if len(rule.ports) == 1:
                port_spec["port"] = str(rule.ports[0])
            else:
                # For multiple ports, create separate port specs
                for port in rule.ports:
                    single_port_spec = {
                        "protocol": self._map_protocol(rule.protocol),
                        "port": str(port),
                    }
                    ingress_rule["ports"].append(single_port_spec)
                return ingress_rule  # Return early since we handled multiple ports
        elif rule.port_ranges:
            # Handle port ranges - Kubernetes supports ranges
            port_spec["port"] = str(rule.port_ranges[0])  # Simplified

        ingress_rule["ports"].append(port_spec)

        return ingress_rule

    def _build_service_accounts(self, infrastructure: UniversalInfrastructure) -> list[dict]:
        """Build ServiceAccount configurations for each tier"""
        service_accounts = []

        for tier in infrastructure.security.network_tiers:
            service_accounts.append(
                {
                    "name": f"{tier.name}-sa",
                    "namespace": infrastructure.name,
                    "tier_labels": {"app.kubernetes.io/tier": tier.name},
                }
            )

        return service_accounts

    def _build_roles(self, infrastructure: UniversalInfrastructure) -> list[dict]:
        """Build Role configurations with appropriate permissions"""
        roles = []

        for tier in infrastructure.security.network_tiers:
            role = {
                "name": f"{tier.name}-role",
                "namespace": infrastructure.name,
                "rules": self._get_role_rules_for_tier(tier),
            }
            roles.append(role)

        return roles

    def _get_role_rules_for_tier(self, tier: NetworkTier) -> list[dict]:
        """Get appropriate RBAC rules based on tier"""
        base_rules = [
            {
                "apiGroups": [""],
                "resources": ["pods", "services", "endpoints"],
                "verbs": ["get", "list", "watch"],
            }
        ]

        # Add tier-specific rules
        if tier.name == "web":
            base_rules.extend(
                [
                    {
                        "apiGroups": [""],
                        "resources": ["configmaps", "secrets"],
                        "verbs": ["get", "list"],
                    }
                ]
            )
        elif tier.name == "api":
            base_rules.extend(
                [
                    {
                        "apiGroups": [""],
                        "resources": ["configmaps", "secrets"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["apps"],
                        "resources": ["deployments", "replicasets"],
                        "verbs": ["get", "list", "watch", "update", "patch"],
                    },
                ]
            )
        elif tier.name == "database":
            base_rules.extend(
                [
                    {
                        "apiGroups": [""],
                        "resources": ["persistentvolumeclaims", "persistentvolumes"],
                        "verbs": ["get", "list", "watch"],
                    }
                ]
            )

        return base_rules

    def _build_role_bindings(self, infrastructure: UniversalInfrastructure) -> list[dict]:
        """Build RoleBinding configurations"""
        role_bindings = []

        for tier in infrastructure.security.network_tiers:
            role_bindings.append(
                {
                    "name": f"{tier.name}-role-binding",
                    "namespace": infrastructure.name,
                    "role_name": f"{tier.name}-role",
                    "service_account_name": f"{tier.name}-sa",
                }
            )

        return role_bindings

    def _map_protocol(self, protocol: str) -> str:
        """Map universal protocol to Kubernetes protocol"""
        protocol_map = {"tcp": "TCP", "udp": "UDP", "icmp": "ICMP", "all": ""}
        return protocol_map.get(protocol, protocol)

    def _format_ports(self, ports: list[int]) -> str:
        """Format port list for template"""
        if not ports:
            return "all"
        return str(ports[0])  # Simplified for now

    def _get_namespace_labels(
        self, tier_name: str, infrastructure: UniversalInfrastructure
    ) -> dict[str, str]:
        """Get namespace labels for a tier"""
        return {"app.kubernetes.io/tier": tier_name}
