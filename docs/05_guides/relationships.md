# Relationships Guide

> **Master entity relationships in SpecQL—foreign keys, cascading, and complex patterns**

## Overview

SpecQL handles relationships declaratively using the `ref()` type. The framework automatically:
- ✅ Creates foreign key constraints
- ✅ Generates indexes on FK columns
- ✅ Handles Trinity pattern resolution (UUID → INTEGER)
- ✅ Enables cross-schema relationships
- ✅ Supports cascading operations

**Zero SQL required.**

---

## Quick Start

### One-to-Many Relationship

```yaml
entity: Contact
schema: crm
fields:
  email: email!
  company: ref(Company)!  # Many contacts → one company
```

**Generated SQL**:
```sql
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,

    email TEXT NOT NULL,
    fk_company INTEGER NOT NULL,  -- Foreign key column

    CONSTRAINT fk_contact_company
        FOREIGN KEY (fk_company)
        REFERENCES crm.tb_company(pk_company)
        ON DELETE RESTRICT
);

-- Auto-generated index
CREATE INDEX idx_tb_contact_company ON crm.tb_contact (fk_company);
```

---

## Relationship Types

### One-to-Many (Most Common)

**Pattern**: Multiple entities reference one parent

```yaml
# Company entity (parent)
entity: Company
schema: crm
fields:
  name: text!
  website: url

---

# Contact entity (child)
entity: Contact
schema: crm
fields:
  email: email!
  company: ref(Company)!  # Many contacts belong to one company
```

**Usage in Actions**:
```yaml
actions:
  - name: get_company_contacts
    steps:
      - query: Contact WHERE company = $company_id
        result: $contacts
      - return: $contacts
```

**GraphQL**:
```graphql
type Contact {
  id: ID!
  email: String!
  company: Company!  # Resolved via foreign key
}

type Company {
  id: ID!
  name: String!
  contacts: [Contact!]!  # Reverse relationship (if configured)
}
```

---

### Many-to-Many (Junction Table)

**Pattern**: Entities relate through an intermediate table

```yaml
# Product entity
entity: Product
schema: catalog
fields:
  name: text!
  price: money!

---

# Order entity
entity: Order
schema: sales
fields:
  customer: ref(Customer)!
  status: enum(pending, shipped, delivered)

---

# OrderItem entity (junction table)
entity: OrderItem
schema: sales
fields:
  order: ref(Order)!
  product: ref(Product)!
  quantity: integer(1)!
  unit_price: money!

unique_together:
  - [order, product]  # Prevent duplicate products in same order
```

**Generated SQL**:
```sql
CREATE TABLE sales.tb_order_item (
    pk_order_item INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,

    fk_order INTEGER NOT NULL,
    fk_product INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 1),
    unit_price NUMERIC(19,4) NOT NULL,

    CONSTRAINT fk_order_item_order
        FOREIGN KEY (fk_order)
        REFERENCES sales.tb_order(pk_order)
        ON DELETE CASCADE,  -- Delete items when order deleted

    CONSTRAINT fk_order_item_product
        FOREIGN KEY (fk_product)
        REFERENCES catalog.tb_product(pk_product)
        ON DELETE RESTRICT,  -- Prevent deleting products with orders

    CONSTRAINT uq_order_item_order_product
        UNIQUE (fk_order, fk_product)
);

CREATE INDEX idx_tb_order_item_order ON sales.tb_order_item (fk_order);
CREATE INDEX idx_tb_order_item_product ON sales.tb_order_item (fk_product);
```

---

### Self-Referencing (Hierarchies)

**Pattern**: Entity references itself (e.g., manager → employee)

```yaml
entity: Employee
schema: hr
fields:
  name: text!
  email: email!
  manager: ref(Employee)  # Optional self-reference
  department: ref(Department)!
```

**Generated SQL**:
```sql
CREATE TABLE hr.tb_employee (
    pk_employee INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,

    name TEXT NOT NULL,
    email TEXT NOT NULL,
    fk_manager INTEGER,  -- Self-referencing FK
    fk_department INTEGER NOT NULL,

    CONSTRAINT fk_employee_manager
        FOREIGN KEY (fk_manager)
        REFERENCES hr.tb_employee(pk_employee)
        ON DELETE SET NULL,  -- Manager leaves → set to NULL

    CONSTRAINT fk_employee_department
        FOREIGN KEY (fk_department)
        REFERENCES hr.tb_department(pk_department)
        ON DELETE RESTRICT
);

CREATE INDEX idx_tb_employee_manager ON hr.tb_employee (fk_manager);
CREATE INDEX idx_tb_employee_department ON hr.tb_employee (fk_department);
```

**Querying Hierarchies**:
```sql
-- Recursive CTE to get all reports under a manager
WITH RECURSIVE reports AS (
    SELECT pk_employee, name, fk_manager, 1 as level
    FROM hr.tb_employee
    WHERE id = '550e8400-e29b-41d4-a716-446655440000'  -- Manager UUID

    UNION ALL

    SELECT e.pk_employee, e.name, e.fk_manager, r.level + 1
    FROM hr.tb_employee e
    INNER JOIN reports r ON e.fk_manager = r.pk_employee
)
SELECT * FROM reports;
```

---

## Cross-Schema Relationships

### Multi-Tenant → Shared

**Pattern**: Tenant-specific entity references shared catalog

```yaml
# Shared catalog (no tenant_id)
entity: Product
schema: catalog  # Tier: shared
fields:
  name: text!
  price: money!

---

# Multi-tenant order (has tenant_id)
entity: Order
schema: sales  # Tier: multi_tenant
fields:
  customer: ref(Customer)!
  product: ref(Product)!  # Cross-schema reference
  quantity: integer(1)!
```

**Generated SQL**:
```sql
-- Shared catalog schema (NO tenant_id)
CREATE TABLE catalog.tb_product (
    pk_product INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC(19,4) NOT NULL
);

-- Multi-tenant sales schema (WITH tenant_id)
CREATE TABLE sales.tb_order (
    pk_order INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,

    tenant_id UUID NOT NULL,  -- Auto-added for multi-tenant
    fk_customer INTEGER NOT NULL,
    fk_product INTEGER NOT NULL,  -- References shared catalog
    quantity INTEGER NOT NULL,

    CONSTRAINT fk_order_customer
        FOREIGN KEY (fk_customer)
        REFERENCES sales.tb_customer(pk_customer)
        ON DELETE RESTRICT,

    CONSTRAINT fk_order_product
        FOREIGN KEY (fk_product)
        REFERENCES catalog.tb_product(pk_product)
        ON DELETE RESTRICT
);

-- RLS policy for multi-tenant schema
ALTER TABLE sales.tb_order ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON sales.tb_order
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

---

## Cascading Behavior

### DELETE Cascades

**Default**: `ON DELETE RESTRICT` (prevent deletion if referenced)

**Custom Cascades**:
```yaml
entity: Order
schema: sales
fields:
  customer: ref(Customer)!
  items: ref(OrderItem)
    on_delete: cascade  # Delete order → delete items

entity: OrderItem
schema: sales
fields:
  order: ref(Order)!
    on_delete: cascade  # Delete order → delete items
  product: ref(Product)!
    on_delete: restrict  # Prevent deleting products with orders
```

**Generated SQL**:
```sql
CONSTRAINT fk_order_item_order
    FOREIGN KEY (fk_order)
    REFERENCES sales.tb_order(pk_order)
    ON DELETE CASCADE  -- Cascade deletes

CONSTRAINT fk_order_item_product
    FOREIGN KEY (fk_product)
    REFERENCES catalog.tb_product(pk_product)
    ON DELETE RESTRICT  -- Prevent deletion
```

**Available Cascades**:
- `restrict` (default) - Prevent deletion if referenced
- `cascade` - Delete referenced records
- `set_null` - Set FK to NULL (requires optional field)
- `set_default` - Set FK to default value

---

### UPDATE Cascades

```yaml
entity: Employee
schema: hr
fields:
  manager: ref(Employee)
    on_update: cascade  # Update manager ID → cascade to reports
```

**Generated SQL**:
```sql
CONSTRAINT fk_employee_manager
    FOREIGN KEY (fk_manager)
    REFERENCES hr.tb_employee(pk_employee)
    ON DELETE SET NULL
    ON UPDATE CASCADE
```

---

## Advanced Patterns

### Polymorphic Relationships (Type Discriminator)

**Pattern**: Reference multiple entity types

```yaml
entity: Comment
schema: social
fields:
  content: text!
  commentable_type: enum(Post, Photo, Video)!
  commentable_id: uuid!
  author: ref(User)!
```

**Usage in Actions**:
```yaml
actions:
  - name: add_comment
    params:
      commentable_type: enum(Post, Photo, Video)!
      commentable_id: uuid!
      content: text!
    steps:
      # Validate reference exists based on type
      - if: $commentable_type = 'Post'
        then:
          - validate: exists(Post WHERE id = $commentable_id)
            error: "post_not_found"
      - if: $commentable_type = 'Photo'
        then:
          - validate: exists(Photo WHERE id = $commentable_id)
            error: "photo_not_found"

      - insert: Comment VALUES (
          commentable_type: $commentable_type,
          commentable_id: $commentable_id,
          content: $content
        )
```

---

### Composite Foreign Keys

**Pattern**: Multi-column foreign keys

```yaml
entity: OrderItem
schema: sales
fields:
  order_number: text!
  order_date: date!
  product: ref(Product)!

composite_foreign_keys:
  - columns: [order_number, order_date]
    references: Order(order_number, order_date)
```

**Generated SQL**:
```sql
CONSTRAINT fk_order_item_order
    FOREIGN KEY (order_number, order_date)
    REFERENCES sales.tb_order(order_number, order_date)
    ON DELETE CASCADE
```

---

### Conditional Relationships

**Pattern**: FK depends on another field value

```yaml
entity: Payment
schema: billing
fields:
  payment_type: enum(invoice, subscription)!
  invoice: ref(Invoice)
    required_if: payment_type = 'invoice'
  subscription: ref(Subscription)
    required_if: payment_type = 'subscription'
```

**Validation in Actions**:
```yaml
actions:
  - name: create_payment
    steps:
      - validate: |
          (payment_type = 'invoice' AND invoice IS NOT NULL) OR
          (payment_type = 'subscription' AND subscription IS NOT NULL)
        error: "invalid_payment_reference"
```

---

## Querying Relationships

### Join Patterns in Actions

**Simple Join**:
```yaml
actions:
  - name: get_contact_with_company
    params:
      contact_id: uuid!
    steps:
      - query: |
          SELECT c.*, comp.name as company_name
          FROM Contact c
          INNER JOIN Company comp ON c.company = comp.id
          WHERE c.id = $contact_id
        result: $contact
      - return: $contact
```

**Multiple Joins**:
```yaml
actions:
  - name: get_order_details
    params:
      order_id: uuid!
    steps:
      - query: |
          SELECT
            o.*,
            c.name as customer_name,
            oi.quantity,
            p.name as product_name
          FROM Order o
          INNER JOIN Customer c ON o.customer = c.id
          INNER JOIN OrderItem oi ON oi.order = o.id
          INNER JOIN Product p ON oi.product = p.id
          WHERE o.id = $order_id
        result: $order_details
      - return: $order_details
```

---

### Trinity Pattern Resolution in Joins

SpecQL auto-generates helper functions for UUID ↔ INTEGER conversion:

```sql
-- Auto-generated helpers
CREATE FUNCTION crm.contact_pk(p_id UUID) RETURNS INTEGER AS $$
    SELECT pk_contact FROM crm.tb_contact WHERE id = p_id;
$$ LANGUAGE SQL STABLE;

CREATE FUNCTION crm.contact_id(p_pk INTEGER) RETURNS UUID AS $$
    SELECT id FROM crm.tb_contact WHERE pk_contact = p_pk;
$$ LANGUAGE SQL STABLE;
```

**Usage in Custom SQL**:
```sql
-- Join using UUID (slow)
SELECT * FROM tb_contact c
INNER JOIN tb_company co ON c.fk_company = company_pk(co.id);

-- Join using INTEGER (fast, recommended)
SELECT * FROM tb_contact c
INNER JOIN tb_company co ON c.fk_company = co.pk_company;
```

**SpecQL auto-uses INTEGER joins** in generated code for 3x performance boost.

---

## GraphQL Integration

### Nested Queries

**SpecQL YAML**:
```yaml
entity: Contact
fields:
  email: email!
  company: ref(Company)!

entity: Company
fields:
  name: text!
```

**Generated GraphQL**:
```graphql
type Contact {
  id: ID!
  email: String!
  company: Company!  # Nested object
}

type Company {
  id: ID!
  name: String!
}

type Query {
  contact(id: ID!): Contact
  contacts(where: ContactFilter): [Contact!]!
}
```

**Frontend Query**:
```typescript
const GET_CONTACT = gql`
  query GetContact($id: ID!) {
    contact(id: $id) {
      id
      email
      company {
        id
        name
        website
      }
    }
  }
`;
```

---

### Reverse Relationships (One-to-Many)

**Configure in Entity**:
```yaml
entity: Company
schema: crm
fields:
  name: text!

reverse_relationships:
  - name: contacts
    entity: Contact
    foreign_key: company
```

**Generated GraphQL**:
```graphql
type Company {
  id: ID!
  name: String!
  contacts: [Contact!]!  # Reverse relationship
}
```

**Frontend Query**:
```typescript
const GET_COMPANY_CONTACTS = gql`
  query GetCompanyContacts($id: ID!) {
    company(id: $id) {
      id
      name
      contacts {
        id
        email
        firstName
        lastName
      }
    }
  }
`;
```

---

## Performance Optimization

### Index Strategy

**SpecQL auto-creates indexes on**:
- ✅ Foreign key columns (`fk_*`)
- ✅ Multi-tenant `tenant_id`
- ✅ Enum fields
- ✅ Composite unique constraints

**Manual Index (if needed)**:
```yaml
entity: Order
schema: sales
fields:
  customer: ref(Customer)!
  status: enum(pending, shipped, delivered)!
  created_at: datetime!

indexes:
  - columns: [customer, status]
    name: idx_order_customer_status
  - columns: [created_at]
    type: brin  # Block Range Index for time-series
```

---

### Join Performance Tips

1. **Use INTEGER joins** (Trinity pattern handles this automatically)
2. **Index foreign keys** (SpecQL does this automatically)
3. **Avoid N+1 queries** - use batch queries or GraphQL data loaders
4. **Denormalize when needed** - add computed fields for frequent joins

**Example Denormalization**:
```yaml
entity: Order
schema: sales
fields:
  customer: ref(Customer)!
  customer_name: text!  # Denormalized for performance

actions:
  - name: create_order
    steps:
      - query: Customer WHERE id = $customer_id
        result: $customer
      - insert: Order VALUES (
          customer: $customer_id,
          customer_name: $customer.name  # Denormalize
        )
```

---

## Best Practices

### ✅ DO

**Use `ref()` for all relationships**:
```yaml
fields:
  company: ref(Company)!  # Good
```

**Set appropriate cascades**:
```yaml
fields:
  order: ref(Order)!
    on_delete: cascade  # Delete order → delete items
```

**Index foreign keys** (SpecQL does this automatically):
```yaml
# No manual index needed - auto-generated
```

**Use Trinity pattern joins** (INTEGER, not UUID):
```sql
-- SpecQL auto-generates efficient INTEGER joins
INNER JOIN tb_company ON fk_company = pk_company
```

---

### ❌ DON'T

**Don't use raw UUID joins**:
```sql
-- Slow: UUID comparison
INNER JOIN tb_company ON company_id = id

-- Fast: INTEGER join (SpecQL default)
INNER JOIN tb_company ON fk_company = pk_company
```

**Don't skip foreign key constraints**:
```yaml
# Bad: Manual UUID field without constraint
fields:
  company_id: uuid!  # No referential integrity

# Good: Use ref()
fields:
  company: ref(Company)!  # FK constraint + index
```

**Don't create circular dependencies**:
```yaml
# Bad: A → B → A
entity: User
fields:
  primary_account: ref(Account)!

entity: Account
fields:
  owner: ref(User)!  # Circular dependency!

# Good: One direction only
entity: User
fields:
  # No reference to Account

entity: Account
fields:
  owner: ref(User)!
```

---

## Troubleshooting

### Error: "Foreign key constraint violation"

**Cause**: Trying to delete/update referenced entity

**Solution**: Use appropriate cascade or check references first
```yaml
fields:
  order: ref(Order)!
    on_delete: cascade  # Allow cascading deletes
```

---

### Error: "Referenced entity not found"

**Cause**: Entity definition missing or circular reference

**Solution**: Define entities in correct order or use forward references
```yaml
# Forward reference (if needed)
entity: Contact
fields:
  company: ref(Company)!  # Company defined elsewhere
```

---

### Slow Join Performance

**Cause**: Joining on UUID instead of INTEGER

**Solution**: Use Trinity pattern helpers (SpecQL does this automatically)
```sql
-- SpecQL auto-generates:
INNER JOIN tb_company ON fk_company = pk_company  -- Fast
```

---

## Next Steps

### Learn More

- **[Multi-Tenancy Guide](multi-tenancy.md)** - Cross-schema relationships with RLS
- **[Actions Guide](actions.md)** - Query and manipulate relationships
- **[Performance Tuning](../07_advanced/performance-tuning.md)** - Optimize joins

### Try These Examples

1. **One-to-Many**: Contact → Company relationship
2. **Many-to-Many**: Order → Product with OrderItem junction
3. **Self-Referencing**: Employee → Manager hierarchy
4. **Cross-Schema**: Multi-tenant → Shared catalog

### Advanced Topics

- **[Custom Patterns](../07_advanced/custom-patterns.md)** - Reusable relationship patterns
- **[GraphQL Optimization](../07_advanced/graphql-optimization.md)** - N+1 query prevention
- **[Testing](../07_advanced/testing.md)** - Test relationship constraints

---

## Summary

You've learned:
- ✅ How to define relationships with `ref()`
- ✅ One-to-many, many-to-many, self-referencing patterns
- ✅ Cross-schema and multi-tenant relationships
- ✅ Cascading behavior and constraints
- ✅ Performance optimization with Trinity pattern

**Key Takeaway**: SpecQL handles all foreign key complexity—you just declare relationships, framework generates constraints, indexes, and efficient joins.

**Next**: Build complex schemas with [Multi-Tenancy Guide](multi-tenancy.md) →

---

**Master relationships declaratively—SpecQL handles the SQL complexity.**
