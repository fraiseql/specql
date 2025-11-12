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

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """Find domain by name or alias"""
        ...

    def save(self, domain: Domain) -> None:
        """Save domain (insert or update)"""
        ...

    def list_all(self) -> list[Domain]:
        """List all domains"""
        ...
```