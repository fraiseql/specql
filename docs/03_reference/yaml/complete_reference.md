# Complete YAML Reference

**Full SpecQL YAML syntax specification** - Every field, option, and configuration

This reference documents the complete YAML syntax accepted by SpecQL, verified against the actual parser implementation.

## 📋 Document Structure

SpecQL YAML files define entities with their data structure and business logic:

```yaml
# Entity definition
entity: Contact
schema: crm
description: "Customer contact information"
organization: customer

# Data structure
fields:
  # Field definitions

# Business logic
actions:
  # Action definitions

# Optional configurations
constraints:
  # Database constraints

projections:
  # View definitions

identifiers:
  # Identifier patterns
```

## 🎯 Top-Level Properties

### entity
**Type**: String (PascalCase)
**Required**: Yes

Entity name. Must be PascalCase, singular noun.

```yaml
entity: Contact          # ✅ Valid
entity: contact          # ❌ lowercase
entity: Contacts         # ❌ plural
entity: contact_info     # ❌ snake_case
```

### schema
**Type**: String (lowercase)
**Required**: Yes

Database schema for organization.

```yaml
schema: crm             # ✅ Valid
schema: CRM             # ❌ uppercase
schema: customer_rm     # ❌ underscores
```

### description
**Type**: String
**Required**: No

Human-readable entity description.

```yaml
description: "Customer contact information and lead management"
```

### organization
**Type**: String
**Required**: No

Business domain grouping for registry organization.

```yaml
organization: customer   # Groups related entities
```

## 📊 Fields Section

### Basic Field Types

```yaml
fields:
  # Text
  name: text
  email: text
  description: text

  # Numbers
  age: integer
  price: decimal
  count: integer

  # Boolean
  active: boolean
  enabled: boolean

  # Dates/Times
  birthday: date
  created: timestamp
  start_time: time

  # Identifiers
  id: uuid
  external_id: uuid

  # JSON
  settings: jsonb
  metadata: jsonb
```

### Rich Scalar Types

```yaml
fields:
  # Contact information
  email: email
  website: url
  phone: phone

  # Financial
  amount: money
  discount: percentage

  # Physical
  size: dimensions
  weight: weight
  capacity: volume
```

### Composite Types

```yaml
fields:
  # Address structure
  address: address

  # Contact information
  contact: contact_info

  # Geographic location
  location: geo_location

  # Money with currency
  price: money_amount
```

### Reference Types

```yaml
fields:
  # Single references
  company: ref(Company)
  manager: ref(User)
  category: ref(Category)

  # List references (creates junction tables)
  projects: ref(Project)[]
  skills: text[]
```

### Enum Types

```yaml
fields:
  status: enum(lead, qualified, customer)
  priority: enum(low, medium, high, urgent)
  type: enum(internal, external, partner)
```

### Field Options

```yaml
fields:
  email: text
    nullable: false
    unique: true
    index: true
    default: ""
    min_length: 5
    max_length: 254
    pattern: "^[^@]+@[^@]+\\.[^@]+$"

  age: integer
    nullable: false
    min: 0
    max: 150
    default: 0

  price: decimal
    nullable: false
    min: 0
    precision: 10
    scale: 2

  active: boolean
    nullable: false
    default: true
```

## 🚀 Actions Section

### Action Structure

```yaml
actions:
  - name: action_name
    description: "Human-readable description"
    requires: "permission_expression"
    pattern: "pattern_name"
    config:
      key: value
    steps:
      # Step definitions
```

### Action Properties

#### name
**Type**: String (snake_case)
**Required**: Yes

```yaml
name: qualify_lead
name: create_contact
name: update_status
```

#### description
**Type**: String
**Required**: No

```yaml
description: "Convert a lead to a qualified prospect"
```

#### requires
**Type**: String (permission expression)
**Required**: No

```yaml
requires: caller.can_edit_contact
requires: caller.is_admin
requires: owner.id = caller.id
requires: caller.department = 'sales' AND amount <= 10000
```

#### pattern
**Type**: String
**Required**: No

Reference to a reusable action pattern.

```yaml
pattern: crud_create
pattern: state_machine_transition
```

#### config
**Type**: Object
**Required**: No

Configuration for pattern-based actions.

```yaml
config:
  state_field: status
  transitions:
    draft: submitted
    submitted: approved
```

### Steps Array

Each action contains a `steps` array with step definitions.

## 🔍 Step Types

### Core Steps

#### validate
```yaml
- validate: expression
  error: "error_code"
  message: "Error message"
```

#### if
```yaml
- if: condition
  then:
    - step1
    - step2
  else:
    - step3
```

#### insert
```yaml
- insert: EntityName
  values:
    field1: value1
    field2: value2
```

#### update
```yaml
- update: EntityName SET field1 = value1, field2 = value2
  where: additional_conditions
```

#### delete
```yaml
- delete: EntityName
  hard: false  # Default: soft delete
```

#### call
```yaml
- call: action_name
  args:
    param1: value1
    param2: value2
```

#### notify
```yaml
- notify: recipient(type, template)
  priority: "normal"
  data:
    key: value
```

#### foreach
```yaml
- foreach: collection
  as: item
  steps:
    - validate: item.field > 0
    - update: Entity SET field = item.value
```

### Extended Steps

#### partial_update
```yaml
- partial_update: EntityName
  fields: [field1, field2]
  values:
    field1: new_value1
    field2: new_value2
```

#### duplicate_check
```yaml
- duplicate_check: EntityName
  fields: [field1, field2]
  scope: "active_only"
  error: "duplicate_found"
```

#### call_service
```yaml
- call_service: service_name
  method: "method_name"
  args:
    param1: value1
    param2: value2
  timeout: 30
```

#### aggregate
```yaml
- aggregate: result_name
  group_by: [field1, field2]
  measures:
    sum_field: SUM(field3)
    count_field: COUNT(*)
    avg_field: AVG(field4)
```

#### call_function
```yaml
- call_function: function_name
  args: [arg1, arg2, arg3]
  result: result_variable
```

#### cte
```yaml
- cte: cte_name AS (
    SELECT * FROM table WHERE condition
  )
  steps:
    - validate: EXISTS(SELECT 1 FROM cte_name)
```

#### declare
```yaml
- declare:
    var1: value1
    var2: value2
    var3: SELECT value FROM table
```

#### exception_handling
```yaml
- exception_handling:
    try:
      - step1
      - step2
    catch:
      - step3
      - step4
    finally:
      - step5
```

#### for_query
```yaml
- for_query: SELECT * FROM table WHERE condition
  as: row
  steps:
    - call: process_item
      args:
        id: row.id
```

#### json_build
```yaml
- json_build: result_name
  fields:
    field1: expression1
    field2: expression2
  template: "template_name"
```

#### return_early
```yaml
- return_early:
    success: false
    message: "Error message"
    code: "error_code"
    data:
      key: value
```

#### subquery
```yaml
- subquery: sub_name
  sql: |
    SELECT * FROM table
    WHERE complex_condition
```

#### switch
```yaml
- switch: expression
  cases:
    value1:
      - step1
    value2:
      - step2
  default:
    - step3
```

#### while
```yaml
- while: condition
  steps:
    - step1
    - step2
```

## 🔒 Constraints Section

```yaml
constraints:
  # Unique constraints
  - unique: [field1, field2]
    name: "unique_constraint_name"

  # Check constraints
  - check: "field1 > 0"
    name: "positive_value"

  # Foreign key constraints
  - foreign_key: field1
    references: OtherEntity(pk_field)
    on_delete: CASCADE
```

## 👁️ Projections Section

```yaml
projections:
  # Table view definitions
  - name: detailed_view
    includes: [field1, field2, related.field3]
    excludes: [field4]
    filters:
      - deleted_at IS NULL
      - status = 'active'
    joins:
      - LEFT JOIN related_table ON condition

  # Aggregation projections
  - name: summary_view
    aggregates:
      total_count: COUNT(*)
      avg_value: AVG(field1)
    group_by: [field2, field3]
```

## 🏷️ Identifiers Section

```yaml
identifiers:
  # Pattern-based identifiers
  - field: identifier
    pattern: "PREFIX-{YYYY}-{MM}-{NNN}"
    scope: "entity"
    unique: true

  # Composite identifiers
  - field: code
    components: [category, sequence]
    separator: "-"
    padding: 3
```

## 🎯 Expressions

SpecQL supports rich expressions in validations, conditions, and updates:

### Field References
```yaml
field_name
entity.field_name
related.field_name
```

### Literals
```yaml
"string literal"
123
45.67
true
false
null
```

### Operators
```yaml
# Comparison
= != < > <= >=
IS NULL IS NOT NULL
IN (value1, value2)
BETWEEN min AND max

# Logical
AND OR NOT

# String
LIKE ILIKE
MATCHES "regex"

# Mathematical
+ - * / %
```

### Functions
```yaml
NOW()
CURRENT_DATE
COALESCE(field, default)
EXTRACT(YEAR FROM date_field)
CASE WHEN condition THEN value ELSE other END
```

### Variables
```yaml
$parameter_name
caller.id
owner.email
```

## 📋 Complete Example

```yaml
entity: Contact
schema: crm
description: "Customer contact information and lead management"
organization: customer

fields:
  email: email
    nullable: false
    unique: true

  first_name: text
    nullable: false

  last_name: text

  status: enum(lead, qualified, customer)
    nullable: false
    default: "lead"

  company: ref(Company)

  phone: phone

  notes: text

  created_at: timestamp
    nullable: false
    default: "NOW()"

actions:
  - name: qualify_lead
    description: "Convert a lead to a qualified prospect"
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified', qualified_at = NOW()
      - notify: owner(email, "Contact qualified")

  - name: create_contact
    description: "Create a new contact with validation"
    steps:
      - validate: email IS NOT NULL
        error: "email_required"
      - validate: first_name IS NOT NULL
        error: "first_name_required"
      - duplicate_check: Contact
        fields: [email]
        error: "email_exists"
      - insert: Contact

  - name: update_contact
    requires: caller.can_edit_contact
    steps:
      - partial_update: Contact
        fields: [first_name, last_name, phone, notes]
        values:
          first_name: $first_name
          last_name: $last_name
          phone: $phone
          notes: $notes

constraints:
  - check: "status IN ('lead', 'qualified', 'customer')"
    name: "valid_status"

projections:
  - name: active_contacts
    filters:
      - deleted_at IS NULL
      - status IN ('qualified', 'customer')
    includes: [email, first_name, last_name, company.name]

identifiers:
  - field: identifier
    pattern: "CONT-{YYYY}-{NNN}"
    unique: true
```

## 🚀 Advanced Features

### Pattern References
```yaml
actions:
  - pattern: crud_create
    config:
      fields: [email, first_name, last_name]
      validations:
        - email: required
        - first_name: required

  - pattern: state_machine
    config:
      field: status
      transitions:
        lead: qualified
        qualified: customer
```

### Template Usage
```yaml
actions:
  - name: send_notification
    template: email_notification
    config:
      recipients: [customer.email, manager.email]
      priority: high
```

### Macro Expansion
```yaml
# Define macros for reuse
macros:
  validate_contact: &validate_contact
    - validate: email IS NOT NULL
    - validate: first_name IS NOT NULL

actions:
  - name: create_contact
    steps:
      *validate_contact
      - insert: Contact
```

## 📚 Related Topics

- **[Entity Schema](entity_schema.md)** - Entity definition details
- **[Field Types](field_types.md)** - Complete field type reference
- **[Action Schema](action_schema.md)** - Action definition details
- **[Step Types](step_types.md)** - All available step types