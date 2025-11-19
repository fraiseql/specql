"""
Extract routes from Next.js App Router

Parses Next.js API routes in app/api/*:
- export async function GET(request) { }
- export async function POST(request) { }
"""

from dataclasses import dataclass
from pathlib import Path

from .tree_sitter_parser import TypeScriptParser


@dataclass
class NextJSAppRoute:
    """Represents a Next.js App Router API route"""

    path: str
    methods: list[str]  # GET, POST, etc.
    is_dynamic: bool = False


class NextJSAppExtractor:
    """Extract routes from Next.js App Router"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def extract_route_from_file(self, file_path: str, source_code: str) -> NextJSAppRoute | None:
        """
        Extract route from Next.js App Router file

        File path determines URL:
        - app/api/users/route.ts -> /api/users
        - app/api/users/[id]/route.ts -> /api/users/:id

        Exports determine methods:
        - export async function GET(request) { }
        - export async function POST(request) { }

        Args:
            file_path: Path to the route file
            source_code: Content of the route file

        Returns:
            NextJSAppRoute if it contains HTTP method exports, None otherwise
        """
        # Convert file path to URL
        url_path = self._file_path_to_url(file_path)

        # Parse source
        ast = self.parser.parse(source_code)

        # Extract exported functions
        methods = self._extract_exported_methods(ast, source_code)

        if not methods:
            return None

        # Check if dynamic route
        is_dynamic = "[" in file_path and "]" in file_path

        return NextJSAppRoute(path=url_path, methods=methods, is_dynamic=is_dynamic)

    def _file_path_to_url(self, file_path: str) -> str:
        """
        Convert App Router file path to URL path

        app/api/users/route.ts -> /api/users
        app/api/users/[id]/route.ts -> /api/users/:id
        """
        path = Path(file_path)
        parts = list(path.parts)

        # Remove app/ prefix
        if "app" in parts:
            idx = parts.index("app")
            parts = parts[idx + 1 :]

        # Remove route.ts
        if parts[-1] == "route.ts" or parts[-1] == "route":
            parts = parts[:-1]

        # Convert [id] to :id
        parts = [p.replace("[", ":").replace("]", "") for p in parts]

        url = "/" + "/".join(parts)
        return url

    def _extract_exported_methods(self, ast, source_code: str) -> list[str]:
        """
        Extract exported HTTP method functions

        Looks for:
        - export async function GET(request) { }
        - export function POST(request) { }
        """
        methods = []

        exports = self.parser.find_nodes_by_type(ast, "export_statement")

        for export in exports:
            # Look for function declarations
            for child in export.children:
                if child.type == "function_declaration":
                    # Get function name
                    for func_child in child.children:
                        if func_child.type == "identifier":
                            name = self.parser.get_node_text(func_child, source_code)
                            if name in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                                methods.append(name)

        return methods
