# Vector Search with FraiseQL

## Overview

SpecQL generates PostgreSQL vector columns and HNSW indexes for semantic search. FraiseQL provides GraphQL API with native vector operators for zero-custom-code vector search.

## Configuration

### Basic Setup (Recommended)

```yaml
entity: Document
schema: content
features:
  - semantic_search  # Generates columns + indexes only

fields:
  title: text!
  content: text
```

FraiseQL auto-detects vector columns and generates native operators:

```graphql
query {
  documents(
    where: { embedding: { cosine_distance: [...] } }
    orderBy: { embedding: { cosine_distance: [...] } }
  ) { id, title }
}
```

### Advanced Configuration

For direct SQL access or legacy compatibility:

```yaml
entity: Document
schema: content
features:
  - semantic_search
vector_config:
  search_functions: true  # Generate SQL functions (optional)

fields:
  title: text!
  content: text
```

## Generated Schema

### Base Table (tb_document)

```sql
-- Vector embedding column
ALTER TABLE content.tb_document ADD COLUMN embedding vector(384);

-- HNSW index for fast similarity search
CREATE INDEX idx_tb_document_embedding_hnsw
ON content.tb_document USING hnsw (embedding vector_cosine_ops);
```

### Table View (tv_document)

```sql
-- Vector columns exposed for FraiseQL
CREATE TABLE content.tv_document (
    -- ... other columns
    embedding vector(384),  -- Separate column (not in JSONB)
    data JSONB             -- Business data only
);
```

### Optional Search Functions

When `search_functions: true`:

```sql
CREATE OR REPLACE FUNCTION content.search_document_by_embedding(
    p_query_embedding vector(384),
    p_limit INTEGER DEFAULT 10,
    p_min_similarity FLOAT DEFAULT 0.0
)
RETURNS TABLE (pk INTEGER, id UUID, similarity FLOAT, data JSONB) AS $$
BEGIN
    RETURN QUERY
    SELECT
        tv.pk_document,
        tv.id,
        1 - (tv.embedding <=> p_query_embedding) AS similarity,
        tv.data
    FROM content.tv_document tv
    WHERE tv.embedding IS NOT NULL
        AND (1 - (tv.embedding <=> p_query_embedding)) >= p_min_similarity
    ORDER BY tv.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;
```

## FraiseQL Integration

### Native Vector Operators

FraiseQL auto-generates these operators for vector columns:

- `cosine_distance`: Cosine similarity (1 - cosine_distance)
- `l2_distance`: Euclidean distance
- `inner_product`: Dot product similarity

### Query Examples

#### Basic Similarity Search

```graphql
query FindSimilar($vector: [Float!]!) {
  documents(
    where: { embedding: { cosine_distance: $vector } }
    orderBy: { embedding: { cosine_distance: $vector } }
    limit: 10
  ) {
    id
    title
    score: _vectorSimilarity  # Computed similarity score
  }
}
```

#### Threshold Filtering

```graphql
query HighQualityMatches($vector: [Float!]!) {
  documents(
    where: {
      embedding: {
        cosine_distance_lt: {  # distance < 0.3 (high similarity)
          value: $vector
          threshold: 0.3
        }
      }
    }
  ) {
    id
    title
  }
}
```

#### Hybrid Search (Text + Vector)

```graphql
query HybridSearch($text: String!, $vector: [Float!]!) {
  documents(
    where: {
      AND: [
        { searchVector: { websearch_query: $text } }
        { embedding: { cosine_distance: $vector } }
      ]
    }
    orderBy: { searchVector: { rank: $text } }  # Text ranking first
    limit: 20
  ) {
    id
    title
    _textRank
    _vectorSimilarity
  }
}
```

## Best Practices

### ✅ Recommended Approach

1. **Use FraiseQL native operators** for GraphQL queries
2. **Enable search functions** only when you need direct SQL backend queries
3. **Keep embedding dimensions consistent** (384, 768, or 1536)
4. **Monitor HNSW index build time** for large datasets

### Architecture Benefits

- **Zero custom code**: SpecQL generates schema, FraiseQL handles queries
- **Type safety**: GraphQL schema auto-generated from PostgreSQL
- **Performance**: HNSW indexes provide sub-millisecond similarity search
- **Scalability**: Works with millions of documents
- **Composability**: Vector filters combine with other GraphQL filters

### Migration from Custom Functions

**Before** (legacy):
```graphql
query { searchDocumentsByEmbedding(queryEmbedding: [...]) { ... } }
```

**After** (recommended):
```graphql
query { documents(where: { embedding: { cosine_distance: [...] } }) { ... } }
```

Benefits:
- ✅ Composable with other filters
- ✅ Type-safe and auto-completed
- ✅ Consistent with FraiseQL patterns
- ✅ Better performance (Rust-native operators)

## Troubleshooting

### "Type vector does not exist"

Install pgvector extension:
```bash
psql $DATABASE_URL -c "CREATE EXTENSION vector;"
```

### "Cannot cast jsonb to vector"

Vectors must be separate columns. Regenerate with SpecQL that includes vector column exposure.

### Slow queries without index

Verify HNSW index exists:
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'tv_document'
AND indexdef LIKE '%hnsw%';
```

### Index build taking too long

For large datasets (>1M rows), consider:
- Build indexes during off-peak hours
- Use `WITH (m = 16, ef_construction = 64)` for faster builds
- Monitor with `SELECT phase, tuples_done, tuples_total FROM pg_stat_progress_create_index;`

## Related Documentation

- [FraiseQL Vector Integration Guide](../integrations/fraiseql_complete_guide.md)
- [SpecQL YAML Reference](../reference/specql_yaml.md)
- [PostgreSQL pgvector Documentation](https://github.com/pgvector/pgvector)