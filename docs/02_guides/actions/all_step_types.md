# All Step Types Reference

**Complete guide to all 25+ action step types** - From basic operations to advanced patterns

This reference covers every step type available in SpecQL actions, organized by category with examples and use cases.

## 🎯 Step Syntax

All steps follow this pattern:

```yaml
steps:
  - step_type: parameters
    option1: value1
    option2: value2
```

## 🔍 Core Steps (Universal AST)

### validate
**Validate data and business rules**

```yaml
- validate: status = 'lead'
  error: "not_a_lead"

- validate: email IS NOT NULL
  error: "email_required"

- validate: age >= 18
  error: "must_be_adult"

- validate: email MATCHES "^[^@]+@[^@]+\\.[^@]+$"
  error: "invalid_email"
```

**Options**:
- `error`: Error code for failed validation

### if
**Conditional execution**

```yaml
- if: status = 'lead'
  then:
    - update: Contact SET qualified_at = NOW()
  else:
    - validate: false
      error: "already_qualified"
```

**Options**:
- `then`: Steps to execute if condition is true
- `else`: Steps to execute if condition is false

### insert
**Create new records**

```yaml
- insert: Contact

- insert: Contact
  values:
    email: $email
    status: 'lead'
```

**Options**:
- `values`: Override default field values

### update
**Modify existing records**

```yaml
- update: Contact SET status = 'qualified'

- update: Contact SET
    status: 'qualified'
    qualified_at: NOW()
    qualified_by: caller.id
```

### delete
**Remove records (soft delete)**

```yaml
- delete: Contact

- delete: Contact
  hard: true  # Physical delete (rare)
```

**Options**:
- `hard`: Perform physical delete instead of soft delete

### call
**Invoke other actions**

```yaml
- call: notify_customer
  args:
    message: "Order confirmed"

- call: crm.create_contact
  args:
    email: $email
```

**Options**:
- `args`: Arguments to pass to called action

### notify
**Send notifications**

```yaml
- notify: owner(email, "Contact qualified")

- notify: admin(email, "System alert")
  template: "alert_template"
  priority: "high"
```

**Options**:
- `template`: Notification template to use
- `priority`: Notification priority level

### foreach
**Iterate over collections**

```yaml
- foreach: items
  as: item
  steps:
    - validate: item.quantity > 0
    - update: Inventory SET quantity = quantity - item.quantity
```

**Options**:
- `as`: Variable name for current item
- `steps`: Steps to execute for each item

## 🔧 Extended Steps (PostgreSQL Implementation)

### partial_update
**Selective field updates**

```yaml
- partial_update: Contact
  fields: [email, phone]
  values:
    email: $new_email
    phone: $new_phone
```

**Options**:
- `fields`: Fields to update
- `values`: New values for fields

### duplicate_check
**Prevent duplicate records**

```yaml
- duplicate_check: Contact
  fields: [email]
  error: "email_already_exists"

- duplicate_check: Contact
  fields: [email, company]
  scope: "active_only"
  error: "contact_already_exists"
```

**Options**:
- `fields`: Fields to check for uniqueness
- `scope`: Scope of uniqueness check
- `error`: Error code for duplicates

### refresh_table_view
**Update materialized views**

```yaml
- refresh_table_view: contact_summary

- refresh_table_view: sales_report
  concurrently: true
```

**Options**:
- `concurrently`: Refresh without blocking reads

### call_service
**External service integration**

```yaml
- call_service: email_service
  method: "send"
  args:
    to: $email
    subject: "Welcome"
    body: $message

- call_service: payment_processor
  method: "charge"
  args:
    amount: $amount
    card: $card_token
```

**Options**:
- `method`: Service method to call
- `args`: Arguments for service call

### aggregate
**Data aggregation operations**

```yaml
- aggregate: sales_summary
  group_by: [month, product]
  measures:
    total_sales: SUM(amount)
    order_count: COUNT(*)

- aggregate: inventory_levels
  measures:
    total_value: SUM(quantity * price)
    low_stock_count: COUNT(CASE WHEN quantity < 10 THEN 1 END)
```

**Options**:
- `group_by`: Grouping dimensions
- `measures`: Aggregation calculations

### call_function
**Direct database function calls**

```yaml
- call_function: calculate_tax
  args: [$amount, $tax_rate]
  result: tax_amount

- call_function: generate_uuid
  result: new_id
```

**Options**:
- `args`: Function arguments
- `result`: Variable to store result

### cte
**Common Table Expressions**

```yaml
- cte: active_contacts AS (
    SELECT * FROM crm.tb_contact
    WHERE deleted_at IS NULL AND status = 'active'
  )
  steps:
    - validate: EXISTS(SELECT 1 FROM active_contacts WHERE email = $email)
      error: "email_not_found"
```

**Options**:
- CTE definition as SQL
- `steps`: Steps that can reference the CTE

### declare
**Variable declarations**

```yaml
- declare:
    total_amount: 0
    item_count: 0
    discount_rate: 0.1

- declare:
    user_data: SELECT * FROM users WHERE id = $user_id
```

**Options**:
- Variable name: value pairs
- Support for scalar values and query results

### exception_handling
**Error handling blocks**

```yaml
- exception_handling:
    try:
      - call_service: payment_processor
      - update: Order SET status = 'paid'
    catch:
      - update: Order SET status = 'payment_failed'
      - notify: admin(email, "Payment processing failed")
    finally:
      - log: "Payment attempt completed"
```

**Options**:
- `try`: Steps to attempt
- `catch`: Steps to execute on error
- `finally`: Steps to always execute

### for_query
**Query-based iteration**

```yaml
- for_query: SELECT * FROM pending_orders WHERE status = 'processing'
  as: order
  steps:
    - call: process_order
      args:
        order_id: order.id
```

**Options**:
- `as`: Variable name for current row
- `steps`: Steps to execute for each row

### json_build
**JSON object construction**

```yaml
- json_build: contact_data
  fields:
    id: contact.id
    name: "contact.first_name || ' ' || contact.last_name"
    email: contact.email
    status: contact.status

- json_build: response
  template: "success_response"
  data: contact_data
```

**Options**:
- `fields`: JSON field mappings
- `template`: JSON template to use

### return_early
**Premature return from action**

```yaml
- validate: status = 'cancelled'
- return_early:
    success: false
    message: "Order already cancelled"
    code: "already_cancelled"

- validate: inventory < quantity
- return_early:
    success: false
    message: "Insufficient inventory"
    data:
      available: inventory
      requested: quantity
```

**Options**:
- `success`: Success flag
- `message`: Response message
- `code`: Error code
- `data`: Additional response data

### subquery
**Subquery operations**

```yaml
- subquery: related_contacts
  sql: |
    SELECT * FROM crm.tb_contact
    WHERE company_id = $company_id
    AND deleted_at IS NULL

- validate: (SELECT COUNT(*) FROM related_contacts) > 0
  error: "no_contacts_found"
```

**Options**:
- `sql`: Subquery SQL definition

### switch
**Multi-condition branching**

```yaml
- switch: order_status
  cases:
    pending:
      - update: Order SET processing_at = NOW()
    processing:
      - validate: payment_received = true
      - update: Order SET shipped_at = NOW()
    shipped:
      - update: Order SET delivered_at = NOW()
  default:
    - validate: false
      error: "invalid_status_transition"
```

**Options**:
- `cases`: Status-value to steps mapping
- `default`: Default case steps

### while
**Conditional loops**

```yaml
- declare: counter: 0
- while: counter < 5
  steps:
    - call: process_batch
    - declare: counter: counter + 1

- while: EXISTS(SELECT 1 FROM queue WHERE status = 'pending')
  steps:
    - call: process_next_item
```

**Options**:
- `steps`: Steps to execute while condition is true

## 🎯 Step Categories Summary

| Category | Steps | Purpose |
|----------|-------|---------|
| **Core** | validate, if, insert, update, delete, call, notify, foreach | Fundamental operations |
| **Data** | partial_update, duplicate_check, aggregate, subquery | Data manipulation |
| **Control** | switch, while, for_query, return_early | Flow control |
| **External** | call_service, call_function, notify | Integration |
| **Advanced** | cte, declare, json_build, exception_handling, refresh_table_view | Complex operations |

## 🚀 Best Practices

### Step Ordering
1. **Validation first** - Check conditions before actions
2. **Data operations** - Perform core business logic
3. **External calls** - Notify other systems
4. **Error handling** - Plan for failure scenarios

### Error Handling
- Use specific error codes
- Provide meaningful messages
- Consider rollback scenarios
- Log important operations

### Performance
- Minimize database round trips
- Use CTEs for complex queries
- Consider bulk operations
- Index frequently queried fields

## 🔍 Common Patterns

### CRUD Operations
```yaml
- name: create_with_validation
  steps:
    - validate: email IS NOT NULL
    - duplicate_check: User fields: [email]
    - insert: User

- name: update_with_audit
  steps:
    - validate: caller.can_edit_user
    - update: User SET updated_at = NOW(), updated_by = caller.id
    - notify: audit_log("User updated")
```

### Business Workflows
```yaml
- name: process_order
  steps:
    - validate: inventory >= quantity
    - update: Product SET inventory = inventory - quantity
    - insert: Order
    - call_service: shipping_service
    - notify: customer("Order shipped")
```

### Complex Validation
```yaml
- name: approve_loan
  steps:
    - validate: credit_score >= 700
    - validate: debt_to_income < 0.4
    - validate: employment_years >= 2
    - switch: risk_level
      cases:
        low: - update: Loan SET approved = true, rate = 0.05
        medium: - update: Loan SET approved = true, rate = 0.08
        high: - return_early: {success: false, message: "Risk too high"}
```

## 📚 Related Topics

- **[Validation Guide](validation.md)** - Detailed validation patterns
- **[Error Handling Guide](error_handling.md)** - Exception management
- **[Authorization Guide](authorization.md)** - Permission systems
- **[YAML Reference](../../03_reference/yaml/step_types.md)** - Complete syntax reference