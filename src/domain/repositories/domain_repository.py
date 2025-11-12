"""Domain Repository Protocol"""
from typing import Protocol
from src.domain.entities.domain import Domain

class DomainRepository(Protocol):
    """Repository for Domain aggregate root"""

    def get(self, domain_number: str) -> Domain:
        """Get domain by number - raises if not found"""
        ...

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """Find domain by name or alias"""
        ...

    def save(self, domain: Domain) -> None:
        """Save domain"""
        ...

    def list_all(self) -> list[Domain]:
        """List all domains"""
        ...