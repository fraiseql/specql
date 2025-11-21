# Getting Started: Your First SpecQL Backend

> **Complete this guide in 30 minutes to have a production PostgreSQL + GraphQL backend**

## What You'll Build

A complete Contact management system with:
- ✅ PostgreSQL database with proper constraints
- ✅ GraphQL API with auto-generated mutations
- ✅ TypeScript types for frontend integration
- ✅ Automatic validation and error handling

## Prerequisites

- ✅ PostgreSQL 14+ installed and running
- ✅ Python 3.11+ installed
- ✅ Basic command line knowledge

```bash
# Verify your setup
postgres --version  # Should show 14+
python --version    # Should show 3.11+
```

## Step 1: Install SpecQL (2 minutes)

```bash
# Install SpecQL
pip install specql

# Verify installation
specql --version
```

**Expected output:**
```
SpecQL 0.1.0
```

> **Troubleshooting**: If you get a "command not found" error, try `python -m specql --version`

## Step 2: Define Your First Entity (3 minutes)

Create a file called `contact.yaml`:

```yaml
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: email!              # Rich type: auto-validates email format
  first_name: text!          # Required text field
  last_name: text!           # Required text field
  phone: phone               # Optional phone number (E.164 format)

actions:
  - name: create_contact     # Auto-generates CRUD operations
  - name: update_contact
```

**What this defines:**
- A `Contact` entity in the `crm` schema
- Email validation and required field constraints
- Automatic CRUD actions with error handling

## Step 3: Generate Your Backend (2 minutes)

```bash
# Generate everything from your YAML
specql generate contact.yaml

# See what was created
ls -la
```

**Generated files:**
```
db/
├── schema/
│   ├── crm.contact.table.sql      # PostgreSQL table DDL
│   ├── crm.contact.actions.sql    # PL/pgSQL functions
│   └── crm.contact.graphql.sql    # GraphQL schema
├── migrations/
│   └── 001_initial_schema.sql     # Migration script
└── types/
    └── contact.types.ts           # TypeScript types
```

## Step 4: Deploy & Test (5 minutes)

```bash
# Create database
createdb specql_demo

# Run the generated migration
psql specql_demo < db/migrations/001_initial_schema.sql

# Verify the table was created
psql specql_demo -c "\d crm.contact"
```

**Expected output:**
```
Table "crm.contact"
Column     | Type                  | Modifiers
-----------+-----------------------+-----------
pk_contact | integer               | not null
id         | uuid                  | not null
identifier | text                  |
tenant_id  | uuid                  |
email      | text                  | not null
first_name | text                  | not null
last_name  | text                  | not null
phone      | text                  |
... (audit fields)
```

## Step 5: Test the GraphQL API (5 minutes)

```bash
# Start a simple GraphQL server (for testing)
# Note: In production, integrate with your GraphQL server
psql specql_demo << 'EOF'
-- Test creating a contact
SELECT crm.create_contact(
  'john.doe@example.com',
  'John',
  'Doe',
  '+14155551234'
);

-- Test querying
SELECT * FROM crm.contact WHERE email = 'john.doe@example.com';
EOF
```

**Expected output:**
```
create_contact
----------------
(1,contact_1)  -- Returns (pk_contact, identifier)

pk_contact | id                                   | identifier | email               | first_name | last_name | phone
-----------+--------------------------------------+-----------+---------------------+------------+-----------+-----------
1          | 550e8400-e29b-41d4-a716-446655440000 | contact_1 | john.doe@example.com| John       | Doe       | +14155551234
```

## Step 6: Add a Custom Action (5 minutes)

Let's add business logic for qualifying leads:

```yaml
# Add to your contact.yaml
actions:
  - name: create_contact
  - name: update_contact
  - name: qualify_lead
    description: "Convert a lead to a qualified contact"
    steps:
      - validate: status = 'lead'  # Check current status
      - update: Contact SET status = 'qualified', qualified_at = now()
      - return: "Lead qualified successfully"
```

```bash
# Regenerate with the new action
specql generate contact.yaml

# Test the custom action
psql specql_demo << 'EOF'
-- First create a lead
SELECT crm.create_contact(
  'jane.smith@example.com',
  'Jane',
  'Smith',
  '+14155559876'
);

-- Then qualify the lead
SELECT crm.qualify_lead(1);  -- Use the pk_contact from above
EOF
```

## Congratulations! 🎉

You now have a production-ready backend with:

- ✅ **PostgreSQL schema** with proper constraints and indexes
- ✅ **Business logic** with validation and error handling
- ✅ **GraphQL mutations** ready for frontend integration
- ✅ **TypeScript types** for type-safe development
- ✅ **Audit trails** and data integrity built-in

## Next Steps

### Add More Entities
- [Create an Organization entity](first-entity.md)
- [Link entities with relationships](../05_guides/relationships.md)

### Go Production
- [Deploy to production](production-deploy.md)
- [Add multi-tenancy](../05_guides/multi-tenancy.md)
- [Set up authentication](../07_advanced/security-hardening.md)

### Explore Advanced Features
- [Use stdlib entities](../04_stdlib/index.md)
- [Reverse engineer existing code](../02_migration/index.md)
- [Advanced topics](../07_advanced/index.md)

## Need Help?

- **Stuck?** Check the [troubleshooting guide](../05_guides/troubleshooting.md)
- **Questions?** Open an [issue](https://github.com/fraiseql/specql/issues)
- **Community** Join our [Discord/Slack]

---

**Time spent: 30 minutes. Code written: 20 lines. Backend created: Production-ready.** 🚀</content>
</xai:function_call
