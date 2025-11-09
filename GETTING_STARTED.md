# Getting Started - Team Parallelization

**Repository is now organized for maximum parallelization!** 🚀

---

## 🎯 Repository Organization Complete

The codebase has been restructured to enable **5 teams to work independently in parallel**.

### ✅ What's Been Done

1. **Modular Structure Created**
   - `src/core/` - Team A (SpecQL parser)
   - `src/generators/` - Team B (SQL generators)
   - `src/numbering/` - Team C (Hierarchical organization)
   - `src/integration/` - Team D (FraiseQL + GraphQL)
   - `src/cli/` - Team E (Developer tools)

2. **Testing Infrastructure**
   - Unit tests organized by team (`tests/unit/{team}/`)
   - Integration tests for end-to-end validation
   - Shared fixtures and mocks (`tests/conftest.py`)
   - Team-specific test commands (`make teamA-test`, etc.)

3. **Development Tooling**
   - `Makefile` - Common development commands
   - `pyproject.toml` - Python dependencies and configuration
   - `.gitignore` - Proper Python/generated file exclusions
   - `CONTRIBUTING.md` - TDD workflow and guidelines

4. **Documentation Structure**
   - `docs/architecture/` - Implementation plans
   - `docs/analysis/` - Analysis documents
   - `docs/guides/` - User guides (TODO)
   - Team READMEs in each module

5. **Foundation Code**
   - `src/core/ast_models.py` - Complete AST data classes ✅
   - Entity, FieldDefinition, Action, ActionStep, Agent models
   - Foundation for all other components

---

## 🚀 Quick Start for Each Team

### Team A: Core Parser (`src/core/`)

**Mission**: Parse SpecQL YAML → Entity AST

```bash
# Start here
cd src/core/
cat README.md

# Run tests
make teamA-test

# Start coding (TDD)
vim tests/unit/core/test_specql_parser.py  # RED: Write failing test
vim src/core/specql_parser.py              # GREEN: Make it pass
make teamA-test                            # REFACTOR: Verify still passes
make lint && make typecheck                # QA: Quality checks
```

**First Task**: Implement `SpecQLParser.parse()` method

---

### Team B: SQL Generators (`src/generators/`)

**Mission**: Generate PostgreSQL DDL + functions from Entity AST

```bash
# Start here
cd src/generators/
cat README.md

# Use mock data (parallel development)
vim tests/fixtures/mock_entities.py  # Create mock Entity objects

# Run tests
make teamB-test

# Start coding (TDD)
vim tests/unit/generators/test_table_generator.py  # RED
vim src/generators/table_generator.py              # GREEN
make teamB-test                                    # REFACTOR + QA
```

**First Task**: Implement `generate_table()` for Trinity pattern tables

---

### Team C: Numbering System (`src/numbering/`)

**Mission**: Hierarchical organization + manifest generation

```bash
# Start here
cd src/numbering/
# cat README.md (TODO: create README)

# Run tests
make teamC-test

# Start coding
vim tests/unit/numbering/test_numbering_parser.py
vim src/numbering/numbering_parser.py
```

**First Task**: Implement `NumberingParser.parse_table_code()`

---

### Team D: Integration Layer (`src/integration/`)

**Mission**: FraiseQL + GraphQL + TypeScript generation

```bash
# Start here
cd src/integration/
# cat README.md (TODO: create README)

# Run tests
make teamD-test

# Start coding
vim tests/unit/integration/test_fraiseql_adapter.py
vim src/integration/fraiseql_adapter.py
```

**First Task**: Implement `generate_fraiseql_comments()`

---

### Team E: CLI & Tooling (`src/cli/`)

**Mission**: Developer experience tools

```bash
# Start here
cd src/cli/
# cat README.md (TODO: create README)

# Run tests
make teamE-test

# Start coding
vim tests/unit/cli/test_confiture_extensions.py
vim src/cli/confiture_extensions.py
```

**First Task**: Create `specql generate` CLI command with Confiture integration

---

## 📊 Current Status

### Completed ✅
- [x] Repository structure
- [x] Development tooling (Makefile, pyproject.toml)
- [x] Testing infrastructure
- [x] AST models (`src/core/ast_models.py`)
- [x] Documentation framework
- [x] Team READMEs (partial)

### Next Steps (Teams Choose)

**Week 1 Goals** (All teams can start immediately):

- [ ] **Team A**: `SpecQLParser.parse()` for simple entities
- [ ] **Team B**: `generate_table()` for Trinity pattern
- [ ] **Team C**: `NumberingParser.parse_table_code()`
- [ ] **Team D**: `fraiseql_adapter.generate_comments()`
- [ ] **Team E**: `cli.generate` basic command

**Integration Point**: End of Week 2 - All components integrate

---

## 🔧 Development Commands

```bash
# Setup (once)
uv venv
source .venv/bin/activate
make install

# Daily workflow
make test              # All tests
make teamA-test        # Team A tests only
make lint              # Code quality
make typecheck         # Type checking
make coverage          # Coverage report

# Before commit
make lint && make typecheck && make test
git add .
git commit -m "feat(core): implement SpecQL parser"
```

---

## 📚 Key Documentation

1. **[REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md)** - Full architecture
2. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development workflow (TDD)
3. **[IMPLEMENTATION_PLAN_SPECQL.md](docs/architecture/IMPLEMENTATION_PLAN_SPECQL.md)** - 10-week roadmap
4. **[README.md](README.md)** - Project overview

---

## 🤝 Team Coordination

### Interface Contracts

Teams can work independently using **well-defined interfaces**:

```python
# Team A Output → Team B Input
from src.core.ast_models import Entity

def generate_table(entity: Entity) -> str:
    """Team B consumes Team A's output"""
    pass
```

### Mock Data for Parallel Development

```python
# tests/fixtures/mock_entities.py
def mock_contact_entity() -> Entity:
    """Teams B/C/D/E can use this while Team A develops parser"""
    return Entity(
        name='Contact',
        schema='crm',
        fields={'email': FieldDefinition(name='email', type='text')}
    )
```

### Communication Channels

- **Daily Standups**: Post in team channels (async)
- **Blockers**: Mention in `#integration` channel
- **Questions**: See `CONTRIBUTING.md` for help resources

---

## 🎯 Success Metrics

### Week 1 Targets
- [ ] Each team completes 1 core component
- [ ] Unit tests pass (>80% coverage per team)
- [ ] Mock interfaces validated

### Week 2 Targets
- [ ] Integration between teams begins
- [ ] End-to-end test (YAML → SQL) passes
- [ ] Documentation updated

---

## 🚨 Important Notes

### TDD is Mandatory
**RED → GREEN → REFACTOR → QA** cycle for every feature.

See `CONTRIBUTING.md` for detailed workflow.

### No Direct Dependencies
Teams should **not directly import** from other teams during Week 1.

Use **mock data** instead:
```python
# ❌ DON'T (Week 1)
from src.core.specql_parser import SpecQLParser

# ✅ DO (Week 1)
from tests.fixtures.mock_entities import mock_contact_entity
```

### Git Strategy
```bash
# Branch naming
git checkout -b teamA/specql-parser
git checkout -b teamB/table-generator

# PR when ready
gh pr create --title "SpecQL Parser Implementation"
```

---

## 🎓 Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [PostgreSQL PL/pgSQL](https://www.postgresql.org/docs/current/plpgsql.html)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)

---

## ✅ Pre-Flight Checklist

Before starting development:

- [ ] Read `REPOSITORY_STRUCTURE.md`
- [ ] Read `CONTRIBUTING.md`
- [ ] Choose your team (A/B/C/D/E)
- [ ] Read your team's `README.md`
- [ ] Setup development environment (`make install`)
- [ ] Run tests (`make test`)
- [ ] Create feature branch (`git checkout -b teamX/feature`)

---

**All systems ready for parallel development!** 🚀

Pick your team and start coding!
