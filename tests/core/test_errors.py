"""Test enhanced error framework."""

from src.core.errors import (
    ErrorContext,
    SpecQLError,
    InvalidFieldTypeError,
    InvalidEnumValueError,
    MissingRequiredFieldError,
    CircularDependencyError,
)


def test_error_context_dataclass():
    """ErrorContext should store contextual information."""
    context = ErrorContext(
        file_path="contact.yaml",
        line_number=5,
        entity_name="Contact",
        field_name="email",
    )

    assert context.file_path == "contact.yaml"
    assert context.line_number == 5
    assert context.entity_name == "Contact"
    assert context.field_name == "email"


def test_specql_error_formats_with_context():
    """SpecQLError should format message with context."""
    context = ErrorContext(
        file_path="user.yaml",
        entity_name="User",
        field_name="age",
    )

    error = SpecQLError(
        message="Invalid value",
        context=context,
        suggestion="Use a positive integer",
        docs_link="https://example.com/docs",
    )

    error_msg = str(error)

    # Should include all parts
    assert "❌" in error_msg
    assert "Invalid value" in error_msg
    assert "user.yaml" in error_msg
    assert "User" in error_msg
    assert "age" in error_msg
    assert "💡" in error_msg
    assert "Use a positive integer" in error_msg
    assert "📚" in error_msg
    assert "https://example.com/docs" in error_msg


def test_invalid_field_type_error_with_suggestions():
    """InvalidFieldTypeError should suggest similar types."""
    context = ErrorContext(
        file_path="post.yaml",
        entity_name="Post",
        field_name="content",
    )

    valid_types = ["text", "integer", "decimal", "boolean", "timestamp"]

    error = InvalidFieldTypeError(
        field_type="txt",  # Typo
        valid_types=valid_types,
        context=context,
    )

    error_msg = str(error)

    # Should suggest "text"
    assert "Did you mean" in error_msg or "text" in error_msg


def test_invalid_enum_value_error():
    """InvalidEnumValueError should list valid values."""
    context = ErrorContext(
        entity_name="Order",
        field_name="status",
    )

    error = InvalidEnumValueError(
        value="shiped",  # Typo
        valid_values=["pending", "paid", "shipped", "delivered"],
        context=context,
    )

    error_msg = str(error)
    assert "shiped" in error_msg
    assert "pending" in error_msg or "shipped" in error_msg


def test_missing_required_field_error():
    """MissingRequiredFieldError should be clear."""
    context = ErrorContext(
        file_path="entity.yaml",
        entity_name="Product",
    )

    error = MissingRequiredFieldError(
        field_name="name",
        context=context,
    )

    error_msg = str(error)
    assert "name" in error_msg
    assert "Product" in error_msg


def test_circular_dependency_error():
    """CircularDependencyError should show dependency chain."""
    context = ErrorContext(file_path="entities.yaml")

    error = CircularDependencyError(
        entities=["User", "Post", "Comment", "User"],
        context=context,
    )

    error_msg = str(error)
    assert "User" in error_msg
    assert "→" in error_msg or "->" in error_msg
