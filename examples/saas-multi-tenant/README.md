# SaaS Multi-Tenant Example

**Multi-tenant SaaS application built with SpecQL** 🏢

Automatic tenant isolation with Row Level Security.

## Overview

Multi-tenant SaaS with:
- **Tenants** (companies using the app)
- **Users** (people within tenants)
- **Projects** (tenant-scoped projects)
- **Tasks** (project tasks)

All business data automatically isolated by tenant.

## Schema Architecture

### `schema: app` - Application-wide data
Shared across all tenants (tenants themselves, global config)

### `schema: tenant` - Tenant-scoped data
Business data automatically isolated per tenant

## Entities

### Tenant (`tenant.yaml`)

```yaml
entity: Tenant
schema: app
description: "SaaS tenant/company"

fields:
  name: text!
  subdomain: text!
  status: enum(active, suspended, cancelled)

actions:
  - name: create_tenant
  - name: update_tenant
```

### User (`user.yaml`)

```yaml
entity: User
schema: tenant
description: "User within a tenant"

fields:
  email: email!
  first_name: text!
  last_name: text!
  role: enum(admin, manager, member)

actions:
  - name: create_user
  - name: update_user
```

### Project (`project.yaml`)

```yaml
entity: Project
schema: tenant
description: "Tenant project"

fields:
  name: text!
  description: text
  status: enum(active, completed, archived)
  owner: ref(User)!

actions:
  - name: create_project
  - name: update_project
```

### Task (`task.yaml`)

```yaml
entity: Task
schema: tenant
description: "Project task"

fields:
  title: text!
  description: markdown
  status: enum(todo, in_progress, done)
  assignee: ref(User)
  project: ref(Project)!

actions:
  - name: create_task
  - name: update_task
  - name: assign_task
```

## Generated Security

### Row Level Security

```sql
-- Automatic tenant isolation
ALTER TABLE tenant.tb_user ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenant.tb_user
  USING (tenant_id = current_tenant_id());

ALTER TABLE tenant.tb_project ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenant.tb_project
  USING (tenant_id = current_tenant_id());
```

### Function Security

```sql
-- Tenant-aware functions
CREATE FUNCTION tenant.create_user(...) RETURNS app.mutation_result
SECURITY DEFINER
SET search_path = tenant, app, common
AS $$
-- Function automatically scoped to current tenant
$$ LANGUAGE plpgsql;
```

## Quick Start

```bash
cd examples/saas-multi-tenant
specql generate entities/*.yaml
createdb saas_example
cd db/schema
confiture migrate up
```

### Test Tenant Isolation

```sql
-- Create two tenants
SELECT app.create_tenant('Company A', 'company-a');
SELECT app.create_tenant('Company B', 'company-b');

-- Set tenant context
SELECT app.set_current_tenant('tenant-1-id');

-- Create user (automatically scoped to tenant 1)
SELECT tenant.create_user('user@company-a.com', 'John', 'Doe');

-- Switch tenant
SELECT app.set_current_tenant('tenant-2-id');

-- Different tenant - no access to tenant 1's data
SELECT COUNT(*) FROM tenant.tb_user;  -- Returns 0
```

## File Structure

```
examples/saas-multi-tenant/
├── README.md
└── entities/
    ├── tenant.yaml      # schema: app
    ├── user.yaml        # schema: tenant
    ├── project.yaml     # schema: tenant
    └── task.yaml        # schema: tenant
```