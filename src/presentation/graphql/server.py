"""
GraphQL server using FraiseQL.

This server provides GraphQL API access to SpecQL registry,
using the same application services as the CLI.
"""
from pathlib import Path
import fraiseql
from src.application.services.domain_service import DomainService
from src.application.services.subdomain_service import SubdomainService
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.postgresql_domain_repository import PostgreSQLDomainRepository
from src.infrastructure.repositories.postgresql_pattern_repository import PostgreSQLPatternRepository


def create_app():
    """Create and configure FraiseQL app"""

    # Get database URL from environment
    import os
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required")

    # Initialize repositories
    domain_repo = PostgreSQLDomainRepository(db_url)
    pattern_repo = PostgreSQLPatternRepository(db_url)

    # Initialize services
    domain_service = DomainService(domain_repo)
    subdomain_service = SubdomainService(domain_repo)
    pattern_service = PatternService(pattern_repo)

    # Create FraiseQL app
    app = fraiseql.create_app(
        config_path=Path("config/fraiseql.yaml"),
        services={
            'domain': domain_service,
            'subdomain': subdomain_service,
            'pattern': pattern_service
        }
    )

    return app


def main():
    """Run GraphQL server"""
    app = create_app()
    fraiseql.run(app)


if __name__ == "__main__":
    main()