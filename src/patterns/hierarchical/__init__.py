"""Hierarchical query patterns for SpecQL."""

from .flattener import generate_hierarchical_flattener
from .path_expander import generate_path_expander

__all__ = [
    "generate_hierarchical_flattener",
    "generate_path_expander",
]
