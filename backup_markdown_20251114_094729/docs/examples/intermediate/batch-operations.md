# Batch Operations Example

This example demonstrates how to efficiently process multiple records in a single operation using SpecQL's batch operation patterns for bulk data processing.

## Overview

We'll create a product catalog system that needs to handle bulk operations like:
- Bulk price updates
- Bulk inventory adjustments
- Bulk product status changes

This shows how SpecQL optimizes performance for high-volume data operations.

## Entity Definition

Create a file `product_catalog.yaml`:

```yaml
entity: Product
schema: catalog
description: "Product catalog with batch operations"

fields:
  name: text
  sku: text
  price: decimal(10,2)
  stock_quantity: integer
  category: text
  status: enum(active, inactive, discontinued)
  updated_at: timestamp
  updated_by: uuid

actions:
  # Bulk price update
  - name: bulk_update_prices
    pattern: batch/bulk_operation
    requires: caller.can_manage_pricing
    operation: update
    batch_field: products  # Array of {id, new_price}
    validations:
      - rule: custom
        condition: "new_price > 0"
        error: "invalid_price"
      - rule: custom
        condition: "new_price < current_price * 2"
        error: "price_increase_too_large"
    steps:
      - update: Product SET
          price = new_price,
          updated_at = now(),
          updated_by = caller.id
        WHERE id = product_id

  # Bulk inventory adjustment
  - name: bulk_adjust_inventory
    pattern: batch/bulk_operation
    requires: caller.can_manage_inventory
    operation: update
    batch_field: adjustments  # Array of {id, quantity_change, reason}
    validations:
      - rule: custom
        condition: "stock_quantity + quantity_change >= 0"
        error: "insufficient_stock"
      - field: reason
        rule: required
        error: "adjustment_reason_required"
    steps:
      - update: Product SET
          stock_quantity = stock_quantity + quantity_change,
          updated_at = now(),
          updated_by = caller.id
        WHERE id = product_id
      - insert: InventoryAdjustment SET
          product_id = product_id,
          quantity_change = quantity_change,
          reason = reason,
          adjusted_at = now(),
          adjusted_by = caller.id

  # Bulk status change
  - name: bulk_change_status
    pattern: batch/bulk_operation
    requires: caller.can_manage_products
    operation: update
    batch_field: products  # Array of {id, new_status}
    validations:
      - field: new_status
        rule: enum
        values: [active, inactive, discontinued]
        error: "invalid_status"
    steps:
      - update: Product SET
          status = new_status,
          updated_at = now(),
          updated_by = caller.id
        WHERE id = product_id
```

## Supporting Entity

Create a file `inventory_adjustment.yaml`:

```yaml
entity: InventoryAdjustment
schema: catalog
description: "Audit trail for inventory changes"

fields:
  product_id: uuid
  quantity_change: integer
  reason: text
  adjusted_at: timestamp
  adjusted_by: uuid
```

## Generated SQL

SpecQL generates optimized batch processing functions:

```sql
-- Bulk price update function
CREATE OR REPLACE FUNCTION catalog.bulk_update_prices(
    p_products jsonb  -- Array of {id, new_price}
) RETURNS integer AS $$
DECLARE
    v_product record;
    v_updated_count integer := 0;
    v_current_price decimal(10,2);
BEGIN
    -- Process each product in the batch
    FOR v_product IN SELECT * FROM jsonb_array_elements(p_products)
    LOOP
        DECLARE
            v_product_id uuid := (v_product.value->>'id')::uuid;
            v_new_price decimal(10,2) := (v_product.value->>'new_price')::decimal;
        BEGIN
            -- Get current price for validation
            SELECT price INTO v_current_price
            FROM catalog.product WHERE id = v_product_id;

            -- Validate price
            IF v_new_price <= 0 THEN
                RAISE EXCEPTION 'Invalid price for product %: %', v_product_id, v_new_price;
            END IF;

            IF v_new_price > v_current_price * 2 THEN
                RAISE EXCEPTION 'Price increase too large for product %', v_product_id;
            END IF;

            -- Update product
            UPDATE catalog.product SET
                price = v_new_price,
                updated_at = now(),
                updated_by = session_user::uuid
            WHERE id = v_product_id;

            IF FOUND THEN
                v_updated_count := v_updated_count + 1;
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                -- Log error but continue processing other items
                RAISE WARNING 'Failed to update product %: %', v_product_id, SQLERRM;
        END;
    END LOOP;

    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Bulk inventory adjustment function
CREATE OR REPLACE FUNCTION catalog.bulk_adjust_inventory(
    p_adjustments jsonb  -- Array of {id, quantity_change, reason}
) RETURNS integer AS $$
DECLARE
    v_adjustment record;
    v_processed_count integer := 0;
BEGIN
    FOR v_adjustment IN SELECT * FROM jsonb_array_elements(p_adjustments)
    LOOP
        DECLARE
            v_product_id uuid := (v_adjustment.value->>'id')::uuid;
            v_quantity_change integer := (v_adjustment.value->>'quantity_change')::integer;
            v_reason text := v_adjustment.value->>'reason';
            v_current_stock integer;
        BEGIN
            -- Get current stock
            SELECT stock_quantity INTO v_current_stock
            FROM catalog.product WHERE id = v_product_id;

            -- Validate adjustment
            IF v_current_stock + v_quantity_change < 0 THEN
                RAISE EXCEPTION 'Insufficient stock for product %', v_product_id;
            END IF;

            IF v_reason IS NULL OR v_reason = '' THEN
                RAISE EXCEPTION 'Adjustment reason required for product %', v_product_id;
            END IF;

            -- Update product inventory
            UPDATE catalog.product SET
                stock_quantity = stock_quantity + v_quantity_change,
                updated_at = now(),
                updated_by = session_user::uuid
            WHERE id = v_product_id;

            -- Record adjustment for audit trail
            INSERT INTO catalog.inventory_adjustment (
                product_id, quantity_change, reason, adjusted_at, adjusted_by
            ) VALUES (
                v_product_id, v_quantity_change, v_reason, now(), session_user::uuid
            );

            v_processed_count := v_processed_count + 1;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE WARNING 'Failed to adjust inventory for product %: %', v_product_id, SQLERRM;
        END;
    END LOOP;

    RETURN v_processed_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Bulk Price Updates

```sql
-- Update prices for multiple products
SELECT catalog.bulk_update_prices('[
    {"id": "product-1-uuid", "new_price": 29.99},
    {"id": "product-2-uuid", "new_price": 49.99},
    {"id": "product-3-uuid", "new_price": 19.99}
]'::jsonb);

-- Returns: 3 (number of products updated)
```

### Bulk Inventory Adjustments

```sql
-- Adjust inventory levels with reasons
SELECT catalog.bulk_adjust_inventory('[
    {"id": "product-1-uuid", "quantity_change": -5, "reason": "Sold online"},
    {"id": "product-2-uuid", "quantity_change": 10, "reason": "Restock delivery"},
    {"id": "product-3-uuid", "quantity_change": -2, "reason": "Damaged goods"}
]'::jsonb);

-- Returns: 3 (number of adjustments processed)
```

### Bulk Status Changes

```sql
-- Change status for multiple products
SELECT catalog.bulk_change_status('[
    {"id": "product-1-uuid", "new_status": "discontinued"},
    {"id": "product-2-uuid", "new_status": "active"},
    {"id": "product-3-uuid", "new_status": "inactive"}
]'::jsonb);
```

### Monitoring Batch Operations

```sql
-- Check recent price updates
SELECT
    p.name,
    p.price,
    p.updated_at,
    p.updated_by
FROM catalog.product p
WHERE p.updated_at > now() - interval '1 hour'
ORDER BY p.updated_at DESC;

-- Check inventory adjustment history
SELECT
    p.name,
    ia.quantity_change,
    ia.reason,
    ia.adjusted_at,
    ia.adjusted_by
FROM catalog.inventory_adjustment ia
JOIN catalog.product p ON ia.product_id = p.id
ORDER BY ia.adjusted_at DESC
LIMIT 10;
```

## Error Handling and Partial Failures

```sql
-- Batch with some failures (continues processing)
SELECT catalog.bulk_update_prices('[
    {"id": "valid-product-uuid", "new_price": 29.99},
    {"id": "invalid-product-uuid", "new_price": -10},  -- Invalid price
    {"id": "another-valid-uuid", "new_price": 49.99}
]'::jsonb);

-- Returns: 2 (only successful updates counted)
-- Warnings logged for failed items
```

## Performance Optimization

### Efficient Batch Processing

```sql
-- Single transaction for entire batch
BEGIN;
    SELECT catalog.bulk_update_prices(large_product_array);
COMMIT;

-- vs multiple individual updates
UPDATE catalog.product SET price = 29.99 WHERE id = 'product-1-uuid';
UPDATE catalog.product SET price = 49.99 WHERE id = 'product-2-uuid';
-- ... many more individual statements
```

### Batch Size Considerations

```sql
-- Process large batches in chunks
SELECT catalog.bulk_update_prices(
    (SELECT jsonb_agg(data) FROM (
        SELECT jsonb_build_object('id', id, 'new_price', new_price) as data
        FROM temp_price_updates
        LIMIT 1000  -- Process in batches of 1000
    ) t)
);
```

## Testing Batch Operations

SpecQL generates comprehensive batch processing tests:

```sql
-- Run batch operation tests
SELECT * FROM runtests('catalog.product_batch_test');

-- Example test output:
-- ok 1 - bulk_update_prices updates multiple products
-- ok 2 - bulk_update_prices validates prices
-- ok 3 - bulk_update_prices handles invalid products gracefully
-- ok 4 - bulk_adjust_inventory updates stock levels
-- ok 5 - bulk_adjust_inventory creates audit trail
-- ok 6 - bulk_adjust_inventory prevents negative stock
-- ok 7 - bulk_change_status validates status values
-- ok 8 - batch operations maintain data consistency
```

## Key Benefits

✅ **Performance**: Single transaction for multiple operations
✅ **Efficiency**: Reduced database round trips
✅ **Reliability**: All-or-nothing semantics with error handling
✅ **Audit Trail**: Complete history of batch operations
✅ **Validation**: Business rules applied to each item
✅ **Monitoring**: Track success/failure rates

## Common Use Cases

- **E-commerce**: Bulk price updates, inventory adjustments
- **Content Management**: Bulk publish/unpublish operations
- **User Management**: Bulk role assignments, status changes
- **Financial**: Bulk transaction processing, account updates
- **Inventory**: Bulk stock level adjustments, product status changes

## Next Steps

- Add [saga patterns](../advanced/saga-pattern.md) for distributed batch operations
- Implement [workflows](workflows.md) for complex batch approval processes
- Use [event-driven patterns](../advanced/event-driven.md) for batch completion notifications

---

**See Also:**
- [Multi-Entity Operations](multi-entity.md)
- [Workflows](workflows.md)
- [Batch Operation Patterns](../../guides/mutation-patterns/batch-operations.md)