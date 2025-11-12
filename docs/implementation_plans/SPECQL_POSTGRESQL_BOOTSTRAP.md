# SpecQL PostgreSQL Bootstrap: Eating Our Own Dog Food

**Date**: 2025-11-12
**Status**: Implementation Plan
**Goal**: Migrate SpecQL's domain model to PostgreSQL using the 6-digit hex architecture we generate

---

## Executive Summary

### The Problem

SpecQL currently uses **multiple heterogeneous formats** for its domain model:

1. **Domain Registry**: `registry/domain_registry.yaml` (YAML)
2. **Pattern Library**: `database/pattern_library_schema.sql` (SQLite)
3. **Service Registry**: `registry/service_registry.yaml` (YAML)
4. **Type Registry**: Python code in `src/core/type_registry.py`

**Issues**:
- ❌ No single source of truth
- ❌ Manual synchronization required
- ❌ Can't query relationships between domains/patterns/types
- ❌ No ACID guarantees across registries
- ❌ We generate production PostgreSQL for users but don't use it ourselves
- ❌ Missing the power of our own 6-digit hierarchical architecture

### The Solution: "Eat Our Own Dog Food"

**Use SpecQL to generate SpecQL's own domain model in PostgreSQL**, respecting the same 6-digit architecture we produce for users.

```
registry/domain_registry.yaml  →  SpecQL Generator  →  PostgreSQL (6-digit architecture)
registry/service_registry.yaml →                    →
src/pattern_library/           →                    →
```

### Benefits

✅ **Single Source of Truth**: PostgreSQL becomes the canonical registry
✅ **ACID Transactions**: All registry operations are transactional
✅ **Powerful Queries**: SQL joins between domains, patterns, entities
✅ **6-Digit Architecture**: Hierarchical organization we generate for users
✅ **GraphQL API**: Auto-generated FraiseQL API for registry
✅ **Pattern Library Integration**: Patterns stored in same database
✅ **Dogfooding**: We use what we build (builds trust)
✅ **Performance**: Native indexes, constraints, triggers

---

## Current State Analysis

### 1. Domain Registry (YAML)

**File**: `registry/domain_registry.yaml`

**Structure**:
```yaml
version: 2.0.0
domains:
  '1':
    name: core
    description: Core infrastructure
    multi_tenant: false
    subdomains:
      '1':
        name: i18n
        description: Internationalization
        entities: {}
  '2':
    name: crm
    description: Customer relationship management
    multi_tenant: true
    subdomains:
      '3':
        name: customer
        entities:
          Contact:
            table_code: 01203581
            entity_code: CON
```

**Python Interface**: `src/generators/schema/naming_conventions.py` (DomainRegistry class)

### 2. Pattern Library (SQLite)

**File**: `src/pattern_library/schema.sql`

**Tables**:
- `patterns` - Universal patterns (Tier 1)
- `languages` - Target languages
- `pattern_implementations` - Language-specific code
- `domain_patterns` - Business logic patterns (Tier 2)
- `entity_templates` - Pre-built entity templates

**Issues**:
- SQLite (not PostgreSQL)
- Separate database (not integrated with SpecQL schemas)
- No connection to domain registry

### 3. Service Registry (YAML)

**File**: `registry/service_registry.yaml`

**Structure**:
```yaml
services:
  - name: user_management
    domain: crm
    database: crm
    schemas:
      - crm
    dependencies: []
```

### 4. Type Registry (Python)

**File**: `src/core/type_registry.py`

**Hardcoded Types**:
- Scalars: text, integer, boolean, timestamp, uuid, money
- Composites: address, contact_info, dimensions
- Rich types with validation

---

## Target State: PostgreSQL 6-Digit Architecture

### Hierarchy

```
0_schema/
├── 01_write_side/                         # Schema layer 01
│   └── 011_core/                          # Domain 1: core
│       ├── 0111_registry/                 # Subdomain 1: registry
│       │   ├── 01111_domain/              # Entity sequence 1: domain
│       │   │   ├── 011111_tb_domain.sql                  # Table
│       │   │   ├── 011112_fn_domain_pk.sql               # Trinity helpers
│       │   │   └── 011113_fn_domain_id.sql
│       │   ├── 01112_subdomain/           # Entity sequence 2: subdomain
│       │   │   ├── 011121_tb_subdomain.sql
│       │   │   └── 011122_fn_subdomain_pk.sql
│       │   ├── 01113_entity/              # Entity sequence 3: entity
│       │   │   ├── 011131_tb_entity.sql
│       │   │   └── 011132_fn_entity_pk.sql
│       │   ├── 01114_field/               # Entity sequence 4: field
│       │   │   └── 011141_tb_field.sql
│       │   └── 01115_type/                # Entity sequence 5: type
│       │       └── 011151_tb_type.sql
│       │
│       ├── 0112_pattern/                  # Subdomain 2: pattern
│       │   ├── 01121_domain_pattern/      # Domain patterns (business logic)
│       │   │   ├── 011211_tb_domain_pattern.sql
│       │   │   └── 011212_fn_domain_pattern_pk.sql
│       │   ├── 01122_entity_template/     # Entity templates
│       │   │   └── 011221_tb_entity_template.sql
│       │   └── 01123_pattern_instantiation/
│       │       └── 011231_tb_pattern_instantiation.sql
│       │
│       └── 0113_service/                  # Subdomain 3: service
│           └── 01131_service/
│               └── 011311_tb_service.sql
│
└── 02_query_side/                         # Schema layer 02
    └── 021_core/                          # Query side views
        └── 0211_registry/
            ├── 02111_domain/
            │   └── 021111_tv_domain.sql           # Table views for GraphQL
            ├── 02112_subdomain/
            │   └── 021121_tv_subdomain.sql
            └── 02113_entity/
                └── 021131_tv_entity.sql
```

### PostgreSQL Schemas

Instead of using `core` schema for everything, we use **proper PostgreSQL schemas**:

| PostgreSQL Schema | Purpose | Multi-Tenant |
|-------------------|---------|--------------|
| `specql_registry` | Domain/subdomain/entity registry | No |
| `specql_pattern` | Pattern library (domain patterns, templates) | No |
| `specql_service` | Service registry | No |
| `specql_type` | Type registry | No |
| `common` | Framework reference data | No |
| `app` | GraphQL types | No |

**Why separate schemas?**
- Clear separation of concerns
- Better security (grant per schema)
- Follows our own conventions (multi-tenant vs shared)
- Easier to backup/restore specific parts

---

## Implementation Phases

### Phase 1: Registry Schema (Week 1)

**Goal**: Define SpecQL YAML entities for domain registry

#### Tasks

**1.1 Create Entity YAMLs**

Create `entities/specql_registry/` directory with:

**`domain.yaml`**:
```yaml
entity: domain
schema: specql_registry
description: Top-level business domains (crm, catalog, projects)

organization:
  table_code: "011111"
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

  description:
    type: text
    nullable: true

  multi_tenant:
    type: boolean
    nullable: false
    default: false
    description: "Whether this domain requires tenant_id"

  aliases:
    type: list(text)
    nullable: true
    description: "Alternative names (e.g., 'management' for 'crm')"

indexes:
  - fields: [domain_number]
    unique: true
  - fields: [domain_name]
    unique: true

fraiseql:
  enabled: true
  queries:
    find_one: true
    find_one_by_identifier: true
    find_many: true

actions:
  - name: register_domain
    steps:
      - validate: domain_number ~ '^[1-9]$'
      - validate: NOT EXISTS (SELECT 1 FROM specql_registry.tb_domain WHERE domain_number = :domain_number)
      - insert: domain (domain_number, domain_name, description, multi_tenant)
    returns: domain
```

**`subdomain.yaml`**:
```yaml
entity: subdomain
schema: specql_registry
description: Domain subdivisions (crm.customer, catalog.manufacturer)

organization:
  table_code: "011121"

fields:
  subdomain_number:
    type: text
    nullable: false
    description: "Single digit subdomain number (1-9)"

  subdomain_name:
    type: text
    nullable: false

  description:
    type: text
    nullable: true

  next_entity_sequence:
    type: integer
    nullable: false
    default: 1
    description: "Next available entity sequence number"

foreign_keys:
  fk_domain:
    references: specql_registry.tb_domain
    on: pk_domain
    nullable: false

unique_constraints:
  - fields: [fk_domain, subdomain_number]
  - fields: [fk_domain, subdomain_name]

indexes:
  - fields: [fk_domain, subdomain_number]
    unique: true
```

**`entity_registration.yaml`**:
```yaml
entity: entity_registration
schema: specql_registry
description: Entity registrations with 6-digit codes

organization:
  table_code: "011131"

fields:
  entity_name:
    type: text
    nullable: false
    description: "Entity name (Contact, Manufacturer)"

  table_code:
    type: text
    nullable: false
    unique: true
    description: "6-digit hierarchical code (012035)"

  entity_code:
    type: text
    nullable: true
    description: "3-letter mnemonic (CON, MNF)"

  entity_sequence:
    type: integer
    nullable: false
    description: "Entity sequence within subdomain"

  assigned_at:
    type: timestamp
    nullable: false
    default: now()

foreign_keys:
  fk_subdomain:
    references: specql_registry.tb_subdomain
    on: pk_subdomain
    nullable: false

unique_constraints:
  - fields: [fk_subdomain, entity_sequence]
  - fields: [table_code]

indexes:
  - fields: [table_code]
    unique: true
  - fields: [fk_subdomain, entity_sequence]
```

**1.2 Generate PostgreSQL Schema**

```bash
specql generate entities/specql_registry/domain.yaml \
  --hierarchical \
  --output-dir=db/schema/

specql generate entities/specql_registry/subdomain.yaml \
  --hierarchical \
  --output-dir=db/schema/

specql generate entities/specql_registry/entity_registration.yaml \
  --hierarchical \
  --output-dir=db/schema/
```

**Output**: Generates PostgreSQL DDL in 6-digit hierarchy

**1.3 Migration Script**

Create `scripts/migrate_registry_to_postgres.py`:

```python
#!/usr/bin/env python3
"""
Migrate domain_registry.yaml to PostgreSQL
"""
import yaml
import psycopg
from datetime import datetime

def migrate_registry():
    # Load YAML
    with open('registry/domain_registry.yaml') as f:
        registry = yaml.safe_load(f)

    # Connect to PostgreSQL
    with psycopg.connect(os.getenv('DATABASE_URL')) as conn:
        with conn.cursor() as cur:
            # Migrate domains
            for domain_num, domain_data in registry['domains'].items():
                cur.execute("""
                    INSERT INTO specql_registry.tb_domain
                    (domain_number, domain_name, description, multi_tenant, aliases)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (domain_number) DO UPDATE SET
                        domain_name = EXCLUDED.domain_name,
                        description = EXCLUDED.description,
                        multi_tenant = EXCLUDED.multi_tenant,
                        aliases = EXCLUDED.aliases
                """, (
                    domain_num,
                    domain_data['name'],
                    domain_data.get('description'),
                    domain_data.get('multi_tenant', False),
                    domain_data.get('aliases')
                ))

                # Get domain PK
                cur.execute(
                    "SELECT pk_domain FROM specql_registry.tb_domain WHERE domain_number = %s",
                    (domain_num,)
                )
                domain_pk = cur.fetchone()[0]

                # Migrate subdomains
                for subdomain_num, subdomain_data in domain_data['subdomains'].items():
                    cur.execute("""
                        INSERT INTO specql_registry.tb_subdomain
                        (fk_domain, subdomain_number, subdomain_name, description, next_entity_sequence)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (fk_domain, subdomain_number) DO UPDATE SET
                            subdomain_name = EXCLUDED.subdomain_name,
                            description = EXCLUDED.description,
                            next_entity_sequence = EXCLUDED.next_entity_sequence
                    """, (
                        domain_pk,
                        subdomain_num,
                        subdomain_data['name'],
                        subdomain_data.get('description'),
                        subdomain_data.get('next_entity_sequence', 1)
                    ))

                    # Get subdomain PK
                    cur.execute(
                        "SELECT pk_subdomain FROM specql_registry.tb_subdomain WHERE fk_domain = %s AND subdomain_number = %s",
                        (domain_pk, subdomain_num)
                    )
                    subdomain_pk = cur.fetchone()[0]

                    # Migrate entities
                    for entity_name, entity_data in subdomain_data.get('entities', {}).items():
                        cur.execute("""
                            INSERT INTO specql_registry.tb_entity_registration
                            (fk_subdomain, entity_name, table_code, entity_code, entity_sequence, assigned_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (table_code) DO UPDATE SET
                                entity_name = EXCLUDED.entity_name,
                                entity_code = EXCLUDED.entity_code
                        """, (
                            subdomain_pk,
                            entity_name,
                            entity_data['table_code'],
                            entity_data.get('entity_code'),
                            entity_data.get('entity_sequence', 1),
                            entity_data.get('assigned_at', datetime.now())
                        ))

            conn.commit()
            print("✅ Migration complete")

if __name__ == '__main__':
    migrate_registry()
```

**1.4 Python API Migration**

Update `src/generators/schema/naming_conventions.py`:

```python
class DomainRegistry:
    """
    PostgreSQL-backed domain registry

    Replaces YAML file with live PostgreSQL queries
    """

    def __init__(self, db_url: str):
        self.db_url = db_url

    def get_domain(self, name_or_alias: str) -> DomainInfo | None:
        """Get domain by name or alias - from PostgreSQL"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        domain_number,
                        domain_name,
                        description,
                        multi_tenant,
                        aliases
                    FROM specql_registry.tb_domain
                    WHERE domain_name = %s
                       OR %s = ANY(aliases)
                """, (name_or_alias, name_or_alias))

                row = cur.fetchone()
                if not row:
                    return None

                return DomainInfo(
                    domain_number=row[0],
                    domain_name=row[1],
                    description=row[2],
                    multi_tenant=row[3],
                    aliases=row[4] or []
                )

    def allocate_entity_code(self, domain: str, subdomain: str, entity_name: str) -> str:
        """Allocate next 6-digit code - transactional"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Get subdomain
                cur.execute("""
                    SELECT s.pk_subdomain, s.next_entity_sequence, d.domain_number, s.subdomain_number
                    FROM specql_registry.tb_subdomain s
                    JOIN specql_registry.tb_domain d ON d.pk_domain = s.fk_domain
                    WHERE d.domain_name = %s AND s.subdomain_name = %s
                    FOR UPDATE  -- Lock row for atomic increment
                """, (domain, subdomain))

                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Subdomain {domain}.{subdomain} not found")

                subdomain_pk, next_seq, domain_num, subdomain_num = row

                # Generate 6-digit code
                table_code = f"{domain_num}{subdomain_num}{next_seq:02d}"

                # Register entity
                cur.execute("""
                    INSERT INTO specql_registry.tb_entity_registration
                    (fk_subdomain, entity_name, table_code, entity_sequence, assigned_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING table_code
                """, (subdomain_pk, entity_name, table_code, next_seq))

                allocated_code = cur.fetchone()[0]

                # Increment sequence
                cur.execute("""
                    UPDATE specql_registry.tb_subdomain
                    SET next_entity_sequence = next_entity_sequence + 1
                    WHERE pk_subdomain = %s
                """, (subdomain_pk,))

                conn.commit()
                return allocated_code
```

**Deliverables**:
- [ ] `entities/specql_registry/domain.yaml`
- [ ] `entities/specql_registry/subdomain.yaml`
- [ ] `entities/specql_registry/entity_registration.yaml`
- [ ] Generated PostgreSQL DDL in `db/schema/0_schema/01_write_side/011_core/0111_registry/`
- [ ] Migration script `scripts/migrate_registry_to_postgres.py`
- [ ] Updated `DomainRegistry` class with PostgreSQL backend
- [ ] All tests passing with PostgreSQL registry

---

### Phase 2: Pattern Library Schema (Week 2)

**Goal**: Migrate pattern library from SQLite to PostgreSQL with 6-digit architecture

#### Tasks

**2.1 Create Pattern Entity YAMLs**

**`entities/specql_pattern/domain_pattern.yaml`**:
```yaml
entity: domain_pattern
schema: specql_pattern
description: Reusable business logic patterns (state_machine, audit_trail)

organization:
  table_code: "011211"
  domain: core
  subdomain: pattern
  entity_sequence: 1

fields:
  pattern_name:
    type: text
    nullable: false
    unique: true

  pattern_category:
    type: enum(state_machine, workflow, hierarchy, audit, validation)
    nullable: false

  description:
    type: text
    nullable: true

  parameters:
    type: jsonb
    nullable: false
    description: "JSON schema for pattern parameters"

  implementation:
    type: jsonb
    nullable: false
    description: "Pattern logic in Tier 1 primitives"

  embedding:
    type: vector(384)
    nullable: true
    description: "Semantic embedding for similarity search"

  usage_count:
    type: integer
    nullable: false
    default: 0

  popularity_score:
    type: real
    nullable: false
    default: 0.0

  tags:
    type: list(text)
    nullable: true

indexes:
  - fields: [pattern_category]
  - fields: [pattern_name]
    unique: true
  - fields: [embedding]
    type: hnsw
    ops: vector_cosine_ops
    description: "HNSW index for fast vector similarity"

fraiseql:
  enabled: true
  queries:
    find_one: true
    find_one_by_identifier: true
    find_many: true

actions:
  - name: register_pattern
    steps:
      - validate: NOT EXISTS (SELECT 1 FROM specql_pattern.tb_domain_pattern WHERE pattern_name = :pattern_name)
      - insert: domain_pattern (pattern_name, pattern_category, description, parameters, implementation)
    returns: domain_pattern

  - name: search_patterns_by_embedding
    parameters:
      - name: query_embedding
        type: vector(384)
      - name: limit
        type: integer
        default: 10
    steps:
      - query: |
          SELECT
            pk_domain_pattern,
            pattern_name,
            pattern_category,
            description,
            embedding <=> :query_embedding AS distance
          FROM specql_pattern.tb_domain_pattern
          WHERE embedding IS NOT NULL
          ORDER BY embedding <=> :query_embedding
          LIMIT :limit
    returns: list(domain_pattern)
```

**2.2 PostgreSQL Extensions**

Add to `db/schema/00_foundation/000_app_foundation.sql`:

```sql
-- pgvector for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Comment
COMMENT ON EXTENSION vector IS 'Vector similarity search for pattern embeddings';
```

**2.3 Migrate Pattern Data**

Create `scripts/migrate_patterns_to_postgres.py`:

```python
#!/usr/bin/env python3
"""
Migrate pattern library from SQLite to PostgreSQL
"""
import sqlite3
import psycopg

def migrate_patterns():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('src/pattern_library/pattern_library.db')
    sqlite_cur = sqlite_conn.cursor()

    # Connect to PostgreSQL
    with psycopg.connect(os.getenv('DATABASE_URL')) as pg_conn:
        with pg_conn.cursor() as pg_cur:
            # Migrate domain patterns
            sqlite_cur.execute("SELECT * FROM domain_patterns")
            for row in sqlite_cur.fetchall():
                pg_cur.execute("""
                    INSERT INTO specql_pattern.tb_domain_pattern
                    (pattern_name, pattern_category, description, parameters, implementation, usage_count, popularity_score, tags)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                    ON CONFLICT (pattern_name) DO UPDATE SET
                        pattern_category = EXCLUDED.pattern_category,
                        description = EXCLUDED.description,
                        parameters = EXCLUDED.parameters,
                        implementation = EXCLUDED.implementation
                """, (
                    row[1],  # pattern_name
                    row[2],  # pattern_category
                    row[3],  # description
                    row[4],  # parameters (JSON)
                    row[5],  # implementation (JSON)
                    row[6],  # usage_count
                    row[7],  # popularity_score
                    row[8].split(',') if row[8] else None  # tags
                ))

            pg_conn.commit()
            print("✅ Pattern migration complete")

    sqlite_conn.close()

if __name__ == '__main__':
    migrate_patterns()
```

**Deliverables**:
- [ ] `entities/specql_pattern/domain_pattern.yaml`
- [ ] `entities/specql_pattern/entity_template.yaml`
- [ ] `entities/specql_pattern/pattern_instantiation.yaml`
- [ ] Generated PostgreSQL DDL with pgvector support
- [ ] Migration script from SQLite
- [ ] HNSW index on embedding column
- [ ] Updated pattern library API to use PostgreSQL

---

### Phase 3: Type Registry Schema (Week 3)

**Goal**: Move type registry from Python code to PostgreSQL

#### Tasks

**3.1 Create Type Entity YAMLs**

**`entities/specql_type/universal_type.yaml`**:
```yaml
entity: universal_type
schema: specql_type
description: SpecQL type system (text, integer, money, address)

organization:
  table_code: "011511"

fields:
  type_name:
    type: text
    nullable: false
    unique: true
    description: "Type name (text, integer, money, address)"

  type_category:
    type: enum(scalar, composite, collection)
    nullable: false

  json_schema:
    type: jsonb
    nullable: true
    description: "JSON Schema definition for validation"

  default_postgres_type:
    type: text
    nullable: true
    description: "Default PostgreSQL type mapping"

  is_rich_type:
    type: boolean
    nullable: false
    default: false
    description: "Whether this is a rich/composite type"

indexes:
  - fields: [type_name]
    unique: true
  - fields: [type_category]
```

**3.2 Seed Types**

Create `db/seed_data/universal_types.sql`:

```sql
-- Scalar types
INSERT INTO specql_type.tb_universal_type (type_name, type_category, default_postgres_type, is_rich_type)
VALUES
  ('text', 'scalar', 'TEXT', false),
  ('integer', 'scalar', 'INTEGER', false),
  ('boolean', 'scalar', 'BOOLEAN', false),
  ('timestamp', 'scalar', 'TIMESTAMPTZ', false),
  ('uuid', 'scalar', 'UUID', false),
  ('money', 'scalar', 'NUMERIC(15,2)', false),
  ('date', 'scalar', 'DATE', false),
  ('time', 'scalar', 'TIME', false),
  ('jsonb', 'scalar', 'JSONB', false);

-- Composite types
INSERT INTO specql_type.tb_universal_type (type_name, type_category, json_schema, is_rich_type)
VALUES
  ('address', 'composite', '{
    "type": "object",
    "properties": {
      "street": {"type": "string"},
      "city": {"type": "string"},
      "postal_code": {"type": "string"},
      "country": {"type": "string"}
    }
  }'::jsonb, true),

  ('contact_info', 'composite', '{
    "type": "object",
    "properties": {
      "email": {"type": "string", "format": "email"},
      "phone": {"type": "string"},
      "mobile": {"type": "string"}
    }
  }'::jsonb, true),

  ('dimensions', 'composite', '{
    "type": "object",
    "properties": {
      "length": {"type": "number"},
      "width": {"type": "number"},
      "height": {"type": "number"},
      "unit": {"type": "string", "enum": ["mm", "cm", "m", "in", "ft"]}
    }
  }'::jsonb, true);

-- Collection types
INSERT INTO specql_type.tb_universal_type (type_name, type_category, default_postgres_type, is_rich_type)
VALUES
  ('list', 'collection', 'ARRAY', false);
```

**Deliverables**:
- [ ] `entities/specql_type/universal_type.yaml`
- [ ] Seed data for common types
- [ ] Updated type registry to read from PostgreSQL
- [ ] Type validation using JSON Schema

---

### Phase 4: Service Registry Schema (Week 4)

**Goal**: Migrate service registry to PostgreSQL

**`entities/specql_service/service.yaml`**:
```yaml
entity: service
schema: specql_service
description: Microservice registry

organization:
  table_code: "011311"

fields:
  service_name:
    type: text
    nullable: false
    unique: true

  database_name:
    type: text
    nullable: false

  schemas:
    type: list(text)
    nullable: false
    description: "PostgreSQL schemas used by this service"

  dependencies:
    type: list(text)
    nullable: true
    description: "Other services this depends on"

foreign_keys:
  fk_domain:
    references: specql_registry.tb_domain
    on: pk_domain
    nullable: true
```

---

### Phase 5: Unified CLI & API (Week 5)

**Goal**: Single CLI to interact with PostgreSQL registry

#### Tasks

**5.1 Create Registry CLI**

```bash
# Query registry
specql registry domains list
specql registry domains show crm
specql registry subdomains list --domain=crm
specql registry entities list --domain=crm --subdomain=customer

# Allocate codes
specql registry allocate-code \
  --domain=crm \
  --subdomain=customer \
  --entity=Contact

# Pattern library
specql patterns list --category=workflow
specql patterns search "approval workflow"
specql patterns register --file=patterns/approval.yaml

# Types
specql types list
specql types show money
specql types register --file=types/custom_type.yaml
```

**5.2 GraphQL API**

Auto-generated from FraiseQL annotations:

```graphql
query {
  domains {
    domainName
    multiTenant
    subdomains {
      subdomainName
      entities {
        entityName
        tableCode
      }
    }
  }
}

query {
  searchPatterns(queryEmbedding: $embedding, limit: 10) {
    patternName
    patternCategory
    description
    distance
  }
}

mutation {
  registerDomain(input: {
    domainNumber: "7"
    domainName: "inventory"
    description: "Inventory management"
    multiTenant: true
  }) {
    ... on Domain {
      id
      domainName
    }
  }
}
```

**Deliverables**:
- [ ] Unified CLI for registry operations
- [ ] GraphQL API for registry (auto-generated)
- [ ] Python SDK for programmatic access
- [ ] REST API wrapper (optional)

---

### Phase 6: Migration & Testing (Week 6)

**Goal**: Complete migration from YAML/SQLite to PostgreSQL

#### Tasks

**6.1 Dual-Write Period**

Maintain both YAML and PostgreSQL during transition:

```python
class DomainRegistry:
    def register_entity(self, domain, subdomain, entity):
        # Write to PostgreSQL (primary)
        code = self._register_in_postgres(domain, subdomain, entity)

        # Write to YAML (backup)
        self._register_in_yaml(domain, subdomain, entity, code)

        return code
```

**6.2 Validation**

```bash
# Compare YAML vs PostgreSQL
specql registry validate --compare-yaml

# Output:
# ✅ Domain 'crm' matches
# ✅ Subdomain 'crm.customer' matches
# ❌ Entity 'Contact' code mismatch: YAML=01203581, PG=012035
```

**6.3 Cut-Over**

1. **Freeze YAML writes** - Make YAML read-only
2. **Verify PostgreSQL complete** - All data migrated
3. **Switch Python API** - Point to PostgreSQL
4. **Archive YAML** - Move to `registry/archive/`
5. **Delete SQLite** - Remove `src/pattern_library/pattern_library.db`

**Deliverables**:
- [ ] Dual-write implementation
- [ ] Validation scripts
- [ ] Cut-over runbook
- [ ] Rollback plan
- [ ] All tests passing with PostgreSQL backend

---

## Benefits Summary

### Before (Current State)

```
Domain Registry:  registry/domain_registry.yaml (2,000 lines)
Pattern Library:  src/pattern_library/schema.sql (SQLite, 183 lines)
Service Registry: registry/service_registry.yaml (50 lines)
Type Registry:    src/core/type_registry.py (Python code)
```

**Issues**:
- 4 different formats
- Manual synchronization
- No relationships
- Can't query across registries
- No ACID guarantees

### After (Target State)

```
PostgreSQL Database:
├── specql_registry schema (domains, subdomains, entities)
├── specql_pattern schema (patterns, templates, instantiations)
├── specql_service schema (services, dependencies)
└── specql_type schema (types, mappings)

All accessible via:
- SQL queries
- GraphQL API (auto-generated)
- Python SDK
- CLI commands
```

**Benefits**:
- ✅ Single source of truth (PostgreSQL)
- ✅ ACID transactions
- ✅ SQL joins across registries
- ✅ 6-digit hierarchical architecture
- ✅ Auto-generated GraphQL API
- ✅ pgvector for pattern search
- ✅ Dogfooding our own framework
- ✅ Production-ready from day 1

---

## File Structure After Migration

```
registry/
├── archive/                           # Legacy files (read-only)
│   ├── domain_registry.yaml.backup
│   └── service_registry.yaml.backup
└── README.md                          # Points to PostgreSQL

src/
├── registry/
│   ├── __init__.py
│   ├── domain_registry.py            # PostgreSQL-backed
│   ├── pattern_library.py            # PostgreSQL-backed
│   ├── service_registry.py           # PostgreSQL-backed
│   └── type_registry.py              # PostgreSQL-backed
└── cli/
    └── registry.py                    # CLI commands

db/
└── schema/
    ├── 0_schema/
    │   ├── 01_write_side/
    │   │   └── 011_core/
    │   │       ├── 0111_registry/    # Domain, subdomain, entity tables
    │   │       ├── 0112_pattern/     # Pattern library tables
    │   │       ├── 0113_service/     # Service registry tables
    │   │       └── 0115_type/        # Type registry tables
    │   └── 02_query_side/
    │       └── 021_core/
    │           └── 0211_registry/    # GraphQL views
    └── seed_data/
        ├── 01_domains.sql
        ├── 02_subdomains.sql
        ├── 03_patterns.sql
        └── 04_types.sql
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Migration Completeness** | 100% data migrated | Compare YAML vs PG |
| **Query Performance** | <10ms for registry lookups | PostgreSQL EXPLAIN |
| **Pattern Search** | <50ms for 1000 patterns | HNSW index benchmark |
| **API Coverage** | 100% YAML operations | Feature parity check |
| **Test Coverage** | >90% | pytest --cov |
| **Zero Downtime** | No service interruption | Dual-write period |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data loss during migration** | High | Dual-write period, validation scripts, backups |
| **Performance regression** | Medium | Benchmarks, indexes, query optimization |
| **Breaking API changes** | Medium | Backward compatibility layer, versioning |
| **PostgreSQL dependency** | Low | Acceptable - production databases use PostgreSQL |

---

## Next Steps

1. **Review this plan** - Get stakeholder approval
2. **Create entity YAMLs** - Start with `domain.yaml`
3. **Generate PostgreSQL DDL** - Use SpecQL generator
4. **Implement migration scripts** - YAML → PostgreSQL
5. **Update Python APIs** - Point to PostgreSQL
6. **Dual-write testing** - Ensure data consistency
7. **Cut-over** - Switch to PostgreSQL as primary
8. **Archive YAML** - Keep for historical reference

---

**Status**: Ready to implement
**Estimated Timeline**: 6 weeks
**Complexity**: Medium (we're using our own framework)
**Risk**: Low (well-understood domain, incremental migration)

Let's eat our own dog food! 🐕
