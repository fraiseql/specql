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

    def generate_app_mutation_annotation(self, action: Action) -> str:
        """
        Generate @fraiseql:mutation annotation for app.* wrapper functions

        Uses YAML format with description for app layer functions.

        Args:
            action: The parsed action definition

        Returns:
            SQL COMMENT statement with descriptive @fraiseql:mutation annotation
        """
        function_name = f"app.{action.name}"
        graphql_name = self._to_camel_case(action.name)
        pascal_name = graphql_name[0].upper() + graphql_name[1:] if graphql_name else ""

        # Get action description
        description = self._get_action_description(action)

        annotation_lines = [
            f"COMMENT ON FUNCTION {function_name} IS",
            f"'{description}",
            "",
            "@fraiseql:mutation",
            f"name: {graphql_name}",
            f"input_type: app.type_{action.name}_input",
            f"success_type: {pascal_name}Success",
            f"failure_type: {pascal_name}Error';",
        ]

        return "\n".join(annotation_lines)

    def _get_action_description(self, action: Action) -> str:
        """
        Get human-readable description for action

        Args:
            action: The action to describe

        Returns:
            Description string
        """
        action_type = self._detect_action_type(action.name)
        entity_name = self.entity_name

        if action_type == "create":
            return f"Creates a new {entity_name} record.\nValidates input and delegates to core business logic."
        elif action_type == "update":
            return f"Updates an existing {entity_name} record.\nValidates input and delegates to core business logic."
        elif action_type == "delete":
            return f"Deletes an existing {entity_name} record.\nValidates permissions and delegates to core business logic."
        else:
            return f"Performs {action.name.replace('_', ' ')} operation on {entity_name}.\nValidates input and delegates to core business logic."

    def _detect_action_type(self, action_name: str) -> str:
        """
        Detect action type from action name

        Args:
            action_name: Name of the action

        Returns:
            Action type: 'create', 'update', 'delete', or 'custom'
        """
        if action_name.startswith("create_"):
            return "create"
        elif action_name.startswith("update_"):
            return "update"
        elif action_name.startswith("delete_"):
            return "delete"
        else:
            return "custom"

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
