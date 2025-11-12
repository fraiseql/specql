"""
Tests for AuditGenerator cascade trigger functionality
"""

from src.generators.enterprise.audit_generator import AuditGenerator


class TestAuditCascadeTriggers:
    """Test audit trigger cascade data capture"""

    def test_audit_trigger_captures_cascade_data(self):
        """Audit triggers should capture cascade data from action context"""
        generator = AuditGenerator()

        # Mock entity dict as expected by the method
        entity = {
            "name": "Post",
            "schema": "blog"
        }

        sql = generator.generate_audit_trigger(entity, {"include_cascade": True})

        # Should reference cascade data from session variable
        assert "NULLIF(current_setting('app.cascade_data', true), '')::jsonb" in sql

        # Should extract cascade_entities array
        assert "string_to_array(NULLIF(current_setting('app.cascade_entities', true), ''), ',')" in sql

        # Should store cascade_source (mutation name)
        assert "NULLIF(current_setting('app.cascade_source', true), '')" in sql

        # Should include cascade columns in INSERT statement
        assert "cascade_data, cascade_entities, cascade_timestamp, cascade_source" in sql

    def test_audit_trigger_without_cascade_unchanged(self):
        """Audit triggers without cascade should work as before"""
        generator = AuditGenerator()

        entity = {
            "name": "User",
            "schema": "app"
        }

        sql = generator.generate_audit_trigger(entity, {"include_cascade": False})

        # Should NOT include cascade session variables
        assert "current_setting('app.cascade_data')" not in sql
        assert "cascade_entities" not in sql
        assert "cascade_source" not in sql

        # Should NOT include cascade columns in INSERT
        assert "cascade_data," not in sql

    def test_audit_trigger_cascade_disabled_by_default(self):
        """Cascade should be disabled by default"""
        generator = AuditGenerator()

        entity = {
            "name": "Comment",
            "schema": "blog"
        }

        sql = generator.generate_audit_trigger(entity, {})  # No include_cascade

        # Should NOT include cascade functionality
        assert "current_setting('app.cascade_data')" not in sql
        assert "cascade_entities" not in sql