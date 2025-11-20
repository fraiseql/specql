"""Test separator constants and utilities."""

from core.separators import Separators


class TestSeparatorConstants:
    """Test separator constant definitions."""

    def test_tenant_separator_is_pipe(self):
        """Tenant separator should be pipe."""
        assert Separators.TENANT == "|"

    def test_hierarchy_separator_is_dot(self):
        """Hierarchy separator should be dot (NEW default)."""
        assert Separators.HIERARCHY == "."

    def test_composition_separator_is_ring(self):
        """Composition separator should be ring operator."""
        assert Separators.COMPOSITION == "∘"

    def test_internal_separator_is_em_dash(self):
        """Internal separator should be em dash."""
        assert Separators.INTERNAL == "—"

    def test_deduplication_suffix_is_hash(self):
        """Deduplication suffix should be hash."""
        assert Separators.DEDUPLICATION == "#"

    def test_ordering_separator_is_dash(self):
        """Ordering separator should be dash."""
        assert Separators.ORDERING == "-"

    def test_all_separators_unique(self):
        """All separators should be unique characters."""
        separators = [
            Separators.TENANT,
            Separators.HIERARCHY,
            Separators.COMPOSITION,
            Separators.INTERNAL,
            Separators.DEDUPLICATION,
            Separators.ORDERING,
        ]
        assert len(separators) == len(set(separators))

    def test_composition_fallback_is_tilde(self):
        """Fallback for composition separator should be tilde."""
        assert Separators.COMPOSITION_FALLBACK == "~"
