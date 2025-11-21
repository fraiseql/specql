"""
Generate command - Transform SpecQL YAML to PostgreSQL + GraphQL.
"""


import click

from cli.base import common_options, validate_common_options
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@common_options
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation")
@click.option("--actions-only", is_flag=True, help="Generate only action functions")
@click.option("--include-tv", is_flag=True, help="Generate table views")
@click.option("--frontend", type=click.Path(), help="Generate frontend code to directory")
@click.option("--tests", is_flag=True, help="Generate test suites")
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
@click.option("--use-registry", is_flag=True, help="Use hexadecimal registry for table codes")
@click.option(
    "--output-format",
    type=click.Choice(["hierarchical", "confiture"]),
    default="hierarchical",
    help="Output format: hierarchical or confiture",
)
@click.option("--with-impacts", is_flag=True, help="Generate mutation impacts JSON")
@click.option("--performance", is_flag=True, help="Enable performance monitoring")
@click.option("--performance-output", type=click.Path(), help="Write performance metrics to file")
@click.pass_context
def generate(
    ctx,
    files,
    output_dir,
    verbose,
    quiet,
    foundation_only,
    actions_only,
    include_tv,
    frontend,
    tests,
    dry_run,
    use_registry,
    output_format,
    with_impacts,
    performance,
    performance_output,
    **kwargs,
):
    """Generate PostgreSQL schema and functions from SpecQL YAML.

    Examples:

        specql generate entities/*.yaml
        specql generate contact.yaml --frontend=src/generated
        specql generate entities/*.yaml --dry-run
        specql generate entities/*.yaml --with-impacts --use-registry
    """
    with handle_cli_error():
        # Validate common options
        validate_common_options(verbose=verbose, quiet=quiet)

        # Configure output settings
        output.verbose = verbose
        output.quiet = quiet

        # Set default output directory
        if output_dir is None:
            output_dir = "migrations"

        if dry_run:
            output.info(f"Dry-run mode: Would process {len(files)} file(s)")
            output.info(f"Would generate to: {output_dir}")
            if foundation_only:
                output.info("Would generate: app foundation only")
            if actions_only:
                output.info("Would generate: actions only")
            if include_tv:
                output.info("Would generate: table views")
            if frontend:
                output.info(f"Would generate frontend code to: {frontend}")
            if tests:
                output.info("Would generate: test suites")
            if with_impacts:
                output.info("Would generate: mutation impacts")
            if use_registry:
                output.info("Would use: registry-based table codes")
            return

        # Show progress
        output.info(f"Generating from {len(files)} file(s)...")

        # Initialize the orchestrator
        from cli.orchestrator import CLIOrchestrator

        orchestrator = CLIOrchestrator(
            use_registry=use_registry,
            output_format=output_format,
            enable_performance_monitoring=performance,
        )

        # Generate migrations
        result = orchestrator.generate_from_files(
            entity_files=list(files),
            output_dir=output_dir,
            with_impacts=with_impacts,
            include_tv=include_tv,
            foundation_only=foundation_only,
        )

        # Report results
        if result.errors:
            for error in result.errors:
                output.error(f"  {error}")
            output.error(f"Generation failed with {len(result.errors)} error(s)")
            raise SystemExit(1)

        if result.warnings:
            for warning in result.warnings:
                output.warning(f"  {warning}")

        # Success summary
        output.success(f"Generated {len(result.migrations)} migration file(s)")
        for migration in result.migrations:
            if migration.path:
                output.info(f"  {migration.path}")

        # Write performance metrics if requested
        if performance and performance_output:
            from utils.performance_monitor import get_performance_monitor
            from pathlib import Path
            import json

            perf_monitor = get_performance_monitor()
            metrics = perf_monitor.get_metrics()
            Path(performance_output).write_text(json.dumps(metrics, indent=2))
