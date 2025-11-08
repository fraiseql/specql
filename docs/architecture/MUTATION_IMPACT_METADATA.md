# Mutation Impact Metadata - Auto-Documenting Side Effects for Frontend

## The Problem

Frontend developers need to know **in advance** (before calling a mutation):
- What entities will be affected?
- What fields might change?
- What side effects will occur?
- What cache invalidations are needed?
- What optimistic UI updates are safe?

Currently, they have to:
- ❌ Read backend code
- ❌ Call mutation in dev and inspect response
- ❌ Ask backend developers
- ❌ Guess and hope

## The Solution: GraphQL Schema Introspection + Parsable Metadata

Generate **machine-readable impact metadata** that frontend can introspect **before runtime**.

### Three Levels of Impact Documentation

## Level 1: GraphQL Schema Type Annotations (GraphQL Native)

**Idea**: Use GraphQL directives and descriptions to document impacts

```graphql
"""
Qualifies a lead by updating their status to 'qualified'.

**Affected Entities:**
- Contact (primary) - Updates: status, updatedAt
- Notification (created) - Creates notification for contact owner

**Cache Impact:**
- Invalidates: Contact queries filtered by status
- Updates: Contact:{id}
- Creates: Notification entries

**Optimistic UI:**
Safe to optimistically update Contact.status = 'qualified'
"""
type QualifyLeadSuccess {
    contact: Contact!
    createdNotifications: [Notification!]!
    updatedFields: [String!]!
}

# Alternative: Use custom directives
type QualifyLeadSuccess
  @mutationImpact(
    primary: "Contact"
    updates: ["status", "updatedAt"]
    creates: ["Notification"]
    invalidates: ["contactsByStatus"]
  )
{
    contact: Contact!
    createdNotifications: [Notification!]!
    updatedFields: [String!]!
}
```

**Frontend can introspect this:**

```typescript
// Auto-generated from GraphQL schema introspection
import { useQuery } from '@apollo/client';
import { getIntrospectionQuery } from 'graphql';

// One-time schema introspection
const { data } = useQuery(INTROSPECTION_QUERY);

// Parse mutation impact metadata
const qualifyLeadMutation = data.__schema.types
    .find(t => t.name === 'Mutation')
    .fields.find(f => f.name === 'qualifyLead');

const impactDoc = qualifyLeadMutation.description;
// Contains: "Affected Entities: Contact (primary), Notification (created)..."
```

**Pros:**
- ✅ GraphQL-native (no extra infrastructure)
- ✅ Already introspectable
- ✅ Works with existing tools (GraphiQL, Playground)

**Cons:**
- ⚠️ Requires parsing description strings
- ⚠️ Not strongly typed (unless using directives)

---

## Level 2: Structured Metadata in GraphQL Schema (Custom Field)

**Idea**: Add a special `_meta` field to every mutation payload that returns impact metadata

```graphql
type QualifyLeadSuccess {
    # Business data
    contact: Contact!
    createdNotifications: [Notification!]!
    updatedFields: [String!]!

    # Machine-readable impact metadata
    _meta: MutationImpactMetadata!
}

type MutationImpactMetadata {
    """The primary entity affected by this mutation"""
    primaryEntity: EntityImpact!

    """Secondary entities created or updated"""
    sideEffects: [EntityImpact!]!

    """Queries that should be invalidated"""
    cacheInvalidations: [CacheInvalidation!]!

    """Whether optimistic UI is safe for this mutation"""
    optimisticUpdateSafe: Boolean!

    """Estimated duration (ms) for this mutation"""
    estimatedDuration: Int
}

type EntityImpact {
    """Entity type name"""
    entityType: String!

    """Operation performed"""
    operation: MutationOperation!

    """Fields that will be modified"""
    modifiedFields: [String!]!

    """Relationships that may be affected"""
    affectedRelationships: [String!]!
}

enum MutationOperation {
    CREATE
    UPDATE
    DELETE
    UPSERT
}

type CacheInvalidation {
    """Query name to invalidate"""
    queryName: String!

    """Specific filter to invalidate (null = all)"""
    filter: JSONObject

    """Invalidation strategy"""
    strategy: InvalidationStrategy!
}

enum InvalidationStrategy {
    REFETCH       # Refetch the query
    EVICT         # Remove from cache
    UPDATE        # Update in place
}
```

**Generated from SpecQL:**

```yaml
actions:
  - name: qualify_lead

    # NEW: Impact declaration
    impact:
      primary:
        entity: Contact
        operation: update
        fields: [status, updatedAt]
        relationships: [company]

      side_effects:
        - entity: Notification
          operation: create
          fields: [id, message, createdAt]

      cache_invalidations:
        - query: contacts
          filter: { status: "lead" }  # This list will change
          strategy: REFETCH
        - query: contactsByStatus
          strategy: EVICT

      optimistic_safe: true
      estimated_duration_ms: 150

    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

**Team D generates PL/pgSQL that includes metadata:**

```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(...)
RETURNS mutation_result AS $$
DECLARE
    v_result mutation_result;
BEGIN
    -- Business logic...

    -- Impact metadata (generated from SpecQL impact declaration)
    v_result.extra_metadata := jsonb_build_object(
        '_meta', jsonb_build_object(
            'primaryEntity', jsonb_build_object(
                'entityType', 'Contact',
                'operation', 'UPDATE',
                'modifiedFields', jsonb_build_array('status', 'updatedAt'),
                'affectedRelationships', jsonb_build_array('company')
            ),
            'sideEffects', jsonb_build_array(
                jsonb_build_object(
                    'entityType', 'Notification',
                    'operation', 'CREATE',
                    'modifiedFields', jsonb_build_array('id', 'message', 'createdAt')
                )
            ),
            'cacheInvalidations', jsonb_build_array(
                jsonb_build_object(
                    'queryName', 'contacts',
                    'filter', jsonb_build_object('status', 'lead'),
                    'strategy', 'REFETCH'
                )
            ),
            'optimisticUpdateSafe', true,
            'estimatedDuration', 150
        ),

        -- Normal side effect data
        'createdNotifications', (...)
    );

    RETURN v_result;
END;
$$;
```

**Frontend usage:**

```typescript
const { data } = await qualifyLead({ variables: { contactId } });

if (data.qualifyLead.__typename === 'QualifyLeadSuccess') {
    const meta = data.qualifyLead._meta;

    // Know exactly what changed
    console.log('Primary entity:', meta.primaryEntity.entityType);
    console.log('Modified fields:', meta.primaryEntity.modifiedFields);
    // Output: Primary entity: Contact
    //         Modified fields: ['status', 'updatedAt']

    // Handle cache invalidations automatically
    meta.cacheInvalidations.forEach(inv => {
        if (inv.strategy === 'REFETCH') {
            client.refetchQueries({ include: [inv.queryName] });
        } else if (inv.strategy === 'EVICT') {
            client.cache.evict({ fieldName: inv.queryName });
        }
    });

    // Side effects
    console.log('Created:', meta.sideEffects);
    // Output: [{ entityType: 'Notification', operation: 'CREATE', ... }]
}
```

**Better: Code generation from schema:**

```typescript
// Auto-generated hooks with impact awareness
import { useQualifyLead } from './generated/mutations';

function ContactCard({ contact }) {
    const [qualifyLead, { loading }] = useQualifyLead({
        // Auto-generated cache handling based on _meta
        refetchQueries: (result) => {
            // Framework reads result._meta.cacheInvalidations
            // Auto-refetches affected queries
            return result._meta.cacheInvalidations
                .filter(i => i.strategy === 'REFETCH')
                .map(i => i.queryName);
        },

        // Auto-generated optimistic response
        optimisticResponse: (vars) => ({
            __typename: 'QualifyLeadSuccess',
            contact: {
                ...contact,
                status: 'qualified',  // Safe per _meta.optimisticUpdateSafe
            },
            createdNotifications: [],  // Empty per _meta.sideEffects
            updatedFields: ['status', 'updatedAt'],  // From _meta.primaryEntity
            _meta: {
                // Metadata for framework use
                primaryEntity: { ... },
                sideEffects: [ ... ]
            }
        })
    });

    return (
        <button onClick={() => qualifyLead({ contactId: contact.id })}>
            Qualify Lead
        </button>
    );
}
```

**Pros:**
- ✅ Fully typed metadata
- ✅ Available at runtime
- ✅ Can drive automatic cache handling
- ✅ Can generate optimistic responses
- ✅ Machine-readable

**Cons:**
- ⚠️ Adds payload size (but can be filtered with selection sets!)
- ⚠️ Requires custom code generation

---

## Level 3: Static Metadata File (Build-Time Discovery)

**Idea**: Generate a separate JSON file with all mutation impacts that frontend consumes at build time

**Generated file: `mutation-impacts.json`**

```json
{
  "version": "1.0.0",
  "generatedAt": "2025-11-08T15:30:00Z",
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
            "reason": "Removes contact from 'lead' status list"
          },
          {
            "query": "dashboardStats",
            "strategy": "EVICT",
            "reason": "Lead count will change"
          }
        ],
        "permissions": ["can_edit_contact"],
        "estimatedDuration": 150,
        "optimisticUpdateSafe": true,
        "idempotent": false
      },
      "examples": [
        {
          "name": "Successful qualification",
          "input": { "contactId": "uuid-here" },
          "expectedResult": {
            "typename": "QualifyLeadSuccess",
            "contact": { "status": "qualified" },
            "createdNotifications": [
              { "message": "Contact qualified" }
            ]
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
    },

    "createContact": {
      "description": "Creates a new contact",
      "input": { ... },
      "impact": {
        "primary": {
          "entity": "Contact",
          "operation": "CREATE",
          "fields": ["id", "email", "name", "status", "createdAt"]
        },
        "sideEffects": [],
        "cacheInvalidations": [
          {
            "query": "contacts",
            "strategy": "REFETCH",
            "reason": "New contact added to list"
          }
        ],
        "optimisticUpdateSafe": false,  // Can't predict ID
        "idempotent": false
      }
    }
  }
}
```

**Team E generates this during migration generation:**

```bash
$ specql generate entities/*.yaml --output-impacts mutation-impacts.json

✓ Parsed 15 entities
✓ Analyzed 42 actions
✓ Generated SQL migrations
✓ Generated mutation-impacts.json (25 mutations documented)
```

**Frontend build consumes it:**

```typescript
// Generated at build time from mutation-impacts.json
import mutationImpacts from './generated/mutation-impacts.json';

// Type-safe impact lookup
export function getMutationImpact(mutationName: string): MutationImpact {
    return mutationImpacts.mutations[mutationName];
}

// Auto-generated hooks
export function useQualifyLead() {
    const impact = getMutationImpact('qualifyLead');

    return useMutation(QUALIFY_LEAD_MUTATION, {
        // Auto-configured from impact metadata
        refetchQueries: impact.cacheInvalidations
            .filter(i => i.strategy === 'REFETCH')
            .map(i => i.query),

        awaitRefetchQueries: true,

        // Can't generate optimistic response if not safe
        ...(impact.optimisticUpdateSafe && {
            optimisticResponse: (vars) => ({
                // Generated based on impact.primary and impact.sideEffects
            })
        }),

        // Update cache for evictions
        update: (cache, { data }) => {
            impact.cacheInvalidations
                .filter(i => i.strategy === 'EVICT')
                .forEach(i => {
                    cache.evict({ fieldName: i.query });
                });
        }
    });
}
```

**Developer tools:**

```typescript
// Debug panel showing mutation impacts
import { MutationImpactViewer } from '@/components/dev-tools';

function DevPanel() {
    return (
        <MutationImpactViewer
            impacts={mutationImpacts}
            showExamples
            showCacheImpact
        />
    );
}

// Renders:
// qualifyLead
//   Primary: Contact (UPDATE)
//     Fields: status, updatedAt
//   Side Effects: Notification (CREATE)
//   Cache Impact:
//     ⚠️ Refetch: contacts (filter: status=lead)
//     ⚠️ Evict: dashboardStats
//   Optimistic: ✅ Safe
//   Duration: ~150ms
```

**Documentation generation:**

```bash
$ specql docs entities/*.yaml --format markdown

# Generates docs/mutations.md with:
- All mutations
- Impact metadata
- Examples
- Error cases
- Cache considerations
```

**Pros:**
- ✅ Zero runtime overhead
- ✅ Build-time type safety
- ✅ Can generate documentation
- ✅ Can generate dev tools
- ✅ Can drive code generation
- ✅ Versionable (track impact changes in git)

**Cons:**
- ⚠️ Requires build step
- ⚠️ Metadata may drift from implementation (needs validation)

---

## Recommended Hybrid Approach

**Combine Level 2 (Runtime) + Level 3 (Build-Time)**

### Build Time (Level 3)

```bash
# Generate mutations + impact metadata file
$ specql generate entities/*.yaml

# Outputs:
# - migrations/001_contact.sql (PostgreSQL functions)
# - generated/mutation-impacts.json (Static metadata)
# - generated/mutation-impacts.d.ts (TypeScript types)
```

**`mutation-impacts.json`:**
```json
{
  "qualifyLead": {
    "impact": {
      "primary": { "entity": "Contact", "operation": "UPDATE", ... },
      "sideEffects": [ ... ],
      "cacheInvalidations": [ ... ]
    }
  }
}
```

**Frontend code generation:**

```typescript
// Auto-generated from mutation-impacts.json
export const MUTATION_IMPACTS = {
    qualifyLead: {
        primary: { entity: 'Contact', operation: 'UPDATE' as const, ... },
        sideEffects: [ ... ],
        cacheInvalidations: [ ... ]
    }
} as const;

export type MutationImpacts = typeof MUTATION_IMPACTS;

// Auto-generated hook with impact awareness
export function useQualifyLead(options?: MutationHookOptions) {
    const impact = MUTATION_IMPACTS.qualifyLead;

    return useMutation(QUALIFY_LEAD, {
        ...options,

        // Auto-configured refetch based on impact
        refetchQueries: [
            ...impact.cacheInvalidations
                .filter(i => i.strategy === 'REFETCH')
                .map(i => i.query),
            ...(options?.refetchQueries || [])
        ],

        // Auto-configured cache evictions
        update: (cache, result) => {
            impact.cacheInvalidations
                .filter(i => i.strategy === 'EVICT')
                .forEach(i => cache.evict({ fieldName: i.query }));

            options?.update?.(cache, result);
        }
    });
}
```

### Runtime (Level 2)

**PostgreSQL function also includes metadata** (for dynamic behavior):

```sql
v_result.extra_metadata := jsonb_build_object(
    '_meta', jsonb_build_object(
        'primaryEntity', jsonb_build_object(...),
        'actualSideEffects', (
            -- ACTUAL side effects (may differ from expected)
            SELECT jsonb_agg(jsonb_build_object(
                'entity', 'Notification',
                'id', n.id,
                'operation', 'CREATE'
            ))
            FROM core.tb_notification n
            WHERE n.created_at > (now() - interval '1 second')
        )
    ),
    'createdNotifications', (...)
);
```

**Frontend can compare expected vs. actual:**

```typescript
const impact = MUTATION_IMPACTS.qualifyLead;  // Build-time metadata
const { data } = await qualifyLead({ ... });  // Runtime result

if (data.qualifyLead._meta.actualSideEffects.length !== impact.sideEffects.length) {
    console.warn('Unexpected side effects detected!');
    // Maybe a notification wasn't created (owner has notifications disabled)
}
```

---

## Implementation in SpecQL Pipeline

### Team C: Enhanced SpecQL Syntax

```yaml
actions:
  - name: qualify_lead

    # NEW: Impact declaration
    impact:
      description: "Qualifies a lead by updating their status to 'qualified'"

      primary:
        entity: Contact
        operation: update
        fields: [status, updatedAt]
        include_relations: [company]  # These will be in response

      side_effects:
        - entity: Notification
          operation: create
          collection: createdNotifications
          fields: [id, message, createdAt]
          condition: "owner has notifications enabled"

      cache_invalidations:
        - query: contacts
          filter: { status: "lead" }
          strategy: refetch
          reason: "Contact removed from lead list"

        - query: dashboardStats
          strategy: evict
          reason: "Lead count changed"

      permissions:
        - can_edit_contact

      optimistic_safe: true
      idempotent: false
      estimated_duration_ms: 150

    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

### Team D: Generate Impact Metadata

**Outputs:**

1. **Static file** (`mutation-impacts.json`)
2. **TypeScript types** (`mutation-impacts.d.ts`)
3. **PL/pgSQL with runtime metadata** (in `extra_metadata._meta`)
4. **FraiseQL annotations** (with impact hints)

```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead
   impact={
     "primary": "Contact",
     "sideEffects": ["Notification"],
     "cacheInvalidations": ["contacts", "dashboardStats"]
   }';
```

### Team E: CLI Commands

```bash
# Generate everything including impact metadata
$ specql generate entities/*.yaml --with-impacts

# Validate impact declarations against implementation
$ specql validate-impacts entities/*.yaml

# Generate documentation from impacts
$ specql docs entities/*.yaml --format=markdown

# Generate frontend code
$ specql codegen:frontend entities/*.yaml --output=src/generated/
```

---

## Frontend Usage Examples

### Example 1: Basic Mutation with Auto-Configured Cache

```typescript
import { useQualifyLead } from '@/generated/mutations';

function ContactActions({ contact }) {
    // Hook is pre-configured with impact metadata
    const [qualifyLead, { loading }] = useQualifyLead();

    return (
        <button
            onClick={() => qualifyLead({ variables: { contactId: contact.id } })}
            disabled={loading}
        >
            Qualify Lead
        </button>
    );

    // Framework automatically:
    // ✅ Refetches contacts (status=lead) query
    // ✅ Evicts dashboardStats from cache
    // ✅ Updates Contact cache entry
}
```

### Example 2: Custom Cache Handling

```typescript
import { useQualifyLead, MUTATION_IMPACTS } from '@/generated/mutations';

function AdvancedContactActions({ contact }) {
    const impact = MUTATION_IMPACTS.qualifyLead;

    const [qualifyLead] = useQualifyLead({
        // Extend default impact-based config
        refetchQueries: [
            'myCustomQuery',  // Add extra query
            ...impact.cacheInvalidations.map(i => i.query)
        ],

        onCompleted: (data) => {
            // Log actual side effects
            console.log('Expected side effects:', impact.sideEffects);
            console.log('Actual side effects:', data.qualifyLead._meta.actualSideEffects);
        }
    });
}
```

### Example 3: Developer Tools

```typescript
import { MUTATION_IMPACTS } from '@/generated/mutations';

function MutationDebugger() {
    return (
        <div>
            <h2>Mutation Impact Reference</h2>
            {Object.entries(MUTATION_IMPACTS).map(([name, impact]) => (
                <details key={name}>
                    <summary>{name}</summary>
                    <dl>
                        <dt>Primary Entity</dt>
                        <dd>{impact.primary.entity} ({impact.primary.operation})</dd>

                        <dt>Modified Fields</dt>
                        <dd>{impact.primary.fields.join(', ')}</dd>

                        <dt>Side Effects</dt>
                        <dd>
                            {impact.sideEffects.map(se =>
                                `${se.entity} (${se.operation})`
                            ).join(', ')}
                        </dd>

                        <dt>Cache Impact</dt>
                        <dd>
                            {impact.cacheInvalidations.map(ci =>
                                `${ci.strategy}: ${ci.query} - ${ci.reason}`
                            ).join('\n')}
                        </dd>

                        <dt>Optimistic Update</dt>
                        <dd>{impact.optimisticSafe ? '✅ Safe' : '❌ Not safe'}</dd>
                    </dl>
                </details>
            ))}
        </div>
    );
}
```

---

## Benefits Summary

### For Frontend Developers

✅ **No guesswork** - Know exactly what each mutation does before calling it
✅ **Auto-configured cache** - Framework handles refetch/evict automatically
✅ **Type-safe impacts** - TypeScript knows all impact metadata
✅ **Better optimistic UI** - Know which mutations are safe to optimistically update
✅ **Faster debugging** - See expected vs. actual side effects
✅ **Better error handling** - Know what to expect, easier to detect anomalies
✅ **Self-documenting code** - Impact metadata serves as inline documentation

### For Backend Developers

✅ **Single source of truth** - SpecQL impact declaration generates everything
✅ **Contract enforcement** - Runtime can validate actual vs. declared impacts
✅ **Breaking change detection** - Impact changes show up in git diffs
✅ **Better testing** - Can test that impacts match declarations
✅ **Documentation generation** - API docs auto-generated from impacts

### For the Project

✅ **100x code leverage maintained** - Impacts declared once, used everywhere
✅ **Frontend/backend alignment** - Both work from same impact metadata
✅ **Easier onboarding** - New devs can see mutation impacts at a glance
✅ **Safer refactoring** - Impact changes are explicit and visible
✅ **Better monitoring** - Can track if mutations behave as expected

---

## Conclusion

**Recommended Implementation:**

1. **SpecQL Syntax**: Add `impact:` section to action declarations
2. **Team C**: Generate PL/pgSQL with runtime `_meta` in `extra_metadata`
3. **Team D**: Generate static `mutation-impacts.json` + TypeScript types
4. **Team E**: CLI commands for validation, docs, and frontend codegen
5. **FraiseQL**: Include impact hints in `@fraiseql:mutation` annotations

**Result:**

Frontend developers get **parsable, type-safe, build-time and runtime impact metadata** that:
- Drives automatic cache configuration
- Enables safe optimistic updates
- Provides self-documenting code
- Detects unexpected behavior
- All generated from SpecQL's lightweight business-domain syntax

**File locations for generated code:**
```
generated/
├── mutation-impacts.json        # Static impact metadata
├── mutation-impacts.d.ts        # TypeScript types
├── mutations.ts                 # Hooks with auto-configured impacts
└── docs/
    └── mutations.md             # Human-readable documentation
```

This completes the loop: SpecQL business logic → Impact metadata → Frontend consumption → Perfect DX.
