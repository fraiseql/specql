# Compliance Frameworks

SpecQL provides automatic compliance with major security frameworks through compliance presets. When you specify a compliance preset in your security configuration, SpecQL automatically applies all required security controls, eliminating manual compliance implementation.

## Overview

Compliance presets transform complex regulatory requirements into simple configuration:

```yaml
# Before: Manual compliance implementation (100+ lines)
security:
  encryption_at_rest: true
  encryption_in_transit: true
  audit_logging: true
  waf:
    enabled: true
    mode: prevention
    rule_sets: [OWASP_TOP_10, SQL_INJECTION, XSS]
  network_tiers:
    - name: web
      # ... complex firewall rules
    - name: api
      # ... complex firewall rules
    - name: database
      # ... complex firewall rules

# After: Automatic compliance (1 line)
security:
  compliance_preset: pci-compliant
```

## Supported Frameworks

### PCI-DSS (Payment Card Industry Data Security Standard)

**Preset**: `pci-compliant` | **Version**: 4.0 | **Industry**: Financial Services

#### What It Does

Automatically applies all PCI-DSS requirements for handling payment card data:

- **Data Protection**: Encryption at rest and in transit
- **Network Security**: WAF with prevention mode, network segmentation
- **Access Control**: Strong authentication, least privilege
- **Monitoring**: Comprehensive audit logging
- **Testing**: Security scanning capabilities

#### Example Usage

```yaml
security:
  compliance_preset: pci-compliant

  # Your application-specific customizations
  network_tiers:
    - name: payment
      firewall_rules:
        - allow: [443]
          from: internet
```

#### Generated Controls

```hcl
# AWS Security Groups
resource "aws_security_group" "web" {
  # PCI-DSS compliant firewall rules
}

# WAF with PCI-DSS required rule sets
resource "aws_wafv2_web_acl" "pci_waf" {
  name = "pci-compliant-waf"

  rule {
    name     = "OWASP-Top-10"
    priority = 1
    # ... OWASP rule configuration
  }

  rule {
    name     = "SQL-Injection"
    priority = 2
    # ... SQL injection protection
  }
}

# CloudTrail for audit logging
resource "aws_cloudtrail" "pci_audit" {
  name = "pci-compliance-trail"
  # ... comprehensive audit configuration
}
```

#### Compliance Validation

```bash
# Check PCI-DSS compliance
specql security check-compliance security.yaml --framework pci-dss

# Output:
✅ Compliant with pci-compliant
```

#### Requirements Met

| PCI-DSS Requirement | SpecQL Implementation |
|-------------------|----------------------|
| **1.2.1** Network segmentation | 3-tier network architecture |
| **2.2.4** Secure configuration | Hardened security groups |
| **3.5.3** Data encryption | AES-256 encryption at rest |
| **4.1** Strong cryptography | TLS 1.3 in transit |
| **6.6** Security testing | WAF rule sets |
| **10.2** Audit logging | CloudTrail/CloudWatch integration |

---

### HIPAA (Health Insurance Portability and Accountability Act)

**Preset**: `hipaa` | **Version**: Security Rule | **Industry**: Healthcare

#### What It Does

Automatically applies HIPAA Security Rule requirements for protected health information (PHI):

- **Data Protection**: Enhanced encryption for sensitive health data
- **Access Control**: Role-based access, audit trails
- **Audit & Monitoring**: Comprehensive logging of all access
- **Data Backup**: 7-year retention requirement
- **Incident Response**: Breach detection capabilities

#### Example Usage

```yaml
security:
  compliance_preset: hipaa

  # Healthcare-specific customizations
  network_tiers:
    - name: patient_portal
      firewall_rules:
        - allow: [443]
          from: internet
    - name: ehr_system
      firewall_rules:
        - allow: [443]
          from: patient_portal
```

#### HIPAA-Specific Features

```yaml
# Automatic 7-year backup retention
database:
  backup_retention_days: 2555  # 7 years

# Enhanced audit logging
security:
  audit_logging: true
  encryption_at_rest: true
  encryption_in_transit: true
```

#### Compliance Validation

```bash
specql security check-compliance security.yaml --framework hipaa

# Output:
✅ Compliant with hipaa
```

#### Requirements Met

| HIPAA Security Rule | SpecQL Implementation |
|-------------------|----------------------|
| **§164.312(a)(1)** Access control | Network segmentation, RBAC |
| **§164.312(a)(2)(iv)** Audit controls | Comprehensive audit logging |
| **§164.312(c)(1)** Integrity | Data validation, checksums |
| **§164.312(c)(2)** Encryption | AES-256 at rest, TLS in transit |
| **§164.312(e)(1)** Transmission security | TLS 1.3, VPN options |
| **§164.316(b)** Backup retention | 7-year automated retention |

---

### SOC 2 (System and Organization Controls 2)

**Preset**: `soc2` | **Version**: Type II | **Industry**: Technology Services

#### What It Does

Automatically applies SOC 2 trust principles for service organizations:

- **Security**: Access controls, encryption, monitoring
- **Availability**: Redundancy, monitoring, incident response
- **Processing Integrity**: Data validation, error handling
- **Confidentiality**: Data protection, access controls
- **Privacy**: Data usage, consent management

#### Example Usage

```yaml
security:
  compliance_preset: soc2

  # SaaS-specific customizations
  network_tiers:
    - name: api_gateway
      firewall_rules:
        - allow: [https]
          from: internet
    - name: microservices
      firewall_rules:
        - allow: "any"
          from: microservices
```

#### SOC 2 Trust Principles

```yaml
security:
  # Security principle
  encryption_at_rest: true
  encryption_in_transit: true
  audit_logging: true

  # Availability principle
  multi_az: true
  backup_enabled: true

  # Processing integrity
  data_validation: true

  # Confidentiality
  access_controls: "strict"

  # Privacy
  data_minimization: true
```

#### Compliance Validation

```bash
specql security check-compliance security.yaml --framework soc2

# Output:
✅ Compliant with soc2
```

#### Requirements Met

| SOC 2 Principle | SpecQL Implementation |
|----------------|----------------------|
| **Security** | Encryption, access controls, monitoring |
| **Availability** | Multi-AZ, backups, redundancy |
| **Processing Integrity** | Data validation, error handling |
| **Confidentiality** | Encryption, access restrictions |
| **Privacy** | Data minimization, consent management |

---

### ISO 27001 (Information Security Management Systems)

**Preset**: `iso27001` | **Version**: 2022 | **Industry**: All Industries

#### What It Does

Automatically applies ISO 27001 information security controls:

- **Information Security Policies**: Security governance
- **Organization of Information Security**: Roles and responsibilities
- **Human Resources Security**: Personnel security
- **Asset Management**: Information classification
- **Access Control**: Access management
- **Cryptography**: Encryption controls
- **Physical Security**: Facility security
- **Operations Security**: Secure operations
- **Communications Security**: Network security
- **System Acquisition**: Secure development
- **Supplier Relationships**: Third-party security
- **Information Security Incident Management**: Incident response
- **Information Security Aspects of Business Continuity**: Continuity planning
- **Compliance**: Regulatory compliance

#### Example Usage

```yaml
security:
  compliance_preset: iso27001

  # Enterprise-specific customizations
  network_tiers:
    - name: dmz
      firewall_rules:
        - allow: [https]
          from: internet
    - name: internal
      firewall_rules:
        - allow: "any"
          from: internal
```

#### ISO 27001 Controls

```yaml
security:
  # Access control (A.9)
  access_controls: "role-based"
  multi_factor_auth: true

  # Cryptography (A.10)
  encryption_at_rest: true
  encryption_in_transit: true

  # Physical security (A.11)
  facility_access_control: true

  # Operations security (A.12)
  change_management: true
  backup_recovery: true

  # Communications security (A.13)
  network_segmentation: true
  vpn_required: true

  # Compliance (A.18)
  audit_logging: true
  compliance_monitoring: true
```

#### Compliance Validation

```bash
specql security check-compliance security.yaml --framework iso27001

# Output:
✅ Compliant with iso27001
```

## How Compliance Presets Work

### Automatic Control Application

When you specify a compliance preset, SpecQL automatically applies required controls:

1. **Parse Preset**: Identify required security controls
2. **Apply Defaults**: Set mandatory security configurations
3. **Validate Requirements**: Ensure all controls are properly configured
4. **Generate Documentation**: Create compliance evidence

### Preset Inheritance

Presets can be combined for multi-framework compliance:

```yaml
security:
  compliance_preset: pci-compliant
  # This automatically includes SOC 2 security controls
  # since PCI-DSS compliance requires SOC 2 alignment
```

### Customization on Top of Compliance

You can add custom security controls while maintaining compliance:

```yaml
security:
  compliance_preset: pci-compliant

  # PCI-DSS requirements automatically applied
  # Plus your custom security controls
  network_tiers:
    - name: admin
      firewall_rules:
        - allow: [ssh]
          from: office_ip
        - allow: [rdp]
          from: office_ip
```

## Validation and Gap Analysis

### Automated Compliance Checking

SpecQL validates your configuration against compliance requirements:

```bash
# Validate configuration syntax
specql security validate security.yaml

# Check compliance gaps
specql security check-compliance security.yaml

# Check specific framework
specql security check-compliance security.yaml --framework pci-dss
```

### Gap Analysis Output

```
❌ Compliance gaps found:
   - PCI-DSS requires encryption at rest
   - PCI-DSS requires Web Application Firewall
   - PCI-DSS requires network segmentation (3-tier minimum)

✅ Compliant with pci-compliant
```

### Compliance Reporting

Generate detailed compliance reports:

```bash
# Generate compliance documentation
specql security generate pattern --provider aws --compliance-report
```

## Best Practices

### 1. Start with Compliance

Always specify compliance requirements first:

```yaml
# ✅ Good: Compliance-first approach
security:
  compliance_preset: pci-compliant
  # Customizations that enhance compliance

# ❌ Avoid: Compliance as afterthought
security:
  # Manual configuration that may miss requirements
  compliance_preset: pci-compliant  # Too late
```

### 2. Use Framework-Specific Patterns

Choose patterns that align with your compliance needs:

```bash
# For PCI-DSS
specql security init --preset three-tier --compliance pci-dss

# For HIPAA
specql security init --preset api-gateway --compliance hipaa

# For SOC 2
specql security init --preset microservices --compliance soc2
```

### 3. Regular Compliance Audits

```bash
# Daily compliance checks in CI/CD
specql security validate security.yaml
specql security check-compliance security.yaml

# Monthly comprehensive audit
specql security generate pattern --provider aws --audit-mode
```

### 4. Multi-Framework Compliance

For organizations needing multiple frameworks:

```yaml
security:
  compliance_preset: pci-compliant

  # Additional custom controls for other frameworks
  enhanced_logging: true  # For SOC 2
  data_retention: 2555    # For HIPAA
```

### 5. Compliance Documentation

Keep compliance evidence:

```bash
# Generate compliance documentation
specql security generate pattern --provider aws --output compliance-evidence/

# Includes:
# - Security control implementations
# - Compliance mappings
# - Validation reports
# - Architecture diagrams
```

## Framework Comparison

| Framework | Primary Focus | Key Requirements | Best For |
|-----------|---------------|------------------|----------|
| **PCI-DSS** | Payment security | Encryption, WAF, segmentation | E-commerce, payment processing |
| **HIPAA** | Health data | PHI protection, audit trails | Healthcare, medical devices |
| **SOC 2** | Service trust | Security, availability, integrity | SaaS, cloud services |
| **ISO 27001** | Information security | Risk management, controls | Enterprise, government |

## Implementation Details

### Control Mapping

Each compliance preset maps to specific security controls:

```python
# Example: PCI-DSS control mapping
PCI_DSS_CONTROLS = {
    "encryption_at_rest": True,
    "encryption_in_transit": True,
    "waf_enabled": True,
    "audit_logging": True,
    "network_segmentation": "3-tier",
    "access_controls": "strict"
}
```

### Validation Rules

SpecQL includes comprehensive validation rules for each framework:

```python
# Example: PCI-DSS validation
def validate_pci_dss(infrastructure):
    gaps = []
    if not infrastructure.security.encryption_at_rest:
        gaps.append("PCI-DSS requires encryption at rest")
    if not infrastructure.security.waf.enabled:
        gaps.append("PCI-DSS requires Web Application Firewall")
    return gaps
```

### Cloud-Specific Implementation

Compliance controls are implemented differently per cloud provider:

- **AWS**: Security Groups, WAFv2, CloudTrail, Config Rules
- **GCP**: Firewall Rules, Cloud Armor, VPC Service Controls
- **Azure**: NSGs, Application Gateway, Azure Policy
- **Kubernetes**: NetworkPolicies, RBAC, Pod Security Standards

## Troubleshooting

### Common Issues

#### Preset Not Applying

```
❌ Compliance preset 'invalid-preset' not recognized
```

**Solution**: Use valid preset names: `pci-compliant`, `hipaa`, `soc2`, `iso27001`

#### Validation Failures

```
❌ Validation failed: Missing required compliance controls
```

**Solution**: Ensure all mandatory fields are present in your security configuration

#### Framework Conflicts

```
⚠️  Conflicting compliance requirements detected
```

**Solution**: Use the strictest framework as your base preset and add custom controls for additional requirements

### Getting Help

- **Documentation**: `docs/infrastructure/compliance-frameworks.md`
- **Examples**: `examples/security/` directory
- **CLI Help**: `specql security --help`

## Future Enhancements

### Planned Framework Support

- **NIST Cybersecurity Framework** (CSF)
- **GDPR** (Data Protection)
- **FedRAMP** (Federal cloud security)
- **CIS Benchmarks** (Center for Internet Security)

### Advanced Features

- **Custom Compliance Presets**: Define organization-specific compliance requirements
- **Compliance Scoring**: Quantitative compliance measurement
- **Automated Remediation**: Fix compliance gaps automatically
- **Compliance Monitoring**: Continuous compliance validation in production