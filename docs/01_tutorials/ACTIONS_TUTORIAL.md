# Actions Tutorial

**Business logic in YAML** - Writing database functions with SpecQL actions

This tutorial covers writing complex business logic using SpecQL actions. Actions compile to PostgreSQL functions with validation, error handling, and transactions.

## 🎯 What You'll Learn

- Action syntax and structure
- Validation rules and error handling
- Complex business workflows
- Transaction management
- Parameter handling

## 📋 Prerequisites

- [ ] Completed [First Entity Tutorial](FIRST_ENTITY_TUTORIAL.md)
- [ ] Understanding of basic entity definition
- [ ] PostgreSQL function basics

## 🏗️ Step 1: Action Structure

Actions are business logic functions defined in YAML:

```yaml
actions:
  - name: action_name
    description: "What this action does"
    requires: caller.permission_name    # Optional permission check
    parameters:                         # Optional input parameters
      - name: param_name
        type: param_type
        required: true/false
    steps:                              # Execution steps
      - validate: condition
        error: "error_code"
      - update: Entity SET field = value
      - insert: Entity SET field = value
      - notify: notification_type
      - return: expression
```

## 📝 Step 2: Basic Actions

### Create Action with Validation

```yaml
entity: Product
schema: inventory

fields:
  name: text
  sku: text
  price: decimal(10,2)
  stock_quantity: integer
  category: enum(electronics, clothing, books, home)
  is_active: boolean

actions:
  - name: create_product
    description: "Create a new product with validation"
    parameters:
      - name: product_name
        type: text
        required: true
      - name: product_sku
        type: text
        required: true
      - name: product_price
        type: decimal
        required: true
    steps:
      # Validate input data
      - validate: LENGTH(product_name) >= 3 AND LENGTH(product_name) <= 100
        error: "invalid_product_name"
      - validate: product_price > 0 AND product_price < 10000
        error: "invalid_price"
      - validate: product_sku IS UNIQUE  # Check uniqueness
        error: "sku_already_exists"

      # Create the product
      - insert: Product SET
          name = :product_name,
          sku = :product_sku,
          price = :product_price,
          stock_quantity = 0,
          is_active = true
```

### Update Action with Business Rules

```yaml
actions:
  - name: update_price
    description: "Update product price with business rules"
    requires: caller.can_manage_products
    parameters:
      - name: new_price
        type: decimal
        required: true
      - name: reason
        type: text
        required: true
    steps:
      # Business validation
      - validate: new_price > 0 AND new_price < 10000
        error: "invalid_price_range"
      - validate: new_price != price  # No pointless updates
        error: "price_unchanged"
      - validate: LENGTH(reason) >= 10  # Require reason
        error: "reason_required"

      # Price change limits (business rule)
      - validate: new_price < price * 1.5  # Max 50% increase
        error: "price_increase_too_large"
      - validate: new_price > price * 0.5  # Max 50% decrease
        error: "price_decrease_too_large"

      # Update with audit trail
      - update: Product SET
          price = :new_price,
          updated_at = NOW()
      - notify: price_changed
```

## 🔄 Step 3: Complex Workflows

### Order Processing Workflow

```yaml
entity: Order
schema: sales

fields:
  status: enum(pending, confirmed, processing, shipped, delivered, cancelled)
  total_amount: decimal(12,2)
  customer_id: integer
  shipping_address: text
  tracking_number: text

actions:
  - name: place_order
    description: "Place a new order"
    steps:
      - validate: total_amount > 0
        error: "invalid_order_total"
      - validate: shipping_address IS NOT NULL
        error: "shipping_address_required"
      - update: Order SET status = 'confirmed'
      - notify: order_placed

  - name: process_order
    description: "Start processing an order"
    requires: caller.can_process_orders
    steps:
      - validate: status = 'confirmed'
        error: "order_not_confirmed"
      # Check inventory availability (simplified)
      - validate: true  # Would check product stock here
        error: "insufficient_inventory"
      - update: Order SET status = 'processing'
      - notify: order_processing_started

  - name: ship_order
    description: "Mark order as shipped"
    requires: caller.can_ship_orders
    parameters:
      - name: tracking
        type: text
        required: true
    steps:
      - validate: status = 'processing'
        error: "order_not_processing"
      - validate: LENGTH(tracking) >= 5
        error: "invalid_tracking_number"
      - update: Order SET
          status = 'shipped',
          tracking_number = :tracking
      - notify: order_shipped

  - name: complete_order
    description: "Mark order as delivered"
    requires: caller.can_complete_orders
    steps:
      - validate: status = 'shipped'
        error: "order_not_shipped"
      - validate: tracking_number IS NOT NULL
        error: "missing_tracking_number"
      - update: Order SET status = 'delivered'
      - notify: order_delivered
```

### User Management Actions

```yaml
entity: User
schema: auth

fields:
  email: text
  status: enum(active, suspended, deactivated)
  role: enum(user, moderator, admin)
  login_attempts: integer
  locked_until: timestamp

actions:
  - name: login_attempt
    description: "Record a login attempt with lockout protection"
    parameters:
      - name: attempt_successful
        type: boolean
        required: true
    steps:
      - validate: status IN ('active', 'suspended')
        error: "account_inactive"

      # Check if account is currently locked
      - validate: locked_until IS NULL OR locked_until < NOW()
        error: "account_locked"

      # Update login attempts
      - update: User SET
          login_attempts = CASE
            WHEN :attempt_successful THEN 0
            ELSE login_attempts + 1
          END,
          locked_until = CASE
            WHEN login_attempts >= 5 THEN NOW() + INTERVAL '30 minutes'
            ELSE locked_until
          END

      # Return login result
      - return: CASE
          WHEN :attempt_successful THEN 'success'
          WHEN login_attempts >= 5 THEN 'locked'
          ELSE 'failed'
        END

  - name: unlock_account
    description: "Manually unlock a locked account"
    requires: caller.is_admin
    steps:
      - validate: locked_until IS NOT NULL
        error: "account_not_locked"
      - update: User SET
          login_attempts = 0,
          locked_until = NULL
      - notify: account_unlocked
```

## 🎯 Step 4: Advanced Action Patterns

### Conditional Logic

```yaml
actions:
  - name: apply_discount
    description: "Apply discount based on order history"
    parameters:
      - name: discount_type
        type: enum(percentage, fixed)
        required: true
      - name: discount_value
        type: decimal
        required: true
    steps:
      # Validate discount parameters
      - validate: discount_value > 0
        error: "invalid_discount_value"

      # Percentage discount validation
      - validate: :discount_type != 'percentage' OR discount_value <= 50
        error: "percentage_discount_too_high"

      # Fixed amount discount validation
      - validate: :discount_type != 'fixed' OR discount_value <= total_amount
        error: "fixed_discount_too_high"

      # Apply discount based on type
      - update: Order SET
          discount_amount = CASE
            WHEN :discount_type = 'percentage'
              THEN total_amount * :discount_value / 100
            WHEN :discount_type = 'fixed'
              THEN :discount_value
          END,
          total_amount = total_amount - CASE
            WHEN :discount_type = 'percentage'
              THEN total_amount * :discount_value / 100
            WHEN :discount_type = 'fixed'
              THEN :discount_value
          END
```

### Bulk Operations

```yaml
actions:
  - name: bulk_update_status
    description: "Update status for multiple products"
    requires: caller.is_admin
    parameters:
      - name: product_ids
        type: json  # Array of UUIDs
        required: true
      - name: new_status
        type: text
        required: true
    steps:
      # Validate status
      - validate: :new_status IN ('active', 'inactive', 'discontinued')
        error: "invalid_status"

      # Update all specified products
      - update: Product SET
          status = :new_status,
          updated_at = NOW()
        WHERE id = ANY(:product_ids)

      # Return count of updated products
      - return: COUNT(*) FROM Product WHERE id = ANY(:product_ids)
```

### Audit Trail Actions

```yaml
entity: AuditLog
schema: audit

fields:
  entity_type: text
  entity_id: uuid
  action: text
  old_values: json
  new_values: json
  performed_by: uuid
  performed_at: timestamp

actions:
  - name: log_change
    description: "Log an entity change"
    parameters:
      - name: entity_type
        type: text
        required: true
      - name: entity_id
        type: uuid
        required: true
      - name: action_type
        type: text
        required: true
      - name: old_data
        type: json
      - name: new_data
        type: json
    steps:
      - insert: AuditLog SET
          entity_type = :entity_type,
          entity_id = :entity_id,
          action = :action_type,
          old_values = :old_data,
          new_values = :new_data,
          performed_by = caller.id,
          performed_at = NOW()
```

## 🧪 Step 5: Testing Actions

Create comprehensive tests for your actions:

```bash
# Generate the schema
specql generate entities/product.yaml entities/order.yaml --output test_actions

# Create test database
createdb action_test

# Apply schema
psql action_test < test_actions/inventory/01_tables.sql
psql action_test < test_actions/inventory/02_functions.sql
psql action_test < test_actions/sales/01_tables.sql
psql action_test < test_actions/sales/02_functions.sql

# Test the actions
psql action_test << 'EOF'
-- Create test product
SELECT * FROM inventory.fn_product_create_product(
    'Test Product',
    'TEST-001',
    29.99
);

-- Test price update
SELECT * FROM inventory.fn_product_update_price(
    (SELECT id FROM inventory.tb_product WHERE sku = 'TEST-001'),
    34.99,
    'Competitive pricing adjustment'
);

-- Check results
SELECT id, name, sku, price FROM inventory.tb_product;
EOF
```

## 🔍 Step 6: Error Handling

Actions provide structured error handling:

```yaml
actions:
  - name: complex_business_operation
    description: "Complex operation with comprehensive error handling"
    steps:
      # Pre-conditions
      - validate: status = 'ready'
        error: "not_ready"
      - validate: amount > 0
        error: "invalid_amount"

      # Business logic with error recovery
      - update: Entity SET status = 'processing'

      # Complex validation
      - validate: complex_business_rule(amount, related_data)
        error: "business_rule_violation"

      # Success path
      - update: Entity SET status = 'completed'
      - notify: operation_completed
      - return: 'success'
```

**Generated error handling:**
```sql
CREATE OR REPLACE FUNCTION app.complex_business_operation(
    p_entity_id UUID
)
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_entity_pk INTEGER;
    v_status TEXT;
    v_amount DECIMAL;
BEGIN
    -- Trinity resolution
    SELECT pk_entity, status, amount INTO v_entity_pk, v_status, v_amount
    FROM app.tb_entity
    WHERE id = p_entity_id;

    -- Pre-condition checks
    IF v_status != 'ready' THEN
        RETURN app.error('not_ready', 'Entity is not ready for operation');
    END IF;

    IF v_amount <= 0 THEN
        RETURN app.error('invalid_amount', 'Amount must be positive');
    END IF;

    -- Business logic
    UPDATE app.tb_entity SET status = 'processing' WHERE pk_entity = v_entity_pk;

    -- Complex validation (would call another function)
    IF NOT app.complex_business_rule(v_amount, v_related_data) THEN
        -- Rollback status
        UPDATE app.tb_entity SET status = 'ready' WHERE pk_entity = v_entity_pk;
        RETURN app.error('business_rule_violation', 'Business rule violated');
    END IF;

    -- Success
    UPDATE app.tb_entity SET status = 'completed' WHERE pk_entity = v_entity_pk;

    RETURN app.success('Operation completed successfully');

EXCEPTION
    WHEN OTHERS THEN
        -- Rollback on any error
        UPDATE app.tb_entity SET status = 'error' WHERE pk_entity = v_entity_pk;
        RETURN app.error('unexpected_error', SQLERRM);
END;
$$;
```

## 🎯 Step 7: Best Practices

### Action Design Principles

1. **Single Responsibility** - One action, one business operation
2. **Comprehensive Validation** - Validate early, fail fast
3. **Atomic Operations** - All-or-nothing with transactions
4. **Clear Error Messages** - User-friendly error codes
5. **Audit Trail** - Log important business operations

### Performance Considerations

1. **Minimize Database Round Trips** - Batch operations where possible
2. **Use Appropriate Indexes** - Ensure foreign key and filter columns are indexed
3. **Avoid Complex Calculations** - Move to application code if too slow
4. **Consider Read/Write Patterns** - Separate read-heavy from write-heavy operations

### Security Best Practices

1. **Permission Checks** - Use `requires` for authorization
2. **Input Validation** - Never trust input parameters
3. **SQL Injection Prevention** - Use parameterized queries (automatic)
4. **Audit Sensitive Operations** - Log security-related changes

## 🔄 Next Steps

You've mastered SpecQL actions!

- **[Relationships Tutorial](RELATIONSHIPS_TUTORIAL.md)** - Connect entities with foreign keys
- **[Multi-Language Tutorial](MULTI_LANGUAGE_TUTORIAL.md)** - Generate code in multiple languages
- **[Reverse Engineering Tutorial](REVERSE_ENGINEERING_TUTORIAL.md)** - Import existing databases

## 🆘 Common Issues

**Action not found after generation?**
- Check schema name in search_path
- Verify function was created: `\\df schema_name.*`

**Validation not working?**
- Use correct operators: `=`, `!=`, `<`, `>`, `<=`, `>=`
- String functions: `LENGTH()`, `UPPER()`, `LOWER()`
- NULL checks: `IS NULL`, `IS NOT NULL`

**Transaction not rolling back?**
- Actions are automatically transactional
- Use `EXCEPTION` blocks for custom rollback logic

---

**Excellent!** You can now write complex business logic with confidence using SpecQL actions.