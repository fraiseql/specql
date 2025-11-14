# Action Syntax Guide

This guide explains how to write actions in SpecQL YAML files for the PrintOptim backend.

## Overview

Actions define the business logic that can be performed on entities. Each action consists of a sequence of steps that are executed in order.

## Basic Structure

```yaml
entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified, customer)

actions:
  - name: create_contact
    steps:
      - validate: email IS NOT NULL, error: missing_email
      - insert: Contact

  - name: update_contact
    steps:
      - validate: contact_id IS NOT NULL, error: missing_id
      - update: Contact SET status = qualified

  - name: delete_contact
    steps:
      - delete: Contact

  - name: qualify_lead
    steps:
      - validate: status = 'lead', error: not_a_lead
      - update: Contact SET status = 'qualified'
      - notify: email to owner with template "lead_qualified"
```

## Action Types

### CRUD Actions (Automatic)

The system automatically recognizes these patterns:

- `create_*` - Creates new records
- `update_*` - Updates existing records
- `delete_*` - Soft deletes records

### Custom Actions

Any action name that doesn't match CRUD patterns is treated as a custom business action:

- `qualify_lead`
- `send_quote`
- `process_payment`
- `schedule_followup`

## Step Types

### validate

Validates conditions before proceeding.

```yaml
- validate: email MATCHES email_pattern, error: invalid_email
- validate: status IN ('lead', 'qualified'), error: invalid_status
```

### insert

Inserts a new record.

```yaml
- insert: Contact
```

### update

Updates an existing record.

```yaml
- update: Contact SET status = 'qualified'
- update: Contact SET last_contacted = NOW()
```

### delete

Soft deletes a record.

```yaml
- delete: Contact
```

### if

Conditional execution.

```yaml
- if: status = 'qualified'
  then:
    - notify: email to sales_team
  else:
    - notify: email to lead_nurture
```

### foreach

Iterate over collections.

```yaml
- foreach: item in related_orders
  steps:
    - update: Order SET processed = true
```

### call

Call another function.

```yaml
- call: send_notification with channel='email', template='welcome'
```

### notify

Send notifications.

```yaml
- notify: email to user with template "order_confirmed"
- notify: webhook to external_system
```

## Validation Rules

### Required Fields

```yaml
fields:
  email: text  # nullable: false is default
  name: text?
   # Adding ? makes it nullable
```

### Field Types

- `text` - String fields
- `email` - Email with validation
- `phoneNumber` - Phone with validation
- `url` - URL with validation
- `integer` - Whole numbers
- `decimal` - Decimal numbers
- `boolean` - True/false
- `date` - Date only
- `datetime` - Date and time
- `enum(value1, value2, value3)` - Fixed set of values

### References

```yaml
fields:
  company: ref(Company)  # References another entity
  manager: ref(User)?    # Optional reference
```

## Error Handling

Actions automatically handle these error conditions:

- **Validation failures**: Return structured error with field and message
- **Foreign key violations**: Check references exist and belong to tenant
- **Unique constraints**: Prevent duplicate values
- **Permission issues**: Ensure user has access to tenant data

## Examples

### Complete Contact Management

```yaml
entity: Contact
schema: crm
fields:
  first_name: text
  last_name: text
  email: email
  phone: phoneNumber?
  status: enum(lead, qualified, customer, inactive)
  company: ref(Company)?
  owner: ref(User)

actions:
  - name: create_contact
    steps:
      - validate: email IS NOT NULL, error: missing_email
      - validate: owner IS NOT NULL, error: missing_owner
      - insert: Contact

  - name: update_contact
    steps:
      - validate: contact_id IS NOT NULL, error: missing_id
      - update: Contact

  - name: qualify_lead
    steps:
      - validate: status = 'lead', error: not_a_lead
      - update: Contact SET status = 'qualified'
      - notify: email to owner with template "lead_qualified"

  - name: assign_to_sales_rep
    steps:
      - validate: contact_id IS NOT NULL, error: missing_id
      - validate: sales_rep_id IS NOT NULL, error: missing_sales_rep
      - update: Contact SET owner = sales_rep_id
      - notify: email to sales_rep with template "new_assignment"
```

## Best Practices

1. **Use descriptive action names**: `qualify_lead` vs `update_status`
2. **Validate early**: Put validations at the start of actions
3. **Handle errors gracefully**: Provide clear error messages
4. **Keep actions focused**: One action should do one business operation
5. **Use references**: Model relationships between entities
6. **Document complex logic**: Add comments for non-obvious steps

## Generated Code

Each action generates:

- **App layer function**: JSON input validation and conversion
- **Core layer function**: Business logic with security
- **Composite types**: Type-safe input/output structures
- **Audit logging**: All mutations are logged
- **Multi-tenant isolation**: Automatic tenant filtering

The generated functions follow the Trinity pattern for scalable data access.