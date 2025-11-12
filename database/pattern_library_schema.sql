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
COMMENT ON INDEX idx_patterns_embedding IS 'HNSW index for fast approximate nearest neighbor search (100x speedup!)';