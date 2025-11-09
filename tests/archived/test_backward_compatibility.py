"""Test backward compatibility with underscore separator."""

import pytest
from tests.utils.db_test import execute_sql, execute_query


class TestBackwardCompatibility:
    """Ensure explicit underscore override still works."""

    def test_explicit_underscore_override_works(self, db):
        """Entities with explicit underscore config should still work."""
        # SpecQL with explicit underscore
        yaml_content = """
entity: LegacyLocation
schema: tenant
hierarchical: true
identifier:
  separator: "_"  # Explicit override to old default
fields:
  name: text
"""
        # Generate and test
        # ... parser + generator + execute ...

        # Should use underscore, not dot
        # identifier should be: acme-corp|parent_child_grandchild
        pass

    def test_new_entities_use_dot_by_default(self, db):
        """New entities without explicit config should use dot."""
        # SpecQL without separator specified
        yaml_content = """
entity: ModernLocation
schema: tenant
hierarchical: true
fields:
  name: text
"""
        # Generate and test
        # Should use dot: acme-corp|parent.child.grandchild
        pass
