# Getting Started with SpecQL

**From zero to production backend in 5 minutes** ⏱️

## Prerequisites

- PostgreSQL 14+ installed
- Python 3.11+
- uv package manager

```bash
# Quick check
postgres --version  # Should be 14+
python --version    # Should be 3.11+
uv --version        # Should be 0.1.0+
```

## Step 1: Installation (30 seconds)

```bash
# Clone and setup
git clone https://github.com/your-org/specql.git
cd specql
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Verify
specql --version
```

## Step 2: Create Your First Entity (1 minute)

Let's build a simple Contact management system.

```bash
# Create entity file
mkdir -p entities
cat > entities/contact.yaml <<'EOF'
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  # Rich types with automatic validation
  email: email!              # NOT NULL + email validation
  phone: phone               # E.164 phone format

  # Basic types
  first_name: text!
  last_name: text!
  company_name: text

  # Enum with automatic CHECK constraint
  status: enum(lead, qualified, customer)

  # Rich type with automatic range validation
  score: percentage          # 0-100 with 2 decimal places

actions:
  - name: create_contact
    description: "Create a new contact"
    steps:
      - validate: email IS NOT NULL
      - insert: Contact

  - name: qualify_lead
    description: "Convert lead to qualified"
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
EOF
```

**What you just wrote**: 25 lines of business logic
**What you'll get**: 2000+ lines of production code

## Step 3: Generate Everything (30 seconds)

```bash
# Generate all code
specql generate entities/contact.yaml

# See what was generated
ls -la db/schema/
# 00_foundation/           - App foundation types (mutation_result, etc.)
# 10_tables/contact.sql     - Table with Trinity pattern
# 20_helpers/contact_helpers.sql - Helper functions (contact_pk, contact_id, etc.)
# 30_functions/create_contact.sql  - PL/pgSQL function
# 30_functions/qualify_lead.sql    - PL/pgSQL function
```

## Step 4: Deploy to Database (1 minute)

```bash
# Setup database
createdb specql_demo

# Run migrations with Confiture
cd db/schema
confiture migrate up

# Verify
psql specql_demo -c "\dt crm.*"
# You should see: crm.tb_contact
```

## Step 5: Test It Works (1 minute)

```bash
# Create a contact
psql specql_demo <<EOF
SELECT crm.create_contact(
  email := 'john@example.com',
  first_name := 'John',
  last_name := 'Doe',
  status := 'lead'
);
EOF

# Qualify the lead
psql specql_demo <<EOF
SELECT crm.qualify_lead(
  contact_id := (SELECT id FROM crm.tb_contact WHERE email = 'john@example.com')
);
EOF

# Check results
psql specql_demo -c "SELECT * FROM crm.tb_contact;"
```

## What You Got (Automatically)

### 1. Production Database Schema
```sql
-- Trinity Pattern table
CREATE TABLE crm.tb_contact (
  -- Trinity Pattern (best practice)
  pk_contact INTEGER PRIMARY KEY,           -- Performance
  id UUID DEFAULT gen_random_uuid(),        -- Stable API
  identifier TEXT NOT NULL,                 -- Human-readable

  -- Your fields with validation
  email TEXT NOT NULL CHECK (email ~ '^[a-zA-Z0-9._%+-]+@...'),
  phone TEXT CHECK (phone ~ '^\+[1-9]\d{1,14}$'),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  company_name TEXT,
  status TEXT CHECK (status IN ('lead', 'qualified', 'customer')),
  score NUMERIC(5,2) CHECK (score >= 0 AND score <= 100),

  -- Automatic audit trails
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by UUID,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID
);
```

### 2. Helper Functions
```sql
-- Get INTEGER primary key from UUID
CREATE FUNCTION crm.contact_pk(contact_id UUID) RETURNS INTEGER;

-- Get UUID from INTEGER primary key
CREATE FUNCTION crm.contact_id(pk INTEGER) RETURNS UUID;

-- Get identifier from UUID
CREATE FUNCTION crm.contact_identifier(contact_id UUID) RETURNS TEXT;
```

### 3. Business Logic Functions
```sql
-- FraiseQL-compliant mutation
CREATE FUNCTION crm.create_contact(
  email TEXT,
  first_name TEXT,
  last_name TEXT,
  ...
) RETURNS app.mutation_result;

-- With error handling, validation, audit trails
CREATE FUNCTION crm.qualify_lead(
  contact_id UUID
) RETURNS app.mutation_result;
```

### 4. Indexes
```sql
-- Unique constraints
CREATE UNIQUE INDEX idx_tb_contact_id ON crm.tb_contact(id);
CREATE UNIQUE INDEX idx_tb_contact_email ON crm.tb_contact(email);

-- Performance indexes
CREATE INDEX idx_tb_contact_status ON crm.tb_contact(status);
```

### 5. GraphQL Ready
All functions automatically discoverable by FraiseQL:
```graphql
mutation QualifyLead($contactId: UUID!) {
  qualifyLead(contactId: $contactId) {
    success
    message
    object {
      id
      email
      firstName
      status
    }
  }
}
```

## Next Steps

### Add More Features

```yaml
# Add a Company entity
entity: Company
schema: crm
fields:
  name: text!
  domain: domainName  # Rich type with validation
  website: url

# Reference it from Contact
entity: Contact
fields:
  company: ref(Company)  # Automatic foreign key!
```

### Use stdlib Entities

```bash
# Import production-ready entities
cp stdlib/crm/organization.yaml entities/
cp stdlib/crm/contact.yaml entities/
specql generate entities/*.yaml
```

### Explore Rich Types

Try these validated types:
- `email`, `phone`, `url` - Automatic regex validation
- `money`, `percentage` - Automatic range validation
- `coordinates` - PostgreSQL POINT with spatial indexes
- `date`, `datetime`, `time` - Temporal types
- `slug`, `markdown`, `html` - Content types

### Add Complex Actions

```yaml
actions:
  - name: create_opportunity
    steps:
      - validate: company IS NOT NULL
      - validate: email MATCHES email_pattern
      - insert: Contact
      - call: send_welcome_email(contact.email)
      - notify: sales_team "New opportunity from {company}"
```

## Common Patterns

### Multi-Tenancy
```yaml
entity: Contact
schema: tenant  # Automatic tenant_id + RLS policies
```

### Hierarchical Data
```yaml
entity: Organization
fields:
  parent: ref(Organization)  # Self-reference = hierarchy
  identifier: hierarchical   # Automatic path calculation
```

### Soft Deletes
```yaml
# Automatic! Every entity gets:
# - deleted_at TIMESTAMPTZ
# - deleted_by UUID
# Actions exclude deleted records by default
```

## Troubleshooting

### "Permission denied for schema"
```bash
# Grant access
psql specql_demo -c "GRANT ALL ON SCHEMA crm TO current_user;"
```

### "Function does not exist"
```bash
# Re-run migration
confiture migrate down
confiture migrate up
```

### "CHECK constraint violation"
```bash
# Check your data matches the rich type format
# Example: email must be valid, phone must be E.164
```

## Learning Resources

- **Examples**: See `entities/examples/` directory
- **stdlib**: Browse 30 production entities in `stdlib/`
- **Guides**: Read `docs/guides/` for deep dives
- **Tests**: Check `tests/integration/` for usage patterns

## Quick Reference

```bash
# Generate schema
specql generate entities/*.yaml

# Validate YAML
specql validate entities/*.yaml

# Show schema diff
specql diff entities/contact.yaml

# Generate with frontend code
specql generate entities/*.yaml --with-impacts
```

---

**You just built a production backend in 5 minutes!** 🎉

**Next**: Read the [User Guide](docs/guides/) or explore [stdlib](stdlib/README.md)