"""
CDC Outbox Pattern Generator

Generates transactional outbox tables and helper functions for
event-driven architecture with Debezium integration.
"""



class OutboxGenerator:
    """Generates CDC outbox infrastructure"""

    def generate_outbox_table(self) -> str:
        """Generate app.outbox table for CDC"""
        return """
-- Transactional Outbox Table for CDC
CREATE TABLE IF NOT EXISTS app.outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event identity
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    event_version INTEGER DEFAULT 1,

    -- Event payload
    event_payload JSONB NOT NULL,
    event_metadata JSONB,  -- Includes cascade data, tracing, etc.

    -- Routing
    tenant_id UUID,
    partition_key TEXT,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ,
    processed_by TEXT,

    -- Distributed tracing
    trace_id TEXT,
    correlation_id UUID,
    causation_id UUID,

    -- Audit link
    audit_id UUID,

    -- Error handling
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,

    -- Constraints
    CONSTRAINT chk_event_type CHECK (
        event_type ~ '^[A-Z][a-zA-Z]*$'  -- PascalCase
    )
);

-- Unprocessed events (Debezium polling)
CREATE INDEX IF NOT EXISTS idx_outbox_unprocessed
    ON app.outbox (created_at)
    WHERE processed_at IS NULL;

-- Aggregate lookups
CREATE INDEX IF NOT EXISTS idx_outbox_aggregate
    ON app.outbox (aggregate_type, aggregate_id);

-- Multi-tenant routing
CREATE INDEX IF NOT EXISTS idx_outbox_tenant
    ON app.outbox (tenant_id)
    WHERE tenant_id IS NOT NULL;

-- Event type filtering
CREATE INDEX IF NOT EXISTS idx_outbox_event_type
    ON app.outbox (event_type);

-- Correlation tracking
CREATE INDEX IF NOT EXISTS idx_outbox_correlation
    ON app.outbox (correlation_id)
    WHERE correlation_id IS NOT NULL;

-- Comment for documentation
COMMENT ON TABLE app.outbox IS
'Transactional outbox for CDC (Change Data Capture) via Debezium. Events written here are streamed to Kafka.';
"""

    def generate_outbox_helper_functions(self) -> str:
        """Generate helper functions for writing to outbox"""
        return """
-- Helper: Write event to outbox
CREATE OR REPLACE FUNCTION app.write_outbox_event(
    p_aggregate_type TEXT,
    p_aggregate_id UUID,
    p_event_type TEXT,
    p_event_payload JSONB,
    p_event_metadata JSONB DEFAULT NULL,
    p_tenant_id UUID DEFAULT NULL,
    p_trace_id TEXT DEFAULT NULL,
    p_correlation_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    INSERT INTO app.outbox (
        aggregate_type,
        aggregate_id,
        event_type,
        event_payload,
        event_metadata,
        tenant_id,
        partition_key,
        trace_id,
        correlation_id
    ) VALUES (
        p_aggregate_type,
        p_aggregate_id,
        p_event_type,
        p_event_payload,
        p_event_metadata,
        p_tenant_id,
        p_aggregate_id::text,  -- Use aggregate_id as partition key
        p_trace_id,
        p_correlation_id
    )
    RETURNING id INTO v_event_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- Helper: Mark event as processed (called by Debezium)
CREATE OR REPLACE FUNCTION app.mark_outbox_processed(
    p_event_id UUID,
    p_processor_id TEXT DEFAULT 'debezium'
) RETURNS void AS $$
BEGIN
    UPDATE app.outbox
    SET
        processed_at = now(),
        processed_by = p_processor_id
    WHERE id = p_event_id;
END;
$$ LANGUAGE plpgsql;

-- Cleanup: Delete old processed events
CREATE OR REPLACE FUNCTION app.cleanup_outbox(
    p_retention_days INTEGER DEFAULT 7
) RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM app.outbox
    WHERE processed_at IS NOT NULL
      AND processed_at < now() - (p_retention_days || ' days')::interval;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;
"""

    def generate_outbox_views(self) -> str:
        """Generate views for monitoring outbox"""
        return """
-- View: Unprocessed events
CREATE OR REPLACE VIEW app.v_outbox_pending AS
SELECT
    id,
    aggregate_type,
    aggregate_id,
    event_type,
    created_at,
    retry_count,
    last_error,
    age(now(), created_at) as pending_duration
FROM app.outbox
WHERE processed_at IS NULL
ORDER BY created_at ASC;

-- View: Event processing stats
CREATE OR REPLACE VIEW app.v_outbox_stats AS
SELECT
    event_type,
    COUNT(*) as total_events,
    COUNT(*) FILTER (WHERE processed_at IS NOT NULL) as processed,
    COUNT(*) FILTER (WHERE processed_at IS NULL) as pending,
    AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) FILTER (WHERE processed_at IS NOT NULL) as avg_processing_seconds,
    MAX(created_at) as latest_event
FROM app.outbox
GROUP BY event_type
ORDER BY total_events DESC;

-- View: Recent events
CREATE OR REPLACE VIEW app.v_outbox_recent AS
SELECT
    id,
    aggregate_type,
    aggregate_id,
    event_type,
    created_at,
    processed_at,
    EXTRACT(EPOCH FROM (COALESCE(processed_at, now()) - created_at)) as processing_seconds
FROM app.outbox
WHERE created_at > now() - interval '1 hour'
ORDER BY created_at DESC;
"""

    def generate_all(self) -> str:
        """Generate complete outbox infrastructure"""
        return "\n\n".join([
            self.generate_outbox_table(),
            self.generate_outbox_helper_functions(),
            self.generate_outbox_views()
        ])