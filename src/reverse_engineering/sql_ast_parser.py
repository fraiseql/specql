"""
SQL AST Parser using pglast

Converts PostgreSQL SQL to AST for analysis
"""

import pglast
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ParsedFunction:
    """Parsed SQL function"""
    function_name: str
    schema: str
    parameters: List[Dict[str, str]]
    return_type: str
    body: Optional[str]  # SQL body text
    language: str = "plpgsql"


class SQLASTParser:
    """Parse SQL functions using pglast"""

    def parse_function(self, sql: str) -> ParsedFunction:
        """
        Parse CREATE FUNCTION statement

        Args:
            sql: SQL CREATE FUNCTION statement

        Returns:
            ParsedFunction with AST
        """
        try:
            # Parse SQL to AST
            ast = pglast.parse_sql(sql)

            # Extract function definition
            stmt = ast[0].stmt

            if not isinstance(stmt, pglast.ast.CreateFunctionStmt):
                raise ValueError("Not a CREATE FUNCTION statement")

            func_stmt = stmt

            # Extract function name
            func_name_parts = [n.sval for n in func_stmt.funcname]
            schema = func_name_parts[0] if len(func_name_parts) > 1 else "public"
            function_name = func_name_parts[-1]

            # Extract parameters
            parameters = self._parse_parameters(func_stmt.parameters)

            # Extract return type
            return_type = self._parse_return_type(func_stmt.returnType)

            # Extract body
            body = self._parse_body(func_stmt)

            return ParsedFunction(
                function_name=function_name,
                schema=schema,
                parameters=parameters,
                return_type=return_type,
                body=body,
                language="plpgsql"
            )

        except Exception as e:
            raise ValueError(f"Failed to parse SQL: {e}")

    def _parse_parameters(self, params) -> List[Dict[str, str]]:
        """Extract function parameters"""
        parameters = []

        if not params:
            return parameters

        for param in params:
            if isinstance(param, pglast.ast.FunctionParameter):
                param_name = param.name if param.name else f"arg{len(parameters)}"
                param_type = self._type_name_to_string(param.argType)

                # Remove 'p_' prefix if present (common convention)
                if param_name.startswith('p_'):
                    param_name = param_name[2:]

                parameters.append({
                    "name": param_name,
                    "type": param_type
                })

        return parameters

    def _parse_return_type(self, return_type_node) -> str:
        """Extract return type"""
        if isinstance(return_type_node, pglast.ast.TypeName):
            return self._type_name_to_string(return_type_node)
        return "unknown"

    def _type_name_to_string(self, type_node) -> str:
        """Convert type node to string"""
        if not type_node:
            return "void"

        if isinstance(type_node, pglast.ast.TypeName):
            names = [n.sval for n in type_node.names]
            type_name = names[-1].lower()

            # Map PostgreSQL types to SpecQL types
            type_map = {
                "integer": "integer",
                "int": "integer",
                "bigint": "bigint",
                "numeric": "numeric",
                "decimal": "numeric",
                "text": "text",
                "varchar": "text",
                "boolean": "boolean",
                "bool": "boolean",
                "uuid": "uuid",
                "timestamptz": "timestamp",
                "timestamp": "timestamp",
                "jsonb": "json",
                "json": "json"
            }

            return type_map.get(type_name, type_name)

        return "unknown"

    def _parse_body(self, func_stmt) -> Optional[str]:
        """Extract function body"""
        # Function body is in options
        for option in func_stmt.options:
            if isinstance(option, pglast.ast.DefElem) and option.defname == 'as':
                # Body is in arg as a tuple of strings
                if isinstance(option.arg, tuple) and len(option.arg) > 0:
                    body_string = option.arg[0].sval
                    # Clean up the body - remove $$ delimiters and extra whitespace
                    body_string = body_string.strip()
                    # For now, return the raw body - we'll parse it later
                    return body_string

        return None