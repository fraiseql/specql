"""Tests for EntityTemplate aggregate"""

import pytest
from src.domain.entities.entity_template import (
    EntityTemplate,
    TemplateField,
    TemplateComposition,
    TemplateInstantiation,
)
from src.domain.value_objects import DomainNumber, TableCode


class TestEntityTemplate:
    """Test EntityTemplate aggregate"""

    def test_create_basic_template(self):
        """Test creating a basic entity template"""
        template = EntityTemplate(
            template_id="tpl_contact",
            template_name="Contact Template",
            description="Standard contact entity with email, phone, address",
            domain_number=DomainNumber("01"),
            base_entity_name="contact",
            fields=[
                TemplateField(
                    field_name="email",
                    field_type="text",
                    required=True,
                    description="Contact email address",
                ),
                TemplateField(
                    field_name="phone",
                    field_type="text",
                    required=False,
                    description="Contact phone number",
                ),
                TemplateField(
                    field_name="address",
                    field_type="composite",
                    composite_type="address_type",
                    required=False,
                ),
            ],
            included_patterns=["audit_trail", "soft_delete"],
            version="1.0.0",
        )

        assert template.template_id == "tpl_contact"
        assert template.template_name == "Contact Template"
        assert len(template.fields) == 3
        assert "audit_trail" in template.included_patterns
        assert template.version == "1.0.0"

    def test_template_composition(self):
        """Test composing templates together"""
        base_template = EntityTemplate(
            template_id="tpl_base_entity",
            template_name="Base Entity",
            description="Common fields for all entities",
            domain_number=DomainNumber("01"),
            base_entity_name="base",
            fields=[
                TemplateField("created_at", "timestamp", required=True),
                TemplateField("updated_at", "timestamp", required=True),
            ],
            version="1.0.0",
        )

        contact_template = EntityTemplate(
            template_id="tpl_contact",
            template_name="Contact",
            description="Contact entity",
            domain_number=DomainNumber("01"),
            base_entity_name="contact",
            fields=[
                TemplateField("email", "text", required=True),
                TemplateField("phone", "text", required=False),
            ],
            composed_from=["tpl_base_entity"],
            version="1.0.0",
        )

        # Composition logic
        composition = TemplateComposition(
            base_templates=[base_template], extending_template=contact_template
        )

        composed = composition.compose()

        # Should have all fields from both templates
        assert len(composed.fields) == 4
        field_names = [f.field_name for f in composed.fields]
        assert "created_at" in field_names
        assert "email" in field_names

    def test_template_instantiation(self):
        """Test instantiating a template to create an entity"""
        template = EntityTemplate(
            template_id="tpl_contact",
            template_name="Contact Template",
            description="Standard contact entity",
            domain_number=DomainNumber("01"),
            base_entity_name="contact",
            fields=[
                TemplateField("email", "text", required=True),
                TemplateField("phone", "text", required=False),
            ],
            included_patterns=["audit_trail"],
            version="1.0.0",
        )

        # Instantiate with customization
        instantiation = TemplateInstantiation(
            template=template,
            entity_name="customer_contact",
            subdomain_number="012",
            table_code=TableCode("012360"),
            field_overrides={
                "phone": {"required": True}  # Make phone required
            },
            additional_fields=[TemplateField("company", "ref", ref_entity="company")],
        )

        entity_spec = instantiation.generate_entity_spec()

        assert entity_spec["entity"] == "customer_contact"
        assert entity_spec["schema"] == "01"  # Domain number
        assert entity_spec["table_code"] == "012360"
        assert len(entity_spec["fields"]) == 3  # email, phone, company
        assert entity_spec["fields"]["phone"]["required"] is True

    def test_template_versioning(self):
        """Test template versioning"""
        v1 = EntityTemplate(
            template_id="tpl_contact",
            template_name="Contact",
            description="Contact entity",
            domain_number=DomainNumber("01"),
            base_entity_name="contact",
            fields=[TemplateField("email", "text", required=True)],
            version="1.0.0",
        )

        # Create new version with additional field
        v2 = v1.create_new_version(
            additional_fields=[TemplateField("phone", "text", required=False)],
            version="2.0.0",
            changelog="Added phone field",
        )

        assert v2.version == "2.0.0"
        assert len(v2.fields) == 2
        assert v2.previous_version == "1.0.0"
        assert "Added phone field" in v2.changelog

    def test_template_validation(self):
        """Test template validation"""
        # Invalid: duplicate field names
        with pytest.raises(ValueError, match="Duplicate field name"):
            EntityTemplate(
                template_id="tpl_invalid",
                template_name="Invalid",
                description="Invalid template",
                domain_number=DomainNumber("01"),
                base_entity_name="invalid",
                fields=[
                    TemplateField("email", "text"),
                    TemplateField("email", "text"),  # Duplicate
                ],
                version="1.0.0",
            )

        # Invalid: empty fields list
        with pytest.raises(ValueError, match="must have at least one field"):
            EntityTemplate(
                template_id="tpl_empty",
                template_name="Empty",
                description="Empty template",
                domain_number=DomainNumber("01"),
                base_entity_name="empty",
                fields=[],
                version="1.0.0",
            )
