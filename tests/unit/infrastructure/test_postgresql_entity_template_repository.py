"""Tests for PostgreSQL EntityTemplate repository"""

import pytest
from src.domain.entities.entity_template import EntityTemplate, TemplateField
from src.domain.value_objects import DomainNumber
from src.infrastructure.repositories.postgresql_entity_template_repository import (
    PostgreSQLEntityTemplateRepository,
)
import os


@pytest.fixture
def db_url():
    """Get database URL from environment"""
    return os.getenv(
        "SPECQL_DB_URL", "postgresql://specql_user:specql_dev_password@localhost/specql"
    )


@pytest.fixture
def repository(db_url):
    """Create repository instance"""
    return PostgreSQLEntityTemplateRepository(db_url)


@pytest.fixture
def sample_template():
    """Create a sample template for testing"""
    return EntityTemplate(
        template_id="tpl_test_contact",
        template_name="Test Contact Template",
        description="Contact template for testing",
        domain_number=DomainNumber("01"),
        base_entity_name="contact",
        fields=[
            TemplateField("email", "text", required=True),
            TemplateField("phone", "text", required=False),
        ],
        included_patterns=["audit_trail", "soft_delete"],
        version="1.0.0",
    )


class TestPostgreSQLEntityTemplateRepository:
    """Test PostgreSQL repository for entity templates"""

    def test_save_and_find_by_id(self, repository, sample_template):
        """Test saving and retrieving template by ID"""
        # Save
        repository.save(sample_template)

        # Find
        found = repository.find_by_id("tpl_test_contact")
        assert found is not None
        assert found.template_id == "tpl_test_contact"
        assert found.template_name == "Test Contact Template"
        assert len(found.fields) == 2
        assert found.fields[0].field_name == "email"

    def test_save_update(self, repository, sample_template):
        """Test updating existing template"""
        # Save initial
        repository.save(sample_template)

        # Modify
        sample_template.description = "Updated description"
        sample_template.times_instantiated = 5

        # Save again
        repository.save(sample_template)

        # Verify update
        found = repository.find_by_id("tpl_test_contact")
        assert found.description == "Updated description"
        assert found.times_instantiated == 5

    def test_find_by_name(self, repository, sample_template):
        """Test finding template by name"""
        repository.save(sample_template)

        found = repository.find_by_name("Test Contact Template")
        assert found is not None
        assert found.template_id == "tpl_test_contact"

    def test_find_by_domain(self, repository, sample_template):
        """Test finding templates by domain"""
        repository.save(sample_template)

        # Create another template in same domain
        template2 = EntityTemplate(
            template_id="tpl_test_company",
            template_name="Test Company Template",
            description="Company template",
            domain_number=DomainNumber("01"),
            base_entity_name="company",
            fields=[TemplateField("name", "text", required=True)],
            version="1.0.0",
        )
        repository.save(template2)

        # Find by domain
        templates = repository.find_by_domain("01")
        assert len(templates) >= 2
        template_ids = [t.template_id for t in templates]
        assert "tpl_test_contact" in template_ids
        assert "tpl_test_company" in template_ids

    def test_find_all_public(self, repository, sample_template):
        """Test finding all public templates"""
        repository.save(sample_template)

        # Create private template
        private_template = EntityTemplate(
            template_id="tpl_test_private",
            template_name="Private Template",
            description="Private template",
            domain_number=DomainNumber("02"),
            base_entity_name="private",
            fields=[TemplateField("secret", "text")],
            is_public=False,
            version="1.0.0",
        )
        repository.save(private_template)

        # Find public only
        public_templates = repository.find_all_public()
        template_ids = [t.template_id for t in public_templates]
        assert "tpl_test_contact" in template_ids
        assert "tpl_test_private" not in template_ids

    def test_increment_usage(self, repository, sample_template):
        """Test incrementing usage counter"""
        repository.save(sample_template)

        # Increment 3 times
        repository.increment_usage("tpl_test_contact")
        repository.increment_usage("tpl_test_contact")
        repository.increment_usage("tpl_test_contact")

        # Verify
        found = repository.find_by_id("tpl_test_contact")
        assert found.times_instantiated == 3

    def test_delete(self, repository, sample_template):
        """Test deleting template"""
        repository.save(sample_template)

        # Delete
        repository.delete("tpl_test_contact")

        # Verify deleted
        found = repository.find_by_id("tpl_test_contact")
        assert found is None

    def test_find_nonexistent(self, repository):
        """Test finding template that doesn't exist"""
        found = repository.find_by_id("tpl_nonexistent")
        assert found is None

        found = repository.find_by_name("Nonexistent Template")
        assert found is None
