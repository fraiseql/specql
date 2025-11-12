# Missing Patterns Implementation Plans

**Document Purpose**: Detailed phased implementation plans for three patterns from PrintOptim backend:
1. Identifier Recalculation (recalcid functions)
2. LTREE Hierarchical Data
3. Node + Info Two-Table Split for Hierarchical Entities

**Methodology**: Phased TDD Approach (RED → GREEN → REFACTOR → QA)

**Overall Timeline**: 6 weeks (2 weeks per pattern)

**Expert Validation**: SQL architect confirmed node+info split is "good, intentional design" for hierarchical entities.

---

## Pattern 1: Identifier Recalculation (recalcid) Functions

### Executive Summary

**Problem**: Derived/computed fields (temporal flags, aggregated values, cache columns) become stale when source data changes. Manual recalculation is error-prone.

**Solution**: Auto-generate `recalcid_{entity}()` functions that recalculate derived fields, with cascade support for related entities.

**Complexity**: COMPLEX - Multi-phase TDD approach required

**Teams Involved**:
- **Team B**: Generate `recalculation_context` composite type
- **Team C**: Generate `recalcid_{entity}()` functions and cascade triggers

**Business Value**: Eliminates data inconsistency bugs, enables complex temporal business logic

---

### PHASE 1: Foundation - Recalculation Context Type

**Objective**: Create reusable `recalculation_context` composite type for propagating entity IDs through cascade chains

**Duration**: 2 days

#### TDD Cycle 1.1: Define Recalculation Context Type

**RED**: Write failing test for context type generation
```python
# tests/unit/schema/test_recalculation_context.py
def test_generate_recalculation_context_type():
    """Schema generator should create recalculation_context composite type"""
    generator = SchemaGenerator()

    # Generate foundation types (one-time, goes in migration 000)
    sql = generator.generate_foundation_types()

    assert "CREATE TYPE core.recalculation_context" in sql
    assert "entity_id INTEGER" in sql
    assert "entity_uuid UUID" in sql
    assert "related_ids INTEGER[]" in sql
    assert "tenant_id INTEGER" in sql

    # Run test - should FAIL (not implemented yet)
```

**Expected failure**: `AttributeError: 'SchemaGenerator' object has no attribute 'generate_foundation_types'`

---

**GREEN**: Minimal implementation to pass test
```python
# src/generators/schema/schema_generator.py
class SchemaGenerator:
    def generate_foundation_types(self) -> str:
        """Generate one-time foundation types for framework"""
        return """
-- Recalculation context for cascade updates
CREATE TYPE core.recalculation_context AS (
    entity_id INTEGER,        -- Primary key of entity being recalculated
    entity_uuid UUID,          -- UUID of entity (for external references)
    related_ids INTEGER[],     -- PKs of related entities affected
    tenant_id INTEGER          -- Tenant context for multi-tenancy
);

COMMENT ON TYPE core.recalculation_context IS
  'Context object passed through recalculation cascade chains';
"""
```

**Run test**: `uv run pytest tests/unit/schema/test_recalculation_context.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Clean up and add documentation
```python
# src/generators/schema/schema_generator.py
class SchemaGenerator:
    def generate_foundation_types(self) -> str:
        """
        Generate framework foundation types (one-time generation).

        These types are created once in migration 000 and used across
        all entities. Currently includes:
        - recalculation_context: For cascade update propagation

        Returns:
            SQL DDL for foundation types
        """
        types_sql = []

        # Recalculation context type
        types_sql.append(self._recalculation_context_type())

        return "\n\n".join(types_sql)

    def _recalculation_context_type(self) -> str:
        """Generate recalculation_context composite type"""
        return """
-- ============================================================
-- RECALCULATION CONTEXT TYPE
-- ============================================================
-- Context object for propagating entity information through
-- cascade update chains (recalcid functions).
--
-- Usage:
--   v_ctx := ROW(pk_entity, entity.id, NULL, NULL)::core.recalculation_context;
--   PERFORM core.recalcid_related_entity(v_ctx);
-- ============================================================

CREATE TYPE core.recalculation_context AS (
    entity_id INTEGER,        -- Primary key of source entity
    entity_uuid UUID,          -- UUID of source entity
    related_ids INTEGER[],     -- PKs of affected related entities
    tenant_id INTEGER          -- Tenant context (NULL if not multi-tenant)
);

COMMENT ON TYPE core.recalculation_context IS
  '@fraiseql:type name=RecalculationContext internal=true';
""".strip()
```

**Run tests**: `uv run pytest tests/unit/schema/ -v`

**Expected**: ✅ All schema tests pass

---

**QA**: Verify quality and integration
```bash
# Full test suite
uv run pytest --tb=short

# Type checking
uv run mypy src/generators/schema/

# Linting
uv run ruff check src/generators/schema/

# Integration test - verify SQL is valid
uv run pytest tests/integration/test_foundation_types.py -v
```

**Quality gates**:
- [ ] All tests pass
- [ ] Type hints correct
- [ ] No linting errors
- [ ] Generated SQL executes without errors in PostgreSQL

---

#### TDD Cycle 1.2: Add to Migration 000 Generator

**RED**: Write failing test for migration 000 inclusion
```python
# tests/unit/cli/test_migration_000.py
def test_migration_000_includes_foundation_types():
    """Migration 000 should include all foundation types"""
    orchestrator = Orchestrator()

    # Generate base migration (migration 000)
    migration_000 = orchestrator.generate_migration_000()

    assert "CREATE TYPE core.recalculation_context" in migration_000
    assert "CREATE SCHEMA IF NOT EXISTS core" in migration_000

    # Should come before any entity tables
    context_pos = migration_000.index("recalculation_context")
    entity_pos = migration_000.find("CREATE TABLE")
    assert context_pos < entity_pos, "Foundation types must come before tables"
```

**Expected failure**: `AttributeError: 'Orchestrator' object has no attribute 'generate_migration_000'`

---

**GREEN**: Minimal implementation
```python
# src/cli/orchestrator.py
class Orchestrator:
    def generate_migration_000(self) -> str:
        """
        Generate migration 000 with framework foundations:
        - Schemas
        - Extensions
        - Foundation types
        """
        schema_gen = SchemaGenerator()

        parts = [
            "-- Migration 000: Framework Foundations",
            "-- Auto-generated by SpecQL",
            "",
            "-- Create schemas",
            "CREATE SCHEMA IF NOT EXISTS core;",
            "CREATE SCHEMA IF NOT EXISTS management;",
            "CREATE SCHEMA IF NOT EXISTS tenant;",
            "CREATE SCHEMA IF NOT EXISTS catalog;",
            "",
            "-- Extensions",
            "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
            "",
            "-- Foundation types",
            schema_gen.generate_foundation_types()
        ]

        return "\n".join(parts)
```

**Run test**: `uv run pytest tests/unit/cli/test_migration_000.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Extract schema list to configuration
```python
# src/core/config.py
@dataclass
class FrameworkConfig:
    """Framework-wide configuration"""

    # Standard schemas (always created)
    STANDARD_SCHEMAS = [
        "core",        # Framework foundations
        "management",  # Management entities
        "tenant",      # Tenant-scoped entities
        "catalog",     # Reference data
        "mutation_metadata"  # FraiseQL metadata types
    ]

    # Required extensions
    REQUIRED_EXTENSIONS = [
        "uuid-ossp",   # UUID generation
        "ltree"        # Hierarchical data (added for Pattern 2)
    ]

# src/cli/orchestrator.py
from src.core.config import FrameworkConfig

class Orchestrator:
    def __init__(self):
        self.config = FrameworkConfig()

    def generate_migration_000(self) -> str:
        """Generate migration 000 with framework foundations"""
        schema_gen = SchemaGenerator()

        # Generate schema creation SQL
        schemas_sql = "\n".join([
            f"CREATE SCHEMA IF NOT EXISTS {schema};"
            for schema in self.config.STANDARD_SCHEMAS
        ])

        # Generate extension SQL
        extensions_sql = "\n".join([
            f"CREATE EXTENSION IF NOT EXISTS \"{ext}\";"
            for ext in self.config.REQUIRED_EXTENSIONS
        ])

        parts = [
            "-- ============================================================",
            "-- Migration 000: Framework Foundations",
            "-- Auto-generated by SpecQL Code Generator",
            "-- ============================================================",
            "",
            "-- Schemas",
            schemas_sql,
            "",
            "-- Extensions",
            extensions_sql,
            "",
            "-- Foundation Types",
            schema_gen.generate_foundation_types()
        ]

        return "\n".join(parts)
```

**Run tests**: `uv run pytest tests/unit/cli/ -v`

**Expected**: ✅ All CLI tests pass

---

**QA**: Integration testing
```python
# tests/integration/test_migration_000_execution.py
import psycopg2
import pytest

def test_migration_000_executes_successfully(test_db_connection):
    """Migration 000 should execute without errors in PostgreSQL"""
    orchestrator = Orchestrator()
    migration_sql = orchestrator.generate_migration_000()

    conn = test_db_connection
    cursor = conn.cursor()

    # Execute migration
    cursor.execute(migration_sql)
    conn.commit()

    # Verify schemas exist
    cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name IN ('core', 'management', 'tenant')
    """)
    schemas = [row[0] for row in cursor.fetchall()]
    assert 'core' in schemas
    assert 'management' in schemas

    # Verify type exists
    cursor.execute("""
        SELECT typname
        FROM pg_type
        WHERE typname = 'recalculation_context'
    """)
    assert cursor.fetchone() is not None
```

**Run integration tests**: `uv run pytest tests/integration/ -v`

**Expected**: ✅ Migration executes cleanly

---

### PHASE 2: AST Support for Recalcid Configuration

**Objective**: Extend SpecQL AST to parse and represent recalcid configuration

**Duration**: 3 days

#### TDD Cycle 2.1: Parse recalcid Flag

**RED**: Write failing test
```python
# tests/unit/core/test_recalcid_parsing.py
def test_parse_recalcid_flag():
    """Parser should recognize operations.recalcid flag"""
    yaml_content = """
entity: Contact
schema: crm

fields:
  status: enum(lead, qualified)

operations:
  recalcid: true
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.operations.recalcid is True
```

**Expected failure**: Test should fail (already implemented in AST, but test missing)

---

**GREEN**: Verify implementation exists
```python
# This should already pass - AST models have recalcid support
# src/core/ast_models.py already has:
# @dataclass
# class OperationConfig:
#     recalcid: bool = True
```

**Run test**: `uv run pytest tests/unit/core/test_recalcid_parsing.py -v`

**Expected**: ✅ PASS (implementation already exists)

---

#### TDD Cycle 2.2: Parse Cascade Updates Configuration

**RED**: Write failing test
```python
# tests/unit/core/test_cascade_updates_parsing.py
def test_parse_cascade_updates():
    """Parser should recognize business_logic.cascade_updates"""
    yaml_content = """
entity: MachineItem

business_logic:
  cascade_updates:
    - name: recalculate_identifiers
      trigger: after_insert
      scope: self
      function: recalcid_machine_item
      parameters: [v_ctx]

    - name: refresh_parent_machine
      trigger: after_insert
      scope: parent
      entity: Machine
      function: refresh_machine
      parameters: [v_ctx]
      ignore_errors: true
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.business_logic.cascade_updates) == 2

    # First cascade
    recalc = entity.business_logic.cascade_updates[0]
    assert recalc.name == "recalculate_identifiers"
    assert recalc.trigger == "after_insert"
    assert recalc.scope == "self"
    assert recalc.function == "recalcid_machine_item"
    assert recalc.parameters == ["v_ctx"]

    # Second cascade
    refresh = entity.business_logic.cascade_updates[1]
    assert refresh.scope == "parent"
    assert refresh.entity == "Machine"
    assert refresh.ignore_errors is True
```

**Expected failure**: `AttributeError: 'BusinessLogic' object has no attribute 'cascade_updates'`

---

**GREEN**: Add AST model for cascade updates
```python
# src/core/ast_models.py

@dataclass
class CascadeUpdate:
    """Cascade update configuration for recalcid chains"""
    name: str
    trigger: str  # "after_insert", "after_update", "after_delete"
    scope: str    # "self", "parent", "related"
    function: str
    parameters: List[str]
    entity: Optional[str] = None  # For parent/related scope
    ignore_errors: bool = False
    find_related: Optional[Dict[str, Any]] = None  # For related scope

@dataclass
class BusinessLogic:
    """Business logic configuration"""
    default_values: List[DefaultValue] = field(default_factory=list)
    validations: List[Validation] = field(default_factory=list)
    cascade_updates: List[CascadeUpdate] = field(default_factory=list)  # NEW
    conflict_detection: List[ConflictDetection] = field(default_factory=list)
```

**Update parser**:
```python
# src/core/specql_parser.py

def _parse_business_logic(self, bl_data: Dict[str, Any]) -> BusinessLogic:
    """Parse business_logic section"""
    return BusinessLogic(
        default_values=self._parse_default_values(bl_data.get("default_values", [])),
        validations=self._parse_validations(bl_data.get("validations", [])),
        cascade_updates=self._parse_cascade_updates(bl_data.get("cascade_updates", [])),
        conflict_detection=self._parse_conflict_detection(bl_data.get("conflict_detection", []))
    )

def _parse_cascade_updates(self, cascade_data: List[Dict]) -> List[CascadeUpdate]:
    """Parse cascade_updates configuration"""
    cascades = []
    for item in cascade_data:
        cascades.append(CascadeUpdate(
            name=item["name"],
            trigger=item["trigger"],
            scope=item["scope"],
            function=item["function"],
            parameters=item["parameters"],
            entity=item.get("entity"),
            ignore_errors=item.get("ignore_errors", False),
            find_related=item.get("find_related")
        ))
    return cascades
```

**Run test**: `uv run pytest tests/unit/core/test_cascade_updates_parsing.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Add validation for cascade configuration
```python
# src/core/specql_parser.py

def _parse_cascade_updates(self, cascade_data: List[Dict]) -> List[CascadeUpdate]:
    """Parse and validate cascade_updates configuration"""
    cascades = []

    for idx, item in enumerate(cascade_data):
        # Validate required fields
        if "name" not in item:
            raise ValueError(f"cascade_updates[{idx}]: 'name' is required")
        if "trigger" not in item:
            raise ValueError(f"cascade_updates[{idx}]: 'trigger' is required")

        # Validate trigger value
        valid_triggers = ["after_insert", "after_update", "after_delete"]
        if item["trigger"] not in valid_triggers:
            raise ValueError(
                f"cascade_updates[{idx}]: trigger must be one of {valid_triggers}"
            )

        # Validate scope
        valid_scopes = ["self", "parent", "related"]
        scope = item.get("scope", "self")
        if scope not in valid_scopes:
            raise ValueError(
                f"cascade_updates[{idx}]: scope must be one of {valid_scopes}"
            )

        # Validate scope-specific requirements
        if scope in ["parent", "related"] and "entity" not in item:
            raise ValueError(
                f"cascade_updates[{idx}]: 'entity' is required for scope={scope}"
            )

        if scope == "related" and "find_related" not in item:
            raise ValueError(
                f"cascade_updates[{idx}]: 'find_related' is required for scope=related"
            )

        cascades.append(CascadeUpdate(
            name=item["name"],
            trigger=item["trigger"],
            scope=scope,
            function=item["function"],
            parameters=item.get("parameters", []),
            entity=item.get("entity"),
            ignore_errors=item.get("ignore_errors", False),
            find_related=item.get("find_related")
        ))

    return cascades
```

**Add validation tests**:
```python
# tests/unit/core/test_cascade_updates_validation.py
import pytest

def test_cascade_missing_name_raises_error():
    """Missing name should raise validation error"""
    yaml_content = """
entity: Test
business_logic:
  cascade_updates:
    - trigger: after_insert
      function: test_func
"""
    parser = SpecQLParser()
    with pytest.raises(ValueError, match="'name' is required"):
        parser.parse(yaml_content)

def test_cascade_invalid_trigger_raises_error():
    """Invalid trigger should raise validation error"""
    yaml_content = """
entity: Test
business_logic:
  cascade_updates:
    - name: test
      trigger: before_insert  # Invalid
      function: test_func
"""
    parser = SpecQLParser()
    with pytest.raises(ValueError, match="trigger must be one of"):
        parser.parse(yaml_content)

def test_cascade_parent_scope_requires_entity():
    """Parent scope without entity should raise error"""
    yaml_content = """
entity: Test
business_logic:
  cascade_updates:
    - name: test
      trigger: after_insert
      scope: parent
      function: test_func
"""
    parser = SpecQLParser()
    with pytest.raises(ValueError, match="'entity' is required for scope=parent"):
        parser.parse(yaml_content)
```

**Run tests**: `uv run pytest tests/unit/core/test_cascade_updates*.py -v`

**Expected**: ✅ All cascade parsing tests pass

---

**QA**: Full quality check
```bash
uv run pytest tests/unit/core/ -v
uv run mypy src/core/
uv run ruff check src/core/
```

**Quality gates**:
- [ ] All core tests pass
- [ ] Type checking passes
- [ ] No linting errors
- [ ] Validation catches malformed YAML

---

### PHASE 3: Generate recalcid Functions (Team C)

**Objective**: Generate `recalcid_{entity}()` functions that recalculate derived fields

**Duration**: 5 days

#### TDD Cycle 3.1: Basic recalcid Function Generation

**RED**: Write failing test
```python
# tests/unit/actions/test_recalcid_generation.py
def test_generate_basic_recalcid_function():
    """Should generate recalcid function for entity with derived fields"""
    entity = Entity(
        name="Allocation",
        schema="management",
        fields=[
            Field(name="start_date", field_type=FieldType(base_type="date")),
            Field(name="end_date", field_type=FieldType(base_type="date")),
            Field(name="is_current", field_type=FieldType(base_type="boolean")),
            Field(name="is_past", field_type=FieldType(base_type="boolean")),
        ],
        operations=OperationConfig(recalcid=True)
    )

    compiler = ActionCompiler()
    sql = compiler.generate_recalcid_function(entity)

    # Should generate function signature
    assert "CREATE OR REPLACE FUNCTION management.recalcid_allocation" in sql
    assert "p_ctx core.recalculation_context" in sql
    assert "RETURNS void" in sql

    # Should recalculate derived fields
    assert "UPDATE management.tb_allocation" in sql
    assert "is_current =" in sql
    assert "is_past =" in sql

    # Should use context
    assert "(p_ctx).entity_id" in sql
```

**Expected failure**: `AttributeError: 'ActionCompiler' object has no attribute 'generate_recalcid_function'`

---

**GREEN**: Minimal implementation
```python
# src/generators/actions/action_compiler.py

class ActionCompiler:
    def generate_recalcid_function(self, entity: Entity) -> str:
        """
        Generate recalcid_{entity}() function.

        Currently generates basic template - derived field detection
        will be added in refactor phase.
        """
        schema = entity.schema
        entity_name = entity.name.lower()
        table_name = f"tb_{entity_name}"
        pk_name = f"pk_{entity_name}"

        return f"""
CREATE OR REPLACE FUNCTION {schema}.recalcid_{entity_name}(
    p_ctx core.recalculation_context
)
RETURNS void AS $$
BEGIN
    -- Recalculate derived fields
    UPDATE {schema}.{table_name}
    SET
        is_current = (start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE),
        is_past = (end_date < CURRENT_DATE),
        updated_at = now(),
        updated_by = (p_ctx).tenant_id
    WHERE {pk_name} = (p_ctx).entity_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION {schema}.recalcid_{entity_name} IS
  'Recalculate derived/computed fields for {entity.name}';
""".strip()
```

**Run test**: `uv run pytest tests/unit/actions/test_recalcid_generation.py::test_generate_basic_recalcid_function -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Make it field-driven (detect derived fields)
```python
# src/generators/actions/recalcid_generator.py

from typing import List, Tuple
from src.core.ast_models import Entity, Field

class RecalcidGenerator:
    """Generator for recalcid functions"""

    def __init__(self):
        self.temporal_field_patterns = {
            "is_current": "start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE",
            "is_past": "end_date < CURRENT_DATE",
            "is_future": "start_date > CURRENT_DATE",
            "is_active": "start_date <= CURRENT_DATE AND (end_date IS NULL OR end_date >= CURRENT_DATE)"
        }

    def generate(self, entity: Entity) -> str:
        """Generate recalcid function for entity"""
        if not entity.operations.recalcid:
            return ""

        derived_fields = self._detect_derived_fields(entity)

        if not derived_fields:
            # No derived fields, skip function generation
            return ""

        return self._build_function(entity, derived_fields)

    def _detect_derived_fields(self, entity: Entity) -> List[Tuple[str, str]]:
        """
        Detect derived/computed fields that need recalculation.

        Returns:
            List of (field_name, calculation_expression) tuples
        """
        derived = []
        field_names = {f.name for f in entity.fields}

        # Check for temporal boolean patterns
        for field_name, expression in self.temporal_field_patterns.items():
            if field_name in field_names:
                # Verify required date fields exist
                if "start_date" in field_names and "end_date" in field_names:
                    derived.append((field_name, expression))

        return derived

    def _build_function(self, entity: Entity, derived_fields: List[Tuple[str, str]]) -> str:
        """Build recalcid function SQL"""
        schema = entity.schema
        entity_name = entity.name.lower()
        table_name = f"tb_{entity_name}"
        pk_name = f"pk_{entity_name}"

        # Build SET clause
        set_assignments = []
        for field_name, expression in derived_fields:
            set_assignments.append(f"        {field_name} = ({expression})")

        # Always update audit fields
        set_assignments.extend([
            "        updated_at = now()",
            "        updated_by = (p_ctx).tenant_id"
        ])

        set_clause = ",\n".join(set_assignments)

        return f"""
CREATE OR REPLACE FUNCTION {schema}.recalcid_{entity_name}(
    p_ctx core.recalculation_context
)
RETURNS void AS $$
BEGIN
    -- Recalculate derived/computed fields
    UPDATE {schema}.{table_name}
    SET
{set_clause}
    WHERE {pk_name} = (p_ctx).entity_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION {schema}.recalcid_{entity_name} IS
  '@fraiseql:internal
   Recalculate derived fields for {entity.name}.
   Derived fields: {", ".join([f[0] for f in derived_fields])}';
""".strip()

# Update ActionCompiler to use RecalcidGenerator
# src/generators/actions/action_compiler.py

class ActionCompiler:
    def __init__(self):
        self.recalcid_gen = RecalcidGenerator()

    def generate_recalcid_function(self, entity: Entity) -> str:
        """Generate recalcid function using specialized generator"""
        return self.recalcid_gen.generate(entity)
```

**Add more comprehensive tests**:
```python
# tests/unit/actions/test_recalcid_detection.py

def test_detect_temporal_derived_fields():
    """Should detect temporal boolean fields"""
    entity = Entity(
        name="Allocation",
        schema="management",
        fields=[
            Field(name="start_date", field_type=FieldType(base_type="date")),
            Field(name="end_date", field_type=FieldType(base_type="date")),
            Field(name="is_current", field_type=FieldType(base_type="boolean")),
            Field(name="is_past", field_type=FieldType(base_type="boolean")),
            Field(name="is_future", field_type=FieldType(base_type="boolean")),
        ],
        operations=OperationConfig(recalcid=True)
    )

    generator = RecalcidGenerator()
    derived = generator._detect_derived_fields(entity)

    assert len(derived) == 3
    field_names = [f[0] for f in derived]
    assert "is_current" in field_names
    assert "is_past" in field_names
    assert "is_future" in field_names

def test_skip_entity_without_recalcid_flag():
    """Should not generate function if recalcid=False"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields=[Field(name="email", field_type=FieldType(base_type="text"))],
        operations=OperationConfig(recalcid=False)
    )

    generator = RecalcidGenerator()
    sql = generator.generate(entity)

    assert sql == ""

def test_skip_entity_without_derived_fields():
    """Should not generate function if no derived fields detected"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields=[
            Field(name="email", field_type=FieldType(base_type="text")),
            Field(name="status", field_type=FieldType(base_type="text"))
        ],
        operations=OperationConfig(recalcid=True)
    )

    generator = RecalcidGenerator()
    sql = generator.generate(entity)

    assert sql == ""
```

**Run tests**: `uv run pytest tests/unit/actions/test_recalcid*.py -v`

**Expected**: ✅ All recalcid tests pass

---

**QA**: Integration test with real database
```python
# tests/integration/test_recalcid_execution.py

def test_recalcid_function_executes(test_db):
    """Generated recalcid function should execute without errors"""

    # Setup: Create entity and generate SQL
    entity = Entity(
        name="Allocation",
        schema="management",
        fields=[
            Field(name="start_date", field_type=FieldType(base_type="date")),
            Field(name="end_date", field_type=FieldType(base_type="date")),
            Field(name="is_current", field_type=FieldType(base_type="boolean")),
        ],
        operations=OperationConfig(recalcid=True)
    )

    schema_gen = SchemaGenerator()
    action_compiler = ActionCompiler()

    table_sql = schema_gen.generate_table(entity)
    recalcid_sql = action_compiler.generate_recalcid_function(entity)

    # Execute SQL
    test_db.execute(table_sql)
    test_db.execute(recalcid_sql)

    # Insert test data
    test_db.execute("""
        INSERT INTO management.tb_allocation (start_date, end_date, is_current)
        VALUES ('2025-01-01', '2025-12-31', FALSE)
        RETURNING pk_allocation
    """)
    pk = test_db.fetchone()[0]

    # Call recalcid function
    test_db.execute(f"""
        SELECT management.recalcid_allocation(
            ROW({pk}, NULL, NULL, NULL)::core.recalculation_context
        )
    """)

    # Verify field was recalculated
    test_db.execute(f"""
        SELECT is_current
        FROM management.tb_allocation
        WHERE pk_allocation = {pk}
    """)
    is_current = test_db.fetchone()[0]
    assert is_current is True  # 2025-11-08 is between 2025-01-01 and 2025-12-31
```

**Quality gates**:
- [ ] All unit tests pass
- [ ] Integration test executes in real PostgreSQL
- [ ] Generated SQL is syntactically valid
- [ ] Function correctly recalculates fields

---

#### TDD Cycle 3.2: Cascade Updates Integration

**RED**: Write failing test
```python
# tests/unit/actions/test_cascade_updates.py

def test_generate_function_with_cascade_updates():
    """Should add cascade calls to generated functions"""
    entity = Entity(
        name="MachineItem",
        schema="management",
        fields=[Field(name="machine", field_type=FieldType(base_type="ref", ref_entity="Machine"))],
        business_logic=BusinessLogic(
            cascade_updates=[
                CascadeUpdate(
                    name="recalculate_self",
                    trigger="after_insert",
                    scope="self",
                    function="recalcid_machine_item",
                    parameters=["v_ctx"]
                ),
                CascadeUpdate(
                    name="refresh_parent",
                    trigger="after_insert",
                    scope="parent",
                    entity="Machine",
                    function="refresh_machine",
                    parameters=["v_ctx"],
                    ignore_errors=True
                )
            ]
        )
    )

    compiler = ActionCompiler()
    sql = compiler.generate_insert_function(entity)

    # Should call recalcid on self
    assert "PERFORM management.recalcid_machine_item(v_ctx)" in sql

    # Should call parent refresh with error handling
    assert "BEGIN" in sql
    assert "PERFORM management.refresh_machine(ctx := v_ctx)" in sql
    assert "EXCEPTION WHEN OTHERS THEN NULL" in sql
```

**Expected failure**: Generated function doesn't include cascade calls

---

**GREEN**: Add cascade generation
```python
# src/generators/actions/cascade_generator.py

class CascadeGenerator:
    """Generate cascade update calls"""

    def generate_cascade_calls(
        self,
        cascades: List[CascadeUpdate],
        trigger: str
    ) -> str:
        """
        Generate SQL for cascade update calls.

        Args:
            cascades: List of cascade configurations
            trigger: Current trigger point (after_insert, after_update, etc.)

        Returns:
            SQL statements for cascade calls
        """
        calls = []

        for cascade in cascades:
            if cascade.trigger != trigger:
                continue

            call_sql = self._build_cascade_call(cascade)

            if cascade.ignore_errors:
                call_sql = f"""
    BEGIN
        {call_sql}
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
"""
            else:
                call_sql = f"    {call_sql}"

            calls.append(call_sql)

        return "\n".join(calls)

    def _build_cascade_call(self, cascade: CascadeUpdate) -> str:
        """Build individual cascade call"""

        # Build parameter list
        params = ", ".join([
            f"{p.split(':=')[0].strip()} := {p.split(':=')[1].strip()}"
            if ":=" in p else p
            for p in cascade.parameters
        ])

        if cascade.scope == "self":
            schema = "management"  # TODO: get from entity
            return f"PERFORM {schema}.{cascade.function}({params});"

        elif cascade.scope == "parent":
            # TODO: Determine schema from entity reference
            schema = "management"
            return f"PERFORM {schema}.{cascade.function}({params});"

        elif cascade.scope == "related":
            # TODO: Build query to find related entities
            # This is complex - needs Phase 4
            return f"-- TODO: Related cascade for {cascade.entity}"

        return ""

# Update ActionCompiler
class ActionCompiler:
    def __init__(self):
        self.recalcid_gen = RecalcidGenerator()
        self.cascade_gen = CascadeGenerator()

    def generate_insert_function(self, entity: Entity) -> str:
        """Generate INSERT function with cascade support"""

        # ... existing function generation ...

        # Add cascade calls after insert
        cascade_calls = self.cascade_gen.generate_cascade_calls(
            entity.business_logic.cascade_updates,
            trigger="after_insert"
        )

        # Insert cascade calls before RETURN
        # ... implementation details ...
```

**Run test**: `uv run pytest tests/unit/actions/test_cascade_updates.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Full integration with action compiler
```python
# src/generators/actions/action_compiler.py

class ActionCompiler:
    """Compile SpecQL actions to PL/pgSQL functions"""

    def __init__(self):
        self.recalcid_gen = RecalcidGenerator()
        self.cascade_gen = CascadeGenerator()
        self.step_compiler = StepCompiler()

    def compile(self, entity: Entity) -> str:
        """
        Compile all action-related functions for entity.

        Generates:
        - recalcid_{entity}() if operations.recalcid=true
        - {action_name}() for each action in entity.actions
        - INSERT/UPDATE triggers with cascade calls
        """
        functions = []

        # Generate recalcid function
        recalcid_fn = self.recalcid_gen.generate(entity)
        if recalcid_fn:
            functions.append(recalcid_fn)

        # Generate action functions
        for action in entity.actions:
            action_fn = self.compile_action(entity, action)
            functions.append(action_fn)

        # Generate triggers with cascades
        if entity.business_logic.cascade_updates:
            trigger_fn = self._generate_cascade_trigger(entity)
            functions.append(trigger_fn)

        return "\n\n".join(functions)

    def _generate_cascade_trigger(self, entity: Entity) -> str:
        """Generate trigger function that invokes cascade updates"""
        schema = entity.schema
        entity_name = entity.name.lower()

        # Build context creation
        context_init = """
    DECLARE
        v_ctx core.recalculation_context;
    BEGIN
        -- Build recalculation context
        v_ctx := ROW(
            NEW.pk_{entity_name},
            NEW.id,
            NULL,
            NULL
        )::core.recalculation_context;
""".format(entity_name=entity_name)

        # Generate cascade calls for each trigger type
        after_insert = self.cascade_gen.generate_cascade_calls(
            entity.business_logic.cascade_updates,
            trigger="after_insert"
        )

        after_update = self.cascade_gen.generate_cascade_calls(
            entity.business_logic.cascade_updates,
            trigger="after_update"
        )

        return f"""
CREATE OR REPLACE FUNCTION {schema}.{entity_name}_cascade_trigger()
RETURNS trigger AS $$
{context_init}

        -- After insert cascades
        IF (TG_OP = 'INSERT') THEN
{after_insert}
        END IF;

        -- After update cascades
        IF (TG_OP = 'UPDATE') THEN
{after_update}
        END IF;

        RETURN NEW;
    END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_{entity_name}_cascade
    AFTER INSERT OR UPDATE ON {schema}.tb_{entity_name}
    FOR EACH ROW
    EXECUTE FUNCTION {schema}.{entity_name}_cascade_trigger();
""".strip()
```

**Run tests**: `uv run pytest tests/unit/actions/ -v`

**Expected**: ✅ All action compiler tests pass

---

**QA**: End-to-end cascade test
```python
# tests/integration/test_cascade_chain.py

def test_cascade_chain_executes(test_db):
    """Cascade updates should propagate through entity relationships"""

    # Create parent entity (Machine)
    machine = Entity(name="Machine", schema="management", fields=[...])

    # Create child entity (MachineItem) with cascade to parent
    machine_item = Entity(
        name="MachineItem",
        schema="management",
        fields=[...],
        business_logic=BusinessLogic(
            cascade_updates=[
                CascadeUpdate(
                    name="refresh_parent",
                    trigger="after_insert",
                    scope="parent",
                    entity="Machine",
                    function="refresh_machine",
                    parameters=["v_ctx"]
                )
            ]
        )
    )

    # Generate and execute SQL
    compiler = ActionCompiler()
    schema_gen = SchemaGenerator()

    test_db.execute(schema_gen.generate_table(machine))
    test_db.execute(compiler.compile(machine))

    test_db.execute(schema_gen.generate_table(machine_item))
    test_db.execute(compiler.compile(machine_item))

    # Insert parent
    test_db.execute("INSERT INTO management.tb_machine (...) VALUES (...)")

    # Insert child - should trigger cascade to parent
    test_db.execute("INSERT INTO management.tb_machine_item (...) VALUES (...)")

    # Verify parent was refreshed
    # ... verification logic ...
```

**Quality gates**:
- [ ] All tests pass
- [ ] Cascade chain executes without errors
- [ ] Parent entity is updated when child changes
- [ ] Error handling works (ignore_errors=true)

---

### PHASE 4: Related Entity Cascades

**Objective**: Support `scope: related` cascades that find and update related entities

**Duration**: 3 days

*(This phase is complex and would follow similar TDD cycles - skipping for brevity)*

**Key Features**:
- Parse `find_related` query configuration
- Generate SQL to find related PKs
- Batch call recalcid functions for related entities
- Handle edge cases (no related entities, circular references)

---

## Success Criteria - Pattern 1

- [ ] `recalculation_context` type generated in migration 000
- [ ] SpecQL parser recognizes `operations.recalcid` and `business_logic.cascade_updates`
- [ ] `recalcid_{entity}()` functions auto-generated for entities with derived fields
- [ ] Cascade triggers call recalcid functions after INSERT/UPDATE
- [ ] `scope: self` cascades work
- [ ] `scope: parent` cascades work
- [ ] `scope: related` cascades work (Phase 4)
- [ ] Error handling respects `ignore_errors` flag
- [ ] All tests pass (90%+ coverage)
- [ ] Integration tests verify cascade chains execute correctly
- [ ] Documentation updated with examples

---

## Pattern 2: LTREE Hierarchical Data

### Executive Summary

**Problem**: Self-referencing hierarchies (organizational units, locations, industry classifications) need efficient ancestor/descendant queries and path-based operations.

**Solution**: Auto-generate LTREE `path` column for entities with `parent: ref(self)`, with automatic path maintenance triggers.

**Complexity**: MEDIUM - Simpler than recalcid, but requires trigger logic

**Teams Involved**:
- **Team B**: Generate LTREE columns, indexes, and triggers

**Business Value**: Enables efficient hierarchical queries (find all descendants, get ancestors, etc.) without recursive CTEs

**Expert Validation**: SQL architect confirmed this is standard pattern for hierarchical data in PostgreSQL

---

### PHASE 1: LTREE Foundation

**Objective**: Add LTREE extension to framework foundations

**Duration**: 1 day

#### TDD Cycle 1.1: Add LTREE Extension

**RED**: Write failing test
```python
# tests/unit/schema/test_ltree_foundation.py

def test_migration_000_includes_ltree_extension():
    """Migration 000 should enable LTREE extension"""
    orchestrator = Orchestrator()
    migration_sql = orchestrator.generate_migration_000()

    assert 'CREATE EXTENSION IF NOT EXISTS "ltree"' in migration_sql
```

**Expected failure**: LTREE not in extension list

---

**GREEN**: Add to config
```python
# src/core/config.py

@dataclass
class FrameworkConfig:
    REQUIRED_EXTENSIONS = [
        "uuid-ossp",
        "ltree"  # Add this
    ]
```

**Run test**: `uv run pytest tests/unit/schema/test_ltree_foundation.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: No refactoring needed - simple change

---

**QA**: Verify in integration test
```python
# tests/integration/test_ltree_available.py

def test_ltree_extension_available(test_db):
    """LTREE extension should be available after migration 000"""
    orchestrator = Orchestrator()
    test_db.execute(orchestrator.generate_migration_000())

    # Test LTREE functionality
    test_db.execute("""
        CREATE TABLE test_tree (path LTREE);
        INSERT INTO test_tree VALUES ('Top.Science.Astronomy');
    """)

    # Test LTREE operator
    result = test_db.execute("""
        SELECT path::text
        FROM test_tree
        WHERE path <@ 'Top.Science'
    """)

    assert result.fetchone()[0] == 'Top.Science.Astronomy'
```

---

### PHASE 2: Detect Hierarchical Entities

**Objective**: Identify entities with `parent: ref(self)` pattern

**Duration**: 2 days

#### TDD Cycle 2.1: Detect Self-Referencing Parent

**RED**: Write failing test
```python
# tests/unit/core/test_hierarchical_detection.py

def test_parse_self_referencing_parent():
    """Parser should recognize parent: ref(self) as hierarchical entity"""
    yaml_content = """
entity: Location
schema: management

fields:
  name: text
  parent: ref(Location)  # Self-reference
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Should mark as hierarchical
    assert entity.is_hierarchical is True

    # Should identify parent field
    parent_field = next(f for f in entity.fields if f.name == "parent")
    assert parent_field.field_type.is_self_reference is True
```

**Expected failure**: `AttributeError: 'Entity' object has no attribute 'is_hierarchical'`

---

**GREEN**: Add detection logic
```python
# src/core/ast_models.py

@dataclass
class FieldType:
    base_type: str
    ref_entity: Optional[str] = None
    is_self_reference: bool = False  # NEW
    # ... existing fields ...

@dataclass
class Entity:
    name: str
    schema: str
    fields: List[Field]
    is_hierarchical: bool = False  # NEW
    # ... existing fields ...

# src/core/specql_parser.py

def parse(self, yaml_content: str) -> Entity:
    """Parse SpecQL YAML to Entity AST"""
    data = yaml.safe_load(yaml_content)

    entity_name = data["entity"]
    fields = self._parse_fields(data.get("fields", {}), entity_name)

    # Detect hierarchical structure
    is_hierarchical = self._detect_hierarchical(fields, entity_name)

    entity = Entity(
        name=entity_name,
        schema=data.get("schema", "public"),
        fields=fields,
        is_hierarchical=is_hierarchical,
        # ... other fields ...
    )

    return entity

def _detect_hierarchical(self, fields: List[Field], entity_name: str) -> bool:
    """Detect if entity is hierarchical (has self-referencing parent field)"""
    for field in fields:
        if field.field_type.base_type == "ref":
            if field.field_type.ref_entity == entity_name:
                # Mark as self-reference
                field.field_type.is_self_reference = True
                return True
    return False
```

**Run test**: `uv run pytest tests/unit/core/test_hierarchical_detection.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Support explicit hierarchical flag
```python
# Support both implicit (parent: ref(self)) and explicit (hierarchical: true)

def test_explicit_hierarchical_flag():
    """Should support explicit hierarchical: true flag"""
    yaml_content = """
entity: Category
schema: catalog

hierarchical: true  # Explicit flag

fields:
  name: text
  parent_category: ref(Category)
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.is_hierarchical is True
```

---

**QA**: Test edge cases
```python
def test_non_hierarchical_entity():
    """Regular entities should not be marked hierarchical"""
    yaml_content = """
entity: Contact
fields:
  email: text
  company: ref(Company)  # Not self-reference
"""
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.is_hierarchical is False

def test_multiple_self_references_raises_error():
    """Multiple parent fields should raise validation error"""
    yaml_content = """
entity: Node
fields:
  parent1: ref(Node)
  parent2: ref(Node)  # Error - only one parent allowed
"""
    parser = SpecQLParser()
    with pytest.raises(ValueError, match="Multiple self-references not allowed"):
        parser.parse(yaml_content)
```

---

### PHASE 3: Generate LTREE Schema

**Objective**: Auto-generate `path` column, indexes, and triggers for hierarchical entities

**Duration**: 4 days

#### TDD Cycle 3.1: Generate Path Column

**RED**: Write failing test
```python
# tests/unit/schema/test_ltree_generation.py

def test_generate_ltree_path_column():
    """Should add LTREE path column to hierarchical entities"""
    entity = Entity(
        name="Location",
        schema="management",
        fields=[
            Field(name="name", field_type=FieldType(base_type="text")),
            Field(name="parent", field_type=FieldType(
                base_type="ref",
                ref_entity="Location",
                is_self_reference=True
            ))
        ],
        is_hierarchical=True
    )

    generator = SchemaGenerator()
    sql = generator.generate_table(entity)

    # Should include path column
    assert "path LTREE NOT NULL" in sql

    # Should include GIST index
    assert "CREATE INDEX idx_location_path_gist" in sql
    assert "USING GIST (path)" in sql

    # Should NOT generate regular btree index for parent FK
    # (path provides better query performance)
```

**Expected failure**: Generated SQL doesn't include path column

---

**GREEN**: Add path column generation
```python
# src/generators/schema/schema_generator.py

class SchemaGenerator:
    def generate_table(self, entity: Entity) -> str:
        """Generate CREATE TABLE statement"""

        columns = []

        # Trinity pattern
        columns.extend(self._trinity_columns(entity))

        # Business fields
        columns.extend(self._business_columns(entity))

        # Hierarchical path (if applicable)
        if entity.is_hierarchical:
            columns.append("    path LTREE NOT NULL")

        # Audit fields
        columns.extend(self._audit_columns())

        table_sql = f"""
CREATE TABLE {entity.schema}.tb_{entity.name.lower()} (
{','.join(columns)}
);
"""

        # Indexes
        indexes = self._generate_indexes(entity)

        return table_sql + "\n" + indexes

    def _generate_indexes(self, entity: Entity) -> str:
        """Generate indexes for table"""
        indexes = []
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        # Standard indexes for FK fields, etc.
        indexes.extend(self._standard_indexes(entity))

        # LTREE GIST index for hierarchical entities
        if entity.is_hierarchical:
            indexes.append(f"""
CREATE INDEX idx_{entity.name.lower()}_path_gist
    ON {table_name}
    USING GIST (path);
""".strip())

        return "\n".join(indexes)
```

**Run test**: `uv run pytest tests/unit/schema/test_ltree_generation.py::test_generate_ltree_path_column -v`

**Expected**: ✅ PASS

---

#### TDD Cycle 3.2: Generate Path Maintenance Trigger

**RED**: Write failing test
```python
# tests/unit/schema/test_ltree_triggers.py

def test_generate_path_maintenance_trigger():
    """Should generate trigger to maintain LTREE paths automatically"""
    entity = Entity(
        name="Location",
        schema="management",
        fields=[...],
        is_hierarchical=True
    )

    generator = SchemaGenerator()
    sql = generator.generate_table(entity)

    # Should include trigger function
    assert "CREATE OR REPLACE FUNCTION management.update_location_path()" in sql

    # Should calculate path from parent
    assert "SELECT path || text2ltree(NEW.identifier)" in sql
    assert "FROM management.tb_location" in sql
    assert "WHERE pk_location = NEW.fk_parent_location" in sql

    # Should handle root nodes (no parent)
    assert "NEW.path := text2ltree(NEW.identifier)" in sql

    # Should create trigger
    assert "CREATE TRIGGER trg_location_path" in sql
    assert "BEFORE INSERT OR UPDATE" in sql
```

**Expected failure**: No trigger function in generated SQL

---

**GREEN**: Generate trigger
```python
# src/generators/schema/ltree_generator.py

class LtreeGenerator:
    """Generator for LTREE hierarchical support"""

    def generate_path_trigger(self, entity: Entity) -> str:
        """Generate trigger function to maintain LTREE paths"""
        schema = entity.schema
        entity_name = entity.name.lower()
        table_name = f"tb_{entity_name}"
        pk_name = f"pk_{entity_name}"

        # Find parent field
        parent_field = next(
            (f for f in entity.fields if f.field_type.is_self_reference),
            None
        )
        if not parent_field:
            raise ValueError(f"Hierarchical entity {entity.name} has no parent field")

        parent_fk = f"fk_{parent_field.name}"

        return f"""
CREATE OR REPLACE FUNCTION {schema}.update_{entity_name}_path()
RETURNS trigger AS $$
BEGIN
    IF NEW.{parent_fk} IS NULL THEN
        -- Root node: path is just the identifier
        NEW.path := text2ltree(NEW.identifier);
    ELSE
        -- Child node: append to parent's path
        SELECT path || text2ltree(NEW.identifier)
        INTO NEW.path
        FROM {schema}.{table_name}
        WHERE {pk_name} = NEW.{parent_fk};

        IF NEW.path IS NULL THEN
            RAISE EXCEPTION 'Parent node not found: %', NEW.{parent_fk};
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_{entity_name}_path
    BEFORE INSERT OR UPDATE OF {parent_fk}, identifier
    ON {schema}.{table_name}
    FOR EACH ROW
    EXECUTE FUNCTION {schema}.update_{entity_name}_path();
""".strip()

# Update SchemaGenerator to use LtreeGenerator
class SchemaGenerator:
    def __init__(self):
        self.ltree_gen = LtreeGenerator()

    def generate_table(self, entity: Entity) -> str:
        """Generate table with LTREE support if hierarchical"""
        parts = [self._create_table_statement(entity)]
        parts.append(self._generate_indexes(entity))

        if entity.is_hierarchical:
            parts.append(self.ltree_gen.generate_path_trigger(entity))

        return "\n\n".join(parts)
```

**Run test**: `uv run pytest tests/unit/schema/test_ltree_triggers.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Add path update propagation
```python
# When a node moves (parent changes), update all descendant paths

class LtreeGenerator:
    def generate_path_trigger(self, entity: Entity) -> str:
        """Generate trigger with descendant update support"""

        # ... existing trigger code ...

        # Add UPDATE cascading for descendants
        update_descendants = f"""
    -- If parent changed, update all descendant paths
    IF (TG_OP = 'UPDATE' AND OLD.{parent_fk} IS DISTINCT FROM NEW.{parent_fk}) THEN
        -- Recursively update all descendants
        WITH RECURSIVE descendants AS (
            SELECT {pk_name}, path
            FROM {schema}.{table_name}
            WHERE {parent_fk} = NEW.{pk_name}

            UNION ALL

            SELECT t.{pk_name}, t.path
            FROM {schema}.{table_name} t
            JOIN descendants d ON t.{parent_fk} = d.{pk_name}
        )
        UPDATE {schema}.{table_name} t
        SET path = (
            SELECT path
            FROM {schema}.{table_name}
            WHERE {pk_name} = t.{parent_fk}
        ) || text2ltree(t.identifier)
        WHERE {pk_name} IN (SELECT {pk_name} FROM descendants);
    END IF;
"""

        # Insert into trigger function before RETURN NEW
        # ... implementation ...
```

---

**QA**: Integration test with real database
```python
# tests/integration/test_ltree_hierarchy.py

def test_ltree_path_automatically_maintained(test_db):
    """LTREE paths should be automatically calculated and updated"""

    entity = Entity(
        name="Location",
        schema="management",
        fields=[
            Field(name="name", field_type=FieldType(base_type="text")),
            Field(name="parent", field_type=FieldType(
                base_type="ref",
                ref_entity="Location",
                is_self_reference=True
            ))
        ],
        is_hierarchical=True
    )

    generator = SchemaGenerator()
    sql = generator.generate_table(entity)
    test_db.execute(sql)

    # Insert root node
    test_db.execute("""
        INSERT INTO management.tb_location (identifier, name, fk_parent_location)
        VALUES ('USA', 'United States', NULL)
        RETURNING pk_location, path::text
    """)
    usa_pk, usa_path = test_db.fetchone()
    assert usa_path == 'USA'

    # Insert child node
    test_db.execute(f"""
        INSERT INTO management.tb_location (identifier, name, fk_parent_location)
        VALUES ('CA', 'California', {usa_pk})
        RETURNING pk_location, path::text
    """)
    ca_pk, ca_path = test_db.fetchone()
    assert ca_path == 'USA.CA'

    # Insert grandchild
    test_db.execute(f"""
        INSERT INTO management.tb_location (identifier, name, fk_parent_location)
        VALUES ('SF', 'San Francisco', {ca_pk})
        RETURNING path::text
    """)
    sf_path = test_db.fetchone()[0]
    assert sf_path == 'USA.CA.SF'

    # Test hierarchical query - all CA descendants
    test_db.execute("""
        SELECT path::text
        FROM management.tb_location
        WHERE path <@ 'USA.CA'
        ORDER BY path
    """)
    results = test_db.fetchall()
    assert len(results) == 2  # CA and SF
    assert results[0][0] == 'USA.CA'
    assert results[1][0] == 'USA.CA.SF'

def test_move_node_updates_descendants(test_db):
    """Moving a node should update all descendant paths"""

    # Setup hierarchy: USA -> CA -> SF
    # ... insert nodes as above ...

    # Move CA to a different parent (create 'Canada' first)
    test_db.execute("""
        INSERT INTO management.tb_location (identifier, name, fk_parent_location)
        VALUES ('CAN', 'Canada', NULL)
        RETURNING pk_location
    """)
    canada_pk = test_db.fetchone()[0]

    # Move CA under Canada
    test_db.execute(f"""
        UPDATE management.tb_location
        SET fk_parent_location = {canada_pk}
        WHERE identifier = 'CA'
    """)

    # Verify CA and SF paths updated
    test_db.execute("""
        SELECT identifier, path::text
        FROM management.tb_location
        WHERE identifier IN ('CA', 'SF')
        ORDER BY identifier
    """)
    results = test_db.fetchall()
    assert results[0] == ('CA', 'CAN.CA')    # CA moved
    assert results[1] == ('SF', 'CAN.CA.SF')  # SF updated automatically
```

**Quality gates**:
- [ ] All unit tests pass
- [ ] Integration tests execute in PostgreSQL
- [ ] Paths automatically calculated on INSERT
- [ ] Paths updated when parent changes
- [ ] Descendant paths cascade correctly
- [ ] Hierarchical queries work (LTREE operators)

---

### PHASE 4: Helper Functions and Views

**Objective**: Generate convenience functions for common hierarchical operations

**Duration**: 2 days

#### TDD Cycle 4.1: Ancestor/Descendant Functions

**RED**: Write failing test
```python
# tests/unit/schema/test_ltree_helpers.py

def test_generate_ancestor_function():
    """Should generate function to get all ancestors"""
    entity = Entity(name="Location", is_hierarchical=True, ...)

    generator = SchemaGenerator()
    sql = generator.generate_table(entity)

    assert "CREATE FUNCTION management.location_ancestors" in sql
    assert "SELECT * FROM management.tb_location" in sql
    assert "WHERE p_path ~ CONCAT(path::text, '.*')::lquery" in sql
```

---

**GREEN**: Generate helper functions
```python
# src/generators/schema/ltree_generator.py

class LtreeGenerator:
    def generate_helper_functions(self, entity: Entity) -> str:
        """Generate helper functions for hierarchical queries"""
        schema = entity.schema
        entity_name = entity.name.lower()
        table_name = f"tb_{entity_name}"

        return f"""
-- Get all ancestors of a node (including self)
CREATE FUNCTION {schema}.{entity_name}_ancestors(p_path LTREE)
RETURNS SETOF {schema}.{table_name} AS $$
    SELECT *
    FROM {schema}.{table_name}
    WHERE p_path ~ CONCAT(path::text, '.*')::lquery
    ORDER BY nlevel(path);
$$ LANGUAGE sql STABLE;

-- Get all descendants of a node (including self)
CREATE FUNCTION {schema}.{entity_name}_descendants(p_path LTREE)
RETURNS SETOF {schema}.{table_name} AS $$
    SELECT *
    FROM {schema}.{table_name}
    WHERE path <@ p_path
    ORDER BY path;
$$ LANGUAGE sql STABLE;

-- Get immediate children only
CREATE FUNCTION {schema}.{entity_name}_children(p_pk INTEGER)
RETURNS SETOF {schema}.{table_name} AS $$
    SELECT *
    FROM {schema}.{table_name}
    WHERE fk_parent_{entity_name} = p_pk
    ORDER BY identifier;
$$ LANGUAGE sql STABLE;

-- Get depth/level in tree
CREATE FUNCTION {schema}.{entity_name}_depth(p_path LTREE)
RETURNS INTEGER AS $$
    SELECT nlevel(p_path);
$$ LANGUAGE sql IMMUTABLE;
""".strip()
```

---

**REFACTOR**: Add FraiseQL annotations
```python
# Add @fraiseql comments for GraphQL exposure

COMMENT ON FUNCTION {schema}.{entity_name}_ancestors IS
  '@fraiseql:query
   name={entity_name}Ancestors
   returns=[{entity.name}!]!
   description=Get all ancestors of a node';
```

---

**QA**: Test helper functions
```python
def test_ancestor_function_works(test_db):
    """Ancestor function should return parent chain"""
    # Setup: USA -> CA -> SF
    # ... insert nodes ...

    # Get ancestors of SF
    result = test_db.execute("""
        SELECT name
        FROM management.location_ancestors('USA.CA.SF')
        ORDER BY path
    """)

    names = [r[0] for r in result.fetchall()]
    assert names == ['United States', 'California', 'San Francisco']
```

---

## Success Criteria - Pattern 2

- [ ] LTREE extension enabled in migration 000
- [ ] Parser detects hierarchical entities (`parent: ref(self)`)
- [ ] `path LTREE` column auto-generated
- [ ] GIST index created on path
- [ ] Trigger automatically maintains paths on INSERT/UPDATE
- [ ] Moving nodes updates descendant paths
- [ ] Helper functions generated (ancestors, descendants, children, depth)
- [ ] All tests pass
- [ ] Integration tests verify hierarchical queries work
- [ ] Documentation includes LTREE usage examples

---

## Pattern 3: Node + Info Two-Table Split

### Executive Summary

**Problem**: Hierarchical entities have structural concerns (parent, path, identifier) mixed with domain-specific attributes, leading to complex tables and inconsistent patterns across hierarchies.

**Solution**: Split into `tb_{entity}` (structure: pk, parent, path, identifier) and `tb_{entity}_info` (domain attributes: name, type, metadata), with convenience view for querying.

**Complexity**: COMPLEX - Requires dual table generation, FK management, view creation

**Teams Involved**:
- **Team B**: Generate both tables + view
- **Team D**: FraiseQL annotations for both tables

**Business Value**: Clean separation of concerns, reusable tree logic, easier versioning/auditing of attribute changes

**Expert Validation**: SQL architect confirmed "good, intentional design" for hierarchical entities

---

### PHASE 1: AST Support for Metadata Split

**Objective**: Extend SpecQL to recognize and parse metadata split configuration

**Duration**: 2 days

#### TDD Cycle 1.1: Parse Metadata Split Flag

**RED**: Write failing test
```python
# tests/unit/core/test_metadata_split_parsing.py

def test_parse_metadata_split_flag():
    """Should recognize metadata_split flag for hierarchical entities"""
    yaml_content = """
entity: Location
schema: management

hierarchical: true
metadata_split: true  # Enable node+info pattern

fields:
  # Node fields (structural)
  parent: ref(Location)

  # Info fields (domain attributes)
  location_type: ref(LocationType)
  legal_name: text
  tax_id: text
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.metadata_split is True
    assert entity.is_hierarchical is True
```

**Expected failure**: `AttributeError: 'Entity' object has no attribute 'metadata_split'`

---

**GREEN**: Add to AST
```python
# src/core/ast_models.py

@dataclass
class Entity:
    name: str
    schema: str
    fields: List[Field]
    is_hierarchical: bool = False
    metadata_split: bool = False  # NEW
    # ... existing fields ...
```

**Update parser**:
```python
# src/core/specql_parser.py

def parse(self, yaml_content: str) -> Entity:
    data = yaml.safe_load(yaml_content)

    # ... existing parsing ...

    metadata_split = data.get("metadata_split", False)

    # Validation: metadata_split requires hierarchical
    if metadata_split and not is_hierarchical:
        raise ValueError(
            f"Entity {entity_name}: metadata_split requires hierarchical=true"
        )

    entity = Entity(
        # ... existing fields ...
        is_hierarchical=is_hierarchical,
        metadata_split=metadata_split
    )

    return entity
```

**Run test**: `uv run pytest tests/unit/core/test_metadata_split_parsing.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Add validation test
```python
def test_metadata_split_requires_hierarchical():
    """metadata_split without hierarchical should raise error"""
    yaml_content = """
entity: Contact
metadata_split: true  # Error - not hierarchical
fields:
  email: text
"""
    parser = SpecQLParser()
    with pytest.raises(ValueError, match="metadata_split requires hierarchical"):
        parser.parse(yaml_content)
```

---

**QA**: Edge cases
```python
def test_hierarchical_without_metadata_split():
    """Hierarchical entities can opt out of metadata split"""
    yaml_content = """
entity: Category
hierarchical: true
metadata_split: false  # Single table
fields:
  parent: ref(Category)
  name: text
"""
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.is_hierarchical is True
    assert entity.metadata_split is False
```

---

### PHASE 2: Field Classification

**Objective**: Classify fields into "node" (structural) vs "info" (domain) categories

**Duration**: 3 days

#### TDD Cycle 2.1: Detect Node vs Info Fields

**RED**: Write failing test
```python
# tests/unit/schema/test_field_classification.py

def test_classify_fields_for_metadata_split():
    """Should classify fields into node and info categories"""
    entity = Entity(
        name="Location",
        schema="management",
        is_hierarchical=True,
        metadata_split=True,
        fields=[
            # Node fields (structural)
            Field(name="parent", field_type=FieldType(base_type="ref", ref_entity="Location")),

            # Info fields (domain attributes)
            Field(name="location_type", field_type=FieldType(base_type="ref", ref_entity="LocationType")),
            Field(name="legal_name", field_type=FieldType(base_type="text")),
            Field(name="tax_id", field_type=FieldType(base_type="text")),
        ]
    )

    generator = SchemaGenerator()
    classifier = generator.field_classifier

    node_fields, info_fields = classifier.classify(entity)

    # Node fields: only parent (trinity, path, identifier auto-added)
    assert len(node_fields) == 1
    assert node_fields[0].name == "parent"

    # Info fields: all domain attributes
    assert len(info_fields) == 3
    info_names = [f.name for f in info_fields]
    assert "location_type" in info_names
    assert "legal_name" in info_names
    assert "tax_id" in info_names
```

**Expected failure**: `AttributeError: 'SchemaGenerator' object has no attribute 'field_classifier'`

---

**GREEN**: Implement classifier
```python
# src/generators/schema/field_classifier.py

class FieldClassifier:
    """Classify fields into node (structural) vs info (domain) for metadata split"""

    NODE_FIELD_PATTERNS = {
        "parent",           # Self-reference
        "fk_parent",        # Parent FK variations
        "organizational_unit",  # Org hierarchy reference
    }

    def classify(self, entity: Entity) -> Tuple[List[Field], List[Field]]:
        """
        Classify entity fields into node and info categories.

        Node fields (go in tb_{entity}):
        - Self-referencing parent field
        - Trinity pattern fields (auto-added, not from user)
        - Path field (auto-added for hierarchical)
        - Audit fields (auto-added)

        Info fields (go in tb_{entity}_info):
        - All other user-defined fields

        Returns:
            (node_fields, info_fields)
        """
        if not entity.metadata_split:
            raise ValueError("classify() only applies to metadata_split entities")

        node_fields = []
        info_fields = []

        for field in entity.fields:
            if self._is_node_field(field, entity):
                node_fields.append(field)
            else:
                info_fields.append(field)

        return node_fields, info_fields

    def _is_node_field(self, field: Field, entity: Entity) -> bool:
        """Determine if field belongs in node table"""

        # Self-reference (parent field)
        if field.field_type.is_self_reference:
            return True

        # Known node field patterns
        if field.name.lower() in self.NODE_FIELD_PATTERNS:
            return True

        # Everything else is info
        return False

# Update SchemaGenerator
class SchemaGenerator:
    def __init__(self):
        self.field_classifier = FieldClassifier()
        self.ltree_gen = LtreeGenerator()
```

**Run test**: `uv run pytest tests/unit/schema/test_field_classification.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Support explicit classification
```python
# Allow users to explicitly mark fields as node/info

@dataclass
class Field:
    name: str
    field_type: FieldType
    required: bool = True
    table_placement: Optional[str] = None  # NEW: "node", "info", or None (auto)

# In YAML:
# fields:
#   created_by:
#     type: ref(User)
#     table: node  # Explicitly in node table
```

---

**QA**: Test edge cases
```python
def test_classify_all_info_fields():
    """Entity with no user node fields should have all in info table"""
    entity = Entity(
        name="Location",
        is_hierarchical=True,
        metadata_split=True,
        fields=[
            Field(name="name", field_type=FieldType(base_type="text")),
            Field(name="description", field_type=FieldType(base_type="text")),
        ]
    )

    classifier = FieldClassifier()
    node_fields, info_fields = classifier.classify(entity)

    assert len(node_fields) == 0  # No user-defined node fields
    assert len(info_fields) == 2

def test_classify_with_explicit_placement():
    """Should respect explicit table placement"""
    entity = Entity(
        name="Location",
        is_hierarchical=True,
        metadata_split=True,
        fields=[
            Field(name="created_by", field_type=FieldType(base_type="uuid"),
                  table_placement="node"),  # Force into node table
            Field(name="name", field_type=FieldType(base_type="text")),
        ]
    )

    classifier = FieldClassifier()
    node_fields, info_fields = classifier.classify(entity)

    assert any(f.name == "created_by" for f in node_fields)
    assert len(info_fields) == 1
```

---

### PHASE 3: Generate Node and Info Tables

**Objective**: Generate both `tb_{entity}` and `tb_{entity}_info` tables

**Duration**: 5 days

#### TDD Cycle 3.1: Generate Node Table

**RED**: Write failing test
```python
# tests/unit/schema/test_node_info_generation.py

def test_generate_node_table():
    """Should generate node table with structural fields only"""
    entity = Entity(
        name="Location",
        schema="management",
        is_hierarchical=True,
        metadata_split=True,
        fields=[
            Field(name="parent", field_type=FieldType(
                base_type="ref",
                ref_entity="Location",
                is_self_reference=True
            )),
            Field(name="name", field_type=FieldType(base_type="text")),
        ]
    )

    generator = SchemaGenerator()
    sql = generator.generate_node_table(entity)

    # Should have trinity pattern
    assert "pk_location INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY" in sql
    assert "id UUID NOT NULL DEFAULT gen_random_uuid()" in sql
    assert "identifier TEXT UNIQUE" in sql

    # Should have LTREE path
    assert "path LTREE NOT NULL" in sql

    # Should have parent FK
    assert "fk_parent_location INTEGER REFERENCES management.tb_location(pk_location)" in sql

    # Should have FK to info table
    assert "fk_location_info INTEGER NOT NULL REFERENCES management.tb_location_info(pk_location_info)" in sql

    # Should NOT have domain fields
    assert "name" not in sql  # Domain field goes in info table

    # Should have audit fields
    assert "created_at" in sql
    assert "updated_at" in sql
```

**Expected failure**: `AttributeError: 'SchemaGenerator' object has no attribute 'generate_node_table'`

---

**GREEN**: Implement node table generation
```python
# src/generators/schema/metadata_split_generator.py

class MetadataSplitGenerator:
    """Generator for node+info two-table pattern"""

    def __init__(self, field_classifier: FieldClassifier):
        self.classifier = field_classifier

    def generate_node_table(self, entity: Entity) -> str:
        """Generate tb_{entity} node table (structure only)"""
        schema = entity.schema
        entity_name = entity.name.lower()
        pk_name = f"pk_{entity_name}"

        node_fields, _ = self.classifier.classify(entity)

        columns = []

        # Trinity pattern
        columns.append(f"    {pk_name} INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY")
        columns.append("    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE")
        columns.append("    identifier TEXT UNIQUE")

        # LTREE path (hierarchical)
        columns.append("    path LTREE NOT NULL")

        # Parent FK (self-reference)
        parent_field = next((f for f in node_fields if f.field_type.is_self_reference), None)
        if parent_field:
            parent_fk = f"fk_{parent_field.name}"
            columns.append(
                f"    {parent_fk} INTEGER REFERENCES {schema}.tb_{entity_name}({pk_name})"
            )

        # FK to info table
        columns.append(
            f"    fk_{entity_name}_info INTEGER NOT NULL "
            f"REFERENCES {schema}.tb_{entity_name}_info(pk_{entity_name}_info)"
        )

        # Audit fields
        columns.append("    created_at TIMESTAMPTZ NOT NULL DEFAULT now()")
        columns.append("    created_by UUID")
        columns.append("    updated_at TIMESTAMPTZ DEFAULT now()")
        columns.append("    updated_by UUID")
        columns.append("    deleted_at TIMESTAMPTZ")

        return f"""
CREATE TABLE {schema}.tb_{entity_name} (
{',\n'.join(columns)}
);
""".strip()

# Update SchemaGenerator
class SchemaGenerator:
    def __init__(self):
        self.field_classifier = FieldClassifier()
        self.metadata_split_gen = MetadataSplitGenerator(self.field_classifier)
        self.ltree_gen = LtreeGenerator()

    def generate_node_table(self, entity: Entity) -> str:
        """Generate node table for metadata split entities"""
        return self.metadata_split_gen.generate_node_table(entity)
```

**Run test**: `uv run pytest tests/unit/schema/test_node_info_generation.py::test_generate_node_table -v`

**Expected**: ✅ PASS

---

#### TDD Cycle 3.2: Generate Info Table

**RED**: Write failing test
```python
def test_generate_info_table():
    """Should generate info table with domain attributes only"""
    entity = Entity(
        name="Location",
        schema="management",
        is_hierarchical=True,
        metadata_split=True,
        fields=[
            Field(name="parent", field_type=FieldType(
                base_type="ref",
                ref_entity="Location",
                is_self_reference=True
            )),
            Field(name="location_type", field_type=FieldType(
                base_type="ref",
                ref_entity="LocationType"
            )),
            Field(name="legal_name", field_type=FieldType(base_type="text")),
            Field(name="tax_id", field_type=FieldType(base_type="text")),
        ]
    )

    generator = SchemaGenerator()
    sql = generator.generate_info_table(entity)

    # Should have trinity pattern
    assert "pk_location_info INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY" in sql
    assert "id UUID" in sql

    # Should have domain attributes
    assert "fk_location_type INTEGER REFERENCES catalog.tb_location_type" in sql
    assert "legal_name TEXT" in sql
    assert "tax_id TEXT" in sql

    # Should NOT have structural fields
    assert "path LTREE" not in sql
    assert "fk_parent_location" not in sql

    # Should have audit fields
    assert "created_at" in sql
    assert "updated_at" in sql
```

---

**GREEN**: Implement info table generation
```python
# src/generators/schema/metadata_split_generator.py

class MetadataSplitGenerator:
    def generate_info_table(self, entity: Entity) -> str:
        """Generate tb_{entity}_info table (domain attributes)"""
        schema = entity.schema
        entity_name = entity.name.lower()
        pk_name = f"pk_{entity_name}_info"

        _, info_fields = self.classifier.classify(entity)

        columns = []

        # Trinity pattern
        columns.append(f"    {pk_name} INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY")
        columns.append("    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE")
        columns.append("    identifier TEXT")

        # Domain attribute columns
        for field in info_fields:
            col_def = self._field_to_column(field, entity)
            columns.append(f"    {col_def}")

        # Audit fields
        columns.append("    created_at TIMESTAMPTZ NOT NULL DEFAULT now()")
        columns.append("    created_by UUID")
        columns.append("    updated_at TIMESTAMPTZ DEFAULT now()")
        columns.append("    updated_by UUID")

        return f"""
CREATE TABLE {schema}.tb_{entity_name}_info (
{',\n'.join(columns)}
);
""".strip()

    def _field_to_column(self, field: Field, entity: Entity) -> str:
        """Convert field to SQL column definition"""
        field_type = field.field_type

        if field_type.base_type == "ref":
            # Foreign key
            ref_table = f"tb_{field_type.ref_entity.lower()}"
            ref_pk = f"pk_{field_type.ref_entity.lower()}"
            # Determine schema (TODO: make this configurable)
            ref_schema = "catalog"  # Default for reference data
            col_name = f"fk_{field.name}"
            return f"{col_name} INTEGER REFERENCES {ref_schema}.{ref_table}({ref_pk})"

        elif field_type.base_type == "text":
            return f"{field.name} TEXT"

        elif field_type.base_type == "integer":
            return f"{field.name} INTEGER"

        # ... other type mappings ...

        else:
            raise ValueError(f"Unsupported field type: {field_type.base_type}")
```

**Run test**: `uv run pytest tests/unit/schema/test_node_info_generation.py::test_generate_info_table -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Extract column generation to shared utility
```python
# src/generators/schema/column_generator.py

class ColumnGenerator:
    """Generate SQL column definitions from Field AST"""

    def generate(self, field: Field, entity: Entity, context: str = "table") -> str:
        """
        Generate SQL column definition.

        Args:
            field: Field from AST
            entity: Parent entity
            context: "table" or "info" (affects FK schema resolution)
        """
        # Centralized column generation logic
        # Used by both regular tables and info tables
        # ... implementation ...
```

---

#### TDD Cycle 3.3: Orchestrate Generation

**RED**: Write failing test
```python
def test_generate_metadata_split_tables():
    """Should generate both node and info tables when metadata_split=true"""
    entity = Entity(
        name="Location",
        schema="management",
        is_hierarchical=True,
        metadata_split=True,
        fields=[...]
    )

    generator = SchemaGenerator()
    sql = generator.generate_table(entity)

    # Should contain both tables
    assert "CREATE TABLE management.tb_location (" in sql
    assert "CREATE TABLE management.tb_location_info (" in sql

    # Node table should come first (info table references it)
    info_pos = sql.index("tb_location_info")
    node_pos = sql.index("CREATE TABLE management.tb_location (")
    assert node_pos < info_pos
```

---

**GREEN**: Update main generate_table method
```python
# src/generators/schema/schema_generator.py

class SchemaGenerator:
    def generate_table(self, entity: Entity) -> str:
        """
        Generate table(s) for entity.

        - If metadata_split=true: generates node + info tables
        - Otherwise: generates single table
        """
        if entity.metadata_split:
            return self._generate_metadata_split_tables(entity)
        else:
            return self._generate_single_table(entity)

    def _generate_metadata_split_tables(self, entity: Entity) -> str:
        """Generate node + info tables"""
        parts = []

        # 1. Info table (no dependencies)
        parts.append(self.metadata_split_gen.generate_info_table(entity))

        # 2. Node table (references info table)
        parts.append(self.metadata_split_gen.generate_node_table(entity))

        # 3. Indexes for both tables
        parts.append(self._generate_metadata_split_indexes(entity))

        # 4. LTREE triggers (node table)
        if entity.is_hierarchical:
            parts.append(self.ltree_gen.generate_path_trigger(entity))

        # 5. Convenience view
        parts.append(self._generate_combined_view(entity))

        return "\n\n".join(parts)

    def _generate_single_table(self, entity: Entity) -> str:
        """Generate regular single table (existing implementation)"""
        # ... existing code ...
```

**Run test**: `uv run pytest tests/unit/schema/test_node_info_generation.py::test_generate_metadata_split_tables -v`

**Expected**: ✅ PASS

---

**QA**: Integration test
```python
# tests/integration/test_metadata_split_tables.py

def test_metadata_split_tables_execute(test_db):
    """Node and info tables should execute without errors"""
    entity = Entity(
        name="Location",
        schema="management",
        is_hierarchical=True,
        metadata_split=True,
        fields=[
            Field(name="parent", field_type=FieldType(
                base_type="ref",
                ref_entity="Location",
                is_self_reference=True
            )),
            Field(name="name", field_type=FieldType(base_type="text")),
        ]
    )

    generator = SchemaGenerator()
    sql = generator.generate_table(entity)

    # Execute SQL
    test_db.execute(sql)

    # Verify both tables exist
    test_db.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'management'
          AND table_name IN ('tb_location', 'tb_location_info')
        ORDER BY table_name
    """)
    tables = [row[0] for row in test_db.fetchall()]
    assert tables == ['tb_location', 'tb_location_info']

    # Verify FK constraint exists
    test_db.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'tb_location'
          AND constraint_type = 'FOREIGN KEY'
          AND constraint_name LIKE '%location_info%'
    """)
    assert test_db.fetchone() is not None
```

---

### PHASE 4: Generate Convenience View

**Objective**: Create `v_{entity}` view that joins node + info for easy querying

**Duration**: 2 days

#### TDD Cycle 4.1: Generate Joined View

**RED**: Write failing test
```python
# tests/unit/schema/test_convenience_view.py

def test_generate_convenience_view():
    """Should generate view that joins node and info tables"""
    entity = Entity(
        name="Location",
        schema="management",
        is_hierarchical=True,
        metadata_split=True,
        fields=[
            Field(name="parent", field_type=FieldType(
                base_type="ref",
                ref_entity="Location",
                is_self_reference=True
            )),
            Field(name="name", field_type=FieldType(base_type="text")),
            Field(name="legal_name", field_type=FieldType(base_type="text")),
        ]
    )

    generator = SchemaGenerator()
    sql = generator._generate_combined_view(entity)

    # Should create view
    assert "CREATE OR REPLACE VIEW management.v_location" in sql

    # Should select from both tables
    assert "FROM management.tb_location n" in sql
    assert "JOIN management.tb_location_info i" in sql
    assert "ON n.fk_location_info = i.pk_location_info" in sql

    # Should expose all fields
    assert "n.pk_location" in sql
    assert "n.id" in sql
    assert "n.path" in sql
    assert "n.fk_parent_location" in sql
    assert "i.name" in sql
    assert "i.legal_name" in sql

    # Should have FraiseQL annotation
    assert "COMMENT ON VIEW management.v_location" in sql
    assert "@fraiseql:type name=Location" in sql
```

**Expected failure**: Method doesn't exist yet

---

**GREEN**: Implement view generation
```python
# src/generators/schema/metadata_split_generator.py

class MetadataSplitGenerator:
    def generate_combined_view(self, entity: Entity) -> str:
        """Generate convenience view joining node + info tables"""
        schema = entity.schema
        entity_name = entity.name.lower()

        node_fields, info_fields = self.classifier.classify(entity)

        # Build SELECT list
        select_columns = []

        # Node table fields
        select_columns.append(f"    n.pk_{entity_name}")
        select_columns.append("    n.id")
        select_columns.append("    n.identifier")
        select_columns.append("    n.path")
        select_columns.append(f"    n.fk_parent_{entity_name} AS parent_id")
        select_columns.append("    n.created_at")
        select_columns.append("    n.created_by")
        select_columns.append("    n.updated_at")
        select_columns.append("    n.updated_by")
        select_columns.append("    n.deleted_at")

        # Info table fields
        for field in info_fields:
            select_columns.append(f"    i.{field.name}")

        select_clause = ",\n".join(select_columns)

        return f"""
CREATE OR REPLACE VIEW {schema}.v_{entity_name} AS
SELECT
{select_clause}
FROM {schema}.tb_{entity_name} n
JOIN {schema}.tb_{entity_name}_info i
    ON n.fk_{entity_name}_info = i.pk_{entity_name}_info
WHERE n.deleted_at IS NULL;  -- Soft delete filter

COMMENT ON VIEW {schema}.v_{entity_name} IS
  '@fraiseql:type name={entity.name},schema={schema}
   Convenience view combining node and info tables';
""".strip()
```

**Run test**: `uv run pytest tests/unit/schema/test_convenience_view.py -v`

**Expected**: ✅ PASS

---

**REFACTOR**: Make view queryable in FraiseQL
```python
# Add field-level annotations

def generate_combined_view(self, entity: Entity) -> str:
    # ... existing code ...

    view_sql = f"""
CREATE OR REPLACE VIEW {schema}.v_{entity_name} AS
SELECT
{select_clause}
FROM {schema}.tb_{entity_name} n
JOIN {schema}.tb_{entity_name}_info i
    ON n.fk_{entity_name}_info = i.pk_{entity_name}_info
WHERE n.deleted_at IS NULL;
"""

    # Add table-level comment
    comments = [f"""
COMMENT ON VIEW {schema}.v_{entity_name} IS
  '@fraiseql:type name={entity.name},schema={schema}';
"""]

    # Add column-level comments for GraphQL field mapping
    for field in info_fields:
        field_type = self._map_graphql_type(field.field_type)
        comments.append(f"""
COMMENT ON COLUMN {schema}.v_{entity_name}.{field.name} IS
  '@fraiseql:field name={field.name},type={field_type}';
""")

    return view_sql + "\n" + "\n".join(comments)
```

---

**QA**: Test view queries
```python
# tests/integration/test_convenience_view_queries.py

def test_query_through_convenience_view(test_db):
    """Should be able to query node+info through view"""

    # Setup tables and view
    entity = Entity(...)
    generator = SchemaGenerator()
    test_db.execute(generator.generate_table(entity))

    # Insert info record
    test_db.execute("""
        INSERT INTO management.tb_location_info (id, identifier, name, legal_name)
        VALUES (gen_random_uuid(), 'usa-info', 'United States', 'United States of America')
        RETURNING pk_location_info
    """)
    info_pk = test_db.fetchone()[0]

    # Insert node record
    test_db.execute(f"""
        INSERT INTO management.tb_location
        (id, identifier, path, fk_parent_location, fk_location_info)
        VALUES (gen_random_uuid(), 'USA', 'USA', NULL, {info_pk})
        RETURNING pk_location
    """)

    # Query through view
    test_db.execute("""
        SELECT identifier, name, legal_name, path::text
        FROM management.v_location
        WHERE identifier = 'USA'
    """)

    result = test_db.fetchone()
    assert result[0] == 'USA'           # identifier (from node)
    assert result[1] == 'United States' # name (from info)
    assert result[2] == 'United States of America'  # legal_name (from info)
    assert result[3] == 'USA'           # path (from node)
```

---

### PHASE 5: FraiseQL Integration

**Objective**: Generate proper FraiseQL annotations for both tables and view

**Duration**: 2 days

*(Implementation similar to Team D work - generates @fraiseql comments)*

**Key Aspects**:
- Annotate `v_{entity}` view as primary GraphQL type
- Mark `tb_{entity}` and `tb_{entity}_info` as internal
- Expose node structural fields (path, parent) through GraphQL
- Map info domain fields to GraphQL fields
- Generate mutations that work with both tables

---

## Success Criteria - Pattern 3

- [ ] Parser recognizes `metadata_split: true` flag
- [ ] Field classifier correctly separates node vs info fields
- [ ] `tb_{entity}` node table generated with structural fields only
- [ ] `tb_{entity}_info` table generated with domain attributes
- [ ] Info table created before node table (dependency order)
- [ ] FK from node to info table established
- [ ] LTREE path maintained in node table
- [ ] Convenience view `v_{entity}` joins both tables
- [ ] View exposes all fields (node + info)
- [ ] FraiseQL annotations expose view as primary GraphQL type
- [ ] All tests pass (90%+ coverage)
- [ ] Integration tests verify queries work through view
- [ ] Documentation includes node+info pattern examples

---

## Overall Implementation Timeline

| Week | Pattern | Team | Focus | Deliverables |
|------|---------|------|-------|--------------|
| **1** | Recalcid | B | Foundation types | `recalculation_context` type in migration 000 |
| **2** | Recalcid | A, C | AST + Basic generation | Parse cascade_updates, generate simple recalcid functions |
| **3** | LTREE | B | Detection + Schema | Detect hierarchical entities, generate path columns and triggers |
| **4** | LTREE | B | Helpers + Testing | Generate helper functions, comprehensive testing |
| **5** | Node+Info | A, B | AST + Field classification | Parse metadata_split, classify fields |
| **6** | Node+Info | B | Table generation | Generate both tables + view |

**Total Duration**: 6 weeks (assumes 1 pattern per 2 weeks)

---

## Testing Strategy

### Unit Tests (Per Pattern)
- **Coverage target**: 90%+
- **Test first**: RED → GREEN → REFACTOR → QA cycle
- **Categories**:
  - AST parsing (Team A)
  - SQL generation (Team B)
  - Validation logic
  - Edge cases

### Integration Tests
- **Database**: Real PostgreSQL instance
- **Execute generated SQL**: Verify syntax and execution
- **Data operations**: INSERT, UPDATE, queries
- **Cascade chains**: Verify recalcid propagation
- **Hierarchical queries**: Test LTREE operators
- **View queries**: Test node+info joins

### End-to-End Tests
- **Full pipeline**: SpecQL YAML → SQL → Database → GraphQL
- **FraiseQL introspection**: Verify GraphQL schema generation
- **Performance**: Benchmark hierarchical queries with LTREE
- **Migration**: Test schema evolution scenarios

---

## Documentation Deliverables

### For Each Pattern

1. **Architecture Decision Record (ADR)**
   - Why this pattern?
   - What problem does it solve?
   - Alternatives considered
   - Trade-offs

2. **SpecQL Syntax Guide**
   - How to enable in YAML
   - Examples
   - Best practices

3. **Generated SQL Examples**
   - Before/after comparison
   - Annotated output
   - Performance considerations

4. **GraphQL Integration Guide**
   - FraiseQL annotations
   - Query examples
   - Mutation patterns

5. **Migration Guide**
   - Adding pattern to existing entities
   - Breaking changes
   - Backward compatibility

---

## Risk Mitigation

### Pattern 1: Recalcid
**Risk**: Cascade chains cause infinite loops
**Mitigation**:
- Limit cascade depth
- Add cycle detection
- Comprehensive tests for circular references

### Pattern 2: LTREE
**Risk**: Path updates on node moves are slow
**Mitigation**:
- Benchmark with large trees (10k+ nodes)
- Consider materialized path vs LTREE trade-offs
- Add indexes on common query patterns

### Pattern 3: Node+Info
**Risk**: Confusion about which table to query
**Mitigation**:
- Default to view in documentation
- Clear naming conventions
- FraiseQL exposes only view by default

---

## Next Steps

1. **Review and approve** this implementation plan
2. **Prioritize patterns** - Which to implement first?
3. **Assign teams** - Map to existing Team A/B/C structure
4. **Create epics** - Break into sprint-sized chunks
5. **Begin Phase 1** of highest-priority pattern

Would you like me to:
1. **Start implementing** Pattern 1 (recalcid) immediately?
2. **Create detailed test specifications** for each phase?
3. **Generate example YAML files** showing pattern usage?
4. **Draft ADRs** for architectural decisions?
