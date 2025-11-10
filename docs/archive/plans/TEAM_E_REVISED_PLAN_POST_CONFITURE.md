# Team E Implementation Plan - Revised Post-Confiture v0.2.0

**Date**: November 9, 2025
**Status**: 🔄 REVISING - Confiture v0.2.0 Now Has All Requested Features!
**Previous Plan**: TEAM_E_IMPLEMENTATION_PLAN.md (pre-Confiture integration)
**Current Progress**: ~40% complete (CLI foundation done, orchestration partial)

---

## 🎉 **MAJOR UPDATE**: Confiture v0.2.0 Release

Confiture team has released v0.2.0 with **ALL features we requested**! This significantly simplifies Team E's work.

### ✅ What Confiture v0.2.0 Now Provides

From Confiture's CHANGELOG.md and README.md:

1. **✅ Production-Ready CI/CD Workflows**
   - Multi-platform wheel building (Linux, macOS, Windows)
   - PyPI Trusted Publishing
   - Quality gate with comprehensive checks
   - Python 3.11, 3.12, 3.13 support

2. **✅ Rust Performance Layer** (10-50x speedup)
   - Fast schema builder with parallel file I/O
   - Fast SHA256 hashing
   - Graceful fallback to Python

3. **✅ 4 Migration Strategies** (All Complete!)
   - Medium 1: Build from DDL (fresh databases <1s)
   - Medium 2: Incremental migrations (ALTER)
   - Medium 3: Production data sync with PII anonymization
   - Medium 4: Zero-downtime via FDW

4. **✅ Comment Preservation** (P0 Blocker - SOLVED!)
   - All SQL comments preserved byte-for-byte
   - `COMMENT ON` statements preserved
   - FraiseQL `@fraiseql:*` comments work perfectly

5. **✅ File Ordering** (Handles our hex codes!)
   - Deterministic alphabetical ordering within directories
   - Works with hexadecimal prefixes (012A31 < 01F231) ✅

6. **✅ Migration Management**
   - Migration versioning and tracking
   - Rollback support
   - Transaction safety
   - State persistence

---

## 🧹 What We Can REMOVE/Simplify

### ❌ **Remove**: Custom Migration Manager

**File to DELETE**: `src/cli/migration_manager.py` (213 lines)

**Why**: Confiture already has comprehensive migration tracking, versioning, rollback, and state management.

**What we had**:
```python
# src/cli/migration_manager.py (NO LONGER NEEDED)
class MigrationManager:
    def track_applied_migrations()
    def version_control()
    def rollback_logic()
    def state_persistence()
```

**Replaced by**:
```bash
# Confiture built-in commands
confiture migrate up           # Apply migrations
confiture migrate down         # Rollback
confiture migrate status       # Check state
confiture migrate generate     # Create new migration
```

---

### ❌ **Remove**: Custom Build Logic

**What we had planned**: Custom schema concatenation, file ordering, hash computation

**Replaced by**: Confiture's Rust-powered schema builder (10-50x faster!)

**What to delete**:
- Custom file discovery logic (Confiture handles this)
- Custom SQL concatenation (Confiture handles this)
- Custom ordering logic (Confiture handles this)

---

### ❌ **Remove**: Custom Database Connection Pooling

**What we had planned**: psycopg connection management in CLI

**Replaced by**: Confiture's built-in database connection handling

---

### ✅ **Keep & Enhance**: SpecQL-Specific Features

What Team E STILL needs to do (Confiture doesn't handle SpecQL-specific concerns):

1. **Registry Integration** (SpecQL-specific)
   - Map registry hexadecimal codes to Confiture directory structure
   - Validate table codes match registry
   - Auto-register entities during generation

2. **Frontend Code Generation** (SpecQL-specific)
   - `mutation-impacts.json` generation
   - TypeScript type definitions
   - Apollo/React hooks
   - Mutation documentation

3. **CLI User Experience** (SpecQL-specific)
   - `specql generate` command (orchestrates Teams A-D + Confiture)
   - `specql validate` command (SpecQL syntax + registry validation)
   - `specql docs` command (generate mutation docs)
   - `specql diff` command (compare SpecQL versions)

4. **Integration Glue** (SpecQL → Confiture)
   - Convert SpecQL entities → SQL files in Confiture format
   - Map registry layers to Confiture directories
   - Pass generated SQL to Confiture for building

---

## 📋 Revised Implementation Plan

### **Week 1: Cleanup & Confiture Integration** (5 days)

#### **Day 1: Remove Redundant Code**

**Objective**: Delete/deprecate code that Confiture now handles

**Tasks**:
1. **Delete** `src/cli/migration_manager.py` (213 lines)
   - Confiture handles all migration tracking
   - Delete tests: `tests/unit/cli/test_migrate.py`

2. **Simplify** `src/cli/orchestrator.py`
   - Remove custom file concatenation logic
   - Remove custom migration numbering
   - Keep only: SpecQL parsing + SQL generation

3. **Deprecate** custom build logic in favor of Confiture

**Tests to Update**:
```bash
# Remove obsolete tests
rm tests/unit/cli/test_migrate.py
rm -rf tests related to migration_manager.py

# Update orchestrator tests
vim tests/unit/cli/test_orchestrator.py
# Focus on: SpecQL → SQL generation (not migration management)
```

**Estimated Time**: 4 hours

---

#### **Day 2: Install & Configure Confiture**

**Objective**: Add Confiture as dependency and configure for SpecQL

**Tasks**:

1. **Install Confiture**:
```bash
cd /home/lionel/code/printoptim_backend_poc
uv add fraiseql-confiture
```

2. **Initialize Confiture**:
```bash
uv run confiture init
# Creates: db/environments/, db/schema/, db/migrations/
```

3. **Create `confiture.yaml`**:
```yaml
# confiture.yaml
environments:
  local:
    database_url: postgresql://localhost/specql_local
    schema_dirs:
      # Foundation (from Team B)
      - path: db/schema/00_foundation
        order: 0

      # Tables (from registry layer 01_write_side)
      - path: db/schema/10_tables
        order: 10

      # Functions (from registry layer 03_functions)
      - path: db/schema/30_functions
        order: 30

      # FraiseQL Metadata (Team D annotations)
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
    migrations_dir: db/migrations

  production:
    database_url: ${DATABASE_URL}  # Environment variable
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
```

4. **Create directory structure**:
```bash
mkdir -p db/schema/{00_foundation,10_tables,30_functions,40_metadata}
mkdir -p db/migrations
```

5. **Test Confiture**:
```bash
# Create test schema file
echo "CREATE TABLE test (id INTEGER);" > db/schema/10_tables/test.sql

# Build schema
uv run confiture build --env local --output db/generated/schema_local.sql

# Verify
cat db/generated/schema_local.sql
# Should contain: CREATE TABLE test (id INTEGER);
```

**Estimated Time**: 3 hours

---

#### **Day 3: Update Orchestrator for Confiture Output**

**Objective**: Make `CLIOrchestrator` write SQL files in Confiture format

**File to Modify**: `src/cli/orchestrator.py`

**Current Behavior** (Team E has this):
```python
# Writes to: migrations/100_contact.sql (flat, single file)
```

**New Behavior** (write to Confiture directories):
```python
# Writes to:
# - db/schema/10_tables/contact.sql         (Team B DDL)
# - db/schema/30_functions/contact.sql      (Team C actions)
# - db/schema/40_metadata/contact.sql       (Team D FraiseQL)
```

**Implementation**:

```python
# src/cli/orchestrator.py (REVISED)

from pathlib import Path
from typing import List
from dataclasses import dataclass

from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator

@dataclass
class GenerationResult:
    """Result of generation process"""
    generated_files: List[Path]
    errors: List[str]
    warnings: List[str]

class CLIOrchestrator:
    """
    Orchestrate SpecQL → SQL generation for Confiture

    Responsibilities:
    - Parse SpecQL YAML files
    - Generate SQL via Teams A-D
    - Write SQL to Confiture directory structure
    - Register entities in domain registry

    NOT Responsible For (Confiture handles):
    - Migration numbering/versioning
    - File concatenation
    - Database connection
    - Migration execution
    """

    def __init__(self, use_registry: bool = True):
        self.parser = SpecQLParser()
        self.schema_orchestrator = SchemaOrchestrator()
        self.use_registry = use_registry

        if use_registry:
            from src.generators.schema.naming_conventions import NamingConventions
            self.naming = NamingConventions()

    def generate_from_files(
        self,
        entity_files: List[str],
        output_base: str = "db/schema",
        with_impacts: bool = False
    ) -> GenerationResult:
        """
        Generate SQL files from SpecQL YAML in Confiture format

        Args:
            entity_files: List of SpecQL YAML file paths
            output_base: Base directory for Confiture schema (default: db/schema)
            with_impacts: Generate impact metadata for frontend

        Returns:
            GenerationResult with list of created files
        """
        result = GenerationResult(
            generated_files=[],
            errors=[],
            warnings=[]
        )

        # Parse all SpecQL files
        entity_defs = []
        for entity_file in entity_files:
            try:
                content = Path(entity_file).read_text()
                entity_def = self.parser.parse(content)
                entity_defs.append(entity_def)
            except Exception as e:
                result.errors.append(f"Parse error in {entity_file}: {e}")

        # Generate SQL for each entity
        for entity_def in entity_defs:
            try:
                from src.cli.generate import convert_entity_definition_to_entity
                entity = convert_entity_definition_to_entity(entity_def)

                # Generate split schema (tables/functions/metadata)
                schema_output = self.schema_orchestrator.generate_split_schema(entity)

                # Determine output paths (Confiture directories)
                entity_name = entity.name.lower()

                # 1. Tables (db/schema/10_tables/entity.sql)
                table_file = Path(output_base) / "10_tables" / f"{entity_name}.sql"
                table_file.parent.mkdir(parents=True, exist_ok=True)
                table_file.write_text(schema_output.tables_sql)
                result.generated_files.append(table_file)

                # 2. Functions (db/schema/30_functions/entity.sql)
                if schema_output.functions_sql:
                    functions_file = Path(output_base) / "30_functions" / f"{entity_name}.sql"
                    functions_file.parent.mkdir(parents=True, exist_ok=True)
                    functions_file.write_text(schema_output.functions_sql)
                    result.generated_files.append(functions_file)

                # 3. Metadata (db/schema/40_metadata/entity.sql)
                if schema_output.metadata_sql:
                    metadata_file = Path(output_base) / "40_metadata" / f"{entity_name}.sql"
                    metadata_file.parent.mkdir(parents=True, exist_ok=True)
                    metadata_file.write_text(schema_output.metadata_sql)
                    result.generated_files.append(metadata_file)

                # Register in domain registry (if using registry)
                if self.use_registry and self.naming:
                    table_code = self.naming.derive_table_code(entity)
                    self.naming.register_entity_auto(entity, table_code)

            except Exception as e:
                result.errors.append(f"Generation error for {entity_def.name}: {e}")

        return result
```

**Test**:
```bash
uv run pytest tests/unit/cli/test_orchestrator.py -v
```

**Estimated Time**: 4 hours

---

#### **Day 4: Update `specql generate` CLI Command**

**Objective**: Simplify CLI command to use Confiture

**File to Modify**: `src/cli/generate.py`

**New Workflow**:
```
User runs: specql generate entities contact.yaml

Step 1: SpecQL → SQL (via CLIOrchestrator)
  → Writes: db/schema/10_tables/contact.sql
  → Writes: db/schema/30_functions/contact.sql
  → Writes: db/schema/40_metadata/contact.sql

Step 2: Confiture builds migration (automatic via confiture.yaml)
  → User runs: confiture build --env local
  → Confiture reads db/schema/**/*.sql
  → Confiture writes: db/generated/schema_local.sql

Step 3: User applies migration
  → confiture migrate up --env local
```

**Implementation**:

```python
# src/cli/generate.py (REVISED)

import click
from pathlib import Path
from src.cli.orchestrator import CLIOrchestrator

@click.group()
def cli():
    """SpecQL - Business DSL → PostgreSQL + GraphQL"""
    pass

@cli.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output-base", default="db/schema", help="Base directory for Confiture schema")
@click.option("--with-impacts", is_flag=True, help="Generate impact metadata for frontend")
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation")
def generate(
    entity_files: tuple,
    output_base: str,
    with_impacts: bool,
    foundation_only: bool
):
    """
    Generate SQL schema from SpecQL YAML files

    Writes SQL to Confiture directory structure:
      - db/schema/10_tables/*.sql
      - db/schema/30_functions/*.sql
      - db/schema/40_metadata/*.sql

    Next steps:
      1. Build migration: confiture build --env local
      2. Apply migration: confiture migrate up --env local
    """
    if foundation_only:
        # Generate app foundation only
        from src.generators.schema_orchestrator import SchemaOrchestrator
        orchestrator = SchemaOrchestrator()
        foundation_sql = orchestrator.generate_app_foundation_only()

        output = Path(output_base) / "00_foundation" / "app_foundation.sql"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(foundation_sql)

        click.secho(f"✅ Generated: {output}", fg="green")
        return 0

    # Generate entities
    orchestrator = CLIOrchestrator(use_registry=True)
    result = orchestrator.generate_from_files(
        entity_files=list(entity_files),
        output_base=output_base,
        with_impacts=with_impacts
    )

    # Report results
    if result.errors:
        click.secho(f"❌ {len(result.errors)} error(s):", fg="red", bold=True)
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

    click.secho(
        f"✅ Generated {len(result.generated_files)} SQL file(s)",
        fg="green",
        bold=True
    )
    click.echo("\nGenerated files:")
    for file in result.generated_files:
        click.echo(f"  {file}")

    if result.warnings:
        click.secho(f"\n⚠️  {len(result.warnings)} warning(s):", fg="yellow")
        for warning in result.warnings:
            click.echo(f"  {warning}")

    # Next steps
    click.echo("\n📋 Next steps:")
    click.echo("  1. Build migration:  confiture build --env local")
    click.echo("  2. Apply migration:  confiture migrate up --env local")
    click.echo("  3. Check status:     confiture migrate status")

    return 0


if __name__ == "__main__":
    cli()
```

**Test**:
```bash
# Generate Contact entity
python -m src.cli.generate entities/examples/contact_lightweight.yaml

# Should create:
# - db/schema/10_tables/contact.sql
# - db/schema/30_functions/contact.sql (if actions exist)
# - db/schema/40_metadata/contact.sql

# Build with Confiture
uv run confiture build --env local --output db/generated/schema_local.sql

# Verify combined schema
cat db/generated/schema_local.sql
```

**Estimated Time**: 3 hours

---

#### **Day 5: End-to-End Integration Test**

**Objective**: Verify complete pipeline works

**Test Scenario**:
```bash
# 1. Generate app foundation
python -m src.cli.generate --foundation-only

# 2. Generate entities
python -m src.cli.generate \
  entities/examples/contact_lightweight.yaml \
  entities/examples/company_lightweight.yaml

# 3. Verify Confiture structure
ls -R db/schema/
# Should show:
#   00_foundation/app_foundation.sql
#   10_tables/contact.sql
#   10_tables/company.sql
#   30_functions/contact.sql (if actions)
#   40_metadata/contact.sql

# 4. Build with Confiture
uv run confiture build --env test --output db/generated/test.sql

# 5. Verify combined schema
grep "CREATE TABLE crm.tb_contact" db/generated/test.sql
grep "CREATE FUNCTION crm.qualify_lead" db/generated/test.sql
grep "@fraiseql:type name=Contact" db/generated/test.sql

# 6. Apply to test database
createdb specql_test
uv run confiture migrate up --env test

# 7. Verify database
psql specql_test -c "\dt crm.*"
psql specql_test -c "\df crm.*"
psql specql_test -c "SELECT obj_description('crm.tb_contact'::regclass)"
```

**Create Integration Test**:

```python
# tests/integration/test_specql_confiture_pipeline.py

import subprocess
from pathlib import Path
import pytest

def test_full_specql_to_confiture_pipeline(tmp_path):
    """
    Test complete pipeline:
    SpecQL YAML → SQL files → Confiture → Database
    """
    # Setup
    output_base = tmp_path / "db" / "schema"

    # Step 1: Generate SQL from SpecQL
    result = subprocess.run([
        "python", "-m", "src.cli.generate",
        "entities/examples/contact_lightweight.yaml",
        "--output-base", str(output_base)
    ], capture_output=True, text=True)

    assert result.returncode == 0

    # Verify SQL files created
    assert (output_base / "10_tables" / "contact.sql").exists()
    assert (output_base / "40_metadata" / "contact.sql").exists()

    # Step 2: Build with Confiture
    # (Would require Confiture config and database for full test)
    # For now, verify file structure is correct

    table_sql = (output_base / "10_tables" / "contact.sql").read_text()
    assert "CREATE TABLE crm.tb_contact" in table_sql

    metadata_sql = (output_base / "40_metadata" / "contact.sql").read_text()
    assert "@fraiseql:type name=Contact" in metadata_sql


def test_confiture_preserves_fraiseql_comments():
    """Critical: Verify Confiture preserves @fraiseql comments"""

    # This was P0 blocker - now SOLVED by Confiture v0.2.0
    # Test to verify it works as documented

    test_sql = """
    COMMENT ON TABLE crm.tb_contact IS
      '@fraiseql:type name=Contact,schema=crm';
    """

    test_file = Path("db/schema/10_tables/test.sql")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(test_sql)

    # Build with Confiture
    result = subprocess.run([
        "confiture", "build", "--env", "test",
        "--output", "db/generated/test.sql"
    ], capture_output=True, text=True)

    assert result.returncode == 0

    # Verify comment preserved
    output = Path("db/generated/test.sql").read_text()
    assert "@fraiseql:type name=Contact" in output

    # Cleanup
    test_file.unlink()
```

**Estimated Time**: 4 hours

---

### **Week 2: Frontend Code Generation** (5 days)

Now that migration handling is delegated to Confiture, focus on SpecQL-specific features.

#### **Day 6-7: Mutation Impacts Generator**

**New Directory**: `src/generators/frontend/`

**Files to Create**:

1. `src/generators/frontend/mutation_impacts_generator.py` (150 lines)
2. `src/generators/frontend/typescript_types_generator.py` (200 lines)
3. `src/generators/frontend/apollo_hooks_generator.py` (250 lines)
4. `src/generators/frontend/mutation_docs_generator.py` (150 lines)

**Implementation**: Follow original TEAM_E plan for frontend codegen (unchanged)

**Estimated Time**: 12 hours (2 days)

---

#### **Day 8: Validate Command**

**File**: `src/cli/validate.py`

**Purpose**: Validate SpecQL syntax + registry consistency

**Implementation**:

```python
# src/cli/validate.py (REVISED - Remove Confiture overlap)

import click
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema.naming_conventions import NamingConventions

@click.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True))
@click.option("--check-registry", is_flag=True, help="Validate against domain registry")
def validate(entity_files: tuple, check_registry: bool):
    """
    Validate SpecQL YAML files

    Checks:
    - YAML syntax
    - Required fields
    - Type correctness
    - Registry conflicts (if --check-registry)

    Does NOT check:
    - SQL syntax (Confiture handles this)
    - Migration conflicts (Confiture handles this)
    """
    parser = SpecQLParser()
    errors = []

    # Parse and validate each file
    for file_path in entity_files:
        try:
            content = Path(file_path).read_text()
            entity_def = parser.parse(content)

            # SpecQL-specific validation
            if not entity_def.name:
                errors.append(f"{file_path}: Missing entity name")

            if not entity_def.fields:
                errors.append(f"{file_path}: Entity has no fields")

        except Exception as e:
            errors.append(f"{file_path}: {e}")

    # Registry validation
    if check_registry:
        naming = NamingConventions()
        # Check for conflicts, duplicate codes, etc.
        # (Existing registry validation logic)

    # Report
    if errors:
        click.secho(f"❌ {len(errors)} error(s) found:", fg="red")
        for error in errors:
            click.echo(f"  {error}")
        return 1
    else:
        click.secho(f"✅ All {len(entity_files)} file(s) valid", fg="green")
        return 0
```

**Estimated Time**: 3 hours

---

#### **Day 9: Docs Command**

**File**: `src/cli/docs.py`

**Purpose**: Generate mutation documentation from SpecQL

**Implementation**: Use existing `docs.py` (already created by Team E!)

**Estimated Time**: 2 hours (review + enhance existing)

---

#### **Day 10: Diff Command**

**File**: `src/cli/diff.py`

**Purpose**: Compare SpecQL file versions

**Implementation**: Use existing `diff.py` (already created by Team E!)

**Estimated Time**: 2 hours (review + enhance existing)

---

## 📊 Revised Success Criteria

### Week 1: Cleanup & Confiture Integration ✅
- [ ] Removed `migration_manager.py` (redundant with Confiture)
- [ ] Confiture v0.2.0 installed and configured
- [ ] `confiture.yaml` created with proper directory mapping
- [ ] `CLIOrchestrator` writes SQL to Confiture directories
- [ ] End-to-end test: SpecQL → Confiture → Database works
- [ ] FraiseQL comments preserved (verified)

### Week 2: SpecQL-Specific Features ✅
- [ ] Frontend code generation (impacts, types, hooks, docs)
- [ ] `specql validate` command works
- [ ] `specql docs` command enhanced
- [ ] `specql diff` command enhanced
- [ ] All CLI commands tested
- [ ] Documentation updated

---

## 🎯 Key Architectural Changes

### **Before Confiture Integration** (Old Plan)

```
SpecQL YAML
    ↓
Team A: Parser
    ↓
Team B/C/D: Generators
    ↓
Team E: Custom Migration Manager ❌ (213 lines we wrote)
    ↓
Team E: Custom SQL Builder ❌ (file concatenation)
    ↓
Team E: Custom Versioning ❌ (numbering logic)
    ↓
Team E: Custom Database Connection ❌ (psycopg pooling)
    ↓
PostgreSQL
```

**Total Team E Code**: ~1000 lines of migration management

---

### **After Confiture Integration** (New Plan)

```
SpecQL YAML
    ↓
Team A: Parser
    ↓
Team B/C/D: Generators
    ↓
Team E: Write SQL to Confiture directories ✅ (simple!)
    ↓
Confiture: Build + Migrate + Version + Track ✅ (external tool)
    ↓
PostgreSQL
```

**Total Team E Code**: ~300 lines (SpecQL → Confiture glue)

**Code Reduction**: **~70% less code** for Team E!

---

## 🔄 Migration Path

### For Existing Generated Migrations

**Old structure**:
```
migrations/
├── 000_app_foundation.sql
├── 100_contact.sql
└── 200_table_views.sql
```

**New structure**:
```
db/schema/
├── 00_foundation/
│   └── app_foundation.sql
├── 10_tables/
│   ├── contact.sql
│   └── company.sql
├── 30_functions/
│   └── contact.sql
└── 40_metadata/
    ├── contact.sql
    └── company.sql
```

**Migration Script**:
```bash
# scripts/migrate_to_confiture.sh

# 1. Create Confiture directory structure
mkdir -p db/schema/{00_foundation,10_tables,30_functions,40_metadata}

# 2. Move existing migrations
# (Manual - need to split combined files into separate layers)

# 3. Initialize Confiture
uv run confiture init

# 4. Build from new structure
uv run confiture build --env local

# 5. Verify identical output
diff migrations/combined_old.sql db/generated/schema_local.sql
```

---

## 📚 Updated Documentation Needed

### Files to Update:

1. **`.claude/CLAUDE.md`** - Team E section
   - Update to reflect Confiture delegation
   - Remove migration management details
   - Focus on SpecQL-specific features

2. **`README.md`** - Quick start
   - Update workflow: `specql generate` → `confiture build` → `confiture migrate`

3. **`docs/teams/TEAM_E_CURRENT_STATE.md`**
   - Mark migration management as "Delegated to Confiture"
   - Update completeness percentages

4. **New**: `docs/guides/CONFITURE_INTEGRATION.md`
   - How Confiture works with SpecQL
   - Directory mapping
   - Common workflows

---

## 🎉 Benefits of Confiture Integration

### **1. Code Reduction**
- **Before**: ~1000 lines of migration management
- **After**: ~300 lines of SpecQL → Confiture glue
- **Savings**: 70% less code to maintain

### **2. Production-Ready Features**
- ✅ Zero-downtime migrations (FDW)
- ✅ Production data sync with PII anonymization
- ✅ Multi-platform support (Linux, macOS, Windows)
- ✅ Rust performance (10-50x speedup)
- ✅ Comprehensive testing (255 tests, 89% coverage)

### **3. CI/CD Integration**
- ✅ Quality gate workflows
- ✅ Trusted publishing to PyPI
- ✅ Security scanning (Bandit, Trivy)

### **4. Focus on SpecQL Value**
Team E can now focus on:
- Frontend code generation (our moat!)
- SpecQL-specific validation
- Business logic → SQL transformation
- GraphQL integration

### **5. External Maintenance**
- Confiture team handles migration system updates
- We benefit from their improvements
- Professional support from FraiseQL ecosystem

---

## 🚨 Risk Mitigation

### **Risk**: Dependency on External Tool

**Mitigation**:
1. Confiture is **production-ready** (v0.2.0, 89% test coverage)
2. Part of **FraiseQL ecosystem** (professional maintenance)
3. **MIT license** (can fork if needed)
4. **Open source** (can contribute features)

### **Risk**: Breaking Changes in Confiture

**Mitigation**:
1. Pin to specific version: `fraiseql-confiture==0.2.0`
2. Test upgrades in isolated environment
3. Our code is abstracted (minimal coupling)

### **Risk**: Missing SpecQL-Specific Features

**Mitigation**:
1. Registry integration is **ours** (not Confiture's concern)
2. Frontend codegen is **ours** (SpecQL-specific)
3. SpecQL syntax validation is **ours**
4. Clear separation of concerns

---

## 📅 Revised Timeline

### **Week 1: Cleanup & Integration** (Nov 9-15)
- Day 1: Remove redundant code (4h)
- Day 2: Install & configure Confiture (3h)
- Day 3: Update orchestrator for Confiture (4h)
- Day 4: Update CLI commands (3h)
- Day 5: Integration tests (4h)

**Total**: 18 hours (2.5 days @ 8h/day)

### **Week 2: SpecQL Features** (Nov 16-22)
- Day 6-7: Frontend code generation (12h)
- Day 8: Validate command (3h)
- Day 9: Docs command enhancement (2h)
- Day 10: Diff command enhancement (2h)
- Buffer: Documentation + polish (3h)

**Total**: 22 hours (3 days @ 8h/day)

### **Grand Total**: 40 hours (5 days)

**Previous Estimate**: 10 weeks (80 hours)
**New Estimate**: 2 weeks (40 hours)
**Time Saved**: 40 hours (50%!)

---

## ✅ Action Items

### **Immediate** (Today)
1. ✅ Review Confiture v0.2.0 changelog (DONE)
2. ✅ Update Team E plan (THIS DOCUMENT)
3. [ ] Install Confiture: `uv add fraiseql-confiture`
4. [ ] Create test configuration
5. [ ] Verify comment preservation (P0 blocker test)

### **Week 1** (Nov 9-15)
1. [ ] Delete `migration_manager.py`
2. [ ] Create `confiture.yaml`
3. [ ] Update `orchestrator.py` for Confiture output
4. [ ] Update `generate.py` CLI
5. [ ] End-to-end test

### **Week 2** (Nov 16-22)
1. [ ] Frontend code generation
2. [ ] CLI command enhancements
3. [ ] Documentation updates
4. [ ] Final testing

---

## 📖 References

**Confiture Documentation**:
- Repository: `/home/lionel/code/confiture/`
- Changelog: `/home/lionel/code/confiture/CHANGELOG.md`
- README: `/home/lionel/code/confiture/README.md`
- Claude Guide: `/home/lionel/code/confiture/CLAUDE.md`

**SpecQL Documentation**:
- Feature Requests (now obsolete): `docs/implementation-plans/CONFITURE_FEATURE_REQUESTS.md`
- Registry Integration: `docs/implementation-plans/REGISTRY_CLI_CONFITURE_INTEGRATION.md`
- Old Plan: `docs/teams/TEAM_E_CURRENT_STATE.md`

---

**Status**: 🟢 READY TO START
**Confidence**: HIGH (Confiture solves all blockers)
**Timeline**: 2 weeks (down from 10!)
**Next Action**: Install Confiture and verify comment preservation

---

*Last Updated*: November 9, 2025
*Revised By*: Claude Code
*Reason*: Confiture v0.2.0 release with all requested features
