# Your First Entity

## Overview

In this guide, you'll create your first SpecQL entity and generate a PostgreSQL table with GraphQL integration.

**Time**: 5 minutes
**Prerequisites**: [Installation](installation.md) complete

## Step 1: Create Entity Directory

```bash
# Create entities directory
mkdir -p entities

# Verify structure
tree entities/
# entities/
```

## Step 2: Create Contact Entity

Create `entities/contact.yaml`:

```yaml
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: text
  first_name: text
  last_name: text
  company: text?
  notes: text?
```

**What this defines**:
- **Entity**: `Contact` (PascalCase, singular)
- **Schema**: `crm` (snake_case, must be in domain registry)
- **Fields**: Business data fields
- **Modifiers**: `?` makes fields nullable

## Step 3: Validate Syntax

```bash
# Check for syntax errors
specql validate entities/contact.yaml

# Expected output:
# ✅ entities/contact.yaml: Valid
```

## Step 4: Generate Schema

```bash
# Generate PostgreSQL schema
specql generate entities/contact.yaml

# Check output
ls -la db/schema/10_tables/
# contact.sql
```

## Step 5: Review Generated SQL

```bash
# View the generated table
cat db/schema/10_tables/contact.sql
```

**What SpecQL generates**:

```sql
-- Auto-generated table with Trinity pattern
CREATE TABLE crm.tb_contact (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  pk_contact UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
  identifier TEXT UNIQUE NOT NULL,

  -- Your fields
  email TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  company TEXT,
  notes TEXT,

  -- Auto-generated audit fields
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  created_by UUID NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_by UUID NOT NULL,
  deleted_at TIMESTAMP WITH TIME ZONE,
  deleted_by UUID
);

-- Auto-generated indexes
CREATE UNIQUE INDEX idx_tb_contact_email ON crm.tb_contact(email);
CREATE INDEX idx_tb_contact_company ON crm.tb_contact(company);
```

## Step 6: Apply to Database

```bash
# Apply foundation (types, schemas)
psql $DATABASE_URL -f db/schema/00_foundation/000_app_foundation.sql

# Apply your table
psql $DATABASE_URL -f db/schema/10_tables/contact.sql

# Apply helpers and functions
psql $DATABASE_URL -f db/schema/20_helpers/contact_helpers.sql
psql $DATABASE_URL -f db/schema/30_functions/*.sql
```

## Step 7: Test Your Table

```bash
# Connect to database
psql $DATABASE_URL

# Check table exists
\d crm.tb_contact

# Insert test data
INSERT INTO crm.tb_contact (email, first_name, last_name)
VALUES ('john@example.com', 'John', 'Doe');

# Query data
SELECT * FROM crm.tb_contact;

# Use helper functions
SELECT crm.contact_pk(uuid_column) FROM crm.tb_contact;
```

## Understanding the Trinity Pattern

SpecQL automatically adds three identifiers to every entity:

1. **`id`** - INTEGER primary key (internal use)
2. **`pk_contact`** - UUID stable identifier (external APIs)
3. **`identifier`** - TEXT human-readable slug (URLs, exports)

```sql
-- Example data
SELECT id, pk_contact, identifier, email FROM crm.tb_contact;

-- Output:
-- id | pk_contact | identifier | email
-- ---|-----------|------------|--------
-- 1  | a1b2c3... | john-doe   | john@example.com
```

## Adding Relationships

Let's add a relationship to a Company entity:

```yaml
# entities/company.yaml
entity: Company
schema: crm
fields:
  name: text
  website: text?

# entities/contact.yaml (updated)
entity: Contact
schema: crm
fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)  # Foreign key reference
  notes: text?
```

**Generated foreign key**:
```sql
-- Auto-generated constraint
ALTER TABLE crm.tb_contact
ADD CONSTRAINT fk_tb_contact_company
FOREIGN KEY (company) REFERENCES crm.tb_company(id);
```

## Next Steps

- [Add your first action](your-first-action.md)
- [Learn about field types](../../reference/yaml-reference.md#scalar-types)
- [Set up multi-tenancy](../../guides/multi-tenancy.md)
- [Migrate existing data](../../guides/migration-guide.md)

## Troubleshooting

**"Schema 'crm' not found in domain registry"**
```bash
# Add to registry/domain_registry.yaml
domains:
  crm:
    type: multi_tenant
```

**"Command not found: specql"**
```bash
# Use uv run
uv run specql validate entities/contact.yaml
```

**"Permission denied"**
```bash
# Check database permissions
psql $DATABASE_URL -c "\dn"  # List schemas
psql $DATABASE_URL -c "\dt crm.*"  # List tables
```