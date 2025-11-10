# FraiseQL Integration Proposal: Mutation Impact Metadata

**Target**: FraiseQL Maintainers
**From**: SpecQL → PostgreSQL → GraphQL Generator Project
**Date**: 2025-11-08
**Status**: Proposal for Enhancement

---

## Executive Summary

We're building a lightweight business DSL (SpecQL) that generates PostgreSQL functions returning FraiseQL's `mutation_result` type. We propose **two small enhancements** to FraiseQL that would enable frontend developers to automatically discover mutation impacts (which entities are affected, cache invalidation needs, etc.) **without reading backend code**.

**What we're asking for:**

1. **Expose `updated_fields` in GraphQL schema** (5 lines of code)
2. **Map `extra_metadata._meta` to a `MutationImpactMetadata` type** (already supported via existing mechanisms)

Both are **backward compatible** and leverage FraiseQL's existing architecture.

---

## Background: What We're Building

### SpecQL: Lightweight Business Domain DSL

**User writes (20 lines of YAML):**
```yaml
entity: Contact
schema: crm

fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified)

actions:
  - name: qualify_lead
    impact:
      primary:
        entity: Contact
        operation: update
        fields: [status, updatedAt]
        include_relations: [company]
      side_effects:
        - entity: Notification
          operation: create
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

**Auto-generates (2000+ lines):**
- PostgreSQL table with Trinity pattern
- PL/pgSQL function returning `mutation_result`
- FraiseQL `@fraiseql:mutation` annotations
- Static `mutation-impacts.json` for frontend
- TypeScript types
- Pre-configured Apollo hooks

**Result**: 100x code leverage

### Why We Chose FraiseQL

FraiseQL's `mutation_result` pattern is **perfect** for our needs:

```sql
CREATE TYPE mutation_result AS (
    id UUID,
    updated_fields TEXT[],      -- ✅ Tracks what changed
    status TEXT,                -- ✅ success/error
    message TEXT,               -- ✅ Human feedback
    object_data JSONB,          -- ✅ Full entity data
    extra_metadata JSONB        -- ✅ Extensible for side effects
);
```

Our generated functions use this structure exactly as designed:

```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(...)
RETURNS mutation_result AS $$
BEGIN
    -- Business logic...

    v_result.object_data := (
        -- Full Contact object (FraiseQL maps this to 'contact' field)
        SELECT jsonb_build_object(
            '__typename', 'Contact',
            'id', c.id,
            'email', c.email,
            'status', c.status,
            'company', (...)  -- Include relationships
        )
        FROM crm.tb_contact c WHERE ...
    );

    v_result.extra_metadata := jsonb_build_object(
        'createdNotifications', (...),  -- Side effects
        '_meta', (...)                   -- Impact metadata
    );

    RETURN v_result;
END;
$$;
```

FraiseQL then auto-generates GraphQL from `@fraiseql:mutation` comments. **This works beautifully.**

---

## The Gap: Frontend Discovery of Mutation Impacts

### Current State (After FraiseQL Auto-Discovery)

**Generated GraphQL (by FraiseQL):**
```graphql
type QualifyLeadSuccess {
    status: String!
    message: String!
    contact: Contact!                      # From object_data
    createdNotifications: [Notification!]! # From extra_metadata
}
```

**Frontend developer's question:**
> "Before I call `qualifyLead`, how do I know:
> - What entities will be affected?
> - Which fields will change?
> - What cache invalidations are needed?
> - Whether optimistic UI is safe?"

**Current answer:** Read backend code or trial-and-error.

### Desired State

**Frontend developer can discover impacts at build-time:**

```typescript
import { MUTATION_IMPACTS } from '@/generated/mutation-impacts';

const impact = MUTATION_IMPACTS.qualifyLead;

console.log(impact.primary);
// { entity: 'Contact', operation: 'UPDATE', fields: ['status', 'updatedAt'] }

console.log(impact.sideEffects);
// [{ entity: 'Notification', operation: 'CREATE' }]

console.log(impact.cacheInvalidations);
// [{ query: 'contacts', filter: {status: 'lead'}, strategy: 'REFETCH' }]

console.log(impact.optimisticUpdateSafe);
// true
```

**And at runtime, validate actual impacts:**

```graphql
mutation QualifyLead($contactId: UUID!) {
    qualifyLead(input: {contactId: $contactId}) {
        __typename
        ... on QualifyLeadSuccess {
            contact { id, status }
            updatedFields        # ✅ NEW: Know what changed
            _meta {              # ✅ NEW: Runtime validation
                primaryEntity {
                    entityType
                    operation
                    modifiedFields
                }
                actualSideEffects {
                    entity
                    operation
                }
            }
        }
    }
}
```

---

## Proposed Enhancements to FraiseQL

### Enhancement 1: Expose `updated_fields` in Success Types

**Current**: `mutation_result.updated_fields` is tracked but not exposed in GraphQL

**Proposed**: Auto-add `updatedFields: [String!]!` to success types

**Implementation** (estimated 5-10 lines):

```python
# In mutation_generator.py or parser.py

# When generating success type from mutation_result:
success_type_fields = {
    'status': String!,
    'message': String!,
    'updatedFields': [String!]!,  # NEW: Map from mutation_result.updated_fields
    # ... other fields from object_data/extra_metadata
}
```

**GraphQL Output:**
```graphql
type QualifyLeadSuccess {
    status: String!
    message: String!
    updatedFields: [String!]!   # ✅ NEW
    contact: Contact!
    createdNotifications: [Notification!]!
}
```

**Frontend Benefit:**
```typescript
const { data } = await qualifyLead({ ... });

console.log('Changed fields:', data.qualifyLead.updatedFields);
// Output: ['status', 'updatedAt']

// Can show precise UI feedback: "Status updated"
// Can invalidate specific cache entries
```

**Backward Compatibility**: ✅ Additive only, no breaking changes

---

### Enhancement 2: Support `_meta` Field Mapping (Already Works?)

**Current**: FraiseQL maps `extra_metadata` fields to GraphQL fields via annotations

**Our Use Case**: Map `extra_metadata._meta` → `_meta: MutationImpactMetadata!`

**Annotation We'll Generate:**
```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead
   success_type=QualifyLeadSuccess
   metadata_mapping={
     "createdNotifications": "Notification[]",
     "_meta": "MutationImpactMetadata"
   }';
```

**PostgreSQL Function Returns:**
```sql
v_result.extra_metadata := jsonb_build_object(
    'createdNotifications', (...),
    '_meta', jsonb_build_object(
        'primaryEntity', jsonb_build_object(
            'entityType', 'Contact',
            'operation', 'UPDATE',
            'modifiedFields', jsonb_build_array('status', 'updatedAt')
        ),
        'actualSideEffects', (...)
    )
);
```

**Expected GraphQL (if FraiseQL supports this):**
```graphql
type QualifyLeadSuccess {
    status: String!
    message: String!
    updatedFields: [String!]!
    contact: Contact!
    createdNotifications: [Notification!]!
    _meta: MutationImpactMetadata!  # From extra_metadata._meta
}

type MutationImpactMetadata {
    primaryEntity: EntityImpact!
    actualSideEffects: [EntityImpact!]!
}

type EntityImpact {
    entityType: String!
    operation: String!
    modifiedFields: [String!]!
}
```

**Question for FraiseQL Team:**
Does `metadata_mapping` already support arbitrary JSONB → GraphQL type mapping?

If YES: ✅ No changes needed, we just document the pattern
If NO: Could this be added to the parser's field extraction logic?

**Frontend Benefit:**
```typescript
const { data } = await qualifyLead({ ... });

// Runtime validation: Compare declared vs. actual impacts
const declaredImpacts = MUTATION_IMPACTS.qualifyLead; // Build-time
const actualImpacts = data.qualifyLead._meta;         // Runtime

if (actualImpacts.actualSideEffects.length !== declaredImpacts.sideEffects.length) {
    console.warn('Unexpected side effects detected!');
}
```

**Backward Compatibility**: ✅ Opt-in via annotation, no impact on existing functions

---

## Alternative: Selection Filter Integration (Separate Enhancement)

**From your analysis document**: `/tmp/investigation_summary.txt`

> **MISSING CAPABILITY: SELECTIVE FIELD RETURNS**
> - ❌ No GraphQL selection set inspection in mutation response
> - ✅ `/src/fraiseql/mutations/selection_filter.py` (complete, unused)
> - **POINT A: IMMEDIATE (1-2 hours, 30-50% savings)**

**Our Request**: Please integrate `selection_filter` into mutation responses!

**Implementation Point** (from your docs):
```python
# File: /src/fraiseql/mutations/mutation_decorator.py
# Line: 157 (after parse_mutation_result)

parsed_result = parse_mutation_result(...)

# NEW: Filter based on GraphQL selection set
if dataclasses.is_dataclass(parsed_result):
    from fraiseql.mutations.selection_filter import filter_mutation_result
    filtered = filter_mutation_result(dataclasses.asdict(parsed_result), info)
    parsed_result = type(parsed_result)(**filtered)

return parsed_result
```

**Why This Matters for Us:**

Frontend developers using SpecQL-generated mutations often request minimal fields:

```graphql
mutation QualifyLead($contactId: UUID!) {
    qualifyLead(input: {contactId: $contactId}) {
        ... on QualifyLeadSuccess {
            contact {
                id      # Only these 2 fields
                status  #
            }
        }
    }
}
```

**Current**: Database returns all fields in `object_data`, network sends all fields
**After integration**: Network only sends requested fields (30-50% savings per your estimate)

**Impact for SpecQL Users:**
- Faster responses
- Less bandwidth
- Better mobile performance
- No changes to our generator (it already produces full objects in `object_data`)

This is a **pure FraiseQL enhancement** that benefits everyone, not just SpecQL.

---

## Summary: What We're Asking

### Must-Have (for MVP)

1. **Expose `updated_fields` as `updatedFields: [String!]!` in success types**
   - Effort: ~5-10 lines of code
   - Backward compatible: Yes (additive only)
   - Benefit: Frontend knows exactly what changed

### Nice-to-Have (for Better DX)

2. **Support `_meta` field mapping from `extra_metadata._meta`**
   - Effort: May already work? Or ~20-30 lines if parser enhancement needed
   - Backward compatible: Yes (opt-in via annotation)
   - Benefit: Runtime impact validation

3. **Integrate `selection_filter` into mutation responses**
   - Effort: 3-4 lines per your analysis
   - Backward compatible: Yes (transparent optimization)
   - Benefit: 30-50% network savings for everyone

---

## What We'll Provide

### For FraiseQL Documentation

We'll contribute examples showing:

1. **How to structure mutation functions for impact metadata**
   ```sql
   v_result.extra_metadata := jsonb_build_object(
       'sideEffectField', (...),
       '_meta', (...)  -- Impact metadata pattern
   );
   ```

2. **How to annotate functions with `metadata_mapping`**
   ```sql
   COMMENT ON FUNCTION ... IS
     '@fraiseql:mutation metadata_mapping={"_meta": "MutationImpactMetadata"}';
   ```

3. **Frontend patterns for consuming impact metadata**
   - Build-time introspection
   - Runtime validation
   - Auto-configured cache handling

### For SpecQL Generator

We'll build:

1. **Team C**: Generates PostgreSQL functions with FraiseQL-compatible `mutation_result`
2. **Team D**: Generates `@fraiseql:mutation` annotations with impact hints
3. **Team E**: Generates static `mutation-impacts.json` + TypeScript types + docs

All working seamlessly with FraiseQL's auto-discovery.

---

## Questions for FraiseQL Team

1. **`updated_fields` Exposure**:
   - Is this something you'd consider adding?
   - Where in the codebase should we look if we wanted to contribute a PR?

2. **`_meta` Field Mapping**:
   - Does `metadata_mapping` already support arbitrary JSONB → GraphQL type?
   - If not, would you accept a PR to add this?
   - Are there alternative patterns we should use?

3. **Selection Filter Integration**:
   - You mentioned this is "ready for integration" - is there a planned timeline?
   - Can we help with testing/documentation?
   - Should this be behind a feature flag initially?

4. **GraphQL Type Generation for Metadata**:
   - Should we define `MutationImpactMetadata` as a table with `@fraiseql:type`?
   - Or should we use a different pattern (custom GraphQL types file)?

5. **Contribution Process**:
   - If we wanted to contribute PRs for these features, what's your preferred process?
   - Do you have contribution guidelines?
   - Should we open GitHub issues first?

---

## Example: Full Integration Flow

### 1. SpecQL Input (User writes)
```yaml
actions:
  - name: qualify_lead
    impact:
      primary:
        entity: Contact
        operation: update
        fields: [status, updatedAt]
      side_effects:
        - entity: Notification
          operation: create
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

### 2. Generated PostgreSQL Function
```sql
CREATE FUNCTION crm.qualify_lead(...)
RETURNS mutation_result AS $$
BEGIN
    v_result.updated_fields := ARRAY['status', 'updated_at'];
    v_result.object_data := (SELECT jsonb_build_object(...));
    v_result.extra_metadata := jsonb_build_object(
        'createdNotifications', (...),
        '_meta', jsonb_build_object(
            'primaryEntity', jsonb_build_object(
                'entityType', 'Contact',
                'operation', 'UPDATE',
                'modifiedFields', jsonb_build_array('status', 'updatedAt')
            )
        )
    );
    RETURN v_result;
END;
$$;
```

### 3. Generated FraiseQL Annotation
```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead
   success_type=QualifyLeadSuccess
   metadata_mapping={
     "createdNotifications": "Notification[]",
     "_meta": "MutationImpactMetadata"
   }';
```

### 4. FraiseQL Auto-Generates GraphQL
```graphql
type QualifyLeadSuccess {
    status: String!
    message: String!
    updatedFields: [String!]!           # From mutation_result.updated_fields
    contact: Contact!                   # From object_data
    createdNotifications: [Notification!]!  # From extra_metadata
    _meta: MutationImpactMetadata!      # From extra_metadata._meta
}
```

### 5. Frontend Gets Perfect Types
```typescript
const { data } = await qualifyLead({ ... });

// Full type safety
data.qualifyLead.updatedFields  // string[]
data.qualifyLead.contact        // Contact
data.qualifyLead._meta          // MutationImpactMetadata

// Runtime validation
console.log('Changed:', data.qualifyLead.updatedFields);
console.log('Actual impacts:', data.qualifyLead._meta.actualSideEffects);
```

---

## Benefits for FraiseQL Ecosystem

1. **Better Developer Experience**:
   - Frontend devs can discover mutation impacts without reading code
   - Optimistic UI becomes easier
   - Cache management becomes automatic

2. **Better Documentation**:
   - Mutation impacts are self-documenting
   - GraphQL schema becomes more informative
   - Example patterns for complex mutations

3. **Better Performance**:
   - Selection filter integration saves bandwidth
   - Fewer roundtrips (no refetch needed)
   - Better mobile experience

4. **Better Testing**:
   - Runtime vs. declared impact validation
   - Easier to detect breaking changes
   - Automated impact testing

5. **Showcase for FraiseQL**:
   - SpecQL → FraiseQL integration becomes a reference example
   - Shows FraiseQL's power for DSL-to-GraphQL use cases
   - Demonstrates ecosystem extensibility

---

## Timeline

**Our Side (SpecQL Generator)**:
- Week 1 (current): Team A - Parser (90% done)
- Week 2-3: Team B - Schema Generator
- Week 3-4: Team C - Action Compiler (needs FraiseQL `mutation_result` pattern)
- Week 5-6: Team D - FraiseQL Metadata Generator (needs answers to questions above)
- Week 7+: Team E - CLI & Frontend Codegen

**Ideal FraiseQL Timeline**:
- **By Week 5**: Clarify `updated_fields` exposure and `_meta` mapping patterns
- **By Week 6**: (Optional) Selection filter integration
- **By Week 8**: Final integration testing

We can work around limitations in the meantime, but having these features would make the integration **much** cleaner.

---

## Contact

**Project**: SpecQL → PostgreSQL → FraiseQL → GraphQL Generator
**GitHub**: (TBD - currently in development)
**Documentation**: `/home/lionel/code/printoptim_backend_poc/docs/architecture/`

**Key Docs**:
- `FRAISEQL_BRIDGES_THE_GAP.md` - How FraiseQL solves frontend pain points
- `MUTATION_IMPACT_METADATA.md` - Impact metadata design
- `FRONTEND_CRITIQUE_RETURN_PATTERN.md` - Why deltas don't work for frontend

We're excited to work with FraiseQL and would love to contribute back to the project!

---

**Thank you for building FraiseQL!** Your `mutation_result` pattern and auto-discovery architecture are exactly what we needed. These small enhancements would make it perfect for our use case and benefit the entire FraiseQL ecosystem.
