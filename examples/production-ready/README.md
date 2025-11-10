# Production-Ready Example

This example demonstrates a complete CRM contact management system with:

- ✅ Full entity modeling (Contact, Company, User)
- ✅ Rich field types (email, phone, address, contact_info)
- ✅ Business actions with validation
- ✅ Table views for common queries
- ✅ Multi-tenant isolation (automatic tenant_id)
- ✅ Audit trail (automatic created_at, updated_at, deleted_at)

## Architecture

```
┌─────────────────────────────────────────────┐
│  entities/                                  │
│  ├── contact.yaml    (47 lines)            │
│  ├── company.yaml    (15 lines)            │
│  └── user.yaml       (12 lines)            │
└─────────────────────────────────────────────┘
                    ↓
            specql generate
                    ↓
┌─────────────────────────────────────────────┐
│  generated/                (2000+ lines)    │
│  ├── tables/                                │
│  │   ├── tb_contact.sql                    │
│  │   ├── tb_company.sql                    │
│  │   └── tb_user.sql                       │
│  ├── functions/                             │
│  │   ├── contact_helpers.sql               │
│  │   ├── crm_create_contact.sql            │
│  │   ├── crm_qualify_lead.sql              │
│  │   └── crm_assign_to_owner.sql           │
│  └── views/                                 │
│      └── tv_qualified_leads.sql            │
└─────────────────────────────────────────────┘
```

## Quick Start

### 1. Generate SQL

```bash
cd examples/production-ready/
specql generate entities/*.yaml
```

### 2. Create Database

```bash
createdb crm_production
```

### 3. Apply Schema

```bash
# Apply framework types
psql crm_production -f generated/types/app_types.sql

# Apply tables
psql crm_production -f generated/tables/*.sql

# Apply functions
psql crm_production -f generated/functions/*.sql

# Apply views
psql crm_production -f generated/views/*.sql
```

### 4. Test It Works

```sql
-- Create a contact
SELECT crm.create_contact(
    p_email := 'john@example.com',
    p_company := 'acme-corp',
    p_caller_id := '00000000-0000-0000-0000-000000000000'::uuid
);

-- Qualify the lead
SELECT crm.qualify_lead(
    p_contact_id := (SELECT id FROM crm.tb_contact WHERE email = 'john@example.com'),
    p_caller_id := '00000000-0000-0000-0000-000000000000'::uuid
);

-- Check qualified leads view
SELECT * FROM crm.tv_qualified_leads;
```

## What Gets Generated

### Tables (Trinity Pattern)

```sql
CREATE TABLE crm.tb_contact (
    -- Trinity pattern
    pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    identifier TEXT NOT NULL UNIQUE,

    -- Business fields
    email TEXT NOT NULL,
    phone TEXT,
    fk_company INTEGER REFERENCES management.tb_company(pk_company),
    fk_owner INTEGER REFERENCES auth.tb_user(pk_user),
    status TEXT CHECK (status IN ('lead', 'qualified', 'customer', 'churned')),

    -- Rich types
    contact_info app.contact_info,
    address app.address,

    -- Audit fields (automatic)
    tenant_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID,
    deleted_at TIMESTAMP,
    deleted_by UUID
);

-- Indexes (automatic)
CREATE INDEX idx_tb_contact_email ON crm.tb_contact(email);
CREATE INDEX idx_tb_contact_fk_company ON crm.tb_contact(fk_company);
CREATE INDEX idx_tb_contact_fk_owner ON crm.tb_contact(fk_owner);
CREATE INDEX idx_tb_contact_status ON crm.tb_contact(status);
CREATE INDEX idx_tb_contact_tenant_id ON crm.tb_contact(tenant_id);
```

### Helper Functions (Trinity Resolution)

```sql
-- Resolve UUID -> INTEGER
CREATE FUNCTION crm.contact_pk(p_id UUID) RETURNS INTEGER AS $$
    SELECT pk_contact FROM crm.tb_contact WHERE id = p_id;
$$ LANGUAGE SQL STABLE;

-- Resolve UUID -> TEXT
CREATE FUNCTION crm.contact_identifier(p_id UUID) RETURNS TEXT AS $$
    SELECT identifier FROM crm.tb_contact WHERE id = p_id;
$$ LANGUAGE SQL STABLE;

-- Resolve TEXT -> INTEGER
CREATE FUNCTION crm.contact_pk_from_identifier(p_identifier TEXT) RETURNS INTEGER AS $$
    SELECT pk_contact FROM crm.tb_contact WHERE identifier = p_identifier;
$$ LANGUAGE SQL STABLE;
```

### Business Functions (FraiseQL Standard)

```sql
CREATE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID
) RETURNS app.mutation_result AS $$
DECLARE
    v_pk INTEGER;
    v_result app.mutation_result;
BEGIN
    -- Trinity resolution
    v_pk := crm.contact_pk(p_contact_id);
    IF v_pk IS NULL THEN
        v_result.status := 'error';
        v_result.message := 'Contact not found';
        RETURN v_result;
    END IF;

    -- Validation
    IF (SELECT status FROM crm.tb_contact WHERE pk_contact = v_pk) != 'lead' THEN
        v_result.status := 'error';
        v_result.message := 'Contact is not a lead';
        RETURN v_result;
    END IF;

    -- Update
    UPDATE crm.tb_contact
    SET status = 'qualified',
        lifecycle_stage = 'sql',
        qualified_at = NOW(),
        updated_at = NOW(),
        updated_by = p_caller_id
    WHERE pk_contact = v_pk;

    -- Return full object
    SELECT INTO v_result
        id,
        ARRAY['status', 'lifecycle_stage', 'qualified_at', 'updated_at'],
        'success',
        'Lead qualified successfully',
        jsonb_build_object(
            '__typename', 'Contact',
            'id', id,
            'email', email,
            'status', status,
            'lifecycle_stage', lifecycle_stage,
            'company', (SELECT jsonb_build_object('__typename', 'Company', 'id', co.id, 'name', co.name)
                        FROM management.tb_company co WHERE co.pk_company = fk_company)
        ),
        jsonb_build_object(
            '_meta', jsonb_build_object(
                'impacts', jsonb_build_object(
                    'updated', ARRAY['Contact'],
                    'notifications', ARRAY['sales_team']
                )
            )
        )
    FROM crm.tb_contact WHERE pk_contact = v_pk;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

## 100x Code Leverage

**You wrote**: 74 lines of YAML
**SpecQL generated**: 2,000+ lines of production SQL

**Leverage factor**: 27x

Breakdown:
- Tables: 400+ lines (structure + constraints + indexes)
- Helpers: 150+ lines (Trinity resolution functions)
- Actions: 1,200+ lines (Business logic + audit + error handling)
- Comments: 180+ lines (FraiseQL annotations + documentation)

## What You Get For Free

### 1. Trinity Pattern
- `pk_*` INTEGER primary key (fast joins)
- `id` UUID (external references)
- `identifier` TEXT (human-readable)

### 2. Audit Trail
- `created_at`, `created_by`
- `updated_at`, `updated_by`
- `deleted_at`, `deleted_by` (soft delete)

### 3. Multi-Tenant Isolation
- `tenant_id` UUID (automatic)
- RLS policies (if enabled)

### 4. Indexes
- Foreign keys
- Enum fields
- Tenant isolation
- Common query patterns

### 5. FraiseQL Integration
- GraphQL auto-discovery
- Type-safe mutations
- Impact tracking
- Frontend type generation

## Next Steps

1. **Customize**: Modify `entities/*.yaml` to match your domain
2. **Extend**: Add more entities, actions, table views
3. **Deploy**: Use migrations tool (Confiture) for production
4. **Integrate**: Generate TypeScript types for frontend

## Learn More

- [Field Types Guide](../../docs/guides/field_types.md)
- [Actions Guide](../../docs/guides/actions.md)
- [Table Views Guide](../../docs/guides/table_views.md)
- [Trinity Pattern](../../docs/architecture/trinity_pattern.md)