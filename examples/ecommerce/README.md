# E-commerce Example

**Complete online store built with SpecQL** 🛒

From product catalog to order processing in minutes.

## Overview

This example demonstrates an e-commerce platform with:
- **Products** with pricing and inventory
- **Customers** with addresses
- **Orders** with line items
- **Payments** and fulfillment

**What you get:**
- ✅ Product catalog with variants
- ✅ Shopping cart and checkout
- ✅ Order management
- ✅ Payment processing
- ✅ Inventory tracking
- ✅ Customer management

## Quick Start

### 1. Generate the Schema

```bash
cd examples/ecommerce
specql generate entities/*.yaml
```

### 2. Deploy to Database

```bash
createdb ecommerce_example
cd db/schema
confiture migrate up
```

### 3. Test the System

```sql
-- Create a product
SELECT commerce.create_product(
  name => 'Wireless Headphones',
  sku => 'WH-001',
  description => 'Premium wireless headphones with noise cancellation',
  price => 199.99,
  inventory_count => 50
);

-- Create a customer
SELECT commerce.create_customer(
  email => 'customer@example.com',
  first_name => 'John',
  last_name => 'Shopper'
);

-- Place an order
SELECT commerce.create_order(
  customer_id => (SELECT id FROM commerce.tb_customer WHERE email = 'customer@example.com' LIMIT 1),
  items => ARRAY[
    (SELECT pk_product FROM commerce.tb_product WHERE sku = 'WH-001' LIMIT 1, 1)
  ]::commerce.order_item[]
);
```

## Entities

### Product (`product.yaml`)

Products with pricing and inventory:

```yaml
entity: Product
schema: commerce
description: "Product in the catalog"

fields:
  name: text!
  sku: text!             # Stock keeping unit
  description: markdown
  price: money!          # Rich monetary type
  compare_at_price: money
  inventory_count: integer!
  track_inventory: boolean = true

  # Product details
  weight: decimal        # For shipping
  dimensions: text       # L x W x H

actions:
  - name: create_product
  - name: update_product
  - name: adjust_inventory
```

### Customer (`customer.yaml`)

Customer accounts with addresses:

```yaml
entity: Customer
schema: commerce
description: "Customer account"

fields:
  email: email!
  first_name: text!
  last_name: text!

  # Shipping address (embedded)
  shipping_street: text
  shipping_city: text
  shipping_state: text
  shipping_zip: text
  shipping_country: text

actions:
  - name: create_customer
  - name: update_customer
  - name: update_address
```

### Order (`order.yaml`)

Orders with line items:

```yaml
entity: Order
schema: commerce
description: "Customer order"

fields:
  order_number: text!    # Human-readable order number
  status: enum(pending, paid, shipped, delivered, cancelled)
  total_amount: money!

  customer: ref(Customer)!

  # Shipping
  shipping_amount: money
  tax_amount: money

  # Timestamps
  ordered_at: datetime!
  shipped_at: datetime
  delivered_at: datetime

actions:
  - name: create_order
  - name: update_status
  - name: ship_order
  - name: cancel_order
```

### Payment (`payment.yaml`)

Payment processing:

```yaml
entity: Payment
schema: commerce
description: "Payment for an order"

fields:
  amount: money!
  currency: currencyCode = 'USD'
  status: enum(pending, processing, succeeded, failed)
  payment_method: enum(card, paypal, bank_transfer)

  # Payment processor details
  processor_id: text     # Stripe charge ID, etc.
  last_four: text        # Last 4 digits of card

  order: ref(Order)!

actions:
  - name: process_payment
  - name: refund_payment
```

## Generated Schema

### Tables

```sql
-- Products
CREATE TABLE commerce.tb_product (
  pk_product INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  sku TEXT NOT NULL,
  description TEXT,
  price NUMERIC(19,4) NOT NULL,
  compare_at_price NUMERIC(19,4),
  inventory_count INTEGER NOT NULL,
  track_inventory BOOLEAN DEFAULT true,
  weight NUMERIC(10,2),
  dimensions TEXT,
  -- Audit fields...
);

-- Customers
CREATE TABLE commerce.tb_customer (
  pk_customer INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  shipping_street TEXT,
  shipping_city TEXT,
  shipping_state TEXT,
  shipping_zip TEXT,
  shipping_country TEXT,
  -- Audit fields...
);

-- Orders
CREATE TABLE commerce.tb_order (
  pk_order INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  order_number TEXT NOT NULL,
  status TEXT CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),
  total_amount NUMERIC(19,4) NOT NULL,
  fk_customer INTEGER NOT NULL,
  shipping_amount NUMERIC(19,4),
  tax_amount NUMERIC(19,4),
  ordered_at TIMESTAMPTZ NOT NULL,
  shipped_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  -- Audit fields...
);

-- Payments
CREATE TABLE commerce.tb_payment (
  pk_payment INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  amount NUMERIC(19,4) NOT NULL,
  currency TEXT DEFAULT 'USD',
  status TEXT CHECK (status IN ('pending', 'processing', 'succeeded', 'failed')),
  payment_method TEXT CHECK (payment_method IN ('card', 'paypal', 'bank_transfer')),
  processor_id TEXT,
  last_four TEXT,
  fk_order INTEGER NOT NULL,
  -- Audit fields...
);
```

### Rich Type Validation

```sql
-- Email validation
ALTER TABLE commerce.tb_customer
ADD CONSTRAINT customer_email_check
CHECK (email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$');

-- Money validation (automatic)
-- SKU uniqueness
ALTER TABLE commerce.tb_product
ADD CONSTRAINT tb_product_sku_key UNIQUE (sku);

-- Order number uniqueness
ALTER TABLE commerce.tb_order
ADD CONSTRAINT tb_order_order_number_key UNIQUE (order_number);
```

## Business Logic

### Order Processing

```sql
-- Create order with inventory check
CREATE FUNCTION commerce.create_order(
  customer_id UUID,
  items commerce.order_item[]
) RETURNS app.mutation_result AS $$
DECLARE
  v_order_id UUID;
  v_total NUMERIC(19,4) := 0;
  v_item commerce.order_item;
BEGIN
  -- Validate inventory for all items
  FOREACH v_item IN ARRAY items LOOP
    PERFORM commerce.check_inventory(v_item.product_id, v_item.quantity);
    v_total := v_total + commerce.get_item_price(v_item.product_id) * v_item.quantity;
  END LOOP;

  -- Create order
  INSERT INTO commerce.tb_order (
    order_number, fk_customer, total_amount, ordered_at
  ) VALUES (
    commerce.generate_order_number(),
    commerce.customer_pk(customer_id::TEXT),
    v_total,
    now()
  ) RETURNING id INTO v_order_id;

  -- Create order items and update inventory
  FOREACH v_item IN ARRAY items LOOP
    PERFORM commerce.add_order_item(v_order_id, v_item);
  END LOOP;

  RETURN app.success_result('Order created successfully');
END;
$$ LANGUAGE plpgsql;
```

### Inventory Management

```sql
-- Check inventory availability
CREATE FUNCTION commerce.check_inventory(
  product_id INTEGER,
  requested_quantity INTEGER
) RETURNS VOID AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM commerce.tb_product
    WHERE pk_product = product_id
      AND track_inventory = true
      AND inventory_count >= requested_quantity
  ) THEN
    RAISE EXCEPTION 'Insufficient inventory for product %', product_id;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Adjust inventory
CREATE FUNCTION commerce.adjust_inventory(
  product_id UUID,
  adjustment INTEGER
) RETURNS app.mutation_result AS $$
DECLARE
  v_pk INTEGER;
BEGIN
  v_pk := commerce.product_pk(product_id::TEXT);

  UPDATE commerce.tb_product
  SET inventory_count = inventory_count + adjustment
  WHERE pk_product = v_pk;

  RETURN app.success_result('Inventory adjusted');
END;
$$ LANGUAGE plpgsql;
```

## GraphQL API

### Product Catalog

```graphql
query GetProducts {
  products(filter: { inventoryCount: { gt: 0 } }) {
    edges {
      node {
        id
        name
        sku
        price
        inventoryCount
      }
    }
  }
}
```

### Order Management

```graphql
mutation CreateOrder($input: CreateOrderInput!) {
  createOrder(input: $input) {
    success
    message
    object {
      id
      orderNumber
      totalAmount
      status
      items {
        product {
          id
          name
          sku
        }
        quantity
        price
      }
    }
  }
}
```

### Customer Portal

```graphql
query CustomerOrders($customerId: UUID!) {
  orders(filter: { customer: { id: { eq: $customerId } } }) {
    edges {
      node {
        id
        orderNumber
        status
        totalAmount
        orderedAt
        payments {
          amount
          status
          paymentMethod
        }
      }
    }
  }
}
```

## Extending the Example

### Product Variants

```yaml
entity: ProductVariant
schema: commerce
description: "Product variant (size, color, etc.)"

fields:
  product: ref(Product)!
  name: text!              # "Small", "Red", etc.
  sku: text!               # Variant-specific SKU
  price_modifier: money    # Additional cost
  inventory_count: integer!

actions:
  - name: create_variant
  - name: update_inventory
```

### Shopping Cart

```yaml
entity: Cart
schema: commerce
description: "Shopping cart"

fields:
  customer: ref(Customer)
  session_id: text         # For anonymous carts
  items: json              # Cart items as JSON

actions:
  - name: add_to_cart
  - name: update_quantity
  - name: remove_from_cart
  - name: convert_to_order
```

### Reviews and Ratings

```yaml
entity: ProductReview
schema: commerce
description: "Customer review of a product"

fields:
  product: ref(Product)!
  customer: ref(Customer)!
  rating: integer          # 1-5 stars
  title: text
  content: markdown
  verified: boolean = false

actions:
  - name: create_review
  - name: moderate_review
```

## File Structure

```
examples/ecommerce/
├── README.md
├── entities/
│   ├── product.yaml
│   ├── customer.yaml
│   ├── order.yaml
│   └── payment.yaml
└── generated/
    └── db/schema/
        ├── 10_tables/
        ├── 20_helpers/
        └── 30_functions/
```

## Learning Points

### Financial Data
- `money` type for precise monetary calculations
- Currency handling
- Tax and shipping calculations

### Complex Relationships
- Order to line items
- Customer to orders
- Product inventory management

### Business Workflows
- Order lifecycle (pending → paid → shipped → delivered)
- Payment processing
- Inventory adjustments

### Data Validation
- SKU uniqueness
- Email validation
- Inventory constraints

## Next Steps

- **Run the example**: Set up a complete e-commerce system
- **Add features**: Shopping cart, reviews, discounts
- **Check other examples**: See `examples/crm/` or `examples/saas-multi-tenant/`
- **Read guides**: Learn more in `docs/guides/`

---

**From YAML to online store in minutes.** 🛒