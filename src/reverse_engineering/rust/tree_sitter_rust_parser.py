"""
Rust AST parser using tree-sitter

Parses Rust source code into an AST for route extraction
"""

from typing import Optional
import tree_sitter_rust as ts_rust
from tree_sitter import Language, Parser, Node


class RustParser:
    """Parse Rust source code using tree-sitter"""

    def __init__(self):
        """Initialize parser with Rust language"""
        # Load Rust grammar
        self.language = Language(ts_rust.language())
        self.parser = Parser(self.language)

    def parse(self, source_code: str) -> Node:
        """
        Parse Rust source into AST

        Args:
            source_code: Rust source code as string

        Returns:
            Root node of AST

        Example:
            >>> parser = RustParser()
            >>> ast = parser.parse("fn main() {}")
            >>> ast.type
            'source_file'
        """
        # Encode to bytes (tree-sitter requirement)
        source_bytes = bytes(source_code, "utf8")

        # Parse and return root node
        tree = self.parser.parse(source_bytes)
        return tree.root_node

    def walk_tree(self, node: Node):
        """
        Recursively walk AST nodes

        Yields each node in depth-first order

        Example:
            >>> for node in parser.walk_tree(ast):
            ...     print(node.type)
        """
        yield node
        for child in node.children:
            yield from self.walk_tree(child)

    def find_nodes_by_type(self, root: Node, node_type: str) -> list[Node]:
        """
        Find all nodes of specific type

        Args:
            root: Root node to search from
            node_type: Type of node to find (e.g., "attribute_item")

        Returns:
            List of matching nodes

        Example:
            >>> attrs = parser.find_nodes_by_type(ast, "attribute_item")
        """
        return [node for node in self.walk_tree(root) if node.type == node_type]

    def get_node_text(self, node: Node, source_code: str) -> str:
        """
        Get source text for a node

        Args:
            node: AST node
            source_code: Original source code

        Returns:
            Text content of the node
        """
        return source_code[node.start_byte : node.end_byte]
