"""Simplified tree-sitter compatibility layer using only tree-sitter-language-pack.

This module provides a unified interface for accessing tree-sitter languages
from the tree-sitter-language-pack package (165+ languages).

Supported languages:
- Prisma (v13)
- TypeScript (v14)
- Rust
"""

from typing import TYPE_CHECKING, Any

try:
    from tree_sitter import Language, Node, Parser
    from tree_sitter_language_pack import get_language, get_parser

    HAS_TREE_SITTER = True

    def get_prisma_language() -> Language:
        """Get Prisma tree-sitter language (v13)."""
        return get_language("prisma")

    def get_prisma_parser() -> Parser:
        """Get Prisma tree-sitter parser (v13)."""
        return get_parser("prisma")

    def get_rust_language() -> Language:
        """Get Rust tree-sitter language."""
        return get_language("rust")

    def get_rust_parser() -> Parser:
        """Get Rust tree-sitter parser."""
        return get_parser("rust")

    def get_typescript_language() -> Language:
        """Get TypeScript tree-sitter language (v14)."""
        return get_language("typescript")

    def get_typescript_parser() -> Parser:
        """Get TypeScript tree-sitter parser (v14)."""
        return get_parser("typescript")

except ImportError:
    HAS_TREE_SITTER = False

    if not TYPE_CHECKING:
        # Create stub types for when the dependency is missing
        Language = Any  # type: ignore
        Parser = Any  # type: ignore
        Node = Any  # type: ignore

        def get_prisma_language() -> Any:  # type: ignore
            raise ImportError(
                "tree-sitter-language-pack is required. "
                "Install with: pip install specql[reverse]"
            )

        def get_prisma_parser() -> Any:  # type: ignore
            raise ImportError(
                "tree-sitter-language-pack is required. "
                "Install with: pip install specql[reverse]"
            )

        def get_rust_language() -> Any:  # type: ignore
            raise ImportError(
                "tree-sitter-language-pack is required. "
                "Install with: pip install specql[reverse]"
            )

        def get_rust_parser() -> Any:  # type: ignore
            raise ImportError(
                "tree-sitter-language-pack is required. "
                "Install with: pip install specql[reverse]"
            )

        def get_typescript_language() -> Any:  # type: ignore
            raise ImportError(
                "tree-sitter-language-pack is required. "
                "Install with: pip install specql[reverse]"
            )

        def get_typescript_parser() -> Any:  # type: ignore
            raise ImportError(
                "tree-sitter-language-pack is required. "
                "Install with: pip install specql[reverse]"
            )


__all__ = [
    "HAS_TREE_SITTER",
    "Language",
    "Parser",
    "Node",
    "get_prisma_language",
    "get_prisma_parser",
    "get_rust_language",
    "get_rust_parser",
    "get_typescript_language",
    "get_typescript_parser",
]
