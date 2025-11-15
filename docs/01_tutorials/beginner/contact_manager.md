# Contact Manager Tutorial

**Build a complete contact management system** - From YAML to production database

This tutorial walks you through building a contact manager with lead qualification, validation, and notifications. You'll learn the core SpecQL concepts while building something real.

## 🎯 What You'll Build

A contact management system with:
- Contact storage with validation
- Lead qualification workflow
- Email notifications
- Type-safe GraphQL API
- Automatic database migrations

## 📋 Prerequisites

- Completed [Quick Start Guide](../00_getting_started/QUICKSTART.md)
- Basic understanding of YAML
- PostgreSQL database for testing

## 🏗️ Step 1: Project Setup

Create a new directory for your contact manager:

```bash
mkdir contact-manager
cd contact-manager
```

## 📝 Step 2: Define Your Entities

Create `entities/contact.yaml`:

```yaml
# Contact entity - our main business object
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: text
  first_name: text
  last_name: text
  status: enum(lead, qualified, customer)
  phone: text
  notes: text

actions:
  # Lead qualification - core business logic
  - name: qualify_lead
    requires: caller.can_edit_contact
    description: "Convert a lead to a qualified prospect"
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")

  # Contact creation with validation
  - name: create_contact
    description: "Create a new contact with validation"
    steps:
      - validate: email MATCHES email_pattern
        error: "invalid_email"
      - validate: first_name IS NOT NULL
        error: "first_name_required"
      - insert: Contact

  # Status update with business rules
  - name: update_status
    requires: caller.can_edit_contact
    description: "Update contact status with validation"
    steps:
      - validate: status IN ('lead', 'qualified', 'customer')
        error: "invalid_status"
      - validate: status != 'customer' OR notes IS NOT NULL
        error: "notes_required_for_customer"
      - update: Contact SET status = $status
```

## 🔧 Step 3: Generate the Code

Generate your PostgreSQL schema and functions:

```bash
specql generate entities/contact.yaml
```

This creates the hierarchical migration structure:
```
migrations/
├── 01_write_side/
│   └── 012_crm/
│       └── 0123_customer/
│           └── 01236_contact/
│               ├── 012361_tb_contact.sql          # Table DDL
│               ├── 012362_fn_qualify_lead.sql     # Business logic
│               ├── 012363_fn_create_contact.sql   # Creation logic
│               └── 012364_fn_update_status.sql    # Update logic
└── 02_query_side/
    └── 022_crm/
        └── 0223_customer/
            └── 0220310_tv_contact.sql              # Query view
```

## 🗄️ Step 4: Inspect Generated Database Schema

Let's look at what SpecQL generated:

**Table Structure** (`012361_tb_contact.sql`):
```sql
-- Trinity Pattern: pk_*, id, identifier
CREATE TABLE IF NOT EXISTS crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT,

    -- Your business fields
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    status TEXT CHECK (status IN ('lead', 'qualified', 'customer')),
    phone TEXT,
    notes TEXT,

    -- Audit fields (automatic)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    created_by UUID,
    updated_by UUID,

    UNIQUE(id),
    UNIQUE(identifier)
);

-- Performance indexes (automatic)
CREATE INDEX IF NOT EXISTS idx_tb_contact_status
    ON crm.tb_contact(status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tb_contact_email
    ON crm.tb_contact(email) WHERE deleted_at IS NULL;
```

**Business Logic Function** (`012362_fn_qualify_lead.sql`):
```sql
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
    v_email TEXT;
BEGIN
    -- Trinity resolution: UUID → INTEGER
    SELECT pk_contact, status, email INTO v_contact_pk, v_status, v_email
    FROM crm.tb_contact
    WHERE id = p_contact_id AND deleted_at IS NULL;

    -- Business validation
    IF v_status != 'lead' THEN
        RETURN app.error('not_a_lead', 'Contact is not a lead');
    END IF;

    -- Business logic
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = NOW(),
        updated_by = p_caller_id
    WHERE pk_contact = v_contact_pk;

    -- Notification (placeholder for email system)
    -- Integration point for your email service
    RAISE NOTICE 'Notification: Contact % qualified - email: %', p_contact_id, v_email;

    -- Success response
    RETURN app.success('Contact qualified', jsonb_build_object(
        'id', p_contact_id,
        'status', 'qualified'
    ));
END;
$$;
```

## 🚀 Step 5: Apply to Database

Create a test database and apply the migrations:

```bash
# Create database
createdb contact_manager

# Apply migrations
psql -d contact_manager -f migrations/**/*.sql
```

## 🔍 Step 6: Test the Business Logic

Test your generated functions:

```sql
-- Insert test data
INSERT INTO crm.tb_contact (email, first_name, last_name, status)
VALUES ('john@example.com', 'John', 'Doe', 'lead');

-- Test qualification
SELECT * FROM app.qualify_lead('{"contact_id": "your-uuid-here"}'::jsonb);

-- Check result
SELECT id, email, first_name, status, updated_at FROM crm.tb_contact;
```

## 🌐 Step 7: Generate GraphQL API

Generate with frontend support:

```bash
specql generate entities/contact.yaml \
  --with-impacts \
  --output-frontend=src/generated
```

This creates:
- GraphQL schema definitions
- TypeScript types
- Apollo React hooks
- Mutation impact metadata

## 📱 Step 8: Use from Frontend

**Generated TypeScript Types**:
```typescript
// src/generated/types.ts
export interface Contact {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  status: 'lead' | 'qualified' | 'customer';
  phone?: string;
  notes?: string;
}

export interface QualifyLeadVariables {
  contactId: string;
}

export interface QualifyLeadResponse {
  success: boolean;
  message: string;
  object: {
    id: string;
    status: string;
  };
  errors?: Array<{
    code: string;
    message: string;
  }>;
}
```

**Generated Apollo Hook**:
```typescript
// src/generated/hooks.ts
import { useMutation } from '@apollo/client';

export const useQualifyLead = () => {
  return useMutation<QualifyLeadResponse, QualifyLeadVariables>(
    gql`
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
    `
  );
};
```

**Usage in React**:
```typescript
// ContactList.tsx
import { useQualifyLead } from '../generated/hooks';

function ContactList() {
  const [qualifyLead] = useQualifyLead();

  const handleQualify = async (contactId: string) => {
    const result = await qualifyLead({
      variables: { contactId }
    });

    if (result.data?.success) {
      console.log('Contact qualified!');
    }
  };

  return (
    <div>
      {/* Your contact list UI */}
      <button onClick={() => handleQualify(contact.id)}>
        Qualify Lead
      </button>
    </div>
  );
}
```

## 🧪 Step 9: Testing Your Code

While SpecQL doesn't currently generate tests automatically, you can test your generated functions manually:

```sql
-- Test the qualify_lead function
SELECT * FROM crm.fn_qualify_lead(
    'your-contact-uuid'::uuid,
    'caller-uuid'::uuid
);

-- Verify the contact was updated
SELECT id, status, updated_at FROM crm.tv_contact WHERE id = 'your-contact-uuid';
```

**Future**: Test generation will be available in v0.5.0 with `--with-tests` flag.

## 🎯 Step 10: Extend Your System

Add more entities to create a complete CRM:

**Company Entity** (`entities/company.yaml`):
```yaml
entity: Company
schema: crm
description: "Company information"

fields:
  name: text
  website: url
  industry: text
  size: enum(startup, small, medium, enterprise)

actions:
  - name: create_company
    steps:
      - validate: name IS NOT NULL
      - insert: Company
```

**Update Contact** to reference Company:
```yaml
# In contact.yaml
fields:
  # ... existing fields ...
  company: ref(Company)  # Now references Company entity
```

## 📊 Step 11: View Your Data

Generate table views for reporting:

```bash
specql generate entities/*.yaml --include-tv
```

This creates query-optimized views:
```sql
-- tv_contact - Query view with JOINs
CREATE OR REPLACE VIEW crm.tv_contact AS
SELECT
    c.id,
    c.email,
    c.first_name,
    c.last_name,
    c.status,
    c.phone,
    comp.name as company_name,
    c.created_at,
    c.updated_at
FROM crm.tb_contact c
LEFT JOIN crm.tb_company comp ON c.fk_company = comp.pk_company
WHERE c.deleted_at IS NULL;
```

## 🚀 Step 12: Deploy to Production

Your migrations are idempotent - run them safely multiple times:

```bash
# Production deployment
psql -d production_db -f migrations/**/*.sql

# Rollbacks handled by your migration system
# No custom rollback scripts needed
```

## 🎉 What You've Learned

✅ **Entity Definition**: How to define business entities in YAML
✅ **Field Types**: Text, enums, references, and validation
✅ **Actions**: Business logic with validation and updates
✅ **Trinity Pattern**: pk_*, id, identifier for different use cases
✅ **GraphQL Integration**: Automatic API generation
✅ **TypeScript Types**: Type-safe frontend integration
✅ **Testing**: Automatic test generation
✅ **Migrations**: Safe, idempotent database changes

## 🔄 Next Steps

- **[Simple Blog Example](../../06_examples/SIMPLE_BLOG.md)** - Content management system
- **[E-commerce Example](../../06_examples/ECOMMERCE_SYSTEM.md)** - Complex business logic
- **[CRM Example](../../06_examples/CRM_SYSTEM_COMPLETE.md)** - Complete business application

## 💡 Key Concepts Covered

- **Business Logic in YAML**: Declarative action definitions
- **Automatic Validation**: Field and business rule validation
- **Type Safety**: End-to-end TypeScript integration
- **Audit Trail**: Automatic created/updated tracking
- **Soft Deletes**: deleted_at pattern for data integrity
- **Performance**: Automatic indexing strategies

## 🆘 Troubleshooting

**"Function does not exist" errors?**
- Ensure migrations are applied in order
- Check schema names match your database setup

**GraphQL mutations not working?**
- Verify `--with-impacts` flag was used
- Check Apollo Client configuration

**TypeScript errors?**
- Regenerate with `--output-frontend` flag
- Update your TypeScript configuration

---

**Congratulations!** You've built a production-ready contact management system with just YAML definitions. This same approach scales to complex enterprise applications.