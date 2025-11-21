# SpecQL CLI Alignment Plan

**Version**: 2.0
**Date**: 2025-11-21
**Status**: Phase 1 Complete, Phase 2 In Progress
**Methodology**: Phased TDD (RED → GREEN → REFACTOR → QA)

---

## Executive Summary

This plan completes the CLI implementation and aligns documentation. Based on analysis and work completed, the CLI is now ~75% complete.

### Progress Summary

| Task | Status | Notes |
|------|--------|-------|
| Implement `validate` command | ✅ Complete | 16 tests passing |
| Connect `generate` to CLIOrchestrator | ✅ Complete | Full integration |
| Update cli-commands.md | ✅ Complete | Aligned with implementation |
| Update GETTING_STARTED.md | ✅ Complete | Fixed broken examples |
| Update main.py help text | ✅ Complete | Correct syntax |
| Create cli-status.md | ✅ Complete | Status tracker |
| Connect `reverse sql` to parsers | ✅ Complete | Full pglast integration |
| Standardize option naming | ⏳ Pending | `--output-dir` → `--output` |
| Implement `diff` command | ⏳ Pending | Planned |

---

## Remaining Work for Next Agent

### Task 1: Connect `reverse sql` to Real Parsers

**Priority**: High
**Effort**: 4 hours
**Location**: `src/cli/commands/reverse/sql.py`

**Current State**: The command accepts arguments and shows mock output but doesn't integrate with the existing parsers.

**Target State**: Full integration with `TableParser` from `reverse_engineering/table_parser.py`.

#### Implementation Steps

1. **Read current implementation**:
   ```bash
   cat src/cli/commands/reverse/sql.py
   ```

2. **Understand the existing parsers**:
   ```bash
   # Table parser
   cat reverse_engineering/table_parser.py

   # Function parser
   cat reverse_engineering/algorithmic_parser.py
   ```

3. **Update sql.py to integrate parsers**:

   ```python
   # src/cli/commands/reverse/sql.py

   from pathlib import Path
   import click
   from cli.utils.error_handler import handle_cli_error
   from cli.utils.output import output


   @click.command()
   @click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
   @click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
   @click.option("--min-confidence", default=0.80, help="Minimum confidence threshold")
   @click.option("--no-ai", is_flag=True, help="Skip AI enhancement")
   @click.option("--merge-translations/--no-merge-translations", default=True)
   @click.option("--preview", is_flag=True, help="Preview without writing")
   @click.option("--with-patterns", is_flag=True, help="Auto-detect and apply patterns")
   def sql(files, output_dir, min_confidence, no_ai, merge_translations, preview, with_patterns):
       """Reverse engineer SQL files to SpecQL YAML."""
       with handle_cli_error():
           from reverse_engineering.table_parser import TableParser

           output.info(f"Reversing {len(files)} SQL file(s)...")

           output_path = Path(output_dir)
           output_path.mkdir(parents=True, exist_ok=True)

           parser = TableParser(merge_translations=merge_translations)
           results = []

           for file_path in files:
               path = Path(file_path)
               content = path.read_text()

               # Auto-detect content type
               if 'CREATE TABLE' in content.upper():
                   output.info(f"  Parsing table DDL: {path.name}")
                   entities = parser.parse_tables(content)
                   results.extend(entities)
               elif 'CREATE FUNCTION' in content.upper():
                   output.info(f"  Parsing function: {path.name}")
                   # Use algorithmic parser for functions
                   if not no_ai:
                       from reverse_engineering.algorithmic_parser import AlgorithmicParser
                       func_parser = AlgorithmicParser()
                       actions = func_parser.parse_functions(content)
                       # Merge actions into entities

           if preview:
               output.info("Preview mode - showing what would be generated:")
               for entity in results:
                   output.info(f"  - {entity.name}.yaml")
               return

           # Write YAML files
           for entity in results:
               yaml_path = output_path / f"{entity.name.lower()}.yaml"
               yaml_content = generate_yaml_from_entity(entity)
               yaml_path.write_text(yaml_content)
               output.success(f"  Created: {yaml_path}")

           output.success(f"Generated {len(results)} entity file(s)")
   ```

4. **Write tests**:

   Create `tests/unit/cli/commands/reverse/test_sql_integration.py`:

   ```python
   from pathlib import Path
   import pytest
   from click.testing import CliRunner
   from cli.main import app


   @pytest.fixture
   def cli_runner():
       return CliRunner()


   @pytest.fixture
   def sample_sql_ddl():
       return '''
   CREATE TABLE crm.tb_contact (
       pk_contact SERIAL PRIMARY KEY,
       id UUID NOT NULL DEFAULT gen_random_uuid(),
       identifier TEXT NOT NULL,
       email TEXT NOT NULL,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
   '''


   def test_reverse_sql_creates_yaml(cli_runner, sample_sql_ddl):
       """Reverse sql should create YAML from SQL DDL."""
       with cli_runner.isolated_filesystem():
           Path('tables.sql').write_text(sample_sql_ddl)
           Path('out').mkdir()

           result = cli_runner.invoke(app, ['reverse', 'sql', 'tables.sql', '-o', 'out/'])

           assert result.exit_code == 0
           yaml_files = list(Path('out/').glob('*.yaml'))
           assert len(yaml_files) > 0


   def test_reverse_sql_preview_mode(cli_runner, sample_sql_ddl):
       """Reverse sql --preview should not write files."""
       with cli_runner.isolated_filesystem():
           Path('tables.sql').write_text(sample_sql_ddl)
           Path('out').mkdir()

           result = cli_runner.invoke(app, ['reverse', 'sql', 'tables.sql', '-o', 'out/', '--preview'])

           assert result.exit_code == 0
           assert 'Preview' in result.output
           yaml_files = list(Path('out/').glob('*.yaml'))
           assert len(yaml_files) == 0
   ```

5. **Run tests**:
   ```bash
   uv run pytest tests/unit/cli/commands/reverse/test_sql_integration.py -v
   ```

---

### Task 2: Standardize Option Naming

**Priority**: Medium
**Effort**: 2 hours
**Files to modify**:
- `src/cli/base.py`
- `src/cli/commands/generate.py`
- `tests/unit/cli/test_base.py`
- `tests/unit/cli/commands/test_generate.py`

#### Implementation Steps

1. **Update base.py**:

   Change `--output-dir` to `--output`:

   ```python
   # src/cli/base.py

   def common_options(f: Callable) -> Callable:
       """Decorator to add common options to a Click command."""
       # Change from --output-dir to --output
       f = click.option("-o", "--output", type=click.Path(), help="Output directory")(f)
       f = click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")(f)
       f = click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")(f)
       return f
   ```

2. **Update generate.py parameter names**:

   Change `output_dir` parameter to `output` throughout the function.

3. **Update feature flags to use `--with-*` prefix** (optional - for consistency):

   ```python
   # Current: --frontend PATH
   # Target: --with-frontend (flag) + --frontend-dir PATH (optional)

   @click.option("--with-frontend", is_flag=True, help="Generate frontend code")
   @click.option("--frontend-dir", type=click.Path(), help="Frontend output directory")
   @click.option("--with-tests", is_flag=True, help="Generate test fixtures")
   ```

4. **Update tests**:

   Modify test assertions to use new option names.

5. **Update documentation**:

   Already done in `docs/06_reference/cli-commands.md`.

---

### Task 3: Implement `diff` Command (Optional)

**Priority**: Low
**Effort**: 4 hours
**Location**: `src/cli/commands/diff.py` (new file)

#### Implementation Steps

1. **Create the diff command**:

   ```python
   # src/cli/commands/diff.py

   import click
   from pathlib import Path
   from cli.base import common_options
   from cli.utils.error_handler import handle_cli_error
   from cli.utils.output import output


   @click.command()
   @click.argument("yaml_file", type=click.Path(exists=True))
   @click.option("--compare", required=True, type=click.Path(exists=True), help="SQL file to compare")
   @click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
   @click.option("--ignore-comments", is_flag=True, help="Ignore comment differences")
   @common_options
   def diff(yaml_file, compare, output_format, ignore_comments, **kwargs):
       """Compare SpecQL YAML with existing SQL schema.

       Examples:

           specql diff entities/contact.yaml --compare db/schema/contact.sql
       """
       with handle_cli_error():
           from core.specql_parser import SpecQLParser
           from generators.schema_orchestrator import SchemaOrchestrator

           # 1. Parse YAML and generate SQL
           parser = SpecQLParser()
           yaml_content = Path(yaml_file).read_text()
           entity_def = parser.parse(yaml_content)

           orchestrator = SchemaOrchestrator()
           generated_sql = orchestrator.generate_table_sql(entity_def)

           # 2. Read existing SQL
           existing_sql = Path(compare).read_text()

           # 3. Compare (simplified - could use difflib)
           import difflib

           if ignore_comments:
               # Strip comments
               generated_lines = [l for l in generated_sql.splitlines() if not l.strip().startswith('--')]
               existing_lines = [l for l in existing_sql.splitlines() if not l.strip().startswith('--')]
           else:
               generated_lines = generated_sql.splitlines()
               existing_lines = existing_sql.splitlines()

           diff_result = list(difflib.unified_diff(
               existing_lines, generated_lines,
               fromfile=str(compare), tofile=f"generated from {yaml_file}",
               lineterm=''
           ))

           if not diff_result:
               output.success("No differences found")
               return

           if output_format == "json":
               import json
               output.info(json.dumps({"differences": diff_result}))
           else:
               for line in diff_result:
                   if line.startswith('+'):
                       output.success(line)
                   elif line.startswith('-'):
                       output.error(line)
                   else:
                       output.info(line)
   ```

2. **Register in main.py**:

   ```python
   # Add to register_commands():
   from cli.commands.diff import diff
   app.add_command(diff)
   ```

3. **Write tests**:

   Create `tests/unit/cli/commands/test_diff.py`.

4. **Update cli-status.md**:

   Change `diff` status from "Planned" to "Stable".

---

### Task 4: Connect Other Reverse Commands (Optional)

**Priority**: Low
**Effort**: 8 hours total

The Python, TypeScript, and Rust reverse commands are stubs. To fully implement:

1. **reverse python**: Integrate with existing Django/SQLAlchemy parsers
2. **reverse typescript**: Create Prisma schema parser
3. **reverse rust**: Create Diesel schema parser

Each follows the same pattern as `reverse sql`.

---

## Testing Checklist

After completing any task, run these checks:

```bash
# Run all CLI tests
uv run pytest tests/unit/cli/ -v

# Run specific command tests
uv run pytest tests/unit/cli/commands/test_validate.py -v
uv run pytest tests/unit/cli/commands/test_generate.py -v
uv run pytest tests/unit/cli/commands/reverse/ -v

# Verify CLI help
uv run specql --help
uv run specql generate --help
uv run specql validate --help
uv run specql reverse sql --help

# Quick smoke test
uv run specql validate entities/user.yaml
uv run specql generate entities/user.yaml --dry-run
```

---

## Files Modified in Phase 1 (Completed)

| File | Change |
|------|--------|
| `src/cli/commands/validate.py` | **Created** - New validate command |
| `src/cli/commands/generate.py` | Connected to CLIOrchestrator |
| `src/cli/orchestrator.py` | Added `convert_entity_definition_to_entity` |
| `src/cli/main.py` | Registered validate, updated help text |
| `docs/06_reference/cli-commands.md` | **Rewritten** - Aligned with implementation |
| `docs/06_reference/cli-status.md` | **Created** - Status tracker |
| `GETTING_STARTED.md` | Fixed Quick Reference section |
| `.claude/CLAUDE.md` | Updated status and test counts |
| `tests/unit/cli/commands/test_validate.py` | **Created** - 16 tests |

---

## Files to Modify in Phase 2 (Remaining)

| File | Change | Priority |
|------|--------|----------|
| `src/cli/commands/reverse/sql.py` | Integrate TableParser | High |
| `src/cli/base.py` | Rename `--output-dir` to `--output` | Medium |
| `src/cli/commands/generate.py` | Update parameter names | Medium |
| `src/cli/commands/diff.py` | **Create** | Low |
| `tests/unit/cli/commands/reverse/test_sql_integration.py` | **Create** | High |
| `tests/unit/cli/commands/test_diff.py` | **Create** | Low |

---

## Success Criteria

### Phase 1 (Completed)
- [x] `specql validate` works
- [x] `specql generate` produces SQL
- [x] Documentation matches implementation
- [x] 49 CLI tests passing

### Phase 2 (Remaining)
- [ ] `specql reverse sql` produces YAML from DDL
- [ ] Option naming standardized
- [ ] 55+ CLI tests passing

### Phase 3 (Optional)
- [ ] `specql diff` implemented
- [ ] `specql reverse python` integrated
- [ ] 65+ CLI tests passing

---

**Document Version**: 2.0
**Last Updated**: 2025-11-21
**Next Agent**: Start with Task 1 (Connect reverse sql to parsers)
