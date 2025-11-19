# Team E Codebase Exploration Report

**Date**: November 9, 2025
**Scope**: Current state of Team E (CLI & Orchestration + Frontend Codegen) implementation

---

## Executive Summary

Team E is responsible for CLI tools, orchestration, and frontend code generation. The codebase shows:

- **CLI Foundation**: Exists with basic structure (`src/cli/generate.py`)
- **Orchestration**: Partially implemented (SchemaOrchestrator in place)
- **Frontend Codegen**: Not yet implemented
- **Documentation**: Comprehensive but plan-based (not yet executed)
- **Tests**: No Team E-specific tests yet (directory doesn't exist)

### Current State Matrix

| Component | Status | Completeness | Notes |
|-----------|--------|----------------|-------|
| **CLI Entry Points** | Partial | 20% | Only `generate entities` command implemented |
| **CLI Commands** | Missing | 0% | validate, migrate, list-duplicates, recalculate, etc. missing |
| **Orchestration** | Partial | 40% | SchemaOrchestrator exists but Team E wrapper missing |
| **Migration Management** | Missing | 0% | No migration versioning or management |
| **Documentation Generation** | Missing | 0% | No mutation docs generator |
| **Frontend Code Generation** | Missing | 0% | No TypeScript, hooks, or JSON generation |
| **Tests** | Missing | 0% | No tests in tests/unit/cli/ |
| **Error Handling** | Partial | 30% | Basic error handling in generate.py |

---

## 1. What Exists: Current CLI Implementation

### 1.1 Location and Files

```
src/cli/
├── __init__.py (empty)
├── generate.py (4,684 bytes - 139 lines)
└── __pycache__/
```

### 1.2 Current CLI Command Structure

**File**: `/home/lionel/code/printoptim_backend_poc/src/cli/generate.py`

**Current Status**:
- Built with Click framework (version 8.1.0+)
- One command group: `cli()`
- One subcommand: `entities()`

**What It Does**:
```bash
specql entities [OPTIONS] entity_files...
```

Options:
- `--output-dir` / `-o`: Output directory for migrations (default: `migrations`)
- `--foundation-only`: Generate only app foundation migration
- `--include-tv`: Generate tv_ table views after entities

**Functionality**:
1. Parses SpecQL YAML files using SpecQLParser
2. Converts EntityDefinition → Entity for orchestrator
3. Uses SchemaOrchestrator to generate complete SQL
4. Writes migrations to filesystem
5. Supports app foundation generation (000_app_foundation.sql)
6. Supports table views generation (200_table_views.sql)

**Known Issues/TODOs in Code**:
- Line 20: `# TODO: Convert impact dict to ActionImpact` - Impact metadata conversion not implemented
- No validate or migrate commands referenced in pyproject.toml but declared as entry points

### 1.3 Entry Points (pyproject.toml)

```toml
[project.scripts]
specql = "src.cli.generate:main"
specql-validate = "src.cli.validate:main"  # MISSING
specql-migrate = "src.cli.migrate:main"    # MISSING
```

**Current Status**:
- Only `specql` works (points to generate.py)
- `specql-validate` and `specql-migrate` are declared but files don't exist

### 1.4 Dependencies

**Already Available**:
- `click>=8.1.0` - CLI framework
- `rich>=13.0.0` - Terminal UI/formatting
- `pyyaml>=6.0` - YAML parsing
- `jinja2>=3.1.2` - Template rendering
- `psycopg2-binary>=2.9.0` & `psycopg>=3.2.12` - Database drivers

---

## 2. What Orchestration Exists

### 2.1 SchemaOrchestrator

**File**: `/home/lionel/code/printoptim_backend_poc/src/generators/schema_orchestrator.py`
**Size**: 203 lines
**Status**: Functional

**Key Methods**:
```python
class SchemaOrchestrator:
    def generate_complete_schema(entity: Entity) -> str
        # Returns SQL for:
        # - App foundation
        # - Table DDL
        # - Input types
        # - Indexes
        # - Foreign keys
        # - Core logic functions
        # - FraiseQL annotations
        # - Trinity helper functions

    def generate_table_views(entities: List[EntityDefinition]) -> str
        # Returns SQL for all tv_ tables in dependency order

    def generate_app_foundation_only() -> str
        # Returns base migration SQL

    def generate_schema_summary(entity: Entity) -> Dict
        # Returns summary of what will be created
```

**Team E Needs**:
- Wrapper orchestrator for CLI that coordinates:
  - Extension generation
  - Utility function generation
  - Schema generation (with Team B)
  - Action compilation (with Team C)
  - FraiseQL metadata (with Team D)
  - Frontend code generation
  - Migration numbering and ordering

### 2.2 Other Orchestration Components

**Action Orchestrator**: `/home/lionel/code/printoptim_backend_poc/src/generators/actions/action_orchestrator.py`
- Handles action step compilation
- Not directly used by Team E CLI yet

---

## 3. What's Missing for Team E

### 3.1 Missing CLI Commands

Based on CLAUDE.md and TEAM_E_DATABASE_DECISIONS_PLAN.md:

#### 3.1.1 Validate Command
```bash
specql-validate entities/*.yaml --check-impacts
specql-validate-impacts --database-url=postgres://...
```

**Missing Files**:
- `src/cli/validate.py` - Validation command implementation
- Should validate:
  - SpecQL syntax correctness
  - Impact declarations
  - Runtime impact matching

#### 3.1.2 Migrate Command
```bash
specql-migrate [OPTIONS] [migrations_dir]
```

**Missing Files**:
- `src/cli/migrate.py` - Migration execution command
- Should handle:
  - Connection management
  - Migration ordering
  - Rollback capability
  - State tracking

#### 3.1.3 Deduplication Commands
```bash
specql list-duplicates --entity=Location --schema=tenant
specql recalculate-identifiers --entity=Contact --schema=crm [--dry-run]
```

**Missing Files**:
- `src/cli/commands/deduplication.py` - Identifier dedup management
- Should list and recalculate duplicate identifiers

#### 3.1.4 Split Entity Commands
```bash
specql list-split-entities
specql validate-split-integrity --entity=Location --schema=tenant
```

**Missing Files**:
- `src/cli/commands/split_entities.py` - Node+info split management
- Should manage node+info split entities

#### 3.1.5 Path Validation Commands
```bash
specql validate-paths --entity=Location --schema=tenant [--fix]
```

**Missing Files**:
- `src/cli/commands/validate_paths.py` - INTEGER path validation
- Should validate LTREE paths

### 3.2 Missing Orchestration Components

#### 3.2.1 CLI Orchestrator
```
src/cli/orchestrator.py
```

**Responsibilities**:
- Migration order management (extensions → utilities → schema → triggers → helpers → annotations)
- Template rendering
- Migration numbering
- Dependency resolution

**Status**: Not started

#### 3.2.2 Migration Management
```
src/cli/migration_manager.py
```

**Responsibilities**:
- Track applied migrations
- Versioning
- Rollback logic
- State persistence

**Status**: Not started

### 3.3 Missing Frontend Code Generation

#### 3.3.1 Mutation Impacts JSON Generator
```
src/generators/frontend/mutation_impacts_generator.py
```

**Should generate**:
```json
{
  "version": "1.0.0",
  "generatedAt": "2025-11-08T16:00:00Z",
  "mutations": {
    "qualifyLead": { ... }
  }
}
```

**Status**: Not started

#### 3.3.2 TypeScript Type Generator
```
src/generators/frontend/typescript_types_generator.py
```

**Should generate**:
```typescript
export interface MutationImpact { ... }
export const MUTATION_IMPACTS: { ... }
```

**Status**: Not started

#### 3.3.3 Apollo/React Hooks Generator
```
src/generators/frontend/apollo_hooks_generator.py
```

**Should generate**:
```typescript
export function useQualifyLead(options?: MutationHookOptions) { ... }
```

**Status**: Not started

#### 3.3.4 Documentation Generator
```
src/generators/frontend/mutation_docs_generator.py
```

**Should generate**: Markdown documentation from impacts

**Status**: Not started

### 3.4 Missing Tests

#### 3.4.1 Test Directory
```
tests/unit/cli/
```

**Doesn't exist yet**

**Should contain**:
- `test_generate_command.py` - CLI generate tests
- `test_validate_command.py` - CLI validate tests
- `test_migrate_command.py` - CLI migrate tests
- `test_deduplication_commands.py` - Dedup CLI tests
- `test_split_entity_commands.py` - Split entity tests
- `test_path_validation_commands.py` - Path validation tests
- `test_cli_orchestrator.py` - Orchestration tests
- `test_frontend_generation.py` - Frontend codegen tests

**Status**: Not started

---

## 4. Integration Points (What Team E Depends On)

### 4.1 Team A Dependencies
- ✅ **DONE**: AST models (EntityDefinition, Action, ActionDefinition)
- ✅ **DONE**: SpecQLParser for parsing YAML

### 4.2 Team B Dependencies
- ✅ **DONE**: SchemaOrchestrator
- ✅ **DONE**: TableGenerator
- ✅ **DONE**: TrinityHelperGenerator
- ✅ **DONE**: NameingConventions
- ✅ **DONE**: SchemaRegistry

### 4.3 Team C Dependencies
- ✅ **DONE**: ActionCompiler
- ✅ **DONE**: Action validation

### 4.4 Team D Dependencies
- ✅ **DONE**: MutationAnnotator (FraiseQL metadata)
- ✅ **DONE**: TableViewAnnotator

### 4.5 Missing Internal Team E Dependencies
- ❌ **MISSING**: CLI Orchestrator
- ❌ **MISSING**: Migration manager
- ❌ **MISSING**: Frontend generators

---

## 5. Current Test Coverage

### 5.1 Unit Tests Structure

```
tests/unit/
├── actions/ (100+ test files)
├── core/ (SpecQL parser tests - ✅ DONE)
├── fraiseql/ (FraiseQL tests - ✅ DONE)
├── generators/ (Team B tests - ✅ DONE)
├── numbering/ (Team C tests - ✅ DONE)
├── registry/ (Schema registry tests - ✅ DONE)
├── schema/ (Schema generation tests - ✅ DONE)
└── cli/ (❌ MISSING - Would test Team E)
```

### 5.2 Integration Tests Structure

```
tests/integration/
├── actions/ (✅ DONE)
├── fraiseql/ (✅ DONE)
├── schema/ (✅ DONE)
└── (Team E tests would go here for CLI/orchestration end-to-end)
```

**Total Test Files**: 100
**Total Source Files**: 78

---

## 6. Documentation Status

### 6.1 Existing Team E Documentation

**File**: `/home/lionel/code/printoptim_backend_poc/docs/teams/TEAM_E_DATABASE_DECISIONS_PLAN.md`

**Status**: Detailed plan document (643 lines)

**Contains**:
- Phase 1: Migration Orchestration (Day 1)
  - MigrationOrchestrator class design
  - Template rendering
  - Order management
- Phase 2: Deduplication Commands (Day 2)
  - list_duplicates
  - recalculate_identifiers
- Phase 3: Node+Info Split Management (Day 3)
  - list_split_entities
  - validate_split_integrity
- Phase 4: INTEGER Path Validation (Day 4)
  - validate_paths with --fix

### 6.2 Other Referenced Docs

**From CLAUDE.md** (`.claude/CLAUDE.md`):
- Section: "Team E: CLI & Orchestration + Frontend Codegen" (lines 596-750)
- Describes:
  - CLI commands (generate, validate, diff, docs, validate-impacts)
  - Orchestration responsibilities
  - Frontend code generation
  - Documentation generation
  - Impact validation

---

## 7. Project Structure Overview

```
/home/lionel/code/printoptim_backend_poc/
├── src/
│   ├── cli/                     # Team E
│   │   ├── generate.py          # ✅ Partial (only entities command)
│   │   ├── __init__.py
│   │   ├── validate.py          # ❌ Missing
│   │   ├── migrate.py           # ❌ Missing
│   │   ├── orchestrator.py      # ❌ Missing
│   │   ├── migration_manager.py # ❌ Missing
│   │   └── commands/            # ❌ Missing directory
│   │       ├── deduplication.py
│   │       ├── split_entities.py
│   │       └── validate_paths.py
│   ├── core/                    # Team A (✅ DONE)
│   ├── generators/
│   │   ├── schema/              # Team B (✅ DONE)
│   │   ├── actions/             # Team C (✅ DONE)
│   │   ├── fraiseql/            # Team D (✅ DONE)
│   │   └── frontend/            # Team E (❌ MISSING)
│   │       ├── mutation_impacts_generator.py
│   │       ├── typescript_types_generator.py
│   │       ├── apollo_hooks_generator.py
│   │       └── mutation_docs_generator.py
│   └── agents/
│
├── tests/
│   ├── unit/
│   │   ├── core/                # ✅ DONE (Team A)
│   │   ├── generators/          # ✅ DONE (Team B)
│   │   ├── actions/             # ✅ DONE (Team C)
│   │   ├── fraiseql/            # ✅ DONE (Team D)
│   │   ├── numbering/
│   │   ├── registry/
│   │   ├── schema/
│   │   └── cli/                 # ❌ MISSING (Team E)
│   └── integration/             # ✅ Partial (Teams A-D)
│
├── docs/
│   ├── teams/
│   │   ├── TEAM_A_COMPLETION_STATUS.md (✅)
│   │   ├── TEAM_B_PHASE_9_QA_REPORT.md (✅)
│   │   ├── TEAM_C_COMPLETION_REPORT.md (✅)
│   │   ├── TEAM_D_PHASED_IMPLEMENTATION_PLAN.md (✅)
│   │   └── TEAM_E_DATABASE_DECISIONS_PLAN.md (✅ PLAN)
│   └── fraiseql/
│
├── entities/
│   ├── examples/                 # ✅ 5 example files
│   └── schemas/
│
├── migrations/                   # ✅ Generated SQLfiles
├── generated/                    # Generated artifacts
├── Makefile
├── pyproject.toml
├── .claude/CLAUDE.md
└── README.md
```

---

## 8. Key Metrics

### 8.1 Code Distribution

| Team | Source Files | Lines | Status |
|------|--------------|-------|--------|
| **A** (Parser) | 2 | ~500 | ✅ Complete |
| **B** (Schema) | 20+ | ~3000 | ✅ Complete |
| **C** (Actions) | 15+ | ~4000 | ✅ Complete |
| **D** (FraiseQL) | 5 | ~500 | ✅ Complete |
| **E** (CLI/Frontend) | 1 | ~140 | ❌ 5% Complete |
| **Total** | 78 | ~8500 | ~95% Complete |

### 8.2 Test Distribution

| Category | Test Files | Status |
|----------|-----------|--------|
| **Unit Tests** | ~60 | ✅ A-D Complete, E Missing |
| **Integration Tests** | ~10 | ✅ A-D Present, E Missing |
| **Total** | ~100 | ~90% Coverage (E Missing) |

---

## 9. Missing Functionality vs. Plan

### 9.1 From CLAUDE.md - CLI Commands

Expected CLI interface (from documentation):
```bash
specql generate entities/contact.yaml
specql generate entities/*.yaml --with-impacts --output-frontend=../frontend
specql validate entities/*.yaml --check-impacts
specql diff entities/contact.yaml
specql docs entities/*.yaml --format=markdown --output=docs/mutations.md
specql validate-impacts --database-url=postgres://...
```

**Implemented**: Only partial `specql generate` (without --with-impacts, --output-frontend)
**Missing**: All others (validate, diff, docs, validate-impacts)

### 9.2 From TEAM_E_DATABASE_DECISIONS_PLAN.md - Commands

```bash
specql list-duplicates --entity=Location --schema=tenant
specql recalculate-identifiers --entity=Contact [--dry-run]
specql list-split-entities
specql validate-split-integrity --entity=Location
specql validate-paths --entity=Location [--fix]
```

**Implemented**: None
**Missing**: All 5 command types

### 9.3 Frontend Code Generation (From CLAUDE.md)

```bash
specql generate entities/*.yaml --with-impacts --output-frontend=../frontend/src/generated
```

Should generate:
- `mutation-impacts.json` - Static metadata
- `mutation-impacts.d.ts` - TypeScript types
- `mutations.ts` - Pre-configured hooks
- `docs/mutations.md` - Documentation

**Implemented**: None
**Missing**: All 4 artifact types

---

## 10. Implementation Roadmap (Based on Codebase Analysis)

### Phase 1: Core CLI Enhancements (Week 1-2)
- [x] Existing `specql entities` command
- [ ] Complete generate command with `--with-impacts` and `--output-frontend`
- [ ] Implement `src/cli/validate.py`
- [ ] Implement `src/cli/migrate.py`
- [ ] Create CLI tests in `tests/unit/cli/`

### Phase 2: Orchestration (Week 2-3)
- [ ] `src/cli/orchestrator.py` - Migration ordering
- [ ] `src/cli/migration_manager.py` - State tracking
- [ ] Database connection pooling
- [ ] Rollback support

### Phase 3: Management Commands (Week 3-4)
- [ ] `src/cli/commands/deduplication.py`
- [ ] `src/cli/commands/split_entities.py`
- [ ] `src/cli/commands/validate_paths.py`
- [ ] Integration tests for each

### Phase 4: Frontend Codegen (Week 4-5)
- [ ] `src/generators/frontend/mutation_impacts_generator.py`
- [ ] `src/generators/frontend/typescript_types_generator.py`
- [ ] `src/generators/frontend/apollo_hooks_generator.py`
- [ ] `src/generators/frontend/mutation_docs_generator.py`

### Phase 5: Testing & QA (Week 5-6)
- [ ] Complete test coverage for all CLI commands
- [ ] Integration tests
- [ ] End-to-end workflow testing
- [ ] Documentation

---

## 11. Recommendations

### 11.1 Highest Priority (Week 1)
1. **Extend existing `generate.py`**:
   - Add `--with-impacts` flag
   - Add `--output-frontend` option
   - Test these flags work with SchemaOrchestrator

2. **Create test structure**:
   - `tests/unit/cli/test_generate_command.py`
   - `tests/unit/cli/test_cli_orchestrator.py`
   - Set up CLI testing with Click's CliRunner

3. **Implement CLI Orchestrator**:
   - Wrapper around SchemaOrchestrator
   - Migration numbering
   - File output management

### 11.2 Medium Priority (Week 2)
1. **Implement validate.py** - Syntax and impact validation
2. **Implement migrate.py** - Database migration execution
3. **Create commands/ directory structure**

### 11.3 Lower Priority (Week 3+)
1. Frontend code generation
2. Management commands (dedup, split, paths)
3. Advanced documentation generation

---

## 12. Key Files to Create (Summary)

| File | Lines | Purpose | Difficulty |
|------|-------|---------|------------|
| `src/cli/validate.py` | 150 | Validation command | Medium |
| `src/cli/migrate.py` | 200 | Migration execution | Hard |
| `src/cli/orchestrator.py` | 200 | Migration orchestration | Medium |
| `src/cli/migration_manager.py` | 150 | State tracking | Medium |
| `src/cli/commands/deduplication.py` | 100 | Dedup management | Easy |
| `src/cli/commands/split_entities.py` | 120 | Split entity management | Easy |
| `src/cli/commands/validate_paths.py` | 100 | Path validation | Easy |
| `src/generators/frontend/mutation_impacts_generator.py` | 150 | Impacts JSON | Medium |
| `src/generators/frontend/typescript_types_generator.py` | 200 | TypeScript types | Hard |
| `src/generators/frontend/apollo_hooks_generator.py` | 250 | React hooks | Hard |
| `src/generators/frontend/mutation_docs_generator.py` | 150 | Markdown docs | Medium |
| `tests/unit/cli/test_*.py` | 1500+ | CLI tests | Medium |
| **TOTAL** | ~3200+ | Complete Team E | - |

---

## 13. Quick Start for Team E Development

### 13.1 Running Current CLI
```bash
# See current capabilities
python -m src.cli.generate --help

# Run entities command
python -m src.cli.generate entities entities/examples/contact_lightweight.yaml

# With table views
python -m src.cli.generate entities entities/examples/contact_lightweight.yaml --include-tv
```

### 13.2 Testing Current CLI
```bash
# Current tests (will fail for validate/migrate)
make teamE-test  # Will run: pytest tests/unit/cli/ -v (currently no tests)

# Run specific test (once created)
uv run pytest tests/unit/cli/test_generate_command.py -v
```

### 13.3 Development Workflow
```bash
# 1. Create test first (TDD)
vim tests/unit/cli/test_validate_command.py

# 2. Run test (should fail)
uv run pytest tests/unit/cli/test_validate_command.py -v

# 3. Implement feature
vim src/cli/validate.py

# 4. Test should pass
uv run pytest tests/unit/cli/test_validate_command.py -v

# 5. Run all Team E tests
make teamE-test

# 6. Run all tests
make test
```

---

## Summary Table: Team E Current State

| Aspect | Status | % Complete | Key Files |
|--------|--------|-----------|-----------|
| **CLI Foundation** | Partial | 20% | `src/cli/generate.py` |
| **Entry Points** | Partial | 33% | `pyproject.toml` (1 of 3 working) |
| **Commands Implemented** | Partial | 13% | Only `entities` (1 of 8) |
| **Orchestration** | Missing | 0% | No `orchestrator.py` |
| **Frontend Codegen** | Missing | 0% | No `src/generators/frontend/` |
| **Tests** | Missing | 0% | No `tests/unit/cli/` |
| **Documentation** | Plan Only | 100% | TEAM_E_DATABASE_DECISIONS_PLAN.md |
| **Overall Team E** | Early Stage | ~5% | Significant work remains |

---

## Notes

1. **Dependencies are ready**: All Teams A-D are complete and functional
2. **Framework is installed**: Click, Rich, Jinja2, psycopg all in pyproject.toml
3. **Examples exist**: 5 entity YAML files ready for testing
4. **Tests can be added**: 100 test files show strong testing culture
5. **Documentation is thorough**: Both CLAUDE.md and TEAM_E_DATABASE_DECISIONS_PLAN.md provide detailed specs
