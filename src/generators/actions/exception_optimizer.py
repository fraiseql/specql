"""Exception handling optimization utilities"""

from src.core.ast_models import ExceptionHandler


class ExceptionOptimizer:
    """Optimizes exception handling constructs"""

    @staticmethod
    def map_specql_to_postgres_exceptions(specql_exception: str) -> str:
        """Map SpecQL exception names to PostgreSQL exception names"""
        mapping = {
            "payment_failed": "RAISE_EXCEPTION",
            "network_error": "CONNECTION_EXCEPTION",
            "database_error": "INTEGRITY_CONSTRAINT_VIOLATION",
            "parse_error": "INVALID_TEXT_REPRESENTATION",
            "validation_error": "CHECK_VIOLATION",
            "division_by_zero": "DIVISION_BY_ZERO",
            "no_data_found": "NO_DATA_FOUND",
            "too_many_rows": "TOO_MANY_ROWS",
            "unique_violation": "UNIQUE_VIOLATION",
            "foreign_key_violation": "FOREIGN_KEY_VIOLATION",
            "not_null_violation": "NOT_NULL_VIOLATION",
        }
        return mapping.get(specql_exception.lower(), specql_exception.upper())

    @staticmethod
    def optimize_exception_handlers(handlers: list[ExceptionHandler]) -> list[ExceptionHandler]:
        """Optimize exception handler ordering and deduplication"""
        # Ensure OTHERS is last if present
        others_handler = None
        specific_handlers = []

        for handler in handlers:
            if handler.when_condition.upper() == "OTHERS":
                others_handler = handler
            else:
                specific_handlers.append(handler)

        # Return specific handlers first, then OTHERS
        result = specific_handlers
        if others_handler:
            result.append(others_handler)

        return result

    @staticmethod
    def validate_exception_usage(step_handlers: list[ExceptionHandler]) -> None:
        """Validate exception handler usage"""
        # Check for duplicate conditions
        conditions = set()
        for handler in step_handlers:
            condition = handler.when_condition.upper()
            if condition in conditions:
                raise ValueError(f"Duplicate exception handler for: {condition}")
            conditions.add(condition)

    @staticmethod
    def suggest_exception_restructuring(handlers: list[ExceptionHandler]) -> str:
        """Suggest restructuring for better exception handling"""
        # Placeholder for future optimization suggestions
        return ""