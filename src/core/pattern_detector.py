"""Detect common patterns in SpecQL actions for optimization"""

from src.core.ast_models import Action


class PatternDetector:
    """Detects and optimizes common action patterns"""

    @staticmethod
    def detect_aggregate_pattern(action: Action) -> bool:
        """Detect if action is a simple aggregate query"""
        if len(action.steps) == 2:
            expr = action.steps[1].expression
            return (
                action.steps[0].type == "declare"
                and action.steps[1].type == "query"
                and expr is not None
                and any(
                    agg in expr.upper() for agg in ["SUM", "COUNT", "AVG", "MAX", "MIN"]
                )
            )
        return False

    @staticmethod
    def detect_cte_chain(action: Action) -> list[str]:
        """Detect chain of dependent CTEs"""
        cte_names = []
        for step in action.steps:
            if step.type == "cte" and step.cte_name is not None:
                cte_names.append(step.cte_name)
        return cte_names
