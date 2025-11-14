# Reply to Issue #8: Automatic Cascade Implementation

## 🎯 Great Idea! Here's How We'll Implement It

Thanks for this excellent feature request! After analyzing SpecQL's architecture, we have **great news**: we can implement this **even better** than originally proposed.

### Key Insight: Zero Configuration Required! 🎁

SpecQL already tracks all mutations via the `ActionImpact` metadata system:
- Primary entity (CREATE/UPDATE/DELETE)
- Side effects (secondary entity mutations)
- Cache invalidations

**We can automatically generate cascade data from this existing metadata** - no YAML configuration needed!

---

<details>
<summary>✨ Automatic Cascade: How It Works</summary>

## No YAML Changes Needed

Your existing actions already work:

```yaml
entity: Post
actions:
  - name: create_post
    steps:
      - insert: Post
      - update: User SET post_count = post_count + 1

    impact:  # Already exists!
      primary:
        entity: Post
        operation: CREATE
      side_effects:
        - entity: User
          operation: UPDATE
          fields: [post_count]
```

## Automatic Cascade Generation

SpecQL will **automatically** generate:

```sql
-- Cascade variables (automatic!)
v_cascade_entities JSONB[];
v_cascade_deleted JSONB[];

-- Build cascade from impact metadata (automatic!)
v_cascade_entities := ARRAY[
    app.cascade_entity('Post', v_post_id, 'CREATED', 'blog', 'tv_post'),
    app.cascade_entity('User', v_user_id, 'UPDATED', 'blog', 'tv_user')
];

-- Include in extra_metadata (automatic!)
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
    '_meta', to_jsonb(v_meta)
);
```

## Result: Perfect FraiseQL Integration

```json
{
  "extra_metadata": {
    "_cascade": {
      "updated": [
        {
          "__typename": "Post",
          "id": "123e4567-...",
          "operation": "CREATED",
          "entity": { "title": "Hello World", ... }
        },
        {
          "__typename": "User",
          "id": "456e4567-...",
          "operation": "UPDATED",
          "entity": { "post_count": 42, ... }
        }
      ],
      "deleted": [],
      "invalidations": [],
      "metadata": {
        "timestamp": "2025-01-15T10:30:00Z",
        "affectedCount": 2
      }
    },
    "_meta": { ... }
  }
}
```

</details>

---

<details>
<summary>📋 Implementation Plan (3-5 days)</summary>

## Phased TDD Approach

We'll follow a disciplined TDD methodology with RED/GREEN/REFACTOR/QA cycles:

### Phase 1: PostgreSQL Helper Functions (1 day)
- Create `app.cascade_entity(typename, id, operation, schema, view)`
- Create `app.cascade_deleted(typename, id)`
- Integration into `AppSchemaGenerator`

### Phase 2: Extend ImpactMetadataCompiler (1-2 days)
- Declare cascade variables when impact exists
- Build cascade array from primary impact
- Build cascade array from side effects
- Integrate `_cascade` into `extra_metadata`

### Phase 3: Verify Step Compilers (1 day)
- Ensure INSERT steps capture entity IDs
- Verify UPDATE/DELETE steps track IDs
- Handle multi-step actions

### Phase 4: E2E Integration Testing (1 day)
- Complete flow test with PostgreSQL
- Test with side effects
- Backward compatibility verification

### Phase 5: Documentation (0.5 days)
- Feature documentation
- Examples
- CHANGELOG entry

**Detailed Plan**: [docs/planning/GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md](https://github.com/fraiseql/specql/blob/main/docs/planning/GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md)

</details>

---

<details>
<summary>🎁 Benefits of Automatic Approach</summary>

## Advantages Over Original Proposal

| Original Proposal | Automatic Approach |
|------------------|-------------------|
| Explicit `cascade:` config | **Zero configuration** |
| User must opt-in | **Always works** |
| Multiple options to choose | **One simple way** |
| 7-10 days | **3-5 days** |
| Can forget to enable | **Can't forget** |

## Benefits

✅ **Zero Configuration**: Works automatically for all actions with impact metadata
✅ **Always Consistent**: Can't forget to enable cascade
✅ **Type-Safe**: Uses PostgreSQL composite types
✅ **Backward Compatible**: Existing actions get cascade for free
✅ **Faster Implementation**: Leverages existing `ActionImpact` system
✅ **Better UX**: Just works without thinking about it

</details>

---

<details>
<summary>🔧 Technical Details</summary>

## PostgreSQL Helper Functions

```sql
-- Build cascade entity with full data from table view
CREATE OR REPLACE FUNCTION app.cascade_entity(
    p_typename TEXT,
    p_id UUID,
    p_operation TEXT,
    p_schema TEXT,
    p_view_name TEXT
) RETURNS JSONB;

-- Build deleted entity marker (no full data)
CREATE OR REPLACE FUNCTION app.cascade_deleted(
    p_typename TEXT,
    p_id UUID
) RETURNS JSONB;
```

## Code Generation

### Files to Modify
- `src/generators/app_schema_generator.py` - Add helper functions
- `src/generators/actions/impact_metadata_compiler.py` - Build cascade arrays

### Files to Create
- `tests/unit/generators/test_app_schema_cascade.py`
- `tests/integration/test_automatic_cascade_e2e.py`
- `docs/features/AUTOMATIC_GRAPHQL_CASCADE.md`
- `examples/cascade_basic.yaml`

## Type Safety

Uses PostgreSQL composite types (like existing `_meta`):
- Compile-time type checking
- No runtime type errors
- Clean JSONB conversion

</details>

---

<details>
<summary>🧪 Testing Strategy</summary>

## Comprehensive Test Coverage

### Unit Tests
- Helper function generation
- Cascade array building
- Metadata integration
- Variable declarations

### Integration Tests
- E2E flow with real PostgreSQL
- Primary entity cascade
- Side effects cascade
- DELETE operations
- Multi-step actions
- Backward compatibility

### Performance Tests
- Benchmark cascade overhead (target: < 10ms)
- Large entity sets
- Multiple side effects

### Acceptance Criteria
- [ ] All tests pass (90%+ coverage)
- [ ] Zero breaking changes
- [ ] Performance overhead < 10ms
- [ ] FraiseQL integration verified
- [ ] Documentation complete

</details>

---

<details>
<summary>📅 Timeline & Next Steps</summary>

## Rollout Schedule

### Week 1
- **Day 1**: Phase 1 (Helper functions)
- **Day 2-3**: Phase 2 (ImpactMetadataCompiler)
- **Day 4**: Phase 3 (Verify step compilers)
- **Day 4-5**: Phase 4 (E2E integration)
- **Day 5**: Phase 5 (Documentation)

## Next Steps

1. ✅ Review and approve automatic cascade approach
2. ⏳ Begin Phase 1 implementation
3. ⏳ Follow TDD methodology
4. ⏳ Test with FraiseQL integration

## Questions?

Feel free to ask about:
- Implementation details
- Performance considerations
- FraiseQL integration specifics
- Timeline adjustments

</details>

---

## Summary

**Automatic cascade is better than opt-in!** By leveraging SpecQL's existing `ActionImpact` metadata, we can provide cascade support with:

- ✨ **Zero configuration**
- 🚀 **3-5 days** implementation (vs 7-10)
- ✅ **Always consistent**
- 🎯 **Perfect FraiseQL integration**

We'll start with Phase 1 this week and have this feature ready for production shortly!

---

**Implementation Status**: Ready to begin
**Full Plan**: [GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md](https://github.com/fraiseql/specql/blob/main/docs/planning/GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md)
