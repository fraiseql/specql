# Your First SpecQL Entity

> **Create your first SpecQL entity in 10 minutes and see the power of 100x code generation**

## What You'll Learn

In this tutorial, you'll create a `Contact` entity and generate:
- PostgreSQL table with Trinity pattern (pk_*, id, identifier)
- GraphQL mutations and queries
- TypeScript types
- CRUD operations

**Result**: 12 lines of YAML → 2000+ lines of production code

---

## Prerequisites

```bash
# Install SpecQL
pip install specql

# Verify installation
specql --version
```

**You'll also need**:
- PostgreSQL running (local or remote)
- Text editor (VS Code recommended)

---

## Step 1: Create Your First Entity (3 minutes)

Create a file `entities/contact.yaml`:

```yaml
entity: Contact
schema: crm

fields:
  email: email!
  first_name: text!
  last_name: text!
  phone: phoneNumber
  company: ref(Company)!
  status: enum(lead, qualified, customer) = 'lead'
```

**That's it!** Just 12 lines of business domain YAML.

### What Each Line Means

```yaml
entity: Contact           # Entity name (becomes tb_contact table)
schema: crm               # Database schema name

fields:
  email: email!           # Required email with validation
  first_name: text!       # Required text field
  last_name: text!        # Required text field
  phone: phoneNumber      # Optional phone (E.164 format)
  company: ref(Company)!  # Required foreign key to Company
  status: enum(lead, qualified, customer) = 'lead'  # Enum with default
```

---

## Step 2: Create Referenced Entity (2 minutes)

SpecQL needs the `Company` entity referenced above.

Create `entities/company.yaml`:

```yaml
entity: Company
schema: crm

fields:
  name: text!
  website: url
```

---

## Step 3: Generate SQL (1 minute)

```bash
specql generate entities/*.yaml --output generated/
```

**Output**:
```
✅ Generating schema...
   entities/contact.yaml → generated/schema/10_tables/contact.sql
   entities/company.yaml → generated/schema/10_tables/company.sql

✅ Generating functions...
   Auto-CRUD for Contact
   Auto-CRUD for Company

✅ Generating GraphQL schema...
   generated/graphql/schema.graphql

✨ Complete! Generated 2,347 lines from 19 lines of YAML
```

---

## Step 4: Review Generated Code (2 minutes)

### Generated PostgreSQL Table

**File**: `generated/schema/10_tables/contact.sql`

```sql
-- Trinity Pattern Table
CREATE TABLE crm.tb_contact (
    -- Trinity Pattern: 3 ways to reference
    pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT UNIQUE NOT NULL,

    -- Your business fields
    email TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    fk_company INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'lead',

    -- Auto-generated audit fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,

    -- Foreign key constraint
    CONSTRAINT fk_contact_company
        FOREIGN KEY (fk_company)
        REFERENCES crm.tb_company(pk_company)
        ON DELETE RESTRICT,

    -- Email validation constraint
    CONSTRAINT chk_contact_email
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),

    -- Enum constraint
    CONSTRAINT chk_contact_status
        CHECK (status IN ('lead', 'qualified', 'customer'))
);

-- Auto-generated indexes
CREATE UNIQUE INDEX idx_tb_contact_email ON crm.tb_contact (email);
CREATE INDEX idx_tb_contact_company ON crm.tb_contact (fk_company);
CREATE INDEX idx_tb_contact_status ON crm.tb_contact (status);

-- Helper functions
CREATE FUNCTION crm.contact_pk(p_id UUID) RETURNS INTEGER AS $$
    SELECT pk_contact FROM crm.tb_contact WHERE id = p_id;
$$ LANGUAGE SQL STABLE;

CREATE FUNCTION crm.contact_id(p_pk INTEGER) RETURNS UUID AS $$
    SELECT id FROM crm.tb_contact WHERE pk_contact = p_pk;
$$ LANGUAGE SQL STABLE;

-- Plus 50+ more lines of helper functions, triggers, and audit logic...
```

### Generated GraphQL Schema

**File**: `generated/graphql/schema.graphql`

```graphql
type Contact {
  id: ID!
  identifier: String!
  email: String!
  firstName: String!
  lastName: String!
  phone: String
  company: Company!
  status: ContactStatus!
  createdAt: DateTime!
  updatedAt: DateTime!
}

enum ContactStatus {
  LEAD
  QUALIFIED
  CUSTOMER
}

type Query {
  contact(id: ID!): Contact
  contacts(
    limit: Int
    offset: Int
    where: ContactFilter
  ): [Contact!]!
}

type Mutation {
  createContact(input: CreateContactInput!): MutationResult!
  updateContact(id: ID!, input: UpdateContactInput!): MutationResult!
  deleteContact(id: ID!): MutationResult!
}

# Plus 100+ more lines of input types, filters, mutations...
```

### Generated TypeScript Types

**File**: `generated/typescript/types/contact.ts`

```typescript
export interface Contact {
  id: string;
  identifier: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  company: Company;
  status: ContactStatus;
  createdAt: Date;
  updatedAt: Date;
}

export enum ContactStatus {
  Lead = 'lead',
  Qualified = 'qualified',
  Customer = 'customer',
}

export interface CreateContactInput {
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  companyId: string;
  status?: ContactStatus;
}

export interface MutationResult<T = any> {
  status: 'success' | 'error';
  code: string;
  message?: string;
  data?: T;
}

// Plus Apollo hooks and more...
```

---

## Step 5: Deploy to Database (2 minutes)

```bash
# Run generated SQL on your database
psql -U postgres -d myapp -f generated/schema/00_framework/app_schema.sql
psql -U postgres -d myapp -f generated/schema/10_tables/company.sql
psql -U postgres -d myapp -f generated/schema/10_tables/contact.sql
```

**Or use migrations** (recommended for production):
```bash
# Copy to your migrations directory
cp generated/schema/10_tables/*.sql migrations/001_initial_schema.sql

# Run with your migration tool
./migrate up
```

---

## What Just Happened?

### From 12 Lines of YAML...

```yaml
entity: Contact
schema: crm
fields:
  email: email!
  first_name: text!
  last_name: text!
  phone: phoneNumber
  company: ref(Company)!
  status: enum(lead, qualified, customer) = 'lead'
```

### To 2000+ Lines of Production Code

1. **PostgreSQL Schema** (500+ lines)
   - Trinity pattern table
   - Foreign key constraints
   - Email/phone validation
   - Automatic indexes
   - Helper functions
   - Audit triggers

2. **GraphQL API** (800+ lines)
   - Complete CRUD mutations
   - Filtered queries
   - Input types
   - FraiseQL metadata

3. **TypeScript Types** (700+ lines)
   - Interface definitions
   - Enum types
   - Apollo hooks
   - Form helpers

**Ratio**: 12 lines → 2,000+ lines = **166x leverage**

---

## Understanding the Trinity Pattern

SpecQL uses the **Trinity Pattern** for flexible entity referencing:

```sql
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY,  -- Database internal (fast joins)
    id UUID UNIQUE,                  -- External API (secure, portable)
    identifier TEXT UNIQUE,          -- Human-readable (URL-friendly)
    ...
);
```

**Use each for different scenarios**:

| Field | Use Case | Example |
|-------|----------|---------|
| `pk_contact` | Internal joins | `JOIN orders ON orders.fk_contact = contacts.pk_contact` |
| `id` | GraphQL API | `query { contact(id: "550e8400-...") }` |
| `identifier` | URLs | `/contacts/CONTACT-ACME-12345` |

**Benefits**:
- **Performance**: INTEGER joins are 3x faster than UUID
- **Security**: UUIDs hide internal IDs
- **UX**: Identifiers are readable in URLs

---

## Next Steps

### Add Business Logic

Edit `entities/contact.yaml` to add an action:

```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead', error: "Only leads can be qualified"
      - update: Contact SET status = 'qualified'
      - notify: lead_qualified, to: $email
```

Regenerate:
```bash
specql generate entities/*.yaml --output generated/
```

**Result**: New PL/pgSQL function + GraphQL mutation generated automatically.

### Tutorials

- **[Your First Action](../05_guides/your-first-action.md)** - Add business logic
- **[Your First Entity (Detailed)](../05_guides/your-first-entity.md)** - Deep dive

### Core Concepts

- **[Business YAML](../03_core-concepts/business-yaml.md)** - Full YAML syntax
- **[Rich Types](../03_core-concepts/rich-types.md)** - email, money, phoneNumber, etc.
- **[Actions](../03_core-concepts/actions.md)** - Business logic steps
- **[Trinity Pattern](../03_core-concepts/trinity-pattern.md)** - Triple identity system

### Guides

- **[Relationships](../05_guides/relationships.md)** - Foreign keys and joins
- **[Multi-Tenancy](../05_guides/multi-tenancy.md)** - SaaS applications
- **[Validation](validation.md)** - Business rules

### Reference

- **[YAML Syntax](../06_reference/yaml-syntax.md)** - Complete syntax reference
- **[CLI Commands](../06_reference/cli-commands.md)** - Command-line tools

---

## Common Questions

### Q: Do I need to write SQL?

**A**: No. SpecQL generates all SQL, GraphQL, and TypeScript for you. You only write business domain YAML.

### Q: What if I need custom SQL?

**A**: You can call custom PL/pgSQL functions from actions:

```yaml
actions:
  - name: complex_calculation
    steps:
      - call: my_custom_function, args: {param: $value}
      - update: Entity SET result = $function_result
```

### Q: How do I handle migrations?

**A**: SpecQL generates idempotent SQL. Use standard PostgreSQL migration tools (Flyway, Liquibase, etc.) to apply changes.

### Q: Can I use SpecQL with existing databases?

**A**: Yes! Use reverse engineering:

```bash
specql reverse --source sql --path ./database/ --output entities/
```

See [Migration Guides](../02_migration/index.md).

### Q: What about performance?

**A**: SpecQL generates highly optimized PostgreSQL code:
- Automatic indexes on foreign keys
- Trinity pattern for fast INTEGER joins
- No ORM overhead (direct PL/pgSQL)
- Query planner can optimize generated SQL

Typically **2-5x faster** than ORMs like Django or TypeORM.

---

## Troubleshooting

### Error: "Schema not found"

**Solution**: Create schema first:
```sql
CREATE SCHEMA IF NOT EXISTS crm;
```

### Error: "Referenced entity Company not found"

**Solution**: Generate Company entity first or generate all at once:
```bash
specql generate entities/*.yaml
```

### Error: "Invalid email format"

**Cause**: Email validation is strict (RFC 5322 compliant).

**Solution**: Use valid email addresses in your data.

---

## Summary

You've learned how to:
- ✅ Define entities in YAML (business domain only)
- ✅ Generate production PostgreSQL schema
- ✅ Create GraphQL API automatically
- ✅ Generate TypeScript types
- ✅ Deploy to database

**Key Takeaway**: SpecQL gives you 100x leverage—write business logic, get production infrastructure.

**Next**: [Add business logic with actions](../05_guides/your-first-action.md) →

---

**Welcome to SpecQL—business domain first, implementation automatic.**
