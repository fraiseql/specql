# Team B Implementation Plan: App/Core Schema Pattern

**Date**: 2025-11-08
**Status**: 🚧 Ready for Implementation
**Priority**: HIGH
**Dependencies**: Team A Complete (✅)
**Estimated Time**: 3-4 days (phased TDD approach)

---

## 🎯 Mission

Transform Team B's schema generator to produce the **App/Core pattern** with:
1. **Composite Type Generation** (`app.type_*_input`)
2. **Standard Output Types** (`app.mutation_result`)
3. **Trinity Pattern Tables** (existing, enhance)
4. **FraiseQL Metadata** for composite types

---

## 📊 Current State Analysis

### What Exists (✅)
- `src/generators/table_generator.py` - Trinity pattern DDL generation
- `src/generators/sql_utils.py` - SQL formatting utilities
- Templates in `templates/sql/` for tables
- Tests in `tests/unit/generators/test_table_generator.py`

### What's Missing (🔴)
- **Composite type generation** for action inputs
- **Standard output type generation** (`app.mutation_result`)
- **Type-level FraiseQL annotations**
- **Integration with action definitions** (needs Team C coordination)

---

## ⚠️ CRITICAL: UUID vs INTEGER - External vs Internal

### The Two Worlds

| Layer | Purpose | Foreign Key Type | Example |
|-------|---------|------------------|---------|
| **Composite Types** (`app.type_*_input`) | External API contract (GraphQL) | **UUID** | `company_id UUID` |
| **Database Tables** (`tb_*`) | Internal storage | **INTEGER** | `fk_company INTEGER` |

### Field Naming Convention

**SpecQL (User writes)**:
```yaml
fields:
  company: ref(Company)  # Just "company"
```

**Composite Type (Team B generates)**:
```sql
CREATE TYPE app.type_create_contact_input AS (
    company_id UUID  -- ✅ Appends "_id", uses UUID
);
```

**Database Table (Team B generates)**:
```sql
CREATE TABLE crm.tb_contact (
    fk_company INTEGER  -- ✅ Prefixes "fk_", uses INTEGER
);
```

**Core Layer Resolution (Team C generates)**:
```sql
-- Convert UUID → INTEGER during INSERT
INSERT INTO crm.tb_contact (fk_company, ...)
VALUES (
    core.company_pk(input_data.company_id),  -- ✅ UUID → INTEGER
    ...
);
```

### Why This Matters

1. **GraphQL API uses UUIDs** - External clients never see INTEGER keys
2. **Database uses INTEGERs** - Efficient joins, smaller indexes
3. **Trinity Pattern** - Every entity has both `pk_* INTEGER` (internal) and `id UUID` (external)
4. **Resolution Functions** - `core.entity_pk(UUID) → INTEGER` converts at query time

---

## 🏗️ Architecture Pattern (Reference)

Based on `docs/architecture/APP_CORE_FUNCTION_PATTERN.md`:

```sql
-- 1. INPUT COMPOSITE TYPE (Team B generates)
-- ⚠️ CRITICAL: Uses UUIDs for external references (GraphQL API contract)
CREATE TYPE app.type_create_contact_input AS (
    email TEXT,
    company_id UUID,      -- ✅ UUID (external API uses UUIDs)
    status TEXT
);

COMMENT ON TYPE app.type_create_contact_input IS
  '@fraiseql:input name=CreateContactInput';

-- 2. OUTPUT COMPOSITE TYPE (Team B generates ONCE)
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB
);

COMMENT ON TYPE app.mutation_result IS
  '@fraiseql:type name=MutationResult';

-- 3. TABLE (Team B existing - Trinity pattern)
-- ⚠️ INTERNAL: Uses INTEGER foreign keys (database internal structure)
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    identifier TEXT UNIQUE,
    email TEXT,
    fk_company INTEGER,  -- ✅ INTEGER (internal FK, not exposed to API)
    status TEXT CHECK (status IN ('lead', 'qualified')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 4. UUID → INTEGER RESOLUTION (Team C handles in core layer)
-- Core layer converts: input_data.company_id (UUID) → core.company_pk(UUID) → INTEGER
-- Example:
--   INSERT INTO crm.tb_contact (fk_company, ...)
--   VALUES (core.company_pk(input_data.company_id), ...)
```

---

## 📋 Implementation Phases (TDD Discipline)

---

### **Phase 1: Composite Type Generator Foundation**

**Objective**: Generate `app.type_*_input` composite types from action definitions

#### 🔴 RED: Write Failing Tests

**Test File**: `tests/unit/generators/test_composite_type_generator.py`

```python
"""Tests for composite type generation (Team B)"""

def test_generate_basic_composite_type():
    """Generate composite type from action with simple fields"""
    # Given: Entity with create action
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(type="text", nullable=False),
            "company": FieldDefinition(type="ref", target_entity="Company", nullable=True),
            "status": FieldDefinition(type="enum", values=["lead", "qualified"], nullable=False)
        },
        actions=[
            Action(
                name="create_contact",
                steps=[...]
            )
        ]
    )

    # When: Generate composite type
    generator = CompositeTypeGenerator()
    sql = generator.generate_input_type(entity, entity.actions[0])

    # Then: Composite type includes all fields
    assert "CREATE TYPE app.type_create_contact_input AS (" in sql
    assert "email TEXT" in sql
    assert "company_id UUID" in sql  # ✅ FK is UUID (external API contract)
    assert "status TEXT" in sql
    # FraiseQL annotation
    assert "COMMENT ON TYPE app.type_create_contact_input IS" in sql
    assert "@fraiseql:input name=CreateContactInput" in sql


def test_generate_composite_type_with_nullable_fields():
    """Nullable fields in composite types"""
    # Given: Action with nullable fields
    entity = Entity(...)

    # When: Generate
    sql = generator.generate_input_type(entity, action)

    # Then: Nullable indicators preserved (via comments or conventions)
    # Note: PostgreSQL composite types don't have NOT NULL
    # We'll use comments to indicate required vs optional
    assert "COMMENT ON COLUMN app.type_create_contact_input.email IS 'Required field'" in sql


def test_generate_composite_type_with_nested_fields():
    """Handle complex field types (arrays, lists)"""
    # Given: Entity with list field
    entity = Entity(
        fields={
            "tags": FieldDefinition(type="list", item_type="text")
        }
    )

    # When: Generate
    sql = generator.generate_input_type(entity, action)

    # Then: Array type used
    assert "tags TEXT[]" in sql


def test_skip_composite_type_for_actions_without_input():
    """Some actions (like delete) may not need input types"""
    # Given: Delete action (only needs ID)
    action = Action(name="delete_contact", steps=[...])

    # When: Generate
    sql = generator.generate_input_type(entity, action)

    # Then: Returns empty or uses standard deletion input type
    assert sql == "" or "type_deletion_input" in sql
```

**Expected Outcome**: All tests FAIL (no `CompositeTypeGenerator` exists yet)

---

#### 🟢 GREEN: Minimal Implementation

**Create**: `src/generators/composite_type_generator.py`

```python
"""
Composite Type Generator (Team B)
Generates PostgreSQL composite types for action inputs
"""

from typing import Dict, List, Optional
from src.core.ast_models import Entity, Action, FieldDefinition


class CompositeTypeGenerator:
    """Generates app.type_*_input composite types from actions"""

    # Field type mappings: SpecQL → PostgreSQL composite type fields
    TYPE_MAPPINGS = {
        "text": "TEXT",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "date": "DATE",
        "timestamp": "TIMESTAMPTZ",
        "uuid": "UUID",
        "json": "JSONB",
        "decimal": "DECIMAL",
    }

    def generate_input_type(self, entity: Entity, action: Action) -> str:
        """
        Generate composite type for action input

        Args:
            entity: Entity containing the action
            action: Action to generate input type for

        Returns:
            SQL for composite type creation
        """
        # Determine fields needed for this action
        fields = self._determine_action_fields(entity, action)

        if not fields:
            return ""  # No input type needed

        type_name = f"type_{action.name}_input"
        graphql_name = self._to_pascal_case(action.name) + "Input"

        # Build field definitions
        field_defs = []
        field_comments = []

        for field_name, field_def in fields.items():
            pg_type = self._map_field_type(field_def)
            field_defs.append(f"    {field_name} {pg_type}")

            # Track nullable info in comments (composite types don't support NOT NULL)
            if not field_def.nullable:
                field_comments.append(
                    f"COMMENT ON COLUMN app.{type_name}.{field_name} IS 'Required field';"
                )

        # Build composite type
        sql_parts = []
        sql_parts.append(f"CREATE TYPE app.{type_name} AS (")
        sql_parts.append(",\n".join(field_defs))
        sql_parts.append(");")

        # FraiseQL annotation
        sql_parts.append(f"\nCOMMENT ON TYPE app.{type_name} IS")
        sql_parts.append(f"  '@fraiseql:input name={graphql_name}';")

        # Field comments
        if field_comments:
            sql_parts.append("\n" + "\n".join(field_comments))

        return "\n".join(sql_parts)

    def _determine_action_fields(self, entity: Entity, action: Action) -> Dict[str, FieldDefinition]:
        """
        Determine which fields are needed for action input

        Strategy:
        - For create actions: all entity fields
        - For update actions: all mutable fields
        - For custom actions: parse action steps to identify referenced fields

        Returns:
            Dict mapping API field name → field definition
            ⚠️ Field names are transformed for external API:
              - "company" (ref) → "company_id" (UUID in composite type)
              - Regular fields keep their names
        """
        # Get base fields
        if action.name.startswith("create"):
            base_fields = entity.fields
        elif action.name.startswith("update"):
            # Exclude audit fields
            base_fields = {k: v for k, v in entity.fields.items()
                          if k not in ["created_at", "created_by"]}
        else:
            # Custom action - analyze steps (TODO: implement step analysis)
            base_fields = entity.fields

        # Transform field names for external API
        api_fields = {}
        for field_name, field_def in base_fields.items():
            if field_def.type == "ref":
                # ref fields: append "_id" for external API
                # "company" → "company_id"
                api_field_name = f"{field_name}_id"
            else:
                # Regular fields: keep name as-is
                api_field_name = field_name

            api_fields[api_field_name] = field_def

        return api_fields

    def _map_field_type(self, field_def: FieldDefinition) -> str:
        """
        Map SpecQL field type to PostgreSQL composite type field

        ⚠️ CRITICAL: Composite types represent EXTERNAL API contract
        - Foreign keys: UUID (not INTEGER - GraphQL uses UUIDs)
        - Core layer handles UUID → INTEGER resolution
        """
        if field_def.type == "ref":
            # ✅ Foreign keys are UUIDs in API input (not INTEGER!)
            # Core layer will resolve UUID → INTEGER when inserting
            return "UUID"
        elif field_def.type == "enum":
            return "TEXT"
        elif field_def.type == "list":
            base_type = self.TYPE_MAPPINGS.get(field_def.item_type, "TEXT")
            return f"{base_type}[]"
        else:
            return self.TYPE_MAPPINGS.get(field_def.type, "TEXT")

    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.capitalize() for word in snake_str.split('_'))
```

**Run Tests**: `uv run pytest tests/unit/generators/test_composite_type_generator.py -v`

**Expected**: Tests PASS (minimal implementation works)

---

#### 🔧 REFACTOR: Enhance and Clean

**Improvements**:
1. Add template-based rendering (use Jinja2 like table generator)
2. Improve field determination logic (parse action steps)
3. Handle UUID vs INTEGER for composite types (FraiseQL introspection needs)
4. Add validation for type name conflicts
5. Support action-specific field subsets

**Create Template**: `templates/sql/composite_type.sql.j2`

```sql
{# Composite Type Template #}
-- ============================================================================
-- INPUT TYPE: {{ type_name }}
-- For action: {{ action_name }}
-- ============================================================================
CREATE TYPE app.{{ type_name }} AS (
{% for field_name, field_def in fields.items() %}
    {{ field_name }} {{ field_def.pg_type }}{{ "," if not loop.last else "" }}
{% endfor %}
);

-- FraiseQL metadata
COMMENT ON TYPE app.{{ type_name }} IS
  '@fraiseql:input name={{ graphql_name }}';

{% if field_comments %}
-- Field metadata
{% for comment in field_comments %}
{{ comment }}
{% endfor %}
{% endif %}
```

**Updated Implementation**: Use template rendering

```python
class CompositeTypeGenerator:
    def __init__(self, templates_dir: str = "templates/sql"):
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate_input_type(self, entity: Entity, action: Action) -> str:
        fields = self._determine_action_fields(entity, action)
        if not fields:
            return ""

        type_name = f"type_{action.name}_input"
        context = {
            "type_name": type_name,
            "action_name": action.name,
            "graphql_name": self._to_pascal_case(action.name) + "Input",
            "fields": self._prepare_fields(fields),
            "field_comments": self._generate_field_comments(type_name, fields)
        }

        template = self.env.get_template("composite_type.sql.j2")
        return template.render(**context)
```

**Run Tests**: All tests still PASS, code is cleaner

---

#### ✅ QA: Quality Verification

```bash
# Full test suite
uv run pytest tests/unit/generators/ -v

# Type checking
uv run mypy src/generators/composite_type_generator.py

# Linting
uv run ruff check src/generators/

# Integration test (with real entity)
uv run pytest tests/integration/test_composite_type_generation.py -v
```

**Acceptance Criteria**:
- ✅ Generates composite types for all action types (create, update, custom)
- ✅ Correctly maps SpecQL types to PostgreSQL types
- ✅ Handles ref → INTEGER conversion
- ✅ Adds FraiseQL annotations
- ✅ All tests pass
- ✅ Code quality checks pass

---

### **Phase 2: Standard Output Type Generation**

**Objective**: Generate `app.mutation_result` once per schema

#### 🔴 RED: Write Test

```python
def test_generate_standard_mutation_result_type():
    """Generate standard mutation_result composite type"""
    # When: Generate
    generator = CompositeTypeGenerator()
    sql = generator.generate_mutation_result_type()

    # Then: Standard structure
    assert "CREATE TYPE app.mutation_result AS (" in sql
    assert "id UUID" in sql
    assert "updated_fields TEXT[]" in sql
    assert "status TEXT" in sql
    assert "message TEXT" in sql
    assert "object_data JSONB" in sql
    assert "extra_metadata JSONB" in sql
    assert "@fraiseql:type name=MutationResult" in sql


def test_mutation_result_generated_only_once():
    """Ensure mutation_result is not duplicated"""
    # Given: Multiple entities
    entities = [Entity(...), Entity(...)]

    # When: Generate for all
    generator = CompositeTypeGenerator()
    results = [generator.generate_common_types() for e in entities]

    # Then: Only first call returns SQL, others return empty
    assert results[0] != ""
    assert all(r == "" for r in results[1:])
```

#### 🟢 GREEN: Implementation

```python
class CompositeTypeGenerator:
    _mutation_result_generated = False  # Class variable to track

    def generate_mutation_result_type(self) -> str:
        """Generate standard mutation_result composite type (once)"""
        if CompositeTypeGenerator._mutation_result_generated:
            return ""

        CompositeTypeGenerator._mutation_result_generated = True

        return """
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB
);

COMMENT ON TYPE app.mutation_result IS
  '@fraiseql:type name=MutationResult';

COMMENT ON COLUMN app.mutation_result.status IS
  'Status: success, failed:*, warning:*';
"""

    def generate_common_types(self) -> str:
        """Generate all common types needed across schema"""
        types = []

        # Mutation result
        result_type = self.generate_mutation_result_type()
        if result_type:
            types.append(result_type)

        # Standard deletion input (if needed)
        types.append(self._generate_deletion_input_type())

        return "\n\n".join(types)
```

#### ✅ QA: Verify

```bash
uv run pytest tests/unit/generators/test_composite_type_generator.py::test_mutation_result -v
```

---

### **Phase 3: Integration with Table Generator**

**Objective**: Coordinate table + type generation for complete schema

#### 🔴 RED: Test

```python
def test_complete_entity_schema_generation():
    """Generate complete schema: tables + types"""
    # Given: Entity with actions
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={...},
        actions=[Action(name="create_contact", ...)]
    )

    # When: Generate complete schema
    orchestrator = SchemaOrchestrator()
    sql = orchestrator.generate_complete_schema(entity)

    # Then: Contains tables + types
    assert "CREATE TABLE crm.tb_contact" in sql
    assert "CREATE TYPE app.type_create_contact_input" in sql
    assert "CREATE TYPE app.mutation_result" in sql
```

#### 🟢 GREEN: Implementation

Create: `src/generators/schema_orchestrator.py`

```python
"""
Schema Orchestrator (Team B)
Coordinates table + type generation
"""

from src.generators.table_generator import TableGenerator
from src.generators.composite_type_generator import CompositeTypeGenerator


class SchemaOrchestrator:
    """Orchestrates complete schema generation"""

    def __init__(self):
        self.table_gen = TableGenerator()
        self.type_gen = CompositeTypeGenerator()

    def generate_complete_schema(self, entity: Entity) -> str:
        """Generate tables + types for entity"""
        parts = []

        # 1. Common types (mutation_result, etc.)
        common_types = self.type_gen.generate_common_types()
        if common_types:
            parts.append("-- Common Types\n" + common_types)

        # 2. Entity table (Trinity pattern)
        table_sql = self.table_gen.generate_table_ddl(entity)
        parts.append("-- Entity Table\n" + table_sql)

        # 3. Input types for actions
        for action in entity.actions:
            input_type = self.type_gen.generate_input_type(entity, action)
            if input_type:
                parts.append(f"-- Input Type: {action.name}\n" + input_type)

        # 4. Indexes
        indexes = self.table_gen.generate_indexes_ddl(entity)
        parts.append("-- Indexes\n" + indexes)

        # 5. Foreign keys
        fks = self.table_gen.generate_foreign_keys_ddl(entity)
        if fks:
            parts.append("-- Foreign Keys\n" + fks)

        return "\n\n".join(parts)
```

---

### **Phase 4: FraiseQL Metadata Enhancement**

**Objective**: Add complete FraiseQL annotations for introspection

#### 🔴 RED: Test

```python
def test_fraiseql_annotations_for_composite_types():
    """Verify FraiseQL can introspect generated types"""
    # Given: Generated composite type
    sql = generator.generate_input_type(entity, action)

    # When: Parse FraiseQL annotations
    annotations = FraiseQLParser.parse_type_annotations(sql)

    # Then: Correct metadata
    assert annotations['type'] == 'input'
    assert annotations['name'] == 'CreateContactInput'
    assert len(annotations['fields']) == 3
```

#### 🟢 GREEN: Enhanced Annotations

Update composite type generator to add field-level metadata:

```python
def _generate_field_annotations(self, type_name: str, fields: Dict[str, FieldDefinition]) -> List[str]:
    """Generate FraiseQL field annotations"""
    annotations = []

    for field_name, field_def in fields.items():
        graphql_type = self._map_to_graphql_type(field_def)

        comment = f"COMMENT ON COLUMN app.{type_name}.{field_name} IS " \
                  f"'@fraiseql:field name={field_name},type={graphql_type}"

        if not field_def.nullable:
            comment += ",required=true"

        comment += "';"
        annotations.append(comment)

    return annotations
```

---

## 🎯 Team B Deliverables

### Code Modules
1. ✅ `src/generators/composite_type_generator.py` - Input type generation
2. ✅ `src/generators/schema_orchestrator.py` - Coordination layer
3. ✅ `templates/sql/composite_type.sql.j2` - Type template
4. ✅ Enhanced `table_generator.py` - Integration hooks

### Tests
1. ✅ `tests/unit/generators/test_composite_type_generator.py` (15+ tests)
2. ✅ `tests/integration/test_schema_orchestration.py` (E2E tests)
3. ✅ Coverage: 90%+ for new code

### Documentation
1. ✅ API docs for `CompositeTypeGenerator`
2. ✅ Examples of generated types
3. ✅ FraiseQL annotation guide

---

## 🔗 Team C Coordination Points

**Team B Provides to Team C**:
1. **Composite type names** for each action (e.g., `app.type_create_contact_input`)
2. **Field mappings** (SpecQL field → composite type field)
3. **Standard output type** (`app.mutation_result`)

**Team C Uses**:
- References composite types in function signatures
- Returns `app.mutation_result` from all mutations
- Maps JSONB payload to composite type in app wrapper

**Interface Contract**:
```python
# Team B generates composite type
composite_type_name = f"app.type_{action.name}_input"

# Team C uses in function signature
def generate_app_wrapper(action: Action):
    return f"""
    CREATE FUNCTION app.{action.name}(
        input_pk_organization UUID,
        input_created_by UUID,
        input_payload JSONB  -- Maps to {composite_type_name}
    ) RETURNS app.mutation_result
    """
```

---

## 📊 Success Metrics

- [ ] ✅ Generate composite types for all action types
- [ ] ✅ Standard `mutation_result` type created once
- [ ] ✅ FraiseQL annotations complete and parseable
- [ ] ✅ Integration with table generation seamless
- [ ] ✅ All tests pass (90%+ coverage)
- [ ] ✅ Team C can reference generated types
- [ ] ✅ Generated SQL matches PrintOptim pattern

---

## 🚀 Getting Started

```bash
# Create branch
git checkout -b feature/team-b-composite-types

# Phase 1: Composite type generation
# 1. Write tests
vim tests/unit/generators/test_composite_type_generator.py

# 2. Run tests (should fail)
uv run pytest tests/unit/generators/test_composite_type_generator.py -v

# 3. Implement
vim src/generators/composite_type_generator.py

# 4. Run tests (should pass)
uv run pytest tests/unit/generators/test_composite_type_generator.py -v

# Continue with Phase 2, 3, 4...
```

---

## 📚 Reference Documents

1. **Architecture**: `docs/architecture/APP_CORE_FUNCTION_PATTERN.md`
2. **Composite Types**: `/tmp/specql-composite-type-input-generation-issue.md`
3. **PrintOptim Example**: `../printoptim_backend/db/0_schema/03_functions/`
4. **Team A AST**: `src/core/ast_models.py`

---

**Last Updated**: 2025-11-08
**Status**: Ready for Development
**Estimated Duration**: 3-4 days (with TDD discipline)
