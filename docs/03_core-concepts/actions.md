# Actions: Declarative Business Logic Engine

> **SpecQL actions: Write business workflows in YAML, get production PL/pgSQL functions**

## Overview

Actions are SpecQL's **declarative business logic engine**. Instead of writing imperative code, you describe **what** should happen using steps, and SpecQL generates the **how** as optimized PL/pgSQL functions.

Actions turn business requirements into executable, validated, transactional database operations.

## Why Actions Matter

### Traditional Approach (Complex)

```python
# Django view - business logic mixed with infrastructure
def create_order(request):
    # Validation
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    # Business logic
    cart = Cart.objects.get(user=request.user)
    if cart.total > request.user.balance:
        return JsonResponse({"error": "Insufficient funds"}, status=400)

    # Transaction management
    with transaction.atomic():
        # Create order
        order = Order.objects.create(
            user=request.user,
            total=cart.total,
            status='pending'
        )

        # Update inventory
        for item in cart.items.all():
            item.product.stock -= item.quantity
            item.product.save()

        # Clear cart
        cart.items.all().delete()

        # Send notification
        send_order_confirmation_email(order)

    return JsonResponse({"order_id": order.id})
```

### SpecQL Approach (Declarative)

```yaml
actions:
  - name: create_order
    description: "Create order from user's cart"
    steps:
      - validate: user_authenticated = true
      - validate: cart_total <= user_balance
      - insert: Order FROM cart_data
      - update: Product REDUCE stock WHERE product_id IN cart_items
      - delete: CartItem WHERE cart_id = $cart_id
      - call: send_order_confirmation_email
      - return: "Order created successfully"
```

**Result**: Same functionality, but declarative, validated, and automatically transactional.

## Action Structure

Every action has a name, optional description, and a sequence of steps:

```yaml
actions:
  - name: action_name                    # Required: unique identifier
    description: "What this action does" # Optional: human-readable
    steps:                              # Required: what to do
      - validate: condition
      - update: Entity SET field = value
      - call: another_action
```

## Step Types

SpecQL supports **8 step types** for different business operations:

### 1. validate - Business Rules

**Purpose**: Check conditions before proceeding
**Use**: Business rules, security checks, data validation

```yaml
steps:
  - validate: user_authenticated = true
  - validate: order_total > 0
  - validate: product_in_stock = true
  - validate: user_age >= 18, error: "Must be 18 or older"
```

**Generated SQL**: CHECK constraints and conditional logic

### 2. update - Data Changes

**Purpose**: Modify existing data
**Use**: Status changes, quantity updates, field modifications

```yaml
steps:
  - update: User SET last_login = now()
  - update: Product SET stock = stock - $quantity WHERE id = $product_id
  - update: Order SET status = 'shipped', shipped_at = now()
```

**Generated SQL**: UPDATE statements with proper WHERE clauses

### 3. insert - New Data

**Purpose**: Create new records
**Use**: New entities, audit logs, related data

```yaml
steps:
  - insert: OrderLog VALUES (order_id: $order_id, action: 'created')
  - insert: Notification VALUES (user_id: $user_id, message: 'Order placed')
```

**Generated SQL**: INSERT statements with Trinity pattern

### 4. delete - Remove Data

**Purpose**: Soft or hard delete records
**Use**: Cleanup, archiving, business rules

```yaml
steps:
  - delete: CartItem WHERE cart_id = $cart_id  # Hard delete
  - update: User SET deleted_at = now()        # Soft delete
```

**Generated SQL**: DELETE or UPDATE (for soft deletes)

### 5. call - Action Composition

**Purpose**: Call other actions
**Use**: Reusable logic, complex workflows

```yaml
steps:
  - call: validate_payment_method
  - call: process_payment
  - call: send_receipt_email
```

**Generated SQL**: Function calls within transaction

### 6. if - Conditional Logic

**Purpose**: Branch based on conditions
**Use**: Business rules, error handling

```yaml
steps:
  - if: user_type = 'premium'
    then:
      - update: Order SET priority = 'high'
      - call: send_priority_notification
    else:
      - update: Order SET priority = 'normal'
```

**Generated SQL**: IF/ELSE blocks

### 7. foreach - Bulk Operations

**Purpose**: Process collections
**Use**: Batch updates, list processing

```yaml
steps:
  - foreach: order_items as item
    do:
      - update: Product SET stock = stock - item.quantity WHERE id = item.product_id
```

**Generated SQL**: Loops with proper iteration

### 8. notify - Event Publishing

**Purpose**: Trigger external systems
**Use**: Webhooks, messaging, integrations

```yaml
steps:
  - notify: order_created, payload: {order_id: $order_id, user_id: $user_id}
```

**Generated SQL**: Event triggers and notifications

## Real-World Examples

### E-commerce Order Processing

```yaml
actions:
  - name: place_order
    description: "Complete order from shopping cart"
    steps:
      # Validation
      - validate: cart_total > 0
      - validate: payment_method_valid = true
      - validate: all_items_in_stock = true

      # Business logic
      - insert: Order FROM cart_data
      - update: Product REDUCE stock FOR EACH cart_item
      - update: User DEDUCT cart_total FROM balance
      - delete: CartItem WHERE cart_id = $cart_id

      # Notifications
      - call: send_order_confirmation
      - notify: order_placed

      # Success
      - return: "Order placed successfully"
```

### User Registration with Validation

```yaml
actions:
  - name: register_user
    description: "Register new user account"
    steps:
      - validate: email_not_exists = true, error: "Email already registered"
      - validate: password_strength >= 8, error: "Password too weak"
      - validate: terms_accepted = true, error: "Terms must be accepted"

      - insert: User VALUES (
          email: $email,
          password_hash: $password_hash,
          status: 'pending'
        )

      - call: send_verification_email
      - return: "Registration successful, check email for verification"
```

### Subscription Management

```yaml
actions:
  - name: upgrade_subscription
    description: "Upgrade user to premium subscription"
    steps:
      - validate: user_active = true
      - validate: payment_method_valid = true
      - validate: not_already_premium = true

      - if: proration_needed = true
        then:
          - call: calculate_proration
          - update: User SET balance = balance - $proration_amount

      - update: User SET subscription_tier = 'premium', upgraded_at = now()
      - insert: SubscriptionEvent VALUES (
          user_id: $user_id,
          event_type: 'upgraded',
          old_tier: $current_tier,
          new_tier: 'premium'
        )

      - call: update_feature_access
      - notify: subscription_upgraded
```

## How Actions Work

### 1. Parse & Validate
SpecQL parses your YAML and validates:
- Step syntax correctness
- Entity and field references
- Business rule logic
- Type safety

### 2. Compile to PL/pgSQL
Each action becomes a PostgreSQL function:

```sql
CREATE FUNCTION crm.place_order(
  cart_id UUID,
  payment_method_id UUID
) RETURNS crm.mutation_result AS $$
DECLARE
  v_cart_total NUMERIC;
  v_user_balance NUMERIC;
  v_order_id UUID;
BEGIN
  -- Validation steps
  SELECT total INTO v_cart_total FROM crm.cart WHERE id = cart_id;
  IF v_cart_total <= 0 THEN
    RAISE EXCEPTION 'Cart is empty';
  END IF;

  -- Business logic
  INSERT INTO crm.order (user_id, total, status)
  SELECT user_id, total, 'placed' FROM crm.cart WHERE id = cart_id;

  -- More steps...
  RETURN ROW('Order placed successfully', v_order_id);
END;
$$ LANGUAGE plpgsql;
```

### 3. GraphQL Integration
Actions automatically become GraphQL mutations:

```graphql
type Mutation {
  placeOrder(cartId: UUID!, paymentMethodId: UUID!): MutationResult!
}

type MutationResult {
  success: Boolean!
  message: String
  data: JSON
}
```

### 4. Transaction Safety
All actions run in transactions:
- **Atomic**: All steps succeed or all fail
- **Isolated**: Concurrent actions don't interfere
- **Durable**: Changes persist reliably

## Best Practices

### Keep Actions Focused
```yaml
# ✅ Good: Single responsibility
actions:
  - name: create_user
  - name: send_welcome_email
  - name: activate_user

# ❌ Bad: Multiple responsibilities
actions:
  - name: create_user_and_send_email_and_activate
```

### Use Validation Early
```yaml
# ✅ Good: Fail fast
steps:
  - validate: user_exists = true
  - validate: permission_granted = true
  - update: User SET status = 'active'

# ❌ Bad: Do work then validate
steps:
  - update: User SET status = 'active'
  - validate: permission_granted = true  # Too late!
```

### Compose with Call Steps
```yaml
# ✅ Good: Reusable actions
actions:
  - name: validate_payment
    steps:
      - validate: payment_method_exists = true
      - validate: payment_method_active = true

  - name: process_payment
    steps:
      - call: validate_payment
      - update: Payment SET status = 'processing'
      - call: charge_credit_card
```

### Handle Errors Gracefully
```yaml
steps:
  - validate: inventory_available = true, error: "Item out of stock"
  - if: payment_failed = true
    then:
      - update: Order SET status = 'payment_failed'
      - call: notify_payment_failure
      - return: "Payment failed, please try again"
```

## Error Handling

Actions include comprehensive error handling:

### Validation Errors
```yaml
steps:
  - validate: age >= 18, error: "Must be 18 or older to register"
  - validate: email_unique = true, error: "Email already exists"
```

### Business Logic Errors
```yaml
steps:
  - if: insufficient_funds = true
    then:
      - return: "Insufficient funds", success: false
```

### System Errors
Automatic transaction rollback on any error.

## Performance Considerations

Actions are optimized for performance:

- **Single Transaction**: All steps in one database transaction
- **Compiled SQL**: Direct PL/pgSQL, no ORM overhead
- **Indexed Access**: Uses Trinity pattern for fast lookups
- **Batch Operations**: Efficient bulk updates

## Testing Actions

Actions are automatically testable:

```sql
-- Test the action directly
SELECT * FROM crm.place_order('cart-uuid', 'payment-uuid');

-- Check generated test fixtures
SELECT * FROM crm.order WHERE created_at > now() - interval '1 minute';
```

## Next Steps

- [Create your first action](../01_getting-started/first-action.md) - hands-on tutorial
- [See all step types](../06_reference/action-steps-reference.md) - complete reference
- [Advanced patterns](../07_advanced/custom-patterns.md) - complex workflows

---

**Actions transform business requirements into reliable, transactional database operations. Write what should happen, SpecQL handles how.**</content>
</xai:function_call
