"""Unit tests for DomainService"""
import pytest
from src.application.services.domain_service import DomainService
from src.application.exceptions import DomainAlreadyExistsError, DomainNotFoundError
from src.infrastructure.repositories.in_memory_domain_repository import InMemoryDomainRepository

class TestDomainService:
    """Test domain service with in-memory repository"""

    @pytest.fixture
    def service(self):
        """Create DomainService with in-memory repository"""
        repository = InMemoryDomainRepository()
        return DomainService(repository)

    def test_register_domain_success(self, service):
        """Test registering a new domain successfully"""
        # Act
        result = service.register_domain(
            domain_number="01",
            domain_name="core",
            schema_type="framework"
        )

        # Assert
        assert result.domain_number == "01"
        assert result.domain_name == "core"
        assert result.schema_type == "framework"
        assert result.identifier == "D01"

    def test_register_domain_already_exists(self, service):
        """Test registering duplicate domain number raises error"""
        # Arrange - register first domain
        service.register_domain("01", "core", "framework")

        # Act & Assert
        with pytest.raises(DomainAlreadyExistsError) as exc_info:
            service.register_domain("01", "duplicate", "shared")

        assert exc_info.value.domain_number == "01"

    def test_list_domains_all(self, service):
        """Test listing all domains"""
        # Arrange
        service.register_domain("01", "core", "framework")
        service.register_domain("02", "crm", "multi_tenant")

        # Act
        result = service.list_domains()

        # Assert
        assert len(result) == 2
        assert [d.domain_name for d in result] == ["core", "crm"]

    def test_get_domain_success(self, service):
        """Test getting domain by number"""
        # Arrange
        service.register_domain("02", "crm", "multi_tenant")

        # Act
        result = service.get_domain("02")

        # Assert
        assert result.domain_number == "02"
        assert result.domain_name == "crm"
        assert result.identifier == "D02"

    def test_get_domain_not_found(self, service):
        """Test getting non-existent domain raises error"""
        # Act & Assert
        with pytest.raises(DomainNotFoundError) as exc_info:
            service.get_domain("FF")

        assert exc_info.value.domain_number == "FF"