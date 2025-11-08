"""
Impact Metadata Compiler - Generate type-safe impact metadata using PostgreSQL composite types
"""

from dataclasses import dataclass

from src.core.ast_models import Action, ActionImpact, EntityImpact
from src.generators.actions.composite_type_builder import CompositeTypeBuilder


@dataclass
class ImpactMetadataCompiler:
    """Compiles impact metadata using composite types"""

    def compile(self, action: Action) -> str:
        """Generate impact metadata construction"""
        if not action.impact:
            return ""

        impact = action.impact

        parts = []

        # Declare metadata variable
        parts.append("v_meta mutation_metadata.mutation_impact_metadata;")

        # Primary entity
        parts.append(self.build_primary_impact(impact))

        # Side effects
        if impact.side_effects:
            parts.append(self.build_side_effects(impact))

        # Cache invalidations
        if impact.cache_invalidations:
            parts.append(self.build_cache_invalidations(impact))

        return "\n    ".join(parts)

    def build_primary_impact(self, impact: ActionImpact) -> str:
        """Build primary entity impact (type-safe)"""
        return f"""
    -- Build primary entity impact (type-safe)
    v_meta.primary_entity := {CompositeTypeBuilder.build_entity_impact(impact.primary)};
"""

    def build_side_effects(self, impact: ActionImpact) -> str:
        """Build side effects array"""
        return f"""
    -- Build side effects array
    v_meta.actual_side_effects := {CompositeTypeBuilder.build_entity_impact_array(impact.side_effects)};
"""

    def build_cache_invalidations(self, impact: ActionImpact) -> str:
        """Build cache invalidation array"""
        return f"""
    -- Build cache invalidations
    v_meta.cache_invalidations := {CompositeTypeBuilder.build_cache_invalidation_array(impact.cache_invalidations)};
"""

    def integrate_into_result(self, action: Action) -> str:
        """Integrate metadata into mutation_result.extra_metadata"""
        if not action.impact:
            return "v_result.extra_metadata := '{}'::jsonb;"

        # Build extra_metadata with side effects + _meta
        parts = []

        # Side effect collections (e.g., createdNotifications)
        for effect in action.impact.side_effects:
            if effect.collection:
                parts.append(f"'{effect.collection}', {self._build_collection_query(effect)}")

        # Add _meta
        parts.append("'_meta', to_jsonb(v_meta)")

        separator = ",\n        "
        return f"""
    v_result.extra_metadata := jsonb_build_object(
        {separator.join(parts)}
    );
"""

    def _build_collection_query(self, effect: EntityImpact) -> str:
        """Build query for side effect collection"""
        # Placeholder - would need actual implementation based on requirements
        return f"'[]'::jsonb  -- {effect.collection} collection"
