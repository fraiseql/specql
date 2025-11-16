"""
Tests for AuditGenerator
"""

from src.generators.enterprise.audit_generator import AuditGenerator


class TestAuditGenerator:
    """Test audit trail generation"""

    def test_generate_audit_trail_basic(self):
        """Test basic audit trail generation without cascade"""
        generator = AuditGenerator()
        sql = generator.generate_audit_trail(
            entity_name="Post",
            fields=["title", "content"],
            audit_config={"enabled": True},
        )

        # Should include basic audit table
        assert "CREATE TABLE IF NOT EXISTS app.audit_post" in sql
        assert "audit_id UUID PRIMARY KEY" in sql
        assert "entity_id UUID NOT NULL" in sql
        assert "operation_type TEXT" in sql

        # Should include basic indexes
        assert "idx_audit_post_entity_id" in sql
        assert "idx_audit_post_tenant_id" in sql
        assert "idx_audit_post_changed_at" in sql

        # Should include trigger function
        assert "CREATE OR REPLACE FUNCTION app.audit_trigger_post()" in sql

        # Should include query function
        assert "get_post_audit_history" in sql

        # Should NOT include cascade columns (not enabled)
        assert "cascade_data JSONB" not in sql
        assert "cascade_entities TEXT[]" not in sql

    def test_audit_generator_includes_cascade_column(self):
        """Audit tables should include cascade_data column when enabled"""
        generator = AuditGenerator()
        sql = generator.generate_audit_trail(
            entity_name="Post",
            fields=["title", "content"],
            audit_config={"enabled": True, "include_cascade": True},
        )

        # Should include cascade_data column
        assert "cascade_data JSONB" in sql

        # Should include cascade_entities array for quick filtering
        assert "cascade_entities TEXT[]" in sql

        # Should include GIN index on cascade_entities
        assert "idx_audit_post_cascade_entities" in sql
        assert "USING GIN (cascade_entities)" in sql

    def test_audit_trail_without_cascade_disabled_by_default(self):
        """Cascade columns should not be included by default"""
        generator = AuditGenerator()
        sql = generator.generate_audit_trail(
            entity_name="User",
            fields=["name", "email"],
            audit_config={"enabled": True},  # No include_cascade
        )

        # Should NOT include cascade columns
        assert "cascade_data JSONB" not in sql
        assert "cascade_entities TEXT[]" not in sql
        assert "idx_audit_user_cascade_entities" not in sql

    def test_audit_trail_with_cascade_explicitly_disabled(self):
        """Cascade columns should not be included when explicitly disabled"""
        generator = AuditGenerator()
        sql = generator.generate_audit_trail(
            entity_name="Comment",
            fields=["text"],
            audit_config={"enabled": True, "include_cascade": False},
        )

        # Should NOT include cascade columns
        assert "cascade_data JSONB" not in sql
        assert "cascade_entities TEXT[]" not in sql
        assert "idx_audit_comment_cascade_entities" not in sql
