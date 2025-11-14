# Week 11: Universal Test Specification & Reverse Engineering

**Phase**: Testing Infrastructure & Cross-Language Validation
**Priority**: Critical - Enables migration validation and multi-language test portability
**Timeline**: 5 working days
**Impact**: Universal test specification format, test reverse engineering, migration validation

---

## 🎯 Executive Summary

**Goal**: Create universal test specification format and reverse engineering capabilities:

```bash
# Reverse engineer existing tests → Universal TestSpec
specql reverse-tests tests/pgtap/contact_test.sql --output test-specs/contact.yaml
specql reverse-tests tests/pytest/test_contact.py --output test-specs/contact.yaml

# Validate migration preserves test semantics
specql validate-migration \
  --reference-tests reference_app/tests/ \
  --generated-tests generated/tests/ \
  --coverage-report coverage.json

# Generate tests in target language from TestSpec
specql generate-tests test-specs/**/*.yaml --format pytest --output tests/
specql generate-tests test-specs/**/*.yaml --format pgtap --output tests/
```

**Strategic Value**:
- **Migration Validation**: Prove migrated code maintains test coverage
- **Cross-Language Tests**: Write tests once, generate for SQL/Python/TypeScript
- **Test Pattern Library**: Catalog and reuse common test patterns
- **Quality Assurance**: Systematic test coverage analysis
- **Documentation**: Tests as executable specifications

**The Vision**:
```
Just as SpecQL has:
  Entity YAML → SQL Schema (generation) ✅
  SQL Schema → Entity YAML (reverse engineering) ✅

It should also have:
  TestSpec YAML → pytest/pgTAP (generation) ✅ EXISTS
  pytest/pgTAP → TestSpec YAML (reverse engineering) ❌ NEW (Week 11)

Then extend to ANY language's tests → Universal TestSpec
```

---

## 📊 Current State Analysis

### ✅ What We Have (Reusable)

1. **Test Generation Infrastructure** (`src/testing/`):
   - `pytest_generator.py` - Generates Python integration tests ✅
   - `pgtap_generator.py` - Generates SQL pgTAP tests ✅
   - `seed_generator.py` - Test data generation ✅
   - `metadata_generator.py` - Test configuration ✅

2. **Reverse Engineering Pipeline** (`src/reverse_engineering/`):
   - 3-stage pipeline: Parser → Mapper → Enhancer ✅
   - Protocol-based architecture (`protocols.py`) ✅
   - SQL reverse engineering (`sql_ast_parser.py`) ✅
   - Python reverse engineering (`python_ast_parser.py`) ✅
   - AI enhancement (`ai_enhancer.py`) ✅

3. **Pattern Infrastructure**:
   - Pattern library with PostgreSQL + pgvector ✅
   - Pattern matching and recommendations ✅
   - Pattern discovery from code ✅

### 🔴 What We Need (New)

1. **Universal Test Specification** (`src/testing/spec/`):
   - `TestSpec` AST (test scenarios, assertions, fixtures)
   - Test pattern definitions (CRUD, validation, state_machine)
   - Cross-language test equivalence mapping

2. **Test Reverse Engineering** (`src/reverse_engineering/tests/`):
   - pgTAP test parser → TestSpec
   - pytest parser → TestSpec
   - Test pattern detector
   - Test coverage analyzer

3. **Migration Validation** (`src/migration/`):
   - Test equivalence checker
   - Coverage comparison
   - Assertion mapping validator

---

## 🏗️ Architecture Design

### Universal TestSpec AST

```python
@dataclass
class TestSpec:
    """Universal test specification (language-agnostic)"""
    test_name: str
    entity_name: str
    test_type: TestType  # CRUD, validation, workflow, integration
    scenarios: List[TestScenario]
    fixtures: List[TestFixture]
    metadata: Dict[str, Any]

@dataclass
class TestScenario:
    """Individual test case"""
    scenario_name: str
    description: str
    category: ScenarioCategory  # happy_path, error_case, edge_case, boundary
    setup_steps: List[TestStep]
    action_steps: List[TestStep]
    assertions: List[TestAssertion]
    teardown_steps: List[TestStep]

@dataclass
class TestAssertion:
    """Test assertion (language-agnostic)"""
    assertion_type: AssertionType  # equals, contains, throws, state_change, count
    target: str  # What's being asserted
    expected: Any  # Expected value/state
    actual: Optional[str] = None  # Actual value expression
    message: Optional[str] = None

class TestType(Enum):
    CRUD_CREATE = "crud_create"
    CRUD_READ = "crud_read"
    CRUD_UPDATE = "crud_update"
    CRUD_DELETE = "crud_delete"
    VALIDATION = "validation"
    STATE_MACHINE = "state_machine"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"

class ScenarioCategory(Enum):
    HAPPY_PATH = "happy_path"
    ERROR_CASE = "error_case"
    EDGE_CASE = "edge_case"
    BOUNDARY = "boundary"
    SECURITY = "security"
```

### Three-Stage Pipeline for Test Reverse Engineering

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Test Parser (Language-Specific)                       │
│ ┌──────────┐                                                    │
│ │ pgTAP    │──→ PgTAPTestParser ──→ ParsedTest                 │
│ │ pytest   │──→ PytestParser    ──→ ParsedTest                 │
│ │ Jest     │──→ JestParser      ──→ ParsedTest (future)        │
│ └──────────┘                                                    │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Test to TestSpec Mapper (Universal)                   │
│ ParsedTest ──→ TestSpec (scenarios, assertions, fixtures)      │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: Test Pattern Detection & Enhancement                  │
│ - Detect test patterns (CRUD, validation, workflow)            │
│ - Identify scenario categories (happy path, error cases)       │
│ - Suggest missing test cases                                   │
│ - Calculate test coverage gaps                                 │
└─────────────────────────────────────────────────────────────────┘
                           ↓
                    TestSpec YAML Output
```

### Bi-Directional Test Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Forward Generation (EXISTS - Week 5)                           │
│ TestSpec YAML → pytest_generator.py → Python Integration Tests │
│ TestSpec YAML → pgtap_generator.py  → SQL pgTAP Tests         │
└─────────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────────┐
│ Reverse Engineering (NEW - Week 11)                            │
│ Python Integration Tests → pytest_parser.py → TestSpec YAML   │
│ SQL pgTAP Tests         → pgtap_parser.py  → TestSpec YAML   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📅 Week 11: Day-by-Day Implementation

### Day 1: Universal TestSpec AST & Core Protocols

**Objective**: Define universal test specification format and protocols

**Morning: TestSpec Data Models (3h)**

```python
# src/testing/spec/test_spec_models.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class TestType(Enum):
    """Type of test being performed"""
    CRUD_CREATE = "crud_create"
    CRUD_READ = "crud_read"
    CRUD_UPDATE = "crud_update"
    CRUD_DELETE = "crud_delete"
    VALIDATION = "validation"
    STATE_MACHINE = "state_machine"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"

class ScenarioCategory(Enum):
    """Category of test scenario"""
    HAPPY_PATH = "happy_path"
    ERROR_CASE = "error_case"
    EDGE_CASE = "edge_case"
    BOUNDARY = "boundary"
    SECURITY = "security"
    PERFORMANCE = "performance"

class AssertionType(Enum):
    """Type of assertion"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    THROWS = "throws"
    NOT_THROWS = "not_throws"
    STATE_CHANGE = "state_change"
    COUNT = "count"
    MATCHES_PATTERN = "matches_pattern"
    TYPE_CHECK = "type_check"

@dataclass
class TestAssertion:
    """
    Universal test assertion

    Examples:
        # Equality assertion
        TestAssertion(
            assertion_type=AssertionType.EQUALS,
            target="result.status",
            expected="success",
            message="Action should return success status"
        )

        # Exception assertion
        TestAssertion(
            assertion_type=AssertionType.THROWS,
            target="action_call",
            expected="ValidationError",
            message="Should throw ValidationError for invalid status"
        )

        # State change assertion
        TestAssertion(
            assertion_type=AssertionType.STATE_CHANGE,
            target="contact.status",
            expected="qualified",
            actual="lead",
            message="Contact status should change from lead to qualified"
        )
    """
    assertion_type: AssertionType
    target: str  # What's being asserted (field, function call, etc.)
    expected: Any  # Expected value/state
    actual: Optional[str] = None  # Actual value expression (for state changes)
    message: Optional[str] = None  # Assertion failure message
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestStep:
    """
    Single step in test setup/action/teardown

    Examples:
        # Setup step: Create test data
        TestStep(
            step_type="setup",
            action="create_entity",
            entity="Contact",
            data={"email": "test@example.com", "status": "lead"}
        )

        # Action step: Call function
        TestStep(
            step_type="action",
            action="call_function",
            function="qualify_lead",
            parameters={"contact_id": "{{contact.id}}"}
        )

        # Teardown step: Clean up
        TestStep(
            step_type="teardown",
            action="delete_entity",
            entity="Contact",
            where="id = {{contact.id}}"
        )
    """
    step_type: str  # setup, action, teardown
    action: str  # create_entity, update_entity, call_function, etc.
    entity: Optional[str] = None
    function: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    where: Optional[str] = None
    store_result: Optional[str] = None  # Variable to store result
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestFixture:
    """
    Test fixture (setup data/state)

    Examples:
        # Entity fixture
        TestFixture(
            fixture_name="test_company",
            fixture_type="entity",
            entity="Company",
            data={"name": "Test Corp", "industry": "Technology"}
        )

        # Database fixture
        TestFixture(
            fixture_name="clean_database",
            fixture_type="database",
            setup_sql="DELETE FROM crm.tb_contact",
            teardown_sql=None
        )
    """
    fixture_name: str
    fixture_type: str  # entity, database, file, mock, etc.
    entity: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    setup_sql: Optional[str] = None
    teardown_sql: Optional[str] = None
    scope: str = "function"  # function, class, module, session
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestScenario:
    """
    Individual test scenario/case

    Example:
        TestScenario(
            scenario_name="test_qualify_lead_happy_path",
            description="Successfully qualify a lead contact",
            category=ScenarioCategory.HAPPY_PATH,
            setup_steps=[
                TestStep(step_type="setup", action="create_entity", ...)
            ],
            action_steps=[
                TestStep(step_type="action", action="call_function", ...)
            ],
            assertions=[
                TestAssertion(assertion_type=AssertionType.EQUALS, ...)
            ],
            teardown_steps=[]
        )
    """
    scenario_name: str
    description: str
    category: ScenarioCategory
    setup_steps: List[TestStep] = field(default_factory=list)
    action_steps: List[TestStep] = field(default_factory=list)
    assertions: List[TestAssertion] = field(default_factory=list)
    teardown_steps: List[TestStep] = field(default_factory=list)
    fixtures: List[str] = field(default_factory=list)  # Fixture names
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestSpec:
    """
    Complete test specification for an entity/feature

    Example:
        TestSpec(
            test_name="contact_qualification_tests",
            entity_name="Contact",
            test_type=TestType.WORKFLOW,
            scenarios=[
                TestScenario(scenario_name="test_qualify_lead_happy_path", ...),
                TestScenario(scenario_name="test_qualify_already_qualified_error", ...)
            ],
            fixtures=[
                TestFixture(fixture_name="test_company", ...)
            ],
            coverage={
                "actions_covered": ["qualify_lead"],
                "scenarios_covered": ["happy_path", "error_case"],
                "coverage_percentage": 85.0
            }
        )
    """
    test_name: str
    entity_name: str
    test_type: TestType
    scenarios: List[TestScenario] = field(default_factory=list)
    fixtures: List[TestFixture] = field(default_factory=list)
    setup_fixtures: List[str] = field(default_factory=list)
    teardown_fixtures: List[str] = field(default_factory=list)
    coverage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_yaml(self) -> str:
        """Convert to YAML format"""
        import yaml

        # Convert to dict representation
        spec_dict = {
            "test": self.test_name,
            "entity": self.entity_name,
            "type": self.test_type.value,
            "scenarios": [self._scenario_to_dict(s) for s in self.scenarios],
            "fixtures": [self._fixture_to_dict(f) for f in self.fixtures],
            "coverage": self.coverage,
            "_metadata": self.metadata
        }

        return yaml.dump(spec_dict, default_flow_style=False, sort_keys=False)

    def _scenario_to_dict(self, scenario: TestScenario) -> Dict[str, Any]:
        """Convert scenario to dict"""
        return {
            "name": scenario.scenario_name,
            "description": scenario.description,
            "category": scenario.category.value,
            "setup": [self._step_to_dict(s) for s in scenario.setup_steps],
            "action": [self._step_to_dict(s) for s in scenario.action_steps],
            "assertions": [self._assertion_to_dict(a) for a in scenario.assertions],
            "teardown": [self._step_to_dict(s) for s in scenario.teardown_steps],
        }

    def _step_to_dict(self, step: TestStep) -> Dict[str, Any]:
        """Convert step to dict"""
        result = {"action": step.action}
        if step.entity:
            result["entity"] = step.entity
        if step.function:
            result["function"] = step.function
        if step.parameters:
            result["parameters"] = step.parameters
        if step.data:
            result["data"] = step.data
        if step.where:
            result["where"] = step.where
        if step.store_result:
            result["store_as"] = step.store_result
        return result

    def _assertion_to_dict(self, assertion: TestAssertion) -> Dict[str, Any]:
        """Convert assertion to dict"""
        result = {
            "type": assertion.assertion_type.value,
            "target": assertion.target,
            "expected": assertion.expected,
        }
        if assertion.actual:
            result["actual"] = assertion.actual
        if assertion.message:
            result["message"] = assertion.message
        return result

    def _fixture_to_dict(self, fixture: TestFixture) -> Dict[str, Any]:
        """Convert fixture to dict"""
        result = {
            "name": fixture.fixture_name,
            "type": fixture.fixture_type,
        }
        if fixture.entity:
            result["entity"] = fixture.entity
        if fixture.data:
            result["data"] = fixture.data
        if fixture.setup_sql:
            result["setup_sql"] = fixture.setup_sql
        if fixture.scope != "function":
            result["scope"] = fixture.scope
        return result
```

**Afternoon: Test Parser Protocols (4h)**

```python
# src/testing/spec/test_parser_protocol.py

from typing import Protocol, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.testing.spec.test_spec_models import TestSpec

class TestSourceLanguage(Enum):
    """Supported test languages"""
    PGTAP = "pgtap"
    PYTEST = "pytest"
    JEST = "jest"
    JUNIT = "junit"
    RSPEC = "rspec"

@dataclass
class ParsedTest:
    """
    Intermediate representation after parsing test source
    (language-specific but structured)
    """
    test_name: str
    source_language: TestSourceLanguage
    test_functions: List['ParsedTestFunction']
    fixtures: List[Dict[str, Any]]
    imports: List[str]
    metadata: Dict[str, Any]

@dataclass
class ParsedTestFunction:
    """Single test function/case"""
    function_name: str
    docstring: Optional[str]
    decorators: List[str]
    body_lines: List[str]
    assertions: List[Dict[str, Any]]
    setup_calls: List[str]
    teardown_calls: List[str]
    metadata: Dict[str, Any]

class TestParser(Protocol):
    """Protocol for test language parsers"""

    def parse_test_file(self, source_code: str, file_path: str = "") -> ParsedTest:
        """Parse test source file to intermediate representation"""
        ...

    def extract_assertions(self, test_function: ParsedTestFunction) -> List[Dict[str, Any]]:
        """Extract assertions from test function"""
        ...

    def detect_test_type(self, parsed_test: ParsedTest) -> str:
        """Detect type of tests (CRUD, validation, workflow, etc.)"""
        ...

    @property
    def supported_language(self) -> TestSourceLanguage:
        """Language supported by this parser"""
        ...

class TestSpecMapper:
    """
    Maps ParsedTest (language-specific) to TestSpec (universal)

    This is the key component that enables cross-language test equivalence
    """

    def map_to_test_spec(self, parsed_test: ParsedTest, entity_name: str) -> TestSpec:
        """
        Convert language-specific ParsedTest to universal TestSpec

        Args:
            parsed_test: Language-specific parsed test
            entity_name: Entity being tested

        Returns:
            Universal TestSpec
        """
        raise NotImplementedError("Implement in subclass")

    def categorize_scenario(self, test_function: ParsedTestFunction) -> ScenarioCategory:
        """
        Determine scenario category from test function

        Heuristics:
            - "happy_path", "success", "valid" → HAPPY_PATH
            - "error", "fail", "invalid", "raises" → ERROR_CASE
            - "edge", "boundary", "limit" → EDGE_CASE/BOUNDARY
            - "security", "auth", "permission" → SECURITY
        """
        function_name = test_function.function_name.lower()
        docstring = (test_function.docstring or "").lower()

        combined = function_name + " " + docstring

        if any(word in combined for word in ["error", "fail", "invalid", "raises", "exception"]):
            return ScenarioCategory.ERROR_CASE
        elif any(word in combined for word in ["edge", "extreme"]):
            return ScenarioCategory.EDGE_CASE
        elif any(word in combined for word in ["boundary", "limit", "max", "min"]):
            return ScenarioCategory.BOUNDARY
        elif any(word in combined for word in ["security", "auth", "permission", "unauthorized"]):
            return ScenarioCategory.SECURITY
        elif any(word in combined for word in ["performance", "speed", "benchmark"]):
            return ScenarioCategory.PERFORMANCE
        else:
            return ScenarioCategory.HAPPY_PATH
```

**Tests** (`tests/unit/testing/test_spec_models.py`):

```python
import pytest
from src.testing.spec.test_spec_models import (
    TestSpec,
    TestScenario,
    TestAssertion,
    TestStep,
    TestFixture,
    TestType,
    ScenarioCategory,
    AssertionType
)

class TestTestSpecModels:
    """Test universal test specification models"""

    def test_create_simple_test_assertion(self):
        """Test creating equality assertion"""
        assertion = TestAssertion(
            assertion_type=AssertionType.EQUALS,
            target="result.status",
            expected="success",
            message="Status should be success"
        )

        assert assertion.assertion_type == AssertionType.EQUALS
        assert assertion.target == "result.status"
        assert assertion.expected == "success"

    def test_create_exception_assertion(self):
        """Test creating exception assertion"""
        assertion = TestAssertion(
            assertion_type=AssertionType.THROWS,
            target="action_call",
            expected="ValidationError",
            message="Should throw ValidationError"
        )

        assert assertion.assertion_type == AssertionType.THROWS
        assert assertion.expected == "ValidationError"

    def test_create_test_step(self):
        """Test creating test step"""
        step = TestStep(
            step_type="setup",
            action="create_entity",
            entity="Contact",
            data={"email": "test@example.com", "status": "lead"},
            store_result="contact"
        )

        assert step.step_type == "setup"
        assert step.action == "create_entity"
        assert step.entity == "Contact"
        assert step.data["email"] == "test@example.com"

    def test_create_test_scenario(self):
        """Test creating complete test scenario"""
        scenario = TestScenario(
            scenario_name="test_qualify_lead_happy_path",
            description="Successfully qualify a lead contact",
            category=ScenarioCategory.HAPPY_PATH,
            setup_steps=[
                TestStep(
                    step_type="setup",
                    action="create_entity",
                    entity="Contact",
                    data={"email": "test@example.com", "status": "lead"},
                    store_result="contact"
                )
            ],
            action_steps=[
                TestStep(
                    step_type="action",
                    action="call_function",
                    function="qualify_lead",
                    parameters={"contact_id": "{{contact.id}}"},
                    store_result="result"
                )
            ],
            assertions=[
                TestAssertion(
                    assertion_type=AssertionType.EQUALS,
                    target="result.status",
                    expected="success"
                ),
                TestAssertion(
                    assertion_type=AssertionType.STATE_CHANGE,
                    target="contact.status",
                    expected="qualified",
                    actual="lead"
                )
            ]
        )

        assert scenario.category == ScenarioCategory.HAPPY_PATH
        assert len(scenario.setup_steps) == 1
        assert len(scenario.action_steps) == 1
        assert len(scenario.assertions) == 2

    def test_test_spec_to_yaml(self):
        """Test converting TestSpec to YAML"""
        spec = TestSpec(
            test_name="contact_qualification_tests",
            entity_name="Contact",
            test_type=TestType.WORKFLOW,
            scenarios=[
                TestScenario(
                    scenario_name="test_qualify_lead",
                    description="Qualify a lead",
                    category=ScenarioCategory.HAPPY_PATH,
                    setup_steps=[],
                    action_steps=[],
                    assertions=[]
                )
            ],
            fixtures=[],
            coverage={
                "actions_covered": ["qualify_lead"],
                "coverage_percentage": 85.0
            }
        )

        yaml_output = spec.to_yaml()

        assert "test: contact_qualification_tests" in yaml_output
        assert "entity: Contact" in yaml_output
        assert "type: workflow" in yaml_output
        assert "actions_covered" in yaml_output
```

**Success Criteria**:
- ✅ TestSpec AST models defined
- ✅ All test primitives (assertions, steps, fixtures, scenarios)
- ✅ Test parser protocols defined
- ✅ YAML serialization working
- ✅ 10+ tests passing

---

### Day 2: pgTAP Test Parser

**Objective**: Parse pgTAP SQL tests → ParsedTest → TestSpec

**Morning: pgTAP Parser Implementation (3h)**

```python
# src/reverse_engineering/tests/pgtap_test_parser.py

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.testing.spec.test_parser_protocol import (
    TestParser,
    ParsedTest,
    ParsedTestFunction,
    TestSourceLanguage
)
from src.testing.spec.test_spec_models import TestSpec, TestType

class PgTAPTestParser:
    """
    Parse pgTAP test files to universal TestSpec

    Supports pgTAP assertions:
        - ok() / is() / isnt()
        - throws_ok() / lives_ok()
        - results_eq() / results_ne()
        - has_table() / has_column()
        - And many more pgTAP functions

    Example pgTAP test:
    ```sql
    BEGIN;
    SELECT plan(5);

    -- Test: Create contact
    SELECT ok(
        (SELECT app.create_contact(
            'test@example.com'::text,
            'Test Corp'::text,
            'lead'::text
        )).status = 'success',
        'Should create contact successfully'
    );

    -- Test: Qualify lead
    SELECT throws_ok(
        $$SELECT app.qualify_lead('00000000-0000-0000-0000-000000000000')$$,
        'Contact not found'
    );

    SELECT * FROM finish();
    ROLLBACK;
    ```
    """

    @property
    def supported_language(self) -> TestSourceLanguage:
        return TestSourceLanguage.PGTAP

    def parse_test_file(self, source_code: str, file_path: str = "") -> ParsedTest:
        """
        Parse pgTAP test file

        Args:
            source_code: SQL test file content
            file_path: Path to test file

        Returns:
            ParsedTest with extracted test functions
        """
        # Extract test name from file path
        test_name = Path(file_path).stem if file_path else "unnamed_test"

        # Parse test plan
        plan_match = re.search(r'SELECT\s+plan\((\d+)\)', source_code, re.IGNORECASE)
        test_count = int(plan_match.group(1)) if plan_match else 0

        # Extract all test assertions
        test_functions = self._extract_test_assertions(source_code)

        # Extract fixtures (setup/teardown SQL)
        fixtures = self._extract_fixtures(source_code)

        return ParsedTest(
            test_name=test_name,
            source_language=TestSourceLanguage.PGTAP,
            test_functions=test_functions,
            fixtures=fixtures,
            imports=[],
            metadata={
                "file_path": file_path,
                "test_count": test_count,
                "has_transaction": "BEGIN" in source_code and "ROLLBACK" in source_code
            }
        )

    def _extract_test_assertions(self, source_code: str) -> List[ParsedTestFunction]:
        """Extract individual pgTAP assertions as test functions"""
        test_functions = []

        # Patterns for different pgTAP assertions
        patterns = [
            # ok() / is() / isnt()
            (r'SELECT\s+(ok|is|isnt)\s*\((.*?),\s*\'([^\']+)\'\s*\)', 'assertion'),

            # throws_ok() / lives_ok()
            (r'SELECT\s+(throws_ok|lives_ok)\s*\(\s*\$\$([^\$]+)\$\$\s*(?:,\s*\'([^\']+)\')?\s*\)', 'exception'),

            # results_eq() / results_ne()
            (r'SELECT\s+(results_eq|results_ne)\s*\((.*?)\)', 'query_result'),

            # has_table() / has_column() / has_function()
            (r'SELECT\s+(has_table|has_column|has_function)\s*\((.*?)\)', 'schema_check'),
        ]

        for pattern, assertion_category in patterns:
            matches = re.finditer(pattern, source_code, re.DOTALL | re.IGNORECASE)

            for i, match in enumerate(matches):
                function_name = f"test_{assertion_category}_{i}"
                assertion_type = match.group(1)

                # Extract comment before assertion (serves as docstring)
                # Look for -- Test: ... pattern
                position = match.start()
                lines_before = source_code[:position].split('\n')
                docstring = None
                for line in reversed(lines_before):
                    if line.strip().startswith('--'):
                        docstring = line.strip()[2:].strip()
                        if docstring.startswith('Test:'):
                            docstring = docstring[5:].strip()
                        break

                test_functions.append(ParsedTestFunction(
                    function_name=function_name,
                    docstring=docstring,
                    decorators=[],
                    body_lines=[match.group(0)],
                    assertions=[{
                        "type": assertion_type,
                        "raw_assertion": match.group(0),
                        "message": match.group(3) if len(match.groups()) >= 3 else None
                    }],
                    setup_calls=[],
                    teardown_calls=[],
                    metadata={
                        "assertion_category": assertion_category,
                        "line_number": source_code[:position].count('\n') + 1
                    }
                ))

        return test_functions

    def _extract_fixtures(self, source_code: str) -> List[Dict[str, Any]]:
        """Extract setup/teardown fixtures from pgTAP test"""
        fixtures = []

        # Transaction wrapper
        if "BEGIN" in source_code and "ROLLBACK" in source_code:
            fixtures.append({
                "name": "transaction_rollback",
                "type": "database",
                "setup_sql": "BEGIN;",
                "teardown_sql": "ROLLBACK;",
                "scope": "module"
            })

        # Look for explicit setup/teardown
        setup_match = re.search(r'-- Setup(.*?)-- Test', source_code, re.DOTALL | re.IGNORECASE)
        if setup_match:
            fixtures.append({
                "name": "custom_setup",
                "type": "database",
                "setup_sql": setup_match.group(1).strip(),
                "scope": "module"
            })

        return fixtures

    def extract_assertions(self, test_function: ParsedTestFunction) -> List[Dict[str, Any]]:
        """Extract assertions from test function"""
        return test_function.assertions

    def detect_test_type(self, parsed_test: ParsedTest) -> str:
        """Detect type of tests from pgTAP file"""
        # Analyze assertion types
        assertion_types = []
        for func in parsed_test.test_functions:
            for assertion in func.assertions:
                assertion_types.append(assertion.get("type", ""))

        # Schema tests
        if any(t in assertion_types for t in ["has_table", "has_column", "has_function"]):
            return TestType.INTEGRATION.value

        # Exception tests
        if any(t in assertion_types for t in ["throws_ok", "lives_ok"]):
            return TestType.VALIDATION.value

        # Query result tests
        if any(t in assertion_types for t in ["results_eq", "results_ne"]):
            return TestType.CRUD_READ.value

        # Default
        return TestType.INTEGRATION.value


class PgTAPTestSpecMapper:
    """Maps pgTAP ParsedTest to universal TestSpec"""

    def map_to_test_spec(
        self,
        parsed_test: ParsedTest,
        entity_name: str
    ) -> TestSpec:
        """
        Convert pgTAP ParsedTest to TestSpec

        Args:
            parsed_test: Parsed pgTAP test
            entity_name: Entity being tested

        Returns:
            Universal TestSpec
        """
        from src.testing.spec.test_spec_models import (
            TestScenario, TestAssertion, TestStep, TestFixture,
            ScenarioCategory, AssertionType
        )

        # Map test functions to scenarios
        scenarios = []
        for func in parsed_test.test_functions:
            category = self._categorize_pgtap_test(func)

            # Map assertions
            assertions = []
            for assertion in func.assertions:
                assertions.append(self._map_pgtap_assertion(assertion))

            scenarios.append(TestScenario(
                scenario_name=func.function_name,
                description=func.docstring or f"pgTAP test: {func.function_name}",
                category=category,
                setup_steps=[],
                action_steps=[],  # pgTAP tests embed action in assertion
                assertions=assertions,
                teardown_steps=[],
                metadata={
                    "source_language": "pgtap",
                    "original_assertion": func.body_lines[0] if func.body_lines else ""
                }
            ))

        # Map fixtures
        fixtures = []
        for fixture_dict in parsed_test.fixtures:
            fixtures.append(TestFixture(
                fixture_name=fixture_dict["name"],
                fixture_type=fixture_dict["type"],
                setup_sql=fixture_dict.get("setup_sql"),
                teardown_sql=fixture_dict.get("teardown_sql"),
                scope=fixture_dict.get("scope", "function")
            ))

        # Detect test type
        parser = PgTAPTestParser()
        test_type_str = parser.detect_test_type(parsed_test)
        test_type = TestType(test_type_str)

        return TestSpec(
            test_name=parsed_test.test_name,
            entity_name=entity_name,
            test_type=test_type,
            scenarios=scenarios,
            fixtures=fixtures,
            coverage={
                "test_count": len(scenarios),
                "source_language": "pgtap"
            },
            metadata=parsed_test.metadata
        )

    def _categorize_pgtap_test(self, func: ParsedTestFunction) -> ScenarioCategory:
        """Categorize pgTAP test function"""
        docstring = (func.docstring or "").lower()
        function_name = func.function_name.lower()

        combined = docstring + " " + function_name

        # Check for keywords
        if any(word in combined for word in ["throws", "error", "fail", "invalid"]):
            return ScenarioCategory.ERROR_CASE
        elif any(word in combined for word in ["success", "valid", "happy"]):
            return ScenarioCategory.HAPPY_PATH
        else:
            return ScenarioCategory.HAPPY_PATH

    def _map_pgtap_assertion(self, assertion_dict: Dict[str, Any]) -> TestAssertion:
        """Map pgTAP assertion to universal TestAssertion"""
        assertion_type_map = {
            "ok": AssertionType.EQUALS,
            "is": AssertionType.EQUALS,
            "isnt": AssertionType.NOT_EQUALS,
            "throws_ok": AssertionType.THROWS,
            "lives_ok": AssertionType.NOT_THROWS,
            "results_eq": AssertionType.EQUALS,
            "results_ne": AssertionType.NOT_EQUALS,
        }

        pgtap_type = assertion_dict.get("type", "ok")
        assertion_type = assertion_type_map.get(pgtap_type, AssertionType.EQUALS)

        return TestAssertion(
            assertion_type=assertion_type,
            target="function_result",
            expected=True if pgtap_type in ["ok", "lives_ok"] else None,
            message=assertion_dict.get("message"),
            metadata={
                "pgtap_assertion": pgtap_type,
                "raw": assertion_dict.get("raw_assertion")
            }
        )
```

**Afternoon: pytest Parser Implementation (4h)**

```python
# src/reverse_engineering/tests/pytest_test_parser.py

import ast
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.testing.spec.test_parser_protocol import (
    TestParser,
    ParsedTest,
    ParsedTestFunction,
    TestSourceLanguage
)
from src.testing.spec.test_spec_models import TestSpec, TestType

class PytestParser:
    """
    Parse pytest test files to universal TestSpec

    Supports:
        - Standard assert statements
        - pytest.raises() context managers
        - pytest fixtures
        - Parametrized tests
        - Test classes

    Example pytest test:
    ```python
    import pytest

    class TestContactQualification:
        @pytest.fixture
        def test_contact(self, test_db):
            # Create test contact
            return create_contact(email="test@example.com", status="lead")

        def test_qualify_lead_happy_path(self, test_contact):
            '''Test: Successfully qualify a lead contact'''
            result = qualify_lead(test_contact.id)

            assert result.status == "success"
            assert test_contact.status == "qualified"

        def test_qualify_already_qualified_error(self, test_contact):
            '''Test: Cannot qualify already qualified contact'''
            test_contact.status = "qualified"

            with pytest.raises(ValidationError, match="already qualified"):
                qualify_lead(test_contact.id)
    ```
    """

    @property
    def supported_language(self) -> TestSourceLanguage:
        return TestSourceLanguage.PYTEST

    def parse_test_file(self, source_code: str, file_path: str = "") -> ParsedTest:
        """
        Parse pytest test file

        Args:
            source_code: Python test file content
            file_path: Path to test file

        Returns:
            ParsedTest with extracted test functions
        """
        test_name = Path(file_path).stem if file_path else "unnamed_test"

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in test file: {e}")

        # Extract imports
        imports = self._extract_imports(tree)

        # Extract fixtures
        fixtures = self._extract_fixtures(tree, source_code)

        # Extract test functions
        test_functions = self._extract_test_functions(tree, source_code)

        return ParsedTest(
            test_name=test_name,
            source_language=TestSourceLanguage.PYTEST,
            test_functions=test_functions,
            fixtures=fixtures,
            imports=imports,
            metadata={
                "file_path": file_path,
                "test_count": len(test_functions)
            }
        )

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports

    def _extract_fixtures(self, tree: ast.AST, source_code: str) -> List[Dict[str, Any]]:
        """Extract pytest fixtures"""
        fixtures = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for @pytest.fixture decorator
                has_fixture_decorator = any(
                    (isinstance(d, ast.Name) and d.id == "fixture") or
                    (isinstance(d, ast.Attribute) and d.attr == "fixture")
                    for d in node.decorator_list
                )

                if has_fixture_decorator:
                    # Extract fixture scope
                    scope = "function"  # default
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            for keyword in decorator.keywords:
                                if keyword.arg == "scope":
                                    if isinstance(keyword.value, ast.Constant):
                                        scope = keyword.value.value

                    # Get fixture body
                    fixture_lines = ast.get_source_segment(source_code, node)

                    fixtures.append({
                        "name": node.name,
                        "type": "pytest_fixture",
                        "scope": scope,
                        "body": fixture_lines,
                        "parameters": [arg.arg for arg in node.args.args if arg.arg != "self"]
                    })

        return fixtures

    def _extract_test_functions(self, tree: ast.AST, source_code: str) -> List[ParsedTestFunction]:
        """Extract test functions from AST"""
        test_functions = []

        # Find all classes and functions
        for node in ast.walk(tree):
            # Test functions (def test_*)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_func = self._parse_test_function(node, source_code)
                test_functions.append(test_func)

        return test_functions

    def _parse_test_function(self, func_node: ast.FunctionDef, source_code: str) -> ParsedTestFunction:
        """Parse single test function"""
        # Extract docstring
        docstring = ast.get_docstring(func_node)

        # Extract decorators
        decorators = []
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(decorator.attr)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    decorators.append(decorator.func.attr)

        # Extract body lines
        body_lines = []
        for stmt in func_node.body:
            if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Constant):
                # Skip docstring
                line = ast.get_source_segment(source_code, stmt)
                if line:
                    body_lines.append(line)

        # Extract assertions
        assertions = self._extract_assertions_from_function(func_node)

        # Extract setup/teardown calls
        setup_calls = self._extract_setup_calls(func_node)

        return ParsedTestFunction(
            function_name=func_node.name,
            docstring=docstring,
            decorators=decorators,
            body_lines=body_lines,
            assertions=assertions,
            setup_calls=setup_calls,
            teardown_calls=[],
            metadata={
                "line_number": func_node.lineno,
                "parameters": [arg.arg for arg in func_node.args.args if arg.arg != "self"]
            }
        )

    def _extract_assertions_from_function(self, func_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract all assertions from function"""
        assertions = []

        for node in ast.walk(func_node):
            # Standard assert
            if isinstance(node, ast.Assert):
                assertions.append(self._parse_assert_statement(node))

            # pytest.raises()
            elif isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        if self._is_pytest_raises(item.context_expr):
                            assertions.append(self._parse_pytest_raises(item))

        return assertions

    def _parse_assert_statement(self, assert_node: ast.Assert) -> Dict[str, Any]:
        """Parse standard assert statement"""
        test_expr = assert_node.test

        # Determine assertion type from comparison
        if isinstance(test_expr, ast.Compare):
            op = test_expr.ops[0]
            left = ast.unparse(test_expr.left)
            right = ast.unparse(test_expr.comparators[0])

            if isinstance(op, ast.Eq):
                assertion_type = "equals"
            elif isinstance(op, ast.NotEq):
                assertion_type = "not_equals"
            elif isinstance(op, ast.In):
                assertion_type = "contains"
            elif isinstance(op, ast.NotIn):
                assertion_type = "not_contains"
            elif isinstance(op, ast.Gt):
                assertion_type = "greater_than"
            elif isinstance(op, ast.Lt):
                assertion_type = "less_than"
            elif isinstance(op, ast.Is):
                if right == "None":
                    assertion_type = "is_null"
                else:
                    assertion_type = "equals"
            elif isinstance(op, ast.IsNot):
                if right == "None":
                    assertion_type = "is_not_null"
                else:
                    assertion_type = "not_equals"
            else:
                assertion_type = "equals"

            return {
                "type": assertion_type,
                "target": left,
                "expected": right,
                "message": ast.unparse(assert_node.msg) if assert_node.msg else None
            }
        else:
            # Boolean assertion
            return {
                "type": "equals",
                "target": ast.unparse(test_expr),
                "expected": True,
                "message": ast.unparse(assert_node.msg) if assert_node.msg else None
            }

    def _is_pytest_raises(self, call_node: ast.Call) -> bool:
        """Check if call is pytest.raises()"""
        if isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr == "raises"
        return False

    def _parse_pytest_raises(self, with_item: ast.withitem) -> Dict[str, Any]:
        """Parse pytest.raises() context manager"""
        call = with_item.context_expr

        # Extract exception type
        if call.args:
            exception_type = ast.unparse(call.args[0])
        else:
            exception_type = "Exception"

        # Extract match pattern if present
        match_pattern = None
        for keyword in call.keywords:
            if keyword.arg == "match":
                match_pattern = ast.unparse(keyword.value)

        return {
            "type": "throws",
            "target": "function_call",
            "expected": exception_type,
            "message": f"Should raise {exception_type}" + (f" matching {match_pattern}" if match_pattern else "")
        }

    def _extract_setup_calls(self, func_node: ast.FunctionDef) -> List[str]:
        """Extract setup calls (non-assertion statements)"""
        setup_calls = []

        for stmt in func_node.body:
            # Skip docstring and assertions
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Constant):
                    continue  # docstring
            elif isinstance(stmt, ast.Assert):
                continue
            elif isinstance(stmt, ast.With):
                # Skip pytest.raises
                continue

            # This is likely setup
            # Extract variable assignments, function calls, etc.
            if isinstance(stmt, (ast.Assign, ast.AugAssign, ast.Expr)):
                setup_calls.append(ast.unparse(stmt))

        return setup_calls

    def extract_assertions(self, test_function: ParsedTestFunction) -> List[Dict[str, Any]]:
        """Extract assertions from test function"""
        return test_function.assertions

    def detect_test_type(self, parsed_test: ParsedTest) -> str:
        """Detect type of tests from pytest file"""
        # Analyze test function names and assertions
        test_names = [f.function_name.lower() for f in parsed_test.test_functions]

        combined_names = " ".join(test_names)

        # CRUD operations
        if any(word in combined_names for word in ["create", "insert"]):
            return TestType.CRUD_CREATE.value
        elif any(word in combined_names for word in ["read", "get", "fetch"]):
            return TestType.CRUD_READ.value
        elif any(word in combined_names for word in ["update", "modify"]):
            return TestType.CRUD_UPDATE.value
        elif any(word in combined_names for word in ["delete", "remove"]):
            return TestType.CRUD_DELETE.value

        # Validation
        elif any(word in combined_names for word in ["validate", "validation", "invalid"]):
            return TestType.VALIDATION.value

        # Workflow
        elif any(word in combined_names for word in ["workflow", "process", "flow"]):
            return TestType.WORKFLOW.value

        # Default
        return TestType.INTEGRATION.value


class PytestTestSpecMapper:
    """Maps pytest ParsedTest to universal TestSpec"""

    def map_to_test_spec(
        self,
        parsed_test: ParsedTest,
        entity_name: str
    ) -> TestSpec:
        """Convert pytest ParsedTest to TestSpec"""
        from src.testing.spec.test_spec_models import (
            TestScenario, TestAssertion, TestStep, TestFixture,
            ScenarioCategory, AssertionType
        )

        # Map test functions to scenarios
        scenarios = []
        for func in parsed_test.test_functions:
            category = self._categorize_pytest_test(func)

            # Map setup steps
            setup_steps = []
            for setup_call in func.setup_calls:
                setup_steps.append(TestStep(
                    step_type="setup",
                    action="execute_code",
                    metadata={"code": setup_call}
                ))

            # Map assertions
            assertions = []
            for assertion_dict in func.assertions:
                assertions.append(self._map_pytest_assertion(assertion_dict))

            scenarios.append(TestScenario(
                scenario_name=func.function_name,
                description=func.docstring or f"pytest test: {func.function_name}",
                category=category,
                setup_steps=setup_steps,
                action_steps=[],
                assertions=assertions,
                teardown_steps=[],
                fixtures=func.metadata.get("parameters", []),
                metadata={
                    "source_language": "pytest",
                    "decorators": func.decorators
                }
            ))

        # Map fixtures
        fixtures = []
        for fixture_dict in parsed_test.fixtures:
            fixtures.append(TestFixture(
                fixture_name=fixture_dict["name"],
                fixture_type=fixture_dict["type"],
                scope=fixture_dict.get("scope", "function"),
                metadata={"body": fixture_dict.get("body")}
            ))

        # Detect test type
        parser = PytestParser()
        test_type_str = parser.detect_test_type(parsed_test)
        test_type = TestType(test_type_str)

        return TestSpec(
            test_name=parsed_test.test_name,
            entity_name=entity_name,
            test_type=test_type,
            scenarios=scenarios,
            fixtures=fixtures,
            coverage={
                "test_count": len(scenarios),
                "source_language": "pytest"
            },
            metadata=parsed_test.metadata
        )

    def _categorize_pytest_test(self, func: ParsedTestFunction) -> ScenarioCategory:
        """Categorize pytest test function"""
        docstring = (func.docstring or "").lower()
        function_name = func.function_name.lower()

        combined = docstring + " " + function_name

        if any(word in combined for word in ["error", "fail", "invalid", "raises"]):
            return ScenarioCategory.ERROR_CASE
        elif any(word in combined for word in ["edge", "extreme"]):
            return ScenarioCategory.EDGE_CASE
        elif any(word in combined for word in ["boundary", "limit"]):
            return ScenarioCategory.BOUNDARY
        else:
            return ScenarioCategory.HAPPY_PATH

    def _map_pytest_assertion(self, assertion_dict: Dict[str, Any]) -> TestAssertion:
        """Map pytest assertion to universal TestAssertion"""
        assertion_type_map = {
            "equals": AssertionType.EQUALS,
            "not_equals": AssertionType.NOT_EQUALS,
            "contains": AssertionType.CONTAINS,
            "not_contains": AssertionType.NOT_CONTAINS,
            "greater_than": AssertionType.GREATER_THAN,
            "less_than": AssertionType.LESS_THAN,
            "is_null": AssertionType.IS_NULL,
            "is_not_null": AssertionType.IS_NOT_NULL,
            "throws": AssertionType.THROWS,
        }

        pytest_type = assertion_dict.get("type", "equals")
        assertion_type = assertion_type_map.get(pytest_type, AssertionType.EQUALS)

        return TestAssertion(
            assertion_type=assertion_type,
            target=assertion_dict.get("target", ""),
            expected=assertion_dict.get("expected"),
            message=assertion_dict.get("message"),
            metadata={
                "pytest_assertion": pytest_type,
                "source": "pytest"
            }
        )
```

**Tests** (`tests/unit/reverse_engineering/test_pgtap_parser.py`, `test_pytest_parser.py`):

```python
# tests/unit/reverse_engineering/test_pgtap_parser.py
import pytest
from src.reverse_engineering.tests.pgtap_test_parser import (
    PgTAPTestParser,
    PgTAPTestSpecMapper
)

class TestPgTAPTestParser:

    def test_parse_simple_pgtap_test(self):
        """Test parsing simple pgTAP test"""
        pgtap_code = """
        BEGIN;
        SELECT plan(2);

        -- Test: Create contact successfully
        SELECT ok(
            (SELECT app.create_contact('test@example.com')).status = 'success',
            'Should create contact'
        );

        -- Test: Throw error for duplicate
        SELECT throws_ok(
            $$SELECT app.create_contact('test@example.com')$$,
            'Duplicate email'
        );

        SELECT * FROM finish();
        ROLLBACK;
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        assert parsed.source_language.value == "pgtap"
        assert parsed.metadata["test_count"] == 2
        assert len(parsed.test_functions) >= 2

    def test_map_pgtap_to_test_spec(self):
        """Test mapping pgTAP to TestSpec"""
        pgtap_code = """
        SELECT ok((SELECT app.qualify_lead('uuid')).status = 'success');
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        mapper = PgTAPTestSpecMapper()
        test_spec = mapper.map_to_test_spec(parsed, "Contact")

        assert test_spec.entity_name == "Contact"
        assert len(test_spec.scenarios) > 0


# tests/unit/reverse_engineering/test_pytest_parser.py
import pytest
from src.reverse_engineering.tests.pytest_test_parser import (
    PytestParser,
    PytestTestSpecMapper
)

class TestPytestParser:

    def test_parse_simple_pytest_test(self):
        """Test parsing simple pytest test"""
        pytest_code = """
import pytest

class TestContact:
    def test_create_contact(self):
        '''Test: Create contact successfully'''
        result = create_contact("test@example.com")
        assert result.status == "success"

    def test_create_duplicate_error(self):
        '''Test: Raise error for duplicate email'''
        with pytest.raises(ValidationError):
            create_contact("existing@example.com")
        """

        parser = PytestParser()
        parsed = parser.parse_test_file(pytest_code)

        assert parsed.source_language.value == "pytest"
        assert len(parsed.test_functions) == 2
        assert parsed.test_functions[0].function_name == "test_create_contact"

    def test_extract_assertions(self):
        """Test extracting assertions from pytest"""
        pytest_code = """
def test_qualify_lead():
    result = qualify_lead(contact_id)
    assert result.status == "success"
    assert contact.status == "qualified"
        """

        parser = PytestParser()
        parsed = parser.parse_test_file(pytest_code)

        assert len(parsed.test_functions) == 1
        test_func = parsed.test_functions[0]
        assert len(test_func.assertions) == 2
        assert test_func.assertions[0]["type"] == "equals"
```

**Success Criteria**:
- ✅ pgTAP parser working
- ✅ pytest parser working
- ✅ Assertion extraction correct
- ✅ Fixture detection working
- ✅ Test type detection accurate
- ✅ Mapping to TestSpec working
- ✅ 15+ tests passing

---

### Day 3: CLI Integration & Test Pattern Detection

**Objective**: Integrate test reverse engineering into CLI + detect test patterns

**Morning: CLI Commands (3h)**

```python
# src/cli/reverse_tests.py

import click
from pathlib import Path
from typing import Optional

from src.reverse_engineering.tests.pgtap_test_parser import PgTAPTestParser, PgTAPTestSpecMapper
from src.reverse_engineering.tests.pytest_test_parser import PytestParser, PytestTestSpecMapper

@click.command()
@click.argument('test_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--entity', '-e', type=str, required=True,
              help='Entity name being tested')
@click.option('--output-dir', '-o', type=click.Path(), default='test-specs/',
              help='Output directory for TestSpec YAML files')
@click.option('--format', '-f', type=click.Choice(['auto', 'pgtap', 'pytest']),
              default='auto', help='Test file format (auto-detect by default)')
@click.option('--preview', is_flag=True,
              help='Preview TestSpec without writing files')
@click.option('--analyze-coverage', is_flag=True,
              help='Analyze test coverage and suggest missing tests')
def reverse_tests(
    test_files,
    entity,
    output_dir,
    format,
    preview,
    analyze_coverage
):
    """
    Reverse engineer test files to universal TestSpec YAML

    Examples:
        # Reverse engineer pgTAP test
        specql reverse-tests tests/pgtap/contact_test.sql --entity Contact

        # Reverse engineer pytest test
        specql reverse-tests tests/pytest/test_contact.py --entity Contact

        # Preview without writing
        specql reverse-tests tests/**/*.sql --entity Contact --preview

        # Analyze coverage
        specql reverse-tests tests/**/*.py --entity Contact --analyze-coverage
    """
    click.echo(f"🔄 Reverse engineering {len(test_files)} test file(s)...\n")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    test_specs = []

    for test_file in test_files:
        test_file_path = Path(test_file)

        # Auto-detect format
        if format == 'auto':
            if test_file_path.suffix == '.sql':
                detected_format = 'pgtap'
            elif test_file_path.suffix == '.py':
                detected_format = 'pytest'
            else:
                click.echo(f"⚠️  Could not auto-detect format for {test_file}, skipping", err=True)
                continue
        else:
            detected_format = format

        click.echo(f"  📄 Parsing {test_file_path.name} ({detected_format})...")

        try:
            # Parse test file
            source_code = test_file_path.read_text()

            if detected_format == 'pgtap':
                parser = PgTAPTestParser()
                mapper = PgTAPTestSpecMapper()
            elif detected_format == 'pytest':
                parser = PytestParser()
                mapper = PytestTestSpecMapper()
            else:
                click.echo(f"❌ Unsupported format: {detected_format}", err=True)
                continue

            # Parse and map
            parsed_test = parser.parse_test_file(source_code, str(test_file_path))
            test_spec = mapper.map_to_test_spec(parsed_test, entity)

            test_specs.append(test_spec)

            # Show summary
            click.echo(f"    ✅ Extracted {len(test_spec.scenarios)} test scenarios")
            click.echo(f"    📦 Found {len(test_spec.fixtures)} fixtures")

            # Preview or write
            if preview:
                click.echo(f"\n--- TestSpec Preview ---")
                click.echo(test_spec.to_yaml())
                click.echo("--- End Preview ---\n")
            else:
                # Write TestSpec YAML
                output_file = output_path / f"{entity.lower()}_tests.yaml"
                output_file.write_text(test_spec.to_yaml())
                click.echo(f"    💾 Saved: {output_file}\n")

        except Exception as e:
            click.echo(f"    ❌ Error: {e}\n", err=True)
            continue

    # Coverage analysis
    if analyze_coverage and test_specs:
        click.echo("\n📊 Test Coverage Analysis:\n")
        _analyze_test_coverage(test_specs, entity)


def _analyze_test_coverage(test_specs, entity_name):
    """Analyze test coverage and suggest missing tests"""
    from collections import Counter

    all_categories = []
    all_test_types = []

    for spec in test_specs:
        all_test_types.append(spec.test_type.value)
        for scenario in spec.scenarios:
            all_categories.append(scenario.category.value)

    # Count coverage
    category_counts = Counter(all_categories)
    type_counts = Counter(all_test_types)

    click.echo(f"  Entity: {entity_name}")
    click.echo(f"  Total Scenarios: {len(all_categories)}")
    click.echo()

    click.echo("  Scenario Categories:")
    for category, count in category_counts.most_common():
        click.echo(f"    - {category}: {count} scenarios")

    click.echo()
    click.echo("  Test Types:")
    for test_type, count in type_counts.most_common():
        click.echo(f"    - {test_type}: {count} tests")

    click.echo()

    # Suggest missing coverage
    click.echo("  💡 Coverage Suggestions:")

    from src.testing.spec.test_spec_models import ScenarioCategory, TestType

    # Check for missing scenario categories
    all_category_values = {c.value for c in ScenarioCategory}
    missing_categories = all_category_values - set(all_categories)

    if missing_categories:
        click.echo(f"    ⚠️  Missing scenario categories: {', '.join(missing_categories)}")

    # Check for CRUD completeness
    crud_types = {TestType.CRUD_CREATE.value, TestType.CRUD_READ.value,
                  TestType.CRUD_UPDATE.value, TestType.CRUD_DELETE.value}
    covered_crud = crud_types & set(all_test_types)
    missing_crud = crud_types - covered_crud

    if missing_crud:
        click.echo(f"    ⚠️  Missing CRUD operations: {', '.join(missing_crud)}")

    if not missing_categories and not missing_crud:
        click.echo("    ✅ Comprehensive test coverage!")
```

**Afternoon: Test Pattern Detector (4h)**

```python
# src/reverse_engineering/tests/test_pattern_detector.py

from typing import List, Dict, Any
from collections import Counter

from src.testing.spec.test_spec_models import (
    TestSpec,
    TestType,
    ScenarioCategory,
    AssertionType
)

class TestPatternDetector:
    """
    Detect common test patterns from TestSpec

    Patterns detected:
        - CRUD completeness (all 4 operations)
        - Happy path bias (too many happy paths, not enough errors)
        - Assertion diversity (variety of assertion types)
        - State machine coverage (state transitions tested)
        - Edge case coverage
        - Security test presence
    """

    def detect_patterns(self, test_specs: List[TestSpec]) -> Dict[str, Any]:
        """
        Detect test patterns across multiple TestSpecs

        Returns:
            {
                "crud_completeness": {
                    "covered": ["create", "read", "update"],
                    "missing": ["delete"],
                    "score": 0.75
                },
                "scenario_coverage": {
                    "happy_path": 10,
                    "error_case": 5,
                    "edge_case": 2,
                    "boundary": 1,
                    "balance_score": 0.6
                },
                "assertion_diversity": {
                    "types_used": ["equals", "throws", "state_change"],
                    "diversity_score": 0.5
                },
                "detected_patterns": [
                    "crud_pattern",
                    "state_machine_testing",
                    "validation_chain"
                ],
                "suggested_improvements": [
                    "Add more error case scenarios",
                    "Consider boundary condition tests",
                    "Add security tests"
                ]
            }
        """
        patterns = {}

        # CRUD completeness
        patterns["crud_completeness"] = self._analyze_crud_completeness(test_specs)

        # Scenario coverage balance
        patterns["scenario_coverage"] = self._analyze_scenario_coverage(test_specs)

        # Assertion diversity
        patterns["assertion_diversity"] = self._analyze_assertion_diversity(test_specs)

        # Detect known patterns
        patterns["detected_patterns"] = self._detect_known_patterns(test_specs)

        # Suggest improvements
        patterns["suggested_improvements"] = self._suggest_improvements(patterns)

        return patterns

    def _analyze_crud_completeness(self, test_specs: List[TestSpec]) -> Dict[str, Any]:
        """Analyze CRUD operation coverage"""
        crud_types = {
            TestType.CRUD_CREATE,
            TestType.CRUD_READ,
            TestType.CRUD_UPDATE,
            TestType.CRUD_DELETE
        }

        covered = set()
        for spec in test_specs:
            if spec.test_type in crud_types:
                covered.add(spec.test_type.value)

        crud_values = {t.value for t in crud_types}
        missing = crud_values - covered

        score = len(covered) / len(crud_types)

        return {
            "covered": list(covered),
            "missing": list(missing),
            "score": round(score, 2),
            "complete": score == 1.0
        }

    def _analyze_scenario_coverage(self, test_specs: List[TestSpec]) -> Dict[str, Any]:
        """Analyze scenario category balance"""
        all_categories = []

        for spec in test_specs:
            for scenario in spec.scenarios:
                all_categories.append(scenario.category.value)

        category_counts = Counter(all_categories)
        total = len(all_categories)

        # Calculate balance score (closer to equal distribution = higher score)
        # Ideal: 40% happy, 30% error, 15% edge, 10% boundary, 5% security
        ideal_distribution = {
            ScenarioCategory.HAPPY_PATH.value: 0.40,
            ScenarioCategory.ERROR_CASE.value: 0.30,
            ScenarioCategory.EDGE_CASE.value: 0.15,
            ScenarioCategory.BOUNDARY.value: 0.10,
            ScenarioCategory.SECURITY.value: 0.05,
        }

        actual_distribution = {
            cat: count / total
            for cat, count in category_counts.items()
        }

        # Calculate deviation from ideal
        deviations = []
        for cat, ideal_pct in ideal_distribution.items():
            actual_pct = actual_distribution.get(cat, 0.0)
            deviation = abs(ideal_pct - actual_pct)
            deviations.append(deviation)

        avg_deviation = sum(deviations) / len(deviations)
        balance_score = max(0, 1.0 - avg_deviation)

        return {
            **category_counts,
            "total_scenarios": total,
            "balance_score": round(balance_score, 2),
            "distribution": actual_distribution
        }

    def _analyze_assertion_diversity(self, test_specs: List[TestSpec]) -> Dict[str, Any]:
        """Analyze variety of assertion types used"""
        assertion_types = set()
        assertion_counts = Counter()

        for spec in test_specs:
            for scenario in spec.scenarios:
                for assertion in scenario.assertions:
                    assertion_types.add(assertion.assertion_type.value)
                    assertion_counts[assertion.assertion_type.value] += 1

        # Diversity score: percentage of available assertion types used
        all_assertion_types = {t.value for t in AssertionType}
        diversity_score = len(assertion_types) / len(all_assertion_types)

        return {
            "types_used": list(assertion_types),
            "type_counts": dict(assertion_counts),
            "diversity_score": round(diversity_score, 2),
            "total_assertions": sum(assertion_counts.values())
        }

    def _detect_known_patterns(self, test_specs: List[TestSpec]) -> List[str]:
        """Detect presence of known test patterns"""
        patterns = []

        test_types = {spec.test_type for spec in test_specs}

        # CRUD pattern
        crud_count = sum(1 for t in test_types if t.value.startswith("crud_"))
        if crud_count >= 3:
            patterns.append("crud_pattern")

        # State machine testing
        if any(spec.test_type == TestType.STATE_MACHINE for spec in test_specs):
            patterns.append("state_machine_testing")

        # Workflow testing
        if any(spec.test_type == TestType.WORKFLOW for spec in test_specs):
            patterns.append("workflow_testing")

        # Validation chain
        validation_count = sum(1 for spec in test_specs if spec.test_type == TestType.VALIDATION)
        if validation_count >= 2:
            patterns.append("validation_chain")

        # Exception testing (many error cases)
        error_scenario_count = sum(
            1 for spec in test_specs
            for scenario in spec.scenarios
            if scenario.category == ScenarioCategory.ERROR_CASE
        )
        if error_scenario_count >= 5:
            patterns.append("comprehensive_error_testing")

        return patterns

    def _suggest_improvements(self, patterns: Dict[str, Any]) -> List[str]:
        """Suggest improvements based on detected patterns"""
        suggestions = []

        # CRUD completeness
        crud = patterns["crud_completeness"]
        if not crud["complete"]:
            suggestions.append(
                f"Add tests for missing CRUD operations: {', '.join(crud['missing'])}"
            )

        # Scenario balance
        coverage = patterns["scenario_coverage"]

        error_cases = coverage.get(ScenarioCategory.ERROR_CASE.value, 0)
        happy_paths = coverage.get(ScenarioCategory.HAPPY_PATH.value, 0)

        if error_cases < happy_paths * 0.5:
            suggestions.append(
                "Consider adding more error case scenarios (best practice: ~50% of happy paths)"
            )

        if coverage.get(ScenarioCategory.EDGE_CASE.value, 0) == 0:
            suggestions.append("Add edge case tests for boundary conditions")

        if coverage.get(ScenarioCategory.SECURITY.value, 0) == 0:
            suggestions.append("Consider adding security tests (auth, permissions, injection)")

        # Assertion diversity
        diversity = patterns["assertion_diversity"]
        if diversity["diversity_score"] < 0.3:
            suggestions.append(
                "Increase assertion diversity (currently using only basic assertions)"
            )

        if "state_change" not in diversity["types_used"]:
            suggestions.append(
                "Consider adding state change assertions for mutation tests"
            )

        return suggestions
```

**Tests** (`tests/unit/reverse_engineering/test_test_pattern_detector.py`):

```python
import pytest
from src.reverse_engineering.tests.test_pattern_detector import TestPatternDetector
from src.testing.spec.test_spec_models import (
    TestSpec,
    TestScenario,
    TestAssertion,
    TestType,
    ScenarioCategory,
    AssertionType
)

class TestTestPatternDetector:

    def test_detect_crud_completeness(self):
        """Test CRUD completeness detection"""
        test_specs = [
            TestSpec(
                test_name="test_create",
                entity_name="Contact",
                test_type=TestType.CRUD_CREATE,
                scenarios=[]
            ),
            TestSpec(
                test_name="test_read",
                entity_name="Contact",
                test_type=TestType.CRUD_READ,
                scenarios=[]
            ),
            TestSpec(
                test_name="test_update",
                entity_name="Contact",
                test_type=TestType.CRUD_UPDATE,
                scenarios=[]
            ),
        ]

        detector = TestPatternDetector()
        patterns = detector.detect_patterns(test_specs)

        crud = patterns["crud_completeness"]
        assert crud["score"] == 0.75
        assert "crud_delete" in crud["missing"]
        assert not crud["complete"]

    def test_detect_scenario_coverage_imbalance(self):
        """Test detecting imbalanced scenario coverage"""
        scenarios = [
            TestScenario(
                scenario_name=f"test_happy_{i}",
                description="Happy path",
                category=ScenarioCategory.HAPPY_PATH,
                setup_steps=[],
                action_steps=[],
                assertions=[]
            )
            for i in range(10)
        ] + [
            TestScenario(
                scenario_name="test_error",
                description="Error case",
                category=ScenarioCategory.ERROR_CASE,
                setup_steps=[],
                action_steps=[],
                assertions=[]
            )
        ]

        test_specs = [
            TestSpec(
                test_name="contact_tests",
                entity_name="Contact",
                test_type=TestType.WORKFLOW,
                scenarios=scenarios
            )
        ]

        detector = TestPatternDetector()
        patterns = detector.detect_patterns(test_specs)

        coverage = patterns["scenario_coverage"]
        assert coverage["happy_path"] == 10
        assert coverage["error_case"] == 1

        # Should suggest more error cases
        suggestions = patterns["suggested_improvements"]
        assert any("error case" in s.lower() for s in suggestions)

    def test_detect_known_patterns(self):
        """Test detecting known test patterns"""
        test_specs = [
            TestSpec(
                test_name="test_create",
                entity_name="Contact",
                test_type=TestType.CRUD_CREATE,
                scenarios=[]
            ),
            TestSpec(
                test_name="test_read",
                entity_name="Contact",
                test_type=TestType.CRUD_READ,
                scenarios=[]
            ),
            TestSpec(
                test_name="test_update",
                entity_name="Contact",
                test_type=TestType.CRUD_UPDATE,
                scenarios=[]
            ),
        ]

        detector = TestPatternDetector()
        patterns = detector.detect_patterns(test_specs)

        assert "crud_pattern" in patterns["detected_patterns"]
```

**Success Criteria**:
- ✅ CLI command `reverse-tests` working
- ✅ Auto-detection of test format
- ✅ TestSpec YAML generation
- ✅ Coverage analysis working
- ✅ Pattern detection implemented
- ✅ Improvement suggestions generated
- ✅ 10+ tests passing

---

### Days 4-5: Migration Validation & Cross-Language Test Equivalence

**Objective**: Enable validation that migrated code maintains test coverage

**Morning Day 4: Migration Validation Framework (3h)**

```python
# src/migration/test_equivalence_checker.py

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.testing.spec.test_spec_models import TestSpec, TestAssertion, AssertionType

class EquivalenceLevel(Enum):
    """Level of test equivalence"""
    EXACT = "exact"  # Identical semantics
    STRONG = "strong"  # Same scenarios, minor differences in assertions
    WEAK = "weak"  # Some scenario overlap
    NONE = "none"  # No equivalence

@dataclass
class EquivalenceResult:
    """Result of test equivalence check"""
    level: EquivalenceLevel
    matching_scenarios: List[Tuple[str, str]]  # (ref_scenario, gen_scenario)
    missing_scenarios: List[str]  # In reference but not generated
    extra_scenarios: List[str]  # In generated but not reference
    assertion_matches: Dict[str, float]  # scenario -> match percentage
    coverage_delta: float  # Difference in coverage (-1.0 to 1.0)
    details: Dict[str, Any]

class TestEquivalenceChecker:
    """
    Check equivalence between reference tests and generated tests

    Used for migration validation: ensure migrated code maintains
    the same test coverage as the original.
    """

    def check_equivalence(
        self,
        reference_spec: TestSpec,
        generated_spec: TestSpec
    ) -> EquivalenceResult:
        """
        Compare two TestSpecs for equivalence

        Args:
            reference_spec: Original/reference test specification
            generated_spec: Generated/migrated test specification

        Returns:
            EquivalenceResult with detailed comparison
        """
        # Match scenarios
        matching, missing, extra = self._match_scenarios(
            reference_spec.scenarios,
            generated_spec.scenarios
        )

        # Calculate assertion matches
        assertion_matches = {}
        for ref_name, gen_name in matching:
            ref_scenario = next(s for s in reference_spec.scenarios if s.scenario_name == ref_name)
            gen_scenario = next(s for s in generated_spec.scenarios if s.scenario_name == gen_name)

            match_pct = self._compare_assertions(
                ref_scenario.assertions,
                gen_scenario.assertions
            )
            assertion_matches[ref_name] = match_pct

        # Calculate coverage delta
        ref_coverage = reference_spec.coverage.get("coverage_percentage", 0)
        gen_coverage = generated_spec.coverage.get("coverage_percentage", 0)
        coverage_delta = (gen_coverage - ref_coverage) / 100.0

        # Determine equivalence level
        level = self._determine_equivalence_level(
            len(matching),
            len(missing),
            len(extra),
            assertion_matches
        )

        return EquivalenceResult(
            level=level,
            matching_scenarios=matching,
            missing_scenarios=missing,
            extra_scenarios=extra,
            assertion_matches=assertion_matches,
            coverage_delta=coverage_delta,
            details={
                "total_ref_scenarios": len(reference_spec.scenarios),
                "total_gen_scenarios": len(generated_spec.scenarios),
                "match_percentage": len(matching) / len(reference_spec.scenarios) if reference_spec.scenarios else 0
            }
        )

    def _match_scenarios(
        self,
        ref_scenarios,
        gen_scenarios
    ) -> Tuple[List[Tuple[str, str]], List[str], List[str]]:
        """
        Match scenarios between reference and generated

        Uses fuzzy matching on:
            - Scenario name similarity
            - Description similarity
            - Category match
        """
        from difflib import SequenceMatcher

        ref_names = {s.scenario_name: s for s in ref_scenarios}
        gen_names = {s.scenario_name: s for s in gen_scenarios}

        matching = []
        missing = []
        extra = []

        matched_gen = set()

        for ref_name, ref_scenario in ref_names.items():
            best_match = None
            best_score = 0.0

            for gen_name, gen_scenario in gen_names.items():
                if gen_name in matched_gen:
                    continue

                # Name similarity
                name_sim = SequenceMatcher(None, ref_name, gen_name).ratio()

                # Description similarity
                ref_desc = ref_scenario.description or ""
                gen_desc = gen_scenario.description or ""
                desc_sim = SequenceMatcher(None, ref_desc, gen_desc).ratio()

                # Category match
                category_match = 1.0 if ref_scenario.category == gen_scenario.category else 0.0

                # Combined score
                score = (name_sim * 0.5) + (desc_sim * 0.3) + (category_match * 0.2)

                if score > best_score:
                    best_score = score
                    best_match = gen_name

            # Threshold for match
            if best_score >= 0.6:
                matching.append((ref_name, best_match))
                matched_gen.add(best_match)
            else:
                missing.append(ref_name)

        # Any generated scenarios not matched are "extra"
        for gen_name in gen_names:
            if gen_name not in matched_gen:
                extra.append(gen_name)

        return matching, missing, extra

    def _compare_assertions(
        self,
        ref_assertions: List[TestAssertion],
        gen_assertions: List[TestAssertion]
    ) -> float:
        """
        Compare assertions between two scenarios

        Returns match percentage (0.0 - 1.0)
        """
        if not ref_assertions:
            return 1.0 if not gen_assertions else 0.0

        matches = 0

        for ref_assertion in ref_assertions:
            # Find equivalent assertion in generated
            for gen_assertion in gen_assertions:
                if self._assertions_equivalent(ref_assertion, gen_assertion):
                    matches += 1
                    break

        return matches / len(ref_assertions)

    def _assertions_equivalent(
        self,
        ref: TestAssertion,
        gen: TestAssertion
    ) -> bool:
        """Check if two assertions are semantically equivalent"""
        # Same assertion type
        if ref.assertion_type != gen.assertion_type:
            return False

        # Same target (with normalization)
        ref_target = self._normalize_target(ref.target)
        gen_target = self._normalize_target(gen.target)

        if ref_target != gen_target:
            return False

        # Same expected value
        if ref.expected != gen.expected:
            return False

        return True

    def _normalize_target(self, target: str) -> str:
        """Normalize assertion target for comparison"""
        # Remove whitespace
        target = target.strip()

        # Normalize case
        target = target.lower()

        # Remove language-specific prefixes (result., v_, etc.)
        target = target.replace("result.", "")
        target = target.replace("v_", "")

        return target

    def _determine_equivalence_level(
        self,
        matching_count: int,
        missing_count: int,
        extra_count: int,
        assertion_matches: Dict[str, float]
    ) -> EquivalenceLevel:
        """Determine overall equivalence level"""
        total_scenarios = matching_count + missing_count

        if total_scenarios == 0:
            return EquivalenceLevel.NONE

        match_pct = matching_count / total_scenarios

        # Average assertion match
        avg_assertion_match = sum(assertion_matches.values()) / len(assertion_matches) if assertion_matches else 0

        # EXACT: All scenarios match, all assertions match perfectly
        if match_pct == 1.0 and avg_assertion_match >= 0.95 and extra_count == 0:
            return EquivalenceLevel.EXACT

        # STRONG: Most scenarios match, assertions mostly match
        elif match_pct >= 0.9 and avg_assertion_match >= 0.8:
            return EquivalenceLevel.STRONG

        # WEAK: Some overlap
        elif match_pct >= 0.5:
            return EquivalenceLevel.WEAK

        # NONE: Little to no overlap
        else:
            return EquivalenceLevel.NONE
```

**Afternoon Day 4: Validation CLI Command (4h)**

```python
# src/cli/validate_migration.py

import click
from pathlib import Path
from typing import List

from src.reverse_engineering.tests.pgtap_test_parser import PgTAPTestParser, PgTAPTestSpecMapper
from src.reverse_engineering.tests.pytest_test_parser import PytestParser, PytestTestSpecMapper
from src.migration.test_equivalence_checker import TestEquivalenceChecker, EquivalenceLevel

@click.command()
@click.option('--reference-tests', '-r', type=click.Path(exists=True), required=True,
              help='Directory with reference/original tests')
@click.option('--generated-tests', '-g', type=click.Path(exists=True), required=True,
              help='Directory with generated/migrated tests')
@click.option('--entity', '-e', type=str, required=True,
              help='Entity name being validated')
@click.option('--report', type=click.Path(), default='validation_report.md',
              help='Output path for validation report')
@click.option('--fail-on-weak', is_flag=True,
              help='Exit with error if equivalence is WEAK or NONE')
def validate_migration(
    reference_tests,
    generated_tests,
    entity,
    report,
    fail_on_weak
):
    """
    Validate that migrated code maintains test coverage

    Examples:
        # Validate migration preserves tests
        specql validate-migration \
          --reference-tests reference_app/tests/ \
          --generated-tests generated/tests/ \
          --entity Contact

        # Generate detailed report
        specql validate-migration \
          --reference-tests ref/tests/ \
          --generated-tests gen/tests/ \
          --entity Contact \
          --report migration_validation.md

        # Fail CI if weak equivalence
        specql validate-migration \
          --reference-tests ref/tests/ \
          --generated-tests gen/tests/ \
          --entity Contact \
          --fail-on-weak
    """
    click.echo(f"🔍 Validating migration for {entity}...\n")

    ref_path = Path(reference_tests)
    gen_path = Path(generated_tests)

    # Find test files
    ref_files = list(ref_path.rglob("*test*.sql")) + list(ref_path.rglob("test_*.py"))
    gen_files = list(gen_path.rglob("*test*.sql")) + list(gen_path.rglob("test_*.py"))

    click.echo(f"  📄 Reference tests: {len(ref_files)} files")
    click.echo(f"  📄 Generated tests: {len(gen_files)} files\n")

    # Parse reference tests
    click.echo("  Parsing reference tests...")
    ref_specs = _parse_test_files(ref_files, entity)

    # Parse generated tests
    click.echo("  Parsing generated tests...")
    gen_specs = _parse_test_files(gen_files, entity)

    if not ref_specs or not gen_specs:
        click.echo("❌ Could not find test specifications", err=True)
        raise click.Abort()

    # Check equivalence
    click.echo("\n  Checking test equivalence...\n")

    checker = TestEquivalenceChecker()

    results = []
    for ref_spec in ref_specs:
        # Find matching generated spec
        gen_spec = next((s for s in gen_specs if s.test_name == ref_spec.test_name), None)

        if not gen_spec:
            click.echo(f"    ⚠️  No generated test found for {ref_spec.test_name}")
            continue

        result = checker.check_equivalence(ref_spec, gen_spec)
        results.append((ref_spec, gen_spec, result))

        # Show result
        _show_equivalence_result(ref_spec.test_name, result)

    # Generate report
    click.echo(f"\n  📊 Generating validation report: {report}")
    _generate_validation_report(results, entity, report)

    # Summary
    click.echo("\n📊 Migration Validation Summary:\n")

    equivalence_counts = {}
    for _, _, result in results:
        level = result.level.value
        equivalence_counts[level] = equivalence_counts.get(level, 0) + 1

    for level, count in equivalence_counts.items():
        icon = "✅" if level in ["exact", "strong"] else "⚠️" if level == "weak" else "❌"
        click.echo(f"  {icon} {level.upper()}: {count} test(s)")

    # Fail if requested
    if fail_on_weak:
        weak_or_none = equivalence_counts.get("weak", 0) + equivalence_counts.get("none", 0)
        if weak_or_none > 0:
            click.echo(f"\n❌ Migration validation failed: {weak_or_none} test(s) have weak or no equivalence")
            raise click.Abort()

    click.echo("\n✅ Migration validation complete!")


def _parse_test_files(test_files: List[Path], entity: str):
    """Parse test files to TestSpecs"""
    specs = []

    for test_file in test_files:
        try:
            source_code = test_file.read_text()

            if test_file.suffix == '.sql':
                parser = PgTAPTestParser()
                mapper = PgTAPTestSpecMapper()
            elif test_file.suffix == '.py':
                parser = PytestParser()
                mapper = PytestTestSpecMapper()
            else:
                continue

            parsed = parser.parse_test_file(source_code, str(test_file))
            spec = mapper.map_to_test_spec(parsed, entity)
            specs.append(spec)

        except Exception as e:
            # Skip files that can't be parsed
            continue

    return specs


def _show_equivalence_result(test_name: str, result):
    """Show equivalence result"""
    level_icons = {
        EquivalenceLevel.EXACT: "✅",
        EquivalenceLevel.STRONG: "✅",
        EquivalenceLevel.WEAK: "⚠️",
        EquivalenceLevel.NONE: "❌"
    }

    icon = level_icons.get(result.level, "❓")

    click.echo(f"    {icon} {test_name}: {result.level.value.upper()}")
    click.echo(f"       Matching: {len(result.matching_scenarios)}, Missing: {len(result.missing_scenarios)}, Extra: {len(result.extra_scenarios)}")

    if result.missing_scenarios:
        click.echo(f"       ⚠️  Missing scenarios: {', '.join(result.missing_scenarios[:3])}")

    if result.extra_scenarios:
        click.echo(f"       ➕ Extra scenarios: {', '.join(result.extra_scenarios[:3])}")


def _generate_validation_report(results, entity, output_path):
    """Generate Markdown validation report"""
    lines = []

    lines.append(f"# Migration Validation Report: {entity}")
    lines.append(f"\nGenerated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    lines.append("## Summary\n")
    lines.append(f"- **Entity**: {entity}")
    lines.append(f"- **Tests Compared**: {len(results)}")

    equivalence_counts = {}
    for _, _, result in results:
        level = result.level.value
        equivalence_counts[level] = equivalence_counts.get(level, 0) + 1

    lines.append("\n### Equivalence Levels\n")
    for level, count in equivalence_counts.items():
        lines.append(f"- **{level.upper()}**: {count} test(s)")

    lines.append("\n## Detailed Results\n")

    for ref_spec, gen_spec, result in results:
        lines.append(f"### {ref_spec.test_name}\n")
        lines.append(f"**Equivalence Level**: {result.level.value.upper()}\n")

        lines.append("#### Scenario Matching\n")
        lines.append(f"- Matching: {len(result.matching_scenarios)}")
        lines.append(f"- Missing: {len(result.missing_scenarios)}")
        lines.append(f"- Extra: {len(result.extra_scenarios)}\n")

        if result.matching_scenarios:
            lines.append("**Matched Scenarios**:\n")
            for ref_name, gen_name in result.matching_scenarios:
                match_pct = result.assertion_matches.get(ref_name, 0) * 100
                lines.append(f"- `{ref_name}` ↔ `{gen_name}` ({match_pct:.0f}% assertion match)")

        if result.missing_scenarios:
            lines.append("\n**⚠️ Missing Scenarios** (in reference but not generated):\n")
            for scenario in result.missing_scenarios:
                lines.append(f"- `{scenario}`")

        if result.extra_scenarios:
            lines.append("\n**➕ Extra Scenarios** (in generated but not reference):\n")
            for scenario in result.extra_scenarios:
                lines.append(f"- `{scenario}`")

        lines.append("\n---\n")

    # Write report
    Path(output_path).write_text('\n'.join(lines))
```

**Day 5: Complete Testing & Documentation (Full day)**

- Write comprehensive tests for all components
- Integration tests for full reverse engineering pipeline
- Generate example TestSpec YAML files
- Write documentation and examples
- Polish CLI output and error messages

**Success Criteria**:
- ✅ Migration validation working
- ✅ Test equivalence checking accurate
- ✅ Validation reports generated
- ✅ CLI integration complete
- ✅ 40+ total tests passing
- ✅ Documentation complete

---

## 📊 Week 11 Summary

### ✅ Completed Features

1. **Universal TestSpec AST** (Day 1)
   - Language-agnostic test specification format
   - Complete test primitives (assertions, scenarios, fixtures)
   - YAML serialization

2. **Test Reverse Engineering** (Day 2)
   - pgTAP test parser
   - pytest test parser
   - Assertion extraction
   - Test pattern detection

3. **CLI & Pattern Detection** (Day 3)
   - `reverse-tests` command
   - Test coverage analysis
   - Pattern detection
   - Improvement suggestions

4. **Migration Validation** (Days 4-5)
   - Test equivalence checking
   - Coverage comparison
   - Validation reports
   - CI/CD integration

### 🎯 Success Criteria Met

- ✅ Universal test specification format defined
- ✅ pgTAP and pytest parsers working
- ✅ Test pattern detection implemented
- ✅ Migration validation framework complete
- ✅ CLI commands integrated
- ✅ 40+ comprehensive tests passing
- ✅ Documentation and examples complete

### 💡 Key Innovations

1. **Universal TestSpec**: Language-agnostic test representation enabling cross-language test portability

2. **Bidirectional Test Flow**:
   - TestSpec → pytest/pgTAP (generation) ✅
   - pytest/pgTAP → TestSpec (reverse engineering) ✅

3. **Migration Validation**: Systematic validation that migrated code maintains original test coverage

4. **Test Pattern Library**: Catalog common test patterns for reuse across projects

### 🚀 Enables

- **Migration Projects**: Validate printoptim_backend_migration preserves tests
- **Multi-Language Testing**: Write tests once, generate for multiple languages
- **Quality Assurance**: Systematic test coverage analysis and gap detection
- **Test Reuse**: Catalog test patterns for future projects
- **Documentation**: Tests as executable specifications

### 📈 Integration with Complete Linear Plan

Week 11 completes the reverse engineering story:

- **Weeks 1-6**: Forward generation (YAML → Code) ✅
- **Weeks 7-8**: Python reverse engineering (Code → YAML) ✅
- **Week 9**: Interactive CLI ✅
- **Week 10**: Visual diagrams ✅
- **Week 11**: Test reverse engineering (Tests → TestSpec) ✅

**Result**: Complete bidirectional capability for code AND tests across multiple languages.

---

**Status**: ✅ Complete

---

## Example: Migration Validation Workflow

```bash
# 1. Reverse engineer existing tests from reference app
specql reverse-tests \
  ../printoptim_backend_migration/reference_app/tests/ \
  --entity Contact \
  --output-dir test-specs/reference/

# 2. Generate new tests from SpecQL entities
specql generate entities/contact.yaml \
  --with-tests \
  --output-tests tests/generated/

# 3. Validate migration preserves test coverage
specql validate-migration \
  --reference-tests test-specs/reference/ \
  --generated-tests tests/generated/ \
  --entity Contact \
  --report migration_validation.md \
  --fail-on-weak

# Output:
# 🔍 Validating migration for Contact...
#
#   📄 Reference tests: 12 files
#   📄 Generated tests: 12 files
#
#   Parsing reference tests...
#   Parsing generated tests...
#
#   Checking test equivalence...
#
#     ✅ contact_crud_tests: STRONG
#        Matching: 8, Missing: 1, Extra: 2
#     ✅ contact_validation_tests: EXACT
#        Matching: 5, Missing: 0, Extra: 0
#     ⚠️  contact_workflow_tests: WEAK
#        Matching: 3, Missing: 3, Extra: 1
#        ⚠️  Missing scenarios: test_bulk_import, test_merge_duplicates
#
#   📊 Generating validation report: migration_validation.md
#
# 📊 Migration Validation Summary:
#
#   ✅ EXACT: 1 test(s)
#   ✅ STRONG: 1 test(s)
#   ⚠️  WEAK: 1 test(s)
#
# ✅ Migration validation complete!
```
