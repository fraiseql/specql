"""
Composite Type Builder - Type-safe construction of PostgreSQL composite types
"""

import json

from src.core.ast_models import CacheInvalidation, EntityImpact


class CompositeTypeBuilder:
    """Builds type-safe PostgreSQL composite type constructors"""

    @staticmethod
    def build_entity_impact(impact: EntityImpact) -> str:
        """Build entity_impact composite type ROW constructor"""
        fields = impact.fields or []

        return f"""ROW(
            '{impact.entity}',                          -- entity_type
            '{impact.operation}',                       -- operation
            ARRAY{fields}::TEXT[]                       -- modified_fields
        )::mutation_metadata.entity_impact"""

    @staticmethod
    def build_cache_invalidation(inv: CacheInvalidation) -> str:
        """Build cache_invalidation composite type ROW constructor"""
        filter_json = json.dumps(inv.filter) if inv.filter else "null"

        return f"""ROW(
            '{inv.query}',                      -- query_name
            '{filter_json}'::jsonb,             -- filter_json
            '{inv.strategy}',                   -- strategy
            '{inv.reason}'                      -- reason
        )::mutation_metadata.cache_invalidation"""

    @staticmethod
    def build_entity_impact_array(impacts: list[EntityImpact]) -> str:
        """Build array of entity_impact composite types"""
        if not impacts:
            return "ARRAY[]::mutation_metadata.entity_impact[]"

        rows = [CompositeTypeBuilder.build_entity_impact(impact) for impact in impacts]
        separator = ",\n        "
        return f"ARRAY[\n        {separator.join(rows)}\n    ]"

    @staticmethod
    def build_cache_invalidation_array(invalidations: list[CacheInvalidation]) -> str:
        """Build array of cache_invalidation composite types"""
        if not invalidations:
            return "ARRAY[]::mutation_metadata.cache_invalidation[]"

        rows = [CompositeTypeBuilder.build_cache_invalidation(inv) for inv in invalidations]
        separator = ",\n        "
        return f"ARRAY[\n        {separator.join(rows)}\n    ]"
