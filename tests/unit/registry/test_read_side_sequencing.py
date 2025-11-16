"""
Tests for read-side entity sequencing in DomainRegistry

Tests independent read-side entity code assignment separate from write-side.
"""

import pytest

from src.generators.schema.naming_conventions import DomainRegistry


class TestIndependentReadEntityAssignment:
    """Test independent read-side entity code assignment"""

    def test_independent_read_entity_assignment(self):
        """Should assign read-side entity codes independently from write-side"""
        registry = DomainRegistry()

        # Write-side has entity 36
        registry.assign_write_entity_code("crm", "customer", "Contact")
        # Returns: 0120361

        # Read-side should start fresh
        code1 = registry.assign_read_entity_code("crm", "customer", "tv_contact")
        code2 = registry.assign_read_entity_code("crm", "customer", "v_contact_summary")

        # Should be sequential on read-side, NOT related to write-side
        assert code1 == "0220310"  # Entity 1 (independent from write-side!)
        assert code2 == "0220320"  # Entity 2

    def test_read_entity_sequence_per_subdomain(self):
        """Should track read entity sequences per subdomain"""
        registry = DomainRegistry()

        # Different subdomains have independent sequences
        crm_code = registry.assign_read_entity_code("crm", "customer", "tv_contact")
        catalog_code = registry.assign_read_entity_code(
            "catalog", "manufacturer", "tv_product"
        )

        # Both can be entity 1 in their respective subdomains
        assert crm_code.endswith("10")  # Entity 1, file 0
        assert catalog_code.endswith("10")  # Entity 1, file 0

    def test_file_sequence_within_entity(self):
        """Should track file sequences within same read entity"""
        registry = DomainRegistry()

        # First file for tv_contact entity
        code1 = registry.assign_read_file_code(
            "crm", "customer", "tv_contact", file_num=0
        )
        assert code1 == "0220310"  # Entity 1, file 0

        # Additional view file for same logical entity
        code2 = registry.assign_read_file_code(
            "crm", "customer", "tv_contact", file_num=1
        )
        assert code2 == "0220311"  # Entity 1, file 1


class TestReadSideRegistryPersistence:
    """Test read-side entity persistence in registry"""

    def test_read_entity_persisted_to_registry(self, tmp_path):
        """Should persist read-side entity assignments to registry YAML"""
        # Create temporary registry
        temp_registry = tmp_path / "test_registry.yaml"
        import shutil

        shutil.copy("registry/domain_registry.yaml", temp_registry)

        registry = DomainRegistry(str(temp_registry))

        # Assign read-side code
        code = registry.assign_read_entity_code("crm", "customer", "tv_contact")

        # Should be persisted
        registry.save()

        # Reload and verify
        registry2 = DomainRegistry(str(temp_registry))
        contact_entry = registry2.get_read_entity("crm", "customer", "tv_contact")
        assert contact_entry is not None
        assert contact_entry.code == code

    def test_read_entity_registry_structure(self, tmp_path):
        """Should create proper read-side registry structure"""
        temp_registry = tmp_path / "test_registry.yaml"
        import shutil

        shutil.copy("registry/domain_registry.yaml", temp_registry)

        registry = DomainRegistry(str(temp_registry))

        # Assign read-side code
        registry.assign_read_entity_code("crm", "customer", "tv_contact")

        # Check registry structure
        crm_domain = registry.registry["domains"]["2"]
        customer_subdomain = crm_domain["subdomains"]["03"]

        assert "read_entities" in customer_subdomain
        assert "tv_contact" in customer_subdomain["read_entities"]
        assert "next_read_entity" in customer_subdomain

        entity_data = customer_subdomain["read_entities"]["tv_contact"]
        assert "entity_number" in entity_data
        assert "files" in entity_data


class TestReadSideCodeValidation:
    """Test read-side code validation and conflicts"""

    def test_read_code_format_validation(self):
        """Should validate read-side code format"""
        registry = DomainRegistry()

        # Valid format
        assert registry.validate_read_code_format("0220310")

        # Invalid formats
        assert not registry.validate_read_code_format("0120310")  # Wrong layer
        assert not registry.validate_read_code_format("022031")  # Too short
        assert not registry.validate_read_code_format("02203100")  # Too long

    def test_read_code_conflict_detection(self, tmp_path):
        """Should detect conflicting read-side codes"""
        temp_registry = tmp_path / "test_registry.yaml"
        import shutil

        shutil.copy("registry/domain_registry.yaml", temp_registry)

        registry = DomainRegistry(str(temp_registry))

        # Assign first code
        code = registry.assign_read_entity_code("crm", "customer", "tv_contact")

        # Try to assign same code manually (should fail)
        with pytest.raises(ValueError, match="Code.*already assigned"):
            registry.force_assign_read_code(code, "crm", "customer", "tv_other")
