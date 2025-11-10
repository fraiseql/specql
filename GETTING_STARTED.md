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

Output is written to `db/schema/`:
- `10_tables/contact.sql` - Table definition
- `20_helpers/contact_helpers.sql` - Helper functions
- `30_functions/` - Business logic functions

## Apply to Database

```bash
createdb specql_demo
psql specql_demo -f db/schema/10_tables/contact.sql
psql specql_demo -f db/schema/20_helpers/contact_helpers.sql
```

## Test It Works

```bash
# Create a contact
psql specql_demo -c "SELECT crm.create_contact('john@example.com', 'lead');"

# Check the result
psql specql_demo -c "SELECT id, email, status FROM crm.tb_contact;"
```

## Next Steps

- [Define complex fields](docs/guides/field_types.md)
- [Write business actions](docs/guides/actions.md)
- [Understand Trinity pattern](docs/architecture/trinity_pattern.md)
- [Explore examples](entities/examples/)