# SpecQL Pattern Library Developer Guide

## Architecture Overview

The Pattern Library consists of several key components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Pattern Library System                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Grok      │  │ Embeddings  │  │ Suggestion  │         │
│  │   Provider  │  │   Service   │  │   Service   │         │
│  │             │  │             │  │             │         │
│  │ • LLM calls │  │ • pgvector  │  │ • CRUD ops  │         │
│  │ • JSON      │  │ • HNSW      │  │ • Review    │         │
│  │ • Logging   │  │ • Search    │  │ • Approval  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │     NL      │  │   Reverse   │  │     CLI     │         │
│  │ Generator   │  │ Engineering │  │ Commands   │         │
│  │             │  │ Enhancer    │  │             │         │
│  │ • Text→YAML │  │ • Discovery │  │ • patterns  │         │
│  │ • Validation │  │ • Analysis │  │ • embeddings│         │
│  │ • Scoring    │  │ • AI        │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │
                ┌─────────────────────────────┐
                │     PostgreSQL Database     │
                │                             │
                │ • domain_patterns           │
                │ • pattern_suggestions       │
                │ • grok_call_logs            │
                │ • vector embeddings         │
                │ • HNSW indexes              │
                └─────────────────────────────┘
```

## Core Components

### 1. GrokProvider (`src/reverse_engineering/grok_provider.py`)

Handles all LLM interactions with OpenCode Grok:

```python
from src.reverse_engineering.grok_provider import GrokProvider

provider = GrokProvider()

# Call with JSON response
result = provider.call_json({
    "prompt": "Generate a pattern for approval workflow",
    "format": "json"
})

# All calls are logged to grok_call_logs table
```

**Key Methods:**
- `call(prompt: str) -> str`: Raw LLM call
- `call_json(data: dict) -> dict`: JSON response with retry logic
- `_call_subprocess()`: Executes `opencode run --model opencode/grok-code`

### 2. PatternEmbeddingService (`src/pattern_library/embeddings_pg.py`)

Manages vector embeddings using pgvector:

```python
from src.pattern_library.embeddings_pg import PatternEmbeddingService

service = PatternEmbeddingService()

# Generate embeddings for patterns
patterns = [
    {
        'id': 'pattern_1',
        'name': 'approval_workflow',
        'description': 'Multi-step approval process',
        'category': 'workflow',
        'parameters': '{"entity": "string"}',
        'implementation': '{"fields": [], "actions": []}'
    }
]

service.generate_embeddings_batch(patterns)

# Search similar patterns
results = service.retrieve_similar("document approval workflow", limit=5)

# Hybrid search (vector + text + category filter)
results = service.hybrid_search(
    query="approval process",
    category="workflow",
    limit=10
)
```

**Key Methods:**
- `generate_embeddings_batch()`: Batch embedding generation
- `retrieve_similar()`: Cosine similarity search
- `hybrid_search()`: Combined search with filters

### 3. PatternSuggestionService (`src/pattern_library/suggestion_service_pg.py`)

Manages the human review workflow:

```python
from src.pattern_library.suggestion_service_pg import PatternSuggestionService

service = PatternSuggestionService()

# Create suggestion
suggestion_id = service.create_suggestion(
    suggested_name="my_workflow",
    suggested_category="workflow",
    description="Custom workflow pattern",
    parameters={"param": "value"},
    implementation={"yaml": "specql_code"},
    source_type="reverse_engineering",
    complexity_score=0.8,
    confidence_score=0.9
)

# Review workflow
service.approve_suggestion(suggestion_id, "reviewer_name")
# or
service.reject_suggestion(suggestion_id, "reason", "reviewer_name")

# Query suggestions
pending = service.list_pending()
stats = service.get_stats()
```

### 4. NLPatternGenerator (`src/pattern_library/nl_generator.py`)

Converts natural language to SpecQL patterns:

```python
from src.pattern_library.nl_generator import NLPatternGenerator

generator = NLPatternGenerator()

# Generate pattern from text
pattern = generator.generate(
    description="A workflow for approving documents that requires two approvals",
    category="workflow"
)

# Validate pattern
is_valid, errors = generator._validate_pattern(pattern)

# Score confidence
confidence = generator._score_confidence(pattern, description)
```

## Database Schema

### Core Tables

#### `pattern_library.domain_patterns`
```sql
CREATE TABLE pattern_library.domain_patterns (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    parameters JSONB,
    implementation JSONB NOT NULL,
    embedding vector(384),  -- pgvector
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- HNSW index for fast vector search
CREATE INDEX ON pattern_library.domain_patterns
USING hnsw (embedding vector_cosine_ops);

-- GIN index for JSONB queries
CREATE INDEX ON pattern_library.domain_patterns
USING gin (parameters jsonb_path_ops);
```

#### `pattern_library.pattern_suggestions`
```sql
CREATE TABLE pattern_library.pattern_suggestions (
    id SERIAL PRIMARY KEY,
    suggested_name TEXT NOT NULL,
    suggested_category TEXT NOT NULL,
    description TEXT,
    parameters JSONB,
    implementation JSONB NOT NULL,
    source_type TEXT NOT NULL,  -- 'reverse_engineering', 'nl_generation', etc.
    complexity_score REAL,
    confidence_score REAL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

#### `pattern_library.grok_call_logs`
```sql
CREATE TABLE pattern_library.grok_call_logs (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    response TEXT,
    response_json JSONB,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    tokens_used INTEGER,
    processing_time REAL,
    created_at TIMESTAMP DEFAULT now()
);
```

## CLI Integration

### Adding New Commands

Commands are defined in `src/cli/patterns.py` and `src/cli/embeddings.py`:

```python
# src/cli/patterns.py
@click.group()
def patterns():
    """Pattern library management commands."""
    pass

@patterns.command()
@click.argument('pattern_id', type=int)
def show(pattern_id):
    """Show pattern suggestion details."""
    service = PatternSuggestionService()
    try:
        suggestion = service.get_suggestion(pattern_id)
        if suggestion:
            # Display suggestion details
            pass
        else:
            click.echo(f"Suggestion {pattern_id} not found")
    finally:
        service.close()
```

### CLI Structure

```
specql patterns/
├── review-suggestions    # List pending suggestions
├── show <id>            # Show suggestion details
├── approve <id>         # Approve suggestion
├── reject <id>          # Reject suggestion
├── list                 # List approved patterns
├── search <query>       # Search patterns
└── create-from-description  # Generate from text

specql embeddings/
├── generate             # Generate all embeddings
└── test-retrieval       # Test similarity search
```

## Extending the System

### Adding New Pattern Categories

1. **Database**: Add to categories table
```sql
INSERT INTO pattern_library.categories (name, description)
VALUES ('my_category', 'Custom category description');
```

2. **Validation**: Update category validation in services
```python
VALID_CATEGORIES = {'workflow', 'audit', 'data', 'my_category'}
```

3. **Documentation**: Update user guide with new category

### Custom Embedding Models

To use different embedding models:

```python
# In embeddings_pg.py
from sentence_transformers import SentenceTransformer

class CustomEmbeddingService(PatternEmbeddingService):
    def __init__(self):
        super().__init__()
        self.model = SentenceTransformer('all-MiniLM-L12-v2')  # Different model

    def _generate_embedding(self, text: str) -> list:
        """Override embedding generation."""
        return self.model.encode(text).tolist()
```

### Adding New LLM Providers

Implement the provider interface:

```python
class CustomLLMProvider:
    def call_json(self, data: dict) -> dict:
        """Call LLM and return JSON response."""
        # Custom LLM logic here
        pass

    def call(self, prompt: str) -> str:
        """Call LLM and return raw response."""
        pass
```

### Custom Pattern Validation

Extend validation in `NLPatternGenerator`:

```python
def _validate_pattern(self, pattern: dict) -> tuple[bool, list[str]]:
    """Validate pattern structure."""
    errors = []

    # Standard validation
    if 'name' not in pattern:
        errors.append("Missing pattern name")

    # Custom validation for your domain
    if pattern.get('category') == 'my_category':
        if 'custom_field' not in pattern.get('implementation', {}):
            errors.append("My category patterns must have custom_field")

    return len(errors) == 0, errors
```

## Testing Strategy

### Unit Tests

Test individual components:

```python
# tests/unit/pattern_library/test_nl_generator.py
def test_pattern_validation():
    generator = NLPatternGenerator()

    # Valid pattern
    valid_pattern = {
        'name': 'test_pattern',
        'category': 'workflow',
        'parameters': {},
        'implementation': {'fields': [], 'actions': []}
    }

    is_valid, errors = generator._validate_pattern(valid_pattern)
    assert is_valid
    assert len(errors) == 0
```

### Integration Tests

Test full workflows:

```python
# tests/integration/test_e2e_pattern_library.py
def test_sql_to_pattern_workflow(db_connection):
    """Test complete SQL → Pattern workflow."""
    # Full end-to-end test
    pass
```

### Performance Tests

Benchmark critical paths:

```python
# tests/performance/test_pattern_library_performance.py
def test_embedding_generation_performance():
    """Benchmark embedding generation speed."""
    # Performance assertions
    assert avg_time < 0.1  # <100ms per pattern
```

## Performance Optimization

### Database Tuning

1. **HNSW Index Parameters**:
```sql
-- Adjust HNSW for your data size
CREATE INDEX ON pattern_library.domain_patterns
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

2. **Connection Pooling**:
```python
# Use connection pooling for high concurrency
import psycopg_pool

pool = psycopg_pool.ConnectionPool(
    conninfo=os.getenv('SPECQL_DB_URL'),
    min_size=4,
    max_size=20
)
```

### Embedding Optimization

1. **Batch Processing**:
```python
# Process embeddings in batches
def generate_embeddings_batch(self, patterns, batch_size=32):
    texts = [self._pattern_to_text(p) for p in patterns]
    embeddings = self.model.encode(texts, batch_size=batch_size)
    # Store embeddings
```

2. **CPU Optimization**:
```python
# Use CPU-optimized models
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
```

### Caching Strategies

1. **Embedding Cache**:
```python
@lru_cache(maxsize=1000)
def get_embedding(text: str) -> list:
    """Cache embeddings for repeated texts."""
    return self.model.encode(text).tolist()
```

2. **Query Result Cache**:
```python
# Cache frequent search results
@cachetools.ttl_cache(maxsize=100, ttl=300)  # 5 minute cache
def search_patterns(query: str, limit: int) -> list:
    pass
```

## Monitoring & Observability

### Key Metrics

```sql
-- System health metrics
SELECT
    (SELECT COUNT(*) FROM pattern_library.domain_patterns) as total_patterns,
    (SELECT COUNT(*) FROM pattern_library.pattern_suggestions WHERE status = 'pending') as pending_suggestions,
    (SELECT AVG(processing_time) FROM pattern_library.grok_call_logs WHERE created_at > now() - interval '1 hour') as avg_grok_time,
    (SELECT COUNT(*) FROM pattern_library.grok_call_logs WHERE success = false AND created_at > now() - interval '1 day') as failed_calls;

-- Performance metrics
SELECT
    query,
    avg_retrieval_time,
    call_count
FROM pattern_library.query_performance
WHERE date >= CURRENT_DATE - INTERVAL '7 days';
```

### Logging

```python
import logging

logger = logging.getLogger('pattern_library')

def log_grok_call(prompt: str, response: str, success: bool, processing_time: float):
    """Log all Grok interactions."""
    logger.info(f"Grok call: success={success}, time={processing_time:.3f}s")
    # Also store in database
```

### Error Handling

```python
class PatternLibraryError(Exception):
    """Base exception for pattern library errors."""
    pass

class EmbeddingError(PatternLibraryError):
    """Embedding generation failed."""
    pass

class LLMError(PatternLibraryError):
    """LLM call failed."""
    pass

# Usage
try:
    embedding = service.generate_embedding(text)
except EmbeddingError:
    logger.error("Embedding generation failed")
    # Fallback logic
```

## Deployment Considerations

### Production Setup

1. **Database Configuration**:
```sql
-- Production PostgreSQL settings
ALTER SYSTEM SET shared_preload_libraries = 'vector';
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET work_mem = '128MB';
```

2. **Backup Strategy**:
```bash
# Daily backups
pg_dump $SPECQL_DB_URL > pattern_library_$(date +%Y%m%d).sql

# Vector-specific backup considerations
pg_dump --format=custom --compress=9 $SPECQL_DB_URL > pattern_library.backup
```

3. **Scaling**:
- **Read Replicas**: For search-heavy workloads
- **Partitioning**: For large pattern libraries
- **Connection Pooling**: For high concurrency

### Security

1. **Database Access**:
```sql
-- Create restricted user
CREATE USER pattern_user WITH PASSWORD 'secure_password';
GRANT SELECT ON pattern_library.domain_patterns TO pattern_user;
GRANT ALL ON pattern_library.pattern_suggestions TO pattern_user;
```

2. **API Security**:
```python
# Rate limiting for LLM calls
@limiter.limit("10 per minute")
def generate_pattern(description: str):
    pass
```

## Troubleshooting

### Common Issues

**High Memory Usage**:
- Reduce batch sizes in embedding generation
- Use streaming for large datasets
- Monitor with `memory_profiler`

**Slow Vector Search**:
- Check HNSW index health: `SELECT * FROM pg_stat_user_indexes WHERE schemaname = 'pattern_library';`
- Rebuild index if needed: `REINDEX INDEX CONCURRENTLY pattern_library.domain_patterns_embedding_idx;`
- Adjust HNSW parameters based on data size

**LLM Call Failures**:
- Check OpenCode installation: `opencode --version`
- Verify network connectivity
- Implement retry logic with exponential backoff
- Monitor rate limits

**Database Connection Issues**:
- Use connection pooling
- Implement connection retry logic
- Monitor connection pool stats

### Debug Mode

```python
import os
os.environ['PATTERN_LIBRARY_DEBUG'] = '1'

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
service = PatternEmbeddingService()
service.test_connection()  # Custom debug method
```

## Contributing

### Code Standards

1. **Type Hints**: All functions must have type hints
2. **Docstrings**: Comprehensive docstrings for public methods
3. **Error Handling**: Proper exception handling and logging
4. **Testing**: Unit tests for all new functionality
5. **Performance**: Profile and optimize performance-critical code

### Pull Request Process

1. **Branch**: Create feature branch from `main`
2. **Tests**: Add comprehensive tests
3. **Documentation**: Update relevant docs
4. **Performance**: Ensure no performance regressions
5. **Review**: Request review from maintainers

### Release Process

1. **Version Bump**: Update version in `src/__version__.py`
2. **Changelog**: Update `CHANGELOG.md`
3. **Tests**: Run full test suite
4. **Documentation**: Update user guide
5. **Tag**: Create git tag
6. **Deploy**: Update production systems

---

**Version**: 1.0.0
**Last Updated**: November 2025