"""CLI command for reverse engineering TypeScript code to SpecQL YAML."""


import click

from ..reverse_engineering.typescript_parser import TypeScriptParser
from ..reverse_engineering.universal_ast_mapper import UniversalASTMapper
from .reverse_common import ReverseEngineeringCLI


@click.command("typescript")
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for YAML files")
@click.option(
    "--framework",
    type=click.Choice(["express", "fastify", "nextjs", "prisma", "auto"]),
    default="auto",
    help="TypeScript framework to parse",
)
@click.option("--preview", is_flag=True, help="Preview mode - do not write files")
def reverse_typescript(input_files, output_dir, framework, preview):
    """
    Reverse engineer TypeScript source code to SpecQL YAML

    Examples:
        specql reverse typescript src/routes/user.ts
        specql reverse typescript src/**/*.ts -o entities/
        specql reverse typescript schema.prisma --framework prisma
        specql reverse typescript src/routes/user.ts --preview
    """
    click.echo("📘 TypeScript → SpecQL Reverse Engineering\n")

    # Initialize parser and mapper
    parser = TypeScriptParser()
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
    click.echo(f"  ✅ Processed {len(input_files)} TypeScript files")

    if not preview and output_dir:
        click.echo(f"  📁 Output directory: {output_dir}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Review generated YAML: ls {output_dir}")
        click.echo(f"  2. Validate: specql validate {output_dir}/*.yaml")
        click.echo(f"  3. Generate schema: specql generate {output_dir}/*.yaml")
