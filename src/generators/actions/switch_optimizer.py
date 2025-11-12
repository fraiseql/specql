"""Switch statement optimization utilities"""

from typing import List
from src.core.ast_models import SwitchCase


class SwitchOptimizer:
    """Optimizes switch/case statements for better compilation"""

    @staticmethod
    def detect_simple_switch(cases: List[SwitchCase], switch_expression: str | None) -> bool:
        """
        Determine if a switch can use simple CASE WHEN syntax

        Returns True if all cases are simple value matches, False if complex conditions
        """
        if not switch_expression:
            return False

        # Check if all cases have simple when_value (not when_condition)
        for case in cases:
            if case.when_condition is not None:
                return False

        return True

    @staticmethod
    def optimize_case_order(cases: List[SwitchCase]) -> List[SwitchCase]:
        """
        Optimize case order for better performance

        Currently a no-op, but could reorder cases based on frequency
        """
        return cases

    @staticmethod
    def validate_switch_cases(cases: List[SwitchCase]) -> None:
        """
        Validate that switch cases are well-formed

        Raises ValueError if cases are invalid
        """
        if not cases:
            raise ValueError("Switch must have at least one case")

        for case in cases:
            if case.when_value is None and case.when_condition is None:
                raise ValueError("Case must have either when_value or when_condition")
            if case.when_value is not None and case.when_condition is not None:
                raise ValueError("Case cannot have both when_value and when_condition")