# Primitive Actions Reference

This document describes the 35 primitive actions in SpecQL - the fundamental building blocks for business logic. These primitives are automatically compiled into optimized PostgreSQL, Django, and SQLAlchemy code.

## Overview

Primitive actions are the atomic operations that make up business logic. They are:

- **Composable**: Can be combined to create complex workflows
- **Multi-language**: Generate code for PostgreSQL, Django, and SQLAlchemy
- **Optimized**: Each primitive compiles to efficient, production-ready code
- **Tested**: Comprehensive test coverage for all implementations

## Categories

### 🔧 Control Flow Primitives

#### `declare`
Declare variables with optional default values.

```yaml
steps:
  - type: declare
    variable_name: total_amount
    variable_type: numeric
    default_value: 0
```

**Generated PostgreSQL:**
```sql
total_amount numeric := 0;
```

**Generated Django:**
```python
total_amount = Decimal('0')
```

#### `assign`
Assign values to variables or fields.

```yaml
steps:
  - type: assign
    variable_name: total_amount
    expression: "SELECT SUM(amount) FROM order_items WHERE order_id = p_order_id"
```

**Generated PostgreSQL:**
```sql
total_amount := (SELECT SUM(amount) FROM order_items WHERE order_id = p_order_id);
```

#### `return`
Return a value from a function.

```yaml
steps:
  - type: return
    expression: total_amount
```

**Generated PostgreSQL:**
```sql
RETURN total_amount;
```

#### `return_early`
Exit function early without a return value.

```yaml
steps:
  - type: return_early
```

**Generated PostgreSQL:**
```sql
RETURN;
```

### 🔄 Loop Primitives

#### `while`
Execute steps while a condition is true.

```yaml
steps:
  - type: while
    condition: "counter < 10"
    steps:
      - type: assign
        variable_name: counter
        expression: "counter + 1"
```

**Generated PostgreSQL:**
```sql
WHILE counter < 10 LOOP
    counter := counter + 1;
END LOOP;
```

#### `for_query`
Iterate over results of a query.

```yaml
steps:
  - type: for_query
    query: "SELECT id, amount FROM order_items WHERE order_id = p_order_id"
    row_variable: item
    steps:
      - type: assign
        variable_name: total
        expression: "total + item.amount"
```

**Generated PostgreSQL:**
```sql
FOR item IN SELECT id, amount FROM order_items WHERE order_id = p_order_id LOOP
    total := total + item.amount;
END LOOP;
```

### 🌐 Function Call Primitives

#### `call_function`
Call a PostgreSQL function and optionally store the result.

```yaml
steps:
  - type: call_function
    function_name: calculate_tax
    arguments: [subtotal, tax_rate]
    result_variable: tax_amount
```

**Generated PostgreSQL:**
```sql
tax_amount := calculate_tax(subtotal, tax_rate);
```

#### `call_service`
Call a service function (external API or microservice).

```yaml
steps:
  - type: call_service
    service_name: payment_gateway
    service_function: process_payment
    parameters:
      amount: total_amount
      currency: "USD"
      card_token: payment_token
```

**Generated PostgreSQL:**
```sql
-- Calls external service via configured adapter
SELECT * FROM service.call_service('payment_gateway', 'process_payment', jsonb_build_object(
    'amount', total_amount,
    'currency', 'USD',
    'card_token', payment_token
));
```

### 🗃️ Database Operation Primitives

#### `insert`
Insert a new record into a table.

```yaml
steps:
  - type: insert
    table: contacts
    data:
      first_name: "{{ first_name }}"
      last_name: "{{ last_name }}"
      email: "{{ email }}"
      created_at: "NOW()"
```

**Generated PostgreSQL:**
```sql
INSERT INTO contacts (first_name, last_name, email, created_at)
VALUES (p_first_name, p_last_name, p_email, NOW());
```

#### `update`
Update existing records in a table.

```yaml
steps:
  - type: update
    table: contacts
    data:
      updated_at: "NOW()"
      status: "'active'"
    where: "id = {{ contact_id }}"
```

**Generated PostgreSQL:**
```sql
UPDATE contacts
SET updated_at = NOW(), status = 'active'
WHERE id = p_contact_id;
```

#### `delete`
Delete records from a table.

```yaml
steps:
  - type: delete
    table: contacts
    where: "id = {{ contact_id }}"
```

**Generated PostgreSQL:**
```sql
DELETE FROM contacts WHERE id = p_contact_id;
```

#### `select`
Query data from tables.

```yaml
steps:
  - type: select
    query: "SELECT * FROM contacts WHERE id = {{ contact_id }}"
    result_variable: contact_data
```

**Generated PostgreSQL:**
```sql
SELECT * INTO contact_data
FROM contacts WHERE id = p_contact_id;
```

### 🔀 Conditional Primitives

#### `if`
Execute steps conditionally.

```yaml
steps:
  - type: if
    condition: "total_amount > 1000"
    then_steps:
      - type: assign
        variable_name: discount
        expression: "total_amount * 0.1"
    else_steps:
      - type: assign
        variable_name: discount
        expression: "0"
```

**Generated PostgreSQL:**
```sql
IF total_amount > 1000 THEN
    discount := total_amount * 0.1;
ELSE
    discount := 0;
END IF;
```

#### `switch`
Multi-branch conditional logic.

```yaml
steps:
  - type: switch
    expression: status
    cases:
      - value: "'draft'"
        steps:
          - type: assign
            variable_name: can_edit
            expression: "true"
      - value: "'published'"
        steps:
          - type: assign
            variable_name: can_edit
            expression: "false"
    default_steps:
      - type: assign
        variable_name: can_edit
        expression: "false"
```

**Generated PostgreSQL:**
```sql
CASE status
    WHEN 'draft' THEN
        can_edit := true;
    WHEN 'published' THEN
        can_edit := false;
    ELSE
        can_edit := false;
END CASE;
```

### 📊 Query Building Primitives

#### `cte`
Define Common Table Expressions (WITH clauses).

```yaml
steps:
  - type: cte
    name: active_orders
    query: "SELECT * FROM orders WHERE status = 'active'"
  - type: select
    query: "SELECT * FROM active_orders WHERE total > 100"
    result_variable: high_value_orders
```

**Generated PostgreSQL:**
```sql
WITH active_orders AS (
    SELECT * FROM orders WHERE status = 'active'
)
SELECT * INTO high_value_orders
FROM active_orders WHERE total > 100;
```

#### `subquery`
Use subqueries in expressions.

```yaml
steps:
  - type: assign
    variable_name: order_count
    expression: "(SELECT COUNT(*) FROM order_items WHERE order_id = p_order_id)"
```

**Generated PostgreSQL:**
```sql
order_count := (SELECT COUNT(*) FROM order_items WHERE order_id = p_order_id);
```

#### `aggregate`
Perform aggregation operations.

```yaml
steps:
  - type: aggregate
    operation: sum
    field: amount
    table: order_items
    where: "order_id = p_order_id"
    result_variable: total_amount
```

**Generated PostgreSQL:**
```sql
SELECT SUM(amount) INTO total_amount
FROM order_items WHERE order_id = p_order_id;
```

### 🛡️ Validation Primitives

#### `validate`
Validate conditions and raise errors if they fail.

```yaml
steps:
  - type: validate
    condition: "email IS NOT NULL"
    error_message: "Email is required"
  - type: validate
    condition: "amount > 0"
    error_message: "Amount must be positive"
```

**Generated PostgreSQL:**
```sql
IF NOT (email IS NOT NULL) THEN
    RAISE EXCEPTION 'Email is required';
END IF;

IF NOT (amount > 0) THEN
    RAISE EXCEPTION 'Amount must be positive';
END IF;
```

#### `duplicate_check`
Check for duplicate records before insertion.

```yaml
steps:
  - type: duplicate_check
    table: contacts
    fields: [email]
    error_message: "Contact with this email already exists"
```

**Generated PostgreSQL:**
```sql
IF EXISTS (SELECT 1 FROM contacts WHERE email = p_email) THEN
    RAISE EXCEPTION 'Contact with this email already exists';
END IF;
```

### 📢 Notification Primitives

#### `notify`
Send notifications (email, webhook, etc.).

```yaml
steps:
  - type: notify
    channel: email
    template: order_confirmation
    recipients: ["{{ customer_email }}"]
    data:
      order_id: "{{ order_id }}"
      total: "{{ total_amount }}"
```

**Generated PostgreSQL:**
```sql
-- Calls notification service
PERFORM notification.send_email(
    'order_confirmation',
    ARRAY[p_customer_email],
    jsonb_build_object('order_id', p_order_id, 'total', total_amount)
);
```

### 🔄 Exception Handling Primitives

#### `exception_handling`
Handle exceptions with try/catch logic.

```yaml
steps:
  - type: exception_handling
    try_steps:
      - type: call_service
        service_name: payment_gateway
        service_function: charge_card
        parameters: {amount: total_amount}
    catch_steps:
      - type: assign
        variable_name: payment_failed
        expression: "true"
      - type: notify
        channel: alert
        message: "Payment processing failed"
```

**Generated PostgreSQL:**
```sql
BEGIN
    -- Call payment service
    PERFORM service.call_service('payment_gateway', 'charge_card', jsonb_build_object('amount', total_amount));
EXCEPTION WHEN OTHERS THEN
    payment_failed := true;
    -- Send alert notification
END;
```

### 🏗️ Advanced Primitives

#### `json_build`
Build JSON objects from data.

```yaml
steps:
  - type: json_build
    result_variable: order_summary
    fields:
      order_id: "{{ order_id }}"
      total: "{{ total_amount }}"
      items: "{{ item_count }}"
      customer: "{{ customer_name }}"
```

**Generated PostgreSQL:**
```sql
order_summary := jsonb_build_object(
    'order_id', p_order_id,
    'total', total_amount,
    'items', item_count,
    'customer', customer_name
);
```

#### `foreach`
Iterate over array elements.

```yaml
steps:
  - type: foreach
    array_variable: order_items
    item_variable: item
    steps:
      - type: assign
        variable_name: total
        expression: "total + item.price * item.quantity"
```

**Generated PostgreSQL:**
```sql
FOREACH item IN ARRAY order_items LOOP
    total := total + (item->>'price')::numeric * (item->>'quantity')::integer;
END LOOP;
```

#### `partial_update`
Update only specified fields (avoids overwriting with NULL).

```yaml
steps:
  - type: partial_update
    table: contacts
    data:
      first_name: "{{ first_name }}"
      email: "{{ email }}"
    where: "id = {{ contact_id }}"
```

**Generated PostgreSQL:**
```sql
UPDATE contacts SET
    first_name = CASE WHEN p_first_name IS NOT NULL THEN p_first_name ELSE first_name END,
    email = CASE WHEN p_email IS NOT NULL THEN p_email ELSE email END
WHERE id = p_contact_id;
```

## Complete Primitive List

Here's the complete list of all 35 primitive actions:

### Control Flow (5)
- `declare` - Variable declaration
- `assign` - Value assignment
- `return` - Function return
- `return_early` - Early exit
- `switch` - Multi-branch conditional

### Loops (3)
- `while` - Conditional loop
- `for_query` - Query result iteration
- `foreach` - Array iteration

### Database Operations (6)
- `insert` - Record insertion
- `update` - Record update
- `delete` - Record deletion
- `select` - Data selection
- `partial_update` - Selective field update
- `duplicate_check` - Uniqueness validation

### Function Calls (2)
- `call_function` - PostgreSQL function call
- `call_service` - External service call

### Conditionals (2)
- `if` - Binary conditional
- `switch` - Multi-branch conditional

### Query Building (4)
- `cte` - Common Table Expression
- `subquery` - Subquery usage
- `aggregate` - Aggregation operations
- `json_build` - JSON object construction

### Validation (2)
- `validate` - Condition validation
- `duplicate_check` - Uniqueness check

### Notifications (1)
- `notify` - Notification sending

### Exception Handling (1)
- `exception_handling` - Try/catch logic

### Advanced (9)
- `fk_resolver` - Foreign key resolution
- `refresh_table_view` - View refresh
- `rich_type_handler` - Complex type handling
- `json_build` - JSON construction
- `validate` - Data validation
- `exception_handling` - Error handling
- `notify` - Notifications
- `call_service` - Service integration
- `partial_update` - Selective updates

## Usage in Actions

Primitives are used within action definitions:

```yaml
actions:
  - name: create_order
    type: insert
    description: "Create a new order with validation"
    parameters:
      customer_id: uuid
      items: jsonb
    steps:
      # Validation primitives
      - type: validate
        condition: "customer_id IS NOT NULL"
        error_message: "Customer ID is required"

      # Database primitives
      - type: insert
        table: orders
        data:
          customer_id: "{{ customer_id }}"
          status: "'pending'"
          created_at: "NOW()"

      # Notification primitives
      - type: notify
        channel: email
        template: order_created
        recipients: ["customer@example.com"]
```

## Multi-Language Generation

Each primitive generates optimized code for all target languages:

- **PostgreSQL**: Efficient PL/pgSQL with proper error handling
- **Django**: Python ORM operations with transaction management
- **SQLAlchemy**: SQLAlchemy Core queries with connection handling

## Best Practices

1. **Compose Primitives**: Combine simple primitives for complex logic
2. **Validate Early**: Use validation primitives at the start of actions
3. **Handle Errors**: Wrap critical operations in exception handling
4. **Keep it Simple**: Use the right primitive for each operation
5. **Test Generated Code**: Always test the generated multi-language output

## Related Documentation

- [Domain Patterns](../domain_patterns.md) - Higher-level business patterns
- [Entity Templates](../entity_templates.md) - Pre-built entity configurations
- [CLI Commands](../cli_commands.md) - Command-line interface reference
- [Migration Guide](../../guides/migration_guide.md) - Converting legacy code