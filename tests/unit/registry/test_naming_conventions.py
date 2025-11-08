"""
Tests for NamingConventions class

Tests table code derivation, validation, entity code generation,
and file path generation.
"""

import pytest
from pathlib import Path

from src.generators.schema.naming_conventions import NamingConventions
from src.core.ast_models import Entity, Organization, FieldDefinition


class TestEntityCodeDerivation:
    """Test entity code generation from entity names"""

    @pytest.fixture
    def nc(self):
        return NamingConventions("registry/domain_registry.yaml")

    def test_derive_entity_code_contact(self, nc):
        """Should derive 3-char code from Contact"""
        code = nc.derive_entity_code("Contact")
        # Algorithm: C (first) + N (first consonant) + T (second consonant) = CNT
        assert code == "CNT"
        assert len(code) == 3

    def test_derive_entity_code_manufacturer(self, nc):
        """Should derive MNF from Manufacturer"""
        code = nc.derive_entity_code("Manufacturer")
        assert code == "MNF"

    def test_derive_entity_code_task(self, nc):
        """Should derive TSK from Task"""
        code = nc.derive_entity_code("Task")
        assert code == "TSK"

    def test_derive_entity_code_company(self, nc):
        """Should derive CMP from Company"""
        code = nc.derive_entity_code("Company")
        assert code == "CMP"

    def test_derive_entity_code_user(self, nc):
        """Should derive USR from User"""
        code = nc.derive_entity_code("User")
        assert code == "USR"

    def test_derive_entity_code_short_name(self, nc):
        """Should handle short entity names"""
        code = nc.derive_entity_code("Tag")
        # T (first) + G (consonant) + A (vowel) = TGA
        assert code == "TGA"
        assert len(code) == 3

    def test_derive_entity_code_single_letter(self, nc):
        """Should handle single-letter names by padding"""
        code = nc.derive_entity_code("A")
        # For single letter, just return the letter (tests edge case)
        # In practice, entities should have longer names
        assert len(code) >= 1


class TestTableCodeValidation:
    """Test table code validation"""

    @pytest.fixture
    def nc(self):
        return NamingConventions("registry/domain_registry.yaml")

    def test_validate_valid_code(self, nc):
        """Should accept valid table code"""
        entity = Entity(name="Contact", schema="crm", fields={})

        # Should not raise
        nc.validate_table_code("012311", entity)

    def test_validate_invalid_format_too_short(self, nc):
        """Should reject codes that are too short"""
        entity = Entity(name="Contact", schema="crm", fields={})

        with pytest.raises(ValueError, match="hexadecimal"):
            nc.validate_table_code("123", entity)

    def test_validate_invalid_format_too_long(self, nc):
        """Should reject codes that are too long"""
        entity = Entity(name="Contact", schema="crm", fields={})

        with pytest.raises(ValueError, match="hexadecimal"):
            nc.validate_table_code("1234567", entity)

    def test_validate_hex_codes(self, nc):
        """Should accept valid hexadecimal codes"""
        entity = Entity(name="Contact", schema="crm", fields={})

        # Valid hex codes (uppercase and lowercase)
        nc.validate_table_code("012A3F", entity)  # Uppercase
        nc.validate_table_code("012a3f", entity)  # Lowercase (normalized)
        nc.validate_table_code("012AbC", entity)  # Mixed case

    def test_validate_invalid_format_not_hex(self, nc):
        """Should reject codes with invalid hex characters"""
        entity = Entity(name="Contact", schema="crm", fields={})

        with pytest.raises(ValueError, match="hexadecimal"):
            nc.validate_table_code("12G456", entity)  # G is not valid hex

        with pytest.raises(ValueError, match="hexadecimal"):
            nc.validate_table_code("12-456", entity)  # - is not valid

    def test_validate_invalid_schema_layer(self, nc):
        """Should reject invalid schema layer"""
        entity = Entity(name="Contact", schema="crm", fields={})

        with pytest.raises(ValueError, match="Invalid schema layer"):
            nc.validate_table_code("991111", entity)

    def test_validate_invalid_domain_code(self, nc):
        """Should reject invalid domain code"""
        entity = Entity(name="Contact", schema="crm", fields={})

        with pytest.raises(ValueError, match="Invalid domain code"):
            nc.validate_table_code("019111", entity)

    def test_validate_domain_mismatch(self, nc):
        """Should reject code that doesn't match entity schema"""
        entity = Entity(name="Contact", schema="crm", fields={})

        # Code 013111 is catalog domain, but entity is crm
        with pytest.raises(ValueError, match="doesn't match"):
            nc.validate_table_code("013111", entity)

    def test_validate_duplicate_code(self, nc):
        """Should reject already-assigned codes"""
        entity = Entity(name="Contact", schema="catalog", fields={})

        # 013211 is already assigned to Manufacturer
        with pytest.raises(ValueError, match="already assigned"):
            nc.validate_table_code("013211", entity)

    def test_validate_allows_own_code(self, nc):
        """Should allow entity to keep its own code"""
        entity = Entity(name="Manufacturer", schema="catalog", fields={})

        # Manufacturer already has 013211 - should be allowed
        nc.validate_table_code("013211", entity)


class TestTableCodeDerivation:
    """Test automatic table code derivation"""

    @pytest.fixture
    def nc(self):
        return NamingConventions("registry/domain_registry.yaml")

    def test_derive_table_code_crm_contact(self, nc):
        """Should derive code for CRM Contact entity"""
        entity = Entity(name="Contact", schema="crm", fields={})

        code = nc.derive_table_code(entity)

        # Should be: 01 (write_side) + 2 (crm) + 03 (customer subdomain) + N1
        assert code.startswith("0120")  # 01 + 2 + 0X
        assert len(code) == 6

    def test_derive_table_code_catalog_product(self, nc):
        """Should derive code for Catalog Product entity"""
        entity = Entity(name="Product", schema="catalog", fields={})

        code = nc.derive_table_code(entity)

        # Should be: 01 (write_side) + 3 (catalog) + 03 (product subdomain) + N1
        assert code.startswith("0130")
        assert len(code) == 6

    def test_derive_table_code_unknown_domain(self, nc):
        """Should raise error for unknown domain"""
        entity = Entity(name="Test", schema="unknown_domain", fields={})

        with pytest.raises(ValueError, match="Unknown domain"):
            nc.derive_table_code(entity)

    def test_derive_table_code_with_schema_layer(self, nc):
        """Should use specified schema layer"""
        entity = Entity(name="ContactView", schema="crm", fields={})

        code = nc.derive_table_code(entity, schema_layer="02")  # read_side

        assert code.startswith("02")  # read_side layer

    def test_derive_table_code_infers_subdomain(self, nc):
        """Should infer subdomain from entity name"""
        # Entity with "contact" in name should go to customer subdomain
        entity = Entity(name="Contact", schema="crm", fields={})

        code = nc.derive_table_code(entity)

        # Customer subdomain is 03 in crm
        assert code[2:4] == "20"  # domain 2, starts with subdomain


class TestSubdomainInference:
    """Test subdomain inference logic"""

    @pytest.fixture
    def nc(self):
        return NamingConventions("registry/domain_registry.yaml")

    def test_infer_customer_subdomain_contact(self, nc):
        """Should infer customer subdomain for Contact"""
        entity = Entity(name="Contact", schema="crm", fields={})
        domain_info = nc.registry.get_domain("crm")

        subdomain = nc._infer_subdomain(entity, domain_info)

        assert subdomain == "customer"

    def test_infer_customer_subdomain_company(self, nc):
        """Should infer customer subdomain for Company"""
        entity = Entity(name="Company", schema="crm", fields={})
        domain_info = nc.registry.get_domain("crm")

        subdomain = nc._infer_subdomain(entity, domain_info)

        assert subdomain == "customer"

    def test_infer_sales_subdomain_opportunity(self, nc):
        """Should infer sales subdomain for Opportunity"""
        entity = Entity(name="Opportunity", schema="crm", fields={})
        domain_info = nc.registry.get_domain("crm")

        subdomain = nc._infer_subdomain(entity, domain_info)

        assert subdomain == "sales"

    def test_infer_manufacturer_subdomain(self, nc):
        """Should infer manufacturer subdomain for Manufacturer"""
        entity = Entity(name="Manufacturer", schema="catalog", fields={})
        domain_info = nc.registry.get_domain("catalog")

        subdomain = nc._infer_subdomain(entity, domain_info)

        assert subdomain == "manufacturer"

    def test_infer_product_subdomain(self, nc):
        """Should infer product subdomain for Product"""
        entity = Entity(name="Product", schema="catalog", fields={})
        domain_info = nc.registry.get_domain("catalog")

        subdomain = nc._infer_subdomain(entity, domain_info)

        assert subdomain == "product"

    def test_infer_defaults_to_core(self, nc):
        """Should default to core subdomain if no match"""
        entity = Entity(name="UnknownEntity", schema="crm", fields={})
        domain_info = nc.registry.get_domain("crm")

        subdomain = nc._infer_subdomain(entity, domain_info)

        assert subdomain == "core"


class TestFilePathGeneration:
    """Test hierarchical file path generation"""

    @pytest.fixture
    def nc(self):
        return NamingConventions("registry/domain_registry.yaml")

    def test_generate_file_path_table(self, nc):
        """Should generate path for table SQL file"""
        entity = Entity(name="Contact", schema="crm", fields={})

        path = nc.generate_file_path(entity, "012311", "table")

        assert "generated/migrations" in path
        assert "01_write_side" in path
        assert "012_crm" in path
        assert "012311_tb_contact.sql" in path

    def test_generate_file_path_function(self, nc):
        """Should generate path for function SQL file"""
        entity = Entity(name="Contact", schema="crm", fields={})

        path = nc.generate_file_path(entity, "012311", "function")

        assert "012311_fn_contact.sql" in path

    def test_generate_file_path_test(self, nc):
        """Should generate path for test file"""
        entity = Entity(name="Contact", schema="crm", fields={})

        path = nc.generate_file_path(entity, "012311", "test")

        assert "012311_test_contact.sql" in path

    def test_generate_file_path_custom_base(self, nc):
        """Should use custom base directory"""
        entity = Entity(name="Contact", schema="crm", fields={})

        path = nc.generate_file_path(
            entity,
            "012311",
            "table",
            base_dir="custom/output"
        )

        assert path.startswith("custom/output")


class TestGetTableCode:
    """Test get_table_code (main entry point)"""

    @pytest.fixture
    def nc(self):
        return NamingConventions("registry/domain_registry.yaml")

    def test_get_table_code_manual(self, nc):
        """Should use manual table code if provided"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={},
            organization=Organization(table_code="012399", domain_name="crm")
        )

        code = nc.get_table_code(entity)

        assert code == "012399"

    def test_get_table_code_from_registry(self, nc):
        """Should use registry code if entity registered"""
        entity = Entity(name="Manufacturer", schema="catalog", fields={})

        code = nc.get_table_code(entity)

        # Manufacturer is already in registry with 013211
        assert code == "013211"

    def test_get_table_code_auto_derive(self, nc):
        """Should auto-derive if not manual and not in registry"""
        entity = Entity(name="NewEntity", schema="crm", fields={})

        code = nc.get_table_code(entity)

        # Should be auto-derived
        assert len(code) == 6
        assert code.startswith("012")  # crm domain


class TestCodeDerivation:
    """Test code derivation for functions and views"""

    @pytest.fixture
    def nc(self):
        return NamingConventions("registry/domain_registry.yaml")

    def test_derive_function_code_from_table(self, nc):
        """Should derive function code by changing layer to 03"""
        table_code = "012031"  # write_side table
        function_code = nc.derive_function_code(table_code)

        assert function_code == "032031"
        assert function_code[:2] == "03"  # functions layer
        assert function_code[2:] == table_code[2:]  # same domain/subdomain/entity

    def test_derive_view_code_from_table(self, nc):
        """Should derive view code by changing layer to 02"""
        table_code = "012031"  # write_side table
        view_code = nc.derive_view_code(table_code)

        assert view_code == "022031"
        assert view_code[:2] == "02"  # read_side layer
        assert view_code[2:] == table_code[2:]  # same domain/subdomain/entity

    def test_derive_function_code_invalid_format(self, nc):
        """Should reject invalid table codes"""
        with pytest.raises(ValueError, match="Invalid table code format"):
            nc.derive_function_code("123")  # Too short

        with pytest.raises(ValueError, match="Invalid table code format"):
            nc.derive_function_code("1234567")  # Too long

    def test_derive_view_code_invalid_format(self, nc):
        """Should reject invalid table codes"""
        with pytest.raises(ValueError, match="Invalid table code format"):
            nc.derive_view_code("123")  # Too short


class TestEntityQueries:
    """Test entity query methods"""

    @pytest.fixture
    def nc(self, tmp_path):
        """Create temporary registry with test data"""
        import shutil
        temp_registry = tmp_path / "test_registry.yaml"
        shutil.copy("registry/domain_registry.yaml", temp_registry)

        nc = NamingConventions(str(temp_registry))

        # Register a test entity
        nc.registry.register_entity(
            entity_name="TestContact",
            table_code="012311",
            entity_code="CON",
            domain_code="2",
            subdomain_code="03"
        )

        return nc

    def test_get_all_entities(self, nc):
        """Should get all registered entities"""
        entities = nc.get_all_entities()

        assert len(entities) >= 2  # Manufacturer + TestContact
        entity_names = [e.entity_name for e in entities]
        assert "Manufacturer" in entity_names
        assert "TestContact" in entity_names

    def test_get_entities_by_domain(self, nc):
        """Should get entities filtered by domain"""
        crm_entities = nc.get_entities_by_domain("crm")

        assert len(crm_entities) >= 1
        for entity in crm_entities:
            assert entity.domain == "crm"

    def test_get_entities_by_subdomain(self, nc):
        """Should get entities filtered by subdomain"""
        customer_entities = nc.get_entities_by_subdomain("crm", "customer")

        assert len(customer_entities) >= 1
        for entity in customer_entities:
            assert entity.domain == "crm"
            assert entity.subdomain == "customer"
