# call_function - Function Calls

Call other SpecQL functions and capture their return values.

## Syntax

```yaml
- call_function:
    function: schema.function_name
    arguments:
      param1: value1
      param2: $parameter_reference
    returns: result_variable (optional)
```

## Parameters

- `function`: The function to call (schema.function_name format)
- `arguments`: Key-value pairs of arguments to pass
- `returns`: Variable to store the return value (optional)

## Examples

### Call with Return Value
```yaml
entity: Invoice
actions:
  - name: process_invoice
    steps:
      - declare:
          name: calculated_total
          type: numeric

      - call_function:
          function: billing.calculate_total
          arguments:
            invoice_id: $invoice_id
          returns: calculated_total

      - update: Invoice SET total_amount = calculated_total WHERE id = $invoice_id
```

### Function Composition
```yaml
entity: Order
actions:
  - name: complex_calculation
    steps:
      - call_function:
          function: calculate_subtotal
          arguments:
            order_id: $order_id
          returns: subtotal

      - call_function:
          function: calculate_tax
          arguments:
            amount: $subtotal
            region: $region
          returns: tax_amount

      - call_function:
          function: apply_discount
          arguments:
            amount: $subtotal
            customer_id: $customer_id
          returns: discount_amount

      - assign: final_total = subtotal + tax_amount - discount_amount
      - return: final_total
```

### Call Without Return Value
```yaml
entity: Notification
actions:
  - name: send_notification
    steps:
      - call_function:
          function: notification.send_email
          arguments:
            to: $email
            subject: "Order Confirmed"
            body: $message
      # No returns specified, function called for side effects
```

## Generated SQL

```sql
-- With return value
SELECT billing.calculate_total(invoice_id) INTO calculated_total;

-- Without return value
PERFORM notification.send_email('user@example.com', 'Subject', 'Body');
```

## Argument Handling

- Parameter references: `$param_name` (removes $ prefix)
- String literals: Automatically quoted
- Other values: Converted to string

## Notes

- Functions must exist and be accessible
- Return values are captured in declared variables
- Use `returns` for functions that return values
- Omit `returns` for void functions (side effects only)
