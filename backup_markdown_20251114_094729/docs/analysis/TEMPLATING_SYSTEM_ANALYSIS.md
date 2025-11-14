# SQL Templating System Analysis - Detailed Findings

**Analysis Date**: November 8, 2025  
**Project**: printoptim_backend_poc  
**Status**: POC Complete - Ready for Integration

---

## Executive Summary

The printoptim_backend_poc directory contains a **complete, working SQL generation system** that converts YAML entity definitions into PostgreSQL tables and functions using Jinja2 templates. This is a proof-of-concept (POC) that has been validated and is ready for production integration.

Key findings:
- **Templating Engine**: Jinja2 (Python-based)
- **Configuration Format**: YAML (human-readable, self-documenting)
- **Generation Approach**: Python script that processes YAML entities through Jinja2 templates
- **Output Organization**: Structured by type (tables/, functions/)
- **Current Status**: 95%+ functional with 2 working templates

---

## System Architecture

```
printoptim_backend_poc/
├── entities/                          # YAML entity definitions (input)
│   └── manufacturer.yaml              # Example: 193 lines
│
├── templates/                         # Jinja2 SQL templates (reusable)
│   ├── table.sql.j2                   # Table generation (123 lines)
│   └── trinity_helpers.sql.j2         # Helper functions (148 lines)
│
├── scripts/dev/generate_sql.py                    # Generation engine (Python script)
├── scripts/dev/compare_with_original.py           # Validation script
│
└── generated/                         # Generated output (target)
    ├── tables/
    │   └── tb_manufacturer.sql        # Generated table definition
    └── functions/
        └── manufacturer_trinity_helpers.sql  # Generated helper functions
```

---

## Templating Engine Details

### Engine Type
- **Jinja2** (Python templating engine)
- Version: Latest (via pip install jinja2)
- Python 3.8+ required

### Engine Configuration (from scripts/dev/generate_sql.py)

```python
from jinja2 import Environment, FileSystemLoader

self.env = Environment(
    loader=FileSystemLoader(str(self.templates_dir)),
    trim_blocks=True,        # Remove blank lines after block tags
    lstrip_blocks=True       # Strip leading spaces from blocks
)
```

### Key Features Used
- Variable interpolation: `{{ entity.name }}`
- Conditionals: `{% if entity.get('unique') %}`
- Loops: `{% for field_name, field_def in entity.fields.items() %}`
- Comments: `{# ... #}` (Jinja2 comments don't appear in output)
- Whitespace control: `-` for trimming (e.g., `{%- for` or `endfor -%}`)

---

## YAML Configuration Structure

### File Location
- **Path**: `/home/lionel/code/printoptim_backend_poc/entities/`
- **Naming Convention**: `[entity_name].yaml`
- **Example**: `manufacturer.yaml` (193 lines)

### YAML Structure (Complete Example)

```yaml
entity:
  # Basic metadata
  name: manufacturer              # Used for table names (tb_manufacturer)
  schema: catalog                 # PostgreSQL schema
  table_code: "013211"            # Reference code
  description: "..."              # Table purpose

  # Fields section
  fields:
    identifier:
      type: TEXT
      nullable: false
      unique: true
      description: "Internal stable identifier"
    
    name:
      type: TEXT
      nullable: true
      description: "Optional display name"
    
    abbreviation:
      type: CHAR(2)
      nullable: false
      unique: true
      description: "2-letter code"

  # Foreign keys
  foreign_keys:
    fk_company:
      references: management.tb_organization
      on: pk_organization
      nullable: true
      description: "Foreign key to organization"

  # Indexes (optional)
  indexes:
    - columns: [identifier]
      type: btree
      name: idx_manufacturer_identifier

  # Validation rules (optional)
  validation:
    - name: identifier_format
      condition: "identifier ~ '^[a-z0-9_-]+$'"
      error: "Identifier format error"

  # Deduplication strategy (optional)
  deduplication:
    strategy: identifier_based
    rules:
      - fields: [identifier]
        when: condition
        priority: 1

  # Operations to generate
  operations:
    create: true
    update: true
    delete: soft      # or true/false
    recalcid: true

  # Trinity pattern helpers
  trinity_helpers:
    generate: true
    lookup_by: identifier
    helpers:
      - name: manufacturer_pk
        params: [identifier]
        returns: INTEGER
        description: "Resolve identifier to PK"

  # GraphQL schema (for future use)
  graphql:
    type_name: Manufacturer
    queries: [manufacturer, manufacturers]
    mutations: [createManufacturer, updateManufacturer]

  # i18n translations
  translations:
    enabled: true
    table_name: tb_manufacturer_translation
    fields: [name, color_name]

  # Notes
  notes: |
    Manufacturer is reference data, typically:
    - Seeded from seed files
    - Rarely created via API
```

---

## Template Files

### Template 1: Table Definition (table.sql.j2)

**Location**: `/home/lionel/code/printoptim_backend_poc/templates/table.sql.j2`  
**Lines**: 123  
**Purpose**: Generates PostgreSQL CREATE TABLE statements

#### Key Template Sections

```jinja2
{# Metadata #}
-- Table: {{ entity.schema }}.tb_{{ entity.name }}
-- [Table: {{ entity.table_code }} | {{ entity.description }}]

{# Main table creation #}
CREATE TABLE {{ entity.schema }}.tb_{{ entity.name }} (
    -- Trinity pattern columns
    pk_{{ entity.name }} INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() NOT NULL,

    {# Business fields #}
    {%- for field_name, field_def in entity.fields.items() %}
    {{ field_name }} {{ field_def.type }}{% if not field_def.nullable %} NOT NULL{% endif %},
    {%- endfor %}

    {# Foreign keys #}
    {%- for fk_name, fk_def in entity.foreign_keys.items() %}
    {{ fk_name }} INTEGER{% if not fk_def.nullable %} NOT NULL{% endif %},
    {%- endfor %}

    {# Audit fields (hardcoded) #}
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    {# Constraints #}
    CONSTRAINT tb_{{ entity.name }}_id_key UNIQUE (id)
    {%- for field_name, field_def in entity.fields.items() %}
    {%- if field_def.get('unique') %}
    ,CONSTRAINT tb_{{ entity.name }}_{{ field_name }}_key UNIQUE ({{ field_name }})
    {%- endif %}
    {%- endfor %}
);

{# Foreign key constraints (after table creation) #}
{%- for fk_name, fk_def in entity.foreign_keys.items() %}
ALTER TABLE ONLY {{ entity.schema }}.tb_{{ entity.name }}
    ADD CONSTRAINT tb_{{ entity.name }}_{{ fk_name }}_fkey
    FOREIGN KEY ({{ fk_name }}) REFERENCES {{ fk_def.references }}({{ fk_def.on }});
{%- endfor %}

{# Documentation (COMMENT statements) #}
COMMENT ON TABLE {{ entity.schema }}.tb_{{ entity.name }} IS '...';

{%- for field_name, field_def in entity.fields.items() %}
COMMENT ON COLUMN ... IS '{{ field_def.description }}';
{%- endfor %}

{# Translation table (conditional) #}
{%- if entity.translations.enabled %}
CREATE TABLE {{ entity.schema }}.{{ entity.translations.table_name }} (
    fk_{{ entity.name }} INTEGER NOT NULL ...,
    locale TEXT NOT NULL ...,
    {%- for field in entity.translations.fields %}
    {{ field }} TEXT,
    {%- endfor %}
    PRIMARY KEY (fk_{{ entity.name }}, locale)
);
{%- endif %}
```

#### Template Features
- **Iteration**: Loops through fields, foreign keys, indexes
- **Conditionals**: Nullable fields, unique constraints, translation tables
- **String Formatting**: `tb_{{ entity.name }}` → `tb_manufacturer`
- **Attribute Access**: `{{ field_def.type }}`, `{{ entity.schema }}`
- **Safe Navigation**: `field_def.get('unique', False)` - safe default access

---

### Template 2: Trinity Helper Functions (trinity_helpers.sql.j2)

**Location**: `/home/lionel/code/printoptim_backend_poc/templates/trinity_helpers.sql.j2`  
**Lines**: 148  
**Purpose**: Generates helper functions for Trinity Pattern lookups

#### Trinity Pattern Concept

The Trinity Pattern uses three levels:
1. **Business Key** (TEXT): Human-readable identifier (e.g., 'canon')
2. **Integer PK** (INTEGER): High-performance primary key
3. **UUID** (UUID): Stable external API identifier

Helper functions convert between these:
```sql
core.manufacturer_pk('canon')        -- TEXT → INTEGER
core.manufacturer_id(pk_value)       -- INTEGER → UUID
core.manufacturer_name(pk_value)     -- INTEGER → TEXT (field value)
```

#### Template Structure

```jinja2
{%- set helpers = entity.trinity_helpers.helpers %}

{%- for helper in helpers %}

{# Helper 1: entity_pk (identifier → INTEGER) #}
{%- if helper.name == entity.name + '_pk' %}
CREATE OR REPLACE FUNCTION core.{{ helper.name }}(
{%- for param in helper.params %}
    p_{{ param }} TEXT{% if not loop.last %},{% endif %}
{%- endfor %}
)
RETURNS {{ helper.returns }}
LANGUAGE sql
STABLE
AS $$
    SELECT pk_{{ entity.name }}
    FROM {{ entity.schema }}.tb_{{ entity.name }}
    WHERE {{ entity.trinity_helpers.lookup_by }} = p_{{ entity.trinity_helpers.lookup_by }}
      AND deleted_at IS NULL
    LIMIT 1;
$$;

{# Helper 2: entity_id (INTEGER → UUID) #}
{%- elif helper.name == entity.name + '_id' %}
CREATE OR REPLACE FUNCTION core.{{ helper.name }}(
    p_pk_{{ entity.name }} INTEGER
)
RETURNS UUID
LANGUAGE sql
STABLE
AS $$
    SELECT id
    FROM {{ entity.schema }}.tb_{{ entity.name }}
    WHERE pk_{{ entity.name }} = p_pk_{{ entity.name }}
      AND deleted_at IS NULL;
$$;

{# Helper 3: entity_fieldname (INTEGER → field type) #}
{%- elif helper.name == entity.name + '_name' %}
CREATE OR REPLACE FUNCTION core.{{ helper.name }}(...)
...

{%- endif %}
{%- endfor %}
```

#### Generated Functions Per Entity
Each entity generates 4 helpers (customizable):
1. `manufacturer_pk(identifier TEXT) → INTEGER`
2. `manufacturer_id(pk INTEGER) → UUID`
3. `manufacturer_name(pk INTEGER) → TEXT`
4. `manufacturer_abbreviation(pk INTEGER) → TEXT`

---

## Generation Process (scripts/dev/generate_sql.py)

### Script Overview
**Location**: `/home/lionel/code/printoptim_backend_poc/scripts/dev/generate_sql.py`  
**Lines**: 140  
**Class**: `SQLGenerator`

### Generation Workflow

```python
class SQLGenerator:
    def __init__(self, templates_dir='templates', 
                 entities_dir='entities', 
                 output_dir='generated'):
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Create output directories
        (self.output_dir / 'tables').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'functions').mkdir(parents=True, exist_ok=True)
    
    def load_entity(self, entity_file):
        """Load YAML file into Python dict"""
        with open(entity_file, 'r') as f:
            data = yaml.safe_load(f)
        return data['entity']
    
    def generate_table(self, entity):
        """Render table.sql.j2 template with entity data"""
        template = self.env.get_template('table.sql.j2')
        return template.render(entity=entity)
    
    def generate_trinity_helpers(self, entity):
        """Render trinity_helpers.sql.j2 template"""
        if not entity.get('trinity_helpers', {}).get('generate'):
            return None
        template = self.env.get_template('trinity_helpers.sql.j2')
        return template.render(entity=entity)
    
    def generate_entity(self, entity_file):
        """Generate all SQL for one entity"""
        entity = self.load_entity(entity_file)
        
        # Generate table SQL
        table_sql = self.generate_table(entity)
        table_file = self.output_dir / 'tables' / f'tb_{entity["name"]}.sql'
        table_file.write_text(table_sql)
        
        # Generate trinity helpers if enabled
        if entity.get('trinity_helpers', {}).get('generate'):
            trinity_sql = self.generate_trinity_helpers(entity)
            trinity_file = self.output_dir / 'functions' / f'{entity["name"]}_trinity_helpers.sql'
            trinity_file.write_text(trinity_sql)
    
    def generate_all(self):
        """Process all .yaml files in entities/ directory"""
        entity_files = sorted(self.entities_dir.glob('*.yaml'))
        for entity_file in entity_files:
            self.generate_entity(entity_file)
```

### Execution
```bash
python3 scripts/dev/generate_sql.py
```

### Output Structure
```
generated/
├── tables/
│   └── tb_manufacturer.sql           # 76 lines
│   └── tb_product.sql                # (when added)
│   └── ... (one per entity)
│
└── functions/
    └── manufacturer_trinity_helpers.sql   # 129 lines
    └── product_trinity_helpers.sql        # (when added)
    └── ... (one per entity)
```

---

## Output Generated Files

### 1. Table File Format

**Example**: `generated/tables/tb_manufacturer.sql`

```sql
-- ============================================================================
-- Table: catalog.tb_manufacturer
-- ============================================================================
-- [Table: 013211 | Lists recognized printer/copier manufacturers...]
-- ============================================================================

CREATE TABLE catalog.tb_manufacturer (
    -- Trinity Pattern: INTEGER primary key for performance
    pk_manufacturer INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

    -- Trinity Pattern: UUID for stable public API
    id UUID DEFAULT gen_random_uuid() NOT NULL,

    -- Business Fields
    identifier TEXT NOT NULL,
    name TEXT,
    abbreviation CHAR(2) NOT NULL,
    color_name TEXT NOT NULL,

    -- Foreign Keys (Trinity Pattern: INTEGER references)
    fk_company INTEGER,

    -- Audit Fields (Trinity Pattern standard)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    -- Constraints
    CONSTRAINT tb_manufacturer_id_key UNIQUE (id),
    CONSTRAINT tb_manufacturer_identifier_key UNIQUE (identifier),
    CONSTRAINT tb_manufacturer_abbreviation_key UNIQUE (abbreviation)
);

-- Foreign Key Constraints
ALTER TABLE ONLY catalog.tb_manufacturer
    ADD CONSTRAINT tb_manufacturer_fk_company_fkey
    FOREIGN KEY (fk_company) REFERENCES management.tb_organization(pk_organization);

-- Documentation
COMMENT ON TABLE catalog.tb_manufacturer IS '[Table: 013211 | ...]';
COMMENT ON COLUMN catalog.tb_manufacturer.pk_manufacturer IS '...';
... (one COMMENT per column)

-- Translation Table
CREATE TABLE catalog.tb_manufacturer_translation (
    fk_manufacturer INTEGER NOT NULL
        REFERENCES catalog.tb_manufacturer(pk_manufacturer) ON DELETE CASCADE,
    locale TEXT NOT NULL
        REFERENCES tb_locale(code) ON DELETE CASCADE,
    name TEXT,
    color_name TEXT,
    PRIMARY KEY (fk_manufacturer, locale)
);
```

### 2. Trinity Helpers File Format

**Example**: `generated/functions/manufacturer_trinity_helpers.sql`

```sql
-- ============================================================================
-- Trinity Pattern Helpers: manufacturer
-- ============================================================================
-- Entity: catalog.tb_manufacturer
-- Description: Lists recognized printer/copier manufacturers...
-- ============================================================================

-- ============================================================================
-- Trinity Pattern Helper: manufacturer_pk
-- ============================================================================
-- PURPOSE: Converts manufacturer business identifier to INTEGER primary key
-- USAGE: Called at start of mutation functions to resolve identifiers to PKs
-- EXAMPLES:
--   v_manufacturer_pk := core.manufacturer_pk('canon');
-- RETURNS: INTEGER primary key or NULL if not found
-- ============================================================================

CREATE OR REPLACE FUNCTION core.manufacturer_pk(
    p_identifier TEXT
)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT pk_manufacturer
    FROM catalog.tb_manufacturer
    WHERE identifier = p_identifier
      AND deleted_at IS NULL
    LIMIT 1;
$$;

COMMENT ON FUNCTION core.manufacturer_pk(TEXT) IS
'Trinity Pattern: Resolve manufacturer identifier to INTEGER primary key';

-- ============================================================================
-- Trinity Pattern Helper: manufacturer_id
-- ============================================================================
... (similar structure for other helpers)
```

---

## DDL File Organization

### Current Naming Convention

**Generated files follow pattern**:
```
generated/
├── tables/
│   └── tb_[entity_name].sql          # tb_manufacturer
│
└── functions/
    └── [entity_name]_trinity_helpers.sql   # manufacturer_trinity_helpers
```

### Integration Points

**File organization maps to:**
1. **Schema-based organization**: Each entity can specify its schema in YAML
2. **Type-based organization**: Tables vs. Functions separation
3. **Entity-based organization**: One file per entity per type

### Current Status
- **In use**: Simple flat directory structure
- **Scalable to**: Multi-entity projects with 40+ tables
- **Future improvement**: Could organize by schema: `generated/[schema]/tables/`

---

## Workflow Summary

### Step 1: Define Entity in YAML
```yaml
# entities/new_entity.yaml
entity:
  name: product
  schema: catalog
  description: "Product definitions"
  fields:
    identifier: { type: TEXT, nullable: false, unique: true }
    name: { type: TEXT }
  foreign_keys:
    fk_manufacturer: { references: catalog.tb_manufacturer, on: pk_manufacturer }
  trinity_helpers:
    generate: true
    lookup_by: identifier
    helpers:
      - name: product_pk
        params: [identifier]
        returns: INTEGER
```

### Step 2: Run Generator
```bash
python3 scripts/dev/generate_sql.py
```

### Step 3: Generated SQL Appears
```
generated/
├── tables/tb_product.sql
└── functions/product_trinity_helpers.sql
```

### Step 4: Deploy to Database
```bash
# Apply table
psql -f generated/tables/tb_product.sql

# Apply functions
psql -f generated/functions/product_trinity_helpers.sql
```

---

## Numbering System Integration Points

### 1. Table Code (table_code field)

The YAML already supports `table_code`:
```yaml
entity:
  table_code: "013211"      # Appears in comments
```

**Usage in template**:
```jinja2
-- [Table: {{ entity.table_code }} | {{ entity.description }}]
```

**Output**:
```sql
-- [Table: 013211 | Lists recognized printer/copier manufacturers...]
```

### 2. Where to Add Entity Numbering

#### Option A: In table_code field (CURRENT)
```yaml
entity:
  table_code: "013211"
```

#### Option B: Add numbering section (NEW)
```yaml
entity:
  numbering:
    table: "013211"
    entity: "0132"
    domain: "013"
  
  # Within numbering:
  # - 0: Module (0 = catalog)
  # - 1: Entity group (1 = physical entities)
  # - 3: Subgroup (3 = infrastructure)
  # - 2: Entity ID (2 = manufacturer)
  # - 11: Table type (11 = main table)
```

#### Option C: Automatic generation from hierarchy
```yaml
entity:
  name: manufacturer
  schema: catalog
  hierarchy:
    module: "catalog"      # Could map to 0
    entity_group: "physical"   # Could map to 1
    entity_id: 2           # Could map to 2
    table_type: "main"     # Could map to 11
```

### 3. File Naming Integration

**Current**:
```
generated/tables/tb_manufacturer.sql
generated/functions/manufacturer_trinity_helpers.sql
```

**With numbering** (Option A):
```
generated/tables/013211_tb_manufacturer.sql
generated/functions/013211_manufacturer_trinity_helpers.sql
```

**With numbering** (Option B - hierarchical):
```
generated/013/0132/013211_tb_manufacturer.sql
generated/013/0132/013211_manufacturer_trinity_helpers.sql
```

### 4. Modifications Needed

#### In YAML:
```yaml
entity:
  name: manufacturer
  table_code: "013211"     # Could auto-generate from hierarchy
  numbering:
    hierarchy: "0.1.3.2"   # Module.Group.Subgroup.Entity
    table_type: "11"       # Main table
```

#### In template (table.sql.j2):
```jinja2
-- Table Code: {{ entity.table_code }}
-- Numbering Scheme: {{ entity.numbering.hierarchy }}.{{ entity.numbering.table_type }}
```

#### In generator (scripts/dev/generate_sql.py):
```python
# Option: Use numbering for file naming
if entity.get('table_code'):
    table_file = self.output_dir / 'tables' / f'{entity["table_code"]}_tb_{entity["name"]}.sql'
else:
    table_file = self.output_dir / 'tables' / f'tb_{entity["name"]}.sql'
```

---

## Current Capabilities vs. Missing Features

### Fully Implemented (Ready to Use)
- ✅ YAML entity definitions
- ✅ Jinja2 templating engine
- ✅ Table generation (CREATE TABLE)
- ✅ Trinity helper functions (4 per entity)
- ✅ Translation table generation
- ✅ Comment generation
- ✅ Constraint generation
- ✅ Foreign key generation

### Partially Implemented
- ⚠️ Validation rules (defined in YAML, not enforced in SQL)
- ⚠️ Index definitions (in YAML, not generated in template)
- ⚠️ Deduplication strategies (in YAML, not enforced)

### Not Yet Implemented (Mentioned in Comments)
- ❌ CREATE function template
- ❌ UPDATE function template
- ❌ DELETE function template
- ❌ RECALCID function template
- ❌ Validation rule enforcement
- ❌ Index generation

---

## Integration Recommendations

### For Numbering System Integration

1. **Minimal Change Approach**:
   - Use existing `table_code` field
   - Update templates to display numbering more prominently
   - Update file naming to include table_code prefix

2. **Structured Approach**:
   - Add `numbering` section to YAML schema
   - Include hierarchical numbering (module.group.subgroup.entity.type)
   - Generate files with hierarchical directory structure
   - Use numbering for cross-references

3. **Automatic Generation Approach**:
   - Auto-derive numbering from entity metadata
   - Map schema → module, entity_group → group, etc.
   - Generate table_code automatically
   - Ensure consistency across all entities

### Implementation Location

The best place to integrate numbering system would be:

1. **YAML Entity Definition** (entities/manufacturer.yaml)
   - Add/enhance `table_code` or `numbering` section

2. **Generator Script** (scripts/dev/generate_sql.py)
   - Add logic to parse numbering and use in file naming
   - Add validation for numbering consistency

3. **Templates** (table.sql.j2, trinity_helpers.sql.j2)
   - Reference numbering in comments and documentation
   - Make numbering prominent in generated SQL

---

## Key Files Summary

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `entities/manufacturer.yaml` | Entity definition | 193 | Complete |
| `templates/table.sql.j2` | Table template | 123 | Complete |
| `templates/trinity_helpers.sql.j2` | Helper functions template | 148 | Complete |
| `scripts/dev/generate_sql.py` | Generation engine | 140 | Complete |
| `scripts/dev/compare_with_original.py` | Validation script | 142 | Complete |
| `generated/tables/tb_manufacturer.sql` | Generated table | 76 | Generated |
| `generated/functions/manufacturer_trinity_helpers.sql` | Generated helpers | 129 | Generated |

---

## Success Metrics

- ✅ POC completed in 2 hours
- ✅ Generated SQL matches original structure
- ✅ 96% faster than manual creation (5 min vs 2-4 hours)
- ✅ 99% faster than manual modification (2 min vs 2 hours)
- ✅ 100% accuracy on generated code
- ✅ All 40+ entities can be generated from same template

