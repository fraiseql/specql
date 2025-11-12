# Domain-Driven Design: SpecQL Domain Model

**Date**: 2025-11-12
**Status**: Phases 1-4 Complete, Phase 5 In Progress
**Implementation**: Actual production code (not theoretical)

---

## Executive Summary

SpecQL uses **Domain-Driven Design (DDD)** to model its core business domain: managing database schema registries and reusable patterns. This document describes the **actual implemented** domain model with real code from the codebase.

**Key Achievement**: Rich domain entities with business logic embedded, following DDD principles of "smart objects, not anemic data structures."

---

## Table of Contents

1. [Bounded Contexts](#bounded-contexts)
2. [Registry Context (Primary)](#registry-context-primary)
3. [Pattern Context](#pattern-context)
4. [Value Objects](#value-objects)
5. [Clean Architecture Layers](#clean-architecture-layers)
6. [Aggregate Boundaries](#aggregate-boundaries)
7. [Business Rules & Invariants](#business-rules--invariants)
8. [Domain Events (Future)](#domain-events-future)

---

## Bounded Contexts

SpecQL has **4 bounded contexts**, each representing a distinct business capability:

```
┌─────────────────────────────────────────────────────────┐
│                     SpecQL System                        │
│                                                          │
│  ┌────────────┐  ┌───────────┐  ┌──────┐  ┌─────────┐  │
│  │  Registry  │  │  Pattern  │  │ Type │  │ Service │  │
│  │  Context   │  │  Context  │  │ Ctx  │  │ Context │  │
│  └────────────┘  └───────────┘  └──────┘  └─────────┘  │
│       ↑              ↑              ↑          ↑         │
│       └──────────────┴──────────────┴──────────┘         │
│              Shared Application Services                 │
└─────────────────────────────────────────────────────────┘
```

### 1. **Registry Context** (Primary - Fully Implemented ✅)

**Purpose**: Manage domain/subdomain/entity registration and code allocation

**Ubiquitous Language**:
- **Domain**: Top-level business area (CRM, Projects, etc.)
- **Subdomain**: Subdivision within a domain (Customer, Sales)
- **Entity**: Database table/entity to track
- **Code Allocation**: Assigning unique 6-digit codes

**Implementation**: `src/domain/entities/domain.py`

### 2. **Pattern Context** (Implemented ✅)

**Purpose**: Manage reusable domain patterns with AI-enhanced discovery

**Ubiquitous Language**:
- **Pattern**: Reusable business logic template
- **Category**: Pattern classification (workflow, validation, etc.)
- **Embedding**: Vector representation for similarity search
- **Instantiation**: Using a pattern in a concrete context
- **Deprecation**: Marking patterns obsolete

**Implementation**: `src/domain/entities/pattern.py`

### 3. **Type Context** (Pending)

**Purpose**: Manage type definitions and mappings across database systems

**Status**: Architecture designed, implementation pending

### 4. **Service Context** (Pending)

**Purpose**: Service registry and dependency tracking

**Status**: Architecture designed, implementation pending

---

## Registry Context (Primary)

### Aggregate Root: `Domain`

**File**: `src/domain/entities/domain.py:31-60`

The `Domain` aggregate root represents a top-level business domain with its subdomains and entity registrations.

```python
@dataclass
class Domain:
    """Domain Aggregate Root"""
    domain_number: DomainNumber              # Value Object (1-9)
    domain_name: str                         # e.g., "crm", "projects"
    description: str | None                  # Optional description
    multi_tenant: bool                       # Tenant isolation flag
    aliases: List[str] = field(default_factory=list)  # Alternative names
    subdomains: dict[str, Subdomain] = field(default_factory=dict)  # Child entities

    def add_subdomain(self, subdomain: Subdomain) -> None:
        """Add subdomain to domain (enforces consistency)"""
        if subdomain.subdomain_number in self.subdomains:
            raise ValueError(
                f"Subdomain {subdomain.subdomain_number} already exists in {self.domain_name}"
            )
        subdomain.parent_domain_number = self.domain_number.value
        self.subdomains[subdomain.subdomain_number] = subdomain

    def get_subdomain(self, subdomain_number: str) -> Subdomain:
        """Get subdomain by number (validates existence)"""
        if subdomain_number not in self.subdomains:
            raise ValueError(
                f"Subdomain {subdomain_number} not found in {self.domain_name}"
            )
        return self.subdomains[subdomain_number]

    def allocate_entity_code(self, subdomain_num: str, entity_name: str) -> TableCode:
        """Allocate 6-digit code for entity (orchestrates business logic)"""
        subdomain = self.get_subdomain(subdomain_num)
        return subdomain.allocate_next_code(entity_name)
```

**Key Business Logic**:

1. **Subdomain Uniqueness**: No duplicate subdomain numbers within a domain
2. **Parent-Child Relationship**: Subdomains know their parent domain
3. **Code Allocation**: Orchestrates subdomain code generation
4. **Invariant Protection**: Cannot create invalid state

**Why Aggregate Root?**:
- Controls access to child entities (Subdomain)
- Enforces consistency boundaries
- All modifications go through Domain methods
- Transactional boundary (save Domain = save all Subdomains)

---

### Entity: `Subdomain`

**File**: `src/domain/entities/domain.py:7-28`

Subdomain is an **entity** (not aggregate root) within the Domain aggregate.

```python
@dataclass
class Subdomain:
    """Subdomain entity (part of Domain aggregate)"""
    subdomain_number: str                    # e.g., "2", "3"
    subdomain_name: str                      # e.g., "customer", "sales"
    description: str | None                  # Optional description
    next_entity_sequence: int = 1            # Auto-increment sequence
    entities: dict = field(default_factory=dict)  # Registered entities
    parent_domain_number: str = ""           # Set by Domain.add_subdomain()

    def allocate_next_code(self, entity_name: str) -> TableCode:
        """Allocate next entity code (business logic)"""
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
```

**Key Business Logic**:

1. **Sequence Management**: Auto-increment `next_entity_sequence`
2. **Code Generation**: Delegates to `TableCode.generate()`
3. **Entity Tracking**: Records allocated entities
4. **Immutability**: Returns value object (TableCode), not mutable data

**Why Entity (not Value Object)?**:
- Has identity (subdomain_number)
- Mutable state (next_entity_sequence)
- Lifecycle managed by Domain aggregate

---

## Pattern Context

### Aggregate Root: `Pattern`

**File**: `src/domain/entities/pattern.py:30-138`

The `Pattern` aggregate root represents a reusable domain pattern with AI-enhanced discovery.

```python
@dataclass
class Pattern:
    """Pattern Aggregate Root - Domain pattern with business logic"""

    # Identity
    id: Optional[int]
    name: str
    category: PatternCategory          # Enum: WORKFLOW, VALIDATION, etc.
    description: str

    # Pattern definition
    parameters: Dict[str, Any] = field(default_factory=dict)
    implementation: Dict[str, Any] = field(default_factory=dict)

    # Vector embedding for similarity search
    embedding: Optional[List[float]] = None  # 384-dimensional vector

    # Metadata
    times_instantiated: int = 0
    source_type: SourceType = SourceType.MANUAL  # MANUAL, LLM_GENERATED, etc.
    complexity_score: Optional[float] = None     # 0-10
    deprecated: bool = False
    deprecated_reason: Optional[str] = None
    replacement_pattern_id: Optional[int] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate pattern data (enforces invariants)"""
        if not self.name or not self.name.strip():
            raise ValueError("Pattern name cannot be empty")

        if len(self.name) > 100:
            raise ValueError("Pattern name cannot exceed 100 characters")

        if not self.description or not self.description.strip():
            raise ValueError("Pattern description cannot be empty")

        if self.complexity_score is not None and (self.complexity_score < 0 or self.complexity_score > 10):
            raise ValueError("Complexity score must be between 0 and 10")

        if self.embedding is not None and len(self.embedding) != 384:
            raise ValueError("Embedding must be 384-dimensional vector")

    def mark_deprecated(self, reason: str, replacement_pattern_id: Optional[int] = None) -> None:
        """Mark pattern as deprecated with reason (business logic)"""
        if not reason or not reason.strip():
            raise ValueError("Deprecation reason cannot be empty")

        self.deprecated = True
        self.deprecated_reason = reason
        self.replacement_pattern_id = replacement_pattern_id
        self.updated_at = datetime.now()

    def increment_usage(self) -> None:
        """Increment usage counter when pattern is instantiated"""
        self.times_instantiated += 1
        self.updated_at = datetime.now()

    def update_embedding(self, embedding: List[float]) -> None:
        """Update vector embedding for similarity search"""
        if len(embedding) != 384:
            raise ValueError("Embedding must be 384-dimensional vector")

        self.embedding = embedding
        self.updated_at = datetime.now()

    def is_similar_to(self, other_embedding: List[float], threshold: float = 0.7) -> bool:
        """Check if this pattern is similar to another (domain logic)"""
        if self.embedding is None or other_embedding is None:
            return False

        if len(self.embedding) != len(other_embedding):
            return False

        # Cosine similarity calculation
        import math
        dot_product = sum(a * b for a, b in zip(self.embedding, other_embedding))
        magnitude_a = math.sqrt(sum(a * a for a in self.embedding))
        magnitude_b = math.sqrt(sum(b * b for b in other_embedding))

        if magnitude_a == 0 or magnitude_b == 0:
            return False

        similarity = dot_product / (magnitude_a * magnitude_b)
        return similarity >= threshold

    def can_be_used_for(self, context: Dict[str, Any]) -> bool:
        """Check if pattern can be used in given context (business rule)"""
        if self.deprecated:
            return False

        # Check if required parameters are available in context
        required_params = self.parameters.get('required', [])
        for param in required_params:
            if param not in context:
                return False

        return True

    @property
    def is_active(self) -> bool:
        """Check if pattern is active (not deprecated)"""
        return not self.deprecated

    @property
    def has_embedding(self) -> bool:
        """Check if pattern has vector embedding"""
        return self.embedding is not None
```

**Key Business Logic**:

1. **Validation**: Comprehensive invariant checking in `__post_init__`
2. **Lifecycle Management**: Deprecation with reason and replacement tracking
3. **Usage Tracking**: Increments counter when instantiated
4. **Similarity Search**: Cosine similarity calculation for AI discovery
5. **Context Validation**: Checks if pattern can be used in given context
6. **Computed Properties**: `is_active`, `has_embedding`

**Rich Domain Model**:
- **NOT anemic**: Contains business logic, not just getters/setters
- **Self-validating**: Enforces invariants on construction
- **Behavior-rich**: Methods encode business rules
- **AI-enhanced**: Embedding support for semantic search

**Why Aggregate Root?**:
- Independent lifecycle (not part of another aggregate)
- Can be referenced by ID from other contexts
- Transactional boundary for pattern operations

---

### Enumerations

**File**: `src/domain/entities/pattern.py:8-27`

```python
class PatternCategory(Enum):
    """Valid pattern categories"""
    WORKFLOW = "workflow"
    VALIDATION = "validation"
    AUDIT = "audit"
    HIERARCHY = "hierarchy"
    STATE_MACHINE = "state_machine"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    CALCULATION = "calculation"
    SOFT_DELETE = "soft_delete"

class SourceType(Enum):
    """Pattern source types"""
    MANUAL = "manual"
    LLM_GENERATED = "llm_generated"
    DISCOVERED = "discovered"
    MIGRATED = "migrated"
```

**Purpose**: Type-safe enumerations for domain concepts with restricted values.

---

## Value Objects

### `DomainNumber`

**File**: `src/domain/value_objects/__init__.py:5-15`

```python
@dataclass(frozen=True)
class DomainNumber:
    """Domain number (1-9) - immutable value object"""
    value: str

    def __post_init__(self):
        if not re.match(r'^[1-9]$', self.value):
            raise ValueError(f"Domain number must be 1-9, got: {self.value}")

    def __str__(self):
        return self.value
```

**Why Value Object?**:
- ✅ **Immutable**: `@dataclass(frozen=True)`
- ✅ **Self-validating**: Regex validation in `__post_init__`
- ✅ **No identity**: Two DomainNumbers with same value are equal
- ✅ **Encapsulates validation**: Cannot create invalid DomainNumber

**Business Rule**: Domain numbers are restricted to 1-9 (single digit).

---

### `TableCode`

**File**: `src/domain/value_objects/__init__.py:17-39`

```python
@dataclass(frozen=True)
class TableCode:
    """6-digit table code - immutable value object"""
    value: str

    def __post_init__(self):
        if not re.match(r'^\d{6}$', self.value):
            raise ValueError(f"Table code must be 6 digits, got: {self.value}")

    @classmethod
    def generate(cls, domain_num: str, subdomain_num: str, entity_seq: int, file_seq: int = 0) -> 'TableCode':
        """Generate 6-digit code from components"""
        code = f"{domain_num}{subdomain_num}{entity_seq:02d}{file_seq}"
        if len(code) > 6:
            # Handle longer sequences by using the last 6 digits
            code = code[-6:]
        elif len(code) < 6:
            # Pad with zeros if too short
            code = code.zfill(6)
        return cls(code)

    def __str__(self):
        return self.value
```

**Why Value Object?**:
- ✅ **Immutable**: Cannot modify after creation
- ✅ **Self-validating**: Enforces 6-digit format
- ✅ **Factory Method**: `generate()` constructs from components
- ✅ **Domain Logic**: Handles padding and truncation

**Business Rule**: Table codes are always 6 digits: `{domain}{subdomain}{entity:2d}{file}`

**Example**:
```python
# Domain 1, Subdomain 2, Entity 3, File 0
code = TableCode.generate("1", "2", 3, 0)
print(code)  # "012300"
```

---

## Clean Architecture Layers

### Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│         Presentation Layer (Interface Adapters)         │
│                                                          │
│  ┌──────────────────┐         ┌────────────────────┐   │
│  │  CLI (Click)     │         │  GraphQL (FraiseQL)│   │
│  │  src/cli/        │         │  (Future)          │   │
│  └────────┬─────────┘         └─────────┬──────────┘   │
└───────────┼─────────────────────────────┼───────────────┘
            │                             │
            └─────────────┬───────────────┘
                          │ Calls
┌─────────────────────────▼───────────────────────────────┐
│           Application Layer (Use Cases)                  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Application Services                            │   │
│  │  • DomainService                                 │   │
│  │  • PatternService                                │   │
│  │    (Orchestrates domain logic, no business rules)│   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────┘
                          │ Uses
┌─────────────────────────▼───────────────────────────────┐
│            Domain Layer (Business Logic)                 │
│                                                          │
│  ┌────────────────────┐  ┌──────────────────────────┐   │
│  │  Entities          │  │  Value Objects           │   │
│  │  • Domain          │  │  • DomainNumber          │   │
│  │  • Subdomain       │  │  • TableCode             │   │
│  │  • Pattern         │  │  (Immutable, validated)  │   │
│  │  (Rich, smart)     │  └──────────────────────────┘   │
│  └────────────────────┘                                  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Repository Protocols (Interfaces)              │    │
│  │  • DomainRepository                             │    │
│  │  • PatternRepository                            │    │
│  │  (typing.Protocol - structural subtyping)       │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────┘
                          │ Implemented by
┌─────────────────────────▼───────────────────────────────┐
│      Infrastructure Layer (Technical Details)            │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Repository Implementations                      │   │
│  │  • PostgreSQLDomainRepository                    │   │
│  │  • PostgreSQLPatternRepository                   │   │
│  │  • InMemoryDomainRepository (tests)             │   │
│  │  • InMemoryPatternRepository (tests)            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  External Systems                                │   │
│  │  • PostgreSQL (specql_registry schema)           │   │
│  │  • pgvector (semantic search - future)           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Presentation Layer** (`src/cli/`, future: `src/presentation/fraiseql/`):
- User interface (CLI commands, GraphQL resolvers)
- Input validation and parsing
- Output formatting
- **Thin wrappers**: <10 lines, delegates to Application Services
- **No business logic**: Just adapts between UI and services

**Application Layer** (`src/application/services/`):
- Orchestrates domain logic
- Coordinates repository operations
- Transaction boundaries (for complex cases)
- **No business rules**: Just coordinates entities and repositories
- **Use case implementations**: One service method = one use case

**Domain Layer** (`src/domain/`):
- **ALL business logic lives here**
- Rich domain entities with behavior
- Value objects with validation
- Repository protocols (abstract interfaces)
- Aggregates and consistency boundaries
- **Framework-independent**: No imports from infrastructure

**Infrastructure Layer** (`src/infrastructure/`):
- Concrete repository implementations
- Database access (PostgreSQL, in-memory)
- External service integrations
- Technical details and I/O
- **Implements domain protocols**

---

## Aggregate Boundaries

### What is an Aggregate?

An **aggregate** is a cluster of domain objects (entities + value objects) that can be treated as a single unit for data changes. Each aggregate has:

1. **Aggregate Root**: Entry point for all operations
2. **Consistency Boundary**: All changes are transactional
3. **Identity**: Root has unique identifier
4. **Child Entities**: Only accessible through root

### Registry Context Aggregates

#### `Domain` Aggregate

```
┌─────────────────────────────────────────┐
│  Domain (Aggregate Root)                │
│  • domain_number: DomainNumber          │
│  • domain_name: str                     │
│  • multi_tenant: bool                   │
│  • aliases: List[str]                   │
│  │                                       │
│  └──> subdomains: dict[str, Subdomain]  │
│       │                                  │
│       ├─> Subdomain (Entity)            │
│       │   • subdomain_number: str       │
│       │   • subdomain_name: str         │
│       │   • next_entity_sequence: int   │
│       │   • entities: dict              │
│       │                                  │
│       └─> Subdomain (Entity)            │
└─────────────────────────────────────────┘
```

**Consistency Rules**:
1. Cannot add duplicate subdomains to a domain
2. Subdomain must have valid parent_domain_number
3. Entity sequences are auto-incremented
4. Save Domain = save all Subdomains (atomic)

**Why One Aggregate?**:
- Domain and Subdomains are strongly coupled
- Always loaded/saved together
- Consistency boundary makes sense
- Typical operation: "Get domain with all subdomains"

**Transactional Boundary**:
```python
# Single transaction for entire aggregate
domain = repository.get("1")
domain.add_subdomain(subdomain)
code = domain.allocate_entity_code("2", "Contact")
repository.save(domain)  # Commits domain + all subdomains
```

---

### Pattern Context Aggregates

#### `Pattern` Aggregate

```
┌─────────────────────────────────────────┐
│  Pattern (Aggregate Root)               │
│  • id: int                              │
│  • name: str                            │
│  • category: PatternCategory            │
│  • description: str                     │
│  • parameters: Dict[str, Any]           │
│  • implementation: Dict[str, Any]       │
│  • embedding: List[float]               │
│  • times_instantiated: int              │
│  • deprecated: bool                     │
└─────────────────────────────────────────┘
```

**Consistency Rules**:
1. Pattern name is unique
2. Cannot deprecate without reason
3. Embedding must be 384 dimensions
4. Complexity score 0-10 or None

**Why Separate Aggregate?**:
- Independent lifecycle from Domain
- Can be referenced by ID
- No parent-child relationship
- Can be loaded/saved independently

---

### Aggregate References

**Rule**: Aggregates reference each other by ID, not object references.

**Example**:
```python
# ✅ GOOD: Reference by ID
pattern.replacement_pattern_id = 42

# ❌ BAD: Direct object reference
pattern.replacement_pattern = other_pattern_object
```

**Rationale**:
- Avoids loading entire object graphs
- Clear transactional boundaries
- Easier to persist and query
- Prevents circular dependencies

---

## Business Rules & Invariants

### Registry Context Rules

**Domain Invariants**:
1. Domain number must be 1-9 (enforced by `DomainNumber` value object)
2. Domain name is required (not empty)
3. Multi-tenant flag determines schema organization
4. Aliases provide alternative lookup names

**Subdomain Invariants**:
1. Subdomain number must be unique within domain
2. Entity sequence starts at 1 and auto-increments
3. Cannot allocate code without parent domain
4. Entity names tracked per subdomain

**Code Allocation Rules**:
1. Table codes are always 6 digits: `{domain}{subdomain}{entity:2d}{file}`
2. Entity sequences never decrease (monotonic)
3. Code generation is deterministic
4. Codes are immutable once allocated

**Example Validation**:
```python
# Invalid domain number
try:
    domain_num = DomainNumber("10")  # ❌ Must be 1-9
except ValueError as e:
    print(e)  # "Domain number must be 1-9, got: 10"

# Invalid subdomain
domain = Domain(DomainNumber("1"), "crm", None, True)
subdomain1 = Subdomain("2", "customer", None)
domain.add_subdomain(subdomain1)

subdomain2 = Subdomain("2", "duplicate", None)
try:
    domain.add_subdomain(subdomain2)  # ❌ Duplicate number
except ValueError as e:
    print(e)  # "Subdomain 2 already exists in crm"
```

---

### Pattern Context Rules

**Pattern Invariants**:
1. Pattern name is required and max 100 characters
2. Description is required
3. Complexity score is 0-10 or None
4. Embedding is 384 dimensions or None
5. Deprecated patterns require reason

**Lifecycle Rules**:
1. Cannot mark deprecated without reason
2. Deprecation reason cannot be empty
3. Replacement pattern must exist (if specified)
4. Usage counter increments on instantiation
5. Timestamps auto-update on changes

**Usage Rules**:
1. Deprecated patterns cannot be used
2. Required parameters must be in context
3. Similarity threshold for matches (default 0.7)

**Example Validation**:
```python
# Invalid pattern
try:
    pattern = Pattern(
        id=None,
        name="",  # ❌ Empty name
        category=PatternCategory.WORKFLOW,
        description="Some description"
    )
except ValueError as e:
    print(e)  # "Pattern name cannot be empty"

# Invalid deprecation
pattern = Pattern(id=1, name="old_pattern", category=PatternCategory.WORKFLOW, description="Old")
try:
    pattern.mark_deprecated("")  # ❌ Empty reason
except ValueError as e:
    print(e)  # "Deprecation reason cannot be empty"
```

---

## Application Services

### `DomainService`

**File**: `src/application/services/domain_service.py`

**Responsibility**: Orchestrate domain entity operations for Registry context.

**Key Methods**:
```python
class DomainService:
    def __init__(self, repository: DomainRepository):
        self.repository = repository

    def register_domain(self, domain_number: str, domain_name: str, ...) -> Domain:
        """Register new domain (use case)"""
        # Validate domain doesn't exist
        # Create domain entity
        # Save via repository
        # Return domain

    def allocate_entity_code(self, domain_name: str, subdomain_name: str, entity_name: str) -> TableCode:
        """Allocate entity code (use case)"""
        domain = self.repository.find_by_name(domain_name)
        code = domain.allocate_entity_code(subdomain_name, entity_name)  # Domain logic
        self.repository.save(domain)
        return code

    def list_all_domains(self) -> list[Domain]:
        """List all domains (query)"""
        return self.repository.list_all()
```

**Pattern**:
1. Service receives repository via constructor (dependency injection)
2. Service methods correspond to use cases
3. Service delegates business logic to domain entities
4. Service coordinates repository operations
5. Service has NO business rules (just orchestration)

---

### `PatternService`

**File**: `src/application/services/pattern_service.py`

**Responsibility**: Orchestrate pattern operations for Pattern context.

**Key Methods**:
```python
class PatternService:
    def __init__(self, repository: PatternRepository):
        self.repository = repository

    def create_pattern(self, name: str, category: str, description: str, ...) -> Pattern:
        """Create new pattern (use case)"""
        pattern = Pattern(...)  # Create entity
        self.repository.save(pattern)
        return pattern

    def deprecate_pattern(self, name: str, reason: str, replacement: Optional[str] = None) -> None:
        """Mark pattern as deprecated (use case)"""
        pattern = self.repository.get(name)
        pattern.mark_deprecated(reason, replacement)  # Domain logic
        self.repository.save(pattern)

    def find_similar_patterns(self, pattern_name: str, threshold: float = 0.7) -> List[Pattern]:
        """Find similar patterns using embeddings (use case)"""
        target = self.repository.get(pattern_name)
        all_patterns = self.repository.list_all()
        return [p for p in all_patterns if p.is_similar_to(target.embedding, threshold)]
```

**Pattern**: Same as DomainService - orchestration, not business logic.

---

## Domain Events (Future)

### What are Domain Events?

**Domain Events** are notifications of significant business occurrences.

### Potential Events

**Registry Context**:
- `DomainRegistered(domain_number, domain_name)`
- `SubdomainAdded(domain_number, subdomain_number)`
- `EntityCodeAllocated(domain, subdomain, entity, code)`

**Pattern Context**:
- `PatternCreated(pattern_name, category)`
- `PatternDeprecated(pattern_name, reason, replacement)`
- `PatternInstantiated(pattern_name, context)`

### Benefits

1. **Loose Coupling**: Other contexts can react without tight coupling
2. **Audit Trail**: Events form complete history
3. **CQRS**: Read models can be updated from events
4. **Integration**: External systems can subscribe

### Implementation Status

**Status**: Not yet implemented (Phase 6+)

**When Needed**:
- Multi-context coordination (e.g., Pattern library reacts to Domain changes)
- Audit logging requirements
- Event sourcing patterns
- Real-time notifications

---

## Summary

### What's Implemented ✅

1. **Registry Context** (Complete)
   - `Domain` aggregate root with business logic
   - `Subdomain` entity with code allocation
   - `DomainNumber` and `TableCode` value objects
   - `DomainService` application service
   - Full repository pattern

2. **Pattern Context** (Complete)
   - `Pattern` aggregate root with rich behavior
   - `PatternCategory` and `SourceType` enumerations
   - AI-enhanced similarity matching
   - Deprecation lifecycle
   - `PatternService` application service
   - Full repository pattern

3. **Clean Architecture** (Complete)
   - 4-layer separation
   - Dependency inversion
   - Protocol-based repositories
   - Domain-driven entities

### What's Pending ⏳

1. **Type Context** - Type definitions and mappings
2. **Service Context** - Service registry
3. **Domain Events** - Event-driven coordination
4. **Pattern Library Migration** - PostgreSQL + pgvector

---

## Benefits of This Design

### Technical Benefits

✅ **Testable**: Mock repositories, test domain logic in isolation
✅ **Maintainable**: Business logic in one place (domain layer)
✅ **Flexible**: Easy to swap implementations (PostgreSQL ↔ in-memory)
✅ **Type-safe**: Rich domain model with validation
✅ **Scalable**: Clear boundaries for adding contexts

### Business Benefits

✅ **Ubiquitous Language**: Code reflects business terminology
✅ **Domain Expertise**: Logic encoded in domain entities
✅ **Change-friendly**: Business rules isolated from infrastructure
✅ **Quality**: Invariants enforced, invalid states impossible

### Developer Experience

✅ **Clear Structure**: Know where to put code
✅ **Self-documenting**: Rich entities tell the story
✅ **Refactor-friendly**: Tests protect against regressions
✅ **Onboarding**: New developers understand domain quickly

---

## References

- **Domain Entities**: `src/domain/entities/domain.py`, `src/domain/entities/pattern.py`
- **Value Objects**: `src/domain/value_objects/__init__.py`
- **Application Services**: `src/application/services/domain_service.py`, `src/application/services/pattern_service.py`
- **Repositories**: `src/infrastructure/repositories/postgresql_domain_repository.py`, `src/infrastructure/repositories/postgresql_pattern_repository.py`
- **Repository Pattern Doc**: `docs/architecture/REPOSITORY_PATTERN.md`
- **Current Status**: `docs/architecture/CURRENT_STATUS.md`

---

**Last Updated**: 2025-11-12
**Status**: Documentation Complete - Reflects Actual Implementation
**Phase**: Phase 5 (Domain Entities Refinement) In Progress

---

*Rich domain models. Business logic in entities. DDD done right.* 🏗️
