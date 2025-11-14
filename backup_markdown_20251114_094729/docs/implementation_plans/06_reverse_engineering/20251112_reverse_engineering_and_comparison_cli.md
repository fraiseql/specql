# Reverse Engineering and Comparison CLI - Implementation Plan

**Date**: 2025-11-12
**Status**: Planning Phase
**Complexity**: Complex - Phased TDD Approach

---

## Executive Summary

This plan extends the SpecQL CLI to support **reverse engineering** of existing PostgreSQL functions into SpecQL YAML, and **comparison** between reference implementations and auto-generated code. This enables:

1. **Migration Path**: Converting existing SQL codebases to SpecQL
2. **Quality Assurance**: Comparing generated code against reference implementations
3. **Learning Tool**: Understanding what SpecQL generates from YAML definitions
4. **Framework Evolution**: Building a foundation for multi-framework targeting

**Key Innovation**: Treating SQL function parsing as a **Universal AST problem** - we parse reference implementations into the same AST that SpecQL uses internally, enabling comparison and learning.

---

## 🎯 Feasibility Assessment

### Overall Feasibility Score: **8/10**

#### Why 8/10?

**High Feasibility Factors** (✅):
1. **Well-Defined Target**: PostgreSQL PL/pgSQL functions follow consistent patterns
2. **Existing AST Infrastructure**: SpecQL already has comprehensive AST models (`src/core/ast_models.py`)
3. **Pattern-Based Generation**: Current generators follow predictable patterns, making reverse-engineering tractable
4. **Structured Comments**: Functions include `@fraiseql:mutation` metadata for discovery
5. **Type System**: Composite types (`app.type_*_input`) provide strong typing hints
6. **Test Generation Already Works**: Existing test generators prove we can analyze generated code

**Moderate Complexity Factors** (⚠️):
1. **SQL Parsing**: Need robust PL/pgSQL parser (can use `pglast` library)
2. **Business Logic Extraction**: Distinguishing framework code from business logic requires heuristics
3. **Ambiguity Resolution**: Multiple SpecQL patterns can generate similar SQL
4. **Custom Step Detection**: Identifying validate/if/update/insert steps from procedural code

**Why Not 10/10?**:
- SQL is imperative; SpecQL is declarative - there's inherent information loss
- Edge cases with complex custom logic may not map cleanly
- Need heuristics for detecting patterns vs custom code

---

## 📊 Current State Analysis

### ✅ What's Already Implemented

1. **Test Generation** (`src/cli/generate.py:586-719`)
   - pgTAP test generation
   - Pytest integration test generation
   - Seed data generation via `EntitySeedGenerator`

2. **Seed Data Generation** (`src/testing/seed/seed_generator.py`)
   - Field value generators
   - Foreign key resolution
   - UUID generation with tenant scoping
   - Batch generation support

3. **Rich CLI Framework** (`src/cli/`)
   - Framework-aware generation (`framework_defaults.py`, `framework_registry.py`)
   - Progress indicators (`progress.py`)
   - Confiture integration for flat/hierarchical output
   - Comprehensive help text

4. **Validation & Diff Commands**
   - `specql validate` - Validates SpecQL YAML syntax
   - `specql diff` - Shows schema differences
   - `specql docs` - Generates documentation

### ❌ What's Missing for Comparison & Reverse Engineering

1. **No SQL Parser**: Cannot parse existing PostgreSQL functions
2. **No Comparison Engine**: Cannot compare generated vs reference implementations
3. **No Reverse Engineering**: Cannot extract SpecQL YAML from SQL functions
4. **No Test Execution**: Tests are generated but not automatically run
5. **No Reporting**: No visual comparison reports or diffs

---

## 🏗️ Architecture Design

### Team F: Reverse Engineering & Comparison

New team focused on bidirectional conversion and quality assurance.

```
┌─────────────────────────────────────────────────────────────┐
│ Team F: Reverse Engineering & Comparison                   │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐ │
│  │ SQL Parser   │─────▶│ AST Mapper   │─────▶│ YAML     │ │
│  │ (pglast)     │      │ (SQL→SpecQL) │      │ Generator│ │
│  └──────────────┘      └──────────────┘      └──────────┘ │
│         │                                           │       │
│         │              ┌──────────────┐             │       │
│         └─────────────▶│ Comparison   │◀────────────┘       │
│                        │ Engine       │                     │
│                        └──────────────┘                     │
│                               │                             │
│                        ┌──────────────┐                     │
│                        │ Report       │                     │
│                        │ Generator    │                     │
│                        └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Reference SQL Functions
         │
         ▼
    SQL Parser (pglast)
         │
         ▼
    Intermediate AST
         │
         ▼
    AST Mapper (Heuristics)
         │
         ▼
    SpecQL Universal AST ◀─────── SpecQL YAML
         │                              │
         │                              │
         ▼                              ▼
    Comparison Engine ◀───────── Generated SQL
         │
         ▼
    Diff Report (JSON/HTML/Terminal)
```

---

## 💻 Ideal CLI Experience

### For AI Agents

**Discovery & Analysis**:
```bash
# Scan reference implementation for functions
specql scan db/reference/schema.sql --output=discovered.json

# Output: JSON with function signatures, types, dependencies
{
  "functions": [
    {
      "name": "app.create_contact",
      "schema": "app",
      "signature": "app.create_contact(UUID, UUID, JSONB)",
      "returns": "app.mutation_result",
      "input_type": "app.type_create_contact_input",
      "entity": "Contact",
      "pattern": "app_wrapper"
    },
    {
      "name": "crm.create_contact",
      "schema": "crm",
      "signature": "crm.create_contact(UUID, app.type_create_contact_input, JSONB, UUID)",
      "returns": "app.mutation_result",
      "entity": "Contact",
      "pattern": "core_logic",
      "steps": ["validate", "fk_resolve", "insert"]
    }
  ],
  "composite_types": [
    {
      "name": "app.type_create_contact_input",
      "fields": ["email", "first_name", "last_name", "company_id", "status", "phone"]
    }
  ]
}
```

**Reverse Engineering**:
```bash
# Generate SpecQL YAML from SQL functions
specql reverse db/reference/fn_contact.sql --output=entities/contact.yaml

# Output: SpecQL YAML
entity: Contact
schema: crm
fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)
  phone: text
actions:
  - name: create_contact
    steps:
      - validate: company_id IS NOT NULL
      - insert: Contact SET email, first_name, last_name, company, status, phone
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Comparison**:
```bash
# Compare generated vs reference
specql compare entities/contact.yaml \
  --reference=db/reference/ \
  --generated=migrations/ \
  --report=comparison_report.html

# Terminal output:
📊 Comparison Report: Contact
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Schema Structure: MATCH
   ├─ Table tb_contact: MATCH
   ├─ Trinity pattern (pk_*, id, identifier): MATCH
   └─ Audit fields (created_at, updated_at): MATCH

✅ Function: create_contact
   ├─ Signature: MATCH
   ├─ Input type: MATCH
   ├─ Return type: MATCH
   └─ Logic: 95% SIMILAR
      ⚠️  Line 78: Reference uses custom validation, generated uses standard pattern
      💡 Suggestion: Add explicit validation step to SpecQL YAML

⚠️  Function: qualify_lead
   ├─ Signature: MATCH
   ├─ Input type: MATCH
   └─ Logic: 80% SIMILAR
      ⚠️  Reference includes audit trail, generated does not
      💡 Suggestion: Add --with-audit-cascade flag

📈 Overall Match: 90%
   Confidence: HIGH
```

### For Human Developers

**Interactive Comparison**:
```bash
# Interactive mode with visual diff
specql compare entities/contact.yaml \
  --reference=db/reference/ \
  --interactive

# Opens side-by-side diff with:
# - Color-coded differences
# - Suggested fixes
# - Copy-to-clipboard snippets
```

**Test Execution**:
```bash
# Generate tests + seed data + run them
specql test entities/contact.yaml \
  --generate-tests \
  --generate-seed \
  --run \
  --coverage

# Output:
🧪 Test Execution Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Generated:
   ├─ tests/pgtap/contact_test.sql (15 tests)
   ├─ tests/pytest/test_contact_integration.py (8 tests)
   └─ tests/seed/contact_seed.sql (50 records)

🏃 Running pgTAP tests...
   ✅ 15/15 passed (2.3s)

🏃 Running Pytest tests...
   ✅ 8/8 passed (4.1s)

📊 Coverage: 94%
   ⚠️  Missing: soft delete scenario
```

**Learning Mode**:
```bash
# Explain what SpecQL generates
specql explain entities/contact.yaml --verbose

# Output:
📚 SpecQL Generation Explanation: Contact
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

From this 12-line YAML, SpecQL generates:

1️⃣  Table: crm.tb_contact
   ├─ Trinity Pattern columns (pk_contact, id, identifier)
   ├─ Field columns (email, first_name, last_name, fk_company, status, phone)
   ├─ Audit columns (created_at, updated_at, deleted_at, created_by, updated_by)
   └─ Indexes (on tenant_id, status, fk_company)
   📄 Generated: migrations/.../012036_tb_contact.sql (98 lines)

2️⃣  Helper Functions
   ├─ crm.contact_pk(UUID, UUID) → INTEGER
   ├─ crm.contact_id(INTEGER) → UUID
   └─ crm.contact_identifier(INTEGER) → TEXT
   📄 Generated: migrations/.../012036_fn_contact.sql (46 lines)

3️⃣  Action: create_contact
   ├─ App wrapper: app.create_contact(UUID, UUID, JSONB)
   ├─ Input type: app.type_create_contact_input
   ├─ Core logic: crm.create_contact(...)
   ├─ Validation: company_id reference check
   ├─ FK resolution: UUID → INTEGER via company_pk()
   └─ Audit: via app.log_and_return_mutation()
   📄 Generated: migrations/.../012036_fn_contact_create_contact.sql (153 lines)

4️⃣  Action: qualify_lead
   ├─ App wrapper: app.qualify_lead(UUID, UUID, JSONB)
   ├─ Input type: app.type_qualify_lead_input
   ├─ Core logic: crm.qualify_lead(...)
   ├─ Validation: status = 'lead' check
   └─ Update: SET status = 'qualified'
   📄 Generated: migrations/.../012036_fn_contact_qualify_lead.sql (126 lines)

💡 Total: 12 lines YAML → 423 lines production SQL
   Leverage: 35x
```

---

## 📋 Detailed Implementation Plan

### Phase 1: SQL Parsing & Discovery (RED → GREEN → REFACTOR → QA)

**Objective**: Parse existing SQL functions and extract metadata

#### RED: Write Failing Tests
```python
# tests/unit/reverse/test_sql_parser.py

def test_parse_app_wrapper_function():
    """Should parse app wrapper function and extract metadata"""
    sql = """
    CREATE OR REPLACE FUNCTION app.create_contact(
        auth_tenant_id UUID,
        auth_user_id UUID,
        input_payload JSONB
    ) RETURNS app.mutation_result
    LANGUAGE plpgsql
    AS $$ ... $$;
    """

    parser = SQLFunctionParser()
    result = parser.parse(sql)

    assert result.name == "create_contact"
    assert result.schema == "app"
    assert result.pattern == "app_wrapper"
    assert len(result.parameters) == 3
    assert result.parameters[0].name == "auth_tenant_id"
    assert result.parameters[0].type == "UUID"
    assert result.returns == "app.mutation_result"

def test_extract_fraiseql_metadata():
    """Should extract @fraiseql:mutation from comments"""
    sql = """
    COMMENT ON FUNCTION app.create_contact IS
    'Creates a new Contact.
    @fraiseql:mutation
    name: createContact
    input_type: app.type_create_contact_input
    success_type: CreateContactSuccess';
    """

    parser = SQLFunctionParser()
    metadata = parser.extract_fraiseql_metadata(sql)

    assert metadata.mutation_name == "createContact"
    assert metadata.input_type == "app.type_create_contact_input"
    assert metadata.success_type == "CreateContactSuccess"
```

#### GREEN: Minimal Implementation
```python
# src/reverse/sql_parser.py

import pglast
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FunctionParameter:
    name: str
    type: str

@dataclass
class ParsedFunction:
    name: str
    schema: str
    parameters: List[FunctionParameter]
    returns: str
    body: str
    pattern: Optional[str] = None

@dataclass
class FraiseSQLMetadata:
    mutation_name: str
    input_type: str
    success_type: str

class SQLFunctionParser:
    """Parse PostgreSQL functions using pglast"""

    def parse(self, sql: str) -> ParsedFunction:
        """Parse CREATE FUNCTION statement"""
        tree = pglast.parse_sql(sql)

        # Extract function definition
        stmt = tree[0].stmt
        func_name = stmt.funcname[-1].sval
        schema_name = stmt.funcname[-2].sval if len(stmt.funcname) > 1 else "public"

        # Extract parameters
        parameters = []
        for param in stmt.parameters:
            param_name = param.name
            param_type = self._extract_type(param.argType)
            parameters.append(FunctionParameter(param_name, param_type))

        # Extract return type
        returns = self._extract_type(stmt.returnType)

        # Extract body
        body = stmt.body

        # Detect pattern (heuristic)
        pattern = self._detect_pattern(func_name, schema_name, parameters)

        return ParsedFunction(
            name=func_name,
            schema=schema_name,
            parameters=parameters,
            returns=returns,
            body=body,
            pattern=pattern
        )

    def extract_fraiseql_metadata(self, sql: str) -> Optional[FraiseSQLMetadata]:
        """Extract @fraiseql:mutation metadata from COMMENT"""
        # Find COMMENT ON FUNCTION
        if "COMMENT ON FUNCTION" not in sql:
            return None

        # Parse comment text
        comment_start = sql.find("'", sql.find("COMMENT ON FUNCTION"))
        comment_end = sql.find("'", comment_start + 1)
        comment_text = sql[comment_start+1:comment_end]

        # Extract metadata fields
        if "@fraiseql:mutation" not in comment_text:
            return None

        metadata = {}
        for line in comment_text.split("\n"):
            if "name:" in line:
                metadata["mutation_name"] = line.split("name:")[1].strip()
            elif "input_type:" in line:
                metadata["input_type"] = line.split("input_type:")[1].strip()
            elif "success_type:" in line:
                metadata["success_type"] = line.split("success_type:")[1].strip()

        return FraiseSQLMetadata(**metadata)

    def _extract_type(self, type_node) -> str:
        """Extract type name from AST node"""
        # Simplified - full implementation handles arrays, composites, etc.
        if hasattr(type_node, 'names'):
            return '.'.join([n.sval for n in type_node.names])
        return str(type_node)

    def _detect_pattern(self, name: str, schema: str, parameters: List[FunctionParameter]) -> str:
        """Detect function pattern using heuristics"""
        if schema == "app" and len(parameters) == 3:
            if parameters[0].type == "UUID" and parameters[2].type == "JSONB":
                return "app_wrapper"

        if len(parameters) == 4 and parameters[1].type.startswith("app.type_"):
            return "core_logic"

        return "unknown"
```

#### REFACTOR: Clean Up & Optimize
- Add comprehensive type extraction (arrays, composites, enums)
- Handle edge cases (function overloading, default parameters)
- Improve pattern detection heuristics
- Add caching for performance

#### QA: Verify Phase Completion
```bash
# Run unit tests
uv run pytest tests/unit/reverse/test_sql_parser.py -v

# Run integration tests with real SQL files
uv run pytest tests/integration/reverse/test_parse_generated_functions.py -v

# Verify all patterns detected correctly
# Verify pglast dependency installed
```

---

### Phase 2: Composite Type Discovery (RED → GREEN → REFACTOR → QA)

**Objective**: Extract composite type definitions and field information

#### RED: Write Failing Tests
```python
# tests/unit/reverse/test_type_extractor.py

def test_extract_composite_type():
    """Should parse CREATE TYPE and extract fields"""
    sql = """
    CREATE TYPE app.type_create_contact_input AS (
        email TEXT,
        first_name TEXT,
        last_name TEXT,
        company_id UUID,
        status TEXT,
        phone TEXT
    );
    """

    extractor = CompositeTypeExtractor()
    result = extractor.extract(sql)

    assert result.name == "type_create_contact_input"
    assert result.schema == "app"
    assert len(result.fields) == 6
    assert result.fields["email"] == "TEXT"
    assert result.fields["company_id"] == "UUID"

def test_map_type_to_specql_field():
    """Should map PostgreSQL type to SpecQL field type"""
    mapper = TypeMapper()

    assert mapper.to_specql("TEXT") == "text"
    assert mapper.to_specql("UUID", field_name="company_id") == "ref(Company)"
    assert mapper.to_specql("INTEGER") == "integer"
```

#### GREEN: Minimal Implementation
```python
# src/reverse/type_extractor.py

from dataclasses import dataclass
from typing import Dict
import pglast

@dataclass
class CompositeType:
    name: str
    schema: str
    fields: Dict[str, str]  # field_name -> type

class CompositeTypeExtractor:
    """Extract composite type definitions"""

    def extract(self, sql: str) -> CompositeType:
        """Parse CREATE TYPE AS statement"""
        tree = pglast.parse_sql(sql)
        stmt = tree[0].stmt

        type_name = stmt.typeName[-1].sval
        schema_name = stmt.typeName[-2].sval if len(stmt.typeName) > 1 else "public"

        fields = {}
        for attr in stmt.colDefList:
            field_name = attr.colName
            field_type = self._extract_type(attr.typeName)
            fields[field_name] = field_type

        return CompositeType(type_name, schema_name, fields)

    def _extract_type(self, type_node) -> str:
        """Extract type name"""
        if hasattr(type_node, 'names'):
            return '.'.join([n.sval for n in type_node.names])
        return str(type_node)

class TypeMapper:
    """Map PostgreSQL types to SpecQL field types"""

    def to_specql(self, pg_type: str, field_name: str = "") -> str:
        """Convert PostgreSQL type to SpecQL field type"""
        pg_type = pg_type.upper()

        # Direct mappings
        direct_map = {
            "TEXT": "text",
            "VARCHAR": "text",
            "INTEGER": "integer",
            "BIGINT": "integer",
            "BOOLEAN": "boolean",
            "TIMESTAMP": "timestamp",
            "DATE": "date",
            "JSONB": "jsonb",
        }

        if pg_type in direct_map:
            return direct_map[pg_type]

        # UUID heuristic: if field ends with _id, it's a reference
        if pg_type == "UUID":
            if field_name.endswith("_id"):
                # Extract entity name from field name
                entity = field_name[:-3]  # Remove _id
                entity = entity.replace("_", " ").title().replace(" ", "")
                return f"ref({entity})"
            return "uuid"

        return "text"  # Fallback
```

#### REFACTOR: Improve Heuristics
- Add enum detection and extraction
- Improve reference detection (use foreign key constraints)
- Handle rich types (money, dimensions, contact_info)
- Add confidence scoring for mappings

#### QA: Verify Phase Completion
```bash
uv run pytest tests/unit/reverse/test_type_extractor.py -v
uv run pytest tests/integration/reverse/test_type_mapping.py -v
```

---

### Phase 3: Business Logic Extraction (RED → GREEN → REFACTOR → QA)

**Objective**: Extract validation, insert, update steps from function body

#### RED: Write Failing Tests
```python
# tests/unit/reverse/test_logic_extractor.py

def test_extract_validate_step():
    """Should detect validation step from IF NOT condition"""
    body = """
    IF NOT (v_current_status = 'lead') THEN
        RETURN app.log_and_return_mutation(
            ..., 'validation_error', ...
        );
    END IF;
    """

    extractor = LogicExtractor()
    steps = extractor.extract_steps(body)

    assert len(steps) == 1
    assert steps[0].type == "validate"
    assert steps[0].condition == "status = 'lead'"

def test_extract_insert_step():
    """Should detect INSERT step"""
    body = """
    INSERT INTO crm.tb_contact (
        id, tenant_id, email, first_name
    ) VALUES (
        v_contact_id, auth_tenant_id, input_data.email, input_data.first_name
    );
    """

    extractor = LogicExtractor()
    steps = extractor.extract_steps(body)

    assert len(steps) == 1
    assert steps[0].type == "insert"
    assert steps[0].entity == "Contact"
    assert "email" in steps[0].fields
    assert "first_name" in steps[0].fields

def test_extract_update_step():
    """Should detect UPDATE step"""
    body = """
    UPDATE crm.tb_contact
    SET status = 'qualified', updated_at = now()
    WHERE id = v_contact_id;
    """

    extractor = LogicExtractor()
    steps = extractor.extract_steps(body)

    assert len(steps) == 1
    assert steps[0].type == "update"
    assert steps[0].entity == "Contact"
    assert "status" in steps[0].fields
```

#### GREEN: Minimal Implementation
```python
# src/reverse/logic_extractor.py

from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class ActionStep:
    type: str  # validate, insert, update, call, notify
    condition: Optional[str] = None
    entity: Optional[str] = None
    fields: Optional[List[str]] = None
    target: Optional[str] = None

class LogicExtractor:
    """Extract business logic steps from function body"""

    def extract_steps(self, body: str) -> List[ActionStep]:
        """Parse function body and extract steps"""
        steps = []

        # Detect validation steps
        validate_pattern = r"IF NOT \((.*?)\) THEN.*?validation_error"
        for match in re.finditer(validate_pattern, body, re.DOTALL):
            condition = match.group(1).strip()
            # Clean up condition (remove v_ prefixes, simplify)
            condition = self._clean_condition(condition)
            steps.append(ActionStep(type="validate", condition=condition))

        # Detect INSERT steps
        insert_pattern = r"INSERT INTO (\w+)\.(\w+)\s*\((.*?)\)\s*VALUES"
        for match in re.finditer(insert_pattern, body, re.DOTALL):
            schema = match.group(1)
            table = match.group(2)
            fields_str = match.group(3)

            entity = self._table_to_entity(table)
            fields = [f.strip() for f in fields_str.split(",")]
            fields = [f for f in fields if f not in ["id", "tenant_id", "created_at", "created_by"]]

            steps.append(ActionStep(type="insert", entity=entity, fields=fields))

        # Detect UPDATE steps
        update_pattern = r"UPDATE (\w+)\.(\w+)\s+SET\s+(.*?)\s+WHERE"
        for match in re.finditer(update_pattern, body, re.DOTALL):
            schema = match.group(1)
            table = match.group(2)
            set_clause = match.group(3)

            entity = self._table_to_entity(table)
            fields = self._extract_updated_fields(set_clause)

            steps.append(ActionStep(type="update", entity=entity, fields=fields))

        return steps

    def _clean_condition(self, condition: str) -> str:
        """Clean up validation condition for SpecQL format"""
        # Remove variable prefixes
        condition = re.sub(r"v_current_", "", condition)
        condition = re.sub(r"v_", "", condition)
        return condition.strip()

    def _table_to_entity(self, table: str) -> str:
        """Convert table name to entity name"""
        if table.startswith("tb_"):
            entity = table[3:]
        elif table.startswith("tv_"):
            entity = table[3:]
        else:
            entity = table

        # Convert to PascalCase
        return entity.replace("_", " ").title().replace(" ", "")

    def _extract_updated_fields(self, set_clause: str) -> List[str]:
        """Extract field names from SET clause"""
        fields = []
        for assignment in set_clause.split(","):
            field = assignment.split("=")[0].strip()
            if field not in ["updated_at", "updated_by"]:
                fields.append(field)
        return fields
```

#### REFACTOR: Improve Detection
- Use AST parsing instead of regex for robustness
- Handle complex expressions (CASE, subqueries)
- Detect foreach loops
- Detect call_service steps
- Add confidence scoring

#### QA: Verify Phase Completion
```bash
uv run pytest tests/unit/reverse/test_logic_extractor.py -v
uv run pytest tests/integration/reverse/test_extract_actions.py -v
```

---

### Phase 4: YAML Generation (RED → GREEN → REFACTOR → QA)

**Objective**: Generate SpecQL YAML from extracted AST

#### RED: Write Failing Tests
```python
# tests/unit/reverse/test_yaml_generator.py

def test_generate_entity_yaml():
    """Should generate complete SpecQL YAML from parsed data"""
    entity_data = {
        "name": "Contact",
        "schema": "crm",
        "fields": {
            "email": "text",
            "first_name": "text",
            "last_name": "text",
            "company": "ref(Company)",
            "status": "enum(lead, qualified, customer)",
            "phone": "text"
        },
        "actions": [
            {
                "name": "create_contact",
                "steps": [
                    {"type": "validate", "condition": "company_id IS NOT NULL"},
                    {"type": "insert", "entity": "Contact",
                     "fields": ["email", "first_name", "last_name", "company", "status", "phone"]}
                ]
            },
            {
                "name": "qualify_lead",
                "steps": [
                    {"type": "validate", "condition": "status = 'lead'"},
                    {"type": "update", "entity": "Contact", "fields": ["status"]}
                ]
            }
        ]
    }

    generator = YAMLGenerator()
    yaml_output = generator.generate(entity_data)

    assert "entity: Contact" in yaml_output
    assert "schema: crm" in yaml_output
    assert "email: text" in yaml_output
    assert "company: ref(Company)" in yaml_output
    assert "- name: create_contact" in yaml_output
    assert "validate: company_id IS NOT NULL" in yaml_output
```

#### GREEN: Minimal Implementation
```python
# src/reverse/yaml_generator.py

import yaml
from typing import Dict, List, Any

class YAMLGenerator:
    """Generate SpecQL YAML from extracted entity data"""

    def generate(self, entity_data: Dict[str, Any]) -> str:
        """Generate SpecQL YAML string"""
        spec = {
            "entity": entity_data["name"],
            "schema": entity_data["schema"],
            "fields": entity_data["fields"],
            "actions": []
        }

        # Convert actions to SpecQL format
        for action in entity_data["actions"]:
            action_spec = {
                "name": action["name"],
                "steps": []
            }

            for step in action["steps"]:
                if step["type"] == "validate":
                    action_spec["steps"].append({
                        "validate": step["condition"]
                    })
                elif step["type"] == "insert":
                    fields_str = ", ".join(step["fields"])
                    action_spec["steps"].append({
                        "insert": f"{step['entity']} SET {fields_str}"
                    })
                elif step["type"] == "update":
                    fields_str = ", ".join(step["fields"])
                    action_spec["steps"].append({
                        "update": f"{step['entity']} SET {fields_str}"
                    })

            spec["actions"].append(action_spec)

        # Generate YAML with proper formatting
        return yaml.dump(spec, default_flow_style=False, sort_keys=False)
```

#### REFACTOR: Improve Formatting
- Add comments explaining extracted patterns
- Add confidence indicators for uncertain mappings
- Format for readability (proper indentation, line breaks)
- Add metadata (source file, extraction date)

#### QA: Verify Phase Completion
```bash
uv run pytest tests/unit/reverse/test_yaml_generator.py -v

# Verify round-trip: SQL → YAML → SQL produces equivalent output
uv run pytest tests/integration/reverse/test_roundtrip.py -v
```

---

### Phase 5: CLI Integration (RED → GREEN → REFACTOR → QA)

**Objective**: Add CLI commands for reverse engineering

#### RED: Write Failing Tests
```python
# tests/unit/cli/test_reverse_command.py

def test_reverse_command_basic():
    """Should reverse engineer SQL to YAML"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "reverse",
        "migrations/crm/01203_contact/012036_fn_contact.sql",
        "--output", "entities/contact.yaml"
    ])

    assert result.exit_code == 0
    assert "✅ Generated entities/contact.yaml" in result.output

    # Verify YAML file created
    assert Path("entities/contact.yaml").exists()

def test_scan_command():
    """Should scan directory and discover functions"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "scan",
        "migrations/",
        "--output", "discovered.json"
    ])

    assert result.exit_code == 0
    assert "📊 Discovered 15 functions" in result.output
```

#### GREEN: Minimal Implementation
```python
# src/cli/reverse.py

import click
from pathlib import Path
from src.reverse import SQLFunctionParser, CompositeTypeExtractor, LogicExtractor, YAMLGenerator

@click.group()
def reverse_cli():
    """Reverse engineering commands"""
    pass

@reverse_cli.command(name="scan")
@click.argument("reference_dir", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), help="Output JSON file")
@click.option("--format", type=click.Choice(["json", "table"]), default="table")
def scan(reference_dir: str, output: str, format: str):
    """Scan reference implementation and discover functions

    Example:
        specql scan db/reference/ --output discovered.json
    """
    click.secho("🔍 Scanning reference implementation...", fg="blue", bold=True)

    parser = SQLFunctionParser()
    type_extractor = CompositeTypeExtractor()

    reference_path = Path(reference_dir)
    discovered = {
        "functions": [],
        "composite_types": []
    }

    # Scan SQL files
    for sql_file in reference_path.rglob("*.sql"):
        content = sql_file.read_text()

        # Parse functions
        if "CREATE FUNCTION" in content or "CREATE OR REPLACE FUNCTION" in content:
            try:
                func = parser.parse(content)
                discovered["functions"].append({
                    "name": f"{func.schema}.{func.name}",
                    "signature": f"{func.schema}.{func.name}({', '.join([p.type for p in func.parameters])})",
                    "returns": func.returns,
                    "pattern": func.pattern,
                    "file": str(sql_file)
                })
            except Exception as e:
                click.echo(f"  ⚠️  Failed to parse {sql_file}: {e}")

        # Parse composite types
        if "CREATE TYPE" in content:
            try:
                comp_type = type_extractor.extract(content)
                discovered["composite_types"].append({
                    "name": f"{comp_type.schema}.{comp_type.name}",
                    "fields": comp_type.fields,
                    "file": str(sql_file)
                })
            except Exception as e:
                click.echo(f"  ⚠️  Failed to parse type in {sql_file}: {e}")

    # Output results
    if format == "json" and output:
        import json
        Path(output).write_text(json.dumps(discovered, indent=2))
        click.secho(f"✅ Saved discovery results to {output}", fg="green")
    else:
        # Table format
        click.echo(f"\n📊 Discovered {len(discovered['functions'])} functions")
        click.echo(f"📊 Discovered {len(discovered['composite_types'])} composite types")

        click.echo("\nFunctions:")
        for func in discovered["functions"]:
            click.echo(f"  • {func['name']} [{func['pattern']}]")

    return 0

@reverse_cli.command(name="reverse")
@click.argument("sql_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output", type=click.Path(), required=True, help="Output YAML file")
@click.option("--confidence-threshold", type=float, default=0.7, help="Minimum confidence for extraction")
def reverse(sql_files: tuple, output: str, confidence_threshold: float):
    """Reverse engineer SQL functions to SpecQL YAML

    Examples:
        specql reverse migrations/crm/01203_contact/*.sql --output entities/contact.yaml
        specql reverse db/reference/fn_contact.sql --output entities/contact.yaml
    """
    click.secho("🔄 Reverse engineering SQL to SpecQL YAML...", fg="blue", bold=True)

    parser = SQLFunctionParser()
    type_extractor = CompositeTypeExtractor()
    logic_extractor = LogicExtractor()
    yaml_gen = YAMLGenerator()

    # TODO: Implement full extraction pipeline
    # 1. Parse all SQL files
    # 2. Group functions by entity
    # 3. Extract composite types
    # 4. Extract business logic
    # 5. Generate YAML

    click.secho(f"✅ Generated {output}", fg="green", bold=True)
    return 0
```

#### REFACTOR: Add Progress & Error Handling
- Show progress bars for large scans
- Handle missing files gracefully
- Add dry-run mode
- Add verbose logging

#### QA: Verify Phase Completion
```bash
uv run pytest tests/unit/cli/test_reverse_command.py -v
uv run pytest tests/integration/cli/test_reverse_e2e.py -v

# Manual verification
specql scan migrations/ --output discovered.json
specql reverse migrations/crm/01203_contact/*.sql --output entities/contact_reversed.yaml
```

---

### Phase 6: Comparison Engine (RED → GREEN → REFACTOR → QA)

**Objective**: Compare generated vs reference implementations

#### RED: Write Failing Tests
```python
# tests/unit/comparison/test_comparison_engine.py

def test_compare_function_signatures():
    """Should detect signature differences"""
    ref_func = ParsedFunction(name="create_contact", schema="app", ...)
    gen_func = ParsedFunction(name="create_contact", schema="app", ...)

    engine = ComparisonEngine()
    result = engine.compare_signatures(ref_func, gen_func)

    assert result.match == True
    assert result.confidence == 1.0

def test_compare_logic_steps():
    """Should compare business logic steps"""
    ref_steps = [
        ActionStep(type="validate", condition="status = 'lead'"),
        ActionStep(type="update", entity="Contact", fields=["status"])
    ]
    gen_steps = [
        ActionStep(type="validate", condition="status = 'lead'"),
        ActionStep(type="update", entity="Contact", fields=["status"])
    ]

    engine = ComparisonEngine()
    result = engine.compare_steps(ref_steps, gen_steps)

    assert result.match == True
    assert result.similarity == 1.0
```

#### GREEN: Minimal Implementation
```python
# src/comparison/engine.py

from dataclasses import dataclass
from typing import List, Optional
from difflib import SequenceMatcher

@dataclass
class ComparisonResult:
    match: bool
    confidence: float
    differences: List[str]
    suggestions: List[str]

class ComparisonEngine:
    """Compare reference vs generated implementations"""

    def compare_signatures(self, ref_func, gen_func) -> ComparisonResult:
        """Compare function signatures"""
        differences = []

        if ref_func.name != gen_func.name:
            differences.append(f"Name: {ref_func.name} != {gen_func.name}")

        if ref_func.schema != gen_func.schema:
            differences.append(f"Schema: {ref_func.schema} != {gen_func.schema}")

        if len(ref_func.parameters) != len(gen_func.parameters):
            differences.append(
                f"Parameter count: {len(ref_func.parameters)} != {len(gen_func.parameters)}"
            )

        if ref_func.returns != gen_func.returns:
            differences.append(f"Return type: {ref_func.returns} != {gen_func.returns}")

        match = len(differences) == 0
        confidence = 1.0 if match else 0.5

        return ComparisonResult(
            match=match,
            confidence=confidence,
            differences=differences,
            suggestions=[]
        )

    def compare_steps(self, ref_steps: List, gen_steps: List) -> ComparisonResult:
        """Compare business logic steps"""
        if len(ref_steps) != len(gen_steps):
            return ComparisonResult(
                match=False,
                confidence=0.5,
                differences=[f"Step count: {len(ref_steps)} != {len(gen_steps)}"],
                suggestions=["Check if steps are missing or extra"]
            )

        differences = []
        for i, (ref, gen) in enumerate(zip(ref_steps, gen_steps)):
            if ref.type != gen.type:
                differences.append(f"Step {i}: type {ref.type} != {gen.type}")

            if ref.type == "validate" and ref.condition != gen.condition:
                similarity = self._text_similarity(ref.condition, gen.condition)
                if similarity < 0.8:
                    differences.append(
                        f"Step {i}: condition differs (similarity: {similarity:.0%})"
                    )

        match = len(differences) == 0
        confidence = 1.0 - (len(differences) / max(len(ref_steps), 1))

        return ComparisonResult(
            match=match,
            confidence=confidence,
            differences=differences,
            suggestions=[]
        )

    def _text_similarity(self, a: str, b: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        return SequenceMatcher(None, a, b).ratio()
```

#### REFACTOR: Advanced Comparison
- Semantic equivalence detection (not just text matching)
- AST-level comparison
- Performance comparison (explain plans)
- Security comparison (SQL injection risks)

#### QA: Verify Phase Completion
```bash
uv run pytest tests/unit/comparison/test_comparison_engine.py -v
uv run pytest tests/integration/comparison/test_compare_e2e.py -v
```

---

### Phase 7: Report Generation (RED → GREEN → REFACTOR → QA)

**Objective**: Generate visual comparison reports

#### RED: Write Failing Tests
```python
# tests/unit/comparison/test_report_generator.py

def test_generate_terminal_report():
    """Should generate colored terminal report"""
    comparison = {
        "entity": "Contact",
        "schema_match": True,
        "functions": [
            {
                "name": "create_contact",
                "signature_match": True,
                "logic_similarity": 0.95
            }
        ]
    }

    generator = ReportGenerator()
    report = generator.generate_terminal_report(comparison)

    assert "Contact" in report
    assert "✅" in report
    assert "95%" in report

def test_generate_html_report():
    """Should generate HTML report with side-by-side diff"""
    # Similar test for HTML generation
    pass
```

#### GREEN: Minimal Implementation
```python
# src/comparison/report_generator.py

from typing import Dict, Any

class ReportGenerator:
    """Generate comparison reports in various formats"""

    def generate_terminal_report(self, comparison: Dict[str, Any]) -> str:
        """Generate terminal-friendly report with colors"""
        lines = []

        entity = comparison["entity"]
        lines.append(f"📊 Comparison Report: {entity}")
        lines.append("━" * 60)
        lines.append("")

        # Schema match
        if comparison.get("schema_match"):
            lines.append("✅ Schema Structure: MATCH")
        else:
            lines.append("❌ Schema Structure: MISMATCH")

        # Functions
        for func in comparison.get("functions", []):
            name = func["name"]
            sig_match = func.get("signature_match", False)
            similarity = func.get("logic_similarity", 0.0)

            if sig_match and similarity > 0.9:
                status = "✅"
            elif similarity > 0.7:
                status = "⚠️ "
            else:
                status = "❌"

            lines.append(f"\n{status} Function: {name}")
            lines.append(f"   ├─ Signature: {'MATCH' if sig_match else 'MISMATCH'}")
            lines.append(f"   └─ Logic: {similarity:.0%} SIMILAR")

            if "differences" in func:
                for diff in func["differences"]:
                    lines.append(f"      ⚠️  {diff}")

            if "suggestions" in func:
                for suggestion in func["suggestions"]:
                    lines.append(f"      💡 {suggestion}")

        # Overall
        overall = comparison.get("overall_match", 0.0)
        lines.append(f"\n📈 Overall Match: {overall:.0%}")
        lines.append(f"   Confidence: {'HIGH' if overall > 0.8 else 'MEDIUM' if overall > 0.6 else 'LOW'}")

        return "\n".join(lines)

    def generate_html_report(self, comparison: Dict[str, Any]) -> str:
        """Generate HTML report with side-by-side diff"""
        # TODO: Implement HTML generation with:
        # - Side-by-side code comparison
        # - Syntax highlighting
        # - Interactive collapsible sections
        # - Export to PDF option
        pass
```

#### REFACTOR: Rich Reports
- Add syntax highlighting (pygments)
- Add side-by-side diff view
- Add interactive HTML with JavaScript
- Add PDF export option

#### QA: Verify Phase Completion
```bash
uv run pytest tests/unit/comparison/test_report_generator.py -v

# Manual verification
specql compare entities/contact.yaml --reference migrations/ --report report.html
```

---

### Phase 8: Test Execution Integration (RED → GREEN → REFACTOR → QA)

**Objective**: Automatically run generated tests

#### RED: Write Failing Tests
```python
# tests/unit/cli/test_test_command.py

def test_run_pgtap_tests():
    """Should run pgTAP tests and report results"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "test",
        "entities/contact.yaml",
        "--run",
        "--db-url", "postgresql://localhost/testdb"
    ])

    assert result.exit_code == 0
    assert "15/15 passed" in result.output
```

#### GREEN: Minimal Implementation
```python
# src/cli/test_runner.py

import subprocess
import click
from pathlib import Path

class TestRunner:
    """Run generated tests and report results"""

    def run_pgtap(self, test_file: Path, db_url: str) -> dict:
        """Run pgTAP test file"""
        cmd = ["pg_prove", "-d", db_url, str(test_file)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        # Parse output
        passed = result.stdout.count("ok")
        failed = result.stdout.count("not ok")

        return {
            "passed": passed,
            "failed": failed,
            "output": result.stdout,
            "success": result.returncode == 0
        }

    def run_pytest(self, test_file: Path) -> dict:
        """Run pytest test file"""
        cmd = ["pytest", str(test_file), "-v", "--tb=short"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        # Parse output
        passed = result.stdout.count("PASSED")
        failed = result.stdout.count("FAILED")

        return {
            "passed": passed,
            "failed": failed,
            "output": result.stdout,
            "success": result.returncode == 0
        }

# Add to generate.py
@cli.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--run", is_flag=True, help="Run tests after generating")
@click.option("--db-url", help="Database connection URL")
def test(entity_files: tuple, run: bool, db_url: str):
    """Generate and optionally run tests"""
    # Generate tests (existing code)
    # ...

    if run:
        if not db_url:
            click.secho("❌ --db-url required to run tests", fg="red")
            return 1

        runner = TestRunner()

        # Run pgTAP tests
        pgtap_results = runner.run_pgtap(pgtap_file, db_url)
        click.echo(f"\n🏃 pgTAP: {pgtap_results['passed']}/{pgtap_results['passed'] + pgtap_results['failed']} passed")

        # Run pytest tests
        pytest_results = runner.run_pytest(pytest_file)
        click.echo(f"🏃 Pytest: {pytest_results['passed']}/{pytest_results['passed'] + pytest_results['failed']} passed")
```

#### REFACTOR: Enhance Test Runner
- Add parallel test execution
- Add coverage reporting
- Add test result caching
- Add CI/CD integration hooks

#### QA: Verify Phase Completion
```bash
uv run pytest tests/unit/cli/test_test_command.py -v
uv run pytest tests/integration/cli/test_test_execution_e2e.py -v

# Manual verification with real database
specql test entities/contact.yaml --run --db-url postgresql://localhost/specql_test
```

---

## 📦 Dependencies

### New Python Libraries
```toml
# pyproject.toml additions

[project.dependencies]
pglast = "^6.3"  # PostgreSQL SQL parser
pygments = "^2.17"  # Syntax highlighting for reports
difflib = "^3.11"  # Text comparison
jinja2 = "^3.1"  # HTML template generation
```

### Installation
```bash
uv add pglast pygments jinja2
```

---

## 🧪 Testing Strategy

### Unit Tests
- **Parser tests**: Verify SQL parsing accuracy
- **Extractor tests**: Verify metadata extraction
- **Generator tests**: Verify YAML generation
- **Comparison tests**: Verify diff detection

### Integration Tests
- **Round-trip tests**: SQL → YAML → SQL produces equivalent code
- **E2E tests**: Full reverse engineering pipeline
- **Comparison tests**: Real generated vs reference comparison

### Performance Tests
- **Large codebases**: 100+ functions
- **Complex functions**: Nested logic, loops
- **Parsing speed**: Target <1s per function

---

## 📈 Success Metrics

1. **Parsing Accuracy**: >95% of generated functions parse successfully
2. **Extraction Confidence**: >80% of steps extracted with high confidence
3. **Round-Trip Equivalence**: >90% functional equivalence after SQL→YAML→SQL
4. **Performance**: <5s for full reverse engineering of 50-function codebase
5. **Comparison Accuracy**: >95% true positive rate for detecting differences

---

## 🚀 Future Enhancements

### Phase 9+: Advanced Features
1. **Multi-Framework Support**: Extend to Django, Rails, Prisma
2. **Learning Mode**: AI-assisted pattern detection
3. **Auto-Fix**: Suggest and apply corrections automatically
4. **Schema Migration**: Generate ALTER scripts for differences
5. **Visual Schema Designer**: Interactive UI for editing and comparing
6. **CI/CD Integration**: GitHub Actions, GitLab CI for automated comparison
7. **Benchmark Suite**: Performance comparison between reference and generated

---

## 💡 Key Insights

### Why This Is Achievable (8/10 Feasibility)

1. **Structured Target**: PostgreSQL functions follow consistent patterns
2. **Existing AST**: SpecQL's AST already models the domain
3. **Pattern-Based**: Generators use predictable patterns, making reverse-engineering tractable
4. **Strong Typing**: Composite types provide clear hints
5. **Metadata**: FraiseQL comments provide discovery hints

### Why Not 10/10

1. **Heuristics Required**: Some patterns need heuristic detection
2. **Information Loss**: SQL is imperative, SpecQL is declarative - perfect round-trip impossible
3. **Custom Code**: Complex custom logic may not map cleanly

### Mitigation Strategies

1. **Confidence Scoring**: Report confidence for each extracted element
2. **Manual Review**: Clearly mark uncertain extractions
3. **Iterative Refinement**: Learn from corrections over time
4. **Human-in-Loop**: Allow manual adjustments to extraction

---

## 🎓 Learning Outcomes

For **AI Agents**:
- Clear JSON output for programmatic processing
- Confidence scores for decision-making
- Structured diff reports for automated actions

For **Human Developers**:
- Visual comparison reports
- Suggested fixes and improvements
- Learning tool for understanding SpecQL patterns

For **Teams**:
- Migration path from legacy SQL
- Quality assurance for generated code
- Documentation of design decisions

---

## 📋 Implementation Checklist

### Phase 1: SQL Parsing ✅
- [ ] Install pglast dependency
- [ ] Implement SQLFunctionParser
- [ ] Extract function metadata
- [ ] Detect function patterns (app_wrapper, core_logic)
- [ ] Extract FraiseQL metadata from comments
- [ ] Write unit tests
- [ ] Write integration tests

### Phase 2: Type Discovery ✅
- [ ] Implement CompositeTypeExtractor
- [ ] Implement TypeMapper
- [ ] Handle enum types
- [ ] Handle rich types (money, dimensions)
- [ ] Improve reference detection using FKs
- [ ] Write unit tests

### Phase 3: Logic Extraction ✅
- [ ] Implement LogicExtractor
- [ ] Detect validate steps
- [ ] Detect insert steps
- [ ] Detect update steps
- [ ] Detect call_service steps
- [ ] Detect foreach loops
- [ ] Write unit tests

### Phase 4: YAML Generation ✅
- [ ] Implement YAMLGenerator
- [ ] Generate entity section
- [ ] Generate fields section
- [ ] Generate actions section
- [ ] Add comments and metadata
- [ ] Write unit tests
- [ ] Test round-trip equivalence

### Phase 5: CLI Integration ✅
- [ ] Add `specql scan` command
- [ ] Add `specql reverse` command
- [ ] Add progress indicators
- [ ] Add error handling
- [ ] Write CLI tests

### Phase 6: Comparison Engine ✅
- [ ] Implement ComparisonEngine
- [ ] Compare function signatures
- [ ] Compare business logic
- [ ] Calculate similarity scores
- [ ] Generate suggestions
- [ ] Write unit tests

### Phase 7: Report Generation ✅
- [ ] Implement terminal report generator
- [ ] Add syntax highlighting
- [ ] Implement HTML report generator
- [ ] Add side-by-side diff view
- [ ] Write report tests

### Phase 8: Test Execution ✅
- [ ] Implement TestRunner
- [ ] Integrate pgTAP execution
- [ ] Integrate pytest execution
- [ ] Add coverage reporting
- [ ] Write execution tests

---

**Last Updated**: 2025-11-12
**Status**: Ready for Implementation
**Feasibility**: 8/10 - High Confidence
**Estimated Effort**: 4-6 weeks with TDD approach
