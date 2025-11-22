# Claude Code Instructions - SpecQL Code Generator

**Project**: Business YAML → Production PostgreSQL + GraphQL API
**Status**: ✅ **100% Complete** - All CLI commands stable and fully functional
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

**Status**: ✅ Complete (Redesigned with unified command structure)
**Tests**: `tests/unit/cli/` - 60 passing tests

**CLI Structure**:
```
specql (v2.0)
├── generate <files>              # Primary: YAML → SQL/Frontend (Stable)
│   ├── --foundation-only        # Only app foundation
│   ├── --actions-only           # Only PL/pgSQL functions
│   ├── --frontend=<dir>         # TypeScript + Apollo
│   ├── --with-impacts           # Generate mutation impacts
│   └── --dry-run                # Preview mode
│
├── validate <files>              # Validate YAML (Stable)
│   └── --strict                 # Treat warnings as errors
│
├── reverse <subcommand>          # Reverse engineering group
│   ├── sql <files>              # SQL → YAML (Stable - full pglast)
│   ├── python <files>           # Django/FastAPI → YAML (Stable)
│   ├── typescript <files>       # Prisma/TypeORM → YAML (Stable)
│   ├── rust <files>             # Diesel/SeaORM → YAML (Stable)
│   ├── java <files>             # JPA/Hibernate → YAML (Stable)
│   └── project <dir>            # Auto-detect & process (Beta)
│
├── patterns detect|apply         # Pattern operations (Beta)
├── init project|entity|registry  # Scaffolding (Beta)
├── workflow migrate|sync         # Multi-step automation (Beta)
├── diff                          # Schema diffing (Stable - 7 tests)
├── docs                          # Documentation generation (Stable - 17 tests)
│
└── test <subcommand>             # Testing tools (Stable - 19 tests)
    ├── seed <entities>           # Generate seed data SQL
    ├── generate <entities>       # Auto-generate pgTAP/pytest tests
    └── reverse <test-files>      # Reverse engineer existing tests
```

**Usage Examples**:
```bash
# Generate schema from SpecQL
specql generate entities/contact.yaml

# Reverse engineer SQL to YAML
specql reverse sql db/tables/*.sql -o entities/

# Auto-detect and migrate a project
specql workflow migrate ./my-django-app -o migration/

# Validate SpecQL syntax
specql validate entities/*.yaml

# Create new entity template
specql init entity Contact --schema=crm

# Show schema diff
specql diff entities/contact.yaml --compare db/schema/10_tables/contact.sql

# Generate test seed data
specql test seed entities/*.yaml -o seeds/ --deterministic

# Auto-generate pgTAP/pytest tests
specql test generate entities/*.yaml -o tests/ --with-seed
```

**Key Files** (`src/cli/`):
- `main.py` - Unified CLI entry point
- `base.py` - Shared options (`@common_options`) and utilities
- `orchestrator.py` - Coordinates all generators
- `commands/` - Command implementations by group
- `utils/error_handler.py` - Unified error handling

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
├── cli/               # Team E: CLI ✅ (Redesigned)
│   ├── main.py        # Unified entry point
│   ├── base.py        # Shared options
│   ├── commands/      # Command implementations
│   │   ├── generate.py
│   │   ├── reverse/   # sql, python, typescript, rust, project
│   │   ├── patterns/  # detect, apply
│   │   ├── init/      # project, entity, registry
│   │   └── workflow/  # migrate, sync
│   └── utils/         # Error handling, output formatting
└── registry/          # Schema registry ✅

tests/
├── unit/              # All passing
│   └── cli/           # 60 CLI tests
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

**Current Status**: v0.8.6 - All CLI commands implemented and tested

**Recent Changes** (2025-11-22 - v0.8.6):
- ✅ **Reverse Engineering Improvements** - Major enhancements to SQL → YAML
  - YAML filenames now use proper snake_case (`machine_contract_relationship.yaml`)
  - SQL `COMMENT ON` statements preserved as entity/field descriptions
  - `project.yaml` auto-generated with schemas, extensions, registry
  - Hierarchical numbering preserved from source files
  - FK fields properly renamed (`fk_company` → `company: ref(...)`)
- ✅ **Documentation Cleanup** - Removed 83 obsolete markdown files (-18%)
  - Root: 56 → 5 files (kept README, CHANGELOG, CONTRIBUTING, GETTING_STARTED, STYLE_GUIDE)
  - docs/: 35 → 14 files (removed planning docs, kept architecture/reference)
  - .claude/prompts/: Removed 7 obsolete team prompt files
- ✅ New files: `core/project_config.py`, `generators/foundation_generator.py`
- ✅ Database test fixtures now use environment variables (configurable)
- ✅ Fixed schema deployment in test fixtures (always refresh for consistency)
- ✅ 1624 tests passing

**Previous** (2025-11-22 - v0.8.5):
- ✅ `test seed` command for type-aware seed data generation (6 tests)
- ✅ `test generate` command for auto-generating pgTAP/pytest tests (6 tests)
- ✅ `test reverse` command for reverse engineering existing tests (7 tests)

**Previous** (2025-11-21 - v0.8.4):
- ✅ `docs` command implemented with multi-format support (17 tests)
- ✅ `reverse java` command integrated with JPA/Hibernate parser (17 tests)
- ✅ `reverse sql` command integrated with pglast (17 tests)
- ✅ `reverse python` command integrated with PythonASTParser (19 tests)
- ✅ `reverse typescript` command integrated with Prisma parser (17 tests)
- ✅ `reverse rust` command integrated with Diesel/SeaORM parsers (16 tests)

**Test Command**: `make test` or `uv run pytest tests/unit/cli/ -v`

**Key Principle**: Keep SpecQL lightweight - business domain ONLY, framework handles ALL technical details

**When in Doubt**: Move complexity to framework, not user YAML

---

## 📚 Essential Docs

- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Full DSL spec
- `docs/architecture/INTEGRATION_PROPOSAL.md` - Framework conventions
- `docs/architecture/ONE_FILE_PER_MUTATION_PATTERN.md` - File organization
- `docs/06_reference/cli-commands.md` - CLI command reference (aligned)
- `docs/06_reference/cli-status.md` - CLI implementation status
- `GETTING_STARTED.md` - Quick start guide

---

**Last Updated**: 2025-11-22
**Version**: 0.8.6
**Project Phase**: CLI Implementation Complete (100%)
**Next Milestone**: Real-world migration testing / Performance optimization
