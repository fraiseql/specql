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
  identifier TEXT UNIQUE NOT NULL,
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