# Azure Deployment Guide

> **Deploy SpecQL backends to Microsoft Azure with auto-generated Terraform and Bicep**

## Overview

SpecQL generates production-ready Azure infrastructure using Terraform or Bicep templates. Define your requirements in YAML, get Azure resources with enterprise features, hybrid cloud capabilities, and Microsoft integration built-in.

**Think of it as**: Azure best practices meets Infrastructure as Code, but declarative and automatic.

---

## Quick Start

### 1. Define Deployment

```yaml
# deployment.yaml
deployment:
  name: crm-backend
  cloud: azure
  subscription_id: ${AZURE_SUBSCRIPTION_ID}
  resource_group: crm-backend-rg
  location: eastus
  environment: production

compute:
  instances: 2
  vm_size: Standard_D2s_v3  # 2 vCPU, 8GB RAM
  auto_scale:
    enabled: true
    min: 2
    max: 10
    cpu_threshold: 70

database:
  type: postgresql
  version: "15"
  sku: GP_Gen5_2  # General Purpose, Gen5, 2 vCores
  storage: 100GB
  high_availability: true
  backups:
    retention_days: 7
    geo_redundant: true

network:
  vnet_address_space: 10.0.0.0/16
  load_balancer:
    type: application_gateway
    tier: Standard_v2
    ssl_certificate: managed

monitoring:
  log_analytics: true
  application_insights: true
  alerts:
    - cpu_high: "> 80% for 5 minutes"
    - memory_high: "> 80% for 5 minutes"
    - error_rate: "> 1% for 2 minutes"
```

### 2. Generate Terraform

```bash
# Generate Terraform configuration
specql deploy deployment.yaml --cloud azure --format terraform --output terraform/azure/

# Output structure
terraform/azure/
├── main.tf                    # Main configuration
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── network.tf                 # Virtual Network
├── compute.tf                 # Virtual Machine Scale Set
├── database.tf                # Azure Database for PostgreSQL
├── load_balancer.tf           # Application Gateway
├── security.tf                # NSGs, Key Vault
├── monitoring.tf              # Log Analytics, App Insights
└── backend.tf                 # Terraform state (Azure Storage)
```

### 3. Deploy to Azure

```bash
cd terraform/azure/

# Authenticate with Azure
az login

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply

# Get outputs
terraform output
```

---

## Deployment Patterns

### Pattern 1: Standard Web Application

**Best for**: Enterprise applications, .NET workloads, hybrid cloud

```yaml
import:
  - patterns/infrastructure/azure_web_app_standard.yaml

deployment:
  name: web-app
  subscription_id: ${AZURE_SUBSCRIPTION_ID}
  location: eastus

# Override defaults
compute:
  vm_size: Standard_D4s_v3  # 4 vCPU, 16GB RAM
database:
  sku: GP_Gen5_4            # 4 vCores
```

**Generated Resources**:

**Compute**:
- Virtual Machine Scale Set (VMSS) with autoscaling
- Azure Linux or Windows VMs
- Custom Script Extension for initialization
- Managed disks (SSD)

**Database**:
- Azure Database for PostgreSQL Flexible Server
- Zone-redundant high availability
- Automated backups (7-35 days)
- Private endpoint (VNet integration)

**Networking**:
- Virtual Network (VNet) with subnets
- Network Security Groups (NSGs)
- Application Gateway (Layer 7 load balancer)
- Azure Firewall (optional)

**Security**:
- Azure Key Vault for secrets
- Managed Identity for authentication
- Azure Active Directory integration
- Azure Policy compliance

**Monitoring**:
- Log Analytics workspace
- Application Insights (APM)
- Azure Monitor alerts
- Azure Dashboards

**Estimated Monthly Cost**: $550-650

| Resource | Monthly Cost |
|----------|--------------|
| VMs (2x Standard_D2s_v3) | $140 |
| Auto-scaling (avg 4 VMs) | $280 |
| PostgreSQL (GP_Gen5_2, 100GB) | $180 |
| Application Gateway (Standard_v2) | $125 |
| VNet + NSGs | $10 |
| Outbound data transfer (1TB) | $85 |
| Log Analytics + App Insights | $20 |
| Key Vault | $5 |
| **Total** | **~$845/month** |

**Generated Terraform (excerpt)**:

```hcl
# Virtual Machine Scale Set
resource "azurerm_linux_virtual_machine_scale_set" "app" {
  name                = "crm-backend-vmss"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard_D2s_v3"
  instances           = 2
  admin_username      = "azureuser"

  admin_ssh_key {
    username   = "azureuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  os_disk {
    storage_account_type = "Premium_LRS"
    caching              = "ReadWrite"
  }

  network_interface {
    name    = "crm-backend-nic"
    primary = true

    ip_configuration {
      name      = "internal"
      primary   = true
      subnet_id = azurerm_subnet.app.id

      application_gateway_backend_address_pool_ids = [
        azurerm_application_gateway.main.backend_address_pool[0].id
      ]
    }
  }

  identity {
    type = "SystemAssigned"
  }

  custom_data = base64encode(templatefile("${path.module}/scripts/init.sh", {
    database_url = azurerm_key_vault_secret.db_url.value
  }))
}

# Autoscale Settings
resource "azurerm_monitor_autoscale_setting" "app" {
  name                = "crm-backend-autoscale"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  target_resource_id  = azurerm_linux_virtual_machine_scale_set.app.id

  profile {
    name = "defaultProfile"

    capacity {
      default = 2
      minimum = 2
      maximum = 10
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.app.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 70
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT1M"
      }
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.app.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "LessThan"
        threshold          = 30
      }

      scale_action {
        direction = "Decrease"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT5M"
      }
    }
  }
}

# Azure Database for PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "crm-backend-db"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "15"
  administrator_login    = "dbadmin"
  administrator_password = random_password.db.result

  sku_name   = "GP_Standard_D2s_v3"
  storage_mb = 102400  # 100GB

  zone                      = "1"
  high_availability {
    mode                      = "ZoneRedundant"
    standby_availability_zone = "2"
  }

  backup_retention_days        = 7
  geo_redundant_backup_enabled = true

  delegated_subnet_id = azurerm_subnet.database.id
  private_dns_zone_id = azurerm_private_dns_zone.postgresql.id

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgresql]
}
```

---

### Pattern 2: App Service with Containers

**Best for**: .NET/Java/Node.js apps, managed PaaS, rapid deployment

```yaml
import:
  - patterns/infrastructure/azure_app_service.yaml

deployment:
  name: web-api
  location: eastus

compute:
  type: app_service
  plan: P1v3  # Premium v3, 2 vCPU, 8GB RAM
  instances: 2
  auto_scale:
    enabled: true
    min: 2
    max: 10

container:
  image: myregistry.azurecr.io/crm-backend:latest
  port: 8080

database:
  type: postgresql_flexible
  sku: B_Standard_B2s  # Burstable, 2 vCores
```

**Generated Resources**:

**Compute**:
- App Service Plan (Linux containers)
- App Service with Docker support
- Azure Container Registry (ACR)
- Deployment slots (staging/production)

**Database**:
- Azure Database for PostgreSQL Flexible Server
- VNet integration (private endpoint)
- Connection pooling

**Networking**:
- Virtual Network integration
- Private endpoints
- Azure Front Door (global CDN, optional)

**Estimated Monthly Cost**: $250-350

| Resource | Monthly Cost |
|----------|--------------|
| App Service Plan (P1v3, 2 instances) | $188 |
| PostgreSQL (B_Standard_B2s) | $50 |
| Azure Container Registry | $5 |
| VNet + Private Endpoints | $15 |
| Outbound data (500GB) | $42 |
| **Total** | **~$300/month** |

**Advantages**:
- ✅ **Fully managed**: No VM management
- ✅ **Easy deployment**: Git push or container deploy
- ✅ **Built-in autoscaling**: Automatic traffic handling
- ✅ **Deployment slots**: Zero-downtime deployments

---

### Pattern 3: Azure Kubernetes Service (AKS)

**Best for**: Microservices, container orchestration, Kubernetes workloads

```yaml
import:
  - patterns/infrastructure/azure_aks_microservices.yaml

deployment:
  name: microservices-platform
  location: eastus

compute:
  cluster_type: aks
  node_pools:
    - name: system
      vm_size: Standard_D2s_v3
      node_count: 3
      mode: System
    - name: user
      vm_size: Standard_D4s_v3
      node_count: 2
      mode: User
      auto_scale:
        min: 2
        max: 10

database:
  type: postgresql_flexible
  sku: GP_Standard_D4s_v3
  replicas: 2

service_mesh:
  type: istio  # or linkerd, consul
  enabled: true
```

**Generated Resources**:

**Compute**:
- AKS cluster with system and user node pools
- Azure Container Instances (for virtual nodes)
- Azure Monitor for containers
- Azure AD pod identity

**Database**:
- PostgreSQL Flexible Server with replicas
- Private endpoint integration
- Kubernetes operators for management

**Networking**:
- Azure CNI (Container Networking Interface)
- Azure Load Balancer (Standard SKU)
- Azure Application Gateway Ingress Controller
- Network policies

**Estimated Monthly Cost**: $600-900

| Resource | Monthly Cost |
|----------|--------------|
| AKS cluster (management) | Free |
| System node pool (3x D2s_v3) | $210 |
| User node pool (2x D4s_v3, avg 4) | $560 |
| PostgreSQL (GP_D4s_v3) | $420 |
| Load Balancer (Standard) | $18 |
| **Total** | **~$1,208/month** |

---

### Pattern 4: Serverless with Azure Functions

**Best for**: Event-driven workloads, background processing, low traffic

```yaml
import:
  - patterns/infrastructure/azure_functions_serverless.yaml

deployment:
  name: serverless-api
  location: eastus

compute:
  type: azure_functions
  plan: Premium  # EP1 (Elastic Premium)
  max_instances: 20
  always_ready_instances: 1

database:
  type: postgresql_flexible
  sku: B_Standard_B1ms  # Burstable, 1 vCore
  storage: 32GB

storage:
  type: storage_account_v2
  tier: Standard
  replication: LRS
```

**Generated Resources**:

**Compute**:
- Azure Functions Premium Plan
- Function App (Python/Node.js/.NET/Java)
- Application Insights integration

**Database**:
- PostgreSQL Flexible Server (Burstable tier)
- Connection pooling (Azure Database Proxy)

**Storage**:
- Azure Storage Account (for function state)
- Azure Blob Storage
- Azure Queue Storage (triggers)

**Estimated Monthly Cost**: $80-200

| Resource | Monthly Cost (low) | Monthly Cost (high) |
|----------|-------------------|---------------------|
| Functions Premium (EP1) | $70 | $140 |
| Executions (1M requests) | $2 | $20 |
| PostgreSQL (B_Standard_B1ms) | $12 | $12 |
| Storage Account | $5 | $10 |
| Application Insights | $5 | $20 |
| **Total** | **~$94/month** | **~$202/month** |

---

## Azure Services Deep Dive

### Virtual Machines (VMs)

**D-series** (general purpose):

| VM Size | vCPU | RAM | Temp Storage | Monthly Cost |
|---------|------|-----|--------------|--------------|
| Standard_D2s_v3 | 2 | 8GB | 16GB | $70 |
| Standard_D4s_v3 | 4 | 16GB | 32GB | $140 |
| Standard_D8s_v3 | 8 | 32GB | 64GB | $281 |

**B-series** (burstable, cost-effective):

| VM Size | vCPU | RAM | Monthly Cost |
|---------|------|-----|--------------|
| Standard_B1s | 1 | 1GB | $8 |
| Standard_B2s | 2 | 4GB | $30 |
| Standard_B2ms | 2 | 8GB | $60 |

**Spot VMs** (70-90% discount):
```hcl
resource "azurerm_linux_virtual_machine_scale_set" "spot" {
  priority        = "Spot"
  eviction_policy = "Deallocate"
  max_bid_price   = -1  # Pay up to on-demand price
}
```

---

### Azure Database for PostgreSQL

**Flexible Server Tiers**:

| SKU | vCPU | RAM | Use Case | Monthly Cost (100GB) |
|-----|------|-----|----------|----------------------|
| B_Standard_B1ms | 1 | 2GB | Dev/test | $15 |
| B_Standard_B2s | 2 | 4GB | Staging | $30 |
| GP_Standard_D2s_v3 | 2 | 8GB | **Production** | $180 |
| GP_Standard_D4s_v3 | 4 | 16GB | High-performance | $360 |
| MO_Standard_E4ds_v4 | 4 | 32GB | Memory-optimized | $500 |

**High Availability (Zone-Redundant)**:

```hcl
resource "azurerm_postgresql_flexible_server" "main" {
  high_availability {
    mode                      = "ZoneRedundant"
    standby_availability_zone = "2"
  }
}
```

**Cost**: +100% (doubles database cost)

**Read Replicas**:

```hcl
resource "azurerm_postgresql_flexible_server" "replica" {
  name                   = "crm-backend-db-replica"
  source_server_id       = azurerm_postgresql_flexible_server.main.id
  location               = "westus"  # Different region
  create_mode            = "Replica"
}
```

---

### Application Gateway

**Tiers**:

| Tier | Features | Monthly Cost (2 instances) |
|------|----------|----------------------------|
| Standard_v2 | Layer 7 LB, SSL termination | $125 |
| WAF_v2 | + Web Application Firewall | $200 |

**Features**:
- Autoscaling
- SSL offloading
- URL-based routing
- Cookie-based session affinity
- WebSocket support

**Configuration**:

```hcl
resource "azurerm_application_gateway" "main" {
  name                = "crm-backend-appgw"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  sku {
    name     = "Standard_v2"
    tier     = "Standard_v2"
    capacity = 2
  }

  gateway_ip_configuration {
    name      = "gateway-ip-config"
    subnet_id = azurerm_subnet.gateway.id
  }

  frontend_port {
    name = "https-port"
    port = 443
  }

  frontend_ip_configuration {
    name                 = "frontend-ip"
    public_ip_address_id = azurerm_public_ip.gateway.id
  }

  backend_address_pool {
    name = "app-backend-pool"
  }

  backend_http_settings {
    name                  = "app-http-settings"
    cookie_based_affinity = "Disabled"
    port                  = 8080
    protocol              = "Http"
    request_timeout       = 30
  }

  http_listener {
    name                           = "https-listener"
    frontend_ip_configuration_name = "frontend-ip"
    frontend_port_name             = "https-port"
    protocol                       = "Https"
    ssl_certificate_name           = "app-ssl-cert"
  }

  request_routing_rule {
    name                       = "app-routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "https-listener"
    backend_address_pool_name  = "app-backend-pool"
    backend_http_settings_name = "app-http-settings"
    priority                   = 100
  }

  ssl_certificate {
    name     = "app-ssl-cert"
    data     = filebase64("${path.module}/certs/app-cert.pfx")
    password = var.ssl_cert_password
  }

  autoscale_configuration {
    min_capacity = 2
    max_capacity = 10
  }
}
```

---

### Azure Monitor & Log Analytics

**Log Analytics Workspace**:

```hcl
resource "azurerm_log_analytics_workspace" "main" {
  name                = "crm-backend-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}
```

**Application Insights** (APM):

```hcl
resource "azurerm_application_insights" "main" {
  name                = "crm-backend-insights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id
}
```

**Alerts**:

```hcl
resource "azurerm_monitor_metric_alert" "cpu_high" {
  name                = "cpu-high-alert"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_virtual_machine_scale_set.app.id]
  description         = "Alert when CPU exceeds 80%"

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachineScaleSets"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}
```

---

## Cost Optimization

### Azure Reserved Instances

**Savings**: 30-72% vs pay-as-you-go

```bash
# 1-year reservation
az reservations reservation-order purchase \
  --reservation-order-id <ORDER_ID> \
  --sku Standard_D2s_v3 \
  --location eastus \
  --term P1Y \
  --quantity 4

# Automatic application to matching VMs
```

**Example**:
- Pay-as-you-go: $70/month (D2s_v3)
- 1-year RI: $49/month (30% savings)
- 3-year RI: $37/month (47% savings)

### Azure Hybrid Benefit

**Savings**: Up to 85% with existing Windows/SQL licenses

```hcl
resource "azurerm_windows_virtual_machine" "app" {
  license_type = "Windows_Server"  # Use existing license
}
```

### Spot VMs

**Savings**: 70-90% vs pay-as-you-go

```hcl
resource "azurerm_linux_virtual_machine_scale_set" "spot" {
  priority        = "Spot"
  eviction_policy = "Deallocate"
  max_bid_price   = -1
}
```

### Azure Advisor Recommendations

```bash
# Get cost optimization recommendations
az advisor recommendation list \
  --category Cost \
  --output table
```

---

## Security Best Practices

### Azure Key Vault

```hcl
resource "azurerm_key_vault" "main" {
  name                = "crm-backend-kv"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  soft_delete_retention_days = 7
  purge_protection_enabled   = true

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
    virtual_network_subnet_ids = [azurerm_subnet.app.id]
  }
}

# Store database password
resource "azurerm_key_vault_secret" "db_password" {
  name         = "db-password"
  value        = random_password.db.result
  key_vault_id = azurerm_key_vault.main.id
}

# Grant access to Managed Identity
resource "azurerm_key_vault_access_policy" "vmss" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_virtual_machine_scale_set.app.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}
```

### Managed Identity

```hcl
resource "azurerm_linux_virtual_machine_scale_set" "app" {
  identity {
    type = "SystemAssigned"
  }
}

# Use Managed Identity to access resources (no passwords!)
```

### Network Security Groups (NSGs)

```hcl
resource "azurerm_network_security_group" "app" {
  name                = "app-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "allow-http-from-gateway"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8080"
    source_address_prefix      = azurerm_subnet.gateway.address_prefixes[0]
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "deny-all-inbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}
```

---

## Deployment Workflow

### CI/CD with Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
  paths:
    include:
      - deployment.yaml
      - entities/**

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: |
      pip install specql
      specql deploy deployment.yaml --cloud azure --output terraform/
    displayName: 'Generate Infrastructure'

  - task: TerraformInstaller@0
    inputs:
      terraformVersion: 'latest'

  - task: TerraformTaskV4@4
    inputs:
      provider: 'azurerm'
      command: 'init'
      workingDirectory: 'terraform'
      backendServiceArm: 'Azure-Connection'
      backendAzureRmResourceGroupName: 'terraform-state-rg'
      backendAzureRmStorageAccountName: 'tfstatestorage'
      backendAzureRmContainerName: 'tfstate'

  - task: TerraformTaskV4@4
    inputs:
      provider: 'azurerm'
      command: 'plan'
      workingDirectory: 'terraform'
      environmentServiceNameAzureRM: 'Azure-Connection'

  - task: TerraformTaskV4@4
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    inputs:
      provider: 'azurerm'
      command: 'apply'
      workingDirectory: 'terraform'
      environmentServiceNameAzureRM: 'Azure-Connection'
```

---

## Troubleshooting

### Common Issues

**Issue**: `The subnet already exists`

**Solution**: Import existing subnet:
```bash
terraform import azurerm_subnet.app \
  /subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}
```

**Issue**: Application Gateway health probe failing

**Solution**: Check backend health:
```bash
az network application-gateway show-backend-health \
  --name crm-backend-appgw \
  --resource-group crm-backend-rg
```

**Issue**: PostgreSQL connection timeout

**Solution**: Verify NSG and firewall rules:
```bash
az postgres flexible-server firewall-rule list \
  --resource-group crm-backend-rg \
  --name crm-backend-db
```

---

## Next Steps

- [AWS Deployment](aws-deployment.md) - Deploy to Amazon Web Services
- [GCP Deployment](gcp-deployment.md) - Deploy to Google Cloud Platform
- [Kubernetes Guide](kubernetes-deployment.md) - Container orchestration
- [Cost Optimization](cost-optimization.md) - Multi-cloud cost comparison

---

**Azure deployment with SpecQL means enterprise-grade infrastructure in minutes. From YAML to production-ready Azure resources with security, compliance, and hybrid cloud capabilities built-in.**

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Coverage**: Complete Azure deployment guide (Terraform, App Service, AKS, PostgreSQL, cost optimization)
