# Quick Start with SpecQL

**Goal**: Generate your first PostgreSQL schema in 5 minutes

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Basic YAML knowledge

## Installation

```bash
pip install specql-generator
specql --version
```

## Your First Entity

### Step 1: Create Entity File

Create `contact.yaml`:

```yaml
# Based on entities/examples/contact_lightweight.yaml
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)
  phone: text

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")

  - name: create_contact
    steps:
      - validate: email MATCHES email_pattern
        error: "invalid_email"
      - validate: first_name IS NOT NULL
        error: "first_name_required"
      - insert: Contact
```

### Step 2: Generate Code

```bash
specql generate contact.yaml
```

### Step 3: What Gets Generated

**Output structure** (with `--hierarchical`, default):
```
migrations/
├── 01_write_side/
│   ├── 012_crm/
│   │   └── 0123_customer/
│   │       └── 01236_contact/
│   │           ├── 012361_tb_contact.sql          # Table
│   │           └── 012362_fn_qualify_lead.sql      # Action
└── 02_query_side/
    └── 022_crm/
        └── 0223_customer/
            └── 0220310_tv_contact.sql              # Query view
```

**Or with `--dev` (flat structure)**:
```
db/schema/
├── 10_tables/
│   └── contact.sql
├── 20_views/
│   └── contact_view.sql
└── 30_functions/
    └── qualify_lead.sql
```

### Step 4: Inspect Generated SQL

**Table** (`012361_tb_contact.sql`):
```sql
-- Trinity Pattern automatically applied
CREATE TABLE IF NOT EXISTS crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT,

    -- Your business fields
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    fk_company INTEGER REFERENCES crm.tb_company(pk_company),
    status TEXT CHECK (status IN ('lead', 'qualified', 'customer')),
    phone TEXT,

    -- Audit fields (automatic)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    created_by UUID,
    updated_by UUID,

    UNIQUE(id),
    UNIQUE(identifier)
);

-- Indexes (automatic)
CREATE INDEX IF NOT EXISTS idx_tb_contact_fk_company
    ON crm.tb_contact(fk_company) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tb_contact_status
    ON crm.tb_contact(status) WHERE deleted_at IS NULL;
```

**Action** (`012362_fn_qualify_lead.sql`):
```sql
-- Core business logic function
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID DEFAULT NULL
)
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_pk INTEGER;
    v_status TEXT;
BEGIN
    -- Trinity resolution: UUID → INTEGER
    SELECT pk_contact, status INTO v_contact_pk, v_status
    FROM crm.tb_contact
    WHERE id = p_contact_id AND deleted_at IS NULL;

    -- Validation
    IF v_status != 'lead' THEN
        RETURN app.error('not_a_lead', 'Contact is not a lead');
    END IF;

    -- Update
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = NOW(),
        updated_by = p_caller_id
    WHERE pk_contact = v_contact_pk;

    -- Notify
    -- (notification logic)

    -- Return success
    RETURN app.success('Contact qualified', jsonb_build_object(
        'id', p_contact_id,
        'status', 'qualified'
    ));
END;
$$;

-- GraphQL wrapper (FraiseQL standard)
CREATE OR REPLACE FUNCTION app.qualify_lead(args JSONB)
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN crm.qualify_lead(
        (args->>'contact_id')::UUID,
        (args->>'caller_id')::UUID
    );
END;
$$;
```

### Step 5: Apply to Database

```bash
psql -d mydb -f migrations/**/*.sql
# Or with flat structure:
psql -d mydb -f db/schema/**/*.sql
```

### Step 6: Use from GraphQL

Auto-generated GraphQL mutation:
```graphql
mutation QualifyLead($contactId: UUID!) {
  qualifyLead(contactId: $contactId) {
    success
    message
    object
    errors {
      code
      message
    }
  }
}
```

## CLI Options

**Most useful flags**:

```bash
# Hierarchical structure with registry codes (default)
specql generate contact.yaml

# Flat structure for development
specql generate contact.yaml --dev

# Dry run (preview without writing files)
specql generate contact.yaml --dry-run

# Generate with frontend code
specql generate contact.yaml --with-impacts --output-frontend=src/generated

# Include table views
specql generate contact.yaml --include-tv

# Verbose output
specql generate contact.yaml --verbose
```

**All available flags**:
- `--output-dir` - Output directory (default: migrations)
- `--foundation-only` - Generate only app foundation
- `--include-tv` - Generate table views
- `--framework` - Target framework (fraiseql, django, rails, prisma)
- `--target` - Target language (postgresql, python_django, python_sqlalchemy)
- `--use-registry` - Use hexadecimal registry (default: true)
- `--output-format` - hierarchical or confiture
- `--hierarchical` / `--flat` - File structure
- `--dry-run` - Preview without writing
- `--with-impacts` - Generate mutation impacts JSON
- `--output-frontend` - Generate frontend code
- `--with-query-patterns` - Generate SQL views from patterns
- `--with-audit-cascade` - Integrate cascade with audit trail
- `--with-outbox` - Generate CDC outbox table
- `--dev` - Development mode (flat structure)
- `--no-tv` - Skip table view generation
- `--verbose` / `-v` - Detailed progress

## Next Steps

- 🎓 [Complete Tutorial](../01_tutorials/beginner/contact_manager.md)
- 📖 [Core Concepts](core_concepts.md)
- 🔧 [CLI Reference](../../03_reference/cli/command_reference.md)
- 💬 [Join Discord](https://discord.gg/specql) for help

## Common Questions

**Q: Where are the TypeScript types?**
A: Use `--output-frontend=src/generated` to generate TypeScript types, Apollo hooks, and documentation.

**Q: Can I customize the generated SQL?**
A: SpecQL focuses on conventions over configuration. For custom SQL, use raw SQL files alongside generated files.

**Q: How do I handle migrations?**
A: Generated files are idempotent (`CREATE IF NOT EXISTS`, `CREATE OR REPLACE`). Run them multiple times safely.

**Q: What's the Trinity pattern?**
A: Three identifiers: `pk_*` (INTEGER for JOINs), `id` (UUID for APIs), `identifier` (TEXT for humans). See [Trinity Pattern Guide](../02_guides/database/trinity_pattern.md).