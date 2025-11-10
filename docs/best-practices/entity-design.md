# Entity Design Best Practices

Guidelines for designing SpecQL entities with proper field types, relationships, constraints, and performance considerations.

## Overview

Well-designed entities form the foundation of maintainable SpecQL applications. This guide covers field selection, relationship modeling, constraint design, and performance optimization.

## Entity Naming Conventions

### Entity Names
- Use **PascalCase** for entity names
- Use **singular nouns** (User, not Users)
- Be **descriptive but concise**
- Avoid abbreviations unless industry-standard

```yaml
# ✅ Good
entity: User
entity: Order
entity: Product
entity: Customer

# ❌ Avoid
entity: usr  # Abbreviation
entity: order_table  # Implementation detail
entity: obj  # Too generic
```

### Schema Names
- Use **lowercase** with underscores
- Group related entities by **business domain**
- Keep schemas **focused and cohesive**

```yaml
# ✅ Good - Domain-based schemas
entity: User
schema: identity

entity: Order
schema: sales

entity: Product
schema: catalog

# ❌ Avoid - Technical schemas
entity: User
schema: users_table  # Implementation detail

entity: Order
schema: main_db  # Too generic
```

## Field Design Principles

### Field Types Selection

**Choose the most specific type:**
```yaml
fields:
  # ✅ Specific types
  email: text          # Any text (but we'll validate format)
  price: decimal(10,2) # Precise decimal for money
  quantity: integer    # Whole numbers only
  is_active: boolean   # True/false only
  created_at: timestamptz  # With timezone
  metadata: jsonb      # Structured data

  # ❌ Generic types
  email: text          # OK, but add validation
  price: numeric       # Too generic, use decimal
  quantity: bigint     # Overkill for quantities
  status: text         # Use enum for controlled values
```

### Enum Types for Controlled Values

**Always use enums for controlled vocabularies:**
```yaml
fields:
  # ✅ Enums for controlled values
  status:
    type: enum[pending, active, inactive, suspended]
    default: pending

  priority:
    type: enum[low, medium, high, urgent]
    default: medium

  category:
    type: enum[electronics, clothing, books, home]
```

**Benefits:**
- Type safety at database level
- Prevents invalid values
- Self-documenting
- Better query performance

### Field Naming

**Follow consistent naming patterns:**
```yaml
fields:
  # ✅ Consistent naming
  first_name: text
  last_name: text
  email_address: text
  phone_number: text
  created_at: timestamptz
  updated_at: timestamptz

  # ❌ Inconsistent
  firstname: text      # No underscore
  Email: text          # Wrong case
  phone: text          # Abbreviated
  date_created: timestamptz  # Wrong order
```

### Required vs Optional Fields

**Be explicit about requirements:**
```yaml
fields:
  # Required fields (explicit)
  id:
    type: uuid
    required: true
  email:
    type: text
    required: true
  created_at:
    type: timestamptz
    required: true

  # Optional fields (default)
  phone: text
  middle_name: text
  notes: text
```

**Guidelines:**
- **Required**: Data essential for the entity to function
- **Optional**: Nice-to-have or conditional data
- **Default values**: Use for optional fields when appropriate

## Relationship Modeling

### Foreign Key References

**Use explicit references for relationships:**
```yaml
fields:
  # ✅ Explicit references
  user_id:
    type: ref(User)
    required: true
  order_id:
    type: ref(Order)
    required: true

  # ✅ With additional constraints
  customer_id:
    type: ref(Customer)
    required: true
    indexed: true
```

**Reference benefits:**
- Automatic foreign key constraints
- Type safety
- Navigation in queries
- Cascade options available

### Many-to-Many Relationships

**Use junction entities for complex relationships:**
```yaml
# For User ↔ Role relationship
entity: UserRole
schema: identity
fields:
  user_id: ref(User)
  role_id: ref(Role)
  assigned_at: timestamptz
  assigned_by: ref(User)

constraints:
  - name: unique_user_role
    type: unique
    fields: [user_id, role_id]
```

### Self-Referencing Relationships

**Use for hierarchical data:**
```yaml
entity: Category
schema: catalog
fields:
  name: text
  parent_id: ref(Category)  # Self-reference
  level: integer
  path: text  # Materialized path

constraints:
  - name: no_self_reference
    type: check
    condition: "parent_id != id"
```

## Constraint Design

### Primary Keys

**Use UUIDs for distributed systems:**
```yaml
fields:
  id:
    type: uuid
    required: true
    description: "Primary key"

constraints:
  - name: pk_entity
    type: primary_key
    fields: [id]
```

**Composite primary keys (rare):**
```yaml
entity: OrderItem
fields:
  order_id: ref(Order)
  product_id: ref(Product)
  quantity: integer

constraints:
  - name: pk_order_item
    type: primary_key
    fields: [order_id, product_id]
```

### Unique Constraints

**Enforce business rules:**
```yaml
constraints:
  # ✅ Business uniqueness
  - name: unique_email
    type: unique
    fields: [email]
    error_message: "Email address must be unique"

  - name: unique_customer_contract
    type: unique
    fields: [customer_id, contract_number]
    error_message: "Contract number must be unique per customer"

  # ✅ Scoped uniqueness
  - name: unique_username_per_tenant
    type: unique
    fields: [tenant_id, username]
```

### Check Constraints

**Enforce data integrity:**
```yaml
constraints:
  # ✅ Value ranges
  - name: positive_price
    type: check
    condition: "price > 0"
    error_message: "Price must be positive"

  - name: valid_percentage
    type: check
    condition: "discount_percentage BETWEEN 0 AND 100"
    error_message: "Discount percentage must be between 0 and 100"

  # ✅ Business rules
  - name: end_after_start
    type: check
    condition: "end_date > start_date"
    error_message: "End date must be after start date"

  - name: adult_age
    type: check
    condition: "age >= 18 OR parental_consent = true"
    error_message: "Users under 18 require parental consent"
```

### Foreign Key Constraints

**Maintain referential integrity:**
```yaml
constraints:
  # ✅ Standard foreign keys
  - name: fk_user_department
    type: foreign_key
    fields: [department_id]
    references: "departments(id)"
    error_message: "Referenced department does not exist"

  # ✅ With cascade options
  - name: fk_order_customer
    type: foreign_key
    fields: [customer_id]
    references: "customers(id)"
    on_delete: "RESTRICT"  # Prevent deletion
    on_update: "CASCADE"   # Update references
```

## Indexing Strategy

### Automatic Indexes

**SpecQL creates indexes for:**
- Primary keys (automatic)
- Foreign keys (recommended)
- Unique constraints (automatic)
- Explicit `indexed: true` fields

### Manual Index Configuration

**Add performance indexes:**
```yaml
indexes:
  # ✅ Query-specific indexes
  - name: idx_orders_customer_date
    columns: [customer_id, created_at DESC]
    type: btree

  - name: idx_products_category_price
    columns: [category, price]
    type: btree

  # ✅ Partial indexes
  - name: idx_active_users
    columns: [last_login DESC]
    condition: "status = 'active'"

  # ✅ JSONB indexes
  - name: idx_metadata_tags
    columns: [metadata]
    type: gin
    condition: "metadata ? 'tags'"
```

### Index Types

| Type | Use Case | Performance | Storage |
|------|----------|-------------|---------|
| `btree` | Equality, range queries | Excellent | Medium |
| `hash` | Simple equality | Good | Low |
| `gist` | Complex types, ranges | Good | High |
| `gin` | Arrays, full-text, JSONB | Variable | High |
| `brin` | Large tables, time-series | Good | Low |

## Identifiers and Sequences

### Automatic Identifiers

**Use for user-facing IDs:**
```yaml
identifier:
  pattern: "ORD-{created_at:YYYY}-{sequence:04d}"
  sequence:
    scope: [customer_id]  # Per customer
    group_by: [created_at:YYYY]  # Reset yearly
```

**Benefits:**
- Human-readable
- Collision-resistant
- Business context

### Sequence Configuration

**Control sequence behavior:**
```yaml
identifier:
  # Simple incrementing
  pattern: "USER-{sequence:06d}"

  # Scoped sequences
  pattern: "INV-{tenant_id}-{sequence:04d}"
  sequence:
    scope: [tenant_id]

  # Time-based with grouping
  pattern: "TXN-{created_at:YYYYMM}-{sequence:04d}"
  sequence:
    group_by: [created_at:YYYYMM]
    start_value: 1
```

## Projections and Views

### Materialized Projections

**For complex queries:**
```yaml
projections:
  - name: user_summary
    includes:
      - User: [id, name, email, status]
      - Department: [name as department_name]
      - Role: [name as role_name]
    filters:
      - condition: "status = 'active'"
    refresh:
      materialized: true
      on: [create, update]
```

### Virtual Projections

**For simple joins:**
```yaml
projections:
  - name: order_details
    includes:
      - Order: [id, total, status, created_at]
      - Customer: [name, email]
      - ShippingAddress: [street, city, state]
```

## Partitioning Strategy

### Time-Based Partitioning

**For high-volume time-series data:**
```yaml
partitioning:
  strategy: RANGE
  column: created_at
  intervals: monthly
  retention: "2 years"
```

### List Partitioning

**For categorical data:**
```yaml
partitioning:
  strategy: LIST
  column: region
  intervals: [us-east, us-west, eu-central, ap-southeast]
```

## Performance Optimization

### Field Order

**Optimize for common access patterns:**
```yaml
fields:
  # Frequently accessed fields first
  id: uuid
  status: enum[...]
  created_at: timestamptz

  # Less frequently accessed fields
  metadata: jsonb
  notes: text
```

### Field Types Optimization

**Choose efficient types:**
```yaml
fields:
  # ✅ Efficient types
  is_active: boolean    # 1 byte
  quantity: integer     # 4 bytes
  price: decimal(10,2)  # 8 bytes

  # ❌ Inefficient types
  quantity: bigint      # 8 bytes (overkill)
  price: numeric        # Variable (unpredictable)
  is_active: text       # Variable (wasteful)
```

### JSONB Usage

**Use JSONB appropriately:**
```yaml
fields:
  # ✅ Good uses for JSONB
  preferences: jsonb     # User preferences
  metadata: jsonb        # Extensible data
  tags: jsonb           # Multi-value attributes

  # ❌ Avoid for structured data
  address: jsonb        # Use separate table
  settings: jsonb       # Use typed fields
```

## Security Considerations

### Data Classification

**Mark sensitive fields:**
```yaml
fields:
  ssn:
    type: text
    encrypted: true
    description: "Social Security Number"

  credit_card:
    type: text
    masked: true
    description: "Credit card number"
```

### Access Control

**Design for row-level security:**
```yaml
# Entity-level permissions
entity: Order
schema: sales

# Fields include tenant isolation
fields:
  tenant_id: uuid  # For RLS
  customer_id: ref(Customer)
  # ... other fields
```

## Migration and Evolution

### Backward Compatibility

**Plan for schema evolution:**
```yaml
entity: User
version: "2.0.0"

# New fields (additive changes)
fields:
  phone: text        # New optional field
  preferences: jsonb # New flexible field

# Migration notes
migration:
  from_version: "1.0.0"
  changes:
    - add_field: phone
    - add_field: preferences
    - add_index: idx_user_phone
```

### Deprecation Strategy

**Handle deprecated fields:**
```yaml
fields:
  old_field:
    type: text
    deprecated: true
    deprecated_since: "2.0.0"
    replacement: "new_field"
    description: "Use new_field instead"
```

## Common Design Patterns

### Audit Trail Entity

```yaml
entity: AuditLog
schema: audit
fields:
  entity_type: text
  entity_id: uuid
  action: enum[create, update, delete]
  old_values: jsonb
  new_values: jsonb
  changed_by: uuid
  changed_at: timestamptz

indexes:
  - name: idx_audit_entity
    columns: [entity_type, entity_id, changed_at DESC]
```

### Soft Delete Pattern

```yaml
entity: Document
fields:
  # Standard fields
  title: text
  content: text

  # Soft delete fields
  is_deleted: boolean
  deleted_at: timestamptz
  deleted_by: uuid

constraints:
  - name: deleted_with_metadata
    type: check
    condition: "(is_deleted = true AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL) OR (is_deleted = false AND deleted_at IS NULL AND deleted_by IS NULL)"
```

### Versioned Entity

```yaml
entity: Contract
fields:
  # Current version data
  title: text
  content: text
  version: integer

  # Version history
  version_history: jsonb  # Array of previous versions

actions:
  - name: create_new_version
    pattern: crud/update
    config:
      partial_updates: true
      track_updated_fields: true
```

## Validation Checklist

### Entity Design Checklist

- [ ] Entity name follows PascalCase convention
- [ ] Schema name reflects business domain
- [ ] All fields have appropriate types
- [ ] Required fields are marked as such
- [ ] Enums used for controlled values
- [ ] Foreign keys use `ref()` syntax
- [ ] Constraints enforce business rules
- [ ] Indexes support query patterns
- [ ] Identifiers are user-friendly
- [ ] Projections defined for complex queries

### Performance Checklist

- [ ] Primary key is efficient (UUID preferred)
- [ ] Foreign keys are indexed
- [ ] Large tables are partitioned
- [ ] JSONB fields have appropriate indexes
- [ ] Field order optimizes access patterns
- [ ] No unnecessary large fields in hot path

### Security Checklist

- [ ] Sensitive data is properly typed
- [ ] Row-level security fields included
- [ ] Access patterns consider tenant isolation
- [ ] Audit fields present where needed

---

**See Also:**
- [Pattern Selection Best Practices](pattern-selection.md)
- [Testing Strategy](testing-strategy.md)
- [Performance Best Practices](performance.md)
- [YAML Schema Reference](../reference/yaml-schema.md)