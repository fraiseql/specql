"""
Tree-sitter-based Rust AST Parser

Replaces regex parsing with robust AST traversal for:
- Procedural macros
- Derive macros
- Complex generics
- Nested structures
"""

from typing import Optional, List, Any
import re
import tree_sitter_rust as ts_rust
from tree_sitter import Language, Parser, Node
from dataclasses import dataclass, field


@dataclass
class RustColumn:
    """Represents a Rust struct field or table column"""

    name: str
    type_name: str
    attributes: Optional[List[str]] = None


@dataclass
class RustFunction:
    """Represents a Rust function"""

    name: str
    is_public: bool
    is_async: bool
    parameters: List[str]
    return_type: Optional[str]


@dataclass
class RustRoute:
    """Represents a Rust web framework route."""

    method: str
    path: str
    handler: str
    framework: str
    is_async: bool = False
    parameters: List[str] = field(default_factory=list)


@dataclass
class RustMethod:
    """Represents a method in an impl block."""

    name: str
    is_async: bool = False
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    visibility: Optional[str] = None


@dataclass
class RustImplBlock:
    """Represents an impl block."""

    target_type: str
    trait_name: Optional[str] = None
    methods: List[RustMethod] = field(default_factory=list)
    generics: Optional[str] = None


@dataclass
class RustStruct:
    """Represents a Rust struct"""

    name: str
    is_public: bool
    derives: List[str]
    attributes: dict
    fields: List[RustColumn]


class TreeSitterRustParser:
    """Tree-sitter based Rust parser"""

    def __init__(self):
        """Initialize tree-sitter parser with Rust grammar"""
        self.language = Language(ts_rust.language())
        self.parser = Parser(self.language)

    def parse(self, code: str) -> Optional[Node]:
        """Parse Rust code into AST"""
        try:
            tree = self.parser.parse(bytes(code, "utf8"))
            return tree.root_node
        except Exception as e:
            print(f"Parse error: {e}")
            return None

    def extract_table_name(self, ast: Node) -> Optional[str]:
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

    def extract_columns(self, ast: Node) -> List[RustColumn]:
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

    def extract_functions(self, ast: Node) -> List[RustFunction]:
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

    def extract_structs(self, ast: Node) -> List[RustStruct]:
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

    def extract_routes(self, ast: Node) -> List[RustRoute]:
        """
        Extract web framework routes from AST.

        Supports: Actix, Rocket, Axum, Warp, Tide
        """
        routes = []

        # Extract attribute-based routes (Actix, Rocket)
        for fn_node in self._find_all(ast, "function_item"):
            route = self._extract_route_from_function(fn_node)
            if route:
                routes.append(route)

        # Extract method-based routes (Axum)
        axum_routes = self._extract_axum_routes(ast)
        routes.extend(axum_routes)

        return routes

    def extract_impl_blocks(self, ast: Node) -> List[RustImplBlock]:
        """Extract impl blocks from AST."""
        impl_blocks = []

        for impl_node in self._find_all(ast, "impl_item"):
            impl_block = self._parse_impl_block(impl_node)
            if impl_block:
                impl_blocks.append(impl_block)

        return impl_blocks

    def _parse_impl_block(self, impl_node: Node) -> Optional[RustImplBlock]:
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

    def _extract_methods_from_body(self, body_node: Node) -> List[RustMethod]:
        """Extract methods from impl block body."""
        methods = []

        for child in body_node.children:
            if child.type == "function_item":
                method = self._parse_method(child)
                if method:
                    methods.append(method)

        return methods

    def _parse_method(self, fn_node: Node) -> Optional[RustMethod]:
        """Parse a method definition."""
        name = self._get_function_name(fn_node)
        is_async = self._is_async_function(fn_node)
        visibility = self._get_visibility(fn_node)

        return RustMethod(name=name, is_async=is_async, visibility=visibility)

    def _extract_route_from_function(self, fn_node: Node) -> Optional[RustRoute]:
        """Extract route information from a function with attributes."""
        fn_name = self._get_function_name(fn_node)
        is_async = self._is_async_function(fn_node)
        attributes = self._get_attributes(fn_node)

        for attr in attributes:
            route_info = self._parse_route_attribute(attr)
            if route_info:
                method, path, framework = route_info
                return RustRoute(
                    method=method,
                    path=path,
                    handler=fn_name,
                    framework=framework,
                    is_async=is_async,
                )

        return None

    def _extract_axum_routes(self, ast: Node) -> List[RustRoute]:
        """Extract Axum routes from Router method chains."""
        routes = []

        # Find Router::new().route()... chains
        call_exprs = self._find_all(ast, "call_expression")

        for call_expr in call_exprs:
            route = self._extract_axum_route_from_call(call_expr)
            if route:
                routes.append(route)

        return routes

    def _extract_axum_route_from_call(self, call_expr: Node) -> Optional[RustRoute]:
        """Extract route from Axum Router::route() call."""
        # Look for .route(path, method(handler)) pattern
        if not self._is_axum_route_call(call_expr):
            return None

        # Extract path from first argument
        args = self._get_call_arguments(call_expr)
        if len(args) < 2:
            return None

        path_arg = args[0]
        method_arg = args[1]

        path = self._extract_string_from_expression(path_arg)
        method, handler = self._extract_axum_method_and_handler(method_arg)

        if path and method and handler:
            return RustRoute(
                method=method,
                path=path,
                handler=handler,
                framework="axum",
                is_async=True,  # Axum handlers are typically async
            )

        return None

    def _is_axum_route_call(self, call_expr: Node) -> bool:
        """Check if this is a Router.route() call."""
        # Look for field_expression like router.route
        field_expr = self._find_node_by_type(call_expr, "field_expression")
        if field_expr:
            field_name = self._find_node_by_type(field_expr, "field_identifier")
            if field_name and self._get_node_text(field_name) == "route":
                return True
        return False

    def _get_call_arguments(self, call_expr: Node) -> List[Node]:
        """Get arguments from a call expression."""
        args = []
        arguments = self._find_node_by_type(call_expr, "arguments")
        if arguments:
            for child in arguments.children:
                if child.type not in ["(", ")", ","]:
                    args.append(child)
        return args

    def _extract_string_from_expression(self, expr: Node) -> Optional[str]:
        """Extract string literal from expression."""
        string_lit = self._find_node_by_type(expr, "string_literal")
        if string_lit:
            text = self._get_node_text(string_lit)
            return text.strip("\"'")

        # Handle &"string" pattern
        if expr.type == "reference_expression":
            for child in expr.children:
                if child.type == "string_literal":
                    text = self._get_node_text(child)
                    return text.strip("\"'")

        return None

    def _extract_axum_method_and_handler(self, method_expr: Node) -> tuple:
        """Extract HTTP method and handler from Axum method call."""
        # Look for get(handler), post(handler), etc.
        if method_expr.type == "call_expression":
            # Get the method name (get, post, etc.)
            method_name_node = self._find_node_by_type(method_expr, "identifier")
            if method_name_node:
                method_name = self._get_node_text(method_name_node)
                if method_name in ["get", "post", "put", "delete", "patch", "head"]:
                    # Get handler from arguments
                    args = self._get_call_arguments(method_expr)
                    if args:
                        handler = self._extract_handler_name(args[0])
                        return (method_name.upper(), handler)

        return (None, None)

    def _extract_handler_name(self, expr: Node) -> Optional[str]:
        """Extract function name from handler expression."""
        # Direct function identifier
        if expr.type == "identifier":
            return self._get_node_text(expr)

        # Scoped identifier (module::function)
        if expr.type == "scoped_identifier":
            identifiers = []
            for child in expr.children:
                if child.type == "identifier":
                    identifiers.append(self._get_node_text(child))
            return identifiers[-1] if identifiers else None

        return None

    def _parse_route_attribute(self, attr_node: Node) -> Optional[tuple]:
        """Parse route attribute from various frameworks."""
        attr_text = self._get_node_text(attr_node)
        http_methods = ["get", "post", "put", "delete", "patch", "head", "options"]

        for method in http_methods:
            if attr_text.startswith(f"#[{method}"):
                path = self._extract_string_literal(attr_node)
                if path:
                    framework = self._detect_framework_from_attribute(attr_node, path)
                    # Normalize Rocket's <param> to standard {param}
                    if framework == "rocket":
                        path = self._normalize_rocket_path(path)
                    return (method.upper(), path, framework)

        return None

    def _normalize_rocket_path(self, path: str) -> str:
        """Convert Rocket's <param> syntax to standard {param} syntax."""
        import re
        # Replace <param> with {param}
        return re.sub(r'<(\w+)>', r'{\1}', path)

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

    def _get_visibility(self, node: Node) -> Optional[str]:
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

    def _get_attributes(self, fn_node: Node) -> List[Node]:
        """Get all attribute nodes for a function."""
        attributes = []
        sibling = fn_node.prev_sibling

        while sibling and sibling.type in ["attribute_item", "line_comment", "block_comment"]:
            if sibling.type == "attribute_item":
                attributes.append(sibling)
            sibling = sibling.prev_sibling

        return attributes

    def _extract_string_literal(self, node: Node) -> Optional[str]:
        """Extract string literal from node tree."""
        if node.type == "string_literal":
            text = self._get_node_text(node)
            return text.strip("\"'")

        for child in node.children:
            result = self._extract_string_literal(child)
            if result:
                return result

        return None

    def _find_all(self, node: Node, node_type: str) -> List[Node]:
        """Find all nodes of a specific type (alias for _find_nodes_by_type)."""
        return self._find_nodes_by_type(node, node_type)

    def _get_node_text(self, node: Node) -> str:
        """Get text content of a node."""
        return node.text.decode("utf8") if isinstance(node.text, bytes) else str(node.text)

    def _parse_column_definitions(self, token_tree: Node, columns: List[RustColumn]):
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

    def _find_node_by_type(self, node: Node, node_type: str) -> Optional[Node]:
        """Recursively find first node of given type (depth-first search)"""
        if node.type == node_type:
            return node

        for child in node.children:
            result = self._find_node_by_type(child, node_type)
            if result:
                return result

        return None

    def _find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
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
