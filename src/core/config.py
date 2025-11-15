"""
Configuration management for SpecQL

Handles repository backend selection and other configuration options.
"""
import os
from enum import Enum
from typing import Optional


class RepositoryBackend(Enum):
    """Repository backend options"""
    POSTGRESQL = "postgresql"
    YAML = "yaml"
    IN_MEMORY = "in_memory"


class SpecQLConfig:
    """
    Configuration for SpecQL components

    Handles repository backend selection and database connections.
    """

    def __init__(self):
        # Repository backend configuration
        self.repository_backend = self._get_repository_backend()
        self.database_url = os.getenv('SPECQL_DB_URL')

        # Validate configuration
        self._validate_config()

    def _get_repository_backend(self) -> RepositoryBackend:
        """Determine which repository backend to use"""
        backend_env = os.getenv('SPECQL_REPOSITORY_BACKEND', '').upper()

        if backend_env == 'IN_MEMORY':
            return RepositoryBackend.IN_MEMORY
        elif backend_env == 'POSTGRESQL':
            return RepositoryBackend.POSTGRESQL
        else:
            # Default to PostgreSQL if DB URL is set, otherwise in-memory for testing
            if os.getenv('SPECQL_DB_URL'):
                return RepositoryBackend.POSTGRESQL
            else:
                return RepositoryBackend.IN_MEMORY

    def _validate_config(self) -> None:
        """Validate configuration consistency"""
        # PostgreSQL requires database URL
        if self.repository_backend == RepositoryBackend.POSTGRESQL and not self.database_url:
            raise ValueError(
                "PostgreSQL repository backend requires SPECQL_DB_URL environment variable"
            )

    def should_use_postgresql_primary(self) -> bool:
        """Check if PostgreSQL should be used as primary repository"""
        return self.repository_backend == RepositoryBackend.POSTGRESQL

    def should_use_yaml_fallback(self) -> bool:
        """Check if YAML should be used as fallback"""
        return self.repository_backend == RepositoryBackend.YAML

    def get_domain_repository(self, monitoring: bool = False):
        """Factory method to get the appropriate domain repository"""
        try:
            if self.repository_backend == RepositoryBackend.POSTGRESQL:
                if not self.database_url:
                    raise ValueError("Database URL is required for PostgreSQL repository")
                if monitoring:
                    from src.infrastructure.repositories.monitored_postgresql_repository import MonitoredPostgreSQLDomainRepository
                    return MonitoredPostgreSQLDomainRepository(self.database_url)
                else:
                    from src.infrastructure.repositories.postgresql_domain_repository import PostgreSQLDomainRepository
                    return PostgreSQLDomainRepository(self.database_url)
            elif self.repository_backend == RepositoryBackend.IN_MEMORY:
                from src.infrastructure.repositories.in_memory_domain_repository import InMemoryDomainRepository
                return InMemoryDomainRepository()
            else:
                raise ValueError(f"Unknown repository backend: {self.repository_backend}")
        except ImportError as e:
            raise RuntimeError(f"Failed to import repository implementation: {e}")

    def get_pattern_repository(self, monitoring: bool = False):
        """Factory method to get the appropriate pattern repository"""
        try:
            if self.repository_backend == RepositoryBackend.POSTGRESQL:
                if not self.database_url:
                    raise ValueError("Database URL is required for PostgreSQL repository")
                if monitoring:
                    from src.infrastructure.repositories.monitored_postgresql_pattern_repository import MonitoredPostgreSQLPatternRepository
                    return MonitoredPostgreSQLPatternRepository(self.database_url)
                else:
                    from src.infrastructure.repositories.postgresql_pattern_repository import PostgreSQLPatternRepository
                    return PostgreSQLPatternRepository(self.database_url)
            elif self.repository_backend == RepositoryBackend.IN_MEMORY:
                from src.infrastructure.repositories.in_memory_pattern_repository import InMemoryPatternRepository
                return InMemoryPatternRepository()
            else:
                raise ValueError(f"Unknown repository backend: {self.repository_backend}")
        except ImportError as e:
            raise RuntimeError(f"Failed to import repository implementation: {e}")


# Global configuration instance
_config_instance: Optional[SpecQLConfig] = None


def get_config() -> SpecQLConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SpecQLConfig()
    return _config_instance