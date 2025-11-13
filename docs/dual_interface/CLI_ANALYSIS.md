# Current CLI Structure Analysis

**Date**: 2025-11-12
**Purpose**: Analyze current CLI implementation before refactoring
**Goal**: Identify business logic to extract into service layer

---

## Current CLI Commands

### Domain Management (`src/cli/domain.py`)

```python
# Current implementation (mixed concerns)
@click.command()
@click.option('--number', type=int, required=True)
@click.option('--name', type=str, required=True)
@click.option('--schema-type', type=click.Choice(['framework', 'multi_tenant', 'shared']))
def register_domain(number: int, name: str, schema_type: str):
    """Register a new domain"""
    # Database connection (infrastructure)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Business logic (should be in service layer)
        if number < 1 or number > 255:
            raise ValueError("Domain number must be between 1 and 255")

        # Database operation (should be in repository)
        cur.execute("""
            INSERT INTO specql_registry.tb_domain
            (domain_number, domain_name, description, schema_type)
            VALUES (%s, %s, %s, %s)
            RETURNING pk_domain, id, identifier
        """, (number, name, None, schema_type))

        result = cur.fetchone()
        conn.commit()

        # Presentation (CLI output)
        click.echo(f"✅ Domain registered: {result['identifier']}")

    except psycopg2.IntegrityError as e:
        conn.rollback()
        click.echo(f"❌ Error: Domain {number} already exists", err=True)
        sys.exit(1)
    finally:
        cur.close()
        conn.close()
```

**Problems**:
1. Business logic mixed with CLI presentation
2. Database operations directly in CLI command
3. Error handling tied to CLI output
4. No reusability (can't call from GraphQL)
5. Testing requires mocking CLI framework

**Current Commands**:
- `specql domain register` - Register new domain
- `specql domain list` - List all domains
- `specql domain show` - Show domain details
- `specql subdomain register` - Register subdomain
- `specql subdomain list` - List subdomains
- `specql patterns search` - Search patterns
- `specql patterns apply` - Apply pattern to entity

---

## Target Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────┐
│  Presentation Layer                             │
│  ├── CLI (thin wrappers)                        │
│  │   └── 10-line commands calling services      │
│  └── GraphQL (resolvers)                        │
│      └── Thin resolvers calling same services   │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓ Both call
┌──────────────────▼──────────────────────────────┐
│  Application Layer (Services)                   │
│  ├── DomainService                              │
│  │   ├── register_domain()                      │
│  │   ├── list_domains()                         │
│  │   └── get_domain()                           │
│  ├── PatternService                             │
│  └── EntityService                              │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌──────────────────▼──────────────────────────────┐
│  Domain Layer (Business Logic)                  │
│  ├── Domain (aggregate)                         │
│  ├── Pattern (aggregate)                        │
│  └── Business rules & validation                │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌──────────────────▼──────────────────────────────┐
│  Infrastructure Layer                           │
│  ├── PostgreSQLDomainRepository                 │
│  ├── PostgreSQLPatternRepository                │
│  └── Database connections                       │
└─────────────────────────────────────────────────┘
```

---

## Refactoring Strategy

### Phase 1: Extract Service Layer

**Current** (70 lines in CLI):
```python
# src/cli/domain.py
@click.command()
def register_domain(...):
    # 70 lines of mixed concerns
    # - CLI argument parsing
    # - Validation
    # - Database operations
    # - Error handling
    # - CLI output
```

**Target** (10 lines in CLI, 60 lines in service):
```python
# src/cli/domain.py (presentation)
@click.command()
def register_domain(number, name, schema_type):
    """Register a new domain"""
    try:
        result = domain_service.register_domain(number, name, schema_type)
        click.echo(f"✅ Domain registered: {result.identifier}")
    except DomainAlreadyExistsError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

# src/application/services/domain_service.py (business logic)
class DomainService:
    def __init__(self, repository: DomainRepository):
        self.repository = repository

    def register_domain(
        self,
        domain_number: int,
        domain_name: str,
        schema_type: str
    ) -> Domain:
        """Register a new domain (business logic)"""
        # Validation
        domain_number_vo = DomainNumber(domain_number)

        # Check uniqueness
        if self.repository.exists(domain_number):
            raise DomainAlreadyExistsError(domain_number)

        # Create domain aggregate
        domain = Domain(
            domain_number=domain_number_vo,
            domain_name=domain_name,
            schema_type=schema_type
        )

        # Persist
        self.repository.save(domain)

        return domain
```

---

## Commands to Refactor

### High Priority (Week 5)
1. ✅ `domain register` - Domain registration
2. ✅ `domain list` - List domains
3. ✅ `domain show` - Show domain details
4. ✅ `subdomain register` - Subdomain registration
5. ✅ `subdomain list` - List subdomains

### Medium Priority (Week 6)
6. ✅ `patterns search` - Pattern search
7. ✅ `patterns apply` - Apply pattern
8. ✅ `generate` - Schema generation (already modular)

### Low Priority (Future)
9. ⏳ `validate` - Validation (already modular)
10. ⏳ `diff` - Schema diff (already modular)

---

## Benefits of Refactoring

### 1. Code Reusability
**Before**: Business logic locked in CLI commands
**After**: Services callable from CLI, GraphQL, tests, scripts

### 2. Testing
**Before**: Must mock Click framework, database connections
**After**: Test services directly with in-memory repositories

### 3. API Access
**Before**: Only CLI access to registry
**After**: CLI **and** GraphQL access to same functionality

### 4. Maintainability
**Before**: 70-line CLI commands with mixed concerns
**After**: 10-line CLI wrappers + 60-line services with clear responsibilities

### 5. Error Handling
**Before**: CLI-specific error messages
**After**: Business exceptions, presentation layer formats for CLI/GraphQL

---

## Refactoring Timeline

### Week 5 Day 1 (Today)
- ✅ Analyze current CLI structure
- ✅ Document refactoring strategy
- ✅ Create service layer structure

### Week 5 Day 2
- Extract DomainService from CLI
- Extract SubdomainService from CLI
- Update CLI to thin wrappers
- All tests passing

### Week 5 Day 3
- Create presentation layer structure
- Move CLI commands to `src/presentation/cli/`
- Verify no regressions

### Week 5 Days 4-5
- Design GraphQL schema
- Create resolver foundations
- Implement basic GraphQL queries

---

## Success Metrics

### Code Metrics
- **CLI Command Size**: 70 lines → 10 lines (85% reduction)
- **Service Layer**: 0 lines → 300+ lines (new, reusable)
- **Test Coverage**: CLI tests → Service tests (faster, more reliable)

### Architectural Metrics
- **Separation of Concerns**: ✅ Clear layer boundaries
- **Dependency Inversion**: ✅ Services depend on repository protocols
- **Reusability**: ✅ Services callable from CLI, GraphQL, tests

---

**Status**: Analysis complete
**Next**: Extract service layer (Day 2)