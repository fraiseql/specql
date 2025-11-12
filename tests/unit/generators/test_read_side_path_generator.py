"""
Tests for read-side path generation

Tests hierarchical path generation for read-side files.
"""

import pytest
from pathlib import Path

from src.generators.schema.read_side_path_generator import ReadSidePathGenerator
from src.generators.schema.code_parser import ReadSideCodeParser


class TestReadSidePathGeneration:
    """Test path generation from read-side codes"""

    def test_generate_tv_path_from_code(self):
        """Should generate path from read-side code"""
        # This test will fail until we implement ReadSidePathGenerator
        path_gen = ReadSidePathGenerator()

        # Given a read-side code
        code = "0220310"  # 02-2-03-1-0 (crm, customer, entity 1, file 0)
        view_name = "tv_contact"

        path = path_gen.generate_path(code, view_name)

        expected = Path("0_schema/02_query_side/022_crm/0223_customer/0220310_tv_contact.sql")
        assert path == expected

    def test_generate_path_with_different_domains(self):
        """Should generate paths for different domains"""
        path_gen = ReadSidePathGenerator()

        # Catalog domain
        code = "0230210"  # 0-2-3-02-1-0 (catalog, manufacturer, entity 1, file 0)
        view_name = "tv_product"

        path = path_gen.generate_path(code, view_name)

        expected = Path("0_schema/02_query_side/033_catalog/0332_manufacturer/0230210_tv_product.sql")
        assert path == expected

    def test_generate_path_with_file_sequences(self):
        """Should handle file sequences in paths"""
        path_gen = ReadSidePathGenerator()

        # Same entity, different file
        code1 = "0220310"  # tv_contact file 0
        code2 = "0220311"  # tv_contact file 1

        path1 = path_gen.generate_path(code1, "tv_contact")
        path2 = path_gen.generate_path(code2, "tv_contact")

        assert path1.name == "0220310_tv_contact.sql"
        assert path2.name == "0220311_tv_contact.sql"
        assert path1.parent == path2.parent  # Same directory


class TestReadSideCodeParsing:
    """Test parsing read-side codes into components"""

    def test_parse_read_side_code(self):
        """Should parse read-side code components"""
        parser = ReadSideCodeParser()

        components = parser.parse("0220310")
        assert components.schema_prefix == "0"
        assert components.layer == "2"
        assert components.domain == "2"
        assert components.subdomain == "03"
        assert components.entity == "1"
        assert components.file_num == "0"

    def test_parse_different_codes(self):
        """Should parse various code formats"""
        parser = ReadSideCodeParser()

        # Catalog manufacturer
        components = parser.parse("0230210")
        assert components.domain == "3"
        assert components.subdomain == "02"
        assert components.entity == "1"

        # Projects location
        components = parser.parse("0440210")
        assert components.domain == "4"
        assert components.subdomain == "02"
        assert components.entity == "1"

    def test_parse_invalid_code_length(self):
        """Should reject invalid code lengths"""
        parser = ReadSideCodeParser()

        with pytest.raises(ValueError, match="Invalid code length"):
            parser.parse("022031")  # Too short

        with pytest.raises(ValueError, match="Invalid code length"):
            parser.parse("02203100")  # Too long


class TestDomainSubdomainPathFormatting:
    """Test domain and subdomain path formatting"""

    def test_format_domain_path(self):
        """Should format domain paths correctly"""
        # This will test the domain path formatting: 0{domain}{subdomain_first_digit}_{domain_name}
        # For crm (domain 2), customer (subdomain 03): 022_crm
        path_gen = ReadSidePathGenerator()

        domain_path = path_gen.format_domain_path("2", "03", "crm")
        assert domain_path == "022_crm"

    def test_format_subdomain_path(self):
        """Should format subdomain paths correctly"""
        # This will test subdomain path formatting: 0{domain}{subdomain}_{subdomain_name}
        # For crm (domain 2), customer (subdomain 03): 0223_customer
        path_gen = ReadSidePathGenerator()

        subdomain_path = path_gen.format_subdomain_path("2", "03", "customer")
        assert subdomain_path == "0223_customer"

    def test_format_paths_different_domains(self):
        """Should format paths for different domains"""
        path_gen = ReadSidePathGenerator()

        # Catalog domain
        domain_path = path_gen.format_domain_path("3", "01", "catalog")
        assert domain_path == "033_catalog"

        subdomain_path = path_gen.format_subdomain_path("3", "01", "manufacturer")
        assert subdomain_path == "0331_manufacturer"


class TestPathIntegration:
    """Test complete path generation integration"""

    def test_full_path_structure(self):
        """Should create complete hierarchical path"""
        path_gen = ReadSidePathGenerator()
        parser = ReadSideCodeParser()

        code = "0220310"
        view_name = "tv_contact"

        # Parse code
        components = parser.parse(code)

        # Generate path
        path = path_gen.generate_path(code, view_name)

        # Verify structure
        assert path.is_absolute() == False  # Relative path
        assert str(path).startswith("0_schema/02_query_side/")
        assert "022_crm" in str(path)
        assert "0223_customer" in str(path)
        assert str(path).endswith("0220310_tv_contact.sql")

    def test_path_matches_reference_structure(self):
        """Should match the reference structure from the plan"""
        path_gen = ReadSidePathGenerator()

        # Reference example from plan:
        # 0_schema/02_query_side/022_crm/0223_customer/0220130_tv_contact.sql

        code = "0220310"  # 0-2-2-03-1-0 (crm, customer, entity 1, file 0)
        view_name = "tv_contact"

        path = path_gen.generate_path(code, view_name)

        expected_parts = [
            "0_schema",
            "02_query_side",
            "022_crm",
            "0223_customer",
            "0220310_tv_contact.sql"
        ]

        path_str = str(path)
        for part in expected_parts:
            assert part in path_str