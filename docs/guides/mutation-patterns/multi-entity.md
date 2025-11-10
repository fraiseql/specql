# Multi-Entity Pattern

The **multi-entity** pattern handles complex operations that span multiple tables. It's perfect for transactions involving related entities like orders with line items, invoices with payments, or any business operation requiring consistency across tables.

## 🎯 What You'll Learn

- Multi-entity operation concepts
- Configuring cross-table transactions
- Handling related entity updates
- Ensuring transactional consistency
- Testing multi-entity operations

## 📋 Prerequisites

- [Pattern basics](getting-started.md)
- Understanding of database relationships
- Knowledge of transactions

## 💡 Multi-Entity Concepts

### What Are Multi-Entity Operations?

**Multi-entity operations** manage transactions across multiple related tables:

```yaml
# Single operation affects multiple entities
patterns:
  - name: multi_entity
    description: "Create order with line items"
    operation: create_order_with_items
    entities: [order, order_item]
    transaction: required  # All or nothing
```

**Benefits:**
- **Consistency** - All changes succeed or all fail
- **Atomicity** - Single transaction across tables
- **Simplicity** - One function call for complex operations
- **Safety** - No partial updates or orphaned records

### When to Use Multi-Entity

| Use Case | Example | Why Multi-Entity |
|----------|---------|------------------|
| **Order Processing** | Order + Line Items | Maintain inventory consistency |
| **Invoice Creation** | Invoice + Line Items + Tax | Calculate totals accurately |
| **User Registration** | User + Profile + Preferences | Complete user setup |
| **Payment Processing** | Payment + Transaction Log | Audit trail integrity |

## 🏗️ Basic Multi-Entity Operation

### Order with Line Items

```yaml
# entities/order.yaml
name: order
fields:
  id: uuid
  customer_id: uuid
  status: string
  total_amount: decimal
  created_at: timestamp

# entities/order_item.yaml
name: order_item
fields:
  id: uuid
  order_id: uuid
  product_id: uuid
  quantity: integer
  unit_price: decimal
  total_price: decimal

# In order.yaml, add multi-entity pattern
patterns:
  - name: multi_entity
    description: "Create complete order with items"
    operation: create_order_with_items
    entities: [order, order_item]
    steps:
      - create: order
        data:
          customer_id: :customer_id
          status: pending
          total_amount: 0  # Will be calculated
      - create: order_item
        for_each: :items
        data:
          order_id: :order.id
          product_id: :item.product_id
          quantity: :item.quantity
          unit_price: :item.unit_price
          total_price: ":item.quantity * :item.unit_price"
      - update: order
        data:
          total_amount: "SUM(order_item.total_price)"
        where: "id = :order.id"
```

### Generated Function

```sql
-- Generated multi-entity function
CREATE FUNCTION create_order_with_items(
  customer_id UUID,
  items JSONB  -- Array of {product_id, quantity, unit_price}
) RETURNS order_result AS $$
DECLARE
  new_order order;
  item_data JSONB;
  calculated_total DECIMAL := 0;
BEGIN
  -- Create order
  INSERT INTO order (customer_id, status, total_amount)
  VALUES (customer_id, 'pending', 0)
  RETURNING * INTO new_order;

  -- Create order items
  FOR item_data IN SELECT * FROM jsonb_array_elements(items)
  LOOP
    INSERT INTO order_item (
      order_id,
      product_id,
      quantity,
      unit_price,
      total_price
    ) VALUES (
      new_order.id,
      (item_data->>'product_id')::UUID,
      (item_data->>'quantity')::INTEGER,
      (item_data->>'unit_price')::DECIMAL,
      (item_data->>'quantity')::INTEGER * (item_data->>'unit_price')::DECIMAL
    );

    calculated_total := calculated_total +
      (item_data->>'quantity')::INTEGER * (item_data->>'unit_price')::DECIMAL;
  END LOOP;

  -- Update order total
  UPDATE order
  SET total_amount = calculated_total
  WHERE id = new_order.id;

  RETURN new_order;
END;
$$ LANGUAGE plpgsql;
```

## ⚙️ Advanced Configuration

### Complex Multi-Entity Operations

```yaml
patterns:
  - name: multi_entity
    description: "Process payment and update accounts"
    operation: process_payment
    entities: [payment, account, transaction_log]
    transaction: required
    isolation_level: serializable  # Highest consistency

    steps:
      # Validate payment
      - validate: account
        where: "id = :account_id"
        condition: "balance >= :amount AND status = 'active'"

      # Create payment record
      - create: payment
        data:
          account_id: :account_id
          amount: :amount
          type: :payment_type
          status: pending

      # Update account balance
      - update: account
        data:
          balance: "balance - :amount"
          last_payment_at: "NOW()"
        where: "id = :account_id"

      # Log transaction
      - create: transaction_log
        data:
          payment_id: :payment.id
          account_id: :account_id
          amount: :amount
          balance_before: :account.balance_before
          balance_after: ":account.balance_before - :amount"
          transaction_type: debit

      # Mark payment complete
      - update: payment
        data:
          status: completed
          completed_at: "NOW()"
        where: "id = :payment.id"

      # Send notification
      - notify: payment_processed
        data:
          payment_id: :payment.id
          amount: :amount
```

### Conditional Operations

```yaml
patterns:
  - name: multi_entity
    description: "Flexible order processing"
    operation: process_order
    entities: [order, order_item, inventory, shipment]

    steps:
      # Create order
      - create: order
        data:
          customer_id: :customer_id
          status: pending

      # Process items with inventory checks
      - create: order_item
        for_each: :items
        condition: "inventory_available(:item.product_id, :item.quantity)"
        data:
          order_id: :order.id
          product_id: :item.product_id
          quantity: :item.quantity

      # Update inventory
      - update: inventory
        for_each: :items
        data:
          quantity: "quantity - :item.quantity"
        where: "product_id = :item.product_id"

      # Create shipment if all items available
      - create: shipment
        condition: "all_items_available(:order.id)"
        data:
          order_id: :order.id
          status: pending
          estimated_delivery: "NOW() + INTERVAL '3 days'"

      # Update order status based on shipment
      - update: order
        data:
          status: "CASE WHEN :shipment.id IS NOT NULL THEN 'confirmed' ELSE 'pending' END"
        where: "id = :order.id"
```

## 🔄 Transaction Management

### Transaction Levels

```yaml
patterns:
  - name: multi_entity
    operation: critical_operation
    transaction: required
    isolation_level: serializable  # Highest isolation

    steps:
      # All steps in single transaction
      - create: record_a
      - update: record_b
      - create: record_c
```

**Isolation Levels:**
- `read_uncommitted` - Lowest isolation, allows dirty reads
- `read_committed` - Default, prevents dirty reads
- `repeatable_read` - Prevents non-repeatable reads
- `serializable` - Highest isolation, prevents phantom reads

### Compensation Actions

For saga-style transactions:

```yaml
patterns:
  - name: multi_entity
    operation: transfer_money
    entities: [account, transfer, transaction_log]
    transaction: saga  # Allow compensation

    steps:
      - update: account
        data:
          balance: "balance - :amount"
        where: "id = :from_account_id"
        compensation:
          balance: "balance + :amount"  # Rollback action

      - update: account
        data:
          balance: "balance + :amount"
        where: "id = :to_account_id"
        compensation:
          balance: "balance - :amount"

      - create: transfer
        data:
          from_account_id: :from_account_id
          to_account_id: :to_account_id
          amount: :amount
          status: completed
```

## 📊 Data Flow and Variables

### Variable Scope

```yaml
patterns:
  - name: multi_entity
    operation: complex_operation

    steps:
      # Create parent record
      - create: parent
        data:
          name: :input_name
        # Result available as :parent

      # Use parent ID in child records
      - create: child
        for_each: :input_children
        data:
          parent_id: :parent.id  # Reference created parent
          name: :child.name

      # Update parent with child count
      - update: parent
        data:
          child_count: "COUNT(*) FROM child WHERE parent_id = :parent.id"
        where: "id = :parent.id"
```

### Loop Operations

```yaml
patterns:
  - name: multi_entity
    operation: bulk_update

    steps:
      - update: user
        for_each: :user_updates
        condition: "can_update_user(:user.id, :current_user_id)"
        data:
          email: :update.email
          name: :update.name
          updated_at: "NOW()"
        where: "id = :user.id"
        # :user refers to current iteration item
```

## 🧪 Testing Multi-Entity Operations

### Generated Tests

```bash
# Generate comprehensive tests
specql generate tests entities/order.yaml

# Run tests
specql test run entities/order.yaml
```

**Test Coverage:**
- ✅ **Transaction integrity** - All changes succeed or fail
- ✅ **Data consistency** - Related records stay synchronized
- ✅ **Validation rules** - Preconditions enforced
- ✅ **Error handling** - Rollback on failures
- ✅ **Edge cases** - Empty inputs, invalid data

### Manual Testing

```sql
-- Test successful operation
SELECT create_order_with_items(
  'customer-uuid'::UUID,
  '[
    {"product_id": "prod-1", "quantity": 2, "unit_price": 10.00},
    {"product_id": "prod-2", "quantity": 1, "unit_price": 25.00}
  ]'::JSONB
);

-- Verify results
SELECT o.*, oi.* FROM order o
JOIN order_item oi ON o.id = oi.order_id
WHERE o.customer_id = 'customer-uuid';

-- Test failure case (insufficient inventory)
SELECT create_order_with_items(
  'customer-uuid'::UUID,
  '[{"product_id": "out-of-stock", "quantity": 100, "unit_price": 10.00}]'::JSONB
);
-- Should fail and rollback
```

## 🚀 Common Use Cases

### E-commerce Order Processing

```yaml
patterns:
  - name: multi_entity
    description: "Complete order fulfillment"
    operation: place_order
    entities: [order, order_item, inventory, payment]

    steps:
      # Validate inventory
      - validate: inventory
        for_each: :items
        condition: "quantity >= :item.quantity"

      # Create order
      - create: order
        data:
          customer_id: :customer_id
          status: pending
          total_amount: :calculated_total

      # Create items and update inventory
      - create: order_item
        for_each: :items
        data:
          order_id: :order.id
          product_id: :item.product_id
          quantity: :item.quantity
          unit_price: :item.price

      - update: inventory
        for_each: :items
        data:
          quantity: "quantity - :item.quantity"
        where: "product_id = :item.product_id"

      # Process payment
      - create: payment
        data:
          order_id: :order.id
          amount: :calculated_total
          method: :payment_method

      # Update order status
      - update: order
        data:
          status: confirmed
        where: "id = :order.id"
```

### User Registration with Profile

```yaml
patterns:
  - name: multi_entity
    description: "Complete user registration"
    operation: register_user
    entities: [user, user_profile, user_preferences, email_verification]

    steps:
      # Create user account
      - create: user
        data:
          email: :email
          password_hash: :password_hash
          status: pending_verification

      # Create profile
      - create: user_profile
        data:
          user_id: :user.id
          first_name: :first_name
          last_name: :last_name
          date_of_birth: :date_of_birth

      # Set default preferences
      - create: user_preferences
        data:
          user_id: :user.id
          theme: light
          notifications_enabled: true
          language: en

      # Create verification token
      - create: email_verification
        data:
          user_id: :user.id
          token: :verification_token
          expires_at: "NOW() + INTERVAL '24 hours'"

      # Send welcome email
      - notify: user_registered
        data:
          user_id: :user.id
          email: :email
```

### Invoice Generation

```yaml
patterns:
  - name: multi_entity
    description: "Generate invoice with line items"
    operation: create_invoice
    entities: [invoice, invoice_item, tax_calculation]

    steps:
      # Create invoice header
      - create: invoice
        data:
          customer_id: :customer_id
          issue_date: "NOW()"
          due_date: "NOW() + INTERVAL '30 days'"
          status: draft

      # Create invoice items
      - create: invoice_item
        for_each: :line_items
        data:
          invoice_id: :invoice.id
          description: :item.description
          quantity: :item.quantity
          unit_price: :item.unit_price
          total_price: ":item.quantity * :item.unit_price"

      # Calculate taxes
      - create: tax_calculation
        data:
          invoice_id: :invoice.id
          subtotal: "SUM(total_price) FROM invoice_item WHERE invoice_id = :invoice.id"
          tax_rate: :tax_rate
          tax_amount: "subtotal * :tax_rate"
          total_amount: "subtotal + tax_amount"

      # Update invoice totals
      - update: invoice
        data:
          subtotal: :tax_calculation.subtotal
          tax_amount: :tax_calculation.tax_amount
          total_amount: :tax_calculation.total_amount
          status: issued
        where: "id = :invoice.id"
```

## 🎯 Best Practices

### Transaction Design
- **Keep transactions short** - Minimize lock time
- **Use appropriate isolation** - Balance consistency vs performance
- **Handle deadlocks** - Design to prevent circular dependencies
- **Plan rollback scenarios** - Know how to undo operations

### Data Consistency
- **Validate early** - Check preconditions before changes
- **Maintain invariants** - Ensure business rules stay true
- **Use constraints** - Database-level data integrity
- **Test edge cases** - Partial failures, concurrent operations

### Performance
- **Index foreign keys** - Speed up joins and lookups
- **Batch operations** - Group similar operations
- **Cache reference data** - Avoid repeated lookups
- **Monitor slow queries** - Optimize bottlenecks

### Error Handling
- **Clear error messages** - Explain what went wrong
- **Partial failure handling** - Decide whether to rollback
- **Retry logic** - Handle transient failures
- **Logging** - Track operation success/failure

## 🆘 Troubleshooting

### "Transaction rolled back"
```sql
-- Check for constraint violations
SELECT * FROM information_schema.constraint_column_usage
WHERE table_name = 'your_table';

-- Check foreign key constraints
SELECT * FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY';
```

### "Deadlock detected"
```bash
# Analyze deadlock
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"

# Common causes:
# - Circular dependencies in updates
# - Inconsistent order of table access
# - Long-running transactions
```

### "Foreign key violation"
```sql
-- Check referential integrity
SELECT
  tc.table_name, kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE constraint_type = 'FOREIGN KEY';
```

### "Performance issues"
```yaml
# Add indexes for multi-entity operations
indexes:
  - fields: [customer_id, status]  # For order lookups
  - fields: [order_id]             # For order items
  - fields: [product_id, quantity] # For inventory checks
```

## 🎉 Summary

Multi-entity patterns provide:
- ✅ **Transactional consistency** - All or nothing operations
- ✅ **Cross-table coordination** - Related data stays synchronized
- ✅ **Complex business logic** - Multi-step operations in one call
- ✅ **Data integrity** - Referential constraints maintained
- ✅ **Comprehensive testing** - Full transaction coverage

## 🚀 What's Next?

- **[Batch Operations](batch-operations.md)** - Bulk data processing
- **[Validation](validation.md)** - Data integrity patterns
- **[State Machines](state-machines.md)** - Entity lifecycle management
- **[Examples](../../examples/)** - Real-world multi-entity operations

**Ready to handle complex transactions? Let's continue! 🚀**