# Tutorial 3: State Machines (45 minutes)

Master SpecQL's state machine patterns by building a comprehensive order management system with complex workflows, validation, and business rules.

## 🎯 What You'll Learn

- Design complex state machines
- Implement guarded transitions
- Add business rule validation
- Handle state machine testing

## 📋 Prerequisites

- Completed [Tutorial 2: Building a CRM](../02-building-crm.md)
- Understanding of state machine concepts

## 🏗️ Step 1: Design Order State Machine

Create an e-commerce order system with a complex state machine:

### Order Entity (`orders/order.yaml`)

```yaml
entity: Order
schema: orders
description: "E-commerce order with complex state management"

fields:
  customer_id: uuid
  total_amount: decimal(10,2)
  shipping_address: text
  billing_address: text
  payment_method: text
  status: enum(
    pending,           # Initial state
    payment_pending,   # Awaiting payment
    payment_failed,    # Payment failed
    paid,              # Payment successful
    processing,        # Order being prepared
    quality_check,     # Quality assurance
    ready_to_ship,     # Ready for shipping
    shipped,           # Shipped to customer
    delivered,         # Delivered successfully
    return_requested,  # Customer requested return
    return_received,   # Return received
    refunded,          # Refund processed
    cancelled          # Order cancelled
  )
  payment_id: text
  tracking_number: text
  shipped_at: timestamp
  delivered_at: timestamp
  cancelled_at: timestamp
  created_at: timestamp
  updated_at: timestamp

actions:
  # Initial order creation
  - name: create_order
    pattern: crud/create
    requires: caller.can_create_orders

  # Payment workflow
  - name: request_payment
    pattern: state_machine/transition
    requires: caller.can_process_payments
    from_state: pending
    to_state: payment_pending
    steps:
      - validate: total_amount > 0
        error: "invalid_order_amount"
      - validate: payment_method IS NOT NULL
        error: "payment_method_required"
      - update: Order SET status = 'payment_pending', updated_at = now()

  - name: confirm_payment
    pattern: state_machine/transition
    requires: caller.can_process_payments
    from_state: payment_pending
    to_state: paid
    steps:
      - validate: payment_id IS NOT NULL
        error: "payment_id_required"
      - update: Order SET status = 'paid', updated_at = now()

  - name: fail_payment
    pattern: state_machine/transition
    requires: caller.can_process_payments
    from_state: payment_pending
    to_state: payment_failed
    steps:
      - update: Order SET status = 'payment_failed', updated_at = now()

  # Order processing workflow
  - name: start_processing
    pattern: state_machine/transition
    requires: caller.can_process_orders
    from_state: paid
    to_state: processing
    steps:
      - update: Order SET status = 'processing', updated_at = now()

  - name: quality_check
    pattern: state_machine/transition
    requires: caller.can_process_orders
    from_state: processing
    to_state: quality_check
    steps:
      - update: Order SET status = 'quality_check', updated_at = now()

  - name: approve_for_shipping
    pattern: state_machine/transition
    requires: caller.can_ship_orders
    from_state: quality_check
    to_state: ready_to_ship
    steps:
      - update: Order SET status = 'ready_to_ship', updated_at = now()

  # Shipping workflow
  - name: ship_order
    pattern: state_machine/guarded_transition
    requires: caller.can_ship_orders
    from_state: ready_to_ship
    to_state: shipped
    guard: tracking_number IS NOT NULL
    steps:
      - update: Order SET
          status = 'shipped',
          shipped_at = now(),
          updated_at = now()

  - name: deliver_order
    pattern: state_machine/transition
    requires: caller.can_deliver_orders
    from_state: shipped
    to_state: delivered
    steps:
      - update: Order SET
          status = 'delivered',
          delivered_at = now(),
          updated_at = now()

  # Return workflow
  - name: request_return
    pattern: state_machine/guarded_transition
    requires: caller.is_customer
    from_states: [shipped, delivered]
    to_state: return_requested
    guard: "EXTRACT(days FROM now() - shipped_at) <= 30"
    steps:
      - update: Order SET status = 'return_requested', updated_at = now()

  - name: receive_return
    pattern: state_machine/transition
    requires: caller.can_process_returns
    from_state: return_requested
    to_state: return_received
    steps:
      - update: Order SET status = 'return_received', updated_at = now()

  - name: process_refund
    pattern: state_machine/transition
    requires: caller.can_process_refunds
    from_state: return_received
    to_state: refunded
    steps:
      - update: Order SET status = 'refunded', updated_at = now()

  # Cancellation workflow
  - name: cancel_order
    pattern: state_machine/guarded_transition
    requires: caller.can_cancel_orders
    from_states: [pending, payment_pending, paid]
    to_state: cancelled
    guard: "total_amount < 500 OR status = 'pending'"
    steps:
      - update: Order SET
          status = 'cancelled',
          cancelled_at = now(),
          updated_at = now()
```

## 🗄️ Step 2: Generate and Apply Schema

Generate the order management schema:

```bash
# Generate schema
specql generate schema

# Apply migrations
specql db migrate
```

## 🏃 Step 3: Test State Transitions

Create and test the complete order workflow:

```sql
-- 1. Create an order
SELECT orders.create_order(
    'customer-uuid-here',
    299.99,
    '123 Main St, Anytown, USA',
    '123 Main St, Anytown, USA',
    'credit_card'
);

-- Returns: order-uuid

-- 2. Start payment process
SELECT orders.request_payment('order-uuid');

-- 3. Confirm payment (simulate successful payment)
UPDATE orders.order SET payment_id = 'payment-123' WHERE id = 'order-uuid';
SELECT orders.confirm_payment('order-uuid');

-- 4. Process the order
SELECT orders.start_processing('order-uuid');
SELECT orders.quality_check('order-uuid');
SELECT orders.approve_for_shipping('order-uuid');

-- 5. Ship the order
UPDATE orders.order SET tracking_number = 'TRK123456' WHERE id = 'order-uuid';
SELECT orders.ship_order('order-uuid');

-- 6. Mark as delivered
SELECT orders.deliver_order('order-uuid');
```

## 🔒 Step 4: Test Guard Conditions

Test the business rule validations:

```sql
-- Try to cancel a large paid order (should fail)
UPDATE orders.order SET total_amount = 1000 WHERE id = 'order-uuid';
SELECT orders.cancel_order('order-uuid');
-- ERROR: Guard condition failed

-- Try to request return after 30 days (should fail)
UPDATE orders.order SET
    shipped_at = now() - interval '31 days'
WHERE id = 'order-uuid';
SELECT orders.request_return('order-uuid');
-- ERROR: Guard condition failed

-- Try invalid state transition
SELECT orders.confirm_payment('order-uuid');  -- Already paid
-- ERROR: Invalid transition: paid → paid
```

## 📊 Step 5: Query State Machine Analytics

Create analytics for your state machine:

```sql
-- Order status distribution
SELECT
    status,
    COUNT(*) as order_count,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        1
    ) as percentage
FROM orders.order
GROUP BY status
ORDER BY order_count DESC;

-- State transition times
SELECT
    id,
    status,
    created_at,
    paid_at,
    shipped_at,
    delivered_at,
    EXTRACT(hours FROM (paid_at - created_at)) as time_to_pay,
    EXTRACT(hours FROM (shipped_at - paid_at)) as time_to_ship,
    EXTRACT(hours FROM (delivered_at - shipped_at)) as time_to_deliver
FROM (
    SELECT
        id,
        status,
        created_at,
        CASE WHEN status IN ('paid', 'processing', 'quality_check', 'ready_to_ship', 'shipped', 'delivered')
             THEN created_at END as paid_at,
        CASE WHEN status IN ('shipped', 'delivered')
             THEN shipped_at END as shipped_at,
        CASE WHEN status = 'delivered'
             THEN delivered_at END as delivered_at
    FROM orders.order
    WHERE status = 'delivered'
) t;

-- Conversion funnel
WITH status_order AS (
    SELECT
        status,
        ROW_NUMBER() OVER (ORDER BY
            CASE status
                WHEN 'pending' THEN 1
                WHEN 'payment_pending' THEN 2
                WHEN 'paid' THEN 3
                WHEN 'processing' THEN 4
                WHEN 'quality_check' THEN 5
                WHEN 'ready_to_ship' THEN 6
                WHEN 'shipped' THEN 7
                WHEN 'delivered' THEN 8
            END
        ) as status_order
    FROM (SELECT DISTINCT status FROM orders.order) s
)
SELECT
    so.status_order,
    o.status,
    COUNT(*) as orders_in_status,
    ROUND(
        100.0 * COUNT(*) /
        FIRST_VALUE(COUNT(*)) OVER (ORDER BY so.status_order),
        1
    ) as conversion_rate
FROM orders.order o
JOIN status_order so ON o.status = so.status
GROUP BY so.status_order, o.status
ORDER BY so.status_order;
```

## 🧪 Step 6: Generate State Machine Tests

Generate and run comprehensive state machine tests:

```bash
# Generate tests
specql generate tests

# Run state machine tests
specql test --pattern "*state_machine*"

# Run order-specific tests
specql test --pattern "*order*"
```

Check test coverage:

```sql
-- Run pgTAP tests manually
SELECT * FROM runtests('orders.order_state_machine_test');

-- Should test all transitions, guards, and error conditions
```

## 🔄 Step 7: Add Parallel State Machines

Create an order item entity with its own state machine:

### OrderItem Entity (`orders/order_item.yaml`)

```yaml
entity: OrderItem
schema: orders
description: "Individual order item with state tracking"

fields:
  order_id: ref(Order)
  product_id: uuid
  product_name: text
  quantity: integer
  unit_price: decimal(10,2)
  total_price: decimal(10,2)
  status: enum(pending, confirmed, backordered, shipped, delivered, returned)
  tracking_number: text
  delivered_at: timestamp

computed_fields:
  total_price: "quantity * unit_price"

actions:
  - name: create_order_item
    pattern: crud/create

  - name: mark_backordered
    pattern: state_machine/transition
    from_state: pending
    to_state: backordered
    steps:
      - update: OrderItem SET status = 'backordered'

  - name: confirm_item
    pattern: state_machine/transition
    from_state: pending
    to_state: confirmed
    steps:
      - update: OrderItem SET status = 'confirmed'

  - name: ship_item
    pattern: state_machine/transition
    from_state: confirmed
    to_state: shipped
    steps:
      - update: OrderItem SET status = 'shipped', tracking_number = tracking_number

  - name: deliver_item
    pattern: state_machine/transition
    from_state: shipped
    to_state: delivered
    steps:
      - update: OrderItem SET status = 'delivered', delivered_at = now()
```

## 📈 Step 8: Advanced State Analytics

Create advanced analytics combining order and item states:

```sql
-- Order completion analysis
SELECT
    o.id as order_id,
    o.status as order_status,
    COUNT(oi.id) as total_items,
    COUNT(CASE WHEN oi.status = 'delivered' THEN 1 END) as delivered_items,
    COUNT(CASE WHEN oi.status = 'backordered' THEN 1 END) as backordered_items,
    ROUND(
        100.0 * COUNT(CASE WHEN oi.status = 'delivered' THEN 1 END) / COUNT(oi.id),
        1
    ) as completion_percentage
FROM orders.order o
LEFT JOIN orders.order_item oi ON o.id = oi.order_id
GROUP BY o.id, o.status
ORDER BY completion_percentage DESC;

-- State machine performance
SELECT
    'Order State Machine' as machine_type,
    COUNT(*) as total_transitions,
    COUNT(DISTINCT id) as unique_orders,
    AVG(EXTRACT(hours FROM (updated_at - created_at))) as avg_time_in_system
FROM orders.order
WHERE status IN ('delivered', 'cancelled', 'refunded');

-- Transition error analysis (from test results)
SELECT
    test_name,
    status,
    execution_time,
    error_message
FROM test_results
WHERE test_name LIKE '%state_machine%'
  AND status = 'failed'
ORDER BY execution_time DESC;
```

## 🎉 Success!

You've mastered complex state machines with:

✅ **Complex Workflows**: 12-state order management system
✅ **Guard Conditions**: Business rule validation
✅ **Multiple Transitions**: From multiple source states
✅ **Parallel State Machines**: Order and order item coordination
✅ **Analytics**: Comprehensive state machine reporting
✅ **Testing**: Full state transition test coverage

## 🧪 Test Your Knowledge

Try these advanced exercises:

1. **Add approval workflow**: Require manager approval for large orders
2. **Implement timeouts**: Auto-cancel pending orders after 24 hours
3. **Add notifications**: Email notifications for state changes
4. **Create audit log**: Track all state transitions
5. **Add rollback**: Allow reverting state transitions

## 📚 Next Steps

- [Tutorial 4: Testing](../04-testing.md) - Comprehensive testing strategies
- [Tutorial 5: Production](../05-production.md) - Production deployment
- [Advanced Patterns](../../../guides/mutation-patterns/) - More complex patterns

## 💡 Pro Tips

- Design state machines on paper first
- Use guard conditions for business rules
- Test all possible state transitions
- Monitor state machine performance
- Consider state machine versioning for changes

---

**Time completed**: 45 minutes
**States implemented**: 13 order states + 6 item states
**Transitions tested**: 20+ state transitions
**Analytics created**: 5 comprehensive reports
**Next tutorial**: [Testing →](../04-testing.md)