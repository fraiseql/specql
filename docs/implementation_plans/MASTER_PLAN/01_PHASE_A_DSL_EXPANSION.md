# Track A: DSL Expansion - Implementation Plan

**Duration**: 7 weeks
**Objective**: Expand SpecQL from 15 → 35 primitive actions (Tier 1)
**Team**: Team A (Parser) + Team C (Action Compiler)
**Output**: Universal SQL expression capability (9/10 feasibility)

---

## 🎯 Vision

Transform SpecQL from supporting 21% of reference SQL to 95% by adding 20 new primitive action types that enable expression of:
- Variable declaration and manipulation
- Complex queries (CTEs, aggregates, subqueries)
- Advanced control flow (switch, while, for_query)
- Function composition and early returns
- Data transformation (JSON, arrays, batch operations)

---

## 📊 Current State (15 Actions)

**Existing in `src/core/ast_models.py`**:
1. `validate` - Conditional checks
2. `if` - Conditional branching
3. `insert` - INSERT operations
4. `update` - UPDATE operations
5. `delete` - DELETE operations
6. `call` - Function calls
7. `find` - Query operations
8. `notify` - Notifications
9. `foreach` - Loop over collections
10. `return` - Return values
11. `assign` - Basic variable assignment
12. `let` - Variable binding
13. `transform` - Data transformation
14. `query` - Basic queries
15. `error` - Error handling

**Limitations**:
- No CTEs or complex queries
- No switch/case statements
- No while loops or cursors
- No early returns
- No JSON/array builders
- No batch operations
- No aggregate expressions
- No subqueries

**Coverage**: 21% of reference SQL functions expressible

---

## 🚀 Target State (35 Actions)

**New Actions to Add** (20 total):
1. `declare` - Variable declarations with types
2. `cte` - Common Table Expressions
3. `aggregate` - Aggregation expressions
4. `switch` - Switch/case statements
5. `while` - While loops
6. `for_query` - Iterate over query results
7. `call_function` - Call functions with return values
8. `return_early` - Early return from function
9. `json_build` - Build JSON objects
10. `array_build` - Build arrays
11. `upsert` - INSERT ON CONFLICT UPDATE
12. `batch_operation` - Batch inserts/updates
13. `return_table` - Return table results
14. `cursor` - Cursor operations
15. `exception_handling` - Try/catch blocks
16. `subquery` - Embedded subqueries
17. `window_function` - Window/analytic functions
18. `recursive_cte` - Recursive CTEs
19. `dynamic_sql` - Dynamic SQL generation
20. `transaction_control` - Transaction boundaries

**Coverage**: 95% of reference SQL functions expressible

---

## 📅 7-Week Timeline

### Phase 1: Core Primitives (Weeks 1-3)
**Goal**: Foundation for variable manipulation and queries
- declare, cte, aggregate, call_function, subquery

### Phase 2: Control Flow (Weeks 4-5)
**Goal**: Advanced control structures
- switch, while, for_query, return_early, exception_handling

### Phase 3: Advanced Queries (Weeks 6-7)
**Goal**: Complex data operations
- json_build, array_build, upsert, batch_operation, window_function, return_table, cursor, recursive_cte, dynamic_sql, transaction_control

---

## 🔄 TDD Methodology

Each new action follows RED → GREEN → REFACTOR → QA:

```
┌─────────────────────────────────────────────────────────┐
│ Week N: [Action Types]                                  │
│                                                         │
│ ┌─────────┐  ┌─────────┐  ┌─────────────┐  ┌─────────┐ │
│ │   RED   │─▶│ GREEN   │─▶│  REFACTOR   │─▶│   QA    │ │
│ │ Tests   │  │ AST     │  │ Compiler    │  │ E2E     │ │
│ └─────────┘  └─────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## WEEK 1: declare + cte

### Objective
Enable variable declarations and Common Table Expressions for complex query composition.

---

### 🔴 RED Phase (Days 1-2): Write Failing Tests

#### Test 1: Variable Declaration
**File**: `tests/unit/core/test_declare_action.py`

```python
def test_declare_variable_integer():
    """Test declaring an integer variable"""
    yaml_content = """
    entity: Invoice
    actions:
      - name: calculate_total
        steps:
          - declare:
              name: subtotal
              type: numeric
              default: 0
          - query: subtotal = SUM(amount) FROM tb_line_item WHERE invoice_id = $invoice_id
          - return: subtotal
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[0].type == "declare"
    assert action.steps[0].variable_name == "subtotal"
    assert action.steps[0].variable_type == "numeric"
    assert action.steps[0].default_value == 0

def test_declare_multiple_variables():
    """Test declaring multiple variables"""
    yaml_content = """
    entity: Order
    actions:
      - name: process_order
        steps:
          - declare:
              - name: tax_rate
                type: numeric
                default: 0.0825
              - name: discount_amount
                type: numeric
                default: 0
              - name: final_total
                type: numeric
          - query: final_total = (subtotal * (1 + tax_rate)) - discount_amount
          - return: final_total
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert len(action.steps[0].declarations) == 3
    assert action.steps[0].declarations[0].name == "tax_rate"
```

#### Test 2: Common Table Expression
**File**: `tests/unit/core/test_cte_action.py`

```python
def test_simple_cte():
    """Test simple CTE for query composition"""
    yaml_content = """
    entity: Report
    actions:
      - name: monthly_sales_report
        steps:
          - cte:
              name: monthly_totals
              query: |
                SELECT
                  DATE_TRUNC('month', order_date) AS month,
                  SUM(total_amount) AS monthly_total
                FROM tb_order
                WHERE EXTRACT(YEAR FROM order_date) = $year
                GROUP BY DATE_TRUNC('month', order_date)
          - query: result = SELECT * FROM monthly_totals ORDER BY month
          - return: result
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[0].type == "cte"
    assert action.steps[0].cte_name == "monthly_totals"
    assert "SELECT" in action.steps[0].cte_query

def test_multiple_ctes():
    """Test multiple CTEs with dependencies"""
    yaml_content = """
    entity: Analytics
    actions:
      - name: customer_lifetime_value
        steps:
          - cte:
              name: customer_orders
              query: |
                SELECT customer_id, COUNT(*) as order_count, SUM(total_amount) as total_spent
                FROM tb_order
                GROUP BY customer_id
          - cte:
              name: customer_segments
              query: |
                SELECT
                  customer_id,
                  CASE
                    WHEN total_spent > 10000 THEN 'vip'
                    WHEN total_spent > 1000 THEN 'regular'
                    ELSE 'occasional'
                  END as segment
                FROM customer_orders
          - query: result = SELECT * FROM customer_segments WHERE segment = $segment
          - return: result
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[0].type == "cte"
    assert action.steps[1].type == "cte"
    assert action.steps[0].cte_name == "customer_orders"
    assert action.steps[1].cte_name == "customer_segments"
```

#### Test 3: Integration Test
**File**: `tests/integration/actions/test_declare_cte_compilation.py`

```python
def test_declare_with_cte_compiles_to_plpgsql():
    """Test that declare + cte compiles to valid PL/pgSQL"""
    yaml_content = """
    entity: Invoice
    schema: billing
    actions:
      - name: calculate_invoice_with_discounts
        parameters:
          - name: invoice_id
            type: uuid
        returns: numeric
        steps:
          - declare:
              name: base_total
              type: numeric
              default: 0
          - cte:
              name: line_totals
              query: |
                SELECT line_item_id, quantity * unit_price as line_total
                FROM tb_line_item
                WHERE invoice_id = $invoice_id
          - query: base_total = SELECT SUM(line_total) FROM line_totals
          - return: base_total
    """

    ast = parse_specql(yaml_content)
    sql = compile_action_to_plpgsql(ast.entities[0].actions[0])

    # Should generate valid PL/pgSQL
    assert "CREATE OR REPLACE FUNCTION billing.calculate_invoice_with_discounts" in sql
    assert "DECLARE" in sql
    assert "base_total NUMERIC := 0;" in sql
    assert "WITH line_totals AS (" in sql
    assert "SELECT SUM(line_total) INTO base_total FROM line_totals" in sql
    assert "RETURN base_total;" in sql

    # Should be valid SQL
    execute_sql(sql)  # Should not raise exception
```

**Expected Output**: All tests FAIL (features not implemented)

```bash
uv run pytest tests/unit/core/test_declare_action.py -v
# FAILED: 'declare' step type not recognized

uv run pytest tests/unit/core/test_cte_action.py -v
# FAILED: 'cte' step type not recognized

uv run pytest tests/integration/actions/test_declare_cte_compilation.py -v
# FAILED: Cannot compile unknown step types
```

---

### 🟢 GREEN Phase (Days 3-4): Minimal Implementation

#### Step 1: Extend AST Models
**File**: `src/core/ast_models.py`

```python
@dataclass
class VariableDeclaration:
    """Variable declaration"""
    name: str
    type: str  # numeric, text, boolean, uuid, etc.
    default_value: Any | None = None

@dataclass
class CTEDefinition:
    """Common Table Expression definition"""
    name: str
    query: str
    materialized: bool = False

@dataclass
class ActionStep:
    type: str

    # Existing fields...
    condition: str | None = None
    then_steps: list["ActionStep"] = field(default_factory=list)
    entity: str | None = None
    fields: dict[str, Any] | None = None

    # NEW: declare step
    variable_name: str | None = None
    variable_type: str | None = None
    default_value: Any | None = None
    declarations: list[VariableDeclaration] = field(default_factory=list)

    # NEW: cte step
    cte_name: str | None = None
    cte_query: str | None = None
    cte_materialized: bool = False
```

#### Step 2: Update Parser
**File**: `src/core/parser.py`

```python
def parse_action_step(step_data: dict) -> ActionStep:
    """Parse a single action step"""

    # Existing step types...
    if "validate" in step_data:
        return parse_validate_step(step_data)
    elif "if" in step_data:
        return parse_if_step(step_data)

    # NEW: declare step
    elif "declare" in step_data:
        declare_data = step_data["declare"]

        # Single declaration
        if "name" in declare_data:
            return ActionStep(
                type="declare",
                variable_name=declare_data["name"],
                variable_type=declare_data.get("type", "text"),
                default_value=declare_data.get("default")
            )

        # Multiple declarations
        elif isinstance(declare_data, list):
            declarations = [
                VariableDeclaration(
                    name=decl["name"],
                    type=decl.get("type", "text"),
                    default_value=decl.get("default")
                )
                for decl in declare_data
            ]
            return ActionStep(
                type="declare",
                declarations=declarations
            )

    # NEW: cte step
    elif "cte" in step_data:
        cte_data = step_data["cte"]
        return ActionStep(
            type="cte",
            cte_name=cte_data["name"],
            cte_query=cte_data["query"],
            cte_materialized=cte_data.get("materialized", False)
        )

    else:
        raise ValueError(f"Unknown step type: {step_data}")
```

#### Step 3: Update Action Compiler
**File**: `src/generators/actions/step_compilers/declare_step.py` (NEW)

```python
"""Compiler for declare steps"""

from src.core.ast_models import ActionStep
from src.generators.actions.step_compilers.base import StepCompiler

class DeclareStepCompiler(StepCompiler):
    """Compiles declare steps to PL/pgSQL DECLARE block"""

    def compile(self, step: ActionStep, context: dict) -> str:
        """
        Generate DECLARE statement(s)

        Returns:
            DECLARE block entries (not full block, added to function DECLARE section)
        """
        if step.variable_name:
            # Single declaration
            default = ""
            if step.default_value is not None:
                default = f" := {self._format_value(step.default_value)}"

            pg_type = self._map_type(step.variable_type)
            return f"{step.variable_name} {pg_type}{default};"

        elif step.declarations:
            # Multiple declarations
            lines = []
            for decl in step.declarations:
                default = ""
                if decl.default_value is not None:
                    default = f" := {self._format_value(decl.default_value)}"

                pg_type = self._map_type(decl.type)
                lines.append(f"{decl.name} {pg_type}{default};")

            return "\n".join(lines)

        return ""

    def _map_type(self, specql_type: str) -> str:
        """Map SpecQL types to PostgreSQL types"""
        type_map = {
            "text": "TEXT",
            "integer": "INTEGER",
            "numeric": "NUMERIC",
            "boolean": "BOOLEAN",
            "uuid": "UUID",
            "timestamp": "TIMESTAMPTZ",
            "json": "JSONB"
        }
        return type_map.get(specql_type.lower(), "TEXT")

    def _format_value(self, value: Any) -> str:
        """Format a value for SQL"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        else:
            return str(value)
```

**File**: `src/generators/actions/step_compilers/cte_step.py` (NEW)

```python
"""Compiler for CTE steps"""

from src.core.ast_models import ActionStep
from src.generators.actions.step_compilers.base import StepCompiler

class CTEStepCompiler(StepCompiler):
    """Compiles CTE steps to SQL WITH clauses"""

    def compile(self, step: ActionStep, context: dict) -> str:
        """
        Generate CTE definition

        Returns:
            CTE definition (will be collected and added to WITH clause)
        """
        materialized = ""
        if step.cte_materialized:
            materialized = " MATERIALIZED"

        # Store CTE in context for later use
        if "ctes" not in context:
            context["ctes"] = []

        cte_def = {
            "name": step.cte_name,
            "query": step.cte_query.strip(),
            "materialized": step.cte_materialized
        }
        context["ctes"].append(cte_def)

        # Return empty string (CTEs are added at query level, not inline)
        return ""

    def get_cte_clause(self, context: dict) -> str:
        """Build the WITH clause from collected CTEs"""
        if "ctes" not in context or not context["ctes"]:
            return ""

        cte_definitions = []
        for cte in context["ctes"]:
            materialized = " MATERIALIZED" if cte["materialized"] else ""
            cte_definitions.append(
                f"{cte['name']} AS{materialized} (\n{cte['query']}\n)"
            )

        return "WITH " + ",\n".join(cte_definitions)
```

#### Step 4: Update Action Orchestrator
**File**: `src/generators/actions/action_orchestrator.py`

```python
from src.generators.actions.step_compilers.declare_step import DeclareStepCompiler
from src.generators.actions.step_compilers.cte_step import CTEStepCompiler

class ActionOrchestrator:
    def __init__(self):
        self.step_compilers = {
            "validate": ValidateStepCompiler(),
            "if": IfStepCompiler(),
            "insert": InsertStepCompiler(),
            "update": UpdateStepCompiler(),
            # ... existing compilers

            # NEW
            "declare": DeclareStepCompiler(),
            "cte": CTEStepCompiler(),
        }

    def compile_action(self, action: Action, schema: str) -> str:
        """Compile action to PL/pgSQL function"""

        # Collect DECLARE statements
        declare_block = []
        cte_context = {"ctes": []}
        body_statements = []

        for step in action.steps:
            compiler = self.step_compilers.get(step.type)
            if not compiler:
                raise ValueError(f"No compiler for step type: {step.type}")

            if step.type == "declare":
                declare_sql = compiler.compile(step, {})
                declare_block.append(declare_sql)

            elif step.type == "cte":
                compiler.compile(step, cte_context)  # Stores in context

            else:
                stmt = compiler.compile(step, cte_context)
                body_statements.append(stmt)

        # Build function
        function_parts = [
            f"CREATE OR REPLACE FUNCTION {schema}.{action.name}(",
            self._build_parameters(action.parameters),
            f") RETURNS {action.returns or 'app.mutation_result'}",
            "LANGUAGE plpgsql",
            "AS $$",
        ]

        # Add DECLARE block
        if declare_block:
            function_parts.append("DECLARE")
            function_parts.extend(declare_block)

        function_parts.append("BEGIN")

        # Add WITH clause if CTEs exist
        if cte_context["ctes"]:
            cte_compiler = self.step_compilers["cte"]
            with_clause = cte_compiler.get_cte_clause(cte_context)
            body_statements.insert(0, with_clause)

        function_parts.extend(body_statements)
        function_parts.append("END;")
        function_parts.append("$$;")

        return "\n".join(function_parts)
```

**Expected Output**: Tests PASS

```bash
uv run pytest tests/unit/core/test_declare_action.py -v
# PASSED: 2 tests

uv run pytest tests/unit/core/test_cte_action.py -v
# PASSED: 2 tests

uv run pytest tests/integration/actions/test_declare_cte_compilation.py -v
# PASSED: 1 test
```

---

### 🔧 REFACTOR Phase (Day 5): Clean & Optimize

#### Refactor 1: Extract Type Mapping
**File**: `src/generators/actions/type_mapper.py` (NEW)

```python
"""Centralized type mapping for all step compilers"""

class TypeMapper:
    """Maps SpecQL types to target language types"""

    SPECQL_TO_POSTGRES = {
        "text": "TEXT",
        "integer": "INTEGER",
        "bigint": "BIGINT",
        "numeric": "NUMERIC",
        "decimal": "DECIMAL",
        "boolean": "BOOLEAN",
        "uuid": "UUID",
        "timestamp": "TIMESTAMPTZ",
        "date": "DATE",
        "time": "TIME",
        "json": "JSONB",
        "array": "ARRAY",
    }

    @classmethod
    def to_postgres(cls, specql_type: str) -> str:
        """Convert SpecQL type to PostgreSQL type"""
        return cls.SPECQL_TO_POSTGRES.get(specql_type.lower(), "TEXT")

    @classmethod
    def to_python(cls, specql_type: str) -> str:
        """Convert SpecQL type to Python type hint"""
        type_map = {
            "text": "str",
            "integer": "int",
            "numeric": "Decimal",
            "boolean": "bool",
            "uuid": "UUID",
            "timestamp": "datetime",
            "json": "dict",
        }
        return type_map.get(specql_type.lower(), "Any")
```

Update `declare_step.py` to use `TypeMapper`:

```python
from src.generators.actions.type_mapper import TypeMapper

class DeclareStepCompiler(StepCompiler):
    def compile(self, step: ActionStep, context: dict) -> str:
        # ...
        pg_type = TypeMapper.to_postgres(step.variable_type)
        # ...
```

#### Refactor 2: Context Management
**File**: `src/generators/actions/compilation_context.py` (NEW)

```python
"""Compilation context for tracking state across step compilation"""

from dataclasses import dataclass, field
from typing import Any

@dataclass
class CompilationContext:
    """Shared context for step compilation"""

    # CTE tracking
    ctes: list[dict] = field(default_factory=list)

    # Variable tracking
    declared_variables: dict[str, str] = field(default_factory=dict)  # name -> type

    # Function context
    schema: str = ""
    function_name: str = ""
    parameters: dict[str, str] = field(default_factory=dict)

    def add_cte(self, name: str, query: str, materialized: bool = False):
        """Register a CTE"""
        self.ctes.append({
            "name": name,
            "query": query.strip(),
            "materialized": materialized
        })

    def add_variable(self, name: str, var_type: str):
        """Register a declared variable"""
        self.declared_variables[name] = var_type

    def has_ctes(self) -> bool:
        """Check if any CTEs are registered"""
        return len(self.ctes) > 0

    def get_with_clause(self) -> str:
        """Build WITH clause from CTEs"""
        if not self.has_ctes():
            return ""

        cte_defs = []
        for cte in self.ctes:
            mat = " MATERIALIZED" if cte["materialized"] else ""
            cte_defs.append(f"{cte['name']} AS{mat} (\n{cte['query']}\n)")

        return "WITH " + ",\n".join(cte_defs) + "\n"
```

Update compilers to use `CompilationContext`:

```python
class CTEStepCompiler(StepCompiler):
    def compile(self, step: ActionStep, context: CompilationContext) -> str:
        context.add_cte(step.cte_name, step.cte_query, step.cte_materialized)
        return ""

class DeclareStepCompiler(StepCompiler):
    def compile(self, step: ActionStep, context: CompilationContext) -> str:
        if step.variable_name:
            context.add_variable(step.variable_name, step.variable_type)
            # ... rest of compilation
```

#### Refactor 3: Pattern Detection
**File**: `src/core/pattern_detector.py` (NEW)

```python
"""Detect common patterns in SpecQL actions for optimization"""

from src.core.ast_models import Action, ActionStep

class PatternDetector:
    """Detects and optimizes common action patterns"""

    @staticmethod
    def detect_aggregate_pattern(action: Action) -> bool:
        """Detect if action is a simple aggregate query"""
        if len(action.steps) == 2:
            return (
                action.steps[0].type == "declare" and
                action.steps[1].type == "query" and
                any(agg in action.steps[1].expression.upper()
                    for agg in ["SUM", "COUNT", "AVG", "MAX", "MIN"])
            )
        return False

    @staticmethod
    def detect_cte_chain(action: Action) -> list[str]:
        """Detect chain of dependent CTEs"""
        cte_names = []
        for step in action.steps:
            if step.type == "cte":
                cte_names.append(step.cte_name)
        return cte_names
```

**Run Tests**: All existing tests should still pass

```bash
uv run pytest tests/unit/core/test_declare_action.py -v
uv run pytest tests/unit/core/test_cte_action.py -v
uv run pytest tests/integration/actions/test_declare_cte_compilation.py -v
# All PASSED
```

---

### ✅ QA Phase (Day 6-7): Verification

#### QA 1: Full Test Suite
```bash
# Run all tests
uv run pytest --tb=short -v

# Expected: All tests pass
# New: 5 tests for declare/cte
# Existing: 120+ tests still passing
```

#### QA 2: Reference SQL Validation

Test against real reference SQL function:

**Reference**: `printoptim_specql/reference_sql/0_schema/fn_calculate_order_total.sql`
```sql
CREATE OR REPLACE FUNCTION crm.calculate_order_total(
    p_order_id UUID
) RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
    v_subtotal NUMERIC := 0;
    v_tax_amount NUMERIC := 0;
    v_total NUMERIC := 0;
BEGIN
    WITH order_lines AS (
        SELECT quantity, unit_price
        FROM tb_order_line
        WHERE order_id = p_order_id
    )
    SELECT SUM(quantity * unit_price) INTO v_subtotal FROM order_lines;

    v_tax_amount := v_subtotal * 0.0825;
    v_total := v_subtotal + v_tax_amount;

    RETURN v_total;
END;
$$;
```

**SpecQL Equivalent**:
```yaml
entity: Order
schema: crm
actions:
  - name: calculate_order_total
    parameters:
      - name: order_id
        type: uuid
    returns: numeric
    steps:
      - declare:
          - name: subtotal
            type: numeric
            default: 0
          - name: tax_amount
            type: numeric
            default: 0
          - name: total
            type: numeric
            default: 0

      - cte:
          name: order_lines
          query: |
            SELECT quantity, unit_price
            FROM tb_order_line
            WHERE order_id = $order_id

      - query: subtotal = SELECT SUM(quantity * unit_price) FROM order_lines
      - assign: tax_amount = subtotal * 0.0825
      - assign: total = subtotal + tax_amount
      - return: total
```

**Test**: Generate and compare

```bash
specql generate entities/order.yaml --output=generated/order.sql

# Compare
diff generated/order.sql reference_sql/0_schema/fn_calculate_order_total.sql

# Should be functionally equivalent (formatting may differ)
```

#### QA 3: Code Quality

```bash
# Linting
uv run ruff check src/core/parser.py
uv run ruff check src/generators/actions/step_compilers/declare_step.py
uv run ruff check src/generators/actions/step_compilers/cte_step.py

# Type checking
uv run mypy src/core/ast_models.py
uv run mypy src/generators/actions/step_compilers/

# All should pass with no errors
```

#### QA 4: Documentation

**File**: `docs/actions/declare.md`

```markdown
# declare - Variable Declaration

Declare local variables for use within an action.

## Syntax

Single variable:
```yaml
- declare:
    name: variable_name
    type: numeric
    default: 0
```

Multiple variables:
```yaml
- declare:
    - name: total
      type: numeric
      default: 0
    - name: count
      type: integer
```

## Supported Types
- text, integer, bigint, numeric, decimal
- boolean, uuid, timestamp, date, time
- json, array

## Examples

See `examples/actions/declare_examples.yaml`
```

**File**: `docs/actions/cte.md`

```markdown
# cte - Common Table Expression

Define reusable query expressions (CTEs) for complex queries.

## Syntax

```yaml
- cte:
    name: cte_name
    query: |
      SELECT ...
      FROM ...
    materialized: false  # optional
```

## Multiple CTEs

```yaml
- cte:
    name: first_cte
    query: SELECT ...

- cte:
    name: second_cte
    query: |
      SELECT ...
      FROM first_cte  # Can reference previous CTEs
```

## Examples

See `examples/actions/cte_examples.yaml`
```

#### QA 5: Integration Test

**Full E2E Test**: `tests/integration/test_week1_declare_cte.py`

```python
def test_week1_full_integration():
    """
    Full integration test for Week 1 features
    - Parse YAML with declare + cte
    - Compile to PL/pgSQL
    - Execute in test database
    - Verify results
    """
    yaml_content = """
    entity: Invoice
    schema: billing
    actions:
      - name: calculate_invoice_total
        parameters:
          - name: invoice_id
            type: uuid
        returns: numeric
        steps:
          - declare:
              name: total
              type: numeric
              default: 0

          - cte:
              name: line_totals
              query: |
                SELECT SUM(quantity * unit_price) as line_total
                FROM tb_line_item
                WHERE invoice_id = $invoice_id

          - query: total = SELECT line_total FROM line_totals
          - return: total
    """

    # Parse
    ast = parse_specql(yaml_content)
    assert len(ast.entities) == 1

    # Compile
    sql = generate_schema(ast)
    assert "DECLARE" in sql
    assert "WITH line_totals AS" in sql

    # Execute in test DB
    with get_test_db_connection() as conn:
        conn.execute(sql)

        # Test with data
        test_invoice_id = uuid.uuid4()
        conn.execute(f"""
            INSERT INTO billing.tb_invoice (pk_invoice, id, identifier)
            VALUES (1, '{test_invoice_id}', 'INV-001');

            INSERT INTO billing.tb_line_item (invoice_id, quantity, unit_price)
            VALUES ('{test_invoice_id}', 2, 50.00),
                   ('{test_invoice_id}', 1, 100.00);
        """)

        # Call function
        result = conn.execute(f"""
            SELECT billing.calculate_invoice_total('{test_invoice_id}');
        """).fetchone()[0]

        assert result == 200.00  # (2*50) + (1*100)
```

**Run Integration Tests**:
```bash
uv run pytest tests/integration/test_week1_declare_cte.py -v
# PASSED: Full E2E working
```

---

### 📊 Week 1 Deliverables

✅ **Code**:
- `src/core/ast_models.py` - Extended with declare/cte
- `src/core/parser.py` - Parses declare/cte steps
- `src/generators/actions/step_compilers/declare_step.py` - NEW
- `src/generators/actions/step_compilers/cte_step.py` - NEW
- `src/generators/actions/type_mapper.py` - NEW (refactor)
- `src/generators/actions/compilation_context.py` - NEW (refactor)

✅ **Tests**:
- `tests/unit/core/test_declare_action.py` - 2 tests
- `tests/unit/core/test_cte_action.py` - 2 tests
- `tests/integration/actions/test_declare_cte_compilation.py` - 1 test
- `tests/integration/test_week1_declare_cte.py` - 1 E2E test

✅ **Documentation**:
- `docs/actions/declare.md`
- `docs/actions/cte.md`
- `examples/actions/declare_examples.yaml`
- `examples/actions/cte_examples.yaml`

✅ **Metrics**:
- **Coverage increase**: 21% → 35% (14 percentage points)
- **Reference SQL expressible**: 20 more functions
- **Test coverage**: 6 new tests, all passing
- **Lines of code**: ~500 new lines

---

## WEEK 2: aggregate + subquery + call_function

### Objective
Enable aggregation expressions, embedded subqueries, and function calls with return values.

---

### 🔴 RED Phase (Days 1-2): Write Failing Tests

#### Test 1: Aggregate Expressions
**File**: `tests/unit/core/test_aggregate_action.py`

```python
def test_aggregate_in_query():
    """Test aggregate functions in queries"""
    yaml_content = """
    entity: Report
    actions:
      - name: sales_summary
        steps:
          - aggregate:
              operation: sum
              field: amount
              from: tb_order
              where: status = 'completed'
              as: total_sales
          - aggregate:
              operation: count
              field: id
              from: tb_order
              where: status = 'completed'
              as: order_count
          - return:
              total_sales: $total_sales
              order_count: $order_count
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[0].type == "aggregate"
    assert action.steps[0].operation == "sum"
    assert action.steps[0].field == "amount"

def test_aggregate_with_group_by():
    """Test aggregate with grouping"""
    yaml_content = """
    entity: Analytics
    actions:
      - name: sales_by_region
        steps:
          - aggregate:
              operation: sum
              field: amount
              from: tb_order
              group_by: region
              as: regional_totals
          - return: regional_totals
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[0].group_by == "region"
```

#### Test 2: Subqueries
**File**: `tests/unit/core/test_subquery_action.py`

```python
def test_subquery_in_where():
    """Test subquery in WHERE clause"""
    yaml_content = """
    entity: Customer
    actions:
      - name: find_high_value_customers
        steps:
          - query: |
              SELECT * FROM tb_customer
              WHERE id IN (
                subquery:
                  SELECT customer_id FROM tb_order
                  WHERE total_amount > 1000
                  GROUP BY customer_id
                  HAVING COUNT(*) > 5
              )
          - return: result
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    # Should detect subquery pattern
    assert "subquery:" in action.steps[0].expression

def test_subquery_as_value():
    """Test subquery returning single value"""
    yaml_content = """
    entity: Order
    actions:
      - name: calculate_order_with_avg
        steps:
          - declare:
              name: avg_order_value
              type: numeric

          - subquery:
              query: SELECT AVG(total_amount) FROM tb_order
              as: avg_order_value

          - if: total_amount > avg_order_value
            then:
              - update: Order SET status = 'high_value'
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[1].type == "subquery"
    assert action.steps[1].result_variable == "avg_order_value"
```

#### Test 3: Function Calls with Returns
**File**: `tests/unit/core/test_call_function_action.py`

```python
def test_call_function_with_return():
    """Test calling function and capturing return value"""
    yaml_content = """
    entity: Invoice
    actions:
      - name: process_invoice
        steps:
          - declare:
              name: calculated_total
              type: numeric

          - call_function:
              function: billing.calculate_total
              arguments:
                invoice_id: $invoice_id
              returns: calculated_total

          - update: Invoice SET total_amount = calculated_total WHERE id = $invoice_id
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[1].type == "call_function"
    assert action.steps[1].function_name == "billing.calculate_total"
    assert action.steps[1].return_variable == "calculated_total"

def test_call_function_composition():
    """Test calling multiple functions in sequence"""
    yaml_content = """
    entity: Order
    actions:
      - name: complex_calculation
        steps:
          - call_function:
              function: calculate_subtotal
              arguments:
                order_id: $order_id
              returns: subtotal

          - call_function:
              function: calculate_tax
              arguments:
                amount: $subtotal
                region: $region
              returns: tax_amount

          - call_function:
              function: apply_discount
              arguments:
                amount: $subtotal
                customer_id: $customer_id
              returns: discount_amount

          - assign: final_total = subtotal + tax_amount - discount_amount
          - return: final_total
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    call_steps = [s for s in action.steps if s.type == "call_function"]
    assert len(call_steps) == 3
```

**Expected Output**: All tests FAIL

```bash
uv run pytest tests/unit/core/test_aggregate_action.py -v
# FAILED: 'aggregate' step type not recognized

uv run pytest tests/unit/core/test_subquery_action.py -v
# FAILED: 'subquery' step type not recognized

uv run pytest tests/unit/core/test_call_function_action.py -v
# FAILED: 'call_function' step type not recognized
```

---

### 🟢 GREEN Phase (Days 3-5): Minimal Implementation

**Summary**: Similar structure to Week 1:
1. Extend `ActionStep` dataclass with new fields
2. Update parser to recognize new step types
3. Create step compilers for each new type
4. Update orchestrator to use new compilers

**Key Files**:
- `src/generators/actions/step_compilers/aggregate_step.py` - NEW
- `src/generators/actions/step_compilers/subquery_step.py` - NEW
- `src/generators/actions/step_compilers/call_function_step.py` - NEW

**Expected Output**: All tests PASS

---

### 🔧 REFACTOR Phase (Day 6): Clean & Optimize

**Refactorings**:
1. Extract query builder utility
2. Optimize aggregate detection
3. Improve subquery nesting handling

---

### ✅ QA Phase (Day 7): Verification

**QA Checklist**:
- [ ] All tests pass (6 new + 126 existing)
- [ ] Reference SQL comparison (3 functions)
- [ ] Code quality (ruff + mypy)
- [ ] Documentation (3 new docs)
- [ ] Integration test (E2E with test DB)

**Metrics**:
- **Coverage increase**: 35% → 55% (20 percentage points)
- **Reference SQL expressible**: 35 more functions
- **Test coverage**: 6 new tests
- **Lines of code**: ~600 new lines

---

## WEEK 3: switch + return_early

### Objective
Enable switch/case statements and early returns for complex conditional logic.

---

### 🔴 RED Phase (Days 1-2): Write Failing Tests

#### Test 1: Switch Statement
**File**: `tests/unit/core/test_switch_action.py`

```python
def test_switch_basic():
    """Test basic switch/case statement"""
    yaml_content = """
    entity: Order
    actions:
      - name: process_order_by_type
        parameters:
          - name: order_type
            type: text
        steps:
          - switch:
              expression: $order_type
              cases:
                - when: 'standard'
                  then:
                    - update: Order SET processing_time = 24

                - when: 'express'
                  then:
                    - update: Order SET processing_time = 4

                - when: 'overnight'
                  then:
                    - update: Order SET processing_time = 1

              default:
                - error: "Invalid order type"
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[0].type == "switch"
    assert action.steps[0].switch_expression == "$order_type"
    assert len(action.steps[0].cases) == 3
    assert action.steps[0].default_steps is not None

def test_switch_with_multiple_conditions():
    """Test switch with complex case conditions"""
    yaml_content = """
    entity: Customer
    actions:
      - name: categorize_customer
        steps:
          - declare:
              name: category
              type: text

          - switch:
              expression: (total_purchases, years_active)
              cases:
                - when: total_purchases > 50000 AND years_active > 5
                  then:
                    - assign: category = 'platinum'

                - when: total_purchases > 10000
                  then:
                    - assign: category = 'gold'

                - when: total_purchases > 1000
                  then:
                    - assign: category = 'silver'

              default:
                - assign: category = 'bronze'

          - return: category
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    switch_step = action.steps[1]
    assert switch_step.type == "switch"
    assert len(switch_step.cases) == 3
```

#### Test 2: Early Return
**File**: `tests/unit/core/test_return_early_action.py`

```python
def test_return_early_simple():
    """Test early return from function"""
    yaml_content = """
    entity: Order
    actions:
      - name: validate_and_process
        steps:
          - if: status != 'pending'
            then:
              - return_early:
                  success: false
                  message: "Order already processed"

          - if: total_amount <= 0
            then:
              - return_early:
                  success: false
                  message: "Invalid order amount"

          # Continue with processing
          - update: Order SET status = 'processing'
          - return:
              success: true
              message: "Order processing started"
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    early_return_steps = [s for s in action.steps[0].then_steps if s.type == "return_early"]
    assert len(early_return_steps) == 1

def test_return_early_with_value():
    """Test early return with computed value"""
    yaml_content = """
    entity: Calculator
    actions:
      - name: divide_numbers
        parameters:
          - name: numerator
            type: numeric
          - name: denominator
            type: numeric
        returns: numeric
        steps:
          - if: denominator = 0
            then:
              - return_early: NULL

          - return: numerator / denominator
    """
    ast = parse_specql(yaml_content)
    action = ast.entities[0].actions[0]

    assert action.steps[0].then_steps[0].type == "return_early"
    assert action.steps[0].then_steps[0].return_value == "NULL"
```

**Expected Output**: All tests FAIL

---

### 🟢 GREEN Phase (Days 3-5): Implementation

**Key Files**:
- `src/generators/actions/step_compilers/switch_step.py` - NEW
- `src/generators/actions/step_compilers/return_early_step.py` - NEW

**Switch Compiler Logic**:
```python
class SwitchStepCompiler(StepCompiler):
    def compile(self, step: ActionStep, context: CompilationContext) -> str:
        """Compile switch to CASE WHEN or IF/ELSIF chain"""

        if self._is_simple_value_switch(step):
            # Use CASE expression for simple value matching
            return self._compile_as_case_expression(step, context)
        else:
            # Use IF/ELSIF for complex conditions
            return self._compile_as_if_chain(step, context)

    def _compile_as_case_expression(self, step, context) -> str:
        lines = [f"CASE {step.switch_expression}"]

        for case in step.cases:
            when_value = case.when_value
            then_body = self._compile_steps(case.then_steps, context)
            lines.append(f"  WHEN {when_value} THEN")
            lines.append(f"    {then_body}")

        if step.default_steps:
            default_body = self._compile_steps(step.default_steps, context)
            lines.append(f"  ELSE")
            lines.append(f"    {default_body}")

        lines.append("END CASE;")
        return "\n".join(lines)

    def _compile_as_if_chain(self, step, context) -> str:
        lines = []

        for i, case in enumerate(step.cases):
            keyword = "IF" if i == 0 else "ELSIF"
            condition = case.when_condition
            then_body = self._compile_steps(case.then_steps, context)

            lines.append(f"{keyword} {condition} THEN")
            lines.append(f"  {then_body}")

        if step.default_steps:
            default_body = self._compile_steps(step.default_steps, context)
            lines.append("ELSE")
            lines.append(f"  {default_body}")

        lines.append("END IF;")
        return "\n".join(lines)
```

**Early Return Compiler Logic**:
```python
class ReturnEarlyStepCompiler(StepCompiler):
    def compile(self, step: ActionStep, context: CompilationContext) -> str:
        """Compile early return to RETURN statement"""

        return_value = step.return_value

        if return_value is None:
            return "RETURN;"

        # Format return value based on function return type
        if context.function_return_type == "app.mutation_result":
            # Return FraiseQL mutation result
            return self._build_mutation_result(return_value)
        else:
            # Simple return
            return f"RETURN {return_value};"

    def _build_mutation_result(self, value: dict) -> str:
        """Build mutation_result return value"""
        return f"""RETURN ROW(
            {value.get('success', 'false')}::BOOLEAN,
            {value.get('message', "''")}::TEXT,
            '{{}}'::JSONB,
            '{{}}'::JSONB
        )::app.mutation_result;"""
```

**Expected Output**: Tests PASS

---

### 🔧 REFACTOR Phase (Day 6): Optimize

**Refactorings**:
1. Extract case condition optimizer
2. Simplify switch pattern detection
3. Optimize early return in nested contexts

---

### ✅ QA Phase (Day 7): Verification

**Metrics**:
- **Coverage increase**: 55% → 68% (13 percentage points)
- **Reference SQL expressible**: 25 more functions
- **Test coverage**: 4 new tests
- **Lines of code**: ~450 new lines

---

## WEEK 4-5: while + for_query + exception_handling

**TDD Methodology**: RED → GREEN → REFACTOR → QA

**New Action Types**:
- `while` - While loops with conditions (WHILE...LOOP...END LOOP)
- `for_query` - Iterate over query results (FOR...IN...LOOP...END LOOP)
- `exception_handling` - Try/catch blocks (BEGIN...EXCEPTION WHEN...END)

**Key Challenges**:
- Loop variable scoping and lifetime management
- Query cursor management and cleanup
- Exception type mapping (PostgreSQL → SpecQL)
- Nested loop context handling

**Metrics**:
- **Coverage increase**: 68% → 82% (14 percentage points)
- **Reference SQL expressible**: 30 more functions
- **Test coverage**: 6 new unit tests, 2 integration tests

---

### 🔴 RED Phase: Write Failing Tests

**Objective**: Define expected behavior through comprehensive test cases

#### 1. Create test_while_action.py
```python
def test_while_basic():
    """Test basic while loop with counter"""
    yaml_content = """
    entity: Counter
    actions:
      - name: countdown
        steps:
          - declare: counter = 10
          - while: counter > 0
            loop:
              - query: counter = counter - 1
              - if: counter = 5
                then:
                  - return_early: "Halfway done"
          - return: "Done"
    """
    # Should parse and validate AST structure

def test_while_with_complex_condition():
    """Test while with complex boolean condition"""
    yaml_content = """
    entity: Processor
    actions:
      - name: process_until_complete
        steps:
          - declare: status = 'pending'
          - while: status != 'complete' AND attempts < 5
            loop:
              - call_function:
                  function: process_batch
                  returns: batch_result
              - query: status = batch_result.status
              - query: attempts = attempts + 1
    """
    # Should handle complex conditions and variable updates
```

#### 2. Create test_for_query_action.py
```python
def test_for_query_basic():
    """Test iteration over query results"""
    yaml_content = """
    entity: Report
    actions:
      - name: process_all_orders
        steps:
          - declare: total = 0
          - for_query: SELECT id, amount FROM orders WHERE status = 'active'
            as: order_record
            loop:
              - query: total = total + order_record.amount
              - if: order_record.amount > 1000
                then:
                  - call_function:
                      function: flag_large_order
                      arguments: {order_id: order_record.id}
          - return: total
    """
    # Should handle cursor iteration and record access

def test_for_query_with_limit():
    """Test for_query with LIMIT and ORDER BY"""
    yaml_content = """
    entity: Notification
    actions:
      - name: send_recent_notifications
        steps:
          - for_query: |
              SELECT id, user_id, message
              FROM notifications
              WHERE sent_at IS NULL
              ORDER BY created_at DESC
              LIMIT 100
            as: notification
            loop:
              - call_service:
                  service: email_service
                  operation: send
                  input: {to: notification.user_id, message: notification.message}
              - update: Notification SET sent_at = now() WHERE id = notification.id
    """
    # Should handle complex queries with ordering and limits
```

#### 3. Create test_exception_handling_action.py
```python
def test_exception_handling_basic():
    """Test basic try/catch exception handling"""
    yaml_content = """
    entity: Transaction
    actions:
      - name: process_payment
        steps:
          - exception_handling:
              try:
                - call_service:
                    service: payment_gateway
                    operation: charge
                    input: {amount: $amount, card: $card_token}
                - update: Transaction SET status = 'completed'
              catch:
                - when: 'payment_failed'
                  then:
                    - update: Transaction SET status = 'failed'
                    - reject: "Payment processing failed"
                - when: 'network_error'
                  then:
                    - update: Transaction SET status = 'retry'
                    - call_function: schedule_retry
              finally:
                - call_function: cleanup_resources
    """
    # Should handle exception types and finally blocks

def test_exception_handling_multiple_catches():
    """Test multiple exception handlers"""
    yaml_content = """
    entity: FileProcessor
    actions:
      - name: import_data
        steps:
          - exception_handling:
              try:
                - call_function: parse_file
                - call_function: validate_data
                - call_function: save_records
              catch:
                - when: 'parse_error'
                  then: [log_error, reject_invalid_format]
                - when: 'validation_error'
                  then: [log_error, reject_invalid_data]
                - when: 'database_error'
                  then: [log_error, rollback_transaction]
                - when: 'OTHERS'
                  then: [log_error, reject_system_error]
    """
    # Should handle multiple exception types including OTHERS
```

**Expected Failures**: All tests should fail with "Unknown step type" errors

---

### 🟢 GREEN Phase: Implement Minimal Code

**Objective**: Make all tests pass with minimal, working implementations

#### 1. Extend AST Models (ast_models.py)
```python
@dataclass
class LoopStep:
    """Loop body for while/for_query"""
    loop_steps: list["ActionStep"] = field(default_factory=list)

@dataclass
class ExceptionHandler:
    """Exception handler in catch block"""
    when_condition: str  # Exception type (payment_failed, OTHERS, etc.)
    then_steps: list["ActionStep"] = field(default_factory=list)

@dataclass
class ActionStep:
    # ... existing fields ...

    # NEW: while loop
    while_condition: str | None = None
    loop_body: list["ActionStep"] = field(default_factory=list)

    # NEW: for_query loop
    for_query_sql: str | None = None
    for_query_alias: str | None = None  # Record variable name
    for_query_body: list["ActionStep"] = field(default_factory=list)

    # NEW: exception handling
    try_steps: list["ActionStep"] = field(default_factory=list)
    catch_handlers: list[ExceptionHandler] = field(default_factory=list)
    finally_steps: list["ActionStep"] = field(default_factory=list)
```

#### 2. Update Parser (specql_parser.py)
```python
def _parse_single_step(self, step_data: dict) -> ActionStep:
    # ... existing elif chain ...
    elif "while" in step_data:
        return self._parse_while_step(step_data)
    elif "for_query" in step_data:
        return self._parse_for_query_step(step_data)
    elif "exception_handling" in step_data:
        return self._parse_exception_handling_step(step_data)

def _parse_while_step(self, step_data: dict) -> ActionStep:
    """Parse while loop"""
    while_data = step_data["while"]
    return ActionStep(
        type="while",
        while_condition=while_data,
        loop_body=[self._parse_single_step(step) for step in step_data.get("loop", [])]
    )

def _parse_for_query_step(self, step_data: dict) -> ActionStep:
    """Parse for_query loop"""
    for_data = step_data["for_query"]
    return ActionStep(
        type="for_query",
        for_query_sql=for_data,
        for_query_alias=step_data.get("as"),
        for_query_body=[self._parse_single_step(step) for step in step_data.get("loop", [])]
    )

def _parse_exception_handling_step(self, step_data: dict) -> ActionStep:
    """Parse exception handling block"""
    eh_data = step_data["exception_handling"]

    # Parse catch handlers
    catch_handlers = []
    for catch_data in eh_data.get("catch", []):
        handler = ExceptionHandler(
            when_condition=catch_data["when"],
            then_steps=[self._parse_single_step(step) for step in catch_data.get("then", [])]
        )
        catch_handlers.append(handler)

    return ActionStep(
        type="exception_handling",
        try_steps=[self._parse_single_step(step) for step in eh_data.get("try", [])],
        catch_handlers=catch_handlers,
        finally_steps=[self._parse_single_step(step) for step in eh_data.get("finally", [])]
    )
```

#### 3. Create Step Compilers

**while_step.py**:
```python
class WhileStepCompiler(StepCompiler):
    def compile(self, step: ActionStep, entity: EntityDefinition, context: CompilationContext) -> str:
        condition = step.while_condition
        body = self._compile_steps(step.loop_body, context)

        return f"""WHILE {condition} LOOP
    {body}
END LOOP;"""
```

**for_query_step.py**:
```python
class ForQueryStepCompiler(StepCompiler):
    def compile(self, step: ActionStep, entity: EntityDefinition, context: CompilationContext) -> str:
        query = step.for_query_sql
        alias = step.for_query_alias or "rec"
        body = self._compile_steps(step.for_query_body, context)

        return f"""FOR {alias} IN {query} LOOP
    {body}
END LOOP;"""
```

**exception_handling_step.py**:
```python
class ExceptionHandlingStepCompiler(StepCompiler):
    def compile(self, step: ActionStep, entity: EntityDefinition, context: CompilationContext) -> str:
        try_body = self._compile_steps(step.try_steps, context)
        finally_body = self._compile_steps(step.finally_steps, context) if step.finally_steps else ""

        # Build exception handlers
        exception_blocks = []
        for handler in step.catch_handlers:
            when_condition = handler.when_condition
            handler_body = self._compile_steps(handler.then_steps, context)
            exception_blocks.append(f"""WHEN {when_condition} THEN
    {handler_body}""")

        exception_block = "\n".join(exception_blocks)

        return f"""BEGIN
    {try_body}
EXCEPTION
    {exception_block}
{f"FINALLY\n    {finally_body}" if finally_body else ""}
END;"""
```

#### 4. Update Core Logic Generator
```python
def _compile_action_steps(self, action: Action, entity: Entity) -> list[str]:
    # ... existing code ...
    elif step.type == "while":
        compiled.append(self._compile_while_step(step, context))
    elif step.type == "for_query":
        compiled.append(self._compile_for_query_step(step, context))
    elif step.type == "exception_handling":
        compiled.append(self._compile_exception_handling_step(step, context))

def _compile_while_step(self, step: ActionStep, context: CompilationContext) -> str:
    # Minimal implementation - expand in REFACTOR
    return f"WHILE {step.while_condition} LOOP\\n    -- loop body\\nEND LOOP;"

def _compile_for_query_step(self, step: ActionStep, context: CompilationContext) -> str:
    # Minimal implementation - expand in REFACTOR
    return f"FOR rec IN {step.for_query_sql} LOOP\\n    -- loop body\\nEND LOOP;"

def _compile_exception_handling_step(self, step: ActionStep, context: CompilationContext) -> str:
    # Minimal implementation - expand in REFACTOR
    return f"BEGIN\\n    -- try body\\nEXCEPTION\\n    WHEN OTHERS THEN\\n        -- catch body\\nEND;"
```

**Success Criteria**: All RED phase tests now pass

---

### 🔧 REFACTOR Phase: Clean Up and Optimize

**Objective**: Improve code structure, add optimizations, and handle edge cases

#### 1. Extract Loop Optimizer (loop_optimizer.py)
```python
class LoopOptimizer:
    @staticmethod
    def detect_infinite_loops(step: ActionStep) -> bool:
        """Detect potential infinite loops"""
        # Check if condition can become false
        return False  # Placeholder

    @staticmethod
    def optimize_loop_variables(step: ActionStep) -> ActionStep:
        """Optimize variable scoping in loops"""
        return step  # Placeholder

    @staticmethod
    def validate_cursor_usage(step: ActionStep) -> None:
        """Validate cursor usage in for_query loops"""
        pass
```

#### 2. Extract Exception Optimizer (exception_optimizer.py)
```python
class ExceptionOptimizer:
    @staticmethod
    def map_specql_to_postgres_exceptions(specql_exception: str) -> str:
        """Map SpecQL exception names to PostgreSQL exception names"""
        mapping = {
            "payment_failed": "RAISE_EXCEPTION",
            "network_error": "CONNECTION_EXCEPTION",
            "database_error": "INTEGRITY_CONSTRAINT_VIOLATION",
            "parse_error": "INVALID_TEXT_REPRESENTATION",
            "validation_error": "CHECK_VIOLATION",
        }
        return mapping.get(specql_exception, specql_exception.upper())

    @staticmethod
    def optimize_exception_handlers(handlers: list[ExceptionHandler]) -> list[ExceptionHandler]:
        """Optimize exception handler ordering"""
        return handlers
```

#### 3. Enhance Step Compilers

**WhileStepCompiler improvements**:
- Add loop variable scoping
- Detect infinite loop conditions
- Optimize condition evaluation

**ForQueryStepCompiler improvements**:
- Proper cursor management
- Record variable scoping
- Query optimization hints

**ExceptionHandlingStepCompiler improvements**:
- Exception type mapping
- Handler ordering optimization
- Finally block guarantees

#### 4. Add Context Management
```python
class CompilationContext:
    # ... existing fields ...
    loop_stack: list[dict] = field(default_factory=list)  # Track nested loops
    exception_context: bool = False  # Track if inside exception handler

    def enter_loop(self, loop_type: str, variables: list[str]):
        """Enter a loop context"""
        self.loop_stack.append({
            "type": loop_type,
            "variables": variables,
            "depth": len(self.loop_stack)
        })

    def exit_loop(self):
        """Exit loop context"""
        if self.loop_stack:
            self.loop_stack.pop()
```

#### 5. Update Variable Validation
```python
def _validate_expression_fields(self, expression: str, entity_fields: dict[str, FieldDefinition]) -> None:
    # ... existing validation ...
    # Add loop variable validation
    for loop_context in context.loop_stack:
        for var in loop_context["variables"]:
            if f"{var}." in expression:
                return  # Valid loop variable reference
```

**Success Criteria**: Code is cleaner, more robust, and handles edge cases

---

### ✅ QA Phase: Verify Implementation

**Objective**: Ensure everything works correctly and maintain quality standards

#### 1. Run Full Test Suite
```bash
uv run pytest tests/unit/core/test_while_action.py tests/unit/core/test_for_query_action.py tests/unit/core/test_exception_handling_action.py -v
```

#### 2. Run Integration Tests
```bash
uv run pytest tests/integration/actions/test_loop_exception_integration.py -v
```

#### 3. Code Quality Checks
```bash
uv run ruff check src/core/ast_models.py src/core/specql_parser.py src/generators/core_logic_generator.py
uv run mypy src/core/ast_models.py src/core/specql_parser.py --ignore-missing-imports
```

#### 4. Performance Validation
- Verify loop compilation doesn't create infinite loops
- Check exception handling doesn't break transaction semantics
- Validate cursor cleanup in for_query loops

#### 5. Documentation and Examples
- Create `docs/actions/while.md`
- Create `docs/actions/for_query.md`
- Create `docs/actions/exception_handling.md`
- Add example YAML files

**Success Criteria**:
- All tests pass (6 unit + 2 integration)
- Code quality maintained (ruff + mypy clean)
- Coverage increased to 82%
- Documentation complete
- No performance regressions

---

### 📊 Week 4-5 Success Metrics

| Metric | Target | Validation |
|--------|--------|------------|
| **Test Count** | 8 tests | pytest results |
| **Coverage Increase** | +14% (68% → 82%) | coverage report |
| **Code Quality** | ruff + mypy clean | linting results |
| **Documentation** | 3 action docs + examples | file existence |
| **Performance** | No regressions | benchmark comparison |

### 🎯 Key Implementation Notes

1. **Loop Variable Scoping**: Variables declared in loops should be scoped to the loop body
2. **Cursor Management**: for_query must properly open/close cursors
3. **Exception Mapping**: SpecQL exceptions must map to PostgreSQL exception names
4. **Nested Contexts**: Handle loops within exception handlers and vice versa
5. **Transaction Semantics**: Exception handling should work with SAVEPOINT/ROLLBACK

### 🚨 Risk Mitigation

- **Infinite Loops**: Add detection and warnings for potential infinite while loops
- **Cursor Leaks**: Ensure proper cursor cleanup in all code paths
- **Exception Masking**: Don't catch exceptions that should propagate
- **Variable Conflicts**: Handle variable name conflicts in nested scopes

---

## WEEK 6-7: Advanced Features

**New Action Types** (10 remaining):
- `json_build` - Build JSON objects/arrays
- `array_build` - Build PostgreSQL arrays
- `upsert` - INSERT ON CONFLICT
- `batch_operation` - Bulk insert/update
- `window_function` - Window/analytic functions
- `return_table` - RETURN TABLE
- `cursor` - Explicit cursor operations
- `recursive_cte` - Recursive CTEs
- `dynamic_sql` - EXECUTE dynamic SQL
- `transaction_control` - SAVEPOINT/ROLLBACK

**Metrics**:
- **Coverage increase**: 82% → 95% (13 percentage points)
- **Reference SQL expressible**: Remaining complex functions

---

## 📊 Track A Summary (7 Weeks)

### Deliverables

**Code**:
- ✅ 20 new step compilers
- ✅ Extended AST models
- ✅ Updated parser
- ✅ Type mapper utility
- ✅ Compilation context
- ✅ Pattern detector

**Tests**:
- ✅ 40+ unit tests (2 per action type)
- ✅ 20+ integration tests
- ✅ 7 E2E tests (1 per week)
- ✅ Reference SQL validation tests

**Documentation**:
- ✅ 20 action reference docs
- ✅ 20 example YAML files
- ✅ Updated architecture docs
- ✅ Migration guide (old → new actions)

### Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Primitive Actions** | 15 | 35 | +20 |
| **Reference SQL Coverage** | 21% | 95% | +74% |
| **Feasibility Score** | 3/10 | 9/10 | +6 |
| **Test Count** | 120 | 180+ | +60 |
| **Lines of Code** | 6,173 | ~10,000 | +3,827 |

### Success Criteria

- [x] All 20 new action types implemented
- [x] All tests passing (180+)
- [x] Reference SQL functions expressible (95%)
- [x] Code quality maintained (ruff + mypy clean)
- [x] Documentation complete
- [x] Migration path from old actions

---

## 🚦 Go/No-Go Decision Points

### After Week 3 (Core + Control Flow)
**Coverage**: ~68%
**Decision**: Continue to advanced features OR release intermediate version?
**Criteria**:
- Test coverage > 80%
- Reference SQL coverage > 65%
- User feedback positive

### After Week 5 (Core + Control + Loops)
**Coverage**: ~82%
**Decision**: Continue to all 35 actions OR focus on Track B?
**Criteria**:
- Remaining 13% high value features?
- User feedback on needed patterns
- Resource availability

### After Week 7 (All 35 Actions)
**Coverage**: 95%
**Decision**: Release Track A OR wait for Track B?
**Criteria**:
- All tests passing
- Documentation complete
- Reference SQL validation successful

---

## 🔄 Integration with Track B

### Parallel Work (Weeks 1-2)
While Track A implements `declare` + `cte`, Track B can:
- Design SQLite pattern library schema
- Create Python API for pattern storage
- Define pattern data model

### Handoff (Week 3)
Track B needs Track A primitives to:
- Store primitive action implementations
- Test pattern compilation
- Validate cross-language mappings

### Critical Path
Track A must complete Weeks 1-3 before Track B can fully implement pattern storage for primitives.

---

## 📚 Resources

### Reference Documentation
- `docs/implementation_plans/20251112_universal_sql_expression_expansion.md` - Original design
- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - DSL specification
- PostgreSQL PL/pgSQL documentation

### Test Data
- `../printoptim_specql/reference_sql/` - 567 reference SQL functions
- `examples/reference_comparison/` - Comparison YAML/SQL pairs

### Tools
- `pglast` - PostgreSQL parser (for reference SQL analysis)
- `pytest` - Test framework
- `ruff` + `mypy` - Code quality

---

**Last Updated**: 2025-11-12
**Status**: Ready for Implementation
**Next**: Week 1 - declare + cte (RED phase)
