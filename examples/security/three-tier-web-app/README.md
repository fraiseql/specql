# Three-Tier Web Application Example

Classic three-tier architecture with web, application, and database layers.

## Architecture

```
Internet
   ↓
┌──────────────────┐
│  Web Tier (LB)   │  Ports: 80, 443
│  10.0.1.0/24     │  Source: Internet
└────────┬─────────┘
         ↓ 8080, 8443
┌──────────────────┐
│   API Tier       │  Ports: 8080, 8443
│  10.0.10.0/24    │  Source: Web Tier
└────────┬─────────┘
         ↓ 5432
┌──────────────────┐
│ Database Tier    │  Port: 5432 (PostgreSQL)
│  10.0.20.0/24    │  Source: API Tier
└──────────────────┘
```

## Usage

### Validate Configuration

```bash
cd examples/security/three-tier-web-app
specql security validate security.yaml
```

### Generate Infrastructure

```bash
# AWS
specql security generate security.yaml --provider aws --output aws-security.tf

# GCP
specql security generate security.yaml --provider gcp --output gcp-security.tf

# Azure
specql security generate security.yaml --provider azure --output azure-security.tf

# Kubernetes
specql security generate security.yaml --provider kubernetes --output k8s-security.yaml
```

### Deploy

```bash
# AWS with Terraform
terraform init
terraform plan
terraform apply

# Kubernetes
kubectl apply -f k8s-security.yaml
```

## Features

- ✅ Three-tier network segmentation
- ✅ Web Application Firewall (WAF)
- ✅ OWASP Top 10 protection
- ✅ Rate limiting
- ✅ Encryption at rest and in transit
- ✅ Audit logging

## Use Cases

- E-commerce websites
- SaaS applications
- Customer portals
- Content management systems
- Internal business applications

## Customization

### Add Admin Access

```yaml
network_tiers:
  - name: admin
    firewall_rules:
      - allow: ssh
        from: vpn
        description: "SSH access from VPN"
```

### Add Redis Cache

```yaml
network_tiers:
  - name: cache
    firewall_rules:
      - allow: redis
        from: api
        description: "Redis cache access"
```

### Enable PCI Compliance

```yaml
security:
  compliance_preset: pci-compliant
  # ... rest of config
```

## Next Steps

1. Review [Security Patterns](../../../docs/infrastructure/security-patterns.md)
2. Explore [Compliance Frameworks](../../../docs/infrastructure/compliance-frameworks.md)
3. Check out other examples in `examples/security/`
