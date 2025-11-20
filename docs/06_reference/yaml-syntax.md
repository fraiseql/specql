# SpecQL YAML Syntax Reference

> **Complete reference for SpecQL's declarative YAML syntax**

## Overview

SpecQL uses YAML to declare business entities and logic. This reference covers every YAML construct supported by SpecQL.

**Philosophy**: Business domain only, no technical implementation details.

---

## File Structure

### Basic Entity File

```yaml
entity: Contact              # Entity name (PascalCase)
schema: crm                  # Schema name (lowercase)
description: "Customer contact information"  # Optional

fields:                      # Entity fields
  email: email!
  first_name: text!
  last_name: text!
  company: ref(Company)!

actions:                     # Business logic
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'

table_views:                 # Read-only views
  - name: active_contacts
    filters:
      - deleted_at IS NULL
```

### Multi-File Organization

**Recommended structure**:
```
entities/
├── crm/
│   ├── contact.yaml
│   ├── company.yaml
│   └── deal.yaml
├── projects/
│   ├── project.yaml
│   ├── task.yaml
│   └── milestone.yaml
└── finance/
    ├── invoice.yaml
    └── payment.yaml
```

---

## Entity Declaration

### Syntax

```yaml
entity: <EntityName>
schema: <schema_name>
description: <optional_description>
extends: <ParentEntity>           # Optional inheritance
patterns:                         # Optional patterns
  - <pattern_name>

fields:
  # ... field declarations

actions:
  # ... action declarations

table_views:
  # ... view declarations

computed_fields:
  # ... computed field declarations
```

### Examples

**Simple Entity**:
```yaml
entity: Company
schema: crm
description: "Business organization"

fields:
  name: text!
  website: url
```

**With Inheritance**:
```yaml
entity: AdminUser
schema: auth
extends: User

fields:
  admin_level: integer(1, 10)!
  permissions: list(text)!
```

**With Patterns**:
```yaml
entity: Order
schema: sales
patterns:
  - audit_trail      # Auto-adds created_at, updated_at, etc.
  - soft_delete      # Auto-adds deleted_at
  - state_machine    # Tracks status transitions

fields:
  customer: ref(Customer)!
  total: money!
  status: enum(draft, pending, paid, shipped)!
```

---

## Fields

### Field Syntax

```yaml
fields:
  <field_name>: <type>[!]            # Simple type
  <field_name>: <type>(<args>)[!]    # Type with arguments
  <field_name>: <type> = <default>   # With default value
```

### Simple Types

```yaml
fields:
  # Text types
  name: text!
  bio: text(500)            # Max length
  email: email!             # Email validation
  url: url
  phone: phoneNumber

  # Numeric types
  age: integer!
  age_range: integer(18, 120)  # Min, max
  price: decimal(10, 2)     # Precision, scale
  amount: money!            # Currency (NUMERIC(19,4))

  # Date/time types
  birth_date: date!
  created_at: datetime!
  duration: interval

  # Boolean
  is_active: boolean!

  # UUID
  id: uuid!

  # JSON
  metadata: jsonb
  config: json!
```

### Rich Types

```yaml
fields:
  # Contact information
  email: email!
  phone: phoneNumber
  website: url

  # Financial
  price: money!
  tax_rate: percentage
  credit_card: creditCard  # Encrypted

  # Geographic
  address: address!
  coordinates: geoPoint
  country: countryCode!

  # Identifiers
  sku: sku!
  isbn: isbn
  ean: ean13

  # Complex types
  tags: list(text)
  metadata: jsonb!
  translations: i18nText!
```

**Full list**: [Rich Types Reference](rich-types-reference.md)

### References (Foreign Keys)

```yaml
fields:
  # Simple reference
  company: ref(Company)!

  # Reference with cascade
  company: ref(Company, on_delete: cascade)!

  # Self-reference
  parent_category: ref(Category)

  # Reference to different schema
  tenant: ref(common.Tenant)!
```

**On Delete Options**:
- `cascade` - Delete child when parent deleted
- `set_null` - Set to NULL when parent deleted
- `restrict` - Prevent parent deletion (default)

### Enums

```yaml
fields:
  # Inline enum
  status: enum(draft, published, archived)!

  # With default
  role: enum(user, admin, moderator) = 'user'

  # Multi-value (PostgreSQL array)
  permissions: list(enum(read, write, delete))!
```

### Lists (Arrays)

```yaml
fields:
  # Simple list
  tags: list(text)

  # List of references
  categories: list(ref(Category))!

  # List with constraints
  scores: list(integer(0, 100))!

  # List of rich types
  emails: list(email)!
```

### Default Values

```yaml
fields:
  # Constant defaults
  status: enum(active, inactive) = 'active'
  created_at: datetime = now()
  is_verified: boolean = false

  # Expression defaults
  total: money = 0.00
  counter: integer = 0
```

### Computed Fields

```yaml
computed_fields:
  # Simple concatenation
  - full_name: concat(first_name, ' ', last_name)

  # Arithmetic
  - total_with_tax: total * 1.2

  # Conditional
  - status_label: case
      when status = 'active' then 'Active'
      when status = 'inactive' then 'Inactive'
      else 'Unknown'

  # Aggregate (from related entity)
  - order_count: count(orders)
  - total_spent: sum(orders.total)
```

---

## Actions

### Action Syntax

```yaml
actions:
  - name: <action_name>
    description: <optional_description>
    params:                          # Input parameters
      <param_name>: <type>[!]
    steps:                           # Business logic steps
      - <step_declaration>
    impacts:                         # Side effects metadata
      - entity: <Entity>
        operation: <insert|update|delete>
```

### Action Steps

**Validate**:
```yaml
- validate: <expression>
  error: <error_code>
  message: <error_message>
```

**If/Then/Else**:
```yaml
- if: <condition>
  then:
    - <steps>
  else:
    - <steps>
```

**Insert**:
```yaml
- insert: <Entity> VALUES (
    <field>: <value>,
    ...
  )
```

**Update**:
```yaml
- update: <Entity>
  SET <field> = <value>, ...
  WHERE <condition>
```

**Delete**:
```yaml
- delete: <Entity>
  WHERE <condition>
```

**Call**:
```yaml
- call: <function_name>
  args: {<arg>: <value>, ...}
  result: $<variable>
```

**Notify**:
```yaml
- notify: <event_name>
  to: <email_address>
  data: {<key>: <value>, ...}
```

**Foreach**:
```yaml
- foreach: <collection> as <item>
  do:
    - <steps>
```

**Refresh**:
```yaml
- refresh: <materialized_view_name>
```

**Full reference**: [Action Steps Reference](action-steps.md)

### Examples

**Simple Action**:
```yaml
actions:
  - name: archive_contact
    steps:
      - update: Contact SET deleted_at = now()
```

**Action with Parameters**:
```yaml
actions:
  - name: update_price
    params:
      product_id: uuid!
      new_price: money!
      reason: text
    steps:
      - validate: $new_price > 0, error: "price_must_be_positive"
      - update: Product
        SET price = $new_price, updated_reason = $reason
        WHERE id = $product_id
```

**Complex Workflow**:
```yaml
actions:
  - name: process_order
    params:
      order_id: uuid!
    steps:
      - validate: status = 'pending', error: "order_not_pending"
      - validate: call(check_inventory, $order_id), error: "insufficient_stock"

      - update: Order SET status = 'processing', processed_at = now()

      - foreach: OrderItem WHERE order_id = $order_id as item
        do:
          - update: Product
            SET stock = stock - $item.quantity
            WHERE id = $item.product_id

      - insert: OrderHistory VALUES (
          order_id: $order_id,
          status: 'processing',
          timestamp: now()
        )

      - notify: order_processed, to: $customer.email
```

---

## Table Views

### Syntax

```yaml
table_views:
  - name: <view_name>
    description: <optional_description>
    source: <Entity>
    params:                          # Optional parameters
      <param>: <type>
    filters:                         # WHERE conditions
      - <condition>
    includes:                        # JOIN relationships
      - <relationship>
    fields:                          # SELECT fields
      - <field>
      - <alias>: <expression>
    order_by:                        # ORDER BY
      - <field> [ASC|DESC]
    group_by:                        # GROUP BY
      - <field>
    limit: <number>
```

### Examples

**Simple View**:
```yaml
table_views:
  - name: active_contacts
    source: Contact
    filters:
      - deleted_at IS NULL
      - status = 'active'
```

**View with Joins**:
```yaml
table_views:
  - name: contacts_with_companies
    source: Contact
    includes:
      - company
      - company.industry
    fields:
      - id
      - email
      - full_name
      - company_name: company.name
      - industry: company.industry.name
```

**Parameterized View**:
```yaml
table_views:
  - name: contacts_by_status
    source: Contact
    params:
      status_filter: enum(active, inactive)!
    filters:
      - status = $status_filter
```

**Aggregate View**:
```yaml
table_views:
  - name: revenue_by_customer
    source: Order
    filters:
      - status = 'paid'
    fields:
      - customer_id
      - customer_name: customer.name
      - total_revenue: sum(total)
      - order_count: count(*)
      - avg_order: avg(total)
    group_by:
      - customer_id
    order_by:
      - total_revenue DESC
```

---

## Expressions

### Comparison Operators

```yaml
# Equality
field = value
field != value

# Comparison
field > value
field >= value
field < value
field <= value

# Pattern matching
field LIKE 'pattern%'
field ILIKE 'pattern%'  # Case-insensitive

# NULL checks
field IS NULL
field IS NOT NULL

# Set membership
field IN (value1, value2, value3)
field NOT IN (value1, value2)

# Range
field BETWEEN min AND max
```

### Logical Operators

```yaml
# AND
condition1 AND condition2

# OR
condition1 OR condition2

# NOT
NOT condition
```

### Arithmetic Operators

```yaml
# Basic arithmetic
field + value
field - value
field * value
field / value
field % value  # Modulo

# Functions
abs(field)
round(field, 2)
ceil(field)
floor(field)
```

### String Functions

```yaml
# Concatenation
concat(first_name, ' ', last_name)

# Case conversion
upper(name)
lower(email)

# Trimming
trim(field)
ltrim(field)
rtrim(field)

# Substring
substring(field, 1, 10)

# Length
length(field)
```

### Date/Time Functions

```yaml
# Current time
now()
current_date
current_timestamp

# Date arithmetic
date + interval '1 day'
timestamp - interval '1 hour'

# Date parts
extract(year from date)
extract(month from date)
date_part('year', date)
```

### Aggregate Functions

```yaml
count(*)
count(field)
sum(field)
avg(field)
min(field)
max(field)
```

### Conditional Expressions

```yaml
# CASE expression
case
  when condition1 then value1
  when condition2 then value2
  else default_value
end

# COALESCE (first non-null)
coalesce(field1, field2, 'default')

# NULLIF
nullif(field, value)
```

---

## Comments

```yaml
# This is a comment

entity: Contact  # Inline comment

fields:
  # Group of related fields
  email: email!
  phone: phoneNumber

  # Financial information
  balance: money!
  credit_limit: money
```

---

## YAML Anchors & Aliases

**Reuse common definitions**:

```yaml
# Define anchor
common_audit_fields: &audit
  created_at: datetime
  updated_at: datetime
  created_by: ref(User)
  updated_by: ref(User)

# Use in entities
entity: Contact
fields:
  email: email!
  <<: *audit  # Merge audit fields

entity: Company
fields:
  name: text!
  <<: *audit  # Reuse same fields
```

---

## Validation

### Field Validation

```yaml
fields:
  # Required fields
  email: email!

  # Range validation
  age: integer(18, 120)!
  score: decimal(0, 100)

  # Length validation
  name: text(100)!      # Max 100 chars
  bio: text(50, 500)    # Min 50, max 500

  # Pattern validation (rich types)
  email: email!         # Email format
  url: url!             # URL format
  phone: phoneNumber!   # Phone format
```

### Action Validation

```yaml
actions:
  - name: create_user
    params:
      email: email!
      age: integer(18)!
    steps:
      # Validation steps
      - validate: $age >= 18, error: "must_be_adult"
      - validate: NOT EXISTS(SELECT 1 FROM User WHERE email = $email),
                 error: "email_already_exists"

      - insert: User FROM $input
```

---

## Best Practices

### 1. Naming Conventions

```yaml
# ✅ Good: PascalCase for entities
entity: CompanyContact

# ❌ Bad: snake_case for entities
entity: company_contact

# ✅ Good: snake_case for fields
fields:
  first_name: text!

# ❌ Bad: camelCase for fields
fields:
  firstName: text!
```

### 2. File Organization

```yaml
# ✅ Good: One entity per file
# contact.yaml
entity: Contact
...

# company.yaml
entity: Company
...

# ❌ Bad: Multiple entities in one file
# entities.yaml
entity: Contact
...
---
entity: Company
...
```

### 3. Use Rich Types

```yaml
# ✅ Good: Rich type with validation
fields:
  email: email!
  phone: phoneNumber!
  price: money!

# ❌ Bad: Generic text type
fields:
  email: text!
  phone: text
  price: decimal
```

### 4. Document Complex Logic

```yaml
actions:
  - name: calculate_commission
    description: |
      Calculate sales commission based on tiered structure:
      - 0-10k: 5%
      - 10k-50k: 7%
      - 50k+: 10%
    steps:
      # ...
```

### 5. Use Descriptive Error Codes

```yaml
# ✅ Good: Descriptive error code
- validate: balance >= amount
  error: "insufficient_funds"

# ❌ Bad: Generic error code
- validate: balance >= amount
  error: "error"
```

---

## Complete Example

```yaml
entity: Order
schema: sales
description: "Customer order with line items"

patterns:
  - audit_trail
  - soft_delete

fields:
  # References
  customer: ref(Customer)!
  shipping_address: ref(Address)!

  # Order details
  order_number: text!
  status: enum(draft, pending, paid, shipped, delivered, cancelled) = 'draft'
  subtotal: money!
  tax: money!
  shipping_cost: money!
  total: money!

  # Dates
  order_date: date!
  ship_date: date
  delivery_date: date

  # Metadata
  notes: text(1000)
  metadata: jsonb

computed_fields:
  - item_count: count(order_items)
  - is_overdue: delivery_date < current_date AND status != 'delivered'

actions:
  - name: process_payment
    description: "Process payment and update order status"
    params:
      payment_method: enum(credit_card, paypal, bank_transfer)!
      payment_reference: text!

    steps:
      - validate: status = 'pending', error: "order_not_pending"
      - validate: total > 0, error: "invalid_order_total"
      - validate: customer.balance >= total, error: "insufficient_funds"

      - update: Customer
        SET balance = balance - $total
        WHERE id = $customer_id

      - update: Order
        SET status = 'paid',
            payment_method = $payment_method,
            payment_reference = $payment_reference,
            paid_at = now()

      - insert: Transaction VALUES (
          order_id: $order_id,
          customer_id: $customer_id,
          amount: $total,
          type: 'payment',
          reference: $payment_reference
        )

      - notify: payment_processed, to: $customer.email

    impacts:
      - entity: Order
        operation: update
      - entity: Customer
        operation: update
      - entity: Transaction
        operation: insert

  - name: ship_order
    steps:
      - validate: status = 'paid', error: "order_not_paid"
      - update: Order SET status = 'shipped', ship_date = now()
      - notify: order_shipped, to: $customer.email

table_views:
  - name: pending_orders
    source: Order
    filters:
      - status = 'pending'
      - deleted_at IS NULL
    order_by:
      - order_date ASC

  - name: revenue_by_month
    source: Order
    filters:
      - status = 'paid'
    fields:
      - month: date_trunc('month', order_date)
      - revenue: sum(total)
      - order_count: count(*)
    group_by:
      - month
    order_by:
      - month DESC
```

---

## Next Steps

- **Tutorial**: [Your First Entity](../01_getting-started/first-entity.md)
- **Reference**:
  - [Rich Types Reference](rich-types-reference.md)
  - [Action Steps Reference](action-steps.md)
  - [CLI Commands](cli-commands.md)
- **Guides**:
  - [Actions Guide](../05_guides/actions.md)
  - [Multi-Tenancy](../05_guides/multi-tenancy.md)

---

**SpecQL's YAML syntax is designed for clarity and business focus—keep it simple, keep it declarative.**
