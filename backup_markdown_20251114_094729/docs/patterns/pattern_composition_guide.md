# Pattern Composition Guide

**Status**: ✅ Complete - Pattern composition documented
**Last Updated**: 2025-11-12
**Related**: Phase C - Three-Tier Architecture

---

## 📚 Overview

Pattern composition is the process of combining multiple **domain patterns** (Tier 2) to create complex business entities. This guide shows how to compose patterns manually or extend entity templates with additional patterns.

**Composition Methods**:
1. **Template Extension**: Start with entity template, add patterns
2. **Manual Composition**: Build entity from scratch with patterns
3. **Pattern Inheritance**: Create derived patterns

---

## 🏗️ Composition Architecture

### Three-Tier System
```
Tier 1: Primitives (35 actions)
  ↓ composed into
Tier 2: Domain Patterns (15 patterns)
  ↓ composed into
Tier 3: Entity Templates (22 templates)
```

### Composition Rules
- **Patterns are composable**: Multiple patterns can be applied to one entity
- **Conflict resolution**: Later patterns override earlier ones
- **Dependency management**: Patterns can depend on other patterns
- **Field merging**: Fields from multiple patterns are combined
- **Action merging**: Actions are combined with name collision resolution

---

## 📝 Template Extension

### Method 1: Extend Entity Template

Start with a base template and add additional patterns:

```yaml
entity: Contact
extends: crm.contact_template  # Base template (state_machine + audit_trail + soft_delete)

# Add additional patterns
patterns:
  - name: tagging
    config:
      allow_custom_tags: true
      tag_categories: [industry, region, vip_status]

  - name: commenting
    config:
      allow_threading: true
      allow_mentions: true

  - name: notification
    config:
      channels: [email, in_app]
      notification_events: [state_changed, tagged, commented]

  - name: file_attachment
    config:
      allowed_types: [pdf, doc, jpg, png]
      max_file_size: 10485760  # 10MB

# Add custom fields
fields:
  vip_status: enum(normal, gold, platinum)
  last_contact_date: timestamp
  preferred_language: text

# Add custom actions
actions:
  - name: promote_to_vip
    description: Promote contact to VIP status
    steps:
      - validate: state = 'customer'
      - update: Contact SET vip_status = 'gold' WHERE id = $id
      - notify: sales_team "New VIP customer: {first_name} {last_name}"
```

**Result**: Contact entity with 25+ patterns applied + custom fields/actions

---

### Method 2: Selective Pattern Override

Override specific pattern configurations:

```yaml
entity: Order
extends: ecommerce.order_template

# Override state machine configuration
patterns:
  - name: state_machine
    config:
      states: [draft, submitted, approved, processing, shipped, delivered, cancelled]
      transitions:
        draft->submitted: {}
        submitted->approved: {guard: "amount < 10000"}  # Auto-approve small orders
        submitted->cancelled: {}
        approved->processing: {}
        processing->shipped: {}
        shipped->delivered: {}
        # Add returns
        delivered->returned: {guard: "days_since_delivery < 30"}

  # Add approval workflow for large orders
  - name: approval_workflow
    config:
      stages:
        - name: manager_approval
          role: sales_manager
          condition: "amount >= 10000"
        - name: director_approval
          role: sales_director
          condition: "amount >= 50000"
```

---

## 🔧 Manual Composition

### Method 3: Build from Scratch

Create entities by composing patterns manually:

```yaml
entity: BlogPost
description: Blog post with publishing workflow

# No template - build from patterns
patterns:
  - name: state_machine
    config:
      states: [draft, review, published, archived]
      transitions:
        draft->review: {}
        review->draft: {}  # Send back for edits
        review->published: {}
        published->archived: {}

  - name: audit_trail
    config:
      track_versions: true

  - name: soft_delete
    config: {}

  - name: commenting
    config:
      allow_threading: true
      allow_mentions: false

  - name: tagging
    config:
      allow_custom_tags: true
      tag_categories: [category, topic]

  - name: search_optimization
    config:
      search_fields: [title, content, tags]

# Define core fields
fields:
  title: text
  slug: text
  content: text
  excerpt: text
  author_id: uuid
  published_at: timestamp
  featured_image: text

# Define core actions
actions:
  - name: publish
    description: Publish the blog post
    steps:
      - validate: state = 'review'
      - update: BlogPost SET published_at = NOW(), state = 'published' WHERE id = $id
      - notify: subscribers "New blog post: {title}"

  - name: submit_for_review
    description: Submit for editorial review
    steps:
      - validate: state = 'draft'
      - call: transition_to {target_state: review}
      - notify: editors "Blog post ready for review: {title}"
```

---

## 🎯 Advanced Composition

### Method 4: Pattern Inheritance

Create derived patterns that extend base patterns:

```yaml
# Define a custom pattern that extends state_machine
patterns:
  - name: order_workflow
    extends: state_machine
    config:
      states: [pending, confirmed, paid, processing, shipped, delivered, cancelled, returned]
      transitions:
        pending->confirmed: {guard: "inventory_available"}
        confirmed->paid: {guard: "payment_processed"}
        paid->processing: {}
        processing->shipped: {guard: "items_packed"}
        shipped->delivered: {guard: "tracking_delivered"}
        delivered->returned: {guard: "days_since_delivery < 30"}
        # Cancellation from any state
        pending->cancelled: {}
        confirmed->cancelled: {}
        paid->cancelled: {guard: "refund_processed"}

      # Add custom guards
      guards:
        inventory_available: "check_inventory(items)"
        payment_processed: "payment_gateway.verify($payment_id)"
        items_packed: "warehouse.packed($order_id)"
        tracking_delivered: "shipping.tracking_status($tracking_number) = 'delivered'"
        refund_processed: "payment_gateway.refund($payment_id)"
```

---

### Method 5: Conditional Pattern Application

Apply patterns based on entity properties:

```yaml
entity: Subscription
description: Subscription with conditional features

patterns:
  - name: state_machine
    config:
      states: [trial, active, past_due, cancelled, suspended]

  - name: audit_trail

  # Apply payment pattern only for paid subscriptions
  - name: payment_processing
    condition: "plan_type != 'free'"
    config:
      supported_methods: [credit_card, paypal, bank_transfer]

  # Apply trial management only for trial subscriptions
  - name: trial_management
    condition: "plan_type = 'trial'"
    config:
      trial_days: 14
      auto_convert: true

  # Apply billing only for recurring subscriptions
  - name: recurring_billing
    condition: "billing_cycle IN ('monthly', 'yearly')"
    config:
      billing_cycle: "{billing_cycle}"
      proration_enabled: true
```

---

## 🔍 Conflict Resolution

### Field Conflicts

When patterns define the same field:

```yaml
entity: Product

patterns:
  - name: audit_trail
    # Defines: created_at (timestamp), updated_at (timestamp)

  - name: soft_delete
    # Defines: deleted_at (timestamp)

  - name: state_machine
    # Defines: state (enum), state_changed_at (timestamp)

# Resolution: All fields are merged
# Result: Product has created_at, updated_at, deleted_at, state, state_changed_at
```

### Action Conflicts

When patterns define actions with the same name:

```yaml
entity: Order

patterns:
  - name: state_machine
    # Defines: transition_to(id, target_state, user_id)

  - name: custom_transitions
    # Also defines: transition_to(id, target_state, user_id, reason)

# Resolution: Last pattern wins, but can be customized
actions:
  - name: transition_to
    # Override the generated action
    parameters:
      - name: id
      - name: target_state
      - name: user_id
      - name: reason  # Add custom parameter
    steps:
      - validate: reason IS NOT NULL
      - call: state_machine.transition_to {id: $id, target_state: $target_state, user_id: $user_id}
      - insert: transition_log {reason: $reason}
```

---

## 📊 Composition Examples

### Example 1: E-Commerce Product

```yaml
entity: Product
extends: ecommerce.product_template

patterns:
  # Additional patterns beyond template
  - name: internationalization
    config:
      localized_fields: [name, description]
      default_locale: en

  - name: inventory_management
    config:
      track_locations: true
      low_stock_alerts: true

  - name: pricing_strategy
    config:
      multiple_price_levels: true
      discount_support: true
```

### Example 2: Healthcare Patient

```yaml
entity: Patient
extends: healthcare.patient_template

patterns:
  # Add compliance patterns
  - name: hipaa_compliance
    config:
      audit_all_access: true
      data_retention_years: 7

  - name: emergency_access
    config:
      emergency_roles: [doctor, nurse, admin]
      audit_emergency_access: true

  # Add care coordination
  - name: care_team
    config:
      team_roles: [primary_care, specialist, nurse, pharmacist]
      care_plan_tracking: true
```

### Example 3: Financial Transaction

```yaml
entity: Transaction
extends: finance.transaction_template

patterns:
  # Add regulatory compliance
  - name: regulatory_reporting
    config:
      report_types: [sar, ctr, kyc]
      retention_years: 5

  - name: fraud_detection
    config:
      risk_scoring: true
      velocity_checks: true
      geo_fencing: true

  # Add multi-currency support
  - name: currency_conversion
    config:
      base_currency: USD
      supported_currencies: [USD, EUR, GBP, JPY]
      real_time_rates: true
```

---

## 🔧 Composition Tools

### CLI Commands

```bash
# List available patterns
specql patterns list

# Show pattern details
specql patterns show state_machine

# Validate composition
specql patterns validate entity.yaml

# Preview composed entity
specql patterns compose entity.yaml --preview

# Generate with composition
specql generate entity.yaml --compose
```

### API Usage

```python
from src.pattern_library.api import PatternLibrary

library = PatternLibrary()

# Compose patterns manually
result = library.compose_patterns(
    entity_name="Contact",
    patterns=[
        {"pattern": "audit_trail", "params": {}},
        {"pattern": "state_machine", "params": {
            "states": ["lead", "customer"],
            "transitions": {"lead->customer": {}}
        }},
        {"pattern": "soft_delete", "params": {}}
    ]
)

print(result)  # Dict with fields, actions, etc.
```

---

## 📈 Best Practices

### 1. Start Simple
Begin with entity templates, then add patterns incrementally:

```yaml
# Phase 1: Basic template
entity: Contact
extends: crm.contact_template

# Phase 2: Add communication
patterns:
  - name: commenting
  - name: notification

# Phase 3: Add advanced features
patterns:
  - name: file_attachment
  - name: internationalization
```

### 2. Group Related Patterns
Organize patterns by business concern:

```yaml
patterns:
  # Core business logic
  - name: state_machine
  - name: audit_trail

  # Data management
  - name: soft_delete
  - name: validation_chain

  # User experience
  - name: search_optimization
  - name: tagging

  # Communication
  - name: commenting
  - name: notification
```

### 3. Use Configuration Wisely
Configure patterns rather than overriding:

```yaml
# Good: Configure the pattern
patterns:
  - name: state_machine
    config:
      states: [draft, published, archived]
      initial_state: draft

# Avoid: Override generated actions unnecessarily
actions:
  - name: transition_to  # Let the pattern handle this
```

### 4. Test Composition
Always test pattern interactions:

```bash
# Test individual patterns
specql test patterns/ --pattern audit_trail

# Test composition
specql test entity.yaml --integration

# Test performance
specql benchmark entity.yaml --patterns
```

---

## 🚨 Common Issues

### Issue 1: Field Name Conflicts
**Problem**: Two patterns define the same field name
**Solution**: Use field aliases or customize field names

```yaml
patterns:
  - name: audit_trail
    config:
      created_at_field: created_timestamp  # Avoid conflict
```

### Issue 2: Action Name Conflicts
**Problem**: Two patterns define actions with the same name
**Solution**: Rename actions or create wrapper actions

```yaml
actions:
  - name: custom_transition
    steps:
      - call: state_machine.transition_to
      - call: audit_trail.log_transition
```

### Issue 3: Performance Issues
**Problem**: Too many patterns slow down queries
**Solution**: Use pattern selectively and optimize indexes

```yaml
# Only apply heavy patterns where needed
patterns:
  - name: search_optimization
    condition: "entity_size > 10000"  # Only for large tables
```

---

## 📊 Composition Metrics

**Composition Complexity**:
- **Simple**: 1-3 patterns (80% of entities)
- **Medium**: 4-7 patterns (15% of entities)
- **Complex**: 8+ patterns (5% of entities)

**Performance Impact**:
- Each pattern adds ~10-50ms to generation time
- Field count increases ~5-20 fields per pattern
- Action count increases ~2-10 actions per pattern

**Maintenance Cost**:
- Simple compositions: Low (template updates)
- Custom compositions: Medium (manual updates)
- Complex compositions: High (careful testing required)

---

## 🚀 Next Steps

Pattern composition enables unlimited business logic combinations. Learn how to:
- **[Template Customization Guide](template_customization_guide.md)**: Extend templates for specific needs
- **[Migration Guide](../guides/migration_pattern_library.md)**: Migrate existing entities to patterns
- **[Performance Guide](../guides/performance_optimization.md)**: Optimize pattern-heavy entities

---

**Status**: ✅ **Complete** - Pattern composition fully documented
**Next**: Create template customization guide