#!/usr/bin/env python3
"""
SpecQL Diff CLI
Show differences between entity definitions and existing migrations
"""

import difflib
from pathlib import Path

import click

from src.cli.generate import convert_entity_definition_to_entity
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator


def generate_entity_sql(entity_file: str) -> str:
    """Generate SQL for an entity file."""
    parser = SpecQLParser()
    orchestrator = SchemaOrchestrator()

    # Parse entity
    content = Path(entity_file).read_text()
    entity_def = parser.parse(content)

    # Convert to Entity for orchestrator
    entity = convert_entity_definition_to_entity(entity_def)

    # Generate schema
    return orchestrator.generate_complete_schema(entity)


def load_migration_sql(migration_file: str) -> str:
    """Load SQL from a migration file."""
    return Path(migration_file).read_text()


def colorize_diff(diff_lines: list[str]) -> str:
    """Colorize diff output using ANSI colors."""
    colored_lines = []

    for line in diff_lines:
        stripped_line = line.rstrip("\n")
        if stripped_line.startswith("+"):
            # Green for additions
            colored_lines.append(f"\x1b[32m{line}\x1b[0m")
        elif stripped_line.startswith("-"):
            # Red for deletions
            colored_lines.append(f"\x1b[31m{line}\x1b[0m")
        elif stripped_line.startswith("@@"):
            # Cyan for hunk headers
            colored_lines.append(f"\x1b[36m{line}\x1b[0m")
        else:
            # Default color for context
            colored_lines.append(line)

    return "\n".join(colored_lines)


@click.command()
@click.argument("entity_file", type=click.Path(exists=True))
@click.option(
    "--compare",
    "-c",
    "migration_file",
    type=click.Path(exists=True),
    help="Migration file to compare against",
)
@click.option("--color/--no-color", default=True, help="Enable/disable colored output")
@click.option("--context", "-C", default=3, help="Number of context lines")
@click.option(
    "--use-rust/--use-python",
    default=True,
    help="Use Confiture's Rust differ (faster) or Python difflib",
)
def diff(entity_file, migration_file, color, context, use_rust):
    """Show differences between entity definition and existing migration.

    If --compare is not specified, shows what would be generated vs current state.
    """

    try:
        # Generate SQL from entity
        entity_sql = generate_entity_sql(entity_file)

        if migration_file:
            # Compare against specific migration file
            migration_sql = load_migration_sql(migration_file)

            # Try Confiture's Rust differ first (10-50x faster)
            diff_output = None
            if use_rust:
                try:
                    from confiture.core.differ import SchemaDiffer  # type: ignore

                    differ = SchemaDiffer()
                    diff_result = differ.compare(migration_sql, entity_sql)

                    if not diff_result:
                        click.echo(f"✅ No differences between {entity_file} and {migration_file}")
                        return

                    # Confiture provides high-level schema analysis
                    click.echo("📋 Schema differences (Confiture analysis):")
                    click.echo(str(diff_result))

                    # Always show detailed diff with Python difflib for complete comparison
                    click.echo("\n📋 Detailed differences:")
                    use_rust = False  # Fall back to Python difflib for full diff

                except ImportError:
                    click.echo(
                        "⚠️  Confiture not available, falling back to Python difflib", err=True
                    )
                    use_rust = False
                except Exception as e:
                    click.echo(
                        f"⚠️  Confiture differ failed ({e}), falling back to Python difflib",
                        err=True,
                    )
                    use_rust = False

            # Fall back to Python difflib
            if not use_rust or diff_output is None:
                diff_lines = difflib.unified_diff(
                    migration_sql.splitlines(keepends=True),
                    entity_sql.splitlines(keepends=True),
                    fromfile=f"a/{migration_file}",
                    tofile=f"b/{entity_file}",
                    n=context,
                    lineterm="",
                )

                diff_lines_list = list(diff_lines)
                diff_output = "".join(diff_lines_list)

                if not diff_output.strip():
                    click.echo(f"✅ No differences between {entity_file} and {migration_file}")
                    return

                if color:
                    diff_output = colorize_diff(diff_lines_list)

            click.echo(f"📋 Differences between {entity_file} and {migration_file}:")
            click.echo(diff_output)

        else:
            # Show what would be generated
            click.echo(f"📄 Generated SQL for {entity_file}:")
            click.echo("=" * 60)
            click.echo(entity_sql)
            click.echo("=" * 60)
            click.echo(f"Size: {len(entity_sql)} bytes")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


def main():
    """Entry point for specql diff command"""
    diff()


if __name__ == "__main__":
    main()
