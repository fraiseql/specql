"""Tests for tenant-scoped composite index generation."""

import pytest
from src.generators.schema.tenant_indexes import (
    generate_tenant_indexes,
    generate_tenant_isolation_index,
    generate_tenant_id_lookup_index,
    _is_entity_hierarchical,
)
from src.core.ast_models import EntityDefinition, FieldDefinition, FieldTier


class TestGenerateTenantIndexes:
    """Test tenant index generation."""

    def test_non_hierarchical_entity_indexes(self):
        """Test indexes for non-hierarchical entity."""
        entity = EntityDefinition(
            name="contact",
            schema="tenant",
            fields={"name": FieldDefinition(name="name", type_name="string")},
        )

        result = generate_tenant_indexes(entity, "tenant")

        expected = [
            "CREATE INDEX idx_contact_tenant\n    ON tenant.tb_contact(tenant_id)\n    WHERE deleted_at IS NULL;",
            "CREATE UNIQUE INDEX idx_contact_tenant_id\n    ON tenant.tb_contact(tenant_id, id);",
        ]

        assert result == expected

    def test_hierarchical_entity_indexes(self):
        """Test indexes for hierarchical entity."""
        entity = EntityDefinition(
            name="location",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "parent": FieldDefinition(name="parent", type_name="ref", tier=FieldTier.REFERENCE, reference_entity="location"),
            },
        )

        result = generate_tenant_indexes(entity, "tenant")

        expected = [
            "CREATE INDEX idx_location_tenant\n    ON tenant.tb_location(tenant_id)\n    WHERE deleted_at IS NULL;",
            "CREATE UNIQUE INDEX idx_location_tenant_id\n    ON tenant.tb_location(tenant_id, id);",
            "CREATE INDEX idx_location_tenant_path\n    ON tenant.tb_location(tenant_id, path)\n    WHERE deleted_at IS NULL;",
            "CREATE INDEX idx_location_tenant_parent\n    ON tenant.tb_location(tenant_id, fk_parent_location)\n    WHERE deleted_at IS NULL;",
        ]

        assert result == expected

    def test_catalog_schema_indexes(self):
        """Test indexes for catalog schema (non-tenant)."""
        entity = EntityDefinition(
            name="country",
            schema="catalog",
            fields={"name": FieldDefinition(name="name", type_name="string")},
        )

        result = generate_tenant_indexes(entity, "catalog")

        expected = [
            "CREATE INDEX idx_country_tenant\n    ON catalog.tb_country(tenant_id)\n    WHERE deleted_at IS NULL;",
            "CREATE UNIQUE INDEX idx_country_tenant_id\n    ON catalog.tb_country(tenant_id, id);",
        ]

        assert result == expected


class TestIndividualIndexFunctions:
    """Test individual index generation functions."""

    def test_tenant_isolation_index(self):
        """Test tenant isolation index generation."""
        entity = EntityDefinition(
            name="product",
            schema="tenant",
            fields={"name": FieldDefinition(name="name", type_name="string")},
        )

        result = generate_tenant_isolation_index(entity, "tenant")

        expected = "CREATE INDEX idx_product_tenant\n    ON tenant.tb_product(tenant_id)\n    WHERE deleted_at IS NULL;"

        assert result == expected

    def test_tenant_id_lookup_index(self):
        """Test tenant + ID lookup index generation."""
        entity = EntityDefinition(
            name="product",
            schema="tenant",
            fields={"name": FieldDefinition(name="name", type_name="string")},
        )

        result = generate_tenant_id_lookup_index(entity, "tenant")

        expected = (
            "CREATE UNIQUE INDEX idx_product_tenant_id\n    ON tenant.tb_product(tenant_id, id);"
        )

        assert result == expected


class TestIsEntityHierarchical:
    """Test hierarchical entity detection."""

    def test_non_hierarchical_entity(self):
        """Test detection of non-hierarchical entity."""
        entity = EntityDefinition(
            name="contact",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "company": FieldDefinition(name="company", type_name="ref", tier=FieldTier.REFERENCE, reference_entity="company"),
            },
        )

        assert not _is_entity_hierarchical(entity)

    def test_hierarchical_entity_with_parent_field(self):
        """Test detection of hierarchical entity with parent field."""
        entity = EntityDefinition(
            name="location",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "parent": FieldDefinition(name="parent", type_name="ref", tier=FieldTier.REFERENCE, reference_entity="location"),
            },
        )

        assert _is_entity_hierarchical(entity)

    def test_hierarchical_entity_with_fk_parent_field(self):
        """Test detection with fk_parent_ naming convention."""
        entity = EntityDefinition(
            name="category",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "fk_parent_category": FieldDefinition(
                    name="fk_parent_category", type_name="ref", tier=FieldTier.REFERENCE, reference_entity="category"
                ),
            },
        )

        assert _is_entity_hierarchical(entity)

    def test_entity_with_no_reference_fields(self):
        """Test entity with no reference fields."""
        entity = EntityDefinition(
            name="user",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "email": FieldDefinition(name="email", type_name="email"),
            },
        )

        assert not _is_entity_hierarchical(entity)


class TestIndexIntegration:
    """Test that tenant indexes integrate properly with schema generation."""

    def test_tenant_indexes_in_schema_ddl(self):
        """Test that tenant indexes appear in generated schema DDL."""
        from src.generators.schema.schema_generator import SchemaGenerator

        entity = EntityDefinition(
            name="department",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "parent": FieldDefinition(name="parent", type_name="ref", tier=FieldTier.REFERENCE, reference_entity="department"),
            },
        )

        generator = SchemaGenerator()
        ddl = generator.generate_table(entity)

        # Check that tenant indexes are included
        assert "CREATE INDEX idx_department_tenant" in ddl
        assert "CREATE UNIQUE INDEX idx_department_tenant_id" in ddl
        assert "CREATE INDEX idx_department_tenant_path" in ddl  # hierarchical
        assert "CREATE INDEX idx_department_tenant_parent" in ddl  # hierarchical

        # Check partial index clauses
        assert "WHERE deleted_at IS NULL" in ddl
