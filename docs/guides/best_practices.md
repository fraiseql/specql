# SpecQL Best Practices

This guide provides recommendations for writing maintainable, efficient, and scalable SpecQL entities. Following these practices will help you build robust business logic that performs well and is easy to maintain.

## Entity Design

### 1. Start with the Business Domain

**✅ Good: Business-focused entity names**
```yaml
entity: CustomerOrder
namespace: sales
description: "Customer purchase orders with approval workflow"
```

**❌ Bad: Technical-focused names**
```yaml
entity: OrderTable
namespace: db
description: "Table for storing orders"
```

### 2. Use Consistent Naming Conventions

**Entity Names**: PascalCase, business domain focused
- `CustomerOrder`, `ProductCatalog`, `InvoicePayment`

**Field Names**: snake_case, descriptive
- `customer_id`, `order_total`, `created_at`

**Action Names**: snake_case, verb-focused
- `create_order`, `update_customer`, `process_payment`

### 3. Design for Change

**Plan for evolution**:
```yaml
entity: Product
fields:
  # Core fields
  name: text
  price: numeric

  # Extension points for future features
  metadata: jsonb  # Flexible extension
  tags: text[]     # Categorization support

  # Audit fields (added via patterns)
  # created_at, updated_at, etc.
```

## Field Design

### 1. Choose Appropriate Data Types

**Text Fields**:
```yaml
fields:
  email:
    type: text
    required: true
    unique: true
    description: "Customer email address"

  description:
    type: text
    description: "Optional product description"
```

**Numeric Fields**:
```yaml
fields:
  price:
    type: numeric(10,2)  # Precision and scale
    required: true
    min: 0
    description: "Product price in USD"

  quantity:
    type: integer
    required: true
    min: 0
    max: 999999
    description: "Available quantity"
```

**Date/Time Fields**:
```yaml
fields:
  created_at:
    type: timestamptz
    default: NOW()
    description: "Record creation timestamp"

  expires_at:
    type: date
    description: "Expiration date"
```

### 2. Use Constraints Wisely

**Validation constraints**:
```yaml
fields:
  email:
    type: text
    required: true
    pattern: "^[\\w.-]+@[\\w.-]+\\.\\w+$"
    description: "Valid email address"

  priority:
    type: enum
    values: [low, medium, high, urgent]
    default: medium
    description: "Task priority level"
```

### 3. Design for NULL vs Empty

**Be explicit about optionality**:
```yaml
fields:
  # Required fields
  name: text  # NOT NULL

  # Optional fields with clear semantics
  middle_name:
    type: text
    description: "Optional middle name"

  # Use appropriate defaults
  status:
    type: text
    default: "active"
    description: "Account status"
```

## Action Design

### 1. Use Descriptive Action Names

**✅ Clear, specific names**:
```yaml
actions:
  - name: place_customer_order
    description: "Create new customer order with validation"

  - name: apply_discount_code
    description: "Apply promotional discount to order"

  - name: ship_order
    description: "Mark order as shipped and update tracking"
```

**❌ Generic or unclear names**:
```yaml
actions:
  - name: process  # Too generic
  - name: do_stuff  # Unhelpful
  - name: update   # Not specific enough
```

### 2. Structure Actions Logically

**Input validation first**:
```yaml
actions:
  - name: create_user
    parameters:
      email: text
      password: text
      role: text
    steps:
      # 1. Validate inputs
      - type: validate
        condition: "email IS NOT NULL AND email != ''"
        error_message: "Email is required"

      - type: validate
        condition: "password IS NOT NULL AND length(password) >= 8"
        error_message: "Password must be at least 8 characters"

      # 2. Check business rules
      - type: duplicate_check
        table: users
        fields: [email]
        error_message: "User with this email already exists"

      # 3. Create record
      - type: insert
        table: users
        data:
          email: "{{ email }}"
          password_hash: "crypt({{ password }}, gen_salt('bf'))"
          role: "{{ role }}"
          created_at: "NOW()"
```

### 3. Handle Errors Appropriately

**Provide helpful error messages**:
```yaml
steps:
  - type: validate
    condition: "balance >= order_total"
    error_message: "Insufficient account balance ($ {{ balance }}) for order total ($ {{ order_total }})"

  - type: validate
    condition: "EXISTS (SELECT 1 FROM products WHERE id = product_id AND active = true)"
    error_message: "Product {{ product_id }} is not available"
```

### 4. Use Transactions Wisely

**Group related operations**:
```yaml
actions:
  - name: transfer_funds
    parameters:
      from_account: uuid
      to_account: uuid
      amount: numeric
    steps:
      # All steps in one transaction
      - type: update
        table: accounts
        data: { balance: "balance - {{ amount }}" }
        where: "id = {{ from_account }}"

      - type: update
        table: accounts
        data: { balance: "balance + {{ amount }}" }
        where: "id = {{ to_account }}"

      - type: insert
        table: transfers
        data:
          from_account_id: "{{ from_account }}"
          to_account_id: "{{ to_account }}"
          amount: "{{ amount }}"
          transferred_at: "NOW()"
```

## Pattern Usage

### 1. Choose Patterns Strategically

**Start with core patterns**:
```yaml
patterns:
  - audit_trail        # Always track changes
  - state_machine      # If entity has lifecycle
  - soft_delete        # If data should be recoverable
  - validation_chain   # For complex business rules
```

**Avoid pattern overload**:
```yaml
# ❌ Too many patterns can complicate the entity
patterns:
  - audit_trail
  - state_machine
  - soft_delete
  - validation_chain
  - notification
  - search_optimization
  - internationalization
  - file_attachment
  # ... 8 more patterns

# ✅ Focus on essential patterns
patterns:
  - audit_trail
  - state_machine:
      states: [draft, active, archived]
```

### 2. Configure Patterns Properly

**Provide meaningful configuration**:
```yaml
patterns:
  - state_machine:
      states: [pending, approved, rejected, completed]
      initial_state: pending
      transitions:
        submit: { from: pending, to: approved }
        reject: { from: pending, to: rejected }

  - approval_workflow:
      levels:
        - name: manager
          condition: "amount <= 1000"
        - name: director
          condition: "amount <= 10000"
```

### 3. Combine Patterns Effectively

**Patterns that work well together**:
```yaml
patterns:
  - state_machine        # Manages status
  - audit_trail         # Tracks all changes
  - soft_delete         # Allows recovery
  - notification        # Alerts on state changes
```

## Performance Optimization

### 1. Index Critical Fields

**Add indexes for frequently queried fields**:
```yaml
entity: Order
fields:
  customer_id:
    type: uuid
    indexed: true  # Foreign key lookups

  status:
    type: enum
    values: [pending, processing, shipped, delivered]
    indexed: true  # Status filtering

  created_at:
    type: timestamptz
    indexed: true  # Date range queries
```

### 2. Use Appropriate Query Patterns

**Prefer indexed lookups**:
```yaml
steps:
  # ✅ Uses index on customer_id
  - type: select
    query: "SELECT * FROM orders WHERE customer_id = {{ customer_id }} ORDER BY created_at DESC"
    result_variable: customer_orders

  # ❌ Table scan (avoid when possible)
  - type: select
    query: "SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '30 days'"
    result_variable: recent_orders
```

### 3. Batch Operations When Possible

**Combine multiple operations**:
```yaml
actions:
  - name: bulk_update_status
    parameters:
      order_ids: uuid[]
      new_status: text
    steps:
      - type: update
        table: orders
        data: { status: "{{ new_status }}", updated_at: "NOW()" }
        where: "id = ANY({{ order_ids }})"
```

### 4. Cache Expensive Operations

**Use generated computed fields**:
```yaml
patterns:
  - computed_fields:
      fields:
        - name: total_value
          expression: "SELECT SUM(amount) FROM order_items WHERE order_id = id"
          update_triggers: ["order_items.amount"]
```

## Security Considerations

### 1. Validate All Inputs

**Never trust user input**:
```yaml
actions:
  - name: update_profile
    parameters:
      user_id: uuid
      email: text
      bio: text
    steps:
      # Validate ownership
      - type: validate
        condition: "EXISTS (SELECT 1 FROM users WHERE id = {{ user_id }} AND owner_id = {{ current_user_id }})"
        error_message: "Access denied"

      # Validate data
      - type: validate
        condition: "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z]{2,}$'"
        error_message: "Invalid email format"

      - type: validate
        condition: "length(bio) <= 500"
        error_message: "Bio must be 500 characters or less"
```

### 2. Use Parameterized Queries

**SpecQL automatically uses parameterized queries** - this is handled for you when using the proper primitives.

### 3. Implement Proper Authorization

**Check permissions at the action level**:
```yaml
actions:
  - name: approve_expense
    parameters:
      expense_id: uuid
    steps:
      # Check if user can approve this expense
      - type: validate
        condition: "user_can_approve_expense({{ current_user_id }}, {{ expense_id }})"
        error_message: "Insufficient permissions to approve this expense"
```

## Testing Strategies

### 1. Test Business Logic Thoroughly

**Cover all scenarios**:
```python
def test_create_order_success():
    """Test successful order creation."""
    order_data = {
        "customer_id": customer.id,
        "items": [{"product_id": product.id, "quantity": 2}]
    }

    result = create_order(order_data)

    assert result["success"] == True
    assert result["order_id"] is not None
    # Verify order was created
    # Verify inventory was updated
    # Verify notifications were sent

def test_create_order_insufficient_inventory():
    """Test order creation with insufficient inventory."""
    order_data = {
        "customer_id": customer.id,
        "items": [{"product_id": product.id, "quantity": 1000}]  # More than available
    }

    result = create_order(order_data)

    assert result["success"] == False
    assert "insufficient inventory" in result["error"].lower()
```

### 2. Test Edge Cases

**Don't forget edge cases**:
```python
def test_create_order_edge_cases():
    """Test order creation edge cases."""

    # Empty order
    result = create_order({"customer_id": customer.id, "items": []})
    assert "at least one item" in result["error"].lower()

    # Invalid customer
    result = create_order({"customer_id": uuid4(), "items": valid_items})
    assert "customer not found" in result["error"].lower()

    # Very large order
    large_items = [{"product_id": product.id, "quantity": 1000000}]
    result = create_order({"customer_id": customer.id, "items": large_items})
    assert result["success"] == False  # Should fail validation
```

### 3. Test Performance

**Ensure operations are fast enough**:
```python
def test_order_creation_performance():
    """Test that order creation is fast enough."""
    order_data = create_large_order_data()

    start_time = time.time()
    result = create_order(order_data)
    duration = time.time() - start_time

    assert result["success"] == True
    assert duration < 0.5  # Should complete in under 500ms
```

## Documentation

### 1. Document Business Rules

**Explain why, not just what**:
```yaml
actions:
  - name: approve_loan
    description: |
      Approve loan application if credit score >= 700 and debt-to-income ratio <= 0.36.
      This ensures responsible lending practices and regulatory compliance.
    parameters:
      application_id: uuid
```

### 2. Add Field Descriptions

**Help future maintainers**:
```yaml
fields:
  credit_score:
    type: integer
    min: 300
    max: 850
    description: "FICO credit score from 300-850. Higher scores indicate better creditworthiness."

  debt_to_income_ratio:
    type: numeric(5,4)
    description: "Ratio of monthly debt payments to gross monthly income. Max 36% for loan approval."
```

### 3. Comment Complex Logic

**Explain non-obvious business rules**:
```yaml
steps:
  # Calculate risk score: 30% credit score, 40% debt ratio, 30% payment history
  - type: assign
    variable_name: risk_score
    expression: |
      (credit_score - 300) / 5.5 * 0.3 +  -- Credit score component (0-30 points)
      (1 - debt_to_income_ratio) * 100 * 0.4 +  -- Debt ratio component (0-40 points)
      on_time_payment_percentage * 0.3  -- Payment history component (0-30 points)
```

## Version Control

### 1. Commit Atomic Changes

**Each commit should be a logical unit**:
```bash
git commit -m "feat: add order approval workflow

- Add approval_required field to orders
- Add approve_order and reject_order actions
- Add approval permission checks
- Add approval audit trail

Business rules:
- Orders > $1000 require manager approval
- Orders > $10000 require director approval
- Approvals are tracked in audit log"
```

### 2. Use Descriptive Commit Messages

**Follow conventional commit format**:
```
feat: add user authentication system
fix: correct tax calculation formula
docs: update API reference
refactor: simplify order processing logic
test: add integration tests for payment processing
```

### 3. Version Your Entities

**Track breaking changes**:
```yaml
entity: Order
version: "2.1.0"
description: "Customer orders with approval workflow (v2.1 adds bulk operations)"

# Breaking changes in v2.0:
# - order_status field renamed to status
# - approval_required is now automatically calculated
```

## Migration Planning

### 1. Plan for Data Migration

**Consider data migration needs**:
```yaml
# When adding required field
entity: User
fields:
  phone:
    type: text
    required: true  # New required field
    migration:
      default_value: ""  # For existing records
      backfill_query: "UPDATE users SET phone = '' WHERE phone IS NULL"
```

### 2. Test Migrations Thoroughly

**Test migration scripts**:
```sql
-- Migration script for new required field
BEGIN;

-- Add column as nullable first
ALTER TABLE users ADD COLUMN phone TEXT;

-- Backfill existing records
UPDATE users SET phone = '' WHERE phone IS NULL;

-- Add constraint
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

COMMIT;
```

### 3. Plan Rollback Strategy

**Always have a rollback plan**:
```sql
-- Rollback script
BEGIN;

-- Remove constraint
ALTER TABLE users ALTER COLUMN phone DROP NOT NULL;

-- Optionally remove data
-- UPDATE users SET phone = NULL WHERE phone = '';

COMMIT;
```

## Monitoring and Maintenance

### 1. Add Health Checks

**Monitor entity health**:
```yaml
actions:
  - name: health_check
    description: "Verify entity integrity and performance"
    steps:
      - type: select
        query: "SELECT count(*) as total_orders FROM orders"
        result_variable: stats

      - type: validate
        condition: "stats.total_orders >= 0"
        error_message: "Order table health check failed"
```

### 2. Log Important Events

**Track business events**:
```yaml
steps:
  # Log significant business events
  - type: insert
    table: audit_log
    data:
      event_type: "order_approved"
      entity_type: "order"
      entity_id: "{{ order_id }}"
      user_id: "{{ current_user_id }}"
      details: jsonb_build_object(
        'order_total', order_total,
        'approved_by', current_user_id,
        'approval_timestamp', NOW()
      )
```

### 3. Plan for Scaling

**Design for growth**:
```yaml
entity: AnalyticsEvent
fields:
  event_type: text
  event_data: jsonb
  user_id: uuid
  session_id: uuid
  timestamp: timestamptz

# Partition by month for performance
partitioning:
  strategy: range
  key: timestamp
  interval: month

# Archive old data
archiving:
  older_than: 1 year
  strategy: compress
  table: analytics_events_archive
```

## Common Anti-Patterns

### 1. God Entities

**❌ One entity trying to do everything**:
```yaml
entity: UniversalEntity  # Too broad
fields:
  data: jsonb  # Everything stored here
  type: text   # Discriminator field
```

**✅ Focused, single-responsibility entities**:
```yaml
entity: Customer
entity: Order
entity: Product
entity: Invoice
```

### 2. Over-Engineering

**❌ Adding complexity that isn't needed**:
```yaml
patterns:
  - state_machine
  - audit_trail
  - soft_delete
  - validation_chain
  - notification
  - search_optimization
  - internationalization
  # ... 10 more patterns for a simple entity
```

**✅ Start simple, add complexity as needed**:
```yaml
patterns:
  - audit_trail  # Essential
  # Add others when the business need arises
```

### 3. Ignoring Performance

**❌ Expensive operations in hot paths**:
```yaml
steps:
  - type: select
    query: "SELECT * FROM orders WHERE customer_id IN (SELECT customer_id FROM customers WHERE region = 'US')"
    result_variable: us_orders
```

**✅ Optimized queries**:
```yaml
steps:
  - type: select
    query: "SELECT o.* FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.region = 'US'"
    result_variable: us_orders
```

### 4. Weak Validation

**❌ Insufficient validation**:
```yaml
actions:
  - name: create_user
    parameters:
      email: text
    steps:
      - type: insert
        table: users
        data: { email: "{{ email }}" }
```

**✅ Comprehensive validation**:
```yaml
actions:
  - name: create_user
    parameters:
      email: text
      password: text
    steps:
      - type: validate
        condition: "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z]{2,}$'"
        error_message: "Invalid email format"

      - type: validate
        condition: "length(password) >= 8"
        error_message: "Password too short"

      - type: duplicate_check
        table: users
        fields: [email]
        error_message: "Email already registered"

      - type: insert
        table: users
        data:
          email: "{{ email }}"
          password_hash: "crypt({{ password }}, gen_salt('bf'))"
```

## Summary

Following these best practices will help you:

- **Build maintainable entities** that are easy to understand and modify
- **Create performant systems** that scale with your business
- **Ensure reliability** through proper validation and error handling
- **Enable evolution** by designing for change
- **Facilitate collaboration** through clear documentation and consistent patterns

Remember: SpecQL is about capturing business logic clearly and generating high-quality code. Focus on expressing your business rules accurately, and let SpecQL handle the implementation details. 🚀