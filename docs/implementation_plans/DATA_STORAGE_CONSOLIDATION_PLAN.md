# Data Storage Consolidation Plan: Clean Up the Mess

**Date**: 2025-11-12
**Status**: Implementation Plan - Ready to Execute
**Goal**: Consolidate from 3 storage formats (YAML, SQLite, PostgreSQL) to 2 clear purposes
**Timeline**: 1-2 days

---

## 🎯 Current State: The Mess

### What We Have Now

```
SpecQL Data Storage (MESSY):

1. YAML Files
   - registry/archive/domain_registry.yaml (ARCHIVED)
   - registry/archive/service_registry.yaml (ARCHIVED)
   - entities/*.yaml (70 files) ← ACTIVE
   - stdlib/*.yaml (70 files) ← ACTIVE

2. SQLite Databases
   - pattern_library.db (136 KB, 25 primitives)
   - test_pattern_library.db (0 KB, empty)
   - database/maestro_analytics.db (0 KB, empty)

3. PostgreSQL
   - NOT SET UP YET
   - Code exists but no database created
   - Repository pattern ready but unused
```

### Why This Is Messy

| Storage | Purpose | Status | Problem |
|---------|---------|--------|---------|
| **YAML (archived)** | Domain registry | Archived | ❌ Obsolete, should delete |
| **YAML (entities)** | Entity definitions | Active | ✅ Good, keep |
| **SQLite (patterns)** | Language primitives | Active | ❌ Wrong tool, should migrate |
| **SQLite (test)** | Testing | Empty | ❌ Unused, should delete |
| **SQLite (analytics)** | Analytics | Empty | ❌ Unused, should delete |
| **PostgreSQL** | Everything | Not set up | ❌ Should be primary |

---

## 🎯 Target State: Clean Architecture

### What We Want

```
SpecQL Data Storage (CLEAN):

1. YAML Files (entities/ + stdlib/)
   Purpose: Entity schema definitions (source code)
   Status: Version controlled in Git
   Usage: Input to code generation
   Example: entities/crm/contact.yaml

2. PostgreSQL (specql database)
   Purpose: ALL runtime data
   Status: Single source of truth
   Usage: Domain registry, pattern library, analytics
   Schemas:
     - specql_registry (domains, subdomains, entities)
     - pattern_library (patterns with pgvector)
     - analytics (usage metrics, performance)
```

### Clear Separation

| Data Type | Storage | Versioned | Purpose |
|-----------|---------|-----------|---------|
| **Entity Definitions** | YAML | Yes (Git) | Schema source code |
| **Domain Registry** | PostgreSQL | No (backups) | Runtime: track codes |
| **Pattern Library** | PostgreSQL | No (backups) | Runtime: discovered patterns |
| **Analytics** | PostgreSQL | No (backups) | Runtime: metrics |

---

## 📋 Detailed Implementation Plan

### Phase 1: Set Up PostgreSQL (30 minutes)

#### Task 1.1: Create PostgreSQL Database

**Script**: `scripts/setup_database.sh` (already exists)

**Run**:
```bash
# Create database and schemas
./scripts/setup_database.sh

# Expected output:
Creating PostgreSQL database for SpecQL...
✅ Database 'specql' created
✅ User 'specql_user' created
✅ Schema 'specql_registry' created
✅ Schema 'pattern_library' created
✅ Tables created:
   - specql_registry.tb_domain
   - specql_registry.tb_subdomain
   - specql_registry.tb_entity_registration
   - pattern_library.tb_pattern
✅ pgvector extension enabled
```

**Verify**:
```bash
# Set environment variable
export SPECQL_DB_URL='postgresql://specql_user:specql_dev_password@localhost/specql'

# Test connection
psql $SPECQL_DB_URL -c "SELECT current_database(), current_user"

# Expected output:
 current_database | current_user
------------------+--------------
 specql           | specql_user
```

**Files Modified**: None (just database creation)

---

#### Task 1.2: Update Configuration

**File**: `src/core/config.py`

**Change**:
```python
# OLD:
self.registry_yaml_path = Path('registry/domain_registry.yaml')

# NEW:
# Remove YAML path (no longer needed)
# Add pattern library backend
self.pattern_library_backend = self._get_pattern_backend()
```

**Full Change**:
```python
class SpecQLConfig:
    def __init__(self):
        # Repository backend configuration
        self.repository_backend = self._get_repository_backend()
        self.database_url = os.getenv('SPECQL_DB_URL')

        # REMOVE: self.registry_yaml_path = Path('registry/domain_registry.yaml')

        # ADD: Pattern library backend
        self.pattern_library_backend = self._get_pattern_backend()

        # Validate configuration
        self._validate_config()

    def _get_pattern_backend(self) -> str:
        """Determine pattern library backend"""
        if self.database_url:
            return 'postgresql'
        return 'in_memory'  # For tests
```

**Deliverable**: Configuration ready for PostgreSQL-only

---

### Phase 2: Migrate SQLite Patterns to PostgreSQL (30 minutes)

#### Task 2.1: Understand What's in SQLite

**Check Current Data**:
```bash
# List all patterns
sqlite3 pattern_library.db "SELECT pattern_name, pattern_category FROM patterns"

# Output:
declare|primitive
assign|primitive
call_function|primitive
call_service|primitive
return|primitive
return_early|primitive
if|control_flow
foreach|control_flow
while|control_flow
for_query|control_flow
select|query
insert|query
update|query
delete|query
map|data_transform
filter|data_transform
reduce|data_transform
validate|data_transform
cte|query
join|query
aggregate|query
union|query
subquery|query
window|query
transaction|control_flow
```

**Analysis**: These are **SpecQL language primitives** (25 patterns)

**Decision**:
- ✅ **DO** migrate to PostgreSQL
- ✅ **BUT** mark as `source_type = 'language_primitive'`
- ✅ Keep separate from user-discovered patterns

---

#### Task 2.2: Migrate Patterns

**Script**: `scripts/migrate_patterns_to_postgresql.py` (already exists)

**Run**:
```bash
python scripts/migrate_patterns_to_postgresql.py \
  --sqlite-db pattern_library.db \
  --db-url $SPECQL_DB_URL \
  --mark-as-primitives

# Expected output:
🔄 Migrating patterns from SQLite to PostgreSQL...
📊 Found 25 patterns in SQLite

Migrating patterns:
  ✅ declare (primitive) → PostgreSQL
  ✅ assign (primitive) → PostgreSQL
  ✅ call_function (primitive) → PostgreSQL
  ✅ call_service (primitive) → PostgreSQL
  ... (21 more)

✅ Migrated 25 patterns successfully
📝 All patterns marked with source_type='language_primitive'

Verifying migration:
  PostgreSQL pattern count: 25
  All patterns have descriptions: ✅
  All patterns have categories: ✅

✅ Migration complete!
```

**Update Script** (add `--mark-as-primitives` flag):

```python
# scripts/migrate_patterns_to_postgresql.py
import argparse

def migrate_patterns(sqlite_db: str, db_url: str, mark_as_primitives: bool = False):
    """Migrate patterns from SQLite to PostgreSQL"""

    # Read from SQLite
    with sqlite3.connect(sqlite_db) as sqlite_conn:
        cur = sqlite_conn.cursor()
        cur.execute("SELECT * FROM patterns")
        patterns = cur.fetchall()

    # Write to PostgreSQL
    with psycopg.connect(db_url) as pg_conn:
        with pg_conn.cursor() as cur:
            for pattern in patterns:
                # Determine source_type
                source_type = 'language_primitive' if mark_as_primitives else 'manual'

                cur.execute("""
                    INSERT INTO pattern_library.tb_pattern
                    (name, category, description, source_type, ...)
                    VALUES (%s, %s, %s, %s, ...)
                    ON CONFLICT (name) DO UPDATE SET ...
                """, (pattern[1], pattern[2], pattern[4], source_type, ...))

            pg_conn.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlite-db', required=True)
    parser.add_argument('--db-url', required=True)
    parser.add_argument('--mark-as-primitives', action='store_true',
                       help='Mark patterns as language primitives')
    args = parser.parse_args()

    migrate_patterns(args.sqlite_db, args.db_url, args.mark_as_primitives)
```

**Deliverable**: 25 language primitives in PostgreSQL

---

### Phase 3: Clean Up Obsolete Files (15 minutes)

#### Task 3.1: Archive SQLite Databases

**Files to Archive**:
```
pattern_library.db (136 KB)
test_pattern_library.db (0 KB)
database/maestro_analytics.db (0 KB)
```

**Commands**:
```bash
# Create archive directory
mkdir -p archive/sqlite_databases/

# Move SQLite databases to archive
mv pattern_library.db archive/sqlite_databases/
mv test_pattern_library.db archive/sqlite_databases/
mv database/maestro_analytics.db archive/sqlite_databases/

# Add README
cat > archive/sqlite_databases/README.md <<EOF
# Archived SQLite Databases

**Date**: 2025-11-12
**Reason**: Migrated to PostgreSQL

## Files

- \`pattern_library.db\`: 25 language primitives (migrated to PostgreSQL)
- \`test_pattern_library.db\`: Empty test database
- \`maestro_analytics.db\`: Empty analytics database

## Migration

All data has been migrated to PostgreSQL database 'specql':
- Patterns → \`pattern_library.tb_pattern\`
- Analytics → (to be implemented in PostgreSQL)

These files are kept for historical reference only.
EOF

# Git operations
git add archive/sqlite_databases/
git rm pattern_library.db test_pattern_library.db database/maestro_analytics.db
git commit -m "chore: archive SQLite databases, migrate to PostgreSQL"
```

**Deliverable**: SQLite databases archived

---

#### Task 3.2: Clean Up Registry YAML

**Current State**:
```
registry/
└── archive/
    ├── domain_registry.yaml (already archived in Phase 4)
    ├── domain_registry.yaml.backup
    └── service_registry.yaml
```

**Action**: Leave as-is (already properly archived)

**Add Documentation**:
```bash
cat > registry/README.md <<EOF
# Registry Directory

**Status**: YAML registry ARCHIVED (Phase 4 complete)

## Current Architecture

Domain registry is now stored in **PostgreSQL**:
- Schema: \`specql_registry\`
- Tables: \`tb_domain\`, \`tb_subdomain\`, \`tb_entity_registration\`

## Archived Files

The \`archive/\` directory contains historical YAML files:
- \`domain_registry.yaml\` - Legacy domain registry (pre-PostgreSQL)
- \`service_registry.yaml\` - Legacy service registry

These files are kept for historical reference only.

## Usage

To manage domains, use the CLI:

\`\`\`bash
# Register new domain
specql domain register --number 2 --name crm --description "CRM"

# List domains
specql domain list

# Allocate entity code
specql domain allocate-code crm customer Contact
\`\`\`

All operations now use PostgreSQL as the source of truth.
EOF

git add registry/README.md
git commit -m "docs: document registry migration to PostgreSQL"
```

**Deliverable**: Registry directory documented

---

### Phase 4: Update Code References (30 minutes)

#### Task 4.1: Remove SQLite Pattern Repository

**Files to Update**:

1. **`src/infrastructure/repositories/sqlite_pattern_repository.py`**
   - **Action**: Move to archive
   ```bash
   mkdir -p archive/repositories/
   git mv src/infrastructure/repositories/sqlite_pattern_repository.py \
          archive/repositories/
   ```

2. **`src/pattern_library/api.py`**
   - **Remove**: SQLite references
   - **Keep**: PostgreSQL only

   ```python
   # OLD:
   def get_pattern_repository():
       """Get pattern repository (SQLite or PostgreSQL)"""
       if has_postgresql():
           return PostgreSQLPatternRepository(db_url)
       else:
           return SQLitePatternRepository('pattern_library.db')

   # NEW:
   def get_pattern_repository():
       """Get pattern repository (PostgreSQL)"""
       config = get_config()
       if config.database_url:
           return PostgreSQLPatternRepository(config.database_url)
       else:
           # For tests only
           return InMemoryPatternRepository()
   ```

3. **`src/application/services/pattern_service_factory.py`**
   - Already uses config-based selection
   - **No changes needed** ✅

**Deliverable**: SQLite references removed

---

#### Task 4.2: Update Documentation

**Files to Update**:

1. **`README.md`**
   ```markdown
   ## Data Storage

   SpecQL uses a clean two-tier storage architecture:

   ### 1. YAML Files (Entity Definitions)
   - **Location**: `entities/`, `stdlib/`
   - **Purpose**: Schema source code
   - **Version Control**: Git
   - **Usage**: Input to code generation

   ### 2. PostgreSQL (Runtime Data)
   - **Database**: `specql`
   - **Purpose**: All runtime data
   - **Schemas**:
     - `specql_registry`: Domain registry, entity tracking
     - `pattern_library`: Discovered patterns, embeddings
   - **Backup**: SQL dumps

   ### Setup

   \`\`\`bash
   # Set up PostgreSQL
   ./scripts/setup_database.sh

   # Set environment variable
   export SPECQL_DB_URL='postgresql://specql_user:specql_dev_password@localhost/specql'

   # Verify
   specql domain list
   \`\`\`
   ```

2. **`docs/architecture/CURRENT_STATUS.md`**
   - Update Phase 5 status to "Complete"
   - Add Phase 6 status: "Ready to start"

**Deliverable**: Documentation updated

---

### Phase 5: Initialize PostgreSQL with Data (45 minutes)

#### Task 5.1: Register Base Domains

**Script**: `scripts/initialize_domains.sh`

```bash
#!/bin/bash
# Initialize base domains in PostgreSQL

set -e

echo "🔄 Initializing base domains in PostgreSQL..."

# Core domains (1-9)
specql domain register --number 1 --name core \
  --description "Core framework and registry" \
  --multi-tenant false

specql domain register --number 2 --name crm \
  --description "Customer relationship management" \
  --multi-tenant true

specql domain register --number 3 --name commerce \
  --description "E-commerce and transactions" \
  --multi-tenant true

specql domain register --number 4 --name geo \
  --description "Geographic and location data" \
  --multi-tenant true

specql domain register --number 5 --name projects \
  --description "Project and task management" \
  --multi-tenant true

specql domain register --number 6 --name finance \
  --description "Financial data and accounting" \
  --multi-tenant true

specql domain register --number 7 --name hr \
  --description "Human resources" \
  --multi-tenant true

specql domain register --number 8 --name analytics \
  --description "Analytics and reporting" \
  --multi-tenant true

specql domain register --number 9 --name system \
  --description "System and infrastructure" \
  --multi-tenant false

echo "✅ Registered 9 base domains"

# Verify
echo ""
echo "📊 Current domains:"
specql domain list
```

**Run**:
```bash
chmod +x scripts/initialize_domains.sh
./scripts/initialize_domains.sh

# Expected output:
🔄 Initializing base domains in PostgreSQL...
✅ Registered domain: core (1)
✅ Registered domain: crm (2)
✅ Registered domain: commerce (3)
✅ Registered domain: geo (4)
✅ Registered domain: projects (5)
✅ Registered domain: finance (6)
✅ Registered domain: hr (7)
✅ Registered domain: analytics (8)
✅ Registered domain: system (9)
✅ Registered 9 base domains

📊 Current domains:
1 | core      | Core framework and registry
2 | crm       | Customer relationship management
3 | commerce  | E-commerce and transactions
4 | geo       | Geographic and location data
5 | projects  | Project and task management
6 | finance   | Financial data and accounting
7 | hr        | Human resources
8 | analytics | Analytics and reporting
9 | system    | System and infrastructure
```

**Deliverable**: 9 base domains registered

---

#### Task 5.2: Register Stdlib Entities

**Script**: `scripts/register_stdlib_entities.py`

```python
#!/usr/bin/env python3
"""
Register all stdlib entities to domains

Scans entities/ and stdlib/ directories and registers each entity
to its appropriate domain/subdomain.
"""
import yaml
from pathlib import Path
from src.application.services.domain_service_factory import get_domain_service
from src.core.entity_parser import EntityParser

def parse_entity_file(file_path: Path) -> dict:
    """Parse entity YAML file"""
    with open(file_path) as f:
        data = yaml.safe_load(f)
    return data

def get_domain_from_schema(schema: str) -> str:
    """Map schema to domain name"""
    # Map common schemas to domains
    schema_to_domain = {
        'crm': 'crm',
        'commerce': 'commerce',
        'ecommerce': 'commerce',
        'geo': 'geo',
        'location': 'geo',
        'projects': 'projects',
        'project': 'projects',
        'finance': 'finance',
        'accounting': 'finance',
        'hr': 'hr',
        'analytics': 'analytics',
        'system': 'system',
        'core': 'core',
    }
    return schema_to_domain.get(schema.lower(), 'core')

def register_entity(service, entity_data: dict, file_path: Path):
    """Register a single entity"""
    entity_name = entity_data.get('entity')
    schema = entity_data.get('schema', 'core')

    # Determine domain and subdomain
    domain_name = get_domain_from_schema(schema)
    subdomain_name = schema  # Use schema as subdomain for simplicity

    # Check if subdomain exists, create if needed
    try:
        domain = service.get_domain_by_name(domain_name)
        if subdomain_name not in [sd.subdomain_name for sd in domain.subdomains.values()]:
            # Add subdomain
            service.add_subdomain_to_domain(
                domain_name=domain_name,
                subdomain_number=str(len(domain.subdomains) + 1),
                subdomain_name=subdomain_name,
                description=f"Subdomain for {schema}"
            )
    except ValueError:
        print(f"⚠️  Domain {domain_name} not found, skipping {entity_name}")
        return

    # Allocate code
    try:
        code = service.allocate_entity_code(
            domain_name=domain_name,
            subdomain_name=subdomain_name,
            entity_name=entity_name
        )
        print(f"✅ {entity_name}: {code} (domain={domain_name}, subdomain={subdomain_name})")
        return code
    except Exception as e:
        print(f"❌ Failed to register {entity_name}: {e}")
        return None

def main():
    """Register all stdlib entities"""
    service = get_domain_service()

    # Find all entity files
    entity_dirs = [Path('entities'), Path('stdlib')]
    entity_files = []
    for entity_dir in entity_dirs:
        if entity_dir.exists():
            entity_files.extend(entity_dir.glob('**/*.yaml'))

    print(f"🔄 Found {len(entity_files)} entity files")
    print(f"📝 Registering entities...\n")

    registered = 0
    failed = 0

    for file_path in entity_files:
        try:
            entity_data = parse_entity_file(file_path)
            if register_entity(service, entity_data, file_path):
                registered += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            failed += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Registered: {registered}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Total: {len(entity_files)}")

if __name__ == '__main__':
    main()
```

**Run**:
```bash
python scripts/register_stdlib_entities.py

# Expected output:
🔄 Found 140 entity files
📝 Registering entities...

✅ Contact: 012301 (domain=crm, subdomain=crm)
✅ Company: 012302 (domain=crm, subdomain=crm)
✅ Lead: 012303 (domain=crm, subdomain=crm)
✅ Order: 032301 (domain=commerce, subdomain=commerce)
✅ Product: 032302 (domain=commerce, subdomain=commerce)
... (135 more)

📊 Summary:
   ✅ Registered: 138
   ❌ Failed: 2
   📈 Total: 140
```

**Deliverable**: All stdlib entities registered

---

### Phase 6: Verify and Test (30 minutes)

#### Task 6.1: Verification Script

**Script**: `scripts/verify_data_migration.py`

```python
#!/usr/bin/env python3
"""
Verify data migration is complete and correct
"""
import psycopg
from src.core.config import get_config

def verify_migration():
    """Verify all data is in PostgreSQL"""
    config = get_config()

    if not config.database_url:
        print("❌ SPECQL_DB_URL not set")
        return False

    with psycopg.connect(config.database_url) as conn:
        with conn.cursor() as cur:
            # Check domains
            cur.execute("SELECT COUNT(*) FROM specql_registry.tb_domain")
            domain_count = cur.fetchone()[0]
            print(f"✅ Domains: {domain_count} (expected: 9)")

            # Check subdomains
            cur.execute("SELECT COUNT(*) FROM specql_registry.tb_subdomain")
            subdomain_count = cur.fetchone()[0]
            print(f"✅ Subdomains: {subdomain_count}")

            # Check entities
            cur.execute("SELECT COUNT(*) FROM specql_registry.tb_entity_registration")
            entity_count = cur.fetchone()[0]
            print(f"✅ Registered entities: {entity_count} (expected: ~140)")

            # Check patterns
            cur.execute("SELECT COUNT(*) FROM pattern_library.tb_pattern")
            pattern_count = cur.fetchone()[0]
            print(f"✅ Patterns: {pattern_count} (expected: 25 language primitives)")

            # Check pattern source types
            cur.execute("""
                SELECT source_type, COUNT(*)
                FROM pattern_library.tb_pattern
                GROUP BY source_type
            """)
            for row in cur.fetchall():
                print(f"   - {row[0]}: {row[1]}")

            # Verify no SQLite references in code
            print("\n🔍 Checking for obsolete references...")

            # Check if SQLite files exist
            import os
            if os.path.exists('pattern_library.db'):
                print("⚠️  WARNING: pattern_library.db still exists (should be archived)")
            else:
                print("✅ SQLite databases archived")

            # Check if YAML registry exists
            if os.path.exists('registry/domain_registry.yaml'):
                print("⚠️  WARNING: registry/domain_registry.yaml still exists (should be archived)")
            else:
                print("✅ YAML registry archived")

            print("\n✅ Data migration verification complete!")
            return True

if __name__ == '__main__':
    verify_migration()
```

**Run**:
```bash
python scripts/verify_data_migration.py

# Expected output:
✅ Domains: 9 (expected: 9)
✅ Subdomains: 12
✅ Registered entities: 138 (expected: ~140)
✅ Patterns: 25 (expected: 25 language primitives)
   - language_primitive: 25

🔍 Checking for obsolete references...
✅ SQLite databases archived
✅ YAML registry archived

✅ Data migration verification complete!
```

**Deliverable**: Migration verified

---

#### Task 6.2: Integration Tests

**Test**: `tests/integration/test_data_consolidation.py`

```python
"""Integration tests for data consolidation"""
import pytest
from src.application.services.domain_service_factory import get_domain_service
from src.application.services.pattern_service_factory import get_pattern_service

def test_postgresql_is_primary():
    """Test PostgreSQL is primary repository"""
    from src.core.config import get_config
    config = get_config()

    assert config.database_url is not None
    assert config.repository_backend.value == 'postgresql'

def test_domains_in_postgresql():
    """Test domains are in PostgreSQL"""
    service = get_domain_service()
    domains = service.list_all_domains()

    assert len(domains) >= 9
    domain_names = [d.domain_name for d in domains]
    assert 'core' in domain_names
    assert 'crm' in domain_names

def test_entities_registered():
    """Test stdlib entities are registered"""
    service = get_domain_service()

    # Get CRM domain
    crm = service.get_domain_by_name('crm')
    assert crm is not None

    # Should have entities registered
    total_entities = sum(
        len(sd.entities)
        for sd in crm.subdomains.values()
    )
    assert total_entities > 0

def test_patterns_in_postgresql():
    """Test patterns are in PostgreSQL"""
    service = get_pattern_service()
    patterns = service.list_all_patterns()

    # Should have 25 language primitives
    assert len(patterns) >= 25

    # All should be marked as language primitives
    primitives = [p for p in patterns if p.source_type.value == 'language_primitive']
    assert len(primitives) == 25

def test_no_sqlite_repositories_in_use():
    """Test SQLite repositories are not in use"""
    from src.infrastructure.repositories import postgresql_pattern_repository
    from src.application.services import pattern_service

    # Pattern service should use PostgreSQL
    service = get_pattern_service()
    assert isinstance(service.repository, postgresql_pattern_repository.PostgreSQLPatternRepository)
```

**Run**:
```bash
pytest tests/integration/test_data_consolidation.py -v

# Expected output:
tests/integration/test_data_consolidation.py::test_postgresql_is_primary PASSED
tests/integration/test_data_consolidation.py::test_domains_in_postgresql PASSED
tests/integration/test_data_consolidation.py::test_entities_registered PASSED
tests/integration/test_data_consolidation.py::test_patterns_in_postgresql PASSED
tests/integration/test_data_consolidation.py::test_no_sqlite_repositories_in_use PASSED

======================== 5 passed in 1.23s ========================
```

**Deliverable**: All tests passing

---

## 📊 Summary: Before and After

### Before (Messy)

```
Data Storage: 3 formats

1. YAML (2 purposes, confused)
   - registry/domain_registry.yaml (runtime data in YAML ❌)
   - entities/*.yaml (schema definitions ✅)

2. SQLite (3 databases, 2 empty)
   - pattern_library.db (136 KB, 25 patterns)
   - test_pattern_library.db (empty)
   - maestro_analytics.db (empty)

3. PostgreSQL
   - Not set up
   - Code ready but unused

Problems:
❌ Multiple sources of truth
❌ Confusion between schema and data
❌ SQLite for patterns (wrong tool)
❌ Empty databases lying around
❌ PostgreSQL infrastructure unused
```

---

### After (Clean)

```
Data Storage: 2 clear purposes

1. YAML (Entity Definitions)
   Location: entities/, stdlib/
   Purpose: Schema source code
   Count: 140 files
   Version Control: Git
   Usage: specql generate input

2. PostgreSQL (Runtime Data)
   Database: specql
   Purpose: All runtime data
   Schemas:
     - specql_registry:
       * 9 domains
       * 12 subdomains
       * 138 registered entities
     - pattern_library:
       * 25 language primitives
       * Future: discovered patterns
   Version Control: SQL backups
   Usage: Application runtime

Benefits:
✅ Single source of truth per data type
✅ Clear separation of concerns
✅ PostgreSQL for all runtime data
✅ YAML only for schema definitions
✅ No confusion, no duplication
```

---

## ✅ Checklist: Execute in Order

### Phase 1: Set Up PostgreSQL
- [ ] Run `./scripts/setup_database.sh`
- [ ] Set `SPECQL_DB_URL` environment variable
- [ ] Verify connection works
- [ ] Update `src/core/config.py`

### Phase 2: Migrate Data
- [ ] Migrate 25 patterns from SQLite → PostgreSQL
- [ ] Mark patterns as `source_type='language_primitive'`
- [ ] Verify pattern count in PostgreSQL

### Phase 3: Clean Up Files
- [ ] Archive `pattern_library.db` → `archive/sqlite_databases/`
- [ ] Archive `test_pattern_library.db` → `archive/sqlite_databases/`
- [ ] Archive `maestro_analytics.db` → `archive/sqlite_databases/`
- [ ] Add README to archive directory
- [ ] Document registry directory
- [ ] Git commit: "chore: archive SQLite databases"

### Phase 4: Update Code
- [ ] Move `sqlite_pattern_repository.py` → `archive/repositories/`
- [ ] Update `src/pattern_library/api.py` (PostgreSQL only)
- [ ] Remove SQLite imports and references
- [ ] Update documentation (README, CURRENT_STATUS)
- [ ] Git commit: "refactor: remove SQLite references"

### Phase 5: Initialize Data
- [ ] Run `./scripts/initialize_domains.sh` (9 domains)
- [ ] Run `python scripts/register_stdlib_entities.py` (138 entities)
- [ ] Verify domain/entity counts
- [ ] Git commit: "feat: initialize PostgreSQL with domains and entities"

### Phase 6: Verify
- [ ] Run `python scripts/verify_data_migration.py`
- [ ] Run `pytest tests/integration/test_data_consolidation.py`
- [ ] Verify all tests pass
- [ ] Check no SQLite files in working directory
- [ ] Verify PostgreSQL is primary

---

## 🎯 Final State Verification

**Run This**:
```bash
# 1. Check environment
echo "SPECQL_DB_URL: ${SPECQL_DB_URL:-NOT SET}"

# 2. Check PostgreSQL
psql $SPECQL_DB_URL -c "
SELECT
    'Domains' as type, COUNT(*) as count
FROM specql_registry.tb_domain
UNION ALL
SELECT
    'Subdomains', COUNT(*)
FROM specql_registry.tb_subdomain
UNION ALL
SELECT
    'Entities', COUNT(*)
FROM specql_registry.tb_entity_registration
UNION ALL
SELECT
    'Patterns', COUNT(*)
FROM pattern_library.tb_pattern
"

# 3. Check file system
echo ""
echo "SQLite files in working directory:"
find . -name "*.db" -not -path "./archive/*" | wc -l
echo "(Should be 0)"

echo ""
echo "Archived SQLite files:"
ls archive/sqlite_databases/*.db | wc -l
echo "(Should be 3)"

# 4. Check CLI
specql domain list
specql patterns list
```

**Expected Output**:
```
SPECQL_DB_URL: postgresql://specql_user:specql_dev_password@localhost/specql

     type     | count
--------------+-------
 Domains      |     9
 Subdomains   |    12
 Entities     |   138
 Patterns     |    25

SQLite files in working directory:
0
(Should be 0)

Archived SQLite files:
3
(Should be 3)

Domains:
1 | core      | Core framework and registry
2 | crm       | Customer relationship management
3 | commerce  | E-commerce and transactions
... (6 more)

Patterns:
declare       | primitive       | language_primitive
assign        | primitive       | language_primitive
... (23 more)
```

---

## 📚 Documentation Updates

### Files to Update

1. **README.md** - Architecture section
2. **docs/architecture/CURRENT_STATUS.md** - Phase 5 complete
3. **docs/guides/GETTING_STARTED.md** - Setup instructions
4. **Contributing Guide** - Development setup

---

## 🎉 Success Criteria

After completion:

- ✅ **PostgreSQL** is the single source of truth for runtime data
- ✅ **YAML** is the single source of truth for schema definitions
- ✅ **No SQLite** databases in working directory
- ✅ **All tests** passing
- ✅ **9 domains** registered
- ✅ **138 entities** registered
- ✅ **25 patterns** migrated
- ✅ **Documentation** updated
- ✅ **Clean architecture** with clear separation

---

**Timeline**: 1-2 days
**Complexity**: Medium (mostly scripting)
**Risk**: Low (migration with backups)
**Priority**: High (cleans up technical debt)

---

*Two storage formats. Two clear purposes. No confusion.* 🎯
