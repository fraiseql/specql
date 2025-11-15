"""
Test Parser Protocols

This module defines protocols for parsing different test languages into
universal TestSpec format. These protocols enable language-agnostic
test reverse engineering and cross-language test equivalence.
"""

from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from src.testing.spec.spec_models import TestSpec


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
    test_functions: List["ParsedTestFunction"]
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

    def extract_assertions(
        self, test_function: ParsedTestFunction
    ) -> List[Dict[str, Any]]:
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

    def categorize_scenario(self, test_function: ParsedTestFunction):
        """
        Determine scenario category from test function

        Heuristics:
            - "happy_path", "success", "valid" → HAPPY_PATH
            - "error", "fail", "invalid", "raises" → ERROR_CASE
            - "edge", "boundary", "limit" → EDGE_CASE/BOUNDARY
            - "security", "auth", "permission" → SECURITY
        """
        from src.testing.spec.spec_models import ScenarioCategory

        function_name = test_function.function_name.lower()
        docstring = (test_function.docstring or "").lower()

        combined = function_name + " " + docstring

        if any(
            word in combined
            for word in ["error", "fail", "invalid", "raises", "exception"]
        ):
            return ScenarioCategory.ERROR_CASE
        elif any(word in combined for word in ["edge", "extreme"]):
            return ScenarioCategory.EDGE_CASE
        elif any(word in combined for word in ["boundary", "limit", "max", "min"]):
            return ScenarioCategory.BOUNDARY
        elif any(
            word in combined
            for word in ["security", "auth", "permission", "unauthorized"]
        ):
            return ScenarioCategory.SECURITY
        elif any(word in combined for word in ["performance", "speed", "benchmark"]):
            return ScenarioCategory.PERFORMANCE
        else:
            return ScenarioCategory.HAPPY_PATH
