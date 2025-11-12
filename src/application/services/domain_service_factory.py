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
    Get a DomainService with explicit fallback behavior.

    Primary: PostgreSQL (read-write)
    Fallback: YAML (read-only)

    This provides resilience during the cut-over period.

    Returns:
        DomainService with fallback capability
    """
    try:
        return get_domain_service()
    except Exception as e:
        # Log the error and fall back to YAML (read-only)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to initialize PostgreSQL repository, falling back to read-only YAML: {e}")

        from src.infrastructure.repositories.yaml_domain_repository import YAMLDomainRepository
        from pathlib import Path
        repository = YAMLDomainRepository(Path('registry/domain_registry.yaml'), read_only=True)
        return DomainService(repository)