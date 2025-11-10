# Getting Started with SpecQL

Welcome! This guide will get you up and running with SpecQL in **5 minutes**. By the end, you'll have created your first entity, used a mutation pattern, and generated automated tests.

## 🎯 What You'll Learn

- Install SpecQL
- Create your first entity
- Use a mutation pattern
- Generate and run tests
- Apply changes to a database

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Basic command-line knowledge

## 🚀 Step 1: Install SpecQL (1 minute)

```bash
# Install SpecQL
pip install specql

# Verify installation
specql --version
```

**Expected output:**
```
SpecQL v1.0.0
```

## 🏗️ Step 2: Create Your First Entity (2 minutes)

Create a new directory for your project and define your first entity:

```bash
# Create project directory
mkdir my-specql-project
cd my-specql-project

# Create entities directory
mkdir entities
```

Create `entities/user.yaml`:

```yaml
# entities/user.yaml
name: user
description: "User account management"

fields:
  id: uuid
  email: string
  name: string
  status: string
  created_at: timestamp
  updated_at: timestamp

patterns:
  - name: state_machine
    states: [inactive, active, suspended]
    initial_state: inactive
    transitions:
      - from: inactive
        to: active
        trigger: activate
      - from: active
        to: suspended
        trigger: suspend
      - from: suspended
        to: active
        trigger: reactivate
```

## 🔧 Step 3: Generate Schema (1 minute)

Generate the database schema from your entity:

```bash
# Generate schema
specql generate schema entities/user.yaml

# Check what was generated
ls -la db/schema/
```

**Expected output:**
```
db/schema/
├── 00_foundation/
├── 10_tables/
│   └── user.sql
├── 20_constraints/
│   └── user_constraints.sql
├── 30_indexes/
│   └── user_indexes.sql
└── 40_functions/
    └── user_state_machine.sql
```

## 🧪 Step 4: Generate Tests (30 seconds)

Generate comprehensive tests automatically:

```bash
# Generate tests
specql generate tests entities/user.yaml

# Check generated tests
ls -la tests/
```

**Expected output:**
```
tests/
├── pgtap/
│   └── user_state_machine_test.sql
└── pytest/
    └── test_user_state_machine.py
```

## 🗄️ Step 5: Apply to Database (30 seconds)

Set up a PostgreSQL database and apply your schema:

```bash
# Create database (if needed)
createdb specql_demo

# Apply schema
psql specql_demo -f db/schema/10_tables/user.sql
psql specql_demo -f db/schema/20_constraints/user_constraints.sql
psql specql_demo -f db/schema/30_indexes/user_indexes.sql
psql specql_demo -f db/schema/40_functions/user_state_machine.sql
```

## ✅ Step 6: Verify Everything Works (30 seconds)

Run the generated tests to verify everything works:

```bash
# Run pgTAP tests
specql test run --type pgtap entities/user.yaml

# Run pytest tests
specql test run --type pytest entities/user.yaml
```

**Expected output:**
```
✅ All tests passed!
```

## 🎉 Congratulations!

You've successfully:
- ✅ Installed SpecQL
- ✅ Created your first entity with a state machine pattern
- ✅ Generated database schema and functions
- ✅ Generated comprehensive tests
- ✅ Applied changes to PostgreSQL
- ✅ Verified everything works with automated tests

## 🚀 What's Next?

Now that you have the basics, explore more advanced features:

### [Create More Entities](first-entity.md)
Learn about relationships, validation, and complex field types.

### [Use More Patterns](first-pattern.md)
Explore the 27 available mutation patterns for common business logic.

### [Generate More Tests](first-tests.md)
Set up CI/CD pipelines with automated testing.

### [CLI Reference](../reference/cli-reference.md)
Master the command-line interface for advanced workflows.

## 💡 Pro Tips

- **Start Simple**: Begin with basic entities, add patterns as needed
- **Test Early**: Generate tests immediately after creating entities
- **Version Control**: Commit your YAML specs alongside generated code
- **Iterate Quickly**: YAML changes → Generate → Test → Deploy

## 🆘 Need Help?

- **Installation Issues**: Check [Installation Guide](installation.md)
- **Pattern Questions**: See [Pattern Basics](../guides/mutation-patterns/getting-started.md)
- **Community Support**: Join our [Discord](https://discord.gg/specql)

**Ready to build something amazing? Let's continue! 🚀**