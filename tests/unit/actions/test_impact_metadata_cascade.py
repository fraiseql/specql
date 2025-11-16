"""
Tests for Impact Metadata Compiler - Cascade Support
TDD Cycle 2.1: Declare Cascade Variables
"""

import pytest

from src.core.ast_models import Action, ActionImpact, EntityImpact, Entity
from src.generators.actions.impact_metadata_compiler import ImpactMetadataCompiler


class TestImpactMetadataCascade:
    """Test cascade variable declaration in impact metadata compiler"""

    @pytest.fixture
    def compiler(self):
        """Create impact metadata compiler instance"""
        return ImpactMetadataCompiler()

    def test_compile_declares_cascade_variables(self, compiler):
        """Compiler should declare cascade variables when impact exists"""
        action = Action(
            name="create_post",
            impact=ActionImpact(
                primary=EntityImpact(entity="Post", operation="CREATE")
            ),
            steps=[],
        )
        entity = Entity(name="Post", schema="blog")

        sql = compiler.compile(action, entity)

        # Should declare cascade arrays
        assert "v_cascade_entities JSONB[]" in sql
        assert "v_cascade_deleted JSONB[]" in sql

        # Should still declare existing metadata
        assert "v_meta mutation_metadata.mutation_impact_metadata" in sql

    def test_compile_builds_primary_cascade_entity(self, compiler):
        """Should build cascade entity from primary impact"""
        action = Action(
            name="create_post",
            impact=ActionImpact(
                primary=EntityImpact(
                    entity="Post", operation="CREATE", fields=["title", "content"]
                )
            ),
            steps=[],
        )
        entity = Entity(name="Post", schema="blog")

        sql = compiler.compile(action, entity)

        # Should call cascade_entity helper
        assert "app.cascade_entity" in sql
        assert "'Post'" in sql
        assert "'CREATE'" in sql or "'CREATED'" in sql
        assert "'blog'" in sql
        assert "'tv_post'" in sql

    def test_compile_builds_side_effects_cascade(self, compiler):
        """Should build cascade entities for side effects"""
        action = Action(
            name="create_post",
            impact=ActionImpact(
                primary=EntityImpact(entity="Post", operation="CREATE"),
                side_effects=[
                    EntityImpact(
                        entity="User", operation="UPDATE", fields=["post_count"]
                    ),
                    EntityImpact(entity="Notification", operation="CREATE"),
                ],
            ),
            steps=[],
        )
        entity = Entity(name="Post", schema="blog")

        sql = compiler.compile(action, entity)

        # Should append to v_cascade_entities
        assert "v_cascade_entities := v_cascade_entities || ARRAY[" in sql

        # Should include User entity
        assert "app.cascade_entity('User'" in sql
        assert "'UPDATED'" in sql

        # Should include Notification entity
        assert "app.cascade_entity('Notification'" in sql
        assert "'CREATED'" in sql
