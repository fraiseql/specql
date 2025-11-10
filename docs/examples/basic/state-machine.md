# Basic State Machine Example

This example demonstrates how to implement a simple state machine for managing order status transitions using SpecQL's state machine patterns.

## Overview

We'll create an `Order` entity that can transition through different states: `pending` → `confirmed` → `shipped` → `delivered`. This shows how SpecQL handles state transitions with validation and business rules.

## Entity Definition

Create a file `order.yaml`:

```yaml
entity: Order
schema: sales
description: "Customer order with state management"

fields:
  customer_id: uuid
  total_amount: decimal(10,2)
  status: enum(pending, confirmed, shipped, delivered, cancelled)
  shipping_address: text
  created_at: timestamp
  updated_at: timestamp
  shipped_at: timestamp
  delivered_at: timestamp

actions:
  # Initial order creation
  - name: create_order
    pattern: crud/create
    requires: caller.can_create_order

  # State transitions
  - name: confirm_order
    pattern: state_machine/transition
    requires: caller.can_confirm_order
    from_state: pending
    to_state: confirmed
    steps:
      - validate: total_amount > 0
        error: "invalid_order_amount"
      - update: Order SET status = 'confirmed', updated_at = now()

  - name: ship_order
    pattern: state_machine/transition
    requires: caller.can_ship_order
    from_state: confirmed
    to_state: shipped
    steps:
      - update: Order SET status = 'shipped', shipped_at = now(), updated_at = now()

  - name: deliver_order
    pattern: state_machine/transition
    requires: caller.can_deliver_order
    from_state: shipped
    to_state: delivered
    steps:
      - update: Order SET status = 'delivered', delivered_at = now(), updated_at = now()

  - name: cancel_order
    pattern: state_machine/guarded_transition
    requires: caller.can_cancel_order
    from_states: [pending, confirmed]
    to_state: cancelled
    guard: total_amount < 1000  # Only small orders can be cancelled
    steps:
      - update: Order SET status = 'cancelled', updated_at = now()
```

## Generated SQL

SpecQL generates state transition functions with built-in validation:

```sql
-- State transition functions
CREATE OR REPLACE FUNCTION sales.confirm_order(
    p_order_id uuid
) RETURNS void AS $$
DECLARE
    v_current_status text;
BEGIN
    -- Get current status
    SELECT status INTO v_current_status
    FROM sales.order WHERE id = p_order_id;

    -- Validate transition
    IF v_current_status != 'pending' THEN
        RAISE EXCEPTION 'Invalid transition: % → confirmed', v_current_status;
    END IF;

    -- Business validation
    IF (SELECT total_amount FROM sales.order WHERE id = p_order_id) <= 0 THEN
        RAISE EXCEPTION 'Order amount must be greater than 0';
    END IF;

    -- Execute transition
    UPDATE sales.order SET
        status = 'confirmed',
        updated_at = now()
    WHERE id = p_order_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION sales.cancel_order(
    p_order_id uuid
) RETURNS void AS $$
DECLARE
    v_current_status text;
    v_total_amount decimal(10,2);
BEGIN
    -- Get current state and amount
    SELECT status, total_amount INTO v_current_status, v_total_amount
    FROM sales.order WHERE id = p_order_id;

    -- Validate transition is allowed
    IF v_current_status NOT IN ('pending', 'confirmed') THEN
        RAISE EXCEPTION 'Cannot cancel order in status: %', v_current_status;
    END IF;

    -- Guard condition: only small orders
    IF v_total_amount >= 1000 THEN
        RAISE EXCEPTION 'Cannot cancel orders over $1000';
    END IF;

    -- Execute transition
    UPDATE sales.order SET
        status = 'cancelled',
        updated_at = now()
    WHERE id = p_order_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Creating and Managing an Order

```sql
-- 1. Create a new order
SELECT sales.create_order(
    '550e8400-e29b-41d4-a716-446655440000', -- customer_id
    299.99,                                 -- total_amount
    '123 Main St, Anytown, USA'            -- shipping_address
);

-- Returns: order_id (uuid)

-- 2. Confirm the order
SELECT sales.confirm_order('order-uuid-here');

-- 3. Ship the order
SELECT sales.ship_order('order-uuid-here');

-- 4. Mark as delivered
SELECT sales.deliver_order('order-uuid-here');
```

### Querying Order Status

```sql
-- Get order with status
SELECT id, status, created_at, shipped_at, delivered_at
FROM sales.order
WHERE id = 'order-uuid-here';

-- Get orders by status
SELECT * FROM sales.order
WHERE status = 'confirmed'
ORDER BY created_at DESC;

-- Get order timeline
SELECT
    id,
    status,
    created_at,
    CASE WHEN shipped_at IS NOT NULL THEN shipped_at ELSE NULL END as shipped_at,
    CASE WHEN delivered_at IS NOT NULL THEN delivered_at ELSE NULL END as delivered_at
FROM sales.order
WHERE id = 'order-uuid-here';
```

### Attempting Invalid Transitions

```sql
-- Try to ship an order that's not confirmed
SELECT sales.ship_order('pending-order-uuid');
-- ERROR: Invalid transition: pending → shipped

-- Try to cancel a large order
SELECT sales.cancel_order('large-order-uuid');
-- ERROR: Cannot cancel orders over $1000
```

## Testing State Transitions

SpecQL generates comprehensive state machine tests:

```sql
-- Run state machine tests
SELECT * FROM runtests('sales.order_state_machine_test');

-- Example test output:
-- ok 1 - confirm_order transitions pending → confirmed
-- ok 2 - confirm_order validates amount > 0
-- ok 3 - ship_order transitions confirmed → shipped
-- ok 4 - ship_order rejects invalid transitions
-- ok 5 - deliver_order transitions shipped → delivered
-- ok 6 - cancel_order works for small orders
-- ok 7 - cancel_order rejects large orders
-- ok 8 - cancel_order rejects wrong states
```

## Key Benefits

✅ **State Safety**: Invalid transitions are prevented at the database level
✅ **Business Rules**: Guard conditions enforce business logic
✅ **Audit Trail**: Automatic timestamp tracking for state changes
✅ **Validation**: Built-in checks for required fields and conditions
✅ **Testing**: Comprehensive test coverage for all transitions
✅ **Security**: Permission checks on all state changes

## Common Patterns

### Linear State Machine
```
pending → confirmed → shipped → delivered
```

### Branching State Machine
```
pending → confirmed → ┬─ shipped → delivered
                      └─ cancelled
```

### Guarded Transitions
- Only allow cancellations under certain conditions
- Require approvals for high-value orders
- Prevent state changes during business hours

## Next Steps

- Add [multi-entity operations](../intermediate/multi-entity.md) for order items
- Implement [batch operations](../intermediate/batch-operations.md) for bulk shipping
- Use [validation patterns](../basic/validation.md) for complex business rules

---

**See Also:**
- [CRUD Example](simple-crud.md)
- [Validation Example](validation.md)
- [State Machine Patterns](../../guides/mutation-patterns/state-machines.md)