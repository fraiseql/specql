# Archived SQLite Databases

**Date Archived**: 2025-11-12
**Reason**: Data storage consolidation (Phase 3 of consolidation plan)

## Contents

### `pattern_library.db` (136 KB)
- **Original Purpose**: Pattern library storage
- **Contents**: 25 language primitives (declare, if, foreach, etc.)
- **Status**: ✅ **Migrated to PostgreSQL** (`specql.pattern_library` schema)
- **Migration Date**: 2025-11-12
- **Verification**: All 25 patterns migrated with `source_type='migrated'`

### `test_pattern_library.db` (0 KB)
- **Original Purpose**: Test database for pattern library
- **Contents**: Empty
- **Status**: No data to migrate

### `maestro_analytics.db` (0 KB)
- **Original Purpose**: Maestro analytics tracking
- **Contents**: Empty
- **Status**: No data to migrate

## Migration Details

All pattern data from `pattern_library.db` was successfully migrated to PostgreSQL using the migration script:

```bash
python scripts/migrate_patterns_to_postgresql.py \
  --sqlite-db pattern_library.db
```

**Results**:
- ✅ 25 patterns migrated
- ✅ 0 patterns skipped
- ✅ 0 errors

## Current State

All runtime data is now stored in PostgreSQL:

- **Database**: `specql`
- **Schemas**:
  - `specql_registry` - Domain/subdomain/entity registration
  - `pattern_library` - Domain patterns with pgvector embeddings
- **Connection**: `postgresql://specql_user:specql_dev_password@localhost/specql`

## Schema Definitions

Entity schema definitions remain in YAML format:
- `entities/*.yaml` - User entity definitions
- `stdlib/*.yaml` - Standard library entities

## Restore Instructions (If Needed)

If you need to access the archived SQLite data:

```bash
# View patterns from archived database
sqlite3 archive/sqlite_databases/pattern_library.db \
  "SELECT pattern_name, pattern_category FROM patterns;"

# Export to CSV
sqlite3 archive/sqlite_databases/pattern_library.db \
  -header -csv \
  "SELECT * FROM patterns;" > patterns_backup.csv
```

## Verification

To verify PostgreSQL contains all migrated data:

```bash
export SPECQL_DB_URL='postgresql://specql_user:specql_dev_password@localhost/specql'

# Count patterns
psql $SPECQL_DB_URL -c \
  "SELECT COUNT(*) FROM pattern_library.domain_patterns;"

# List patterns
psql $SPECQL_DB_URL -c \
  "SELECT name, category, source_type FROM pattern_library.domain_patterns ORDER BY name;"
```

---

**Consolidation Status**: ✅ Phase 3 complete - SQLite databases archived
**Next Phase**: Phase 4 - Remove SQLite references from codebase
