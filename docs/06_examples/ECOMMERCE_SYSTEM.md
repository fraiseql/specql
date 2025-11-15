# E-commerce System Example

**What You'll Build**: A complete e-commerce platform with products, orders, inventory, and customer management.

**Time**: 30 minutes
**Complexity**: Intermediate

## System Overview

Our e-commerce system will have:
- **Products**: Items for sale with variants and pricing
- **Categories**: Product organization hierarchy
- **Customers**: User accounts and profiles
- **Orders**: Purchase transactions
- **Order Items**: Individual line items in orders
- **Inventory**: Stock management and tracking

## Architecture

```
Category (1) ──< (N) Product
   │                    │
   │                    │
   └──< (N) Subcategory  │
                        │
Customer (1) ───────────┼──< (N) Order
                        │         │
                        │         │
Product ────────────────┼──< (N) OrderItem
   │                    │
   │                    │
   └──< (1) Inventory ──┘
```

## Step 1: Create Category Entity

Create `entities/shop/category.yaml`:

```yaml
entity: Category
schema: shop
description: Product category for organization

fields:
  # Identity
  name: text
  slug: text
  description: text

  # Hierarchy
  parent: ref(Category)  # Self-referencing for subcategories

  # Display
  image_url: url
  display_order: integer

  # Status
  is_active: boolean

indexes:
  - fields: [slug]
    unique: true
  - fields: [parent_id, display_order]
  - fields: [is_active]

actions:
  - name: activate_category
    description: Make category visible to customers
    requires: caller.can_manage_categories
    steps:
      - update: Category SET is_active = true
      - log: "Category activated"

  - name: deactivate_category
    description: Hide category from customers
    requires: caller.can_manage_categories
    steps:
      - validate: NOT EXISTS (SELECT 1 FROM Product WHERE category_id = id AND is_active = true)
        error: "category_has_active_products"
      - update: Category SET is_active = false
      - log: "Category deactivated"
```

## Step 2: Create Product Entity

Create `entities/shop/product.yaml`:

```yaml
entity: Product
schema: shop
description: An item available for purchase

fields:
  # Identity
  name: text
  slug: text
  description: text
  short_description: text

  # Categorization
  category: ref(Category)

  # Pricing
  base_price: decimal
  sale_price: decimal  # Nullable for sale items
  cost_price: decimal  # Internal cost

  # Media
  main_image_url: url
  additional_images: json  # Array of image URLs

  # Inventory
  sku: text  # Stock Keeping Unit
  track_inventory: boolean
  is_active: boolean

  # SEO
  meta_title: text
  meta_description: text

  # Variants (for future expansion)
  has_variants: boolean
  variant_options: json  # Size, color, etc.

indexes:
  - fields: [slug]
    unique: true
  - fields: [sku]
    unique: true
  - fields: [category_id, is_active]
  - fields: [is_active, base_price]

actions:
  - name: put_on_sale
    description: Apply sale pricing
    requires: caller.can_manage_products
    steps:
      - validate: sale_price IS NOT NULL AND sale_price < base_price
        error: "invalid_sale_price"
      - update: Product SET sale_price = ?
      - notify: marketing_team
      - log: "Product put on sale"

  - name: remove_sale
    description: Remove sale pricing
    requires: caller.can_manage_products
    steps:
      - update: Product SET sale_price = NULL
      - log: "Sale removed from product"

  - name: activate_product
    description: Make product available for purchase
    requires: caller.can_manage_products
    steps:
      - update: Product SET is_active = true
      - log: "Product activated"

  - name: deactivate_product
    description: Remove product from store
    requires: caller.can_manage_products
    steps:
      - update: Product SET is_active = false
      - log: "Product deactivated"
```

## Step 3: Create Inventory Entity

Create `entities/shop/inventory.yaml`:

```yaml
entity: Inventory
schema: shop
description: Stock levels for products

fields:
  # Relationships
  product: ref(Product)

  # Stock levels
  quantity_available: integer
  quantity_reserved: integer  # In shopping carts/orders
  quantity_on_order: integer  # From suppliers

  # Thresholds
  low_stock_threshold: integer
  out_of_stock_threshold: integer

  # Auto-management
  auto_reorder: boolean
  reorder_quantity: integer
  reorder_point: integer

indexes:
  - fields: [product_id]
    unique: true
  - fields: [quantity_available]

actions:
  - name: adjust_stock
    description: Manually adjust inventory levels
    requires: caller.can_manage_inventory
    steps:
      - update: Inventory SET quantity_available = quantity_available + ?
      - validate: quantity_available >= 0
        error: "negative_stock_not_allowed"
      - log: "Stock adjusted by {adjustment}"

  - name: reserve_stock
    description: Reserve items for an order
    requires: system  # Called by order system
    steps:
      - validate: quantity_available >= ?
        error: "insufficient_stock"
      - update: Inventory SET
          quantity_available = quantity_available - ?,
          quantity_reserved = quantity_reserved + ?

  - name: release_stock
    description: Release reserved items (order cancelled)
    requires: system
    steps:
      - update: Inventory SET
          quantity_available = quantity_available + ?,
          quantity_reserved = quantity_reserved - ?

  - name: check_low_stock
    description: Alert when stock is low
    steps:
      - validate: quantity_available <= low_stock_threshold
      - notify: inventory_manager
      - log: "Low stock alert for product"
```

## Step 4: Create Customer Entity

Create `entities/shop/customer.yaml`:

```yaml
entity: Customer
schema: shop
description: Registered customer account

fields:
  # Identity
  email: email
  first_name: text
  last_name: text

  # Account
  password_hash: text
  is_active: boolean
  email_verified: boolean

  # Contact
  phone: text

  # Preferences
  marketing_opt_in: boolean
  preferred_currency: text
  language: text

  # Loyalty
  total_orders: integer
  total_spent: decimal
  loyalty_points: integer

indexes:
  - fields: [email]
    unique: true
  - fields: [is_active, created_at]

actions:
  - name: verify_email
    description: Mark email as verified
    steps:
      - update: Customer SET email_verified = true
      - log: "Email verified"

  - name: add_loyalty_points
    description: Add points to customer account
    steps:
      - update: Customer SET loyalty_points = loyalty_points + ?
      - log: "Added {points} loyalty points"

  - name: deactivate_account
    description: Deactivate customer account
    requires: caller.can_manage_customers
    steps:
      - update: Customer SET is_active = false
      - log: "Customer account deactivated"
```

## Step 5: Create Order Entity

Create `entities/shop/order.yaml`:

```yaml
entity: Order
schema: shop
description: Customer purchase order

fields:
  # Relationships
  customer: ref(Customer)

  # Order info
  order_number: text  # Human-readable order number
  status: enum(pending, confirmed, processing, shipped, delivered, cancelled, refunded)

  # Totals
  subtotal: decimal
  tax_amount: decimal
  shipping_amount: decimal
  discount_amount: decimal
  total_amount: decimal

  # Shipping
  shipping_address: json  # Structured address data
  shipping_method: text
  tracking_number: text

  # Payment
  payment_status: enum(pending, paid, failed, refunded)
  payment_method: text
  payment_reference: text

  # Timestamps
  ordered_at: timestamp
  shipped_at: timestamp
  delivered_at: timestamp

indexes:
  - fields: [order_number]
    unique: true
  - fields: [customer_id, ordered_at]
  - fields: [status, ordered_at]
  - fields: [payment_status]

actions:
  - name: confirm_order
    description: Confirm pending order
    requires: system
    steps:
      - validate: status = 'pending'
        error: "order_not_pending"
      - update: Order SET status = 'confirmed'
      - notify: customer
      - log: "Order confirmed"

  - name: process_order
    description: Start processing confirmed order
    requires: warehouse_staff
    steps:
      - validate: status = 'confirmed' AND payment_status = 'paid'
        error: "order_not_ready_for_processing"
      - update: Order SET status = 'processing'
      - log: "Order moved to processing"

  - name: ship_order
    description: Mark order as shipped
    requires: warehouse_staff
    steps:
      - validate: status = 'processing'
        error: "order_not_processing"
      - update: Order SET
          status = 'shipped',
          shipped_at = NOW(),
          tracking_number = ?
      - notify: customer
      - log: "Order shipped with tracking {tracking_number}"

  - name: cancel_order
    description: Cancel an order
    requires: customer_service
    steps:
      - validate: status IN ('pending', 'confirmed')
        error: "order_cannot_be_cancelled"
      - update: Order SET status = 'cancelled'
      - release_inventory: order_items  # Custom action to release stock
      - process_refund: payment_reference
      - notify: customer
      - log: "Order cancelled"
```

## Step 6: Create OrderItem Entity

Create `entities/shop/order_item.yaml`:

```yaml
entity: OrderItem
schema: shop
description: Individual item in an order

fields:
  # Relationships
  order: ref(Order)
  product: ref(Product)

  # Item details
  product_name: text  # Snapshot at order time
  product_sku: text
  unit_price: decimal
  quantity: integer

  # Totals
  line_total: decimal

  # Status
  status: enum(pending, confirmed, backordered, shipped, delivered, cancelled, returned)

indexes:
  - fields: [order_id, product_id]
  - fields: [status]

actions:
  - name: ship_item
    description: Mark item as shipped
    requires: warehouse_staff
    steps:
      - validate: status IN ('confirmed', 'backordered')
        error: "item_not_ready_to_ship"
      - update: OrderItem SET status = 'shipped'
      - log: "Order item shipped"

  - name: cancel_item
    description: Cancel individual item
    requires: customer_service
    steps:
      - validate: status IN ('pending', 'confirmed')
        error: "item_cannot_be_cancelled"
      - update: OrderItem SET status = 'cancelled'
      - release_inventory: product_id, quantity
      - log: "Order item cancelled"
```

## Step 7: Generate the E-commerce System

```bash
# Create output directory
mkdir -p output/ecommerce

# Generate all entities
specql generate entities/shop/*.yaml --output output/ecommerce

# You should see generation for all 6 entities
```

## Step 8: Inspect Generated Code

### PostgreSQL Schema
```bash
# Check the generated tables
ls output/ecommerce/postgresql/shop/

# You'll see:
# - 01_tables.sql (all table definitions)
# - 02_functions.sql (business logic functions)
# - 03_triggers.sql (audit and automation triggers)
```

### Business Logic Functions
```bash
# Check key functions
grep -A 5 "fn_order_confirm" output/ecommerce/postgresql/shop/02_functions.sql
grep -A 5 "fn_inventory_reserve_stock" output/ecommerce/postgresql/shop/02_functions.sql
```

### Java/Spring Boot
```bash
# Check generated services
ls output/ecommerce/java/com/example/shop/

# You'll see complete Spring Boot application:
# - ProductService.java (with inventory management)
# - OrderService.java (with payment processing)
# - CustomerService.java (with loyalty programs)
```

## Step 9: Test the E-commerce System

If you have PostgreSQL running:

```bash
# Create test database
createdb ecommerce_test

# Apply schema
psql ecommerce_test < output/ecommerce/postgresql/shop/01_tables.sql
psql ecommerce_test < output/ecommerce/postgresql/shop/02_functions.sql

# Insert test data
psql ecommerce_test << 'EOF'
-- Create a category
INSERT INTO shop.tb_category (name, slug, is_active)
VALUES ('Electronics', 'electronics', true);

-- Create a product
INSERT INTO shop.tb_product (name, slug, base_price, sku, track_inventory, is_active, category_id)
VALUES ('Wireless Headphones', 'wireless-headphones', 99.99, 'WH-001', true, true, 1);

-- Create inventory
INSERT INTO shop.tb_inventory (product_id, quantity_available, low_stock_threshold)
VALUES (1, 50, 10);

-- Create a customer
INSERT INTO shop.tb_customer (email, first_name, last_name, is_active)
VALUES ('john@example.com', 'John', 'Doe', true);

-- Create an order
INSERT INTO shop.tb_order (customer_id, order_number, status, subtotal, total_amount, payment_status)
VALUES (1, 'ORD-001', 'pending', 99.99, 99.99, 'pending');

-- Add order item
INSERT INTO shop.tb_order_item (order_id, product_id, product_name, unit_price, quantity, line_total)
VALUES (1, 1, 'Wireless Headphones', 99.99, 1, 99.99);
EOF

# Test business logic
psql ecommerce_test -c "SELECT shop.fn_order_confirm(1);"
psql ecommerce_test -c "SELECT * FROM shop.tv_order WHERE id = 1;"
psql ecommerce_test -c "SELECT * FROM shop.tv_inventory WHERE product_id = 1;"
```

## E-commerce Patterns Implemented

### 1. Inventory Management
- **Stock tracking**: Automatic quantity management
- **Reservations**: Items held during checkout
- **Low stock alerts**: Automatic notifications
- **Backorders**: Handle out-of-stock items

### 2. Order Fulfillment Workflow
```
Pending → Confirmed → Processing → Shipped → Delivered
   ↓         ↓           ↓           ↓
Cancelled  Cancelled  Cancelled  Returned
```

### 3. Price Calculations
- **Base pricing**: Standard product prices
- **Sale pricing**: Temporary discounts
- **Tax calculations**: Automatic tax application
- **Shipping costs**: Dynamic shipping fees

### 4. Discount Codes
- **Percentage discounts**: 10% off entire order
- **Fixed amount discounts**: $5 off orders over $50
- **Free shipping**: Remove shipping costs
- **Product-specific discounts**: Special pricing for specific items

### 5. Customer Loyalty
- **Points system**: Earn points on purchases
- **Tier benefits**: Different perks by spending level
- **Referral bonuses**: Rewards for bringing new customers

### 6. Audit Trail
All changes automatically logged with:
- Who made the change
- When it was made
- What was changed
- Why it was changed

## Advanced Features

### Shopping Cart
```yaml
entity: Cart
schema: shop
fields:
  customer: ref(Customer)
  items: json  # Array of {product_id, quantity, price}
  expires_at: timestamp

actions:
  - name: add_item
  - name: remove_item
  - name: update_quantity
  - name: apply_discount
  - name: checkout
```

### Payment Processing
```yaml
entity: Payment
schema: shop
fields:
  order: ref(Order)
  amount: decimal
  method: enum(credit_card, paypal, bank_transfer)
  status: enum(pending, processing, completed, failed, refunded)
  transaction_id: text

actions:
  - name: process_payment
  - name: refund_payment
  - name: chargeback
```

## Full Source Code

All YAML files for this example:
- [View Source](../../examples/ecommerce/)
- [View on GitHub](https://github.com/fraiseql/specql/tree/main/examples/ecommerce)

## Next Steps

- Add payment gateway integration
- Implement shopping cart functionality
- Add product reviews and ratings
- Create admin dashboard
- Set up automated email notifications
- Implement search and filtering

This e-commerce system demonstrates how SpecQL handles complex business workflows, inventory management, and multi-table transactions while generating production-ready code across multiple languages.