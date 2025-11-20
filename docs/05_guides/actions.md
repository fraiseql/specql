# SpecQL Actions: Business Logic Implementation Guide

> **Master SpecQL actions—the declarative way to implement complex business logic in PostgreSQL**

## Overview

**Actions** are SpecQL's approach to business logic. They compile YAML declarations into production-ready PL/pgSQL functions with automatic:
- ✅ Transaction safety
- ✅ Error handling
- ✅ Type validation
- ✅ Audit trails
- ✅ FraiseQL GraphQL integration

**Think of it as**: SQL stored procedures, but declarative, type-safe, and 95% less code.

---

## What Are Actions?

Actions define **business workflows** as a series of declarative steps. Each action compiles to:

1. **Core PL/pgSQL Function** (`{schema}.{action_name}`)
   - Contains business logic
   - Returns structured result
   - Handles errors

2. **GraphQL Wrapper** (`app.{action_name}`)
   - FraiseQL-compatible mutation
   - Returns `mutation_result` type
   - Includes impact metadata

### Before/After Example

**Before** (Hand-written PL/pgSQL - 87 lines):
```sql
CREATE FUNCTION crm.qualify_lead(
    p_contact_id UUID
) RETURNS TABLE(...) AS $$
DECLARE
    v_contact RECORD;
    v_result RECORD;
BEGIN
    -- Fetch contact
    SELECT * INTO v_contact
    FROM crm.tb_contact
    WHERE id = p_contact_id FOR UPDATE;

    -- Validate
    IF v_contact IS NULL THEN
        RAISE EXCEPTION 'Contact not found';
    END IF;

    IF v_contact.status != 'lead' THEN
        RAISE EXCEPTION 'Only leads can be qualified';
    END IF;

    -- Update
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = NOW()
    WHERE id = p_contact_id;

    -- Send notification
    PERFORM pg_notify('lead_qualified', json_build_object(
        'contact_id', p_contact_id,
        'email', v_contact.email
    )::text);

    -- Return result
    RETURN QUERY SELECT * FROM crm.tb_contact WHERE id = p_contact_id;
END;
$$ LANGUAGE plpgsql;
```

**After** (SpecQL - 8 lines):
```yaml
entity: Contact
schema: crm

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead', error: "Only leads can be qualified"
      - update: Contact SET status = 'qualified'
      - notify: lead_qualified, to: $email
```

**Result**: 87 lines → 8 lines (91% reduction)

---

## Action Anatomy

```yaml
entity: Order
schema: sales

actions:
  - name: process_payment          # Action name
    description: "Process order payment"  # Optional documentation
    params:                        # Input parameters
      amount: money!
      payment_method: text!

    steps:                         # Business logic steps
      - validate: status != 'paid'  # Step 1: Validate
      - update: ...                 # Step 2: Update data
      - insert: ...                 # Step 3: Create records
      - notify: ...                 # Step 4: Send events
```

### Key Components

1. **Name**: Unique action identifier (becomes function name)
2. **Description**: Optional documentation
3. **Params**: Input parameters with types
4. **Steps**: Ordered list of operations

---

## Action Steps Reference

### Available Step Types

| Step | Purpose | Example |
|------|---------|---------|
| `validate` | Assert conditions | `validate: status = 'draft'` |
| `if` | Conditional logic | `if: total > 1000` |
| `insert` | Create records | `insert: Order VALUES (...)` |
| `update` | Modify records | `update: Order SET status = 'paid'` |
| `delete` | Remove records | `delete: OrderItem WHERE ...` |
| `call` | Invoke functions | `call: calculate_tax(...)` |
| `notify` | Send events | `notify: order_placed` |
| `foreach` | Loop over data | `foreach: items as item` |
| `refresh` | Refresh views | `refresh: order_statistics` |

**Full Reference**: [Action Steps Reference](../06_reference/action-steps.md)

---

## Common Patterns

### 1. Simple CRUD Operation

```yaml
actions:
  - name: archive_contact
    steps:
      - update: Contact SET deleted_at = now()
```

**Generates**:
- Soft delete function
- Automatic audit trail
- GraphQL mutation

### 2. Multi-Step Workflow

```yaml
actions:
  - name: approve_contract
    steps:
      - validate: status = 'pending', error: "Contract not pending"
      - validate: total_value > 0, error: "Invalid contract value"

      - update: Contract SET status = 'approved', approved_at = now()
      - update: Customer SET contract_count = contract_count + 1

      - insert: ContractHistory VALUES (
          contract_id: $contract_id,
          action: 'approved',
          user_id: $current_user_id
        )

      - notify: contract_approved
```

**Generates**:
- Transaction-safe function
- Multiple validations
- Cross-entity updates
- Audit trail
- Event notification

### 3. Conditional Logic

```yaml
actions:
  - name: process_order
    steps:
      - validate: status = 'pending'

      - if: total > 10000
        then:
          - call: require_manager_approval
          - update: Order SET requires_approval = true
        else:
          - update: Order SET status = 'approved'
          - call: send_order_confirmation
```

**Generates**:
- Branching logic
- Conditional execution
- Different code paths

### 4. Loops and Iteration

```yaml
actions:
  - name: apply_discounts
    steps:
      - foreach: OrderItem WHERE order_id = $order_id as item
        do:
          - if: item.quantity >= 10
            then:
              - update: OrderItem
                SET price = price * 0.9
                WHERE id = $item.id
```

**Generates**:
- Loop over results
- Batch processing
- Conditional updates

### 5. Complex Validation

```yaml
actions:
  - name: create_high_value_order
    steps:
      - validate: total > 0, error: "Order total must be positive"
      - validate: customer.credit_limit >= total,
                 error: "Exceeds customer credit limit"
      - validate: call(check_inventory_available, $items),
                 error: "Insufficient inventory"

      - insert: Order FROM $order_data
```

**Generates**:
- Multiple validation checks
- Custom validation functions
- Early error returns

### 6. Cross-Entity Operations

```yaml
actions:
  - name: transfer_funds
    params:
      from_account_id: uuid!
      to_account_id: uuid!
      amount: money!

    steps:
      - validate: amount > 0
      - validate: call(check_balance, $from_account_id, $amount)

      - update: Account
        SET balance = balance - $amount
        WHERE id = $from_account_id

      - update: Account
        SET balance = balance + $amount
        WHERE id = $to_account_id

      - insert: Transaction VALUES (
          from_account: $from_account_id,
          to_account: $to_account_id,
          amount: $amount,
          type: 'transfer'
        )
```

**Generates**:
- Atomic transaction
- Cross-entity updates
- Transaction logging

---

## Parameters

### Defining Parameters

```yaml
actions:
  - name: create_invoice
    params:
      customer_id: uuid!           # Required UUID
      items: list(InvoiceItem)!    # Required list
      discount: decimal(0, 100)    # Optional decimal 0-100
      notes: text                  # Optional text
```

### Parameter Types

| Type | Example | Description |
|------|---------|-------------|
| `uuid!` | Required UUID | Primary key reference |
| `text!` | Required text | String parameter |
| `integer(0, 100)` | Range integer | With min/max |
| `money!` | Required money | Currency amount |
| `date` | Optional date | Date parameter |
| `list(Type)!` | Required list | Array parameter |
| `enum(a, b, c)!` | Required enum | One of values |

### Accessing Parameters

```yaml
steps:
  - validate: $customer_id EXISTS IN Customer
  - update: Invoice SET total = $total
  - insert: Item VALUES (price: $price)
```

Parameters are prefixed with `$` in expressions.

---

## Return Values

### Automatic Returns

By default, actions return:
- **Success**: `mutation_result` with updated entity
- **Error**: Error code, message, and status

```typescript
// Auto-generated return type
type QualifyLeadResult = {
  status: 'success' | 'error';
  code: string;
  message?: string;
  data?: Contact;        // Full updated object
  _meta: {
    impacts: Impact[];   // Side effects
  };
};
```

### Custom Return Data

```yaml
actions:
  - name: calculate_order_total
    steps:
      - call: sum_items, result: $subtotal
      - call: calculate_tax, args: {amount: $subtotal}, result: $tax
      - return: {
          subtotal: $subtotal,
          tax: $tax,
          total: $subtotal + $tax
        }
```

---

## Error Handling

### Validation Errors

```yaml
steps:
  - validate: status = 'draft'
    error: "not_in_draft_status"
    message: "Order must be in draft status to edit"
```

**Generated Error Response**:
```json
{
  "status": "error",
  "code": "not_in_draft_status",
  "message": "Order must be in draft status to edit"
}
```

### Try/Catch Equivalent

```yaml
steps:
  - if: call(risky_operation)
    then:
      - update: Order SET status = 'completed'
    else:
      - update: Order SET status = 'failed'
      - notify: operation_failed
```

### Database Constraint Errors

SpecQL automatically catches and translates:
- **Unique violations** → `duplicate_key`
- **Foreign key violations** → `invalid_reference`
- **Check constraint violations** → `constraint_violation`
- **Not null violations** → `required_field_missing`

---

## Transaction Safety

### Automatic Transactions

**Every action runs in a transaction**:
```yaml
actions:
  - name: process_order
    steps:
      - update: Customer SET balance = balance - $total
      - insert: Order FROM $order_data
      - update: Inventory SET stock = stock - $quantity
      # ✅ All succeed or all rollback
```

**Generated**:
```sql
BEGIN;
  UPDATE customers ...
  INSERT INTO orders ...
  UPDATE inventory ...
COMMIT;
-- ❌ Any failure → automatic ROLLBACK
```

### Nested Transactions

```yaml
steps:
  - call: process_payment  # This is also transactional
  - update: Order SET status = 'paid'
  # ✅ Both succeed or both rollback
```

---

## Impact Metadata

Actions automatically track side effects for UI updates:

```yaml
actions:
  - name: approve_order
    impacts:
      - entity: Order
        operation: update
        filters: {id: $order_id}
      - entity: Customer
        operation: update
        filters: {id: $customer_id}
      - entity: Notification
        operation: insert
```

**Generated Metadata**:
```json
{
  "_meta": {
    "impacts": [
      {"entity": "Order", "operation": "update", "ids": ["123"]},
      {"entity": "Customer", "operation": "update", "ids": ["456"]},
      {"entity": "Notification", "operation": "insert"}
    ]
  }
}
```

**Frontend Use**:
- Apollo cache updates
- Optimistic UI
- Real-time sync

---

## Testing Actions

### Generated Test Helpers

SpecQL auto-generates test utilities:

```typescript
// Auto-generated TypeScript test helpers
import { testQualifyLead } from './generated/test-helpers';

describe('qualify_lead', () => {
  it('should qualify a lead contact', async () => {
    const contact = await createTestContact({ status: 'lead' });

    const result = await testQualifyLead({
      contact_id: contact.id
    });

    expect(result.status).toBe('success');
    expect(result.data.status).toBe('qualified');
  });

  it('should reject non-lead contacts', async () => {
    const contact = await createTestContact({ status: 'customer' });

    const result = await testQualifyLead({
      contact_id: contact.id
    });

    expect(result.status).toBe('error');
    expect(result.code).toBe('only_leads_can_be_qualified');
  });
});
```

### Database Testing

```bash
# Generate test SQL
specql generate entities/*.yaml --with-tests

# Run PL/pgSQL tests
psql -d testdb -f generated/tests/test_actions.sql
```

---

## Performance Optimization

### 1. Batch Operations

**Bad** (N+1 queries):
```yaml
- foreach: orders as order
  do:
    - update: Order SET status = 'shipped' WHERE id = $order.id
```

**Good** (Single query):
```yaml
- update: Order
  SET status = 'shipped'
  WHERE id IN $order_ids
```

### 2. Selective Fetching

```yaml
# Only fetch fields you need
- call: get_customer_email, args: {id: $customer_id}, result: $email
# Instead of fetching entire customer record
```

### 3. Indexing

Actions automatically benefit from Trinity pattern indexes:
- `pk_*` (INTEGER) - Fast lookups
- `id` (UUID) - External references
- Foreign keys - Automatic indexes

---

## Common Patterns & Best Practices

### ✅ DO: Keep Actions Focused

```yaml
# Good: Single responsibility
- name: approve_order
  steps:
    - validate: status = 'pending'
    - update: Order SET status = 'approved'
    - notify: order_approved
```

### ❌ DON'T: Create God Actions

```yaml
# Bad: Too many responsibilities
- name: process_everything
  steps:
    - # 50+ steps doing everything
```

### ✅ DO: Compose Actions

```yaml
- name: complete_checkout
  steps:
    - call: validate_cart
    - call: process_payment
    - call: create_shipment
    - call: send_confirmations
```

### ✅ DO: Use Meaningful Error Codes

```yaml
- validate: balance >= total
  error: "insufficient_funds"  # ✅ Clear
  # NOT: error: "error_123"    # ❌ Unclear
```

### ✅ DO: Document Complex Logic

```yaml
- name: calculate_tiered_discount
  description: |
    Applies tiered discounts based on order total:
    - $0-$100: 0%
    - $100-$500: 5%
    - $500-$1000: 10%
    - $1000+: 15%
```

---

## Advanced Topics

### Custom PL/pgSQL Functions

```yaml
actions:
  - name: complex_calculation
    steps:
      # Call custom PL/pgSQL function
      - call: calculate_amortization_schedule
        args:
          principal: $loan_amount
          rate: $interest_rate
          periods: $term_months
        result: $schedule

      - insert: LoanSchedule FROM $schedule
```

### Event-Driven Actions

```yaml
actions:
  - name: on_order_placed
    trigger: after_insert
    entity: Order
    steps:
      - notify: order_placed
      - call: update_inventory
      - call: send_order_confirmation
```

### Idempotency

```yaml
actions:
  - name: process_payment
    idempotent: true
    idempotency_key: $payment_id
    steps:
      - if: payment_already_processed($payment_id)
        then:
          - return: existing_payment
        else:
          - insert: Payment FROM $payment_data
```

---

## Debugging Actions

### View Generated SQL

```bash
# Generate SQL and inspect
specql generate entities/order.yaml --output generated/

# View the generated function
cat generated/functions/process_order.sql
```

### Enable Query Logging

```sql
-- PostgreSQL logging
SET log_statement = 'all';

-- Execute action
SELECT app.process_order(...);

-- Check logs
\! tail -f /var/log/postgresql/postgresql.log
```

### Use RAISE NOTICE

Custom functions can use `RAISE NOTICE` for debugging:
```sql
RAISE NOTICE 'Processing order_id: %', v_order_id;
```

---

## Migration from Other Frameworks

### From Django/Python

**Before** (Django):
```python
def approve_order(order_id):
    order = Order.objects.get(id=order_id)
    if order.status != 'pending':
        raise ValidationError("Order not pending")
    order.status = 'approved'
    order.save()
    send_notification(order.customer.email)
```

**After** (SpecQL):
```yaml
- name: approve_order
  steps:
    - validate: status = 'pending'
    - update: Order SET status = 'approved'
    - notify: order_approved, to: $customer.email
```

### From TypeScript/Prisma

**Before** (Prisma):
```typescript
async function processPayment(orderId, amount) {
  return await prisma.$transaction(async (tx) => {
    const order = await tx.order.update({
      where: { id: orderId },
      data: { status: 'paid' }
    });

    await tx.customer.update({
      where: { id: order.customerId },
      data: { balance: { decrement: amount } }
    });

    return order;
  });
}
```

**After** (SpecQL):
```yaml
- name: process_payment
  steps:
    - update: Order SET status = 'paid'
    - update: Customer SET balance = balance - $amount
```

---

## Next Steps

- **Tutorial**: [Your First Action](your-first-action.md) - Step-by-step guide
- **Reference**: [Action Steps Reference](../06_reference/action-steps.md) - All step types
- **Advanced**: [Custom Patterns](../07_advanced/custom-patterns.md) - Advanced techniques
- **Examples**: Real-world action patterns
  - [Payment Integration](payment-integration.md)
  - [Order Workflow](order-workflow.md)
  - [Shipping Logic](shipping-logic.md)

---

**Actions are the heart of SpecQL—master them to build powerful, maintainable business logic.**
