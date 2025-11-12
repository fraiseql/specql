"""
Registry Management CLI

Provides commands for managing the domain registry, including listing domains/subdomains,
adding new entries, and inspecting registry contents.
"""

import click
from pathlib import Path

from src.generators.schema.naming_conventions import DomainRegistry


@click.group()
def registry():
    """Manage domain registry"""
    pass


@registry.command("list-domains")
def list_domains():
    """List all domains in the registry"""
    try:
        registry = DomainRegistry()
        domains = registry.load_domain_mapping()

        click.secho("Registered Domains:", fg="blue", bold=True)
        click.echo()

        # Group by domain code for better display
        domain_codes = sorted([k for k in domains.keys() if k.isdigit()])

        for domain_code in domain_codes:
            domain_info = domains[domain_code]
            multi_tenant = " (multi-tenant)" if domain_info["multi_tenant"] else ""
            aliases = f" [{', '.join(domain_info['aliases'])}]" if domain_info["aliases"] else ""

            click.echo(f"  {domain_info['code']} - {domain_info['name']}{multi_tenant}{aliases}")
            click.echo(f"      {domain_info['description']}")
            click.echo()

    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        return 1

    return 0


@registry.command("list-subdomains")
@click.argument("domain")
def list_subdomains(domain):
    """List subdomains for a specific domain"""
    try:
        registry = DomainRegistry()
        subdomains = registry.load_subdomain_mapping(domain)

        if not subdomains:
            click.secho(f"Domain '{domain}' not found", fg="red")
            raise click.ClickException(f"Domain '{domain}' not found")

        # Get domain info for header
        domain_info = registry.get_domain(domain)
        if not domain_info:
            click.secho(f"Domain '{domain}' not found", fg="red")
            raise click.ClickException(f"Domain '{domain}' not found")
        click.secho(f"Subdomains for {domain_info.domain_name} ({domain_info.domain_code}):", fg="blue", bold=True)
        click.echo()

        # Group by subdomain code
        subdomain_codes = sorted([k for k in subdomains.keys() if k.isdigit()])

        for subdomain_code in subdomain_codes:
            subdomain_info = subdomains[subdomain_code]
            click.echo(f"  {subdomain_info['code']} - {subdomain_info['name']}")
            click.echo(f"      {subdomain_info['description']}")
            click.echo(f"      Next entity: {subdomain_info['next_entity_sequence']}, Next read: {subdomain_info['next_read_entity']}")
            click.echo()

    except click.ClickException:
        raise
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        raise click.ClickException(f"Error: {e}")


@registry.command("show-entity")
@click.argument("entity_name")
def show_entity(entity_name):
    """Show detailed information about a specific entity"""
    try:
        registry = DomainRegistry()

        # Try to find the entity
        entity = registry.get_entity(entity_name)

        if not entity:
            click.secho(f"Entity '{entity_name}' not found in registry", fg="red")
            raise click.ClickException(f"Entity '{entity_name}' not found in registry")

        click.secho(f"Entity: {entity.entity_name}", fg="blue", bold=True)
        click.echo(f"Domain: {entity.domain}")
        click.echo(f"Subdomain: {entity.subdomain}")
        click.echo(f"Table Code: {entity.table_code}")
        click.echo(f"Entity Code: {entity.entity_code}")
        click.echo(f"Assigned: {entity.assigned_at}")

        # Show read entities if any
        domain_info = registry.get_domain(entity.domain)
        if domain_info:
            subdomain_info = registry.get_subdomain(domain_info.domain_code, entity.subdomain)
            if subdomain_info and subdomain_info.read_entities:
                click.echo()
                click.secho("Read Entities:", fg="green")
                for read_entity_name, read_entity_data in subdomain_info.read_entities.items():
                    click.echo(f"  - {read_entity_name} ({read_entity_data['code']})")

    except click.ClickException:
        raise
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        raise click.ClickException(f"Error: {e}")


@registry.command("add-domain")
@click.option("--code", required=True, help="Domain code (1-9)")
@click.option("--name", required=True, help="Domain name")
@click.option("--description", required=True, help="Domain description")
@click.option("--multi-tenant", is_flag=True, help="Mark as multi-tenant domain")
def add_domain(code, name, description, multi_tenant):
    """Add a new domain to the registry"""
    try:
        registry = DomainRegistry()

        # Validate domain code
        if not code.isdigit() or len(code) != 1 or code == "0":
            click.secho("Domain code must be a single digit from 1-9", fg="red")
            raise click.ClickException("Domain code must be a single digit from 1-9")

        # Check if domain already exists
        if registry.get_domain(code):
            click.secho(f"Domain with code '{code}' already exists", fg="red")
            raise click.ClickException(f"Domain with code '{code}' already exists")

        if registry.get_domain(name):
            click.secho(f"Domain with name '{name}' already exists", fg="red")
            raise click.ClickException(f"Domain with name '{name}' already exists")

        # Add domain to registry
        if "domains" not in registry.registry:
            registry.registry["domains"] = {}

        registry.registry["domains"][code] = {
            "name": name,
            "description": description,
            "multi_tenant": multi_tenant,
            "subdomains": {}
        }

        # Update last_updated
        from datetime import datetime
        registry.registry["last_updated"] = datetime.now().isoformat()

        # Save registry
        registry.save()

        click.secho(f"Domain '{name}' ({code}) added successfully", fg="green")

    except click.ClickException:
        raise
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        raise click.ClickException(f"Error: {e}")


@registry.command("add-subdomain")
@click.option("--domain", required=True, help="Domain code or name")
@click.option("--code", required=True, help="Subdomain code (00-99)")
@click.option("--name", required=True, help="Subdomain name")
@click.option("--description", required=True, help="Subdomain description")
def add_subdomain(domain, code, name, description):
    """Add a new subdomain to an existing domain"""
    try:
        registry = DomainRegistry()

        # Get domain
        domain_info = registry.get_domain(domain)
        if not domain_info:
            click.secho(f"Domain '{domain}' not found", fg="red")
            raise click.ClickException(f"Domain '{domain}' not found")

        # Validate subdomain code
        if not code.isdigit() or len(code) != 2:
            click.secho("Subdomain code must be exactly 2 digits (00-99)", fg="red")
            raise click.ClickException("Subdomain code must be exactly 2 digits (00-99)")

        # Check if subdomain already exists
        if registry.get_subdomain(domain_info.domain_code, code):
            click.secho(f"Subdomain with code '{code}' already exists in domain {domain}", fg="red")
            raise click.ClickException(f"Subdomain with code '{code}' already exists in domain {domain}")

        if registry.get_subdomain(domain_info.domain_code, name):
            click.secho(f"Subdomain with name '{name}' already exists in domain {domain}", fg="red")
            raise click.ClickException(f"Subdomain with name '{name}' already exists in domain {domain}")

        # Add subdomain to registry
        domain_data = registry.registry["domains"][domain_info.domain_code]
        if "subdomains" not in domain_data:
            domain_data["subdomains"] = {}

        domain_data["subdomains"][code] = {
            "name": name,
            "description": description,
            "next_entity_sequence": 1,
            "entities": {},
            "read_entities": {},
            "next_read_entity": 1
        }

        # Update last_updated
        from datetime import datetime
        registry.registry["last_updated"] = datetime.now().isoformat()

        # Save registry
        registry.save()

        click.secho(f"Subdomain '{name}' ({code}) added to domain '{domain_info.domain_name}' successfully", fg="green")

    except click.ClickException:
        raise
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        raise click.ClickException(f"Error: {e}")


@registry.command("validate")
def validate_registry():
    """Validate registry integrity and consistency"""
    try:
        registry = DomainRegistry()

        click.secho("Validating registry...", fg="blue")

        errors = []
        warnings = []

        # Check domains
        domains = registry.registry.get("domains", {})
        if not domains:
            errors.append("No domains found in registry")
        else:
            for domain_code, domain_data in domains.items():
                # Validate domain code
                if not domain_code.isdigit() or len(domain_code) != 1:
                    errors.append(f"Invalid domain code: {domain_code}")

                # Check required fields
                if "name" not in domain_data:
                    errors.append(f"Domain {domain_code} missing 'name' field")
                if "description" not in domain_data:
                    errors.append(f"Domain {domain_code} missing 'description' field")

                # Check subdomains
                subdomains = domain_data.get("subdomains", {})
                for subdomain_code, subdomain_data in subdomains.items():
                    if not subdomain_code.isdigit() or len(subdomain_code) != 2:
                        errors.append(f"Invalid subdomain code: {subdomain_code} in domain {domain_code}")

                    if "name" not in subdomain_data:
                        errors.append(f"Subdomain {subdomain_code} in domain {domain_code} missing 'name' field")

        # Report results
        if errors:
            click.secho("Validation Errors:", fg="red", bold=True)
            for error in errors:
                click.echo(f"  ❌ {error}")
            return 1

        if warnings:
            click.secho("Validation Warnings:", fg="yellow", bold=True)
            for warning in warnings:
                click.echo(f"  ⚠️  {warning}")

        click.secho("Registry validation passed!", fg="green")

    except Exception as e:
        click.secho(f"Error during validation: {e}", fg="red")
        return 1

    return 0


if __name__ == "__main__":
    registry()