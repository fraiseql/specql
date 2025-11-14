# Team B Action Required - Team C Coordination

**Date**: 2025-11-08
**Priority**: 🔴 **CRITICAL BLOCKER**
**Blocking**: Team C integration testing and production deployment
**Effort**: 1 day (Team B work)

---

## 🚨 Critical Issue

Team C has completed 85% of the action compiler implementation (78 tests passing, 3,348 lines of code) but is **blocked** because Team B has not yet generated the `app.log_and_return_mutation()` helper function that all Team C generated code depends on.

---

## 📋 What Team B Needs to Provide

### 1. Helper Function: `app.log_and_return_mutation()`

**Location**: `migrations/000_app_foundation.sql`
**Schema**: `app`
**Purpose**: Audit logging and standardized mutation result builder

```sql
-- ============================================================================
-- REQUIRED BY TEAM C: Audit Logger and Mutation Result Builder
-- This function is called by ALL app/core functions for:
--   - Success responses
--   - Validation errors
--   - FK resolution errors
--   - Audit trail logging
-- ============================================================================

CREATE OR REPLACE FUNCTION app.log_and_return_mutation(
    -- JWT Context
    p_tenant_id UUID,              -- From auth.tenant_id
    p_user_id UUID,                -- From auth.user_id

    -- Mutation Identity
    p_entity TEXT,                 -- 'contact', 'company', etc.
    p_entity_id UUID,              -- UUID of affected entity
    p_operation TEXT,              -- 'INSERT', 'UPDATE', 'DELETE', 'NOOP'

    -- Result Details
    p_status TEXT,                 -- 'success', 'failed:*'
    p_updated_fields TEXT[],       -- ['email', 'status']
    p_message TEXT,                -- User-facing message

    -- Response Data
    p_object_data JSONB,           -- Full entity object (for success)
    p_extra_metadata JSONB DEFAULT NULL,  -- Side effects, impacts
    p_error_context JSONB DEFAULT NULL    -- Error details (for failures)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_audit_id UUID := gen_random_uuid();
BEGIN
    -- Log to audit table (for compliance, debugging, analytics)
    INSERT INTO app.tb_mutation_audit_log (
        id,
        tenant_id,
        user_id,
        entity_type,
        entity_id,
        operation,
        status,
        updated_fields,
        message,
        object_data,
        extra_metadata,
        error_context,
        created_at
    ) VALUES (
        v_audit_id,
        p_tenant_id,
        p_user_id,
        p_entity,
        p_entity_id,
        p_operation,
        p_status,
        p_updated_fields,
        p_message,
        p_object_data,
        p_extra_metadata,
        p_error_context,
        now()
    );

    -- Return standardized mutation result (FraiseQL compatible)
    RETURN ROW(
        p_entity_id,
        p_updated_fields,
        p_status,
        p_message,
        p_object_data,
        p_extra_metadata
    )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.log_and_return_mutation IS
  'Audit logger and standardized mutation result builder. Used by all app/core functions to ensure consistent audit trail and response format. Required by Team C generated functions.';
```

---

### 2. Audit Log Table: `app.tb_mutation_audit_log`

**Location**: `migrations/000_app_foundation.sql`
**Purpose**: Store complete audit trail of all mutations

```sql
-- ============================================================================
-- AUDIT LOG TABLE
-- Stores complete history of all mutations (success and failures)
-- Used for: compliance, debugging, analytics, security
-- ============================================================================

CREATE TABLE app.tb_mutation_audit_log (
    -- Primary Key
    id UUID PRIMARY KEY,

    -- Multi-Tenancy
    tenant_id UUID NOT NULL,

    -- User Context
    user_id UUID NOT NULL,

    -- Mutation Identity
    entity_type TEXT NOT NULL,     -- 'contact', 'company', 'order', etc.
    entity_id UUID NOT NULL,       -- UUID of affected entity

    -- Operation Details
    operation TEXT NOT NULL,       -- 'INSERT', 'UPDATE', 'DELETE', 'NOOP'
    status TEXT NOT NULL,          -- 'success', 'failed:validation', 'failed:not_found', etc.
    updated_fields TEXT[],         -- Which fields were changed

    -- Response Data
    message TEXT,                  -- User-facing message
    object_data JSONB,             -- Full entity object (for success)
    extra_metadata JSONB,          -- Side effects, impact metadata
    error_context JSONB,           -- Error details (for failures)

    -- Audit Trail
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX idx_audit_tenant_time ON app.tb_mutation_audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_entity ON app.tb_mutation_audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_user ON app.tb_mutation_audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_status ON app.tb_mutation_audit_log(status, created_at DESC);
CREATE INDEX idx_audit_operation ON app.tb_mutation_audit_log(operation, created_at DESC);

-- Optional: Partial index for failures only (for monitoring)
CREATE INDEX idx_audit_failures ON app.tb_mutation_audit_log(tenant_id, created_at DESC)
WHERE status LIKE 'failed:%';

COMMENT ON TABLE app.tb_mutation_audit_log IS
  'Complete audit trail of all mutations. Provides compliance, debugging, and analytics capabilities.';
```

---

## 🔍 Why This Is Critical

### Team C Usage Pattern

Every single function generated by Team C calls `app.log_and_return_mutation()`:

**Example - Success Response**:
```sql
-- Core CREATE function (Team C generates this)
CREATE OR REPLACE FUNCTION crm.create_contact(...)
RETURNS app.mutation_result
AS $$
BEGIN
    -- ... business logic ...

    INSERT INTO crm.tb_contact (...) VALUES (...);

    -- ✅ Team C calls app.log_and_return_mutation() here
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

**Example - Validation Error**:
```sql
-- Core CREATE function with validation (Team C generates this)
BEGIN
    IF input_data.email IS NULL THEN
        -- ✅ Team C calls app.log_and_return_mutation() for errors too
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
            NULL,
            jsonb_build_object('reason', 'validation_email_null')
        );
    END IF;
    ...
END;
```

**Without This Function**:
- ❌ All Team C generated SQL will fail with "function app.log_and_return_mutation does not exist"
- ❌ Cannot run integration tests
- ❌ Cannot deploy to database
- ❌ No audit trail
- ❌ Blocks Team C from moving to production

---

## 📊 Impact Analysis

### What Works Now
- ✅ Team C code compiles and generates correct SQL
- ✅ All 78 Team C tests pass (mocked database)
- ✅ Templates are correct and reference the right function signature

### What's Blocked
- ❌ **Database integration tests** - Cannot execute generated SQL
- ❌ **End-to-end testing** - SQL fails when applied to database
- ❌ **Production deployment** - Missing critical dependency
- ❌ **Team D integration** - FraiseQL can't test with broken SQL
- ❌ **Team E integration** - CLI can't generate working migrations

### Timeline Impact
- **If added today**: Team C can complete integration testing this week
- **If delayed 1 week**: Team C blocked, 2-3 week delay to production
- **If not added**: Complete redesign required (4+ weeks)

---

## ✅ Acceptance Criteria

Team C will verify the following after Team B delivers:

### 1. Function Signature Validation
```bash
# Connect to test database
psql test_db

# Verify function exists
\df app.log_and_return_mutation

# Expected output:
#  Schema | Name                     | Result data type      | Argument data types
# --------+--------------------------+-----------------------+---------------------
#  app    | log_and_return_mutation  | app.mutation_result   | p_tenant_id uuid, ...
```

### 2. Return Type Validation
```sql
-- Verify return type matches app.mutation_result
SELECT pg_get_function_result('app.log_and_return_mutation'::regproc);

-- Expected: app.mutation_result
```

### 3. Audit Table Exists
```sql
-- Verify table structure
\d app.tb_mutation_audit_log

-- Expected columns:
-- id, tenant_id, user_id, entity_type, entity_id, operation, status,
-- updated_fields, message, object_data, extra_metadata, error_context, created_at
```

### 4. Indexes Exist
```sql
-- Verify indexes
\di app.idx_audit_*

-- Expected:
-- idx_audit_tenant_time, idx_audit_entity, idx_audit_user,
-- idx_audit_status, idx_audit_operation, idx_audit_failures
```

### 5. Functional Test
```sql
-- Call function and verify it works
SELECT app.log_and_return_mutation(
    'test-tenant-id'::UUID,
    'test-user-id'::UUID,
    'test_entity',
    gen_random_uuid(),
    'INSERT',
    'success',
    ARRAY['field1', 'field2']::TEXT[],
    'Test message',
    '{"key": "value"}'::JSONB,
    NULL,
    NULL
);

-- Expected: Returns app.mutation_result composite type
-- Verify: Row inserted into app.tb_mutation_audit_log
```

---

## 🗓️ Proposed Timeline

### Day 1 (Today - 2 hours)
- [ ] Team B reviews this specification
- [ ] Team B asks any clarification questions
- [ ] Team B and Team C align on signature

### Day 2 (Tomorrow - 4 hours)
- [ ] Team B adds function to `000_app_foundation.sql`
- [ ] Team B adds audit table to `000_app_foundation.sql`
- [ ] Team B runs migration on test database
- [ ] Team B notifies Team C: "Ready for testing"

### Day 3 (Day After - 1 hour)
- [ ] Team C runs acceptance tests (above)
- [ ] Team C runs first database roundtrip test
- [ ] Team C provides feedback (if any issues)
- [ ] **BLOCKER RESOLVED** ✅

---

## 📞 Coordination

### Team B Contact
**Lead**: [To be assigned]
**Channel**: #team-b-schema-generator
**Priority**: 🔴 CRITICAL BLOCKER

### Team C Contact
**Lead**: [To be assigned]
**Channel**: #team-c-action-compiler
**Availability**: Immediate for questions

### Questions to Resolve
1. ❓ Should `error_context` be separate parameter or part of `extra_metadata`?
   - **Team C Preference**: Separate (clearer semantics)
   - **Decision**: Team B to confirm

2. ❓ Should audit log have retention policy?
   - **Suggestion**: Partition by month, retain 12 months
   - **Decision**: Can be added later (not blocking)

3. ❓ Should we capture execution time?
   - **Suggestion**: Add `execution_time_ms INTEGER` column
   - **Decision**: Nice to have, not blocking

---

## 🔗 Related Documents

1. **Team C Full Plan**: `docs/implementation-plans/TEAM_C_REMAINING_WORK_PLAN.md`
2. **App/Core Pattern**: `docs/architecture/APP_CORE_FUNCTION_PATTERN.md`
3. **Team C Implementation Plan**: `docs/implementation-plans/TEAM_C_APP_CORE_FUNCTIONS_PLAN.md`

---

## 📝 Notes

### Why Not Generate This in Team C?

**Q**: Why can't Team C just add this function themselves?

**A**: Because it belongs in the `app` schema foundation layer:
- Used by **all** entities (Contact, Company, Order, Machine, etc.)
- Should be created **once** in `000_app_foundation.sql`
- Team B owns the `app` schema foundation
- Team C generates entity-specific functions that **use** app.log_and_return_mutation()

**Analogy**: Team B builds the foundation (app.mutation_result, app.log_and_return_mutation), Team C builds the house on top (crm.create_contact, management.create_company).

### Alternative (Not Recommended)

If Team B is blocked, Team C could:
1. Create a temporary `001_team_c_helpers.sql` with this function
2. Continue integration testing
3. Move to Team B's migration later

**Why Not Recommended**:
- Creates migration ordering issues
- Duplicates responsibility
- Harder to maintain
- Team B should own `app` schema

---

**Created**: 2025-11-08
**Urgency**: 🔴 **CRITICAL** - Blocking Team C production readiness
**Expected Resolution**: 1-2 days
**Status**: ⏸️ **WAITING ON TEAM B**
