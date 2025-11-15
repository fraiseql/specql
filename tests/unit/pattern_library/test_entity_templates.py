"""Tests for entity templates (Tier 3)"""

import pytest
from src.pattern_library.api import PatternLibrary


class TestEntityTemplates:
    """Test entity template functionality"""

    @pytest.fixture
    def library(self):
        """Create a test library with seeded patterns and templates"""
        lib = PatternLibrary(":memory:")

        # Add minimal domain patterns manually for testing
        lib.add_domain_pattern(
            name="state_machine",
            category="workflow",
            description="State machine pattern",
            parameters={"states": {"type": "array"}, "transitions": {"type": "object"}},
            implementation={"fields": [], "actions": []}
        )
        lib.add_domain_pattern(
            name="audit_trail",
            category="audit",
            description="Audit trail pattern",
            parameters={"track_versions": {"type": "boolean"}},
            implementation={"fields": [], "triggers": []}
        )
        lib.add_domain_pattern(
            name="soft_delete",
            category="data_management",
            description="Soft delete pattern",
            parameters={},
            implementation={"fields": [], "actions": []}
        )

        # Add contact template manually for testing
        lib.add_entity_template(
            template_name="contact",
            template_namespace="crm",
            description="CRM contact with state machine, audit trail, and soft delete",
            default_fields={
                "first_name": {"type": "text", "required": True},
                "last_name": {"type": "text", "required": True},
                "email": {"type": "email", "required": True, "unique": True},
                "phone": {"type": "text"}
            },
            default_patterns={
                "state_machine": {
                    "states": ["lead", "prospect", "customer"],
                    "transitions": {"lead->prospect": {}, "prospect->customer": {}},
                    "initial_state": "lead"
                },
                "audit_trail": {"track_versions": True},
                "soft_delete": {}
            },
            default_actions={
                "qualify": {
                    "description": "Qualify lead as prospect",
                    "steps": [{"type": "validate", "condition": "state == 'lead'"}]
                }
            }
        )

        yield lib
        lib.close()

    def test_add_entity_template(self, library):
        """Test adding an entity template"""
        template_id = library.add_entity_template(
            template_name="test_template",
            template_namespace="test",
            description="Test template",
            default_fields={"name": {"type": "text"}},
            default_patterns={},
            default_actions={}
        )

        assert template_id > 0

        # Retrieve and verify
        template = library.get_entity_template("test_template")
        assert template is not None
        assert template["template_name"] == "test_template"
        assert template["template_namespace"] == "test"
        assert template["default_fields"]["name"]["type"] == "text"

    def test_get_entity_templates_by_namespace(self, library):
        """Test getting templates by namespace"""
        # Add another CRM template
        library.add_entity_template(
            template_name="test_crm",
            template_namespace="crm",
            description="Another CRM template",
            default_fields={"field": {"type": "text"}},
            default_patterns={},
            default_actions={}
        )

        crm_templates = library.get_entity_templates_by_namespace("crm")
        assert len(crm_templates) >= 2  # contact + test_crm

        template_names = [t["template_name"] for t in crm_templates]
        assert "contact" in template_names
        assert "test_crm" in template_names

    def test_instantiate_entity_template_basic(self, library):
        """Test basic entity template instantiation"""
        result = library.instantiate_entity_template("contact", "TestContact")

        assert result is not None
        assert result["entity"] == "TestContact"
        assert result["schema"] == "crm"
        assert "fields" in result
        assert "actions" in result

        # Check that default fields are present
        field_names = [f["name"] for f in result["fields"] if isinstance(f, dict)]
        assert "first_name" in field_names
        assert "last_name" in field_names
        assert "email" in field_names

    def test_instantiate_entity_template_with_custom_fields(self, library):
        """Test instantiation with custom fields"""
        custom_fields = {
            "custom_field": {"type": "text", "required": True}
        }

        result = library.instantiate_entity_template(
            "contact",
            "TestContact",
            custom_fields=custom_fields
        )

        field_names = [f["name"] for f in result["fields"] if isinstance(f, dict)]
        assert "custom_field" in field_names

        # Find the custom field
        custom_field = next(f for f in result["fields"] if isinstance(f, dict) and f["name"] == "custom_field")
        assert custom_field["required"] is True

    def test_validate_entity_template(self, library):
        """Test entity template validation"""
        # Valid template should pass
        validation = library.validate_entity_template("contact")
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0

        # Test with non-existent template
        validation = library.validate_entity_template("non_existent")
        assert validation["valid"] is False
        assert "Template not found" in validation["errors"][0]

    def test_template_with_invalid_pattern(self, library):
        """Test template validation with invalid pattern reference"""
        # Add template with invalid pattern
        library.add_entity_template(
            template_name="invalid_template",
            template_namespace="test",
            description="Template with invalid pattern",
            default_fields={},
            default_patterns={"non_existent_pattern": {}},
            default_actions={}
        )

        validation = library.validate_entity_template("invalid_template")
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
        assert "Referenced pattern not found" in validation["errors"][0]

    def test_instantiation_records_usage(self, library):
        """Test that instantiation is recorded"""
        # Instantiate template
        library.instantiate_entity_template("contact", "UsageTestContact")

        # Check that instantiation was recorded
        cursor = library.db.execute(
            "SELECT * FROM pattern_instantiations WHERE entity_name = ? AND entity_template_id IS NOT NULL",
            ("UsageTestContact",)
        )
        record = cursor.fetchone()

        assert record is not None
        assert record["entity_name"] == "UsageTestContact"
        assert record["entity_template_id"] is not None

    def test_get_all_entity_templates_method(self, library):
        """Test that get_all_entity_templates method works"""
        templates = library.get_all_entity_templates()
        assert isinstance(templates, list)

        # Should have at least the contact template from the fixture
        assert len(templates) >= 1
        assert any(t["template_name"] == "contact" for t in templates)

    def test_template_validation_with_minimal_template(self, library):
        """Test template validation with a minimal template"""
        initial_count = len(library.get_all_entity_templates())

        # Add a minimal template
        library.add_entity_template(
            template_name="minimal_test",
            template_namespace="test",
            description="Minimal test template",
            default_fields={"name": {"type": "text"}},
            default_patterns={},
            default_actions={}
        )

        # Should be able to retrieve it
        templates = library.get_all_entity_templates()
        assert len(templates) == initial_count + 1

        minimal_template = next(t for t in templates if t["template_name"] == "minimal_test")
        assert minimal_template["template_namespace"] == "test"