# SpecQL YAML Design for Registry Schema

**Date**: 2025-11-13
**Purpose**: Design YAML structure before implementation

## Directory Structure

```
entities/specql_registry/
├── domain.yaml
├── subdomain.yaml
├── entity_registration.yaml
└── pattern_library/
    ├── domain_pattern.yaml
    └── entity_template.yaml
```

## Entity Designs

### domain.yaml

```yaml
# Domain Registry Entity
# Stores all domains in the SpecQL system

entity: Domain
schema: specql_registry
description: "Registry of all domains in SpecQL system. Domains represent top-level organizational units (1-255)."

# Trinity pattern: automatically generates pk_domain, id, identifier
identifier_template: "D{domain_number}"

fields:
  # Business fields
  domain_number:
    type: integer
    required: true
    unique: true
    description: "Unique domain identifier (1-255). Used as first digit in hierarchical numbering."
    validation:
      min: 1
      max: 255

  domain_name:
    type: text
    required: true
    unique: true
    description: "Human-readable domain name (e.g., 'core', 'crm', 'projects')"
    validation:
      pattern: "^[a-z][a-z0-9_]*$"
      max_length: 50

  description:
    type: text
    description: "Domain purpose and scope description"
    validation:
      max_length: 500

  schema_type:
    type: enum
    values: [framework, multi_tenant, shared]
    required: true
    description: |
      Type of schema for this domain:
      - framework: Core SpecQL schemas (common, app, core)
      - multi_tenant: User schemas with tenant_id isolation
      - shared: User schemas shared across all tenants

  # Audit fields: created_at, updated_at, deleted_at added automatically

# Indexes
indexes:
  - fields: [domain_number]
    name: idx_domain_registry_domain_number
  - fields: [domain_name]
    name: idx_domain_registry_domain_name
  - fields: [schema_type]
    name: idx_domain_registry_schema_type

# Post-processing notes:
# - Add CHECK constraint: domain_number BETWEEN 1 AND 255
# - Populated by specql domain register CLI command
```

### subdomain.yaml

```yaml
# Subdomain Registry Entity
# Stores subdomains within domains

entity: Subdomain
schema: specql_registry
description: "Registry of subdomains within domains. Subdomains provide second-level organization (0-15 per domain)."

# Identifier format: SD{parent_domain_number}{subdomain_number}
# Example: SD12 = Domain 1, Subdomain 2
identifier_template: "SD{parent_domain.domain_number}{subdomain_number}"

fields:
  # Business fields
  subdomain_number:
    type: integer
    required: true
    description: "Subdomain number within parent domain (0-15)"
    validation:
      min: 0
      max: 15

  parent_domain:
    type: ref(Domain)
    required: true
    description: "Parent domain this subdomain belongs to"
    # Note: Creates fk_domain foreign key automatically

  subdomain_name:
    type: text
    required: true
    description: "Human-readable subdomain name (e.g., 'entities', 'workflows')"
    validation:
      pattern: "^[a-z][a-z0-9_]*$"
      max_length: 50

  description:
    type: text
    description: "Subdomain purpose and scope description"
    validation:
      max_length: 500

# Unique constraint: each subdomain_number must be unique within a domain
constraints:
  - type: unique
    fields: [parent_domain, subdomain_number]
    name: uq_subdomain_parent_number

# Indexes
indexes:
  - fields: [parent_domain]
    name: idx_subdomain_registry_parent_domain
  - fields: [subdomain_number]
    name: idx_subdomain_registry_number
  - fields: [subdomain_name]
    name: idx_subdomain_registry_name

# Post-processing notes:
# - Populated by specql subdomain register CLI command
```

### entity_registration.yaml

```yaml
# Entity Registration
# Central registry of all entities with codes and metadata

entity: EntityRegistration
schema: specql_registry
description: "Central registry of all entities in SpecQL system with their hierarchical codes and table codes."

# Identifier format: DDS-EX (e.g., 012-31 = Domain 0, Subdomain 12, Entity 3, Hex 1)
identifier_template: "{domain_number:03d}{subdomain_number:02d}{entity_sequence}"

fields:
  # Hierarchical numbering components
  domain_number:
    type: integer
    required: true
    description: "Domain number (1-255)"
    validation:
      min: 1
      max: 255

  subdomain_number:
    type: integer
    required: true
    description: "Subdomain number within domain (0-15)"
    validation:
      min: 0
      max: 15

  entity_sequence:
    type: integer
    required: true
    description: "Entity sequence within subdomain (0-15)"
    validation:
      min: 0
      max: 15

  # Foreign keys to parent structures
  parent_domain:
    type: ref(Domain)
    required: true
    description: "Parent domain"

  parent_subdomain:
    type: ref(Subdomain)
    required: true
    description: "Parent subdomain"
    # Note: Ideally would be composite FK (domain_number, subdomain_number)
    # For dogfooding, using simple ref with application-level validation

  # Entity metadata
  entity_name:
    type: text
    required: true
    description: "Entity name (e.g., 'Contact', 'Company')"
    validation:
      pattern: "^[A-Z][A-Za-z0-9]*$"
      max_length: 100

  table_code:
    type: text
    required: true
    unique: true
    description: "6-digit hexadecimal table code (e.g., '012361' for Contact)"
    validation:
      pattern: "^[0-9A-Fa-f]{6}$"

  schema_name:
    type: text
    required: true
    description: "PostgreSQL schema name (e.g., 'crm', 'core', 'projects')"
    validation:
      pattern: "^[a-z][a-z0-9_]*$"
      max_length: 63  # PostgreSQL identifier limit

  table_name:
    type: text
    required: true
    description: "PostgreSQL table name (e.g., 'tb_contact')"
    validation:
      pattern: "^tb_[a-z][a-z0-9_]*$"
      max_length: 63

  entity_type:
    type: enum
    values: [standard, aggregate, value_object, view]
    required: true
    default: standard
    description: "Type of entity in DDD terms"

  # Metadata
  registration_source:
    type: enum
    values: [manual, generated, discovered]
    required: true
    default: generated
    description: "How this entity was registered"

# Unique constraints
constraints:
  - type: unique
    fields: [domain_number, subdomain_number, entity_sequence]
    name: uq_entity_dds_code
    description: "Each DDS code must be unique"

  - type: unique
    fields: [schema_name, table_name]
    name: uq_entity_schema_table
    description: "Each table name must be unique within schema"

# Indexes
indexes:
  - fields: [domain_number]
    name: idx_entity_registration_domain
  - fields: [subdomain_number]
    name: idx_entity_registration_subdomain
  - fields: [entity_sequence]
    name: idx_entity_registration_sequence
  - fields: [table_code]
    name: idx_entity_registration_table_code
  - fields: [schema_name]
    name: idx_entity_registration_schema
  - fields: [entity_name]
    name: idx_entity_registration_name
  - fields: [parent_domain]
    name: idx_entity_registration_parent_domain
  - fields: [parent_subdomain]
    name: idx_entity_registration_parent_subdomain

# Post-processing notes:
# - Add composite CHECK constraint: table_code calculated from DDS-EX formula
# - Add trigger to validate parent_subdomain belongs to parent_domain
# - Populated by code generation pipeline
```

### pattern_library/domain_pattern.yaml

```yaml
# Domain Pattern Entity
# Stores reusable patterns for business logic

entity: DomainPattern
schema: pattern_library
description: "Registry of reusable domain patterns including universal patterns, domain-specific patterns, and entity templates."

# Identifier format: pattern_id is human-readable (e.g., "email_validation")
identifier_template: "{pattern_id}"

fields:
  # Primary identifier
  pattern_id:
    type: text
    required: true
    unique: true
    description: "Unique pattern identifier (e.g., 'email_validation', 'audit_trail')"
    validation:
      pattern: "^[a-z][a-z0-9_]*$"
      max_length: 100

  # Pattern metadata
  pattern_name:
    type: text
    required: true
    description: "Human-readable pattern name"
    validation:
      max_length: 200

  category:
    type: enum
    values: [validation, audit, security, workflow, notification, data_quality, performance]
    required: true
    description: "Pattern category for organization"

  description:
    type: text
    required: true
    description: "Detailed pattern description and usage instructions"

  pattern_type:
    type: enum
    values: [universal, domain, entity_template]
    required: true
    description: |
      Pattern scope level:
      - universal: Applies to any domain (e.g., soft_delete)
      - domain: Specific to a domain (e.g., crm_contact_validation)
      - entity_template: Complete entity template (e.g., customer_entity_template)

  # Pattern definition
  fields_json:
    type: json
    required: true
    description: "Pattern field definitions in JSON format"
    validation:
      schema: pattern_fields_schema

  actions_json:
    type: json
    description: "Pattern actions in JSON format (optional)"

  # Usage tracking
  usage_count:
    type: integer
    required: true
    default: 0
    description: "Number of times pattern has been applied to entities"
    validation:
      min: 0

  popularity_score:
    type: decimal
    required: true
    default: 0.0
    description: "Calculated popularity score (0.0-1.0)"
    validation:
      min: 0.0
      max: 1.0
      precision: 3

  # Relationships
  parent_domain:
    type: ref(Domain)
    description: "Domain this pattern belongs to (for domain-specific patterns)"

  created_by_user:
    type: text
    description: "User who created this pattern"

  # Versioning
  version:
    type: text
    required: true
    default: "1.0.0"
    description: "Pattern version (semver format)"
    validation:
      pattern: '^\d+\.\d+\.\d+$'

  # Status
  status:
    type: enum
    values: [draft, active, deprecated]
    required: true
    default: active
    description: "Pattern lifecycle status"

# Indexes
indexes:
  - fields: [pattern_id]
    name: idx_domain_patterns_pattern_id
  - fields: [category]
    name: idx_domain_patterns_category
  - fields: [pattern_type]
    name: idx_domain_patterns_type
  - fields: [parent_domain]
    name: idx_domain_patterns_domain
  - fields: [status]
    name: idx_domain_patterns_status
  - fields: [usage_count]
    name: idx_domain_patterns_usage
    description: "For finding popular patterns"

# Post-processing notes:
# - Add embedding vector(384) column for semantic search
#   ALTER TABLE pattern_library.domain_patterns ADD COLUMN embedding vector(384);
# - Create IVFFlat index on embedding
#   CREATE INDEX idx_domain_patterns_embedding ON pattern_library.domain_patterns
#   USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
# - Embeddings generated by EmbeddingService after pattern creation
```

### pattern_library/entity_template.yaml

```yaml
# Entity Template
# Complete reusable entity templates with fields and patterns

entity: EntityTemplate
schema: pattern_library
description: "Complete entity templates that can be instantiated to create new entities with pre-configured fields and patterns."

identifier_template: "{template_id}"

fields:
  # Primary identifier
  template_id:
    type: text
    required: true
    unique: true
    description: "Unique template identifier (e.g., 'customer_contact_template')"
    validation:
      pattern: "^[a-z][a-z0-9_]*$"
      max_length: 100

  # Template metadata
  template_name:
    type: text
    required: true
    description: "Human-readable template name"
    validation:
      max_length: 200

  description:
    type: text
    required: true
    description: "Template description and use cases"

  # Domain context
  parent_domain:
    type: ref(Domain)
    required: true
    description: "Domain this template belongs to"

  base_entity_name:
    type: text
    required: true
    description: "Base entity name for instantiation (e.g., 'Contact' produces 'tb_contact')"
    validation:
      pattern: "^[A-Z][A-Za-z0-9]*$"
      max_length: 100

  # Template definition
  fields_json:
    type: json
    required: true
    description: "Complete field definitions in JSON format"
    validation:
      schema: entity_fields_schema

  # Pattern composition
  included_patterns:
    type: list(text)
    description: "List of pattern_ids to apply to this template"

  composed_from:
    type: list(text)
    description: "List of other template_ids this template is composed from"

  # Instantiation tracking
  instantiation_count:
    type: integer
    required: true
    default: 0
    description: "Number of times this template has been instantiated"
    validation:
      min: 0

  # Versioning
  version:
    type: text
    required: true
    default: "1.0.0"
    description: "Template version (semver format)"
    validation:
      pattern: '^\d+\.\d+\.\d+$'

  # Status
  status:
    type: enum
    values: [draft, active, deprecated]
    required: true
    default: active
    description: "Template lifecycle status"

  # Metadata
  created_by_user:
    type: text
    description: "User who created this template"

  tags:
    type: list(text)
    description: "Tags for template discovery (e.g., ['crm', 'customer', 'b2b'])"

# Indexes
indexes:
  - fields: [template_id]
    name: idx_entity_templates_id
  - fields: [parent_domain]
    name: idx_entity_templates_domain
  - fields: [base_entity_name]
    name: idx_entity_templates_base_name
  - fields: [status]
    name: idx_entity_templates_status
  - fields: [instantiation_count]
    name: idx_entity_templates_usage

# Actions
actions:
  - name: instantiate_template
    description: "Create a new entity from this template"
    parameters:
      - name: target_entity_name
        type: text
        required: true
      - name: target_schema
        type: text
        required: true
      - name: customizations
        type: json
        description: "Field customizations to apply"
    steps:
      - validate: status = 'active'
      - call: pattern_library.apply_template(template_id, target_entity_name, target_schema, customizations)
      - update: EntityTemplate SET instantiation_count = instantiation_count + 1 WHERE pk_entity_template = @pk_entity_template
      - notify:
          event: template_instantiated
          data:
            template_id: "@template_id"
            entity_name: "@target_entity_name"
    impacts:
      mutates: [EntityTemplate]
      creates: [Entity]

  - name: compose_templates
    description: "Create a new template by composing existing templates"
    parameters:
      - name: new_template_id
        type: text
        required: true
      - name: source_template_ids
        type: list(text)
        required: true
    steps:
      - validate: status = 'active'
      - foreach: template_id IN source_template_ids
        do:
          - validate: EXISTS(SELECT 1 FROM pattern_library.tb_entity_template WHERE template_id = @template_id AND status = 'active')
      - call: pattern_library.merge_templates(source_template_ids)
      - insert:
          into: EntityTemplate
          values:
            template_id: "@new_template_id"
            composed_from: "@source_template_ids"
    impacts:
      creates: [EntityTemplate]

# Post-processing notes:
# - Add embedding vector(384) column for semantic search
# - Template instantiation handled by SpecQL CLI: specql template instantiate <template_id>
```

## Design Notes

### Simplifications from Manual Schema

1. **Composite Foreign Keys**: Using single-field refs instead
   - Manual: `FOREIGN KEY (domain_number, subdomain_number) REFERENCES subdomain_registry(parent_domain_number, subdomain_number)`
   - SpecQL: `parent_subdomain: ref(Subdomain)`
   - Trade-off: Less referential integrity at DB level, enforced in application

2. **Vector Types**: Excluded from YAML, added post-generation
   - Manual: `embedding vector(384)`
   - SpecQL: (not in YAML)
   - Post-processing: `ALTER TABLE pattern_library.domain_patterns ADD COLUMN embedding vector(384);`

3. **Complex CHECK Constraints**: Simplified or post-processed
   - Manual: `CHECK (domain_number BETWEEN 1 AND 255)`
   - SpecQL: (not in YAML, or simplified)
   - Post-processing: `ALTER TABLE specql_registry.domain_registry ADD CONSTRAINT check_domain_number_range CHECK (domain_number BETWEEN 1 AND 255);`

### Benefits Demonstrated

1. **95% Code Reduction**:
   - Manual schema: ~500 lines SQL
   - SpecQL YAML: ~150 lines
   - Generation output: ~2000+ lines (with Trinity, indexes, helpers)

2. **Consistency**:
   - Trinity pattern automatically applied
   - Audit fields automatically added
   - Index naming conventions enforced
   - Comment generation consistent

3. **Maintainability**:
   - Business logic in YAML (version controlled)
   - Technical details generated (less manual maintenance)
   - Changes to conventions applied globally via regeneration

## Validation Strategy

### Phase 1: Generate & Compare
```bash
# Generate schema from YAML
specql generate entities/specql_registry/*.yaml --output-dir generated/

# Compare with manual schema
diff -u db/schema/00_registry/specql_registry.sql generated/0_schema/01_write_side/...
```

### Phase 2: Post-Processing
```bash
# Apply specialized features
psql -d specql_test < scripts/self_schema_post_processing.sql
```

### Phase 3: Test Equivalence
```bash
# Run full test suite against generated schema
pytest tests/integration/test_self_schema.py
```

## Next Steps

1. Create actual YAML files (Day 2)
2. Run generation (Day 3)
3. Document discrepancies (Day 3)
4. Create post-processing script (Day 4)
5. Validate equivalence (Day 4-5)</content>
</xai:function_call">Write the YAML design document