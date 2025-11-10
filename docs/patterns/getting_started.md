# Getting Started with Action Patterns

Welcome to SpecQL Action Patterns! This guide will get you up and running with declarative business logic in under 30 minutes.

## 🎯 What You'll Learn

By the end of this guide, you'll be able to:
- Create entities with enhanced CRUD operations
- Implement state machine transitions
- Build multi-entity workflows
- Process batch operations
- Generate production-ready SQL from YAML

## 🛠️ Prerequisites

- Basic SpecQL knowledge (entities, fields, actions)
- Understanding of your business domain
- 30 minutes of focused time

## 🚀 Quick Start Tutorial

### Step 1: Create Your First Enhanced Entity

Let's start with a simple `Product` entity that uses enhanced CRUD features.

**Create** `entities/product.yaml`:

```yaml
entity: Product
schema: tenant
description: "Products in our catalog"

fields:
  code:
    type: text!
    description: "Unique product code"

  name:
    type: text!
    description: "Product name"

  price:
    type: decimal(10,2)!
    description: "Product price"

  status:
    type: enum(active, discontinued)
    default: active
    description: "Product status"

# Business constraint: no duplicate product codes
constraints:
  - name: unique_product_code
    type: unique
    fields: [code]
    check_on_create: true
    error_message: "Product code already exists"

# GraphQL projection with formatted data
projections:
  - name: product_projection
    materialize: true
    refresh_on: [create, update]
    includes: []  # Add related entities later

actions:
  # Enhanced CRUD operations
  - name: create_product
    duplicate_detection: true  # Check constraints before insert
    refresh_projection: product_projection

  - name: update_product
    partial_updates: true      # Only update provided fields
    track_updated_fields: true # Track what changed
    refresh_projection: product_projection

  - name: delete_product
```

**Generate and test:**

```bash
# Generate SQL functions
specql generate --entity product

# Check generated SQL
cat generated/product.sql

# Test the functions
specql test --entity product
```

### Step 2: Add State Machine Transitions

Now let's add product lifecycle management using the state machine pattern.

**Update** `entities/product.yaml`:

```yaml
actions:
  # ... existing CRUD actions ...

  # State machine: discontinue product
  - name: discontinue_product
    pattern: state_machine/transition
    config:
      from_states: [active]
      to_state: discontinued
      input_fields:
        - name: discontinued_reason
          type: text
          required: true
      validation_checks:
        - condition: "NOT EXISTS (SELECT 1 FROM order_items WHERE product_id = v_product_id AND status = 'pending')"
          error: "Cannot discontinue product with pending orders"
      refresh_projection: product_projection

  # State machine: reactivate product
  - name: reactivate_product
    pattern: state_machine/transition
    config:
      from_states: [discontinued]
      to_state: active
      side_effects:
        - entity: ProductEvent
          set:
            event_type: reactivated
            event_data: $input_payload
          where: "product_id = v_product_id"
      refresh_projection: product_projection
```

**What this generates:**
- Automatic state validation
- Input field handling
- Business rule enforcement
- Audit logging
- Projection updates

### Step 3: Create Multi-Entity Workflows

Let's add order creation that coordinates between Order and OrderItem entities.

**Create** `entities/order.yaml`:

```yaml
entity: Order
schema: tenant
description: "Customer orders"

fields:
  order_number:
    type: text!
    description: "Unique order number"

  customer_id:
    type: uuid!
    description: "Customer placing the order"

  status:
    type: enum(pending, confirmed, shipped, delivered, cancelled)
    default: pending

  total_amount:
    type: decimal(10,2)!
    description: "Order total"

# Auto-generated order numbers
identifier:
  pattern: "ORD-{created_at:YYYYMMDD}-{sequence:04d}"
  sequence:
    scope: [customer_id]  # Per-customer sequence
    group_by: [created_at:YYYYMMDD]  # Reset daily
  recalculate_on: [create]

projections:
  - name: order_projection
    materialize: true
    refresh_on: [create, update]
    includes:
      - customer: [id, name, email]
      - order_items: [id, product_id, quantity, unit_price]

actions:
  # Multi-entity: create order with items
  - name: create_order_with_items
    pattern: multi_entity/coordinated_update
    config:
      primary_entity: Order
      operations:
        # Create the order
        - action: insert
          entity: Order
          values:
            customer_id: $input_data.customer_id
            status: pending
            total_amount: $input_data.total_amount
          store_as: order_id

        # Create order items
        - action: insert
          entity: OrderItem
          values:
            order_id: $order_id
            product_id: $item.product_id
            quantity: $item.quantity
            unit_price: $item.unit_price
            total_price: $item.quantity * $item.unit_price
          # Note: This would be in a loop for multiple items

        # Update product inventory (if you had inventory)
        # - action: update
        #   entity: Product
        #   set: {stock_quantity: stock_quantity - $item.quantity}
        #   where: {id: $item.product_id}

      refresh_projections:
        - order_projection
        - product_projection
```

### Step 4: Add Batch Operations

Finally, let's add bulk price updates using the batch operation pattern.

**Update** `entities/product.yaml`:

```yaml
actions:
  # ... existing actions ...

  # Batch: bulk price updates
  - name: bulk_update_prices
    pattern: batch/bulk_operation
    config:
      batch_input: price_updates
      operation:
        action: update
        entity: Product
        set:
          price: $item.new_price
        where: "id = $item.id AND tenant_id = $auth_tenant_id"
      error_handling: continue_on_error
      batch_size: 50
      refresh_projections:
        - product_projection
      return_summary:
        updated_count: v_processed_count
        failed_count: v_failed_count
        failed_updates: v_failed_items
```

## 🧪 Testing Your Patterns

### 1. Generate SQL

```bash
# Generate all entities
specql generate

# Generate specific entity
specql generate --entity product

# Check generated functions
ls generated/
```

### 2. Run Tests

```bash
# Run all tests
specql test

# Run entity-specific tests
specql test --entity product

# Run integration tests
specql test --integration
```

### 3. Manual Testing

Test your generated functions directly:

```sql
-- Test duplicate detection
SELECT * FROM tenant.create_product(
    '550e8400-e29b-41d4-a716-446655440000'::UUID,  -- tenant_id
    '550e8400-e29b-41d4-a716-446655440001'::UUID,  -- user_id
    '{"code": "DUPE", "name": "Duplicate Product", "price": 29.99}'::JSONB
);

-- Should return NOOP with conflict details

-- Test state transition
SELECT * FROM tenant.discontinue_product(
    '550e8400-e29b-41d4-a716-446655440000'::UUID,
    '550e8400-e29b-41d4-a716-446655440001'::UUID,
    '{"id": "550e8400-e29b-41d4-a716-446655440002", "discontinued_reason": "End of life"}'::JSONB
);

-- Test batch operation
SELECT * FROM tenant.bulk_update_prices(
    '550e8400-e29b-41d4-a716-446655440000'::UUID,
    '550e8400-e29b-41d4-a716-446655440001'::UUID,
    '{"price_updates": [
        {"id": "550e8400-e29b-41d4-a716-446655440002", "new_price": 24.99},
        {"id": "550e8400-e29b-41d4-a716-446655440003", "new_price": 19.99}
    ]}'::JSONB
);
```

## 🎯 Common Patterns & Recipes

### User Registration with Profile

```yaml
actions:
  - name: register_user
    pattern: multi_entity/coordinated_update
    config:
      operations:
        - action: insert
          entity: User
          values:
            email: $input.email
            password_hash: $input.password_hash
          store_as: user_id

        - action: insert
          entity: UserProfile
          values:
            user_id: $user_id
            first_name: $input.first_name
            last_name: $input.last_name

        - action: insert
          entity: UserPreferences
          values:
            user_id: $user_id
            theme: 'light'
            notifications: true
```

### Order Status Workflow

```yaml
actions:
  - name: ship_order
    pattern: state_machine/transition
    config:
      from_states: [confirmed]
      to_state: shipped
      validation_checks:
        - condition: "EXISTS (SELECT 1 FROM order_items WHERE order_id = v_order_id)"
          error: "Cannot ship order without items"
      side_effects:
        - entity: OrderItem
          set: {shipped_at: NOW()}
          where: "order_id = v_order_id"

  - name: deliver_order
    pattern: state_machine/transition
    config:
      from_states: [shipped]
      to_state: delivered
      side_effects:
        - entity: Customer
          set: {last_order_date: NOW()}
          where: "id = (SELECT customer_id FROM orders WHERE id = v_order_id)"
```

### Bulk Status Updates

```yaml
actions:
  - name: bulk_activate_products
    pattern: batch/bulk_operation
    config:
      batch_input: product_ids
      operation:
        action: update
        entity: Product
        set: {status: 'active'}
        where: "id = $item AND status = 'discontinued'"
      return_summary:
        activated_count: v_processed_count
        already_active: v_failed_count
```

## 🚨 Troubleshooting

### "Pattern not found" Error
```yaml
# Check pattern name spelling
pattern: state_machine/transition  # ✅ Correct
pattern: state_machine_transition  # ❌ Wrong
```

### "Field not found" Error
```yaml
# Check field references in expressions
condition: "status = 'active'"  # ✅ Entity field
condition: "user_status = 'active'"  # ❌ Not an entity field
```

### "Template expansion failed" Error
```yaml
# Check YAML syntax and indentation
config:
  from_states: [active]  # ✅ Correct
  from_states: active   # ❌ Should be array
```

### SQL Generation Issues
```bash
# Regenerate after config changes
specql generate --clean
specql generate --entity your_entity
```

## 📚 Next Steps

### Advanced Topics
- [Custom Patterns](../patterns/custom_patterns.md) - Create your own patterns
- [Performance Tuning](performance.md) - Optimize generated SQL
- [Testing Strategies](testing.md) - Comprehensive testing approaches

### Real-World Examples
- [E-commerce](../../entities/examples/ecommerce/) - Complete online store
- [SaaS Multi-tenant](../../entities/examples/saas-multi-tenant/) - B2B application
- [PrintOptim Migration](../../migration/printoptim_to_specql.md) - Production migration

### Community & Support
- **Documentation**: Full API reference and guides
- **Examples**: 10+ complete working entities
- **Migration Support**: Step-by-step migration assistance

---

**Congratulations!** 🎉 You've successfully created your first SpecQL entities with action patterns. Your YAML now generates production-ready SQL with complex business logic, validation, and error handling.

**What's next?**
1. Explore the [full pattern library](../patterns/README.md)
2. Check out [complete examples](../../entities/examples/)
3. Start migrating your existing manual SQL using the [migration guide](../../migration/printoptim_to_specql.md)