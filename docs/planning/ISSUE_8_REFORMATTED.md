# Issue #8: GraphQL Cascade Support via extra_metadata (Reformatted)

## Summary

Request to enhance SpecQL's SQL function generation to include **GraphQL Cascade** support within the `extra_metadata` field of the `mutation_result` type. This would enable FraiseQL mutations to return information about all entities affected by a mutation, allowing GraphQL clients to automatically update their caches.

**Key Insight**: SpecQL already tracks all mutations via `ActionImpact` metadata, so we can **automatically generate cascade data** without any YAML configuration!

---

<details>
<summary>📖 Background & Motivation</summary>

## Background

FraiseQL is implementing a GraphQL Cascade feature that helps clients (Apollo, Relay, URQL) automatically update their caches when mutations have side effects. The feature works by returning metadata about all entities created, updated, or deleted as part of a mutation.

**Related Documentation**: https://github.com/fraiseql/fraiseql (see `docs/planning/graphql-cascade-simplified-approach.md`)

## Current SpecQL Structure

SpecQL already has the perfect foundation for this feature:

```sql
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB  -- ← Perfect for cascade data!
);
```

The `extra_metadata` JSONB field currently stores:
- Impact metadata (`_meta`)
- Side effect collections
- Cache invalidation hints

## Why This Matters

SpecQL already has an `ActionImpact` system that tracks:
- **Primary entity**: The main entity being created/updated/deleted
- **Side effects**: Secondary entities affected by the mutation
- **Cache invalidations**: What GraphQL queries should be invalidated

This means **we can automatically generate cascade data** from existing impact metadata!

</details>

---

<details>
<summary>🎯 Proposed Solution: Automatic Cascade Generation</summary>

## Automatic Cascade (Zero Configuration)

Instead of requiring users to configure cascade in YAML, we can **automatically generate it** from existing impact metadata.

### Example: Existing YAML (No Changes Needed!)

```yaml
entity: Post
schema: blog
actions:
  - name: create_post
    steps:
      - insert: Post
      - update: User SET post_count = post_count + 1

    impact:  # Already exists in SpecQL!
      primary:
        entity: Post
        operation: CREATE
        fields: [title, content]
      side_effects:
        - entity: User
          operation: UPDATE
          fields: [post_count]
```

### Generated SQL (Automatic Cascade!)

```sql
CREATE OR REPLACE FUNCTION blog.fn_create_post(input jsonb)
RETURNS app.mutation_result AS $$
DECLARE
    v_result app.mutation_result;
    v_post_id uuid;
    v_user_id uuid;
    v_meta mutation_metadata.mutation_impact_metadata;
    v_cascade_entities JSONB[];  -- ← NEW: Auto-generated!
    v_cascade_deleted JSONB[];   -- ← NEW: Auto-generated!
BEGIN
    -- Mutation logic...
    INSERT INTO blog.tb_post (title, content, author_id)
    VALUES (input->>'title', input->>'content', (input->>'author_id')::uuid)
    RETURNING id INTO v_post_id;

    v_user_id := (input->>'author_id')::uuid;
    UPDATE blog.tb_user
    SET post_count = post_count + 1
    WHERE id = v_user_id;

    -- Build cascade automatically from impact metadata
    v_cascade_entities := ARRAY[
        -- Primary entity
        app.cascade_entity('Post', v_post_id, 'CREATED', 'blog', 'tv_post'),
        -- Side effect
        app.cascade_entity('User', v_user_id, 'UPDATED', 'blog', 'tv_user')
    ];

    -- Build result with cascade
    v_result.extra_metadata := jsonb_build_object(
        '_cascade', jsonb_build_object(
            'updated', (SELECT jsonb_agg(e) FROM unnest(v_cascade_entities) e),
            'deleted', '[]'::jsonb,
            'invalidations', to_jsonb(v_meta.cache_invalidations),
            'metadata', jsonb_build_object(
                'timestamp', now(),
                'affectedCount', array_length(v_cascade_entities, 1)
            )
        ),
        '_meta', to_jsonb(v_meta)  -- Existing metadata still works
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

### Result JSON

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "success",
  "extra_metadata": {
    "_cascade": {
      "updated": [
        {
          "__typename": "Post",
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "operation": "CREATED",
          "entity": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Hello World",
            "content": "...",
            "author": { "name": "John", "email": "john@example.com" }
          }
        },
        {
          "__typename": "User",
          "id": "456e4567-e89b-12d3-a456-426614174001",
          "operation": "UPDATED",
          "entity": {
            "id": "456e4567-e89b-12d3-a456-426614174001",
            "name": "John",
            "post_count": 42
          }
        }
      ],
      "deleted": [],
      "invalidations": [],
      "metadata": {
        "timestamp": "2025-01-15T10:30:00Z",
        "affectedCount": 2
      }
    },
    "_meta": { /* existing impact metadata */ }
  }
}
```

</details>

---

<details>
<summary>🏗️ Cascade Data Structure Specification</summary>

## Cascade Structure Format

```typescript
interface CascadeData {
  updated: CascadeEntity[];       // Created or updated entities
  deleted: DeletedEntity[];        // Deleted entity IDs
  invalidations: QueryInvalidation[];  // Cache invalidation hints
  metadata: {
    timestamp: string;
    affectedCount: number;
  };
}

interface CascadeEntity {
  __typename: string;   // GraphQL type name
  id: string;          // Entity UUID
  operation: 'CREATED' | 'UPDATED';
  entity: object;      // Full entity data from table view
}

interface DeletedEntity {
  __typename: string;
  id: string;
  operation: 'DELETED';
}

interface QueryInvalidation {
  queryName: string;          // e.g., 'posts', 'userPosts'
  strategy: 'INVALIDATE' | 'UPDATE' | 'EVICT';
  scope: 'PREFIX' | 'EXACT';
}
```

</details>

---

<details>
<summary>🔧 Implementation Components</summary>

## PostgreSQL Helper Functions

### `app.cascade_entity()`

```sql
CREATE OR REPLACE FUNCTION app.cascade_entity(
    p_typename TEXT,
    p_id UUID,
    p_operation TEXT,
    p_schema TEXT,
    p_view_name TEXT
) RETURNS JSONB AS $$
DECLARE
    v_entity_data JSONB;
BEGIN
    -- Fetch full entity data from table view
    EXECUTE format('SELECT data FROM %I.%I WHERE id = $1', p_schema, p_view_name)
    INTO v_entity_data
    USING p_id;

    -- Fallback to table if view doesn't exist
    IF v_entity_data IS NULL THEN
        EXECUTE format('SELECT row_to_json(t.*) FROM %I.tb_%I t WHERE id = $1',
                       p_schema, lower(p_typename))
        INTO v_entity_data
        USING p_id;
    END IF;

    RETURN jsonb_build_object(
        '__typename', p_typename,
        'id', p_id,
        'operation', p_operation,
        'entity', COALESCE(v_entity_data, '{}'::jsonb)
    );
END;
$$ LANGUAGE plpgsql;
```

### `app.cascade_deleted()`

```sql
CREATE OR REPLACE FUNCTION app.cascade_deleted(
    p_typename TEXT,
    p_id UUID
) RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        '__typename', p_typename,
        'id', p_id,
        'operation', 'DELETED'
    );
END;
$$ LANGUAGE plpgsql;
```

## Code Generation Changes

### ImpactMetadataCompiler Extension

The existing `ImpactMetadataCompiler` will be extended to:
1. Declare cascade variables (`v_cascade_entities`, `v_cascade_deleted`)
2. Build cascade entities from `ActionImpact.primary`
3. Build cascade entities from `ActionImpact.side_effects`
4. Integrate `_cascade` into `extra_metadata`

### Files to Modify

- `src/generators/app_schema_generator.py` - Add helper functions
- `src/generators/actions/impact_metadata_compiler.py` - Build cascade arrays
- `src/generators/actions/step_compilers/*.py` - Verify ID tracking

</details>

---

<details>
<summary>✅ Benefits & Use Cases</summary>

## Benefits

### For FraiseQL
- **Automatic cache updates**: GraphQL clients update caches without manual config
- **Type-safe**: All cascade data from PostgreSQL views with proper structure
- **Zero overhead**: Only affects actions that already have impact metadata
- **No Python involvement**: All tracking happens in PostgreSQL

### For SpecQL Users
- **Zero configuration**: Works automatically for all actions with impact metadata
- **Declarative side effects**: Impact metadata clearly expresses affected entities
- **Better GraphQL integration**: Works seamlessly with Apollo, Relay, URQL
- **Standardized pattern**: Consistent cascade structure across all mutations
- **Performance**: Native PostgreSQL JSONB operations

## Use Cases

### 1. Blog Post Creation
Creating a post updates author stats → cascade returns both Post and User

### 2. Order Placement
Creating an order:
- Creates Order entity
- Updates Product inventory
- Updates User order_count
- Creates OrderItems

→ Cascade returns all 4 entity types

### 3. User Deletion
Soft-deleting a user:
- Marks User as deleted
- Marks all Posts as deleted
- Marks all Comments as deleted

→ Cascade returns User + all affected entities

### 4. Multi-Tenant Operations
Actions affecting multiple organizations → cascade helps invalidate the right caches per tenant

</details>

---

<details>
<summary>📅 Implementation Timeline</summary>

## Phased TDD Implementation Plan

**Total Duration**: 3-5 days

### Phase 1: PostgreSQL Helper Functions (1 day)
- Create `app.cascade_entity()` and `app.cascade_deleted()`
- Integrate into `AppSchemaGenerator`
- Integration tests

### Phase 2: Extend ImpactMetadataCompiler (1-2 days)
- Declare cascade variables
- Build cascade from primary impact
- Build cascade from side effects
- Integrate into `extra_metadata`

### Phase 3: Verify Step Compilers (1 day)
- Ensure INSERT steps capture entity IDs
- Verify UPDATE/DELETE steps
- Multi-step action tests

### Phase 4: E2E Integration (1 day)
- Complete flow test
- Side effects tests
- Backward compatibility tests

### Phase 5: Documentation (0.5 days)
- Feature documentation
- Examples
- CHANGELOG

**Detailed Plan**: See `docs/planning/GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md`

</details>

---

<details>
<summary>🔄 Comparison with Original Proposal</summary>

## Original Proposal (Issue)

- Explicit `cascade:` configuration in YAML
- Multiple implementation options (auto, explicit, helpers)
- User chooses when to enable cascade
- 7-10 days implementation

## Revised Proposal (Automatic)

- **Zero configuration** - works automatically
- Leverages existing `ActionImpact` metadata
- Always enabled for actions with impact metadata
- **3-5 days implementation**

## Why Automatic is Better

1. **Simpler**: No new YAML syntax, no parser changes
2. **Consistent**: Can't forget to enable it
3. **Leverages existing work**: Uses `ActionImpact` system
4. **Faster**: Shorter implementation timeline
5. **Better UX**: Just works without thinking about it

</details>

---

## Compatibility

- **Backward compatible**: Actions without impact work unchanged
- **Optional feature**: Only affects actions with impact metadata
- **No breaking changes**: Just adds data to `extra_metadata`
- **FraiseQL integration**: FraiseQL reads `_cascade` from `extra_metadata`

---

## Questions

1. ✅ **Should cascade be automatic?** - YES, leverage existing impact metadata
2. ✅ **Helper functions needed?** - YES, `cascade_entity()` and `cascade_deleted()`
3. ✅ **Default behavior?** - Automatic for all actions with impact metadata
4. ⏳ **Performance considerations?** - Need to benchmark (expect < 10ms overhead)

---

## Next Steps

1. Review and approve automatic cascade approach
2. Begin Phase 1 implementation (PostgreSQL helpers)
3. Follow TDD methodology with RED/GREEN/REFACTOR/QA cycles
4. Test with FraiseQL integration

---

**Labels**: enhancement, feature-request, fraiseql-integration
**Priority**: Medium-High
**Complexity**: Medium (reduced from original)
**Implementation Plan**: [docs/planning/GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md](../planning/GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md)
