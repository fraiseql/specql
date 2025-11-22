"""Test reverse engineering command"""

import re
from pathlib import Path

import click

from cli.base import common_options, validate_common_options
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output as cli_output


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@common_options
@click.option(
    "--type",
    "test_type",
    type=click.Choice(["pgtap", "pytest", "jest", "auto"]),
    default="auto",
    help="Source test type",
)
@click.option("--preview", is_flag=True, help="Preview without writing files")
@click.pass_context
def reverse(ctx, files, output, verbose, quiet, test_type, preview):
    """Reverse engineer existing tests to SpecQL test specs.

    Analyzes existing test files and extracts test specifications
    that can be used to regenerate or validate tests.

    Examples:

        # Auto-detect and reverse engineer
        specql test reverse tests/*.sql -o specs/

        # Specify test type
        specql test reverse tests/*.py --type pytest

        # Preview without writing
        specql test reverse tests/ --preview
    """
    with handle_cli_error():
        validate_common_options(verbose=verbose, quiet=quiet)
        cli_output.verbose = verbose
        cli_output.quiet = quiet

        output_dir = Path(output) if output else Path("test-specs")

        processed_count = 0
        for file_path in files:
            path = Path(file_path)

            try:
                # Auto-detect type
                detected_type = test_type
                if test_type == "auto":
                    detected_type = _detect_test_type(path)

                if detected_type == "auto":
                    cli_output.warning(f"Could not detect test type for {path}")
                    continue

                # Parse test file
                if detected_type == "pgtap":
                    spec = _parse_pgtap(path)
                elif detected_type == "pytest":
                    spec = _parse_pytest(path)
                elif detected_type == "jest":
                    spec = _parse_jest(path)
                else:
                    cli_output.warning(f"Unsupported test type '{detected_type}' for {path}")
                    continue

                # Generate YAML spec
                yaml_content = _spec_to_yaml(spec)

                if preview:
                    cli_output.info(f"\n--- {spec['entity'].lower()}-test-spec.yaml ---")
                    cli_output.info(yaml_content)
                else:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    # Include test type in filename to avoid collisions
                    type_suffix = f"_{detected_type}" if detected_type != "auto" else ""
                    spec_file = output_dir / f"{spec['entity'].lower()}-test-spec{type_suffix}.yaml"
                    spec_file.write_text(yaml_content)
                    cli_output.success(f"Generated {spec_file}")

                processed_count += 1

            except Exception as e:
                cli_output.error(f"Failed to process {path}: {e}")
                continue

        if not preview:
            cli_output.success(f"\nTest specs written to {output_dir}/")


def _detect_test_type(path: Path) -> str:
    """Detect test type from file extension and content"""
    if not path.exists():
        return "auto"

    # Fast extension-based detection
    if path.suffix == ".sql":
        return "pgtap"
    elif path.suffix == ".py":
        return "pytest"
    elif path.suffix in (".ts", ".js"):
        return "jest"

    # Content-based detection for unknown extensions
    try:
        content = path.read_text()
    except (UnicodeDecodeError, OSError):
        return "auto"

    if "SELECT plan(" in content or "pgTAP" in content.lower():
        return "pgtap"
    elif "import pytest" in content or "def test_" in content:
        return "pytest"
    elif "describe(" in content or "it(" in content:
        return "jest"

    return "auto"  # Unable to detect


def _parse_pgtap(path: Path) -> dict:
    """Parse pgTAP test file into spec"""
    try:
        content = path.read_text()
    except (UnicodeDecodeError, OSError) as e:
        raise ValueError(f"Could not read pgTAP file: {e}")

    spec = {
        "entity": _extract_entity_name(content, path),
        "schema": _extract_schema(content),
        "tests": {"structure": [], "crud": [], "actions": [], "constraints": []},
    }

    # Validate we have an entity
    if not spec["entity"] or spec["entity"] == "Unknown":
        raise ValueError("Could not extract entity name from pgTAP file")

    # Parse structure tests
    if "has_table(" in content:
        spec["tests"]["structure"].append({"table_exists": True})
    if "col_is_pk(" in content:
        spec["tests"]["structure"].append({"has_trinity_pattern": True})
    if "has_column" in content and ("created_at" in content or "updated_at" in content):
        spec["tests"]["structure"].append({"has_audit_columns": True})

    # Parse CRUD tests
    crud_patterns = [
        (r"app\.create_(\w+)", "create"),
        (r"app\.update_(\w+)", "update"),
        (r"app\.delete_(\w+)", "delete"),
    ]
    for pattern, action in crud_patterns:
        if re.search(pattern, content):
            spec["tests"]["crud"].append({action: {"expect": "success"}})

    # Parse action tests
    action_pattern = r"(\w+)\.(\w+)\s*\("
    for match in re.finditer(action_pattern, content):
        schema, action = match.groups()
        if schema not in ("app", "public") and action not in ("create", "update", "delete"):
            spec["tests"]["actions"].append({action: {"expect": "success"}})

    return spec


def _parse_pytest(path: Path) -> dict:
    """Parse pytest test file into spec"""
    try:
        content = path.read_text()
    except (UnicodeDecodeError, OSError) as e:
        raise ValueError(f"Could not read pytest file: {e}")

    spec = {
        "entity": _extract_entity_name_from_class(content, path),
        "schema": _extract_schema_from_python(content),
        "tests": {"structure": [], "crud": [], "actions": [], "constraints": []},
    }

    # Validate we have an entity
    if not spec["entity"] or spec["entity"] == "Unknown":
        raise ValueError("Could not extract entity name from pytest file")

    # Parse test methods
    test_methods = re.findall(r"def (test_\w+)\(", content)
    for method in test_methods:
        if "create" in method:
            spec["tests"]["crud"].append({"create": {"expect": "success"}})
        elif "update" in method:
            spec["tests"]["crud"].append({"update": {"expect": "success"}})
        elif "delete" in method:
            spec["tests"]["crud"].append({"delete": {"expect": "success"}})
        else:
            # Likely an action test
            action_name = method.replace("test_", "")
            spec["tests"]["actions"].append({action_name: {"expect": "success"}})

    return spec


def _parse_jest(path: Path) -> dict:
    """Parse Jest/Vitest test file into spec"""
    content = path.read_text()
    spec = {
        "entity": _extract_entity_from_jest(content, path),
        "schema": "crm",  # Default
        "tests": {"structure": [], "crud": [], "actions": [], "constraints": []},
    }

    # Parse describe/it blocks
    it_blocks = re.findall(r"it\(['\"](.+?)['\"]", content)
    for description in it_blocks:
        if "create" in description.lower():
            spec["tests"]["crud"].append({"create": {"expect": "success"}})
        elif "update" in description.lower():
            spec["tests"]["crud"].append({"update": {"expect": "success"}})
        elif "delete" in description.lower():
            spec["tests"]["crud"].append({"delete": {"expect": "success"}})

    return spec


def _extract_entity_name(content: str, path: Path) -> str:
    """Extract entity name from pgTAP content"""
    # Try to find from table name
    match = re.search(r"tb_(\w+)", content)
    if match:
        return match.group(1).title()

    # Try from file name
    return path.stem.replace("test_", "").title()


def _extract_entity_name_from_class(content: str, path: Path) -> str:
    """Extract entity name from pytest class"""
    match = re.search(r"class Test(\w+)", content)
    if match:
        name = match.group(1).replace("Integration", "")
        return name
    return path.stem.replace("test_", "").title()


def _extract_entity_from_jest(content: str, path: Path) -> str:
    """Extract entity name from Jest describe block"""
    match = re.search(r"describe\(['\"](\w+)", content)
    if match:
        return match.group(1)
    return path.stem.replace("test_", "").title()


def _extract_schema(content: str) -> str:
    """Extract schema name from SQL content"""
    match = re.search(r"['\"](\w+)['\"],\s*['\"]tb_", content)
    if match:
        return match.group(1)
    return "crm"  # Default


def _extract_schema_from_python(content: str) -> str:
    """Extract schema from Python test content"""
    match = re.search(r"(\w+)\.tb_", content)
    if match:
        return match.group(1)
    return "crm"


def _spec_to_yaml(spec: dict) -> str:
    """Convert spec dict to YAML string"""
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for test reverse engineering. Install with: pip install PyYAML"
        )

    # Clean up empty sections
    spec["tests"] = {k: v for k, v in spec["tests"].items() if v}

    # Ensure required fields
    if "entity" not in spec:
        spec["entity"] = "Unknown"
    if "schema" not in spec:
        spec["schema"] = "public"

    return yaml.dump(spec, default_flow_style=False, sort_keys=False, allow_unicode=True)
