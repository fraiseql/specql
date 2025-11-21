"""Utility for checking optional dependencies."""

import importlib.util


class OptionalDependency:
    """Check if an optional dependency is available."""

    def __init__(self, package_name: str, pip_extra: str, purpose: str):
        self.package_name = package_name
        self.pip_extra = pip_extra
        self.purpose = purpose
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        """Check if dependency is installed."""
        if self._available is None:
            self._available = importlib.util.find_spec(self.package_name) is not None
        return self._available

    def require(self) -> None:
        """Raise helpful error if dependency not available."""
        if not self.available:
            raise ImportError(
                f"\n{self.purpose} requires {self.package_name}.\n"
                f"Install with: pip install specql[{self.pip_extra}]\n"
            )


# Define optional dependencies
PGLAST = OptionalDependency(
    package_name="pglast",
    pip_extra="reverse",
    purpose="SQL parsing for reverse engineering",
)

FAKER = OptionalDependency(
    package_name="faker",
    pip_extra="testing",
    purpose="Test data generation",
)

TREE_SITTER = OptionalDependency(
    package_name="tree_sitter",
    pip_extra="reverse",
    purpose="Multi-language AST parsing",
)

class TreeSitterLanguagePackRust(OptionalDependency):
    """Check for Rust support via tree-sitter-language-pack."""

    def __init__(self):
        super().__init__(
            package_name="tree_sitter_language_pack",
            pip_extra="reverse",
            purpose="Rust AST parsing"
        )

    @property
    def available(self) -> bool:
        """Check if Rust is available via language-pack."""
        if self._available is None:
            try:
                from tree_sitter_language_pack import get_language
                # Verify Rust is available
                get_language("rust")
                self._available = True
            except (ImportError, Exception):
                self._available = False
        return self._available

TREE_SITTER_RUST = TreeSitterLanguagePackRust()

class TreeSitterLanguagePackTypeScript(OptionalDependency):
    """Check for TypeScript support via tree-sitter-language-pack."""

    def __init__(self):
        super().__init__(
            package_name="tree_sitter_language_pack",
            pip_extra="reverse",
            purpose="TypeScript AST parsing"
        )

    @property
    def available(self) -> bool:
        """Check if TypeScript is available via language-pack."""
        if self._available is None:
            try:
                from tree_sitter_language_pack import get_language
                # Verify TypeScript is available
                get_language("typescript")
                self._available = True
            except (ImportError, Exception):
                self._available = False
        return self._available

TREE_SITTER_TYPESCRIPT = TreeSitterLanguagePackTypeScript()


class TreeSitterLanguagePackPrisma(OptionalDependency):
    """Check for Prisma support via tree-sitter-language-pack."""

    def __init__(self):
        super().__init__(
            package_name="tree_sitter_language_pack",
            pip_extra="reverse",
            purpose="Prisma schema parsing"
        )

    @property
    def available(self) -> bool:
        """Check if Prisma is available via language-pack."""
        if self._available is None:
            try:
                from tree_sitter_language_pack import get_language
                # Verify Prisma is available
                get_language("prisma")
                self._available = True
            except (ImportError, Exception):
                self._available = False
        return self._available

TREE_SITTER_PRISMA = TreeSitterLanguagePackPrisma()
