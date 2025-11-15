"""
Repository Pattern Implementation

Provides abstract base classes and protocols for data access.
"""

from typing import TypeVar, Generic, Protocol

T = TypeVar("T")


class Repository(Protocol, Generic[T]):
    """
    Generic repository protocol

    All concrete repositories should implement this protocol
    """

    def get(self, id: str) -> T:
        """Get entity by ID - raises if not found"""
        ...

    def find(self, id: str) -> T | None:
        """Find entity by ID - returns None if not found"""
        ...

    def save(self, entity: T) -> None:
        """Save entity (insert or update)"""
        ...

    def delete(self, id: str) -> None:
        """Delete entity by ID"""
        ...

    def list_all(self) -> list[T]:
        """List all entities"""
        ...
