# State Machine Pattern

The **state machine** pattern manages entity lifecycle and status transitions. It's perfect for workflows like order processing, user approvals, content publishing, and any process with defined states and transitions.

## 🎯 What You'll Learn

- State machine concepts and benefits
- Configuring states and transitions
- Guards, actions, and events
- Testing state machines
- Common use cases and patterns

## 📋 Prerequisites

- [Pattern basics](getting-started.md)
- Understanding of entity lifecycles
- Basic YAML knowledge

## 💡 State Machine Concepts

### What Are State Machines?

A **state machine** defines:
- **States** - Possible statuses (pending, approved, shipped)
- **Transitions** - Allowed status changes
- **Triggers** - Functions that cause transitions
- **Guards** - Conditions that must be met
- **Actions** - Side effects during transitions
- **Events** - Notifications emitted

### Why Use State Machines?

| Benefit | Description | Example |
|---------|-------------|---------|
| **Consistency** | Enforced valid transitions | Can't ship unapproved orders |
| **Auditability** | Track all status changes | Who changed what when |
| **Automation** | Trigger actions on changes | Send email when order ships |
| **Safety** | Prevent invalid states | No "shipped" without "paid" |
| **Clarity** | Explicit business rules | Clear approval workflow |

## 🏗️ Basic State Machine

### Simple Example

```yaml
# entities/order.yaml
name: order
fields:
  id: uuid
  status: string
  total: decimal

patterns:
  - name: state_machine
    description: "Order processing workflow"
    initial_state: pending
    states: [pending, confirmed, shipped, delivered, cancelled]
    transitions:
      - from: pending
        to: confirmed
        trigger: confirm
      - from: confirmed
        to: shipped
        trigger: ship
      - from: shipped
        to: delivered
        trigger: deliver
      - from: pending
        to: cancelled
        trigger: cancel
      - from: confirmed
        to: cancelled
        trigger: cancel
```

### Generated Functions

```sql
-- State transition functions
SELECT order_confirm(order_id);
SELECT order_ship(order_id);
SELECT order_deliver(order_id);
SELECT order_cancel(order_id);

-- Query functions
SELECT * FROM order_get_available_transitions(order_id);
SELECT order_can_transition(order_id, 'confirm');
SELECT order_get_current_state(order_id);
```

## ⚙️ Advanced Configuration

### State Definitions

```yaml
patterns:
  - name: state_machine
    description: "User account management"
    initial_state: inactive

    # Detailed state configuration
    states:
      - name: inactive
        description: "Account created but not verified"
        color: "gray"
        metadata:
          can_login: false
          requires_verification: true

      - name: active
        description: "Fully active account"
        color: "green"
        metadata:
          can_login: true
          requires_verification: false

      - name: suspended
        description: "Temporarily disabled"
        color: "red"
        metadata:
          can_login: false
          suspension_reason: required

      - name: deactivated
        description: "Permanently deactivated"
        color: "black"
        metadata:
          can_login: false
          can_reactivate: false
```

### Transition Configuration

```yaml
transitions:
  - from: inactive
    to: pending_verification
    trigger: request_verification
    description: "Send verification email"
    guard: "email IS NOT NULL"
    action: "send_verification_email"
    events: ["user_verification_requested"]
    metadata:
      estimated_duration: "5 minutes"

  - from: pending_verification
    to: active
    trigger: verify_email
    description: "Complete email verification"
    guard: "verification_token IS NOT NULL"
    action: "send_welcome_email"
    events: ["user_activated"]
    timeout: "24 hours"

  - from: active
    to: suspended
    trigger: suspend
    description: "Suspend user account"
    reason: "Violation of terms of service"
    action: "send_suspension_notice"
    events: ["user_suspended"]
    requires_permission: "admin"

  - from: suspended
    to: active
    trigger: reactivate
    description: "Reactivate suspended account"
    guard: "suspension_reason_resolved = true"
    action: "send_reactivation_notice"
    events: ["user_reactivated"]
```

## 🔒 Guards and Conditions

### Precondition Guards

Guards prevent invalid transitions:

```yaml
transitions:
  - from: pending
    to: confirmed
    trigger: confirm
    guard: "total_amount > 0 AND payment_method IS NOT NULL"

  - from: confirmed
    to: shipped
    trigger: ship
    guard: "inventory_available = true AND shipping_address IS NOT NULL"

  - from: any
    to: cancelled
    trigger: cancel
    guard: "cancelled_by IN ('customer', 'admin')"
```

**Guard Types:**
- **SQL expressions** - `balance > 100`
- **Field checks** - `status = 'active'`
- **Function calls** - `has_permission(user_id, 'cancel')`
- **Complex logic** - `age >= 18 AND country IN ('US', 'CA')`

### Dynamic Guards

```yaml
transitions:
  - from: draft
    to: published
    trigger: publish
    guard: |
      published_at IS NULL
      AND author_id = CURRENT_USER_ID()
      AND word_count >= 100
      AND reviewed_by IS NOT NULL
```

## ⚡ Actions and Side Effects

### Transition Actions

Actions execute during transitions:

```yaml
transitions:
  - from: pending
    to: confirmed
    trigger: confirm
    action: "send_order_confirmation"

  - from: confirmed
    to: shipped
    trigger: ship
    action: "update_inventory"

  - from: shipped
    to: delivered
    trigger: deliver
    actions:  # Multiple actions
      - "send_delivery_notification"
      - "update_delivery_metrics"
      - "trigger_customer_survey"
```

### Action Functions

Actions call custom functions:

```sql
-- Generated action function
CREATE FUNCTION order_send_order_confirmation(order_id UUID)
RETURNS VOID AS $$
DECLARE
  customer_email TEXT;
  order_total DECIMAL;
BEGIN
  -- Get order details
  SELECT email, total INTO customer_email, order_total
  FROM customer c
  JOIN order o ON c.id = o.customer_id
  WHERE o.id = order_id;

  -- Send email
  PERFORM send_email(
    customer_email,
    'Order Confirmed',
    format('Your order totaling $%s has been confirmed', order_total)
  );
END;
$$ LANGUAGE plpgsql;
```

## 📢 Events and Notifications

### Event Emission

Events notify external systems:

```yaml
transitions:
  - from: pending
    to: confirmed
    trigger: confirm
    events: ["order_confirmed", "payment_captured"]

  - from: confirmed
    to: shipped
    trigger: ship
    events: ["order_shipped"]

  - from: shipped
    to: delivered
    trigger: deliver
    events: ["order_delivered", "customer_satisfaction_survey"]
```

### Event Handling

Events use PostgreSQL NOTIFY:

```sql
-- Listen for events
LISTEN order_events;

-- Event payload structure
{
  "event": "order_confirmed",
  "entity_type": "order",
  "entity_id": "123e4567-e89b-12d3-a456-426614174000",
  "from_state": "pending",
  "to_state": "confirmed",
  "triggered_by": "user_456",
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "order_total": 299.99,
    "customer_id": "789e0123-e89b-12d3-a456-426614174001"
  }
}
```

## 🧪 Testing State Machines

### Generated Tests

State machines generate comprehensive tests:

```bash
# Generate tests
specql generate tests entities/order.yaml

# Run tests
specql test run entities/order.yaml
```

**Test Coverage:**
- ✅ **Initial state** - Entity starts correctly
- ✅ **Valid transitions** - Allowed state changes work
- ✅ **Invalid transitions** - Blocked changes fail
- ✅ **Guard conditions** - Preconditions enforced
- ✅ **Actions executed** - Side effects triggered
- ✅ **Events emitted** - Notifications sent
- ✅ **Edge cases** - Boundary conditions

### Manual Testing

```sql
-- Setup test data
INSERT INTO order (id, status, total)
VALUES ('test-order-id', 'pending', 100.00);

-- Test valid transition
SELECT order_confirm('test-order-id');
-- Should succeed

-- Check state changed
SELECT status FROM order WHERE id = 'test-order-id';
-- Should be 'confirmed'

-- Test invalid transition
SELECT order_ship('test-order-id');
-- Should fail (not confirmed yet)

-- Test with guard violation
UPDATE order SET total = 0 WHERE id = 'test-order-id';
SELECT order_confirm('test-order-id');
-- Should fail (guard: total > 0)
```

## 🚀 Common Use Cases

### E-commerce Order

```yaml
patterns:
  - name: state_machine
    description: "Order fulfillment process"
    initial_state: pending
    states: [pending, confirmed, processing, shipped, delivered, cancelled, refunded]

    transitions:
      - from: pending
        to: confirmed
        trigger: confirm
        guard: "payment_received = true"

      - from: confirmed
        to: processing
        trigger: start_processing
        action: "reserve_inventory"

      - from: processing
        to: shipped
        trigger: ship
        action: "update_tracking"
        events: ["order_shipped"]

      - from: shipped
        to: delivered
        trigger: mark_delivered
        action: "send_delivery_email"

      - from: [pending, confirmed, processing]
        to: cancelled
        trigger: cancel
        action: "refund_payment"

      - from: delivered
        to: refunded
        trigger: refund
        guard: "refund_eligible = true"
```

### User Account Management

```yaml
patterns:
  - name: state_machine
    description: "User lifecycle management"
    initial_state: inactive
    states: [inactive, pending_verification, active, suspended, deactivated]

    transitions:
      - from: inactive
        to: pending_verification
        trigger: request_verification
        guard: "email_verified = false"
        action: "send_verification_email"

      - from: pending_verification
        to: active
        trigger: verify_email
        guard: "verification_token_valid = true"
        action: "send_welcome_email"

      - from: active
        to: suspended
        trigger: suspend
        reason: "Policy violation"
        action: "send_suspension_notice"

      - from: suspended
        to: active
        trigger: reactivate
        guard: "violation_resolved = true"

      - from: [active, suspended]
        to: deactivated
        trigger: deactivate
        action: "send_deactivation_notice"
```

### Content Publishing

```yaml
patterns:
  - name: state_machine
    description: "Content publishing workflow"
    initial_state: draft
    states: [draft, review, approved, published, archived]

    transitions:
      - from: draft
        to: review
        trigger: submit_for_review
        guard: "word_count >= 100"

      - from: review
        to: approved
        trigger: approve
        guard: "reviewed_by IS NOT NULL"

      - from: approved
        to: published
        trigger: publish
        action: "update_published_at"

      - from: published
        to: archived
        trigger: archive
        guard: "age_days > 365"

      - from: [draft, review, approved]
        to: archived
        trigger: reject
        action: "notify_author"
```

## 🎯 Best Practices

### State Design
- **Clear state names** - Use descriptive, unambiguous names
- **Logical progression** - States should flow naturally
- **Minimal states** - Don't create unnecessary states
- **Terminal states** - Include end states (delivered, cancelled)

### Transition Design
- **Explicit triggers** - Clear function names (`confirm_order`, not `next`)
- **Strong guards** - Prevent invalid transitions
- **Useful actions** - Add value during transitions
- **Informative events** - Help external systems react

### Performance
- **Index guard fields** - Speed up precondition checks
- **Cache state data** - For frequently accessed entities
- **Batch transitions** - For bulk operations
- **Monitor timeouts** - Handle stuck transitions

### Maintenance
- **Version transitions** - Track workflow changes
- **Document reasons** - Explain guard conditions
- **Test thoroughly** - All paths and edge cases
- **Monitor usage** - Track transition frequencies

## 🆘 Troubleshooting

### "Transition not allowed"
```sql
-- Check current state
SELECT status FROM order WHERE id = 'order-id';

-- Check available transitions
SELECT * FROM order_get_available_transitions('order-id');

-- Check guard conditions
SELECT total_amount > 0 AND payment_received = true
FROM order WHERE id = 'order-id';
```

### "Action function not found"
```bash
# Regenerate after adding actions
specql generate schema entities/order.yaml --force

# Check function exists
psql $DATABASE_URL -c "\df order_send_confirmation"
```

### "Event not received"
```sql
-- Check event emission
LISTEN order_events;

-- Trigger transition
SELECT order_confirm('order-id');

-- Should see notification
-- NOTIFY order_events, '{"event": "order_confirmed", ...}';
```

### "Performance issues"
```yaml
# Add indexes for guards
indexes:
  - fields: [status]
  - fields: [total_amount]
  - fields: [payment_received]
    where: "status = 'pending'"
```

## 🎉 Summary

State machines provide:
- ✅ **Structured workflows** - Clear state progressions
- ✅ **Data integrity** - Enforced valid transitions
- ✅ **Automatic actions** - Side effects during changes
- ✅ **Event notifications** - External system integration
- ✅ **Comprehensive testing** - Full coverage out of the box

## 🚀 What's Next?

- **[Multi-Entity Operations](multi-entity.md)** - Cross-table transactions
- **[Validation](validation.md)** - Data integrity patterns
- **[Batch Operations](batch-operations.md)** - Bulk data processing
- **[Examples](../../examples/)** - Real-world state machines

**Ready to implement complex workflows? Let's continue! 🚀**