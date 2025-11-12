# Phases 6-8: Detailed Implementation Plan

**Date**: 2025-11-12
**Status**: Planning - Ready for Implementation
**Prerequisites**: Phases 0-5 Complete (Repository Pattern, DDD, PostgreSQL Migration)
**Timeline**: 4-6 weeks total

---

## Executive Summary

### What We're Building

**Phase 6**: Use SpecQL to generate SpecQL's own PostgreSQL schema (dogfooding)
**Phase 7**: Add dual interface (CLI + GraphQL) for registry access
**Phase 8**: Complete pattern library migration with semantic search

### Why These Phases Matter

1. **Phase 6**: Proves SpecQL can generate its own infrastructure (trust/marketing)
2. **Phase 7**: Better developer experience (GraphQL API for programmatic access)
3. **Phase 8**: Semantic pattern search across projects (AI-powered discovery)

### Timeline Overview

```
Week 1-2: Phase 6 (SpecQL Self-Schema)
Week 3-4: Phase 7 (Dual Interface)
Week 5-6: Phase 8 (Pattern Library Complete)
```

---

## Table of Contents

1. [Phase 6: SpecQL Self-Schema](#phase-6-specql-self-schema)
2. [Phase 7: Dual Interface Architecture](#phase-7-dual-interface-architecture)
3. [Phase 8: Pattern Library Complete](#phase-8-pattern-library-complete)
4. [Testing Strategy](#testing-strategy)
5. [Deployment Plan](#deployment-plan)
6. [Success Metrics](#success-metrics)

---

# Phase 6: SpecQL Self-Schema (Dogfooding)

**Duration**: 2 weeks
**Goal**: Generate SpecQL's registry schema using SpecQL itself
**Status**: Not started (0%)

---

## 6.1 Overview

### The Concept

Currently, SpecQL's PostgreSQL schema (`specql_registry`) is **manually created**. We want SpecQL to **generate its own schema** from YAML definitions.

**Before**:
```sql
-- Manually written SQL
CREATE TABLE specql_registry.tb_domain (
    pk_domain INTEGER PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid(),
    identifier TEXT GENERATED ALWAYS AS (domain_name) STORED,
    domain_number TEXT NOT NULL UNIQUE,
    domain_name TEXT NOT NULL UNIQUE,
    ...
);
```

**After**:
```yaml
# entities/specql_registry/domain.yaml
entity: domain
schema: specql_registry
description: Top-level business domains (crm, catalog, projects)

organization:
  table_code: "011111"  # Core domain, registry subdomain, entity 1
  domain: core
  subdomain: registry
  entity_sequence: 1

fields:
  domain_number:
    type: text
    nullable: false
    unique: true
    description: "Single digit domain number (1-9)"

  domain_name:
    type: text
    nullable: false
    unique: true
    description: "Canonical domain name (crm, catalog)"

  # ... rest of fields

# Then generate:
$ specql generate entities/specql_registry/*.yaml
# → migrations/specql_registry/tb_domain.sql (auto-generated)
```

---

## 6.2 Phase 6 Detailed Timeline

### Week 1: YAML Definitions

#### Day 1-2: Domain Entity YAML

**Task**: Create `entities/specql_registry/domain.yaml`

**File Structure**:
```
entities/
└── specql_registry/
    ├── domain.yaml
    ├── subdomain.yaml
    └── entity_registration.yaml
```

**`entities/specql_registry/domain.yaml`**:
```yaml
entity: domain
schema: specql_registry
description: Top-level business domains (crm, catalog, projects)

organization:
  table_code: "011111"
  domain: core
  subdomain: registry
  entity_sequence: 1
  file_sequence: 0

fields:
  # Trinity pattern fields (auto-generated)
  # pk_domain INTEGER PRIMARY KEY
  # id UUID DEFAULT gen_random_uuid()
  # identifier TEXT GENERATED ALWAYS AS (domain_name) STORED

  domain_number:
    type: text
    nullable: false
    unique: true
    description: "Single digit domain number (1-9)"
    validation:
      pattern: "^[1-9]$"

  domain_name:
    type: text
    nullable: false
    unique: true
    description: "Canonical domain name (crm, catalog)"
    validation:
      max_length: 100

  description:
    type: text
    nullable: true
    description: "Human-readable description of the domain"

  multi_tenant:
    type: boolean
    nullable: false
    default: false
    description: "Whether this domain requires tenant_id"

  aliases:
    type: list(text)
    nullable: true
    description: "Alternative names (e.g., 'management' for 'crm')"

  # Audit fields (auto-generated)
  # created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
  # updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
  # deleted_at TIMESTAMPTZ

indexes:
  - fields: [domain_number]
    unique: true
  - fields: [domain_name]
    unique: true

fraiseql:
  enabled: true
  queries:
    find_one: true
    find_one_by_identifier: true  # By domain_name
    find_many: true
  mutations:
    create: true
    update: true
    delete: false  # Use soft delete
```

**Deliverable**: `entities/specql_registry/domain.yaml` (complete, validated)

---

#### Day 3-4: Subdomain Entity YAML

**Task**: Create `entities/specql_registry/subdomain.yaml`

**`entities/specql_registry/subdomain.yaml`**:
```yaml
entity: subdomain
schema: specql_registry
description: Subdivisions within a domain (customer, sales)

organization:
  table_code: "011112"
  domain: core
  subdomain: registry
  entity_sequence: 2
  file_sequence: 0

fields:
  # Foreign key to domain
  fk_domain:
    type: ref(domain)
    nullable: false
    description: "Parent domain"
    on_delete: cascade

  subdomain_number:
    type: text
    nullable: false
    description: "Subdomain number within domain (1-9)"
    validation:
      pattern: "^[1-9]$"

  subdomain_name:
    type: text
    nullable: false
    description: "Canonical subdomain name"
    validation:
      max_length: 100

  description:
    type: text
    nullable: true

  next_entity_sequence:
    type: integer
    nullable: false
    default: 1
    description: "Auto-increment sequence for entity codes"

indexes:
  - fields: [fk_domain, subdomain_number]
    unique: true
  - fields: [fk_domain, subdomain_name]
    unique: true

fraiseql:
  enabled: true
  queries:
    find_one: true
    find_many: true
    find_by_parent:
      parent: domain
      field: fk_domain
```

**Deliverable**: `entities/specql_registry/subdomain.yaml` (complete, validated)

---

#### Day 5: Entity Registration YAML

**Task**: Create `entities/specql_registry/entity_registration.yaml`

**`entities/specql_registry/entity_registration.yaml`**:
```yaml
entity: entity_registration
schema: specql_registry
description: Registered entities within subdomains

organization:
  table_code: "011113"
  domain: core
  subdomain: registry
  entity_sequence: 3
  file_sequence: 0

fields:
  fk_subdomain:
    type: ref(subdomain)
    nullable: false
    on_delete: cascade

  entity_name:
    type: text
    nullable: false
    description: "Entity name (Contact, Company)"
    validation:
      max_length: 100

  table_code:
    type: text
    nullable: false
    unique: true
    description: "6-digit hierarchical code"
    validation:
      pattern: "^\\d{6}$"

  entity_sequence:
    type: integer
    nullable: false
    description: "Sequence number within subdomain"

  entity_path:
    type: text
    nullable: true
    description: "File path to YAML definition"

indexes:
  - fields: [table_code]
    unique: true
  - fields: [fk_subdomain, entity_name]
    unique: true

fraiseql:
  enabled: true
  queries:
    find_one: true
    find_many: true
    find_by_code:
      field: table_code
```

**Deliverable**: `entities/specql_registry/entity_registration.yaml` (complete, validated)

---

### Week 2: Generation and Validation

#### Day 6-7: Generate Schema

**Task**: Use SpecQL to generate its own schema

**Commands**:
```bash
# Validate YAML definitions
specql validate entities/specql_registry/*.yaml

# Generate PostgreSQL DDL
specql generate entities/specql_registry/*.yaml \
  --output=migrations/specql_registry_generated/

# Output structure:
# migrations/specql_registry_generated/
# ├── 0_schema/
# │   ├── 01_write_side/
# │   │   └── 011_core/
# │   │       └── 0111_registry/
# │   │           ├── 011111_tb_domain.sql
# │   │           ├── 011112_tb_subdomain.sql
# │   │           └── 011113_tb_entity_registration.sql
# │   └── 02_query_side/
# │       └── 021_core/
# │           └── 0211_registry/
# │               ├── 0210110_tv_domain.sql
# │               ├── 0210120_tv_subdomain.sql
# │               └── 0210130_tv_entity_registration.sql
# └── 2_fraiseql/
#     └── metadata.json
```

**Expected Output** (`011111_tb_domain.sql`):
```sql
-- Auto-generated by SpecQL
-- Source: entities/specql_registry/domain.yaml
-- Table Code: 011111

CREATE TABLE specql_registry.tb_domain (
    -- Trinity pattern
    pk_domain INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    identifier TEXT GENERATED ALWAYS AS (domain_name) STORED,

    -- Business fields
    domain_number TEXT NOT NULL UNIQUE,
    domain_name TEXT NOT NULL UNIQUE,
    description TEXT,
    multi_tenant BOOLEAN NOT NULL DEFAULT false,
    aliases TEXT[],

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT chk_domain_number CHECK (domain_number ~ '^[1-9]$'),
    CONSTRAINT chk_domain_name_length CHECK (length(domain_name) <= 100)
);

-- Indexes
CREATE UNIQUE INDEX idx_tb_domain_domain_number ON specql_registry.tb_domain(domain_number);
CREATE UNIQUE INDEX idx_tb_domain_domain_name ON specql_registry.tb_domain(domain_name);

-- FraiseQL annotations
COMMENT ON TABLE specql_registry.tb_domain IS '@fraiseql:table';
COMMENT ON COLUMN specql_registry.tb_domain.domain_number IS '@fraiseql:field';
-- ... more annotations
```

**Deliverable**: Generated SQL files matching current manual schema

---

#### Day 8-9: Compare Schemas

**Task**: Validate generated schema matches manual schema

**Script**: `scripts/compare_schemas.py`

```python
"""Compare manually written schema vs generated schema"""
import psycopg
from pathlib import Path

def compare_schemas(manual_schema: str, generated_schema: str) -> dict:
    """
    Compare two PostgreSQL schemas

    Returns:
        {
            'tables_match': bool,
            'columns_match': bool,
            'indexes_match': bool,
            'constraints_match': bool,
            'differences': list[str]
        }
    """
    # Connect to test database
    with psycopg.connect("postgresql://localhost/specql_test") as conn:
        with conn.cursor() as cur:
            # Apply manual schema
            cur.execute(Path(manual_schema).read_text())
            manual_metadata = extract_metadata(cur, 'specql_registry')

            # Drop schema
            cur.execute("DROP SCHEMA specql_registry CASCADE")

            # Apply generated schema
            cur.execute(Path(generated_schema).read_text())
            generated_metadata = extract_metadata(cur, 'specql_registry')

            # Compare
            return compare_metadata(manual_metadata, generated_metadata)

def extract_metadata(cur, schema: str) -> dict:
    """Extract schema metadata from database"""
    return {
        'tables': get_tables(cur, schema),
        'columns': get_columns(cur, schema),
        'indexes': get_indexes(cur, schema),
        'constraints': get_constraints(cur, schema),
        'foreign_keys': get_foreign_keys(cur, schema),
    }

def get_tables(cur, schema: str) -> list[dict]:
    """Get all tables in schema"""
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
    """, (schema,))
    return [{'name': row[0]} for row in cur.fetchall()]

def get_columns(cur, schema: str) -> list[dict]:
    """Get all columns with types"""
    cur.execute("""
        SELECT table_name, column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s
        ORDER BY table_name, ordinal_position
    """, (schema,))
    return [
        {
            'table': row[0],
            'column': row[1],
            'type': row[2],
            'nullable': row[3],
            'default': row[4]
        }
        for row in cur.fetchall()
    ]

def get_indexes(cur, schema: str) -> list[dict]:
    """Get all indexes"""
    cur.execute("""
        SELECT
            i.indexname,
            i.tablename,
            i.indexdef
        FROM pg_indexes i
        WHERE i.schemaname = %s
        ORDER BY i.tablename, i.indexname
    """, (schema,))
    return [
        {
            'name': row[0],
            'table': row[1],
            'definition': row[2]
        }
        for row in cur.fetchall()
    ]

def compare_metadata(manual: dict, generated: dict) -> dict:
    """Compare two metadata dicts"""
    differences = []

    # Compare tables
    manual_tables = {t['name'] for t in manual['tables']}
    generated_tables = {t['name'] for t in generated['tables']}

    if manual_tables != generated_tables:
        differences.append(f"Table mismatch: {manual_tables ^ generated_tables}")

    # Compare columns
    manual_cols = {(c['table'], c['column'], c['type']) for c in manual['columns']}
    generated_cols = {(c['table'], c['column'], c['type']) for c in generated['columns']}

    if manual_cols != generated_cols:
        differences.append(f"Column mismatch: {manual_cols ^ generated_cols}")

    # Compare indexes
    manual_idx = {i['name'] for i in manual['indexes']}
    generated_idx = {i['name'] for i in generated['indexes']}

    if manual_idx != generated_idx:
        differences.append(f"Index mismatch: {manual_idx ^ generated_idx}")

    return {
        'tables_match': len(manual_tables ^ generated_tables) == 0,
        'columns_match': len(manual_cols ^ generated_cols) == 0,
        'indexes_match': len(manual_idx ^ generated_idx) == 0,
        'differences': differences,
        'success': len(differences) == 0
    }

if __name__ == '__main__':
    result = compare_schemas(
        manual_schema='database/specql_registry_schema.sql',
        generated_schema='migrations/specql_registry_generated/0_schema/**/*.sql'
    )

    if result['success']:
        print("✅ Generated schema matches manual schema perfectly!")
    else:
        print("⚠️ Differences found:")
        for diff in result['differences']:
            print(f"  - {diff}")
```

**Run Comparison**:
```bash
python scripts/compare_schemas.py

# Expected output:
✅ Generated schema matches manual schema perfectly!
  Tables: 3/3 match
  Columns: 23/23 match
  Indexes: 8/8 match
  Constraints: 5/5 match
  Foreign keys: 2/2 match
```

**Deliverable**: Validation that generated schema is equivalent to manual schema

---

#### Day 10: Migration Script

**Task**: Create migration script to apply generated schema

**Script**: `scripts/migrate_to_generated_schema.sh`

```bash
#!/bin/bash
set -e

echo "🔄 Migrating SpecQL registry to generated schema"

# Backup current data
echo "📦 Backing up current data..."
pg_dump -d specql -n specql_registry -F c -f backup/specql_registry_$(date +%Y%m%d_%H%M%S).dump

# Export data to JSON
echo "💾 Exporting data..."
psql -d specql -c "COPY (SELECT row_to_json(t) FROM specql_registry.tb_domain t) TO '/tmp/domains.json'"
psql -d specql -c "COPY (SELECT row_to_json(t) FROM specql_registry.tb_subdomain t) TO '/tmp/subdomains.json'"
psql -d specql -c "COPY (SELECT row_to_json(t) FROM specql_registry.tb_entity_registration t) TO '/tmp/entities.json'"

# Drop old schema
echo "🗑️  Dropping old schema..."
psql -d specql -c "DROP SCHEMA IF EXISTS specql_registry CASCADE"

# Apply generated schema
echo "🏗️  Applying generated schema..."
psql -d specql -f migrations/specql_registry_generated/0_schema/01_write_side/**/*.sql
psql -d specql -f migrations/specql_registry_generated/0_schema/02_query_side/**/*.sql

# Restore data
echo "♻️  Restoring data..."
psql -d specql <<EOF
COPY specql_registry.tb_domain FROM '/tmp/domains.json';
COPY specql_registry.tb_subdomain FROM '/tmp/subdomains.json';
COPY specql_registry.tb_entity_registration FROM '/tmp/entities.json';
EOF

# Verify
echo "✅ Verifying data integrity..."
psql -d specql <<EOF
SELECT 'Domains: ' || count(*) FROM specql_registry.tb_domain;
SELECT 'Subdomains: ' || count(*) FROM specql_registry.tb_subdomain;
SELECT 'Entities: ' || count(*) FROM specql_registry.tb_entity_registration;
EOF

echo "✅ Migration complete!"
```

**Test Migration**:
```bash
# Test on development database
./scripts/migrate_to_generated_schema.sh

# Expected output:
🔄 Migrating SpecQL registry to generated schema
📦 Backing up current data...
💾 Exporting data...
🗑️  Dropping old schema...
🏗️  Applying generated schema...
♻️  Restoring data...
✅ Verifying data integrity...
  Domains: 9
  Subdomains: 42
  Entities: 234
✅ Migration complete!
```

**Deliverable**: Migration script with rollback capability

---

## 6.3 Phase 6 Deliverables

### Must Have ✅

- [ ] `entities/specql_registry/domain.yaml` - Complete YAML definition
- [ ] `entities/specql_registry/subdomain.yaml` - Complete YAML definition
- [ ] `entities/specql_registry/entity_registration.yaml` - Complete YAML definition
- [ ] Generated SQL matches manual SQL (100% equivalence)
- [ ] Migration script with backup/restore
- [ ] Schema comparison validation passes
- [ ] All existing tests still pass
- [ ] Documentation updated

### Nice to Have ⭐

- [ ] Actions for domain registration (CREATE, UPDATE operations)
- [ ] Helper functions (get_next_entity_code, validate_domain_number)
- [ ] Performance benchmarks (manual vs generated schema)
- [ ] CI/CD integration for schema validation

---

## 6.4 Phase 6 Testing Strategy

### Unit Tests

```python
def test_domain_yaml_valid():
    """Test domain YAML is valid SpecQL"""
    yaml_file = Path('entities/specql_registry/domain.yaml')
    entity = EntityParser().parse(yaml_file.read_text())

    assert entity.entity_name == 'domain'
    assert entity.schema == 'specql_registry'
    assert 'domain_number' in entity.fields
    assert 'domain_name' in entity.fields

def test_generated_schema_has_trinity_pattern():
    """Test generated schema includes Trinity pattern"""
    sql = Path('migrations/specql_registry_generated/.../tb_domain.sql').read_text()

    assert 'pk_domain' in sql
    assert 'id UUID' in sql
    assert 'identifier TEXT' in sql
```

### Integration Tests

```python
def test_generated_schema_functional():
    """Test generated schema works with repository"""
    # Apply generated schema
    apply_schema('migrations/specql_registry_generated/')

    # Create repository
    repo = PostgreSQLDomainRepository(db_url)

    # Test CRUD operations
    domain = Domain(DomainNumber('1'), 'test', None, False)
    repo.save(domain)

    loaded = repo.get('1')
    assert loaded.domain_name == 'test'

def test_migration_preserves_data():
    """Test migration script preserves all data"""
    # Snapshot current data
    before = snapshot_database()

    # Run migration
    run_migration_script()

    # Compare data
    after = snapshot_database()
    assert before == after
```

---

## 6.5 Phase 6 Success Criteria

### Technical Success

- ✅ Generated schema 100% equivalent to manual schema
- ✅ All 9 domains migrate successfully
- ✅ All 42 subdomains migrate successfully
- ✅ All 234 entities migrate successfully
- ✅ Zero data loss during migration
- ✅ Performance equivalent or better
- ✅ All existing tests pass

### Business Success

- ✅ SpecQL generates its own schema (dogfooding proof)
- ✅ Can regenerate schema from YAML anytime
- ✅ Documentation shows end-to-end example
- ✅ Confidence in SpecQL's generation capabilities

---

# Phase 7: Dual Interface Architecture

**Duration**: 2 weeks
**Goal**: Add GraphQL API alongside existing CLI
**Status**: Designed but not implemented (0%)

---

## 7.1 Overview

### The Concept

Add **FraiseQL GraphQL API** for registry access while keeping existing CLI.

**Current State (CLI only)**:
```bash
# CLI commands
specql registry list-domains
specql registry get-domain crm
specql registry allocate-code --domain=crm --subdomain=customer --entity=Contact
```

**Future State (CLI + GraphQL)**:
```bash
# CLI (same as before)
specql registry list-domains

# GraphQL API (new)
curl -X POST http://localhost:4000/graphql -d '{
  "query": "{ domains { domainName description } }"
}'
```

**Architecture**:
```
┌─────────────────────────────────────────────────────┐
│         Presentation Layer (2 Interfaces)           │
│                                                      │
│  ┌──────────────────┐       ┌──────────────────┐   │
│  │  CLI (Click)     │       │  GraphQL         │   │
│  │  src/cli/        │       │  (FraiseQL)      │   │
│  │                  │       │  src/presentation│   │
│  │  registry.py     │       │  /fraiseql/      │   │
│  │  <10 lines each  │       │  <10 lines each  │   │
│  └────────┬─────────┘       └────────┬─────────┘   │
└───────────┼──────────────────────────┼──────────────┘
            │                          │
            └──────────┬───────────────┘
                       │ Both call same services
┌──────────────────────▼──────────────────────────────┐
│          Application Services (SHARED)               │
│  • DomainService                                    │
│  • PatternService                                   │
│  (Same services, zero duplication)                  │
└─────────────────────────────────────────────────────┘
```

---

## 7.2 Phase 7 Detailed Timeline

### Week 3: CLI Refactoring

#### Day 11-12: Refactor CLI to Thin Wrapper

**Task**: Move business logic from CLI to services

**Current** (`src/cli/registry.py`):
```python
@click.command()
def list_domains():
    """List all domains"""
    # ❌ Business logic in CLI
    with open('registry/domain_registry.yaml') as f:
        data = yaml.load(f)

    for domain_num, domain_data in data['domains'].items():
        click.echo(f"{domain_num}: {domain_data['name']}")
```

**Refactored** (`src/cli/registry.py`):
```python
from src.application.services.domain_service_factory import get_domain_service

@click.command()
def list_domains():
    """List all domains (thin wrapper)"""
    # ✅ Delegate to service
    service = get_domain_service()
    domains = service.list_all_domains()

    # ✅ Only formatting logic in CLI
    for domain in domains:
        click.echo(f"{domain.domain_number}: {domain.domain_name}")
```

**Refactor All Commands**:

1. `list-domains` → `DomainService.list_all_domains()`
2. `get-domain` → `DomainService.get_domain(name)`
3. `register-domain` → `DomainService.register_domain(...)`
4. `allocate-code` → `DomainService.allocate_entity_code(...)`
5. `list-subdomains` → `DomainService.get_subdomains(domain_name)`

**Target**: Each CLI command is **<10 lines** (just formatting)

**Deliverable**: Refactored CLI with zero business logic

---

#### Day 13: Create Presentation Layer Structure

**Task**: Organize CLI as part of presentation layer

**New Structure**:
```
src/
├── presentation/              # NEW: Presentation layer
│   ├── __init__.py
│   ├── cli/                   # Refactored CLI
│   │   ├── __init__.py
│   │   ├── registry_commands.py    # Domain registry commands
│   │   ├── pattern_commands.py     # Pattern library commands
│   │   └── generate_commands.py    # Generation commands
│   └── fraiseql/              # NEW: GraphQL interface (next week)
│       └── __init__.py
│
├── application/               # EXISTING: Services layer
│   └── services/
│       ├── domain_service.py
│       └── pattern_service.py
│
├── domain/                    # EXISTING: Domain layer
└── infrastructure/            # EXISTING: Infrastructure layer
```

**Move Commands**:
```bash
# Move CLI files to presentation layer
mv src/cli/registry.py src/presentation/cli/registry_commands.py
mv src/cli/patterns.py src/presentation/cli/pattern_commands.py
mv src/cli/generate.py src/presentation/cli/generate_commands.py
```

**Update Imports**:
```python
# src/cli/__init__.py
# OLD: from src.cli.registry import registry
# NEW: from src.presentation.cli.registry_commands import registry
```

**Deliverable**: CLI organized under `src/presentation/cli/`

---

### Week 4: GraphQL Interface

#### Day 14-15: FraiseQL Types

**Task**: Define GraphQL types for registry

**Create**: `src/presentation/fraiseql/types.py`

```python
"""FraiseQL GraphQL Types for SpecQL Registry"""
from fraiseql import type as fraiseql_type, field

@fraiseql_type
class Domain:
    """Domain aggregate in registry"""

    domain_number: str = field(description="Single digit domain number (1-9)")
    domain_name: str = field(description="Canonical domain name")
    description: str | None = field(description="Human-readable description")
    multi_tenant: bool = field(description="Requires tenant_id?")
    aliases: list[str] = field(description="Alternative names")

    # Relationships
    subdomains: list["Subdomain"] = field(description="Subdomains in this domain")

@fraiseql_type
class Subdomain:
    """Subdomain entity"""

    subdomain_number: str = field(description="Subdomain number (1-9)")
    subdomain_name: str = field(description="Canonical subdomain name")
    description: str | None = field(description="Human-readable description")
    next_entity_sequence: int = field(description="Auto-increment sequence")

    # Relationships
    domain: Domain = field(description="Parent domain")
    entities: list["EntityRegistration"] = field(description="Registered entities")

@fraiseql_type
class EntityRegistration:
    """Registered entity"""

    entity_name: str = field(description="Entity name (Contact, Company)")
    table_code: str = field(description="6-digit hierarchical code")
    entity_sequence: int = field(description="Sequence within subdomain")
    entity_path: str | None = field(description="Path to YAML definition")

    # Relationships
    subdomain: Subdomain = field(description="Parent subdomain")

@fraiseql_type
class Pattern:
    """Pattern from pattern library"""

    name: str = field(description="Pattern name")
    category: str = field(description="Pattern category (workflow, validation, etc.)")
    description: str = field(description="What the pattern does")
    times_instantiated: int = field(description="Usage count")
    complexity_score: float | None = field(description="Complexity score (0-10)")
    deprecated: bool = field(description="Is pattern deprecated?")
```

**Deliverable**: GraphQL type definitions

---

#### Day 16-17: FraiseQL Queries

**Task**: Implement GraphQL queries

**Create**: `src/presentation/fraiseql/queries.py`

```python
"""FraiseQL Queries for SpecQL Registry"""
from fraiseql import query
from src.application.services.domain_service_factory import get_domain_service
from src.application.services.pattern_service_factory import get_pattern_service
from src.presentation.fraiseql.types import Domain, Subdomain, Pattern

@query
async def domains(info) -> list[Domain]:
    """List all domains"""
    service = get_domain_service()
    domain_entities = service.list_all_domains()

    # Convert domain entities to GraphQL types
    return [
        Domain(
            domain_number=d.domain_number.value,
            domain_name=d.domain_name,
            description=d.description,
            multi_tenant=d.multi_tenant,
            aliases=d.aliases,
            subdomains=[
                Subdomain(
                    subdomain_number=sd.subdomain_number,
                    subdomain_name=sd.subdomain_name,
                    description=sd.description,
                    next_entity_sequence=sd.next_entity_sequence,
                    domain=None,  # Avoid circular reference
                    entities=[]   # Load separately if needed
                )
                for sd in d.subdomains.values()
            ]
        )
        for d in domain_entities
    ]

@query
async def domain(info, name: str) -> Domain | None:
    """Get domain by name"""
    service = get_domain_service()
    domain_entity = service.get_domain_by_name(name)

    if not domain_entity:
        return None

    return Domain(
        domain_number=domain_entity.domain_number.value,
        domain_name=domain_entity.domain_name,
        description=domain_entity.description,
        multi_tenant=domain_entity.multi_tenant,
        aliases=domain_entity.aliases,
        subdomains=[...]  # Map subdomains
    )

@query
async def patterns(info, category: str | None = None) -> list[Pattern]:
    """List patterns, optionally filtered by category"""
    service = get_pattern_service()

    if category:
        pattern_entities = service.find_patterns_by_category(category)
    else:
        pattern_entities = service.list_all_patterns()

    return [
        Pattern(
            name=p.name,
            category=p.category.value,
            description=p.description,
            times_instantiated=p.times_instantiated,
            complexity_score=p.complexity_score,
            deprecated=p.deprecated
        )
        for p in pattern_entities
    ]

@query
async def pattern(info, name: str) -> Pattern | None:
    """Get pattern by name"""
    service = get_pattern_service()
    pattern_entity = service.get_pattern(name)

    if not pattern_entity:
        return None

    return Pattern(
        name=pattern_entity.name,
        category=pattern_entity.category.value,
        description=pattern_entity.description,
        times_instantiated=pattern_entity.times_instantiated,
        complexity_score=pattern_entity.complexity_score,
        deprecated=pattern_entity.deprecated
    )
```

**Example Queries**:
```graphql
# List all domains
query {
  domains {
    domainNumber
    domainName
    description
    subdomains {
      subdomainName
    }
  }
}

# Get specific domain
query {
  domain(name: "crm") {
    domainNumber
    domainName
    subdomains {
      subdomainName
      nextEntitySequence
    }
  }
}

# List patterns by category
query {
  patterns(category: "validation") {
    name
    description
    timesInstantiated
  }
}
```

**Deliverable**: GraphQL queries with service delegation

---

#### Day 18-19: FraiseQL Mutations

**Task**: Implement GraphQL mutations

**Create**: `src/presentation/fraiseql/mutations.py`

```python
"""FraiseQL Mutations for SpecQL Registry"""
from fraiseql import mutation, input_type, field
from src.application.services.domain_service_factory import get_domain_service
from src.presentation.fraiseql.types import Domain

@input_type
class RegisterDomainInput:
    """Input for registering a new domain"""
    domain_number: str = field(description="Domain number (1-9)")
    domain_name: str = field(description="Canonical name")
    description: str | None = field(description="Description")
    multi_tenant: bool = field(description="Requires tenant_id?")
    aliases: list[str] | None = field(description="Alternative names")

@input_type
class AllocateEntityCodeInput:
    """Input for allocating entity code"""
    domain_name: str = field(description="Domain name")
    subdomain_name: str = field(description="Subdomain name")
    entity_name: str = field(description="Entity name")

@mutation
async def register_domain(info, input: RegisterDomainInput) -> Domain:
    """Register a new domain"""
    service = get_domain_service()

    domain_entity = service.register_domain(
        domain_number=input.domain_number,
        domain_name=input.domain_name,
        description=input.description,
        multi_tenant=input.multi_tenant,
        aliases=input.aliases or []
    )

    return Domain(
        domain_number=domain_entity.domain_number.value,
        domain_name=domain_entity.domain_name,
        description=domain_entity.description,
        multi_tenant=domain_entity.multi_tenant,
        aliases=domain_entity.aliases,
        subdomains=[]
    )

@mutation
async def allocate_entity_code(info, input: AllocateEntityCodeInput) -> str:
    """Allocate 6-digit entity code"""
    service = get_domain_service()

    table_code = service.allocate_entity_code(
        domain_name=input.domain_name,
        subdomain_name=input.subdomain_name,
        entity_name=input.entity_name
    )

    return str(table_code)
```

**Example Mutations**:
```graphql
# Register new domain
mutation {
  registerDomain(input: {
    domainNumber: "8"
    domainName: "analytics"
    description: "Analytics and reporting"
    multiTenant: true
    aliases: ["reporting", "metrics"]
  }) {
    domainNumber
    domainName
  }
}

# Allocate entity code
mutation {
  allocateEntityCode(input: {
    domainName: "crm"
    subdomainName: "customer"
    entityName: "Contact"
  })
}
```

**Deliverable**: GraphQL mutations with service delegation

---

#### Day 20: FraiseQL Server Setup

**Task**: Create FastAPI server with FraiseQL

**Create**: `src/presentation/fraiseql/server.py`

```python
"""FraiseQL GraphQL Server"""
from fastapi import FastAPI
from fraiseql import create_fraiseql_app
from src.presentation.fraiseql.types import Domain, Subdomain, Pattern
from src.presentation.fraiseql.queries import domains, domain, patterns, pattern
from src.presentation.fraiseql.mutations import register_domain, allocate_entity_code

# Create FastAPI app
app = FastAPI(title="SpecQL Registry API")

# Create FraiseQL app with all types, queries, and mutations
fraiseql_app = create_fraiseql_app(
    types=[Domain, Subdomain, Pattern],
    queries=[domains, domain, patterns, pattern],
    mutations=[register_domain, allocate_entity_code],
    context={}  # Services created per-request
)

# Mount FraiseQL at /graphql
app.mount("/graphql", fraiseql_app)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SpecQL Registry API",
        "graphql": "/graphql",
        "playground": "/graphql/playground"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
```

**Add CLI Command**:
```python
# src/cli/server.py
import click

@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=4000, help="Port to bind to")
def serve(host: str, port: int):
    """Start GraphQL API server"""
    import uvicorn
    from src.presentation.fraiseql.server import app

    click.echo(f"🚀 Starting SpecQL Registry API on {host}:{port}")
    click.echo(f"📊 GraphQL Playground: http://{host}:{port}/graphql/playground")

    uvicorn.run(app, host=host, port=port)
```

**Usage**:
```bash
# Start GraphQL server
specql serve

# Output:
🚀 Starting SpecQL Registry API on 0.0.0.0:4000
📊 GraphQL Playground: http://0.0.0.0:4000/graphql/playground

# Access GraphQL playground
open http://localhost:4000/graphql/playground
```

**Deliverable**: Working GraphQL server

---

## 7.3 Phase 7 Deliverables

### Must Have ✅

- [ ] CLI refactored to thin wrappers (<10 lines per command)
- [ ] `src/presentation/cli/` structure created
- [ ] `src/presentation/fraiseql/` structure created
- [ ] GraphQL types for Domain, Subdomain, Pattern
- [ ] GraphQL queries (list, get by name)
- [ ] GraphQL mutations (register, allocate)
- [ ] FastAPI server with FraiseQL mounted
- [ ] `specql serve` command to start server
- [ ] Documentation with GraphQL examples
- [ ] Both CLI and GraphQL call same services (zero duplication)

### Nice to Have ⭐

- [ ] GraphQL subscriptions (for real-time updates)
- [ ] Authentication/authorization for GraphQL API
- [ ] Rate limiting
- [ ] GraphQL query complexity analysis
- [ ] OpenAPI docs at /docs

---

## 7.4 Phase 7 Testing Strategy

### Consistency Tests

```python
def test_cli_and_graphql_return_same_data():
    """Test CLI and GraphQL return identical results"""
    # Via CLI
    cli_runner = CliRunner()
    cli_result = cli_runner.invoke(list_domains)
    cli_domains = parse_cli_output(cli_result.output)

    # Via GraphQL
    graphql_result = client.query("""
        query { domains { domainName } }
    """)
    graphql_domains = [d['domainName'] for d in graphql_result['data']['domains']]

    # Must be identical
    assert set(cli_domains) == set(graphql_domains)

def test_both_interfaces_use_same_service():
    """Test both interfaces delegate to same service"""
    with patch('src.application.services.domain_service.DomainService') as mock:
        # Call via CLI
        cli_runner = CliRunner()
        cli_runner.invoke(list_domains)

        # Call via GraphQL
        client.query("""query { domains { domainName } }""")

        # Service should be called twice (same service)
        assert mock.list_all_domains.call_count == 2
```

### Integration Tests

```python
def test_graphql_query_domains():
    """Test GraphQL query returns domains"""
    response = client.post('/graphql', json={
        'query': '{ domains { domainName } }'
    })

    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    assert 'domains' in data['data']
    assert len(data['data']['domains']) > 0

def test_graphql_mutation_allocate_code():
    """Test GraphQL mutation allocates code"""
    response = client.post('/graphql', json={
        'query': '''
            mutation {
                allocateEntityCode(input: {
                    domainName: "crm"
                    subdomainName: "customer"
                    entityName: "Contact"
                })
            }
        '''
    })

    assert response.status_code == 200
    data = response.json()
    code = data['data']['allocateEntityCode']
    assert len(code) == 6
    assert code.isdigit()
```

---

## 7.5 Phase 7 Success Criteria

### Technical Success

- ✅ CLI commands all <10 lines (thin wrappers)
- ✅ GraphQL queries return correct data
- ✅ GraphQL mutations work correctly
- ✅ Both interfaces call same services (zero duplication)
- ✅ Consistency tests pass (CLI == GraphQL)
- ✅ Server starts without errors
- ✅ GraphQL Playground accessible

### Business Success

- ✅ Developers can query registry via GraphQL
- ✅ Programmatic access to pattern library
- ✅ Remote access to registry (not just CLI)
- ✅ Better developer experience
- ✅ Documentation shows both interfaces

---

# Phase 8: Pattern Library Complete

**Duration**: 2 weeks
**Goal**: Complete PostgreSQL migration with semantic search
**Status**: 80% complete (needs pgvector integration)

---

## 8.1 Overview

### The Concept

Complete pattern library migration with **semantic search** using pgvector.

**Current State** (80% done):
- ✅ Pattern entity in PostgreSQL
- ✅ Repository pattern implemented
- ✅ PatternService with PostgreSQL
- ⚠️ Embeddings stored but not used for search

**Future State** (100%):
- ✅ All of above
- ✅ **Semantic search with pgvector**
- ✅ Natural language pattern queries
- ✅ "Find patterns like X"
- ✅ Pattern recommendations

---

## 8.2 Phase 8 Detailed Timeline

### Week 5: pgvector Integration

#### Day 21-22: pgvector Schema

**Task**: Add pgvector extension and update schema

**SQL Migration**: `migrations/pattern_library_pgvector.sql`

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Update pattern table with vector column
ALTER TABLE pattern_library.tb_pattern
ADD COLUMN embedding vector(384);  -- 384-dimensional vectors

-- Create vector index for fast similarity search
CREATE INDEX idx_pattern_embedding ON pattern_library.tb_pattern
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Add helper function for similarity search
CREATE OR REPLACE FUNCTION pattern_library.fn_find_similar_patterns(
    p_query_embedding vector(384),
    p_threshold float DEFAULT 0.7,
    p_limit int DEFAULT 10
)
RETURNS TABLE (
    pattern_name TEXT,
    similarity FLOAT,
    category TEXT,
    description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.name,
        1 - (p.embedding <=> p_query_embedding) AS similarity,
        p.category,
        p.description
    FROM pattern_library.tb_pattern p
    WHERE p.embedding IS NOT NULL
        AND p.deprecated = false
        AND (1 - (p.embedding <=> p_query_embedding)) >= p_threshold
    ORDER BY p.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Add function for pattern recommendations
CREATE OR REPLACE FUNCTION pattern_library.fn_recommend_patterns(
    p_pattern_name TEXT,
    p_limit int DEFAULT 5
)
RETURNS TABLE (
    pattern_name TEXT,
    similarity FLOAT,
    category TEXT,
    description TEXT,
    times_instantiated INT
) AS $$
DECLARE
    v_embedding vector(384);
BEGIN
    -- Get embedding for source pattern
    SELECT embedding INTO v_embedding
    FROM pattern_library.tb_pattern
    WHERE name = p_pattern_name;

    IF v_embedding IS NULL THEN
        RAISE EXCEPTION 'Pattern % not found or has no embedding', p_pattern_name;
    END IF;

    -- Find similar patterns
    RETURN QUERY
    SELECT
        p.name,
        1 - (p.embedding <=> v_embedding) AS similarity,
        p.category,
        p.description,
        p.times_instantiated
    FROM pattern_library.tb_pattern p
    WHERE p.name != p_pattern_name
        AND p.embedding IS NOT NULL
        AND p.deprecated = false
    ORDER BY p.embedding <=> v_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
```

**Apply Migration**:
```bash
psql -d specql -f migrations/pattern_library_pgvector.sql

# Verify pgvector is working
psql -d specql -c "SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector"
# Should return: 5.196152422706632
```

**Deliverable**: pgvector schema with similarity search functions

---

#### Day 23-24: Embedding Service

**Task**: Create embedding generation service

**Create**: `src/application/services/embedding_service.py`

```python
"""Embedding Service for Pattern Similarity Search"""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """
    Generate embeddings for patterns using sentence-transformers

    Uses all-MiniLM-L6-v2 model (384 dimensions, fast, good quality)
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text

        Args:
            text: Text to embed (pattern description, name, etc.)

        Returns:
            384-dimensional embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_pattern_embedding(self, pattern) -> List[float]:
        """
        Generate embedding for a pattern

        Combines pattern name, description, and category for rich representation
        """
        text = f"{pattern.name}. {pattern.category.value}. {pattern.description}"
        return self.generate_embedding(text)

    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (more efficient)"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]

    def cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        a = np.array(emb1)
        b = np.array(emb2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

**Add to PatternService**:
```python
# src/application/services/pattern_service.py
from src.application.services.embedding_service import EmbeddingService

class PatternService:
    def __init__(self, repository: PatternRepository):
        self.repository = repository
        self.embedding_service = EmbeddingService()

    def create_pattern_with_embedding(
        self,
        name: str,
        category: str,
        description: str,
        **kwargs
    ) -> Pattern:
        """Create pattern and generate embedding"""
        pattern = Pattern(
            id=None,
            name=name,
            category=PatternCategory(category),
            description=description,
            **kwargs
        )

        # Generate embedding
        embedding = self.embedding_service.generate_pattern_embedding(pattern)
        pattern.embedding = embedding

        self.repository.save(pattern)
        return pattern

    def update_pattern_embedding(self, pattern_name: str) -> None:
        """Regenerate embedding for existing pattern"""
        pattern = self.repository.get(pattern_name)

        embedding = self.embedding_service.generate_pattern_embedding(pattern)
        pattern.update_embedding(embedding)

        self.repository.save(pattern)

    def batch_update_embeddings(self) -> int:
        """Update embeddings for all patterns missing them"""
        patterns = self.repository.list_all()
        updated = 0

        for pattern in patterns:
            if not pattern.has_embedding:
                embedding = self.embedding_service.generate_pattern_embedding(pattern)
                pattern.embedding = embedding
                self.repository.save(pattern)
                updated += 1

        return updated
```

**Deliverable**: Embedding generation service

---

#### Day 25: Semantic Search Repository

**Task**: Add semantic search to pattern repository

**Update**: `src/infrastructure/repositories/postgresql_pattern_repository.py`

```python
class PostgreSQLPatternRepository:
    """PostgreSQL pattern repository with semantic search"""

    def find_similar_by_embedding(
        self,
        embedding: List[float],
        threshold: float = 0.7,
        limit: int = 10
    ) -> List[Pattern]:
        """
        Find patterns similar to given embedding

        Args:
            embedding: Query embedding vector
            threshold: Minimum similarity score (0-1)
            limit: Maximum number of results

        Returns:
            List of similar patterns ordered by similarity
        """
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Call pgvector similarity search function
                cur.execute("""
                    SELECT
                        pattern_name,
                        similarity,
                        category,
                        description
                    FROM pattern_library.fn_find_similar_patterns(
                        %s::vector(384),
                        %s,
                        %s
                    )
                """, (embedding, threshold, limit))

                results = []
                for row in cur.fetchall():
                    pattern_name = row[0]
                    # Load full pattern
                    pattern = self.get(pattern_name)
                    results.append(pattern)

                return results

    def find_similar_to_pattern(
        self,
        pattern_name: str,
        limit: int = 5
    ) -> List[Pattern]:
        """
        Find patterns similar to given pattern

        Args:
            pattern_name: Name of source pattern
            limit: Maximum number of results

        Returns:
            List of similar patterns
        """
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        pattern_name,
                        similarity,
                        category,
                        description,
                        times_instantiated
                    FROM pattern_library.fn_recommend_patterns(%s, %s)
                """, (pattern_name, limit))

                results = []
                for row in cur.fetchall():
                    pattern_name = row[0]
                    pattern = self.get(pattern_name)
                    results.append(pattern)

                return results

    def search_by_text(
        self,
        query: str,
        threshold: float = 0.7,
        limit: int = 10
    ) -> List[Pattern]:
        """
        Semantic search for patterns using natural language

        Args:
            query: Natural language query (e.g., "validate email addresses")
            threshold: Minimum similarity score
            limit: Maximum results

        Returns:
            Relevant patterns
        """
        from src.application.services.embedding_service import EmbeddingService

        # Generate embedding for query
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.generate_embedding(query)

        # Search using embedding
        return self.find_similar_by_embedding(query_embedding, threshold, limit)
```

**Deliverable**: Semantic search in repository

---

### Week 6: CLI Integration and Testing

#### Day 26-27: Semantic Search CLI

**Task**: Add semantic search commands to CLI

**Create**: `src/cli/pattern_search.py`

```python
"""Pattern semantic search CLI commands"""
import click
from src.application.services.pattern_service_factory import get_pattern_service

@click.group()
def pattern_search():
    """Semantic pattern search commands"""
    pass

@pattern_search.command()
@click.argument('query')
@click.option('--threshold', default=0.7, help='Minimum similarity (0-1)')
@click.option('--limit', default=10, help='Maximum results')
def search(query: str, threshold: float, limit: int):
    """
    Search patterns using natural language

    Examples:
        specql pattern-search search "validate email addresses"
        specql pattern-search search "audit trail" --threshold=0.8
    """
    service = get_pattern_service()
    patterns = service.search_patterns_by_text(query, threshold, limit)

    if not patterns:
        click.echo("No patterns found matching query")
        return

    click.echo(f"\n🔍 Found {len(patterns)} patterns matching '{query}':\n")

    for i, pattern in enumerate(patterns, 1):
        click.echo(f"{i}. {pattern.name}")
        click.echo(f"   Category: {pattern.category.value}")
        click.echo(f"   Description: {pattern.description}")
        click.echo(f"   Used {pattern.times_instantiated} times")
        if pattern.complexity_score:
            click.echo(f"   Complexity: {pattern.complexity_score}/10")
        click.echo()

@pattern_search.command()
@click.argument('pattern_name')
@click.option('--limit', default=5, help='Number of recommendations')
def similar(pattern_name: str, limit: int):
    """
    Find patterns similar to given pattern

    Examples:
        specql pattern-search similar email_validation
        specql pattern-search similar audit_trail --limit=10
    """
    service = get_pattern_service()

    try:
        similar_patterns = service.find_similar_patterns(pattern_name, limit)
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
        return

    if not similar_patterns:
        click.echo(f"No similar patterns found for '{pattern_name}'")
        return

    click.echo(f"\n🎯 Patterns similar to '{pattern_name}':\n")

    for i, pattern in enumerate(similar_patterns, 1):
        click.echo(f"{i}. {pattern.name}")
        click.echo(f"   Category: {pattern.category.value}")
        click.echo(f"   Description: {pattern.description}")
        click.echo()

@pattern_search.command()
def update_embeddings():
    """
    Update embeddings for all patterns

    Run this after adding new patterns or changing descriptions
    """
    service = get_pattern_service()

    click.echo("🔄 Updating pattern embeddings...")
    updated = service.batch_update_embeddings()

    click.echo(f"✅ Updated embeddings for {updated} patterns")

@pattern_search.command()
@click.argument('pattern_name')
def recommend(pattern_name: str):
    """
    Get pattern recommendations based on usage

    Suggests patterns that are often used together
    """
    service = get_pattern_service()

    recommendations = service.get_pattern_recommendations(pattern_name)

    if not recommendations:
        click.echo(f"No recommendations available for '{pattern_name}'")
        return

    click.echo(f"\n💡 If you're using '{pattern_name}', consider these patterns:\n")

    for i, pattern in enumerate(recommendations, 1):
        click.echo(f"{i}. {pattern.name}")
        click.echo(f"   Why: Often used together")
        click.echo(f"   Category: {pattern.category.value}")
        click.echo()
```

**Usage Examples**:
```bash
# Natural language search
specql pattern-search search "validate email addresses"
# Output:
🔍 Found 3 patterns matching 'validate email addresses':

1. email_validation
   Category: validation
   Description: Validate email format using regex
   Used 23 times
   Complexity: 2/10

2. contact_info_validation
   Category: validation
   Description: Validate contact information (email, phone)
   Used 15 times

3. user_registration_validation
   Category: workflow
   Description: Complete user registration with email validation
   Used 8 times

# Find similar patterns
specql pattern-search similar email_validation
# Output:
🎯 Patterns similar to 'email_validation':

1. phone_validation (92% similar)
   Category: validation
   Description: Validate phone number format

2. url_validation (88% similar)
   Category: validation
   Description: Validate URL format

# Update all embeddings
specql pattern-search update-embeddings
# Output:
🔄 Updating pattern embeddings...
✅ Updated embeddings for 47 patterns
```

**Deliverable**: Full semantic search CLI

---

#### Day 28: GraphQL Semantic Search

**Task**: Add semantic search to GraphQL API

**Update**: `src/presentation/fraiseql/queries.py`

```python
@query
async def search_patterns(
    info,
    query: str,
    threshold: float = 0.7,
    limit: int = 10
) -> list[Pattern]:
    """
    Semantic search for patterns using natural language

    Args:
        query: Natural language query (e.g., "validate email addresses")
        threshold: Minimum similarity score (0-1)
        limit: Maximum number of results
    """
    service = get_pattern_service()
    pattern_entities = service.search_patterns_by_text(query, threshold, limit)

    return [
        Pattern(
            name=p.name,
            category=p.category.value,
            description=p.description,
            times_instantiated=p.times_instantiated,
            complexity_score=p.complexity_score,
            deprecated=p.deprecated
        )
        for p in pattern_entities
    ]

@query
async def similar_patterns(
    info,
    pattern_name: str,
    limit: int = 5
) -> list[Pattern]:
    """Find patterns similar to given pattern"""
    service = get_pattern_service()
    pattern_entities = service.find_similar_patterns(pattern_name, limit)

    return [
        Pattern(
            name=p.name,
            category=p.category.value,
            description=p.description,
            times_instantiated=p.times_instantiated,
            complexity_score=p.complexity_score,
            deprecated=p.deprecated
        )
        for p in pattern_entities
    ]
```

**GraphQL Examples**:
```graphql
# Semantic search
query {
  searchPatterns(
    query: "validate email addresses"
    threshold: 0.7
    limit: 10
  ) {
    name
    category
    description
    timesInstantiated
  }
}

# Find similar patterns
query {
  similarPatterns(
    patternName: "email_validation"
    limit: 5
  ) {
    name
    category
    description
  }
}
```

**Deliverable**: GraphQL semantic search

---

#### Day 29-30: Integration Testing

**Task**: Comprehensive testing of semantic search

**Tests**: `tests/integration/test_semantic_search.py`

```python
"""Integration tests for semantic pattern search"""
import pytest
from src.application.services.pattern_service_factory import get_pattern_service
from src.application.services.embedding_service import EmbeddingService

def test_semantic_search_finds_relevant_patterns():
    """Test semantic search returns relevant patterns"""
    service = get_pattern_service()

    # Search for email validation patterns
    results = service.search_patterns_by_text("validate email addresses", threshold=0.7)

    # Should find email_validation pattern
    pattern_names = [p.name for p in results]
    assert 'email_validation' in pattern_names

    # Should find related patterns
    assert any('email' in name.lower() or 'validation' in name.lower()
               for name in pattern_names)

def test_similar_patterns_returns_related():
    """Test similar pattern search"""
    service = get_pattern_service()

    # Find patterns similar to email_validation
    results = service.find_similar_patterns('email_validation', limit=5)

    # Should return other validation patterns
    assert len(results) > 0
    categories = {p.category.value for p in results}
    assert 'validation' in categories

def test_embeddings_have_correct_dimensions():
    """Test embeddings are 384-dimensional"""
    embedding_service = EmbeddingService()

    embedding = embedding_service.generate_embedding("test pattern")

    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)

def test_cosine_similarity_calculation():
    """Test cosine similarity is correct"""
    embedding_service = EmbeddingService()

    emb1 = embedding_service.generate_embedding("email validation")
    emb2 = embedding_service.generate_embedding("email validation")
    emb3 = embedding_service.generate_embedding("completely different")

    # Identical text should have high similarity
    similarity_same = embedding_service.cosine_similarity(emb1, emb2)
    assert similarity_same > 0.99

    # Different text should have lower similarity
    similarity_diff = embedding_service.cosine_similarity(emb1, emb3)
    assert similarity_diff < 0.9

def test_batch_embedding_generation():
    """Test batch generation is efficient"""
    service = get_pattern_service()
    embedding_service = EmbeddingService()

    # Get all patterns
    patterns = service.list_all_patterns()
    pattern_texts = [p.description for p in patterns[:10]]

    # Generate embeddings in batch
    embeddings = embedding_service.batch_generate_embeddings(pattern_texts)

    # Should return correct number
    assert len(embeddings) == len(pattern_texts)

    # All should be 384-dimensional
    assert all(len(emb) == 384 for emb in embeddings)

def test_search_with_different_thresholds():
    """Test search behavior with different similarity thresholds"""
    service = get_pattern_service()

    query = "validate email addresses"

    # High threshold (strict matching)
    strict_results = service.search_patterns_by_text(query, threshold=0.9, limit=10)

    # Low threshold (loose matching)
    loose_results = service.search_patterns_by_text(query, threshold=0.5, limit=10)

    # Loose should return more results
    assert len(loose_results) >= len(strict_results)

    # Strict results should be subset of loose
    strict_names = {p.name for p in strict_results}
    loose_names = {p.name for p in loose_results}
    assert strict_names.issubset(loose_names)

@pytest.mark.performance
def test_semantic_search_performance():
    """Test semantic search is fast enough"""
    import time

    service = get_pattern_service()

    # Measure search time
    start = time.time()
    results = service.search_patterns_by_text("validate email", threshold=0.7, limit=10)
    duration = time.time() - start

    # Should complete in <100ms
    assert duration < 0.1

    # Should return results
    assert len(results) > 0
```

**Run Tests**:
```bash
# Run integration tests
pytest tests/integration/test_semantic_search.py -v

# Run performance tests
pytest tests/integration/test_semantic_search.py -v -m performance

# Expected output:
tests/integration/test_semantic_search.py::test_semantic_search_finds_relevant_patterns PASSED
tests/integration/test_semantic_search.py::test_similar_patterns_returns_related PASSED
tests/integration/test_semantic_search.py::test_embeddings_have_correct_dimensions PASSED
tests/integration/test_semantic_search.py::test_cosine_similarity_calculation PASSED
tests/integration/test_semantic_search.py::test_batch_embedding_generation PASSED
tests/integration/test_semantic_search.py::test_search_with_different_thresholds PASSED
tests/integration/test_semantic_search.py::test_semantic_search_performance PASSED

======================== 7 passed in 2.34s ========================
```

**Deliverable**: Comprehensive test suite

---

## 8.3 Phase 8 Deliverables

### Must Have ✅

- [ ] pgvector extension enabled
- [ ] Pattern table with vector(384) column
- [ ] Vector similarity search functions (SQL)
- [ ] EmbeddingService with sentence-transformers
- [ ] Semantic search in PostgreSQLPatternRepository
- [ ] CLI commands: `search`, `similar`, `update-embeddings`
- [ ] GraphQL queries: `searchPatterns`, `similarPatterns`
- [ ] Batch embedding generation
- [ ] Integration tests for semantic search
- [ ] Performance tests (<100ms per search)
- [ ] Documentation with examples

### Nice to Have ⭐

- [ ] Pattern recommendation algorithm (usage-based)
- [ ] Multi-language embedding models
- [ ] Fine-tuned embedding model on SpecQL patterns
- [ ] Embedding caching for frequently searched queries
- [ ] Analytics dashboard for pattern usage

---

## 8.4 Phase 8 Testing Strategy

### Unit Tests

```python
def test_embedding_service_generates_384_dim():
    """Test embedding service generates correct dimensions"""
    service = EmbeddingService()
    embedding = service.generate_embedding("test")
    assert len(embedding) == 384

def test_pattern_service_adds_embedding():
    """Test pattern service adds embedding on create"""
    service = PatternService(mock_repository)
    pattern = service.create_pattern_with_embedding(
        name="test",
        category="validation",
        description="Test pattern"
    )
    assert pattern.has_embedding
    assert len(pattern.embedding) == 384
```

### Integration Tests

```python
def test_semantic_search_end_to_end():
    """Test complete semantic search workflow"""
    # Create pattern with embedding
    service = get_pattern_service()
    service.create_pattern_with_embedding(
        name="email_validation",
        category="validation",
        description="Validate email addresses using regex"
    )

    # Search for it
    results = service.search_patterns_by_text("validate email")

    # Should find it
    assert any(p.name == 'email_validation' for p in results)

def test_pgvector_similarity_search():
    """Test pgvector similarity search works"""
    repo = PostgreSQLPatternRepository(db_url)

    # Get a pattern with embedding
    pattern = repo.get('email_validation')
    assert pattern.has_embedding

    # Find similar patterns
    similar = repo.find_similar_by_embedding(pattern.embedding, threshold=0.7)

    # Should return results
    assert len(similar) > 0
```

---

## 8.5 Phase 8 Success Criteria

### Technical Success

- ✅ pgvector extension working
- ✅ Embeddings generated for all patterns
- ✅ Semantic search returns relevant results
- ✅ Search performance <100ms
- ✅ Similarity scores accurate (cosine similarity)
- ✅ Batch embedding generation works
- ✅ All tests passing

### Business Success

- ✅ Users can search patterns with natural language
- ✅ Pattern recommendations improve discovery
- ✅ Cross-project pattern reuse increases
- ✅ Pattern library more useful
- ✅ Developer experience improved

---

# Testing Strategy (All Phases)

## Test Pyramid

```
         /\
        /  \  E2E Tests (5%)
       /────\
      / Inte-\  Integration Tests (15%)
     / gration\
    /──────────\
   /            \  Unit Tests (80%)
  /______________\
```

### Unit Tests (80%)

**Focus**: Test individual components in isolation

```python
# Domain entities
def test_domain_entity_business_logic()
def test_pattern_entity_validation()

# Value objects
def test_domain_number_validation()
def test_table_code_generation()

# Services
def test_domain_service_with_mock_repository()
def test_pattern_service_with_mock_repository()

# Embeddings
def test_embedding_service_generates_correct_dimensions()
```

**Target**: >90% code coverage

---

### Integration Tests (15%)

**Focus**: Test components working together

```python
# Repository tests
def test_postgresql_domain_repository_roundtrip()
def test_pattern_repository_semantic_search()

# Service tests
def test_domain_service_with_real_repository()
def test_pattern_service_end_to_end()

# API tests
def test_graphql_query_returns_data()
def test_cli_and_graphql_consistency()
```

**Target**: All major workflows covered

---

### E2E Tests (5%)

**Focus**: Test complete user workflows

```python
# Phase 6: Self-schema generation
def test_generate_specql_schema_from_yaml()

# Phase 7: Dual interface
def test_cli_and_graphql_return_same_results()

# Phase 8: Semantic search
def test_search_discover_use_pattern_workflow()
```

**Target**: Critical paths only

---

## CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: uv sync
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=term

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: uv sync
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          SPECQL_DB_URL: postgresql://postgres:postgres@localhost/specql

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: uv sync
      - name: Start GraphQL server
        run: specql serve &
      - name: Run E2E tests
        run: pytest tests/e2e/ -v
```

---

# Deployment Plan

## Phase 6 Deployment

**Goal**: Migrate to SpecQL-generated schema

**Steps**:
1. Generate schema from YAML: `specql generate entities/specql_registry/*.yaml`
2. Validate generated schema matches manual: `python scripts/compare_schemas.py`
3. Backup current data: `pg_dump -n specql_registry`
4. Apply generated schema: `./scripts/migrate_to_generated_schema.sh`
5. Verify data integrity: Compare row counts
6. Monitor for 1 week
7. Archive manual SQL files

**Rollback**: Restore from backup

---

## Phase 7 Deployment

**Goal**: Add GraphQL API alongside CLI

**Steps**:
1. Deploy refactored CLI (no behavior change)
2. Start GraphQL server: `specql serve --port=4000`
3. Test GraphQL queries in Playground
4. Add to production stack (Docker/Kubernetes)
5. Document GraphQL API (examples)
6. Announce to users

**Rollback**: Stop GraphQL server, CLI still works

---

## Phase 8 Deployment

**Goal**: Enable semantic pattern search

**Steps**:
1. Install pgvector extension: `CREATE EXTENSION vector`
2. Run migration: `psql -f migrations/pattern_library_pgvector.sql`
3. Generate embeddings: `specql pattern-search update-embeddings`
4. Test semantic search: `specql pattern-search search "validate email"`
5. Monitor query performance
6. Document semantic search usage
7. Announce feature

**Rollback**: Semantic search is additive, no rollback needed

---

# Success Metrics

## Phase 6 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Schema Equivalence** | 100% | Compare generated vs manual |
| **Data Integrity** | Zero loss | Row count comparison |
| **Migration Time** | <5 minutes | Timed execution |
| **Regeneration Time** | <30 seconds | `specql generate` duration |

---

## Phase 7 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **CLI LOC Reduction** | <10 lines/cmd | Count lines per command |
| **Code Duplication** | 0% | CLI vs GraphQL logic shared |
| **GraphQL Latency** | <100ms | Query response time |
| **API Availability** | >99.9% | Uptime monitoring |

---

## Phase 8 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Search Relevance** | >90% | User feedback on results |
| **Search Latency** | <100ms | pgvector query time |
| **Pattern Discovery** | +50% | Patterns found via search |
| **Embedding Coverage** | 100% | Patterns with embeddings |

---

# Risk Assessment

## Phase 6 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Generated schema differs | Medium | High | Comprehensive comparison script |
| Data loss during migration | Low | Critical | Backup before migration |
| Performance degradation | Low | Medium | Benchmark before/after |

---

## Phase 7 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| GraphQL bugs affect CLI | Low | High | Shared services tested independently |
| Security vulnerabilities | Medium | High | Add auth/rate limiting |
| Server crashes | Low | Medium | Health checks, auto-restart |

---

## Phase 8 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Poor search relevance | Medium | Medium | Fine-tune threshold, test queries |
| Embedding generation slow | Low | Low | Batch generation, caching |
| pgvector performance | Low | Medium | Proper indexes, monitoring |

---

# Timeline Summary

```
Week 1-2:  Phase 6 (SpecQL Self-Schema)
  Day 1-5:   YAML definitions
  Day 6-10:  Generate, validate, migrate

Week 3-4:  Phase 7 (Dual Interface)
  Day 11-13: Refactor CLI
  Day 14-20: GraphQL API

Week 5-6:  Phase 8 (Pattern Library Complete)
  Day 21-25: pgvector integration
  Day 26-30: CLI/GraphQL semantic search + testing
```

**Total**: 6 weeks (30 working days)

---

# Conclusion

## What You Get After Phases 6-8

### Phase 6 Complete

- ✅ SpecQL generates its own schema (dogfooding)
- ✅ Can regenerate schema anytime from YAML
- ✅ Trust in SpecQL's generation capabilities
- ✅ Documentation shows end-to-end example

### Phase 7 Complete

- ✅ CLI + GraphQL API (dual interface)
- ✅ Both interfaces call same services (zero duplication)
- ✅ Programmatic access to registry
- ✅ Better developer experience

### Phase 8 Complete

- ✅ Semantic pattern search with pgvector
- ✅ Natural language queries ("validate email")
- ✅ Pattern recommendations
- ✅ Cross-project pattern discovery
- ✅ 50%+ increase in pattern reuse

---

## Priority Assessment

### Must Have (Critical for Core Workflow)

- **None** - Phases 6-8 are all enhancements

### Should Have (High Value)

- **Phase 8**: Semantic search (AI-powered discovery)
- **Phase 7**: GraphQL API (better developer experience)

### Nice to Have (Internal/Marketing)

- **Phase 6**: Self-schema generation (dogfooding proof)

---

## Recommendation

**Start with Phase 8** (Pattern Library Complete):
- Highest user value (semantic search)
- Already 80% done
- Can complete in 2 weeks

**Then Phase 7** (Dual Interface):
- Good developer experience improvement
- Enables remote/programmatic access

**Finally Phase 6** (Self-Schema):
- Good for marketing/trust
- Internal consistency
- Can defer if time constrained

---

**Status**: Detailed plan complete, ready for implementation
**Timeline**: 6 weeks total (can prioritize based on value)
**Risk**: Low (all enhancements, core workflow already works)

---

*Build what users need most. Enhance what already works.* 🚀
