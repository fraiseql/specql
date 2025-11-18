"""
TypeScript Parser - Extract routes and actions from TypeScript code

Supports:
- Express routes
- Fastify routes
- Next.js Pages Router (pages/api)
- Next.js App Router (app directory, route.ts)
- Next.js Server Actions

Uses tree-sitter for robust AST parsing with regex fallback for compatibility.
"""

from dataclasses import dataclass
from typing import List, Optional
import re

# Import tree-sitter parser with dependency check
from src.core.dependencies import TREE_SITTER

TREE_SITTER_AVAILABLE = TREE_SITTER.available

if TREE_SITTER_AVAILABLE:
    from .tree_sitter_typescript_parser import (
        TreeSitterTypeScriptParser,
        TypeScriptRoute as TSRoute,
        TypeScriptAction as TSAction,
    )


@dataclass
class TypeScriptRoute:
    """Represents a TypeScript route"""

    method: str
    path: str
    framework: str  # express, fastify, nextjs-pages, nextjs-app
    handler_name: Optional[str] = None


@dataclass
class TypeScriptAction:
    """Represents a TypeScript server action"""

    name: str
    is_server_action: bool = True


class TypeScriptParser:
    """Parser for TypeScript routes and actions"""

    def __init__(self, use_tree_sitter: bool = True):
        """Initialize parser with optional tree-sitter support"""
        self.use_tree_sitter = use_tree_sitter and TREE_SITTER_AVAILABLE
        self.tree_sitter_parser = None

        if self.use_tree_sitter:
            try:
                self.tree_sitter_parser = TreeSitterTypeScriptParser()
            except Exception:
                # Fall back to regex if tree-sitter fails to initialize
                self.use_tree_sitter = False

    def extract_routes(self, code: str) -> List[TypeScriptRoute]:
        """Extract Express/Fastify routes using tree-sitter or regex fallback"""
        if self.use_tree_sitter and self.tree_sitter_parser:
            try:
                ast = self.tree_sitter_parser.parse(code)
                if ast:
                    ts_routes = self.tree_sitter_parser.extract_routes(ast)
                    # Convert to our TypeScriptRoute format
                    return [
                        TypeScriptRoute(
                            method=route.method,
                            path=route.path,
                            framework=route.framework,
                            handler_name=route.handler_name,
                        )
                        for route in ts_routes
                    ]
            except Exception:
                # Fall back to regex parsing
                pass

        # Regex fallback
        return self._extract_routes_regex(code)

    def _extract_routes_regex(self, code: str) -> List[TypeScriptRoute]:
        """Extract routes using regex patterns (fallback method)"""
        routes = []

        # Express patterns
        express_pattern = r'router\.(get|post|put|patch|delete)\([\'"]([^\'"]+)[\'"]'
        for match in re.finditer(express_pattern, code):
            method = match.group(1).upper()
            path = match.group(2)
            routes.append(TypeScriptRoute(method=method, path=path, framework="express"))

        # Fastify patterns
        fastify_pattern = r'fastify\.(get|post|put|patch|delete)\([\'"]([^\'"]+)[\'"]'
        for match in re.finditer(fastify_pattern, code):
            method = match.group(1).upper()
            path = match.group(2)
            routes.append(TypeScriptRoute(method=method, path=path, framework="fastify"))

        return routes

    def extract_nextjs_pages_routes(self, code: str, file_path: str) -> List[TypeScriptRoute]:
        """Extract Next.js Pages Router API routes"""
        if self.use_tree_sitter and self.tree_sitter_parser:
            try:
                ast = self.tree_sitter_parser.parse(code)
                if ast:
                    ts_routes = self.tree_sitter_parser.extract_nextjs_pages_routes(ast, file_path)
                    # Convert to our TypeScriptRoute format
                    return [
                        TypeScriptRoute(
                            method=route.method,
                            path=route.path,
                            framework=route.framework,
                            handler_name=route.handler_name,
                        )
                        for route in ts_routes
                    ]
            except Exception:
                # Fall back to regex parsing
                pass

        # Regex fallback
        return self._extract_nextjs_pages_routes_regex(code, file_path)

    def _extract_nextjs_pages_routes_regex(
        self, code: str, file_path: str
    ) -> List[TypeScriptRoute]:
        """Extract Next.js Pages Router routes using regex (fallback)"""
        routes = []

        # Convert file path to route path
        # pages/api/contacts.ts -> /api/contacts
        route_path = file_path.replace("pages", "").replace(".ts", "").replace(".js", "")

        # Detect methods from req.method checks
        method_pattern = r"req\.method\s*===\s*['\"](\w+)['\"]"
        methods = re.findall(method_pattern, code)

        for method in methods:
            routes.append(
                TypeScriptRoute(
                    method=method, path=route_path, framework="nextjs-pages", handler_name="handler"
                )
            )

        return routes

    def extract_nextjs_app_routes(self, code: str, file_path: str) -> List[TypeScriptRoute]:
        """Extract Next.js App Router route handlers"""
        if self.use_tree_sitter and self.tree_sitter_parser:
            try:
                ast = self.tree_sitter_parser.parse(code)
                if ast:
                    ts_routes = self.tree_sitter_parser.extract_nextjs_app_routes(ast, file_path)
                    # Convert to our TypeScriptRoute format
                    return [
                        TypeScriptRoute(
                            method=route.method,
                            path=route.path,
                            framework=route.framework,
                            handler_name=route.handler_name,
                        )
                        for route in ts_routes
                    ]
            except Exception:
                # Fall back to regex parsing
                pass

        # Regex fallback
        return self._extract_nextjs_app_routes_regex(code, file_path)

    def _extract_nextjs_app_routes_regex(self, code: str, file_path: str) -> List[TypeScriptRoute]:
        """Extract Next.js App Router routes using regex (fallback)"""
        routes = []

        # app/api/contacts/route.ts -> /api/contacts
        route_path = file_path.replace("app", "").replace("/route.ts", "").replace("/route.js", "")

        # Detect exported HTTP method functions
        http_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        for method in http_methods:
            pattern = rf"export\s+async\s+function\s+{method}\s*\("
            if re.search(pattern, code):
                routes.append(
                    TypeScriptRoute(
                        method=method, path=route_path, framework="nextjs-app", handler_name=method
                    )
                )

        return routes

    def extract_server_actions(self, code: str) -> List[TypeScriptAction]:
        """Extract Next.js Server Actions"""
        if self.use_tree_sitter and self.tree_sitter_parser:
            try:
                ast = self.tree_sitter_parser.parse(code)
                if ast:
                    ts_actions = self.tree_sitter_parser.extract_server_actions(ast)
                    # Convert to our TypeScriptAction format
                    return [TypeScriptAction(name=action.name) for action in ts_actions]
            except Exception:
                # Fall back to regex parsing
                pass

        # Regex fallback
        return self._extract_server_actions_regex(code)

    def _extract_server_actions_regex(self, code: str) -> List[TypeScriptAction]:
        """Extract Next.js Server Actions using regex (fallback)"""
        actions = []

        # Check for 'use server' directive
        if "'use server'" not in code and '"use server"' not in code:
            return actions

        # Extract exported async functions
        function_pattern = r"export\s+async\s+function\s+(\w+)\s*\("

        for match in re.finditer(function_pattern, code):
            function_name = match.group(1)
            actions.append(TypeScriptAction(name=function_name))

        return actions
