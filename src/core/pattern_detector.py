"""Detect common patterns in SpecQL actions for optimization"""

from src.core.ast_models import Action


class PatternDetector:
    """Detects and optimizes common action patterns"""

    @staticmethod
    def detect_aggregate_pattern(action: Action) -> bool:
        """Detect if action is a simple aggregate query"""
        if len(action.steps) == 2:
            return (
                action.steps[0].type == "declare" and
                action.steps[1].type == "query" and
                bool(action.steps[1].expression) and
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