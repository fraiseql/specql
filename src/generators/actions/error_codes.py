"""
Standardized error codes and messages for Team C action compilation

Provides structured error responses with user-friendly messages and actionable guidance.
"""

from typing import Any

ERROR_CATALOG = {
    "MISSING_REQUIRED_FIELD": {
        "code": "validation:required_field",
        "message_template": "{field} is required",
        "user_action": "Provide a value for {field}",
        "severity": "error",
    },
    "FK_NOT_FOUND": {
        "code": "validation:reference_not_found",
        "message_template": "Referenced {entity} not found",
        "user_action": "Verify {entity}_id exists and belongs to your organization",
        "severity": "error",
    },
    "INVALID_ENUM_VALUE": {
        "code": "validation:invalid_enum",
        "message_template": "{field} must be one of: {allowed_values}",
        "user_action": "Choose a valid value for {field}",
        "severity": "error",
    },
    "DUPLICATE_KEY": {
        "code": "constraint:unique_violation",
        "message_template": "A {entity} with this {field} already exists",
        "user_action": "Use a different {field} or update the existing record",
        "severity": "error",
    },
    "TENANT_ISOLATION_VIOLATION": {
        "code": "security:tenant_isolation",
        "message_template": "Cannot access {entity} from another organization",
        "user_action": "Contact support if you believe this is an error",
        "severity": "critical",
    },
    "VALIDATION_FAILED": {
        "code": "validation:expression_failed",
        "message_template": "Validation failed: {expression}",
        "user_action": "Check your input data and try again",
        "severity": "error",
    },
    "PERMISSION_DENIED": {
        "code": "security:permission_denied",
        "message_template": "You don't have permission to perform this action",
        "user_action": "Contact your administrator for access",
        "severity": "error",
    },
}


def build_error_response(error_type: str, **context) -> dict[str, Any]:
    """
    Build structured error response

    Args:
        error_type: Key from ERROR_CATALOG
        **context: Variables to substitute in templates

    Returns:
        Structured error dict
    """
    if error_type not in ERROR_CATALOG:
        # Fallback for unknown error types
        return {
            "code": "error:unknown",
            "message": f"An error occurred: {error_type}",
            "user_action": "Contact support if this persists",
            "severity": "error",
            "context": context,
        }

    error_def = ERROR_CATALOG[error_type]
    return {
        "code": error_def["code"],
        "message": error_def["message_template"].format(**context),
        "user_action": error_def["user_action"].format(**context),
        "severity": error_def["severity"],
        "context": context,
    }


def format_error_for_sql(error_response: dict[str, Any]) -> str:
    """
    Format error response as SQL-safe string for TEXT column

    Args:
        error_response: Error dict from build_error_response

    Returns:
        JSON string safe for SQL TEXT columns
    """
    import json

    return json.dumps(error_response)
