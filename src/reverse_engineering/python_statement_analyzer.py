import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PythonStatement:
    """Analyzed Python statement"""
    statement_type: str  # 'assign', 'if', 'return', 'call', 'for', 'raise'
    raw_code: str
    ast_node: ast.stmt
    metadata: Dict[str, Any]

class PythonStatementAnalyzer:
    """
    Analyze Python method body statements

    Converts Python AST statements to intermediate representation
    for mapping to SpecQL steps
    """

    def analyze_method_body(self, method_body: List[str]) -> List[PythonStatement]:
        """
        Analyze method body lines

        Args:
            method_body: List of source code lines

        Returns:
            List of analyzed statements
        """
        statements = []

        # Join lines and parse
        body_code = '\n'.join(method_body)
        try:
            tree = ast.parse(body_code)

            for node in ast.walk(tree):
                if isinstance(node, ast.stmt):
                    stmt = self._analyze_statement(node)
                    if stmt:
                        statements.append(stmt)

        except SyntaxError:
            # Return empty list if can't parse
            pass

        return statements

    def _analyze_statement(self, node: ast.stmt) -> Optional[PythonStatement]:
        """Analyze single AST statement"""

        if isinstance(node, ast.Assign):
            return PythonStatement(
                statement_type='assign',
                raw_code=ast.unparse(node),
                ast_node=node,
                metadata={
                    'targets': [ast.unparse(t) for t in node.targets],
                    'value': ast.unparse(node.value),
                }
            )

        elif isinstance(node, ast.If):
            return PythonStatement(
                statement_type='if',
                raw_code=ast.unparse(node),
                ast_node=node,
                metadata={
                    'condition': ast.unparse(node.test),
                    'then_body': [ast.unparse(n) for n in node.body],
                    'else_body': [ast.unparse(n) for n in node.orelse] if node.orelse else [],
                }
            )

        elif isinstance(node, ast.Return):
            return PythonStatement(
                statement_type='return',
                raw_code=ast.unparse(node),
                ast_node=node,
                metadata={
                    'value': ast.unparse(node.value) if node.value else None,
                }
            )

        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            return PythonStatement(
                statement_type='call',
                raw_code=ast.unparse(node),
                ast_node=node,
                metadata={
                    'function': ast.unparse(node.value.func),
                    'args': [ast.unparse(arg) for arg in node.value.args],
                }
            )

        elif isinstance(node, ast.For):
            return PythonStatement(
                statement_type='for',
                raw_code=ast.unparse(node),
                ast_node=node,
                metadata={
                    'target': ast.unparse(node.target),
                    'iter': ast.unparse(node.iter),
                    'body': [ast.unparse(n) for n in node.body],
                }
            )

        elif isinstance(node, ast.Raise):
            return PythonStatement(
                statement_type='raise',
                raw_code=ast.unparse(node),
                ast_node=node,
                metadata={
                    'exception': ast.unparse(node.exc) if node.exc else None,
                }
            )

        return None