# Your First Entity: Step-by-Step Guide

> **Complete this guide in 15 minutes to create your first SpecQL entity with database schema, GraphQL API, and TypeScript types**

## What You'll Build

A complete `Product` entity for an e-commerce system with:
- ✅ PostgreSQL table with Trinity pattern
- ✅ Rich type validation (money, email, etc.)
- ✅ GraphQL queries and mutations
- ✅ TypeScript interfaces
- ✅ Automatic CRUD operations

## Prerequisites

- ✅ SpecQL installed (`pip install specql`)
- ✅ PostgreSQL running
- ✅ Basic YAML knowledge

## Step 1: Plan Your Entity (2 minutes)

Think about what your entity represents in your business domain:

**Product Entity Requirements:**
- Unique identifier (handled by Trinity pattern)
- Name and description
- Price (with currency support)
- Stock quantity
- Category relationship
- Audit fields (automatic)

**Business Rules:**
- Price must be positive
- Stock can't be negative
- Name is required

## Step 2: Create Entity YAML (3 minutes)

Create `product.yaml`:

```yaml
entity: Product
schema: ecommerce
description: "Product in our catalog"

fields:
  # Basic information
  name: text!                    # Required text
  description: text              # Optional description

  # Pricing
  price: money!                  # Required monetary amount
  currency: currencyCode!        # ISO currency code

  # Inventory
  stock_quantity: integer(0)     # Non-negative integer
  sku: text!                     # Stock keeping unit

  # Relationships
  category: ref(Category)        # Reference to Category entity

  # Status
  is_active: boolean!            # Active/inactive flag
  tags: text[]                   # Array of tags
```

**What each field does:**
- `text!` - Required text field
- `money!` - Monetary amount with decimal precision
- `currencyCode!` - ISO 4217 currency code validation
- `integer(0)` - Integer with minimum value 0
- `ref(Category)` - Foreign key to Category entity
- `boolean!` - Required true/false
- `text[]` - Array of text values

## Step 3: Add Basic Actions (3 minutes)

Add CRUD operations to your YAML:

```yaml
actions:
  # Auto-generated CRUD
  - name: create_product
  - name: update_product
  - name: delete_product

  # Custom business logic
  - name: update_stock
    description: "Update product stock level"
    steps:
      - validate: $quantity >= 0, error: "Stock cannot be negative"
      - update: Product SET stock_quantity = $quantity WHERE id = $product_id
      - return: "Stock updated successfully"

  - name: activate_product
    description: "Mark product as active"
    steps:
      - update: Product SET is_active = true WHERE id = $product_id
      - return: "Product activated"

  - name: deactivate_product
    description: "Mark product as inactive"
    steps:
      - update: Product SET is_active = false WHERE id = $product_id
      - return: "Product deactivated"
```

## Step 4: Generate Everything (2 minutes)

```bash
# Generate from your YAML
specql generate product.yaml

# See what was created
ls -la
```

**Generated files:**
```
db/
├── schema/
│   ├── ecommerce.product.table.sql     # PostgreSQL DDL
│   ├── ecommerce.product.actions.sql   # PL/pgSQL functions
│   └── ecommerce.product.graphql.sql   # GraphQL schema
├── migrations/
│   └── 001_initial_schema.sql          # Migration script
└── types/
    └── product.types.ts                # TypeScript types
```

## Step 5: Deploy to Database (2 minutes)

```bash
# Create database
createdb ecommerce_demo

# Run the migration
psql ecommerce_demo < db/migrations/001_initial_schema.sql

# Verify the table
psql ecommerce_demo -c "\d ecommerce.tb_product"
```

**Expected output:**
```
Table "ecommerce.tb_product"
Column          | Type                  | Modifiers
----------------+-----------------------+-----------
pk_product      | integer               | not null
id              | uuid                  | not null
identifier      | text                  |
tenant_id       | uuid                  |
name            | text                  | not null
description     | text                  |
price           | numeric(19,4)         | not null
currency        | text                  | not null
stock_quantity  | integer               | not null
sku             | text                  | not null
fk_category     | integer               |
is_active       | boolean               | not null
tags            | text[]                |
created_at      | timestamp with time zone | not null
... (more audit fields)
```

## Step 6: Test the Actions (3 minutes)

```bash
# Test creating a product
psql ecommerce_demo << 'EOF'
-- Create a product
SELECT * FROM ecommerce.create_product(
  'Wireless Headphones',           -- name
  'Premium noise-cancelling headphones', -- description
  299.99,                          -- price
  'USD',                           -- currency
  50,                              -- stock_quantity
  'WH-1000XM5'                     -- sku
);

-- Check it was created
SELECT id, name, price, currency, stock_quantity, sku
FROM ecommerce.tb_product
WHERE name = 'Wireless Headphones';
EOF
```

**Expected output:**
```
create_product
----------------
(1,product_1)  -- (pk_product, identifier)

id | name                | price  | currency | stock_quantity | sku
---+---------------------+--------+----------+----------------+-----------
...uuid... | Wireless Headphones | 299.99 | USD      | 50             | WH-1000XM5
```

## Step 7: Test Custom Actions (3 minutes)

```bash
# Test custom stock update
psql ecommerce_demo << 'EOF'
-- Update stock using custom action
SELECT * FROM ecommerce.update_stock(
  '550e8400-e29b-41d4-a716-446655440000'::uuid,  -- product_id
  75                                             -- new quantity
);

-- Verify stock was updated
SELECT name, stock_quantity FROM ecommerce.tb_product
WHERE id = '550e8400-e29b-41d4-a716-446655440000'::uuid;
EOF
```

**Expected output:**
```
update_stock
-------------
Stock updated successfully

name                | stock_quantity
--------------------+----------------
Wireless Headphones | 75
```

## Step 8: Explore Generated GraphQL (2 minutes)

Check the generated GraphQL schema:

```bash
# View the GraphQL schema
cat db/schema/ecommerce.product.graphql.sql
```

**Generated GraphQL:**
```graphql
type Product {
  id: UUID!
  identifier: String
  name: String!
  description: String
  price: Money!
  currency: CurrencyCode!
  stockQuantity: Int!
  sku: String!
  category: Category
  isActive: Boolean!
  tags: [String!]
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Query {
  product(id: UUID!): Product
  products: [Product!]!
}

type Mutation {
  createProduct(input: CreateProductInput!): MutationResult!
  updateProduct(id: UUID!, input: UpdateProductInput!): MutationResult!
  deleteProduct(id: UUID!): MutationResult!
  updateStock(productId: UUID!, quantity: Int!): MutationResult!
  activateProduct(productId: UUID!): MutationResult!
  deactivateProduct(productId: UUID!): MutationResult!
}
```

## Step 9: Check TypeScript Types (1 minute)

```bash
# View generated TypeScript
cat db/types/product.types.ts
```

**Generated types:**
```typescript
export interface Product {
  id: string;
  identifier?: string;
  name: string;
  description?: string;
  price: number;
  currency: string;
  stockQuantity: number;
  sku: string;
  category?: Category;
  isActive: boolean;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateProductInput {
  name: string;
  description?: string;
  price: number;
  currency: string;
  stockQuantity: number;
  sku: string;
  categoryId?: string;
  isActive: boolean;
  tags?: string[];
}
```

## Congratulations! 🎉

You now have a complete Product entity with:

- ✅ **PostgreSQL table** with proper constraints and indexes
- ✅ **Rich type validation** (money, currency codes, etc.)
- ✅ **Business logic** with custom actions
- ✅ **GraphQL API** ready for frontend integration
- ✅ **TypeScript types** for type safety
- ✅ **Audit trails** and data integrity

## What You Learned

### Entity Design
- How to define fields with rich types
- Relationship modeling with `ref()`
- Array fields and optional fields

### Action Creation
- Auto-generated CRUD operations
- Custom business logic with steps
- Validation and error handling

### SpecQL Workflow
- YAML → Generation → Database → Testing
- How generated files work together
- GraphQL and TypeScript integration

## Next Steps

### Add Relationships
- [Create a Category entity](your-first-entity.md) (similar process)
- [Link entities together](relationships.md)

### Add More Business Logic
- [Create complex actions](your-first-action.md)
- [Add validation rules](validation.md)

### Go Production
- [Multi-tenancy setup](multi-tenancy.md)
- [Deploy to production](production-deploy.md)
- [Add authentication](security.md)

## Troubleshooting

### "Command not found: specql"
```bash
# Make sure it's installed
pip install specql
specql --version
```

### "Permission denied" on database
```bash
# Create database as superuser
sudo -u postgres createdb ecommerce_demo
```

### "Table doesn't exist"
```bash
# Make sure migration ran successfully
psql ecommerce_demo -c "\dt ecommerce.*"
```

### Rich type validation errors
```bash
# Check the generated constraints
psql ecommerce_demo -c "\d ecommerce.tb_product"
```

---

**Time spent: 15 minutes. Business logic defined: 30 lines YAML. Production infrastructure generated: 2000+ lines of code.** 🚀</content>
</xai:function_call