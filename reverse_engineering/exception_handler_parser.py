"""
Parse SQL EXCEPTION blocks into SpecQL try/except constructs

Handles PostgreSQL PL/pgSQL exception handling syntax:
- EXCEPTION WHEN condition THEN action
- Multiple WHEN clauses
- WHEN OTHERS clause
"""

from typing import Any

from core.ast_models import ActionStep


class ExceptionHandlerParser:
    """Parse EXCEPTION blocks from PL/pgSQL functions"""

    def __init__(self):
        self.confidence_boost = 0.15  # Confidence boost for successful exception parsing

    def parse(self, sql_text: str) -> list[ActionStep]:
        """
        Parse EXCEPTION block from SQL text

        Args:
            sql_text: SQL text containing EXCEPTION block

        Returns:
            List of ActionStep objects representing the exception handling
        """
        steps = []

        # Split on EXCEPTION keyword
        parts = sql_text.upper().split("EXCEPTION", 1)
        if len(parts) != 2:
            return steps

        parts[0].strip()
        exception_block = parts[1].strip()

        # Parse exception handlers
        self._parse_exception_handlers(exception_block)

        # Create try/except step
        steps.append(
            ActionStep(
                type="try_except",
                sql=f"EXCEPTION {exception_block}",
                then_steps=[],  # Could be extended to parse individual handlers
                else_steps=[],  # Could be extended for WHEN OTHERS
            )
        )

        return steps

    def _parse_exception_handlers(self, exception_text: str) -> list[dict[str, Any]]:
        """
        Parse individual WHEN clauses from exception block

        Args:
            exception_text: Text after EXCEPTION keyword

        Returns:
            List of handler dictionaries with condition and action
        """
        handlers = []

        # Split by WHEN keywords
        when_parts = exception_text.upper().split("WHEN")
        for part in when_parts[1:]:  # Skip first empty part
            part = part.strip()
            if "THEN" in part.upper():
                condition, action = part.upper().split("THEN", 1)
                handlers.append({"condition": condition.strip(), "action": action.strip()})

        return handlers
