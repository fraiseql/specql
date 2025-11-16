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
    # Case-insensitive matching
    invalid_lower = invalid_value.lower()
    valid_lower = [v.lower() for v in valid_values]

    matches_lower = get_close_matches(
        invalid_lower,
        valid_lower,
        n=max_suggestions,
        cutoff=cutoff,
    )

    if not matches_lower:
        return None

    # Map back to original case
    result = []
    for match_lower in matches_lower:
        # Find the original case version
        for original in valid_values:
            if original.lower() == match_lower:
                result.append(original)
                break

    return result
