# Transaction Management Strategy

**Date**: 2025-11-12
**Status**: Implemented and Documented
**Decision**: Repositories Manage Transactions

---

## Executive Summary

**Decision**: Repositories manage their own transactions using psycopg context managers. Services coordinate repository calls but don't manage transactions directly.

**Rationale**: 99% of use cases involve single-repository operations. For the rare 1% that need multi-repository transactions, we'll implement Unit of Work pattern when needed.

---

## The Question

**Original Issue** (from ARCHITECTURE_REVIEW.md):

> Who manages transactions?
> - Do repositories commit? Or services?
> - What about multi-repository operations?
> - How do we handle rollback?

---

## The Answer

### Current Implementation ✅

**Repositories commit transactions.**

**Evidence**: `src/infrastructure/repositories/postgresql_domain_repository.py`

```python
class PostgreSQLDomainRepository:
    def save(self, domain: Domain) -> None:
        """Save domain to PostgreSQL (repository commits)"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Save domain
                cur.execute("""
                    INSERT INTO specql_registry.tb_domain (...)
                    VALUES (...)
                    ON CONFLICT (domain_number) DO UPDATE SET ...
                """, (...))

                # Save all subdomains
                for subdomain in domain.subdomains.values():
                    cur.execute("""INSERT INTO ...""")

                # COMMIT happens here automatically
                conn.commit()
```

**Pattern**: psycopg's `with conn:` context manager commits on successful exit, rolls back on exception.

---

## Transaction Management Patterns

### Pattern 1: Single Repository Operations (99% of cases)

**Use Case**: One aggregate, one repository, one transaction.

**Example**:
```python
# Application Service
class DomainService:
    def allocate_entity_code(self, domain_name, subdomain_name, entity_name) -> TableCode:
        # 1. Load aggregate
        domain = self.repository.find_by_name(domain_name)

        # 2. Execute business logic (in-memory, no DB)
        code = domain.allocate_entity_code(subdomain_name, entity_name)

        # 3. Save aggregate (repository commits transaction)
        self.repository.save(domain)

        return code
```

**Transaction Boundary**: Repository's `save()` method
- ✅ Commits on success
- ✅ Rolls back on exception
- ✅ Simple and clear
- ✅ Works for 99% of use cases

---

### Pattern 2: Multi-Repository Operations (Future - Unit of Work)

**Use Case**: Operations spanning multiple aggregates/repositories.

**Example Scenario** (not yet implemented):
```python
# Future: Coordinated save across Domain and Pattern repositories
def link_pattern_to_domain(domain_name: str, pattern_name: str):
    # Load from two repositories
    domain = domain_repo.get(domain_name)
    pattern = pattern_repo.get(pattern_name)

    # Modify both
    domain.add_linked_pattern(pattern.id)
    pattern.increment_usage()

    # Save both atomically (needs Unit of Work)
    domain_repo.save(domain)   # Commits transaction A
    pattern_repo.save(pattern)  # Commits transaction B  # ⚠️ NOT ATOMIC!
```

**Problem**: Two separate transactions, not atomic across aggregates.

**Solution** (when needed): Unit of Work pattern

```python
class UnitOfWork:
    """Manages transactional boundary across multiple repositories"""
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.connection = None

    def __enter__(self):
        self.connection = psycopg.connect(self.db_url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()

    def domain_repository(self) -> DomainRepository:
        """Return repository that shares this UoW's connection"""
        return PostgreSQLDomainRepository(connection=self.connection)

    def pattern_repository(self) -> PatternRepository:
        """Return repository that shares this UoW's connection"""
        return PostgreSQLPatternRepository(connection=self.connection)

# Usage:
with UnitOfWork(db_url) as uow:
    domain = uow.domain_repository().get(domain_name)
    pattern = uow.pattern_repository().get(pattern_name)

    domain.add_linked_pattern(pattern.id)
    pattern.increment_usage()

    uow.domain_repository().save(domain)
    uow.pattern_repository().save(pattern)
    # Commit happens here (single transaction)
```

**Status**: NOT YET IMPLEMENTED (not needed yet)

---

## Decision Matrix

| Scenario | Pattern | Who Commits | Status |
|----------|---------|-------------|--------|
| Single aggregate operation | Repository manages transaction | Repository | ✅ Implemented |
| Query operation (read-only) | Repository manages connection | Repository | ✅ Implemented |
| Multi-aggregate atomic update | Unit of Work | UnitOfWork | ⏳ Future (when needed) |
| Saga / eventual consistency | Domain Events + handlers | Event handlers | ⏳ Future (Phase 6+) |

---

## Why This Approach?

### Benefits ✅

1. **Simplicity**: 99% of operations just call `repository.save(aggregate)` - no transaction management needed
2. **Encapsulation**: Transaction details hidden in infrastructure layer
3. **Testability**: Easy to mock - `InMemoryRepository` doesn't need transactions
4. **Clear Boundaries**: Aggregate = transactional boundary
5. **Gradual Complexity**: Start simple, add Unit of Work only when actually needed

### Tradeoffs ⚠️

1. **No Multi-Aggregate Transactions**: Can't atomically update Domain + Pattern in single transaction
   - **Mitigation**: Design aggregates to be independently consistent
   - **Alternative**: Use Domain Events for eventual consistency
   - **Future**: Add Unit of Work if truly needed

2. **Repository Must Know About Transactions**: Infrastructure layer knows about transactions
   - **Mitigation**: This is appropriate for infrastructure layer
   - **Alternative**: None - transactions are infrastructure concern

---

## Examples from Codebase

### Example 1: PostgreSQL Repository Commits

**File**: `src/infrastructure/repositories/postgresql_domain_repository.py:63-98`

```python
def save(self, domain: Domain) -> None:
    """Save domain and all subdomains (transactional)"""
    with psycopg.connect(self.db_url) as conn:
        with conn.cursor() as cur:
            # UPSERT domain
            cur.execute("""
                INSERT INTO specql_registry.tb_domain
                (domain_number, domain_name, description, multi_tenant, aliases)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (domain_number) DO UPDATE SET
                    domain_name = EXCLUDED.domain_name,
                    description = EXCLUDED.description,
                    multi_tenant = EXCLUDED.multi_tenant,
                    aliases = EXCLUDED.aliases,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING pk_domain
            """, (...))

            # Save all subdomains atomically
            for subdomain in domain.subdomains.values():
                cur.execute("""
                    INSERT INTO specql_registry.tb_subdomain (...)
                    VALUES (...)
                    ON CONFLICT (...) DO UPDATE SET ...
                """, (...))

            conn.commit()  # ✅ REPOSITORY COMMITS
```

**Result**: Domain + all Subdomains saved atomically in single transaction.

---

### Example 2: In-Memory Repository (No Transactions)

**File**: `src/infrastructure/repositories/in_memory_domain_repository.py`

```python
class InMemoryDomainRepository:
    def __init__(self):
        self._domains: dict[str, Domain] = {}

    def save(self, domain: Domain) -> None:
        """Save domain (no transaction needed - in-memory)"""
        self._domains[domain.domain_number.value] = domain
        # ✅ No commit needed - just update dict
```

**Result**: Test repository doesn't need transaction management.

---

### Example 3: Application Service Uses Repository

**File**: `src/application/services/domain_service.py`

```python
class DomainService:
    def allocate_entity_code(
        self,
        domain_name: str,
        subdomain_name: str,
        entity_name: str
    ) -> TableCode:
        """Allocate entity code (service doesn't manage transaction)"""

        # Load aggregate
        domain = self.repository.find_by_name(domain_name)

        # Business logic (in-memory)
        code = domain.allocate_entity_code(subdomain_name, entity_name)

        # Save aggregate (repository commits)
        self.repository.save(domain)  # ✅ Repository handles transaction

        return code
```

**Result**: Service coordinates, repository manages transaction.

---

## Rollback Behavior

### Automatic Rollback on Exception

**psycopg context manager** handles rollback automatically:

```python
with psycopg.connect(self.db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO tb_domain ...")

        # If exception raised here
        raise ValueError("Something went wrong")

        conn.commit()  # Never reached
# Context manager AUTOMATICALLY calls conn.rollback()
```

**Result**: No partial commits, clean rollback on error.

---

### Example: Subdomain Validation Failure

```python
def save(self, domain: Domain) -> None:
    with psycopg.connect(self.db_url) as conn:
        with conn.cursor() as cur:
            # Save domain (succeeds)
            cur.execute("INSERT INTO tb_domain ...")

            # Save subdomains
            for subdomain in domain.subdomains.values():
                cur.execute("INSERT INTO tb_subdomain ...")  # ❌ Fails on duplicate

            conn.commit()  # Never reached
    # psycopg rolls back ALL changes (domain + subdomains)
```

**Result**: Either entire aggregate saves, or nothing saves. Atomicity guaranteed.

---

## Testing Strategy

### Unit Tests: Mock Repositories

```python
def test_allocate_entity_code():
    # Use in-memory repository (no transactions)
    repo = InMemoryDomainRepository()
    service = DomainService(repo)

    # Test business logic without transaction complexity
    code = service.allocate_entity_code("crm", "customer", "Contact")

    assert code.value == "012301"
```

**Benefit**: Tests focus on business logic, not transaction management.

---

### Integration Tests: Real Database

```python
@pytest.fixture
def db_repository():
    """Use real PostgreSQL repository with transactions"""
    return PostgreSQLDomainRepository(TEST_DB_URL)

def test_save_rollback_on_error(db_repository):
    domain = Domain(...)

    # Force error during save
    with pytest.raises(ValueError):
        domain.add_subdomain(invalid_subdomain)
        db_repository.save(domain)

    # Verify rollback - domain not in DB
    with pytest.raises(ValueError):
        db_repository.get(domain.domain_number.value)
```

**Benefit**: Integration tests verify transaction behavior.

---

## Future Considerations

### When to Add Unit of Work?

**Indicators**:
1. Need to atomically update 2+ aggregates
2. Operations span multiple bounded contexts
3. Complex multi-step workflows
4. Sagas requiring compensation

**Current Status**: NOT NEEDED YET
- All current operations are single-aggregate
- Aggregates designed to be independently consistent
- No cross-context transactions required

**When Implemented**:
- Add `src/application/unit_of_work.py`
- Update repositories to accept connection parameter
- Document UoW usage in services
- Add integration tests for multi-aggregate scenarios

---

### Alternative: Domain Events for Eventual Consistency

**Pattern**: Instead of multi-aggregate transactions, use events.

**Example**:
```python
# Instead of atomic transaction:
with UnitOfWork() as uow:
    domain.link_pattern(pattern_id)
    pattern.increment_usage()
    uow.commit()

# Use domain events:
domain.link_pattern(pattern_id)
domain_repo.save(domain)
# Emits: PatternLinkedToDomain(domain_id, pattern_id)

# Event handler (separate transaction):
def on_pattern_linked(event):
    pattern = pattern_repo.get_by_id(event.pattern_id)
    pattern.increment_usage()
    pattern_repo.save(pattern)
```

**Status**: Phase 6+ (not implemented yet)

---

## Summary

### Current Implementation ✅

| Aspect | Decision | Implementation |
|--------|----------|----------------|
| **Who commits?** | Repository | `conn.commit()` in `save()` |
| **Rollback?** | Automatic | psycopg context manager |
| **Multi-repo?** | Not supported yet | Add Unit of Work when needed |
| **Test strategy?** | Mock repo for unit tests | Real repo for integration tests |

### Key Principles

1. ✅ **Repositories commit** - Transaction boundary at repository `save()`
2. ✅ **Services orchestrate** - No transaction management in services
3. ✅ **Context managers** - psycopg handles commit/rollback automatically
4. ✅ **Aggregate = transaction** - Save aggregate = single transaction
5. ⏳ **Unit of Work** - Add when multi-aggregate transactions needed (future)

---

## References

- **Repository Implementation**: `src/infrastructure/repositories/postgresql_domain_repository.py`
- **Repository Pattern Doc**: `docs/architecture/REPOSITORY_PATTERN.md`
- **DDD Domain Model**: `docs/architecture/DDD_DOMAIN_MODEL.md`
- **Architecture Review**: `docs/architecture/ARCHITECTURE_REVIEW.md` (section 5)

---

**Last Updated**: 2025-11-12
**Status**: Implemented and Documented
**Decision**: Repositories Manage Transactions ✅

---

*Simple by default. Complex when needed. Atomic where it matters.* 🔒
