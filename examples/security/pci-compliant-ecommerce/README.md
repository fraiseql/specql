# PCI-DSS Compliant E-commerce Application

This example demonstrates how to use SpecQL's compliance presets to automatically achieve PCI-DSS compliance for payment processing applications.

## Key Features

- ✅ **Automatic PCI-DSS Compliance**: One line (`compliance_preset: pci-compliant`) applies all requirements
- ✅ **Payment Security**: WAF with payment-specific rules
- ✅ **Network Segmentation**: Required 3-tier architecture
- ✅ **Data Protection**: Encryption at rest and in transit
- ✅ **Audit Logging**: Comprehensive security monitoring

## Usage

```bash
# Validate the configuration
specql security validate security.yaml

# Check PCI-DSS compliance
specql security check-compliance security.yaml --framework pci-dss

# Generate AWS security infrastructure
specql security generate three-tier-app --provider aws --output pci-aws-security.tf
```

## What the Compliance Preset Applies

When you specify `compliance_preset: pci-compliant`, SpecQL automatically applies:

1. **Encryption**: Data encrypted at rest and in transit
2. **WAF Protection**: Web Application Firewall with PCI-required rule sets
3. **Network Security**: 3-tier network segmentation (web → app → database)
4. **Audit Logging**: Comprehensive security event logging
5. **Access Controls**: Least privilege access between tiers

## Customization

Add payment-specific security controls:

```yaml
security:
  compliance_preset: pci-compliant
  network_tiers:
    - name: payment_processor
      firewall_rules:
        - name: allow_payment_api
          protocol: tcp
          ports: [443]
          source: app
        - name: deny_direct_internet
          protocol: tcp
          ports: [443]
          source: internet
          action: deny
```

This ensures payment processing is only accessible through the application tier, not directly from the internet.