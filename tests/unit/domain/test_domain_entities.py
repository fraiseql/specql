"""Unit tests for domain entities"""
import pytest
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber

class TestSubdomain:
    """Test Subdomain entity"""

    def test_allocate_next_code(self):
        """Test allocating entity codes"""
        subdomain = Subdomain(
            subdomain_number="01",
            subdomain_name="customer",
            description="Customer management",
            next_entity_sequence=1
        )

        # Allocate first code
        code1 = subdomain.allocate_next_code("Contact")
        assert str(code1) == "001010"  # domain 0, subdomain 01, entity 1, file 0
        assert subdomain.next_entity_sequence == 2

        # Allocate second code
        code2 = subdomain.allocate_next_code("Lead")
        assert str(code2) == "001020"  # domain 0, subdomain 01, entity 2, file 0
        assert subdomain.next_entity_sequence == 3

class TestDomain:
    """Test Domain aggregate root"""

    def test_create_domain(self):
        """Test creating a domain"""
        domain = Domain(
            domain_number=DomainNumber("2"),
            domain_name="crm",
            description="Customer Relationship Management",
            multi_tenant=True,
            aliases=["management", "sales"]
        )

        assert domain.domain_number.value == "2"
        assert domain.domain_name == "crm"
        assert domain.multi_tenant is True
        assert "management" in domain.aliases

    def test_add_subdomain(self):
        """Test adding subdomains to domain"""
        domain = Domain(
            domain_number=DomainNumber("2"),
            domain_name="crm",
            description="CRM",
            multi_tenant=False
        )

        subdomain = Subdomain(
            subdomain_number="01",
            subdomain_name="customer",
            description="Customer management"
        )

        domain.add_subdomain(subdomain)

        assert "01" in domain.subdomains
        assert domain.subdomains["01"].subdomain_name == "customer"
        assert domain.subdomains["01"].parent_domain_number == "2"

    def test_allocate_entity_code(self):
        """Test allocating entity codes through domain"""
        domain = Domain(
            domain_number=DomainNumber("2"),
            domain_name="crm",
            description="CRM",
            multi_tenant=False
        )

        subdomain = Subdomain(
            subdomain_number="01",
            subdomain_name="customer",
            description="Customer management",
            next_entity_sequence=1
        )

        domain.add_subdomain(subdomain)

        # Allocate code
        code = domain.allocate_entity_code("01", "Contact")
        assert str(code) == "201010"  # domain 2, subdomain 01, entity 1, file 0

        # Check it was saved
        assert "Contact" in domain.subdomains["01"].entities
        assert domain.subdomains["01"].entities["Contact"]["table_code"] == "201010"

    def test_prevent_duplicate_subdomain(self):
        """Test preventing duplicate subdomains"""
        domain = Domain(
            domain_number=DomainNumber("2"),
            domain_name="crm",
            description="CRM",
            multi_tenant=False
        )

        subdomain1 = Subdomain(
            subdomain_number="01",
            subdomain_name="customer",
            description="Customer management"
        )

        subdomain2 = Subdomain(
            subdomain_number="01",  # Same number
            subdomain_name="client",
            description="Client management"
        )

        domain.add_subdomain(subdomain1)

        with pytest.raises(ValueError, match="already exists"):
            domain.add_subdomain(subdomain2)