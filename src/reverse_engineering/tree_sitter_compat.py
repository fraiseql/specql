"""Compatibility layer for tree-sitter language access.

This module provides a unified interface for accessing tree-sitter languages,
supporting multiple tree-sitter package variants with automatic fallback.

Fallback order (by priority):
1. Individual packages (most up-to-date grammars, e.g., Prisma v15)
2. tree-sitter-language-pack (actively maintained, 165+ languages, Prisma v13)
3. tree-sitter-languages (legacy, unmaintained)
"""

from typing import TYPE_CHECKING, Any

# Try individual tree-sitter packages first (Priority 1 - most up-to-date grammars)
try:
    import tree_sitter_prisma
    import tree_sitter_rust
    import tree_sitter_typescript
    from tree_sitter import Language, Node, Parser

    HAS_TREE_SITTER = True
    _USE_INDIVIDUAL_PACKAGES = True

    def get_prisma_language() -> Language:
        """Get Prisma tree-sitter language (v15)."""
        return Language(tree_sitter_prisma.language())

    def get_prisma_parser() -> Parser:
        """Get Prisma tree-sitter parser (v15)."""
        lang = get_prisma_language()
        return Parser(lang)

    def get_rust_language() -> Language:
        """Get Rust tree-sitter language."""
        return Language(tree_sitter_rust.language())

    def get_rust_parser() -> Parser:
        """Get Rust tree-sitter parser."""
        lang = get_rust_language()
        return Parser(lang)

    def get_typescript_language() -> Language:
        """Get TypeScript tree-sitter language."""
        return Language(tree_sitter_typescript.language_typescript())

    def get_typescript_parser() -> Parser:
        """Get TypeScript tree-sitter parser."""
        lang = get_typescript_language()
        return Parser(lang)

except ImportError:
    # Fallback 2: Try tree-sitter-language-pack (actively maintained, 165+ languages)
    _USE_INDIVIDUAL_PACKAGES = False
    try:
        from tree_sitter import Language, Node, Parser
        from tree_sitter_language_pack import get_language, get_parser

        HAS_TREE_SITTER = True
        _USE_TREE_SITTER_LANGUAGE_PACK = True

        def get_prisma_language() -> Language:
            """Get Prisma tree-sitter language (v13)."""
            return get_language('prisma')

        def get_prisma_parser() -> Parser:
            """Get Prisma tree-sitter parser (v13)."""
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
        # Fallback 3: Try tree-sitter-languages (legacy, unmaintained)
        _USE_TREE_SITTER_LANGUAGE_PACK = False
        try:
            from tree_sitter import Language, Node, Parser
            from tree_sitter_languages import get_language, get_parser

            HAS_TREE_SITTER = True
            _USE_TREE_SITTER_LANGUAGES = True

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
                        "No tree-sitter package found. "
                        "Install with: pip install tree-sitter-language-pack"
                    )

                def get_prisma_parser() -> Any:  # type: ignore
                    raise ImportError(
                        "No tree-sitter package found. "
                        "Install with: pip install tree-sitter-language-pack"
                    )

                def get_rust_language() -> Any:  # type: ignore
                    raise ImportError(
                        "No tree-sitter package found. "
                        "Install with: pip install tree-sitter-language-pack"
                    )

                def get_rust_parser() -> Any:  # type: ignore
                    raise ImportError(
                        "No tree-sitter package found. "
                        "Install with: pip install tree-sitter-language-pack"
                    )

                def get_typescript_language() -> Any:  # type: ignore
                    raise ImportError(
                        "No tree-sitter package found. "
                        "Install with: pip install tree-sitter-language-pack"
                    )

                def get_typescript_parser() -> Any:  # type: ignore
                    raise ImportError(
                        "No tree-sitter package found. "
                        "Install with: pip install tree-sitter-language-pack"
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
