"""Application Service for Domain operations"""
from src.domain.repositories.domain_repository import DomainRepository
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber, TableCode

class DomainService:
    """
    Application Service for Domain operations

    Uses repository abstraction - doesn't care about storage implementation
    """

    def __init__(self, repository: DomainRepository):
        self.repository = repository

    def register_domain(
        self,
        domain_number: str,
        domain_name: str,
        description: str | None,
        multi_tenant: bool,
        aliases: list[str] | None = None
    ) -> Domain:
        """Register a new domain"""
        domain = Domain(
            domain_number=DomainNumber(domain_number),
            domain_name=domain_name,
            description=description,
            multi_tenant=multi_tenant,
            aliases=aliases or []
        )
        self.repository.save(domain)
        return domain

    def add_subdomain(
        self,
        domain_name: str,
        subdomain_number: str,
        subdomain_name: str,
        description: str | None = None
    ) -> None:
        """Add a subdomain to an existing domain"""
        # Find domain
        domain = self.repository.find_by_name(domain_name)
        if not domain:
            raise ValueError(f"Domain {domain_name} not found")

        # Create subdomain
        subdomain = Subdomain(
            subdomain_number=subdomain_number,
            subdomain_name=subdomain_name,
            description=description
        )

        # Add to domain (business logic in domain entity)
        domain.add_subdomain(subdomain)

        # Save
        self.repository.save(domain)

    def allocate_entity_code(
        self,
        domain_name: str,
        subdomain_name: str,
        entity_name: str
    ) -> TableCode:
        """Allocate 6-digit code for entity"""
        # Find domain
        domain = self.repository.find_by_name(domain_name)
        if not domain:
            raise ValueError(f"Domain {domain_name} not found")

        # Find subdomain
        subdomain = None
        for sd in domain.subdomains.values():
            if sd.subdomain_name == subdomain_name:
                subdomain = sd
                break

        if not subdomain:
            raise ValueError(f"Subdomain {subdomain_name} not found in {domain_name}")

        # Allocate code (business logic in domain entity)
        code = subdomain.allocate_next_code(entity_name)

        # Save (increments next_entity_sequence)
        self.repository.save(domain)

        return code