"""
Test Kubernetes Security Generator

Tests for generating Kubernetes security resources (NetworkPolicies, RBAC, Pod Security Standards) from universal schema:
- NetworkPolicy generation for pod-to-pod communication
- RBAC ServiceAccount, Role, and RoleBinding generation
- Pod Security Standards configuration
- Cross-tier NetworkPolicy references
"""

from src.infrastructure.generators.kubernetes_security_generator import KubernetesSecurityGenerator
from src.infrastructure.universal_infra_schema import (
    CompliancePreset,
    FirewallRule,
    NetworkTier,
    SecurityConfig,
    UniversalInfrastructure,
    WAFConfig,
)


def test_generate_kubernetes_network_policies():
    """Should generate Kubernetes NetworkPolicies from universal schema"""
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

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    assert "apiVersion: networking.k8s.io/v1" in yaml_output
    assert "kind: NetworkPolicy" in yaml_output
    assert "name: web-network-policy" in yaml_output
    assert "app.kubernetes.io/tier: web" in yaml_output
    assert "protocol: TCP" in yaml_output
    assert "port: 80" in yaml_output
    assert "port: 443" in yaml_output


def test_generate_kubernetes_network_policies_with_multiple_tiers():
    """Should generate NetworkPolicies for multiple tiers"""
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
            ]
        ),
    )

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    assert "name: web-network-policy" in yaml_output
    assert "name: api-network-policy" in yaml_output
    # Cross-tier reference using podSelector
    assert "app.kubernetes.io/tier: web" in yaml_output
    assert "podSelector:" in yaml_output
    assert "matchLabels:" in yaml_output


def test_generate_kubernetes_rbac():
    """Should generate RBAC resources when WAF is enabled"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            waf=WAFConfig(enabled=True),
            network_tiers=[
                NetworkTier(name="web", firewall_rules=[]),
                NetworkTier(name="api", firewall_rules=[]),
            ],
        ),
    )

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    assert "kind: ServiceAccount" in yaml_output
    assert "name: web-sa" in yaml_output
    assert "name: api-sa" in yaml_output
    assert "kind: Role" in yaml_output
    assert "name: web-role" in yaml_output
    assert "kind: RoleBinding" in yaml_output
    assert "name: web-role-binding" in yaml_output


def test_generate_kubernetes_pod_security_standards():
    """Should generate Pod Security Standards when compliance preset requires it"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            compliance_preset=CompliancePreset.HIPAA,
            network_tiers=[
                NetworkTier(name="web", firewall_rules=[]),
            ],
        ),
    )

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    assert "pod-security.kubernetes.io/enforce: restricted" in yaml_output
    assert "pod-security.kubernetes.io/enforce-version: v1.24" in yaml_output
    assert "kind: ConfigMap" in yaml_output
    assert "name: pod-security-standards" in yaml_output


def test_generate_cross_tier_network_policies():
    """Should generate NetworkPolicies with podSelector references for cross-tier access"""
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

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    # Web tier allows from internet (ipBlock)
    assert "ipBlock:" in yaml_output
    assert "cidr: 0.0.0.0/0" in yaml_output

    # API tier allows from web (podSelector)
    assert "podSelector:" in yaml_output
    assert "app.kubernetes.io/tier: web" in yaml_output

    # Database tier allows from api (podSelector)
    assert "app.kubernetes.io/tier: api" in yaml_output


def test_generate_port_ranges():
    """Should generate NetworkPolicies with port ranges"""
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

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    assert "port: 8000-9000" in yaml_output


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

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    # PCI-DSS should enable RBAC
    assert "kind: ServiceAccount" in yaml_output
    assert "kind: Role" in yaml_output
    assert "kind: RoleBinding" in yaml_output


def test_generate_udp_and_icmp_rules():
    """Should generate NetworkPolicies for UDP and ICMP protocols"""
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

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    assert "protocol: UDP" in yaml_output
    assert "port: 123" in yaml_output
    assert "protocol: ICMP" in yaml_output


def test_generate_multiple_ports():
    """Should generate NetworkPolicies with multiple ports"""
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

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    # Kubernetes NetworkPolicy should have multiple port entries
    assert "port: 80" in yaml_output
    assert "port: 443" in yaml_output
    assert "port: 8080" in yaml_output


def test_generate_rbac_roles_with_tier_specific_permissions():
    """Should generate RBAC roles with appropriate permissions based on tier"""
    infrastructure = UniversalInfrastructure(
        name="test-app",
        security=SecurityConfig(
            waf=WAFConfig(enabled=True),
            network_tiers=[
                NetworkTier(name="web", firewall_rules=[]),
                NetworkTier(name="api", firewall_rules=[]),
                NetworkTier(name="database", firewall_rules=[]),
            ],
        ),
    )

    generator = KubernetesSecurityGenerator()
    yaml_output = generator.generate(infrastructure)

    # Web tier should have basic permissions
    assert 'resources: ["pods", "services", "endpoints"]' in yaml_output
    assert 'verbs: ["get", "list", "watch"]' in yaml_output

    # API tier should have additional permissions
    assert 'resources: ["configmaps", "secrets"]' in yaml_output
    assert 'resources: ["deployments", "replicasets"]' in yaml_output

    # Database tier should have PVC permissions
    assert 'resources: ["persistentvolumeclaims", "persistentvolumes"]' in yaml_output
