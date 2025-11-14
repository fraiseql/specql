# Multi-Tenancy in SpecQL

**Automatic tenant isolation with Row Level Security** 🏢

## Overview

SpecQL makes multi-tenancy simple. Specify `schema: tenant` and get automatic tenant isolation, RLS policies, and cross-tenant security built-in.

**What you get automatically:**
- ✅ `tenant_id UUID` foreign key on all tables
- ✅ Row Level Security (RLS) policies
- ✅ Tenant context in all functions
- ✅ Cross-tenant relationship validation
- ✅ Audit trails with tenant tracking

## Quick Start

### Basic Multi-Tenant Entity

```yaml
entity: Contact
schema: tenant  # This enables multi-tenancy
description: "Customer contacts"

fields:
  first_name: text!
  last_name: text!
  email: email!
  company: text

actions:
  - name: create_contact
  - name: update_contact
  - name: delete_contact
```

**Generated automatically:**
```sql
-- Table with tenant isolation
CREATE TABLE tenant.tb_contact (
  -- Trinity Pattern
  pk_contact INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  -- Automatic tenant isolation
  tenant_id UUID NOT NULL,  -- Every record belongs to a tenant

  -- Your fields
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL,
  company TEXT,

  -- Audit trails
  created_at TIMESTAMPTZ DEFAULT now(),
  created_by UUID,
  updated_at TIMESTAMPTZ DEFAULT now(),
  updated_by UUID,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID
);

-- Row Level Security: Users only see their tenant's data
ALTER TABLE tenant.tb_contact ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenant.tb_contact
  USING (tenant_id = current_tenant_id());
```

## Schema Types

### `schema: tenant` - Multi-Tenant Data
Business data that should be isolated per tenant:

```yaml
entity: Customer
schema: tenant
fields:
  name: text!
  industry: text
```

**Use for:**
- Customer data
- Business transactions
- User-generated content
- Organization-specific settings

### `schema: common` - Shared Reference Data
Data shared across all tenants:

```yaml
entity: Country
schema: common
fields:
  name: text!
  iso_code: text!
```

**Use for:**
- Countries, currencies, languages
- Industry classifications
- System-wide reference data

### `schema: app` - Application Data
Global application configuration:

```yaml
entity: AppConfig
schema: app
fields:
  setting_name: text!
  setting_value: text
```

**Use for:**
- Application-wide settings
- System configuration
- Global reference data

## Tenant Context

### Automatic Context Propagation

All generated functions automatically include tenant context:

```sql
-- Generated function with tenant awareness
CREATE FUNCTION tenant.create_contact(
  tenant_id UUID,  -- Automatic tenant parameter
  first_name TEXT,
  last_name TEXT,
  email TEXT
) RETURNS app.mutation_result AS $$
BEGIN
  -- Function automatically scoped to tenant
  INSERT INTO tenant.tb_contact (
    tenant_id, first_name, last_name, email
  ) VALUES (
    tenant_id, first_name, last_name, email
  );

  RETURN app.success_result('Contact created');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Setting Tenant Context

```sql
-- Set current tenant for session
SELECT app.set_current_tenant('550e8400-e29b-41d4-a716-446655440000');

-- All queries now automatically filtered to this tenant
SELECT * FROM tenant.tb_contact;  -- Only shows this tenant's contacts
```

## Relationships

### Same-Tenant Relationships

```yaml
entity: Contact
schema: tenant
fields:
  organization: ref(Organization)  # Same tenant automatically

entity: Organization
schema: tenant
fields:
  name: text!
```

**Generated:**
```sql
-- Foreign key with tenant enforcement
ALTER TABLE tenant.tb_contact
ADD CONSTRAINT fk_contact_organization
FOREIGN KEY (tenant_id, organization_id)
REFERENCES tenant.tb_organization(tenant_id, pk_organization);
```

### Cross-Schema Relationships

```yaml
entity: Contact
schema: tenant
fields:
  country: ref(Country)  # References common schema

entity: Country
schema: common
fields:
  name: text!
  iso_code: text!
```

**Generated:**
```sql
-- Foreign key to common schema (no tenant_id)
ALTER TABLE tenant.tb_contact
ADD CONSTRAINT fk_contact_country
FOREIGN KEY (country_id)
REFERENCES common.tb_country(pk_country);
```

## Actions & Business Logic

### Tenant-Scoped Actions

```yaml
entity: Contact
schema: tenant
actions:
  - name: create_contact
    description: "Create a new contact for current tenant"
    steps:
      - validate: email IS NOT NULL
      - insert: Contact

  - name: transfer_contact
    description: "Transfer contact to another organization"
    steps:
      - validate: new_org_id IS NOT NULL
      - validate: organization_id != new_org_id
      - update: Contact SET organization_id = new_org_id
```

### Cross-Tenant Operations

For operations that need to span tenants (admin functions):

```yaml
entity: Contact
schema: tenant
actions:
  - name: migrate_tenant_data
    description: "Admin: Migrate data between tenants"
    security: admin_only  # Custom security context
    steps:
      - call: admin.migrate_contact_data(source_tenant, target_tenant)
```

## Security Model

### Row Level Security (RLS)

Automatic RLS policies ensure tenant isolation:

```sql
-- Automatic policy creation
CREATE POLICY tenant_isolation ON tenant.tb_contact
  USING (tenant_id = current_tenant_id());

-- Users can only see/modify their tenant's data
SELECT * FROM tenant.tb_contact;  -- Filtered automatically
```

### Function Security

```sql
-- Generated functions run with tenant context
CREATE FUNCTION tenant.create_contact(...) RETURNS app.mutation_result
SECURITY DEFINER  -- Runs with elevated privileges
SET search_path = tenant, app, common  -- Controlled schema access
```

### Audit Trails

All changes tracked with tenant context:

```sql
-- Audit table includes tenant information
CREATE TABLE app.audit_log (
  tenant_id UUID,  -- Which tenant made the change
  table_name TEXT,
  record_id UUID,
  action TEXT,  -- INSERT, UPDATE, DELETE
  old_values JSONB,
  new_values JSONB,
  changed_by UUID,
  changed_at TIMESTAMPTZ DEFAULT now()
);
```

## Implementation Patterns

### SaaS Application

```yaml
# Core tenant entity
entity: Tenant
schema: app
fields:
  name: text!
  subdomain: text!
  status: enum(active, suspended, cancelled)

# Tenant-scoped business data
entity: Customer
schema: tenant
fields:
  name: text!
  email: email!
  tenant: ref(Tenant)  # Cross-schema reference

entity: Project
schema: tenant
fields:
  name: text!
  customer: ref(Customer)
  status: enum(active, completed, cancelled)
```

### Multi-Organization Enterprise

```yaml
# Top-level organization
entity: Enterprise
schema: app
fields:
  name: text!
  industry: text

# Departments within enterprise
entity: Department
schema: tenant
fields:
  name: text!
  enterprise: ref(Enterprise)
  manager: ref(Employee)

# Employees in departments
entity: Employee
schema: tenant
fields:
  first_name: text!
  last_name: text!
  department: ref(Department)
  email: email!
```

## Best Practices

### 1. Use `tenant` Schema for Business Data

```yaml
# ✅ Good: Business data is tenant-scoped
entity: Invoice
schema: tenant
fields:
  amount: money!
  customer: ref(Customer)

# ❌ Bad: Don't put business data in common schema
entity: Invoice
schema: common  # Wrong! Invoices should be per-tenant
```

### 2. Use `common` for Reference Data

```yaml
# ✅ Good: Reference data shared across tenants
entity: Currency
schema: common
fields:
  code: text!  # USD, EUR, etc.
  name: text!

# ❌ Bad: Don't duplicate reference data per tenant
entity: Currency
schema: tenant  # Wrong! Currency codes are universal
```

### 3. Validate Cross-Tenant Access

```yaml
actions:
  - name: share_customer
    description: "Share customer with another tenant"
    steps:
      - validate: target_tenant_id IS NOT NULL
      - validate: has_permission('share_customers')
      - call: admin.create_tenant_sharing(customer_id, target_tenant_id)
```

### 4. Handle Tenant Context Properly

```yaml
# Always set tenant context at session start
SELECT app.set_current_tenant(get_jwt_claim('tenant_id'));

# Use tenant-aware functions
SELECT tenant.create_customer(name := 'Acme Corp');
```

## Migration Strategies

### Adding Multi-Tenancy to Existing Data

```sql
-- 1. Add tenant_id column
ALTER TABLE existing_table ADD COLUMN tenant_id UUID;

-- 2. Set default tenant for existing data
UPDATE existing_table SET tenant_id = 'default-tenant-id';

-- 3. Make tenant_id NOT NULL
ALTER TABLE existing_table ALTER COLUMN tenant_id SET NOT NULL;

-- 4. Add RLS policy
ALTER TABLE existing_table ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON existing_table
  USING (tenant_id = current_tenant_id());

-- 5. Create tenant-aware functions
-- (SpecQL generates these automatically)
```

### Splitting Single-Tenant to Multi-Tenant

```sql
-- Create tenant table
CREATE TABLE app.tb_tenant (
  pk_tenant INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  name TEXT NOT NULL
);

-- Migrate existing data to default tenant
INSERT INTO app.tb_tenant (name) VALUES ('Default Tenant');

-- Add tenant_id to existing tables
-- Follow steps above for each table
```

## Testing Multi-Tenant Applications

### Unit Tests with Tenant Context

```sql
-- Set up test tenant
INSERT INTO app.tb_tenant (id, name)
VALUES ('test-tenant-id', 'Test Tenant');

-- Set tenant context for test
SELECT app.set_current_tenant('test-tenant-id');

-- Run tenant-scoped tests
SELECT tenant.create_customer(name := 'Test Customer');
SELECT COUNT(*) FROM tenant.tb_customer;  -- Should be 1

-- Switch tenant context
SELECT app.set_current_tenant('other-tenant-id');
SELECT COUNT(*) FROM tenant.tb_customer;  -- Should be 0
```

### Integration Tests

```python
def test_tenant_isolation():
    # Create two tenants
    tenant1 = create_tenant("Tenant 1")
    tenant2 = create_tenant("Tenant 2")

    # Create customer in tenant 1
    with tenant_context(tenant1):
        customer = create_customer("Customer A")

    # Verify isolation
    with tenant_context(tenant1):
        assert get_customers() == [customer]

    with tenant_context(tenant2):
        assert get_customers() == []
```

## Troubleshooting

### "No tenant context set" Error

```sql
-- Set tenant context first
SELECT app.set_current_tenant('your-tenant-id');

-- Then run tenant operations
SELECT tenant.create_contact(...);
```

### "Permission denied" on RLS

```sql
-- Check current tenant context
SELECT current_tenant_id();

-- Verify user has access to tenant
SELECT * FROM app.tb_tenant WHERE id = current_tenant_id();
```

### Cross-tenant data leakage

```sql
-- Check RLS policies are enabled
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'tenant';

-- Verify policies exist
SELECT * FROM pg_policies WHERE schemaname = 'tenant';
```

## Advanced Patterns

### Tenant-Specific Configuration

```yaml
entity: TenantConfig
schema: tenant
fields:
  setting_name: text!
  setting_value: text
  data_type: enum(string, number, boolean)

actions:
  - name: get_setting
    description: "Get tenant-specific setting"
  - name: update_setting
    description: "Update tenant configuration"
```

### Tenant User Management

```yaml
entity: TenantUser
schema: tenant
fields:
  user_id: ref(User)  # Global user
  role: enum(admin, editor, viewer)
  permissions: json

entity: User
schema: app  # Global users
fields:
  email: email!
  password_hash: text
```

### Multi-Tenant Reporting

```yaml
entity: Report
schema: tenant
actions:
  - name: generate_tenant_report
    description: "Generate report for current tenant"
    steps:
      - call: reporting.generate_customer_summary()
      - call: reporting.generate_revenue_report()
```

## Performance Considerations

### Indexing Strategy

```sql
-- Automatic tenant-aware indexes
CREATE INDEX idx_contact_tenant_email ON tenant.tb_contact(tenant_id, email);
CREATE INDEX idx_contact_tenant_created ON tenant.tb_contact(tenant_id, created_at);
```

### Query Optimization

```sql
-- Tenant-aware queries are automatically optimized
SELECT * FROM tenant.tb_contact
WHERE tenant_id = current_tenant_id()  -- Automatic filter
  AND email LIKE '%@company.com';
```

### Partitioning Strategy

For high-volume multi-tenant applications:

```sql
-- Partition by tenant for massive scale
CREATE TABLE tenant.tb_contact PARTITION BY LIST (tenant_id);

-- Create partition per tenant
CREATE TABLE tenant.tb_contact_tenant1 PARTITION OF tenant.tb_contact
  FOR VALUES IN ('tenant-1-id');
```

## Next Steps

- **Read Actions Guide**: Learn business logic patterns in `docs/guides/actions-guide.md`
- **Check GraphQL Integration**: See `docs/guides/graphql-integration.md` for API patterns
- **Browse Examples**: See `examples/saas-multi-tenant/` for complete implementation
- **Security Best Practices**: Read `docs/guides/security-best-practices.md`

---

**Multi-tenancy should be invisible to your business logic, but rock-solid in your data layer.** 🔒