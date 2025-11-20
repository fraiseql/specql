# Action Steps Reference

> **Status**: 🚧 Documentation in Progress
>
> This page provides a quick reference. Comprehensive documentation coming soon!

## Overview

SpecQL actions are composed of steps that define business logic. This reference documents all available step types with syntax and examples.

## Quick Reference

### Core Steps

| Step Type | Purpose | Syntax |
|-----------|---------|--------|
| `validate` | Assert conditions | `validate: <condition>, error: "<message>"` |
| `update` | Update records | `update: Entity SET field = value WHERE condition` |
| `insert` | Create records | `insert: Entity { field: value, ... }` |
| `call` | Invoke function | `call: function_name, args: { param: value }` |
| `notify` | Send notification | `notify: event_name, to: $email, data: {...}` |
| `if` | Conditional logic | `if: <condition>` + `then:` + `else:` |
| `foreach` | Iterate collection | `foreach: item in $collection` + `do:` |
| `return` | Return value | `return: "Success message"` |

## Detailed Step Types

### validate

Assert a condition is true, otherwise raise an error.

```yaml
steps:
  - validate: status = 'lead'
    error: "Only leads can be qualified"

  - validate: email IS NOT NULL
    error: "Email is required"

  - validate: amount > 0
    error: "Amount must be positive"
```

**SQL Generated**:
```sql
IF NOT (status = 'lead') THEN
  RAISE EXCEPTION 'Only leads can be qualified' USING ERRCODE = 'P0001';
END IF;
```

### update

Update one or more records.

```yaml
steps:
  - update: Contact SET status = 'qualified' WHERE pk_contact = $pk

  - update: Order SET
      status = 'shipped',
      shipped_at = now()
    WHERE pk_order = $pk
```

**SQL Generated**:
```sql
UPDATE crm.tb_contact
SET status = 'qualified', updated_at = now()
WHERE pk_contact = v_pk_contact;
```

### insert

Create new records.

```yaml
steps:
  - insert: OrderLine {
      fk_order: $pk_order,
      product_name: $product,
      quantity: $qty,
      price: $price
    }
```

**SQL Generated**:
```sql
INSERT INTO crm.tb_order_line (
  fk_order, product_name, quantity, price
) VALUES (
  v_pk_order, v_product, v_qty, v_price
);
```

### call

Invoke a PostgreSQL function.

```yaml
steps:
  - call: calculate_discount
    args:
      customer_id: $pk_contact
      order_total: $total
```

**SQL Generated**:
```sql
v_discount := crm.calculate_discount(
  p_customer_id => v_pk_contact,
  p_order_total => v_total
);
```

### notify

Send notifications (integrates with PostgreSQL NOTIFY/LISTEN).

```yaml
steps:
  - notify: lead_qualified
    to: $email
    data:
      contact_id: $pk_contact
      qualified_at: now()
```

**SQL Generated**:
```sql
PERFORM pg_notify('lead_qualified', json_build_object(
  'email', v_email,
  'contact_id', v_pk_contact,
  'qualified_at', now()
)::text);
```

### if/then/else

Conditional branching.

```yaml
steps:
  - if: amount > 1000
    then:
      - update: Order SET requires_approval = true
      - notify: approval_required, to: 'manager@example.com'
    else:
      - update: Order SET status = 'approved'
```

**SQL Generated**:
```sql
IF v_amount > 1000 THEN
  UPDATE crm.tb_order SET requires_approval = true WHERE pk_order = v_pk_order;
  PERFORM pg_notify('approval_required', ...);
ELSE
  UPDATE crm.tb_order SET status = 'approved' WHERE pk_order = v_pk_order;
END IF;
```

### foreach

Iterate over collections.

```yaml
steps:
  - foreach: item in $order_lines
    do:
      - validate: item.quantity > 0
        error: "Quantity must be positive"

      - insert: OrderLine {
          fk_order: $pk_order,
          product: item.product,
          quantity: item.quantity
        }
```

**SQL Generated**:
```sql
FOR v_item IN SELECT * FROM unnest(v_order_lines) LOOP
  IF NOT (v_item.quantity > 0) THEN
    RAISE EXCEPTION 'Quantity must be positive';
  END IF;

  INSERT INTO crm.tb_order_line (...) VALUES (...);
END LOOP;
```

### return

Return a value from the action.

```yaml
steps:
  - validate: status = 'lead'
  - update: Contact SET status = 'qualified'
  - return: "Lead successfully qualified"
```

**SQL Generated**:
```sql
v_result := app.mutation_result(
  p_status => 'success',
  p_code => 'LEAD_QUALIFIED',
  p_message => 'Lead successfully qualified',
  p_object_data => row_to_json(v_contact)
);
RETURN v_result;
```

## Coming Soon

Full documentation will cover:
- [ ] Advanced condition expressions
- [ ] Variable scoping and references
- [ ] Transaction handling
- [ ] Error propagation
- [ ] Step composition patterns
- [ ] Performance optimization
- [ ] Testing strategies

## Related Documentation

- [Actions Overview](../03_core-concepts/actions.md) - Understanding actions
- [Business YAML](../03_core-concepts/business-yaml.md) - Full YAML syntax
- [Your First Action](../05_guides/your-first-action.md) - Hands-on tutorial
- [Custom Patterns](../07_advanced/custom-patterns.md) - Advanced action patterns

## Expression Syntax

### Variables

```yaml
$pk_contact        # Parameter from function signature
$email             # Field value
$item.quantity     # Nested field access
```

### Conditions

```yaml
status = 'lead'                    # Equality
amount > 100                       # Comparison
email IS NOT NULL                  # Null check
status IN ('lead', 'qualified')    # Set membership
created_at > now() - interval '1 day'  # Time comparison
```

### Field References

```yaml
Entity SET field = value           # Direct assignment
Entity SET field = $variable       # Variable assignment
Entity SET field = other_field + 1 # Expression
```

## Best Practices

### 1. Validate Early
```yaml
steps:
  - validate: all preconditions
  - perform: business logic
```

### 2. Use Transactions
All action steps run in a single transaction automatically.

### 3. Clear Error Messages
```yaml
validate: status = 'lead'
error: "Only leads can be qualified. Current status: {status}"
```

### 4. Atomic Operations
Keep actions focused on a single business operation.

## Questions?

If you need more details:
- Check [Actions Overview](../03_core-concepts/actions.md)
- Review [Your First Action](../05_guides/your-first-action.md)
- See [Custom Patterns](../07_advanced/custom-patterns.md)
- Open an issue on GitHub

---

*Last Updated*: 2025-11-20
