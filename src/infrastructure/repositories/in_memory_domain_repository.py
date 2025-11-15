"""In-Memory Domain Repository (for testing)"""
from src.domain.entities.domain import Domain

class InMemoryDomainRepository:
    """In-memory repository for testing"""

    def __init__(self):
        self._domains: dict[str, Domain] = {}

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
        """Save domain"""
        self._domains[domain.domain_number.value] = domain

    def list_all(self) -> list[Domain]:
        """List all domains"""
        return list(self._domains.values())

    def clear(self) -> None:
        """Clear all domains (for testing)"""
        self._domains.clear()