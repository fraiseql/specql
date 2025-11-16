# Week 1: Make Features Discoverable

**Duration**: 15-18 hours
**Goal**: Users can find and use test generation features
**Status**: Planning

---

## Overview

Transform hidden test generation code into discoverable, usable CLI commands. By end of week, users should be able to:
1. Generate tests with `specql generate-tests`
2. Reverse engineer tests with `specql reverse-tests`
3. See both commands in `specql --help`
4. Find documentation in README

---

## Phase 1.1: Fix `reverse-tests` Command

**Time Estimate**: 2-3 hours
**Priority**: CRITICAL (command exists but broken)

### Current Issue

```bash
$ specql reverse-tests test.sql
# Currently prompts for confirmation then aborts
# Expected: Parse test file and output TestSpec YAML
```

### Objective

Make `specql reverse-tests` work without errors or unexpected prompts.

### TDD Cycle

#### RED: Write Failing Test (30 min)

Create `tests/cli/test_reverse_tests_command.py`:

```python
"""Tests for reverse-tests CLI command."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from src.cli.confiture_extensions import specql


class TestReverseTestsCommand:
    """Test reverse-tests CLI command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def sample_pgtap_test(self, tmp_path):
        """Create sample pgTAP test file."""
        test_file = tmp_path / "test_contact.sql"
        test_file.write_text("""
BEGIN;
SELECT plan(2);

-- Test: Contact table should exist
SELECT has_table('crm'::name, 'tb_contact'::name, 'Contact table exists');

-- Test: Contact should have email column
SELECT has_column('crm', 'tb_contact', 'email', 'Has email column');

SELECT * FROM finish();
ROLLBACK;
        """)
        return test_file

    def test_reverse_tests_help_works(self, runner):
        """reverse-tests --help should work."""
        result = runner.invoke(specql, ['reverse-tests', '--help'])
        assert result.exit_code == 0
        assert 'Reverse engineer test files' in result.output

    def test_reverse_tests_with_preview(self, runner, sample_pgtap_test):
        """reverse-tests with --preview should not prompt."""
        result = runner.invoke(
            specql,
            ['reverse-tests', str(sample_pgtap_test), '--preview']
        )

        # Should succeed without prompts
        assert result.exit_code == 0
        # Should show preview output
        assert 'Contact' in result.output or 'test_contact' in result.output
        # Should NOT contain prompt text
        assert 'Aborted' not in result.output

    def test_reverse_tests_parses_pgtap(self, runner, sample_pgtap_test, tmp_path):
        """reverse-tests should parse pgTAP test file."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            specql,
            [
                'reverse-tests',
                str(sample_pgtap_test),
                '--output-dir', str(output_dir),
                '--entity', 'Contact',
                '--format', 'yaml'
            ]
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Should create YAML output
        expected_yaml = output_dir / "Contact_tests.yaml"
        assert expected_yaml.exists(), f"Expected {expected_yaml} to be created"

    def test_reverse_tests_analyze_coverage(self, runner, sample_pgtap_test):
        """reverse-tests --analyze-coverage should suggest missing tests."""
        result = runner.invoke(
            specql,
            [
                'reverse-tests',
                str(sample_pgtap_test),
                '--analyze-coverage',
                '--preview'
            ]
        )

        assert result.exit_code == 0
        # Should show coverage analysis
        assert 'coverage' in result.output.lower() or 'missing' in result.output.lower()
```

**Run test** (should fail):
```bash
uv run pytest tests/cli/test_reverse_tests_command.py -v
```

Expected failure: Command prompts for input or exits with non-zero code.

#### GREEN: Fix Implementation (1-1.5 hours)

**Debug the issue**:

```bash
# Test command directly
uv run specql reverse-tests --help

# Identify the problem
# Issue: Command likely has confirmation prompt or missing input validation
```

**Fix in `src/cli/reverse_tests.py`**:

The issue is that `reverse_tests` function likely has a confirmation prompt. Check line 26-42:

```python
# Current code (line 26-42):
def reverse_tests(input_files, output_dir, entity, analyze_coverage, format, preview, verbose):
    """
    Reverse engineer test files to SpecQL TestSpec YAML
    ...
    """
    if not input_files:
        click.echo("❌ No input files specified")
        return  # BUG: Should return 1 for error
```

**Fix #1**: Change return to return proper exit code:

```python
# src/cli/reverse_tests.py (line 40-42)

# OLD:
    if not input_files:
        click.echo("❌ No input files specified")
        return  # Returns None, not an error code

# NEW:
    if not input_files:
        click.echo("❌ No input files specified")
        return 1  # Proper error exit code
```

**Check for other issues** - Read the full function:

```bash
# Read the entire reverse_tests function
uv run python -c "
from src.cli.reverse_tests import reverse_tests
import inspect
print(inspect.getsource(reverse_tests))
" | head -100
```

**Likely issue**: Look for `click.confirm()` or similar prompts. If found, make it conditional on `--preview`:

```python
# If there's a confirmation like:
if not preview and not click.confirm('Process files?'):
    click.echo('Aborted!')
    return 1

# Change to:
# Remove confirmation entirely OR only show if not in preview/CI
import os
if not preview and not os.environ.get('CI') and len(input_files) > 10:
    if not click.confirm(f'Process {len(input_files)} files?', default=True):
        click.echo('Aborted!')
        return 1
```

**Fix #2**: Ensure file processing works:

```python
# src/cli/reverse_tests.py (around line 50-100)

# After "Process files" section, ensure output happens:

for input_file in input_files:
    file_path = Path(input_file)

    if verbose:
        click.echo(f"📄 Processing {file_path.name}...")

    # Detect test framework
    test_lang = _detect_test_language(file_path)

    if test_lang not in parsers:
        click.secho(f"⚠️  Unsupported test format: {file_path}", fg="yellow")
        continue

    # Parse test file
    try:
        with open(file_path, 'r') as f:
            test_content = f.read()

        parser = parsers[test_lang]
        parsed = parser.parse_test_file(test_content)

        if preview:
            click.echo(f"✅ Parsed {file_path.name}:")
            click.echo(f"   Source: {parsed.source_language.value}")
            click.echo(f"   Tests: {len(parsed.test_functions)}")
            click.echo(f"   Fixtures: {len(parsed.fixtures)}")
        else:
            # Map to TestSpec and write
            mapper = _get_mapper(test_lang)
            entity_name = entity or _detect_entity_name(file_path)
            test_spec = mapper.map_to_test_spec(parsed, entity_name)

            # Write output
            _write_test_spec(test_spec, output_dir, format, verbose)

    except Exception as e:
        click.secho(f"❌ Failed to parse {file_path}: {e}", fg="red")
        if verbose:
            import traceback
            traceback.print_exc()
        continue

click.echo(f"\n✅ Processed {len(results)} test file(s)")
```

**Add helper functions** if missing:

```python
# src/cli/reverse_tests.py (add these helper functions)

def _detect_test_language(file_path: Path) -> TestSourceLanguage:
    """Detect test framework from file extension."""
    suffix = file_path.suffix.lower()

    if suffix == '.sql':
        return TestSourceLanguage.PGTAP
    elif suffix == '.py':
        return TestSourceLanguage.PYTEST
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _detect_entity_name(file_path: Path) -> str:
    """Detect entity name from test filename."""
    # test_contact.sql -> Contact
    # test_user_profile.py -> UserProfile
    name = file_path.stem

    # Remove 'test_' prefix
    if name.startswith('test_'):
        name = name[5:]

    # Convert to PascalCase
    parts = name.split('_')
    return ''.join(part.capitalize() for part in parts)


def _get_mapper(test_lang: TestSourceLanguage):
    """Get appropriate mapper for test language."""
    if test_lang == TestSourceLanguage.PGTAP:
        from src.reverse_engineering.tests.pgtap_test_parser import PgTAPTestSpecMapper
        return PgTAPTestSpecMapper()
    elif test_lang == TestSourceLanguage.PYTEST:
        from src.reverse_engineering.tests.pytest_test_parser import PytestTestSpecMapper
        return PytestTestSpecMapper()
    else:
        raise ValueError(f"No mapper for {test_lang}")


def _write_test_spec(test_spec, output_dir: str, format: str, verbose: bool):
    """Write TestSpec to file."""
    from pathlib import Path
    import yaml
    import json

    output_path = Path(output_dir) if output_dir else Path('.')
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"{test_spec.entity_name}_tests.{format}"
    file_path = output_path / filename

    # Serialize TestSpec
    spec_dict = _test_spec_to_dict(test_spec)

    if format == 'yaml':
        with open(file_path, 'w') as f:
            yaml.dump(spec_dict, f, default_flow_style=False, sort_keys=False)
    elif format == 'json':
        with open(file_path, 'w') as f:
            json.dump(spec_dict, f, indent=2)

    if verbose:
        click.echo(f"💾 Written {file_path}")


def _test_spec_to_dict(test_spec):
    """Convert TestSpec to dictionary for serialization."""
    return {
        'entity_name': test_spec.entity_name,
        'test_framework': test_spec.test_framework,
        'scenarios': [
            {
                'name': scenario.name,
                'category': scenario.category.value if hasattr(scenario, 'category') else 'integration',
                'description': scenario.description,
                'assertions': [
                    {
                        'type': assertion.assertion_type.value,
                        'target': assertion.target,
                        'expected': assertion.expected,
                        'message': assertion.message
                    }
                    for assertion in scenario.assertions
                ]
            }
            for scenario in test_spec.scenarios
        ],
        'coverage_analysis': getattr(test_spec, 'coverage_analysis', {})
    }
```

#### REFACTOR: Clean Up Code (30 min)

1. **Add type hints**:
```python
from pathlib import Path
from typing import Optional, List

def reverse_tests(
    input_files: tuple[str, ...],
    output_dir: Optional[str],
    entity: Optional[str],
    analyze_coverage: bool,
    format: str,
    preview: bool,
    verbose: bool
) -> int:
    """Reverse engineer test files to SpecQL TestSpec YAML."""
    # ... implementation
```

2. **Extract magic strings**:
```python
# At top of file
DEFAULT_OUTPUT_DIR = '.'
SUPPORTED_FORMATS = ['yaml', 'json']
SUPPORTED_EXTENSIONS = {'.sql': 'pgTAP', '.py': 'pytest'}
```

3. **Improve error messages**:
```python
if not input_files:
    click.secho("❌ Error: No input files specified", fg="red")
    click.echo("\nUsage:")
    click.echo("  specql reverse-tests test.sql")
    click.echo("  specql reverse-tests tests/**/*.py --output-dir=specs/")
    return 1
```

#### QA: Verify Quality (30 min)

**Run tests**:
```bash
# Run the new tests
uv run pytest tests/cli/test_reverse_tests_command.py -v

# Run all CLI tests
uv run pytest tests/cli/ -v

# Run all tests to ensure no regression
uv run pytest --tb=short
```

**Manual testing**:
```bash
# Test with actual file
echo "SELECT has_table('crm', 'tb_contact');" > /tmp/test.sql
uv run specql reverse-tests /tmp/test.sql --preview

# Should output parsed information without prompts

# Test with output
uv run specql reverse-tests /tmp/test.sql --entity=Contact --output-dir=/tmp/specs --format=yaml

# Check output created
ls -la /tmp/specs/
cat /tmp/specs/Contact_tests.yaml
```

**Code quality**:
```bash
# Type checking
uv run mypy src/cli/reverse_tests.py

# Linting
uv run ruff check src/cli/reverse_tests.py

# Fix any issues found
uv run ruff check --fix src/cli/reverse_tests.py
```

### Success Criteria

- [ ] `specql reverse-tests --help` works
- [ ] `specql reverse-tests test.sql --preview` works without prompts
- [ ] `specql reverse-tests test.sql --entity=Contact --output-dir=specs/` creates YAML
- [ ] All tests pass
- [ ] No ruff/mypy errors
- [ ] Command documented in `--help` output

### Deliverables

1. Fixed `src/cli/reverse_tests.py`
2. New test file `tests/cli/test_reverse_tests_command.py`
3. Command works in CLI without errors

---

## Phase 1.2: Create `generate-tests` CLI Command

**Time Estimate**: 6-8 hours
**Priority**: CRITICAL (main feature CLI)

### Objective

Create `specql generate-tests` command that generates pgTAP and pytest tests from entity YAML files.

### TDD Cycle

#### RED: Write Failing Test (1 hour)

Create `tests/cli/test_generate_tests_command.py`:

```python
"""Tests for generate-tests CLI command."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from src.cli.confiture_extensions import specql


class TestGenerateTestsCommand:
    """Test generate-tests CLI command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def sample_entity(self, tmp_path):
        """Create sample entity YAML file."""
        entity_file = tmp_path / "contact.yaml"
        entity_file.write_text("""
entity: Contact
schema: crm

fields:
  email: email
  first_name: text
  last_name: text
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
        """)
        return entity_file

    def test_generate_tests_help_works(self, runner):
        """generate-tests --help should work."""
        result = runner.invoke(specql, ['generate-tests', '--help'])
        assert result.exit_code == 0
        assert 'Generate test files' in result.output
        assert '--type' in result.output
        assert '--output-dir' in result.output

    def test_generate_tests_requires_entity_file(self, runner):
        """generate-tests should require entity file."""
        result = runner.invoke(specql, ['generate-tests'])
        assert result.exit_code != 0
        assert 'entity' in result.output.lower() or 'Usage' in result.output

    def test_generate_tests_pgtap_only(self, runner, sample_entity, tmp_path):
        """generate-tests --type pgtap should generate only pgTAP tests."""
        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                'generate-tests',
                str(sample_entity),
                '--type', 'pgtap',
                '--output-dir', str(output_dir)
            ]
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Should create pgTAP test files
        assert (output_dir / "test_contact_structure.sql").exists()
        assert (output_dir / "test_contact_crud.sql").exists()

        # Should NOT create pytest files
        assert not any(output_dir.glob("*.py"))

    def test_generate_tests_pytest_only(self, runner, sample_entity, tmp_path):
        """generate-tests --type pytest should generate only pytest tests."""
        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                'generate-tests',
                str(sample_entity),
                '--type', 'pytest',
                '--output-dir', str(output_dir)
            ]
        )

        assert result.exit_code == 0

        # Should create pytest test files
        assert (output_dir / "test_contact_integration.py").exists()

        # Should NOT create SQL files
        assert not any(output_dir.glob("*.sql"))

    def test_generate_tests_all_types(self, runner, sample_entity, tmp_path):
        """generate-tests --type all should generate both pgTAP and pytest."""
        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                'generate-tests',
                str(sample_entity),
                '--type', 'all',
                '--output-dir', str(output_dir)
            ]
        )

        assert result.exit_code == 0

        # Should create both pgTAP and pytest
        assert (output_dir / "test_contact_structure.sql").exists()
        assert (output_dir / "test_contact_crud.sql").exists()
        assert (output_dir / "test_contact_integration.py").exists()

    def test_generate_tests_multiple_entities(self, runner, tmp_path):
        """generate-tests should handle multiple entity files."""
        # Create multiple entities
        contact = tmp_path / "contact.yaml"
        contact.write_text("entity: Contact\nschema: crm\nfields:\n  email: email")

        company = tmp_path / "company.yaml"
        company.write_text("entity: Company\nschema: crm\nfields:\n  name: text")

        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                'generate-tests',
                str(contact),
                str(company),
                '--output-dir', str(output_dir)
            ]
        )

        assert result.exit_code == 0

        # Should create tests for both entities
        assert any('contact' in f.name.lower() for f in output_dir.iterdir())
        assert any('company' in f.name.lower() for f in output_dir.iterdir())

    def test_generate_tests_preview_mode(self, runner, sample_entity, tmp_path):
        """generate-tests --preview should not write files."""
        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                'generate-tests',
                str(sample_entity),
                '--preview',
                '--output-dir', str(output_dir)
            ]
        )

        assert result.exit_code == 0
        assert 'Preview' in result.output or 'preview' in result.output

        # Should NOT create any files
        assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0

    def test_generated_pgtap_content(self, runner, sample_entity, tmp_path):
        """Generated pgTAP tests should have correct content."""
        output_dir = tmp_path / "tests"

        runner.invoke(
            specql,
            [
                'generate-tests',
                str(sample_entity),
                '--type', 'pgtap',
                '--output-dir', str(output_dir)
            ]
        )

        structure_test = (output_dir / "test_contact_structure.sql").read_text()

        # Verify pgTAP test structure
        assert 'BEGIN;' in structure_test
        assert 'SELECT plan(' in structure_test
        assert 'has_table' in structure_test
        assert 'crm' in structure_test
        assert 'tb_contact' in structure_test
        assert 'SELECT * FROM finish();' in structure_test
        assert 'ROLLBACK;' in structure_test

    def test_generated_pytest_content(self, runner, sample_entity, tmp_path):
        """Generated pytest tests should have correct content."""
        output_dir = tmp_path / "tests"

        runner.invoke(
            specql,
            [
                'generate-tests',
                str(sample_entity),
                '--type', 'pytest',
                '--output-dir', str(output_dir)
            ]
        )

        pytest_test = (output_dir / "test_contact_integration.py").read_text()

        # Verify pytest test structure
        assert 'import pytest' in pytest_test
        assert 'class TestContactIntegration' in pytest_test
        assert 'def test_create_contact' in pytest_test
        assert 'app.create_contact' in pytest_test
        assert "assert result['status'] == 'success'" in pytest_test
```

**Run test** (should fail):
```bash
uv run pytest tests/cli/test_generate_tests_command.py -v
# Expected: Command not found or all tests fail
```

#### GREEN: Implement Command (3-4 hours)

**Step 1: Create the CLI command file**

Create `src/cli/generate_tests.py`:

```python
"""
CLI command for generating tests from SpecQL entities

Usage:
    specql generate-tests entities/contact.yaml
    specql generate-tests entities/*.yaml --type pgtap
    specql generate-tests entities/ --type pytest --output-dir tests/
"""

import click
from pathlib import Path
from typing import List, Optional
import yaml

from src.core.specql_parser import SpecQLParser
from src.testing.pgtap.pgtap_generator import PgTAPGenerator
from src.testing.pytest.pytest_generator import PytestGenerator


@click.command()
@click.argument('entity_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    '--type',
    'test_type',
    type=click.Choice(['all', 'pgtap', 'pytest'], case_sensitive=False),
    default='all',
    help='Type of tests to generate (default: all)'
)
@click.option(
    '--output-dir',
    '-o',
    type=click.Path(),
    default='tests',
    help='Output directory for generated tests (default: tests/)'
)
@click.option(
    '--preview',
    is_flag=True,
    help='Preview mode - show what would be generated without writing files'
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    help='Show detailed generation progress'
)
@click.option(
    '--overwrite',
    is_flag=True,
    help='Overwrite existing test files'
)
def generate_tests(
    entity_files: tuple[str, ...],
    test_type: str,
    output_dir: str,
    preview: bool,
    verbose: bool,
    overwrite: bool
) -> int:
    """
    Generate test files from SpecQL entity definitions.

    Generates comprehensive test suites including:
    - pgTAP tests: Structure, CRUD, constraints, actions
    - pytest tests: Integration tests for CRUD and actions

    Examples:

        # Generate all tests for Contact entity
        specql generate-tests entities/contact.yaml

        # Generate only pgTAP tests
        specql generate-tests entities/*.yaml --type pgtap

        # Generate pytest tests to custom directory
        specql generate-tests entities/ --type pytest --output-dir tests/integration/

        # Preview what would be generated
        specql generate-tests entities/contact.yaml --preview
    """
    if not entity_files:
        click.secho("❌ Error: No entity files specified", fg="red")
        click.echo("\nUsage: specql generate-tests entities/contact.yaml")
        return 1

    # Initialize generators
    pgtap_gen = PgTAPGenerator()
    pytest_gen = PytestGenerator()
    parser = SpecQLParser()

    # Prepare output directory
    output_path = Path(output_dir)
    if not preview:
        output_path.mkdir(parents=True, exist_ok=True)

    # Track statistics
    stats = {
        'entities_processed': 0,
        'pgtap_files': 0,
        'pytest_files': 0,
        'total_files': 0,
        'errors': []
    }

    # Process each entity file
    for entity_file_path in entity_files:
        try:
            entity_file = Path(entity_file_path)

            if verbose:
                click.echo(f"\n📄 Processing {entity_file.name}...")

            # Parse entity YAML
            with open(entity_file, 'r') as f:
                entity_content = f.read()

            # Parse with SpecQL parser
            try:
                entity = parser.parse(entity_content)
            except Exception as parse_error:
                # Try as dict
                entity_dict = yaml.safe_load(entity_content)
                entity = entity_dict  # We'll use dict directly

            # Extract entity config
            entity_config = _build_entity_config(entity, entity_file)

            if verbose:
                click.echo(f"   Entity: {entity_config['entity_name']}")
                click.echo(f"   Schema: {entity_config['schema_name']}")

            # Generate tests based on type
            generated_files = []

            if test_type in ['all', 'pgtap']:
                pgtap_files = _generate_pgtap_tests(
                    pgtap_gen,
                    entity_config,
                    entity,
                    output_path,
                    preview,
                    verbose,
                    overwrite
                )
                generated_files.extend(pgtap_files)
                stats['pgtap_files'] += len(pgtap_files)

            if test_type in ['all', 'pytest']:
                pytest_files = _generate_pytest_tests(
                    pytest_gen,
                    entity_config,
                    entity,
                    output_path,
                    preview,
                    verbose,
                    overwrite
                )
                generated_files.extend(pytest_files)
                stats['pytest_files'] += len(pytest_files)

            stats['entities_processed'] += 1
            stats['total_files'] += len(generated_files)

            if preview:
                click.echo(f"\n   📋 Would generate {len(generated_files)} test file(s):")
                for file_info in generated_files:
                    click.echo(f"      • {file_info['path']}")
            else:
                click.echo(f"   ✅ Generated {len(generated_files)} test file(s)")

        except Exception as e:
            error_msg = f"Failed to process {entity_file_path}: {e}"
            stats['errors'].append(error_msg)
            click.secho(f"   ❌ {error_msg}", fg="red")
            if verbose:
                import traceback
                traceback.print_exc()
            continue

    # Summary
    click.echo("\n" + "="*60)
    click.echo("📊 Test Generation Summary")
    click.echo("="*60)
    click.echo(f"Entities processed: {stats['entities_processed']}")
    click.echo(f"pgTAP test files:   {stats['pgtap_files']}")
    click.echo(f"pytest test files:  {stats['pytest_files']}")
    click.echo(f"Total test files:   {stats['total_files']}")

    if stats['errors']:
        click.echo(f"\n⚠️  Errors: {len(stats['errors'])}")
        for error in stats['errors']:
            click.echo(f"   • {error}")

    if preview:
        click.secho("\n🔍 Preview mode - no files were written", fg="yellow")
    else:
        click.secho(f"\n✅ Tests generated in {output_dir}/", fg="green", bold=True)

    return 1 if stats['errors'] else 0


def _build_entity_config(entity, entity_file: Path) -> dict:
    """Build entity configuration from parsed entity."""
    # Handle both UniversalEntity and dict
    if isinstance(entity, dict):
        entity_name = entity.get('entity', entity_file.stem.capitalize())
        schema_name = entity.get('schema', 'public')
    else:
        entity_name = getattr(entity, 'name', entity_file.stem.capitalize())
        schema_name = getattr(entity, 'schema', 'public')

    table_name = f"tb_{entity_name.lower()}"

    return {
        'entity_name': entity_name,
        'schema_name': schema_name,
        'table_name': table_name,
        'default_tenant_id': '01232122-0000-0000-2000-000000000001',
        'default_user_id': '01232122-0000-0000-2000-000000000002',
    }


def _generate_pgtap_tests(
    generator: PgTAPGenerator,
    entity_config: dict,
    entity,
    output_path: Path,
    preview: bool,
    verbose: bool,
    overwrite: bool
) -> List[dict]:
    """Generate pgTAP test files."""
    entity_name = entity_config['entity_name']
    generated = []

    # 1. Structure tests
    structure_sql = generator.generate_structure_tests(entity_config)
    structure_file = output_path / f"test_{entity_name.lower()}_structure.sql"

    if not preview:
        if overwrite or not structure_file.exists():
            structure_file.write_text(structure_sql)
            if verbose:
                click.echo(f"      ✓ {structure_file.name}")

    generated.append({'path': str(structure_file.relative_to(output_path.parent)), 'type': 'pgtap_structure'})

    # 2. CRUD tests
    field_mappings = _extract_field_mappings(entity)
    crud_sql = generator.generate_crud_tests(entity_config, field_mappings)
    crud_file = output_path / f"test_{entity_name.lower()}_crud.sql"

    if not preview:
        if overwrite or not crud_file.exists():
            crud_file.write_text(crud_sql)
            if verbose:
                click.echo(f"      ✓ {crud_file.name}")

    generated.append({'path': str(crud_file.relative_to(output_path.parent)), 'type': 'pgtap_crud'})

    # 3. Action tests (if actions exist)
    actions = _extract_actions(entity)
    if actions:
        action_scenarios = _build_action_scenarios(actions)
        action_sql = generator.generate_action_tests(entity_config, actions, action_scenarios)
        action_file = output_path / f"test_{entity_name.lower()}_actions.sql"

        if not preview:
            if overwrite or not action_file.exists():
                action_file.write_text(action_sql)
                if verbose:
                    click.echo(f"      ✓ {action_file.name}")

        generated.append({'path': str(action_file.relative_to(output_path.parent)), 'type': 'pgtap_actions'})

    return generated


def _generate_pytest_tests(
    generator: PytestGenerator,
    entity_config: dict,
    entity,
    output_path: Path,
    preview: bool,
    verbose: bool,
    overwrite: bool
) -> List[dict]:
    """Generate pytest test files."""
    entity_name = entity_config['entity_name']
    generated = []

    # Integration tests
    actions = _extract_actions(entity)
    pytest_code = generator.generate_pytest_integration_tests(entity_config, actions)
    pytest_file = output_path / f"test_{entity_name.lower()}_integration.py"

    if not preview:
        if overwrite or not pytest_file.exists():
            pytest_file.write_text(pytest_code)
            if verbose:
                click.echo(f"      ✓ {pytest_file.name}")

    generated.append({'path': str(pytest_file.relative_to(output_path.parent)), 'type': 'pytest_integration'})

    return generated


def _extract_field_mappings(entity) -> List[dict]:
    """Extract field mappings from entity."""
    mappings = []

    # Handle both dict and object
    if isinstance(entity, dict):
        fields = entity.get('fields', {})
        if isinstance(fields, dict):
            for field_name, field_def in fields.items():
                field_type = field_def if isinstance(field_def, str) else field_def.get('type', 'text')
                mappings.append({
                    'field_name': field_name,
                    'field_type': field_type,
                    'generator_type': 'random'
                })
    else:
        fields = getattr(entity, 'fields', [])
        for field in fields:
            mappings.append({
                'field_name': field.name,
                'field_type': field.type.value if hasattr(field.type, 'value') else str(field.type),
                'generator_type': 'random'
            })

    return mappings


def _extract_actions(entity) -> List[dict]:
    """Extract actions from entity."""
    actions = []

    # Handle both dict and object
    if isinstance(entity, dict):
        entity_actions = entity.get('actions', [])
        for action in entity_actions:
            if isinstance(action, dict):
                actions.append({
                    'name': action.get('name'),
                    'description': action.get('description', '')
                })
            else:
                actions.append({
                    'name': getattr(action, 'name'),
                    'description': getattr(action, 'description', '')
                })
    else:
        entity_actions = getattr(entity, 'actions', [])
        for action in entity_actions:
            actions.append({
                'name': action.name,
                'description': getattr(action, 'description', '')
            })

    return actions


def _build_action_scenarios(actions: List[dict]) -> List[dict]:
    """Build basic test scenarios for actions."""
    scenarios = []

    for action in actions:
        scenarios.append({
            'target_action': action['name'],
            'scenario_name': f"{action['name']}_happy_path",
            'expected_result': 'success',
            'setup_sql': f"-- Setup for {action['name']} test"
        })

    return scenarios
```

**Step 2: Register command in confiture_extensions.py**

Add to `src/cli/confiture_extensions.py` (around line 860, after reverse-tests):

```python
# Add test generation command
from src.cli.generate_tests import generate_tests

specql.add_command(generate_tests, name='generate-tests')
```

#### REFACTOR: Improve Code Quality (1-1.5 hours)

1. **Extract constants**:
```python
# At top of generate_tests.py
DEFAULT_TEST_DIR = 'tests'
DEFAULT_TENANT_ID = '01232122-0000-0000-2000-000000000001'
DEFAULT_USER_ID = '01232122-0000-0000-2000-000000000002'

TEST_TYPES = ['all', 'pgtap', 'pytest']
```

2. **Add comprehensive docstrings**:
```python
def _extract_field_mappings(entity) -> List[dict]:
    """
    Extract field mappings from entity for test generation.

    Converts entity field definitions into a format suitable for
    test data generation. Handles both dictionary and object representations.

    Args:
        entity: Entity definition (dict or UniversalEntity object)

    Returns:
        List of field mapping dictionaries with:
            - field_name: Name of the field
            - field_type: Type of the field (email, text, enum, etc.)
            - generator_type: How to generate test data ('random', 'fixed')

    Example:
        >>> entity = {'fields': {'email': 'email', 'name': 'text'}}
        >>> mappings = _extract_field_mappings(entity)
        >>> len(mappings)
        2
    """
```

3. **Add error handling**:
```python
def _build_entity_config(entity, entity_file: Path) -> dict:
    """Build entity configuration from parsed entity."""
    try:
        # Handle both UniversalEntity and dict
        if isinstance(entity, dict):
            entity_name = entity.get('entity')
            if not entity_name:
                raise ValueError(f"Entity file {entity_file} missing 'entity' field")
            schema_name = entity.get('schema', 'public')
        else:
            entity_name = getattr(entity, 'name', None)
            if not entity_name:
                raise ValueError(f"Entity file {entity_file} has no name")
            schema_name = getattr(entity, 'schema', 'public')

        table_name = f"tb_{entity_name.lower()}"

        return {
            'entity_name': entity_name,
            'schema_name': schema_name,
            'table_name': table_name,
            'default_tenant_id': DEFAULT_TENANT_ID,
            'default_user_id': DEFAULT_USER_ID,
        }
    except Exception as e:
        raise ValueError(f"Failed to build config from {entity_file}: {e}")
```

#### QA: Verify Quality (1 hour)

**Run tests**:
```bash
# Run new tests
uv run pytest tests/cli/test_generate_tests_command.py -v

# Run all tests
uv run pytest --tb=short

# Check coverage for new code
uv run pytest tests/cli/test_generate_tests_command.py --cov=src/cli/generate_tests --cov-report=term-missing
```

**Manual testing**:
```bash
# Test with Contact entity
uv run specql generate-tests docs/06_examples/simple_contact/contact.yaml --preview -v

# Generate actual files
uv run specql generate-tests docs/06_examples/simple_contact/contact.yaml --output-dir /tmp/tests -v

# Verify generated files
ls -la /tmp/tests/
head -50 /tmp/tests/test_contact_structure.sql
head -50 /tmp/tests/test_contact_integration.py

# Test different types
uv run specql generate-tests docs/06_examples/simple_contact/contact.yaml --type pgtap --output-dir /tmp/pgtap
uv run specql generate-tests docs/06_examples/simple_contact/contact.yaml --type pytest --output-dir /tmp/pytest
```

**Code quality**:
```bash
# Type checking
uv run mypy src/cli/generate_tests.py

# Linting
uv run ruff check src/cli/generate_tests.py

# Fix issues
uv run ruff check --fix src/cli/generate_tests.py
```

### Success Criteria

- [ ] `specql generate-tests --help` works
- [ ] `specql generate-tests contact.yaml` generates tests
- [ ] `--type pgtap` generates only SQL files
- [ ] `--type pytest` generates only Python files
- [ ] `--type all` generates both
- [ ] `--preview` doesn't write files
- [ ] Multiple entity files work
- [ ] Generated tests are valid SQL/Python
- [ ] All tests pass
- [ ] No type/lint errors

### Deliverables

1. New file `src/cli/generate_tests.py` (~400 lines)
2. Command registered in `confiture_extensions.py`
3. Tests in `tests/cli/test_generate_tests_command.py` (~200 lines)
4. Command fully functional

---

## Phase 1.3: Update CLI Help & README

**Time Estimate**: 4-5 hours
**Priority**: HIGH

### Objective

Make test commands visible and documented in main user touchpoints.

### Tasks

#### Task 1.3.1: Update Main CLI Help (1 hour)

**Edit `src/cli/confiture_extensions.py`** (line 20-35):

```python
@click.group()
@click.version_option(version="0.4.0-alpha")
def specql():
    """
    SpecQL - Multi-Language Backend Code Generator

    Generate PostgreSQL, Java, Rust, and TypeScript from YAML specifications.

    Code Generation:
      generate       - Generate code from entities
      generate-java  - Generate Spring Boot Java code

    Testing:
      generate-tests - Generate pgTAP and pytest tests
      reverse-tests  - Import existing tests to TestSpec

    Reverse Engineering:
      reverse        - Reverse engineer PostgreSQL to entities
      reverse-python - Reverse engineer Python to entities
      parse-plpgsql  - Parse PostgreSQL DDL to entities

    Utilities:
      validate       - Validate entity definitions
      examples       - Show example entity definitions
      diagram        - Generate entity relationship diagrams
      interactive    - Interactive CLI mode

    Get help on any command:
      specql <command> --help

    Documentation:
      https://github.com/fraiseql/specql/blob/main/docs/
    """
    pass
```

**Test**:
```bash
uv run specql --help
# Should see "Testing:" section with generate-tests and reverse-tests
```

#### Task 1.3.2: Update README (2-3 hours)

**Edit `README.md`** - Add after line 100 (before "What is SpecQL?"):

```markdown
## Automated Testing

SpecQL automatically generates comprehensive test suites for your entities:

### Generate Tests

```bash
# Generate both pgTAP and pytest tests
specql generate-tests entities/contact.yaml

# Generate only pgTAP (PostgreSQL unit tests)
specql generate-tests entities/*.yaml --type pgtap

# Generate only pytest (Python integration tests)
specql generate-tests entities/*.yaml --type pytest --output-dir tests/integration/
```

### What Tests Are Generated?

From a single Contact entity (15 lines of YAML), SpecQL generates **70+ comprehensive tests**:

**pgTAP Tests** (PostgreSQL unit tests):
- ✅ **Structure validation** (10+ tests): Tables, columns, constraints, indexes
- ✅ **CRUD operations** (15+ tests): Create, read, update, delete with happy/error paths
- ✅ **Constraint validation** (8+ tests): NOT NULL, foreign keys, unique constraints
- ✅ **Business logic** (12+ tests): Action execution, state transitions, validations

**pytest Tests** (Python integration tests):
- ✅ **Integration tests** (10+ tests): End-to-end CRUD workflows
- ✅ **Action tests** (8+ tests): Business action execution
- ✅ **Error handling** (6+ tests): Duplicate detection, validation errors
- ✅ **Edge cases** (5+ tests): Boundary conditions, state machine paths

### Example: Contact Entity

```yaml
# contact.yaml (15 lines)
entity: Contact
schema: crm

fields:
  email: email
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Generates**:
```sql
-- test_contact_structure.sql (50+ lines)
SELECT has_table('crm', 'tb_contact', 'Contact table exists');
SELECT has_column('crm', 'tb_contact', 'email', 'Has email column');
SELECT col_is_pk('crm', 'tb_contact', 'pk_contact', 'PK constraint');
-- ... 7 more structure tests

-- test_contact_crud.sql (100+ lines)
SELECT lives_ok(
  $$SELECT app.create_contact('test@example.com')$$,
  'Create contact succeeds'
);
-- ... 14 more CRUD tests

-- test_contact_actions.sql (80+ lines)
SELECT ok(
  (SELECT app.qualify_lead(contact_id)).status = 'success',
  'Qualify lead action succeeds'
);
-- ... 11 more action tests
```

```python
# test_contact_integration.py (150+ lines)
class TestContactIntegration:
    def test_create_contact_happy_path(self, clean_db):
        result = execute("SELECT app.create_contact('test@example.com')")
        assert result['status'] == 'success'

    def test_qualify_lead_action(self, clean_db):
        # ... 9 more integration tests
```

### Reverse Engineer Existing Tests

Import your existing pgTAP or pytest tests into universal TestSpec format:

```bash
# Parse pgTAP tests
specql reverse-tests tests/test_contact.sql

# Parse pytest tests with coverage analysis
specql reverse-tests tests/test_*.py --analyze-coverage

# Convert to universal YAML format
specql reverse-tests test.sql --entity=Contact --output-dir=specs/ --format=yaml
```

**Use cases**:
- 📊 **Coverage analysis** - Find missing test scenarios
- 🔄 **Framework migration** - Convert between test frameworks
- 📚 **Documentation** - Generate test documentation from code
- 🎯 **Gap detection** - Identify untested business logic

---
```

**Add to Features section** (around line 120):

```markdown
**Automated Testing**:
- ✅ pgTAP test generation (structure, CRUD, constraints, actions)
- ✅ pytest test generation (integration, actions, error handling)
- ✅ Test reverse engineering (pgTAP, pytest → universal TestSpec)
- ✅ Coverage analysis and gap detection
```

**Update Quick Example section** to mention tests:

```markdown
**Auto-generates** 2000+ lines across 4 languages **+ 70+ tests**:
- ✅ **PostgreSQL**: Tables, indexes, constraints, audit fields, PL/pgSQL functions
- ✅ **Java/Spring Boot**: JPA entities, repositories, services, controllers
- ✅ **Rust/Diesel**: Models, schemas, queries, Actix-web handlers
- ✅ **TypeScript/Prisma**: Schema, interfaces, type-safe client
- ✅ **Tests**: pgTAP unit tests + pytest integration tests

Plus: FraiseQL GraphQL metadata, tests, CI/CD workflows.
```

#### Task 1.3.3: Create Demo GIF (1 hour)

Record a demo showing:

1. **Entity definition** - Show contact.yaml
2. **Generate tests** - Run `specql generate-tests contact.yaml`
3. **Show generated files** - List output directory
4. **Show test content** - Cat one pgTAP and one pytest file
5. **Run tests** - Show tests passing

```bash
# Record with asciinema or similar
asciinema rec docs/demos/test_generation_demo.cast

# Commands to record:
cat entities/contact.yaml
specql generate-tests entities/contact.yaml -v
ls -la tests/
head -20 tests/test_contact_structure.sql
head -20 tests/test_contact_integration.py
# (optionally show tests passing)
```

Convert to GIF:
```bash
# If using asciinema
asciicast2gif -s 2 docs/demos/test_generation_demo.cast docs/demos/test_generation_demo.gif
```

Add to README after "Quick Start Demo":

```markdown
### Test Generation
![Test Generation Demo](docs/demos/test_generation_demo.gif)
```

### Success Criteria

- [ ] `specql --help` shows Testing section
- [ ] README has "Automated Testing" section
- [ ] README example shows 70+ tests being generated
- [ ] Demo GIF shows test generation workflow
- [ ] All links work
- [ ] No typos or formatting issues

### Deliverables

1. Updated `README.md` (+150 lines)
2. Updated `src/cli/confiture_extensions.py` help text
3. Demo GIF in `docs/demos/test_generation_demo.gif`

---

## Phase 1.4: Basic Examples & Integration Testing

**Time Estimate**: 3-4 hours
**Priority**: HIGH

### Objective

Ensure commands work end-to-end with real entity files and document basic usage.

### Tasks

#### Task 1.4.1: Test with Existing Examples (1 hour)

```bash
# Test with Contact entity from docs
uv run specql generate-tests docs/06_examples/simple_contact/contact.yaml --output-dir /tmp/test_output -v

# Verify generated files
ls -la /tmp/test_output/

# Check pgTAP files are valid SQL
for f in /tmp/test_output/*.sql; do
    echo "Checking $f..."
    # Basic SQL syntax check
    psql -d test_db < $f --dry-run 2>&1 | head -5
done

# Check pytest files are valid Python
for f in /tmp/test_output/*.py; do
    echo "Checking $f..."
    python -m py_compile $f
done
```

#### Task 1.4.2: Create Integration Test (1.5 hours)

Create `tests/integration/test_test_generation_workflow.py`:

```python
"""Integration test for end-to-end test generation workflow."""

import pytest
from pathlib import Path
import subprocess
import tempfile


class TestTestGenerationWorkflow:
    """Test complete test generation workflow."""

    def test_generate_and_validate_pgtap_tests(self, tmp_path):
        """Generate pgTAP tests and validate they're correct SQL."""
        # Create entity file
        entity_file = tmp_path / "test_entity.yaml"
        entity_file.write_text("""
entity: TestEntity
schema: test_schema

fields:
  name: text
  email: email
  status: enum(active, inactive)

actions:
  - name: activate
    steps:
      - update: TestEntity SET status = 'active'
        """)

        # Generate tests
        output_dir = tmp_path / "tests"
        result = subprocess.run(
            [
                "uv", "run", "specql", "generate-tests",
                str(entity_file),
                "--type", "pgtap",
                "--output-dir", str(output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify files created
        structure_test = output_dir / "test_testentity_structure.sql"
        crud_test = output_dir / "test_testentity_crud.sql"
        action_test = output_dir / "test_testentity_actions.sql"

        assert structure_test.exists(), "Structure test not created"
        assert crud_test.exists(), "CRUD test not created"
        assert action_test.exists(), "Action test not created"

        # Verify content
        structure_content = structure_test.read_text()
        assert "has_table" in structure_content
        assert "test_schema" in structure_content
        assert "tb_testentity" in structure_content

        # Verify SQL is syntactically valid (basic check)
        assert "BEGIN;" in structure_content
        assert "SELECT plan(" in structure_content
        assert "SELECT * FROM finish();" in structure_content
        assert "ROLLBACK;" in structure_content

    def test_generate_and_validate_pytest_tests(self, tmp_path):
        """Generate pytest tests and validate they're valid Python."""
        # Create entity file
        entity_file = tmp_path / "test_entity.yaml"
        entity_file.write_text("""
entity: TestEntity
schema: test_schema

fields:
  name: text
  email: email
        """)

        # Generate tests
        output_dir = tmp_path / "tests"
        result = subprocess.run(
            [
                "uv", "run", "specql", "generate-tests",
                str(entity_file),
                "--type", "pytest",
                "--output-dir", str(output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify file created
        pytest_test = output_dir / "test_testentity_integration.py"
        assert pytest_test.exists(), "Pytest test not created"

        # Verify content
        pytest_content = pytest_test.read_text()
        assert "import pytest" in pytest_content
        assert "class TestTestEntityIntegration" in pytest_content
        assert "def test_create_testentity" in pytest_content

        # Verify Python is syntactically valid
        import py_compile
        py_compile.compile(str(pytest_test), doraise=True)

    def test_full_workflow_with_real_entity(self):
        """Test with actual Contact entity from docs."""
        contact_file = Path("docs/06_examples/simple_contact/contact.yaml")

        if not contact_file.exists():
            pytest.skip("Contact example not found")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "tests"

            # Generate all tests
            result = subprocess.run(
                [
                    "uv", "run", "specql", "generate-tests",
                    str(contact_file),
                    "--type", "all",
                    "--output-dir", str(output_dir),
                    "-v"
                ],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, f"Failed: {result.stderr}"

            # Should have both pgTAP and pytest files
            sql_files = list(output_dir.glob("*.sql"))
            py_files = list(output_dir.glob("*.py"))

            assert len(sql_files) >= 2, f"Expected 2+ SQL files, got {len(sql_files)}"
            assert len(py_files) >= 1, f"Expected 1+ Python files, got {len(py_files)}"
```

**Run integration test**:
```bash
uv run pytest tests/integration/test_test_generation_workflow.py -v
```

#### Task 1.4.3: Create Usage Examples Doc (30 min)

Create `docs/06_examples/simple_contact/TEST_GENERATION_EXAMPLES.md`:

```markdown
# Test Generation Examples

This directory contains examples of generated tests for the Contact entity.

## Entity Definition

See [contact.yaml](contact.yaml) for the entity definition (15 lines).

## Generating Tests

### Generate All Tests

```bash
# Generate both pgTAP and pytest tests
specql generate-tests contact.yaml --output-dir generated_tests/

# Output:
# generated_tests/
# ├── test_contact_structure.sql    (50 lines, 10 tests)
# ├── test_contact_crud.sql         (100 lines, 15 tests)
# ├── test_contact_actions.sql      (80 lines, 12 tests)
# └── test_contact_integration.py   (150 lines, 18 tests)
```

### Generate Only pgTAP Tests

```bash
specql generate-tests contact.yaml --type pgtap --output-dir tests/pgtap/
```

### Generate Only pytest Tests

```bash
specql generate-tests contact.yaml --type pytest --output-dir tests/integration/
```

### Preview Mode

```bash
# See what would be generated without writing files
specql generate-tests contact.yaml --preview
```

## Running Generated Tests

### Run pgTAP Tests

```bash
# Install pgTAP extension
psql -d your_db -c "CREATE EXTENSION IF NOT EXISTS pgtap;"

# Run tests
pg_prove -d your_db generated_tests/test_contact_*.sql
```

### Run pytest Tests

```bash
# Install pytest and dependencies
pip install pytest psycopg[binary]

# Run tests
pytest generated_tests/test_contact_integration.py -v
```

## What Gets Tested?

### Structure Tests (test_contact_structure.sql)
- Table existence: `tb_contact`
- Required columns: pk_contact, id, identifier, email, status
- Column types and constraints
- Primary key constraint
- Unique constraints
- Audit columns: created_at, updated_at, deleted_at

### CRUD Tests (test_contact_crud.sql)
- Create contact (happy path)
- Create duplicate (error case)
- Read/lookup contact
- Update contact
- Delete contact (soft delete)
- Record persistence in database

### Action Tests (test_contact_actions.sql)
- qualify_lead action (happy path)
- qualify_lead with invalid status (error case)
- State transitions
- Action validation

### Integration Tests (test_contact_integration.py)
- Full CRUD workflow
- Duplicate detection
- Action execution
- Error handling
- Database cleanup fixtures

## Customizing Generated Tests

You can customize the generated tests by:

1. **Modifying after generation** - Edit the generated files
2. **Using as templates** - Copy and adapt for similar entities
3. **Extending with additional tests** - Add your custom test cases

## Next Steps

- Read the [Test Generation Guide](../../02_guides/TEST_GENERATION.md)
- Learn about [Test Reverse Engineering](../../02_guides/TEST_REVERSE_ENGINEERING.md)
- See [CI/CD Integration Guide](../../02_guides/CI_CD_INTEGRATION.md)
```

### Success Criteria

- [ ] Integration tests pass
- [ ] Manual workflow with Contact entity works
- [ ] Generated SQL is syntactically valid
- [ ] Generated Python is syntactically valid
- [ ] Examples documentation created
- [ ] All files committed

### Deliverables

1. Integration test `tests/integration/test_test_generation_workflow.py`
2. Examples doc `docs/06_examples/simple_contact/TEST_GENERATION_EXAMPLES.md`
3. Validated workflow with Contact entity

---

## Week 1 Completion Checklist

### Functionality
- [ ] `specql reverse-tests test.sql --preview` works without errors
- [ ] `specql generate-tests entities/contact.yaml` generates tests
- [ ] `specql generate-tests --type pgtap` generates only SQL
- [ ] `specql generate-tests --type pytest` generates only Python
- [ ] `specql generate-tests --type all` generates both
- [ ] Both commands appear in `specql --help`

### Quality
- [ ] All unit tests pass (2,937+ existing + ~30 new)
- [ ] All integration tests pass
- [ ] Code coverage >80% for new CLI code
- [ ] No ruff linting errors
- [ ] No mypy type errors
- [ ] Generated SQL is valid
- [ ] Generated Python is valid

### Documentation
- [ ] README has "Automated Testing" section
- [ ] README example shows test generation
- [ ] CLI help text updated
- [ ] Basic examples documented
- [ ] Demo GIF created

### Git
- [ ] All changes committed
- [ ] Commit message follows template (see below)
- [ ] No uncommitted changes

---

## Week 1 Git Commit

After completing all phases, commit with:

```bash
git add -A
git commit -m "feat: make test generation features discoverable

Week 1 Complete: CLI integration and basic documentation

Phase 1.1: Fixed reverse-tests Command
- Fixed exit code handling in reverse_tests.py
- Removed unexpected prompts
- Added helper functions for parsing and output
- Tests: tests/cli/test_reverse_tests_command.py

Phase 1.2: Created generate-tests Command
- New CLI command: src/cli/generate_tests.py (~400 lines)
- Generates pgTAP tests (structure, CRUD, actions)
- Generates pytest tests (integration tests)
- Options: --type (all/pgtap/pytest), --output-dir, --preview
- Tests: tests/cli/test_generate_tests_command.py

Phase 1.3: Updated CLI Help & README
- Updated main CLI docstring with Testing section
- Added Automated Testing section to README
- Example: 15 lines YAML → 70+ tests
- Created demo GIF

Phase 1.4: Integration Testing & Examples
- Integration test: tests/integration/test_test_generation_workflow.py
- Examples: docs/06_examples/simple_contact/TEST_GENERATION_EXAMPLES.md
- Validated with Contact entity from docs

Commands now working:
  specql generate-tests entities/contact.yaml
  specql generate-tests entities/*.yaml --type pgtap
  specql generate-tests entities/*.yaml --type pytest
  specql reverse-tests test.sql --preview
  specql reverse-tests test.sql --entity=Contact --output-dir=specs/

Statistics:
- New code: ~800 lines (CLI + helpers)
- New tests: ~400 lines (unit + integration)
- Documentation: ~200 lines (README + examples)
- All 2,937+ existing tests passing
- 30+ new tests passing

Related: docs/implementation_plans/v0.5.0_beta/WEEK_01_DISCOVERABLE.md
Next: Week 2 - Comprehensive Documentation
"
```

---

## Next Steps

After completing Week 1:

1. **Test the commands** with real projects
2. **Gather feedback** from team/users
3. **Move to Week 2**: [WEEK_02_DOCUMENTATION.md](WEEK_02_DOCUMENTATION.md)
   - Write comprehensive guides
   - Create detailed examples
   - Record demonstration videos

**Week 1 Goal Achieved**: ✅ Users can discover and use test generation features!
