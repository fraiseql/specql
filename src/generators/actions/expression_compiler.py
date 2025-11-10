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

from src.core.ast_models import EntityDefinition
from src.core.scalar_types import get_scalar_type


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
        "MATCHES",
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
        "EXISTS",
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
        Parse expression into AST-like structure with support for advanced expressions

        Supports:
        - Nested function calls: UPPER(TRIM(email))
        - Complex expressions: (a AND b) OR (c AND d)
        - Subqueries: field IN (SELECT ...)
        """
        # Remove extra whitespace
        expression = expression.strip()

        # Handle parentheses for grouping FIRST (before binary operations)
        if expression.startswith("(") and expression.endswith(")"):
            # Check if these are matching outer parentheses
            # We need to verify that the opening '(' matches the closing ')'
            # by ensuring the inner expression is balanced
            paren_depth = 0
            in_string = False
            string_char = None
            matches_at_end = True

            for i, char in enumerate(expression[1:-1], start=1):
                if in_string:
                    if char == string_char:
                        in_string = False
                        string_char = None
                elif char in ("'", '"'):
                    in_string = True
                    string_char = char
                elif char == "(":
                    paren_depth += 1
                elif char == ")":
                    paren_depth -= 1
                    if paren_depth < 0:
                        # The opening '(' and closing ')' don't match
                        # Example: "(status = 'lead') AND (score > 50)"
                        # The '(' belongs to the first group, not the outer expression
                        matches_at_end = False
                        break

            # Only treat as grouping if outer parens actually match
            if matches_at_end and paren_depth == 0:
                inner_expr = expression[1:-1].strip()

                # Handle empty parentheses
                if not inner_expr:
                    return {"type": "literal", "value": "()"}

                # Check if inner expression starts with SELECT (subquery)
                if inner_expr.upper().startswith("SELECT"):
                    return {"type": "subquery", "query": expression}

                # Check if this looks like a function call
                paren_pos = inner_expr.find("(")
                if paren_pos > 0 and inner_expr.endswith(")"):
                    potential_func = inner_expr[:paren_pos].strip()
                    if potential_func.upper() in self.SAFE_FUNCTIONS:
                        # This is a function call inside parentheses
                        func_name = potential_func.upper()
                        args_str = inner_expr[paren_pos + 1 : -1].strip()
                        args = self._parse_function_args(args_str)
                        return {"type": "function", "name": func_name, "args": args}

                # Just parentheses for grouping
                inner = self._parse_expression(inner_expr)
                return {"type": "group", "inner": inner}

        # Handle function calls (without outer parentheses)
        # Use proper parentheses matching instead of greedy regex
        func_start_match = re.match(r"^(\w+)\s*\(", expression)
        if func_start_match:
            func_name = func_start_match.group(1).upper()
            # Find the matching closing parenthesis
            start_pos = func_start_match.end() - 1  # Position of opening '('
            closing_pos = self._find_matching_paren(expression, start_pos)

            if closing_pos == len(expression) - 1:
                # This is a complete function call
                args_str = expression[start_pos + 1 : closing_pos].strip()

                if func_name in self.SAFE_FUNCTIONS:
                    args = self._parse_function_args(args_str)
                    return {"type": "function", "name": func_name, "args": args}
                elif func_name == "SELECT":
                    # Subquery
                    return {"type": "subquery", "query": expression}
                else:
                    raise SecurityError(f"Function '{func_name}' not allowed")

        # Handle binary operations with proper precedence
        # Process operators in order of precedence (lowest to highest)
        operators_by_precedence = [
            ("OR",),  # Lowest precedence
            ("AND",),
            ("=", "!=", "<", ">", "<=", ">=", "LIKE", "ILIKE", "IN", "IS", "IS NOT", "MATCHES"),
        ]

        for op_group in operators_by_precedence:
            for op in op_group:
                # Find operator with proper word boundaries, but respect parentheses
                pattern = rf"\s{re.escape(op)}\s"
                matches = list(re.finditer(pattern, expression, re.IGNORECASE))

                # Find the rightmost operator at the top level (not inside parentheses)
                for match in reversed(matches):
                    pos = match.start()
                    # Check if this operator is at the top level (not inside parentheses)
                    if self._is_top_level_operator(expression, pos, len(match.group())):
                        left_part = expression[:pos].strip()
                        right_part = expression[pos + len(match.group()) :].strip()

                        return {
                            "type": "binary",
                            "operator": op.upper(),
                            "left": self._parse_expression(left_part),
                            "right": self._parse_expression(right_part),
                        }

        # Handle unary NOT
        if expression.upper().startswith("NOT "):
            return {
                "type": "unary",
                "operator": "NOT",
                "operand": self._parse_expression(expression[4:]),
            }

        # Check for subqueries (SELECT statements)
        if expression.upper().startswith("SELECT"):
            return {"type": "subquery", "query": f"({expression})"}

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

    def _parse_function_args(self, args_str: str) -> list[dict]:
        """Parse function arguments with support for nested functions and subqueries"""
        if not args_str:
            return []

        # Special handling for EXISTS - it takes a single subquery argument
        if args_str.strip().startswith("(") and args_str.strip().endswith(")"):
            inner = args_str.strip()[1:-1].strip()
            if inner.upper().startswith("SELECT"):
                return [{"type": "subquery", "query": f"({inner})"}]

        args = []
        current_arg = ""
        paren_depth = 0
        in_string = False
        string_char = None

        i = 0
        while i < len(args_str):
            char = args_str[i]

            if in_string:
                if char == string_char:
                    in_string = False
                    string_char = None
                current_arg += char
            elif char in ("'", '"'):
                in_string = True
                string_char = char
                current_arg += char
            elif char == "(":
                paren_depth += 1
                current_arg += char
            elif char == ")":
                paren_depth -= 1
                current_arg += char
            elif char == "," and paren_depth == 0:
                # End of argument
                if current_arg.strip():
                    args.append(self._parse_expression(current_arg.strip()))
                current_arg = ""
            else:
                current_arg += char

            i += 1

        # Add the last argument
        if current_arg.strip():
            args.append(self._parse_expression(current_arg.strip()))

        return args

    def _find_matching_paren(self, expression: str, start_pos: int) -> int:
        """
        Find the matching closing parenthesis for the opening paren at start_pos

        Args:
            expression: The expression string
            start_pos: Position of the opening parenthesis

        Returns:
            Position of the matching closing parenthesis, or -1 if not found
        """
        if start_pos >= len(expression) or expression[start_pos] != "(":
            return -1

        depth = 0
        in_string = False
        string_char = None

        for i in range(start_pos, len(expression)):
            char = expression[i]

            if in_string:
                if char == string_char:
                    in_string = False
                    string_char = None
            elif char in ("'", '"'):
                in_string = True
                string_char = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return i

        return -1  # No matching paren found

    def _is_top_level_operator(self, expression: str, op_start: int, op_length: int) -> bool:
        """Check if operator at given position is at the top level (not inside parentheses or strings)"""
        paren_depth = 0
        in_string = False
        string_char = None

        # Check parentheses and string literal balance up to the start of the operator
        for i in range(op_start):
            char = expression[i]

            if in_string:
                if char == string_char:
                    in_string = False
                    string_char = None
            elif char in ("'", '"'):
                in_string = True
                string_char = char
            elif char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
                if paren_depth < 0:
                    return False  # Unbalanced parentheses

        # Operator must be at top level (paren_depth == 0) AND not inside a string
        return paren_depth == 0 and not in_string

    def _are_parentheses_balanced(self, expr: str) -> bool:
        """Check if parentheses are balanced in the expression"""
        paren_depth = 0
        in_string = False
        string_char = None

        for char in expr:
            if in_string:
                if char == string_char:
                    in_string = False
                    string_char = None
            elif char in ("'", '"'):
                in_string = True
                string_char = char
            elif char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
                if paren_depth < 0:
                    return False

        return paren_depth == 0

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

        elif ast["type"] == "subquery":
            # Basic subquery validation - only allow SELECT
            query = ast["query"].strip().upper()
            if not (query.startswith("(") and "SELECT" in query):
                raise SecurityError("Subqueries must contain SELECT statements")
            # Note: We skip detailed field validation for subqueries since they
            # can reference columns from their own tables, not just entity fields

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

            # Handle special operators
            if ast["operator"] == "MATCHES":
                # Convert MATCHES to PostgreSQL regex matching
                if self._is_rich_type_pattern(right):
                    pattern = self._get_rich_type_pattern(right)
                    return f"{left} ~ '{pattern}'"
                else:
                    # For non-rich-type patterns, treat as literal regex
                    return f"{left} ~ {right}"
            else:
                return f"{left} {ast['operator']} {right}"

        elif ast["type"] == "unary":
            operand = self._ast_to_sql(ast["operand"], entity)
            return f"{ast['operator']} {operand}"

        elif ast["type"] == "function":
            args = [self._ast_to_sql(arg, entity) for arg in ast["args"]]
            return f"{ast['name']}({', '.join(args)})"

        elif ast["type"] == "subquery":
            # Return the subquery as-is (already validated)
            return ast["query"]

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

    def _is_rich_type_pattern(self, pattern_expr: str) -> bool:
        """Check if the pattern expression refers to a rich type"""
        # Remove quotes if present
        pattern_name = pattern_expr.strip("'\"")
        return get_scalar_type(pattern_name) is not None

    def _get_rich_type_pattern(self, pattern_expr: str) -> str:
        """Get the regex pattern for a rich type"""
        pattern_name = pattern_expr.strip("'\"")
        scalar_def = get_scalar_type(pattern_name)
        if scalar_def and scalar_def.validation_pattern:
            return scalar_def.validation_pattern
        raise ValueError(f"No validation pattern found for rich type: {pattern_name}")


class SecurityError(Exception):
    """Raised when SQL injection or unsafe operations are detected"""

    pass
