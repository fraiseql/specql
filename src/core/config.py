"""
Configuration management for SpecQL

Handles repository backend selection and other configuration options.
"""
import os
from enum import Enum
from pathlib import Path
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
        self.registry_yaml_path = Path('registry/domain_registry.yaml')

        # Validate configuration
        self._validate_config()

    def _get_repository_backend(self) -> RepositoryBackend:
        """Determine which repository backend to use"""
        backend_env = os.getenv('SPECQL_REPOSITORY_BACKEND', '').upper()

        if backend_env == 'YAML':
            return RepositoryBackend.YAML
        elif backend_env == 'IN_MEMORY':
            return RepositoryBackend.IN_MEMORY
        elif backend_env == 'POSTGRESQL':
            return RepositoryBackend.POSTGRESQL
        else:
            # Auto-detect: prefer PostgreSQL if database URL is available
            if os.getenv('SPECQL_DB_URL'):
                return RepositoryBackend.POSTGRESQL
            else:
                return RepositoryBackend.YAML

    def _validate_config(self) -> None:
        """Validate configuration consistency"""
        if self.repository_backend == RepositoryBackend.POSTGRESQL:
            if not self.database_url:
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
                if monitoring:
                    from src.infrastructure.repositories.monitored_postgresql_repository import MonitoredPostgreSQLDomainRepository
                    return MonitoredPostgreSQLDomainRepository(self.database_url)
                else:
                    from src.infrastructure.repositories.postgresql_domain_repository import PostgreSQLDomainRepository
                    return PostgreSQLDomainRepository(self.database_url)
            elif self.repository_backend == RepositoryBackend.YAML:
                from src.infrastructure.repositories.yaml_domain_repository import YAMLDomainRepository
                return YAMLDomainRepository(self.registry_yaml_path)
            elif self.repository_backend == RepositoryBackend.IN_MEMORY:
                from src.infrastructure.repositories.in_memory_domain_repository import InMemoryDomainRepository
                return InMemoryDomainRepository()
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