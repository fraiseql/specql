# Cleanup Opportunities After Confiture v0.2.0 Integration

**Date**: November 9, 2025
**Context**: Confiture v0.2.0 now provides ALL features we requested, eliminating need for custom migration management code.

---

## 🎯 Executive Summary

**Confiture v0.2.0 eliminates ~700 lines of redundant code from Team E.**

### What Changed
- ✅ Confiture now has production-ready migration management
- ✅ Confiture handles versioning, tracking, rollback
- ✅ Confiture preserves SQL comments (FraiseQL blocker SOLVED)
- ✅ Confiture has Rust performance layer (10-50x speedup)

### Impact on Team E
- **Before**: Team E needed to build migration management from scratch (~1000 lines)
- **After**: Team E only writes SpecQL → Confiture glue (~300 lines)
- **Savings**: **70% code reduction**, **50% time reduction** (10 weeks → 2 weeks)

---

## 🗑️ Files to DELETE

### 1. **`src/cli/migration_manager.py`** (213 lines)

**Why Delete**: Confiture handles all migration tracking

**What it does** (now redundant):
```python
class MigrationManager:
    def track_applied_migrations()  # Confiture: migrate status
    def version_control()           # Confiture: automatic versioning
    def rollback_logic()            # Confiture: migrate down
    def state_persistence()         # Confiture: built-in tracking
```

**Replaced by**:
```bash
confiture migrate status   # Check migration state
confiture migrate up       # Apply migrations
confiture migrate down     # Rollback
```

**Action**:
```bash
git rm src/cli/migration_manager.py
git rm tests/unit/cli/test_migrate.py  # Related tests
```

---

### 2. **Custom Migration Tests** (related to migration_manager.py)

**Files to delete**:
- `tests/unit/cli/test_migrate.py` - Tests migration manager (redundant)
- Any tests in `test_orchestrator.py` that test migration numbering/versioning

**Why**: Confiture has 255 tests covering migration functionality

**Action**:
```bash
# Review and remove migration-specific tests
vim tests/unit/cli/test_orchestrator.py
# Keep: SpecQL → SQL generation tests
# Remove: Migration numbering, versioning, state tracking tests
```

---

## 🔧 Files to SIMPLIFY

### 3. **`src/cli/orchestrator.py`** (currently 10,162 bytes)

**What to remove**:

```python
# ❌ REMOVE: Custom migration numbering
def assign_migration_number(entity):
    """Confiture handles numbering automatically"""
    pass

# ❌ REMOVE: Custom file concatenation
def concatenate_sql_files(files):
    """Confiture handles concatenation"""
    pass

# ❌ REMOVE: Custom versioning logic
def generate_version_number():
    """Confiture handles versioning"""
    pass

# ❌ REMOVE: Migration file writing logic
def write_migration_file(number, name, content):
    """Just write to Confiture directories instead"""
    pass
```

**What to KEEP**:
```python
# ✅ KEEP: SpecQL parsing
def parse_specql_files(files):
    """This is SpecQL-specific"""
    pass

# ✅ KEEP: SQL generation coordination
def generate_from_files(entity_files):
    """Coordinate Teams A-D, write SQL to Confiture dirs"""
    pass

# ✅ KEEP: Registry integration
def register_entity(entity, table_code):
    """SpecQL registry is our concern, not Confiture's"""
    pass
```

**Estimated reduction**: ~400 lines → ~200 lines (50% smaller)

---

### 4. **`src/cli/generate.py`** (currently 3,724 bytes)

**What to simplify**:

```python
# ❌ REMOVE: Custom migration output logic
@click.option("--output-dir", default="migrations", ...)
def generate(..., output_dir):
    # Write to migrations/100_entity.sql
    pass

# ✅ REPLACE WITH: Confiture directory output
@click.option("--output-base", default="db/schema", ...)
def generate(..., output_base):
    # Write to db/schema/10_tables/entity.sql
    # Write to db/schema/30_functions/entity.sql
    # Write to db/schema/40_metadata/entity.sql
    pass
```

**What to ADD**:
```python
# ✅ ADD: Guidance for next steps
if result.success:
    click.echo("\n📋 Next steps:")
    click.echo("  1. confiture build --env local")
    click.echo("  2. confiture migrate up --env local")
```

---

### 5. **`src/cli/migrate.py`** (currently 3,314 bytes)

**Current state**: Custom migration execution logic

**New approach**: **Delegate to Confiture entirely**

**Option A**: Delete file, tell users to use `confiture migrate`
```bash
# Instead of: specql migrate up
# Users run:   confiture migrate up --env local
```

**Option B**: Thin wrapper around Confiture
```python
# src/cli/migrate.py (SIMPLIFIED)

import click
import subprocess

@click.command()
@click.argument("direction", type=click.Choice(["up", "down", "status"]))
@click.option("--env", default="local", help="Environment")
def migrate(direction: str, env: str):
    """
    Apply migrations (delegates to Confiture)

    This is a thin wrapper around 'confiture migrate'.
    For advanced options, use confiture directly.
    """
    subprocess.run(["confiture", "migrate", direction, "--env", env])
```

**Estimated reduction**: 3,314 bytes → ~500 bytes (if keeping wrapper)

**Recommendation**: **Delete entirely** and use Confiture directly

---

## 📝 Files to UPDATE

### 6. **`.claude/CLAUDE.md`** - Team E Section

**Current text** (lines 596-750):
```markdown
## Team E: CLI & Orchestration + Frontend Codegen

**Mission**: Developer tools + pipeline orchestration + frontend code generation

**CLI Commands**:
```bash
specql generate entities/contact.yaml
specql validate entities/*.yaml
specql migrate up  # Custom migration execution
specql migrate status  # Custom migration tracking
```

**Orchestration**: Coordinates Teams B + C + D + Migration Management
```

**New text** (REVISED):
```markdown
## Team E: CLI & Orchestration + Frontend Codegen

**Mission**: SpecQL → Confiture integration + frontend code generation

**Responsibilities**:
- ✅ SpecQL YAML → SQL file generation
- ✅ Write SQL to Confiture directory structure
- ✅ Registry integration (hexadecimal table codes)
- ✅ Frontend code generation (mutation impacts, TypeScript, hooks)
- ✅ SpecQL-specific validation

**NOT Responsible** (Confiture handles):
- ❌ Migration versioning/tracking
- ❌ SQL file concatenation
- ❌ Database connection management
- ❌ Migration execution/rollback

**CLI Commands**:
```bash
# Team E commands (SpecQL-specific)
specql generate entities/contact.yaml   # Generate SQL files
specql validate entities/*.yaml         # Validate SpecQL syntax
specql docs entities/*.yaml            # Generate documentation
specql diff contact_v1.yaml contact_v2.yaml  # Compare versions

# Confiture commands (migration management)
confiture build --env local            # Build combined migration
confiture migrate up --env local       # Apply migration
confiture migrate status               # Check migration state
confiture migrate down                 # Rollback
```

**Workflow**:
```
SpecQL YAML
    ↓ (Team E: generate)
db/schema/10_tables/entity.sql
db/schema/30_functions/entity.sql
db/schema/40_metadata/entity.sql
    ↓ (Confiture: build)
db/generated/schema_local.sql
    ↓ (Confiture: migrate)
PostgreSQL Database
```
```

---

### 7. **`README.md`** - Quick Start Section

**Add Confiture workflow**:

```markdown
## Quick Start

### 1. Generate Schema from SpecQL

```bash
# Write SpecQL YAML
cat > entities/contact.yaml << EOF
entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified)
EOF

# Generate SQL files
python -m src.cli.generate entities/contact.yaml

# Output:
#   db/schema/10_tables/contact.sql
#   db/schema/30_functions/contact.sql (if actions)
#   db/schema/40_metadata/contact.sql
```

### 2. Build & Apply with Confiture

```bash
# Build combined migration
uv run confiture build --env local

# Apply to database
uv run confiture migrate up --env local

# Verify
psql specql_local -c "\dt crm.*"
psql specql_local -c "\df crm.*"
```

### 3. Check Migration Status

```bash
confiture migrate status
# Shows: Applied migrations, pending migrations, database state
```
```

---

### 8. **`docs/teams/TEAM_E_CURRENT_STATE.md`**

**Update status table**:

```markdown
| Component | Status | Completeness | Notes |
|-----------|--------|--------------|-------|
| **CLI Entry Points** | Complete | 100% | `specql generate` working |
| **Migration Management** | Delegated | 100% | **Using Confiture** ✅ |
| **Frontend Codegen** | In Progress | 60% | Impacts + TypeScript |
| **Documentation** | Updated | 90% | Confiture integration docs |
```

**Add note**:
```markdown
## ⚠️ IMPORTANT: Migration Management Delegated to Confiture

As of November 9, 2025, Team E no longer implements custom migration management.

**Migration responsibilities now handled by Confiture v0.2.0**:
- ✅ Migration versioning
- ✅ State tracking
- ✅ Rollback support
- ✅ Transaction safety
- ✅ Database connection management

**Team E focuses on**:
- ✅ SpecQL → SQL generation
- ✅ Registry integration
- ✅ Frontend code generation
- ✅ SpecQL-specific validation

See: `docs/implementation-plans/TEAM_E_REVISED_PLAN_POST_CONFITURE.md`
```

---

### 9. **`pyproject.toml`** - Update Dependencies

**Add Confiture**:

```toml
[project.dependencies]
# ... existing dependencies ...
fraiseql-confiture = "^0.2.0"  # NEW: Migration management
```

**Update entry points**:

```toml
[project.scripts]
specql = "src.cli.generate:main"           # Keep
# specql-migrate = "src.cli.migrate:main"  # REMOVE (use confiture directly)
```

---

## 🏗️ New Files to CREATE

### 10. **`confiture.yaml`** (NEW - Configuration)

**Location**: Project root

**Content**:
```yaml
# Confiture Configuration for SpecQL
# See: https://github.com/fraiseql/confiture

environments:
  local:
    database_url: postgresql://localhost/specql_local
    schema_dirs:
      - path: db/schema/00_foundation
        order: 0
      - path: db/schema/10_tables
        order: 10
      - path: db/schema/30_functions
        order: 30
      - path: db/schema/40_metadata
        order: 40
    migrations_dir: db/migrations

  test:
    database_url: postgresql://localhost/specql_test
    schema_dirs:
      - path: db/schema/00_foundation
        order: 0
      - path: db/schema/10_tables
        order: 10
      - path: db/schema/30_functions
        order: 30
      - path: db/schema/40_metadata
        order: 40

  production:
    database_url: ${DATABASE_URL}
    schema_dirs:
      - path: db/schema/00_foundation
        order: 0
      - path: db/schema/10_tables
        order: 10
      - path: db/schema/30_functions
        order: 30
      - path: db/schema/40_metadata
        order: 40
```

---

### 11. **`docs/guides/CONFITURE_INTEGRATION.md`** (NEW - Documentation)

**Content**: Guide on how SpecQL uses Confiture

**Sections**:
1. Why Confiture?
2. Directory structure mapping
3. Workflow: SpecQL → Confiture → Database
4. Common commands
5. Troubleshooting

---

### 12. **`scripts/migrate_to_confiture.sh`** (NEW - Migration Script)

**Purpose**: Help existing users migrate from old flat structure to Confiture

**Content**:
```bash
#!/bin/bash
# Migrate from old migrations/ to Confiture db/schema/

# Create directory structure
mkdir -p db/schema/{00_foundation,10_tables,30_functions,40_metadata}

# Move existing migrations
# (Would need manual splitting of combined files)

echo "Migration to Confiture structure complete!"
echo "Next steps:"
echo "  1. Review files in db/schema/"
echo "  2. confiture build --env local"
echo "  3. confiture migrate up --env local"
```

---

## 📊 Impact Summary

### Code Reduction

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| `migration_manager.py` | 213 lines | 0 lines | 100% |
| `orchestrator.py` | ~400 lines | ~200 lines | 50% |
| `migrate.py` | 3,314 bytes | 0 bytes | 100% |
| Migration tests | ~500 lines | 0 lines | 100% |
| **Total** | **~1,400 lines** | **~200 lines** | **~86%** |

### Time Reduction

| Phase | Before | After | Savings |
|-------|--------|-------|---------|
| Migration system implementation | 4 weeks | 0 weeks | 100% |
| Testing migration system | 2 weeks | 0 weeks | 100% |
| Confiture integration | 0 weeks | 1 week | N/A |
| SpecQL-specific features | 4 weeks | 1 week | 75% |
| **Total** | **10 weeks** | **2 weeks** | **80%** |

### Risk Reduction

| Risk | Before | After |
|------|--------|-------|
| Custom migration bugs | HIGH | None (using battle-tested tool) |
| Maintenance burden | HIGH | LOW (external team maintains) |
| Production readiness | MEDIUM | HIGH (Confiture is production-ready) |
| Zero-downtime migrations | Not planned | Built-in (FDW) |
| Data sync | Not planned | Built-in (PII anonymization) |

---

## ✅ Action Plan

### **Phase 1: Install & Verify** (1 day)

```bash
# 1. Install Confiture
cd /home/lionel/code/printoptim_backend_poc
uv add fraiseql-confiture

# 2. Initialize
uv run confiture init

# 3. Verify comment preservation (P0 blocker)
echo "COMMENT ON TABLE test IS '@fraiseql:test';" > db/schema/10_tables/test.sql
uv run confiture build --env local --output test.sql
grep "@fraiseql:test" test.sql  # Should find it

# 4. Clean up test
rm db/schema/10_tables/test.sql test.sql
```

### **Phase 2: Delete Redundant Code** (1 day)

```bash
# Delete files
git rm src/cli/migration_manager.py
git rm tests/unit/cli/test_migrate.py

# Simplify files (manual editing)
vim src/cli/orchestrator.py  # Remove migration numbering logic
vim src/cli/generate.py      # Update for Confiture directories
vim src/cli/migrate.py       # DELETE or make thin wrapper

# Commit
git add -A
git commit -m "chore: Remove custom migration code, delegate to Confiture

Confiture v0.2.0 provides all migration management features:
- Migration versioning/tracking
- Rollback support
- Database connection management
- Zero-downtime migrations

Team E now focuses on SpecQL-specific features only.

Deleted:
- src/cli/migration_manager.py (213 lines)
- tests/unit/cli/test_migrate.py

Simplified:
- src/cli/orchestrator.py (~50% reduction)
- src/cli/generate.py (Confiture directory output)

See: docs/implementation-plans/TEAM_E_REVISED_PLAN_POST_CONFITURE.md
"
```

### **Phase 3: Create Confiture Integration** (2 days)

```bash
# 1. Create confiture.yaml
vim confiture.yaml  # See template above

# 2. Update orchestrator for Confiture output
vim src/cli/orchestrator.py
# Write to: db/schema/10_tables/entity.sql
#          db/schema/30_functions/entity.sql
#          db/schema/40_metadata/entity.sql

# 3. Test end-to-end
python -m src.cli.generate entities/examples/contact_lightweight.yaml
ls -R db/schema/  # Verify files created
uv run confiture build --env local
cat db/generated/schema_local.sql  # Verify combined schema

# 4. Commit
git add confiture.yaml db/schema/
git commit -m "feat: Integrate Confiture for migration management"
```

### **Phase 4: Update Documentation** (1 day)

```bash
# Update existing docs
vim .claude/CLAUDE.md           # Team E section
vim README.md                   # Quick start
vim docs/teams/TEAM_E_CURRENT_STATE.md

# Create new docs
vim docs/guides/CONFITURE_INTEGRATION.md

# Commit
git commit -m "docs: Update Team E documentation for Confiture integration"
```

---

## 🎯 Success Criteria

- [ ] Confiture v0.2.0 installed
- [ ] FraiseQL comment preservation verified (P0 blocker)
- [ ] `migration_manager.py` deleted
- [ ] `orchestrator.py` simplified (50% reduction)
- [ ] `confiture.yaml` created and tested
- [ ] End-to-end workflow works: SpecQL → Confiture → Database
- [ ] All documentation updated
- [ ] All tests passing (with migration tests removed)

---

## 📚 References

**Confiture**:
- Repository: `/home/lionel/code/confiture/`
- Changelog: Contains all v0.2.0 features
- Documentation: Production-ready guides

**SpecQL**:
- Old plan: `docs/teams/TEAM_E_CURRENT_STATE.md`
- New plan: `docs/implementation-plans/TEAM_E_REVISED_PLAN_POST_CONFITURE.md`
- Feature requests (now obsolete): `docs/implementation-plans/CONFITURE_FEATURE_REQUESTS.md`

---

**Status**: 🟢 READY TO EXECUTE
**Timeline**: 5 days
**Risk**: LOW (Confiture is production-ready)
**ROI**: HIGH (86% code reduction, 80% time savings)

---

*Last Updated*: November 9, 2025
*Author*: Claude Code
*Purpose*: Maximize value from Confiture v0.2.0 integration
