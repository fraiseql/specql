# FraiseQL Server Troubleshooting Guide

**Date**: 2025-11-14
**Status**: Active Development
**Priority**: High
**Context**: Team is struggling to make FraiseQL server work with expected features

---

## Table of Contents

1. [Current Status](#current-status)
2. [Key Findings](#key-findings)
3. [Issues and Solutions](#issues-and-solutions)
4. [What Works](#what-works)
5. [What Doesn't Work](#what-doesnt-work)
6. [Workarounds](#workarounds)
7. [Next Steps](#next-steps)

---

## Current Status

### ✅ What's Working

1. **FraiseQL Installation**: v1.5.0 is installed correctly
   ```bash
   $ pip list | grep fraise
   fraiseql                  1.5.0
   fraiseql-confiture        0.3.0
   ```

2. **Server Starts Successfully**:
   ```bash
   $ DATABASE_URL="postgresql://..." python -m uvicorn src.presentation.graphql.server:app --host 127.0.0.1 --port 4000

   INFO:     Started server process [1919646]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:4000
   ```

3. **Basic FraiseQL App Creation**: The app initializes without errors
   ```python
   from src.presentation.graphql.server import create_app
   app = create_app()  # ✓ Works!
   ```

4. **GraphQL Schema Registration**: Types and queries register successfully
   ```python
   @fraiseql.fraise_type
   class TestEmbedding(BaseModel):
       id: int
       content: str
       embedding: list[float]  # ✓ Works!
   ```

### ❌ What's NOT Working

1. **No Embedding/Vector Features in FraiseQL 1.5**

   The team discovered that **FraiseQL 1.5 does NOT include** the expected features:
   - ❌ No `fraiseql.embeddings` module
   - ❌ No `fraiseql.operators.vector` module
   - ❌ No `FraiseQLClient` class
   - ❌ No automatic embedding generation
   - ❌ No vector operator auto-discovery

2. **Configuration Not Recognized**

   The `config/fraiseql.yaml` file has embedding configuration:
   ```yaml
   embeddings:
     provider: sentence_transformers
     model: all-MiniLM-L6-v2
     auto_generate: true
   ```

   **But FraiseQL 1.5 ignores it** - these features don't exist in the current version.

3. **Test Failures**
   ```bash
   $ python test_fraiseql_capabilities.py

   ✓ FraiseQL imported (1.5.0)
   ✗ FraiseQLClient not found
   ⚠ fraiseql.operators not available
   ⚠ fraiseql.embeddings not available

   Passed: 1/4
   ```

---

## Key Findings

### Finding #1: FraiseQL 1.5 Feature Gap

**Discovery**: The simplification plan assumed FraiseQL 1.5 has embedding/vector features, but **it doesn't**.

**Evidence**:
```python
import fraiseql
print(dir(fraiseql))
# Available modules: build_fraiseql_schema, create_fraiseql_app, fraise_type, etc.
# Missing: embeddings, operators.vector, FraiseQLClient
```

**Available in FraiseQL 1.5.0**:
- ✅ `create_fraiseql_app()` - FastAPI app creation
- ✅ `build_fraiseql_schema()` - GraphQL schema builder
- ✅ `fraise_type`, `fraise_input` - Type decorators
- ✅ `query`, `mutation` - Resolver decorators
- ✅ `auto_discover` - PostgreSQL metadata discovery
- ✅ CRUD operations auto-generation
- ✅ Authentication (Auth0, custom providers)
- ✅ CQRS patterns

**NOT Available in FraiseQL 1.5.0**:
- ❌ Embedding service
- ❌ Vector operators (cosineDistance, l2Distance)
- ❌ Auto-embedding generation
- ❌ FraiseQLClient (GraphQL client)

### Finding #2: Version Mismatch

**Issue**: The simplification plan document assumes a **future version** of FraiseQL with embedding features.

**Reality**: FraiseQL 1.5.0 is a **GraphQL schema generator**, not a vector search platform.

**Implication**: The 70% code reduction plan **cannot be implemented yet** - those features don't exist.

### Finding #3: Confiture vs FraiseQL Confusion

**Discovery**: There are TWO packages:
- `fraiseql` (1.5.0) - GraphQL server/schema builder
- `fraiseql-confiture` (0.3.0) - Configuration management

**Confusion**: Team may have expected `fraiseql-confiture` to handle the `config/fraiseql.yaml` embedding config, but it only handles basic server config.

---

## Issues and Solutions

### Issue #1: "FraiseQL doesn't expose vector operators"

**Problem**: Team tried to use vector operators in GraphQL queries:
```graphql
query {
  documents(
    where: { embedding: { cosineDistance: { ... } } }
  ) { id }
}
```

**Error**: Field `cosineDistance` doesn't exist - it's not in FraiseQL 1.5.

**Solution**:
1. **Keep using SpecQL's custom functions** (don't deprecate yet!)
2. **Wait for FraiseQL update** with vector features
3. **OR implement custom vector operators** in FraiseQL app

**Workaround** (Option 3):
```python
# src/presentation/graphql/server.py
from fraiseql import fraise_type, query
from pydantic import BaseModel

@fraise_type
class VectorSearchInput(BaseModel):
    query_text: str
    threshold: float = 0.7
    limit: int = 10

@query
def search_documents(vector_search: VectorSearchInput) -> list[Document]:
    """Custom resolver for vector search"""
    from src.infrastructure.services.embedding_service import EmbeddingService

    service = EmbeddingService()
    query_embedding = service.generate_embedding(vector_search.query_text)

    # Use raw SQL with pgvector
    results = db.execute("""
        SELECT id, title, content,
               1 - (embedding <=> %s) AS similarity
        FROM tv_document
        WHERE 1 - (embedding <=> %s) >= %s
        ORDER BY embedding <=> %s
        LIMIT %s
    """, [query_embedding] * 4 + [vector_search.limit])

    return [Document(**row) for row in results]
```

### Issue #2: "Embedding generation doesn't work automatically"

**Problem**: Config says `auto_generate: true`, but embeddings aren't created on INSERT.

**Cause**: FraiseQL 1.5 doesn't have embedding features - this config is ignored.

**Solution**:
1. **Keep SpecQL's embedding infrastructure** (`embedding_service.py`, `embeddings_pg.py`)
2. **Use PostgreSQL triggers** for auto-generation (current approach works)
3. **Wait for FraiseQL update** OR contribute embedding feature

**Workaround** (current approach):
```sql
-- Keep using SpecQL-generated triggers
CREATE OR REPLACE FUNCTION auto_generate_embedding()
RETURNS TRIGGER AS $$
BEGIN
    -- Call external embedding service (via pg_background, http, etc.)
    -- This is what SpecQL currently does
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_document_embedding
AFTER INSERT OR UPDATE ON tv_document
FOR EACH ROW EXECUTE FUNCTION auto_generate_embedding();
```

### Issue #3: "Can't query FraiseQL server from Python"

**Problem**: Team tried to use `FraiseQLClient` for programmatic queries:
```python
from fraiseql import FraiseQLClient  # ❌ ModuleNotFoundError
```

**Cause**: FraiseQL 1.5 doesn't include a client library.

**Solution**: Use a standard GraphQL client instead:

**Option A: HTTPX + GraphQL**
```python
import httpx

class FraiseQLClient:
    """Custom GraphQL client for FraiseQL server"""

    def __init__(self, url: str = "http://localhost:4000/graphql"):
        self.url = url
        self.client = httpx.Client()

    def query(self, query: str, variables: dict = None):
        """Execute GraphQL query"""
        response = self.client.post(
            self.url,
            json={"query": query, "variables": variables or {}}
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data["data"]
```

**Option B: GQL Library**
```python
from gql import gql, Client
from gql.transport.httpx import HTTPXTransport

transport = HTTPXTransport(url="http://localhost:4000/graphql")
client = Client(transport=transport, fetch_schema_from_transport=True)

# Execute query
query = gql("""
    query GetDocuments {
        documents { id title }
    }
""")
result = client.execute(query)
```

### Issue #4: "Server works but no data appears"

**Problem**: Server starts, GraphQL playground loads, but queries return empty results.

**Possible Causes**:
1. Database URL incorrect
2. Schema not discovered
3. Tables don't exist
4. Permissions issue

**Debugging Steps**:

```bash
# 1. Check database connection
$ DATABASE_URL="postgresql://user:pass@localhost:5432/specql"
$ psql $DATABASE_URL -c "SELECT current_database();"

# 2. Verify tables exist
$ psql $DATABASE_URL -c "\dt specql_registry.*"

# 3. Test manual query
$ psql $DATABASE_URL -c "SELECT * FROM specql_registry.tb_domain LIMIT 5;"

# 4. Check FraiseQL auto-discovery
$ python -c "
from src.presentation.graphql.server import create_app
app = create_app()
# Check if schema was built
"
```

**Solution**: Ensure `auto_discover=True` is working:

```python
# src/presentation/graphql/server.py
def create_app():
    config = FraiseQLConfig(
        database_url=os.getenv("DATABASE_URL"),
        auto_camel_case=True,
    )

    app = fraiseql.create_fraiseql_app(
        types=[],  # Empty if using auto_discover
        queries=[],
        config=config,
        auto_discover=True,  # ← Enable PostgreSQL introspection
    )
    return app
```

---

## What Works (Current FraiseQL 1.5 Capabilities)

### ✅ Feature #1: Auto-Discovery from PostgreSQL

FraiseQL can automatically generate GraphQL schema from PostgreSQL tables:

```python
app = fraiseql.create_fraiseql_app(
    database_url="postgresql://...",
    auto_discover=True,  # ← Introspects database
)
```

**Result**: GraphQL types auto-generated from:
- Table columns → GraphQL fields
- Foreign keys → Relations
- Constraints → Validation
- Comments → Descriptions

**Example**:
```sql
-- PostgreSQL
CREATE TABLE specql_registry.tb_domain (
    pk_domain INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    identifier TEXT NOT NULL,
    description TEXT
);

COMMENT ON TABLE specql_registry.tb_domain IS 'Domain registry';
COMMENT ON COLUMN specql_registry.tb_domain.identifier IS 'Domain code (0-255)';
```

**Auto-generated GraphQL**:
```graphql
type Domain {
  pkDomain: Int!      # auto_camel_case=True
  id: UUID!
  identifier: String!
  description: String
}

type Query {
  domain(pkDomain: Int!): Domain
  domains(
    where: DomainWhereInput
    orderBy: DomainOrderBy
    limit: Int
    offset: Int
  ): [Domain!]!
}
```

### ✅ Feature #2: Custom Types and Resolvers

You can register custom types:

```python
from fraiseql import fraise_type, query
from pydantic import BaseModel

@fraise_type
class SearchResult(BaseModel):
    id: int
    title: str
    similarity: float

@query
def search_documents(query_text: str, limit: int = 10) -> list[SearchResult]:
    """Custom search resolver"""
    # Your custom logic here
    return results

app = fraiseql.create_fraiseql_app(
    types=[SearchResult],
    queries=[search_documents],
)
```

### ✅ Feature #3: CRUD Mutations

FraiseQL auto-generates mutations for discovered tables:

```graphql
mutation {
  createDomain(input: {
    identifier: "001"
    description: "Core domain"
  }) {
    domain {
      pkDomain
      identifier
    }
  }
}

mutation {
  updateDomain(pkDomain: 1, input: {
    description: "Updated description"
  }) {
    domain { pkDomain }
  }
}

mutation {
  deleteDomain(pkDomain: 1) {
    success
  }
}
```

### ✅ Feature #4: Authentication

FraiseQL supports Auth0 and custom auth:

```python
from fraiseql.auth import Auth0Config

app = fraiseql.create_fraiseql_app(
    auth=Auth0Config(
        domain="your-tenant.auth0.com",
        audience="your-api-identifier",
    ),
)
```

---

## What Doesn't Work (Missing in FraiseQL 1.5)

### ❌ Feature #1: Vector/Embedding Operators

**NOT Available**:
```graphql
# This doesn't work in FraiseQL 1.5
query {
  documents(
    where: {
      embedding: { cosineDistance: { text: "AI", threshold: 0.7 } }
    }
  ) { id }
}
```

**Current Status**: No vector operators in FraiseQL 1.5.0

**Workaround**: Use custom resolver (see Issue #1 solution above)

### ❌ Feature #2: Automatic Embedding Generation

**NOT Available**:
- No embedding service
- No auto-generate on INSERT/UPDATE
- No sentence-transformers integration

**Current Status**: Must use SpecQL's current approach

**Workaround**: Keep `src/infrastructure/services/embedding_service.py`

### ❌ Feature #3: FraiseQL Client Library

**NOT Available**:
```python
from fraiseql import FraiseQLClient  # ❌ Doesn't exist
```

**Workaround**: Use HTTPX or GQL library (see Issue #3)

### ❌ Feature #4: Vector Discovery

**NOT Available**:
- No auto-detection of `vector(384)` columns
- No HNSW index optimization
- No special handling of pgvector

**Workaround**: Manually register vector fields as `list[float]`

---

## Workarounds (Until FraiseQL Adds Vector Features)

### Workaround #1: Manual Vector Search Resolver

**File**: `src/presentation/graphql/vector_resolvers.py` (NEW)

```python
"""
Custom vector search resolvers for FraiseQL server.

These resolvers provide vector search capabilities until FraiseQL
natively supports embedding/vector operations.
"""

from fraiseql import query, fraise_type, fraise_input
from pydantic import BaseModel, Field
from typing import Optional
import os

from src.infrastructure.services.embedding_service import EmbeddingService
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)


@fraise_input
class VectorSearchInput(BaseModel):
    """Input for vector similarity search"""
    query: str = Field(description="Search query text")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    limit: int = Field(default=10, gt=0, le=100)
    category: Optional[str] = Field(default=None)


@fraise_type
class PatternSearchResult(BaseModel):
    """Pattern search result with similarity score"""
    id: int
    name: str
    category: str
    description: str
    similarity: float


@query
def search_patterns(search: VectorSearchInput) -> list[PatternSearchResult]:
    """
    Search patterns using vector similarity.

    Example:
        query {
          searchPatterns(search: {
            query: "audit logging pattern"
            threshold: 0.6
            limit: 5
          }) {
            id
            name
            category
            similarity
          }
        }
    """
    # Use SpecQL's existing embedding infrastructure
    embedding_service = EmbeddingService()
    query_embedding = embedding_service.generate_embedding(search.query)

    # Get repository
    repo = PostgreSQLPatternRepository(
        connection_string=os.getenv("DATABASE_URL")
    )

    # Perform vector search
    results = repo.search_by_embedding(
        embedding=query_embedding,
        limit=search.limit,
        threshold=search.threshold,
        category=search.category
    )

    return [
        PatternSearchResult(
            id=r['id'],
            name=r['name'],
            category=r['category'],
            description=r['description'],
            similarity=r['similarity']
        )
        for r in results
    ]


@fraise_input
class EmbeddingInput(BaseModel):
    """Input for generating embeddings"""
    text: str = Field(description="Text to embed")


@fraise_type
class EmbeddingResult(BaseModel):
    """Embedding vector result"""
    embedding: list[float]
    dimensions: int


@query
def generate_embedding(input: EmbeddingInput) -> EmbeddingResult:
    """
    Generate embedding vector for text.

    Example:
        query {
          generateEmbedding(input: { text: "some text" }) {
            embedding
            dimensions
          }
        }
    """
    service = EmbeddingService()
    embedding = service.generate_embedding(input.text)

    return EmbeddingResult(
        embedding=embedding.tolist(),
        dimensions=len(embedding)
    )
```

**Update server.py**:
```python
# src/presentation/graphql/server.py
from src.presentation.graphql.vector_resolvers import (
    search_patterns,
    generate_embedding,
    VectorSearchInput,
    EmbeddingInput,
    PatternSearchResult,
    EmbeddingResult,
)

def create_app():
    config = FraiseQLConfig(
        database_url=os.getenv("DATABASE_URL"),
        auto_camel_case=True,
    )

    app = fraiseql.create_fraiseql_app(
        types=[
            PatternSearchResult,
            EmbeddingResult,
            VectorSearchInput,
            EmbeddingInput,
        ],
        queries=[
            search_patterns,      # ← Custom vector search
            generate_embedding,   # ← Custom embedding generation
        ],
        config=config,
        auto_discover=True,
    )
    return app
```

### Workaround #2: Keep SpecQL Infrastructure

**DO NOT REMOVE** (yet):
- ✅ `src/infrastructure/services/embedding_service.py`
- ✅ `src/pattern_library/embeddings_pg.py`
- ✅ `src/generators/schema/vector_generator.py`
- ✅ `src/cli/embeddings.py`

**Rationale**: FraiseQL 1.5 doesn't have these features, so we need them.

**Update deprecation warnings**:
```python
# src/infrastructure/services/embedding_service.py
class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Remove deprecation warning - we still need this!
        # warnings.warn("... deprecated ...")  ← REMOVE THIS
        self.model = SentenceTransformer(model_name)
```

### Workaround #3: GraphQL Client Wrapper

**File**: `src/clients/fraiseql_client.py` (NEW)

```python
"""
FraiseQL GraphQL client wrapper.

Provides a simple interface for querying the FraiseQL server.
"""

import httpx
from typing import Any, Optional


class FraiseQLClient:
    """
    GraphQL client for FraiseQL server.

    Usage:
        client = FraiseQLClient("http://localhost:4000/graphql")

        result = client.query('''
            query {
              searchPatterns(search: { query: "audit" }) {
                name similarity
              }
            }
        ''')

        patterns = result['searchPatterns']
    """

    def __init__(
        self,
        url: str = "http://localhost:4000/graphql",
        headers: Optional[dict[str, str]] = None
    ):
        self.url = url
        self.headers = headers or {}
        self.client = httpx.Client()

    def query(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """
        Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables
            headers: Additional headers for this request

        Returns:
            Query result data

        Raises:
            GraphQLError: If query has errors
            HTTPError: If HTTP request fails
        """
        request_headers = {**self.headers, **(headers or {})}

        response = self.client.post(
            self.url,
            json={
                "query": query,
                "variables": variables or {}
            },
            headers=request_headers
        )

        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise GraphQLError(data["errors"])

        return data.get("data", {})

    def mutate(
        self,
        mutation: str,
        variables: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """
        Execute GraphQL mutation.

        Same as query(), but semantically clearer for mutations.
        """
        return self.query(mutation, variables, headers)

    def close(self):
        """Close HTTP client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class GraphQLError(Exception):
    """GraphQL query errors"""

    def __init__(self, errors: list[dict]):
        self.errors = errors
        messages = [e.get("message", str(e)) for e in errors]
        super().__init__(f"GraphQL errors: {', '.join(messages)}")
```

**Usage**:
```python
from src.clients.fraiseql_client import FraiseQLClient

# Pattern search via GraphQL
with FraiseQLClient() as client:
    result = client.query("""
        query SearchPatterns($query: String!) {
          searchPatterns(search: { query: $query, limit: 5 }) {
            id
            name
            category
            similarity
          }
        }
    """, variables={"query": "audit logging"})

    for pattern in result['searchPatterns']:
        print(f"{pattern['name']}: {pattern['similarity']:.3f}")
```

### Workaround #4: Hybrid Approach

**Strategy**: Use FraiseQL for CRUD, SpecQL infrastructure for vector search

```python
# src/presentation/graphql/server.py
def create_app():
    """
    Hybrid FraiseQL + SpecQL server.

    FraiseQL provides:
    - Auto-discovered CRUD operations
    - Standard GraphQL queries
    - Authentication

    SpecQL provides (via custom resolvers):
    - Vector similarity search
    - Embedding generation
    - Pattern library features
    """

    # Import SpecQL custom resolvers
    from src.presentation.graphql.vector_resolvers import (
        search_patterns,
        generate_embedding,
        # ... vector search types
    )

    # Import other custom resolvers
    from src.presentation.graphql.pattern_resolvers import (
        compile_pattern,
        validate_pattern,
        # ... pattern library features
    )

    config = FraiseQLConfig(
        database_url=os.getenv("DATABASE_URL"),
        auto_camel_case=True,
    )

    app = fraiseql.create_fraiseql_app(
        types=[
            # Vector search types
            PatternSearchResult,
            VectorSearchInput,
            # ... other custom types
        ],
        queries=[
            # Custom vector search
            search_patterns,
            generate_embedding,
            # Custom pattern operations
            compile_pattern,
            validate_pattern,
            # FraiseQL auto-discovers standard CRUD
        ],
        config=config,
        auto_discover=True,  # ← Auto CRUD + custom resolvers
    )

    return app
```

---

## Next Steps

### Short-Term (This Week)

1. **✅ Accept Reality**: FraiseQL 1.5 doesn't have vector/embedding features

2. **✅ Keep SpecQL Infrastructure**: Don't deprecate embedding code

3. **✅ Implement Hybrid Approach**:
   - Use FraiseQL for auto-discovered CRUD
   - Add custom resolvers for vector search
   - Expose SpecQL features via GraphQL

4. **✅ Create Custom Client**:
   - Implement `FraiseQLClient` wrapper (see Workaround #3)
   - Test with pattern library
   - Document usage examples

5. **✅ Update Documentation**:
   - Clarify that simplification plan is FUTURE state
   - Document current hybrid approach
   - Add "Current Limitations" section

### Medium-Term (Next Month)

6. **Contact FraiseQL Maintainers**:
   - Ask about roadmap for vector/embedding features
   - Share our requirements and use cases
   - Offer to contribute if features are planned

7. **Evaluate Alternatives**:
   - Option A: Wait for FraiseQL update
   - Option B: Fork FraiseQL and add vector features
   - Option C: Use different GraphQL framework (Strawberry, Ariadne)
   - Option D: Keep hybrid approach long-term

8. **Contribute to FraiseQL** (if possible):
   - Propose vector operator design
   - Implement pgvector integration
   - Add embedding service plugin system

### Long-Term (Next Quarter)

9. **If FraiseQL Adds Features**:
   - Migrate custom resolvers to native operators
   - Implement simplification plan
   - Remove SpecQL infrastructure

10. **If FraiseQL Doesn't Add Features**:
    - Formalize hybrid approach as permanent solution
    - Improve custom vector resolvers
    - Consider alternative GraphQL framework

---

## Testing Current Setup

### Test #1: Server Starts
```bash
$ DATABASE_URL="postgresql://..." python -m uvicorn src.presentation.graphql.server:app --host 127.0.0.1 --port 4000

# Expected: Server starts, no errors
# URL: http://localhost:4000/graphql
```

### Test #2: GraphQL Playground
```bash
# Open browser: http://localhost:4000/graphql

# Try introspection query:
query {
  __schema {
    types {
      name
    }
  }
}

# Expected: List of types including auto-discovered Domain, Subdomain, etc.
```

### Test #3: Custom Vector Search Resolver

**After implementing Workaround #1**:

```graphql
query TestVectorSearch {
  searchPatterns(search: {
    query: "audit logging pattern"
    threshold: 0.6
    limit: 5
  }) {
    id
    name
    category
    description
    similarity
  }
}

# Expected: List of similar patterns with similarity scores
```

### Test #4: Client Library

**After implementing Workaround #3**:

```python
from src.clients.fraiseql_client import FraiseQLClient

client = FraiseQLClient("http://localhost:4000/graphql")

result = client.query("""
    query {
      domains { id identifier description }
    }
""")

print(result)
# Expected: List of domains from specql_registry
```

---

## Summary

### Current Reality
- ✅ FraiseQL 1.5 installed and working
- ✅ Server starts successfully
- ✅ Auto-discovery works
- ❌ NO vector/embedding features
- ❌ NO FraiseQLClient
- ❌ Config embeddings section ignored

### What Team Should Do
1. **Stop trying to use non-existent features**
2. **Implement custom resolvers** for vector search (Workaround #1)
3. **Keep SpecQL infrastructure** (don't remove yet)
4. **Create client wrapper** (Workaround #3)
5. **Use hybrid approach** (FraiseQL CRUD + SpecQL vectors)

### Simplification Plan Status
- **Status**: BLOCKED - awaiting FraiseQL vector features
- **Timeline**: Unknown (FraiseQL roadmap unclear)
- **Alternative**: Hybrid approach (documented above)

### Questions for FraiseQL Team
1. Are vector/embedding features planned?
2. What's the timeline for these features?
3. Would you accept contributions for this functionality?
4. Is there a plugin system we could use?

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Status**: Active troubleshooting in progress
**Next Review**: After contacting FraiseQL maintainers
