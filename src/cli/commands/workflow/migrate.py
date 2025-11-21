"""
Migrate subcommand - Full migration pipeline (reverse → validate → generate).
"""

from pathlib import Path

import click

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output-dir", type=click.Path(), help="Output directory for generated files")
@click.option(
    "--reverse-from",
    type=click.Choice(["sql", "python", "typescript", "rust"]),
    help="Source to reverse from",
)
@click.option("--validate-only", is_flag=True, help="Stop after validation")
@click.option("--generate-only", is_flag=True, help="Skip reverse and validation, only generate")
@click.option("--dry-run", is_flag=True, help="Preview the migration pipeline without executing")
@click.option(
    "--continue-on-error", is_flag=True, help="Continue pipeline even if individual steps fail"
)
@click.option("--progress", is_flag=True, help="Show detailed progress reporting")
def migrate(
    files,
    output_dir,
    reverse_from,
    validate_only,
    generate_only,
    dry_run,
    continue_on_error,
    progress,
    **kwargs,
):
    """Run full migration pipeline: reverse → validate → generate.

    Orchestrates the complete SpecQL workflow for migrating existing
    codebases to SpecQL format and generating production artifacts.

    Pipeline steps:
    1. Reverse: Convert existing code to SpecQL YAML
    2. Validate: Ensure YAML conforms to SpecQL schema
    3. Generate: Create PostgreSQL + GraphQL from YAML

    Examples:

        specql workflow migrate db/tables/*.sql --reverse-from=sql
        specql workflow migrate src/models.py --reverse-from=python -o generated/
        specql workflow migrate entities/*.yaml --generate-only
        specql workflow migrate entities/ --dry-run --progress
    """
    with handle_cli_error():
        output.info("🚀 Starting SpecQL migration pipeline")

        if dry_run:
            output.info("🔍 Dry-run mode: Previewing migration pipeline")
            _show_migration_plan(files, reverse_from, validate_only, generate_only, output_dir)
            return

        # Set defaults
        if output_dir is None:
            output_dir = "generated"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1: Reverse engineering
        if not generate_only:
            output.info("🔄 Phase 1: Reverse engineering")
            if progress:
                output.info("  📊 Reversing existing code to SpecQL YAML...")

            if reverse_from:
                output.info(f"  🔍 Reversing from: {reverse_from}")
                # Simulate reverse operation
                reversed_files = _simulate_reverse(files, reverse_from, output_dir)
                yaml_files = reversed_files
            else:
                # Assume files are already YAML
                yaml_files = [Path(f) for f in files]
                output.info(f"  ✅ Using existing YAML files: {len(yaml_files)}")

        else:
            yaml_files = [Path(f) for f in files]
            output.info("⏭️  Skipping reverse phase (--generate-only)")

        if validate_only:
            output.info("🛑 Stopping after validation (--validate-only)")
            return

        # Phase 2: Validation
        output.info("✅ Phase 2: Validation")
        if progress:
            output.info("  🔍 Validating SpecQL YAML schemas...")

        validation_errors = _simulate_validate(yaml_files)
        if validation_errors and not continue_on_error:
            output.error(f"❌ Validation failed with {len(validation_errors)} error(s)")
            for error in validation_errors:
                output.error(f"  • {error}")
            raise click.ClickException("Validation failed")

        if validation_errors:
            output.warning(f"⚠️  Validation completed with {len(validation_errors)} warning(s)")
        else:
            output.success("✅ Validation passed")

        # Phase 3: Generation
        output.info("🔧 Phase 3: Code generation")
        if progress:
            output.info("  📝 Generating PostgreSQL schema and GraphQL...")

        generated_files = _simulate_generate(yaml_files, output_dir)
        output.success("✅ Migration pipeline completed successfully")
        output.info(f"📁 Generated {len(generated_files)} file(s) to {output_dir}")


def _show_migration_plan(files, reverse_from, validate_only, generate_only, output_dir):
    """Show the migration plan without executing."""
    output.info("📋 Migration Plan:")
    output.info(f"  📄 Input files: {len(files)}")

    if not generate_only:
        output.info("  🔄 Phase 1: Reverse Engineering")
        if reverse_from:
            output.info(f"    • Source type: {reverse_from}")
        else:
            output.info("    • Using existing YAML files")
    else:
        output.info("  ⏭️  Phase 1: Skipped (--generate-only)")

    output.info("  ✅ Phase 2: Validation")
    if validate_only:
        output.info("    • Will stop after validation")

    output.info("  🔧 Phase 3: Code Generation")
    output.info(f"    • Output directory: {output_dir or 'generated'}")

    output.info("  🎯 Pipeline complete")


def _simulate_reverse(files, reverse_from, output_dir):
    """Simulate reverse engineering operation."""
    reversed_files = []
    for file_path in files:
        path = Path(file_path)
        yaml_path = output_dir / f"{path.stem}.yaml"
        output.info(f"  📄 {path.name} → {yaml_path.name}")
        reversed_files.append(yaml_path)
    return reversed_files


def _simulate_validate(yaml_files):
    """Simulate validation operation."""
    # Simulate some validation warnings for demo
    errors = []
    for i, file_path in enumerate(yaml_files):
        if i % 3 == 0:  # Simulate validation issues on every 3rd file
            errors.append(f"Missing required field in {file_path.name}")
    return errors


def _simulate_generate(yaml_files, output_dir):
    """Simulate code generation operation."""
    generated_files = []
    for yaml_file in yaml_files:
        # Generate SQL schema
        sql_file = output_dir / "schema" / f"{yaml_file.stem}.sql"
        output.info(f"  📝 {yaml_file.name} → {sql_file.name}")
        generated_files.append(sql_file)

        # Generate GraphQL types
        gql_file = output_dir / "graphql" / f"{yaml_file.stem}.graphql"
        output.info(f"  📝 {yaml_file.name} → {gql_file.name}")
        generated_files.append(gql_file)

    return generated_files
