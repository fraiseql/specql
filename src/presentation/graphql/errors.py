"""
GraphQL error formatting.

Converts application exceptions to GraphQL errors with proper codes.
"""
# Note: GraphQL error handling will be implemented when FraiseQL is available
from src.application.exceptions import (
    ApplicationError,
    DomainAlreadyExistsError,
    DomainNotFoundError,
    SubdomainAlreadyExistsError,
    SubdomainNotFoundError
)


def format_application_error(error: Exception) -> Exception:
    """
    Format application exception as GraphQL error.

    Maps application exceptions to appropriate error codes.
    For now, just re-raise with additional context.
    """
    error_map = {
        DomainAlreadyExistsError: 'DOMAIN_ALREADY_EXISTS',
        DomainNotFoundError: 'DOMAIN_NOT_FOUND',
        SubdomainAlreadyExistsError: 'SUBDOMAIN_ALREADY_EXISTS',
        SubdomainNotFoundError: 'SUBDOMAIN_NOT_FOUND',
        ValueError: 'VALIDATION_ERROR'
    }

    error_code = error_map.get(type(error), 'INTERNAL_ERROR')

    # For now, just re-raise with code in message
    raise Exception(f"[{error_code}] {str(error)}")


# Middleware for error handling
def error_handler_middleware(next, root, info, **args):
    """Middleware to catch and format application errors"""
    try:
        return next(root, info, **args)
    except ApplicationError as e:
        raise format_application_error(e)
    except ValueError as e:
        raise format_application_error(e)
    except Exception as e:
        # Log unexpected errors
        import logging
        logging.error(f"Unexpected error in GraphQL resolver: {e}", exc_info=True)
        raise Exception("Internal server error")