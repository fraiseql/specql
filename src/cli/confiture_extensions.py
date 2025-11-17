#!/usr/bin/env python3
"""
SpecQL Confiture Extensions
Extend Confiture CLI with SpecQL-specific commands
"""

from pathlib import Path

import click

from src.cli.orchestrator import CLIOrchestrator


@click.group()
def specql():
    """SpecQL commands for Confiture"""
    pass


@specql.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation")
@click.option("--include-tv", is_flag=True, help="Generate table views")
@click.option("--env", default="local", help="Confiture environment to use")
def generate(entity_files, foundation_only, include_tv, env):
    """Generate PostgreSQL schema from SpecQL YAML files"""

    # Create orchestrator (always use Confiture-compatible output now)
    orchestrator = CLIOrchestrator(use_registry=False, output_format="confiture")

    # Generate to db/schema/ (Confiture's expected location)
    result = orchestrator.generate_from_files(
        entity_files=list(entity_files),
        output_dir="db/schema",  # Changed from "migrations"
        foundation_only=foundation_only,
        include_tv=include_tv,
    )

    if result.errors:
        click.secho(f"❌ {len(result.errors)} error(s):", fg="red")
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

    # Success - now build with Confiture
    click.secho(f"✅ Generated {len(result.migrations)} schema file(s)", fg="green")

    if not foundation_only:
        click.echo("\nBuilding final migration with Confiture...")

        # Import Confiture here to avoid circular imports
        try:
            from confiture.core.builder import SchemaBuilder  # type: ignore

            builder = SchemaBuilder(env=env)
            builder.build()  # Let Confiture use its default output path

            output_path = Path(f"db/generated/schema_{env}.sql")
            click.secho(f"✅ Complete! Migration written to: {output_path}", fg="green", bold=True)
            click.echo("\nNext steps:")
            click.echo(f"  1. Review: cat {output_path}")
            click.echo(f"  2. Apply: confiture migrate up --env {env}")
            click.echo("  3. Status: confiture migrate status")

        except ImportError:
            click.secho("⚠️  Confiture not available, generated schema files only", fg="yellow")
            click.echo("Install confiture: uv add fraiseql-confiture")
        except Exception as e:
            click.secho(f"❌ Confiture build failed: {e}", fg="red")
            return 1

    return 0


@specql.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--check-impacts", is_flag=True, help="Validate impact declarations")
@click.option("--verbose", "-v", is_flag=True)
def validate(entity_files, check_impacts, verbose):
    """Validate SpecQL entity files"""
    # Reuse existing validate.py logic by running it as a subprocess
    import subprocess
    import sys

    cmd = [sys.executable, "-m", "src.cli.validate"] + list(entity_files)
    if check_impacts:
        cmd.append("--check-impacts")
    if verbose:
        cmd.append("--verbose")

    result = subprocess.run(cmd)
    return result.returncode


@specql.command(name="reverse")
@click.argument("sql_files", nargs=-1, type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for YAML files")
@click.option("--min-confidence", type=float, default=0.80, help="Minimum confidence threshold")
@click.option("--no-ai", is_flag=True, help="Skip AI enhancement (faster)")
@click.option("--preview", is_flag=True, help="Preview mode (no files written)")
@click.option("--compare", is_flag=True, help="Generate comparison report")
@click.option("--use-heuristics/--no-heuristics", default=True, help="Use heuristic enhancements")
def reverse_sql(sql_files, output_dir, min_confidence, no_ai, preview, compare, use_heuristics):
    """
    Reverse engineer SQL functions to SpecQL YAML

    Examples:
        specql reverse function.sql
        specql reverse reference_sql/**/*.sql -o entities/
        specql reverse function.sql --no-ai --preview
        specql reverse function.sql --min-confidence=0.90
    """
    # Import here to avoid circular imports
    from src.cli.reverse import reverse as reverse_cmd
    from click import Context

    # Create a click context and invoke the command
    ctx = Context(reverse_cmd)
    ctx.invoke(
        reverse_cmd,
        sql_files=sql_files,
        output_dir=output_dir,
        min_confidence=min_confidence,
        no_ai=no_ai,
        preview=preview,
        compare=compare,
        use_heuristics=use_heuristics
    )


@specql.command(name="reverse-python")
@click.argument("python_files", nargs=-1, type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), default="entities/", help="Output directory for YAML files")
@click.option("--discover-patterns", is_flag=True, help="Discover and save patterns to pattern library")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without writing files")
def reverse_python_cmd(python_files, output_dir, discover_patterns, dry_run):
    """
    Reverse engineer Python code (SQLAlchemy/Django) to SpecQL YAML

    Examples:
        specql reverse-python src/models/contact.py
        specql reverse-python src/models/*.py -o entities/
        specql reverse-python src/models/*.py --discover-patterns
    """
    from src.cli.reverse_python import reverse_python
    from click import Context

    ctx = Context(reverse_python)
    ctx.invoke(
        reverse_python,
        python_files=python_files,
        output_dir=output_dir,
        discover_patterns=discover_patterns,
        dry_run=dry_run
    )


if __name__ == "__main__":
    specql()
