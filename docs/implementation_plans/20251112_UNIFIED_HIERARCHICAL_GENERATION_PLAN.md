# Unified Hierarchical Generation + Universal Pattern Library

**Date**: 2025-11-12
**Status**: Ready to Implement
**Complexity**: MEDIUM (builds on existing foundation)
**Timeline**: 2-3 weeks

---

## 🎯 Executive Summary

Complete the hierarchical file generation for **read-side** (tv_/v_) by reusing existing **write-side** infrastructure, then expand to a **universal pattern library** for architectural code generation.

**What's Done**: ✅ 60% complete
- Code parsing (7-digit decimal codes)
- Path generation (hierarchical structure)
- Registry integration (read-side sequencing)
- File object generation
- Write-side hierarchical generation (DONE)

**What's Missing**: ❌ 40% remaining
- File writing to disk (reuse write-side writer)
- CLI integration (add `--hierarchical` flag)
- Integration tests (end-to-end)

**Then**: Expand to universal architectural pattern library (Tier 1→2→3)

---

## 📊 Current State Analysis

### Existing Infrastructure (REUSABLE) ✅

#### 1. Write-Side Hierarchical Generation (src/generators/schema/naming_conventions.py:960-1055)
```python
def generate_file_path(
    entity: Entity,
    table_code: str,
    file_type: str = "table",
    base_dir: str = "generated/migrations",
) -> str:
    """
    Generate hierarchical file path for entity

    Hierarchy:
    base_dir/
      01_write_side/
        012_crm/
          0123_customer/
            01236_contact/
              012361_tb_contact.sql
    """
```

**Pattern**: Schema layer → Domain → Subdomain → Entity → File

#### 2. CLI Orchestrator File Path Generation (src/cli/orchestrator.py:131-150)
```python
def _generate_tv_file_path(self, tv_file, output_path) -> Path:
    """Generate hierarchical path for tv_ table file."""
    if self.use_registry and self.naming:
        from src.generators.schema.read_side_path_generator import ReadSidePathGenerator
        path_gen = ReadSidePathGenerator()
        relative_path = path_gen.generate_path(tv_file.code, tv_file.name)
        return output_path / relative_path
    else:
        return output_path / f"{tv_file.code}_{tv_file.name}.sql"
```

**Already integrated!** Just needs actual file writing.

---

## 🏗️ Phase 1: Complete Read-Side Hierarchical Generation

**Goal**: Make `specql generate --hierarchical` work for tv_/v_ files
**Timeline**: Week 1 (5 days)
**Foundation**: Reuse write-side patterns

### Step 1.1: Create Unified File Writer (2 days)

**File**: `src/generators/schema/hierarchical_file_writer.py`

```python
"""
Unified file writer for both write-side and read-side hierarchical output.
Reuses path generation logic from naming_conventions.py and read_side_path_generator.py
"""

from pathlib import Path
from typing import Protocol
from dataclasses import dataclass

@dataclass
class FileSpec:
    """Generic file specification"""
    code: str              # 7-digit code (write: 012361, read: 0220310)
    name: str              # File name (tb_contact, tv_contact)
    content: str           # SQL content
    layer: str             # "write_side" or "query_side"
    dependencies: list[str] = field(default_factory=list)


class PathGenerator(Protocol):
    """Protocol for path generation"""
    def generate_path(self, code: str, name: str) -> Path:
        ...


class HierarchicalFileWriter:
    """
    Unified writer for hierarchical file structure.
    Works for both write-side (tables) and read-side (views).
    """

    def __init__(self, base_path: Path, path_generator: PathGenerator):
        """
        Args:
            base_path: Root directory (e.g., "0_schema")
            path_generator: Write-side or read-side path generator
        """
        self.base_path = base_path
        self.path_generator = path_generator

    def write_files(self, files: list[FileSpec], dry_run: bool = False) -> list[Path]:
        """
        Write files to hierarchical directory structure.

        Args:
            files: List of file specifications
            dry_run: If True, don't write, just return paths

        Returns:
            List of written file paths

        Example:
            writer = HierarchicalFileWriter(
                base_path=Path("0_schema"),
                path_generator=ReadSidePathGenerator()
            )

            files = [
                FileSpec("0220310", "tv_contact", "CREATE TABLE...", "query_side"),
                FileSpec("0220110", "tv_company", "CREATE TABLE...", "query_side"),
            ]

            paths = writer.write_files(files)
            # → [
            #     "0_schema/02_query_side/022_crm/0223_customer/0220310_tv_contact.sql",
            #     "0_schema/02_query_side/022_crm/0221_core/0220110_tv_company.sql"
            #   ]
        """
        written_paths = []

        for file_spec in files:
            # Generate hierarchical path
            relative_path = self.path_generator.generate_path(file_spec.code, file_spec.name)
            full_path = self.base_path / relative_path

            if not dry_run:
                # Create parent directories
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                full_path.write_text(file_spec.content, encoding='utf-8')

            written_paths.append(full_path)

        return written_paths

    def write_single_file(self, file_spec: FileSpec, dry_run: bool = False) -> Path:
        """Write a single file"""
        return self.write_files([file_spec], dry_run)[0]
```

**Tests**: `tests/unit/generators/test_hierarchical_file_writer.py`

```python
def test_write_tv_files_to_hierarchy(tmp_path):
    """Should write tv_ files to correct hierarchical structure"""
    writer = HierarchicalFileWriter(
        base_path=tmp_path,
        path_generator=ReadSidePathGenerator()
    )

    files = [
        FileSpec("0220310", "tv_contact", "CREATE TABLE crm.tv_contact ...", "query_side")
    ]

    paths = writer.write_files(files)

    expected = tmp_path / "0_schema/02_query_side/022_crm/0223_customer/0220310_tv_contact.sql"
    assert expected.exists()
    assert "CREATE TABLE crm.tv_contact" in expected.read_text()


def test_write_table_files_to_hierarchy(tmp_path):
    """Should write tb_ files using same pattern"""
    writer = HierarchicalFileWriter(
        base_path=tmp_path,
        path_generator=WriteSidePathGenerator()  # Wrapper around naming_conventions
    )

    files = [
        FileSpec("012361", "tb_contact", "CREATE TABLE crm.tb_contact ...", "write_side")
    ]

    paths = writer.write_files(files)

    expected = tmp_path / "0_schema/01_write_side/012_crm/0123_customer/01236_contact/012361_tb_contact.sql"
    assert expected.exists()


def test_dry_run_returns_paths_without_writing(tmp_path):
    """Should return paths without creating files"""
    writer = HierarchicalFileWriter(tmp_path, ReadSidePathGenerator())

    files = [FileSpec("0220310", "tv_contact", "...", "query_side")]

    paths = writer.write_files(files, dry_run=True)

    assert len(paths) == 1
    assert not paths[0].exists()  # Not written
```

---

### Step 1.2: Integrate TableViewFileGenerator with Writer (1 day)

**Update**: `src/generators/schema/table_view_file_generator.py`

```python
def write_files_to_disk(
    self,
    output_path: Path,
    dry_run: bool = False
) -> list[Path]:
    """
    Generate and write tv_ files to hierarchical structure.

    Args:
        output_path: Base output directory
        dry_run: If True, don't write files

    Returns:
        List of written file paths
    """
    # Generate file objects
    files = self.generate_files()

    # Convert to FileSpec format
    file_specs = [
        FileSpec(
            code=f.code,
            name=f.name,
            content=f.content,
            layer="query_side",
            dependencies=f.dependencies
        )
        for f in files
    ]

    # Write using unified writer
    writer = HierarchicalFileWriter(
        base_path=output_path,
        path_generator=ReadSidePathGenerator()
    )

    return writer.write_files(file_specs, dry_run=dry_run)
```

---

### Step 1.3: CLI Integration (1 day)

**Update**: `src/cli/generate.py`

```python
@click.command()
@click.argument("specql_files", nargs=-1, type=click.Path(exists=True))
@click.option("--output", "-o", default="generated", help="Output directory")
@click.option("--hierarchical/--flat", default=True, help="Hierarchical file structure")
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def generate(specql_files, output, hierarchical, dry_run, verbose):
    """Generate SQL schema from SpecQL files"""

    orchestrator = CLIOrchestrator(
        use_registry=hierarchical,  # Registry required for hierarchical
        output_format="hierarchical" if hierarchical else "flat",
        verbose=verbose
    )

    output_path = Path(output)

    # Parse entities
    entities = []
    for file_path in specql_files:
        entity = orchestrator.parser.parse_file(file_path)
        entities.append(entity)

    if hierarchical:
        # Generate hierarchical structure
        click.echo(f"Generating hierarchical structure in {output_path}/")

        # Write-side (tables)
        for entity in entities:
            table_code = orchestrator.get_table_code(entity)
            table_sql = orchestrator.schema_orchestrator.generate_table_sql(entity)

            file_spec = FileSpec(
                code=table_code,
                name=f"tb_{entity.name.lower()}",
                content=table_sql,
                layer="write_side"
            )

            writer = HierarchicalFileWriter(
                output_path,
                WriteSidePathGenerator(orchestrator.naming)
            )
            path = writer.write_single_file(file_spec, dry_run=dry_run)

            if verbose:
                click.echo(f"  ✅ {path}")

        # Read-side (table views)
        tv_generator = TableViewFileGenerator(entities)
        tv_paths = tv_generator.write_files_to_disk(output_path, dry_run=dry_run)

        for path in tv_paths:
            if verbose:
                click.echo(f"  ✅ {path}")

        click.echo(f"✨ Generated {len(entities)} tables + {len(tv_paths)} views")

    else:
        # Legacy flat generation
        result = orchestrator.generate_from_files(specql_files, output_path)
        click.echo(f"✨ Generated {len(result.migrations)} migrations")
```

**Usage**:
```bash
# Hierarchical (default)
specql generate entities/contact.yaml --output=0_schema/

# Flat (legacy)
specql generate entities/contact.yaml --output=generated/ --flat

# Preview
specql generate entities/*.yaml --dry-run
```

---

### Step 1.4: Integration Tests (1 day)

**File**: `tests/integration/test_hierarchical_generation.py`

```python
def test_generate_hierarchical_structure_end_to_end(tmp_path):
    """E2E: SpecQL YAML → Hierarchical file structure"""

    # Create test YAML
    yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
  company: ref(Company)
table_views:
  mode: force
"""
    yaml_path = tmp_path / "contact.yaml"
    yaml_path.write_text(yaml_content)

    # Generate
    result = cli_runner.invoke([
        "generate",
        str(yaml_path),
        "--output", str(tmp_path / "output"),
        "--hierarchical"
    ])

    assert result.exit_code == 0

    # Verify write-side table
    table_path = tmp_path / "output/0_schema/01_write_side/012_crm/0123_customer/01236_contact/012361_tb_contact.sql"
    assert table_path.exists()
    assert "CREATE TABLE crm.tb_contact" in table_path.read_text()

    # Verify read-side view
    view_path = tmp_path / "output/0_schema/02_query_side/022_crm/0223_customer/0220310_tv_contact.sql"
    assert view_path.exists()
    assert "CREATE TABLE crm.tv_contact" in view_path.read_text()


def test_hierarchical_preserves_dependencies(tmp_path):
    """Should generate files in dependency order"""

    company_yaml = tmp_path / "company.yaml"
    company_yaml.write_text("""
entity: Company
schema: crm
fields:
  name: text
table_views:
  mode: force
""")

    contact_yaml = tmp_path / "contact.yaml"
    contact_yaml.write_text("""
entity: Contact
schema: crm
fields:
  company: ref(Company)
table_views:
  mode: force
""")

    result = cli_runner.invoke([
        "generate",
        str(company_yaml),
        str(contact_yaml),
        "--output", str(tmp_path / "output"),
        "--hierarchical"
    ])

    # Both should exist
    company_view = tmp_path / "output/0_schema/02_query_side/022_crm/0221_core/0220110_tv_company.sql"
    contact_view = tmp_path / "output/0_schema/02_query_side/022_crm/0223_customer/0220310_tv_contact.sql"

    assert company_view.exists()
    assert contact_view.exists()
```

---

## 🏗️ Phase 2: Universal Architectural Pattern Library

**Goal**: Expand from code generation to **architectural pattern generation**
**Timeline**: Week 2-3 (10 days)
**Foundation**: Three-tier pattern hierarchy

### Architecture: Pattern-Driven Generation

```
┌─────────────────────────────────────────────────────────────┐
│ USER INPUT (SpecQL YAML)                                    │
│   entity: Order                                             │
│   patterns:                                                 │
│     - state_machine: [pending, confirmed, shipped]          │
│     - approval_workflow                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: Business Domain Templates                          │
│   - E-commerce (Order, Product, Cart)                      │
│   - CRM (Contact, Company, Opportunity)                    │
│   - Healthcare (Patient, Appointment, Medication)          │
└────────────────────┬────────────────────────────────────────┘
                     │ Composes
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Domain Patterns (Pattern Library DB)               │
│   - state_machine → generates transitions + guards         │
│   - approval_workflow → generates request/approve/reject   │
│   - hierarchy_navigation → generates ancestors/descendants │
└────────────────────┬────────────────────────────────────────┘
                     │ Compiles to
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Primitive Actions (35 step types)                  │
│   declare, query, cte, if/then, foreach, call_function     │
└────────────────────┬────────────────────────────────────────┘
                     │ Generates
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ TARGET CODE (PostgreSQL, Python, TypeScript, etc.)         │
│   PL/pgSQL functions, Django models, Prisma schema         │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 2.1: Create Pattern Library Database (2 days)

**File**: `database/pattern_library.db`
**Schema**: `database/pattern_library_schema.sql`

```sql
-- Tier 1: Primitive Actions
CREATE TABLE primitive_patterns (
    pattern_id INTEGER PRIMARY KEY,
    pattern_name TEXT UNIQUE NOT NULL,      -- 'declare', 'query', 'cte'
    category TEXT NOT NULL,                 -- 'variables', 'queries', 'control_flow'
    description TEXT,
    yaml_syntax TEXT NOT NULL,              -- SpecQL syntax template
    complexity_score INTEGER,               -- 1-10
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tier 2: Domain Patterns (composable)
CREATE TABLE domain_patterns (
    pattern_id INTEGER PRIMARY KEY,
    pattern_name TEXT UNIQUE NOT NULL,      -- 'state_machine', 'approval_workflow'
    category TEXT NOT NULL,                 -- 'state_management', 'workflows'
    description TEXT,
    parameters_schema TEXT NOT NULL,        -- JSON schema for parameters
    implementation_template TEXT NOT NULL,  -- Jinja2 template using Tier 1
    example_usage TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tier 3: Business Domain Templates
CREATE TABLE business_templates (
    template_id INTEGER PRIMARY KEY,
    domain TEXT NOT NULL,                   -- 'crm', 'ecommerce', 'healthcare'
    entity_name TEXT NOT NULL,              -- 'Order', 'Contact', 'Patient'
    template_yaml TEXT NOT NULL,            -- Complete SpecQL entity template
    patterns_used TEXT NOT NULL,            -- JSON array of Tier 2 patterns
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(domain, entity_name)
);

-- Language Implementations
CREATE TABLE language_implementations (
    implementation_id INTEGER PRIMARY KEY,
    pattern_id INTEGER NOT NULL,
    language TEXT NOT NULL,                 -- 'postgresql', 'python', 'typescript'
    implementation_template TEXT NOT NULL,  -- Language-specific Jinja2
    example_code TEXT,
    FOREIGN KEY (pattern_id) REFERENCES primitive_patterns(pattern_id),
    UNIQUE(pattern_id, language)
);
```

**Seed Data**: `database/seed_pattern_library.py`

```python
# Tier 1: Primitive Patterns
PRIMITIVE_PATTERNS = [
    {
        "pattern_name": "declare",
        "category": "variables",
        "yaml_syntax": "declare:\n  variable_name: type [= value]",
        "complexity_score": 2
    },
    {
        "pattern_name": "query",
        "category": "queries",
        "yaml_syntax": "query:\n  into: variable\n  select: fields\n  from: table\n  where: condition",
        "complexity_score": 4
    },
    {
        "pattern_name": "cte",
        "category": "queries",
        "yaml_syntax": "cte:\n  name: cte_name\n  query: select_statement",
        "complexity_score": 6
    },
    # ... 32 more patterns
]

# Tier 2: Domain Patterns
DOMAIN_PATTERNS = [
    {
        "pattern_name": "state_machine",
        "category": "state_management",
        "parameters_schema": {
            "states": "list[string]",
            "transitions": "list[tuple[from, to]]",
            "guards": "dict[transition, condition]"
        },
        "implementation_template": """
actions:
  - name: transition_{{ entity_lower }}
    steps:
      - query:
          into: current_state
          select: state
          from: tb_{{ entity_lower }}
          where: id = $input.id

      - validate:
          expression: $input.target_state IN {{ states }}
          error: invalid_target_state

      - validate:
          expression: ($current_state, $input.target_state) IN {{ transitions }}
          error: invalid_transition

      {% for (from_state, to_state), guard in guards.items() %}
      - if:
          condition: $current_state = '{{ from_state }}' AND $input.target_state = '{{ to_state }}'
          then:
            - validate:
                expression: {{ guard }}
                error: guard_failed
      {% endfor %}

      - update:
          entity: {{ entity }}
          set:
            state: $input.target_state
            state_changed_at: now()
          where: id = $input.id
"""
    },
    {
        "pattern_name": "approval_workflow",
        "category": "workflows",
        "parameters_schema": {
            "approver_role": "string",
            "approval_field": "string"
        },
        "implementation_template": """
actions:
  - name: request_{{ entity_lower }}_approval
    steps:
      - insert:
          entity: {{ entity }}_Approval
          fields:
            {{ entity_lower }}_id: $input.id
            requested_by: $context.user_id
            status: pending

  - name: approve_{{ entity_lower }}
    steps:
      - validate:
          expression: $context.user_role = '{{ approver_role }}'
          error: unauthorized

      - update:
          entity: {{ entity }}_Approval
          set:
            status: approved
            approved_by: $context.user_id
            approved_at: now()
          where: {{ entity_lower }}_id = $input.id

      - update:
          entity: {{ entity }}
          set:
            {{ approval_field }}: true
          where: id = $input.id
"""
    }
]

# Tier 3: Business Templates
BUSINESS_TEMPLATES = [
    {
        "domain": "ecommerce",
        "entity_name": "Order",
        "patterns_used": ["state_machine", "approval_workflow"],
        "template_yaml": """
entity: Order
schema: ecommerce
fields:
  customer_id: ref(Customer)
  total_amount: money
  state: enum(pending, confirmed, shipped, delivered, cancelled)

patterns:
  - state_machine:
      states: [pending, confirmed, shipped, delivered, cancelled]
      transitions:
        - [pending, confirmed]
        - [pending, cancelled]
        - [confirmed, shipped]
        - [confirmed, cancelled]
        - [shipped, delivered]
      guards:
        pending->confirmed: payment_received = true
        confirmed->shipped: items_packed = true
"""
    }
]
```

---

### Step 2.2: Pattern Compiler (3 days)

**File**: `src/generators/patterns/pattern_compiler.py`

```python
"""
Pattern Compiler: Tier 3 → Tier 2 → Tier 1 → Target Code

Compiles business templates through domain patterns to primitive actions.
"""

from dataclasses import dataclass
from typing import Any
import sqlite3
from jinja2 import Template

from src.core.ast_models import EntityDefinition, Action


@dataclass
class PatternApplication:
    """Represents application of a domain pattern to an entity"""
    pattern_name: str
    parameters: dict[str, Any]
    entity: EntityDefinition


class PatternCompiler:
    """
    Compile patterns from Tier 3 → Tier 2 → Tier 1.

    Usage:
        compiler = PatternCompiler("database/pattern_library.db")

        # Apply state_machine pattern
        application = PatternApplication(
            pattern_name="state_machine",
            parameters={
                "states": ["pending", "confirmed", "shipped"],
                "transitions": [("pending", "confirmed"), ...],
                "guards": {"pending->confirmed": "payment_received = true"}
            },
            entity=order_entity
        )

        actions = compiler.compile_pattern(application)
        # → [Action(name="transition_order", steps=[...]), ...]
    """

    def __init__(self, db_path: str = "database/pattern_library.db"):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

    def compile_pattern(self, application: PatternApplication) -> list[Action]:
        """
        Compile a domain pattern into SpecQL actions.

        Args:
            application: Pattern application specification

        Returns:
            List of generated Action objects
        """
        # Load pattern from database
        pattern = self._load_domain_pattern(application.pattern_name)

        if not pattern:
            raise ValueError(f"Pattern '{application.pattern_name}' not found")

        # Render template with parameters
        template = Template(pattern['implementation_template'])
        rendered_yaml = template.render(
            entity=application.entity.name,
            entity_lower=application.entity.name.lower(),
            **application.parameters
        )

        # Parse rendered YAML into SpecQL actions
        from src.core.specql_parser import SpecQLParser
        parser = SpecQLParser()
        actions = parser.parse_yaml_actions(rendered_yaml)

        return actions

    def _load_domain_pattern(self, pattern_name: str) -> dict:
        """Load pattern from database"""
        cursor = self.db.execute(
            "SELECT * FROM domain_patterns WHERE pattern_name = ?",
            (pattern_name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def compile_business_template(self, domain: str, entity_name: str) -> EntityDefinition:
        """
        Load and compile a complete business template.

        Args:
            domain: Business domain (e.g., 'ecommerce')
            entity_name: Entity name (e.g., 'Order')

        Returns:
            Complete EntityDefinition with patterns applied
        """
        # Load template
        cursor = self.db.execute(
            "SELECT * FROM business_templates WHERE domain = ? AND entity_name = ?",
            (domain, entity_name)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Template '{domain}.{entity_name}' not found")

        template_yaml = row['template_yaml']

        # Parse template
        from src.core.specql_parser import SpecQLParser
        parser = SpecQLParser()
        entity = parser.parse_yaml_entity(template_yaml)

        # Apply patterns
        if hasattr(entity, 'patterns'):
            for pattern_spec in entity.patterns:
                application = PatternApplication(
                    pattern_name=pattern_spec['name'],
                    parameters=pattern_spec['parameters'],
                    entity=entity
                )
                pattern_actions = self.compile_pattern(application)
                entity.actions.extend(pattern_actions)

        return entity
```

---

### Step 2.3: CLI Integration for Pattern Generation (2 days)

**New Command**: `specql patterns`

```python
# src/cli/patterns.py

@click.group()
def patterns():
    """Pattern library management"""
    pass


@patterns.command()
@click.argument("domain")
@click.argument("entity")
@click.option("--output", "-o", default="entities", help="Output directory")
def generate_from_template(domain, entity, output):
    """
    Generate entity from business template.

    Example:
        specql patterns generate-from-template ecommerce Order -o entities/
    """
    compiler = PatternCompiler()

    try:
        entity_def = compiler.compile_business_template(domain, entity)

        # Convert to YAML
        yaml_output = entity_to_yaml(entity_def)

        # Write file
        output_path = Path(output) / f"{entity.lower()}.yaml"
        output_path.write_text(yaml_output)

        click.echo(f"✨ Generated {output_path}")
        click.echo(f"   Patterns applied: {len(entity_def.patterns)}")
        click.echo(f"   Actions generated: {len(entity_def.actions)}")

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@patterns.command()
def list_templates():
    """List available business templates"""
    db = sqlite3.connect("database/pattern_library.db")
    cursor = db.execute("SELECT domain, entity_name, description FROM business_templates")

    click.echo("Available Business Templates:\n")
    for row in cursor:
        click.echo(f"  {row[0]}.{row[1]:<20} - {row[2]}")


@patterns.command()
def list_patterns():
    """List available domain patterns"""
    db = sqlite3.connect("database/pattern_library.db")
    cursor = db.execute("SELECT pattern_name, category, description FROM domain_patterns")

    click.echo("Available Domain Patterns:\n")
    for row in cursor:
        click.echo(f"  {row[0]:<25} [{row[1]}] - {row[2]}")
```

**Usage**:
```bash
# List available templates
specql patterns list-templates

# Generate from template
specql patterns generate-from-template ecommerce Order -o entities/

# This creates entities/order.yaml with:
# - All fields from template
# - state_machine pattern compiled into actions
# - approval_workflow pattern compiled into actions

# Then generate SQL
specql generate entities/order.yaml --hierarchical
```

---

### Step 2.4: Multi-Language Support (3 days)

**Goal**: Generate code for multiple languages from same SpecQL

**File**: `src/generators/languages/language_compiler.py`

```python
"""
Multi-language compiler: SpecQL → PostgreSQL/Python/TypeScript/Ruby/etc.

Uses pattern_library.db language_implementations table.
"""

class LanguageCompiler:
    """
    Compile SpecQL to target language.

    Usage:
        compiler = LanguageCompiler("postgresql")
        sql = compiler.compile_entity(entity)

        compiler = LanguageCompiler("python")
        python_code = compiler.compile_entity(entity)
        # → Django models

        compiler = LanguageCompiler("typescript")
        ts_code = compiler.compile_entity(entity)
        # → Prisma schema
    """

    def __init__(self, language: str):
        self.language = language
        self.db = sqlite3.connect("database/pattern_library.db")

    def compile_entity(self, entity: EntityDefinition) -> str:
        """Compile entity to target language"""

        if self.language == "postgresql":
            return self._compile_postgresql(entity)
        elif self.language == "python":
            return self._compile_python_django(entity)
        elif self.language == "typescript":
            return self._compile_typescript_prisma(entity)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _compile_postgresql(self, entity: EntityDefinition) -> str:
        """Current implementation (already exists)"""
        from src.generators.schema_orchestrator import SchemaOrchestrator
        orchestrator = SchemaOrchestrator()
        return orchestrator.generate_complete_schema(entity)

    def _compile_python_django(self, entity: EntityDefinition) -> str:
        """
        Generate Django model.

        Example output:
            from django.db import models

            class Order(models.Model):
                customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
                total_amount = models.DecimalField(max_digits=10, decimal_places=2)
                state = models.CharField(max_length=20, choices=STATE_CHOICES)

                def transition_order(self, target_state):
                    # State machine logic
                    ...
        """
        # Load primitive pattern implementations for Python
        # Render using Jinja2 templates
        pass

    def _compile_typescript_prisma(self, entity: EntityDefinition) -> str:
        """
        Generate Prisma schema.

        Example output:
            model Order {
              id          String   @id @default(uuid())
              customerId  String
              customer    Customer @relation(fields: [customerId], references: [id])
              totalAmount Decimal  @db.Money
              state       OrderState
              createdAt   DateTime @default(now())
            }

            enum OrderState {
              PENDING
              CONFIRMED
              SHIPPED
              DELIVERED
              CANCELLED
            }
        """
        pass
```

**CLI Integration**:
```bash
# Generate for multiple targets
specql generate entities/order.yaml \
  --target=postgresql \
  --target=python \
  --target=typescript \
  --output=generated/

# Output:
# generated/postgresql/0_schema/01_write_side/.../order.sql
# generated/python/models/order.py
# generated/typescript/prisma/schema.prisma
```

---

## 📋 Implementation Timeline

### Week 1: Complete Read-Side Hierarchical Generation
- **Day 1-2**: Create HierarchicalFileWriter (reusable for write+read)
- **Day 3**: Integrate TableViewFileGenerator with writer
- **Day 4**: CLI integration (--hierarchical flag)
- **Day 5**: Integration tests

**Deliverable**: `specql generate --hierarchical` working for both tables and views

---

### Week 2: Pattern Library Foundation
- **Day 1-2**: Create pattern_library.db with seed data
- **Day 3-5**: Implement PatternCompiler (Tier 3→2→1)

**Deliverable**: State machine and approval workflow patterns working

---

### Week 3: Multi-Language Support
- **Day 1-2**: CLI pattern commands
- **Day 3-5**: Language compiler (Python/TypeScript support)

**Deliverable**: Generate Django models and Prisma schema from SpecQL

---

## 🎯 Success Criteria

### Phase 1 (Week 1)
- [ ] `specql generate --hierarchical` creates correct directory structure
- [ ] Both write-side (01_) and read-side (02_) files generated
- [ ] Files written to: `0_schema/{layer}/{domain}/{subdomain}/{entity}/{code}_{name}.sql`
- [ ] Integration tests pass
- [ ] Documentation updated

### Phase 2 (Week 2-3)
- [ ] pattern_library.db created with 35 primitive patterns
- [ ] State machine pattern generates working SpecQL actions
- [ ] `specql patterns generate-from-template` works
- [ ] At least 3 business templates available (Order, Contact, Patient)

### Phase 3 (Future)
- [ ] Multi-language compilation (Python, TypeScript)
- [ ] Pattern marketplace (community patterns)
- [ ] Visual pattern editor

---

## 🤔 Feasibility Assessment: Universal Architectural Pattern Library

**Question**: Can we universalize the architecture itself as a pattern library?

**Answer**: **YES - Highly Feasible (9/10)**

### Why This Works

#### 1. **Architecture IS Patterns**
- DDD patterns (Aggregates, Repositories, Value Objects)
- Event Sourcing (Events, Projections, Sagas)
- CQRS (Commands, Queries, Handlers)
- Microservices (Service Boundaries, API Contracts)

All of these are **composable patterns** that can be expressed in the three-tier system.

#### 2. **Code-Level Patterns → Architecture-Level Patterns**

Same approach, different abstraction level:

```yaml
# Code-level pattern (Tier 2)
pattern: state_machine
applies_to: entity
generates: actions

# Architecture-level pattern (Tier 2)
pattern: cqrs_boundary
applies_to: bounded_context
generates:
  - command_handler
  - query_handler
  - event_store
  - projection
```

#### 3. **Deployment Patterns**

```yaml
# Tier 3: Deployment template
deployment_template: kubernetes_microservice
parameters:
  service_name: order-service
  replicas: 3
  database: postgresql

patterns:
  - service_mesh: istio
  - observability: prometheus+grafana
  - scaling: horizontal_pod_autoscaler

# Generates:
# - k8s/deployment.yaml
# - k8s/service.yaml
# - k8s/configmap.yaml
# - k8s/hpa.yaml
# - istio/virtualservice.yaml
# - monitoring/servicemonitor.yaml
```

---

## 🚀 Extended Vision: Universal System Architecture Library

### Tier 4: System Architecture Patterns

```sql
CREATE TABLE system_architectures (
    arch_id INTEGER PRIMARY KEY,
    arch_name TEXT UNIQUE NOT NULL,         -- 'microservices', 'monolith', 'event_driven'
    category TEXT NOT NULL,                 -- 'application', 'data', 'integration'
    description TEXT,
    components_template TEXT NOT NULL,      -- YAML template for system components
    deployment_template TEXT NOT NULL,      -- Infrastructure as code
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example: Microservices Architecture
INSERT INTO system_architectures VALUES (
    1,
    'microservices_cqrs_event_sourcing',
    'application',
    'Microservices with CQRS and Event Sourcing',
    '
services:
  - name: {{ service_name }}_command
    patterns: [cqrs_command, event_sourcing]
    database: postgresql

  - name: {{ service_name }}_query
    patterns: [cqrs_query, materialized_view]
    database: postgresql_read_replica

  - name: {{ service_name }}_events
    patterns: [event_store, saga_orchestrator]
    database: event_store
',
    '
kubernetes:
  deployments: [command, query, events]
  services: [command-svc, query-svc, events-svc]
  configmaps: [app-config]
  secrets: [db-credentials]
'
);
```

### Usage

```bash
# Generate entire system architecture
specql architecture generate \
  --template=microservices_cqrs_event_sourcing \
  --service-name=order \
  --output=system/

# Generates:
# system/
#   services/
#     order-command/
#       entities/order.yaml
#       generated/... (PostgreSQL)
#     order-query/
#       entities/order_view.yaml
#       generated/... (PostgreSQL)
#     order-events/
#       events/order_events.yaml
#       generated/... (Event Store)
#   k8s/
#     order-command-deployment.yaml
#     order-query-deployment.yaml
#     order-events-deployment.yaml
#   docker-compose.yml
#   README.md
```

---

## 📊 Comparison: Current vs Target

| Feature | Current | Phase 1 | Phase 2 | Phase 3 |
|---------|---------|---------|---------|---------|
| Write-side files | ✅ Hierarchical | ✅ | ✅ | ✅ |
| Read-side files | ❌ Monolithic | ✅ Hierarchical | ✅ | ✅ |
| Pattern library | ❌ None | ❌ | ✅ 35 primitives | ✅ Full |
| Domain patterns | ❌ None | ❌ | ✅ 10 patterns | ✅ 50+ |
| Business templates | ❌ None | ❌ | ✅ 3 templates | ✅ 20+ |
| Multi-language | ❌ PostgreSQL only | ❌ | ❌ | ✅ Python, TS |
| Architecture generation | ❌ None | ❌ | ❌ | 🚀 Future |

---

## 🎯 Final Recommendation

### **Immediate (Week 1)**
**Complete read-side hierarchical generation** by reusing write-side infrastructure.
- Low risk, high value
- Completes existing feature
- Production-ready in 1 week

### **Short Term (Week 2-3)**
**Build pattern library foundation** (Tier 1→2→3)
- Medium complexity, high strategic value
- Enables code generation at scale
- Opens path to multi-language support

### **Long Term (Month 2-3)**
**Expand to architecture generation**
- High complexity, transformative value
- True universal system generation
- Opens $100M+ market opportunity

---

**Status**: Ready to implement Phase 1 immediately
**Next Action**: Create HierarchicalFileWriter and tests
