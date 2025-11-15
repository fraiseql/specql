"""Tests for TemplateService"""
import pytest
from src.application.services.template_service import TemplateService
from src.domain.entities.entity_template import EntityTemplate, TemplateField
from src.domain.value_objects import DomainNumber
from src.infrastructure.repositories.in_memory_entity_template_repository import (
    InMemoryEntityTemplateRepository
)


@pytest.fixture
def repository():
    """Create in-memory repository for testing"""
    return InMemoryEntityTemplateRepository()


@pytest.fixture
def service(repository):
    """Create service with in-memory repository"""
    return TemplateService(repository)


@pytest.fixture
def sample_template():
    """Create sample template"""
    return EntityTemplate(
        template_id="tpl_contact",
        template_name="Contact Template",
        description="Standard contact entity",
        domain_number=DomainNumber("01"),
        base_entity_name="contact",
        fields=[
            TemplateField("email", "text", required=True),
            TemplateField("phone", "text", required=False)
        ],
        included_patterns=["audit_trail"],
        version="1.0.0"
    )


class TestTemplateService:
    """Test TemplateService application service"""

    def test_create_template(self, service):
        """Test creating a new template"""
        template = service.create_template(
            template_id="tpl_test",
            template_name="Test Template",
            description="Test template",
            domain_number="01",
            base_entity_name="test",
            fields=[
                {"field_name": "name", "field_type": "text", "required": True}
            ],
            included_patterns=["audit_trail"],
            is_public=True
        )

        assert template.template_id == "tpl_test"
        assert len(template.fields) == 1
        assert template.fields[0].field_name == "name"

    def test_get_template(self, service, sample_template):
        """Test retrieving template by ID"""
        service.repository.save(sample_template)

        found = service.get_template("tpl_contact")
        assert found is not None
        assert found.template_id == "tpl_contact"

    def test_list_templates_by_domain(self, service, sample_template):
        """Test listing templates by domain"""
        service.repository.save(sample_template)

        templates = service.list_templates_by_domain("01")
        assert len(templates) >= 1
        assert any(t.template_id == "tpl_contact" for t in templates)

    def test_instantiate_template(self, service, sample_template):
        """Test instantiating template to create entity spec"""
        service.repository.save(sample_template)

        entity_spec = service.instantiate_template(
            template_id="tpl_contact",
            entity_name="customer_contact",
            subdomain_number="012",
            table_code="012360",
            field_overrides={"phone": {"required": True}},
            additional_fields=[
                {"field_name": "company", "field_type": "ref", "ref_entity": "company"}
            ]
        )

        assert entity_spec["entity"] == "customer_contact"
        assert entity_spec["table_code"] == "012360"
        assert len(entity_spec["fields"]) == 3  # email, phone, company
        assert entity_spec["fields"]["phone"]["required"] is True

        # Verify usage counter incremented
        template = service.get_template("tpl_contact")
        assert template.times_instantiated == 1

    def test_search_templates(self, service, sample_template):
        """Test searching templates by text"""
        service.repository.save(sample_template)

        # Search by name
        results = service.search_templates("contact")
        assert len(results) >= 1
        assert results[0].template_id == "tpl_contact"

        # Search by description
        results = service.search_templates("standard")
        assert len(results) >= 1

    def test_update_template(self, service, sample_template):
        """Test updating template"""
        service.repository.save(sample_template)

        # Update description
        updated = service.update_template(
            template_id="tpl_contact",
            description="Updated contact template"
        )

        assert updated.description == "Updated contact template"

    def test_create_template_version(self, service, sample_template):
        """Test creating new template version"""
        service.repository.save(sample_template)

        # Create v2 with additional field
        v2 = service.create_template_version(
            template_id="tpl_contact",
            additional_fields=[
                {"field_name": "address", "field_type": "composite", "composite_type": "address_type"}
            ],
            version="2.0.0",
            changelog="Added address field"
        )

        assert v2.version == "2.0.0"
        assert len(v2.fields) == 3  # email, phone, address
        assert v2.previous_version == "1.0.0"

    def test_delete_template(self, service, sample_template):
        """Test deleting template"""
        service.repository.save(sample_template)

        service.delete_template("tpl_contact")

        found = service.get_template("tpl_contact")
        assert found is None

    def test_get_most_used_templates(self, service, sample_template):
        """Test getting most used templates"""
        # Create templates with different usage counts
        sample_template.times_instantiated = 10
        service.repository.save(sample_template)

        template2 = EntityTemplate(
            template_id="tpl_company",
            template_name="Company Template",
            description="Company entity",
            domain_number=DomainNumber("01"),
            base_entity_name="company",
            fields=[TemplateField("name", "text", required=True)],
            times_instantiated=25,
            version="1.0.0"
        )
        service.repository.save(template2)

        # Get most used
        most_used = service.get_most_used_templates(limit=2)
        assert len(most_used) == 2
        assert most_used[0].template_id == "tpl_company"  # Higher usage first
        assert most_used[1].template_id == "tpl_contact"