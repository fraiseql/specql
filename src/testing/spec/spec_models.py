"""
Universal Test Specification Models

This module defines the AST (Abstract Syntax Tree) for universal test specifications.
These models enable language-agnostic representation of tests, allowing conversion
between different testing frameworks (pytest, pgTAP, Jest, etc.).

Key Features:
- Language-agnostic test representation
- Rich type system for assertions and scenarios
- YAML serialization for portability
- Extensible for new test patterns and frameworks
"""

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

        return yaml.dump(spec_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def _scenario_to_dict(self, scenario: TestScenario) -> Dict[str, Any]:
        """Convert scenario to dict"""
        result = {
            "name": scenario.scenario_name,
            "description": scenario.description,
            "category": scenario.category.value,
        }

        if scenario.setup_steps:
            result["setup"] = [self._step_to_dict(s) for s in scenario.setup_steps]
        if scenario.action_steps:
            result["action"] = [self._step_to_dict(s) for s in scenario.action_steps]
        if scenario.assertions:
            result["assertions"] = [self._assertion_to_dict(a) for a in scenario.assertions]
        if scenario.teardown_steps:
            result["teardown"] = [self._step_to_dict(s) for s in scenario.teardown_steps]
        if scenario.fixtures:
            result["fixtures"] = scenario.fixtures
        if scenario.tags:
            result["tags"] = scenario.tags

        return result

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