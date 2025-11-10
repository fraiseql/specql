"""
Custom exceptions with helpful error messages.
"""

from typing import Dict, Any, Optional


class SpecQLError(Exception):
    """Base exception for SpecQL errors."""

    help_text: str = ""  # Default empty help text

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        error_msg = f"\n❌ {self.__class__.__name__}: {self.message}\n"

        if self.details:
            error_msg += "\nDetails:\n"
            for key, value in self.details.items():
                error_msg += f"  • {key}: {value}\n"

        if self.help_text:
            error_msg += f"\n💡 Help: {self.help_text}\n"

        return error_msg


class EntityParseError(SpecQLError):
    """Error parsing entity YAML."""

    help_text = "Check YAML syntax and ensure required fields are present (entity, schema, fields)"


class FieldTypeError(SpecQLError):
    """Invalid field type specified."""

    help_text = "See docs/guides/field_types.md for supported types"


class ActionCompilationError(SpecQLError):
    """Error compiling action to PL/pgSQL."""

    help_text = "Check action syntax in your YAML. See docs/guides/actions.md"


class SpecQLValidationError(SpecQLError):
    """Raised when SpecQL validation fails."""

    def __init__(self, entity: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Validation error in entity '{entity}': {message}", details)
        self.entity = entity
