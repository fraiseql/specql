"""
Table View File data structures

Data classes for representing individual tv_ table files.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TableViewFile:
    """
    Represents a single tv_ table file

    Contains all SQL components for one tv_ entity.
    """
    code: str  # 7-digit read-side code (e.g., "0220110")
    name: str  # View name (e.g., "tv_contact")
    content: str  # Complete SQL content for this file
    dependencies: List[str] = field(default_factory=list)  # List of view names this depends on