# Semantic Pattern Search

**Feature**: AI-powered pattern discovery using natural language
**Status**: ✅ Complete
**Version**: 1.0.0

---

## Overview

Semantic Pattern Search uses AI embeddings to enable natural language pattern discovery. Instead of exact keyword matching, it understands the *meaning* of your query to find relevant patterns.

### Key Features

- **Natural Language Queries**: Search using plain English
- **Semantic Understanding**: Finds patterns by meaning, not just keywords
- **Similarity Search**: Discover related patterns
- **Smart Recommendations**: Get pattern suggestions for entities
- **Fast**: <100ms search latency with pgvector indexes

---

## How It Works

### 1. Embedding Generation

Each pattern is converted to a 384-dimensional vector embedding that captures its semantic meaning:

```
Pattern: "email_validation"
Description: "Validates email addresses using RFC 5322 regex"

↓ sentence-transformers (all-MiniLM-L6-v2)

Embedding: [0.234, -0.512, 0.891, ..., 0.123]  # 384 dimensions
```

### 2. Similarity Search

Query embeddings are compared using cosine similarity:

```
Query: "validate email addresses"
↓ embedding
Query Vector: [0.241, -0.498, 0.887, ...]

↓ cosine similarity with all patterns

Results (sorted by similarity):
1. email_validation       (0.952 similarity)
2. contact_validation     (0.827 similarity)
3. user_input_validation  (0.683 similarity)
```

### 3. pgvector Indexing

PostgreSQL's pgvector extension provides efficient vector search:

```sql
-- HNSW index for fast approximate nearest neighbor search
CREATE INDEX idx_patterns_embedding ON domain_patterns
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Search using <=> operator (cosine distance)
SELECT name, 1 - (embedding <=> query_vector) as similarity
FROM domain_patterns
ORDER BY embedding <=> query_vector
LIMIT 10;
```

---

## CLI Usage

### Natural Language Search

Search patterns using plain English:

```bash
# Basic search
specql patterns search "validate email addresses"

# With filters
specql patterns search "audit logging" --category infrastructure --limit 10 --min-similarity 0.7

# Output:
# 🔍 Searching for: 'validate email addresses'
#    Minimum similarity: 0.5
#
# Found 3 pattern(s):
#
# 1. email_validation (95.2% match)
#    Category: validation
#    Description: Validates email addresses using RFC 5322 regex pattern...
#    Used 12 times
#
# 2. contact_validation (82.7% match)
#    Category: validation
#    Description: Validates contact information including email and phone...
#
# 3. user_input_validation (68.3% match)
#    Category: validation
#    Description: Validates all user input fields...
```

### Find Similar Patterns

Discover patterns related to a known pattern:

```bash
# Find patterns similar to email_validation
specql patterns similar email_validation --limit 5

# Output:
# 🔍 Finding patterns similar to: email_validation
#    Validates email addresses using RFC 5322 regex pattern
#
# Found 5 similar pattern(s):
#
# 1. phone_validation (87.3% similar)
#    Validates phone numbers in multiple formats...
#
# 2. contact_info_validation (79.1% similar)
#    Comprehensive contact information validation...
```

### Get Pattern Recommendations

Get pattern suggestions for an entity:

```bash
specql patterns recommend \
  --entity-description "Customer contact with email and phone" \
  --field email \
  --field phone \
  --field company \
  --limit 5

# Output:
# 🎯 Pattern recommendations for:
#    Entity: Customer contact with email and phone
#    Fields: email, phone, company
#
# 💡 Recommended 5 pattern(s):
#
# 1. email_validation (88.4% match)
#    Validates email addresses using RFC 5322 regex pattern
#    ⭐ Popular: Used 12 times
#
# 2. phone_validation (85.2% match)
#    Validates phone numbers in multiple formats
#    ⭐ Popular: Used 8 times
```

---

## Programmatic Usage

### Using PatternService

```python
from src.application.services.pattern_service_factory import get_pattern_service_with_fallback

# Get service
service = get_pattern_service_with_fallback()

# Natural language search
results = service.search_patterns_semantic(
    query="validate user input",
    limit=10,
    min_similarity=0.6
)

for pattern, similarity in results:
    print(f"{pattern.name}: {similarity:.2%} match")
    print(f"  {pattern.description}")

# Find similar patterns
similar = service.find_similar_patterns(
    pattern_id=123,
    limit=5,
    min_similarity=0.7
)

# Get recommendations
recommendations = service.recommend_patterns_for_entity(
    entity_description="User profile",
    field_names=["email", "username", "password"],
    limit=5
)
```

### Using EmbeddingService Directly

```python
from src.infrastructure.services.embedding_service import get_embedding_service

# Get service
embedding_service = get_embedding_service()

# Generate single embedding
text = "Email validation pattern"
embedding = embedding_service.generate_embedding(text)
print(f"Embedding dimension: {embedding.shape}")  # (384,)

# Generate batch
texts = ["Email validation", "Phone validation", "Address validation"]
embeddings = embedding_service.generate_embeddings_batch(texts)
print(f"Batch shape: {embeddings.shape}")  # (3, 384)

# Calculate similarity
emb1 = embedding_service.generate_embedding("email validation")
emb2 = embedding_service.generate_embedding("email checking")
similarity = embedding_service.cosine_similarity(emb1, emb2)
print(f"Similarity: {similarity:.2%}")  # 89%
```

---

## Example Use Cases

### Use Case 1: Finding Validation Patterns

**Scenario**: You need to validate user input fields

```bash
# Search for validation patterns
specql patterns search "validate user input fields" --category validation

# Results:
# 1. email_validation (92% match)
# 2. phone_validation (88% match)
# 3. user_input_validation (85% match)
# 4. form_validation (78% match)
```

### Use Case 2: Building New Entity

**Scenario**: Creating a new Customer entity, need pattern suggestions

```bash
specql patterns recommend \
  --entity-description "Customer with contact and order history" \
  --field email \
  --field phone \
  --field orders \
  --field address

# Recommendations:
# 1. email_validation (91% match) - Validates email addresses
# 2. phone_validation (89% match) - Validates phone numbers
# 3. audit_trail (85% match) - Tracks all changes to records
# 4. soft_delete (82% match) - Prevents permanent deletion
# 5. contact_info (78% match) - Standard contact fields
```

### Use Case 3: Pattern Discovery

**Scenario**: Exploring what patterns exist for infrastructure

```bash
specql patterns search "database connection and performance" --category infrastructure --min-similarity 0.6

# Results:
# 1. connection_pooling (89% match)
# 2. database_monitoring (84% match)
# 3. performance_logging (79% match)
# 4. connection_retry (76% match)
```

---

## Architecture

### Components

1. **EmbeddingService**: Generates vector embeddings using sentence-transformers
2. **PatternRepository**: Stores and retrieves patterns with vector search
3. **PatternService**: Business logic for pattern operations
4. **CLI Commands**: User interface for semantic search

### Data Flow

```
User Query → EmbeddingService → Vector → pgvector Search → Pattern Results
     ↓              ↓              ↓              ↓              ↓
"validate email" → [0.234,...] → Cosine Similarity → Ranked Patterns → Display
```

### Performance Characteristics

- **Embedding Generation**: ~5ms per text (CPU)
- **Vector Search**: <10ms per query (with HNSW index)
- **Batch Processing**: 100+ texts/second
- **Memory Usage**: ~200MB for sentence-transformers model

---

## Implementation Details

### Database Schema

```sql
-- Vector embedding column
ALTER TABLE pattern_library.domain_patterns
ADD COLUMN embedding vector(384);

-- HNSW index for fast similarity search
CREATE INDEX idx_patterns_embedding ON domain_patterns
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Backfill Process

```bash
# Generate embeddings for existing patterns
python scripts/backfill_pattern_embeddings.py

# Output:
# 🔄 Starting embedding backfill...
# 📝 Found 25 patterns without embeddings
# [1/25] Processing: email_validation ✅
# [2/25] Processing: phone_validation ✅
# ...
# ✅ Backfill complete! Updated 25 patterns
```

### Testing

```bash
# Unit tests
uv run pytest tests/unit/infrastructure/test_embedding_service.py -v
uv run pytest tests/unit/application/test_pattern_service_embeddings.py -v

# Integration tests
uv run pytest tests/integration/test_semantic_search_cli.py -v

# Performance tests
uv run pytest tests/performance/test_semantic_search_performance.py -v -s
```

---

## Future Enhancements

### Planned Features

1. **Hybrid Search**: Combine vector similarity with full-text search
2. **Pattern Clustering**: Automatically group similar patterns
3. **Recommendation Engine**: ML-based pattern suggestions
4. **Multi-language Support**: Embeddings for different languages
5. **Custom Models**: Fine-tuned embeddings for domain-specific patterns

### Optimization Opportunities

1. **Index Tuning**: Optimize HNSW parameters for better recall/speed tradeoff
2. **Caching**: Cache frequent query embeddings
3. **Batch Processing**: Process multiple queries simultaneously
4. **GPU Acceleration**: Use GPU for embedding generation (if available)

---

## Troubleshooting

### Common Issues

**"Pattern has no embedding"**
```bash
# Run backfill script
python scripts/backfill_pattern_embeddings.py
```

**"Search returns no results"**
- Lower `--min-similarity` threshold
- Check if patterns have embeddings
- Try different query wording

**"Slow search performance"**
- Ensure HNSW index is created
- Check PostgreSQL configuration
- Consider index rebuild if data changed significantly

### Debug Commands

```bash
# Check embedding status
psql $SPECQL_DB_URL -c "SELECT COUNT(*) FROM pattern_library.domain_patterns WHERE embedding IS NOT NULL;"

# Verify pgvector extension
psql $SPECQL_DB_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check index exists
psql $SPECQL_DB_URL -c "SELECT indexname FROM pg_indexes WHERE tablename = 'domain_patterns' AND indexname LIKE '%embedding%';"
```