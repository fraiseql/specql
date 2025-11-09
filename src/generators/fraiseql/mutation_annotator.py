"""
Mutation Annotator (Team D)
Generates FraiseQL annotations for PL/pgSQL mutation functions

Purpose:
- Tell FraiseQL how to expose mutation functions as GraphQL mutations
- Include impact metadata for frontend cache invalidation
- Map PostgreSQL function parameters to GraphQL input types
"""

from typing import Any, Dict, Optional

from src.core.ast_models import Action, ActionImpact


class MutationAnnotator:
    """Generate FraiseQL annotations for mutation functions"""

    def __init__(self, schema: str, entity_name: str):
        self.schema = schema
        self.entity_name = entity_name

    def generate_mutation_annotation(self, action: Action) -> str:
        """
        Generate @fraiseql:mutation annotation for a PL/pgSQL function

        Args:
            action: The parsed action definition

        Returns:
            SQL COMMENT statement with @fraiseql:mutation annotation
        """
        function_name = f"{self.schema}.{action.name}"
        graphql_name = self._to_camel_case(action.name)

        # Build metadata mapping if impact exists
        metadata_mapping = self._build_metadata_mapping(action.impact)

        # Generate the annotation
        pascal_name = graphql_name[0].upper() + graphql_name[1:] if graphql_name else ""
        annotation_lines = [
            f"COMMENT ON FUNCTION {function_name} IS",
            "  '@fraiseql:mutation",
            f"   name={graphql_name}",
            f"   input={pascal_name}Input",
            f"   success_type={pascal_name}Success",
            f"   error_type={pascal_name}Error",
            f"   primary_entity={self.entity_name}",
            f"   metadata_mapping={metadata_mapping}';",
        ]

        return "\n".join(annotation_lines)

    def _build_metadata_mapping(self, impact: Optional[ActionImpact] = None) -> str:
        """
        Build metadata mapping JSON for cache invalidation

        Args:
            impact: Action impact metadata

        Returns:
            JSON string with metadata mapping
        """
        if not impact:
            return "{}"

        # For now, include basic impact metadata
        # In a full implementation, this would include detailed cache invalidation rules
        mapping: Dict[str, Any] = {"_meta": "MutationImpactMetadata"}

        # Add primary entity impact
        if impact.primary:
            mapping["primary_impact"] = {
                "entity": impact.primary.entity,
                "operation": impact.primary.operation,
                "fields": impact.primary.fields,
            }

        # Add side effects if any
        if impact.side_effects:
            mapping["side_effects"] = [
                {"entity": side.entity, "operation": side.operation, "fields": side.fields}
                for side in impact.side_effects
            ]

        # Convert to JSON-like string (Python dict representation)
        return str(mapping).replace("'", '"')

    def _to_camel_case(self, snake_str: str) -> str:
        """
        Convert snake_case to camelCase

        Args:
            snake_str: String in snake_case format

        Returns:
            String in camelCase format
        """
        components = snake_str.split("_")
        return components[0] + "".join(x.capitalize() for x in components[1:])
