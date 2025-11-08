"""
Tests for DependencyResolver
"""

import pytest
from src.numbering.dependency_resolver import DependencyResolver


def test_dependency_resolver_creation():
    """Test creating a dependency resolver"""
    resolver = DependencyResolver()
    assert resolver is not None


def test_topological_sort_simple():
    """Test topological sort with simple dependencies"""
    resolver = DependencyResolver()

    # A depends on B, B depends on C
    resolver.add_dependency("A", "B")
    resolver.add_dependency("B", "C")

    order = resolver.resolve(["A", "B", "C"])
    assert order == ["C", "B", "A"]


def test_topological_sort_no_dependencies():
    """Test topological sort with no dependencies"""
    resolver = DependencyResolver()

    order = resolver.resolve(["A", "B", "C"])
    # Should maintain original order when no dependencies
    assert order == ["A", "B", "C"]


def test_circular_dependency_detection():
    """Test detection of circular dependencies"""
    resolver = DependencyResolver()

    resolver.add_dependency("A", "B")
    resolver.add_dependency("B", "C")
    resolver.add_dependency("C", "A")

    with pytest.raises(ValueError, match="Circular dependency detected"):
        resolver.resolve(["A", "B", "C"])


def test_partial_dependencies():
    """Test with some items having dependencies and others not"""
    resolver = DependencyResolver()

    resolver.add_dependency("X", "Y")  # X depends on Y
    # Z has no dependencies

    order = resolver.resolve(["X", "Y", "Z"])
    # Y and Z can be in either order, but X must come after Y
    assert order.index("X") > order.index("Y")
    assert set(order) == {"X", "Y", "Z"}
