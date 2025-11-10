# Multi-Entity Operations Example

This example demonstrates how to coordinate operations across multiple related entities using SpecQL's multi-entity patterns for maintaining data consistency.

## Overview

We'll create an e-commerce system with `Order` and `OrderItem` entities that must be coordinated. When an order is placed, we need to:
1. Create the order
2. Create order items
3. Update product inventory
4. Calculate order totals

This shows how SpecQL handles complex multi-table transactions.

## Entity Definitions

### Order Entity (`order.yaml`)

```yaml
entity: Order
schema: sales
description: "Customer order"

fields:
  customer_id: uuid
  status: enum(pending, confirmed, shipped, delivered)
  total_amount: decimal(10,2)
  shipping_address: text
  created_at: timestamp

actions:
  - name: place_order
    pattern: multi_entity/coordinated_update
    requires: caller.can_place_order
    entities:
      - entity: Order
        operation: insert
        fields: [customer_id, shipping_address]
        computed:
          total_amount: "SUM(OrderItem.quantity * OrderItem.unit_price)"
          status: "'pending'"
          created_at: "now()"

      - entity: OrderItem
        operation: insert
        fields: [product_id, quantity, unit_price]
        validations:
          - field: quantity
            rule: range
            min: 1
            error: "invalid_quantity"
          - field: unit_price
            rule: custom
            condition: "unit_price > 0"
            error: "invalid_price"

      - entity: Product
        operation: update
        condition: "id = OrderItem.product_id"
        fields:
          stock_quantity: "stock_quantity - OrderItem.quantity"
        validations:
          - rule: custom
            condition: "stock_quantity >= OrderItem.quantity"
            error: "insufficient_stock"
```

### OrderItem Entity (`order_item.yaml`)

```yaml
entity: OrderItem
schema: sales
description: "Individual item in an order"

fields:
  order_id: uuid
  product_id: uuid
  quantity: integer
  unit_price: decimal(10,2)
  total_price: decimal(10,2)
  created_at: timestamp

computed_fields:
  total_price: "quantity * unit_price"
```

### Product Entity (`product.yaml`)

```yaml
entity: Product
schema: inventory
description: "Product catalog item"

fields:
  name: text
  stock_quantity: integer
  unit_price: decimal(10,2)
  category: text
```

## Generated SQL

SpecQL generates a coordinated transaction function:

```sql
CREATE OR REPLACE FUNCTION sales.place_order(
    p_customer_id uuid,
    p_shipping_address text,
    p_order_items jsonb  -- Array of {product_id, quantity}
) RETURNS uuid AS $$
DECLARE
    v_order_id uuid;
    v_total_amount decimal(10,2) := 0;
    v_item record;
BEGIN
    -- Start transaction
    BEGIN
        -- Validate all products exist and have sufficient stock
        FOR v_item IN SELECT * FROM jsonb_array_elements(p_order_items)
        LOOP
            -- Check product exists and get price
            SELECT unit_price INTO v_item.unit_price
            FROM inventory.product
            WHERE id = (v_item.value->>'product_id')::uuid;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Product not found: %', v_item.value->>'product_id';
            END IF;

            -- Check stock availability
            IF (SELECT stock_quantity FROM inventory.product
                WHERE id = (v_item.value->>'product_id')::uuid) <
               (v_item.value->>'quantity')::integer THEN
                RAISE EXCEPTION 'Insufficient stock for product: %', v_item.value->>'product_id';
            END IF;

            -- Calculate line total
            v_total_amount := v_total_amount +
                ((v_item.value->>'quantity')::integer * v_item.unit_price);
        END LOOP;

        -- Create order
        INSERT INTO sales.order (
            customer_id, shipping_address, total_amount, status, created_at
        ) VALUES (
            p_customer_id, p_shipping_address, v_total_amount, 'pending', now()
        ) RETURNING id INTO v_order_id;

        -- Create order items and update inventory
        FOR v_item IN SELECT * FROM jsonb_array_elements(p_order_items)
        LOOP
            DECLARE
                v_product_id uuid := (v_item.value->>'product_id')::uuid;
                v_quantity integer := (v_item.value->>'quantity')::integer;
                v_unit_price decimal(10,2);
            BEGIN
                -- Get current price
                SELECT unit_price INTO v_unit_price
                FROM inventory.product WHERE id = v_product_id;

                -- Create order item
                INSERT INTO sales.order_item (
                    order_id, product_id, quantity, unit_price, total_price, created_at
                ) VALUES (
                    v_order_id, v_product_id, v_quantity, v_unit_price,
                    v_quantity * v_unit_price, now()
                );

                -- Update product stock
                UPDATE inventory.product
                SET stock_quantity = stock_quantity - v_quantity
                WHERE id = v_product_id;
            END;
        END LOOP;

        -- Commit transaction
        RETURN v_order_id;

    EXCEPTION
        WHEN OTHERS THEN
            -- Rollback on any error
            RAISE EXCEPTION 'Order placement failed: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Placing an Order

```sql
-- Place an order with multiple items
SELECT sales.place_order(
    'customer-uuid-here',                    -- customer_id
    '123 Main St, Anytown, USA',            -- shipping_address
    '[                                   -- order_items as JSON array
        {"product_id": "product-1-uuid", "quantity": 2},
        {"product_id": "product-2-uuid", "quantity": 1},
        {"product_id": "product-3-uuid", "quantity": 3}
    ]'::jsonb
);

-- Returns: order_id (uuid)
```

### Querying Order Details

```sql
-- Get complete order with items
SELECT
    o.id,
    o.customer_id,
    o.total_amount,
    o.status,
    o.created_at,
    json_agg(
        json_build_object(
            'product_id', oi.product_id,
            'quantity', oi.quantity,
            'unit_price', oi.unit_price,
            'total_price', oi.total_price,
            'product_name', p.name
        )
    ) as items
FROM sales.order o
JOIN sales.order_item oi ON o.id = oi.order_id
JOIN inventory.product p ON oi.product_id = p.id
WHERE o.id = 'order-uuid-here'
GROUP BY o.id, o.customer_id, o.total_amount, o.status, o.created_at;
```

### Checking Inventory Impact

```sql
-- Verify inventory was updated correctly
SELECT
    p.name,
    p.stock_quantity as current_stock,
    SUM(oi.quantity) as ordered_quantity
FROM inventory.product p
JOIN sales.order_item oi ON p.id = oi.product_id
WHERE oi.order_id = 'order-uuid-here'
GROUP BY p.id, p.name, p.stock_quantity;
```

## Error Handling

### Insufficient Stock

```sql
-- Attempt to order more than available stock
SELECT sales.place_order(
    'customer-uuid',
    '123 Main St',
    '[{"product_id": "scarce-product-uuid", "quantity": 100}]'::jsonb
);
-- ERROR: Insufficient stock for product: scarce-product-uuid
```

### Invalid Product

```sql
-- Attempt to order non-existent product
SELECT sales.place_order(
    'customer-uuid',
    '123 Main St',
    '[{"product_id": "nonexistent-uuid", "quantity": 1}]'::jsonb
);
-- ERROR: Product not found: nonexistent-uuid
```

## Testing Multi-Entity Operations

SpecQL generates comprehensive coordination tests:

```sql
-- Run multi-entity tests
SELECT * FROM runtests('sales.order_multi_entity_test');

-- Example test output:
-- ok 1 - place_order creates order record
-- ok 2 - place_order creates all order items
-- ok 3 - place_order updates product inventory
-- ok 4 - place_order calculates correct totals
-- ok 5 - place_order validates stock availability
-- ok 6 - place_order handles invalid products
-- ok 7 - place_order rolls back on failure
-- ok 8 - place_order maintains data consistency
```

## Advanced Patterns

### Parent-Child Cascade

```yaml
actions:
  - name: delete_order
    pattern: multi_entity/parent_child_cascade
    entities:
      - entity: OrderItem
        operation: delete
        condition: "order_id = parent.id"
      - entity: Order
        operation: delete
```

### Event-Driven Updates

```yaml
actions:
  - name: process_payment
    pattern: multi_entity/event_driven_orchestrator
    trigger: payment_received
    entities:
      - entity: Order
        operation: update
        fields: [status: 'paid']
      - entity: Invoice
        operation: insert
        fields: [order_id, amount, payment_date]
```

## Key Benefits

✅ **Atomicity**: All operations succeed or all fail
✅ **Consistency**: Data integrity across multiple tables
✅ **Validation**: Cross-entity business rules
✅ **Performance**: Single transaction, minimal round trips
✅ **Testing**: Comprehensive multi-entity test coverage
✅ **Error Handling**: Automatic rollback on failures

## Common Use Cases

- **Order Processing**: Order + OrderItems + Inventory updates
- **User Registration**: User + Profile + Preferences + Email verification
- **Financial Transactions**: Account + Transaction + Ledger + Audit log
- **Content Management**: Article + Tags + Categories + Media assets

## Next Steps

- Add [saga patterns](../advanced/saga-pattern.md) for distributed transactions
- Implement [batch operations](batch-operations.md) for bulk order processing
- Use [workflows](workflows.md) for complex order fulfillment

---

**See Also:**
- [Batch Operations](batch-operations.md)
- [Workflows](workflows.md)
- [Multi-Entity Patterns](../../guides/mutation-patterns/multi-entity.md)