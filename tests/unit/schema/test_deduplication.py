"""
Tests for deduplication pattern generation
Tests the 3-field deduplication pattern implementation
"""

import pytest
from src.generators.schema.deduplication import (
    generate_deduplication_fields,
    generate_deduplication_indexes,
)
from src.core.ast_models import EntityDefinition


class TestDeduplicationFields:
    """Test deduplication field generation."""

    def test_generate_deduplication_fields_basic(self):
        """Test basic deduplication field generation."""
        entity = EntityDefinition(name="Contact", schema="crm")

        result = generate_deduplication_fields(entity)

        assert "identifier TEXT NOT NULL" in result
        assert "sequence_number INTEGER NOT NULL DEFAULT 1" in result
        assert "display_identifier TEXT GENERATED ALWAYS AS" in result
        assert "WHEN sequence_number > 1" in result
        assert "THEN identifier || '#' || sequence_number" in result
        assert "ELSE identifier" in result

    def test_generate_deduplication_fields_no_constraints_in_fields(self):
        """Test that constraints are not included in field definitions."""
        entity = EntityDefinition(name="Product", schema="inventory")

        result = generate_deduplication_fields(entity)

        # Should not contain constraint definitions
        assert "UNIQUE" not in result
        assert "CONSTRAINT" not in result


class TestDeduplicationIndexes:
    """Test deduplication index and constraint generation."""

    def test_generate_deduplication_indexes_tenant_scoped(self):
        """Test tenant-scoped deduplication indexes."""
        entity = EntityDefinition(name="Location", schema="tenant")

        result = generate_deduplication_indexes(entity, "tenant")

        assert "unique_tenant_display_identifier" in result
        assert "UNIQUE (tenant_id, display_identifier)" in result
        assert "unique_tenant_identifier_sequence" in result
        assert "UNIQUE (tenant_id, identifier, sequence_number)" in result
        assert "idx_location_tenant_identifier" in result
        assert "ON tenant.tb_location(tenant_id, identifier)" in result

    def test_generate_deduplication_indexes_drop_existing(self):
        """Test that existing constraints are dropped."""
        entity = EntityDefinition(name="Asset", schema="inventory")

        result = generate_deduplication_indexes(entity, "inventory")

        assert "DROP CONSTRAINT IF EXISTS tb_asset_display_identifier_key" in result


class TestDeduplicationIntegration:
    """Test deduplication integration with schema generator."""

    def test_deduplication_in_schema_generator(self):
        """Test that deduplication fields are included in generated schema."""
        from src.generators.schema.schema_generator import SchemaGenerator

        entity = EntityDefinition(name="Manufacturer", schema="inventory", fields={})

        generator = SchemaGenerator()
        ddl = generator.generate_table(entity)

        # Check deduplication fields are present
        assert "identifier TEXT NOT NULL" in ddl
        assert "sequence_number INTEGER NOT NULL DEFAULT 1" in ddl
        assert "display_identifier TEXT GENERATED ALWAYS" in ddl

        # Check deduplication constraints are present
        assert "unique_tenant_display_identifier" in ddl
        assert "unique_tenant_identifier_sequence" in ddl
