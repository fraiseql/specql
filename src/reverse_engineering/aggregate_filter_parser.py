"""
Parse SQL aggregate functions with FILTER clauses into SpecQL steps

Handles PostgreSQL aggregate functions with FILTER syntax:
- COUNT(*) FILTER (WHERE condition)
- SUM(column) FILTER (WHERE condition)
- AVG(column) FILTER (WHERE condition)
- Other aggregates with FILTER clauses
"""


from src.core.ast_models import ActionStep


class AggregateFilterParser:
    """Parse aggregate functions with FILTER clauses from PL/pgSQL functions"""

    def __init__(self):
        self.confidence_boost = 0.10  # Confidence boost for successful FILTER parsing

    def parse(self, sql_text: str) -> list[ActionStep]:
        """
        Parse aggregate functions with FILTER clauses from SQL text

        Args:
            sql_text: SQL text containing aggregate functions with FILTER

        Returns:
            List of ActionStep objects representing aggregate functions
        """
        steps = []

        # Parse aggregate functions with FILTER
        steps.extend(self._parse_aggregate_filters(sql_text))

        return steps

    def _parse_aggregate_filters(self, sql_text: str) -> list[ActionStep]:
        """Parse aggregate functions with FILTER clauses"""
        steps = []
        sql_upper = sql_text.upper()

        # Look for FILTER clauses in aggregate functions
        if "FILTER" in sql_upper and "WHERE" in sql_upper:
            # Create an aggregate step
            steps.append(
                ActionStep(type="aggregate", sql=f"aggregate with filter: {sql_text.strip()}")
            )

        return steps
