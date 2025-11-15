"""
Function Analyzer

Parse PL/pgSQL functions to SpecQL actions.
"""

from typing import List, Dict, Any, Optional
import re
from src.core.universal_ast import UniversalAction, UniversalStep, StepType


class FunctionAnalyzer:
    """Analyze PL/pgSQL functions and convert to actions"""

    def parse_functions(self, functions: List[Dict[str, Any]]) -> List[UniversalAction]:
        """
        Parse list of PL/pgSQL functions to actions

        Args:
            functions: List of function definitions from database

        Returns:
            List of UniversalAction objects
        """
        actions = []

        for func in functions:
            action = self.parse_function(func)
            if action:
                actions.append(action)

        return actions

    def parse_function(self, function: Dict[str, Any]) -> Optional[UniversalAction]:
        """
        Parse single PL/pgSQL function to action

        Args:
            function: Function definition dict with:
                - routine_name: function name
                - routine_definition: PL/pgSQL code
                - external_language: should be 'plpgsql'

        Returns:
            UniversalAction or None if cannot parse
        """
        if function["external_language"].upper() != "PLPGSQL":
            return None

        action_name = function["routine_name"]
        function_body = function["routine_definition"]

        # Parse function body to steps
        steps = self._parse_function_body(function_body)

        if not steps:
            return None

        # Create action
        action = UniversalAction(
            name=action_name,
            entity=self._extract_entity_from_function_name(action_name),
            steps=steps,
            impacts=[],  # TODO: Analyze which tables are affected
        )

        return action

    def _parse_function_body(self, body: str) -> List[UniversalStep]:
        """
        Parse PL/pgSQL function body to action steps

        Detects:
            - IF statements → validate steps
            - UPDATE statements → update steps
            - INSERT statements → insert steps
            - DELETE statements → delete steps
            - RAISE EXCEPTION → error steps
        """
        steps = []

        # Split body into statements
        statements = self._split_statements(body)

        for stmt in statements:
            step = self._parse_statement(stmt)
            if step:
                steps.append(step)

        return steps

    def _split_statements(self, body: str) -> List[str]:
        """Split function body into individual statements"""
        # Remove comments
        body = re.sub(r"--[^\n]*", "", body)
        body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)

        # Remove BEGIN and END wrappers if present
        body = re.sub(r"^\s*BEGIN\s*", "", body, flags=re.IGNORECASE)
        body = re.sub(r"\s*END\s*$", "", body, flags=re.IGNORECASE)

        # Split by semicolons
        statements = [s.strip() for s in body.split(";") if s.strip()]

        return statements

    def _parse_statement(self, stmt: str) -> Optional[UniversalStep]:
        """Parse single PL/pgSQL statement to step"""
        stmt_upper = stmt.upper().strip()

        # IF statement → validate step
        if stmt_upper.startswith("IF"):
            return self._parse_if_statement(stmt)

        # UPDATE statement → update step
        if stmt_upper.startswith("UPDATE"):
            return self._parse_update_statement(stmt)

        # INSERT statement → insert step
        if stmt_upper.startswith("INSERT"):
            return self._parse_insert_statement(stmt)

        # DELETE statement → delete step
        if stmt_upper.startswith("DELETE"):
            return self._parse_delete_statement(stmt)

        # RAISE EXCEPTION → error step
        if "RAISE EXCEPTION" in stmt_upper:
            return self._parse_raise_exception(stmt)

        return None

    def _parse_if_statement(self, stmt: str) -> Optional[UniversalStep]:
        """
        Parse IF statement to validate step

        Example:
            IF status != 'pending' THEN
                RAISE EXCEPTION 'not_pending';
            END IF;

        → validate: status = 'pending'
        """
        # Extract condition
        pattern = r"IF\s+(.+?)\s+THEN"
        match = re.search(pattern, stmt, re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        condition = match.group(1).strip()

        # Invert condition (IF NOT x → validate x)
        inverted_condition = self._invert_condition(condition)

        return UniversalStep(type=StepType.VALIDATE, expression=inverted_condition)

    def _parse_update_statement(self, stmt: str) -> Optional[UniversalStep]:
        """
        Parse UPDATE statement to update step

        Example:
            UPDATE contact SET status = 'active' WHERE pk_contact = v_pk_contact

        → update: Contact SET status = 'active'
        """
        # Extract table and SET clause
        pattern = r"UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE|$)"
        match = re.search(pattern, stmt, re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        table = match.group(1)
        set_clause = match.group(2).strip()

        # Convert table name to entity name
        entity_name = self._table_to_entity_name(table)

        # Parse SET clause to field updates
        fields = self._parse_set_clause(set_clause)

        return UniversalStep(type=StepType.UPDATE, entity=entity_name, fields=fields)

    def _parse_insert_statement(self, stmt: str) -> Optional[UniversalStep]:
        """
        Parse INSERT statement to insert step

        Example:
            INSERT INTO contact (email, name) VALUES (p_email, p_name)
            INSERT INTO schema.table (col) VALUES (val)

        → insert: Contact
        """
        # Extract table name from INSERT statement (handle schema.table format)
        pattern = r"INSERT\s+INTO\s+([.\w]+)\s+"
        match = re.search(pattern, stmt, re.IGNORECASE)

        if not match:
            return None

        table_full = match.group(1)

        # Extract just the table name (remove schema prefix if present)
        table = table_full.split(".")[-1]

        # Convert table name to entity name
        entity_name = self._table_to_entity_name(table)

        return UniversalStep(type=StepType.INSERT, entity=entity_name)

    def _parse_delete_statement(self, stmt: str) -> Optional[UniversalStep]:
        """Parse DELETE statement to delete step"""
        # Extract table name from DELETE statement (handle schema.table format)
        pattern = r"DELETE\s+FROM\s+([.\w]+)\s+"
        match = re.search(pattern, stmt, re.IGNORECASE)

        if not match:
            return None

        table_full = match.group(1)

        # Extract just the table name (remove schema prefix if present)
        table = table_full.split(".")[-1]

        # Convert table name to entity name
        entity_name = self._table_to_entity_name(table)

        return UniversalStep(type=StepType.DELETE, entity=entity_name)

    def _parse_raise_exception(self, stmt: str) -> Optional[UniversalStep]:
        """
        Parse RAISE EXCEPTION to error code

        Example:
            RAISE EXCEPTION 'not_pending'

        → validate step with error code
        """
        pattern = r"RAISE\s+EXCEPTION\s+'([^']+)'"
        match = re.search(pattern, stmt, re.IGNORECASE)

        if match:
            error_code = match.group(1)
            # Store error code in expression
            return UniversalStep(
                type=StepType.VALIDATE,
                expression=f"error_code = '{error_code}'",  # Will fail with error code
            )

        return None

    def _invert_condition(self, condition: str) -> str:
        """
        Invert a boolean condition

        Examples:
            status != 'pending' → status = 'pending'
            is_active = false → is_active = true
        """
        # Replace != with =
        if "!=" in condition:
            condition = condition.replace("!=", "=")
        # Replace <> with =
        elif "<>" in condition:
            condition = condition.replace("<>", "=")
        # TODO: Handle more complex inversions

        return condition

    def _parse_set_clause(self, set_clause: str) -> Dict[str, Any]:
        """
        Parse SET clause to field→value mapping

        Example:
            status = 'active', updated_at = NOW()

        → {'status': "'active'", 'updated_at': 'NOW()'}
        """
        fields = {}

        # Split by commas
        assignments = set_clause.split(",")

        for assignment in assignments:
            parts = assignment.split("=", 1)
            if len(parts) == 2:
                field_name = parts[0].strip()
                value = parts[1].strip()
                fields[field_name] = value

        return fields

    def _table_to_entity_name(self, table: str) -> str:
        """Convert table name to entity name"""
        # Remove tb_ prefix
        name = re.sub(r"^tb_", "", table, flags=re.IGNORECASE)

        # Convert to PascalCase (all words)
        parts = name.split("_")
        return "".join(word.capitalize() for word in parts) if parts else "Unknown"

    def _extract_entity_from_function_name(self, func_name: str) -> str:
        """
        Extract entity name from function name

        Examples:
            create_contact → Contact
            update_order_status → OrderStatus
            app_create_lead → Lead
            core_update_user_profile → UserProfile
        """
        # Remove schema prefix if present
        if "." in func_name:
            func_name = func_name.split(".")[-1]

        # Remove action prefixes (can have multiple)
        prefixes = ["create_", "update_", "delete_", "app_", "core_"]
        while True:
            removed = False
            for prefix in prefixes:
                if func_name.startswith(prefix):
                    func_name = func_name[len(prefix) :]
                    removed = True
                    break
            if not removed:
                break

        # Convert to PascalCase (capitalize first word after removing prefixes)
        parts = func_name.split("_")
        return parts[0].capitalize() if parts else "Unknown"
