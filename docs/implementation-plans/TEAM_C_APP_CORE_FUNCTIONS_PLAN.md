# Team C Implementation Plan: App/Core Function Pattern

**Date**: 2025-11-08
**Status**: 🚧 Ready for Implementation
**Priority**: HIGH
**Dependencies**: Team B Complete (✅)
**Estimated Time**: 4-5 days (phased TDD approach)

---

## 🎯 Mission

Transform Team C's function generator to produce the **App/Core two-layer pattern** with:
1. **App Layer Functions** (`app.*` schema) - API wrappers with JSONB → Composite Type conversion
2. **Core Layer Functions** (entity schema) - Business logic with typed inputs
3. **JWT Context Integration** - tenant_id and user_id from JWT claims
4. **Audit Trail** - Complete tracking with `created_by`, `updated_by`, `deleted_by`
5. **Trinity Resolution** - Use Team B's helper functions for UUID → INTEGER
6. **FraiseQL Metadata** - Annotations for GraphQL auto-discovery

---

## 📊 Current State Analysis

### What Exists (✅)
- `src/generators/function_generator.py` - Basic CRUD and action generation
- Function templates in `templates/sql/`
- Tests in `tests/unit/generators/test_function_generator.py`
- 7 tests passing (100%)

### What's Missing/Needs Adaptation (🔴)
- ❌ **App/Core two-layer pattern** - Currently generates single-layer functions
- ❌ **Composite type integration** - Needs to use Team B's generated types
- ❌ **JWT context parameters** - Missing `input_pk_organization`, `input_created_by`
- ❌ **tenant_id injection** - Not populating denormalized tenant_id
- ❌ **Audit field population** - created_by, updated_by, deleted_by not set
- ❌ **Trinity helper usage** - Not using `entity_pk()` for UUID → INTEGER
- ❌ **app.mutation_result return type** - Still returning JSONB
- ❌ **FraiseQL annotations** - Missing mutation metadata

---

## ⚠️ CRITICAL: App/Core Pattern Overview

### **The Two-Layer Architecture**

```
┌────────────────────────────────────────────────────────────┐
│  LAYER 1: APP WRAPPER (GraphQL Entry Point)               │
├────────────────────────────────────────────────────────────┤
│  Schema: app.*                                             │
│  Purpose: API contract, type conversion                    │
│  Input:  JSONB (from GraphQL/REST)                        │
│  Output: app.mutation_result                               │
│                                                            │
│  Responsibilities:                                         │
│  - Extract JWT context (tenant_id, user_id)              │
│  - Convert JSONB → Composite Type                         │
│  - Delegate to core layer                                 │
│  - NO business logic!                                      │
└────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────┐
│  LAYER 2: CORE LOGIC (Business Rules)                     │
├────────────────────────────────────────────────────────────┤
│  Schema: {entity_schema}  (e.g., crm, management)        │
│  Purpose: Business logic, validation, data manipulation    │
│  Input:  Composite Type (typed, validated)                │
│  Output: app.mutation_result                               │
│                                                            │
│  Responsibilities:                                         │
│  - Validate business rules                                │
│  - UUID → INTEGER resolution (Trinity helpers)            │
│  - INSERT/UPDATE with tenant_id, audit fields            │
│  - Error handling                                         │
│  - Return standardized result                             │
└────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Pattern (Reference)

Based on `docs/architecture/APP_CORE_FUNCTION_PATTERN.md`:

### **Example: create_contact Action**

**Team B Generated**:
```sql
-- Composite type (Team B)
CREATE TYPE app.type_create_contact_input AS (
    email TEXT,
    company_id UUID,
    status TEXT
);

-- Table (Team B)
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    tenant_id UUID NOT NULL,
    email TEXT,
    fk_company INTEGER,
    status TEXT,
    created_at TIMESTAMPTZ,
    created_by UUID,
    ...
);

-- Helper functions (Team B)
CREATE FUNCTION crm.contact_pk(TEXT) RETURNS INTEGER ...;
CREATE FUNCTION crm.company_pk(TEXT) RETURNS INTEGER ...;
```

**Team C Generates**:

```sql
-- ================================================================
-- APP LAYER: API Wrapper
-- ================================================================
CREATE OR REPLACE FUNCTION app.create_contact(
    input_pk_organization UUID,      -- JWT context: tenant_id
    input_created_by UUID,            -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_create_contact_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_create_contact_input,
        input_payload
    );

    -- Delegate to core logic (NO business logic here!)
    RETURN crm.create_contact(
        input_pk_organization,
        input_data,
        input_payload,
        input_created_by
    );
END;
$$;

COMMENT ON FUNCTION app.create_contact IS
  '@fraiseql:mutation name=createContact,input=CreateContactInput,output=MutationResult';

-- ================================================================
-- CORE LAYER: Business Logic
-- ================================================================
CREATE OR REPLACE FUNCTION crm.create_contact(
    input_pk_organization UUID,                   -- Tenant context
    input_data app.type_create_contact_input,     -- Typed input
    input_payload JSONB,                          -- Original (audit)
    input_created_by UUID                         -- User context
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID := gen_random_uuid();
    v_pk_contact INTEGER;
    v_fk_company INTEGER;
BEGIN
    -- === VALIDATION ===
    IF input_data.email IS NULL THEN
        RETURN crm.log_and_return_mutation(
            input_pk_organization,
            input_created_by,
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
        v_fk_company := crm.company_pk(input_data.company_id::TEXT);

        IF v_fk_company IS NULL THEN
            RETURN crm.log_and_return_mutation(
                input_pk_organization,
                input_created_by,
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
        id,
        tenant_id,              -- ✅ From JWT (denormalized)
        email,
        fk_company,            -- ✅ INTEGER (from Trinity helper)
        status,
        created_at,
        created_by             -- ✅ From JWT
    ) VALUES (
        v_id,
        input_pk_organization, -- ✅ JWT tenant_id → denormalized column
        input_data.email,
        v_fk_company,          -- ✅ Resolved UUID → INTEGER
        input_data.status,
        now(),
        input_created_by       -- ✅ JWT user_id
    )
    RETURNING pk_contact INTO v_pk_contact;

    -- === AUDIT & RETURN ===
    RETURN crm.log_and_return_mutation(
        input_pk_organization,
        input_created_by,
        'contact',
        v_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact created successfully',
        (SELECT row_to_json(c.*) FROM crm.tb_contact c WHERE c.id = v_id)::JSONB,
        NULL
    );
END;
$$;
```

---

## 📋 Implementation Phases (TDD Discipline)

---

### **Phase 1: App Wrapper Generator**

**Objective**: Generate `app.*` wrapper functions with JSONB → Composite Type conversion

#### 🔴 RED: Write Failing Tests

**Test File**: `tests/unit/generators/test_app_wrapper_generator.py`

```python
"""Tests for App Wrapper Generator (Team C)"""

def test_generate_app_wrapper_for_create_action():
    """Generate app wrapper for create action"""
    # Given: Entity with create action
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={...},
        actions=[Action(name="create_contact", ...)]
    )

    # When: Generate app wrapper
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, entity.actions[0])

    # Then: App wrapper function with correct signature
    assert "CREATE OR REPLACE FUNCTION app.create_contact(" in sql
    assert "input_pk_organization UUID" in sql
    assert "input_created_by UUID" in sql
    assert "input_payload JSONB" in sql
    assert "RETURNS app.mutation_result" in sql

    # Then: JSONB → Composite Type conversion
    assert "input_data app.type_create_contact_input" in sql
    assert "jsonb_populate_record" in sql

    # Then: Delegation to core layer
    assert "RETURN crm.create_contact(" in sql
    assert "input_pk_organization," in sql
    assert "input_data," in sql
    assert "input_payload," in sql
    assert "input_created_by" in sql

    # Then: FraiseQL annotation
    assert "COMMENT ON FUNCTION app.create_contact IS" in sql
    assert "@fraiseql:mutation" in sql


def test_app_wrapper_jwt_context_parameters():
    """App wrapper extracts JWT context"""
    # When: Generate
    sql = generator.generate_app_wrapper(entity, action)

    # Then: Context parameters are first two params
    assert "input_pk_organization UUID" in sql
    assert "input_created_by UUID" in sql
    # Then: Payload is third param
    assert "input_payload JSONB" in sql


def test_app_wrapper_uses_team_b_composite_type():
    """App wrapper references Team B's composite type"""
    # Given: Action name "create_contact"
    action = Action(name="create_contact")

    # When: Generate
    sql = generator.generate_app_wrapper(entity, action)

    # Then: Uses correct composite type name
    assert "app.type_create_contact_input" in sql
```

**Expected Outcome**: All tests FAIL (no `AppWrapperGenerator` exists yet)

---

#### 🟢 GREEN: Minimal Implementation

**Create**: `src/generators/app_wrapper_generator.py`

```python
"""
App Wrapper Generator (Team C)
Generates app.* API wrapper functions
"""

from jinja2 import Environment, FileSystemLoader
from src.core.ast_models import Entity, Action


class AppWrapperGenerator:
    """Generates app.* wrapper functions for GraphQL/REST API"""

    def __init__(self, templates_dir: str = "templates/sql"):
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate_app_wrapper(self, entity: Entity, action: Action) -> str:
        """
        Generate app wrapper function for action

        Args:
            entity: Entity containing the action
            action: Action to generate wrapper for

        Returns:
            SQL for app wrapper function
        """
        composite_type_name = f"app.type_{action.name}_input"
        graphql_name = self._to_camel_case(action.name)

        context = {
            "app_function_name": action.name,
            "composite_type_name": composite_type_name,
            "core_schema": entity.schema,
            "core_function_name": action.name,
            "graphql_name": graphql_name,
        }

        template = self.env.get_template("app_wrapper.sql.j2")
        return template.render(**context)

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
```

**Create Template**: `templates/sql/app_wrapper.sql.j2`

```sql
-- ============================================================================
-- APP WRAPPER: {{ app_function_name }}
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.{{ app_function_name }}(
    input_pk_organization UUID,      -- JWT context: tenant_id
    input_created_by UUID,            -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data {{ composite_type_name }};
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::{{ composite_type_name }},
        input_payload
    );

    -- Delegate to core business logic
    RETURN {{ core_schema }}.{{ core_function_name }}(
        input_pk_organization,
        input_data,
        input_payload,
        input_created_by
    );
END;
$$;

-- FraiseQL Metadata
COMMENT ON FUNCTION app.{{ app_function_name }} IS
  '@fraiseql:mutation name={{ graphql_name }},input={{ graphql_name | title }}Input,output=MutationResult';
```

**Run Tests**: `uv run pytest tests/unit/generators/test_app_wrapper_generator.py -v`

**Expected**: Tests PASS (minimal implementation works)

---

#### 🔧 REFACTOR: Enhance and Clean

**Improvements**:
1. Handle update actions (different parameter needs)
2. Handle delete actions (may not need composite type)
3. Add error handling
4. Support custom action parameter detection

---

#### ✅ QA: Quality Verification

```bash
uv run pytest tests/unit/generators/test_app_wrapper_generator.py -v
uv run mypy src/generators/app_wrapper_generator.py
uv run ruff check src/generators/
```

---

### **Phase 2: Core Logic Generator**

**Objective**: Generate core business logic functions with validation, Trinity resolution, audit trail

#### 🔴 RED: Write Failing Tests

**Test File**: `tests/unit/generators/test_core_logic_generator.py`

```python
"""Tests for Core Logic Generator (Team C)"""

def test_generate_core_create_function():
    """Generate core create function with full pattern"""
    # Given: Entity with fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(type="text", nullable=False),
            "company": FieldDefinition(type="ref", target_entity="Company", nullable=True),
            "status": FieldDefinition(type="enum", values=["lead", "qualified"], nullable=False)
        }
    )

    # When: Generate core function
    generator = CoreLogicGenerator()
    sql = generator.generate_core_create_function(entity)

    # Then: Correct signature
    assert "CREATE OR REPLACE FUNCTION crm.create_contact(" in sql
    assert "input_pk_organization UUID" in sql
    assert "input_data app.type_create_contact_input" in sql
    assert "input_payload JSONB" in sql
    assert "input_created_by UUID" in sql
    assert "RETURNS app.mutation_result" in sql

    # Then: Validation logic
    assert "IF input_data.email IS NULL THEN" in sql
    assert "RETURN crm.log_and_return_mutation" in sql

    # Then: Trinity resolution (UUID → INTEGER)
    assert "v_fk_company := crm.company_pk(input_data.company_id::TEXT)" in sql

    # Then: INSERT with all fields
    assert "INSERT INTO crm.tb_contact (" in sql
    assert "tenant_id," in sql
    assert "created_by" in sql
    assert "VALUES (" in sql
    assert "input_pk_organization," in sql  # tenant_id from JWT
    assert "input_created_by" in sql        # created_by from JWT

    # Then: Return mutation result
    assert "RETURN crm.log_and_return_mutation" in sql


def test_core_function_uses_trinity_helpers():
    """Core function uses Team B's Trinity helpers"""
    # Given: Entity with foreign key
    entity = Entity(fields={"company": FieldDefinition(type="ref", target_entity="Company")})

    # When: Generate
    sql = generator.generate_core_create_function(entity)

    # Then: Uses entity_pk() helper
    assert "crm.company_pk(" in sql
    assert "input_data.company_id::TEXT" in sql


def test_core_function_populates_audit_fields():
    """Core function populates all audit fields"""
    # When: Generate
    sql = generator.generate_core_create_function(entity)

    # Then: All audit fields in INSERT
    assert "created_at," in sql
    assert "created_by," in sql
    # Then: Values from JWT and now()
    assert "now()" in sql
    assert "input_created_by" in sql


def test_core_function_populates_tenant_id():
    """Core function populates denormalized tenant_id"""
    # When: Generate
    sql = generator.generate_core_create_function(entity)

    # Then: tenant_id in INSERT
    assert "tenant_id," in sql
    # Then: Value from JWT context
    assert "input_pk_organization" in sql
```

**Expected Outcome**: All tests FAIL (no `CoreLogicGenerator` exists yet)

---

#### 🟢 GREEN: Minimal Implementation

**Create**: `src/generators/core_logic_generator.py`

```python
"""
Core Logic Generator (Team C)
Generates core.* business logic functions
"""

from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from src.core.ast_models import Entity, FieldDefinition


class CoreLogicGenerator:
    """Generates core layer business logic functions"""

    def __init__(self, templates_dir: str = "templates/sql"):
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate_core_create_function(self, entity: Entity) -> str:
        """
        Generate core CREATE function with:
        - Input validation
        - Trinity resolution (UUID → INTEGER)
        - tenant_id population
        - Audit field population
        """
        # Prepare field mappings
        fields = self._prepare_insert_fields(entity)
        validations = self._generate_validations(entity)
        fk_resolutions = self._generate_fk_resolutions(entity)

        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": f"tb_{entity.name.lower()}",
                "pk_column": f"pk_{entity.name.lower()}",
            },
            "composite_type": f"app.type_create_{entity.name.lower()}_input",
            "fields": fields,
            "validations": validations,
            "fk_resolutions": fk_resolutions,
        }

        template = self.env.get_template("core_create_function.sql.j2")
        return template.render(**context)

    def _prepare_insert_fields(self, entity: Entity) -> Dict:
        """Prepare field list for INSERT statement"""
        insert_fields = []
        insert_values = []

        # Trinity fields
        insert_fields.append("id")
        insert_values.append("v_id")

        # Multi-tenancy
        insert_fields.append("tenant_id")
        insert_values.append("input_pk_organization")

        # Business fields
        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref":
                # Foreign key (INTEGER)
                fk_name = f"fk_{field_name}"
                insert_fields.append(fk_name)
                insert_values.append(f"v_{fk_name}")
            else:
                # Regular field
                insert_fields.append(field_name)
                insert_values.append(f"input_data.{field_name}")

        # Audit fields
        insert_fields.extend(["created_at", "created_by"])
        insert_values.extend(["now()", "input_created_by"])

        return {
            "columns": insert_fields,
            "values": insert_values,
        }

    def _generate_validations(self, entity: Entity) -> List[str]:
        """Generate validation checks for required fields"""
        validations = []
        for field_name, field_def in entity.fields.items():
            if not field_def.nullable:
                # Generate validation for required field
                validations.append({
                    "field": field_name,
                    "check": f"input_data.{field_name} IS NULL",
                    "error": f"failed:missing_{field_name}",
                    "message": f"{field_name.capitalize()} is required",
                })
        return validations

    def _generate_fk_resolutions(self, entity: Entity) -> List[Dict]:
        """Generate UUID → INTEGER FK resolutions using Trinity helpers"""
        resolutions = []
        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref" and field_def.target_entity:
                resolutions.append({
                    "field": field_name,
                    "target_entity": field_def.target_entity,
                    "variable": f"v_fk_{field_name}",
                    "helper_function": f"{entity.schema}.{field_def.target_entity.lower()}_pk",
                    "input_field": f"{field_name}_id",  # Composite type uses company_id
                })
        return resolutions
```

**Create Template**: `templates/sql/core_create_function.sql.j2`

```sql
-- ============================================================================
-- CORE LOGIC: {{ entity.schema }}.create_{{ entity.name | lower }}
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION {{ entity.schema }}.create_{{ entity.name | lower }}(
    input_pk_organization UUID,
    input_data {{ composite_type }},
    input_payload JSONB,
    input_created_by UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID := gen_random_uuid();
    v_{{ entity.pk_column }} INTEGER;
{%- for resolution in fk_resolutions %}
    {{ resolution.variable }} INTEGER;
{%- endfor %}
BEGIN
    -- === VALIDATION ===
{%- for validation in validations %}
    IF {{ validation.check }} THEN
        RETURN {{ entity.schema }}.log_and_return_mutation(
            input_pk_organization,
            input_created_by,
            '{{ entity.name | lower }}',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            '{{ validation.error }}',
            ARRAY['{{ validation.field }}']::TEXT[],
            '{{ validation.message }}',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_{{ validation.field }}_null')
        );
    END IF;
{%- endfor %}

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
{%- for resolution in fk_resolutions %}
    IF input_data.{{ resolution.input_field }} IS NOT NULL THEN
        {{ resolution.variable }} := {{ resolution.helper_function }}(input_data.{{ resolution.input_field }}::TEXT);

        IF {{ resolution.variable }} IS NULL THEN
            RETURN {{ entity.schema }}.log_and_return_mutation(
                input_pk_organization,
                input_created_by,
                '{{ entity.name | lower }}',
                '00000000-0000-0000-0000-000000000000'::UUID,
                'NOOP',
                'failed:{{ resolution.field }}_not_found',
                ARRAY['{{ resolution.input_field }}']::TEXT[],
                '{{ resolution.target_entity }} not found',
                NULL, NULL,
                jsonb_build_object('{{ resolution.input_field }}', input_data.{{ resolution.input_field }})
            );
        END IF;
    END IF;
{%- endfor %}

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO {{ entity.schema }}.{{ entity.table_name }} (
{%- for column in fields.columns %}
        {{ column }}{{ "," if not loop.last else "" }}
{%- endfor %}
    ) VALUES (
{%- for value in fields.values %}
        {{ value }}{{ "," if not loop.last else "" }}
{%- endfor %}
    )
    RETURNING {{ entity.pk_column }} INTO v_{{ entity.pk_column }};

    -- === AUDIT & RETURN ===
    RETURN {{ entity.schema }}.log_and_return_mutation(
        input_pk_organization,
        input_created_by,
        '{{ entity.name | lower }}',
        v_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        '{{ entity.name }} created successfully',
        (SELECT row_to_json(t.*) FROM {{ entity.schema }}.{{ entity.table_name }} t WHERE t.id = v_id)::JSONB,
        NULL
    );
END;
$$;
```

**Run Tests**: `uv run pytest tests/unit/generators/test_core_logic_generator.py -v`

---

#### 🔧 REFACTOR: Support Update and Delete

**Add**:
- `generate_core_update_function()` - Similar pattern but UPDATE instead of INSERT
- `generate_core_delete_function()` - Soft delete with deleted_at, deleted_by

---

#### ✅ QA: Quality Verification

```bash
uv run pytest tests/unit/generators/test_core_logic_generator.py -v
uv run mypy src/generators/core_logic_generator.py
```

---

### **Phase 3: Integration with Function Generator**

**Objective**: Update existing `FunctionGenerator` to use App+Core generators

#### 🔴 RED: Update Tests

```python
def test_function_generator_produces_app_core_layers():
    """Function generator produces both app and core layers"""
    # Given: Entity with create action
    entity = Entity(...)

    # When: Generate functions
    generator = FunctionGenerator()
    sql = generator.generate_action_functions(entity)

    # Then: Contains app wrapper
    assert "CREATE OR REPLACE FUNCTION app.create_contact(" in sql
    # Then: Contains core logic
    assert "CREATE OR REPLACE FUNCTION crm.create_contact(" in sql
```

#### 🟢 GREEN: Update FunctionGenerator

```python
class FunctionGenerator:
    def __init__(self, templates_dir: str = "templates/sql"):
        self.app_gen = AppWrapperGenerator(templates_dir)
        self.core_gen = CoreLogicGenerator(templates_dir)

    def generate_action_functions(self, entity: Entity) -> str:
        """Generate both app and core layers for actions"""
        functions = []

        for action in entity.actions:
            # App layer
            app_wrapper = self.app_gen.generate_app_wrapper(entity, action)
            functions.append(app_wrapper)

            # Core layer
            if action.name.startswith("create"):
                core_logic = self.core_gen.generate_core_create_function(entity)
            elif action.name.startswith("update"):
                core_logic = self.core_gen.generate_core_update_function(entity)
            elif action.name.startswith("delete"):
                core_logic = self.core_gen.generate_core_delete_function(entity)
            else:
                # Custom action
                core_logic = self.core_gen.generate_core_custom_action(entity, action)

            functions.append(core_logic)

        return "\n\n".join(functions)
```

---

### **Phase 4: log_and_return_mutation Helper**

**Objective**: Generate the audit logging helper function

#### 🔴 RED: Write Test

```python
def test_generate_log_and_return_mutation_helper():
    """Generate log_and_return_mutation helper for schema"""
    # When: Generate helper
    generator = CoreLogicGenerator()
    sql = generator.generate_log_and_return_mutation("crm")

    # Then: Helper function exists
    assert "CREATE OR REPLACE FUNCTION crm.log_and_return_mutation(" in sql
    assert "RETURNS app.mutation_result" in sql
```

#### 🟢 GREEN: Implementation

Generate once per schema:

```sql
CREATE OR REPLACE FUNCTION crm.log_and_return_mutation(
    p_tenant_id UUID,
    p_user_id UUID,
    p_entity TEXT,
    p_entity_id UUID,
    p_operation TEXT,
    p_status TEXT,
    p_updated_fields TEXT[],
    p_message TEXT,
    p_object_data JSONB,
    p_extra_metadata JSONB
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
BEGIN
    -- TODO: Insert into audit log table

    -- Return standardized result
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
```

---

## 🎯 Team C Deliverables

### Code Modules
1. ✅ `src/generators/app_wrapper_generator.py` - App layer wrappers
2. ✅ `src/generators/core_logic_generator.py` - Core business logic
3. ✅ Updated `src/generators/function_generator.py` - Orchestration
4. ✅ `templates/sql/app_wrapper.sql.j2` - App wrapper template
5. ✅ `templates/sql/core_create_function.sql.j2` - Core CREATE template
6. ✅ `templates/sql/core_update_function.sql.j2` - Core UPDATE template
7. ✅ `templates/sql/core_delete_function.sql.j2` - Core DELETE template

### Tests
1. ✅ `tests/unit/generators/test_app_wrapper_generator.py` (10+ tests)
2. ✅ `tests/unit/generators/test_core_logic_generator.py` (15+ tests)
3. ✅ Updated `tests/unit/generators/test_function_generator.py` (integration tests)
4. ✅ Coverage: 90%+ for new code

### Documentation
1. ✅ API docs for new generators
2. ✅ Examples of generated functions
3. ✅ JWT context mapping documentation

---

## 🔗 Team B Integration Points

**Team C Uses from Team B**:
1. **Composite Types**: `app.type_{action}_input`
2. **Trinity Helpers**: `{schema}.{entity}_pk(TEXT) → INTEGER`
3. **Standard Output**: `app.mutation_result`
4. **Table Schema**: Column names, types for INSERT/UPDATE

**Example Usage**:
```sql
-- Team B generated:
CREATE TYPE app.type_create_contact_input AS (company_id UUID);
CREATE FUNCTION crm.company_pk(TEXT) RETURNS INTEGER;

-- Team C uses:
DECLARE
    input_data app.type_create_contact_input;  -- ✅ Team B's type
    v_fk_company INTEGER;
BEGIN
    v_fk_company := crm.company_pk(input_data.company_id::TEXT);  -- ✅ Team B's helper
    INSERT INTO crm.tb_contact (fk_company) VALUES (v_fk_company);
END;
```

---

## 📊 Success Metrics

- [ ] ✅ Generate app wrapper functions for all actions
- [ ] ✅ Generate core logic functions with full pattern
- [ ] ✅ Use Team B's composite types correctly
- [ ] ✅ Use Team B's Trinity helpers for FK resolution
- [ ] ✅ Populate tenant_id from JWT context
- [ ] ✅ Populate all audit fields (created_by, updated_by, deleted_by)
- [ ] ✅ Return app.mutation_result (not JSONB)
- [ ] ✅ Generate FraiseQL mutation annotations
- [ ] ✅ All tests pass (90%+ coverage)
- [ ] ✅ Generated SQL matches PrintOptim pattern

---

## 🚀 Getting Started

```bash
# Create branch
git checkout -b feature/team-c-app-core-functions

# Phase 1: App wrapper generation
# 1. Write tests
vim tests/unit/generators/test_app_wrapper_generator.py

# 2. Run tests (should fail)
uv run pytest tests/unit/generators/test_app_wrapper_generator.py -v

# 3. Implement
vim src/generators/app_wrapper_generator.py
vim templates/sql/app_wrapper.sql.j2

# 4. Run tests (should pass)
uv run pytest tests/unit/generators/test_app_wrapper_generator.py -v

# Continue with Phase 2, 3, 4...
```

---

## 📚 Reference Documents

1. **Architecture**: `docs/architecture/APP_CORE_FUNCTION_PATTERN.md`
2. **Team B Review**: `docs/implementation-plans/CTO_IMPLEMENTATION_REVIEW_TEAM_B.md`
3. **PrintOptim Examples**: `../printoptim_backend/db/0_schema/03_functions/`
4. **JWT Pattern**: CTO Review Appendix A

---

## ⚠️ Common Pitfalls to Avoid

### ❌ Don't Use INTEGER in Composite Types
```sql
-- ❌ BAD (Team C should never do this)
CREATE TYPE app.type_create_contact_input AS (
    company INTEGER  -- Wrong! External API uses UUID
);
```
Team B already generated composite types with UUID. Just use them.

### ❌ Don't Forget tenant_id
```sql
-- ❌ BAD
INSERT INTO crm.tb_contact (email, fk_company) VALUES (...);

-- ✅ GOOD
INSERT INTO crm.tb_contact (tenant_id, email, fk_company)
VALUES (input_pk_organization, ...);
```

### ❌ Don't Skip Trinity Resolution
```sql
-- ❌ BAD (UUID can't go into INTEGER column!)
INSERT INTO crm.tb_contact (fk_company) VALUES (input_data.company_id);

-- ✅ GOOD
v_fk_company := crm.company_pk(input_data.company_id::TEXT);
INSERT INTO crm.tb_contact (fk_company) VALUES (v_fk_company);
```

### ❌ Don't Skip Audit Fields
```sql
-- ❌ BAD
INSERT INTO crm.tb_contact (email) VALUES (...);

-- ✅ GOOD
INSERT INTO crm.tb_contact (email, created_at, created_by)
VALUES (..., now(), input_created_by);
```

---

**Last Updated**: 2025-11-08
**Status**: Ready for Development
**Estimated Duration**: 4-5 days (with TDD discipline)
