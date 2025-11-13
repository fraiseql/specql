-- ============================================================================
-- Self-Schema Post-Processing: Advanced Features
-- ============================================================================
-- This script adds specialized database features that SpecQL doesn't generate
-- automatically, such as vector embeddings, advanced indexes, and complex constraints.
--
-- Run this AFTER deploying the generated Trinity schema.

-- Enable pgvector extension (required for vector operations)
CREATE EXTENSION IF NOT EXISTS vector;

-- Set search path for pattern_library operations
SET search_path TO pattern_library, specql_registry, app, public;

-- ============================================================================
-- 1. VECTOR EMBEDDINGS FOR PATTERN LIBRARY
-- ============================================================================

-- Add vector embedding column to tv_domainpattern
-- Uses all-MiniLM-L6-v2 dimension (384) for semantic search
ALTER TABLE pattern_library.tv_domainpattern
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Add vector embedding column to tv_entitytemplate
ALTER TABLE pattern_library.tv_entitytemplate
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- ============================================================================
-- 2. ADVANCED INDEXES FOR VECTOR SEARCH
-- ============================================================================

-- HNSW index for domain patterns (fast approximate nearest neighbor)
-- 100x faster than brute-force cosine similarity for large datasets
CREATE INDEX IF NOT EXISTS idx_tv_domainpattern_embedding_hnsw
ON pattern_library.tv_domainpattern
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- HNSW index for entity templates
CREATE INDEX IF NOT EXISTS idx_tv_entitytemplate_embedding_hnsw
ON pattern_library.tv_entitytemplate
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat index as alternative (good for smaller datasets, exact search)
CREATE INDEX IF NOT EXISTS idx_tv_domainpattern_embedding_ivfflat
ON pattern_library.tv_domainpattern
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_tv_entitytemplate_embedding_ivfflat
ON pattern_library.tv_entitytemplate
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- 3. COMPLEX CHECK CONSTRAINTS
-- ============================================================================

-- Add complex validation constraints to domain patterns
ALTER TABLE pattern_library.tv_domainpattern
ADD CONSTRAINT IF NOT EXISTS chk_domainpattern_category
CHECK (data->>'category' IN (
    'workflow', 'validation', 'audit', 'hierarchy',
    'state_machine', 'approval', 'notification',
    'calculation', 'soft_delete', 'data_modeling'
));

ALTER TABLE pattern_library.tv_domainpattern
ADD CONSTRAINT IF NOT EXISTS chk_domainpattern_complexity
CHECK (
    (data->>'complexity_score')::float >= 0.0 AND
    (data->>'complexity_score')::float <= 10.0
);

-- Add validation for entity templates
ALTER TABLE pattern_library.tv_entitytemplate
ADD CONSTRAINT IF NOT EXISTS chk_entitytemplate_actions_valid
CHECK (jsonb_array_length(data->'actions') > 0);

-- ============================================================================
-- 4. FULL-TEXT SEARCH CAPABILITIES
-- ============================================================================

-- Add generated search vector column for domain patterns
ALTER TABLE pattern_library.tv_domainpattern
ADD COLUMN IF NOT EXISTS search_vector tsvector
GENERATED ALWAYS AS (
    to_tsvector('english',
        coalesce(data->>'name', '') || ' ' ||
        coalesce(data->>'description', '') || ' ' ||
        coalesce(data->>'category', '') || ' ' ||
        coalesce(data->>'tags', '')
    )
) STORED;

-- GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_tv_domainpattern_search
ON pattern_library.tv_domainpattern
USING gin (search_vector);

-- Add search vector for entity templates
ALTER TABLE pattern_library.tv_entitytemplate
ADD COLUMN IF NOT EXISTS search_vector tsvector
GENERATED ALWAYS AS (
    to_tsvector('english',
        coalesce(data->>'name', '') || ' ' ||
        coalesce(data->>'description', '') || ' ' ||
        coalesce(data->>'entity_type', '')
    )
) STORED;

CREATE INDEX IF NOT EXISTS idx_tv_entitytemplate_search
ON pattern_library.tv_entitytemplate
USING gin (search_vector);

-- ============================================================================
-- 5. PERFORMANCE INDEXES FOR COMMON QUERIES
-- ============================================================================

-- Composite indexes for pattern queries
CREATE INDEX IF NOT EXISTS idx_tv_domainpattern_category_usage
ON pattern_library.tv_domainpattern (data->>'category', (data->>'times_instantiated')::int DESC);

CREATE INDEX IF NOT EXISTS idx_tv_domainpattern_complexity
ON pattern_library.tv_domainpattern ((data->>'complexity_score')::float DESC);

-- Index for entity template queries
CREATE INDEX IF NOT EXISTS idx_tv_entitytemplate_type
ON pattern_library.tv_entitytemplate (data->>'entity_type');

-- ============================================================================
-- 6. TRIGGERS FOR AUTOMATED MAINTENANCE
-- ============================================================================

-- Function to update refreshed_at timestamp
CREATE OR REPLACE FUNCTION pattern_library.update_refreshed_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.refreshed_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for domain patterns
CREATE OR REPLACE TRIGGER trg_tv_domainpattern_refresh
    BEFORE UPDATE ON pattern_library.tv_domainpattern
    FOR EACH ROW
    EXECUTE FUNCTION pattern_library.update_refreshed_at();

-- Trigger for entity templates
CREATE OR REPLACE TRIGGER trg_tv_entitytemplate_refresh
    BEFORE UPDATE ON pattern_library.tv_entitytemplate
    FOR EACH ROW
    EXECUTE FUNCTION pattern_library.update_refreshed_at();

-- ============================================================================
-- 7. HELPER FUNCTIONS FOR TRINITY PATTERN
-- ============================================================================

-- Function to get pattern recommendations based on semantic similarity
CREATE OR REPLACE FUNCTION pattern_library.get_similar_patterns(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    pattern_id uuid,
    pattern_name text,
    similarity float,
    category text,
    description text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dp.id,
        dp.data->>'name',
        1 - (dp.embedding <=> query_embedding) as similarity,
        dp.data->>'category',
        dp.data->>'description'
    FROM pattern_library.tv_domainpattern dp
    WHERE dp.embedding IS NOT NULL
      AND 1 - (dp.embedding <=> query_embedding) > match_threshold
    ORDER BY dp.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to validate pattern data integrity
CREATE OR REPLACE FUNCTION pattern_library.validate_pattern_data()
RETURNS TABLE (
    pattern_id uuid,
    validation_errors text[]
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dp.id,
        ARRAY[
            CASE WHEN dp.data->>'name' IS NULL THEN 'missing_name' ELSE NULL END,
            CASE WHEN dp.data->>'category' IS NULL THEN 'missing_category' ELSE NULL END,
            CASE WHEN NOT (dp.data->>'category' IN ('workflow', 'validation', 'audit', 'hierarchy', 'state_machine', 'approval', 'notification', 'calculation', 'soft_delete', 'data_modeling'))
                 THEN 'invalid_category' ELSE NULL END,
            CASE WHEN (dp.data->>'complexity_score')::float < 0 OR (dp.data->>'complexity_score')::float > 10
                 THEN 'invalid_complexity_score' ELSE NULL END
        ] FILTER (WHERE item IS NOT NULL) as errors
    FROM pattern_library.tv_domainpattern dp
    WHERE array_length(ARRAY[
        CASE WHEN dp.data->>'name' IS NULL THEN 'missing_name' ELSE NULL END,
        CASE WHEN dp.data->>'category' IS NULL THEN 'missing_category' ELSE NULL END,
        CASE WHEN NOT (dp.data->>'category' IN ('workflow', 'validation', 'audit', 'hierarchy', 'state_machine', 'approval', 'notification', 'calculation', 'soft_delete', 'data_modeling'))
             THEN 'invalid_category' ELSE NULL END,
        CASE WHEN (dp.data->>'complexity_score')::float < 0 OR (dp.data->>'complexity_score')::float > 10
             THEN 'invalid_complexity_score' ELSE NULL END
    ] FILTER (WHERE item IS NOT NULL), 1) > 0;
END;
$$;

-- ============================================================================
-- 8. PARTITIONING FOR LARGE DATASETS (Future-Ready)
-- ============================================================================

-- Note: Partitioning can be added later when datasets grow large
-- Example partitioning strategy for domain patterns by category:
--
-- CREATE TABLE pattern_library.tv_domainpattern_y2024m01 PARTITION OF pattern_library.tv_domainpattern
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify vector extension
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension not installed. Install with: CREATE EXTENSION vector;';
    END IF;
END
$$;

-- Verify indexes were created
DO $$
DECLARE
    index_count int;
BEGIN
    SELECT count(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'pattern_library'
      AND tablename LIKE 'tv_%'
      AND indexname LIKE '%embedding%';

    RAISE NOTICE 'Created % vector indexes', index_count;
END
$$;

-- ============================================================================
-- POST-PROCESSING COMPLETE
-- ============================================================================

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Self-schema post-processing completed successfully';
    RAISE NOTICE 'Added: vector embeddings, HNSW/IVFFlat indexes, complex constraints, full-text search, triggers, helper functions';
END
$$;