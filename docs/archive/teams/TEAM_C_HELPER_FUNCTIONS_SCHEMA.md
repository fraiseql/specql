# Team C: Helper Functions Schema Correction

**Date**: 2025-11-08
**Status**: 🚨 CRITICAL ARCHITECTURE DECISION
**Priority**: HIGH - Must decide before Team C implementation

---

## 🎯 Issue: Where Should `log_and_return_mutation` Live?

### Current (Inconsistent) Pattern

The implementation plans show **TWO different approaches**:

#### Approach 1: Schema-Specific (WRONG for SpecQL)
```sql
-- From TEAM_C_APP_CORE_FUNCTIONS_PLAN.md
RETURN crm.log_and_return_mutation(...)
RETURN management.log_and_return_mutation(...)
```

**Problem**: Every schema (crm, management, inventory, etc.) would need its own copy!

#### Approach 2: Core Schema (PrintOptim Pattern)
```sql
-- From APP_CORE_FUNCTION_PATTERN.md (existing PrintOptim)
RETURN core.log_and_return_mutation(...)
```

**Problem**: PrintOptim uses `core.*` for business logic functions, not utilities

---

## ✅ Recommended Solution: Utility Schema Pattern

### **Architecture Decision: Use `app.*` Schema for Shared Utilities**

The `app.*` schema should contain:
1. **Type Definitions** - `app.mutation_result`, `app.type_*_input`
2. **API Wrappers** - `app.create_contact()`, `app.update_contact()`
3. **Shared Utilities** - `app.log_and_return_mutation()`

**Rationale**:
- ✅ **Already exists** - Team B generates `app.*` schema
- ✅ **Single location** - All mutations use `app.mutation_result` type
- ✅ **Logical grouping** - App layer concerns (API, types, utilities)
- ✅ **No duplication** - One function serves all business schemas
- ✅ **Clear separation** - Business schemas (`crm`, `management`) only have business logic

---

## 📋 Schema Organization

### **Proposed Schema Structure**

```
┌─────────────────────────────────────────────────────┐
│  app.* - Application Layer (Cross-Cutting)         │
├─────────────────────────────────────────────────────┤
│  - app.mutation_result (type)                       │
│  - app.type_*_input (composite types)              │
│  - app.create_contact() (API wrapper)              │
│  - app.update_contact() (API wrapper)              │
│  - app.log_and_return_mutation() ✅ UTILITY         │
│  - app.build_error_response() ✅ UTILITY            │
│  - app.emit_event() ✅ UTILITY                      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  crm.* - CRM Business Domain                        │
├─────────────────────────────────────────────────────┤
│  - crm.tb_contact (table)                          │
│  - crm.contact_pk() (Trinity helper)               │
│  - crm.create_contact() (business logic)           │
│  - crm.update_contact() (business logic)           │
│  - crm.qualify_lead() (business action)            │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  management.* - Management Domain                   │
├─────────────────────────────────────────────────────┤
│  - management.tb_company (table)                    │
│  - management.company_pk() (Trinity helper)         │
│  - management.create_company() (business logic)     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  mutation_metadata.* - FraiseQL Metadata Types     │
├─────────────────────────────────────────────────────┤
│  - mutation_metadata.entity_impact (type)          │
│  - mutation_metadata.cache_invalidation (type)     │
│  - mutation_metadata.mutation_impact_metadata      │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Corrected Function Pattern

### **1. Utility Function in `app.*` Schema**

```sql
-- ============================================================================
-- SHARED UTILITY: app.log_and_return_mutation
-- Used by ALL business schemas
-- ============================================================================
CREATE OR REPLACE FUNCTION app.log_and_return_mutation(
    p_tenant_id UUID,
    p_user_id UUID,
    p_entity TEXT,
    p_entity_id UUID,
    p_operation TEXT,
    p_status TEXT,
    p_updated_fields TEXT[],
    p_message TEXT,
    p_object_data JSONB,
    p_extra_metadata JSONB DEFAULT NULL
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_result app.mutation_result;
BEGIN
    -- TODO: Insert into audit log table (future Phase)
    -- INSERT INTO app.tb_mutation_log (...)

    -- Build standardized result
    v_result.id := p_entity_id;
    v_result.updated_fields := p_updated_fields;
    v_result.status := p_status;
    v_result.message := p_message;
    v_result.object_data := p_object_data;
    v_result.extra_metadata := COALESCE(p_extra_metadata, '{}'::jsonb);

    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION app.log_and_return_mutation IS
  'Shared utility for building mutation_result responses. Used by all business schemas.';
```

### **2. Usage in Business Logic**

```sql
-- ============================================================================
-- BUSINESS LOGIC: crm.create_contact
-- Uses app.log_and_return_mutation (shared utility)
-- ============================================================================
CREATE OR REPLACE FUNCTION crm.create_contact(
    auth_tenant_id UUID,
    input_data app.type_create_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := gen_random_uuid();
    v_contact_pk INTEGER;
BEGIN
    -- === VALIDATION ===
    IF input_data.email IS NULL THEN
        -- ✅ Use app.log_and_return_mutation (shared utility)
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'failed:missing_email',
            ARRAY['email']::TEXT[],
            'Email is required',
            NULL,
            jsonb_build_object('reason', 'validation_email_null')
        );
    END IF;

    -- === INSERT ===
    INSERT INTO crm.tb_contact (...) VALUES (...);

    -- === SUCCESS RESPONSE ===
    -- ✅ Use app.log_and_return_mutation (shared utility)
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact created successfully',
        (SELECT row_to_json(c.*) FROM crm.tb_contact c WHERE c.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;
```

### **3. Usage in Other Schemas (Same Pattern)**

```sql
-- management.create_company also uses app.log_and_return_mutation
CREATE OR REPLACE FUNCTION management.create_company(...)
RETURNS app.mutation_result
AS $$
BEGIN
    -- Validation
    IF input_data.name IS NULL THEN
        RETURN app.log_and_return_mutation(...);  -- ✅ Shared utility
    END IF;

    -- Business logic
    INSERT INTO management.tb_company (...) VALUES (...);

    -- Success
    RETURN app.log_and_return_mutation(...);  -- ✅ Shared utility
END;
$$;
```

---

## 📊 Benefits of `app.*` Schema for Utilities

### **1. Single Source of Truth**
```sql
-- ✅ ONE function in app schema
CREATE FUNCTION app.log_and_return_mutation(...) ...

-- ❌ NOT multiple copies per schema
-- CREATE FUNCTION crm.log_and_return_mutation(...) ...
-- CREATE FUNCTION management.log_and_return_mutation(...) ...
-- CREATE FUNCTION inventory.log_and_return_mutation(...) ...
```

### **2. Easy Maintenance**
```sql
-- ✅ Update logic in ONE place
ALTER FUNCTION app.log_and_return_mutation ...

-- Add audit logging:
INSERT INTO app.tb_mutation_log (
    tenant_id,
    user_id,
    entity,
    entity_id,
    operation,
    status,
    timestamp
) VALUES (
    p_tenant_id,
    p_user_id,
    p_entity,
    p_entity_id,
    p_operation,
    p_status,
    now()
);
```

### **3. Consistent Behavior**
All mutations across all schemas return identically structured responses.

### **4. Clear Architecture**
```
app.*         → Cross-cutting concerns (types, wrappers, utilities)
{entity}.*    → Domain-specific business logic
mutation_metadata.* → FraiseQL type metadata
```

---

## 🔧 Additional Shared Utilities (Future)

Once established, `app.*` can host other shared utilities:

### **Error Response Builder**
```sql
CREATE FUNCTION app.build_error_response(
    p_error_code TEXT,
    p_message TEXT,
    p_details JSONB DEFAULT NULL
) RETURNS app.mutation_result
AS $$
BEGIN
    RETURN ROW(
        '00000000-0000-0000-0000-000000000000'::UUID,
        ARRAY[]::TEXT[],
        p_error_code,
        p_message,
        NULL::JSONB,
        COALESCE(p_details, '{}'::jsonb)
    )::app.mutation_result;
END;
$$ LANGUAGE plpgsql;
```

### **Event Emitter**
```sql
CREATE FUNCTION app.emit_event(
    p_tenant_id UUID,
    p_event_type TEXT,
    p_payload JSONB
) RETURNS VOID
AS $$
BEGIN
    INSERT INTO app.tb_event_log (tenant_id, event_type, payload, timestamp)
    VALUES (p_tenant_id, p_event_type, p_payload, now());
END;
$$ LANGUAGE plpgsql;
```

### **Audit Logger**
```sql
CREATE FUNCTION app.log_mutation(
    p_tenant_id UUID,
    p_user_id UUID,
    p_entity TEXT,
    p_entity_id UUID,
    p_operation TEXT,
    p_changed_fields TEXT[],
    p_old_data JSONB,
    p_new_data JSONB
) RETURNS VOID
AS $$
BEGIN
    INSERT INTO app.tb_mutation_audit (...)
    VALUES (...);
END;
$$ LANGUAGE plpgsql;
```

---

## 📝 Template Updates Required

### **Core Function Templates**

All templates must use `app.log_and_return_mutation`:

```diff
 -- templates/sql/core_create_function.sql.j2

     IF {{ validation.check }} THEN
-        RETURN {{ entity.schema }}.log_and_return_mutation(
+        RETURN app.log_and_return_mutation(
             auth_tenant_id,
             auth_user_id,
             ...
         );
     END IF;

     -- Success response
-    RETURN {{ entity.schema }}.log_and_return_mutation(
+    RETURN app.log_and_return_mutation(
         auth_tenant_id,
         auth_user_id,
         ...
     );
```

Same for:
- `templates/sql/core_update_function.sql.j2`
- `templates/sql/core_delete_function.sql.j2`

---

## 🎯 Team B Deliverable

**Team B should generate ONE shared utility function**:

```sql
-- Migration: 001_app_schema.sql
-- Generated by Team B ONCE (not per entity)

CREATE SCHEMA IF NOT EXISTS app;

-- Mutation result type (already planned)
CREATE TYPE app.mutation_result AS (...);

-- Shared utility function (NEW)
CREATE OR REPLACE FUNCTION app.log_and_return_mutation(
    p_tenant_id UUID,
    p_user_id UUID,
    p_entity TEXT,
    p_entity_id UUID,
    p_operation TEXT,
    p_status TEXT,
    p_updated_fields TEXT[],
    p_message TEXT,
    p_object_data JSONB,
    p_extra_metadata JSONB DEFAULT NULL
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_result app.mutation_result;
BEGIN
    -- Build standardized result
    v_result.id := p_entity_id;
    v_result.updated_fields := p_updated_fields;
    v_result.status := p_status;
    v_result.message := p_message;
    v_result.object_data := p_object_data;
    v_result.extra_metadata := COALESCE(p_extra_metadata, '{}'::jsonb);

    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION app.log_and_return_mutation IS
  '@fraiseql:utility Used by mutations to build standardized responses';
```

**Location**: Should be in the **base app schema migration**, not entity-specific migrations.

---

## ✅ Decision Summary

| Aspect | Decision |
|--------|----------|
| **Schema** | `app.*` (application layer) |
| **Function Name** | `app.log_and_return_mutation` |
| **Ownership** | Team B generates once in base migration |
| **Usage** | All business schemas call this shared utility |
| **Benefit** | Single source of truth, no duplication |

---

## 🚀 Implementation Impact

### **Team B** (Schema Generator)
- ✅ Generate `app.log_and_return_mutation()` in base app schema
- ✅ Include in `migrations/000_app_foundation.sql` (before entity migrations)
- ✅ Document as shared utility

### **Team C** (Action Compiler)
- ✅ Update templates to call `app.log_and_return_mutation(...)`
- ✅ **NOT** `{entity.schema}.log_and_return_mutation(...)`
- ✅ All validations, errors, and success responses use this utility

### **Team E** (CLI)
- ✅ Ensure `app.*` foundation is generated before entity migrations
- ✅ Order: `000_app_foundation.sql` → `001_contact.sql` → ...

---

## 📚 Reference Architecture

```
Migration Order:
├── 000_app_foundation.sql
│   ├── CREATE SCHEMA app
│   ├── CREATE TYPE app.mutation_result
│   ├── CREATE FUNCTION app.log_and_return_mutation()  ✅
│   └── (Other shared utilities)
│
├── 001_mutation_metadata.sql
│   ├── CREATE SCHEMA mutation_metadata
│   └── CREATE TYPE mutation_metadata.* (FraiseQL types)
│
├── 100_crm_contact.sql
│   ├── CREATE TABLE crm.tb_contact
│   ├── CREATE FUNCTION crm.contact_pk()
│   ├── CREATE FUNCTION crm.create_contact()  → calls app.log_and_return_mutation()
│   └── CREATE FUNCTION crm.update_contact()  → calls app.log_and_return_mutation()
│
└── 200_management_company.sql
    ├── CREATE TABLE management.tb_company
    ├── CREATE FUNCTION management.company_pk()
    └── CREATE FUNCTION management.create_company()  → calls app.log_and_return_mutation()
```

---

**Decision**: Use `app.log_and_return_mutation()` as a shared utility function.

**Status**: Ready for implementation
**Priority**: Must update before Team C starts
**Impact**: Cleaner architecture, easier maintenance, no code duplication

---

**Last Updated**: 2025-11-08
**Approved By**: Architecture Review
