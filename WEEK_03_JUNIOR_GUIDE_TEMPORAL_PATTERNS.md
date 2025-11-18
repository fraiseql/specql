# Week 3 Junior Guide: Temporal Non-Overlapping Daterange Pattern

**Target Audience**: Junior engineers
**Goal**: Fix 47 skipped temporal/validation pattern tests
**Prerequisites**: SCD Type 2 completed
**Time Estimate**: 5-6 days

---

## 📊 Current Status

```bash
uv run pytest tests/unit/patterns/temporal/ -v | grep SKIPPED | wc -l
# Result: 18 skipped tests (non-overlapping daterange)

uv run pytest tests/unit/patterns/validation/ -v | grep SKIPPED | wc -l
# Result: 29 skipped tests (recursive dependencies + template inheritance)
```

---

## 🎯 What is Non-Overlapping Daterange?

### Real-World Problem: Resource Double-Booking

Imagine any booking system (conference rooms, vehicles, equipment):

**Problem**: Two bookings overlap
```
Room A:
  Jan 1-10: Meeting 1   ──────────
  Jan 5-15: Meeting 2       ──────────
                            ^^^^ OVERLAP! Room can't host both!
```

**Solution**: PostgreSQL `EXCLUDE` constraint prevents overlaps
```sql
ALTER TABLE bookings
ADD CONSTRAINT no_overlap
EXCLUDE USING gist (resource_id WITH =, date_range WITH &&);
-- This blocks the second INSERT automatically!
```

---

## 📝 Key PostgreSQL Concepts

### 1. DATERANGE Type

PostgreSQL has built-in range types:
```sql
-- Create a date range
SELECT daterange('2024-01-01', '2024-01-10', '[)');
-- [2024-01-01, 2024-01-10) means: includes start, excludes end

-- Check if ranges overlap
SELECT daterange('2024-01-01', '2024-01-10') && daterange('2024-01-05', '2024-01-15');
-- Result: TRUE (they overlap)

-- Check if ranges are adjacent
SELECT daterange('2024-01-01', '2024-01-10') -|- daterange('2024-01-10', '2024-01-15');
-- Result: TRUE (end of first = start of second)
```

**Bounds notation**:
- `[)` - Includes start, excludes end (most common)
- `[]` - Includes both start and end
- `()` - Excludes both
- `(]` - Excludes start, includes end

### 2. GIST Index

**GiST** = Generalized Search Tree

Special index type for ranges and geometric data:
```sql
CREATE INDEX idx_allocations_daterange
ON allocations
USING gist(date_range);
-- Makes range overlap queries FAST (O(log n) instead of O(n))
```

### 3. EXCLUDE Constraint

Prevents overlapping data:
```sql
CREATE TABLE bookings (
    resource_id INTEGER,
    start_date DATE,
    end_date DATE,
    date_range DATERANGE GENERATED ALWAYS AS (daterange(start_date, end_date, '[)')) STORED
);

ALTER TABLE bookings
ADD CONSTRAINT no_overlap
EXCLUDE USING gist (
    resource_id WITH =,     -- Same resource
    date_range WITH &&      -- Overlapping ranges
);
-- Blocks INSERTs/UPDATEs that would create overlaps
```

---

## 🛠️ Implementation Guide

### Day 1: Understanding the Pattern (Learning Day)

#### Step 1: Read the Test File

**File**: `tests/unit/patterns/temporal/test_non_overlapping_daterange.py`

```bash
# Read the first few tests
head -100 tests/unit/patterns/temporal/test_non_overlapping_daterange.py
```

**Key tests to understand**:
1. `test_computed_daterange_column_added` - Pattern should add computed column
2. `test_gist_index_created` - Pattern should add GIST index
3. `test_exclusion_constraint_strict_mode` - Pattern should add EXCLUDE constraint

#### Step 2: Understand What the Pattern Should Generate

**Input YAML**:
```yaml
entity: Booking
schema: tenant  # Multi-tenant domain
fields:
  resource: ref(Resource)  # Conference room, vehicle, equipment, etc.
  user: ref(User)
  start_date: date
  end_date: date
  status: enum(pending, confirmed, cancelled)

patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [resource]         # Check overlaps per resource
      start_date_field: start_date
      end_date_field: end_date
      check_mode: strict               # Use EXCLUDE constraint
      inclusive_bounds: '[)'           # Include start, exclude end
```

**Expected Output SQL**:
```sql
CREATE TABLE tenant.tb_booking (
    pk_id SERIAL PRIMARY KEY,
    id UUID DEFAULT uuid_generate_v4(),
    identifier TEXT NOT NULL,
    tenant_id UUID NOT NULL,  -- Added automatically (multi-tenant schema)
    resource INTEGER REFERENCES tenant.tb_resource(pk_id),
    user INTEGER REFERENCES crm.tb_user(pk_id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'cancelled')),

    -- COMPUTED COLUMN (added by pattern)
    start_date_end_date_range DATERANGE
        GENERATED ALWAYS AS (daterange(start_date, end_date, '[)')) STORED,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- GIST INDEX (added by pattern)
CREATE INDEX idx_tb_booking_daterange
ON tenant.tb_booking
USING gist(start_date_end_date_range);

-- EXCLUSION CONSTRAINT (added by pattern if strict mode)
ALTER TABLE tenant.tb_booking
ADD CONSTRAINT excl_booking_no_overlap
EXCLUDE USING gist (
    resource WITH =,
    start_date_end_date_range WITH &&
);
```

#### Step 3: Experiment with PostgreSQL

Create a test database and try it:
```bash
# Start PostgreSQL (if using Docker)
docker run -d --name postgres-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16

# Connect
psql -h localhost -U postgres

# Create test table
CREATE TABLE test_bookings (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER,  -- Room, vehicle, equipment
    start_date DATE,
    end_date DATE,
    date_range DATERANGE GENERATED ALWAYS AS (daterange(start_date, end_date, '[)')) STORED
);

-- Add exclusion constraint
ALTER TABLE test_bookings
ADD CONSTRAINT no_overlap
EXCLUDE USING gist (resource_id WITH =, date_range WITH &&);

-- Test: Insert first booking (should work)
INSERT INTO test_bookings (resource_id, start_date, end_date)
VALUES (1, '2024-01-01', '2024-01-10');

-- Test: Insert overlapping booking (should FAIL)
INSERT INTO test_bookings (resource_id, start_date, end_date)
VALUES (1, '2024-01-05', '2024-01-15');
-- ERROR: conflicting key value violates exclusion constraint "no_overlap"

-- Test: Insert adjacent booking (should work)
INSERT INTO test_bookings (resource_id, start_date, end_date)
VALUES (1, '2024-01-10', '2024-01-20');
-- SUCCESS: No overlap (end of first = start of second, '[)' bounds)

-- Test: Different resource (should work)
INSERT INTO test_bookings (resource_id, start_date, end_date)
VALUES (2, '2024-01-05', '2024-01-15');
-- SUCCESS: Different scope (resource_id = 2)
```

**Key Learnings**:
- `&&` operator checks for overlap
- Exclusion constraint blocks conflicting data
- Adjacent ranges DON'T overlap with `[)` bounds

---

### Day 2: Implement Pattern Class (4 hours)

#### Step 1: Create Pattern Module

**Create file**: `src/patterns/temporal/non_overlapping_daterange.py`

```python
"""Temporal non-overlapping daterange pattern implementation."""

from dataclasses import dataclass
from typing import Optional
from src.core.ast_models import EntityDefinition, FieldDefinition


@dataclass
class DateRangeConfig:
    """Configuration for non-overlapping daterange pattern."""
    scope_fields: list[str]
    start_date_field: str
    end_date_field: str
    check_mode: str = "strict"  # 'strict' or 'warning'
    inclusive_bounds: str = "[)"  # '[)', '[]', '()', '(]'
    allow_adjacent: bool = True


class NonOverlappingDateRangePattern:
    """Prevent overlapping date ranges within a scope."""

    @classmethod
    def apply(cls, entity: EntityDefinition, params: dict) -> None:
        """
        Apply non-overlapping daterange pattern.

        Generates:
        1. Computed daterange column
        2. GIST index on daterange column
        3. EXCLUSION constraint (if strict mode)

        Args:
            entity: Entity to modify
            params: Pattern parameters
                - scope_fields: list[str] - Fields defining scope (e.g., ['resource_id'])
                - start_date_field: str - Start date field name
                - end_date_field: str - End date field name
                - check_mode: 'strict' | 'warning' (default: strict)
                - inclusive_bounds: '[)' | '[]' | '()' | '(]' (default: '[)')
        """
        config = cls._parse_config(params)

        # Validate fields exist
        cls._validate_fields(entity, config)

        # Add computed daterange column
        range_column_name = cls._add_daterange_column(entity, config)

        # Add GIST index
        cls._add_gist_index(entity, range_column_name)

        # Add exclusion constraint (if strict mode)
        if config.check_mode == "strict":
            cls._add_exclusion_constraint(entity, config, range_column_name)
        elif config.check_mode == "warning":
            cls._add_warning_trigger(entity, config, range_column_name)

    @classmethod
    def _parse_config(cls, params: dict) -> DateRangeConfig:
        """Parse pattern parameters."""
        scope_fields = params.get("scope_fields", [])
        if not scope_fields:
            raise ValueError("Non-overlapping daterange pattern requires 'scope_fields'")

        start_field = params.get("start_date_field")
        end_field = params.get("end_date_field")

        if not start_field or not end_field:
            raise ValueError(
                "Non-overlapping daterange pattern requires 'start_date_field' and 'end_date_field'"
            )

        return DateRangeConfig(
            scope_fields=scope_fields,
            start_date_field=start_field,
            end_date_field=end_field,
            check_mode=params.get("check_mode", "strict"),
            inclusive_bounds=params.get("inclusive_bounds", "[)"),
            allow_adjacent=params.get("allow_adjacent", True)
        )

    @classmethod
    def _validate_fields(cls, entity: EntityDefinition, config: DateRangeConfig) -> None:
        """Validate that required fields exist."""
        # Check scope fields
        for field in config.scope_fields:
            if field not in entity.fields:
                raise ValueError(f"Scope field '{field}' not found in entity '{entity.name}'")

        # Check date fields
        if config.start_date_field not in entity.fields:
            raise ValueError(f"Start date field '{config.start_date_field}' not found")
        if config.end_date_field not in entity.fields:
            raise ValueError(f"End date field '{config.end_date_field}' not found")

    @classmethod
    def _add_daterange_column(cls, entity: EntityDefinition, config: DateRangeConfig) -> str:
        """
        Add computed daterange column.

        Returns:
            str: Name of the created range column
        """
        range_col_name = f"{config.start_date_field}_{config.end_date_field}_range"

        # Create computed column
        range_field = FieldDefinition(
            name=range_col_name,
            type_name="DATERANGE",
            nullable=False,
            is_computed=True,
            computed_expression=f"daterange({config.start_date_field}, {config.end_date_field}, '{config.inclusive_bounds}')",
            comment=f"Computed date range for overlap detection ({config.start_date_field} to {config.end_date_field})"
        )

        entity.fields[range_col_name] = range_field

        return range_col_name

    @classmethod
    def _add_gist_index(cls, entity: EntityDefinition, range_column: str) -> None:
        """Add GIST index on range column for efficient overlap queries."""
        index_name = f"idx_{entity.table_name}_daterange"

        # Add index metadata to entity
        if not hasattr(entity, '_indexes'):
            entity._indexes = []

        entity._indexes.append({
            "name": index_name,
            "columns": [range_column],
            "index_type": "gist",
            "comment": "GIST index for efficient date range overlap detection"
        })

    @classmethod
    def _add_exclusion_constraint(cls, entity: EntityDefinition, config: DateRangeConfig,
                                  range_column: str) -> None:
        """Add exclusion constraint to prevent overlapping ranges."""
        constraint_name = f"excl_{entity.name.lower()}_no_overlap"

        # Build exclusion elements
        # Format: (scope_field1 WITH =, scope_field2 WITH =, range_col WITH &&)
        exclusion_elements = []

        for scope_field in config.scope_fields:
            exclusion_elements.append(f"{scope_field} WITH =")

        exclusion_elements.append(f"{range_column} WITH &&")

        constraint_ddl = f"""
ALTER TABLE {entity.schema}.{entity.table_name}
ADD CONSTRAINT {constraint_name}
EXCLUDE USING gist (
    {', '.join(exclusion_elements)}
);"""

        # Add to entity's custom DDL
        if not hasattr(entity, '_custom_ddl'):
            entity._custom_ddl = []

        entity._custom_ddl.append(constraint_ddl.strip())

    @classmethod
    def _add_warning_trigger(cls, entity: EntityDefinition, config: DateRangeConfig,
                            range_column: str) -> None:
        """Add trigger that warns about overlaps but doesn't block them."""
        function_name = f"warn_overlap_{entity.table_name}"
        trigger_name = f"trigger_warn_overlap_{entity.table_name}"

        # Build overlap check query
        scope_conditions = " AND ".join(
            f"NEW.{field} = {field}"
            for field in config.scope_fields
        )

        function_ddl = f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{function_name}()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_overlap_count INTEGER;
BEGIN
    -- Check for overlaps
    SELECT COUNT(*)
    INTO v_overlap_count
    FROM {entity.schema}.{entity.table_name}
    WHERE {scope_conditions}
      AND {range_column} && NEW.{range_column}
      AND pk_id != COALESCE(NEW.pk_id, -1);  -- Exclude current record on UPDATE

    IF v_overlap_count > 0 THEN
        RAISE WARNING 'Date range overlap detected for % (% overlapping records)',
            NEW.identifier, v_overlap_count;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER {trigger_name}
BEFORE INSERT OR UPDATE ON {entity.schema}.{entity.table_name}
FOR EACH ROW
EXECUTE FUNCTION {entity.schema}.{function_name}();
"""

        if not hasattr(entity, '_custom_ddl'):
            entity._custom_ddl = []

        entity._custom_ddl.append(function_ddl.strip())
```

**What this does**:
1. ✅ Adds computed `DATERANGE` column
2. ✅ Adds GIST index
3. ✅ Adds EXCLUDE constraint (strict mode)
4. ✅ Adds warning trigger (warning mode)
5. ✅ Validates all configuration

#### Step 2: Update Entity Model for Computed Columns

**File**: `src/core/ast_models.py`

**Update `FieldDefinition`**:
```python
@dataclass
class FieldDefinition:
    name: str
    type_name: str
    nullable: bool = True
    default: Optional[str] = None
    comment: Optional[str] = None

    # NEW: Computed column support
    is_computed: bool = False
    computed_expression: Optional[str] = None
```

#### Step 3: Register Pattern

**File**: `src/generators/schema/pattern_applier.py`

```python
from src.patterns.temporal.non_overlapping_daterange import NonOverlappingDateRangePattern

PATTERN_APPLIERS = {
    # ... existing patterns ...
    "temporal_non_overlapping_daterange": apply_non_overlapping_daterange_pattern,
}

def apply_non_overlapping_daterange_pattern(entity: EntityDefinition, params: dict) -> None:
    """Apply non-overlapping daterange pattern."""
    NonOverlappingDateRangePattern.apply(entity, params)
```

---

### Day 3: Update Table Generator (4 hours)

#### Step 1: Generate Computed Columns in DDL

**File**: `src/generators/schema/table_generator.py`

**Update the `generate()` method**:
```python
def generate(self, entity: EntityDefinition) -> str:
    """Generate CREATE TABLE DDL."""

    columns = []

    for field_name, field_def in entity.fields.items():
        # Check if computed column
        if field_def.is_computed:
            col_ddl = self._generate_computed_column_ddl(field_def)
        else:
            col_ddl = self._generate_regular_column_ddl(field_def)

        columns.append(col_ddl)

    # ... rest of generation ...

def _generate_computed_column_ddl(self, field_def: FieldDefinition) -> str:
    """Generate DDL for computed column."""
    null_clause = "" if field_def.nullable else "NOT NULL"

    ddl = f"    {field_def.name} {field_def.type_name} "
    ddl += f"GENERATED ALWAYS AS ({field_def.computed_expression}) STORED"

    if not field_def.nullable:
        ddl += " NOT NULL"

    return ddl
```

#### Step 2: Generate GIST Indexes

**File**: `src/generators/schema/index_generator.py`

```python
def generate_indexes(self, entity: EntityDefinition) -> list[str]:
    """Generate all indexes for entity."""
    indexes = []

    # ... existing index generation ...

    # Generate custom indexes (from patterns)
    if hasattr(entity, '_indexes'):
        for index_def in entity._indexes:
            index_ddl = self._generate_custom_index(entity, index_def)
            indexes.append(index_ddl)

    return indexes

def _generate_custom_index(self, entity: EntityDefinition, index_def: dict) -> str:
    """Generate custom index (e.g., GIST)."""
    index_name = index_def["name"]
    columns = ", ".join(index_def["columns"])
    index_type = index_def.get("index_type", "btree")

    ddl = f"CREATE INDEX {index_name} "
    ddl += f"ON {entity.schema}.{entity.table_name} "
    ddl += f"USING {index_type} ({columns});"

    return ddl
```

#### Step 3: Append Custom DDL

**File**: `src/generators/schema/schema_orchestrator.py`

```python
def generate_complete_schema(self, entity: EntityDefinition) -> str:
    """Generate complete schema including constraints."""

    ddl_parts = []

    # 1. Table DDL
    table_ddl = self.table_generator.generate(entity)
    ddl_parts.append(table_ddl)

    # 2. Indexes
    indexes = self.index_generator.generate_indexes(entity)
    ddl_parts.extend(indexes)

    # 3. Custom DDL (from patterns)
    if hasattr(entity, '_custom_ddl'):
        ddl_parts.extend(entity._custom_ddl)

    return "\n\n".join(ddl_parts)
```

---

### Day 4: Run Tests and Debug (4 hours)

#### Step 1: Run First Test

```bash
uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py::TestNonOverlappingDateRange::test_computed_daterange_column_added -v -s
```

**If it fails**, add debug output to test:
```python
def test_computed_daterange_column_added(self, allocation_yaml):
    parser = SpecQLParser()
    entity = parser.parse(allocation_yaml)

    # DEBUG: Check pattern was parsed
    print(f"\n=== DEBUG ===")
    print(f"Entity patterns: {entity.patterns}")
    print(f"Entity fields: {list(entity.fields.keys())}")

    generator = TableGenerator(entity)
    ddl = generator.generate()

    # DEBUG: Show generated DDL
    print(f"Generated DDL:\n{ddl}")
    print(f"=== END DEBUG ===\n")

    assert "start_date_end_date_range" in ddl
```

#### Step 2: Fix Issues One by One

**Common issues**:

1. **Pattern not applied**:
   ```python
   # Check if pattern applier is registered
   print(f"Registered patterns: {PATTERN_APPLIERS.keys()}")
   ```

2. **Field not added**:
   ```python
   # Check if computed field exists
   print(f"Computed fields: {[f for f, d in entity.fields.items() if d.is_computed]}")
   ```

3. **DDL not generated correctly**:
   ```python
   # Check computed column DDL
   for field_name, field_def in entity.fields.items():
       if field_def.is_computed:
           print(f"Computed field: {field_name}")
           print(f"  Expression: {field_def.computed_expression}")
   ```

#### Step 3: Run All Tests

```bash
uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py -v

# Expected results:
# ✅ test_computed_daterange_column_added PASSED
# ✅ test_gist_index_created PASSED
# ✅ test_exclusion_constraint_strict_mode PASSED
# ✅ test_nullable_end_date_supported PASSED
# ... (should have ~18 passing tests)
```

---

### Day 5: Advanced Features (4 hours)

#### Feature 1: Multiple Scope Fields

**Test**: `test_multiple_scope_fields`

```python
# Pattern should support multiple scope fields
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [resource, user]  # Both must match for overlap
```

**Generated constraint**:
```sql
EXCLUDE USING gist (
    resource WITH =,
    user WITH =,
    date_range WITH &&
);
```

#### Feature 2: Warning Mode

**Test**: `test_warning_mode_no_constraint`

```python
# Warning mode: log warnings but don't block
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      check_mode: warning  # Don't block, just warn
```

**Should generate**: Trigger that logs warnings instead of constraint.

#### Feature 3: Custom Bounds

**Test**: `test_inclusive_bounds_variations`

```python
# Test different bound types
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      inclusive_bounds: '[]'  # Include both start and end
```

---

### Day 6: Integration Testing (3 hours)

#### Create Real Test Database

```bash
# Setup test database
docker run -d --name specql-test -e POSTGRES_PASSWORD=test -p 5433:5432 postgres:16

# Generate and apply schema
uv run specql generate examples/booking.yaml --output /tmp/booking.sql
psql -h localhost -p 5433 -U postgres < /tmp/booking.sql
```

#### Test Overlap Prevention

```sql
-- Insert first booking (Conference Room A)
INSERT INTO tenant.tb_booking (resource, identifier, start_date, end_date)
VALUES (123, 'BOOK-001', '2024-01-01', '2024-01-10');

-- Try overlapping booking (should FAIL)
INSERT INTO tenant.tb_booking (resource, identifier, start_date, end_date)
VALUES (123, 'BOOK-002', '2024-01-05', '2024-01-15');
-- Expected: ERROR: conflicting key value violates exclusion constraint

-- Adjacent booking (should SUCCEED)
INSERT INTO tenant.tb_booking (resource, identifier, start_date, end_date)
VALUES (123, 'BOOK-003', '2024-01-10', '2024-01-20');
-- Expected: INSERT 1 (no overlap)
```

---

## ✅ Verification

```bash
# All temporal tests should pass
uv run pytest tests/unit/patterns/temporal/ -v

# Expected:
# ✅ 18 PASSED
# ❌ 0 FAILED
# ⏸️ 0 SKIPPED
```

---

## 🎓 Key Learnings

### 1. Computed Columns

```sql
-- Computed column is generated automatically
col_name TYPE GENERATED ALWAYS AS (expression) STORED
```

- `STORED` means computed once on INSERT/UPDATE
- Can be indexed
- Can be used in constraints

### 2. GIST Indexes

- Required for range operators (`&&`, `@>`, `<@`)
- Much faster than sequential scans
- Used by EXCLUDE constraints

### 3. Exclusion Constraints

- Generalized UNIQUE constraints
- Can use any operator (not just `=`)
- `&&` means "overlaps"
- Works with GIST indexes

---

**Next**: Week 4 - Recursive Dependency Validation & Template Inheritance 🚀
