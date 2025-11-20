# Error Handling Guide

> **Master error handling in SpecQL—validation, error codes, and user-friendly messages**

## Overview

SpecQL provides structured error handling with:
- ✅ **Typed error responses** (FraiseQL `mutation_result`)
- ✅ **Custom error codes** for business logic
- ✅ **Automatic database constraint errors**
- ✅ **Validation at multiple levels**
- ✅ **User-friendly error messages**

**Result**: Consistent, type-safe error handling across your entire stack.

---

## Error Response Structure

### Standard MutationResult

Every SpecQL action returns a `mutation_result`:

```typescript
type MutationResult<T = any> = {
  status: 'success' | 'error';
  code: string;
  message?: string;
  data?: T;
  _meta?: {
    impacts: Impact[];
  };
};
```

**Examples**:

**Success**:
```json
{
  "status": "success",
  "code": "contact_qualified",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john@example.com",
    "status": "qualified"
  }
}
```

**Error**:
```json
{
  "status": "error",
  "code": "not_a_lead",
  "message": "Only leads can be qualified"
}
```

---

## Validation Errors

### Field Validation

**Simple validation**:
```yaml
actions:
  - name: update_price
    params:
      new_price: money!
    steps:
      - validate: $new_price > 0
        error: "price_must_be_positive"
        message: "Price must be greater than zero"
```

**Result**:
```json
{
  "status": "error",
  "code": "price_must_be_positive",
  "message": "Price must be greater than zero"
}
```

### Multi-Field Validation

```yaml
actions:
  - name: create_order
    steps:
      - validate: total > 0
        error: "invalid_order_total"
        message: "Order total must be positive"

      - validate: customer.balance >= total
        error: "insufficient_funds"
        message: "Customer balance (${customer.balance}) is less than order total (${total})"

      - validate: shipping_address IS NOT NULL
        error: "missing_shipping_address"
        message: "Shipping address is required"
```

**Frontend handling**:
```typescript
const result = await createOrder(orderData);

if (result.status === 'error') {
  switch (result.code) {
    case 'invalid_order_total':
      showFieldError('total', result.message);
      break;
    case 'insufficient_funds':
      showAlert('Payment Error', result.message);
      break;
    case 'missing_shipping_address':
      showFieldError('shippingAddress', result.message);
      break;
  }
}
```

### Existence Validation

```yaml
- validate: customer_id EXISTS IN Customer
  error: "customer_not_found"
  message: "Customer with ID ${customer_id} not found"

- validate: NOT EXISTS (SELECT 1 FROM Order WHERE customer_id = $customer_id AND status = 'pending')
  error: "pending_order_exists"
  message: "Customer already has a pending order"
```

### Custom Validation Functions

```yaml
actions:
  - name: place_order
    steps:
      - validate: call(check_inventory_available, $items)
        error: "insufficient_inventory"
        message: "Some items are out of stock"

      - validate: call(validate_shipping_address, $address)
        error: "invalid_shipping_address"
        message: "Shipping address cannot be validated"
```

---

## Database Constraint Errors

### Automatic Error Translation

SpecQL automatically translates PostgreSQL constraint violations:

**Unique Constraint**:
```yaml
fields:
  email: email!  # Unique constraint
```

```json
// Duplicate email attempt
{
  "status": "error",
  "code": "duplicate_key",
  "message": "Email already exists",
  "details": {
    "constraint": "tb_contact_email_key",
    "field": "email"
  }
}
```

**Foreign Key Violation**:
```yaml
fields:
  company: ref(Company)!
```

```json
// Invalid company_id
{
  "status": "error",
  "code": "invalid_reference",
  "message": "Referenced company does not exist",
  "details": {
    "constraint": "fk_contact_company",
    "field": "company"
  }
}
```

**Not Null Violation**:
```yaml
fields:
  email: email!  # NOT NULL
```

```json
// Missing required field
{
  "status": "error",
  "code": "required_field_missing",
  "message": "Email is required",
  "details": {
    "field": "email"
  }
}
```

**Check Constraint**:
```yaml
fields:
  age: integer(18, 120)!
```

```json
// Age out of range
{
  "status": "error",
  "code": "constraint_violation",
  "message": "Age must be between 18 and 120",
  "details": {
    "constraint": "chk_contact_age",
    "field": "age"
  }
}
```

---

## Error Code Conventions

### Recommended Naming

```yaml
# ✅ Good: Descriptive, lowercase with underscores
error: "insufficient_funds"
error: "customer_not_found"
error: "invalid_shipping_address"
error: "order_already_processed"

# ❌ Bad: Generic or unclear
error: "error"
error: "failed"
error: "error_123"
error: "ERR-001"
```

### Error Code Categories

**Validation Errors** (`invalid_*`, `missing_*`):
```yaml
- error: "invalid_email"
- error: "invalid_phone_number"
- error: "missing_required_field"
```

**Business Rule Errors** (`*_not_allowed`, `cannot_*`):
```yaml
- error: "refund_not_allowed"
- error: "cannot_delete_active_order"
- error: "insufficient_permissions"
```

**State Errors** (`*_already_*`, `not_*`):
```yaml
- error: "order_already_shipped"
- error: "not_authenticated"
- error: "account_not_active"
```

**Resource Errors** (`*_not_found`, `*_exists`):
```yaml
- error: "customer_not_found"
- error: "email_already_exists"
- error: "product_out_of_stock"
```

---

## Conditional Error Handling

### Early Returns

```yaml
actions:
  - name: process_refund
    steps:
      # Validate order exists
      - validate: order_id EXISTS IN Order
        error: "order_not_found"
        message: "Order ${order_id} not found"

      # Validate order is paid
      - validate: status = 'paid'
        error: "order_not_paid"
        message: "Only paid orders can be refunded"

      # Validate refund window
      - validate: paid_at > (NOW() - INTERVAL '30 days')
        error: "refund_window_expired"
        message: "Refunds must be requested within 30 days of payment"

      # All validations passed - process refund
      - update: Order SET status = 'refunded', refunded_at = NOW()
      - update: Customer SET balance = balance + $total
```

### Conditional Logic

```yaml
actions:
  - name: apply_discount
    steps:
      - if: call(is_vip_customer, $customer_id)
        then:
          - update: Order SET discount = 0.20  # 20% VIP discount
        else:
          - if: total > 1000
            then:
              - update: Order SET discount = 0.10  # 10% bulk discount
            else:
              - validate: FALSE
                error: "discount_not_applicable"
                message: "Customer is not eligible for discounts"
```

---

## Error Handling Patterns

### Pattern 1: Validation-Heavy Actions

```yaml
actions:
  - name: create_high_value_order
    params:
      customer_id: uuid!
      items: list(OrderItem)!
      total: money!
    steps:
      # Validate customer
      - validate: customer_id EXISTS IN Customer
        error: "customer_not_found"

      - validate: call(check_customer_status, $customer_id) = 'active'
        error: "customer_account_inactive"

      - validate: call(check_credit_limit, $customer_id, $total)
        error: "exceeds_credit_limit"
        message: "Order total exceeds customer credit limit"

      # Validate items
      - validate: count($items) > 0
        error: "empty_order"
        message: "Order must contain at least one item"

      - foreach: $items as item
        do:
          - validate: item.product_id EXISTS IN Product
            error: "product_not_found"
            message: "Product ${item.product_id} not found"

          - validate: call(check_stock, item.product_id, item.quantity)
            error: "insufficient_stock"
            message: "Insufficient stock for ${item.product_name}"

      # All validations passed
      - insert: Order FROM $order_data
```

### Pattern 2: Try-Catch Equivalent

```yaml
actions:
  - name: process_payment
    steps:
      - if: call(charge_payment_gateway, $payment_data)
        then:
          - update: Order SET status = 'paid', paid_at = NOW()
          - notify: payment_success, to: $customer.email
        else:
          - update: Order SET status = 'payment_failed'
          - insert: PaymentFailure VALUES (
              order_id: $order_id,
              reason: 'gateway_declined',
              timestamp: NOW()
            )
          - notify: payment_failed, to: $customer.email
          - validate: FALSE
            error: "payment_declined"
            message: "Payment was declined by the payment gateway"
```

### Pattern 3: Cascading Validation

```yaml
actions:
  - name: ship_order
    steps:
      # Level 1: Basic validation
      - validate: order_id EXISTS IN Order
        error: "order_not_found"

      # Level 2: State validation
      - validate: status = 'paid'
        error: "order_not_paid"
        message: "Only paid orders can be shipped"

      # Level 3: Business rule validation
      - validate: shipping_address IS NOT NULL
        error: "missing_shipping_address"

      - validate: call(validate_shipping_provider_available, $shipping_address)
        error: "shipping_unavailable"
        message: "Shipping is not available to this address"

      # Level 4: Inventory validation
      - foreach: OrderItem WHERE order_id = $order_id as item
        do:
          - validate: call(reserve_inventory, item.product_id, item.quantity)
            error: "inventory_reservation_failed"
            message: "Could not reserve inventory for ${item.product_name}"

      # All levels passed - proceed
      - update: Order SET status = 'shipped', shipped_at = NOW()
```

---

## Frontend Integration

### React/TypeScript Example

```typescript
import { useMutation } from '@apollo/client';
import { QUALIFY_LEAD } from './mutations';

function QualifyLeadButton({ contactId }: { contactId: string }) {
  const [qualifyLead, { loading, error }] = useMutation(QUALIFY_LEAD);

  const handleQualify = async () => {
    try {
      const result = await qualifyLead({
        variables: { contactId }
      });

      if (result.data.qualifyLead.status === 'success') {
        toast.success('Lead qualified successfully');
      } else {
        // Handle business logic errors
        const { code, message } = result.data.qualifyLead;

        switch (code) {
          case 'not_a_lead':
            toast.error('This contact is not a lead');
            break;
          case 'missing_required_field':
            toast.error('Please complete all required fields first');
            break;
          default:
            toast.error(message || 'Failed to qualify lead');
        }
      }
    } catch (err) {
      // Handle network/GraphQL errors
      console.error('GraphQL error:', err);
      toast.error('Network error - please try again');
    }
  };

  return (
    <button onClick={handleQualify} disabled={loading}>
      {loading ? 'Qualifying...' : 'Qualify Lead'}
    </button>
  );
}
```

### Form Validation Integration

```typescript
interface FormErrors {
  [field: string]: string;
}

function handleMutationError(
  result: MutationResult,
  setErrors: (errors: FormErrors) => void
) {
  const errorMap: Record<string, { field: string; message: string }> = {
    'invalid_email': {
      field: 'email',
      message: 'Please enter a valid email address'
    },
    'email_already_exists': {
      field: 'email',
      message: 'This email is already registered'
    },
    'price_must_be_positive': {
      field: 'price',
      message: 'Price must be greater than zero'
    },
    'insufficient_funds': {
      field: 'total',
      message: result.message || 'Insufficient funds'
    }
  };

  const errorInfo = errorMap[result.code];
  if (errorInfo) {
    setErrors({ [errorInfo.field]: errorInfo.message });
  } else {
    // Generic error
    toast.error(result.message || 'An error occurred');
  }
}
```

---

## Testing Error Cases

### Unit Tests

```typescript
describe('qualify_lead action', () => {
  it('should return error for non-lead contacts', async () => {
    const contact = await createTestContact({ status: 'customer' });

    const result = await qualifyLead({ contactId: contact.id });

    expect(result.status).toBe('error');
    expect(result.code).toBe('not_a_lead');
    expect(result.message).toContain('Only leads');
  });

  it('should return error for missing contact', async () => {
    const result = await qualifyLead({ contactId: 'non-existent-id' });

    expect(result.status).toBe('error');
    expect(result.code).toBe('contact_not_found');
  });

  it('should succeed for valid lead', async () => {
    const contact = await createTestContact({ status: 'lead' });

    const result = await qualifyLead({ contactId: contact.id });

    expect(result.status).toBe('success');
    expect(result.data.status).toBe('qualified');
  });
});
```

### Integration Tests

```sql
-- Test error handling in PL/pgSQL
DO $$
DECLARE
    v_result app.mutation_result;
BEGIN
    -- Test 1: Invalid contact ID
    SELECT * INTO v_result FROM app.qualify_lead('00000000-0000-0000-0000-000000000000');
    ASSERT v_result.status = 'error', 'Should return error for invalid ID';
    ASSERT v_result.code = 'contact_not_found', 'Should have correct error code';

    -- Test 2: Non-lead contact
    INSERT INTO crm.tb_contact (email, status) VALUES ('test@example.com', 'customer')
    RETURNING id INTO v_contact_id;

    SELECT * INTO v_result FROM app.qualify_lead(v_contact_id);
    ASSERT v_result.status = 'error', 'Should return error for non-lead';
    ASSERT v_result.code = 'not_a_lead', 'Should have correct error code';

    RAISE NOTICE 'All tests passed ✅';
END $$;
```

---

## Debugging Errors

### Enable Detailed Error Logging

```sql
-- PostgreSQL logging
SET log_statement = 'all';
SET log_min_messages = 'info';

-- Execute action
SELECT app.qualify_lead('...');

-- View logs
\! tail -f /var/log/postgresql/postgresql.log
```

### Custom Error Logging

```yaml
actions:
  - name: critical_operation
    steps:
      - call: log_operation_start, args: {operation: 'critical_operation'}

      - if: call(risky_step)
        then:
          - call: log_success
        else:
          - call: log_failure, args: {reason: 'risky_step_failed'}
          - validate: FALSE
            error: "operation_failed"
```

---

## Best Practices

### ✅ DO: Provide Context in Error Messages

```yaml
# Good: Includes context
- validate: balance >= amount
  error: "insufficient_funds"
  message: "Account balance ($${balance}) is less than withdrawal amount ($${amount})"

# Bad: Generic message
- validate: balance >= amount
  error: "insufficient_funds"
  message: "Insufficient funds"
```

### ✅ DO: Use Specific Error Codes

```yaml
# Good: Specific codes
- error: "email_already_exists"
- error: "invalid_phone_format"
- error: "order_already_shipped"

# Bad: Generic codes
- error: "validation_error"
- error: "error"
- error: "failed"
```

### ✅ DO: Validate Early

```yaml
# Good: Validate before expensive operations
steps:
  - validate: customer_id EXISTS IN Customer  # Fast check
  - validate: balance >= amount               # Fast check
  - call: expensive_external_api_call        # Only if validations pass

# Bad: Expensive operation before validation
steps:
  - call: expensive_external_api_call
  - validate: balance >= amount  # Too late!
```

### ✅ DO: Handle Both Business and Technical Errors

```typescript
// Frontend error handling
try {
  const result = await mutation();

  if (result.status === 'error') {
    // Business logic error (from SpecQL)
    handleBusinessError(result.code, result.message);
  }
} catch (err) {
  // Technical error (network, GraphQL, etc.)
  handleTechnicalError(err);
}
```

### ❌ DON'T: Expose Internal Details

```yaml
# Bad: Exposes internal implementation
- validate: call(complex_internal_check)
  error: "internal_error"
  message: "Database constraint pk_contact_fkey violated on table tb_contact"

# Good: User-friendly message
- validate: call(complex_internal_check)
  error: "invalid_contact_reference"
  message: "The specified contact is invalid"
```

---

## Common Error Patterns

### Authentication/Authorization

```yaml
actions:
  - name: delete_order
    steps:
      - validate: call(is_authenticated)
        error: "not_authenticated"
        message: "You must be logged in to perform this action"

      - validate: call(has_permission, 'delete_order')
        error: "insufficient_permissions"
        message: "You do not have permission to delete orders"

      - validate: call(owns_order, $order_id, $current_user_id)
        error: "unauthorized_access"
        message: "You can only delete your own orders"
```

### Rate Limiting

```yaml
actions:
  - name: send_email
    steps:
      - validate: call(check_rate_limit, $user_id, 'email', 100, '1 hour')
        error: "rate_limit_exceeded"
        message: "You have exceeded the email sending limit. Please try again later."
```

### Idempotency

```yaml
actions:
  - name: process_payment
    steps:
      - validate: NOT EXISTS (
          SELECT 1 FROM payments
          WHERE idempotency_key = $idempotency_key
        )
        error: "duplicate_request"
        message: "This payment has already been processed"
```

---

## Next Steps

- **Tutorial**: [Your First Action](your-first-action.md) - Implement error handling
- **Reference**: [Action Steps](../06_reference/action-steps.md) - Validation step syntax
- **Guide**: [Actions](actions.md) - Complete actions guide
- **Advanced**: [Custom Validators](../07_advanced/custom-validators.md) - Custom validation logic

---

**Error handling in SpecQL is structured, type-safe, and user-friendly—build robust applications with confidence.**
