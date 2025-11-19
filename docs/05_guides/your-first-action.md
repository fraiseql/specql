# Your First Action: Business Logic Implementation

> **Complete this guide in 20 minutes to implement complex business workflows with SpecQL actions**

## What You'll Build

A complete order processing system with:
- ✅ Multi-step business workflows
- ✅ Validation and error handling
- ✅ Transaction safety
- ✅ Complex business rules
- ✅ Integration between multiple entities

## Prerequisites

- ✅ SpecQL installed
- ✅ PostgreSQL running
- ✅ Completed [Your First Entity](your-first-entity.md) guide
- ✅ Basic understanding of [Actions](../03_core-concepts/actions.md)

## Scenario: E-commerce Order Processing

We'll build an order processing system that handles:
1. **Validation**: Check inventory, payment, user status
2. **Order Creation**: Create order from cart
3. **Inventory Management**: Reduce stock levels
4. **Payment Processing**: Handle payment (simulated)
5. **Notifications**: Send confirmations
6. **Error Handling**: Rollback on failures

## Step 1: Define Required Entities (3 minutes)

Create entities for our order processing system:

**user.yaml:**
```yaml
entity: User
schema: ecommerce
description: "Customer account"

fields:
  email: email!
  balance: money!          # Account balance for payments
  status: enum(active, suspended, banned)!
```

**product.yaml:**
```yaml
entity: Product
schema: ecommerce
description: "Product in catalog"

fields:
  name: text!
  price: money!
  stock_quantity: integer(0)!
  sku: text!
```

**cart.yaml:**
```yaml
entity: Cart
schema: ecommerce
description: "Shopping cart"

fields:
  user_id: uuid!           # Reference to User.id
  total: money!
  item_count: integer(0)!

actions:
  - name: add_to_cart
    description: "Add product to cart"
    steps:
      - validate: $quantity > 0, error: "Quantity must be positive"
      - validate: $product_id EXISTS IN Product, error: "Product not found"
      - insert: CartItem VALUES (
          cart_id: $cart_id,
          product_id: $product_id,
          quantity: $quantity,
          price: Product.price WHERE id = $product_id
        )
      - update: Cart SET total = total + ($quantity * Product.price),
                      item_count = item_count + $quantity
      - return: "Item added to cart"
```

**cart_item.yaml:**
```yaml
entity: CartItem
schema: ecommerce
description: "Item in shopping cart"

fields:
  cart_id: uuid!
  product_id: uuid!
  quantity: integer(1)!     # Minimum 1
  price: money!             # Price at time of adding
```

**order.yaml:**
```yaml
entity: Order
schema: ecommerce
description: "Customer order"

fields:
  user_id: uuid!
  total: money!
  status: enum(pending, paid, shipped, delivered, cancelled)!
  shipping_address: text
```

## Step 2: Implement Order Processing Action (5 minutes)

Create the main order processing workflow:

**order_actions.yaml:**
```yaml
entity: Order
schema: ecommerce

actions:
  - name: process_order
    description: "Complete order from shopping cart"
    steps:
      # Step 1: Validate cart and user
      - validate: $cart_id EXISTS IN Cart, error: "Cart not found"
      - validate: Cart.user_id = $user_id, error: "Cart does not belong to user"
      - validate: Cart.total > 0, error: "Cart is empty"
      - validate: User.status = 'active', error: "Account is not active"
      - validate: User.balance >= Cart.total, error: "Insufficient funds"

      # Step 2: Check inventory for all items
      - foreach: CartItem WHERE cart_id = $cart_id as item
        do:
          - validate: item.quantity <= Product.stock_quantity WHERE id = item.product_id,
                     error: "Insufficient stock for {Product.name}"

      # Step 3: Create the order
      - insert: Order VALUES (
          user_id: $user_id,
          total: Cart.total WHERE id = $cart_id,
          status: 'pending',
          shipping_address: $shipping_address
        )

      # Step 4: Process payment (deduct from balance)
      - update: User SET balance = balance - Cart.total WHERE id = Cart.id

      # Step 5: Update inventory
      - foreach: CartItem WHERE cart_id = $cart_id as item
        do:
          - update: Product SET stock_quantity = stock_quantity - item.quantity
                           WHERE id = item.product_id

      # Step 6: Clear the cart
      - delete: CartItem WHERE cart_id = $cart_id
      - delete: Cart WHERE id = $cart_id

      # Step 7: Send confirmation
      - call: send_order_confirmation

      # Step 8: Success
      - return: "Order processed successfully"
```

## Step 3: Add Helper Actions (4 minutes)

Create supporting actions for notifications and validation:

**notification_actions.yaml:**
```yaml
entity: Notification
schema: ecommerce
description: "User notifications"

fields:
  user_id: uuid!
  type: enum(order_confirmation, payment_failed, shipping_update)!
  message: text!
  sent_at: datetime

actions:
  - name: send_order_confirmation
    description: "Send order confirmation to user"
    steps:
      - insert: Notification VALUES (
          user_id: $user_id,
          type: 'order_confirmation',
          message: 'Your order has been placed successfully',
          sent_at: now()
        )
      - return: "Confirmation sent"
```

**validation_actions.yaml:**
```yaml
entity: Validation
schema: ecommerce

actions:
  - name: validate_order_readiness
    description: "Comprehensive order validation"
    steps:
      # User validation
      - validate: User.status = 'active', error: "Account suspended"
      - validate: User.email_verified = true, error: "Email not verified"

      # Cart validation
      - validate: Cart EXISTS, error: "Cart not found"
      - validate: Cart.total > 0, error: "Cart is empty"
      - validate: Cart.user_id = $user_id, error: "Cart access denied"

      # Inventory validation
      - foreach: CartItem WHERE cart_id = $cart_id as item
        do:
          - validate: Product.stock_quantity >= item.quantity WHERE id = item.product_id,
                     error: "Insufficient stock: {Product.name}"

      # Payment validation
      - validate: User.balance >= Cart.total, error: "Insufficient balance: {User.balance}"

      - return: "Order ready for processing"
```

## Step 4: Generate and Deploy (3 minutes)

```bash
# Generate all entities
for file in *.yaml; do
  specql generate "$file"
done

# Create database and run migrations
createdb ecommerce_orders
cat db/migrations/*.sql | psql ecommerce_orders

# Check generated schema
psql ecommerce_orders -c "\dt ecommerce.*"
```

## Step 5: Test the Complete Workflow (5 minutes)

```bash
# Set up test data
psql ecommerce_orders << 'EOF'
-- Create test user
INSERT INTO ecommerce.tb_user (id, email, balance, status)
VALUES ('user-123', 'test@example.com', 1000.00, 'active');

-- Create test product
INSERT INTO ecommerce.tb_product (id, name, price, stock_quantity, sku)
VALUES ('prod-456', 'Test Product', 99.99, 10, 'TEST-001');

-- Create cart
INSERT INTO ecommerce.tb_cart (id, user_id, total, item_count)
VALUES ('cart-789', 'user-123', 99.99, 1);

-- Add item to cart
INSERT INTO ecommerce.tb_cart_item (cart_id, product_id, quantity, price)
VALUES ('cart-789', 'prod-456', 1, 99.99);
EOF

# Test the order processing
psql ecommerce_orders << 'EOF'
-- Process the order
SELECT * FROM ecommerce.process_order(
  'user-123'::uuid,     -- user_id
  'cart-789'::uuid,     -- cart_id
  '123 Main St, Anytown, USA'  -- shipping_address
);

-- Verify results
SELECT 'User balance:' as info, balance FROM ecommerce.tb_user WHERE id = 'user-123';
SELECT 'Product stock:' as info, stock_quantity FROM ecommerce.tb_product WHERE id = 'prod-456';
SELECT 'Orders created:' as info, count(*) FROM ecommerce.tb_order;
SELECT 'Notifications sent:' as info, count(*) FROM ecommerce.tb_notification;
EOF
```

**Expected successful output:**
```
process_order
----------------
Order processed successfully

info          | balance
--------------+---------
User balance: | 900.01

info          | stock_quantity
--------------+----------------
Product stock: | 9

info          | count
--------------+-------
Orders created: | 1

info          | count
--------------+-------
Notifications sent: | 1
```

## Step 6: Test Error Handling (3 minutes)

```bash
# Test insufficient funds
psql ecommerce_orders << 'EOF'
-- Create another cart with expensive item
INSERT INTO ecommerce.tb_cart (id, user_id, total, item_count)
VALUES ('cart-999', 'user-123', 2000.00, 1);

-- Try to process (should fail)
SELECT * FROM ecommerce.process_order(
  'user-123'::uuid,
  'cart-999'::uuid,
  '123 Main St'
);
EOF
```

**Expected error:**
```
ERROR: Insufficient funds
```

## Step 7: Explore Generated GraphQL (1 minute)

```bash
# Check the generated GraphQL mutations
grep -A 10 "processOrder" db/schema/ecommerce.order.graphql.sql
```

**Generated GraphQL:**
```graphql
type Mutation {
  processOrder(
    userId: UUID!
    cartId: UUID!
    shippingAddress: String
  ): MutationResult!
}
```

## Congratulations! 🎉

You built a complete order processing system with:

- ✅ **Multi-entity coordination** (User, Cart, Product, Order)
- ✅ **Complex business logic** with validation and error handling
- ✅ **Transactional safety** (all-or-nothing operations)
- ✅ **Inventory management** with stock validation
- ✅ **Payment processing** with balance checks
- ✅ **Notification system** for user feedback
- ✅ **GraphQL integration** for frontend consumption

## What You Learned

### Action Design Patterns
- **Validation first**: Check all preconditions before making changes
- **Transactional workflows**: Complex business processes in single transactions
- **Error handling**: Clear error messages and rollback behavior
- **Entity relationships**: Coordinating changes across multiple tables

### Advanced Action Features
- **Foreach loops**: Processing collections of items
- **Conditional logic**: If/then/else branching
- **Action composition**: Calling other actions
- **Parameter passing**: Using variables across steps

### Business Logic Best Practices
- **Fail fast**: Validate early, fail with clear messages
- **Atomic operations**: Either everything succeeds or nothing does
- **Data consistency**: Maintain integrity across related entities
- **User feedback**: Clear success/error messages

## Next Steps

### Enhance the System
- [Add payment integration](payment-integration.md)
- [Implement order status tracking](order-workflow.md)
- [Add shipping calculations](shipping-logic.md)

### Advanced Patterns
- [Complex validation rules](advanced-validation.md)
- [Event-driven actions](event-processing.md)
- [Batch operations](bulk-processing.md)

### Production Considerations
- [Add authentication](authentication.md)
- [Implement rate limiting](rate-limiting.md)
- [Add audit logging](audit-trails.md)

## Troubleshooting

### "Function does not exist"
```bash
# Make sure all migrations ran
psql ecommerce_orders -c "\df ecommerce.*"
```

### "Insufficient privilege"
```bash
# Check database permissions
psql ecommerce_orders -c "\dp ecommerce.*"
```

### Actions not working as expected
```bash
# Debug by running individual steps
psql ecommerce_orders -c "SELECT * FROM ecommerce.validate_order_readiness('user-123'::uuid, 'cart-789'::uuid);"
```

### GraphQL schema not generated
```bash
# Check FraiseQL integration
ls -la db/schema/*graphql*
```

---

**Time spent: 20 minutes. Business logic implemented: Complex order processing workflow. Production reliability: Transaction-safe, validated, error-handled.** 🚀</content>
</xai:function_call