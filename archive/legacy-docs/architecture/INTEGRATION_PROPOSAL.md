# Integration Proposal: Numbering System + Group Leader Pattern + FraiseQL

**Date**: November 8, 2025
**Status**: Proposal
**Integration Goal**: Unified YAML → Numbered DDL → FraiseQL GraphQL with Group Leader Pattern

---

## Executive Summary

This proposal integrates **three powerful concepts** into the YAML-to-SQL templating system:

1. **Materialized Numbering System** (from printoptim_backend/db/)
2. **Group Leader Pattern** (from TestFoundry)
3. **FraiseQL Integration** (from FRAISEQL_INTEGRATION_REQUIREMENTS.md)

**Result**: A production-ready, AI-discoverable, self-organizing backend generation pipeline.

---

## 1. Materialized Numbering System Integration

### Current Pattern Analysis

From `../printoptim_backend/db/`, the numbering system follows:

```
Level 1 (Top):     0_schema/, 1_seed_common/, 2_seed_backend/
Level 2 (Schema):  00_common/, 01_write_side/, 02_query_side/, 03_functions/
Level 3 (Domain):  010_i18n/, 011_common_dim/, 013_catalog/, 014_dim/
Level 4 (Group):   0132_manufacturer/, 0141_location/
Level 5 (Entity):  01321_manufacturer/
Level 6 (Files):   013211_tb_manufacturer.sql, 013212_fn_manufacturer_pk.sql
```

### Enhanced YAML Schema

```yaml
entity:
  name: manufacturer
  schema: catalog
  description: "Printer/copier manufacturers"

  # ============================================================================
  # NEW: Numbering & Organization
  # ============================================================================
  organization:
    # Materialized numbering (6-digit hierarchical code)
    table_code: "013211"         # Used for all file prefixes

    # Directory structure (auto-generated from table_code)
    schema_layer: "01"            # write_side (01), query_side (02), functions (03)
    domain_code: "013"            # catalog domain
    entity_group_code: "0132"     # manufacturer group
    entity_code: "01321"          # specific manufacturer entity

    # Alternative: Let generator parse table_code automatically
    # parse_table_code: true      # Auto-extract: 01|3|2|1|1

    # Execution order metadata
    execution_order: 13211        # Numeric for sorting
    depends_on:                   # Dependencies (lower numbers)
      - "012111"                  # organization table
      - "010111"                  # language table

  # ============================================================================
  # Group Leader Pattern (TestFoundry Integration)
  # ============================================================================
  field_groups:
    # Define groups of fields that must be generated together
    - group_name: "location_coherence"
      group_leader: "country"     # This field triggers group generation
      dependent_fields:           # These fields come from same source record
        - postal_code
        - city_code
        - administrative_unit
      description: "Ensures postal codes, cities, and countries match"

    - group_name: "manufacturer_company"
      group_leader: "fk_company"
      dependent_fields:
        - company_country
        - company_address
      description: "Links manufacturer to company location"

  # ============================================================================
  # Fields (with Group Leader annotations)
  # ============================================================================
  fields:
    identifier:
      type: TEXT
      nullable: false
      unique: true
      description: "Internal stable identifier (e.g., 'canon', 'ricoh')"

      # NEW: Group leader configuration
      group_leader: false         # Not a group leader
      generator_group: null       # Not part of a group

      # FraiseQL metadata
      fraiseql:
        filter_operators: [eq, neq, in, nin, contains, startsWith, endsWith]
        sortable: true

    name:
      type: TEXT
      nullable: true
      description: "Display name"

    abbreviation:
      type: CHAR(2)
      nullable: false
      unique: true
      description: "2-letter code"

    color_name:
      type: TEXT
      nullable: false
      description: "CSS color for UI"

  # ============================================================================
  # Foreign Keys (with Group Leader support)
  # ============================================================================
  foreign_keys:
    fk_company:
      references: management.tb_organization
      on: pk_organization
      nullable: true
      description: "Company entity link"

      # NEW: Group leader configuration
      group_leader: true                    # This FK is a group leader
      generator_group: "manufacturer_company"
      group_dependency_fields:              # Fields to fetch with this FK
        - company_country                   # Will be populated from same record
        - company_address

      # TestFoundry FK mapping
      testfoundry:
        mapping_key: "organization"
        from_expression: "management.tb_organization"
        select_field: "pk_organization"
        random_pk_field: "pk_organization"
        random_value_field: "name"
        random_select_where: "deleted_at IS NULL"

  # ============================================================================
  # FraiseQL Integration
  # ============================================================================
  fraiseql:
    enabled: true

    type:
      generate_view: true
      trinity: true
      use_projection: false
      expose_fields: [id, identifier, name, abbreviation, color_name]

    queries:
      find_one: true
      find_one_by_identifier: true
      find_many: true
      connection: true

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
        soft: true
        success_type: DeleteResult
        failure_type: ValidationError

  # ============================================================================
  # Trinity Helpers
  # ============================================================================
  trinity_helpers:
    generate: true
    lookup_by: identifier
    helpers:
      - name: manufacturer_pk
        params: [identifier]
        returns: INTEGER
        description: "Resolve identifier to PK"

      - name: manufacturer_id
        params: [pk_manufacturer]
        returns: UUID
        description: "Resolve PK to UUID"

  # ============================================================================
  # TestFoundry Integration
  # ============================================================================
  testfoundry:
    enabled: true

    # Input type mapping
    input_type: "manufacturer_input"

    # Field mappings for test generation
    field_mappings:
      identifier:
        generator_type: random
        random_function: testfoundry_random_identifier
        required: true

      name:
        generator_type: random
        random_function: testfoundry_random_company_name
        required: false

      abbreviation:
        generator_type: random
        random_function: testfoundry_random_abbreviation
        required: true

      fk_company:
        generator_type: resolve_fk
        fk_mapping_key: organization
        required: false
        group_leader: true                    # Triggers group generation
        group_dependency_fields: [company_country, company_address]

    # Test scenarios to generate
    test_scenarios:
      - happy_create
      - duplicate_create
      - fk_violation
      - soft_delete
      - authorization
```

---

## 2. Generated Output Structure

With numbering + group leaders + FraiseQL:

```
generated/
├── manifest.yaml                           # Execution order manifest
├── README.md                               # Auto-generated overview
│
├── 01_write_side/                          # Schema layer 01
│   └── 013_catalog/                        # Domain 013
│       └── 0132_manufacturer/              # Entity group 0132
│           ├── README.md                   # Auto-generated entity docs
│           │
│           └── 01321_manufacturer/         # Specific entity 01321
│               ├── 013211_tb_manufacturer.sql              # Table
│               ├── 013212_fn_manufacturer_pk.sql           # Trinity helper
│               ├── 013213_fn_manufacturer_id.sql           # Trinity helper
│               ├── 013214_fn_manufacturer_name.sql         # Trinity helper
│               └── 013215_fn_manufacturer_abbreviation.sql # Trinity helper
│
├── 02_query_side/                          # Schema layer 02
│   └── 023_catalog/                        # Domain 023 (query side)
│       └── 0232_manufacturer/
│           └── 02321_manufacturer/
│               └── 023211_v_manufacturer.sql               # FraiseQL view
│
├── 03_functions/                           # Schema layer 03
│   └── 033_catalog/                        # Domain 033 (functions)
│       └── 0332_manufacturer/
│           └── 03321_manufacturer_mutations/
│               ├── 033211_fn_create_manufacturer.sql       # CREATE mutation
│               ├── 033212_fn_update_manufacturer.sql       # UPDATE mutation
│               └── 033213_fn_delete_manufacturer.sql       # DELETE mutation
│
└── 09_testfoundry/                         # Schema layer 09 (testing)
    └── 093_catalog/
        └── 0932_manufacturer/
            └── 09321_manufacturer_tests/
                ├── 093211_test_happy_create.sql            # Happy path test
                ├── 093212_test_duplicate_create.sql        # Duplicate test
                ├── 093213_test_fk_violation.sql            # FK test
                └── 093214_metadata_mappings.sql            # TestFoundry metadata
```

---

## 3. Manifest Generation

Auto-generated `manifest.yaml` for execution order:

```yaml
# Auto-generated by scripts/dev/generate_sql.py
# DO NOT EDIT MANUALLY

metadata:
  generated_at: "2025-11-08T11:30:00Z"
  generator_version: "2.0.0"
  total_entities: 1
  total_files: 15

execution_order:
  # Tables first (layer 01)
  - code: "013211"
    path: "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql"
    entity: manufacturer
    type: table
    schema: catalog
    layer: write_side
    dependencies: []

  # Trinity helpers (layer 01)
  - code: "013212"
    path: "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013212_fn_manufacturer_pk.sql"
    entity: manufacturer
    type: function
    schema: core
    layer: write_side
    dependencies: ["013211"]

  - code: "013213"
    path: "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013213_fn_manufacturer_id.sql"
    entity: manufacturer
    type: function
    schema: core
    layer: write_side
    dependencies: ["013211"]

  # Views second (layer 02)
  - code: "023211"
    path: "02_query_side/023_catalog/0232_manufacturer/02321_manufacturer/023211_v_manufacturer.sql"
    entity: manufacturer
    type: view
    schema: catalog
    layer: query_side
    dependencies: ["013211"]

  # Mutations third (layer 03)
  - code: "033211"
    path: "03_functions/033_catalog/0332_manufacturer/03321_manufacturer_mutations/033211_fn_create_manufacturer.sql"
    entity: manufacturer
    type: mutation
    schema: catalog
    layer: functions
    dependencies: ["013211", "023211"]

  # Tests last (layer 09)
  - code: "093211"
    path: "09_testfoundry/093_catalog/0932_manufacturer/09321_manufacturer_tests/093211_test_happy_create.sql"
    entity: manufacturer
    type: test
    schema: testfoundry
    layer: testing
    dependencies: ["033211"]

# Entity index for AI discoverability
entities:
  manufacturer:
    table_code: "013211"
    schema: catalog
    domain: catalog
    description: "Printer/copier manufacturers"

    files:
      table: "013211_tb_manufacturer.sql"

      trinity_helpers:
        - "013212_fn_manufacturer_pk.sql"
        - "013213_fn_manufacturer_id.sql"
        - "013214_fn_manufacturer_name.sql"
        - "013215_fn_manufacturer_abbreviation.sql"

      views:
        - "023211_v_manufacturer.sql"

      mutations:
        - "033211_fn_create_manufacturer.sql"
        - "033212_fn_update_manufacturer.sql"
        - "033213_fn_delete_manufacturer.sql"

      tests:
        - "093211_test_happy_create.sql"
        - "093212_test_duplicate_create.sql"
        - "093213_test_fk_violation.sql"
        - "093214_metadata_mappings.sql"

    dependencies:
      - organization
      - language

    dependents:
      - product
      - accessory

    field_groups:
      - name: manufacturer_company
        leader: fk_company
        members: [company_country, company_address]
```

---

## 4. Group Leader Pattern Implementation

### In Table Template

```jinja2
{# templates/table.sql.j2 #}

-- ============================================================================
-- Table: {{ entity.schema }}.tb_{{ entity.name }}
-- Code: {{ entity.organization.table_code }}
-- ============================================================================

CREATE TABLE {{ entity.schema }}.tb_{{ entity.name }} (
    pk_{{ entity.name }} INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() NOT NULL,

    -- Business Fields
    {%- for field_name, field_def in entity.fields.items() %}
    {{ field_name }} {{ field_def.type }}{% if not field_def.nullable %} NOT NULL{% endif %},
    {%- endfor %}

    -- Foreign Keys
    {%- for fk_name, fk_def in entity.foreign_keys.items() %}
    {{ fk_name }} INTEGER{% if not fk_def.nullable %} NOT NULL{% endif %},
    {%- endfor %}

    -- Group Leader Dependent Fields (auto-populated by triggers)
    {%- for group in entity.field_groups %}
    {%- for dep_field in group.dependent_fields %}
    {{ dep_field }} TEXT,  -- Populated by group leader {{ group.group_leader }}
    {%- endfor %}
    {%- endfor %}

    -- Audit Fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

{%- if entity.field_groups %}

-- ============================================================================
-- Group Leader Triggers
-- ============================================================================

{%- for group in entity.field_groups %}

-- Group: {{ group.group_name }}
-- Leader: {{ group.group_leader }}
-- Dependents: {{ group.dependent_fields | join(', ') }}

CREATE OR REPLACE FUNCTION {{ entity.schema }}.fn_populate_{{ group.group_name }}()
RETURNS TRIGGER AS $$
DECLARE
    v_source_record RECORD;
BEGIN
    -- When {{ group.group_leader }} is set, fetch dependent fields from source
    IF NEW.{{ group.group_leader }} IS NOT NULL THEN
        SELECT
            {%- for dep_field in group.dependent_fields %}
            {{ dep_field }}{% if not loop.last %},{% endif %}
            {%- endfor %}
        INTO v_source_record
        FROM {{ entity.foreign_keys[group.group_leader].references }}
        WHERE {{ entity.foreign_keys[group.group_leader].on }} = NEW.{{ group.group_leader }};

        -- Populate dependent fields
        {%- for dep_field in group.dependent_fields %}
        NEW.{{ dep_field }} := v_source_record.{{ dep_field }};
        {%- endfor %}
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_populate_{{ group.group_name }}
    BEFORE INSERT OR UPDATE ON {{ entity.schema }}.tb_{{ entity.name }}
    FOR EACH ROW
    EXECUTE FUNCTION {{ entity.schema }}.fn_populate_{{ group.group_name }}();

{%- endfor %}
{%- endif %}
```

### In TestFoundry Metadata Template

```jinja2
{# templates/testfoundry_metadata.sql.j2 #}

-- ============================================================================
-- TestFoundry Metadata: {{ entity.name }}
-- Code: 09{{ entity.organization.table_code[2:] }}
-- ============================================================================

-- Input field mappings
INSERT INTO testfoundry.testfoundry_tb_input_field_mapping
(input_type, field_name, generator_type, fk_mapping_key, random_function, required,
 generator_group, group_leader, group_dependency_fields)
VALUES
{%- for field_name, field_mapping in entity.testfoundry.field_mappings.items() %}
(
    '{{ entity.testfoundry.input_type }}',
    '{{ field_name }}',
    '{{ field_mapping.generator_type }}',
    {{ "'" + field_mapping.fk_mapping_key + "'" if field_mapping.fk_mapping_key else 'NULL' }},
    {{ "'" + field_mapping.random_function + "'" if field_mapping.random_function else 'NULL' }},
    {{ field_mapping.required | default(true) }},
    {{ "'" + field_mapping.generator_group + "'" if field_mapping.generator_group else 'NULL' }},
    {{ field_mapping.group_leader | default(false) }},
    {{ 'ARRAY[' + (field_mapping.group_dependency_fields | map('quote') | join(', ')) + ']' if field_mapping.group_dependency_fields else 'NULL' }}
){% if not loop.last %},{% endif %}
{%- endfor %};

COMMENT ON TABLE testfoundry.testfoundry_tb_input_field_mapping IS
'TestFoundry metadata for {{ entity.name }} - auto-generated from YAML';
```

---

## 5. AI Discoverability Features

### Auto-Generated README per Entity

```markdown
# 01321 - Manufacturer

**Table Code**: 013211
**Schema**: catalog
**Layer**: write_side
**Domain**: catalog (013)

## Description

Lists recognized printer/copier manufacturers (e.g., Canon, HP, Xerox), with internal
identifiers and display attributes.

## Files

### Tables (01_write_side)
- `013211_tb_manufacturer.sql` - Base table definition with Trinity pattern

### Trinity Helpers (01_write_side)
- `013212_fn_manufacturer_pk.sql` - Resolve identifier → INTEGER PK
- `013213_fn_manufacturer_id.sql` - Resolve PK → UUID
- `013214_fn_manufacturer_name.sql` - Resolve PK → display name
- `013215_fn_manufacturer_abbreviation.sql` - Resolve PK → abbreviation

### Views (02_query_side)
- `023211_v_manufacturer.sql` - FraiseQL GraphQL type view

### Mutations (03_functions)
- `033211_fn_create_manufacturer.sql` - Create new manufacturer
- `033212_fn_update_manufacturer.sql` - Update existing manufacturer
- `033213_fn_delete_manufacturer.sql` - Soft delete manufacturer

### Tests (09_testfoundry)
- `093211_test_happy_create.sql` - Happy path creation test
- `093212_test_duplicate_create.sql` - Duplicate identifier test
- `093213_test_fk_violation.sql` - Foreign key violation test
- `093214_metadata_mappings.sql` - TestFoundry field mappings

## Dependencies

This entity depends on:
- `012111` - management.tb_organization (for fk_company)
- `010111` - i18n.tb_language (for translations)

## Dependents

These entities depend on manufacturer:
- `014311` - catalog.tb_product
- `013311` - catalog.tb_accessory

## Field Groups

### manufacturer_company
**Group Leader**: `fk_company`
**Dependent Fields**: `company_country`, `company_address`
**Purpose**: Ensures manufacturer company data is coherent

When `fk_company` is set, the following fields are automatically populated from the
organization record:
- `company_country` - Country of the company
- `company_address` - Address of the company

This prevents impossible combinations like a Canon manufacturer with HP company location.

## GraphQL API

### Queries
- `manufacturer(id: UUID!)` - Find one by UUID
- `manufacturerByIdentifier(identifier: String!)` - Find one by identifier
- `manufacturers(where: ManufacturerWhereInput)` - Find many with filters
- `manufacturersConnection(...)` - Paginated query with cursors

### Mutations
- `createManufacturer(input: CreateManufacturerInput!)` - Create new
- `updateManufacturer(id: UUID!, input: UpdateManufacturerInput!)` - Update existing
- `deleteManufacturer(id: UUID!)` - Soft delete

## Execution Order

Apply SQL files in this order:

1. `013211_tb_manufacturer.sql` (table first)
2. `013212_fn_manufacturer_pk.sql` (trinity helpers)
3. `013213_fn_manufacturer_id.sql`
4. `013214_fn_manufacturer_name.sql`
5. `013215_fn_manufacturer_abbreviation.sql`
6. `023211_v_manufacturer.sql` (view)
7. `033211_fn_create_manufacturer.sql` (mutations)
8. `033212_fn_update_manufacturer.sql`
9. `033213_fn_delete_manufacturer.sql`
10. `093211_test_happy_create.sql` (tests)
11. `093212_test_duplicate_create.sql`
12. `093213_test_fk_violation.sql`
13. `093214_metadata_mappings.sql`

## Generated

This documentation was auto-generated from `entities/manufacturer.yaml` on 2025-11-08.
```

---

## 6. Implementation Roadmap

### Phase 1: Numbering System (Week 1)

**Tasks**:
1. Extend YAML schema with `organization` section
2. Create `NumberingParser` class to parse table_code
3. Update `SQLGenerator` to create directory hierarchy
4. Generate `manifest.yaml` from all entities
5. Generate entity README.md files

**Deliverable**: Hierarchical output with numbered files

### Phase 2: Group Leader Pattern (Week 2)

**Tasks**:
1. Extend YAML schema with `field_groups` section
2. Create `group_leader_trigger.sql.j2` template
3. Update table template to include dependent fields
4. Generate TestFoundry metadata with group leaders
5. Create validation for group leader consistency

**Deliverable**: Group leader triggers generated

### Phase 3: TestFoundry Integration (Week 3)

**Tasks**:
1. Extend YAML schema with `testfoundry` section
2. Create `testfoundry_metadata.sql.j2` template
3. Create `testfoundry_test_happy_create.sql.j2` template
4. Create `testfoundry_test_duplicate.sql.j2` template
5. Generate complete test suite

**Deliverable**: Full test generation from YAML

### Phase 4: Documentation & Polish (Week 4)

**Tasks**:
1. Auto-generate entity README.md
2. Auto-generate top-level README.md
3. Create migration guide from existing entities
4. Add CLI commands for validation
5. Complete integration testing

**Deliverable**: Production-ready system

---

## 7. Benefits Summary

### For AI Discoverability

✅ **Hierarchical paths** tell the complete story
✅ **Numbered files** ensure execution order
✅ **Auto-generated manifests** provide programmatic access
✅ **Entity READMEs** give context at every level
✅ **Cross-reference index** enables dependency tracking

### For Data Integrity

✅ **Group leader pattern** prevents impossible data combinations
✅ **Automatic population** of dependent fields via triggers
✅ **Test generation** validates group leader behavior
✅ **Declarative configuration** in YAML

### For Development Speed

✅ **Single YAML source** generates 15+ files
✅ **Complete test suite** auto-generated
✅ **FraiseQL integration** gives instant GraphQL API
✅ **Trinity helpers** auto-generated
✅ **Documentation** auto-generated

### For Maintainability

✅ **One place to change** (YAML)
✅ **Consistent patterns** across all entities
✅ **Version controlled** manifests
✅ **Clear dependencies** in manifest
✅ **Migration tools** for existing entities

---

## 8. Example: Complete Workflow

### Step 1: Define in YAML (5 minutes)

```yaml
# entities/manufacturer.yaml
entity:
  name: manufacturer
  organization:
    table_code: "013211"
  field_groups:
    - group_name: "manufacturer_company"
      group_leader: "fk_company"
      dependent_fields: [company_country, company_address]
  # ... rest of entity definition
```

### Step 2: Generate (30 seconds)

```bash
python scripts/dev/generate_sql.py --entity manufacturer
```

**Output**:
```
✅ Generated 15 files for manufacturer entity
✅ Created directory hierarchy: 01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/
✅ Generated manifest.yaml with execution order
✅ Generated entity README.md
```

### Step 3: Apply to Database (2 minutes)

```bash
# Use manifest for correct execution order
python apply_manifest.py --manifest generated/manifest.yaml
```

### Step 4: Start GraphQL API (1 minute)

```bash
uvicorn app:app --reload
```

### Step 5: Query via GraphQL (instant)

```graphql
mutation {
  createManufacturer(input: {
    identifier: "canon"
    name: "Canon Inc."
    abbreviation: "CN"
    colorName: "#E60012"
    fkCompany: 42  # Group leader triggers population of:
                   # - company_country
                   # - company_address
  }) {
    ... on Manufacturer {
      id
      identifier
      companyCountry  # Auto-populated!
      companyAddress  # Auto-populated!
    }
  }
}
```

**Total Time**: < 10 minutes from YAML to working GraphQL API with group leader validation!

---

## 9. Next Steps

Would you like me to:

1. **Implement the numbering system** integration first?
2. **Implement the group leader pattern** integration?
3. **Create a complete example** with manufacturer entity?
4. **Build the manifest generator** first?
5. **All of the above** in phased approach?

Let me know which direction you'd like to take, and I can start implementing immediately!
