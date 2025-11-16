"""
Tests for DomainRegistry class

Tests registry loading, entity lookup, and management functions.
"""

from pathlib import Path

import pytest
import yaml

from src.generators.schema.naming_conventions import DomainRegistry


class TestDomainRegistryLoading:
    """Test registry loading and initialization"""

    def test_registry_file_exists(self):
        """Domain registry YAML should exist"""
        registry_path = Path("registry/domain_registry.yaml")
        assert registry_path.exists(), "registry/domain_registry.yaml not found"

    def test_load_registry(self):
        """Should load registry from YAML"""
        registry = DomainRegistry("registry/domain_registry.yaml")

        assert registry.registry is not None
        assert "version" in registry.registry
        assert "domains" in registry.registry
        assert "schema_layers" in registry.registry

    def test_registry_has_version(self):
        """Registry should have version field"""
        with open("registry/domain_registry.yaml") as f:
            data = yaml.safe_load(f)

        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_registry_has_schema_layers(self):
        """Registry should define schema layers"""
        with open("registry/domain_registry.yaml") as f:
            data = yaml.safe_load(f)

        assert "schema_layers" in data
        assert "01" in data["schema_layers"]
        assert data["schema_layers"]["01"] == "write_side"
        assert "02" in data["schema_layers"]
        assert data["schema_layers"]["02"] == "read_side"

    def test_registry_has_domains(self):
        """Registry should define domains"""
        with open("registry/domain_registry.yaml") as f:
            data = yaml.safe_load(f)

        assert "domains" in data
        assert "1" in data["domains"]  # core
        assert "2" in data["domains"]  # crm
        assert "3" in data["domains"]  # catalog
        assert "4" in data["domains"]  # projects

    def test_crm_domain_has_subdomains(self):
        """CRM domain should have subdomains"""
        with open("registry/domain_registry.yaml") as f:
            data = yaml.safe_load(f)

        crm = data["domains"]["2"]
        assert crm["name"] == "crm"
        assert "subdomains" in crm
        assert "03" in crm["subdomains"]  # customer subdomain
        assert crm["subdomains"]["03"]["name"] == "customer"


class TestDomainRegistryQueries:
    """Test registry query methods"""

    @pytest.fixture
    def registry(self):
        return DomainRegistry("registry/domain_registry.yaml")

    def test_get_entity_not_found(self, registry):
        """Should return None for unregistered entity"""
        entity = registry.get_entity("NonExistentEntity")
        assert entity is None

    def test_get_entity_manufacturer(self, registry):
        """Should get manufacturer entity from registry"""
        entity = registry.get_entity("Manufacturer")

        assert entity is not None
        assert entity.entity_name == "Manufacturer"
        assert entity.table_code == "013029"  # Actual code from registry
        assert entity.entity_code == "MNF"
        assert entity.domain == "catalog"
        assert entity.subdomain == "manufacturer"

    def test_get_domain_by_code(self, registry):
        """Should get domain by code"""
        domain = registry.get_domain("2")

        assert domain is not None
        assert domain.domain_name == "crm"
        assert domain.domain_code == "2"
        assert domain.description is not None

    def test_get_domain_by_name(self, registry):
        """Should get domain by name"""
        domain = registry.get_domain("crm")

        assert domain is not None
        assert domain.domain_code == "2"
        assert domain.domain_name == "crm"

    def test_get_domain_by_alias(self, registry):
        """Should get domain by alias"""
        domain = registry.get_domain("management")  # alias for crm

        assert domain is not None
        assert domain.domain_name == "crm"
        assert domain.domain_code == "2"
        assert "management" in domain.aliases

    def test_get_domain_not_found(self, registry):
        """Should return None for unknown domain"""
        domain = registry.get_domain("unknown_domain")
        assert domain is None

    def test_get_subdomain_by_code(self, registry):
        """Should get subdomain by code"""
        subdomain = registry.get_subdomain("2", "03")

        assert subdomain is not None
        assert subdomain.subdomain_name == "customer"
        assert subdomain.subdomain_code == "03"

    def test_get_subdomain_by_name(self, registry):
        """Should get subdomain by name"""
        subdomain = registry.get_subdomain("2", "customer")

        assert subdomain is not None
        assert subdomain.subdomain_code == "03"
        assert subdomain.subdomain_name == "customer"

    def test_is_code_available_reserved(self, registry):
        """Should check reserved codes"""
        assert not registry.is_code_available("000000")
        assert not registry.is_code_available("999999")

    def test_is_code_available_assigned(self, registry):
        """Should check assigned codes"""
        # Manufacturer has 013029 (from actual registry)
        assert not registry.is_code_available("013029")

    def test_is_code_available_unassigned(self, registry):
        """Should return true for unassigned codes"""
        assert registry.is_code_available("012399")
        assert registry.is_code_available("014999")


class TestDomainRegistryModification:
    """Test registry modification methods"""

    @pytest.fixture
    def registry(self, tmp_path):
        """Create temporary registry for testing modifications"""
        # Copy main registry to temp location
        import shutil

        temp_registry = tmp_path / "test_registry.yaml"
        shutil.copy("registry/domain_registry.yaml", temp_registry)
        return DomainRegistry(str(temp_registry))

    def test_register_entity(self, registry):
        """Should register new entity"""
        # Before: entity doesn't exist
        assert registry.get_entity("TestContact") is None

        # Register
        registry.register_entity(
            entity_name="TestContact",
            table_code="012311",
            entity_code="CON",
            domain_code="2",
            subdomain_code="03",
        )

        # After: entity exists
        entity = registry.get_entity("TestContact")
        assert entity is not None
        assert entity.table_code == "012311"
        assert entity.entity_code == "CON"

    def test_register_entity_increments_sequence(self, registry):
        """Should increment next_entity_sequence after registration"""
        # Get initial sequence
        initial_seq = registry.get_next_entity_sequence("2", "03")

        # Register entity
        registry.register_entity(
            entity_name="TestContact2",
            table_code="012321",
            entity_code="CON",
            domain_code="2",
            subdomain_code="03",
        )

        # Sequence should have incremented
        new_seq = registry.get_next_entity_sequence("2", "03")
        assert new_seq == initial_seq + 1

    def test_register_entity_invalid_domain(self, registry):
        """Should raise error for invalid domain"""
        with pytest.raises(ValueError, match="Domain.*not found"):
            registry.register_entity(
                entity_name="Test",
                table_code="099999",
                entity_code="TST",
                domain_code="9",  # Invalid
                subdomain_code="01",
            )

    def test_register_entity_invalid_subdomain(self, registry):
        """Should raise error for invalid subdomain"""
        with pytest.raises(ValueError, match="Subdomain.*not found"):
            registry.register_entity(
                entity_name="Test",
                table_code="012981",
                entity_code="TST",
                domain_code="2",
                subdomain_code="98",  # Invalid
            )

    def test_assign_function_code(self, registry):
        """Should assign function codes with sequence tracking"""
        # First register a test entity
        registry.register_entity(
            entity_name="TestContact",
            table_code="0123611",  # 7-digit code
            entity_code="CON",
            domain_code="2",
            subdomain_code="03",
        )

        # Assign first function
        func1_code = registry.assign_function_code(
            "crm", "customer", "TestContact", "create_contact"
        )
        assert func1_code == "0323611"

        # Assign second function
        func2_code = registry.assign_function_code(
            "crm", "customer", "TestContact", "update_contact"
        )
        assert func2_code == "0323612"

        # Assign third function
        func3_code = registry.assign_function_code(
            "crm", "customer", "TestContact", "delete_contact"
        )
        assert func3_code == "0323613"

    def test_assign_function_code_unregistered_entity(self, registry):
        """Should raise error for unregistered entity"""
        with pytest.raises(ValueError, match="Entity.*not registered"):
            registry.assign_function_code(
                "crm", "customer", "NonExistentEntity", "create"
            )

    def test_assign_function_code_invalid_domain(self, registry):
        """Should raise error for invalid domain"""
        # First register a test entity
        registry.register_entity(
            entity_name="TestContact",
            table_code="0123611",
            entity_code="CON",
            domain_code="2",
            subdomain_code="03",
        )

        with pytest.raises(ValueError, match="Domain.*not found"):
            registry.assign_function_code(
                "invalid", "customer", "TestContact", "create"
            )


class TestDomainRegistryMappings:
    """Test domain and subdomain mapping methods"""

    def test_load_domain_mapping(self, registry):
        """Should load domain mapping with codes, names, and aliases"""
        mapping = registry.load_domain_mapping()

        # Should have mappings by code
        assert "2" in mapping
        assert mapping["2"]["name"] == "crm"
        assert mapping["2"]["code"] == "2"
        assert (
            mapping["2"]["description"]
            == "Customer relationship management & organizational structure"
        )
        assert mapping["2"]["multi_tenant"] is True

        # Should have mappings by name
        assert "crm" in mapping
        assert mapping["crm"] == mapping["2"]

        # Should have mappings by alias
        assert "management" in mapping
        assert mapping["management"] == mapping["2"]

    def test_load_domain_mapping_caching(self, registry):
        """Should cache domain mapping results"""
        # First call
        mapping1 = registry.load_domain_mapping()

        # Second call should return cached result
        mapping2 = registry.load_domain_mapping()

        assert mapping1 is mapping2

        # Reload registry should clear cache
        registry.load()
        mapping3 = registry.load_domain_mapping()

        assert mapping1 is not mapping3

    def test_load_subdomain_mapping(self, registry):
        """Should load subdomain mapping for a domain"""
        mapping = registry.load_subdomain_mapping("crm")

        # Should have mappings by code
        assert "03" in mapping
        assert mapping["03"]["name"] == "customer"
        assert mapping["03"]["code"] == "03"
        assert (
            mapping["03"]["description"]
            == "Customer contact entities (contact, company, account)"
        )
        assert "next_entity_sequence" in mapping["03"]
        assert "next_read_entity" in mapping["03"]

        # Should have mappings by name
        assert "customer" in mapping
        assert mapping["customer"] == mapping["03"]

    def test_load_subdomain_mapping_by_alias(self, registry):
        """Should load subdomain mapping using domain alias"""
        mapping1 = registry.load_subdomain_mapping("crm")
        mapping2 = registry.load_subdomain_mapping("management")  # alias

        assert mapping1 == mapping2

    def test_load_subdomain_mapping_invalid_domain(self, registry):
        """Should return empty dict for invalid domain"""
        mapping = registry.load_subdomain_mapping("invalid_domain")

        assert mapping == {}

    def test_load_subdomain_mapping_caching(self, registry):
        """Should cache subdomain mapping results"""
        # First call
        mapping1 = registry.load_subdomain_mapping("crm")

        # Second call should return cached result
        mapping2 = registry.load_subdomain_mapping("crm")

        assert mapping1 is mapping2

        # Reload registry should clear cache
        registry.load()
        mapping3 = registry.load_subdomain_mapping("crm")

        assert mapping1 is not mapping3
