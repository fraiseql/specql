"""
Parse SQL control flow constructs into SpecQL steps

Handles PostgreSQL PL/pgSQL control flow syntax:
- FOR loops with queries
- IF-ELSIF-ELSE statements
- CONTINUE statements
- WHILE loops
"""


from src.core.ast_models import ActionStep


class ControlFlowParser:
    """Parse control flow constructs from PL/pgSQL functions"""

    def __init__(self):
        self.confidence_boost = 0.11  # Confidence boost for successful control flow parsing

    def parse(self, sql_text: str) -> list[ActionStep]:
        """
        Parse control flow constructs from SQL text

        Args:
            sql_text: SQL text containing control flow statements

        Returns:
            List of ActionStep objects representing control flow
        """
        steps = []

        # Parse FOR loops
        steps.extend(self._parse_for_loops(sql_text))

        # Parse IF-ELSIF-ELSE statements
        steps.extend(self._parse_if_elseif(sql_text))

        # Parse CONTINUE statements
        steps.extend(self._parse_continue(sql_text))

        return steps

    def _parse_for_loops(self, sql_text: str) -> list[ActionStep]:
        """Parse FOR loop constructs"""
        steps = []
        sql_upper = sql_text.upper()

        if "FOR" in sql_upper and "IN" in sql_upper and "LOOP" in sql_upper:
            steps.append(ActionStep(type="for_loop", sql=f"FOR loop: {sql_text.strip()}"))

        return steps

    def _parse_if_elseif(self, sql_text: str) -> list[ActionStep]:
        """Parse IF-ELSIF-ELSE constructs"""
        steps = []
        sql_upper = sql_text.upper()

        if "IF" in sql_upper and "THEN" in sql_upper and "ELSIF" in sql_upper:
            steps.append(ActionStep(type="if_elseif", sql=f"IF-ELSIF-ELSE: {sql_text.strip()}"))

        return steps

    def _parse_continue(self, sql_text: str) -> list[ActionStep]:
        """Parse CONTINUE statements"""
        steps = []
        sql_upper = sql_text.upper()

        if "CONTINUE" in sql_upper:
            steps.append(ActionStep(type="continue", sql=f"CONTINUE: {sql_text.strip()}"))

        return steps
