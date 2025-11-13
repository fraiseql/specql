"""Application service for entity template management"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.domain.entities.entity_template import (
    EntityTemplate,
    TemplateField,
    TemplateInstantiation
)
from src.domain.value_objects import DomainNumber, TableCode
from src.domain.repositories.entity_template_repository import EntityTemplateRepository


class TemplateService:
    """Application service for managing entity templates"""

    def __init__(self, repository: EntityTemplateRepository):
        self.repository = repository

    def create_template(
        self,
        template_id: str,
        template_name: str,
        description: str,
        domain_number: str,
        base_entity_name: str,
        fields: List[Dict[str, Any]],
        included_patterns: Optional[List[str]] = None,
        composed_from: Optional[List[str]] = None,
        is_public: bool = True,
        author: str = "system"
    ) -> EntityTemplate:
        """Create a new entity template"""
        # Convert field dicts to TemplateField objects
        template_fields = [
            TemplateField(
                field_name=f["field_name"],
                field_type=f["field_type"],
                required=f.get("required", False),
                description=f.get("description", ""),
                composite_type=f.get("composite_type"),
                ref_entity=f.get("ref_entity"),
                enum_values=f.get("enum_values"),
                default_value=f.get("default_value"),
                validation_rules=f.get("validation_rules", [])
            )
            for f in fields
        ]

        # Create template
        template = EntityTemplate(
            template_id=template_id,
            template_name=template_name,
            description=description,
            domain_number=DomainNumber(domain_number),
            base_entity_name=base_entity_name,
            fields=template_fields,
            included_patterns=included_patterns or [],
            composed_from=composed_from or [],
            version="1.0.0",
            is_public=is_public,
            author=author
        )

        # Save
        self.repository.save(template)

        return template

    def get_template(self, template_id: str) -> Optional[EntityTemplate]:
        """Get template by ID"""
        return self.repository.find_by_id(template_id)

    def list_templates_by_domain(self, domain_number: str) -> List[EntityTemplate]:
        """List all templates for a domain"""
        return self.repository.find_by_domain(domain_number)

    def list_public_templates(self) -> List[EntityTemplate]:
        """List all public templates"""
        return self.repository.find_all_public()

    def instantiate_template(
        self,
        template_id: str,
        entity_name: str,
        subdomain_number: str,
        table_code: str,
        field_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        additional_fields: Optional[List[Dict[str, Any]]] = None,
        pattern_overrides: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Instantiate a template to create an entity specification

        Returns a dict that can be written as SpecQL YAML
        """
        # Get template
        template = self.repository.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Convert additional fields if provided
        additional_template_fields = []
        if additional_fields:
            additional_template_fields = [
                TemplateField(
                    field_name=f["field_name"],
                    field_type=f["field_type"],
                    required=f.get("required", False),
                    description=f.get("description", ""),
                    composite_type=f.get("composite_type"),
                    ref_entity=f.get("ref_entity"),
                    enum_values=f.get("enum_values")
                )
                for f in additional_fields
            ]

        # Create instantiation
        instantiation = TemplateInstantiation(
            template=template,
            entity_name=entity_name,
            subdomain_number=subdomain_number,
            table_code=TableCode(table_code),
            field_overrides=field_overrides or {},
            additional_fields=additional_template_fields,
            pattern_overrides=pattern_overrides
        )

        # Generate entity spec
        entity_spec = instantiation.generate_entity_spec()

        # Increment usage counter
        self.repository.increment_usage(template_id)

        return entity_spec

    def update_template(
        self,
        template_id: str,
        template_name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> EntityTemplate:
        """Update template metadata"""
        template = self.repository.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Update fields
        if template_name:
            template.template_name = template_name
        if description:
            template.description = description
        if is_public is not None:
            template.is_public = is_public

        template.updated_at = datetime.now(timezone.utc)

        # Save
        self.repository.save(template)

        return template

    def create_template_version(
        self,
        template_id: str,
        additional_fields: Optional[List[Dict[str, Any]]] = None,
        removed_fields: Optional[List[str]] = None,
        modified_fields: Optional[Dict[str, Dict[str, Any]]] = None,
        version: str = "",
        changelog: str = ""
    ) -> EntityTemplate:
        """Create a new version of existing template"""
        template = self.repository.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Convert dicts to TemplateField objects if needed
        add_fields = []
        if additional_fields:
            add_fields = [
                TemplateField(
                    field_name=f["field_name"],
                    field_type=f["field_type"],
                    required=f.get("required", False),
                    description=f.get("description", ""),
                    composite_type=f.get("composite_type"),
                    ref_entity=f.get("ref_entity"),
                    enum_values=f.get("enum_values")
                )
                for f in additional_fields
            ]

        mod_fields = {}
        if modified_fields:
            mod_fields = {
                name: TemplateField(
                    field_name=f["field_name"],
                    field_type=f["field_type"],
                    required=f.get("required", False),
                    description=f.get("description", "")
                )
                for name, f in modified_fields.items()
            }

        # Create new version
        new_version = template.create_new_version(
            additional_fields=add_fields,
            removed_fields=removed_fields,
            modified_fields=mod_fields,
            version=version,
            changelog=changelog
        )

        # Save
        self.repository.save(new_version)

        return new_version

    def delete_template(self, template_id: str) -> None:
        """Delete a template"""
        self.repository.delete(template_id)

    def search_templates(self, query: str) -> List[EntityTemplate]:
        """Search templates by name or description"""
        # Simple in-memory search (PostgreSQL can do full-text search)
        all_public = self.repository.find_all_public()
        query_lower = query.lower()

        return [
            t for t in all_public
            if query_lower in t.template_name.lower()
            or query_lower in t.description.lower()
        ]

    def get_most_used_templates(self, limit: int = 10) -> List[EntityTemplate]:
        """Get most frequently instantiated templates"""
        all_public = self.repository.find_all_public()
        sorted_templates = sorted(
            all_public,
            key=lambda t: t.times_instantiated,
            reverse=True
        )
        return sorted_templates[:limit]