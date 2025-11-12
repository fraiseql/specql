"""
Tests for NumberingParser
"""

import pytest

from src.numbering.numbering_parser import NumberingParser


def test_parse_table_code_6_digit():
    """Test parsing 6-digit table code into components"""
    parser = NumberingParser()
    result = parser.parse_table_code("013211")

    assert result == {
        "schema_layer": "01",  # write_side
        "domain_code": "3",  # catalog
        "subdomain_code": "2",  # manufacturer subdomain (single digit)
        "entity_sequence": "1",  # manufacturer entity sequence
        "file_sequence": "1",  # first file
        "full_domain": "013",  # schema_layer + domain (3 digits)
        "full_group": "0132",  # + subdomain (4 digits: SS+D+S)
        "full_entity": "01321",  # + entity_sequence (5 digits: SS+D+S+E)
    }


def test_parse_invalid_code():
    """Test error handling for invalid codes"""
    parser = NumberingParser()

    with pytest.raises(ValueError, match="Invalid table_code"):
        parser.parse_table_code("12345")  # 5 digits - wrong length

    with pytest.raises(ValueError, match="Invalid table_code"):
        parser.parse_table_code("GGGGGG")  # Invalid hex (G is not valid hex)

    with pytest.raises(ValueError, match="Invalid table_code"):
        parser.parse_table_code("12-456")  # Contains invalid character


def test_generate_directory_path():
    """Test directory path generation from table code"""
    parser = NumberingParser()
    path = parser.generate_directory_path("013211", "manufacturer")

    expected = "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer"
    assert path == expected


def test_generate_file_path():
    """Test file path generation"""
    parser = NumberingParser()
    path = parser.generate_file_path(
        table_code="013211", entity_name="manufacturer", file_type="table"
    )

    expected = (
        "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql"
    )
    assert path == expected


def test_parse_table_code_subdomain_single_digit():
    """Subdomain should be SINGLE digit (position 3)"""
    parser = NumberingParser()

    # Test case from PrintOptim: ColorMode entity
    components = parser.parse_table_code_detailed("013111")

    assert components.schema_layer == "01"
    assert components.domain_code == "3"
    assert components.subdomain_code == "1"  # ← SINGLE DIGIT
    assert components.entity_sequence == "1"
    assert components.file_sequence == "1"


def test_parse_table_code_manufacturer_subdomain():
    """Manufacturer subdomain (code 2) should parse correctly"""
    parser = NumberingParser()

    components = parser.parse_table_code_detailed("013211")

    assert components.subdomain_code == "2"  # ← SINGLE DIGIT
    assert components.entity_sequence == "1"


def test_correct_field_names():
    """New field names work correctly"""
    parser = NumberingParser()
    components = parser.parse_table_code_detailed("013111")

    # New field names
    assert components.subdomain_code == "1"
    assert components.entity_sequence == "1"


def test_correct_field_names_manufacturer():
    """New field names work for manufacturer subdomain"""
    parser = NumberingParser()
    components = parser.parse_table_code_detailed("013121")

    # New field names
    assert components.subdomain_code == "1"
    assert components.entity_sequence == "2"
