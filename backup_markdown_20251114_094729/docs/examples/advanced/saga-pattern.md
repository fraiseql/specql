# Saga Pattern Example

This example demonstrates how to implement distributed transactions using SpecQL's saga orchestration patterns for maintaining consistency across multiple services or databases.

## Overview

We'll create an e-commerce order fulfillment system that coordinates:
1. Order creation
2. Payment processing
3. Inventory reservation
4. Shipping arrangement
5. Email notification

If any step fails, the saga compensates by undoing previous steps. This shows how SpecQL handles complex distributed transactions.

## Entity Definitions

### Order Saga Entity (`order_saga.yaml`)

```yaml
entity: OrderSaga
schema: ecommerce
description: "Distributed order fulfillment using saga pattern"

fields:
  customer_id: uuid
  total_amount: decimal(10,2)
  status: enum(pending, processing, completed, failed, compensating)
  saga_state: jsonb  # Tracks progress of each step
  created_at: timestamp
  completed_at: timestamp

actions:
  # Start order fulfillment saga
  - name: start_order_fulfillment
    pattern: multi_entity/saga_orchestrator
    requires: caller.can_create_orders
    saga_steps:
      - name: create_order
        action: insert
        entity: Order
        fields: [customer_id, total_amount, status: 'processing']
        compensation:
          action: delete
          entity: Order

      - name: process_payment
        action: call_external
        service: payment_service
        method: charge_customer
        params: [customer_id, total_amount]
        compensation:
          action: call_external
          service: payment_service
          method: refund_customer

      - name: reserve_inventory
        action: update
        entity: Product
        condition: "id IN (SELECT product_id FROM OrderItem WHERE order_id = Order.id)"
        fields: [reserved_quantity: 'reserved_quantity + OrderItem.quantity']
        validations:
          - rule: custom
            condition: "available_quantity >= reserved_quantity + OrderItem.quantity"
            error: "insufficient_inventory"
        compensation:
          action: update
          entity: Product
          fields: [reserved_quantity: 'reserved_quantity - OrderItem.quantity']

      - name: arrange_shipping
        action: call_external
        service: shipping_service
        method: create_shipment
        params: [order_id, shipping_address]
        compensation:
          action: call_external
          service: shipping_service
          method: cancel_shipment

      - name: send_confirmation
        action: call_external
        service: notification_service
        method: send_order_confirmation
        params: [customer_id, order_id]
        # No compensation needed for notifications

    success_action:
      - update: OrderSaga SET status = 'completed', completed_at = now()
      - update: Order SET status = 'confirmed'

    failure_action:
      - update: OrderSaga SET status = 'failed'
      - update: Order SET status = 'cancelled'
```

### Supporting Entities

Create `order.yaml`, `order_item.yaml`, and `product.yaml` as in previous examples.

## Generated SQL

SpecQL generates saga orchestration functions with compensation logic:

```sql
-- Saga orchestrator function
CREATE OR REPLACE FUNCTION ecommerce.start_order_fulfillment(
    p_customer_id uuid,
    p_items jsonb,  -- Array of {product_id, quantity, price}
    p_shipping_address text
) RETURNS uuid AS $$
DECLARE
    v_saga_id uuid;
    v_order_id uuid;
    v_total_amount decimal(10,2) := 0;
    v_saga_state jsonb := '{}';
    v_step_results jsonb := '{}';
BEGIN
    -- Calculate total
    SELECT SUM((item->>'quantity')::integer * (item->>'price')::decimal)
    INTO v_total_amount
    FROM jsonb_array_elements(p_items) as item;

    -- Create saga record
    INSERT INTO ecommerce.order_saga (
        customer_id, total_amount, status, saga_state, created_at
    ) VALUES (
        p_customer_id, v_total_amount, 'processing', v_saga_state, now()
    ) RETURNING id INTO v_saga_id;

    -- Start saga transaction
    BEGIN
        -- Step 1: Create order
        SELECT ecommerce.create_order_saga(p_customer_id, p_items, p_shipping_address)
        INTO v_order_id;

        v_saga_state := jsonb_set(v_saga_state, '{create_order}', 'true');
        v_step_results := jsonb_set(v_step_results, '{order_id}', to_jsonb(v_order_id));

        -- Update saga progress
        UPDATE ecommerce.order_saga SET
            saga_state = v_saga_state,
            saga_state = jsonb_set(saga_state, '{step_results}', v_step_results)
        WHERE id = v_saga_id;

        -- Step 2: Process payment
        PERFORM ecommerce.call_payment_service('charge_customer', jsonb_build_object(
            'customer_id', p_customer_id,
            'amount', v_total_amount,
            'order_id', v_order_id
        ));

        v_saga_state := jsonb_set(v_saga_state, '{process_payment}', 'true');

        -- Step 3: Reserve inventory
        PERFORM ecommerce.reserve_inventory_for_order(v_order_id);

        v_saga_state := jsonb_set(v_saga_state, '{reserve_inventory}', 'true');

        -- Step 4: Arrange shipping
        PERFORM ecommerce.call_shipping_service('create_shipment', jsonb_build_object(
            'order_id', v_order_id,
            'shipping_address', p_shipping_address
        ));

        v_saga_state := jsonb_set(v_saga_state, '{arrange_shipping}', 'true');

        -- Step 5: Send confirmation
        PERFORM ecommerce.call_notification_service('send_order_confirmation', jsonb_build_object(
            'customer_id', p_customer_id,
            'order_id', v_order_id
        ));

        v_saga_state := jsonb_set(v_saga_state, '{send_confirmation}', 'true');

        -- Saga completed successfully
        UPDATE ecommerce.order_saga SET
            status = 'completed',
            completed_at = now(),
            saga_state = v_saga_state
        WHERE id = v_saga_id;

        UPDATE ecommerce.order SET status = 'confirmed' WHERE id = v_order_id;

        RETURN v_saga_id;

    EXCEPTION
        WHEN OTHERS THEN
            -- Start compensation
            UPDATE ecommerce.order_saga SET status = 'compensating' WHERE id = v_saga_id;

            -- Execute compensations in reverse order
            PERFORM ecommerce.compensate_order_fulfillment(v_saga_id, v_step_results);

            -- Mark saga as failed
            UPDATE ecommerce.order_saga SET
                status = 'failed',
                saga_state = jsonb_set(saga_state, '{error}', to_jsonb(SQLERRM))
            WHERE id = v_saga_id;

            RAISE EXCEPTION 'Order fulfillment failed: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Compensation function
CREATE OR REPLACE FUNCTION ecommerce.compensate_order_fulfillment(
    p_saga_id uuid,
    p_step_results jsonb
) RETURNS void AS $$
DECLARE
    v_order_id uuid;
    v_customer_id uuid;
    v_total_amount decimal(10,2);
BEGIN
    -- Get saga details
    SELECT (p_step_results->>'order_id')::uuid,
           customer_id,
           total_amount
    INTO v_order_id, v_customer_id, v_total_amount
    FROM ecommerce.order_saga WHERE id = p_saga_id;

    -- Compensate in reverse order
    BEGIN
        -- Compensate shipping (if it was arranged)
        IF p_step_results ? 'shipping_id' THEN
            PERFORM ecommerce.call_shipping_service('cancel_shipment',
                jsonb_build_object('shipping_id', p_step_results->'shipping_id'));
        END IF;

        -- Compensate inventory (if it was reserved)
        IF v_order_id IS NOT NULL THEN
            PERFORM ecommerce.release_inventory_reservation(v_order_id);
        END IF;

        -- Compensate payment (if it was charged)
        IF v_customer_id IS NOT NULL AND v_total_amount IS NOT NULL THEN
            PERFORM ecommerce.call_payment_service('refund_customer',
                jsonb_build_object(
                    'customer_id', v_customer_id,
                    'amount', v_total_amount,
                    'order_id', v_order_id
                ));
        END IF;

        -- Compensate order creation (delete order)
        IF v_order_id IS NOT NULL THEN
            DELETE FROM ecommerce.order WHERE id = v_order_id;
        END IF;

    EXCEPTION
        WHEN OTHERS THEN
            -- Log compensation failure but don't fail the saga
            RAISE WARNING 'Compensation step failed: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Successful Order Fulfillment

```sql
-- Start order fulfillment saga
SELECT ecommerce.start_order_fulfillment(
    'customer-uuid-here',                    -- customer_id
    '[                                   -- order items
        {"product_id": "product-1-uuid", "quantity": 2, "price": 29.99},
        {"product_id": "product-2-uuid", "quantity": 1, "price": 49.99}
    ]'::jsonb,
    '123 Main St, Anytown, USA'            -- shipping_address
);

-- Returns: saga-id-uuid
```

### Monitoring Saga Progress

```sql
-- Check saga status
SELECT
    id,
    status,
    saga_state,
    created_at,
    completed_at
FROM ecommerce.order_saga
WHERE id = 'saga-uuid-here';

-- Check saga state details
SELECT
    saga_state->>'create_order' as order_created,
    saga_state->>'process_payment' as payment_processed,
    saga_state->>'reserve_inventory' as inventory_reserved,
    saga_state->>'arrange_shipping' as shipping_arranged,
    saga_state->>'send_confirmation' as confirmation_sent
FROM ecommerce.order_saga
WHERE id = 'saga-uuid-here';
```

### Handling Failures

```sql
-- Simulate payment failure
-- The saga will automatically compensate:
-- 1. Cancel shipping (if arranged)
-- 2. Release inventory reservations
-- 3. Refund payment (if charged)
-- 4. Delete order

-- Check failed saga
SELECT
    id,
    status,
    saga_state->>'error' as failure_reason,
    created_at
FROM ecommerce.order_saga
WHERE status = 'failed';
```

## Saga Recovery

### Manual Recovery

```sql
-- Retry failed saga (if recoverable)
SELECT ecommerce.retry_saga('failed-saga-uuid');

-- Manually compensate stuck saga
SELECT ecommerce.manual_compensation('stuck-saga-uuid');
```

### Automatic Recovery

```sql
-- Check for stuck sagas (processing for too long)
SELECT ecommerce.recover_stuck_sagas(interval '1 hour');

-- Clean up old completed sagas
SELECT ecommerce.cleanup_completed_sagas(interval '30 days');
```

## Testing Saga Patterns

SpecQL generates comprehensive saga tests:

```sql
-- Run saga tests
SELECT * FROM runtests('ecommerce.saga_test');

-- Example test output:
-- ok 1 - start_order_fulfillment creates saga record
-- ok 2 - successful saga completes all steps
-- ok 3 - payment failure triggers compensation
-- ok 4 - inventory failure triggers compensation
-- ok 5 - shipping failure triggers compensation
-- ok 6 - compensation undoes all completed steps
-- ok 7 - saga recovery handles stuck transactions
-- ok 8 - manual compensation works correctly
```

## Advanced Saga Patterns

### Branching Sagas

```yaml
saga_steps:
  - name: initial_processing
    branches:
      - condition: "order_type = 'standard'"
        steps: [create_order, process_payment, ship_standard]
      - condition: "order_type = 'express'"
        steps: [create_order, process_payment, ship_express, notify_customer]
```

### Parallel Execution

```yaml
saga_steps:
  - name: parallel_steps
    parallel:
      - name: payment_processing
        action: call_external
        service: payment
      - name: inventory_check
        action: call_external
        service: inventory
      - name: fraud_check
        action: call_external
        service: fraud_detection
```

### Conditional Compensation

```yaml
saga_steps:
  - name: risky_operation
    action: call_external
    compensation:
      condition: "step_completed"  # Only compensate if step actually ran
      action: call_external
      service: cleanup_service
```

## Key Benefits

✅ **Consistency**: Distributed transactions maintain data consistency
✅ **Reliability**: Automatic compensation prevents partial failures
✅ **Observability**: Complete audit trail of saga execution
✅ **Recovery**: Automatic and manual recovery from failures
✅ **Flexibility**: Complex workflows with conditional logic
✅ **Performance**: Optimized for high-throughput scenarios

## Common Use Cases

- **E-commerce**: Order fulfillment across payment, inventory, shipping services
- **Financial**: Money transfers between accounts, currency exchange
- **Travel**: Booking flights, hotels, cars with compensation
- **Microservices**: Coordinating complex business processes across services
- **SaaS**: User provisioning, resource allocation, billing coordination

## Next Steps

- Add [event-driven patterns](event-driven.md) for saga triggers
- Implement [performance tuning](performance-tuning.md) for high-volume sagas
- Use [batch operations](../../intermediate/batch-operations.md) for bulk saga processing

---

**See Also:**
- [Multi-Entity Operations](../../intermediate/multi-entity.md)
- [Workflows](../../intermediate/workflows.md)
- [Event-Driven Patterns](event-driven.md)
- [Saga Pattern Reference](../../../guides/mutation-patterns/saga-patterns.md)