# Schema Strategy: App/Core Pattern & Multi-Tenancy

**Date**: 2025-11-08
**Status**: ✅ FINALIZED
**Context**: PostgreSQL schema organization for multi-tenant enterprise applications

---

## Executive Summary

This document defines the schema strategy for the PrintOptim backend, establishing clear patterns for:

1. **Schema Organization**: `app` (API) vs `core` (business logic) vs entity schemas
2. **Multi-Tenancy**: JWT token context, denormalized `tenant_id`, tenant isolation
3. **Security Boundaries**: Row-Level Security (RLS) and data isolation
4. **Performance Patterns**: Denormalization for query efficiency

---

## Schema Types & Purposes

### 1. Application Schema (`app`)
**Purpose**: Public API contract, GraphQL types, external interfaces

**Contents**:
- Composite types: `app.type_*_input` (GraphQL input types)
- Standard types: `app.mutation_result` (GraphQL MutationResult)
- Deletion types: `app.type_deletion_input`

**Example**:
```sql
-- GraphQL API contract
CREATE TYPE app.type_create_contact_input AS (
    email TEXT,
    company_id UUID,  -- External: UUIDs
    status TEXT
);

-- Standard mutation response
CREATE TYPE app.mutation_result AS (
    id UUID,
    status TEXT,
    message TEXT,
    object_data JSONB
);
```

**Security**: No sensitive data, public interface.

### 2. Core Schema (`core`)
**Purpose**: Business logic functions, data validation, complex operations

**Contents**:
- Business functions: `core.create_contact()`, `core.update_contact()`
- Validation logic: Email patterns, business rules
- Trinity helper functions: `core.contact_pk()`, `core.contact_id()`

**Example**:
```sql
-- Business logic function
CREATE FUNCTION core.create_contact(
    input_pk_organization UUID,  -- JWT tenant_id
    input_created_by UUID,       -- JWT user_id
    input_data app.type_create_contact_input
) RETURNS app.mutation_result;

-- Trinity helper: UUID → INTEGER
CREATE FUNCTION core.contact_pk(identifier TEXT) RETURNS INTEGER;
```

**Security**: Row-Level Security (RLS) applied, tenant isolation enforced.

### 3. Entity Schemas (`crm`, `management`, `operations`)
**Purpose**: Domain-specific data storage, business entities

**Contents**:
- Tables: `crm.tb_contact`, `management.tb_organization`
- Indexes: Performance optimization
- Constraints: Data integrity

**Schema Tiers & Multi-Tenancy Classification**:

| Schema | Type | tenant_id | RLS | Purpose | Tier |
|--------|------|-----------|-----|---------|------|
| `common` | Framework | ❌ NONE | ❌ NO | Reference data | **Tier 1** |
| `app` | Framework | ❌ NONE | ❌ NO | API types | **Tier 1** |
| `core` | Framework | Mixed | Mixed | Business functions | **Tier 1** |
| `crm` | Multi-Tenant | ✅ REQUIRED | ✅ YES | Customer data | **Tier 2** |
| `projects` | Multi-Tenant | ✅ REQUIRED | ✅ YES | Projects/tasks | **Tier 2** |
| `catalog` | Shared (App-Specific) | ❌ NONE | ❌ NO | Product catalog (PrintOptim) | **Tier 3** |
| `analytics` | Shared (App-Specific) | ❌ NONE | ❌ NO | Analytics data | **Tier 3** |
| `finance` | Shared (App-Specific) | ❌ NONE | ❌ NO | Financial data | **Tier 3** |

### Schema Registry Pattern

**Central Source of Truth**: Domain registry (`registry/domain_registry.yaml`) + SchemaRegistry class

```yaml
# registry/domain_registry.yaml
domains:
  "2":
    name: crm
    aliases: [management]
    multi_tenant: true  # ← EXPLICIT FLAG
    description: "Customer relationship management"
```

```python
# src/generators/schema/schema_registry.py
schema_registry = SchemaRegistry(domain_registry)

# Check multi-tenancy
if schema_registry.is_multi_tenant("crm"):  # True
    add_tenant_id_column()

# Resolve aliases
canonical = schema_registry.get_canonical_schema_name("management")  # "crm"
```

### Adding Custom Domains

Users can extend the framework with custom domains:

```yaml
# Add to registry/domain_registry.yaml
domains:
  "7":
    name: sales
    multi_tenant: true   # Tenant-specific sales data
    description: "Sales pipeline and opportunities"

  "8":
    name: hr
    multi_tenant: true   # Employee records
    description: "Human resources management"

  "9":
    name: legal
    multi_tenant: false  # Shared legal documents
    description: "Legal templates and contracts"
```

---

## Multi-Tenancy Pattern: JWT Context + Denormalized tenant_id

### The Golden Rule
**Never trust user input for security context. JWT tokens are verified by auth middleware.**

### JWT Token Structure
```javascript
// Verified JWT payload (server-enforced)
{
  "sub": "user-uuid-123",        // → created_by, updated_by
  "tenant_id": "tenant-uuid-456", // → tenant_id column
  "organization_id": "org-uuid-789" // → fk_organization (optional)
}
```

### Table Structure Pattern

#### Tenant-Specific Tables (crm, management, operations)
```sql
CREATE TABLE crm.tb_contact (
    -- Trinity Pattern
    pk_contact INTEGER PRIMARY KEY,
    id UUID UNIQUE,

    -- 🔒 SECURITY: Denormalized from JWT (CRITICAL!)
    tenant_id UUID NOT NULL,  -- From JWT "tenant_id"

    -- 🔗 BUSINESS: Optional FK to organization
    fk_organization INTEGER,  -- From user input (optional)

    -- 💼 BUSINESS: User-provided data
    email TEXT,               -- From user input
    fk_company INTEGER,       -- From user input

    -- 📋 AUDIT: From JWT (server-controlled)
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID,          -- From JWT "sub"
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID,          -- From JWT "sub"
    deleted_at TIMESTAMPTZ,   -- Soft delete
    deleted_by UUID           -- From JWT "sub"
);

-- 🔑 CRITICAL INDEX: tenant_id for filtering & RLS
CREATE INDEX idx_tb_contact_tenant ON crm.tb_contact(tenant_id);
```

#### Shared Tables (common, catalog)
```sql
CREATE TABLE common.tb_country (
    -- Trinity Pattern (no tenant isolation)
    pk_country INTEGER PRIMARY KEY,
    id UUID UNIQUE,

    -- 🌍 SHARED: No tenant context
    code TEXT UNIQUE,
    name TEXT
    -- No tenant_id, no audit fields
);
```

### Row-Level Security (RLS)

#### Enable RLS on Tenant Tables
```sql
-- Enable RLS
ALTER TABLE crm.tb_contact ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policy
CREATE POLICY tenant_isolation ON crm.tb_contact
FOR ALL
TO authenticated_user
USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

#### JWT Context Injection
```sql
-- Set session context from JWT
SELECT set_config('app.current_tenant_id', 'tenant-uuid-456', false);
SELECT set_config('app.current_user_id', 'user-uuid-123', false);
```

### Function Signature Pattern

#### App Layer (GraphQL → Core)
```sql
CREATE FUNCTION app.create_contact(
    input_payload JSONB  -- GraphQL mutation input
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_result app.mutation_result;
BEGIN
    -- Extract JWT context (injected by GraphQL server)
    -- Call core function with security context
    v_result := core.create_contact(
        input_pk_organization := current_setting('app.current_tenant_id')::UUID,
        input_created_by := current_setting('app.current_user_id')::UUID,
        input_data := input_payload::app.type_create_contact_input
    );

    RETURN v_result;
END;
$$;
```

#### Core Layer (Business Logic)
```sql
CREATE FUNCTION core.create_contact(
    input_pk_organization UUID,  -- JWT tenant_id (security)
    input_created_by UUID,       -- JWT user_id (audit)
    input_data app.type_create_contact_input  -- User data
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID := gen_random_uuid();
    v_fk_company INTEGER;
BEGIN
    -- Resolve business FKs (UUID → INTEGER)
    v_fk_company := crm.company_pk(input_data.company_id);

    -- INSERT with security context
    INSERT INTO crm.tb_contact (
        id, tenant_id, fk_company, email,
        created_at, created_by
    ) VALUES (
        v_id,
        input_pk_organization,  -- JWT tenant_id
        v_fk_company,
        input_data.email,
        now(),
        input_created_by        -- JWT user_id
    );

    RETURN (v_id, 'success', 'Contact created', NULL)::app.mutation_result;
END;
$$;
```

---

## Field Transformation Chain

### Complete Mapping: SpecQL → Composite → GraphQL → Database

| SpecQL Field | Composite Type | GraphQL Field | Database Column | Purpose |
|-------------|----------------|----------------|-----------------|---------|
| `company: ref(Company)` | `company_id UUID` | `companyId: UUID` | `fk_company INTEGER` | Business relationship |
| `status: enum(...)` | `status TEXT` | `status: String` | `status TEXT` | Business data |
| `email: text` | `email TEXT` | `email: String` | `email TEXT` | Business data |
| `created_at: timestamp` | ❌ (not in composite) | ❌ (hidden) | `created_at TIMESTAMPTZ` | Audit (server) |
| `tenant_id` | ❌ (security!) | ❌ (hidden) | `tenant_id UUID` | Security (JWT) |

### Transformation Rules

1. **Reference Fields**: `field` → `field_id` (UUID in composite) → `fk_field` (INTEGER in DB)
2. **Security Fields**: Never in composite types (injected by server)
3. **Audit Fields**: Never in composite types (managed by triggers/functions)
4. **Business Fields**: Always in composite types (user-provided)

### Naming Convention Priority
1. **GraphQL Convention**: `companyId` (camelCase)
2. **Database Convention**: `fk_company` (snake_case with prefix)
3. **SpecQL Convention**: `company` (simple names)

---

## Implementation Checklist

### Schema Classification
- ✅ `app`: API types only
- ✅ `core`: Business functions + helpers
- ✅ `crm`, `management`, `operations`: Tenant data
- ✅ `common`, `catalog`: Shared data

### Multi-Tenancy Implementation
- ✅ JWT token structure defined
- ✅ `tenant_id` denormalization pattern
- ✅ RLS policies for tenant isolation
- ✅ Session context management

### Security Boundaries
- ✅ JWT context injection
- ✅ Server-controlled security fields
- ✅ User input validation
- ✅ No security data in composite types

### Performance Patterns
- ✅ `tenant_id` indexes on all tenant tables
- ✅ Denormalized tenant_id for fast filtering
- ✅ Trinity helper functions for UUID ↔ INTEGER

---

## Migration Strategy

### Phase 1: Foundation (Current)
- ✅ Schema strategy documented
- ✅ Multi-tenancy pattern defined
- ✅ JWT context integration planned

### Phase 2: Implementation
- 🔄 Update table generators for tenant_id
- 🔄 Add Trinity helper functions
- 🔄 Implement RLS policies
- 🔄 Update function signatures

### Phase 3: Migration
- 🔄 Data migration for existing tables
- 🔄 Update existing functions
- 🔄 Test tenant isolation
- 🔄 Performance validation

---

## References

- **APP_CORE_FUNCTION_PATTERN.md**: Function signature patterns
- **JWT Token Specification**: Authentication service docs
- **Row-Level Security Guide**: PostgreSQL RLS documentation
- **Trinity Pattern**: UUID/INTEGER/identifier resolution

---

**Last Updated**: 2025-11-08
**Status**: ✅ APPROVED FOR IMPLEMENTATION</content>
</xai:function_call
