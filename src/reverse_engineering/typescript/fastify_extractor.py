"""
Extract routes from Fastify TypeScript code

Parses Fastify route definitions:
- fastify.get('/path', handler)
- fastify.post('/path', opts, handler)
"""

from dataclasses import dataclass
from typing import List, Optional
from tree_sitter import Node

from .tree_sitter_parser import TypeScriptParser


@dataclass
class FastifyRoute:
    """Represents a Fastify route"""

    method: str  # GET, POST, PUT, DELETE
    path: str  # /users/:id
    handler_name: Optional[str] = None
    has_schema: bool = False


class FastifyRouteExtractor:
    """Extract routes from Fastify code"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def extract_routes(self, source_code: str) -> List[FastifyRoute]:
        """
        Extract all Fastify routes from source code

        Args:
            source_code: TypeScript source code

        Returns:
            List of FastifyRoute objects

        Example:
            >>> extractor = FastifyRouteExtractor()
            >>> code = "fastify.get('/users', getUsers);"
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
        Check if node is a Fastify route definition

        Fastify routes look like:
        - fastify.get(...)
        - fastify.post(...)
        - app.get(...) (Fastify can also use 'app')

        Node structure:
        call_expression
          member_expression
            identifier: "fastify" or "app"
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

        # Check if object is 'fastify' or 'app'
        object_name = self.parser.get_node_text(member_expr.children[0], source_code)
        if object_name not in ["fastify", "app"]:
            return False

        # Check if method is HTTP method
        method_name = self.parser.get_node_text(member_expr.children[2], source_code)
        if method_name not in ["get", "post", "put", "delete", "patch"]:
            return False

        return True

    def _parse_route(self, node: Node, source_code: str) -> Optional[FastifyRoute]:
        """
        Parse route definition into FastifyRoute object

        Fastify routes can have different formats:
        - fastify.get('/users', handler)
        - fastify.post('/users', { schema: ... }, handler)

        Route structure:
        fastify.get('/users', handler)
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

        # Find arguments - Fastify can have 2 or 3 args
        path = None
        handler_name = None
        has_schema = False

        # Collect all non-parenthesis arguments
        arg_nodes = []
        for arg in args.children:
            if arg.type not in ["(", ")", ","]:
                arg_nodes.append(arg)

        # Fastify routes: fastify.method(path, [options,] handler)
        if len(arg_nodes) >= 2:
            # First argument should be path (string)
            if arg_nodes[0].type == "string":
                path_text = self.parser.get_node_text(arg_nodes[0], source_code)
                path = path_text.strip('"').strip("'")

            # Last argument should be handler (identifier or function)
            last_arg = arg_nodes[-1]
            if last_arg.type == "identifier":
                handler_name = self.parser.get_node_text(last_arg, source_code)
            elif last_arg.type == "arrow_function" or last_arg.type == "function":
                handler_name = "anonymous_handler"

            # Check if there's a middle argument (options object)
            if len(arg_nodes) == 3:
                middle_arg = arg_nodes[1]
                if middle_arg.type == "object":
                    has_schema = True

        if not path:
            return None

        return FastifyRoute(
            method=method, path=path, handler_name=handler_name, has_schema=has_schema
        )
