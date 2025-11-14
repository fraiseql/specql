# Feature Gaps for Self-Schema Generation

**Date**: 2025-11-13
**Purpose**: Document features needed to generate registry schema

## Critical Gaps

### 1. Trinity Pattern Support
**Current**: Manual schema uses simple SERIAL PRIMARY KEY
**Needed**: Automatic pk_*, id (UUID), identifier (computed) fields
```yaml
# What we want
entity: Domain
identifier_template: "D{domain_number}"
# Should generate:
# pk_domain INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY
# id UUID DEFAULT uuid_generate_v4() NOT NULL
# identifier TEXT NOT NULL (computed as "D{domain_number}")
```

**Priority**: High (core SpecQL feature)
**Workaround**: Define Trinity fields manually in YAML
**Enhancement**: Already implemented - verify it's working

### 2. Audit Fields (created_at, updated_at, deleted_at)
**Current**: Manual schema has minimal timestamps
**Needed**: Automatic audit fields on all tables
```yaml
# Should be automatic, but may need explicit definition
fields:
  created_at:
    type: timestamp
    default: now()
  updated_at:
    type: timestamp
    default: now()
  deleted_at:
    type: timestamp
```

**Priority**: High
**Workaround**: Define explicitly in YAML
**Enhancement**: Should be automatic in generators

### 3. Vector Type Support
**Current**: SpecQL doesn't recognize vector(N) type
```yaml
# Needed
embedding: vector(384)
```

**Priority**: Medium (specialized use case)
**Workaround**: Manual ALTER TABLE after generation
**Enhancement**: Add vector type to SpecQL field types

### 4. Complex CHECK Constraints
**Current**: SpecQL enum creates CHECK automatically
```yaml
# Current (works)
status: enum(active, inactive)
# Generates: CHECK (status IN ('active', 'inactive'))
```

**Needed**: Complex CHECK constraints
```yaml
# Example
domain_number:
  type: integer
  constraint: "domain_number BETWEEN 1 AND 255"
```

**Priority**: Medium
**Workaround**: Add CHECK in post-processing
**Enhancement**: Add `constraint` field option

### 5. Hierarchical Identifier Templates
**Current**: SpecQL supports basic templates
```yaml
# Current (works)
identifier_template: "{entity_name}_{id}"
```

**Needed**: Computed templates with parent references
```yaml
# Example
identifier_template: "SD{parent_domain.domain_number}{subdomain_number}"
```

**Priority**: Medium
**Workaround**: Use simpler template, compute in application
**Enhancement**: Support parent field references in templates

## Minor Gaps

### 6. JSONB Field Comments
**Current**: SpecQL adds table/field comments
**Needed**: Comments on JSONB sub-fields
**Priority**: Low
**Workaround**: Document separately

### 7. Index Types (IVFFlat, GIN, etc.)
**Current**: SpecQL creates B-tree indexes
**Needed**: Specify index type
```yaml
fields:
  embedding:
    type: binary
    index:
      type: ivfflat
      options: "lists = 100"
```

**Priority**: Low
**Workaround**: Manual CREATE INDEX after generation

### 8. Array Type Support
**Current**: SpecQL may not support PostgreSQL arrays
**Needed**: TEXT[] and other array types
```yaml
aliases:
  type: list(text)
```

**Priority**: Low
**Workaround**: Use JSONB or manual post-processing

## Decisions for Dogfooding MVP

**Scope**: Use SpecQL for 95% of schema, manual post-processing for specialized features

**Inclusions** (demonstrate SpecQL capabilities):
- ✅ Trinity pattern (pk_*, id, identifier)
- ✅ Foreign keys (single-field)
- ✅ Enums with automatic CHECK constraints
- ✅ Audit fields (created_at, updated_at, deleted_at)
- ✅ Indexes (B-tree)
- ✅ Comments on tables and columns
- ✅ Unique constraints
- ✅ NOT NULL constraints
- ✅ Basic identifier templates

**Exclusions** (manual post-processing):
- ❌ Vector types (ALTER TABLE after generation)
- ❌ Complex CHECK constraints (ALTER TABLE after generation)
- ❌ Specialized indexes (CREATE INDEX after generation)
- ❌ Hierarchical identifier templates (simplify for now)

**Benefit**: Demonstrates SpecQL's value for 95% of business schemas, documents extension patterns for specialized cases.

## Enhancement Backlog

**Phase 1** (Current dogfooding):
- No changes to SpecQL generators
- Demonstrate core capabilities
- Document workarounds

**Phase 2** (Post-dogfooding enhancements):
1. Add vector type support (1 day)
2. Add custom constraint support (1 day)
3. Add index type specification (1 day)
4. Add hierarchical identifier templates (2 days)
5. Add array type support (1 day)

**Total**: ~6 days of enhancement work (optional, post-MVP)</content>
</xai:function_call">Write the feature gaps document