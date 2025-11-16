"""
Enhanced error handling with helpful messages.
"""

from typing import Optional, List
from dataclasses import dataclass


@dataclass
class ErrorContext:
    """Context about where error occurred."""

    file_path: Optional[str] = None
    line_number: Optional[int] = None
    entity_name: Optional[str] = None
    field_name: Optional[str] = None
    action_name: Optional[str] = None


class SpecQLError(Exception):
    """Base exception for SpecQL with enhanced messaging."""

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        suggestion: Optional[str] = None,
        docs_link: Optional[str] = None,
    ):
        self.message = message
        self.context = context
        self.suggestion = suggestion
        self.docs_link = docs_link
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error with context and suggestions."""
        parts = []

        # Main error
        parts.append(f"❌ {self.message}")

        # Context
        if self.context:
            ctx_parts = []
            if self.context.file_path:
                ctx_parts.append(f"File: {self.context.file_path}")
            if self.context.line_number:
                ctx_parts.append(f"Line: {self.context.line_number}")
            if self.context.entity_name:
                ctx_parts.append(f"Entity: {self.context.entity_name}")
            if self.context.field_name:
                ctx_parts.append(f"Field: {self.context.field_name}")
            if self.context.action_name:
                ctx_parts.append(f"Action: {self.context.action_name}")

            if ctx_parts:
                parts.append("  " + " | ".join(ctx_parts))

        # Suggestion
        if self.suggestion:
            parts.append(f"  💡 Suggestion: {self.suggestion}")

        # Documentation
        if self.docs_link:
            parts.append(f"  📚 Docs: {self.docs_link}")

        return "\n".join(parts)


class InvalidFieldTypeError(SpecQLError):
    """Raised when field has invalid type."""

    def __init__(self, field_type: str, valid_types: List[str], context: ErrorContext):
        from src.utils.suggestions import suggest_correction

        # Get fuzzy matching suggestions
        suggestions = suggest_correction(field_type, valid_types)
        suggestion_text = (
            f"Did you mean: {', '.join(suggestions)}?"
            if suggestions
            else f"Valid types: {', '.join(valid_types[:10])}{'...' if len(valid_types) > 10 else ''}"
        )

        super().__init__(
            message=f"Invalid field type: '{field_type}'",
            context=context,
            suggestion=suggestion_text,
            docs_link="https://github.com/fraiseql/specql/blob/main/docs/03_reference/FIELD_TYPES.md",
        )


class InvalidEnumValueError(SpecQLError):
    """Raised when enum value is invalid."""

    def __init__(self, value: str, valid_values: List[str], context: ErrorContext):
        super().__init__(
            message=f"Invalid enum value: '{value}'",
            context=context,
            suggestion=f"Valid values: {', '.join(valid_values)}",
            docs_link="https://github.com/fraiseql/specql/blob/main/docs/03_reference/FIELD_TYPES.md#enum",
        )


class MissingRequiredFieldError(SpecQLError):
    """Raised when required field is missing."""

    def __init__(self, field_name: str, context: ErrorContext):
        super().__init__(
            message=f"Missing required field: '{field_name}'",
            context=context,
            suggestion="Add the missing field to your entity definition",
            docs_link="https://github.com/fraiseql/specql/blob/main/docs/03_reference/ENTITY_SYNTAX.md",
        )


class CircularDependencyError(SpecQLError):
    """Raised when circular dependency is detected."""

    def __init__(self, entities: List[str], context: ErrorContext):
        super().__init__(
            message=f"Circular dependency detected: {' → '.join(entities)}",
            context=context,
            suggestion="Remove or restructure the circular reference",
            docs_link="https://github.com/fraiseql/specql/blob/main/docs/03_reference/RELATIONSHIPS.md",
        )


class ParseError(SpecQLError):
    """Raised when YAML parsing fails."""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            context=context,
            suggestion="Check your YAML syntax and structure",
            docs_link="https://github.com/fraiseql/specql/blob/main/docs/03_reference/YAML_SYNTAX.md",
        )


class SpecQLValidationError(SpecQLError):
    """Raised when entity validation fails."""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            context=context,
            suggestion="Review the entity definition and fix the validation error",
            docs_link="https://github.com/fraiseql/specql/blob/main/docs/03_reference/VALIDATION.md",
        )
