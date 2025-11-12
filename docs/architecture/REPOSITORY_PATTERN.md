# Repository Pattern for SpecQL - IMPLEMENTED ✅

**Status**: Production Implementation
**Last Updated**: 2025-11-12
**Implementation**: Phases 1-4 Complete

---

## Overview

SpecQL implements the Repository Pattern using Python's `typing.Protocol` for structural subtyping. This provides abstract data access with complete flexibility to swap implementations.

**Current Implementations**:
- ✅ `PostgreSQLDomainRepository` - Production (primary)
- ✅ `InMemoryDomainRepository` - Testing
- ✅ `MonitoredPostgreSQLRepository` - Production with monitoring

---

## Principles

### 1. Abstract Data Access
Hide database implementation details behind repository protocol

### 2. Domain-Driven
Repositories return **domain entities**, not raw data structures

### 3. Testable
Easy to mock for unit tests using in-memory implementations

### 4. Single Responsibility
One repository per aggregate root

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Application Layer                   │
│  (Services depend on Repository Protocol)           │
│  DomainService(repository: DomainRepository)        │
└──────────────────────┬──────────────────────────────┘
                       │ Depends on interface
                       ▼
┌─────────────────────────────────────────────────────┐
│              Repository Protocol                     │
│  class DomainRepository(Protocol):                  │
│    def get(domain_number) -> Domain                 │
│    def find_by_name(name) -> Domain | None          │
│    def save(domain) -> None                         │
│    def list_all() -> list[Domain]                  │
└──────────────────────┬──────────────────────────────┘
                       │ Implemented by
                       ▼
┌─────────────────────────────────────────────────────┐
│            Concrete Implementations                  │
│  • PostgreSQLDomainRepository ✅                    │
│  • InMemoryDomainRepository ✅                      │
│  • MonitoredPostgreSQLRepository ✅                 │
└─────────────────────────────────────────────────────┘
```

---

## Implementation

### Repository Protocol

**File**: `src/domain/repositories/domain_repository.py`

```python
"""Domain Repository Protocol"""
from typing import Protocol
from src.domain.entities.domain import Domain

class DomainRepository(Protocol):
    """
    Repository for Domain aggregate root

    Uses Protocol (structural subtyping) instead of ABC
    for maximum flexibility
    """

    def get(self, domain_number: str) -> Domain:
        """
        Get domain by number

        Raises:
            ValueError: If domain not found
        """
        ...

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """
        Find domain by name or alias

        Returns:
            Domain if found, None otherwise
        """
        ...

    def save(self, domain: Domain) -> None:
        """
        Save domain (insert or update)

        Transaction management:
        - Repository handles transaction commit
        - Atomic operation (domain + subdomains)
        """
        ...

    def list_all(self) -> list[Domain]:
        """List all domains"""
        ...
```

**Why Protocol over ABC?**
- ✅ Structural subtyping (duck typing with type safety)
- ✅ No need to inherit from base class
- ✅ Easier to add new implementations
- ✅ Better for testing (simple classes can match protocol)

---

### PostgreSQL Implementation (Production)

**File**: `src/infrastructure/repositories/postgresql_domain_repository.py`

```python
"""PostgreSQL-backed Domain Repository"""
import psycopg
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber

class PostgreSQLDomainRepository:
    """
    PostgreSQL implementation of DomainRepository protocol

    Transaction Management:
    - Uses psycopg connection context manager
    - Auto-commit on context exit
    - Rollback on exception
    """

    def __init__(self, db_url: str):
        """
        Initialize repository

        Args:
            db_url: PostgreSQL connection string
                   e.g., "postgresql://user:pass@localhost/specql"
        """
        self.db_url = db_url

    def get(self, domain_number: str) -> Domain:
        """
        Get domain by number from PostgreSQL

        Loads full aggregate:
        - Domain
        - Subdomains
        - Entity registrations

        Raises:
            ValueError: If domain not found
        """
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Load domain
                cur.execute("""
                    SELECT domain_number, domain_name, description,
                           multi_tenant, aliases
                    FROM specql_registry.tb_domain
                    WHERE domain_number = %s
                """, (domain_number,))

                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Domain {domain_number} not found")

                # Create domain entity
                domain = Domain(
                    domain_number=DomainNumber(row[0]),
                    domain_name=row[1],
                    description=row[2],
                    multi_tenant=row[3],
                    aliases=row[4] or []
                )

                # Load subdomains (part of aggregate)
                cur.execute("""
                    SELECT pk_subdomain, subdomain_number, subdomain_name,
                           description, next_entity_sequence
                    FROM specql_registry.tb_subdomain
                    WHERE fk_domain = (
                        SELECT pk_domain
                        FROM specql_registry.tb_domain
                        WHERE domain_number = %s
                    )
                """, (domain_number,))

                for subdomain_row in cur.fetchall():
                    subdomain = Subdomain(
                        subdomain_number=subdomain_row[1],
                        subdomain_name=subdomain_row[2],
                        description=subdomain_row[3],
                        next_entity_sequence=subdomain_row[4]
                    )

                    # Load entity registrations
                    cur.execute("""
                        SELECT entity_name, table_code, entity_sequence
                        FROM specql_registry.tb_entity_registration
                        WHERE fk_subdomain = %s
                    """, (subdomain_row[0],))

                    for entity_row in cur.fetchall():
                        subdomain.entities[entity_row[0]] = {
                            'table_code': entity_row[1],
                            'entity_sequence': entity_row[2]
                        }

                    domain.add_subdomain(subdomain)

                return domain

    def save(self, domain: Domain) -> None:
        """
        Save domain to PostgreSQL

        Transaction:
        - Saves domain
        - Saves all subdomains
        - Commits atomically
        - Rolls back on error

        Uses UPSERT (INSERT ... ON CONFLICT):
        - Insert if new
        - Update if exists
        """
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Save/update domain
                cur.execute("""
                    INSERT INTO specql_registry.tb_domain
                    (domain_number, domain_name, description,
                     multi_tenant, aliases)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (domain_number) DO UPDATE SET
                        domain_name = EXCLUDED.domain_name,
                        description = EXCLUDED.description,
                        multi_tenant = EXCLUDED.multi_tenant,
                        aliases = EXCLUDED.aliases
                    RETURNING pk_domain
                """, (
                    domain.domain_number.value,
                    domain.domain_name,
                    domain.description,
                    domain.multi_tenant,
                    domain.aliases
                ))

                result = cur.fetchone()
                if result is None:
                    raise ValueError(
                        f"Failed to save domain {domain.domain_number.value}"
                    )
                domain_pk = result[0]

                # Save/update subdomains
                for subdomain in domain.subdomains.values():
                    cur.execute("""
                        INSERT INTO specql_registry.tb_subdomain
                        (fk_domain, subdomain_number, subdomain_name,
                         description, next_entity_sequence)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (fk_domain, subdomain_number) DO UPDATE SET
                            subdomain_name = EXCLUDED.subdomain_name,
                            description = EXCLUDED.description,
                            next_entity_sequence = EXCLUDED.next_entity_sequence
                    """, (
                        domain_pk,
                        subdomain.subdomain_number,
                        subdomain.subdomain_name,
                        subdomain.description,
                        subdomain.next_entity_sequence
                    ))

                # Commit transaction
                conn.commit()

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """
        Find domain by name or alias

        Search strategy:
        1. Try exact name match
        2. Try alias match
        3. Return None if not found
        """
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Try exact name match
                cur.execute("""
                    SELECT domain_number
                    FROM specql_registry.tb_domain
                    WHERE domain_name = %s
                """, (name_or_alias,))

                row = cur.fetchone()
                if row:
                    return self.get(row[0])

                # Try alias match
                cur.execute("""
                    SELECT domain_number
                    FROM specql_registry.tb_domain
                    WHERE %s = ANY(aliases)
                """, (name_or_alias,))

                row = cur.fetchone()
                if row:
                    return self.get(row[0])

                return None

    def list_all(self) -> list[Domain]:
        """
        List all domains

        Loads full aggregates for all domains
        """
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT domain_number FROM specql_registry.tb_domain"
                )
                domain_numbers = [row[0] for row in cur.fetchall()]
                return [self.get(num) for num in domain_numbers]
```

---

### In-Memory Implementation (Testing)

**File**: `src/infrastructure/repositories/in_memory_domain_repository.py`

```python
"""In-Memory Domain Repository for Testing"""
from src.domain.entities.domain import Domain

class InMemoryDomainRepository:
    """
    In-memory implementation for unit tests

    Perfect for testing without database:
    - Fast (no I/O)
    - Isolated (no shared state)
    - Deterministic (no external dependencies)
    """

    def __init__(self):
        """Initialize with empty storage"""
        self._domains: dict[str, Domain] = {}

    def get(self, domain_number: str) -> Domain:
        """Get domain from memory"""
        if domain_number not in self._domains:
            raise ValueError(f"Domain {domain_number} not found")
        return self._domains[domain_number]

    def save(self, domain: Domain) -> None:
        """Save domain to memory"""
        self._domains[domain.domain_number.value] = domain

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """Find domain by name or alias"""
        for domain in self._domains.values():
            if domain.domain_name == name_or_alias:
                return domain
            if name_or_alias in domain.aliases:
                return domain
        return None

    def list_all(self) -> list[Domain]:
        """List all domains"""
        return list(self._domains.values())

    def clear(self):
        """Clear all data (useful for test cleanup)"""
        self._domains.clear()
```

---

## Transaction Management

### Strategy: Repository Commits

**Decision**: Repositories manage their own transactions

**Rationale**:
- ✅ Simple for single-repository operations (most cases)
- ✅ Clear responsibility (repository owns transaction)
- ✅ Connection context manager handles rollback

**Implementation**:
```python
def save(self, domain: Domain) -> None:
    with psycopg.connect(self.db_url) as conn:
        with conn.cursor() as cur:
            # Multiple operations
            cur.execute(...)  # Save domain
            cur.execute(...)  # Save subdomains

            # Commit at end
            conn.commit()  # Repository commits

    # Auto-rollback if exception raised
```

### Complex Scenarios: Unit of Work (Future)

For multi-repository operations, we'll add Unit of Work pattern:

```python
class UnitOfWork:
    """Manages transactions across multiple repositories"""

    def __init__(self, db_url: str):
        self.conn = psycopg.connect(db_url)
        self.domain_repo = PostgreSQLDomainRepository(self.conn)
        self.pattern_repo = PostgreSQLPatternRepository(self.conn)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
```

**Current Status**: Not yet needed, repositories handle 99% of cases

---

## Usage Examples

### Application Service

```python
from src.application.services.domain_service import DomainService
from src.infrastructure.repositories.postgresql_domain_repository import PostgreSQLDomainRepository

# Create repository
repo = PostgreSQLDomainRepository("postgresql://localhost/specql")

# Create service
service = DomainService(repo)

# Use service (calls repository)
code = service.allocate_entity_code("crm", "customer", "Lead")
print(f"Allocated: {code}")  # "012059"
```

### Unit Testing with Mock

```python
from unittest.mock import Mock
from src.domain.entities.domain import Domain
from src.domain.value_objects import DomainNumber

def test_domain_service():
    # Mock repository
    mock_repo = Mock()
    mock_repo.find_by_name.return_value = Domain(
        domain_number=DomainNumber("2"),
        domain_name="crm",
        description="CRM",
        multi_tenant=True
    )

    # Create service with mock
    service = DomainService(mock_repo)

    # Use service
    domain = service.find_domain("crm")

    # Verify
    assert domain.domain_name == "crm"
    mock_repo.find_by_name.assert_called_once_with("crm")
```

### Integration Testing

```python
from src.infrastructure.repositories.in_memory_domain_repository import InMemoryDomainRepository

def test_allocate_code_integration():
    # Use in-memory repository
    repo = InMemoryDomainRepository()
    service = DomainService(repo)

    # Register domain
    service.register_domain("2", "crm", "CRM", True)

    # Add subdomain
    service.add_subdomain("crm", "3", "customer")

    # Allocate code
    code = service.allocate_entity_code("crm", "customer", "Lead")

    assert str(code) == "023001"
```

---

## Testing Strategy

### Unit Tests
- **What**: Domain entities, value objects
- **How**: Pure Python tests, no database
- **Coverage**: >90%

### Service Tests
- **What**: Application services
- **How**: Mock repositories
- **Coverage**: >90%

### Repository Tests
- **What**: Repository implementations
- **How**: Real database (PostgreSQL test instance) or in-memory
- **Coverage**: >80%

### Integration Tests
- **What**: Full stack (service → repository → database)
- **How**: In-memory repository or test database
- **Coverage**: >70%

---

## Benefits

### 1. Testability

**Before** (direct database access):
```python
def allocate_code(domain_name):
    conn = psycopg.connect(...)  # Hard to test!
    # Direct SQL
```

**After** (repository pattern):
```python
def allocate_code(domain_name):
    domain = self.repository.find_by_name(domain_name)  # Easy to mock!
    return domain.allocate_code(...)
```

### 2. Flexibility

Swap implementations without changing services:
```python
# Development
repo = InMemoryDomainRepository()

# Production
repo = PostgreSQLDomainRepository(db_url)

# Same service works with both!
service = DomainService(repo)
```

### 3. Performance Monitoring

```python
class MonitoredPostgreSQLRepository:
    def __init__(self, db_url: str):
        self.repo = PostgreSQLDomainRepository(db_url)
        self.metrics = MetricsCollector()

    def get(self, domain_number: str) -> Domain:
        start = time.time()
        result = self.repo.get(domain_number)
        self.metrics.record("get", time.time() - start)
        return result
```

### 4. Clean Architecture

Dependency inversion - services depend on **protocols**, not implementations:

```python
# Service depends on protocol (interface)
class DomainService:
    def __init__(self, repository: DomainRepository):  # Protocol!
        self.repository = repository

# Can use any implementation
service = DomainService(PostgreSQLDomainRepository(...))
service = DomainService(InMemoryDomainRepository())
service = DomainService(MonitoredRepository(...))
```

---

## Pattern Repository (Similar)

**File**: `src/domain/repositories/pattern_repository.py`

Same pattern for domain patterns:
- ✅ `PatternRepository` protocol
- ✅ `PostgreSQLPatternRepository` implementation
- ✅ `SQLitePatternRepository` (legacy)
- ✅ Used by `PatternService`

---

## Files

```
src/
├── domain/repositories/
│   ├── __init__.py
│   ├── domain_repository.py              ✅ Protocol
│   └── pattern_repository.py             ✅ Protocol
│
└── infrastructure/repositories/
    ├── __init__.py
    ├── postgresql_domain_repository.py   ✅ Production
    ├── postgresql_pattern_repository.py  ✅ Production
    ├── in_memory_domain_repository.py    ✅ Testing
    ├── monitored_postgresql_repository.py ✅ Monitoring
    └── sqlite_pattern_repository.py      ✅ Legacy
```

---

## Summary

✅ **Repository Pattern Implemented**
- Protocol-based (structural subtyping)
- PostgreSQL primary implementation
- In-memory for testing
- Transaction management in repositories
- Clean Architecture compliance

✅ **Benefits Realized**
- Testable (easy mocking)
- Flexible (swap implementations)
- Performant (monitored variant)
- Maintainable (clear separation)

✅ **Production Ready**
- All tests passing
- Used in CLI and generators
- PostgreSQL is default
- Monitoring available

---

**Status**: IMPLEMENTED ✅
**Phase**: 4 Complete (PostgreSQL migration done)
**Next**: Phase 5 (Domain entities refinement)

*Pattern documented from actual implementation, not theory.* 📚
