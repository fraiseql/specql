"""
Integration tests for SchemaRegistry across the full pipeline

Tests that schema_registry properly affects:
- Table generation (tenant_id column)
- Trinity helpers (tenant-aware parameters)
- FK resolution (correct schema mapping)
- Alias resolution (management → crm)
"""

import pytest
from src.core.ast_models import Entity, FieldDefinition
from src.generators.table_generator import TableGenerator
from src.generators.trinity_helper_generator import TrinityHelperGenerator
from src.generators.actions.step_compilers.fk_resolver import ForeignKeyResolver
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry


@pytest.fixture
def crm_entity():
    """Test entity in multi-tenant schema (crm)"""
    return Entity(
        name="Contact",
        schema="crm",  # Multi-tenant domain
        description="Customer contact",
        fields={
            "email": FieldDefinition(name="email", type_name="text", nullable=False),
            "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company"),
        },
    )


@pytest.fixture
def catalog_entity():
    """Test entity in shared schema (catalog)"""
    return Entity(
        name="Manufacturer",
        schema="catalog",  # Shared reference data
        description="Product manufacturer",
        fields={"name": FieldDefinition(name="name", type_name="text", nullable=False)},
    )


class TestMultiTenantSchemaGeneration:
    """Test that multi-tenant schemas get tenant_id column"""

    def test_crm_entity_has_tenant_id(self, table_generator, crm_entity):
        """CRM schema (multi_tenant=true) should generate tenant_id column"""
        result = table_generator.generate_table_ddl(crm_entity)

        # Should have tenant_id column
        assert "tenant_id UUID NOT NULL" in result

        # Should reference tenant table
        assert "REFERENCES" in result and "tenant" in result.lower()

    def test_catalog_entity_no_tenant_id(self, table_generator, catalog_entity):
        """Catalog schema (multi_tenant=false) should NOT have tenant_id"""
        result = table_generator.generate_table_ddl(catalog_entity)

        # Should NOT have tenant_id column
        assert "tenant_id" not in result.lower()


class TestAliasResolution:
    """Test that schema aliases resolve correctly"""

    def test_management_alias_resolves_to_crm(self, schema_registry):
        """'management' is alias for 'crm' domain"""
        assert schema_registry.is_multi_tenant("management") is True
        assert schema_registry.get_canonical_schema_name("management") == "crm"

    def test_tenant_alias_resolves_to_projects(self, schema_registry):
        """'tenant' is alias for 'projects' domain"""
        assert schema_registry.is_multi_tenant("tenant") is True
        assert schema_registry.get_canonical_schema_name("tenant") == "projects"

    def test_dim_alias_resolves_to_projects(self, schema_registry):
        """'dim' is alias for 'projects' domain"""
        assert schema_registry.is_multi_tenant("dim") is True
        assert schema_registry.get_canonical_schema_name("dim") == "projects"

    def test_management_entity_generates_with_tenant_id(self, table_generator):
        """Entity with schema='management' should get tenant_id (via crm)"""
        entity = Entity(
            name="Contact",
            schema="management",  # Alias for crm
            fields={},
        )

        result = table_generator.generate_table_ddl(entity)
        assert "tenant_id UUID NOT NULL" in result


class TestFKResolverIntegration:
    """Test FK resolver uses registry for schema mapping"""

    def test_manufacturer_resolves_to_catalog(self, naming_conventions):
        """Manufacturer should map to 'catalog' schema (not 'product')"""
        resolver = ForeignKeyResolver(naming_conventions)

        schema = resolver._resolve_entity_schema("Manufacturer")

        # Should be catalog (from registry), not product (old bug)
        assert schema == "catalog"

    def test_contact_resolves_to_crm(self, naming_conventions):
        """Contact should map to 'crm' schema"""
        resolver = ForeignKeyResolver(naming_conventions)

        schema = resolver._resolve_entity_schema("Contact")

        assert schema == "crm"

    def test_unregistered_entity_uses_inference(self, naming_conventions):
        """Unregistered entities should fall back to inference"""
        resolver = ForeignKeyResolver(naming_conventions)

        # UnknownEntity not in registry
        schema = resolver._resolve_entity_schema("UnknownEntity")

        # Should return inferred schema (lowercase entity name)
        assert schema == "unknownentity"


class TestFrameworkSchemas:
    """Test framework schemas (common, app, core) behavior"""

    def test_common_is_framework_schema(self, schema_registry):
        """'common' should be recognized as framework schema"""
        assert schema_registry.is_framework_schema("common") is True
        assert schema_registry.is_multi_tenant("common") is False

    def test_app_is_framework_schema(self, schema_registry):
        """'app' should be recognized as framework schema"""
        assert schema_registry.is_framework_schema("app") is True
        assert schema_registry.is_multi_tenant("app") is False

    def test_core_is_framework_schema(self, schema_registry):
        """'core' should be recognized as framework schema"""
        assert schema_registry.is_framework_schema("core") is True
        assert schema_registry.is_multi_tenant("core") is False


class TestTrinityHelperGeneration:
    """Test Trinity helpers respect multi-tenant flag"""

    def test_multi_tenant_helpers_have_tenant_param(self, trinity_helper_generator, crm_entity):
        """Multi-tenant entities should have tenant_id in helper functions"""
        result = trinity_helper_generator.generate_all_helpers(crm_entity)

        # Should have tenant_id parameter in pk/id/identifier helpers
        assert "tenant_id UUID" in result

    def test_shared_helpers_no_tenant_param(self, trinity_helper_generator, catalog_entity):
        """Shared entities should NOT have tenant_id in helpers"""
        result = trinity_helper_generator.generate_all_helpers(catalog_entity)

        # Should NOT have tenant_id parameter
        # (Check that tenant_id is not in function signatures)
        lines = result.split("\n")
        function_lines = [
            l for l in lines if "CREATE FUNCTION" in l or "CREATE OR REPLACE FUNCTION" in l
        ]

        for line in function_lines:
            # tenant_id should not appear in function parameters
            if "tenant_id" in line.lower():
                pytest.fail(f"Shared schema function should not have tenant_id: {line}")
