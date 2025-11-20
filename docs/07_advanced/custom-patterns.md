# Custom Patterns Guide

> **Create reusable patterns for common business logic—DRY principles at scale**

## Overview

SpecQL patterns are reusable templates that encapsulate common database patterns. Instead of repeating the same logic across entities, define patterns once and apply them declaratively.

**Benefits**:
- ✅ DRY (Don't Repeat Yourself) - Write once, use everywhere
- ✅ Consistency - Same pattern generates same code
- ✅ Maintainability - Update pattern, all entities update
- ✅ Best practices - Encode expertise into patterns

---

## Quick Start

### Using Built-in Patterns

```yaml
entity: Product
schema: catalog

patterns:
  - audit_trail       # Adds created_at, updated_at, created_by, updated_by
  - soft_delete       # Adds deleted_at, is_deleted, soft delete logic
  - multi_tenant      # Adds tenant_id, RLS policies

fields:
  name: text!
  price: money!
```

**Generated fields automatically**:
```sql
CREATE TABLE catalog.tb_product (
    -- Your fields
    name TEXT NOT NULL,
    price NUMERIC(19,4) NOT NULL,

    -- From audit_trail pattern
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,

    -- From soft_delete pattern
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    -- From multi_tenant pattern
    tenant_id UUID NOT NULL
);
```

---

## Built-in Patterns

### audit_trail

**Purpose**: Track who created/updated records and when

**Adds**:
- `created_at: datetime!` - Timestamp of creation
- `updated_at: datetime!` - Timestamp of last update
- `created_by: uuid` - User who created record
- `updated_by: uuid` - User who last updated record

**Auto-generated triggers**:
```sql
CREATE TRIGGER trg_tb_product_updated_at
    BEFORE UPDATE ON catalog.tb_product
    FOR EACH ROW
    EXECUTE FUNCTION core.update_updated_at_column();

CREATE TRIGGER trg_tb_product_updated_by
    BEFORE UPDATE ON catalog.tb_product
    FOR EACH ROW
    EXECUTE FUNCTION core.update_updated_by_column();
```

**Usage**:
```yaml
entity: Contact
patterns:
  - audit_trail

fields:
  email: email!
```

---

### soft_delete

**Purpose**: Mark records as deleted instead of removing them

**Adds**:
- `deleted_at: datetime` - Timestamp of soft deletion
- `is_deleted: boolean = false` - Deletion flag

**Auto-generated functions**:
```sql
-- Soft delete function
CREATE FUNCTION catalog.soft_delete_product(p_id UUID)
RETURNS catalog.tb_product AS $$
    UPDATE catalog.tb_product
    SET deleted_at = NOW(),
        is_deleted = TRUE,
        updated_at = NOW()
    WHERE id = p_id AND is_deleted = FALSE
    RETURNING *;
$$ LANGUAGE SQL;

-- Restore function
CREATE FUNCTION catalog.restore_product(p_id UUID)
RETURNS catalog.tb_product AS $$
    UPDATE catalog.tb_product
    SET deleted_at = NULL,
        is_deleted = FALSE,
        updated_at = NOW()
    WHERE id = p_id AND is_deleted = TRUE
    RETURNING *;
$$ LANGUAGE SQL;
```

**Auto-filters in queries**:
```sql
-- All generated queries auto-filter deleted records
CREATE VIEW catalog.vw_product AS
SELECT * FROM catalog.tb_product
WHERE is_deleted = FALSE;
```

**Usage**:
```yaml
entity: Contact
patterns:
  - soft_delete

actions:
  - name: delete_contact
    steps:
      - call: soft_delete_contact, args: {id: $contact_id}
```

---

### multi_tenant

**Purpose**: Isolate data by tenant in SaaS applications

**Adds**:
- `tenant_id: uuid!` - Tenant identifier
- Row-level security (RLS) policies
- Automatic tenant filtering

**Auto-generated security**:
```sql
ALTER TABLE catalog.tb_product ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their tenant's data
CREATE POLICY tenant_isolation ON catalog.tb_product
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Policy: Inserts must include current tenant
CREATE POLICY tenant_insert ON catalog.tb_product
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

**Auto-injection in actions**:
```sql
-- All inserts/updates automatically inject tenant_id
INSERT INTO catalog.tb_product (name, price, tenant_id)
VALUES ('Product', 99.99, current_setting('app.current_tenant_id')::UUID);
```

**Usage**:
```yaml
entity: Contact
patterns:
  - multi_tenant

# tenant_id automatically added to all queries/mutations
```

---

### versioning

**Purpose**: Track historical changes to records

**Adds**:
- `version: integer = 1` - Version counter
- `version_history` table - Historical snapshots

**Auto-generated history table**:
```sql
CREATE TABLE catalog.tb_product_history (
    history_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    pk_product INTEGER NOT NULL,
    version INTEGER NOT NULL,
    snapshot JSONB NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by UUID,

    CONSTRAINT fk_product_history
        FOREIGN KEY (pk_product)
        REFERENCES catalog.tb_product(pk_product)
        ON DELETE CASCADE
);

CREATE INDEX idx_tb_product_history_product ON catalog.tb_product_history(pk_product);
CREATE INDEX idx_tb_product_history_version ON catalog.tb_product_history(version);
```

**Auto-generated triggers**:
```sql
CREATE TRIGGER trg_tb_product_version
    BEFORE UPDATE ON catalog.tb_product
    FOR EACH ROW
    EXECUTE FUNCTION core.increment_version_and_save_history();
```

**Usage**:
```yaml
entity: Product
patterns:
  - versioning

actions:
  - name: get_product_history
    params:
      product_id: uuid!
    steps:
      - query: |
          SELECT * FROM catalog.tb_product_history
          WHERE pk_product = product_pk($product_id)
          ORDER BY version DESC
        result: $history
      - return: $history
```

---

### hierarchical

**Purpose**: Tree structures with parent/child relationships

**Adds**:
- `parent_id: uuid` - Self-reference to parent
- `path: text` - Materialized path (e.g., `/1/5/12/`)
- `depth: integer` - Depth in hierarchy

**Auto-generated functions**:
```sql
-- Get all children (recursive)
CREATE FUNCTION catalog.get_category_children(p_parent_id UUID)
RETURNS SETOF catalog.tb_category AS $$
    WITH RECURSIVE children AS (
        SELECT * FROM catalog.tb_category
        WHERE id = p_parent_id

        UNION ALL

        SELECT c.* FROM catalog.tb_category c
        INNER JOIN children p ON c.fk_parent = category_pk(p.id)
    )
    SELECT * FROM children;
$$ LANGUAGE SQL STABLE;

-- Get all ancestors
CREATE FUNCTION catalog.get_category_ancestors(p_id UUID)
RETURNS SETOF catalog.tb_category AS $$
    WITH RECURSIVE ancestors AS (
        SELECT * FROM catalog.tb_category
        WHERE id = p_id

        UNION ALL

        SELECT p.* FROM catalog.tb_category p
        INNER JOIN ancestors c ON p.pk_category = c.fk_parent
    )
    SELECT * FROM ancestors;
$$ LANGUAGE SQL STABLE;
```

**Usage**:
```yaml
entity: Category
patterns:
  - hierarchical

fields:
  name: text!
  description: text
```

---

### state_machine

**Purpose**: Enforce valid state transitions

**Requires**:
- `status` field with enum type

**Auto-generated validation**:
```sql
-- Transition validation function
CREATE FUNCTION catalog.validate_product_status_transition(
    p_from_status TEXT,
    p_to_status TEXT
) RETURNS BOOLEAN AS $$
    SELECT CASE
        WHEN p_from_status = 'draft' THEN p_to_status IN ('pending_review', 'archived')
        WHEN p_from_status = 'pending_review' THEN p_to_status IN ('approved', 'rejected', 'draft')
        WHEN p_from_status = 'approved' THEN p_to_status IN ('published', 'archived')
        WHEN p_from_status = 'published' THEN p_to_status IN ('archived')
        WHEN p_from_status = 'rejected' THEN p_to_status IN ('draft', 'archived')
        WHEN p_from_status = 'archived' THEN p_to_status IN ('draft')
        ELSE FALSE
    END;
$$ LANGUAGE SQL IMMUTABLE;

-- Trigger to enforce transitions
CREATE TRIGGER trg_tb_product_status_transition
    BEFORE UPDATE ON catalog.tb_product
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION core.enforce_state_machine_transition(
        'validate_product_status_transition'
    );
```

**Configuration**:
```yaml
entity: Product
patterns:
  - state_machine:
      field: status
      transitions:
        draft: [pending_review, archived]
        pending_review: [approved, rejected, draft]
        approved: [published, archived]
        published: [archived]
        rejected: [draft, archived]
        archived: [draft]

fields:
  name: text!
  status: enum(draft, pending_review, approved, rejected, published, archived) = 'draft'
```

---

### event_sourcing

**Purpose**: Store all changes as immutable events

**Adds**:
- `events` table - Event log
- Projection functions - Rebuild state from events

**Auto-generated event table**:
```sql
CREATE TABLE catalog.tb_product_events (
    event_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    pk_product INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL,
    occurred_at TIMESTAMP DEFAULT NOW(),
    occurred_by UUID,

    CONSTRAINT fk_product_events
        FOREIGN KEY (pk_product)
        REFERENCES catalog.tb_product(pk_product)
        ON DELETE CASCADE
);

CREATE INDEX idx_tb_product_events_product ON catalog.tb_product_events(pk_product);
CREATE INDEX idx_tb_product_events_type ON catalog.tb_product_events(event_type);
CREATE INDEX idx_tb_product_events_time ON catalog.tb_product_events(occurred_at);
```

**Usage**:
```yaml
entity: Product
patterns:
  - event_sourcing

actions:
  - name: change_price
    params:
      product_id: uuid!
      new_price: money!
    steps:
      - insert: ProductEvent VALUES (
          product: $product_id,
          event_type: 'price_changed',
          event_data: json({
            old_price: $product.price,
            new_price: $new_price
          })
        )
      - update: Product SET price = $new_price
```

---

## Creating Custom Patterns

### Pattern Definition File

**Location**: `patterns/custom/my_pattern.yaml`

```yaml
pattern: approval_workflow
description: Two-stage approval workflow with comments

fields:
  approval_status: enum(pending, first_approved, final_approved, rejected) = 'pending'
  first_approver: ref(User)
  first_approved_at: datetime
  first_approval_comment: text
  final_approver: ref(User)
  final_approved_at: datetime
  final_approval_comment: text
  rejection_reason: text

actions:
  - name: first_approve
    params:
      comment: text
    steps:
      - validate: approval_status = 'pending'
        error: "invalid_state"
      - update: ENTITY SET
          approval_status = 'first_approved',
          first_approver = current_user_id(),
          first_approved_at = NOW(),
          first_approval_comment = $comment

  - name: final_approve
    params:
      comment: text
    steps:
      - validate: approval_status = 'first_approved'
        error: "invalid_state"
      - update: ENTITY SET
          approval_status = 'final_approved',
          final_approver = current_user_id(),
          final_approved_at = NOW(),
          final_approval_comment = $comment

  - name: reject
    params:
      reason: text!
    steps:
      - validate: approval_status IN ('pending', 'first_approved')
        error: "invalid_state"
      - update: ENTITY SET
          approval_status = 'rejected',
          rejection_reason = $reason

constraints:
  - check: |
      (approval_status = 'first_approved' AND first_approver IS NOT NULL) OR
      (approval_status = 'final_approved' AND final_approver IS NOT NULL) OR
      (approval_status NOT IN ('first_approved', 'final_approved'))
    name: valid_approval_state
```

---

### Using Custom Patterns

```yaml
entity: PurchaseOrder
schema: procurement

patterns:
  - audit_trail
  - approval_workflow  # Custom pattern

fields:
  vendor: ref(Vendor)!
  total_amount: money!
  description: text!
```

**Result**: PurchaseOrder gets all approval workflow fields and actions automatically.

---

## Advanced Pattern Features

### Parameterized Patterns

**Pattern Definition**:
```yaml
pattern: rate_limiting
description: Limit operations per time window

parameters:
  max_operations: integer!
  time_window_minutes: integer!

fields:
  last_operation_count: integer = 0
  last_operation_window_start: datetime

actions:
  - name: check_rate_limit
    steps:
      - if: |
          last_operation_window_start IS NULL OR
          NOW() - last_operation_window_start > INTERVAL '${time_window_minutes} minutes'
        then:
          - update: ENTITY SET
              last_operation_count = 1,
              last_operation_window_start = NOW()
        else:
          - validate: last_operation_count < ${max_operations}
            error: "rate_limit_exceeded"
          - update: ENTITY SET
              last_operation_count = last_operation_count + 1
```

**Usage**:
```yaml
entity: ApiKey
patterns:
  - rate_limiting:
      max_operations: 1000
      time_window_minutes: 60

fields:
  key: apiKey!
```

---

### Conditional Patterns

**Apply pattern based on field values**:

```yaml
entity: Document
schema: docs

patterns:
  - audit_trail
  - if: security_level = 'high'
    then:
      - encryption_at_rest
      - access_logging
  - if: is_public = false
    then:
      - approval_workflow

fields:
  title: text!
  content: text!
  security_level: enum(low, medium, high)!
  is_public: boolean = false
```

---

### Composite Patterns

**Combine multiple patterns**:

```yaml
pattern: full_audit
description: Complete audit trail with versioning and event sourcing

includes:
  - audit_trail
  - versioning
  - event_sourcing
  - soft_delete

actions:
  - name: audit_report
    params:
      entity_id: uuid!
    steps:
      - query: |
          SELECT
            h.version,
            h.snapshot,
            h.changed_at,
            h.changed_by,
            e.event_type,
            e.event_data
          FROM ENTITY_history h
          LEFT JOIN ENTITY_events e ON e.pk_ENTITY = h.pk_ENTITY
          WHERE h.pk_ENTITY = entity_pk($entity_id)
          ORDER BY h.version DESC, e.occurred_at DESC
        result: $audit_trail
      - return: $audit_trail
```

---

## Pattern Library Organization

### Standard Library Patterns

**Location**: `src/patterns/stdlib/`

```
stdlib/
├── audit/
│   ├── audit_trail.yaml
│   ├── event_sourcing.yaml
│   └── versioning.yaml
├── security/
│   ├── multi_tenant.yaml
│   ├── encryption.yaml
│   └── access_control.yaml
├── data/
│   ├── soft_delete.yaml
│   ├── archival.yaml
│   └── caching.yaml
└── workflow/
    ├── state_machine.yaml
    ├── approval.yaml
    └── scheduling.yaml
```

---

### Project Patterns

**Location**: `patterns/` (project root)

```
patterns/
├── custom/
│   ├── approval_workflow.yaml
│   ├── rate_limiting.yaml
│   └── document_lifecycle.yaml
└── domain/
    ├── ecommerce_order.yaml
    ├── crm_lead_scoring.yaml
    └── inventory_tracking.yaml
```

---

## Testing Custom Patterns

### Pattern Test File

**Location**: `tests/patterns/test_approval_workflow.py`

```python
import pytest
from specql.patterns import PatternRegistry
from specql.generators.schema import SchemaGenerator

def test_approval_workflow_pattern():
    """Test approval workflow pattern generates correct fields"""
    registry = PatternRegistry()
    pattern = registry.get_pattern('approval_workflow')

    # Test fields are added
    assert 'approval_status' in pattern.fields
    assert 'first_approver' in pattern.fields
    assert 'final_approver' in pattern.fields

def test_approval_workflow_actions():
    """Test approval workflow actions are generated"""
    registry = PatternRegistry()
    pattern = registry.get_pattern('approval_workflow')

    # Test actions exist
    assert 'first_approve' in pattern.actions
    assert 'final_approve' in pattern.actions
    assert 'reject' in pattern.actions

def test_approval_workflow_state_transitions():
    """Test state machine transitions are valid"""
    # Generate SQL
    sql = generate_pattern_sql('approval_workflow', 'PurchaseOrder', 'procurement')

    # Test constraint exists
    assert 'valid_approval_state' in sql
    assert 'CHECK' in sql
```

---

## Pattern Best Practices

### ✅ DO

**Keep patterns focused**:
```yaml
# Good: Single responsibility
pattern: audit_trail
fields:
  created_at: datetime!
  updated_at: datetime!

# Bad: Too many concerns
pattern: everything
fields:
  created_at: datetime!
  approval_status: enum(...)
  tenant_id: uuid!
  # ... 20 more fields
```

**Document pattern purpose**:
```yaml
pattern: approval_workflow
description: |
  Two-stage approval workflow with comments.
  Use for: Purchase orders, expense reports, document reviews.
  Requires: User entity for approvers.
```

**Provide examples**:
```yaml
pattern: rate_limiting
examples:
  - entity: ApiKey
    config:
      max_operations: 1000
      time_window_minutes: 60
  - entity: EmailSender
    config:
      max_operations: 100
      time_window_minutes: 1
```

---

### ❌ DON'T

**Don't make patterns too generic**:
```yaml
# Bad: Vague purpose
pattern: business_logic
fields:
  field1: text
  field2: integer
  # What does this do?
```

**Don't hardcode values**:
```yaml
# Bad: Hardcoded
pattern: rate_limiting
fields:
  max_requests: integer = 1000  # What if user wants 100?

# Good: Parameterized
pattern: rate_limiting
parameters:
  max_requests: integer!
fields:
  max_requests: integer = ${max_requests}
```

---

## Real-World Pattern Examples

### E-commerce Order Pattern

```yaml
pattern: ecommerce_order
description: Complete order lifecycle management

includes:
  - audit_trail
  - state_machine:
      field: status
      transitions:
        cart: [pending_payment]
        pending_payment: [paid, cancelled]
        paid: [processing]
        processing: [shipped, cancelled]
        shipped: [delivered, returned]
        delivered: []
        cancelled: []
        returned: [refunded]
        refunded: []

fields:
  status: enum(cart, pending_payment, paid, processing, shipped, delivered, cancelled, returned, refunded) = 'cart'
  total_amount: money!
  payment_method: enum(credit_card, paypal, bank_transfer)
  payment_reference: text
  shipping_address: address!
  tracking_number: trackingNumber

actions:
  - name: checkout
    steps:
      - validate: status = 'cart'
      - validate: total_amount > 0
      - update: Order SET status = 'pending_payment'

  - name: confirm_payment
    params:
      payment_reference: text!
    steps:
      - validate: status = 'pending_payment'
      - update: Order SET
          status = 'paid',
          payment_reference = $payment_reference
      - notify: order_paid, to: $customer.email

  - name: ship
    params:
      tracking_number: trackingNumber!
    steps:
      - validate: status = 'processing'
      - update: Order SET
          status = 'shipped',
          tracking_number = $tracking_number
      - notify: order_shipped, to: $customer.email
```

---

### CRM Lead Scoring Pattern

```yaml
pattern: lead_scoring
description: Automatic lead scoring based on activity

fields:
  score: integer = 0
  score_last_updated: datetime
  last_activity_at: datetime
  activity_count: integer = 0

actions:
  - name: update_score
    steps:
      - call: calculate_lead_score, args: {lead_id: $id}
        result: $new_score
      - update: Lead SET
          score = $new_score,
          score_last_updated = NOW()

  - name: track_activity
    params:
      activity_type: enum(email_open, link_click, form_submit, demo_request)!
    steps:
      - update: Lead SET
          last_activity_at = NOW(),
          activity_count = activity_count + 1
      - call: update_score

functions:
  - name: calculate_lead_score
    params:
      lead_id: uuid!
    returns: integer
    implementation: |
      SELECT
        COALESCE(email_score, 0) +
        COALESCE(engagement_score, 0) +
        COALESCE(demographic_score, 0)
      FROM (
        SELECT
          CASE WHEN email_verified THEN 20 ELSE 0 END as email_score,
          (activity_count * 5)::INTEGER as engagement_score,
          CASE company_size
            WHEN 'enterprise' THEN 50
            WHEN 'mid_market' THEN 30
            WHEN 'smb' THEN 10
            ELSE 0
          END as demographic_score
        FROM tb_lead
        WHERE id = lead_id
      ) scores;
```

---

## Next Steps

### Learn More

- **[Performance Tuning](performance-tuning.md)** - Optimize pattern-generated code
- **[Testing Guide](testing.md)** - Test custom patterns
- **[Extending StdLib](extending-stdlib.md)** - Contribute patterns to standard library

### Try These Examples

1. **Create approval workflow pattern** - Two-stage approval
2. **Create rate limiting pattern** - API throttling
3. **Create scoring pattern** - Lead/content scoring
4. **Combine patterns** - Build composite pattern

### Advanced Topics

- **[Pattern Composition](../08_internals/pattern-composition.md)** - How patterns merge
- **[Pattern Performance](../08_internals/pattern-performance.md)** - Optimize patterns
- **[Pattern Testing](../08_internals/pattern-testing.md)** - Comprehensive testing

---

## Summary

You've learned:
- ✅ Built-in patterns (audit_trail, soft_delete, multi_tenant, etc.)
- ✅ How to create custom patterns
- ✅ Pattern parameters and composition
- ✅ Testing and best practices
- ✅ Real-world pattern examples

**Key Takeaway**: Patterns encapsulate expertise and ensure consistency—define once, apply everywhere.

**Next**: Optimize generated code with [Performance Tuning](performance-tuning.md) →

---

**Build reusable patterns—scale best practices across your entire codebase.**
