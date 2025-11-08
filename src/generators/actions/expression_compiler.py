"""
Expression Compiler

Compiles SpecQL expressions to safe SQL with injection protection.

Example SpecQL expressions:
    - "status = 'qualified'"
    - "email LIKE '%@company.com'"
    - "created_at > '2024-01-01'"

Generated safe SQL:
    - "v_status = 'qualified'"
    - "v_email LIKE '%@company.com'"
    - "v_created_at > '2024-01-01'"
"""

import re
from typing import List

from src.core.ast_models import EntityDefinition


class ExpressionCompiler:
    """Compiles SpecQL expressions to safe SQL"""

    # Allowed operators and functions for security
    SAFE_OPERATORS = {
        "=",
        "!=",
        "<",
        ">",
        "<=",
        ">=",
        "AND",
        "OR",
        "NOT",
        "IN",
        "LIKE",
        "ILIKE",
        "IS",
        "IS NOT",
        "+",
        "-",
        "*",
        "/",
    }

    SAFE_FUNCTIONS = {
        "UPPER",
        "LOWER",
        "TRIM",
        "LENGTH",
        "COALESCE",
        "NOW",
        "CURRENT_DATE",
        "CURRENT_TIME",
        "EXTRACT",
        "SUBSTRING",
        "POSITION",
        "CONCAT",
    }

    # SQL injection patterns to block
    DANGEROUS_PATTERNS = [
        r";\s*--",  # Semicolon followed by comment
        r";\s*/\*",  # Semicolon followed by block comment
        r"union\s+select",  # UNION SELECT
        r"exec\s*\(",  # EXEC function calls
        r"xp_\w+",  # Extended stored procedures
        r";\s*drop\s+",  # DROP statements
        r";\s*delete\s+from",  # DELETE statements
        r";\s*update\s+",  # UPDATE statements
        r";\s*insert\s+",  # INSERT statements
    ]

    def compile(self, expression: str, entity: EntityDefinition) -> str:
        """
        Compile expression with SQL injection protection

        Args:
            expression: SpecQL expression string
            entity: Entity for field validation

        Returns:
            Safe SQL expression

        Raises:
            SecurityError: If expression contains dangerous patterns
        """
        # Security check first
        self._validate_security(expression)

        # Parse and validate expression structure
        ast = self._parse_expression(expression)

        # Validate all components are safe
        self._validate_safety(ast, entity)

        # Convert to SQL
        return self._ast_to_sql(ast, entity)

    def _validate_security(self, expression: str) -> None:
        """
        Check for SQL injection patterns

        Raises:
            SecurityError: If dangerous patterns are found
        """
        expr_lower = expression.lower()

        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, expr_lower, re.IGNORECASE):
                raise SecurityError(f"Potentially dangerous SQL pattern detected: {pattern}")

        # Check for suspicious characters
        if any(char in expression for char in ["\\", "\x00", "\n", "\r"]):
            raise SecurityError("Expression contains suspicious characters")

    def _parse_expression(self, expression: str) -> dict:
        """
        Parse expression into AST-like structure

        This is a simplified parser for basic expressions.
        For complex expressions, consider using a proper SQL parser.
        """
        # Remove extra whitespace
        expression = expression.strip()

        # Handle parentheses
        if expression.startswith("(") and expression.endswith(")"):
            # Recursively parse inner expression
            inner = self._parse_expression(expression[1:-1])
            return {"type": "group", "inner": inner}

        # Handle function calls
        func_match = re.match(r"^(\w+)\s*\((.*)\)$", expression)
        if func_match:
            func_name = func_match.group(1).upper()
            args_str = func_match.group(2).strip()

            if func_name in self.SAFE_FUNCTIONS:
                args = self._parse_function_args(args_str)
                return {"type": "function", "name": func_name, "args": args}
            else:
                raise SecurityError(f"Function '{func_name}' not allowed")

        # Handle binary operations
        for op in [
            "AND",
            "OR",
            "NOT",
            "=",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "LIKE",
            "ILIKE",
            "IN",
            "IS",
        ]:
            if f" {op} " in expression.upper():
                parts = re.split(rf"\s{re.escape(op)}\s", expression, flags=re.IGNORECASE)
                if len(parts) == 2:
                    return {
                        "type": "binary",
                        "operator": op.upper(),
                        "left": self._parse_expression(parts[0]),
                        "right": self._parse_expression(parts[1]),
                    }

        # Handle unary operations
        if expression.upper().startswith("NOT "):
            return {
                "type": "unary",
                "operator": "NOT",
                "operand": self._parse_expression(expression[4:]),
            }

        # Handle literals and identifiers
        if self._is_string_literal(expression):
            return {"type": "literal", "value": expression}
        elif self._is_number_literal(expression):
            return {"type": "literal", "value": expression}
        elif self._is_boolean_literal(expression):
            return {"type": "literal", "value": expression}
        else:
            # Assume it's an identifier/field reference
            return {"type": "identifier", "name": expression}

    def _parse_function_args(self, args_str: str) -> List[dict]:
        """Parse function arguments"""
        if not args_str:
            return []

        # Simple comma splitting (doesn't handle nested functions well)
        args = []
        for arg in args_str.split(","):
            args.append(self._parse_expression(arg.strip()))

        return args

    def _is_string_literal(self, expr: str) -> bool:
        """Check if expression is a string literal"""
        return (expr.startswith("'") and expr.endswith("'")) or (
            expr.startswith('"') and expr.endswith('"')
        )

    def _is_number_literal(self, expr: str) -> bool:
        """Check if expression is a number literal"""
        try:
            float(expr)
            return True
        except ValueError:
            return False

    def _is_boolean_literal(self, expr: str) -> bool:
        """Check if expression is a boolean literal"""
        return expr.upper() in ["TRUE", "FALSE", "NULL"]

    def _validate_safety(self, ast: dict, entity: EntityDefinition) -> None:
        """
        Validate that AST contains only safe operations

        Raises:
            SecurityError: If unsafe operations are found
        """
        if ast["type"] == "binary":
            if ast["operator"] not in self.SAFE_OPERATORS:
                raise SecurityError(f"Operator '{ast['operator']}' not allowed")
            self._validate_safety(ast["left"], entity)
            self._validate_safety(ast["right"], entity)

        elif ast["type"] == "unary":
            if ast["operator"] not in self.SAFE_OPERATORS:
                raise SecurityError(f"Operator '{ast['operator']}' not allowed")
            self._validate_safety(ast["operand"], entity)

        elif ast["type"] == "function":
            if ast["name"] not in self.SAFE_FUNCTIONS:
                raise SecurityError(f"Function '{ast['name']}' not allowed")
            for arg in ast["args"]:
                self._validate_safety(arg, entity)

        elif ast["type"] == "identifier":
            # Check if identifier is a valid field name
            field_name = ast["name"]
            if field_name not in entity.fields and not self._is_valid_variable(field_name):
                raise SecurityError(f"Unknown field or variable: '{field_name}'")

        elif ast["type"] == "group":
            self._validate_safety(ast["inner"], entity)

        # Literals are always safe

    def _is_valid_variable(self, name: str) -> bool:
        """
        Check if name is a valid variable reference

        Allows things like 'v_field_name', 'auth_user_id', etc.
        """
        # Allow variables starting with 'v_' (generated variables)
        # Allow auth context variables
        # Allow some built-in variables
        return name.startswith("v_") or name in ["auth_user_id", "auth_tenant_id", "now()"]

    def _ast_to_sql(self, ast: dict, entity: EntityDefinition) -> str:
        """Convert AST back to SQL expression"""
        if ast["type"] == "binary":
            left = self._ast_to_sql(ast["left"], entity)
            right = self._ast_to_sql(ast["right"], entity)
            return f"{left} {ast['operator']} {right}"

        elif ast["type"] == "unary":
            operand = self._ast_to_sql(ast["operand"], entity)
            return f"{ast['operator']} {operand}"

        elif ast["type"] == "function":
            args = [self._ast_to_sql(arg, entity) for arg in ast["args"]]
            return f"{ast['name']}({', '.join(args)})"

        elif ast["type"] == "identifier":
            # Convert field names to variable names
            field_name = ast["name"]
            if field_name in entity.fields:
                return f"v_{field_name}"
            else:
                return field_name  # Variable or built-in

        elif ast["type"] == "literal":
            return ast["value"]

        elif ast["type"] == "group":
            inner = self._ast_to_sql(ast["inner"], entity)
            return f"({inner})"

        else:
            raise ValueError(f"Unknown AST node type: {ast['type']}")


class SecurityError(Exception):
    """Raised when SQL injection or unsafe operations are detected"""

    pass
