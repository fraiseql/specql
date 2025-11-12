"""
Domain Service Factory

Provides configured domain services using the repository configuration system.
"""
from src.application.services.domain_service import DomainService
from src.core.config import get_config


def get_domain_service(monitoring: bool = False) -> DomainService:
    """
    Get a configured DomainService using the current repository configuration.

    This factory automatically selects the appropriate repository backend
    based on environment configuration (PostgreSQL primary, YAML fallback).

    Args:
        monitoring: Enable performance monitoring for PostgreSQL operations

    Returns:
        Configured DomainService instance
    """
    config = get_config()
    repository = config.get_domain_repository(monitoring=monitoring)
    return DomainService(repository)


def get_domain_service_with_fallback() -> DomainService:
    """
    Get a DomainService.

    PostgreSQL is now the only supported backend.

    Returns:
        DomainService instance
    """
    return get_domain_service()