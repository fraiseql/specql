"""Test fuzzy matching suggestions."""

from src.utils.suggestions import suggest_correction


def test_suggest_correction_for_typo():
    """Should suggest corrections for typos."""
    valid_values = ["text", "integer", "decimal", "boolean", "timestamp"]

    # Close match
    suggestions = suggest_correction("txt", valid_values)
    assert suggestions is not None
    assert "text" in suggestions


def test_suggest_correction_case_insensitive():
    """Should handle case differences."""
    valid_values = ["pending", "confirmed", "shipped"]

    suggestions = suggest_correction("PENDING", valid_values)
    assert suggestions is not None
    assert "pending" in suggestions


def test_suggest_correction_returns_none_for_no_match():
    """Should return None when no close matches."""
    valid_values = ["apple", "banana", "orange"]

    suggestions = suggest_correction("xyz123", valid_values)
    # Might return None or empty list depending on cutoff
    assert not suggestions or len(suggestions) == 0


def test_suggest_correction_limits_suggestions():
    """Should limit number of suggestions."""
    valid_values = ["text1", "text2", "text3", "text4", "text5"]

    suggestions = suggest_correction("text", valid_values, max_suggestions=2)
    assert suggestions is not None
    assert len(suggestions) <= 2


def test_suggest_correction_enum_values():
    """Should work with enum values."""
    enum_values = ["draft", "published", "archived"]

    # Typo in 'published'
    suggestions = suggest_correction("publshed", enum_values)
    assert suggestions is not None
    assert "published" in suggestions
