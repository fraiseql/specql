"""
pytest Test Parser

Parses pytest test files into universal TestSpec format.

pytest is a mature testing framework for Python that supports fixtures,
parametrization, and various assertion styles. This parser extracts test
functions, fixtures, assertions, and metadata from pytest test files.

Supported pytest features:
- Standard assert statements
- pytest.raises() context managers
- pytest fixtures (function, class, module scope)
- Parametrized tests
- Test classes and methods
"""

import ast
from typing import List, Dict, Any
from pathlib import Path
from src.testing.spec.spec_models import ScenarioCategory, TestAssertion

from src.testing.spec.test_parser_protocol import (
    ParsedTest,
    ParsedTestFunction,
    TestSourceLanguage,
)
from src.testing.spec.spec_models import TestSpec, TestType


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

    class TestContact:
        @pytest.fixture
        def test_contact(self, test_db):
            # Create test contact
            return create_contact(email="test@example.com", status="lead")

        def test_create_contact(self):
            '''Test: Create contact successfully'''
            result = create_contact("test@example.com")
            assert result.status == "success"

        def test_create_duplicate_error(self):
            '''Test: Raise error for duplicate email'''
            with pytest.raises(ValidationError):
                create_contact("existing@example.com")
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
            metadata={"file_path": file_path, "test_count": len(test_functions)},
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

    def _extract_fixtures(
        self, tree: ast.AST, source_code: str
    ) -> List[Dict[str, Any]]:
        """Extract pytest fixtures"""
        fixtures = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for @pytest.fixture decorator
                has_fixture_decorator = any(
                    (isinstance(d, ast.Name) and d.id == "fixture")
                    or (isinstance(d, ast.Attribute) and d.attr == "fixture")
                    or (
                        isinstance(d, ast.Call)
                        and (
                            (isinstance(d.func, ast.Name) and d.func.id == "fixture")
                            or (
                                isinstance(d.func, ast.Attribute)
                                and d.func.attr == "fixture"
                            )
                        )
                    )
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

                    fixtures.append(
                        {
                            "name": node.name,
                            "type": "pytest_fixture",
                            "scope": scope,
                            "body": fixture_lines,
                            "parameters": [
                                arg.arg for arg in node.args.args if arg.arg != "self"
                            ],
                        }
                    )

        return fixtures

    def _extract_test_functions(
        self, tree: ast.AST, source_code: str
    ) -> List[ParsedTestFunction]:
        """Extract test functions from AST"""
        test_functions = []

        # Find all classes and functions
        for node in ast.walk(tree):
            # Test functions (def test_*)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_func = self._parse_test_function(node, source_code)
                test_functions.append(test_func)

        return test_functions

    def _parse_test_function(
        self, func_node: ast.FunctionDef, source_code: str
    ) -> ParsedTestFunction:
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
            if not isinstance(stmt, ast.Expr) or not isinstance(
                stmt.value, ast.Constant
            ):
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
                "parameters": [
                    arg.arg for arg in func_node.args.args if arg.arg != "self"
                ],
            },
        )

    def _extract_assertions_from_function(
        self, func_node: ast.FunctionDef
    ) -> List[Dict[str, Any]]:
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
                "message": ast.unparse(assert_node.msg) if assert_node.msg else None,
            }
        else:
            # Boolean assertion
            return {
                "type": "equals",
                "target": ast.unparse(test_expr),
                "expected": True,
                "message": ast.unparse(assert_node.msg) if assert_node.msg else None,
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
            "message": f"Should raise {exception_type}"
            + (f" matching {match_pattern}" if match_pattern else ""),
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

    def extract_assertions(
        self, test_function: ParsedTestFunction
    ) -> List[Dict[str, Any]]:
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
        elif any(
            word in combined_names for word in ["validate", "validation", "invalid"]
        ):
            return TestType.VALIDATION.value

        # Workflow
        elif any(word in combined_names for word in ["workflow", "process", "flow"]):
            return TestType.WORKFLOW.value

        # Default
        return TestType.INTEGRATION.value


class PytestTestSpecMapper:
    """Maps pytest ParsedTest to universal TestSpec"""

    def map_to_test_spec(self, parsed_test: ParsedTest, entity_name: str) -> TestSpec:
        """Convert pytest ParsedTest to TestSpec"""
        from src.testing.spec.spec_models import (
            TestScenario,
            TestStep,
            TestFixture,
        )

        # Map test functions to scenarios
        scenarios = []
        for func in parsed_test.test_functions:
            category = self._categorize_pytest_test(func)

            # Map setup steps
            setup_steps = []
            for setup_call in func.setup_calls:
                setup_steps.append(
                    TestStep(
                        step_type="setup",
                        action="execute_code",
                        metadata={"code": setup_call},
                    )
                )

            # Map assertions
            assertions = []
            for assertion_dict in func.assertions:
                assertions.append(self._map_pytest_assertion(assertion_dict))

            scenarios.append(
                TestScenario(
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
                        "decorators": func.decorators,
                    },
                )
            )

        # Map fixtures
        fixtures = []
        for fixture_dict in parsed_test.fixtures:
            fixtures.append(
                TestFixture(
                    fixture_name=fixture_dict["name"],
                    fixture_type=fixture_dict["type"],
                    scope=fixture_dict.get("scope", "function"),
                    metadata={"body": fixture_dict.get("body")},
                )
            )

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
            coverage={"test_count": len(scenarios), "source_language": "pytest"},
            metadata=parsed_test.metadata,
        )

    def _categorize_pytest_test(self, func: ParsedTestFunction) -> "ScenarioCategory":
        """Categorize pytest test function"""
        from src.testing.spec.spec_models import ScenarioCategory

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
        from src.testing.spec.spec_models import AssertionType, TestAssertion

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
            metadata={"pytest_assertion": pytest_type, "source": "pytest"},
        )
