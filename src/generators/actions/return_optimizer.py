"""Early return optimization utilities"""

from typing import List
from src.core.ast_models import ActionStep


class ReturnOptimizer:
    """Optimizes early return statements"""

    @staticmethod
    def detect_unreachable_code_after_return(steps: List[ActionStep], start_index: int) -> List[int]:
        """
        Detect steps that become unreachable after an early return

        Returns list of indices of unreachable steps
        """
        unreachable = []

        for i in range(start_index + 1, len(steps)):
            step = steps[i]
            if step.type in ("return", "return_early"):
                # Another return makes everything after it unreachable too
                unreachable.extend(range(i, len(steps)))
                break
            elif step.type in ("if", "switch"):
                # Control flow - check if it contains returns
                if ReturnOptimizer._step_contains_return(step):
                    # If the control flow always returns, subsequent steps are unreachable
                    unreachable.extend(range(i + 1, len(steps)))
                    break
                else:
                    # Control flow doesn't always return, so subsequent steps are reachable
                    break
            else:
                # Regular step - mark as unreachable
                unreachable.append(i)

        return unreachable

    @staticmethod
    def _step_contains_return(step: ActionStep) -> bool:
        """Check if a step contains return statements"""
        if step.type in ("return", "return_early"):
            return True

        # Check nested steps
        if hasattr(step, 'then_steps') and step.then_steps:
            if any(s.type in ("return", "return_early") for s in step.then_steps):
                return True

        if hasattr(step, 'else_steps') and step.else_steps:
            if any(s.type in ("return", "return_early") for s in step.else_steps):
                return True

        if hasattr(step, 'cases') and step.cases:
            for case in step.cases:
                if any(s.type in ("return", "return_early") for s in case.then_steps):
                    return True

        if hasattr(step, 'default_steps') and step.default_steps:
            if any(s.type in ("return", "return_early") for s in step.default_steps):
                return True

        return False

    @staticmethod
    def can_optimize_return_placement(steps: List[ActionStep]) -> bool:
        """
        Check if returns can be reordered for better performance

        Currently a placeholder for future optimization
        """
        return False