"""
Map SQL AST to SpecQL primitives

Algorithmic mapping without AI
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from src.core.ast_models import ActionStep
from src.reverse_engineering.parser_coordinator import ParserCoordinator

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of SQL → SpecQL conversion"""

    function_name: str
    schema: str
    parameters: list[dict[str, str]]
    return_type: str
    steps: list[ActionStep]
    confidence: float
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ASTToSpecQLMapper:
    """Map PostgreSQL AST to SpecQL primitives"""

    def __init__(self):
        self.confidence = 1.0
        self.warnings = []
        self.variables = {}  # Track declared variables

        # REPLACE all individual parsers with coordinator
        self.parser_coordinator = ParserCoordinator()

    def map_function(self, parsed_func) -> ConversionResult:
        """
        Map parsed function to SpecQL

        Args:
            parsed_func: ParsedFunction from SQLASTParser

        Returns:
            ConversionResult with SpecQL steps
        """
        self.confidence = 1.0
        self.warnings = []
        self.variables = {}

        # Parse function body
        if parsed_func.body:
            steps = self._parse_body_text(parsed_func.body)
        else:
            steps = []
            self.warnings.append("No function body found")
            self.confidence = 0.5

        return ConversionResult(
            function_name=parsed_func.function_name,
            schema=parsed_func.schema,
            parameters=parsed_func.parameters,
            return_type=parsed_func.return_type,
            steps=steps,
            confidence=self.confidence,
            warnings=self.warnings,
        )

    def _parse_body_text(self, body_text: str) -> list[ActionStep]:
        """Parse function body using simple text analysis (algorithmic approach)"""
        steps = []

        # Clean up the body text
        body_text = body_text.strip()
        if body_text.startswith("DECLARE"):
            # Split into DECLARE and BEGIN blocks
            parts = body_text.split("BEGIN", 1)
            if len(parts) == 2:
                declare_block = parts[0].strip()
                begin_block = "BEGIN" + parts[1]

                # Parse DECLARE block
                steps.extend(self._parse_declare_block(declare_block))

                # Parse BEGIN block
                steps.extend(self._parse_begin_block(begin_block))
        elif body_text.startswith("BEGIN"):
            # No DECLARE block
            steps.extend(self._parse_begin_block(body_text))
        else:
            # Fallback: treat as BEGIN block
            steps.extend(self._parse_begin_block(body_text))

        return steps

    def _parse_declare_block(self, declare_text: str) -> list[ActionStep]:
        """Parse DECLARE block for variable declarations and cursors"""
        steps = []

        # Skip the DECLARE keyword
        declare_content = declare_text[7:].strip()  # Remove 'DECLARE'

        # Handle cursor declarations in DECLARE block
        cursor_steps = self._parse_cursor_declarations_in_declare(declare_content)
        steps.extend(cursor_steps)

        # Then parse regular variable declarations
        # Split by semicolons to get individual declarations
        declarations = [d.strip() for d in declare_content.split(";") if d.strip()]

        for decl in declarations:
            # Skip cursor declarations (already handled above)
            if "CURSOR FOR" in decl.upper():
                continue

            # Parse regular variable declarations: var_name type [= default]
            import re

            var_pattern = r"^(\w+)\s+(\w+)(?:\s*:=\s*(.+))?$"
            match = re.match(var_pattern, decl.strip())

            if match:
                var_name, var_type, default_val = match.groups()
                var_type_lower = var_type.lower()

                # Map SQL types to SpecQL types
                type_map = {
                    "integer": "integer",
                    "numeric": "numeric",
                    "text": "text",
                    "boolean": "boolean",
                    "uuid": "uuid",
                    "record": "record",
                }
                specql_type = type_map.get(var_type_lower, var_type_lower)

                # Reduce confidence for unknown types
                if specql_type == var_type_lower and var_type_lower not in type_map.values():
                    self.confidence *= 0.95
                    self.warnings.append(f"Unknown variable type: {var_type}")

                steps.append(
                    ActionStep(
                        type="declare",
                        variable_name=var_name,
                        variable_type=specql_type,
                        default_value=default_val if default_val else None,
                    )
                )
            else:
                # Unknown declaration format
                self.confidence *= 0.95
                self.warnings.append(f"Unknown declaration: {decl[:50]}...")

        return steps

    def _parse_cursor_declarations_in_declare(self, declare_content: str) -> list[ActionStep]:
        """
        Parse cursor declarations from DECLARE block content

        Args:
            declare_content: Content after 'DECLARE' keyword (without DECLARE)

        Returns:
            List of cursor_declare ActionStep objects
        """
        steps = []

        # Split by semicolons to get individual declarations
        declarations = [d.strip() for d in declare_content.split(";") if d.strip()]

        for decl in declarations:
            # Look for cursor declarations: variable_name CURSOR FOR SELECT ...
            if "CURSOR FOR" in decl.upper():
                import re

                # Pattern: variable_name CURSOR FOR query
                cursor_pattern = r"(\w+)\s+CURSOR\s+FOR\s+(.+)"
                match = re.match(cursor_pattern, decl.strip(), re.IGNORECASE | re.DOTALL)

                if match:
                    cursor_name, cursor_query = match.groups()
                    cursor_query = cursor_query.strip()

                    # Clean up whitespace and newlines
                    cursor_query = " ".join(cursor_query.split())

                    steps.append(
                        ActionStep(
                            type="cursor_declare", variable_name=cursor_name, sql=cursor_query
                        )
                    )

        return steps

    def _parse_begin_block(self, begin_text: str) -> list[ActionStep]:
        """Parse BEGIN block with coordinated specialized parsers"""
        steps = []

        # Remove BEGIN and END
        if begin_text.upper().startswith("BEGIN"):
            begin_text = begin_text[5:]
        if begin_text.upper().endswith("END"):
            begin_text = begin_text[:-3]

        begin_text = begin_text.strip()

        # Strip comments before parsing
        begin_text = self._strip_sql_comments(begin_text)

        # Use ParserCoordinator to get all applicable parser results
        parser_results = self.parser_coordinator.parse_with_best_parsers(begin_text)

        # Process results
        for result in parser_results:
            # Add steps from parser
            steps.extend(result.steps)

            # Apply confidence boost
            self.confidence = min(1.0, self.confidence + result.confidence_boost)

            # Log parser usage
            logger.debug(
                f"Used {result.parser_used} parser (boost: {result.confidence_boost:+.2f})"
            )

        # If no specialized parsers matched, fall back to basic parsing
        if not parser_results:
            steps = self._parse_basic_statements(begin_text)

        return steps

    def _parse_basic_statements(self, begin_text: str) -> list[ActionStep]:
        """Parse basic SQL statements when no specialized parsers match"""
        steps = []

        # Split by semicolons to get individual statements
        statements = [s.strip() for s in begin_text.split(";") if s.strip()]

        for stmt in statements:
            stmt = stmt.strip()

            # RETURN QUERY statements
            if stmt.upper().startswith("RETURN QUERY"):
                query = stmt[12:].strip()  # Remove 'RETURN QUERY'
                steps.append(ActionStep(type="return_table", return_table_query=query))

            # RETURN statements
            elif stmt.upper().startswith("RETURN"):
                expr = stmt[6:].strip()
                steps.append(ActionStep(type="return", return_value=expr))

            # SELECT INTO statements
            elif "INTO" in stmt.upper() and "SELECT" in stmt.upper():
                # Parse SELECT ... INTO variable FROM ...
                parts = stmt.split("INTO")
                if len(parts) == 2:
                    select_part = parts[0].strip()
                    into_and_rest = parts[1].strip()
                    into_parts = into_and_rest.split("FROM", 1)
                    if len(into_parts) == 2:
                        var_name = into_parts[0].strip()
                        from_part = "FROM" + into_parts[1]
                        full_query = f"{select_part} {from_part}"
                        steps.append(
                            ActionStep(
                                type="query",
                                sql=full_query,
                                variable_name=var_name,
                            )
                        )

            # PERFORM statements
            elif stmt.upper().startswith("PERFORM"):
                self.confidence *= 0.9
                self.warnings.append(f"Unknown operation: {stmt}")
                # Skip unknown operations

            # IF statements (simplified)
            elif stmt.upper().startswith("IF"):
                # Basic IF parsing - extract condition between IF and THEN
                if "THEN" in stmt.upper():
                    condition_part = stmt[2:].upper().split("THEN")[0].strip()
                    # Remove variable prefixes for simplicity
                    condition = condition_part.replace("V_", "").replace("P_", "")
                    steps.append(
                        ActionStep(
                            type="if", condition=condition.lower(), then_steps=[], else_steps=[]
                        )
                    )

            # UPDATE statements
            elif stmt.upper().startswith("UPDATE"):
                steps.append(ActionStep(type="query", sql=stmt))

            # INSERT statements
            elif stmt.upper().startswith("INSERT"):
                steps.append(ActionStep(type="query", sql=stmt))

            # DELETE statements
            elif stmt.upper().startswith("DELETE"):
                steps.append(ActionStep(type="query", sql=stmt))

            # Unknown statements
            elif stmt:
                self.confidence *= 0.95
                self.warnings.append(f"Unknown statement: {stmt[:50]}...")

        return steps

    def _map_statements(self, plpgsql_ast: Any) -> list[ActionStep]:
        """Map PL/pgSQL statements to SpecQL steps"""
        steps = []

        if not plpgsql_ast:
            return steps

        # Extract statements from function body
        for item in plpgsql_ast:
            if hasattr(item, "PLpgSQL_function"):
                func = item.PLpgSQL_function

                # Process DECLARE block
                if hasattr(func, "decls") and func.decls:
                    for decl in func.decls:
                        declare_step = self._map_declare(decl)
                        if declare_step:
                            steps.append(declare_step)

                # Process body statements
                if hasattr(func, "body") and func.body:
                    for stmt in func.body:
                        stmt_steps = self._map_statement(stmt)
                        steps.extend(stmt_steps)

        return steps

    def _map_declare(self, decl: Any) -> ActionStep | None:
        """Map DECLARE statement to declare step"""
        if hasattr(decl, "PLpgSQL_var"):
            var = decl.PLpgSQL_var

            var_name = var.refname
            var_type = self._extract_type(var.datatype)
            default_value = self._extract_default(var.default_val)

            # Track variable
            self.variables[var_name] = var_type

            return ActionStep(
                type="declare",
                variable_name=var_name,
                variable_type=var_type,
                default_value=default_value,
            )

        return None

    def _map_statement(self, stmt: Any) -> list[ActionStep]:
        """Map a single PL/pgSQL statement to SpecQL steps"""
        steps = []

        # Assignment
        if hasattr(stmt, "PLpgSQL_stmt_assign"):
            steps.append(self._map_assign(stmt.PLpgSQL_stmt_assign))

        # EXECUTE (SQL query)
        elif hasattr(stmt, "PLpgSQL_stmt_execsql"):
            steps.append(self._map_execsql(stmt.PLpgSQL_stmt_execsql))

        # IF statement
        elif hasattr(stmt, "PLpgSQL_stmt_if"):
            steps.append(self._map_if(stmt.PLpgSQL_stmt_if))

        # RETURN
        elif hasattr(stmt, "PLpgSQL_stmt_return"):
            steps.append(self._map_return(stmt.PLpgSQL_stmt_return))

        # RETURN QUERY
        elif hasattr(stmt, "PLpgSQL_stmt_return_query"):
            steps.append(self._map_return_query(stmt.PLpgSQL_stmt_return_query))

        # FOR loop
        elif hasattr(stmt, "PLpgSQL_stmt_fors"):
            steps.append(self._map_for_query(stmt.PLpgSQL_stmt_fors))

        # WHILE loop
        elif hasattr(stmt, "PLpgSQL_stmt_while"):
            steps.append(self._map_while(stmt.PLpgSQL_stmt_while))

        # Unknown statement type
        else:
            self.warnings.append(f"Unknown statement type: {stmt}")
            self.confidence *= 0.95

        return steps

    def _map_assign(self, assign: Any) -> ActionStep:
        """Map assignment to assign step"""
        var_name = self._extract_var_name(assign.varno)
        expression = self._extract_expression(assign.expr)

        return ActionStep(type="assign", variable_name=var_name, expression=expression)

    def _map_execsql(self, execsql: Any) -> ActionStep:
        """Map EXECUTE SQL to query step"""
        sql = self._extract_sql_string(execsql.sqlstmt)

        # Detect if this is a CTE
        if "WITH" in sql.upper() and "AS (" in sql.upper():
            return self._map_cte(sql)

        # Detect if INTO variable
        if hasattr(execsql, "into") and execsql.into:
            into_var = self._extract_into_variable(execsql.into)
            return ActionStep(type="query", sql=sql, store_result=into_var)

        # Regular query
        return ActionStep(type="query", sql=sql)

    def _map_cte(self, sql: str) -> ActionStep:
        """Map CTE to cte step"""
        # Extract CTE name and query (simplified)
        # TODO: More robust CTE parsing
        import re

        match = re.search(r"WITH\s+(\w+)\s+AS\s*\((.*?)\)", sql, re.IGNORECASE | re.DOTALL)

        if match:
            cte_name = match.group(1)
            cte_query = match.group(2).strip()

            return ActionStep(type="cte", cte_name=cte_name, cte_query=cte_query)

        # Fallback to query
        self.warnings.append("Failed to parse CTE, treating as query")
        return ActionStep(type="query", expression=sql)

    def _map_if(self, if_stmt: Any) -> ActionStep:
        """Map IF statement to if step"""
        condition = self._extract_expression(if_stmt.cond)
        then_steps = [
            self._map_statement(s)[0] for s in if_stmt.then_body if self._map_statement(s)
        ]

        else_steps = []
        if hasattr(if_stmt, "else_body") and if_stmt.else_body:
            else_steps = [
                self._map_statement(s)[0] for s in if_stmt.else_body if self._map_statement(s)
            ]

        return ActionStep(
            type="if", condition=condition, then_steps=then_steps, else_steps=else_steps
        )

    def _map_return(self, return_stmt: Any) -> ActionStep:
        """Map RETURN to return step"""
        expression = self._extract_expression(return_stmt.expr)

        return ActionStep(type="return", return_value=expression)

    def _map_return_query(self, return_query: Any) -> ActionStep:
        """Map RETURN QUERY to return_table step"""
        sql = self._extract_sql_string(return_query.query)

        return ActionStep(type="return_table", return_table_query=sql)

    def _map_for_query(self, for_stmt: Any) -> ActionStep:
        """Map FOR ... LOOP to for_query step"""
        loop_var = self._extract_var_name(for_stmt.var)
        query = self._extract_sql_string(for_stmt.query)
        body_steps = [self._map_statement(s)[0] for s in for_stmt.body if self._map_statement(s)]

        return ActionStep(
            type="for_query",
            for_query_alias=loop_var,
            for_query_sql=query,
            for_query_body=body_steps,
        )

    def _map_while(self, while_stmt: Any) -> ActionStep:
        """Map WHILE to while step"""
        condition = self._extract_expression(while_stmt.cond)
        body_steps = [self._map_statement(s)[0] for s in while_stmt.body if self._map_statement(s)]

        return ActionStep(type="while", while_condition=condition, loop_body=body_steps)

    # Helper methods
    def _extract_var_name(self, varno: int) -> str:
        """Extract variable name from variable number"""
        # In pglast, variables are tracked by number
        # Need to look up in symbol table
        # Simplified: use v_varno format
        return f"v_{varno}"

    def _extract_expression(self, expr: Any) -> str:
        """Extract expression as string"""
        # Simplified: convert AST to SQL string
        # TODO: More robust expression extraction
        return str(expr)

    def _extract_sql_string(self, sql_node: Any) -> str:
        """Extract SQL string from node"""
        return str(sql_node)

    def _extract_type(self, datatype: Any) -> str:
        """Extract type from datatype node"""
        # Simplified type extraction
        return "text"  # TODO: Implement

    def _extract_default(self, default_val: Any) -> Any:
        """Extract default value"""
        if not default_val:
            return None
        return str(default_val)

    def _extract_into_variable(self, into: Any) -> str:
        """Extract INTO variable name"""
        if hasattr(into, "target") and into.target:
            return self._extract_var_name(into.target.varno)
        return "result"

    def _remove_cursor_statements(self, sql_text: str) -> str:
        """Remove cursor statements that have already been parsed"""
        import re

        # Remove OPEN statements
        sql_text = re.sub(r"OPEN\s+\w+\s*;", "", sql_text, flags=re.IGNORECASE)

        # Remove CLOSE statements
        sql_text = re.sub(r"CLOSE\s+\w+\s*;", "", sql_text, flags=re.IGNORECASE)

        # Remove LOOP blocks containing FETCH (simplified - remove entire LOOP...END LOOP)
        sql_text = re.sub(r"LOOP.*?END\s+LOOP\s*;", "", sql_text, flags=re.IGNORECASE | re.DOTALL)

        return sql_text.strip()

    def _strip_sql_comments(self, sql_text: str) -> str:
        """
        Strip single-line SQL comments (-- comments) from SQL text

        Note: Block comments (/* */) are more complex to handle correctly
        and are typically handled by the SQL parser itself
        """

        # Remove single-line comments: -- comment
        # Match -- followed by anything until end of line
        lines = sql_text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Find -- comment marker
            if "--" in line:
                # Keep everything before the --
                line = line.split("--")[0]

            # Keep non-empty lines
            if line.strip():
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)
