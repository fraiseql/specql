"""
pgTAP Test Parser

Parses pgTAP SQL test files into universal TestSpec format.

pgTAP is a unit testing framework for PostgreSQL that provides TAP-compatible
output. This parser extracts test assertions, fixtures, and metadata from
pgTAP test files.

Supported pgTAP functions:
- ok() / is() / isnt() - Basic assertions
- throws_ok() / lives_ok() - Exception testing
- results_eq() / results_ne() - Query result comparison
- has_table() / has_column() / has_function() - Schema validation
"""

import re
from typing import List, Dict, Any
from pathlib import Path

from src.testing.spec.test_parser_protocol import (
    ParsedTest,
    ParsedTestFunction,
    TestSourceLanguage
)
from src.testing.spec.spec_models import (
    TestSpec,
    TestType,
    TestScenario,
    TestAssertion,
    TestFixture,
    ScenarioCategory,
    AssertionType
)


class PgTAPTestParser:
    """
    Parse pgTAP test files to universal TestSpec

    Supports pgTAP assertions:
        - ok() / is() / isnt()
        - throws_ok() / lives_ok()
        - results_eq() / results_ne()
        - has_table() / has_column() / has_function()
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
            # ok() / is() / isnt() - match entire SELECT statement
            (r'SELECT\s+(ok|is|isnt)\s*\([^;]*\)(?:\s*;\s*)?', 'assertion'),

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
                # Look for -- Test: ... pattern, preferring Test: comments
                position = match.start()
                lines_before = source_code[:position].split('\n')
                docstring = None
                test_comment = None
                for line in reversed(lines_before):
                    if line.strip().startswith('--'):
                        comment = line.strip()[2:].strip()
                        if comment.startswith('Test:'):
                            test_comment = comment[5:].strip()
                            break  # Found Test: comment, use it
                        elif docstring is None:
                            docstring = comment  # Use last non-Test comment as fallback

                # Prefer Test: comment, fallback to other comment
                final_docstring = test_comment or docstring

                # For ok/is/isnt, try to extract message if present
                message = None
                if assertion_category == 'assertion':
                    # Look for comma followed by quoted string at the end
                    assertion_content = match.group(0)
                    message_match = re.search(r',\s*\'([^\']*)\'\s*\)\s*;?\s*$', assertion_content)
                    if message_match:
                        message = message_match.group(1)

                test_functions.append(ParsedTestFunction(
                    function_name=function_name,
                    docstring=final_docstring,
                    decorators=[],
                    body_lines=[match.group(0)],
                    assertions=[{
                        "type": assertion_type,
                        "raw_assertion": match.group(0),
                        "message": message
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
                action_steps=[],
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

    def _categorize_pgtap_test(self, func: ParsedTestFunction) -> 'ScenarioCategory':
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