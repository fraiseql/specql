"""
Migrate subcommand - Full migration pipeline (reverse → validate → generate).
"""

from pathlib import Path

import click

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output
from cli.utils.pipeline import PipelineOrchestrator


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

        # Use the pipeline orchestrator
        orchestrator = PipelineOrchestrator()

        def progress_callback(message: str):
            if progress:
                output.info(f"  📊 {message}")
            else:
                output.info(message)

        result = orchestrator.run_pipeline(
            files=[Path(f) for f in files],
            reverse_from=reverse_from,
            output_dir=Path(output_dir) if output_dir else None,
            validate_only=validate_only,
            generate_only=generate_only,
            continue_on_error=continue_on_error,
            strict_validation=False,  # Could be made configurable later
            progress_callback=progress_callback,
        )

        if not result["success"]:
            if result["errors"]:
                for error in result["errors"]:
                    output.error(f"  • {error}")
            raise click.ClickException("Migration pipeline failed")


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
