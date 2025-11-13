"""EntityTemplate aggregate for reusable entity patterns"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from src.domain.value_objects import DomainNumber, TableCode


@dataclass
class TemplateField:
    """A field definition in a template"""
    field_name: str
    field_type: str  # text, integer, ref, enum, composite, etc.
    required: bool = False
    description: str = ""
    composite_type: Optional[str] = None  # For composite types
    ref_entity: Optional[str] = None  # For ref fields
    enum_values: Optional[List[str]] = None  # For enum fields
    default_value: Optional[Any] = None
    validation_rules: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate field configuration"""
        if self.field_type == "composite" and not self.composite_type:
            raise ValueError(f"Field {self.field_name}: composite type must specify composite_type")
        if self.field_type == "ref" and not self.ref_entity:
            raise ValueError(f"Field {self.field_name}: ref type must specify ref_entity")
        if self.field_type == "enum" and not self.enum_values:
            raise ValueError(f"Field {self.field_name}: enum type must specify enum_values")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "type": self.field_type,
            "required": self.required
        }
        if self.description:
            result["description"] = self.description
        if self.composite_type:
            result["composite_type"] = self.composite_type
        if self.ref_entity:
            result["ref_entity"] = self.ref_entity
        if self.enum_values:
            result["enum_values"] = self.enum_values
        if self.default_value is not None:
            result["default"] = self.default_value
        if self.validation_rules:
            result["validation"] = self.validation_rules
        return result


@dataclass
class EntityTemplate:
    """
    Aggregate: Reusable entity template

    EntityTemplate defines a reusable pattern for creating entities with
    common field structures, patterns, and behaviors.
    """
    template_id: str  # Unique identifier (e.g., "tpl_contact")
    template_name: str
    description: str
    domain_number: DomainNumber
    base_entity_name: str  # Base name for entities created from this template
    fields: List[TemplateField]
    included_patterns: List[str] = field(default_factory=list)  # Pattern IDs
    composed_from: List[str] = field(default_factory=list)  # Other template IDs
    version: str = "1.0.0"
    previous_version: Optional[str] = None
    changelog: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    times_instantiated: int = 0
    is_public: bool = True  # Can be used by others
    author: str = "system"

    def __post_init__(self):
        """Validate template configuration"""
        self._validate()

    def _validate(self):
        """Validate template invariants"""
        # Must have at least one field
        if not self.fields:
            raise ValueError(f"Template {self.template_id} must have at least one field")

        # No duplicate field names
        field_names = [f.field_name for f in self.fields]
        if len(field_names) != len(set(field_names)):
            duplicates = [name for name in field_names if field_names.count(name) > 1]
            raise ValueError(f"Duplicate field name in template {self.template_id}: {duplicates[0]}")

        # Validate template_id format
        if not self.template_id.startswith("tpl_"):
            raise ValueError(f"Template ID must start with 'tpl_': {self.template_id}")

    def create_new_version(
        self,
        additional_fields: Optional[List[TemplateField]] = None,
        removed_fields: Optional[List[str]] = None,
        modified_fields: Optional[Dict[str, TemplateField]] = None,
        version: str = "",
        changelog: str = ""
    ) -> "EntityTemplate":
        """Create a new version of this template"""
        import copy

        # Copy current fields
        new_fields = copy.deepcopy(self.fields)

        # Remove fields
        if removed_fields:
            new_fields = [f for f in new_fields if f.field_name not in removed_fields]

        # Modify fields
        if modified_fields:
            for i, field_obj in enumerate(new_fields):
                if field_obj.field_name in modified_fields:
                    new_fields[i] = modified_fields[field_obj.field_name]

        # Add fields
        if additional_fields:
            new_fields.extend(additional_fields)

        # Create new version
        return EntityTemplate(
            template_id=self.template_id,
            template_name=self.template_name,
            description=self.description,
            domain_number=self.domain_number,
            base_entity_name=self.base_entity_name,
            fields=new_fields,
            included_patterns=self.included_patterns.copy(),
            composed_from=self.composed_from.copy(),
            version=version or self._increment_version(),
            previous_version=self.version,
            changelog=changelog,
            times_instantiated=self.times_instantiated,
            is_public=self.is_public,
            author=self.author
        )

    def _increment_version(self) -> str:
        """Auto-increment version number"""
        major, minor, patch = map(int, self.version.split("."))
        return f"{major}.{minor}.{patch + 1}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "description": self.description,
            "domain_number": str(self.domain_number.value),
            "base_entity_name": self.base_entity_name,
            "fields": {f.field_name: f.to_dict() for f in self.fields},
            "included_patterns": self.included_patterns,
            "composed_from": self.composed_from,
            "version": self.version,
            "previous_version": self.previous_version,
            "changelog": self.changelog,
            "times_instantiated": self.times_instantiated,
            "is_public": self.is_public,
            "author": self.author
        }


@dataclass
class TemplateComposition:
    """Composes multiple templates together"""
    base_templates: List[EntityTemplate]
    extending_template: EntityTemplate

    def compose(self) -> EntityTemplate:
        """Compose templates into a single template"""
        import copy

        # Start with extending template's fields
        composed_fields = copy.deepcopy(self.extending_template.fields)
        field_names = {f.field_name for f in composed_fields}

        # Add fields from base templates (no duplicates)
        for base in self.base_templates:
            for field_obj in base.fields:
                if field_obj.field_name not in field_names:
                    composed_fields.append(copy.deepcopy(field_obj))
                    field_names.add(field_obj.field_name)

        # Merge patterns
        all_patterns = set(self.extending_template.included_patterns)
        for base in self.base_templates:
            all_patterns.update(base.included_patterns)

        # Create composed template
        return EntityTemplate(
            template_id=self.extending_template.template_id,
            template_name=self.extending_template.template_name,
            description=self.extending_template.description,
            domain_number=self.extending_template.domain_number,
            base_entity_name=self.extending_template.base_entity_name,
            fields=composed_fields,
            included_patterns=list(all_patterns),
            composed_from=[t.template_id for t in self.base_templates],
            version=self.extending_template.version,
            is_public=self.extending_template.is_public,
            author=self.extending_template.author
        )


@dataclass
class TemplateInstantiation:
    """Instantiates a template to create an entity specification"""
    template: EntityTemplate
    entity_name: str
    subdomain_number: str
    table_code: TableCode
    field_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    additional_fields: List[TemplateField] = field(default_factory=list)
    pattern_overrides: Optional[List[str]] = None  # Replace template's patterns

    def generate_entity_spec(self) -> Dict[str, Any]:
        """
        Generate a complete entity specification from the template

        Returns a dict that matches SpecQL YAML format
        """

        # Start with template fields
        fields = {}
        for template_field in self.template.fields:
            field_name = template_field.field_name
            field_spec = template_field.to_dict()

            # Apply overrides
            if field_name in self.field_overrides:
                field_spec.update(self.field_overrides[field_name])

            fields[field_name] = field_spec

        # Add additional fields
        for additional in self.additional_fields:
            fields[additional.field_name] = additional.to_dict()

        # Determine patterns to include
        patterns = (
            self.pattern_overrides
            if self.pattern_overrides is not None
            else self.template.included_patterns
        )

        # Build entity spec
        spec = {
            "entity": self.entity_name,
            "schema": str(self.template.domain_number.value),
            "table_code": str(self.table_code.value),
            "description": f"Generated from template: {self.template.template_name}",
            "fields": fields
        }

        if patterns:
            spec["patterns"] = patterns

        # Update template usage counter (domain event would be raised here)
        self.template.times_instantiated += 1
        self.template.updated_at = datetime.now(timezone.utc)

        return spec