# Week 04: Data Migration Planning

**Objective**: Create safe, tested data migration scripts

## Day 1-2: Mapping Tables

```yaml
# reverse_engineering/mappings/table_mappings.yaml
tables:
  contact:
    old_table: public.contact
    new_table: crm.tb_contact
    strategy: rename_with_trinity
    mappings:
      id: pk_contact              # UUID → INTEGER pk
      email: email
      company_id: fk_company      # UUID → INTEGER fk
      status: status
      created_at: created_at
      updated_at: updated_at
      deleted_at: deleted_at

  company:
    old_table: public.company
    new_table: crm.tb_company
    strategy: rename_with_trinity
    mappings:
      id: pk_company
      name: identifier
      industry: industry
```

## Day 3-4: Migration Script Generation

```bash
# Generate data migration scripts
uv run python scripts/migration/generate_data_migration.py \
  reverse_engineering/mappings/table_mappings.yaml \
  > db/migrations/data_migration/001_migrate_printoptim_data.sql

# Generate validation scripts
uv run python scripts/migration/generate_validation_scripts.py \
  reverse_engineering/mappings/table_mappings.yaml \
  > db/migrations/validation/001_validate_migration.sql
```

## Day 5: Test Migration on Staging

```bash
# Create staging test database
dropdb --if-exists printoptim_staging_migration
createdb printoptim_staging_migration

# Restore production data to staging
pg_restore -d printoptim_staging_migration production_dump.backup

# Execute migration
psql printoptim_staging_migration < db/migrations/data_migration/001_migrate_printoptim_data.sql

# Run validation
psql printoptim_staging_migration < db/migrations/validation/001_validate_migration.sql
```

## Deliverables

- ✅ Complete table mapping YAML
- ✅ Data migration SQL scripts
- ✅ Validation SQL scripts
- ✅ Staging migration test report