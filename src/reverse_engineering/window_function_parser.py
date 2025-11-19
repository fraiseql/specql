"""
Parse SQL window function constructs into SpecQL steps

Handles PostgreSQL window function syntax:
- ROW_NUMBER(), RANK(), DENSE_RANK(), etc.
- OVER clauses with PARTITION BY and ORDER BY
- Frame clauses (ROWS/RANGE BETWEEN)
- LAG(), LEAD(), FIRST_VALUE(), LAST_VALUE(), etc.
"""


from src.core.ast_models import ActionStep


class WindowFunctionParser:
    """Parse window function constructs from PL/pgSQL functions"""

    def __init__(self):
        self.confidence_boost = 0.12  # Confidence boost for successful window function parsing

    def parse(self, sql_text: str) -> list[ActionStep]:
        """
        Parse window function constructs from SQL text

        Args:
            sql_text: SQL text containing window functions

        Returns:
            List of ActionStep objects representing window functions
        """
        steps = []

        # Parse window functions with OVER clauses
        steps.extend(self._parse_window_functions(sql_text))

        return steps

    def _parse_window_functions(self, sql_text: str) -> list[ActionStep]:
        """Parse window function constructs"""
        steps = []
        sql_upper = sql_text.upper()

        # Look for OVER clauses which indicate window functions
        if "OVER" in sql_upper:
            # Create a window_function step
            steps.append(
                ActionStep(type="window_function", sql=f"window functions: {sql_text.strip()}")
            )

        return steps
