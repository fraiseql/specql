# GraphQL Cascade + Debezium CDC Integration

**Purpose**: Design document showing how SpecQL's automatic GraphQL Cascade feature integrates with Debezium-style Change Data Capture (CDC) patterns.

**Status**: Planning / Design
**Related**: Issue #8 (GraphQL Cascade), Transactional Outbox Pattern

---

## 🎯 Executive Summary

GraphQL Cascade and Debezium CDC are **complementary** patterns that solve different problems:

| Pattern | Purpose | Scope | Consumer |
|---------|---------|-------|----------|
| **GraphQL Cascade** | Immediate cache updates | Single mutation | GraphQL client (Apollo, Relay) |
| **Debezium CDC** | Async event streaming | All database changes | External systems (microservices, analytics) |

**Key Insight**: The **same mutation metadata** can power both patterns!

---

## 🏗️ Architecture Overview

### Current SpecQL Components

```
┌─────────────────────────────────────────────────────────────┐
│ SpecQL Action with Impact Metadata                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  impact:                                                     │
│    primary:                                                  │
│      entity: Post                                            │
│      operation: CREATE                                       │
│      fields: [title, content]                                │
│    side_effects:                                             │
│      - entity: User                                          │
│        operation: UPDATE                                     │
│        fields: [post_count]                                  │
│                                                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├──────────────────┬─────────────────────┐
                   ↓                  ↓                     ↓
         ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐
         │ GraphQL Cascade │  │ Audit Fields │  │ CDC Outbox       │
         │ (Immediate)     │  │ (Tracking)   │  │ (Async Events)   │
         └─────────────────┘  └──────────────┘  └──────────────────┘
                   │                  │                     │
                   ↓                  ↓                     ↓
         ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐
         │ GraphQL Client  │  │ Audit Trail  │  │ Kafka / Event    │
         │ Cache Update    │  │ Queries      │  │ Bus              │
         └─────────────────┘  └──────────────┘  └──────────────────┘
```

---

## 📊 Pattern Comparison

### GraphQL Cascade (Issue #8)

**Purpose**: Return cascade data in mutation result for immediate GraphQL cache updates

**Storage**: `mutation_result.extra_metadata._cascade`

**Structure**:
```json
{
  "_cascade": {
    "updated": [
      {
        "__typename": "Post",
        "id": "123e4567-...",
        "operation": "CREATED",
        "entity": { "title": "Hello", ... }
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
  }
}
```

**Consumer**: GraphQL client (Apollo, Relay, URQL)

**Latency**: Immediate (synchronous)

**Use Case**: Update UI cache after mutation

---

### Debezium CDC / Transactional Outbox

**Purpose**: Capture all database changes as events for async processing

**Storage**: Dedicated `outbox` table + Debezium connector

**Structure**:
```sql
CREATE TABLE app.outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type TEXT NOT NULL,      -- 'Post', 'User', etc.
    aggregate_id UUID NOT NULL,        -- Entity ID
    event_type TEXT NOT NULL,          -- 'PostCreated', 'UserUpdated', etc.
    event_payload JSONB NOT NULL,      -- Full event data
    event_metadata JSONB,              -- Correlation, causation, etc.
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ,          -- For cleanup
    trace_id TEXT,                     -- Distributed tracing
    correlation_id UUID                -- Link related events
);

CREATE INDEX idx_outbox_processed ON app.outbox (processed_at)
    WHERE processed_at IS NULL;  -- Unprocessed events
```

**Consumer**: Debezium connector → Kafka → Microservices

**Latency**: Async (eventual consistency)

**Use Case**:
- Sync to data warehouse
- Trigger workflows in other services
- Audit trail
- Analytics

---

## 🔄 Integration Strategy: Unified Event Generation

### Approach: Generate Both from Same Impact Metadata

SpecQL can generate **both** cascade data and outbox events from the same `ActionImpact` metadata.

```yaml
entity: Post
actions:
  - name: create_post
    steps:
      - insert: Post
      - update: User SET post_count = post_count + 1

    impact:  # Single source of truth
      primary:
        entity: Post
        operation: CREATE
        fields: [title, content]
      side_effects:
        - entity: User
          operation: UPDATE
          fields: [post_count]

    # NEW: CDC configuration (optional)
    cdc:
      enabled: true
      event_type: PostCreated
      include_side_effects: true
```

---

## 🔧 Implementation Options

### Option 1: Cascade-Only (Current Plan)

**Status**: Implementing now (Issue #8)

**What**: Generate `_cascade` in `extra_metadata`

**When**: Every mutation with impact metadata

**Storage**: In-memory (returned in mutation result)

**Pros**:
- ✅ Immediate availability
- ✅ Zero infrastructure
- ✅ Perfect for GraphQL cache updates

**Cons**:
- ❌ Not persistent
- ❌ Lost if client doesn't capture it
- ❌ Can't replay events

---

### Option 2: Cascade + Outbox (CDC Integration)

**Status**: Future enhancement

**What**: Generate both `_cascade` AND `outbox` events

**When**: Every mutation with `cdc: enabled`

**Storage**:
- `_cascade` → In-memory (mutation result)
- `outbox` → PostgreSQL table

**Pros**:
- ✅ Immediate cascade for GraphQL clients
- ✅ Persistent events for async processing
- ✅ Event replay capability
- ✅ Audit trail
- ✅ Microservices integration

**Cons**:
- ❌ More complex
- ❌ Requires outbox table
- ❌ Requires Debezium setup

---

### Option 3: Audit Trail + Cascade

**Status**: Can implement alongside Option 1

**What**: Log all mutations to audit trail table

**When**: Every mutation

**Storage**:
- `_cascade` → In-memory
- `audit_log` → PostgreSQL table

**Pros**:
- ✅ Full audit history
- ✅ Query past mutations
- ✅ Compliance (SOC2, GDPR)
- ✅ Debugging

**Cons**:
- ❌ Storage overhead
- ❌ Not event-driven (just logs)

---

## 🎯 Recommended Approach: Phased Implementation

### Phase 1: Cascade Only (Current)

**Timeline**: 3-5 days (in progress)

**Deliverables**:
- ✅ Automatic cascade generation
- ✅ `extra_metadata._cascade` structure
- ✅ GraphQL client integration ready

### Phase 2: Integrate Cascade with Existing Audit Trail ✅

**Status**: ✅ **AUDIT TRAIL ALREADY EXISTS!**

**Existing Components**:
- ✅ `AuditGenerator` - Enterprise audit trail generator
- ✅ `AuditTrailGenerator` - Temporal audit trail pattern
- ✅ Audit tables with triggers (INSERT/UPDATE/DELETE tracking)
- ✅ Audit query functions
- ✅ Compliance monitoring

**What's Already Available**:

```sql
-- Existing audit table structure
CREATE TABLE app.audit_{entity} (
    audit_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    operation_type TEXT CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_by UUID,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT,
    transaction_id BIGINT,
    application_name TEXT
);

-- Existing audit query function
CREATE OR REPLACE FUNCTION app.get_{entity}_audit_history(
    p_entity_id UUID,
    p_tenant_id UUID,
    p_limit INTEGER DEFAULT 100
) RETURNS TABLE (
    audit_id UUID,
    operation_type TEXT,
    changed_by UUID,
    changed_at TIMESTAMPTZ,
    old_values JSONB,
    new_values JSONB
);
```

**Future Enhancement** (Optional):

Add cascade data to existing audit trail:

```sql
-- Option 1: Add cascade_data column to existing audit tables
ALTER TABLE app.audit_{entity}
ADD COLUMN cascade_data JSONB,
ADD COLUMN cascade_entities TEXT[];  -- ['Post', 'User', etc.]

-- Option 2: Store cascade in change_reason or metadata field
-- (Can use existing columns without schema changes)

-- Enhanced audit query with cascade
CREATE OR REPLACE FUNCTION app.get_{entity}_audit_history_with_cascade(
    p_entity_id UUID,
    p_tenant_id UUID
) RETURNS TABLE (
    audit_id UUID,
    operation_type TEXT,
    changed_at TIMESTAMPTZ,
    old_values JSONB,
    new_values JSONB,
    cascade_data JSONB  -- ← CASCADE INTEGRATION
);
```

**Integration Strategy**:
1. Actions write to audit tables via triggers (existing)
2. Cascade data stored in `cascade_data` column (new)
3. Query functions return both audit history AND cascade data
4. UI can replay mutations with full cascade context

### Phase 3: CDC Outbox Pattern

**Timeline**: 3-5 days (future)

**Deliverables**:
- Add `app.outbox` table
- Generate events from cascade data
- Debezium connector configuration
- Kafka integration examples
- Link outbox events to existing audit trail

---

## 💡 Integration Example: Cascade + Existing Audit Trail

### How It Works Today (Without Cascade)

**Action**: User creates a blog post

**What Happens**:
1. Action function executes `INSERT INTO tb_post`
2. Trigger fires: `INSERT INTO app.audit_post` (operation='INSERT', new_values={...})
3. Action function returns `mutation_result`
4. Audit trail captures the change ✅

**Audit Query Result**:
```sql
SELECT * FROM app.get_post_audit_history('123...', 'tenant-abc');

-- Result:
-- audit_id | operation | changed_at | old_values | new_values
-- ---------+-----------+------------+------------+------------------
-- abc...   | INSERT    | 2025-01-15 | NULL       | {"title":"Hello"}
```

### How It Will Work (With Cascade)

**Action**: User creates a blog post (also updates author stats)

**What Happens**:
1. Action function executes `INSERT INTO tb_post`
2. Trigger fires: `INSERT INTO app.audit_post`
3. Action function executes `UPDATE tb_user SET post_count = post_count + 1`
4. Trigger fires: `INSERT INTO app.audit_user`
5. **NEW**: Action builds cascade data from impact metadata
6. **NEW**: Cascade data returned in `mutation_result.extra_metadata._cascade`
7. Audit trail captures the change ✅

**Audit Query Result** (Enhanced):
```sql
SELECT * FROM app.get_post_audit_history_with_cascade('123...', 'tenant-abc');

-- Result includes cascade data showing side effects:
-- audit_id | operation | changed_at | old_values | new_values         | cascade_data
-- ---------+-----------+------------+------------+--------------------+------------------
-- abc...   | INSERT    | 2025-01-15 | NULL       | {"title":"Hello"}  | {"updated": [
--          |           |            |            |                    |   {"__typename": "Post", ...},
--          |           |            |            |                    |   {"__typename": "User", ...}
--          |           |            |            |                    | ]}
```

**Key Benefit**: Audit trail now shows **all affected entities**, not just the primary one!

### Practical Use Case: Audit Trail Replay

**Scenario**: Admin wants to see what happened when user created post 'Hello'

**Without Cascade**:
```sql
-- Need multiple queries to piece together what happened
SELECT * FROM app.audit_post WHERE entity_id = '123...';
-- Shows: Post created

-- But wait, did this affect other entities?
-- Need to manually check other audit tables...
SELECT * FROM app.audit_user WHERE changed_at BETWEEN '...' AND '...';
-- Maybe find related User update?
```

**With Cascade in Audit Trail**:
```sql
-- Single query shows everything that happened
SELECT * FROM app.get_post_audit_history_with_cascade('123...', 'tenant-abc');

-- Result shows:
-- 1. Post 'Hello' was created
-- 2. CASCADE: User 'John' post_count was updated from 41 → 42
-- 3. CASCADE: All affected entities in one place
-- 4. CASCADE: Can replay the entire mutation with full context
```

### Implementation: Store Cascade in Audit

**Option 1**: Add column to existing audit tables (schema change)
```sql
ALTER TABLE app.audit_post ADD COLUMN cascade_data JSONB;
ALTER TABLE app.audit_user ADD COLUMN cascade_data JSONB;
-- etc.
```

**Option 2**: Store in existing JSONB field (no schema change)
```sql
-- Store cascade in new_values or custom metadata field
UPDATE app.audit_post
SET new_values = new_values || jsonb_build_object('_cascade', cascade_data);
```

**Option 3**: Separate cascade log table (normalized)
```sql
CREATE TABLE app.mutation_cascade_log (
    id UUID PRIMARY KEY,
    audit_id UUID REFERENCES app.audit_post(audit_id),
    cascade_data JSONB,
    affected_entities TEXT[]
);
```

**Recommendation**: Start with Option 2 (use existing columns), then migrate to Option 1 if needed.

---

## 📋 Detailed Design: Option 2 (Cascade + CDC)

### Generated SQL with Outbox

```sql
CREATE OR REPLACE FUNCTION blog.fn_create_post(input jsonb)
RETURNS app.mutation_result AS $$
DECLARE
    v_result app.mutation_result;
    v_post_id uuid;
    v_user_id uuid;
    v_meta mutation_metadata.mutation_impact_metadata;
    v_cascade_entities JSONB[];
    v_event_id uuid;  -- NEW: For outbox
BEGIN
    -- Mutation logic
    INSERT INTO blog.tb_post (title, content, author_id)
    VALUES (input->>'title', input->>'content', (input->>'author_id')::uuid)
    RETURNING id INTO v_post_id;

    v_user_id := (input->>'author_id')::uuid;
    UPDATE blog.tb_user
    SET post_count = post_count + 1
    WHERE id = v_user_id;

    -- Build cascade (for GraphQL clients)
    v_cascade_entities := ARRAY[
        app.cascade_entity('Post', v_post_id, 'CREATED', 'blog', 'tv_post'),
        app.cascade_entity('User', v_user_id, 'UPDATED', 'blog', 'tv_user')
    ];

    -- NEW: Write to outbox (for CDC/Kafka)
    INSERT INTO app.outbox (
        aggregate_type,
        aggregate_id,
        event_type,
        event_payload,
        event_metadata,
        trace_id,
        correlation_id
    )
    VALUES (
        'Post',
        v_post_id,
        'PostCreated',
        jsonb_build_object(
            'post', (SELECT data FROM blog.tv_post WHERE id = v_post_id),
            'author', (SELECT data FROM blog.tv_user WHERE id = v_user_id)
        ),
        jsonb_build_object(
            'mutation', 'create_post',
            'cascade', (SELECT jsonb_agg(e) FROM unnest(v_cascade_entities) e),
            'affectedEntities', ARRAY['Post', 'User']
        ),
        input->>'trace_id',
        gen_random_uuid()
    )
    RETURNING id INTO v_event_id;

    -- Build result with cascade
    v_result.extra_metadata := jsonb_build_object(
        '_cascade', jsonb_build_object(
            'updated', (SELECT jsonb_agg(e) FROM unnest(v_cascade_entities) e),
            'deleted', '[]'::jsonb,
            'invalidations', to_jsonb(v_meta.cache_invalidations),
            'metadata', jsonb_build_object(
                'timestamp', now(),
                'affectedCount', array_length(v_cascade_entities, 1),
                'eventId', v_event_id  -- Link to outbox event
            )
        ),
        '_meta', to_jsonb(v_meta)
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

## 🔍 Event Payload Comparison

### GraphQL Cascade (Immediate)

```json
{
  "_cascade": {
    "updated": [
      {
        "__typename": "Post",
        "id": "123...",
        "operation": "CREATED",
        "entity": { "title": "Hello", "content": "..." }
      },
      {
        "__typename": "User",
        "id": "456...",
        "operation": "UPDATED",
        "entity": { "post_count": 42 }
      }
    ],
    "metadata": {
      "timestamp": "2025-01-15T10:30:00Z",
      "affectedCount": 2,
      "eventId": "789..."  // ← Links to outbox
    }
  }
}
```

### CDC Outbox Event (Async)

```json
{
  "id": "789...",
  "aggregate_type": "Post",
  "aggregate_id": "123...",
  "event_type": "PostCreated",
  "event_payload": {
    "post": {
      "id": "123...",
      "title": "Hello",
      "content": "...",
      "author": { "id": "456...", "name": "John" }
    },
    "author": {
      "id": "456...",
      "post_count": 42
    }
  },
  "event_metadata": {
    "mutation": "create_post",
    "cascade": [ /* same as above */ ],
    "affectedEntities": ["Post", "User"]
  },
  "created_at": "2025-01-15T10:30:00Z",
  "trace_id": "abc123",
  "correlation_id": "def456"
}
```

---

## 🚀 Benefits of Unified Approach

### 1. Single Source of Truth

Both cascade and CDC events derive from the same `ActionImpact` metadata:
- ✅ Consistent data across patterns
- ✅ No duplicate configuration
- ✅ Easier to maintain

### 2. Flexible Consumption

Different consumers get data in their preferred format:
- GraphQL clients → `_cascade` (immediate)
- Microservices → Kafka events (async)
- Analytics → Event stream
- Audit → Mutation log

### 3. Traceability

Link events across systems:
- `eventId` in cascade → `id` in outbox
- `trace_id` for distributed tracing
- `correlation_id` for causality chains

### 4. Replay Capability

Outbox events enable:
- Event sourcing
- State reconstruction
- Debugging
- Testing

---

## 📊 Use Case Examples

### Use Case 1: Blog Post Creation

**Action**: User creates a blog post

**Immediate (GraphQL Cascade)**:
1. Mutation returns `_cascade` with Post + User
2. Apollo Client updates cache
3. UI instantly shows new post + updated author stats

**Async (CDC Outbox)**:
1. Event written to outbox: `PostCreated`
2. Debezium streams to Kafka
3. Analytics service updates post count metrics
4. Notification service sends email to followers
5. Search indexer updates Elasticsearch

---

### Use Case 2: E-commerce Order

**Action**: User places order

**Immediate (GraphQL Cascade)**:
```json
{
  "_cascade": {
    "updated": [
      { "__typename": "Order", "operation": "CREATED", ... },
      { "__typename": "Product", "operation": "UPDATED", ... },  // inventory
      { "__typename": "User", "operation": "UPDATED", ... }      // order_count
    ],
    "invalidations": [
      { "queryName": "products", "strategy": "INVALIDATE" }
    ]
  }
}
```

**Async (CDC Outbox)**:
- `OrderCreated` → Fulfillment service
- `ProductInventoryUpdated` → Warehouse system
- `UserOrderPlaced` → Loyalty points service

---

### Use Case 3: Multi-Tenant SaaS

**Action**: Admin updates organization settings

**Immediate (GraphQL Cascade)**:
```json
{
  "_cascade": {
    "updated": [
      { "__typename": "Organization", "operation": "UPDATED", ... }
    ],
    "metadata": {
      "tenantId": "tenant-123"
    }
  }
}
```

**Async (CDC Outbox)**:
- `OrganizationUpdated` → Cache invalidation service (clear all users' caches)
- → Billing service (update subscription)
- → Analytics (track configuration changes)

---

## 🛠️ Implementation Checklist

### Phase 1: Cascade Only ✅
- [ ] PostgreSQL helper functions
- [ ] Cascade array generation
- [ ] Integration with `extra_metadata`
- [ ] GraphQL client integration docs

### Phase 2: Audit Trail (Future)
- [ ] Create `app.mutation_log` table
- [ ] Log mutations with cascade data
- [ ] Query API for audit history
- [ ] Retention policies

### Phase 3: CDC Outbox (Future)
- [ ] Create `app.outbox` table
- [ ] Generate outbox events from cascade
- [ ] Debezium connector configuration
- [ ] Kafka topic mapping
- [ ] Event schema registry
- [ ] Consumer examples

### Phase 4: Advanced Features (Future)
- [ ] Event versioning
- [ ] Schema evolution
- [ ] Dead letter queue
- [ ] Event replay API
- [ ] Distributed tracing integration
- [ ] Event compaction strategies

---

## 📚 Related Patterns

### Transactional Outbox Pattern
- **Problem**: Dual writes (database + message bus) aren't atomic
- **Solution**: Write events to outbox table in same transaction
- **SpecQL Fit**: Perfect! Action functions already use transactions

### Event Sourcing
- **Problem**: Need to reconstruct state from events
- **Solution**: Store all state changes as events
- **SpecQL Fit**: Outbox events can be event source

### CQRS (Command Query Responsibility Segregation)
- **Problem**: Read and write models have different requirements
- **Solution**: Separate read and write paths
- **SpecQL Fit**: Table views (read) + Actions (write) naturally fit CQRS

### Saga Pattern
- **Problem**: Distributed transactions across services
- **Solution**: Orchestrate multi-service workflows via events
- **SpecQL Fit**: Outbox events can trigger saga steps

---

## 🎯 Decision Matrix: Which Pattern When?

| Requirement | GraphQL Cascade | Audit Trail | CDC Outbox |
|-------------|-----------------|-------------|------------|
| Immediate UI updates | ✅ Perfect | ❌ No | ❌ Too slow |
| Event replay | ❌ No | ⚠️ Limited | ✅ Yes |
| Microservices integration | ❌ No | ❌ No | ✅ Yes |
| Compliance audit | ⚠️ Limited | ✅ Yes | ✅ Yes |
| Analytics pipeline | ❌ No | ⚠️ Batch only | ✅ Real-time |
| Storage overhead | ✅ Zero | ⚠️ Medium | ⚠️ Medium |
| Setup complexity | ✅ Simple | ✅ Simple | ⚠️ Complex |

---

## 🚀 Recommended Rollout

### Now: Phase 1 (Cascade Only)
- Implement automatic cascade generation
- Perfect for GraphQL-first applications
- Zero infrastructure requirements
- Immediate value

### Soon: Phase 2 (Audit Trail)
- Add mutation logging
- Compliance and debugging
- Simple to implement
- Builds on cascade foundation

### Later: Phase 3 (CDC Outbox)
- Event-driven architecture
- Microservices integration
- Requires infrastructure (Debezium, Kafka)
- Build when needed

---

## 📖 References

- **Debezium**: https://debezium.io/
- **Transactional Outbox Pattern**: https://microservices.io/patterns/data/transactional-outbox.html
- **GraphQL Cascade**: Issue #8
- **SpecQL Impact Metadata**: `src/generators/actions/impact_metadata_compiler.py`
- **Audit Fields**: `src/generators/schema/audit_fields.py`

---

**Status**: Design Complete
**Next**: Implement Phase 1 (Cascade Only) per Issue #8
**Future**: Consider Phase 2/3 based on user demand
