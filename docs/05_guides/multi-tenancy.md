# Multi-Tenancy Guide

> **Build secure, scalable SaaS applications with SpecQL's built-in multi-tenancy support**

## Overview

SpecQL provides **automatic multi-tenancy** for SaaS applications. Define your entities once, and SpecQL generates:
- ✅ Tenant isolation at the database level
- ✅ Row-level security (RLS) policies
- ✅ Automatic tenant_id injection
- ✅ Cross-tenant query prevention
- ✅ Tenant-aware indexes

**Zero configuration required** - just declare which schemas are multi-tenant.

---

## What is Multi-Tenancy?

Multi-tenancy allows a single application instance to serve multiple customers (tenants) while ensuring complete data isolation.

### Example: SaaS CRM

```
Tenant 1 (Acme Corp):
  - Contacts: 500
  - Companies: 50
  - Orders: 1,200

Tenant 2 (Widget Inc):
  - Contacts: 300
  - Companies: 30
  - Orders: 800

❌ Tenant 1 can NEVER see Tenant 2's data
✅ Complete isolation enforced by PostgreSQL RLS
```

---

## Quick Start

### Step 1: Define Schema Registry

**`registry/domain_registry.yaml`**:
```yaml
schemas:
  # Multi-tenant schemas
  crm:
    tier: multi_tenant
    description: "Customer relationship management"

  projects:
    tier: multi_tenant
    description: "Project management"

  # Shared schemas (no tenant isolation)
  catalog:
    tier: shared
    description: "Product catalog (shared across all tenants)"

  # Framework schemas (universal)
  app:
    tier: framework
  common:
    tier: framework
```

### Step 2: Define Entities

**`entities/contact.yaml`**:
```yaml
entity: Contact
schema: crm  # Multi-tenant schema

fields:
  email: email!
  first_name: text!
  last_name: text!
  company: ref(Company)!

# ✅ tenant_id is automatically added
# ✅ RLS policies are automatically created
# ✅ Indexes include tenant_id
```

### Step 3: Generate SQL

```bash
specql generate entities/*.yaml --output generated/
```

**Generated SQL** (automatic):
```sql
-- Table with automatic tenant_id
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,

    email TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    fk_company INTEGER NOT NULL,

    tenant_id UUID NOT NULL,  -- ✅ Automatically added

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Row-level security policy
ALTER TABLE crm.tb_contact ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON crm.tb_contact
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Tenant-aware indexes
CREATE INDEX idx_tb_contact_tenant_email
    ON crm.tb_contact (tenant_id, email);

CREATE INDEX idx_tb_contact_tenant_company
    ON crm.tb_contact (tenant_id, fk_company);
```

### Step 4: Use in Application

```typescript
// Set tenant context (once per request)
await db.query(
  "SELECT set_config('app.current_tenant_id', $1, false)",
  [tenantId]
);

// All queries are automatically tenant-scoped
const contacts = await graphql(`
  query {
    contacts {  # Only returns current tenant's contacts
      email
      firstName
    }
  }
`);

// Mutations are automatically tenant-scoped
const result = await graphql(`
  mutation {
    qualifyLead(contactId: "123") {
      status
      data {
        email
        status
      }
    }
  }
`);
// ✅ Can only qualify leads in current tenant
```

---

## Schema Tiers

SpecQL supports three schema tiers:

### 1. Multi-Tenant Schemas

**Purpose**: Customer-specific data (isolated per tenant)

```yaml
schemas:
  crm:
    tier: multi_tenant
  projects:
    tier: multi_tenant
  finance:
    tier: multi_tenant
```

**Automatic Features**:
- ✅ `tenant_id UUID NOT NULL` added to all tables
- ✅ RLS policies enforce isolation
- ✅ All indexes include `tenant_id`
- ✅ Foreign keys are tenant-aware
- ✅ GraphQL mutations check tenant ownership

**Use Cases**:
- Customer data (contacts, companies, orders)
- User-generated content
- Tenant-specific settings
- Isolated workflows

### 2. Shared Schemas

**Purpose**: Data shared across all tenants

```yaml
schemas:
  catalog:
    tier: shared
    description: "Product catalog"
  analytics:
    tier: shared
    description: "Cross-tenant analytics"
```

**Features**:
- ❌ NO `tenant_id` column
- ❌ NO RLS policies
- ✅ Accessible by all tenants (read-only recommended)

**Use Cases**:
- Product catalogs
- Reference data (countries, currencies)
- Global settings
- Cross-tenant reporting (admin only)

### 3. Framework Schemas

**Purpose**: SpecQL framework internals

```yaml
schemas:
  app:
    tier: framework
  common:
    tier: framework
  core:
    tier: framework
```

**Features**:
- System-level types (`mutation_result`, etc.)
- Helper functions
- Not user-modifiable

---

## Tenant Context

### Setting Tenant Context

**Every request must set the tenant context**:

```typescript
// Express middleware
app.use(async (req, res, next) => {
  const tenantId = req.user.tenantId;  // From JWT/session

  await db.query(
    "SELECT set_config('app.current_tenant_id', $1, false)",
    [tenantId]
  );

  next();
});
```

```python
# Django middleware
class TenantMiddleware:
    def __call__(self, request):
        tenant_id = request.user.tenant_id

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.current_tenant_id', %s, false)",
                [str(tenant_id)]
            )

        return self.get_response(request)
```

```rust
// Actix-web middleware
async fn set_tenant_context(
    req: ServiceRequest,
    srv: &mut S,
) -> Result<ServiceResponse, Error> {
    let tenant_id = extract_tenant_id(&req)?;

    let conn = req.app_data::<PgPool>().unwrap();
    sqlx::query("SELECT set_config('app.current_tenant_id', $1, false)")
        .bind(tenant_id.to_string())
        .execute(conn)
        .await?;

    srv.call(req).await
}
```

### Current Tenant Access

**In actions, access current tenant**:

```yaml
actions:
  - name: create_contact
    steps:
      - insert: Contact VALUES (
          email: $email,
          first_name: $first_name,
          tenant_id: current_setting('app.current_tenant_id')::UUID
        )
      # ✅ Automatically uses current tenant
```

**SpecQL automatically injects `tenant_id`**, so you typically don't need to specify it manually.

---

## Cross-Tenant Queries

### Preventing Cross-Tenant Access

**Row-Level Security (RLS) automatically prevents**:

```sql
-- Attacker tries to access another tenant's data
SET app.current_tenant_id = '00000000-0000-0000-0000-000000000001';

SELECT * FROM crm.tb_contact WHERE pk_contact = 123;
-- ❌ Returns empty (contact belongs to different tenant)

UPDATE crm.tb_contact SET email = 'hacked@evil.com' WHERE pk_contact = 123;
-- ❌ Updates 0 rows (RLS blocks access)
```

### Intentional Cross-Tenant Access (Admin)

**For admin/super-user scenarios**:

```yaml
# Admin-only schema (NOT multi-tenant)
schemas:
  admin:
    tier: shared

entity: TenantReport
schema: admin

table_view: CrossTenantAnalytics
source: Contact  # Multi-tenant table
bypass_rls: true  # Admin only!

fields:
  tenant_id: uuid!
  contact_count: count(*)
  total_revenue: sum(orders.total)
group_by:
  - tenant_id
```

**Security**: Only accessible by superuser role.

---

## Tenant-Aware Relationships

### Same-Schema Relationships

**Automatic tenant scoping**:

```yaml
entity: Contact
schema: crm  # Multi-tenant

fields:
  company: ref(Company)!  # Also in crm schema

# ✅ Automatically scoped: Contact.tenant_id = Company.tenant_id
```

**Generated Foreign Key**:
```sql
ALTER TABLE crm.tb_contact
    ADD CONSTRAINT fk_contact_company
    FOREIGN KEY (fk_company, tenant_id)
    REFERENCES crm.tb_company (pk_company, tenant_id);
```

### Cross-Schema Relationships

**Multi-tenant → Shared** (allowed):

```yaml
entity: Order
schema: crm  # Multi-tenant

fields:
  product: ref(Product)!  # Product in 'catalog' (shared)

# ✅ Allowed: Orders can reference shared product catalog
```

**Multi-tenant → Multi-tenant (different schemas)** (not allowed):

```yaml
entity: Invoice
schema: finance  # Multi-tenant schema

fields:
  contact: ref(Contact)!  # Contact in 'crm' (different multi-tenant schema)

# ❌ Error: Cross-schema multi-tenant references not allowed
#    Use shared identifiers or duplicate data
```

**Reason**: Different multi-tenant schemas may have different tenant sets.

---

## Tenant Onboarding

### Automatic Tenant Creation

**When a new tenant signs up**:

1. **Create tenant record** (in shared schema):

```yaml
entity: Tenant
schema: common  # Shared schema

fields:
  name: text!
  subdomain: text!
  plan: enum(free, pro, enterprise)!
  status: enum(trial, active, suspended)!
```

2. **Tenant data is automatically isolated**:

```typescript
// New tenant signup
const tenantId = await createTenant({
  name: "Acme Corp",
  subdomain: "acme",
  plan: "pro"
});

// Set tenant context
await setTenantContext(tenantId);

// Create initial data (automatically scoped to tenant)
await graphql(`
  mutation {
    createCompany(input: {
      name: "Acme Corporation"
    }) {
      status
    }
  }
`);
// ✅ Company.tenant_id = tenantId (automatic)
```

### Data Migration Between Tenants

**Intentional data transfer** (rare):

```sql
-- Admin-only operation
BEGIN;

-- Copy contact from tenant A to tenant B
INSERT INTO crm.tb_contact (
    id, identifier, email, first_name, last_name, tenant_id
)
SELECT
    gen_random_uuid(),  -- New UUID
    'CONTACT-' || gen_random_uuid()::text,  -- New identifier
    email, first_name, last_name,
    '00000000-0000-0000-0000-000000000002'  -- Target tenant
FROM crm.tb_contact
WHERE pk_contact = 123
  AND tenant_id = '00000000-0000-0000-0000-000000000001';  -- Source tenant

COMMIT;
```

**Security**: Requires superuser or special admin role.

---

## Performance Optimization

### Tenant-Aware Indexes

**SpecQL automatically creates tenant-aware indexes**:

```sql
-- Standard index (BAD for multi-tenant)
CREATE INDEX idx_tb_contact_email ON crm.tb_contact (email);
-- ❌ Slow: scans across all tenants

-- Tenant-aware index (GOOD)
CREATE INDEX idx_tb_contact_tenant_email ON crm.tb_contact (tenant_id, email);
-- ✅ Fast: tenant_id narrows search immediately
```

**Query performance**:
```sql
-- Without tenant-aware index
EXPLAIN SELECT * FROM crm.tb_contact WHERE email = 'john@example.com';
-- Seq Scan: 1,000,000 rows

-- With tenant-aware index
SET app.current_tenant_id = '...';
EXPLAIN SELECT * FROM crm.tb_contact WHERE email = 'john@example.com';
-- Index Scan: ~500 rows (single tenant)
```

### Partitioning (Advanced)

**For very large deployments**, consider table partitioning by tenant:

```sql
-- Partition by tenant_id
CREATE TABLE crm.tb_contact (
    -- fields
) PARTITION BY HASH (tenant_id);

-- Create partitions
CREATE TABLE crm.tb_contact_p0 PARTITION OF crm.tb_contact
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE crm.tb_contact_p1 PARTITION OF crm.tb_contact
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

-- etc.
```

**Benefits**:
- Faster queries (scans fewer rows)
- Easier tenant archival
- Better vacuum performance

**Tradeoff**: More complex schema management.

---

## Security Best Practices

### 1. Always Set Tenant Context

```typescript
// ❌ BAD: Forget to set tenant context
const contacts = await db.query('SELECT * FROM crm.tb_contact');
// Returns 0 rows (RLS blocks everything)

// ✅ GOOD: Always set tenant context
await setTenantContext(req.user.tenantId);
const contacts = await db.query('SELECT * FROM crm.tb_contact');
```

### 2. Use Connection Pooling Carefully

```typescript
// ❌ BAD: Tenant context leaks between requests
app.use((req, res, next) => {
  db.query("SET app.current_tenant_id = $1", [req.user.tenantId]);
  // Uses same connection for all requests!
  next();
});

// ✅ GOOD: Set per-transaction
app.use(async (req, res, next) => {
  await db.query(
    "SELECT set_config('app.current_tenant_id', $1, true)",
    //                                              ^^^ true = transaction-local
    [req.user.tenantId]
  );
  next();
});
```

### 3. Validate Tenant Ownership

```yaml
actions:
  - name: delete_contact
    steps:
      - validate: tenant_id = current_setting('app.current_tenant_id')::UUID
        error: "unauthorized_tenant_access"
      - update: Contact SET deleted_at = now()
```

### 4. Audit Cross-Tenant Access

```yaml
# Log all admin cross-tenant queries
table_view: AdminAuditLog
source: AuditTrail
filters:
  - action = 'cross_tenant_access'
  - user_role = 'admin'
```

---

## Common Patterns

### 1. Tenant-Specific Settings

```yaml
entity: TenantSettings
schema: crm  # Multi-tenant

fields:
  feature_flags: jsonb!
  branding: jsonb!
  limits: jsonb!

# ✅ Each tenant has their own settings
```

### 2. Shared Reference Data

```yaml
entity: Country
schema: common  # Shared

fields:
  name: text!
  code: text(2)!

# ✅ All tenants share same country list
```

### 3. Tenant User Management

```yaml
entity: User
schema: crm  # Multi-tenant

fields:
  email: email!
  role: enum(admin, user, viewer)!
  tenant_id: uuid!  # Automatically added

# ✅ Users belong to specific tenants
```

### 4. Cross-Tenant Reporting (Admin)

```yaml
entity: TenantMetrics
schema: admin  # Shared (admin-only)

table_view: TenantRevenue
source: Order  # Multi-tenant
bypass_rls: true  # Admin only

fields:
  tenant_id: uuid!
  total_revenue: sum(total)
  order_count: count(*)
group_by:
  - tenant_id
```

---

## Migration to Multi-Tenancy

### Adding Multi-Tenancy to Existing App

**Step 1**: Update schema registry
```yaml
schemas:
  crm:
    tier: multi_tenant  # Was: shared
```

**Step 2**: SpecQL auto-generates migration
```bash
specql generate entities/*.yaml --output generated/
```

**Generated Migration**:
```sql
-- Add tenant_id column
ALTER TABLE crm.tb_contact
    ADD COLUMN tenant_id UUID;

-- Set default tenant for existing data
UPDATE crm.tb_contact
    SET tenant_id = '00000000-0000-0000-0000-000000000000'
    WHERE tenant_id IS NULL;

-- Make it required
ALTER TABLE crm.tb_contact
    ALTER COLUMN tenant_id SET NOT NULL;

-- Enable RLS
ALTER TABLE crm.tb_contact ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON crm.tb_contact
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

**Step 3**: Migrate data to tenant-specific records
```sql
-- Assign existing data to specific tenants
UPDATE crm.tb_contact
    SET tenant_id = (
        SELECT tenant_id FROM users WHERE users.pk_user = tb_contact.fk_created_by
    )
    WHERE tenant_id = '00000000-0000-0000-0000-000000000000';
```

---

## Testing Multi-Tenancy

### Unit Tests

```typescript
describe('Multi-tenancy', () => {
  it('should isolate tenant data', async () => {
    // Tenant A creates contact
    await setTenantContext(tenantA);
    const contactA = await createContact({ email: 'a@example.com' });

    // Tenant B cannot see Tenant A's contact
    await setTenantContext(tenantB);
    const contacts = await getContacts();
    expect(contacts).not.toContainEqual(contactA);
  });

  it('should prevent cross-tenant updates', async () => {
    await setTenantContext(tenantA);
    const contact = await createContact({ email: 'test@example.com' });

    await setTenantContext(tenantB);
    const result = await updateContact(contact.id, { email: 'hacked@evil.com' });

    expect(result.status).toBe('error');
    expect(result.code).toBe('not_found');
  });
});
```

### Integration Tests

```bash
# Generate test data for multiple tenants
specql generate entities/*.yaml --with-tests --output generated/

# Run multi-tenant tests
psql -d testdb -f generated/tests/test_multi_tenancy.sql
```

---

## Troubleshooting

### Issue: "Current tenant not set" Error

**Cause**: Forgot to set tenant context

**Solution**:
```typescript
await db.query(
  "SELECT set_config('app.current_tenant_id', $1, false)",
  [tenantId]
);
```

### Issue: Cross-Tenant Data Leak

**Cause**: RLS policy bypassed or disabled

**Check**:
```sql
-- Verify RLS is enabled
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'crm';

-- Check policies
\d+ crm.tb_contact
```

### Issue: Slow Queries

**Cause**: Missing tenant-aware indexes

**Solution**:
```sql
-- Ensure indexes start with tenant_id
CREATE INDEX idx_tb_contact_tenant_email
    ON crm.tb_contact (tenant_id, email);
```

---

## Next Steps

- **Tutorial**: [Your First Entity](your-first-entity.md) - Learn multi-tenant entities
- **Reference**: [Schema Registry](../06_reference/schema-registry.md) - Schema configuration
- **Advanced**: [Performance Tuning](../07_advanced/performance-tuning.md) - Optimize multi-tenant queries
- **Security**: [Security Hardening](../07_advanced/security-hardening.md) - Secure multi-tenant apps

---

**Multi-tenancy in SpecQL is automatic, secure, and performant—focus on your business logic, not isolation.**
