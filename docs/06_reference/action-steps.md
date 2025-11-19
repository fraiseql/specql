# Action Steps Reference

> **Complete reference for all SpecQL action step types—the building blocks of business logic**

## Overview

Actions in SpecQL are composed of **steps**—declarative instructions that compile to PL/pgSQL. Each step type handles a specific operation: validation, data manipulation, conditional logic, or external interactions.

**Think of it as**: SQL meets imperative programming, but declarative and type-safe.

---

## Step Types

### Quick Reference

| Step Type | Purpose | Example |
|-----------|---------|---------|
| `validate` | Assert conditions | `validate: status = 'draft'` |
| `if` | Conditional branching | `if: total > 1000` |
| `insert` | Create records | `insert: Invoice SET ...` |
| `update` | Modify records | `update: Contract SET status = 'approved'` |
| `delete` | Remove records | `delete: ContractItem WHERE ...` |
| `call` | Invoke functions | `call: send_notification(...)` |
| `notify` | PostgreSQL NOTIFY | `notify: contract_approved` |
| `foreach` | Loop over arrays | `foreach: item IN items` |
| `refresh` | Materialized views | `refresh: contract_projection` |

---

## 1. Validate Step

**Purpose**: Assert business rules and pre-conditions.

### Syntax

```yaml
- validate: <expression>
  error: <error_code>  # optional, default: "validation_failed"
  message: <error_message>  # optional
```

### Examples

#### Simple Field Validation

```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
        message: "Contact must be a lead to qualify"
```

**Generated PL/pgSQL**:
```sql
-- Validate: status = 'lead'
SELECT status INTO v_status
FROM crm.tb_contact
WHERE pk_contact = v_pk;

IF v_status != 'lead' THEN
    v_result.status := 'error';
    v_result.code := 'not_a_lead';
    v_result.message := 'Contact must be a lead to qualify';
    RETURN v_result;
END IF;
```

#### Multi-Field Validation

```yaml
- validate: status = 'draft' AND total_value > 0
  error: "invalid_contract_state"
```

**Generated PL/pgSQL**:
```sql
SELECT status, total_value INTO v_status, v_total_value
FROM crm.tb_contract
WHERE pk_contract = v_pk;

IF NOT (v_status = 'draft' AND v_total_value > 0) THEN
    v_result.status := 'error';
    v_result.code := 'invalid_contract_state';
    RETURN v_result;
END IF;
```

#### Rich Type Validation

```yaml
- validate: email IS VALID  # Checks email format
  error: "invalid_email"

- validate: phone_number IS VALID  # Checks phone format
  error: "invalid_phone"
```

#### Relationship Validation

```yaml
- validate: customer_org EXISTS
  error: "customer_not_found"
  message: "Customer organization must exist"

- validate: NOT EXISTS (SELECT 1 FROM contracts WHERE customer_org = $customer_org AND status = 'active')
  error: "duplicate_active_contract"
```

### Validation Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=`, `!=` | Equality | `status = 'draft'` |
| `<`, `>`, `<=`, `>=` | Comparison | `total_value > 1000` |
| `IS NULL`, `IS NOT NULL` | Nullability | `deleted_at IS NULL` |
| `AND`, `OR`, `NOT` | Logic | `status = 'draft' AND total > 0` |
| `IN`, `NOT IN` | Membership | `status IN ('draft', 'pending')` |
| `EXISTS`, `NOT EXISTS` | Subqueries | `customer_org EXISTS` |
| `IS VALID` | Rich type validation | `email IS VALID` |
| `LIKE`, `ILIKE` | Pattern matching | `name LIKE 'Acme%'` |

---

## 2. If Step

**Purpose**: Conditional execution of steps.

### Syntax

```yaml
- if: <condition>
  then:
    - <steps...>
  else:  # optional
    - <steps...>
```

### Examples

#### Simple Conditional

```yaml
actions:
  - name: approve_contract
    steps:
      - if: total_value > 10000
        then:
          - validate: manager_approval EXISTS
            error: "manager_approval_required"
          - update: Contract SET approved_by = $manager_id
        else:
          - update: Contract SET status = 'auto_approved'
```

**Generated PL/pgSQL**:
```sql
SELECT total_value INTO v_total_value
FROM crm.tb_contract
WHERE pk_contract = v_pk;

IF v_total_value > 10000 THEN
    -- Manager approval required
    SELECT EXISTS (
        SELECT 1 FROM approvals
        WHERE contract_fk = v_pk AND approver_role = 'manager'
    ) INTO v_manager_approval_exists;

    IF NOT v_manager_approval_exists THEN
        v_result.status := 'error';
        v_result.code := 'manager_approval_required';
        RETURN v_result;
    END IF;

    UPDATE crm.tb_contract
    SET approved_by = v_manager_id
    WHERE pk_contract = v_pk;
ELSE
    UPDATE crm.tb_contract
    SET status = 'auto_approved'
    WHERE pk_contract = v_pk;
END IF;
```

#### Nested Conditionals

```yaml
- if: status = 'draft'
  then:
    - if: total_value > 5000
      then:
        - validate: executive_approval EXISTS
      else:
        - validate: manager_approval EXISTS
    - update: Contract SET status = 'approved'
```

#### Multiple Conditions

```yaml
- if: status = 'draft' AND total_value > 0 AND customer_org EXISTS
  then:
    - update: Contract SET status = 'pending_review'
```

---

## 3. Insert Step

**Purpose**: Create new records in database tables.

### Syntax

```yaml
- insert: <Entity> SET <field> = <value>, <field> = <value>, ...
  return_id: <variable_name>  # optional
```

### Examples

#### Simple Insert

```yaml
actions:
  - name: create_invoice
    steps:
      - insert: Invoice SET
          contract = $contract_id,
          total_amount = $total,
          status = 'draft'
        return_id: invoice_id
```

**Generated PL/pgSQL**:
```sql
-- Resolve FK: contract (UUID → INTEGER)
SELECT pk_contract INTO v_contract_fk
FROM crm.tb_contract
WHERE id = v_contract_id;

-- Insert
INSERT INTO billing.tb_invoice (
    contract_fk,
    total_amount,
    status,
    created_by
) VALUES (
    v_contract_fk,
    v_total,
    'draft',
    user_id
) RETURNING pk_invoice INTO v_invoice_id;
```

#### Insert with Multiple Records

```yaml
- foreach: item IN $items
  steps:
    - insert: InvoiceItem SET
        invoice = $invoice_id,
        product = $item.product_id,
        quantity = $item.quantity,
        unit_price = $item.price
```

#### Insert with Computed Values

```yaml
- insert: ContractEvent SET
    contract = $contract_id,
    event_type = 'approved',
    event_timestamp = NOW(),
    event_data = jsonb_build_object('approved_by', $user_id, 'total', $total_value)
```

#### Trinity Pattern Auto-Resolution

All `ref(Entity)` fields are **automatically resolved** from UUID to INTEGER:

```yaml
# YAML
- insert: Contract SET
    customer_org = $customer_uuid  # UUID

# Generated SQL
SELECT pk_organization INTO v_customer_org_fk
FROM crm.tb_organization
WHERE id = v_customer_uuid;  -- UUID → INTEGER

INSERT INTO crm.tb_contract (customer_org_fk, ...)
VALUES (v_customer_org_fk, ...);  -- INTEGER FK
```

---

## 4. Update Step

**Purpose**: Modify existing records.

### Syntax

```yaml
- update: <Entity> SET <field> = <value>, ... WHERE <condition>
```

### Examples

#### Simple Update

```yaml
actions:
  - name: approve_contract
    steps:
      - update: Contract SET
          status = 'approved',
          approved_at = NOW(),
          approved_by = $user_id
```

**Generated PL/pgSQL**:
```sql
UPDATE crm.tb_contract
SET
    status = 'approved',
    approved_at = NOW(),
    approved_by = v_user_id,
    updated_at = NOW(),  -- Auto-added
    updated_by = user_id  -- Auto-added
WHERE pk_contract = v_pk;
```

#### Conditional Update

```yaml
- update: Contract SET status = 'expired'
  WHERE end_date < CURRENT_DATE AND status = 'active'
```

**Generated PL/pgSQL**:
```sql
UPDATE crm.tb_contract
SET
    status = 'expired',
    updated_at = NOW(),
    updated_by = user_id
WHERE pk_contract = v_pk
  AND end_date < CURRENT_DATE
  AND status = 'active';
```

#### Computed Updates

```yaml
- update: Contract SET
    total_value = (SELECT SUM(total_price) FROM contract_items WHERE contract_fk = v_pk),
    item_count = (SELECT COUNT(*) FROM contract_items WHERE contract_fk = v_pk)
```

#### Increment/Decrement

```yaml
- update: Department SET
    used_budget = used_budget + $contract_total,
    contract_count = contract_count + 1
```

### Auto-Updated Fields

The following fields are **automatically updated** (no need to specify):

- `updated_at` → `NOW()`
- `updated_by` → `user_id` (from action parameter)

---

## 5. Delete Step

**Purpose**: Remove records (soft or hard delete).

### Syntax

```yaml
- delete: <Entity> WHERE <condition>
  hard: true  # optional, default: false (soft delete)
```

### Examples

#### Soft Delete (Default)

```yaml
actions:
  - name: cancel_contract
    steps:
      - delete: Contract
```

**Generated PL/pgSQL**:
```sql
UPDATE crm.tb_contract
SET
    deleted_at = NOW(),
    deleted_by = user_id
WHERE pk_contract = v_pk;
```

#### Hard Delete

```yaml
- delete: Contract
  hard: true
```

**Generated PL/pgSQL**:
```sql
DELETE FROM crm.tb_contract
WHERE pk_contract = v_pk;
```

#### Conditional Delete

```yaml
- delete: ContractItem WHERE quantity = 0
```

**Generated PL/pgSQL**:
```sql
UPDATE crm.tb_contract_item
SET
    deleted_at = NOW(),
    deleted_by = user_id
WHERE contract_fk = v_pk
  AND quantity = 0;
```

#### Cascade Delete

```yaml
actions:
  - name: delete_contract
    steps:
      # Delete contract items first
      - delete: ContractItem WHERE contract = $contract_id

      # Then delete contract
      - delete: Contract
```

---

## 6. Call Step

**Purpose**: Invoke other functions or actions.

### Syntax

```yaml
- call: <function_name>(<args...>)
  return: <variable_name>  # optional
```

### Examples

#### Call Action

```yaml
actions:
  - name: approve_and_invoice
    steps:
      - call: approve_contract(contract_id = $contract_id)

      - call: create_invoice(
          contract_id = $contract_id,
          total_amount = $total_value
        )
        return: invoice_id
```

**Generated PL/pgSQL**:
```sql
-- Call approve_contract
PERFORM crm.approve_contract(v_user_id, jsonb_build_object('contract_id', v_contract_id));

-- Call create_invoice with return value
SELECT billing.create_invoice(
    v_user_id,
    jsonb_build_object(
        'contract_id', v_contract_id,
        'total_amount', v_total_value
    )
) INTO v_invoice_id;
```

#### Call PostgreSQL Function

```yaml
- call: pg_notify('contract_approved', json_build_object('id', $contract_id))
```

#### Call stdlib Action

```yaml
- call: stdlib.send_email(
    to = $customer_email,
    subject = 'Contract Approved',
    body = 'Your contract has been approved.'
  )
```

---

## 7. Notify Step

**Purpose**: Send PostgreSQL NOTIFY events.

### Syntax

```yaml
- notify: <channel>
  payload: <json_object>  # optional
```

### Examples

#### Simple Notification

```yaml
actions:
  - name: approve_contract
    steps:
      - update: Contract SET status = 'approved'

      - notify: contract_approved
        payload:
          contract_id: $contract_id
          approved_by: $user_id
```

**Generated PL/pgSQL**:
```sql
PERFORM pg_notify(
    'contract_approved',
    json_build_object(
        'contract_id', v_contract_id,
        'approved_by', v_user_id
    )::text
);
```

#### Multiple Notifications

```yaml
- notify: contract_status_changed
  payload:
    old_status: $old_status
    new_status: 'approved'

- notify: user_action
  payload:
    user_id: $user_id
    action: 'contract_approval'
```

---

## 8. Foreach Step

**Purpose**: Iterate over arrays and perform operations.

### Syntax

```yaml
- foreach: <item_var> IN <array>
  steps:
    - <steps...>
```

### Examples

#### Bulk Insert

```yaml
actions:
  - name: create_invoice_items
    steps:
      - foreach: item IN $items
        steps:
          - insert: InvoiceItem SET
              invoice = $invoice_id,
              product = $item.product_id,
              quantity = $item.quantity,
              unit_price = $item.price,
              total_price = $item.quantity * $item.price
```

**Generated PL/pgSQL**:
```sql
FOR v_item IN SELECT * FROM jsonb_array_elements(v_items)
LOOP
    -- Resolve product FK
    SELECT pk_product INTO v_product_fk
    FROM catalog.tb_product
    WHERE id = (v_item->>'product_id')::uuid;

    -- Insert item
    INSERT INTO billing.tb_invoice_item (
        invoice_fk,
        product_fk,
        quantity,
        unit_price,
        total_price
    ) VALUES (
        v_invoice_fk,
        v_product_fk,
        (v_item->>'quantity')::integer,
        (v_item->>'price')::numeric,
        (v_item->>'quantity')::integer * (v_item->>'price')::numeric
    );
END LOOP;
```

#### Conditional Foreach

```yaml
- foreach: item IN $items
  steps:
    - if: $item.quantity > 0
      then:
        - insert: OrderItem SET ...
      else:
        - notify: invalid_item
          payload:
            product_id: $item.product_id
```

#### Nested Foreach

```yaml
- foreach: order IN $orders
  steps:
    - insert: Order SET ...
      return_id: order_id

    - foreach: item IN $order.items
      steps:
        - insert: OrderItem SET order = $order_id, ...
```

---

## 9. Refresh Step

**Purpose**: Refresh materialized views or table views.

### Syntax

```yaml
- refresh: <view_name>
  concurrently: true  # optional, default: true
```

### Examples

#### Refresh Materialized View

```yaml
actions:
  - name: update_contract
    steps:
      - update: Contract SET ...

      - refresh: contract_projection
```

**Generated PL/pgSQL**:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY crm.contract_projection;
```

#### Refresh Multiple Views

```yaml
- refresh: contract_projection
- refresh: invoice_summary
- refresh: customer_statistics
```

#### Non-Concurrent Refresh

```yaml
- refresh: analytics_daily
  concurrently: false  # Faster but locks view
```

---

## Step Composition Patterns

### Sequential Steps

```yaml
actions:
  - name: approve_contract
    steps:
      - validate: status = 'draft'
      - validate: total_value > 0
      - update: Contract SET status = 'approved'
      - notify: contract_approved
```

### Conditional Workflow

```yaml
actions:
  - name: process_contract
    steps:
      - if: total_value > 10000
        then:
          - validate: executive_approval EXISTS
          - call: create_invoice_immediately()
        else:
          - call: queue_for_processing()

      - update: Contract SET processed_at = NOW()
```

### Error Handling

```yaml
actions:
  - name: safe_update
    steps:
      - validate: status = 'draft'
        error: "not_draft"

      - if: total_value > budget
        then:
          - validate: FALSE
            error: "exceeds_budget"
            message: "Contract exceeds available budget"

      - update: Contract SET status = 'approved'
```

### Multi-Entity Coordination

```yaml
actions:
  - name: approve_and_bill
    steps:
      # Approve contract
      - update: Contract SET status = 'approved'

      # Create invoice
      - insert: Invoice SET
          contract = $contract_id,
          total_amount = $total_value
        return_id: invoice_id

      # Create invoice items
      - foreach: item IN $items
        steps:
          - insert: InvoiceItem SET
              invoice = $invoice_id,
              product = $item.product_id,
              quantity = $item.quantity

      # Refresh projections
      - refresh: contract_projection
      - refresh: invoice_summary
```

---

## Advanced Features

### Variable Declarations

Steps can reference variables declared earlier:

```yaml
steps:
  - insert: Invoice SET ...
    return_id: invoice_id  # Declare variable

  - insert: InvoiceItem SET invoice = $invoice_id  # Use variable
```

### Input Parameters

Actions receive `user_id` (UUID) and `input_data` (JSONB):

```yaml
# Called as: app.create_contract(user_id, jsonb)

actions:
  - name: create_contract
    steps:
      - validate: $input_data.total_value > 0  # Access input

      - insert: Contract SET
          customer_org = $input_data.customer_id,  # Use input
          total_value = $input_data.total_value
```

### Return Values

Actions return `app.mutation_result`:

```sql
TYPE app.mutation_result AS (
    status TEXT,              -- 'success' or 'error'
    pk INTEGER,               -- Entity primary key
    object_data JSONB,        -- Complete entity object
    metadata JSONB            -- _meta with impact info
);
```

### Error Codes

Standard error codes for `validate` steps:

| Code | Meaning |
|------|---------|
| `validation_failed` | Generic validation error |
| `not_found` | Entity not found |
| `duplicate` | Duplicate record |
| `invalid_state` | Invalid entity state |
| `permission_denied` | Authorization failure |
| `business_rule_violation` | Business logic violated |

---

## Step Compilation Details

### Trinity Pattern Resolution

All `ref(Entity)` fields undergo **automatic FK resolution**:

```yaml
# YAML
- insert: Contract SET customer_org = $customer_uuid

# Compiled SQL
SELECT pk_organization INTO v_customer_org_fk
FROM crm.tb_organization
WHERE id = v_customer_uuid;  -- UUID lookup

INSERT INTO crm.tb_contract (customer_org_fk, ...)
VALUES (v_customer_org_fk, ...);  -- INTEGER FK
```

### Audit Field Injection

Audit fields are **automatically populated**:

**Insert**:
- `created_at` → `NOW()`
- `created_by` → `user_id`

**Update**:
- `updated_at` → `NOW()`
- `updated_by` → `user_id`

**Delete** (soft):
- `deleted_at` → `NOW()`
- `deleted_by` → `user_id`

### Type Coercion

Input values from JSONB are **coerced to correct types**:

```sql
-- Integer
(input_data->>'quantity')::integer

-- Numeric/Decimal
(input_data->>'total_value')::numeric

-- UUID
(input_data->>'customer_id')::uuid

-- Date
(input_data->>'start_date')::date

-- Boolean
(input_data->>'is_active')::boolean
```

---

## Performance Considerations

### Minimize Round-Trips

**❌ Bad**: Multiple queries
```yaml
- validate: status = 'draft'  # Query 1
- validate: total > 0         # Query 2
- validate: customer EXISTS   # Query 3
```

**✅ Good**: Single compound validation
```yaml
- validate: status = 'draft' AND total > 0 AND customer EXISTS
```

### Use Foreach for Bulk Operations

**❌ Bad**: Individual inserts (multiple action calls)
```yaml
# Calling create_item 100 times
```

**✅ Good**: Foreach loop (single transaction)
```yaml
- foreach: item IN $items
  steps:
    - insert: Item SET ...
```

### Conditional Refreshes

**❌ Bad**: Always refresh
```yaml
- update: Contract SET ...
- refresh: contract_projection  # Expensive!
```

**✅ Good**: Conditional refresh
```yaml
- update: Contract SET ...
- if: significant_change
  then:
    - refresh: contract_projection
```

---

## Testing Action Steps

### Unit Testing

Test individual steps in isolation:

```sql
-- Test validate step
SELECT crm.validate_contract_status(
    gen_random_uuid(),
    '{"contract_id": "..."}'::jsonb
);
```

### Integration Testing

Test complete action workflows:

```bash
# Generate and test
specql generate entities/contract.yaml
specql test --entity contract --action approve_contract
```

### Validation Testing

Test business rule violations:

```sql
-- Should fail validation
SELECT crm.approve_contract(
    gen_random_uuid(),
    '{"contract_id": "...", "status": "expired"}'::jsonb
);
-- Expect: {status: 'error', code: 'invalid_state'}
```

---

## Summary

### Step Types Overview

| Category | Steps | Use Cases |
|----------|-------|-----------|
| **Control Flow** | `validate`, `if` | Business rules, conditionals |
| **Data Manipulation** | `insert`, `update`, `delete` | CRUD operations |
| **Composition** | `call`, `foreach` | Reusability, bulk operations |
| **Integration** | `notify`, `refresh` | External systems, caching |

### Key Principles

1. **Declarative Over Imperative**: Describe *what*, not *how*
2. **Type-Safe**: Automatic type coercion and validation
3. **Trinity-Aware**: Automatic UUID ↔ INTEGER resolution
4. **Audit-Friendly**: Automatic audit field population
5. **Transactional**: All steps execute in single transaction

### Best Practices

- ✅ Use `validate` for all pre-conditions
- ✅ Prefer compound validations over multiple steps
- ✅ Use `foreach` for bulk operations
- ✅ Always handle error cases with clear error codes
- ✅ Minimize database round-trips

### Next Steps

- [Action Patterns Guide](../07_stdlib/action-patterns.md) - Pre-built patterns
- [YAML Syntax Reference](yaml-syntax.md) - Complete syntax
- [CLI Commands](cli-commands.md) - CLI usage

---

**Master these action steps to unlock declarative, production-ready business logic generation with SpecQL.**

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Coverage**: Complete action steps reference (9 step types)
