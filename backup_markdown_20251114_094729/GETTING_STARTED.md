# Getting Started with SpecQL

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- 15 minutes

## Installation

```bash
git clone https://github.com/fraiseql/specql.git
cd specql
uv sync
uv pip install -e .
```

## Create Your First Entity

Create `entities/contact.yaml`:

```yaml
entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified, customer)

actions:
  - name: create_contact
    steps:
      - insert: Contact

  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

## Generate Schema

```bash
specql generate entities/contact.yaml
```

**New in v1.0**: Production-ready defaults with FraiseQL framework!

Output is written to `migrations/` with hierarchical structure:
- `000_app_foundation.sql` - App schema foundation
- `01_write_side/011_crm/011XXX_contact/` - Entity-specific directory
  - `011XXX_tb_contact.sql` - Table definition with Trinity pattern
  - `011XXX_tv_contact.sql` - Table view for GraphQL queries
  - `011XXX_fn_contact_*.sql` - Business logic functions

**For development mode** (flat structure like before):
```bash
specql generate entities/contact.yaml --dev
```

## Apply to Database

**For production mode** (hierarchical structure):

```bash
createdb specql_demo

# Apply foundation first
psql specql_demo -f migrations/000_app_foundation.sql

# Apply entity files in order
find migrations/01_write_side -name "*.sql" | sort | xargs -I {} psql specql_demo -f {}
```

**For development mode** (flat structure):

```bash
createdb specql_demo

# Apply foundation
psql specql_demo -f db/schema/00_foundation/000_app_foundation.sql

# Apply tables
for file in db/schema/10_tables/*.sql; do psql specql_demo -f "$file"; done

# Apply functions
for file in db/schema/30_functions/*.sql; do psql specql_demo -f "$file"; done
```

## Test It Works

```bash
# Create a contact
psql specql_demo -c "SELECT crm.create_contact('john@example.com', 'lead');"

# Check the result
psql specql_demo -c "SELECT id, email, status FROM crm.tb_contact;"

# Or query the GraphQL view
psql specql_demo -c "SELECT id, email, status FROM crm.tv_contact;"
```

## Next Steps

- [Define complex fields](docs/guides/field_types.md)
- [Write business actions](docs/guides/actions.md)
- [Understand Trinity pattern](docs/architecture/trinity_pattern.md)
- [Explore examples](entities/examples/)