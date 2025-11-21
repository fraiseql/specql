# SpecQL CLI Redesign - Implementation Plan

**Version**: 1.0
**Date**: 2025-11-21
**Methodology**: Phased TDD (RED → GREEN → REFACTOR → QA)

---

## Executive Summary

This plan transforms the SpecQL CLI from a fragmented, hard-to-discover command set into a unified, intuitive interface. The redesign follows a **6-phase approach** with strict TDD discipline.

### Current State
- 10+ commands scattered across files
- Primary command (`generate`) not in main CLI
- Inconsistent naming (`reverse-*` vs `reverse_*`)
- Two separate CLI entry points causing confusion
- Multi-step workflows require scripting

### Target State
- Single unified CLI with logical command groups
- All commands discoverable via `--help`
- Verb-noun consistent naming
- Workflow commands for common tasks
- Progressive disclosure (simple defaults, expert options)

---

## Architecture Overview

### Target CLI Structure

```
specql (v2.0)
│
├── generate <files>              # Primary: YAML → SQL/Frontend
│   ├── --schema-only            # Only DDL
│   ├── --actions-only           # Only PL/pgSQL functions
│   ├── --frontend=<dir>         # TypeScript + Apollo
│   ├── --tests                  # Generate test suites
│   └── --dry-run                # Preview mode
│
├── reverse <subcommand>          # Reverse engineering group
│   ├── sql <files>              # SQL → YAML (tables + functions)
│   ├── python <files>           # Django/FastAPI → YAML
│   ├── typescript <files>       # Prisma/TypeORM → YAML
│   ├── rust <files>             # Diesel/SeaORM → YAML
│   └── project <dir>            # Auto-detect & process
│
├── validate <files>              # Validate YAML
│   └── --check-impacts          # Include impact validation
│
├── patterns <subcommand>         # Pattern operations
│   ├── detect <files>           # Find patterns
│   └── apply <pattern> <file>   # Apply to YAML
│
├── diff <yaml> --compare <sql>   # Schema diffing
│
├── docs <files> -o <output>      # Documentation
│
├── init <subcommand>             # Scaffolding
│   ├── project                  # New SpecQL project
│   ├── entity <name>            # Entity template
│   └── registry                 # Schema registry
│
├── cache <subcommand>            # Cache management
│   ├── stats
│   └── clear
│
└── workflow <subcommand>         # Multi-step automation
    ├── migrate <project>        # Full migration pipeline
    └── sync                     # Incremental sync
```

### File Organization (Target)

```
src/cli/
├── __init__.py
├── main.py                    # Single entry point
├── base.py                    # Shared options, decorators, utilities
│
├── commands/                  # Command implementations
│   ├── __init__.py
│   ├── generate.py            # generate command
│   ├── validate.py            # validate command
│   ├── diff.py                # diff command
│   ├── docs.py                # docs command
│   │
│   ├── reverse/               # reverse subgroup
│   │   ├── __init__.py        # Group definition
│   │   ├── sql.py             # reverse sql
│   │   ├── python.py          # reverse python
│   │   ├── typescript.py      # reverse typescript
│   │   ├── rust.py            # reverse rust
│   │   └── project.py         # reverse project (auto-detect)
│   │
│   ├── patterns/              # patterns subgroup
│   │   ├── __init__.py
│   │   ├── detect.py
│   │   └── apply.py
│   │
│   ├── init/                  # init subgroup
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── entity.py
│   │   └── registry.py
│   │
│   ├── cache/                 # cache subgroup
│   │   ├── __init__.py
│   │   ├── stats.py
│   │   └── clear.py
│   │
│   └── workflow/              # workflow subgroup
│       ├── __init__.py
│       ├── migrate.py
│       └── sync.py
│
└── utils/                     # Shared utilities
    ├── __init__.py
    ├── output.py              # Rich console output
    ├── progress.py            # Progress indicators
    └── error_handler.py       # Unified error handling
```

---

## Phase Breakdown

### Phase 1: Foundation & Base Infrastructure
**Objective**: Create the CLI foundation with shared utilities and the main entry point.

**Deliverables**:
- Unified CLI entry point (`main.py`)
- Base utilities (output formatting, progress, error handling)
- Shared options decorator (`@common_options`)
- Help system with examples

**Dependencies**: None (starting point)

---

### Phase 2: Generate Command (Primary)
**Objective**: Expose the hidden `generate` command as the primary CLI action.

**Deliverables**:
- Top-level `generate` command
- All current options preserved
- `--dry-run` preview mode
- Backward compatibility with existing usage

**Dependencies**: Phase 1

---

### Phase 3: Reverse Command Group
**Objective**: Unify all reverse engineering under `reverse <subcommand>`.

**Deliverables**:
- `reverse sql` (merges `reverse` + `reverse-schema`)
- `reverse python` (from `reverse-python`)
- `reverse typescript` (from `reverse-typescript`)
- `reverse rust` (from `reverse-rust`)
- `reverse project` (new: auto-detect)
- Deprecation warnings for old commands

**Dependencies**: Phase 1

---

### Phase 4: Patterns & Init Commands
**Objective**: Add pattern operations and project scaffolding.

**Deliverables**:
- `patterns detect` (from `detect-patterns`)
- `patterns apply` (new)
- `init project` (new)
- `init entity` (new)
- `init registry` (new)

**Dependencies**: Phase 1

---

### Phase 5: Workflow Commands
**Objective**: Single-command automation for common multi-step tasks.

**Deliverables**:
- `workflow migrate` (reverse → validate → generate)
- `workflow sync` (incremental regeneration)
- Progress reporting and error recovery

**Dependencies**: Phases 2, 3

---

### Phase 6: Polish & Migration
**Objective**: Complete migration, deprecation, and documentation.

**Deliverables**:
- Remove legacy command registrations
- Shell completion scripts
- Interactive help with examples
- Migration guide for users
- Updated documentation

**Dependencies**: Phases 1-5

---

## Detailed Phase Plans

---

## PHASE 1: Foundation & Base Infrastructure

**Objective**: Create shared CLI infrastructure that all commands will use.

### TDD Cycle 1.1: Base Options Decorator

#### RED: Write failing test
```python
# tests/unit/cli/test_base.py
def test_common_options_adds_verbose():
    """Common options decorator should add --verbose flag."""
    from cli.base import common_options

    @common_options
    @click.command()
    def sample_cmd():
        pass

    # Should have --verbose option
    assert any(p.name == 'verbose' for p in sample_cmd.params)

def test_common_options_adds_quiet():
    """Common options decorator should add --quiet flag."""
    # Similar test for --quiet

def test_verbose_and_quiet_mutually_exclusive():
    """--verbose and --quiet should be mutually exclusive."""
    runner = CliRunner()
    result = runner.invoke(sample_cmd, ['--verbose', '--quiet'])
    assert result.exit_code != 0
```

**Expected failure**: `cli.base` module doesn't exist.

#### GREEN: Minimal implementation
```python
# src/cli/base.py
import click
from functools import wraps

def common_options(func):
    """Add common options to any command."""
    @click.option('--verbose', '-v', is_flag=True, help='Enable debug logging')
    @click.option('--quiet', '-q', is_flag=True, help='Suppress non-error output')
    @click.option('--output-dir', '-o', type=click.Path(), help='Output directory')
    @wraps(func)
    def wrapper(*args, verbose, quiet, **kwargs):
        if verbose and quiet:
            raise click.UsageError("--verbose and --quiet are mutually exclusive")
        # Configure logging based on flags
        return func(*args, **kwargs)
    return wrapper
```

#### REFACTOR: Clean up
- Extract logging configuration to utility function
- Add type hints
- Add docstrings

#### QA: Verify
```bash
uv run pytest tests/unit/cli/test_base.py -v
uv run ruff check src/cli/base.py
uv run mypy src/cli/base.py
```

---

### TDD Cycle 1.2: Unified Error Handler

#### RED: Write failing test
```python
# tests/unit/cli/test_error_handler.py
def test_cli_error_shows_message():
    """CLI errors should display user-friendly message."""
    from cli.utils.error_handler import CLIError, handle_cli_error

    with pytest.raises(SystemExit) as exc_info:
        with handle_cli_error():
            raise CLIError("Something went wrong", hint="Try --verbose")

    assert exc_info.value.code == 1

def test_validation_error_shows_file_location():
    """Validation errors should show file and line number."""
    from cli.utils.error_handler import ValidationError

    err = ValidationError("Invalid field type", file="entity.yaml", line=42)
    assert "entity.yaml:42" in str(err)
```

#### GREEN: Minimal implementation
```python
# src/cli/utils/error_handler.py
import click
from contextlib import contextmanager

class CLIError(click.ClickException):
    def __init__(self, message: str, hint: str | None = None):
        super().__init__(message)
        self.hint = hint

    def format_message(self) -> str:
        msg = f"Error: {self.message}"
        if self.hint:
            msg += f"\nHint: {self.hint}"
        return msg

class ValidationError(CLIError):
    def __init__(self, message: str, file: str | None = None, line: int | None = None):
        location = f"{file}:{line}" if file and line else file or ""
        super().__init__(f"{location}: {message}" if location else message)

@contextmanager
def handle_cli_error():
    """Context manager for consistent error handling."""
    try:
        yield
    except CLIError:
        raise
    except Exception as e:
        raise CLIError(str(e)) from e
```

#### REFACTOR: Add rich formatting, suggestions, exit codes

#### QA: Full test suite
```bash
uv run pytest tests/unit/cli/test_error_handler.py -v
```

---

### TDD Cycle 1.3: Main Entry Point

#### RED: Write failing test
```python
# tests/unit/cli/test_main.py
def test_main_help_shows_all_commands():
    """Main --help should list all command groups."""
    runner = CliRunner()
    result = runner.invoke(app, ['--help'])

    assert result.exit_code == 0
    # All top-level commands should be visible
    assert 'generate' in result.output
    assert 'reverse' in result.output
    assert 'validate' in result.output
    assert 'patterns' in result.output
    assert 'diff' in result.output
    assert 'docs' in result.output
    assert 'init' in result.output
    assert 'cache' in result.output
    assert 'workflow' in result.output

def test_main_version():
    """--version should show SpecQL version."""
    runner = CliRunner()
    result = runner.invoke(app, ['--version'])

    assert result.exit_code == 0
    assert 'specql' in result.output.lower()
```

#### GREEN: Minimal implementation
```python
# src/cli/main.py
import click
from importlib.metadata import version

@click.group()
@click.version_option(version('specql'), prog_name='specql')
def app():
    """SpecQL - Business YAML to Production PostgreSQL + GraphQL.

    Transform lightweight business domain definitions into production-ready
    database schemas, PL/pgSQL functions, and frontend code.

    Quick start:

        specql generate entities/*.yaml
        specql reverse sql db/tables/*.sql
        specql validate entities/*.yaml

    Run 'specql COMMAND --help' for command-specific help.
    """
    pass

# Commands will be registered here in subsequent phases
```

#### REFACTOR: Add command groups, lazy loading

#### QA: Integration test
```bash
uv run pytest tests/unit/cli/test_main.py -v
uv run specql --help  # Manual verification
```

---

### Phase 1 Success Criteria
- [ ] `cli.base` module with `@common_options` decorator
- [ ] `cli.utils.error_handler` with consistent error types
- [ ] `cli.utils.output` with Rich console formatting
- [ ] `cli.main` with empty app group showing help
- [ ] All tests pass: `uv run pytest tests/unit/cli/test_base.py tests/unit/cli/test_main.py`
- [ ] Linting passes: `uv run ruff check src/cli/`

---

## PHASE 2: Generate Command (Primary)

**Objective**: Make `generate` the discoverable, primary command.

### TDD Cycle 2.1: Basic Generate Command

#### RED: Write failing test
```python
# tests/unit/cli/commands/test_generate.py
def test_generate_requires_files():
    """Generate should require at least one YAML file."""
    runner = CliRunner()
    result = runner.invoke(app, ['generate'])

    assert result.exit_code != 0
    assert 'Missing argument' in result.output or 'required' in result.output.lower()

def test_generate_accepts_yaml_files():
    """Generate should accept YAML file arguments."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('entity.yaml').write_text('entity: Test\nfields:\n  name: text')
        result = runner.invoke(app, ['generate', 'entity.yaml'])

        # Should not fail due to argument parsing
        assert 'Missing argument' not in result.output

def test_generate_shows_in_help():
    """Generate command should appear in main --help."""
    runner = CliRunner()
    result = runner.invoke(app, ['--help'])

    assert 'generate' in result.output
    assert 'Generate' in result.output  # Description visible
```

#### GREEN: Minimal implementation
```python
# src/cli/commands/generate.py
import click
from pathlib import Path
from cli.base import common_options
from cli.utils.error_handler import CLIError, handle_cli_error

@click.command()
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True))
@common_options
@click.option('--output-dir', '-o', default='migrations', help='Output directory')
@click.option('--schema-only', is_flag=True, help='Generate only schema DDL')
@click.option('--actions-only', is_flag=True, help='Generate only action functions')
@click.option('--frontend', type=click.Path(), help='Generate frontend code to directory')
@click.option('--tests', is_flag=True, help='Generate test suites')
@click.option('--dry-run', is_flag=True, help='Preview without writing files')
@click.pass_context
def generate(ctx, files, output_dir, schema_only, actions_only, frontend, tests, dry_run, **kwargs):
    """Generate PostgreSQL schema and functions from SpecQL YAML.

    Examples:

        specql generate entities/*.yaml
        specql generate contact.yaml --frontend=src/generated
        specql generate entities/*.yaml --dry-run
    """
    with handle_cli_error():
        from cli.orchestrator import CLIOrchestrator

        orchestrator = CLIOrchestrator(
            output_dir=output_dir,
            schema_only=schema_only,
            actions_only=actions_only,
            frontend_dir=frontend,
            generate_tests=tests,
            dry_run=dry_run,
        )

        for file_path in files:
            orchestrator.process(Path(file_path))

        orchestrator.finalize()
```

#### REFACTOR:
- Integrate with existing `CLIOrchestrator`
- Add progress indicators
- Support glob patterns in files

#### QA:
```bash
uv run pytest tests/unit/cli/commands/test_generate.py -v
uv run pytest tests/integration/test_cli_workflow.py -v
```

---

### TDD Cycle 2.2: Generate Options Compatibility

#### RED: Write failing test
```python
def test_generate_with_impacts():
    """--with-impacts should generate mutation impacts JSON."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Setup test entity with action
        Path('entity.yaml').write_text('''
entity: Contact
fields:
  email: text
actions:
  - name: update_email
    steps:
      - update: Contact SET email = :new_email
''')
        result = runner.invoke(app, ['generate', 'entity.yaml', '--with-impacts'])

        assert result.exit_code == 0
        # Should mention impacts generation
        assert 'impacts' in result.output.lower() or Path('mutations/impacts.json').exists()

def test_generate_use_registry():
    """--use-registry should use hex table codes."""
    # Test implementation
```

#### GREEN: Add all current options from `cli/generate.py`

#### REFACTOR: Ensure backward compatibility

#### QA: Run full existing test suite
```bash
uv run pytest tests/unit/cli/test_generate.py -v
uv run pytest tests/integration/ -k generate -v
```

---

### Phase 2 Success Criteria
- [ ] `specql generate` works from command line
- [ ] All existing options preserved (`--with-impacts`, `--use-registry`, etc.)
- [ ] `--dry-run` preview mode functional
- [ ] Generate appears in `specql --help`
- [ ] Existing tests pass (backward compatibility)
- [ ] New tests for CLI interface pass

---

## PHASE 3: Reverse Command Group

**Objective**: Unify all reverse engineering commands under `reverse <subcommand>`.

### TDD Cycle 3.1: Reverse Group Structure

#### RED: Write failing test
```python
# tests/unit/cli/commands/reverse/test_reverse_group.py
def test_reverse_shows_subcommands():
    """reverse --help should show all subcommands."""
    runner = CliRunner()
    result = runner.invoke(app, ['reverse', '--help'])

    assert result.exit_code == 0
    assert 'sql' in result.output
    assert 'python' in result.output
    assert 'typescript' in result.output
    assert 'rust' in result.output
    assert 'project' in result.output

def test_reverse_without_subcommand_shows_help():
    """reverse alone should show help."""
    runner = CliRunner()
    result = runner.invoke(app, ['reverse'])

    # Should show help, not error
    assert 'Usage:' in result.output
```

#### GREEN: Create group structure
```python
# src/cli/commands/reverse/__init__.py
import click

@click.group()
def reverse():
    """Reverse engineer existing code to SpecQL YAML.

    Supports multiple languages and frameworks:

        specql reverse sql db/tables/*.sql
        specql reverse python src/models.py
        specql reverse project ./my-app

    Use 'specql reverse SUBCOMMAND --help' for details.
    """
    pass

# Register in main.py
from cli.commands.reverse import reverse
app.add_command(reverse)
```

#### REFACTOR: Lazy-load subcommands

---

### TDD Cycle 3.2: Reverse SQL (Tables + Functions)

#### RED: Write failing test
```python
# tests/unit/cli/commands/reverse/test_sql.py
def test_reverse_sql_tables():
    """reverse sql should handle table DDL."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('table.sql').write_text('''
CREATE TABLE tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
''')
        result = runner.invoke(app, ['reverse', 'sql', 'table.sql', '-o', 'entities/'])

        assert result.exit_code == 0
        assert Path('entities/contact.yaml').exists()

def test_reverse_sql_functions():
    """reverse sql should handle PL/pgSQL functions."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('func.sql').write_text('''
CREATE FUNCTION crm.update_contact(p_id UUID, p_email TEXT)
RETURNS app.mutation_result AS $$
BEGIN
    UPDATE tb_contact SET email = p_email WHERE id = p_id;
    RETURN (TRUE, 'updated', NULL, NULL);
END;
$$ LANGUAGE plpgsql;
''')
        result = runner.invoke(app, ['reverse', 'sql', 'func.sql', '-o', 'entities/'])

        assert result.exit_code == 0

def test_reverse_sql_auto_detects_type():
    """reverse sql should auto-detect tables vs functions."""
    # Implementation test
```

#### GREEN: Implement unified SQL reverse
```python
# src/cli/commands/reverse/sql.py
import click
from pathlib import Path
from cli.base import common_options
from cli.utils.error_handler import handle_cli_error

@click.command()
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-o', '--output-dir', required=True, type=click.Path(), help='Output directory')
@click.option('--min-confidence', default=0.80, help='Minimum confidence threshold')
@click.option('--no-ai', is_flag=True, help='Skip AI enhancement')
@click.option('--merge-translations/--no-merge-translations', default=True)
@click.option('--preview', is_flag=True, help='Preview without writing')
@click.option('--with-patterns', is_flag=True, help='Auto-detect and apply patterns')
@common_options
def sql(files, output_dir, min_confidence, no_ai, merge_translations, preview, with_patterns, **kwargs):
    """Reverse engineer SQL files to SpecQL YAML.

    Handles both table DDL and PL/pgSQL functions. Auto-detects
    Trinity pattern, foreign keys, audit fields, and more.

    Examples:

        specql reverse sql db/tables/*.sql -o entities/
        specql reverse sql functions.sql -o entities/ --no-ai
        specql reverse sql db/ -o entities/ --with-patterns
    """
    with handle_cli_error():
        from reverse_engineering.table_parser import TableParser
        from reverse_engineering.algorithmic_parser import AlgorithmicParser

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for file_path in files:
            path = Path(file_path)
            content = path.read_text()

            # Auto-detect: table DDL vs function
            if 'CREATE TABLE' in content.upper():
                parser = TableParser(merge_translations=merge_translations)
                # ... table parsing logic
            elif 'CREATE FUNCTION' in content.upper():
                parser = AlgorithmicParser(use_ai=not no_ai)
                # ... function parsing logic

            # Generate YAML output
            # ...
```

#### REFACTOR: Extract shared logic from existing `reverse.py` and `reverse_schema.py`

---

### TDD Cycle 3.3: Reverse Python/TypeScript/Rust

Similar TDD cycles for each language, wrapping existing implementations.

---

### TDD Cycle 3.4: Reverse Project (Auto-detect)

#### RED: Write failing test
```python
# tests/unit/cli/commands/reverse/test_project.py
def test_reverse_project_detects_django():
    """reverse project should detect Django projects."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create Django project structure
        Path('manage.py').write_text('#!/usr/bin/env python')
        Path('app').mkdir()
        Path('app/models.py').write_text('''
from django.db import models

class Contact(models.Model):
    email = models.EmailField()
''')
        result = runner.invoke(app, ['reverse', 'project', '.', '-o', 'entities/'])

        assert result.exit_code == 0
        assert 'Django' in result.output or 'django' in result.output

def test_reverse_project_detects_rust():
    """reverse project should detect Rust/Diesel projects."""
    # Similar test with Cargo.toml and diesel dependency
```

#### GREEN: Implement project detection
```python
# src/cli/commands/reverse/project.py
import click
from pathlib import Path
from cli.base import common_options
from cli.utils.error_handler import handle_cli_error

def detect_project_type(directory: Path) -> str:
    """Auto-detect project type from files."""
    if (directory / 'manage.py').exists():
        return 'django'
    if (directory / 'Cargo.toml').exists():
        return 'rust'
    if (directory / 'package.json').exists():
        pkg = json.loads((directory / 'package.json').read_text())
        if 'prisma' in pkg.get('dependencies', {}):
            return 'prisma'
        return 'typescript'
    if (directory / 'requirements.txt').exists():
        return 'python'
    return 'unknown'

@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('-o', '--output-dir', required=True, type=click.Path())
@click.option('--framework', help='Override auto-detection')
@common_options
def project(directory, output_dir, framework, **kwargs):
    """Reverse engineer an entire project to SpecQL YAML.

    Auto-detects project type (Django, FastAPI, Rust/Diesel, Prisma, etc.)
    and processes all relevant files.

    Examples:

        specql reverse project ./my-django-app -o entities/
        specql reverse project . --framework=diesel -o entities/
    """
    with handle_cli_error():
        project_type = framework or detect_project_type(Path(directory))
        click.echo(f"Detected project type: {project_type}")

        # Dispatch to appropriate reverse command
        # ...
```

---

### TDD Cycle 3.5: Deprecation Warnings

#### RED: Write failing test
```python
def test_old_reverse_schema_shows_deprecation():
    """Old reverse-schema command should show deprecation warning."""
    runner = CliRunner()
    result = runner.invoke(app, ['reverse-schema', '--help'])

    # Should still work but warn
    assert 'deprecated' in result.output.lower() or 'reverse sql' in result.output

def test_old_reverse_python_shows_deprecation():
    """Old reverse-python command should show deprecation warning."""
    # Similar test
```

#### GREEN: Add deprecated command aliases
```python
# src/cli/commands/deprecated.py
import click
import warnings

def deprecated_command(old_name: str, new_name: str, target_func):
    """Create a deprecated alias for a command."""
    @click.command(old_name, hidden=True)  # Hidden from --help
    @click.pass_context
    def wrapper(ctx, **kwargs):
        click.secho(
            f"Warning: '{old_name}' is deprecated. Use '{new_name}' instead.",
            fg='yellow', err=True
        )
        ctx.invoke(target_func, **kwargs)
    return wrapper
```

---

### Phase 3 Success Criteria
- [ ] `specql reverse sql` works for tables and functions
- [ ] `specql reverse python` works for Django/FastAPI
- [ ] `specql reverse typescript` works for Prisma
- [ ] `specql reverse rust` works for Diesel/SeaORM
- [ ] `specql reverse project` auto-detects project type
- [ ] Old commands (`reverse-schema`, `reverse-python`) show deprecation warnings
- [ ] All existing reverse engineering tests pass
- [ ] New unified tests pass

---

## PHASE 4: Patterns & Init Commands

**Objective**: Add pattern management and project scaffolding.

### TDD Cycle 4.1: Patterns Detect

#### RED: Write failing test
```python
# tests/unit/cli/commands/patterns/test_detect.py
def test_patterns_detect_finds_audit_trail():
    """patterns detect should find audit trail pattern."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('table.sql').write_text('''
CREATE TABLE tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    created_by UUID,
    updated_by UUID
);
''')
        result = runner.invoke(app, ['patterns', 'detect', 'table.sql'])

        assert result.exit_code == 0
        assert 'audit' in result.output.lower()

def test_patterns_detect_json_output():
    """patterns detect --format=json should output JSON."""
    # Test JSON output format
```

#### GREEN: Wrap existing `detect-patterns`
```python
# src/cli/commands/patterns/detect.py
import click
from cli.base import common_options

@click.command()
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--min-confidence', default=0.75, help='Minimum confidence (0.0-1.0)')
@click.option('--patterns', multiple=True, help='Specific patterns to detect')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json', 'yaml']), default='text')
@common_options
def detect(files, min_confidence, patterns, output_format, **kwargs):
    """Detect architectural patterns in source code.

    Patterns detected: soft-delete, audit-trail, multi-tenant,
    state-machine, hierarchical, versioning, event-sourcing, etc.

    Examples:

        specql patterns detect db/*.sql
        specql patterns detect src/ --format=json
        specql patterns detect . --patterns=audit-trail --patterns=soft-delete
    """
    from reverse_engineering.universal_pattern_detector import UniversalPatternDetector
    # ... implementation
```

---

### TDD Cycle 4.2: Init Entity

#### RED: Write failing test
```python
# tests/unit/cli/commands/init/test_entity.py
def test_init_entity_creates_file():
    """init entity should create YAML template."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ['init', 'entity', 'Contact', '--schema=crm'])

        assert result.exit_code == 0
        assert Path('entities/contact.yaml').exists()

        content = Path('entities/contact.yaml').read_text()
        assert 'entity: Contact' in content
        assert 'schema: crm' in content

def test_init_entity_with_fields():
    """init entity --field should add fields."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, [
            'init', 'entity', 'Contact',
            '--field=email:text',
            '--field=phone:text'
        ])

        assert result.exit_code == 0
        content = Path('entities/contact.yaml').read_text()
        assert 'email: text' in content
        assert 'phone: text' in content
```

#### GREEN: Implement scaffolding
```python
# src/cli/commands/init/entity.py
import click
from pathlib import Path

ENTITY_TEMPLATE = '''entity: {name}
schema: {schema}
fields:
{fields}
'''

@click.command()
@click.argument('name')
@click.option('--schema', '-s', default='public', help='Database schema')
@click.option('--field', '-f', multiple=True, help='Field definition (name:type)')
@click.option('--output-dir', '-o', default='entities', help='Output directory')
def entity(name, schema, field, output_dir):
    """Create a new SpecQL entity template.

    Examples:

        specql init entity Contact --schema=crm
        specql init entity Order --field=total:decimal --field=status:enum
    """
    fields = []
    for f in field:
        fname, ftype = f.split(':')
        fields.append(f'  {fname}: {ftype}')

    if not fields:
        fields = ['  # Add your fields here', '  name: text']

    content = ENTITY_TEMPLATE.format(
        name=name,
        schema=schema,
        fields='\n'.join(fields)
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / f'{name.lower()}.yaml'
    file_path.write_text(content)

    click.echo(f"Created {file_path}")
```

---

### Phase 4 Success Criteria
- [ ] `specql patterns detect` works with all formats
- [ ] `specql patterns apply` modifies YAML files
- [ ] `specql init entity` creates templates
- [ ] `specql init project` creates project structure
- [ ] `specql init registry` creates domain registry
- [ ] All tests pass

---

## PHASE 5: Workflow Commands

**Objective**: Single commands for common multi-step operations.

### TDD Cycle 5.1: Workflow Migrate

#### RED: Write failing test
```python
# tests/unit/cli/commands/workflow/test_migrate.py
def test_workflow_migrate_django():
    """workflow migrate should reverse + validate + generate."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create minimal Django project
        Path('manage.py').write_text('')
        Path('app').mkdir()
        Path('app/models.py').write_text('''
from django.db import models
class Contact(models.Model):
    email = models.EmailField()
''')

        result = runner.invoke(app, ['workflow', 'migrate', '.', '-o', 'output/'])

        assert result.exit_code == 0
        # Should have created YAML and SQL
        assert Path('output/entities/').exists() or 'entities' in result.output

def test_workflow_migrate_shows_progress():
    """workflow migrate should show step progress."""
    # Test that each step is reported
```

#### GREEN: Implement workflow orchestration
```python
# src/cli/commands/workflow/migrate.py
import click
from pathlib import Path
from cli.base import common_options
from cli.utils.output import console

@click.command()
@click.argument('project_dir', type=click.Path(exists=True, file_okay=False))
@click.option('-o', '--output-dir', required=True, type=click.Path())
@click.option('--skip-validate', is_flag=True, help='Skip validation step')
@click.option('--skip-generate', is_flag=True, help='Skip generation step')
@common_options
def migrate(project_dir, output_dir, skip_validate, skip_generate, **kwargs):
    """Full migration: reverse engineer → validate → generate.

    Automates the complete migration workflow for an existing project.

    Steps:
      1. Detect project type
      2. Reverse engineer to SpecQL YAML
      3. Validate generated YAML
      4. Generate PostgreSQL schema

    Examples:

        specql workflow migrate ./my-django-app -o migration/
        specql workflow migrate . -o output/ --skip-generate
    """
    from cli.commands.reverse.project import detect_project_type

    project_path = Path(project_dir)
    output_path = Path(output_dir)
    entities_dir = output_path / 'entities'
    migrations_dir = output_path / 'migrations'

    # Step 1: Detect project type
    console.print("[bold]Step 1/4:[/bold] Detecting project type...")
    project_type = detect_project_type(project_path)
    console.print(f"  Detected: {project_type}")

    # Step 2: Reverse engineer
    console.print("[bold]Step 2/4:[/bold] Reverse engineering...")
    # ... invoke reverse command

    # Step 3: Validate
    if not skip_validate:
        console.print("[bold]Step 3/4:[/bold] Validating YAML...")
        # ... invoke validate command

    # Step 4: Generate
    if not skip_generate:
        console.print("[bold]Step 4/4:[/bold] Generating PostgreSQL...")
        # ... invoke generate command

    console.print("[bold green]Migration complete![/bold green]")
```

---

### Phase 5 Success Criteria
- [ ] `specql workflow migrate` completes full pipeline
- [ ] `specql workflow sync` does incremental regeneration
- [ ] Progress reporting works
- [ ] Error recovery (partial completion) works
- [ ] All tests pass

---

## PHASE 6: Polish & Migration

**Objective**: Complete the transition, deprecate old commands, finalize docs.

### TDD Cycle 6.1: Shell Completion

#### RED: Write failing test
```python
def test_shell_completion_bash():
    """Should generate bash completion script."""
    runner = CliRunner()
    result = runner.invoke(app, ['--install-completion', 'bash'])

    assert result.exit_code == 0
    # Should output or install completion script
```

#### GREEN: Add completion support
```python
# Use click-completion or built-in Click 8.0+ completion
```

---

### TDD Cycle 6.2: Remove Legacy Commands

#### RED: Write failing test
```python
def test_legacy_commands_removed():
    """Legacy commands should no longer exist after migration period."""
    runner = CliRunner()

    # These should NOT be top-level commands anymore
    result = runner.invoke(app, ['reverse-schema', '--help'])
    assert 'reverse sql' in result.output  # Redirects to new command
```

---

### Phase 6 Deliverables
- [ ] Shell completion for bash/zsh/fish
- [ ] Legacy commands removed or hidden with redirect messages
- [ ] `MIGRATION_GUIDE.md` for users
- [ ] Updated `README.md` with new CLI examples
- [ ] Updated `--help` text with examples
- [ ] Release notes

---

## Implementation Schedule

| Phase | Description | Dependencies | Effort |
|-------|-------------|--------------|--------|
| 1 | Foundation & Base | None | Small |
| 2 | Generate Command | Phase 1 | Medium |
| 3 | Reverse Command Group | Phase 1 | Large |
| 4 | Patterns & Init | Phase 1 | Medium |
| 5 | Workflow Commands | Phases 2, 3 | Medium |
| 6 | Polish & Migration | Phases 1-5 | Small |

### Recommended Order
1. **Phase 1** first (required by all others)
2. **Phase 2** immediately after (primary command)
3. **Phase 3** in parallel with Phase 4
4. **Phase 5** after 2 & 3 complete
5. **Phase 6** last (cleanup)

---

## Testing Strategy

### Test Categories

```bash
# Unit tests (fast, no I/O)
uv run pytest tests/unit/cli/ -v

# Integration tests (file I/O, no database)
uv run pytest tests/integration/cli/ -v

# End-to-end tests (full pipeline)
uv run pytest tests/e2e/cli/ -v

# Backward compatibility tests
uv run pytest tests/compat/cli/ -v
```

### Test Fixtures

```python
# tests/conftest.py
@pytest.fixture
def cli_runner():
    """Click test runner with isolated filesystem."""
    return CliRunner(mix_stderr=False)

@pytest.fixture
def sample_entity_yaml():
    """Sample entity YAML for testing."""
    return '''
entity: Contact
schema: crm
fields:
  email: text
  phone: text
'''

@pytest.fixture
def sample_sql_table():
    """Sample SQL table for reverse engineering tests."""
    return '''
CREATE TABLE tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
'''
```

---

## Risk Mitigation

### Risk 1: Breaking Existing Scripts
**Mitigation**:
- Deprecation warnings for 2 releases before removal
- Legacy command aliases during transition
- `MIGRATION_GUIDE.md` with sed/awk one-liners for script updates

### Risk 2: Test Suite Breaks
**Mitigation**:
- Run existing tests after each phase
- Add compatibility test suite
- Feature flag for new CLI (`SPECQL_CLI_V2=1`)

### Risk 3: Scope Creep
**Mitigation**:
- Strict TDD cycles (no untested code)
- Each phase has clear success criteria
- Phase gates require all tests passing

---

## Success Metrics

### Quantitative
- [ ] All 439+ existing tests pass
- [ ] New tests: 50+ unit, 20+ integration
- [ ] CLI response time < 100ms for help commands
- [ ] Zero breaking changes for documented commands

### Qualitative
- [ ] New user can generate schema in < 2 minutes
- [ ] All commands discoverable via `--help`
- [ ] Common workflows achievable in single command
- [ ] Error messages include actionable hints

---

## Appendix: Command Mapping

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `python -m cli.generate entities` | `specql generate` | Now discoverable |
| `specql reverse` | `specql reverse sql` | Functions only |
| `specql reverse-schema` | `specql reverse sql` | Tables (merged) |
| `specql reverse-python` | `specql reverse python` | |
| `specql reverse-typescript` | `specql reverse typescript` | |
| `specql reverse-rust` | `specql reverse rust` | |
| `specql detect-patterns` | `specql patterns detect` | |
| `specql validate` | `specql validate` | Unchanged |
| `specql diff` | `specql diff` | Now discoverable |
| `specql docs` | `specql docs` | Now discoverable |
| `specql cache *` | `specql cache *` | Unchanged |
| N/A | `specql init *` | New |
| N/A | `specql workflow *` | New |
| N/A | `specql reverse project` | New |
| N/A | `specql patterns apply` | New |

---

**Document Version**: 1.0
**Status**: Ready for Implementation
**Next Step**: Begin Phase 1 TDD cycles
