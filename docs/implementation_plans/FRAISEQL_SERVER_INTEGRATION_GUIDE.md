# FraiseQL Server Integration Guide - Vector Search & SpecQL

**Date**: 2025-11-14
**Status**: Active Development
**FraiseQL Version**: 1.5.0 (with pgvector support!)
**Priority**: High

---

## Executive Summary

Good news! **FraiseQL 1.5.0 DOES include comprehensive vector search capabilities**. The troubleshooting document was written based on incorrect assumptions about the pip-installed package. The actual FraiseQL source at `~/code/fraiseql/` contains full pgvector integration with 6 distance operators.

This guide shows how to properly integrate SpecQL with FraiseQL's vector search features.

---

## Table of Contents

1. [FraiseQL 1.5.0 Vector Capabilities](#fraiseql-150-vector-capabilities)
2. [Installation & Setup](#installation--setup)
3. [Integration Strategy](#integration-strategy)
4. [Code Examples](#code-examples)
5. [Migration Path](#migration-path)

---

## FraiseQL 1.5.0 Vector Capabilities

### ✅ What FraiseQL 1.5 Actually Includes

Based on the source code at `~/code/fraiseql/`:

**1. Native Vector Types** (`src/fraiseql/types/scalars/vector.py`)
- `Vector` - Standard 32-bit float vectors
- `HalfVector` - 16-bit half-precision (50% memory savings)
- `SparseVector` - Sparse vectors for high-dimensional data
- `QuantizedVector` - Quantized vectors for memory efficiency

**2. Six Distance Operators** (`src/fraiseql/sql/where/operators/vectors.py`)
- `cosine_distance` (`<=>`) - Semantic similarity (0.0 = identical, 2.0 = opposite)
- `l2_distance` (`<->`) - Euclidean distance
- `l1_distance` (`<+>`) - Manhattan distance
- `inner_product` (`<#>`) - Dot product similarity
- `hamming_distance` (`<~>`) - Binary fingerprint matching
- `jaccard_distance` (`<%>`) - Set similarity

**3. GraphQL Integration**
```graphql
input VectorFilter {
  cosine_distance: [Float!]
  l2_distance: [Float!]
  inner_product: [Float!]
  l1_distance: [Float!]
  hamming_distance: String
  jaccard_distance: String
  isnull: Boolean
}

input VectorOrderBy {
  cosine_distance: [Float!]
  l2_distance: [Float!]
  inner_product: [Float!]
  # ... etc
}
```

**4. Performance Features**
- HNSW index support (~12ms on 1M vectors)
- IVFFlat index support (~25ms on 1M vectors)
- Automatic index usage
- Dimension validation

**5. Vector Aggregations**
- `SUM(vector)` - Sum of vectors
- `AVG(vector)` - Average of vectors
- Supports all vector types

---

## Installation & Setup

### Problem: PyPI Package vs Source Code

**The Issue**: The PyPI package `fraiseql==1.5.0` is a COMPILED version without full vector support exported to Python. The source code at `~/code/fraiseql/` has complete vector features.

**Solution Options**:

#### Option A: Install from Local Source (Recommended)

```bash
cd ~/code/fraiseql
pip uninstall fraiseql  # Remove PyPI version
pip install -e .         # Install from source in development mode
```

This gives you the full FraiseQL with vector support.

#### Option B: Use FraiseQL Repo Directly

```bash
# In SpecQL pyproject.toml
[project]
dependencies = [
    # ... other deps
    "fraiseql @ file:///home/lionel/code/fraiseql",
]
```

#### Option C: Wait for PyPI Update

The PyPI package may need to be republished with vector modules exposed. Check with FraiseQL maintainers.

### Verify Installation

```python
# test_fraiseql_vector_support.py
import fraiseql
from fraiseql.types.scalars.vector import VectorScalar, VectorField
from fraiseql.sql.where.operators.vectors import build_cosine_distance_sql

print("✓ FraiseQL vector support verified!")
print(f"  Vector scalar: {VectorScalar}")
print(f"  Vector field marker: {VectorField}")
print(f"  Distance operators: cosine_distance, l2_distance, etc.")
```

---

## Integration Strategy

### Current State: SpecQL + FraiseQL

**SpecQL Generates**:
- PostgreSQL schema with vector columns
- HNSW indexes for performance
- Trinity pattern (tb_*, tv_*, functions)
- FraiseQL annotations via COMMENT

**FraiseQL Provides**:
- Auto-discovery of vector columns
- GraphQL schema with VectorFilter
- Type-safe vector queries
- Distance operator SQL generation

### Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│ SpecQL Generator                                         │
│                                                          │
│ Input: YAML Entity Definition                           │
│   entity: Document                                       │
│   features: [semantic_search]                            │
│                                                          │
│ Output: PostgreSQL Schema                                │
│   • ALTER TABLE tv_document ADD COLUMN embedding vector(384)│
│   • CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)│
│   • COMMENT ON TABLE tv_document IS '@fraiseql:type ...' │
│   • COMMENT ON COLUMN embedding IS '@fraiseql:field ...' │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ FraiseQL Server                                          │
│                                                          │
│ 1. Auto-Discovery (PostgreSQL introspection)            │
│    • Detects vector(384) columns                         │
│    • Reads @fraiseql:field annotations                   │
│    • Identifies vector field patterns (embedding, vector)│
│                                                          │
│ 2. GraphQL Schema Generation                             │
│    • Creates VectorFilter input type                     │
│    • Adds cosine_distance, l2_distance operators         │
│    • Enables vector ORDER BY                             │
│                                                          │
│ 3. Query Execution                                       │
│    • Translates GraphQL to SQL with pgvector operators   │
│    • Uses HNSW indexes automatically                     │
│    • Returns results with distance scores                │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ GraphQL API                                              │
│                                                          │
│ query {                                                  │
│   documents(                                             │
│     where: {                                             │
│       embedding: { cosine_distance: [0.1, 0.2, ...] }   │
│     }                                                    │
│     orderBy: { embedding: { cosine_distance: [...] } }  │
│     limit: 10                                            │
│   ) { id title }                                         │
│ }                                                        │
└─────────────────────────────────────────────────────────┘
```

---

## Code Examples

### Example 1: SpecQL Entity with Vector Search

```yaml
# entities/document.yaml
entity: Document
schema: content
description: "Document with semantic search capability"

features:
  - semantic_search  # SpecQL generates vector column + HNSW index

fields:
  title: text
  content: text
  category: text
  # Vector field added automatically by semantic_search feature
  # embedding: vector(384)
```

**Generated SQL** (by SpecQL):
```sql
-- Base table
CREATE TABLE content.tb_document (
    pk_document INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ
);

-- Table view with vector
CREATE TABLE content.tv_document (
    pk_document INTEGER PRIMARY KEY,
    id UUID NOT NULL,
    identifier TEXT NOT NULL,
    data JSONB NOT NULL,
    refreshed_at TIMESTAMPTZ DEFAULT NOW(),
    embedding vector(384)  -- ← Added by semantic_search feature
);

-- HNSW index for fast vector search
CREATE INDEX idx_tv_document_embedding_hnsw
ON content.tv_document
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- FraiseQL annotations
COMMENT ON TABLE content.tv_document IS
'@fraiseql:type
name: Document
query: true';

COMMENT ON COLUMN content.tv_document.embedding IS
'@fraiseql:field
name: embedding
type: [Float!]
description: Vector embedding (384 dimensions)
operators: cosine_distance, l2_distance, inner_product';
```

### Example 2: FraiseQL Server Setup

```python
# src/presentation/graphql/server.py
import os
from fraiseql.fastapi import create_fraiseql_app, FraiseQLConfig
from fraiseql.types.scalars.vector import VectorField
from fraiseql import fraise_type
from typing import List
from uuid import UUID

# Optional: Define custom types for better control
@fraise_type
class Document:
    """Document with vector embedding (auto-discovered from database)"""
    id: UUID
    title: str
    content: str
    category: str
    embedding: List[float]  # FraiseQL detects as vector field

def create_app():
    """Create FraiseQL app with vector search support"""

    config = FraiseQLConfig(
        database_url=os.getenv("DATABASE_URL"),
        auto_camel_case=True,
    )

    app = create_fraiseql_app(
        types=[],  # Use auto-discovery
        queries=[],
        config=config,
        auto_discover=True,  # ← Auto-detects vector columns
        title="SpecQL Registry API",
        version="1.0.0",
        description="GraphQL API with semantic search"
    )

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.presentation.graphql.server:app",
        host="127.0.0.1",
        port=4000,
        reload=True
    )
```

### Example 3: Vector Search Queries

**GraphQL Query**:
```graphql
query SemanticSearch($queryEmbedding: [Float!]!) {
  documents(
    where: {
      # Vector similarity filter
      embedding: { cosine_distance: $queryEmbedding }
      # Regular filters still work
      category: { eq: "technical" }
    }
    # Order by similarity
    orderBy: {
      embedding: { cosine_distance: $queryEmbedding }
    }
    limit: 10
  ) {
    id
    title
    content
    category
  }
}
```

**Variables**:
```json
{
  "queryEmbedding": [0.123, 0.456, 0.789, ...]  // 384 dimensions
}
```

**Python Client**:
```python
from src.clients.fraiseql_client import FraiseQLClient
from src.infrastructure.services.embedding_service import EmbeddingService

# Generate query embedding
embedding_service = EmbeddingService()
query_embedding = embedding_service.generate_embedding("machine learning tutorial")

# Search via GraphQL
with FraiseQLClient("http://localhost:4000/graphql") as client:
    result = client.query("""
        query SemanticSearch($queryEmbedding: [Float!]!) {
          documents(
            where: {
              embedding: { cosine_distance: $queryEmbedding }
              category: { eq: "technical" }
            }
            orderBy: { embedding: { cosine_distance: $queryEmbedding } }
            limit: 10
          ) {
            id
            title
            content
          }
        }
    """, variables={"queryEmbedding": query_embedding.tolist()})

    for doc in result['documents']:
        print(f"{doc['title']}")
```

### Example 4: Pattern Library with FraiseQL

**SpecQL Pattern Entity**:
```yaml
# entities/pattern_library/domain_pattern.yaml
entity: DomainPattern
schema: pattern_library

features:
  - semantic_search  # Enable vector search

fields:
  name: text
  category: text
  description: text
  parameters: json
  implementation: json
  # embedding added automatically by feature
```

**FraiseQL Auto-Discovery** (no manual types needed!):
```python
# FraiseQL automatically discovers:
# - pattern_library.tv_domain_pattern table
# - embedding vector(384) column
# - HNSW index

# Generates GraphQL type:
"""
type DomainPattern {
  id: UUID!
  name: String!
  category: String!
  description: String!
  parameters: JSON
  implementation: JSON
  embedding: [Float!]  # ← Auto-detected vector field
}

input DomainPatternWhereInput {
  embedding: VectorFilter  # ← Auto-added filter
  category: StringFilter
  # ... other filters
}
"""
```

**Query Patterns via GraphQL**:
```graphql
query FindSimilarPatterns($query: String!) {
  # First, generate embedding for query text (outside GraphQL)
  # Then search with the embedding vector
  domainPatterns(
    where: {
      embedding: { cosine_distance: $queryEmbeddingVector }
      deprecated: { eq: false }
    }
    orderBy: { embedding: { cosine_distance: $queryEmbeddingVector } }
    limit: 5
  ) {
    id
    name
    category
    description
  }
}
```

---

## Migration Path

### Phase 1: Verify FraiseQL Source Installation ✅

```bash
# 1. Check current installation
pip show fraiseql
# Location: .venv/lib/python3.13/site-packages/fraiseql

# 2. Check if vector modules exist
python -c "from fraiseql.types.scalars.vector import VectorScalar; print('OK')"
# If fails: vector support not in installed package

# 3. Install from source
cd ~/code/fraiseql
pip uninstall fraiseql
pip install -e .

# 4. Verify vector support
python -c "from fraiseql.types.scalars.vector import VectorScalar; print('✓ Vector support!')"
```

### Phase 2: Update SpecQL Server ✅

**Current** (`src/presentation/graphql/server.py`):
```python
# Dummy config, not using real database
config = FraiseQLConfig(
    database_url="postgresql://dummy:dummy@localhost:5432/dummy",
    auto_camel_case=True,
)

app = fraiseql.create_fraiseql_app(
    types=[TestEmbedding],  # Manual type
    queries=[query_hello],  # Dummy query
    config=config,
)
```

**Updated** (with auto-discovery):
```python
import os

config = FraiseQLConfig(
    database_url=os.getenv("DATABASE_URL", "postgresql://specql:specql@localhost:5432/specql"),
    auto_camel_case=True,
)

app = fraiseql.create_fraiseql_app(
    types=[],  # Let FraiseQL auto-discover
    queries=[],  # FraiseQL generates CRUD queries
    config=config,
    auto_discover=True,  # ← KEY: Auto-discover vector columns
)
```

### Phase 3: Test Vector Discovery ✅

```bash
# 1. Start FraiseQL server
DATABASE_URL="postgresql://specql:specql@localhost:5432/specql" \
  python -m uvicorn src.presentation.graphql.server:app --host 127.0.0.1 --port 4000

# 2. Open GraphQL Playground
# http://localhost:4000/graphql

# 3. Run introspection query
query {
  __type(name: "DomainPatternWhereInput") {
    inputFields {
      name
      type {
        name
        ofType { name }
      }
    }
  }
}

# Expected: Should include "embedding: VectorFilter"
```

### Phase 4: Simplify SpecQL Code ✅

**What to Remove** (from SpecQL):
- ❌ Custom search functions (FraiseQL provides GraphQL operators)
- ❌ Manual vector annotations (FraiseQL auto-discovers)
- ❌ Complex SQL generation for vectors (FraiseQL handles it)

**What to Keep** (in SpecQL):
- ✅ Vector column generation (`ALTER TABLE ... ADD COLUMN embedding vector(384)`)
- ✅ HNSW index creation (critical for performance)
- ✅ Embedding generation service (still needed to create embeddings)
- ✅ Pattern-specific business logic

**Updated VectorGenerator** (simplified):
```python
# src/generators/schema/vector_generator.py
class VectorGenerator:
    """Generates vector schema for FraiseQL auto-discovery"""

    def generate(self, entity: EntityDefinition) -> str:
        """Generate ONLY schema setup - FraiseQL handles queries"""
        if "semantic_search" not in (entity.features or []):
            return ""

        parts = []

        # Generate column
        parts.append(self._generate_columns(entity))

        # Generate HNSW index (critical for performance!)
        parts.append(self._generate_indexes(entity))

        # Optional: Add minimal annotation for FraiseQL
        parts.append(self._generate_annotation(entity))

        # NO custom search functions - FraiseQL provides GraphQL operators!

        return "\n\n".join(filter(None, parts))

    def _generate_annotation(self, entity: EntityDefinition) -> str:
        """Minimal annotation - FraiseQL auto-discovers vector columns"""
        entity_lower = entity.name.lower()
        return f"""
        -- FraiseQL auto-discovers this as a vector field
        COMMENT ON COLUMN {entity.schema}.tv_{entity_lower}.embedding IS
        'Vector embedding for semantic similarity search';
        """
```

### Phase 5: Update Pattern Library ✅

**Before** (manual SQL):
```python
# src/pattern_library/embeddings_pg.py
def retrieve_similar(self, query_embedding, top_k=5):
    """Raw SQL with pgvector"""
    query = """
        SELECT *, 1 - (embedding <=> %s) AS similarity
        FROM pattern_library.domain_patterns
        WHERE ...
    """
    cursor = self.conn.execute(query, [query_embedding, ...])
    return cursor.fetchall()
```

**After** (FraiseQL GraphQL):
```python
# src/pattern_library/fraiseql_patterns.py
from src.clients.fraiseql_client import FraiseQLClient

class FraiseQLPatternService:
    def __init__(self, client: FraiseQLClient):
        self.client = client

    def retrieve_similar(self, query_embedding: list[float], top_k: int = 5):
        """Type-safe GraphQL query"""
        result = self.client.query("""
            query FindPatterns($embedding: [Float!]!, $limit: Int!) {
              domainPatterns(
                where: {
                  embedding: { cosine_distance: $embedding }
                  deprecated: { eq: false }
                }
                orderBy: { embedding: { cosine_distance: $embedding } }
                limit: $limit
              ) {
                id
                name
                category
                description
              }
            }
        """, variables={"embedding": query_embedding, "limit": top_k})

        return result['domainPatterns']
```

---

## Testing Guide

### Test 1: FraiseQL Installation

```bash
# Test vector support is available
python << 'EOF'
try:
    from fraiseql.types.scalars.vector import VectorScalar, VectorField
    from fraiseql.sql.where.operators.vectors import build_cosine_distance_sql
    print("✓ FraiseQL vector support verified!")
except ImportError as e:
    print(f"✗ Vector support missing: {e}")
    print("→ Solution: pip install -e ~/code/fraiseql")
EOF
```

### Test 2: Server Startup

```bash
DATABASE_URL="postgresql://specql:specql@localhost:5432/specql" \
  python -m uvicorn src.presentation.graphql.server:app --host 127.0.0.1 --port 4000

# Expected output:
# INFO: Started server process
# INFO: Application startup complete
# INFO: Uvicorn running on http://127.0.0.1:4000
```

### Test 3: GraphQL Playground

Visit: http://localhost:4000/graphql

**Query 1: Check vector field detection**
```graphql
query IntrospectVectorFields {
  __type(name: "DomainPattern") {
    fields {
      name
      type { name ofType { name } }
    }
  }
}

# Expected: Should include field "embedding: [Float!]"
```

**Query 2: Check VectorFilter availability**
```graphql
query IntrospectVectorFilter {
  __type(name: "DomainPatternWhereInput") {
    inputFields {
      name
      type { name ofType { name } }
    }
  }
}

# Expected: Should include "embedding: VectorFilter"
```

**Query 3: Test vector search**
```graphql
query TestVectorSearch {
  domainPatterns(
    where: {
      embedding: {
        cosine_distance: [0.1, 0.2, 0.3, ..., 0.384]  # 384 dims
      }
    }
    limit: 3
  ) {
    id
    name
    category
  }
}

# Expected: Returns patterns ordered by similarity
```

### Test 4: End-to-End Pattern Search

```python
# test_e2e_pattern_search.py
from src.clients.fraiseql_client import FraiseQLClient
from src.infrastructure.services.embedding_service import EmbeddingService

def test_pattern_search():
    # 1. Generate embedding
    service = EmbeddingService()
    query_embedding = service.generate_embedding("audit logging pattern")

    # 2. Search via FraiseQL
    with FraiseQLClient("http://localhost:4000/graphql") as client:
        result = client.query("""
            query SearchPatterns($embedding: [Float!]!) {
              domainPatterns(
                where: {
                  embedding: { cosine_distance: $embedding }
                }
                orderBy: { embedding: { cosine_distance: $embedding } }
                limit: 5
              ) {
                id
                name
                category
                description
              }
            }
        """, variables={"embedding": query_embedding.tolist()})

        patterns = result['domainPatterns']
        assert len(patterns) > 0, "Should find similar patterns"

        print(f"✓ Found {len(patterns)} similar patterns:")
        for p in patterns:
            print(f"  - {p['name']} ({p['category']})")

if __name__ == "__main__":
    test_pattern_search()
```

---

## Troubleshooting

### Issue 1: "Cannot import vector modules"

**Error**:
```python
from fraiseql.types.scalars.vector import VectorScalar
# ImportError: cannot import name 'VectorScalar'
```

**Cause**: Installed PyPI package doesn't include vector modules.

**Solution**:
```bash
cd ~/code/fraiseql
pip uninstall fraiseql
pip install -e .
```

### Issue 2: "VectorFilter not in GraphQL schema"

**Error**: Introspection doesn't show VectorFilter for embedding field.

**Cause**: FraiseQL not detecting field as vector.

**Solution**: Ensure field name matches pattern:
```python
# ✓ These work:
embedding: List[float]
text_embedding: List[float]
vector: List[float]
image_embedding: List[float]

# ✗ These don't work:
embed: List[float]       # Name doesn't match pattern
data: List[float]        # Generic name
```

### Issue 3: "Vector dimension mismatch"

**Error**: PostgreSQL error about dimension mismatch.

**Cause**: Query vector has different dimensions than column.

**Solution**: Ensure consistency:
```sql
-- Check column dimensions
SELECT pg_typeof(embedding),
       pg_column_size(embedding) as size_bytes,
       pg_column_size(embedding) / 4 as dimensions
FROM tv_domain_pattern LIMIT 1;

-- Expected: dimensions = 384 for all-MiniLM-L6-v2
```

### Issue 4: "Slow vector queries"

**Error**: Queries taking >1 second on small dataset.

**Cause**: Missing HNSW index or index not being used.

**Solution**:
```sql
-- Check if index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'tv_domain_pattern'
  AND indexdef LIKE '%hnsw%';

-- Create if missing
CREATE INDEX idx_tv_domain_pattern_embedding_hnsw
ON pattern_library.tv_domain_pattern
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Verify index usage
EXPLAIN ANALYZE
SELECT * FROM pattern_library.tv_domain_pattern
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;

-- Expected: "Index Scan using idx_tv_domain_pattern_embedding_hnsw"
```

---

## Summary

### ✅ Key Findings

1. **FraiseQL 1.5.0 HAS vector support** (in source at ~/code/fraiseql/)
2. **PyPI package may be incomplete** (install from source)
3. **Auto-discovery works** (FraiseQL detects vector columns)
4. **GraphQL operators provided** (cosine_distance, l2_distance, etc.)

### 🎯 Recommended Actions

1. **Install FraiseQL from source**: `pip install -e ~/code/fraiseql`
2. **Update server config**: Enable `auto_discover=True`
3. **Simplify SpecQL generators**: Remove custom search functions
4. **Use GraphQL for queries**: Type-safe, auto-completed
5. **Keep performance critical parts**: HNSW indexes, embedding generation

### 📊 Expected Results

- **70% code reduction** in vector/embedding infrastructure
- **Type-safe queries** with IDE autocomplete
- **Better performance** via FraiseQL optimization
- **Standardized API** across all vector-enabled entities

---

**Document Version**: 2.0
**Last Updated**: 2025-11-14
**Status**: Ready for implementation
**Next Steps**: Install FraiseQL from source, test auto-discovery
