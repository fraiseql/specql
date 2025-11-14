# Create Your First Entity

Learn how to define your first SpecQL entity and generate a complete database schema with relationships, constraints, and indexes.

## 🎯 What You'll Learn

- Define entity structure in YAML
- Understand field types and relationships
- Generate database schema automatically
- Apply schema to PostgreSQL
- Query your generated tables

## 📋 Prerequisites

- [SpecQL installed](installation.md)
- PostgreSQL database running
- Basic YAML knowledge

## 🏗️ Step 1: Create Project Structure

```bash
# Create project directory
mkdir my-first-specql-app
cd my-first-specql-app

# Create entities directory
mkdir entities

# Verify structure
tree .
# .
# └── entities/
```

## 📝 Step 2: Define Your First Entity

Create `entities/user.yaml`:

```yaml
# entities/user.yaml
name: user
description: "User account with profile information"

fields:
  id: uuid
  email: string
  first_name: string
  last_name: string
  phone: string?
  date_of_birth: date?
  is_active: boolean
  created_at: timestamp
  updated_at: timestamp
```

### Field Types Available

| Type | Description | Example |
|------|-------------|---------|
| `uuid` | Universally unique identifier | `user_id: uuid` |
| `string` | Text string (up to 255 chars) | `email: string` |
| `text` | Long text (unlimited) | `description: text` |
| `integer` | Whole numbers | `age: integer` |
| `decimal` | Decimal numbers | `price: decimal` |
| `boolean` | True/false values | `is_active: boolean` |
| `date` | Date only | `birth_date: date` |
| `timestamp` | Date and time | `created_at: timestamp` |
| `json` | JSON data | `metadata: json` |

### Optional Fields

Add `?` to make fields nullable:

```yaml
fields:
  required_field: string      # NOT NULL
  optional_field: string?     # NULL allowed
```

## 🔗 Step 3: Add Relationships

Create a related entity and add foreign keys:

```yaml
# entities/company.yaml
name: company
description: "Company information"

fields:
  id: uuid
  name: string
  website: string?
  industry: string
  created_at: timestamp
```

Update user to reference company:

```yaml
# entities/user.yaml (updated)
name: user
description: "User account with profile information"

fields:
  id: uuid
  email: string
  first_name: string
  last_name: string
  company_id: uuid?           # Foreign key field
  phone: string?
  date_of_birth: date?
  is_active: boolean
  created_at: timestamp
  updated_at: timestamp

relationships:
  company:
    type: belongs_to
    entity: company
    foreign_key: company_id
```

## ✅ Step 4: Validate Your Entities

```bash
# Validate syntax
specql validate entities/user.yaml entities/company.yaml

# Expected output:
# ✅ entities/user.yaml: Valid
# ✅ entities/company.yaml: Valid
```

## 🔧 Step 5: Generate Database Schema

```bash
# Generate schema for both entities
specql generate schema entities/user.yaml entities/company.yaml

# Check generated files
ls -la db/schema/
# 00_foundation/
# 10_tables/
# ├── company.sql
# └── user.sql
# 20_constraints/
# 30_indexes/
# 40_functions/
```

## 📄 Step 6: Review Generated SQL

```bash
# View the user table
cat db/schema/10_tables/user.sql
```

**Generated SQL includes:**
```sql
-- Auto-generated user table
CREATE TABLE user (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  company_id UUID,
  phone VARCHAR(255),
  date_of_birth DATE,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Foreign key constraint
ALTER TABLE user
ADD CONSTRAINT fk_user_company_id
FOREIGN KEY (company_id) REFERENCES company(id);

-- Indexes for performance
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_company_id ON user(company_id);
CREATE INDEX idx_user_created_at ON user(created_at);
```

## 🗄️ Step 7: Apply to Database

```bash
# Apply foundation schema
psql $DATABASE_URL -f db/schema/00_foundation/*.sql

# Apply tables
psql $DATABASE_URL -f db/schema/10_tables/company.sql
psql $DATABASE_URL -f db/schema/10_tables/user.sql

# Apply constraints and indexes
psql $DATABASE_URL -f db/schema/20_constraints/*.sql
psql $DATABASE_URL -f db/schema/30_indexes/*.sql
```

## 🧪 Step 8: Test Your Schema

```bash
# Connect to database
psql $DATABASE_URL

# Check tables exist
\d

# Insert test data
INSERT INTO company (name, industry) VALUES
  ('Acme Corp', 'Technology'),
  ('Globex Inc', 'Manufacturing');

INSERT INTO user (email, first_name, last_name, company_id) VALUES
  ('john@acme.com', 'John', 'Doe', (SELECT id FROM company WHERE name = 'Acme Corp')),
  ('jane@globex.com', 'Jane', 'Smith', (SELECT id FROM company WHERE name = 'Globex Inc'));

# Query with joins
SELECT u.first_name, u.last_name, u.email, c.name as company
FROM user u
LEFT JOIN company c ON u.company_id = c.id;
```

**Expected output:**
```
 first_name | last_name |     email      |   company
------------+-----------+----------------+-------------
 John       | Doe       | john@acme.com  | Acme Corp
 Jane       | Smith     | jane@globex.com| Globex Inc
```

## 🎯 Best Practices

### Entity Design
- **Use snake_case** for field names: `first_name`, not `firstName`
- **Add descriptions** for clarity
- **Use appropriate types** - `string` for short text, `text` for long content
- **Make fields optional** when appropriate with `?`

### Relationships
- **Use UUIDs for foreign keys** for consistency
- **Name foreign key fields** as `{entity}_id`
- **Add relationship metadata** for clarity

### Schema Evolution
- **Version control** your YAML files
- **Test migrations** before applying to production
- **Use constraints** to maintain data integrity

## 🚀 Advanced Features

### Custom Constraints
```yaml
fields:
  email: string
  age: integer

constraints:
  - name: check_age_positive
    expression: "age > 0"
  - name: unique_email_active
    expression: "UNIQUE(email) WHERE is_active = true"
```

### Indexes
```yaml
indexes:
  - name: idx_user_email_active
    fields: [email]
    where: "is_active = true"
  - name: idx_user_name
    fields: [first_name, last_name]
```

### Triggers
```yaml
triggers:
  - name: update_timestamp
    timing: before
    event: update
    function: |
      NEW.updated_at = NOW();
      RETURN NEW;
```

## 🆘 Troubleshooting

### "Table already exists"
```bash
# Drop and recreate
psql $DATABASE_URL -c "DROP TABLE IF EXISTS user CASCADE;"

# Or use migration tools
specql migrate up entities/user.yaml
```

### "Foreign key constraint violation"
```bash
# Check referenced data exists
SELECT id FROM company WHERE id = 'your-uuid';

# Insert parent records first
INSERT INTO company (name) VALUES ('Parent Company');
```

### "Permission denied"
```bash
# Grant permissions
psql $DATABASE_URL -c "GRANT ALL ON SCHEMA public TO your_user;"

# Or check connection string
echo $DATABASE_URL
```

## 🎉 Congratulations!

You've created your first SpecQL entities with:
- ✅ Basic field types and constraints
- ✅ Relationships between entities
- ✅ Auto-generated database schema
- ✅ Indexes for performance
- ✅ Working PostgreSQL tables

## 🚀 What's Next?

- **[Use Your First Pattern](first-pattern.md)** - Add business logic
- **[Generate Tests](first-tests.md)** - Automated testing
- **[Entity Design Guide](../best-practices/entity-design.md)** - Advanced patterns

## 📚 Related Topics

- **[YAML Schema Reference](../reference/yaml-schema.md)** - Complete syntax
- **[Field Types](../reference/yaml-schema.md#field-types)** - All available types
- **[Relationships](../guides/mutation-patterns/multi-entity.md)** - Advanced relationships

**Ready to add some business logic? Let's continue! 🚀**