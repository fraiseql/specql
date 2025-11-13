"""Repository interface for EntityTemplate aggregate"""
from typing import Protocol, Optional, List
from src.domain.entities.entity_template import EntityTemplate


class EntityTemplateRepository(Protocol):
    """Repository for managing entity templates"""

    def save(self, template: EntityTemplate) -> None:
        """Save or update an entity template"""
        ...

    def find_by_id(self, template_id: str) -> Optional[EntityTemplate]:
        """Find template by ID"""
        ...

    def find_by_name(self, template_name: str) -> Optional[EntityTemplate]:
        """Find template by name"""
        ...

    def find_by_domain(self, domain_number: str) -> List[EntityTemplate]:
        """Find all templates for a domain"""
        ...

    def find_all_public(self) -> List[EntityTemplate]:
        """Find all public templates"""
        ...

    def delete(self, template_id: str) -> None:
        """Delete a template"""
        ...

    def increment_usage(self, template_id: str) -> None:
        """Increment times_instantiated counter"""
        ...