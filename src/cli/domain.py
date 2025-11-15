"""
Domain Management CLI (PostgreSQL Primary)

Provides commands for managing domains using the PostgreSQL-backed repository.
This demonstrates the Phase 3 cut-over where PostgreSQL is the primary data source.
"""

import click
from src.application.services.domain_service_factory import get_domain_service_with_fallback


@click.group()
def domain():
    """Manage domains using PostgreSQL primary repository"""
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

            click.echo(f"  {domain.domain_number} - {domain.domain_name}{schema_desc}")
            click.echo(f"      Identifier: {domain.identifier}")
            click.echo()

    except Exception as e:
        click.secho(f"Error listing domains: {e}", fg="red")
        return 1

    return 0


@domain.command("get")
@click.argument("domain_number", type=int)
def get_domain(domain_number):
    """Get domain details by number"""
    try:
        service = get_domain_service_with_fallback()

        domain = service.get_domain(domain_number)

        click.secho(f"Domain {domain.domain_number}: {domain.domain_name}", fg="green", bold=True)
        click.echo(f"Schema Type: {domain.schema_type}")
        click.echo(f"Identifier: {domain.identifier}")

        # TODO: Add subdomain listing to get_domain method
        click.echo()
        click.secho("Subdomains: (TODO - implement)", fg="yellow")

    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        return 1

    return 0


@domain.command("register")
@click.option("--number", required=True, type=int, help="Domain number (1-99)")
@click.option("--name", required=True, help="Domain name")
@click.option("--schema-type", type=click.Choice(['framework', 'multi_tenant', 'shared']), default='framework', help="Schema type")
def register_domain(number, name, schema_type):
    """Register a new domain"""
    try:
        service = get_domain_service_with_fallback()

        result = service.register_domain(
            domain_number=number,
            domain_name=name,
            schema_type=schema_type
        )

        click.secho("✅ Domain registered successfully!", fg="green")
        click.echo(f"Domain: {result.domain_number} - {result.domain_name}")
        click.echo(f"Identifier: {result.identifier}")

    except Exception as e:
        click.secho(f"Error registering domain: {e}", fg="red")
        return 1

    return 0


# TODO: Re-implement these commands with new service layer
# @domain.command("allocate-code")
# @domain.command("check-consistency")
# @domain.command("performance-report")