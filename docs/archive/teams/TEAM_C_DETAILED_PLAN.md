# Team C: Action Compiler - Detailed Phased TDD Plan

**Mission**: Transform SpecQL action steps → Type-safe PL/pgSQL functions returning FraiseQL-compatible `mutation_result`

**Timeline**: Week 3-4 (10 working days)

**Overall Progress Target**: Transform business logic DSL into production-ready PostgreSQL functions

---

## 🎯 Executive Summary

Team C converts business action steps from the AST into executable PL/pgSQL functions. We follow a disciplined phased TDD approach, building from simple validations to complex multi-step workflows with full FraiseQL integration.

**Key Principles**:
- ✅ Type-safe metadata using PostgreSQL composite types
- ✅ Full object returns (not deltas)
- ✅ Trinity pattern resolution
- ✅ Runtime impact tracking
- ✅ FraiseQL-compatible responses

**Dependencies**:
- **Requires**: Team A's AST (Week 1) ✅
- **Requires**: Team B's schema + `mutation_metadata` types (Week 2)
- **Provides**: PL/pgSQL functions for Team D to annotate (Week 5)

---

## 📋 PHASE 1: Function Scaffolding & Basic Returns

**Duration**: Week 3, Days 1-2 (2 days)
**Objective**: Generate basic PL/pgSQL function structure with simple `mutation_result` returns

### 🔴 RED Phase: Write Failing Tests

**Test File**: `tests/unit/actions/test_basic_scaffolding.py`

```python
def test_generate_basic_function_signature():
    """Test: Generate function with correct signature"""
    action = Action(
        name="create_contact",
        steps=[
            ActionStep(type="insert", entity="Contact")
        ]
    )
    entity = Entity(name="Contact", schema="crm", fields={...})

    sql = ActionCompiler().compile_action(action, entity)

    # Expected: function exists with proper signature
    assert "CREATE OR REPLACE FUNCTION crm.create_contact(" in sql
    assert "RETURNS mutation_result AS $$" in sql
    assert "LANGUAGE plpgsql" in sql


def test_generate_function_parameters():
    """Test: Generate parameters from field inputs"""
    action = Action(name="create_contact", steps=[...])
    entity = Entity(
        name="Contact",
        fields={
            "email": FieldDefinition(name="email", type="text"),
            "company": FieldDefinition(name="company", type="ref", target_entity="Company")
        }
    )

    sql = ActionCompiler().compile_action(action, entity)

    # Expected: UUID parameters for ref fields, native types for others
    assert "p_email TEXT" in sql
    assert "p_company_id UUID" in sql
    assert "p_caller_id UUID DEFAULT NULL" in sql  # Auto-added caller context


def test_basic_success_response():
    """Test: Generate basic success response structure"""
    action = Action(
        name="create_contact",
        steps=[ActionStep(type="insert", entity="Contact")]
    )

    sql = ActionCompiler().compile_action(action, entity)

    # Expected: mutation_result structure
    assert "v_result mutation_result;" in sql
    assert "v_result.status := 'success';" in sql
    assert "v_result.message :=" in sql
    assert "v_result.object_data :=" in sql
    assert "RETURN v_result;" in sql


def test_trinity_resolution_for_update_action():
    """Test: Auto-generate Trinity resolution for actions needing pk"""
    action = Action(
        name="update_contact",
        steps=[ActionStep(type="update", entity="Contact")]
    )

    sql = ActionCompiler().compile_action(action, entity)

    # Expected: Trinity helper call
    assert "v_pk INTEGER;" in sql
    assert "v_pk := crm.contact_pk(p_contact_id);" in sql
```

**Run Tests**:
```bash
uv run pytest tests/unit/actions/test_basic_scaffolding.py -v
# Expected: FAILED (not implemented)
```

### 🟢 GREEN Phase: Minimal Implementation

**Implementation File**: `src/generators/actions/action_compiler.py`

```python
from dataclasses import dataclass
from typing import List
from src.core.ast_models import Action, Entity, ActionStep

@dataclass
class ActionCompiler:
    """Compiles SpecQL actions to PL/pgSQL functions"""

    def compile_action(self, action: Action, entity: Entity) -> str:
        """Generate PL/pgSQL function from action definition"""
        schema = entity.schema
        function_name = f"{schema}.{action.name}"

        # Generate parameters
        params = self._generate_parameters(entity, action)

        # Generate function body
        body = self._generate_basic_body(action, entity)

        return f"""
CREATE OR REPLACE FUNCTION {function_name}(
    {', '.join(params)}
)
RETURNS mutation_result AS $$
DECLARE
    v_result mutation_result;
    {self._generate_declarations(action, entity)}
BEGIN
    {body}
END;
$$ LANGUAGE plpgsql;
"""

    def _generate_parameters(self, entity: Entity, action: Action) -> List[str]:
        """Generate function parameters"""
        params = []

        # For update/delete actions, need entity ID
        if self._needs_entity_id(action):
            params.append(f"p_{entity.name.lower()}_id UUID")

        # For create/update, add field parameters
        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref":
                params.append(f"p_{field_name}_id UUID DEFAULT NULL")
            else:
                pg_type = self._map_type(field_def.type)
                params.append(f"p_{field_name} {pg_type} DEFAULT NULL")

        # Always add caller context
        params.append("p_caller_id UUID DEFAULT NULL")

        return params

    def _generate_declarations(self, action: Action, entity: Entity) -> str:
        """Generate DECLARE block variables"""
        declarations = []

        if self._needs_entity_id(action):
            declarations.append("v_pk INTEGER;")

        return "\n    ".join(declarations)

    def _generate_basic_body(self, action: Action, entity: Entity) -> str:
        """Generate minimal function body"""
        parts = []

        # Trinity resolution if needed
        if self._needs_entity_id(action):
            parts.append(f"v_pk := {entity.schema}.{entity.name.lower()}_pk(p_{entity.name.lower()}_id);")

        # Basic success response
        parts.append("""
    -- Basic success response
    v_result.status := 'success';
    v_result.message := 'Operation completed';
    v_result.object_data := '{}'::jsonb;

    RETURN v_result;
""")

        return "\n    ".join(parts)

    def _needs_entity_id(self, action: Action) -> bool:
        """Check if action operates on existing entity"""
        return any(
            step.type in ("update", "delete", "validate")
            for step in action.steps
        )

    def _map_type(self, specql_type: str) -> str:
        """Map SpecQL types to PostgreSQL types"""
        mapping = {
            "text": "TEXT",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "timestamp": "TIMESTAMPTZ",
            "date": "DATE",
            "jsonb": "JSONB",
            "uuid": "UUID"
        }
        return mapping.get(specql_type, "TEXT")
```

**Run Tests**:
```bash
uv run pytest tests/unit/actions/test_basic_scaffolding.py -v
# Expected: PASSED
```

### 🔧 REFACTOR Phase: Clean Up

**Improvements**:
1. Extract parameter generation to separate class
2. Add type hints everywhere
3. Improve readability with constants
4. Add comprehensive docstrings

```python
# Refactored version
from typing import List, Dict
from enum import Enum

class PostgreSQLType(Enum):
    """PostgreSQL type mappings"""
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    TIMESTAMPTZ = "TIMESTAMPTZ"
    DATE = "DATE"
    JSONB = "JSONB"
    UUID = "UUID"

class ParameterGenerator:
    """Generates function parameters from entity fields"""

    def generate(self, entity: Entity, action: Action) -> List[str]:
        """Generate list of parameter declarations"""
        params = []

        if self._requires_entity_id(action):
            params.append(self._entity_id_param(entity))

        params.extend(self._field_params(entity))
        params.append(self._caller_context_param())

        return params

    def _entity_id_param(self, entity: Entity) -> str:
        """Generate entity ID parameter for update/delete"""
        return f"p_{entity.name.lower()}_id UUID"

    def _field_params(self, entity: Entity) -> List[str]:
        """Generate parameters for entity fields"""
        # ... implementation

    def _caller_context_param(self) -> str:
        """Generate caller context parameter (always added)"""
        return "p_caller_id UUID DEFAULT NULL"
```

**Run Tests Again**:
```bash
uv run pytest tests/unit/actions/ -v
# Expected: All PASSED
```

### ✅ QA Phase: Quality Verification

```bash
# Full test suite
uv run pytest --tb=short

# Type checking
uv run mypy src/generators/actions/

# Linting
uv run ruff check src/generators/actions/

# Coverage
uv run pytest --cov=src/generators/actions/ --cov-report=term-missing
# Target: 90%+ coverage
```

**Acceptance Criteria**:
- ✅ Generates valid PL/pgSQL function signatures
- ✅ Includes correct parameters based on entity fields
- ✅ Returns `mutation_result` type
- ✅ Includes Trinity resolution when needed
- ✅ All tests pass
- ✅ 90%+ code coverage

---

## 📋 PHASE 2: Validation Step Compilation

**Duration**: Week 3, Days 3-4 (2 days)
**Objective**: Compile `validate:` steps into PL/pgSQL validation logic with proper error handling

### 🔴 RED Phase: Write Failing Tests

**Test File**: `tests/unit/actions/test_validation_steps.py`

```python
def test_simple_equality_validation():
    """Test: Compile simple equality validation"""
    step = ActionStep(
        type="validate",
        expression="status = 'lead'",
        error="not_a_lead"
    )

    sql = ValidationStepCompiler().compile(step, entity)

    # Expected: IF NOT validation THEN error response
    assert "IF NOT (status = 'lead') THEN" in sql
    assert "v_result.status := 'error';" in sql
    assert "v_result.message := 'not_a_lead';" in sql
    assert "RETURN v_result;" in sql


def test_null_check_validation():
    """Test: Compile NULL validation"""
    step = ActionStep(
        type="validate",
        expression="email IS NOT NULL",
        error="email_required"
    )

    sql = ValidationStepCompiler().compile(step, entity)

    assert "IF NOT (email IS NOT NULL) THEN" in sql
    assert "'email_required'" in sql


def test_pattern_match_validation():
    """Test: Compile regex pattern validation"""
    step = ActionStep(
        type="validate",
        expression="email MATCHES email_pattern",
        error="invalid_email"
    )

    sql = ValidationStepCompiler().compile(step, entity)

    # Expected: PostgreSQL regex operator
    assert "IF NOT (email ~ '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}') THEN" in sql


def test_exists_query_validation():
    """Test: Compile EXISTS subquery validation"""
    step = ActionStep(
        type="validate",
        expression="NOT EXISTS Contact WHERE email = input.email",
        error="duplicate_email"
    )

    sql = ValidationStepCompiler().compile(step, entity)

    # Expected: Subquery in validation
    assert "IF NOT (NOT EXISTS (SELECT 1 FROM crm.tb_contact" in sql
    assert "WHERE email = p_email" in sql
```

**Run Tests**:
```bash
uv run pytest tests/unit/actions/test_validation_steps.py -v
# Expected: FAILED (not implemented)
```

### 🟢 GREEN Phase: Minimal Implementation

**Implementation File**: `src/generators/actions/validation_step_compiler.py`

```python
import re
from dataclasses import dataclass
from src.core.ast_models import ActionStep, Entity

@dataclass
class ValidationStepCompiler:
    """Compiles validation steps to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: Entity) -> str:
        """Generate validation SQL from step"""
        expression = step.expression
        error_code = step.error

        # Transform expression to SQL
        sql_expr = self._transform_expression(expression, entity)

        return f"""
    -- Validation: {expression}
    IF NOT ({sql_expr}) THEN
        v_result.status := 'error';
        v_result.message := '{error_code}';
        v_result.object_data := '{{}}'::jsonb;
        RETURN v_result;
    END IF;
"""

    def _transform_expression(self, expr: str, entity: Entity) -> str:
        """Transform SpecQL expression to PostgreSQL SQL"""

        # Handle MATCHES (regex)
        if "MATCHES" in expr:
            return self._transform_pattern_match(expr)

        # Handle EXISTS
        if "EXISTS" in expr:
            return self._transform_exists(expr, entity)

        # Handle field references (replace with parameter names)
        expr = self._replace_field_refs(expr, entity)

        return expr

    def _transform_pattern_match(self, expr: str) -> str:
        """Transform MATCHES to PostgreSQL regex operator"""
        # Example: "email MATCHES email_pattern" → "email ~ '[pattern]'"
        match = re.match(r"(\w+)\s+MATCHES\s+(\w+)", expr)
        if match:
            field, pattern_name = match.groups()
            pattern = self._get_pattern(pattern_name)
            return f"{field} ~ '{pattern}'"
        return expr

    def _transform_exists(self, expr: str, entity: Entity) -> str:
        """Transform EXISTS query to PostgreSQL"""
        # Example: "NOT EXISTS Contact WHERE email = input.email"
        # → "NOT EXISTS (SELECT 1 FROM crm.tb_contact WHERE email = p_email)"

        match = re.match(r"(NOT\s+)?EXISTS\s+(\w+)\s+WHERE\s+(.+)", expr)
        if match:
            not_clause, entity_name, where = match.groups()
            not_clause = not_clause or ""

            # Get table name
            table = f"{entity.schema}.tb_{entity_name.lower()}"

            # Transform WHERE clause
            where_sql = self._transform_expression(where, entity)

            return f"{not_clause}EXISTS (SELECT 1 FROM {table} WHERE {where_sql})"

        return expr

    def _replace_field_refs(self, expr: str, entity: Entity) -> str:
        """Replace field references with parameter names"""
        # Replace "input.field" with "p_field"
        expr = re.sub(r"input\.(\w+)", r"p_\1", expr)

        # Replace bare field names with parameters
        for field_name in entity.fields.keys():
            expr = re.sub(rf"\b{field_name}\b", f"p_{field_name}", expr)

        return expr

    def _get_pattern(self, pattern_name: str) -> str:
        """Get regex pattern by name"""
        patterns = {
            "email_pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone_pattern": r"^\+?[1-9]\d{1,14}$"
        }
        return patterns.get(pattern_name, ".*")
```

**Run Tests**:
```bash
uv run pytest tests/unit/actions/test_validation_steps.py -v
# Expected: PASSED
```

### 🔧 REFACTOR Phase: Expression Parser

Extract expression transformation into proper parser:

```python
class ExpressionParser:
    """Parses and transforms SpecQL expressions to PostgreSQL SQL"""

    def __init__(self, entity: Entity):
        self.entity = entity

    def parse(self, expr: str) -> str:
        """Parse SpecQL expression to SQL"""
        # Use proper parser pattern
        if self._is_pattern_match(expr):
            return self._parse_pattern_match(expr)

        if self._is_exists_query(expr):
            return self._parse_exists_query(expr)

        if self._is_comparison(expr):
            return self._parse_comparison(expr)

        return self._replace_identifiers(expr)

    # ... cleaner implementation with better separation
```

### ✅ QA Phase

```bash
uv run pytest tests/unit/actions/test_validation_steps.py -v --tb=short
uv run mypy src/generators/actions/validation_step_compiler.py
uv run ruff check src/generators/actions/
```

**Acceptance Criteria**:
- ✅ Simple validations (equality, NULL checks)
- ✅ Pattern matching (MATCHES → regex)
- ✅ EXISTS queries
- ✅ Error responses with correct format
- ✅ All tests pass

---

## 📋 PHASE 3: Insert/Update/Delete Operations

**Duration**: Week 3, Day 5 - Week 4, Day 1 (2 days)
**Objective**: Compile database operations with full object returns

### 🔴 RED Phase

**Test File**: `tests/unit/actions/test_database_operations.py`

```python
def test_insert_operation():
    """Test: Generate INSERT statement with RETURNING"""
    step = ActionStep(type="insert", entity="Contact")
    entity = Entity(name="Contact", schema="crm", fields={...})

    sql = DatabaseOperationCompiler().compile(step, entity)

    # Expected: INSERT with all fields + RETURNING
    assert "INSERT INTO crm.tb_contact" in sql
    assert "email, fk_company, status" in sql
    assert "p_email, crm.company_pk(p_company_id), p_status" in sql
    assert "RETURNING pk_contact INTO v_pk" in sql


def test_update_operation_with_audit():
    """Test: Generate UPDATE with auto-audit fields"""
    step = ActionStep(
        type="update",
        entity="Contact",
        fields={"status": "qualified"}
    )

    sql = DatabaseOperationCompiler().compile(step, entity)

    # Expected: UPDATE with audit fields
    assert "UPDATE crm.tb_contact" in sql
    assert "SET status = 'qualified'" in sql
    assert "updated_at = now()" in sql
    assert "updated_by = p_caller_id" in sql
    assert "WHERE pk_contact = v_pk" in sql


def test_full_object_return_with_relationships():
    """Test: Generate full object query with relationships"""
    step = ActionStep(type="insert", entity="Contact")
    impact = ActionImpact(
        primary=EntityImpact(
            entity="Contact",
            include_relations=["company"]
        )
    )

    sql = DatabaseOperationCompiler().generate_object_return(step, entity, impact)

    # Expected: Full object with company relationship
    assert "SELECT jsonb_build_object(" in sql
    assert "'__typename', 'Contact'" in sql
    assert "'id', c.id" in sql
    assert "'email', c.email" in sql
    assert "'company', jsonb_build_object(" in sql
    assert "'__typename', 'Company'" in sql
    assert "LEFT JOIN management.tb_company co ON co.pk_company = c.fk_company" in sql
```

### 🟢 GREEN Phase

```python
class DatabaseOperationCompiler:
    """Compiles database operation steps"""

    def compile_insert(self, step: ActionStep, entity: Entity) -> str:
        """Generate INSERT statement"""
        table = entity.get_table_name()

        # Get field columns (exclude Trinity pattern fields - auto-generated)
        field_cols = []
        field_vals = []

        for field_name, field_def in entity.fields.items():
            col_name = f"fk_{field_name}" if field_def.type == "ref" else field_name
            field_cols.append(col_name)

            if field_def.type == "ref":
                # Resolve ref to pk
                target = field_def.target_entity
                field_vals.append(f"{entity.schema}.{target.lower()}_pk(p_{field_name}_id)")
            else:
                field_vals.append(f"p_{field_name}")

        # Add audit fields
        field_cols.extend(["created_at", "created_by"])
        field_vals.extend(["now()", "p_caller_id"])

        return f"""
    -- Insert {entity.name}
    INSERT INTO {entity.schema}.{table} (
        {', '.join(field_cols)}
    ) VALUES (
        {', '.join(field_vals)}
    ) RETURNING pk_{entity.name.lower()} INTO v_pk;
"""

    def compile_update(self, step: ActionStep, entity: Entity) -> str:
        """Generate UPDATE statement"""
        set_clauses = []

        # User-specified fields
        for field_name, value in (step.fields or {}).items():
            set_clauses.append(f"{field_name} = {self._format_value(value)}")

        # Auto-audit fields
        set_clauses.extend([
            "updated_at = now()",
            "updated_by = p_caller_id"
        ])

        return f"""
    -- Update {entity.name}
    UPDATE {entity.schema}.{entity.get_table_name()}
    SET {', '.join(set_clauses)}
    WHERE pk_{entity.name.lower()} = v_pk;
"""

    def generate_object_return(
        self,
        step: ActionStep,
        entity: Entity,
        impact: Optional[ActionImpact] = None
    ) -> str:
        """Generate full object return with relationships"""

        # Build field list
        fields = []
        joins = []

        # __typename (for Apollo cache)
        fields.append(f"'__typename', '{entity.name}'")

        # Primary fields
        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref":
                # Handle relationship
                if impact and field_name in (impact.primary.include_relations or []):
                    target = field_def.target_entity
                    fields.append(f"'{field_name}', {self._build_relation_object(field_name, target)}")
                    joins.append(self._build_join(field_name, target, entity))
                else:
                    # Just include ID
                    fields.append(f"'{field_name}Id', c.fk_{field_name}")
            else:
                # Regular field
                camel_name = self._to_camel(field_name)
                fields.append(f"'{camel_name}', c.{field_name}")

        # Build query
        join_sql = "\n    ".join(joins) if joins else ""

        return f"""
    -- Return full {entity.name} object
    v_result.object_data := (
        SELECT jsonb_build_object(
            {',\n            '.join(fields)}
        )
        FROM {entity.schema}.{entity.get_table_name()} c
        {join_sql}
        WHERE c.pk_{entity.name.lower()} = v_pk
    );
"""
```

### 🔧 REFACTOR Phase

Extract to cleaner service:

```python
class ObjectBuilder:
    """Builds full GraphQL-compatible object responses"""

    def build_object_query(
        self,
        entity: Entity,
        include_relations: List[str] = None
    ) -> str:
        """Build SELECT query for full object"""
        # Proper builder pattern with better organization
```

### ✅ QA Phase

```bash
uv run pytest tests/unit/actions/test_database_operations.py -v
uv run pytest --cov=src/generators/actions/
```

**Acceptance Criteria**:
- ✅ INSERT with RETURNING
- ✅ UPDATE with audit fields
- ✅ Full object returns (not deltas)
- ✅ Relationship inclusion
- ✅ `__typename` for cache normalization

---

## 📋 PHASE 4: Conditional Logic (if/then/else, switch)

**Duration**: Week 4, Days 2-3 (2 days)
**Objective**: Compile conditional steps into PL/pgSQL control flow

### 🔴 RED Phase

```python
def test_if_then_simple():
    """Test: Compile simple if/then"""
    step = ActionStep(
        type="if",
        condition="status = 'lead'",
        then_steps=[
            ActionStep(type="update", entity="Contact", fields={"status": "qualified"})
        ]
    )

    sql = ConditionalCompiler().compile(step, entity)

    assert "IF (status = 'lead') THEN" in sql
    assert "UPDATE crm.tb_contact" in sql
    assert "END IF;" in sql


def test_if_then_else():
    """Test: Compile if/then/else"""
    step = ActionStep(
        type="if",
        condition="lead_score >= 70",
        then_steps=[ActionStep(type="update", fields={"status": "qualified"})],
        else_steps=[ActionStep(type="update", fields={"status": "nurture"})]
    )

    sql = ConditionalCompiler().compile(step, entity)

    assert "IF (lead_score >= 70) THEN" in sql
    assert "ELSE" in sql
    assert "END IF;" in sql


def test_switch_statement():
    """Test: Compile switch/case"""
    step = ActionStep(
        type="switch",
        expression="source_type",
        cases={
            "Product": [ActionStep(type="insert", ...)],
            "ContractItem": [ActionStep(type="call", ...)]
        }
    )

    sql = ConditionalCompiler().compile(step, entity)

    assert "CASE source_type" in sql
    assert "WHEN 'Product' THEN" in sql
    assert "WHEN 'ContractItem' THEN" in sql
    assert "END CASE;" in sql
```

### 🟢 GREEN Phase

```python
class ConditionalCompiler:
    """Compiles conditional control flow"""

    def compile(self, step: ActionStep, entity: Entity) -> str:
        """Compile conditional step"""
        if step.type == "if":
            return self._compile_if(step, entity)
        elif step.type == "switch":
            return self._compile_switch(step, entity)
        return ""

    def _compile_if(self, step: ActionStep, entity: Entity) -> str:
        """Compile if/then/else"""
        condition = ExpressionParser(entity).parse(step.condition)

        then_body = self._compile_steps(step.then_steps, entity)
        else_body = self._compile_steps(step.else_steps, entity) if step.else_steps else ""

        sql = f"""
    IF ({condition}) THEN
        {then_body}
"""
        if else_body:
            sql += f"""
    ELSE
        {else_body}
"""
        sql += """
    END IF;
"""
        return sql

    def _compile_switch(self, step: ActionStep, entity: Entity) -> str:
        """Compile switch/case"""
        expr = step.expression

        cases = []
        for value, case_steps in step.cases.items():
            body = self._compile_steps(case_steps, entity)
            cases.append(f"""
        WHEN '{value}' THEN
            {body}
""")

        return f"""
    CASE {expr}
        {'\n'.join(cases)}
    END CASE;
"""

    def _compile_steps(self, steps: List[ActionStep], entity: Entity) -> str:
        """Compile list of steps"""
        # Recursive compilation
        compiled = []
        for step in steps:
            if step.type == "validate":
                compiled.append(ValidationStepCompiler().compile(step, entity))
            elif step.type in ("insert", "update", "delete"):
                compiled.append(DatabaseOperationCompiler().compile(step, entity))
            elif step.type in ("if", "switch"):
                compiled.append(self.compile(step, entity))
        return "\n".join(compiled)
```

### ✅ QA Phase

**Acceptance Criteria**:
- ✅ if/then/else compilation
- ✅ Nested conditionals
- ✅ switch/case statements
- ✅ Proper indentation

---

## 📋 PHASE 5: Impact Metadata with Composite Types

**Duration**: Week 4, Days 4-5 (2 days)
**Objective**: Generate type-safe impact metadata using PostgreSQL composite types

### 🔴 RED Phase

```python
def test_impact_metadata_declaration():
    """Test: Declare impact metadata variable"""
    action = Action(
        name="qualify_lead",
        impact=ActionImpact(
            primary=EntityImpact(entity="Contact", operation="UPDATE")
        )
    )

    sql = ImpactMetadataCompiler().compile(action, entity)

    # Expected: Type-safe declaration
    assert "v_meta mutation_metadata.mutation_impact_metadata;" in sql


def test_primary_impact_construction():
    """Test: Build primary entity impact"""
    impact = ActionImpact(
        primary=EntityImpact(
            entity="Contact",
            operation="UPDATE",
            fields=["status", "updated_at"]
        )
    )

    sql = ImpactMetadataCompiler().build_primary_impact(impact)

    # Expected: ROW constructor with type cast
    assert "v_meta.primary_entity := ROW(" in sql
    assert "'Contact'" in sql
    assert "'UPDATE'" in sql
    assert "ARRAY['status', 'updated_at']" in sql
    assert ")::mutation_metadata.entity_impact;" in sql


def test_side_effects_array():
    """Test: Build side effects array"""
    impact = ActionImpact(
        side_effects=[
            EntityImpact(entity="Notification", operation="CREATE", fields=["id", "message"])
        ]
    )

    sql = ImpactMetadataCompiler().build_side_effects(impact)

    # Expected: Array of entity_impact
    assert "v_meta.actual_side_effects := ARRAY[" in sql
    assert "ROW(" in sql
    assert "'Notification'" in sql
    assert "'CREATE'" in sql
    assert "::mutation_metadata.entity_impact" in sql


def test_cache_invalidations():
    """Test: Build cache invalidation array"""
    impact = ActionImpact(
        cache_invalidations=[
            CacheInvalidation(
                query="contacts",
                filter={"status": "lead"},
                strategy="REFETCH",
                reason="Contact removed from lead list"
            )
        ]
    )

    sql = ImpactMetadataCompiler().build_cache_invalidations(impact)

    # Expected: Array of cache_invalidation composite type
    assert "v_meta.cache_invalidations := ARRAY[" in sql
    assert "ROW(" in sql
    assert "'contacts'" in sql
    assert '\'{"status": "lead"}\'::jsonb' in sql
    assert "'REFETCH'" in sql
    assert "::mutation_metadata.cache_invalidation" in sql


def test_full_metadata_integration():
    """Test: Full metadata in extra_metadata field"""
    action = Action(
        name="qualify_lead",
        impact=ActionImpact(
            primary=EntityImpact(entity="Contact", operation="UPDATE"),
            side_effects=[...],
            cache_invalidations=[...]
        )
    )

    sql = ActionCompiler().compile_action(action, entity)

    # Expected: _meta in extra_metadata
    assert "v_result.extra_metadata := jsonb_build_object(" in sql
    assert "'_meta', to_jsonb(v_meta)" in sql
```

### 🟢 GREEN Phase

```python
class ImpactMetadataCompiler:
    """Compiles impact metadata using composite types"""

    def compile(self, action: Action, entity: Entity) -> str:
        """Generate impact metadata construction"""
        if not action.impact:
            return ""

        impact = action.impact

        parts = []

        # Primary entity
        parts.append(self.build_primary_impact(impact))

        # Side effects
        if impact.side_effects:
            parts.append(self.build_side_effects(impact))

        # Cache invalidations
        if impact.cache_invalidations:
            parts.append(self.build_cache_invalidations(impact))

        return "\n    ".join(parts)

    def build_primary_impact(self, impact: ActionImpact) -> str:
        """Build primary entity impact (type-safe)"""
        primary = impact.primary

        return f"""
    -- Build primary entity impact (type-safe)
    v_meta.primary_entity := ROW(
        '{primary.entity}',                          -- entity_type
        '{primary.operation}',                       -- operation
        ARRAY{primary.fields}::TEXT[]                -- modified_fields
    )::mutation_metadata.entity_impact;
"""

    def build_side_effects(self, impact: ActionImpact) -> str:
        """Build side effects array"""
        rows = []

        for effect in impact.side_effects:
            rows.append(f"""
        ROW(
            '{effect.entity}',
            '{effect.operation}',
            ARRAY{effect.fields}::TEXT[]
        )::mutation_metadata.entity_impact
""")

        return f"""
    -- Build side effects array
    v_meta.actual_side_effects := ARRAY[
        {','.join(rows)}
    ];
"""

    def build_cache_invalidations(self, impact: ActionImpact) -> str:
        """Build cache invalidation array"""
        rows = []

        for inv in impact.cache_invalidations:
            filter_json = json.dumps(inv.filter) if inv.filter else "null"

            rows.append(f"""
        ROW(
            '{inv.query}',                      -- query_name
            '{filter_json}'::jsonb,             -- filter_json
            '{inv.strategy}',                   -- strategy
            '{inv.reason}'                      -- reason
        )::mutation_metadata.cache_invalidation
""")

        return f"""
    -- Build cache invalidations
    v_meta.cache_invalidations := ARRAY[
        {','.join(rows)}
    ];
"""

    def integrate_into_result(self, action: Action) -> str:
        """Integrate metadata into mutation_result.extra_metadata"""
        if not action.impact:
            return "v_result.extra_metadata := '{}'::jsonb;"

        # Build extra_metadata with side effects + _meta
        parts = []

        # Side effect collections (e.g., createdNotifications)
        for effect in action.impact.side_effects:
            if effect.collection:
                parts.append(f"'{effect.collection}', {self._build_collection_query(effect)}")

        # Add _meta
        parts.append("'_meta', to_jsonb(v_meta)")

        return f"""
    v_result.extra_metadata := jsonb_build_object(
        {',\n        '.join(parts)}
    );
"""
```

### 🔧 REFACTOR Phase

Clean up with better type safety:

```python
from typing import TypedDict

class CompositeTypeBuilder:
    """Type-safe builder for PostgreSQL composite types"""

    def build_entity_impact(
        self,
        entity: str,
        operation: str,
        fields: List[str]
    ) -> str:
        """Build entity_impact composite type"""
        # Validate inputs
        assert operation in ("CREATE", "UPDATE", "DELETE", "UPSERT")

        return f"""ROW(
    '{entity}',
    '{operation}',
    ARRAY{fields}::TEXT[]
)::mutation_metadata.entity_impact"""
```

### ✅ QA Phase

```bash
# Test composite type compilation
uv run pytest tests/unit/actions/test_impact_metadata.py -v

# Integration test: Does PostgreSQL accept the generated SQL?
uv run pytest tests/integration/test_composite_types.py -v

# Type check
uv run mypy src/generators/actions/
```

**Acceptance Criteria**:
- ✅ Type-safe composite type construction
- ✅ Proper `_meta` field in `extra_metadata`
- ✅ Side effects tracked
- ✅ Cache invalidations declared
- ✅ PostgreSQL validates types at compile time
- ✅ Full integration with mutation_result

---

## 📋 PHASE 6: Integration & End-to-End Testing

**Duration**: Week 4, Last Day (1 day)
**Objective**: Verify full pipeline works with actual PostgreSQL + FraiseQL

### Integration Tests

```python
def test_full_contact_qualify_lead_function():
    """Integration: Generate complete qualify_lead function"""
    # Load full Contact entity from YAML
    entity = SpecQLParser().parse("entities/examples/contact_lightweight.yaml")
    action = entity.get_action("qualify_lead")

    # Generate SQL
    sql = ActionCompiler().compile_action(action, entity)

    # Apply to test database
    db.execute(sql)

    # Call function
    result = db.query("""
        SELECT crm.qualify_lead(
            p_contact_id := '...',
            p_caller_id := '...'
        );
    """)

    # Verify structure
    assert result.status == "success"
    assert result.object_data["__typename"] == "Contact"
    assert result.object_data["status"] == "qualified"
    assert result.extra_metadata["_meta"]["primaryEntity"]["entityType"] == "Contact"


def test_fraiseql_discovers_function():
    """Integration: FraiseQL discovers generated function"""
    # Generate + apply SQL
    apply_generated_migration()

    # Run FraiseQL introspection
    schema = run_fraiseql_introspection()

    # Verify mutation exists
    assert "qualifyLead" in schema["mutations"]
    mutation = schema["mutations"]["qualifyLead"]

    # Verify return types
    assert "QualifyLeadSuccess" in mutation["returnType"]
    assert "_meta" in mutation["successFields"]
    assert mutation["successFields"]["_meta"]["type"] == "MutationImpactMetadata"
```

### ✅ Final QA

```bash
# All unit tests
make teamC-test

# Integration tests
uv run pytest tests/integration/actions/ -v

# Full test suite
make test

# Coverage report
uv run pytest --cov=src/generators/actions/ --cov-report=html

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

---

## 🎯 Success Criteria Summary

### By End of Week 3
- ✅ Basic function scaffolding working
- ✅ Validation steps compile correctly
- ✅ INSERT/UPDATE/DELETE operations work
- ✅ Full object returns (not deltas)
- ✅ Conditional logic (if/then/switch)

### By End of Week 4
- ✅ Impact metadata with composite types
- ✅ Side effects tracking
- ✅ Cache invalidation declarations
- ✅ Full FraiseQL compatibility
- ✅ Integration tests passing
- ✅ 90%+ test coverage
- ✅ Ready for Team D (annotation generation)

---

## 📊 Testing Strategy

### Unit Tests (70% of effort)
- Test each step compiler independently
- Mock entity/action objects
- Verify SQL correctness
- Fast execution (< 1s total)

### Integration Tests (20% of effort)
- Apply SQL to real PostgreSQL
- Verify functions execute
- Check return structure
- Moderate speed (~30s total)

### E2E Tests (10% of effort)
- Full SpecQL → SQL → Database → FraiseQL flow
- Verify GraphQL schema generation
- Test real mutations
- Slower (few minutes)

### Coverage Target
- **Unit Tests**: 95%+ coverage
- **Integration Tests**: Critical paths
- **E2E Tests**: Happy path + 2-3 edge cases

---

## 🚨 Risk Mitigation

### Risk: Composite Types Don't Work with FraiseQL
**Mitigation**: Test in Week 2 (Team B responsibility)
**Fallback**: Use plain JSONB temporarily

### Risk: Expression Parser Too Complex
**Mitigation**: Start with simple cases, iterate
**Fallback**: Support subset of expressions initially

### Risk: Performance Issues
**Mitigation**: Benchmark early (Week 4)
**Fallback**: Optimize generated SQL patterns

---

**Team C Ready to Execute!** 🚀

This plan provides clear phases, test-first discipline, and measurable progress milestones. Each phase builds on the previous, ensuring we deliver type-safe, FraiseQL-compatible PL/pgSQL functions that transform 20 lines of YAML into production-ready business logic.
