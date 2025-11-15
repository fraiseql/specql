"""
Pattern Service Factory

Provides configured PatternService instances with appropriate repository backends.
Similar to DomainServiceFactory but for pattern library operations.
"""

import logging
from src.application.services.pattern_service import PatternService
from src.core.config import get_config

logger = logging.getLogger(__name__)


class PatternServiceFactory:
    """
    Factory for creating PatternService instances with proper repository configuration.

    Supports PostgreSQL primary with fallback mechanisms.
    """

    @staticmethod
    def get_pattern_service(monitoring: bool = False) -> PatternService:
        """
        Get a configured PatternService with PostgreSQL primary backend.

        Args:
            monitoring: Whether to enable performance monitoring

        Returns:
            PatternService: Configured service instance

        Raises:
            RuntimeError: If repository configuration fails
        """
        try:
            config = get_config()
            repository = config.get_pattern_repository(monitoring=monitoring)
            return PatternService(repository)
        except Exception as e:
            logger.error(f"Failed to create pattern service: {e}")
            raise RuntimeError(f"Pattern service creation failed: {e}")

    @staticmethod
    def get_pattern_service_with_fallback(monitoring: bool = False) -> PatternService:
        """
        Get a PatternService with automatic fallback to in-memory if PostgreSQL fails.

        This provides resilience during database outages or configuration issues.

        Args:
            monitoring: Whether to enable performance monitoring

        Returns:
            PatternService: Configured service with fallback
        """
        try:
            # Try PostgreSQL first
            return PatternServiceFactory.get_pattern_service(monitoring=monitoring)
        except Exception as e:
            logger.warning(f"PostgreSQL pattern repository failed, falling back to in-memory: {e}")

            # Fallback to in-memory repository
            try:
                from src.infrastructure.repositories.in_memory_pattern_repository import InMemoryPatternRepository
                repository = InMemoryPatternRepository()
                logger.info("Using in-memory pattern repository as fallback")
                return PatternService(repository)
            except Exception as fallback_error:
                logger.error(f"Fallback pattern repository also failed: {fallback_error}")
                raise RuntimeError(f"Both primary and fallback pattern repositories failed: {e}, {fallback_error}")


# Convenience functions for easy access
def get_pattern_service(monitoring: bool = False) -> PatternService:
    """Get configured pattern service (convenience function)"""
    return PatternServiceFactory.get_pattern_service(monitoring=monitoring)


def get_pattern_service_with_fallback(monitoring: bool = False) -> PatternService:
    """Get pattern service with fallback (convenience function)"""
    return PatternServiceFactory.get_pattern_service_with_fallback(monitoring=monitoring)