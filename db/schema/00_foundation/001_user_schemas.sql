-- ============================================================================
-- USER SCHEMAS
-- Create all application schemas needed for SpecQL entities
-- ============================================================================
-- This file creates the schemas referenced by SpecQL-generated tables.
-- Schemas are created in alphabetical order for deterministic builds.
-- ============================================================================

-- Catalog schema - Shared reference data (products, manufacturers, etc.)
CREATE SCHEMA IF NOT EXISTS catalog;

COMMENT ON SCHEMA catalog IS
'Catalog schema for shared reference data.
Contains products, manufacturers, and other catalog entities.
Tier: Shared (no tenant_id)';

-- CRM schema - Customer relationship management
CREATE SCHEMA IF NOT EXISTS crm;

COMMENT ON SCHEMA crm IS
'CRM schema for customer relationship management.
Contains contacts, companies, and other CRM entities.
Tier: Multi-Tenant (with tenant_id)';

-- Projects schema - Project and task management
CREATE SCHEMA IF NOT EXISTS projects;

COMMENT ON SCHEMA projects IS
'Projects schema for project and task management.
Contains tasks, projects, and related entities.
Tier: Multi-Tenant (with tenant_id)';

-- Sales schema - Sales and order management
CREATE SCHEMA IF NOT EXISTS sales;

COMMENT ON SCHEMA sales IS
'Sales schema for sales and order management.
Contains orders, bookings, and sales entities.
Tier: Multi-Tenant (with tenant_id)';

-- Tenant schema - Tenant-specific entities
CREATE SCHEMA IF NOT EXISTS tenant;

COMMENT ON SCHEMA tenant IS
'Tenant schema for tenant-specific entities.
Contains user accounts, machines, and tenant-managed entities.
Tier: Multi-Tenant (with tenant_id)';
