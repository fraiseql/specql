"""
Tests for Foreign Key Resolver
Phase 2: Tier 3 entity reference resolution
"""

import pytest

from src.core.ast_models import Entity, FieldDefinition
from src.generators.actions.step_compilers.fk_resolver import ForeignKeyResolver


class TestForeignKeyResolver:
    """Test FK resolution for Tier 3 entity references"""

    @pytest.fixture
    def resolver(self):
        """Create FK resolver instance"""
        return ForeignKeyResolver()

    @pytest.fixture
    def task_entity(self):
        """Create test Task entity"""
        return Entity(
            name="Task",
            schema="crm",
            fields={
                "title": FieldDefinition(name="title", type_name="text"),
                "contact_id": FieldDefinition(name="contact_id", type_name="integer"),
            },
        )

    def test_resolve_fk_reference_simple(self, resolver, task_entity):
        """Test resolving a simple FK reference using Trinity helper"""
        sql = resolver.resolve_fk_reference("ref(Contact).uuid", task_entity)

        expected = """    -- Resolve FK: ref(Contact).uuid → pk_contact
    v_contact_id := crm.contact_pk(v_uuid_param, auth_tenant_id);
    IF v_contact_id IS NULL THEN
        v_result.status := 'error';
        v_result.message := 'Contact not found';
        RETURN v_result;
    END IF;"""

        assert sql == expected

    def test_generate_fk_assignment(self, resolver, task_entity):
        """Test generating FK assignment with Trinity resolution"""
        sql = resolver.generate_fk_assignment("contact_id", "ref(Contact).uuid", task_entity)

        expected = """    -- Resolve and assign FK: contact_id = ref(Contact).uuid
    -- Resolve FK: ref(Contact).uuid → pk_contact
    v_contact_id := crm.contact_pk(v_uuid_param, auth_tenant_id);
    IF v_contact_id IS NULL THEN
        v_result.status := 'error';
        v_result.message := 'Contact not found';
        RETURN v_result;
    END IF;

    v_contact_id := v_contact_id;"""

        assert sql == expected

    def test_parse_reference_expr(self, resolver):
        """Test parsing reference expressions"""
        entity, field = resolver._parse_reference_expr("ref(Contact).uuid")
        assert entity == "Contact"
        assert field == "uuid"

        entity, field = resolver._parse_reference_expr("ref(Task).title")
        assert entity == "Task"
        assert field == "title"

    def test_invalid_reference_expr(self, resolver):
        """Test error handling for invalid reference expressions"""
        with pytest.raises(ValueError, match="Invalid reference format"):
            resolver._parse_reference_expr("Contact.uuid")

        with pytest.raises(ValueError, match="Invalid reference format"):
            resolver._parse_reference_expr("ref(Contact)")

    def test_infer_schema(self, resolver):
        """Test schema inference"""
        assert resolver._infer_schema("Contact") == "crm"
        assert resolver._infer_schema("Task") == "crm"
        assert resolver._infer_schema("Manufacturer") == "product"
        assert resolver._infer_schema("Unknown") == "public"
