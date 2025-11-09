# Registry + CLI + Confiture Integration - Phased Implementation Plan

**Objective**: Integrate the existing hexadecimal registry system with Team E's CLI orchestrator and Confiture migration tool

**Current State**:
- ✅ Hexadecimal registry system fully implemented (`naming_conventions.py`, `domain_registry.yaml`)
- ✅ CLI orchestrator working with flat `migrations/` directory
- ❌ No integration between registry and CLI
- ❌ Confiture not yet adopted

**Target State**:
- ✅ CLI generates files using registry's hierarchical structure
- ✅ Confiture builds from hierarchical `db/schema/` directories
- ✅ Hexadecimal table codes enforced across the pipeline
- ✅ Automatic directory creation based on registry

**Timeline**: 2 weeks (10 working days)
**Approach**: TDD with RED → GREEN → REFACTOR → QA cycles

---

## 📊 Overview: Three Systems to Integrate

```
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 1: Registry (Hexadecimal Naming)                        │
│  ✅ COMPLETE                                                     │
│  - naming_conventions.py (795 lines)                            │
│  - domain_registry.yaml (312 lines)                             │
│  - 63 tests (100% passing)                                      │
│  Generates: generated/migrations/01_write_side/012_crm/...      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (INTEGRATE)
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 2: CLI Orchestrator                                     │
│  ✅ 85% COMPLETE                                                │
│  - orchestrator.py (139 lines)                                  │
│  - generate.py (139 lines)                                      │
│  - Tests: 1,209 lines                                           │
│  Generates: migrations/100_contact.sql (flat)                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (INTEGRATE)
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 3: Confiture Migration Tool                             │
│  ❌ NOT INTEGRATED                                              │
│  - External tool (production-ready)                             │
│  - Expects: db/schema/ hierarchy                                │
│  - Builds: Final migrations from multiple directories           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Integration Goals

### Phase 1: Registry → CLI (Days 1-3)
Connect `NamingConventions` to `CLIOrchestrator` so generated files use hexadecimal codes and hierarchical paths

### Phase 2: Dual-Mode Output (Days 4-5)
Support BOTH hierarchical (registry) and flat (Confiture) output formats

### Phase 3: Confiture Integration (Days 6-8)
Adopt Confiture for migration building and execution

### Phase 4: CLI Enhancement (Days 9-10)
Add registry-aware commands and validation

---

## 📅 Detailed Implementation Timeline

---

## 🔴 Phase 1: Registry Integration with CLI (Days 1-3)

### **Objective**: Make CLI orchestrator use registry's hexadecimal naming and hierarchical structure

---

### **Day 1: Registry Adapter Layer** (RED → GREEN)

#### RED: Write Failing Tests

```python
# tests/unit/cli/test_registry_integration.py

import pytest
from pathlib import Path
from src.cli.orchestrator import CLIOrchestrator
from src.core.ast_models import Entity, Field

def test_orchestrator_uses_registry_table_codes():
    """Orchestrator should derive table codes from registry"""
    orchestrator = CLIOrchestrator(use_registry=True)

    # Create test entity
    entity = Entity(name="Contact", schema="crm", fields=[])

    # Generate should use registry to get table code
    table_code = orchestrator.get_table_code(entity)

    # Should be hexadecimal, 6 chars
    assert len(table_code) == 6
    assert all(c in '0123456789ABCDEF' for c in table_code.upper())

def test_orchestrator_generates_hierarchical_paths():
    """Orchestrator should generate hierarchical file paths"""
    orchestrator = CLIOrchestrator(use_registry=True)

    entity = Entity(name="Contact", schema="crm", fields=[])
    table_code = "012311"

    # Should generate multi-level path
    file_path = orchestrator.generate_file_path(entity, table_code)

    # Should have hierarchy: layer/domain/subdomain/group/file
    parts = Path(file_path).parts
    assert len(parts) >= 5
    assert "01_write_side" in parts
    assert any("012_crm" in p for p in parts)

def test_orchestrator_creates_directories():
    """Orchestrator should create all required directories"""
    orchestrator = CLIOrchestrator(use_registry=True)

    entity = Entity(name="Contact", schema="crm", fields=[])

    result = orchestrator.generate_from_files(
        ["entities/contact.yaml"],
        output_dir="test_output"
    )

    # Should create hierarchical directories
    assert Path("test_output/01_write_side").exists()
    assert Path("test_output/01_write_side/012_crm").exists()
```

**Run:**
```bash
uv run pytest tests/unit/cli/test_registry_integration.py -v
# Expected: FAILED (orchestrator doesn't have registry integration yet)
```

---

#### GREEN: Minimal Implementation

**File to modify**: `src/cli/orchestrator.py`

```python
# src/cli/orchestrator.py (enhanced)

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator
from src.generators.schema.naming_conventions import NamingConventions  # NEW
from src.core.ast_models import EntityDefinition

@dataclass
class MigrationFile:
    """Represents a generated migration file"""
    number: int  # Kept for backward compatibility
    name: str
    content: str
    path: Optional[Path] = None
    table_code: Optional[str] = None  # NEW: Hexadecimal table code

@dataclass
class GenerationResult:
    """Result of generation process"""
    migrations: List[MigrationFile]
    errors: List[str]
    warnings: List[str]

class CLIOrchestrator:
    """Orchestrate all Teams for CLI commands"""

    def __init__(self, use_registry: bool = False):
        self.parser = SpecQLParser()
        self.schema_orchestrator = SchemaOrchestrator()

        # NEW: Registry integration
        self.use_registry = use_registry
        if use_registry:
            self.naming = NamingConventions()
        else:
            self.naming = None

    def get_table_code(self, entity) -> str:
        """
        Derive table code from registry

        Returns:
            6-character hexadecimal table code (e.g., "012311")
        """
        if not self.use_registry or not self.naming:
            raise ValueError("Registry not enabled. Use CLIOrchestrator(use_registry=True)")

        return self.naming.derive_table_code(entity)

    def generate_file_path(
        self,
        entity,
        table_code: str,
        file_type: str = "table",
        base_dir: str = "generated/migrations"
    ) -> str:
        """
        Generate file path (registry-aware or legacy flat)

        Args:
            entity: Entity AST model
            table_code: 6-digit hexadecimal table code
            file_type: Type of file ('table', 'function', 'comment')
            base_dir: Base directory for output

        Returns:
            File path (hierarchical if registry enabled, flat otherwise)
        """
        if self.use_registry and self.naming:
            # Use registry's hierarchical path
            return self.naming.generate_file_path(
                entity=entity,
                table_code=table_code,
                file_type=file_type,
                base_dir=base_dir
            )
        else:
            # Legacy flat path
            return str(Path(base_dir) / f"{table_code}_{entity.name.lower()}.sql")

    def generate_from_files(
        self,
        entity_files: List[str],
        output_dir: str = "migrations",
        with_impacts: bool = False,
        include_tv: bool = False,
        foundation_only: bool = False
    ) -> GenerationResult:
        """
        Generate migrations from SpecQL files (registry-aware)

        When use_registry=True:
        - Derives hexadecimal table codes
        - Creates hierarchical directory structure
        - Registers entities in domain_registry.yaml

        When use_registry=False:
        - Uses legacy flat numbering (000, 100, 200)
        - Single directory output
        """
        result = GenerationResult(migrations=[], errors=[], warnings=[])

        # Parse all entities
        entity_defs = []
        for entity_file in entity_files:
            try:
                content = Path(entity_file).read_text()
                entity_def = self.parser.parse(content)
                entity_defs.append(entity_def)
            except Exception as e:
                result.errors.append(f"Failed to parse {entity_file}: {e}")

        # Generate entity migrations
        for entity_def in entity_defs:
            try:
                from src.cli.generate import convert_entity_definition_to_entity
                entity = convert_entity_definition_to_entity(entity_def)

                if self.use_registry:
                    # Registry-based generation
                    table_code = self.get_table_code(entity)

                    # Generate schema
                    migration_sql = self.schema_orchestrator.generate_complete_schema(entity)

                    # Hierarchical file path
                    file_path = self.generate_file_path(
                        entity=entity,
                        table_code=table_code,
                        file_type="table",
                        base_dir=output_dir
                    )

                    # Create all parent directories
                    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

                    migration = MigrationFile(
                        number=int(table_code, 16),  # Convert hex to decimal for sorting
                        name=entity.name.lower(),
                        content=migration_sql,
                        path=Path(file_path),
                        table_code=table_code
                    )

                    # Register entity in domain registry
                    self.naming.register_entity_auto(entity, table_code)

                else:
                    # Legacy flat generation (current behavior)
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)

                    migration_sql = self.schema_orchestrator.generate_complete_schema(entity)

                    # Use sequential numbering
                    entity_number = 100 + len(result.migrations)

                    migration = MigrationFile(
                        number=entity_number,
                        name=entity.name.lower(),
                        content=migration_sql,
                        path=output_path / f"{entity_number:03d}_{entity.name.lower()}.sql"
                    )

                result.migrations.append(migration)

            except Exception as e:
                result.errors.append(f"Failed to generate {entity_def.name}: {e}")

        # Write migrations to disk
        for migration in result.migrations:
            if migration.path:
                migration.path.write_text(migration.content)

        return result
```

**Run:**
```bash
uv run pytest tests/unit/cli/test_registry_integration.py -v
# Expected: PASSED (basic integration working)
```

---

#### REFACTOR: Clean Up

**Refactoring checklist**:
- ✅ Extract directory creation to helper method
- ✅ Add type hints
- ✅ Add docstrings
- ✅ Handle edge cases (entity without schema, invalid table codes)

---

#### QA: Full Testing

```bash
# Test registry integration
uv run pytest tests/unit/cli/test_registry_integration.py -v

# Test backward compatibility (legacy mode)
uv run pytest tests/unit/cli/test_orchestrator.py -v

# Full test suite
uv run pytest tests/unit/cli/ -v

# Lint
uv run ruff check src/cli/orchestrator.py
```

---

### **Day 2: Update CLI Commands** (GREEN → REFACTOR)

#### Objective: Add `--use-registry` flag to CLI commands

**File to modify**: `src/cli/generate.py`

```python
# src/cli/generate.py (enhanced)

import click
from pathlib import Path
from src.cli.orchestrator import CLIOrchestrator

@click.command()
@click.argument("subcommand", type=click.Choice(["entities"]))
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output-dir", default="migrations", help="Output directory")
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation")
@click.option("--include-tv", is_flag=True, help="Generate table views")
@click.option("--use-registry", is_flag=True, help="Use hexadecimal registry for table codes and paths")  # NEW
def generate(
    subcommand: str,
    entity_files: tuple,
    output_dir: str,
    foundation_only: bool,
    include_tv: bool,
    use_registry: bool  # NEW
):
    """Generate PostgreSQL migrations from SpecQL YAML files"""

    if subcommand != "entities":
        click.secho(f"Unknown subcommand: {subcommand}", fg="red")
        return 1

    # Create orchestrator with registry support
    orchestrator = CLIOrchestrator(use_registry=use_registry)

    # Generate migrations
    result = orchestrator.generate_from_files(
        entity_files=list(entity_files),
        output_dir=output_dir,
        foundation_only=foundation_only,
        include_tv=include_tv
    )

    # Report results
    if result.errors:
        click.secho(f"❌ {len(result.errors)} error(s):", fg="red", bold=True)
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

    if use_registry:
        click.secho(
            f"✅ Generated {len(result.migrations)} file(s) with hexadecimal codes",
            fg="green",
            bold=True
        )

        # Show hierarchical structure
        click.echo("\nGenerated files:")
        for migration in result.migrations:
            click.echo(f"  [{migration.table_code}] {migration.path}")
    else:
        click.secho(
            f"✅ Generated {len(result.migrations)} migration(s)",
            fg="green",
            bold=True
        )

    if result.warnings:
        click.secho(f"\n⚠️  {len(result.warnings)} warning(s):", fg="yellow")
        for warning in result.warnings:
            click.echo(f"  {warning}")

    return 0
```

**Test:**
```bash
# Legacy mode (flat structure)
python -m src.cli.generate entities entities/examples/contact.yaml --output-dir test_legacy
# → test_legacy/100_contact.sql

# Registry mode (hierarchical structure)
python -m src.cli.generate entities entities/examples/contact.yaml --output-dir test_registry --use-registry
# → test_registry/01_write_side/012_crm/0123_customer/01231_contact_group/012311_tb_contact.sql
```

---

### **Day 3: Split Schema Output by Component** (REFACTOR)

#### Objective: Generate separate files for tables, functions, metadata

**Current behavior**: One SQL file with everything combined
**Target behavior**: Separate files for Team B (tables), Team C (functions), Team D (metadata)

**File to modify**: `src/generators/schema_orchestrator.py`

```python
# src/generators/schema_orchestrator.py (enhanced)

from dataclasses import dataclass
from typing import Optional

@dataclass
class SchemaOutput:
    """Split output for registry-based generation"""
    tables_sql: str        # Team B output
    functions_sql: str     # Team C output
    metadata_sql: str      # Team D output

class SchemaOrchestrator:
    """Orchestrate schema generation across Teams B, C, D"""

    def __init__(self):
        # Existing initialization
        self.table_generator = TableGenerator()
        self.action_compiler = ActionCompiler()
        self.fraiseql_annotator = FraiseQLAnnotator()

    def generate_complete_schema(self, entity) -> str:
        """
        Generate complete schema (legacy - all in one file)

        DEPRECATED: Use generate_split_schema() for registry mode
        """
        sql = []
        sql.append(self.table_generator.generate(entity))

        if entity.actions:
            sql.append(self.action_compiler.compile(entity.actions))

        sql.append(self.fraiseql_annotator.annotate(entity))

        return "\n\n".join(sql)

    def generate_split_schema(self, entity) -> SchemaOutput:
        """
        Generate schema split by component (for registry mode)

        Returns:
            SchemaOutput with separate tables/functions/metadata SQL
        """
        # Team B: Tables
        tables_sql = self.table_generator.generate(entity)

        # Team C: Functions
        functions_sql = ""
        if entity.actions:
            functions_sql = self.action_compiler.compile(entity.actions)

        # Team D: Metadata
        metadata_sql = self.fraiseql_annotator.annotate(entity)

        return SchemaOutput(
            tables_sql=tables_sql,
            functions_sql=functions_sql,
            metadata_sql=metadata_sql
        )
```

**Update orchestrator to use split output:**

```python
# src/cli/orchestrator.py (enhanced for split output)

def generate_from_files(self, entity_files, output_dir="migrations", ...):
    # ... (entity parsing) ...

    for entity_def in entity_defs:
        entity = convert_entity_definition_to_entity(entity_def)

        if self.use_registry:
            # Get table code
            table_code = self.get_table_code(entity)

            # Generate SPLIT schema
            schema_output = self.schema_orchestrator.generate_split_schema(entity)

            # Write to separate files using registry paths

            # 1. Tables (layer 01)
            table_path = self.naming.generate_file_path(
                entity, table_code, file_type="table", base_dir=output_dir
            )
            Path(table_path).parent.mkdir(parents=True, exist_ok=True)
            Path(table_path).write_text(schema_output.tables_sql)

            # 2. Functions (layer 03)
            if schema_output.functions_sql:
                # Derive function code from table code (change layer to 03)
                function_code = self.naming.derive_function_code(table_code)
                function_path = self.naming.generate_file_path(
                    entity, function_code, file_type="function", base_dir=output_dir
                )
                Path(function_path).parent.mkdir(parents=True, exist_ok=True)
                Path(function_path).write_text(schema_output.functions_sql)

            # 3. Metadata (layer 01, comment file)
            metadata_path = self.naming.generate_file_path(
                entity, table_code, file_type="comment", base_dir=output_dir
            )
            Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
            Path(metadata_path).write_text(schema_output.metadata_sql)

            # Track all files
            migration = MigrationFile(
                number=int(table_code, 16),
                name=entity.name.lower(),
                content=schema_output.tables_sql,  # Primary content
                path=Path(table_path),
                table_code=table_code
            )
            result.migrations.append(migration)

        else:
            # Legacy mode (combined file)
            # ... (existing code) ...
```

**Test split output:**
```bash
python -m src.cli.generate entities entities/examples/contact.yaml --use-registry --output-dir test_split

# Should create:
# test_split/01_write_side/.../012311_tb_contact.sql      (tables)
# test_split/03_functions/.../032311_fn_contact.sql       (functions)
# test_split/01_write_side/.../012311_comments_contact.sql (metadata)
```

---

## 🟢 Phase 2: Dual-Mode Output (Days 4-5)

### **Objective**: Support both hierarchical (registry) and Confiture-compatible flat output

---

### **Day 4: Confiture Output Mode** (GREEN)

#### Add `--output-format` option

```python
# src/cli/generate.py

@click.option(
    "--output-format",
    type=click.Choice(["hierarchical", "confiture"]),
    default="hierarchical",
    help="Output format: hierarchical (full registry paths) or confiture (db/schema/ flat)"
)
def generate(subcommand, entity_files, output_format, ...):
    orchestrator = CLIOrchestrator(
        use_registry=True,
        output_format=output_format
    )
```

**Confiture mode mapping:**

| Registry Layer | Confiture Directory | Example |
|----------------|---------------------|---------|
| `01_write_side` | `db/schema/10_tables` | `10_tables/contact.sql` |
| `03_functions` | `db/schema/30_functions` | `30_functions/contact_actions.sql` |
| `01_write_side` (comments) | `db/schema/40_metadata` | `40_metadata/contact_fraiseql.sql` |
| `00_common` | `db/schema/00_foundation` | `00_foundation/app_foundation.sql` |

**Implementation:**

```python
# src/cli/orchestrator.py

class CLIOrchestrator:
    def __init__(self, use_registry=False, output_format="hierarchical"):
        self.use_registry = use_registry
        self.output_format = output_format
        # ...

    def generate_file_path_confiture(self, entity, file_type):
        """
        Generate Confiture-compatible flat paths

        Maps registry layers to Confiture directories:
        - 01_write_side → db/schema/10_tables
        - 03_functions → db/schema/30_functions
        - metadata → db/schema/40_metadata
        """
        confiture_map = {
            "table": "10_tables",
            "function": "30_functions",
            "comment": "40_metadata"
        }

        dir_name = confiture_map.get(file_type, "10_tables")
        filename = f"{entity.name.lower()}.sql"

        return f"db/schema/{dir_name}/{filename}"
```

**Test:**
```bash
# Hierarchical mode (full registry paths)
python -m src.cli.generate entities contact.yaml --use-registry --output-format hierarchical
# → generated/migrations/01_write_side/012_crm/.../012311_tb_contact.sql

# Confiture mode (flat)
python -m src.cli.generate entities contact.yaml --use-registry --output-format confiture
# → db/schema/10_tables/contact.sql
# → db/schema/30_functions/contact_actions.sql
# → db/schema/40_metadata/contact_fraiseql.sql
```

---

### **Day 5: Registry Validation** (QA)

#### Add validation commands

**New file**: `src/cli/registry_commands.py`

```python
# src/cli/registry_commands.py

import click
from src.generators.schema.naming_conventions import NamingConventions, DomainRegistry

@click.group()
def registry():
    """Registry management commands"""
    pass

@registry.command()
def validate():
    """Validate domain registry for conflicts and consistency"""

    naming = NamingConventions()

    click.echo("Validating domain registry...")

    # Check for duplicate table codes
    errors = []
    all_codes = set()

    for domain_code, domain in naming.registry.registry["domains"].items():
        for subdomain_code, subdomain in domain.get("subdomains", {}).items():
            for entity_name, entity_data in subdomain.get("entities", {}).items():
                table_code = entity_data.get("table_code")
                if table_code in all_codes:
                    errors.append(f"Duplicate table code {table_code} for entity {entity_name}")
                all_codes.add(table_code)

    if errors:
        click.secho(f"❌ {len(errors)} error(s) found:", fg="red")
        for error in errors:
            click.echo(f"  {error}")
        return 1
    else:
        click.secho(f"✅ Registry valid ({len(all_codes)} entities registered)", fg="green")
        return 0

@registry.command()
@click.argument("entity_name")
def lookup(entity_name):
    """Look up entity in registry"""

    naming = NamingConventions()
    entry = naming.registry.get_entity(entity_name)

    if entry:
        click.echo(f"Entity: {entry.entity_name}")
        click.echo(f"Table Code: {entry.table_code}")
        click.echo(f"Entity Code: {entry.entity_code}")
        click.echo(f"Domain: {entry.domain}")
        click.echo(f"Subdomain: {entry.subdomain}")
        click.echo(f"Assigned: {entry.assigned_at}")
    else:
        click.secho(f"❌ Entity '{entity_name}' not found in registry", fg="red")
        return 1

@registry.command()
def list_codes():
    """List all assigned table codes"""

    naming = NamingConventions()

    click.echo("Registered table codes:\n")

    for domain_code, domain in naming.registry.registry["domains"].items():
        domain_name = domain["name"]
        click.secho(f"Domain {domain_code}: {domain_name}", fg="cyan", bold=True)

        for subdomain_code, subdomain in domain.get("subdomains", {}).items():
            subdomain_name = subdomain["name"]

            entities = subdomain.get("entities", {})
            if entities:
                click.echo(f"  Subdomain {subdomain_code}: {subdomain_name}")
                for entity_name, entity_data in entities.items():
                    table_code = entity_data["table_code"]
                    entity_code = entity_data["entity_code"]
                    click.echo(f"    [{table_code}] {entity_name} ({entity_code})")

        click.echo()
```

**Register commands:**
```python
# src/cli/generate.py (add registry group)

from src.cli.registry_commands import registry

@click.group()
def cli():
    """SpecQL CLI"""
    pass

cli.add_command(generate)
cli.add_command(registry)

if __name__ == "__main__":
    cli()
```

**Test registry commands:**
```bash
# Validate registry
python -m src.cli.generate registry validate

# Look up entity
python -m src.cli.generate registry lookup Contact

# List all codes
python -m src.cli.generate registry list-codes
```

---

## 🔵 Phase 3: Confiture Integration (Days 6-8)

### **Day 6: Install Confiture** (GREEN)

Follow the Confiture integration plan from `TEAM_E_IMPLEMENTATION_PLAN.md`:

```bash
# Add dependency
uv add fraiseql-confiture

# Initialize
uv run confiture init

# Test
echo "CREATE TABLE test (id INTEGER);" > db/schema/test.sql
uv run confiture build --env local
```

---

### **Day 7: Create confiture.yaml** (GREEN)

```yaml
# confiture.yaml

environments:
  local:
    database_url: postgresql://localhost/specql_local
    schema_dirs:
      # Foundation
      - path: db/schema/00_foundation
        order: 0

      # Tables (from registry layer 01)
      - path: db/schema/10_tables
        order: 10

      # Functions (from registry layer 03)
      - path: db/schema/30_functions
        order: 30

      # Metadata (FraiseQL comments)
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

**Test end-to-end:**
```bash
# 1. Generate with registry (Confiture format)
python -m src.cli.generate entities entities/examples/*.yaml --use-registry --output-format confiture

# 2. Build with Confiture
uv run confiture build --env local --output migrations/001_complete.sql

# 3. Verify output contains all parts
grep "CREATE TABLE" migrations/001_complete.sql
grep "CREATE FUNCTION" migrations/001_complete.sql
grep "@fraiseql" migrations/001_complete.sql
```

---

### **Day 8: Update Documentation** (REFACTOR)

Update all documentation to reflect registry + Confiture integration:

**Files to update:**
1. `README.md` - Quick start with registry
2. `.claude/CLAUDE.md` - Team E section
3. `docs/teams/TEAM_E_IMPLEMENTATION_PLAN.md` - Mark phases complete
4. `docs/implementation-plans/naming-conventions-registry/01_PHASED_IMPLEMENTATION.md` - Add Phase 4

**Example README update:**
```markdown
# Quick Start

## Generate Schema from SpecQL (with Registry)

```bash
# 1. Write SpecQL YAML
cat > entities/contact.yaml << EOF
entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified)
EOF

# 2. Generate with hexadecimal registry
python -m src.cli.generate entities entities/contact.yaml --use-registry --output-format confiture

# Generated files:
#   db/schema/10_tables/contact.sql
#   db/schema/30_functions/contact_actions.sql
#   db/schema/40_metadata/contact_fraiseql.sql

# 3. Build final migration with Confiture
uv run confiture build --env local

# 4. Apply to database
uv run confiture migrate up --env local
```

## Commands

- `specql generate entities *.yaml --use-registry` - Generate with hexadecimal codes
- `specql registry validate` - Validate registry for conflicts
- `specql registry lookup Contact` - Look up entity table code
- `confiture build --env local` - Build final migration
- `confiture migrate up` - Apply migrations
```

---

## 🟣 Phase 4: CLI Enhancement (Days 9-10)

### **Day 9: Make Registry Default** (REFACTOR)

Update CLI to use registry by default:

```python
# src/cli/generate.py

@click.option("--use-registry/--no-registry", default=True, help="Use hexadecimal registry (default: True)")
@click.option("--output-format", default="confiture", ...)
def generate(..., use_registry=True, output_format="confiture", ...):
    # Now defaults to registry + Confiture mode
```

**Migration path for existing users:**
```bash
# Old behavior (flat migrations)
python -m src.cli.generate entities *.yaml --no-registry

# New default (registry + Confiture)
python -m src.cli.generate entities *.yaml
```

---

### **Day 10: Integration Tests** (QA)

**File**: `tests/integration/test_registry_confiture_integration.py`

```python
import subprocess
import pytest
from pathlib import Path

def test_full_pipeline_with_registry():
    """Test: SpecQL → Registry → Confiture → Database"""

    # 1. Generate with registry
    result = subprocess.run([
        "python", "-m", "src.cli.generate",
        "entities", "entities/examples/contact.yaml",
        "--use-registry",
        "--output-format", "confiture"
    ], capture_output=True)

    assert result.returncode == 0

    # 2. Verify files created in Confiture structure
    assert Path("db/schema/10_tables/contact.sql").exists()
    assert Path("db/schema/30_functions/contact_actions.sql").exists()
    assert Path("db/schema/40_metadata/contact_fraiseql.sql").exists()

    # 3. Verify table codes are hexadecimal
    content = Path("db/schema/10_tables/contact.sql").read_text()
    # Should contain table name with registry code
    assert "tb_contact" in content

    # 4. Build with Confiture
    result = subprocess.run([
        "confiture", "build", "--env", "test", "--output", "migrations/001_test.sql"
    ], capture_output=True)

    assert result.returncode == 0
    assert Path("migrations/001_test.sql").exists()

    # 5. Verify combined migration
    migration = Path("migrations/001_test.sql").read_text()
    assert "CREATE TABLE" in migration
    assert "CREATE FUNCTION" in migration
    assert "@fraiseql" in migration

    # 6. Verify table code in registry
    from src.generators.schema.naming_conventions import NamingConventions
    naming = NamingConventions()
    entry = naming.registry.get_entity("Contact")

    assert entry is not None
    assert entry.table_code is not None
    assert len(entry.table_code) == 6
    assert all(c in '0123456789ABCDEF' for c in entry.table_code.upper())

def test_hierarchical_vs_confiture_output():
    """Test both output formats produce valid SQL"""

    # Hierarchical
    subprocess.run([
        "python", "-m", "src.cli.generate",
        "entities", "entities/examples/contact.yaml",
        "--use-registry",
        "--output-format", "hierarchical",
        "--output-dir", "test_hierarchical"
    ])

    # Confiture
    subprocess.run([
        "python", "-m", "src.cli.generate",
        "entities", "entities/examples/contact.yaml",
        "--use-registry",
        "--output-format", "confiture"
    ])

    # Both should produce valid SQL
    # (content comparison tests)
```

---

## 📊 Success Criteria

### Phase 1: Registry Integration (Days 1-3)
- [ ] `CLIOrchestrator` uses `NamingConventions` to derive table codes
- [ ] Hierarchical file paths generated from registry
- [ ] `--use-registry` flag working
- [ ] Split output (tables/functions/metadata) working
- [ ] Tests passing (registry integration + backward compatibility)

### Phase 2: Dual-Mode Output (Days 4-5)
- [ ] `--output-format` option (hierarchical vs confiture)
- [ ] Confiture-compatible flat output working
- [ ] Registry validation commands (`validate`, `lookup`, `list-codes`)
- [ ] Documentation updated

### Phase 3: Confiture Integration (Days 6-8)
- [ ] Confiture dependency added
- [ ] `confiture.yaml` configured
- [ ] End-to-end pipeline working (SpecQL → Registry → Confiture → SQL)
- [ ] Migration to `db/schema/` complete
- [ ] Old `migrations/` directory deprecated

### Phase 4: CLI Enhancement (Days 9-10)
- [ ] Registry mode is default
- [ ] Integration tests passing
- [ ] All documentation updated
- [ ] Examples working
- [ ] Migration guide for existing users

---

## 🔧 Development Commands

```bash
# Generate with registry (Confiture format)
python -m src.cli.generate entities entities/*.yaml

# Generate with registry (full hierarchical)
python -m src.cli.generate entities entities/*.yaml --output-format hierarchical

# Legacy mode (no registry)
python -m src.cli.generate entities entities/*.yaml --no-registry

# Registry commands
python -m src.cli.generate registry validate
python -m src.cli.generate registry lookup Contact
python -m src.cli.generate registry list-codes

# Confiture commands
uv run confiture build --env local
uv run confiture migrate up --env local
uv run confiture migrate status

# Tests
uv run pytest tests/unit/cli/test_registry_integration.py -v
uv run pytest tests/integration/test_registry_confiture_integration.py -v
uv run pytest --cov=src/cli --cov=src/generators/schema
```

---

## 📁 Final File Structure

```
registry/
└── domain_registry.yaml              # ✅ EXISTS (Central registry)

src/
├── generators/schema/
│   └── naming_conventions.py         # ✅ EXISTS (795 lines)
│
└── cli/
    ├── orchestrator.py               # ✅ ENHANCE (add registry integration)
    ├── generate.py                   # ✅ ENHANCE (add --use-registry flag)
    ├── registry_commands.py          # ❌ NEW (validate, lookup, list-codes)
    └── confiture_extensions.py       # ❌ NEW (from TEAM_E plan)

db/
├── schema/                           # ❌ NEW (Confiture structure)
│   ├── 00_foundation/
│   ├── 10_tables/                    # Maps to registry layer 01
│   ├── 30_functions/                 # Maps to registry layer 03
│   └── 40_metadata/                  # FraiseQL comments
└── migrations/                       # Confiture Python migrations

generated/migrations/                 # ❌ NEW (Full hierarchical output)
    ├── 01_write_side/
    │   └── 012_crm/
    │       └── 0123_customer/
    │           └── 01231_contact_group/
    │               └── 012311_tb_contact.sql
    └── 03_functions/
        └── 032_crm/
            └── 0323_customer/
                └── 03231_contact_group/
                    └── 032311_fn_qualify_lead.sql

migrations/                           # ❌ DEPRECATED (Old flat structure)
    ├── 000_app_foundation.sql
    └── 100_contact.sql

confiture.yaml                        # ❌ NEW (Confiture config)

tests/
├── unit/
│   ├── cli/
│   │   └── test_registry_integration.py  # ❌ NEW
│   └── registry/
│       ├── test_domain_registry.py       # ✅ EXISTS (21 tests)
│       └── test_naming_conventions.py    # ✅ EXISTS (42 tests)
│
└── integration/
    └── test_registry_confiture_integration.py  # ❌ NEW
```

---

## 📚 Related Documentation

**Existing**:
- `/docs/implementation-plans/naming-conventions-registry/00_OVERVIEW.md`
- `/docs/implementation-plans/naming-conventions-registry/01_PHASED_IMPLEMENTATION.md`
- `/docs/teams/TEAM_E_IMPLEMENTATION_PLAN.md`

**To Create**:
- Migration guide for existing users
- Registry best practices
- Hexadecimal table code reference

**To Update**:
- `.claude/CLAUDE.md` - Team E section
- `README.md` - Quick start
- `CONTRIBUTING.md` - Development workflow

---

## 🎉 Summary

**What This Achieves**:
- ✅ **Registry-based table codes**: Hexadecimal, 6-char, UUID-compatible
- ✅ **Hierarchical file organization**: Multi-level directories based on registry
- ✅ **Dual output modes**: Full hierarchical OR Confiture-compatible flat
- ✅ **Confiture integration**: Production-ready migration tool
- ✅ **Backward compatibility**: Legacy flat mode still available
- ✅ **Registry validation**: Commands to check conflicts and consistency

**Benefits**:
- **Scalability**: 16 domains × 256 subdomains × 16 entities = 65,536 possible entities
- **Clarity**: File paths reflect domain hierarchy
- **Flexibility**: Support both deep hierarchy and Confiture flat mode
- **Consistency**: Single source of truth (registry) for all naming
- **Production-ready**: Confiture handles migration execution

**Timeline**: 10 days (2 weeks)
**Complexity**: MEDIUM-HIGH (integration of 3 systems)
**ROI**: High - unified registry + production migration tool + hexadecimal codes

---

**Status**: 🟢 READY TO START
**Dependencies**:
- ✅ Registry system (COMPLETE)
- ✅ CLI orchestrator (85% complete)
- ❌ Confiture (to be added)

**Next Action**: Start Phase 1 Day 1 - Registry Adapter Layer
