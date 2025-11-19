"""CLI command for reverse engineering Rust code to SpecQL YAML."""

from pathlib import Path

import click

from ..reverse_engineering.rust_parser import RustParser
from ..reverse_engineering.universal_ast_mapper import UniversalASTMapper
from .reverse_common import ReverseEngineeringCLI


@click.command("rust")
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for YAML files")
@click.option(
    "--framework",
    type=click.Choice(["diesel", "seaorm", "auto"]),
    default="auto",
    help="Rust ORM framework to parse",
)
@click.option("--with-patterns", is_flag=True, help="Auto-detect and apply architectural patterns")
@click.option("--exclude", multiple=True, help="Exclude file patterns (e.g., */tests/*)")
@click.option("--recursive", is_flag=True, default=True, help="Recursively process directories")
@click.option("--preview", is_flag=True, help="Preview mode - do not write files")
@click.option("--no-cache", is_flag=True, help="Disable caching")
@click.option("--clear-cache", is_flag=True, help="Clear cache before processing")
def reverse_rust(
    input_files,
    output_dir,
    framework,
    with_patterns,
    exclude,
    recursive,
    preview,
    no_cache,
    clear_cache,
):
    """
    Reverse engineer Rust source code to SpecQL YAML

    Examples:
        specql reverse rust src/models/user.rs
        specql reverse rust src/models/*.rs -o entities/
        specql reverse rust src/models/*.rs --framework diesel
        specql reverse rust src/models/user.rs --preview
        specql reverse rust src/ --with-patterns --framework diesel
    """
    from .cache_manager import CacheManager

    if clear_cache:
        CacheManager().clear_cache()
        click.echo("✓ Cache cleared")
        return

    use_cache = not no_cache

    click.echo("🦀 Rust → SpecQL Reverse Engineering\n")

    # Check if this is project mode (directory input)
    if len(input_files) == 1 and Path(input_files[0]).is_dir():
        # Project mode
        ReverseEngineeringCLI.process_project(
            input_files[0],
            framework=framework if framework != "auto" else None,
            with_patterns=with_patterns,
            output_dir=output_dir or "entities/",
            exclude=list(exclude) if exclude else None,
            preview=preview,
            use_cache=use_cache,
        )
    else:
        # File mode (existing implementation)
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
