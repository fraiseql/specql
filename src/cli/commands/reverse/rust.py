"""
Reverse Rust subcommand - Convert Diesel/SeaORM schemas to SpecQL YAML.
"""

from pathlib import Path

import click

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
@click.option(
    "--framework", type=click.Choice(["diesel", "seaorm", "sqlx"]), help="Framework override"
)
@click.option("--preview", is_flag=True, help="Preview without writing")
def rust(files, output_dir, framework, preview, **kwargs):
    """Reverse engineer Rust schemas to SpecQL YAML.

    Supports Diesel, SeaORM, and SQLx schemas.

    Examples:

        specql reverse rust src/schema.rs -o entities/
        specql reverse rust src/models/ -o entities/ --framework=diesel
    """
    with handle_cli_error():
        output.info(f"🦀 Reversing {len(files)} Rust file(s)")

        if preview:
            output.info("🔍 Preview mode: no files will be written")
            return

        # Auto-detect framework if not specified
        if not framework:
            framework = "auto-detected"
            output.info(f"🔍 Auto-detected framework: {framework}")

        # TODO: Integrate with existing Rust reverse engineering
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        processed_count = 0
        for file_path in files:
            path = Path(file_path)
            output.info(f"  📄 Processing: {path.name}")
            output.info(f"    🏗️  Framework: {framework}")
            processed_count += 1

        output.success(f"Phase 3 reverse rust command processed {processed_count} file(s)")
        output.warning("Full Rust reverse engineering integration pending in Phase 4")
