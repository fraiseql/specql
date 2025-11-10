"""
Tests for ViewDependencyResolver - resolves dependencies between generated views.
"""

import pytest
from src.generators.schema.view_dependency import ViewDependencyResolver


class TestViewDependencyResolver:
    """Test the ViewDependencyResolver class."""

    def test_topological_sort_simple(self):
        """Test topological sort with simple dependencies."""
        patterns = [
            {"name": "v_base", "depends_on": []},
            {"name": "v_derived", "depends_on": ["v_base"]},
        ]

        resolver = ViewDependencyResolver()
        result = resolver.sort(patterns)

        assert result == ["v_base", "v_derived"]

    def test_topological_sort_complex(self):
        """Test topological sort with multiple levels of dependencies."""
        patterns = [
            {"name": "v_a", "depends_on": []},
            {"name": "v_b", "depends_on": ["v_a"]},
            {"name": "v_c", "depends_on": ["v_a"]},
            {"name": "v_d", "depends_on": ["v_b", "v_c"]},
        ]

        resolver = ViewDependencyResolver()
        result = resolver.sort(patterns)

        # v_a must come first
        assert result.index("v_a") == 0
        # v_b and v_c must come after v_a
        assert result.index("v_b") > result.index("v_a")
        assert result.index("v_c") > result.index("v_a")
        # v_d must come after v_b and v_c
        assert result.index("v_d") > result.index("v_b")
        assert result.index("v_d") > result.index("v_c")

    def test_topological_sort_circular_dependency(self):
        """Test that circular dependencies raise an error."""
        patterns = [
            {"name": "v_a", "depends_on": ["v_b"]},
            {"name": "v_b", "depends_on": ["v_a"]},
        ]

        resolver = ViewDependencyResolver()

        with pytest.raises(ValueError, match="Circular dependency detected"):
            resolver.sort(patterns)

    def test_topological_sort_missing_dependency(self):
        """Test that missing dependencies raise an error."""
        patterns = [
            {"name": "v_derived", "depends_on": ["v_missing"]},
        ]

        resolver = ViewDependencyResolver()

        with pytest.raises(ValueError, match="depends on unknown pattern"):
            resolver.sort(patterns)

    def test_validate_dependencies_valid(self):
        """Test validation of valid dependencies."""
        patterns = [
            {"name": "v_base", "depends_on": []},
            {"name": "v_derived", "depends_on": ["v_base"]},
        ]

        resolver = ViewDependencyResolver()
        errors = resolver.validate_dependencies(patterns)

        assert errors == []

    def test_validate_dependencies_circular(self):
        """Test validation detects circular dependencies."""
        patterns = [
            {"name": "v_a", "depends_on": ["v_b"]},
            {"name": "v_b", "depends_on": ["v_a"]},
        ]

        resolver = ViewDependencyResolver()
        errors = resolver.validate_dependencies(patterns)

        assert len(errors) == 1
        assert "Circular dependency detected" in errors[0]

    def test_validate_dependencies_missing(self):
        """Test validation detects missing dependencies."""
        patterns = [
            {"name": "v_derived", "depends_on": ["v_missing"]},
        ]

        resolver = ViewDependencyResolver()
        errors = resolver.validate_dependencies(patterns)

        assert len(errors) == 1
        assert "depends on unknown pattern" in errors[0]
