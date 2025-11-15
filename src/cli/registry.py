"""
Registry Management CLI

Provides commands for managing the domain registry, including listing domains/subdomains,
adding new entries, and inspecting registry contents.
"""

import click

from src.application.services.domain_service_factory import get_domain_service


@click.group()
def registry():
    """Manage domain registry"""
    pass


@registry.command("list-domains")
def list_domains():
    """List all domains in the registry"""
    try:
        service = get_domain_service()
        domains = service.repository.list_all()

        click.secho("Registered Domains:", fg="blue", bold=True)
        click.echo()

        # Sort by domain number
        domains_sorted = sorted(domains, key=lambda d: int(d.domain_number.value))

        for domain in domains_sorted:
            multi_tenant = " (multi-tenant)" if domain.multi_tenant else ""
            aliases = f" [{', '.join(domain.aliases)}]" if domain.aliases else ""

            click.echo(f"  {domain.domain_number.value} - {domain.domain_name}{multi_tenant}{aliases}")
            click.echo(f"      {domain.description or 'No description'}")
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
        service = get_domain_service()

        # Find domain by name or number
        domain_obj = service.repository.find_by_name(domain)
        if not domain_obj:
            try:
                domain_obj = service.repository.get(domain)
            except ValueError:
                click.secho(f"Domain '{domain}' not found", fg="red")
                raise click.ClickException(f"Domain '{domain}' not found")

        click.secho(f"Subdomains for {domain_obj.domain_name} ({domain_obj.domain_number.value}):", fg="blue", bold=True)
        click.echo()

        # Sort subdomains by subdomain number
        subdomains_sorted = sorted(domain_obj.subdomains.values(), key=lambda s: s.subdomain_number)

        for subdomain in subdomains_sorted:
            click.echo(f"  {subdomain.subdomain_number} - {subdomain.subdomain_name}")
            click.echo(f"      {subdomain.description or 'No description'}")
            click.echo(f"      Next entity: {subdomain.next_entity_sequence}")
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
        service = get_domain_service()

        # Search through all domains and subdomains for the entity
        found_entity = None
        found_domain = None
        found_subdomain = None

        domains = service.repository.list_all()
        for domain in domains:
            for subdomain in domain.subdomains.values():
                if entity_name in subdomain.entities:
                    found_entity = subdomain.entities[entity_name]
                    found_domain = domain
                    found_subdomain = subdomain
                    break
            if found_entity:
                break

        if not found_entity:
            click.secho(f"Entity '{entity_name}' not found in registry", fg="red")
            raise click.ClickException(f"Entity '{entity_name}' not found in registry")

        click.secho(f"Entity: {entity_name}", fg="blue", bold=True)
        click.echo(f"Domain: {found_domain.domain_name if found_domain else 'Unknown'}")
        click.echo(f"Subdomain: {found_subdomain.subdomain_name if found_subdomain else 'Unknown'}")
        click.echo(f"Table Code: {found_entity['table_code']}")
        click.echo(f"Entity Sequence: {found_entity['entity_sequence']}")

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
        service = get_domain_service()

        # Validate domain code
        if not code.isdigit() or len(code) != 1 or code == "0":
            click.secho("Domain code must be a single digit from 1-9", fg="red")
            raise click.ClickException("Domain code must be a single digit from 1-9")

        # Check if domain already exists
        try:
            existing = service.repository.get(code)
            click.secho(f"Domain with code '{code}' already exists", fg="red")
            raise click.ClickException(f"Domain with code '{code}' already exists")
        except ValueError:
            pass  # Domain doesn't exist, which is good

        try:
            existing = service.repository.find_by_name(name)
            if existing:
                click.secho(f"Domain with name '{name}' already exists", fg="red")
                raise click.ClickException(f"Domain with name '{name}' already exists")
        except ValueError:
            pass

        # Add domain using service
        service.register_domain(
            domain_number=code,
            domain_name=name,
            description=description,
            multi_tenant=multi_tenant
        )

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
        service = get_domain_service()

        # Validate subdomain code
        if not code.isdigit() or len(code) != 2:
            click.secho("Subdomain code must be exactly 2 digits (00-99)", fg="red")
            raise click.ClickException("Subdomain code must be exactly 2 digits (00-99)")

        # Check if domain exists
        domain_obj = service.repository.find_by_name(domain)
        if not domain_obj:
            try:
                domain_obj = service.repository.get(domain)
            except ValueError:
                click.secho(f"Domain '{domain}' not found", fg="red")
                raise click.ClickException(f"Domain '{domain}' not found")

        # Check if subdomain already exists
        if code in domain_obj.subdomains:
            click.secho(f"Subdomain with code '{code}' already exists in domain {domain}", fg="red")
            raise click.ClickException(f"Subdomain with code '{code}' already exists in domain {domain}")

        for subdomain in domain_obj.subdomains.values():
            if subdomain.subdomain_name == name:
                click.secho(f"Subdomain with name '{name}' already exists in domain {domain}", fg="red")
                raise click.ClickException(f"Subdomain with name '{name}' already exists in domain {domain}")

        # Add subdomain using service
        service.add_subdomain(
            domain_name=domain_obj.domain_name,
            subdomain_number=code,
            subdomain_name=name,
            description=description
        )

        click.secho(f"Subdomain '{name}' ({code}) added to domain '{domain_obj.domain_name}' successfully", fg="green")

    except click.ClickException:
        raise
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        raise click.ClickException(f"Error: {e}")


@registry.command("validate")
def validate_registry():
    """Validate registry integrity and consistency"""
    try:
        service = get_domain_service()

        click.secho("Validating registry...", fg="blue")

        errors = []
        warnings = []

        # Check domains
        domains = service.repository.list_all()
        if not domains:
            errors.append("No domains found in registry")
        else:
            for domain in domains:
                # Validate domain number
                try:
                    int(domain.domain_number.value)
                except ValueError:
                    errors.append(f"Invalid domain number: {domain.domain_number.value}")

                # Check required fields
                if not domain.domain_name:
                    errors.append(f"Domain {domain.domain_number.value} missing name")
                if not domain.description:
                    warnings.append(f"Domain {domain.domain_name} has no description")

                # Check subdomains
                for subdomain in domain.subdomains.values():
                    if not subdomain.subdomain_number.isdigit() or len(subdomain.subdomain_number) != 2:
                        errors.append(f"Invalid subdomain code: {subdomain.subdomain_number} in domain {domain.domain_name}")

                    if not subdomain.subdomain_name:
                        errors.append(f"Subdomain {subdomain.subdomain_number} in domain {domain.domain_name} missing name")

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