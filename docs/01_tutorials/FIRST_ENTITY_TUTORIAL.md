# First Entity Tutorial

**Designing your first SpecQL entity** - Best practices for entity definition

This tutorial focuses on entity design patterns, field types, validation, and indexing strategies. Assumes you've completed the [Getting Started Tutorial](GETTING_STARTED_TUTORIAL.md).

## 🎯 What You'll Learn

- Entity naming conventions and schema organization
- Complete field type reference
- Validation rules and constraints
- Indexing strategies for performance
- Common entity design patterns

## 📋 Prerequisites

- [ ] Completed [Getting Started Tutorial](GETTING_STARTED_TUTORIAL.md)
- [ ] Understanding of basic YAML syntax
- [ ] PostgreSQL basics

## 🏗️ Step 1: Entity Structure Basics

Every SpecQL entity follows this structure:

```yaml
entity: EntityName          # PascalCase, singular noun
schema: schema_name         # lowercase, domain-based
description: "What this entity represents"

fields:                     # Your data fields
  field_name: field_type    # snake_case names

indexes:                    # Optional performance indexes
  - fields: [field_name]
    unique: true

actions:                    # Optional business logic
  - name: action_name
    steps:
      - validate: condition
      - update: Entity SET field = value
```

## 📝 Step 2: Complete Field Type Reference

### Text Fields

```yaml
fields:
  # Basic text (VARCHAR with unlimited length in PostgreSQL)
  name: text
  description: text

  # Email validation
  email: text
  # Generates: CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')

  # URL validation
  website: text
  # Generates: CHECK (website ~ '^https?://.*')

  # Phone number
  phone: text
  # Generates: CHECK (phone ~ '^\+?[\d\s\-\(\)]+$')
```

### Numeric Fields

```yaml
fields:
  # Integers
  age: integer              # Standard integer
  quantity: integer         # Can be negative
  user_count: integer       # For counts/metrics

  # Decimals (specify precision and scale)
  price: decimal            # DECIMAL(10,2) - default precision
  weight: decimal(8,3)      # DECIMAL(8,3) - 8 digits total, 3 after decimal
  percentage: decimal(5,2)  # DECIMAL(5,2) - 0.00 to 999.99

  # Auto-incrementing (rarely used - prefer Trinity pattern)
  legacy_id: serial         # Small serial
  big_id: bigserial         # Large serial
```

### Date/Time Fields

```yaml
fields:
  # Date and time
  created_at: timestamp     # TIMESTAMPTZ - always use this
  updated_at: timestamp     # Automatic in SpecQL
  published_at: timestamp   # For scheduling

  # Date only
  birth_date: date          # DATE - no time component
  due_date: date            # For deadlines

  # Time intervals
  duration: interval        # INTERVAL - for time spans
```

### Boolean and Choice Fields

```yaml
fields:
  # Boolean
  is_active: boolean        # TRUE/FALSE
  has_discount: boolean     # For flags
  email_verified: boolean   # Account status

  # Enums (predefined choices)
  status: enum(active, inactive, suspended)
  priority: enum(low, medium, high, urgent)
  category: enum(personal, work, family, other)

  # Status with business meaning
  order_status: enum(pending, processing, shipped, delivered, cancelled)
  user_role: enum(user, moderator, admin, super_admin)
```

### Special Types

```yaml
fields:
  # Universally Unique Identifier
  external_id: uuid         # UUID - for external APIs

  # JSON data
  metadata: json            # JSONB in PostgreSQL
  settings: json            # User preferences, flexible data

  # Binary data (references)
  avatar_file: text         # File path/reference
  document_hash: text       # SHA256 hash

  # Geographic (if PostGIS enabled)
  location: geometry        # Point, Polygon, etc.
  latitude: decimal(10,8)   # DECIMAL(10,8) for GPS
  longitude: decimal(11,8)  # DECIMAL(11,8) for GPS
```

## 🔍 Step 3: Validation Rules

SpecQL supports comprehensive validation:

### Field-Level Validation

```yaml
fields:
  email: text
  age: integer
  username: text

actions:
  - name: create_user
    steps:
      # Email format validation
      - validate: email MATCHES "^[^@]+@[^@]+\\.[^@]+$"
        error: "invalid_email"

      # Range validation
      - validate: age >= 13 AND age <= 120
        error: "age_out_of_range"

      # String length
      - validate: LENGTH(username) >= 3 AND LENGTH(username) <= 50
        error: "username_length_invalid"

      # Required fields
      - validate: email IS NOT NULL
        error: "email_required"

      # Uniqueness (checked at database level via unique indexes)
      - validate: username IS UNIQUE
        error: "username_taken"
```

### Business Rule Validation

```yaml
actions:
  - name: update_order_status
    steps:
      # Status transition rules
      - validate: status IN ('pending', 'processing', 'shipped')
        error: "invalid_status_transition"

      # Business logic validation
      - validate: status != 'shipped' OR tracking_number IS NOT NULL
        error: "tracking_required_for_shipped"

      # Cross-field validation
      - validate: priority = 'urgent' OR due_date > NOW() + INTERVAL '24 hours'
        error: "urgent_tasks_must_have_due_date"
```

## 📊 Step 4: Indexing Strategy

Proper indexing is crucial for performance:

### Basic Indexes

```yaml
# User entity with comprehensive indexing
entity: User
schema: app

fields:
  email: text
  username: text
  status: enum(active, inactive, suspended)
  role: enum(user, admin, moderator)
  created_at: timestamp
  last_login: timestamp

indexes:
  # Unique constraints (automatically create unique indexes)
  - fields: [email]
    unique: true
  - fields: [username]
    unique: true

  # Performance indexes
  - fields: [status]                    # Common filter
  - fields: [role]                      # Access control
  - fields: [created_at]                # Date ranges
  - fields: [last_login]                # Recent activity

  # Composite indexes
  - fields: [status, created_at]        # Status + date queries
  - fields: [role, status]              # Role-based filtering
```

### Advanced Indexing Patterns

```yaml
# E-commerce product indexing
entity: Product
schema: shop

fields:
  name: text
  category: text
  brand: text
  price: decimal
  in_stock: boolean
  rating: decimal(3,2)  # 0.00 to 5.00
  tags: json            # Array of tags

indexes:
  # Text search
  - fields: [name]
    type: gin            # For full-text search
  - fields: [tags]
    type: gin            # JSON array indexing

  # Range queries
  - fields: [price]      # Price filtering
  - fields: [rating]     # Rating sorting

  # Multi-column for complex queries
  - fields: [category, brand, price]
  - fields: [in_stock, category]
```

## 🏷️ Step 5: Naming Conventions

Follow these conventions for maintainable code:

### Entity Names
```yaml
# Good
entity: User
entity: Product
entity: Order
entity: Invoice

# Avoid
entity: user          # lowercase
entity: Users         # plural
entity: user_table    # redundant
```

### Field Names
```yaml
# Good
fields:
  first_name: text     # snake_case
  email_address: text  # descriptive
  is_active: boolean   # boolean prefix
  created_at: timestamp # past tense for events

# Avoid
fields:
  firstname: text     # no separation
  email: text         # too generic
  active: boolean     # unclear type
  date: timestamp     # too vague
```

### Schema Names
```yaml
# Domain-based schemas
schema: app           # General application
schema: auth          # Authentication
schema: billing       # Payment processing
schema: inventory     # Product management
schema: reporting     # Analytics

# Avoid
schema: public        # Too generic
schema: myapp         # Not descriptive
schema: db1           # Version-specific
```

## 🏛️ Step 6: Common Entity Patterns

### User Management

```yaml
entity: User
schema: auth
description: "Application user accounts"

fields:
  username: text
  email: text
  password_hash: text
  status: enum(active, inactive, suspended, pending_verification)
  role: enum(user, moderator, admin)
  email_verified: boolean
  last_login: timestamp
  login_attempts: integer

indexes:
  - fields: [email]
    unique: true
  - fields: [username]
    unique: true
  - fields: [status]
  - fields: [role]

actions:
  - name: create_user
    steps:
      - validate: email MATCHES "^[^@]+@[^@]+\\.[^@]+$"
      - validate: LENGTH(username) >= 3
      - insert: User SET status = 'pending_verification'

  - name: verify_email
    steps:
      - validate: status = 'pending_verification'
      - update: User SET email_verified = true, status = 'active'
```

### Product Catalog

```yaml
entity: Product
schema: catalog
description: "Product catalog items"

fields:
  sku: text
  name: text
  description: text
  category: text
  brand: text
  price: decimal(10,2)
  cost: decimal(10,2)
  stock_quantity: integer
  is_active: boolean
  weight_kg: decimal(8,3)
  dimensions: json      # {"length": 10, "width": 5, "height": 2}

indexes:
  - fields: [sku]
    unique: true
  - fields: [category]
  - fields: [brand]
  - fields: [price]
  - fields: [is_active]
  - fields: [name]
    type: gin

actions:
  - name: update_stock
    parameters:
      - name: quantity_change
        type: integer
        required: true
    steps:
      - validate: stock_quantity + :quantity_change >= 0
        error: "insufficient_stock"
      - update: Product SET stock_quantity = stock_quantity + :quantity_change
```

### Order Management

```yaml
entity: Order
schema: sales
description: "Customer orders"

fields:
  order_number: text
  customer_id: integer    # References User.pk_user
  status: enum(pending, confirmed, processing, shipped, delivered, cancelled)
  total_amount: decimal(12,2)
  tax_amount: decimal(10,2)
  shipping_amount: decimal(8,2)
  discount_amount: decimal(8,2)
  ordered_at: timestamp
  shipped_at: timestamp
  delivered_at: timestamp

indexes:
  - fields: [order_number]
    unique: true
  - fields: [customer_id]
  - fields: [status]
  - fields: [ordered_at]
  - fields: [status, ordered_at]  # Status + date queries

actions:
  - name: place_order
    steps:
      - validate: total_amount > 0
      - validate: status = 'pending'
      - update: Order SET status = 'confirmed', ordered_at = NOW()

  - name: ship_order
    steps:
      - validate: status = 'processing'
      - update: Order SET status = 'shipped', shipped_at = NOW()
```

## 🧪 Step 7: Testing Your Entity

Create a comprehensive test for your entity:

```bash
# Generate the schema
specql generate entities/user/profile.yaml --output test_output

# Create test database
createdb entity_test

# Apply schema
psql entity_test < test_output/app/01_tables.sql
psql entity_test < test_output/app/02_functions.sql

# Test basic operations
psql entity_test << 'EOF'
-- Test successful creation
SELECT * FROM app.fn_user_create_user(
    'testuser',
    'test@example.com',
    'Test',
    'User'
);

-- Test validation failures
SELECT * FROM app.fn_user_create_user(
    'tu',  -- Too short
    'invalid-email',  -- Invalid format
    'Test',
    'User'
);

-- Check data
SELECT id, username, email, first_name, last_name, status
FROM app.tb_user;
EOF
```

## 🎯 Step 8: Best Practices Summary

### Design Principles

1. **Single Responsibility** - One entity, one primary purpose
2. **Descriptive Names** - Clear, unambiguous field names
3. **Appropriate Types** - Choose the most specific type
4. **Validation First** - Prevent bad data at the source
5. **Index Strategically** - Index for actual query patterns

### Performance Tips

1. **Index Common Filters** - Status, dates, foreign keys
2. **Use Appropriate Types** - Don't use text for booleans
3. **Consider Cardinality** - Low-cardinality fields first in composites
4. **Monitor Slow Queries** - Add indexes as needed

### Maintenance Tips

1. **Version Control** - Keep entity definitions in git
2. **Document Changes** - Comment complex business rules
3. **Test Migrations** - Always test schema changes
4. **Monitor Performance** - Watch for slow queries after changes

## 🔄 Next Steps

You've mastered entity design fundamentals!

- **[Relationships Tutorial](RELATIONSHIPS_TUTORIAL.md)** - Connect entities together
- **[Actions Tutorial](ACTIONS_TUTORIAL.md)** - Complex business logic
- **[Multi-Language Tutorial](MULTI_LANGUAGE_TUTORIAL.md)** - Generate multiple languages

## 🆘 Troubleshooting

**"Field type not supported"?**
- Check spelling: `integer` not `int`, `text` not `string`
- Use `decimal` for money, not `float`

**Validation not working?**
- Use `MATCHES` for regex: `field MATCHES "^pattern$"`
- Use `IN` for lists: `status IN ('active', 'inactive')`

**Indexes not created?**
- `unique: true` creates unique indexes automatically
- Use `type: gin` for full-text and JSON indexes

---

**Great work!** You now know how to design robust, scalable entities with SpecQL.