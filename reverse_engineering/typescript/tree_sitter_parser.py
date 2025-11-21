"""
TypeScript AST parser using tree-sitter

Parses TypeScript source code into an AST for analysis
"""

from typing import TYPE_CHECKING, Any

# Conditional imports for optional dependencies
try:
    from ..tree_sitter_compat import (
        HAS_TREE_SITTER,
        Language,
        Node,
        Parser,
        get_typescript_language,
        get_typescript_parser,
    )

    HAS_TREE_SITTER_TYPESCRIPT = HAS_TREE_SITTER
except ImportError:
    HAS_TREE_SITTER_TYPESCRIPT = False
    if not TYPE_CHECKING:
        # Create stub types for when the dependency is missing
        Language = Any  # type: ignore
        Parser = Any  # type: ignore
        Node = Any  # type: ignore
        get_typescript_language = None  # type: ignore
        get_typescript_parser = None  # type: ignore


class TypeScriptParser:
    """Parse TypeScript source code using tree-sitter"""

    def __init__(self):
        """Initialize parser with TypeScript language"""
        if not HAS_TREE_SITTER_TYPESCRIPT:
            raise ImportError(
                "tree-sitter-language-pack is required for TypeScript parsing. "
                "Install with: pip install specql[reverse]"
            )
        # Load TypeScript grammar from language pack
        self.language = get_typescript_language()
        self.parser = get_typescript_parser()

    def parse(self, source_code: str) -> Node:
        """
        Parse TypeScript source into AST

        Args:
            source_code: TypeScript source code as string

        Returns:
            Root node of AST

        Example:
            >>> parser = TypeScriptParser()
            >>> ast = parser.parse("const x = 5;")
            >>> ast.type
            'program'
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
            node_type: Type of node to find (e.g., "call_expression")

        Returns:
            List of matching nodes

        Example:
            >>> calls = parser.find_nodes_by_type(ast, "call_expression")
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
