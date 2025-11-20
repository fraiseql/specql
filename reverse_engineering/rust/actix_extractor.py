"""
Extract routes from Actix-web Rust code

Parses Actix route macros:
- #[get("/users")]
- #[post("/users")]
- web::get().to(handler)
"""

from dataclasses import dataclass

from tree_sitter import Node

from .tree_sitter_rust_parser import RustParser


@dataclass
class ActixRoute:
    """Represents an Actix-web route"""

    method: str  # GET, POST, PUT, DELETE
    path: str  # /users/{id}
    handler_name: str | None = None


class ActixRouteExtractor:
    """Extract routes from Actix-web code"""

    def __init__(self):
        self.parser = RustParser()

    def extract_routes(self, source_code: str) -> list[ActixRoute]:
        """
        Extract all Actix routes from source code

        Args:
            source_code: Rust source code

        Returns:
            List of ActixRoute objects

        Example:
            >>> extractor = ActixRouteExtractor()
            >>> code = '#[get("/users")] async fn get_users() {}'
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

    def _parse_attribute_route(self, node: Node, source_code: str) -> ActixRoute | None:
        """
        Parse route from attribute macro

        Example: #[get("/users/{id}")]
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
        # Format: #[get("/users/{id}")]
        start = text.find('"')
        end = text.rfind('"')

        if start == -1 or end == -1:
            return None

        path = text[start + 1 : end]

        # Convert Rust path params to standard format
        # /users/{id} -> /users/:id
        path = path.replace("{", ":").replace("}", "")

        return ActixRoute(method=method, path=path)
