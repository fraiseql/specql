# Tutorial 1: Hello SpecQL (5 minutes)

Welcome to SpecQL! This 5-minute tutorial will get you up and running with your first SpecQL entity and basic operations.

## 🎯 What You'll Learn

- Install SpecQL
- Create your first entity
- Generate database schema
- Run basic operations

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- Basic command line knowledge

## 🚀 Step 1: Install SpecQL

First, install SpecQL using pip:

```bash
pip install specql
```

Or if you're using uv (recommended):

```bash
uv add specql
```

Verify installation:

```bash
specql --version
# Should show: specql 0.1.0
```

## 🏗️ Step 2: Create Your First Entity

Create a new directory for your project:

```bash
mkdir hello-specql
cd hello-specql
```

Create a simple `user.yaml` entity file:

```yaml
entity: User
schema: app
description: "Application user"

fields:
  email: text
  first_name: text
  last_name: text
  created_at: timestamp

actions:
  - name: create_user
    pattern: crud/create
    requires: caller.can_create_users
```

## 🗄️ Step 3: Generate Database Schema

Initialize your SpecQL project:

```bash
specql init
```

This creates:
- `specql.yaml` - Project configuration
- `db/` - Database migration files

Generate the SQL schema:

```bash
specql generate schema
```

Check the generated SQL:

```bash
cat db/migrations/001_initial_schema.sql
```

You should see something like:

```sql
-- Schema creation
CREATE SCHEMA IF NOT EXISTS app;

-- Table creation
CREATE TABLE app.user (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL,
    first_name text,
    last_name text,
    created_at timestamp DEFAULT now()
);

-- Generated functions
CREATE OR REPLACE FUNCTION app.create_user(
    p_email text,
    p_first_name text DEFAULT NULL,
    p_last_name text DEFAULT NULL
) RETURNS uuid AS $$
DECLARE
    v_user_id uuid;
BEGIN
    INSERT INTO app.user (
        email, first_name, last_name, created_at
    ) VALUES (
        p_email, p_first_name, p_last_name, now()
    ) RETURNING id INTO v_user_id;

    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 🏃 Step 4: Run Your First Operations

Apply the schema to your database:

```bash
# Set your database connection
export DATABASE_URL="postgresql://user:password@localhost:5432/hello_specql"

# Run migrations
specql db migrate
```

Create your first user:

```sql
-- Connect to your database
psql $DATABASE_URL

-- Create a user
SELECT app.create_user(
    'john.doe@example.com',
    'John',
    'Doe'
);

-- Should return a UUID like: 550e8400-e29b-41d4-a716-446655440000
```

Query your data:

```sql
-- See all users
SELECT * FROM app.user;

-- Should show:
-- id                                    | email               | first_name | last_name | created_at
-- 550e8400-e29b-41d4-a716-446655440000 | john.doe@example.com | John       | Doe       | 2024-01-15 10:30:00+00
```

## 🎉 Success!

Congratulations! You've just:

✅ Installed SpecQL
✅ Created your first entity
✅ Generated database schema
✅ Created and queried data

## 🔍 What Just Happened

SpecQL automatically generated:
- Database table with proper types
- CRUD functions with validation
- Migration scripts for schema changes
- Type-safe operations

## 🧪 Test Your Knowledge

Try these exercises:

1. **Add a new field**: Add `phone: text` to your User entity
2. **Regenerate schema**: Run `specql generate schema` and `specql db migrate`
3. **Create another user**: Use the updated function with phone number
4. **Query with filter**: `SELECT * FROM app.user WHERE first_name = 'John';`

## 📚 Next Steps

- [Tutorial 2: Building a CRM](../02-building-crm.md) - Create a complete CRM system
- [Tutorial 3: State Machines](../03-state-machines.md) - Add workflow states
- [Tutorial 4: Testing](../04-testing.md) - Generate and run tests
- [Tutorial 5: Production](../05-production.md) - Deploy to production

## 💡 Pro Tips

- Use `specql generate --watch` for automatic regeneration during development
- Check `specql --help` for all available commands
- Entity files support YAML syntax highlighting in most editors
- Use `specql validate` to check your entity definitions

---

**Time completed**: 5 minutes
**Files created**: `user.yaml`, database schema
**Next tutorial**: [Building a CRM →](../02-building-crm.md)