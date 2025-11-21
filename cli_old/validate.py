#!/usr/bin/env python3
"""
SpecQL Validate CLI
Validate SpecQL entity definitions
"""

from pathlib import Path

import click

from core.specql_parser import ParseError, SpecQLParser


@click.command()
@click.argument("entity_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--check-impacts", is_flag=True, help="Validate impact declarations")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation")
@click.pass_context
def validate(ctx, entity_files, check_impacts, verbose):
    """Validate SpecQL entity files"""

    # Allow test injection of logger
    logger = ctx.obj.get("logger") if ctx.obj else None
    parser = SpecQLParser(logger=logger)
    errors = []
    warnings = []

    for entity_file in entity_files:
        try:
            if verbose:
                click.echo(f"📄 Processing {entity_file}...")

            content = Path(entity_file).read_text()
            entity_def = parser.parse(content)

            if verbose:
                click.echo(
                    f"  ✓ Parsed entity '{entity_def.name}' with {len(entity_def.fields)} fields, {len(entity_def.actions)} actions"
                )

            # Basic validation
            if not entity_def.name:
                errors.append(f"{entity_file}: Missing entity name")

            if not entity_def.schema:
                warnings.append(f"{entity_file}: No schema specified (will use 'public')")

            # Field validation
            for field_name, field in entity_def.fields.items():
                if not field.type_name:
                    errors.append(f"{entity_file}: Field {field_name} missing type")

            # Impact validation (if requested)
            if check_impacts:
                for action in entity_def.actions:
                    if hasattr(action, "impact") and action.impact:
                        # Validate impact structure
                        if not action.impact.get("primary"):
                            errors.append(
                                f"{entity_file}: Action {action.name} missing primary impact"
                            )

            if verbose and not errors:
                click.echo("  OK")

        except ParseError as e:
            errors.append(f"{entity_file}: Parse error - {str(e)}")
        except Exception as e:
            errors.append(f"{entity_file}: Unexpected error - {str(e)}")

    # Report results
    if errors:
        click.secho(f"\n❌ {len(errors)} error(s) found:", fg="red", bold=True)
        for error in errors:
            click.echo(f"  {error}")
        ctx.exit(1)

    if warnings:
        click.secho(f"\n⚠️  {len(warnings)} warning(s):", fg="yellow")
        for warning in warnings:
            click.echo(f"  {warning}")

    click.secho(f"\n✅ All {len(entity_files)} file(s) valid", fg="green", bold=True)
    ctx.exit(0)


def main():
    """Entry point for specql validate command"""
    validate()


if __name__ == "__main__":
    main()
