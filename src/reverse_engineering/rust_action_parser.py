"""
Rust Action Parser for SpecQL

Parses Rust impl blocks, route handlers, and enum types to extract actions.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

# from src.core.ast_models import Action  # Using dict for now
from src.reverse_engineering.rust_parser import (
    RustParser,
    DieselDeriveInfo,
    ImplMethodInfo,
    RouteHandlerInfo,
)

logger = logging.getLogger(__name__)


class RustActionParser:
    """Extract actions from Rust impl blocks and route handlers."""

    def __init__(self):
        self.rust_parser = RustParser()
        self.action_mapper = RustActionMapper()
        self.route_mapper = RouteToActionMapper()

    def extract_actions(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract SpecQL actions from Rust file."""
        # Parse file
        structs, enums, diesel_tables, diesel_derives, impl_blocks, route_handlers = (
            self.rust_parser.parse_file(file_path)
        )

        actions = []

        # Map impl blocks to actions
        for impl_block in impl_blocks:
            for method in impl_block.methods:
                action = self.action_mapper.map_method_to_action(method)
                if action:
                    actions.append(action)

        # Map route handlers to actions
        for route_handler in route_handlers:
            action = self.route_mapper.map_route_to_action(route_handler)
            if action:
                actions.append(action)

        return actions

    def extract_endpoints(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract API endpoints from route handlers."""
        structs, enums, diesel_tables, diesel_derives, impl_blocks, route_handlers = (
            self.rust_parser.parse_file(file_path)
        )

        endpoints = []
        for route_handler in route_handlers:
            endpoint = self.route_mapper.map_route_to_endpoint(route_handler)
            if endpoint:
                endpoints.append(endpoint)

        return endpoints


class RustActionMapper:
    """Maps Rust constructs to SpecQL actions."""

    def map_method_to_action(self, method: ImplMethodInfo) -> Optional[Dict[str, Any]]:
        """Map impl method to SpecQL action."""
        # Only map public methods
        if method.visibility != "pub":
            return None

        # Detect CRUD pattern from method name
        action_type = self._detect_crud_pattern(method.name)

        if action_type:
            return {
                "name": method.name,
                "type": action_type,
                "parameters": self._map_parameters(method.parameters),
                "return_type": method.return_type,
                "is_async": method.is_async,
            }
        return None

    def _detect_crud_pattern(self, method_name: str) -> Optional[str]:
        """Detect CRUD pattern from method name."""
        import re

        # Check for CRUD keywords with proper word boundaries
        crud_keywords = {
            "create": ["create", "insert", "add", "new", "save"],
            "read": ["get", "find", "read", "select", "fetch", "retrieve", "query"],
            "update": ["update", "modify", "edit", "change", "set"],
            "delete": ["delete", "remove", "destroy", "erase"],
        }

        for action_type, keywords in crud_keywords.items():
            for keyword in keywords:
                # Check for camelCase: keyword followed by uppercase
                # Look for pattern like "createUser", "getData", etc.
                camel_pattern = re.compile(
                    r"\b" + re.escape(keyword) + r"(?-i:[A-Z])", re.IGNORECASE
                )
                if camel_pattern.search(method_name):
                    return action_type

                # Check for keyword at start of method name
                if method_name.lower().startswith(keyword):
                    # Check if it's followed by valid boundary (end, underscore, or uppercase)
                    remaining = method_name[len(keyword) :]
                    if not remaining or remaining[0] == "_" or remaining[0].isupper():
                        return action_type

                # Check for keyword after underscore
                underscore_pattern = f"_{keyword}"
                if underscore_pattern in method_name.lower():
                    # Find the position and check boundary
                    pos = method_name.lower().find(underscore_pattern)
                    if pos >= 0:
                        remaining = method_name[pos + len(underscore_pattern) :]
                        if (
                            not remaining
                            or remaining[0] == "_"
                            or remaining[0].isupper()
                        ):
                            return action_type

        return "custom"

    def _map_parameters(self, parameters: List[dict]) -> List[dict]:
        """Map method parameters to action parameters."""
        mapped_params = []
        for param in parameters:
            if param["name"] != "self":  # Skip self parameter
                mapped_params.append(
                    {
                        "name": param["name"],
                        "type": param["param_type"],
                    }
                )
        return mapped_params

    def map_diesel_derive_to_action(
        self, derive: DieselDeriveInfo
    ) -> Optional[Dict[str, Any]]:
        """Map Diesel derive to SpecQL action."""
        # TODO: Implement mapping logic
        return None


class RouteToActionMapper:
    """Maps route handlers to SpecQL actions and endpoints."""

    def map_route_to_action(
        self, route_handler: RouteHandlerInfo
    ) -> Optional[Dict[str, Any]]:
        """Map route handler to SpecQL action."""
        # Map HTTP methods to CRUD actions
        method_to_action = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "DELETE": "delete",
            "PATCH": "update",
        }

        action_type = method_to_action.get(route_handler.method)
        if not action_type:
            return None

        return {
            "name": route_handler.function_name,
            "type": action_type,
            "parameters": route_handler.parameters,
            "return_type": route_handler.return_type,
            "is_async": route_handler.is_async,
            "http_method": route_handler.method,
            "path": route_handler.path,
        }

    def map_route_to_endpoint(
        self, route_handler: RouteHandlerInfo
    ) -> Optional[Dict[str, Any]]:
        """Map route handler to SpecQL endpoint."""
        return {
            "method": route_handler.method,
            "path": route_handler.path,
            "handler": route_handler.function_name,
            "is_async": route_handler.is_async,
            "return_type": route_handler.return_type,
            "parameters": route_handler.parameters,
        }
