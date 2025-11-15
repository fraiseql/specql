# Multi-Tenant SaaS System Example

**What You'll Build**: A multi-tenant SaaS platform with tenant isolation, row-level security, and shared data patterns.

**Time**: 30 minutes
**Complexity**: Advanced

## System Overview

Our SaaS platform will have:
- **Tenants**: Organizations/customers using the platform
- **Users**: Users belonging to specific tenants
- **Projects**: Projects within each tenant
- **Shared Resources**: Global data shared across tenants
- **Tenant-specific Data**: Data isolated per tenant

## Architecture

```
Tenant (1) ──< (N) User
   │              │
   │              │
   └──< (N) Project ──< (N) Task
   │              │
   │              │
   └──< (N) Invoice
          │
          └──< (N) InvoiceItem

GlobalSettings (1) ──< Shared across all tenants
```

## Step 1: Create Tenant Entity

Create `entities/saas/tenant.yaml`:

```yaml
entity: Tenant
schema: saas
description: An organization/customer in the SaaS platform

fields:
  # Identity
  name: text
  subdomain: text
  domain: text

  # Contact
  contact_email: email
  contact_phone: text

  # Billing
  plan: enum(free, starter, professional, enterprise)
  status: enum(active, suspended, cancelled)

  # Limits
  max_users: integer
  max_projects: integer
  storage_limit_gb: integer

  # Metadata
  created_by: text

indexes:
  - fields: [subdomain]
    unique: true
  - fields: [domain]
    unique: true
  - fields: [status]
  - fields: [plan]

actions:
  - name: upgrade_plan
    description: Upgrade tenant to a higher plan
    requires: caller.can_manage_tenants
    steps:
      - validate: plan IN ('free', 'starter', 'professional')
        error: "already_enterprise"
      - update: Tenant SET plan = CASE
          WHEN plan = 'free' THEN 'starter'
          WHEN plan = 'starter' THEN 'professional'
          WHEN plan = 'professional' THEN 'enterprise'
        END
      - update: Tenant SET
          max_users = CASE
            WHEN plan = 'starter' THEN 50
            WHEN plan = 'professional' THEN 200
            WHEN plan = 'enterprise' THEN 1000
          END,
          max_projects = CASE
            WHEN plan = 'starter' THEN 10
            WHEN plan = 'professional' THEN 50
            WHEN plan = 'enterprise' THEN 500
          END,
          storage_limit_gb = CASE
            WHEN plan = 'starter' THEN 10
            WHEN plan = 'professional' THEN 100
            WHEN plan = 'enterprise' THEN 1000
          END
      - notify: tenant_admin
      - log: "Tenant plan upgraded"

  - name: suspend_tenant
    description: Suspend a tenant account
    requires: caller.can_suspend_tenants
    steps:
      - validate: status = 'active'
        error: "tenant_not_active"
      - update: Tenant SET status = 'suspended'
      - update: User SET status = 'suspended' WHERE tenant_id = id
      - notify: tenant_admin
      - log: "Tenant suspended"
```

## Step 2: Create User Entity

Create `entities/saas/user.yaml`:

```yaml
entity: User
schema: saas
description: A user belonging to a specific tenant

fields:
  # Relationships
  tenant: ref(Tenant)

  # Identity
  username: text
  email: email
  password_hash: text

  # Profile
  display_name: text
  first_name: text
  last_name: text

  # Status
  status: enum(active, inactive, suspended)
  role: enum(admin, manager, user)

indexes:
  - fields: [tenant_id, username]
    unique: true
  - fields: [tenant_id, email]
    unique: true
  - fields: [tenant_id, status]
  - fields: [tenant_id, role]

actions:
  - name: change_role
    description: Change user role within tenant
    requires: caller.can_manage_users AND caller.tenant_id = tenant_id
    steps:
      - validate: role IN ('manager', 'user')
        error: "cannot_demote_admin"
      - update: User SET role = ?
      - log: "User role changed"

  - name: deactivate_user
    description: Deactivate a user account
    requires: (caller.can_manage_users AND caller.tenant_id = tenant_id) OR caller.is_super_admin
    steps:
      - update: User SET status = 'inactive'
      - log: "User deactivated"
```

## Step 3: Create Project Entity

Create `entities/saas/project.yaml`:

```yaml
entity: Project
schema: saas
description: A project within a tenant

fields:
  # Relationships
  tenant: ref(Tenant)
  owner: ref(User)

  # Project info
  name: text
  description: text
  status: enum(active, archived, completed)

  # Settings
  is_public: boolean
  allow_guest_access: boolean

indexes:
  - fields: [tenant_id, name]
    unique: true
  - fields: [tenant_id, status]
  - fields: [tenant_id, owner_id]

actions:
  - name: archive_project
    description: Archive a completed project
    requires: caller.tenant_id = tenant_id AND (caller.id = owner_id OR caller.role IN ('admin', 'manager'))
    steps:
      - validate: status IN ('active', 'completed')
        error: "project_already_archived"
      - update: Project SET status = 'archived'
      - log: "Project archived"

  - name: transfer_ownership
    description: Transfer project ownership to another user
    requires: caller.tenant_id = tenant_id AND caller.id = owner_id
    steps:
      - validate: ? IN (SELECT id FROM User WHERE tenant_id = tenant_id)
        error: "user_not_in_tenant"
      - update: Project SET owner_id = ?
      - log: "Project ownership transferred"
```

## Step 4: Create Task Entity

Create `entities/saas/task.yaml`:

```yaml
entity: Task
schema: saas
description: A task within a project

fields:
  # Relationships
  project: ref(Project)
  tenant: ref(Tenant)  # Denormalized for RLS
  assigned_to: ref(User)

  # Task info
  title: text
  description: text
  status: enum(todo, in_progress, done, cancelled)
  priority: enum(low, medium, high, urgent)

  # Dates
  due_date: date
  completed_at: timestamp

indexes:
  - fields: [project_id, status]
  - fields: [tenant_id, assigned_to_id]
  - fields: [tenant_id, due_date]
  - fields: [tenant_id, priority]

actions:
  - name: assign_task
    description: Assign task to a user
    requires: caller.tenant_id = tenant_id
    steps:
      - validate: assigned_to_id IS NULL OR assigned_to_id IN (SELECT id FROM User WHERE tenant_id = tenant_id)
        error: "user_not_in_tenant"
      - update: Task SET assigned_to_id = ?
      - log: "Task assigned"

  - name: complete_task
    description: Mark task as completed
    requires: caller.tenant_id = tenant_id
    steps:
      - validate: status IN ('todo', 'in_progress')
        error: "task_already_completed"
      - update: Task SET status = 'done', completed_at = NOW()
      - log: "Task completed"
```

## Step 5: Create Invoice Entity

Create `entities/saas/invoice.yaml`:

```yaml
entity: Invoice
schema: saas
description: An invoice for a tenant

fields:
  # Relationships
  tenant: ref(Tenant)

  # Invoice info
  invoice_number: text
  amount: decimal
  currency: text
  status: enum(draft, sent, paid, overdue, cancelled)

  # Dates
  issued_at: date
  due_date: date
  paid_at: timestamp

indexes:
  - fields: [tenant_id, invoice_number]
    unique: true
  - fields: [tenant_id, status]
  - fields: [tenant_id, due_date]

actions:
  - name: mark_paid
    description: Mark invoice as paid
    requires: system
    steps:
      - validate: status IN ('draft', 'sent', 'overdue')
        error: "invoice_already_paid"
      - update: Invoice SET status = 'paid', paid_at = NOW()
      - log: "Invoice marked as paid"
```

## Step 6: Create InvoiceItem Entity

Create `entities/saas/invoice_item.yaml`:

```yaml
entity: InvoiceItem
schema: saas
description: Line items on an invoice

fields:
  # Relationships
  invoice: ref(Invoice)
  tenant: ref(Tenant)  # Denormalized for RLS

  # Item info
  description: text
  quantity: integer
  unit_price: decimal
  amount: decimal

indexes:
  - fields: [invoice_id]
  - fields: [tenant_id, invoice_id]
```

## Step 7: Create GlobalSettings Entity

Create `entities/saas/global_settings.yaml`:

```yaml
entity: GlobalSettings
schema: saas
description: Global settings shared across all tenants

fields:
  # System settings
  maintenance_mode: boolean
  max_file_size_mb: integer
  allowed_file_types: text

  # Feature flags
  advanced_reporting_enabled: boolean
  api_access_enabled: boolean

  # Limits
  default_max_users: integer
  default_max_projects: integer

indexes:
  - fields: [id]  # Only one global settings record
```

## Step 8: Generate the Complete System

```bash
# Create output directory
mkdir -p output/saas

# Generate all entities
specql generate entities/saas/*.yaml --output output/saas

# You should see generation for all 8 entities
```

## Step 9: Inspect Generated Code

### PostgreSQL Schema with RLS
```bash
# Check the generated tables
cat output/saas/postgresql/saas/01_tables.sql

# You'll see:
# - saas.tb_tenant (tenants)
# - saas.tb_user (users per tenant)
# - saas.tb_project (projects per tenant)
# - saas.tb_task (tasks per project/tenant)
# - saas.tb_invoice (invoices per tenant)
# - saas.tb_invoice_item (invoice items per tenant)
# - saas.tb_global_settings (shared settings)
# - Row Level Security policies on tenant-specific tables
```

### Business Logic Functions
```bash
# Check the generated functions
cat output/saas/postgresql/saas/02_functions.sql

# You'll see tenant-aware functions like:
# - saas.fn_tenant_upgrade_plan()
# - saas.fn_user_change_role()
# - saas.fn_project_archive_project()
```

### Java/Spring Boot with Multi-Tenant Support
```bash
# Check Java entities
ls output/saas/java/com/example/saas/

# You'll see all entity classes with tenant-aware repositories
```

## Step 10: Test the Multi-Tenant System

If you have PostgreSQL running:

```bash
# Create test database
createdb saas_test

# Apply schema
psql saas_test < output/saas/postgresql/saas/01_tables.sql
psql saas_test < output/saas/postgresql/saas/02_functions.sql

# Insert test data
psql saas_test << 'EOF'
-- Create global settings
INSERT INTO saas.tb_global_settings (maintenance_mode, max_file_size_mb, default_max_users, default_max_projects)
VALUES (false, 10, 10, 5);

-- Create tenants
INSERT INTO saas.tb_tenant (name, subdomain, plan, status, max_users, max_projects)
VALUES ('Acme Corp', 'acme', 'starter', 'active', 50, 10);

INSERT INTO saas.tb_tenant (name, subdomain, plan, status, max_users, max_projects)
VALUES ('TechStart Inc', 'techstart', 'professional', 'active', 200, 50);

-- Create users for each tenant
INSERT INTO saas.tb_user (tenant_id, username, email, display_name, role, status)
VALUES (1, 'john', 'john@acme.com', 'John Doe', 'admin', 'active');

INSERT INTO saas.tb_user (tenant_id, username, email, display_name, role, status)
VALUES (2, 'jane', 'jane@techstart.com', 'Jane Smith', 'admin', 'active');

-- Create projects
INSERT INTO saas.tb_project (tenant_id, owner_id, name, description, status)
VALUES (1, 1, 'Website Redesign', 'Redesign company website', 'active');

INSERT INTO saas.tb_project (tenant_id, owner_id, name, description, status)
VALUES (2, 2, 'Mobile App', 'Develop mobile application', 'active');

-- Create tasks
INSERT INTO saas.tb_task (project_id, tenant_id, assigned_to_id, title, status, priority)
VALUES (1, 1, 1, 'Design homepage', 'in_progress', 'high');

INSERT INTO saas.tb_task (project_id, tenant_id, assigned_to_id, title, status, priority)
VALUES (2, 2, 2, 'Setup development environment', 'todo', 'medium');
EOF

# Query tenant-isolated data
psql saas_test -c "SELECT * FROM saas.tv_tenant;"
psql saas_test -c "SELECT * FROM saas.tv_user WHERE tenant_id = 1;"
psql saas_test -c "SELECT * FROM saas.tv_project WHERE tenant_id = 1;"

# Test business logic
psql saas_test -c "SELECT saas.fn_tenant_upgrade_plan(1, 'admin@example.com');"
psql saas_test -c "SELECT saas.fn_task_complete_task(1, 'john@acme.com');"
```

## Step 11: FraiseQL Integration

Add this to your FraiseQL configuration:

```yaml
# fraiseql-config.yaml
schemas:
  - name: saas
    entities:
      - entities/saas/tenant.yaml
      - entities/saas/user.yaml
      - entities/saas/project.yaml
      - entities/saas/task.yaml
      - entities/saas/invoice.yaml
      - entities/saas/invoice_item.yaml
      - entities/saas/global_settings.yaml

# This gives you instant GraphQL API with tenant isolation:
# - query { projects { name tasks { title status } } } # Only shows current tenant's data
# - mutation { createProject(input: {name: "New Project"}) { id } }
# - query { globalSettings { maintenanceMode } } # Shared across tenants
```

## Common Multi-Tenant Patterns Used

### 1. Tenant Isolation
- **Foreign Keys**: All tenant-specific tables have `tenant_id`
- **Row Level Security**: Database-level access control
- **Application Logic**: Code validates tenant access

### 2. Shared vs Tenant Data
```yaml
# Shared data (no tenant_id)
entity: GlobalSettings

# Tenant-specific data (has tenant_id)
entity: User
fields:
  tenant: ref(Tenant)
```

### 3. Plan-based Limits
- **Resource Limits**: Different plans have different limits
- **Validation**: Actions check against tenant limits
- **Upgrades**: Plan changes adjust limits automatically

### 4. Hierarchical Permissions
- **Tenant Admin**: Can manage tenant users/projects
- **Project Owner**: Can manage their projects
- **Regular User**: Limited to assigned tasks

### 5. Denormalization for Performance
```yaml
entity: Task
fields:
  project: ref(Project)
  tenant: ref(Tenant)  # Denormalized for faster RLS queries
```

## Full Source Code

All YAML files for this example:
- [View Source](../../examples/saas-multi-tenant/)
- [View on GitHub](https://github.com/fraiseql/specql/tree/main/examples/saas-multi-tenant)

## Next Steps

- Implement tenant provisioning automation
- Add billing and subscription management
- Create tenant-specific customizations
- Implement data export/import per tenant
- Add tenant analytics and reporting
- Set up tenant migration tools
- Create super-admin dashboard
- Implement tenant backup/restore
- Add cross-tenant collaboration features

This multi-tenant SaaS system demonstrates how SpecQL enables rapid development of scalable, secure multi-tenant applications with proper data isolation, resource management, and enterprise-grade features.