"""Pattern Repository Protocol"""
from typing import Protocol
# from src.domain.entities.pattern import Pattern  # TODO: Create Pattern entity

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