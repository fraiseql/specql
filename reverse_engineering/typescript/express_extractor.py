"""
Extract routes from Express.js TypeScript code

Parses Express.js route definitions:
- app.get('/path', handler)
- app.post('/path', handler)
- router.get('/path', handler)
"""

from dataclasses import dataclass

from tree_sitter import Node

from .tree_sitter_parser import TypeScriptParser


@dataclass
class ExpressRoute:
    """Represents an Express.js route"""

    method: str  # GET, POST, PUT, DELETE
    path: str  # /users/:id
    handler_name: str | None = None
    has_middleware: bool = False


class ExpressRouteExtractor:
    """Extract routes from Express.js code"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def extract_routes(self, source_code: str) -> list[ExpressRoute]:
        """
        Extract all Express routes from source code

        Args:
            source_code: TypeScript source code

        Returns:
            List of ExpressRoute objects

        Example:
            >>> extractor = ExpressRouteExtractor()
            >>> code = "app.get('/users', getUsers);"
            >>> routes = extractor.extract_routes(code)
            >>> routes[0].method
            'GET'
            >>> routes[0].path
            '/users'
        """
        # Parse source
        ast = self.parser.parse(source_code)

        routes = []

        # Find all call expressions (function calls)
        calls = self.parser.find_nodes_by_type(ast, "call_expression")

        for call in calls:
            if self._is_route_definition(call, source_code):
                route = self._parse_route(call, source_code)
                if route:
                    routes.append(route)

        return routes

    def _is_route_definition(self, node: Node, source_code: str) -> bool:
        """
        Check if node is a route definition

        Express routes look like:
        - app.get(...)
        - app.post(...)
        - router.get(...)

        Node structure:
        call_expression
          member_expression
            identifier: "app" or "router"
            property_identifier: "get", "post", "put", "delete"
          arguments
        """
        # Must have at least 2 children (member_expression + arguments)
        if len(node.children) < 2:
            return False

        # First child should be member_expression
        if node.children[0].type != "member_expression":
            return False

        member_expr = node.children[0]

        # Member expression should have 3 parts: object.property
        if len(member_expr.children) < 3:
            return False

        # Check if object is 'app' or 'router'
        object_name = self.parser.get_node_text(member_expr.children[0], source_code)
        if object_name not in ["app", "router"]:
            return False

        # Check if method is HTTP method
        method_name = self.parser.get_node_text(member_expr.children[2], source_code)
        if method_name not in ["get", "post", "put", "delete", "patch"]:
            return False

        return True

    def _parse_route(self, node: Node, source_code: str) -> ExpressRoute | None:
        """
        Parse route definition into ExpressRoute object

        Route structure:
        app.get('/users', handler)
              └─┬─┘ └──┬──┘  └──┬──┘
              method  path   handler
        """
        member_expr = node.children[0]
        method_name = self.parser.get_node_text(member_expr.children[2], source_code)
        method = method_name.upper()

        # Get arguments
        if len(node.children) < 2:
            return None

        args = node.children[1]  # arguments node

        # Find string argument (the path)
        path = None
        handler_name = None

        for arg in args.children:
            if arg.type == "string":
                # Remove quotes
                path_text = self.parser.get_node_text(arg, source_code)
                path = path_text.strip('"').strip("'")
            elif arg.type == "identifier":
                handler_name = self.parser.get_node_text(arg, source_code)

        if not path:
            return None

        return ExpressRoute(method=method, path=path, handler_name=handler_name)
