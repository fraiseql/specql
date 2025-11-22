"""
Patterns detect subcommand - Find architectural patterns in SpecQL YAML.
"""

from pathlib import Path

import click
import yaml

from cli.base import common_options
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def detect_patterns_from_yaml(file_path: Path, min_confidence: float = 0.75) -> list[dict]:
    """Detect patterns from SpecQL YAML file."""
    # Load YAML directly to avoid validation issues
    with open(file_path) as f:
        data = yaml.safe_load(f)

    # Extract fields from YAML
    fields = data.get("fields", {}) if isinstance(data, dict) else {}

    patterns = []

    # Check for audit-trail pattern
    audit_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    present_audit_fields = [field for field in audit_fields if field in fields]
    if len(present_audit_fields) >= 2:  # At least 2 out of 4 fields for basic detection
        confidence = min(1.0, len(present_audit_fields) / 4.0)
        if confidence >= min_confidence:
            evidence = [
                f"Found {len(present_audit_fields)} audit fields: {', '.join(present_audit_fields)}"
            ]
            if len(present_audit_fields) >= 3:
                evidence.append("Strong audit trail pattern detected")
            patterns.append(
                {
                    "name": "audit-trail",
                    "confidence": confidence,
                    "evidence": evidence,
                    "fields": present_audit_fields,
                }
            )

    # Check for soft-delete pattern
    if "deleted_at" in fields:
        confidence = 0.9  # High confidence if deleted_at exists
        if confidence >= min_confidence:
            patterns.append(
                {
                    "name": "soft-delete",
                    "confidence": confidence,
                    "evidence": ["Found deleted_at field for logical deletion"],
                    "fields": ["deleted_at"],
                }
            )

    # Check for multi-tenant pattern
    if "tenant_id" in fields:
        confidence = 0.95  # High confidence if tenant_id exists
        if confidence >= min_confidence:
            patterns.append(
                {
                    "name": "multi-tenant",
                    "confidence": confidence,
                    "evidence": ["Found tenant_id field for tenant isolation"],
                    "fields": ["tenant_id"],
                }
            )

    # Check for state-machine pattern
    status_fields = ["status", "state", "status_code"]
    for field_name in status_fields:
        if field_name in fields:
            field_type = str(fields[field_name])
            # Check if it's an enum field (either "enum(...)" or starts with "enum")
            if field_type.startswith("enum(") or field_type.lower().startswith("enum"):
                confidence = 0.85
                if confidence >= min_confidence:
                    patterns.append(
                        {
                            "name": "state-machine",
                            "confidence": confidence,
                            "evidence": [
                                f"Found enum status field: {field_name} with type {field_type}"
                            ],
                            "fields": [field_name],
                        }
                    )
                break

    # Check for hierarchical pattern
    if "parent_id" in fields:
        confidence = 0.8
        if confidence >= min_confidence:
            patterns.append(
                {
                    "name": "hierarchical",
                    "confidence": confidence,
                    "evidence": ["Found parent_id field for tree structure"],
                    "fields": ["parent_id"],
                }
            )

    return patterns


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@common_options
@click.option("--min-confidence", default=0.75, help="Minimum confidence threshold (0.0-1.0)")
@click.option("--patterns", multiple=True, help="Specific patterns to detect")
@click.option(
    "--format", "output_format", type=click.Choice(["text", "json", "yaml"]), default="text"
)
@click.pass_context
def detect(
    ctx,
    files,
    min_confidence,
    patterns,
    output_format,
    output_path=None,
    verbose=False,
    quiet=False,
    **kwargs,
):
    """Detect architectural patterns in SpecQL YAML files.

    Identifies common database design patterns like:
    - audit-trail: Created/updated timestamps and user tracking
    - soft-delete: Logical deletion with deleted_at fields
    - multi-tenant: Tenant isolation patterns
    - state-machine: Status transition patterns
    - hierarchical: Tree structures with parent-child relationships

    Examples:

        specql patterns detect entities/*.yaml
        specql patterns detect . --format=json --output=patterns.json
        specql patterns detect entities/ --patterns=audit-trail --patterns=soft-delete
    """
    with handle_cli_error():
        # Configure output
        output.verbose = verbose
        output.quiet = quiet

        output.info(f"🔍 Detecting patterns in {len(files)} file(s)")

        detected_patterns = []

        for file_path in files:
            path = Path(file_path)
            output.info(f"  📄 Analyzing: {path.name}")

            try:
                file_patterns = detect_patterns_from_yaml(path, min_confidence)
                detected_patterns.append({"file": str(path), "patterns": file_patterns})
            except Exception as e:
                output.warning(f"  ⚠️  Failed to analyze {path.name}: {e}")
                detected_patterns.append({"file": str(path), "patterns": []})

        # Display results
        total_patterns = sum(len(result["patterns"]) for result in detected_patterns)
        output.success(f"Detected {total_patterns} pattern(s) across {len(files)} file(s)")

        if output_format == "text":
            for result in detected_patterns:
                output.info(f"\n📋 {Path(result['file']).name}:")
                if not result["patterns"]:
                    output.info("  • No patterns detected")
                else:
                    for pattern in result["patterns"]:
                        confidence_pct = int(pattern["confidence"] * 100)
                        output.info(f"  • {pattern['name']} ({confidence_pct}% confidence)")
                        if pattern.get("fields"):
                            output.info(f"    Fields: {', '.join(pattern['fields'])}")

        elif output_format in ["json", "yaml"]:
            import json

            if output_path:
                output_file_path = Path(output_path)
                with open(output_file_path, "w") as f:
                    if output_format == "json":
                        json.dump(detected_patterns, f, indent=2)
                    else:
                        yaml.dump(detected_patterns, f)
                output.info(f"Results saved to: {output_file_path}")
            else:
                output.warning("Specify --output file for JSON/YAML format")
