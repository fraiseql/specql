# Firewall Configuration Guide

**Comprehensive guide to network security and firewall rules in SpecQL**

---

## Overview

SpecQL's firewall configuration system provides a simple, cloud-agnostic way to define network security rules. Write firewall rules once in YAML, and SpecQL generates cloud-specific security configurations for AWS, GCP, Azure, and Kubernetes.

**Key Features**:
- **Service name expansion**: Use `http` instead of `80`
- **Tier-based security**: Define security by application layer
- **Cross-cloud consistency**: Same rules work everywhere
- **Best practices built-in**: Defaults follow security standards

---

## Quick Examples

### Basic HTTP/HTTPS Access

```yaml
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
```

**Generates**:
- AWS: Security group with ports 80, 443 open to `0.0.0.0/0`
- GCP: Firewall rule allowing TCP 80, 443 from `0.0.0.0/0`
- Azure: NSG rule allowing HTTP/HTTPS inbound
- Kubernetes: NetworkPolicy allowing TCP 80, 443 ingress

### Three-Tier Application

```yaml
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
        - allow: postgresql
          from: api
```

**Security Model**: Internet ’ Web ’ API ’ Database (defense in depth)

---

## Firewall Rule Anatomy

### Complete Rule Structure

```yaml
firewall_rules:
  - name: rule-name
    protocol: tcp  # tcp, udp, icmp, all
    ports: [80, 443]
    port_ranges: []  # Alternative to ports
    source: internet  # CIDR or tier name
    destination: self  # CIDR or tier name
    action: allow  # allow or deny
    priority: 1000  # Lower = higher priority
    description: "Optional description for documentation"
```

### Minimal Rule (Compact Syntax)

```yaml
firewall_rules:
  - allow: [http, https]
    from: internet
```

**Auto-expanded to**:
```yaml
firewall_rules:
  - name: auto-allow-http-https
    protocol: tcp
    ports: [80, 443]
    source: 0.0.0.0/0
    destination: self
    action: allow
    priority: 1000
```

---

## Rule Parameters

### Protocol

Specifies the network protocol:

```yaml
protocol: tcp   # Transmission Control Protocol (most common)
protocol: udp   # User Datagram Protocol (DNS, streaming)
protocol: icmp  # Internet Control Message Protocol (ping)
protocol: all   # All protocols
```

**Default**: `tcp`

**Examples**:
```yaml
# Web traffic
- protocol: tcp
  ports: [80, 443]

# DNS traffic
- protocol: udp
  ports: [53]

# Ping/health checks
- protocol: icmp

# Allow all traffic (use sparingly)
- protocol: all
```

### Ports

List of individual ports to allow/deny:

```yaml
# Single port
ports: [80]

# Multiple ports
ports: [80, 443, 8080, 8443]

# Database ports
ports: [5432, 3306, 6379]
```

**Service Name Expansion**:
```yaml
# Instead of:
ports: [80, 443, 22, 5432]

# Use service names:
allow: [http, https, ssh, postgresql]
```

### Port Ranges

Alternative to listing individual ports:

```yaml
# Allow port range 8000-9000
port_ranges: ["8000-9000"]

# Multiple ranges
port_ranges: ["8000-9000", "10000-11000"]

# Mix ranges and individual ports NOT allowed
# Use one or the other:
ports: [80, 443]  # OR
port_ranges: ["80-443"]  # Choose one approach
```

**Use Cases**:
- **Development**: `"3000-3999"` (dev servers)
- **Microservices**: `"8000-8999"` (service ports)
- **Ephemeral ports**: `"32768-65535"` (client-side)

### Source

Where traffic originates from:

```yaml
# Public internet
source: internet  # Expands to 0.0.0.0/0

# Specific CIDR block
source: 10.0.0.0/16

# Another tier (by name)
source: web

# Multiple CIDRs (some providers)
source: [10.0.0.0/16, 192.168.0.0/16]

# Load balancer
source: load_balancer

# VPN
source: vpn
```

**Special Keywords**:
- `internet` ’ `0.0.0.0/0` (all IPv4)
- `self` ’ Same tier (intra-tier communication)
- `{tier-name}` ’ References another tier

### Destination

Where traffic is going:

```yaml
# This tier (default)
destination: self

# Another tier
destination: database

# Specific CIDR
destination: 10.0.1.0/24
```

**Note**: Most rules use `destination: self` (default) or omit it.

### Action

What to do with matching traffic:

```yaml
# Allow traffic (most common)
action: allow

# Deny/block traffic
action: deny
```

**Default**: `allow`

**Deny Example**:
```yaml
# Block specific IP range
- protocol: all
  source: 192.0.2.0/24
  action: deny
  priority: 100  # High priority to block first
```

### Priority

Rule evaluation order (lower number = higher priority):

```yaml
# Evaluated first
- allow: [https]
  priority: 100

# Evaluated second
- allow: [http]
  priority: 200

# Default priority
- allow: [ssh]
  # priority: 1000 (auto-assigned)
```

**Use Cases**:
- **Deny rules**: Low priority numbers (100-500)
- **Critical allows**: Medium priority (500-900)
- **Standard rules**: High priority (1000+)

---

## Service Names

Instead of remembering port numbers, use service names:

### Web Services

```yaml
allow: [http, https]  # Ports 80, 443
```

| Service | Port | Protocol |
|---------|------|----------|
| `http` | 80 | TCP |
| `https` | 443 | TCP |

### Remote Access

```yaml
allow: [ssh]  # Port 22
```

| Service | Port | Protocol |
|---------|------|----------|
| `ssh` | 22 | TCP |
| `rdp` | 3389 | TCP |

### Databases

```yaml
allow: [postgresql, mysql, redis, mongodb]
```

| Service | Port | Protocol |
|---------|------|----------|
| `postgresql` / `postgres` | 5432 | TCP |
| `mysql` | 3306 | TCP |
| `redis` | 6379 | TCP |
| `mongodb` / `mongo` | 27017 | TCP |
| `cassandra` | 9042 | TCP |
| `elasticsearch` | 9200 | TCP |

### File Transfer

```yaml
allow: [ftp, ftps, sftp]
```

| Service | Port | Protocol |
|---------|------|----------|
| `ftp` | 21 | TCP |
| `ftps` | 990 | TCP |
| `sftp` | 22 | TCP |

### Email

```yaml
allow: [smtp, smtps, imap, imaps]
```

| Service | Port | Protocol |
|---------|------|----------|
| `smtp` | 25 | TCP |
| `smtps` | 465 | TCP |
| `imap` | 143 | TCP |
| `imaps` | 993 | TCP |
| `pop3` | 110 | TCP |
| `pop3s` | 995 | TCP |

### Infrastructure

```yaml
allow: [dns, ntp]
```

| Service | Port | Protocol |
|---------|------|----------|
| `dns` | 53 | UDP |
| `dhcp` | 67 | UDP |
| `ntp` | 123 | UDP |
| `snmp` | 161 | UDP |

---

## Network Tiers

Organize your application into logical security tiers:

### What is a Tier?

A **network tier** is a logical grouping of resources with shared security policies. Common tiers:

- **web**: Public-facing load balancers
- **api**: Application servers
- **database**: Data storage
- **admin**: Administrative access
- **workers**: Background job processors
- **cache**: Caching layer (Redis, Memcached)

### Defining Tiers

```yaml
security:
  network_tiers:
    - name: web
      description: "Public-facing load balancer"
      cidr_blocks: ["10.0.1.0/24"]
      firewall_rules:
        - allow: [http, https]
          from: internet

    - name: api
      description: "Application servers"
      cidr_blocks: ["10.0.10.0/24"]
      firewall_rules:
        - allow: 8080
          from: web

    - name: database
      description: "Database servers"
      cidr_blocks: ["10.0.20.0/24"]
      firewall_rules:
        - allow: postgresql
          from: api
```

### Cross-Tier Communication

Tiers can reference each other by name:

```yaml
network_tiers:
  - name: api
    firewall_rules:
      - allow: 8080
        from: web  # References "web" tier

  - name: database
    firewall_rules:
      - allow: postgresql
        from: api  # References "api" tier
```

**Generated** (AWS example):
```hcl
resource "aws_security_group_rule" "api_from_web" {
  type                     = "ingress"
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.web.id
  security_group_id        = aws_security_group.api.id
}
```

### Intra-Tier Communication

Allow traffic within the same tier:

```yaml
network_tiers:
  - name: api
    firewall_rules:
      - allow: 8080
        from: api  # Same tier
        # OR
        from: self
```

**Use Cases**:
- Microservices communicating within same tier
- Database clustering
- Cache synchronization

---

## Common Patterns

### 1. Public Web Server

```yaml
security:
  network_tiers:
    - name: web
      firewall_rules:
        # Allow HTTP/HTTPS from internet
        - allow: [http, https]
          from: internet

        # Allow health checks from load balancer
        - allow: http
          from: load_balancer
          description: "Health check endpoint"

        # Allow SSH from bastion (admin access)
        - allow: ssh
          from: 10.0.0.10/32
          description: "Bastion host"
```

### 2. API Server (Private)

```yaml
security:
  network_tiers:
    - name: api
      firewall_rules:
        # Only allow traffic from web tier
        - allow: 8080
          from: web
          description: "API endpoints"

        # Health checks from monitoring
        - allow: 8080
          from: monitoring
          description: "Health checks"

        # Deny all other traffic (implicit)
```

### 3. Database Server (Isolated)

```yaml
security:
  network_tiers:
    - name: database
      firewall_rules:
        # PostgreSQL only from API tier
        - allow: postgresql
          from: api
          description: "Application database access"

        # PostgreSQL from read-only analytics
        - allow: postgresql
          from: analytics
          description: "Read-only analytics access"

        # Deny everything else (implicit)
```

### 4. Microservices Mesh

```yaml
security:
  network_tiers:
    - name: services
      firewall_rules:
        # Allow inter-service communication
        - allow: "8000-9000"
          from: services
          description: "Service-to-service communication"

        # Allow ingress from gateway
        - allow: [8080, 8443]
          from: gateway
          description: "Ingress traffic"
```

### 5. Admin/Bastion Access

```yaml
security:
  network_tiers:
    - name: admin
      firewall_rules:
        # SSH from corporate VPN only
        - allow: ssh
          from: vpn
          description: "Admin SSH access"

        # RDP for Windows
        - allow: rdp
          from: vpn
          description: "Windows admin access"

        # Deny all other access
        - deny: all
          from: internet
          priority: 100
```

### 6. CDN + Web + API + DB

```yaml
security:
  network_tiers:
    # CDN/Edge
    - name: cdn
      firewall_rules:
        - allow: [http, https]
          from: internet

    # Web tier (behind CDN)
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: cdn
        - allow: [http, https]
          from: internet  # Direct access allowed

    # API tier (private)
    - name: api
      firewall_rules:
        - allow: 8080
          from: web

    # Database tier (most restricted)
    - name: database
      firewall_rules:
        - allow: postgresql
          from: api
```

---

## Cloud-Specific Behavior

### AWS Security Groups

```yaml
# SpecQL YAML
firewall_rules:
  - allow: [http, https]
    from: internet
```

**Generated AWS Terraform**:
```hcl
resource "aws_security_group" "web" {
  name   = "web-tier-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }
}
```

**AWS-Specific Features**:
- **Stateful**: Return traffic automatically allowed
- **Security Groups**: Can reference other SGs by ID
- **VPC Scoped**: Tied to VPC

### GCP Firewall Rules

```yaml
# SpecQL YAML (same as above)
firewall_rules:
  - allow: [http, https]
    from: internet
```

**Generated GCP Terraform**:
```hcl
resource "google_compute_firewall" "web_allow_http_https" {
  name    = "web-allow-http-https"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web-tier"]
  priority      = 1000
}
```

**GCP-Specific Features**:
- **Target tags**: Rules apply to instances with matching tags
- **Priority**: Explicit priority numbers (lower = higher priority)
- **Stateful**: Return traffic allowed

### Azure Network Security Groups

```yaml
# SpecQL YAML (same as above)
firewall_rules:
  - allow: [http, https]
    from: internet
```

**Generated Azure Terraform**:
```hcl
resource "azurerm_network_security_group" "web" {
  name                = "web-tier-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_network_security_rule" "web_allow_http" {
  name                        = "allow-http"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "80"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.main.name
  network_security_group_name = azurerm_network_security_group.web.name
}

resource "azurerm_network_security_rule" "web_allow_https" {
  name                        = "allow-https"
  priority                    = 101
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "443"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.main.name
  network_security_group_name = azurerm_network_security_group.web.name
}
```

**Azure-Specific Features**:
- **NSG Rules**: Individual rules per port
- **Priority**: 100-4096 (lower = higher priority)
- **Direction**: Explicit inbound/outbound

### Kubernetes NetworkPolicies

```yaml
# SpecQL YAML (same as above)
firewall_rules:
  - allow: [http, https]
    from: internet
```

**Generated Kubernetes YAML**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-tier-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: web
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector: {}  # Allow from all pods
      ports:
        - protocol: TCP
          port: 80
        - protocol: TCP
          port: 443
  egress:
    - to:
        - podSelector:
            matchLabels:
              tier: api
      ports:
        - protocol: TCP
          port: 8080
```

**Kubernetes-Specific Features**:
- **Pod selectors**: Label-based targeting
- **Namespace scoped**: Policies per namespace
- **Default deny**: Pods without policies are isolated

---

## Advanced Scenarios

### 1. Geo-Restriction (with WAF)

```yaml
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet

  waf:
    enabled: true
    geo_blocking:
      - CN  # China
      - RU  # Russia
      - KP  # North Korea
```

### 2. Rate Limiting (with WAF)

```yaml
security:
  waf:
    enabled: true
    rate_limiting: true  # 10,000 req/5min default
```

### 3. IP Whitelist/Blacklist

```yaml
security:
  waf:
    enabled: true
    ip_whitelist:
      - 203.0.113.0/24  # Your office
    ip_blacklist:
      - 192.0.2.0/24  # Known bad actors
```

### 4. VPN-Only Access

```yaml
security:
  network_tiers:
    - name: admin
      firewall_rules:
        - allow: ssh
          from: vpn  # VPN users only
        - deny: ssh
          from: internet
          priority: 100

  vpn:
    enabled: true
    type: client-vpn
    remote_cidr: 10.100.0.0/16
```

### 5. Blue-Green Deployment

```yaml
security:
  network_tiers:
    # Blue environment
    - name: blue
      firewall_rules:
        - allow: 8080
          from: load_balancer

    # Green environment
    - name: green
      firewall_rules:
        - allow: 8080
          from: load_balancer

    # Load balancer routes to active environment
    - name: load_balancer
      firewall_rules:
        - allow: [http, https]
          from: internet
```

---

## Best Practices

### 1. Principle of Least Privilege

Only allow necessary traffic:

```yaml
#  Good: Specific source
firewall_rules:
  - allow: postgresql
    from: api  # Only API tier

# L Avoid: Too permissive
firewall_rules:
  - allow: postgresql
    from: internet  # Database exposed!
```

### 2. Use Service Names

```yaml
#  Good: Readable
allow: [http, https, postgresql]

# L Avoid: Hard to understand
allow: [80, 443, 5432]
```

### 3. Add Descriptions

```yaml
firewall_rules:
  - allow: 8080
    from: web
    description: "REST API endpoints for web tier"
```

### 4. Deny by Default

Firewall rules are deny-by-default. Only explicitly allowed traffic passes:

```yaml
# Implicit deny all
network_tiers:
  - name: database
    firewall_rules:
      - allow: postgresql
        from: api
      # Everything else is denied (no need to specify)
```

### 5. Organize by Tier

Group rules logically by network tier:

```yaml
network_tiers:
  - name: web
    firewall_rules:
      # All web-related rules here

  - name: api
    firewall_rules:
      # All API-related rules here
```

### 6. Use Priorities for Deny Rules

Put deny rules first (low priority number):

```yaml
firewall_rules:
  # Deny specific IP first
  - deny: all
    from: 192.0.2.0/24
    priority: 100

  # Then allow everything else
  - allow: [http, https]
    from: internet
    priority: 1000
```

---

## Troubleshooting

### Rule Not Working

1. **Check priority**: Lower priority rules might override yours
2. **Check source**: Verify tier name or CIDR is correct
3. **Check service name**: Ensure service name is supported
4. **Validate YAML**: Run `specql security validate security.yaml`

### Connection Timeout

```yaml
# Make sure both ingress AND egress are allowed:
- name: web
  firewall_rules:
    - allow: 8080
      from: api  # Ingress: API ’ Web

- name: api
  firewall_rules:
    # Don't forget egress! (usually auto-allowed)
```

### Tier Reference Not Found

```yaml
# L Wrong: Typo in tier name
- allow: 8080
  from: apis  # Should be "api"

#  Correct
- allow: 8080
  from: api
```

---

## Examples

See `examples/security/` for complete examples:

- `three-tier-web-app/` - Basic 3-tier
- `api-gateway/` - API gateway pattern
- `microservices/` - Service mesh
- `zero-trust/` - Zero-trust architecture

---

**Last Updated**: 2025-11-19
**Status**: Production Ready
