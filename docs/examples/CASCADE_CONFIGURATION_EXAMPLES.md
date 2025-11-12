# Cascade Configuration Examples

**Purpose**: Comprehensive examples showing how to configure GraphQL Cascade at application-wide and per-mutation levels.

---

## 🎯 Configuration Levels

SpecQL supports **three configuration levels** with clear priority:

```
Priority: Per-Action > Application-Wide > Default
```

### Level 1: Default (Zero Config)

```yaml
# No configuration needed!
entity: Post
actions:
  - name: create_post
    impact:
      primary: { entity: Post, operation: CREATE }
      side_effects: [{ entity: User, operation: UPDATE }]

# ← Cascade automatically enabled because impact exists
```

**Result**: Cascade includes Post (primary) + User (side effect)

---

### Level 2: Application-Wide Configuration

```yaml
# At the top of your SpecQL file or in specql.config.yaml
cascade:
  enabled: true
  include_full_data: true
  max_entities: 50

entity: Post
actions:
  - name: create_post
    impact: { ... }
    # ← Uses application-wide config

  - name: update_post
    impact: { ... }
    # ← Also uses application-wide config
```

**Result**: All actions use the same cascade configuration

---

### Level 3: Per-Action Override

```yaml
cascade:
  enabled: true  # Application default

entity: Post
actions:
  - name: create_post
    impact: { ... }
    cascade:
      enabled: true
      include_entities: [Post]  # ← Only Post in cascade
    # ← Overrides application config

  - name: update_post_with_stats
    impact: { ... }
    cascade:
      enabled: true
      include_entities: [Post, User, Statistics]  # ← All entities
    # ← Different override for this action
```

**Result**: Each action has custom cascade behavior

---

## 📚 Complete Examples by Use Case

### Example 1: Simple Blog (Minimal Config)

**Use Case**: Personal blog, all mutations should include cascade

**Configuration**: None needed (use defaults)

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

# ✅ Cascade automatically enabled
# ✅ Includes: Post (primary) + User (side effect)
```

**Generated Cascade**:
```json
{
  "_cascade": {
    "updated": [
      { "__typename": "Post", "operation": "CREATED", ... },
      { "__typename": "User", "operation": "UPDATED", ... }
    ]
  }
}
```

---

### Example 2: SaaS App (Application-Wide Config)

**Use Case**: Multi-tenant SaaS, consistent cascade across all mutations

**Configuration**: Application-wide settings

```yaml
# Application-wide cascade configuration
cascade:
  enabled: true
  include_full_data: true
  include_deleted: true
  max_entities: 100

entity: Project
schema: saas

fields:
  name: text
  owner: ref(User)

actions:
  - name: create_project
    steps:
      - insert: Project
      - update: User SET project_count = project_count + 1

    impact:
      primary: { entity: Project, operation: CREATE }
      side_effects: [{ entity: User, operation: UPDATE }]

  - name: delete_project
    steps:
      - update: Project SET deleted_at = now()
      - update: User SET project_count = project_count - 1

    impact:
      primary: { entity: Project, operation: DELETE }
      side_effects: [{ entity: User, operation: UPDATE }]

  - name: archive_project
    steps:
      - update: Project SET archived_at = now()

    impact:
      primary: { entity: Project, operation: UPDATE }

# All actions use the same application-wide cascade config
```

**Benefits**:
- ✅ Consistent cascade behavior across app
- ✅ Single place to configure
- ✅ Easy to adjust globally

---

### Example 3: E-commerce (Mixed Configuration)

**Use Case**: E-commerce with different cascade needs per action

**Configuration**: Application defaults + per-action overrides

```yaml
# Application defaults
cascade:
  enabled: true
  include_full_data: true

entity: Order
schema: ecommerce

actions:
  # Critical mutation: Full cascade with all entities
  - name: place_order
    steps:
      - insert: Order
      - update: Product SET inventory = inventory - quantity
      - update: User SET order_count = order_count + 1
      - insert: OrderItem (multiple)

    impact:
      primary: { entity: Order, operation: CREATE }
      side_effects:
        - { entity: Product, operation: UPDATE }
        - { entity: User, operation: UPDATE }
        - { entity: OrderItem, operation: CREATE }

    cascade:
      enabled: true
      # Include all entities for critical order placement
      # (overrides app default if needed)

  # Less critical: Only order details in cascade
  - name: update_shipping_address
    steps:
      - update: Order SET shipping_address = new_address

    impact:
      primary: { entity: Order, operation: UPDATE, fields: [shipping_address] }

    cascade:
      enabled: true
      include_entities: [Order]  # ← Only Order, skip side effects

  # Internal action: No cascade needed
  - name: recalculate_tax
    steps:
      - update: Order SET tax_amount = calculated_tax

    impact:
      primary: { entity: Order, operation: UPDATE, fields: [tax_amount] }

    cascade:
      enabled: false  # ← Disabled for internal calculations
```

**Why Different Configs**:
- `place_order`: Critical UX, needs all entities for UI update
- `update_shipping_address`: Simple update, only Order needed
- `recalculate_tax`: Internal, no UI impact, cascade unnecessary

---

### Example 4: Performance Optimization (Entity Filtering)

**Use Case**: Large mutations affecting many entities, optimize cascade payload

**Configuration**: Selective entity inclusion

```yaml
cascade:
  enabled: true
  max_entities: 50  # Application limit

entity: BulkOperation
schema: admin

actions:
  - name: bulk_approve_posts
    steps:
      - update: Post SET status = 'approved' WHERE id IN (ids)
      - update: User SET approved_posts_count = approved_posts_count + 1
      - insert: Notification (for each post author)
      - insert: AuditLog

    impact:
      primary:
        entity: Post
        operation: UPDATE  # Multiple posts
      side_effects:
        - entity: User
          operation: UPDATE  # Multiple users
        - entity: Notification
          operation: CREATE  # Many notifications
        - entity: AuditLog
          operation: CREATE

    cascade:
      enabled: true
      # Only include critical entities for UI
      include_entities: [Post, User]
      # Exclude notifications and audit logs (not needed in UI)
      exclude_entities: [Notification, AuditLog]
      # Limit to 50 total entities
      max_entities: 50

# Result: Cascade only includes Post + User, up to 50 entities total
```

**Performance Benefit**:
- Without filtering: Cascade could include 500+ notification entities
- With filtering: Cascade limited to Posts + Users, max 50 entities
- Response size: Reduced from ~500KB to ~50KB

---

### Example 5: Mobile App (Minimal Cascade)

**Use Case**: Mobile app with limited bandwidth, minimize cascade payload

**Configuration**: Exclude full entity data

```yaml
cascade:
  enabled: true
  include_full_data: false  # ← Only IDs and operations, no entity data

entity: Post
schema: mobile

actions:
  - name: create_post
    steps:
      - insert: Post
      - update: User SET post_count = post_count + 1

    impact:
      primary: { entity: Post, operation: CREATE }
      side_effects: [{ entity: User, operation: UPDATE }]

# Result: Cascade includes only __typename, id, operation (no full entity)
```

**Generated Cascade** (minimal):
```json
{
  "_cascade": {
    "updated": [
      {
        "__typename": "Post",
        "id": "123...",
        "operation": "CREATED"
        // ← No "entity" field = smaller payload
      },
      {
        "__typename": "User",
        "id": "456...",
        "operation": "UPDATED"
      }
    ],
    "metadata": {
      "affectedCount": 2
    }
  }
}
```

**Benefit**: ~80% smaller cascade payload for mobile clients

---

### Example 6: Multi-App Portfolio

**Use Case**: Multiple apps with different cascade needs

**Configuration**: Separate config files per app

#### App 1: Personal Blog (blog/specql.yaml)

```yaml
# Minimal config
entity: Post
actions:
  - name: create_post
    impact: { ... }
    # Uses default cascade (enabled, full data)
```

#### App 2: SaaS Product (saas/specql.yaml)

```yaml
# Application-wide strict config
cascade:
  enabled: true
  include_full_data: true
  max_entities: 100

entity: Project
actions:
  - name: create_project
    impact: { ... }
    # Uses application config
```

#### App 3: E-commerce (ecommerce/specql.yaml)

```yaml
# Mixed config with overrides
cascade:
  enabled: true
  include_full_data: true

entity: Order
actions:
  - name: place_order
    impact: { ... }
    cascade:
      max_entities: 50  # Override for performance

  - name: internal_calculation
    impact: { ... }
    cascade:
      enabled: false  # Override: disable
```

**Benefit**: Each app has exactly the cascade behavior it needs

---

## 🔧 Advanced Configuration Patterns

### Pattern 1: Whitelist Approach

**Use Case**: Only include specific entities, ignore all others

```yaml
actions:
  - name: update_user_profile
    impact:
      primary: { entity: User, operation: UPDATE }
      side_effects:
        - { entity: Profile, operation: UPDATE }
        - { entity: Settings, operation: UPDATE }
        - { entity: Cache, operation: UPDATE }
        - { entity: SearchIndex, operation: UPDATE }

    cascade:
      enabled: true
      include_entities: [User, Profile]  # ← Only these
      # Settings, Cache, SearchIndex excluded automatically
```

**Result**: Cascade only includes User + Profile

---

### Pattern 2: Blacklist Approach

**Use Case**: Include most entities, exclude specific ones

```yaml
actions:
  - name: create_post_with_analytics
    impact:
      primary: { entity: Post, operation: CREATE }
      side_effects:
        - { entity: User, operation: UPDATE }
        - { entity: Category, operation: UPDATE }
        - { entity: AnalyticsEvent, operation: CREATE }
        - { entity: SearchIndex, operation: CREATE }

    cascade:
      enabled: true
      exclude_entities: [AnalyticsEvent, SearchIndex]  # ← Exclude these
      # Post, User, Category included automatically
```

**Result**: Cascade includes Post + User + Category (excludes analytics/search)

---

### Pattern 3: Conditional Cascade

**Use Case**: Different cascade configs for different environments

```yaml
# In production: Full cascade
cascade:
  enabled: true
  include_full_data: true
  max_entities: 100

# In development: Minimal cascade for faster testing
# cascade:
#   enabled: true
#   include_full_data: false
#   max_entities: 10
```

**Implementation**: Use environment variables or separate config files

---

### Pattern 4: Incremental Adoption

**Use Case**: Gradually enable cascade across existing app

```yaml
# Global: Disabled by default
cascade:
  enabled: false

entity: Post
actions:
  # New action: Enable cascade
  - name: create_post_v2
    impact: { ... }
    cascade:
      enabled: true  # ← Explicitly enable for new action

  # Legacy action: No cascade
  - name: create_post_legacy
    impact: { ... }
    # Uses global config (disabled)
```

**Benefit**: Safely test cascade on new mutations without affecting existing ones

---

## 📊 Configuration Comparison

| Config Style | Use Case | Example |
|--------------|----------|---------|
| **No Config** | Simple apps, all mutations similar | Personal blog, prototype |
| **Application-Wide** | Consistent behavior across app | SaaS product, internal tool |
| **Per-Action** | Different needs per mutation | E-commerce, complex workflows |
| **Mixed** | Most actions similar, some special | Typical production app |

---

## 🎯 Configuration Best Practices

### 1. Start with Defaults

```yaml
# First version: No config
entity: MyEntity
actions:
  - name: my_action
    impact: { ... }
    # ← Use defaults
```

**Rationale**: Defaults work for 80% of cases

---

### 2. Add Application Config When Needed

```yaml
# After testing, if all actions need same config:
cascade:
  enabled: true
  max_entities: 50  # Performance limit

entity: MyEntity
actions:
  - name: action1
    impact: { ... }
  - name: action2
    impact: { ... }
```

**Rationale**: Reduces repetition, single source of truth

---

### 3. Override Per-Action Only When Necessary

```yaml
cascade:
  enabled: true  # Default

actions:
  # Most actions use default
  - name: regular_action
    impact: { ... }

  # Special case needs override
  - name: bulk_action
    impact: { ... }
    cascade:
      max_entities: 10  # ← Override for this action only
```

**Rationale**: Keep configuration minimal and clear

---

### 4. Document Overrides

```yaml
actions:
  - name: bulk_approve
    impact: { ... }
    cascade:
      max_entities: 10  # Performance: Limit for bulk operations
      exclude_entities: [AuditLog]  # Not needed in UI
```

**Rationale**: Future developers understand why config differs

---

### 5. Use Consistent Patterns Across Apps

```yaml
# Pattern: All apps use application-wide config
# App 1
cascade:
  enabled: true
  max_entities: 100

# App 2
cascade:
  enabled: true
  max_entities: 50  # Different limit, same pattern
```

**Rationale**: Easier to maintain multiple apps

---

## 🔍 Testing Configurations

### Test 1: Verify Default Behavior

```bash
# Generate SQL without any cascade config
specql generate entities/post.yaml -o /tmp/test.sql

# Check that cascade is generated
grep "_cascade" /tmp/test.sql
# Should find cascade code
```

---

### Test 2: Verify Application Config

```yaml
# test-config.yaml
cascade:
  enabled: false  # Explicitly disable

entity: Test
actions:
  - name: test_action
    impact: { ... }
```

```bash
specql generate test-config.yaml -o /tmp/test.sql

# Check that cascade is NOT generated
grep "_cascade" /tmp/test.sql
# Should NOT find cascade code
```

---

### Test 3: Verify Per-Action Override

```yaml
cascade:
  enabled: false  # Global: disabled

actions:
  - name: test_action
    impact: { ... }
    cascade:
      enabled: true  # Override: enabled
```

```bash
specql generate test-config.yaml -o /tmp/test.sql

# Check that cascade IS generated (override wins)
grep "_cascade" /tmp/test.sql
# Should find cascade code
```

---

## 📝 Configuration Schema Reference

```yaml
# Complete cascade configuration schema

cascade:
  # Enable/disable cascade generation
  enabled: boolean  # Default: true (if impact exists)

  # Entity filtering
  include_entities: [string]  # Whitelist (optional)
  exclude_entities: [string]  # Blacklist (optional, default: [])

  # Data inclusion
  include_full_data: boolean  # Include complete entity objects (default: true)
  include_deleted: boolean    # Include deleted entities (default: true)

  # Performance
  max_entities: integer  # Limit number of entities in cascade (optional)

# Per-action override (same schema)
entity: MyEntity
actions:
  - name: my_action
    cascade:
      # Same options as above
      enabled: boolean
      include_entities: [string]
      # ...
```

---

## 🚀 Migration Guide

### Migrating from No Config to Application Config

**Before**:
```yaml
entity: Post
actions:
  - name: action1
    impact: { ... }
  - name: action2
    impact: { ... }
```

**After**:
```yaml
# Add application-wide config
cascade:
  enabled: true
  max_entities: 50

entity: Post
actions:
  - name: action1
    impact: { ... }
  - name: action2
    impact: { ... }
```

**Impact**: No breaking changes, just adds performance limit

---

### Migrating from Application Config to Per-Action

**Before**:
```yaml
cascade:
  enabled: true

actions:
  - name: action1
    impact: { ... }
  - name: action2
    impact: { ... }
```

**After**:
```yaml
# Remove application config
# cascade:
#   enabled: true

actions:
  - name: action1
    impact: { ... }
    cascade:
      enabled: true  # Now explicit per-action

  - name: action2
    impact: { ... }
    cascade:
      enabled: true
```

**Impact**: More verbose, but more control

---

## 📚 Summary

### Configuration Priority

```
1. Per-Action Config (highest priority)
2. Application-Wide Config
3. Default (lowest priority)
```

### When to Use Each Level

| Level | Use When |
|-------|----------|
| **Default** | Simple apps, prototyping, all mutations similar |
| **Application** | Production apps, consistent behavior needed |
| **Per-Action** | Complex apps, different needs per mutation |

### Key Takeaways

- ✅ **Defaults work great** - No config needed for most apps
- ✅ **Application config reduces repetition** - Single source of truth
- ✅ **Per-action overrides provide flexibility** - Special cases handled
- ✅ **Configs are additive** - Can mix and match
- ✅ **Easy to migrate** - Start simple, add config as needed

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Related**: `GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md`
