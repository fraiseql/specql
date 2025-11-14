# GraphQL Cascade - Implementation Status

**Issue**: [#8 - Add GraphQL Cascade Support](https://github.com/fraiseql/specql/issues/8)
**Status**: 🟡 Ready for Implementation
**Last Updated**: 2025-11-11

---

## 📊 Overview

SpecQL will automatically generate GraphQL Cascade data in `mutation_result.extra_metadata._cascade` to enable FraiseQL to automatically update GraphQL client caches without manual refetch queries.

### Key Features

✅ **Automatic Generation** - No configuration needed for 80% of use cases
✅ **Flexible Configuration** - Application-wide OR per-mutation settings
✅ **Audit Trail Integration** - Cascade data persisted in audit tables
✅ **CDC Support** - Optional Kafka streaming via transactional outbox
✅ **Performance Controls** - Entity filtering and payload limits

---

## 🎯 Configuration Levels (Priority Order)

```
1. Per-Mutation Config (highest priority)
2. Application-Wide Config
3. Default Behavior (lowest priority)
```

### Level 1: Default (Zero Config)

```yaml
entity: Post
actions:
  - name: create_post
    impact:
      primary: { entity: Post, operation: CREATE }
      side_effects: [{ entity: User, operation: UPDATE }]
# ✅ Cascade automatically enabled from impact metadata
```

**Result**: Cascade includes Post (primary) + User (side effect)

---

### Level 2: Application-Wide

```yaml
# At top of SpecQL file or in specql.config.yaml
cascade:
  enabled: true
  include_full_data: true
  max_entities: 100

entity: Post
actions:
  - name: create_post
    impact: { ... }
    # Uses application-wide config
```

**Result**: All actions use the same cascade configuration

---

### Level 3: Per-Mutation Override

```yaml
cascade:
  enabled: true  # Application default

entity: Order
actions:
  - name: place_order
    impact: { ... }
    cascade:
      enabled: true
      include_entities: [Order, Product, User]
      # Override: Custom cascade for this action

  - name: recalculate_tax
    impact: { ... }
    cascade:
      enabled: false
      # Override: Disable cascade for internal action
```

**Result**: Each action has custom cascade behavior

---

## 🏗️ Implementation Phases

### ✅ PHASE 0: Configuration System (0.5-1 day)

**Objective**: Add cascade configuration support at application and action levels

**Deliverables**:
- `CascadeConfig` dataclass in AST
- `ApplicationConfig` for app-wide settings
- Parser updates for both configuration levels
- Priority resolution logic
- Tests for all configuration patterns

**Status**: 🟡 Ready to implement

---

### ✅ PHASE 1: PostgreSQL Helpers (1 day)

**Objective**: Add helper functions to fetch complete entity data from table views

**Deliverables**:
- `core.fetch_entity_by_id(entity_name, entity_id)` - Fetch single entity
- `core.fetch_entity_by_pk(entity_name, entity_pk)` - Fetch by primary key
- `core.build_cascade_entry(entity_name, entity_id, operation)` - Build cascade JSON
- Tests for all helper functions

**Status**: 🟡 Ready to implement

---

### ✅ PHASE 2: Cascade Compilation (1-2 days)

**Objective**: Generate cascade data collection logic in action functions

**Deliverables**:
- `CascadeCompiler` class
- Cascade variable declarations (`v_cascade_entities`, `v_cascade_deleted`)
- Cascade collection logic (from primary + side effects)
- Entity filtering (include/exclude lists)
- Performance limits (max_entities)
- Integration with `extra_metadata._cascade`
- Tests for cascade generation

**Status**: 🟡 Ready to implement

---

### ✅ PHASE 3: Step Compiler Verification (1 day)

**Objective**: Verify cascade tracking across all step types

**Deliverables**:
- `INSERT` step: Track created entity IDs
- `UPDATE` step: Track updated entity IDs
- Validation tests for each step type
- Edge case handling (bulk operations, conditional logic)

**Status**: 🟡 Ready to implement

---

### ✅ PHASE 4: Integration & Testing (1 day)

**Objective**: End-to-end validation of cascade generation

**Deliverables**:
- E2E tests for full cascade workflow
- Performance tests (large mutations, many entities)
- Frontend integration verification (TypeScript types)
- Documentation updates

**Status**: 🟡 Ready to implement

---

### ✅ PHASE 5: Audit Trail Integration (2-3 days)

**Objective**: Persist cascade data in audit trail tables

**Deliverables**:
- Add `cascade_data JSONB` to audit tables
- Session variables to pass cascade from function to trigger
- Audit trail tests with cascade data
- Documentation updates

**Status**: 🟡 Future enhancement (after Phase 1-4)

---

### ✅ PHASE 6: CDC Outbox Pattern (3-5 days)

**Objective**: Stream cascade events to Kafka via transactional outbox

**Deliverables**:
- `tb_cdc_outbox` table with Debezium metadata
- Outbox insertion logic in action functions
- Debezium connector configuration
- Kafka streaming tests
- Documentation updates

**Status**: 🟡 Future enhancement (after Phase 5)

---

## 📚 Documentation

### Core Documents

- **[GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md](./GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md)** - Detailed Phase 1-4 implementation plan with TDD cycles
- **[CASCADE_CONFIGURATION_EXAMPLES.md](../examples/CASCADE_CONFIGURATION_EXAMPLES.md)** - 6 real-world configuration examples
- **[CASCADE_AUDIT_CDC_PHASES_2_3.md](./CASCADE_AUDIT_CDC_PHASES_2_3.md)** - Detailed Phase 5-6 implementation plan
- **[COMPLETE_SYSTEM_SYNTHESIS.md](./COMPLETE_SYSTEM_SYNTHESIS.md)** - Comprehensive system overview (100+ pages)
- **[CHOOSING_PATTERNS_FOR_YOUR_APP.md](../guides/CHOOSING_PATTERNS_FOR_YOUR_APP.md)** - Decision framework for pattern selection

### Example Apps

From `CASCADE_CONFIGURATION_EXAMPLES.md`:

1. **Simple Blog** - Zero config, automatic cascade
2. **SaaS App** - Application-wide config for consistency
3. **E-commerce** - Mixed config with per-action overrides
4. **Bulk Operations** - Entity filtering for performance
5. **Mobile App** - Minimal payload (`include_full_data: false`)
6. **Multi-App Portfolio** - Different configs per app

---

## 🔧 Configuration Schema

```yaml
# Complete cascade configuration options

cascade:
  # Enable/disable cascade generation
  enabled: boolean  # Default: true (if impact exists)

  # Entity filtering
  include_entities: [string]  # Whitelist (optional)
  exclude_entities: [string]  # Blacklist (default: [])

  # Data inclusion
  include_full_data: boolean  # Include complete entity objects (default: true)
  include_deleted: boolean    # Include deleted entities (default: true)

  # Performance
  max_entities: integer  # Limit number of entities in cascade (optional)
```

### Shorthand Syntax

```yaml
# Quick enable/disable
actions:
  - name: my_action
    cascade: false  # Shorthand for { enabled: false }
```

---

## 🎯 Use Cases by Configuration

| Use Case | Configuration | Rationale |
|----------|---------------|-----------|
| **Simple Blog** | Default (zero config) | All mutations similar, no special needs |
| **SaaS Product** | Application-wide | Consistent behavior across all mutations |
| **E-commerce** | Mixed (app + overrides) | Critical mutations need full cascade, internal ones don't |
| **Bulk Operations** | Per-action filtering | Performance optimization for large mutations |
| **Mobile App** | Application-wide minimal | Bandwidth constraints require smaller payloads |
| **Enterprise** | All patterns enabled | Needs cascade + audit + CDC for compliance |

---

## 🚀 Getting Started

### For Simple Apps (Recommended Starting Point)

```yaml
# No configuration needed!
entity: Contact
actions:
  - name: create_contact
    steps:
      - insert: Contact
      - update: User SET contact_count = contact_count + 1

    impact:
      primary: { entity: Contact, operation: CREATE }
      side_effects: [{ entity: User, operation: UPDATE }]

# ✅ Cascade automatically includes Contact + User
```

### For Production Apps (Add Global Config)

```yaml
# Application-wide configuration
cascade:
  enabled: true
  include_full_data: true
  max_entities: 100  # Performance limit

entity: Contact
actions:
  - name: create_contact
    impact: { ... }
    # Uses application config
```

### For Complex Apps (Add Per-Action Overrides)

```yaml
cascade:
  enabled: true  # Default for all actions

entity: Contact
actions:
  # Critical mutation: Full cascade
  - name: create_contact
    impact: { ... }
    cascade:
      enabled: true
      include_entities: [Contact, User, Company]

  # Internal action: No cascade
  - name: recalculate_stats
    impact: { ... }
    cascade:
      enabled: false
```

---

## 🧪 Testing Strategy

### Phase 0-4 Tests (Core Cascade)

```bash
# Configuration parsing tests
uv run pytest tests/unit/core/test_cascade_config.py

# Helper function tests
uv run pytest tests/unit/generators/test_cascade_helpers.py

# Cascade compilation tests
uv run pytest tests/unit/generators/test_cascade_compiler.py

# E2E integration tests
uv run pytest tests/integration/test_cascade_e2e.py
```

### Phase 5 Tests (Audit Integration)

```bash
# Audit trail with cascade tests
uv run pytest tests/integration/test_cascade_audit_integration.py
```

### Phase 6 Tests (CDC Outbox)

```bash
# CDC outbox tests
uv run pytest tests/integration/test_cascade_cdc_outbox.py
```

---

## 📊 Performance Considerations

### Entity Filtering

**Problem**: Mutation affects 500+ entities (e.g., bulk notifications)

**Solution**: Use `include_entities` or `exclude_entities` to limit cascade

```yaml
actions:
  - name: bulk_approve_posts
    cascade:
      include_entities: [Post, User]  # Only essential entities
      exclude_entities: [Notification, AuditLog]  # Skip non-UI entities
      max_entities: 50  # Hard limit
```

**Result**: 500KB → 50KB response size (90% reduction)

---

### Minimal Payload for Mobile

**Problem**: Mobile clients have limited bandwidth

**Solution**: Set `include_full_data: false` at application level

```yaml
cascade:
  enabled: true
  include_full_data: false  # Only __typename, id, operation
```

**Result**: 80% smaller cascade payload (IDs only, no entity data)

---

## 🔍 Troubleshooting

### Cascade Not Generated

**Check**:
1. Does action have `impact` metadata? (Required for automatic cascade)
2. Is cascade explicitly disabled? (`cascade: { enabled: false }`)
3. Is entity excluded? (`exclude_entities: [MyEntity]`)

### Cascade Too Large

**Solutions**:
1. Add `max_entities` limit
2. Use `include_entities` to whitelist only essential entities
3. Use `exclude_entities` to blacklist non-critical entities
4. Set `include_full_data: false` for ID-only cascade

### Cascade Missing Entities

**Check**:
1. Are side effects declared in `impact`?
2. Is entity filtered out? (Check `include_entities`/`exclude_entities`)
3. Is `max_entities` limit reached?

---

## 🎯 Success Metrics

### Phase 1-4 (Core Cascade)

- ✅ Zero-config cascade works for simple apps
- ✅ Application-wide config reduces repetition
- ✅ Per-action overrides handle special cases
- ✅ All tests passing (unit + integration)
- ✅ Documentation complete with examples

### Phase 5 (Audit Integration)

- ✅ Cascade data persisted in audit trail
- ✅ Session variables bridge working
- ✅ Audit queries include cascade data
- ✅ Tests verify cascade persistence

### Phase 6 (CDC Outbox)

- ✅ Cascade events in Kafka
- ✅ Debezium connector configured
- ✅ Event replay capability verified
- ✅ Multi-tenant isolation maintained

---

## 🤝 Related Features

### Existing SpecQL Features Leveraged

- **ActionImpact** - Source of cascade metadata
- **Table Views (tv_*)** - Complete entity data fetching
- **Trinity Pattern** - UUID → pk/id/identifier resolution
- **Audit Trail** - Existing infrastructure for persistence
- **ImpactMetadataCompiler** - Existing metadata generation

### Future Enhancements

- **Subscription Support** - Real-time cascade streaming
- **Optimistic UI Updates** - Client-side cascade prediction
- **Cascade Replay** - Replay cascade from audit trail
- **Cascade Analytics** - Track cascade performance metrics

---

## 📅 Timeline

### Recommended Implementation Order

**Week 1**: Core Cascade (Phase 0-4)
- Day 1: Configuration system (Phase 0)
- Day 2: PostgreSQL helpers (Phase 1)
- Day 3-4: Cascade compilation (Phase 2)
- Day 5: Step verification + E2E tests (Phase 3-4)

**Week 2** (Optional): Audit Integration (Phase 5)
- Day 1-2: Session variables + audit tables
- Day 3: Testing + documentation

**Week 3** (Optional): CDC Outbox (Phase 6)
- Day 1-2: Outbox table + insertion logic
- Day 3-4: Debezium configuration
- Day 5: Testing + documentation

---

## 🎯 Next Steps

1. **Review Configuration Examples** - Read `CASCADE_CONFIGURATION_EXAMPLES.md` for patterns
2. **Begin Phase 0** - Implement configuration system with TDD
3. **Follow Implementation Plan** - See `GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md` for detailed TDD cycles
4. **Test as You Go** - Run tests after each RED/GREEN/REFACTOR cycle
5. **Update Documentation** - Keep docs in sync with implementation

---

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Status**: 🟡 Ready for Implementation
**Owner**: SpecQL Core Team
