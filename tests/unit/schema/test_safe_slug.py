"""
Tests for safe_slug utility function
Tests that safe_slug function handles all edge cases correctly
"""

from utils.safe_slug import safe_identifier, safe_slug, safe_table_name


def test_normal_text():
    """Test: Normal text converts to lowercase with underscores"""
    assert safe_slug("Hello World") == "hello_world"


def test_unicode_unaccent():
    """Test: Unicode characters are converted to ASCII equivalents"""
    assert safe_slug("Café résumé") == "cafe_resume"


def test_special_characters():
    """Test: Special characters are replaced with separators"""
    assert safe_slug("Hello@World!#$") == "hello_world"


def test_empty_string():
    """Test: Empty string returns fallback"""
    assert safe_slug("", fallback="default") == "default"


def test_consecutive_separators():
    """Test: Multiple spaces/special chars become single separator"""
    assert safe_slug("Hello    World!!!") == "hello_world"


def test_mixed_case():
    """Test: Mixed case converts to lowercase with camelCase splitting"""
    assert safe_slug("CamelCaseText") == "camel_case_text"


def test_max_length():
    """Test: Truncation to max_length"""
    assert safe_slug("very_long_text_here", max_length=10) == "very_long"


def test_custom_separator():
    """Test: Custom separator character"""
    assert safe_slug("Hello World", separator="-") == "hello-world"


def test_safe_identifier_function():
    """Test: safe_identifier ensures valid Python identifier"""
    assert safe_identifier("First Name") == "first_name"
    assert safe_identifier("123-field") == "field_123_field"


def test_safe_table_name_function():
    """Test: safe_table_name adds prefix"""
    assert safe_table_name("Contact") == "tb_contact"
    assert safe_table_name("TaskItem") == "tb_task_item"


def test_none_input():
    """Test: None input returns fallback"""
    assert safe_slug(None, fallback="default") == "default"


def test_whitespace_only():
    """Test: Whitespace-only input returns fallback"""
    assert safe_slug("   \t\n   ", fallback="default") == "default"


def test_starts_with_digit():
    """Test: Text starting with digit gets fallback prefix"""
    assert safe_slug("123 Numbers", fallback="n") == "n_123_numbers"


def test_all_digits():
    """Test: All digits gets fallback prefix"""
    assert safe_slug("123", fallback="n") == "n_123"


def test_max_length_with_separator():
    """Test: max_length trims at separator boundary"""
    assert safe_slug("very_long_text_here", max_length=12) == "very_long_te"
