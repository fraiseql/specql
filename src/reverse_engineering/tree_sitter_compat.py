"""Compatibility layer for tree-sitter language access.

This module provides a unified interface for accessing tree-sitter languages,
using py-tree-sitter-languages when available.
"""

from typing import Any, TYPE_CHECKING

# Try to import py-tree-sitter-languages (preferred)
try:
    from tree_sitter_languages import get_language, get_parser
    from tree_sitter import Language, Parser, Node

    HAS_TREE_SITTER = True

    # Create language accessors for backward compatibility
    def get_prisma_language() -> Language:
        """Get Prisma tree-sitter language."""
        return get_language('prisma')

    def get_prisma_parser() -> Parser:
        """Get Prisma tree-sitter parser."""
        return get_parser('prisma')

    def get_rust_language() -> Language:
        """Get Rust tree-sitter language."""
        return get_language('rust')

    def get_rust_parser() -> Parser:
        """Get Rust tree-sitter parser."""
        return get_parser('rust')

    def get_typescript_language() -> Language:
        """Get TypeScript tree-sitter language."""
        return get_language('typescript')

    def get_typescript_parser() -> Parser:
        """Get TypeScript tree-sitter parser."""
        return get_parser('typescript')

except ImportError:
    HAS_TREE_SITTER = False

    if not TYPE_CHECKING:
        # Create stub types and functions for when dependencies are missing
        Language = Any  # type: ignore
        Parser = Any  # type: ignore
        Node = Any  # type: ignore

        def get_prisma_language() -> Any:  # type: ignore
            raise ImportError(
                "py-tree-sitter-languages is not installed. "
                "Install it with: pip install 'specql[reverse]'"
            )

        def get_prisma_parser() -> Any:  # type: ignore
            raise ImportError(
                "py-tree-sitter-languages is not installed. "
                "Install it with: pip install 'specql[reverse]'"
            )

        def get_rust_language() -> Any:  # type: ignore
            raise ImportError(
                "py-tree-sitter-languages is not installed. "
                "Install it with: pip install 'specql[reverse]'"
            )

        def get_rust_parser() -> Any:  # type: ignore
            raise ImportError(
                "py-tree-sitter-languages is not installed. "
                "Install it with: pip install 'specql[reverse]'"
            )

        def get_typescript_language() -> Any:  # type: ignore
            raise ImportError(
                "py-tree-sitter-languages is not installed. "
                "Install it with: pip install 'specql[reverse]'"
            )

        def get_typescript_parser() -> Any:  # type: ignore
            raise ImportError(
                "py-tree-sitter-languages is not installed. "
                "Install it with: pip install 'specql[reverse]'"
            )


__all__ = [
    'HAS_TREE_SITTER',
    'Language',
    'Parser',
    'Node',
    'get_prisma_language',
    'get_prisma_parser',
    'get_rust_language',
    'get_rust_parser',
    'get_typescript_language',
    'get_typescript_parser',
]
