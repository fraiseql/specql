"""
Impact Metadata Compiler - Generate type-safe impact metadata using PostgreSQL composite types
"""

from dataclasses import dataclass

from src.core.ast_models import Action, ActionImpact, EntityImpact, Entity
from src.generators.actions.composite_type_builder import CompositeTypeBuilder


@dataclass
class ImpactMetadataCompiler:
    """Compiles impact metadata using composite types"""

    has_cascade: bool = False  # Track whether cascade variables are available

    def compile(self, action: Action, entity: Entity | None = None) -> str:
        """Generate impact metadata + cascade construction"""
        if not action.impact:
            return ""

        # Track whether cascade is enabled
        self.has_cascade = entity is not None

        impact = action.impact

        # Handle legacy dict format for backwards compatibility
        if isinstance(impact, dict):
            from src.core.ast_models import (
                ActionImpact,
                EntityImpact,
                CacheInvalidation,
            )

            primary_data = impact.get("primary", {})
            # Infer entity and operation from action/entity context
            entity_name = (
                entity.name if entity else primary_data.get("entity", "Unknown")
            )
            operation = primary_data.get("operation", "UPDATE")  # Default assumption
            fields = primary_data.get("fields", [])

            side_effects_data = impact.get("side_effects", [])
            side_effects = (
                [EntityImpact(**effect) for effect in side_effects_data]
                if side_effects_data
                else []
            )

            cache_data = impact.get("cache_invalidations", [])
            cache_invalidations = (
                [CacheInvalidation(**inv) for inv in cache_data] if cache_data else []
            )

            impact = ActionImpact(
                primary=EntityImpact(
                    entity=entity_name, operation=operation, fields=fields
                ),
                side_effects=side_effects,
                cache_invalidations=cache_invalidations,
            )

        parts = []

        # Declare metadata variable (EXISTING)
        parts.append("v_meta mutation_metadata.mutation_impact_metadata;")

        # NEW: Declare cascade variables (only when entity provided for cascade support)
        if self.has_cascade:
            parts.append("v_cascade_entities JSONB[];")
            parts.append("v_cascade_deleted JSONB[];")

        # Primary entity impact (EXISTING)
        parts.append(self.build_primary_impact(impact))

        # NEW: Build primary cascade entity (only when entity provided)
        if entity is not None:
            parts.append(self.build_primary_cascade(impact, entity))

        # Side effects (EXISTING)
        if impact.side_effects:
            parts.append(self.build_side_effects(impact))
            # NEW: Build side effects cascade
            if entity is not None:
                parts.append(self.build_side_effects_cascade(impact, entity))

        # Cache invalidations (EXISTING)
        if impact.cache_invalidations:
            parts.append(self.build_cache_invalidations(impact))

        return "\n    ".join(parts)

    def build_primary_impact(self, impact: ActionImpact) -> str:
        """Build primary entity impact (type-safe)"""
        return f"""
    -- Build primary entity impact (type-safe)
    v_meta.primary_entity := {CompositeTypeBuilder.build_entity_impact(impact.primary)};
"""

    def build_primary_cascade(self, impact: ActionImpact, entity: Entity) -> str:
        """Build cascade entity for primary impact"""
        typename = impact.primary.entity
        operation = impact.primary.operation
        schema = entity.schema
        view_name = f"tv_{typename.lower()}"

        # Map operation to GraphQL convention
        operation_graphql = self._map_operation(operation)

        # Determine ID variable based on operation
        # For CREATE: v_{entity}_id (captured from INSERT)
        # For UPDATE/DELETE: p_{entity}_id (function parameter)
        if operation == "CREATE":
            id_var = f"v_{typename.lower()}_id"
        else:
            id_var = f"p_{typename.lower()}_id"

        return f"""
    -- Build cascade entity for primary impact
    v_cascade_entities := ARRAY[
        app.cascade_entity(
            '{typename}',
            {id_var},
            '{operation_graphql}',
            '{schema}',
            '{view_name}'
        )
    ];
"""

    def build_side_effects_cascade(self, impact: ActionImpact, entity: Entity) -> str:
        """Build cascade entities for side effects"""
        if not impact.side_effects:
            return ""

        cascade_calls = []

        for effect in impact.side_effects:
            typename = effect.entity
            operation = effect.operation
            # Support cross-schema: check if effect has schema, otherwise use entity's schema
            schema = getattr(effect, "schema", None) or entity.schema
            view_name = f"tv_{typename.lower()}"
            operation_graphql = self._map_operation(operation)

            # Determine ID variable (convention: v_{entity}_id)
            id_var = f"v_{typename.lower()}_id"

            if operation == "DELETE":
                # Deleted entities don't include full data
                cascade_calls.append(f"app.cascade_deleted('{typename}', {id_var})")
            else:
                # Created/Updated entities include full data
                cascade_calls.append(
                    f"app.cascade_entity('{typename}', {id_var}, '{operation_graphql}', '{schema}', '{view_name}')"
                )

        if not cascade_calls:
            return ""

        # Append to existing cascade array
        cascade_array = ",\n        ".join(cascade_calls)
        return f"""
    -- Append side effect cascade entities
    v_cascade_entities := v_cascade_entities || ARRAY[
        {cascade_array}
    ];
"""

    def _map_operation(self, operation: str) -> str:
        """Map SpecQL operation to GraphQL cascade operation"""
        mapping = {"CREATE": "CREATED", "UPDATE": "UPDATED", "DELETE": "DELETED"}
        return mapping.get(operation, operation)

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
        """Integrate metadata AND cascade into mutation_result.extra_metadata"""
        if not action.impact:
            return "v_result.extra_metadata := '{}'::jsonb;"

        # Handle legacy dict format for backwards compatibility
        impact = action.impact
        if isinstance(impact, dict):
            from src.core.ast_models import (
                ActionImpact,
                EntityImpact,
                CacheInvalidation,
            )

            primary_data = impact.get("primary", {})
            # Infer entity and operation from action/entity context
            entity_name = primary_data.get("entity", "Unknown")
            operation = primary_data.get("operation", "UPDATE")  # Default assumption
            fields = primary_data.get("fields", [])

            side_effects_data = impact.get("side_effects", [])
            side_effects = (
                [EntityImpact(**effect) for effect in side_effects_data]
                if side_effects_data
                else []
            )

            cache_data = impact.get("cache_invalidations", [])
            cache_invalidations = (
                [CacheInvalidation(**inv) for inv in cache_data] if cache_data else []
            )

            impact = ActionImpact(
                primary=EntityImpact(
                    entity=entity_name, operation=operation, fields=fields
                ),
                side_effects=side_effects,
                cache_invalidations=cache_invalidations,
            )
            # Update action.impact for the rest of the method
            action = Action(
                name=action.name,
                requires=action.requires,
                steps=action.steps,
                impact=impact,
                hierarchy_impact=action.hierarchy_impact,
                cdc=action.cdc,
            )

        parts = []

        # Build cascade data structure
        cascade_data = ""
        if self.has_cascade:
            cascade_data = """jsonb_build_object(
                'updated', COALESCE(
                    (SELECT jsonb_agg(e) FROM unnest(v_cascade_entities) e),
                    '[]'::jsonb
                ),
                'deleted', COALESCE(
                    (SELECT jsonb_agg(e) FROM unnest(v_cascade_deleted) e),
                    '[]'::jsonb
                ),
                'invalidations', COALESCE(to_jsonb(v_meta.cache_invalidations), '[]'::jsonb),
                'metadata', jsonb_build_object(
                    'timestamp', now(),
                    'affectedCount', COALESCE(array_length(v_cascade_entities, 1), 0) +
                                     COALESCE(array_length(v_cascade_deleted, 1), 0)
                )
            )"""

        # NEW: Set session variables for audit triggers (only if cascade is available)
        session_setup = ""
        if self.has_cascade:
            session_setup = f"""
    -- Set cascade data in session for audit triggers
    PERFORM set_config('app.cascade_data', {cascade_data}::text, true);
    PERFORM set_config('app.cascade_entities',
        array_to_string(
            ARRAY(SELECT jsonb_array_elements_text(
                {cascade_data}->'updated')->>'__typename'
            ),
            ','
        ),
        true
    );
    PERFORM set_config('app.cascade_source', '{action.name}', true);
"""

        # NEW: Add _cascade structure (only if cascade variables are available)
        if self.has_cascade:
            parts.append(f"'_cascade', {cascade_data}")

        # EXISTING: Side effect collections (e.g., createdNotifications)
        for effect in impact.side_effects:
            if effect.collection:
                parts.append(
                    f"'{effect.collection}', {self._build_collection_query(effect)}"
                )

        # EXISTING: Add _meta
        parts.append("'_meta', to_jsonb(v_meta)")

        separator = ",\n        "
        result_sql = f"""
    v_result.extra_metadata := jsonb_build_object(
        {separator.join(parts)}
    );
"""

        # NEW: Clear session variables after mutation
        session_cleanup = ""
        if self.has_cascade:
            session_cleanup = """
    -- Clear cascade session variables
    PERFORM set_config('app.cascade_data', NULL, true);
    PERFORM set_config('app.cascade_entities', NULL, true);
    PERFORM set_config('app.cascade_source', NULL, true);
"""

        return session_setup + result_sql + session_cleanup

    def _build_collection_query(self, effect: EntityImpact) -> str:
        """Build query for side effect collection"""
        # Placeholder - would need actual implementation based on requirements
        return f"'[]'::jsonb  -- {effect.collection} collection"
