"""
TypeScript Parser - Extract routes and actions from TypeScript code

Supports:
- Express routes
- Fastify routes
- Next.js Pages Router (pages/api)
- Next.js App Router (app directory, route.ts)
- Next.js Server Actions
"""

from dataclasses import dataclass
from typing import List, Optional
import re


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

    def extract_routes(self, code: str) -> List[TypeScriptRoute]:
        """Extract Express/Fastify routes"""
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
