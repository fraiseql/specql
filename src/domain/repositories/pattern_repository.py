"""Pattern Repository Protocol"""
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.pattern import Pattern

class PatternRepository(Protocol):
    """Repository for Pattern aggregate root"""

    def get(self, pattern_name: str) -> "Pattern":
        """Get pattern by name - raises if not found"""
        ...

    def find_by_category(self, category: str) -> list["Pattern"]:
        """Find patterns by category"""
        ...

    def save(self, pattern: "Pattern") -> None:
        """Save pattern"""
        ...

    def list_all(self) -> list["Pattern"]:
        """List all patterns"""
        ...