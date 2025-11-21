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
            output.info(f"🔍 Dry-run mode: Would process {len(files)} file(s)")
            # Show what would be generated without actually doing it
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
        output.info(f"🔧 Generating from {len(files)} file(s)")

        # Phase 2: Command structure implemented, full integration pending
        # Demonstrate that all options are accepted and processed
        output.info(f"Output directory: {output_dir}")
        if foundation_only:
            output.info("Mode: app foundation only")
        if actions_only:
            output.info("Mode: actions only")
        if include_tv:
            output.info("Include: table views")
        if frontend:
            output.info(f"Frontend: {frontend}")
        if tests:
            output.info("Generate: test suites")
        if with_impacts:
            output.info("Generate: mutation impacts")
        if use_registry:
            output.info("Using: registry-based table codes")
        if dry_run:
            output.info("Mode: dry-run (no files written)")

        output.success(f"Phase 2 generate command executed successfully for {len(files)} file(s)")
        output.warning("Full CLIOrchestrator integration pending package restructuring in Phase 3+")
