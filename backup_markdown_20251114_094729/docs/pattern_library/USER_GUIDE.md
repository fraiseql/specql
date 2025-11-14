# SpecQL Pattern Library User Guide

## Overview

The SpecQL Pattern Library is an intelligent system that helps you discover, reuse, and generate business logic patterns for your SpecQL entities. It uses PostgreSQL with native vector search and Grok LLM to provide:

- **Pattern Discovery**: Automatically finds reusable patterns in your legacy SQL
- **Natural Language Generation**: Create patterns from plain English descriptions
- **Intelligent Search**: Find relevant patterns using semantic similarity
- **Human Review Workflow**: Approve or reject pattern suggestions

## Quick Start

### 1. Setup Database

```bash
# Set your database URL
export SPECQL_DB_URL="postgresql://user:password@localhost:5432/specql_patterns"

# Run setup script
./scripts/setup_database.sh

# Load seed patterns
psql $SPECQL_DB_URL -f database/pattern_library_schema.sql
psql $SPECQL_DB_URL -f database/seed_patterns.sql
```

### 2. Generate Embeddings

```bash
# Generate embeddings for all patterns
specql embeddings generate

# Test retrieval
specql embeddings test-retrieval "approval workflow"
```

### 3. Reverse Engineer with Pattern Discovery

```bash
# Analyze SQL with pattern discovery
specql reverse --discover-patterns complex_function.sql

# Review pending suggestions
specql patterns review-suggestions

# Show suggestion details
specql patterns show 1

# Approve or reject
specql patterns approve 1
specql patterns reject 1 --reason "Too specific"
```

### 4. Generate Patterns from Text

```bash
# Create pattern from description
specql patterns create-from-description \
  --description "A workflow for approving documents that requires two approvals" \
  --category workflow
```

## Core Features

### Pattern Discovery

The system automatically analyzes your SQL functions and suggests reusable patterns:

```bash
# Analyze a complex SQL file
specql reverse --discover-patterns my_complex_function.sql
```

**What gets analyzed:**
- Control flow complexity
- State management patterns
- Audit logging patterns
- Multi-step approval workflows
- Validation chains

**Discovery triggers:**
- Functions with >10 steps
- Similarity score <0.7 to existing patterns
- High cyclomatic complexity

### Pattern Suggestions Review

Review and manage pattern suggestions through the CLI:

```bash
# List all pending suggestions
specql patterns review-suggestions

# Get detailed view of a suggestion
specql patterns show 123

# Approve a suggestion (moves to pattern library)
specql patterns approve 123

# Reject with reason
specql patterns reject 123 --reason "Duplicates existing pattern"

# List approved patterns
specql patterns list --category workflow
```

### Natural Language Pattern Generation

Create patterns from plain English descriptions:

```bash
# Simple approval workflow
specql patterns create-from-description \
  --description "Approve documents with manager review" \
  --category workflow

# Complex audit pattern
specql patterns create-from-description \
  --description "Track all changes to financial records with user and timestamp" \
  --category audit

# State machine
specql patterns create-from-description \
  --description "Order processing with states: pending, confirmed, shipped, delivered" \
  --category workflow
```

### Intelligent Pattern Search

Find patterns using semantic search:

```bash
# Via CLI
specql patterns search "multi-step approval"

# Via embeddings CLI
specql embeddings test-retrieval "workflow approval process"
```

## Pattern Categories

### Workflow Patterns
- **Approval Workflow**: Multi-step approvals with audit trails
- **State Machine**: Status transitions with validation
- **Validation Chain**: Sequential validation steps

### Audit Patterns
- **Audit Trail**: Track all changes with full history
- **Soft Delete**: Mark records as deleted without removing
- **Change Log**: Log specific field changes

### Data Patterns
- **Hierarchical Data**: Tree structures with parent-child relationships
- **Temporal Data**: Time-based data with effective dates
- **Reference Data**: Lookup tables with caching

## CLI Reference

### Pattern Management

```bash
specql patterns review-suggestions          # List pending suggestions
specql patterns show <id>                   # Show suggestion details
specql patterns approve <id>                # Approve suggestion
specql patterns reject <id> --reason "..."  # Reject suggestion
specql patterns list [--category <cat>]     # List approved patterns
specql patterns search <query>              # Search patterns
specql patterns create-from-description     # Generate from text
```

### Embeddings Management

```bash
specql embeddings generate                  # Generate all embeddings
specql embeddings test-retrieval <query>    # Test similarity search
```

### Reverse Engineering

```bash
specql reverse <file> --discover-patterns    # Analyze with pattern discovery
```

## Pattern Format

Patterns are defined in SpecQL YAML format:

```yaml
name: approval_workflow
category: workflow
description: Multi-step approval with audit logging

parameters:
  entity:
    type: string
    required: true
    description: The entity being approved
  approvals_required:
    type: integer
    default: 2
    description: Number of approvals needed

implementation:
  fields:
    - name: status
      type: enum(pending,approved,rejected)
    - name: approved_at
      type: timestamp
    - name: approved_by
      type: ref(User)

  actions:
    - name: approve
      steps:
        - validate: "status == 'pending'"
        - update: "increment approval_count"
        - condition: "approval_count >= approvals_required"
          then:
            - update: "status = 'approved', approved_at = now()"
            - log: "Document approved"
```

## Best Practices

### Writing Good Pattern Descriptions

**Good descriptions:**
- "Multi-step approval workflow with audit logging"
- "Soft delete with recovery capability"
- "State machine for order processing"

**Avoid vague descriptions:**
- "Approval thing" ❌
- "Some workflow" ❌
- "Pattern for stuff" ❌

### Pattern Discovery Tips

1. **Complex Functions**: Focus on functions with >15 lines or complex logic
2. **Business Logic**: Look for domain-specific workflows in your SQL
3. **Audit Requirements**: Functions that log changes are often reusable
4. **State Management**: Status transitions are commonly reusable

### Review Guidelines

**Approve when:**
- Pattern is genuinely reusable across entities
- Implementation is clean and follows SpecQL conventions
- Parameters are well-defined and flexible

**Reject when:**
- Too specific to one use case
- Implementation has bugs or inconsistencies
- Duplicates existing patterns
- Doesn't follow SpecQL conventions

## Troubleshooting

### Common Issues

**"Pattern library not available"**
```bash
# Check database connection
psql $SPECQL_DB_URL -c "SELECT 1"

# Verify schema exists
psql $SPECQL_DB_URL -c "SELECT COUNT(*) FROM pattern_library.domain_patterns"

# Check embeddings
specql embeddings generate
```

**"No patterns found"**
```bash
# Check if embeddings are generated
psql $SPECQL_DB_URL -c "SELECT COUNT(*) FROM pattern_library.domain_patterns WHERE embedding IS NOT NULL"

# Regenerate embeddings
specql embeddings generate
```

**"Grok service unavailable"**
```bash
# Test Grok directly
echo "test" | opencode run --model opencode/grok-code

# Check OpenCode installation
which opencode
```

### Performance Tuning

**Slow embedding generation:**
- Reduce batch size in configuration
- Use CPU-optimized sentence transformers
- Consider GPU acceleration for large libraries

**Slow pattern retrieval:**
- HNSW index should provide <50ms retrieval
- Check PostgreSQL configuration
- Monitor pgvector performance

## Integration Examples

### With Existing SpecQL Projects

```bash
# 1. Set up pattern library
./scripts/setup_database.sh

# 2. Import existing patterns
psql $SPECQL_DB_URL -f database/seed_patterns.sql

# 3. Generate embeddings
specql embeddings generate

# 4. Analyze legacy SQL
find sql/ -name "*.sql" -exec specql reverse --discover-patterns {} \;

# 5. Review suggestions
specql patterns review-suggestions
```

### CI/CD Integration

```yaml
# .github/workflows/pattern-library.yml
name: Pattern Library
on: [push, pull_request]

jobs:
  test-patterns:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup PostgreSQL
        uses: postgresql-action@v2
        with:
          postgresql version: '17'
          postgresql db: specql_patterns

      - name: Install dependencies
        run: uv sync --extra patterns

      - name: Run pattern tests
        run: uv run pytest tests/integration/test_e2e_pattern_library.py -v

      - name: Generate embeddings
        run: specql embeddings generate

      - name: Performance benchmarks
        run: uv run pytest tests/performance/test_pattern_library_performance.py -v
```

## Advanced Usage

### Custom Pattern Categories

Add your own pattern categories:

```sql
-- Add custom category
INSERT INTO pattern_library.categories (name, description)
VALUES ('compliance', 'Regulatory compliance patterns');
```

### Bulk Operations

```bash
# Export patterns
psql $SPECQL_DB_URL -c "COPY pattern_library.domain_patterns TO 'patterns_export.csv' CSV HEADER"

# Import patterns
psql $SPECQL_DB_URL -c "COPY pattern_library.domain_patterns FROM 'patterns_import.csv' CSV HEADER"
```

### Monitoring

```sql
-- Check system health
SELECT
    (SELECT COUNT(*) FROM pattern_library.domain_patterns) as total_patterns,
    (SELECT COUNT(*) FROM pattern_library.pattern_suggestions WHERE status = 'pending') as pending_suggestions,
    (SELECT COUNT(*) FROM pattern_library.grok_call_logs WHERE created_at > now() - interval '1 hour') as recent_calls;

-- Performance metrics
SELECT
    avg(extract(epoch from (completed_at - started_at))) as avg_embedding_time
FROM pattern_library.embedding_jobs
WHERE completed_at IS NOT NULL;
```

## Support

- **Documentation**: See `docs/pattern_library/DEVELOPER_GUIDE.md`
- **Issues**: Report bugs at https://github.com/sst/opencode/issues
- **Discussions**: Join the SpecQL community discussions

---

**Version**: 1.0.0
**Last Updated**: November 2025