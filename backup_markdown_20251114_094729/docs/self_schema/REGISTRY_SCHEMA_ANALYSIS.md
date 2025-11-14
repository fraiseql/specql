# Registry Schema Analysis

**Date**: 2025-11-13
**Purpose**: Analyze manual schema to guide SpecQL YAML creation

## Tables

### 1. specql_registry.tb_domain

**Current Structure**:
- pk_domain: SERIAL PRIMARY KEY
- domain_number: VARCHAR(10) NOT NULL UNIQUE
- domain_name: VARCHAR(100) NOT NULL
- description: TEXT
- multi_tenant: BOOLEAN NOT NULL DEFAULT FALSE
- aliases: TEXT[] DEFAULT ARRAY[]::TEXT[]

**Analysis**:
- Simple structure, no Trinity pattern currently
- domain_number appears to be a string identifier (not numeric as in plan)
- multi_tenant field instead of schema_type enum
- aliases array field not in original plan

**SpecQL Mapping**:
- Needs Trinity pattern (pk_domain, id, identifier)
- domain_number should be integer 1-255 with CHECK constraint
- schema_type enum instead of multi_tenant boolean
- aliases field may need to be dropped or redesigned

### 2. specql_registry.tb_subdomain

**Current Structure**:
- pk_subdomain: SERIAL PRIMARY KEY
- fk_domain: INTEGER NOT NULL REFERENCES specql_registry.tb_domain(pk_domain) ON DELETE CASCADE
- subdomain_number: VARCHAR(10) NOT NULL
- subdomain_name: VARCHAR(100) NOT NULL
- description: TEXT
- next_entity_sequence: INTEGER NOT NULL DEFAULT 1
- UNIQUE(fk_domain, subdomain_number)

**Analysis**:
- No Trinity pattern
- subdomain_number is VARCHAR, not INTEGER
- next_entity_sequence field for sequencing (not in plan)
- Simple foreign key to domain

**SpecQL Mapping**:
- Add Trinity pattern
- Convert subdomain_number to INTEGER 0-15
- Remove next_entity_sequence (move to application logic)
- Keep unique constraint on (fk_domain, subdomain_number)

### 3. specql_registry.tb_entity_registration

**Current Structure**:
- pk_entity_registration: SERIAL PRIMARY KEY
- fk_subdomain: INTEGER NOT NULL REFERENCES specql_registry.tb_subdomain(pk_subdomain) ON DELETE CASCADE
- entity_name: VARCHAR(100) NOT NULL
- table_code: VARCHAR(20) NOT NULL
- entity_sequence: INTEGER NOT NULL
- UNIQUE(fk_subdomain, entity_name)

**Analysis**:
- No Trinity pattern
- Missing domain_number, schema_name fields from plan
- table_code is VARCHAR(20), not fixed 6-digit hex
- entity_sequence exists but no domain_number for DDS calculation

**SpecQL Mapping**:
- Add Trinity pattern
- Add domain_number, schema_name fields
- Convert table_code to 6-digit hex validation
- Keep entity_sequence
- Change unique constraint to (fk_subdomain, entity_sequence) for DDS uniqueness

## Pattern Library Tables

### 4. pattern_library.domain_patterns

**Current Structure** (from database/pattern_library_schema.sql):
- id: SERIAL PRIMARY KEY
- name: TEXT NOT NULL UNIQUE
- category: TEXT NOT NULL
- description: TEXT NOT NULL
- parameters: JSONB NOT NULL DEFAULT '{}'
- implementation: JSONB NOT NULL DEFAULT '{}'
- embedding: vector(384)
- times_instantiated: INTEGER DEFAULT 0
- source_type: TEXT DEFAULT 'manual'
- complexity_score: REAL
- deprecated: BOOLEAN DEFAULT FALSE
- deprecated_reason: TEXT
- replacement_pattern_id: INTEGER REFERENCES domain_patterns(id)
- created_at: TIMESTAMPTZ DEFAULT now()
- updated_at: TIMESTAMPTZ DEFAULT now()

**Analysis**:
- No Trinity pattern
- Uses 'name' instead of 'pattern_id'
- Has vector(384) embedding column
- More fields than plan (complexity_score, deprecated, etc.)
- Uses JSONB for parameters and implementation

**SpecQL Mapping**:
- Add Trinity pattern
- Rename 'name' to 'pattern_id'
- Keep vector(384) embedding (post-processing)
- Simplify to match plan structure
- Add pattern_type enum

### 5. pattern_library.entity_templates

**Current Structure** (from db/schema/pattern_library/entity_templates.sql):
- template_id: TEXT PRIMARY KEY
- template_name: TEXT NOT NULL
- description: TEXT NOT NULL
- domain_number: CHAR(2) NOT NULL
- base_entity_name: TEXT NOT NULL
- fields: JSONB NOT NULL
- included_patterns: TEXT[] DEFAULT '{}'
- composed_from: TEXT[] DEFAULT '{}'
- version: TEXT NOT NULL DEFAULT '1.0.0'
- previous_version: TEXT
- changelog: TEXT DEFAULT ''
- created_at: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
- updated_at: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
- times_instantiated: INTEGER NOT NULL DEFAULT 0
- is_public: BOOLEAN NOT NULL DEFAULT true
- author: TEXT NOT NULL DEFAULT 'system'

**Analysis**:
- Has template_id as TEXT PRIMARY KEY (no Trinity)
- domain_number as CHAR(2) instead of ref
- Uses arrays for included_patterns, composed_from
- Has versioning and audit fields
- More complex than plan suggests

**SpecQL Mapping**:
- Add Trinity pattern
- Convert domain_number to ref(Domain)
- Keep JSONB fields structure
- Simplify some fields for dogfooding MVP

## SpecQL Mapping Strategy

### Field Type Mappings

| PostgreSQL | SpecQL YAML | Status |
|------------|-------------|--------|
| SERIAL | integer (auto) | ✅ |
| VARCHAR(n) | text | ✅ |
| TEXT | text | ✅ |
| BOOLEAN | boolean | ✅ |
| INTEGER | integer | ✅ |
| JSONB | json | ✅ |
| TIMESTAMPTZ | timestamp | ✅ |
| TEXT[] | list(text) | ✅ |
| vector(384) | (custom type) | ⚠️ Post-processing |

### Constraint Mappings

| PostgreSQL | SpecQL YAML | Status |
|------------|-------------|--------|
| REFERENCES | ref(Entity) | ✅ |
| UNIQUE | unique: true | ✅ |
| CHECK (x IN (...)) | enum(...) | ✅ |
| NOT NULL | required: true | ✅ |
| CHECK (condition) | constraint: "condition" | ⚠️ Post-processing |

### Features Requiring Enhancement

1. **Trinity Pattern**: Not implemented in current schema
   - Need: Automatic pk_*, id, identifier fields
   - Workaround: Add manually in YAML

2. **Vector Type**: embedding: vector(384)
   - Current: Uses pgvector extension
   - SpecQL: No native support
   - Workaround: Post-processing ALTER TABLE

3. **Complex CHECK Constraints**: domain_number BETWEEN 1 AND 255
   - Current: No such constraints
   - SpecQL: Limited constraint support
   - Workaround: Post-processing ALTER TABLE

4. **Hierarchical Identifiers**: "D{domain_number}", "SD{parent}{subdomain}"
   - Current: No identifier fields
   - SpecQL: Supports identifier_template
   - Status: ✅ Can implement

## Decisions

### 1. Schema Evolution Approach
**Decision**: Generate enhanced schema with Trinity pattern and additional fields
**Reasoning**: Dogfooding should demonstrate SpecQL's full capabilities, not just replicate current schema
**Implementation**:
- Add Trinity pattern to all tables
- Add audit fields (created_at, updated_at, deleted_at)
- Add identifier fields with templates
- Enhance constraints and validations

### 2. Vector Type Handling
**Decision**: Include in YAML design but implement via post-processing
**Reasoning**: Vector embeddings are core to pattern library functionality
**Implementation**:
- SpecQL generates base table
- Post-processing adds vector column and indexes

### 3. Field Simplifications
**Decision**: Focus on core fields for dogfooding, document extensions
**Reasoning**: Demonstrate 80% of SpecQL capabilities with simpler schema
**Implementation**:
- Include essential fields only
- Document advanced features as "future enhancements"

## Next Steps

1. Create SpecQL YAML for each entity with Trinity pattern
2. Run `specql generate` and compare output with current schema
3. Document any missing features or generation issues
4. Create post-processing script for advanced features
5. Test schema equivalence and functionality</content>
</xai:function_call">Write the registry schema analysis document