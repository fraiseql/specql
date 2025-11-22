"""
Patterns apply subcommand - Apply architectural patterns to SpecQL YAML.
"""

from pathlib import Path

import click
import yaml

from cli.base import common_options
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def apply_pattern_to_yaml(
    file_path: Path, pattern_name: str, preview: bool = False, output_path: str | None = None
) -> dict:
    """Apply pattern to SpecQL YAML file."""
    # Load current YAML
    with open(file_path) as f:
        content = yaml.safe_load(f)

    # Ensure fields section exists
    if "fields" not in content:
        content["fields"] = {}

    changes = []

    if pattern_name == "audit-trail":
        audit_fields = {
            "created_at": "timestamptz",
            "updated_at": "timestamptz",
            "created_by": "uuid",
            "updated_by": "uuid",
        }
        for field_name, field_type in audit_fields.items():
            if field_name not in content["fields"]:
                content["fields"][field_name] = field_type
                changes.append(f"Add {field_name}: {field_type} field")

    elif pattern_name == "soft-delete":
        if "deleted_at" not in content["fields"]:
            content["fields"]["deleted_at"] = "timestamptz"
            changes.append("Add deleted_at: timestamptz field")

    elif pattern_name == "multi-tenant":
        if "tenant_id" not in content["fields"]:
            content["fields"]["tenant_id"] = "uuid"
            changes.append("Add tenant_id: uuid field (required)")

    elif pattern_name == "state-machine":
        if "status" not in content["fields"]:
            content["fields"]["status"] = "enum(pending, active, completed, cancelled)"
            changes.append("Add status: enum field (pending, active, completed, cancelled)")
        if "status_updated_at" not in content["fields"]:
            content["fields"]["status_updated_at"] = "timestamptz"
            changes.append("Add status_updated_at: timestamptz field")

    elif pattern_name == "hierarchical":
        hierarchical_fields = {"parent_id": "uuid", "path": "text", "depth": "integer"}
        for field_name, field_type in hierarchical_fields.items():
            if field_name not in content["fields"]:
                content["fields"][field_name] = field_type
                changes.append(f"Add {field_name}: {field_type} field")

    if preview:
        return {"preview": True, "changes": changes}

    # Write to output path or overwrite input
    output_file_path = Path(output_path) if output_path else file_path
    with open(output_file_path, "w") as f:
        yaml.dump(content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return {"applied": True, "changes": changes}


@click.command()
@click.argument("pattern")
@click.argument("file", type=click.Path(exists=True))
@common_options
@click.option("--preview", is_flag=True, help="Preview changes without writing")
@click.pass_context
def apply(
    ctx, pattern, file, output_path=None, preview=False, verbose=False, quiet=False, **kwargs
):
    """Apply an architectural pattern to a SpecQL YAML file.

    Available patterns:
    - audit-trail: Add created_at, updated_at, created_by, updated_by fields
    - soft-delete: Add deleted_at field and logical deletion support
    - multi-tenant: Add tenant_id field for tenant isolation
    - state-machine: Add status field with transition tracking
    - hierarchical: Add parent_id and path fields for tree structures

    Examples:

        specql patterns apply audit-trail contact.yaml
        specql patterns apply soft-delete user.yaml --preview
        specql patterns apply multi-tenant product.yaml -o product_tenant.yaml
    """
    with handle_cli_error():
        # Configure output
        output.verbose = verbose
        output.quiet = quiet

        file_path = Path(file)
        output.info(f"🔧 Applying pattern '{pattern}' to {file_path.name}")

        if preview:
            output.info("🔍 Preview mode: no files will be modified")

        # Validate pattern
        valid_patterns = [
            "audit-trail",
            "soft-delete",
            "multi-tenant",
            "state-machine",
            "hierarchical",
        ]
        if pattern not in valid_patterns:
            from cli.utils.error_handler import CLIError

            raise CLIError(f"Unknown pattern: {pattern}. Available: {', '.join(valid_patterns)}")

        # Apply pattern
        try:
            result = apply_pattern_to_yaml(file_path, pattern, preview, output_path)

            # Display changes
            output.info(f"\n📋 Changes for pattern '{pattern}':")
            if result.get("changes"):
                for change in result["changes"]:
                    output.info(f"  • {change}")
            else:
                output.info("  • No changes needed (pattern already applied)")

            if preview:
                output.success("Preview complete - no files modified")
            else:
                final_path = Path(output_path) if output_path else file_path
                output.success(f"Pattern '{pattern}' applied successfully")
                if output_path:
                    output.info(f"Output saved to: {final_path}")
                else:
                    output.info("File modified in-place")

        except Exception as e:
            from cli.utils.error_handler import CLIError

            raise CLIError(f"Failed to apply pattern: {e}")
