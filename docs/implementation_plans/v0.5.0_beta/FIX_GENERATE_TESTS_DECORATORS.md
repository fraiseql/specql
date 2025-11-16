# URGENT FIX: Restore generate_tests Decorators

**Issue**: The `generate_tests` function in `src/cli/generate_tests.py` is missing its Click decorators
**Impact**: CRITICAL - Command registered as plain function instead of Click Command
**Time to Fix**: 2 minutes

---

## Problem

The `generate_tests` function (line 157-159) is currently:

```python
def generate_tests() -> int:
    click.echo("generate-tests command")
    return 0
```

This is just a stub - the decorators and proper implementation are missing!

## Root Cause

During editing, the Click decorators (@click.command(), @click.argument(), @click.option()) were accidentally removed, leaving just a stub function.

## Fix

Replace lines 157-159 with the proper decorated function:

```python
@click.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "--type",
    "test_type",
    type=click.Choice(["all", "pgtap", "pytest"], case_sensitive=False),
    default="all",
    help="Type of tests to generate (default: all)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="tests",
    help="Output directory for generated tests (default: tests/)",
)
@click.option(
    "--preview",
    is_flag=True,
    help="Preview mode - show what would be generated without writing files",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed generation progress")
@click.option("--overwrite", is_flag=True, help="Overwrite existing test files")
def generate_tests(
    entity_files: tuple[str, ...],
    test_type: str,
    output_dir: str,
    preview: bool,
    verbose: bool,
    overwrite: bool,
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
    return _generate_tests_core(
        entity_files=entity_files,
        test_type=test_type,
        output_dir=output_dir,
        preview=preview,
        verbose=verbose,
        overwrite=overwrite,
    )
```

## Verification

After fix:

```bash
# Should work without errors
uv run specql --help
uv run specql generate-tests --help

# Should show proper help text
uv run specql generate-tests --help | grep "Generate test files"
```

## Quick Fix Script

```bash
# Create backup
cp src/cli/generate_tests.py src/cli/generate_tests.py.backup

# The decorators need to be added before line 157
```

---

**This must be fixed before the CLI will work!**
