# Choosing Patterns for Your Application

**Purpose**: Decision framework to help you choose which patterns (Cascade, Audit, CDC) you need for each application you build with SpecQL.

**Audience**: Developers building multiple applications with different requirements

---

## 🎯 Quick Decision Matrix

Use this matrix to quickly identify which patterns you need:

| Your App Type | Cascade | Audit | CDC | Reasoning |
|---------------|---------|-------|-----|-----------|
| **Simple CRUD app** (todo list, blog) | ✅ Yes | ⚠️ Maybe | ❌ No | Cache updates needed; audit if multi-user; no microservices |
| **SaaS Product** (project management, CRM) | ✅ Yes | ✅ Yes | ⚠️ Maybe | Cache + compliance required; CDC if scaling |
| **E-commerce** | ✅ Yes | ✅ Yes | ✅ Yes | All patterns for inventory, audit, and integrations |
| **Internal Tool** (admin dashboard) | ✅ Yes | ✅ Yes | ❌ No | Cache + audit trail for admin actions |
| **Mobile App Backend** | ✅ Yes | ⚠️ Maybe | ❌ No | Cache critical; audit if sensitive data |
| **Microservices Architecture** | ✅ Yes | ✅ Yes | ✅ Yes | All patterns for distributed systems |
| **Analytics Platform** | ✅ Yes | ⚠️ Maybe | ✅ Yes | Cache + events for data pipelines |
| **Healthcare/Finance** | ✅ Yes | ✅ Yes | ✅ Yes | Compliance mandatory; events for integrations |

Legend:
- ✅ **Yes** - Strongly recommended
- ⚠️ **Maybe** - Depends on specific requirements
- ❌ **No** - Probably not needed

---

## 📋 Pattern-by-Pattern Decision Guide

### Pattern 1: GraphQL Cascade

**What it does**: Returns all affected entities in mutation response for immediate cache updates

**When to use**:
- ✅ You have a GraphQL frontend (Apollo, Relay, URQL)
- ✅ Users expect instant UI updates
- ✅ Mutations have side effects (counters, stats, relationships)
- ✅ You want to avoid manual cache management

**When NOT to use**:
- ❌ You're building a REST API only (not GraphQL)
- ❌ Your app has no frontend (pure backend service)
- ❌ Mutations never affect multiple entities

**Cost**: ~5-10ms per mutation (negligible)

**Recommendation**: **Use for 95% of apps** - it's lightweight and incredibly useful

---

### Pattern 2: Audit Trail with Cascade

**What it does**: Stores complete mutation history including all side effects in PostgreSQL

**When to use**:
- ✅ **Compliance required** (HIPAA, SOC2, GDPR, financial regulations)
- ✅ **Multi-user apps** where you need to know "who changed what"
- ✅ **Debugging complex issues** - "Why did this value change?"
- ✅ **Customer support** - "Show me what happened to user X"
- ✅ **Data integrity** - Need to reconstruct past states
- ✅ **B2B SaaS** - Customers often require audit trails

**When NOT to use**:
- ❌ Simple personal projects or prototypes
- ❌ High-volume logging apps (use CDC instead)
- ❌ Temporary data that's never audited

**Cost**: ~2-5ms per mutation + storage

**Recommendation**: **Use for any production SaaS or multi-user application**

---

### Pattern 3: CDC Outbox

**What it does**: Streams mutation events to Kafka for async processing by microservices

**When to use**:
- ✅ **Microservices architecture** - Need to notify other services
- ✅ **Event-driven architecture** - Services react to domain events
- ✅ **Data pipelines** - Sync to warehouse, search indexes, caches
- ✅ **Third-party integrations** - Webhooks, external APIs
- ✅ **Analytics** - Real-time metrics and dashboards
- ✅ **Notifications** - Email, SMS, push notifications
- ✅ **Eventually consistent reads** - CQRS patterns

**When NOT to use**:
- ❌ Monolithic architecture with no external services
- ❌ Simple apps with no async processing
- ❌ No infrastructure for Kafka/messaging

**Cost**: ~5-10ms per mutation + Kafka infrastructure

**Recommendation**: **Use when you need to scale beyond a monolith**

---

## 🏗️ Multi-App Strategy

Since you're building **multiple apps**, here's how to think about it:

### Strategy 1: Start Minimal, Add As Needed

**Phase 1: Build All Apps with Cascade Only**
```yaml
# All apps start with this:
entity: Post
actions:
  - name: create_post
    impact:
      primary: { entity: Post, operation: CREATE }
      side_effects: [{ entity: User, operation: UPDATE }]

    # No audit or CDC yet
```

**Benefits**:
- ✅ Consistent foundation across all apps
- ✅ GraphQL cache updates work everywhere
- ✅ Zero infrastructure overhead
- ✅ Can add audit/CDC later per-app

**Phase 2: Add Audit to Production Apps**
```yaml
# When app goes to production, add:
actions:
  - name: create_post
    impact: { ... }

    audit:
      include_cascade: true  # ← Add this
```

**Phase 3: Add CDC to Apps That Need It**
```yaml
# For apps with microservices/integrations:
actions:
  - name: create_post
    impact: { ... }
    audit: { include_cascade: true }

    cdc:
      enabled: true  # ← Add this
      event_type: PostCreated
```

---

### Strategy 2: App Templates by Type

Create **SpecQL configuration templates** for different app types:

#### Template A: Simple App (Blog, Portfolio)
```yaml
# config/simple_app_template.yaml

# Patterns:
patterns:
  cascade: enabled       # ← GraphQL cache updates
  audit: disabled        # ← Not needed for simple apps
  cdc: disabled          # ← No microservices

# Use for:
# - Personal blogs
# - Portfolios
# - Small internal tools
# - Prototypes
```

#### Template B: SaaS Product (CRM, Project Management)
```yaml
# config/saas_product_template.yaml

# Patterns:
patterns:
  cascade: enabled       # ← GraphQL cache updates
  audit:
    enabled: true        # ← Compliance & debugging
    include_cascade: true
    retention: 7 years   # ← Compliance requirement
  cdc: disabled          # ← Start without, add later if needed

# Use for:
# - B2B SaaS products
# - Multi-tenant applications
# - Team collaboration tools
# - Customer-facing apps
```

#### Template C: E-commerce / Enterprise
```yaml
# config/enterprise_template.yaml

# Patterns:
patterns:
  cascade: enabled       # ← GraphQL cache updates
  audit:
    enabled: true        # ← Required for compliance
    include_cascade: true
    retention: 10 years
  cdc:
    enabled: true        # ← Microservices integration
    kafka_bootstrap: kafka:9092
    topics:
      - orders
      - inventory
      - notifications

# Use for:
# - E-commerce platforms
# - Healthcare systems
# - Financial services
# - Large-scale enterprise apps
```

#### Template D: Microservices Backend
```yaml
# config/microservices_template.yaml

# Patterns:
patterns:
  cascade: enabled       # ← Even for backend-only
  audit:
    enabled: true        # ← Service-to-service audit
    include_cascade: true
  cdc:
    enabled: true        # ← Core pattern for microservices
    kafka_bootstrap: kafka:9092

# Use for:
# - Distributed systems
# - Event-driven architectures
# - Service mesh environments
# - Cloud-native apps
```

---

## 🎯 Real-World App Examples

### Example 1: Personal Blog

**Requirements**:
- Single author
- GraphQL frontend (Next.js)
- No compliance needs
- No microservices

**Recommended Patterns**:
```yaml
patterns:
  cascade: ✅ enabled    # Apollo cache updates
  audit: ❌ disabled     # Overkill for personal blog
  cdc: ❌ disabled       # No external services
```

**Reasoning**: Cascade gives you instant UI updates. Audit/CDC would be unnecessary overhead.

---

### Example 2: Team Task Manager (SaaS)

**Requirements**:
- Multi-user (teams of 5-50)
- GraphQL frontend (React + Apollo)
- Need to know "who completed this task"
- Planning to add Slack integration later

**Recommended Patterns**:
```yaml
patterns:
  cascade: ✅ enabled           # Instant task updates
  audit:
    enabled: ✅ true            # Track who did what
    include_cascade: true
  cdc: ⚠️ disabled (for now)   # Add when Slack integration ready
```

**Reasoning**:
- Cascade: Essential for multi-user real-time collaboration
- Audit: "Who marked this done?" is a common question
- CDC: Not yet, but easy to add when integrations are needed

**Migration Path**:
```yaml
# Later, when adding Slack integration:
cdc:
  enabled: true
  event_type: TaskCompleted  # Triggers Slack notification
```

---

### Example 3: E-commerce Platform

**Requirements**:
- High transaction volume
- Inventory management
- Order fulfillment (separate microservice)
- Email notifications
- Analytics dashboard
- Fraud detection system
- Payment processing (Stripe)
- Financial compliance (PCI-DSS)

**Recommended Patterns**:
```yaml
patterns:
  cascade: ✅ enabled           # Cart, checkout UI updates
  audit:
    enabled: ✅ true            # Financial compliance
    include_cascade: true
    retention: 7 years          # Legal requirement
  cdc:
    enabled: ✅ true            # Critical for architecture
    event_type: OrderPlaced
```

**Why All Three**:

**Cascade**:
- Customer adds item → cart count updates instantly
- Order placed → inventory count updates in UI
- Payment confirmed → order status updates

**Audit**:
- Compliance: "Show all changes to order #12345"
- Fraud investigation: "What happened with this suspicious order?"
- Refund disputes: "Prove what the customer ordered"

**CDC (Outbox Events)**:
```
OrderPlaced event →
  - Fulfillment service (prepare shipment)
  - Inventory service (decrement stock)
  - Email service (confirmation email)
  - Analytics (conversion tracking)
  - Fraud detection (risk scoring)
  - Warehouse (pick & pack queue)
```

---

### Example 4: Healthcare Patient Portal

**Requirements**:
- HIPAA compliance mandatory
- Doctors + patients + staff
- Integration with labs, pharmacies
- Audit trail required by law
- Real-time updates for medical staff

**Recommended Patterns**:
```yaml
patterns:
  cascade: ✅ enabled           # Critical for medical staff UI
  audit:
    enabled: ✅ true            # HIPAA requirement
    include_cascade: true
    retention: 10 years         # Legal minimum
    encryption: true
  cdc:
    enabled: ✅ true            # Lab/pharmacy integrations
    secure: true                # HIPAA-compliant Kafka
```

**Why All Three**:
- **Cascade**: Doctor updates prescription → UI updates instantly → patient sees it
- **Audit**: "Show me all accesses to patient X's records" (HIPAA requirement)
- **CDC**: Lab results ready → event → notify doctor + update patient portal

---

### Example 5: Mobile App Backend (Fitness Tracker)

**Requirements**:
- Mobile apps (iOS + Android)
- GraphQL API
- Single-user data (no sharing)
- No compliance requirements
- No external integrations yet

**Recommended Patterns**:
```yaml
patterns:
  cascade: ✅ enabled           # Essential for mobile cache
  audit: ❌ disabled            # Not needed for personal fitness data
  cdc: ❌ disabled              # No integrations
```

**Reasoning**:
- **Cascade**: Critical for mobile apps with Apollo/URQL cache
- **Audit**: Overkill for personal fitness data
- **CDC**: Add later if you want to integrate with Apple Health, Strava, etc.

**Future Enhancement**:
```yaml
# When adding Strava integration:
cdc:
  enabled: true
  event_type: WorkoutCompleted  # Sync to Strava
```

---

### Example 6: Analytics Dashboard (Internal Tool)

**Requirements**:
- Admin users only
- Read-heavy (reports, charts)
- Some writes (annotations, settings)
- Need to track who changed what
- Data pipeline to data warehouse

**Recommended Patterns**:
```yaml
patterns:
  cascade: ✅ enabled           # Admin UI updates
  audit:
    enabled: ✅ true            # Track admin changes
    include_cascade: true
  cdc:
    enabled: ✅ true            # Sync to data warehouse
    event_type: MetricAnnotated
```

**Why**:
- **Cascade**: Even admin tools need responsive UIs
- **Audit**: "Who changed this metric definition?" is important
- **CDC**: Events feed data warehouse for historical analysis

---

## 🛠️ Implementation Approach

### Approach 1: Global Configuration

Set defaults for all apps, override per-app:

```yaml
# specql.config.yaml (global defaults)

patterns:
  cascade:
    enabled: true  # Always on by default

  audit:
    enabled: false  # Opt-in per app
    include_cascade: true

  cdc:
    enabled: false  # Opt-in per app
```

```yaml
# apps/saas-app/specql.yaml (override for this app)

patterns:
  audit:
    enabled: true  # ← Override: enable audit for this app
```

---

### Approach 2: Per-Entity Configuration

Different entities in same app can use different patterns:

```yaml
entity: Post
actions:
  - name: create_post
    impact: { ... }

    # Cascade enabled (default)
    audit: { include_cascade: true }  # Enable audit
    cdc: { enabled: true }             # Enable CDC

entity: Comment
actions:
  - name: create_comment
    impact: { ... }

    # Cascade enabled (default)
    # No audit (comments don't need audit trail)
    # No CDC (not critical for events)
```

**Use Case**: In e-commerce app:
- **Order** entity: All patterns (critical data)
- **CartItem** entity: Cascade only (temporary data)
- **Product** entity: Cascade + CDC (inventory events)

---

### Approach 3: Per-Action Configuration

Different actions on same entity can use different patterns:

```yaml
entity: User

actions:
  - name: update_profile
    impact: { ... }
    audit: { include_cascade: true }  # Track profile changes
    # No CDC (not critical)

  - name: change_password
    impact: { ... }
    audit: { include_cascade: true }  # Track for security
    cdc: { enabled: true }             # Alert security service

  - name: update_preferences
    impact: { ... }
    # Cascade only (preferences don't need audit/events)
```

---

## 📊 Cost-Benefit Analysis

### Cascade (Pattern 1)

| Benefit | Cost |
|---------|------|
| Instant UI updates | ~5-10ms per mutation |
| Automatic cache management | ~1KB per response |
| Better UX | Code complexity: Low |
| Works with any GraphQL client | No infrastructure needed |

**ROI**: **Extremely High** - Small cost, huge UX benefit

---

### Audit Trail (Pattern 2)

| Benefit | Cost |
|---------|------|
| Compliance (HIPAA, SOC2) | ~2-5ms per mutation |
| Debugging & support | Storage: ~1-5KB per mutation |
| Legal protection | Schema: 3 extra columns |
| Customer trust | Query overhead: Minimal |

**ROI**: **High for SaaS** - Essential for compliance, minimal overhead

**Storage Calculation**:
- 1,000 mutations/day = ~5MB/day = ~1.8GB/year
- Affordable for most apps

---

### CDC Outbox (Pattern 3)

| Benefit | Cost |
|---------|------|
| Microservices integration | ~5-10ms per mutation |
| Event-driven architecture | Infrastructure: Kafka, Debezium |
| Scalability | Storage: ~2-10KB per event |
| Async processing | Operational complexity: Medium |
| Analytics pipelines | Team knowledge required |

**ROI**: **High for Microservices** - Essential for distributed systems, but requires infrastructure

**When ROI is Negative**:
- Monolithic app with no plans to scale
- No external integrations
- No async processing needs

---

## 🎯 Decision Tree

```
START: Which patterns do I need?
    ↓
┌─────────────────────────────────────┐
│ Do you have a GraphQL frontend?     │
└─────────────┬───────────────────────┘
              │
        Yes ──┴── No → Consider REST API instead
              │
              ↓
    ┌─────────────────────┐
    │ ✅ ENABLE CASCADE   │
    └──────────┬──────────┘
               │
               ↓
    ┌──────────────────────────────────┐
    │ Is this a production app with    │
    │ multiple users or compliance     │
    │ requirements?                    │
    └──────────┬───────────────────────┘
               │
         Yes ──┴── No → Skip audit for now
               │
               ↓
    ┌─────────────────────┐
    │ ✅ ENABLE AUDIT     │
    └──────────┬──────────┘
               │
               ↓
    ┌──────────────────────────────────┐
    │ Do you have microservices or     │
    │ need async processing?           │
    └──────────┬───────────────────────┘
               │
         Yes ──┴── No → Skip CDC for now
               │
               ↓
    ┌─────────────────────┐
    │ ✅ ENABLE CDC       │
    └─────────────────────┘
```

---

## 🚀 Recommended Starting Point

### For Most Apps: Start with Cascade Only

```yaml
# Recommended starting point for ANY app:

entity: YourEntity
actions:
  - name: your_action
    impact:
      primary: { entity: YourEntity, operation: CREATE }
      side_effects: [ ... ]

    # ✅ Cascade: Always enabled (automatic from impact)
    # ⚠️ Audit: Add when app goes to production
    # ⚠️ CDC: Add when you need microservices
```

**Why**:
- ✅ Zero risk - Cascade is lightweight and always useful
- ✅ Easy to add audit/CDC later without breaking changes
- ✅ Keeps initial setup simple
- ✅ Gives you time to evaluate if you need more

### Upgrade Path

```
Week 1-4: Build with Cascade
    ↓
Week 5: App going to production?
    ↓
Add Audit Trail (1 hour to enable)
    ↓
Month 3: Need microservices?
    ↓
Add CDC Outbox (1 day to setup infrastructure)
```

---

## 📝 Configuration Checklist

Use this checklist when starting a new app:

### ✅ App Requirements Checklist

- [ ] **Frontend Framework**: React / Vue / Angular / Next.js / ...
- [ ] **GraphQL Client**: Apollo / Relay / URQL / ...
- [ ] **User Type**: Single-user / Multi-user / Team / Enterprise
- [ ] **Compliance Needs**: None / GDPR / HIPAA / SOC2 / PCI-DSS / ...
- [ ] **Architecture**: Monolith / Microservices / Serverless / ...
- [ ] **Integrations**: None / Third-party APIs / External services / ...
- [ ] **Scale**: Prototype / Startup / Growth / Enterprise
- [ ] **Budget**: Tight / Moderate / Enterprise

### ✅ Pattern Selection

Based on answers above, select patterns:

- [ ] **Cascade**: YES (always recommended for GraphQL apps)
- [ ] **Audit**: YES / NO / MAYBE
  - YES if: Compliance required, multi-user, production SaaS
  - NO if: Personal project, prototype, temporary app
  - MAYBE if: Unsure - start without, add later
- [ ] **CDC**: YES / NO / LATER
  - YES if: Microservices architecture, event-driven, integrations
  - NO if: Monolithic app, no async processing
  - LATER if: Might need in future - design for it, enable later

---

## 🎓 Summary: Rules of Thumb

### Rule 1: Cascade is Almost Always Worth It
- Cost: ~5-10ms
- Benefit: Automatic cache updates
- **Use for**: 95% of GraphQL apps

### Rule 2: Audit is Worth It for Production SaaS
- Cost: ~2-5ms + storage
- Benefit: Compliance, debugging, customer support
- **Use for**: Any app with paying customers

### Rule 3: CDC is Worth It When You Need It
- Cost: Infrastructure + operational complexity
- Benefit: Microservices, event-driven architecture
- **Use for**: Apps that need to scale beyond monolith

### Rule 4: Start Small, Grow As Needed
- ✅ All apps: Start with Cascade
- ✅ Production apps: Add Audit
- ✅ Scaled apps: Add CDC when needed

### Rule 5: Patterns are Additive
- Each pattern adds value
- No conflicts between patterns
- Can enable/disable per-entity or per-action
- Easy to add later without breaking changes

---

## 🔗 Next Steps

1. **Identify your app type** using the Quick Decision Matrix
2. **Choose your patterns** using the Decision Tree
3. **Follow implementation plan**:
   - Phase 1 (Cascade): `docs/planning/GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md`
   - Phase 2 (Audit): `docs/planning/CASCADE_AUDIT_CDC_PHASES_2_3.md` (Section: Phase 2)
   - Phase 3 (CDC): `docs/planning/CASCADE_AUDIT_CDC_PHASES_2_3.md` (Section: Phase 3)

4. **Review complete system**: `docs/planning/COMPLETE_SYSTEM_SYNTHESIS.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**For Questions**: See FAQ in `COMPLETE_SYSTEM_SYNTHESIS.md`
