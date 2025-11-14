# FraiseQL Integration for SpecQL Registry

**Date**: 2025-11-12
**Status**: Architecture Design
**Goal**: Use FraiseQL as the presentation layer for SpecQL's PostgreSQL registry

---

## Executive Summary

Instead of building a custom GraphQL API, **leverage the existing FraiseQL framework** (`../fraiseql/`) as the presentation layer for SpecQL's domain registry.

### Why FraiseQL?

✅ **Already exists** - No need to build GraphQL layer from scratch
✅ **Production-ready** - Battle-tested, v1.4.1 stable
✅ **Rust performance** - Zero Python JSON overhead
✅ **PostgreSQL-native** - Perfect match for our PostgreSQL registry
✅ **LLM-friendly** - Simple API that AI can generate
✅ **Dogfooding** - Use our own ecosystem tools

---

## Architecture Integration

### Clean Architecture with FraiseQL

```
┌─────────────────────────────────────────────────────────┐
│              Presentation Layer (FraiseQL)               │
│  GraphQL API - queries, mutations, subscriptions        │
│  └─ FraiseQL Types: Domain, Subdomain, EntityRegistration│
└──────────────────────┬──────────────────────────────────┘
                       │ (calls Application Services)
┌──────────────────────▼──────────────────────────────────┐
│              Application Layer (SpecQL)                  │
│  DomainService, PatternService, TypeService             │
│  └─ Use Cases: register_domain, allocate_code, etc.    │
└──────────────────────┬──────────────────────────────────┘
                       │ (uses Repository Protocol)
┌──────────────────────▼──────────────────────────────────┐
│              Domain Layer (SpecQL)                       │
│  Domain, Subdomain, EntityRegistration (Aggregates)     │
│  DomainNumber, TableCode (Value Objects)                │
│  Business Logic & Validation                            │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│         Infrastructure Layer (SpecQL)                    │
│  PostgreSQLDomainRepository, YAMLDomainRepository       │
│  └─ Data Access & External Systems                     │
└─────────────────────────────────────────────────────────┘
```

### Key Principle: **FraiseQL calls Application Services**

FraiseQL resolvers should be **thin wrappers** that:
1. Parse GraphQL input
2. Call Application Services (DomainService, etc.)
3. Return formatted results

**DO NOT**:
- ❌ Put business logic in resolvers
- ❌ Access repositories directly from FraiseQL
- ❌ Duplicate validation logic

**DO**:
- ✅ Keep resolvers simple (< 10 lines)
- ✅ Call application services
- ✅ Handle GraphQL-specific concerns (context, info)

---

## Implementation Plan

### Phase 0.9: FraiseQL Integration (Week 0.5)

**Prerequisites**: Phase 0.4-0.7 complete (Repositories, Domain, Services)

**Goal**: Expose SpecQL registry via FraiseQL GraphQL API

#### Step 0.9.1: Create FraiseQL Types

**Create**: `src/presentation/fraiseql/types.py`

```python
"""
FraiseQL GraphQL Types for SpecQL Registry

Maps domain entities to GraphQL types
"""
from fraiseql import type
from dataclasses import dataclass

@type(
    sql_source="specql_registry.v_domain",
    jsonb_column="data",
    description="Top-level business domain (crm, catalog, projects)"
)
class Domain:
    """Domain GraphQL type"""
    id: int  # pk_domain
    domain_number: str
    domain_name: str
    description: str | None
    multi_tenant: bool
    aliases: list[str]

    # Computed field
    subdomain_count: int

@type(
    sql_source="specql_registry.v_subdomain",
    jsonb_column="data",
    description="Domain subdivision (crm.customer, catalog.manufacturer)"
)
class Subdomain:
    """Subdomain GraphQL type"""
    id: int  # pk_subdomain
    subdomain_number: str
    subdomain_name: str
    description: str | None
    next_entity_sequence: int
    domain: Domain  # Nested object

@type(
    sql_source="specql_registry.v_entity_registration",
    jsonb_column="data",
    description="Entity registration with 6-digit code"
)
class EntityRegistration:
    """Entity registration GraphQL type"""
    id: int  # pk_entity_registration
    entity_name: str
    table_code: str
    entity_code: str | None
    entity_sequence: int
    assigned_at: str
    subdomain: Subdomain  # Nested object
```

**Why Table Views?**
FraiseQL expects PostgreSQL views with JSONB. SpecQL's generators already create these (`v_domain`, `v_subdomain`, etc.)

#### Step 0.9.2: Create FraiseQL Queries

**Create**: `src/presentation/fraiseql/queries.py`

```python
"""
FraiseQL GraphQL Queries for SpecQL Registry

THIN WRAPPERS - Business logic lives in Application Services
"""
from fraiseql import query
from src.presentation.fraiseql.types import Domain, Subdomain, EntityRegistration
from src.application.services.domain_service import DomainService
from src.infrastructure.repositories.postgresql_domain_repository import PostgreSQLDomainRepository

@query
async def domains(info) -> list[Domain]:
    """
    Query all domains

    Thin wrapper - delegates to application service
    """
    db = info.context["db"]
    # FraiseQL handles the SQL query based on GraphQL selection set
    return await db.find("specql_registry.v_domain")

@query
async def domain(info, domain_number: str) -> Domain | None:
    """Query single domain by number"""
    db = info.context["db"]
    return await db.find_one(
        "specql_registry.v_domain",
        where={"domain_number": domain_number}
    )

@query
async def domain_by_name(info, name_or_alias: str) -> Domain | None:
    """
    Find domain by name or alias

    Uses application service for business logic
    """
    # Get repository from context
    domain_repo = info.context["domain_repository"]
    service = DomainService(domain_repo)

    # Application service handles lookup logic
    domain_entity = service.find_domain(name_or_alias)

    if not domain_entity:
        return None

    # Convert domain entity to GraphQL response
    db = info.context["db"]
    return await db.find_one(
        "specql_registry.v_domain",
        where={"domain_number": domain_entity.domain_number.value}
    )

@query
async def subdomains(info, domain_number: str | None = None) -> list[Subdomain]:
    """Query subdomains, optionally filtered by domain"""
    db = info.context["db"]
    where = {"domain_number": domain_number} if domain_number else {}
    return await db.find("specql_registry.v_subdomain", where=where)

@query
async def entity_registrations(
    info,
    domain_number: str | None = None,
    subdomain_number: str | None = None
) -> list[EntityRegistration]:
    """Query entity registrations with optional filters"""
    db = info.context["db"]
    where = {}
    if domain_number:
        where["domain_number"] = domain_number
    if subdomain_number:
        where["subdomain_number"] = subdomain_number
    return await db.find("specql_registry.v_entity_registration", where=where)
```

#### Step 0.9.3: Create FraiseQL Mutations

**Create**: `src/presentation/fraiseql/mutations.py`

```python
"""
FraiseQL GraphQL Mutations for SpecQL Registry

THIN WRAPPERS - Business logic lives in Domain Entities & Application Services
"""
from fraiseql import mutation, input_type
from src.presentation.fraiseql.types import Domain, EntityRegistration
from src.application.services.domain_service import DomainService

@input_type
class RegisterDomainInput:
    """Input for registering a new domain"""
    domain_number: str
    domain_name: str
    description: str | None = None
    multi_tenant: bool = False
    aliases: list[str] | None = None

@mutation
async def register_domain(info, input: RegisterDomainInput) -> Domain:
    """
    Register a new domain

    Thin wrapper - delegates to application service
    """
    # Get repository from context
    domain_repo = info.context["domain_repository"]
    service = DomainService(domain_repo)

    # Application service handles business logic
    domain_entity = service.register_domain(
        domain_number=input.domain_number,
        domain_name=input.domain_name,
        description=input.description,
        multi_tenant=input.multi_tenant,
        aliases=input.aliases
    )

    # Fetch from database for GraphQL response
    db = info.context["db"]
    return await db.find_one(
        "specql_registry.v_domain",
        where={"domain_number": domain_entity.domain_number.value}
    )

@input_type
class AllocateEntityCodeInput:
    """Input for allocating entity code"""
    domain_name: str
    subdomain_name: str
    entity_name: str

@mutation
async def allocate_entity_code(
    info,
    input: AllocateEntityCodeInput
) -> EntityRegistration:
    """
    Allocate 6-digit code for new entity

    Thin wrapper - delegates to application service
    """
    # Get repository from context
    domain_repo = info.context["domain_repository"]
    service = DomainService(domain_repo)

    # Application service handles business logic (including validation)
    table_code = service.allocate_entity_code(
        domain_name=input.domain_name,
        subdomain_name=input.subdomain_name,
        entity_name=input.entity_name
    )

    # Fetch newly created entity registration
    db = info.context["db"]
    return await db.find_one(
        "specql_registry.v_entity_registration",
        where={"table_code": str(table_code)}
    )
```

#### Step 0.9.4: Create FraiseQL App

**Create**: `src/presentation/fraiseql/app.py`

```python
"""
FraiseQL FastAPI Application for SpecQL Registry

Entry point for GraphQL API
"""
import os
from fraiseql.fastapi import create_fraiseql_app
from src.presentation.fraiseql.types import Domain, Subdomain, EntityRegistration
from src.presentation.fraiseql.queries import (
    domains,
    domain,
    domain_by_name,
    subdomains,
    entity_registrations
)
from src.presentation.fraiseql.mutations import (
    register_domain,
    allocate_entity_code
)
from src.infrastructure.repositories.postgresql_domain_repository import PostgreSQLDomainRepository

# Dependency injection: Create repositories
database_url = os.getenv("DATABASE_URL", "postgresql://localhost/specql")
domain_repository = PostgreSQLDomainRepository(database_url)

# Create FraiseQL app
app = create_fraiseql_app(
    database_url=database_url,
    types=[Domain, Subdomain, EntityRegistration],
    queries=[
        domains,
        domain,
        domain_by_name,
        subdomains,
        entity_registrations
    ],
    mutations=[
        register_domain,
        allocate_entity_code
    ],
    context={
        "domain_repository": domain_repository
        # Add more repositories as needed
    },
    enable_graphiql=True  # GraphQL playground
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Step 0.9.5: Example GraphQL Queries

**Create**: `examples/graphql/registry_queries.graphql`

```graphql
# Query all domains
query GetAllDomains {
  domains {
    id
    domainNumber
    domainName
    description
    multiTenant
    aliases
    subdomainCount
  }
}

# Find domain by name or alias
query FindDomain {
  domainByName(nameOrAlias: "crm") {
    id
    domainNumber
    domainName
    multiTenant
  }
}

# Query subdomains for a domain
query GetSubdomains {
  subdomains(domainNumber: "2") {
    id
    subdomainNumber
    subdomainName
    description
    nextEntitySequence
    domain {
      domainName
    }
  }
}

# Query entity registrations
query GetEntityRegistrations {
  entityRegistrations(
    domainNumber: "2",
    subdomainNumber: "3"
  ) {
    id
    entityName
    tableCode
    entityCode
    assignedAt
    subdomain {
      subdomainName
      domain {
        domainName
      }
    }
  }
}

# Register new domain
mutation RegisterDomain {
  registerDomain(input: {
    domainNumber: "7"
    domainName: "inventory"
    description: "Inventory management"
    multiTenant: true
    aliases: ["stock", "warehouse"]
  }) {
    id
    domainNumber
    domainName
    description
    multiTenant
    aliases
  }
}

# Allocate entity code
mutation AllocateCode {
  allocateEntityCode(input: {
    domainName: "crm"
    subdomainName: "customer"
    entityName: "Lead"
  }) {
    id
    entityName
    tableCode
    entityCode
    assignedAt
    subdomain {
      subdomainName
      domain {
        domainName
      }
    }
  }
}
```

---

## Benefits of FraiseQL Integration

### 1. **Zero Boilerplate**

**Without FraiseQL** (Custom GraphQL):
```python
# Need to write:
- GraphQL schema definitions (SDL)
- Resolver functions
- Type mappers
- Query builders
- Connection handling
- Error handling
- Performance optimization
= ~500-1000 lines of code
```

**With FraiseQL**:
```python
# Just write:
- @type decorators
- @query/@mutation wrappers
- Delegate to services
= ~100-200 lines of code
```

### 2. **Performance**

- ✅ Rust pipeline (no Python JSON overhead)
- ✅ Native PostgreSQL JSONB queries
- ✅ Automatic query optimization based on GraphQL selection set
- ✅ N+1 query prevention built-in

### 3. **Type Safety**

```python
@type(sql_source="v_domain", jsonb_column="data")
class Domain:
    id: int            # Runtime validation
    domain_name: str   # Type hints enforced
```

### 4. **LLM-Friendly**

FraiseQL's API is so simple that LLMs can generate correct code:

```python
# LLM can generate this correctly on first try
@query
async def domains(info) -> list[Domain]:
    db = info.context["db"]
    return await db.find("v_domain")
```

### 5. **Ecosystem Integration**

- FraiseQL is part of the SpecQL ecosystem
- Same PostgreSQL database
- Same conventions (table views, JSONB)
- Same tooling

---

## Testing Strategy

### Unit Tests (Mock Services)

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.presentation.fraiseql.mutations import register_domain
from src.domain.entities.domain import Domain
from src.domain.value_objects import DomainNumber

@pytest.mark.asyncio
async def test_register_domain_mutation():
    """Test register_domain mutation with mock service"""
    # Mock info context
    mock_info = Mock()
    mock_info.context = {
        "domain_repository": Mock(),
        "db": AsyncMock()
    }

    # Mock service response
    domain_entity = Domain(
        domain_number=DomainNumber("7"),
        domain_name="inventory",
        description="Inventory management",
        multi_tenant=True,
        aliases=["stock"]
    )

    # Mock database response
    mock_info.context["db"].find_one.return_value = {
        "id": 7,
        "domain_number": "7",
        "domain_name": "inventory",
        "multi_tenant": True
    }

    # Call mutation
    result = await register_domain(
        mock_info,
        input={
            "domain_number": "7",
            "domain_name": "inventory",
            "multi_tenant": True
        }
    )

    assert result["domain_name"] == "inventory"
```

### Integration Tests (Real FraiseQL)

```python
import pytest
from httpx import AsyncClient
from src.presentation.fraiseql.app import app

@pytest.mark.asyncio
async def test_graphql_query_domains():
    """Test GraphQL query with real FraiseQL app"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            json={
                "query": """
                    query {
                        domains {
                            domainNumber
                            domainName
                            multiTenant
                        }
                    }
                """
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "domains" in data["data"]
        assert len(data["data"]["domains"]) > 0
```

---

## Running the GraphQL API

### Development

```bash
# Start FraiseQL API server
cd src/presentation/fraiseql
python app.py

# Or with uvicorn hot reload
uvicorn src.presentation.fraiseql.app:app --reload --port 8000
```

### GraphQL Playground

Navigate to: `http://localhost:8000/graphql`

Interactive playground with:
- Schema explorer
- Query autocompletion
- Documentation
- Query history

### Production

```bash
# With gunicorn (production ASGI server)
gunicorn src.presentation.fraiseql.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## File Structure

```
src/
├── presentation/              # NEW: Presentation layer
│   └── fraiseql/
│       ├── __init__.py
│       ├── app.py            # FraiseQL FastAPI app
│       ├── types.py          # GraphQL types (Domain, Subdomain, etc.)
│       ├── queries.py        # GraphQL queries
│       ├── mutations.py      # GraphQL mutations
│       └── context.py        # Context setup (repositories)
│
├── application/              # Application services
│   └── services/
│       ├── domain_service.py
│       └── pattern_service.py
│
├── domain/                   # Domain entities & logic
│   ├── entities/
│   │   └── domain.py
│   ├── value_objects/
│   │   └── __init__.py
│   └── repositories/         # Repository protocols
│       └── domain_repository.py
│
└── infrastructure/           # Infrastructure implementations
    └── repositories/
        ├── postgresql_domain_repository.py
        └── yaml_domain_repository.py

examples/
└── graphql/
    └── registry_queries.graphql  # Example queries

tests/
├── unit/
│   └── presentation/
│       └── test_fraiseql_mutations.py
└── integration/
    └── test_fraiseql_api.py
```

---

## Deliverables (Phase 0.9)

- [ ] `src/presentation/fraiseql/types.py` - GraphQL types
- [ ] `src/presentation/fraiseql/queries.py` - Query resolvers
- [ ] `src/presentation/fraiseql/mutations.py` - Mutation resolvers
- [ ] `src/presentation/fraiseql/app.py` - FraiseQL app
- [ ] `examples/graphql/registry_queries.graphql` - Example queries
- [ ] Unit tests for resolvers (mock services)
- [ ] Integration tests for GraphQL API
- [ ] Documentation in `docs/api/GRAPHQL.md`

---

## Success Criteria

| Metric | Target | Why |
|--------|--------|-----|
| **Resolver Complexity** | <10 lines each | Proves thin wrapper pattern |
| **API Response Time** | <50ms | Proves Rust performance |
| **Test Coverage** | >90% | Proves testability |
| **LLM Code Quality** | First-try success | Proves simplicity |

---

## Next Steps

1. ✅ Complete Phase 0.4-0.7 (Repositories, Domain, Services)
2. ✅ Implement Phase 0.9.1 (FraiseQL types)
3. ✅ Implement Phase 0.9.2 (FraiseQL queries)
4. ✅ Implement Phase 0.9.3 (FraiseQL mutations)
5. ✅ Implement Phase 0.9.4 (FraiseQL app)
6. ✅ Test GraphQL API
7. ✅ Document API usage

---

**Status**: Architecture design complete
**Integration Level**: Presentation layer only (Clean Architecture preserved)
**Complexity**: Low (FraiseQL does the heavy lifting)
**Risk**: Very low (production-ready framework)

Let's use FraiseQL! 🍓
