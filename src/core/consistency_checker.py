"""
Data Consistency Checker

Validates data consistency between PostgreSQL and YAML repositories
during the cut-over period.
"""

import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ConsistencyChecker:
    """
    Checks data consistency between PostgreSQL and YAML repositories.

    Used during Phase 3 cut-over to ensure data integrity.
    """

    def __init__(self, db_url: str, yaml_path: Path):
        self.db_url = db_url
        self.yaml_path = yaml_path

    def check_consistency(self) -> Dict[str, Any]:
        """
        Check consistency between PostgreSQL and YAML repositories.

        Returns:
            Dict with consistency results and any discrepancies found
        """
        results = {
            'consistent': True,
            'domains_checked': 0,
            'discrepancies': [],
            'summary': {}
        }

        try:
            # Load data from both sources
            pg_domains = self._load_postgresql_domains()
            yaml_domains = self._load_yaml_domains()

            results['domains_checked'] = len(pg_domains)

            # Compare domains
            discrepancies = self._compare_domains(pg_domains, yaml_domains)
            results['discrepancies'] = discrepancies
            results['consistent'] = len(discrepancies) == 0

            # Summary
            results['summary'] = {
                'postgresql_domains': len(pg_domains),
                'yaml_domains': len(yaml_domains),
                'discrepancies_found': len(discrepancies)
            }

            if discrepancies:
                logger.warning(f"Found {len(discrepancies)} data discrepancies")
            else:
                logger.info("Data consistency check passed")

        except Exception as e:
            logger.error(f"Consistency check failed: {e}")
            results['consistent'] = False
            results['error'] = str(e)

        return results

    def _load_postgresql_domains(self) -> Dict[str, Dict[str, Any]]:
        """Load domains from PostgreSQL"""
        import psycopg

        domains = {}
        try:
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Get all domains with their subdomains
                    cur.execute("""
                        SELECT
                            d.domain_number,
                            d.domain_name,
                            d.description,
                            d.multi_tenant,
                            d.aliases,
                            array_agg(
                                json_build_object(
                                    'subdomain_number', s.subdomain_number,
                                    'subdomain_name', s.subdomain_name,
                                    'description', s.description,
                                    'next_entity_sequence', s.next_entity_sequence,
                                    'entities', (
                                        SELECT json_object_agg(entity_name, json_build_object(
                                            'table_code', table_code,
                                            'entity_sequence', entity_sequence
                                        ))
                                        FROM specql_registry.tb_entity_registration er
                                        WHERE er.fk_subdomain = s.pk_subdomain
                                    )
                                )
                            ) FILTER (WHERE s.pk_subdomain IS NOT NULL) as subdomains
                        FROM specql_registry.tb_domain d
                        LEFT JOIN specql_registry.tb_subdomain s ON s.fk_domain = d.pk_domain
                        GROUP BY d.pk_domain, d.domain_number, d.domain_name, d.description, d.multi_tenant, d.aliases
                        ORDER BY d.domain_number
                    """)

                    for row in cur.fetchall():
                        domain_num = row[0]
                        domains[domain_num] = {
                            'domain_number': row[0],
                            'domain_name': row[1],
                            'description': row[2],
                            'multi_tenant': row[3],
                            'aliases': row[4] or [],
                            'subdomains': {}
                        }

                        # Process subdomains
                        if row[5]:
                            for subdomain_data in row[5]:
                                if subdomain_data:  # Skip None values
                                    subdomain_num = subdomain_data['subdomain_number']
                                    domains[domain_num]['subdomains'][subdomain_num] = {
                                        'subdomain_number': subdomain_num,
                                        'subdomain_name': subdomain_data['subdomain_name'],
                                        'description': subdomain_data['description'],
                                        'next_entity_sequence': subdomain_data['next_entity_sequence'],
                                        'entities': subdomain_data['entities'] or {}
                                    }

        except Exception as e:
            logger.error(f"Failed to load PostgreSQL domains: {e}")
            raise

        return domains

    def _load_yaml_domains(self) -> Dict[str, Dict[str, Any]]:
        """Load domains from YAML"""
        import yaml

        domains = {}
        try:
            with open(self.yaml_path) as f:
                data = yaml.safe_load(f)

            for domain_num, domain_data in data.get('domains', {}).items():
                domains[domain_num] = {
                    'domain_number': domain_num,
                    'domain_name': domain_data['name'],
                    'description': domain_data.get('description'),
                    'multi_tenant': domain_data.get('multi_tenant', False),
                    'aliases': domain_data.get('aliases', []),
                    'subdomains': {}
                }

                # Process subdomains
                for subdomain_num, subdomain_data in domain_data.get('subdomains', {}).items():
                    domains[domain_num]['subdomains'][subdomain_num] = {
                        'subdomain_number': subdomain_num,
                        'subdomain_name': subdomain_data['name'],
                        'description': subdomain_data.get('description'),
                        'next_entity_sequence': subdomain_data.get('next_entity_sequence', 1),
                        'entities': subdomain_data.get('entities', {})
                    }

        except Exception as e:
            logger.error(f"Failed to load YAML domains: {e}")
            raise

        return domains

    def _compare_domains(self, pg_domains: Dict, yaml_domains: Dict) -> List[Dict[str, Any]]:
        """Compare domains between PostgreSQL and YAML"""
        discrepancies = []

        # Check all domains exist in both
        all_domain_nums = set(pg_domains.keys()) | set(yaml_domains.keys())

        for domain_num in all_domain_nums:
            pg_domain = pg_domains.get(domain_num)
            yaml_domain = yaml_domains.get(domain_num)

            if pg_domain is None:
                discrepancies.append({
                    'type': 'missing_in_postgresql',
                    'domain': domain_num,
                    'details': f"Domain {domain_num} exists in YAML but not in PostgreSQL"
                })
                continue

            if yaml_domain is None:
                discrepancies.append({
                    'type': 'missing_in_yaml',
                    'domain': domain_num,
                    'details': f"Domain {domain_num} exists in PostgreSQL but not in YAML"
                })
                continue

            # Compare domain-level attributes
            domain_discrepancies = self._compare_domain_attributes(domain_num, pg_domain, yaml_domain)
            discrepancies.extend(domain_discrepancies)

            # Compare subdomains
            subdomain_discrepancies = self._compare_subdomains(domain_num, pg_domain, yaml_domain)
            discrepancies.extend(subdomain_discrepancies)

        return discrepancies

    def _compare_domain_attributes(self, domain_num: str, pg_domain: Dict, yaml_domain: Dict) -> List[Dict]:
        """Compare domain-level attributes"""
        discrepancies = []

        attrs_to_check = ['domain_name', 'description', 'multi_tenant', 'aliases']

        for attr in attrs_to_check:
            pg_value = pg_domain.get(attr)
            yaml_value = yaml_domain.get(attr)

            if pg_value != yaml_value:
                discrepancies.append({
                    'type': 'domain_attribute_mismatch',
                    'domain': domain_num,
                    'attribute': attr,
                    'postgresql_value': pg_value,
                    'yaml_value': yaml_value
                })

        return discrepancies

    def _compare_subdomains(self, domain_num: str, pg_domain: Dict, yaml_domain: Dict) -> List[Dict]:
        """Compare subdomains between sources"""
        discrepancies = []

        pg_subdomains = pg_domain.get('subdomains', {})
        yaml_subdomains = yaml_domain.get('subdomains', {})

        all_subdomain_nums = set(pg_subdomains.keys()) | set(yaml_subdomains.keys())

        for subdomain_num in all_subdomain_nums:
            pg_subdomain = pg_subdomains.get(subdomain_num)
            yaml_subdomain = yaml_subdomains.get(subdomain_num)

            if pg_subdomain is None:
                discrepancies.append({
                    'type': 'missing_subdomain_in_postgresql',
                    'domain': domain_num,
                    'subdomain': subdomain_num,
                    'details': f"Subdomain {subdomain_num} exists in YAML but not in PostgreSQL"
                })
                continue

            if yaml_subdomain is None:
                discrepancies.append({
                    'type': 'missing_subdomain_in_yaml',
                    'domain': domain_num,
                    'subdomain': subdomain_num,
                    'details': f"Subdomain {subdomain_num} exists in PostgreSQL but not in YAML"
                })
                continue

            # Compare subdomain attributes
            subdomain_discrepancies = self._compare_subdomain_attributes(
                domain_num, subdomain_num, pg_subdomain, yaml_subdomain
            )
            discrepancies.extend(subdomain_discrepancies)

        return discrepancies

    def _compare_subdomain_attributes(self, domain_num: str, subdomain_num: str,
                                    pg_subdomain: Dict, yaml_subdomain: Dict) -> List[Dict]:
        """Compare subdomain-level attributes"""
        discrepancies = []

        attrs_to_check = ['subdomain_name', 'description', 'next_entity_sequence']

        for attr in attrs_to_check:
            pg_value = pg_subdomain.get(attr)
            yaml_value = yaml_subdomain.get(attr)

            if pg_value != yaml_value:
                discrepancies.append({
                    'type': 'subdomain_attribute_mismatch',
                    'domain': domain_num,
                    'subdomain': subdomain_num,
                    'attribute': attr,
                    'postgresql_value': pg_value,
                    'yaml_value': yaml_value
                })

        # Compare entities
        pg_entities = pg_subdomain.get('entities', {})
        yaml_entities = yaml_subdomain.get('entities', {})

        entity_discrepancies = self._compare_entities(domain_num, subdomain_num, pg_entities, yaml_entities)
        discrepancies.extend(entity_discrepancies)

        return discrepancies

    def _compare_entities(self, domain_num: str, subdomain_num: str,
                         pg_entities: Dict, yaml_entities: Dict) -> List[Dict]:
        """Compare entities between sources"""
        discrepancies = []

        all_entity_names = set(pg_entities.keys()) | set(yaml_entities.keys())

        for entity_name in all_entity_names:
            pg_entity = pg_entities.get(entity_name)
            yaml_entity = yaml_entities.get(entity_name)

            if pg_entity is None:
                discrepancies.append({
                    'type': 'missing_entity_in_postgresql',
                    'domain': domain_num,
                    'subdomain': subdomain_num,
                    'entity': entity_name,
                    'details': f"Entity {entity_name} exists in YAML but not in PostgreSQL"
                })
                continue

            if yaml_entity is None:
                discrepancies.append({
                    'type': 'missing_entity_in_yaml',
                    'domain': domain_num,
                    'subdomain': subdomain_num,
                    'entity': entity_name,
                    'details': f"Entity {entity_name} exists in PostgreSQL but not in YAML"
                })
                continue

            # Compare entity attributes
            if pg_entity != yaml_entity:
                discrepancies.append({
                    'type': 'entity_attribute_mismatch',
                    'domain': domain_num,
                    'subdomain': subdomain_num,
                    'entity': entity_name,
                    'postgresql_value': pg_entity,
                    'yaml_value': yaml_entity
                })

        return discrepancies