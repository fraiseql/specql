"""Provide helpful suggestions for user errors."""

from difflib import get_close_matches
from typing import List, Optional


def suggest_correction(
    invalid_value: str,
    valid_values: List[str],
    max_suggestions: int = 3,
    cutoff: float = 0.6,
) -> Optional[List[str]]:
    """
    Suggest corrections for misspelled values.

    Args:
        invalid_value: The invalid input
        valid_values: List of valid options
        max_suggestions: Maximum number of suggestions
        cutoff: Similarity threshold (0-1)

    Returns:
        List of suggestions or None
    """
    matches = get_close_matches(
        invalid_value,
        valid_values,
        n=max_suggestions,
        cutoff=cutoff,
    )
    return matches if matches else None
