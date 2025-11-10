"""
Safe Slug Generator
Converts arbitrary text to URL-safe identifiers
"""

import re
import unicodedata


def safe_slug(
    text: str | None,
    separator: str = "_",
    fallback: str = "untitled",
    max_length: int | None = None,
) -> str:
    """
    Convert text to a safe slug (URL-safe identifier)

    Args:
        text: Input text to convert
        separator: Character to use as word separator (default: "_")
        fallback: Text to use if result is empty (default: "untitled")
        max_length: Maximum length of result (default: None = unlimited)

    Returns:
        Safe slug string

    Examples:
        >>> safe_slug("Hello World")
        'hello_world'
        >>> safe_slug("Café résumé")
        'cafe_resume'
        >>> safe_slug("Special!@#$Characters")
        'special_characters'
        >>> safe_slug("", fallback="default")
        'default'
        >>> safe_slug("123 Numbers", fallback="n")
        'n_123_numbers'
    """
    # Handle None or empty string
    if not text or not text.strip():
        return fallback

    # Convert to string (in case it's not)
    text = str(text)

    # Normalize Unicode characters (NFD = decompose accents)
    # Example: "é" → "e" + accent mark
    text = unicodedata.normalize("NFD", text)

    # Remove accent marks (category Mn = Mark, nonspacing)
    # This converts "é" → "e", "ñ" → "n", etc.
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    # Insert separators before uppercase letters that follow lowercase (camelCase handling)
    # Pattern: (?=[A-Z])(?<=[a-z]) - positive lookahead for uppercase, positive lookbehind for lowercase
    text = re.sub(r"(?=[A-Z])(?<=[a-z])", separator, text)

    # Convert to lowercase
    text = text.lower()

    # Replace sequences of non-alphanumeric characters with separator
    # Pattern: \W+ matches one or more non-word characters
    text = re.sub(r"\W+", separator, text)

    # Remove leading/trailing separators
    text = text.strip(separator)

    # Handle case where result is empty or starts with digit
    if not text or text[0].isdigit():
        # Prefix with fallback if starts with digit
        if text and text[0].isdigit():
            text = f"{fallback}{separator}{text}"
        else:
            text = fallback

    # Truncate to max_length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip(separator)

    return text


def safe_identifier(text: str | None, fallback: str = "field") -> str:
    """
    Create a safe Python/PostgreSQL identifier from text

    Wrapper around safe_slug with identifier-specific defaults.
    Ensures result is a valid Python/PostgreSQL identifier.

    Args:
        text: Input text
        fallback: Fallback if text is empty (default: "field")

    Returns:
        Valid identifier string

    Examples:
        >>> safe_identifier("First Name")
        'first_name'
        >>> safe_identifier("123-ID")
        'field_123_id'
    """
    slug = safe_slug(text, separator="_", fallback=fallback)

    # Ensure it doesn't start with a number (invalid identifier)
    if slug[0].isdigit():
        slug = f"{fallback}_{slug}"

    return slug


def safe_table_name(entity_name: str, prefix: str = "tb") -> str:
    """
    Create a safe table name from entity name

    Args:
        entity_name: Entity name (e.g., "Contact", "TaskItem")
        prefix: Table prefix (default: "tb")

    Returns:
        Table name with prefix (e.g., "tb_contact", "tb_task_item")

    Examples:
        >>> safe_table_name("Contact")
        'tb_contact'
        >>> safe_table_name("TaskItem")
        'tb_task_item'
    """
    slug = safe_slug(entity_name, fallback="entity")
    return f"{prefix}_{slug}"
