"""
Init entity subcommand - Create entity templates.
"""

from pathlib import Path

import click

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


@click.command()
@click.argument("name")
@click.option("--schema", "-s", default="public", help="Database schema")
@click.option("--field", "-f", multiple=True, help="Field definition (name:type)")
@click.option("--output-dir", "-o", default="entities", help="Output directory")
@click.option(
    "--template",
    type=click.Choice(["basic", "audit", "tenant"]),
    default="basic",
    help="Entity template",
)
def entity(name, schema, field, output_dir, template, **kwargs):
    """Create a new SpecQL entity template.

    Generates a YAML template with common fields and patterns based on the
    selected template. Customize with additional fields using --field options.

    Templates:
    - basic: Standard entity with ID and timestamps
    - audit: Includes audit trail fields (created/updated by)
    - tenant: Multi-tenant entity with tenant isolation

    Examples:

        specql init entity Contact --schema=crm
        specql init entity Order --field=total:decimal --field=status:enum --template=audit
        specql init entity Product --template=tenant --schema=inventory
    """
    with handle_cli_error():
        output.info(f"📝 Creating entity template: {name}")

        # Build field list
        fields = {}

        # Add template-specific fields
        if template == "basic":
            fields.update(
                {
                    "id": {"type": "uuid", "primary_key": True, "default": "gen_random_uuid()"},
                    "created_at": {"type": "timestamptz", "default": "now()"},
                    "updated_at": {"type": "timestamptz"},
                }
            )
        elif template == "audit":
            fields.update(
                {
                    "id": {"type": "uuid", "primary_key": True, "default": "gen_random_uuid()"},
                    "created_at": {"type": "timestamptz", "default": "now()"},
                    "updated_at": {"type": "timestamptz"},
                    "created_by": {"type": "uuid"},
                    "updated_by": {"type": "uuid"},
                }
            )
        elif template == "tenant":
            fields.update(
                {
                    "id": {"type": "uuid", "primary_key": True, "default": "gen_random_uuid()"},
                    "tenant_id": {"type": "uuid", "required": True},
                    "created_at": {"type": "timestamptz", "default": "now()"},
                    "updated_at": {"type": "timestamptz"},
                }
            )

        # Add user-specified fields
        for field_def in field:
            if ":" in field_def:
                fname, ftype = field_def.split(":", 1)
                fields[fname] = {"type": ftype}
            else:
                fields[field_def] = {"type": "text"}

        # Generate YAML content
        yaml_content = f"""entity: {name}
schema: {schema}
description: {name} entity
"""

        if fields:
            yaml_content += "\nfields:\n"
            for field_name, field_config in fields.items():
                yaml_content += f"  {field_name}:\n"
                for key, value in field_config.items():
                    if isinstance(value, str):
                        yaml_content += f"    {key}: {value}\n"
                    else:
                        yaml_content += f"    {key}: {value}\n"

        # Add basic actions
        yaml_content += f"""
actions:
  - name: create_{name.lower()}
    description: Create a new {name.lower()}
    steps:
      - insert: {name}

  - name: update_{name.lower()}
    description: Update {name.lower()} information
    steps:
      - update: {name} SET updated_at = now() WHERE id = :id

  - name: delete_{name.lower()}
    description: Delete {name.lower()}
    steps:
      - delete: {name} WHERE id = :id
"""

        # Create output directory and file
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"{name.lower()}.yaml"
        file_path.write_text(yaml_content)

        output.success(f"✅ Entity template created: {file_path}")
        output.info("📋 Template features:")
        output.info(f"  • Schema: {schema}")
        output.info(f"  • Template: {template}")
        output.info(f"  • Fields: {len(fields)}")
        output.info("  • Actions: 3 (create, update, delete)")

        output.warning("Full entity template integration pending in Phase 5")
