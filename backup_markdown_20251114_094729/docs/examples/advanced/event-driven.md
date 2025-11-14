# Event-Driven Architecture Example

This example demonstrates how to implement event-driven patterns using SpecQL's event-driven orchestration for reactive systems that respond to changes and trigger automated workflows.

## Overview

We'll create a real-time inventory management system that reacts to:
1. Low stock alerts
2. Automatic reordering
3. Supplier notifications
4. Customer backorder handling

This shows how SpecQL handles event-driven architectures with triggers, reactions, and cascading updates.

## Entity Definitions

### Inventory Event System (`inventory_events.yaml`)

```yaml
entity: InventoryEvent
schema: inventory
description: "Event-driven inventory management"

fields:
  product_id: uuid
  event_type: enum(low_stock, out_of_stock, restock, backorder)
  quantity_change: integer
  previous_stock: integer
  new_stock: integer
  triggered_at: timestamp
  processed_at: timestamp
  event_data: jsonb

actions:
  # Stock level change trigger
  - name: on_stock_change
    pattern: multi_entity/event_driven_orchestrator
    trigger: stock_level_changed
    conditions:
      - if: "new_stock <= reorder_point AND new_stock > 0"
        then:
          - insert: InventoryEvent SET
              product_id: "product_id"
              event_type: "'low_stock'"
              quantity_change: "quantity_change"
              previous_stock: "previous_stock"
              new_stock: "new_stock"
              triggered_at: "now()"
              event_data: "jsonb_build_object('reorder_point', reorder_point)"
          - call_external: notification_service "send_low_stock_alert"
          - call_external: procurement_service "create_reorder_request"

      - if: "new_stock = 0"
        then:
          - insert: InventoryEvent SET
              product_id: "product_id"
              event_type: "'out_of_stock'"
              quantity_change: "quantity_change"
              previous_stock: "previous_stock"
              new_stock: "new_stock"
              triggered_at: "now()"
          - update: Product SET backorder_available = true
          - notify: sales_team "Product out of stock - enable backorders"
          - notify: affected_customers "Product backorder available"

      - if: "previous_stock = 0 AND new_stock > 0"
        then:
          - insert: InventoryEvent SET
              product_id: "product_id"
              event_type: "'restock'"
              quantity_change: "quantity_change"
              previous_stock: "previous_stock"
              new_stock: "new_stock"
              triggered_at: "now()"
          - update: Product SET backorder_available = false
          - process_backorders: "fulfill_pending_backorders(product_id)"
          - notify: sales_team "Product restocked - process backorders"

  # Reorder fulfillment event
  - name: on_reorder_received
    pattern: multi_entity/event_driven_orchestrator
    trigger: reorder_delivered
    steps:
      - update: Product SET
          stock_quantity: "stock_quantity + delivered_quantity"
          last_restocked: "now()"
      - insert: InventoryEvent SET
          product_id: "product_id"
          event_type: "'restock'"
          quantity_change: "delivered_quantity"
          previous_stock: "stock_quantity"
          new_stock: "stock_quantity + delivered_quantity"
          triggered_at: "now()"
          event_data: "jsonb_build_object('supplier_id', supplier_id, 'po_number', po_number)"
      - notify: inventory_team "Restock received and processed"

  # Customer order impact
  - name: on_order_placed
    pattern: multi_entity/event_driven_orchestrator
    trigger: order_item_created
    conditions:
      - if: "stock_quantity - ordered_quantity <= reorder_point"
        then:
          - insert: InventoryEvent SET
              product_id: "product_id"
              event_type: "'low_stock'"
              quantity_change: "-ordered_quantity"
              previous_stock: "stock_quantity"
              new_stock: "stock_quantity - ordered_quantity"
              triggered_at: "now()"
              event_data: "jsonb_build_object('order_id', order_id, 'customer_id', customer_id)"
          - escalate_reorder: "urgent_reorder_if_needed(product_id)"

  # Backorder processing
  - name: process_backorders
    pattern: batch/bulk_operation
    trigger: product_restocked
    operation: update
    batch_field: pending_backorders
    steps:
      - update: Backorder SET status = 'fulfilled', fulfilled_at = now()
        WHERE product_id = product_id AND status = 'pending'
        ORDER BY created_at LIMIT available_quantity
      - notify: customers "Backorder fulfilled - shipment in progress"
```

### Supporting Entities

```yaml
# Product with event triggers
entity: Product
schema: inventory
fields:
  name: text
  stock_quantity: integer
  reorder_point: integer
  backorder_available: boolean
  last_restocked: timestamp

# Backorder tracking
entity: Backorder
schema: sales
fields:
  customer_id: uuid
  product_id: uuid
  quantity: integer
  status: enum(pending, fulfilled, cancelled)
  created_at: timestamp
  fulfilled_at: timestamp
```

## Generated SQL

SpecQL generates event-driven triggers and handlers:

```sql
-- Stock level change trigger
CREATE OR REPLACE FUNCTION inventory.trigger_stock_change_events()
RETURNS trigger AS $$
BEGIN
    -- Only trigger on stock quantity changes
    IF OLD.stock_quantity = NEW.stock_quantity THEN
        RETURN NEW;
    END IF;

    -- Low stock event
    IF NEW.stock_quantity <= NEW.reorder_point AND NEW.stock_quantity > 0 THEN
        PERFORM inventory.create_inventory_event(
            NEW.id,
            'low_stock',
            NEW.stock_quantity - OLD.stock_quantity,
            OLD.stock_quantity,
            NEW.stock_quantity,
            jsonb_build_object('reorder_point', NEW.reorder_point)
        );

        -- Trigger external notifications
        PERFORM inventory.notify_low_stock(NEW.id);
        PERFORM inventory.create_reorder_request(NEW.id);
    END IF;

    -- Out of stock event
    IF NEW.stock_quantity = 0 THEN
        PERFORM inventory.create_inventory_event(
            NEW.id,
            'out_of_stock',
            NEW.stock_quantity - OLD.stock_quantity,
            OLD.stock_quantity,
            NEW.stock_quantity,
            NULL
        );

        -- Enable backorders and notify
        UPDATE inventory.product SET backorder_available = true WHERE id = NEW.id;
        PERFORM inventory.notify_out_of_stock(NEW.id);
    END IF;

    -- Restock event
    IF OLD.stock_quantity = 0 AND NEW.stock_quantity > 0 THEN
        PERFORM inventory.create_inventory_event(
            NEW.id,
            'restock',
            NEW.stock_quantity - OLD.stock_quantity,
            OLD.stock_quantity,
            NEW.stock_quantity,
            NULL
        );

        -- Process backorders
        PERFORM inventory.process_backorders(NEW.id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger
CREATE TRIGGER stock_change_trigger
    AFTER UPDATE ON inventory.product
    FOR EACH ROW EXECUTE FUNCTION inventory.trigger_stock_change_events();

-- Event processing function
CREATE OR REPLACE FUNCTION inventory.create_inventory_event(
    p_product_id uuid,
    p_event_type text,
    p_quantity_change integer,
    p_previous_stock integer,
    p_new_stock integer,
    p_event_data jsonb
) RETURNS uuid AS $$
DECLARE
    v_event_id uuid;
BEGIN
    INSERT INTO inventory.inventory_event (
        product_id, event_type, quantity_change,
        previous_stock, new_stock, triggered_at, event_data
    ) VALUES (
        p_product_id, p_event_type, p_quantity_change,
        p_previous_stock, p_new_stock, now(), p_event_data
    ) RETURNING id INTO v_event_id;

    -- Mark as processed
    UPDATE inventory.inventory_event SET processed_at = now() WHERE id = v_event_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Backorder processing
CREATE OR REPLACE FUNCTION inventory.process_backorders(
    p_product_id uuid
) RETURNS integer AS $$
DECLARE
    v_backorder record;
    v_processed_count integer := 0;
BEGIN
    -- Get available stock
    DECLARE
        v_available_stock integer;
    BEGIN
        SELECT stock_quantity INTO v_available_stock
        FROM inventory.product WHERE id = p_product_id;

        -- Process backorders FIFO
        FOR v_backorder IN
            SELECT * FROM sales.backorder
            WHERE product_id = p_product_id AND status = 'pending'
            ORDER BY created_at
        LOOP
            IF v_available_stock >= v_backorder.quantity THEN
                -- Fulfill backorder
                UPDATE sales.backorder SET
                    status = 'fulfilled',
                    fulfilled_at = now()
                WHERE id = v_backorder.id;

                -- Reduce available stock
                v_available_stock := v_available_stock - v_backorder.quantity;
                v_processed_count := v_processed_count + 1;

                -- Notify customer
                PERFORM sales.notify_backorder_fulfilled(v_backorder.customer_id, p_product_id);
            ELSE
                -- Not enough stock for remaining backorders
                EXIT;
            END IF;
        END LOOP;
    END;

    RETURN v_processed_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Automatic Stock Monitoring

```sql
-- Product automatically triggers events based on stock changes
UPDATE inventory.product SET stock_quantity = 5 WHERE id = 'product-uuid';
-- Triggers: low_stock event, reorder request, notification

UPDATE inventory.product SET stock_quantity = 0 WHERE id = 'product-uuid';
-- Triggers: out_of_stock event, backorder enablement, customer notifications

-- Restock triggers backorder fulfillment
UPDATE inventory.product SET stock_quantity = 100 WHERE id = 'product-uuid';
-- Triggers: restock event, backorder processing, status updates
```

### Event Monitoring

```sql
-- View recent inventory events
SELECT
    ie.event_type,
    p.name as product_name,
    ie.quantity_change,
    ie.previous_stock,
    ie.new_stock,
    ie.triggered_at,
    ie.event_data
FROM inventory.inventory_event ie
JOIN inventory.product p ON ie.product_id = p.id
ORDER BY ie.triggered_at DESC
LIMIT 10;

-- Event type distribution
SELECT
    event_type,
    COUNT(*) as event_count,
    AVG(quantity_change) as avg_quantity_change
FROM inventory.inventory_event
WHERE triggered_at > now() - interval '7 days'
GROUP BY event_type;
```

### Backorder Management

```sql
-- Check backorder status
SELECT
    bo.customer_id,
    p.name as product_name,
    bo.quantity,
    bo.status,
    bo.created_at,
    bo.fulfilled_at
FROM sales.backorder bo
JOIN inventory.product p ON bo.product_id = p.id
WHERE bo.status = 'pending'
ORDER BY bo.created_at;

-- Manual backorder fulfillment
SELECT inventory.process_backorders('product-uuid');
-- Returns: number of backorders fulfilled
```

## Event-Driven Analytics

### Stock Level Trends

```sql
-- Stock level changes over time
SELECT
    p.name,
    date_trunc('day', ie.triggered_at) as date,
    SUM(ie.quantity_change) as net_change,
    MIN(ie.new_stock) as min_stock,
    MAX(ie.new_stock) as max_stock
FROM inventory.inventory_event ie
JOIN inventory.product p ON ie.product_id = p.id
WHERE ie.triggered_at > now() - interval '30 days'
GROUP BY p.name, date_trunc('day', ie.triggered_at)
ORDER BY date;

-- Reorder frequency
SELECT
    p.name,
    COUNT(*) as reorder_events,
    AVG(ie.new_stock) as avg_stock_at_reorder,
    MIN(ie.new_stock) as min_stock_at_reorder
FROM inventory.inventory_event ie
JOIN inventory.product p ON ie.product_id = p.id
WHERE ie.event_type = 'low_stock'
  AND ie.triggered_at > now() - interval '90 days'
GROUP BY p.name;
```

### System Performance

```sql
-- Event processing latency
SELECT
    event_type,
    AVG(EXTRACT(EPOCH FROM (processed_at - triggered_at))) as avg_processing_seconds,
    MAX(EXTRACT(EPOCH FROM (processed_at - triggered_at))) as max_processing_seconds,
    COUNT(*) as total_events
FROM inventory.inventory_event
WHERE processed_at IS NOT NULL
GROUP BY event_type;

-- Event failure rate
SELECT
    event_type,
    COUNT(*) as total_events,
    SUM(CASE WHEN processed_at IS NULL THEN 1 ELSE 0 END) as failed_events,
    ROUND(
        SUM(CASE WHEN processed_at IS NULL THEN 1 ELSE 0 END)::decimal /
        COUNT(*) * 100, 2
    ) as failure_rate
FROM inventory.inventory_event
GROUP BY event_type;
```

## Testing Event-Driven Systems

SpecQL generates comprehensive event tests:

```sql
-- Run event-driven tests
SELECT * FROM runtests('inventory.event_driven_test');

-- Example test output:
-- ok 1 - stock_change_trigger fires on quantity update
-- ok 2 - low_stock event creates reorder request
-- ok 3 - out_of_stock enables backorders
-- ok 4 - restock processes pending backorders
-- ok 5 - order_placement triggers stock alerts
-- ok 6 - event processing maintains data consistency
-- ok 7 - failed events are logged and retried
-- ok 8 - event cascade prevents infinite loops
```

## Advanced Event Patterns

### Event Filtering and Aggregation

```yaml
actions:
  - name: aggregated_alerts
    pattern: event_driven_orchestrator
    trigger: multiple_low_stock_events
    condition: "COUNT(low_stock_events) >= 5 WITHIN 1 hour"
    steps:
      - notify: management "Multiple products low on stock"
      - create: BulkReorderRequest
```

### Event Correlation

```yaml
actions:
  - name: correlated_events
    pattern: event_driven_orchestrator
    triggers: [order_failed, payment_failed, inventory_shortage]
    correlation_window: "10 minutes"
    condition: "order_failed AND (payment_failed OR inventory_shortage)"
    steps:
      - escalate: customer_service "Complex order failure - manual review needed"
```

### Event Sourcing

```yaml
actions:
  - name: event_sourcing
    pattern: event_driven_orchestrator
    trigger: any_inventory_change
    steps:
      - append: InventoryEventLog SET
          entity_id: "product_id"
          event_type: "event_type"
          event_data: "row_to_json(NEW)"
          event_timestamp: "now()"
```

## Key Benefits

✅ **Reactivity**: Automatic responses to system changes
✅ **Decoupling**: Events trigger actions without tight coupling
✅ **Scalability**: Event-driven systems handle high throughput
✅ **Auditability**: Complete event history for debugging
✅ **Reliability**: Event replay and failure recovery
✅ **Maintainability**: Declarative event handling logic

## Common Use Cases

- **Inventory**: Stock alerts, automatic reordering, backorder processing
- **E-commerce**: Order status updates, shipping notifications, returns processing
- **IoT**: Sensor data processing, threshold alerts, predictive maintenance
- **Financial**: Fraud detection, transaction monitoring, compliance alerts
- **DevOps**: System monitoring, auto-scaling, incident response

## Next Steps

- Add [saga patterns](saga-pattern.md) for complex event compensation
- Implement [performance tuning](performance-tuning.md) for high-frequency events
- Use [batch operations](../../intermediate/batch-operations.md) for bulk event processing

---

**See Also:**
- [Saga Patterns](saga-pattern.md)
- [Workflows](../../intermediate/workflows.md)
- [Multi-Entity Operations](../../intermediate/multi-entity.md)
- [Event-Driven Patterns Reference](../../../guides/mutation-patterns/event-driven.md)