# Automatic GraphQL Cascade Support

## Overview

SpecQL automatically generates GraphQL Cascade data for all actions with impact metadata.
This enables FraiseQL to automatically update GraphQL client caches without manual configuration.

## How It Works

When you define an action with impact metadata:

```yaml
entity: Post
actions:
  - name: create_post
    steps:
      - insert: Post
    impact:
      primary:
        entity: Post
        operation: CREATE
        fields: [title, content]
```

SpecQL automatically generates SQL that includes cascade data in `mutation_result.extra_metadata._cascade`.

## Generated Structure

```json
{
  "extra_metadata": {
    "_cascade": {
      "updated": [
        {
          "__typename": "Post",
          "id": "123e4567-...",
          "operation": "CREATED",
          "entity": { ... full post data ... }
        }
      ],
      "deleted": [],
      "invalidations": [],
      "metadata": {
        "timestamp": "2025-01-15T10:30:00Z",
        "affectedCount": 1
      }
    },
    "_meta": { ... impact metadata ... }
  }
}
```

## Benefits

- **Zero Configuration**: Works automatically for all actions with impact metadata
- **Always Consistent**: Can't forget to enable cascade
- **Type-Safe**: Uses PostgreSQL composite types
- **Performance**: Native PostgreSQL operations
- **FraiseQL Integration**: Perfect for GraphQL cache updates

## Configuration Options

### Application-Wide Configuration

```yaml
# specql.config.yaml (applies to all entities/actions)
cascade:
  enabled: true              # Default: true
  include_full_entities: true  # Include complete entity data
  include_deleted: true      # Include deleted entities
```

### Per-Action Configuration

```yaml
entity: Post
actions:
  - name: create_post
    steps:
      - insert: Post
    impact:
      primary:
        entity: Post
        operation: CREATE

    # Optional: Override cascade behavior for this action
    cascade:
      enabled: true           # Override: enable/disable for this action
      include_entities: [Post, User]  # Only these entities in cascade
      exclude_entities: []    # Exclude specific entities
      include_full_data: true # Include complete entity objects
```

### Minimal (Zero Config)

```yaml
# No cascade configuration needed!
entity: Post
actions:
  - name: create_post
    impact: { ... }
    # ← Cascade automatically generated from impact
```

## Examples

See `examples/cascade_*.yaml` for complete examples.

## Technical Details

### PostgreSQL Helper Functions

SpecQL generates these helper functions in the `app` schema:

- `app.cascade_entity()` - Builds cascade entity with full data from table view
- `app.cascade_deleted()` - Builds deleted entity (ID only)

### Cascade Data Flow

1. Action compiler detects impact metadata
2. Declares cascade arrays: `v_cascade_entities`, `v_cascade_deleted`
3. Builds cascade entities from primary impact and side effects
4. Integrates cascade data into `mutation_result.extra_metadata._cascade`
5. FraiseQL reads cascade data to update GraphQL client caches

### Performance

- Native PostgreSQL operations (no external calls)
- Minimal overhead (< 10ms per mutation)
- Scales with existing impact metadata processing