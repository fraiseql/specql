"""
Extract routes from Axum Rust code

Parses Axum route builders:
- Router::new().route("/users", get(handler))
- Router::new().route("/users", post(handler))
"""

from dataclasses import dataclass

from tree_sitter import Node

from .tree_sitter_rust_parser import RustParser


@dataclass
class AxumRoute:
    """Represents an Axum route"""

    method: str  # GET, POST, PUT, DELETE
    path: str  # /users/{id}
    handler_name: str | None = None


class AxumRouteExtractor:
    """Extract routes from Axum code"""

    def __init__(self):
        self.parser = RustParser()

    def extract_routes(self, source_code: str) -> list[AxumRoute]:
        """
        Extract all Axum routes from source code

        Args:
            source_code: Rust source code

        Returns:
            List of AxumRoute objects

        Example:
            >>> extractor = AxumRouteExtractor()
            >>> code = 'Router::new().route("/users", get(get_users))'
            >>> routes = extractor.extract_routes(code)
            >>> routes[0].method
            'GET'
            >>> routes[0].path
            '/users'
        """
        routes = []

        # Split code into lines and look for .route() calls
        lines = source_code.split("\n")
        for line in lines:
            line = line.strip()
            if ".route(" in line:
                route = self._parse_route_line(line, source_code)
                if route:
                    routes.append(route)

        return routes

    def _parse_route_line(self, line: str, source_code: str) -> AxumRoute | None:
        """
        Parse route from Axum .route() line

        Example: .route("/users/{id}", get(get_users))
        """
        # Find the .route( part
        route_start = line.find(".route(")
        if route_start == -1:
            return None

        # Extract the arguments part
        paren_count = 0
        args_start = route_start + 7  # After '.route('
        args_end = args_start

        for i in range(args_start, len(line)):
            if line[i] == "(":
                paren_count += 1
            elif line[i] == ")":
                paren_count -= 1
                if paren_count == 0:
                    args_end = i
                    break

        if args_end == args_start:
            return None

        args_text = line[args_start:args_end]

        # Split arguments by comma
        args = [arg.strip() for arg in args_text.split(",")]
        if len(args) < 2:
            return None

        # First argument should be path
        path_arg = args[0]
        if path_arg.startswith('"') and path_arg.endswith('"'):
            path = path_arg[1:-1]  # Remove quotes
        else:
            return None

        # Second argument should be method call like get(handler)
        method_arg = args[1]
        method = self._extract_method_from_call(method_arg)
        if not method:
            return None

        # Convert Axum path params to standard format
        # /users/{id} -> /users/:id
        path = path.replace("{", ":").replace("}", "")

        return AxumRoute(method=method, path=path)

    def _extract_method_from_call(self, method_call_text: str) -> str | None:
        """
        Extract HTTP method from Axum method call

        Examples:
        - get(handler) -> GET
        - post(handler) -> POST
        """
        methods = ["get", "post", "put", "delete", "patch"]

        for method in methods:
            if method_call_text.startswith(method + "("):
                return method.upper()

        return None

    def _get_call_arguments(self, call_expr: Node) -> list[Node]:
        """Get arguments from a call expression"""
        args = []
        arguments = self._find_node_by_type(call_expr, "arguments")
        if arguments:
            for child in arguments.children:
                if child.type not in ["(", ")", ","]:
                    args.append(child)
        return args

    def _find_node_by_type(self, node: Node, node_type: str) -> Node | None:
        """Recursively find first node of given type (depth-first search)"""
        if node.type == node_type:
            return node

        for child in node.children:
            result = self._find_node_by_type(child, node_type)
            if result:
                return result

        return None

    def _extract_string_literal(self, node: Node, source_code: str) -> str | None:
        """Extract string literal content from a node"""
        if node.type == "string_literal":
            text = self.parser.get_node_text(node, source_code)
            # Remove quotes
            return text.strip('"')

        # Handle other string expressions
        string_lit = self._find_node_by_type(node, "string_literal")
        if string_lit:
            text = self.parser.get_node_text(string_lit, source_code)
            return text.strip('"')

        return None
