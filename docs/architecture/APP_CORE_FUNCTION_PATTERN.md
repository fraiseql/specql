# App/Core Function Pattern - Architecture Decision

**Date**: 2025-11-08
**Status**: ✅ **RECOMMENDED APPROACH**
**Source**: Existing PrintOptim Backend Pattern

---

## 🎯 Pattern Overview

Based on `../printoptim_backend/db/0_schema/03_functions/`, the architecture uses a **two-layer function pattern**:

1. **`app.*` schema** - API wrapper functions (thin, handles type conversion)
2. **`core.*` schema** - Business logic functions (thick, contains all logic)

---

## 📐 Architecture Pattern

### Example: Create Reservation

**File**: `035_scd/03502_reservation/035021_create_reservation.sql`

```sql
-- ============================================================================
-- LAYER 1: APP WRAPPER (API Entry Point)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create_reservation(
    auth_tenant_id UUID,              -- Tenant context
    auth_user_id UUID,                -- User context
    input_payload JSONB               -- Raw API input (GraphQL/REST)
) RETURNS app.mutation_result         -- Standard response
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_reservation_input;  -- Typed structure
BEGIN
    -- Convert JSONB → Custom Type
    input_data := jsonb_populate_record(
        NULL::app.type_reservation_input,
        input_payload
    );

    -- Delegate to core logic
    RETURN core.create_reservation(
        auth_tenant_id,
        input_data,          -- ✅ Typed input
        input_payload,       -- Original for audit
        auth_user_id
    );
END;
$$;


-- ============================================================================
-- LAYER 2: CORE LOGIC (Business Rules)
-- ============================================================================
CREATE OR REPLACE FUNCTION core.create_reservation(
    auth_tenant_id UUID,
    input_data app.type_reservation_input,  -- ✅ Typed input
    input_payload JSONB,                     -- Original for audit
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID := gen_random_uuid();
    v_status TEXT;
    v_message TEXT;
    -- ... business logic variables ...
BEGIN
    -- === INPUT VALIDATION ===
    IF input_data.machine_id IS NULL THEN
        RETURN core.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'allocation',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'failed:missing_machine_id',
            ARRAY['machine_id']::TEXT[],
            'Machine ID is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_machine_id_null')
        );
    END IF;

    -- Check machine exists
    IF NOT EXISTS (
        SELECT 1 FROM public.tv_machine
        WHERE id = input_data.machine_id
          AND tenant_id = input_pk_organization
    ) THEN
        RETURN core.log_and_return_mutation(...'failed:machine_not_found'...);
    END IF;

    -- === BUSINESS LOGIC ===
    INSERT INTO public.tb_allocation (
        id,
        tenant_id,
        fk_machine,
        reserved_from,
        reserved_until,
        ...
    ) VALUES (
        v_id,
        auth_tenant_id,
        input_data.machine_id,
        COALESCE(input_data.reserved_from, CURRENT_DATE + INTERVAL '1 year'),
        COALESCE(input_data.reserved_until, '2099-12-31'::DATE),
        ...
    );

    -- === AUDIT & RETURN ===
    RETURN core.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'allocation',
        v_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Reservation created successfully',
        row_to_json(...)::JSONB,
        NULL
    );
END;
$$;
```

---

## 🎯 Why This Pattern is EXCELLENT

### 1. **Clear Separation of Concerns**

| Layer | Responsibility | Changes When |
|-------|----------------|--------------|
| **`app.*`** | API contract, type conversion | API format changes (GraphQL→REST) |
| **`core.*`** | Business logic, validation | Business rules change |

**Benefit**: Change API layer without touching business logic

---

### 2. **FraiseQL Perfect Integration** ✅

```sql
-- FraiseQL introspects app.* layer
COMMENT ON FUNCTION app.create_reservation IS
  '@fraiseql:mutation name=createReservation,input=ReservationInput,output=MutationResult';

COMMENT ON TYPE app.type_reservation_input IS
  '@fraiseql:input name=ReservationInput';
```

**FraiseQL auto-generates**:
```graphql
input ReservationInput {
  machineId: UUID!
  reservedFrom: Date
  reservedUntil: Date
  organizationalUnitId: UUID
  # ... all fields from type_reservation_input
}

type Mutation {
  createReservation(input: ReservationInput!): MutationResult!
}
```

**Core layer is invisible to GraphQL** - pure business logic!

---

### 3. **Type Safety Throughout**

```sql
-- Input types (app.type_*_input)
CREATE TYPE app.type_reservation_input AS (
    machine_id UUID,
    reserved_from DATE,
    reserved_until DATE,
    organizational_unit_id UUID,
    location_id UUID,
    is_provisionnal BOOLEAN
);

-- Output types (app.mutation_result)
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,              -- 'success', 'failed:*', 'warning:*'
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB
);
```

**Benefits**:
- ✅ PostgreSQL validates types before execution
- ✅ IDE autocomplete for all fields
- ✅ FraiseQL generates exact GraphQL types
- ✅ No manual JSONB extraction in core logic

---

### 4. **Audit Trail Built-In**

```sql
-- App layer preserves original input
RETURN core.create_reservation(
    input_pk_organization,
    input_data,          -- Parsed typed input
    input_payload,       -- ✅ Original JSONB for audit!
    input_created_by
);

-- Core layer logs everything
RETURN core.log_and_return_mutation(
    input_pk_organization,
    input_created_by,
    v_entity,
    v_id,
    v_op,                    -- 'INSERT', 'UPDATE', 'DELETE', 'NOOP'
    v_status,                -- 'success', 'failed:*'
    v_updated_fields,        -- Which fields changed
    v_message,
    v_object_data,           -- Final state
    v_extra_metadata         -- Debug info
);
```

**Result**: Complete audit trail of every mutation

---

### 5. **Testability**

```sql
-- Test core logic directly (no API noise)
SELECT core.create_reservation(
    'tenant-uuid'::UUID,
    ROW('machine-uuid', '2025-01-01', '2025-12-31', NULL, NULL, FALSE)::app.type_reservation_input,
    '{}'::JSONB,
    'user-uuid'::UUID
);

-- Test app wrapper separately
SELECT app.create_reservation(
    'tenant-uuid'::UUID,
    'user-uuid'::UUID,
    '{"machine_id": "..."}'::JSONB
);
```

**Benefit**: Unit test business logic independent of API layer

---

### 6. **Multiple API Frontends**

```sql
-- GraphQL frontend (FraiseQL)
app.create_reservation(tenant, user, graphql_input)

-- REST frontend (future)
app_rest.create_reservation_v1(tenant, user, rest_input)

-- gRPC frontend (future)
app_grpc.create_reservation(tenant, user, protobuf_input)

-- All call same core logic!
core.create_reservation(tenant, typed_data, audit_json, user)
```

**Benefit**: Add new API protocols without changing business logic

---

### 7. **Standard Return Types**

```sql
-- ALL mutations return the same structure
CREATE TYPE app.mutation_result AS (
    id UUID,              -- Created/updated entity ID
    updated_fields TEXT[],  -- For change tracking
    status TEXT,            -- 'success', 'failed:reason', 'warning:reason'
    message TEXT,           -- Human-readable message
    object_data JSONB,      -- Full entity state
    extra_metadata JSONB    -- Debug/context info
);
```

**Benefits**:
- ✅ Consistent error handling across all APIs
- ✅ FraiseQL generates predictable GraphQL types
- ✅ Frontend code can handle all mutations uniformly
- ✅ Easy to add instrumentation/monitoring

---

## 🏗️ Generator Implementation Strategy

### Team B: Schema Generator

**Generate Input Types**:
```python
# src/generators/types_generator.py

class TypesGenerator:
    def generate_input_type(self, entity: Entity, action: Action) -> str:
        """Generate app.type_{action_name}_input"""
        fields = self._gather_action_fields(entity, action)

        return f"""
CREATE TYPE app.type_{action.name}_input AS (
{self._format_fields(fields)}
);

COMMENT ON TYPE app.type_{action.name}_input IS
  '@fraiseql:input name={self._to_pascal_case(action.name)}Input';
"""
```

**Generate Common Output Type** (once):
```sql
-- Auto-generated once in 00_common/
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB
);

COMMENT ON TYPE app.mutation_result IS
  '@fraiseql:type name=MutationResult';
```

---

### Team C: Action Compiler

**Generate App Wrapper**:
```python
# src/generators/actions/app_wrapper_generator.py

class AppWrapperGenerator:
    def generate_app_wrapper(self, entity: Entity, action: Action) -> str:
        """Generate app.{action_name} wrapper function"""
        schema = entity.schema

        return f"""
CREATE OR REPLACE FUNCTION app.{action.name}(
    auth_tenant_id UUID,
    auth_user_id UUID,
    input_payload JSONB
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_{action.name}_input;
BEGIN
    -- Convert JSONB → Typed structure
    input_data := jsonb_populate_record(
        NULL::app.type_{action.name}_input,
        input_payload
    );

    -- Delegate to core logic
    RETURN {schema}.{action.name}(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
END;
$$;

COMMENT ON FUNCTION app.{action.name} IS
  '@fraiseql:mutation name={self._to_camel_case(action.name)},input={self._to_pascal_case(action.name)}Input,output=MutationResult';
"""
```

**Generate Core Logic**:
```python
# src/generators/actions/core_logic_generator.py

class CoreLogicGenerator:
    def generate_core_function(self, entity: Entity, action: Action) -> str:
        """Generate core.{action_name} with business logic"""
        schema = entity.schema
        entity_lower = entity.name.lower()

        return f"""
CREATE OR REPLACE FUNCTION {schema}.{action.name}(
    auth_tenant_id UUID,
    input_data app.type_{action.name}_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID := gen_random_uuid();
    v_entity TEXT := '{entity_lower}';
    v_status TEXT;
    v_message TEXT;
BEGIN
    -- === VALIDATION ===
    {self._compile_validation_steps(action.steps)}

    -- === BUSINESS LOGIC ===
    {self._compile_action_steps(entity, action.steps)}

    -- === AUDIT & RETURN ===
    RETURN {schema}.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        v_entity,
        v_id,
        'INSERT',  -- or 'UPDATE', 'DELETE'
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        '{entity.name} {action.name} completed successfully',
        row_to_json(...)::JSONB,
        NULL
    );
END;
$$;
"""
```

---

## 📊 Directory Structure

```
generated/
├── 00_common/
│   └── 004_input_types/
│       ├── 00402_type_mutation_result.sql     # ✅ Standard output type
│       └── 00403_type_deletion_input.sql      # ✅ Standard delete input
│
├── 032_crm/
│   ├── 00_types/
│   │   ├── 03201_type_create_contact_input.sql    # ✅ Input type
│   │   └── 03202_type_update_contact_input.sql
│   │
│   ├── 03_functions/
│   │   └── 03201_contact/
│   │       ├── 0320101_create_contact.sql         # ✅ app + core functions
│   │       ├── 0320102_update_contact.sql
│   │       └── 0320103_delete_contact.sql
│   │
│   └── 04_fraiseql/
│       └── 03201_contact_metadata.sql             # ✅ FraiseQL annotations
```

---

## 🎯 Benefits Summary

| Benefit | App/Core Pattern | JSONB Only |
|---------|------------------|------------|
| **FraiseQL Auto-Discovery** | ✅ **Perfect** | ❌ Manual annotations |
| **Type Safety** | ✅ **Database level** | ❌ Runtime only |
| **API Flexibility** | ✅ **Multiple frontends** | ❌ Tied to one API |
| **Testability** | ✅ **Easy unit tests** | ⚠️ Harder to isolate |
| **Code Clarity** | ✅ **Thin wrapper + clean logic** | ❌ Mixed concerns |
| **Audit Trail** | ✅ **Built-in** | ⚠️ Manual |
| **Error Messages** | ✅ **Consistent** | ❌ Ad-hoc |
| **Performance** | ✅ **Native types** | ⚠️ JSONB parsing |
| **IDE Support** | ✅ **Autocomplete** | ❌ No schema |
| **Migration Safety** | ✅ **Type checks** | ❌ Silent failures |

---

## ✅ Recommendation: ADOPT APP/CORE PATTERN

### Why This is Perfect for SpecQL

1. **FraiseQL Integration**: Type introspection works perfectly
2. **Clean Separation**: Business logic (core) separate from API (app)
3. **Proven Pattern**: Already working in production (printoptim_backend)
4. **Type Safety**: PostgreSQL validates before execution
5. **Multi-API**: Support GraphQL, REST, gRPC with same core
6. **Audit Built-In**: Complete mutation tracking
7. **Testable**: Core logic testable without API noise

---

## 📋 Implementation Checklist

### Team B (Schema Generator)
- [ ] Generate `app.type_{action}_input` custom types
- [ ] Generate standard `app.mutation_result` type (once)
- [ ] Add FraiseQL comments to types
- [ ] Document type→GraphQL mapping

### Team C (Action Compiler)
- [ ] Generate `app.{action}` wrapper functions
- [ ] Generate `core.{action}` business logic functions
- [ ] Compile SpecQL steps → PL/pgSQL
- [ ] Add validation, audit, error handling
- [ ] Generate FraiseQL mutation comments

### Team D (FraiseQL Metadata)
- [ ] Annotate input types
- [ ] Annotate app wrapper functions
- [ ] Verify FraiseQL discovers types correctly

---

## 🎯 Next Steps

1. **Update generator design** to produce app/core layers
2. **Create type generator** (Team B)
3. **Update action compiler** (Team C) for two-layer output
4. **Test with FraiseQL** to verify auto-discovery

---

**Verdict**: ✅ **STRONGLY RECOMMENDED**

This pattern is **production-proven**, **FraiseQL-optimized**, and provides **excellent separation of concerns**. It's the right architecture for the SpecQL generator.

**Estimated Impact**: +2 days implementation, but **massive long-term benefits** for maintainability, API flexibility, and FraiseQL integration.
