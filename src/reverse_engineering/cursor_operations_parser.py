"""
Parse SQL cursor operations into SpecQL steps

Handles PostgreSQL PL/pgSQL cursor syntax:
- CURSOR variable declarations
- OPEN cursor statements
- FETCH cursor INTO variable statements
- CLOSE cursor statements
- MOVE cursor statements
"""

import re
from typing import List, Tuple
from src.core.ast_models import ActionStep


class CursorOperationsParser:
    """Parse cursor operations from PL/pgSQL functions"""

    def __init__(self):
        self.confidence_boost = 0.20  # Increased confidence boost for proper parsing

    def parse(self, sql_text: str) -> List[ActionStep]:
        """
        Parse cursor operations from SQL text

        Args:
            sql_text: SQL text containing cursor operations

        Returns:
            List of ActionStep objects representing cursor operations
        """
        steps = []

        # Parse cursor declarations
        steps.extend(self._parse_cursor_declarations(sql_text))

        # Parse cursor operations
        steps.extend(self._parse_cursor_operations(sql_text))

        return steps

    def _parse_cursor_declarations(self, sql_text: str) -> List[ActionStep]:
        """Parse CURSOR variable declarations"""
        steps = []

        # Pattern: variable_name CURSOR FOR SELECT ...
        # Case insensitive, multiline support
        cursor_pattern = r"(\w+)\s+CURSOR\s+FOR\s+(.+?);"
        matches = re.findall(cursor_pattern, sql_text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            cursor_name, cursor_query = match
            cursor_query = cursor_query.strip()

            steps.append(
                ActionStep(type="cursor_declare", variable_name=cursor_name, sql=cursor_query)
            )

        return steps

    def _parse_cursor_operations(self, sql_text: str) -> List[ActionStep]:
        """Parse cursor operations (OPEN, FETCH, CLOSE)"""
        steps = []

        # Split into statements for individual processing
        statements = [s.strip() for s in sql_text.split(";") if s.strip()]

        for stmt in statements:
            stmt_upper = stmt.upper()

            # Parse OPEN statements: OPEN cursor_name
            if stmt_upper.startswith("OPEN "):
                cursor_name = stmt[5:].strip()
                steps.append(ActionStep(type="cursor_open", variable_name=cursor_name))

            # Parse FETCH statements: FETCH cursor_name INTO variable
            elif stmt_upper.startswith("FETCH "):
                fetch_parts = self._parse_fetch_statement(stmt)
                if fetch_parts:
                    cursor_name, into_var = fetch_parts
                    steps.append(
                        ActionStep(
                            type="cursor_fetch", variable_name=cursor_name, store_result=into_var
                        )
                    )

            # Parse CLOSE statements: CLOSE cursor_name
            elif stmt_upper.startswith("CLOSE "):
                cursor_name = stmt[6:].strip()
                steps.append(ActionStep(type="cursor_close", variable_name=cursor_name))

            # Also check for FETCH statements inside LOOP blocks
            elif "LOOP" in stmt_upper and "FETCH" in stmt_upper:
                # Extract FETCH statements from within LOOP blocks
                loop_fetch_steps = self._parse_fetch_in_loop(stmt)
                steps.extend(loop_fetch_steps)

        return steps

    def _parse_fetch_statement(self, fetch_stmt: str) -> Tuple[str, str] | None:
        """
        Parse FETCH statement to extract cursor name and INTO variable

        Args:
            fetch_stmt: FETCH statement like "FETCH cursor_name INTO variable"

        Returns:
            Tuple of (cursor_name, into_variable) or None if parsing fails
        """
        # Pattern: FETCH cursor_name INTO variable_name
        fetch_pattern = r"FETCH\s+(\w+)\s+INTO\s+(\w+)"
        match = re.search(fetch_pattern, fetch_stmt, re.IGNORECASE)

        if match:
            cursor_name, into_var = match.groups()
            return cursor_name, into_var

        return None

    def _parse_fetch_in_loop(self, loop_stmt: str) -> List[ActionStep]:
        """
        Parse FETCH statements that appear inside LOOP blocks

        Args:
            loop_stmt: LOOP statement containing FETCH operations

        Returns:
            List of cursor_fetch ActionStep objects
        """
        steps = []

        # Find all FETCH statements within the LOOP block
        fetch_pattern = r"FETCH\s+(\w+)\s+INTO\s+(\w+)"
        matches = re.findall(fetch_pattern, loop_stmt, re.IGNORECASE)

        for match in matches:
            cursor_name, into_var = match
            steps.append(
                ActionStep(type="cursor_fetch", variable_name=cursor_name, store_result=into_var)
            )

        return steps
