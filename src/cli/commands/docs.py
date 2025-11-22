"""
Docs command - Generate documentation from SpecQL YAML.

Generates comprehensive documentation including:
- Entity reference documentation
- Mutation/Action API reference
- Database schema documentation
- Pattern documentation
"""

from pathlib import Path

import click

from cli.base import common_options, validate_common_options
from cli.utils.error_handler import handle_cli_error


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "html", "json"]),
    default="markdown",
    help="Documentation output format",
)
@click.option(
    "--preview",
    is_flag=True,
    help="Preview without writing files",
)
@click.option(
    "--include-examples",
    is_flag=True,
    default=True,
    help="Include code examples in documentation",
)
@common_options
def docs(files, output, output_format, preview, include_examples, verbose, quiet, **kwargs):
    """Generate documentation from SpecQL YAML files.

    Creates comprehensive documentation including entity reference,
    mutation API docs, schema documentation, and pattern guides.

    Examples:

        specql docs entities/*.yaml -o docs/generated/

        specql docs entities/contact.yaml --format=html

        specql docs entities/*.yaml --preview
    """
    with handle_cli_error():
        validate_common_options(verbose=verbose, quiet=quiet)

        from cli.utils.output import output as cli_output

        cli_output.info(f"Generating documentation for {len(files)} file(s)")

        # Use default output directory if not specified
        output_dir = output or "docs/generated"

        # Parse entities
        from core.specql_parser import ParseError, SpecQLParser

        parser = SpecQLParser()
        entities = []

        for file_path in files:
            path = Path(file_path)
            cli_output.info(f"  Parsing: {path.name}")

            try:
                content = path.read_text()
                parsed = parser.parse(content)
                if parsed:
                    entities.append((parsed, path.name))
            except ParseError as e:
                cli_output.warning(f"    Failed to parse: {e}")
                continue
            except Exception as e:
                cli_output.warning(f"    Failed to parse: {e}")
                continue

        cli_output.info(f"  Found {len(entities)} entity/entities")

        if preview:
            cli_output.info("Preview mode - showing what would be generated:")
            cli_output.info("    index.md")
            for entity, source_file in entities:
                cli_output.info(f"    entities/{entity.name.lower()}.md")
            return

        # Create output structure
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / "entities").mkdir(exist_ok=True)

        # Generate documentation
        from cli.commands.docs_generators import DocsGenerator

        generator = DocsGenerator(
            output_format=output_format,
            include_examples=include_examples,
        )

        generated_files = generator.generate(entities, output_path)

        for file in generated_files:
            cli_output.success(f"    Created: {file}")

        cli_output.success(f"Generated {len(generated_files)} file(s)")
