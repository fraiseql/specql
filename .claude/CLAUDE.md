# Claude Code Instructions - SpecQL Schema Generator

**Project**: Business-focused YAML → PostgreSQL + GraphQL Backend
**Status**: 🚧 Active Development - Parallel Team Execution
**Context Window Optimization**: This file provides instant project context for AI assistants

---

## 🎯 Project Mission

Transform 40 lines of SpecQL YAML into production-ready PostgreSQL schema + GraphQL API.

**Example**:
```yaml
entity: Contact
  fields: {email: text, status: enum(lead, qualified)}
  actions:
    - name: create_contact
      steps: [validate, insert]
```
→ Generates 2000+ lines of SQL, GraphQL, TypeScript, tests

---

## 🏗️ Repository Architecture (5-Team Parallel Structure)

```
src/
├── core/           → Team A: SpecQL Parser
├── generators/     → Team B: SQL Generators
├── numbering/      → Team C: Hierarchical Organization
├── integration/    → Team D: FraiseQL + GraphQL
└── cli/            → Team E: Developer Tools
```

---

## 👥 TEAM STATUS & PROGRESS

### 🔵 Team A: Core Parser (`src/core/`)
**Mission**: Parse SpecQL YAML → Entity AST
**Status**: 🟡 In Progress (10%)

**Components**:
- ✅ `ast_models.py` - Data classes (Entity, FieldDefinition, Action, ActionStep, Agent)
- 🚧 `specql_parser.py` - YAML parser (TODO)
- 🚧 `validators.py` - Business rule validation (TODO)
- 🚧 `expression_parser.py` - SpecQL expression → SQL (TODO)

**Current Work**:
- Implementing `SpecQLParser.parse()` method
- Parsing field definitions (text, enum, ref, list)
- Parsing action steps (validate, if/then, insert, update)

**Dependencies**: None (can start immediately)
**Blocks**: Teams B, C, D, E (waiting for Entity AST)

**Test Coverage**: 0% (no implementation yet)
**Test Command**: `make teamA-test`

**Next Task**: Write failing test for `test_parse_simple_entity()` → Implement parser

---

### 🟢 Team B: SQL Generators (`src/generators/`)
**Mission**: Generate PostgreSQL DDL + Functions from Entity AST
**Status**: 🔴 Blocked (0% - waiting for Team A)

**Components**:
- 🚧 `table_generator.py` - Trinity pattern tables (TODO)
- 🚧 `view_generator.py` - FraiseQL views (TODO)
- 🚧 `function_generator.py` - CRUD functions (TODO)
- 🚧 `action_generator.py` - SpecQL actions → PL/pgSQL (TODO)
- 🚧 `trigger_generator.py` - Group leader triggers (TODO)
- 🚧 `sql_utils.py` - SQL formatting utilities (TODO)

**Current Work**:
- Can start with **mock Entity objects** from `tests/fixtures/mock_entities.py`
- Developing table generation templates
- Setting up Jinja2 template infrastructure

**Dependencies**: Team A (Entity AST) - **CAN USE MOCKS FOR NOW**
**Blocks**: None

**Test Coverage**: 0%
**Test Command**: `make teamB-test`

**Next Task**: Create mock Entity → Generate Trinity pattern table → Write test

---

### 🟠 Team C: Numbering System (`src/numbering/`)
**Mission**: Hierarchical 6-digit codes + Manifest generation
**Status**: 🔴 Not Started (0%)

**Components**:
- 🚧 `numbering_parser.py` - Parse 6-digit table codes (TODO)
- 🚧 `directory_generator.py` - Create directory hierarchy (TODO)
- 🚧 `manifest_generator.py` - Execution order manifest (TODO)
- 🚧 `dependency_resolver.py` - Topological sort (TODO)

**Current Work**: Not started

**Dependencies**: None (standalone component)
**Blocks**: None

**Test Coverage**: 0%
**Test Command**: `make teamC-test`

**Next Task**: Implement `NumberingParser.parse_table_code("013211")` → Parse into components

---

### 🟣 Team D: Integration Layer (`src/integration/`)
**Mission**: FraiseQL + GraphQL + TypeScript generation
**Status**: 🔴 Not Started (0%)

**Components**:
- 🚧 `fraiseql_adapter.py` - COMMENT annotations for FraiseQL (TODO)
- 🚧 `testfoundry_adapter.py` - TestFoundry metadata (TODO)
- 🚧 `graphql_schema_gen.py` - GraphQL schema generation (TODO)
- 🚧 `typescript_gen.py` - TypeScript type generation (TODO)

**Current Work**: Not started

**Dependencies**: Team A (Entity AST), Team B (SQL output) - **CAN USE MOCKS**
**Blocks**: None

**Test Coverage**: 0%
**Test Command**: `make teamD-test`

**Next Task**: Generate FraiseQL COMMENT annotations from mock Entity

---

### 🔴 Team E: CLI & Tooling (`src/cli/`)
**Mission**: Developer experience tools
**Status**: 🔴 Not Started (0%)

**Components**:
- 🚧 `generate.py` - Main generation CLI (TODO)
- 🚧 `validate.py` - YAML validation CLI (TODO)
- 🚧 `migrate.py` - SQL → YAML migration (TODO)
- 🚧 `healthcheck.py` - Health check system (TODO)
- 🚧 `diff.py` - Schema diff tool (TODO)

**Current Work**: Not started

**Dependencies**: All teams (orchestration layer) - **CAN USE MOCKS**
**Blocks**: None

**Test Coverage**: 0%
**Test Command**: `make teamE-test`

**Next Task**: Create basic CLI structure with Click → Test `specql generate --help`

---

## 📊 Overall Project Progress

### Phase 1: Core Parser + SQL Generators (Weeks 1-2)
**Timeline**: Week 1-2 of 10
**Overall Progress**: 5%

**Completed**:
- ✅ Repository structure
- ✅ Development tooling
- ✅ Testing infrastructure
- ✅ AST models foundation

**In Progress**:
- 🚧 Team A: SpecQL parser (10%)
- 🚧 Team B: Can start with mocks (0%)
- 🔴 Teams C, D, E: Not started (0%)

**Week 1 Goals** (Current):
- [ ] Team A: Parse simple entities (contact.yaml)
- [ ] Team B: Generate Trinity pattern tables
- [ ] Team C: Parse 6-digit table codes
- [ ] Team D: FraiseQL COMMENT generation
- [ ] Team E: Basic CLI scaffold

**Week 2 Goals**:
- [ ] Team A: Parse complex entities (reservation.yaml with actions)
- [ ] Team B: SpecQL action compilation to PL/pgSQL
- [ ] Team C: Manifest generation with dependencies
- [ ] Team D: GraphQL schema generation
- [ ] Team E: Validation and health checks

**Integration Point**: End of Week 2 - Full pipeline (YAML → SQL → Database)

---

## 🔄 Critical Paths & Blockers

### Critical Path (Longest Dependencies)
```
Team A (Parser) → Team B (SQL Gen) → Team D (GraphQL) → Team E (CLI)
```

### Current Blockers
1. **Team A blocks everyone** - No Entity AST yet
   - **Mitigation**: Teams B/D/E use mock data (see below)
   - **Priority**: HIGH - Team A must deliver Week 1

2. **No blockers for Teams C** - Standalone component

### Unblocking Strategy
```python
# teams/fixtures/mock_entities.py
def mock_contact_entity() -> Entity:
    """Mock Entity for parallel development"""
    return Entity(
        name='Contact',
        schema='crm',
        fields={'email': FieldDefinition(name='email', type='text')},
        actions=[Action(name='create_contact', steps=[...])]
    )
```

Teams B/D/E can develop against mocks, then integrate when Team A delivers.

---

## 🧪 Testing Status

### Test Coverage by Team
- **Team A**: 0% (no tests written)
- **Team B**: 0% (no tests written)
- **Team C**: 0% (no tests written)
- **Team D**: 0% (no tests written)
- **Team E**: 0% (no tests written)

**Overall Coverage**: 0% (baseline)
**Target Coverage**: 90% (by end of Week 2)

### Test Commands
```bash
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests (Week 2+)

# Team-specific
make teamA-test        # Core parser tests
make teamB-test        # SQL generator tests
make teamC-test        # Numbering system tests
make teamD-test        # Integration layer tests
make teamE-test        # CLI tests
```

---

## 📁 Key Files for AI Context

### Essential Reading (High Priority)
1. **`GETTING_STARTED.md`** - Team onboarding guide
2. **`REPOSITORY_STRUCTURE.md`** - Full architecture & parallelization strategy
3. **`docs/architecture/IMPLEMENTATION_PLAN_SPECQL.md`** - 10-week roadmap with TDD cycles
4. **`src/core/ast_models.py`** - Foundation data classes (COMPLETE)

### Team-Specific Context
- **Team A**: `src/core/README.md` + `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md`
- **Team B**: `src/generators/README.md` + `templates/sql/*.j2`
- **Team C**: `docs/architecture/INTEGRATION_PROPOSAL.md` (numbering system section)
- **Team D**: `docs/analysis/FRAISEQL_INTEGRATION_REQUIREMENTS.md`
- **Team E**: `CONTRIBUTING.md` (CLI workflow)

### Reference Documentation
- **SpecQL DSL**: `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md`
- **Trinity Pattern**: Explained in `docs/analysis/POC_RESULTS.md`
- **Group Leaders**: `docs/architecture/INTEGRATION_PROPOSAL.md`

---

## 🎯 AI Assistant Instructions

### When Asked About Progress
1. Check **team status sections above** (🔵🟢🟠🟣🔴 indicators)
2. Report current % completion per team
3. Identify blockers and critical path
4. Suggest next actionable task

### When Asked to Help a Team
1. Read team's `README.md` in `src/{team}/`
2. Check `tests/unit/{team}/` for existing tests
3. Follow **TDD cycle**: RED → GREEN → REFACTOR → QA
4. Use mocks from `tests/fixtures/` if dependencies not ready

### When Suggesting Work
1. **Always prioritize Team A** (blocks everyone)
2. Suggest teams use **mock data** for parallel work
3. Ensure **one team-specific task at a time**
4. Follow test-first approach (write test, then implementation)

### Code Quality Standards
- Type hints required (`mypy` passing)
- Linting passing (`ruff check`)
- Test coverage > 80% per module
- Docstrings for all public functions

---

## 🔧 Common Development Commands

```bash
# Setup (once)
uv venv && source .venv/bin/activate && make install

# TDD Cycle (daily)
vim tests/unit/core/test_specql_parser.py  # RED: Write failing test
uv run pytest tests/unit/core/ -v          # Verify it fails
vim src/core/specql_parser.py              # GREEN: Make it pass
uv run pytest tests/unit/core/ -v          # Verify it passes
vim src/core/specql_parser.py              # REFACTOR: Clean up
make teamA-test                            # Verify still passes
make lint && make typecheck                # QA: Quality checks

# Before commit
make lint && make typecheck && make test
git add . && git commit -m "feat(core): implement SpecQL parser"
```

---

## 📈 Success Metrics

### Week 1 Targets (Current Week)
- [ ] Team A: 50% (simple entity parsing working)
- [ ] Team B: 30% (table generation with mocks)
- [ ] Team C: 40% (numbering parser working)
- [ ] Team D: 20% (FraiseQL comments with mocks)
- [ ] Team E: 20% (CLI scaffold)

### Week 2 Targets
- [ ] Team A: 100% (complex entity parsing)
- [ ] Team B: 70% (action compilation)
- [ ] Team C: 80% (manifest generation)
- [ ] Team D: 60% (GraphQL schema gen)
- [ ] Team E: 50% (validation tools)

### Integration Milestone (End of Week 2)
- [ ] Full pipeline: YAML → Entity AST → SQL → Database
- [ ] End-to-end test passing
- [ ] 80%+ test coverage overall

---

## 🚨 Important Constraints

### Development Methodology
- **TDD is mandatory**: RED → GREEN → REFACTOR → QA
- **No skipping tests**: Every feature needs tests first
- **Small PRs**: < 500 lines per PR
- **Team isolation Week 1**: Use mocks, not cross-team imports

### Performance Targets
- Parse 100 entities: < 5 seconds
- Generate SQL for 1 entity: < 100ms
- Full pipeline (1 entity): < 500ms

### Code Standards
- Python 3.8+ compatibility
- Type hints everywhere
- Comprehensive docstrings
- 80%+ test coverage minimum

---

## 🎓 AI Learning Resources

When helping with specific technologies:

### SpecQL DSL
- See: `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md`
- Action steps: validate, if/then, insert, update, call, find
- Framework handles: audit, events, permissions (auto-generated)

### PostgreSQL Trinity Pattern
- `pk_*` INTEGER PRIMARY KEY (fast joins)
- `id` UUID (stable external ID)
- `identifier` TEXT (human-readable key)
- See: `docs/analysis/POC_RESULTS.md`

### Group Leader Pattern
- Auto-populate dependent fields via triggers
- Ensures data coherence (e.g., company address matches company)
- See: `docs/architecture/INTEGRATION_PROPOSAL.md`

---

## 💡 Quick Reference: What Each Team Needs

### Team A Needs
- YAML parsing (PyYAML)
- Regex for expression parsing
- AST design patterns
- **Currently working on**: Basic entity parsing

### Team B Needs
- Jinja2 templates
- PostgreSQL DDL knowledge
- PL/pgSQL for functions
- **Currently working on**: Mock-based table generation

### Team C Needs
- Graph algorithms (topological sort)
- File system operations
- Dependency resolution
- **Currently working on**: Numbering parser

### Team D Needs
- GraphQL schema knowledge
- FraiseQL introspection format
- TypeScript type generation
- **Currently working on**: Not started (can use mocks)

### Team E Needs
- Click (CLI framework)
- Rich (terminal UI)
- Orchestration patterns
- **Currently working on**: Not started

---

## 🎯 Recommended Next Actions (for AI to Suggest)

### Immediate (This Session)
1. **Team A**: Implement `SpecQLParser.parse()` for simple entities
   - Start with failing test in `tests/unit/core/test_specql_parser.py`
   - Parse basic fields (text, integer types)
   - Return Entity AST

2. **Team B**: Create mock Entity → Generate table SQL
   - Use `tests/fixtures/mock_entities.py`
   - Implement `table_generator.py` with Trinity pattern
   - Test with `make teamB-test`

### Short-term (This Week)
3. **Team C**: Implement numbering parser
4. **Team D**: FraiseQL COMMENT generation with mocks
5. **Team E**: CLI scaffold with Click

### Medium-term (Week 2)
6. Integration testing across teams
7. Complex entity parsing (actions with steps)
8. Full pipeline demo

---

## 📞 Getting Help

When AI needs clarification:
1. Check team's `README.md` first
2. Review `REPOSITORY_STRUCTURE.md` for interfaces
3. Look at existing test fixtures for examples
4. Suggest reading `IMPLEMENTATION_PLAN_SPECQL.md` for detailed specs

---

**Last Updated**: 2025-11-08
**Project Phase**: 1 (Core Parser + SQL Generators)
**Overall Progress**: 5%
**Next Milestone**: Week 1 completion (simple entity → SQL pipeline working)

---

## 🤖 AI Optimization Notes

This file is designed for efficient AI context loading:
- **Team status**: Quick visual indicators (🔵🟢🟠🟣🔴)
- **Progress tracking**: % completion per team
- **Blocker visibility**: Critical path clearly marked
- **Actionable next steps**: Specific tasks for each team
- **File references**: Direct pointers to relevant documentation

**AI should prioritize**:
1. Team A (blocks everyone)
2. Teams with no blockers (B/C/D/E can use mocks)
3. Test-first development (TDD mandatory)
4. Small, incremental progress over large changes

**AI should avoid**:
1. Suggesting work across multiple teams simultaneously
2. Skipping test writing
3. Large refactorings before basic functionality works
4. Cross-team imports during Week 1 (use mocks instead)
