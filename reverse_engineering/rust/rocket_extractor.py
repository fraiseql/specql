"""
Extract routes from Rocket Rust code

Parses Rocket route macros:
- #[get("/users")]
- #[post("/users")]
"""

from dataclasses import dataclass

from tree_sitter import Node

from .tree_sitter_rust_parser import RustParser


@dataclass
class RocketRoute:
    """Represents a Rocket route"""

    method: str  # GET, POST, PUT, DELETE
    path: str  # /users/<id>
    handler_name: str | None = None


class RocketRouteExtractor:
    """Extract routes from Rocket code"""

    def __init__(self):
        self.parser = RustParser()

    def extract_routes(self, source_code: str) -> list[RocketRoute]:
        """
        Extract all Rocket routes from source code

        Args:
            source_code: Rust source code

        Returns:
            List of RocketRoute objects

        Example:
            >>> extractor = RocketRouteExtractor()
            >>> code = '#[get("/users")] fn get_users() {}'
            >>> routes = extractor.extract_routes(code)
            >>> routes[0].method
            'GET'
            >>> routes[0].path
            '/users'
        """
        # Parse source
        ast = self.parser.parse(source_code)

        routes = []

        # Find all attribute items (#[get("/path")])
        attributes = self.parser.find_nodes_by_type(ast, "attribute_item")

        for attr in attributes:
            route = self._parse_attribute_route(attr, source_code)
            if route:
                routes.append(route)

        return routes

    def _parse_attribute_route(self, node: Node, source_code: str) -> RocketRoute | None:
        """
        Parse route from Rocket attribute macro

        Example: #[get("/users/<id>")]
        """
        text = self.parser.get_node_text(node, source_code)

        # Check if it's a route macro
        methods = ["get", "post", "put", "delete", "patch"]
        method = None

        for m in methods:
            if f"#[{m}(" in text:
                method = m.upper()
                break

        if not method:
            return None

        # Extract path from string literal
        # Format: #[get("/users/<id>")]
        start = text.find('"')
        end = text.rfind('"')

        if start == -1 or end == -1:
            return None

        path = text[start + 1 : end]

        # Convert Rocket path params to standard format
        # /users/<id> -> /users/:id
        path = path.replace("<", ":").replace(">", "")

        return RocketRoute(method=method, path=path)
