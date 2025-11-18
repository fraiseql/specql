# Week 1 Implementation Guide: Test Infrastructure + Pattern Testing

**Phase**: Test Infrastructure Restoration & Pattern Testing
**Duration**: 7 days
**Objective**: Achieve 100% test collection success + 78+ pattern tests

---

## 📋 Daily Breakdown

### **Day 1: Dependency Resolution** (Monday)

#### **Morning Session (4 hours): Dependency Analysis**

**Tasks**:

1. **Audit Failing Test Imports** (1 hour)
```bash
# Find all import errors
uv run pytest --collect-only 2>&1 | grep "ModuleNotFoundError" | sort -u

# Expected findings:
# - ModuleNotFoundError: No module named 'pglast'
# - ModuleNotFoundError: No module named 'faker'
# - ModuleNotFoundError: No module named 'tree_sitter_*'
```

2. **Categorize Dependencies** (1 hour)

Create dependency matrix:

| Module | Used By | Purpose | Current Location | Target Location |
|--------|---------|---------|------------------|-----------------|
| `pglast` | reverse_engineering/* | SQL parsing | dependencies | optional-dependencies.reverse |
| `faker` | testing/seed/* | Test data gen | dependencies | optional-dependencies.testing |
| `tree-sitter-*` | reverse_engineering/parsers/* | AST parsing | dependencies | optional-dependencies.reverse |

3. **Document Dependency Rationale** (1 hour)

Create `docs/architecture/DEPENDENCY_STRATEGY.md`:

```markdown
# SpecQL Dependency Strategy

## Core Dependencies (Always Installed)
- **pyyaml**: YAML parsing (core feature)
- **jinja2**: Template generation (core feature)
- **click**: CLI framework (core feature)
- **rich**: Terminal UI (core feature)
- **psycopg**: PostgreSQL client (core feature)
- **fraiseql-confiture**: Confiture integration (core feature)

## Optional Dependencies

### `specql[reverse]` - Reverse Engineering
- **pglast**: SQL AST parsing for reverse engineering existing schemas
- **tree-sitter-***: Multi-language parsing (Rust, TypeScript, Prisma)
- **Use Case**: Converting existing databases to SpecQL

### `specql[testing]` - Test Data Generation
- **faker**: Realistic test data generation
- **Use Case**: Seed databases with realistic data for testing

### `specql[dev]` - Development Tools
- **pytest**: Testing framework
- **ruff**: Linting
- **mypy**: Type checking

### `specql[all]` - Everything
- All of the above

## Installation Examples

```bash
# Core only (most users)
pip install specql

# With reverse engineering
pip install specql[reverse]

# Development
pip install specql[dev,reverse,testing]

# Everything
pip install specql[all]
```

## Why Optional Dependencies?

1. **Reduced install time**: Core install is fast (< 10s)
2. **Smaller footprint**: No unnecessary packages
3. **Clear feature boundaries**: Users know what they're getting
4. **Better error messages**: Can guide users to install [reverse] if needed
```

4. **Update `pyproject.toml`** (1 hour)

```toml
[project]
name = "specql"
version = "0.5.0"
description = "SpecQL - Business-focused YAML to PostgreSQL + GraphQL code generator"
requires-python = ">=3.11"

# Core dependencies - MINIMAL, always installed
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.1.2",
    "click>=8.1.0",
    "rich>=13.0.0",
    "psycopg>=3.2.12",
    "fraiseql-confiture>=0.3.0",
]

[project.optional-dependencies]
# Development tools
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "pytest-time-machine>=2.19.0",
    "hypothesis>=6.142.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "black>=23.0.0",
    "types-pyyaml>=6.0.0",
]

# Reverse engineering features
reverse = [
    "pglast>=7.10",  # SQL AST parsing
    "tree-sitter>=0.20.0",
    "tree-sitter-rust>=0.20.0",
    "tree-sitter-typescript>=0.20.0",
]

# Test data generation
testing = [
    "faker>=37.12.0",
]

# Convenience: all optional features
all = [
    "specql[dev,reverse,testing]",
]
```

**Commit Point**: `git commit -m "refactor: reorganize dependencies into optional groups"`

---

#### **Afternoon Session (4 hours): Graceful Degradation**

**Tasks**:

1. **Create Dependency Check Utilities** (1 hour)

Create `src/core/dependencies.py`:

```python
"""Utility for checking optional dependencies."""

from typing import Optional
import importlib.util


class OptionalDependency:
    """Check if an optional dependency is available."""

    def __init__(self, package_name: str, pip_extra: str, purpose: str):
        self.package_name = package_name
        self.pip_extra = pip_extra
        self.purpose = purpose
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Check if dependency is installed."""
        if self._available is None:
            self._available = importlib.util.find_spec(self.package_name) is not None
        return self._available

    def require(self) -> None:
        """Raise helpful error if dependency not available."""
        if not self.available:
            raise ImportError(
                f"\n{self.purpose} requires {self.package_name}.\n"
                f"Install with: pip install specql[{self.pip_extra}]\n"
            )


# Define optional dependencies
PGLAST = OptionalDependency(
    package_name="pglast",
    pip_extra="reverse",
    purpose="SQL parsing for reverse engineering",
)

FAKER = OptionalDependency(
    package_name="faker",
    pip_extra="testing",
    purpose="Test data generation",
)

TREE_SITTER = OptionalDependency(
    package_name="tree_sitter",
    pip_extra="reverse",
    purpose="Multi-language AST parsing",
)
```

2. **Update Reverse Engineering Modules** (2 hours)

Update `src/reverse_engineering/sql_ast_parser.py`:

```python
"""SQL AST parsing using pglast."""

from typing import List, Optional
from src.core.dependencies import PGLAST

# Lazy import with availability check
_pglast = None

def _get_pglast():
    global _pglast
    if _pglast is None:
        PGLAST.require()  # Raises helpful error if not installed
        import pglast
        _pglast = pglast
    return _pglast


class SQLASTParser:
    """Parse SQL to AST using pglast."""

    def __init__(self):
        # Check dependency on instantiation
        self.pglast = _get_pglast()

    def parse(self, sql: str) -> dict:
        """Parse SQL string to AST."""
        return self.pglast.parse_sql(sql)
```

Similar updates for:
- `src/reverse_engineering/rust_parser.py` → Check TREE_SITTER
- `src/reverse_engineering/typescript_parser.py` → Check TREE_SITTER
- `src/reverse_engineering/prisma_parser.py` → Check TREE_SITTER
- `src/testing/seed/field_generators.py` → Check FAKER

3. **Update CLI Commands** (1 hour)

Update `src/cli/reverse.py`:

```python
"""Reverse engineering CLI commands."""

import click
from rich.console import Console
from src.core.dependencies import PGLAST, TREE_SITTER

console = Console()


@click.command()
@click.argument("input_sql", type=click.Path(exists=True))
def reverse_sql(input_sql: str):
    """Reverse engineer SQL to SpecQL YAML."""

    # Check dependencies upfront with helpful message
    if not PGLAST.available:
        console.print("[red]Error:[/red] SQL reverse engineering requires pglast", style="bold")
        console.print("Install with: [cyan]pip install specql[reverse][/cyan]")
        raise click.Abort()

    # Import and proceed
    from src.reverse_engineering.sql_ast_parser import SQLASTParser

    parser = SQLASTParser()
    # ... rest of implementation
```

**Commit Point**: `git commit -m "feat: add graceful degradation for optional dependencies"`

---

### **Day 2: Test Infrastructure** (Tuesday)

#### **Morning Session (4 hours): Pytest Configuration**

**Tasks**:

1. **Create Pytest Markers for Optional Features** (1 hour)

Update `conftest.py`:

```python
"""Pytest configuration for SpecQL tests."""

import pytest
from src.core.dependencies import PGLAST, FAKER, TREE_SITTER


# Markers for optional dependencies
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_pglast: test requires pglast (SQL parsing)"
    )
    config.addinivalue_line(
        "markers",
        "requires_faker: test requires faker (test data)"
    )
    config.addinivalue_line(
        "markers",
        "requires_tree_sitter: test requires tree-sitter (AST parsing)"
    )


# Skip hooks
def pytest_collection_modifyitems(config, items):
    """Skip tests that require unavailable dependencies."""

    skip_pglast = pytest.mark.skip(reason="pglast not installed (pip install specql[reverse])")
    skip_faker = pytest.mark.skip(reason="faker not installed (pip install specql[testing])")
    skip_tree_sitter = pytest.mark.skip(reason="tree-sitter not installed (pip install specql[reverse])")

    for item in items:
        # Check markers and skip if dependency unavailable
        if "requires_pglast" in item.keywords and not PGLAST.available:
            item.add_marker(skip_pglast)

        if "requires_faker" in item.keywords and not FAKER.available:
            item.add_marker(skip_faker)

        if "requires_tree_sitter" in item.keywords and not TREE_SITTER.available:
            item.add_marker(skip_tree_sitter)


# Auto-apply markers based on test path
def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on test location."""

    for item in items:
        test_path = str(item.fspath)

        # Reverse engineering tests need pglast/tree-sitter
        if "reverse_engineering" in test_path:
            if "tree_sitter" in test_path or "parser" in test_path:
                item.add_marker(pytest.mark.requires_tree_sitter)
            if "sql" in test_path:
                item.add_marker(pytest.mark.requires_pglast)

        # Testing module needs faker
        if "testing/seed" in test_path or "field_generator" in test_path:
            item.add_marker(pytest.mark.requires_faker)
```

2. **Update Test Files with Markers** (2 hours)

Update `tests/unit/reverse_engineering/test_sql_ast_parser.py`:

```python
"""Tests for SQL AST parser."""

import pytest
from src.reverse_engineering.sql_ast_parser import SQLASTParser


@pytest.mark.requires_pglast
class TestSQLASTParser:
    """Test SQL AST parsing functionality."""

    def test_parse_create_table(self):
        """Test parsing CREATE TABLE statement."""
        sql = """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL
        );
        """

        parser = SQLASTParser()
        ast = parser.parse(sql)

        assert ast is not None
        # ... assertions
```

Similar updates for all reverse engineering + testing tests.

3. **Run Test Suite & Verify** (1 hour)

```bash
# Without optional dependencies
uv pip install -e ".[dev]"
uv run pytest

# Expected:
# - Core tests: 384 passed
# - Reverse engineering: 60 skipped (dependency not available)
# - Testing module: 8 skipped (dependency not available)
# - Total: 384 passed, 68 skipped, 0 errors ✅

# With all dependencies
uv pip install -e ".[all]"
uv run pytest

# Expected:
# - All tests: 452+ passed (384 + 68), 0 skipped, 0 errors ✅
```

**Commit Point**: `git commit -m "test: add pytest markers for optional dependencies"`

---

#### **Afternoon Session (4 hours): Coverage & Documentation**

**Tasks**:

1. **Generate Coverage Report** (1 hour)

```bash
# Run tests with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Analyze results
open htmlcov/index.html

# Expected coverage:
# - Core parsing: 95%+
# - Schema generation: 95%+
# - Action compilation: 90%+
# - CLI: 80%+
# - Reverse engineering: 70%+ (optional feature)
# - Overall: 85-90%
```

2. **Document Coverage Gaps** (1 hour)

Create `docs/testing/COVERAGE_ANALYSIS.md`:

```markdown
# Test Coverage Analysis

## Current Coverage: 87%

### High Coverage (95%+) ✅
- Core parser (`src/core/parser.py`): 98%
- Schema generator (`src/generators/schema/`): 96%
- Action compiler (`src/generators/actions/`): 95%

### Medium Coverage (80-95%) ⚠️
- CLI commands (`src/cli/`): 84%
- FraiseQL generator (`src/generators/fraiseql/`): 88%

### Low Coverage (<80%) 🚨
- Reverse engineering (`src/reverse_engineering/`): 72%
- Frontend generator (`src/generators/frontend/`): 68%

## Coverage Improvement Plan

### Phase 1 (Week 1)
- Add pattern tests: +8% coverage
- Target: 95% overall

### Phase 2 (Week 2)
- Add CLI integration tests: +3% coverage
- Target: 98% overall

### Excluded from Coverage
- Vendor modules (`vendor/`)
- Generated code (`generated/`)
- Deprecated code (`archive/`)
```

3. **Update README with Dependency Info** (1 hour)

Update `README.md`:

```markdown
## Installation

### Basic Installation (Most Users)
```bash
pip install specql
```

This installs core SpecQL features:
- YAML → PostgreSQL schema generation
- Action compilation
- CLI tools

### Optional Features

#### Reverse Engineering
Convert existing SQL/TypeScript/Rust to SpecQL:
```bash
pip install specql[reverse]
```

#### Test Data Generation
Generate realistic test data with Faker:
```bash
pip install specql[testing]
```

#### Development
For contributing to SpecQL:
```bash
pip install specql[dev]
```

#### All Features
```bash
pip install specql[all]
```
```

4. **Run Final Verification** (1 hour)

```bash
# Test core installation
pip install -e ".[dev]"
uv run pytest tests/unit/core tests/unit/generators tests/unit/schema

# Test with reverse engineering
pip install -e ".[all]"
uv run pytest

# Test CLI
specql --help
specql generate --help
specql validate --help

# Expected: All commands work, helpful error messages
```

**Commit Point**: `git commit -m "docs: document optional dependencies and coverage"`

**Day 2 Deliverable**: ✅ 0 test collection errors, graceful skips

---

### **Day 3: Coverage Analysis & Planning** (Wednesday)

#### **Morning Session (4 hours): Pattern Test Planning**

**Tasks**:

1. **Analyze Existing Patterns** (1 hour)

```bash
# List implemented patterns
find stdlib/actions stdlib/schema -name "*.yaml"

# Review pattern specifications
cat stdlib/actions/temporal/non_overlapping_daterange.yaml
cat stdlib/actions/validation/recursive_dependency_validator.yaml
cat stdlib/schema/aggregate_view.yaml
```

2. **Design Pattern Test Strategy** (2 hours)

Create `tests/unit/patterns/README.md`:

```markdown
# Pattern Testing Strategy

## Test Structure

Each pattern gets a dedicated test module with:
1. **Schema Tests** (5-8 tests): Verify DDL generation
2. **Validation Tests** (5-8 tests): Verify runtime behavior
3. **Integration Tests** (5-8 tests): Verify with actions/entities
4. **Edge Case Tests** (3-5 tests): Verify error handling

## Test Template

```python
import pytest
from src.core.parser import SpecQLParser
from src.generators.schema.schema_orchestrator import SchemaOrchestrator

class TestPatternName:
    """Test suite for pattern_name pattern."""

    @pytest.fixture
    def entity_yaml(self):
        """Base entity with pattern."""
        return '''
entity: TestEntity
schema: test
fields:
  field1: text
patterns:
  - type: pattern_name
    params:
      param1: value1
'''

    # Schema Generation Tests
    def test_schema_extension_applied(self, entity_yaml):
        """Verify pattern adds schema extensions."""
        pass

    def test_indexes_generated(self, entity_yaml):
        """Verify pattern adds required indexes."""
        pass

    # ... more tests
```

## Pattern Test Matrix

| Pattern | Schema Tests | Validation Tests | Integration Tests | Total |
|---------|--------------|------------------|-------------------|-------|
| non_overlapping_daterange | 8 | 5 | 7 | 20 |
| recursive_dependency_validator | 6 | 10 | 8 | 24 |
| aggregate_view | 8 | 5 | 7 | 20 |
| scd_type2_helper | 6 | 6 | 6 | 18 |
| template_inheritance | 5 | 5 | 6 | 16 |
| computed_column | 6 | 4 | 4 | 14 |
| **Total** | **39** | **35** | **38** | **112** |

Target: 112 new tests for patterns
```

3. **Create Test File Structure** (1 hour)

```bash
# Create test directories
mkdir -p tests/unit/patterns/temporal
mkdir -p tests/unit/patterns/validation
mkdir -p tests/unit/patterns/schema

# Create test files (stubs)
touch tests/unit/patterns/temporal/test_non_overlapping_daterange.py
touch tests/unit/patterns/temporal/test_scd_type2_helper.py
touch tests/unit/patterns/validation/test_recursive_dependency_validator.py
touch tests/unit/patterns/validation/test_template_inheritance_validator.py
touch tests/unit/patterns/schema/test_aggregate_view.py
touch tests/unit/patterns/schema/test_computed_column.py

# Create shared fixtures
touch tests/unit/patterns/conftest.py
```

**Commit Point**: `git commit -m "test: create pattern test infrastructure"`

---

#### **Afternoon Session (4 hours): First Pattern Tests**

**Objective**: Implement complete test suite for `non_overlapping_daterange`

**Tasks**:

1. **Schema Generation Tests** (2 hours)

Create `tests/unit/patterns/temporal/test_non_overlapping_daterange.py`:

```python
"""Tests for temporal non-overlapping daterange pattern."""

import pytest
from src.core.parser import SpecQLParser
from src.generators.schema.table_generator import TableGenerator


class TestNonOverlappingDateRange:
    """Test temporal non-overlapping daterange pattern."""

    @pytest.fixture
    def allocation_entity(self):
        """Machine allocation entity with temporal pattern."""
        return """
entity: Allocation
schema: operations
fields:
  machine: ref(Machine)
  product: ref(Product)
  start_date: date
  end_date: date
  quantity: integer
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [machine]
      start_date_field: start_date
      end_date_field: end_date
      check_mode: strict
      allow_adjacent: true
"""

    def test_computed_daterange_column_added(self, allocation_entity):
        """Test that computed daterange column is generated."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_entity)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify computed column exists
        assert "start_date_end_date_range DATERANGE" in ddl
        assert "GENERATED ALWAYS AS (daterange(start_date, end_date, '[]'))" in ddl
        assert "STORED" in ddl

    def test_gist_index_created(self, allocation_entity):
        """Test that GIST index on daterange is created."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_entity)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify GIST index
        assert "CREATE INDEX idx_tb_allocation_daterange" in ddl
        assert "USING gist" in ddl
        assert "(start_date_end_date_range)" in ddl

    def test_exclusion_constraint_strict_mode(self, allocation_entity):
        """Test that EXCLUSION constraint is generated in strict mode."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_entity)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify exclusion constraint
        assert "ALTER TABLE operations.tb_allocation" in ddl
        assert "ADD CONSTRAINT excl_allocation_no_overlap" in ddl
        assert "EXCLUDE USING gist" in ddl
        assert "(machine WITH =, start_date_end_date_range WITH &&)" in ddl

    def test_nullable_end_date_supported(self, allocation_entity):
        """Test that NULL end_date (open-ended ranges) is supported."""
        # Modify YAML to allow NULL end_date
        yaml_with_null = allocation_entity.replace(
            "end_date: date",
            "end_date: date?\n"
        )

        parser = SpecQLParser()
        entity = parser.parse(yaml_with_null)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify computed column handles NULL
        assert "daterange(start_date, end_date, '[]')" in ddl
        # PostgreSQL daterange handles NULL end_date as unbounded

    def test_multiple_scope_fields(self):
        """Test pattern with multiple scope fields."""
        yaml = """
entity: Allocation
schema: operations
fields:
  machine: ref(Machine)
  product: ref(Product)
  start_date: date
  end_date: date
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [machine, product]
      start_date_field: start_date
      end_date_field: end_date
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify exclusion constraint includes both scope fields
        assert "(machine WITH =, product WITH =, start_date_end_date_range WITH &&)" in ddl

    def test_warning_mode_no_constraint(self):
        """Test that warning mode doesn't add EXCLUSION constraint."""
        yaml = """
entity: Allocation
schema: operations
fields:
  machine: ref(Machine)
  start_date: date
  end_date: date
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [machine]
      check_mode: warning
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify NO exclusion constraint
        assert "EXCLUDE USING gist" not in ddl
        # But computed column and index still present
        assert "start_date_end_date_range DATERANGE" in ddl
        assert "USING gist" in ddl

    def test_adjacent_ranges_configurable(self):
        """Test that adjacent ranges can be disallowed."""
        yaml = """
entity: Allocation
schema: operations
fields:
  machine: ref(Machine)
  start_date: date
  end_date: date
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [machine]
      allow_adjacent: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify exclusion uses && (overlaps) instead of &&= (overlaps or adjacent)
        # When allow_adjacent=false, we want strict overlap check
        assert "WITH &&" in ddl

    def test_fraiseql_metadata_includes_pattern(self, allocation_entity):
        """Test that FraiseQL comments include pattern info."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_entity)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify FraiseQL comment
        assert "COMMENT ON TABLE operations.tb_allocation" in ddl
        assert "@fraiseql:pattern:temporal_non_overlapping_daterange" in ddl
```

2. **Run Tests & Fix Issues** (2 hours)

```bash
# Run pattern tests
uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py -v

# Expected: Some tests fail (pattern not fully implemented)
# This is TDD - write tests first, implement after
```

**Tasks**:
- If tests fail (expected), note which features need implementation
- Start implementing pattern in schema generator
- Iterate until all 8 tests pass

**Commit Point**: `git commit -m "test: add tests for non_overlapping_daterange pattern"`

**Day 3 Deliverable**: ✅ 8 tests for temporal daterange pattern

---

### **Day 4-5: Complete Pattern Test Suites** (Thursday-Friday)

#### **Day 4: Recursive Dependency Validator** (24 tests)

**Focus**: `recursive_dependency_validator` pattern testing

**Morning** (4 hours): Schema + Validation Tests (15 tests)
**Afternoon** (4 hours): Integration + Edge Cases (9 tests)

**Key Test Areas**:
1. Recursive CTE generation (5 tests)
2. REQUIRES validation (4 tests)
3. REQUIRES_ONE_OF groups (3 tests)
4. CONFLICTS_WITH rules (3 tests)
5. Circular dependency detection (3 tests)
6. Category limits (2 tests)
7. Performance with large graphs (2 tests)
8. Integration with product configuration (2 tests)

**Deliverable**: 24 tests passing

---

#### **Day 5: Aggregate View Pattern** (20 tests)

**Focus**: `aggregate_view` pattern testing

**Morning** (4 hours): View Generation Tests (12 tests)
**Afternoon** (4 hours): Refresh + Integration Tests (8 tests)

**Key Test Areas**:
1. Materialized view DDL (4 tests)
2. FILTER clause support (3 tests)
3. Aggregate functions (3 tests)
4. Index generation (2 tests)
5. Refresh strategies (3 tests)
6. Dependency ordering (2 tests)
7. Performance benchmarks (2 tests)
8. FraiseQL integration (1 test)

**Deliverable**: 20 tests passing

---

### **Day 6-7: Missing Pattern Implementation** (Weekend/Extended)

#### **Day 6: SCD Type 2 Helper** (18 tests)

**Morning** (4 hours):
1. Design `scd_type2_helper.yaml` pattern spec (1 hour)
2. Implement pattern schema extensions (2 hours)
3. Write schema generation tests (1 hour)

**Afternoon** (4 hours):
1. Implement version management functions (2 hours)
2. Write validation tests (1 hour)
3. Write integration tests (1 hour)

**Pattern Specification**:
```yaml
pattern: temporal_scd_type2_helper
version: 1.0
description: "Slowly Changing Dimension Type 2 with automatic versioning"

parameters:
  - name: natural_key
    type: array<string>
    required: true
    description: "Fields that uniquely identify the business entity"

  - name: version_field
    type: string
    default: version_number

  - name: is_current_field
    type: string
    default: is_current

  - name: effective_date_field
    type: string
    default: effective_date

  - name: expiry_date_field
    type: string
    default: expiry_date

schema_extensions:
  fields:
    - name: "{{ version_field }}"
      type: integer
      default: 1
      comment: "Version number (increments on change)"

    - name: "{{ is_current_field }}"
      type: boolean
      default: true
      comment: "True for current version"

    - name: "{{ effective_date_field }}"
      type: timestamptz
      default: now()
      comment: "When this version became effective"

    - name: "{{ expiry_date_field }}"
      type: timestamptz
      nullable: true
      comment: "When this version was superseded (NULL for current)"

  constraints:
    # Only one current version per natural key
    - type: unique
      fields: "{{ natural_key + [is_current_field] }}"
      where: "{{ is_current_field }} = true"
      comment: "Ensure only one current version per business entity"

  indexes:
    # Fast current version lookups
    - fields: "{{ natural_key + [is_current_field] }}"
      where: "{{ is_current_field }} = true"
      comment: "Index for current version queries"

    # Fast history lookups
    - fields: "{{ natural_key + [effective_date_field] }}"
      comment: "Index for temporal queries"

action_helpers:
  - function: "create_new_version_{{ entity.name | lower }}"
    returns: "uuid"
    params:
      - name: "natural_key_values"
        type: "jsonb"
      - name: "new_data"
        type: "jsonb"
    logic: |
      -- Expire current version
      UPDATE {{ schema }}.tb_{{ entity.name | lower }}
      SET
        {{ is_current_field }} = false,
        {{ expiry_date_field }} = now(),
        updated_at = now()
      WHERE {{ natural_key_where_clause }}
        AND {{ is_current_field }} = true;

      -- Insert new version
      INSERT INTO {{ schema }}.tb_{{ entity.name | lower }} (...)
      VALUES (...)
      RETURNING id;

  - function: "get_current_version_{{ entity.name | lower }}"
    returns: "uuid"
    params:
      - name: "natural_key_values"
        type: "jsonb"
    logic: |
      SELECT id
      FROM {{ schema }}.tb_{{ entity.name | lower }}
      WHERE {{ natural_key_where_clause }}
        AND {{ is_current_field }} = true;

  - function: "get_version_at_time_{{ entity.name | lower }}"
    returns: "uuid"
    params:
      - name: "natural_key_values"
        type: "jsonb"
      - name: "as_of_time"
        type: "timestamptz"
    logic: |
      SELECT id
      FROM {{ schema }}.tb_{{ entity.name | lower }}
      WHERE {{ natural_key_where_clause }}
        AND {{ effective_date_field }} <= as_of_time
        AND ({{ expiry_date_field }} IS NULL OR {{ expiry_date_field }} > as_of_time)
      LIMIT 1;
```

**Deliverable**: 18 tests for SCD Type 2 pattern

---

#### **Day 7: Template Inheritance + Computed Column** (30 tests)

**Morning** (4 hours): Template Inheritance Validator (16 tests)
**Afternoon** (4 hours): Computed Column Pattern (14 tests)

**Template Inheritance Spec**:
```yaml
pattern: validation_template_inheritance
version: 1.0
description: "Resolve configuration from template hierarchy (model → parent → generic)"

parameters:
  - name: template_field
    type: string
    default: template_id
    description: "Field linking to template entity"

  - name: template_entity
    type: string
    required: true
    description: "Entity name of template (e.g., ProductTemplate)"

  - name: merge_strategy
    type: enum
    values: [override, merge, append]
    default: override
    description: "How to merge inherited values"

  - name: max_depth
    type: integer
    default: 5
    description: "Maximum template hierarchy depth"

action_helpers:
  - function: "resolve_template_{{ entity.name | lower }}"
    returns: "jsonb"
    params:
      - name: "entity_id"
        type: "uuid"
    logic: |
      -- Recursive CTE to traverse template hierarchy
      WITH RECURSIVE template_chain AS (
        -- Base case: entity's direct template
        SELECT
          1 as depth,
          {{ template_field }} as template_id,
          config_data
        FROM {{ schema }}.tb_{{ entity.name | lower }}
        WHERE id = entity_id

        UNION ALL

        -- Recursive case: parent templates
        SELECT
          tc.depth + 1,
          t.{{ template_field }},
          t.config_data
        FROM template_chain tc
        JOIN {{ schema }}.tb_{{ template_entity | lower }} t
          ON t.id = tc.template_id
        WHERE tc.depth < max_depth
          AND tc.template_id IS NOT NULL
      )
      SELECT jsonb_merge_recursive(
        config_data ORDER BY depth DESC
      ) as resolved_config
      FROM template_chain;
```

**Computed Column Spec**:
```yaml
pattern: schema_computed_column
version: 1.0
description: "Add GENERATED ALWAYS AS computed columns"

parameters:
  - name: column_name
    type: string
    required: true

  - name: expression
    type: string
    required: true
    description: "SQL expression for computed value"

  - name: stored
    type: boolean
    default: true
    description: "STORED (pre-computed) vs VIRTUAL (computed on read)"

  - name: index
    type: boolean
    default: false
    description: "Create index on computed column"

schema_extensions:
  computed_columns:
    - name: "{{ column_name }}"
      type: "inferred from expression"
      expression: "{{ expression }}"
      stored: "{{ stored }}"
      comment: "Computed column: {{ expression }}"

  indexes:
    - fields: ["{{ column_name }}"]
      when: "{{ index }}"
```

**Deliverable**: 30 tests for final 2 patterns

---

## 📊 Week 1 Success Metrics

### **Quantitative Metrics**
- ✅ Test collection errors: 60 → 0 (100% reduction)
- ✅ Core tests passing: 384/384 (100%)
- ✅ Pattern tests added: 0 → 112 (NEW)
- ✅ Total tests: 384 → 496 (29% increase)
- ✅ Test coverage: 87% → 95% (+8%)

### **Qualitative Metrics**
- ✅ Optional dependencies properly organized
- ✅ Graceful degradation for reverse engineering
- ✅ Helpful error messages when deps missing
- ✅ All 6 v0.6.0 patterns have test coverage
- ✅ Pattern test infrastructure reusable

### **Deliverables**
- ✅ `pyproject.toml` with organized dependencies
- ✅ `src/core/dependencies.py` utility module
- ✅ Updated `conftest.py` with pytest markers
- ✅ 112 new pattern tests in `tests/unit/patterns/`
- ✅ Documentation: `docs/architecture/DEPENDENCY_STRATEGY.md`
- ✅ Documentation: `tests/unit/patterns/README.md`

---

## 🚀 Handoff to Week 2

**Status Check**:
```bash
# Verify all tests pass
uv run pytest

# Expected output:
# ==================== 496 passed, 0 failed, 68 skipped ====================
# (Skipped = optional dependencies not installed)

# With all deps:
uv pip install -e ".[all]"
uv run pytest

# Expected output:
# ==================== 564 passed, 0 failed, 0 skipped ====================
```

**Next Week Preview**:
- Week 2 focuses on implementing the 3 missing patterns based on tests written this week
- CLI improvements and test fixes
- Integration with schema generator

**Risk Assessment**: ✅ **LOW RISK**
- Test infrastructure is solid foundation
- Pattern tests provide clear implementation roadmap
- Dependencies properly managed

---

**Week 1 Completion Criteria**:
- [ ] All 60 collection errors resolved
- [ ] 0 import errors (with or without optional deps)
- [ ] 112 new pattern tests written
- [ ] Documentation updated
- [ ] Coverage increased to 95%+

**Confidence Level**: 95% ✅
