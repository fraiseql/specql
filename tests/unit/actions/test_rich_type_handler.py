"""
Tests for Rich Type Handler
Phase 2: JSONB composite field manipulation
"""

import pytest

from src.core.ast_models import Entity, FieldDefinition, FieldTier
from src.generators.actions.step_compilers.rich_type_handler import RichTypeHandler


class TestRichTypeHandler:
    """Test JSONB composite field operations"""

    @pytest.fixture
    def handler(self):
        """Create rich type handler instance"""
        return RichTypeHandler()

    @pytest.fixture
    def contact_entity(self):
        """Create test Contact entity with composite address field"""
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text"),
                "address": FieldDefinition(
                    name="address", type_name="SimpleAddress", tier=FieldTier.COMPOSITE
                ),
            },
        )

    def test_extract_jsonb_value_simple(self, handler, contact_entity):
        """Test extracting a simple JSONB field value"""
        expr = handler.extract_jsonb_value("address.street", contact_entity)

        assert expr == "v_address->>'street'"

    def test_extract_jsonb_value_nested(self, handler, contact_entity):
        """Test extracting a nested JSONB field value"""
        expr = handler.extract_jsonb_value("address.location.city", contact_entity)

        assert expr == "v_address#>>'{location,city}'"

    def test_set_jsonb_value_string(self, handler, contact_entity):
        """Test setting a string value in JSONB field"""
        sql = handler.set_jsonb_value("address.street", "'123 Main St'", contact_entity)

        expected = "v_address := jsonb_set(v_address, '{street}', \"123 Main St\");"
        assert sql == expected

    def test_set_jsonb_value_number(self, handler, contact_entity):
        """Test setting a number value in JSONB field"""
        sql = handler.set_jsonb_value("address.zip_code", "12345", contact_entity)

        expected = "v_address := jsonb_set(v_address, '{zip_code}', 12345);"
        assert sql == expected

    def test_set_jsonb_value_boolean(self, handler, contact_entity):
        """Test setting a boolean value in JSONB field"""
        sql = handler.set_jsonb_value("address.is_primary", "true", contact_entity)

        expected = "v_address := jsonb_set(v_address, '{is_primary}', true);"
        assert sql == expected

    def test_build_jsonb_object(self, handler, contact_entity):
        """Test building a JSONB object from field assignments"""
        assignments = {
            "address.street": "'123 Main St'",
            "address.city": "'Springfield'",
            "address.zip_code": "12345",
        }

        sql = handler.build_jsonb_object(assignments, contact_entity)

        expected = (
            "jsonb_build_object('street', '123 Main St', 'city', 'Springfield', 'zip_code', 12345)"
        )
        assert sql == expected

    def test_invalid_field_path(self, handler, contact_entity):
        """Test error handling for invalid field paths"""
        with pytest.raises(ValueError, match="Invalid field path"):
            handler.extract_jsonb_value("street", contact_entity)

    def test_non_composite_field(self, handler, contact_entity):
        """Test error handling for non-composite fields"""
        with pytest.raises(ValueError, match="not a composite"):
            handler.extract_jsonb_value("email.domain", contact_entity)
