from unittest.mock import Mock

import pytest

from src.generators.schema.naming_conventions import DomainInfo
from src.generators.schema.schema_registry import SchemaRegistry


@pytest.fixture
def mock_domain_registry():
    """Create a mock domain registry with test domains"""
    registry = Mock()

    # Mock domain data
    crm_domain = DomainInfo(
        domain_code="2",
        domain_name="crm",
        description="Customer relationship management",
        subdomains={},
        aliases=["management"],
        multi_tenant=True,
    )

    catalog_domain = DomainInfo(
        domain_code="3",
        domain_name="catalog",
        description="Product catalog",
        subdomains={},
        aliases=[],
        multi_tenant=False,
    )

    projects_domain = DomainInfo(
        domain_code="4",
        domain_name="projects",
        description="Project management",
        subdomains={},
        aliases=["tenant", "dim"],
        multi_tenant=True,
    )

    # Configure mock behavior
    def mock_get_domain(identifier):
        if identifier in ["crm", "management"]:
            return crm_domain
        elif identifier == "catalog":
            return catalog_domain
        elif identifier in ["projects", "tenant", "dim"]:
            return projects_domain
        return None

    registry.get_domain.side_effect = mock_get_domain
    return registry


@pytest.fixture
def schema_registry():
    """Create SchemaRegistry instance"""
    return SchemaRegistry()


def test_is_multi_tenant_true_for_multi_tenant_domains(schema_registry):
    """Test that multi-tenant domains return True"""
    assert schema_registry.is_multi_tenant("crm")  is True
    assert schema_registry.is_multi_tenant("management")  is True  # alias
    assert schema_registry.is_multi_tenant("projects")  is True
    assert schema_registry.is_multi_tenant("tenant")  is True  # alias
    assert schema_registry.is_multi_tenant("dim")  is True  # alias


def test_is_multi_tenant_false_for_shared_domains(schema_registry):
    """Test that shared domains return False"""
    assert not schema_registry.is_multi_tenant("catalog")


def test_is_multi_tenant_false_for_unknown_domains(schema_registry):
    """Test that unknown domains default to False (safe)"""
    assert not schema_registry.is_multi_tenant("unknown_schema")
    assert not schema_registry.is_multi_tenant("nonexistent")


def test_is_multi_tenant_false_for_framework_schemas(schema_registry):
    """Test that framework schemas return False"""
    assert not schema_registry.is_multi_tenant("common")
    assert not schema_registry.is_multi_tenant("app")
    assert not schema_registry.is_multi_tenant("core")


def test_get_canonical_schema_name_resolves_aliases(schema_registry):
    """Test that aliases are resolved to canonical names"""
    assert schema_registry.get_canonical_schema_name("management") == "crm"
    assert schema_registry.get_canonical_schema_name("tenant") == "projects"
    assert schema_registry.get_canonical_schema_name("dim") == "projects"


def test_get_canonical_schema_name_returns_input_for_canonical_names(schema_registry):
    """Test that canonical names are returned as-is"""
    assert schema_registry.get_canonical_schema_name("crm") == "crm"
    assert schema_registry.get_canonical_schema_name("catalog") == "catalog"
    assert schema_registry.get_canonical_schema_name("projects") == "projects"


def test_get_canonical_schema_name_returns_input_for_unknown_schemas(schema_registry):
    """Test that unknown schemas are returned as-is"""
    assert schema_registry.get_canonical_schema_name("unknown") == "unknown"
    assert schema_registry.get_canonical_schema_name("nonexistent") == "nonexistent"


def test_is_framework_schema_true_for_framework_schemas(schema_registry):
    """Test framework schema detection"""
    assert schema_registry.is_framework_schema("common")  is True
    assert schema_registry.is_framework_schema("app")  is True
    assert schema_registry.is_framework_schema("core")  is True


def test_is_framework_schema_false_for_user_domains(schema_registry):
    """Test that user domains are not considered framework schemas"""
    assert not schema_registry.is_framework_schema("crm")
    assert not schema_registry.is_framework_schema("catalog")
    assert not schema_registry.is_framework_schema("projects")


def test_is_shared_reference_schema_true_for_framework_schemas(schema_registry):
    """Test that framework schemas are shared reference schemas"""
    assert schema_registry.is_shared_reference_schema("common")  is True
    assert schema_registry.is_shared_reference_schema("app")  is True


def test_is_shared_reference_schema_true_for_non_multi_tenant_domains(schema_registry):
    """Test that non-multi-tenant domains are shared reference schemas"""
    assert schema_registry.is_shared_reference_schema("catalog")  is True


def test_is_shared_reference_schema_false_for_multi_tenant_domains(schema_registry):
    """Test that multi-tenant domains are not shared reference schemas"""
    assert not schema_registry.is_shared_reference_schema("crm")
    assert not schema_registry.is_shared_reference_schema("projects")
    assert not schema_registry.is_shared_reference_schema("management")  # alias


def test_is_shared_reference_schema_false_for_unknown_schemas(schema_registry):
    """Test that unknown schemas default to not shared (safe default)"""
    assert not schema_registry.is_shared_reference_schema("unknown")


def test_get_domain_by_name_or_alias_delegates_to_registry(schema_registry, mock_domain_registry):
    """Test that get_domain_by_name_or_alias delegates to domain registry"""
    result = schema_registry.get_domain_by_name_or_alias("crm")
    assert result is not None
    assert result.domain_name == "crm"

    mock_domain_registry.get_domain.assert_called_with("crm")
