"""Unit tests for domain value objects"""

import pytest
from src.domain.value_objects import DomainNumber, TableCode


class TestDomainNumber:
    """Test DomainNumber value object"""

    def test_valid_domain_numbers(self):
        """Test valid domain numbers 1-9"""
        for num in range(1, 10):
            domain_num = DomainNumber(str(num))
            assert str(domain_num) == str(num)

    def test_invalid_domain_numbers(self):
        """Test invalid domain numbers"""
        invalid_values = ["0", "10", "a", "1.5", ""]
        for value in invalid_values:
            with pytest.raises(ValueError):
                DomainNumber(value)

    def test_immutable(self):
        """Test that DomainNumber is immutable"""
        domain_num = DomainNumber("5")
        with pytest.raises(AttributeError):
            domain_num.value = "6"


class TestTableCode:
    """Test TableCode value object"""

    def test_valid_table_codes(self):
        """Test valid 6-digit table codes"""
        valid_codes = ["012345", "999999", "000000"]
        for code in valid_codes:
            table_code = TableCode(code)
            assert str(table_code) == code

    def test_invalid_table_codes(self):
        """Test invalid table codes"""
        invalid_codes = ["12345", "1234567", "abc123", "12.345", ""]
        for code in invalid_codes:
            with pytest.raises(ValueError):
                TableCode(code)

    def test_generate_table_code(self):
        """Test table code generation"""
        code = TableCode.generate("1", "23", 4)
        assert str(code) == "123040"  # domain 1, subdomain 23, entity 4, file 0

    def test_immutable(self):
        """Test that TableCode is immutable"""
        table_code = TableCode("012345")
        with pytest.raises(AttributeError):
            table_code.value = "012346"
