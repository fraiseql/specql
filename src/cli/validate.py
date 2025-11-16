#!/usr/bin/env python3
"""
SpecQL Validate CLI
Validate SpecQL entity definitions with comprehensive checks
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import click

from src.core.specql_parser import SpecQLParser
from src.core.validation_limits import ValidationLimits
from src.core.ast_models import FieldTier


class ValidationResult:
    """Container for validation results"""

    def __init__(self):
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.files_processed = 0
        self.entities_found: Dict[str, str] = {}  # entity_name -> file_path

    def add_error(
        self,
        file_path: str,
        message: str,
        entity: Optional[str] = None,
        field: Optional[str] = None,
        action: Optional[str] = None,
        line: Optional[int] = None,
    ):
        """Add an error"""
        self.errors.append(
            {
                "file": str(file_path),
                "message": message,
                "entity": entity,
                "field": field,
                "action": action,
                "line": line,
                "severity": "error",
            }
        )

    def add_warning(
        self,
        file_path: str,
        message: str,
        entity: Optional[str] = None,
        field: Optional[str] = None,
        action: Optional[str] = None,
        line: Optional[int] = None,
    ):
        """Add a warning"""
        self.warnings.append(
            {
                "file": str(file_path),
                "message": message,
                "entity": entity,
                "field": field,
                "action": action,
                "line": line,
                "severity": "warning",
            }
        )

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


@click.command()
@click.argument("entity_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--check-impacts", is_flag=True, help="Validate impact declarations")
@click.option(
    "--check-references", is_flag=True, help="Validate cross-entity references"
)
@click.option("--check-naming", is_flag=True, help="Validate naming conventions")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "junit"]),
    default="text",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation")
@click.pass_context
def validate(
    ctx,
    entity_files,
    check_impacts,
    check_references,
    check_naming,
    strict,
    output_format,
    output,
    verbose,
):
    """Validate SpecQL entity files with comprehensive checks

    Performs thorough validation including:
    - YAML syntax and structure
    - Entity and field definitions
    - Type validation and constraints
    - Cross-entity references
    - Naming conventions
    - Action and impact validation

    Examples:
        specql validate entities/*.yaml
        specql validate entities/ --check-references --format json
        specql validate entities/ --strict --output validation.json
    """

    result = ValidationResult()
    parser = SpecQLParser()

    # Parse all entities first
    entities = {}
    for entity_file in entity_files:
        entity_path = Path(entity_file)
        result.files_processed += 1

        try:
            content = entity_path.read_text()
            entity_def = parser.parse(content)

            # Store entity for cross-reference validation
            entities[entity_def.name] = {"entity": entity_def, "file": entity_path}
            result.entities_found[entity_def.name] = str(entity_path)

            # Perform comprehensive validation
            validate_entity(
                result,
                entity_def,
                str(entity_path),
                check_impacts,
                check_naming,
                verbose,
            )

        except Exception as e:
            result.add_error(str(entity_path), f"Parse error: {str(e)}")

    # Cross-entity reference validation
    if check_references and entities:
        validate_cross_references(result, entities)

    # Output results
    if output_format == "json":
        output_json(result, output)
    elif output_format == "junit":
        output_junit(result, output)
    else:
        output_text(result, strict)

    # Exit with appropriate code
    if result.has_errors() or (strict and result.has_warnings()):
        ctx.exit(1)
    else:
        ctx.exit(0)


def validate_entity(
    result: ValidationResult,
    entity_def,
    entity_path: Path,
    check_impacts: bool,
    check_naming: bool,
    verbose: bool,
):
    """Validate a single entity"""

    # Basic entity validation
    if not entity_def.name:
        result.add_error(str(entity_path), "Missing entity name")
        return

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", entity_def.name):
        result.add_error(
            str(entity_path),
            f"Invalid entity name: '{entity_def.name}' (must match ^[a-zA-Z_][a-zA-Z0-9_]*$)",
            entity=entity_def.name,
        )

    # Schema validation
    if not entity_def.schema:
        result.add_warning(
            str(entity_path),
            "No schema specified (will use 'public')",
            entity=entity_def.name,
        )

    # Field validation
    field_names = set()
    for field_name, field in entity_def.fields.items():
        validate_field(
            result, entity_def, str(entity_path), field_name, field, check_naming
        )

        # Check for duplicate field names
        if field_name in field_names:
            result.add_error(
                str(entity_path),
                f"Duplicate field name: '{field_name}'",
                entity=entity_def.name,
                field=field_name,
            )
        field_names.add(field_name)

    # Field count validation
    try:
        ValidationLimits.validate_field_count(entity_def.name, len(entity_def.fields))
    except Exception as e:
        result.add_error(str(entity_path), str(e), entity=entity_def.name)

    # Action validation
    action_names = set()
    for action in entity_def.actions:
        validate_action(
            result, entity_def, str(entity_path), action, check_impacts, check_naming
        )

        # Check for duplicate action names
        if action.name in action_names:
            result.add_error(
                str(entity_path),
                f"Duplicate action name: '{action.name}'",
                entity=entity_def.name,
                action=action.name,
            )
        action_names.add(action.name)

    # Action count validation
    try:
        ValidationLimits.validate_action_count(entity_def.name, len(entity_def.actions))
    except Exception as e:
        result.add_error(str(entity_path), str(e), entity=entity_def.name)

    if verbose and not result.has_errors():
        click.secho(
            f"✓ {entity_path}: OK ({len(entity_def.fields)} fields, {len(entity_def.actions)} actions)",
            fg="green",
        )


def validate_field(
    result: ValidationResult,
    entity_def,
    entity_path: Path,
    field_name: str,
    field,
    check_naming: bool,
):
    """Validate a single field"""

    # Field name validation
    if not re.match(r"^[a-z_][a-z0-9_]*$", field_name):
        result.add_error(
            str(entity_path),
            f"Invalid field name: '{field_name}' (must match ^[a-z_][a-z0-9_]*$)",
            entity=entity_def.name,
            field=field_name,
        )

    if check_naming and field_name.upper() == field_name:
        result.add_warning(
            str(entity_path),
            f"Field name should be lowercase: '{field_name}'",
            entity=entity_def.name,
            field=field_name,
        )

    # Type validation
    if not field.type_name:
        result.add_error(
            str(entity_path),
            "Missing field type",
            entity=entity_def.name,
            field=field_name,
        )
        return

    # Check for reserved field names
    from src.core.reserved_fields import (
        is_reserved_field_name,
        get_reserved_field_error_message,
    )

    if is_reserved_field_name(field_name):
        result.add_error(
            str(entity_path),
            get_reserved_field_error_message(field_name),
            entity=entity_def.name,
            field=field_name,
        )

    # Type-specific validation
    if field.tier == FieldTier.REFERENCE:
        if not field.reference_entity:
            result.add_error(
                str(entity_path),
                "Reference field missing target entity",
                entity=entity_def.name,
                field=field_name,
            )
    elif field.values:
        # Enum field validation
        if not field.values:
            result.add_error(
                str(entity_path),
                "Enum field missing values",
                entity=entity_def.name,
                field=field_name,
            )
        elif field.default and field.default not in field.values:
            result.add_error(
                str(entity_path),
                f"Enum default value '{field.default}' not in allowed values: {field.values}",
                entity=entity_def.name,
                field=field_name,
            )


def validate_action(
    result: ValidationResult,
    entity_def,
    entity_path: Path,
    action,
    check_impacts: bool,
    check_naming: bool,
):
    """Validate a single action"""

    # Action name validation
    if not re.match(r"^[a-z_][a-z0-9_]*$", action.name):
        result.add_error(
            str(entity_path),
            f"Invalid action name: '{action.name}' (must match ^[a-z_][a-z0-9_]*$)",
            entity=entity_def.name,
            action=action.name,
        )

    if check_naming and action.name.upper() == action.name:
        result.add_warning(
            str(entity_path),
            f"Action name should be lowercase: '{action.name}'",
            entity=entity_def.name,
            action=action.name,
        )

    # Impact validation
    if check_impacts and hasattr(action, "impact") and action.impact:
        if not action.impact.get("primary"):
            result.add_error(
                str(entity_path),
                "Action missing primary impact declaration",
                entity=entity_def.name,
                action=action.name,
            )

    # Step count validation
    try:
        from src.core.validation_limits import ValidationLimits

        ValidationLimits.validate_steps_count(
            entity_def.name, action.name, len(action.steps)
        )
    except Exception as e:
        result.add_error(
            str(entity_path), str(e), entity=entity_def.name, action=action.name
        )


def validate_cross_references(result: ValidationResult, entities: Dict):
    """Validate cross-entity references"""

    for entity_name, entity_data in entities.items():
        entity_def = entity_data["entity"]
        entity_path = entity_data["file"]

        for field_name, field in entity_def.fields.items():
            if field.tier == field.tier.REFERENCE and field.reference_entity:
                if field.reference_entity not in entities:
                    result.add_error(
                        str(entity_path),
                        f"Referenced entity '{field.reference_entity}' not found",
                        entity=entity_name,
                        field=field_name,
                    )


def output_text(result: ValidationResult, strict: bool):
    """Output results in text format"""

    if result.has_errors():
        click.secho(f"\n❌ {len(result.errors)} error(s) found:", fg="red", bold=True)
        for error in result.errors:
            location = []
            if error.get("entity"):
                location.append(f"entity:{error['entity']}")
            if error.get("field"):
                location.append(f"field:{error['field']}")
            if error.get("action"):
                location.append(f"action:{error['action']}")
            location_str = f" ({', '.join(location)})" if location else ""
            click.echo(f"  {error['file']}{location_str}: {error['message']}")

    warning_count = len(result.warnings)
    if result.has_warnings():
        if strict:
            click.secho(
                f"\n❌ {warning_count} warning(s) treated as errors (--strict):",
                fg="red",
                bold=True,
            )
        else:
            click.secho(f"\n⚠️  {warning_count} warning(s):", fg="yellow")

        for warning in result.warnings:
            location = []
            if warning.get("entity"):
                location.append(f"entity:{warning['entity']}")
            if warning.get("field"):
                location.append(f"field:{warning['field']}")
            if warning.get("action"):
                location.append(f"action:{warning['action']}")
            location_str = f" ({', '.join(location)})" if location else ""
            click.echo(f"  {warning['file']}{location_str}: {warning['message']}")

    if not result.has_errors() and (not result.has_warnings() or not strict):
        click.secho(
            f"\n✅ Validation passed! {result.files_processed} file(s), {len(result.entities_found)} entities",
            fg="green",
            bold=True,
        )


def output_json(result: ValidationResult, output_file: Optional[str]):
    """Output results in JSON format"""

    output_data = {
        "summary": {
            "files_processed": result.files_processed,
            "entities_found": len(result.entities_found),
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "success": not result.has_errors(),
        },
        "errors": result.errors,
        "warnings": result.warnings,
        "entities": result.entities_found,
    }

    json_output = json.dumps(output_data, indent=2)

    if output_file:
        Path(output_file).write_text(json_output)
        click.echo(f"Results written to: {output_file}")
    else:
        click.echo(json_output)


def output_junit(result: ValidationResult, output_file: Optional[str]):
    """Output results in JUnit XML format for CI/CD"""

    # Create JUnit XML structure
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += "<testsuites>\n"
    xml_content += (
        f'  <testsuite name="SpecQL Validation" tests="{result.files_processed}" '
    )
    xml_content += f'failures="{len(result.errors)}" errors="0" skipped="0">\n'

    # Add test cases for each file
    for entity_name, file_path in result.entities_found.items():
        xml_content += f'    <testcase name="{entity_name}" classname="SpecQL.Entity" '
        xml_content += f'file="{file_path}">\n'

        # Add failures for errors related to this entity
        for error in result.errors:
            if error.get("entity") == entity_name:
                xml_content += f'      <failure message="{error["message"]}">\n'
                xml_content += f"        {error['file']}\n"
                xml_content += "      </failure>\n"

        xml_content += "    </testcase>\n"

    xml_content += "  </testsuite>\n"
    xml_content += "</testsuites>\n"

    if output_file:
        Path(output_file).write_text(xml_content)
        click.echo(f"JUnit results written to: {output_file}")
    else:
        click.echo(xml_content)


def main():
    """Entry point for specql validate command"""
    validate()


if __name__ == "__main__":
    main()
