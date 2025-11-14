# Complete System Synthesis: GraphQL Cascade + Audit Trail + CDC

**Purpose**: Comprehensive explanation of how SpecQL's mutation tracking, GraphQL cascade, audit trail, and CDC outbox patterns work together as a unified system.

**Audience**: Developers who want to deeply understand the architecture

**Last Updated**: 2025-01-15

---

## 🎯 Table of Contents

1. [The Big Picture: What Problem Are We Solving?](#the-big-picture)
2. [Core Concepts](#core-concepts)
3. [System Architecture Overview](#system-architecture-overview)
4. [Component Deep Dive](#component-deep-dive)
5. [Data Flow: From YAML to Events](#data-flow)
6. [Integration Points](#integration-points)
7. [Use Cases & Examples](#use-cases--examples)
8. [Implementation Phases](#implementation-phases)
9. [FAQ](#faq)

---

## The Big Picture: What Problem Are We Solving?

### The Challenge

When you build modern applications, **mutations affect multiple entities**:

```
User clicks "Create Post"
    ↓
1. Post is created ✅
2. Author's post_count is incremented ✅
3. User's activity feed is updated ✅
4. Notification is sent to followers ✅
5. Analytics counter is incremented ✅
```

**The Problems**:
1. **GraphQL Clients** don't know what to update in their cache (just Post? User too?)
2. **Audit trails** only show individual table changes, not the complete picture
3. **Microservices** don't get notified about side effects
4. **Debugging** is hard: "Why did this counter change?"
5. **Compliance** needs: "Show me everything that changed when this happened"

### The Solution: Three Complementary Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                     SpecQL Action with Impact                    │
│                                                                   │
│  impact:                                                          │
│    primary: { entity: Post, operation: CREATE }                  │
│    side_effects:                                                  │
│      - { entity: User, operation: UPDATE }                        │
│      - { entity: Notification, operation: CREATE }                │
└───────────────────────┬───────────────────────────────────────────┘
                        │
            Single Source of Truth (ActionImpact metadata)
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌───────────────┐ ┌──────────────┐ ┌────────────────┐
│   PATTERN 1   │ │  PATTERN 2   │ │   PATTERN 3    │
│ GraphQL       │ │ Audit Trail  │ │ CDC Outbox     │
│ Cascade       │ │ Integration  │ │ Pattern        │
└───────────────┘ └──────────────┘ └────────────────┘
        ↓               ↓               ↓
┌───────────────┐ ┌──────────────┐ ┌────────────────┐
│ Apollo Client │ │ Audit Query  │ │ Kafka Events   │
│ Cache Update  │ │ & Compliance │ │ → Microservices│
└───────────────┘ └──────────────┘ └────────────────┘
```

**Key Insight**: **One metadata structure (`ActionImpact`) powers all three patterns!**

---

## Core Concepts

### Concept 1: Impact Metadata (The Foundation)

**What is it?** A declaration of what a mutation affects.

**Where does it live?** In your SpecQL YAML:

```yaml
entity: Post
actions:
  - name: create_post
    steps:
      - insert: Post
      - update: User SET post_count = post_count + 1

    impact:  # ← THIS IS THE FOUNDATION
      primary:
        entity: Post
        operation: CREATE
        fields: [id, title, content, author]

      side_effects:
        - entity: User
          operation: UPDATE
          fields: [post_count]

      cache_invalidations:
        - query: posts
          strategy: INVALIDATE
```

**Why is it powerful?**
- ✅ **Single source of truth** for what a mutation does
- ✅ **Declarative** - you describe effects, SpecQL generates code
- ✅ **Type-safe** - PostgreSQL composite types validate at compile time
- ✅ **Powers multiple systems** from one definition

---

### Concept 2: The Trinity Pattern (SpecQL Convention)

Every SpecQL entity uses **three identifiers**:

```sql
CREATE TABLE blog.tb_post (
    pk_post INTEGER PRIMARY KEY,        -- 1. Internal database key
    id UUID NOT NULL UNIQUE,            -- 2. External API identifier
    identifier TEXT NOT NULL UNIQUE     -- 3. Human-readable identifier
);
```

**Why this matters for cascade**:
- GraphQL APIs use `id` (UUID)
- Internal operations use `pk_post` (INTEGER for performance)
- Cascade needs to convert: UUID → INTEGER → fetch data → UUID for response

**Helper Functions**:
```sql
SELECT blog.post_pk('123e4567-...')        → Returns INTEGER pk
SELECT blog.post_id(42)                     → Returns UUID id
SELECT blog.post_identifier(42)             → Returns TEXT identifier
```

---

### Concept 3: Table Views (Denormalized GraphQL-Ready Data)

SpecQL generates **table views** for entities with foreign keys:

```sql
-- Table (normalized)
CREATE TABLE blog.tb_post (
    pk_post INTEGER PRIMARY KEY,
    id UUID,
    title TEXT,
    fk_author INTEGER REFERENCES blog.tb_user(pk_user)
);

-- Table View (denormalized, GraphQL-ready)
CREATE VIEW blog.tv_post AS
SELECT
    p.id,
    jsonb_build_object(
        'id', p.id,
        'title', p.title,
        'author', jsonb_build_object(  -- ← Nested relationship!
            'id', u.id,
            'name', u.name,
            'email', u.email
        )
    ) as data
FROM blog.tb_post p
LEFT JOIN blog.tb_user u ON u.pk_user = p.fk_author;
```

**Why this matters for cascade**:
- Cascade returns **complete entity data** including relationships
- No N+1 queries needed
- GraphQL clients get exactly what they need

---

### Concept 4: mutation_result Type (The Response Container)

Every SpecQL action returns this structure:

```sql
CREATE TYPE app.mutation_result AS (
    id UUID,                  -- Primary entity ID
    updated_fields TEXT[],    -- Which fields changed
    status TEXT,              -- 'success' or 'error'
    message TEXT,             -- Human-readable message
    object_data JSONB,        -- Full entity data
    extra_metadata JSONB      -- ← Where cascade, audit, and CDC data live
);
```

**The `extra_metadata` structure**:

```json
{
  "extra_metadata": {
    "_cascade": {              // ← Pattern 1: GraphQL Cascade
      "updated": [...],
      "deleted": [...],
      "invalidations": [...],
      "metadata": {...}
    },
    "_meta": {                 // ← Impact metadata (existing)
      "primary_entity": {...},
      "actual_side_effects": [...],
      "cache_invalidations": [...]
    },
    "createdNotifications": [] // ← Side effect collections (existing)
  }
}
```

---

## System Architecture Overview

### Layer 1: YAML Definition (User Input)

```yaml
entity: Post
schema: blog

fields:
  title: text
  content: text
  author: ref(User)

actions:
  - name: create_post
    steps:
      - insert: Post
      - update: User SET post_count = post_count + 1

    impact:
      primary:
        entity: Post
        operation: CREATE
      side_effects:
        - entity: User
          operation: UPDATE
          fields: [post_count]

    # Optional: Audit integration
    audit:
      include_cascade: true

    # Optional: CDC integration
    cdc:
      enabled: true
      event_type: PostCreated
```

---

### Layer 2: AST Models (Internal Representation)

```python
# src/core/ast_models.py

@dataclass
class Action:
    name: str
    steps: list[ActionStep]
    impact: ActionImpact | None  # ← The key!
    cdc: CDCConfig | None

@dataclass
class ActionImpact:
    primary: EntityImpact
    side_effects: list[EntityImpact]
    cache_invalidations: list[CacheInvalidation]

@dataclass
class EntityImpact:
    entity: str              # 'Post', 'User', etc.
    operation: str           # 'CREATE', 'UPDATE', 'DELETE'
    fields: list[str]        # ['title', 'content']
    collection: str | None   # 'createdNotifications'
```

---

### Layer 3: Code Generators (SQL Generation)

```python
# The compilation pipeline:

SpecQL YAML
    ↓ (SpecQLParser)
Action AST with ActionImpact
    ↓ (ImpactMetadataCompiler)
┌─────────────────────────────────────┐
│ Generates:                           │
│ 1. v_meta (composite type)          │
│ 2. v_cascade_entities (JSONB[])     │ ← Pattern 1
│ 3. Session variables for audit      │ ← Pattern 2
│ 4. Outbox event writes              │ ← Pattern 3
└─────────────────────────────────────┘
    ↓
Complete PL/pgSQL Function
```

---

### Layer 4: Generated SQL (Runtime Execution)

**Complete Generated Function** (simplified):

```sql
CREATE OR REPLACE FUNCTION blog.fn_create_post(
    p_input JSONB,
    p_caller_id UUID DEFAULT NULL,
    p_tenant_id UUID DEFAULT NULL,
    p_trace_id TEXT DEFAULT NULL
) RETURNS app.mutation_result AS $$
DECLARE
    -- Result
    v_result app.mutation_result;

    -- Entity IDs
    v_post_id UUID;
    v_user_id UUID;

    -- Impact metadata (existing)
    v_meta mutation_metadata.mutation_impact_metadata;

    -- Cascade (Pattern 1)
    v_cascade_entities JSONB[];
    v_cascade_deleted JSONB[];
    v_cascade_data JSONB;

    -- CDC (Pattern 3)
    v_event_id UUID;
BEGIN
    -- ==========================================
    -- BUSINESS LOGIC
    -- ==========================================

    -- Parse input
    v_user_id := (p_input->>'author_id')::uuid;

    -- Insert Post
    INSERT INTO blog.tb_post (title, content, fk_author, tenant_id)
    SELECT
        p_input->>'title',
        p_input->>'content',
        blog.user_pk(v_user_id),  -- UUID → INTEGER
        p_tenant_id
    RETURNING id INTO v_post_id;

    -- Update User (side effect)
    UPDATE blog.tb_user
    SET
        post_count = post_count + 1,
        updated_at = now(),
        updated_by = p_caller_id
    WHERE id = v_user_id
      AND tenant_id = p_tenant_id;

    -- ==========================================
    -- PATTERN 1: BUILD CASCADE DATA
    -- ==========================================

    -- Build cascade entities array
    v_cascade_entities := ARRAY[
        -- Primary: Post created
        app.cascade_entity(
            'Post',              -- __typename
            v_post_id,           -- id
            'CREATED',           -- operation
            'blog',              -- schema
            'tv_post'            -- table view
        ),
        -- Side effect: User updated
        app.cascade_entity(
            'User',
            v_user_id,
            'UPDATED',
            'blog',
            'tv_user'
        )
    ];

    -- Build complete cascade structure
    v_cascade_data := jsonb_build_object(
        'updated', (SELECT jsonb_agg(e) FROM unnest(v_cascade_entities) e),
        'deleted', '[]'::jsonb,
        'invalidations', '[]'::jsonb,
        'metadata', jsonb_build_object(
            'timestamp', now(),
            'affectedCount', array_length(v_cascade_entities, 1)
        )
    );

    -- ==========================================
    -- PATTERN 2: SET AUDIT SESSION VARIABLES
    -- ==========================================

    -- Set session variables for audit triggers to capture
    PERFORM set_config('app.cascade_data', v_cascade_data::text, true);
    PERFORM set_config('app.cascade_entities', 'Post,User', true);
    PERFORM set_config('app.cascade_source', 'create_post', true);

    -- (Audit triggers will fire during INSERT/UPDATE and capture this data)

    -- ==========================================
    -- PATTERN 3: WRITE TO OUTBOX (if enabled)
    -- ==========================================

    IF p_cdc_enabled THEN  -- Configuration check
        v_event_id := app.write_outbox_event(
            'Post',                    -- aggregate_type
            v_post_id,                 -- aggregate_id
            'PostCreated',             -- event_type
            (SELECT data FROM blog.tv_post WHERE id = v_post_id),  -- payload
            jsonb_build_object(        -- metadata
                'cascade', v_cascade_data,
                'mutation', 'create_post',
                'affectedEntities', ARRAY['Post', 'User']
            ),
            p_tenant_id,               -- tenant routing
            p_trace_id,                -- distributed tracing
            gen_random_uuid()          -- correlation_id
        );
    END IF;

    -- ==========================================
    -- BUILD IMPACT METADATA (existing)
    -- ==========================================

    v_meta.primary_entity := ROW(
        'Post',
        'CREATE',
        ARRAY['id', 'title', 'content', 'author']
    )::mutation_metadata.entity_impact;

    v_meta.actual_side_effects := ARRAY[
        ROW('User', 'UPDATE', ARRAY['post_count'])::mutation_metadata.entity_impact
    ];

    -- ==========================================
    -- BUILD SUCCESS RESPONSE
    -- ==========================================

    v_result.id := v_post_id;
    v_result.status := 'success';
    v_result.message := 'Post created successfully';
    v_result.updated_fields := ARRAY['id', 'title', 'content', 'author'];

    -- Object data (from table view)
    SELECT data INTO v_result.object_data
    FROM blog.tv_post
    WHERE id = v_post_id;

    -- Extra metadata (ALL patterns combined!)
    v_result.extra_metadata := jsonb_build_object(
        '_cascade', v_cascade_data,        -- Pattern 1: GraphQL Cascade
        '_meta', to_jsonb(v_meta),         -- Existing impact metadata
        'eventId', v_event_id              -- Pattern 3: Link to CDC event
    );

    -- ==========================================
    -- CLEANUP
    -- ==========================================

    -- Clear audit session variables
    PERFORM set_config('app.cascade_data', NULL, true);
    PERFORM set_config('app.cascade_entities', NULL, true);
    PERFORM set_config('app.cascade_source', NULL, true);

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

### Layer 5: Runtime Infrastructure

#### Pattern 1: GraphQL Cascade (Immediate)

**What happens**:
1. Client calls mutation
2. Function returns with `_cascade` in `extra_metadata`
3. Apollo Client receives response
4. Cache updated with all affected entities

**Response**:
```json
{
  "data": {
    "createPost": {
      "id": "123e4567-...",
      "status": "success",
      "object_data": {
        "id": "123e4567-...",
        "title": "Hello World",
        "author": {
          "id": "456e4567-...",
          "name": "John",
          "post_count": 42
        }
      },
      "extra_metadata": {
        "_cascade": {
          "updated": [
            {
              "__typename": "Post",
              "id": "123e4567-...",
              "operation": "CREATED",
              "entity": { "title": "Hello World", "author": {...} }
            },
            {
              "__typename": "User",
              "id": "456e4567-...",
              "operation": "UPDATED",
              "entity": { "name": "John", "post_count": 42 }
            }
          ],
          "deleted": [],
          "invalidations": [],
          "metadata": {
            "timestamp": "2025-01-15T10:30:00Z",
            "affectedCount": 2
          }
        }
      }
    }
  }
}
```

**Apollo Client Integration**:
```typescript
// Apollo Client automatically updates cache for both Post and User!
import { useMutation } from '@apollo/client';

const [createPost] = useMutation(CREATE_POST, {
  update(cache, { data }) {
    const cascade = data.createPost.extra_metadata._cascade;

    // Process cascade updates
    cascade.updated.forEach(entity => {
      const typename = entity.__typename;
      const id = entity.id;

      // Write to cache
      cache.writeFragment({
        id: cache.identify({ __typename: typename, id }),
        fragment: gql`fragment _ on ${typename} { ... }`,
        data: entity.entity
      });
    });

    // Process deletions
    cascade.deleted.forEach(entity => {
      cache.evict({ id: cache.identify(entity) });
    });

    // Process invalidations
    cascade.invalidations.forEach(inv => {
      // Refetch or invalidate queries
    });
  }
});
```

---

#### Pattern 2: Audit Trail (Persistent History)

**What happens**:
1. Function sets session variables with cascade data
2. PostgreSQL triggers fire during INSERT/UPDATE/DELETE
3. Triggers read session variables
4. Audit records written with cascade context
5. Function clears session variables

**Audit Table**:
```sql
CREATE TABLE app.audit_post (
    audit_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    operation_type TEXT,                -- 'INSERT', 'UPDATE', 'DELETE'
    changed_by UUID,
    changed_at TIMESTAMPTZ,
    old_values JSONB,
    new_values JSONB,

    -- Cascade integration (NEW)
    cascade_data JSONB,                 -- Full cascade structure
    cascade_entities TEXT[],            -- ['Post', 'User']
    cascade_source TEXT                 -- 'create_post'
);
```

**Audit Query with Cascade**:
```sql
SELECT * FROM app.get_post_audit_history_with_cascade(
    '123e4567-...',  -- entity_id
    'tenant-abc'     -- tenant_id
);

-- Returns:
-- audit_id | operation | changed_at | cascade_data
-- ---------+-----------+------------+------------------
-- abc...   | INSERT    | 2025-01-15 | {
--          |           |            |   "updated": [
--          |           |            |     {"__typename": "Post", ...},
--          |           |            |     {"__typename": "User", ...}
--          |           |            |   ]
--          |           |            | }
```

**Use Cases**:
- **Compliance**: "Show me everything that changed when this post was created"
- **Debugging**: "Why did User.post_count change to 42?"
- **Replay**: Reconstruct exact state of mutation including side effects
- **Cross-entity correlation**: Find all mutations that affected User entity

---

#### Pattern 3: CDC Outbox (Async Events)

**What happens**:
1. Function writes event to `app.outbox` table
2. Debezium polls outbox table (every 1 second)
3. Events streamed to Kafka topics
4. Microservices consume events
5. Events marked as processed
6. Periodic cleanup removes old processed events

**Outbox Table**:
```sql
CREATE TABLE app.outbox (
    id UUID PRIMARY KEY,
    aggregate_type TEXT,           -- 'Post'
    aggregate_id UUID,             -- '123e4567-...'
    event_type TEXT,               -- 'PostCreated'
    event_payload JSONB,           -- Full Post data
    event_metadata JSONB,          -- Cascade + tracing
    tenant_id UUID,
    trace_id TEXT,
    correlation_id UUID,
    created_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ       -- NULL = pending
);
```

**Event in Outbox**:
```sql
SELECT * FROM app.outbox WHERE event_type = 'PostCreated' LIMIT 1;

-- id: 789e4567-...
-- aggregate_type: Post
-- aggregate_id: 123e4567-...
-- event_type: PostCreated
-- event_payload: {"id": "123...", "title": "Hello World", "author": {...}}
-- event_metadata: {
--   "cascade": {
--     "updated": [
--       {"__typename": "Post", ...},
--       {"__typename": "User", ...}
--     ]
--   },
--   "mutation": "create_post",
--   "affectedEntities": ["Post", "User"]
-- }
-- processed_at: NULL  ← Debezium will process this
```

**Kafka Topic Structure**:
```
specql.events.Post    → All Post events (PostCreated, PostUpdated, PostDeleted)
specql.events.User    → All User events
specql.events.Comment → All Comment events
```

**Microservice Consumer** (Python example):
```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'specql.events.Post',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    event = message.value

    if event['event_type'] == 'PostCreated':
        # Update search index
        elasticsearch.index(
            index='posts',
            id=event['aggregate_id'],
            body=event['event_payload']
        )

        # Update analytics
        analytics.increment('posts_created')

        # Check cascade for side effects
        cascade = event['event_metadata']['cascade']
        for entity in cascade['updated']:
            if entity['__typename'] == 'User':
                # User stats changed, update user index too
                elasticsearch.update(...)
```

**Use Cases**:
- **Search Indexing**: ElasticSearch, Algolia, etc.
- **Analytics**: Data warehouse, metrics, dashboards
- **Notifications**: Email, push notifications, webhooks
- **Caching**: Redis, CDN invalidation
- **CQRS**: Sync read models
- **Event Sourcing**: Event store, audit log

---

## Data Flow: From YAML to Events

### Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DEVELOPER WRITES YAML                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   entity: Post                                                    │
│   actions:                                                        │
│     - name: create_post                                           │
│       impact:                                                     │
│         primary: { entity: Post, operation: CREATE }              │
│         side_effects: [{ entity: User, operation: UPDATE }]       │
│                                                                   │
└───────────────────────┬───────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. SPECQL PARSER (SpecQLParser.parse())                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Action(                                                         │
│     name='create_post',                                           │
│     impact=ActionImpact(                                          │
│       primary=EntityImpact(entity='Post', operation='CREATE'),    │
│       side_effects=[EntityImpact(entity='User', ...)]             │
│     )                                                             │
│   )                                                               │
│                                                                   │
└───────────────────────┬───────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CODE GENERATORS                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ImpactMetadataCompiler:                                         │
│   • Declares v_cascade_entities                                   │
│   • Builds cascade from impact.primary + impact.side_effects      │
│   • Sets session variables for audit                              │
│   • Integrates into extra_metadata                                │
│                                                                   │
│   OutboxEventCompiler (if CDC enabled):                           │
│   • Generates app.write_outbox_event() call                       │
│   • Includes cascade in event_metadata                            │
│                                                                   │
└───────────────────────┬───────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. GENERATED SQL FUNCTION                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   CREATE FUNCTION blog.fn_create_post(...) AS $$                 │
│   DECLARE                                                         │
│     v_cascade_entities JSONB[];                                   │
│   BEGIN                                                           │
│     -- Business logic                                             │
│     INSERT INTO tb_post ...                                       │
│     UPDATE tb_user ...                                            │
│                                                                   │
│     -- Build cascade                                              │
│     v_cascade_entities := ARRAY[                                  │
│       app.cascade_entity('Post', ...),                            │
│       app.cascade_entity('User', ...)                             │
│     ];                                                            │
│                                                                   │
│     -- Set audit session vars                                     │
│     PERFORM set_config('app.cascade_data', ...)                   │
│                                                                   │
│     -- Write to outbox                                            │
│     INSERT INTO app.outbox ...                                    │
│                                                                   │
│     -- Return with cascade                                        │
│     RETURN v_result;                                              │
│   END $$;                                                         │
│                                                                   │
└───────────────────────┬───────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. RUNTIME EXECUTION (User calls mutation)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   GraphQL Client → FraiseQL → PostgreSQL                          │
│                                                                   │
│   SELECT blog.fn_create_post('{"title": "Hello"}'::jsonb)        │
│                                                                   │
└───────────────────────┬───────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬───────────────────┐
        ↓               ↓               ↓                   ↓
┌───────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ PATTERN 1     │ │ PATTERN 2    │ │ PATTERN 3    │ │ EXISTING     │
│ Cascade       │ │ Audit Trail  │ │ CDC Outbox   │ │ Impact Meta  │
└───────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        ↓               ↓               ↓                   ↓
┌───────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ extra_metadata│ │ app.audit_   │ │ app.outbox   │ │ extra_metadata│
│ ._cascade     │ │ post table   │ │ table        │ │ ._meta       │
│               │ │              │ │              │ │              │
│ {             │ │ INSERT INTO  │ │ INSERT INTO  │ │ {            │
│   updated: [  │ │ audit_post   │ │ outbox       │ │   primary:   │
│     Post,     │ │ (            │ │ (            │ │     {...}    │
│     User      │ │   cascade_   │ │   event_     │ │   side_      │
│   ]           │ │   data,      │ │   metadata:  │ │   effects:   │
│ }             │ │   ...        │ │   {cascade}  │ │     [...]    │
│               │ │ )            │ │ )            │ │ }            │
└───────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        ↓               ↓               ↓
┌───────────────┐ ┌──────────────┐ ┌──────────────┐
│ Apollo Client │ │ Compliance   │ │ Debezium     │
│ Cache Update  │ │ Queries      │ │ → Kafka      │
│               │ │              │ │ → Services   │
└───────────────┘ └──────────────┘ └──────────────┘
```

---

## Integration Points

### Integration 1: Session Variables Bridge (Pattern 2)

**Problem**: Audit triggers fire at row level, but cascade is at mutation level.

**Solution**: PostgreSQL session variables!

```sql
-- In action function:
PERFORM set_config('app.cascade_data', v_cascade_data::text, true);

-- In trigger (fires during INSERT/UPDATE):
CREATE TRIGGER audit_trigger_post ...
INSERT INTO audit_post (
    cascade_data
) VALUES (
    NULLIF(current_setting('app.cascade_data', true), '')::jsonb
);
```

**Why this works**:
- Session variables persist within a transaction
- All triggers in the transaction can read them
- Automatically cleared at transaction end
- No schema changes needed to pass data

---

### Integration 2: Outbox Event Metadata (Pattern 3)

**Problem**: Kafka events need cascade context for consumers.

**Solution**: Include cascade in `event_metadata`:

```sql
INSERT INTO app.outbox (
    event_metadata
) VALUES (
    jsonb_build_object(
        'cascade', v_cascade_data,           -- Full cascade structure
        'mutation', 'create_post',           -- Source mutation
        'affectedEntities', ARRAY['Post', 'User']  -- Quick filter
    )
);
```

**Why this works**:
- Consumers know all affected entities
- Can route events based on cascade
- Can reconstruct full mutation context
- Distributed tracing via trace_id

---

### Integration 3: Table Views for Complete Data (Pattern 1)

**Problem**: Cascade needs complete entity data including relationships.

**Solution**: Use table views:

```sql
-- Helper function uses table view
CREATE FUNCTION app.cascade_entity(
    p_typename TEXT,
    p_id UUID,
    p_view_name TEXT  -- 'tv_post'
) RETURNS JSONB AS $$
BEGIN
    -- Fetch complete denormalized data
    EXECUTE format('SELECT data FROM %I WHERE id = $1', p_view_name)
    INTO v_entity_data
    USING p_id;

    RETURN jsonb_build_object(
        '__typename', p_typename,
        'entity', v_entity_data  -- Complete nested data!
    );
END $$;
```

**Why this works**:
- One query fetches entity + relationships
- GraphQL-ready format
- No N+1 queries
- Consistent with FraiseQL API

---

## Use Cases & Examples

### Use Case 1: Blog Platform

**Scenario**: User creates a blog post

**What Happens**:
```yaml
action: create_post
impact:
  primary: Post (CREATE)
  side_effects:
    - User.post_count (UPDATE)
    - ActivityFeed (INSERT)
    - Notification (INSERT for followers)
```

**Pattern 1 (Cascade)**: Apollo Client updates cache for Post + User
**Pattern 2 (Audit)**: Admin can query "What happened when this post was created?"
**Pattern 3 (CDC)**:
- Search service indexes new post
- Analytics increments counter
- Email service sends notifications to followers

---

### Use Case 2: E-commerce Order

**Scenario**: Customer places order

**What Happens**:
```yaml
action: place_order
impact:
  primary: Order (CREATE)
  side_effects:
    - Product.inventory (UPDATE - decrement stock)
    - User.order_count (UPDATE)
    - Cart (DELETE - clear cart)
    - OrderItem (INSERT multiple)
```

**Pattern 1 (Cascade)**:
```json
{
  "_cascade": {
    "updated": [
      {"__typename": "Order", "operation": "CREATED"},
      {"__typename": "Product", "operation": "UPDATED"},  // Stock: 100 → 99
      {"__typename": "User", "operation": "UPDATED"},     // Orders: 5 → 6
      {"__typename": "OrderItem", "operation": "CREATED"},
      {"__typename": "OrderItem", "operation": "CREATED"}
    ],
    "deleted": [
      {"__typename": "CartItem", "id": "..."}
    ]
  }
}
```

**Pattern 2 (Audit)**:
```sql
-- Compliance query: "Show me all changes from order #12345"
SELECT * FROM get_order_audit_history_with_cascade('12345', 'tenant-abc');

-- Result shows: Order created, Product stock changed, User stats updated, Cart cleared
```

**Pattern 3 (CDC)**:
- Warehouse service receives `OrderCreated` event → prepares shipment
- Inventory service receives event with Product update → triggers restock if needed
- Email service receives event → sends confirmation email
- Analytics service tracks conversion

---

### Use Case 3: Multi-Tenant SaaS

**Scenario**: Admin updates organization settings

**What Happens**:
```yaml
action: update_organization_settings
impact:
  primary: Organization (UPDATE)
  side_effects:
    - User (UPDATE - all org members, feature flags)
    - Subscription (UPDATE - billing)
```

**Pattern 1 (Cascade)**:
```json
{
  "_cascade": {
    "updated": [
      {"__typename": "Organization"},
      {"__typename": "User"},      // 50 users updated
      {"__typename": "User"},      // (one entry per user)
      // ... 48 more
      {"__typename": "Subscription"}
    ],
    "metadata": {
      "affectedCount": 52,
      "tenantId": "tenant-abc"
    }
  }
}
```

**Pattern 2 (Audit)**:
- Compliance: "Show me when feature X was enabled"
- Debugging: "Why did user permissions change?"

**Pattern 3 (CDC)**:
- Cache service invalidates all user caches for this tenant
- Billing service updates subscription
- Analytics tracks feature adoption

---

## Implementation Phases

### ✅ COMPLETED: Phase 0 (Pre-existing)

**What We Had**:
- Audit trail infrastructure (`AuditGenerator`)
- Audit fields on entities
- Impact metadata system (`ActionImpact`)
- Table views generation
- Trinity pattern

**Status**: Production-ready

---

### 🚧 CURRENT: Phase 1 (GraphQL Cascade)

**Duration**: 3-5 days
**Status**: Implementation in progress

**Deliverables**:
1. PostgreSQL helper functions
   - `app.cascade_entity(typename, id, operation, schema, view)`
   - `app.cascade_deleted(typename, id)`

2. ImpactMetadataCompiler enhancements
   - Declare `v_cascade_entities`, `v_cascade_deleted`
   - Build cascade from `ActionImpact`
   - Integrate into `extra_metadata._cascade`

3. Cascade structure
   ```json
   {
     "updated": [CascadeEntity],
     "deleted": [DeletedEntity],
     "invalidations": [QueryInvalidation],
     "metadata": { timestamp, affectedCount }
   }
   ```

**Testing**:
- Unit tests for cascade compilation
- Integration tests with PostgreSQL
- E2E tests with FraiseQL

**Documentation**:
- `GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md`
- `CASCADE_CDC_INTEGRATION.md`

---

### 🔜 FUTURE: Phase 2 (Audit Trail Integration)

**Duration**: 2-3 days
**Status**: Planned

**Deliverables**:
1. Audit table schema extension
   - Add `cascade_data JSONB` column
   - Add `cascade_entities TEXT[]` column
   - Migration scripts

2. Session variable integration
   - Action functions set `app.cascade_data`
   - Triggers capture from session variables
   - Automatic cleanup

3. Enhanced audit queries
   - `get_{entity}_audit_history_with_cascade()`
   - `get_mutations_affecting_entity()`
   - Cascade audit views

4. CLI integration
   - `--with-audit-cascade` flag
   - YAML: `audit.include_cascade: true`

**Value**:
- Complete mutation history
- Compliance queries
- Debugging and replay
- Cross-entity correlation

**Documentation**:
- `CASCADE_AUDIT_CDC_PHASES_2_3.md` (Section: Phase 2)
- `AUDIT_TRAIL_CASCADE.md`

---

### 🔜 FUTURE: Phase 3 (CDC Outbox Pattern)

**Duration**: 3-5 days
**Status**: Planned (only if event-driven architecture needed)

**Deliverables**:
1. Outbox table and helpers
   - `app.outbox` table
   - `app.write_outbox_event()` function
   - Monitoring views

2. Action integration
   - Add `CDCConfig` to AST
   - `OutboxEventCompiler` generates event writes
   - Cascade in `event_metadata`

3. Debezium setup
   - Connector configuration generator
   - Docker Compose CDC stack
   - CLI commands: `specql cdc generate-config`

4. Event streaming
   - Kafka topic routing
   - Event schema
   - Consumer examples

**Value**:
- Async event streaming
- Microservices integration
- Event sourcing
- Analytics pipelines

**Documentation**:
- `CASCADE_AUDIT_CDC_PHASES_2_3.md` (Section: Phase 3)
- `CDC_OUTBOX_PATTERN.md`
- `SETTING_UP_CDC.md`

---

## FAQ

### Q1: Why do we need three patterns? Isn't one enough?

**A**: They solve different problems:

| Pattern | Problem | Solution | Latency | Persistence |
|---------|---------|----------|---------|-------------|
| **Cascade** | GraphQL cache doesn't know what to update | Return all affected entities | Immediate (sync) | No (in-memory) |
| **Audit** | Need historical record of mutations | Store cascade in audit trail | Immediate (sync) | Yes (PostgreSQL) |
| **CDC** | Microservices need async notifications | Stream events to Kafka | Eventual (async) | Yes (Kafka) |

You don't need all three! Pick what you need:
- **GraphQL-only app**: Phase 1 (Cascade) is enough
- **Need compliance**: Phase 1 + Phase 2 (Audit)
- **Microservices**: Phase 1 + Phase 3 (CDC)
- **Enterprise**: All three

---

### Q2: What's the performance impact?

**Cascade (Phase 1)**:
- Overhead: ~5-10ms per mutation
- Cost: Building JSONB arrays, fetching from table views
- Acceptable for: All applications (very low cost)

**Audit (Phase 2)**:
- Overhead: ~2-5ms per mutation
- Cost: Setting session variables, trigger execution
- Already present: Audit triggers exist, cascade just adds data

**CDC (Phase 3)**:
- Overhead: ~5-10ms per mutation
- Cost: INSERT into outbox table
- Async processing: Debezium lag < 1 second
- Acceptable for: Event-driven architectures

**Total worst case**: ~20ms overhead (still very fast!)

---

### Q3: How does cascade handle large mutations (100+ affected entities)?

**A**: Several strategies:

1. **Pagination** in cascade response:
   ```json
   {
     "_cascade": {
       "updated": [...],  // First 50 entities
       "metadata": {
         "totalCount": 127,
         "hasMore": true,
         "cursor": "..."
       }
     }
   }
   ```

2. **Selective cascade** - only include entities GraphQL client needs:
   ```yaml
   impact:
     primary: Order (CREATE)
     side_effects:
       - Product (UPDATE)  # Include in cascade
       - OrderItem (CREATE)  # Don't include (internal only)
   ```

3. **Cascade summary** - just counts, not full data:
   ```json
   {
     "_cascade": {
       "summary": {
         "Post": { created: 1, updated: 0 },
         "User": { created: 0, updated: 1 },
         "OrderItem": { created: 127, updated: 0 }  // Count only!
       }
     }
   }
   ```

---

### Q4: Can I use cascade without impact metadata?

**A**: No. Cascade **requires** impact metadata because:

```
impact: { primary: Post, side_effects: [User] }
    ↓
CASCADE KNOWS: "Track Post and User changes"
    ↓
Generates: v_cascade_entities := ARRAY[Post, User]
```

Without `impact`, cascade doesn't know what to track.

**But**: Impact metadata is valuable on its own:
- Powers FraiseQL GraphQL schema generation
- Enables frontend code generation
- Provides mutation documentation

So defining impact is a best practice regardless!

---

### Q5: How does this work with multi-tenancy?

**A**: Built-in tenant isolation:

**Pattern 1 (Cascade)**:
- Cascade data includes only tenant's entities
- Trinity resolution includes `tenant_id` check
- No cross-tenant leakage

**Pattern 2 (Audit)**:
- Audit queries require `tenant_id` parameter
- Row-level security can enforce tenant isolation
- Audit indexes include `tenant_id`

**Pattern 3 (CDC)**:
- Outbox events include `tenant_id` field
- Kafka routing can use `tenant_id` as partition key
- Consumers filter by tenant

Example:
```sql
-- Cascade only sees tenant's data
SELECT blog.fn_create_post(..., p_tenant_id := 'tenant-abc');

-- Helper function includes tenant check
CREATE FUNCTION blog.post_pk(p_id UUID, p_tenant_id UUID) ...
WHERE id = p_id AND tenant_id = p_tenant_id;

-- Audit queries require tenant
SELECT * FROM get_post_audit_history(
    '123...', 'tenant-abc'  -- ← Enforced
);
```

---

### Q6: What about event replay?

**A**: Audit trail (Phase 2) enables mutation replay:

```sql
-- Get complete mutation context
SELECT
    audit_id,
    operation_type,
    new_values,
    cascade_data
FROM app.get_post_audit_history_with_cascade('123...', 'tenant-abc');

-- Reconstruct mutation:
-- 1. Primary: Post created with {title: "Hello"}
-- 2. Side effect: User.post_count updated from 41 → 42
-- 3. Side effect: Notification created

-- Replay logic:
-- INSERT INTO tb_post (title) VALUES ('Hello');
-- UPDATE tb_user SET post_count = 42 WHERE ...;
-- INSERT INTO tb_notification ...;
```

With cascade data, you know:
- **What** changed (entities, fields)
- **When** it changed (timestamp)
- **Who** changed it (changed_by)
- **Why** it changed (mutation name)
- **Impact** (all affected entities)

Perfect for:
- Compliance audits
- Debugging
- Event sourcing
- Disaster recovery

---

### Q7: Can I opt-out of cascade for specific actions?

**A**: Yes! Cascade is generated **only if** action has `impact` metadata.

```yaml
# Action WITH cascade
actions:
  - name: create_post
    impact:
      primary: { entity: Post, operation: CREATE }
    # ← Cascade generated automatically

# Action WITHOUT cascade
actions:
  - name: simple_insert
    steps:
      - insert: TempData
    # ← No impact = no cascade
```

You can also disable cascade per-pattern:

```yaml
actions:
  - name: create_post
    impact: { ... }

    # Disable audit cascade
    audit:
      include_cascade: false

    # Disable CDC
    cdc:
      enabled: false
```

---

### Q8: How do I test cascade locally?

**A**: Simple integration test:

```sql
-- 1. Generate SQL
specql generate entities/post.yaml -o /tmp/test.sql

-- 2. Create test database
psql -c "CREATE DATABASE test_cascade"

-- 3. Execute generated SQL
psql test_cascade -f /tmp/test.sql

-- 4. Call mutation
psql test_cascade -c "
SELECT blog.fn_create_post('{
  \"title\": \"Test Post\",
  \"author_id\": \"<some-uuid>\"
}'::jsonb);
"

-- 5. Check cascade in response
-- Should see extra_metadata._cascade with Post and User!
```

For automated testing:
```bash
uv run pytest tests/integration/test_cascade_e2e.py -v
```

---

## Summary: The Complete Picture

### One Metadata Definition

```yaml
impact:
  primary: { entity: Post, operation: CREATE }
  side_effects: [{ entity: User, operation: UPDATE }]
```

### Powers Three Patterns

```
┌─────────────────┐
│  ActionImpact   │ (Single Source of Truth)
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ↓         ↓            ↓
┌────────┐ ┌────────┐ ┌────────┐
│CASCADE │ │ AUDIT  │ │  CDC   │
│(sync)  │ │(sync)  │ │(async) │
└───┬────┘ └───┬────┘ └───┬────┘
    ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐
│GraphQL │ │ Audit  │ │ Kafka  │
│Client  │ │History │ │→Services│
└────────┘ └────────┘ └────────┘
```

### Delivers Complete Solution

- ✅ **GraphQL cache** automatically updated
- ✅ **Audit trail** captures complete mutation history
- ✅ **Microservices** receive async events with full context
- ✅ **Type-safe** at compile time (PostgreSQL composite types)
- ✅ **Zero configuration** (automatic from impact metadata)
- ✅ **Backward compatible** (existing code works unchanged)

### Use What You Need

- **Minimal**: Phase 1 only (GraphQL cache)
- **Standard**: Phase 1 + Phase 2 (+ Audit trail)
- **Enterprise**: All phases (+ CDC for microservices)

---

**The beauty of this system**: Write impact metadata **once**, get three powerful patterns **automatically**!

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Status**: Complete system synthesis
