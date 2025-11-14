# Implementation Plan: Documentation Improvements (Issue #3)

**Issue**: https://github.com/fraiseql/specql/issues/3
**Priority**: Medium (User Experience Enhancement)
**Estimated Effort**: 19-24 hours (2-3 days)
**Complexity**: Simple - Multiple independent documentation files
**Status**: Ready for Implementation

---

## 🎯 Executive Summary

Create comprehensive user-facing documentation to improve SpecQL's adoption and usability. Currently, SpecQL has excellent technical/implementation docs but lacks practical user guides, complete reference documentation, and migration resources.

**Goal**: Enable new users to get started in <15 minutes and successfully migrate existing databases.

---

## 📋 Deliverables Overview

| File | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| 1. `docs/reference/yaml-reference.md` | HIGH | 4h | None |
| 2. `docs/guides/migration-guide.md` | HIGH | 6h | #1 |
| 3. `docs/reference/cli-reference.md` | MEDIUM | 3h | None |
| 4. `docs/guides/troubleshooting.md` | MEDIUM | 4h | #1, #3 |
| 5. `docs/QUICK_REFERENCE.md` | LOW | 2h | #1 |
| 6. Reorganize docs structure | LOW | 3h | All above |

**Total**: ~22 hours across 6 tasks

**Approach**: Direct execution (no TDD needed for documentation)

---

## 📝 Task 1: Complete YAML Reference

**File**: `docs/reference/yaml-reference.md`
**Priority**: HIGH
**Effort**: 4 hours
**Dependencies**: None

### Objective
Create a comprehensive, searchable reference for all SpecQL YAML syntax options.

### Content Structure

```markdown
# SpecQL YAML Complete Reference

## Table of Contents
1. Entity Structure Overview
2. Top-Level Fields
3. Fields Section
4. Actions Section
5. Organization Metadata
6. Advanced Features

## 1. Entity Structure Overview
[Minimal example with all sections]

## 2. Top-Level Fields

### Required Fields
- `entity` (string, PascalCase)
  - Description: Entity name
  - Example: `entity: Contact`
  - Rules: Must be PascalCase, must be unique in schema

- `schema` (string, snake_case)
  - Description: PostgreSQL schema name
  - Example: `schema: crm`
  - Rules: Must be registered in domain registry

- `fields` (object)
  - Description: Field definitions
  - See Fields Section below

### Optional Fields
- `description` (string)
  - Purpose: Entity documentation
  - Example: `description: "Customer contact information"`
  - Impact: Added as PostgreSQL comment

- `organization` (object)
  - Purpose: Advanced metadata for migrations
  - See Organization Metadata section
  - When to use: Migrating from existing systems with numbering

- `actions` (array)
  - Purpose: Business logic definitions
  - See Actions Section

- `translations` (array)
  - Purpose: i18n support
  - Status: Implemented
  - Reference: docs/guides/i18n-guide.md (if exists)

- `hierarchical` (boolean)
  - Purpose: Enable hierarchical identifiers
  - Default: false
  - Reference: docs/guides/hierarchical-entities.md

## 3. Fields Section

### Scalar Types

#### text
- SQL Type: TEXT
- Use for: Free-form text, names, descriptions
- Example: `name: text`
- Auto-generated features: None
- Validation: None (use rich types for validated text)

#### integer
- SQL Type: INTEGER
- Use for: Whole numbers, counts, quantities
- Example: `quantity: integer`
- Auto-generated features: None
- Validation: Must be whole number

#### decimal
- SQL Type: NUMERIC
- Use for: Monetary values, precise calculations
- Example: `price: decimal`
- Auto-generated features: None
- Validation: Precision depends on PostgreSQL defaults

#### boolean
- SQL Type: BOOLEAN
- Use for: True/false flags
- Example: `is_active: boolean`
- Auto-generated features: None
- Validation: Must be true/false

#### timestamp
- SQL Type: TIMESTAMP WITH TIME ZONE
- Use for: Precise date-time values
- Example: `delivered_at: timestamp`
- Auto-generated features: None (except created_at/updated_at)
- Validation: ISO 8601 format

#### date
- SQL Type: DATE
- Use for: Dates without time component
- Example: `birthday: date`
- Auto-generated features: None
- Validation: YYYY-MM-DD format

#### json
- SQL Type: JSONB
- Use for: Semi-structured data, flexible schemas
- Example: `metadata: json`
- Auto-generated features: GIN index
- Validation: Must be valid JSON

### Rich Types (Composite Types)

#### email
- SQL Type: app.email (composite)
- Use for: Email addresses
- Example: `contact_email: email`
- Structure: `{address: TEXT, display_name: TEXT}`
- Validation: Basic email format

#### phone
- SQL Type: app.phone (composite)
- Use for: Phone numbers
- Example: `mobile: phone`
- Structure: `{country_code: TEXT, number: TEXT, extension: TEXT}`
- Validation: None (international format varies)

#### money
- SQL Type: app.money (composite)
- Use for: Monetary values with currency
- Example: `total_amount: money`
- Structure: `{amount: NUMERIC, currency: TEXT}`
- Validation: ISO 4217 currency codes

#### dimensions
- SQL Type: app.dimensions (composite)
- Use for: Physical measurements
- Example: `package_size: dimensions`
- Structure: `{length: NUMERIC, width: NUMERIC, height: NUMERIC, unit: TEXT}`
- Validation: None

#### contact_info
- SQL Type: app.contact_info (composite)
- Use for: Complete contact details
- Example: `primary_contact: contact_info`
- Structure: `{email: email, phone: phone, address: address}`
- Validation: Validates nested types

### Relational Types

#### ref(Entity)
- SQL Type: INTEGER (FK to tb_entity.id)
- Use for: Foreign key relationships
- Example: `company: ref(Company)`
- Auto-generated features:
  - Foreign key constraint: `fk_tb_contact_company`
  - Index: `idx_tb_contact_company`
  - ON DELETE RESTRICT by default
- Validation: Referenced entity must exist

#### enum(value1, value2, ...)
- SQL Type: TEXT with CHECK constraint
- Use for: Fixed set of values
- Example: `status: enum(lead, qualified, customer)`
- Auto-generated features:
  - CHECK constraint
  - Index: `idx_tb_contact_status`
- Validation: Must be one of listed values

#### list(Type)
- SQL Type: Type[] (PostgreSQL array)
- Use for: Multiple values of same type
- Example: `tags: list(text)`
- Auto-generated features: GIN index
- Validation: All elements must be valid Type

### Field Modifiers

#### nullable
- Syntax: `field: text?` or `field: "text | null"`
- Effect: Field can be NULL
- Default: All fields are NOT NULL
- Example: `middle_name: text?`

#### required (default)
- Syntax: `field: text` (no modifier)
- Effect: Field must have value
- Example: `email: text`

## 4. Actions Section

### Action Structure
```yaml
actions:
  - name: action_name
    description: "What this action does"
    impacts:
      entities: [Entity1, Entity2]
      read: [Entity3]
      write: [Entity1]
    steps:
      - [step definitions]
```

### Step Types

#### validate
- Purpose: Check preconditions
- Syntax: `validate: <expression>`
- Example: `validate: status = 'draft'`
- On failure: Returns error, halts execution
- Expression syntax: SQL WHERE clause

#### if
- Purpose: Conditional branching
- Syntax:
  ```yaml
  - if: <condition>
    then:
      - [steps]
    else:
      - [steps]
  ```
- Example:
  ```yaml
  - if: amount > 1000
    then:
      - update: Order SET requires_approval = true
    else:
      - update: Order SET approved = true
  ```

#### insert
- Purpose: Create new record
- Syntax: `insert: Entity [SET field = value, ...]`
- Example: `insert: AuditLog SET action = 'created'`
- Returns: Complete inserted object
- Auto-generated: id, created_at, created_by

#### update
- Purpose: Modify existing record
- Syntax: `update: Entity SET field = value [WHERE condition]`
- Example: `update: Contact SET status = 'qualified' WHERE id = :contact_id`
- Returns: Updated object
- Auto-generated: updated_at, updated_by

#### soft_delete
- Purpose: Mark record as deleted
- Syntax: `soft_delete: Entity [WHERE condition]`
- Example: `soft_delete: Contact WHERE id = :id`
- Effect: Sets deleted_at = NOW(), deleted_by = current_user
- Returns: Deleted object

#### call
- Purpose: Invoke another action
- Syntax: `call: schema.action_name(param1: value1, ...)`
- Example: `call: crm.send_welcome_email(contact_id: :id)`
- Returns: Result from called action

#### notify
- Purpose: Send notification/event
- Syntax: `notify: channel WITH payload`
- Example: `notify: contact_created WITH {contact_id: :id}`
- Effect: PostgreSQL NOTIFY

#### foreach
- Purpose: Loop over collection
- Syntax:
  ```yaml
  - foreach: item IN <collection>
    do:
      - [steps with :item available]
  ```
- Example:
  ```yaml
  - foreach: line IN order_lines
    do:
      - update: Product SET stock = stock - :line.quantity WHERE id = :line.product_id
  ```

### Expression Syntax

#### Variables
- `:param_name` - Input parameter
- `:item.field` - Foreach item field
- `CURRENT_TIMESTAMP` - Current time
- `CURRENT_USER` - Current user UUID

#### Operators
- Comparison: `=`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `AND`, `OR`, `NOT`
- Null: `IS NULL`, `IS NOT NULL`
- Pattern: `LIKE`, `ILIKE`
- Membership: `IN (value1, value2)`

#### Functions
- String: `LOWER()`, `UPPER()`, `TRIM()`
- Date: `NOW()`, `CURRENT_DATE`
- Math: `ABS()`, `ROUND()`
- Aggregation: Use subqueries

## 5. Organization Metadata

### Purpose
Advanced metadata for migrations and hierarchical output structure.

### When to Use
- ✅ Migrating from existing system with file numbering (e.g., `012311_tb_contact.sql`)
- ✅ Generating hierarchical directory structure with `--output-format hierarchical`
- ✅ Maintaining traceability to legacy database code
- ❌ New projects (not needed)
- ❌ Simple prototypes

### Fields

#### table_code
- Type: string (6-character hex)
- Format: `[0-9A-F]{6}`
- Example: `table_code: "012311"`
- Purpose: Unique identifier for migration files
- Validation: Must be unique across all entities
- Check with: `specql check-codes entities/**/*.yaml`

#### domain
- Type: string
- Example: `domain: "CRM"`
- Purpose: High-level business domain classification
- Use: Documentation and organization

#### subdomain
- Type: string
- Example: `subdomain: "Customer Management"`
- Purpose: Functional area within domain
- Use: Documentation and hierarchical structure

### Example
```yaml
entity: Contact
schema: crm
organization:
  table_code: "012311"
  domain: "CRM"
  subdomain: "Customer"
fields:
  email: text
```

### Output Impact
With `--output-format hierarchical`:
```
db/schema/10_tables/
└── CRM/
    └── Customer/
        └── 012311_contact.sql
```

Without (default flat):
```
db/schema/10_tables/
└── contact.sql
```

## 6. Advanced Features

### Hierarchical Entities
See: `docs/guides/hierarchical-entities.md`

Enables tree structures with parent-child relationships.

```yaml
entity: Category
schema: catalog
hierarchical: true
fields:
  name: text
  parent: ref(Category)?
```

Generates:
- `identifier` as hierarchical path (e.g., `electronics/computers/laptops`)
- Helper functions for tree operations
- Recursive queries

### Multi-Tenancy
See: `docs/guides/multi-tenancy.md`

Automatic `tenant_id` for multi-tenant schemas.

**Configuration**: `registry/domain_registry.yaml`
```yaml
domains:
  crm:
    type: multi_tenant  # Adds tenant_id to all tables
  catalog:
    type: shared        # No tenant_id
```

**Effect**:
```sql
CREATE TABLE crm.tb_contact (
  id INTEGER PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES common.tb_tenant(id),
  -- ... other fields
);
```

### Stdlib Imports
See: `stdlib/` directory

Reusable entity templates.

```yaml
# entities/contact.yaml
import: stdlib/crm/contact
schema: crm  # Override schema
fields:
  # Additional fields beyond stdlib
  custom_field: text
```

## 7. Auto-Generated Features

### Trinity Pattern
Every entity automatically gets:
- `id` - INTEGER primary key (main identifier)
- `pk_<entity>` - UUID unique identifier (stable external reference)
- `identifier` - TEXT unique identifier (human-readable slug)

**Don't include these in YAML** - they're always generated.

### Audit Fields
Automatically added to all entities:
- `created_at` - TIMESTAMP WITH TIME ZONE
- `created_by` - UUID (references user)
- `updated_at` - TIMESTAMP WITH TIME ZONE
- `updated_by` - UUID
- `deleted_at` - TIMESTAMP WITH TIME ZONE (NULL unless soft-deleted)
- `deleted_by` - UUID

### Indexes
Automatically created for:
- Foreign key columns: `idx_tb_<entity>_<field>`
- Enum fields: `idx_tb_<entity>_<field>`
- `tenant_id`: `idx_tb_<entity>_tenant_id`
- JSONB fields: GIN index

### Helper Functions
Generated in `db/schema/20_helpers/`:
- `<schema>.<entity>_pk(uuid)` - Get INTEGER id from UUID
- `<schema>.<entity>_id(integer)` - Get UUID from INTEGER id
- `<schema>.<entity>_identifier(text)` - Get INTEGER id from identifier

### Naming Conventions
**Tables**: `tb_<entity>` (lowercase, snake_case)
**Views**: `tv_<entity>` (table views)
**Foreign Keys**: `fk_tb_<entity>_<field>`
**Indexes**: `idx_tb_<entity>_<field>`
**Functions**: `<schema>.<action_name>`
**Wrappers**: `app.<action_name>` (GraphQL entry point)

---

## 📖 Examples Section

### Complete Minimal Example
```yaml
entity: Contact
schema: crm
fields:
  email: text
  name: text
```

### Complete Rich Example
```yaml
entity: Order
schema: commerce
description: "Customer purchase orders"
organization:
  table_code: "042001"
  domain: "Commerce"
  subdomain: "Orders"
fields:
  order_number: text
  customer: ref(Customer)
  status: enum(draft, confirmed, shipped, delivered, cancelled)
  total_amount: money
  shipping_address: json
  notes: text?
  delivered_at: timestamp?
actions:
  - name: confirm_order
    description: "Confirm a draft order"
    impacts:
      write: [Order]
      read: [Customer, Product]
    steps:
      - validate: status = 'draft'
      - validate: total_amount.amount > 0
      - update: Order SET status = 'confirmed', confirmed_at = NOW()
      - notify: order_confirmed WITH {order_id: :id}

  - name: ship_order
    description: "Mark order as shipped"
    impacts:
      write: [Order, OrderLine, Product]
    steps:
      - validate: status = 'confirmed'
      - foreach: line IN (SELECT * FROM commerce.tb_order_line WHERE order_id = :id)
        do:
          - update: Product SET stock = stock - :line.quantity WHERE id = :line.product_id
      - update: Order SET status = 'shipped', shipped_at = NOW()
      - call: notifications.send_tracking_email(order_id: :id)
```

---

## 🔍 Reference

### Related Documentation
- **Guides**: `docs/guides/` - How-to tutorials
- **Architecture**: `docs/architecture/` - Technical design
- **CLI Reference**: `docs/reference/cli-reference.md`
- **Troubleshooting**: `docs/guides/troubleshooting.md`

### External References
- PostgreSQL Data Types: https://www.postgresql.org/docs/current/datatype.html
- SQL Syntax: https://www.postgresql.org/docs/current/sql.html
- GraphQL: https://graphql.org/

---

## ✅ Validation Checklist

Before finalizing this reference:
- [ ] All field types documented with examples
- [ ] All action step types explained
- [ ] Organization section clearly marked as optional/advanced
- [ ] Auto-generated features explicitly listed
- [ ] Common gotchas addressed (e.g., text vs string)
- [ ] Examples are copy-paste ready
- [ ] Links to related docs work
- [ ] Table of contents is accurate
```

### Implementation Steps

1. **Create file structure**:
   ```bash
   mkdir -p docs/reference
   touch docs/reference/yaml-reference.md
   ```

2. **Write content sections in order**:
   - Start with Table of Contents
   - Write Entity Structure Overview
   - Document each field type (reference existing code in `src/core/models/field.py`)
   - Document each action step (reference `src/generators/actions/step_compilers/`)
   - Add examples from tests (`tests/unit/core/test_entity_parser.py`)

3. **Validate examples**:
   ```bash
   # Extract YAML examples to temp files
   # Run: specql validate <temp-file>
   # Ensure all examples parse correctly
   ```

4. **Cross-reference existing docs**:
   - Link to `docs/guides/actions-guide.md`
   - Link to `docs/guides/multi-tenancy.md`
   - Link to `docs/reference/scalar-types.md`

### Quality Criteria
- [ ] Every YAML key is documented
- [ ] Every field type has an example
- [ ] Every action step type has an example
- [ ] All examples validate successfully
- [ ] Clear distinction between required/optional
- [ ] Clear marking of auto-generated features

---

## 📝 Task 2: Migration Guide

**File**: `docs/guides/migration-guide.md`
**Priority**: HIGH
**Effort**: 6 hours
**Dependencies**: Task 1 (YAML Reference)

### Objective
Enable teams to migrate existing PostgreSQL databases to SpecQL with clear, step-by-step instructions.

### Content Structure

```markdown
# Migrating Existing Databases to SpecQL

## Overview
This guide helps you convert existing PostgreSQL schemas to SpecQL YAML definitions.

**Time Estimate**: 1-2 hours per 10 tables
**Difficulty**: Intermediate
**Prerequisites**:
- Existing PostgreSQL database
- Understanding of your schema structure
- SpecQL installed (`uv add specql-generator`)

---

## 🎯 Migration Strategy

### 1. Inventory Phase (30 minutes)
Understand what you have.

### 2. Mapping Phase (1-2 hours per 10 tables)
Convert SQL → YAML.

### 3. Validation Phase (1 hour)
Verify generated SQL matches intent.

### 4. Testing Phase (1-2 hours)
Test in development environment.

---

## Step 1: Export Current Schema

### Export DDL
```bash
# Full schema dump
pg_dump --schema-only mydb > schema_export.sql

# Specific schema only
pg_dump --schema-only --schema=crm mydb > crm_schema.sql

# Exclude framework schemas
pg_dump --schema-only \
  --exclude-schema=information_schema \
  --exclude-schema=pg_catalog \
  mydb > app_schema.sql
```

### Analyze Schema
```bash
# List all tables
psql mydb -c "\dt crm.*"

# Show table structure
psql mydb -c "\d crm.contacts"

# Show foreign keys
psql mydb -c "
  SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
  FROM information_schema.table_constraints AS tc
  JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
  JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
  WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'crm';
"
```

---

## Step 2: Map Tables to Entities

### Mapping Rules

#### Table Names
**SQL**: `crm.contacts`, `crm.tb_contact`, `contact`
**SpecQL**:
```yaml
entity: Contact  # Singular, PascalCase
schema: crm      # Schema name
```

**Rule**: Drop `tb_` prefix, singularize, PascalCase

#### Column Types
| SQL Type | SpecQL Type | Notes |
|----------|-------------|-------|
| `TEXT`, `VARCHAR` | `text` | |
| `INTEGER`, `INT` | `integer` | |
| `NUMERIC`, `DECIMAL` | `decimal` | |
| `BOOLEAN` | `boolean` | |
| `TIMESTAMP` | `timestamp` | |
| `DATE` | `date` | |
| `JSONB`, `JSON` | `json` | |
| `TEXT[]` | `list(text)` | Arrays |
| `INTEGER REFERENCES` | `ref(Entity)` | Foreign keys |
| `TEXT CHECK (...)` | `enum(...)` | Extract values |

#### Foreign Keys
**SQL**:
```sql
company_id INTEGER REFERENCES companies(id)
```

**SpecQL**:
```yaml
company: ref(Company)
```

**Rule**:
1. Drop `_id` suffix from column name
2. Reference entity name in PascalCase
3. SpecQL generates FK constraint automatically

#### Enums (CHECK Constraints)
**SQL**:
```sql
status TEXT CHECK (status IN ('lead', 'qualified', 'customer'))
```

**SpecQL**:
```yaml
status: enum(lead, qualified, customer)
```

**Rule**: Extract values from CHECK constraint

#### Nullable Columns
**SQL**:
```sql
middle_name TEXT NULL
```

**SpecQL**:
```yaml
middle_name: text?
```

**Rule**: Add `?` suffix for nullable fields

---

## Step 3: Handle Auto-Generated Fields

### Fields to EXCLUDE from YAML

SpecQL auto-generates these - **do not include**:

#### Trinity Pattern
```sql
-- DON'T INCLUDE:
id INTEGER PRIMARY KEY
uuid UUID UNIQUE
slug TEXT UNIQUE
```
**Reason**: Trinity pattern is always generated

#### Audit Fields
```sql
-- DON'T INCLUDE:
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP
deleted_at TIMESTAMP
created_by UUID
updated_by UUID
deleted_by UUID
```
**Reason**: Audit fields are always generated

#### Multi-Tenant Fields
```sql
-- DON'T INCLUDE (if schema is multi-tenant):
tenant_id UUID REFERENCES tenants(id)
```
**Reason**: Generated based on domain registry

#### Indexes
```sql
-- DON'T INCLUDE:
CREATE INDEX idx_contacts_company_id ON contacts(company_id);
CREATE INDEX idx_contacts_status ON contacts(status);
```
**Reason**: Indexes auto-generated for FKs and enums

### Fields to INCLUDE

Only include **business domain fields**:
```yaml
entity: Contact
schema: crm
fields:
  # ✅ Include: Business fields
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)
  notes: text?

  # ❌ Don't include: Auto-generated
  # id, uuid, slug, created_at, updated_at, tenant_id
```

---

## Step 4: Convert Business Logic

### Triggers → Actions

**SQL Trigger**:
```sql
CREATE FUNCTION qualify_lead() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'qualified' AND OLD.status = 'lead' THEN
    UPDATE contacts
    SET qualified_at = NOW()
    WHERE id = NEW.id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER qualify_lead_trigger
  AFTER UPDATE ON contacts
  FOR EACH ROW
  EXECUTE FUNCTION qualify_lead();
```

**SpecQL Action**:
```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified', qualified_at = NOW()
```

**Benefits**:
- No trigger syntax
- Declarative steps
- Automatic GraphQL integration
- Built-in error handling

### Stored Procedures → Actions

**SQL Procedure**:
```sql
CREATE FUNCTION archive_contact(contact_id INTEGER)
RETURNS VOID AS $$
BEGIN
  UPDATE contacts
  SET deleted_at = NOW(), deleted_by = current_user
  WHERE id = contact_id;

  INSERT INTO audit_log (entity_type, entity_id, action)
  VALUES ('contact', contact_id, 'archived');
END;
$$ LANGUAGE plpgsql;
```

**SpecQL Action**:
```yaml
actions:
  - name: archive_contact
    steps:
      - soft_delete: Contact
      - insert: AuditLog SET entity_type = 'contact', action = 'archived'
```

---

## Step 5: Preserve Existing Table Codes

If you have numbered migration files (e.g., `001_contacts.sql`, `002_companies.sql`):

### Extract Table Codes
```bash
# List migration files
ls db/migrations/

# Output:
# 001_contacts.sql
# 002_companies.sql
# 003_orders.sql
```

### Add to YAML
```yaml
entity: Contact
schema: crm
organization:
  table_code: "000001"  # Pad to 6 hex digits
fields:
  # ... fields
```

### Validate Uniqueness
```bash
specql check-codes entities/**/*.yaml
```

**Output**:
```
✅ All table codes are unique
📊 3 entities with table codes
```

---

## Step 6: Create Domain Registry

Configure schema types (multi-tenant vs shared):

**File**: `registry/domain_registry.yaml`

```yaml
domains:
  # Multi-tenant schemas (add tenant_id)
  crm:
    type: multi_tenant
    description: "Customer relationship management"

  projects:
    type: multi_tenant
    description: "Project management"

  # Shared schemas (no tenant_id)
  catalog:
    type: shared
    description: "Product catalog"

  analytics:
    type: shared
    description: "Cross-tenant analytics"
```

---

## Step 7: Generate and Compare

### Generate SpecQL Schema
```bash
# Generate all entities
specql generate entities/**/*.yaml

# Output directory:
# db/schema/10_tables/
# db/schema/20_helpers/
# db/schema/30_functions/
```

### Compare with Original
```bash
# Compare table structure
diff -u schema_export.sql db/schema/10_tables/contact.sql

# Focus on business logic (ignore auto-generated differences)
```

### Expected Differences

✅ **Safe to ignore**:
- Trinity pattern columns (`id`, `pk_*`, `identifier`)
- Audit fields (`created_at`, `updated_at`, etc.)
- Auto-generated indexes
- Naming conventions (`tb_` prefix vs original name)

⚠️ **Review carefully**:
- Missing business columns
- Different field types
- Missing foreign keys
- Different constraints

---

## Step 8: Test in Development

### Apply Generated Schema
```bash
# Create test database
createdb specql_migration_test

# Apply foundation
psql specql_migration_test -f db/schema/00_foundation/000_app_foundation.sql

# Apply tables
psql specql_migration_test -f db/schema/10_tables/*.sql

# Apply helpers
psql specql_migration_test -f db/schema/20_helpers/*.sql

# Apply actions
psql specql_migration_test -f db/schema/30_functions/*.sql
```

### Migrate Data
```bash
# Export data from original
pg_dump --data-only --schema=crm mydb > data_export.sql

# Map column names if needed
sed 's/company_id/company/g' data_export.sql > data_mapped.sql

# Import to test database
psql specql_migration_test -f data_mapped.sql
```

### Validate Data
```sql
-- Check row counts
SELECT 'contacts' as table, count(*) FROM crm.tb_contact
UNION ALL
SELECT 'companies', count(*) FROM crm.tb_company;

-- Validate foreign keys
SELECT count(*) FROM crm.tb_contact WHERE company IS NULL;

-- Check constraints
SELECT status, count(*) FROM crm.tb_contact GROUP BY status;
```

---

## Common Migration Patterns

### Pattern 1: Serial IDs → Trinity
**Before**:
```sql
CREATE TABLE contacts (
  id SERIAL PRIMARY KEY,
  -- ...
);
```

**After** (auto-generated):
```sql
CREATE TABLE crm.tb_contact (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  pk_contact UUID DEFAULT gen_random_uuid() UNIQUE,
  identifier TEXT UNIQUE,
  -- ...
);
```

**Migration**:
- Keep original `id` values
- Generate `pk_*` UUID for new external references
- Generate `identifier` from business key (e.g., email, name)

### Pattern 2: Manual Audit → Automatic
**Before**:
```sql
CREATE TABLE contacts (
  -- ...
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);

CREATE TRIGGER update_timestamp
  BEFORE UPDATE ON contacts
  FOR EACH ROW
  EXECUTE FUNCTION update_modified_column();
```

**After** (auto-generated):
```sql
-- Fields added automatically
-- Triggers added automatically
-- updated_by tracking added automatically
```

**Migration**:
- Remove manual triggers
- SpecQL handles updates automatically

### Pattern 3: CHECK Constraints → Enums
**Before**:
```sql
CREATE TABLE contacts (
  status TEXT CHECK (status IN ('lead', 'qualified', 'customer')),
  priority TEXT CHECK (priority IN ('low', 'medium', 'high'))
);
```

**After**:
```yaml
fields:
  status: enum(lead, qualified, customer)
  priority: enum(low, medium, high)
```

**Migration**:
- Extract enum values from CHECK constraints
- Validate data matches enum values
- SpecQL generates CHECK constraint automatically

### Pattern 4: Composite Types
**Before**:
```sql
CREATE TABLE contacts (
  email_address TEXT,
  email_display_name TEXT,
  phone_country TEXT,
  phone_number TEXT,
  phone_extension TEXT
);
```

**After**:
```yaml
fields:
  email: email  # Composite: {address, display_name}
  phone: phone  # Composite: {country_code, number, extension}
```

**Migration**:
```sql
-- Map existing columns to composite type
UPDATE crm.tb_contact SET
  email = ROW(email_address, email_display_name)::app.email,
  phone = ROW(phone_country, phone_number, phone_extension)::app.phone;
```

---

## Troubleshooting

### Issue: "Table code already assigned"
**Symptom**:
```
ValueError: Table code 012311 already assigned to Contact
```

**Solution**:
```bash
specql check-codes entities/**/*.yaml
```

Each entity must have unique `table_code`.

### Issue: "Unknown field type"
**Symptom**:
```
Parse Error: Unknown field type 'varchar'
```

**Solution**: Use SpecQL type names
- ❌ `varchar` → ✅ `text`
- ❌ `int` → ✅ `integer`
- ❌ `bool` → ✅ `boolean`

See: `docs/reference/yaml-reference.md#scalar-types`

### Issue: Foreign key references wrong column
**Symptom**:
```sql
-- Generated:
FOREIGN KEY (company) REFERENCES crm.tb_company(id)
-- But original was:
FOREIGN KEY (company_id) REFERENCES companies(company_uuid)
```

**Solution**: SpecQL always references `id` (INTEGER PK)
- If original uses UUID: Map to new `pk_*` column
- If original uses different PK: Requires manual migration

### Issue: Missing custom indexes
**Symptom**: Original has `CREATE INDEX idx_contacts_email` but SpecQL doesn't generate it.

**Solution**:
- SpecQL auto-indexes FKs and enums
- For custom indexes, add manually to `db/schema/10_tables/contact.sql` after generation
- Or request feature: Rich type with auto-index (e.g., `email: email` could auto-index)

---

## Migration Checklist

### Pre-Migration
- [ ] Export current schema (`pg_dump --schema-only`)
- [ ] Document custom business logic (triggers, procedures)
- [ ] Identify table numbering scheme (if any)
- [ ] List all schemas (multi-tenant vs shared)
- [ ] Back up production data

### Mapping Phase
- [ ] Create `entities/` directory structure
- [ ] Create domain registry (`registry/domain_registry.yaml`)
- [ ] Map each table → YAML entity
- [ ] Extract CHECK constraints → enums
- [ ] Convert foreign keys → ref()
- [ ] Add table codes if preserving numbering
- [ ] Validate all YAML files (`specql validate`)

### Generation Phase
- [ ] Generate schema (`specql generate entities/**/*.yaml`)
- [ ] Review generated SQL
- [ ] Compare with original schema
- [ ] Verify naming conventions applied
- [ ] Check auto-generated indexes

### Testing Phase
- [ ] Create test database
- [ ] Apply generated schema
- [ ] Migrate sample data
- [ ] Validate data integrity
- [ ] Test actions/business logic
- [ ] Performance test with real data volume

### Production Cutover
- [ ] Schedule maintenance window
- [ ] Final data export from old schema
- [ ] Apply new schema to production
- [ ] Migrate data with mapping scripts
- [ ] Validate foreign key constraints
- [ ] Smoke test critical workflows
- [ ] Monitor for errors

---

## Example: Complete Migration

### Original Schema
```sql
-- Original: 42 lines SQL
CREATE TABLE crm.contacts (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  first_name TEXT,
  last_name TEXT,
  company_id INTEGER REFERENCES companies(id),
  status TEXT CHECK (status IN ('lead', 'qualified', 'customer')),
  priority TEXT CHECK (priority IN ('low', 'medium', 'high')),
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP,
  UNIQUE(email)
);

CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_contacts_status ON contacts(status);

CREATE FUNCTION qualify_lead(contact_id INTEGER) RETURNS VOID AS $$
BEGIN
  UPDATE contacts
  SET status = 'qualified', updated_at = NOW()
  WHERE id = contact_id AND status = 'lead';
END;
$$ LANGUAGE plpgsql;
```

### SpecQL YAML
```yaml
# Migrated: 15 lines YAML (3x less code)
entity: Contact
schema: crm
organization:
  table_code: "012311"
fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)
  priority: enum(low, medium, high)
  notes: text?
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

### Generated Schema
```sql
-- Generated: 87 lines SQL (includes Trinity, audit, helpers, GraphQL)
CREATE TABLE crm.tb_contact (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  pk_contact UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
  identifier TEXT UNIQUE NOT NULL,
  tenant_id UUID NOT NULL REFERENCES common.tb_tenant(pk_tenant),
  email TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  company INTEGER NOT NULL REFERENCES crm.tb_company(id),
  status TEXT NOT NULL CHECK (status IN ('lead', 'qualified', 'customer')),
  priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  created_by UUID NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_by UUID NOT NULL,
  deleted_at TIMESTAMP WITH TIME ZONE,
  deleted_by UUID
);

CREATE UNIQUE INDEX idx_tb_contact_email ON crm.tb_contact(email);
CREATE INDEX idx_tb_contact_company ON crm.tb_contact(company);
CREATE INDEX idx_tb_contact_status ON crm.tb_contact(status);
CREATE INDEX idx_tb_contact_tenant_id ON crm.tb_contact(tenant_id);

-- Helper functions
CREATE FUNCTION crm.contact_pk(uuid_val UUID) RETURNS INTEGER ...
CREATE FUNCTION crm.contact_id(id_val INTEGER) RETURNS UUID ...

-- Business action
CREATE FUNCTION crm.qualify_lead(...) RETURNS app.mutation_result ...

-- GraphQL wrapper
CREATE FUNCTION app.qualify_lead(...) RETURNS app.mutation_result ...
```

**Result**:
- 15 lines YAML → 87 lines production SQL
- **6x code leverage**
- Trinity pattern included
- GraphQL ready
- Audit trail built-in

---

## Next Steps

After successful migration:
1. **Update CI/CD**: Use `specql generate` in build pipeline
2. **Train team**: Share YAML reference and guides
3. **Deprecate old migrations**: Archive SQL files, use YAML as source of truth
4. **Add actions**: Migrate remaining business logic to SpecQL actions
5. **Enable GraphQL**: Configure FraiseQL for frontend integration

---

## Resources

- **YAML Reference**: `docs/reference/yaml-reference.md`
- **CLI Reference**: `docs/reference/cli-reference.md`
- **Troubleshooting**: `docs/guides/troubleshooting.md`
- **Examples**: `examples/entities/`
- **Stdlib**: `stdlib/` (reusable templates)

---

## Support

**Questions?**
- Search issues: https://github.com/fraiseql/specql/issues
- Create issue with:
  - Original SQL schema
  - Generated YAML
  - Generated SQL
  - Specific differences/questions
```

### Implementation Steps

1. **Create file**:
   ```bash
   touch docs/guides/migration-guide.md
   ```

2. **Write content** following structure above

3. **Create example migration**:
   ```bash
   mkdir -p examples/migration
   # Add before.sql, after.yaml, comparison.md
   ```

4. **Test migration steps**:
   - Create test database
   - Follow guide step-by-step
   - Document any issues
   - Refine guide based on experience

5. **Cross-reference**:
   - Link to YAML reference
   - Link to CLI reference
   - Link to troubleshooting

### Quality Criteria
- [ ] Step-by-step instructions are clear
- [ ] Common patterns documented
- [ ] Complete example provided
- [ ] Troubleshooting section comprehensive
- [ ] Checklist is actionable
- [ ] All steps tested in practice

---

## 📝 Task 3: CLI Reference

**File**: `docs/reference/cli-reference.md`
**Priority**: MEDIUM
**Effort**: 3 hours
**Dependencies**: None

### Objective
Document all CLI commands, options, and usage patterns.

### Content Structure

```markdown
# SpecQL CLI Reference

## Installation

### Via UV (Recommended)
```bash
uv add specql-generator
```

### Via Git (Development)
```bash
git clone https://github.com/fraiseql/specql
cd specql
uv sync
```

### Verify Installation
```bash
specql --version
specql --help
```

---

## Commands Overview

| Command | Purpose | Priority |
|---------|---------|----------|
| `generate` | Generate SQL from YAML | HIGH |
| `validate` | Validate YAML syntax | HIGH |
| `check-codes` | Check table code uniqueness | MEDIUM |
| `diff` | Compare generated vs existing SQL | LOW |
| `docs` | Generate documentation | LOW |

---

## `specql generate`

Generate PostgreSQL schema and functions from SpecQL YAML files.

### Syntax
```bash
specql generate [OPTIONS] ENTITY_FILES...
```

### Arguments
- `ENTITY_FILES...` - One or more YAML entity files or glob patterns

### Options

#### `--foundation-only`
Generate only the app foundation SQL (types, schemas).

**Use case**: Initialize database before adding entities.

**Example**:
```bash
specql generate entities/contact.yaml --foundation-only
```

**Output**: `db/schema/00_foundation/000_app_foundation.sql`

#### `--include-tv`
Generate table views (CQRS read-side).

**Use case**: Enable read-optimized views for queries.

**Example**:
```bash
specql generate entities/**/*.yaml --include-tv
```

**Output**:
- `db/schema/10_tables/` - Tables
- `db/schema/10_tables/views/` - Table views

#### `--env TEXT`
Specify Confiture environment (default: `local`).

**Use case**: Generate for different environments (local, staging, prod).

**Example**:
```bash
specql generate entities/**/*.yaml --env staging
```

**Config**: Uses `confiture.yaml` environment settings.

#### `--with-impacts`
Generate FraiseQL impact metadata (JSON).

**Use case**: Frontend integration, GraphQL client codegen.

**Example**:
```bash
specql generate entities/**/*.yaml --with-impacts
```

**Output**: `db/metadata/mutation_impacts.json`

#### `--output-frontend PATH`
Generate frontend code (TypeScript types, Apollo hooks).

**Use case**: Full-stack codegen from YAML.

**Example**:
```bash
specql generate entities/**/*.yaml \
  --with-impacts \
  --output-frontend=src/generated
```

**Output**:
- `src/generated/types.ts` - TypeScript types
- `src/generated/mutations.ts` - Apollo hooks
- `src/generated/docs/` - Markdown documentation

#### `--output-format [flat|hierarchical]`
Control output directory structure.

**Use case**: Organize generated files by domain/subdomain.

**Options**:
- `flat` (default): All files in single directory
- `hierarchical`: Organize by `organization.domain` / `organization.subdomain`

**Example**:
```bash
specql generate entities/**/*.yaml --output-format hierarchical
```

**Output (flat)**:
```
db/schema/10_tables/
├── contact.sql
├── company.sql
└── order.sql
```

**Output (hierarchical)**:
```
db/schema/10_tables/
├── CRM/
│   ├── Customer/
│   │   └── 012311_contact.sql
│   └── Account/
│       └── 012312_company.sql
└── Commerce/
    └── Orders/
        └── 042001_order.sql
```

### Examples

#### Single Entity
```bash
specql generate entities/contact.yaml
```

#### Multiple Entities
```bash
specql generate entities/contact.yaml entities/company.yaml
```

#### All Entities in Directory
```bash
specql generate entities/**/*.yaml
```

#### Specific Schema
```bash
specql generate entities/crm/*.yaml
```

#### Foundation Only
```bash
specql generate entities/contact.yaml --foundation-only
```

#### With Frontend Codegen
```bash
specql generate entities/**/*.yaml \
  --with-impacts \
  --output-frontend=src/generated
```

### Output Structure

```
db/schema/
├── 00_foundation/
│   └── 000_app_foundation.sql  # Types, schemas
├── 10_tables/
│   ├── contact.sql             # Table DDL
│   └── company.sql
├── 20_helpers/
│   ├── contact_helpers.sql     # Helper functions
│   └── company_helpers.sql
├── 30_functions/
│   ├── qualify_lead.sql        # Business actions
│   └── create_company.sql
└── 40_metadata/
    ├── contact_metadata.sql    # FraiseQL annotations
    └── company_metadata.sql
```

---

## `specql validate`

Validate SpecQL YAML entity files for syntax errors and consistency.

### Syntax
```bash
specql validate [OPTIONS] ENTITY_FILES...
```

### Arguments
- `ENTITY_FILES...` - One or more YAML files or glob patterns

### Options

#### `-v, --verbose`
Show detailed validation output.

**Example**:
```bash
specql validate entities/**/*.yaml --verbose
```

#### `--check-impacts`
Validate impact declarations are complete and consistent.

**Use case**: Ensure mutations declare all side effects.

**Example**:
```bash
specql validate entities/**/*.yaml --check-impacts
```

**Checks**:
- All entities in `write:` exist
- All entities in `read:` exist
- No circular dependencies
- No missing declarations

### Examples

#### Single File
```bash
specql validate entities/contact.yaml
```

#### All Entities
```bash
specql validate entities/**/*.yaml
```

#### With Impact Checking
```bash
specql validate entities/**/*.yaml --check-impacts
```

### Exit Codes
- `0` - All files valid
- `1` - Validation errors found

### Example Output

**Success**:
```
✅ entities/contact.yaml: Valid
✅ entities/company.yaml: Valid
✅ All 2 entities validated successfully
```

**Errors**:
```
❌ entities/contact.yaml: Parse error
  Line 5: Unknown field type 'string' (use 'text')

❌ entities/order.yaml: Validation error
  Action 'ship_order': References undefined entity 'Shipment'

❌ 2 files have errors
```

---

## `specql check-codes`

Verify uniqueness of table codes across all entities.

### Syntax
```bash
specql check-codes [OPTIONS] ENTITY_FILES...
```

### Arguments
- `ENTITY_FILES...` - YAML files or directories

### Options

#### `--format [text|json|csv]`
Output format (default: `text`).

**Example**:
```bash
specql check-codes entities/ --format json
```

#### `--export PATH`
Export results to file.

**Example**:
```bash
specql check-codes entities/ --format csv --export codes.csv
```

### Examples

#### Check All Entities
```bash
specql check-codes entities/**/*.yaml
```

#### Export to JSON
```bash
specql check-codes entities/ --format json --export table_codes.json
```

#### Export to CSV
```bash
specql check-codes entities/ --format csv --export codes.csv
```

### Output

**Text Format**:
```
📊 Table Code Report

✅ All codes are unique

Entities with table codes:
  • 012311 - Contact (entities/crm/contact.yaml)
  • 012312 - Company (entities/crm/company.yaml)
  • 042001 - Order (entities/commerce/order.yaml)

📈 Summary:
  Total entities: 15
  With table codes: 3
  Without table codes: 12
```

**JSON Format**:
```json
{
  "valid": true,
  "codes": [
    {
      "code": "012311",
      "entity": "Contact",
      "file": "entities/crm/contact.yaml"
    }
  ],
  "duplicates": [],
  "summary": {
    "total": 15,
    "with_codes": 3,
    "without_codes": 12
  }
}
```

**Error (Duplicates)**:
```
❌ Duplicate table codes found

⚠️  Code 012311 assigned to multiple entities:
  • Contact (entities/crm/contact.yaml)
  • Customer (entities/crm/customer.yaml)

❌ 1 duplicate code(s) found
```

---

## `specql diff`

Compare generated SQL with existing schema files.

### Syntax
```bash
specql diff [OPTIONS] ENTITY_FILES...
```

### Options

#### `--compare PATH`
Path to existing SQL file(s) to compare against.

**Example**:
```bash
specql diff entities/contact.yaml --compare db/schema/10_tables/contact.sql
```

#### `--ignore-whitespace`
Ignore whitespace differences.

#### `--ignore-comments`
Ignore SQL comment differences.

### Examples

#### Compare Single Entity
```bash
specql diff entities/contact.yaml \
  --compare db/schema/10_tables/contact.sql
```

#### Compare All Entities
```bash
specql diff entities/**/*.yaml \
  --compare db/schema/10_tables/
```

### Output
```diff
Comparing: entities/contact.yaml → db/schema/10_tables/contact.sql

--- Generated
+++ Existing
@@ -12,6 +12,7 @@
   company INTEGER NOT NULL REFERENCES crm.tb_company(id),
   status TEXT NOT NULL CHECK (status IN ('lead', 'qualified', 'customer')),
+  priority TEXT,  -- Added in existing, not in YAML
   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

✅ 1 file compared
⚠️  1 difference found
```

---

## `specql docs`

Generate documentation from entity files.

### Syntax
```bash
specql docs [OPTIONS] ENTITY_FILES...
```

### Options

#### `--output-dir PATH`
Output directory for docs (default: `docs/generated`).

**Example**:
```bash
specql docs entities/**/*.yaml --output-dir docs/entities
```

#### `--format [markdown|html]`
Documentation format (default: `markdown`).

### Examples

#### Generate Entity Docs
```bash
specql docs entities/**/*.yaml
```

#### Output to Custom Directory
```bash
specql docs entities/ --output-dir docs/entities
```

### Output
```
docs/generated/
├── entities/
│   ├── contact.md
│   ├── company.md
│   └── order.md
└── index.md
```

---

## Configuration

### `confiture.yaml`

SpecQL uses Confiture for configuration.

**Location**: Project root (`confiture.yaml`)

**Example**:
```yaml
schema_dirs:
  - path: db/schema/00_foundation
    order: 0
  - path: db/schema/10_tables
    order: 10
  - path: db/schema/20_helpers
    order: 20
  - path: db/schema/30_functions
    order: 30
  - path: db/schema/40_metadata
    order: 40

environments:
  local:
    database_url: postgresql://localhost:5432/myapp_dev
    migrations_dir: db/migrations

  staging:
    database_url: ${DATABASE_URL}
    migrations_dir: db/migrations

  production:
    database_url: ${DATABASE_URL}
    migrations_dir: db/migrations
```

### Environment Variables

#### `DATABASE_URL`
PostgreSQL connection string.

**Format**: `postgresql://user:password@host:port/database`

**Example**:
```bash
export DATABASE_URL="postgresql://localhost:5432/myapp"
```

#### `SPECQL_ENV`
Override environment (overrides `--env` flag).

**Example**:
```bash
export SPECQL_ENV=staging
specql generate entities/**/*.yaml
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error (validation, parse, etc.) |
| `2` | File not found |
| `3` | Configuration error |

---

## Common Workflows

### Initial Setup
```bash
# 1. Install
uv add specql-generator

# 2. Verify
specql --version

# 3. Create first entity
mkdir -p entities
cat > entities/contact.yaml << 'EOF'
entity: Contact
schema: crm
fields:
  email: text
  name: text
EOF

# 4. Generate foundation
specql generate entities/contact.yaml --foundation-only

# 5. Generate tables
specql generate entities/contact.yaml
```

### Development Loop
```bash
# 1. Edit YAML
vim entities/contact.yaml

# 2. Validate
specql validate entities/contact.yaml

# 3. Generate
specql generate entities/contact.yaml

# 4. Apply to DB
psql myapp -f db/schema/10_tables/contact.sql

# 5. Test
psql myapp -c "SELECT * FROM crm.tb_contact;"
```

### Full Codegen (Backend + Frontend)
```bash
# Generate everything
specql generate entities/**/*.yaml \
  --with-impacts \
  --output-frontend=src/generated

# Output:
# - db/schema/ (PostgreSQL)
# - db/metadata/ (GraphQL metadata)
# - src/generated/types.ts (TypeScript)
# - src/generated/mutations.ts (Apollo hooks)
```

### CI/CD Pipeline
```bash
#!/bin/bash
# .github/workflows/generate-schema.yml

# 1. Validate all entities
specql validate entities/**/*.yaml || exit 1

# 2. Check table codes
specql check-codes entities/**/*.yaml || exit 1

# 3. Generate schema
specql generate entities/**/*.yaml --env production

# 4. Run migrations
confiture migrate up --env production
```

---

## Troubleshooting

See: `docs/guides/troubleshooting.md`

### Common Issues

#### "Command not found: specql"
**Solution**:
```bash
# Ensure UV environment is activated
uv sync
uv run specql --version
```

#### "No such file or directory"
**Solution**: Use absolute paths or run from project root
```bash
cd /path/to/project
specql generate entities/contact.yaml
```

#### "Confiture build failed"
**Solution**: Install Confiture
```bash
uv add fraiseql-confiture
```

---

## Reference

### Related Documentation
- **YAML Reference**: `docs/reference/yaml-reference.md`
- **Migration Guide**: `docs/guides/migration-guide.md`
- **Troubleshooting**: `docs/guides/troubleshooting.md`
- **Examples**: `examples/entities/`

### External Tools
- **UV**: https://github.com/astral-sh/uv
- **Confiture**: https://github.com/fraiseql/confiture
- **PostgreSQL**: https://www.postgresql.org/docs/
```

### Implementation Steps

1. **Create file**:
   ```bash
   touch docs/reference/cli-reference.md
   ```

2. **Document each command**:
   - Run `specql --help`
   - Run `specql generate --help`
   - Run each command variant
   - Document actual output

3. **Test examples**:
   - Create test entities
   - Run each example command
   - Verify output matches documentation

4. **Add workflow examples**:
   - Document common development patterns
   - Add CI/CD examples
   - Include troubleshooting

### Quality Criteria
- [ ] All commands documented
- [ ] All options explained
- [ ] Examples are tested and work
- [ ] Exit codes documented
- [ ] Common workflows included

---

## 📝 Task 4: Troubleshooting Guide

**File**: `docs/guides/troubleshooting.md`
**Priority**: MEDIUM
**Effort**: 4 hours
**Dependencies**: Task 1 (YAML Reference), Task 3 (CLI Reference)

### Objective
Provide quick solutions to common errors and issues users encounter.

### Content Structure

```markdown
# Troubleshooting Guide

Quick solutions to common SpecQL issues.

**Can't find your issue?** Search existing issues or create a new one: https://github.com/fraiseql/specql/issues

---

## Table of Contents

1. [Parse Errors](#parse-errors)
2. [Validation Errors](#validation-errors)
3. [Generation Errors](#generation-errors)
4. [Database Errors](#database-errors)
5. [CLI Issues](#cli-issues)
6. [Performance Issues](#performance-issues)
7. [Getting Help](#getting-help)

---

## Parse Errors

### "Missing 'entity' key"

**Error**:
```
Failed to parse entities/contact.yaml: Missing required key 'entity'
```

**Cause**: File uses `import:` instead of `entity:` (import-only file).

**Solution**: Import files reference stdlib and don't generate directly.

```yaml
# ❌ Import-only (doesn't generate)
import: stdlib/crm/contact

# ✅ Full entity (generates SQL)
entity: Contact
schema: crm
fields:
  email: text
```

**When to use imports**: Extending stdlib entities with custom fields.

---

### "Unknown field type"

**Error**:
```
Parse Error: Unknown field type 'string' at line 5
```

**Cause**: SpecQL uses different type names than some SQL dialects.

**Solution**: Use SpecQL type names

| ❌ Don't Use | ✅ Use Instead |
|-------------|---------------|
| `string` | `text` |
| `int` | `integer` |
| `bool` | `boolean` |
| `varchar` | `text` |
| `numeric` | `decimal` |

**Reference**: `docs/reference/yaml-reference.md#scalar-types`

---

### "Invalid YAML syntax"

**Error**:
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Cause**: YAML indentation or syntax error.

**Solution**: Check YAML formatting

```yaml
# ❌ Invalid (missing colon)
entity Contact
schema crm

# ✅ Valid
entity: Contact
schema: crm

# ❌ Invalid (inconsistent indentation)
fields:
 email: text
   name: text

# ✅ Valid (2-space indentation)
fields:
  email: text
  name: text
```

**Tools**: Use YAML linter (e.g., `yamllint`)

```bash
uv add --dev yamllint
yamllint entities/contact.yaml
```

---

### "Duplicate key"

**Error**:
```
yaml.constructor.ConstructorError: found duplicate key 'email'
```

**Cause**: Same field name appears twice.

**Solution**: Remove duplicate or rename one field

```yaml
# ❌ Duplicate
fields:
  email: text
  email: email  # Duplicate key

# ✅ Fixed
fields:
  email: text
  alternate_email: email
```

---

## Validation Errors

### "Table code already assigned"

**Error**:
```
ValueError: Table code '012311' already assigned to Contact
```

**Cause**: Multiple entities have the same `organization.table_code`.

**Solution**: Check uniqueness

```bash
specql check-codes entities/**/*.yaml
```

**Output**:
```
❌ Duplicate table codes found

⚠️  Code 012311 assigned to:
  • Contact (entities/crm/contact.yaml)
  • Customer (entities/crm/customer.yaml)
```

**Fix**: Assign unique codes or remove `table_code` if not needed.

---

### "Referenced entity not found"

**Error**:
```
Validation Error: Field 'company' references undefined entity 'Company'
```

**Cause**: `ref(Company)` but no `Company` entity exists.

**Solution**:
1. Create referenced entity first
2. Or fix typo in reference name

```yaml
# ❌ References missing entity
entity: Contact
fields:
  company: ref(Company)  # Company.yaml doesn't exist

# ✅ Option 1: Create Company.yaml
# entities/company.yaml
entity: Company
schema: crm
fields:
  name: text

# ✅ Option 2: Fix typo
entity: Contact
fields:
  company: ref(Organization)  # Correct entity name
```

---

### "Invalid enum value"

**Error**:
```
Validation Error: Enum must have at least 2 values
```

**Cause**: `enum()` with 0 or 1 value.

**Solution**: Enums need 2+ values

```yaml
# ❌ Invalid
status: enum(active)  # Only 1 value

# ✅ Valid
status: enum(active, inactive)  # 2+ values

# ✅ Alternative: Use boolean
active: boolean
```

---

### "Circular reference detected"

**Error**:
```
Validation Error: Circular reference: Contact → Company → Contact
```

**Cause**: Entities reference each other in a loop.

**Solution**: Break circle with nullable reference

```yaml
# ❌ Circular
# Contact → Company
entity: Contact
fields:
  company: ref(Company)

# Company → Contact
entity: Company
fields:
  primary_contact: ref(Contact)  # Circular!

# ✅ Fixed: Make one nullable
entity: Company
fields:
  primary_contact: ref(Contact)?  # Optional breaks circle
```

---

## Generation Errors

### "No such file or directory"

**Error**:
```
Error: Invalid value for 'ENTITY_FILES': Path 'entities/contact.yaml' does not exist
```

**Cause**: File path is wrong or command run from wrong directory.

**Solution**: Use absolute paths or run from project root

```bash
# ❌ Wrong directory
cd /tmp
specql generate entities/contact.yaml  # Fails

# ✅ Run from project root
cd /path/to/project
specql generate entities/contact.yaml

# ✅ Or use absolute path
specql generate /path/to/project/entities/contact.yaml
```

---

### "Confiture build failed"

**Error**:
```
❌ Confiture build failed: No such file 'confiture.yaml'
```

**Cause**: Confiture not configured or not installed.

**Solution**:

```bash
# 1. Install Confiture
uv add fraiseql-confiture

# 2. Create confiture.yaml
cat > confiture.yaml << 'EOF'
schema_dirs:
  - path: db/schema/10_tables
    order: 10

environments:
  local:
    database_url: postgresql://localhost/mydb
EOF

# 3. Verify
specql generate entities/contact.yaml
```

---

### "Schema not in domain registry"

**Error**:
```
ValueError: Schema 'crm' not found in domain registry
```

**Cause**: Schema not registered in `registry/domain_registry.yaml`.

**Solution**: Add schema to registry

```yaml
# registry/domain_registry.yaml
domains:
  crm:
    type: multi_tenant
    description: "Customer relationship management"
```

---

### "Output directory not found"

**Error**:
```
FileNotFoundError: Directory 'db/schema/10_tables' does not exist
```

**Cause**: Output directories not created.

**Solution**: Create directory structure

```bash
mkdir -p db/schema/{00_foundation,10_tables,20_helpers,30_functions,40_metadata}
```

---

## Database Errors

### "relation does not exist"

**Error**:
```sql
psql: ERROR: relation "crm.tb_contact" does not exist
```

**Cause**: Schema not applied to database.

**Solution**: Apply generated SQL files

```bash
# Apply foundation first
psql mydb -f db/schema/00_foundation/000_app_foundation.sql

# Apply tables
psql mydb -f db/schema/10_tables/*.sql

# Or use Confiture
confiture migrate up --env local
```

---

### "constraint violation"

**Error**:
```sql
ERROR: insert or update on table "tb_contact" violates foreign key constraint "fk_tb_contact_company"
DETAIL: Key (company)=(999) is not present in table "tb_company".
```

**Cause**: Referenced record doesn't exist.

**Solution**: Insert parent records first

```sql
-- Insert in dependency order
INSERT INTO crm.tb_company (name) VALUES ('Acme Corp');
INSERT INTO crm.tb_contact (email, company) VALUES ('john@acme.com', 1);
```

---

### "column does not exist"

**Error**:
```sql
ERROR: column "company_id" does not exist
```

**Cause**: SpecQL uses different column naming (no `_id` suffix for ref fields).

**Solution**: Use correct column name

```sql
# ❌ Wrong (old naming)
SELECT * FROM crm.tb_contact WHERE company_id = 1;

# ✅ Correct (SpecQL naming)
SELECT * FROM crm.tb_contact WHERE company = 1;
```

**YAML**:
```yaml
fields:
  company: ref(Company)  # Column name is 'company' (not 'company_id')
```

---

### "permission denied"

**Error**:
```sql
ERROR: permission denied for schema crm
```

**Cause**: Database user lacks permissions.

**Solution**: Grant permissions

```sql
-- As superuser
GRANT USAGE ON SCHEMA crm TO myapp_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA crm TO myapp_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA crm TO myapp_user;
```

---

## CLI Issues

### "Command not found: specql"

**Error**:
```bash
$ specql
command not found: specql
```

**Cause**: SpecQL not installed or UV environment not activated.

**Solution**:

```bash
# Option 1: Use uv run
uv run specql --version

# Option 2: Install globally
uv add specql-generator
specql --version

# Option 3: Check PATH
which specql
echo $PATH
```

---

### "Permission denied"

**Error**:
```bash
$ specql generate entities/contact.yaml
Permission denied: db/schema/10_tables/contact.sql
```

**Cause**: File permissions issue.

**Solution**:

```bash
# Check permissions
ls -la db/schema/10_tables/

# Fix permissions
chmod 644 db/schema/10_tables/*.sql
chmod 755 db/schema/10_tables/
```

---

### "Timeout during generation"

**Error**:
```
TimeoutError: Generation took longer than 30 seconds
```

**Cause**: Very large number of entities or complex actions.

**Solution**: Generate in batches

```bash
# ❌ All at once (slow)
specql generate entities/**/*.yaml

# ✅ By schema (faster)
specql generate entities/crm/*.yaml
specql generate entities/commerce/*.yaml

# ✅ Parallel generation
find entities -name '*.yaml' | xargs -P 4 -n 1 specql generate
```

---

## Performance Issues

### "Generation is slow"

**Symptom**: `specql generate` takes >10 seconds for small number of entities.

**Causes & Solutions**:

1. **Too many glob patterns**
   ```bash
   # ❌ Slow
   specql generate entities/*/*.yaml

   # ✅ Faster
   specql generate entities/**/*.yaml
   ```

2. **Confiture rebuilding**
   ```bash
   # Skip Confiture if not needed
   specql generate entities/contact.yaml --skip-confiture
   ```

3. **Large number of actions**
   - Profile generation: `specql generate --profile`
   - Split complex actions into smaller ones

---

### "Database queries are slow"

**Symptom**: Queries on generated tables are slow.

**Causes & Solutions**:

1. **Missing indexes**
   ```sql
   -- Add custom index
   CREATE INDEX idx_tb_contact_email ON crm.tb_contact(email);
   ```

2. **Large JSON columns**
   ```sql
   -- Add GIN index (auto-generated for json fields, but verify)
   CREATE INDEX idx_tb_contact_metadata ON crm.tb_contact USING GIN (metadata);
   ```

3. **Soft-deleted records**
   ```sql
   -- Filter deleted records
   SELECT * FROM crm.tb_contact WHERE deleted_at IS NULL;
   ```

---

## Getting Help

### Before Creating an Issue

1. **Search existing issues**: https://github.com/fraiseql/specql/issues
2. **Check documentation**:
   - YAML Reference: `docs/reference/yaml-reference.md`
   - CLI Reference: `docs/reference/cli-reference.md`
   - Migration Guide: `docs/guides/migration-guide.md`
3. **Run validation**: `specql validate entities/**/*.yaml --verbose`

### Creating a Good Issue

Include:

1. **SpecQL version**:
   ```bash
   specql --version
   # Or: git rev-parse HEAD
   ```

2. **Minimal YAML example**:
   ```yaml
   entity: Contact
   schema: crm
   fields:
     email: text
   ```

3. **Complete error message**:
   ```
   [Copy full error output]
   ```

4. **Steps to reproduce**:
   ```bash
   1. Create entities/contact.yaml with above content
   2. Run: specql generate entities/contact.yaml
   3. Error occurs
   ```

5. **Expected vs actual behavior**:
   - Expected: Should generate table
   - Actual: Parse error

### Community Resources

- **GitHub Issues**: https://github.com/fraiseql/specql/issues
- **Documentation**: `docs/`
- **Examples**: `examples/entities/`
- **Stdlib**: `stdlib/` (reference implementations)

---

## Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set log level
export SPECQL_LOG_LEVEL=DEBUG

# Run with verbose output
specql generate entities/contact.yaml --verbose

# Check logs
tail -f /tmp/specql.log
```

---

## Common Gotchas

### 1. Auto-Generated Fields
❌ **Don't include** in YAML: `id`, `created_at`, `updated_at`, `tenant_id`
✅ **These are automatic** - SpecQL adds them

### 2. Field Names vs Column Names
```yaml
company: ref(Company)  # Field name is 'company'
# Column name is also 'company' (NOT 'company_id')
```

### 3. Enum Values Are Case-Sensitive
```yaml
status: enum(Active, Inactive)  # Capital A, I
# ❌ INSERT: status = 'active'  (lowercase fails)
# ✅ INSERT: status = 'Active'
```

### 4. Nullable References
```yaml
# ❌ Circular reference
company: ref(Company)
# Company also refs Contact

# ✅ Break circle
company: ref(Company)?  # Nullable
```

### 5. Import vs Entity
```yaml
# Import = reference only (doesn't generate)
import: stdlib/crm/contact

# Entity = full definition (generates SQL)
entity: Contact
```

---

## Diagnostic Commands

### Check Entity Validity
```bash
specql validate entities/contact.yaml --verbose
```

### Check Table Codes
```bash
specql check-codes entities/**/*.yaml
```

### Compare Generated vs Existing
```bash
specql diff entities/contact.yaml --compare db/schema/10_tables/contact.sql
```

### Test Database Connection
```bash
psql $DATABASE_URL -c "SELECT version();"
```

### Check Confiture Config
```bash
confiture validate confiture.yaml
```

---

**Still stuck?** Create a detailed issue: https://github.com/fraiseql/specql/issues/new
```

### Implementation Steps

1. **Collect common errors**:
   ```bash
   # Search existing issues
   gh issue list --label bug --limit 100

   # Review test failures
   grep -r "pytest.raises" tests/
   ```

2. **Document each error**:
   - Error message (exact text)
   - Root cause
   - Step-by-step solution
   - Prevention tips

3. **Test solutions**:
   - Reproduce each error
   - Verify solution works
   - Document workarounds if no fix

4. **Add diagnostic tools**:
   - Debug mode instructions
   - Validation commands
   - Logging configuration

### Quality Criteria
- [ ] All common errors documented
- [ ] Solutions are tested and work
- [ ] Root causes explained
- [ ] Prevention tips included
- [ ] Diagnostic commands provided

---

## 📝 Task 5: Quick Reference Card

**File**: `docs/QUICK_REFERENCE.md`
**Priority**: LOW (High Value)
**Effort**: 2 hours
**Dependencies**: Task 1 (YAML Reference)

### Objective
Single-page cheat sheet for quick lookups while coding.

### Content Structure

[Content is concise version of YAML Reference - see issue for details]

**Implementation**: Extract key examples from Task 1, format as cheat sheet.

---

## 📝 Task 6: Reorganize Documentation

**File**: Multiple (restructure `docs/`)
**Priority**: LOW
**Effort**: 3 hours
**Dependencies**: All above tasks

### Objective
Improve documentation discoverability by organizing into clear categories.

### Current Structure
```
docs/
├── architecture/      # Technical/implementation docs
├── guides/            # Mixed user + developer guides
├── implementation-plans/  # Development plans
├── qa/                # Test reports
└── reference/         # Limited reference material
```

### Proposed Structure
```
docs/
├── README.md                    # Documentation index (NEW)
├── getting-started/             # NEW: Beginner path
│   ├── installation.md
│   ├── your-first-entity.md
│   └── your-first-action.md
├── guides/                      # How-to guides (user-focused)
│   ├── migration-guide.md       # NEW (Task 2)
│   ├── actions-guide.md         # EXISTING
│   ├── multi-tenancy.md         # EXISTING
│   ├── hierarchical-entities.md # EXISTING
│   └── troubleshooting.md       # NEW (Task 4)
├── reference/                   # Complete references
│   ├── yaml-reference.md        # NEW (Task 1)
│   ├── cli-reference.md         # NEW (Task 3)
│   ├── scalar-types.md          # EXISTING
│   ├── generated-sql.md         # NEW
│   └── api/                     # Future: Python API docs
├── architecture/                # EXISTING: Keep as-is
│   ├── SPECQL_BUSINESS_LOGIC_REFINED.md
│   ├── INTEGRATION_PROPOSAL.md
│   └── ... (technical design docs)
├── contributing/                # NEW: Developer docs
│   ├── CONTRIBUTING.md
│   ├── team-structure.md
│   └── testing.md
├── implementation-plans/        # EXISTING: Keep as-is
└── qa/                          # EXISTING: Keep as-is
```

### Implementation Steps

1. **Create new documentation index**:
   ```markdown
   # docs/README.md

   # SpecQL Documentation

   ## Getting Started
   - [Installation](getting-started/installation.md)
   - [Your First Entity](getting-started/your-first-entity.md)
   - [Your First Action](getting-started/your-first-action.md)

   ## User Guides
   - [Migration Guide](guides/migration-guide.md) - Migrate existing databases
   - [Actions Guide](guides/actions-guide.md) - Write business logic
   - [Multi-Tenancy](guides/multi-tenancy.md) - Multi-tenant architecture
   - [Troubleshooting](guides/troubleshooting.md) - Common issues

   ## Reference
   - [YAML Reference](reference/yaml-reference.md) - Complete syntax
   - [CLI Reference](reference/cli-reference.md) - Command-line tools
   - [Scalar Types](reference/scalar-types.md) - Field types
   - [Generated SQL](reference/generated-sql.md) - What SpecQL produces

   ## Architecture
   - [Business Logic Spec](architecture/SPECQL_BUSINESS_LOGIC_REFINED.md)
   - [Integration Proposal](architecture/INTEGRATION_PROPOSAL.md)
   - [Team Structure](architecture/TEAM_STRUCTURE.md)

   ## Contributing
   - [Contributing Guide](contributing/CONTRIBUTING.md)
   - [Development Setup](contributing/development-setup.md)
   - [Testing Guide](contributing/testing.md)
   ```

2. **Create getting-started guides**:
   - Extract from README
   - Add step-by-step walkthroughs
   - Focus on first 15 minutes

3. **Move files to new structure**:
   ```bash
   mkdir -p docs/getting-started
   mkdir -p docs/contributing

   # Create new files (don't move existing yet - preserve git history)
   ```

4. **Update all internal links**:
   ```bash
   # Find all markdown links
   grep -r "docs/" --include="*.md" .

   # Update links to new structure
   ```

5. **Add navigation to each doc**:
   ```markdown
   <!-- Add to top of each file -->
   📚 **[Documentation Index](../README.md)** |
   ⬅️ [Previous: Topic](../file.md) |
   ➡️ [Next: Topic](file.md)
   ```

### Quality Criteria
- [ ] All docs categorized logically
- [ ] Documentation index complete
- [ ] All internal links work
- [ ] Navigation aids added
- [ ] Getting started path clear

---

## 🎯 Execution Strategy

### Phase 1: Core References (HIGH Priority - Week 1)
**Order**:
1. Task 1: YAML Reference (4h)
2. Task 2: Migration Guide (6h)

**Total**: 10 hours / ~1.5 days

**Rationale**: These two docs provide the most immediate value for new users.

### Phase 2: Support Documentation (MEDIUM Priority - Week 2)
**Order**:
3. Task 3: CLI Reference (3h)
4. Task 4: Troubleshooting (4h)

**Total**: 7 hours / ~1 day

**Rationale**: CLI reference enables self-service; troubleshooting reduces support burden.

### Phase 3: Polish (LOW Priority - Week 3)
**Order**:
5. Task 5: Quick Reference (2h)
6. Task 6: Reorganize Structure (3h)

**Total**: 5 hours / ~0.5 days

**Rationale**: Nice-to-have improvements that enhance usability but aren't blocking.

---

## ✅ Success Criteria

### Quantitative
- [ ] 5-6 new documentation files created
- [ ] Documentation covers 100% of YAML syntax
- [ ] All CLI commands documented
- [ ] 20+ common errors with solutions
- [ ] New user can generate first entity in <15 minutes

### Qualitative
- [ ] Documentation is searchable (good TOCs)
- [ ] Examples are copy-paste ready
- [ ] Migration path is clear for existing projects
- [ ] Troubleshooting reduces issue volume
- [ ] Professional presentation

---

## 🚀 Next Steps After Completion

1. **Announce documentation updates** in README changelog
2. **Link from main README** to docs/README.md
3. **Create video walkthrough** (5-10 minutes)
4. **Gather feedback** from new users
5. **Iterate based on common questions**

---

## 📊 Estimated Impact

**Before**:
- New users struggle with syntax
- Migration unclear
- Support burden high
- Documentation fragmented

**After**:
- Clear reference for all syntax
- Step-by-step migration path
- Self-service troubleshooting
- Professional, organized docs
- <15 minute onboarding

**ROI**: ~22 hours of work → Significant reduction in support time + faster adoption

---

## 📝 Notes for Implementation Agent

### Context Available
- **Existing docs**: `docs/` directory has good architecture docs
- **Test examples**: `tests/unit/` has comprehensive YAML examples
- **Code reference**: `src/core/models/` defines all syntax
- **CLI code**: `src/cli/` shows all commands

### Quality Guidelines
- **Copy-paste ready**: All examples must work as-is
- **Tested examples**: Validate YAML examples with `specql validate`
- **Cross-referenced**: Link related docs together
- **Searchable**: Good table of contents in each doc
- **Professional tone**: Clear, concise, helpful

### Validation Process
1. **Syntax check**: All YAML examples validate
2. **Command check**: All CLI examples work
3. **Link check**: All internal links valid
4. **Spell check**: Run spell checker
5. **Review**: Read through as if you're a new user

---

**Ready for implementation!** This plan provides complete guidance for creating comprehensive user documentation for SpecQL.