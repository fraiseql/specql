"""CLI commands for entity template management"""

import click
import yaml
from src.application.services.template_service import TemplateService
from src.infrastructure.repositories.postgresql_entity_template_repository import (
    PostgreSQLEntityTemplateRepository,
)
from src.core.config import get_config


@click.group()
def templates():
    """Manage entity templates"""
    pass


@templates.command()
@click.option("--template-id", required=True, help="Template ID (e.g., tpl_contact)")
@click.option("--name", required=True, help="Template name")
@click.option("--description", required=True, help="Template description")
@click.option("--domain", required=True, help="Domain number (e.g., 01)")
@click.option("--base-entity", required=True, help="Base entity name")
@click.option(
    "--fields-file",
    required=True,
    type=click.Path(exists=True),
    help="YAML file with field definitions",
)
@click.option("--patterns", multiple=True, help="Pattern IDs to include")
@click.option("--public/--private", default=True, help="Is template public?")
def create(
    template_id, name, description, domain, base_entity, fields_file, patterns, public
):
    """Create a new entity template"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    # Load fields from YAML
    with open(fields_file) as f:
        fields_data = yaml.safe_load(f)
        fields = fields_data.get("fields", [])

    # Create template
    template = service.create_template(
        template_id=template_id,
        template_name=name,
        description=description,
        domain_number=domain,
        base_entity_name=base_entity,
        fields=fields,
        included_patterns=list(patterns) if patterns else [],
        is_public=public,
    )

    click.echo(f"✅ Created template: {template.template_id} (v{template.version})")


@templates.command()
@click.option("--domain", help="Filter by domain number")
def list(domain):
    """List available templates"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    if domain:
        templates_list = service.list_templates_by_domain(domain)
        click.echo(f"Templates in domain {domain}:")
    else:
        templates_list = service.list_public_templates()
        click.echo("All public templates:")

    if not templates_list:
        click.echo("  No templates found")
        return

    for template in templates_list:
        click.echo(f"\n  {template.template_id}")
        click.echo(f"  Name: {template.template_name}")
        click.echo(f"  Description: {template.description}")
        click.echo(f"  Version: {template.version}")
        click.echo(f"  Fields: {len(template.fields)}")
        click.echo(f"  Times used: {template.times_instantiated}")


@templates.command()
@click.argument("template_id")
def show(template_id):
    """Show details of a specific template"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    template = service.get_template(template_id)
    if not template:
        click.echo(f"❌ Template not found: {template_id}")
        return

    click.echo(f"Template: {template.template_id}")
    click.echo(f"Name: {template.template_name}")
    click.echo(f"Description: {template.description}")
    click.echo(f"Domain: {template.domain_number.value}")
    click.echo(f"Base Entity: {template.base_entity_name}")
    click.echo(f"Version: {template.version}")
    click.echo(f"Public: {template.is_public}")
    click.echo(f"Author: {template.author}")
    click.echo(f"Times Used: {template.times_instantiated}")
    click.echo(f"Created: {template.created_at}")
    click.echo(f"Updated: {template.updated_at}")

    if template.previous_version:
        click.echo(f"Previous Version: {template.previous_version}")
    if template.changelog:
        click.echo(f"Changelog: {template.changelog}")

    click.echo(
        f"\nIncluded Patterns: {', '.join(template.included_patterns) if template.included_patterns else 'None'}"
    )
    click.echo(
        f"Composed From: {', '.join(template.composed_from) if template.composed_from else 'None'}"
    )

    click.echo("\nFields:")
    for field in template.fields:
        click.echo(f"  - {field.field_name} ({field.field_type})")
        if field.required:
            click.echo("    Required: Yes")
        if field.description:
            click.echo(f"    Description: {field.description}")
        if field.composite_type:
            click.echo(f"    Composite Type: {field.composite_type}")
        if field.ref_entity:
            click.echo(f"    Reference Entity: {field.ref_entity}")
        if field.enum_values:
            click.echo(f"    Enum Values: {field.enum_values}")
        click.echo()


@templates.command()
@click.option("--template-id", required=True, help="Template to instantiate")
@click.option("--entity-name", required=True, help="Name for the new entity")
@click.option("--subdomain", required=True, help="Subdomain number (e.g., 012)")
@click.option("--table-code", required=True, help="Table code (e.g., 012360)")
@click.option("--output", type=click.Path(), help="Output YAML file path")
@click.option(
    "--field-overrides",
    type=click.Path(exists=True),
    help="YAML file with field overrides",
)
@click.option(
    "--additional-fields",
    type=click.Path(exists=True),
    help="YAML file with additional fields",
)
@click.option("--patterns", multiple=True, help="Override included patterns")
def instantiate(
    template_id,
    entity_name,
    subdomain,
    table_code,
    output,
    field_overrides,
    additional_fields,
    patterns,
):
    """Instantiate a template to create an entity specification"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    # Load overrides if provided
    field_overrides_data = {}
    if field_overrides:
        with open(field_overrides) as f:
            field_overrides_data = yaml.safe_load(f)

    additional_fields_data = []
    if additional_fields:
        with open(additional_fields) as f:
            data = yaml.safe_load(f)
            additional_fields_data = data.get("fields", [])

    # Instantiate template
    entity_spec = service.instantiate_template(
        template_id=template_id,
        entity_name=entity_name,
        subdomain_number=subdomain,
        table_code=table_code,
        field_overrides=field_overrides_data,
        additional_fields=additional_fields_data,
        pattern_overrides=list(patterns) if patterns else None,
    )

    # Output result
    if output:
        with open(output, "w") as f:
            yaml.dump(entity_spec, f, default_flow_style=False, sort_keys=False)
        click.echo(f"✅ Entity specification written to: {output}")
    else:
        # Print to stdout
        click.echo(yaml.dump(entity_spec, default_flow_style=False, sort_keys=False))


@templates.command()
@click.argument("query")
def search(query):
    """Search templates by name or description"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    results = service.search_templates(query)

    if not results:
        click.echo(f"No templates found matching: {query}")
        return

    click.echo(f"Found {len(results)} template(s) matching '{query}':")
    for template in results:
        click.echo(f"\n  {template.template_id}: {template.template_name}")
        click.echo(f"  {template.description}")


@templates.command()
@click.option("--limit", default=10, help="Maximum number of templates to show")
def most_used(limit):
    """Show most frequently used templates"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    templates_list = service.get_most_used_templates(limit)

    if not templates_list:
        click.echo("No templates found")
        return

    click.echo(f"Most used templates (top {limit}):")
    for i, template in enumerate(templates_list, 1):
        click.echo(f"{i}. {template.template_id}: {template.template_name}")
        click.echo(f"   Used {template.times_instantiated} times")


@templates.command()
@click.argument("template_id")
@click.option("--name", help="New template name")
@click.option("--description", help="New description")
@click.option("--public/--private", help="Change visibility")
def update(template_id, name, description, public):
    """Update template metadata"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    try:
        template = service.update_template(
            template_id=template_id,
            template_name=name,
            description=description,
            is_public=public,
        )
        click.echo(f"✅ Updated template: {template.template_id}")
    except ValueError as e:
        click.echo(f"❌ Error: {e}")


@templates.command()
@click.argument("template_id")
@click.option(
    "--additional-fields",
    type=click.Path(exists=True),
    help="YAML file with additional fields",
)
@click.option("--version", help="New version number")
@click.option("--changelog", help="Changelog description")
def version(template_id, additional_fields, version, changelog):
    """Create a new version of a template"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    # Load additional fields if provided
    additional_fields_data = []
    if additional_fields:
        with open(additional_fields) as f:
            data = yaml.safe_load(f)
            additional_fields_data = data.get("fields", [])

    try:
        new_version = service.create_template_version(
            template_id=template_id,
            additional_fields=additional_fields_data,
            version=version,
            changelog=changelog,
        )
        click.echo(
            f"✅ Created new version: {new_version.template_id} v{new_version.version}"
        )
    except ValueError as e:
        click.echo(f"❌ Error: {e}")


@templates.command()
@click.argument("template_id")
def delete(template_id):
    """Delete a template"""
    # Ask for confirmation before deletion
    if not click.confirm(
        "Are you sure you want to delete this template?", default=False
    ):
        click.echo("❌ Deletion cancelled")
        return 0

    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    try:
        service.delete_template(template_id)
        click.echo(f"✅ Deleted template: {template_id}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
