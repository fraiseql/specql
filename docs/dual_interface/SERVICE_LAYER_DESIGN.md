# Service Layer Design

**Date**: 2025-11-12
**Purpose**: Design application service layer for CLI + GraphQL access
**Pattern**: Application Services + Domain-Driven Design

---

## Service Layer Responsibilities

### Application Services
**Purpose**: Orchestrate use cases, coordinate domain objects and repositories

**Responsibilities**:
- Accept input from presentation layer (CLI, GraphQL)
- Validate input and create value objects
- Load domain aggregates from repositories
- Execute business logic (domain methods)
- Persist changes via repositories
- Return DTOs to presentation layer

**NOT Responsible For**:
- ❌ Presentation logic (formatting output)
- ❌ Infrastructure (database connections)
- ❌ Domain logic (business rules in aggregates)

---

## Service Interfaces

### 1. DomainService

**Purpose**: Manage domain registration and queries

```python
# src/application/services/domain_service.py

from dataclasses import dataclass
from typing import List, Optional
from src.domain.entities.domain import Domain
from src.domain.repositories.domain_repository import DomainRepository
from src.domain.value_objects.domain_number import DomainNumber


@dataclass
class DomainDTO:
    """Data Transfer Object for Domain"""
    domain_number: int
    domain_name: str
    schema_type: str
    identifier: str
    pk_domain: Optional[int] = None


class DomainAlreadyExistsError(Exception):
    """Raised when domain number already exists"""
    def __init__(self, domain_number: int):
        self.domain_number = domain_number
        super().__init__(f"Domain {domain_number} already exists")


class DomainNotFoundError(Exception):
    """Raised when domain not found"""
    def __init__(self, domain_number: int):
        self.domain_number = domain_number
        super().__init__(f"Domain {domain_number} not found")


class DomainService:
    """Application service for domain management"""

    def __init__(self, repository: DomainRepository):
        self.repository = repository

    def register_domain(
        self,
        domain_number: int,
        domain_name: str,
        schema_type: str
    ) -> DomainDTO:
        """
        Register a new domain.

        Args:
            domain_number: Unique domain identifier (1-255)
            domain_name: Human-readable domain name
            schema_type: 'framework', 'multi_tenant', or 'shared'

        Returns:
            DomainDTO with registered domain details

        Raises:
            DomainAlreadyExistsError: If domain_number already exists
            ValueError: If input validation fails
        """
        # Create value object (validates range)
        domain_number_vo = DomainNumber(domain_number)

        # Check uniqueness
        if self.repository.exists_by_number(domain_number):
            raise DomainAlreadyExistsError(domain_number)

        # Create domain aggregate
        domain = Domain(
            domain_number=domain_number_vo,
            domain_name=domain_name,
            schema_type=schema_type
        )

        # Persist
        saved_domain = self.repository.save(domain)

        # Return DTO
        return DomainDTO(
            domain_number=saved_domain.domain_number.value,
            domain_name=saved_domain.domain_name,
            schema_type=saved_domain.schema_type,
            identifier=saved_domain.identifier,
            pk_domain=saved_domain.pk_domain
        )

    def list_domains(
        self,
        schema_type: Optional[str] = None
    ) -> List[DomainDTO]:
        """
        List all domains, optionally filtered by schema_type.

        Args:
            schema_type: Optional filter by schema type

        Returns:
            List of DomainDTO objects
        """
        if schema_type:
            domains = self.repository.find_by_schema_type(schema_type)
        else:
            domains = self.repository.find_all()

        return [
            DomainDTO(
                domain_number=d.domain_number.value,
                domain_name=d.domain_name,
                schema_type=d.schema_type,
                identifier=d.identifier,
                pk_domain=d.pk_domain
            )
            for d in domains
        ]

    def get_domain(
        self,
        domain_number: int
    ) -> DomainDTO:
        """
        Get domain by number.

        Args:
            domain_number: Domain identifier

        Returns:
            DomainDTO

        Raises:
            DomainNotFoundError: If domain not found
        """
        domain_number_vo = DomainNumber(domain_number)
        domain = self.repository.find_by_number(domain_number_vo)

        if not domain:
            raise DomainNotFoundError(domain_number)

        return DomainDTO(
            domain_number=domain.domain_number.value,
            domain_name=domain.domain_name,
            schema_type=domain.schema_type,
            identifier=domain.identifier,
            pk_domain=domain.pk_domain
        )
```

---

### 2. SubdomainService

**Purpose**: Manage subdomain registration and queries

```python
# src/application/services/subdomain_service.py

@dataclass
class SubdomainDTO:
    """Data Transfer Object for Subdomain"""
    subdomain_number: int
    subdomain_name: str
    parent_domain_number: int
    identifier: str
    pk_subdomain: Optional[int] = None


class SubdomainAlreadyExistsError(Exception):
    """Raised when subdomain already exists in domain"""
    def __init__(self, domain_number: int, subdomain_number: int):
        self.domain_number = domain_number
        self.subdomain_number = subdomain_number
        super().__init__(
            f"Subdomain {subdomain_number} already exists in domain {domain_number}"
        )


class SubdomainService:
    """Application service for subdomain management"""

    def __init__(
        self,
        subdomain_repository: SubdomainRepository,
        domain_repository: DomainRepository
    ):
        self.subdomain_repository = subdomain_repository
        self.domain_repository = domain_repository

    def register_subdomain(
        self,
        parent_domain_number: int,
        subdomain_number: int,
        subdomain_name: str
    ) -> SubdomainDTO:
        """
        Register a new subdomain under a parent domain.

        Args:
            parent_domain_number: Parent domain identifier
            subdomain_number: Subdomain number within domain (0-15)
            subdomain_name: Human-readable subdomain name

        Returns:
            SubdomainDTO with registered subdomain details

        Raises:
            DomainNotFoundError: If parent domain doesn't exist
            SubdomainAlreadyExistsError: If subdomain already exists
            ValueError: If input validation fails
        """
        # Validate parent domain exists
        parent_domain_number_vo = DomainNumber(parent_domain_number)
        parent_domain = self.domain_repository.find_by_number(parent_domain_number_vo)

        if not parent_domain:
            raise DomainNotFoundError(parent_domain_number)

        # Create value object (validates range 0-15)
        subdomain_number_vo = SubdomainNumber(subdomain_number)

        # Check uniqueness within domain
        if self.subdomain_repository.exists_in_domain(
            parent_domain_number_vo,
            subdomain_number_vo
        ):
            raise SubdomainAlreadyExistsError(parent_domain_number, subdomain_number)

        # Create subdomain aggregate
        subdomain = Subdomain(
            subdomain_number=subdomain_number_vo,
            subdomain_name=subdomain_name,
            parent_domain=parent_domain
        )

        # Persist
        saved_subdomain = self.subdomain_repository.save(subdomain)

        # Return DTO
        return SubdomainDTO(
            subdomain_number=saved_subdomain.subdomain_number.value,
            subdomain_name=saved_subdomain.subdomain_name,
            parent_domain_number=parent_domain_number,
            identifier=saved_subdomain.identifier,
            pk_subdomain=saved_subdomain.pk_subdomain
        )

    def list_subdomains(
        self,
        parent_domain_number: Optional[int] = None
    ) -> List[SubdomainDTO]:
        """
        List all subdomains, optionally filtered by parent domain.

        Args:
            parent_domain_number: Optional filter by parent domain

        Returns:
            List of SubdomainDTO objects
        """
        if parent_domain_number:
            domain_number_vo = DomainNumber(parent_domain_number)
            subdomains = self.subdomain_repository.find_by_domain(domain_number_vo)
        else:
            subdomains = self.subdomain_repository.find_all()

        return [
            SubdomainDTO(
                subdomain_number=s.subdomain_number.value,
                subdomain_name=s.subdomain_name,
                parent_domain_number=s.parent_domain.domain_number.value,
                identifier=s.identifier,
                pk_subdomain=s.pk_subdomain
            )
            for s in subdomains
        ]
```

---

### 3. PatternService (Enhanced)

**Purpose**: Manage pattern library operations

```python
# src/application/services/pattern_service.py (enhanced)

@dataclass
class PatternDTO:
    """Data Transfer Object for Pattern"""
    pattern_id: str
    pattern_name: str
    category: str
    description: str
    pattern_type: str
    usage_count: int
    popularity_score: float


class PatternService:
    """Application service for pattern management (enhanced for GraphQL)"""

    def __init__(
        self,
        pattern_repository: PatternRepository,
        embedding_service: EmbeddingService
    ):
        self.pattern_repository = pattern_repository
        self.embedding_service = embedding_service

    def search_patterns(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[PatternDTO]:
        """
        Search patterns by natural language query using semantic similarity.

        Args:
            query: Natural language search query
            limit: Maximum number of results
            min_similarity: Minimum similarity score (0-1)

        Returns:
            List of PatternDTO objects, sorted by similarity
        """
        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query)

        # Search patterns
        patterns_with_similarity = self.pattern_repository.search_by_similarity(
            query_embedding=query_embedding,
            limit=limit,
            min_similarity=min_similarity
        )

        # Return DTOs
        return [
            PatternDTO(
                pattern_id=p.pattern_id,
                pattern_name=p.pattern_name,
                category=p.category,
                description=p.description,
                pattern_type=p.pattern_type,
                usage_count=p.usage_count,
                popularity_score=p.popularity_score
            )
            for p, similarity in patterns_with_similarity
        ]

    def get_pattern(
        self,
        pattern_id: str
    ) -> PatternDTO:
        """
        Get pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            PatternDTO

        Raises:
            PatternNotFoundError: If pattern not found
        """
        pattern = self.pattern_repository.find_by_id(pattern_id)

        if not pattern:
            raise PatternNotFoundError(pattern_id)

        return PatternDTO(
            pattern_id=pattern.pattern_id,
            pattern_name=pattern.pattern_name,
            category=pattern.category,
            description=pattern.description,
            pattern_type=pattern.pattern_type,
            usage_count=pattern.usage_count,
            popularity_score=pattern.popularity_score
        )
```

---

## Service Layer Testing

### Unit Tests (Fast)

```python
# tests/unit/services/test_domain_service.py

from src.application.services.domain_service import DomainService, DomainAlreadyExistsError
from src.infrastructure.repositories.in_memory_domain_repository import InMemoryDomainRepository


class TestDomainService:

    """Unit tests for DomainService"""

    def test_register_domain_success(self):
        """Test registering a new domain successfully"""
        # Arrange
        repository = InMemoryDomainRepository()
        service = DomainService(repository)

        # Act
        result = service.register_domain(
            domain_number=1,
            domain_name="core",
            schema_type="framework"
        )

        # Assert
        assert result.domain_number == 1
        assert result.domain_name == "core"
        assert result.identifier == "D1"

    def test_register_domain_already_exists(self):
        """Test registering duplicate domain number raises error"""
        # Arrange
        repository = InMemoryDomainRepository()
        service = DomainService(repository)
        service.register_domain(1, "core", "framework")

        # Act & Assert
        with pytest.raises(DomainAlreadyExistsError) as exc_info:
            service.register_domain(1, "duplicate", "shared")

        assert exc_info.value.domain_number == 1

    def test_list_domains_empty(self):
        """Test listing domains when none exist"""
        # Arrange
        repository = InMemoryDomainRepository()
        service = DomainService(repository)

        # Act
        result = service.list_domains()

        # Assert
        assert result == []

    def test_list_domains_filtered_by_schema_type(self):
        """Test listing domains filtered by schema type"""
        # Arrange
        repository = InMemoryDomainRepository()
        service = DomainService(repository)
        service.register_domain(1, "core", "framework")
        service.register_domain(2, "crm", "multi_tenant")
        service.register_domain(3, "catalog", "shared")

        # Act
        result = service.list_domains(schema_type="multi_tenant")

        # Assert
        assert len(result) == 1
        assert result[0].domain_name == "crm"
```

---

## Benefits Summary

### 1. Reusability
**CLI + GraphQL** both use same services → DRY principle

### 2. Testability
Unit tests run **10x faster** than integration tests (in-memory repositories)

### 3. Maintainability
Clear separation of concerns → Easy to modify presentation or business logic independently

### 4. Type Safety
DTOs provide clear contracts between layers → TypeScript-friendly for GraphQL

---

**Status**: Service layer designed
**Next**: Implement services (Day 2)