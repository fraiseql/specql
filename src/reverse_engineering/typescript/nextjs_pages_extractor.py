"""
Extract routes from Next.js Pages Router

Parses Next.js API routes in pages/api/*:
- export default function handler(req, res) { }
- export default async function handler(req, res) { }
"""

from dataclasses import dataclass
from pathlib import Path

from .tree_sitter_parser import TypeScriptParser


@dataclass
class NextJSPagesRoute:
    """Represents a Next.js Pages API route"""

    path: str  # Derived from file path: pages/api/users.ts -> /api/users
    is_dynamic: bool = False  # [id].ts
    methods: list[str] | None = None  # Extracted from handler (req.method checks)


class NextJSPagesExtractor:
    """Extract routes from Next.js Pages Router"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def extract_route_from_file(
        self, file_path: str, source_code: str
    ) -> NextJSPagesRoute | None:
        """
        Extract route from Next.js API file

        File path determines URL:
        - pages/api/users.ts -> /api/users
        - pages/api/users/[id].ts -> /api/users/:id
        - pages/api/users/index.ts -> /api/users

        Args:
            file_path: Path to the API file
            source_code: Content of the API file

        Returns:
            NextJSPagesRoute if it's a valid API route, None otherwise
        """
        # Convert file path to URL path
        url_path = self._file_path_to_url(file_path)

        # Parse source to check if it's an API route
        ast = self.parser.parse(source_code)

        # Look for default export
        if not self._has_default_export(ast, source_code):
            return None

        # Check if dynamic route ([id].ts)
        is_dynamic = "[" in file_path and "]" in file_path

        # Extract HTTP methods from handler
        methods = self._extract_methods(ast, source_code)

        return NextJSPagesRoute(
            path=url_path,
            is_dynamic=is_dynamic,
            methods=methods or ["GET", "POST"],  # Default to both
        )

    def _file_path_to_url(self, file_path: str) -> str:
        """
        Convert file path to URL path

        pages/api/users.ts -> /api/users
        pages/api/users/[id].ts -> /api/users/:id
        pages/api/users/index.ts -> /api/users
        """
        path = Path(file_path)

        # Remove pages/ prefix
        parts = list(path.parts)
        if "pages" in parts:
            idx = parts.index("pages")
            parts = parts[idx + 1 :]

        # Remove .ts/.tsx extension
        parts[-1] = path.stem

        # Handle index.ts
        if parts[-1] == "index":
            parts = parts[:-1]

        # Convert [id] to :id
        parts = [p.replace("[", ":").replace("]", "") for p in parts]

        # Join with /
        url = "/" + "/".join(parts)

        return url

    def _has_default_export(self, ast, source_code: str) -> bool:
        """Check if file has default export"""
        exports = self.parser.find_nodes_by_type(ast, "export_statement")

        for export in exports:
            text = self.parser.get_node_text(export, source_code)
            if "default" in text:
                return True

        return False

    def _extract_methods(self, ast, source_code: str) -> list[str]:
        """
        Extract HTTP methods from handler

        Looks for: if (req.method === 'GET') { }
        """
        methods = []

        # Look for req.method === 'METHOD' patterns
        import re

        method_pattern = r"req\.method\s*===\s*['\"](\w+)['\"]"
        matches = re.findall(method_pattern, source_code)

        for match in matches:
            if match in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                methods.append(match)

        return list(set(methods))  # Deduplicate
