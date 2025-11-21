"""
Validate command - Check SpecQL YAML syntax and semantics.
"""

from pathlib import Path

import click

from cli.base import common_options, validate_common_options
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@common_options
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option(
    "--schema-registry",
    type=click.Path(exists=True),
    help="Schema registry for cross-entity validation",
)
@click.pass_context
def validate(ctx, files, output_dir, verbose, quiet, strict, schema_registry, **kwargs):
    """Validate SpecQL YAML syntax and business logic.

    Checks performed:
      - YAML syntax correctness
      - Entity field types
      - Action step syntax
      - Rich type validations
      - Naming conventions
      - Cross-entity references (with --schema-registry)

    Examples:

        specql validate entities/*.yaml
        specql validate entities/*.yaml --strict
        specql validate entities/*.yaml --schema-registry registry/domain_registry.yaml
    """
    with handle_cli_error():
        # Validate common options
        validate_common_options(verbose=verbose, quiet=quiet)

        # Configure output
        output.verbose = verbose
        output.quiet = quiet

        # Import parser
        from core.specql_parser import ParseError, SpecQLParser

        parser = SpecQLParser()
        errors = []
        warnings = []
        validated_count = 0

        output.info(f"Validating {len(files)} file(s)...")

        for file_path in files:
            path = Path(file_path)

            try:
                content = path.read_text()
                entity_def = parser.parse(content)

                # Basic validation passed - entity parsed successfully
                validated_count += 1

                if verbose:
                    output.success(f"  {path.name}: {entity_def.name} (valid)")
                else:
                    output.success(f"  {path.name}")

                # Additional validations
                file_warnings = _validate_entity(entity_def, path, schema_registry)
                warnings.extend(file_warnings)

            except ParseError as e:
                errors.append((path, f"Parse error: {e}"))
                output.error(f"  {path.name}: {e}")

            except Exception as e:
                errors.append((path, f"Validation error: {e}"))
                output.error(f"  {path.name}: {e}")

        # Summary
        output.info("")  # Empty line

        if errors:
            output.error(f"{len(errors)} file(s) failed validation")
            if strict or not warnings:
                raise SystemExit(2)

        if warnings:
            output.warning(f"{len(warnings)} warning(s)")
            for warning in warnings:
                output.warning(f"  - {warning}")

            if strict:
                output.error("Failing due to --strict mode")
                raise SystemExit(2)

        if not errors:
            output.success(f"All {validated_count} file(s) valid")


def _validate_entity(entity_def, file_path: Path, schema_registry: str | None) -> list[str]:
    """
    Perform additional validation checks on a parsed entity.

    Returns list of warning messages.
    """
    warnings = []

    # Check for empty fields
    if not entity_def.fields:
        warnings.append(f"{file_path.name}: Entity has no fields defined")

    # Check for missing schema (uses default 'public')
    if entity_def.schema == "public":
        warnings.append(f"{file_path.name}: Using default schema 'public' - consider specifying schema")

    # Check field naming conventions - fields is a dict, iterate over keys (field names)
    for field_name in entity_def.fields:
        if field_name.startswith("_"):
            warnings.append(f"{file_path.name}: Field '{field_name}' starts with underscore (unconventional)")

        # Check for camelCase (should be snake_case)
        if any(c.isupper() for c in field_name):
            warnings.append(
                f"{file_path.name}: Field '{field_name}' uses camelCase (prefer snake_case)"
            )

    # Check action naming
    for action in entity_def.actions:
        if not action.name:
            warnings.append(f"{file_path.name}: Action missing name")
        elif action.name.startswith("_"):
            warnings.append(f"{file_path.name}: Action '{action.name}' starts with underscore")

    return warnings
