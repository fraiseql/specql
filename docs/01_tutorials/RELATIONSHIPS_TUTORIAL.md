# Relationships Tutorial

**Connecting entities** - Foreign keys, joins, and data integrity with SpecQL

This tutorial covers defining and working with relationships between entities, including foreign keys, cascading operations, and complex data models.

## 🎯 What You'll Learn

- Relationship types (one-to-one, one-to-many, many-to-many)
- Foreign key constraints and naming
- Cascading operations
- Complex relationship patterns
- Querying related data

## 📋 Prerequisites

- [ ] Completed [First Entity Tutorial](FIRST_ENTITY_TUTORIAL.md)
- [ ] Understanding of basic entity definition
- [ ] Database relationship concepts

## 🏗️ Step 1: Basic Relationships

### One-to-Many Relationship

```yaml
# entities/user.yaml
entity: User
schema: app
fields:
  username: text
  email: text

# entities/post.yaml
entity: Post
schema: app
fields:
  title: text
  content: text
  author_id: integer  # Foreign key to User.pk_user

relationships:
  - name: author
    entity: User
    type: many-to-one
    local_field: author_id
    foreign_field: pk_user
```

**Generated foreign key:**
```sql
-- In posts table
ALTER TABLE app.tb_post
ADD CONSTRAINT fk_post_author
FOREIGN KEY (author_id) REFERENCES app.tb_user(pk_user);

-- Index for performance
CREATE INDEX idx_post_author_id ON app.tb_post(author_id);
```

### One-to-One Relationship

```yaml
# entities/user.yaml
entity: User
schema: app
fields:
  username: text
  email: text

# entities/profile.yaml
entity: Profile
schema: app
fields:
  bio: text
  avatar_url: text
  user_id: integer  # Unique foreign key

relationships:
  - name: user
    entity: User
    type: one-to-one
    local_field: user_id
    foreign_field: pk_user

indexes:
  - fields: [user_id]
    unique: true  # Ensures one profile per user
```

### Many-to-Many Relationship

```yaml
# entities/user.yaml
entity: User
schema: app
fields:
  username: text

# entities/group.yaml
entity: Group
schema: app
fields:
  name: text

# entities/user_group.yaml (junction table)
entity: UserGroup
schema: app
fields:
  user_id: integer
  group_id: integer

relationships:
  - name: user
    entity: User
    type: many-to-one
    local_field: user_id
    foreign_field: pk_user
  - name: group
    entity: Group
    type: many-to-one
    local_field: group_id
    foreign_field: pk_group

indexes:
  - fields: [user_id, group_id]
    unique: true  # Prevent duplicate memberships
```

## 📝 Step 2: E-commerce Example

Complete e-commerce data model:

```yaml
# entities/customer.yaml
entity: Customer
schema: sales
fields:
  email: text
  first_name: text
  last_name: text

# entities/product.yaml
entity: Product
schema: inventory
fields:
  name: text
  sku: text
  price: decimal
  category_id: integer

relationships:
  - name: category
    entity: Category
    type: many-to-one
    local_field: category_id
    foreign_field: pk_category

# entities/order.yaml
entity: Order
schema: sales
fields:
  customer_id: integer
  order_date: timestamp
  total_amount: decimal
  status: enum(pending, paid, shipped, delivered)

relationships:
  - name: customer
    entity: Customer
    type: many-to-one
    local_field: customer_id
    foreign_field: pk_customer

# entities/order_item.yaml
entity: OrderItem
schema: sales
fields:
  order_id: integer
  product_id: integer
  quantity: integer
  unit_price: decimal

relationships:
  - name: order
    entity: Order
    type: many-to-one
    local_field: order_id
    foreign_field: pk_order
  - name: product
    entity: Product
    type: many-to-one
    local_field: product_id
    foreign_field: pk_product
```

## 🔄 Step 3: Cascading Operations

Handle related data changes:

```yaml
entity: Department
schema: hr
fields:
  name: text
  manager_id: integer

relationships:
  - name: manager
    entity: Employee
    type: many-to-one
    local_field: manager_id
    foreign_field: pk_employee
    on_delete: set_null  # When manager deleted, set to NULL

entity: Employee
schema: hr
fields:
  first_name: text
  last_name: text
  department_id: integer
  manager_id: integer

relationships:
  - name: department
    entity: Department
    type: many-to-one
    local_field: department_id
    foreign_field: pk_department
    on_delete: restrict  # Prevent department deletion if employees exist

  - name: manager
    entity: Employee
    type: many-to-one
    local_field: manager_id
    foreign_field: pk_employee
    on_delete: set_null  # Allow manager changes
```

## 🎯 Step 4: Complex Queries

Generate views for complex relationships:

```bash
# Generate with relationship views
specql generate entities/*.yaml --include-tv --output generated
```

**Generated relationship view:**
```sql
CREATE OR REPLACE VIEW sales.tv_order_complete AS
SELECT
    o.id,
    o.order_date,
    o.total_amount,
    o.status,
    -- Customer info
    c.email as customer_email,
    c.first_name as customer_first_name,
    c.last_name as customer_last_name,
    -- Order items with product details
    json_agg(json_build_object(
        'product_name', p.name,
        'quantity', oi.quantity,
        'unit_price', oi.unit_price,
        'total', oi.quantity * oi.unit_price
    )) as items
FROM sales.tb_order o
JOIN sales.tb_customer c ON o.customer_id = c.pk_customer
JOIN sales.tb_order_item oi ON o.pk_order = oi.order_id
JOIN inventory.tb_product p ON oi.product_id = p.pk_product
WHERE o.deleted_at IS NULL
GROUP BY o.id, o.order_date, o.total_amount, o.status,
         c.email, c.first_name, c.last_name;
```

## 🧪 Step 5: Testing Relationships

Test referential integrity:

```bash
# Generate schema
specql generate entities/customer.yaml entities/order.yaml --output test_relations

# Create test database
createdb relation_test

# Apply schema
psql relation_test < test_relations/sales/01_tables.sql

# Test foreign key constraints
psql relation_test << 'EOF'
-- This should work
INSERT INTO sales.tb_customer (email, first_name, last_name)
VALUES ('john@example.com', 'John', 'Doe');

-- Get customer ID
SELECT id FROM sales.tb_customer WHERE email = 'john@example.com';

-- Create order for valid customer (should work)
INSERT INTO sales.tb_order (customer_id, total_amount, status)
VALUES (1, 100.00, 'pending');

-- Try to create order for non-existent customer (should fail)
INSERT INTO sales.tb_order (customer_id, total_amount, status)
VALUES (999, 50.00, 'pending');
EOF
```

## 🔍 Step 6: Relationship Best Practices

### Naming Conventions

```yaml
# Good relationship names
relationships:
  - name: author        # Clear, descriptive
  - name: category      # Matches entity name
  - name: parent        # For self-referencing

# Avoid
relationships:
  - name: user_ref      # Unnecessary suffix
  - name: fk_user       # Technical naming
  - name: user_id_rel   # Redundant
```

### Index Strategy

```yaml
# Always index foreign keys
entity: Order
indexes:
  - fields: [customer_id]     # Foreign key index
  - fields: [status]          # Common filter
  - fields: [customer_id, status]  # Composite for complex queries
```

### Data Integrity

```yaml
# Use appropriate cascade actions
relationships:
  - name: author
    entity: User
    type: many-to-one
    on_delete: restrict      # Prevent deletion if posts exist

  - name: category
    entity: Category
    type: many-to-one
    on_delete: set_null      # Allow category deletion

  - name: parent
    entity: Category
    type: many-to-one
    on_delete: cascade       # Delete child categories
```

## 🔄 Next Steps

You've mastered SpecQL relationships!

- **[Actions Tutorial](ACTIONS_TUTORIAL.md)** - Business logic with relationships
- **[Multi-Language Tutorial](MULTI_LANGUAGE_TUTORIAL.md)** - Generate across languages
- **[Reverse Engineering Tutorial](REVERSE_ENGINEERING_TUTORIAL.md)** - Import existing schemas

## 🆘 Common Issues

**Foreign key constraint violations?**
- Ensure referenced records exist before creating relationships
- Use correct field types (integer for pk_*, uuid for id)

**Circular references?**
- Avoid bidirectional required relationships
- Use set_null or restrict for circular deps

**Performance issues with joins?**
- Index all foreign key columns
- Consider denormalization for read-heavy workloads

---

**Excellent!** You now understand how to model complex data relationships with SpecQL.