"""YAML-backed Domain Repository (legacy)"""
import yaml
from pathlib import Path
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber


class YAMLDomainRepository:
    """Legacy YAML-backed repository"""

    def __init__(self, yaml_path: Path):
        self.yaml_path = yaml_path
        self._domains: dict[str, Domain] = {}
        self._load_from_yaml()

    def _load_from_yaml(self):
        """Load domains from YAML file"""
        with open(self.yaml_path) as f:
            data = yaml.safe_load(f)

        for domain_num, domain_data in data['domains'].items():
            domain = Domain(
                domain_number=DomainNumber(domain_num),
                domain_name=domain_data['name'],
                description=domain_data.get('description'),
                multi_tenant=domain_data.get('multi_tenant', False),
                aliases=domain_data.get('aliases', [])
            )

            # Load subdomains
            for subdomain_num, subdomain_data in domain_data.get('subdomains', {}).items():
                subdomain = Subdomain(
                    subdomain_number=subdomain_num,
                    subdomain_name=subdomain_data['name'],
                    description=subdomain_data.get('description'),
                    next_entity_sequence=subdomain_data.get('next_entity_sequence', 1),
                    entities=subdomain_data.get('entities', {})
                )
                domain.add_subdomain(subdomain)

            self._domains[domain_num] = domain

    def get(self, domain_number: str) -> Domain:
        """Get domain by number"""
        if domain_number not in self._domains:
            raise ValueError(f"Domain {domain_number} not found")
        return self._domains[domain_number]

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """Find domain by name or alias"""
        for domain in self._domains.values():
            if domain.domain_name == name_or_alias:
                return domain
            if name_or_alias in domain.aliases:
                return domain
        return None

    def save(self, domain: Domain) -> None:
        """Save domain (writes back to YAML)"""
        self._domains[domain.domain_number.value] = domain
        self._write_to_yaml()

    def list_all(self) -> list[Domain]:
        """List all domains"""
        return list(self._domains.values())

    def _write_to_yaml(self):
        """Write domains back to YAML"""
        # Convert domains to YAML structure
        data = {'version': '2.0.0', 'domains': {}}
        for domain in self._domains.values():
            data['domains'][domain.domain_number.value] = {
                'name': domain.domain_name,
                'description': domain.description,
                'multi_tenant': domain.multi_tenant,
                'aliases': domain.aliases,
                'subdomains': {
                    subdomain.subdomain_number: {
                        'name': subdomain.subdomain_name,
                        'description': subdomain.description,
                        'next_entity_sequence': subdomain.next_entity_sequence,
                        'entities': subdomain.entities
                    }
                    for subdomain in domain.subdomains.values()
                }
            }

        with open(self.yaml_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)