"""
Parse SQL EXECUTE statements into SpecQL dynamic SQL constructs

Handles PostgreSQL PL/pgSQL dynamic SQL syntax:
- EXECUTE query_text
- EXECUTE query_text USING parameters
- EXECUTE IMMEDIATE (future extension)
"""

from typing import List
from src.core.ast_models import ActionStep


class DynamicSQLParser:
    """Parse EXECUTE statements from PL/pgSQL functions"""

    def __init__(self):
        self.confidence_boost = 0.12  # Confidence boost for successful dynamic SQL parsing

    def parse(self, sql_text: str) -> List[ActionStep]:
        """
        Parse EXECUTE statement from SQL text

        Args:
            sql_text: SQL text containing EXECUTE statement

        Returns:
            List of ActionStep objects representing dynamic SQL execution
        """
        steps = []

        # Look for EXECUTE statements
        lines = sql_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.upper().startswith("EXECUTE"):
                steps.append(ActionStep(type="execute", sql=f"dynamic sql: {line}"))

        return steps
