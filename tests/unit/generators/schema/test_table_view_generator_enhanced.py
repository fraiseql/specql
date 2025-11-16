"""Tests for enhanced table view (tv_) generation"""

import pytest
from src.generators.schema.enhanced_table_view_generator import (
    EnhancedTableViewGenerator,
)
from src.core.ast_models import Entity, FieldDefinition


class TestTableViewGeneration:
    """Test enhanced tv_ table generation"""

    @pytest.fixture
    def generator(self):
        return EnhancedTableViewGenerator()

    @pytest.fixture
    def sample_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text"),
                "status": FieldDefinition(
                    name="status", type_name="enum", values=["lead", "qualified"]
                ),
            },
        )

    def test_table_view_structure(self, generator, sample_entity):
        """Test table view has correct JSONB structure"""
        # Act
        result = generator.generate(sample_entity)

        # Assert
        assert "CREATE TABLE crm.tv_contact" in result
        assert "pk_contact INTEGER PRIMARY KEY" in result
        assert "id UUID NOT NULL UNIQUE" in result
        assert "data JSONB NOT NULL" in result
        assert "refreshed_at TIMESTAMPTZ DEFAULT now()" in result

    def test_table_view_foreign_key_to_base(self, generator, sample_entity):
        """Test tv_ has FK to tb_ for data integrity"""
        # Act
        result = generator.generate(sample_entity)

        # Assert
        assert "REFERENCES crm.tb_contact(pk_contact)" in result

    def test_table_view_refresh_function(self, generator, sample_entity):
        """Test refresh function generated for syncing tb_ -> tv_"""
        # Act
        result = generator.generate(sample_entity)

        # Assert
        assert "CREATE OR REPLACE FUNCTION crm.refresh_tv_contact()" in result
        assert "INSERT INTO crm.tv_contact" in result
        assert "NEW.pk_contact" in result
        assert "NEW.id" in result
        assert "jsonb_build_object" in result
        assert "ON CONFLICT (pk_contact)" in result
        assert "DO UPDATE SET" in result

    def test_table_view_trigger(self, generator, sample_entity):
        """Test trigger keeps tv_ in sync with tb_"""
        # Act
        result = generator.generate(sample_entity)

        # Assert
        assert "CREATE TRIGGER trg_refresh_tv_contact" in result
        assert "AFTER INSERT OR UPDATE ON crm.tb_contact" in result
        assert "EXECUTE FUNCTION crm.refresh_tv_contact()" in result
