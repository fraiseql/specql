"""Unit tests for DomainService"""
import pytest
from unittest.mock import Mock
from src.application.services.domain_service import DomainService
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber, TableCode

class TestDomainService:
    """Test domain service with mocked repository"""

    def setup_method(self):
        """Setup with mocked repository"""
        self.mock_repo = Mock()
        self.service = DomainService(self.mock_repo)

    def test_register_domain(self):
        """Test registering a new domain"""
        # Register domain
        domain = self.service.register_domain(
            domain_number="2",
            domain_name="crm",
            description="Customer Relationship Management",
            multi_tenant=True,
            aliases=["sales", "management"]
        )

        # Verify domain was created correctly
        assert domain.domain_number.value == "2"
        assert domain.domain_name == "crm"
        assert domain.multi_tenant is True
        assert "sales" in domain.aliases

        # Verify repository was called
        self.mock_repo.save.assert_called_once_with(domain)

    def test_allocate_entity_code_success(self):
        """Test successful entity code allocation"""
        # Mock domain with subdomain
        mock_domain = Mock(spec=Domain)
        mock_domain.domain_name = "crm"
        mock_subdomain = Mock(spec=Subdomain)
        mock_subdomain.subdomain_name = "customer"
        mock_subdomain.allocate_next_code.return_value = TableCode("201010")
        mock_domain.subdomains = {"01": mock_subdomain}

        # Mock repository to return domain
        self.mock_repo.find_by_name.return_value = mock_domain

        # Allocate code
        code = self.service.allocate_entity_code("crm", "customer", "Contact")

        # Verify correct code returned
        assert str(code) == "201010"

        # Verify repository interactions
        self.mock_repo.find_by_name.assert_called_once_with("crm")
        mock_subdomain.allocate_next_code.assert_called_once_with("Contact")
        self.mock_repo.save.assert_called_once_with(mock_domain)

    def test_allocate_entity_code_domain_not_found(self):
        """Test allocation when domain not found"""
        self.mock_repo.find_by_name.return_value = None

        with pytest.raises(ValueError, match="Domain nonexistent not found"):
            self.service.allocate_entity_code("nonexistent", "customer", "Contact")

    def test_allocate_entity_code_subdomain_not_found(self):
        """Test allocation when subdomain not found"""
        # Mock domain without the requested subdomain
        mock_domain = Mock(spec=Domain)
        mock_domain.domain_name = "crm"
        mock_domain.subdomains = {}  # No subdomains

        self.mock_repo.find_by_name.return_value = mock_domain

        with pytest.raises(ValueError, match="Subdomain wrong not found in crm"):
            self.service.allocate_entity_code("crm", "wrong", "Contact")