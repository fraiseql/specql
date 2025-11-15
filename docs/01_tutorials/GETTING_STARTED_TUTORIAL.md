# Getting Started Tutorial

**Your first steps with SpecQL** - From installation to your first generated code

This tutorial assumes you've completed the [Quick Start Guide](../00_getting_started/QUICKSTART.md) and want to dive deeper into the fundamentals.

## 🎯 What You'll Learn

- Setting up a proper SpecQL project structure
- Understanding the YAML syntax in detail
- Generating and inspecting your first schema
- Testing generated code manually

## 📋 Prerequisites

- [ ] SpecQL installed ([Installation Guide](../00_getting_started/INSTALLATION.md))
- [ ] Basic YAML knowledge
- [ ] Terminal/command line access
- [ ] Text editor (VS Code recommended)

## 🏗️ Step 1: Project Structure

Create a well-organized SpecQL project:

```bash
# Create project directory
mkdir my-specql-app
cd my-specql-app

# Create standard directory structure
mkdir -p entities/{user,product,order}
mkdir -p generated/{postgresql,java,rust,typescript}
mkdir -p tests/{unit,integration}
mkdir -p docs

# Initialize git (recommended)
git init
```

**Why this structure?**
- `entities/` - Your YAML definitions (organized by domain)
- `generated/` - Auto-generated code (don't edit manually)
- `tests/` - Your test files
- `docs/` - Project documentation

## 📝 Step 2: Your First Entity

Create `entities/user/profile.yaml`:

```yaml
# User Profile Entity
entity: User
schema: app
description: "User account and profile information"

fields:
  # Basic information
  username: text
  email: text
  first_name: text
  last_name: text

  # Account status
  status: enum(active, inactive, suspended)
  role: enum(user, admin, moderator)

  # Profile data
  bio: text
  avatar_url: text
  website: text

  # Preferences
  email_notifications: boolean
  theme: enum(light, dark, auto)

# Business logic
actions:
  - name: create_user
    description: "Create a new user account"
    steps:
      - validate: email MATCHES "^[^@]+@[^@]+\\.[^@]+$"
        error: "invalid_email_format"
      - validate: username IS NOT NULL AND LENGTH(username) >= 3
        error: "username_too_short"
      - insert: User SET status = 'active'

  - name: suspend_user
    requires: caller.is_admin
    description: "Suspend a user account"
    steps:
      - validate: status = 'active'
        error: "user_not_active"
      - update: User SET status = 'suspended'
      - notify: user_suspended
```

## 🔧 Step 3: Generate Your Schema

Generate PostgreSQL schema from your YAML:

```bash
# Generate all entities
specql generate entities/user/profile.yaml --output generated/postgresql

# Check what was generated
ls -la generated/postgresql/
```

**Expected output:**
```
generated/postgresql/
├── app/
│   ├── 01_tables.sql      # Table DDL
│   ├── 02_functions.sql   # Business logic functions
│   └── 03_views.sql       # Query views
└── migrations/
    └── 001_initial_schema.sql  # Migration file
```

## 🗄️ Step 4: Inspect Generated Code

Let's examine what SpecQL created:

**Table Structure** (`01_tables.sql`):
```sql
-- Trinity Pattern fields
CREATE TABLE app.tb_user (
    pk_user SERIAL PRIMARY KEY,           -- Integer PK for JOINs
    id UUID DEFAULT gen_random_uuid(),    -- UUID for APIs
    identifier TEXT,                      -- Human-readable ID

    -- Your fields
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    status TEXT CHECK (status IN ('active', 'inactive', 'suspended')),
    role TEXT CHECK (role IN ('user', 'admin', 'moderator')),

    -- Audit fields (automatic)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- Indexes (automatic)
CREATE UNIQUE INDEX idx_user_email ON app.tb_user(email);
CREATE UNIQUE INDEX idx_user_username ON app.tb_user(username);
CREATE INDEX idx_user_status ON app.tb_user(status);
```

**Business Logic Function** (`02_functions.sql`):
```sql
CREATE OR REPLACE FUNCTION app.fn_user_create_user(
    p_username TEXT,
    p_email TEXT,
    p_first_name TEXT DEFAULT NULL,
    p_last_name TEXT DEFAULT NULL
)
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
BEGIN
    -- Validation
    IF p_email NOT LIKE '%@%' THEN
        RETURN app.error('invalid_email_format', 'Invalid email format');
    END IF;

    IF p_username IS NULL OR LENGTH(TRIM(p_username)) < 3 THEN
        RETURN app.error('username_too_short', 'Username must be at least 3 characters');
    END IF;

    -- Insert with default status
    INSERT INTO app.tb_user (
        username, email, first_name, last_name, status
    ) VALUES (
        TRIM(p_username), LOWER(TRIM(p_email)),
        TRIM(p_first_name), TRIM(p_last_name), 'active'
    );

    -- Return success
    RETURN app.success('User created successfully');
END;
$$;
```

## 🧪 Step 5: Test Your Code

Create a test database and verify everything works:

```bash
# Create test database
createdb specql_tutorial

# Apply schema
psql specql_tutorial < generated/postgresql/app/01_tables.sql
psql specql_tutorial < generated/postgresql/app/02_functions.sql

# Test the function
psql specql_tutorial -c "
SELECT * FROM app.fn_user_create_user(
    'johndoe',
    'john@example.com',
    'John',
    'Doe'
);"

# Check the data
psql specql_tutorial -c "SELECT * FROM app.tb_user;"
```

**Expected result:**
```
success | t
message | User created successfully
object  | {"id": "uuid-here"}
```

## 🔍 Step 6: Understanding the Trinity Pattern

SpecQL automatically creates three identifiers for each entity:

```sql
-- Example: User with ID "johndoe"
SELECT pk_user, id, identifier FROM app.tb_user;
-- Result: 1 | a1b2c3d4-... | johndoe
```

**When to use each:**
- `pk_user` (INTEGER) - Database JOINs, foreign keys, performance
- `id` (UUID) - APIs, external references, security
- `identifier` (TEXT) - Human-readable IDs, URLs, display

## 📊 Step 7: Add Query Views

Generate views for safe querying:

```bash
# Generate with views
specql generate entities/user/profile.yaml --include-tv --output generated/postgresql
```

**Generated View** (`03_views.sql`):
```sql
CREATE OR REPLACE VIEW app.tv_user AS
SELECT
    id,
    identifier,
    username,
    email,
    first_name,
    last_name,
    status,
    role,
    bio,
    avatar_url,
    website,
    email_notifications,
    theme,
    created_at,
    updated_at
FROM app.tb_user
WHERE deleted_at IS NULL;  -- Soft delete filter
```

## 🎯 Step 8: Next Steps

You've successfully:
- ✅ Created a SpecQL project structure
- ✅ Defined your first entity with business logic
- ✅ Generated working PostgreSQL code
- ✅ Tested the generated functions
- ✅ Understood the Trinity pattern

**Ready for more?**
- **[Entity Tutorial](FIRST_ENTITY_TUTORIAL.md)** - Deep dive into entity design
- **[Actions Tutorial](ACTIONS_TUTORIAL.md)** - Complex business logic
- **[Relationships Tutorial](RELATIONSHIPS_TUTORIAL.md)** - Multi-entity systems

## 🆘 Common Issues

**"Permission denied" when creating database?**
```bash
# Create database with your user
createdb -U $(whoami) specql_tutorial
```

**Functions not found after generation?**
```bash
# Check schema search path
psql specql_tutorial -c "SHOW search_path;"
# Should include 'app'
```

**YAML syntax errors?**
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('entities/user/profile.yaml'))"
```

---

**Congratulations!** You now understand the fundamentals of SpecQL. Time to build something more complex!