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


@specql.command("check-codes")
@click.argument("entity_files", nargs=-1, required=True)
@click.option(
    "--format", type=click.Choice(["text", "json", "csv"]), default="text", help="Output format"
)
@click.option("--export", type=click.Path(), help="Export results to file")
@click.pass_context
def check_codes(ctx, entity_files, format, export):
    """Check uniqueness of table codes across entity files.

    ENTITY_FILES can be file paths or glob patterns (e.g., entities/*.yaml, entities/**/*.yaml)

    Examples:
        specql check-codes entities/*.yaml
        specql check-codes entities/**/*.yaml --format json
        specql check-codes entities/ --export results.json
    """
    from src.cli.commands.check_codes import check_table_code_uniqueness
    from pathlib import Path
    import glob
    import json
    import csv

    # Expand glob patterns and convert to Path objects
    file_paths = []
    for pattern in entity_files:
        if "*" in pattern or "?" in pattern:
            # It's a glob pattern
            matches = glob.glob(pattern, recursive=True)
            file_paths.extend(Path(f) for f in matches if f.endswith(".yaml") or f.endswith(".yml"))
        else:
            # It's a direct path
            path = Path(pattern)
            if path.is_file() and (path.suffix in [".yaml", ".yml"]):
                file_paths.append(path)
            elif path.is_dir():
                # If it's a directory, find all YAML files in it
                file_paths.extend(path.glob("**/*.yaml"))
                file_paths.extend(path.glob("**/*.yml"))

    # Filter to only existing files
    file_paths = [f for f in file_paths if f.exists()]

    if not file_paths:
        click.secho("❌ No YAML files found", fg="red")
        ctx.exit(1)

    duplicates = check_table_code_uniqueness(file_paths)

    # Calculate total unique codes found
    all_codes = set()
    for entity_file in file_paths:
        try:
            from src.core.specql_parser import SpecQLParser

            parser = SpecQLParser()
            content = entity_file.read_text()
            entity_def = parser.parse(content)
            if entity_def.organization and entity_def.organization.table_code:
                all_codes.add(entity_def.organization.table_code)
        except Exception:
            pass  # Skip files that can't be parsed

    # Prepare results
    results = {
        "total_files": len(file_paths),
        "total_codes": len(all_codes),
        "duplicates": duplicates,
        "success": len(duplicates) == 0,
    }

    # Display results
    if format == "json":
        click.echo(json.dumps(results, indent=2))
    elif format == "csv":
        writer = csv.writer(click.get_text_stream("stdout"))
        writer.writerow(["code", "entity"])
        for code, entities in duplicates.items():
            for entity in entities:
                writer.writerow([code, entity])
    else:  # text format
        if duplicates:
            click.secho("❌ Table code uniqueness check FAILED", fg="red", bold=True)
            click.secho("\n🔴 Duplicate Codes:", fg="red", bold=True)

            for code, entities in duplicates.items():
                click.secho(f"\n  Code: {code}", fg="red")
                for entity in entities:
                    click.echo(f"    - {entity}")

            click.secho(f"\n❌ Fix duplicates before running 'specql generate'", fg="red")
            ctx.exit(1)
        else:
            click.secho("✅ Table code uniqueness check PASSED", fg="green", bold=True)
            click.secho(f"\n📊 Summary:", fg="blue")
            click.echo(f"   Total files scanned: {results['total_files']}")
            click.echo(f"   Unique codes found: {results['total_codes']}")
            click.echo(f"   Duplicate codes: {len(duplicates)}")
            click.secho("\nAll table codes are unique! 🎉", fg="green")
            ctx.exit(0)

    # Export if requested (only for non-text formats)
    if export:
        export_path = Path(export)
        if format == "json":
            with open(export_path, "w") as f:
                json.dump(results, f, indent=2)
        elif format == "csv":
            with open(export_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["code", "entity"])
                for code, entities in duplicates.items():
                    for entity in entities:
                        writer.writerow([code, entity])
        click.echo(f"📄 Results exported to: {export_path}")


if __name__ == "__main__":
    specql()
