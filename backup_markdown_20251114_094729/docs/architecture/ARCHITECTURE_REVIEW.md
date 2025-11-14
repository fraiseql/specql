# Architecture Review: SpecQL PostgreSQL Bootstrap

**Date**: 2025-11-12
**Reviewers**: Development Team
**Status**: Ready for Review

---

## Executive Summary

This document provides a critical review of the proposed architecture for SpecQL's PostgreSQL migration, highlighting strengths, potential issues, and areas requiring clarification before implementation.

---

## Architecture Overview

### Proposed Stack

```
┌─────────────────────────────────────────┐
│  Presentation (2 interfaces)            │
│  • CLI (Click)                          │
│  • GraphQL (FraiseQL from ../fraiseql/) │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────▼──────────────────────────┐
│  Application Services (SHARED)          │
│  • DomainService                        │
│  • PatternService                       │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────▼──────────────────────────┐
│  Domain Entities                        │
│  • Domain, Subdomain                    │
│  • DomainNumber, TableCode              │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────▼──────────────────────────┐
│  Repositories (Protocol)                │
│  • PostgreSQL, YAML, InMemory           │
└─────────────────────────────────────────┘
```

---

## ✅ Strengths

### 1. Clean Architecture Compliance

**Good**:
- Clear separation of concerns (4 layers)
- Dependency inversion (interfaces not implementations)
- Testability built-in (mock repositories)
- Framework independence (can swap Click, FraiseQL, etc.)

**Evidence**: All layers defined with clear responsibilities in `DUAL_INTERFACE_ARCHITECTURE.md`

### 2. Dual Interface Design

**Good**:
- CLI for developers (local, fast, scriptable)
- GraphQL for applications (remote, rich queries)
- Shared Application Services (zero duplication)
- Thin wrappers (<10 lines) for both interfaces

**Evidence**: Side-by-side comparisons show same service calls in `DUAL_INTERFACE_ARCHITECTURE.md`

### 3. FraiseQL Integration

**Good**:
- Leverages existing production-ready framework
- Zero boilerplate (100-200 LOC vs 500-1000)
- Rust performance (no Python JSON overhead)
- Dogfooding our own ecosystem

**Evidence**: Complete integration plan in `FRAISEQL_INTEGRATION.md`

### 4. Repository Pattern

**Good**:
- Abstract data access (easy to swap PostgreSQL ↔ YAML)
- Protocol-based (Python typing.Protocol)
- Multiple implementations (PostgreSQL, YAML, InMemory)
- Testable with mocks

**Evidence**: Pattern documented in `REPOSITORY_PATTERN.md` (stub)

### 5. DDD Approach

**Good**:
- Rich domain model (not anemic)
- Business logic in entities
- Value objects for validation (DomainNumber, TableCode)
- Aggregates (Domain contains Subdomains)

**Evidence**: DDD layers in `DDD_DOMAIN_MODEL.md` (stub)

---

## ⚠️ Potential Issues & Questions

### 1. **Existing Code Integration**

**Issue**: SpecQL already has existing code in `src/generators/`, `src/cli/`, etc.

**Questions**:
- How do we migrate existing CLI commands to new architecture?
- What happens to `src/generators/schema/naming_conventions.py`?
- Is there a migration path for existing code?
- Can we do this incrementally or big bang?

**Recommendation**:
- ✅ Phase 0.8 addresses this ("Update existing code to use repositories")
- ⚠️ Need detailed migration plan for each existing module
- ⚠️ Need backward compatibility strategy

**Action Required**:
- [ ] Document migration path for each existing module
- [ ] Define backward compatibility requirements
- [ ] Create incremental migration checklist

### 2. **YAML Registry During Transition**

**Issue**: Current YAML registry is actively used

**Questions**:
- Do we maintain YAML registry during transition?
- When can we safely remove YAML?
- What if PostgreSQL migration fails?
- How do we handle dual-write period?

**Recommendation**:
- ✅ YAMLDomainRepository provides backward compatibility
- ⚠️ Need dual-write strategy (write to both, read from one)
- ⚠️ Need rollback plan

**Action Required**:
- [ ] Define dual-write implementation
- [ ] Create validation script (YAML vs PostgreSQL consistency)
- [ ] Document rollback procedure

### 3. **Repository Protocol vs ABC**

**Issue**: Implementation plan shows both `Protocol` and `ABC`

```python
# Which one?
class DomainRepository(Protocol):  # Option 1: Protocol (structural)
    ...

class DomainRepository(ABC):       # Option 2: ABC (nominal)
    ...
```

**Questions**:
- Protocol (duck typing) or ABC (inheritance)?
- What's the tradeoff?
- Does it matter for our use case?

**Recommendation**:
- ✅ Use `Protocol` for flexibility (structural subtyping)
- ✅ Easier to add new implementations
- ✅ No need to inherit from base class

**Action Required**:
- [ ] Confirm: Use `Protocol` consistently
- [ ] Update all examples to use `Protocol`
- [ ] Document rationale in REPOSITORY_PATTERN.md

### 4. **Value Object Validation**

**Issue**: Value objects validate on construction

```python
@dataclass(frozen=True)
class DomainNumber:
    value: str

    def __post_init__(self):
        if not re.match(r'^[1-9]$', self.value):
            raise ValueError(...)
```

**Questions**:
- What happens if validation fails in repository load?
- How do we handle corrupt data in YAML?
- Should we have `DomainNumber.try_parse()` for safer parsing?

**Recommendation**:
- ✅ Fail fast on invalid data (current approach)
- ⚠️ Add `from_string_safe()` factory method for parsing
- ⚠️ Repository should handle validation errors gracefully

**Action Required**:
- [ ] Add safe factory methods to value objects
- [ ] Document validation error handling strategy
- [ ] Add recovery mechanisms for corrupt data

### 5. **Transaction Boundaries**

**Issue**: Who manages transactions?

**Questions**:
- Do repositories commit? Or services?
- What about multi-repository operations?
- How do we handle rollback?

**Example**:
```python
def allocate_entity_code(...):
    domain = repo.get(...)
    code = domain.allocate_code(...)
    repo.save(domain)  # <-- Does this commit? Or do we commit outside?
```

**Recommendation**:
- ✅ Repositories manage their own transactions (simple case)
- ⚠️ Services manage transactions for complex cases (Unit of Work pattern)
- ⚠️ Need clear transaction boundary documentation

**Action Required**:
- [ ] Define transaction management strategy
- [ ] Document who commits (repository vs service)
- [ ] Consider Unit of Work pattern for complex scenarios
- [ ] Add examples in REPOSITORY_PATTERN.md

### 6. **FraiseQL Context Injection**

**Issue**: How do we inject repositories into FraiseQL context?

```python
app = create_fraiseql_app(
    ...
    context={
        "domain_service": domain_service  # How is this created?
    }
)
```

**Questions**:
- Who creates the services?
- Do we use a DI container?
- How do we handle lifecycle (per-request vs singleton)?
- What about connection pooling?

**Recommendation**:
- ✅ Simple approach: Create services at app startup (singleton)
- ⚠️ Need to handle database connection pooling properly
- ⚠️ Consider FastAPI dependency injection for per-request

**Action Required**:
- [ ] Document service lifecycle
- [ ] Define dependency injection strategy
- [ ] Handle connection pooling properly
- [ ] Add examples in FRAISEQL_INTEGRATION.md

### 7. **Testing Strategy**

**Issue**: Multiple testing levels mentioned

**Questions**:
- What's the test pyramid (unit vs integration)?
- Do we test each layer separately?
- What's the minimum coverage?
- How do we test CLI without subprocess?

**Recommendation**:
- ✅ Unit tests: Domain entities, value objects (>90%)
- ✅ Unit tests: Services with mock repositories (>90%)
- ✅ Integration tests: Repositories with real DB (>80%)
- ✅ Integration tests: CLI commands with Click.testing
- ✅ Integration tests: GraphQL with httpx AsyncClient

**Action Required**:
- [ ] Define test coverage targets per layer
- [ ] Create test template examples
- [ ] Document testing best practices
- [ ] Set up CI/CD test pipeline

### 8. **Performance Considerations**

**Issue**: No performance targets defined

**Questions**:
- What's acceptable latency for registry operations?
- Do we need caching?
- What about N+1 queries in GraphQL?
- How do we handle large registries (1000+ entities)?

**Recommendation**:
- ✅ Set performance targets (<10ms for registry lookups)
- ✅ FraiseQL handles N+1 with its query optimization
- ⚠️ Consider caching for frequently accessed domains
- ⚠️ Benchmark before and after migration

**Action Required**:
- [ ] Define performance SLAs
- [ ] Add benchmarking to Phase 0
- [ ] Consider caching strategy
- [ ] Document performance characteristics

### 9. **Error Handling**

**Issue**: No unified error handling strategy

**Questions**:
- How do we handle validation errors?
- What error types do we return (exceptions vs Result types)?
- How do errors propagate from domain → service → presentation?
- Do CLI and GraphQL return consistent errors?

**Recommendation**:
- ✅ Domain: Raise specific exceptions (ValueError, DomainError)
- ✅ Services: Let exceptions propagate (don't catch blindly)
- ✅ Presentation: Convert to appropriate format (CLI exit codes, GraphQL errors)
- ⚠️ Need error hierarchy

**Action Required**:
- [ ] Define error hierarchy (DomainError, ValidationError, etc.)
- [ ] Document error handling strategy per layer
- [ ] Ensure consistent errors across interfaces
- [ ] Add error examples in docs

### 10. **Documentation Completeness**

**Issue**: Some docs are stubs

**Current State**:
- ✅ FRAISEQL_INTEGRATION.md - Complete
- ✅ DUAL_INTERFACE_ARCHITECTURE.md - Complete
- ✅ README.md - Complete
- ⚠️ REPOSITORY_PATTERN.md - Stub (58 lines)
- ⚠️ DDD_DOMAIN_MODEL.md - Stub (71 lines)

**Action Required**:
- [ ] Complete REPOSITORY_PATTERN.md with full examples
- [ ] Complete DDD_DOMAIN_MODEL.md with all aggregates
- [ ] Add migration guide for existing code
- [ ] Add troubleshooting section

---

## 🔍 Detailed Review: Phase 0

### Phase 0.1: Revert Working Directory ✅

**Good**: Clean slate approach

**Action**: None needed

### Phase 0.2: Create REPOSITORY_PATTERN.md ⚠️

**Issue**: Current doc is stub

**Required Content**:
- [ ] Complete repository protocol examples
- [ ] Show all CRUD operations
- [ ] Document transaction management
- [ ] Add testing examples with mocks
- [ ] Show repository composition patterns

### Phase 0.3: Create DDD_DOMAIN_MODEL.md ⚠️

**Issue**: Current doc is stub

**Required Content**:
- [ ] Complete all bounded contexts
- [ ] Define all aggregates (not just Domain)
- [ ] Define all value objects
- [ ] Show aggregate boundaries
- [ ] Document invariants and business rules
- [ ] Add domain events (if needed)

### Phase 0.4: Implement Base Repository ⚠️

**Question**: Generic `Repository[T]` vs specific protocols?

**Options**:
```python
# Option 1: Generic
class Repository(Protocol, Generic[T]):
    def get(self, id: str) -> T: ...

# Option 2: Specific
class DomainRepository(Protocol):
    def get(self, domain_number: str) -> Domain: ...
```

**Recommendation**: Use specific protocols (Option 2)
- More type-safe
- Better IDE support
- Clearer intent

**Action Required**:
- [ ] Confirm approach (specific vs generic)
- [ ] Update examples accordingly

### Phase 0.5: Implement Domain Entities ⚠️

**Issue**: Aggregate boundaries not clear

**Questions**:
- Is `EntityRegistration` part of `Domain` aggregate or separate?
- Should `Subdomain.entities` be a collection or separate aggregate?
- What about pattern library entities?

**Recommendation**:
- ✅ `Domain` aggregate contains `Subdomain` (natural composition)
- ⚠️ `EntityRegistration` might be separate aggregate (different lifecycle)
- ⚠️ Need to define aggregate boundaries clearly

**Action Required**:
- [ ] Define aggregate boundaries in DDD_DOMAIN_MODEL.md
- [ ] Document aggregate consistency rules
- [ ] Show aggregate interaction patterns

### Phase 0.6: Implement Repositories ⚠️

**Issue**: PostgreSQL schema doesn't exist yet

**Problem**: Can't implement PostgreSQLDomainRepository without tables

**Solution**:
1. Start with YAMLDomainRepository (works with existing registry)
2. Implement InMemoryDomainRepository (for tests)
3. Generate PostgreSQL schema (Phase 1)
4. Implement PostgreSQLDomainRepository (Phase 1)

**Action Required**:
- [ ] Update phase order in BOOTSTRAP plan
- [ ] Start with YAML repository first
- [ ] Defer PostgreSQL repository to Phase 1

### Phase 0.7: Implement Services ✅

**Good**: Clear separation, thin wrappers

**Confirmation Needed**:
- Services are stateless? ✅ Yes
- Services take repository as constructor arg? ✅ Yes
- Services don't know about presentation layer? ✅ Yes

### Phase 0.8: Update Existing Code ⚠️

**Major Risk**: This could break everything

**Questions**:
- Which files need updating?
- Can we do it incrementally?
- What's the testing strategy?
- What's the rollback plan?

**Recommendation**:
- Create detailed migration plan for each module
- Use feature flags for gradual rollout
- Extensive testing before switching

**Action Required**:
- [ ] List all files that need updating
- [ ] Create migration plan for each
- [ ] Define testing strategy
- [ ] Add rollback mechanism

### Phase 0.9: Dual Presentation Layer ✅

**Good**: Well documented

**Confirmation Needed**:
- Both interfaces are thin wrappers? ✅ Yes
- Both call same services? ✅ Yes
- Consistency tests exist? ⚠️ To be implemented

---

## 📋 Decision Log

### Decisions Made

1. **Use Protocol over ABC** - For repository interfaces
2. **Dual Interface** - CLI + GraphQL, not just one
3. **Use FraiseQL** - Leverage existing framework
4. **Shared Services** - Zero duplication
5. **Architecture First** - No implementation without design

### Decisions Needed

1. **Transaction Management** - Who commits? Repository or Service?
2. **Error Hierarchy** - What exceptions do we define?
3. **Caching Strategy** - Do we cache domains? Where?
4. **Migration Order** - Update existing code before or after PostgreSQL?
5. **Aggregate Boundaries** - Is EntityRegistration part of Domain aggregate?

---

## 🎯 Recommendations

### Critical (Must Address Before Implementation)

1. **Complete Documentation**
   - Finish REPOSITORY_PATTERN.md with all patterns
   - Finish DDD_DOMAIN_MODEL.md with all aggregates
   - Add error handling documentation
   - Add performance targets

2. **Define Transaction Management**
   - Document who manages transactions
   - Add Unit of Work pattern if needed
   - Show examples for complex scenarios

3. **Create Migration Plan**
   - List all existing code to update
   - Define incremental migration steps
   - Add backward compatibility layer
   - Document rollback procedure

4. **Clarify Aggregate Boundaries**
   - Define what's inside Domain aggregate
   - Define separate aggregates
   - Document consistency rules

### Important (Should Address Soon)

5. **Add Error Hierarchy**
   - Define DomainError, ValidationError, etc.
   - Document error propagation
   - Ensure consistent errors across interfaces

6. **Define Performance Targets**
   - Set SLAs for registry operations
   - Add benchmarking to Phase 0
   - Consider caching strategy

7. **Update Repository Order**
   - YAML first (works with existing)
   - InMemory second (for tests)
   - PostgreSQL third (Phase 1)

### Nice to Have

8. **Add Domain Events** - If needed for complex workflows
9. **Add Caching Layer** - If performance requires it
10. **Add Monitoring** - Instrumentation for production

---

## ✅ Go / No-Go Checklist

### Required Before Implementation

- [ ] REPOSITORY_PATTERN.md complete
- [ ] DDD_DOMAIN_MODEL.md complete
- [ ] Transaction management strategy documented
- [ ] Error hierarchy defined
- [ ] Aggregate boundaries clear
- [ ] Migration plan for existing code
- [ ] Performance targets set
- [ ] Test strategy documented

### Nice to Have

- [ ] Caching strategy defined
- [ ] Monitoring approach documented
- [ ] Domain events considered

---

## 🚦 Recommendation: GO or NO-GO?

### Current Status: **YELLOW** (Proceed with Caution)

**Strengths**:
- ✅ Solid architectural foundation
- ✅ Clean separation of concerns
- ✅ Good documentation (partial)
- ✅ Dual interface well designed
- ✅ FraiseQL integration clear

**Gaps**:
- ⚠️ Documentation incomplete (2 stubs)
- ⚠️ Transaction management unclear
- ⚠️ Error handling not defined
- ⚠️ Migration plan vague
- ⚠️ Aggregate boundaries fuzzy

**Recommendation**:
1. **Complete critical documentation** (items 1-4 above)
2. **Review with team** - Get feedback on decisions
3. **Start Phase 0.1-0.5** (safe, no breaking changes)
4. **Pause before 0.6-0.8** - Ensure migration plan solid
5. **Proceed incrementally** - One phase at a time

### Estimated Time to GREEN

- **1-2 days**: Complete documentation
- **2-3 days**: Review and approve
- **Then**: Ready for implementation

---

## 📝 Next Steps

1. **Review this document** with team
2. **Address critical items** (1-4)
3. **Update documentation** (REPOSITORY_PATTERN, DDD_DOMAIN_MODEL)
4. **Get approval** on architectural decisions
5. **Start Phase 0** with confidence

---

**Status**: Architecture review complete
**Recommendation**: Complete documentation, then proceed
**Timeline**: 1-2 days to GREEN light

---

*Let's build it right, not fast.* 🏗️
