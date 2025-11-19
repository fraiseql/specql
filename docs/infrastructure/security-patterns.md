# Security Patterns

SpecQL security patterns provide pre-built, enterprise-ready security configurations that can be instantly deployed across AWS, GCP, Azure, and Kubernetes. These patterns follow industry best practices and support automatic compliance with frameworks like PCI-DSS, HIPAA, SOC2, and ISO27001.

## Overview

Security patterns in SpecQL follow a **universal expression model** - you write security configuration once, and SpecQL generates cloud-specific infrastructure code. This eliminates the complexity of managing security across multiple cloud providers.

```yaml
# Your security specification (12 lines)
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
    - name: api
      firewall_rules:
        - allow: 8080
          from: web
  waf: enabled
  compliance_preset: pci-compliant

# Generates production-ready infrastructure (200+ lines per cloud)
# ✅ AWS: Security Groups + WAFv2 + Network ACLs
# ✅ GCP: Firewall Rules + Cloud Armor + VPC
# ✅ Azure: NSGs + Application Gateway + VNets
# ✅ Kubernetes: NetworkPolicies + RBAC + Pod Security
```

## Quick Start

### 1. List Available Patterns

```bash
specql security list
```

### 2. Inspect a Pattern

```bash
specql security inspect three-tier-app
```

### 3. Generate Infrastructure Code

```bash
# Generate AWS Terraform
specql security generate three-tier-app --provider aws --output security.tf

# Generate GCP Terraform
specql security generate three-tier-app --provider gcp --output security.tf

# Preview what will be generated
specql security generate three-tier-app --provider aws --dry-run
```

### 4. Initialize from Preset

```bash
# Create security config from preset
specql security init --preset three-tier --compliance pci-dss --output security.yaml

# Validate your configuration
specql security validate security.yaml

# Check compliance
specql security check-compliance security.yaml
```

## Available Patterns

### Three-Tier Web Application

**Pattern**: `three-tier-app`

A classic three-tier architecture with web, application, and database layers. Includes WAF protection and secure cross-tier communication.

```yaml
# Generated configuration includes:
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
    - name: api
      firewall_rules:
        - allow: 8080
          from: web
    - name: database
      firewall_rules:
        - allow: 5432
          from: api
  waf:
    enabled: true
    mode: prevention
```

**Use Cases**:
- E-commerce applications
- Content management systems
- Customer portals

### API Gateway Pattern

**Pattern**: `api-gateway`

Modern API-first architecture with gateway, microservices, and shared database layer.

```yaml
security:
  network_tiers:
    - name: gateway
      firewall_rules:
        - allow: [http, https]
          from: internet
    - name: services
      firewall_rules:
        - allow: [8080, 8081, 8082]
          from: gateway
    - name: database
      firewall_rules:
        - allow: 5432
          from: services
  waf:
    enabled: true
    rate_limiting: true
```

**Use Cases**:
- Microservices architectures
- API marketplaces
- Mobile app backends

### Microservices Pattern

**Pattern**: `microservices`

Service mesh architecture with inter-service communication and external access control.

```yaml
security:
  network_tiers:
    - name: ingress
      firewall_rules:
        - allow: [http, https]
          from: internet
    - name: services
      firewall_rules:
        - allow: "any"
          from: services  # Inter-service communication
        - allow: [8080, 8443]
          from: ingress
    - name: database
      firewall_rules:
        - allow: 5432
          from: services
```

**Use Cases**:
- Containerized applications
- Service mesh deployments
- Cloud-native architectures

## Compliance Frameworks

SpecQL supports automatic compliance with major security frameworks. When you specify a compliance preset, SpecQL automatically applies required security controls.

### PCI-DSS (Payment Card Industry)

**Preset**: `pci-compliant`

Required for handling payment card data. Includes encryption, WAF, network segmentation, and audit logging.

```yaml
security:
  compliance_preset: pci-compliant
  # Automatically applies:
  # - Encryption at rest and in transit
  # - WAF with prevention mode
  # - Network segmentation (3-tier minimum)
  # - Audit logging
  # - Strong access controls
```

**Requirements Met**:
- ✅ Data encryption
- ✅ Secure network architecture
- ✅ Access control
- ✅ Monitoring and logging
- ✅ Regular testing

### HIPAA (Healthcare)

**Preset**: `hipaa`

Required for handling protected health information (PHI). Includes enhanced encryption and 7-year backup retention.

```yaml
security:
  compliance_preset: hipaa
  # Automatically applies:
  # - Encryption at rest and in transit
  # - Audit logging and access controls
  # - PHI data isolation
  # - 7-year backup retention
  # - Access logging
```

**Requirements Met**:
- ✅ Data encryption
- ✅ Access controls
- ✅ Audit trails
- ✅ Data backup (7 years)
- ✅ Breach notification procedures

### SOC 2 (Trust Services)

**Preset**: `soc2`

Focuses on security, availability, processing integrity, confidentiality, and privacy.

```yaml
security:
  compliance_preset: soc2
  # Automatically applies:
  # - Security controls
  # - Availability assurance
  # - Processing integrity
  # - Confidentiality protection
  # - Privacy protection
  # - Audit logging
```

**Requirements Met**:
- ✅ Security controls
- ✅ Availability monitoring
- ✅ Data processing integrity
- ✅ Confidentiality
- ✅ Privacy protection

### ISO 27001 (Information Security)

**Preset**: `iso27001`

Comprehensive information security management system.

```yaml
security:
  compliance_preset: iso27001
  # Automatically applies:
  # - Information security policy
  # - Risk assessment framework
  # - Access controls
  # - Cryptography
  # - Physical security
  # - Operations security
```

**Requirements Met**:
- ✅ Risk management
- ✅ Access control
- ✅ Cryptography
- ✅ Operations security
- ✅ Compliance monitoring

## Custom Security Configuration

While patterns provide a great starting point, you can customize security for your specific needs.

### Network Tiers

Define your application architecture using network tiers:

```yaml
security:
  network_tiers:
    - name: web
      firewall_rules:
        - name: allow_https
          protocol: tcp
          ports: [443]
          source: internet
        - name: allow_health_checks
          protocol: tcp
          ports: [80]
          source: load_balancer

    - name: api
      firewall_rules:
        - name: allow_from_web
          protocol: tcp
          ports: [8080, 8443]
          source: web

    - name: database
      firewall_rules:
        - name: allow_postgres
          protocol: tcp
          ports: [5432]
          source: api
```

### Service Names

Use friendly service names instead of port numbers:

```yaml
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
    - name: api
      firewall_rules:
        - allow: [http, https]
          from: web
```

Supported services: `http`, `https`, `ssh`, `postgresql`, `mysql`, `redis`, `mongodb`, `ftp`, `smtp`, `dns`, etc.

### WAF Configuration

Enable and configure Web Application Firewall:

```yaml
security:
  waf:
    enabled: true
    mode: prevention  # or 'detection'
    rule_sets:
      - OWASP_TOP_10
      - SQL_INJECTION
      - XSS
    rate_limiting: true
    geo_blocking: ["CN", "RU"]  # Block by country
```

### VPN Configuration

Set up secure connectivity:

```yaml
security:
  vpn:
    enabled: true
    type: site-to-site  # or 'client-vpn', 'private-link'
    remote_cidr: "192.168.0.0/16"
```

## CLI Reference

### List Patterns

```bash
specql security list [--tags TAG] [--json]
```

**Options**:
- `--tags`: Filter patterns by tags (e.g., `--tags web,api`)
- `--json`: Output in JSON format

### Inspect Pattern

```bash
specql security inspect PATTERN_NAME [--json]
```

**Options**:
- `--json`: Output detailed pattern information in JSON

### Generate Infrastructure

```bash
specql security generate PATTERN_NAME --provider {aws,gcp,azure,kubernetes} [--output FILE] [--dry-run]
```

**Options**:
- `--provider`: Target cloud provider
- `--output`: Output file path
- `--dry-run`: Show generated code without writing to file

### Validate Configuration

```bash
specql security validate YAML_FILE
```

Validates security YAML syntax and structure.

### Check Compliance

```bash
specql security check-compliance YAML_FILE [--framework FRAMEWORK]
```

**Options**:
- `--framework`: Check against specific framework (`pci-dss`, `hipaa`, `soc2`, `iso27001`)

### Initialize Configuration

```bash
specql security init --preset {three-tier,microservices,api-gateway} [--compliance FRAMEWORK] [--output FILE]
```

**Options**:
- `--preset`: Starting pattern preset
- `--compliance`: Apply compliance framework
- `--output`: Output file (default: `security.yaml`)

### Compare Configurations

```bash
specql security diff FILE1 FILE2
```

Shows differences between two security configuration files.

## Best Practices

### 1. Start with Patterns

Use built-in patterns as a foundation, then customize for your needs:

```bash
# Start with a pattern
specql security init --preset three-tier --compliance pci-dss --output security.yaml

# Customize as needed
# Edit security.yaml...

# Validate and generate
specql security validate security.yaml
specql security generate three-tier-app --provider aws --output security.tf
```

### 2. Use Compliance Presets

Always specify compliance requirements upfront:

```yaml
security:
  compliance_preset: pci-compliant  # Applies all PCI-DSS requirements
  # Your customizations here...
```

### 3. Validate Regularly

Validate your security configuration before deployment:

```bash
# Syntax validation
specql security validate security.yaml

# Compliance checking
specql security check-compliance security.yaml

# Dry-run generation
specql security generate pattern --provider aws --dry-run
```

### 4. Multi-Cloud Consistency

Generate the same security posture across clouds:

```bash
# Same YAML generates consistent security across all clouds
specql security generate pattern --provider aws --output aws-security.tf
specql security generate pattern --provider gcp --output gcp-security.tf
specql security generate pattern --provider azure --output azure-security.tf
```

### 5. Version Control

Keep security configurations in version control alongside your infrastructure code.

## Troubleshooting

### Pattern Not Found

```
❌ Pattern 'my-pattern' not found
```

**Solution**: List available patterns and check spelling:

```bash
specql security list
```

### Validation Errors

```
❌ Validation failed: Invalid firewall rule
```

**Solution**: Check your YAML syntax and ensure all required fields are present. Use `specql security validate` to get detailed error messages.

### Compliance Gaps

```
❌ Compliance gaps found:
   - PCI-DSS requires encryption at rest
```

**Solution**: Either fix the configuration or use a compliance preset that automatically applies required controls.

### Generation Fails

```
❌ Generation failed: Unsupported provider
```

**Solution**: Ensure you're using a supported provider (`aws`, `gcp`, `azure`, `kubernetes`).

## Examples

See the `examples/security/` directory for complete working examples:

- `three-tier-web-app/` - Basic three-tier application
- `pci-compliant-ecommerce/` - PCI-DSS compliant e-commerce
- `zero-trust-microservices/` - Zero trust microservices architecture
- `api-gateway-with-waf/` - API gateway with WAF protection

Each example includes:
- Security configuration YAML
- Generated infrastructure code for all supported clouds
- README with deployment instructions

## Architecture

SpecQL's security system follows a universal expression model:

1. **Security Parser**: Converts user-friendly YAML into universal security schema
2. **Compliance Manager**: Applies compliance framework requirements
3. **Pattern Library**: Provides pre-built security patterns
4. **Cloud Generators**: Generate provider-specific infrastructure code
5. **CLI Interface**: Command-line tools for management and validation

This architecture ensures consistency across clouds while maintaining the simplicity of a single security specification.