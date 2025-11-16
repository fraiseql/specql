"""Tests for SubdomainNumber value object"""

import pytest
from src.domain.value_objects import SubdomainNumber


class TestSubdomainNumber:
    """Test SubdomainNumber value object"""

    def test_valid_subdomain_numbers(self):
        """Test valid subdomain number formats"""
        # 3-digit hex format (012)
        sn1 = SubdomainNumber("012")
        assert str(sn1) == "012"
        assert sn1.value == "012"
        assert sn1.domain_part == "01"
        assert sn1.subdomain_part == "2"

        # With domain separator
        sn2 = SubdomainNumber("01:2")
        assert str(sn2) == "012"
        assert sn2.domain_part == "01"

        # With leading zeros
        sn3 = SubdomainNumber("001")
        assert str(sn3) == "001"

        # Hex digits
        sn4 = SubdomainNumber("0A5")
        assert str(sn4) == "0A5"
        assert sn4.domain_part == "0A"
        assert sn4.subdomain_part == "5"

        # Uppercase conversion
        sn5 = SubdomainNumber("0a5")
        assert str(sn5) == "0A5"

    def test_invalid_subdomain_numbers(self):
        """Test invalid subdomain number formats"""
        # Too short
        with pytest.raises(ValueError, match="must be 3 hex digits"):
            SubdomainNumber("01")

        # Too long
        with pytest.raises(ValueError, match="must be 3 hex digits"):
            SubdomainNumber("0123")

        # Invalid hex character
        with pytest.raises(ValueError, match="must contain only hex digits"):
            SubdomainNumber("01G")

        # Empty
        with pytest.raises(ValueError, match="cannot be empty"):
            SubdomainNumber("")

    def test_subdomain_number_equality(self):
        """Test value object equality"""
        sn1 = SubdomainNumber("012")
        sn2 = SubdomainNumber("012")
        sn3 = SubdomainNumber("013")

        assert sn1 == sn2
        assert sn1 != sn3
        assert hash(sn1) == hash(sn2)

    def test_parent_domain_number(self):
        """Test extracting parent domain number"""
        sn = SubdomainNumber("012")
        domain_num = sn.get_parent_domain_number()

        from src.domain.value_objects import DomainNumber

        assert isinstance(domain_num, DomainNumber)
        assert str(domain_num) == "01"

    def test_subdomain_sequence(self):
        """Test subdomain sequence number"""
        sn = SubdomainNumber("012")
        assert sn.subdomain_sequence == 2

        sn2 = SubdomainNumber("019")
        assert sn2.subdomain_sequence == 9

    def test_formatting(self):
        """Test different formatting options"""
        sn = SubdomainNumber("012")

        # Default format (012)
        assert str(sn) == "012"

        # With separator (01:2)
        assert sn.format_with_separator() == "01:2"

        # Full format with domain (Domain 01, Subdomain 2)
        assert sn.format_full() == "Domain 01, Subdomain 2"
