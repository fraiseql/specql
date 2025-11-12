#!/usr/bin/env python3
"""
Migrate domain registry from YAML to PostgreSQL

This script reads the existing domain_registry.yaml file and populates
the PostgreSQL specql_registry schema with the domain, subdomain, and
entity registration data.
"""

import yaml
import psycopg
from pathlib import Path
from typing import Dict, Any


def migrate_registry_to_postgres(db_url: str, yaml_path: Path) -> None:
    """
    Migrate domain registry data from YAML to PostgreSQL

    Args:
        db_url: PostgreSQL connection string
        yaml_path: Path to domain_registry.yaml file
    """
    # Load YAML data
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Migrate domains
            for domain_num, domain_data in data['domains'].items():
                _migrate_domain(cur, domain_num, domain_data)

        conn.commit()


def _migrate_domain(cur, domain_num: str, domain_data: Dict[str, Any]) -> None:
    """Migrate a single domain and its subdomains"""
    # Insert domain
    cur.execute("""
        INSERT INTO specql_registry.tb_domain
        (domain_number, domain_name, description, multi_tenant, aliases)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (domain_number) DO UPDATE SET
            domain_name = EXCLUDED.domain_name,
            description = EXCLUDED.description,
            multi_tenant = EXCLUDED.multi_tenant,
            aliases = EXCLUDED.aliases
        RETURNING pk_domain
    """, (
        domain_num,
        domain_data['name'],
        domain_data.get('description'),
        domain_data.get('multi_tenant', False),
        domain_data.get('aliases', [])
    ))

    domain_pk = cur.fetchone()[0]

    # Migrate subdomains
    for subdomain_num, subdomain_data in domain_data.get('subdomains', {}).items():
        _migrate_subdomain(cur, domain_pk, subdomain_num, subdomain_data)


def _migrate_subdomain(cur, domain_pk: int, subdomain_num: str, subdomain_data: Dict[str, Any]) -> None:
    """Migrate a single subdomain and its entities"""
    # Insert subdomain
    cur.execute("""
        INSERT INTO specql_registry.tb_subdomain
        (fk_domain, subdomain_number, subdomain_name, description, next_entity_sequence)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (fk_domain, subdomain_number) DO UPDATE SET
            subdomain_name = EXCLUDED.subdomain_name,
            description = EXCLUDED.description,
            next_entity_sequence = EXCLUDED.next_entity_sequence
        RETURNING pk_subdomain
    """, (
        domain_pk,
        subdomain_num,
        subdomain_data['name'],
        subdomain_data.get('description'),
        subdomain_data.get('next_entity_sequence', 1)
    ))

    subdomain_pk = cur.fetchone()[0]

    # Migrate entities
    for entity_name, entity_data in subdomain_data.get('entities', {}).items():
        _migrate_entity(cur, subdomain_pk, entity_name, entity_data)

    # Also migrate read_entities if they exist
    for entity_name, entity_data in subdomain_data.get('read_entities', {}).items():
        _migrate_entity(cur, subdomain_pk, entity_name, entity_data)


def _migrate_entity(cur, subdomain_pk: int, entity_name: str, entity_data: Dict[str, Any]) -> None:
    """Migrate a single entity registration"""
    # Handle different entity data formats
    if isinstance(entity_data, dict):
        table_code = entity_data.get('table_code')
        entity_sequence = entity_data.get('entity_sequence', entity_data.get('entity_number', 1))
    else:
        # Handle legacy format where entity_data might be just a table_code string
        table_code = str(entity_data)
        entity_sequence = 1

    if table_code:
        cur.execute("""
            INSERT INTO specql_registry.tb_entity_registration
            (fk_subdomain, entity_name, table_code, entity_sequence)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (fk_subdomain, entity_name) DO UPDATE SET
                table_code = EXCLUDED.table_code,
                entity_sequence = EXCLUDED.entity_sequence
        """, (
            subdomain_pk,
            entity_name,
            table_code,
            entity_sequence
        ))


def main():
    """Command line interface for migration"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Migrate domain registry from YAML to PostgreSQL')
    parser.add_argument('--db-url', help='PostgreSQL connection URL')
    parser.add_argument('--yaml-path', default='registry/domain_registry.yaml',
                       help='Path to domain_registry.yaml file')

    args = parser.parse_args()

    # Get database URL from environment or argument
    db_url = args.db_url or os.getenv('SPECQL_DB_URL')
    if not db_url:
        print("Error: Database URL not provided. Use --db-url or set SPECQL_DB_URL environment variable.")
        return 1

    yaml_path = Path(args.yaml_path)
    if not yaml_path.exists():
        print(f"Error: YAML file not found: {yaml_path}")
        return 1

    try:
        migrate_registry_to_postgres(db_url, yaml_path)
        print("✅ Migration completed successfully!")
        return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())