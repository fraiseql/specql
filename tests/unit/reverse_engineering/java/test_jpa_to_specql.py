"""Tests for JPA to SpecQL converter"""

import pytest
from src.reverse_engineering.java.jpa_to_specql import JPAToSpecQLConverter
from src.reverse_engineering.java.jpa_visitor import JPAEntity, JPAField


class TestJPAToSpecQLConverter:
    """Test JPA to SpecQL conversion"""

    @pytest.fixture
    def converter(self):
        return JPAToSpecQLConverter()

    def test_simple_entity_conversion(self, converter):
        """Test converting a simple JPA entity"""
        jpa_entity = JPAEntity(
            class_name="Contact",
            table_name="contacts",
            schema="crm",
            id_field="id",
            fields=[
                JPAField(name="id", java_type="Long"),
                JPAField(name="email", java_type="String", nullable=False),
                JPAField(name="name", java_type="String", nullable=True),
            ],
        )

        entity = converter.convert(jpa_entity)

        assert entity.name == "Contact"
        assert entity.schema == "crm"
        assert entity.table == "contacts"
        assert len(entity.fields) == 2  # ID field is skipped

        # Check email field
        email_field = entity.fields["email"]
        assert email_field.name == "email"
        assert email_field.type_name == "text"
        assert not email_field.nullable

        # Check name field
        name_field = entity.fields["name"]
        assert name_field.name == "name"
        assert name_field.type_name == "text"
        assert name_field.nullable  is True

    def test_relationship_conversion(self, converter):
        """Test converting entities with relationships"""
        jpa_entity = JPAEntity(
            class_name="Contact",
            table_name="contacts",
            id_field="id",
            fields=[
                JPAField(name="id", java_type="Long"),
                JPAField(
                    name="company",
                    java_type="Company",
                    is_relationship=True,
                    relationship_type="ManyToOne",
                    target_entity="Company",
                ),
                JPAField(
                    name="tasks",
                    java_type="List<Task>",
                    is_relationship=True,
                    relationship_type="OneToMany",
                    target_entity="Task",
                ),
            ],
        )

        entity = converter.convert(jpa_entity)

        assert len(entity.fields) == 2

        # Check ManyToOne relationship
        company_field = entity.fields["company"]
        assert company_field.name == "company"
        assert company_field.type_name == "ref(Company)"
        assert company_field.reference_entity == "Company"

        # Check OneToMany relationship
        tasks_field = entity.fields["tasks"]
        assert tasks_field.name == "tasks"
        assert tasks_field.type_name == "list(Task)"
        assert tasks_field.item_type == "Task"

    def test_enum_conversion(self, converter):
        """Test converting entities with enum fields"""
        jpa_entity = JPAEntity(
            class_name="Contact",
            table_name="contacts",
            id_field="id",
            fields=[
                JPAField(name="id", java_type="Long"),
                JPAField(
                    name="status",
                    java_type="ContactStatus",
                    is_enum=True,
                    enum_type="STRING",
                ),
            ],
        )

        entity = converter.convert(jpa_entity)

        assert len(entity.fields) == 1

        status_field = entity.fields["status"]
        assert status_field.name == "status"
        assert status_field.type_name == "text"  # Enums map to text

    def test_default_schema(self, converter):
        """Test default schema assignment"""
        jpa_entity = JPAEntity(
            class_name="Contact",
            table_name="contacts",
            schema=None,  # No schema specified
            id_field="id",
            fields=[
                JPAField(name="id", java_type="Long"),
                JPAField(name="email", java_type="String"),
            ],
        )

        entity = converter.convert(jpa_entity)

        assert entity.schema == "public"  # Default schema

    def test_skip_id_field(self, converter):
        """Test that ID fields are skipped (handled by Trinity pattern)"""
        jpa_entity = JPAEntity(
            class_name="Contact",
            table_name="contacts",
            id_field="id",
            fields=[
                JPAField(name="id", java_type="Long"),  # This should be skipped
                JPAField(name="email", java_type="String"),
            ],
        )

        entity = converter.convert(jpa_entity)

        assert len(entity.fields) == 1
        assert "id" not in entity.fields
        assert "email" in entity.fields
