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