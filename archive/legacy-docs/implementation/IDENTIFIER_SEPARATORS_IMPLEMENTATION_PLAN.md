# Implementation Plan: Identifier Separators (Dot Hierarchy + Composition)

**Status**: 🎯 Detailed Phased Plan (TDD Methodology)
**Timeline**: 5 days (Team A/B/C coordination)
**Dependencies**: Team A parser complete, `safe_slug()` function exists
**Related Docs**:
- `IDENTIFIER_SEPARATORS_STRATEGY.md`
- `IDENTIFIER_STRATEGIES_SPECQL.md`
- PrintOptim allocation pattern

---

## 📋 Overview

Implement **3-level separator hierarchy** based on PrintOptim production patterns:
1. **Tenant prefix**: `|` (pipe)
2. **Hierarchy levels**: `.` (dot) ← **Change from underscore**
3. **Cross-hierarchy composition**: `∘` (ring operator) ← **New feature**

**Total Effort**: 5 days across Teams A, B, C

---

## 🎯 Success Criteria

- [ ] Default hierarchy separator changed to `.` (dot)
- [ ] Tenant prefix remains `|` (backward compatible)
- [ ] New `∘` composition separator for cross-hierarchy
- [ ] `strip_tenant_prefix` works in composite identifiers
- [ ] `composite_hierarchical` strategy implemented
- [ ] All existing tests pass with new defaults
- [ ] 90%+ test coverage
- [ ] Documentation updated

---

## 📅 Phased Implementation (TDD)

### **Phase 1: Separator Constants & Utilities** (Day 1)

**Objective**: Define separator constants and utility functions

**TDD Cycle 1.1: Separator Constants**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/core/test_separator_constants.py` (NEW)

```python
"""Test separator constants and utilities."""

import pytest
from src.core.separators import Separators


class TestSeparatorConstants:
    """Test separator constant definitions."""

    def test_tenant_separator_is_pipe(self):
        """Tenant separator should be pipe."""
        assert Separators.TENANT == "|"

    def test_hierarchy_separator_is_dot(self):
        """Hierarchy separator should be dot (NEW default)."""
        assert Separators.HIERARCHY == "."

    def test_composition_separator_is_ring(self):
        """Composition separator should be ring operator."""
        assert Separators.COMPOSITION == "∘"

    def test_deduplication_suffix_is_hash(self):
        """Deduplication suffix should be hash."""
        assert Separators.DEDUPLICATION == "#"

    def test_ordering_separator_is_dash(self):
        """Ordering separator should be dash."""
        assert Separators.ORDERING == "-"

    def test_all_separators_unique(self):
        """All separators should be unique characters."""
        separators = [
            Separators.TENANT,
            Separators.HIERARCHY,
            Separators.COMPOSITION,
            Separators.DEDUPLICATION,
            Separators.ORDERING
        ]
        assert len(separators) == len(set(separators))

    def test_composition_fallback_is_tilde(self):
        """Fallback for composition separator should be tilde."""
        assert Separators.COMPOSITION_FALLBACK == "~"
```

**Expected**: ❌ FAIL - Module does not exist

#### 🟢 GREEN: Minimal Implementation

**File**: `src/core/separators.py` (NEW)

```python
"""Separator constants for identifier generation."""


class Separators:
    """Identifier separator constants.

    Three-level hierarchy:
    1. TENANT (|): Separates tenant from entity identifier
    2. HIERARCHY (.): Separates parent from child within one tree
    3. COMPOSITION (∘): Combines identifiers from different hierarchies

    Examples:
        Simple:       acme-corp|coffee-maker
        Hierarchical: acme-corp|warehouse.floor1.room101
        Composite:    acme-corp|2025-Q1∘machine.child∘location.child
    """

    # Level 1: Tenant scoping
    TENANT = "|"

    # Level 2: Hierarchy depth (within single tree)
    HIERARCHY = "."

    # Level 3: Cross-hierarchy composition
    COMPOSITION = "∘"  # U+2218 Ring Operator
    COMPOSITION_FALLBACK = "~"  # If ∘ causes encoding issues

    # Other separators
    DEDUPLICATION = "#"
    ORDERING = "-"

    # Legacy support (old default was underscore)
    HIERARCHY_LEGACY = "_"


# Default separator configuration
DEFAULT_SEPARATORS = {
    "tenant": Separators.TENANT,
    "hierarchy": Separators.HIERARCHY,
    "composition": Separators.COMPOSITION,
    "deduplication": Separators.DEDUPLICATION,
    "ordering": Separators.ORDERING
}
```

**Expected**: ✅ PASS

#### 🔧 REFACTOR: Add Utility Functions

**File**: `src/core/separators.py` (UPDATE)

```python
def strip_tenant_prefix(identifier: str, tenant_identifier: str) -> str:
    """Strip tenant prefix from identifier.

    Args:
        identifier: Full identifier (e.g., "acme-corp|warehouse.floor1")
        tenant_identifier: Tenant identifier (e.g., "acme-corp")

    Returns:
        Identifier without tenant prefix (e.g., "warehouse.floor1")

    Examples:
        >>> strip_tenant_prefix("acme-corp|warehouse.floor1", "acme-corp")
        'warehouse.floor1'
        >>> strip_tenant_prefix("no-prefix", "acme-corp")
        'no-prefix'
    """
    prefix = f"{tenant_identifier}{Separators.TENANT}"
    if identifier.startswith(prefix):
        return identifier[len(prefix):]
    return identifier


def join_with_composition(components: list[str]) -> str:
    """Join components with composition separator.

    Args:
        components: List of identifier components

    Returns:
        Joined identifier

    Examples:
        >>> join_with_composition(["2025-Q1", "machine.child", "location.parent"])
        '2025-Q1∘machine.child∘location.parent'
    """
    return Separators.COMPOSITION.join(components)


def split_composition(identifier: str) -> list[str]:
    """Split identifier by composition separator.

    Args:
        identifier: Composite identifier

    Returns:
        List of components

    Examples:
        >>> split_composition("2025-Q1∘machine∘location")
        ['2025-Q1', 'machine', 'location']
    """
    return identifier.split(Separators.COMPOSITION)
```

#### ✅ QA: Phase 1 Complete

```bash
uv run pytest tests/unit/core/test_separator_constants.py -v
uv run pytest tests/unit/core/test_separators.py -v  # Utility tests
uv run pytest tests/unit/core/ -v
uv run pytest --tb=short
make lint && make typecheck
```

**Deliverables**:
- ✅ `Separators` class with all constants
- ✅ Utility functions for stripping/joining
- ✅ Comprehensive tests

---

### **Phase 2: Team A - Parse Separator Config** (Day 1)

**Objective**: Parse separator configuration from SpecQL YAML

**TDD Cycle 2.1: Parse Separator Overrides**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/core/test_specql_parser_separators.py` (NEW)

```python
"""Test SpecQL parser separator configuration."""

import pytest
from src.core.specql_parser import SpecQLParser
from src.core.separators import Separators


class TestParseIdentifierSeparators:
    """Test parsing of separator configuration."""

    def test_default_separators_when_not_specified(self):
        """Should use default separators if not specified."""
        yaml_content = """
entity: Location
hierarchical: true
fields:
  name: text
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        # Should use defaults (no explicit config)
        assert entity.identifier is None or entity.identifier.separator == Separators.HIERARCHY

    def test_parse_explicit_hierarchy_separator(self):
        """Should parse explicit hierarchy separator override."""
        yaml_content = """
entity: Location
hierarchical: true
identifier:
  separator: "_"  # Override to underscore
fields:
  name: text
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.identifier is not None
        assert entity.identifier.separator == "_"

    def test_parse_composition_separator(self):
        """Should parse composition separator for composite strategy."""
        yaml_content = """
entity: Allocation
identifier:
  strategy: composite_hierarchical
  composition_separator: "∘"
  components:
    - field: machine.identifier
      strip_tenant_prefix: true
    - field: location.identifier
      strip_tenant_prefix: true
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.identifier.strategy == "composite_hierarchical"
        assert entity.identifier.composition_separator == "∘"
        assert len(entity.identifier.components) == 2
        assert entity.identifier.components[0].strip_tenant_prefix is True

    def test_parse_strip_tenant_prefix_option(self):
        """Should parse strip_tenant_prefix for components."""
        yaml_content = """
entity: Allocation
identifier:
  strategy: composite_hierarchical
  components:
    - field: daterange
      strip_tenant_prefix: false
    - field: machine.identifier
      strip_tenant_prefix: true
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.identifier.components[0].strip_tenant_prefix is False
        assert entity.identifier.components[1].strip_tenant_prefix is True

    def test_default_composition_separator(self):
        """Should default to ring operator for composition separator."""
        yaml_content = """
entity: Allocation
identifier:
  strategy: composite_hierarchical
  components:
    - field: machine.identifier
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        # Default composition separator
        assert entity.identifier.composition_separator == Separators.COMPOSITION or \
               entity.identifier.composition_separator is None  # Will use default
```

**Expected**: ❌ FAIL - Parser doesn't support these fields

#### 🟢 GREEN: Minimal Implementation

**File**: `src/core/ast_models.py` (UPDATE)

```python
@dataclass
class IdentifierComponent:
    """Component of identifier calculation."""
    field: str
    transform: str = "slugify"
    format: Optional[str] = None
    separator: str = ""
    replace: Optional[Dict[str, str]] = None
    strip_tenant_prefix: bool = False  # NEW: Strip tenant prefix from referenced identifiers


@dataclass
class IdentifierConfig:
    """Identifier calculation strategy."""
    strategy: str

    # Components
    prefix: List[IdentifierComponent] = field(default_factory=list)
    components: List[IdentifierComponent] = field(default_factory=list)

    # Separators (NEW)
    separator: str = Separators.HIERARCHY  # Default changed from "_" to "."
    composition_separator: str = Separators.COMPOSITION  # For composite_hierarchical

    # ... existing fields ...
```

**File**: `src/core/specql_parser.py` (UPDATE)

```python
from src.core.separators import Separators

class SpecQLParser:
    def _parse_identifier_config(self, yaml_data: dict) -> Optional[IdentifierConfig]:
        """Parse identifier configuration from YAML."""

        if "identifier" not in yaml_data:
            return None

        id_config = yaml_data["identifier"]

        # Parse separators
        hierarchy_separator = id_config.get("separator", Separators.HIERARCHY)
        composition_separator = id_config.get("composition_separator", Separators.COMPOSITION)

        # Parse components
        components = self._parse_identifier_components(id_config.get("components", []))

        return IdentifierConfig(
            strategy=id_config.get("strategy", "simple"),
            separator=hierarchy_separator,
            composition_separator=composition_separator,
            components=components,
            # ... other fields ...
        )

    def _parse_identifier_components(
        self,
        components: List[Union[str, dict]]
    ) -> List[IdentifierComponent]:
        """Parse identifier components (with strip_tenant_prefix support)."""

        result = []

        for comp in components:
            if isinstance(comp, str):
                # Shorthand
                result.append(IdentifierComponent(field=comp, transform="slugify"))
            else:
                # Detailed config
                result.append(IdentifierComponent(
                    field=comp["field"],
                    transform=comp.get("transform", "slugify"),
                    format=comp.get("format"),
                    separator=comp.get("separator", ""),
                    replace=comp.get("replace"),
                    strip_tenant_prefix=comp.get("strip_tenant_prefix", False)  # NEW
                ))

        return result
```

**Expected**: ✅ PASS

#### ✅ QA: Phase 2 Complete

```bash
uv run pytest tests/unit/core/test_specql_parser_separators.py -v
uv run pytest tests/unit/core/test_specql_parser.py -v
uv run pytest --tb=short
```

**Deliverables**:
- ✅ Parser supports `separator`, `composition_separator`
- ✅ Parser supports `strip_tenant_prefix` on components
- ✅ Default separator is `.` (dot)

---

### **Phase 3: Team C - Hierarchical with Dot Separator** (Day 2)

**Objective**: Update hierarchical identifier generation to use dot separator

**TDD Cycle 3.1: Simple Hierarchical with Dot**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/actions/test_identifier_hierarchical_dot.py` (NEW)

```python
"""Test hierarchical identifier generation with dot separator."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestHierarchicalDotSeparator:
    """Test hierarchical identifiers use dot by default."""

    @pytest.fixture
    def location_hierarchy(self, db):
        """Create location hierarchy for testing."""
        execute_sql(db, """
            CREATE SCHEMA IF NOT EXISTS tenant;

            CREATE TABLE tenant.tb_location (
                pk_location INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                fk_parent_location INTEGER REFERENCES tenant.tb_location(pk_location),
                name TEXT NOT NULL,
                identifier TEXT,
                base_identifier TEXT,
                sequence_number INTEGER DEFAULT 1,
                identifier_recalculated_at TIMESTAMPTZ,
                identifier_recalculated_by UUID
            );

            -- Create tenant
            CREATE TABLE management.tb_tenant (
                pk_tenant INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                identifier TEXT NOT NULL
            );

            INSERT INTO management.tb_tenant (pk_tenant, id, identifier)
            VALUES (1, gen_random_uuid(), 'acme-corp');

            -- Create hierarchy
            INSERT INTO tenant.tb_location (pk_location, tenant_id, fk_parent_location, name)
            VALUES
                (1, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), NULL, 'Warehouse A'),
                (2, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), 1, 'Floor 1'),
                (3, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), 2, 'Room 101');
        """)
        yield
        execute_sql(db, "DROP SCHEMA tenant CASCADE; DROP SCHEMA management CASCADE;")

    def test_hierarchical_uses_dot_separator(self, db, location_hierarchy):
        """Hierarchical identifiers should use dot separator by default."""
        # Generate recalculate function (Team C generates this)
        # Simulated generated function
        execute_sql(db, """
            CREATE OR REPLACE FUNCTION tenant.recalculate_location_identifier()
            RETURNS INTEGER AS $$
            DECLARE
                v_count INTEGER := 0;
            BEGIN
                WITH RECURSIVE hierarchy AS (
                    -- Root nodes
                    SELECT
                        l.pk_location,
                        (SELECT identifier FROM management.tb_tenant WHERE id = l.tenant_id)
                            || '|' || public.safe_slug(l.name) AS base_identifier
                    FROM tenant.tb_location l
                    WHERE l.fk_parent_location IS NULL

                    UNION ALL

                    -- Child nodes (use DOT separator)
                    SELECT
                        child.pk_location,
                        parent.base_identifier || '.' || public.safe_slug(child.name)
                    FROM tenant.tb_location child
                    JOIN hierarchy parent ON child.fk_parent_location = parent.pk_location
                )
                UPDATE tenant.tb_location l
                SET
                    identifier = h.base_identifier,
                    base_identifier = h.base_identifier
                FROM hierarchy h
                WHERE l.pk_location = h.pk_location;

                GET DIAGNOSTICS v_count = ROW_COUNT;
                RETURN v_count;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Execute recalculation
        result = execute_query(db, "SELECT tenant.recalculate_location_identifier()")
        assert result >= 3  # Updated 3 nodes

        # Verify identifiers use dot separator
        locations = execute_query(db, """
            SELECT pk_location, identifier
            FROM tenant.tb_location
            ORDER BY pk_location
        """, fetch_all=True)

        assert locations[0]['identifier'] == 'acme-corp|warehouse-a'  # Root
        assert locations[1]['identifier'] == 'acme-corp|warehouse-a.floor-1'  # Child (DOT!)
        assert locations[2]['identifier'] == 'acme-corp|warehouse-a.floor-1.room-101'  # Grandchild (DOT!)

    def test_explicit_underscore_override(self, db, location_hierarchy):
        """Should support explicit underscore override for backward compatibility."""
        # Generate function with underscore separator (explicit override)
        execute_sql(db, """
            CREATE OR REPLACE FUNCTION tenant.recalculate_location_identifier_underscore()
            RETURNS INTEGER AS $$
            BEGIN
                WITH RECURSIVE hierarchy AS (
                    SELECT
                        l.pk_location,
                        (SELECT identifier FROM management.tb_tenant WHERE id = l.tenant_id)
                            || '|' || public.safe_slug(l.name) AS base_identifier
                    FROM tenant.tb_location l
                    WHERE l.fk_parent_location IS NULL

                    UNION ALL

                    SELECT
                        child.pk_location,
                        parent.base_identifier || '_' || public.safe_slug(child.name)  -- Underscore override
                    FROM tenant.tb_location child
                    JOIN hierarchy parent ON child.fk_parent_location = parent.pk_location
                )
                UPDATE tenant.tb_location l
                SET identifier = h.base_identifier
                FROM hierarchy h
                WHERE l.pk_location = h.pk_location;

                RETURN (SELECT COUNT(*) FROM tenant.tb_location);
            END;
            $$ LANGUAGE plpgsql;
        """)

        execute_query(db, "SELECT tenant.recalculate_location_identifier_underscore()")

        locations = execute_query(db, """
            SELECT identifier FROM tenant.tb_location ORDER BY pk_location
        """, fetch_all=True)

        assert locations[1]['identifier'] == 'acme-corp|warehouse-a_floor-1'  # Underscore!
```

**Expected**: ❌ FAIL - Generated function doesn't exist yet

#### 🟢 GREEN: Minimal Implementation

**File**: `src/generators/actions/identifier_recalc_generator.py` (UPDATE)

```python
from src.core.separators import Separators

class IdentifierRecalcGenerator:
    def _generate_hierarchical_strategy(self, entity: EntityDefinition) -> str:
        """Generate hierarchical identifier recalculation with DOT separator."""

        entity_lower = entity.name.lower()
        schema = entity.schema
        parent_field = f"fk_parent_{entity_lower}"

        # Get separator (default is now DOT)
        separator = Separators.HIERARCHY
        if entity.identifier and entity.identifier.separator:
            separator = entity.identifier.separator

        # Check for tenant prefix
        has_tenant_prefix = self._should_apply_tenant_prefix(entity)
        tenant_expr = ""
        if has_tenant_prefix:
            tenant_lookup = self._get_tenant_identifier_expression(entity)
            tenant_expr = f"{tenant_lookup} || '{Separators.TENANT}' || "

        # Build component expression
        component_expr = self._build_component_expression(
            entity.identifier.components if entity.identifier else [
                IdentifierComponent(field="name", transform="slugify")
            ]
        )

        return f"""
-- Recalculate hierarchical identifiers (separator: '{separator}')
CREATE OR REPLACE FUNCTION {schema}.recalculate_{entity_lower}_identifier(
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
) RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER := 0;
BEGIN
    -- Build hierarchical identifiers using recursive CTE
    WITH RECURSIVE hierarchy AS (
        -- Root nodes
        SELECT
            t.pk_{entity_lower},
            {tenant_expr}{component_expr} AS base_identifier
        FROM {schema}.tb_{entity_lower} t
        WHERE t.{parent_field} IS NULL

        UNION ALL

        -- Child nodes (use configured separator: '{separator}')
        SELECT
            child.pk_{entity_lower},
            parent.base_identifier || '{separator}' || {component_expr}
        FROM {schema}.tb_{entity_lower} child
        JOIN hierarchy parent ON child.{parent_field} = parent.pk_{entity_lower}
    )
    UPDATE {schema}.tb_{entity_lower} t
    SET
        identifier = h.base_identifier,
        base_identifier = h.base_identifier,
        identifier_recalculated_at = now(),
        identifier_recalculated_by = ctx.updated_by
    FROM hierarchy h
    WHERE t.pk_{entity_lower} = h.pk_{entity_lower}
      AND (
          t.identifier IS DISTINCT FROM h.base_identifier OR
          t.base_identifier IS DISTINCT FROM h.base_identifier
      );

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION {schema}.recalculate_{entity_lower}_identifier IS
'Recalculate hierarchical identifiers for {entity.name}.
Separator: {separator} (default: dot for hierarchy)
Pattern: {{tenant}}|{{parent}}{separator}{{child}}';
""".strip()
```

**Expected**: ✅ PASS

#### ✅ QA: Phase 3 Complete

```bash
uv run pytest tests/unit/actions/test_identifier_hierarchical_dot.py -v
uv run pytest tests/unit/actions/ -v
uv run pytest --tb=short
```

**Deliverables**:
- ✅ Hierarchical generation uses dot by default
- ✅ Explicit override to underscore works
- ✅ Tenant prefix still uses pipe

---

### **Phase 4: Team C - Composite Hierarchical Strategy** (Days 3-4)

**Objective**: Implement cross-hierarchy composition with ring operator

**TDD Cycle 4.1: Strip Tenant Prefix Logic**

#### 🔴 RED: Write Failing Test

**File**: `tests/unit/actions/test_strip_tenant_prefix.py` (NEW)

```python
"""Test tenant prefix stripping for composite identifiers."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestStripTenantPrefix:
    """Test stripping tenant prefix from referenced identifiers."""

    @pytest.fixture
    def composite_setup(self, db):
        """Create entities for composite testing."""
        execute_sql(db, """
            CREATE SCHEMA tenant;
            CREATE SCHEMA management;

            CREATE TABLE management.tb_tenant (
                pk_tenant INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                identifier TEXT NOT NULL
            );

            CREATE TABLE tenant.tb_machine (
                pk_machine INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                identifier TEXT NOT NULL
            );

            CREATE TABLE tenant.tb_location (
                pk_location INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                identifier TEXT NOT NULL
            );

            INSERT INTO management.tb_tenant (pk_tenant, id, identifier)
            VALUES (1, gen_random_uuid(), 'acme-corp');

            INSERT INTO tenant.tb_machine (pk_machine, tenant_id, identifier)
            VALUES (1, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), 'acme-corp|hp.laser.s123');

            INSERT INTO tenant.tb_location (pk_location, tenant_id, identifier)
            VALUES (1, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), 'acme-corp|warehouse.floor1');
        """)
        yield
        execute_sql(db, "DROP SCHEMA tenant CASCADE; DROP SCHEMA management CASCADE;")

    def test_strip_tenant_prefix_from_machine(self, db, composite_setup):
        """Should strip tenant prefix from machine identifier."""
        result = execute_query(db, """
            SELECT
                m.identifier AS full_identifier,
                REGEXP_REPLACE(
                    m.identifier,
                    '^' || (SELECT identifier FROM management.tb_tenant WHERE id = m.tenant_id) || '\\|',
                    ''
                ) AS stripped_identifier
            FROM tenant.tb_machine m
            WHERE pk_machine = 1;
        """)

        assert result['full_identifier'] == 'acme-corp|hp.laser.s123'
        assert result['stripped_identifier'] == 'hp.laser.s123'  # Prefix stripped!

    def test_composite_identifier_without_duplicate_tenant(self, db, composite_setup):
        """Composite identifier should not have duplicate tenant prefix."""
        # Simulate allocation identifier construction
        result = execute_query(db, """
            SELECT
                (SELECT identifier FROM management.tb_tenant WHERE pk_tenant = 1)
                    || '|2025-Q1∘'
                    || REGEXP_REPLACE(m.identifier, '^' || (SELECT identifier FROM management.tb_tenant WHERE id = m.tenant_id) || '\\|', '')
                    || '∘'
                    || REGEXP_REPLACE(l.identifier, '^' || (SELECT identifier FROM management.tb_tenant WHERE id = l.tenant_id) || '\\|', '')
                AS composite_identifier
            FROM tenant.tb_machine m, tenant.tb_location l
            WHERE m.pk_machine = 1 AND l.pk_location = 1;
        """)

        composite = result['composite_identifier']

        # Should be: acme-corp|2025-Q1∘hp.laser.s123∘warehouse.floor1
        assert composite == 'acme-corp|2025-Q1∘hp.laser.s123∘warehouse.floor1'

        # Should NOT be: acme-corp|2025-Q1∘acme-corp|hp.laser.s123∘acme-corp|warehouse.floor1
        assert 'acme-corp|acme-corp' not in composite
        assert composite.count('acme-corp') == 1  # Only once at start!
```

**Expected**: ❌ FAIL - SQL pattern doesn't exist in generator yet

#### 🟢 GREEN: Minimal Implementation

**File**: `src/generators/actions/identifier_recalc_generator.py` (UPDATE)

```python
def _generate_composite_hierarchical_strategy(
    self,
    entity: EntityDefinition
) -> str:
    """Generate composite hierarchical identifier (allocation pattern)."""

    entity_lower = entity.name.lower()
    schema = entity.schema

    # Get separators
    composition_sep = entity.identifier.composition_separator or Separators.COMPOSITION

    # Check for tenant prefix
    has_tenant_prefix = self._should_apply_tenant_prefix(entity)
    tenant_field = self._detect_tenant_field(entity) if has_tenant_prefix else None

    # Build component expressions
    component_exprs = []
    for comp in entity.identifier.components:
        expr = f"t.{comp.field}"

        # Apply transforms
        if comp.transform == "slugify":
            expr = f"public.safe_slug({expr})"
        elif comp.transform == "uppercase":
            expr = f"UPPER({expr})"
        elif comp.transform == "lowercase":
            expr = f"LOWER({expr})"

        # Strip tenant prefix if requested
        if comp.strip_tenant_prefix and has_tenant_prefix and tenant_field:
            tenant_lookup = self._get_tenant_identifier_expression(entity)
            expr = f"""REGEXP_REPLACE(
                {expr},
                '^' || {tenant_lookup} || '\\{Separators.TENANT}',
                ''
            )"""

        # Apply character replacements
        if comp.replace:
            for old_char, new_char in comp.replace.items():
                expr = f"REPLACE({expr}, '{old_char}', '{new_char}')"

        component_exprs.append(expr)

    # Join components with composition separator
    components_joined = f" || '{composition_sep}' || ".join(component_exprs)

    # Add tenant prefix if applicable
    if has_tenant_prefix:
        tenant_lookup = self._get_tenant_identifier_expression(entity)
        base_identifier_expr = f"{tenant_lookup} || '{Separators.TENANT}' || {components_joined}"
    else:
        base_identifier_expr = components_joined

    return f"""
-- Recalculate composite hierarchical identifiers (allocation pattern)
-- Composition separator: '{composition_sep}'
CREATE OR REPLACE FUNCTION {schema}.recalculate_{entity_lower}_identifier(
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
) RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER := 0;
BEGIN
    -- Create temp table
    DROP TABLE IF EXISTS tmp_{entity_lower}_identifiers;
    CREATE TEMP TABLE tmp_{entity_lower}_identifiers (
        pk_{entity_lower} INTEGER,
        base_identifier TEXT,
        unique_identifier TEXT,
        sequence_number INTEGER
    ) ON COMMIT DROP;

    -- Calculate composite identifiers
    INSERT INTO tmp_{entity_lower}_identifiers (pk_{entity_lower}, base_identifier)
    SELECT
        t.pk_{entity_lower},
        {base_identifier_expr} AS base_identifier
    FROM {schema}.tb_{entity_lower} t
    WHERE
        CASE
            WHEN ctx.pk IS NOT NULL THEN t.id = ctx.pk
            WHEN ctx.pk_tenant IS NOT NULL THEN t.tenant_id = ctx.pk_tenant
            ELSE true
        END;

    -- Deduplicate (same logic as simple strategy)
    -- ... deduplication loop ...

    -- Apply updates
    UPDATE {schema}.tb_{entity_lower} t
    SET
        identifier = tmp.unique_identifier,
        base_identifier = tmp.base_identifier,
        sequence_number = tmp.sequence_number,
        identifier_recalculated_at = now(),
        identifier_recalculated_by = ctx.updated_by
    FROM tmp_{entity_lower}_identifiers tmp
    WHERE t.pk_{entity_lower} = tmp.pk_{entity_lower}
      AND (
          t.identifier IS DISTINCT FROM tmp.unique_identifier OR
          t.sequence_number IS DISTINCT FROM tmp.sequence_number
      );

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION {schema}.recalculate_{entity_lower}_identifier IS
'Recalculate composite hierarchical identifiers for {entity.name}.
Strategy: composite_hierarchical
Pattern: {{tenant}}|{{comp1}}{composition_sep}{{comp2}}{composition_sep}...
Components have tenant prefix stripped to avoid duplication.';
""".strip()
```

**Expected**: ✅ PASS

#### 🔧 REFACTOR: Extract Deduplication Logic

Create shared deduplication template to avoid duplication:

**File**: `src/generators/actions/templates/deduplication_loop.sql.jinja2` (NEW)

```sql
-- Deduplicate identifiers (WITHIN TENANT if applicable)
FOR v_record IN
    SELECT pk_{{ entity_lower }}, base_identifier
    FROM tmp_{{ entity_lower }}_identifiers
LOOP
    v_new_identifier := v_record.base_identifier;
    v_suffix := 1;

    -- Find unique identifier
    LOOP
        EXIT WHEN NOT EXISTS (
            SELECT 1 FROM {{ schema }}.tb_{{ entity_lower }}
            WHERE identifier = v_new_identifier
              AND pk_{{ entity_lower }} != v_record.pk_{{ entity_lower }}
              AND deleted_at IS NULL
        ) AND NOT EXISTS (
            SELECT 1 FROM tmp_{{ entity_lower }}_identifiers
            WHERE unique_identifier = v_new_identifier
              AND pk_{{ entity_lower }} != v_record.pk_{{ entity_lower }}
        );

        v_suffix := v_suffix + 1;
        v_new_identifier := v_record.base_identifier || '{{ dedup_separator }}' || v_suffix;
    END LOOP;

    -- Update temp table
    UPDATE tmp_{{ entity_lower }}_identifiers
    SET
        unique_identifier = v_new_identifier,
        sequence_number = v_suffix
    WHERE pk_{{ entity_lower }} = v_record.pk_{{ entity_lower }};
END LOOP;
```

**TDD Cycle 4.2: Integration Test**

#### 🔴 RED: Integration Test

**File**: `tests/integration/test_composite_hierarchical_e2e.py` (NEW)

```python
"""End-to-end test of composite hierarchical identifiers."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestCompositeHierarchicalE2E:
    """Test complete allocation-style composite identifiers."""

    @pytest.fixture
    def allocation_schema(self, db):
        """Create allocation schema with dependencies."""
        # Create all dependent entities
        execute_sql(db, """
            CREATE SCHEMA tenant;
            CREATE SCHEMA management;

            -- Tenant
            CREATE TABLE management.tb_tenant (
                pk_tenant INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                identifier TEXT NOT NULL
            );

            -- Machine (hierarchical)
            CREATE TABLE tenant.tb_machine (
                pk_machine INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                fk_parent_machine INTEGER REFERENCES tenant.tb_machine(pk_machine),
                name TEXT NOT NULL,
                identifier TEXT
            );

            -- Location (hierarchical)
            CREATE TABLE tenant.tb_location (
                pk_location INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                fk_parent_location INTEGER REFERENCES tenant.tb_location(pk_location),
                name TEXT NOT NULL,
                identifier TEXT
            );

            -- Allocation (composite)
            CREATE TABLE tenant.tb_allocation (
                pk_allocation INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                allocation_daterange TEXT NOT NULL,
                fk_machine INTEGER REFERENCES tenant.tb_machine(pk_machine),
                fk_location INTEGER REFERENCES tenant.tb_location(pk_location),
                identifier TEXT,
                base_identifier TEXT,
                sequence_number INTEGER DEFAULT 1
            );

            -- Sample data
            INSERT INTO management.tb_tenant VALUES (1, gen_random_uuid(), 'acme-corp');

            -- Machine hierarchy
            INSERT INTO tenant.tb_machine VALUES
                (1, gen_random_uuid(), (SELECT id FROM management.tb_tenant), NULL, 'HP', 'acme-corp|hp'),
                (2, gen_random_uuid(), (SELECT id FROM management.tb_tenant), 1, 'LaserJet', 'acme-corp|hp.laserjet'),
                (3, gen_random_uuid(), (SELECT id FROM management.tb_tenant), 2, 'S123', 'acme-corp|hp.laserjet.s123');

            -- Location hierarchy
            INSERT INTO tenant.tb_location VALUES
                (1, gen_random_uuid(), (SELECT id FROM management.tb_tenant), NULL, 'Warehouse', 'acme-corp|warehouse'),
                (2, gen_random_uuid(), (SELECT id FROM management.tb_tenant), 1, 'Floor 1', 'acme-corp|warehouse.floor1');

            -- Allocation
            INSERT INTO tenant.tb_allocation (pk_allocation, tenant_id, allocation_daterange, fk_machine, fk_location)
            VALUES (1, (SELECT id FROM management.tb_tenant), '2025-Q1', 3, 2);
        """)
        yield
        execute_sql(db, "DROP SCHEMA tenant CASCADE; DROP SCHEMA management CASCADE;")

    def test_allocation_composite_identifier(self, db, allocation_schema):
        """Should generate allocation identifier with composition separator."""
        # Generate recalculate function (from SpecQL)
        # ... generator creates this function ...

        # Execute recalculation
        execute_query(db, "SELECT tenant.recalculate_allocation_identifier()")

        # Verify composite identifier
        result = execute_query(db, """
            SELECT identifier, base_identifier
            FROM tenant.tb_allocation
            WHERE pk_allocation = 1;
        """)

        # Expected: acme-corp|2025-Q1∘hp.laserjet.s123∘warehouse.floor1
        identifier = result['identifier']

        assert identifier.startswith('acme-corp|')  # Tenant prefix
        assert '∘' in identifier  # Composition separator
        assert identifier.count('acme-corp') == 1  # Only one tenant prefix!
        assert 'hp.laserjet.s123' in identifier  # Machine hierarchy with dots
        assert 'warehouse.floor1' in identifier  # Location hierarchy with dots
        assert identifier == 'acme-corp|2025-Q1∘hp.laserjet.s123∘warehouse.floor1'
```

**Expected**: ❌ FAIL initially, then ✅ PASS

#### ✅ QA: Phase 4 Complete

```bash
uv run pytest tests/unit/actions/test_strip_tenant_prefix.py -v
uv run pytest tests/integration/test_composite_hierarchical_e2e.py -v
uv run pytest tests/unit/actions/ -v
uv run pytest --tb=short
```

**Deliverables**:
- ✅ `composite_hierarchical` strategy implemented
- ✅ Tenant prefix stripping works
- ✅ Ring operator `∘` used for composition
- ✅ Each component hierarchy uses dot separator

---

### **Phase 5: Documentation & Migration** (Day 5)

**Objective**: Update docs, create migration guide, verify backward compatibility

**TDD Cycle 5.1: Backward Compatibility Test**

#### 🔴 RED: Backward Compatibility Test

**File**: `tests/integration/test_backward_compatibility.py` (NEW)

```python
"""Test backward compatibility with underscore separator."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestBackwardCompatibility:
    """Ensure explicit underscore override still works."""

    def test_explicit_underscore_override_works(self, db):
        """Entities with explicit underscore config should still work."""
        # SpecQL with explicit underscore
        yaml_content = """
entity: LegacyLocation
schema: tenant
hierarchical: true
identifier:
  separator: "_"  # Explicit override to old default
fields:
  name: text
"""
        # Generate and test
        # ... parser + generator + execute ...

        # Should use underscore, not dot
        # identifier should be: acme-corp|parent_child_grandchild
        pass

    def test_new_entities_use_dot_by_default(self, db):
        """New entities without explicit config should use dot."""
        # SpecQL without separator specified
        yaml_content = """
entity: ModernLocation
schema: tenant
hierarchical: true
fields:
  name: text
"""
        # Generate and test
        # Should use dot: acme-corp|parent.child.grandchild
        pass
```

**Expected**: ❌ FAIL, then ✅ PASS after ensuring override works

#### 🟢 GREEN: Documentation

**Deliverables**:

1. **Update `IDENTIFIER_STRATEGIES_SPECQL.md`**
   - Change all examples to use dot separator
   - Show composition separator examples
   - Document backward compatibility

2. **Create Migration Guide**: `docs/migration/SEPARATOR_MIGRATION_GUIDE.md`

```markdown
# Migration Guide: Underscore to Dot Hierarchy Separator

## Summary

Default hierarchy separator changed from `_` to `.` in version X.Y.Z.

## Impact

**Low** - Explicit override available, existing data unaffected.

## For Existing Entities

### Option 1: Keep Underscore (Explicit Override)

```yaml
identifier:
  separator: "_"  # Maintain old behavior
```

### Option 2: Migrate to Dot (Recommended)

1. Update SpecQL YAML (remove explicit `separator: "_"`)
2. Regenerate functions
3. Run identifier recalculation
4. Update any hardcoded identifier strings

## For New Entities

No action needed - dot separator is now default.

## Examples

**Before**:
```
acme-corp|warehouse_floor1_room101
```

**After**:
```
acme-corp|warehouse.floor1.room101
```
```

3. **Update Examples in Docs**

All documentation examples should show new defaults:
- Dot for hierarchy
- Ring for composition
- Pipe for tenant

#### ✅ QA: Phase 5 Complete

```bash
uv run pytest tests/integration/test_backward_compatibility.py -v
uv run pytest tests/integration/ -v
uv run pytest --tb=short
make lint && make typecheck
make test
```

**Deliverables**:
- ✅ Backward compatibility tested
- ✅ Migration guide written
- ✅ All documentation updated
- ✅ Examples show new defaults

---

## 📊 Summary

### Timeline

| Phase | Days | Focus | Team | Deliverables |
|-------|------|-------|------|-------------|
| **1** | 1 | Separator constants | All | Constants, utilities, tests |
| **2** | 1 | Parse config | A | Parser updates, AST changes |
| **3** | 1 | Hierarchical dot | C | Updated generator, tests |
| **4** | 2 | Composite strategy | C | New strategy, strip logic |
| **5** | 1 | Docs & migration | All | Guides, compat tests |

**Total**: 5 days (1 week)

### Files Created/Modified

**New Files** (8):
- `src/core/separators.py`
- `tests/unit/core/test_separator_constants.py`
- `tests/unit/core/test_separators.py`
- `tests/unit/core/test_specql_parser_separators.py`
- `tests/unit/actions/test_identifier_hierarchical_dot.py`
- `tests/unit/actions/test_strip_tenant_prefix.py`
- `tests/integration/test_composite_hierarchical_e2e.py`
- `tests/integration/test_backward_compatibility.py`
- `src/generators/actions/templates/deduplication_loop.sql.jinja2`
- `docs/migration/SEPARATOR_MIGRATION_GUIDE.md`

**Updated Files** (4):
- `src/core/ast_models.py`
- `src/core/specql_parser.py`
- `src/generators/actions/identifier_recalc_generator.py`
- `IDENTIFIER_STRATEGIES_SPECQL.md`

**Total Effort**: ~800 lines code + 1200 lines tests + 300 lines docs = 2300 lines

---

## ✅ Final Acceptance Criteria

- [ ] `Separators` class with all constants
- [ ] Default hierarchy separator is `.` (dot)
- [ ] Composition separator is `∘` (ring operator)
- [ ] `strip_tenant_prefix` works correctly
- [ ] `composite_hierarchical` strategy implemented
- [ ] Tenant prefix still uses `|` (pipe)
- [ ] Backward compatibility: explicit `_` override works
- [ ] 90%+ test coverage
- [ ] All integration tests pass
- [ ] Documentation complete
- [ ] Migration guide written

---

**Status**: 🎯 Ready for Implementation
**Priority**: HIGH (affects all identifier generation)
**Dependencies**: `safe_slug()` function, Team A parser complete
**Methodology**: Strict TDD - RED → GREEN → REFACTOR → QA at each phase
