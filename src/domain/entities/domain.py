"""Domain Aggregate Root"""
from dataclasses import dataclass, field
from typing import List
from src.domain.value_objects import DomainNumber, TableCode

@dataclass
class Subdomain:
    """Subdomain entity (part of Domain aggregate)"""
    subdomain_number: str
    subdomain_name: str
    description: str | None
    next_entity_sequence: int = 1
    entities: dict = field(default_factory=dict)
    parent_domain_number: str = ""  # Set when added to domain

    def allocate_next_code(self, entity_name: str) -> TableCode:
        """Allocate next entity code"""
        code = TableCode.generate(
            domain_num=self.parent_domain_number,
            subdomain_num=self.subdomain_number,
            entity_seq=self.next_entity_sequence
        )
        self.entities[entity_name] = {
            'table_code': str(code),
            'entity_sequence': self.next_entity_sequence
        }
        self.next_entity_sequence += 1
        return code

@dataclass
class Domain:
    """Domain Aggregate Root"""
    domain_number: DomainNumber
    domain_name: str
    description: str | None
    multi_tenant: bool
    aliases: List[str] = field(default_factory=list)
    subdomains: dict[str, Subdomain] = field(default_factory=dict)

    def add_subdomain(self, subdomain: Subdomain) -> None:
        """Add subdomain to domain"""
        if subdomain.subdomain_number in self.subdomains:
            raise ValueError(
                f"Subdomain {subdomain.subdomain_number} already exists in {self.domain_name}"
            )
        subdomain.parent_domain_number = self.domain_number.value
        self.subdomains[subdomain.subdomain_number] = subdomain

    def get_subdomain(self, subdomain_number: str) -> Subdomain:
        """Get subdomain by number"""
        if subdomain_number not in self.subdomains:
            raise ValueError(
                f"Subdomain {subdomain_number} not found in {self.domain_name}"
            )
        return self.subdomains[subdomain_number]

    def allocate_entity_code(self, subdomain_num: str, entity_name: str) -> TableCode:
        """Allocate 6-digit code for entity"""
        subdomain = self.get_subdomain(subdomain_num)
        return subdomain.allocate_next_code(entity_name)