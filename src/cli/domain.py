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
def list_domains():
    """List all domains using PostgreSQL primary repository"""
    try:
        service = get_domain_service_with_fallback()
        domains = service.repository.list_all()

        click.secho("Registered Domains (PostgreSQL Primary):", fg="green", bold=True)
        click.echo()

        for domain in domains:
            multi_tenant = " (multi-tenant)" if domain.multi_tenant else ""
            aliases = f" [{', '.join(domain.aliases)}]" if domain.aliases else ""
            subdomains_count = len(domain.subdomains)

            click.echo(f"  {domain.domain_number.value} - {domain.domain_name}{multi_tenant}{aliases}")
            click.echo(f"      {domain.description or 'No description'}")
            click.echo(f"      {subdomains_count} subdomains")
            click.echo()

    except Exception as e:
        click.secho(f"Error accessing PostgreSQL repository: {e}", fg="red")
        click.secho("Falling back to YAML repository...", fg="yellow")
        return 1

    return 0


@domain.command("get")
@click.argument("domain_number")
def get_domain(domain_number):
    """Get domain details by number"""
    try:
        service = get_domain_service_with_fallback()

        domain = service.repository.get(domain_number)

        click.secho(f"Domain {domain.domain_number.value}: {domain.domain_name}", fg="green", bold=True)
        click.echo(f"Description: {domain.description or 'No description'}")
        click.echo(f"Multi-tenant: {domain.multi_tenant}")
        if domain.aliases:
            click.echo(f"Aliases: {', '.join(domain.aliases)}")

        click.echo()
        click.secho("Subdomains:", fg="blue")
        for subdomain in domain.subdomains.values():
            entities_count = len(subdomain.entities)
            click.echo(f"  {subdomain.subdomain_number} - {subdomain.subdomain_name}")
            click.echo(f"      Next sequence: {subdomain.next_entity_sequence}, Entities: {entities_count}")

    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        return 1

    return 0


@domain.command("register")
@click.option("--number", required=True, help="Domain number (1-9)")
@click.option("--name", required=True, help="Domain name")
@click.option("--description", help="Domain description")
@click.option("--multi-tenant/--no-multi-tenant", default=False, help="Multi-tenant flag")
@click.option("--aliases", help="Comma-separated aliases")
def register_domain(number, name, description, multi_tenant, aliases):
    """Register a new domain (PostgreSQL primary)"""
    try:
        service = get_domain_service_with_fallback()

        aliases_list = [alias.strip() for alias in aliases.split(",")] if aliases else []

        domain = service.register_domain(
            domain_number=number,
            domain_name=name,
            description=description,
            multi_tenant=multi_tenant,
            aliases=aliases_list
        )

        click.secho(f"✅ Domain registered successfully!", fg="green")
        click.echo(f"Domain: {domain.domain_number.value} - {domain.domain_name}")

    except Exception as e:
        click.secho(f"Error registering domain: {e}", fg="red")
        return 1

    return 0


@domain.command("allocate-code")
@click.argument("domain_name")
@click.argument("subdomain_name")
@click.argument("entity_name")
def allocate_entity_code(domain_name, subdomain_name, entity_name):
    """Allocate 6-digit entity code"""
    try:
        service = get_domain_service_with_fallback()

        code = service.allocate_entity_code(domain_name, subdomain_name, entity_name)

        click.secho(f"✅ Entity code allocated!", fg="green")
        click.echo(f"Entity: {entity_name}")
        click.echo(f"Code: {code}")
        click.echo(f"Domain: {domain_name} -> Subdomain: {subdomain_name}")

    except Exception as e:
        click.secho(f"Error allocating code: {e}", fg="red")
        return 1

    return 0


@domain.command("check-consistency")
@click.option("--db-url", help="PostgreSQL database URL")
@click.option("--yaml-path", default="registry/domain_registry.yaml", help="YAML registry path")
def check_consistency(db_url, yaml_path):
    """Check data consistency between PostgreSQL and YAML repositories"""
    import os
    from pathlib import Path
    from src.core.consistency_checker import ConsistencyChecker

    # Get database URL from environment or argument
    db_url = db_url or os.getenv('SPECQL_DB_URL')
    if not db_url:
        click.secho("Error: Database URL not provided. Use --db-url or set SPECQL_DB_URL", fg="red")
        return 1

    yaml_path = Path(yaml_path)
    if not yaml_path.exists():
        click.secho(f"Error: YAML file not found: {yaml_path}", fg="red")
        return 1

    try:
        checker = ConsistencyChecker(db_url, yaml_path)
        results = checker.check_consistency()

        click.secho("🔍 Data Consistency Check Results", fg="blue", bold=True)
        click.echo()

        if results['consistent']:
            click.secho("✅ Data is consistent between PostgreSQL and YAML!", fg="green")
        else:
            click.secho("❌ Data inconsistencies found!", fg="red")

        click.echo()
        click.secho("Summary:", fg="blue")
        click.echo(f"  • Domains checked: {results['summary']['postgresql_domains']}")
        click.echo(f"  • Discrepancies found: {results['summary']['discrepancies_found']}")

        if results['discrepancies']:
            click.echo()
            click.secho("Discrepancies:", fg="yellow")
            for i, disc in enumerate(results['discrepancies'][:10], 1):  # Show first 10
                click.echo(f"  {i}. [{disc['type']}] {disc.get('details', f"{disc.get('domain', 'N/A')}.{disc.get('subdomain', 'N/A')}.{disc.get('entity', 'N/A')}: {disc.get('attribute', 'N/A')}")}")
                if 'postgresql_value' in disc:
                    click.echo(f"     PostgreSQL: {disc['postgresql_value']}")
                    click.echo(f"     YAML: {disc['yaml_value']}")

            if len(results['discrepancies']) > 10:
                click.echo(f"  ... and {len(results['discrepancies']) - 10} more")

        return 0 if results['consistent'] else 1

    except Exception as e:
        click.secho(f"Error checking consistency: {e}", fg="red")
        return 1


@domain.command("performance-report")
def performance_report():
    """Show PostgreSQL repository performance report"""
    try:
        from src.application.services.domain_service_factory import get_domain_service

        # Get service with monitoring enabled
        service = get_domain_service(monitoring=True)

        # Perform some operations to generate stats
        domains = service.repository.list_all()

        # Get performance report
        if hasattr(service.repository, 'get_performance_report'):
            report = service.repository.get_performance_report()

            click.secho("📊 PostgreSQL Repository Performance Report", fg="blue", bold=True)
            click.echo()
            click.echo(f"Queries executed: {report['queries_executed']}")
            click.echo(f"Total query time: {report['total_query_time']:.3f}s")
            click.echo(f"Average query time: {report['average_query_time']:.3f}s")
            click.echo(f"Slow queries (>100ms): {report['slow_query_count']}")
            click.echo(f"Failed queries: {report['failed_queries']}")
            click.echo(f"Success rate: {report['success_rate']:.1f}%")
            click.echo()
            click.echo(f"Domains loaded: {len(domains)}")

            if report['slow_queries']:
                click.echo()
                click.secho("Slow queries:", fg="yellow")
                for slow_query in report['slow_queries'][-5:]:  # Show last 5
                    click.echo(f"  • {slow_query['operation']}: {slow_query['duration']:.3f}s")
        else:
            click.secho("Performance monitoring not available for current repository", fg="yellow")

    except Exception as e:
        click.secho(f"Error generating performance report: {e}", fg="red")
        return 1

    return 0