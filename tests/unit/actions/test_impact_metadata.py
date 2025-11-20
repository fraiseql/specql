"""
Tests for Impact Metadata Compilation
Phase 5: Impact Metadata with Composite Types
"""

import pytest

from core.ast_models import Action, ActionImpact, CacheInvalidation, EntityImpact
from generators.actions.composite_type_builder import CompositeTypeBuilder
from generators.actions.impact_metadata_compiler import ImpactMetadataCompiler


class TestImpactMetadata:
    """Test impact metadata compilation to PL/pgSQL"""

    @pytest.fixture
    def compiler(self):
        """Create impact metadata compiler instance"""
        return ImpactMetadataCompiler()

    def test_impact_metadata_declaration(self, compiler):
        """Test: Declare impact metadata variable"""
        action = Action(
            name="qualify_lead",
            impact=ActionImpact(primary=EntityImpact(entity="Contact", operation="UPDATE")),
        )

        sql = compiler.compile(action)

        # Expected: Type-safe declaration
        assert "v_meta mutation_metadata.mutation_impact_metadata;" in sql

    def test_primary_impact_construction(self, compiler):
        """Test: Build primary entity impact"""
        impact = ActionImpact(
            primary=EntityImpact(
                entity="Contact", operation="UPDATE", fields=["status", "updated_at"]
            )
        )

        sql = compiler.build_primary_impact(impact)

        # Expected: ROW constructor with type cast
        assert "v_meta.primary_entity := ROW(" in sql
        assert "'Contact'" in sql
        assert "'UPDATE'" in sql
        assert "ARRAY['status', 'updated_at']" in sql
        assert ")::mutation_metadata.entity_impact;" in sql

    def test_side_effects_array(self, compiler):
        """Test: Build side effects array"""
        impact = ActionImpact(
            primary=EntityImpact(entity="Contact", operation="UPDATE"),
            side_effects=[
                EntityImpact(entity="Notification", operation="CREATE", fields=["id", "message"])
            ],
        )

        sql = compiler.build_side_effects(impact)

        # Expected: Array of entity_impact
        assert "v_meta.actual_side_effects := ARRAY[" in sql
        assert "ROW(" in sql
        assert "'Notification'" in sql
        assert "'CREATE'" in sql
        assert "::mutation_metadata.entity_impact" in sql

    def test_cache_invalidations(self, compiler):
        """Test: Build cache invalidation array"""
        impact = ActionImpact(
            primary=EntityImpact(entity="Contact", operation="UPDATE"),
            cache_invalidations=[
                CacheInvalidation(
                    query="contacts",
                    filter={"status": "lead"},
                    strategy="REFETCH",
                    reason="Contact removed from lead list",
                )
            ],
        )

        sql = compiler.build_cache_invalidations(impact)

        # Expected: Array of cache_invalidation composite type
        assert "v_meta.cache_invalidations := ARRAY[" in sql
        assert "ROW(" in sql
        assert "'contacts'" in sql
        assert '\'{"status": "lead"}\'::jsonb' in sql
        assert "'REFETCH'" in sql
        assert "::mutation_metadata.cache_invalidation" in sql

    def test_full_metadata_integration(self, compiler):
        """Test: Full metadata in extra_metadata field"""
        action = Action(
            name="qualify_lead",
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="UPDATE"),
                side_effects=[],
                cache_invalidations=[],
            ),
        )

        sql = compiler.integrate_into_result(action)

        # Expected: _meta in extra_metadata
        assert "v_result.extra_metadata := jsonb_build_object(" in sql
        assert "'_meta', to_jsonb(v_meta)" in sql

    def test_no_impact_metadata(self, compiler):
        """Test: Action with no impact metadata"""
        action = Action(name="simple_action")

        sql = compiler.compile(action)
        assert sql == ""

        sql = compiler.integrate_into_result(action)
        assert sql == "v_result.extra_metadata := '{}'::jsonb;"

    def test_impact_without_side_effects(self, compiler):
        """Test: Impact with no side effects"""
        action = Action(
            name="update_only",
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="UPDATE"),
                side_effects=[],  # Empty
                cache_invalidations=[CacheInvalidation(query="contacts")],
            ),
        )

        sql = compiler.compile(action)
        assert "v_meta.primary_entity :=" in sql
        assert "v_meta.actual_side_effects :=" not in sql  # Should not include side effects
        assert "v_meta.cache_invalidations :=" in sql

    def test_impact_without_cache_invalidations(self, compiler):
        """Test: Impact with no cache invalidations"""
        action = Action(
            name="create_with_effects",
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="CREATE"),
                side_effects=[EntityImpact(entity="Notification", operation="CREATE")],
                cache_invalidations=[],  # Empty
            ),
        )

        sql = compiler.compile(action)
        assert "v_meta.primary_entity :=" in sql
        assert "v_meta.actual_side_effects :=" in sql
        assert "v_meta.cache_invalidations :=" not in sql  # Should not include cache invalidations

    def test_empty_arrays_in_builder(self):
        """Test: Empty arrays in CompositeTypeBuilder"""
        # Test empty entity impact array
        sql = CompositeTypeBuilder.build_entity_impact_array([])
        assert sql == "ARRAY[]::mutation_metadata.entity_impact[]"

        # Test empty cache invalidation array
        sql = CompositeTypeBuilder.build_cache_invalidation_array([])
        assert sql == "ARRAY[]::mutation_metadata.cache_invalidation[]"

    def test_side_effect_collections(self, compiler):
        """Test: Side effects with collections"""
        action = Action(
            name="create_with_collection",
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="CREATE"),
                side_effects=[
                    EntityImpact(
                        entity="Notification", operation="CREATE", collection="createdNotifications"
                    )
                ],
            ),
        )

        sql = compiler.integrate_into_result(action)
        assert "'createdNotifications'" in sql
        assert "_build_collection_query" not in sql  # Method should be called
