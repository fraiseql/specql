"""
Tests for OutboxGenerator
"""

from src.generators.cdc.outbox_generator import OutboxGenerator


class TestOutboxGenerator:
    """Test outbox table generation"""

    def test_generate_outbox_table(self):
        """Test outbox table generation includes all required columns and indexes"""
        generator = OutboxGenerator()
        sql = generator.generate_outbox_table()

        # Core columns
        assert "aggregate_type TEXT NOT NULL" in sql
        assert "aggregate_id UUID NOT NULL" in sql
        assert "event_type TEXT NOT NULL" in sql
        assert "event_payload JSONB NOT NULL" in sql
        assert "event_metadata JSONB" in sql

        # Tracking columns
        assert "created_at TIMESTAMPTZ" in sql
        assert "processed_at TIMESTAMPTZ" in sql
        assert "processed_by TEXT" in sql

        # Tracing columns
        assert "trace_id TEXT" in sql
        assert "correlation_id UUID" in sql
        assert "causation_id UUID" in sql

        # Indexes
        assert "idx_outbox_unprocessed" in sql
        assert "WHERE processed_at IS NULL" in sql
        assert "idx_outbox_aggregate" in sql
        assert "idx_outbox_tenant" in sql
        assert "idx_outbox_event_type" in sql

    def test_generate_outbox_helper_functions(self):
        """Test outbox helper functions are generated"""
        generator = OutboxGenerator()
        sql = generator.generate_outbox_helper_functions()

        # Helper functions
        assert "write_outbox_event" in sql
        assert "mark_outbox_processed" in sql
        assert "cleanup_outbox" in sql

    def test_generate_outbox_views(self):
        """Test outbox monitoring views are generated"""
        generator = OutboxGenerator()
        sql = generator.generate_outbox_views()

        # Views
        assert "v_outbox_pending" in sql
        assert "v_outbox_stats" in sql
        assert "v_outbox_recent" in sql

    def test_generate_all(self):
        """Test complete outbox infrastructure generation"""
        generator = OutboxGenerator()
        sql = generator.generate_all()

        # Should contain all components
        assert "CREATE TABLE IF NOT EXISTS app.outbox" in sql
        assert "write_outbox_event" in sql
        assert "v_outbox_pending" in sql
