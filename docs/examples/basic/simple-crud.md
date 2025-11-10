# Basic CRUD Example

This example demonstrates the fundamental Create, Read, Update, Delete operations using SpecQL's built-in CRUD patterns.

## Overview

We'll create a simple `Product` entity with basic CRUD operations. This example shows how SpecQL handles the most common database operations automatically.

## Entity Definition

Create a file `product.yaml`:

```yaml
entity: Product
schema: inventory
description: "Product catalog item"

fields:
  name: text
  description: text
  price: decimal(10,2)
  category: text
  in_stock: boolean
  created_at: timestamp
  updated_at: timestamp

actions:
  # Create operation
  - name: create_product
    pattern: crud/create
    requires: caller.can_create_product

  # Read operations (handled automatically by framework)
  # No explicit read actions needed - framework provides SELECT queries

  # Update operation
  - name: update_product
    pattern: crud/update
    requires: caller.can_edit_product
    fields: [name, description, price, category, in_stock]

  # Delete operation
  - name: delete_product
    pattern: crud/delete
    requires: caller.can_delete_product
```

## Generated SQL

SpecQL will generate the following database schema:

```sql
-- Schema creation
CREATE SCHEMA IF NOT EXISTS inventory;

-- Table creation
CREATE TABLE inventory.product (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    description text,
    price decimal(10,2),
    category text,
    in_stock boolean DEFAULT true,
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

-- Generated functions
CREATE OR REPLACE FUNCTION inventory.create_product(
    p_name text,
    p_description text DEFAULT NULL,
    p_price decimal(10,2) DEFAULT NULL,
    p_category text DEFAULT NULL,
    p_in_stock boolean DEFAULT true
) RETURNS uuid AS $$
DECLARE
    v_id uuid;
BEGIN
    INSERT INTO inventory.product (
        name, description, price, category, in_stock,
        created_at, updated_at
    ) VALUES (
        p_name, p_description, p_price, p_category, p_in_stock,
        now(), now()
    ) RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION inventory.update_product(
    p_id uuid,
    p_name text DEFAULT NULL,
    p_description text DEFAULT NULL,
    p_price decimal(10,2) DEFAULT NULL,
    p_category text DEFAULT NULL,
    p_in_stock boolean DEFAULT NULL
) RETURNS void AS $$
BEGIN
    UPDATE inventory.product SET
        name = COALESCE(p_name, name),
        description = COALESCE(p_description, description),
        price = COALESCE(p_price, price),
        category = COALESCE(p_category, category),
        in_stock = COALESCE(p_in_stock, in_stock),
        updated_at = now()
    WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product not found';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION inventory.delete_product(
    p_id uuid
) RETURNS void AS $$
BEGIN
    DELETE FROM inventory.product WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product not found';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Creating a Product

```sql
-- Create a new product
SELECT inventory.create_product(
    'Wireless Headphones',
    'Premium noise-cancelling wireless headphones',
    299.99,
    'Electronics',
    true
);
```

### Reading Products

```sql
-- Get all products
SELECT * FROM inventory.product;

-- Get products by category
SELECT * FROM inventory.product
WHERE category = 'Electronics';

-- Get a specific product
SELECT * FROM inventory.product
WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

### Updating a Product

```sql
-- Update product price and stock status
SELECT inventory.update_product(
    '550e8400-e29b-41d4-a716-446655440000',
    NULL,  -- name (no change)
    NULL,  -- description (no change)
    249.99, -- new price
    NULL,  -- category (no change)
    false  -- out of stock
);
```

### Deleting a Product

```sql
-- Delete a product
SELECT inventory.delete_product(
    '550e8400-e29b-41d4-a716-446655440000'
);
```

## Testing

SpecQL automatically generates comprehensive tests for CRUD operations:

```sql
-- Generated pgTAP tests
SELECT * FROM runtests('inventory.product_crud_test');

-- Example test output:
-- ok 1 - create_product creates valid product
-- ok 2 - create_product validates required fields
-- ok 3 - update_product modifies existing product
-- ok 4 - update_product handles not found
-- ok 5 - delete_product removes product
-- ok 6 - delete_product handles not found
```

## Key Benefits

✅ **Zero Boilerplate**: No manual SQL writing for basic operations
✅ **Automatic Validation**: Required fields and data types enforced
✅ **Consistent API**: All CRUD operations follow the same pattern
✅ **Built-in Testing**: Comprehensive test coverage included
✅ **Security**: Row-level security and permission checks
✅ **Audit Trail**: Automatic timestamp tracking

## Next Steps

- Add [validation patterns](../intermediate/validation.md) for business rules
- Implement [state machines](../basic/state-machine.md) for product lifecycle
- Use [batch operations](../intermediate/batch-operations.md) for bulk updates

---

**See Also:**
- [State Machine Example](state-machine.md)
- [Validation Example](validation.md)
- [CRUD Pattern Reference](../../guides/mutation-patterns/crud-patterns.md)