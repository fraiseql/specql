# Claude Code Instructions - SpecQL → PostgreSQL → GraphQL Generator

**Project**: Lightweight Business DSL → Production Database + Auto-GraphQL API
**Status**: 🚧 Active Development - Parallel Team Execution
**Context Window Optimization**: This file provides instant project context for AI assistants

---

## 🎯 Project Vision

**Transform 20 lines of business-focused YAML into production-ready PostgreSQL + GraphQL API.**

### Core Principle: **Business Domain ONLY in YAML**

Users write **ONLY** business logic. Framework handles ALL technical details automatically.

**Example Input** (20 lines):
```yaml
entity: Contact
schema: crm

fields:
  email: text
  company: ref(Company)          # Framework auto-creates FK
  status: enum(lead, qualified)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

**Auto-Generated Output** (2000+ lines):
- ✅ PostgreSQL table with Trinity pattern (pk_*, id, identifier)
- ✅ Auto-generated foreign keys and indexes
- ✅ PL/pgSQL function for `qualify_lead` action
- ✅ FraiseQL metadata comments for GraphQL
- ✅ Complete GraphQL API (queries, mutations, types)

**Result**: **100x code leverage** - Business logic in YAML, framework handles implementation.

---

## 🏗️ Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  LIGHTWEIGHT SpecQL (Business Only - 20 lines)              │
│  - Entities & relationships                                  │
│  - Business actions & validations                            │
│  - NO infrastructure details                                 │
└──────────────────┬───────────────────────────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    │  TEAM A: SpecQL Parser      │
    │  Parse DSL → Business AST   │
    └──────────────┬──────────────┘
                   │
                   ▼
    ┌────────────────────────────────────┐
    │   Business Entity AST               │
    │   (No infrastructure details)       │
    └──────────────┬─────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌──────────────┐
│ TEAM B  │  │ TEAM C  │  │  TEAM D      │
│ Schema  │  │ Action  │  │  FraiseQL    │
│ Gen     │  │ Compiler│  │  Metadata    │
└────┬────┘  └────┬────┘  └──────┬───────┘
     │            │               │
     └────────────┼───────────────┘
                  │
                  ▼
    ┌──────────────────────────┐
    │  TEAM E: Orchestrator    │
    │  Combine → Migration SQL │
    └──────────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  PostgreSQL Database             │
    │  - Tables (Trinity pattern)      │
    │  - Functions (business actions)  │
    │  - FraiseQL metadata comments    │
    └──────────────┬───────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  FraiseQL Auto-Discovery         │
    │  (External tool - introspects)   │
    └──────────────┬───────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  GraphQL API (Auto-Generated)    │
    │  - Types, Queries, Mutations     │
    └──────────────────────────────────┘
```

---

## 👥 TEAM STRUCTURE (5 Teams, Clear Separation of Concerns)

### 🔵 Team A: SpecQL Parser (Business DSL)
**Mission**: Parse lightweight business YAML → Business AST (NO infrastructure details)

**Parses**:
- ✅ Entity name, schema, description
- ✅ Fields: name, type (text, integer, ref, enum, list)
- ✅ Actions: name, steps (validate, if/then, insert, update, call, notify)
- ✅ Business validation rules
- ✅ AI agent definitions

**Does NOT Parse** (Framework handles):
- ❌ Trinity pattern syntax (pk_*, id, identifier) - Auto-generated by Team B
- ❌ Foreign key syntax (fk_*, REFERENCES) - Inferred from ref(Entity)
- ❌ Index definitions - Auto-generated by Team B
- ❌ Constraint details - Inferred from types
- ❌ GraphQL metadata - Generated by Team D

**Status**: ✅ **90% Complete** (Current implementation is correct!)
**Location**: `src/core/`
**Test Command**: `make teamA-test`

---

### 🟢 Team B: Schema Generator (Convention-Based DDL)
**Mission**: Business AST → PostgreSQL DDL with **automatic framework conventions**

**Input**: Business Entity AST (from Team A)

**Applies Conventions** (Automatically):
1. **Trinity Pattern**: Every table gets `pk_*`, `id`, `identifier`
2. **Naming**: `tb_{entity}` tables, `fk_{entity}` foreign keys
3. **Audit Fields**: `created_at`, `created_by`, `updated_at`, `updated_by`, `deleted_at`
4. **Auto-Indexes**: FK columns, enum fields, common query patterns
5. **Constraints**: NOT NULL inference, CHECK for enums, UNIQUE where appropriate

**Example Transformation**:
```yaml
# Input (SpecQL)
fields:
  company: ref(Company)
  status: enum(lead, qualified)
```

```sql
-- Output (Auto-generated DDL)
CREATE TABLE crm.tb_contact (
    -- Trinity Pattern (AUTO)
    pk_contact INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    identifier TEXT UNIQUE,

    -- Business fields + AUTO conventions
    fk_company INTEGER REFERENCES management.tb_company(pk_company),  -- AUTO FK
    status TEXT CHECK (status IN ('lead', 'qualified')),              -- AUTO CHECK

    -- Audit fields (AUTO)
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-generated indexes
CREATE INDEX idx_contact_company ON crm.tb_contact(fk_company);
CREATE INDEX idx_contact_status ON crm.tb_contact(status);
```

**NEW RESPONSIBILITY (Post FraiseQL Response)**: Also generate `mutation_metadata` schema

**One-Time Generation** (`migrations/000_mutation_metadata.sql`):
```sql
-- Metadata types for mutation impacts (FraiseQL composite type pattern)
CREATE SCHEMA mutation_metadata;

CREATE TYPE mutation_metadata.entity_impact AS (
    entity_type TEXT,
    operation TEXT,
    modified_fields TEXT[]
);

CREATE TYPE mutation_metadata.cache_invalidation AS (
    query_name TEXT,
    filter_json JSONB,
    strategy TEXT,
    reason TEXT
);

CREATE TYPE mutation_metadata.mutation_impact_metadata AS (
    primary_entity mutation_metadata.entity_impact,
    actual_side_effects mutation_metadata.entity_impact[],
    cache_invalidations mutation_metadata.cache_invalidation[]
);

-- FraiseQL annotations for auto-discovery
COMMENT ON TYPE mutation_metadata.mutation_impact_metadata IS
  '@fraiseql:type name=MutationImpactMetadata';
COMMENT ON TYPE mutation_metadata.entity_impact IS
  '@fraiseql:type name=EntityImpact';
COMMENT ON TYPE mutation_metadata.cache_invalidation IS
  '@fraiseql:type name=CacheInvalidation';
```

**Why**: FraiseQL team confirmed composite types are the best pattern for type-safe metadata

**Status**: 🔴 Not Started (Week 2 focus)
**Location**: `src/generators/schema/`
**Test Command**: `make teamB-test`
**Critical Test**: Week 2 Day 1-2 - Verify composite types work with FraiseQL (see `/docs/architecture/UPDATED_TEAM_PLANS_POST_FRAISEQL_RESPONSE.md`)

---

### 🟠 Team C: Action Compiler (Business Logic → PL/pgSQL with FraiseQL Integration)
**Mission**: SpecQL action steps → PostgreSQL functions returning FraiseQL-compatible `mutation_result`

**CRITICAL UPDATE (Post FraiseQL Response)**: Use PostgreSQL composite types for type-safe metadata!

**Input**: Action definitions from AST (including impact declarations)

**Generates**: PL/pgSQL functions with:
1. **FraiseQL Standard Return**: `mutation_result` type (not plain jsonb)
2. **Trinity Resolution**: Auto-convert UUID → INTEGER for queries
3. **Audit Updates**: Auto-update `updated_at`, `updated_by`
4. **Event Emission**: Auto-emit events on state changes
5. **Error Handling**: Standard exception patterns with typed errors
6. **Full Object Returns**: Complete entities in `object_data` (not deltas)
7. **Impact Metadata**: Runtime `_meta` field with actual side effects
8. **Side Effect Tracking**: Secondary entities in `extra_metadata`

**Example Transformation**:
```yaml
# Input (SpecQL)
actions:
  - name: qualify_lead

    # Impact declaration (NEW)
    impact:
      primary:
        entity: Contact
        operation: update
        fields: [status, updatedAt]
        include_relations: [company]
      side_effects:
        - entity: Notification
          operation: create
          collection: createdNotifications
      cache_invalidations:
        - query: contacts
          filter: { status: "lead" }
          strategy: refetch
      optimistic_safe: true

    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

```sql
-- Output (Auto-generated FraiseQL-compatible Function)
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID DEFAULT NULL
)
RETURNS mutation_result AS $$  -- FraiseQL standard type
DECLARE
    v_pk INTEGER;
    v_status TEXT;
    v_result mutation_result;
BEGIN
    -- Trinity resolution (AUTO)
    v_pk := crm.contact_pk(p_contact_id);

    -- Validation (from SpecQL)
    SELECT status INTO v_status FROM crm.tb_contact WHERE pk_contact = v_pk;
    IF v_status != 'lead' THEN
        -- Error response
        v_result.status := 'error';
        v_result.message := 'Contact is not a lead';
        v_result.object_data := (
            -- Full Contact object for error case
            SELECT jsonb_build_object(
                '__typename', 'Contact',
                'id', c.id,
                'status', c.status
            )
            FROM crm.tb_contact c WHERE c.pk_contact = v_pk
        );
        RETURN v_result;
    END IF;

    -- Update (from SpecQL + AUTO audit)
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_contact = v_pk;

    -- Success response
    v_result.id := gen_random_uuid();
    v_result.status := 'success';
    v_result.message := 'Contact qualified successfully';
    v_result.updated_fields := ARRAY['status', 'updated_at'];

    -- Primary entity with relationships (FULL object, not delta)
    v_result.object_data := (
        SELECT jsonb_build_object(
            '__typename', 'Contact',
            'id', c.id,
            'email', c.email,
            'status', c.status,
            'updatedAt', c.updated_at,
            'company', jsonb_build_object(
                '__typename', 'Company',
                'id', co.id,
                'name', co.name
            )
        )
        FROM crm.tb_contact c
        LEFT JOIN management.tb_company co ON co.pk_company = c.fk_company
        WHERE c.pk_contact = v_pk
    );

    -- Build impact metadata using composite types (TYPE-SAFE!)
    DECLARE
        v_meta mutation_metadata.mutation_impact_metadata;
    BEGIN
        -- Type-safe construction (PostgreSQL validates at compile time!)
        v_meta.primary_entity := ROW(
            'Contact',                          -- entity_type
            'UPDATE',                           -- operation
            ARRAY['status', 'updated_at']       -- modified_fields
        )::mutation_metadata.entity_impact;

        v_meta.actual_side_effects := ARRAY[
            ROW(
                'Notification',
                'CREATE',
                ARRAY['id', 'message', 'created_at']::TEXT[]
            )::mutation_metadata.entity_impact
        ];

        v_meta.cache_invalidations := ARRAY[
            ROW(
                'contacts',                      -- query_name
                '{"status": "lead"}'::jsonb,     -- filter_json
                'REFETCH',                       -- strategy
                'Contact removed from lead list' -- reason
            )::mutation_metadata.cache_invalidation
        ];

        -- Side effects + impact metadata
        v_result.extra_metadata := jsonb_build_object(
            'createdNotifications', (
                SELECT COALESCE(jsonb_agg(
                    jsonb_build_object(
                        '__typename', 'Notification',
                        'id', n.id,
                        'message', n.message,
                        'createdAt', n.created_at
                    )
                ), '[]'::jsonb)
                FROM core.tb_notification n
                WHERE n.fk_contact = v_pk
                  AND n.created_at > (now() - interval '1 second')
            ),
            '_meta', to_jsonb(v_meta)  -- Convert composite type to JSONB
        );
    END;

    -- Event emission (AUTO)
    PERFORM core.emit_event('contact.qualified', jsonb_build_object('id', p_contact_id));

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

**Key Differences from Original Design:**
- ✅ Returns `mutation_result` (FraiseQL standard) instead of plain `jsonb`
- ✅ Includes FULL objects in `object_data` (not just modified fields)
- ✅ Includes relationships (company) as specified in `impact.include_relations`
- ✅ Tracks side effects in `extra_metadata.createdNotifications`
- ✅ **Uses composite types for `_meta` (TYPE-SAFE!)** - FraiseQL recommended pattern
- ✅ Tracks which fields changed in `updated_fields` array
- ✅ Proper `__typename` for Apollo/Relay cache normalization

**IMPORTANT**: Composite types provide compile-time validation - PostgreSQL will error if you use wrong types!

**Status**: 🔴 Not Started (Week 3-4 focus - extra time for composite type integration)
**Location**: `src/generators/actions/`
**Test Command**: `make teamC-test`

---

### 🟣 Team D: FraiseQL Metadata Generator + Impact Documentation
**Mission**: Generate `@fraiseql:*` COMMENT annotations for GraphQL auto-discovery + mutation impact metadata

**Input**: Entity AST + Generated SQL (from Teams B & C) + Impact declarations

**Generates Three Outputs**:

#### 1. SQL COMMENT Annotations (FraiseQL Discovery)
```sql
-- Table metadata
COMMENT ON TABLE crm.tb_contact IS
  '@fraiseql:type name=Contact,schema=crm';

-- Field metadata
COMMENT ON COLUMN crm.tb_contact.email IS
  '@fraiseql:field name=email,type=String!';
COMMENT ON COLUMN crm.tb_contact.fk_company IS
  '@fraiseql:field name=company,type=Company,relation=many-to-one';
COMMENT ON COLUMN crm.tb_contact.status IS
  '@fraiseql:field name=status,type=ContactStatus,enum=true';

-- Mutation metadata with impact hints
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead
   input=QualifyLeadInput
   success_type=QualifyLeadSuccess
   error_type=QualifyLeadError
   primary_entity=Contact
   metadata_mapping={
     "createdNotifications": "Notification[]",
     "_meta": "MutationImpactMetadata"
   }
   impact={
     "primary": "Contact",
     "operations": ["UPDATE"],
     "side_effects": ["Notification"],
     "optimistic_safe": true
   }';
```

#### 2. Static Impact Metadata File (`mutation-impacts.json`)
```json
{
  "version": "1.0.0",
  "generatedAt": "2025-11-08T16:00:00Z",
  "mutations": {
    "qualifyLead": {
      "description": "Qualifies a lead by updating their status",
      "input": {
        "contactId": { "type": "UUID", "required": true }
      },
      "impact": {
        "primary": {
          "entity": "Contact",
          "operation": "UPDATE",
          "fields": ["status", "updatedAt"],
          "relationships": ["company"]
        },
        "sideEffects": [
          {
            "entity": "Notification",
            "operation": "CREATE",
            "fields": ["id", "message", "createdAt"],
            "collection": "createdNotifications"
          }
        ],
        "cacheInvalidations": [
          {
            "query": "contacts",
            "filter": { "status": "lead" },
            "strategy": "REFETCH",
            "reason": "Contact removed from lead status list"
          },
          {
            "query": "dashboardStats",
            "strategy": "EVICT",
            "reason": "Lead count changed"
          }
        ],
        "permissions": ["can_edit_contact"],
        "optimisticUpdateSafe": true,
        "idempotent": false,
        "estimatedDuration": 150
      },
      "examples": [
        {
          "name": "Successful qualification",
          "input": { "contactId": "uuid-here" },
          "expectedResult": {
            "__typename": "QualifyLeadSuccess",
            "contact": { "status": "qualified" }
          }
        }
      ],
      "errors": [
        {
          "code": "validation_failed",
          "condition": "Contact is not a lead",
          "recovery": "Check contact status before calling"
        }
      ]
    }
  }
}
```

#### 3. TypeScript Type Definitions (`mutation-impacts.d.ts`)
```typescript
// Auto-generated types for mutation impacts

export interface MutationImpact {
  description: string;
  input: Record<string, { type: string; required: boolean }>;
  impact: {
    primary: EntityImpact;
    sideEffects: EntityImpact[];
    cacheInvalidations: CacheInvalidation[];
    permissions: string[];
    optimisticUpdateSafe: boolean;
    idempotent: boolean;
    estimatedDuration: number;
  };
  examples: MutationExample[];
  errors: MutationError[];
}

export interface EntityImpact {
  entity: string;
  operation: 'CREATE' | 'UPDATE' | 'DELETE' | 'UPSERT';
  fields: string[];
  relationships?: string[];
  collection?: string;
}

export interface CacheInvalidation {
  query: string;
  filter?: Record<string, any>;
  strategy: 'REFETCH' | 'EVICT' | 'UPDATE';
  reason: string;
}

export const MUTATION_IMPACTS: {
  qualifyLead: MutationImpact;
  // ... other mutations
};
```

**FraiseQL Integration**:
- Introspects `@fraiseql:mutation` comments
- Auto-generates GraphQL schema with proper types
- Maps `object_data` → primary entity field (e.g., `contact: Contact!`)
- Maps `extra_metadata.createdNotifications` → `createdNotifications: [Notification!]!`
- Maps `extra_metadata._meta` → `_meta: MutationImpactMetadata!`
- Exposes `updated_fields` as `updatedFields: [String!]!`

**Generated GraphQL Schema** (by FraiseQL):
```graphql
type QualifyLeadSuccess {
  status: String!
  message: String!
  updatedFields: [String!]!
  contact: Contact!
  createdNotifications: [Notification!]!
  _meta: MutationImpactMetadata!
}

type MutationImpactMetadata {
  primaryEntity: EntityImpact!
  actualSideEffects: [EntityImpact!]!
}

union QualifyLeadPayload = QualifyLeadSuccess | QualifyLeadError

type Mutation {
  qualifyLead(input: QualifyLeadInput!): QualifyLeadPayload!
}
```

**Frontend Code Generation**:
Team D also generates frontend-consumable artifacts:
- `mutation-impacts.json` - Static metadata for build-time consumption
- `mutation-impacts.d.ts` - TypeScript types
- `mutations.ts` - Pre-configured hooks with impact-based cache handling

**Status**: 🔴 Not Started (Week 5 focus)
**Location**: `src/generators/fraiseql/`
**Test Command**: `make teamD-test`

---

### 🔴 Team E: CLI & Orchestration + Frontend Codegen
**Mission**: Developer tools + pipeline orchestration + frontend code generation

**CLI Commands**:
```bash
# Generate complete migration from SpecQL
specql generate entities/contact.yaml
# Output:
#   - migrations/001_contact.sql (schema + functions + metadata)
#   - generated/mutation-impacts.json (impact metadata)
#   - generated/mutation-impacts.d.ts (TypeScript types)

# Generate with impact metadata for frontend
specql generate entities/*.yaml --with-impacts --output-frontend=../frontend/src/generated

# Validate SpecQL syntax and impact declarations
specql validate entities/*.yaml --check-impacts

# Show what would change
specql diff entities/contact.yaml

# Generate documentation from impacts
specql docs entities/*.yaml --format=markdown --output=docs/mutations.md

# Validate runtime impacts match declarations
specql validate-impacts --database-url=postgres://...
```

**Orchestration**: Coordinates Teams B + C + D + Frontend Codegen:
```python
def generate(yaml_file, with_impacts=False, output_frontend=None):
    # Team A: Parse
    entity = SpecQLParser().parse(yaml_file)

    # Team B: Generate schema
    schema_sql = SchemaGenerator().generate(entity)

    # Team C: Compile actions (with impact metadata if declared)
    action_sql = ActionCompiler().compile(entity.actions, include_impacts=with_impacts)

    # Team D: Add FraiseQL metadata + impact documentation
    metadata_sql = FraiseQLAnnotator().annotate(entity)

    # Combine into migration
    migration = combine(schema_sql, action_sql, metadata_sql)
    write_migration(migration)

    # NEW: Generate frontend artifacts
    if with_impacts:
        # Generate mutation-impacts.json
        impacts = extract_impacts(entity.actions)
        write_json('generated/mutation-impacts.json', impacts)

        # Generate TypeScript types
        ts_types = generate_typescript_types(impacts)
        write_file('generated/mutation-impacts.d.ts', ts_types)

        # Generate pre-configured mutation hooks
        if output_frontend:
            hooks = generate_mutation_hooks(impacts, entity.actions)
            write_file(f'{output_frontend}/mutations.ts', hooks)

        # Generate documentation
        docs = generate_mutation_docs(impacts, entity.actions)
        write_file('docs/mutations.md', docs)
```

**Frontend Code Generation**:

Generates pre-configured hooks with impact-based cache handling:

```typescript
// generated/mutations.ts (auto-generated)

import { useMutation, MutationHookOptions } from '@apollo/client';
import { MUTATION_IMPACTS } from './mutation-impacts';
import { QUALIFY_LEAD } from './graphql/mutations';

export function useQualifyLead(options?: MutationHookOptions) {
    const impact = MUTATION_IMPACTS.qualifyLead;

    return useMutation(QUALIFY_LEAD, {
        ...options,

        // Auto-configured from impact.cacheInvalidations
        refetchQueries: [
            ...impact.impact.cacheInvalidations
                .filter(i => i.strategy === 'REFETCH')
                .map(i => i.query),
            ...(options?.refetchQueries || [])
        ],

        // Auto-configured cache evictions
        update: (cache, result) => {
            // Evict queries marked with EVICT strategy
            impact.impact.cacheInvalidations
                .filter(i => i.strategy === 'EVICT')
                .forEach(i => cache.evict({ fieldName: i.query }));

            // Call user-provided update
            options?.update?.(cache, result);
        },

        // Auto-configured optimistic response (if safe)
        ...(impact.impact.optimisticUpdateSafe && {
            optimisticResponse: (vars) => ({
                __typename: 'Mutation',
                qualifyLead: {
                    __typename: 'QualifyLeadSuccess',
                    status: 'success',
                    message: 'Contact qualified',
                    updatedFields: impact.impact.primary.fields,
                    contact: {
                        __typename: 'Contact',
                        // User can override via options.optimisticResponse
                        ...(options?.variables || {})
                    },
                    createdNotifications: [],
                    _meta: {
                        primaryEntity: {
                            entityType: impact.impact.primary.entity,
                            operation: impact.impact.primary.operation,
                            modifiedFields: impact.impact.primary.fields
                        },
                        actualSideEffects: []
                    }
                }
            })
        })
    });
}

// Export all mutation impacts for reference
export { MUTATION_IMPACTS } from './mutation-impacts';
```

**Documentation Generation**:

```bash
$ specql docs entities/*.yaml --format=markdown

# Generates docs/mutations.md:
```

````markdown
# Mutation Reference

## qualifyLead

**Description**: Qualifies a lead by updating their status to 'qualified'

**Input**:
- `contactId` (UUID, required)

**Primary Impact**:
- **Entity**: Contact
- **Operation**: UPDATE
- **Modified Fields**: status, updatedAt
- **Relationships Included**: company

**Side Effects**:
- Creates Notification(s) in `createdNotifications` field

**Cache Impact**:
- ⚠️ **Refetch** `contacts` query (filter: `{status: "lead"}`)
  - *Reason*: Contact removed from lead status list
- ⚠️ **Evict** `dashboardStats` query
  - *Reason*: Lead count changed

**Optimistic Updates**: ✅ Safe

**Example Usage**:
```typescript
import { useQualifyLead } from '@/generated/mutations';

const [qualifyLead, { loading }] = useQualifyLead();

await qualifyLead({ variables: { contactId: '...' } });
```

**Possible Errors**:
- `validation_failed`: Contact is not a lead
  - *Recovery*: Check contact status before calling
```
````

**Impact Validation**:

```bash
# Runtime validation - compares actual vs declared impacts
$ specql validate-impacts --database-url=postgres://localhost/mydb

# Executes each mutation in test mode
# Compares result._meta.actualSideEffects vs. declared impact.sideEffects
# Reports mismatches

✓ qualifyLead: Actual impacts match declaration
✗ createContact: Expected 1 Notification, got 0
  → Check: Notification creation logic may have conditions
```

**Status**: 🔴 Not Started (Week 7 focus)
**Location**: `src/cli/`
**Test Command**: `make teamE-test`

---

## 📊 TEAM PROGRESS DASHBOARD

### Overall Project: 10% Complete (Week 1 of 10)

| Team | Focus | Week 1 Goal | Progress | Status |
|------|-------|-------------|----------|--------|
| **Team A** | SpecQL Parser | Parse lightweight DSL | **90%** | ✅ ON TRACK |
| **Team B** | Schema Gen | Not started yet | **0%** | ⏸️ WAITING |
| **Team C** | Action Compiler | Not started yet | **0%** | ⏸️ WAITING |
| **Team D** | FraiseQL Meta | Not started yet | **0%** | ⏸️ WAITING |
| **Team E** | CLI Tools | Not started yet | **0%** | ⏸️ WAITING |

### Week-by-Week Plan

**Week 1** (Current): Team A - SpecQL Parser
- ✅ Parse entity definitions (DONE)
- ✅ Parse field types (DONE)
- ✅ Parse actions and steps (DONE)
- 🚧 Minor refinements (in progress)

**Week 2**: Team B - Schema Generator
- Convention-based DDL generation
- Trinity pattern application
- Auto FK and index generation

**Week 3**: Team C - Action Compiler
- Basic step compilation (validate, insert, update)
- Conditional logic (if/then/else)
- Function scaffolding

**Week 4**: Integration Testing
- End-to-end: SpecQL → SQL → Database
- Performance testing
- Bug fixes

**Week 5-6**: Team D - FraiseQL Integration
- Metadata annotation generation
- GraphQL schema validation
- End-to-end with FraiseQL

**Week 7-8**: Team E - CLI & Developer Experience
- Command-line tools
- Migration management
- Documentation

**Week 9-10**: Production Readiness
- Advanced features
- Security hardening
- Performance optimization

---

## 🎯 CRITICAL: What Makes SpecQL "Lightweight"

### Users Write (Business Domain)
```yaml
entity: Contact
fields:
  email: text
  company: ref(Company)  # Just say "ref" - framework figures out FK
  status: enum(lead, qualified)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Total: 12 lines**

### Framework Auto-Generates (Technical Implementation)
- ✅ Trinity pattern (pk_contact, id, identifier)
- ✅ Foreign key: `fk_company INTEGER REFERENCES tb_company(pk_company)`
- ✅ Enum constraint: `CHECK (status IN ('lead', 'qualified'))`
- ✅ Indexes on fk_company, status, email
- ✅ Audit fields (created_at, updated_at, etc.)
- ✅ Helper functions (contact_pk, contact_id, contact_identifier)
- ✅ PL/pgSQL function for qualify_lead with:
  - Trinity resolution
  - Validation logic
  - Audit updates
  - Event emission
  - Error handling
- ✅ FraiseQL comments for GraphQL auto-discovery
- ✅ GraphQL types, queries, mutations

**Total: 2000+ lines auto-generated**

### What Users DON'T Write
- ❌ No SQL DDL syntax
- ❌ No foreign key syntax
- ❌ No index definitions
- ❌ No constraint syntax
- ❌ No PL/pgSQL code
- ❌ No GraphQL schema
- ❌ No resolver functions
- ❌ No type definitions

**Result**: 99% less code, 100% production-ready

---

## 📁 Repository Structure

```
src/
├── core/              # Team A: SpecQL Parser
│   ├── ast_models.py       # ✅ Business Entity AST
│   ├── specql_parser.py    # ✅ YAML → AST parser
│   └── README.md
│
├── generators/
│   ├── schema/        # Team B: Schema Generator
│   │   ├── schema_generator.py
│   │   ├── trinity_pattern.py
│   │   ├── naming_conventions.py
│   │   └── index_strategy.py
│   │
│   ├── actions/       # Team C: Action Compiler
│   │   ├── action_compiler.py
│   │   ├── expression_to_sql.py
│   │   └── step_generators/
│   │
│   └── fraiseql/      # Team D: FraiseQL Metadata
│       ├── annotator.py
│       ├── graphql_mapper.py
│       └── metadata_gen.py
│
├── cli/               # Team E: CLI & Orchestration
│   ├── generate.py
│   ├── validate.py
│   └── orchestrator.py
│
└── templates/
    ├── sql/           # DDL templates
    └── plpgsql/       # Function templates

tests/
├── unit/
│   ├── core/          # Team A tests ✅
│   ├── schema/        # Team B tests
│   ├── actions/       # Team C tests
│   ├── fraiseql/      # Team D tests
│   └── cli/           # Team E tests
│
└── integration/       # End-to-end tests

entities/
└── examples/
    ├── contact.yaml   # Simple example
    └── machine_item.yaml  # Complex example
```

---

## 🧪 Testing Strategy

### TDD Discipline (Mandatory)

Every feature follows: **RED → GREEN → REFACTOR → QA**

```bash
# RED: Write failing test
vim tests/unit/schema/test_schema_generator.py
uv run pytest tests/unit/schema/ -v  # Should fail

# GREEN: Minimal implementation
vim src/generators/schema/schema_generator.py
uv run pytest tests/unit/schema/ -v  # Should pass

# REFACTOR: Clean up
vim src/generators/schema/schema_generator.py
uv run pytest tests/unit/schema/ -v  # Still pass

# QA: Quality checks
make lint && make typecheck && make test
```

### Team-Specific Test Commands

```bash
make teamA-test  # Core parser tests
make teamB-test  # Schema generator tests
make teamC-test  # Action compiler tests
make teamD-test  # FraiseQL metadata tests
make teamE-test  # CLI tests

make test        # All tests
make integration # Integration tests
make coverage    # Coverage report (target: 90%+)
```

---

## 🚀 Getting Started (For AI Assistants)

### When Asked About Progress
1. Check **TEAM PROGRESS DASHBOARD** above
2. Report current week and focus
3. Identify what's blocking next steps

### When Asked to Help a Specific Team
1. Read team's section above for mission and focus
2. Check `src/{team}/README.md` for detailed specs
3. Follow **TDD cycle**: RED → GREEN → REFACTOR → QA
4. Use templates from `templates/` directory

### When Suggesting Work
1. **Prioritize current week's focus** (Week 1 = Team A only)
2. **Follow sequential team dependencies**:
   - Team A must finish before B/C/D start
   - Teams B/C/D can work in parallel (Week 2-6)
   - Team E orchestrates in Week 7+
3. **One team-specific task at a time**
4. **Test-first always** (write test before implementation)

---

## 💡 Example: Complete SpecQL → GraphQL Flow

### Step 1: User Writes SpecQL (20 lines)
```yaml
# entities/contact.yaml
entity: Contact
schema: crm

fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

### Step 2: Run Generator
```bash
specql generate entities/contact.yaml

# Output:
# ✓ Parsing SpecQL...
# ✓ Generating schema (Team B)...
#   - tb_contact table (Trinity pattern)
#   - 3 auto-indexes
#   - 4 helper functions
# ✓ Compiling actions (Team C)...
#   - qualify_lead() function
# ✓ Adding FraiseQL metadata (Team D)...
#   - 8 COMMENT annotations
# ✓ Writing: migrations/001_contact.sql (1,847 lines)
# ✓ Complete!
```

### Step 3: Apply to Database
```bash
psql < migrations/001_contact.sql
# Contact table created with Trinity pattern
# Functions created
# FraiseQL metadata attached
```

### Step 4: FraiseQL Auto-Discovery
```bash
# FraiseQL introspects database
# Finds @fraiseql:* comments
# Auto-generates GraphQL schema
```

### Step 5: GraphQL API Ready!
```graphql
# Auto-generated types
type Contact {
  id: UUID!
  email: String!
  company: Company
  status: ContactStatus!
}

# Auto-generated queries
query {
  contact(id: "...") { email, company { name } }
  contacts(filter: {status: LEAD}) { id, email }
}

# Auto-generated mutations (from qualify_lead function)
mutation {
  qualifyLead(contactId: "...") {
    success
    contact { id, status }
  }
}
```

**Total User Code**: 20 lines YAML
**Total Generated Code**: 2000+ lines (SQL + GraphQL)
**Code Leverage**: **100x**

---

## 🎯 Key Principles for AI Assistants

### 1. **Lightweight SpecQL Above All**
- If implementation requires users to write SQL/DDL → ❌ Wrong
- If implementation requires users to write GraphQL → ❌ Wrong
- Users write ONLY business domain → ✅ Correct

### 2. **Convention Over Configuration**
- Trinity pattern is ALWAYS applied → Not configurable
- Naming conventions are ALWAYS applied → Not configurable
- Audit fields are ALWAYS added → Not configurable
- Users specify business logic, framework handles the rest

### 3. **Test-Driven Development is Mandatory**
- Every feature starts with a failing test
- No implementation without tests
- 90%+ coverage target

### 4. **Clear Team Boundaries**
- Team A: Parse business DSL (NO infrastructure details)
- Team B: Apply DDL conventions (Trinity, indexes, constraints)
- Team C: Compile business actions to PL/pgSQL
- Team D: Add FraiseQL metadata
- Team E: Orchestrate everything

### 5. **Sequential Team Dependencies**
- Week 1: Team A only (parse SpecQL)
- Week 2+: Teams B/C/D (need Team A's AST)
- Week 7+: Team E (needs B/C/D output)

---

## 📚 Essential Documentation

### For Team A (SpecQL Parser)
- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Lightweight DSL spec
- `src/core/README.md` - Parser implementation guide

### For Team B (Schema Generator)
- `docs/analysis/POC_RESULTS.md` - Trinity pattern examples
- `docs/architecture/INTEGRATION_PROPOSAL.md` - Conventions to apply

### For Team C (Action Compiler)
- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Action step syntax
- Examples in `entities/examples/`

### For Team D (FraiseQL)
- `docs/analysis/FRAISEQL_INTEGRATION_REQUIREMENTS.md` - Metadata format
- FraiseQL documentation (external)

### For Team E (CLI)
- `CONTRIBUTING.md` - CLI workflow
- `docs/guides/` - User-facing docs (to be written)

---

## 🚨 Common Mistakes to Avoid

### ❌ Don't Parse Infrastructure Details in Team A
```yaml
# ❌ BAD - Don't parse this in SpecQL
foreign_keys:
  fk_company:
    references: tb_company
    on: pk_company
```
**Why**: Team B infers FKs from `ref(Company)` automatically

### ❌ Don't Make Users Write SQL Syntax
```yaml
# ❌ BAD - Don't require SQL syntax
fields:
  status: "TEXT CHECK (status IN ('lead', 'qualified'))"
```
```yaml
# ✅ GOOD - Simple business domain
fields:
  status: enum(lead, qualified)
```

### ❌ Don't Make Trinity Pattern Configurable
```yaml
# ❌ BAD - Don't let users configure Trinity
trinity_pattern:
  pk_field: custom_pk  # NO!
  id_field: custom_id  # NO!
```
**Why**: Consistency across all tables is critical

### ❌ Don't Skip Tests
```python
# ❌ BAD - Writing code without tests first
def generate_schema(entity):
    # Implementation without test
```

```python
# ✅ GOOD - Test-first development
def test_generate_schema_with_trinity_pattern():
    entity = Entity(name='Contact', ...)
    sql = SchemaGenerator().generate(entity)
    assert 'pk_contact' in sql
    assert 'id UUID' in sql
```

---

## 📞 Questions for AI to Ask

When uncertain, AI should ask:

### About Requirements
- "Does this feature belong in SpecQL (business), or is it a framework convention?"
- "Should this be auto-generated, or user-specified?"
- "Is this simplifying the user's YAML, or making it more complex?"

### About Implementation
- "Which team owns this functionality?"
- "Does Team A's AST support this, or do we need to extend it?"
- "Can we infer this from existing data, or must user specify?"

### About Testing
- "What's the failing test for this feature?"
- "Have we covered edge cases in tests?"
- "Does this maintain 90%+ coverage?"

---

**Last Updated**: 2025-11-08 (Post-Architecture Revision)
**Project Phase**: Week 1 - Team A (SpecQL Parser)
**Overall Progress**: 10% (1 of 10 weeks)
**Next Milestone**: Week 2 - Team B starts Schema Generation

---

## 🤖 AI Quick Reference Card

**Project Goal**: 20 lines YAML → 2000 lines production code (100x leverage)

**Current Focus**: Week 1 - Team A - SpecQL Parser (90% done)

**Key Principle**: Users write business domain ONLY, framework handles ALL technical details

**Critical Path**: Team A → Teams B/C/D → Team E → FraiseQL

**Test Command**: `make test`

**When in Doubt**: Keep SpecQL lightweight, move complexity to framework
