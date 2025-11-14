# Schema Organization Strategy: From PrintOptim-Specific to Universal Framework

**Date**: 2025-11-09
**Status**: 🚧 PROPOSED
**Context**: Refactoring schema organization to support any business domain, not just PrintOptim

---

## Executive Summary

The current codebase has a **schema organization problem**: it mixes PrintOptim-specific schemas (catalog) with universal patterns, and uses inconsistent terminology between the domain registry (new, better) and hardcoded lists in generators (old, inflexible).

**Goal**: Transform schema organization to be **domain-agnostic** while maintaining clear separation between:
1. **Common**: Shared reference data (countries, languages, timezones)
2. **Tenant**: Multi-tenant business data (isolated per tenant)
3. **Domain-Specific**: Application-specific schemas (catalog for PrintOptim, others for different apps)

---

## Problem Analysis

### Issue 1: PrintOptim-Specific Schema Hardcoded as "Universal"

**Current State**:
```yaml
# registry/domain_registry.yaml
"3":
  name: catalog  # ← PrintOptim-specific!
  description: "Product catalog, manufacturer data & inventory"
```

**Problem**:
- "catalog" is PrintOptim's product domain, not a universal pattern
- Framework treats it as a core schema alongside "crm", "projects"
- Other applications may not need catalog at all
- Misleads users into thinking catalog is required

**Impact**:
- ❌ Cannot use framework for non-e-commerce applications
- ❌ Confusing for users building HR, legal, or other domains
- ❌ Schema list grows with every app type (catalog, retail, healthcare, etc.)

---

### Issue 2: Inconsistent Multi-Tenancy Classification

**Two Different Systems**:

**System A: Hardcoded Lists** (in 3 generator files):
```python
# src/generators/table_generator.py:147
tenant_schemas = ["tenant", "crm", "management", "operations"]

# src/generators/trinity_helper_generator.py:64
TENANT_SCHEMAS = ["tenant", "crm", "management", "operations"]

# src/generators/core_logic_generator.py:201
TENANT_SCHEMAS = ["tenant", "crm", "management", "operations"]
```

**System B: Domain Registry** (registry/domain_registry.yaml):
```yaml
"2":
  name: crm
  aliases: ["management"]  # ← Supports aliases!

"4":
  name: projects
  aliases: ["tenant", "dim"]  # ← "tenant" is just an alias!
```

**Problems**:
- System A doesn't recognize aliases (would fail for "management")
- System A doesn't have metadata for multi_tenant flag
- No single source of truth
- Adding new domains requires updating 3+ files

---

### Issue 3: Confusing Terminology (Domain vs Schema vs Subdomain)

**Current Usage** (inconsistent):

| File/Location | Calls it... | Actually Means |
|---------------|-------------|----------------|
| `domain_registry.yaml` | "domain: catalog" | Top-level grouping |
| `table_generator.py` | "schema: catalog" | PostgreSQL schema |
| `numbering_parser.py` | "domain code: 3" | Hexadecimal digit |
| FK resolver | "schema: product" | ❌ BUG! Should be "catalog" |
| SpecQL YAML | "schema: catalog" | Where table goes |
| Subdomain | "subdomain: manufacturer" | Sub-grouping under catalog |

**Problem**: Same word ("domain") means different things in different contexts.

---

### Issue 4: Missing Multi-Tenancy Metadata

**Current**: Hardcoded lists determine tenant_id behavior
```python
if schema in ["tenant", "crm", "management", "operations"]:
    add_tenant_id_column()
```

**Problem**:
- What if user creates custom schema "sales" that needs tenant isolation?
- What if "catalog" needs to be tenant-specific for some apps?
- No way to configure multi-tenancy per schema

---

## Proposed Solution: Three-Tier Schema Model

### Tier 1: Framework Schemas (Universal, Hardcoded)

**Built-in schemas that exist in every deployment**:

```yaml
framework_schemas:
  common:
    description: "Shared reference data (countries, currencies, timezones)"
    multi_tenant: false
    purpose: "Global lookups, no tenant isolation"
    examples:
      - tb_country
      - tb_language
      - tb_currency
      - tb_timezone

  app:
    description: "GraphQL API types (composite types, mutation_result)"
    multi_tenant: false
    purpose: "Framework-level API contract"
    examples:
      - mutation_result
      - type_*_input

  core:
    description: "Framework business functions & helpers"
    multi_tenant: mixed  # Depends on which entity
    purpose: "Trinity helpers, core utilities"
    examples:
      - entity_pk()
      - entity_id()
      - emit_event()
```

**Key Points**:
- ✅ These exist in EVERY application
- ✅ Cannot be removed or renamed
- ✅ Framework generators know about them
- ✅ No domain-specific logic (product, manufacturer, etc.)

---

### Tier 2: Multi-Tenant Schemas (User-Defined, Configurable)

**Business domains that need tenant isolation**:

```yaml
# User's domain_registry.yaml (for PrintOptim app)
multi_tenant_domains:
  "2":
    name: crm
    aliases: [management]
    multi_tenant: true  # ← EXPLICIT FLAG
    description: "Customer relationship management"

  "4":
    name: projects
    aliases: [tenant, dim]
    multi_tenant: true  # ← EXPLICIT FLAG
    description: "Project & task management"
```

**Behavior**:
- ✅ Automatic `tenant_id UUID NOT NULL` column
- ✅ RLS policies applied
- ✅ Trinity helpers accept `tenant_id` parameter
- ✅ Foreign keys resolve within tenant scope

**User Flexibility**:
- User can add "sales", "hr", "legal" domains
- User can rename "crm" to "customers" if preferred
- Framework doesn't care about names, only `multi_tenant` flag

---

### Tier 3: Shared Schemas (User-Defined, Domain-Specific)

**Application-specific reference data (no tenant isolation)**:

```yaml
# User's domain_registry.yaml (for PrintOptim app)
shared_domains:
  "3":
    name: catalog
    multi_tenant: false  # ← EXPLICIT FLAG
    description: "Product catalog (PrintOptim-specific)"
    note: "Other apps wouldn't have this"

  # Example for different app:
  # "3":
  #   name: healthcare
  #   multi_tenant: false
  #   description: "Medical codes (ICD-10, CPT)"
```

**Behavior**:
- ✅ NO `tenant_id` column
- ✅ No RLS policies
- ✅ Shared across all tenants
- ✅ Foreign keys resolve globally

**Key Insight**:
- "catalog" is NOT universal like "common"
- "catalog" is PrintOptim's domain-specific shared data
- Other apps would have different Tier 3 schemas

---

## Implementation Plan

### Phase 1: Add Multi-Tenancy Metadata to Domain Registry

**Update**: `registry/domain_registry.yaml`

```yaml
domains:
  "1":
    name: core
    multi_tenant: false  # ← NEW FIELD
    framework_schema: true  # ← Framework-level

  "2":
    name: crm
    aliases: [management]
    multi_tenant: true  # ← NEW FIELD

  "3":
    name: catalog
    multi_tenant: false  # ← NEW FIELD (shared reference data)
    app_specific: true  # ← Not universal like "common"

  "4":
    name: projects
    aliases: [tenant, dim]
    multi_tenant: true  # ← NEW FIELD
```

**Benefits**:
- Single source of truth for tenant_id behavior
- Explicit, not inferred from schema name
- User can configure any schema as multi_tenant

---

### Phase 2: Create Central Schema Registry

**New File**: `src/generators/schema/schema_registry.py`

```python
from typing import Optional
from src.numbering.naming_conventions import NamingConventions
from src.core.domain_registry import DomainRegistry

class SchemaRegistry:
    """
    Central registry for schema properties

    Replaces hardcoded TENANT_SCHEMAS lists with registry-driven lookups
    """

    def __init__(self, domain_registry: DomainRegistry):
        self.domain_registry = domain_registry

    def is_multi_tenant(self, schema_name: str) -> bool:
        """
        Check if schema requires tenant_id column

        Checks:
        1. Domain registry (including aliases)
        2. multi_tenant flag in domain metadata
        3. Falls back to False (safe default)

        Example:
            registry.is_multi_tenant("crm")         # True
            registry.is_multi_tenant("management")  # True (alias of crm)
            registry.is_multi_tenant("catalog")     # False
            registry.is_multi_tenant("common")      # False
        """
        domain = self.domain_registry.get_domain_by_name_or_alias(schema_name)
        if domain:
            return domain.metadata.get('multi_tenant', False)

        # Framework schemas (hardcoded, safe)
        framework_multi_tenant = {
            # None currently - core has mixed behavior
        }
        return schema_name in framework_multi_tenant

    def get_canonical_schema_name(self, schema_name: str) -> str:
        """
        Resolve alias to canonical schema name

        Example:
            registry.get_canonical_schema_name("management")  # "crm"
            registry.get_canonical_schema_name("tenant")      # "projects"
            registry.get_canonical_schema_name("catalog")     # "catalog"
        """
        domain = self.domain_registry.get_domain_by_name_or_alias(schema_name)
        return domain.name if domain else schema_name

    def is_framework_schema(self, schema_name: str) -> bool:
        """Check if schema is framework-level (common, app, core)"""
        return schema_name in ['common', 'app', 'core']

    def is_shared_reference_schema(self, schema_name: str) -> bool:
        """
        Check if schema is shared reference data (no tenant_id)

        Includes:
        - Framework schemas: common, app
        - User-defined domains with multi_tenant=false
        """
        if schema_name in ['common', 'app']:
            return True

        domain = self.domain_registry.get_domain_by_name_or_alias(schema_name)
        if domain:
            return not domain.metadata.get('multi_tenant', False)

        return False
```

**Usage in Generators**:
```python
# BEFORE (hardcoded)
TENANT_SCHEMAS = ["tenant", "crm", "management", "operations"]
if schema in TENANT_SCHEMAS:
    add_tenant_id()

# AFTER (registry-driven)
schema_registry = SchemaRegistry(domain_registry)
if schema_registry.is_multi_tenant(entity.schema):
    add_tenant_id()
```

---

### Phase 3: Update All Generators

**Files to Update**:

1. **`src/generators/table_generator.py`** (line 147)
   ```python
   # BEFORE
   def _is_tenant_specific_schema(self, schema: str) -> bool:
       tenant_schemas = ["tenant", "crm", "management", "operations"]
       return schema in tenant_schemas

   # AFTER
   def _is_tenant_specific_schema(self, schema: str) -> bool:
       return self.schema_registry.is_multi_tenant(schema)
   ```

2. **`src/generators/trinity_helper_generator.py`** (line 64)
   ```python
   # BEFORE
   TENANT_SCHEMAS = ["tenant", "crm", "management", "operations"]
   if entity.schema in TENANT_SCHEMAS:
       # Add tenant_id parameter

   # AFTER
   if self.schema_registry.is_multi_tenant(entity.schema):
       # Add tenant_id parameter
   ```

3. **`src/generators/core_logic_generator.py`** (line 201)
   ```python
   # Similar replacement
   ```

4. **`src/generators/actions/step_compilers/fk_resolver.py`** (line 127)
   ```python
   # BEFORE (hardcoded schema map)
   schema_map = {
       "Contact": "crm",
       "Manufacturer": "product",  # BUG!
   }

   # AFTER (registry lookup)
   def _resolve_entity_schema(self, entity_name: str) -> str:
       # Check if entity is registered
       entry = self.naming_conventions.registry.get_entity(entity_name)
       if entry:
           domain = self.domain_registry.get_domain(entry.domain_code)
           return domain.name  # Use canonical domain name

       # Fallback to inference
       return self._infer_schema_from_entity_name(entity_name)
   ```

---

### Phase 4: Update Documentation

**Files to Update**:

1. **`.claude/CLAUDE.md`**
   - Clarify Tier 1 (framework) vs Tier 2 (multi-tenant) vs Tier 3 (shared)
   - Remove "catalog" from universal examples
   - Add examples for different app types (HR, legal, etc.)

2. **`docs/architecture/SCHEMA_STRATEGY.md`**
   - Add section on schema tiers
   - Explain multi_tenant flag
   - Show how to add custom domains

3. **New**: `docs/guides/ADDING_CUSTOM_DOMAINS.md`
   - Step-by-step guide for users
   - Examples: "sales", "hr", "legal", "healthcare"

---

### Phase 5: Validation & Migration

**Validation Rules** (add to `registry/domain_registry.yaml`):
```yaml
validation:
  require_multi_tenant_flag: true  # Must be explicit
  warn_on_app_specific_in_framework: true  # Warn if "catalog" treated as universal

  framework_schemas:
    - common
    - app
    - core

  reserved_names:
    - public
    - pg_catalog
    - information_schema
```

**Migration Script**: `scripts/migrate_schema_metadata.py`
```python
#!/usr/bin/env python3
"""
Migrate hardcoded TENANT_SCHEMAS to registry-driven model
"""

def migrate_domain_registry():
    """Add multi_tenant flag to all existing domains"""
    # Read registry
    # Add multi_tenant: true/false to each domain
    # Validate no conflicts
    pass

def update_generators():
    """Replace hardcoded lists with schema_registry calls"""
    pass

def validate_migration():
    """Ensure all schemas have multi_tenant flag"""
    pass
```

---

## Examples: Different Application Types

### PrintOptim (Current)
```yaml
framework_schemas: [common, app, core]

multi_tenant_domains:
  crm: "Customer management"
  projects: "Tenant-specific project data"

shared_domains:
  catalog: "Product catalog (shared across tenants)"
```

**Result**:
- `common.tb_country` - Framework shared
- `crm.tb_contact` - Tenant-specific (has tenant_id)
- `catalog.tb_manufacturer` - App-specific shared (no tenant_id)

---

### HR Management System
```yaml
framework_schemas: [common, app, core]

multi_tenant_domains:
  hr: "Employee records"
  payroll: "Payroll & compensation"
  recruiting: "Job postings & candidates"

shared_domains:
  legal: "Labor laws & regulations (shared)"
  benefits: "Health plans & providers (shared)"
```

**Result**:
- `common.tb_country` - Framework shared
- `hr.tb_employee` - Tenant-specific (has tenant_id)
- `legal.tb_labor_law` - App-specific shared (no tenant_id)

---

### Healthcare Platform
```yaml
framework_schemas: [common, app, core]

multi_tenant_domains:
  patients: "Patient records"
  appointments: "Scheduling"

shared_domains:
  medical_codes: "ICD-10, CPT codes (shared)"
  medications: "Drug formulary (shared)"
```

**Result**:
- `common.tb_country` - Framework shared
- `patients.tb_patient` - Tenant-specific (has tenant_id)
- `medical_codes.tb_icd10` - App-specific shared (no tenant_id)

---

## Key Benefits

### 1. Domain-Agnostic Framework
- ✅ No hardcoded business domains (catalog, crm, etc.)
- ✅ Users define their own schemas
- ✅ Framework only knows: common, app, core

### 2. Explicit Multi-Tenancy
- ✅ `multi_tenant` flag in registry (no guessing)
- ✅ Works for any schema name
- ✅ Easy to add new multi-tenant domains

### 3. Flexible Alias Support
- ✅ "crm" or "management" (same domain)
- ✅ "projects", "tenant", or "dim" (same domain)
- ✅ Generators check aliases automatically

### 4. Single Source of Truth
- ✅ Domain registry controls multi-tenancy
- ✅ No hardcoded lists in generators
- ✅ Easy to add new schemas

### 5. Clear Terminology
- **Framework Schema**: Built-in (common, app, core)
- **Multi-Tenant Domain**: User-defined, has tenant_id
- **Shared Domain**: User-defined, no tenant_id
- **Subdomain**: Finer grouping within domain (manufacturer, product)

---

## Testing Strategy

### Test Cases

**Test 1: Multi-Tenant Flag Respected**
```python
def test_multi_tenant_flag():
    # Given: Domain with multi_tenant=true
    registry.set_multi_tenant("sales", True)

    # When: Generate table
    sql = table_gen.generate(Entity(schema="sales", ...))

    # Then: tenant_id column exists
    assert "tenant_id UUID NOT NULL" in sql
```

**Test 2: Alias Resolution**
```python
def test_alias_resolution():
    # Given: "management" is alias for "crm"
    registry.add_domain("crm", aliases=["management"])

    # When: Check multi_tenant
    assert schema_registry.is_multi_tenant("management") == True
    assert schema_registry.get_canonical_schema_name("management") == "crm"
```

**Test 3: Framework Schemas Unchanged**
```python
def test_framework_schemas():
    # Framework schemas always work
    assert schema_registry.is_framework_schema("common") == True
    assert schema_registry.is_multi_tenant("common") == False
```

**Test 4: FK Resolver Uses Registry**
```python
def test_fk_resolver_registry():
    # Register Manufacturer in catalog domain
    registry.register_entity("Manufacturer", domain="3")

    # FK resolver should use "catalog" schema
    schema = fk_resolver.resolve_entity_schema("Manufacturer")
    assert schema == "catalog"  # NOT "product"!
```

---

## Migration Checklist

### Pre-Migration
- [ ] Review all schemas in current codebase
- [ ] Identify which are tenant-specific vs shared
- [ ] Document any custom schemas users might have

### Implementation
- [ ] Add `multi_tenant` flag to `domain_registry.yaml`
- [ ] Create `SchemaRegistry` class
- [ ] Update `table_generator.py`
- [ ] Update `trinity_helper_generator.py`
- [ ] Update `core_logic_generator.py`
- [ ] Fix FK resolver bug (Manufacturer → catalog)
- [ ] Add validation rules

### Testing
- [ ] All unit tests pass
- [ ] Integration tests with multi-tenant schemas
- [ ] Integration tests with shared schemas
- [ ] Test alias resolution
- [ ] Test FK resolver with registry

### Documentation
- [ ] Update `.claude/CLAUDE.md`
- [ ] Update `SCHEMA_STRATEGY.md`
- [ ] Create `ADDING_CUSTOM_DOMAINS.md`
- [ ] Add examples for different app types

### Cleanup
- [ ] Remove all hardcoded `TENANT_SCHEMAS` lists
- [ ] Remove hardcoded schema maps in FK resolver
- [ ] Remove PrintOptim-specific assumptions
- [ ] Deprecate old patterns

---

## Decision Log

### Decision 1: Three-Tier Model (Framework / Multi-Tenant / Shared)
**Reason**: Clear separation between universal (common), tenant-isolated (crm), and app-specific (catalog)

### Decision 2: Explicit `multi_tenant` Flag
**Reason**: No guessing based on schema name; user controls behavior

### Decision 3: Keep "catalog" as User-Defined Domain
**Reason**: It's PrintOptim-specific, not universal; other apps won't need it

### Decision 4: Support Aliases in Registry
**Reason**: Flexibility for users ("crm" vs "management"); already in domain_registry.yaml

### Decision 5: Centralize Schema Logic in SchemaRegistry
**Reason**: Single source of truth; eliminates hardcoded lists in 3+ files

---

## Next Steps

1. **Review this proposal** with stakeholders
2. **Prioritize implementation**: High impact, medium effort
3. **Create subtasks** for Phase 1-5
4. **Update Week 2 plan** to include schema registry work
5. **Consider impact on Team B** (schema generation)

---

**Status**: 🚧 PROPOSED - Awaiting Review
**Priority**: High (affects all generators)
**Effort**: Medium (4-6 hours)
**Impact**: High (makes framework domain-agnostic)

**Last Updated**: 2025-11-09
