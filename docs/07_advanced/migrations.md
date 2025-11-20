# Migrations Guide

> **Safe schema evolution for SpecQL applications—change schemas without downtime**

## Overview

Database migrations allow you to:
- ✅ **Evolve schemas** safely over time
- ✅ **Version control** database changes
- ✅ **Rollback** failed migrations
- ✅ **Coordinate** schema and code deployments
- ✅ **Zero-downtime** schema changes

**Goal**: Automated, reversible, zero-downtime schema evolution

---

## Migration Strategies

### 1. Expand-Contract Pattern

**Safest approach for production**:

1. **Expand**: Add new schema (backward compatible)
2. **Migrate data**: Copy old → new
3. **Deploy code**: Support both old and new
4. **Contract**: Remove old schema

**Example**: Renaming a column

```sql
-- Migration 1: Expand (add new column)
ALTER TABLE crm.tb_contact
ADD COLUMN full_name TEXT;

-- Backfill data
UPDATE crm.tb_contact
SET full_name = first_name || ' ' || last_name;

-- Migration 2: Deploy code using full_name

-- Migration 3: Contract (remove old columns) - AFTER code deployed
ALTER TABLE crm.tb_contact
DROP COLUMN first_name,
DROP COLUMN last_name;
```

**Benefits**: Zero downtime, rollback-safe

---

### 2. Blue-Green Migrations

**For large schema changes**:

1. Create new schema version (green)
2. Migrate data to green
3. Switch application to green
4. Drop old schema (blue)

```sql
-- Create new schema version
CREATE SCHEMA crm_v2;

-- Copy tables with changes
CREATE TABLE crm_v2.tb_contact AS
SELECT
    pk_contact,
    id,
    identifier,
    first_name || ' ' || last_name AS full_name,
    email,
    phone,
    fk_company,
    status,
    created_at,
    updated_at
FROM crm.tb_contact;

-- Switch application
-- (Update DATABASE_URL to use crm_v2)

-- After validation, drop old schema
DROP SCHEMA crm CASCADE;
ALTER SCHEMA crm_v2 RENAME TO crm;
```

---

## Migration Tools

### Flyway (Recommended)

**Directory structure**:
```
migrations/
├── V001__initial_schema.sql
├── V002__add_orders_table.sql
├── V003__rename_contact_name.sql
├── V004__add_qualify_lead_action.sql
└── R__refresh_materialized_views.sql  # Repeatable
```

**Versioned migration**:
```sql
-- V003__rename_contact_name.sql

-- Expand: Add new column
ALTER TABLE crm.tb_contact
ADD COLUMN full_name TEXT;

-- Backfill
UPDATE crm.tb_contact
SET full_name = first_name || ' ' || last_name
WHERE full_name IS NULL;

-- Make NOT NULL after backfill
ALTER TABLE crm.tb_contact
ALTER COLUMN full_name SET NOT NULL;

-- Note: Remove first_name/last_name in next migration after code deployed
```

**Run migrations**:
```bash
flyway -url=jdbc:postgresql://localhost:5432/myapp \
       -user=app_user \
       -password=secret \
       migrate
```

---

### Liquibase (Alternative)

**changelog.xml**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <changeSet id="3" author="dev">
        <addColumn tableName="tb_contact" schemaName="crm">
            <column name="full_name" type="TEXT"/>
        </addColumn>

        <sql>
            UPDATE crm.tb_contact
            SET full_name = first_name || ' ' || last_name;
        </sql>

        <addNotNullConstraint
            tableName="tb_contact"
            columnName="full_name"
            schemaName="crm"/>
    </changeSet>
</databaseChangeLog>
```

**Run migrations**:
```bash
liquibase update
```

---

## SpecQL-Specific Migrations

### Regenerating Schema from YAML

**Workflow**:

1. **Update SpecQL YAML**:
   ```yaml
   entity: Contact
   fields:
     full_name: text!  # Changed from first_name/last_name
     email: email!
   ```

2. **Generate new schema**:
   ```bash
   specql generate entities/contact.yaml --output generated/
   ```

3. **Create migration** from diff:
   ```bash
   specql diff entities/contact.yaml \
     --compare db/schema/contact.sql \
     --output migrations/V005__update_contact_schema.sql
   ```

4. **Review and apply migration**:
   ```bash
   flyway migrate
   ```

---

### Handling Breaking Changes

**Adding required field** (breaks old code):

```yaml
# Before
entity: Contact
fields:
  email: email!

# After (add required phone)
entity: Contact
fields:
  email: email!
  phone: phoneNumber!  # New required field
```

**Migration strategy**:

```sql
-- V006__add_phone_field.sql

-- Step 1: Add nullable column
ALTER TABLE crm.tb_contact
ADD COLUMN phone TEXT CHECK (phone ~ '^\+[1-9]\d{1,14}$');

-- Step 2: Backfill with default (or from external data)
UPDATE crm.tb_contact
SET phone = '+10000000000'  -- Placeholder
WHERE phone IS NULL;

-- Step 3: Make NOT NULL (after backfill complete)
ALTER TABLE crm.tb_contact
ALTER COLUMN phone SET NOT NULL;
```

**Deploy code** supporting new field, THEN make NOT NULL.

---

## Zero-Downtime Migration Patterns

### Adding a Column

**Safe** (immediate):
```sql
-- Always safe (nullable)
ALTER TABLE crm.tb_contact
ADD COLUMN middle_name TEXT;

-- Safe with default
ALTER TABLE crm.tb_contact
ADD COLUMN is_verified BOOLEAN DEFAULT FALSE NOT NULL;
```

---

### Removing a Column

**Use Expand-Contract**:

```sql
-- Migration 1: Ignore column (deploy code that doesn't use it)
-- (No SQL needed, just deploy code)

-- Migration 2: Remove column (after code deployed)
ALTER TABLE crm.tb_contact
DROP COLUMN middle_name;
```

**Rollback safety**: Deploy code ignoring column BEFORE dropping.

---

### Renaming a Column

**Use Expand-Contract**:

```sql
-- Migration 1: Add new column, backfill
ALTER TABLE crm.tb_contact
ADD COLUMN email_address TEXT;

UPDATE crm.tb_contact
SET email_address = email;

ALTER TABLE crm.tb_contact
ALTER COLUMN email_address SET NOT NULL;

-- Migration 2: Deploy code using email_address

-- Migration 3: Drop old column
ALTER TABLE crm.tb_contact
DROP COLUMN email;
```

**Alternative**: Use view for compatibility:

```sql
-- Create view with old column name
CREATE VIEW crm.v_contact_compat AS
SELECT
    pk_contact,
    id,
    email_address AS email,  -- Alias new column as old name
    ...
FROM crm.tb_contact;

-- Old code can use v_contact_compat
-- New code uses tb_contact directly
```

---

### Changing Column Type

**Use Expand-Contract**:

```sql
-- Migration 1: Add new column with new type
ALTER TABLE sales.tb_order
ADD COLUMN total_amount_cents INTEGER;

-- Backfill (convert dollars to cents)
UPDATE sales.tb_order
SET total_amount_cents = (total_amount * 100)::INTEGER;

ALTER TABLE sales.tb_order
ALTER COLUMN total_amount_cents SET NOT NULL;

-- Migration 2: Deploy code using total_amount_cents

-- Migration 3: Drop old column
ALTER TABLE sales.tb_order
DROP COLUMN total_amount;

ALTER TABLE sales.tb_order
RENAME COLUMN total_amount_cents TO total_amount;
```

---

### Adding NOT NULL Constraint

**Safe approach**:

```sql
-- Step 1: Add column as nullable
ALTER TABLE crm.tb_contact
ADD COLUMN phone TEXT;

-- Step 2: Backfill data
UPDATE crm.tb_contact
SET phone = '+10000000000'
WHERE phone IS NULL;

-- Step 3: Add NOT NULL constraint (after backfill)
ALTER TABLE crm.tb_contact
ALTER COLUMN phone SET NOT NULL;
```

**Avoid**: Adding NOT NULL immediately (fails if any NULLs exist).

---

## Handling Large Tables

### Online Schema Changes (pg_repack)

**For tables > 1GB**:

```bash
# Install pg_repack
apt-get install postgresql-15-repack

# Add column without locking table
pg_repack -t crm.tb_contact --add-column="phone TEXT"
```

**Benefits**: No downtime for large tables

---

### Partitioned Migrations

**For very large tables**:

```sql
-- Add column to new partitions only
DO $$
DECLARE
    partition_name TEXT;
BEGIN
    FOR partition_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'crm'
          AND tablename LIKE 'tb_contact_y%'
    LOOP
        EXECUTE format('ALTER TABLE crm.%I ADD COLUMN phone TEXT', partition_name);
    END LOOP;
END $$;

-- Backfill in batches
DO $$
DECLARE
    batch_size INT := 10000;
    total_updated INT := 0;
BEGIN
    LOOP
        UPDATE crm.tb_contact
        SET phone = '+10000000000'
        WHERE phone IS NULL
        LIMIT batch_size;

        GET DIAGNOSTICS total_updated = ROW_COUNT;
        EXIT WHEN total_updated = 0;

        -- Commit batch
        COMMIT;

        -- Sleep to avoid overload
        PERFORM pg_sleep(0.1);
    END LOOP;
END $$;
```

---

## Rollback Strategies

### Automatic Rollback

**Flyway undo migrations**:

```sql
-- V003__add_phone.sql (forward)
ALTER TABLE crm.tb_contact
ADD COLUMN phone TEXT;

-- U003__add_phone.sql (undo)
ALTER TABLE crm.tb_contact
DROP COLUMN phone;
```

**Rollback**:
```bash
flyway undo
```

---

### Manual Rollback

**Transaction-wrapped migrations**:

```sql
-- V003__add_phone.sql
BEGIN;

ALTER TABLE crm.tb_contact
ADD COLUMN phone TEXT;

-- Test migration
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM crm.tb_contact;
    RAISE NOTICE 'Migrated % rows', v_count;

    -- Validation checks
    IF EXISTS (SELECT 1 FROM crm.tb_contact WHERE phone IS NOT NULL) THEN
        RAISE EXCEPTION 'Unexpected data in phone column';
    END IF;
END $$;

COMMIT;
```

**If migration fails**: Automatic rollback via transaction.

---

## Testing Migrations

### Test in Staging

```bash
# 1. Backup production
pg_dump -h prod-db myapp > prod_backup.sql

# 2. Restore to staging
psql -h staging-db myapp < prod_backup.sql

# 3. Test migration
flyway -url=jdbc:postgresql://staging-db:5432/myapp migrate

# 4. Validate
psql -h staging-db myapp -c "SELECT COUNT(*) FROM crm.tb_contact WHERE phone IS NULL"

# 5. If successful, apply to production
```

---

### Automated Testing

```python
# tests/migrations/test_add_phone.py
import pytest

def test_add_phone_migration(db_connection):
    """Test adding phone column"""
    cursor = db_connection.cursor()

    # Run migration
    with open('migrations/V006__add_phone.sql') as f:
        cursor.execute(f.read())

    # Verify column exists
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'crm'
          AND table_name = 'tb_contact'
          AND column_name = 'phone'
    """)
    result = cursor.fetchone()

    assert result is not None
    assert result['data_type'] == 'text'
    assert result['is_nullable'] == 'YES'

def test_backfill_phone(db_connection):
    """Test phone backfill"""
    cursor = db_connection.cursor()

    # Run backfill
    cursor.execute("""
        UPDATE crm.tb_contact
        SET phone = '+10000000000'
        WHERE phone IS NULL
    """)

    # Verify no NULLs
    cursor.execute("SELECT COUNT(*) FROM crm.tb_contact WHERE phone IS NULL")
    assert cursor.fetchone()[0] == 0
```

---

## Migration Best Practices

### ✅ DO

1. **Always use transactions** (wrap in BEGIN/COMMIT)
2. **Test in staging** before production
3. **Use Expand-Contract** for breaking changes
4. **Backfill in batches** for large tables
5. **Version control** all migrations
6. **Add comments** explaining why
7. **Monitor performance** during migration
8. **Have rollback plan** documented

---

### ❌ DON'T

1. **Don't add NOT NULL** without backfill
2. **Don't rename** directly (use Expand-Contract)
3. **Don't drop columns** before deploying code
4. **Don't run untested** migrations in production
5. **Don't lock tables** during migrations (use CONCURRENTLY)
6. **Don't skip version numbers**
7. **Don't modify applied** migrations

---

## Migration Checklist

### Pre-Migration

- [ ] Migration tested in staging
- [ ] Rollback plan documented
- [ ] Downtime window scheduled (if needed)
- [ ] Backup created
- [ ] Team notified
- [ ] Monitoring alerts configured

### During Migration

- [ ] Monitor database metrics (CPU, connections)
- [ ] Watch for lock waits
- [ ] Check application logs for errors
- [ ] Verify data integrity

### Post-Migration

- [ ] Validate migration success
- [ ] Check application functionality
- [ ] Monitor error rates
- [ ] Document any issues
- [ ] Clean up temporary artifacts

---

## Common Migration Scenarios

### Adding an Index (Non-Blocking)

```sql
-- ❌ Bad: Locks table
CREATE INDEX idx_contact_status ON crm.tb_contact (status);

-- ✅ Good: Concurrent (no lock)
CREATE INDEX CONCURRENTLY idx_contact_status ON crm.tb_contact (status);
```

---

### Adding Foreign Key

```sql
-- Step 1: Add column
ALTER TABLE sales.tb_order
ADD COLUMN fk_customer INTEGER;

-- Step 2: Backfill
UPDATE sales.tb_order o
SET fk_customer = (
    SELECT pk_customer
    FROM crm.tb_customer c
    WHERE c.id = o.customer_id
);

-- Step 3: Add FK constraint (validates existing data)
ALTER TABLE sales.tb_order
ADD CONSTRAINT fk_order_customer
    FOREIGN KEY (fk_customer)
    REFERENCES crm.tb_customer(pk_customer);
```

---

### Splitting a Table

```sql
-- Original: Single table
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    -- Address fields
    street TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT
);

-- Migration: Split into two tables
CREATE TABLE crm.tb_contact_address (
    pk_contact_address INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fk_contact INTEGER NOT NULL,
    street TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    CONSTRAINT fk_address_contact
        FOREIGN KEY (fk_contact)
        REFERENCES crm.tb_contact(pk_contact)
);

-- Migrate data
INSERT INTO crm.tb_contact_address (fk_contact, street, city, state, postal_code)
SELECT pk_contact, street, city, state, postal_code
FROM crm.tb_contact
WHERE street IS NOT NULL;

-- Remove address columns from contact
ALTER TABLE crm.tb_contact
DROP COLUMN street,
DROP COLUMN city,
DROP COLUMN state,
DROP COLUMN postal_code;
```

---

## Next Steps

### Learn More

- **[Deployment Guide](deployment.md)** - Deploy with migrations
- **[Testing Guide](testing.md)** - Test migrations
- **[Performance Tuning](performance-tuning.md)** - Optimize migrations

### Tools

- **Flyway** - Database migrations
- **Liquibase** - Alternative migration tool
- **pg_repack** - Online schema changes
- **pgAdmin** - Database management

---

## Summary

You've learned:
- ✅ Expand-Contract pattern for zero-downtime
- ✅ Migration tools (Flyway, Liquibase)
- ✅ Safe patterns for common changes
- ✅ Large table migration strategies
- ✅ Rollback strategies
- ✅ Testing migrations
- ✅ Common migration scenarios

**Key Takeaway**: Safe migrations require Expand-Contract pattern—add before removing, deploy code between steps.

**Next**: Return to [Advanced Topics](../07_advanced/) for more guides →

---

**Migrate safely—schema changes should never cause downtime.**
