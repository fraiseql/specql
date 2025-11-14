"""
GraphQL server using FraiseQL.

This server provides GraphQL API access to SpecQL registry,
using the same application services as the CLI.
"""

from pathlib import Path
import fraiseql
from fraiseql.fastapi import FraiseQLConfig
from pydantic import BaseModel
from src.application.services.domain_service import DomainService
from src.application.services.subdomain_service import SubdomainService
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.postgresql_domain_repository import (
    PostgreSQLDomainRepository,
)
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository,
)


# Create app at module level for uvicorn
def create_app():
    """Create and configure FraiseQL app"""
    # Create FraiseQL config
    config = FraiseQLConfig(
        database_url="postgresql://dummy:dummy@localhost:5432/dummy",
        auto_camel_case=True,
    )

    # Create FraiseQL app
    app = fraiseql.create_fraiseql_app(
        types=[TestEmbedding],
        queries=[query_hello],
        config=config,
    )
    return app


@fraiseql.fraise_type
class TestEmbedding(BaseModel):
    id: int
    content: str
    embedding: list[float]  # Vector as list of floats


def query_hello() -> str:
    # Simple query to test
    return "Hello from FraiseQL!"


# Create the app instance
app = create_app()


def main():
    """Run GraphQL server"""
    app = create_app()
    # FraiseQL 1.5 uses uvicorn directly
    import uvicorn

    uvicorn.run(
        "src.presentation.graphql.server:app", host="127.0.0.1", port=4000, reload=False
    )


if __name__ == "__main__":
    main()
