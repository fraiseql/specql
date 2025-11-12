# CTO Review: Team B Implementation Plan - App/Core Schema Pattern

**Reviewer**: CTO
**Date**: 2025-11-08
**Document**: `docs/implementation-plans/TEAM_B_APP_CORE_SCHEMA_PLAN.md`
**Status**: 🔴 **CONCERNS IDENTIFIED - Requires Revisions**

---

## 📋 Executive Summary

**Overall Assessment**: ⚠️ **GOOD FOUNDATION, BUT CRITICAL GAPS**

The Team B plan demonstrates strong understanding of the app/core pattern and FraiseQL integration requirements. However, there are several **architectural concerns** and **missing requirements** that must be addressed before implementation begins.

**Recommendation**: 🔴 **DO NOT PROCEED** without addressing the issues below.

---

## 🔑 Key Pattern: JWT Context + Denormalized Multi-Tenancy

**CRITICAL UNDERSTANDING**:

```
┌──────────────────────────────────────────────────────────────┐
│ Security Context (JWT Token - Server Enforced)              │
├──────────────────────────────────────────────────────────────┤
│ • tenant_id: "tenant-uuid"  → Database: tenant_id UUID       │
│ • sub: "user-uuid"          → Database: created_by UUID      │
│ • NEVER in composite types (security!)                       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Business Data (User Input - Validated)                       │
├──────────────────────────────────────────────────────────────┤
│ • organization_id UUID      → Database: fk_organization INT  │
│ • company_id UUID           → Database: fk_company INT       │
│ • email TEXT                → Database: email TEXT           │
│ • IN composite types (user provides)                         │
└──────────────────────────────────────────────────────────────┘

Table Structure:
┌──────────────────────────────────────────────────────────────┐
│ CREATE TABLE crm.tb_contact (                                │
│   -- Trinity Pattern                                         │
│   pk_contact INTEGER PRIMARY KEY,                            │
│   id UUID UNIQUE,                                            │
│   identifier TEXT UNIQUE,                                    │
│                                                              │
│   -- SECURITY: Denormalized from JWT (ALWAYS)               │
│   tenant_id UUID NOT NULL,  ← FROM JWT, NOT user input!    │
│                                                              │
│   -- BUSINESS: Optional FK (domain-specific)                 │
│   fk_organization INTEGER,  ← FROM user input (optional)    │
│                                                              │
│   -- BUSINESS: User data                                     │
│   email TEXT,                                                │
│   fk_company INTEGER,                                        │
│                                                              │
│   -- AUDIT: From JWT                                         │
│   created_by UUID,          ← FROM JWT "sub"                │
│   updated_by UUID,          ← FROM JWT "sub"                │
│   deleted_by UUID                                            │
│ );                                                           │
│                                                              │
│ -- CRITICAL: Index on denormalized tenant_id                │
│ CREATE INDEX idx_contact_tenant ON tb_contact(tenant_id);   │
└──────────────────────────────────────────────────────────────┘
```

**Why Denormalize `tenant_id`?**
- ⚡ **Performance**: Fast filtering without JOINs
- 🔒 **RLS**: Simple row-level security policies
- 🛠️ **Utility**: Easy filtering in helper functions

---

## 🗂️ Schema Organization: Tenant vs. Common Data

**CRITICAL DISTINCTION**:

```
┌──────────────────────────────────────────────────────────────┐
│ TENANT-SPECIFIC SCHEMAS (Multi-tenant data)                 │
├──────────────────────────────────────────────────────────────┤
│ • tenant.*         - Tenant business data                    │
│ • crm.*            - Customer relationship management        │
│ • management.*     - Organization/hierarchy                  │
│ • operations.*     - Operational data                        │
│                                                              │
│ ALL tables in these schemas MUST have:                       │
│ ✅ tenant_id UUID NOT NULL                                   │
│ ✅ INDEX on tenant_id                                        │
│ ✅ RLS policies for tenant isolation                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ COMMON/CATALOG SCHEMAS (Shared across all tenants)          │
├──────────────────────────────────────────────────────────────┤
│ • common.*         - Shared reference data                   │
│ • catalog.*        - Product catalogs, SKUs                  │
│ • public.*         - PostgreSQL default (avoid using)        │
│                                                              │
│ Tables in these schemas:                                     │
│ ❌ NO tenant_id (data is shared!)                            │
│ ❌ NO tenant-specific RLS                                    │
│ ✅ Read-only or admin-only access                            │
│                                                              │
│ Examples:                                                    │
│ • common.tb_country (list of countries)                      │
│ • catalog.tb_product_category (global categories)           │
│ • common.tb_currency (currency definitions)                 │
└──────────────────────────────────────────────────────────────┘
```

**Team B Implementation Impact**:

1. **Schema Detection Strategy**:
   ```python
   # In TableGenerator
   TENANT_SCHEMAS = ['tenant', 'crm', 'management', 'operations']
   COMMON_SCHEMAS = ['common', 'catalog', 'public']

   def generate_table_ddl(self, entity: Entity) -> str:
       is_tenant_specific = entity.schema in TENANT_SCHEMAS

       if is_tenant_specific:
           # ✅ Add tenant_id, RLS policies
           context['multi_tenant'] = True
       else:
           # ❌ Skip tenant_id, no RLS
           context['multi_tenant'] = False
   ```

2. **Conditional Fields**:
   ```sql
   -- Tenant-specific table (crm.tb_contact):
   CREATE TABLE crm.tb_contact (
       pk_contact INTEGER PRIMARY KEY,
       id UUID UNIQUE,
       tenant_id UUID NOT NULL,  -- ✅ Required
       ...
   );

   -- Common table (common.tb_country):
   CREATE TABLE common.tb_country (
       pk_country INTEGER PRIMARY KEY,
       id UUID UNIQUE,
       -- ❌ NO tenant_id
       code TEXT UNIQUE,
       name TEXT,
       ...
   );
   ```

3. **Index Generation**:
   ```python
   def generate_indexes_ddl(self, entity: Entity) -> str:
       indexes = []

       # Always index UUID
       indexes.append(f"CREATE INDEX idx_{entity.name}_id ...")

       # Only add tenant_id index for tenant-specific schemas
       if entity.schema in TENANT_SCHEMAS:
           indexes.append(f"CREATE INDEX idx_{entity.name}_tenant ON {entity.schema}.tb_{entity.name}(tenant_id);")
   ```

**Action Required**:
1. Add schema classification logic to `TableGenerator`
2. Document which schemas are tenant-specific vs. common
3. Make `tenant_id` conditional based on schema
4. Update tests for both patterns

---

## ✅ Strengths

### 1. **Clear UUID vs INTEGER Separation** ✅
The plan correctly identifies that:
- Composite types use **UUID** for external API
- Database tables use **INTEGER** for internal FKs
- Resolution happens in core layer

**Evidence**: Lines 37-84 clearly document this critical architectural decision.

### 2. **FraiseQL Integration Well Understood** ✅
The plan demonstrates excellent understanding of:
- Composite type field comments work (verified with PostgreSQL test)
- `@fraiseql:input` annotations
- Field-level metadata via `COMMENT ON COLUMN`

**Evidence**: Phase 4 (lines 646-689) shows proper FraiseQL annotation strategy.

### 3. **TDD Discipline** ✅
Follows RED → GREEN → REFACTOR → QA cycle consistently.

**Evidence**: All 4 phases follow proper TDD methodology.

### 4. **Team C Coordination** ✅
Clear interface contract defined for handoff to Team C.

**Evidence**: Lines 713-739 document exactly what Team B provides.

---

## 🔴 Critical Issues

### **Issue #1: Missing Multi-Tenancy Pattern (JWT Context + Denormalized tenant_id)**

**Severity**: 🔴 **CRITICAL**

**Problem**: The composite types and table schema don't implement the full multi-tenancy pattern with JWT token context and denormalized `tenant_id`.

**Current Plan** (Line 94-97):
```sql
CREATE TYPE app.type_create_contact_input AS (
    email TEXT,
    company_id UUID,
    status TEXT
);
```

**Database Table** (Line 118-127):
```sql
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER,
    id UUID,
    identifier TEXT,
    email TEXT,
    fk_company INTEGER,
    status TEXT,
    -- ❌ MISSING: tenant_id denormalization
    -- ❌ MISSING: fk_organization/fk_tenant
```

**Correct Multi-Tenancy Pattern**:

```sql
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    identifier TEXT UNIQUE,

    -- ✅ MULTI-TENANT CONTEXT (CRITICAL!)
    -- Denormalized for performance - extracted from JWT token
    tenant_id UUID NOT NULL,

    -- ✅ OPTIONAL: Explicit FK to organization/tenant table
    -- (Some tables have this, some don't - depends on domain model)
    fk_organization INTEGER,  -- References management.tb_organization(pk_organization)

    -- Business fields
    email TEXT,
    fk_company INTEGER,
    status TEXT,

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID,        -- From JWT token (sub claim)
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID,        -- From JWT token
    deleted_at TIMESTAMPTZ,
    deleted_by UUID
);

-- ✅ CRITICAL INDEX: tenant_id for filtering & RLS
CREATE INDEX idx_tb_contact_tenant ON crm.tb_contact(tenant_id);

-- ✅ If FK to organization exists, index it too
CREATE INDEX idx_tb_contact_organization ON crm.tb_contact(fk_organization);
```

**Why This Pattern?**

1. **JWT Token Context**:
   ```javascript
   // JWT payload contains:
   {
     "sub": "user-uuid",           // → created_by, updated_by
     "tenant_id": "tenant-uuid",   // → tenant_id column
     "organization_id": "org-uuid" // → fk_organization (if needed)
   }
   ```

2. **Denormalized `tenant_id`**:
   - **Performance**: Fast filtering without JOIN to organization table
   - **RLS (Row-Level Security)**: Direct comparison in policies
   - **Utility Functions**: Filter by tenant easily

   ```sql
   -- Fast query (uses index on tenant_id):
   SELECT * FROM crm.tb_contact
   WHERE tenant_id = current_setting('app.current_tenant_id')::UUID;

   -- Slow query (requires JOIN):
   SELECT c.* FROM crm.tb_contact c
   JOIN management.tb_organization o ON c.fk_organization = o.pk_organization
   WHERE o.id = current_setting('app.current_tenant_id')::UUID;
   ```

3. **Optional FK to Organization**:
   - **Some tables** have explicit `fk_organization` for business logic
   - **Some tables** only have `tenant_id` for isolation
   - Example: `tb_contact` might need `fk_organization` if contacts belong to specific org units
   - Example: `tb_system_config` only needs `tenant_id` for tenant isolation

**Core Layer Function Pattern**:

```sql
CREATE OR REPLACE FUNCTION crm.create_contact(
    input_pk_organization UUID,      -- From JWT: tenant_id
    input_data app.type_create_contact_input,
    input_payload JSONB,
    input_created_by UUID            -- From JWT: sub (user ID)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID := gen_random_uuid();
    v_fk_organization INTEGER;
BEGIN
    -- ✅ Resolve organization UUID → INTEGER (if table has FK)
    -- Note: Some tables won't have this step
    IF input_data.organization_id IS NOT NULL THEN
        v_fk_organization := management.organization_pk(input_data.organization_id);
    END IF;

    -- ✅ INSERT with JWT context
    INSERT INTO crm.tb_contact (
        id,
        tenant_id,              -- ✅ From JWT (denormalized)
        fk_organization,        -- ✅ From user input (if applicable)
        email,
        fk_company,
        status,
        created_at,
        created_by              -- ✅ From JWT
    ) VALUES (
        v_id,
        input_pk_organization,  -- ✅ JWT tenant_id → denormalized column
        v_fk_organization,      -- ✅ Business FK (may be NULL)
        input_data.email,
        crm.company_pk(input_data.company_id),
        input_data.status,
        now(),
        input_created_by        -- ✅ JWT user_id
    );

    RETURN crm.log_and_return_mutation(...);
END;
$$;
```

**Why Composite Types Don't Need tenant_id**:
- ✅ `tenant_id` comes from **JWT token** (via `input_pk_organization` parameter)
- ✅ **NOT** from user input (security - users can't fake their tenant!)
- ✅ App wrapper extracts from JWT and passes to core layer
- ✅ Core layer injects into INSERT

**Composite Type MAY Include organization_id (Business Logic)**:

```sql
-- If Contact belongs to specific organizational unit (business requirement)
CREATE TYPE app.type_create_contact_input AS (
    email TEXT,
    company_id UUID,
    organization_id UUID,     -- ✅ OPTIONAL: Business FK to org unit
    status TEXT
);
```

**Key Distinction**:
- **`tenant_id`**: Security/isolation context (from JWT, ALWAYS present, denormalized)
- **`fk_organization`**: Business relationship (from user input, OPTIONAL, depends on domain)

**Impact**:
- ❌ No tenant isolation → data leakage risk
- ❌ No RLS support → security vulnerability
- ❌ Slow queries → JOIN required for filtering
- ❌ Non-compliant with PrintOptim pattern

**Action Required**:
1. ✅ Add `tenant_id UUID NOT NULL` to ALL tables (denormalized)
2. ✅ Add `tenant_id` index for performance
3. ✅ Add `fk_organization INTEGER` to tables where business logic requires it
4. ✅ Document JWT token → database column mapping
5. ✅ Update app wrapper to extract JWT claims
6. ✅ Document which tables need `fk_organization` vs. only `tenant_id`

---

### **Issue #2: Missing Audit Fields in Table Generation**

**Severity**: 🔴 **CRITICAL**

**Problem**: The table example (line 118-127) shows minimal audit fields, but PrintOptim requires comprehensive audit trail.

**Current Plan**:
```sql
CREATE TABLE crm.tb_contact (
    ...
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**PrintOptim Reality** (from actual production schema):
```sql
CREATE TABLE crm.tb_contact (
    ...
    -- FULL AUDIT TRAIL (Required!)
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID,                      -- ✅ WHO created
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID,                      -- ✅ WHO updated
    deleted_at TIMESTAMPTZ,               -- ✅ Soft delete timestamp
    deleted_by UUID                       -- ✅ WHO deleted
);
```

**Impact**:
- ❌ No audit trail for compliance
- ❌ Can't track who made changes
- ❌ Soft delete not supported
- ❌ Non-compliant with enterprise requirements

**Action Required**:
1. Update `TableGenerator._prepare_template_context()` to include all audit fields
2. Add `created_by`, `updated_by`, `deleted_at`, `deleted_by` as standard
3. Document that these are NOT in composite types (injected by core layer)

---

### **Issue #3: Schema Assumption - Not Always `app`**

**Severity**: ⚠️ **MEDIUM**

**Problem**: Plan hardcodes composite types in `app` schema, but this may not be correct.

**Current Plan** (Line 261):
```python
type_name = f"type_{action.name}_input"
# Implicitly: app.type_create_contact_input
```

**Question**: What if action is in `crm` schema? Where should composite type go?

**PrintOptim Pattern** (from APP_CORE_FUNCTION_PATTERN.md):
- ✅ **App functions**: `app.create_organizational_unit()`
- ✅ **Core functions**: `core.create_organizational_unit()` (NOTE: `core`, not entity schema!)
- ✅ **Composite types**: `app.type_organizational_unit_input`

**Observation**: PrintOptim uses `core` schema for business logic, not entity schema (`crm`, `management`, etc.).

**Potential Issue**: SpecQL uses entity schema (`crm`, `management`). This differs from PrintOptim.

**Questions for Team**:
1. Should we follow PrintOptim's `app` + `core` pattern exactly?
2. Or use `app` + entity schema (e.g., `crm`, `management`)?
3. Do we need `core` schema at all, or is entity schema fine?

**Recommendation**:
- **Composite types**: Always `app` schema (public API contract) ✅
- **Core functions**: Need decision - `core` schema (PrintOptim) or entity schema (`crm`, `management`)?

**Action Required**:
1. Document schema strategy in architecture docs
2. Update Team C plan to match decision
3. Consider configurability if different projects have different conventions

---

### **Issue #4: Missing Trinity Helper Functions**

**Severity**: 🔴 **CRITICAL**

**Problem**: Plan doesn't include generation of `entity_pk()` and `entity_id()` helper functions.

**Current Plan**: ❌ No mention of helper functions

**PrintOptim Requires** (from APP_CORE_FUNCTION_PATTERN.md):
```sql
-- UUID → INTEGER (pk)
CREATE OR REPLACE FUNCTION crm.contact_pk(p_identifier TEXT)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_contact
    FROM crm.tb_contact
    WHERE id::TEXT = p_identifier
       OR identifier = p_identifier
       OR pk_contact::TEXT = p_identifier
    LIMIT 1;
$$;

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION crm.contact_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM crm.tb_contact WHERE pk_contact = p_pk;
$$;
```

**Impact**:
- ❌ Team C can't resolve UUID → INTEGER
- ❌ Core layer INSERT statements will fail
- ❌ Pattern incomplete

**Required in Team B Deliverables**:
1. `entity_pk(TEXT) → INTEGER` - Accepts UUID, identifier, or pk as text
2. `entity_id(INTEGER) → UUID` - Converts pk → UUID
3. Optional: `entity_identifier(INTEGER) → TEXT`

**Action Required**:
1. Add Phase 2.5: "Trinity Helper Function Generation"
2. Create `TrinityHelperGenerator` class
3. Generate for EVERY entity (part of schema generation)
4. Test that Team C can use these in INSERT statements

---

### **Issue #5: Field Naming Inconsistency**

**Severity**: ⚠️ **MEDIUM**

**Problem**: Field naming transformation is inconsistent and may cause confusion.

**Current Plan** (Line 340-348):
```python
if field_def.type == "ref":
    # ref fields: append "_id" for external API
    # "company" → "company_id"
    api_field_name = f"{field_name}_id"
else:
    # Regular fields: keep name as-is
    api_field_name = field_name
```

**Concern**: SpecQL field is `company`, but composite type field is `company_id`. GraphQL field will be `companyId`.

**Transformation Chain**:
```
SpecQL:           company: ref(Company)
↓
Composite Type:   company_id UUID
↓
GraphQL:          companyId: UUID
↓
Database Table:   fk_company INTEGER
```

**Question**: Is this mapping documented clearly enough for users?

**Potential Confusion**:
- User writes `company` in YAML
- GraphQL mutation needs `companyId`
- Database has `fk_company`
- Three different names for the same concept!

**Recommendation**:
1. ✅ Keep the convention (it's correct for GraphQL)
2. ⚠️ Document the transformation clearly in user-facing docs
3. ⚠️ Consider generating a mapping table for debugging

**Action Required**:
1. Add documentation section: "Field Name Transformations"
2. Include table showing SpecQL → Composite → GraphQL → Database
3. Generate comments in SQL explaining the mapping

---

### **Issue #6: Missing Validation Logic**

**Severity**: ⚠️ **MEDIUM**

**Problem**: No validation for edge cases and conflicts.

**Missing Validations**:

1. **Type name conflicts**: What if two actions generate same composite type name?
   ```python
   # action: create_contact → type_create_contact_input
   # action: create_contact_async → type_create_contact_async_input
   # What if user has both create_contact and update_contact?
   ```

2. **Reserved names**: What if user names field `id`, `pk`, or `tenant_id`?
   ```yaml
   fields:
     id: text  # ❌ Conflicts with Trinity pattern!
   ```

3. **Circular references**: What if Entity A refs Entity B, and B refs A?
   ```yaml
   # entities/user.yaml
   fields:
     team: ref(Team)

   # entities/team.yaml
   fields:
     owner: ref(User)  # Circular!
   ```

4. **Schema existence**: Does target schema exist before generating types?

**Action Required**:
1. Add validation phase before generation
2. Detect and error on reserved field names
3. Warn on potential circular dependencies
4. Validate schema existence

---

## ⚠️ Medium Priority Issues

### **Issue #7: Missing Enterprise Features**

**Severity**: ⚠️ **MEDIUM** (can be phased)

**Missing from Plan**:

1. **Row-Level Security (RLS)**:
   ```sql
   -- PrintOptim has RLS on all tables
   ALTER TABLE crm.tb_contact ENABLE ROW LEVEL SECURITY;

   CREATE POLICY tenant_isolation ON crm.tb_contact
   FOR ALL
   TO authenticated_user
   USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
   ```

2. **Partition Strategy**: For high-volume tables
   ```sql
   -- Partition by tenant_id for large tables?
   CREATE TABLE crm.tb_contact PARTITION BY LIST (tenant_id);
   ```

3. **Triggers**: Audit trail triggers, timestamp updates

4. **Constraints**: UNIQUE constraints, CHECK constraints beyond enums

**Recommendation**: Phase 2 features, but should be in roadmap.

**Action Required**:
1. Add "Future Enhancements" section to plan
2. Document RLS strategy for later implementation
3. Consider partitioning for scale

---

### **Issue #8: Template Organization**

**Severity**: 🟡 **LOW**

**Problem**: Template structure not fully specified.

**Current**: `templates/sql/composite_type.sql.j2`

**Needed**:
- `templates/sql/composite_type.sql.j2` ✅
- `templates/sql/trinity_helpers.sql.j2` ❌
- `templates/sql/table_with_audit.sql.j2` ❌ (update existing `table.sql.j2`)

**Action Required**:
1. Document complete template structure
2. Ensure templates handle all edge cases
3. Add template tests

---

## 💡 Recommendations

### **Recommendation #1: Add Schema Strategy Document**

Create: `docs/architecture/SCHEMA_STRATEGY.md`

**Contents**:
- Which schemas are used for what (`app`, `core`, entity schemas)
- Multi-tenancy strategy (tenant_id placement)
- Audit field requirements
- Security (RLS, policies)
- Naming conventions (comprehensive)

### **Recommendation #2: Expand Phase 2 to Include Trinity Helpers**

**Current**: Phase 2 only generates `mutation_result`

**Should Be**:
- Standard types (`mutation_result`)
- **Trinity helper functions** (`entity_pk`, `entity_id`)
- Standard deletion input type

### **Recommendation #3: Add Pre-Generation Validation Phase**

**Before** generating any SQL:
1. Validate entity names (no conflicts)
2. Validate field names (no reserved words)
3. Check schema exists
4. Detect circular refs
5. Validate action names (unique composite types)

### **Recommendation #4: Document Field Transformation Chain**

Add to plan:
```
SpecQL Field → Composite Type Field → GraphQL Field → Database Column

company      → company_id (UUID)    → companyId    → fk_company (INTEGER)
status       → status (TEXT)        → status       → status (TEXT)
created_at   → (not in composite)   → (hidden)     → created_at (TIMESTAMPTZ)
```

### **Recommendation #5: Consider Performance Implications**

**Question**: For entities with 50+ fields, should composite types include ALL fields?

**Optimization**:
- Create action could need all fields
- Update action might only need subset
- Delete action only needs ID

**Recommendation**: Support **action-specific field selection** in Phase 3.

---

## 📊 Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **Missing tenant_id** | 🔴 CRITICAL | HIGH | Add to table generator immediately |
| **Missing audit fields** | 🔴 CRITICAL | HIGH | Add `created_by`, `updated_by`, `deleted_at`, `deleted_by` |
| **Missing helper functions** | 🔴 CRITICAL | HIGH | Add Trinity helper generation to Phase 2 |
| **Schema confusion** | ⚠️ MEDIUM | MEDIUM | Document schema strategy clearly |
| **Field naming confusion** | ⚠️ MEDIUM | MEDIUM | Add comprehensive docs |
| **Type name conflicts** | ⚠️ MEDIUM | LOW | Add validation phase |
| **Missing RLS** | ⚠️ MEDIUM | LOW | Phase 2 feature |
| **Performance at scale** | 🟡 LOW | LOW | Monitor and optimize later |

---

## ✅ Required Changes Before Approval

### **Must-Have (Blocking)**:

1. ✅ Add `tenant_id UUID NOT NULL` to all tables
2. ✅ Add complete audit fields (`created_by`, `updated_by`, `deleted_at`, `deleted_by`)
3. ✅ Add Trinity helper function generation (`entity_pk`, `entity_id`)
4. ✅ Add tenant index: `CREATE INDEX idx_tb_{entity}_tenant ON {schema}.tb_{entity}(tenant_id)`
5. ✅ Document schema strategy (`app` vs entity schema for core functions)
6. ✅ Add field transformation documentation

### **Should-Have (Recommended)**:

1. ⚠️ Add validation phase (reserved names, conflicts)
2. ⚠️ Expand error handling for edge cases
3. ⚠️ Document future enterprise features (RLS, partitioning)

### **Nice-to-Have (Future)**:

1. 🟡 Action-specific field selection (optimization)
2. 🟡 Template organization documentation
3. 🟡 Performance testing plan

---

## 📝 Updated Deliverables List

### **Team B Must Deliver**:

1. ✅ `CompositeTypeGenerator` - Input types
2. ✅ `StandardTypesGenerator` - `mutation_result`, etc.
3. ✅ **`TrinityHelperGenerator`** - `entity_pk()`, `entity_id()` functions
4. ✅ `TableGenerator` (updated) - With `tenant_id` and full audit fields
5. ✅ `SchemaOrchestrator` - Coordinates all generators
6. ✅ Templates for all above
7. ✅ Comprehensive tests (90%+ coverage)
8. ✅ **Schema strategy documentation**
9. ✅ **Field transformation mapping documentation**

---

## 🎯 Verdict

**Status**: 🔴 **REVISE REQUIRED**

**Approval Conditions**:
1. Address all 🔴 CRITICAL issues (#1, #2, #4)
2. Document schema strategy (#3)
3. Add field naming documentation (#5)
4. Include validation strategy (#6)

**Estimated Time to Address**: +1-2 days

**Next Review**: After critical issues are addressed

---

## 💬 CTO Comments

**Positive**:
> "The team demonstrates excellent understanding of the app/core pattern and FraiseQL integration. The UUID vs INTEGER separation is handled correctly, and the TDD discipline is commendable."

**Concerns**:
> "Multi-tenancy is NOT OPTIONAL in enterprise systems. Every table must have `tenant_id` for data isolation. This is a security requirement, not a feature."

> "Trinity helper functions are the glue between app layer (UUID) and database layer (INTEGER). Without them, Team C will be blocked."

> "Audit trail is compliance requirement. We need to know WHO did WHAT and WHEN. Missing `created_by`, `updated_by`, `deleted_by` is unacceptable."

**Direction**:
> "Fix the critical issues first. Multi-tenancy, audit trail, and helper functions are foundational - they can't be added later without breaking changes. Get these right in Phase 1."

> "Schema strategy needs clarity. Are we following PrintOptim's `core` schema pattern, or using entity schemas? This affects Team C's work. Decide now, document clearly."

> "Once critical issues are resolved, this plan will be excellent. The foundation is solid - we just need to ensure it's complete."

---

## 📞 Next Steps

1. **Team B**: Address critical issues (#1, #2, #4)
2. **Architecture Team**: Document schema strategy
3. **Team B**: Add validation and field naming docs
4. **CTO**: Re-review updated plan
5. **Proceed**: Once approved, begin implementation

---

**Review Completed**: 2025-11-08
**Reviewer**: CTO
**Next Review Date**: TBD (after revisions submitted)

---

## Appendix A: JWT Token Pattern - Security vs Business Data

### **The Golden Rule**: Never Trust User Input for Security Context

```
┌─────────────────────────────────────────────────────────────┐
│  JWT Token (Verified by Auth Middleware)                   │
├─────────────────────────────────────────────────────────────┤
│  {                                                          │
│    "sub": "user-uuid-123",        ← WHO (authenticated)   │
│    "tenant_id": "tenant-uuid-456" ← WHERE (authorized)    │
│  }                                                          │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  GraphQL Context (Injected by Server)                      │
├─────────────────────────────────────────────────────────────┤
│  context = {                                                │
│    tenant_id: jwt.tenant_id,      ← Extracted from JWT    │
│    user_id: jwt.sub               ← Extracted from JWT    │
│  }                                                          │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  App Wrapper Function Call                                  │
├─────────────────────────────────────────────────────────────┤
│  app.create_contact(                                        │
│    input_pk_organization := context.tenant_id, ← JWT      │
│    input_created_by := context.user_id,        ← JWT      │
│    input_payload := mutation_input             ← User data │
│  )                                                          │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  Database INSERT                                            │
├─────────────────────────────────────────────────────────────┤
│  INSERT INTO crm.tb_contact (                               │
│    tenant_id,        ← FROM JWT (security)                 │
│    created_by,       ← FROM JWT (audit)                    │
│    fk_organization,  ← FROM USER INPUT (business, OPTIONAL)│
│    email,            ← FROM USER INPUT (business)          │
│    ...                                                      │
│  ) VALUES (                                                 │
│    input_pk_organization,     -- JWT tenant_id             │
│    input_created_by,          -- JWT user_id               │
│    v_fk_organization,         -- User-provided org         │
│    input_data.email,          -- User-provided email       │
│    ...                                                      │
│  )                                                          │
└─────────────────────────────────────────────────────────────┘
```

### **Key Distinction**

| Field | Source | Purpose | In Composite Type? | Can User Fake? |
|-------|--------|---------|-------------------|----------------|
| `tenant_id` | JWT token | Security isolation | ❌ NO | ❌ NO - Server enforces |
| `created_by` | JWT token | Audit trail | ❌ NO | ❌ NO - Server enforces |
| `fk_organization` | User input | Business relationship | ✅ YES (optional) | ✅ YES - But validated by core layer |
| `email` | User input | Business data | ✅ YES | ✅ YES - Validated by business logic |

### **Why Denormalize tenant_id?**

**Performance**:
```sql
-- ✅ FAST (index on tenant_id):
SELECT * FROM crm.tb_contact
WHERE tenant_id = 'tenant-uuid-456'
  AND status = 'active';

-- Uses: idx_tb_contact_tenant (tenant_id)

-- ❌ SLOW (requires JOIN):
SELECT c.* FROM crm.tb_contact c
JOIN management.tb_organization o ON c.fk_organization = o.pk_organization
WHERE o.id = 'tenant-uuid-456'
  AND c.status = 'active';

-- Needs JOIN + multiple index lookups
```

**Row-Level Security (RLS)**:
```sql
-- ✅ SIMPLE RLS POLICY:
CREATE POLICY tenant_isolation ON crm.tb_contact
FOR ALL
TO authenticated_user
USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- ❌ COMPLEX RLS (with JOIN):
CREATE POLICY tenant_isolation ON crm.tb_contact
FOR ALL
TO authenticated_user
USING (
  EXISTS (
    SELECT 1 FROM management.tb_organization o
    WHERE o.pk_organization = tb_contact.fk_organization
      AND o.id = current_setting('app.current_tenant_id')::UUID
  )
);
-- Slower, harder to maintain
```

### **When to Add fk_organization?**

**Add `fk_organization` when**:
- Entity logically belongs to an organizational unit (not just tenant)
- Business queries need to filter by organization
- Organizational hierarchy matters for the entity

**Examples**:
```sql
-- ✅ HAS fk_organization (belongs to specific org unit):
CREATE TABLE crm.tb_contact (
  tenant_id UUID NOT NULL,           -- Isolation
  fk_organization INTEGER,            -- Which org unit owns this contact
  ...
);

-- ✅ NO fk_organization (tenant-level only):
CREATE TABLE system.tb_configuration (
  tenant_id UUID NOT NULL,           -- Isolation (enough!)
  config_key TEXT,
  config_value JSONB,
  ...
);
```

---

## Appendix B: Reference Checklist

Use this checklist when generating tables:

```python
# Table Generation Checklist (Team B)

✅ Trinity Pattern:
   - pk_{entity} INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
   - id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE
   - identifier TEXT UNIQUE

✅ Multi-Tenancy (JWT Token Context):
   - tenant_id UUID NOT NULL              -- Denormalized from JWT (ALWAYS)
   - fk_organization INTEGER               -- Business FK (OPTIONAL, depends on domain)
   - INDEX on tenant_id (CRITICAL!)
   - INDEX on fk_organization (if present)

✅ Business Fields:
   - All entity fields
   - Foreign keys as fk_{field} INTEGER (not UUID!)
   - Enums with CHECK constraints

✅ Audit Trail (JWT Token Context):
   - created_at TIMESTAMPTZ DEFAULT now()
   - created_by UUID                       -- From JWT "sub" claim
   - updated_at TIMESTAMPTZ DEFAULT now()
   - updated_by UUID                       -- From JWT "sub" claim
   - deleted_at TIMESTAMPTZ                -- Soft delete timestamp
   - deleted_by UUID                       -- Who deleted (from JWT)

✅ Indexes:
   - id (UUID lookups)
   - tenant_id (multi-tenancy - CRITICAL!)
   - fk_organization (if present)
   - All FK fields
   - All enum fields

✅ Constraints:
   - Primary key
   - Foreign keys (via ALTER TABLE)
   - CHECK constraints for enums
   - NOT NULL where appropriate

✅ Helper Functions (Trinity Resolution):
   - {schema}.{entity}_pk(TEXT) → INTEGER  -- Accepts UUID/identifier/pk as text
   - {schema}.{entity}_id(INTEGER) → UUID  -- Converts pk → UUID

✅ FraiseQL Annotations:
   - Table comment with @fraiseql:type
   - Column comments for special fields

✅ JWT Token Mapping:
   - JWT "tenant_id" → tenant_id column (security context)
   - JWT "sub" → created_by, updated_by (user context)
   - JWT "organization_id" → MAY map to fk_organization (business logic)
```

Use this for composite types:

```python
# Composite Type Generation Checklist (Team B)

✅ Type Structure:
   - app.type_{action}_input
   - Fields use UUID for refs (not INTEGER!)
   - Field names: {field}_id for refs
   - Correct PostgreSQL types

✅ FraiseQL Annotations:
   - Type comment: @fraiseql:input name={PascalCase}Input
   - Field comments: @fraiseql:field with type info
   - Nullable indicators: required=true/false

✅ NOT in Composite Type (JWT Context - Security):
   - tenant_id (from JWT "tenant_id", NOT user input)
   - created_by (from JWT "sub", NOT user input)
   - updated_by (from JWT "sub", NOT user input)
   - audit fields (added by core layer)
   - pk_{entity} (internal only, never exposed)

✅ MAY be in Composite Type (Business Logic):
   - organization_id UUID (if entity belongs to org unit - business FK)
   - Other business relationships (e.g., team_id, department_id)
   - These are USER-PROVIDED, not from JWT context

✅ Naming Convention:
   - SpecQL: company
   - Composite: company_id UUID
   - GraphQL: companyId
   - Database: fk_company INTEGER

✅ Security Principle:
   - JWT context (tenant_id, user_id) → Function parameters → NOT in composite type
   - Business data (organization_id, company_id) → Composite type → From user input
   - Rule: Users can't fake their tenant/identity via API!
```
