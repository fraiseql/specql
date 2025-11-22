"""
Diff command - Compare SpecQL YAML with existing SQL schema.
"""

from pathlib import Path

import click

from cli.base import common_options
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


@click.command()
@click.argument("yaml_file", type=click.Path(exists=True))
@click.option("--compare", required=True, type=click.Path(exists=True), help="SQL file to compare")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.option("--ignore-comments", is_flag=True, help="Ignore comment differences")
@common_options
def diff(yaml_file, compare, output_format, ignore_comments, **kwargs):
    """Compare SpecQL YAML with existing SQL schema.

    Examples:

        specql diff entities/contact.yaml --compare db/schema/contact.sql
    """
    with handle_cli_error():
        from core.specql_parser import SpecQLParser
        from generators.schema_orchestrator import SchemaOrchestrator

        # 1. Parse YAML and generate SQL
        parser = SpecQLParser()
        yaml_content = Path(yaml_file).read_text()
        entity_def = parser.parse(yaml_content)

        # Convert to Entity for generator
        from cli.orchestrator import convert_entity_definition_to_entity

        entity = convert_entity_definition_to_entity(entity_def)

        orchestrator = SchemaOrchestrator()
        generated_sql = orchestrator.table_gen.generate_table_ddl(entity)

        # 2. Read existing SQL
        existing_sql = Path(compare).read_text()

        # 3. Compare (simplified - could use difflib)
        import difflib

        if ignore_comments:
            # Strip comments
            generated_lines = [
                line for line in generated_sql.splitlines() if not line.strip().startswith("--")
            ]
            existing_lines = [
                line for line in existing_sql.splitlines() if not line.strip().startswith("--")
            ]
        else:
            generated_lines = generated_sql.splitlines()
            existing_lines = existing_sql.splitlines()

        diff_result = list(
            difflib.unified_diff(
                existing_lines,
                generated_lines,
                fromfile=str(compare),
                tofile=f"generated from {yaml_file}",
                lineterm="",
            )
        )

        if not diff_result:
            output.success("No differences found")
            return

        if output_format == "json":
            import json

            output.info(json.dumps({"differences": diff_result}))
        else:
            for line in diff_result:
                if line.startswith("+"):
                    output.success(line)
                elif line.startswith("-"):
                    output.error(line)
                else:
                    output.info(line)
