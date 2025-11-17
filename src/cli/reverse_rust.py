"""CLI command for reverse engineering Rust code to SpecQL YAML."""

import click
from pathlib import Path

from .reverse_common import ReverseEngineeringCLI
from ..reverse_engineering.rust_parser import RustParser
from ..reverse_engineering.universal_ast_mapper import UniversalASTMapper


@click.command("rust")
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for YAML files")
@click.option(
    "--framework",
    type=click.Choice(["diesel", "seaorm", "auto"]),
    default="auto",
    help="Rust ORM framework to parse",
)
@click.option("--preview", is_flag=True, help="Preview mode - do not write files")
def reverse_rust(input_files, output_dir, framework, preview):
    """
    Reverse engineer Rust source code to SpecQL YAML

    Examples:
        specql reverse rust src/models/user.rs
        specql reverse rust src/models/*.rs -o entities/
        specql reverse rust src/models/*.rs --framework diesel
        specql reverse rust src/models/user.rs --preview
    """
    click.echo("🦀 Rust → SpecQL Reverse Engineering\n")

    # Initialize parser and mapper
    parser = RustParser()
    mapper = UniversalASTMapper()

    # Process files using common logic
    ReverseEngineeringCLI.process_files(
        input_files=input_files,
        output_dir=output_dir,
        parser=parser,
        mapper=mapper,
        preview=preview,
    )

    # Summary
    click.echo("\n📊 Summary:")
    click.echo(f"  ✅ Processed {len(input_files)} Rust files")

    if not preview and output_dir:
        click.echo(f"  📁 Output directory: {output_dir}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Review generated YAML: ls {output_dir}")
        click.echo(f"  2. Validate: specql validate {output_dir}/*.yaml")
        click.echo(f"  3. Generate schema: specql generate {output_dir}/*.yaml")
