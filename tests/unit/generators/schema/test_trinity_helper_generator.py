"""Tests for Trinity helper function generation"""

import pytest
from src.generators.schema.trinity_helper_generator import TrinityHelperGenerator
from src.core.ast_models import Entity


class TestTrinityHelperFunctions:
    """Test Trinity pattern helper functions"""

    @pytest.fixture
    def generator(self):
        return TrinityHelperGenerator()

    @pytest.fixture
    def sample_entity(self):
        return Entity(name="Contact", schema="crm")

    def test_generate_pk_function(self, generator, sample_entity):
        """Test {entity}_pk() function for UUID/TEXT -> INTEGER"""
        # Act
        result = generator.generate(sample_entity)

        # Assert
        assert "CREATE OR REPLACE FUNCTION crm.contact_pk(p_identifier TEXT)" in result
        assert "RETURNS INTEGER" in result
        assert "SELECT pk_contact" in result
        assert "FROM crm.tb_contact" in result
        assert "id::TEXT = p_identifier" in result
        assert "pk_contact::TEXT = p_identifier" in result

    def test_generate_id_function(self, generator, sample_entity):
        """Test {entity}_id() function for INTEGER -> UUID"""
        # Act
        result = generator.generate(sample_entity)

        # Assert
        assert "CREATE OR REPLACE FUNCTION crm.contact_id(p_pk INTEGER)" in result
        assert "RETURNS UUID" in result
        assert "SELECT id FROM crm.tb_contact" in result
        assert "WHERE pk_contact = p_pk" in result

    def test_helper_functions_marked_stable(self, generator, sample_entity):
        """Test helper functions marked as STABLE for performance"""
        # Act
        result = generator.generate(sample_entity)

        # Assert
        assert "LANGUAGE sql STABLE" in result
