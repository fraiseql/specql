"""Unit tests for InMemoryDomainRepository"""

import pytest
from src.infrastructure.repositories.in_memory_domain_repository import (
    InMemoryDomainRepository,
)
from src.domain.entities.domain import Domain
from src.domain.value_objects import DomainNumber


class TestInMemoryDomainRepository:
    """Test in-memory repository implementation"""

    def setup_method(self):
        """Setup fresh repository for each test"""
        self.repo = InMemoryDomainRepository()

    def test_save_and_get_domain(self):
        """Test saving and retrieving domains"""
        domain = Domain(
            domain_number=DomainNumber("02"),
            domain_name="crm",
            description="Customer Relationship Management",
            multi_tenant=True,
            aliases=["sales"],
        )

        # Save domain
        self.repo.save(domain)

        # Retrieve domain
        retrieved = self.repo.get("02")
        assert retrieved.domain_name == "crm"
        assert retrieved.multi_tenant is True
        assert "sales" in retrieved.aliases

    def test_find_by_name(self):
        """Test finding domain by name or alias"""
        domain = Domain(
            domain_number=DomainNumber("03"),
            domain_name="catalog",
            description="Product catalog",
            multi_tenant=False,
            aliases=["products", "inventory"],
        )

        self.repo.save(domain)

        # Find by name
        found = self.repo.find_by_name("catalog")
        assert found is not None
        assert found.domain_number.value == "03"

        # Find by alias
        found_alias = self.repo.find_by_name("products")
        assert found_alias is not None
        assert found_alias.domain_name == "catalog"

        # Not found
        not_found = self.repo.find_by_name("nonexistent")
        assert not_found is None

    def test_list_all_domains(self):
        """Test listing all domains"""
        # Create and save multiple domains
        domains = []
        for i in range(1, 4):
            domain = Domain(
                domain_number=DomainNumber(f"{i:02X}"),
                domain_name=f"domain{i}",
                description=f"Domain {i}",
                multi_tenant=False,
            )
            self.repo.save(domain)
            domains.append(domain)

        # List all
        all_domains = self.repo.list_all()
        assert len(all_domains) == 3

        # Check they're the same objects
        domain_names = {d.domain_name for d in all_domains}
        assert domain_names == {"domain1", "domain2", "domain3"}

    def test_get_nonexistent_domain(self):
        """Test getting a domain that doesn't exist"""
        with pytest.raises(ValueError, match="Domain nonexistent not found"):
            self.repo.get("nonexistent")

    def test_clear_repository(self):
        """Test clearing the repository"""
        domain = Domain(
            domain_number=DomainNumber("01"),
            domain_name="test",
            description="Test domain",
            multi_tenant=False,
        )

        self.repo.save(domain)
        assert len(self.repo.list_all()) == 1

        self.repo.clear()
        assert len(self.repo.list_all()) == 0
