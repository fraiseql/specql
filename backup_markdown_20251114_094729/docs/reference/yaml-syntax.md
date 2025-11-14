# SpecQL YAML Syntax Reference

**Complete DSL specification for defining business entities** 📋

## Overview

SpecQL uses a YAML-based domain-specific language (DSL) to define business entities. The YAML is declarative, focusing on business logic rather than implementation details.

**Key Principles:**
- **Business-focused**: Define what, not how
- **Type-safe**: Rich scalar types with automatic validation
- **Relationship-aware**: Automatic foreign keys and constraints
- **Action-oriented**: Business logic as composable steps

## Document Structure

### Basic Entity

```yaml
entity: Contact                    # Entity name (PascalCase)
schema: crm                        # PostgreSQL schema
description: "Customer contacts"   # Human-readable description

fields:                            # Data fields
  first_name: text!                # Field definition
  last_name: text!
  email: email!

actions:                           # Business operations
  - name: create_contact          # Action definition
    steps:
      - insert: Contact
```

### Complete Entity

```yaml
entity: Contact
schema: tenant                     # Multi-tenant schema
description: "Customer contact information with validation"

fields:
  # Basic information
  first_name: text!
  last_name: text!
  email: email!

  # Rich types with validation
  phone: phone
  website: url
  avatar: image

  # Relationships
  organization: ref(Organization)
  manager: ref(Contact)            # Self-reference

  # Enums
  status: enum(lead, qualified, customer)
  priority: enum(low, medium, high)

  # Computed fields
  full_name: text                  # Auto-computed

actions:
  - name: create_contact
    description: "Create a new contact"
    steps:
      - validate: email IS NOT NULL
      - insert: Contact

  - name: qualify_lead
    description: "Convert lead to qualified prospect"
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'

  - name: transfer_contact
    description: "Move contact to different organization"
    steps:
      - validate: new_org_id IS NOT NULL
      - update: Contact SET organization_id = ?
```

## Entity Definition

### entity (required)
**Type**: `string` (PascalCase)
**Description**: The entity name, used for table names, function names, etc.

```yaml
entity: Contact           # ✅ Good
entity: contact           # ❌ Bad - not PascalCase
entity: CustomerContact   # ✅ Good - compound words
```

### schema (required)
**Type**: `string`
**Description**: PostgreSQL schema name. Affects multi-tenancy and access patterns.

```yaml
schema: tenant   # Multi-tenant business data
schema: common   # Shared reference data
schema: app      # Application-global data
schema: crm      # Domain-specific schema
```

### description (optional)
**Type**: `string`
**Description**: Human-readable description used for documentation and GraphQL.

```yaml
description: "Customer contact information"
description: |
  Multi-line description
  with detailed explanation
```

### extends (optional)
**Type**: `object`
**Description**: Inherit from another entity (stdlib or custom).

```yaml
extends:
  from: stdlib/crm/contact    # Import stdlib entity
  # or
  from: entities/base_entity  # Import custom entity
```

## Fields Definition

### Field Syntax
```
field_name: type[!][modifiers]
```

**Components:**
- `field_name`: snake_case identifier
- `type`: Scalar type or reference
- `!`: NOT NULL constraint (optional)
- `modifiers`: Additional constraints (optional)

### Scalar Types

#### Basic Types
```yaml
# Text types
name: text              # VARCHAR without length limit
code: text!             # NOT NULL text
description: text       # Optional long text

# Numeric types
count: integer          # INTEGER
price: decimal          # DECIMAL(10,2)
percentage: numeric     # NUMERIC with validation

# Boolean
active: boolean         # TRUE/FALSE

# Binary
data: bytea             # BYTEA for binary data

# JSON
metadata: json          # JSONB
settings: jsonb         # JSONB (explicit)
```

#### Rich Types (49 validated types)
```yaml
# Contact
email: email!           # Email validation
phone: phone            # E.164 phone format

# Web
website: url            # URL validation
domain: domainName      # Domain name validation
slug: slug              # URL-friendly string

# Content
content: markdown       # Markdown text
html_content: html      # HTML content

# Financial
price: money            # Monetary amount
rate: percentage        # 0-100 percentage
currency: currencyCode  # ISO currency code

# Temporal
birth_date: date        # Date only
created_at: datetime    # Date and time
duration: duration      # Time duration

# Geographic
location: coordinates   # PostgreSQL POINT
latitude: latitude      # -90 to 90
longitude: longitude    # -180 to 180

# Technical
ip: ipAddress           # IPv4/IPv6
mac: macAddress        # MAC address
uuid_field: uuid        # UUID validation

# Business
stock: stockSymbol      # Stock ticker
isin: isin              # ISIN code
vin: vin                # Vehicle VIN
```

### Reference Types
```yaml
# Single reference
organization: ref(Organization)           # Foreign key
manager: ref(Contact)                     # Self-reference

# Multiple references
tags: ref(Tag, many: true)               # Many-to-many
categories: ref(Category, many: true)

# Polymorphic reference
owner: ref(User|Organization)            # Union type
```

### Enum Types
```yaml
# Simple enum
status: enum(active, inactive, suspended)

# Enum with default
priority: enum(low, medium, high) = 'medium'

# Complex enum with validation
type: enum(
  individual,     # Person
  organization,   # Company
  department      # Internal dept
)
```

### Field Modifiers

#### Nullability
```yaml
required_field: text!    # NOT NULL
optional_field: text     # NULL allowed
```

#### Default Values
```yaml
status: enum(active, inactive) = 'active'
count: integer = 0
name: text = 'Unknown'
```

#### Custom Validation
```yaml
age: integer(min: 0, max: 150)           # Range validation
length: decimal(precision: 10, scale: 2) # Precision
code: text(maxLength: 10)                # Length limit
```

#### Field Descriptions
```yaml
email:
  type: email!
  description: "Primary email address - must be unique"

phone:
  type: phone
  description: "Business phone in E.164 format"
```

### Advanced Field Syntax

#### Complex Field Definition
```yaml
email:
  type: email
  nullable: false
  description: "Primary contact email"
  unique: true
  index: true

score:
  type: percentage
  min: 0
  max: 100
  default: 50
  description: "Lead scoring percentage"
```

#### Computed Fields
```yaml
full_name:
  type: text
  computed: "first_name || ' ' || last_name"
  description: "Auto-computed full name"

total_value:
  type: money
  computed: "SUM(order_amounts)"
  description: "Total order value"
```

## Actions Definition

### Action Structure
```yaml
actions:
  - name: action_name
    description: "What this action does"
    security: permission_required
    steps:
      - step_type: parameters
```

### Action Types

#### CRUD Actions (Auto-generated)
```yaml
actions:
  - name: create_entity    # Auto-generated INSERT
  - name: update_entity    # Auto-generated UPDATE
  - name: delete_entity    # Auto-generated soft DELETE
  - name: get_entity       # Auto-generated SELECT
  - name: list_entities    # Auto-generated SELECT with filters
```

#### Custom Business Actions
```yaml
actions:
  - name: qualify_lead
    description: "Convert marketing lead to sales qualified"
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified', qualified_at = now()
      - notify: sales_team "New qualified lead"

  - name: transfer_customer
    description: "Move customer to different organization"
    steps:
      - validate: new_org_id IS NOT NULL
      - validate: has_permission('transfer_customers')
      - update: Contact SET organization_id = ?
      - log: "Customer transferred to {new_org}"
```

### Step Types

#### Validation Steps
```yaml
steps:
  - validate: email IS NOT NULL
  - validate: status IN ('lead', 'qualified')
  - validate: age >= 18
  - validate: email MATCHES '^[^@]+@[^@]+\.[^@]+$'
  - validate: UNIQUE(email, organization_id)  # Composite unique
```

#### Data Manipulation
```yaml
steps:
  - insert: Contact                    # Insert current entity
  - insert: ContactLog VALUES (...)    # Insert related record

  - update: Contact SET status = ?     # Update current entity
  - update: Organization SET updated_at = now() WHERE id = ?

  - delete: Contact WHERE status = 'inactive'  # Soft delete
```

#### Control Flow
```yaml
steps:
  - if: status = 'lead'
    then:
      - update: Contact SET qualified_at = now()
    else:
      - error: "Contact already qualified"

  - foreach: active_contacts
    do:
      - send_email: welcome_email(contact.email)

  - try:
      - call: external_api_sync()
    catch:
      - log: "API sync failed: {error}"
      - retry: 3
```

#### External Integration
```yaml
steps:
  - call: send_welcome_email(email, first_name)
  - notify: sales_team "New customer signed up"
  - webhook: https://crm.example.com/webhook
  - schedule: follow_up_email DELAY '24 hours'
```

### Action Modifiers

#### Security
```yaml
actions:
  - name: delete_customer
    security: admin_only
    steps: [...]

  - name: view_sensitive_data
    security: role('manager', 'supervisor')
    steps: [...]
```

#### Transactions
```yaml
actions:
  - name: process_order
    transaction: required  # Auto-wrap in transaction
    steps:
      - validate: inventory_available
      - update: Inventory SET quantity = quantity - ?
      - insert: Order
      - call: payment_processor()

  - name: bulk_import
    transaction: each     # Transaction per item
    steps: [...]
```

#### Error Handling
```yaml
actions:
  - name: create_user
    on_error: rollback   # Default
    steps:
      - validate: email_unique
      - insert: User
      - error: "Email already exists" WHEN duplicate_key

  - name: send_notification
    on_error: continue   # Don't fail whole action
    steps:
      - call: email_service()
```

## Advanced Features

### Inheritance
```yaml
# Base entity
entity: BaseEntity
fields:
  created_at: datetime!
  updated_at: datetime!

# Extended entity
entity: Contact
extends:
  from: BaseEntity
fields:
  name: text!
  email: email!
```

### Mixins
```yaml
# Mixin definition
mixin: Auditable
fields:
  created_by: ref(User)
  updated_by: ref(User)

# Usage
entity: Contact
mixins: [Auditable, SoftDelete]
fields:
  name: text!
```

### Templates
```yaml
# Template for common patterns
template: StandardEntity
fields:
  id: uuid!
  name: text!
  active: boolean = true

# Usage
entity: Product
template: StandardEntity
fields:
  price: money
```

### Imports
```yaml
# Import stdlib entities
import: stdlib/crm/contact
import: stdlib/i18n/country

# Import custom entities
import: entities/base_types

entity: ExtendedContact
extends:
  from: stdlib/crm/contact
fields:
  custom_field: text
```

## Schema Organization

### Multi-Tenant Schemas
```yaml
# Business data per tenant
entity: Customer
schema: tenant

# Shared reference data
entity: Country
schema: common

# Application configuration
entity: AppSettings
schema: app
```

### Domain Schemas
```yaml
# CRM domain
entity: Contact
schema: crm

entity: Organization
schema: crm

# Billing domain
entity: Invoice
schema: billing

entity: Payment
schema: billing
```

## Validation Rules

### Naming Conventions
- **Entities**: PascalCase (`Contact`, `OrderItem`)
- **Fields**: snake_case (`first_name`, `email_address`)
- **Actions**: snake_case (`create_contact`, `process_payment`)
- **Schemas**: lowercase (`crm`, `tenant`, `common`)

### Type Consistency
```yaml
# ✅ Consistent types
entity: User
fields:
  email: email!     # Rich type
  phone: phone      # Rich type

# ❌ Mixed types
entity: User
fields:
  email: text       # Generic type
  phone: text       # Generic type - loses validation
```

### Relationship Patterns
```yaml
# ✅ Clear relationships
entity: Order
fields:
  customer: ref(Customer)
  items: ref(OrderItem, many: true)

# ❌ Unclear relationships
entity: Order
fields:
  customer_id: integer  # Magic number, no constraint
  item_ids: json        # No referential integrity
```

## Examples

### Simple Entity
```yaml
entity: Tag
schema: common
description: "Content tags"

fields:
  name: text!
  color: text
  slug: slug!

actions:
  - name: create_tag
  - name: update_tag
  - name: delete_tag
```

### Complex Entity
```yaml
entity: Order
schema: tenant
description: "Customer orders with line items"

fields:
  order_number: text!
  customer: ref(Customer)
  status: enum(pending, confirmed, shipped, delivered)
  total_amount: money!
  shipping_address: ref(Address)

  # Computed field
  item_count:
    type: integer
    computed: "COUNT(order_items)"

actions:
  - name: create_order
    steps:
      - validate: customer IS NOT NULL
      - validate: item_count > 0
      - insert: Order

  - name: add_item
    description: "Add item to order"
    steps:
      - validate: order.status = 'pending'
      - insert: OrderItem

  - name: ship_order
    description: "Mark order as shipped"
    steps:
      - validate: status = 'confirmed'
      - update: Order SET status = 'shipped', shipped_at = now()
      - notify: customer "Your order has shipped"
```

### Multi-Tenant SaaS Entity
```yaml
entity: Project
schema: tenant
description: "User projects with team collaboration"

fields:
  name: text!
  description: text
  owner: ref(User)
  team_members: ref(User, many: true)
  status: enum(active, archived, deleted)
  settings: json

actions:
  - name: create_project
    security: authenticated
    steps:
      - insert: Project

  - name: invite_member
    description: "Invite user to project"
    steps:
      - validate: has_permission('manage_team')
      - validate: user_not_already_member
      - insert: ProjectMember
      - send_email: invitation_email

  - name: archive_project
    description: "Archive completed project"
    steps:
      - validate: owner = current_user
      - update: Project SET status = 'archived'
```

## Best Practices

### 1. Use Rich Types
```yaml
# ✅ Semantic types with validation
fields:
  email: email!
  phone: phone
  website: url

# ❌ Generic types lose validation
fields:
  email: text
  phone: text
  website: text
```

### 2. Descriptive Names
```yaml
# ✅ Clear intent
entity: CustomerOrder
fields:
  shipping_address: ref(Address)
  billing_address: ref(Address)

# ❌ Unclear
entity: Order
fields:
  address1: ref(Address)
  address2: ref(Address)
```

### 3. Consistent Patterns
```yaml
# ✅ Consistent action naming
actions:
  - name: create_customer
  - name: update_customer
  - name: delete_customer

# ❌ Inconsistent
actions:
  - name: add_customer
  - name: modify_customer
  - name: remove_customer
```

### 4. Validation First
```yaml
# ✅ Validate before action
actions:
  - name: process_payment
    steps:
      - validate: amount > 0
      - validate: payment_method_valid
      - validate: sufficient_funds
      - call: payment_processor()

# ❌ Action then validation
actions:
  - name: process_payment
    steps:
      - call: payment_processor()  # Might fail
      - validate: success = true
```

## Migration Guide

### From SQL DDL
```sql
-- Old SQL approach
CREATE TABLE contacts (
  id SERIAL PRIMARY KEY,
  email VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);
```

```yaml
# New SpecQL approach
entity: Contact
fields:
  email: email!  # Automatic validation + NOT NULL
  # created_at added automatically
```

### From ORM Models
```python
# Old ORM approach
class Contact(Model):
    email = CharField(validators=[EmailValidator()])
    created_at = DateTimeField(default=datetime.now)
```

```yaml
# New SpecQL approach
entity: Contact
fields:
  email: email!  # Validation built-in
  # created_at automatic
```

## Error Reference

### Common Syntax Errors
```
❌ entity: contact          # Must be PascalCase
✅ entity: Contact

❌ fields:
    FirstName: text        # Must be snake_case
✅ fields:
    first_name: text

❌ actions:
    - CreateContact        # Must be snake_case
✅ actions:
    - name: create_contact
```

### Validation Errors
```
❌ email: email!            # Invalid - no such type
✅ email: email!

❌ status: enum             # Missing values
✅ status: enum(active, inactive)

❌ ref(UnknownEntity)      # Entity not found
✅ ref(Contact)
```

## Next Steps

- **Read Rich Types Guide**: Complete type reference in `docs/guides/rich-types-guide.md`
- **Check Actions Guide**: Business logic patterns in `docs/guides/actions-guide.md`
- **Browse Examples**: Real implementations in `examples/`
- **Generate Code**: Run `specql generate entities/*.yaml`

---

**YAML that defines your business, generates your backend.** 🚀