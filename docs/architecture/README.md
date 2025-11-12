# SpecQL Architecture Documentation

**Date**: 2025-11-12
**Status**: Architecture Complete - Ready for Implementation

---

## Overview

This directory contains the complete architecture documentation for SpecQL's PostgreSQL migration using Clean Architecture, DDD, and dual interface design.

---

## Architecture Documents

### 1. [REPOSITORY_PATTERN.md](./REPOSITORY_PATTERN.md) (To Be Created)
**Phase 0.2**

Repository pattern design for abstracting data access:
- Repository protocols (abstract interfaces)
- Concrete implementations (PostgreSQL, YAML, InMemory)
- Dependency injection
- Testing with mocks

### 2. [DDD_DOMAIN_MODEL.md](./DDD_DOMAIN_MODEL.md) (To Be Created)
**Phase 0.3**

Domain-Driven Design for SpecQL:
- Bounded contexts (Registry, Pattern, Type, Service)
- Aggregates (Domain, Subdomain, EntityRegistration)
- Entities vs Value Objects
- Domain logic placement
- Layered architecture

### 3. [FRAISEQL_INTEGRATION.md](./FRAISEQL_INTEGRATION.md) ✅
**Phase 0.9 - Part 1**

FraiseQL as GraphQL presentation layer:
- Using ../fraiseql/ framework
- Thin wrapper resolvers (<10 lines)
- Delegates to Application Services
- GraphQL types from domain entities
- Example queries and mutations

### 4. [DUAL_INTERFACE_ARCHITECTURE.md](./DUAL_INTERFACE_ARCHITECTURE.md) ✅
**Phase 0.9 - Complete**

CLI + GraphQL dual interface design:
- Why both interfaces
- Shared Application Services
- Zero duplication principle
- When to use each interface
- Side-by-side comparisons
- Testing strategy

---

## Quick Reference

### Complete Architecture Stack

```
┌─────────────────────────────────────────────────────┐
│          Presentation Layer (2 Interfaces)          │
│                                                      │
│  ┌──────────────────┐   ┌──────────────────────┐   │
│  │  CLI (Click)     │   │  GraphQL (FraiseQL)  │   │
│  │  - specql cmd    │   │  - /graphql endpoint │   │
│  │  - Developer UX  │   │  - Web/Mobile apps   │   │
│  └────────┬─────────┘   └─────────┬────────────┘   │
└───────────┼───────────────────────┼─────────────────┘
            │                       │
            └──────────┬────────────┘
                       │ Both call same services
┌──────────────────────▼──────────────────────────────┐
│            Application Layer (Services)              │
│  - DomainService, PatternService, TypeService       │
│  - Business logic orchestration                     │
│  - Use case implementations                         │
└──────────────────────┬──────────────────────────────┘
                       │ Uses Repository Protocol
┌──────────────────────▼──────────────────────────────┐
│            Domain Layer (Business Logic)             │
│  - Entities: Domain, Subdomain, Pattern             │
│  - Value Objects: DomainNumber, TableCode           │
│  - Business rules and validation                    │
└──────────────────────┬──────────────────────────────┘
                       │ Persisted by
┌──────────────────────▼──────────────────────────────┐
│         Infrastructure Layer (Data Access)           │
│  - PostgreSQLDomainRepository                       │
│  - YAMLDomainRepository (legacy)                    │
│  - InMemoryDomainRepository (testing)               │
└─────────────────────────────────────────────────────┘
```

### Key Principles

1. **Clean Architecture**: Separation of concerns, dependency inversion
2. **Repository Pattern**: Abstract data access, testable with mocks
3. **DDD**: Rich domain model, business logic in entities
4. **Thin Wrappers**: Presentation layers stay simple (<10 lines)
5. **Zero Duplication**: Shared Application Services for all interfaces
6. **Dependency Injection**: Services receive dependencies via constructor

### File Structure

```
src/
├── presentation/               # Presentation Layer
│   ├── cli/                    # CLI interface
│   └── fraiseql/               # GraphQL interface
│
├── application/                # Application Layer
│   └── services/               # Business logic orchestration
│
├── domain/                     # Domain Layer
│   ├── entities/               # Aggregates and entities
│   ├── value_objects/          # Immutable value objects
│   └── repositories/           # Repository protocols
│
└── infrastructure/             # Infrastructure Layer
    └── repositories/           # Repository implementations
```

### Example: Same Service, Two Interfaces

**Shared Service**:
```python
class DomainService:
    def allocate_entity_code(self, domain: str, subdomain: str, entity: str) -> TableCode:
        # Business logic here
        return code
```

**CLI Interface**:
```bash
specql registry allocate-code --domain=crm --subdomain=customer --entity=Lead
```

**GraphQL Interface**:
```graphql
mutation {
  allocateEntityCode(input: {
    domainName: "crm"
    subdomainName: "customer"
    entityName: "Lead"
  }) { tableCode }
}
```

---

## Implementation Phases

### Phase 0: Architecture Foundation (Week 0)

**Status**: Design Complete, Implementation Pending

#### Steps:
1. ✅ Revert working directory
2. ⏳ Create REPOSITORY_PATTERN.md
3. ⏳ Create DDD_DOMAIN_MODEL.md
4. ⏳ Implement base Repository protocols
5. ⏳ Implement domain entities and value objects
6. ⏳ Implement concrete repositories (PostgreSQL, YAML, InMemory)
7. ⏳ Implement application services
8. ⏳ Update existing code to use repositories
9. ⏳ Implement dual presentation layer (CLI + FraiseQL)

**Deliverables**:
- Complete repository pattern implementation
- Complete DDD domain model
- Both CLI and GraphQL working
- >90% test coverage
- All unit and integration tests passing

### Phase 1+: PostgreSQL Migration (Weeks 1-7)

See: `docs/implementation_plans/SPECQL_POSTGRESQL_BOOTSTRAP.md`

---

## Benefits Summary

### Technical Benefits

✅ **Testable**: Mock repositories, easy unit tests
✅ **Maintainable**: Business logic in one place
✅ **Flexible**: Easy to swap implementations
✅ **Scalable**: Add new interfaces easily
✅ **Type-safe**: Rich domain model with validation

### User Benefits

✅ **CLI for developers**: Fast, local, scriptable
✅ **GraphQL for apps**: Rich queries, remote access
✅ **Consistent**: Same logic, same results
✅ **Reliable**: Comprehensive test coverage
✅ **Dogfooding**: We use what we build (FraiseQL + SpecQL)

### Business Benefits

✅ **Faster development**: Shared services
✅ **Lower maintenance**: Single source of truth
✅ **Better quality**: Layered architecture, tests
✅ **Future-proof**: Easy to extend
✅ **Confidence**: Architecture-first approach

---

## Next Steps

1. **Review Architecture** - Stakeholder sign-off
2. **Start Phase 0** - Begin implementation
3. **TDD Approach** - RED → GREEN → REFACTOR → QA
4. **Incremental Delivery** - Complete one step at a time
5. **Continuous Testing** - Tests at every step

---

## Related Documents

- `docs/implementation_plans/SPECQL_POSTGRESQL_BOOTSTRAP.md` - Complete migration plan
- `.claude/CLAUDE.md` - Development methodology (TDD)
- `docs/architecture/INTEGRATION_PROPOSAL.md` - Original integration proposal

---

**Questions?** Review the individual architecture documents for detailed implementation guidance.

**Ready to implement?** Start with Phase 0.1: Revert working directory to clean state.

---

*Architecture First. Quality Built In. Dogfooding FTW.* 🏗️ 🍓
