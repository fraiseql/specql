# FraiseQL Integration Requirements

**Project**: PrintOptim Backend + FraiseQL Auto-Generation
**Date**: November 8, 2025
**Status**: Requirements Definition
**Integration Goal**: Unified YAML → SQL DDL → GraphQL Backend Pipeline

---

## Executive Summary

This document defines requirements for integrating **two complementary systems**:

1. **YAML-to-DDL Generator** (printoptim_backend_poc) - Generates PostgreSQL tables/functions from YAML
2. **FraiseQL Auto-Backend** (fraiseql) - Generates GraphQL API from PostgreSQL metadata

### Vision: Single Source of Truth

```
┌─────────────────────────────────────────────────────────────────────┐
│                     UNIFIED YAML ENTITY DEFINITION                  │
│                  (Single Source of Truth - entities/)               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
         ┌─────────────────┴──────────────────┐
         ▼                                    ▼
┌──────────────────────┐            ┌─────────────────────────┐
│  YAML-to-DDL Engine  │            │  FraiseQL Metadata      │
│  (printoptim_poc)    │            │  Annotations            │
└──────────┬───────────┘            └────────┬────────────────┘
           │                                 │
           ▼                                 ▼
┌──────────────────────┐            ┌─────────────────────────┐
│  PostgreSQL Schema   │            │  @fraiseql:type         │
│  - Tables            │───────────▶│  COMMENT annotations    │
│  - Functions         │            │  in generated SQL       │
│  - Trinity Helpers   │            └────────┬────────────────┘
└──────────────────────┘                     │
                                             ▼
                                    ┌─────────────────────────┐
                                    │  FraiseQL Auto-Discovery│
                                    │  (introspection engine) │
                                    └────────┬────────────────┘
                                             ▼
                                    ┌─────────────────────────┐
                                    │  Full GraphQL Backend   │
                                    │  - Types (auto)         │
                                    │  - Queries (auto)       │
                                    │  - Mutations (auto)     │
                                    │  - Filters (auto)       │
                                    └─────────────────────────┘
```

**Result**: Write YAML once → Get PostgreSQL schema + GraphQL API automatically

---

## 🎯 Integration Objectives

### Primary Goal
Enable **zero-code GraphQL backend generation** from YAML entity definitions by:
1. Generating PostgreSQL schema with FraiseQL-compatible metadata annotations
2. Auto-discovering schema to generate complete GraphQL API
3. Maintaining Trinity Pattern compatibility throughout the stack

### Success Criteria

**Functional:**
- ✅ YAML entity → PostgreSQL tables with `@fraiseql:type` annotations
- ✅ YAML entity → PostgreSQL functions with `@fraiseql:mutation` annotations
- ✅ FraiseQL auto-discovers types, queries, mutations from generated SQL
- ✅ GraphQL API works without writing Python code
- ✅ Trinity Pattern preserved (pk_* INTEGER, id UUID, identifier TEXT)

**Non-Functional:**
- ✅ Developer experience: Define entity in YAML, get full API (< 10 minutes)
- ✅ Quality: Generated code is production-ready
- ✅ Maintainability: Single YAML change propagates to SQL + GraphQL
- ✅ Performance: Trinity Pattern ensures optimal database performance

---

## 📊 Current State Analysis

### System 1: YAML-to-DDL Generator (printoptim_backend_poc)

**Status**: ✅ POC Complete, Validated
**Location**: `/home/lionel/code/printoptim_backend_poc/`

#### Current Capabilities
- ✅ Generate CREATE TABLE from YAML (76 lines generated)
- ✅ Generate Trinity helper functions (4 per entity, 129 lines)
- ✅ Generate translation tables (i18n support)
- ✅ Support foreign keys, constraints, indexes
- ✅ Generate comprehensive documentation (COMMENT statements)
- ✅ 96% faster than manual SQL creation

#### Current Output Structure
```
generated/
├── tables/
│   └── tb_manufacturer.sql          # Table definitions
└── functions/
    └── manufacturer_trinity_helpers.sql  # Trinity helpers
```

#### Missing for FraiseQL Integration
- ❌ No `@fraiseql:type` annotations in generated SQL
- ❌ No `@fraiseql:mutation` annotations on functions
- ❌ No view generation (FraiseQL needs views for types)
- ❌ No JSONB data column in views (FraiseQL trinity pattern)
- ❌ CREATE/UPDATE/DELETE mutation functions not generated

---

### System 2: FraiseQL Auto-Backend (from analysis)

**Status**: 📋 Design Complete, Implementation Planned
**Location**: `/tmp/fraiseql_auto_backend_analysis.md`

#### Required Input Format
FraiseQL auto-discovery expects:

**1. Views with Annotations:**
```sql
CREATE VIEW v_manufacturer AS
SELECT
    id,
    identifier,
    jsonb_build_object(
        'id', id::text,
        'identifier', identifier,
        'name', name,
        'abbreviation', abbreviation
    ) AS data
FROM tb_manufacturer;

COMMENT ON VIEW v_manufacturer IS '@fraiseql:type
trinity: true
use_projection: false
description: Printer/copier manufacturer';

COMMENT ON COLUMN v_manufacturer.id IS 'Public UUID identifier';
COMMENT ON COLUMN v_manufacturer.identifier IS 'Internal stable identifier';
```

**2. Functions with Annotations:**
```sql
CREATE FUNCTION fn_create_manufacturer(
    p_identifier TEXT,
    p_name TEXT,
    p_abbreviation CHAR(2)
) RETURNS JSONB AS $$
-- Business logic here
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_create_manufacturer IS '@fraiseql:mutation
input:
  identifier: { type: string, description: "Stable identifier" }
  name: { type: string, description: "Display name" }
  abbreviation: { type: string, description: "2-letter code" }
success: Manufacturer
failure: ValidationError
description: Create a new manufacturer';
```

#### Auto-Generated Output
From annotated views + functions, FraiseQL generates:
- ✅ GraphQL types (from views)
- ✅ Queries: `manufacturer(id)`, `manufacturers(where, orderBy)`, `manufacturersConnection(...)`
- ✅ Mutations: `createManufacturer`, `updateManufacturer`, `deleteManufacturer`
- ✅ Filter inputs: `ManufacturerWhereInput` with field-specific operators
- ✅ OrderBy inputs: `ManufacturerOrderByInput`

---

## 🏗️ Integration Architecture

### Phase 1: Enhanced YAML Schema (YAML Extension)

Add FraiseQL metadata to existing YAML entity definitions:

```yaml
entity:
  name: manufacturer
  schema: catalog
  table_code: "013211"
  description: "Lists recognized printer/copier manufacturers"

  # === NEW: FraiseQL Integration Section ===
  fraiseql:
    enabled: true                    # Generate FraiseQL-compatible artifacts

    # Type configuration
    type:
      generate_view: true            # Generate v_manufacturer view
      trinity: true                  # Use trinity pattern (id, identifier)
      use_projection: false          # Use v_* (views) not tv_* (projection tables)
      expose_fields:                 # Fields to expose in GraphQL
        - id
        - identifier
        - name
        - abbreviation
        - color_name

    # Query configuration
    queries:
      find_one: true                 # manufacturer(id: UUID)
      find_one_by_identifier: true   # manufacturerByIdentifier(identifier: String)
      find_many: true                # manufacturers(where, orderBy, limit, offset)
      connection: true               # manufacturersConnection(first, after, where)

    # Mutation configuration
    mutations:
      create:
        enabled: true
        function_name: fn_create_manufacturer
        input_fields: [identifier, name, abbreviation, color_name, fk_company]
        success_type: Manufacturer
        failure_type: ValidationError

      update:
        enabled: true
        function_name: fn_update_manufacturer
        input_fields: [name, abbreviation, color_name]
        success_type: Manufacturer
        failure_type: ValidationError

      delete:
        enabled: true
        function_name: fn_delete_manufacturer
        soft: true                   # Use deleted_at
        success_type: DeleteResult
        failure_type: ValidationError

  # === Existing Fields Section ===
  fields:
    identifier:
      type: TEXT
      nullable: false
      unique: true
      description: "Internal stable identifier (e.g., 'canon', 'ricoh')"
      fraiseql:                      # NEW: FraiseQL field metadata
        filter_operators: [eq, neq, in, nin, contains, startsWith, endsWith]
        sortable: true

    name:
      type: TEXT
      nullable: true
      description: "Optional display name (can be localized)"
      fraiseql:
        filter_operators: [eq, contains, startsWith]
        sortable: true

    abbreviation:
      type: CHAR(2)
      nullable: false
      unique: true
      description: "Short 2-letter code"
      fraiseql:
        filter_operators: [eq, in]
        sortable: true

    color_name:
      type: TEXT
      nullable: false
      description: "CSS-compatible color name or code"
      fraiseql:
        filter_operators: [eq, contains]
        sortable: false

  # === Existing Sections (Unchanged) ===
  foreign_keys:
    fk_company:
      references: management.tb_organization
      on: pk_organization
      nullable: true
      description: "Foreign key to organization"

  trinity_helpers:
    generate: true
    lookup_by: identifier
    helpers:
      - name: manufacturer_pk
        params: [identifier]
        returns: INTEGER
        description: "Resolve identifier to PK"
      # ... other helpers
```

---

### Phase 2: Extended Template System

Add new Jinja2 templates to generate FraiseQL-compatible artifacts:

#### New Templates Needed

**1. `templates/fraiseql_view.sql.j2`** - Generate FraiseQL type views
```jinja2
{# Generate v_[entity] view for FraiseQL type #}
{%- if entity.fraiseql.enabled and entity.fraiseql.type.generate_view %}

-- ============================================================================
-- FraiseQL Type View: v_{{ entity.name }}
-- ============================================================================
-- Purpose: Exposes {{ entity.name }} as GraphQL type via FraiseQL auto-discovery
-- Trinity Pattern: id (UUID), identifier (TEXT business key)
-- ============================================================================

CREATE OR REPLACE VIEW {{ entity.schema }}.v_{{ entity.name }} AS
SELECT
    -- Trinity identifiers
    id,
    {%- if entity.fraiseql.type.trinity %}
    identifier,
    {%- endif %}

    -- JSONB data column (FraiseQL convention)
    jsonb_build_object(
        'id', id::text,
        {%- if entity.fraiseql.type.trinity %}
        'identifier', identifier,
        {%- endif %}
        {%- for field in entity.fraiseql.type.expose_fields %}
        {%- if field not in ['id', 'identifier'] %}
        '{{ field | camel_case }}', {{ field }},
        {%- endif %}
        {%- endfor %}
        'createdAt', created_at,
        'updatedAt', updated_at
    ) AS data

FROM {{ entity.schema }}.tb_{{ entity.name }}
WHERE deleted_at IS NULL;  -- Soft delete filter

-- ============================================================================
-- FraiseQL Metadata Annotations
-- ============================================================================

COMMENT ON VIEW {{ entity.schema }}.v_{{ entity.name }} IS '@fraiseql:type
trinity: {{ entity.fraiseql.type.trinity | lower }}
use_projection: {{ entity.fraiseql.type.use_projection | lower }}
description: {{ entity.description }}';

-- Column descriptions (visible in GraphQL schema)
COMMENT ON COLUMN {{ entity.schema }}.v_{{ entity.name }}.id IS '{{ entity.fields.id.description | default("Public UUID identifier") }}';

{%- for field_name, field_def in entity.fields.items() %}
{%- if field_name in entity.fraiseql.type.expose_fields %}
COMMENT ON COLUMN {{ entity.schema }}.v_{{ entity.name }}.{{ field_name }} IS '{{ field_def.description }}';
{%- endif %}
{%- endfor %}

{%- endif %}
```

**2. `templates/fraiseql_mutation_create.sql.j2`** - Generate CREATE mutations
```jinja2
{%- if entity.fraiseql.enabled and entity.fraiseql.mutations.create.enabled %}

-- ============================================================================
-- FraiseQL Mutation: {{ entity.fraiseql.mutations.create.function_name }}
-- ============================================================================
-- PURPOSE: Create new {{ entity.name }} entity
-- RETURNS: JSONB with success/failure structure
-- USAGE: Called via GraphQL createManufacturer mutation
-- ============================================================================

CREATE OR REPLACE FUNCTION {{ entity.schema }}.{{ entity.fraiseql.mutations.create.function_name }}(
    {%- for field_name in entity.fraiseql.mutations.create.input_fields %}
    {%- set field_def = entity.fields.get(field_name, entity.foreign_keys.get(field_name)) %}
    p_{{ field_name }} {{ field_def.type }}{% if not loop.last %},{% endif %}
    {%- endfor %}
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_{{ entity.name }}_pk INTEGER;
    v_{{ entity.name }}_id UUID;
BEGIN
    -- ========================================================================
    -- Validation
    -- ========================================================================

    {%- for validation in entity.validation %}
    -- {{ validation.name }}
    IF NOT ({{ validation.condition }}) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', '{{ validation.error }}',
            'code', '{{ validation.name | upper }}'
        );
    END IF;
    {%- endfor %}

    -- ========================================================================
    -- Deduplication Check
    -- ========================================================================

    {%- if entity.deduplication %}
    {%- for rule in entity.deduplication.rules %}
    -- Priority {{ rule.priority }}: {{ rule.message }}
    {%- if rule.when %}
    IF {{ rule.when }} THEN
    {%- endif %}
        SELECT pk_{{ entity.name }} INTO v_{{ entity.name }}_pk
        FROM {{ entity.schema }}.tb_{{ entity.name }}
        WHERE {%- for field in rule.fields %}
            {{ field }} = p_{{ field }}{% if not loop.last %} AND {% endif %}
        {%- endfor %}
          AND deleted_at IS NULL
        LIMIT 1;

        IF v_{{ entity.name }}_pk IS NOT NULL THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', '{{ rule.message }}',
                'code', 'DUPLICATE_{{ entity.name | upper }}',
                'existing_id', (SELECT id FROM {{ entity.schema }}.tb_{{ entity.name }} WHERE pk_{{ entity.name }} = v_{{ entity.name }}_pk)
            );
        END IF;
    {%- if rule.when %}
    END IF;
    {%- endif %}
    {%- endfor %}
    {%- endif %}

    -- ========================================================================
    -- Foreign Key Resolution (Trinity Pattern)
    -- ========================================================================

    {%- for fk_name, fk_def in entity.foreign_keys.items() %}
    {%- if fk_name in entity.fraiseql.mutations.create.input_fields %}
    -- Resolve {{ fk_name }} (if provided)
    -- Note: Input should already be INTEGER PK (client uses helper functions)
    {%- endif %}
    {%- endfor %}

    -- ========================================================================
    -- Insert Entity
    -- ========================================================================

    INSERT INTO {{ entity.schema }}.tb_{{ entity.name }} (
        {%- for field_name in entity.fraiseql.mutations.create.input_fields %}
        {{ field_name }}{% if not loop.last %},{% endif %}
        {%- endfor %}
    )
    VALUES (
        {%- for field_name in entity.fraiseql.mutations.create.input_fields %}
        p_{{ field_name }}{% if not loop.last %},{% endif %}
        {%- endfor %}
    )
    RETURNING pk_{{ entity.name }}, id INTO v_{{ entity.name }}_pk, v_{{ entity.name }}_id;

    -- ========================================================================
    -- Return Success
    -- ========================================================================

    RETURN jsonb_build_object(
        'success', true,
        '{{ entity.name | lower }}', (
            SELECT data FROM {{ entity.schema }}.v_{{ entity.name }}
            WHERE id = v_{{ entity.name }}_id
        )
    );

EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'code', 'DATABASE_ERROR'
        );
END;
$$;

-- ============================================================================
-- FraiseQL Mutation Metadata
-- ============================================================================

COMMENT ON FUNCTION {{ entity.schema }}.{{ entity.fraiseql.mutations.create.function_name }} IS '@fraiseql:mutation
input:
{%- for field_name in entity.fraiseql.mutations.create.input_fields %}
{%- set field_def = entity.fields.get(field_name, entity.foreign_keys.get(field_name)) %}
  {{ field_name }}:
    type: {{ field_def.type | pg_to_graphql_type }}
    description: "{{ field_def.description }}"
{%- endfor %}
success: {{ entity.fraiseql.mutations.create.success_type }}
failure: {{ entity.fraiseql.mutations.create.failure_type }}
description: {{ entity.description }}';

{%- endif %}
```

**3. `templates/fraiseql_mutation_update.sql.j2`** - Generate UPDATE mutations
**4. `templates/fraiseql_mutation_delete.sql.j2`** - Generate DELETE mutations

---

### Phase 3: Enhanced Generator Engine

Extend `generate_sql.py` to support FraiseQL generation:

```python
class SQLGenerator:
    def __init__(self, templates_dir='templates',
                 entities_dir='entities',
                 output_dir='generated'):
        # ... existing initialization ...

        # NEW: Create FraiseQL output directories
        (self.output_dir / 'views').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'mutations').mkdir(parents=True, exist_ok=True)

    def generate_entity(self, entity_file):
        """Generate all SQL for one entity (extended)"""
        entity = self.load_entity(entity_file)

        # Existing: Generate table SQL
        table_sql = self.generate_table(entity)
        table_file = self.output_dir / 'tables' / f'tb_{entity["name"]}.sql'
        table_file.write_text(table_sql)

        # Existing: Generate trinity helpers
        if entity.get('trinity_helpers', {}).get('generate'):
            trinity_sql = self.generate_trinity_helpers(entity)
            trinity_file = self.output_dir / 'functions' / f'{entity["name"]}_trinity_helpers.sql'
            trinity_file.write_text(trinity_sql)

        # NEW: Generate FraiseQL artifacts
        if entity.get('fraiseql', {}).get('enabled'):
            self.generate_fraiseql_artifacts(entity)

    def generate_fraiseql_artifacts(self, entity):
        """Generate FraiseQL-specific SQL artifacts"""

        # 1. Generate view (for type)
        if entity['fraiseql']['type']['generate_view']:
            view_sql = self.generate_fraiseql_view(entity)
            view_file = self.output_dir / 'views' / f'v_{entity["name"]}.sql'
            view_file.write_text(view_sql)

        # 2. Generate CREATE mutation
        if entity['fraiseql']['mutations']['create']['enabled']:
            create_sql = self.generate_fraiseql_mutation_create(entity)
            create_file = self.output_dir / 'mutations' / f'{entity["fraiseql"]["mutations"]["create"]["function_name"]}.sql'
            create_file.write_text(create_sql)

        # 3. Generate UPDATE mutation
        if entity['fraiseql']['mutations']['update']['enabled']:
            update_sql = self.generate_fraiseql_mutation_update(entity)
            update_file = self.output_dir / 'mutations' / f'{entity["fraiseql"]["mutations"]["update"]["function_name"]}.sql'
            update_file.write_text(update_sql)

        # 4. Generate DELETE mutation
        if entity['fraiseql']['mutations']['delete']['enabled']:
            delete_sql = self.generate_fraiseql_mutation_delete(entity)
            delete_file = self.output_dir / 'mutations' / f'{entity["fraiseql"]["mutations"]["delete"]["function_name"]}.sql'
            delete_file.write_text(delete_sql)

    def generate_fraiseql_view(self, entity):
        """Render fraiseql_view.sql.j2 template"""
        template = self.env.get_template('fraiseql_view.sql.j2')
        return template.render(entity=entity)

    def generate_fraiseql_mutation_create(self, entity):
        """Render fraiseql_mutation_create.sql.j2 template"""
        template = self.env.get_template('fraiseql_mutation_create.sql.j2')
        return template.render(entity=entity)

    # ... similar for update/delete mutations
```

---

### Phase 4: Generated Output Structure

After integration, the generator will produce:

```
generated/
├── tables/                          # Existing: Table definitions
│   └── tb_manufacturer.sql
│
├── functions/                       # Existing: Trinity helpers
│   └── manufacturer_trinity_helpers.sql
│
├── views/                           # NEW: FraiseQL type views
│   └── v_manufacturer.sql           # With @fraiseql:type annotation
│
└── mutations/                       # NEW: FraiseQL mutation functions
    ├── fn_create_manufacturer.sql   # With @fraiseql:mutation annotation
    ├── fn_update_manufacturer.sql
    └── fn_delete_manufacturer.sql
```

---

### Phase 5: FraiseQL Backend Integration

Create FraiseQL application that auto-discovers generated schema:

```python
# app.py - FraiseQL Backend
from fraiseql.fastapi import create_fraiseql_app

app = create_fraiseql_app(
    database_url="postgresql://localhost/printoptim",

    # Enable auto-discovery
    auto_discover=True,

    # Auto-discovery configuration
    auto_discover_types=True,        # Discover v_* views as types
    auto_discover_queries=True,       # Generate find/findOne queries
    auto_discover_mutations=True,     # Discover fn_* functions as mutations

    # Source patterns
    view_pattern="v_%",               # Views for types
    function_pattern="fn_%",          # Functions for mutations

    # Schema to introspect
    introspection_schema="catalog",   # Match YAML schema

    # Naming conventions (match YAML camelCase)
    strip_view_prefixes=True,         # v_manufacturer → Manufacturer
    pascal_case_types=True,           # manufacturer → Manufacturer
    camel_case_fields=True,           # created_at → createdAt

    # Source priority (use views, not projection tables)
    source_priority=["v", "tv"],      # Prefer v_* (real-time)
)
```

**Result**: GraphQL API is fully generated from database introspection!

---

## 📋 Detailed Requirements

### REQ-1: YAML Schema Extension

**Priority**: Critical
**Effort**: 4 hours

**Description**: Extend YAML entity schema to include FraiseQL configuration

**Acceptance Criteria**:
- [ ] YAML supports `fraiseql.enabled` flag
- [ ] YAML supports `fraiseql.type` configuration (view generation)
- [ ] YAML supports `fraiseql.queries` configuration (query types)
- [ ] YAML supports `fraiseql.mutations` configuration (CRUD operations)
- [ ] YAML supports per-field `fraiseql.filter_operators` and `fraiseql.sortable`
- [ ] Backward compatible with existing YAML entities (fraiseql section optional)
- [ ] Documented with examples in README

---

### REQ-2: FraiseQL View Template

**Priority**: Critical
**Effort**: 8 hours

**Description**: Create Jinja2 template to generate FraiseQL-compatible views

**Acceptance Criteria**:
- [ ] Template generates `CREATE VIEW v_[entity]` with JSONB data column
- [ ] Template includes Trinity Pattern (id, identifier columns)
- [ ] Template generates `COMMENT ON VIEW` with `@fraiseql:type` annotation
- [ ] Template generates `COMMENT ON COLUMN` for each exposed field
- [ ] Template supports field selection (expose_fields configuration)
- [ ] Template handles soft delete filtering (WHERE deleted_at IS NULL)
- [ ] Generated view is valid PostgreSQL SQL
- [ ] Generated view is recognized by FraiseQL introspection

---

### REQ-3: FraiseQL Mutation Templates

**Priority**: High
**Effort**: 24 hours (8 hours per template)

**Description**: Create Jinja2 templates for CREATE/UPDATE/DELETE mutations

**Acceptance Criteria**:

**CREATE Mutation:**
- [ ] Template generates `CREATE FUNCTION fn_create_[entity]` with input parameters
- [ ] Template includes validation rules from YAML
- [ ] Template includes deduplication checks from YAML
- [ ] Template includes Trinity Pattern foreign key resolution
- [ ] Template returns JSONB with success/failure structure
- [ ] Template generates `COMMENT ON FUNCTION` with `@fraiseql:mutation` annotation
- [ ] Template handles errors gracefully (EXCEPTION block)

**UPDATE Mutation:**
- [ ] Template generates `CREATE FUNCTION fn_update_[entity]`
- [ ] Template accepts identifier/id for lookup
- [ ] Template updates only specified fields
- [ ] Template validates before updating
- [ ] Template returns JSONB success/failure
- [ ] Template generates proper metadata annotations

**DELETE Mutation:**
- [ ] Template generates `CREATE FUNCTION fn_delete_[entity]`
- [ ] Template supports soft delete (sets deleted_at)
- [ ] Template supports hard delete (optional)
- [ ] Template returns success/failure
- [ ] Template generates proper metadata annotations

---

### REQ-4: Enhanced SQL Generator

**Priority**: High
**Effort**: 12 hours

**Description**: Extend `generate_sql.py` to support FraiseQL artifact generation

**Acceptance Criteria**:
- [ ] Generator creates `generated/views/` directory
- [ ] Generator creates `generated/mutations/` directory
- [ ] Generator calls `generate_fraiseql_view()` when `fraiseql.enabled=true`
- [ ] Generator calls mutation templates when mutations enabled
- [ ] Generator validates YAML fraiseql section (schema validation)
- [ ] Generator logs what FraiseQL artifacts are generated
- [ ] Generator handles missing fraiseql section gracefully (skips)
- [ ] Generator supports dry-run mode (preview without writing files)

---

### REQ-5: FraiseQL Backend Integration

**Priority**: High
**Effort**: 8 hours

**Description**: Create FraiseQL application that auto-discovers generated schema

**Acceptance Criteria**:
- [ ] `app.py` creates FraiseQL app with auto-discovery enabled
- [ ] App successfully introspects generated views as types
- [ ] App successfully introspects generated functions as mutations
- [ ] App generates GraphQL schema with correct types
- [ ] App generates queries: `find`, `findOne`, `connection`
- [ ] App generates mutations from annotated functions
- [ ] App generates WhereInput filters automatically
- [ ] App generates OrderByInput for sortable fields
- [ ] GraphQL schema matches YAML entity definitions

---

### REQ-6: Type Mapping Utilities

**Priority**: Medium
**Effort**: 6 hours

**Description**: Create utilities to map PostgreSQL types ↔ GraphQL types

**Acceptance Criteria**:
- [ ] Function `pg_to_graphql_type(pg_type)` maps PostgreSQL → GraphQL
- [ ] Function `graphql_to_pg_type(gql_type)` maps GraphQL → PostgreSQL
- [ ] Supports all common types (TEXT→String, INTEGER→Int, UUID→UUID, etc.)
- [ ] Handles nullable types (adds `!` for non-nullable)
- [ ] Handles array types (`TEXT[]` → `[String!]`)
- [ ] Handles JSONB → JSON
- [ ] Available as Jinja2 filter in templates

**Type Mapping Table**:
| PostgreSQL | GraphQL | Notes |
|------------|---------|-------|
| TEXT | String | |
| VARCHAR | String | |
| INTEGER | Int | |
| BIGINT | BigInt | Custom scalar |
| UUID | UUID | Custom scalar |
| BOOLEAN | Boolean | |
| TIMESTAMPTZ | DateTime | Custom scalar |
| DATE | Date | Custom scalar |
| JSONB | JSON | |
| CHAR(n) | String | |
| TEXT[] | [String!] | Array |

---

### REQ-7: End-to-End Testing

**Priority**: High
**Effort**: 16 hours

**Description**: Validate complete YAML → SQL → GraphQL pipeline

**Test Cases**:

**TC-1: Simple Entity (manufacturer)**
- [ ] Define manufacturer entity in YAML with fraiseql section
- [ ] Run `python generate_sql.py`
- [ ] Verify generated files:
  - `generated/tables/tb_manufacturer.sql`
  - `generated/views/v_manufacturer.sql`
  - `generated/mutations/fn_create_manufacturer.sql`
  - `generated/functions/manufacturer_trinity_helpers.sql`
- [ ] Apply SQL to PostgreSQL database
- [ ] Start FraiseQL app with auto-discovery
- [ ] Verify GraphQL schema includes:
  - Type `Manufacturer`
  - Query `manufacturer(id: UUID)`
  - Query `manufacturers(where: ManufacturerWhereInput)`
  - Mutation `createManufacturer(input: CreateManufacturerInput)`
- [ ] Execute GraphQL queries successfully
- [ ] Execute GraphQL mutations successfully

**TC-2: Entity with Foreign Keys**
- [ ] Define entity with foreign keys (e.g., product → manufacturer)
- [ ] Generate SQL
- [ ] Verify foreign key resolution in mutations
- [ ] Verify GraphQL schema includes relations
- [ ] Test querying related entities

**TC-3: Entity with Translations**
- [ ] Define entity with `translations.enabled=true`
- [ ] Generate SQL including translation table
- [ ] Verify FraiseQL handles translation fields
- [ ] Test i18n queries

**TC-4: Entity with Complex Validation**
- [ ] Define entity with multiple validation rules
- [ ] Generate CREATE mutation
- [ ] Test validation errors via GraphQL
- [ ] Verify error messages match YAML definitions

---

### REQ-8: Documentation

**Priority**: Medium
**Effort**: 8 hours

**Description**: Document the integrated YAML → GraphQL workflow

**Deliverables**:
- [ ] **Tutorial**: "From YAML to GraphQL in 10 Minutes"
  - Define entity in YAML
  - Generate SQL
  - Apply to database
  - Start GraphQL API
  - Execute first query
- [ ] **YAML Schema Reference**: Document all fraiseql configuration options
- [ ] **Template Reference**: Document available Jinja2 templates
- [ ] **Integration Guide**: How to customize generated artifacts
- [ ] **Migration Guide**: Converting existing entities to YAML
- [ ] **Best Practices**: When to use auto-generation vs manual code

---

### REQ-9: Developer Experience Improvements

**Priority**: Low
**Effort**: 8 hours

**Description**: Improve developer workflow and debugging

**Acceptance Criteria**:
- [ ] CLI command: `python generate_sql.py --entity manufacturer --dry-run`
- [ ] CLI command: `python generate_sql.py --validate-yaml` (check YAML syntax)
- [ ] CLI command: `python generate_sql.py --list-entities`
- [ ] Validation errors show line numbers and helpful messages
- [ ] Generator logs summary: "Generated 4 files for manufacturer entity"
- [ ] Generator supports `--verbose` flag for detailed output
- [ ] Generator supports `--watch` mode (regenerate on YAML changes)

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1) - 32 hours

**Goal**: Extend YAML schema and create basic FraiseQL view generation

**Tasks**:
1. ✅ REQ-1: YAML Schema Extension (4 hours)
2. ✅ REQ-2: FraiseQL View Template (8 hours)
3. ✅ REQ-6: Type Mapping Utilities (6 hours)
4. ✅ REQ-4: Enhanced SQL Generator (partial - view generation only) (6 hours)
5. ✅ REQ-7: End-to-End Testing TC-1 (partial - view generation) (8 hours)

**Deliverable**: Generator can produce FraiseQL-compatible views from YAML

---

### Phase 2: Mutations (Week 2) - 40 hours

**Goal**: Add CREATE/UPDATE/DELETE mutation generation

**Tasks**:
1. ✅ REQ-3: FraiseQL Mutation Templates (24 hours)
   - CREATE mutation (8 hours)
   - UPDATE mutation (8 hours)
   - DELETE mutation (8 hours)
2. ✅ REQ-4: Enhanced SQL Generator (complete mutation generation) (6 hours)
3. ✅ REQ-7: End-to-End Testing TC-1 (complete) (10 hours)

**Deliverable**: Generator produces complete SQL schema + mutations from YAML

---

### Phase 3: Integration (Week 3) - 24 hours

**Goal**: Integrate with FraiseQL auto-discovery

**Tasks**:
1. ✅ REQ-5: FraiseQL Backend Integration (8 hours)
2. ✅ REQ-7: End-to-End Testing TC-2, TC-3, TC-4 (16 hours)

**Deliverable**: Full YAML → GraphQL pipeline working end-to-end

---

### Phase 4: Polish (Week 4) - 16 hours

**Goal**: Documentation and developer experience

**Tasks**:
1. ✅ REQ-8: Documentation (8 hours)
2. ✅ REQ-9: Developer Experience Improvements (8 hours)

**Deliverable**: Production-ready system with complete documentation

---

**Total Effort**: ~112 hours (3-4 weeks)

---

## 💡 Example: Complete Workflow

### Step 1: Define Entity in YAML

```yaml
# entities/manufacturer.yaml
entity:
  name: manufacturer
  schema: catalog
  description: "Printer/copier manufacturers"

  fraiseql:
    enabled: true
    type:
      generate_view: true
      trinity: true
      expose_fields: [id, identifier, name, abbreviation]
    mutations:
      create:
        enabled: true
        function_name: fn_create_manufacturer
        input_fields: [identifier, name, abbreviation, color_name]
        success_type: Manufacturer
        failure_type: ValidationError

  fields:
    identifier: { type: TEXT, nullable: false, unique: true }
    name: { type: TEXT, nullable: true }
    abbreviation: { type: CHAR(2), nullable: false, unique: true }
    color_name: { type: TEXT, nullable: false }
```

### Step 2: Generate SQL

```bash
python generate_sql.py
```

**Output**:
```
✅ Generated tables/tb_manufacturer.sql (76 lines)
✅ Generated views/v_manufacturer.sql (42 lines)
✅ Generated mutations/fn_create_manufacturer.sql (95 lines)
✅ Generated functions/manufacturer_trinity_helpers.sql (129 lines)
```

### Step 3: Apply to Database

```bash
psql -f generated/tables/tb_manufacturer.sql
psql -f generated/views/v_manufacturer.sql
psql -f generated/mutations/fn_create_manufacturer.sql
psql -f generated/functions/manufacturer_trinity_helpers.sql
```

### Step 4: Start GraphQL API

```bash
uvicorn app:app --reload
```

### Step 5: Query via GraphQL

```graphql
# Create manufacturer
mutation {
  createManufacturer(input: {
    identifier: "canon"
    name: "Canon Inc."
    abbreviation: "CN"
    colorName: "#E60012"
  }) {
    ... on Manufacturer {
      id
      identifier
      name
    }
    ... on ValidationError {
      message
      code
    }
  }
}

# Query manufacturers
query {
  manufacturers(
    where: { abbreviation: { eq: "CN" } }
  ) {
    id
    identifier
    name
    abbreviation
  }
}
```

**Total Time**: < 10 minutes from YAML to working GraphQL API

---

## 🎯 Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Developer Time** | < 10 minutes | Time from YAML edit to working GraphQL endpoint |
| **Code Generation** | > 95% | Percentage of backend code auto-generated |
| **Boilerplate Reduction** | > 90% | Lines of manual code eliminated |
| **Entity Creation Speed** | < 1 hour | Time to add new entity (YAML + test) |
| **Schema Migration Speed** | < 30 min | Time to regenerate all entities after pattern change |
| **Test Coverage** | > 85% | Coverage of generated SQL code |

### Qualitative Metrics

- ✅ **Developer Satisfaction**: "Easier to define entities in YAML than SQL"
- ✅ **Onboarding Time**: New developers can add entities without deep SQL knowledge
- ✅ **Maintainability**: Single YAML change propagates to all layers
- ✅ **Consistency**: All entities follow exact same patterns
- ✅ **Documentation**: Generated code is self-documenting

---

## 🔄 Future Enhancements (Phase 5+)

### Multi-Database Support
- Generate MySQL DDL from same YAML
- Generate SQLite DDL from same YAML
- Abstract type mapping per database

### Additional Generators
- **TypeScript Types**: YAML → TypeScript interfaces
- **OpenAPI Schema**: YAML → REST API documentation
- **Test Fixtures**: YAML → seed data generators
- **Postman Collections**: YAML → API testing collections

### Advanced FraiseQL Features
- **Subscriptions**: Real-time GraphQL subscriptions from YAML
- **Custom Scalars**: Define custom GraphQL scalars in YAML
- **Computed Fields**: Add derived fields to GraphQL types
- **Field Resolvers**: Custom resolution logic for complex fields

### Developer Tooling
- **VS Code Extension**: YAML syntax highlighting + validation
- **GraphQL Playground**: Integrated API explorer
- **Migration Generator**: Diff YAML changes → generate SQL migrations
- **Visual Entity Designer**: GUI for creating YAML entities

---

## 📊 Risk Assessment

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Template Complexity** | High | Medium | Start simple, iterate. Keep templates focused. |
| **Type Mapping Edge Cases** | Medium | Medium | Comprehensive type mapping tests. |
| **FraiseQL Integration Issues** | High | Low | Close collaboration with FraiseQL development. |
| **Performance at Scale** | Medium | Low | Projection tables (tv_*) for performance-critical paths. |
| **Breaking Changes** | Medium | Medium | Version templates, maintain backward compatibility. |

### Process Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Learning Curve** | Medium | Medium | Comprehensive documentation and examples. |
| **Adoption Resistance** | Low | Low | Show clear time savings in demos. |
| **Template Maintenance** | Medium | Medium | Centralized template repository, versioning. |

---

## 📝 Open Questions

### Q1: Hybrid Approach Support?
**Question**: Should we support hybrid entities (some manual SQL + some YAML)?
**Options**:
- A) Full YAML-only (strict)
- B) Allow manual SQL overrides
- C) Support partial generation (e.g., just views, manual mutations)

**Recommendation**: Option C - Allow partial generation for flexibility

---

### Q2: YAML Validation Strategy?
**Question**: How to validate YAML before generation?
**Options**:
- A) JSON Schema validation
- B) Python Pydantic models
- C) Custom validator

**Recommendation**: Option B - Pydantic models provide best error messages and IDE support

---

### Q3: Migration Path for Existing Entities?
**Question**: How to convert 40+ existing entities to YAML?
**Options**:
- A) Manual conversion (slow but accurate)
- B) Reverse-engineer from SQL (automated but risky)
- C) Gradual migration (new entities use YAML, old entities stay SQL)

**Recommendation**: Option C - Gradual migration minimizes risk

---

### Q4: FraiseQL Customization?
**Question**: How to handle custom business logic not in YAML?
**Options**:
- A) Generate stubs, developers fill in logic
- B) Support inline SQL/PL/pgSQL in YAML
- C) Keep complex logic in separate manual files

**Recommendation**: Option C - Separation of concerns, YAML for structure only

---

## ✅ Acceptance Criteria (Overall)

The integration is complete when:

1. ✅ A developer can define an entity in YAML with FraiseQL configuration
2. ✅ Running `python generate_sql.py` produces:
   - PostgreSQL table DDL
   - FraiseQL-annotated view
   - CREATE/UPDATE/DELETE mutation functions
   - Trinity helper functions
3. ✅ Applying generated SQL to PostgreSQL works without errors
4. ✅ FraiseQL app auto-discovers the schema and generates GraphQL API
5. ✅ GraphQL queries and mutations work end-to-end
6. ✅ The generated GraphQL schema matches YAML entity definitions
7. ✅ Documentation exists showing the complete workflow
8. ✅ At least 3 example entities demonstrate the full pipeline
9. ✅ Tests validate correctness of generated SQL and GraphQL
10. ✅ Time savings of > 90% are demonstrated vs. manual approach

---

## 🎓 Appendix A: YAML Schema Specification

### Complete YAML Entity Schema

```yaml
entity:
  # === Core Metadata ===
  name: string                       # Required: entity name (snake_case)
  schema: string                     # Required: PostgreSQL schema (e.g., "catalog")
  table_code: string                 # Optional: numeric table identifier
  description: string                # Required: entity description

  # === FraiseQL Integration ===
  fraiseql:
    enabled: boolean                 # Enable FraiseQL generation

    type:
      generate_view: boolean         # Generate v_[entity] view
      trinity: boolean               # Use trinity pattern (id + identifier)
      use_projection: boolean        # Prefer tv_* over v_* (performance)
      expose_fields: [string]        # Fields to include in GraphQL type

    queries:
      find_one: boolean              # Generate entity(id: UUID) query
      find_one_by_identifier: boolean # Generate entityByIdentifier() query
      find_many: boolean             # Generate entities() query
      connection: boolean            # Generate entitiesConnection() query

    mutations:
      create:
        enabled: boolean
        function_name: string        # PostgreSQL function name
        input_fields: [string]       # Fields in input
        success_type: string         # GraphQL success type
        failure_type: string         # GraphQL failure type

      update:
        enabled: boolean
        function_name: string
        input_fields: [string]
        success_type: string
        failure_type: string

      delete:
        enabled: boolean
        function_name: string
        soft: boolean                # Use deleted_at vs. hard delete
        success_type: string
        failure_type: string

  # === Fields ===
  fields:
    field_name:
      type: string                   # PostgreSQL type (TEXT, INTEGER, UUID, etc.)
      nullable: boolean              # Allow NULL
      unique: boolean                # UNIQUE constraint
      default: string                # Default value
      description: string            # Column description
      fraiseql:
        filter_operators: [string]   # Allowed filter operators
        sortable: boolean            # Allow sorting on this field

  # === Foreign Keys ===
  foreign_keys:
    fk_name:
      references: string             # schema.table
      on: string                     # Referenced column
      nullable: boolean
      description: string

  # === Indexes ===
  indexes:
    - columns: [string]
      type: string                   # btree, gin, gist, etc.
      name: string                   # Index name

  # === Validation Rules ===
  validation:
    - name: string                   # Validation rule name
      condition: string              # SQL condition
      error: string                  # Error message

  # === Deduplication ===
  deduplication:
    strategy: string                 # identifier_based, uuid_based, etc.
    rules:
      - fields: [string]
        when: string                 # Optional condition
        priority: integer
        message: string

  # === Operations ===
  operations:
    create: boolean
    update: boolean
    delete: soft | true | false      # Soft delete or hard delete
    recalcid: boolean

  # === Trinity Helpers ===
  trinity_helpers:
    generate: boolean
    lookup_by: string                # Field for pk lookup (e.g., "identifier")
    helpers:
      - name: string
        params: [string]
        returns: string
        description: string

  # === Translations (i18n) ===
  translations:
    enabled: boolean
    table_name: string
    fields: [string]                 # Translatable fields

  # === Notes ===
  notes: string                      # Additional documentation
```

---

## 🎓 Appendix B: Template Filter Reference

### Custom Jinja2 Filters

```python
# Available in templates as {{ value | filter_name }}

@jinja2_filter
def camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

@jinja2_filter
def pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase"""
    return ''.join(x.title() for x in snake_str.split('_'))

@jinja2_filter
def pg_to_graphql_type(pg_type: str) -> str:
    """Map PostgreSQL type to GraphQL type"""
    mapping = {
        'TEXT': 'String',
        'VARCHAR': 'String',
        'CHAR': 'String',
        'INTEGER': 'Int',
        'BIGINT': 'BigInt',
        'UUID': 'UUID',
        'BOOLEAN': 'Boolean',
        'TIMESTAMPTZ': 'DateTime',
        'DATE': 'Date',
        'JSONB': 'JSON',
        'NUMERIC': 'Decimal',
    }
    return mapping.get(pg_type.upper(), 'String')

@jinja2_filter
def sql_safe(value: str) -> str:
    """Escape single quotes for SQL strings"""
    return value.replace("'", "''")
```

---

**END OF REQUIREMENTS DOCUMENT**
