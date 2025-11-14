# Repository Structure - Parallelization Guide

**Project**: PrintOptim Backend - SpecQL Schema Generator
**Date**: November 8, 2025
**Purpose**: Organize codebase for maximum team parallelization

---

## 🎯 Parallelization Strategy

This repository is organized into **5 independent work streams** that can be developed in parallel:

1. **Core Parser** (Team A) - SpecQL YAML parsing
2. **SQL Generators** (Team B) - Table/function/view generation
3. **Numbering System** (Team C) - Hierarchical organization
4. **Integration Layer** (Team D) - FraiseQL + TestFoundry
5. **Tooling & CLI** (Team E) - Developer tools

Each stream has:
- ✅ **Clear interfaces** - Well-defined APIs between components
- ✅ **Independent tests** - Can test in isolation
- ✅ **Mock data** - Fixtures for integration testing
- ✅ **Minimal dependencies** - Reduced blocking

---

## 📁 Directory Structure

```
printoptim_backend_poc/
│
├── README.md                           # Quick start guide
├── CONTRIBUTING.md                     # Development guidelines
├── pyproject.toml                      # Python dependencies
├── .gitignore                          # Git ignore patterns
├── Makefile                            # Common commands
│
├── docs/                               # 📚 Documentation
│   ├── architecture/
│   │   ├── IMPLEMENTATION_PLAN_SPECQL.md
│   │   ├── INTEGRATION_PROPOSAL.md
│   │   └── SPECQL_BUSINESS_LOGIC_REFINED.md
│   ├── analysis/
│   │   ├── TEMPLATING_SYSTEM_ANALYSIS.md
│   │   ├── FRAISEQL_INTEGRATION_REQUIREMENTS.md
│   │   └── COMPLEX_BUSINESS_LOGIC_YAML_ANALYSIS.md
│   ├── guides/
│   │   ├── getting-started.md
│   │   ├── writing-entities.md
│   │   └── specql-dsl-reference.md
│   └── adr/                            # Architecture Decision Records
│       ├── 001-specql-vs-manual-sql.md
│       └── 002-numbering-system.md
│
├── src/                                # 🔧 Source Code
│   ├── __init__.py
│   │
│   ├── core/                           # TEAM A: Core Parser
│   │   ├── __init__.py
│   │   ├── specql_parser.py            # SpecQL YAML → AST
│   │   ├── ast_models.py               # Data classes (Entity, Action, etc.)
│   │   ├── validators.py               # Business rule validation
│   │   └── expression_parser.py        # Parse SpecQL expressions
│   │
│   ├── generators/                     # TEAM B: SQL Generators
│   │   ├── __init__.py
│   │   ├── table_generator.py          # Trinity pattern tables
│   │   ├── view_generator.py           # FraiseQL views
│   │   ├── function_generator.py       # CRUD functions
│   │   ├── action_generator.py         # SpecQL action → SQL
│   │   ├── trigger_generator.py        # Group leader triggers
│   │   └── sql_utils.py                # SQL formatting utilities
│   │
│   ├── numbering/                      # TEAM C: Numbering System
│   │   ├── __init__.py
│   │   ├── numbering_parser.py         # Parse 6-digit codes
│   │   ├── directory_generator.py      # Create hierarchy
│   │   ├── manifest_generator.py       # Execution order manifest
│   │   └── dependency_resolver.py      # Topological sort
│   │
│   ├── integration/                    # TEAM D: Integration Layer
│   │   ├── __init__.py
│   │   ├── fraiseql_adapter.py         # FraiseQL COMMENT annotations
│   │   ├── testfoundry_adapter.py      # TestFoundry metadata
│   │   ├── graphql_schema_gen.py       # GraphQL schema generation
│   │   └── typescript_gen.py           # TypeScript type generation
│   │
│   ├── agents/                         # TEAM D: AI Agent Runtime (Phase 4)
│   │   ├── __init__.py
│   │   ├── agent_runtime.py            # Agent sandbox
│   │   ├── llm_integration.py          # OpenAI/Anthropic
│   │   └── event_observer.py           # Event triggering
│   │
│   ├── cli/                            # TEAM E: CLI Tools
│   │   ├── __init__.py
│   │   ├── generate.py                 # Main generation CLI
│   │   ├── validate.py                 # YAML validation CLI
│   │   ├── migrate.py                  # SQL → YAML migration
│   │   ├── healthcheck.py              # Health check system
│   │   └── diff.py                     # Schema diff tool
│   │
│   └── utils/                          # Shared Utilities
│       ├── __init__.py
│       ├── yaml_loader.py              # YAML loading with validation
│       ├── file_utils.py               # File I/O helpers
│       ├── sql_formatter.py            # SQL pretty-printing
│       └── logger.py                   # Logging configuration
│
├── tests/                              # 🧪 Test Suite
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   │
│   ├── unit/                           # Unit tests (fast, isolated)
│   │   ├── core/
│   │   │   ├── test_specql_parser.py
│   │   │   ├── test_ast_models.py
│   │   │   └── test_validators.py
│   │   ├── generators/
│   │   │   ├── test_table_generator.py
│   │   │   ├── test_action_generator.py
│   │   │   └── test_trigger_generator.py
│   │   ├── numbering/
│   │   │   ├── test_numbering_parser.py
│   │   │   └── test_manifest_generator.py
│   │   └── integration/
│   │       ├── test_fraiseql_adapter.py
│   │       └── test_testfoundry_adapter.py
│   │
│   ├── integration/                    # Integration tests (slower)
│   │   ├── test_end_to_end_generation.py
│   │   ├── test_database_execution.py
│   │   └── test_graphql_integration.py
│   │
│   ├── fixtures/                       # Test data
│   │   ├── entities/
│   │   │   ├── simple_contact.yaml
│   │   │   ├── complex_reservation.yaml
│   │   │   └── with_agents.yaml
│   │   ├── expected_sql/
│   │   │   ├── contact_table.sql
│   │   │   └── contact_create_function.sql
│   │   └── mock_schemas/
│   │       └── existing_database.sql
│   │
│   └── benchmarks/                     # Performance tests
│       ├── test_parser_performance.py
│       └── test_generation_speed.py
│
├── templates/                          # 📝 Jinja2 Templates
│   ├── sql/
│   │   ├── table.sql.j2                # Trinity pattern table
│   │   ├── view.sql.j2                 # FraiseQL view
│   │   ├── function_crud.sql.j2        # CRUD functions
│   │   ├── action_function.sql.j2      # SpecQL action function
│   │   ├── group_leader_trigger.sql.j2 # Group leader triggers
│   │   └── testfoundry_metadata.sql.j2 # TestFoundry metadata
│   │
│   ├── graphql/
│   │   ├── type.graphql.j2             # GraphQL type
│   │   └── mutation.graphql.j2         # GraphQL mutation
│   │
│   ├── typescript/
│   │   ├── entity_type.ts.j2           # TypeScript entity
│   │   └── api_client.ts.j2            # API client
│   │
│   └── docs/
│       ├── entity_readme.md.j2         # Entity README
│       └── api_docs.md.j2              # API documentation
│
├── entities/                           # 📦 Entity Definitions
│   ├── examples/                       # Example entities
│   │   ├── contact.yaml                # CRM contact
│   │   ├── manufacturer.yaml           # Existing POC entity
│   │   ├── reservation.yaml            # Complex temporal logic
│   │   └── machine_item.yaml           # Complex workflow
│   │
│   └── schemas/                        # JSON schemas for validation
│       └── specql_entity_schema.json   # JSON Schema for SpecQL YAML
│
├── generated/                          # 🎨 Generated Output
│   ├── .gitignore                      # Ignore generated files
│   ├── manifest.yaml                   # Execution order
│   ├── README.md                       # Auto-generated overview
│   │
│   ├── 01_write_side/                  # Schema layer 01
│   │   └── 013_catalog/
│   │       └── 0132_manufacturer/
│   │           └── 01321_manufacturer/
│   │               ├── README.md
│   │               ├── 013211_tb_manufacturer.sql
│   │               ├── 013212_fn_manufacturer_pk.sql
│   │               └── 013213_fn_manufacturer_id.sql
│   │
│   ├── 02_query_side/                  # Schema layer 02
│   │   └── 023_catalog/
│   │       └── 0232_manufacturer/
│   │           └── 02321_manufacturer/
│   │               └── 023211_v_manufacturer.sql
│   │
│   ├── 03_functions/                   # Schema layer 03
│   │   └── 033_catalog/
│   │       └── 0332_manufacturer/
│   │           └── 03321_manufacturer_mutations/
│   │               ├── 033211_fn_create_manufacturer.sql
│   │               └── 033212_fn_update_manufacturer.sql
│   │
│   └── 09_testfoundry/                 # Schema layer 09
│       └── 093_catalog/
│           └── 0932_manufacturer/
│               └── 09321_manufacturer_tests/
│                   └── 093211_metadata_mappings.sql
│
├── scripts/                            # 🛠️ Development Scripts
│   ├── setup_dev.sh                    # Setup development environment
│   ├── run_tests.sh                    # Run test suite
│   ├── apply_manifest.py               # Apply SQL to database
│   ├── validate_all.sh                 # Run all validators
│   └── benchmark.py                    # Performance benchmarking
│
├── database/                           # 🗄️ Database Utilities
│   ├── migrations/                     # Database migrations
│   ├── seed_data/                      # Seed data for testing
│   └── test_db_setup.sql               # Test database schema
│
└── .github/                            # 🤖 CI/CD
    └── workflows/
        ├── test.yml                    # Run tests on PR
        ├── lint.yml                    # Code quality checks
        └── benchmark.yml               # Performance regression tests
```

---

## 🔀 Work Stream Dependencies

### Stream Dependency Graph

```
┌─────────────────┐
│   TEAM A        │
│  Core Parser    │
│  (src/core/)    │
└────────┬────────┘
         │
         │ Provides: Entity AST
         │
    ┌────┴──────────────────┬──────────────────┬─────────────┐
    ▼                       ▼                  ▼             ▼
┌─────────────┐    ┌────────────────┐  ┌──────────────┐  ┌──────────┐
│  TEAM B     │    │   TEAM C       │  │   TEAM D     │  │ TEAM E   │
│SQL Gens     │    │   Numbering    │  │ Integration  │  │  CLI     │
│(generators/)│    │  (numbering/)  │  │(integration/)│  │  (cli/)  │
└─────────────┘    └────────────────┘  └──────────────┘  └──────────┘
     │                      │                  │                │
     └──────────────────────┴──────────────────┴────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  Integration   │
                   │  (Week 2-3)    │
                   └────────────────┘
```

### Phase 1 (Week 1-2): Parallel Development

| Team | Component | Deliverable | Depends On |
|------|-----------|-------------|------------|
| **A** | Core Parser | Entity AST, Validators | None ✅ |
| **B** | SQL Generators | Table/Function templates | None ✅ (uses mock AST) |
| **C** | Numbering System | Directory hierarchy | None ✅ (standalone) |
| **D** | FraiseQL Adapter | COMMENT annotations | None ✅ (uses mock AST) |
| **E** | CLI Tools | Basic CLI structure | None ✅ (uses mocks) |

**All teams can start Day 1** with mock interfaces!

### Phase 2 (Week 3): Integration

| Team | Task | Integration Point |
|------|------|-------------------|
| **A+B** | Parser → Generators | Entity AST → SQL |
| **A+C** | Parser → Numbering | Entity metadata → Paths |
| **B+D** | Generators → FraiseQL | SQL → COMMENT annotations |
| **E** | CLI → All | Orchestrate full pipeline |

---

## 🔧 Interface Contracts

### 1. Core Parser → SQL Generators

**Interface**: `Entity` AST

```python
# src/core/ast_models.py
@dataclass
class Entity:
    name: str
    schema: str
    fields: Dict[str, FieldDefinition]
    actions: List[Action]
    # ... etc
```

**Contract**: All generators consume `Entity` AST, never raw YAML.

**Mock for Team B**:
```python
# tests/fixtures/mock_entities.py
def mock_contact_entity() -> Entity:
    return Entity(
        name='Contact',
        schema='crm',
        fields={'email': FieldDefinition(name='email', type='text')},
        actions=[]
    )
```

---

### 2. SQL Generators → Numbering System

**Interface**: File metadata

```python
# src/generators/base.py
@dataclass
class GeneratedFile:
    table_code: str
    entity_name: str
    file_type: str  # 'table', 'view', 'function'
    content: str
    dependencies: List[str]
```

**Contract**: Generators return `GeneratedFile` objects with numbering metadata.

---

### 3. Numbering System → File System

**Interface**: Directory paths

```python
# src/numbering/numbering_parser.py
class NumberingParser:
    def generate_file_path(
        self,
        table_code: str,
        entity_name: str,
        file_type: str
    ) -> str:
        """Returns: 01_write_side/.../013211_tb_manufacturer.sql"""
```

**Contract**: Pure function, no side effects.

---

### 4. All Components → Manifest

**Interface**: Manifest entries

```python
# src/numbering/manifest_generator.py
class ManifestGenerator:
    def add_file(self, file_metadata: Dict) -> None:
        """Add file to execution order"""
```

**Contract**: Thread-safe accumulator pattern.

---

## 🧪 Testing Strategy for Parallelization

### Unit Tests (Each team independently)

```bash
# Team A
uv run pytest tests/unit/core/ -v

# Team B
uv run pytest tests/unit/generators/ -v

# Team C
uv run pytest tests/unit/numbering/ -v

# Team D
uv run pytest tests/unit/integration/ -v

# Team E
uv run pytest tests/unit/cli/ -v
```

### Integration Tests (Week 3)

```bash
# End-to-end pipeline
uv run pytest tests/integration/test_end_to_end_generation.py -v

# Database execution
uv run pytest tests/integration/test_database_execution.py -v --db=postgres://localhost/test
```

---

## 📦 Development Workflow

### Day 1 Setup (All Teams)

```bash
# Clone and setup
git clone <repo>
cd printoptim_backend_poc

# Create virtual environment
uv venv
source .venv/bin/activate  # or `.venv/bin/activate.fish` on fish shell

# Install dependencies
uv pip install -e ".[dev]"

# Verify setup
make test
```

### Daily Development (Each Team)

```bash
# Create feature branch
git checkout -b teamA/specql-parser

# Write tests (RED phase)
vim tests/unit/core/test_specql_parser.py

# Run tests (should fail)
uv run pytest tests/unit/core/ -v

# Implement feature (GREEN phase)
vim src/core/specql_parser.py

# Run tests (should pass)
uv run pytest tests/unit/core/ -v

# Refactor (REFACTOR phase)
vim src/core/specql_parser.py

# Final QA
make lint
make test
make typecheck

# Commit and push
git add .
git commit -m "feat(core): implement SpecQL parser"
git push origin teamA/specql-parser

# Create PR
gh pr create --title "SpecQL Parser Implementation"
```

### Integration Day (Week 3)

```bash
# Merge all feature branches
git checkout main
git merge teamA/specql-parser
git merge teamB/sql-generators
git merge teamC/numbering-system
git merge teamD/fraiseql-adapter
git merge teamE/cli-tools

# Run integration tests
uv run pytest tests/integration/ -v

# Fix integration issues
# ... debug and fix

# Tag release
git tag v0.1.0-alpha
git push --tags
```

---

## 🎯 Team Assignments

### Team A: Core Parser (src/core/)
**Skills**: Python, YAML, AST design
**Priority**: Critical path - everyone depends on this
**Deliverables**:
- [ ] `specql_parser.py` - Parse YAML to AST
- [ ] `ast_models.py` - Entity, Action, Field dataclasses
- [ ] `validators.py` - Business rule validation
- [ ] `expression_parser.py` - Parse SpecQL expressions

**Estimated**: 50 hours (2 developers × 1 week)

---

### Team B: SQL Generators (src/generators/)
**Skills**: PostgreSQL, Jinja2, SQL optimization
**Priority**: High - core functionality
**Deliverables**:
- [ ] `table_generator.py` - Trinity pattern tables
- [ ] `action_generator.py` - SpecQL actions → SQL functions
- [ ] `view_generator.py` - FraiseQL views
- [ ] `trigger_generator.py` - Group leader triggers

**Estimated**: 60 hours (2 developers × 1.5 weeks)

---

### Team C: Numbering System (src/numbering/)
**Skills**: Python, file systems, graph algorithms
**Priority**: Medium - can integrate later
**Deliverables**:
- [ ] `numbering_parser.py` - Parse 6-digit codes
- [ ] `directory_generator.py` - Create hierarchy
- [ ] `manifest_generator.py` - Execution order
- [ ] `dependency_resolver.py` - Topological sort

**Estimated**: 40 hours (1 developer × 2 weeks)

---

### Team D: Integration Layer (src/integration/)
**Skills**: GraphQL, FraiseQL, TypeScript
**Priority**: Medium - nice-to-have for Phase 1
**Deliverables**:
- [ ] `fraiseql_adapter.py` - COMMENT annotations
- [ ] `testfoundry_adapter.py` - Test metadata
- [ ] `graphql_schema_gen.py` - GraphQL schema
- [ ] `typescript_gen.py` - TypeScript types

**Estimated**: 50 hours (2 developers × 1 week)

---

### Team E: CLI & Tooling (src/cli/)
**Skills**: Python CLI, DevOps, documentation
**Priority**: Medium - developer experience
**Deliverables**:
- [ ] `generate.py` - Main generation CLI
- [ ] `validate.py` - YAML validation
- [ ] `healthcheck.py` - Health checks
- [ ] `migrate.py` - SQL → YAML migration

**Estimated**: 40 hours (1 developer × 2 weeks)

---

## 📊 Progress Tracking

### Week 1 Goals

- [ ] **Team A**: Parser parses simple entities (contact.yaml)
- [ ] **Team B**: Generates tables and basic CRUD functions
- [ ] **Team C**: Numbering parser works, creates directories
- [ ] **Team D**: FraiseQL annotations generated
- [ ] **Team E**: CLI scaffolding complete

### Week 2 Goals

- [ ] **Team A**: Parser handles complex entities (reservation.yaml)
- [ ] **Team B**: SpecQL action steps compile to SQL
- [ ] **Team C**: Manifest generator with dependency resolution
- [ ] **Team D**: GraphQL schema generation
- [ ] **Team E**: Validation and health checks working

### Week 3 Goals (Integration)

- [ ] **All teams**: Integration tests passing
- [ ] **All teams**: End-to-end demo (YAML → SQL → Database)
- [ ] **All teams**: Documentation complete
- [ ] **Release**: v0.1.0-alpha

---

## 🚀 Quick Start Commands

### Generate from YAML
```bash
python -m src.cli.generate --entity entities/examples/contact.yaml
```

### Validate YAML
```bash
python -m src.cli.validate entities/examples/*.yaml
```

### Apply to Database
```bash
python scripts/apply_manifest.py generated/manifest.yaml --db postgres://localhost/printoptim
```

### Run Tests
```bash
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
```

### Health Check
```bash
python -m src.cli.healthcheck generated/
```

---

## 📝 Git Strategy

### Branch Naming
- `main` - Stable releases
- `develop` - Integration branch
- `teamA/<feature>` - Team A features
- `teamB/<feature>` - Team B features
- etc.

### PR Requirements
- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: uv pip install -e ".[dev]"
      - run: make test
      - run: make lint
      - run: make typecheck
```

---

**This structure enables 5 teams to work in parallel with minimal blocking!** 🚀
