#!/usr/bin/env python3
"""
SpecQL Docs CLI
Generate documentation from SpecQL entity definitions
"""

from pathlib import Path
from typing import Any

import click

from src.cli.generate import convert_entity_definition_to_entity
from src.core.specql_parser import SpecQLParser


def generate_markdown_docs(entities: list[dict[str, Any]], output_file: str) -> None:
    """Generate markdown documentation for entities."""
    content = ["# SpecQL Entity Documentation\n"]

    for entity_data in entities:
        entity_def = entity_data["definition"]

        content.append(f"## {entity_def.name}\n")
        content.append(f"**Schema:** {entity_def.schema}\n")
        if entity_def.description:
            content.append(f"**Description:** {entity_def.description}\n")

        content.append("### Fields\n")
        content.append("| Field | Type | Required | Description |")
        content.append("|-------|------|----------|-------------|")

        for field_name, field in entity_def.fields.items():
            required = "Yes" if not field.nullable else "No"
            content.append(
                f"| {field_name} | {field.type_name} | {required} | {field.description or ''} |"
            )

        content.append("")

        if entity_def.actions:
            content.append("### Actions\n")
            for action in entity_def.actions:
                content.append(f"#### {action.name}")
                if hasattr(action, "description") and action.description:
                    content.append(f"**Description:** {action.description}")
                content.append("")

                if hasattr(action, "steps") and action.steps:
                    content.append("**Steps:**")
                    for i, step in enumerate(action.steps, 1):
                        content.append(f"{i}. {step.get('type', 'unknown')}")
                    content.append("")

                if hasattr(action, "impact") and action.impact:
                    content.append("**Impact:**")
                    impact = action.impact
                    if "primary" in impact:
                        primary = impact["primary"]
                        content.append(
                            f"- **Primary:** {primary.get('entity', '')}.{primary.get('operation', '')}"
                        )
                    if "sideEffects" in impact:
                        content.append("- **Side Effects:**")
                        for side_effect in impact["sideEffects"]:
                            content.append(
                                f"  - {side_effect.get('entity', '')}.{side_effect.get('operation', '')}"
                            )
                    content.append("")

        content.append("---\n")

    # Write to file
    Path(output_file).write_text("\n".join(content))


def generate_html_docs(entities: list[dict[str, Any]], output_dir: str) -> None:
    """Generate HTML documentation for entities."""
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate index.html
    index_content = """<!DOCTYPE html>
<html>
<head>
    <title>SpecQL Entity Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2, h3 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .entity { margin-bottom: 40px; }
        .field-required { color: red; }
    </style>
</head>
<body>
    <h1>SpecQL Entity Documentation</h1>
"""

    for entity_data in entities:
        entity_def = entity_data["definition"]

        index_content += f"""
    <div class="entity">
        <h2>{entity_def.name}</h2>
        <p><strong>Schema:</strong> {entity_def.schema}</p>
"""
        if entity_def.description:
            index_content += (
                f"        <p><strong>Description:</strong> {entity_def.description}</p>\n"
            )

        index_content += """
        <h3>Fields</h3>
        <table>
            <tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr>
"""

        for field_name, field in entity_def.fields.items():
            required = "<span class='field-required'>Yes</span>" if not field.nullable else "No"
            index_content += f"            <tr><td>{field_name}</td><td>{field.type_name}</td><td>{required}</td><td>{field.description or ''}</td></tr>\n"

        index_content += "        </table>\n"

        if entity_def.actions:
            index_content += "        <h3>Actions</h3>\n"
            for action in entity_def.actions:
                index_content += f"        <h4>{action.name}</h4>\n"
                if hasattr(action, "description") and action.description:
                    index_content += (
                        f"        <p><strong>Description:</strong> {action.description}</p>\n"
                    )

                if hasattr(action, "steps") and action.steps:
                    index_content += "        <p><strong>Steps:</strong></p><ol>\n"
                    for step in action.steps:
                        index_content += f"            <li>{step.get('type', 'unknown')}</li>\n"
                    index_content += "        </ol>\n"

                if hasattr(action, "impact") and action.impact:
                    index_content += "        <p><strong>Impact:</strong></p>\n"
                    impact = action.impact
                    if "primary" in impact:
                        primary = impact["primary"]
                        index_content += f"        <p>- <strong>Primary:</strong> {primary.get('entity', '')}.{primary.get('operation', '')}</p>\n"
                    if "sideEffects" in impact:
                        index_content += "        <p>- <strong>Side Effects:</strong></p><ul>\n"
                        for side_effect in impact["sideEffects"]:
                            index_content += f"            <li>{side_effect.get('entity', '')}.{side_effect.get('operation', '')}</li>\n"
                        index_content += "        </ul>\n"

        index_content += "    </div>\n"

    index_content += """
</body>
</html>
"""

    (output_path / "index.html").write_text(index_content)


@click.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "html"]),
    default="markdown",
    help="Output format",
)
@click.option("--output", "-o", required=True, help="Output file (markdown) or directory (html)")
def docs(entity_files, format, output):
    """Generate documentation from SpecQL entity files.

    Examples:
        specql docs entities/*.yaml --format=markdown --output=docs/entities.md
        specql docs entities/*.yaml --format=html --output=docs/
    """

    if not entity_files:
        click.echo("❌ No entity files specified", err=True)
        return

    try:
        parser = SpecQLParser()
        entities = []

        # Parse all entities
        for entity_file in entity_files:
            content = Path(entity_file).read_text()
            entity_def = parser.parse(content)
            entity = convert_entity_definition_to_entity(entity_def)

            entities.append({"definition": entity_def, "entity": entity, "file": entity_file})

        # Generate documentation based on format
        if format == "markdown":
            generate_markdown_docs(entities, output)
            click.echo(f"✅ Generated markdown documentation: {output}")

        elif format == "html":
            generate_html_docs(entities, output)
            click.echo(f"✅ Generated HTML documentation: {output}/index.html")

        click.echo(f"📚 Documented {len(entities)} entities")

    except Exception as e:
        click.echo(f"❌ Error generating documentation: {e}", err=True)
        raise click.Abort()


def main():
    """Entry point for specql docs command"""
    docs()


if __name__ == "__main__":
    main()
