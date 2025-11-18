"""
Tree-sitter based TypeScript parser

Combines all TypeScript extractors for comprehensive route and action extraction.
"""

from dataclasses import dataclass
from typing import List, Optional
from tree_sitter import Node

from .tree_sitter_parser import TypeScriptParser


@dataclass
class TypeScriptRoute:
    """Represents a TypeScript route extracted by tree-sitter"""

    method: str
    path: str
    framework: str  # express, fastify, nextjs-pages, nextjs-app
    handler_name: Optional[str] = None


@dataclass
class TypeScriptAction:
    """Represents a TypeScript server action extracted by tree-sitter"""

    name: str
    is_server_action: bool = True


class TreeSitterTypeScriptParser:
    """Tree-sitter based TypeScript parser with regex fallbacks"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def parse(self, source_code: str) -> Node:
        """
        Parse TypeScript source code into AST

        Args:
            source_code: TypeScript source code

        Returns:
            Root AST node
        """
        return self.parser.parse(source_code)

    def extract_routes(self, ast: Node, source_code: str) -> List[TypeScriptRoute]:
        """
        Extract all routes from source code using regex patterns

        Args:
            ast: Parsed AST (unused for now)
            source_code: Original source code

        Returns:
            List of all routes found
        """
        routes = []

        # Express routes: app.get('/path', handler)
        import re

        express_pattern = (
            r"(?:app|router)\.(get|post|put|delete|patch)\s*(?:<[^>]*>)?\s*\(\s*['\"]([^'\"]+)['\"]"
        )
        for match in re.finditer(express_pattern, source_code):
            method = match.group(1).upper()
            path = match.group(2)
            routes.append(
                TypeScriptRoute(method=method, path=path, framework="express", handler_name=None)
            )

        # Fastify routes: fastify.get('/path', handler)
        fastify_pattern = r"fastify\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(fastify_pattern, source_code):
            method = match.group(1).upper()
            path = match.group(2)
            routes.append(
                TypeScriptRoute(method=method, path=path, framework="fastify", handler_name=None)
            )

        return routes

    def extract_nextjs_pages_routes(
        self, ast: Node, source_code: str, file_path: str
    ) -> List[TypeScriptRoute]:
        """
        Extract Next.js Pages Router routes

        Args:
            ast: Parsed AST
            source_code: Original source code
            file_path: Path to the file

        Returns:
            List of Next.js pages routes
        """
        import re

        method_pattern = r"req\.method\s*===\s*['\"](\w+)['\"]"
        methods = re.findall(method_pattern, source_code)

        # Convert file path to route path
        route_path = file_path.replace("pages", "").replace(".ts", "").replace(".js", "")

        routes = []
        for method in methods:
            routes.append(
                TypeScriptRoute(
                    method=method, path=route_path, framework="nextjs-pages", handler_name="handler"
                )
            )

        return routes

    def extract_nextjs_app_routes(
        self, ast: Node, source_code: str, file_path: str
    ) -> List[TypeScriptRoute]:
        """
        Extract Next.js App Router routes

        Args:
            ast: Parsed AST
            source_code: Original source code
            file_path: Path to the file

        Returns:
            List of Next.js app routes
        """
        import re

        # Look for export async function GET/POST/etc.
        method_pattern = r"export\s+async\s+function\s+(GET|POST|PUT|DELETE|PATCH)"
        methods = re.findall(method_pattern, source_code)

        # Convert file path to route path
        # app/api/contacts/route.ts -> /api/contacts
        route_path = "/" + "/".join(
            file_path.replace("app/", "")
            .replace("/route.ts", "")
            .replace("/route.js", "")
            .split("/")
        )

        routes = []
        for method in methods:
            routes.append(
                TypeScriptRoute(
                    method=method,
                    path=route_path,
                    framework="nextjs-app",
                    handler_name=method.lower(),
                )
            )

        return routes

    def extract_server_actions(self, ast: Node, source_code: str) -> List[TypeScriptAction]:
        """
        Extract Next.js Server Actions

        Args:
            ast: Parsed AST
            source_code: Original source code

        Returns:
            List of server actions
        """
        actions = []

        # Check for 'use server' directive
        if "'use server'" not in source_code and '"use server"' not in source_code:
            return actions

        # Extract exported async functions using regex
        import re

        export_pattern = r"export\s+async\s+function\s+(\w+)\s*\("
        for match in re.finditer(export_pattern, source_code):
            func_name = match.group(1)
            actions.append(TypeScriptAction(name=func_name))

        return actions
