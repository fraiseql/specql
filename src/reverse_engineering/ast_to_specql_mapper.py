"""
Map SQL AST to SpecQL primitives

Algorithmic mapping without AI
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from src.core.ast_models import ActionStep


@dataclass
class ConversionResult:
    """Result of SQL → SpecQL conversion"""
    function_name: str
    schema: str
    parameters: List[Dict[str, str]]
    return_type: str
    steps: List[ActionStep]
    confidence: float
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ASTToSpecQLMapper:
    """Map PostgreSQL AST to SpecQL primitives"""

    def __init__(self):
        self.confidence = 1.0
        self.warnings = []
        self.variables = {}  # Track declared variables

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
            warnings=self.warnings
        )

    def _parse_body_text(self, body_text: str) -> List[ActionStep]:
        """Parse function body using simple text analysis (algorithmic approach)"""
        steps = []

        # Clean up the body text
        body_text = body_text.strip()
        if body_text.startswith('DECLARE'):
            # Split into DECLARE and BEGIN blocks
            parts = body_text.split('BEGIN', 1)
            if len(parts) == 2:
                declare_block = parts[0].strip()
                begin_block = 'BEGIN' + parts[1]

                # Parse DECLARE block
                steps.extend(self._parse_declare_block(declare_block))

                # Parse BEGIN block
                steps.extend(self._parse_begin_block(begin_block))
        elif body_text.startswith('BEGIN'):
            # No DECLARE block
            steps.extend(self._parse_begin_block(body_text))
        else:
            # Fallback: treat as BEGIN block
            steps.extend(self._parse_begin_block(body_text))

        return steps

    def _parse_declare_block(self, declare_text: str) -> List[ActionStep]:
        """Parse DECLARE block for variable declarations"""
        steps = []

        # Simple parsing: look for variable declarations
        # Pattern: variable_name type [= default]
        import re
        # Match patterns like: v_total NUMERIC := 0
        # Skip the DECLARE keyword
        declare_content = declare_text[7:].strip()  # Remove 'DECLARE'
        var_pattern = r'(\w+)\s+(\w+)(?:\s*:=\s*([^;]+))?;?'
        matches = re.findall(var_pattern, declare_content)

        for match in matches:
            var_name, var_type, default_val = match
            var_type_lower = var_type.lower()

            # Map SQL types to SpecQL types
            type_map = {
                "integer": "integer",
                "numeric": "numeric",
                "text": "text",
                "boolean": "boolean",
                "uuid": "uuid",
            }
            specql_type = type_map.get(var_type_lower, var_type_lower)

            # Reduce confidence for unknown types
            if specql_type == var_type_lower and var_type_lower not in type_map.values():
                self.confidence *= 0.95
                self.warnings.append(f"Unknown variable type: {var_type}")

            steps.append(ActionStep(
                type="declare",
                variable_name=var_name,
                variable_type=specql_type,
                default_value=default_val if default_val else None
            ))

        return steps

    def _parse_begin_block(self, begin_text: str) -> List[ActionStep]:
        """Parse BEGIN block for executable statements"""
        steps = []

        # Remove BEGIN and END
        if begin_text.upper().startswith('BEGIN'):
            begin_text = begin_text[5:]
        if begin_text.upper().endswith('END'):
            begin_text = begin_text[:-3]

        begin_text = begin_text.strip()

        # Split by semicolons to get individual statements
        statements = [s.strip() for s in begin_text.split(';') if s.strip()]

        for stmt in statements:
            stmt = stmt.strip()

            # RETURN QUERY statements
            if stmt.upper().startswith('RETURN QUERY'):
                query = stmt[12:].strip()  # Remove 'RETURN QUERY'
                steps.append(ActionStep(type="return_table", return_table_query=query))

            # RETURN statements
            elif stmt.upper().startswith('RETURN'):
                expr = stmt[6:].strip()
                steps.append(ActionStep(type="return", return_value=expr))

            # SELECT INTO statements
            elif 'INTO' in stmt.upper() and 'SELECT' in stmt.upper():
                # Parse SELECT ... INTO variable FROM ...
                parts = stmt.split('INTO')
                if len(parts) == 2:
                    select_part = parts[0].strip()
                    into_and_rest = parts[1].strip()
                    into_parts = into_and_rest.split('FROM', 1)
                    if len(into_parts) == 2:
                        var_name = into_parts[0].strip()
                        from_part = 'FROM' + into_parts[1]
                        full_query = f"{select_part} {from_part}"
                        steps.append(ActionStep(
                            type="query",
                            sql=full_query,
                            store_result=var_name
                        ))

            # PERFORM statements (unknown operations)
            elif stmt.upper().startswith('PERFORM'):
                self.confidence *= 0.9
                self.warnings.append(f"Unknown operation: {stmt}")
                # Skip unknown operations

            # IF statements (simplified)
            elif stmt.upper().startswith('IF'):
                # Basic IF parsing - extract condition between IF and THEN
                if 'THEN' in stmt.upper():
                    condition_part = stmt[2:].upper().split('THEN')[0].strip()
                    # Remove variable prefixes for simplicity
                    condition = condition_part.replace('V_', '').replace('P_', '')
                    steps.append(ActionStep(
                        type="if",
                        condition=condition.lower(),
                        then_steps=[],
                        else_steps=[]
                    ))

            # UPDATE statements
            elif stmt.upper().startswith('UPDATE'):
                steps.append(ActionStep(type="query", sql=stmt))

            # INSERT statements
            elif stmt.upper().startswith('INSERT'):
                steps.append(ActionStep(type="query", sql=stmt))

            # DELETE statements
            elif stmt.upper().startswith('DELETE'):
                steps.append(ActionStep(type="query", sql=stmt))

            # Unknown statements
            elif stmt:
                self.confidence *= 0.95
                self.warnings.append(f"Unknown statement: {stmt[:50]}...")

        return steps

    def _map_statements(self, plpgsql_ast: Any) -> List[ActionStep]:
        """Map PL/pgSQL statements to SpecQL steps"""
        steps = []

        if not plpgsql_ast:
            return steps

        # Extract statements from function body
        for item in plpgsql_ast:
            if hasattr(item, 'PLpgSQL_function'):
                func = item.PLpgSQL_function

                # Process DECLARE block
                if hasattr(func, 'decls') and func.decls:
                    for decl in func.decls:
                        declare_step = self._map_declare(decl)
                        if declare_step:
                            steps.append(declare_step)

                # Process body statements
                if hasattr(func, 'body') and func.body:
                    for stmt in func.body:
                        stmt_steps = self._map_statement(stmt)
                        steps.extend(stmt_steps)

        return steps

    def _map_declare(self, decl: Any) -> Optional[ActionStep]:
        """Map DECLARE statement to declare step"""
        if hasattr(decl, 'PLpgSQL_var'):
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
                default_value=default_value
            )

        return None

    def _map_statement(self, stmt: Any) -> List[ActionStep]:
        """Map a single PL/pgSQL statement to SpecQL steps"""
        steps = []

        # Assignment
        if hasattr(stmt, 'PLpgSQL_stmt_assign'):
            steps.append(self._map_assign(stmt.PLpgSQL_stmt_assign))

        # EXECUTE (SQL query)
        elif hasattr(stmt, 'PLpgSQL_stmt_execsql'):
            steps.append(self._map_execsql(stmt.PLpgSQL_stmt_execsql))

        # IF statement
        elif hasattr(stmt, 'PLpgSQL_stmt_if'):
            steps.append(self._map_if(stmt.PLpgSQL_stmt_if))

        # RETURN
        elif hasattr(stmt, 'PLpgSQL_stmt_return'):
            steps.append(self._map_return(stmt.PLpgSQL_stmt_return))

        # RETURN QUERY
        elif hasattr(stmt, 'PLpgSQL_stmt_return_query'):
            steps.append(self._map_return_query(stmt.PLpgSQL_stmt_return_query))

        # FOR loop
        elif hasattr(stmt, 'PLpgSQL_stmt_fors'):
            steps.append(self._map_for_query(stmt.PLpgSQL_stmt_fors))

        # WHILE loop
        elif hasattr(stmt, 'PLpgSQL_stmt_while'):
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

        return ActionStep(
            type="assign",
            variable_name=var_name,
            expression=expression
        )

    def _map_execsql(self, execsql: Any) -> ActionStep:
        """Map EXECUTE SQL to query step"""
        sql = self._extract_sql_string(execsql.sqlstmt)

        # Detect if this is a CTE
        if "WITH" in sql.upper() and "AS (" in sql.upper():
            return self._map_cte(sql)

        # Detect if INTO variable
        if hasattr(execsql, 'into') and execsql.into:
            into_var = self._extract_into_variable(execsql.into)
            return ActionStep(
                type="query",
                sql=sql,
                store_result=into_var
            )

        # Regular query
        return ActionStep(
            type="query",
            sql=sql
        )

    def _map_cte(self, sql: str) -> ActionStep:
        """Map CTE to cte step"""
        # Extract CTE name and query (simplified)
        # TODO: More robust CTE parsing
        import re
        match = re.search(r'WITH\s+(\w+)\s+AS\s*\((.*?)\)', sql, re.IGNORECASE | re.DOTALL)

        if match:
            cte_name = match.group(1)
            cte_query = match.group(2).strip()

            return ActionStep(
                type="cte",
                cte_name=cte_name,
                cte_query=cte_query
            )

        # Fallback to query
        self.warnings.append("Failed to parse CTE, treating as query")
        return ActionStep(type="query", expression=sql)

    def _map_if(self, if_stmt: Any) -> ActionStep:
        """Map IF statement to if step"""
        condition = self._extract_expression(if_stmt.cond)
        then_steps = [self._map_statement(s)[0] for s in if_stmt.then_body if self._map_statement(s)]

        else_steps = []
        if hasattr(if_stmt, 'else_body') and if_stmt.else_body:
            else_steps = [self._map_statement(s)[0] for s in if_stmt.else_body if self._map_statement(s)]

        return ActionStep(
            type="if",
            condition=condition,
            then_steps=then_steps,
            else_steps=else_steps
        )

    def _map_return(self, return_stmt: Any) -> ActionStep:
        """Map RETURN to return step"""
        expression = self._extract_expression(return_stmt.expr)

        return ActionStep(
            type="return",
            return_value=expression
        )

    def _map_return_query(self, return_query: Any) -> ActionStep:
        """Map RETURN QUERY to return_table step"""
        sql = self._extract_sql_string(return_query.query)

        return ActionStep(
            type="return_table",
            return_table_query=sql
        )

    def _map_for_query(self, for_stmt: Any) -> ActionStep:
        """Map FOR ... LOOP to for_query step"""
        loop_var = self._extract_var_name(for_stmt.var)
        query = self._extract_sql_string(for_stmt.query)
        body_steps = [self._map_statement(s)[0] for s in for_stmt.body if self._map_statement(s)]

        return ActionStep(
            type="for_query",
            for_query_alias=loop_var,
            for_query_sql=query,
            for_query_body=body_steps
        )

    def _map_while(self, while_stmt: Any) -> ActionStep:
        """Map WHILE to while step"""
        condition = self._extract_expression(while_stmt.cond)
        body_steps = [self._map_statement(s)[0] for s in while_stmt.body if self._map_statement(s)]

        return ActionStep(
            type="while",
            while_condition=condition,
            loop_body=body_steps
        )

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
        if hasattr(into, 'target') and into.target:
            return self._extract_var_name(into.target.varno)
        return "result"