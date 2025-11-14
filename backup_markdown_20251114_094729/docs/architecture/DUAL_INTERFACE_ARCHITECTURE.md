# Dual Interface Architecture: CLI + GraphQL

**Date**: 2025-11-12
**Status**: Architecture Design
**Goal**: Provide both CLI and GraphQL interfaces to SpecQL registry, sharing the same application services

---

## Executive Summary

SpecQL will provide **two presentation interfaces** for the same underlying functionality:

1. **CLI (Command Line Interface)** - For developers, scripts, CI/CD
2. **GraphQL API (FraiseQL)** - For web apps, integrations, external services

**Key Principle**: **Both interfaces are thin wrappers** that call the same Application Services. Zero duplication of business logic.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                           │
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐   │
│  │   CLI Interface          │  │   GraphQL Interface       │   │
│  │   (Click framework)      │  │   (FraiseQL)              │   │
│  │                          │  │                           │   │
│  │  specql registry list    │  │  query { domains { } }    │   │
│  │  specql patterns search  │  │  mutation { register... } │   │
│  │  specql generate ...     │  │  /graphql endpoint        │   │
│  │                          │  │  GraphiQL playground      │   │
│  └────────────┬─────────────┘  └────────────┬─────────────┘   │
└───────────────┼──────────────────────────────┼─────────────────┘
                │                              │
                │    Both call same services   │
                │                              │
                └──────────┬───────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Application Layer                           │
│  (Use Cases - Business Logic Orchestration)                 │
│                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ Domain       │ │ Pattern      │ │ Generation       │   │
│  │ Service      │ │ Service      │ │ Service          │   │
│  └──────────────┘ └──────────────┘ └──────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Domain Layer                               │
│  (Business Entities, Value Objects, Domain Logic)           │
│                                                              │
│  Domain, Subdomain, EntityRegistration (Aggregates)         │
│  DomainNumber, TableCode (Value Objects)                    │
│  Validation, Business Rules                                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               Infrastructure Layer                           │
│  (Data Access, External Systems)                            │
│                                                              │
│  PostgreSQLDomainRepository, YAMLDomainRepository           │
│  InMemoryDomainRepository (for tests)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Interface Comparison

### CLI Interface

**Purpose**: Developer-friendly commands for local development and automation

**Features**:
- ✅ Fast local execution (no server needed)
- ✅ Shell integration (pipes, scripting)
- ✅ Colored output, progress bars
- ✅ Tab completion
- ✅ Environment variable support
- ✅ Exit codes for scripting

**Use Cases**:
- Developer workflow
- CI/CD pipelines
- Database migrations
- Code generation
- Admin tasks
- Quick queries

**Example Commands**:
```bash
# Domain registry
specql registry list-domains
specql registry show-domain crm --verbose
specql registry allocate-code --domain=crm --subdomain=customer --entity=Lead

# Pattern library
specql patterns list --category=workflow
specql patterns search "approval workflow" --limit=10
specql patterns register --file=patterns/approval.yaml

# Code generation
specql generate entities/contact.yaml --output=db/schema/
specql generate entities/*.yaml --hierarchical

# Database operations
specql db migrate
specql db seed --pattern-library
specql db validate

# Dev tools
specql validate entities/*.yaml
specql diff entities/contact.yaml --compare=db/schema/contact.sql
```

### GraphQL Interface

**Purpose**: API for web applications, mobile apps, and external integrations

**Features**:
- ✅ HTTP-based (remote access)
- ✅ Rich nested queries
- ✅ Type safety
- ✅ GraphiQL playground
- ✅ Subscriptions (future)
- ✅ Batching, caching

**Use Cases**:
- Web dashboard
- Mobile applications
- External integrations
- Complex queries
- Real-time updates
- Multi-user access

**Example Queries**:
```graphql
# Query domains with nested data
query GetDomains {
  domains {
    id
    domainName
    multiTenant
    subdomains {
      subdomainName
      entities {
        entityName
        tableCode
      }
    }
  }
}

# Search patterns
query SearchPatterns {
  searchPatterns(query: "approval workflow", limit: 10) {
    patternName
    patternCategory
    description
    distance
  }
}

# Allocate entity code
mutation AllocateCode {
  allocateEntityCode(input: {
    domainName: "crm"
    subdomainName: "customer"
    entityName: "Lead"
  }) {
    tableCode
    entityName
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

## Implementation: Shared Application Services

### Application Service (Shared)

**File**: `src/application/services/domain_service.py`

```python
"""
Domain Service - Application Layer

SHARED by both CLI and GraphQL interfaces
Contains business logic orchestration
"""
from src.domain.repositories.domain_repository import DomainRepository
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber, TableCode

class DomainService:
    """
    Application Service for Domain operations

    This service is called by BOTH CLI and GraphQL interfaces
    """

    def __init__(self, repository: DomainRepository):
        self.repository = repository

    def list_domains(self) -> list[Domain]:
        """List all domains - called by both CLI and GraphQL"""
        return self.repository.list_all()

    def get_domain(self, domain_number: str) -> Domain:
        """Get domain by number - called by both CLI and GraphQL"""
        return self.repository.get(domain_number)

    def find_domain(self, name_or_alias: str) -> Domain | None:
        """Find domain by name or alias - called by both CLI and GraphQL"""
        return self.repository.find_by_name(name_or_alias)

    def register_domain(
        self,
        domain_number: str,
        domain_name: str,
        description: str | None,
        multi_tenant: bool,
        aliases: list[str] | None = None
    ) -> Domain:
        """
        Register new domain

        Business logic:
        1. Validate domain number (1-9)
        2. Check uniqueness
        3. Create domain entity
        4. Save via repository

        Called by both CLI and GraphQL
        """
        # Validate domain number
        domain_num = DomainNumber(domain_number)  # Raises if invalid

        # Check if domain already exists
        existing = self.repository.find_by_name(domain_name)
        if existing:
            raise ValueError(f"Domain {domain_name} already exists")

        # Create domain entity (domain logic validates)
        domain = Domain(
            domain_number=domain_num,
            domain_name=domain_name,
            description=description,
            multi_tenant=multi_tenant,
            aliases=aliases or []
        )

        # Save via repository
        self.repository.save(domain)

        return domain

    def allocate_entity_code(
        self,
        domain_name: str,
        subdomain_name: str,
        entity_name: str
    ) -> TableCode:
        """
        Allocate 6-digit code for entity

        Business logic:
        1. Find domain
        2. Find subdomain
        3. Allocate code (domain entity logic)
        4. Save updated domain

        Called by both CLI and GraphQL
        """
        # Find domain
        domain = self.repository.find_by_name(domain_name)
        if not domain:
            raise ValueError(f"Domain {domain_name} not found")

        # Find subdomain (business logic in domain entity)
        subdomain = None
        for sd in domain.subdomains.values():
            if sd.subdomain_name == subdomain_name:
                subdomain = sd
                break

        if not subdomain:
            raise ValueError(f"Subdomain {subdomain_name} not found in {domain_name}")

        # Allocate code (business logic in subdomain entity)
        code = subdomain.allocate_next_code(entity_name)

        # Save updated domain (increments next_entity_sequence)
        self.repository.save(domain)

        return code
```

---

## CLI Implementation

### CLI Entry Point

**File**: `src/presentation/cli/main.py`

```python
"""
SpecQL CLI - Entry Point

Thin wrapper around Application Services
"""
import click
from pathlib import Path
from src.application.services.domain_service import DomainService
from src.infrastructure.repositories.yaml_domain_repository import YAMLDomainRepository

# Dependency injection - create repositories
def get_domain_service() -> DomainService:
    """Create domain service with repository"""
    repo = YAMLDomainRepository(Path('registry/domain_registry.yaml'))
    return DomainService(repo)

@click.group()
def cli():
    """SpecQL - Business YAML → Production PostgreSQL"""
    pass

# Registry commands
@cli.group()
def registry():
    """Domain registry commands"""
    pass

@registry.command('list-domains')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def list_domains(verbose):
    """List all domains"""
    service = get_domain_service()

    try:
        domains = service.list_domains()

        if not domains:
            click.echo("No domains found")
            return

        click.echo(f"Found {len(domains)} domain(s):\n")

        for domain in domains:
            if verbose:
                click.echo(f"  {domain.domain_number.value}. {domain.domain_name}")
                click.echo(f"     Description: {domain.description or 'N/A'}")
                click.echo(f"     Multi-tenant: {domain.multi_tenant}")
                click.echo(f"     Aliases: {', '.join(domain.aliases) if domain.aliases else 'None'}")
                click.echo(f"     Subdomains: {len(domain.subdomains)}")
                click.echo()
            else:
                click.echo(f"  {domain.domain_number.value}. {domain.domain_name} "
                          f"({'multi-tenant' if domain.multi_tenant else 'shared'})")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

@registry.command('show-domain')
@click.argument('domain_name')
def show_domain(domain_name):
    """Show domain details"""
    service = get_domain_service()

    try:
        domain = service.find_domain(domain_name)

        if not domain:
            click.echo(f"❌ Domain '{domain_name}' not found", err=True)
            raise click.Abort()

        click.echo(f"\n📋 Domain: {domain.domain_name}")
        click.echo(f"   Number: {domain.domain_number.value}")
        click.echo(f"   Description: {domain.description or 'N/A'}")
        click.echo(f"   Multi-tenant: {domain.multi_tenant}")
        click.echo(f"   Aliases: {', '.join(domain.aliases) if domain.aliases else 'None'}")
        click.echo(f"\n   Subdomains ({len(domain.subdomains)}):")

        for subdomain in domain.subdomains.values():
            click.echo(f"     {subdomain.subdomain_number}. {subdomain.subdomain_name}")
            click.echo(f"        Entities: {len(subdomain.entities)}")
            click.echo(f"        Next sequence: {subdomain.next_entity_sequence}")

        click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

@registry.command('allocate-code')
@click.option('--domain', required=True, help='Domain name (e.g., crm)')
@click.option('--subdomain', required=True, help='Subdomain name (e.g., customer)')
@click.option('--entity', required=True, help='Entity name (e.g., Lead)')
def allocate_code(domain, subdomain, entity):
    """Allocate 6-digit code for new entity"""
    service = get_domain_service()

    try:
        # Call application service (same as GraphQL!)
        code = service.allocate_entity_code(domain, subdomain, entity)

        click.echo(f"\n✅ Allocated code: {code}")
        click.echo(f"   Domain: {domain}")
        click.echo(f"   Subdomain: {subdomain}")
        click.echo(f"   Entity: {entity}\n")

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

@registry.command('register-domain')
@click.option('--number', required=True, help='Domain number (1-9)')
@click.option('--name', required=True, help='Domain name (e.g., inventory)')
@click.option('--description', help='Domain description')
@click.option('--multi-tenant', is_flag=True, help='Multi-tenant domain')
@click.option('--alias', multiple=True, help='Domain aliases (can be repeated)')
def register_domain_cmd(number, name, description, multi_tenant, alias):
    """Register new domain"""
    service = get_domain_service()

    try:
        # Call application service (same as GraphQL!)
        domain = service.register_domain(
            domain_number=number,
            domain_name=name,
            description=description,
            multi_tenant=multi_tenant,
            aliases=list(alias) if alias else None
        )

        click.echo(f"\n✅ Registered domain: {domain.domain_name}")
        click.echo(f"   Number: {domain.domain_number.value}")
        click.echo(f"   Multi-tenant: {domain.multi_tenant}")
        if alias:
            click.echo(f"   Aliases: {', '.join(alias)}")
        click.echo()

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

# Pattern commands
@cli.group()
def patterns():
    """Pattern library commands"""
    pass

@patterns.command('list')
@click.option('--category', help='Filter by category')
def list_patterns(category):
    """List domain patterns"""
    # TODO: Implement PatternService
    click.echo("Pattern library commands coming soon...")

# Generate commands
@cli.group()
def generate():
    """Code generation commands"""
    pass

@generate.command('entity')
@click.argument('yaml_file', type=click.Path(exists=True))
@click.option('--output', type=click.Path(), help='Output directory')
@click.option('--hierarchical', is_flag=True, help='Use hierarchical file structure')
def generate_entity(yaml_file, output, hierarchical):
    """Generate PostgreSQL code from entity YAML"""
    # TODO: Implement GenerationService
    click.echo(f"Generating from {yaml_file}...")

if __name__ == '__main__':
    cli()
```

### CLI Usage Examples

```bash
# List domains
$ specql registry list-domains
Found 6 domain(s):

  1. core (shared)
  2. crm (multi-tenant)
  3. catalog (shared)
  4. projects (multi-tenant)
  5. analytics (shared)
  6. finance (shared)

# Show domain details
$ specql registry show-domain crm

📋 Domain: crm
   Number: 2
   Description: Customer relationship management & organizational structure
   Multi-tenant: True
   Aliases: management

   Subdomains (5):
     1. core
        Entities: 0
        Next sequence: 1
     3. customer
        Entities: 1
        Next sequence: 59

# Allocate code
$ specql registry allocate-code --domain=crm --subdomain=customer --entity=Lead

✅ Allocated code: 012059
   Domain: crm
   Subdomain: customer
   Entity: Lead

# Register new domain
$ specql registry register-domain \
    --number=7 \
    --name=inventory \
    --description="Inventory management" \
    --multi-tenant \
    --alias=stock \
    --alias=warehouse

✅ Registered domain: inventory
   Number: 7
   Multi-tenant: True
   Aliases: stock, warehouse

# Use in scripts
$ if specql registry show-domain crm > /dev/null 2>&1; then
    echo "CRM domain exists"
  fi

# Pipeline usage
$ specql registry list-domains | grep multi-tenant
```

---

## GraphQL Implementation

### GraphQL Resolvers

**File**: `src/presentation/fraiseql/queries.py`

```python
"""
FraiseQL GraphQL Queries

THIN WRAPPERS - Delegate to Application Services
"""
from fraiseql import query
from src.presentation.fraiseql.types import Domain, Subdomain
from src.application.services.domain_service import DomainService

@query
async def domains(info) -> list[Domain]:
    """
    Query all domains

    Thin wrapper - FraiseQL handles SQL query
    """
    db = info.context["db"]
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

    Uses application service (same as CLI!)
    """
    # Get service from context
    domain_service: DomainService = info.context["domain_service"]

    # Call application service (SAME AS CLI!)
    domain_entity = domain_service.find_domain(name_or_alias)

    if not domain_entity:
        return None

    # Convert to GraphQL response
    db = info.context["db"]
    return await db.find_one(
        "specql_registry.v_domain",
        where={"domain_number": domain_entity.domain_number.value}
    )
```

**File**: `src/presentation/fraiseql/mutations.py`

```python
"""
FraiseQL GraphQL Mutations

THIN WRAPPERS - Delegate to Application Services
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
    Register new domain

    Thin wrapper - delegates to application service (SAME AS CLI!)
    """
    # Get service from context
    domain_service: DomainService = info.context["domain_service"]

    # Call application service (SAME AS CLI!)
    domain_entity = domain_service.register_domain(
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

    Thin wrapper - delegates to application service (SAME AS CLI!)
    """
    # Get service from context
    domain_service: DomainService = info.context["domain_service"]

    # Call application service (SAME AS CLI!)
    table_code = domain_service.allocate_entity_code(
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

### GraphQL App with Context

**File**: `src/presentation/fraiseql/app.py`

```python
"""
FraiseQL FastAPI Application

Provides GraphQL API with dependency injection
"""
import os
from fraiseql.fastapi import create_fraiseql_app
from src.presentation.fraiseql.types import Domain, Subdomain, EntityRegistration
from src.presentation.fraiseql.queries import domains, domain, domain_by_name
from src.presentation.fraiseql.mutations import register_domain, allocate_entity_code

# Dependency Injection - Create services
from src.application.services.domain_service import DomainService
from src.infrastructure.repositories.postgresql_domain_repository import PostgreSQLDomainRepository

database_url = os.getenv("DATABASE_URL", "postgresql://localhost/specql")
domain_repository = PostgreSQLDomainRepository(database_url)
domain_service = DomainService(domain_repository)

# Create FraiseQL app
app = create_fraiseql_app(
    database_url=database_url,
    types=[Domain, Subdomain, EntityRegistration],
    queries=[domains, domain, domain_by_name],
    mutations=[register_domain, allocate_entity_code],
    context={
        # Inject services - available to all resolvers
        "domain_service": domain_service,
        "domain_repository": domain_repository
    },
    enable_graphiql=True
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Side-by-Side Comparison

### Same Operation, Two Interfaces

**CLI**:
```bash
$ specql registry allocate-code \
    --domain=crm \
    --subdomain=customer \
    --entity=Lead

✅ Allocated code: 012059
   Domain: crm
   Subdomain: customer
   Entity: Lead
```

**GraphQL**:
```graphql
mutation {
  allocateEntityCode(input: {
    domainName: "crm"
    subdomainName: "customer"
    entityName: "Lead"
  }) {
    tableCode       # "012059"
    entityName      # "Lead"
    subdomain {
      subdomainName # "customer"
      domain {
        domainName  # "crm"
      }
    }
  }
}
```

**Both call**:
```python
domain_service.allocate_entity_code("crm", "customer", "Lead")
```

---

## Testing Strategy

### Unit Tests (Mock Services)

**Test CLI**:
```python
from click.testing import CliRunner
from unittest.mock import Mock
from src.presentation.cli.main import cli
from src.domain.value_objects import TableCode

def test_cli_allocate_code():
    """Test CLI allocate-code command with mock service"""
    runner = CliRunner()

    # Mock service
    mock_service = Mock()
    mock_service.allocate_entity_code.return_value = TableCode("012059")

    # Inject mock (monkeypatch)
    with patch('src.presentation.cli.main.get_domain_service', return_value=mock_service):
        result = runner.invoke(cli, [
            'registry', 'allocate-code',
            '--domain', 'crm',
            '--subdomain', 'customer',
            '--entity', 'Lead'
        ])

    assert result.exit_code == 0
    assert "012059" in result.output
    mock_service.allocate_entity_code.assert_called_once_with('crm', 'customer', 'Lead')
```

**Test GraphQL**:
```python
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock
from src.presentation.fraiseql.app import app

@pytest.mark.asyncio
async def test_graphql_allocate_code():
    """Test GraphQL allocate_entity_code mutation with mock service"""
    # Mock service
    mock_service = Mock()
    mock_service.allocate_entity_code.return_value = TableCode("012059")

    # Override context
    app.context["domain_service"] = mock_service

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/graphql", json={
            "query": """
                mutation {
                    allocateEntityCode(input: {
                        domainName: "crm"
                        subdomainName: "customer"
                        entityName: "Lead"
                    }) {
                        tableCode
                        entityName
                    }
                }
            """
        })

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["allocateEntityCode"]["tableCode"] == "012059"
    mock_service.allocate_entity_code.assert_called_once_with('crm', 'customer', 'Lead')
```

**Same Service Tested Twice** - Different interfaces, same logic!

### Integration Tests (Real Services)

```python
def test_integration_cli_and_graphql_consistency():
    """Ensure CLI and GraphQL return same results"""
    # Use real repository (in-memory for testing)
    from src.infrastructure.repositories.in_memory_domain_repository import InMemoryDomainRepository

    repo = InMemoryDomainRepository()
    service = DomainService(repo)

    # Register domain via service
    domain = service.register_domain("7", "inventory", "Inventory", True)

    # Query via CLI
    runner = CliRunner()
    cli_result = runner.invoke(cli, ['registry', 'show-domain', 'inventory'])

    # Query via GraphQL
    # ... GraphQL query ...

    # Both should return same data
    assert "inventory" in cli_result.output
    assert graphql_result["domainName"] == "inventory"
```

---

## File Structure

```
src/
├── presentation/                    # Presentation Layer (2 interfaces)
│   ├── cli/                         # CLI interface
│   │   ├── __init__.py
│   │   ├── main.py                  # Entry point (specql command)
│   │   ├── registry.py              # Registry commands
│   │   ├── patterns.py              # Pattern commands
│   │   ├── generate.py              # Generate commands
│   │   └── db.py                    # Database commands
│   │
│   └── fraiseql/                    # GraphQL interface
│       ├── __init__.py
│       ├── app.py                   # FraiseQL app
│       ├── types.py                 # GraphQL types
│       ├── queries.py               # Query resolvers
│       ├── mutations.py             # Mutation resolvers
│       └── subscriptions.py         # Subscriptions (future)
│
├── application/                     # SHARED Application Layer
│   └── services/
│       ├── __init__.py
│       ├── domain_service.py        # Called by both CLI & GraphQL
│       ├── pattern_service.py       # Called by both CLI & GraphQL
│       ├── type_service.py          # Called by both CLI & GraphQL
│       └── generation_service.py    # Called by both CLI & GraphQL
│
├── domain/                          # SHARED Domain Layer
│   ├── entities/
│   │   ├── __init__.py
│   │   └── domain.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   └── domain_number.py
│   └── repositories/                # Repository protocols
│       ├── __init__.py
│       └── domain_repository.py
│
└── infrastructure/                  # SHARED Infrastructure Layer
    └── repositories/
        ├── __init__.py
        ├── postgresql_domain_repository.py
        ├── yaml_domain_repository.py
        └── in_memory_domain_repository.py

tests/
├── unit/
│   ├── presentation/
│   │   ├── test_cli_commands.py     # Unit tests for CLI
│   │   └── test_graphql_resolvers.py # Unit tests for GraphQL
│   ├── application/
│   │   └── test_services.py         # Service tests (used by both)
│   └── domain/
│       └── test_entities.py
│
└── integration/
    ├── test_cli_integration.py      # Full CLI integration
    ├── test_graphql_integration.py  # Full GraphQL integration
    └── test_interface_consistency.py # CLI vs GraphQL consistency
```

---

## When to Use Each Interface

| Scenario | CLI | GraphQL | Why |
|----------|-----|---------|-----|
| **Local development** | ✅ | ❌ | No server needed, fast |
| **CI/CD pipeline** | ✅ | ❌ | Shell scripting, exit codes |
| **Quick admin task** | ✅ | ❌ | One command, done |
| **Generate SQL files** | ✅ | ❌ | File operations |
| **Web dashboard** | ❌ | ✅ | Rich UI, nested data |
| **Mobile app** | ❌ | ✅ | HTTP-based |
| **External integration** | ❌ | ✅ | Standard API |
| **Complex query** | ❌ | ✅ | Filtering, relations |
| **Real-time updates** | ❌ | ✅ | Subscriptions |
| **Shell script** | ✅ | ❌ | Pipes, variables |
| **Database migration** | ✅ | ❌ | Direct file access |
| **Pattern discovery** | ✅ | ❌ | File system access |

---

## Benefits of Dual Interface

### 1. **Zero Duplication**

- ✅ Business logic lives in Application Services
- ✅ Both interfaces call same services
- ✅ Fix bug once, fixed everywhere
- ✅ Add feature once, available in both

### 2. **Best Tool for Job**

- ✅ CLI for developers (fast, local)
- ✅ GraphQL for apps (rich, remote)
- ✅ Users choose what works best

### 3. **Testing Confidence**

- ✅ Test services once
- ✅ Test each interface separately
- ✅ Test consistency between interfaces

### 4. **Future Flexibility**

Easy to add more interfaces later:
- REST API
- gRPC
- WebSockets
- Desktop GUI

All would call the same Application Services!

---

## Updated Phase 0.9

**Phase 0.9: Dual Presentation Layer (Week 0.5)**

**Prerequisites**: Phase 0.4-0.7 complete (Repositories, Domain, Services)

#### Step 0.9.1: Refactor Existing CLI

- Move CLI logic to Application Services
- Update CLI commands to call services (thin wrappers)
- Ensure backward compatibility
- Add tests

#### Step 0.9.2: Create FraiseQL Types

- Define GraphQL types from domain entities
- Map to PostgreSQL table views

#### Step 0.9.3: Create FraiseQL Queries

- Thin wrappers calling Application Services
- Delegate complex logic to services

#### Step 0.9.4: Create FraiseQL Mutations

- Thin wrappers calling Application Services
- Same validation as CLI

#### Step 0.9.5: Create FraiseQL App

- FastAPI + FraiseQL integration
- Dependency injection (services in context)
- GraphiQL playground

#### Step 0.9.6: Integration Tests

- Test CLI commands
- Test GraphQL queries/mutations
- **Test consistency** (CLI vs GraphQL return same data)

**Deliverables**:
- [ ] Refactored CLI using Application Services
- [ ] FraiseQL GraphQL API
- [ ] Both interfaces tested
- [ ] Consistency tests passing
- [ ] Documentation for both interfaces

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Logic Duplication** | 0% | All logic in services |
| **CLI Test Coverage** | >90% | pytest --cov |
| **GraphQL Test Coverage** | >90% | pytest --cov |
| **Consistency** | 100% | CLI == GraphQL results |
| **Resolver Complexity** | <10 lines | Code review |

---

**Status**: Architecture design complete
**Interfaces**: CLI (Click) + GraphQL (FraiseQL)
**Shared Layer**: Application Services
**Principle**: Thin wrappers, zero duplication

Let's build both interfaces! 🚀 🍓
