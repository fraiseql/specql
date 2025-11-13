"""In-memory implementation of EntityTemplateRepository for testing"""
from typing import Optional, List, Dict
from src.domain.entities.entity_template import EntityTemplate


class InMemoryEntityTemplateRepository:
    """In-memory repository for EntityTemplate (testing only)"""

    def __init__(self):
        self._templates: Dict[str, EntityTemplate] = {}

    def save(self, template: EntityTemplate) -> None:
        """Save template to memory"""
        # Make a copy to simulate persistence
        import copy
        self._templates[template.template_id] = copy.deepcopy(template)

    def find_by_id(self, template_id: str) -> Optional[EntityTemplate]:
        """Find template by ID"""
        import copy
        template = self._templates.get(template_id)
        return copy.deepcopy(template) if template else None

    def find_by_name(self, template_name: str) -> Optional[EntityTemplate]:
        """Find template by name"""
        import copy
        for template in self._templates.values():
            if template.template_name == template_name:
                return copy.deepcopy(template)
        return None

    def find_by_domain(self, domain_number: str) -> List[EntityTemplate]:
        """Find all templates for a domain"""
        import copy
        return [
            copy.deepcopy(t)
            for t in self._templates.values()
            if str(t.domain_number.value) == domain_number
        ]

    def find_all_public(self) -> List[EntityTemplate]:
        """Find all public templates"""
        import copy
        return [
            copy.deepcopy(t)
            for t in self._templates.values()
            if t.is_public
        ]

    def delete(self, template_id: str) -> None:
        """Delete a template"""
        if template_id in self._templates:
            del self._templates[template_id]

    def increment_usage(self, template_id: str) -> None:
        """Increment usage counter"""
        if template_id in self._templates:
            self._templates[template_id].times_instantiated += 1