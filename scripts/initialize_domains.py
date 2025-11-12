#!/usr/bin/env python3
"""
Initialize PostgreSQL Domain Registry

Reads the archived domain registry YAML and initializes PostgreSQL
with domain, subdomain, and entity data.
"""
import sys
import yaml
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.application.services.domain_service_factory import get_domain_service

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_archived_registry(yaml_path: Path) -> dict:
    """Load archived YAML registry"""
    logger.info(f"Loading archived registry from {yaml_path}")
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return data


def initialize_domains_from_yaml(yaml_path: Path, dry_run: bool = False):
    """Initialize PostgreSQL from archived YAML"""
    data = load_archived_registry(yaml_path)
    service = get_domain_service()

    domains_data = data.get('domains', {})
    logger.info(f"Found {len(domains_data)} domains in YAML")

    stats = {
        'domains_created': 0,
        'subdomains_created': 0,
        'entities_registered': 0,
        'errors': []
    }

    for domain_num, domain_data in domains_data.items():
        domain_name = domain_data['name']
        description = domain_data.get('description', '')
        multi_tenant = domain_data.get('multi_tenant', False)
        aliases = domain_data.get('aliases', [])

        logger.info(f"\nProcessing domain {domain_num}: {domain_name}")

        try:
            if not dry_run:
                # Check if domain already exists
                existing_domain = service.repository.find_by_name(domain_name)
                if existing_domain:
                    logger.info(f"  Domain {domain_name} already exists, skipping")
                    domain = existing_domain
                else:
                    # Register domain
                    domain = service.register_domain(
                        domain_number=domain_num,
                        domain_name=domain_name,
                        description=description,
                        multi_tenant=multi_tenant,
                        aliases=aliases
                    )
                    stats['domains_created'] += 1
                    logger.info(f"  ✓ Created domain: {domain_name}")
            else:
                logger.info(f"  Would create domain: {domain_name}")

            # Process subdomains
            subdomains_data = domain_data.get('subdomains', {})
            logger.info(f"  Found {len(subdomains_data)} subdomains")

            for subdomain_num, subdomain_data in subdomains_data.items():
                subdomain_name = subdomain_data['name']
                subdomain_desc = subdomain_data.get('description', '')

                if not dry_run:
                    # Check if subdomain exists
                    try:
                        domain.get_subdomain(subdomain_num)
                        logger.info(f"    Subdomain {subdomain_name} already exists")
                    except (ValueError, KeyError):
                        # Create and add subdomain
                        from src.domain.entities.domain import Subdomain
                        subdomain = Subdomain(
                            subdomain_number=subdomain_num,
                            subdomain_name=subdomain_name,
                            description=subdomain_desc,
                            parent_domain_number=str(domain.domain_number.value)
                        )
                        domain.add_subdomain(subdomain)
                        stats['subdomains_created'] += 1
                        logger.info(f"    ✓ Created subdomain: {subdomain_name}")

                    # Save domain after subdomain registration
                    service.repository.save(domain)
                else:
                    logger.info(f"    Would create subdomain: {subdomain_name}")

                # Process entities
                entities_data = subdomain_data.get('entities', {})
                for entity_code, entity_name in entities_data.items():
                    if not dry_run:
                        try:
                            # Allocate code (will skip if exists)
                            code = service.allocate_entity_code(
                                domain_name=domain_name,
                                subdomain_name=subdomain_name,
                                entity_name=entity_name
                            )
                            stats['entities_registered'] += 1
                            logger.info(f"      ✓ Registered entity: {entity_name} → {code}")
                        except Exception as e:
                            logger.warning(f"      Entity {entity_name} may already exist: {e}")
                    else:
                        logger.info(f"      Would register entity: {entity_name}")

        except Exception as e:
            error_msg = f"Error processing domain {domain_name}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("INITIALIZATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Domains created:      {stats['domains_created']}")
    logger.info(f"Subdomains created:   {stats['subdomains_created']}")
    logger.info(f"Entities registered:  {stats['entities_registered']}")
    logger.info(f"Errors:               {len(stats['errors'])}")

    if stats['errors']:
        logger.error("\nErrors encountered:")
        for error in stats['errors']:
            logger.error(f"  - {error}")

    return stats


def main():
    """Main initialization script"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Initialize PostgreSQL from archived YAML")
    parser.add_argument(
        "--yaml",
        default="registry/archive/domain_registry.yaml",
        help="Path to archived domain registry YAML"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    # Check environment
    if not os.getenv('SPECQL_DB_URL'):
        logger.error("SPECQL_DB_URL environment variable must be set")
        sys.exit(1)

    yaml_path = Path(args.yaml)
    if not yaml_path.exists():
        logger.error(f"YAML file not found: {yaml_path}")
        sys.exit(1)

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made\n")

    stats = initialize_domains_from_yaml(yaml_path, dry_run=args.dry_run)

    if stats['errors']:
        sys.exit(1)


if __name__ == "__main__":
    main()
