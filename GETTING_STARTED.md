# Getting Started with SpecQL

**Goal**: Build a working contact manager in 5 minutes

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Basic YAML knowledge

## Installation

```bash
pip install specql
specql --version
```

## Your First Project

### Step 1: Create Project

```bash
specql init contact-manager
cd contact-manager
```

Creates:
```
contact-manager/
├── entities/
│   └── example.yaml
├── generated/
└── specql.yaml
```

### Step 2: Define Entity

Edit `entities/contact.yaml`:

```yaml
entity: Contact
schema: app
fields:
  name: text
  email: text
  phone: text
  status: enum(active, inactive)
```

### Step 3: Generate Code

```bash
specql generate entities/contact.yaml
```

Generates:
- `generated/01_write_side/012361_tb_contact.sql` - Table definition
- `generated/02_query_side/0220310_tv_contact.sql` - Query view
- Plus: Indexes, functions, GraphQL schema, TypeScript types

### Step 4: Apply to Database

```bash
psql -d mydb -f generated/**/*.sql
```

### Step 5: Add Business Logic

Edit `entities/contact.yaml`:

```yaml
entity: Contact
# ... previous fields ...
actions:
  - name: activate_contact
    steps:
      - validate: status = 'inactive'
      - update: Contact SET status = 'active'
```

Regenerate:
```bash
specql generate entities/contact.yaml
```

Now you have a `app.activate_contact(contact_id UUID)` function!

## Next Steps

- 🎓 [Complete Tutorial](docs/01_tutorials/beginner/contact_manager.md)
- 📖 [Core Concepts](docs/00_getting_started/core_concepts.md)
- 🔧 [CLI Reference](docs/03_reference/cli/command_reference.md)
- 💬 [Join Discord](https://discord.gg/specql) for help