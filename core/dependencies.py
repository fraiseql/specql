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

TREE_SITTER_RUST = OptionalDependency(
    package_name="tree_sitter_rust",
    pip_extra="reverse",
    purpose="Rust AST parsing",
)

TREE_SITTER_TYPESCRIPT = OptionalDependency(
    package_name="tree_sitter_typescript",
    pip_extra="reverse",
    purpose="TypeScript AST parsing",
)

TREE_SITTER_PRISMA = OptionalDependency(
    package_name="tree_sitter_prisma",
    pip_extra="reverse",
    purpose="Prisma schema parsing",
)
