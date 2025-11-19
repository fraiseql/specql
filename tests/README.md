# SpecQL Test Suite

Comprehensive test suite for the SpecQL code generator.

**Current Status**: 1265+ tests, ~99% pass rate

---

## 🚀 Quick Start

```bash
# All core tests (no optional dependencies)
uv run pytest --ignore=tests/unit/reverse_engineering --ignore=tests/integration/reverse_engineering -v

# With coverage
uv run pytest --cov=src --cov-report=html

# Skip database tests
uv run pytest -m "not database"
```

---

## 📁 Structure

- **unit/** - Unit tests for individual components (fast, no external deps)
  - `core/` - Parser, AST models
  - `generators/` - Code generators
  - `schema/` - Schema generation
  - `actions/` - Action compilation
  - `fraiseql/` - FraiseQL metadata
  - `cli/` - CLI commands
  - `testing/` - Seed generation (requires faker)
  - `reverse_engineering/` - RE features (requires optional deps)
- **integration/** - Integration tests with PostgreSQL
  - `schema/` - PostgreSQL DDL tests
  - `actions/` - PL/pgSQL function tests
  - `fraiseql/` - FraiseQL discovery tests
  - `reverse_engineering/` - RE integration tests
- **fixtures/** - Shared test fixtures and mock data
- **archived/** - Deprecated tests kept for reference

---

## 📦 Dependencies

### Required (Always Installed)
Installed automatically with SpecQL:
- pytest>=7.4.0
- pytest-cov>=4.1.0
- psycopg>=3.2.12

### Optional Dependencies

**Test Data Generation** (8 tests):
```bash
pip install specql[testing]  # Includes faker
```

**Reverse Engineering** (200+ tests):
```bash
pip install specql[reverse]  # Includes pglast, tree-sitter
```

**All Features**:
```bash
pip install specql[all]
```

---

## 🗄️ Database Tests

Integration tests require PostgreSQL:

```bash
# Create test database
createdb specql_test

# Run integration tests
uv run pytest tests/integration/ -v
```

**Environment Variables** (optional):
```bash
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5432
export TEST_DB_NAME=specql_test
export TEST_DB_USER=$USER
```

---

## 🧪 Running Tests

### By Category
```bash
# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Core tests (no optional deps)
uv run pytest \
  --ignore=tests/unit/reverse_engineering \
  --ignore=tests/integration/reverse_engineering \
  -v
```

### By Marker
```bash
# Database tests only
uv run pytest -m database

# Skip database tests
uv run pytest -m "not database"
```

### Single Test
```bash
uv run pytest tests/unit/core/test_scalar_types.py::test_parse_text_field -v
```

---

## 📊 Test Coverage

**Current**:
- Core tests: 1239 passing
- Seed generation: 8 passing
- Integration tests: 18 passing
- **Total**: 1265+ tests

**Coverage Targets**:
- Core modules: >90%
- Generators: >85%
- CLI: >70%

Run coverage:
```bash
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 🔧 Useful Fixtures

**Database**:
- `test_db_connection` (session) - PostgreSQL connection
- `test_db` (function) - Fresh transaction per test
- `isolated_schema` (function) - Unique test_<uuid> schema

**Generators**:
- `naming_conventions` - NamingConventions instance
- `schema_registry` - SchemaRegistry instance
- `table_generator` - TableGenerator instance

---

## 🐛 Debugging

```bash
# Show print statements
uv run pytest tests/unit/core/test_parser.py -s

# Drop into debugger on failure
uv run pytest tests/unit/core/test_parser.py --pdb

# Full traceback
uv run pytest tests/unit/core/test_parser.py --tb=long
```

---

For detailed testing guide, see planning documents in `docs/post_beta_plan/`