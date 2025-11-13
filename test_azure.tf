

# ============================================================================
# Provider Configuration
# ============================================================================
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# ============================================================================
# Resource Group
# ============================================================================

resource "azurerm_resource_group" "test-app" {
  name     = "test-app-rg"
  location = "East US"

  tags = {
    Name = "test-app"
  }
}

# ============================================================================
# Compute Resources (Virtual Machine Scale Set)
# ============================================================================

resource "azurerm_linux_virtual_machine_scale_set" "test-app" {
  name                = "test-app-vmss"
  resource_group_name = azurerm_resource_group.test-app.name
  location            = azurerm_resource_group.test-app.location
  sku                 = "Standard_B1s"
  instances           = 2

  admin_username = "adminuser"
  admin_ssh_key {
    username   = "adminuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }

  os_disk {
    storage_account_type = "Standard_LRS"
    caching              = "ReadWrite"
  }
  custom_data = base64encode(<<-EOF
    #!/bin/bash
    # Install Docker
    apt-get update
    apt-get install -y docker.io

    # Run container
    docker run -d \
      -p 80:80 \
      -e ENV=production \
      nginx:latest
  EOF
  )

  network_interface {
    name    = "test-app-nic"
    primary = true

    ip_configuration {
      name      = "internal"
      primary   = true
      subnet_id = azurerm_subnet.test-app.id
      load_balancer_backend_address_pool_ids = [azurerm_lb_backend_address_pool.test-app.id]
    }
  }

  tags = {
    Name = "test-app"
  }
}

# Auto Scaling
resource "azurerm_monitor_autoscale_setting" "test-app" {
  name                = "test-app-autoscale"
  resource_group_name = azurerm_resource_group.test-app.name
  location            = azurerm_resource_group.test-app.location
  target_resource_id  = azurerm_linux_virtual_machine_scale_set.test-app.id

  profile {
    name = "defaultProfile"

    capacity {
      default = 2
      minimum = 1
      maximum = 5
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.test-app.id
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
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.test-app.id
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
        cooldown  = "PT1M"
      }
    }
  }
}

# ============================================================================
# Database (Azure Database for PostgreSQL)
# ============================================================================

resource "azurerm_postgresql_flexible_server" "test-app" {
  name                   = "test-app-db"
  resource_group_name    = azurerm_resource_group.test-app.name
  location               = azurerm_resource_group.test-app.location
  version                = "15"
  administrator_login    = "adminuser"
  administrator_password = random_password.db_password.result
  storage_mb             = 51200
  sku_name               = "GP_Standard_D2s_v3"

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  tags = {
    Name = "test-app-database"
  }
}

resource "azurerm_postgresql_flexible_server_database" "test-app" {
  name      = "test_app"
  server_id = azurerm_postgresql_flexible_server.test-app.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store password in Key Vault
resource "azurerm_key_vault_secret" "test-app" {
  name         = "test-app-db-password"
  value        = random_password.db_password.result
  key_vault_id = azurerm_key_vault.test-app.id
}

resource "azurerm_key_vault" "test-app" {
  name                        = "test-app-kv"
  location                    = azurerm_resource_group.test-app.location
  resource_group_name         = azurerm_resource_group.test-app.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false

  sku_name = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "Set",
      "List",
      "Delete",
      "Purge"
    ]
  }
}

# ============================================================================
# Load Balancer
# ============================================================================

resource "azurerm_public_ip" "test-app" {
  name                = "test-app-pip"
  resource_group_name = azurerm_resource_group.test-app.name
  location            = azurerm_resource_group.test-app.location
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_lb" "test-app" {
  name                = "test-app-lb"
  resource_group_name = azurerm_resource_group.test-app.name
  location            = azurerm_resource_group.test-app.location
  sku                 = "Standard"

  frontend_ip_configuration {
    name                 = "test-app-frontend"
    public_ip_address_id = azurerm_public_ip.test-app.id
  }
}

resource "azurerm_lb_backend_address_pool" "test-app" {
  name            = "test-app-backend-pool"
  loadbalancer_id = azurerm_lb.test-app.id
}

resource "azurerm_lb_probe" "test-app" {
  name            = "test-app-probe"
  loadbalancer_id = azurerm_lb.test-app.id
  port            = 80
  protocol        = "Http"
  request_path    = "/health"
}

resource "azurerm_lb_rule" "test-app" {
  name                           = "test-app-rule"
  loadbalancer_id                = azurerm_lb.test-app.id
  probe_id                       = azurerm_lb_probe.test-app.id
  backend_address_pool_ids       = [azurerm_lb_backend_address_pool.test-app.id]

  frontend_ip_configuration_name = "test-app-frontend"
  protocol                       = "Tcp"
  frontend_port                  = 80
  backend_port                   = 80
}

# ============================================================================
# Networking (Virtual Network, Subnets, etc.)
# ============================================================================

resource "azurerm_virtual_network" "test-app" {
  name                = "test-app-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.test-app.location
  resource_group_name = azurerm_resource_group.test-app.name
}

resource "azurerm_subnet" "test-app" {
  name                 = "test-app-subnet"
  resource_group_name  = azurerm_resource_group.test-app.name
  virtual_network_name = azurerm_virtual_network.test-app.name
  address_prefixes     = ["10.0.1.0/24"]
}
resource "azurerm_nat_gateway" "test-app" {
  name                    = "test-app-nat"
  location                = azurerm_resource_group.test-app.location
  resource_group_name     = azurerm_resource_group.test-app.name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
}

resource "azurerm_nat_gateway_public_ip_association" "test-app" {
  nat_gateway_id       = azurerm_nat_gateway.test-app.id
  public_ip_address_id = azurerm_public_ip.nat.id
}

resource "azurerm_public_ip" "nat" {
  name                = "test-app-nat-pip"
  location            = azurerm_resource_group.test-app.location
  resource_group_name = azurerm_resource_group.test-app.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_subnet_nat_gateway_association" "test-app" {
  subnet_id      = azurerm_subnet.test-app.id
  nat_gateway_id = azurerm_nat_gateway.test-app.id
}

# Network Security Group
resource "azurerm_network_security_group" "test-app" {
  name                = "test-app-nsg"
  location            = azurerm_resource_group.test-app.location
  resource_group_name = azurerm_resource_group.test-app.name

  security_rule {
    name                       = "HTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "PostgreSQL"
    priority                   = 102
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5432"
    source_address_prefix      = "10.0.0.0/16"
    destination_address_prefix = "*"
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "azurerm_client_config" "current" {}

# ============================================================================
# Outputs
# ============================================================================
output "load_balancer_ip" {
  value = azurerm_public_ip.test-app.ip_address
}
output "database_server_fqdn" {
  value = azurerm_postgresql_flexible_server.test-app.fqdn
}

output "database_password_secret" {
  value = azurerm_key_vault_secret.test-app.name
}

output "resource_group_name" {
  value = azurerm_resource_group.test-app.name
}