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
from dataclasses import dataclass


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
