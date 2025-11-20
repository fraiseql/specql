"""
Tree-sitter-based Rust AST Parser

Replaces regex parsing with robust AST traversal for:
- Procedural macros
- Derive macros
- Complex generics
- Nested structures
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from utils.logger import get_logger

logger = get_logger(__name__)

# Conditional imports for optional dependencies
try:
    from .tree_sitter_compat import (
        HAS_TREE_SITTER,
        Language,
        Node,
        Parser,
        get_rust_language,
        get_rust_parser,
    )

    HAS_TREE_SITTER_RUST = HAS_TREE_SITTER
except ImportError:
    HAS_TREE_SITTER_RUST = False
    if not TYPE_CHECKING:
        # Create stub types for when the dependency is missing
        Language = Any  # type: ignore
        Parser = Any  # type: ignore
        Node = Any  # type: ignore
        get_rust_language = None  # type: ignore
        get_rust_parser = None  # type: ignore


@dataclass
class RustColumn:
    """Represents a Rust struct field or table column"""

    name: str
    type_name: str
    attributes: list[str] | None = None


@dataclass
class RustFunction:
    """Represents a Rust function"""

    name: str
    is_public: bool
    is_async: bool
    parameters: list[str]
    return_type: str | None


@dataclass
class RustRoute:
    """Represents a Rust web framework route."""

    method: str
    path: str
    handler: str
    framework: str
    is_async: bool = False
    parameters: list[dict] = field(default_factory=list)
    has_guard: bool = False


@dataclass
class RustMethod:
    """Represents a method in an impl block."""

    name: str
    is_async: bool = False
    parameters: list[str] = field(default_factory=list)
    return_type: str | None = None
    visibility: str | None = None


@dataclass
class RustImplBlock:
    """Represents an impl block."""

    target_type: str
    trait_name: str | None = None
    methods: list[RustMethod] = field(default_factory=list)
    generics: str | None = None


@dataclass
class RustStruct:
    """Represents a Rust struct"""

    name: str
    is_public: bool
    derives: list[str]
    attributes: dict
    fields: list[RustColumn]


class TreeSitterRustParser:
    """Tree-sitter based Rust parser"""

    def __init__(self):
        """Initialize tree-sitter parser with Rust grammar"""
        if not HAS_TREE_SITTER_RUST:
            raise ImportError(
                "tree-sitter-rust is required for Rust parsing. "
                "Install with: pip install specql[reverse]"
            )
        self.language = get_rust_language()
        self.parser = get_rust_parser()

    def parse(self, code: str) -> Node | None:
        """Parse Rust code into AST"""
        try:
            tree = self.parser.parse(bytes(code, "utf8"))
            return tree.root_node
        except Exception as e:
            logger.error(f"Parse error: {e}", exc_info=True)
            return None

    def extract_table_name(self, ast: Node) -> str | None:
        """Extract table name from diesel::table! macro"""
        # Find macro invocation node
        macro_node = self._find_node_by_type(ast, "macro_invocation")
        if not macro_node:
            return None

        # Check if this is a diesel::table! macro
        scoped_id = self._find_node_by_type(macro_node, "scoped_identifier")
        if not scoped_id:
            return None

        # Check if the macro name is "table"
        macro_name = self._get_macro_name_from_scoped_id(scoped_id)
        if macro_name != "table":
            return None

        # Extract table name (first identifier in macro body after scoped_identifier)
        token_tree = self._find_node_by_type(macro_node, "token_tree")
        if token_tree:
            # Find the first identifier in the token tree (should be table name)
            for child in token_tree.children:
                if child.type == "identifier":
                    return self._node_text(child)

        return None

    def extract_columns(self, ast: Node) -> list[RustColumn]:
        """Extract columns from diesel::table! macro"""
        columns = []
        macro_node = self._find_node_by_type(ast, "macro_invocation")
        if not macro_node:
            return columns

        # Find the main token_tree of the macro
        main_token_tree = self._find_node_by_type(macro_node, "token_tree")
        if not main_token_tree:
            return columns

        # Find all nested token_trees - the column definitions are in the one with field declarations
        nested_token_trees = []
        for child in main_token_tree.children:
            if child.type == "token_tree":
                nested_token_trees.append(child)

        # The column definitions should be in the last nested token_tree
        # (after the primary key specification)
        if nested_token_trees:
            column_tree = nested_token_trees[-1]  # Last one should have the columns
            self._parse_column_definitions(column_tree, columns)

        return columns

    def extract_functions(self, ast: Node) -> list[RustFunction]:
        """Extract all function definitions from AST"""
        functions = []

        function_nodes = self._find_nodes_by_type(ast, "function_item")

        for func_node in function_nodes:
            # Extract function name
            name_node = func_node.child_by_field_name("name")
            if not name_node:
                continue
            name = self._node_text(name_node)

            # Check visibility (pub)
            is_public = any(child.type == "visibility_modifier" for child in func_node.children)

            # Check async
            is_async = any(self._node_text(child) == "async" for child in func_node.children)

            # Extract parameters
            params = []
            params_node = func_node.child_by_field_name("parameters")
            if params_node:
                for param in params_node.children:
                    if param.type == "parameter":
                        pattern = param.child_by_field_name("pattern")
                        if pattern:
                            params.append(self._node_text(pattern))

            # Extract return type
            return_type = None
            return_node = func_node.child_by_field_name("return_type")
            if return_node:
                return_type = self._node_text(return_node)

            functions.append(
                RustFunction(
                    name=name,
                    is_public=is_public,
                    is_async=is_async,
                    parameters=params,
                    return_type=return_type,
                )
            )

        return functions

    def extract_structs(self, ast: Node) -> list[RustStruct]:
        """Extract struct definitions with derive macros"""
        structs = []

        struct_nodes = self._find_nodes_by_type(ast, "struct_item")

        for struct_node in struct_nodes:
            # Extract struct name
            name_node = struct_node.child_by_field_name("name")
            if not name_node:
                continue
            name = self._node_text(name_node)

            # Check visibility
            is_public = any(child.type == "visibility_modifier" for child in struct_node.children)

            # Extract attributes and derives
            derives = []
            attributes = {}

            # Look for attribute macros above struct
            prev_sibling = struct_node.prev_sibling
            while prev_sibling and prev_sibling.type == "attribute_item":
                attr_text = self._node_text(prev_sibling)

                # Extract derive macros
                if "derive(" in attr_text:
                    derive_match = re.search(r"derive\(([^)]+)\)", attr_text)
                    if derive_match:
                        derives = [d.strip() for d in derive_match.group(1).split(",")]

                # Extract diesel attributes
                if "diesel(" in attr_text:
                    diesel_match = re.search(r"diesel\((\w+)\s*=\s*(\w+)\)", attr_text)
                    if diesel_match:
                        key, value = diesel_match.groups()
                        attributes[key] = value

                prev_sibling = prev_sibling.prev_sibling

            # Extract fields
            fields = []
            field_list = struct_node.child_by_field_name("body")
            if field_list:
                for field in self._find_nodes_by_type(field_list, "field_declaration"):
                    field_name_node = field.child_by_field_name("name")
                    field_type_node = field.child_by_field_name("type")
                    if field_name_node and field_type_node:
                        fields.append(
                            RustColumn(
                                name=self._node_text(field_name_node),
                                type_name=self._node_text(field_type_node),
                            )
                        )

            structs.append(
                RustStruct(
                    name=name,
                    is_public=is_public,
                    derives=derives,
                    attributes=attributes,
                    fields=fields,
                )
            )

        return structs

    def extract_routes(self, ast: Node) -> list[RustRoute]:
        """Extract web framework routes from AST.

        Supports: Actix, Rocket, Axum, Warp, Tide
        """
        routes = []

        # Extract attribute-based routes (Actix, Rocket)
        for fn_node in self._find_all(ast, "function_item"):
            route = self._extract_route_from_function(fn_node)
            if route:
                routes.append(route)

        # Extract configuration-based routes (Actix resource-based)
        config_routes = self._extract_actix_config_routes(ast)
        routes.extend(config_routes)

        # Extract method-based routes (Axum)
        axum_routes = self._extract_axum_routes(ast)
        routes.extend(axum_routes)

        # Extract Warp filter chains
        warp_routes = self._extract_warp_routes(ast)
        routes.extend(warp_routes)

        # Extract Tide routes
        tide_routes = self._extract_tide_routes(ast)
        routes.extend(tide_routes)

        return routes

    def _extract_actix_config_routes(self, ast: Node) -> list[RustRoute]:
        """Extract Actix routes from configuration code (web::resource, web::scope, etc.)"""
        routes = []

        # Check if file has guard-related code
        has_guards = self._file_has_guards(ast)

        # Use simple regex patterns for common Actix patterns
        source_text = self._get_node_text(ast)

        # Pattern for scope-based routes: web::scope("/api").service(web::scope("/v1").route("/contacts", web::post().to(handler)))
        import re

        # Pattern for resource-based routes: web::resource("/contacts").guard(...).route(web::post().to(handler))
        resource_pattern = r'web::resource\s*\(\s*"([^"]+)"\s*\)(.*?)\.route\s*\(\s*web::(\w+)\s*\(\s*\)\s*\.to\s*\(\s*([^)]+)\s*\)\s*\)'
        for match in re.finditer(resource_pattern, source_text, re.DOTALL):
            path = match.group(1)
            config_text = match.group(2)
            method = match.group(3).upper()
            handler = match.group(4)

            # Check if this resource has guards
            has_guard = ".guard(" in config_text

            routes.append(
                RustRoute(
                    method=method,
                    path=path,
                    handler=handler,
                    framework="actix",
                    is_async=True,
                    has_guard=has_guard,
                )
            )

        # Find all route calls within scope chains
        route_pattern = r'\.route\("([^"]+)"\s*,\s*web::(get|post|put|delete)\(\)\.to\(([^)]+)\)'
        for match in re.finditer(route_pattern, source_text):
            route_path = match.group(1)
            method = match.group(2).upper()
            handler = match.group(3)

            # Find the scope prefix by looking backwards for scope calls
            prefix = self._find_scope_prefix(source_text, match.start())
            full_path = f"{prefix}{route_path}"

            routes.append(
                RustRoute(
                    method=method,
                    path=full_path,
                    handler=handler,
                    framework="actix",
                    is_async=True,
                    has_guard=has_guards,
                )
            )

        return routes

    def _extract_axum_routes(self, ast: Node) -> list[RustRoute]:
        """Extract Axum routes from Router chains."""
        routes = []

        # Check if file has state-related code
        self._file_has_state(ast)

        # Use regex to find Router::new().route() chains
        source_text = self._get_node_text(ast)
        import re

        # Pattern for Router::new().route("/path", method(handler))
        route_pattern = r'\.route\("([^"]+)"\s*,\s*(?:axum::routing::|routing::)?(\w+)\(([^)]+)\)'
        for match in re.finditer(route_pattern, source_text):
            route_path = match.group(1)
            method = match.group(2).upper()
            handler = match.group(3)

            # Normalize Axum :param to {param}
            import re

            route_path = re.sub(r":(\w+)", r"{\1}", route_path)

            routes.append(
                RustRoute(
                    method=method,
                    path=route_path,
                    handler=handler,
                    framework="axum",
                    is_async=True,
                    has_guard=False,  # Axum uses state instead of guards
                    parameters=[],  # TODO: Could extract state parameters
                )
            )

        return routes

    def _extract_warp_routes(self, ast: Node) -> list[RustRoute]:
        """Extract Warp routes from filter chains."""
        routes = []

        source_text = self._get_node_text(ast)
        import re

        # Pattern for warp::path("route").and(warp::method()).and_then(handler)
        warp_pattern = (
            r'warp::path\("([^"]+)"\)[^}]*?\.and\(warp::(\w+)\(\)\)[^}]*?\.and_then\(([^)]+)\)'
        )
        for match in re.finditer(warp_pattern, source_text):
            route_path = match.group(1)
            method = match.group(2).upper()
            handler = match.group(3)

            # Warp paths are relative, add leading slash
            if not route_path.startswith("/"):
                route_path = "/" + route_path

            routes.append(
                RustRoute(
                    method=method,
                    path=route_path,
                    handler=handler,
                    framework="warp",
                    is_async=False,  # Warp handlers are typically not async in the same way
                    has_guard=False,
                    parameters=[],
                )
            )

        return routes

    def _extract_tide_routes(self, ast: Node) -> list[RustRoute]:
        """Extract Tide routes from .at() chains."""
        routes = []

        source_text = self._get_node_text(ast)
        import re

        # Pattern for app.at("/path").method(handler)
        tide_pattern = r'\.at\("([^"]+)"\)\.(\w+)\(([^)]+)\)'
        for match in re.finditer(tide_pattern, source_text):
            route_path = match.group(1)
            method = match.group(2).upper()
            handler = match.group(3)

            # Normalize Tide :param to {param}
            import re

            route_path = re.sub(r":(\w+)", r"{\1}", route_path)

            routes.append(
                RustRoute(
                    method=method,
                    path=route_path,
                    handler=handler,
                    framework="tide",
                    is_async=True,
                    has_guard=False,
                    parameters=[],
                )
            )

        return routes

    def _file_has_state(self, ast: Node) -> bool:
        """Check if the file contains state-related code."""
        source_text = self._get_node_text(ast)
        return "State" in source_text or "with_state" in source_text

    def _find_scope_prefix(self, source_text: str, route_start: int) -> str:
        """Find the scope prefix for a route by looking backwards."""
        # Look backwards from route_start to find scope calls
        search_text = source_text[:route_start]

        # Find all scope calls before this route
        scope_matches = list(re.finditer(r'web::scope\("([^"]+)"\)', search_text))

        # Build prefix from nested scopes (last two should be the relevant ones)
        prefix = ""
        if len(scope_matches) >= 2:
            scope1 = scope_matches[-2].group(1)
            scope2 = scope_matches[-1].group(1)
            prefix = f"{scope1}{scope2}"

        return prefix

    def _extract_scope_hierarchies(self, ast: Node) -> list[dict]:
        """Extract web::scope() hierarchies from the AST."""
        scopes = []

        call_exprs = self._find_all(ast, "call_expression")

        for call_expr in call_exprs:
            if self._is_actix_scope_call(call_expr):
                scope_info = self._parse_scope_hierarchy(call_expr)
                if scope_info:
                    scopes.append(scope_info)

        return scopes

    def _is_actix_scope_call(self, call_expr: Node) -> bool:
        """Check if call is web::scope()."""
        func_text = self._get_function_call_name(call_expr)
        return "scope" in func_text.lower()

    def _parse_scope_hierarchy(self, scope_call: Node, prefix: str = "") -> dict | None:
        """Parse a scope hierarchy recursively."""
        path = self._extract_string_literal(scope_call)
        if not path:
            return None

        full_path = prefix + path

        # Find nested services/routes
        services = []
        current = scope_call

        # Walk through the method chain
        while current:
            if current.type == "call_expression":
                # Look for .service() calls
                if self._is_service_method(current):
                    service_info = self._parse_service_call(current, full_path)
                    if service_info:
                        services.append(service_info)

            # Move to parent in chain
            if current.parent and current.parent.type == "call_expression":
                current = current.parent
            else:
                break

        return {"path": full_path, "services": services}

    def _is_service_method(self, call_expr: Node) -> bool:
        """Check if call is .service() method."""
        for child in call_expr.children:
            if child.type == "field_expression":
                text = self._get_node_text(child)
                if ".service" in text:
                    return True
        return False

    def _parse_service_call(self, service_call: Node, scope_prefix: str) -> dict | None:
        """Parse a .service() call which can contain scopes or resources."""
        # Extract the argument (should be a scope or resource call)
        for child in service_call.children:
            if child.type == "arguments":
                if child.children:
                    inner_call = child.children[0]
                    if inner_call.type == "call_expression":
                        if self._is_actix_scope_call(inner_call):
                            # Nested scope
                            return self._parse_scope_hierarchy(inner_call, scope_prefix)
                        elif self._is_actix_resource_call(inner_call):
                            # Resource with routes
                            return self._parse_resource_with_routes(inner_call, scope_prefix)

        return None

    def _parse_resource_with_routes(self, resource_call: Node, scope_prefix: str) -> dict | None:
        """Parse a resource call with its routes."""
        path = self._extract_string_literal(resource_call)
        if not path:
            return None

        full_path = scope_prefix + path
        routes = []

        # Find .route() calls in the chain
        current = resource_call
        while current:
            if current.type == "call_expression" and self._is_route_method(current):
                route_info = self._parse_route_call(current)
                if route_info:
                    routes.append(route_info)

            if current.parent and current.parent.type == "call_expression":
                current = current.parent
            else:
                break

        return {"path": full_path, "routes": routes}

    def _is_route_method(self, call_expr: Node) -> bool:
        """Check if call is .route() method."""
        for child in call_expr.children:
            if child.type == "field_expression":
                text = self._get_node_text(child)
                if ".route" in text:
                    return True
        return False

    def _parse_route_call(self, route_call: Node) -> dict | None:
        """Parse a .route(path, method.to(handler)) call."""
        # Extract arguments
        for child in route_call.children:
            if child.type == "arguments":
                args = [arg for arg in child.children if arg.type not in [",", "("]]
                if len(args) >= 2:
                    # First arg is path
                    path_arg = args[0]
                    route_path = self._extract_string_literal(path_arg) or ""

                    # Second arg is method chain
                    method_arg = args[1]
                    if method_arg.type == "call_expression":
                        method_info = self._parse_method_chain(method_arg)
                        if method_info:
                            return {
                                "path": route_path,
                                "method": method_info["method"],
                                "handler": method_info["handler"],
                            }

        return None

    def _parse_method_chain(self, method_call: Node) -> dict | None:
        """Parse web::get().to(handler) chain."""
        method = None
        handler = None

        # Extract method from web::get()
        func_text = self._get_function_call_name(method_call)
        if "get" in func_text.lower():
            method = "GET"
        elif "post" in func_text.lower():
            method = "POST"
        elif "put" in func_text.lower():
            method = "PUT"
        elif "delete" in func_text.lower():
            method = "DELETE"

        # Find .to(handler) in chain
        current = method_call
        while current:
            if current.type == "call_expression":
                if self._is_to_method(current):
                    for child in current.children:
                        if child.type == "arguments":
                            if child.children:
                                handler_node = child.children[0]
                                handler = self._get_node_text(handler_node)
                                break

            if current.parent and current.parent.type == "call_expression":
                current = current.parent
            else:
                break

        if method and handler:
            return {"method": method, "handler": handler}
        return None

    def _is_to_method(self, call_expr: Node) -> bool:
        """Check if call is .to() method."""
        for child in call_expr.children:
            if child.type == "field_expression":
                text = self._get_node_text(child)
                if ".to" in text:
                    return True
        return False

    def _build_routes_from_scopes(self, scopes: list[dict], has_guards: bool) -> list[RustRoute]:
        """Build RustRoute objects from parsed scope hierarchies."""
        routes = []

        def process_scope(scope: dict, prefix: str = ""):
            scope_path = scope.get("path", "")

            # Process direct routes in this scope
            for route in scope.get("routes", []):
                full_path = prefix + route["path"]
                routes.append(
                    RustRoute(
                        method=route["method"],
                        path=full_path,
                        handler=route["handler"],
                        framework="actix",
                        is_async=True,
                        has_guard=has_guards,
                    )
                )

            # Process nested scopes
            for service in scope.get("services", []):
                if "path" in service:  # It's a nested scope
                    process_scope(service, prefix + scope_path)
                elif "routes" in service:  # It's a resource with routes
                    for route in service["routes"]:
                        full_path = prefix + scope_path + route["path"]
                        routes.append(
                            RustRoute(
                                method=route["method"],
                                path=full_path,
                                handler=route["handler"],
                                framework="actix",
                                is_async=True,
                                has_guard=has_guards,
                            )
                        )

        for scope in scopes:
            process_scope(scope)

        return routes

    def _is_actix_resource_call(self, call_expr: Node) -> bool:
        """Check if call is web::resource()."""
        func_text = self._get_function_call_name(call_expr)
        return "resource" in func_text.lower()

    def _file_has_guards(self, ast: Node) -> bool:
        """Check if the file contains guard-related code."""
        source_text = self._get_node_text(ast)
        return "guard" in source_text.lower()

    def _find_handler_in_chain(self, resource_call: Node) -> str | None:
        """Find handler function name in the resource chain."""
        # Look for .to(handler) pattern in the source text
        source_text = self._get_node_text(resource_call)
        import re

        to_match = re.search(r"\.to\(([^)]+)\)", source_text)
        if to_match:
            return to_match.group(1)
        return None

    def _is_guard_method(self, call_expr: Node) -> bool:
        """Check if call is .guard() method."""
        for child in call_expr.children:
            if child.type == "field_expression":
                text = self._get_node_text(child)
                if ".guard" in text:
                    return True
        return False

    def _parse_actix_route(self, route_call: Node, base_path: str) -> RustRoute | None:
        """Parse .route(web::get().to(handler)) call."""
        method = None
        handler = None

        # Extract arguments: .route(web::get().to(handler))
        for child in route_call.children:
            if child.type == "arguments":
                for arg in child.children:
                    if arg.type == "call_expression":
                        # Parse web::get().to(handler)
                        method_call = arg
                        if self._is_http_method_call(method_call):
                            method = self._extract_http_method(method_call)
                            handler = self._extract_route_handler(method_call)

        if method and handler:
            return RustRoute(
                method=method,
                path=base_path,
                handler=handler,
                framework="actix",
                is_async=True,  # Assume async for Actix
                has_guard=self._has_guard_in_chain(route_call),
            )

        return None

    def _is_http_method_call(self, call_expr: Node) -> bool:
        """Check if call is web::get(), web::post(), etc."""
        func_text = self._get_function_call_name(call_expr)
        return any(
            method in func_text.lower() for method in ["get", "post", "put", "delete", "patch"]
        )

    def _extract_http_method(self, method_call: Node) -> str | None:
        """Extract HTTP method from web::get() call."""
        func_text = self._get_function_call_name(method_call)
        if "get" in func_text.lower():
            return "GET"
        elif "post" in func_text.lower():
            return "POST"
        elif "put" in func_text.lower():
            return "PUT"
        elif "delete" in func_text.lower():
            return "DELETE"
        elif "patch" in func_text.lower():
            return "PATCH"
        return None

    def _extract_route_handler(self, method_call: Node) -> str | None:
        """Extract handler from .to(handler) call."""
        # Look for chained .to() call
        parent = method_call.parent
        while parent:
            if parent.type == "call_expression":
                if self._is_to_method(parent):
                    for child in parent.children:
                        if child.type == "arguments":
                            # Extract handler name from .to(handler)
                            if child.children:
                                handler_node = child.children[0]
                                return self._get_node_text(handler_node)

            if parent.parent and parent.parent.type == "call_expression":
                parent = parent.parent
            else:
                break

        return None

    def _is_to_method(self, call_expr: Node) -> bool:
        """Check if call is .to() method."""
        for child in call_expr.children:
            if child.type == "field_expression":
                text = self._get_node_text(child)
                if ".to" in text:
                    return True
        return False

    def _has_guard_in_chain(self, route_call: Node) -> bool:
        """Check if the resource chain has guard calls."""
        # Walk up from route_call to find guard calls in the chain
        current = route_call
        while current:
            if current.type == "call_expression" and self._is_guard_method(current):
                return True

            if current.parent and current.parent.type == "call_expression":
                current = current.parent
            else:
                break

        return False

    def extract_impl_blocks(self, ast: Node) -> list[RustImplBlock]:
        """Extract impl blocks from AST."""
        impl_blocks = []

        for impl_node in self._find_all(ast, "impl_item"):
            impl_block = self._parse_impl_block(impl_node)
            if impl_block:
                impl_blocks.append(impl_block)

        return impl_blocks

    def _parse_impl_block(self, impl_node: Node) -> RustImplBlock | None:
        """Parse an impl block node."""
        target_type = None
        trait_name = None
        methods = []

        for child in impl_node.children:
            if child.type == "type_identifier":
                if target_type is None:
                    target_type = self._get_node_text(child)
                else:
                    # impl Trait for Type pattern
                    trait_name = target_type
                    target_type = self._get_node_text(child)

            elif child.type == "declaration_list":
                methods = self._extract_methods_from_body(child)

        if target_type:
            return RustImplBlock(target_type=target_type, trait_name=trait_name, methods=methods)

        return None

    def _extract_methods_from_body(self, body_node: Node) -> list[RustMethod]:
        """Extract methods from impl block body."""
        methods = []

        for child in body_node.children:
            if child.type == "function_item":
                method = self._parse_method(child)
                if method:
                    methods.append(method)

        return methods

    def _parse_method(self, fn_node: Node) -> RustMethod | None:
        """Parse a method definition."""
        name = self._get_function_name(fn_node)
        is_async = self._is_async_function(fn_node)
        visibility = self._get_visibility(fn_node)

        return RustMethod(name=name, is_async=is_async, visibility=visibility)

    def _extract_function_parameters(self, fn_node: Node) -> list[dict]:
        """Extract parameters from function signature."""
        parameters = []

        # Find parameters node
        for child in fn_node.children:
            if child.type == "parameters":
                for param_node in child.children:
                    if param_node.type == "parameter":
                        param_info = self._parse_parameter(param_node)
                        if param_info:
                            parameters.append(param_info)

        return parameters

    def _parse_parameter(self, param_node: Node) -> dict | None:
        """Parse a single parameter (name: Type)."""
        param_name = None
        param_type = None

        for child in param_node.children:
            if child.type == "identifier":
                param_name = self._get_node_text(child)
            elif child.type == "type_identifier" or child.type.endswith("_type"):
                param_type = self._get_node_text(child)

        if param_name and param_name not in ["self", "&self", "&mut self"]:
            return {"name": param_name, "type": param_type or "unknown"}

        return None

    def _has_guard_annotation(self, fn_node: Node) -> bool:
        """Check if function has guard-related code."""
        # Look for guard imports in parent scope
        # Or check for guard-related attributes
        attributes = self._get_attributes(fn_node)
        for attr in attributes:
            attr_text = self._get_node_text(attr)
            if "guard" in attr_text.lower():
                return True
        return False

    def _extract_route_from_function(self, fn_node: Node) -> RustRoute | None:
        """Extract route information from a function with attributes."""
        fn_name = self._get_function_name(fn_node)
        is_async = self._is_async_function(fn_node)
        attributes = self._get_attributes(fn_node)
        parameters = self._extract_function_parameters(fn_node)
        has_guard = self._has_guard_annotation(fn_node)

        for attr in attributes:
            route_info = self._parse_route_attribute(
                attr, normalize=False
            )  # Keep original framework syntax for routes
            if route_info:
                method, path, framework = route_info
                return RustRoute(
                    method=method,
                    path=path,
                    handler=fn_name,
                    framework=framework,
                    is_async=is_async,
                    parameters=parameters,
                    has_guard=has_guard,
                )

        return None

    def _parse_route_attribute(self, attr_node: Node, normalize: bool = False) -> tuple | None:
        """Parse route attribute from various frameworks."""
        attr_text = self._get_node_text(attr_node)
        http_methods = ["get", "post", "put", "delete", "patch", "head", "options"]

        for method in http_methods:
            if attr_text.startswith(f"#[{method}"):
                path = self._extract_string_literal(attr_node)
                if path:
                    framework = self._detect_framework_from_attribute(attr_node, path)
                    # Only normalize when explicitly requested (for endpoints)
                    if normalize and framework == "rocket":
                        path = self._normalize_rocket_path(path)
                    return (method.upper(), path, framework)

        return None

    def _normalize_rocket_path(self, path: str) -> str:
        """Convert Rocket's <param> syntax to standard {param} syntax."""
        import re

        # Replace <param> with {param}
        return re.sub(r"<(\w+)>", r"{\1}", path)

    def _detect_framework_from_attribute(self, attr_node: Node, path: str) -> str:
        """Detect web framework from attribute structure."""
        attr_text = self._get_node_text(attr_node)

        # Rocket indicators
        if "data = " in attr_text or "format = " in attr_text or "rank = " in attr_text:
            return "rocket"
        if "<" in path and ">" in path:  # Rocket uses <param>
            return "rocket"

        # Default to actix
        return "actix"

    def _get_function_name(self, fn_node: Node) -> str:
        """Extract function name from function_item node."""
        for child in fn_node.children:
            if child.type == "identifier":
                return self._get_node_text(child)
        return ""

    def _is_async_function(self, fn_node: Node) -> bool:
        """Check if function has 'async' keyword."""
        for child in fn_node.children:
            if child.type == "async" or self._get_node_text(child) == "async":
                return True
        return False

    def _get_visibility(self, node: Node) -> str | None:
        """Extract visibility modifier from node (pub, pub(crate), etc.)."""
        for child in node.children:
            if child.type == "visibility_modifier":
                text = self._get_node_text(child)
                # Only return "pub" for unrestricted public visibility
                # pub(crate), pub(super), etc. are considered restricted
                if text.strip() == "pub":
                    return "pub"
                elif "pub" in text:
                    return "pub(crate)"  # or other restricted visibility
                return "private"
        return None

    def _get_attributes(self, fn_node: Node) -> list[Node]:
        """Get all attribute nodes for a function."""
        attributes = []
        sibling = fn_node.prev_sibling

        while sibling and sibling.type in ["attribute_item", "line_comment", "block_comment"]:
            if sibling.type == "attribute_item":
                attributes.append(sibling)
            sibling = sibling.prev_sibling

        return attributes

    def _extract_string_literal(self, node: Node) -> str | None:
        """Extract string literal from node tree."""
        if node.type == "string_literal":
            text = self._get_node_text(node)
            return text.strip("\"'")

        for child in node.children:
            result = self._extract_string_literal(child)
            if result:
                return result

        return None

    def _find_all(self, node: Node, node_type: str) -> list[Node]:
        """Find all nodes of a specific type (alias for _find_nodes_by_type)."""
        return self._find_nodes_by_type(node, node_type)

    def _get_node_text(self, node: Node) -> str:
        """Get text content of a node."""
        return node.text.decode("utf8") if isinstance(node.text, bytes) else str(node.text)

    def _get_function_call_name(self, call_expr: Node) -> str:
        """Get the name of a function call (e.g., 'web::resource' from web::resource(...))."""
        for child in call_expr.children:
            if child.type in ["scoped_identifier", "field_expression", "identifier"]:
                return self._get_node_text(child)
        return ""

    def _parse_column_definitions(self, token_tree: Node, columns: list[RustColumn]):
        """Parse column definitions from a token_tree node (format: name -> Type)"""
        children = token_tree.children
        i = 0

        while i < len(children):
            # Skip opening brace and commas
            if children[i].type in ["{", ",", "}"]:
                i += 1
                continue

            # Look for field definition pattern: identifier -> identifier
            if (
                i + 2 < len(children)
                and children[i].type == "identifier"
                and children[i + 1].type == "->"
                and children[i + 2].type == "identifier"
            ):
                field_name = self._node_text(children[i])
                type_name = self._node_text(children[i + 2])
                columns.append(RustColumn(name=field_name, type_name=type_name))
                i += 3  # Skip the three tokens we processed
            else:
                i += 1

    def _find_node_by_type(self, node: Node, node_type: str) -> Node | None:
        """Recursively find first node of given type (depth-first search)"""
        if node.type == node_type:
            return node

        for child in node.children:
            result = self._find_node_by_type(child, node_type)
            if result:
                return result

        return None

    def _find_nodes_by_type(self, node: Node, node_type: str) -> list[Node]:
        """Recursively find all nodes of given type"""
        results = []
        if node.type == node_type:
            results.append(node)

        for child in node.children:
            results.extend(self._find_nodes_by_type(child, node_type))

        return results

    def _get_macro_name_from_scoped_id(self, scoped_id: Node) -> str:
        """Extract macro name from scoped_identifier (e.g., 'diesel::table' -> 'table')"""
        # Find all identifiers in the scoped identifier
        identifiers = []
        for child in scoped_id.children:
            if child.type == "identifier":
                identifiers.append(self._node_text(child))

        # Return the last identifier (the actual macro name)
        return identifiers[-1] if identifiers else ""

    def _get_macro_name(self, macro_node: Node) -> str:
        """Extract macro name from macro_invocation node"""
        # Get the macro path (e.g., "diesel::table")
        path_node = self._find_node_by_type(macro_node, "scoped_identifier")
        if path_node:
            return self._get_macro_name_from_scoped_id(path_node)

        # Simple macro name
        name_node = macro_node.child_by_field_name("macro")
        if name_node:
            return self._node_text(name_node)

        return ""

    def _node_text(self, node: Node) -> str:
        """Get text content of node"""
        return node.text.decode("utf8")
