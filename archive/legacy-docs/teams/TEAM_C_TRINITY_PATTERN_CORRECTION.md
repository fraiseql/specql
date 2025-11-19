# Team C: Trinity Pattern Naming Correction

**Date**: 2025-11-08
**Status**: 🚨 CRITICAL CORRECTION REQUIRED
**Priority**: IMMEDIATE

---

## 🚨 Issue Identified

Team C implementation plans and templates are using **INCORRECT** naming conventions that violate the Trinity pattern established by Team B.

### ❌ Current (WRONG) Naming

```sql
-- WRONG: Current templates use these names
CREATE OR REPLACE FUNCTION app.create_contact(
    input_pk_organization UUID,      -- ❌ WRONG
    input_created_by UUID,            -- ❌ WRONG
    input_payload JSONB
)
...
DECLARE
    v_id UUID := gen_random_uuid();  -- ❌ WRONG (ambiguous)
    v_pk_contact INTEGER;             -- ❌ WRONG (inconsistent)
```

### ✅ Correct (Trinity Pattern) Naming

```sql
-- ✅ CORRECT: Trinity pattern naming
CREATE OR REPLACE FUNCTION app.create_contact(
    auth_tenant_id UUID,              -- ✅ JWT tenant context
    auth_user_id UUID,                -- ✅ JWT user context
    input_payload JSONB
)
...
DECLARE
    v_contact_id UUID := gen_random_uuid();  -- ✅ Entity-specific UUID
    v_contact_pk INTEGER;                     -- ✅ Entity-specific INTEGER PK
```

---

## 📋 Trinity Pattern Naming Conventions

### **Parameter Naming**

| Purpose | Correct Name | Type | Source |
|---------|-------------|------|--------|
| Tenant context | `auth_tenant_id` | UUID | JWT claims |
| User context | `auth_user_id` | UUID | JWT claims |
| Input payload | `input_payload` | JSONB | GraphQL/REST |
| Composite input | `input_data` | composite type | Converted from JSONB |

### **Variable Naming**

| Purpose | Pattern | Example | Type |
|---------|---------|---------|------|
| New entity UUID | `v_{entity}_id` | `v_contact_id` | UUID |
| Entity INTEGER PK | `v_{entity}_pk` | `v_contact_pk` | INTEGER |
| Foreign key INTEGER | `v_{relation}_pk` | `v_company_pk` | INTEGER |
| Result variable | `v_result` | `v_result` | mutation_result |

### **Column Naming in INSERT/UPDATE**

| Purpose | Pattern | Example | Type |
|---------|---------|---------|------|
| Primary key | `pk_{entity}` | `pk_contact` | INTEGER |
| UUID identifier | `id` | `id` | UUID |
| Tenant denormalization | `tenant_id` | `tenant_id` | UUID |
| Created by | `created_by` | `created_by` | UUID |
| Updated by | `updated_by` | `updated_by` | UUID |
| Deleted by | `deleted_by` | `deleted_by` | UUID |

---

## 🔄 Required Changes

### **1. App Wrapper Template** (`templates/sql/app_wrapper.sql.j2`)

```diff
 CREATE OR REPLACE FUNCTION app.{{ app_function_name }}(
-    input_pk_organization UUID,      -- JWT context: tenant_id
-    input_created_by UUID,            -- JWT context: user_id
+    auth_tenant_id UUID,              -- JWT context: tenant_id
+    auth_user_id UUID,                -- JWT context: user_id
     input_payload JSONB               -- User input (GraphQL/REST)
 ) RETURNS app.mutation_result
 ...
     -- Delegate to core business logic
     RETURN {{ core_schema }}.{{ core_function_name }}(
-        input_pk_organization,
+        auth_tenant_id,
         input_data,
         input_payload,
-        input_created_by
+        auth_user_id
     );
```

### **2. Core Create Function Template** (`templates/sql/core_create_function.sql.j2`)

```diff
 CREATE OR REPLACE FUNCTION {{ entity.schema }}.create_{{ entity.name | lower }}(
-    input_pk_organization UUID,
+    auth_tenant_id UUID,
     input_data {{ composite_type }},
     input_payload JSONB,
-    input_created_by UUID
+    auth_user_id UUID
 ) RETURNS app.mutation_result
 ...
 DECLARE
-    v_id UUID := gen_random_uuid();
-    v_{{ entity.pk_column }} INTEGER;
+    v_{{ entity.name | lower }}_id UUID := gen_random_uuid();
+    v_{{ entity.name | lower }}_pk INTEGER;
 ...
     IF {{ validation.check }} THEN
         RETURN {{ entity.schema }}.log_and_return_mutation(
-            input_pk_organization,
-            input_created_by,
+            auth_tenant_id,
+            auth_user_id,
             '{{ entity.name | lower }}',
             '00000000-0000-0000-0000-000000000000'::UUID,
             ...
         );
     END IF;
 ...
     -- === BUSINESS LOGIC: INSERT ===
     INSERT INTO {{ entity.schema }}.{{ entity.table_name }} (
+        id,                           -- UUID
+        tenant_id,                    -- Denormalized tenant
         ...
         created_by                    -- Audit field
     ) VALUES (
+        v_{{ entity.name | lower }}_id,
+        auth_tenant_id,
         ...
-        input_created_by
+        auth_user_id
     )
-    RETURNING {{ entity.pk_column }} INTO v_{{ entity.pk_column }};
+    RETURNING pk_{{ entity.name | lower }} INTO v_{{ entity.name | lower }}_pk;
 ...
     -- === AUDIT & RETURN ===
     RETURN {{ entity.schema }}.log_and_return_mutation(
-        input_pk_organization,
-        input_created_by,
+        auth_tenant_id,
+        auth_user_id,
         '{{ entity.name | lower }}',
-        v_id,
+        v_{{ entity.name | lower }}_id,
         'INSERT',
         'success',
         ...
-        (SELECT row_to_json(t.*) FROM {{ entity.schema }}.{{ entity.table_name }} t WHERE t.id = v_id)::JSONB,
+        (SELECT row_to_json(t.*) FROM {{ entity.schema }}.{{ entity.table_name }} t WHERE t.id = v_{{ entity.name | lower }}_id)::JSONB,
         NULL
     );
```

### **3. Core Update Function Template** (`templates/sql/core_update_function.sql.j2`)

```diff
 CREATE OR REPLACE FUNCTION {{ entity.schema }}.update_{{ entity.name | lower }}(
-    input_pk_organization UUID,
+    auth_tenant_id UUID,
     input_payload JSONB,
-    input_created_by UUID
+    auth_user_id UUID
 ) RETURNS app.mutation_result
 ...
 DECLARE
-    v_pk_{{ entity.name | lower }} INTEGER;
+    v_{{ entity.name | lower }}_id UUID;
+    v_{{ entity.name | lower }}_pk INTEGER;
 ...
     -- Extract entity ID from payload
-    v_pk_{{ entity.name | lower }} := {{ entity.schema }}.{{ entity.name | lower }}_pk(
+    v_{{ entity.name | lower }}_id := (input_payload->>'id')::UUID;
+    v_{{ entity.name | lower }}_pk := {{ entity.schema }}.{{ entity.name | lower }}_pk(
-        (input_payload->>'id')::TEXT
+        v_{{ entity.name | lower }}_id::TEXT
     );
 ...
     UPDATE {{ entity.schema }}.{{ entity.table_name }}
     SET ...
         updated_at = now(),
-        updated_by = input_created_by
-    WHERE pk_{{ entity.name | lower }} = v_pk_{{ entity.name | lower }};
+        updated_by = auth_user_id
+    WHERE pk_{{ entity.name | lower }} = v_{{ entity.name | lower }}_pk;
```

### **4. Core Delete Function Template** (`templates/sql/core_delete_function.sql.j2`)

```diff
 CREATE OR REPLACE FUNCTION {{ entity.schema }}.delete_{{ entity.name | lower }}(
-    input_pk_organization UUID,
+    auth_tenant_id UUID,
     input_payload JSONB,
-    input_created_by UUID
+    auth_user_id UUID
 ) RETURNS app.mutation_result
 ...
 DECLARE
-    v_pk_{{ entity.name | lower }} INTEGER;
+    v_{{ entity.name | lower }}_id UUID;
+    v_{{ entity.name | lower }}_pk INTEGER;
 ...
     -- Soft delete
     UPDATE {{ entity.schema }}.{{ entity.table_name }}
     SET deleted_at = now(),
-        deleted_by = input_created_by
-    WHERE pk_{{ entity.name | lower }} = v_pk_{{ entity.name | lower }};
+        deleted_by = auth_user_id
+    WHERE pk_{{ entity.name | lower }} = v_{{ entity.name | lower }}_pk;
```

---

## 🎯 Rationale for Trinity Pattern Naming

### **Why `auth_tenant_id` not `input_pk_organization`?**

1. **Clarity**: `auth_` prefix clearly indicates JWT context parameter
2. **Consistency**: Matches JWT claim structure (`auth.tenant_id`)
3. **Separation**: Distinguishes auth context from business input
4. **Standard**: Follows PostgreSQL RLS pattern conventions

### **Why `v_{entity}_id` and `v_{entity}_pk`?**

1. **Type Safety**: Clear distinction between UUID (id) and INTEGER (pk)
2. **Entity-Specific**: `v_contact_id` is unambiguous, `v_id` is unclear
3. **Maintenance**: Easy to grep/search for specific entity operations
4. **Trinity Compliance**: Directly maps to Trinity columns (`id`, `pk_*`)

### **Why `auth_user_id` not `input_created_by`?**

1. **Semantic Clarity**: User ID is auth context, not input data
2. **Consistency**: Matches `auth_tenant_id` pattern
3. **Reusability**: Same user ID for created_by, updated_by, deleted_by
4. **JWT Mapping**: Directly corresponds to `auth.user_id` claim

---

## 📝 Code Generation Changes Required

### **CoreLogicGenerator** (`src/generators/core_logic_generator.py`)

```python
# Current (WRONG)
context = {
    "params": [
        "input_pk_organization UUID",      # ❌ WRONG
        "input_data composite_type",
        "input_payload JSONB",
        "input_created_by UUID"            # ❌ WRONG
    ],
    "variables": {
        "id": "v_id",                      # ❌ WRONG (ambiguous)
        "pk": f"v_{entity.pk_column}"      # ❌ WRONG (inconsistent)
    }
}

# Corrected (RIGHT)
context = {
    "params": [
        "auth_tenant_id UUID",              # ✅ CORRECT
        "input_data composite_type",
        "input_payload JSONB",
        "auth_user_id UUID"                 # ✅ CORRECT
    ],
    "variables": {
        "id": f"v_{entity.name.lower()}_id",    # ✅ CORRECT
        "pk": f"v_{entity.name.lower()}_pk"     # ✅ CORRECT
    }
}
```

### **AppWrapperGenerator** (`src/generators/app_wrapper_generator.py`)

```python
# Update template context
context = {
    "app_function_name": action.name,
    "composite_type_name": f"app.type_{action.name}_input",
    "core_schema": entity.schema,
    "core_function_name": action.name,
    "graphql_name": self._to_camel_case(action.name),
    # Parameter names
    "auth_params": {
        "tenant": "auth_tenant_id",  # ✅ CORRECT
        "user": "auth_user_id"       # ✅ CORRECT
    }
}
```

---

## 🧪 Test Updates Required

### **test_app_wrapper_generator.py**

```diff
 def test_app_wrapper_jwt_context_parameters():
     """App wrapper extracts JWT context"""
     sql = generator.generate_app_wrapper(entity, action)

     # Then: Context parameters use auth_ prefix
-    assert "input_pk_organization UUID" in sql
-    assert "input_created_by UUID" in sql
+    assert "auth_tenant_id UUID" in sql
+    assert "auth_user_id UUID" in sql
     # Then: Payload is third param
     assert "input_payload JSONB" in sql
```

### **test_core_logic_generator.py**

```diff
 def test_core_function_uses_trinity_naming():
     """Core function uses Trinity pattern variable names"""
     entity = Entity(name="Contact", ...)
     sql = generator.generate_core_create_function(entity)

-    assert "v_id UUID := gen_random_uuid()" in sql
-    assert "v_pk_contact INTEGER" in sql
+    assert "v_contact_id UUID := gen_random_uuid()" in sql
+    assert "v_contact_pk INTEGER" in sql
+    assert "auth_tenant_id UUID" in sql
+    assert "auth_user_id UUID" in sql
```

---

## 📊 Impact Analysis

### **Files to Update**

#### Templates
- ✅ `templates/sql/app_wrapper.sql.j2`
- ✅ `templates/sql/core_create_function.sql.j2`
- ✅ `templates/sql/core_update_function.sql.j2`
- ✅ `templates/sql/core_delete_function.sql.j2`

#### Python Generators
- ✅ `src/generators/app_wrapper_generator.py`
- ✅ `src/generators/core_logic_generator.py`
- ⚠️ `src/generators/actions/action_compiler.py` (if exists)
- ⚠️ `src/generators/actions/function_scaffolding.py` (if exists)

#### Tests
- ✅ `tests/unit/generators/test_app_wrapper_generator.py`
- ✅ `tests/unit/generators/test_core_logic_generator.py`

#### Documentation
- ✅ `docs/implementation-plans/TEAM_C_APP_CORE_FUNCTIONS_PLAN.md`
- ✅ `docs/teams/TEAM_C_DETAILED_PLAN.md`
- ⚠️ `docs/architecture/APP_CORE_FUNCTION_PATTERN.md`

---

## ✅ Verification Checklist

After making changes, verify:

- [ ] All templates use `auth_tenant_id` and `auth_user_id`
- [ ] All templates use `v_{entity}_id` and `v_{entity}_pk` pattern
- [ ] INSERT statements include `tenant_id` populated from `auth_tenant_id`
- [ ] INSERT statements include `created_by` populated from `auth_user_id`
- [ ] UPDATE statements include `updated_by = auth_user_id`
- [ ] DELETE statements include `deleted_by = auth_user_id`
- [ ] All tests updated to expect new naming
- [ ] All documentation reflects Trinity pattern
- [ ] Generated SQL validates in PostgreSQL
- [ ] No references to old naming remain

---

## 🚀 Migration Strategy

### Phase 1: Update Templates (Immediate)
```bash
# Update all SQL templates with correct naming
vim templates/sql/app_wrapper.sql.j2
vim templates/sql/core_create_function.sql.j2
vim templates/sql/core_update_function.sql.j2
vim templates/sql/core_delete_function.sql.j2
```

### Phase 2: Update Generators (Immediate)
```bash
# Update Python generators to use correct context
vim src/generators/app_wrapper_generator.py
vim src/generators/core_logic_generator.py
```

### Phase 3: Update Tests (Immediate)
```bash
# Update test expectations
vim tests/unit/generators/test_app_wrapper_generator.py
vim tests/unit/generators/test_core_logic_generator.py

# Run tests to verify
uv run pytest tests/unit/generators/ -v
```

### Phase 4: Update Documentation (Before Team C starts)
```bash
# Update all Team C documentation
vim docs/implementation-plans/TEAM_C_APP_CORE_FUNCTIONS_PLAN.md
vim docs/teams/TEAM_C_DETAILED_PLAN.md
vim docs/architecture/APP_CORE_FUNCTION_PATTERN.md
```

### Phase 5: Code Review (Before merge)
```bash
# Grep for old naming patterns
git grep -n "input_pk_organization"
git grep -n "input_created_by"
git grep -n "v_id UUID :="

# Should return 0 results
```

---

## 📚 Reference: Trinity Pattern Summary

### **Complete Example (Corrected)**

```sql
-- ============================================================================
-- APP LAYER: GraphQL Entry Point
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create_contact(
    auth_tenant_id UUID,              -- ✅ JWT tenant context
    auth_user_id UUID,                -- ✅ JWT user context
    input_payload JSONB               -- ✅ GraphQL input
) RETURNS app.mutation_result
LANGUAGE plpgsql AS $$
DECLARE
    input_data app.type_create_contact_input;
BEGIN
    input_data := jsonb_populate_record(NULL::app.type_create_contact_input, input_payload);

    RETURN crm.create_contact(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
END;
$$;

-- ============================================================================
-- CORE LAYER: Business Logic
-- ============================================================================
CREATE OR REPLACE FUNCTION crm.create_contact(
    auth_tenant_id UUID,
    input_data app.type_create_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id UUID := gen_random_uuid();  -- ✅ Entity-specific UUID
    v_contact_pk INTEGER;                     -- ✅ Entity-specific PK
    v_company_pk INTEGER;                     -- ✅ FK variable
BEGIN
    -- === VALIDATION ===
    IF input_data.email IS NULL THEN
        RETURN crm.log_and_return_mutation(
            auth_tenant_id,           -- ✅ Tenant context
            auth_user_id,             -- ✅ User context
            'contact',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'failed:missing_email',
            ARRAY['email']::TEXT[],
            'Email is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_email_null')
        );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.company_id IS NOT NULL THEN
        v_company_pk := crm.company_pk(input_data.company_id::TEXT);  -- ✅ FK resolution

        IF v_company_pk IS NULL THEN
            RETURN crm.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                '00000000-0000-0000-0000-000000000000'::UUID,
                'NOOP',
                'failed:company_not_found',
                ARRAY['company_id']::TEXT[],
                'Company not found',
                NULL, NULL,
                jsonb_build_object('company_id', input_data.company_id)
            );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO crm.tb_contact (
        id,                   -- ✅ UUID from v_contact_id
        tenant_id,            -- ✅ Denormalized from auth_tenant_id
        email,
        fk_company,           -- ✅ INTEGER FK from v_company_pk
        status,
        created_at,
        created_by            -- ✅ From auth_user_id
    ) VALUES (
        v_contact_id,         -- ✅ Generated UUID
        auth_tenant_id,       -- ✅ JWT tenant
        input_data.email,
        v_company_pk,         -- ✅ Resolved FK
        input_data.status,
        now(),
        auth_user_id          -- ✅ JWT user
    )
    RETURNING pk_contact INTO v_contact_pk;  -- ✅ Entity-specific PK variable

    -- === AUDIT & RETURN ===
    RETURN crm.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,         -- ✅ UUID identifier
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

---

## 🔍 Quick Reference Card

### **Parameter Naming**
```sql
-- ✅ ALWAYS use these names
auth_tenant_id UUID      -- JWT tenant context
auth_user_id UUID        -- JWT user context
input_payload JSONB      -- GraphQL/REST input
input_data composite     -- Typed composite (app layer)
```

### **Variable Naming**
```sql
-- ✅ ALWAYS use entity-specific names
v_contact_id UUID        -- New entity UUID
v_contact_pk INTEGER     -- Entity INTEGER PK
v_company_pk INTEGER     -- Foreign key PK
v_result mutation_result -- Function result
```

### **Column Value Mapping**
```sql
INSERT INTO crm.tb_contact (
    id,          -- ← v_contact_id
    tenant_id,   -- ← auth_tenant_id
    fk_company,  -- ← v_company_pk (resolved)
    created_by   -- ← auth_user_id
) VALUES (
    v_contact_id,
    auth_tenant_id,
    v_company_pk,
    auth_user_id
);
```

---

**CRITICAL**: All Team C code MUST follow these naming conventions to maintain consistency with the Trinity pattern and enable proper multi-tenancy, audit tracking, and UUID/INTEGER resolution.

**Last Updated**: 2025-11-08
**Priority**: IMMEDIATE ACTION REQUIRED
**Status**: Ready for Implementation
