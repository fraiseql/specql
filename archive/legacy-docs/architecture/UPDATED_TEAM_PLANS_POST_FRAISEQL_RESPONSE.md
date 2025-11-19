# Updated Team Plans - Post FraiseQL Response

**Date**: 2025-11-08
**Status**: FraiseQL v1.4.0 alignment confirmed
**Impact**: Minor adjustments to original plan, major clarity gains

---

## Executive Summary: What Changed

### FraiseQL's Response (All Positive! ✅)

1. **`updatedFields` exposure**: ✅ ACCEPTED - Will be in v1.4.0 (Week 3-4)
2. **`_meta` mapping via composite types**: ✅ ACCEPTED - Already 80% supported, test ASAP
3. **Selection filter integration**: ✅ ALREADY PLANNED - Need our help with tests

### Key Decision: Use PostgreSQL Composite Types for Metadata

**Before (uncertain)**:
```yaml
impact:
  _meta: ???  # How to make this work with FraiseQL?
```

**After (clear pattern from FraiseQL)**:
```sql
-- One-time: Create metadata types
CREATE SCHEMA mutation_metadata;

CREATE TYPE mutation_metadata.entity_impact AS (
    entity_type TEXT,
    operation TEXT,
    modified_fields TEXT[]
);

CREATE TYPE mutation_metadata.mutation_impact_metadata AS (
    primary_entity mutation_metadata.entity_impact,
    actual_side_effects mutation_metadata.entity_impact[]
);

COMMENT ON TYPE mutation_metadata.mutation_impact_metadata IS
  '@fraiseql:type name=MutationImpactMetadata';

-- Per function: Use the types
DECLARE
    v_meta mutation_metadata.mutation_impact_metadata;
BEGIN
    v_meta.primary_entity := ('Contact', 'UPDATE', ARRAY['status', 'updated_at']);
    v_result.extra_metadata := jsonb_build_object('_meta', to_jsonb(v_meta));
END;
```

**Benefits**:
- ✅ Type safety in PostgreSQL (compile-time errors)
- ✅ FraiseQL auto-discovery (already works!)
- ✅ No parser changes needed
- ✅ Reusable across all functions

---

## Updated Team Plans

### 🔵 Team A: SpecQL Parser (Week 1)

**Status**: 90% Complete ✅

**No Changes Required** - Parser already supports impact declarations

**Current Output**:
```python
@dataclass
class ActionImpact:
    primary: EntityImpact
    side_effects: List[EntityImpact]
    cache_invalidations: List[CacheInvalidation]
    optimistic_safe: bool
    estimated_duration_ms: int
```

**Next Steps**:
- Finish remaining 10% (error handling, edge cases)
- Add tests for impact parsing
- **NEW**: Validate impact declarations can map to composite types

---

### 🟢 Team B: Schema Generator (Week 2-3)

**Status**: Not Started

**New Responsibility**: Generate `mutation_metadata` schema (ONE-TIME)

#### Phase Plan

**Phase 1: Trinity Pattern Tables (Week 2)**
- Generate `CREATE TABLE` with pk_*, id, identifier
- Generate foreign keys from `ref(Entity)`
- Generate indexes
- Generate constraints

**Phase 2: Metadata Schema (Week 2, End)**

**NEW: Generate composite types for mutation metadata**

```sql
-- migrations/000_mutation_metadata.sql (ONE-TIME)

CREATE SCHEMA mutation_metadata;

-- Entity impact type
CREATE TYPE mutation_metadata.entity_impact AS (
    entity_type TEXT,           -- e.g., "Contact"
    operation TEXT,             -- "CREATE", "UPDATE", "DELETE"
    modified_fields TEXT[]      -- Fields that were changed
);

COMMENT ON TYPE mutation_metadata.entity_impact IS
  '@fraiseql:type
   name=EntityImpact
   description="Describes impact on a single entity during mutation"';

-- Cache invalidation type
CREATE TYPE mutation_metadata.cache_invalidation AS (
    query_name TEXT,            -- e.g., "contacts"
    filter_json JSONB,          -- e.g., {"status": "lead"}
    strategy TEXT,              -- "REFETCH", "EVICT", "UPDATE"
    reason TEXT                 -- Human-readable explanation
);

COMMENT ON TYPE mutation_metadata.cache_invalidation IS
  '@fraiseql:type
   name=CacheInvalidation
   description="Describes which queries should be invalidated"';

-- Main metadata type
CREATE TYPE mutation_metadata.mutation_impact_metadata AS (
    primary_entity mutation_metadata.entity_impact,
    actual_side_effects mutation_metadata.entity_impact[],
    cache_invalidations mutation_metadata.cache_invalidation[]
);

COMMENT ON TYPE mutation_metadata.mutation_impact_metadata IS
  '@fraiseql:type
   name=MutationImpactMetadata
   description="Runtime metadata about mutation impacts for frontend cache management"';
```

**Testing**:
- ✅ Types are created
- ✅ FraiseQL discovers them (introspection test)
- ✅ GraphQL schema includes MutationImpactMetadata type

**Timeline**: Week 2 end (before Team C needs them)

---

### 🟠 Team C: Action Compiler (Week 3-4)

**Status**: Not Started

**Major Update**: Use composite types for type-safe metadata construction

#### Phase Plan

**Phase 1: Basic Actions WITHOUT Impacts (Week 3, Days 1-2)**

Generate simple functions:
```sql
CREATE FUNCTION crm.qualify_lead(...)
RETURNS mutation_result AS $$
DECLARE
    v_pk INTEGER;
    v_result mutation_result;
BEGIN
    -- Trinity resolution
    v_pk := crm.contact_pk(p_contact_id);

    -- Validation (from SpecQL steps)
    -- Business logic (from SpecQL steps)

    -- Simple response (no _meta yet)
    v_result.status := 'success';
    v_result.message := 'Contact qualified';
    v_result.updated_fields := ARRAY['status', 'updated_at'];
    v_result.object_data := (...);  -- Full Contact object

    RETURN v_result;
END;
$$;
```

**Testing**: Basic mutations work with FraiseQL

**Phase 2: Add Impact Metadata (Week 3, Days 3-5)**

**NEW: Type-safe metadata construction**

```sql
CREATE FUNCTION crm.qualify_lead(...)
RETURNS mutation_result AS $$
DECLARE
    v_pk INTEGER;
    v_result mutation_result;
    v_meta mutation_metadata.mutation_impact_metadata;  -- ✅ Type-safe!
BEGIN
    -- ... business logic ...

    -- Build impact metadata (compile-time type checking!)
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

    -- Combine into result
    v_result.extra_metadata := jsonb_build_object(
        'createdNotifications', (...),
        '_meta', to_jsonb(v_meta)  -- ✅ Convert to JSONB
    );

    RETURN v_result;
END;
$$;
```

**Key Changes from Original Plan**:
- ❌ No manual JSONB construction (error-prone)
- ✅ Use composite types (type-safe)
- ✅ PostgreSQL validates at compile time
- ✅ `to_jsonb(v_meta)` converts to proper structure

**Phase 3: Full Object Selection with Relationships (Week 4)**

```sql
-- Include relationships as specified in impact.primary.include_relations
v_result.object_data := (
    SELECT jsonb_build_object(
        '__typename', 'Contact',
        'id', c.id,
        'email', c.email,
        'status', c.status,
        'updatedAt', c.updated_at,
        'company', jsonb_build_object(  -- ✅ From include_relations: [company]
            '__typename', 'Company',
            'id', co.id,
            'name', co.name
        )
    )
    FROM crm.tb_contact c
    LEFT JOIN management.tb_company co ON co.pk_company = c.fk_company
    WHERE c.pk_contact = v_pk
);
```

**Timeline Adjustment**:
- Original: Week 3 focus
- **New**: Week 3-4 (extra time for composite type integration)
- **Benefit**: Type safety worth the extra time

---

### 🟣 Team D: FraiseQL Metadata Generator + Impact Documentation (Week 5-6)

**Status**: Not Started

**Major Simplification**: Composite types already have annotations, less work needed!

#### Phase Plan

**Phase 1: FraiseQL Mutation Annotations (Week 5, Days 1-2)**

Generate `@fraiseql:mutation` comments:

```sql
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
   }';
```

**Simplified from original plan**:
- ❌ Don't need to define MutationImpactMetadata GraphQL type (Team B did it!)
- ❌ Don't need custom type registry (composite types work!)
- ✅ Just reference the type name in `metadata_mapping`

**Phase 2: Static Impact Metadata File (Week 5, Days 3-5)**

Generate `mutation-impacts.json` for frontend build-time consumption:

```json
{
  "version": "1.0.0",
  "mutations": {
    "qualifyLead": {
      "description": "Qualifies a lead by updating their status",
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
            "collection": "createdNotifications"
          }
        ],
        "cacheInvalidations": [
          {
            "query": "contacts",
            "filter": {"status": "lead"},
            "strategy": "REFETCH",
            "reason": "Contact removed from lead list"
          }
        ],
        "optimisticUpdateSafe": true,
        "estimatedDuration": 150
      }
    }
  }
}
```

**Phase 3: TypeScript Type Definitions (Week 6, Days 1-2)**

Generate `mutation-impacts.d.ts`:

```typescript
export const MUTATION_IMPACTS: {
  qualifyLead: {
    description: string;
    impact: {
      primary: EntityImpact;
      sideEffects: EntityImpact[];
      cacheInvalidations: CacheInvalidation[];
      optimisticUpdateSafe: boolean;
    };
  };
  // ... other mutations
};
```

**Phase 4: Documentation (Week 6, Days 3-5)**

Generate `docs/mutations.md` with human-readable impact documentation.

**Timeline Adjustment**:
- Original: Week 5 focus
- **New**: Week 5-6 (composite types simplified backend, but frontend codegen is new scope)

---

### 🔴 Team E: CLI & Orchestration + Frontend Codegen (Week 7-8)

**Status**: Not Started

**Enhanced Scope**: Frontend codegen + FraiseQL integration testing

#### Phase Plan

**Phase 1: Core CLI (Week 7, Days 1-3)**

```bash
# Basic generation
specql generate entities/contact.yaml

# With impact metadata
specql generate entities/*.yaml --with-impacts

# Frontend codegen
specql generate entities/*.yaml --with-impacts --output-frontend=../frontend/src/generated
```

**Phase 2: Validation Commands (Week 7, Days 4-5)**

```bash
# Validate SpecQL syntax
specql validate entities/*.yaml --check-impacts

# Validate runtime impacts match declarations
specql validate-impacts --database-url=postgres://localhost/mydb
```

**Phase 3: Frontend Codegen (Week 8, Days 1-3)**

**NEW: Generate pre-configured Apollo hooks**

```typescript
// generated/mutations.ts

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
            impact.impact.cacheInvalidations
                .filter(i => i.strategy === 'EVICT')
                .forEach(i => cache.evict({ fieldName: i.query }));

            options?.update?.(cache, result);
        }
    });
}
```

**Phase 4: FraiseQL Integration Testing (Week 8, Days 4-5)**

Test with actual FraiseQL v1.4.0:
- ✅ Composite types discovered correctly
- ✅ `updatedFields` appears in GraphQL
- ✅ Selection filtering works
- ✅ `_meta` field properly typed
- ✅ Frontend hooks work end-to-end

---

## New: Week 2 - Composite Type Testing

**Before Team C starts**, we need to validate FraiseQL's composite type approach works.

### Test Plan (Week 2, 1-2 hours)

```sql
-- 1. Create test schema
CREATE SCHEMA mutation_metadata;

CREATE TYPE mutation_metadata.entity_impact AS (
    entity_type TEXT,
    operation TEXT,
    modified_fields TEXT[]
);

CREATE TYPE mutation_metadata.mutation_impact_metadata AS (
    primary_entity mutation_metadata.entity_impact,
    actual_side_effects mutation_metadata.entity_impact[]
);

COMMENT ON TYPE mutation_metadata.mutation_impact_metadata IS
  '@fraiseql:type name=MutationImpactMetadata';

-- 2. Create test mutation
CREATE FUNCTION public.test_mutation()
RETURNS mutation_result AS $$
DECLARE
    v_result mutation_result;
    v_meta mutation_metadata.mutation_impact_metadata;
BEGIN
    v_meta.primary_entity := ('Contact', 'UPDATE', ARRAY['status']);

    v_result.status := 'success';
    v_result.message := 'Test';
    v_result.updated_fields := ARRAY['status'];
    v_result.object_data := '{"id": "123"}'::jsonb;
    v_result.extra_metadata := jsonb_build_object('_meta', to_jsonb(v_meta));

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.test_mutation IS
  '@fraiseql:mutation
   name=testMutation
   metadata_mapping={"_meta": "MutationImpactMetadata"}';
```

**Expected Result**:

```graphql
# FraiseQL should generate:
type MutationImpactMetadata {
  primaryEntity: EntityImpact!
  actualSideEffects: [EntityImpact!]!
}

type EntityImpact {
  entityType: String!
  operation: String!
  modifiedFields: [String!]!
}

type TestMutationSuccess {
  status: String!
  message: String!
  _meta: MutationImpactMetadata!
}
```

**Test Cases**:
1. ✅ Type generation works
2. ✅ `_meta` field appears in success type
3. ✅ JSONB → GraphQL mapping is correct
4. ✅ Can query `_meta.primaryEntity.entityType`

**If This Fails**:
- Report to FraiseQL team
- They'll implement custom type registry in v1.4.0
- We adjust Team C to use temporary `JSON` scalar

**Timeline**: Week 2, Day 1-2 (parallel with Team B starting)

---

## Updated Timeline with FraiseQL Sync Points

### Week 1 (Current)
- ✅ Team A: SpecQL Parser (90% → 100%)

### Week 2
- 🆕 **Day 1-2**: Test composite type approach (blocking Team C)
- Team B: Schema Generator + `mutation_metadata` schema
- **FraiseQL**: v1.4.0 development starts

### Week 3
- Team B: Finish schema generation
- Team C: Start action compiler (basic functions)
- **FraiseQL**: v1.4.0 beta available ✅
- **Sync Point**: Verify `updatedFields` exposure works

### Week 4
- Team C: Complete action compiler (with `_meta`)
- **FraiseQL**: v1.4.0 released ✅
- **Sync Point**: All features available, start final integration testing

### Week 5-6
- Team D: FraiseQL metadata + static impact files
- **FraiseQL**: Documentation + example project available
- **Sync Point**: Reference FraiseQL examples

### Week 7-8
- Team E: CLI + frontend codegen
- **FraiseQL**: v1.5.0 planning (if needed)
- **Sync Point**: Full end-to-end testing

### Week 9-10
- Integration testing
- Production readiness
- **FraiseQL**: Showcase SpecQL + FraiseQL integration

---

## Collaboration with FraiseQL Team

### Immediate Actions (This Week)

**Our Side**:
- [ ] Test composite type approach (Week 2, Day 1-2)
- [ ] Provide 3-5 real-world mutation patterns for their tests
- [ ] Review v1.4.0 implementation plan
- [ ] Set up communication channel (GitHub issues + weekly sync?)

**FraiseQL Side**:
- [ ] Create GitHub issues for 3 enhancements
- [ ] Spike composite type mapping test
- [ ] Review selection_filter.py
- [ ] Set up test database for SpecQL integration

### Weekly Syncs (Proposed)

**Week 2-4**:
- Share: Composite type test results
- Share: Real-world mutation patterns
- Receive: FraiseQL v1.4.0 beta access

**Week 5-6**:
- Share: Integration feedback
- Share: Performance benchmarks
- Receive: FraiseQL documentation + examples

**Week 7-8**:
- Share: End-to-end test results
- Share: Frontend developer feedback
- Jointly: Plan public showcase

---

## Key Decisions Made

### 1. Use Composite Types (Not Custom Types)

**Decision**: Generate PostgreSQL composite types for all metadata

**Rationale**:
- ✅ FraiseQL already supports this (80% sure, needs test)
- ✅ Type safety at database level
- ✅ No parser changes needed
- ✅ Reusable across functions

**Impact**:
- Team B: Generate `mutation_metadata` schema (one-time)
- Team C: Use composite types in `DECLARE` blocks
- Team D: Just reference types in annotations

### 2. One-Time Metadata Schema

**Decision**: Single `mutation_metadata` schema shared across all functions

**Rationale**:
- ✅ DRY (don't repeat type definitions)
- ✅ Consistent across all mutations
- ✅ Easy to version (add new types for v2)

**Impact**:
- Team B generates this ONCE in migration `000_mutation_metadata.sql`
- All other migrations reference these types

### 3. Wait for FraiseQL v1.4.0 for Production

**Decision**: Don't ship to production until FraiseQL v1.4.0 is released

**Rationale**:
- ✅ Get `updatedFields` exposure
- ✅ Get selection filter (30-50% bandwidth savings)
- ✅ Avoid workarounds that we'd have to remove later

**Impact**:
- Week 4: Can start final integration testing
- Week 8: Production-ready with all features

### 4. Frontend Codegen is Team E Responsibility

**Decision**: SpecQL generator owns frontend codegen (not FraiseQL)

**Rationale**:
- ✅ We control the impact metadata format
- ✅ Can customize for our use cases
- ✅ FraiseQL provides GraphQL schema, we build on top

**Impact**:
- Team E scope increased (Week 7-8)
- But we get full control of developer experience

---

## Success Metrics (Updated)

### Technical Success

✅ All mutations return `mutation_result`
✅ All mutations include `_meta` with type-safe composite types
✅ FraiseQL discovers all types and mutations
✅ GraphQL schema includes `MutationImpactMetadata`
✅ `updatedFields` appears in all success types (v1.4.0)
✅ Selection filtering reduces response size by 30%+ (v1.4.0)
✅ Frontend hooks auto-configure cache invalidation
✅ 100x code leverage (20 lines YAML → 2000 lines generated)

### Integration Success

✅ Composite type approach works (tested Week 2)
✅ SpecQL → FraiseQL integration seamless
✅ No manual mapping needed
✅ Frontend developers don't read backend code
✅ Impact metadata discoverable at build-time
✅ Runtime validation works (actual vs. declared)

### Timeline Success

✅ Week 2: Composite type test passes
✅ Week 3: FraiseQL v1.4.0 beta available
✅ Week 4: FraiseQL v1.4.0 released
✅ Week 8: Production-ready integration
✅ Week 10: Public showcase

---

## Risks & Mitigations (Updated)

### Risk 1: Composite Type Mapping Doesn't Work

**Likelihood**: Low (FraiseQL team confident it works)

**Impact**: Medium (need workaround)

**Mitigation**:
- Test in Week 2 (early!)
- FraiseQL will implement custom registry if needed
- Worst case: Use `JSON` scalar temporarily

**Status**: ⏳ Will know by end of Week 2

### Risk 2: FraiseQL v1.4.0 Delayed

**Likelihood**: Medium (software timelines slip)

**Impact**: Low (can continue without it)

**Mitigation**:
- We can work with v1.3.x for development
- Just won't get `updatedFields` and selection filter yet
- Adjust timeline if needed (shift Week 8 milestone)

**Status**: ✅ Monitoring FraiseQL progress

### Risk 3: Selection Filter Edge Cases

**Likelihood**: Medium (complex feature)

**Impact**: Low (feature flag allows disable)

**Mitigation**:
- Provide real-world test cases to FraiseQL team
- Test with our queries in Week 3-4
- Report issues early

**Status**: ✅ FraiseQL wants our test cases

---

## Summary of Changes from Original Plan

### What Stayed the Same

✅ Overall architecture (SpecQL → PostgreSQL → FraiseQL → GraphQL)
✅ Team structure (A, B, C, D, E)
✅ Timeline (10 weeks)
✅ 100x code leverage goal

### What Changed

**Team B**: Added `mutation_metadata` schema generation (one-time)

**Team C**: Use composite types instead of manual JSONB construction

**Team D**: Simplified (composite types already annotated by Team B)

**Team E**: Added frontend codegen scope

**New**: Week 2 composite type testing (blocking test)

**New**: Sync points with FraiseQL team

### What Improved

✅ **Type safety**: Composite types give compile-time checks
✅ **Clarity**: Clear pattern from FraiseQL team
✅ **Less risk**: Test composite types early (Week 2)
✅ **Better DX**: FraiseQL v1.4.0 features aligned
✅ **Support**: FraiseQL team actively helping

---

## Next Steps

### This Week (Week 1)

- [ ] Finish Team A (SpecQL Parser) to 100%
- [ ] Review this updated plan
- [ ] Prepare composite type test for Week 2
- [ ] Open GitHub issues on FraiseQL repo

### Week 2

- [ ] **Day 1-2**: Test composite type approach (CRITICAL)
- [ ] Start Team B (Schema Generator)
- [ ] Generate `mutation_metadata` schema
- [ ] Report composite type test results to FraiseQL

### Week 3

- [ ] Access FraiseQL v1.4.0 beta
- [ ] Start Team C with real `mutation_result` functions
- [ ] Test `updatedFields` exposure
- [ ] Provide feedback to FraiseQL

---

**Updated**: 2025-11-08 post FraiseQL response
**Status**: Plan refined, ready to execute
**Next Milestone**: Composite type test (Week 2)
