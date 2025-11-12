# SpecQL PostgreSQL Bootstrap: Eating Our Own Dog Food

**Date**: 2025-11-12
**Status**: Implementation Plan - REVISED
**Goal**: Migrate SpecQL's domain model to PostgreSQL using DDD + Repository Pattern + 6-digit hex architecture

---

## Executive Summary

### The Problem

SpecQL currently uses **multiple heterogeneous formats** for its domain model:

1. **Domain Registry**: `registry/domain_registry.yaml` (YAML)
2. **Pattern Library**: `database/pattern_library_schema.sql` (SQLite)
3. **Service Registry**: `registry/service_registry.yaml` (YAML)
4. **Type Registry**: Python code in `src/core/type_registry.py`

**Issues**:
- ❌ No single source of truth
- ❌ Manual synchronization required
- ❌ Can't query relationships between domains/patterns/types
- ❌ No ACID guarantees across registries
- ❌ We generate production PostgreSQL for users but don't use it ourselves
- ❌ Missing the power of our own 6-digit hierarchical architecture
- ❌ **No proper architecture** - Direct database access scattered throughout code
- ❌ **Hard to test** - Tightly coupled to data sources
- ❌ **No domain model** - Anemic entities with no business logic

### The Solution: "Eat Our Own Dog Food" + Proper Architecture

**Phase 0**: Establish proper architecture patterns FIRST
**Phase 1+**: Use SpecQL to generate SpecQL's own domain model in PostgreSQL

```
Architecture First:
  Repository Pattern → Domain Model (DDD) → Clean Architecture
                              ↓
Then Migration:
  registry/domain_registry.yaml  →  SpecQL Generator  →  PostgreSQL (6-digit)
```

### Benefits

✅ **Proper Architecture**: Repository pattern, DDD, clean separation
✅ **Single Source of Truth**: PostgreSQL becomes the canonical registry
✅ **ACID Transactions**: All registry operations are transactional
✅ **Testable**: Mock repositories for unit tests
✅ **Powerful Queries**: SQL joins between domains, patterns, entities
✅ **6-Digit Architecture**: Hierarchical organization we generate for users
✅ **GraphQL API**: Auto-generated FraiseQL API for registry
✅ **Dogfooding**: We use what we build (builds trust)

---

## Revised Implementation Timeline

### Phase 0: Architecture Foundation (Week 0 - CRITICAL)

**Goal**: Establish proper architectural patterns before any migration

**Why this comes FIRST**:
- ❌ **Stop** implementing without architecture
- ✅ **Start** with proper patterns
- ✅ Make code testable and maintainable
- ✅ Prepare for PostgreSQL migration

#### Step 0.1: Revert Working Directory (FIRST!)

**IMPORTANT**: Revert any uncommitted changes from previous attempts:

```bash
# Check what's uncommitted
git status

# Revert all uncommitted changes
git restore .

# Remove any new untracked directories created
rm -rf entities/specql_registry/

# Verify clean state
git status
# Should show: "nothing to commit, working tree clean"
```

#### Step 0.2: Repository Pattern Design

**Create**: `docs/architecture/REPOSITORY_PATTERN.md`

**Contents**:
```markdown
# Repository Pattern for SpecQL

## Principles

1. **Abstract Data Access**: Hide database implementation details
2. **Domain-Driven**: Repositories return domain entities, not raw data
3. **Testable**: Easy to mock for unit tests
4. **Single Responsibility**: One repository per aggregate root

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Application Layer                   │
│  (CLI, API, Services - depend on Repository Protocol)│
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              Repository Protocol (ABC)               │
│  - get(), find(), save(), delete()                  │
│  - Domain-focused interface                         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│            Concrete Implementations                  │
│  - PostgreSQLDomainRepository                       │
│  - YAMLDomainRepository (legacy)                    │
│  - InMemoryDomainRepository (testing)               │
└─────────────────────────────────────────────────────┘
```

## Example

```python
from abc import ABC, abstractmethod
from typing import Protocol

class DomainRepository(Protocol):
    """Repository for Domain aggregate"""

    def get(self, domain_number: str) -> Domain:
        """Get domain by number - raises if not found"""
        ...

    def find_by_name(self, name: str) -> Domain | None:
        """Find domain by name or alias"""
        ...

    def save(self, domain: Domain) -> None:
        """Save domain (insert or update)"""
        ...

    def list_all(self) -> list[Domain]:
        """List all domains"""
        ...
```
```

**Deliverable**: Complete repository pattern design document

#### Step 0.3: Domain-Driven Design (DDD)

**Create**: `docs/architecture/DDD_DOMAIN_MODEL.md`

**Contents**:
```markdown
# Domain-Driven Design for SpecQL

## Bounded Contexts

SpecQL has 4 bounded contexts:

1. **Registry Context**: Domains, subdomains, entities
2. **Pattern Context**: Domain patterns, templates, instantiations
3. **Type Context**: Type definitions, mappings
4. **Service Context**: Service registry, dependencies

## Aggregates

### Registry Context

**Aggregate Root**: `Domain`
**Entities**: `Subdomain`, `EntityRegistration`
**Value Objects**: `DomainNumber`, `TableCode`

```python
@dataclass
class Domain:
    """Aggregate Root for Registry Context"""
    domain_number: DomainNumber  # Value Object
    domain_name: str
    description: str
    multi_tenant: bool
    aliases: list[str]
    subdomains: list[Subdomain]  # Child entities

    def add_subdomain(self, subdomain: Subdomain) -> None:
        """Business logic: Add subdomain"""
        if self._has_subdomain(subdomain.number):
            raise ValueError(f"Subdomain {subdomain.number} already exists")
        self.subdomains.append(subdomain)

    def allocate_entity_code(self, subdomain_num: str, entity_name: str) -> TableCode:
        """Business logic: Allocate 6-digit code"""
        subdomain = self._get_subdomain(subdomain_num)
        return subdomain.allocate_next_code(entity_name)
```

## Layers

```
┌──────────────────────────────────────────┐
│         Presentation Layer               │
│  (CLI, GraphQL API)                      │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│         Application Layer                │
│  (Use Cases, Services)                   │
│  - RegisterDomainService                 │
│  - AllocateEntityCodeService             │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│          Domain Layer                    │
│  (Entities, Value Objects, Domain Logic) │
│  - Domain, Subdomain                     │
│  - DomainNumber, TableCode               │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│      Infrastructure Layer                │
│  (Repositories, Database, External APIs) │
│  - PostgreSQLDomainRepository            │
│  - YAMLDomainRepository                  │
└──────────────────────────────────────────┘
```
```

**Deliverable**: Complete DDD domain model design

#### Step 0.4: Implement Base Repository

**Create**: `src/domain/repositories/__init__.py`

```python
"""
Repository Pattern Implementation

Provides abstract base classes and protocols for data access.
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Protocol

T = TypeVar('T')

class Repository(Protocol, Generic[T]):
    """
    Generic repository protocol

    All concrete repositories should implement this protocol
    """

    def get(self, id: str) -> T:
        """Get entity by ID - raises if not found"""
        ...

    def find(self, id: str) -> T | None:
        """Find entity by ID - returns None if not found"""
        ...

    def save(self, entity: T) -> None:
        """Save entity (insert or update)"""
        ...

    def delete(self, id: str) -> None:
        """Delete entity by ID"""
        ...

    def list_all(self) -> list[T]:
        """List all entities"""
        ...
```

**Create**: `src/domain/repositories/domain_repository.py`

```python
"""Domain Repository Protocol"""
from typing import Protocol
from src.domain.entities.domain import Domain

class DomainRepository(Protocol):
    """Repository for Domain aggregate root"""

    def get(self, domain_number: str) -> Domain:
        """Get domain by number - raises if not found"""
        ...

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """Find domain by name or alias"""
        ...

    def save(self, domain: Domain) -> None:
        """Save domain"""
        ...

    def list_all(self) -> list[Domain]:
        """List all domains"""
        ...
```

**Deliverables**:
- [ ] `src/domain/repositories/__init__.py`
- [ ] `src/domain/repositories/domain_repository.py`
- [ ] `src/domain/repositories/pattern_repository.py`
- [ ] Unit tests for protocols

#### Step 0.5: Implement Domain Entities

**Create**: `src/domain/entities/domain.py`

```python
"""Domain Aggregate Root"""
from dataclasses import dataclass, field
from typing import List
from src.domain.value_objects import DomainNumber, TableCode

@dataclass
class Subdomain:
    """Subdomain entity (part of Domain aggregate)"""
    subdomain_number: str
    subdomain_name: str
    description: str | None
    next_entity_sequence: int = 1
    entities: dict = field(default_factory=dict)

    def allocate_next_code(self, entity_name: str) -> TableCode:
        """Allocate next entity code"""
        code = TableCode.generate(
            domain_num=self.parent_domain_number,
            subdomain_num=self.subdomain_number,
            entity_seq=self.next_entity_sequence
        )
        self.entities[entity_name] = {
            'table_code': str(code),
            'entity_sequence': self.next_entity_sequence
        }
        self.next_entity_sequence += 1
        return code

@dataclass
class Domain:
    """Domain Aggregate Root"""
    domain_number: DomainNumber
    domain_name: str
    description: str | None
    multi_tenant: bool
    aliases: List[str] = field(default_factory=list)
    subdomains: dict[str, Subdomain] = field(default_factory=dict)

    def add_subdomain(self, subdomain: Subdomain) -> None:
        """Add subdomain to domain"""
        if subdomain.subdomain_number in self.subdomains:
            raise ValueError(
                f"Subdomain {subdomain.subdomain_number} already exists in {self.domain_name}"
            )
        subdomain.parent_domain_number = self.domain_number.value
        self.subdomains[subdomain.subdomain_number] = subdomain

    def get_subdomain(self, subdomain_number: str) -> Subdomain:
        """Get subdomain by number"""
        if subdomain_number not in self.subdomains:
            raise ValueError(
                f"Subdomain {subdomain_number} not found in {self.domain_name}"
            )
        return self.subdomains[subdomain_number]

    def allocate_entity_code(self, subdomain_num: str, entity_name: str) -> TableCode:
        """Allocate 6-digit code for entity"""
        subdomain = self.get_subdomain(subdomain_num)
        return subdomain.allocate_next_code(entity_name)
```

**Create**: `src/domain/value_objects/__init__.py`

```python
"""Value Objects for Domain Model"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class DomainNumber:
    """Domain number (1-9) - immutable value object"""
    value: str

    def __post_init__(self):
        if not re.match(r'^[1-9]$', self.value):
            raise ValueError(f"Domain number must be 1-9, got: {self.value}")

    def __str__(self):
        return self.value

@dataclass(frozen=True)
class TableCode:
    """6-digit table code - immutable value object"""
    value: str

    def __post_init__(self):
        if not re.match(r'^\d{6}$', self.value):
            raise ValueError(f"Table code must be 6 digits, got: {self.value}")

    @classmethod
    def generate(cls, domain_num: str, subdomain_num: str, entity_seq: int) -> 'TableCode':
        """Generate 6-digit code from components"""
        code = f"{domain_num}{subdomain_num}{entity_seq:02d}"
        if len(code) != 6:
            # Handle longer sequences
            code = f"{domain_num}{subdomain_num}{entity_seq}"
        return cls(code)

    def __str__(self):
        return self.value
```

**Deliverables**:
- [ ] `src/domain/entities/domain.py`
- [ ] `src/domain/value_objects/__init__.py`
- [ ] Unit tests for entities
- [ ] Unit tests for value objects

#### Step 0.6: Implement Concrete Repositories

**Create**: `src/infrastructure/repositories/yaml_domain_repository.py`

```python
"""YAML-backed Domain Repository (legacy)"""
import yaml
from pathlib import Path
from src.domain.repositories.domain_repository import DomainRepository
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber

class YAMLDomainRepository:
    """Legacy YAML-backed repository"""

    def __init__(self, yaml_path: Path):
        self.yaml_path = yaml_path
        self._domains: dict[str, Domain] = {}
        self._load_from_yaml()

    def _load_from_yaml(self):
        """Load domains from YAML file"""
        with open(self.yaml_path) as f:
            data = yaml.safe_load(f)

        for domain_num, domain_data in data['domains'].items():
            domain = Domain(
                domain_number=DomainNumber(domain_num),
                domain_name=domain_data['name'],
                description=domain_data.get('description'),
                multi_tenant=domain_data.get('multi_tenant', False),
                aliases=domain_data.get('aliases', [])
            )

            # Load subdomains
            for subdomain_num, subdomain_data in domain_data.get('subdomains', {}).items():
                subdomain = Subdomain(
                    subdomain_number=subdomain_num,
                    subdomain_name=subdomain_data['name'],
                    description=subdomain_data.get('description'),
                    next_entity_sequence=subdomain_data.get('next_entity_sequence', 1),
                    entities=subdomain_data.get('entities', {})
                )
                domain.add_subdomain(subdomain)

            self._domains[domain_num] = domain

    def get(self, domain_number: str) -> Domain:
        """Get domain by number"""
        if domain_number not in self._domains:
            raise ValueError(f"Domain {domain_number} not found")
        return self._domains[domain_number]

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """Find domain by name or alias"""
        for domain in self._domains.values():
            if domain.domain_name == name_or_alias:
                return domain
            if name_or_alias in domain.aliases:
                return domain
        return None

    def save(self, domain: Domain) -> None:
        """Save domain (writes back to YAML)"""
        self._domains[domain.domain_number.value] = domain
        self._write_to_yaml()

    def list_all(self) -> list[Domain]:
        """List all domains"""
        return list(self._domains.values())

    def _write_to_yaml(self):
        """Write domains back to YAML"""
        # Convert domains to YAML structure
        data = {'version': '2.0.0', 'domains': {}}
        for domain in self._domains.values():
            data['domains'][domain.domain_number.value] = {
                'name': domain.domain_name,
                'description': domain.description,
                'multi_tenant': domain.multi_tenant,
                'aliases': domain.aliases,
                'subdomains': {
                    subdomain.subdomain_number: {
                        'name': subdomain.subdomain_name,
                        'description': subdomain.description,
                        'next_entity_sequence': subdomain.next_entity_sequence,
                        'entities': subdomain.entities
                    }
                    for subdomain in domain.subdomains.values()
                }
            }

        with open(self.yaml_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
```

**Create**: `src/infrastructure/repositories/postgresql_domain_repository.py`

```python
"""PostgreSQL-backed Domain Repository"""
import psycopg
from src.domain.repositories.domain_repository import DomainRepository
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber

class PostgreSQLDomainRepository:
    """PostgreSQL-backed repository"""

    def __init__(self, db_url: str):
        self.db_url = db_url

    def get(self, domain_number: str) -> Domain:
        """Get domain by number from PostgreSQL"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Get domain
                cur.execute("""
                    SELECT domain_number, domain_name, description, multi_tenant, aliases
                    FROM specql_registry.tb_domain
                    WHERE domain_number = %s
                """, (domain_number,))

                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Domain {domain_number} not found")

                domain = Domain(
                    domain_number=DomainNumber(row[0]),
                    domain_name=row[1],
                    description=row[2],
                    multi_tenant=row[3],
                    aliases=row[4] or []
                )

                # Get subdomains
                cur.execute("""
                    SELECT pk_subdomain, subdomain_number, subdomain_name, description, next_entity_sequence
                    FROM specql_registry.tb_subdomain
                    WHERE fk_domain = (
                        SELECT pk_domain FROM specql_registry.tb_domain WHERE domain_number = %s
                    )
                """, (domain_number,))

                for subdomain_row in cur.fetchall():
                    subdomain = Subdomain(
                        subdomain_number=subdomain_row[1],
                        subdomain_name=subdomain_row[2],
                        description=subdomain_row[3],
                        next_entity_sequence=subdomain_row[4]
                    )

                    # Get entities for this subdomain
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
        """Save domain to PostgreSQL (transactional)"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Save domain
                cur.execute("""
                    INSERT INTO specql_registry.tb_domain
                    (domain_number, domain_name, description, multi_tenant, aliases)
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

                domain_pk = cur.fetchone()[0]

                # Save subdomains
                for subdomain in domain.subdomains.values():
                    cur.execute("""
                        INSERT INTO specql_registry.tb_subdomain
                        (fk_domain, subdomain_number, subdomain_name, description, next_entity_sequence)
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

                conn.commit()
```

**Deliverables**:
- [ ] `src/infrastructure/repositories/yaml_domain_repository.py`
- [ ] `src/infrastructure/repositories/postgresql_domain_repository.py`
- [ ] `src/infrastructure/repositories/in_memory_domain_repository.py` (for tests)
- [ ] Integration tests for each repository

#### Step 0.7: Application Services

**Create**: `src/application/services/domain_service.py`

```python
"""Application Service for Domain operations"""
from src.domain.repositories.domain_repository import DomainRepository
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber, TableCode

class DomainService:
    """
    Application Service for Domain operations

    Uses repository abstraction - doesn't care about storage implementation
    """

    def __init__(self, repository: DomainRepository):
        self.repository = repository

    def register_domain(
        self,
        domain_number: str,
        domain_name: str,
        description: str | None,
        multi_tenant: bool,
        aliases: list[str] | None = None
    ) -> Domain:
        """Register a new domain"""
        domain = Domain(
            domain_number=DomainNumber(domain_number),
            domain_name=domain_name,
            description=description,
            multi_tenant=multi_tenant,
            aliases=aliases or []
        )
        self.repository.save(domain)
        return domain

    def allocate_entity_code(
        self,
        domain_name: str,
        subdomain_name: str,
        entity_name: str
    ) -> TableCode:
        """Allocate 6-digit code for entity"""
        # Find domain
        domain = self.repository.find_by_name(domain_name)
        if not domain:
            raise ValueError(f"Domain {domain_name} not found")

        # Find subdomain
        subdomain = None
        for sd in domain.subdomains.values():
            if sd.subdomain_name == subdomain_name:
                subdomain = sd
                break

        if not subdomain:
            raise ValueError(f"Subdomain {subdomain_name} not found in {domain_name}")

        # Allocate code (business logic in domain entity)
        code = subdomain.allocate_next_code(entity_name)

        # Save (increments next_entity_sequence)
        self.repository.save(domain)

        return code
```

**Deliverables**:
- [ ] `src/application/services/domain_service.py`
- [ ] `src/application/services/pattern_service.py`
- [ ] Unit tests using mock repositories

#### Step 0.8: Update Existing Code

**Update**: `src/generators/schema/naming_conventions.py`

```python
"""
Naming Conventions - Now uses Repository Pattern

BEFORE: Direct YAML access
AFTER: Uses DomainRepository abstraction
"""
from src.domain.repositories.domain_repository import DomainRepository
from src.infrastructure.repositories.yaml_domain_repository import YAMLDomainRepository

class NamingConventions:
    """Naming conventions for generated SQL"""

    def __init__(self, domain_repository: DomainRepository | None = None):
        # Default to YAML repository for backward compatibility
        if domain_repository is None:
            domain_repository = YAMLDomainRepository(Path('registry/domain_registry.yaml'))

        self.domain_repository = domain_repository

    def get_table_code(self, domain: str, subdomain: str, entity: str) -> str:
        """Get 6-digit table code"""
        domain_obj = self.domain_repository.find_by_name(domain)
        if not domain_obj:
            raise ValueError(f"Domain {domain} not found")

        # Business logic now lives in domain entity
        return str(domain_obj.allocate_entity_code(subdomain, entity))
```

**Deliverables**:
- [ ] Update all files that access registry directly
- [ ] Add dependency injection where needed
- [ ] Ensure backward compatibility

**Phase 0 Deliverables Summary**:
- [ ] `docs/architecture/REPOSITORY_PATTERN.md`
- [ ] `docs/architecture/DDD_DOMAIN_MODEL.md`
- [ ] Complete repository protocol implementations
- [ ] Complete domain entities and value objects
- [ ] Application services layer
- [ ] All unit tests passing (>90% coverage)
- [ ] Integration tests for each repository
- [ ] Updated existing code to use repositories

---

### Phase 1: Registry Schema (Week 1)

**Prerequisites**: Phase 0 MUST be complete

**Goal**: Create SpecQL YAML entities for domain registry, generate PostgreSQL DDL

#### Tasks

**1.1 Create Registry Entity YAMLs**

Now that we have proper domain model, create SpecQL YAML definitions:

**`entities/specql_registry/domain.yaml`**:
```yaml
entity: domain
schema: specql_registry
description: Top-level business domains (crm, catalog, projects)

organization:
  table_code: "011111"
  domain: core
  subdomain: registry
  entity_sequence: 1

fields:
  domain_number:
    type: text
    nullable: false
    unique: true
    description: "Single digit domain number (1-9)"

  domain_name:
    type: text
    nullable: false
    unique: true
    description: "Canonical domain name (crm, catalog)"

  description:
    type: text
    nullable: true

  multi_tenant:
    type: boolean
    nullable: false
    default: false
    description: "Whether this domain requires tenant_id"

  aliases:
    type: list(text)
    nullable: true
    description: "Alternative names (e.g., 'management' for 'crm')"

indexes:
  - fields: [domain_number]
    unique: true
  - fields: [domain_name]
    unique: true

fraiseql:
  enabled: true
  queries:
    find_one: true
    find_one_by_identifier: true
    find_many: true
```

*(Continue with subdomain.yaml, entity_registration.yaml as in original plan)*

**Deliverables**:
- [ ] `entities/specql_registry/domain.yaml`
- [ ] `entities/specql_registry/subdomain.yaml`
- [ ] `entities/specql_registry/entity_registration.yaml`
- [ ] Generated PostgreSQL DDL
- [ ] Migration script from YAML to PostgreSQL
- [ ] PostgreSQL repository fully tested

---

### Phase 2-6: Same as Original Plan

*(Pattern Library, Type Registry, Service Registry, CLI, Migration)*

---

## Architecture Benefits

### Before (No Architecture)

```python
# Direct YAML access scattered everywhere
def get_domain():
    with open('registry/domain_registry.yaml') as f:
        data = yaml.load(f)  # Tightly coupled!
        return data['domains']['1']

# Hard to test!
# Hard to change storage!
# Business logic mixed with data access!
```

### After (Repository Pattern + DDD)

```python
# Clean separation
class DomainService:
    def __init__(self, repository: DomainRepository):  # Dependency injection
        self.repository = repository

    def register_domain(self, ...):
        domain = Domain(...)  # Rich domain model
        domain.validate()     # Business logic in entity
        self.repository.save(domain)  # Abstracted storage

# Easy to test with mocks!
# Easy to swap PostgreSQL <-> YAML!
# Business logic in domain entities!
```

---

## Testing Strategy

### Unit Tests (Phase 0)

```python
def test_domain_allocate_code():
    """Test domain entity business logic"""
    domain = Domain(
        domain_number=DomainNumber('1'),
        domain_name='core',
        ...
    )
    subdomain = Subdomain(subdomain_number='1', ...)
    domain.add_subdomain(subdomain)

    code = domain.allocate_entity_code('1', 'Contact')
    assert str(code) == '011101'

def test_domain_service_with_mock_repository():
    """Test service with mock repository"""
    mock_repo = Mock(spec=DomainRepository)
    service = DomainService(mock_repo)

    service.register_domain('1', 'core', ...)
    mock_repo.save.assert_called_once()
```

### Integration Tests (Phase 1+)

```python
def test_postgresql_repository_roundtrip():
    """Test PostgreSQL repository"""
    repo = PostgreSQLDomainRepository(db_url)

    domain = Domain(...)
    repo.save(domain)

    loaded = repo.get('1')
    assert loaded.domain_name == domain.domain_name
```

---

## Migration Path

### Step 1: Implement Architecture (Phase 0)
- Repository pattern
- Domain entities
- Application services
- All using existing YAML backend

### Step 2: Generate PostgreSQL Schema (Phase 1)
- Create SpecQL YAML entities
- Generate DDL
- Create PostgreSQL repository

### Step 3: Dual Repository (Phase 2)
- Write to both YAML and PostgreSQL
- Validate consistency
- Build confidence

### Step 4: Cut-Over (Phase 3)
- Switch primary to PostgreSQL
- Keep YAML as backup
- Monitor performance

### Step 5: Clean-Up (Phase 4)
- Remove YAML repository
- Archive YAML files
- Full PostgreSQL

---

## Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| **Test Coverage** | >90% | Proves architecture works |
| **Repository Swappability** | <1 hour to swap | Proves abstraction works |
| **Performance** | <10ms queries | Proves PostgreSQL works |
| **Code Quality** | Zero direct DB access | Proves separation works |

---

## Next Steps

**STOP and DO Phase 0 FIRST!**

1. ✅ **Revert uncommitted changes** - Clean slate
2. ✅ **Design repository pattern** - Document first
3. ✅ **Design DDD domain model** - Entities and value objects
4. ✅ **Implement base repositories** - Protocols and abstractions
5. ✅ **Implement domain entities** - Rich business logic
6. ✅ **Implement concrete repositories** - YAML, PostgreSQL, InMemory
7. ✅ **Implement application services** - Use case layer
8. ✅ **Update existing code** - Use repositories
9. ✅ **Test everything** - Unit + integration tests
10. ✅ **Then proceed to Phase 1** - Generate PostgreSQL schema

---

**Status**: Architecture-first approach
**Estimated Timeline**: 8 weeks (1 week for Phase 0 + 7 weeks for migration)
**Complexity**: Medium-High (proper architecture takes time, but pays off)
**Risk**: Low (well-architected systems are easier to change)

Let's build it right! 🏗️
