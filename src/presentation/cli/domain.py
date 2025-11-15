"""
Domain and Subdomain Management CLI (Presentation Layer)

Thin presentation layer that delegates to application services.
"""

import re
import click
from src.application.services.domain_service_factory import get_domain_service_with_fallback


@click.group()
def domain():
    """Manage domains"""
    pass


@domain.command("list")
@click.option("--schema-type", help="Filter by schema type")
def list_domains(schema_type):
    """List all domains"""
    try:
        service = get_domain_service_with_fallback()
        domains = service.list_domains(schema_type=schema_type)

        click.secho("Registered Domains:", fg="green", bold=True)
        click.echo()

        for domain in domains:
            schema_desc = f" ({domain.schema_type})"
            click.echo(f"  {domain.domain_number.upper()} - {domain.domain_name}{schema_desc}")
            click.echo(f"      Identifier: {domain.identifier}")
            click.echo()

    except Exception as e:
        click.secho(f"Error listing domains: {e}", fg="red")
        return 1

    return 0


@domain.command("get")
@click.argument("domain_number")
def get_domain(domain_number):
    """Get domain details by number"""
    try:
        # Validate hex input
        if not re.match(r'^[0-9a-fA-F]{2}$', domain_number):
            click.secho("Domain number must be 2-digit hex (00-FF)", fg="red")
            return 1

        # Convert to uppercase for consistency
        domain_number = domain_number.upper()

        service = get_domain_service_with_fallback()
        domain = service.get_domain(domain_number)

        click.secho(f"Domain {domain.domain_number.upper()}: {domain.domain_name}", fg="green", bold=True)
        click.echo(f"Schema Type: {domain.schema_type}")
        click.echo(f"Identifier: {domain.identifier}")

        # TODO: Add subdomain listing
        click.echo()
        click.secho("Subdomains: (TODO - implement)", fg="yellow")

    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        return 1

    return 0


@domain.command("register")
@click.option("--number", required=True, help="Domain number (00-FF hex)")
@click.option("--name", required=True, help="Domain name")
@click.option("--schema-type", type=click.Choice(['framework', 'multi_tenant', 'shared']), default='framework', help="Schema type")
def register_domain(number, name, schema_type):
    """Register a new domain"""
    try:
        # Validate hex input
        if not re.match(r'^[0-9a-fA-F]{2}$', number):
            click.secho("Domain number must be 2-digit hex (00-FF)", fg="red")
            return 1

        # Convert to uppercase for consistency
        number = number.upper()

        service = get_domain_service_with_fallback()

        result = service.register_domain(
            domain_number=number,
            domain_name=name,
            schema_type=schema_type
        )

        click.secho("✅ Domain registered successfully!", fg="green")
        click.echo(f"Domain: {result.domain_number.upper()} - {result.domain_name}")
        click.echo(f"Identifier: {result.identifier}")

    except Exception as e:
        click.secho(f"Error registering domain: {e}", fg="red")
        return 1

    return 0


# Subdomain commands
@domain.command("register-subdomain")
@click.option("--domain", required=True, help="Parent domain number (00-FF hex)")
@click.option("--number", required=True, help="Subdomain number (0-F hex)")
@click.option("--name", required=True, help="Subdomain name")
def register_subdomain(domain, number, name):
    """Register a new subdomain under a parent domain"""
    try:
        # Validate domain hex input
        if not re.match(r'^[0-9a-fA-F]{2}$', domain):
            click.secho("Parent domain number must be 2-digit hex (00-FF)", fg="red")
            return 1

        # Validate subdomain hex input
        if not re.match(r'^[0-9a-fA-F]{1}$', number):
            click.secho("Subdomain number must be 1-digit hex (0-F)", fg="red")
            return 1

        # Convert to uppercase for consistency
        domain = domain.upper()
        number = number.upper()

        # Create 3-digit subdomain number (domain + subdomain)
        subdomain_number = f"{domain}{number}"

        service = get_domain_service_with_fallback()

        result = service.register_subdomain(
            parent_domain_number=domain,
            subdomain_number=subdomain_number,
            subdomain_name=name
        )

        click.secho("✅ Subdomain registered successfully!", fg="green")
        click.echo(f"Subdomain: {result.subdomain_number.upper()} - {result.subdomain_name}")
        click.echo(f"Parent Domain: {result.parent_domain_number.upper()}")
        click.echo(f"Identifier: {result.identifier}")

    except Exception as e:
        click.secho(f"Error registering subdomain: {e}", fg="red")
        return 1

    return 0


@domain.command("list-subdomains")
@click.option("--domain", help="Filter by parent domain number (00-FF hex)")
def list_subdomains(domain):
    """List all subdomains or subdomains for a specific domain"""
    try:
        if domain:
            # Validate domain hex input
            if not re.match(r'^[0-9a-fA-F]{2}$', domain):
                click.secho("Domain number must be 2-digit hex (00-FF)", fg="red")
                return 1
            domain = domain.upper()

        service = get_domain_service_with_fallback()
        subdomains = service.list_subdomains(parent_domain_number=domain)

        if domain:
            click.secho(f"Subdomains for domain {domain.upper()}:", fg="green", bold=True)
        else:
            click.secho("All Subdomains:", fg="green", bold=True)
        click.echo()

        for subdomain in subdomains:
            click.echo(f"  {subdomain.subdomain_number.upper()} - {subdomain.subdomain_name}")
            click.echo(f"      Parent Domain: {subdomain.parent_domain_number.upper()}")
            click.echo(f"      Identifier: {subdomain.identifier}")
            click.echo()

    except Exception as e:
        click.secho(f"Error listing subdomains: {e}", fg="red")
        return 1

    return 0