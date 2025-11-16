"""
Tests for AuditGenerator enhanced query functions with cascade support
"""

from src.generators.enterprise.audit_generator import AuditGenerator


class TestAuditQueryCascade:
    """Test enhanced audit query functions with cascade support"""

    def test_audit_query_includes_cascade_option(self):
        """Audit query functions should support cascade data retrieval"""
        generator = AuditGenerator()
        sql = generator.generate_audit_query_functions(
            entity_name="Post", audit_config={"include_cascade": True}
        )

        # Should include function with cascade
        assert "get_post_audit_history_with_cascade" in sql

        # Should return cascade_data column
        assert "cascade_data JSONB" in sql

        # Should support filtering by affected entities
        assert "p_affected_entity" in sql

    def test_audit_query_without_cascade_backward_compatible(self):
        """Audit query functions without cascade should work as before"""
        generator = AuditGenerator()
        sql = generator.generate_audit_query_functions(
            entity_name="User", audit_config={"include_cascade": False}
        )

        # Should include standard function
        assert "get_user_audit_history" in sql

        # Should NOT include cascade function
        assert "get_user_audit_history_with_cascade" not in sql

        # Should NOT include cascade columns in return type
        assert "cascade_data JSONB" not in sql

    def test_audit_query_cascade_disabled_by_default(self):
        """Cascade query functions should be disabled by default"""
        generator = AuditGenerator()
        sql = generator.generate_audit_query_functions(
            entity_name="Comment",
            audit_config={},  # No include_cascade
        )

        # Should NOT include cascade function
        assert "get_comment_audit_history_with_cascade" not in sql
        assert "get_mutations_affecting_entity" not in sql

    def test_audit_query_includes_mutations_affecting_entity(self):
        """Should include function to find mutations affecting specific entity types"""
        generator = AuditGenerator()
        sql = generator.generate_audit_query_functions(
            entity_name="Post", audit_config={"include_cascade": True}
        )

        # Should include mutations affecting entity function
        assert "get_mutations_affecting_entity" in sql
        assert "p_entity_type TEXT" in sql
        assert "mutation_name TEXT" in sql

    def test_generate_cascade_audit_views(self):
        """Should generate helper views for cascade audit queries"""
        generator = AuditGenerator()
        sql = generator.generate_cascade_audit_views("Post")

        # Should include cascade audit summary view
        assert "v_post_cascade_audit" in sql
        assert "CREATE OR REPLACE VIEW app.v_post_cascade_audit" in sql

        # Should include recent cascade mutations view
        assert "v_post_recent_cascade_mutations" in sql
        assert "CREATE OR REPLACE VIEW app.v_post_recent_cascade_mutations" in sql

        # Should include cascade data filtering
        assert "WHERE a.cascade_data IS NOT NULL" in sql
