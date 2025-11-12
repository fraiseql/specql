# Claude Code Instructions - SpecQL Code Generator

**Project**: Business YAML → Production PostgreSQL + GraphQL API
**Status**: ✅ **Production Ready** - Core features implemented and tested
**Goal**: 20 lines YAML → 2000+ lines production code (100x leverage)

---

## 🎯 Core Principle

**Users write ONLY business domain in YAML. Framework auto-generates ALL technical implementation.**

**Input** (20 lines):
```yaml
entity: Contact
schema: crm
fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified)
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Output** (2000+ lines auto-generated):
- PostgreSQL tables (Trinity pattern: pk_*, id, identifier)
- Foreign keys, indexes, constraints
- PL/pgSQL functions with audit trails
- FraiseQL metadata for GraphQL discovery
- TypeScript types & Apollo hooks

---

## 🏗️ Architecture

```
SpecQL YAML → Team A (Parser) → AST
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
Team B      Team C      Team D
Schema      Actions     FraiseQL
Generator   Compiler    Metadata
    └───────────┼───────────┘
                ↓
            Team E: CLI
                ↓
        PostgreSQL + GraphQL
```

### 🔧 Core Protocols

**FileSpec**: Standard file specification for generation
```python
@dataclass
class FileSpec:
    code: str      # Table/view code (6-digit write, 7-digit read)
    name: str      # Filename without extension
    content: str   # Complete file content
    layer: str     # "write_side" or "read_side"
```

**PathGenerator**: Protocol for hierarchical path generation
```python
class PathGenerator(Protocol):
    def generate_path(self, file_spec: FileSpec) -> Path:
        """Generate hierarchical file path from FileSpec"""
```

---

## 👥 TEAMS (✅ = Implemented)

### ✅ Team A: SpecQL Parser (`src/core/`)
**Status**: ✅ Complete
**Tests**: `tests/unit/core/` - All passing

Parses YAML → Business AST:
- Entities, fields (text, integer, ref, enum, list, rich types)
- Actions with steps (validate, if/then, insert, update, call, notify, foreach)
- Impact declarations for mutations
- Table views, hierarchical identifiers

---

### ✅ Team B: Schema Generator (`src/generators/schema/`, `src/generators/`)
**Status**: ✅ Complete
**Tests**: `tests/unit/schema/`, `tests/unit/generators/` - All passing

Generates PostgreSQL DDL with **automatic conventions**:
1. **Trinity Pattern**: `pk_*` (INTEGER PK), `id` (UUID), `identifier` (TEXT)
2. **Naming**: `tb_{entity}` tables, `fk_{entity}` foreign keys
3. **Audit Fields**: `created_at`, `updated_at`, `deleted_at`
4. **Auto-Indexes**: FK columns, enum fields, tenant_id
5. **Composite Types**: Rich types (money, dimensions, contact_info)
6. **Schema Registry**: Configurable multi-tenant vs shared schemas

**Key Files**:
- `schema_orchestrator.py` - Orchestrates full schema generation
- `table_generator.py` - DDL generation
- `trinity_helper_generator.py` - Helper functions (entity_pk, entity_id, entity_identifier)
- `composite_type_generator.py` - Rich type handling
- `comment_generator.py` - PostgreSQL comments

### ✅ Hierarchical File Generation
**Status**: ✅ Complete (Week 1)
**Files**: `hierarchical_file_writer.py`, `write_side_path_generator.py`, `read_side_path_generator.py`

Unified file writer for both write-side and read-side with:
1. **Protocol-based design**: `PathGenerator` protocol for flexible path generation
2. **Hierarchical paths**: Domain/subdomain/entity layered structure
3. **Dry-run support**: Preview file operations without writing
4. **Registry integration**: Dynamic codes from domain registry

**Example**:
```bash
# Generate hierarchical structure
specql generate entities/*.yaml --hierarchical

# Output structure:
0_schema/
├── 01_write_side/
│   ├── 012_crm/
│   │   ├── 0123_customer/
│   │   │   ├── 01236_contact/
│   │   │   │   └── 012361_tb_contact.sql
│   │   │   └── 012362_tb_company.sql
│   │   └── 0124_sales/
│   │       └── ...
└── 02_query_side/
    ├── 022_crm/
    │   ├── 0223_customer/
    │   │   ├── 0220310_tv_contact.sql
    │   │   └── 0220320_tv_company.sql
    │   └── ...
```

---

### ✅ Team C: Action Compiler (`src/generators/actions/`)
**Status**: ✅ Complete
**Tests**: `tests/unit/actions/`, `tests/integration/actions/` - All passing

Compiles SpecQL actions → PL/pgSQL functions with:
1. **FraiseQL Standard**: Returns `app.mutation_result` type
2. **Trinity Resolution**: Auto-convert UUID → INTEGER
3. **Audit Updates**: Auto-update `updated_at`, `updated_by`
4. **Error Handling**: Typed errors with proper status codes
5. **Full Object Returns**: Complete entities in `object_data`
6. **Impact Metadata**: Runtime `_meta` with side effects tracking
7. **Composite Type Support**: Type-safe metadata using PostgreSQL types

**Step Compilers** (`src/generators/actions/step_compilers/`):
- `validate_step.py` - Validation logic
- `if_step.py` - Conditional branching
- `insert_step.py` - INSERT operations
- `update_step.py` - UPDATE operations
- `call_step.py` - Function calls
- `notify_step.py` - Notifications
- `foreach_step.py` - Loops

**Key Files**:
- `action_orchestrator.py` - Orchestrates action compilation
- `core_logic_generator.py` - Core business function (`{schema}.{action}`)
- `app_wrapper_generator.py` - GraphQL wrapper (`app.{action}`)
- `expression_compiler.py` - Expression → SQL
- `success_response_generator.py` - Response formatting

---

### ✅ Team D: FraiseQL Metadata (`src/generators/fraiseql/`)
**Status**: ✅ Complete
**Tests**: `tests/unit/fraiseql/`, `tests/integration/fraiseql/` - All passing

Generates:
1. **SQL Comments**: `@fraiseql:*` annotations for auto-discovery
2. **Mutation Impacts**: Static metadata JSON for frontend
3. **TypeScript Types**: Type definitions for mutations
4. **Documentation**: Auto-generated mutation docs

**Key Files**:
- `mutation_annotator.py` - Function annotations
- `table_view_annotator.py` - Table view annotations

**Frontend Codegen** (`src/generators/frontend/`):
- `mutation_impacts_generator.py` - JSON metadata
- `typescript_types_generator.py` - TS type definitions
- `apollo_hooks_generator.py` - Pre-configured Apollo hooks
- `mutation_docs_generator.py` - Markdown documentation

---

### ✅ Team E: CLI & Orchestration (`src/cli/`)

**Status**: ✅ Complete (Confiture Integration)
**Tests**: `tests/unit/cli/` + `tests/integration/test_confiture_integration.py` - All passing

**Commands**:
```bash
# Generate schema from SpecQL
specql generate entities/contact.yaml

# Validate SpecQL syntax
specql validate entities/*.yaml

# Show schema diff
specql diff entities/contact.yaml --compare db/schema/10_tables/contact.sql

# Generate frontend code
specql generate entities/*.yaml --with-impacts --output-frontend=src/generated
```

**Key Files**:
- `orchestrator.py` - Coordinates all generators
- `generate.py` - Generation command
- `validate.py` - Validation command
- `diff.py` - Schema diffing
- `docs.py` - Documentation generation

---

## 🏗️ Schema Organization (3 Tiers)

### Tier 1: Framework Schemas (Universal)
- `common` - Shared reference data
- `app` - GraphQL types (`mutation_result`, composite types)
- `core` - Framework functions

### Tier 2: Multi-Tenant (User-Defined)
- `crm`, `projects`, etc.
- Auto-adds `tenant_id UUID NOT NULL`
- RLS policies enabled

### Tier 3: Shared (User-Defined)
- `catalog`, `analytics`, etc.
- NO `tenant_id` - shared across tenants

**Registry**: `registry/domain_registry.yaml` + `src/registry/domain_registry.py`

---

## 📁 Repository Structure

```
src/
├── core/              # Team A: Parser ✅
├── generators/
│   ├── schema/        # Team B: Schema ✅
│   ├── actions/       # Team C: Actions ✅
│   ├── fraiseql/      # Team D: FraiseQL ✅
│   └── frontend/      # Frontend codegen ✅
├── cli/               # Team E: CLI ✅
└── registry/          # Schema registry ✅

tests/
├── unit/              # Comprehensive unit tests
└── integration/       # E2E tests
```

---

## 🧪 Testing

```bash
# Team-specific tests
make teamA-test   # Parser
make teamB-test   # Schema generator
make teamC-test   # Action compiler
make teamD-test   # FraiseQL
make teamE-test   # CLI

# All tests
make test
```

**TDD Cycle**: RED → GREEN → REFACTOR → QA

---

## 🎯 What Makes SpecQL "Lightweight"

**Users Write** (12 lines):
```yaml
entity: Contact
fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified)
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Framework Auto-Generates**:
- Trinity pattern tables
- Foreign keys & indexes
- Audit fields
- Helper functions
- PL/pgSQL action functions
- FraiseQL metadata
- GraphQL schema
- TypeScript types
- Apollo hooks

**Result**: 99% less code, 100% production-ready

---

## 🚨 Key Constraints

### Users DON'T Write:
- ❌ SQL DDL syntax
- ❌ Foreign key definitions
- ❌ Index definitions
- ❌ PL/pgSQL code
- ❌ GraphQL schema
- ❌ TypeScript types

### Conventions (NOT Configurable):
- ✅ Trinity pattern is ALWAYS applied
- ✅ Naming conventions are ALWAYS applied
- ✅ Index naming: `idx_tb_{entity}_{field}` (tables) / `idx_tv_{entity}_{field}` (views)
- ✅ Audit fields are ALWAYS added
- ✅ Consistency > flexibility

---

## 🤖 AI Quick Reference

**Current Status**: Production ready with comprehensive test coverage

**Test Command**: `make test`

**Key Principle**: Keep SpecQL lightweight - business domain ONLY, framework handles ALL technical details

**Test Command**: `make test`

**Key Principle**: Keep SpecQL lightweight - business domain ONLY, framework handles ALL technical details

**When in Doubt**: Move complexity to framework, not user YAML

---

## 📚 Essential Docs

- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Full DSL spec
- `docs/architecture/INTEGRATION_PROPOSAL.md` - Framework conventions
- `docs/architecture/ONE_FILE_PER_MUTATION_PATTERN.md` - File organization
- `GETTING_STARTED.md` - Quick start guide

---

**Last Updated**: 2025-11-11
**Project Phase**: Production Ready
**Next Milestone**: Community adoption and ecosystem growth
