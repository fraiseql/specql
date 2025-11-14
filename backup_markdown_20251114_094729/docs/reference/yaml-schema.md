# YAML Schema Reference

Complete reference for SpecQL entity definition YAML schema, including all supported fields, types, patterns, and configuration options.

## Overview

SpecQL entities are defined using a declarative YAML schema that describes database structure, business logic, and behavior. The schema supports progressive enhancement - start simple and add complexity as needed.

## Basic Entity Structure

```yaml
entity: EntityName
schema: schema_name
description: "Human-readable description"

fields:
  field_name: field_type
  # ... more fields

actions:
  - name: action_name
    pattern: pattern/type
    config:
      # Pattern-specific configuration
```

## Schema Reference

### Root Level Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `entity` | string | Yes | Entity name (PascalCase) |
| `schema` | string | Yes | Database schema name |
| `description` | string | No | Human-readable description |
| `version` | string | No | Entity version for migrations |
| `tags` | array | No | Tags for organization/filtering |

### Fields Definition

#### Field Types

| Type | PostgreSQL Type | Description | Example |
|------|----------------|-------------|---------|
| `text` | `text` | Variable-length string | `name: text` |
| `varchar(n)` | `varchar(n)` | Fixed-length string | `code: varchar(10)` |
| `integer` | `integer` | 32-bit integer | `count: integer` |
| `bigint` | `bigint` | 64-bit integer | `user_count: bigint` |
| `decimal` | `decimal` | Arbitrary precision decimal | `price: decimal` |
| `decimal(p,s)` | `decimal(p,s)` | Decimal with precision | `price: decimal(10,2)` |
| `boolean` | `boolean` | True/false value | `active: boolean` |
| `date` | `date` | Date without time | `birth_date: date` |
| `timestamp` | `timestamp` | Date and time | `created_at: timestamp` |
| `timestamptz` | `timestamptz` | Timestamp with timezone | `updated_at: timestamptz` |
| `uuid` | `uuid` | Universally unique identifier | `id: uuid` |
| `jsonb` | `jsonb` | JSON data | `metadata: jsonb` |
| `enum[...]` | `enum` | Enumerated values | `status: enum[active,inactive]` |
| `ref(Entity)` | `uuid` | Foreign key reference | `user_id: ref(User)` |

#### Field Properties

```yaml
fields:
  field_name:
    type: field_type
    required: true|false          # Default: false
    default: default_value        # Default value
    description: "Field description"
    constraints: [...]           # Additional constraints
    indexed: true|false          # Create index (default: false)
    unique: true|false           # Unique constraint (default: false)
```

**Field Examples:**
```yaml
fields:
  # Simple fields
  name: text
  email: text
  age: integer
  price: decimal(10,2)
  active: boolean
  created_at: timestamp

  # Fields with properties
  user_id:
    type: ref(User)
    required: true
    description: "Reference to the user who owns this record"

  status:
    type: enum[pending,active,inactive]
    default: pending
    indexed: true
    description: "Current status of the entity"

  metadata:
    type: jsonb
    default: "{}"
    description: "Additional metadata as JSON"
```

### Constraints

```yaml
constraints:
  - name: constraint_name
    type: unique|check|foreign_key
    fields: [field1, field2]      # For unique constraints
    condition: "sql_condition"    # For check constraints
    references: "table(column)"   # For foreign keys
    deferrable: true|false        # Default: false
    check_on_create: true|false   # Validate on create (default: true)
    error_message: "Custom error message"
```

**Constraint Examples:**
```yaml
constraints:
  # Unique constraint
  - name: unique_email
    type: unique
    fields: [email]
    error_message: "Email address must be unique"

  # Check constraint
  - name: positive_price
    type: check
    condition: "price > 0"
    error_message: "Price must be positive"

  # Multi-column unique
  - name: unique_customer_contract
    type: unique
    fields: [customer_id, contract_number]
    error_message: "Contract number must be unique per customer"

  # Foreign key (alternative to ref() type)
  - name: fk_user
    type: foreign_key
    fields: [user_id]
    references: "users(id)"
    error_message: "Referenced user does not exist"
```

### Identifiers

```yaml
identifier:
  pattern: "PREFIX-{field:format}-{sequence:format}"
  sequence:
    scope: [field1, field2]       # Fields that scope the sequence
    group_by: [field:format]      # Additional grouping
    start_value: 1               # Default: 1
    increment: 1                # Default: 1
  recalculate_on: [create, update] # When to recalculate (default: [create])
  fields: [field1, field2]       # Fields to include in pattern
```

**Identifier Examples:**
```yaml
identifier:
  # Simple sequence: INV-001, INV-002, ...
  pattern: "INV-{sequence:03d}"

  # Date-based: ORD-2024-001, ORD-2024-002, ...
  pattern: "ORD-{created_at:YYYY}-{sequence:03d}"
  sequence:
    group_by: [created_at:YYYY]

  # Scoped by customer: CUST001-001, CUST001-002, CUST002-001, ...
  pattern: "{customer_id}-{sequence:03d}"
  sequence:
    scope: [customer_id]

  # Complex: PRJ-2024-Q1-001, PRJ-2024-Q1-002, ...
  pattern: "PRJ-{created_at:YYYY}-{created_at:Q}-{sequence:03d}"
  sequence:
    group_by: [created_at:YYYY, created_at:Q]
```

### Projections

```yaml
projections:
  - name: projection_name
    includes:
      - entity.field: [subfield1, subfield2]
      - related_entity: [field1, field2]
    filters:
      - condition: "sql_condition"
        parameters: [param1, param2]
    refresh:
      on: [create, update, delete]  # Default: [create, update]
      materialized: true|false     # Default: false
```

**Projection Examples:**
```yaml
projections:
  # Simple projection
  - name: user_profile
    includes:
      - User: [id, name, email]
      - Department: [id, name]

  # Filtered projection
  - name: active_orders
    includes:
      - Order: [id, total, status, created_at]
      - Customer: [name, email]
    filters:
      - condition: "status IN ('pending', 'processing')"
    refresh:
      on: [create, update]

  # Materialized view
  - name: sales_summary
    includes:
      - Order: [total, created_at:month]
    refresh:
      materialized: true
      on: [create]  # Only refresh on new orders
```

### Actions

Actions define the operations that can be performed on entities.

#### Action Structure

```yaml
actions:
  - name: action_name
    pattern: pattern/type
    requires: permission_expression
    config:
      # Pattern-specific configuration
    description: "Action description"
    tags: [tag1, tag2]
```

#### Pattern Types

**CRUD Patterns:**
```yaml
# Create
- name: create_entity
  pattern: crud/create
  config:
    duplicate_check:
      fields: [unique_field]
      error_message: "Duplicate found"

# Update
- name: update_entity
  pattern: crud/update
  config:
    partial_updates: true
    track_updated_fields: true

# Delete
- name: delete_entity
  pattern: crud/delete
  config:
    supports_hard_delete: true
    check_dependencies:
      - entity: RelatedEntity
        field: foreign_key_field
```

**State Machine Patterns:**
```yaml
# Simple transition
- name: approve_entity
  pattern: state_machine/transition
  config:
    from_states: [pending]
    to_state: approved
    validation_checks:
      - condition: "amount > 0"
        error: "invalid_amount"

# Guarded transition
- name: approve_large_entity
  pattern: state_machine/guarded_transition
  config:
    from_states: [pending]
    to_state: approved
    guards:
      - name: budget_check
        condition: "amount <= budget_limit"
        error: "insufficient_budget"
```

**Validation Patterns:**
```yaml
- name: validate_entity
  pattern: validation/validation_chain
  config:
    validations:
      - name: required_field
        field: name
        condition: "input_data.name IS NOT NULL"
        message: "Name is required"
    collect_all_errors: true
```

**Batch Operation Patterns:**
```yaml
- name: bulk_update_entities
  pattern: batch/bulk_operation
  config:
    batch_input: entity_updates
    operation:
      action: update
      entity: Entity
      set:
        status: $item.status
      where: "id = $item.id"
    error_handling: continue_on_error
```

**Multi-Entity Patterns:**
```yaml
# Coordinated update
- name: create_order_with_items
  pattern: multi_entity/coordinated_update
  config:
    entities:
      - entity: Order
        operation: insert
        fields: [customer_id, total]
      - entity: OrderItem
        operation: insert
        fields: [order_id, product_id, quantity]

# Saga orchestration
- name: process_order_fulfillment
  pattern: multi_entity/saga_orchestrator
  config:
    saga_steps:
      - name: create_order
        action: insert
        entity: Order
      - name: reserve_inventory
        action: update
        entity: Product
        compensation:
          action: update
          entity: Product
```

**Composite Patterns:**
```yaml
# Workflow orchestration
- name: process_requisition
  pattern: composite/workflow_orchestrator
  config:
    workflow:
      - step: validate_requisition
        action: validate
      - step: check_budget
        action: call_external
        service: budget_service
      - step: create_approval
        action: insert
        entity: Approval

# Conditional workflow
- name: process_based_on_amount
  pattern: composite/conditional_workflow
  config:
    conditions:
      - if: "amount <= 1000"
        then:
          - action: auto_approve
      - if: "amount > 1000"
        then:
          - action: require_approval
```

### Permissions

```yaml
actions:
  - name: admin_action
    requires: caller.is_admin

  - name: user_action
    requires: caller.id = entity.user_id

  - name: team_action
    requires: caller.team_id = entity.team_id OR caller.is_admin

  - name: complex_permission
    requires: >
      (caller.is_admin OR
       caller.id = entity.created_by OR
       EXISTS (SELECT 1 FROM team_members
               WHERE team_id = entity.team_id
               AND user_id = caller.id))
```

### Indexes

```yaml
indexes:
  - name: idx_entity_field
    columns: [field_name]
    type: btree|hash|gist|gin  # Default: btree
    unique: true|false        # Default: false
    condition: "sql_condition" # Partial index
    fillfactor: 90           # Default: 90

  - name: idx_composite
    columns: [field1, field2 DESC]
    type: btree

  - name: idx_jsonb
    columns: [metadata]
    type: gin
    condition: "metadata IS NOT NULL"
```

**Index Examples:**
```yaml
indexes:
  # Single column index
  - name: idx_user_email
    columns: [email]
    unique: true

  # Composite index
  - name: idx_order_customer_date
    columns: [customer_id, created_at DESC]

  # Partial index
  - name: idx_active_users
    columns: [last_login DESC]
    condition: "status = 'active'"

  # JSONB index
  - name: idx_metadata_tags
    columns: [metadata]
    type: gin
    condition: "metadata ? 'tags'"
```

### Partitioning

```yaml
partitioning:
  strategy: RANGE|LIST|HASH
  column: partition_column
  intervals: monthly|weekly|daily|[custom_intervals]
  retention: "90 days"  # For time-based partitions
```

**Partitioning Examples:**
```yaml
partitioning:
  # Monthly partitions by date
  strategy: RANGE
  column: created_at
  intervals: monthly
  retention: "2 years"

  # List partitions by region
  strategy: LIST
  column: region
  intervals: [us-east, us-west, eu-central, ap-southeast]

  # Hash partitions for even distribution
  strategy: HASH
  column: id
  intervals: 8  # 8 partitions
```

### Hooks

```yaml
hooks:
  before_create:
    - name: set_defaults
      action: set_default_values
    - name: validate_business_rules
      action: custom_validation

  after_update:
    - name: refresh_cache
      action: invalidate_cache
    - name: send_notifications
      action: notify_subscribers

  before_delete:
    - name: check_dependencies
      action: validate_no_dependencies
```

### Rich Types

```yaml
rich_types:
  - name: address
    fields:
      street: text
      city: text
      state: text
      zip_code: text
    validations:
      - condition: "zip_code ~ '^\d{5}$'"

  - name: phone_number
    base_type: text
    validations:
      - condition: "value ~ '^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'"
```

## Complete Entity Example

```yaml
entity: Order
schema: sales
description: "Customer order with comprehensive business logic"
version: "1.0.0"
tags: [ecommerce, transaction]

fields:
  customer_id:
    type: ref(Customer)
    required: true
    description: "Customer who placed the order"

  order_number:
    type: text
    unique: true
    description: "Human-readable order number"

  status:
    type: enum[pending,confirmed,shipped,delivered,cancelled]
    default: pending
    indexed: true
    description: "Current order status"

  total_amount:
    type: decimal(10,2)
    required: true
    description: "Total order amount"

  shipping_address:
    type: jsonb
    required: true
    description: "Shipping address as JSON"

  created_at:
    type: timestamptz
    default: now()

  updated_at:
    type: timestamptz
    default: now()

constraints:
  - name: positive_total
    type: check
    condition: "total_amount > 0"
    error_message: "Order total must be positive"

  - name: valid_status_transition
    type: check
    condition: "status IN ('pending','confirmed','shipped','delivered','cancelled')"
    error_message: "Invalid order status"

identifier:
  pattern: "ORD-{created_at:YYYYMMDD}-{sequence:04d}"

projections:
  - name: order_summary
    includes:
      - Order: [id, order_number, status, total_amount, created_at]
      - Customer: [name, email]
    refresh:
      on: [create, update]

indexes:
  - name: idx_order_customer_status
    columns: [customer_id, status, created_at DESC]

  - name: idx_order_date
    columns: [created_at]
    type: brin

partitioning:
  strategy: RANGE
  column: created_at
  intervals: monthly
  retention: "3 years"

actions:
  # CRUD operations
  - name: create_order
    pattern: crud/create
    requires: caller.can_create_orders
    description: "Create a new customer order"

  - name: update_order
    pattern: crud/update
    requires: caller.is_order_owner OR caller.can_manage_orders
    config:
      partial_updates: true
      allowed_fields: [shipping_address, notes]

  - name: cancel_order
    pattern: crud/delete
    requires: caller.is_order_owner OR caller.can_manage_orders
    config:
      supports_hard_delete: false

  # State machine transitions
  - name: confirm_order
    pattern: state_machine/transition
    requires: caller.can_confirm_orders
    config:
      from_states: [pending]
      to_state: confirmed
      validation_checks:
        - condition: "total_amount <= 50000"
          error: "order_too_large"
      side_effects:
        - entity: OrderEvent
          insert:
            order_id: v_order_id
            event_type: confirmed
            event_data: input_data

  - name: ship_order
    pattern: state_machine/guarded_transition
    requires: caller.can_ship_orders
    config:
      from_states: [confirmed]
      to_state: shipped
      guards:
        - name: inventory_available
          condition: "check_inventory_availability(v_order_id)"
          error: "insufficient_inventory"
      input_fields:
        - name: tracking_number
          type: text
          required: true

  # Business logic
  - name: calculate_shipping
    pattern: validation/validation_chain
    config:
      validations:
        - name: valid_address
          condition: "jsonb_typeof(shipping_address->'street') = 'string'"
          message: "Shipping address must include street"
        - name: supported_region
          condition: "shipping_address->>'country' IN ('US', 'CA', 'MX')"
          message: "Shipping not available to this country"

  # Batch operations
  - name: bulk_update_status
    pattern: batch/bulk_operation
    requires: caller.can_manage_orders
    config:
      batch_input: status_updates
      operation:
        action: update
        entity: Order
        set:
          status: $item.status
          updated_at: now()
        where: "id = $item.id AND status = $item.from_status"
      return_summary: true

hooks:
  before_create:
    - name: generate_order_number
      action: set_order_number
  after_update:
    - name: send_notifications
      action: notify_status_change
```

## Schema Validation

SpecQL validates entity definitions against the schema:

```bash
# Validate single entity
specql validate entities/order.yaml

# Validate all entities
specql validate entities/

# Validate with strict mode
specql validate --strict entities/order.yaml
```

## Migration Support

```yaml
# Versioned entity for migrations
entity: Order
schema: sales
version: "2.0.0"

# Migration-specific fields
migration:
  from_version: "1.0.0"
  changes:
    - add_field: shipping_method
    - modify_field: total_amount (increase precision)
    - add_index: idx_order_shipping_method
    - add_constraint: check_positive_total
```

## Best Practices

### Entity Design
- Use descriptive names for entities and fields
- Prefer enum types over boolean flags for status
- Use JSONB for flexible metadata fields
- Define constraints at the schema level when possible

### Field Organization
- Group related fields together
- Use consistent naming conventions
- Add descriptions for complex fields
- Consider indexing requirements early

### Action Patterns
- Start with basic CRUD patterns
- Add state machines for status transitions
- Use validation patterns for business rules
- Consider batch operations for bulk updates

### Performance Considerations
- Index foreign key columns
- Use appropriate index types (B-tree, BRIN, GIN)
- Consider partitioning for large tables
- Use projections for complex queries

---

**See Also:**
- [Pattern Library API](pattern-library-api.md)
- [Test Generation API](test-generation-api.md)
- [Best Practices: Entity Design](../best-practices/entity-design.md)
- [CLI Reference](../reference/cli-reference.md)