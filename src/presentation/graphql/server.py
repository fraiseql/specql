"""
GraphQL server using FraiseQL.

This server provides GraphQL API access to SpecQL registry,
using the same application services as the CLI.
"""

import fraiseql
from fraiseql.fastapi import FraiseQLConfig
from pydantic import BaseModel


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
    create_app()
    # FraiseQL 1.5 uses uvicorn directly
    import uvicorn

    uvicorn.run(
        "src.presentation.graphql.server:app", host="127.0.0.1", port=4000, reload=False
    )


if __name__ == "__main__":
    main()
