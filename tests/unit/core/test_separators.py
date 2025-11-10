"""Test separator utility functions."""

from src.core.separators import join_with_composition, split_composition, strip_tenant_prefix


class TestStripTenantPrefix:
    """Test tenant prefix stripping utility."""

    def test_strip_tenant_prefix_basic(self):
        """Should strip tenant prefix correctly."""
        result = strip_tenant_prefix("acme-corp|warehouse.floor1", "acme-corp")
        assert result == "warehouse.floor1"

    def test_strip_tenant_prefix_no_prefix(self):
        """Should return original string if no prefix."""
        result = strip_tenant_prefix("no-prefix", "acme-corp")
        assert result == "no-prefix"

    def test_strip_tenant_prefix_partial_match(self):
        """Should not strip if tenant identifier doesn't match exactly."""
        result = strip_tenant_prefix("acme-corp|warehouse", "acme")
        assert result == "acme-corp|warehouse"

    def test_strip_tenant_prefix_empty_tenant(self):
        """Should handle empty tenant identifier."""
        result = strip_tenant_prefix("warehouse", "")
        assert result == "warehouse"


class TestJoinWithComposition:
    """Test composition joining utility."""

    def test_join_with_composition_basic(self):
        """Should join components with ring operator."""
        result = join_with_composition(["2025-Q1", "machine.child", "location.parent"])
        assert result == "2025-Q1∘machine.child∘location.parent"

    def test_join_with_composition_single_component(self):
        """Should handle single component."""
        result = join_with_composition(["single"])
        assert result == "single"

    def test_join_with_composition_empty_list(self):
        """Should handle empty list."""
        result = join_with_composition([])
        assert result == ""


class TestSplitComposition:
    """Test composition splitting utility."""

    def test_split_composition_basic(self):
        """Should split by ring operator."""
        result = split_composition("2025-Q1∘machine∘location")
        assert result == ["2025-Q1", "machine", "location"]

    def test_split_composition_single_component(self):
        """Should handle single component."""
        result = split_composition("single")
        assert result == ["single"]

    def test_split_composition_no_separator(self):
        """Should return whole string if no separator."""
        result = split_composition("no-separator")
        assert result == ["no-separator"]
