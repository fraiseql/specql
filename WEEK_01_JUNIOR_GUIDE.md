# Week 1 Junior Engineer Guide: Pattern Testing Foundation

**Target Audience**: Junior engineers new to SpecQL
**Prerequisites**: Basic Python, pytest basics, SQL fundamentals
**Time Estimate**: 7 days (8 hours/day)
**Status**: Computed Column ✅ Done | Others ⚠️ Need Help

---

## 📚 Table of Contents

1. [Understanding Patterns](#understanding-patterns)
2. [Day 1-2: Dependency Management](#day-1-2-dependency-management)
3. [Day 3: Pattern Test Infrastructure](#day-3-pattern-test-infrastructure)
4. [Day 4: Temporal Non-Overlapping DateRange](#day-4-temporal-non-overlapping-daterange)
5. [Day 5: Recursive Dependency Validator](#day-5-recursive-dependency-validator)
6. [Day 6: Aggregate View Pattern](#day-6-aggregate-view-pattern)
7. [Day 7: SCD Type 2 Helper](#day-7-scd-type-2-helper)
8. [Common Pitfalls & Solutions](#common-pitfalls--solutions)

---

## Understanding Patterns

### What is a Pattern?

A **pattern** is a reusable piece of functionality that extends entities in SpecQL. Think of it like a "plugin" that adds specific behavior to your database schema.

**Real-World Example**:
```yaml
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
```

This pattern automatically:
- Prevents double-booking a machine
- Creates indexes for fast lookups
- Adds database constraints

### Why Test Patterns?

Patterns generate complex SQL code. Tests ensure:
1. **Correctness**: Generated SQL is valid
2. **Completeness**: All features work
3. **Edge Cases**: Handles nulls, errors, etc.

---

## Day 1-2: Dependency Management

### 🎯 Goal
Organize dependencies so tests can run with or without optional features (like SQL parsing libraries).

### 📝 Concepts You Need

#### What are Dependencies?
Libraries your code needs to run. Example:
- `pyyaml` - Parse YAML files (REQUIRED)
- `pglast` - Parse SQL syntax (OPTIONAL - only for reverse engineering)

#### Why Optional Dependencies?
- Faster install for most users
- Smaller package size
- Clear feature boundaries

### 🛠️ Step-by-Step Implementation

#### Step 1: Update `pyproject.toml`

**Location**: `/home/lionel/code/specql/pyproject.toml`

**Find this section**:
```toml
[project]
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.1.2",
    # ... many dependencies
]
```

**Change to**:
```toml
[project]
# ONLY core dependencies here
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.1.2",
    "click>=8.1.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
# Reverse engineering (optional)
reverse = [
    "pglast>=7.10",
    "tree-sitter>=0.20.0",
]

# Development tools
dev = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
]

# Everything
all = [
    "specql[dev,reverse]",
]
```

**Why?**
- Users installing SpecQL don't need `pglast` (SQL parser) unless they're doing reverse engineering
- Makes the package smaller and faster to install

#### Step 2: Create Dependency Checker

**Create file**: `src/core/dependencies.py`

```python
"""Check if optional dependencies are installed."""

import importlib.util
from typing import Optional


class OptionalDependency:
    """Represents an optional dependency."""

    def __init__(self, package_name: str, pip_extra: str, purpose: str):
        """
        Args:
            package_name: Import name (e.g., "pglast")
            pip_extra: Install group (e.g., "reverse")
            purpose: Human-readable purpose
        """
        self.package_name = package_name
        self.pip_extra = pip_extra
        self.purpose = purpose
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Check if dependency is installed."""
        if self._available is None:
            # Try to find the package
            self._available = importlib.util.find_spec(self.package_name) is not None
        return self._available

    def require(self) -> None:
        """Raise error if dependency not available."""
        if not self.available:
            raise ImportError(
                f"\n{self.purpose} requires {self.package_name}.\n"
                f"Install with: pip install specql[{self.pip_extra}]\n"
            )


# Define dependencies
PGLAST = OptionalDependency(
    package_name="pglast",
    pip_extra="reverse",
    purpose="SQL parsing for reverse engineering",
)
```

**How to Use**:
```python
from src.core.dependencies import PGLAST

# Check if available
if PGLAST.available:
    import pglast
    # Use pglast...

# Or require it (raises error if not installed)
PGLAST.require()
import pglast
```

#### Step 3: Update Pytest Config

**Edit**: `conftest.py` (in project root)

**Add this code**:
```python
import pytest
from src.core.dependencies import PGLAST

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_pglast: test requires pglast (SQL parsing)"
    )

def pytest_collection_modifyitems(config, items):
    """Skip tests that need unavailable dependencies."""
    skip_pglast = pytest.mark.skip(
        reason="pglast not installed (pip install specql[reverse])"
    )

    for item in items:
        if "requires_pglast" in item.keywords and not PGLAST.available:
            item.add_marker(skip_pglast)
```

**What this does**:
- Defines a `@pytest.mark.requires_pglast` decorator
- Automatically skips tests if `pglast` is not installed
- Shows helpful error message

#### Step 4: Mark Tests

**Example test**:
```python
import pytest

@pytest.mark.requires_pglast
def test_sql_parsing():
    """This test needs pglast."""
    from pglast import parse_sql
    # Test code...
```

**Result**:
- If `pglast` installed: Test runs normally
- If `pglast` NOT installed: Test is skipped with helpful message

### ✅ Verification

```bash
# Install WITHOUT optional deps
uv pip install -e ".[dev]"
uv run pytest

# Expected: Some tests skipped (that's OK!)
# ==================== 400 passed, 50 skipped ====================

# Install WITH optional deps
uv pip install -e ".[all]"
uv run pytest

# Expected: All tests run
# ==================== 450 passed, 0 skipped ====================
```

### 🚨 Common Mistakes

1. **Putting optional deps in main dependencies**
   - ❌ Bad: All users install pglast
   - ✅ Good: Only users who need it install pglast

2. **Forgetting pytest markers**
   - ❌ Bad: Tests fail with import errors
   - ✅ Good: Tests are skipped with helpful message

3. **Wrong import check**
   ```python
   # ❌ Bad - will fail if not installed
   import pglast

   # ✅ Good - checks first
   from src.core.dependencies import PGLAST
   PGLAST.require()
   import pglast
   ```

---

## Day 3: Pattern Test Infrastructure

### 🎯 Goal
Create shared fixtures and utilities for testing patterns.

### 📝 Concepts You Need

#### What is a Fixture?
A pytest fixture is reusable test data. Instead of writing the same YAML in every test, create it once:

```python
@pytest.fixture
def simple_entity():
    """Reusable entity definition."""
    return """
entity: Contact
schema: crm
fields:
  email: text
"""

def test_something(simple_entity):
    # Use simple_entity here
    parser = SpecQLParser()
    entity = parser.parse(simple_entity)
```

### 🛠️ Step-by-Step Implementation

#### Step 1: Create Test Directory Structure

```bash
# Create directories
mkdir -p tests/unit/patterns/temporal
mkdir -p tests/unit/patterns/validation
mkdir -p tests/unit/patterns/schema

# Create __init__.py files (makes them Python packages)
touch tests/unit/patterns/__init__.py
touch tests/unit/patterns/temporal/__init__.py
touch tests/unit/patterns/validation/__init__.py
touch tests/unit/patterns/schema/__init__.py
```

#### Step 2: Create Shared Fixtures

**Create**: `tests/unit/patterns/conftest.py`

```python
"""Shared fixtures for pattern tests."""

import pytest
from src.core.parser import SpecQLParser
from src.generators.schema.table_generator import TableGenerator


@pytest.fixture
def parser():
    """Reusable SpecQL parser."""
    return SpecQLParser()


@pytest.fixture
def simple_entity_yaml():
    """Basic entity without patterns."""
    return """
entity: TestEntity
schema: test
fields:
  name: text
  value: integer
"""


@pytest.fixture
def entity_with_refs_yaml():
    """Entity with foreign key references."""
    return """
entity: Order
schema: sales
fields:
  customer: ref(Customer)
  product: ref(Product)
  quantity: integer
"""


def generate_ddl(yaml_content: str) -> str:
    """
    Helper function to generate DDL from YAML.

    Args:
        yaml_content: SpecQL YAML string

    Returns:
        Generated SQL DDL
    """
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)
    generator = TableGenerator(entity)
    return generator.generate()
```

**Why?**
- Fixtures reduce code duplication
- Tests are easier to read
- Changes to test data happen in one place

#### Step 3: Create Test Template

**Create**: `tests/unit/patterns/README.md`

```markdown
# Pattern Testing Guide

## Test Structure

Each pattern test file should have:

1. **Schema Generation Tests** - Verify DDL output
2. **Validation Tests** - Verify runtime behavior
3. **Integration Tests** - Verify with other features
4. **Edge Case Tests** - Verify error handling

## Test Template

```python
import pytest
from src.core.parser import SpecQLParser
from src.generators.schema.table_generator import TableGenerator


class TestPatternName:
    """Test suite for pattern_name pattern."""

    @pytest.fixture
    def entity_with_pattern(self):
        """Entity using this pattern."""
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

    def test_schema_generation(self, entity_with_pattern):
        """Test that pattern generates correct SQL."""
        parser = SpecQLParser()
        entity = parser.parse(entity_with_pattern)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify expected SQL is present
        assert "EXPECTED_SQL_FRAGMENT" in ddl
```

## Running Pattern Tests

```bash
# All pattern tests
uv run pytest tests/unit/patterns -v

# Specific pattern
uv run pytest tests/unit/patterns/schema/test_computed_column.py -v

# Single test
uv run pytest tests/unit/patterns/schema/test_computed_column.py::TestComputedColumn::test_basic_computation -v
```
```

### ✅ Verification

```bash
# Run tests (should pass even with no pattern tests yet)
uv run pytest tests/unit/patterns -v

# Should show:
# ==================== no tests ran ====================
# (That's OK - we haven't written tests yet!)
```

---

## Day 4: Temporal Non-Overlapping DateRange

### 🎯 Goal
Test a pattern that prevents overlapping date ranges (e.g., prevent double-booking a machine).

### 📝 Concepts You Need

#### What is a DateRange?
PostgreSQL has a special `daterange` type:
```sql
-- Check if two date ranges overlap
SELECT daterange('2024-01-01', '2024-01-10') && daterange('2024-01-05', '2024-01-15');
-- Result: TRUE (they overlap)
```

#### What is a GIST Index?
A special index type for range queries:
```sql
CREATE INDEX idx_allocation_daterange
ON allocations
USING gist(machine_id, date_range);
-- Makes overlap checks FAST
```

#### What is an EXCLUSION Constraint?
Prevents overlapping ranges:
```sql
ALTER TABLE allocations
ADD CONSTRAINT no_overlap
EXCLUDE USING gist (machine_id WITH =, date_range WITH &&);
-- Blocks inserts that would overlap
```

### 🛠️ Step-by-Step Implementation

#### Step 1: Understand the Pattern

**Pattern YAML** (`stdlib/actions/temporal/non_overlapping_daterange.yaml`):
```yaml
pattern: temporal_non_overlapping_daterange
version: 1.0
description: "Prevent overlapping date ranges within a scope"

parameters:
  - name: scope_fields
    type: array<string>
    required: true
    description: "Fields that define scope (e.g., [machine_id])"

  - name: start_date_field
    type: string
    required: true

  - name: end_date_field
    type: string
    required: true

  - name: check_mode
    type: enum
    values: [strict, warning]
    default: strict
```

**What it does**:
1. Creates a computed `daterange` column
2. Creates a GIST index on that column
3. (Optional) Creates an EXCLUSION constraint to prevent overlaps

#### Step 2: Write Schema Generation Tests

**Create**: `tests/unit/patterns/temporal/test_non_overlapping_daterange.py`

```python
"""Tests for temporal non-overlapping daterange pattern."""

import pytest
from src.core.parser import SpecQLParser
from src.generators.schema.table_generator import TableGenerator


class TestNonOverlappingDateRange:
    """Test temporal non-overlapping daterange pattern."""

    @pytest.fixture
    def allocation_yaml(self):
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
"""

    def test_computed_daterange_column_added(self, allocation_yaml):
        """Test that pattern adds computed daterange column."""
        # STEP 1: Parse YAML
        parser = SpecQLParser()
        entity = parser.parse(allocation_yaml)

        # STEP 2: Generate DDL
        generator = TableGenerator(entity)
        ddl = generator.generate()

        # STEP 3: Verify computed column exists
        # Expected SQL:
        # start_date_end_date_range DATERANGE
        # GENERATED ALWAYS AS (daterange(start_date, end_date, '[]')) STORED

        assert "start_date_end_date_range" in ddl, \
            "Missing computed daterange column"
        assert "DATERANGE" in ddl, \
            "Column should be DATERANGE type"
        assert "GENERATED ALWAYS AS" in ddl, \
            "Should be a computed column"
        assert "daterange(start_date, end_date" in ddl, \
            "Should compute range from start/end dates"
        assert "STORED" in ddl, \
            "Should be STORED (not VIRTUAL)"

    def test_gist_index_created(self, allocation_yaml):
        """Test that GIST index on daterange is created."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_yaml)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Expected SQL:
        # CREATE INDEX idx_tb_allocation_daterange
        # ON operations.tb_allocation
        # USING gist(machine, start_date_end_date_range);

        assert "CREATE INDEX" in ddl, \
            "Should create an index"
        assert "USING gist" in ddl, \
            "Should use GIST index type"
        assert "start_date_end_date_range" in ddl, \
            "Index should include daterange column"

    def test_exclusion_constraint_strict_mode(self, allocation_yaml):
        """Test that EXCLUSION constraint is generated in strict mode."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_yaml)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Expected SQL:
        # ALTER TABLE operations.tb_allocation
        # ADD CONSTRAINT excl_allocation_no_overlap
        # EXCLUDE USING gist (machine WITH =, start_date_end_date_range WITH &&);

        assert "EXCLUDE USING gist" in ddl, \
            "Strict mode should create EXCLUSION constraint"
        assert "WITH =" in ddl, \
            "Should check scope field equality"
        assert "WITH &&" in ddl, \
            "Should check daterange overlap"

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
      start_date_field: start_date
      end_date_field: end_date
      check_mode: warning
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        generator = TableGenerator(entity)
        ddl = generator.generate()

        # Verify NO exclusion constraint
        assert "EXCLUDE USING gist" not in ddl, \
            "Warning mode should NOT create EXCLUSION constraint"

        # But computed column and index still present
        assert "start_date_end_date_range DATERANGE" in ddl, \
            "Should still have computed column"
        assert "USING gist" in ddl, \
            "Should still have GIST index"
```

#### Step 3: Run Tests

```bash
# Run the tests
uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py -v

# Expected: Some tests may FAIL (pattern not fully implemented yet)
# That's OK - this is TDD (Test-Driven Development)
```

#### Step 4: Debug Failing Tests

**If tests fail, check**:

1. **Is the pattern being applied?**
   ```python
   # Add debug print in test:
   print(f"Entity patterns: {entity.patterns}")
   ```

2. **Is DDL generation working?**
   ```python
   # Add debug print in test:
   print(f"Generated DDL:\n{ddl}")
   ```

3. **Is pattern applier registered?**
   Check `src/generators/schema/pattern_applier.py`:
   ```python
   PATTERN_APPLIERS = {
       "temporal_non_overlapping_daterange": apply_temporal_daterange,
       # Should be here!
   }
   ```

### 🚨 Common Mistakes

1. **Wrong assertion messages**
   ```python
   # ❌ Bad - no helpful message
   assert "DATERANGE" in ddl

   # ✅ Good - tells you what's wrong
   assert "DATERANGE" in ddl, \
       "Expected DATERANGE column but not found in DDL"
   ```

2. **Too specific assertions**
   ```python
   # ❌ Bad - breaks if spacing changes
   assert "DATERANGE GENERATED" in ddl

   # ✅ Good - checks each part separately
   assert "DATERANGE" in ddl
   assert "GENERATED" in ddl
   ```

3. **Not checking case sensitivity**
   ```python
   # ❌ Bad - might fail if SQL uses lowercase
   assert "DATERANGE" in ddl

   # ✅ Better - case insensitive
   assert "daterange" in ddl.lower()
   ```

---

## Day 5: Recursive Dependency Validator

### 🎯 Goal
Test a pattern that validates recursive dependencies (e.g., "Product A requires Feature B").

### 📝 Concepts You Need

#### What is a Recursive CTE?
A SQL query that references itself:
```sql
WITH RECURSIVE dependencies AS (
  -- Base case: direct dependencies
  SELECT feature_id, requires_feature_id
  FROM feature_dependencies
  WHERE feature_id = 'bluetooth'

  UNION ALL

  -- Recursive case: dependencies of dependencies
  SELECT fd.feature_id, fd.requires_feature_id
  FROM feature_dependencies fd
  JOIN dependencies d ON d.requires_feature_id = fd.feature_id
)
SELECT * FROM dependencies;
-- Returns: bluetooth → wifi → power_management → ...
```

#### What are Validation Rules?

**REQUIRES**: Feature A needs Feature B
```yaml
rules:
  - bluetooth REQUIRES wifi
```

**REQUIRES_ONE_OF**: Feature A needs at least one of [B, C]
```yaml
rules:
  - camera REQUIRES_ONE_OF [flash, hdr]
```

**CONFLICTS_WITH**: Feature A cannot coexist with Feature B
```yaml
rules:
  - low_power_mode CONFLICTS_WITH high_performance_mode
```

### 🛠️ Step-by-Step Implementation

#### Step 1: Understand the Pattern

**Example Usage**:
```yaml
entity: ProductConfiguration
schema: catalog
fields:
  product: ref(Product)
  selected_features: list(ref(Feature))
patterns:
  - type: validation_recursive_dependency_validator
    params:
      dependency_entity: FeatureDependency
      max_depth: 10
```

**What it does**:
1. Creates validation function that checks dependencies
2. Uses recursive CTE to find all dependencies
3. Returns errors if dependencies missing or conflicts exist

#### Step 2: Write Tests (Simplified)

**Create**: `tests/unit/patterns/validation/test_recursive_dependency_validator.py`

```python
"""Tests for recursive dependency validator pattern."""

import pytest
from src.core.parser import SpecQLParser


class TestRecursiveDependencyValidator:
    """Test recursive dependency validation pattern."""

    @pytest.fixture
    def config_yaml(self):
        """Product configuration with dependency validation."""
        return """
entity: ProductConfiguration
schema: catalog
fields:
  product: ref(Product)
  features: list(ref(Feature))
patterns:
  - type: validation_recursive_dependency_validator
    params:
      dependency_entity: FeatureDependency
      max_depth: 10
"""

    def test_validation_function_created(self, config_yaml):
        """Test that pattern creates validation function."""
        parser = SpecQLParser()
        entity = parser.parse(config_yaml)

        # Pattern should add a validation action
        # (Implementation detail: check entity.actions or entity.validation_functions)

        # For now, just verify pattern is parsed
        assert len(entity.patterns) == 1
        assert entity.patterns[0].type == "validation_recursive_dependency_validator"

    def test_recursive_cte_in_function(self, config_yaml):
        """Test that generated function uses recursive CTE."""
        # This test verifies the SQL generation
        # You would generate the function SQL and check for:
        # - WITH RECURSIVE keyword
        # - Base case query
        # - Recursive case with JOIN

        # For now, this is a placeholder
        # Real implementation would check generated SQL
        pass

    def test_max_depth_parameter(self, config_yaml):
        """Test that max_depth parameter is respected."""
        parser = SpecQLParser()
        entity = parser.parse(config_yaml)

        pattern = entity.patterns[0]
        assert pattern.params["max_depth"] == 10
```

**Note**: These tests are simpler because this pattern is more complex. Start with basic tests, add more as you understand the pattern better.

### 🚨 Helpful Tips for Complex Patterns

1. **Start Simple**: Test that pattern is parsed correctly
2. **Add Gradually**: Add more tests as you implement
3. **Use Debug Prints**: Print generated SQL to understand it
4. **Ask Questions**: Complex patterns take time to understand

---

## Day 6: Aggregate View Pattern

### 🎯 Goal
Test a pattern that creates materialized views for aggregations.

### 📝 Concepts You Need

#### What is a Materialized View?
A view that stores results physically:
```sql
CREATE MATERIALIZED VIEW sales_summary AS
SELECT
  product_id,
  COUNT(*) as order_count,
  SUM(quantity) as total_quantity
FROM orders
GROUP BY product_id;

-- Refresh when data changes
REFRESH MATERIALIZED VIEW sales_summary;
```

**Benefits**:
- Fast queries (pre-computed)
- Can add indexes
- Good for dashboards/reports

#### What is a FILTER Clause?
Conditional aggregation:
```sql
SELECT
  COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
  COUNT(*) FILTER (WHERE status = 'pending') as pending_count
FROM orders;
```

### 🛠️ Step-by-Step Implementation

**Create**: `tests/unit/patterns/schema/test_aggregate_view.py`

```python
"""Tests for aggregate view pattern."""

import pytest
from src.core.parser import SpecQLParser


class TestAggregateView:
    """Test aggregate view pattern."""

    @pytest.fixture
    def sales_summary_yaml(self):
        """Sales summary view with aggregations."""
        return """
entity: SalesSummary
schema: analytics
type: view
source_entity: Order
patterns:
  - type: schema_aggregate_view
    params:
      materialized: true
      refresh_strategy: on_demand
      aggregations:
        - field: order_count
          function: count
        - field: total_revenue
          function: sum
          source_field: amount
      group_by: [product_id, customer_id]
"""

    def test_materialized_view_created(self, sales_summary_yaml):
        """Test that pattern creates MATERIALIZED VIEW."""
        parser = SpecQLParser()
        entity = parser.parse(sales_summary_yaml)

        # Generate view DDL
        # (You would use a ViewGenerator here)

        # Verify pattern applied
        assert len(entity.patterns) == 1
        assert entity.patterns[0].type == "schema_aggregate_view"

    def test_aggregations_in_select(self, sales_summary_yaml):
        """Test that aggregations are added to SELECT."""
        # Generated SQL should include:
        # SELECT
        #   product_id,
        #   customer_id,
        #   COUNT(*) as order_count,
        #   SUM(amount) as total_revenue
        # FROM orders
        # GROUP BY product_id, customer_id

        # For now, just verify pattern params
        parser = SpecQLParser()
        entity = parser.parse(sales_summary_yaml)
        pattern = entity.patterns[0]

        assert len(pattern.params["aggregations"]) == 2
        assert pattern.params["aggregations"][0]["function"] == "count"
        assert pattern.params["aggregations"][1]["function"] == "sum"
```

---

## Day 7: SCD Type 2 Helper

### 🎯 Goal
Test a pattern for Slowly Changing Dimensions (versioning).

### 📝 Concepts You Need

#### What is SCD Type 2?
Tracks history by creating new versions:

**Example**: Customer address changes

| id | customer_id | address | version | is_current | effective_date | expiry_date |
|----|-------------|---------|---------|------------|----------------|-------------|
| 1  | c123       | 123 Oak St | 1    | FALSE      | 2024-01-01     | 2024-06-01  |
| 2  | c123       | 456 Elm St | 2    | TRUE       | 2024-06-01     | NULL        |

**Benefits**:
- Full history preserved
- Can query "as of" any date
- One current version per entity

### 🛠️ Step-by-Step Implementation

**Create**: `tests/unit/patterns/temporal/test_scd_type2_helper.py`

```python
"""Tests for SCD Type 2 helper pattern."""

import pytest
from src.core.parser import SpecQLParser


class TestSCDType2Helper:
    """Test SCD Type 2 pattern."""

    @pytest.fixture
    def customer_yaml(self):
        """Customer entity with version tracking."""
        return """
entity: Customer
schema: crm
fields:
  customer_number: text
  name: text
  address: text
  email: text
patterns:
  - type: temporal_scd_type2_helper
    params:
      natural_key: [customer_number]
      version_field: version_number
      is_current_field: is_current
      effective_date_field: effective_date
      expiry_date_field: expiry_date
"""

    def test_version_fields_added(self, customer_yaml):
        """Test that pattern adds version tracking fields."""
        parser = SpecQLParser()
        entity = parser.parse(customer_yaml)

        # Pattern should add these fields:
        # - version_number: integer
        # - is_current: boolean
        # - effective_date: timestamptz
        # - expiry_date: timestamptz (nullable)

        # Verify pattern parsed
        assert len(entity.patterns) == 1
        pattern = entity.patterns[0]
        assert pattern.params["natural_key"] == ["customer_number"]

    def test_unique_constraint_current_version(self, customer_yaml):
        """Test unique constraint on current version."""
        # Generated SQL should include:
        # CREATE UNIQUE INDEX idx_customer_current
        # ON crm.tb_customer (customer_number, is_current)
        # WHERE is_current = true;

        # This ensures only one current version per customer
        pass
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Tests Don't Run

**Symptom**:
```bash
$ uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py
ERROR: file not found
```

**Solution**:
1. Check file exists: `ls tests/unit/patterns/temporal/`
2. Check `__init__.py` files exist in each directory
3. Run from project root, not from `tests/` directory

### Pitfall 2: Import Errors

**Symptom**:
```python
ModuleNotFoundError: No module named 'src'
```

**Solution**:
Add to top of test file:
```python
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core.parser import SpecQLParser
```

### Pitfall 3: Assertions Fail with Unclear Errors

**Symptom**:
```
AssertionError
```

**Solution**:
Always add helpful messages:
```python
# ❌ Bad
assert "DATERANGE" in ddl

# ✅ Good
assert "DATERANGE" in ddl, \
    f"Expected DATERANGE in DDL but got:\n{ddl[:200]}"
```

### Pitfall 4: Tests Pass But Don't Test Anything

**Symptom**:
```python
def test_something():
    pass  # Test passes but does nothing!
```

**Solution**:
Always have at least one assertion:
```python
def test_something():
    result = do_something()
    assert result is not None, "Expected result but got None"
```

### Pitfall 5: Not Understanding What to Test

**Solution**:
Follow this checklist for each pattern:

1. **Parse Test**: Does pattern parse from YAML?
   ```python
   entity = parser.parse(yaml)
   assert len(entity.patterns) == 1
   ```

2. **Schema Test**: Does pattern modify DDL?
   ```python
   ddl = generate_ddl(yaml)
   assert "EXPECTED_SQL" in ddl
   ```

3. **Parameter Test**: Are parameters respected?
   ```python
   pattern = entity.patterns[0]
   assert pattern.params["key"] == "expected_value"
   ```

4. **Edge Case Test**: What if params are missing/invalid?
   ```python
   with pytest.raises(ValidationError):
       parser.parse(invalid_yaml)
   ```

---

## Quick Reference Commands

```bash
# Run all pattern tests
uv run pytest tests/unit/patterns -v

# Run specific pattern
uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py -v

# Run single test
uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py::TestNonOverlappingDateRange::test_computed_daterange_column_added -v

# Run with debug output
uv run pytest tests/unit/patterns -v -s

# Run with coverage
uv run pytest tests/unit/patterns --cov=src --cov-report=term-missing
```

---

## Getting Help

### When You're Stuck

1. **Read the Error Message Carefully**
   - Copy full error to a file
   - Read from bottom up
   - Look for the actual error (not traceback)

2. **Add Debug Prints**
   ```python
   print(f"Entity patterns: {entity.patterns}")
   print(f"Generated DDL:\n{ddl}")
   ```

3. **Check Existing Tests**
   - Look at `tests/unit/generators/test_table_generator.py`
   - See how other tests work

4. **Test Incrementally**
   - Start with simple test that just parses YAML
   - Add assertions one at a time
   - Run test after each change

5. **Ask for Help**
   - Include: What you tried, what happened, what you expected
   - Share: Code snippet, error message, test output

---

## Success Criteria

By end of Week 1, you should have:

- [ ] Dependencies organized in `pyproject.toml`
- [ ] Dependency checker in `src/core/dependencies.py`
- [ ] Pytest markers working in `conftest.py`
- [ ] Pattern test infrastructure in `tests/unit/patterns/`
- [ ] Tests for non_overlapping_daterange (10+ tests)
- [ ] Tests for recursive_dependency_validator (10+ tests)
- [ ] Tests for aggregate_view (8+ tests)
- [ ] Tests for scd_type2_helper (8+ tests)
- [ ] All tests running (passing or failing is OK!)

**Remember**: It's OK if tests fail initially. That's Test-Driven Development! You write tests first, then implement the features to make them pass.

---

**Good luck! You've got this! 🚀**
