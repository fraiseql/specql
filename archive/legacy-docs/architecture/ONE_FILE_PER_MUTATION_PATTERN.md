# One File Per Mutation Pattern - Architecture Specification

**Date**: 2025-11-09
**Status**: ✅ **REQUIRED PATTERN**
**Applies To**: Team E (CLI Orchestrator) + Schema Orchestrator

---

## 🎯 Core Principle

**Each mutation/action MUST have its own SQL file containing EXACTLY 2 functions:**
1. `app.{action_name}()` - App wrapper (API layer)
2. `core.{action_name}()` - Core logic (business layer)

**Utility functions** (Trinity helpers) go in **separate helper files**.

---

## 📂 Directory Structure

```
db/schema/
├── 00_foundation/
│   └── app_foundation.sql              # Composite types (mutation_result, etc.)
│
├── 10_tables/                          # ONE FILE PER ENTITY
│   ├── contact.sql                     # Table DDL + FraiseQL COMMENT annotations
│   ├── company.sql                     # Table DDL + FraiseQL COMMENT annotations
│   └── machine_item.sql                # Table DDL + FraiseQL COMMENT annotations
│
├── 20_helpers/                         # ONE FILE PER ENTITY (utility functions)
│   ├── contact_helpers.sql             # Trinity helpers: contact_pk(), contact_id(), etc.
│   ├── company_helpers.sql
│   └── machine_item_helpers.sql
│
└── 30_functions/                       # ONE FILE PER MUTATION ⚠️ CRITICAL!
    ├── create_contact.sql              # app + core functions + FraiseQL COMMENT annotations
    ├── update_contact.sql              # app + core functions + FraiseQL COMMENT annotations
    ├── delete_contact.sql              # app + core functions + FraiseQL COMMENT annotations
    ├── qualify_lead.sql                # app + core functions + FraiseQL COMMENT annotations
    ├── create_company.sql
    ├── update_company.sql
    └── create_reservation.sql
```

---

## 📄 File Content Example

### File: `db/schema/30_functions/qualify_lead.sql`

```sql
-- ============================================================================
-- Mutation: qualify_lead
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic
-- Generated: 2025-11-09
-- ============================================================================

-- ============================================================================
-- LAYER 1: APP WRAPPER (API Entry Point)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.qualify_lead(
    auth_tenant_id UUID,              -- Tenant context (from JWT)
    auth_user_id UUID,                -- User context (from JWT)
    input_payload JSONB               -- Raw API input (GraphQL/REST)
) RETURNS app.mutation_result         -- Standard response
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_qualify_lead_input;  -- Typed structure
BEGIN
    -- Convert JSONB → Composite Type
    input_data := jsonb_populate_record(
        NULL::app.type_qualify_lead_input,
        input_payload
    );

    -- Delegate to core logic
    RETURN core.qualify_lead(
        auth_tenant_id,
        input_data,          -- ✅ Typed input
        input_payload,       -- Original for audit
        auth_user_id
    );
END;
$$;

-- FraiseQL metadata (Team D) - IN SAME FILE as function
COMMENT ON FUNCTION app.qualify_lead IS
  '@fraiseql:mutation name=qualifyLead,input=QualifyLeadInput,output=MutationResult';


-- ============================================================================
-- LAYER 2: CORE LOGIC (Business Rules)
-- ============================================================================
CREATE OR REPLACE FUNCTION core.qualify_lead(
    auth_tenant_id UUID,
    input_data app.type_qualify_lead_input,  -- ✅ Typed input
    input_payload JSONB,                      -- Original for audit
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_pk INTEGER;
    v_status TEXT;
BEGIN
    -- === Trinity Resolution (UUID → INTEGER) ===
    v_contact_pk := crm.contact_pk(input_data.contact_id);

    IF v_contact_pk IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_data.contact_id,
            'NOOP',
            'failed:contact_not_found',
            ARRAY['contact_id']::TEXT[],
            'Contact not found',
            NULL,
            NULL
        );
    END IF;

    -- === Business Validation ===
    SELECT status INTO v_status
    FROM crm.tb_contact
    WHERE pk_contact = v_contact_pk
      AND tenant_id = auth_tenant_id;

    IF v_status != 'lead' THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_data.contact_id,
            'NOOP',
            'failed:not_a_lead',
            ARRAY['status']::TEXT[],
            'Contact is not a lead',
            NULL,
            jsonb_build_object('current_status', v_status)
        );
    END IF;

    -- === Business Logic ===
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = now(),
        updated_by = auth_user_id
    WHERE pk_contact = v_contact_pk
      AND tenant_id = auth_tenant_id;

    -- === Success Response ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        input_data.contact_id,
        'UPDATE',
        'success',
        ARRAY['status', 'updated_at', 'updated_by']::TEXT[],
        'Lead qualified successfully',
        (
            SELECT row_to_json(c)::JSONB
            FROM crm.tv_contact c
            WHERE c.id = input_data.contact_id
        ),
        NULL
    );
END;
$$;

-- FraiseQL metadata (Team D) - IN SAME FILE as function
COMMENT ON FUNCTION core.qualify_lead IS
  '@fraiseql:core_logic for=qualifyLead';
```

---

## 🔑 Key Patterns

### 1. App Wrapper Responsibilities

✅ **ONLY handles**:
- JSONB → Composite Type conversion
- Delegation to core layer
- FraiseQL annotation

❌ **Does NOT contain**:
- Business logic
- Validation
- Database operations

### 2. Core Logic Responsibilities

✅ **Handles**:
- Trinity resolution (UUID → INTEGER)
- Business validation
- Database operations (INSERT, UPDATE, DELETE)
- Audit field population
- Error handling
- Success/failure responses

### 3. File Naming

| Component | Naming Pattern | Example |
|-----------|---------------|---------|
| **Tables** | `{entity_name}.sql` | `contact.sql` |
| **Helpers** | `{entity_name}_helpers.sql` | `contact_helpers.sql` |
| **Mutations** | `{action_name}.sql` | `qualify_lead.sql` |
| **Table Metadata** | `{entity_name}_table_metadata.sql` | `contact_table_metadata.sql` |
| **Mutations Metadata** | `{entity_name}_mutations_metadata.sql` | `contact_mutations_metadata.sql` |

---

## 🚫 Anti-Patterns (WRONG ❌)

### ❌ WRONG: All actions in one file

```
30_functions/
└── contact_actions.sql    # ❌ Contains ALL actions for Contact
    ├── app.create_contact()
    ├── core.create_contact()
    ├── app.update_contact()
    ├── core.update_contact()
    ├── app.qualify_lead()
    └── core.qualify_lead()
```

**Problem**: Hard to manage, review, and version control. Changes to one mutation affect all others.

---

### ❌ WRONG: Functions mixed with helpers

```
30_functions/
└── contact.sql    # ❌ Mixes mutations + helpers
    ├── app.create_contact()
    ├── core.create_contact()
    ├── contact_pk()           # ← Helper function!
    ├── contact_id()           # ← Helper function!
    └── app.update_contact()
```

**Problem**: Helpers have different lifecycle than mutations. Helpers are stable, mutations change frequently.

---

### ❌ WRONG: One file per function (too granular)

```
30_functions/
├── app_create_contact.sql       # ❌ Only app wrapper
├── core_create_contact.sql      # ❌ Only core logic
├── app_update_contact.sql
└── core_update_contact.sql
```

**Problem**: App wrapper and core logic are tightly coupled. They should be together.

---

## ✅ Correct Pattern (RIGHT ✅)

### ✅ RIGHT: One file per mutation, 2 functions per file

```
30_functions/
├── create_contact.sql           # ✅ app.create_contact() + core.create_contact()
├── update_contact.sql           # ✅ app.update_contact() + core.update_contact()
├── delete_contact.sql           # ✅ app.delete_contact() + core.delete_contact()
└── qualify_lead.sql             # ✅ app.qualify_lead() + core.qualify_lead()

20_helpers/
└── contact_helpers.sql          # ✅ Separate file for utility functions
    ├── contact_pk()
    ├── contact_id()
    └── contact_identifier()
```

**Benefits**:
- ✅ Each mutation is self-contained
- ✅ Easy to review changes (one mutation at a time)
- ✅ Clear separation of concerns
- ✅ Helpers are reusable across mutations
- ✅ Version control friendly (small, focused commits)

---

## 🛠️ Implementation Requirements

### For `SchemaOrchestrator.generate_split_schema()`

**MUST return**:

```python
@dataclass
class MutationFunctionPair:
    """One mutation = 2 functions + FraiseQL comments (ALL IN ONE FILE)"""
    action_name: str
    app_wrapper_sql: str         # app.{action_name}()
    core_logic_sql: str          # core.{action_name}()
    fraiseql_comments_sql: str   # COMMENT ON FUNCTION statements (Team D)

@dataclass
class SchemaOutput:
    """Split output"""
    table_sql: str                           # → 10_tables/{entity}.sql (includes FraiseQL COMMENT)
    helpers_sql: str                         # → 20_helpers/{entity}_helpers.sql
    mutations: List[MutationFunctionPair]    # → 30_functions/{action_name}.sql (ONE FILE EACH!)
```

### For `CLIOrchestrator.generate_from_files()`

**MUST write**:

```python
# For each entity
for entity in entities:
    schema_output = orchestrator.generate_split_schema(entity)

    # 1. Write table (ONE file per entity)
    write_file(f"10_tables/{entity.name}.sql", schema_output.table_sql)

    # 2. Write helpers (ONE file per entity)
    write_file(f"20_helpers/{entity.name}_helpers.sql", schema_output.helpers_sql)

    # 3. Write mutations (ONE FILE PER MUTATION! ✅)
    for mutation in schema_output.mutations:
        content = f"""
-- ============================================================================
-- Mutation: {mutation.action_name}
-- Entity: {entity.name}
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

{mutation.app_wrapper_sql}

{mutation.core_logic_sql}

{mutation.fraiseql_comments_sql}
"""
        write_file(f"30_functions/{mutation.action_name}.sql", content)
```

---

## 📊 Benefits of This Pattern

| Benefit | Description |
|---------|-------------|
| **Modularity** | Each mutation is independent, can be modified without affecting others |
| **Version Control** | Git diffs are focused on single mutations, easy to review |
| **Testing** | Can test each mutation in isolation |
| **Debugging** | Easy to locate specific mutation code |
| **Code Review** | Reviewers see complete mutation (app + core) in one file |
| **Migration Management** | Confiture can track which mutations changed |
| **Refactoring** | Safe to refactor one mutation without risk to others |
| **Documentation** | Each file is self-documenting with header comments |

---

## 🚀 Migration from Current Implementation

**Current State (WRONG ❌)**:
- `generate_split_schema()` returns `functions_sql` as one blob
- All actions bundled together

**Target State (RIGHT ✅)**:
- `generate_split_schema()` returns `List[MutationFunctionPair]`
- Each action has separate `app_wrapper_sql` + `core_logic_sql`
- Orchestrator writes one file per mutation

**Implementation Steps**:
1. Update `SchemaOutput` dataclass (add `MutationFunctionPair`)
2. Modify `generate_split_schema()` to iterate actions
3. Update `CLIOrchestrator` to write one file per mutation
4. Update tests to expect multiple files
5. Verify with integration test

---

## 🎯 Success Criteria

- [ ] Each mutation has its own SQL file in `30_functions/`
- [ ] Each file contains exactly 2 functions (app + core)
- [ ] Helper functions are in separate `20_helpers/` directory
- [ ] File names match action names (e.g., `qualify_lead.sql`)
- [ ] Confiture can build from split files
- [ ] Git diff shows only changed mutations
- [ ] Tests verify correct file structure

---

**Status**: ⚠️ **NOT IMPLEMENTED** - Current code bundles all actions together
**Priority**: 🔴 **CRITICAL** - Breaks modularity and version control
**Owner**: Team E (CLI Orchestrator)
