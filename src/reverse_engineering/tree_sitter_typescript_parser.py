"""
Tree-sitter-based TypeScript AST Parser

Replaces regex parsing with robust AST traversal for:
- Express routes
- Fastify routes
- Next.js Pages Router
- Next.js App Router
- Next.js Server Actions
"""

from typing import Optional, List, Any, TYPE_CHECKING
import re
from dataclasses import dataclass, field

# Conditional imports for optional dependencies
try:
    import tree_sitter_typescript as ts_typescript
    from tree_sitter import Language, Parser, Node

    HAS_TREE_SITTER_TYPESCRIPT = True
except ImportError:
    HAS_TREE_SITTER_TYPESCRIPT = False
    ts_typescript = None
    if not TYPE_CHECKING:
        # Create stub types for when the dependency is missing
        Language = Any  # type: ignore
        Parser = Any  # type: ignore
        Node = Any  # type: ignore


@dataclass
class TypeScriptRoute:
    """Represents a TypeScript route"""

    method: str
    path: str
    framework: str  # express, fastify, nextjs-pages, nextjs-app
    handler_name: Optional[str] = None
    parameters: List[str] = field(default_factory=list)


@dataclass
class TypeScriptAction:
    """Represents a TypeScript server action"""

    name: str
    is_server_action: bool = True


class TreeSitterTypeScriptParser:
    """Tree-sitter based TypeScript parser"""

    def __init__(self):
        """Initialize tree-sitter parser with TypeScript grammar"""
        if not HAS_TREE_SITTER_TYPESCRIPT:
            raise ImportError(
                "tree-sitter-typescript is required for TypeScript parsing. "
                "Install with: pip install specql[reverse]"
            )

        # Initialize with TypeScript grammar (handles both .ts and .tsx)
        self.language = Language(ts_typescript.language_typescript())
        self.parser = Parser(self.language)

    def parse(self, code: str) -> Optional[Node]:
        """Parse TypeScript code into AST"""
        try:
            tree = self.parser.parse(bytes(code, "utf8"))
            return tree.root_node
        except Exception as e:
            print(f"Parse error: {e}")
            return None

    def extract_routes(self, ast: Node) -> List[TypeScriptRoute]:
        """
        Extract routes from AST supporting multiple frameworks.

        Supports: Express, Fastify, Next.js Pages/App Router
        """
        routes = []

        # Extract Express routes
        express_routes = self._extract_express_routes(ast)
        routes.extend(express_routes)

        # Extract Fastify routes
        fastify_routes = self._extract_fastify_routes(ast)
        routes.extend(fastify_routes)

        return routes

    def extract_nextjs_pages_routes(self, ast: Node, file_path: str) -> List[TypeScriptRoute]:
        """Extract Next.js Pages Router API routes"""
        routes = []

        # Convert file path to route path
        # pages/api/contacts.ts -> /api/contacts
        route_path = self._convert_pages_path_to_route(file_path)
        if not route_path:
            return routes

        # Detect methods from req.method checks or exported handlers
        methods = self._detect_pages_router_methods(ast)

        for method in methods:
            routes.append(
                TypeScriptRoute(
                    method=method, path=route_path, framework="nextjs-pages", handler_name="handler"
                )
            )

        return routes

    def extract_nextjs_app_routes(self, ast: Node, file_path: str) -> List[TypeScriptRoute]:
        """Extract Next.js App Router route handlers"""
        routes = []

        # Convert file path to route path
        # app/api/contacts/route.ts -> /api/contacts
        route_path = self._convert_app_path_to_route(file_path)
        if not route_path:
            return routes

        # Detect exported HTTP method functions
        http_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        for method in http_methods:
            if self._has_exported_function(ast, method):
                routes.append(
                    TypeScriptRoute(
                        method=method,
                        path=route_path,
                        framework="nextjs-app",
                        handler_name=method.lower(),
                    )
                )

        return routes

    def extract_server_actions(self, ast: Node) -> List[TypeScriptAction]:
        """Extract Next.js Server Actions from AST"""
        actions = []

        # Check for 'use server' directive
        if not self._has_use_server_directive(ast):
            return actions

        # Extract exported async functions
        exported_functions = self._find_exported_functions(ast)
        for func_name in exported_functions:
            actions.append(TypeScriptAction(name=func_name))

        return actions

        # Extract exported async functions
        exported_functions = self._find_exported_functions(ast)
        print(f"DEBUG: exported_functions = {exported_functions}")
        for func_name in exported_functions:
            actions.append(TypeScriptAction(name=func_name))

        return actions

    def _extract_express_routes(self, ast: Node) -> List[TypeScriptRoute]:
        """Extract Express router.get/post/put/delete() calls"""
        routes = []

        # Find all call expressions
        call_expressions = self._find_nodes_by_type(ast, "call_expression")

        for call_expr in call_expressions:
            route = self._parse_express_route_call(call_expr)
            if route:
                routes.append(route)

        return routes

    def _extract_fastify_routes(self, ast: Node) -> List[TypeScriptRoute]:
        """Extract Fastify route definitions"""
        routes = []

        # Find all call expressions
        call_expressions = self._find_nodes_by_type(ast, "call_expression")

        for call_expr in call_expressions:
            route = self._parse_fastify_route_call(call_expr)
            if route:
                routes.append(route)

        return routes

    def _parse_express_route_call(self, call_expr: Node) -> Optional[TypeScriptRoute]:
        """Parse Express router.method() call"""
        # Look for member expression like router.get, router.post, etc.
        member_expr = self._find_node_by_type(call_expr, "member_expression")
        if not member_expr:
            return None

        # Check if it's a router method call
        object_node = member_expr.child_by_field_name("object")
        property_node = member_expr.child_by_field_name("property")

        if not (object_node and property_node):
            return None

        object_name = self._node_text(object_node)
        method_name = self._node_text(property_node)

        # Check if object is 'router' and method is HTTP method
        if object_name != "router":
            return None

        http_methods = ["get", "post", "put", "patch", "delete"]
        if method_name not in http_methods:
            return None

        # Extract path argument
        arguments = self._get_call_arguments(call_expr)
        if not arguments:
            return None

        path_arg = arguments[0]
        path = self._extract_string_literal(path_arg)

        if path:
            return TypeScriptRoute(method=method_name.upper(), path=path, framework="express")

        return None

    def _parse_fastify_route_call(self, call_expr: Node) -> Optional[TypeScriptRoute]:
        """Parse Fastify fastify.method() call"""
        # Look for member expression like fastify.get, fastify.post, etc.
        member_expr = self._find_node_by_type(call_expr, "member_expression")
        if not member_expr:
            return None

        # Check if it's a fastify method call
        object_node = member_expr.child_by_field_name("object")
        property_node = member_expr.child_by_field_name("property")

        if not (object_node and property_node):
            return None

        object_name = self._node_text(object_node)
        method_name = self._node_text(property_node)

        # Check if object is 'fastify' and method is HTTP method
        if object_name != "fastify":
            return None

        http_methods = ["get", "post", "put", "patch", "delete"]
        if method_name not in http_methods:
            return None

        # Extract path argument
        arguments = self._get_call_arguments(call_expr)
        if not arguments:
            return None

        path_arg = arguments[0]
        path = self._extract_string_literal(path_arg)

        if path:
            return TypeScriptRoute(method=method_name.upper(), path=path, framework="fastify")

        return None

    def _has_use_server_directive(self, ast: Node) -> bool:
        """Check if the file contains 'use server' directive"""
        # Look for expression statements that contain 'use server'
        expression_statements = self._find_nodes_by_type(ast, "expression_statement")

        for expr_stmt in expression_statements:
            text = self._node_text(expr_stmt).strip()

            # Check for 'use server' directive (with or without quotes and semicolon)
            if "'use server'" in text or '"use server"' in text or "use server" in text:
                return True

        return False

    def _find_exported_functions(self, ast: Node) -> List[str]:
        """Find all exported async function declarations"""
        functions = []

        # Find all export statements
        export_statements = self._find_nodes_by_type(ast, "export_statement")

        for export_stmt in export_statements:
            stmt_text = self._node_text(export_stmt)

            # Check if it's an async function export
            if "export async function" in stmt_text:
                # Extract function name from pattern: 'export async function name('
                if "function " in stmt_text:
                    name_part = stmt_text.split("function ")[1].split("(")[0].strip()
                    functions.append(name_part)

        return functions

    def _is_async_function(self, function_node: Node) -> bool:
        """Check if a function has the 'async' keyword"""
        # Look for 'async' token in function children
        for child in function_node.children:
            if self._node_text(child) == "async":
                return True
        return False

    def _extract_string_literal(self, node: Node) -> Optional[str]:
        """Extract string literal content from a node"""
        if node.type == "string":
            text = self._node_text(node)
            # Remove quotes
            return text.strip("\"'")

        # Handle template strings and other string expressions
        string_lit = self._find_node_by_type(node, "string")
        if string_lit:
            text = self._node_text(string_lit)
            return text.strip("\"'")

        return None

    def _get_call_arguments(self, call_expr: Node) -> List[Node]:
        """Get arguments from a call expression"""
        args = []
        arguments = self._find_node_by_type(call_expr, "arguments")
        if arguments:
            for child in arguments.children:
                if child.type not in ["(", ")", ","]:
                    args.append(child)
        return args

    def _find_node_by_type(self, node: Node, node_type: str) -> Optional[Node]:
        """Recursively find first node of given type (depth-first search)"""
        if node.type == node_type:
            return node

        for child in node.children:
            result = self._find_node_by_type(child, node_type)
            if result:
                return result

        return None

    def _find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
        """Recursively find all nodes of given type"""
        results = []
        if node.type == node_type:
            results.append(node)

        for child in node.children:
            results.extend(self._find_nodes_by_type(child, node_type))

        return results

    def _node_text(self, node: Node) -> str:
        """Get text content of a node"""
        return node.text.decode("utf8") if isinstance(node.text, bytes) else str(node.text)

    def _convert_pages_path_to_route(self, file_path: str) -> Optional[str]:
        """Convert Next.js Pages Router file path to route path"""
        # pages/api/contacts.ts -> /api/contacts
        # pages/api/contacts/[id].ts -> /api/contacts/[id]

        if "pages" not in file_path:
            return None

        # Remove pages prefix and file extension
        route_path = file_path.replace("pages", "").replace(".ts", "").replace(".js", "")

        # Remove leading slash if present
        if route_path.startswith("/"):
            route_path = route_path[1:]

        return f"/{route_path}" if route_path else "/"

    def _convert_app_path_to_route(self, file_path: str) -> Optional[str]:
        """Convert Next.js App Router file path to route path"""
        # app/api/contacts/route.ts -> /api/contacts
        # app/api/contacts/[id]/route.ts -> /api/contacts/[id]

        if "app" not in file_path or "route." not in file_path:
            return None

        # Remove app prefix and route.ts
        route_path = file_path.replace("app", "").replace("/route.ts", "").replace("/route.js", "")

        # Remove leading slash if present
        if route_path.startswith("/"):
            route_path = route_path[1:]

        return f"/{route_path}" if route_path else "/"

    def _detect_pages_router_methods(self, ast: Node) -> List[str]:
        """Detect HTTP methods used in Next.js Pages Router"""
        methods = []

        # Check for req.method conditionals
        method_checks = self._find_req_method_checks(ast)
        methods.extend(method_checks)

        # Check for exported HTTP method handlers
        exported_handlers = self._find_exported_pages_handlers(ast)
        methods.extend(exported_handlers)

        # If no specific methods found, assume GET (default)
        if not methods:
            methods.append("GET")

        # Remove duplicates
        return list(set(methods))

    def _find_req_method_checks(self, ast: Node) -> List[str]:
        """Find req.method === 'GET' style checks"""
        methods = []

        # Look for binary expressions with req.method
        binary_exprs = self._find_nodes_by_type(ast, "binary_expression")

        for expr in binary_exprs:
            left = expr.child_by_field_name("left")
            operator = expr.child_by_field_name("operator")
            right = expr.child_by_field_name("right")

            if left and operator and right and self._node_text(operator) == "===":
                # Check if left side is req.method
                if self._is_req_method_access(left):
                    method = self._extract_string_literal(right)
                    if method and method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                        methods.append(method.upper())

        return methods

    def _find_exported_pages_handlers(self, ast: Node) -> List[str]:
        """Find exported handler functions in Pages Router"""
        methods = []

        # Look for exported functions that might be HTTP handlers
        export_statements = self._find_nodes_by_type(ast, "export_statement")

        for export_stmt in export_statements:
            # Check for default export of handler function
            if "default" in self._node_text(export_stmt):
                # This is likely the default export handler
                methods.extend(["GET", "POST", "PUT", "PATCH", "DELETE"])

        return methods

    def _has_exported_function(self, ast: Node, function_name: str) -> bool:
        """Check if AST has an exported function with given name"""
        export_statements = self._find_nodes_by_type(ast, "export_statement")

        for export_stmt in export_statements:
            # Look for function declarations
            function_node = self._find_node_by_type(export_stmt, "function_declaration")
            if function_node:
                name_node = function_node.child_by_field_name("name")
                if name_node and self._node_text(name_node) == function_name:
                    return True

        return False

    def _is_req_method_access(self, node: Node) -> bool:
        """Check if node represents req.method access"""
        # Look for member expression: req.method
        if node.type == "member_expression":
            object_node = node.child_by_field_name("object")
            property_node = node.child_by_field_name("property")

            if (
                object_node
                and property_node
                and self._node_text(object_node) == "req"
                and self._node_text(property_node) == "method"
            ):
                return True

        return False
