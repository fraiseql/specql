"""CLI command for reverse engineering Java code to SpecQL YAML."""

import click

# from ..reverse_engineering.java.java_parser import JavaParser


@click.command("java")
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for YAML files")
@click.option(
    "--framework",
    type=click.Choice(["jpa", "hibernate", "auto"]),
    default="auto",
    help="Java framework to parse",
)
@click.option("--preview", is_flag=True, help="Preview mode - do not write files")
def reverse_java(input_files, output_dir, framework, preview):
    """
    Reverse engineer Java source code to SpecQL YAML

    Examples:
        specql reverse java src/main/java/com/example/User.java
        specql reverse java src/**/*.java -o entities/
        specql reverse java src/**/*.java --framework jpa
        specql reverse java src/main/java/com/example/User.java --preview
    """
    click.echo("☕ Java → SpecQL Reverse Engineering\n")

    # Initialize parser and mapper
    # parser = JavaParser()  # TODO: Implement Java parser
    # mapper = UniversalASTMapper()
    click.echo("Java reverse engineering not yet implemented")
