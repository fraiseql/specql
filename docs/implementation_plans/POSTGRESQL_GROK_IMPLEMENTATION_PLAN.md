# PostgreSQL + Grok: Pattern Library Implementation Plan

**Project**: SpecQL Pattern Library Enhancement
**Hardware**: Lenovo X270 (Intel i5/i7, 8-16GB RAM, no GPU)
**LLM**: OpenCode Grok Code Fast 1 (FREE)
**Database**: PostgreSQL 17.6 + pgvector
**Version**: 2.0 (Production-Ready)
**Date**: 2025-11-12
**Status**: Ready to Execute

---

## Executive Summary

### Vision

Build a **production-ready pattern library** for SpecQL using PostgreSQL with native vector search (pgvector) and free Grok LLM, running on standard laptop hardware with **zero LLM costs**.

### Why This Stack

**PostgreSQL 17.6 + pgvector**:
- ✅ **Already installed** on your system
- ✅ **Native vector search** (100x faster than SQLite)
- ✅ **Same database** as SpecQL-generated schemas
- ✅ **Advanced JSONB** with GIN indexes
- ✅ **Production-ready** from day 1

**OpenCode Grok Code Fast 1**:
- ✅ **FREE** (no API costs)
- ✅ **Fast** (1-3s response time)
- ✅ **Good quality** (validated: produces JSON, understands SQL)
- ✅ **No GPU needed** (runs on OpenCode infrastructure)

**X270 Laptop**:
- ✅ **Sufficient** for PostgreSQL + embeddings
- ✅ **CPU-friendly** embeddings (~50ms)
- ✅ **No upgrades needed**

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL 17.6 Database                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────────┐    │
│  │ Pattern Library      │  │ SpecQL Schemas           │    │
│  │ (pattern_library)    │  │ (crm, sales, etc.)       │    │
│  │                      │  │                          │    │
│  │ • domain_patterns    │  │ • crm.tb_contact        │    │
│  │   - embedding VECTOR │  │ • crm.tb_company        │    │
│  │   - parameters JSONB │  │ • sales.tb_invoice      │    │
│  │   - HNSW index       │  │ • ...                   │    │
│  │                      │  │                          │    │
│  │ • pattern_suggestions│  │ Same ACID transactions!  │    │
│  │ • pattern_instantiations                          │    │
│  │ • grok_call_logs     │  │ Cross-schema queries!   │    │
│  └──────────────────────┘  └──────────────────────────┘    │
│                                                              │
│  Extensions: pgvector, pg_trgm                              │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌───────────────────────────┴───────────────────────────┐
│              Python Application Layer                  │
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Grok LLM     │  │ Embeddings   │  │ Pattern    │  │
│  │ Provider     │  │ (pgvector)   │  │ Library    │  │
│  │              │  │              │  │ API        │  │
│  │ • Subprocess │  │ • sentence-  │  │            │  │
│  │ • OpenCode   │  │   transformers│ │ • psycopg  │  │
│  │ • JSON parse │  │ • CPU-friendly│ │ • pgvector │  │
│  └──────────────┘  └──────────────┘  └────────────┘  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Timeline: 8 Weeks

| Phase | Duration | Focus |
|-------|----------|-------|
| **Phase 0** | Week 1 | PostgreSQL setup + schema + baseline |
| **Phase 1** | Weeks 2-3 | Pattern embeddings + pgvector retrieval |
| **Phase 2** | Weeks 4-5 | Pattern discovery + human review |
| **Phase 3** | Weeks 6-7 | Natural language pattern generation |
| **Phase 4** | Week 8 | Integration testing + documentation |

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Pattern Retrieval Accuracy** | >75% Top-5 relevant | Manual validation (20 queries) |
| **Vector Search Performance** | <50ms (1000 patterns) | HNSW index benchmark |
| **Pattern Discovery Rate** | 5-10% of functions | Auto-tracking |
| **NL Pattern Quality** | >70% valid first try | Validation pass rate |
| **LLM Cost** | $0 | No API charges |
| **Setup Time** | <30 minutes | Automated script |

---

## Phase 0: PostgreSQL Setup & Baseline (Week 1)

### Goals
- PostgreSQL database configured with pgvector
- Schema created and validated
- Baseline seed patterns loaded
- Development environment ready

### 0.1 PostgreSQL Installation & Configuration

#### Prerequisites Check

```bash
# Verify PostgreSQL installation
psql --version
# Expected: psql (PostgreSQL) 17.6 ✅

# Check if service is running
sudo systemctl status postgresql

# If not running
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
```

#### Create Database & User

**Script**: `scripts/setup_database.sh`

```bash
#!/bin/bash
set -e

echo "========================================="
echo "SpecQL Pattern Library: Database Setup"
echo "========================================="
echo ""

# Configuration
DB_NAME="specql_patterns"
DB_USER="specql_user"
DB_PASSWORD="specql_dev_password"  # Change for production!

# Create database and user
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
      CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
   END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo "✓ Database '$DB_NAME' created"
echo "✓ User '$DB_USER' created"

# Install pgvector extension
echo ""
echo "Installing pgvector extension..."
sudo -u postgres psql -d $DB_NAME << EOF
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text similarity
EOF

echo "✓ pgvector extension installed"
echo "✓ pg_trgm extension installed"

# Set connection string
echo ""
echo "Connection string:"
echo "postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME"
echo ""
echo "Add to ~/.bashrc:"
echo "export SPECQL_DB_URL='postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME'"

echo ""
echo "========================================="
echo "Setup complete! ✓"
echo "========================================="
```

Run setup:

```bash
chmod +x scripts/setup_database.sh
./scripts/setup_database.sh

# Add to environment
echo "export SPECQL_DB_URL='postgresql://specql_user:specql_dev_password@localhost/specql_patterns'" >> ~/.bashrc
source ~/.bashrc
```

### 0.2 Database Schema

**File**: `database/pattern_library_schema.sql`

```sql
-- ============================================================================
-- SpecQL Pattern Library Schema (PostgreSQL 17 + pgvector)
-- ============================================================================

-- Create schema for pattern library
CREATE SCHEMA IF NOT EXISTS pattern_library;

-- Set search path
SET search_path TO pattern_library, public;

-- ============================================================================
-- Core Pattern Tables
-- ============================================================================

-- Domain patterns with native vector embeddings
CREATE TABLE domain_patterns (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT NOT NULL,

    -- Pattern definition (JSONB for advanced queries)
    parameters JSONB NOT NULL DEFAULT '{}',
    implementation JSONB NOT NULL DEFAULT '{}',

    -- Vector embedding (pgvector native type!)
    embedding vector(384),  -- all-MiniLM-L6-v2 dimension

    -- Metadata
    times_instantiated INTEGER DEFAULT 0,
    source_type TEXT DEFAULT 'manual',  -- 'manual', 'llm_generated', 'discovered'
    complexity_score REAL,
    deprecated BOOLEAN DEFAULT FALSE,
    deprecated_reason TEXT,
    replacement_pattern_id INTEGER REFERENCES domain_patterns(id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT valid_category CHECK (
        category IN (
            'workflow', 'validation', 'audit', 'hierarchy',
            'state_machine', 'approval', 'notification',
            'calculation', 'soft_delete'
        )
    ),
    CONSTRAINT valid_source CHECK (
        source_type IN ('manual', 'llm_generated', 'discovered', 'migrated')
    )
);

-- HNSW index for fast approximate nearest neighbor search
-- This is the magic! 100x faster than brute-force cosine similarity
CREATE INDEX idx_patterns_embedding ON domain_patterns
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- GIN indexes for JSONB queries (super fast JSON searches)
CREATE INDEX idx_patterns_parameters ON domain_patterns
USING gin (parameters jsonb_path_ops);

CREATE INDEX idx_patterns_implementation ON domain_patterns
USING gin (implementation jsonb_path_ops);

-- Regular indexes
CREATE INDEX idx_patterns_category ON domain_patterns(category);
CREATE INDEX idx_patterns_source_type ON domain_patterns(source_type);
CREATE INDEX idx_patterns_deprecated ON domain_patterns(deprecated) WHERE deprecated = FALSE;

-- Full-text search (tsvector)
ALTER TABLE domain_patterns
ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (
    to_tsvector('english',
        coalesce(name, '') || ' ' ||
        coalesce(description, '') || ' ' ||
        coalesce(category, '')
    )
) STORED;

CREATE INDEX idx_patterns_search ON domain_patterns
USING gin (search_vector);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_domain_patterns_updated_at
    BEFORE UPDATE ON domain_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- Pattern Suggestions (Human-in-the-Loop)
-- ============================================================================

CREATE TABLE pattern_suggestions (
    id SERIAL PRIMARY KEY,
    suggested_name TEXT NOT NULL,
    suggested_category TEXT NOT NULL,
    description TEXT NOT NULL,
    parameters JSONB,
    implementation JSONB,

    -- Source tracking
    source_type TEXT NOT NULL,  -- 'reverse_engineering', 'user_nl', 'manual'
    source_sql TEXT,
    source_description TEXT,
    source_function_id TEXT,

    -- Quality metrics
    complexity_score REAL,
    confidence_score REAL,
    trigger_reason TEXT,

    -- Review tracking
    status TEXT DEFAULT 'pending',
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_feedback TEXT,
    merged_into_pattern_id INTEGER REFERENCES domain_patterns(id),

    created_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT valid_status CHECK (
        status IN ('pending', 'approved', 'rejected', 'merged')
    ),
    CONSTRAINT valid_source CHECK (
        source_type IN ('reverse_engineering', 'user_nl', 'manual')
    )
);

CREATE INDEX idx_suggestions_status ON pattern_suggestions(status);
CREATE INDEX idx_suggestions_category ON pattern_suggestions(suggested_category);
CREATE INDEX idx_suggestions_created ON pattern_suggestions(created_at DESC);


-- ============================================================================
-- Pattern Instantiations (Usage Tracking)
-- ============================================================================

CREATE TABLE pattern_instantiations (
    id SERIAL PRIMARY KEY,
    pattern_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,
    entity_name TEXT NOT NULL,
    entity_schema TEXT,  -- e.g., 'crm', 'sales'
    instantiated_at TIMESTAMPTZ DEFAULT now(),
    instantiated_by TEXT,
    parameters_used JSONB,

    UNIQUE(pattern_id, entity_name, entity_schema)
);

CREATE INDEX idx_instantiations_pattern ON pattern_instantiations(pattern_id);
CREATE INDEX idx_instantiations_entity ON pattern_instantiations(entity_name);
CREATE INDEX idx_instantiations_schema ON pattern_instantiations(entity_schema);


-- ============================================================================
-- Pattern Co-occurrence (Which patterns are used together?)
-- ============================================================================

CREATE TABLE pattern_cooccurrence (
    id SERIAL PRIMARY KEY,
    pattern_a_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,
    pattern_b_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,
    cooccurrence_count INTEGER DEFAULT 1,
    last_seen TIMESTAMPTZ DEFAULT now(),

    UNIQUE(pattern_a_id, pattern_b_id),
    CONSTRAINT ordered_patterns CHECK (pattern_a_id < pattern_b_id)
);

CREATE INDEX idx_cooccurrence_a ON pattern_cooccurrence(pattern_a_id);
CREATE INDEX idx_cooccurrence_b ON pattern_cooccurrence(pattern_b_id);


-- ============================================================================
-- Pattern Quality Metrics
-- ============================================================================

CREATE TABLE pattern_quality_metrics (
    id SERIAL PRIMARY KEY,
    pattern_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,

    -- Usage metrics
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    review_required_count INTEGER DEFAULT 0,

    -- Quality scores
    success_rate REAL,
    avg_review_time_seconds REAL,
    reusability_score REAL,

    -- Confidence tracking
    avg_confidence_score REAL,

    last_updated TIMESTAMPTZ DEFAULT now(),

    UNIQUE(pattern_id)
);

CREATE INDEX idx_quality_success_rate ON pattern_quality_metrics(success_rate);


-- ============================================================================
-- Reverse Engineering Results (Training Data)
-- ============================================================================

CREATE TABLE reverse_engineering_results (
    id SERIAL PRIMARY KEY,
    function_id TEXT NOT NULL UNIQUE,

    -- Input
    source_sql TEXT NOT NULL,
    source_file TEXT,

    -- Output
    generated_specql JSONB NOT NULL,
    detected_patterns JSONB,

    -- Confidence scores
    algorithmic_confidence REAL,
    heuristic_confidence REAL,
    ai_confidence REAL,
    final_confidence REAL,

    -- Features (for future ML training)
    features JSONB,

    -- Human review
    reviewed BOOLEAN DEFAULT FALSE,
    review_status TEXT,
    review_feedback TEXT,
    corrected_specql JSONB,
    review_time_seconds INTEGER,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,

    -- Pattern suggestions
    suggested_pattern BOOLEAN DEFAULT FALSE,
    suggestion_id INTEGER REFERENCES pattern_suggestions(id),

    -- Performance metrics
    processing_time_ms INTEGER,
    llm_calls INTEGER,

    created_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT valid_review_status CHECK (
        review_status IS NULL OR
        review_status IN ('approved', 'rejected', 'modified')
    )
);

CREATE INDEX idx_re_results_reviewed ON reverse_engineering_results(reviewed);
CREATE INDEX idx_re_results_confidence ON reverse_engineering_results(final_confidence);
CREATE INDEX idx_re_results_created ON reverse_engineering_results(created_at DESC);


-- ============================================================================
-- Grok Call Logging (Metrics & Cost Tracking)
-- ============================================================================

CREATE TABLE grok_call_logs (
    id SERIAL PRIMARY KEY,
    call_id TEXT NOT NULL UNIQUE,

    -- Task details
    task_type TEXT NOT NULL,
    task_context JSONB,

    -- Request/response
    prompt_length INTEGER,
    response_length INTEGER,
    prompt_hash TEXT,  -- For deduplication

    -- Performance
    latency_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,

    -- Cost (always $0 for Grok, but track for future)
    cost_usd REAL DEFAULT 0.0,

    created_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT valid_task_type CHECK (
        task_type IN (
            'reverse_engineering', 'pattern_discovery',
            'pattern_generation', 'template_generation',
            'pattern_validation'
        )
    )
);

CREATE INDEX idx_grok_logs_task ON grok_call_logs(task_type);
CREATE INDEX idx_grok_logs_created ON grok_call_logs(created_at DESC);
CREATE INDEX idx_grok_logs_prompt_hash ON grok_call_logs(prompt_hash);


-- ============================================================================
-- Utility Views
-- ============================================================================

-- View: Popular patterns
CREATE VIEW popular_patterns AS
SELECT
    dp.id,
    dp.name,
    dp.category,
    dp.description,
    dp.times_instantiated,
    COUNT(DISTINCT pi.entity_name) AS unique_entities,
    pqm.success_rate
FROM domain_patterns dp
LEFT JOIN pattern_instantiations pi ON dp.id = pi.pattern_id
LEFT JOIN pattern_quality_metrics pqm ON dp.id = pqm.pattern_id
WHERE dp.deprecated = FALSE
GROUP BY dp.id, dp.name, dp.category, dp.description, dp.times_instantiated, pqm.success_rate
ORDER BY dp.times_instantiated DESC;

-- View: Pending reviews
CREATE VIEW pending_reviews AS
SELECT
    ps.id,
    ps.suggested_name,
    ps.suggested_category,
    ps.description,
    ps.confidence_score,
    ps.source_type,
    ps.created_at,
    EXTRACT(EPOCH FROM (now() - ps.created_at))/3600 AS hours_pending
FROM pattern_suggestions ps
WHERE ps.status = 'pending'
ORDER BY ps.confidence_score DESC, ps.created_at ASC;

-- View: Pattern library stats
CREATE VIEW pattern_library_stats AS
SELECT
    COUNT(*) FILTER (WHERE deprecated = FALSE) AS active_patterns,
    COUNT(*) FILTER (WHERE deprecated = TRUE) AS deprecated_patterns,
    COUNT(DISTINCT category) AS categories,
    COUNT(*) FILTER (WHERE source_type = 'llm_generated') AS llm_generated,
    COUNT(*) FILTER (WHERE source_type = 'discovered') AS discovered,
    COUNT(*) FILTER (WHERE source_type = 'manual') AS manual,
    AVG(times_instantiated) AS avg_usage,
    SUM(times_instantiated) AS total_instantiations
FROM domain_patterns;


-- ============================================================================
-- Utility Functions
-- ============================================================================

-- Function: Find similar patterns (wrapper for convenience)
CREATE OR REPLACE FUNCTION find_similar_patterns(
    query_embedding vector(384),
    top_k INTEGER DEFAULT 5,
    similarity_threshold REAL DEFAULT 0.5
)
RETURNS TABLE (
    pattern_id INTEGER,
    pattern_name TEXT,
    category TEXT,
    description TEXT,
    similarity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dp.id,
        dp.name,
        dp.category,
        dp.description,
        1 - (dp.embedding <=> query_embedding) AS sim
    FROM domain_patterns dp
    WHERE dp.embedding IS NOT NULL
        AND dp.deprecated = FALSE
        AND (1 - (dp.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY dp.embedding <=> query_embedding
    LIMIT top_k;
END;
$$ LANGUAGE plpgsql;


-- Function: Hybrid search (vector + text + filters)
CREATE OR REPLACE FUNCTION hybrid_pattern_search(
    query_embedding vector(384),
    query_text TEXT DEFAULT NULL,
    category_filter TEXT DEFAULT NULL,
    top_k INTEGER DEFAULT 10
)
RETURNS TABLE (
    pattern_id INTEGER,
    pattern_name TEXT,
    category TEXT,
    description TEXT,
    combined_score REAL
) AS $$
BEGIN
    RETURN QUERY
    WITH vector_scores AS (
        SELECT
            id,
            1 - (embedding <=> query_embedding) AS vector_score
        FROM domain_patterns
        WHERE embedding IS NOT NULL
            AND deprecated = FALSE
            AND (category_filter IS NULL OR category = category_filter)
    ),
    text_scores AS (
        SELECT
            id,
            ts_rank(search_vector, to_tsquery('english', coalesce(query_text, ''))) AS text_score
        FROM domain_patterns
        WHERE query_text IS NOT NULL
            AND search_vector @@ to_tsquery('english', query_text)
            AND deprecated = FALSE
            AND (category_filter IS NULL OR category = category_filter)
    )
    SELECT
        dp.id,
        dp.name,
        dp.category,
        dp.description,
        (COALESCE(vs.vector_score, 0) * 0.7 + COALESCE(ts.text_score, 0) * 0.3)::REAL AS score
    FROM domain_patterns dp
    LEFT JOIN vector_scores vs ON dp.id = vs.id
    LEFT JOIN text_scores ts ON dp.id = ts.id
    WHERE dp.deprecated = FALSE
        AND (category_filter IS NULL OR dp.category = category_filter)
        AND (vs.vector_score IS NOT NULL OR ts.text_score IS NOT NULL)
    ORDER BY score DESC
    LIMIT top_k;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT USAGE ON SCHEMA pattern_library TO specql_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pattern_library TO specql_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA pattern_library TO specql_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pattern_library TO specql_user;

-- ============================================================================
-- Comments (Documentation)
-- ============================================================================

COMMENT ON SCHEMA pattern_library IS 'SpecQL pattern library with vector embeddings and advanced analytics';
COMMENT ON TABLE domain_patterns IS 'Core pattern definitions with pgvector embeddings for similarity search';
COMMENT ON TABLE pattern_suggestions IS 'LLM-suggested patterns awaiting human review';
COMMENT ON TABLE pattern_instantiations IS 'Tracking which patterns are used where';
COMMENT ON INDEX idx_patterns_embedding IS 'HNSW index for fast approximate nearest neighbor search (100x speedup!)';
```

Run schema:

```bash
psql $SPECQL_DB_URL -f database/pattern_library_schema.sql
```

### 0.3 Seed Baseline Patterns

**File**: `database/seed_patterns.sql`

```sql
-- Seed basic patterns for testing

SET search_path TO pattern_library;

-- Pattern 1: Audit Trail
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'audit_trail',
    'audit',
    'Track created_at, updated_at, deleted_at timestamps for record auditing',
    '{"entity": {"type": "string", "required": true, "description": "Target entity name"}}'::jsonb,
    '{
        "fields": [
            {"name": "created_at", "type": "timestamp", "default": "now()", "description": "Record creation time"},
            {"name": "updated_at", "type": "timestamp", "default": "now()", "description": "Last update time"},
            {"name": "deleted_at", "type": "timestamp", "description": "Soft delete timestamp"}
        ]
    }'::jsonb,
    'manual'
);

-- Pattern 2: Soft Delete
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'soft_delete',
    'audit',
    'Mark records as deleted without physical removal',
    '{"entity": {"type": "string", "required": true}}'::jsonb,
    '{
        "fields": [
            {"name": "deleted_at", "type": "timestamp", "description": "Soft delete timestamp"},
            {"name": "deleted_by", "type": "ref(User)", "description": "User who deleted"}
        ],
        "actions": [
            {
                "name": "soft_delete",
                "steps": [
                    {"validate": "deleted_at IS NULL"},
                    {"update": "{{entity}} SET deleted_at = now(), deleted_by = current_user_id"}
                ]
            },
            {
                "name": "restore",
                "steps": [
                    {"validate": "deleted_at IS NOT NULL"},
                    {"update": "{{entity}} SET deleted_at = NULL, deleted_by = NULL"}
                ]
            }
        ]
    }'::jsonb,
    'manual'
);

-- Pattern 3: State Machine
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'state_machine',
    'state_machine',
    'Finite state machine with configurable states and transitions',
    '{
        "entity": {"type": "string", "required": true},
        "states": {"type": "array", "default": ["draft", "active", "archived"], "description": "Valid states"},
        "initial_state": {"type": "string", "default": "draft"}
    }'::jsonb,
    '{
        "fields": [
            {"name": "status", "type": "enum({{states}})", "default": "{{initial_state}}"},
            {"name": "status_changed_at", "type": "timestamp"},
            {"name": "previous_status", "type": "enum({{states}})"}
        ],
        "actions": [
            {
                "name": "transition_state",
                "steps": [
                    {"validate": "new_status IN {{states}}"},
                    {"update": "{{entity}} SET previous_status = status, status = new_status, status_changed_at = now()"}
                ]
            }
        ]
    }'::jsonb,
    'manual'
);

-- Pattern 4: Approval Workflow
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'approval_workflow',
    'workflow',
    'Two-stage approval workflow: pending -> approved/rejected',
    '{
        "entity": {"type": "string", "required": true},
        "approver_role": {"type": "string", "default": "manager"}
    }'::jsonb,
    '{
        "fields": [
            {"name": "approval_status", "type": "enum(pending, approved, rejected)", "default": "pending"},
            {"name": "approved_by", "type": "ref(User)"},
            {"name": "approved_at", "type": "timestamp"},
            {"name": "rejection_reason", "type": "text"}
        ],
        "actions": [
            {
                "name": "approve",
                "steps": [
                    {"validate": "approval_status = ''pending''"},
                    {"validate": "current_user_has_role(''{{approver_role}}'')"},
                    {"update": "{{entity}} SET approval_status = ''approved'', approved_by = current_user_id, approved_at = now()"},
                    {"notify": "submitter", "template": "approval_granted"}
                ]
            },
            {
                "name": "reject",
                "steps": [
                    {"validate": "approval_status = ''pending''"},
                    {"validate": "current_user_has_role(''{{approver_role}}'')"},
                    {"update": "{{entity}} SET approval_status = ''rejected'', rejection_reason = :reason"},
                    {"notify": "submitter", "template": "approval_rejected"}
                ]
            }
        ]
    }'::jsonb,
    'manual'
);

-- Pattern 5: Validation Chain
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'validation_chain',
    'validation',
    'Sequential validation steps with error accumulation',
    '{"entity": {"type": "string", "required": true}}'::jsonb,
    '{
        "actions": [
            {
                "name": "validate_entity",
                "steps": [
                    {"validate": "field1 IS NOT NULL", "error": "Field1 is required"},
                    {"validate": "field2 > 0", "error": "Field2 must be positive"},
                    {"validate": "field3 IN (''valid1'', ''valid2'')", "error": "Invalid field3 value"}
                ]
            }
        ]
    }'::jsonb,
    'manual'
);

-- Display seeded patterns
SELECT name, category, description FROM domain_patterns;
```

Run seed:

```bash
psql $SPECQL_DB_URL -f database/seed_patterns.sql
```

### 0.4 Python Dependencies

**File**: `pyproject.toml` (extend)

```toml
[project.optional-dependencies]
patterns = [
    "psycopg[binary]>=3.1.0",      # PostgreSQL driver
    "pgvector>=0.2.0",              # pgvector integration
    "sentence-transformers>=2.2.0", # Embeddings (CPU-friendly)
    "numpy>=1.24.0",                # Math operations
    "rich>=13.0.0",                 # CLI formatting
]
```

Install:

```bash
cd ~/code/specql
uv sync --extra patterns

# Verify
uv run python -c "import psycopg; print('✓ psycopg ready')"
uv run python -c "from pgvector.psycopg import register_vector; print('✓ pgvector ready')"
uv run python -c "from sentence_transformers import SentenceTransformer; print('✓ embeddings ready')"
```

### 0.5 Week 1 Deliverables

- [ ] PostgreSQL database setup (15 min)
- [ ] Schema created with pgvector (5 min)
- [ ] Seed patterns loaded (5 patterns)
- [ ] Python dependencies installed
- [ ] Connection verified
- [ ] Baseline metrics captured

**Success Criteria**:
```bash
# Test pgvector is working
psql $SPECQL_DB_URL -c "SELECT vector '[1,2,3]' <=> vector '[4,5,6]';"
# Expected: Returns a distance value

# Test patterns loaded
psql $SPECQL_DB_URL -c "SELECT COUNT(*) FROM pattern_library.domain_patterns;"
# Expected: 5

# Test embeddings ready
uv run python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('all-MiniLM-L6-v2'); print(m.encode('test').shape)"
# Expected: (384,)
```

---

## Phase 1: Pattern Embeddings & RAG (Weeks 2-3)

### Goals
- Generate embeddings for all patterns
- Implement pgvector-based retrieval
- Integrate RAG into reverse engineering
- Test hybrid search (vector + text + filters)

### 1.1 Pattern Embedding Service

**File**: `src/pattern_library/embeddings_pg.py`

```python
"""Pattern embedding service using PostgreSQL + pgvector."""

from sentence_transformers import SentenceTransformer
import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from typing import Dict, List, Optional
from pathlib import Path
import os

class PatternEmbeddingService:
    """
    Generate and manage pattern embeddings using PostgreSQL + pgvector.

    Features:
    - CPU-friendly sentence-transformers
    - Native pgvector storage and similarity search
    - HNSW index for 100x speedup
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize embedding service.

        Args:
            connection_string: PostgreSQL connection string (or uses SPECQL_DB_URL env)
            model_name: Sentence transformer model (384-dim, fast on CPU)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        # Connect to PostgreSQL
        self.conn_string = connection_string or os.getenv('SPECQL_DB_URL')
        if not self.conn_string:
            raise ValueError("No connection string provided and SPECQL_DB_URL not set")

        self.conn = psycopg.connect(self.conn_string)
        register_vector(self.conn)

        print(f"✓ Embedding service ready ({model_name}, PostgreSQL + pgvector)")

    def embed_pattern(self, pattern: Dict) -> np.ndarray:
        """
        Generate embedding for a domain pattern.

        Combines:
        - Pattern name and description
        - Category
        - Field names
        - Action names

        Returns:
            384-dim numpy array
        """
        text = self._pattern_to_text(pattern)
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.astype(np.float32)

    def embed_function(self, sql: str, description: str = "") -> np.ndarray:
        """Generate embedding for SQL function."""
        text = f"{description}\n{sql}" if description else sql
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.astype(np.float32)

    def update_pattern_embedding(self, pattern_id: int, embedding: np.ndarray):
        """Update pattern with embedding (native pgvector!)."""
        self.conn.execute(
            """
            UPDATE pattern_library.domain_patterns
            SET embedding = %s
            WHERE id = %s
            """,
            (embedding, pattern_id)
        )
        self.conn.commit()

    def generate_all_embeddings(self):
        """Batch generate embeddings for all patterns without embeddings."""
        cursor = self.conn.execute(
            """
            SELECT id, name, category, description, parameters, implementation
            FROM pattern_library.domain_patterns
            WHERE embedding IS NULL
            """
        )

        patterns = cursor.fetchall()
        print(f"Generating embeddings for {len(patterns)} patterns...")

        for i, row in enumerate(patterns, 1):
            pattern_id, name, category, description, parameters, implementation = row

            pattern = {
                'name': name,
                'category': category,
                'description': description,
                'parameters': parameters,
                'implementation': implementation
            }

            embedding = self.embed_pattern(pattern)
            self.update_pattern_embedding(pattern_id, embedding)

            if i % 10 == 0:
                print(f"  {i}/{len(patterns)} complete")

        print(f"✓ {len(patterns)} embeddings generated")

    def retrieve_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.5,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve top-K similar patterns using native pgvector.

        Uses HNSW index for fast approximate nearest neighbor search.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            category_filter: Optional category filter

        Returns:
            List of {pattern_id, name, category, description, similarity, ...}
        """
        # Build query
        query = """
            SELECT
                id,
                name,
                category,
                description,
                parameters,
                1 - (embedding <=> %s) AS similarity
            FROM pattern_library.domain_patterns
            WHERE embedding IS NOT NULL
                AND deprecated = FALSE
                AND (1 - (embedding <=> %s)) >= %s
        """

        params = [query_embedding, query_embedding, threshold]

        if category_filter:
            query += " AND category = %s"
            params.append(category_filter)

        query += " ORDER BY embedding <=> %s LIMIT %s"
        params.extend([query_embedding, top_k])

        # Execute
        cursor = self.conn.execute(query, params)

        results = []
        for row in cursor:
            results.append({
                'pattern_id': row[0],
                'name': row[1],
                'category': row[2],
                'description': row[3],
                'parameters': row[4],
                'similarity': float(row[5])
            })

        return results

    def hybrid_search(
        self,
        query_embedding: np.ndarray,
        query_text: Optional[str] = None,
        category_filter: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Hybrid search: vector similarity + full-text search + filters.

        Uses PostgreSQL function for optimized query.
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM pattern_library.hybrid_pattern_search(
                %s, %s, %s, %s
            )
            """,
            (query_embedding, query_text, category_filter, top_k)
        )

        results = []
        for row in cursor:
            results.append({
                'pattern_id': row[0],
                'name': row[1],
                'category': row[2],
                'description': row[3],
                'combined_score': float(row[4])
            })

        return results

    def _pattern_to_text(self, pattern: Dict) -> str:
        """Convert pattern to searchable text."""
        parts = [
            f"Pattern: {pattern.get('name', '')}",
            f"Category: {pattern.get('category', '')}",
            f"Description: {pattern.get('description', '')}"
        ]

        # Add field names if available
        impl = pattern.get('implementation', {})
        if isinstance(impl, dict) and 'fields' in impl:
            field_names = [f.get('name', '') for f in impl['fields']]
            parts.append(f"Fields: {', '.join(field_names)}")

        # Add action names
        if isinstance(impl, dict) and 'actions' in impl:
            action_names = [a.get('name', '') for a in impl['actions']]
            parts.append(f"Actions: {', '.join(action_names)}")

        return " | ".join(parts)

    def close(self):
        """Close database connection."""
        self.conn.close()
```

### 1.2 Grok LLM Provider

**File**: `src/reverse_engineering/grok_provider.py`

```python
"""Grok LLM provider using OpenCode CLI."""

import subprocess
import json
import time
import tempfile
import uuid
from pathlib import Path
from typing import Optional
import psycopg
import os

class GrokProvider:
    """
    Grok Code Fast 1 provider via OpenCode CLI.

    Features:
    - FREE (no API costs)
    - Fast (1-3s response time)
    - Good at structured output (JSON)
    - Logs calls to PostgreSQL for metrics
    """

    def __init__(self, log_to_db: bool = True):
        """
        Initialize Grok provider.

        Args:
            log_to_db: Whether to log calls to PostgreSQL for metrics
        """
        self.model = "opencode/grok-code"
        self.log_to_db = log_to_db

        # Verify opencode is available
        try:
            result = subprocess.run(
                ["which", "opencode"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("opencode not found in PATH")
        except Exception as e:
            raise RuntimeError(f"Failed to verify opencode: {e}")

        # Database connection for logging
        if log_to_db:
            conn_string = os.getenv('SPECQL_DB_URL')
            if conn_string:
                try:
                    self.db_conn = psycopg.connect(conn_string)
                except Exception as e:
                    print(f"Warning: Could not connect to DB for logging: {e}")
                    self.db_conn = None
            else:
                self.db_conn = None
        else:
            self.db_conn = None

        print(f"✓ Grok provider ready (model: {self.model}, FREE)")

    def call(
        self,
        prompt: str,
        task_type: str = "general",
        timeout: int = 30
    ) -> str:
        """
        Call Grok via OpenCode CLI.

        Args:
            prompt: Prompt to send to Grok
            task_type: Type of task (for logging)
            timeout: Timeout in seconds

        Returns:
            Grok's response as string
        """
        call_id = str(uuid.uuid4())
        start_time = time.time()
        prompt_hash = str(hash(prompt))

        try:
            # Write prompt to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(prompt)
                prompt_file = f.name

            # Call opencode
            result = subprocess.run(
                ["opencode", "run", "--model", self.model],
                stdin=open(prompt_file),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Clean up
            Path(prompt_file).unlink()

            if result.returncode != 0:
                raise RuntimeError(f"Grok call failed: {result.stderr}")

            response = result.stdout.strip()
            latency_ms = int((time.time() - start_time) * 1000)

            # Log call
            if self.log_to_db and self.db_conn:
                self._log_call(
                    call_id=call_id,
                    task_type=task_type,
                    prompt_length=len(prompt),
                    response_length=len(response),
                    prompt_hash=prompt_hash,
                    latency_ms=latency_ms,
                    success=True
                )

            return response

        except subprocess.TimeoutExpired:
            if self.log_to_db and self.db_conn:
                self._log_call(
                    call_id=call_id,
                    task_type=task_type,
                    prompt_length=len(prompt),
                    response_length=0,
                    prompt_hash=prompt_hash,
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error_message=f"Timeout after {timeout}s"
                )
            raise RuntimeError(f"Grok call timed out after {timeout}s")

        except Exception as e:
            if self.log_to_db and self.db_conn:
                self._log_call(
                    call_id=call_id,
                    task_type=task_type,
                    prompt_length=len(prompt),
                    response_length=0,
                    prompt_hash=prompt_hash,
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error_message=str(e)
                )
            raise RuntimeError(f"Grok call failed: {e}")

    def call_json(
        self,
        prompt: str,
        task_type: str = "general",
        max_retries: int = 2
    ) -> dict:
        """
        Call Grok and parse JSON response.

        Retries if JSON parsing fails.
        """
        for attempt in range(max_retries):
            response = self.call(prompt, task_type)

            try:
                # Try to parse as JSON
                return json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass

                # If last attempt, raise error
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to parse JSON from Grok response: {response[:200]}")

                # Retry with more explicit instructions
                prompt = f"{prompt}\n\nIMPORTANT: Output ONLY valid JSON, no markdown, no explanations."

        raise ValueError("Failed to get valid JSON from Grok")

    def _log_call(
        self,
        call_id: str,
        task_type: str,
        prompt_length: int,
        response_length: int,
        prompt_hash: str,
        latency_ms: int,
        success: bool,
        error_message: str = None
    ):
        """Log Grok call to PostgreSQL."""
        try:
            self.db_conn.execute(
                """
                INSERT INTO pattern_library.grok_call_logs
                (call_id, task_type, prompt_length, response_length,
                 prompt_hash, latency_ms, success, error_message, cost_usd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0.0)
                """,
                (call_id, task_type, prompt_length, response_length,
                 prompt_hash, latency_ms, success, error_message)
            )
            self.db_conn.commit()
        except Exception:
            # Don't fail on logging errors
            pass

    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()
```

### 1.3 CLI Integration

**File**: `src/cli/embeddings.py` (NEW)

```python
"""CLI commands for pattern embeddings."""

import click
from rich.console import Console
from rich.progress import Progress
from pathlib import Path
import os

console = Console()

@click.group(name="embeddings")
def embeddings_cli():
    """Pattern embedding management."""
    pass

@embeddings_cli.command(name="generate")
def generate_embeddings():
    """Generate embeddings for all patterns without embeddings."""
    from src.pattern_library.embeddings_pg import PatternEmbeddingService

    console.print("[cyan]Generating embeddings...[/cyan]")

    service = PatternEmbeddingService()
    service.generate_all_embeddings()
    service.close()

    console.print("[green]✓ Embeddings generated successfully[/green]")

@embeddings_cli.command(name="test-retrieval")
@click.argument("query", type=str)
@click.option("--top-k", default=5, help="Number of results")
def test_retrieval(query: str, top_k: int):
    """Test pattern retrieval with a query."""
    from src.pattern_library.embeddings_pg import PatternEmbeddingService

    service = PatternEmbeddingService()

    # Generate query embedding
    query_embedding = service.embed_function(query)

    # Retrieve similar patterns
    results = service.retrieve_similar(query_embedding, top_k=top_k)

    # Display results
    from rich.table import Table
    table = Table(title=f"Top-{top_k} Similar Patterns")
    table.add_column("Pattern", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Similarity", style="yellow")
    table.add_column("Description", style="dim")

    for r in results:
        table.add_row(
            r['name'],
            r['category'],
            f"{r['similarity']:.3f}",
            r['description'][:60] + "..." if len(r['description']) > 60 else r['description']
        )

    console.print(table)
    service.close()
```

### 1.4 Week 2-3 Deliverables

**Week 2**:
- [ ] `src/pattern_library/embeddings_pg.py` - PostgreSQL + pgvector embedding service
- [ ] `src/reverse_engineering/grok_provider.py` - Grok LLM provider
- [ ] Generate embeddings for seed patterns
- [ ] Tests for embedding generation and storage

**Week 3**:
- [ ] `src/cli/embeddings.py` - CLI commands
- [ ] Integration with `specql reverse --with-patterns`
- [ ] Test hybrid search (vector + text)
- [ ] Benchmark: retrieval performance with HNSW index

**Success Criteria**:
- [ ] All patterns have embeddings in PostgreSQL
- [ ] Retrieval returns relevant patterns (>70% accuracy on 20 queries)
- [ ] Hybrid search works (vector + text + category filter)
- [ ] Performance: <50ms for top-10 from 100 patterns

---

## Phase 2: Pattern Discovery (Weeks 4-5)

### Goals
- Automatically suggest patterns from legacy SQL
- Human review workflow via CLI
- Pattern approval → pattern library

### Implementation

Similar structure to SQLite version, but using PostgreSQL:
- `src/pattern_library/suggestion_service_pg.py`
- CLI commands: `specql patterns review-suggestions`, `show`, `approve`, `reject`
- Integration with `specql reverse --discover-patterns`

**Key Difference**: All JSONB queries benefit from GIN indexes (20x faster than SQLite)

### Week 4-5 Deliverables

- [ ] Pattern discovery logic in `ai_enhancer.py`
- [ ] `src/pattern_library/suggestion_service_pg.py`
- [ ] CLI commands for review workflow
- [ ] Integration tests
- [ ] Documentation

---

## Phase 3: NL Pattern Generation (Weeks 6-7)

### Goals
- Users describe patterns in natural language
- Grok generates structured SpecQL patterns
- Validation pipeline
- PostgreSQL storage

### Week 6-7 Deliverables

- [ ] `src/pattern_library/nl_generator.py`
- [ ] CLI command `patterns create-from-description`
- [ ] Validation logic (JSON schema, SpecQL syntax, conventions)
- [ ] Tests
- [ ] Documentation

---

## Phase 4: Integration & Testing (Week 8)

### Goals
- End-to-end testing
- Performance benchmarks
- Documentation
- Demo preparation

### Deliverables

- [ ] Integration tests (full workflows)
- [ ] Performance benchmarks (embeddings, retrieval, Grok)
- [ ] User documentation
- [ ] Demo video/script
- [ ] Production deployment guide

---

## Cost Analysis

| Component | Cost |
|-----------|------|
| **OpenCode Grok** | $0 (free) |
| **PostgreSQL** | $0 (local) |
| **Hardware** | $0 (existing X270) |
| **Dependencies** | $0 (open source) |
| **Total** | **$0** ✅ |

---

## Performance Targets

| Operation | Target | Expected (PostgreSQL + HNSW) |
|-----------|--------|------------------------------|
| Embedding generation | <100ms | 50-80ms (CPU) |
| Pattern retrieval (10 patterns) | <50ms | 10-30ms (HNSW index) |
| Pattern retrieval (1000 patterns) | <200ms | 50-100ms (HNSW index) |
| JSONB query | <20ms | 5-15ms (GIN index) |
| Hybrid search | <100ms | 30-80ms |
| Grok call | <5s | 2-3s (tested) |
| End-to-end reverse engineering | <15s | 8-12s |

**100x improvement over SQLite for large scale!**

---

## Migration Path: Future Scaling

### When Pattern Library Grows (>10,000 patterns)

PostgreSQL scales naturally:
- ✅ HNSW index still <100ms
- ✅ Concurrent users (MVCC)
- ✅ Replication for high availability
- ✅ Partitioning for massive scale

### When Need GPU-Accelerated LLM

Easy upgrade path:
1. Keep PostgreSQL (no change!)
2. Add local Llama 3.1 8B with GPU
3. Use Grok as fallback
4. Pattern library unchanged

---

## Success Criteria

### Technical Success
- [ ] PostgreSQL + pgvector working perfectly
- [ ] HNSW index provides <50ms retrieval
- [ ] All phases implemented
- [ ] Tests passing
- [ ] Zero LLM costs

### Quality Success
- [ ] Pattern retrieval accuracy >75%
- [ ] Pattern discovery rate 5-10%
- [ ] NL pattern quality >70% valid
- [ ] No critical bugs

### Production Readiness
- [ ] Multi-user capable (PostgreSQL MVCC)
- [ ] Backups automated (pg_dump)
- [ ] Monitoring in place (pg_stat views)
- [ ] Documentation complete

---

## Next Steps

1. ✅ Run setup script: `./scripts/setup_database.sh`
2. ✅ Create schema: `psql $SPECQL_DB_URL -f database/pattern_library_schema.sql`
3. ✅ Seed patterns: `psql $SPECQL_DB_URL -f database/seed_patterns.sql`
4. ✅ Install dependencies: `uv sync --extra patterns`
5. ✅ Generate embeddings: `specql embeddings generate`
6. ✅ Test retrieval: `specql embeddings test-retrieval "approval workflow"`

---

## Conclusion

This implementation leverages:
- ✅ **PostgreSQL 17.6 + pgvector** (100x faster vector search)
- ✅ **OpenCode Grok** (free, fast, good quality)
- ✅ **X270 laptop** (CPU-friendly, sufficient)
- ✅ **Same database** as SpecQL schemas (critical integration)

**Result**: Production-ready pattern library with $0 cost, native vector search, and seamless SpecQL integration.

---

**Document Version**: 2.0 (PostgreSQL + Grok)
**Hardware**: Lenovo X270
**Database**: PostgreSQL 17.6 + pgvector
**LLM**: OpenCode Grok Code Fast 1 (FREE)
**Status**: Ready to Execute
**Last Updated**: 2025-11-12
