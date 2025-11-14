# SpecQL Actions Guide

**Complete reference for defining business logic with SpecQL actions**

---

## Table of Contents

- [Overview](#overview)
- [Action Basics](#action-basics)
- [Step Types](#step-types)
  - [Validate](#validate-business-rules)
  - [If/Then/Else](#ifthenelse-conditional-logic)
  - [Switch](#switch-multi-way-branching)
  - [Insert](#insert-create-records)
  - [Update](#update-modify-records)
  - [Delete](#delete-remove-records)
  - [Call](#call-function-calls)
  - [Notify](#notify-notifications)
  - [Foreach](#foreach-loops)
- [Advanced Patterns](#advanced-patterns)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)

---

## Overview

**SpecQL actions** define your business logic as declarative workflow steps. The framework automatically handles:

- ✅ **Type validation** - Field types are checked automatically
- ✅ **Permission checks** - Caller authorization via `requires:`
- ✅ **Transaction management** - All steps run in a single transaction
- ✅ **Error handling** - Typed errors with proper status codes
- ✅ **Audit trails** - Automatic logging of all mutations
- ✅ **Event emission** - Events fired for all actions
- ✅ **GraphQL integration** - Actions become mutations automatically

**You focus on**: Business rules, workflows, and domain logic.

---

## Action Basics

### Minimal Action

```yaml
entity: Contact
actions:
  - name: create_contact
    steps:
      - insert: Contact
```

**Generates**:
```sql
CREATE FUNCTION crm.create_contact(
  email TEXT,
  first_name TEXT,
  last_name TEXT
) RETURNS app.mutation_result;
```

### Action with Validation

```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

### Action with Permissions

```yaml
actions:
  - name: delete_contact
    requires: caller.has_permission('delete_contact')
    steps:
      - delete: Contact
```

**Framework automatically**:
- Checks permission before executing
- Returns `permission_denied` error if unauthorized
- Logs permission check in audit trail

---

## Step Types

### Validate (Business Rules)

**Purpose**: Enforce business rules and constraints

**Syntax**:
```yaml
- validate: condition
  error: "error_code"
```

**Examples**:

#### Simple Validation
```yaml
steps:
  - validate: email IS NOT NULL
  - validate: status IN ('lead', 'qualified', 'customer')
  - validate: age >= 18
```

#### Custom Error Codes
```yaml
steps:
  - validate: status = 'lead'
    error: "not_a_lead"

  - validate: phone MATCHES '^\+[1-9]\d{1,14}$'
    error: "invalid_phone_format"
```

#### Complex Conditions
```yaml
steps:
  - validate: start_date <= end_date
    error: "invalid_date_range"

  - validate: NOT EXISTS (
      SELECT 1 FROM crm.tb_contact
      WHERE email = input.email
        AND pk_contact != input.pk_contact
    )
    error: "duplicate_email"
```

#### Multiple Field Validation
```yaml
steps:
  - validate: NOT (order_id IS NOT NULL AND order_data IS NOT NULL)
    error: "conflicting_order_fields"
```

**Generated SQL**:
```sql
IF NOT (status = 'lead') THEN
  RETURN (
    FALSE,
    'not_a_lead',
    'Validation failed: status must be lead',
    NULL,
    NULL
  )::app.mutation_result;
END IF;
```

---

### If/Then/Else (Conditional Logic)

**Purpose**: Conditional execution based on runtime conditions

**Syntax**:
```yaml
- if: condition
  then:
    - step1
    - step2
  else:  # Optional
    - step3
```

**Examples**:

#### Simple Conditional
```yaml
steps:
  - if: status = 'lead'
    then:
      - update: Contact SET lead_score = lead_score + 10
```

#### If/Else
```yaml
steps:
  - if: order_data IS NOT NULL
    then:
      - call: create_order(order_data)
      - set: order_id = result.id
    else:
      - validate: order_id IS NOT NULL
```

#### Nested Conditions
```yaml
steps:
  - if: source_type = 'Product'
    then:
      - if: product.is_available
        then:
          - insert: MachineItem
        else:
          - validate: FALSE
            error: "product_not_available"
```

#### Existence Checks
```yaml
steps:
  - if: EXISTS (
      SELECT 1 FROM crm.tb_company
      WHERE email_domain = extract_domain(input.email)
    )
    then:
      - call: link_contact_to_company(input.email)
```

**Generated SQL**:
```sql
IF (status = 'lead') THEN
  UPDATE crm.tb_contact
  SET lead_score = lead_score + 10
  WHERE pk_contact = v_pk_contact;
END IF;
```

---

### Switch (Multi-Way Branching)

**Purpose**: Multiple conditional branches based on a field value

**Syntax**:
```yaml
- switch: field
  cases:
    value1:
      - steps
    value2:
      - steps
```

**Examples**:

#### Enum Switch
```yaml
steps:
  - switch: source_type
    cases:
      MachineItem:
        - validate: source.fk_machine IS NULL
          error: "machine_item_already_allocated"
        - update: source SET fk_machine = input.machine_id

      ContractItem:
        - fetch: source AS contract_item
        - set: fk_product = contract_item.fk_product
        - insert: MachineItem

      Product:
        - set: fk_product = source_id
        - insert: MachineItem
```

#### Status-Based Workflow
```yaml
steps:
  - switch: status
    cases:
      lead:
        - update: Contact SET lead_score = 50
      qualified:
        - update: Contact SET lead_score = 75
        - notify: sales_team "Lead qualified: {email}"
      customer:
        - update: Contact SET lead_score = 100
        - call: create_welcome_sequence(contact_id)
```

**Generated SQL**:
```sql
CASE v_source_type
  WHEN 'MachineItem' THEN
    -- MachineItem steps
  WHEN 'ContractItem' THEN
    -- ContractItem steps
  WHEN 'Product' THEN
    -- Product steps
END CASE;
```

---

### Insert (Create Records)

**Purpose**: Create new database records

**Syntax**:
```yaml
- insert: Entity
- insert: Entity(field1, field2, ...)
```

**Examples**:

#### Simple Insert
```yaml
steps:
  - insert: Contact
```

**Inserts all fields from action parameters**

#### Explicit Fields
```yaml
steps:
  - insert: Contact(email, first_name, last_name)
```

#### Computed Fields
```yaml
steps:
  - compute: full_name = first_name || ' ' || last_name
  - insert: Contact(email, full_name)
```

#### Nested Insert with Foreign Key
```yaml
steps:
  - insert: Company(name, domain)
  - set: company_id = result.id
  - insert: Contact(email, first_name, last_name, company_id)
```

**Generated SQL**:
```sql
INSERT INTO crm.tb_contact (
  email,
  first_name,
  last_name,
  created_at,
  created_by,
  updated_at,
  updated_by
) VALUES (
  p_email,
  p_first_name,
  p_last_name,
  now(),
  auth.uid(),  -- Framework provides
  now(),
  auth.uid()
) RETURNING pk_contact, id, identifier INTO v_pk_contact, v_id, v_identifier;
```

**Framework automatically adds**:
- `created_at = now()`
- `created_by = auth.uid()`
- `updated_at = now()`
- `updated_by = auth.uid()`

---

### Update (Modify Records)

**Purpose**: Modify existing records

**Syntax**:
```yaml
- update: Entity SET field = value
- update: Entity SET field1 = value1, field2 = value2
```

**Examples**:

#### Simple Update
```yaml
steps:
  - update: Contact SET status = 'qualified'
```

#### Multiple Fields
```yaml
steps:
  - update: Contact SET
      status = 'customer',
      lead_score = 100,
      qualified_at = now()
```

#### Conditional Update
```yaml
steps:
  - if: lead_score > 80
    then:
      - update: Contact SET status = 'qualified'
```

#### Update with Expression
```yaml
steps:
  - update: Contact SET
      lead_score = lead_score + 10,
      last_activity = now()
```

#### Computed Update
```yaml
steps:
  - compute: new_score = calculate_lead_score(email, phone, company_id)
  - update: Contact SET lead_score = new_score
```

**Generated SQL**:
```sql
UPDATE crm.tb_contact
SET
  status = 'qualified',
  updated_at = now(),  -- Framework adds
  updated_by = auth.uid()  -- Framework adds
WHERE pk_contact = v_pk_contact;
```

**Framework automatically**:
- Updates `updated_at = now()`
- Updates `updated_by = auth.uid()`
- Respects soft deletes (`deleted_at IS NULL`)

---

### Delete (Remove Records)

**Purpose**: Delete or soft-delete records

**Syntax**:
```yaml
- delete: Entity
```

**Examples**:

#### Soft Delete (Default)
```yaml
steps:
  - delete: Contact
```

**Generated SQL**:
```sql
UPDATE crm.tb_contact
SET
  deleted_at = now(),
  deleted_by = auth.uid()
WHERE pk_contact = v_pk_contact;
```

#### Conditional Delete
```yaml
steps:
  - if: status = 'inactive'
    then:
      - delete: Contact
```

#### Cascade Delete
```yaml
steps:
  - delete: Order
  - delete: OrderItem WHERE fk_order = order_id
```

**Note**: Hard deletes are NOT generated by SpecQL. All deletes are soft deletes to maintain audit trails.

---

### Call (Function Calls)

**Purpose**: Call other functions or actions

**Syntax**:
```yaml
- call: function_name(arg1, arg2)
- call: schema.function_name(arg1, arg2)
  store: variable_name
```

**Examples**:

#### Simple Call
```yaml
steps:
  - call: send_welcome_email(contact.email)
```

#### Call with Result
```yaml
steps:
  - call: create_order(order_data)
  - set: order_id = result.id
```

#### Call Another Action
```yaml
steps:
  - call: crm.create_company(company_data)
  - set: company_id = result.object.id
  - insert: Contact(email, company_id)
```

#### Conditional Call
```yaml
steps:
  - if: lead_score > 80
    then:
      - call: notify_sales_team(contact_id, "High-value lead")
```

#### Multiple Calls
```yaml
steps:
  - insert: Contact
  - call: send_welcome_email(contact.email)
  - call: add_to_mailing_list(contact.email)
  - call: trigger_lead_scoring(contact.id)
```

**Generated SQL**:
```sql
SELECT crm.send_welcome_email(v_email) INTO v_result;
```

---

### Notify (Notifications)

**Purpose**: Send notifications to users or teams

**Syntax**:
```yaml
- notify: recipient(channel, message)
```

**Examples**:

#### Email Notification
```yaml
steps:
  - notify: contact.email "Welcome to our platform!"
```

#### Team Notification
```yaml
steps:
  - notify: sales_team "New lead: {first_name} {last_name}"
```

#### Conditional Notification
```yaml
steps:
  - if: lead_score > 90
    then:
      - notify: sales_manager "High-value lead qualified: {email}"
```

#### Multiple Recipients
```yaml
steps:
  - notify: contact.email "Your order has been confirmed"
  - notify: admin.email "New order from {contact.email}"
```

**Generated SQL**:
```sql
-- Framework handles notification queuing
INSERT INTO app.notifications (
  recipient,
  channel,
  message,
  created_at
) VALUES (
  v_contact_email,
  'email',
  'Welcome to our platform!',
  now()
);
```

---

### Foreach (Loops)

**Purpose**: Iterate over collections

**Syntax**:
```yaml
- foreach: item IN collection
  do:
    - steps
```

**Examples**:

#### Process Multiple Items
```yaml
steps:
  - foreach: item IN input.items
    do:
      - insert: OrderItem(
          order_id = order.id,
          product_id = item.product_id,
          quantity = item.quantity
        )
```

#### Batch Updates
```yaml
steps:
  - foreach: contact IN selected_contacts
    do:
      - update: Contact SET status = 'qualified'
        WHERE id = contact.id
```

#### Conditional Loop
```yaml
steps:
  - foreach: allocation IN future_allocations
    do:
      - if: allocation.is_provisional
        then:
          - delete: allocation
```

**Generated SQL**:
```sql
FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
LOOP
  INSERT INTO crm.tb_order_item (
    fk_order,
    fk_product,
    quantity
  ) VALUES (
    v_order_id,
    (v_item->>'product_id')::UUID,
    (v_item->>'quantity')::INTEGER
  );
END LOOP;
```

---

## Advanced Patterns

### Pattern 1: Deduplication

**Check for duplicates before insert**:

```yaml
actions:
  - name: create_contact
    steps:
      - validate: NOT EXISTS (
          SELECT 1 FROM crm.tb_contact
          WHERE email = input.email
        )
        error: "duplicate_email"

      - insert: Contact
```

### Pattern 2: Nested Object Creation

**Create parent, then child with FK**:

```yaml
actions:
  - name: create_contact_with_company
    steps:
      - if: company_data IS NOT NULL
        then:
          - call: create_company(company_data)
          - set: company_id = result.object.id
        else:
          - validate: company_id IS NOT NULL
            error: "company_required"

      - insert: Contact(email, first_name, last_name, company_id)
```

### Pattern 3: Status Transitions

**Enforce valid state transitions**:

```yaml
actions:
  - name: update_order_status
    steps:
      - fetch: order

      - validate: new_status IN allowed_transitions(order.status)
        error: "invalid_status_transition"

      - update: Order SET status = new_status

      - switch: new_status
        cases:
          shipped:
            - notify: customer.email "Your order has shipped!"
          delivered:
            - notify: customer.email "Your order was delivered"
            - call: trigger_review_request(order.id)
```

### Pattern 4: Temporal Logic

**Handle date ranges and overlaps**:

```yaml
actions:
  - name: create_reservation
    steps:
      - validate: reserved_from <= reserved_until
        error: "invalid_date_range"

      - validate: reserved_from >= CURRENT_DATE
        error: "past_date_not_allowed"

      - validate: NOT EXISTS (
          SELECT 1 FROM allocation
          WHERE fk_machine = input.machine_id
            AND daterange(start_date, end_date) &&
                daterange(input.reserved_from, input.reserved_until)
        )
        error: "overlapping_reservation"

      - insert: Reservation
```

### Pattern 5: Cascade Updates

**Update related records**:

```yaml
actions:
  - name: update_company_domain
    steps:
      - update: Company SET domain = new_domain

      - update: Contact SET
          email = replace(email, old_domain, new_domain)
        WHERE company_id = input.company_id
          AND email LIKE '%@' || old_domain
```

### Pattern 6: Computed Defaults

**Resolve defaults from related data**:

```yaml
actions:
  - name: create_allocation
    steps:
      - if: location_id IS NULL
        then:
          - call: get_default_location(organizational_unit_id)
          - set: location_id = result.id

      - if: start_date IS NULL
        then:
          - set: start_date = CURRENT_DATE

      - insert: Allocation
```

### Pattern 7: Conflict Resolution

**Detect and handle conflicts**:

```yaml
actions:
  - name: allocate_machine
    steps:
      - if: EXISTS current_allocation WITH same location AND orgunit
        then:
          - validate: FALSE
            error: "current_allocation_is_the_same"

      - if: EXISTS future_provisional_allocations
        then:
          - if: input.delete_future_allocations
            then:
              - foreach: allocation IN future_allocations
                do:
                  - delete: allocation
            else:
              - validate: FALSE
                error: "future_allocations_exist"

      - insert: Allocation
```

---

## Complete Examples

### Example 1: CRM Lead Management

```yaml
entity: Contact
schema: crm

fields:
  email: email!
  first_name: text!
  last_name: text!
  company: ref(Company)
  status: enum(lead, qualified, customer, inactive)
  lead_score: integer = 0
  qualified_at: timestamp

actions:
  - name: create_lead
    steps:
      # Validation
      - validate: email MATCHES email_pattern
        error: "invalid_email"

      # Deduplication
      - validate: NOT EXISTS (
          SELECT 1 FROM crm.tb_contact WHERE email = input.email
        )
        error: "duplicate_email"

      # Create contact
      - insert: Contact(email, first_name, last_name, company_id)

      # Trigger scoring
      - call: calculate_lead_score(contact.id)

      # Notify sales
      - if: lead_score > 80
        then:
          - notify: sales_team "High-value lead: {email}"

  - name: qualify_lead
    steps:
      # Validate current status
      - validate: status = 'lead'
        error: "not_a_lead"

      # Validate score threshold
      - validate: lead_score >= 60
        error: "score_too_low"

      # Update status
      - update: Contact SET
          status = 'qualified',
          qualified_at = now()

      # Notify
      - notify: owner.email "Lead qualified: {first_name} {last_name}"
      - notify: contact.email "Thank you for your interest!"

  - name: convert_to_customer
    steps:
      - validate: status = 'qualified'
        error: "not_qualified"

      - update: Contact SET
          status = 'customer',
          lead_score = 100

      - call: create_customer_account(contact.id)
      - call: send_welcome_sequence(contact.email)
      - notify: sales_team "New customer: {email}"
```

### Example 2: Order Processing

```yaml
entity: Order
schema: commerce

fields:
  customer: ref(Customer)!
  items: list(OrderItem)
  status: enum(draft, confirmed, shipped, delivered, cancelled)
  total_amount: money
  shipping_address: ref(Address)!

actions:
  - name: create_order
    steps:
      # Validate customer
      - validate: customer_id IS NOT NULL
        error: "customer_required"

      # Validate items
      - validate: jsonb_array_length(items) > 0
        error: "items_required"

      # Create order
      - insert: Order(customer_id, status = 'draft')

      # Create order items
      - foreach: item IN items
        do:
          - validate: item.quantity > 0
            error: "invalid_quantity"

          - call: get_product_price(item.product_id)
          - compute: line_total = result.price * item.quantity

          - insert: OrderItem(
              order_id = order.id,
              product_id = item.product_id,
              quantity = item.quantity,
              unit_price = result.price,
              total = line_total
            )

      # Calculate total
      - call: calculate_order_total(order.id)
      - update: Order SET total_amount = result.total

  - name: confirm_order
    steps:
      - validate: status = 'draft'
        error: "invalid_status"

      - validate: total_amount > 0
        error: "invalid_total"

      # Check inventory
      - foreach: item IN order.items
        do:
          - call: check_inventory(item.product_id, item.quantity)
          - validate: result.available = TRUE
            error: "insufficient_inventory"

      # Reserve inventory
      - foreach: item IN order.items
        do:
          - call: reserve_inventory(item.product_id, item.quantity)

      # Update order
      - update: Order SET
          status = 'confirmed',
          confirmed_at = now()

      # Notify
      - notify: customer.email "Order confirmed: #{order.identifier}"
      - notify: warehouse_team "New order to fulfill: #{order.identifier}"
```

### Example 3: Resource Allocation

```yaml
entity: Allocation
schema: inventory

fields:
  machine: ref(Machine)!
  organizational_unit: ref(OrganizationalUnit)!
  location: ref(Location)!
  start_date: date!
  end_date: date!
  is_provisional: boolean = false

actions:
  - name: create_allocation
    steps:
      # Validate dates
      - validate: start_date <= end_date
        error: "invalid_date_range"

      - validate: start_date >= CURRENT_DATE
        error: "past_date_not_allowed"

      # Check for same current allocation
      - if: EXISTS (
          SELECT 1 FROM inventory.allocation
          WHERE fk_machine = input.machine_id
            AND fk_organizational_unit = input.organizational_unit_id
            AND fk_location = input.location_id
            AND start_date <= CURRENT_DATE
            AND end_date >= CURRENT_DATE
            AND deleted_at IS NULL
        )
        then:
          - validate: FALSE
            error: "current_allocation_is_the_same"

      # Handle future provisional allocations
      - if: EXISTS (
          SELECT 1 FROM inventory.allocation
          WHERE fk_machine = input.machine_id
            AND start_date > CURRENT_DATE
            AND is_provisional = TRUE
            AND deleted_at IS NULL
        )
        then:
          - if: input.delete_future_allocations = TRUE
            then:
              - foreach: allocation IN (
                  SELECT * FROM inventory.allocation
                  WHERE fk_machine = input.machine_id
                    AND start_date > CURRENT_DATE
                    AND is_provisional = TRUE
                    AND deleted_at IS NULL
                )
                do:
                  - delete: allocation
            else:
              - validate: FALSE
                error: "future_allocations_exist"

      # Close current allocation
      - if: EXISTS (
          SELECT 1 FROM inventory.allocation
          WHERE fk_machine = input.machine_id
            AND start_date <= input.start_date
            AND end_date >= input.start_date
            AND deleted_at IS NULL
        )
        then:
          - update: allocation SET end_date = input.start_date - interval '1 day'
            WHERE fk_machine = input.machine_id
              AND start_date <= input.start_date
              AND end_date >= input.start_date

      # Create allocation
      - insert: Allocation(
          machine_id,
          organizational_unit_id,
          location_id,
          start_date,
          end_date,
          is_provisional
        )

      # Update machine flags
      - call: update_machine_allocation_flags(machine_id)
```

---

## Best Practices

### 1. **Validate Early**
Put validation steps at the beginning of your action:

✅ **Good**:
```yaml
steps:
  - validate: email IS NOT NULL
  - validate: phone MATCHES phone_pattern
  - insert: Contact
```

❌ **Bad**:
```yaml
steps:
  - insert: Contact
  - validate: email IS NOT NULL  # Too late!
```

### 2. **Use Meaningful Error Codes**

✅ **Good**:
```yaml
- validate: lead_score >= 60
  error: "score_below_qualification_threshold"
```

❌ **Bad**:
```yaml
- validate: lead_score >= 60
  error: "invalid"
```

### 3. **Keep Actions Focused**

One action should do one thing well:

✅ **Good**:
```yaml
- name: qualify_lead
  steps:
    - validate: status = 'lead'
    - update: Contact SET status = 'qualified'

- name: convert_to_customer
  steps:
    - validate: status = 'qualified'
    - update: Contact SET status = 'customer'
```

❌ **Bad**:
```yaml
- name: update_status
  steps:
    - if: new_status = 'qualified'
      then: [...]
    - if: new_status = 'customer'
      then: [...]
    # Too many responsibilities!
```

### 4. **Use Switch for Multiple Cases**

✅ **Good**:
```yaml
- switch: status
  cases:
    lead: [...]
    qualified: [...]
    customer: [...]
```

❌ **Bad**:
```yaml
- if: status = 'lead'
  then: [...]
- if: status = 'qualified'
  then: [...]
- if: status = 'customer'
  then: [...]
```

### 5. **Document Complex Logic**

```yaml
actions:
  - name: create_allocation
    description: |
      Creates a new machine allocation with automatic conflict resolution.
      Handles: temporal overlaps, provisional allocation cleanup, neighbor adjustment.

    steps:
      # Check for temporal conflicts
      - validate: NOT EXISTS overlapping_allocation
        error: "overlapping_allocation"

      # Close previous allocation if needed
      - if: EXISTS previous_allocation
        then:
          - update: previous SET end_date = input.start_date - 1
```

### 6. **Handle Edge Cases**

```yaml
steps:
  # Normal case
  - if: company_id IS NOT NULL
    then:
      - insert: Contact(company_id, ...)

  # Edge case: create company first
  - if: company_data IS NOT NULL
    then:
      - call: create_company(company_data)
      - set: company_id = result.id
      - insert: Contact(company_id, ...)

  # Error case
  - validate: company_id IS NOT NULL
    error: "company_required"
```

### 7. **Use Foreach for Collections**

✅ **Good**:
```yaml
- foreach: item IN order.items
  do:
    - insert: OrderItem(item.product_id, item.quantity)
```

❌ **Bad**: Don't try to manually iterate

### 8. **Leverage Framework Features**

Let the framework handle:
- ✅ Audit trails (automatic)
- ✅ Permission checks (`requires:`)
- ✅ Type validation (automatic)
- ✅ Event emission (automatic)

Focus your YAML on:
- 🎯 Business rules
- 🎯 Workflows
- 🎯 Domain logic

---

## What's Next?

- **[Rich Types Guide](rich-types-guide.md)** - Learn about validated scalar types
- **[stdlib Usage](stdlib-usage.md)** - Use production-ready entities
- **[Multi-Tenancy Guide](multi-tenancy.md)** - Build SaaS applications
- **[GraphQL Integration](graphql-integration.md)** - Auto-generated mutations

---

**SpecQL Actions: Because your business logic should be declarative, not imperative.** 🚀
