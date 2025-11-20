"""
FraiseQL compatibility layer
Verifies that SpecQL types work with FraiseQL autodiscovery
"""

from .compatibility_checker import CompatibilityChecker
from .mutation_annotator import MutationAnnotator
from .table_view_annotator import TableViewAnnotator

__all__ = ["CompatibilityChecker", "TableViewAnnotator", "MutationAnnotator"]
