"""Domain Data Transfer Objects"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DomainDTO:
    """Data Transfer Object for Domain aggregate"""
    domain_number: str
    domain_name: str
    schema_type: str
    identifier: str
    pk_domain: Optional[int] = None
    description: Optional[str] = None

    @classmethod
    def from_domain(cls, domain):
        """Create DTO from Domain aggregate"""
        return cls(
            domain_number=domain.domain_number.value,
            domain_name=domain.domain_name,
            schema_type=domain.schema_type,
            identifier=domain.identifier,
            pk_domain=domain.pk_domain,
            description=domain.description
        )


@dataclass
class SubdomainDTO:
    """Data Transfer Object for Subdomain aggregate"""
    subdomain_number: str
    subdomain_name: str
    parent_domain_number: str
    identifier: str
    pk_subdomain: Optional[int] = None
    description: Optional[str] = None

    @classmethod
    def from_subdomain(cls, subdomain):
        """Create DTO from Subdomain aggregate"""
        return cls(
            subdomain_number=subdomain.subdomain_number.value,
            subdomain_name=subdomain.subdomain_name,
            parent_domain_number=subdomain.parent_domain.domain_number.value,
            identifier=subdomain.identifier,
            pk_subdomain=subdomain.pk_subdomain,
            description=subdomain.description
        )