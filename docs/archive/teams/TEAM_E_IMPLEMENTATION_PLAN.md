# Team E: Detailed Implementation Plan - Confiture Integration

**Team**: CLI & Orchestration (Confiture-Based)
**Status**: 85% Complete (8 of 10 files)
**Timeline**: 2 Weeks (32-40 hours) - REDUCED from 4 weeks by using Confiture
**Last Updated**: 2025-11-09

---

## 🎯 Strategic Decision: Adopt Confiture as Migration Foundation

**Confiture** is a production-ready PostgreSQL migration tool (built for FraiseQL ecosystem) that provides:
- ✅ Build-from-DDL schema generation (<1 second)
- ✅ Migration tracking with Trinity pattern
- ✅ CLI framework (Typer + Rich output)
- ✅ Schema diff detection with Rust performance
- ✅ Multi-environment support
- ✅ 95% test coverage, battle-tested

**Decision**: Use Confiture's infrastructure, extend with SpecQL-specific orchestration.

**Time Saved**: 2 weeks (~40 hours) by not building generic migration infrastructure.

---

## 📊 Current Status: Team E is 85% Complete

**What exists:**
- ✅ `src/cli/generate.py` (139 lines) - Entity generation working
- ✅ `src/cli/validate.py` (80 lines) - SpecQL validation working
- ✅ `src/cli/orchestrator.py` (139 lines) - Pipeline orchestration working
- ✅ `src/cli/migration_manager.py` (214 lines) - Migration tracking (TO BE REPLACED by Confiture)
- ✅ `src/cli/migrate.py` (115 lines) - Migration commands (TO BE REPLACED by Confiture)
- ✅ `src/cli/diff.py` (129 lines) - SQL diff tool (TO BE ENHANCED with Confiture)
- ✅ `src/cli/docs.py` (225 lines) - Documentation generator
- ✅ All upstream dependencies (Teams A, B, C, D) complete and tested
- ✅ Comprehensive test suite (1,209 lines of tests!)

**What's missing:**
- ❌ Confiture integration and directory restructure
- ❌ Adapt orchestrator to write to `db/schema/` (not `migrations/`)
- ❌ Extend Confiture CLI with `specql` commands
- ⏸️ Frontend code generation (DEFERRED - out of scope for now)

---

## 🎯 Implementation Roadmap: 2 Weeks (Confiture Integration)

### **Week 1: Confiture Foundation & Directory Restructure** (Days 1-5)

#### Phase 1.1: Install Confiture & Verify Integration (Day 1)
**Objective**: Add Confiture dependency and verify it works

**Actions:**
1. **Add Confiture to project:**
   ```bash
   uv add fraiseql-confiture
   uv run confiture --version  # Verify installation
   ```

2. **Initialize Confiture structure:**
   ```bash
   uv run confiture init
   # Creates:
   # - db/schema/          (for DDL files)
   # - db/migrations/      (for Python migrations - optional)
   # - confiture.yaml      (environment config)
   ```

3. **Test Confiture with simple schema:**
   ```bash
   # Create test file
   echo "CREATE TABLE test_table (id INTEGER);" > db/schema/test.sql

   # Build schema
   uv run confiture build --env local

   # Verify it works
   ```

**QA Cycle:**
```bash
# Verify Confiture commands work
uv run confiture --help
uv run confiture build --help
uv run confiture migrate --help
```

---

#### Phase 1.2: Directory Restructure (Day 2 - REFACTOR)
**Objective**: Adapt existing code to write to `db/schema/` instead of `migrations/`

**New Directory Structure:**
```
db/
├── schema/                    # ← Confiture expects this
│   ├── 00_foundation/         # ← App foundation (000_app_foundation.sql)
│   ├── 10_tables/             # ← Team B output (entity schemas)
│   │   └── contact.sql        # ← One file per entity (table definition)
│   ├── 20_helpers/            # ← Utility functions (Trinity helpers)
│   │   └── contact_helpers.sql
│   └── 30_functions/          # ← Team C + Team D output (ONE FILE PER MUTATION)
│       ├── create_contact.sql           # ← app + core functions + FraiseQL COMMENT
│       ├── update_contact.sql           # ← app + core functions + FraiseQL COMMENT
│       └── qualify_lead.sql             # ← app + core functions + FraiseQL COMMENT
└── migrations/                # ← Confiture Python migrations (optional)

migrations/                    # ← OLD (to be removed after migration)
    ├── 000_app_foundation.sql
    ├── 100_contact.sql
    └── ...
```

**CRITICAL PATTERN**: Each mutation gets its **own SQL file** with **exactly 2 functions + FraiseQL comments**:
1. `app.{action_name}()` - App wrapper (JSONB → typed input, delegates to core)
2. `core.{action_name}()` - Core logic (business rules, validation, audit)
3. `COMMENT ON FUNCTION` statements - FraiseQL metadata (Team D) **IN SAME FILE**

**Changes to `orchestrator.py`:**
```python
# OLD:
output_path = Path(output_dir)  # "migrations/"
migration.path = output_path / f"{i:03d}_{entity.name.lower()}.sql"

# NEW:
schema_base = Path("db/schema")

# Foundation → db/schema/00_foundation/
foundation_path = schema_base / "00_foundation" / "app_foundation.sql"

# Tables → db/schema/10_tables/ (one file per entity)
table_path = schema_base / "10_tables" / f"{entity.name.lower()}.sql"

# Helpers → db/schema/20_helpers/ (Trinity helpers, shared utilities)
helpers_path = schema_base / "20_helpers" / f"{entity.name.lower()}_helpers.sql"

# Functions → db/schema/30_functions/ (ONE FILE PER MUTATION!)
for action in entity.actions:
    mutation_path = schema_base / "30_functions" / f"{action.name}.sql"
    # Contains: app.{action_name}() + core.{action_name}() + COMMENT statements
```

**Test Update:**
```bash
# Update tests to expect db/schema/ paths
uv run pytest tests/unit/cli/test_orchestrator.py -v
```

---

#### Phase 1.3: Adapt Schema Orchestrator to Split Output (Day 3 - GREEN)
**Objective**: Make Teams B/C/D write to separate files - **ONE FILE PER MUTATION**

**Files to modify:**
- `src/generators/schema_orchestrator.py`

**Current behavior (WRONG ❌):**
```python
# Generates one big SQL file with everything
def generate_complete_schema(entity) -> str:
    sql = []
    sql.append(self.table_generator.generate(entity))      # Team B
    sql.append(self.action_compiler.compile(entity.actions))  # Team C - ALL ACTIONS BUNDLED!
    sql.append(self.fraiseql_annotator.annotate(entity))  # Team D
    return "\n\n".join(sql)
```

**New behavior (CORRECT ✅) - Split by mutation:**
```python
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MutationFunctionPair:
    """One mutation = 2 functions + FraiseQL comments (ALL IN ONE FILE)"""
    action_name: str
    app_wrapper_sql: str         # app.{action_name}()
    core_logic_sql: str          # core.{action_name}()
    fraiseql_comments_sql: str   # COMMENT ON FUNCTION statements (Team D)

@dataclass
class SchemaOutput:
    """Split output for Confiture directory structure"""
    table_sql: str                           # → db/schema/10_tables/{entity}.sql (includes FraiseQL COMMENT)
    helpers_sql: str                         # → db/schema/20_helpers/{entity}_helpers.sql
    mutations: List[MutationFunctionPair]    # → db/schema/30_functions/{action_name}.sql (ONE FILE EACH!)

def generate_split_schema(entity) -> SchemaOutput:
    """
    Generate schema split by component

    CRITICAL: Each action generates a SEPARATE file with 2 functions + comments
    """
    # Team B: Table definition
    table_ddl = self.table_gen.generate_table_ddl(entity)

    # Team D: Table metadata (IN SAME FILE as table DDL)
    table_comments = self.fraiseql_annotator.annotate_table(entity)
    table_sql = f"{table_ddl}\n\n{table_comments}"

    # Team B: Helper functions (Trinity pattern utilities)
    helpers_sql = self.helper_gen.generate_all_helpers(entity)

    # Team C + Team D: ONE FILE PER MUTATION (app + core + comments)
    mutations = []
    for action in entity.actions:
        mutations.append(MutationFunctionPair(
            action_name=action.name,
            app_wrapper_sql=self.app_gen.generate_app_wrapper(entity, action),
            core_logic_sql=self.core_gen.generate_core_function(entity, action),
            fraiseql_comments_sql=self.fraiseql_annotator.annotate_mutation(action)
        ))

    return SchemaOutput(
        table_sql=table_sql,  # Includes FraiseQL comments
        helpers_sql=helpers_sql,
        mutations=mutations  # Each includes FraiseQL comments
    )
```

**Update orchestrator to write ONE FILE PER MUTATION:**
```python
# In orchestrator.py
schema_output = self.schema_orchestrator.generate_split_schema(entity)

# 1. Write table definition (ONE file per entity)
(schema_base / "10_tables" / f"{entity.name.lower()}.sql").write_text(schema_output.table_sql)

# 2. Write helper functions (ONE file per entity)
(schema_base / "20_helpers" / f"{entity.name.lower()}_helpers.sql").write_text(schema_output.helpers_sql)

# 3. Write mutation functions (ONE FILE PER MUTATION! ✅)
for mutation in schema_output.mutations:
    mutation_file = schema_base / "30_functions" / f"{mutation.action_name}.sql"

    # Each file contains EXACTLY 2 functions + FraiseQL comments:
    mutation_content = f"""
-- ============================================================================
-- Mutation: {mutation.action_name}
-- Entity: {entity.name}
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

{mutation.app_wrapper_sql}

{mutation.core_logic_sql}

{mutation.fraiseql_comments_sql}
"""
    mutation_file.write_text(mutation_content)
```

**Test:**
```bash
# Verify split output
uv run pytest tests/unit/cli/test_orchestrator.py::test_split_schema_output -v
```

#### Phase 1.4: Test Confiture Build (Day 4 - QA)
**Objective**: Verify Confiture can build from SpecQL output

**Actions:**
1. **Generate Contact entity to `db/schema/`:**
   ```bash
   python -m src.cli.generate entities entities/examples/contact.yaml
   # Should write to:
   # - db/schema/00_foundation/app_foundation.sql
   # - db/schema/10_tables/contact.sql
   # - db/schema/30_functions/contact_actions.sql
   # - db/schema/40_metadata/contact_fraiseql.sql
   ```

2. **Build with Confiture:**
   ```bash
   uv run confiture build --env local --output migrations/001_complete.sql
   # Confiture concatenates all db/schema/* files in deterministic order
   ```

3. **Verify output:**
   ```bash
   # Check that 001_complete.sql contains:
   # - Foundation types (from 00_foundation/)
   # - Contact table (from 10_tables/)
   # - Action functions (from 30_functions/)
   # - FraiseQL comments (from 40_metadata/)
   ```

**QA:**
```bash
# Run full test suite
uv run pytest tests/unit/cli/ -v

# Test end-to-end
uv run confiture build --env local
psql -f migrations/001_complete.sql  # Apply to test DB
```

---

#### Phase 1.5: Replace Migration Manager with Confiture (Day 5 - REFACTOR)
**Objective**: Remove custom migration tracking, use Confiture's

**Files to REMOVE:**
- ❌ `src/cli/migration_manager.py` (214 lines) - Replaced by Confiture
- ❌ `src/cli/migrate.py` (115 lines) - Replaced by Confiture

**What Confiture provides instead:**
```bash
# Confiture's migration commands (better than custom implementation!)
uv run confiture migrate up --env production
uv run confiture migrate down --steps 1
uv run confiture migrate status

# Uses confiture_migrations table (with Trinity pattern!)
# Transaction-safe, rollback support, better error handling
```

**Update documentation:**
```bash
# OLD:
specql migrate up --database-url=postgres://...

# NEW:
confiture migrate up --env production
```

**Test cleanup:**
```bash
# Remove tests for deleted files
rm tests/unit/cli/test_migration_manager.py
rm tests/unit/cli/test_migrate.py

# Run remaining tests
uv run pytest tests/unit/cli/ -v
```

---

### **Week 2: Extend Confiture CLI with SpecQL Commands** (Days 6-10)

#### Phase 2.1: Create SpecQL Extension Module (Day 6 - GREEN)
**Objective**: Extend Confiture's CLI with `specql` subcommands

**File to create:**
- `src/cli/confiture_extensions.py` (150 lines)

**Approach**: Add commands to Confiture's existing CLI

```python
# src/cli/confiture_extensions.py
from pathlib import Path
from typing import List
import click
from confiture.core.builder import SchemaBuilder
from src.cli.orchestrator import CLIOrchestrator

# Extend Confiture's CLI (if possible) or create parallel commands
@click.group()
def specql():
    """SpecQL commands for Confiture"""
    pass

@specql.command()
@click.argument('entity_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--foundation-only', is_flag=True, help='Generate only app foundation')
@click.option('--include-tv', is_flag=True, help='Generate table views')
def generate(entity_files: tuple, foundation_only: bool, include_tv: bool):
    """Generate PostgreSQL schema from SpecQL YAML files"""

    orchestrator = CLIOrchestrator()

    # Generate to db/schema/ (Confiture's expected location)
    result = orchestrator.generate_from_files(
        entity_files=list(entity_files),
        output_dir="db/schema",  # Changed from "migrations"
        foundation_only=foundation_only,
        include_tv=include_tv
    )

    if result.errors:
        click.secho(f"❌ {len(result.errors)} error(s):", fg='red')
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

    # Success - now build with Confiture
    click.secho(f"✅ Generated {len(result.migrations)} schema file(s)", fg='green')
    click.echo("\nBuilding final migration with Confiture...")

    # Use Confiture to build
    builder = SchemaBuilder(env="local")
    output_path = Path("migrations/001_schema.sql")
    builder.build(output_path=output_path)

    click.secho(f"✅ Complete! Migration written to: {output_path}", fg='green', bold=True)
    click.echo("\nNext steps:")
    click.echo("  1. Review: cat migrations/001_schema.sql")
    click.echo("  2. Apply: confiture migrate up --env local")

@specql.command()
@click.argument('entity_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--check-impacts', is_flag=True, help='Validate impact declarations')
@click.option('--verbose', '-v', is_flag=True)
def validate(entity_files: tuple, check_impacts: bool, verbose: bool):
    """Validate SpecQL entity files"""
    # Reuse existing validate.py logic
    from src.cli.validate import validate as validate_cmd
    ctx = click.get_current_context()
    ctx.invoke(validate_cmd, entity_files=entity_files,
               check_impacts=check_impacts, verbose=verbose)

if __name__ == '__main__':
    specql()
```

**Register with setuptools:**
```python
# pyproject.toml
[project.scripts]
specql = "src.cli.confiture_extensions:specql"
```

**Test:**
```bash
# New command structure
specql generate entities/examples/contact.yaml
specql validate entities/examples/*.yaml --verbose
```

---

#### Phase 2.2: Enhance Diff Command with Confiture (Day 7 - REFACTOR)
**Objective**: Use Confiture's schema differ (Rust-powered!)

**File to enhance:**
- ✅ `src/cli/diff.py` (keep, but enhance with Confiture integration)

**Current implementation:**
- Uses Python `difflib` for text comparison

**Enhanced with Confiture:**
```python
# src/cli/diff.py (enhanced)
from confiture.core.differ import SchemaDiffer  # Rust-powered!

@click.command()
@click.argument('entity_file', type=click.Path(exists=True))
@click.option('--compare', type=click.Path(), help='Compare against existing SQL')
@click.option('--use-rust', is_flag=True, default=True, help='Use Rust differ (faster)')
def diff(entity_file, compare, use_rust):
    """Show what would change if entity is generated"""

    # Generate in memory
    orchestrator = CLIOrchestrator()
    result = orchestrator.generate_from_files([entity_file], output_dir="/tmp")
    new_sql = result.migrations[0].content if result.migrations else ""

    # Load existing (if specified)
    old_sql = Path(compare).read_text() if compare else ""

    # Use Confiture's Rust differ if available
    if use_rust:
        try:
            differ = SchemaDiffer()
            changes = differ.compare(old_sql, new_sql)
            # Confiture provides structured diff (better than text diff)
            for change in changes:
                print_structured_change(change)
        except ImportError:
            # Fall back to Python difflib
            show_text_diff(old_sql, new_sql)
    else:
        show_text_diff(old_sql, new_sql)
```

**Benefit:** 10-50x faster diff detection with Confiture's Rust parser

---

#### Phase 2.3: Integrate Confiture Environment Config (Day 8 - GREEN)
**Objective**: Use Confiture's YAML config for multi-environment support

**File to create:**
- `confiture.yaml` (Confiture's config file)

**Example config:**
```yaml
# confiture.yaml
environments:
  local:
    database_url: postgresql://localhost/specql_local
    schema_dirs:
      - path: db/schema/00_foundation
        order: 0
      - path: db/schema/10_tables        # Table definitions (ONE file per entity)
        order: 10
      - path: db/schema/20_helpers       # Trinity helper functions
        order: 20
      - path: db/schema/30_functions     # Mutations (ONE file per mutation: app + core + COMMENT)
        order: 30
    migrations_dir: db/migrations

  test:
    database_url: postgresql://localhost/specql_test
    schema_dirs:
      - path: db/schema/00_foundation
        order: 0
      - path: db/schema/10_tables
        order: 10
      - path: db/schema/20_helpers
        order: 20
      - path: db/schema/30_functions
        order: 30

  production:
    database_url: ${DATABASE_URL}  # From environment variable
    schema_dirs:
      - path: db/schema/00_foundation
        order: 0
      - path: db/schema/10_tables
        order: 10
      - path: db/schema/20_helpers
        order: 20
      - path: db/schema/30_functions
        order: 30
```

**Usage:**
```bash
# Build for different environments
confiture build --env local
confiture build --env test
confiture build --env production

# Migrate different environments
confiture migrate up --env local
confiture migrate up --env production
```

**Benefit:** No more hardcoded database URLs, environment-specific behavior built-in

---

#### Phase 2.4: Integration Testing (Day 9 - QA)
**Objective**: End-to-end testing with Confiture

**File to create:**
- `tests/integration/test_confiture_integration.py` (200 lines)

**Test scenarios:**
```python
def test_generate_and_build_with_confiture():
    """Test full pipeline: SpecQL → db/schema/ → Confiture build"""
    # 1. Generate Contact entity
    result = subprocess.run([
        "specql", "generate", "entities/examples/contact.yaml"
    ], capture_output=True)
    assert result.returncode == 0

    # 2. Verify files in db/schema/
    assert Path("db/schema/00_foundation/app_foundation.sql").exists()
    assert Path("db/schema/10_tables/contact.sql").exists()

    # 3. Build with Confiture
    result = subprocess.run([
        "confiture", "build", "--env", "test", "--output", "migrations/001_test.sql"
    ], capture_output=True)
    assert result.returncode == 0

    # 4. Verify combined migration
    migration_sql = Path("migrations/001_test.sql").read_text()
    assert "CREATE TABLE crm.tb_contact" in migration_sql
    assert "CREATE FUNCTION crm.qualify_lead" in migration_sql
    assert "@fraiseql:type name=Contact" in migration_sql

def test_migrate_up_and_down():
    """Test Confiture migration commands"""
    # Apply migration
    result = subprocess.run([
        "confiture", "migrate", "up", "--env", "test"
    ], capture_output=True)
    assert result.returncode == 0

    # Verify table exists
    # ... (database check)

    # Rollback
    result = subprocess.run([
        "confiture", "migrate", "down", "--steps", "1", "--env", "test"
    ], capture_output=True)
    assert result.returncode == 0
```

**Run:**
```bash
uv run pytest tests/integration/test_confiture_integration.py -v
```

---

#### Phase 2.5: Documentation & Cleanup (Day 10 - QA)
**Objective**: Update all docs to reflect Confiture usage

**Files to update:**
1. `README.md` - New workflow with Confiture
2. `.claude/CLAUDE.md` - Update Team E section
3. `docs/cli/README.md` - Command reference
4. `CONTRIBUTING.md` - Development workflow

**Example README update:**
```markdown
# Quick Start

## Generate Schema from SpecQL

python
# 1. Write SpecQL YAML
cat > entities/contact.yaml << EOF
entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified)
EOF

# 2. Generate SQL files
specql generate entities/contact.yaml

# 3. Build final migration (Confiture)
confiture build --env local

# 4. Apply to database
confiture migrate up --env local


## Commands

- `specql generate` - Generate schema from SpecQL YAML
- `specql validate` - Validate SpecQL syntax
- `confiture build` - Build final migration from db/schema/
- `confiture migrate up` - Apply migrations
- `confiture migrate status` - Check migration status
```

**Cleanup:**
```bash
# Remove deprecated migration files
rm -rf migrations/  # Old location
git rm src/cli/migration_manager.py src/cli/migrate.py

# Update .gitignore
echo "migrations/*.sql" >> .gitignore  # Ignore generated migrations
echo "db/schema/**/*.sql" >> .gitignore  # Ignore generated schema files
```

---

## 📁 File Structure (Final State with Confiture)

```
src/cli/
├── __init__.py
├── generate.py (139 lines - ✅ EXISTS, to be updated)
├── validate.py (80 lines - ✅ EXISTS)
├── diff.py (129 lines - ✅ EXISTS, to be enhanced with Confiture)
├── docs.py (225 lines - ✅ EXISTS)
├── orchestrator.py (139 lines - ✅ EXISTS, to be updated for db/schema/)
├── confiture_extensions.py (150 lines - ❌ NEW, wraps existing commands)
├── migration_manager.py (214 lines - ❌ TO BE REMOVED, replaced by Confiture)
└── migrate.py (115 lines - ❌ TO BE REMOVED, replaced by Confiture)

db/
├── schema/                           # ← NEW: Confiture's expected structure
│   ├── 00_foundation/                # ← App foundation SQL
│   │   └── app_foundation.sql
│   ├── 10_tables/                    # ← Team B output (ONE FILE PER ENTITY)
│   │   ├── contact.sql               # ← Table definition for Contact
│   │   └── company.sql
│   ├── 20_helpers/                   # ← Utility functions (Trinity helpers)
│   │   ├── contact_helpers.sql       # ← Trinity functions for Contact
│   │   └── company_helpers.sql
│   └── 30_functions/                 # ← Team C + Team D output (ONE FILE PER MUTATION! ✅)
    ├── create_contact.sql        # ← app + core functions + FraiseQL COMMENT
    ├── update_contact.sql        # ← app + core functions + FraiseQL COMMENT
    ├── qualify_lead.sql          # ← app + core functions + FraiseQL COMMENT
    ├── create_company.sql
    └── update_company.sql
└── migrations/                       # ← Confiture Python migrations (optional)

confiture.yaml                        # ← NEW: Confiture config

tests/unit/cli/
├── conftest.py (65 lines - ✅ EXISTS)
├── test_generate.py (185 lines - ✅ EXISTS, to be updated)
├── test_validate.py (179 lines - ✅ EXISTS)
├── test_diff.py (184 lines - ✅ EXISTS)
├── test_docs.py (193 lines - ✅ EXISTS)
├── test_orchestrator.py (178 lines - ✅ EXISTS, to be updated)
├── test_migration_manager.py - ❌ TO BE REMOVED
├── test_migrate.py - ❌ TO BE REMOVED
└── test_confiture_extensions.py (150 lines - ❌ NEW)

tests/integration/
├── test_confiture_integration.py (200 lines - ❌ NEW)
└── test_cli_workflow.py - ✅ EXISTS (to be updated)
```

**Key Pattern (CRITICAL ✅)**:
- **10_tables/**: ONE file per entity (table DDL + FraiseQL COMMENT annotations)
- **20_helpers/**: ONE file per entity (Trinity helper functions)
- **30_functions/**: **ONE FILE PER MUTATION** containing exactly 2 functions + metadata:
  1. `app.{action_name}()` - App wrapper (JSONB → typed input)
  2. `core.{action_name}()` - Core business logic
  3. `COMMENT ON FUNCTION` statements - FraiseQL metadata (Team D) **IN SAME FILE**

**Code Changes Summary:**
- ✅ **Keep & Enhance**: ~940 lines (orchestrator, generate, validate, diff, docs)
- ❌ **Remove**: ~330 lines (migration_manager.py, migrate.py + tests)
- ❌ **Add New**: ~500 lines (confiture_extensions.py, integration tests, config)
- **Net Change**: +170 lines (vs -1,870 if we built from scratch!)

**Time Savings**: **2 weeks saved** by using Confiture infrastructure

---

## 🎯 Success Criteria (Confiture-Based)

### Week 1 (Confiture Foundation)
- [ ] Confiture dependency added and verified
- [ ] Directory restructure complete (`db/schema/` structure)
- [ ] Orchestrator writing to `db/schema/` directories
- [ ] Schema split by Team (tables/functions/metadata)
- [ ] Confiture can build from SpecQL output
- [ ] Migration tracking migrated to Confiture
- [ ] Old `migration_manager.py` and `migrate.py` removed
- [ ] Tests updated for new structure
- [ ] 85%+ Team E test coverage maintained

### Week 2 (SpecQL CLI Extension)
- [ ] `specql` CLI command wrapping Confiture
- [ ] `specql generate` working with Confiture build
- [ ] `specql validate` integrated
- [ ] `diff.py` enhanced with Confiture differ (optional Rust speedup)
- [ ] `confiture.yaml` config created with environments
- [ ] Integration tests with Confiture passing
- [ ] Documentation updated for Confiture workflow
- [ ] All examples work end-to-end
- [ ] 90%+ Team E test coverage

### Deferred (Future Work)
- ⏸️ Frontend code generation (separate project scope)
- ⏸️ Database-specific commands (deduplication, split entities, path validation)
- ⏸️ Advanced impact metadata features

---

## 🔧 Development Commands (Updated for Confiture)

```bash
# Run Team E tests only
make teamE-test

# Run specific test file
uv run pytest tests/unit/cli/test_orchestrator.py -v

# Test with coverage
uv run pytest tests/unit/cli/ --cov=src/cli --cov-report=html

# Test Confiture integration
uv run pytest tests/integration/test_confiture_integration.py -v

# Lint CLI code
uv run ruff check src/cli/

# Type checking
uv run mypy src/cli/

# Test new SpecQL commands
specql generate entities/examples/contact.yaml
specql validate entities/examples/*.yaml --verbose

# Test Confiture commands
uv run confiture build --env local
uv run confiture migrate status --env local
uv run confiture migrate up --env local

# Full quality check
make lint && make typecheck && make test
```

---

## 📊 Effort Estimate (Reduced with Confiture!)

| Week | Focus | Hours | Complexity | Notes |
|------|-------|-------|------------|-------|
| Week 1 | Confiture Foundation | 16-20 | MEDIUM | Directory restructure, remove old code |
| Week 2 | SpecQL CLI Extension | 16-20 | MEDIUM | Wrap Confiture, integrate commands |
| **TOTAL** | **2 weeks** | **32-40 hours** | **MEDIUM** | **50% reduction from original plan!** |

**Removed from scope (handled by Confiture):**
- ❌ Week 2 (Advanced CLI): 24-28 hours - Migration management now free
- ❌ Week 3 (Frontend Gen): 20-24 hours - Deferred to separate project
- ❌ Week 4 (Integration): 16-20 hours - Confiture has this built-in

**Total Time Saved**: **60-72 hours** (2.5 weeks)

---

## 🚀 Getting Started (Next Steps for Confiture Integration)

### Week 1 Day 1: Install Confiture

1. **Add Confiture dependency**:
   ```bash
   uv add fraiseql-confiture
   uv run confiture --version  # Verify installation
   ```

2. **Initialize Confiture structure**:
   ```bash
   uv run confiture init
   # Creates db/schema/, db/migrations/, confiture.yaml
   ```

3. **Test Confiture with simple schema**:
   ```bash
   echo "CREATE TABLE test (id INTEGER);" > db/schema/test.sql
   uv run confiture build --env local
   ```

### Week 1 Day 2: Directory Restructure

1. **Update orchestrator.py**:
   ```bash
   # Modify CLIOrchestrator.generate_from_files()
   # Change output_dir from "migrations/" to "db/schema/"
   # Split output by directory (00_foundation, 10_tables, etc.)
   ```

2. **Update tests**:
   ```bash
   # Update test expectations for new paths
   uv run pytest tests/unit/cli/test_orchestrator.py -v
   ```

### Week 1 Day 3-5: Split Output & Remove Old Code

1. **Modify schema_orchestrator.py**:
   ```bash
   # Add generate_split_schema() method
   # Return SchemaOutput with separate tables/functions/metadata SQL
   ```

2. **Remove old migration code**:
   ```bash
   git rm src/cli/migration_manager.py src/cli/migrate.py
   git rm tests/unit/cli/test_migration_manager.py tests/unit/cli/test_migrate.py
   ```

3. **Test end-to-end with Confiture**:
   ```bash
   specql generate entities/examples/contact.yaml
   uv run confiture build --env local
   ```

### Week 2: Extend Confiture CLI

1. **Create confiture_extensions.py**:
   ```bash
   # Implement specql CLI wrapping existing commands
   # Register in pyproject.toml
   ```

2. **Add confiture.yaml config**:
   ```bash
   # Configure environments (local, test, production)
   # Set schema_dirs with proper ordering
   ```

3. **Integration tests**:
   ```bash
   # Create test_confiture_integration.py
   # Test full pipeline: SpecQL → db/schema/ → Confiture build → migrate
   ```

4. **Update documentation**:
   ```bash
   # Update README.md, .claude/CLAUDE.md with new workflow
   # Document Confiture commands
   ```

---

## 🔗 Dependencies

**Depends On**:
- ✅ Team A: SpecQL Parser (COMPLETE)
- ✅ Team B: Schema Generator (COMPLETE)
- ✅ Team C: Action Compiler (COMPLETE)
- ✅ Team D: FraiseQL Metadata (COMPLETE)
- ❌ **Confiture**: External dependency (to be added)

**Blocks**:
- None (final integration layer)

**External Tools**:
- Confiture (fraiseql-confiture) - Production-ready migration tool
  - Repository: https://github.com/fraiseql/confiture
  - PyPI: https://pypi.org/project/fraiseql-confiture/
  - License: MIT
  - Status: Beta (v0.1.0), Production-Ready

---

## 📚 Related Documentation

**Team E Specific**:
- `/docs/teams/TEAM_E_CURRENT_STATE.md` - Detailed current state (outdated, needs update)
- `/docs/teams/TEAM_E_EXPLORATION_EXECUTIVE_SUMMARY.md` - Analysis summary
- `/docs/teams/TEAM_E_DATABASE_DECISIONS_PLAN.md` - Database-specific commands (deferred)

**Project Context**:
- `/.claude/CLAUDE.md` - Team E section (needs update for Confiture)
- `/src/cli/` - Current implementation (85% complete)
- `/tests/unit/cli/` - Comprehensive test suite (1,209 lines)

**Confiture Documentation** (External):
- Confiture README - Migration tool overview
- Confiture examples/ - Production deployment patterns
- Confiture docs/ - API reference

---

## 🎉 Summary: Why Confiture?

**Benefits**:
- ✅ **2 weeks saved** (60-72 hours) by not building migration infrastructure
- ✅ **Production features** free: Multi-environment, schema diff, rollback
- ✅ **Rust performance** when needed (10-50x faster)
- ✅ **Battle-tested** with 95% test coverage
- ✅ **Natural fit**: Built for FraiseQL (same ecosystem)
- ✅ **Focus on value**: Time saved goes to SpecQL-specific features

**Trade-offs**:
- ⚠️ External dependency (mitigated: MIT license, active development)
- ⚠️ Directory restructure (one-time cost: ~4 hours)
- ⚠️ Learning curve (mitigated: excellent docs, simple API)

**Net Result**:
- **Original Plan**: 4 weeks, 80-96 hours, build everything from scratch
- **Confiture Plan**: 2 weeks, 32-40 hours, leverage production tool
- **ROI**: 50% time reduction, 100% production-ready features

---

**Status**: 🟢 READY TO START (with Confiture integration plan)
**Priority**: HIGH (final integration layer)
**Effort**: 2 weeks (32-40 hours) - **REDUCED from 4 weeks!**
**Start Date**: TBD
**Target Completion**: TBD + 2 weeks
